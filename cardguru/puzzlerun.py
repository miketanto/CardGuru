"""Puzzle benchmark runs with an in-session agent as the model turn.

The gameplay counterpart of `agent_bridge`: same on-disk conventions
(`pending/<id>.md` awaiting an answer, `answers/<id>.txt` holding raw model
output), same discipline (the answer file is folded in uncleaned — fences,
prose and all — because the replay must be exactly as unkind as the API),
same guarantee (everything but the model turn is deterministic, so a run is
resumable and re-gradable at zero model cost).

Arm (a) runs are single-shot by design: one pending task per puzzle, one
answer, no retry. An answer that fails to parse or fails line validation is
a LOSS with the parser's/validator's message as the reason — the invalid-
line rate of a bare prompt is itself a P1 finding, not a nuisance to be
retried away (repair arrives with `lines.py` in P2).

A run directory is one (arm, seed) cell:

    runs/<name>/config.json      arm, mode, seed, puzzle paths — written once
    runs/<name>/pending/<id>.md  task files awaiting answers
    runs/<name>/answers/<id>.txt raw model output, one per puzzle
    runs/<name>/results.json     graded verdicts, written by collect
"""
from __future__ import annotations

import json
import os
import re

from .agent_bridge import RunDir
from .puzzle import grade

# The action vocabulary the model may answer with. Deliberately the full
# scenario vocabulary (not just what tier 1 needs): the vocabulary is part
# of the fixed instrument across tiers, so tier difficulty lives in the
# board, never in a shifting instruction sheet.
VOCABULARY = """\
Answer with a LINE: a JSON array of action objects, executed in order.
Action vocabulary (all fields required unless marked optional):

  {"do": "cast", "turn": T, "phase": "PRECOMBAT_MAIN" | "POSTCOMBAT_MAIN",
   "player": "A", "card": "Name", "target_player": "A" | "B" (optional)}
      Cast a spell from your hand. Use target_player for spells that
      target a player. Casting taps your untapped lands to pay the cost.
  {"do": "play_land", "turn": T, "phase": ..., "player": "A", "card": "Name"}
  {"do": "activate", "turn": T, "phase": ..., "player": "A",
   "ability": "text prefix, e.g. {T}: Add"}
  {"do": "attack", "turn": T, "player": "A", "attacker": "Name"}
      One entry per attacker. Attacking taps the creature.
  {"do": "block", "turn": T, "player": "A", "blocker": "Name",
   "attacker": "Name"}
      One entry per blocking creature.
  {"do": "wait_stack", "turn": T, "phase": ...}
      Let the stack fully resolve before the next action.
  {"do": "choice" | "target" | "mode", "player": "A", "value": "..."}
      Answers the engine's next question for that player, in order.

Notation for edge cases:
  - Two permanents share a name: suffix a zero-based index by battlefield
    entry order — "Grizzly Bears:1" is the second Bears.
  - You attack and 2+ creatures block one of your attackers: you must
    assign that attacker's combat damage with consecutive choice entries,
    one per blocker in block order: {"do": "choice", "player": "A",
    "value": "X=2"} assigns 2 damage to the next blocker.
"""

TASK_TEMPLATE = """\
# Puzzle: `{qid}`

You are a Magic: The Gathering player facing a single decision. Somewhere
in this position is a line that wins the game THIS TURN. Find it.

**Write your answer to `../answers/{qid}.txt`** and nothing else: the JSON
array only, no prose. You are standing in for a single model call — do not
run searches, read project files, or use tools; anything extra makes this
run incomparable to an API run.

## The position

{board}

## How to answer

{vocabulary}
Rules context: every creature already on the battlefield may attack this
turn — treat battlefield permanents as having been under their controller's
control since the turn began (no summoning sickness on setup-placed
creatures).

{execution_note} Use turn {turn} for every action's "turn" field.
"""

SINGLE_NOTE = """\
Your line is executed by a rules engine exactly as written; the game ends
in a win only if your opponent is dead when it resolves."""

