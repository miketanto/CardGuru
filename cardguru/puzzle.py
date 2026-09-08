"""Decision puzzles: "find the winning line", graded by execution.

A puzzle is a board state with a provable win available to player A this
turn. An agent answers with a LINE — a scripted action sequence in the
vocabulary of `docs/scenario-spec.md` — and is graded by splicing that line
into the puzzle's state as a scenario, executing it, and checking the
puzzle's `win` conditions against the resulting state. All-or-nothing, no
string matching: any line that wins, wins.

Format (a scenario minus `actions`, plus grading fields):

    {
      "id": "t1-lethal-007",
      "tier": 1,
      "description": "...",
      "trap": null,                     # what a naive agent gets wrong (T2+)
      "notes": "...",
      "turn": 5,                        # the decision turn; A is active
      "players": { ... scenario player blocks ... },
      "win": [{"metric": "life", "player": "B", "max": 0}],
      "known_good": [ ...actions... ],  # admission: must grade as a win
      "known_bad":  [ ...actions... ]   # admission: must grade as a loss
    }

`known_good`/`known_bad` are the instrument check, not hints shown to any
agent: a puzzle is admitted to the suite only after its good line grades
green and its bad line grades red through the same runner that will grade
agents. A puzzle that cannot tell those two apart measures nothing.

Grading is runner-injectable. The default is the XMage batch adjudicator
(`adjudicate.run_scenarios`) — the real instrument. Until an XMage checkout
is configured, `localrunner.run_scenarios` grades tier-1 combat-arithmetic
puzzles with the same simplified damage model the generator proves lethality
with; results carry `"engine": "local-combat"` so a provisional grade can
never be mistaken for an engine-verified one.

Win metrics are evaluated client-side on the outcome's `state` (not via the
driver's `expect` checks) because a win is an inequality — lethal leaves B at
0 *or less*, and the engine may end the game before the scenario's stop
point. Client-side checks stay meaningful in both cases.
"""
from __future__ import annotations

import json
import os

from .adjudicate import validate_scenario

WIN_METRICS = {"life", "permanent_count", "winner"}

_REQUIRED = ("id", "tier", "turn", "players", "win", "known_good", "known_bad")


# -- validation -------------------------------------------------------------

def validate_puzzle(spec: dict) -> list[str]:
    """Cheap structural validation; admission (`admit`) is the real gate."""
    errors = [f"missing field '{k}'" for k in _REQUIRED if k not in spec]
    if errors:
        return errors
    for label in ("known_good", "known_bad"):
        errs = validate_scenario(splice(spec, spec[label]))
        errors += [f"{label}: {e}" for e in errs]
    for r, response in enumerate(spec.get("opponent_responses") or []):
        if not isinstance(response, list):
            errors.append(f"opponent_responses[{r}]: not an action list")
            continue
        errs = validate_scenario(splice(spec, spec["known_good"] + response))
        errors += [f"opponent_responses[{r}]: {e}" for e in errs]
    for i, w in enumerate(spec["win"]):
        if w.get("metric") not in WIN_METRICS:
            errors.append(f"win[{i}]: unknown metric '{w.get('metric')}'")
        elif w["metric"] != "winner" and w.get("player") not in ("A", "B"):
            errors.append(f"win[{i}]: bad player '{w.get('player')}'")
        if w["metric"] != "winner" and "max" not in w and "min" not in w:
            errors.append(f"win[{i}]: needs 'max' and/or 'min'")
    return errors


def validate_line(spec: dict, line: list) -> list[str]:
    """Is an agent's proposed line even runnable against this puzzle?

    This is the pre-screen that turns an illegal answer into a bounded
    retry with a message, instead of a wasted engine run.
    """
    if not isinstance(line, list) or not line:
        return ["line must be a non-empty JSON array of actions"]
    return validate_scenario(splice(spec, line))


# -- splice -----------------------------------------------------------------

def splice(spec: dict, line: list, run_id: str | None = None) -> dict:
    """A puzzle plus a line IS a scenario. Stop at end of the decision turn."""
    return {
        "id": run_id or spec["id"],
        "description": spec.get("description", ""),
        "players": spec["players"],
        "actions": line,
        "stop": {"turn": spec["turn"], "phase": "END_TURN"},
    }


# -- win evaluation ---------------------------------------------------------

def _metric_value(outcome: dict, w: dict):
    state = outcome.get("state") or {}
    player = state.get(w.get("player"), {})
    if w["metric"] == "life":
        return player.get("life")
    if w["metric"] == "permanent_count":
        return sum(1 for p in player.get("battlefield", [])
                   if p.get("name") == w.get("card"))
    if w["metric"] == "winner":
        return outcome.get("winner")
    return None


def evaluate_win(outcome: dict, win: list[dict]) -> tuple[bool, list[str]]:
    """All win conditions must hold on the outcome state.

    A run that errored is a loss with the engine's own message as the reason
    — `status: "error"` stays a first-class outcome here exactly as it is in
    adjudication.
    """
    if outcome.get("status") != "executed":
        return False, [f"run did not execute: {outcome.get('error')}"]
    reasons = []
    ok = True
    for w in win:
        val = _metric_value(outcome, w)
        if w["metric"] == "winner":
            hit = val == w.get("player")
            reasons.append(f"winner={val!r} want {w.get('player')!r}")
        elif val is None:
            hit = False
            reasons.append(f"{w['metric']}({w.get('player')}) missing from state")
        else:
            hit = (("max" not in w or val <= w["max"])
                   and ("min" not in w or val >= w["min"]))
            bound = " ".join(f"{k}={w[k]}" for k in ("min", "max") if k in w)
            reasons.append(f"{w['metric']}({w.get('player')})={val} want {bound}")
        ok = ok and hit
    return ok, reasons


