import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru.adjudicate import validate_scenario  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "corpus"))
from parse_mage_tests import parse_method  # noqa: E402


def test_shipped_scenarios_validate():
    for fn in os.listdir("scenarios"):
        with open(os.path.join("scenarios", fn), encoding="utf-8") as f:
            assert validate_scenario(json.load(f)) == [], fn


def test_validate_catches_mistakes():
    assert validate_scenario({}) != []
    errs = validate_scenario({
        "players": {"C": {}},
        "actions": [{"do": "cast", "phase": "MAIN_ONE"}, {"do": "teleport"}],
        "stop": {"phase": "END"},
    })
    assert any("unknown player 'C'" in e for e in errs)
    assert any("bad phase" in e for e in errs)
    assert any("teleport" in e for e in errs)
    assert any("stop" in e for e in errs)


JAVA_FIXTURE = """
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 3);
        addCard(Zone.HAND, playerA, "Lightning Bolt");
        setLife(playerB, 15);
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Lightning Bolt", playerB);
        addTarget(playerA, "PlayerB");
        setChoice(playerA, "Yes");
        setStopAt(1, PhaseStep.END_TURN);
        execute();
        assertLife(playerB, 12);
        assertGraveyardCount(playerA, "Lightning Bolt", 1);
    }
"""


def test_parse_method_extracts_structure():
    rec = parse_method("testBolt", JAVA_FIXTURE, "x/BoltTest.java", "BoltTest")
    kinds = [s["kind"] for s in rec["setup"]]
    assert kinds.count("add_card") == 2 and "set_life" in kinds
    bolt = next(s for s in rec["setup"] if s["card"] == "Mountain")
    assert bolt["count"] == 3 and bolt["zone"] == "BATTLEFIELD"
    assert any(a["kind"] == "cast" and a["what"] == "Lightning Bolt"
               for a in rec["actions"])
    assert any(a["kind"] == "target" for a in rec["actions"])
    assert {a["assert"] for a in rec["assertions"]} == {"assertLife", "assertGraveyardCount"}
    cov = rec["coverage"]
    assert cov["recognized"] == cov["total_calls"] == 8


sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "corpus"))
from generate_scenarios import base_scenario, parse_mono_cost  # noqa: E402


def test_parse_mono_cost():
    assert parse_mono_cost("2 G") == ("G", 3)
    assert parse_mono_cost("1 G G") == ("G", 3)
    assert parse_mono_cost("W") == ("W", 1)
    assert parse_mono_cost("2 W U") is None      # multicolor
    assert parse_mono_cost("X R") is None        # X cost
    assert parse_mono_cost("no cost") is None
    assert parse_mono_cost("3") is None          # colorless only


def test_generated_scenarios_validate():
    scn = base_scenario(
        "gen-test", "test scenario", "etb_token_doubling",
        [{"card": "Plains", "count": 3}, {"card": "Doubling Season"}],
        ["Attended Knight"],
        [{"do": "cast", "turn": 1, "phase": "PRECOMBAT_MAIN", "player": "A",
          "card": "Attended Knight"}],
        [{"check": "battlefield_count", "player": "A", "count": 7}])
    assert validate_scenario(scn) == []
    # every shipped generated scenario must validate too
    gen_dir = "corpus/generated"
    for fn in os.listdir(gen_dir):
        if fn.startswith("gen-") and fn.endswith(".json"):
            with open(os.path.join(gen_dir, fn), encoding="utf-8") as f:
                assert validate_scenario(json.load(f)) == [], fn


from cardguru.cite import Citer, scenario_card_names  # noqa: E402

ONTO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "data")


def test_scenario_card_names_ordered_dedup():
    spec = json.load(open("scenarios/lindblum_impulse.json", encoding="utf-8"))
    names = scenario_card_names(spec)
    assert names[0] == "Mountain" and "Mage Siege" in names
    assert len(names) == len(set(names))


def test_citations_from_graph():
    citer = Citer(os.path.join(ONTO_DIR, "cr_mapping.json"),
                  os.path.join(ONTO_DIR, "cr_rules.json"))
    rec = {"name": "Fake Season", "alternateMode": None, "nodes": [
        {"id": "ab0", "kind": "R", "params": {"Event": "CreateToken"}},
        {"id": "X", "kind": "SVar", "api": "ReplaceToken", "params": {}},
        {"id": "kw0", "kind": "K", "keyword": "Trample"},
    ]}
    cites = citer.citations_for_record(rec)
    rules = {c["rule"] for c in cites}
    assert "614" in rules and "702.19" in rules


def test_layout_citation():
    citer = Citer(os.path.join(ONTO_DIR, "cr_mapping.json"),
                  os.path.join(ONTO_DIR, "cr_rules.json"))
    rec = {"name": "Adv", "alternateMode": "Adventure", "nodes": []}
    cites = citer.citations_for_record(rec)
    assert cites and cites[0]["rule"] == "715"
