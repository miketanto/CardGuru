"""Scoring for the 40-question execution-accuracy harness.

The point of the harness is that the number it prints is trustworthy, so the
scorer is tested on the two ways it could lie: counting an unscorable question
as a failure, and rewarding a query that returns nothing.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru import evalset  # noqa: E402

Q = {"id": "q1", "question": "counterspells", "difficulty": "easy",
     "mechanical_area": "1", "expect_present": ["Counterspell", "Mana Leak"],
     "expect_absent": ["Grizzly Bears"]}
UNSCORABLE = {"id": "q0", "question": "combos", "difficulty": "hard",
              "mechanical_area": "7", "expect_present": [], "expect_absent": []}


def test_all_goldens_satisfied_passes():
    r = evalset.score_one(Q, {"Counterspell", "Mana Leak", "Force of Will"})
    assert r["passed"] and r["present_found"] == 2 and r["absent_leaked"] == []


def test_a_missing_expect_present_fails():
    r = evalset.score_one(Q, {"Counterspell"})
    assert not r["passed"] and r["missing"] == ["Mana Leak"]
    assert r["present_found"] == 1        # partial credit still recorded


def test_a_leaked_expect_absent_fails():
    r = evalset.score_one(Q, {"Counterspell", "Mana Leak", "Grizzly Bears"})
    assert not r["passed"] and r["absent_leaked"] == ["Grizzly Bears"]


def test_empty_result_set_cannot_pass():
    """The failure mode the whole exercise exists to catch."""
    assert not evalset.score_one(Q, set())["passed"]


def test_failure_to_compile_is_a_failure_not_an_exclusion():
    r = evalset.score_one(Q, set(), compiled=False, error="boom")
    assert not r["passed"] and r["scorable"] and r["error"] == "boom"


def test_question_with_no_goldens_is_neither_pass_nor_fail():
    r = evalset.score_one(UNSCORABLE, {"anything"})
    assert not r["scorable"] and not r["passed"]


def test_unscorable_questions_leave_the_denominator():
    """Three of the 40 are provably unexpressible in the DSL and carry no
    goldens. Counting them as failures would put a permanent 7.5% floor under
    the error rate and make a real regression harder to see."""
    rows = [evalset.score_one(Q, {"Counterspell", "Mana Leak"}),
            evalset.score_one(UNSCORABLE, set())]
    agg = evalset.aggregate(rows)
    assert agg["n"] == 2 and agg["n_scorable"] == 1
    assert agg["passed"] == 1 and agg["pass_rate"] == 1.0
    assert agg["excluded_ids"] == ["q0"]


def test_excluded_questions_are_named_in_the_headline():
    """Silent exclusion reads as 'we covered everything'."""
    agg = evalset.aggregate([evalset.score_one(UNSCORABLE, set())])
    assert "q0" in evalset.headline(agg)


def test_recall_is_over_cards_not_questions():
    rows = [evalset.score_one(Q, {"Counterspell"})]
    agg = evalset.aggregate(rows)
    assert agg["present_found"] == 1 and agg["present_total"] == 2
    assert agg["recall"] == 0.5 and agg["pass_rate"] == 0.0


def test_overlap_is_jaccard_over_result_sets():
    """Execution grading: two different queries returning the same cards agree
    completely, whatever their text."""
    r = evalset.score_one(Q, {"a", "b"}, reference_hits={"b", "c"})
    assert r["overlap"] == 1 / 3
    assert evalset.score_one(Q, {"a"}, reference_hits={"a"})["overlap"] == 1.0


def test_overlap_is_none_when_both_sides_are_empty():
    """0.0 would read as total disagreement between two identical answers."""
    assert evalset.score_one(Q, set(), reference_hits=set())["overlap"] is None


def test_zero_hit_queries_are_counted_separately():
    agg = evalset.aggregate([evalset.score_one(Q, set()),
                             evalset.score_one(Q, {"Counterspell", "Mana Leak"})])
    assert agg["zero_hit"] == 1


# --- the shipped eval set itself -----------------------------------------

def test_the_eval_set_loads_and_lines_up():
    questions = evalset.load_questions()
    reference = evalset.load_reference()
    assert len(questions) == 40
    assert [q["id"] for q in questions] == list(reference)
    scorable = [q for q in questions if evalset.is_scorable(q)]
    assert len(scorable) == 37
    # every unscorable question is one the reference marked unexpressible —
    # if that stops being true the exclusion is hiding something
    for q in questions:
        if not evalset.is_scorable(q):
            assert reference[q["id"]]["status"] == "unexpressible"
