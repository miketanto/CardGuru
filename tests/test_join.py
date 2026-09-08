"""Join-report tests. Offline only — the network paths (bulk download, fuzzy
alias resolution) are not exercised here by design."""
import gzip
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru import cardstore as cs  # noqa: E402
from cardguru import join as jn  # noqa: E402

SCRYFALL = [
    {"oracle_id": "oid-bolt", "name": "Lightning Bolt", "color_identity": ["R"]},
    {"oracle_id": "oid-fireice", "name": "Fire // Ice", "color_identity": ["U", "R"],
     "card_faces": [{"name": "Fire"}, {"name": "Ice"}]},
]

# One face per join class: card, face, alchemy-rebalance, absent.
FORGE_FACES = [
    {"name": "Lightning Bolt", "types": "Instant", "nodes": [], "edges": []},
    {"name": "Fire", "alternateMode": "Split", "types": "Instant",
     "nodes": [], "edges": []},
    {"name": "A-Goldspan Dragon", "types": "Legendary Creature",
     "nodes": [], "edges": []},
    {"name": "Some Upcoming Card", "types": "Sorcery", "nodes": [], "edges": []},
]


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    d = tmp_path_factory.mktemp("join")
    src = os.path.join(d, "scryfall.jsonl.gz")
    with gzip.open(src, "wt", encoding="utf-8") as f:
        for rec in SCRYFALL:
            f.write(json.dumps(rec) + "\n")
    db = os.path.join(d, "cards.sqlite")
    cs.build(src, db, snapshot_date="2026-08-07T00:00:00Z")

    dataset = os.path.join(d, "dataset.jsonl.gz")
    with gzip.open(dataset, "wt", encoding="utf-8") as f:
        f.write(json.dumps({"_meta": {"source_pin": "670429bf", "format": 1}}) + "\n")
        for rec in FORGE_FACES:
            f.write(json.dumps(rec) + "\n")
    return dataset, cs.CardStore(db)


def test_report_classifies_every_face(built):
    dataset, store = built
    rep = jn.report(dataset, store)
    assert rep["total_faces"] == 4
    assert rep["matched"] == 2
    assert rep["by_class"] == {"card": 1, "face": 1,
                               "alchemy-rebalance": 1, "absent": 1}


def test_report_stamps_both_version_axes(built):
    """Forge pin and Scryfall snapshot are independent axes (architecture §4)."""
    dataset, store = built
    rep = jn.report(dataset, store)
    assert rep["forge_pin"] == "670429bf"
    assert rep["scryfall_snapshot"] == "2026-08-07T00:00:00Z"


def test_misses_carry_their_class(built):
    dataset, store = built
    rep = jn.report(dataset, store)
    by_name = {m["name"]: m["class"] for m in rep["misses"]}
    assert by_name == {"A-Goldspan Dragon": "alchemy-rebalance",
                       "Some Upcoming Card": "absent"}


def test_match_rate(built):
    dataset, store = built
    assert jn.report(dataset, store)["match_rate"] == 0.5


def test_color_identity_is_lowercased(built):
    """Scryfall returns 'UR'; recommend.CI_ORDER is 'wubrg'. Emitting uppercase
    silently renders every commander as colorless."""
    from cardguru.cli import load_color_identity

    _dataset, store = built
    ci, printings, src = load_color_identity(None, db_path=store.path)
    assert ci["Fire // Ice"] == "ur"
    assert ci["Lightning Bolt"] == "r"
    assert printings == {}, "oracle-cards carries no printing counts"
    assert src == store.path


def test_load_color_identity_requires_a_source(tmp_path):
    from cardguru.cli import load_color_identity

    with pytest.raises(SystemExit):
        load_color_identity(None, db_path=str(tmp_path / "missing.sqlite"))


def test_load_aliases_ignores_unconfirmed(tmp_path):
    p = tmp_path / "aliases.json"
    p.write_text(json.dumps({"aliases": [
        {"forge": "a", "scryfall": "b", "status": "confirmed"},
        {"forge": "c", "scryfall": "d", "status": "candidate"},
        {"forge": "e", "scryfall": "f"},
    ]}))
    confirmed, _ = cs.load_aliases(str(p))
    assert [a["forge"] for a in confirmed] == ["a"]


def test_load_aliases_absent_file_is_fine():
    assert cs.load_aliases("/no/such/aliases.json") == ([], [])
