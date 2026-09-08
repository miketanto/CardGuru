"""Leaf valuation, linear first: score an engine outcome with no LLM call.

Arm (c)'s whole bet is that once candidate lines have been EXECUTED, choosing
among real outcomes is mechanical. The scorer reads only what the driver's
outcome JSON reports — never the puzzle's win conditions, never a golden —
so the same function generalizes from puzzles ("pick the line that killed
them") to midgame states later ("pick the line that left the best board").

Weights are deliberately coarse and documented; the point of the linear arm
is not a tuned evaluation but an ablation baseline the LLM value prompt
(arm d) must beat to justify its calls. If these five terms hold up, that
is a finding.

An errored outcome (illegal line, unimplemented card) scores None and is
excluded from the pick — the engine's veto, which is where the search arm's
power is predicted to come from.
"""
from __future__ import annotations

W_GAME_WON = 1000.0      # a finished win dominates every positional term
W_OPP_LIFE = -10.0       # pressure: every point of their life is bad
W_OWN_LIFE = 1.0
W_OWN_PERMANENT = 2.0    # board presence kept after the line
W_CARD_IN_HAND = 1.0     # resources not spent


def score(outcome: dict) -> float | None:
    """Linear value of one executed outcome, from player A's seat."""
    if outcome.get("status") != "executed":
        return None
    state = outcome.get("state") or {}
    a, b = state.get("A", {}), state.get("B", {})
    total = 0.0
    if outcome.get("winner") == "A" or b.get("life", 20) <= 0:
        total += W_GAME_WON
    total += W_OPP_LIFE * b.get("life", 20)
    total += W_OWN_LIFE * a.get("life", 20)
    total += W_OWN_PERMANENT * len(a.get("battlefield", []))
    total += W_CARD_IN_HAND * a.get("hand_count", 0)
    return total


def pick(outcomes: list[dict]) -> tuple[int | None, list[float | None]]:
    """Index of the best-scoring outcome, with all scores for the record.

    Returns (None, scores) when every candidate errored — the caller
    reports that as a loss carrying each candidate's engine message.
    """
    scores = [score(o) for o in outcomes]
    best, best_score = None, None
    for i, s in enumerate(scores):
        if s is not None and (best_score is None or s > best_score):
            best, best_score = i, s
    return best, scores
