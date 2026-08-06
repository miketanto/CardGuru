import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru.adjudicate import validate_scenario  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "corpus"))
from parse_mage_tests import parse_method  # noqa: E402


def test_shipped_scenarios_validate():
    for dirpath, _dirs, files in os.walk("scenarios"):
        for fn in files:
            if fn.endswith(".json"):
                with open(os.path.join(dirpath, fn), encoding="utf-8") as f:
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


from cardguru.answers import evaluate_answer, threat_profile  # noqa: E402
from cardguru.recommend import detect_hooks  # noqa: E402


def _fake_threat(kws=(), pt="4/5", cost="2 B B"):
    return {"name": "T", "types": "Creature", "pt": pt, "manaCost": cost,
            "nodes": [{"id": f"kw{i}", "kind": "K", "keyword": k.split(":")[0],
                       "raw": k} for i, k in enumerate(kws)]}


def test_threat_profile_reads_keyword_nodes():
    p = threat_profile(_fake_threat(["Indestructible", "Ward:2"]))
    assert p["indestructible"] and p["ward"] == "Ward:2" and p["toughness"] == 5


def test_answer_verdicts():
    plain = threat_profile(_fake_threat())
    indestructible = threat_profile(_fake_threat(["Indestructible"]))
    hexproof = threat_profile(_fake_threat(["Hexproof"]))
    bolt = {"name": "Bolt", "manaCost": "R"}
    assert evaluate_answer("damage_target", bolt, {"NumDmg": "3"}, plain)["works"] is False
    assert evaluate_answer("damage_target", bolt, {"NumDmg": "5"}, plain)["works"] is True
    assert evaluate_answer("destroy_target", bolt, {}, indestructible)["works"] is False
    assert evaluate_answer("exile_target", bolt, {}, indestructible)["works"] is True
    assert evaluate_answer("destroy_target", bolt, {}, hexproof)["works"] is False
    assert evaluate_answer("edict_sacrifice", bolt, {}, hexproof)["works"] is None


from cardguru.answers import (ability_dependence, token_is_ability_defined,  # noqa: E402
                              _class_queries, find_answers)


CONSTRUCT_TOKEN = {"name": "Construct Token", "pt": "0/0", "nodes": [
    {"id": "s0", "kind": "S", "params": {"Mode": "Continuous",
                                         "Affected": "Card.Self",
                                         "AddPower": "X", "AddToughness": "X"}}]}


def test_token_is_ability_defined():
    assert token_is_ability_defined(CONSTRUCT_TOKEN)
    assert not token_is_ability_defined({"name": "Soldier", "pt": "1/1", "nodes": []})
    assert not token_is_ability_defined({"name": "Vanilla 0/0", "pt": "0/0", "nodes": []})


def test_ability_dependence_via_token_scripts():
    saga_like = {"name": "Saga-like", "types": "Enchantment Land", "pt": "",
                 "manaCost": "no cost", "nodes": [
                     {"id": "a0", "kind": "A",
                      "params": {"TokenScript": "c_0_0_construct"}}]}
    prof = threat_profile(saga_like)
    assert prof["is_land"] and not prof["is_creature"]
    assert prof["token_scripts"] == ["c_0_0_construct"]
    deps = ability_dependence(prof, {"c_0_0_construct": CONSTRUCT_TOKEN})
    assert deps and "704.5f" in deps[0]
    assert ability_dependence(prof, {}) == []


def test_class_queries_are_type_aware():
    land = threat_profile({"name": "L", "types": "Land", "pt": "",
                           "manaCost": "no cost", "nodes": []})
    creature = threat_profile(_fake_threat())
    lq = _class_queries(land)
    # creature-only classes must not apply to a land threat
    assert "damage_target" not in lq and "destroy_all" not in lq
    assert "Land" in lq["destroy_target"]["node"]["params"]["ValidTgts"]["regex"]
    cq = _class_queries(creature)
    assert "damage_target" in cq and "destroy_all" in cq


