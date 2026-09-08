"""Pooled, adjudicated goldens — the benchmark measuring itself.

Six runs of the compiler produced only 2 question-verdict changes out of 37:
nineteen questions passed every time and sixteen failed every time. Extra seeds
cannot help a saturated benchmark, so the resolution had to come from inside
the questions, and the eval set only judged ~3 cards per question while the
runs disagreed about thousands more.

These tests pin the two properties that keep pooling honest: the assessor must
not be able to infer which system returned a card, and `unclear` must survive
as its own verdict rather than being forced to a side.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BENCH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "benchmark")
sys.path.insert(0, BENCH)

import adjudicate  # noqa: E402


def test_sample_is_deterministic_and_spreads_over_the_pool():
    """A cap is needed to finish at all, but taking the alphabetical head would
    bias the judged set toward one corner of the pool."""
    names = [f"card{i:03d}" for i in range(100)]
    a = adjudicate.sample(names, 10)
    assert a == adjudicate.sample(names, 10)
    assert len(a) == 10 and len(set(a)) == 10
    assert a[0] == "card000" and a[-1] != "card009", "must not be the head"


def test_sample_keeps_everything_when_under_the_cap():
    names = ["a", "b", "c"]
    assert sorted(adjudicate.sample(names, 30)) == names


@pytest.fixture
def merged(tmp_path):
    q = [{"id": "q1", "question": "?", "expect_present": ["Keep"],
          "expect_absent": ["Nope"]}]
    qpath = tmp_path / "questions.json"
    qpath.write_text(json.dumps(q))
    adj = tmp_path / "adj"
    (adj / "verdicts").mkdir(parents=True)
    (adj / "verdicts" / "q1.json").write_text(json.dumps({
        "NewYes": "present", "NewNo": "absent", "Dunno": "unclear",
        "Keep": "absent",          # already judged: must not be overwritten
    }))
    out = tmp_path / "dense.json"

    import argparse
    adjudicate.cmd_merge(argparse.Namespace(adjudication=str(adj),
                                            questions=str(qpath),
                                            out=str(out)))
    return json.loads(out.read_text())[0]


def test_merge_adds_both_sides(merged):
    assert "NewYes" in merged["expect_present"]
    assert "NewNo" in merged["expect_absent"]


def test_unclear_is_not_scored_and_not_discarded(merged):
    """A card the question's wording does not decide is a fact about the
    QUESTION. Forcing it to a side invents a golden; dropping it silently
    loses the only record that the question is underdetermined."""
    assert merged["unclear"] == ["Dunno"]
    assert "Dunno" not in merged["expect_present"]
    assert "Dunno" not in merged["expect_absent"]


def test_existing_goldens_are_never_overwritten(merged):
    """The hand-vetted goldens outrank a fresh adjudication; an assessor
    contradicting one is a signal to look, not a licence to rewrite."""
    assert "Keep" in merged["expect_present"]
    assert "Keep" not in merged["expect_absent"], \
        "the assessor called Keep 'absent'; it must not move"


def test_task_file_hides_which_system_returned_a_card(tmp_path):
    """The whole validity of pooling rests on this. An assessor who can see the
    vote count ratifies the majority instead of reading the card, and the
    goldens would then only ever confirm what the current compiler does."""
    import argparse

    pool = {"q1": {"systems": 7, "union": 3, "already_judged": ["Keep"],
                   "contested": ["Alpha", "Beta"], "n_singleton": 4,
                   "n_unanimous_unjudged": 9, "unanimous_unjudged": ["Gamma"]}}
    ppath = tmp_path / "pool.json"
    ppath.write_text(json.dumps(pool))
    qpath = tmp_path / "questions.json"
    qpath.write_text(json.dumps([{"id": "q1", "question": "does it?",
                                  "expect_present": ["Keep"],
                                  "expect_absent": []}]))
    out = tmp_path / "adj"

    adjudicate.cmd_tasks(argparse.Namespace(
        out=str(out), pool=str(ppath), questions=str(qpath),
        dataset=os.path.join(BENCH, "..", "data", "dataset.jsonl.gz"),
        max_per_question=30))

    text = (out / "q1.md").read_text()
    assert "Alpha" in text and "Beta" in text
    for leak in ("systems", "vote", "contested", "unanimous", "n_singleton",
                 "off_s", "fam_s", "7"):
        assert leak not in text, f"task file leaks {leak!r} to the assessor"
