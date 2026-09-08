"""Puzzles are an instrument before they are a benchmark.

The tests here mirror the admission gate's logic: a puzzle is only useful if
a known-good line grades as a win and a known-bad line grades as a loss
through the same runner that will grade agents. Most tests run against a
synthetic card store (the local runner must never need real data to be
testable); the generator tests use the real store because the generator's
whole job is to mine it, and skip cleanly where it isn't built.
"""
import gzip
import json
import os

import pytest

from cardguru import cardstore as cs
from cardguru.localrunner import LocalRunner
from cardguru.puzzle import (admit, evaluate_win, grade, splice,
                             validate_line, validate_puzzle)
from cardguru.puzzlegen import generate, max_damage

FIXTURE = [
    {"oracle_id": "oid-bear", "name": "Test Bear", "layout": "normal",
     "type_line": "Creature — Bear", "oracle_text": "", "power": "2",
     "toughness": "2", "cmc": 2.0, "mana_cost": "{1}{G}"},
    {"oracle_id": "oid-ox", "name": "Test Ox", "layout": "normal",
     "type_line": "Creature — Ox", "oracle_text": "", "power": "3",
     "toughness": "3", "cmc": 3.0, "mana_cost": "{2}{W}"},
    {"oracle_id": "oid-shock", "name": "Test Shock", "layout": "normal",
     "type_line": "Instant",
     "oracle_text": "Test Shock deals 2 damage to any target.",
     "power": None, "toughness": None, "cmc": 1.0, "mana_cost": "{R}"},
    {"oracle_id": "oid-mountain", "name": "Mountain", "layout": "normal",
     "type_line": "Basic Land — Mountain", "oracle_text": "({T}: Add {R}.)",
     "cmc": 0.0},
    {"oracle_id": "oid-island", "name": "Island", "layout": "normal",
     "type_line": "Basic Land — Island", "oracle_text": "({T}: Add {U}.)",
     "cmc": 0.0},
]


@pytest.fixture(scope="module")
def runner(tmp_path_factory):
    d = tmp_path_factory.mktemp("puzzlestore")
    src = os.path.join(d, "scryfall.jsonl.gz")
    with gzip.open(src, "wt", encoding="utf-8") as f:
        for rec in FIXTURE:
            f.write(json.dumps(rec) + "\n")
    db = os.path.join(d, "cards.sqlite")
    cs.build(src, db, snapshot_date="2026-09-08T00:00:00Z")
    return LocalRunner(cs.CardStore(db))


def make_puzzle(**over):
    spec = {
        "id": "t1-test", "tier": 1, "turn": 1,
        "players": {
            "A": {"life": 20,
                  "battlefield": [{"card": "Test Bear"}, {"card": "Test Ox"},
                                  {"card": "Mountain", "count": 1}],
                  "hand": ["Test Shock"]},
            "B": {"life": 6,
                  "battlefield": [{"card": "Island", "count": 2,
                                   "tapped": True}]},
        },
        "win": [{"metric": "life", "player": "B", "max": 0}],
        "known_good": [
            {"do": "cast", "turn": 1, "phase": "PRECOMBAT_MAIN",
             "player": "A", "card": "Test Shock", "target_player": "B"},
            {"do": "attack", "turn": 1, "player": "A", "attacker": "Test Bear"},
            {"do": "attack", "turn": 1, "player": "A", "attacker": "Test Ox"},
        ],
        "known_bad": [
            {"do": "attack", "turn": 1, "player": "A", "attacker": "Test Bear"},
        ],
    }
    spec.update(over)
    return spec


# --- structure -----------------------------------------------------------

def test_validate_puzzle_accepts_the_reference_shape():
    assert validate_puzzle(make_puzzle()) == []


def test_validate_puzzle_flags_missing_fields_and_bad_metrics():
    assert "missing field 'win'" in validate_puzzle(
        {k: v for k, v in make_puzzle().items() if k != "win"})
    errs = validate_puzzle(make_puzzle(
        win=[{"metric": "vibes", "player": "B", "max": 0}]))
    assert any("unknown metric" in e for e in errs)


def test_splice_produces_a_valid_scenario():
    from cardguru.adjudicate import validate_scenario
    spec = make_puzzle()
    assert validate_scenario(splice(spec, spec["known_good"])) == []


def test_validate_line_rejects_non_lines():
    assert validate_line(make_puzzle(), []) \
        == ["line must be a non-empty JSON array of actions"]
    assert any("unknown do" in e
               for e in validate_line(make_puzzle(), [{"do": "yolo"}]))


# --- win evaluation ------------------------------------------------------

def test_evaluate_win_is_an_inequality_not_an_equality():
    out = {"status": "executed", "state": {"B": {"life": -3}}}
    ok, _ = evaluate_win(out, [{"metric": "life", "player": "B", "max": 0}])
    assert ok


def test_evaluate_win_treats_error_runs_as_losses():
    ok, reasons = evaluate_win({"status": "error", "error": "boom"},
                               [{"metric": "life", "player": "B", "max": 0}])
    assert not ok and "boom" in reasons[0]


# --- local runner --------------------------------------------------------

def test_combat_and_burn_arithmetic(runner):
    spec = make_puzzle()
    verdicts = grade([(spec, spec["known_good"]), (spec, spec["known_bad"])],
                     runner=runner.run_scenarios)
    good, bad = verdicts
    assert good["win"] and good["engine"] == "local-combat"
    assert not bad["win"]  # lone 2-power Bear into 6 life