SEARCH_NOTE = """\
Answer with SEVERAL candidate lines — a JSON array of 3 to 5 lines, i.e.
an array of arrays: [[action, action, ...], [action, ...], ...]. Make the
candidates genuinely DIFFERENT plans, not permutations of one plan. Every
candidate is executed by a rules engine exactly as written, and the best
resulting position is kept; a candidate that is illegal or falls short
simply loses its slot, so cover your uncertainty with variety."""


def init_run(puzzles: list[dict], run_path: str, encoder, mode: str = "bare",
             seed: int | None = None, arm: str = "a",
             search: bool = False) -> RunDir:
    """Write one pending task per puzzle. Idempotent per run directory."""
    run = RunDir(run_path)
    cfg_path = os.path.join(run_path, "config.json")
    if not os.path.exists(cfg_path):
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump({"arm": arm, "mode": mode, "seed": seed,
                       "search": search,
                       "puzzles": [p["id"] for p in puzzles]}, f, indent=1)
    note = SEARCH_NOTE if search else SINGLE_NOTE
    for spec in puzzles:
        task = TASK_TEMPLATE.format(qid=spec["id"],
                                    board=encoder.render(spec, mode=mode),
                                    vocabulary=VOCABULARY, turn=spec["turn"],
                                    execution_note=note)
        path = os.path.join(run_path, "pending", spec["id"] + ".md")
        answered = os.path.join(run_path, "answers", spec["id"] + ".txt")
        if not os.path.exists(path) and not os.path.exists(answered):
            with open(path, "w", encoding="utf-8") as f:
                f.write(task)
    return run


