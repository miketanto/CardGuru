"""Integration goldens against a built dataset (skipped when absent).

Build first:
  python -m cardguru build --cardsfolder <forge>/forge-gui/res/cardsfolder \
      --canonical <index.json> --out data/dataset.jsonl.gz
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru.index import SearchIndex  # noqa: E402

DATASET = os.environ.get("CARDGURU_DATASET", "data/dataset.jsonl.gz")
QUERIES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "queries")

pytestmark = pytest.mark.skipif(
    not os.path.exists(DATASET), reason=f"dataset not built at {DATASET}")


@pytest.fixture(scope="module")
def idx():
    return SearchIndex.load(DATASET)


def run_query_file(idx, fname):
    with open(os.path.join(QUERIES, fname), encoding="utf-8") as f:
        spec = json.load(f)
    return {h["record"]["name"] for h in idx.search(spec["query"])}


def test_q1_goldens(idx):
    names = run_query_file(idx, "q1_combat_damage_token.json")
    assert "Ragavan, Nimble Pilferer" in names
    assert "Old Gnawbone" in names
    assert "Grim Hireling" in names
    assert "Brazen Freebooter" not in names      # ETB trigger, not combat damage
    assert "Grizzly Bears" not in names
    assert len(names) > 50


def test_q2_goldens(idx):
    names = run_query_file(idx, "q2_impulse_exile.json")
    assert "Ragavan, Nimble Pilferer" in names
    assert "Light Up the Stage" in names
    assert "Outpost Siege" in names
    assert len(names) > 100


def test_q3_goldens(idx):
    names = run_query_file(idx, "q3_sac_creature_mana.json")
    assert "Phyrexian Altar" in names
    assert "Ashnod's Altar" in names
    assert "Blood Pet" in names                  # self-sac creature
    assert "Dark Ritual" not in names
    assert len(names) > 20


def test_saga_chapter_query(idx):
    """Structural query impossible in Scryfall: saga whose chapter chain
    reaches a ChangeZone effect fetching from library to battlefield."""
    q = {"chain": {"from": {"kind": "K", "keyword": "Chapter"},
                   "to": {"api": "ChangeZone",
                          "params": {"Origin": "Library",
                                     "Destination": "Battlefield"}}}}
    names = {h["record"]["name"] for h in idx.search(q)}
    assert "Urza's Saga" in names


def test_evidence_paths_resolve(idx):
    with open(os.path.join(QUERIES, "q1_combat_damage_token.json"), encoding="utf-8") as f:
        spec = json.load(f)
    hit = next(iter(idx.search(spec["query"], limit=1)))
    ids = {n["id"] for n in hit["record"]["nodes"]}
    for ev in hit["evidence"]:
        assert set(ev["path"]) <= ids