def test_ability_removal_verdicts():
    prof = {"name": "T", "ability_dependent": ["dies as 0/0"], "shroud": False,
            "hexproof": False, "indestructible": False, "ward": None,
            "protection": [], "toughness": None}
    mass = evaluate_answer("ability_removal", {"name": "Dress Down"},
                           {"Affected": "Creature"}, prof)
    assert mass["works"] is True and mass["reasons"] == ["dies as 0/0"]
    single = evaluate_answer("ability_removal", {"name": "Frozen in Ice"},
                             {"Affected": "Creature.EnchantedBy"}, prof)
    assert single["works"] is True and any("single-target" in r
                                          for r in single["reasons"])
    setpt = evaluate_answer("ability_removal", {"name": "Witness Protection"},
                            {"Affected": "Creature.EnchantedBy",
                             "SetPower": "1", "SetToughness": "1"}, prof)
    assert setpt["works"] is None and any("does not die" in r
                                         for r in setpt["reasons"])


class _FakeIdx:
    def __init__(self, records):
        self._records = records

    def search(self, query):
        # trivially return every record; find_answers filters/evaluates
        return [{"record": r} for r in self._records]


def test_find_answers_handles_mode_only_query():
    threat = {"name": "Saga-like", "types": "Enchantment Land", "pt": "",
              "manaCost": "no cost", "nodes": [
                  {"id": "a0", "kind": "A",
                   "params": {"TokenScript": "c_0_0_construct"}}]}
    dress = {"name": "Dress Downish", "manaCost": "1 U", "types": "Enchantment",
             "nodes": [{"id": "s0", "kind": "S",
                        "params": {"Mode": "Continuous", "Affected": "Creature",
                                   "RemoveAllAbilities": "True"}}]}
    res = find_answers(_FakeIdx([dress]), threat,
                       token_scripts={"c_0_0_construct": CONSTRUCT_TOKEN})
    ar = res["classes"]["ability_removal"]
    assert ar["working"] == 1
    assert ar["top"][0]["card"] == "Dress Downish"
    assert any("704.5f" in r for r in ar["top"][0]["reasons"])


def test_detect_hooks_panharmonicon():
    rec = {"name": "Teysa-like", "nodes": [
        {"id": "s0", "kind": "S", "params": {"Mode": "Panharmonicon",
                                             "Origin": "Battlefield",
                                             "Destination": "Graveyard"}}]}
    assert "amplifies_death_triggers" in detect_hooks(rec)


def test_detect_hooks_expanded():
    spellslinger = {"name": "S", "nodes": [
        {"id": "t0", "kind": "T", "params": {"Mode": "SpellCast",
                                             "ValidCard": "Instant,Sorcery"}}]}
    assert "spellslinger" in detect_hooks(spellslinger)
    gitrog = {"name": "G", "nodes": [
        {"id": "t0", "kind": "T", "params": {"Mode": "ChangesZoneAll",
                                             "ValidCards": "Land.YouOwn",
                                             "Destination": "Graveyard"}}]}
    assert "landfall" in detect_hooks(gitrog)
    isshin = {"name": "I", "nodes": [
        {"id": "s0", "kind": "S", "params": {"Mode": "Panharmonicon",
                                             "ValidMode": "Attacks,AttackersDeclared"}}]}
    assert "amplifies_attack_triggers" in detect_hooks(isshin)
    muldrotha = {"name": "M", "nodes": [
        {"id": "s0", "kind": "S", "params": {"Mode": "Continuous",
                                             "MayPlay": "True",
                                             "AffectedZone": "Graveyard"}}]}
    assert "plays_from_graveyard" in detect_hooks(muldrotha)


from cardguru.deck import (cross_synergy, deck_shape, mana_value,  # noqa: E402
                           parse_decklist)


from cardguru.deck import find_loops  # noqa: E402
from cardguru.goldfish import simulate  # noqa: E402


def test_find_loops_two_cycle():
    edges = [
        {"src": "A", "dst": "B", "hook": "h1", "class": "c1"},
        {"src": "B", "dst": "A", "hook": "h2", "class": "c2"},
        {"src": "A", "dst": "C", "hook": "h1", "class": "c1"},
    ]
    loops = find_loops(edges)
    assert len(loops) == 1
    assert set(loops[0]["cards"]) == {"A", "B"}
    assert len(loops[0]["edges"]) == 2


