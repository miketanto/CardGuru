"""Execution feedback for the NL -> DSL compile loop.

`nl_compiler.compile_question` retries on `validate()` errors only — syntax and
vocabulary. It never runs the query, so it cannot tell a query that returns the
right 40 cards from one that returns 0 or 4,470. Both pass validation.

This module supplies the missing signal. It executes a validated query and
returns feedback the compiler can hand back to the model:

  ZERO HITS       run `diagnose`, which executes every branch independently and
                  marks the clauses that are empty *on their own* while sitting
                  inside an `all`. That is the sharp version of "it returned
                  nothing": six of the seven failures in `docs/handoff.md` were
                  a single bad conjunct inside an `all`, and the tree names it
                  instead of making the model re-guess the whole query.

  DEAD PREDICATE  run `near_misses`, which drops one param predicate at a time
                  and reports what that param actually takes in the data, and
                  keep only the predicates that match NONE of those values.

`research/agent-compiler-round2.md` measured the plain zero-result signal at
18/20 -> 19/20 with no goldens leaked. The per-clause tree here is a strictly
richer version of the same signal.

## What the over-narrow signal is NOT, and why

`near_misses` ranks rows by how much relaxing one parameter unlocks, on the
theory that the parameter doing nearly all the filtering is the over-narrow one.
That ranking is useful to a human reading a diagnosis. It is useless as an
automatic retry trigger, and this was measured rather than argued:

  * At the shipped >=2x threshold it fires on **24 of the 37 hand-vetted
    reference queries** — queries known to satisfy their goldens — and turns 37
    API calls into 61.
  * There is no higher threshold that separates good from bad. On known-good
    queries the top single-parameter unlock ratios are 267x
    (`sac-outlet-that-refills`), 206x (`global-untap-denial`) and 123x
    (`exile-from-graveyard-as-cost`). The real defect from `docs/handoff.md` #7
    — `ChangeType` filtered on the category word "Land" when Forge writes
    "Plains,Island" — sits at 61x, *below* all three.

That is the expected result in hindsight: a correct precise predicate is
supposed to do most of the filtering. So the ratio is kept for ranking and
display and is not used to trigger anything.

What IS used is the one part of the same computation that carries no judgement:
a predicate that matches none of the values its parameter actually takes among
reachable cards is wrong, the way an out-of-ontology token is wrong. That fires
on **0 of the 37 known-good queries**. It is mostly subsumed by the zero-result
signal — a dead predicate usually zeroes its own clause — but not always: under
an `any`, a dead branch is silent, and the compiler prompt actively encourages
`any` ("query both when unsure"), so a silently-dead branch costs recall with no
symptom at all.

Deliberately absent: a "suspiciously many results" signal. The handoff lists two
such failures (1,170 and 4,470 hits), but both came from `similar.py`'s signature
ranking, not from this compiler, and — as above — no threshold separating "broad"
from "too broad" survives contact with the reference set. Left out until there is
something to derive it from.
"""
from __future__ import annotations

from .diagnose import diagnose, near_misses, render, render_near_misses

# Which execution signals to act on. `off` reproduces the current production
# behaviour exactly (validate-only), so an A/B run is a flag change.
SIGNALS = ("off", "zero", "full")

ZERO_PREAMBLE = (
    "That query is valid, but running it against the card corpus returned "
    "0 cards.\n\nEvery branch was executed independently. Hit counts:\n\n")

ZERO_KILLER_NOTE = (
    "\nA branch marked KILLER matches no card on its own, and because it sits "
    "inside an `all` it forces the entire query to zero no matter how good the "
    "other branches are. Fix or drop exactly that branch — leave the branches "
    "with non-zero counts alone.\n")

ZERO_NO_KILLER_NOTE = (
    "\nNo single branch is empty, so no clause is individually wrong: the "
    "branches simply never describe the same card. Reconsider whether the "
    "question really requires all of them at once, or whether one of them "
    "should be a different structure.\n")

