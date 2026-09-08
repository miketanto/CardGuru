"""Execution feedback in the compile loop.

The defect this closes: `compile_question` retried only on `validate()` errors,
so a query that parsed, validated, and returned zero cards was indistinguishable
from a correct one. Five of the seven failures in `docs/handoff.md` were
detectable from the result count alone, and six of seven were a single bad
conjunct inside an `all` — which is why the feedback is a per-clause execution
tree, not just "that returned nothing".
"""
import json
import os
import sys
import types

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru.diagnose import near_misses, query_relaxations  # noqa: E402
from cardguru.index import SearchIndex  # noqa: E402
from cardguru.nl_compiler import compile_question  # noqa: E402
from cardguru.repair import ExecutionChecker, make_checker  # noqa: E402

ONTO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "research", "data", "ontology.json")

# A miniature corpus. `ChangeType` deliberately mirrors the real fetchland
# shape: Forge names concrete land types, never the category "Land".
RECORDS = [
    {"name": "Counterspell", "types": "Instant", "manaCost": "U U",
     "nodes": [{"id": "a0", "kind": "A", "api": "Counter", "apiKind": "SP",
                "params": {"ValidTgts": "Card"}}], "edges": []},
    {"name": "Mana Leak", "types": "Instant", "manaCost": "1 U",
     "nodes": [{"id": "a0", "kind": "A", "api": "Counter", "apiKind": "SP",
                "params": {"ValidTgts": "Card"}}], "edges": []},
    {"name": "Essence Scatter", "types": "Instant", "manaCost": "1 U",
     "nodes": [{"id": "a0", "kind": "A", "api": "Counter", "apiKind": "SP",
                "params": {"ValidTgts": "Creature"}}], "edges": []},
    {"name": "Flooded Strand", "types": "Land",
     "nodes": [{"id": "a0", "kind": "A", "api": "ChangeZone", "apiKind": "AB",
                "params": {"Origin": "Library", "Destination": "Battlefield",
                           "ChangeType": "Plains,Island"}}], "edges": []},
    {"name": "Windswept Heath", "types": "Land",
     "nodes": [{"id": "a0", "kind": "A", "api": "ChangeZone", "apiKind": "AB",
                "params": {"Origin": "Library", "Destination": "Battlefield",
                           "ChangeType": "Forest,Plains"}}], "edges": []},
    {"name": "Terramorphic Expanse", "types": "Land",
     "nodes": [{"id": "a0", "kind": "A", "api": "ChangeZone", "apiKind": "AB",
                "params": {"Origin": "Library", "Destination": "Battlefield",
                           "ChangeType": "Land"}}], "edges": []},
    {"name": "Hanweir Garrison", "types": "Creature Human", "manaCost": "2 R",
     "nodes": [{"id": "t0", "kind": "T", "mode": "Attacks",
                "params": {"ValidCard": "Card.Self"}},
               {"id": "s0", "kind": "SVar", "api": "Token",
                "params": {"TokenTypes": "Human"}}],
     "edges": [{"src": "t0", "dst": "s0", "type": "Execute"}]},
]


@pytest.fixture(scope="module")
def index():
    return SearchIndex(list(RECORDS))


# --------------------------------------------------------------- the checker

def test_off_signal_never_executes(index):
    """`off` must reproduce production behaviour exactly, so the A/B is a flag."""
    assert make_checker(index, "off") is None
    check = ExecutionChecker(index, signals="off")({"node": {"api": "Nope"}})
    assert check.ok and check.hits == -1


def test_zero_hit_feedback_names_the_killer_clause(index):
    query = {"all": [
        {"node": {"api": "Counter"}},                    # 3 cards
        {"card": {"types": {"contains": "Blue"}}},       # 0 — the killer
    ]}
    check = ExecutionChecker(index, signals="zero")(query)
    assert not check.ok and check.kind == "zero" and check.hits == 0
    assert "KILLER" in check.feedback
    assert 'card types contains "Blue"' in check.feedback
    # and the healthy clause's count is in there, so the model can see what to keep
    assert "3" in check.feedback


def test_zero_hits_with_no_empty_clause_says_so(index):
    """Clauses that are each fine but never co-occur is a different diagnosis,
    and telling the model 'fix the empty clause' would send it hunting for one
    that doesn't exist."""
    query = {"all": [
        {"node": {"api": "Counter"}},
        {"card": {"types": {"contains": "Creature"}}},
    ]}
    check = ExecutionChecker(index, signals="zero")(query)
    assert check.kind == "zero"
    assert "KILLER" not in check.feedback
    assert "never describe the same card" in check.feedback


def test_healthy_query_is_accepted_untouched(index):
    check = ExecutionChecker(index, signals="full")({"node": {"api": "Counter"}})
    assert check.ok and check.hits == 3 and check.kind == "ok"


