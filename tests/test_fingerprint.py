"""Deck-fingerprint goldens on the live Standard Dimir Midrange list.

The claim under test: projecting the KG onto one deck and running
centrality + sole-provider analysis points at what a human expert calls the
deck's engine (Enduring Curiosity, fed in combat by cheap evasive bodies),
and the break plan prefers history-clean cuts over rental removal.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru.index import SearchIndex  # noqa: E402

DATASET = os.environ.get("CARDGURU_DATASET", "data/dataset.jsonl.gz")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

pytestmark = pytest.mark.skipif(
    not os.path.exists(DATASET), reason=f"dataset not built at {DATASET}")


@pytest.fixture(scope="module")
def by_name():
    idx = SearchIndex.load(DATASET)
    out = {}
    for r in idx.records:
        out.setdefault(r.get("name"), r)
    return out


@pytest.fixture(scope="module")
def dimir_fp(by_name):
    from cardguru.deck import parse_decklist
    from cardguru.fingerprint import build_fingerprint
    with open(os.path.join(ROOT, "decks", "dimir_deck.txt")) as f:
        decklist = parse_decklist(f.read())
    return build_fingerprint(by_name, decklist), decklist


def test_top_linchpin_is_the_draw_engine(dimir_fp):
    fp, _ = dimir_fp
    assert fp["linchpins"][0][0] == "Enduring Curiosity"


def test_spine_is_combat_damage_fed(dimir_fp):
    fp, _ = dimir_fp
    top = fp["spine"][0]
    assert top["family"] == "combat_damage_matters"
    assert "Enduring Curiosity" in top["payoffs"]
    assert "Deep-Cavern Bat" in top["enablers"]


def test_self_recursion_is_not_a_reanimator_hook(dimir_fp):
    fp, _ = dimir_fp
    assert not any(e["via"].startswith("reanimator") for e in fp["edges"])


def test_break_plan_prefers_history_clean_cut(by_name, dimir_fp):
    from cardguru.fingerprint import break_plan
    fp, _ = dimir_fp
    plan = break_plan(by_name, fp, top=1)[0]
    assert plan["card"] == "Enduring Curiosity"
    assert plan["preferred"].startswith("stack")
    assert any("destroy is rental" in a["note"] for a in plan["avoid"])


def test_kaito_break_plan_derives_the_edict(by_name, dimir_fp):
    from cardguru.fingerprint import break_plan
    fp, _ = dimir_fp
    plans = break_plan(by_name, fp, top=8)
    kaito = next(p for p in plans if p["card"].startswith("Kaito"))
    assert kaito["preferred"].startswith("edict")
    assert any("GUARANTEED" in w["note"] for w in kaito["windows"])
    assert any("phase-shifter" in a["note"] for a in kaito["avoid"])


@pytest.fixture(scope="module")
def jeskai_fp(by_name):
    from cardguru.deck import parse_decklist
    from cardguru.fingerprint import build_fingerprint
    with open(os.path.join(ROOT, "decks", "jeskai_deck.txt")) as f:
        decklist = parse_decklist(f.read())
    return build_fingerprint(by_name, decklist)


def test_jeskai_spine_is_the_lesson_count_engine(jeskai_fp):
    top = jeskai_fp["spine"][0]
    assert top["family"] == "scaling_lesson@graveyard"
    assert "Combustion Technique" in top["payoffs"]
    assert "Gran-Gran" in top["payoffs"]


def test_jeskai_resource_cut_is_graveyard_exile(jeskai_fp):
    cuts = jeskai_fp["resource_cuts"]
    assert cuts and cuts[0]["zone"] == "graveyard"
    assert "graveyard exile" in cuts[0]["note"]


def test_one_shot_spell_linchpin_has_no_battlefield_window(by_name, jeskai_fp):
    from cardguru.fingerprint import break_plan
    plans = break_plan(by_name, jeskai_fp, top=3)
    combustion = next(p for p in plans if p["card"] == "Combustion Technique")
    assert any("never a permanent" in a["note"] for a in combustion["avoid"])
