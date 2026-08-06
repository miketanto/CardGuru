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