# A branch that matches nothing while the query as a whole returns plenty. The
# compiler prompt actively encourages this shape ("query both with any when
# unsure"), and the zero-result signal is blind to it: nothing looks wrong.
DEAD_BRANCH_Q = {"any": [
    {"node": {"api": "Counter"}},                                    # 3 cards
    {"node": {"api": "ChangeZone", "params": {"ChangeType": "Swamp"}}},  # 0
]}


def test_zero_signal_does_not_raise_dead_predicate_complaints(index):
    """The `zero` arm exists to reproduce the measured round-2 signal alone."""
    assert ExecutionChecker(index, signals="zero")(DEAD_BRANCH_Q).ok
    assert not ExecutionChecker(index, signals="full")(DEAD_BRANCH_Q).ok


def test_dead_predicate_feedback_reports_the_real_values(index):
    """No card's ChangeType says "Swamp"; the fetchlands say "Plains,Island".
    The correction has to come from the data, because nobody remembers this."""
    check = ExecutionChecker(index, signals="full")(DEAD_BRANCH_Q)
    assert check.kind == "narrow" and check.hits == 3
    assert "Plains,Island" in check.feedback
    assert "matches NONE" in check.feedback


def test_a_narrow_but_live_predicate_is_not_flagged(index):
    """Measured regression. Triggering on "relaxing this parameter unlocks
    >=2x more cards" fires on 24 of the 37 hand-vetted reference queries, and
    no higher threshold separates them: known-good queries reach 267x, while
    the real ChangeType defect from docs/handoff.md sits at 61x. A precise
    predicate is SUPPOSED to do most of the filtering."""
    narrow = {"node": {"api": "Counter", "params": {"ValidTgts": "Creature"}}}
    check = ExecutionChecker(index, signals="full")(narrow)
    assert check.ok and check.hits == 1


def test_execution_error_is_reported_not_swallowed(index):
    class Boom:
        def search(self, q):
            raise RuntimeError("kaboom")
    check = ExecutionChecker(Boom(), signals="full")({"node": {"api": "Counter"}})
    assert check.kind == "error" and "kaboom" in check.feedback


# ------------------------------------------------------- relaxation coverage

def test_relaxations_reach_chain_specs():
    """Only 2 of the 40 vetted benchmark queries are a top-level `all` holding
    `node` clauses, which is all the original near_misses could probe. Chains
    carry params too, and most compiled queries are chains."""
    query = {"chain": {"from": {"kind": "T", "params": {"ValidCard": "Card.Self"}},
                       "to": {"api": "Token", "params": {"TokenTypes": "Human"}}}}
    got = {p for p, _vp, _q in query_relaxations(query)}
    assert got == {"ValidCard", "TokenTypes"}


def test_relaxation_drops_exactly_one_predicate():
    query = {"node": {"api": "ChangeZone",
                      "params": {"Origin": "Library", "Destination": "Battlefield"}}}
    relaxed = {p: q for p, _vp, q in query_relaxations(query)}
    assert relaxed["Origin"] == {"node": {"api": "ChangeZone",
                                          "params": {"Destination": "Battlefield"}}}
    assert relaxed["Destination"] == {"node": {"api": "ChangeZone",
                                               "params": {"Origin": "Library"}}}


def test_relaxation_skips_negated_branches():
    """Under `not`, dropping a predicate narrows rather than widens, so the
    'what does relaxing this unlock' reading would be inverted."""
    assert list(query_relaxations({"not": {"node": {"params": {"Origin": "Library"}}}})) == []


def test_near_miss_flags_a_predicate_the_data_never_uses(index):
    """The strongest form of the signal: the predicate matches none of the
    values the parameter actually takes."""
    rows = near_misses(index, {"node": {"api": "ChangeZone",
                                        "params": {"ChangeType": "Swamp"}}})
    row = next(r for r in rows if r["param"] == "ChangeType")
    assert row["matched_values"] == 0
    assert row["reachable"] == 3


def test_near_miss_stays_quiet_when_relaxing_unlocks_nothing(index):
    """A param that isn't doing the filtering is noise and must not be raised."""
    rows = near_misses(index, {"node": {"api": "ChangeZone",
                                        "params": {"Origin": "Library"}}})
    assert rows == []


# ---------------------------------------------------------------- the loop

class StubClient:
    def __init__(self, texts):
        self._texts = list(texts)
        self.requests = []
        self.messages = types.SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        # The compiler grows one `messages` list in place, so recording the
        # kwargs by reference would make every request look like the last one.
        self.requests.append(dict(kwargs, messages=list(kwargs["messages"])))
        block = types.SimpleNamespace(type="text", text=self._texts.pop(0))
        return types.SimpleNamespace(content=[block], stop_reason="end_turn")


ZERO_Q = {"all": [{"node": {"api": "Counter"}},
                  {"card": {"types": {"contains": "Blue"}}}]}
GOOD_Q = {"node": {"api": "Counter"}}