def test_goldfish_all_lands_deck():
    mountain = {"name": "Mountain", "types": "Basic Land Mountain",
                "oracle": "{T}: Add {R}.", "edges": [], "nodes": []}
    cmdr = {"name": "C", "types": "Legendary Creature", "manaCost": "1 R",
            "edges": [], "nodes": []}
    by_name = {"Mountain": mountain}
    gf = simulate(by_name, cmdr, [("Mountain", 40)], iterations=200, turns=3)
    # a 100%-land deck always hits drops and casts the MV-2 commander on T2
    assert gf["land_drop_pct"][1] == 100.0
    assert gf["commander_by_turn_pct"][2] == 100.0
    assert gf["screw_rate_pct"] == 0.0


def test_mana_value():
    assert mana_value("2 B B") == 4
    assert mana_value("X R") == 1
    assert mana_value("no cost") is None
    assert mana_value(None) is None


def test_deck_shape_flags():
    bolt = {"name": "Bolt", "types": "Instant", "manaCost": "R", "oracle": "",
            "edges": [], "nodes": [
                {"id": "a0", "kind": "A", "apiKind": "SP", "api": "DealDamage",
                 "params": {"ValidTgts": "Any", "NumDmg": "3"}}]}
    mountain = {"name": "Mountain", "types": "Basic Land Mountain",
                "oracle": "{T}: Add {R}.", "edges": [], "nodes": []}
    cmdr = {"name": "C", "types": "Legendary Creature", "manaCost": "1 R",
            "edges": [], "nodes": []}
    by_name = {r["name"]: r for r in (bolt, mountain, cmdr)}
    shape = deck_shape(by_name, cmdr, [("Bolt", 4), ("Mountain", 10)])
    assert shape["curve"] == {1: 4}
    assert shape["lands"] == 10 and shape["sources"]["R"] == 10
    assert shape["pips"]["R"] == 4
    assert shape["gameplan"] == "generic"     # no hooks anywhere
    # interaction quotas deficient in a 4-spell deck; ramp has NO quota
    # (mana sufficiency is measured by the goldfish sim, not quoted)
    assert any("card_draw" in f for f in shape["flags"])
    assert not any("ramp" in f for f in shape["flags"])


def test_answer_windows_tinker_shape():
    """The golden Tinker intuition: counter it or answer the output - the
    sorcery itself is never a permanent."""
    from cardguru.intuition import answer_windows
    tinker = {"name": "Tinker-like", "types": "Sorcery", "manaCost": "2 U",
              "edges": [], "nodes": [
                  {"id": "a0", "kind": "A", "apiKind": "SP", "api": "ChangeZone",
                   "params": {"Origin": "Library", "Destination": "Battlefield",
                              "ChangeType": "Artifact"}}]}
    w = answer_windows(tinker)
    open_names = {x["window"] for x in w["windows"]}
    assert "stack" in open_names            # counterable
    assert "output" in open_names           # kill what it fetches
    assert "preempt" in open_names          # search hate
    assert "permanent" not in open_names    # never removable itself
    assert any(x["window"] == "permanent" for x in w["closed"])


def test_axis_matching_high_noon_shape():
    """The golden High Noon intuition: a cast-scaling deck is throttled by a
    CantBeCast rate cap."""
    from cardguru.intuition import AXES, axis_profile
    payoff = {"name": "Prowessy", "types": "Creature", "manaCost": "R",
              "edges": [], "nodes": [
                  {"id": "t0", "kind": "T",
                   "params": {"Mode": "SpellCast", "ValidCard": "Card"}}]}
    high_noon = {"name": "Noonish", "types": "Enchantment", "manaCost": "1 W",
                 "edges": [], "nodes": [
                     {"id": "s0", "kind": "S", "mode": "CantBeCast",
                      "params": {"Mode": "CantBeCast", "ValidCard": "Card",
                                 "NumLimitEachTurn": "1"}}]}
    by_name = {r["name"]: r for r in (payoff, high_noon)}
    prof = axis_profile(by_name, payoff, [("Prowessy", 4)])
    assert prof and prof[0]["axis"] == "casting_spells"
    from cardguru.intuition import _matches
    q = AXES["casting_spells"]["hate"]["cast_rate_caps"]
    assert _matches(high_noon, q)
    assert not _matches(payoff, q)


