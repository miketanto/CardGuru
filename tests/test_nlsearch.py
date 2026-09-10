"""NL-ish search: parsing, and the claim that a new game costs a profile only."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru.nlsearch import (GameProfile, build_lexicon,  # noqa: E402
                               load_corpus, parse, run, similarity, stems)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RIFTBOUND_FIXTURE = os.path.join(ROOT, "tests/fixtures/riftbound_sample.json")
MTG_CORPUS = os.path.join(ROOT, "eval/rulesguru/cards_index.json")


@pytest.fixture(scope="module")
def riftbound():
    profile = GameProfile.load(os.path.join(ROOT, "profiles/riftbound.json"))
    corpus = load_corpus(RIFTBOUND_FIXTURE)
    return profile, corpus, build_lexicon(corpus, profile)


@pytest.fixture(scope="module")
def mtg():
    profile = GameProfile.load(os.path.join(ROOT, "profiles/mtg.json"))
    corpus = load_corpus(MTG_CORPUS)
    return profile, corpus, build_lexicon(corpus, profile)


# ------------------------------------------------------------ helpers

def test_stems_and_similarity():
    assert "cost" in list(stems("costing"))
    assert "unit" in list(stems("units"))
    assert similarity("flying", "flyng") > 0.8       # typo
    assert similarity("flying", "trample") < 0.8     # unrelated


# ------------------------------------------------ lexicon is mined, not authored

def test_lexicon_comes_from_the_corpus(riftbound):
    _, _, lex = riftbound
    # Nothing in profiles/riftbound.json names "calm" or "ambush" — they are
    # in the lexicon only because they appear in the card dump.
    profile_text = open(os.path.join(ROOT, "profiles/riftbound.json")).read()
    assert "Calm" not in profile_text and "Ambush" not in profile_text
    assert "calm" in lex.terms and "ambush" in lex.terms
    assert lex.terms["calm"][0][0] == "domain"
    assert lex.terms["ambush"][0][0] == "keyword"


def test_new_game_needs_no_new_code(riftbound):
    """The question that started this: same engine, different game, zero code."""
    profile, corpus, lex = riftbound
    res = run("Card in Calm that has ambush", corpus, profile, lex)
    assert res["interpretation"] == "domain = Calm AND keyword = Ambush"
    assert {c["name"] for c in res["results"]} == {"Fixture Scout", "Fixture Duelist"}


# --------------------------------------------------------------- grammar

def test_negation(riftbound):
    profile, corpus, lex = riftbound
    res = run("units with ambush not in calm", corpus, profile, lex)
    assert {c["name"] for c in res["results"]} == {"Fixture Raider", "Fixture Ambusher"}


def test_disjunction(riftbound):
    profile, corpus, lex = riftbound
    res = run("Fury or Chaos unit", corpus, profile, lex)
    assert "OR" in res["interpretation"]
    assert {c["name"] for c in res["results"]} == {"Fixture Raider", "Fixture Ambusher"}


@pytest.mark.parametrize("question,op,value", [
    ("cost 3 or less", "<=", 3),
    ("costing 3 or less", "<=", 3),
    ("cost at least 4", ">=", 4),
    ("cost more than 4", ">", 4),
    ("might 5 or more", ">=", 5),
])
def test_numeric_comparators(riftbound, question, op, value):
    _, _, lex = riftbound
    clauses = parse(question, lex).clauses
    numeric = [c for c in clauses if not isinstance(c, list) and c.kind == "numeric"]
    assert len(numeric) == 1
    assert (numeric[0].op, numeric[0].value) == (op, value)


def test_prepositions_steer_ambiguous_terms(mtg):
    """'in X' means colour; 'with X' means keyword — same word, two facets."""
    _, _, lex = mtg
    assert parse("in blue", lex).clauses[0].facet == "color"
    assert parse("with flash", lex).clauses[0].facet == "keyword"


# ----------------------------------------------------- honesty of the reading

def test_typo_is_corrected_but_flagged(mtg):
    profile, corpus, lex = mtg
    res = run("creature with flyng", corpus, profile, lex, limit=1)
    assert res["low_confidence"], "a fuzzy match must be reported, never silent"
    warn = res["low_confidence"][0]
    assert warn["span"] == "flyng" and warn["read_as"] == "keyword = Flying"
    assert warn["confidence"] < 1.0


def test_fuzzy_never_eats_a_neighbouring_word(mtg):
    """Regression: 'red creature' once fuzzy-matched 'creature' as a 2-word
    span and silently dropped the colour."""
    profile, corpus, lex = mtg
    res = run("red creature with power 4 or more", corpus, profile, lex, limit=1)
    assert "color = Red" in res["interpretation"]
    assert "type = Creature" in res["interpretation"]
    assert "power >= 4" in res["interpretation"]


def test_unrecognized_words_are_reported(mtg):
    profile, corpus, lex = mtg
    res = run("blue creature that goes bananas", corpus, profile, lex, limit=1)
    assert "bananas" in res["unparsed"]


# ------------------------------------------------------------ real-corpus end to end

def test_mtg_end_to_end(mtg):
    profile, corpus, lex = mtg
    res = run("card in blue that has flash", corpus, profile, lex, limit=100)
    assert res["interpretation"] == "color = Blue AND keyword = Flash"
    assert res["total"] > 10
    for card in res["results"]:
        assert "Blue" in card["colors"] and "Flash" in card["keywords"]


def test_corpus_loader_shapes(tmp_path):
    cards = [{"name": "A", "types": ["Unit"]}, {"name": "B", "types": ["Spell"]}]
    as_list = tmp_path / "l.json"
    as_list.write_text(json.dumps(cards))
    as_obj = tmp_path / "o.json"
    as_obj.write_text(json.dumps({c["name"]: c for c in cards}))
    as_jsonl = tmp_path / "j.jsonl"
    as_jsonl.write_text("\n".join(json.dumps(c) for c in cards))
    for path in (as_list, as_obj, as_jsonl):
        assert {c["name"] for c in load_corpus(str(path))} == {"A", "B"}


def test_null_alias_means_field_is_empty(mtg):
    """'colorless' is not a colour value — it is the absence of one."""
    profile, corpus, lex = mtg
    res = run("colorless artifact with cost 2", corpus, profile, lex, limit=100)
    assert "color is empty" in res["interpretation"]
    assert not res["unparsed"] and res["total"] > 0
    for card in res["results"]:
        assert not card["colors"] and card["manaValue"] == 2


def test_fuzzy_does_not_swallow_a_different_real_word(mtg):
    """Regression: 'create' fuzzy-matched the keyword 'Creature' at 0.857 and
    produced a confident-looking but wrong reading."""
    _, _, lex = mtg
    clauses = parse("cards that double the tokens you create", lex).clauses
    assert not any(getattr(c, "value", None) == "Creature" for c in clauses)


def test_structure_questions_fall_through_visibly(mtg):
    """Questions about card STRUCTURE are the query DSL's job. This layer must
    not answer them silently — the words it could not bind have to surface."""
    profile, corpus, lex = mtg
    for q in ["creatures that sacrifice a creature as a cost to add mana",
              "cards that let you play lands from your graveyard",
              "spells that counter target spell and nothing else"]:
        res = run(q, corpus, profile, lex, limit=1)
        assert res["unparsed"], f"{q!r} parsed as complete but is structural"
