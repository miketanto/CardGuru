"""Card store unit tests — synthetic Scryfall input, no built data required."""
import gzip
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru import cardstore as cs  # noqa: E402

# Each entry mirrors the shape of a real Scryfall oracle-cards record, trimmed
# to the fields the store reads. Names chosen to exercise the join classes.
SCRYFALL_FIXTURE = [
    {
        "oracle_id": "oid-bolt", "name": "Lightning Bolt", "layout": "normal",
        "mana_cost": "{R}", "cmc": 1.0, "type_line": "Instant",
        "oracle_text": "Lightning Bolt deals 3 damage to any target.",
        "colors": ["R"], "color_identity": ["R"], "keywords": [],
        "rarity": "common", "set": "lea", "released_at": "1993-08-05",
        "legalities": {"modern": "legal"}, "scryfall_uri": "https://x/bolt",
        "image_uris": {"normal": "https://img/bolt.jpg"},
    },
    {   # split card: joins at the face level, not the top level
        "oracle_id": "oid-fireice", "name": "Fire // Ice", "layout": "split",
        "cmc": 2.0, "type_line": "Instant // Instant",
        "color_identity": ["U", "R"],
        "card_faces": [{"name": "Fire", "oracle_text": "deals 2 damage"},
                       {"name": "Ice", "oracle_text": "Tap target permanent."}],
    },
    {   # em-dash and modifier-colon: Forge spells these with ASCII
        "oracle_id": "oid-meta", "name": "Human—Time Lord Meta-Crisis",
        "layout": "normal", "type_line": "Phenomenon", "color_identity": [],
    },
    {
        "oracle_id": "oid-raton", "name": "Ratonhnhaké꞉ton", "layout": "normal",
        "type_line": "Legendary Creature — Human Assassin", "color_identity": ["G"],
    },
    {
        "oracle_id": "oid-joven", "name": "Joven and Chandler", "layout": "normal",
        "type_line": "Legendary Creature — Human Rogue", "color_identity": ["B", "R"],
    },
    {   # the paper card an Alchemy rebalance must NOT be joined to
        "oracle_id": "oid-goldspan", "name": "Goldspan Dragon", "layout": "normal",
        "type_line": "Legendary Creature — Dragon", "color_identity": ["R"],
    },
    {   # the Universes Within card; Forge scripts it under its UB name
        "oracle_id": "oid-greymond", "name": "Greymond, Avacyn's Stalwart",
        "layout": "normal", "type_line": "Legendary Creature — Human Soldier",
        "color_identity": ["W"],
    },
]


@pytest.fixture(scope="module")
def store(tmp_path_factory):
    d = tmp_path_factory.mktemp("cardstore")
    src = os.path.join(d, "scryfall.jsonl.gz")
    with gzip.open(src, "wt", encoding="utf-8") as f:
        for rec in SCRYFALL_FIXTURE:
            f.write(json.dumps(rec) + "\n")
    aliases = os.path.join(d, "aliases.json")
    with open(aliases, "w", encoding="utf-8") as f:
        json.dump({"aliases": [
            {"forge": "Rick, Steadfast Leader",
             "scryfall": "Greymond, Avacyn's Stalwart",
             "class": "universes-within", "status": "confirmed"},
            # candidate rows are inert until a human promotes them
            {"forge": "Drake Stone", "scryfall": "Lightning Bolt",
             "class": "fuzzy", "status": "candidate"},
        ]}, f)
    db = os.path.join(d, "cards.sqlite")
    stats = cs.build(src, db, snapshot_date="2026-08-07T00:00:00Z",
                     aliases_path=aliases)
    assert stats["cards"] == len(SCRYFALL_FIXTURE)
    return cs.CardStore(db)


# --- normalization -------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("Lightning Bolt", "lightning bolt"),
    ("Human—Time Lord Meta-Crisis", "human-time lord meta-crisis"),
    ("Human-Time Lord Meta-Crisis", "human-time lord meta-crisis"),
    ("Ratonhnhaké꞉ton", "ratonhnhake:ton"),
    ("Ratonhnhaké:ton", "ratonhnhake:ton"),
    ("Jace’s Ingenuity", "jace's ingenuity"),
    ("  Spaced   Out  ", "spaced out"),
])
def test_fold_name(raw, expected):
    assert cs.fold_name(raw) == expected