def test_cuts_protects_mana_rocks_and_deficient_roles():
    from cardguru.deck import cuts
    rock = {"name": "Rock", "types": "Artifact", "manaCost": "1",
            "edges": [], "nodes": [
                {"id": "a0", "kind": "A", "apiKind": "AB", "api": "Mana",
                 "params": {"Cost": "T", "Produced": "C"}}]}
    vanilla = {"name": "Bear", "types": "Creature", "manaCost": "1 G",
               "edges": [], "nodes": []}
    cmdr = {"name": "C", "types": "Legendary Creature", "manaCost": "2 G",
            "edges": [], "nodes": []}
    by_name = {r["name"]: r for r in (rock, vanilla, cmdr)}
    shape = {"quotas": {"card_draw": 8}, "effective_roles": {"card_draw": 0}}
    rows = cuts(by_name, cmdr, [("Rock", 1), ("Bear", 1)], [], shape)
    by_card = {r["card"]: r for r in rows}
    assert any("PROTECTED" in x for x in by_card["Rock"]["reasons"])
    assert not any("PROTECTED" in x for x in by_card["Bear"]["reasons"])
    assert by_card["Bear"]["cut_score"] > by_card["Rock"]["cut_score"]


def test_detect_roles_engine_vs_oneshot():
    from cardguru.deck import detect_roles
    reaper = {"name": "Reaper-like", "types": "Creature Zombie",
              "manaCost": "2 B", "edges": [], "nodes": [
                  {"id": "t0", "kind": "T",
                   "params": {"Mode": "ChangesZone", "Origin": "Battlefield",
                              "Destination": "Graveyard"}},
                  {"id": "d0", "kind": "SVar", "api": "Draw",
                   "params": {"NumCards": "1"}}]}
    divination = {"name": "Div", "types": "Sorcery", "manaCost": "2 U",
                  "edges": [], "nodes": [
                      {"id": "a0", "kind": "A", "apiKind": "SP", "api": "Draw",
                       "params": {"NumCards": "2"}}]}
    assert detect_roles(reaper).get("card_draw") == "engine"
    assert detect_roles(divination).get("card_draw") == "one_shot"


def test_cross_synergy_finds_non_commander_pairs():
    token_maker = {"name": "Maker", "types": "Enchantment", "edges": [], "nodes": [
        {"id": "t0", "kind": "T", "params": {"Mode": "Phase"}},
        {"id": "ab0", "kind": "SVar", "api": "Token", "params": {}}]}
    doubler = {"name": "Doubler", "types": "Enchantment", "edges": [
        {"src": "r0", "dst": "d0", "type": "ReplaceWith"}], "nodes": [
        {"id": "r0", "kind": "R", "params": {"Event": "CreateToken"}},
        {"id": "d0", "kind": "SVar", "api": "ReplaceToken", "params": {}}]}
    commander = {"name": "Cmdr", "types": "Legendary Creature", "edges": [],
                 "nodes": []}
    by_name = {r["name"]: r for r in (token_maker, doubler, commander)}
    cs = cross_synergy(by_name, commander, [("Maker", 1), ("Doubler", 1)])
    # the commander has no hooks, but Maker's makes_tokens hook finds Doubler
    assert any(e["src"] == "Maker" and e["dst"] == "Doubler"
               and e["class"] == "token_doubling" for e in cs["edges"])
    assert "Cmdr" in cs["isolated"]


def test_parse_decklist_formats():
    text = """// comment
1 Sol Ring
2x Swamp
Lightning Bolt
1 Arcane Signet (C21) 263

Sideboard
1 Pithing Needle
"""
    cards = parse_decklist(text)
    assert ("Sol Ring", 1) in cards and ("Swamp", 2) in cards
    assert ("Lightning Bolt", 1) in cards
    assert any(n == "Arcane Signet" for n, _c in cards)
    assert not any(n == "Pithing Needle" for n, _c in cards)
