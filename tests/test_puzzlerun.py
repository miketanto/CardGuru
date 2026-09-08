"""The run bridge must be exactly as unkind as the API.

Answers are folded in raw (fences and prose included), unparseable answers
are losses with the parser's message, and a run directory is a resumable
cell: init is idempotent, collect grades in one batch. The encoder tests
pin what a bare prompt promises — printed card facts, no advice, no
arithmetic done for the model.
"""
import gzip
import json
import os

import pytest

from cardguru import cardstore as cs
from cardguru.encoder import Encoder
from cardguru.localrunner import LocalRunner
from cardguru.puzzlerun import collect_run, extract_line, init_run
from tests.test_puzzle import FIXTURE, make_puzzle


@pytest.fixture(scope="module")
def store(tmp_path_factory):
    d = tmp_path_factory.mktemp("runstore")
    src = os.path.join(d, "scryfall.jsonl.gz")
    with gzip.open(src, "wt", encoding="utf-8") as f:
        for rec in FIXTURE:
            f.write(json.dumps(rec) + "\n")
    db = os.path.join(d, "cards.sqlite")
    cs.build(src, db, snapshot_date="2026-09-08T00:00:00Z")
    return cs.CardStore(db)


# --- encoder -------------------------------------------------------------

def test_bare_render_shows_facts_not_advice(store):
    text = Encoder(store).render(make_puzzle())
    assert "Test Bear {1}{G} 2/2" in text
    assert "(TAPPED)" in text          # B's tapped Islands
    assert "deals 2 damage" in text    # oracle text for the hand card
    assert "life 6" in text
    # no computed layer in bare mode
    assert "lethal" not in text.lower() and "clock" not in text.lower()


def test_annotated_mode_adds_facts_never_advice(store):
    text = Encoder(store).render(make_puzzle(), mode="annotated")
    assert "COMPUTED" in text and "not advice" in text
    assert "your full attack: 5 combat damage" in text      # Bear 2 + Ox 3
    assert "opponent at 6: a full attack alone leaves them at 1" in text
    assert "your untapped lands: 1" in text
    assert "Test Shock ({R}): 2 damage, may target a player" in text
    # facts, not instructions: no imperative line recommendations
    for verb in ("you should", "best line", "recommended"):
        assert verb not in text.lower()
    # bare mode must NOT contain the computed layer
    assert "COMPUTED" not in Encoder(store).render(make_puzzle())


def test_unknown_cards_degrade_the_prompt_not_the_run(store):
    spec = make_puzzle()
    spec["players"]["A"]["battlefield"].append({"card": "Not A Real Card"})
    assert "Not A Real Card [stats unknown]" in Encoder(store).render(spec)


# --- answer parsing ------------------------------------------------------

def test_extract_line_handles_fences_and_prose():
    raw = 'Here is my line:\n```json\n[{"do": "attack"}]\n```\nGood luck!'
    assert extract_line(raw) == [{"do": "attack"}]


def test_extract_line_refuses_non_arrays():
    with pytest.raises(ValueError, match="no JSON array"):
        extract_line('{"do": "attack"}')


def test_extract_line_ignores_brackets_inside_strings():
    assert extract_line('[{"card": "we[ird] name"}]') \
        == [{"card": "we[ird] name"}]


# --- run lifecycle -------------------------------------------------------

def test_init_writes_tasks_and_is_idempotent(store, tmp_path):
    run = str(tmp_path / "run")
    init_run([make_puzzle()], run, Encoder(store), seed=1)
    task_path = os.path.join(run, "pending", "t1-test.md")
    task = open(task_path, encoding="utf-8").read()
    assert "../answers/t1-test.txt" in task
    assert '"do": "cast"' in task           # vocabulary is in the task
    assert "X=2" in task                    # multi-block idiom is taught
    assert "standing in for a single model call" in task
    before = os.path.getmtime(task_path)
    init_run([make_puzzle()], run, Encoder(store), seed=1)
    assert os.path.getmtime(task_path) == before


def test_collect_grades_answers_and_reports_the_rest(store, tmp_path):
    run = str(tmp_path / "run")
    good = make_puzzle()
    bad = make_puzzle(id="t1-test-2")
    missing = make_puzzle(id="t1-test-3")
    init_run([good, bad, missing], run, Encoder(store), seed=1)
    adir = os.path.join(run, "answers")
    with open(os.path.join(adir, "t1-test.txt"), "w") as f:
        f.write("```json\n" + json.dumps(good["known_good"]) + "\n```")
    with open(os.path.join(adir, "t1-test-2.txt"), "w") as f:
        f.write("I attack with everything!")  # unparseable
    runner = LocalRunner(store)
    summary = collect_run([good, bad, missing], run,
                          runner=runner.run_scenarios)
    assert (summary["puzzles"], summary["answered"], summary["wins"]) \
        == (3, 2, 1)
    assert summary["invalid_or_unparsed"] == 1
    assert summary["missing"] == ["t1-test-3"]
    saved = json.load(open(os.path.join(run, "results.json")))
    assert saved["wins"] == 1
