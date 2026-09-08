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
Your line is executed by a rules engine exactly as written; the game ends
in a win only if your opponent is dead when it resolves. Use turn {turn}
for every action's "turn" field.
"""


def init_run(puzzles: list[dict], run_path: str, encoder, mode: str = "bare",
             seed: int | None = None, arm: str = "a") -> RunDir:
    """Write one pending task per puzzle. Idempotent per run directory."""
    run = RunDir(run_path)
    cfg_path = os.path.join(run_path, "config.json")
    if not os.path.exists(cfg_path):
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump({"arm": arm, "mode": mode, "seed": seed,
                       "puzzles": [p["id"] for p in puzzles]}, f, indent=1)
    for spec in puzzles:
        task = TASK_TEMPLATE.format(qid=spec["id"],
                                    board=encoder.render(spec, mode=mode),
                                    vocabulary=VOCABULARY, turn=spec["turn"])
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
