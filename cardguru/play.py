"""Play real interactive 1v1 games against XMage's built-in AI.

The scenario adjudicator (adjudicate.py) runs a PREDETERMINED script and stops.
This module drives the opposite: a genuine game loop where our agent decides
turn by turn while XMage's AI plays the other seat. The Java side
(CardGuruScenarioRunner interactive mode) runs the whole game synchronously
inside one JVM and, at every decision playerA must make, writes a request to
the spool and blocks until we answer -- so from Python a match is: launch the
driver, then repeatedly read request/<n>.json, call a POLICY(request) -> answer
callback, and write response/<n>.json, until result.json names the winner.

Why file-based (not a socket): it reuses the driver's existing, proven spool
handshake (atomic tmp-then-rename, READY/SHUTDOWN markers) so the interactive
path shares the server mode's plumbing rather than inventing a second one. The
JVM warmup (~40s of card-DB load) is paid once per launched match process.

A POLICY is any callable `request(dict) -> response(dict)`. The request carries
`kind` (mulligan/priority/attackers/blockers), the observable board `state`,
and a decision-specific option menu; the response is the picked option(s). See
`dumb_policy` for the exact shapes and a deterministic baseline that plays a
full aggro game with no model calls at all -- the plumbing proof.
"""
from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
import tempfile
import time
from typing import Callable, Optional

from .adjudicate import ensure_driver

# A policy maps a decision request to a decision response, both plain dicts.
Policy = Callable[[dict], dict]


def dumb_policy(request: dict) -> dict:
    """A deterministic, no-LLM policy that plays a full aggro game.

    The point of this policy is to prove the interactive plumbing end to end
    without any model in the loop: every answer is a fixed rule over the option
    menu the driver offers. Its "strategy" is the classic goldfish line --
    develop the board and swing -- which is enough to reach a real game over
    against the AI, win or lose.

    - mulligan: always keep (never mulligan).
    - priority: take the FIRST non-pass play offered if any (the driver lists
      playable lands/spells/abilities), else pass. Playing the first available
      action each priority drains the hand onto the board turn over turn; when
      nothing is castable it passes, moving the game forward.
    - attackers: attack with EVERYTHING available.
    - blockers: never block (aggro's plan is to race, and unscripted blocks are
      the simplest safe default).
    """
    kind = request.get("kind")
    if kind == "mulligan":
        return {"mulligan": False}
    if kind == "priority":
        options = request.get("options", [])
        for opt in options:
            if opt.get("action") == "activate":
                return {"choice": opt["index"]}
        return {"choice": 0}  # pass
    if kind == "attackers":
        return {"attackers": [o["index"] for o in request.get("options", [])]}
    if kind == "blockers":
        return {"blocks": []}  # no blocks
    # Unknown decision kind: the safest no-op is an empty response, which the
    # driver reads as "no selection" (pass / no attackers / no blocks).
    return {}


def belief_policy(corpus=None, rng=None) -> "Policy":
    """A policy that reads the opponent and plays around what it can't see.

    This is the first wiring of `believe.py` into live play. At the attackers
    decision it gathers the opponent's REVEALED cards (their battlefield +
    graveyard names, which the request state exposes), classifies the meta
    archetype, and asks believe.py how often that deck holds instant-speed
    removal. When removal is believed-live AND the opponent has untapped mana
    to cast it, the policy holds its single biggest attacker back rather than
    over-committing into a blow-out — the same "keep reach for the removal you
    can't see" skill the T4 benchmark rewarded, now applied to a real game.
    Every other decision defers to `dumb_policy`.

    Honest scope: this is a belief-INFORMED heuristic, not the propose-
    simulate-pick search the puzzles use. Full search in a live game needs a
    fork-the-state-and-roll-out primitive the interactive driver does not
    expose yet (see docs/live-match-feasibility.md); until then the belief
    shapes a heuristic rather than driving a simulation. It never holds back
    so much that it stops applying pressure — at most one attacker.
    """
    from . import believe as _believe

    decks = corpus if corpus is not None else _believe.load_corpus()
    r = rng if rng is not None else random.Random(0)

    def policy(request: dict) -> dict:
        if request.get("kind") != "attackers" or not decks:
            return dumb_policy(request)
        options = request.get("options", [])
        if len(options) <= 1:
            return dumb_policy(request)
        b = (request.get("state") or {}).get("B", {})
        seen = [p.get("name") for p in b.get("battlefield", [])
                if p.get("name")] + list(b.get("graveyard", []))
        untapped_lands = sum(1 for p in b.get("battlefield", [])
                             if not p.get("tapped")
                             and _looks_like_land(p))
        summary = _believe.response_probability(seen, decks, hand_size=7,
                                                k=100, rng=r)
        # play around removal only when it is both believed-likely and
        # castable (open mana); otherwise commit fully like aggro wants
        if summary["trick_rate"] >= 0.5 and untapped_lands >= 1:
            biggest = max(options, key=lambda o: o.get("power", 0))
            kept = [o["index"] for o in options if o is not biggest]
            return {"attackers": kept, "belief": summary["archetype"],
                    "played_around": biggest.get("name")}
        return {"attackers": [o["index"] for o in options],
                "belief": summary["archetype"]}

    return policy