def test_loop_repairs_a_zero_result_query(index):
    client = StubClient([json.dumps(ZERO_Q), json.dumps(GOOD_Q)])
    res = compile_question("counterspells", ONTO_PATH, client=client,
                           use_cache=False, checker=make_checker(index, "zero"))
    assert res.ok and res.query == GOOD_Q
    assert res.checks == ["zero", "ok"] and res.repaired and not res.exhausted
    # the diagnosis, not just "it returned nothing", went back to the model
    assert "KILLER" in client.requests[1]["messages"][-1]["content"]


def test_loop_without_a_checker_accepts_the_zero_result_query(index):
    """The defect, pinned: this is what production did before."""
    client = StubClient([json.dumps(ZERO_Q)])
    res = compile_question("counterspells", ONTO_PATH, client=client,
                           use_cache=False)
    assert res.ok and res.query == ZERO_Q and res.checks == []


def test_standing_by_a_flagged_query_is_accepted(index):
    """The advisory signal must not be able to argue the model out of a
    predicate it re-affirms — otherwise a query it is wrong about costs retries
    and eventually degrades into whatever the loop nags it into."""
    client = StubClient([json.dumps(DEAD_BRANCH_Q), json.dumps(DEAD_BRANCH_Q)])
    res = compile_question("counterspells or swamp fetchers", ONTO_PATH,
                           client=client, use_cache=False,
                           checker=make_checker(index, "full"))
    assert res.ok and res.query == DEAD_BRANCH_Q
    assert res.checks == ["narrow", "narrow"] and len(res.attempts) == 2


def test_dead_predicate_advice_is_given_at_most_once(index):
    """Two different flagged queries in a row: the second is accepted rather
    than spending the whole budget on advice."""
    b = {"any": [{"node": {"api": "Counter"}},
                 {"node": {"api": "ChangeZone", "params": {"ChangeType": "Wastes"}}}]}
    client = StubClient([json.dumps(DEAD_BRANCH_Q), json.dumps(b)])
    res = compile_question("fetchlands", ONTO_PATH, client=client,
                           use_cache=False, checker=make_checker(index, "full"))
    assert res.ok and res.query == b and len(res.attempts) == 2


def test_exhausted_budget_prefers_a_nonempty_answer(index):
    """When every candidate was complained about, an empty result is never the
    better of the two."""
    other_zero = {"all": [{"node": {"api": "Counter"}},
                          {"card": {"types": {"contains": "White"}}}]}
    client = StubClient([json.dumps(ZERO_Q), json.dumps(DEAD_BRANCH_Q),
                         json.dumps(other_zero)])
    res = compile_question("q", ONTO_PATH, client=client, use_cache=False,
                           max_retries=2, checker=make_checker(index, "full"))
    assert res.exhausted and res.query == DEAD_BRANCH_Q and res.hits == 3


def test_exhausted_budget_still_returns_something(index):
    client = StubClient([json.dumps(ZERO_Q)] * 3)
    res = compile_question("q", ONTO_PATH, client=client, use_cache=False,
                           max_retries=2, checker=make_checker(index, "zero"))
    assert res.ok and res.exhausted and res.query == ZERO_Q and res.hits == 0


def test_validation_and_execution_feedback_compose(index):
    """A vocabulary error and then a zero-result query: both signals fire in
    the same loop."""
    bad = json.dumps({"node": {"api": "SummonDragon"}})
    client = StubClient([bad, json.dumps(ZERO_Q), json.dumps(GOOD_Q)])
    res = compile_question("q", ONTO_PATH, client=client, use_cache=False,
                           max_retries=2, checker=make_checker(index, "zero"))
    assert res.ok and res.query == GOOD_Q
    assert "SummonDragon" in client.requests[1]["messages"][-1]["content"]
    assert "KILLER" in client.requests[2]["messages"][-1]["content"]


# ------------------------------------------------------------------- caching

def test_cache_key_separates_the_ab_arms():
    """The feedback config lives in the message turns, not the system prompt,
    so without this the two arms of an A/B serve each other's cached compiles."""
    from cardguru import nl_compiler as nl
    off = nl._cache_key("q", "m", "sys", "off")
    zero = nl._cache_key("q", "m", "sys", "exec:zero")
    full = nl._cache_key("q", "m", "sys", "exec:full")
    assert len({off, zero, full}) == 3


def test_exhausted_results_are_not_cached(index, tmp_path, monkeypatch):
    """A best-effort answer must not be frozen in front of a later prompt fix."""
    from cardguru import nl_compiler as nl
    monkeypatch.setattr(nl, "CACHE_DIR", str(tmp_path))
    client = StubClient([json.dumps(ZERO_Q)] * 3)
    res = compile_question("q", ONTO_PATH, client=client, max_retries=2,
                           checker=make_checker(index, "zero"))
    assert res.exhausted
    assert list(tmp_path.iterdir()) == []