def extract_line(text: str) -> list:
    """Pull the first JSON array out of raw model output. Raises ValueError
    with a message fit for a verdict's reasons — never cleans silently."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?|\n?```$", "", text.strip())
    start = text.find("[")
    if start < 0:
        raise ValueError("no JSON array in answer")
    depth, in_str, esc = 0, False, False
    for i, ch in enumerate(text[start:], start):
        if esc:
            esc = False
        elif ch == "\\":
            esc = True
        elif ch == '"':
            in_str = not in_str
        elif not in_str:
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    return json.loads(text[start:i + 1])
    raise ValueError("unbalanced JSON array in answer")


MAX_CANDIDATES = 5


def extract_candidates(text: str) -> list[list]:
    """Candidate lines from raw model output.

    An array of arrays is a candidate set; an array of action objects is a
    single-line answer wrapped as one candidate (the single-shot format
    stays valid under search — one candidate is just a search of width 1).
    Mixed or empty shapes raise with a verdict-ready message.
    """
    parsed = extract_line(text)
    if all(isinstance(e, list) for e in parsed):
        if not parsed:
            raise ValueError("empty candidate set")
        return parsed[:MAX_CANDIDATES]
    if all(isinstance(e, dict) for e in parsed):
        return [parsed]
    raise ValueError("answer mixes actions and lines; send an array of "
                     "lines (array of arrays) or one line")


def collect_search_run(puzzles: list[dict], run_path: str, runner=None,
                       mage_repo: str | None = None) -> dict:
    """Arm (c): simulate EVERY candidate, let the linear value pick.

    One engine batch covers all candidates of all puzzles. The pick sees
    only executed outcomes — the engine's veto on illegal or unexecutable
    candidates is the search arm's predicted advantage. The verdict is the
    picked outcome's win status; candidates, scores, and the picked index
    are all recorded so a pick can be audited later.
    """
    from . import value
    from .puzzle import evaluate_win, splice, validate_line

    by_id = {p["id"]: p for p in puzzles}
    adir = os.path.join(run_path, "answers")
    parsed, results = {}, {}
    n_answered = 0
    for fn in sorted(os.listdir(adir)) if os.path.isdir(adir) else []:
        qid, ext = os.path.splitext(fn)
        if ext != ".txt" or qid not in by_id:
            continue
        n_answered += 1
        with open(os.path.join(adir, fn), encoding="utf-8") as f:
            raw = f.read()
        try:
            parsed[qid] = extract_candidates(raw)
        except ValueError as e:
            results[qid] = {"id": qid, "win": False,
                            "reasons": [f"unparseable answer: {e}"],
                            "engine": None}

    # splice every structurally valid candidate; invalid ones keep a note
    to_run, slots, notes = [], [], {}
    for qid, candidates in parsed.items():
        spec = by_id[qid]
        notes[qid] = [None] * len(candidates)
        for i, line in enumerate(candidates):
            errs = validate_line(spec, line)
            if errs:
                notes[qid][i] = "invalid: " + "; ".join(errs)
            else:
                to_run.append(splice(spec, line, run_id=f"{qid}#c{i}"))
                slots.append((qid, i))

    if runner is None:
        from .adjudicate import run_scenarios
        from .puzzle import run_scenarios_from_specs
        runner = lambda specs: run_scenarios_from_specs(specs, run_scenarios,
                                                        mage_repo)
    outcomes_by = {qid: [None] * len(c) for qid, c in parsed.items()}
    if to_run:
        for (qid, i), outcome in zip(slots, runner(to_run)):
            outcomes_by[qid][i] = outcome

    for qid, candidates in parsed.items():
        spec = by_id[qid]
        outcomes = [o if o is not None
                    else {"status": "error", "error": notes[qid][i]}
                    for i, o in enumerate(outcomes_by[qid])]
        best, scores = value.pick(outcomes)
        if best is None:
            results[qid] = {"id": qid, "win": False,
                            "reasons": ["all candidates failed: "
                                        + "; ".join(str(o.get("error"))
                                                    for o in outcomes)],
                            "engine": None, "candidates": len(candidates),
                            "scores": scores}
            continue
        ok, reasons = evaluate_win(outcomes[best], spec["win"])
        results[qid] = {"id": qid, "win": ok, "reasons": reasons,
                        "engine": outcomes[best].get("engine"),
                        "candidates": len(candidates), "picked": best,
                        "scores": scores,
                        "candidate_errors": sum(
                            1 for o in outcomes
                            if o.get("status") != "executed")}

    missing = sorted(set(by_id) - set(results))
    summary = {
        "puzzles": len(by_id),
        "answered": n_answered,
        "wins": sum(1 for v in results.values() if v["win"]),
        "invalid_or_unparsed": sum(1 for v in results.values()
                                   if not v["win"] and v["engine"] is None),
        "missing": missing,
        "results": [results[qid] for qid in sorted(results)],
    }
    with open(os.path.join(run_path, "results.json"), "w",
              encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    return summary


def collect_run(puzzles: list[dict], run_path: str, runner=None,
                mage_repo: str | None = None) -> dict:
    """Parse every answer, grade the parseable ones in ONE engine batch,
    and write results.json. Unanswered puzzles are reported, not graded."""
    by_id = {p["id"]: p for p in puzzles}
    adir = os.path.join(run_path, "answers")
    answered, unparsed = {}, {}
    for fn in sorted(os.listdir(adir)) if os.path.isdir(adir) else []:
        qid, ext = os.path.splitext(fn)
        if ext != ".txt" or qid not in by_id:
            continue
        with open(os.path.join(adir, fn), encoding="utf-8") as f:
            raw = f.read()
        try:
            answered[qid] = extract_line(raw)
        except ValueError as e:
            unparsed[qid] = str(e)

    pairs = [(by_id[qid], line) for qid, line in answered.items()]
    verdicts = grade(pairs, runner=runner, mage_repo=mage_repo)
    results = {v["id"]: v for v in verdicts}
    for qid, why in unparsed.items():
        results[qid] = {"id": qid, "win": False,
                        "reasons": [f"unparseable answer: {why}"],
                        "engine": None}

    missing = sorted(set(by_id) - set(results))
    summary = {
        "puzzles": len(by_id),
        "answered": len(answered) + len(unparsed),
        "wins": sum(1 for v in results.values() if v["win"]),
        "invalid_or_unparsed": sum(
            1 for v in results.values()
            if not v["win"] and v["engine"] is None),
        "missing": missing,
        "results": [results[qid] for qid in sorted(results)],
    }
    with open(os.path.join(run_path, "results.json"), "w",
              encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    return summary