def _looks_like_land(perm: dict) -> bool:
    """A permanent with no power/toughness on the opponent's board is treated
    as a mana source for the open-mana proxy (creatures carry P/T; lands do
    not). Coarse but sufficient for 'could they cast removal right now?'."""
    return "power" not in perm and "toughness" not in perm


def pass_policy(request: dict) -> dict:
    """Do nothing ever: keep, never play, never attack, never block.

    Useful as a lower-bound control -- playerA should reliably LOSE to the AI,
    which is itself a plumbing signal (a full game still runs to completion).
    """
    kind = request.get("kind")
    if kind == "mulligan":
        return {"mulligan": False}
    if kind == "priority":
        return {"choice": 0}
    if kind == "attackers":
        return {"attackers": []}
    if kind == "blockers":
        return {"blocks": []}
    return {}


class MatchClient:
    """Launch the interactive driver and serve one match's decisions.

    Use as a context manager so the JVM is always cleaned up::

        with MatchClient(mage_repo) as m:
            result = m.play(dumb_policy)

    `result` is the driver's result.json: {status, winner?, turns}. `winner`
    is "A" (our policy) or "B" (the AI), absent if the game errored before a
    winner was decided.
    """

    def __init__(self, mage_repo: Optional[str] = None,
                 warmup_timeout: int = 300, minimax: bool = False,
                 opp_blockers: int = 0):
        self.mage_repo = mage_repo or os.environ.get("CARDGURU_MAGE_REPO")
        if not self.mage_repo or not os.path.isdir(self.mage_repo):
            raise RuntimeError("XMage checkout not found: set "
                               "CARDGURU_MAGE_REPO or pass mage_repo")
        ensure_driver(self.mage_repo)
        self.warmup_timeout = warmup_timeout
        # When True the driver runs its in-JVM simulation-backed minimax search
        # at the declare-attackers decision (design A in docs/live-minimax.md):
        # attacks are chosen by the search, never by `policy`. Every other
        # decision still comes from `policy` over the spool.
        self.minimax = minimax
        # Plumbing scaffold: seat this many blockers on the (otherwise passive)
        # opponent's battlefield so the search's min-layer has real blocks to
        # weigh. 0 = the honest empty-opponent game. See docs/live-minimax.md.
        self.opp_blockers = opp_blockers
        self.spool: Optional[str] = None
        self.proc: Optional[subprocess.Popen] = None

    # -- lifecycle ---------------------------------------------------------

    def _launch(self):
        self.spool = tempfile.mkdtemp(prefix="cardguru-play-")
        os.makedirs(os.path.join(self.spool, "request"), exist_ok=True)
        os.makedirs(os.path.join(self.spool, "response"), exist_ok=True)
        cmd = ["mvn", "-q", "-pl", "Mage.Tests", "test",
               "-Dtest=CardGuruScenarioRunner", "-DfailIfNoTests=false",
               f"-Dcardguru.interactive.spool={self.spool}"]
        if self.minimax:
            cmd.append("-Dcardguru.minimax=attacks")
            if self.opp_blockers:
                cmd.append(f"-Dcardguru.minimax.opp_blockers={self.opp_blockers}")
        self.proc = subprocess.Popen(
            cmd, cwd=self.mage_repo, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        ready = os.path.join(self.spool, "READY")
        deadline = time.time() + self.warmup_timeout
        while not os.path.exists(ready):
            if self.proc.poll() is not None:
                raise RuntimeError("interactive driver exited during warmup "
                                   f"(rc={self.proc.returncode})")
            if time.time() > deadline:
                self.close()
                raise RuntimeError("interactive driver warmup timed out")
            time.sleep(0.5)

    def close(self):
        if self.proc is not None:
            if self.proc.poll() is None:
                # Ask the JVM to abandon any in-flight decision, then kill.
                try:
                    with open(os.path.join(self.spool, "SHUTDOWN"), "w"):
                        pass
                    self.proc.wait(timeout=10)
                except Exception:
                    self.proc.kill()
            self.proc = None
        if self.spool and os.path.isdir(self.spool):
            shutil.rmtree(self.spool, ignore_errors=True)
        self.spool = None

    def __enter__(self):
        self._launch()
        return self

    def __exit__(self, *exc):
        self.close()

    # -- the match loop ----------------------------------------------------

    def play(self, policy: Policy, decision_timeout: float = 130.0) -> dict:
        """Run one game to completion, serving each decision from `policy`.

        Processes request files in strict sequence order (1, 2, 3, ...): the
        driver never emits request n+1 before it has our response to n (the
        game thread is blocked in the callback), so waiting for exactly the
        next sequence number can never miss or reorder a decision. Returns when
        result.json appears with no request still pending.
        """
        if self.proc is None:
            raise RuntimeError("call play() inside the context manager")
        reqdir = os.path.join(self.spool, "request")
        respdir = os.path.join(self.spool, "response")
        result_path = os.path.join(self.spool, "result.json")

        seq = 1
        while True:
            req_path = os.path.join(reqdir, f"{seq}.json")
            deadline = time.time() + decision_timeout
            while not os.path.exists(req_path):
                # The game may have ended between decisions.
                if os.path.exists(result_path):
                    return self._read_result(result_path)
                if self.proc.poll() is not None:
                    # JVM gone without a result.json -- report what we can.
                    if os.path.exists(result_path):
                        return self._read_result(result_path)
                    raise RuntimeError("interactive driver died mid-match "
                                       f"(rc={self.proc.returncode})")
                if time.time() > deadline:
                    raise RuntimeError(f"timed out awaiting request {seq}")
                time.sleep(0.02)

            with open(req_path, encoding="utf-8") as f:
                request = json.load(f)
            response = policy(request)
            self._write_response(respdir, seq, response)
            seq += 1

    @staticmethod
    def _write_response(respdir: str, seq: int, response: dict):
        tmp = os.path.join(respdir, f"{seq}.json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(response, f)
        os.replace(tmp, os.path.join(respdir, f"{seq}.json"))

    def read_trace(self) -> list[dict]:
        """The driver's per-decision minimax records for this match.

        Present only in minimax mode: one JSON object per declare-attackers
        decision (spool/minimax.jsonl), each recording how many candidate
        attack sets were simulated, the opponent block responses weighed, and
        which set was chosen -- the search's proof-of-work for the sanity check
        deliverable. Empty when the game made no attack decisions.
        """
        if not self.spool:
            return []
        path = os.path.join(self.spool, "minimax.jsonl")
        if not os.path.exists(path):
            return []
        records = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records

    @staticmethod
    def _read_result(path: str) -> dict:
        # The driver writes result.json via tmp-then-rename, so any file we see
        # is complete; a short retry only guards a torn read on odd filesystems.
        for _ in range(50):
            try:
                with open(path, encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                time.sleep(0.02)
        with open(path, encoding="utf-8") as f:
            return json.load(f)


def play_matches(n: int, policy: Policy = dumb_policy,
                 mage_repo: Optional[str] = None,
                 minimax: bool = False, opp_blockers: int = 0) -> dict:
    """Play N games with `policy` vs the AI; return a win/loss tally.

    One JVM per game (a fresh MatchClient each match). Games that error before a
    winner is decided are tallied separately so a flaky rollout never inflates
    either win count. Returns {games, wins, losses, errors, results:[...]}.

    With `minimax=True` the driver runs its simulation-backed attack search
    in-JVM; each game's result carries a `minimax` block summarising the search
    (total attack decisions, candidate-set counts) as integration evidence.
    """
    wins = losses = errors = 0
    results = []
    for i in range(n):
        with MatchClient(mage_repo, minimax=minimax,
                         opp_blockers=opp_blockers) as m:
            result = m.play(policy)
            if minimax:
                trace = m.read_trace()
                result = dict(result)
                result["minimax"] = _summarize_trace(trace)
        results.append(result)
        winner = result.get("winner")
        if winner == "A":
            wins += 1
        elif winner == "B":
            losses += 1
        else:
            errors += 1
    return {"games": n, "wins": wins, "losses": losses,
            "errors": errors, "results": results}


def _summarize_trace(trace: list[dict]) -> dict:
    """Condense the driver's per-decision minimax records into a game summary.

    Keeps the sanity-check numbers the deliverable asks for: how many attack
    decisions the search made, how many candidate sets it simulated in total,
    and a compact per-decision list (turn, candidates, chosen). The full
    records stay under `decisions` for anyone who wants the leaf scores.
    """
    total_candidates = sum(d.get("candidate_sets", 0) for d in trace)
    decisions = [{"turn": d.get("turn"),
                  "candidate_sets": d.get("candidate_sets"),
                  "chosen": d.get("chosen"),
                  "chosen_value": d.get("chosen_value")}
                 for d in trace]
    return {"attack_decisions": len(trace),
            "total_candidate_sets_simulated": total_candidates,
            "decisions": decisions}