NARROW_PREAMBLE = (
    "That query is valid and returned {hits} card(s), but it contains a "
    "parameter predicate that matches NOTHING in the data. Each line below "
    "drops one predicate and lists the values that parameter really takes "
    "among the cards the rest of the query reaches:\n\n")

NARROW_NOTE = (
    "\nA predicate that matches none of those values contributes no cards — it "
    "either zeroes its clause or, inside an `any`, silently does nothing. "
    "Replace it with a predicate that matches the real values, or drop it. If "
    "you are confident the predicate is right anyway, re-emit the SAME query "
    "unchanged and it will be accepted.\n")

REEMIT = "\nRespond with the query JSON only."


class Check:
    """Outcome of executing one candidate query."""

    def __init__(self, hits: int, feedback: str | None = None, kind: str = "ok"):
        self.hits = hits
        self.feedback = feedback        # None = accept this query
        self.kind = kind                # "ok" | "zero" | "narrow" | "error"

    @property
    def ok(self) -> bool:
        return self.feedback is None

    def __repr__(self):
        return f"<Check {self.kind} hits={self.hits}>"


class ExecutionChecker:
    """Callable that executes a query and returns a `Check`.

    Injected into `compile_question` so the compiler keeps no dependency on the
    search index (and so tests can drive the loop with a fake).
    """

    def __init__(self, index, signals: str = "zero", max_branches: int = 40,
                 max_params: int = 6, top_values: int = 6):
        if signals not in SIGNALS:
            raise ValueError(f"signals must be one of {SIGNALS}, got {signals!r}")
        self.index = index
        self.signals = signals
        self.max_branches = max_branches
        self.max_params = max_params
        self.top_values = top_values
        self.log: list[Check] = []

    def _record(self, check: Check) -> Check:
        self.log.append(check)
        return check

    def __call__(self, query: dict) -> Check:
        if self.signals == "off":
            return self._record(Check(-1))
        try:
            hits = sum(1 for _ in self.index.search(query))
        except Exception as e:
            # A validated query that still explodes at evaluation time is worth
            # reporting back verbatim — it is a real defect in the query.
            return self._record(Check(-1, kind="error", feedback=(
                f"That query is valid but failed to execute: {e}\n"
                "Emit a corrected query." + REEMIT)))

        if hits == 0:
            return self._record(Check(0, kind="zero",
                                      feedback=self._zero_feedback(query)))
        if self.signals != "full":
            return self._record(Check(hits))
        narrow = self._narrow_feedback(query, hits)
        if narrow:
            return self._record(Check(hits, kind="narrow", feedback=narrow))
        return self._record(Check(hits))

    def _zero_feedback(self, query: dict) -> str:
        tree = diagnose(self.index, query, limit_branches=self.max_branches)
        body = "\n".join(render(tree))
        note = ZERO_KILLER_NOTE if tree.get("killers") else ZERO_NO_KILLER_NOTE
        return ZERO_PREAMBLE + body + "\n" + note + REEMIT

    def _narrow_feedback(self, query: dict, hits: int) -> str | None:
        # min_unlock=0 turns off near_misses' own >=2x ranking filter, which is
        # for human display and measured useless as a trigger (see module
        # docstring). Only the dead-predicate rows are acted on.
        rows = [r for r in near_misses(self.index, query,
                                       max_params=self.max_params,
                                       top=self.top_values, min_unlock=0)
                if r["matched_values"] == 0]
        if not rows:
            return None
        body = "\n".join(render_near_misses(rows))
        return NARROW_PREAMBLE.format(hits=hits) + body + NARROW_NOTE + REEMIT


def make_checker(index, signals: str = "zero") -> ExecutionChecker | None:
    """`None` for signals="off" so the compiler skips execution entirely."""
    return None if signals == "off" else ExecutionChecker(index, signals=signals)
