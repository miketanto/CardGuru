import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "benchmark"))

from llm_bridge import YieldGate  # noqa: E402


def req(kind="priority", turn=5, phase="Upkeep", active="B",
        enemy_creatures=1, life=20):
    return {
        "kind": kind, "turn": turn, "phase": phase, "active": active,
        "state": {
            "A": {"life": life, "battlefield": []},
            "B": {"life": 20, "battlefield": [
                {"name": "Bear", "power": 2, "toughness": 2}
            ] * enemy_creatures + [{"name": "Forest"}]},
        },
    }


def test_no_yield_by_default():
    assert not YieldGate().covers(req())


def test_invalid_until_ignored():
    g = YieldGate()
    assert g.set("forever", req()) is None
    assert not g.covers(req())


def test_my_turn_covers_their_turn_and_wakes_at_my_main():
    g = YieldGate()
    assert g.set("my_turn", req(turn=5, active="B")) == "my_turn"
    assert g.covers(req(turn=5, phase="End Turn", active="B"))
    assert g.covers(req(turn=6, phase="Upkeep", active="A"))
    assert not g.covers(req(turn=6, phase="Precombat Main", active="A"))
    # gate is spent after waking
    assert not g.covers(req(turn=6, phase="Precombat Main", active="A"))


def test_end_of_turn_expires_on_turn_change():
    g = YieldGate()
    g.set("end_of_turn", req(turn=5, phase="Postcombat Main", active="A"))
    assert g.covers(req(turn=5, phase="End Turn", active="A"))
    assert not g.covers(req(turn=6, phase="Upkeep", active="B"))


def test_breaks_on_enemy_creature_gain():
    g = YieldGate()
    g.set("my_turn", req(enemy_creatures=1))
    assert not g.covers(req(enemy_creatures=2))


def test_breaks_on_life_drop():
    g = YieldGate()
    g.set("my_turn", req(life=20))
    assert not g.covers(req(life=17))


def test_breaks_on_non_priority():
    g = YieldGate()
    g.set("my_turn", req())
    assert not g.covers(req(kind="blockers"))
    # and the yield is cancelled, not just skipped
    assert not g.covers(req())


def test_survives_enemy_creature_death():
    g = YieldGate()
    g.set("my_turn", req(enemy_creatures=2))
    assert g.covers(req(enemy_creatures=1))