def test_fold_name_is_spelling_only():
    """Folding must never merge two genuinely different cards."""
    assert cs.fold_name("A-Goldspan Dragon") != cs.fold_name("Goldspan Dragon")


# --- join classes --------------------------------------------------------

def test_card_level_match(store):
    row = store.resolve("Lightning Bolt")
    assert row["oracle_id"] == "oid-bolt"
    assert row["match_source"] == "card"


def test_face_level_match(store):
    """Forge splits Fire // Ice into two faces; each must resolve."""
    for face in ("Fire", "Ice"):
        row = store.resolve(face)
        assert row is not None and row["oracle_id"] == "oid-fireice"
        assert row["match_source"] == "face"


def test_punctuation_folding_joins(store):
    """Forge's ASCII spellings reach the Unicode originals."""
    assert store.resolve("Human-Time Lord Meta-Crisis")["oracle_id"] == "oid-meta"
    assert store.resolve("Ratonhnhaké:ton")["oracle_id"] == "oid-raton"


def test_playtest_prefix_stripped(store):
    row = store.resolve("P-Joven and Chandler")
    assert row is not None and row["oracle_id"] == "oid-joven"


def test_confirmed_alias_applied(store):
    row = store.resolve("Rick, Steadfast Leader")
    assert row is not None and row["oracle_id"] == "oid-greymond"
    assert row["match_source"] == "alias"


def test_candidate_alias_not_applied(store):
    """Fuzzy candidates are inert until a human sets status='confirmed'."""
    assert store.resolve("Drake Stone") is None


# --- the correctness trap ------------------------------------------------

def test_alchemy_rebalance_never_joins_to_paper_card(store):
    """A-<name> is a mechanically different card. Joining it to the paper card
    would attach the wrong oracle text to the wrong card."""
    assert store.resolve("A-Goldspan Dragon") is None
    assert cs.classify_unmatched("A-Goldspan Dragon") == "alchemy-rebalance"


def test_classify_unmatched_defaults_to_absent():
    assert cs.classify_unmatched("Some Upcoming Card") == "absent"


# --- hydrate -------------------------------------------------------------

def test_hydrate_attaches_scryfall_fields(store):
    out = store.hydrate({"name": "Lightning Bolt", "nodes": [], "edges": []})
    assert out["join_status"] == "card"
    assert out["scryfall"]["color_identity"] == "R"
    assert out["scryfall"]["legalities"] == {"modern": "legal"}
    assert out["scryfall"]["image_uris"]["normal"].startswith("https://")
    assert out["nodes"] == []          # original record preserved


def test_hydrate_degrades_gracefully_on_miss(store):
    """A graph result with no Scryfall counterpart must still render."""
    out = store.hydrate({"name": "A-Goldspan Dragon", "nodes": []})
    assert out["scryfall"] is None
    assert out["join_status"] == "alchemy-rebalance"


def test_color_identity_lookup(store):
    assert store.color_identity("Fire") == "UR"
    assert store.color_identity("No Such Card") is None


def test_meta_records_snapshot(store):
    assert store.meta["scryfall_snapshot"] == "2026-08-07T00:00:00Z"


def test_open_returns_none_when_absent(tmp_path):
    assert cs.CardStore.open(str(tmp_path / "nope.sqlite")) is None


def test_store_is_thread_safe(store):
    """ThreadingHTTPServer hands each request to a new thread, and SQLite
    forbids sharing a connection across threads. Connections are thread-local."""
    import threading

    errors = []

    def work():
        try:
            for name in ("Lightning Bolt", "Fire", "Ice"):
                assert store.resolve(name) is not None, name
        except Exception as e:      # noqa: BLE001 - surfaced via `errors`
            errors.append(e)

    threads = [threading.Thread(target=work) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
