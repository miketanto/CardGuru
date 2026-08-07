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