# -- grading ----------------------------------------------------------------

def responses_of(spec: dict) -> list[list]:
    """The opponent's enumerated response scripts.

    Tier 3 introduces a defender who ACTS: `opponent_responses` lists every
    response the opponent might make (block assignments, and always the
    empty no-response), each as a scripted action list merged into the
    agent's line at simulation time. A line only wins if it wins against
    ALL of them — minimax grading with the response set enumerated by the
    generator rather than guessed by a model. Absent (tiers 1-2), the sole
    response is "do nothing", which reduces to the old single-run grading.
    """
    return spec.get("opponent_responses") or [[]]


def response_impossible(outcome: dict, response: list) -> bool:
    """A response the line has made illegal cannot beat the line.

    Example: the line kills the blocker, and the scripted block then fails
    with "No permanents found called <blocker>". That error is the
    RESPONSE's, not the line's — the opponent simply no longer has that
    option — so the response is excluded rather than counted as a loss.
    Detection is narrow: the run errored, the response is non-empty, and
    the engine's error names something the response's actions reference.
    The empty response is never excluded, so a genuinely broken line still
    loses through it.
    """
    if outcome.get("status") == "executed" or not response:
        return False
    err = str(outcome.get("error") or "")
    names = {a.get(k) for a in response
             for k in ("blocker", "attacker", "card") if a.get(k)}
    return any(name in err for name in names)


def grade(pairs: list[tuple[dict, list]], runner=None,
          mage_repo: str | None = None) -> list[dict]:
    """Grade (puzzle, line) pairs in ONE batch through the runner.

    Batching is the point: with the XMage adjudicator the JVM warmup is paid
    once per grade call, not per line. Returns one verdict per pair:

        {"id", "win": bool, "reasons": [...], "engine": ...}

    A puzzle with `opponent_responses` grades each line against every
    response; the line's verdict is its WORST case, and the reasons name
    which response beat it. Lines that fail the pre-screen never reach the
    runner; their verdict carries the validator's message.
    """
    if runner is None:
        from .adjudicate import run_scenarios
        runner = lambda specs: run_scenarios_from_specs(specs, run_scenarios,
                                                        mage_repo)
    verdicts: list[dict | None] = []
    to_run, run_slots = [], []
    for i, (spec, line) in enumerate(pairs):
        errs = validate_line(spec, line)
        if errs:
            verdicts.append({"id": spec["id"], "win": False,
                             "reasons": ["invalid line: " + "; ".join(errs)],
                             "engine": None})
            continue
        verdicts.append(None)
        for r, response in enumerate(responses_of(spec)):
            to_run.append(splice(spec, line + response,
                                 run_id=f"{spec['id']}#{i}r{r}"))
            run_slots.append((i, r))
    by_pair: dict[int, list] = {}
    if to_run:
        for (slot, r), outcome in zip(run_slots, runner(to_run)):
            by_pair.setdefault(slot, []).append((r, outcome))
    for slot, response_outcomes in by_pair.items():
        spec = pairs[slot][0]
        responses = responses_of(spec)
        worst_ok, worst_reasons, worst_r, engine = True, [], None, None
        for r, outcome in response_outcomes:
            if response_impossible(outcome, responses[r]):
                continue
            ok, reasons = evaluate_win(outcome, spec["win"])
            engine = engine or outcome.get("engine")
            if not ok and worst_ok:
                worst_ok, worst_reasons, worst_r = False, reasons, r
        if worst_ok:
            _, worst_reasons = evaluate_win(response_outcomes[0][1],
                                            spec["win"])
        reasons = worst_reasons if worst_r is None else (
            [f"beaten by opponent response #{worst_r}"] + worst_reasons)
        verdicts[slot] = {"id": spec["id"], "win": worst_ok,
                          "reasons": reasons, "engine": engine}
    return verdicts  # type: ignore[return-value]


def run_scenarios_from_specs(specs: list[dict], run_scenarios, mage_repo):
    """Adapter: `adjudicate.run_scenarios` takes file paths, not dicts."""
    import tempfile
    with tempfile.TemporaryDirectory(prefix="cardguru-pzl-") as tmp:
        paths = []
        for spec in specs:
            p = os.path.join(tmp, spec["id"].replace("#", "_") + ".json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump(spec, f)
            paths.append(p)
        return run_scenarios(paths, mage_repo=mage_repo)


# -- admission --------------------------------------------------------------

def admit(specs: list[dict], runner=None, mage_repo: str | None = None) -> list[dict]:
    """The instrument check: known_good must win, known_bad must lose.

    Returns one report per puzzle: {"id", "admitted", "good", "bad",
    "reasons"}. Run this through the REAL engine before any published
    number; a local-combat admission is provisional by construction.
    """
    pairs = []
    for spec in specs:
        pairs.append((spec, spec["known_good"]))
        pairs.append((spec, spec["known_bad"]))
    verdicts = grade(pairs, runner=runner, mage_repo=mage_repo)
    reports = []
    for i, spec in enumerate(specs):
        good, bad = verdicts[2 * i], verdicts[2 * i + 1]
        reports.append({
            "id": spec["id"],
            "admitted": bool(good["win"]) and not bad["win"],
            "good": good, "bad": bad,
            "engine": good.get("engine") or bad.get("engine"),
        })
    return reports


# -- io ---------------------------------------------------------------------

def load_puzzles(paths: list[str]) -> list[dict]:
    specs = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            spec = json.load(f)
        errs = validate_puzzle(spec)
        if errs:
            raise ValueError(f"{p}: " + "; ".join(errs))
        specs.append(spec)
    return specs