def test_burn_without_mana_is_a_loud_loss(runner):
    spec = make_puzzle()
    spec["players"]["A"]["battlefield"] = [{"card": "Test Bear"},
                                           {"card": "Test Ox"}]  # no Mountain
    [v] = grade([(spec, spec["known_good"])], runner=runner.run_scenarios)
    assert not v["win"] and "cannot pay" in " ".join(v["reasons"])


def test_untapped_defenders_are_refused_not_guessed(runner):
    spec = make_puzzle()
    spec["players"]["B"]["battlefield"].append({"card": "Test Ox"})
    [v] = grade([(spec, spec["known_good"])], runner=runner.run_scenarios)
    assert not v["win"] and "blocks" in " ".join(v["reasons"])


def test_actions_outside_the_slice_are_refused(runner):
    spec = make_puzzle()
    line = [{"do": "play_land", "turn": 1, "phase": "PRECOMBAT_MAIN",
             "player": "A", "card": "Mountain"}]
    [v] = grade([(spec, line)], runner=runner.run_scenarios)
    assert not v["win"] and "tier-1 slice" in " ".join(v["reasons"])


def test_invalid_lines_never_reach_the_runner():
    def exploding_runner(specs):
        raise AssertionError("runner must not be called")
    [v] = grade([(make_puzzle(), [{"do": "yolo"}])], runner=exploding_runner)
    assert not v["win"] and "invalid line" in v["reasons"][0]


# --- admission gate ------------------------------------------------------

def test_admission_requires_good_to_win_and_bad_to_lose(runner):
    [report] = admit([make_puzzle()], runner=runner.run_scenarios)
    assert report["admitted"]
    # a puzzle whose "bad" line also wins measures nothing
    broken = make_puzzle(known_bad=make_puzzle()["known_good"])
    [report] = admit([broken], runner=runner.run_scenarios)
    assert not report["admitted"]


# --- generator -----------------------------------------------------------

def test_max_damage_brute_force_includes_the_burn_knapsack():
    # combat 5; lands=2 afford the 3-damage spell or the 2-damage one, not both
    assert max_damage([2, 3], [(3, 1), (2, 2)], lands=2) == 8
    assert max_damage([2, 3], [], lands=0) == 5


REAL_DB = os.path.join(os.path.dirname(__file__), "..", "data", "cards.sqlite")
needs_real_store = pytest.mark.skipif(not os.path.exists(REAL_DB),
                                      reason="real card store not built")


@needs_real_store
def test_generated_puzzles_are_deterministic_and_admissible():
    store = cs.CardStore(REAL_DB)
    a = generate(store, count=5, seed=7)
    b = generate(store, count=5, seed=7)
    assert [p["id"] for p in a] == [p["id"] for p in b]
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    assert validate_puzzle(a[0]) == []
    reports = admit(a, runner=LocalRunner(store).run_scenarios)
    assert all(r["admitted"] for r in reports)


@needs_real_store
def test_generated_burn_variant_requires_the_burn():
    store = cs.CardStore(REAL_DB)
    runner = LocalRunner(store)
    burns = [p for p in generate(store, count=30, seed=7)
             if "burn" in p["notes"].split(";")[0]]
    assert burns, "seed 7 should produce combat+burn puzzles"
    for spec in burns:
        attacks_only = [a for a in spec["known_good"] if a["do"] == "attack"]
        [v] = grade([(spec, attacks_only)], runner=runner.run_scenarios)
        assert not v["win"], f"{spec['id']}: lethal without burn"


@needs_real_store
def test_t2_generation_is_deterministic_and_balanced():
    from cardguru.puzzlegen import generate_t2
    store = cs.CardStore(REAL_DB)
    a = generate_t2(store, count=30, seed=11)
    b = generate_t2(store, count=30, seed=11)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    fams = {}
    for p in a:
        fams[p["id"].rsplit("-", 1)[0]] = fams.get(p["id"].rsplit("-", 1)[0], 0) + 1
        assert p["tier"] == 2 and p["trap"], "every t2 puzzle names its trap"
        assert validate_puzzle(p) == []
    assert fams == {"t2-creature-only": 10, "t2-face-not-decoy": 10,
                    "t2-right-burn": 10}


@needs_real_store
def test_t2_defender_creatures_are_always_tapped():
    # spike-block-unscripted: strict-choose auto-declines blocks, so an
    # untapped defender would teach the agent an engine artifact.
    from cardguru.puzzlegen import generate_t2
    store = cs.CardStore(REAL_DB)
    runner = LocalRunner(store)
    for p in generate_t2(store, count=30, seed=11):
        for entry in p["players"]["B"]["battlefield"]:
            if runner.is_creature(entry["card"]):
                assert entry.get("tapped"), f"{p['id']}: untapped defender"


@needs_real_store
def test_t2_admission_holds_under_the_local_runner_too():
    # Verdict-level agreement only: family A/C bad lines lose locally via
    # unsupported-action errors rather than the engine's shortfall, but a
    # loss is a loss — the instrument check is good-wins-and-bad-loses.
    from cardguru.puzzlegen import generate_t2
    store = cs.CardStore(REAL_DB)
    reports = admit(generate_t2(store, count=12, seed=11),
                    runner=LocalRunner(store).run_scenarios)
    assert all(r["admitted"] for r in reports)
