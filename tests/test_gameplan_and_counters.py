"""Golden tests for texture-based gameplans (control / ramp_aggro) and the
counter_spell answer class."""
from cardguru.answers import evaluate_answer, _counter_target_legal
from cardguru.deck import detect_gameplan


def _profile(**kw):
    base = {"name": "T", "types": "Instant", "mv": 7, "colors": {"U", "R", "W"},
            "uncounterable": False, "is_creature": False, "is_land": False,
            "hexproof": False, "shroud": False, "ward": None,
            "indestructible": False, "toughness": None, "pt_is_cda": False,
            "token_scripts": [], "protection": []}
    base.update(kw)
    return base


def test_hard_counter_works():
    v = evaluate_answer("counter_spell", {}, {"ValidTgts": "Card"}, _profile())
    assert v["works"] is True


def test_annul_style_hits_artifact_not_instant():
    params = {"ValidTgts": "Artifact,Enchantment"}
    art = _profile(types="Artifact", mv=3, colors={"R"})
    assert evaluate_answer("counter_spell", {}, params, art)["works"] is True
    inst = _profile(types="Instant")
    assert evaluate_answer("counter_spell", {}, params, inst)["works"] is False


def test_mv_gates():
    ge4 = {"ValidTgts": "Card.cmcGE4"}
    assert evaluate_answer("counter_spell", {}, ge4, _profile(mv=7))["works"] is True
    assert evaluate_answer("counter_spell", {}, ge4, _profile(mv=3))["works"] is False
    eq2 = {"ValidTgts": "Card.cmcEQ2"}
    assert evaluate_answer("counter_spell", {}, eq2, _profile(mv=2))["works"] is True
    assert evaluate_answer("counter_spell", {}, eq2, _profile(mv=7))["works"] is False


def test_color_restricted_counter():
    params = {"ValidTgts": "Card.Red,Card.Green"}
    assert evaluate_answer("counter_spell", {}, params,
                           _profile(colors={"R"}))["works"] is True
    assert evaluate_answer("counter_spell", {}, params,
                           _profile(colors={"U", "B"}))["works"] is False


def test_soft_counter_conditional():
    v = evaluate_answer("counter_spell", {},
                        {"ValidTgts": "Card", "UnlessCost": "2"}, _profile())
    assert v["works"] is None


def test_uncounterable_threat_blocks():
    v = evaluate_answer("counter_spell", {}, {"ValidTgts": "Card"},
                        _profile(uncounterable=True))
    assert v["works"] is False


def test_unknown_condition_is_conditional():
    assert _counter_target_legal("Card.targetsYou", _profile()) is None


def test_control_gameplan_from_texture():
    # a pile of answers with few creatures reads control even with weak hooks
    plan = detect_gameplan({"self_mill": 4},
                           {"nonland": 37, "creatures": 6,
                            "interaction": 16, "ramp": 4})
    assert plan == "control"


def test_ramp_aggro_gameplan_from_texture():
    plan = detect_gameplan({"puts_counters": 4},
                           {"nonland": 38, "creatures": 31,
                            "interaction": 0, "ramp": 11})
    assert plan == "ramp_aggro"


def test_hook_plans_win_when_texture_thin():
    # a 12-copy disruptive_etb core is tempo regardless of modest interaction
    plan = detect_gameplan({"disruptive_etb": 12},
                           {"nonland": 32, "creatures": 22,
                            "interaction": 8, "ramp": 0})
    assert plan == "tempo"


def test_recursive_threat_demotes_death_removal():
    prof = _profile(types="Enchantment Creature", is_creature=True,
                    toughness=3, recursive=True)
    v = evaluate_answer("destroy_target", {}, {"ValidTgts": "Creature"}, prof)
    assert v["works"] is None
    assert any("prefer an exile" in r for r in v["reasons"])


def test_exile_rider_beats_recursion():
    prof = _profile(types="Enchantment Creature", is_creature=True,
                    toughness=3, recursive=True)
    v = evaluate_answer("damage_target", {},
                        {"ValidTgts": "Creature", "NumDmg": "5",
                         "ReplaceDyingDefined": "Targeted"}, prof)
    assert v["works"] is True
    assert any("exile rider" in r for r in v["reasons"])


def test_exile_class_annotated_vs_recursion():
    prof = _profile(types="Creature", is_creature=True, recursive=True)
    v = evaluate_answer("exile_target", {}, {"ValidTgts": "Creature"}, prof)
    assert v["works"] is True
    assert any("denies its return" in r for r in v["reasons"])


def test_stack_window_contests():
    from cardguru.intuition import stack_window_contests
    granter = {"name": "Granter", "nodes": [
        {"id": "e", "kind": "SVar", "api": "Effect",
         "params": {"ReplacementEffects": "AntiMagic"}}]}
    selfu = {"name": "SelfU", "nodes": [
        {"id": "r", "kind": "R",
         "params": {"Event": "Counter", "Layer": "CantHappen",
                    "ValidCard": "Card.Self"}}]}
    by = {"Granter": granter, "SelfU": selfu}
    out = stack_window_contests(by, [("Granter", 1), ("SelfU", 3)])
    assert out["closers"] == [{"card": "Granter", "count": 1}]
    assert out["self_uncounterable"] == [{"card": "SelfU", "count": 3}]


# ---------------------------------------------------- battlefield legality

def _prof(**kw):
    base = {"types": "Creature Cat", "keywords": {"Flash"}, "power": 4,
            "toughness": 3, "mv": 4, "colors": {"U"}, "protection": [],
            "hexproof": False, "shroud": False, "indestructible": False,
            "ward": None}
    base.update(kw)
    return base


def test_flying_restriction_excludes_ground_creature():
    from cardguru.answers import _battlefield_target_legal
    assert _battlefield_target_legal("Creature.withFlying", _prof()) is False
    assert _battlefield_target_legal(
        "Creature.withFlying", _prof(keywords={"Flying"})) is True


def test_plus_conjunction_and_or_alternatives():
    from cardguru.answers import _battlefield_target_legal
    # Arbor Colossus: fight only a flyer the opponent controls
    assert _battlefield_target_legal(
        "Creature.OppCtrl+withFlying", _prof()) is False
    # Airship Crash: an enchantment creature is hit via the Enchantment leg
    assert _battlefield_target_legal(
        "Artifact,Enchantment,Creature.withFlying",
        _prof(types="Enchantment Creature Cat")) is True


def test_power_gate_and_situational():
    from cardguru.answers import _battlefield_target_legal
    assert _battlefield_target_legal("Creature.powerGE4", _prof()) is True
    assert _battlefield_target_legal("Creature.powerLE2", _prof()) is False
    # tapped/attacking depend on game state, not the card
    assert _battlefield_target_legal("Creature.tapped", _prof()) is None


def test_wrong_type_head_excluded():
    from cardguru.answers import _battlefield_target_legal
    assert _battlefield_target_legal("Artifact,Enchantment", _prof()) is False
    assert _battlefield_target_legal("Creature.YouCtrl", _prof()) is False


def test_evaluate_answer_applies_battlefield_legality():
    from cardguru.answers import evaluate_answer
    verdict = evaluate_answer(
        "destroy_target", {"name": "Aerial Predation", "manaCost": "1 G"},
        {"ValidTgts": "Creature.withFlying"}, _prof())
    assert verdict["works"] is False
    assert "targeting-illegal" in verdict["reasons"][0]
