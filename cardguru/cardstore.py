"""Scryfall card store — the attribute tier (architecture §1.1).

Deliberately a *separate* artifact from the ability-graph dataset. Forge and
Scryfall refresh on different cadences (Forge on set release, Scryfall daily),
and `oracle_data_date` / `forge_commit` are independent axes of the version
tuple (architecture §4). Baking Scryfall fields into dataset.jsonl.gz would
collapse those axes and force a full graph rebuild on every oracle-text fix.

SQLite because it is stdlib — no new dependency, and it gives the attribute
query layer somewhere to live later.

The join key is the card name, normalized. Match classes, in priority order:
  card    - Forge face name == Scryfall top-level name
  face    - Forge face name == one of Scryfall's card_faces[].name
  alias   - a hand-confirmed row in data/aliases.json

Names that resolve to none of those are recorded as misses with a class, not
silently dropped. Two miss classes are *deliberately* left unjoined:
  alchemy-rebalance  A-<name> is a mechanically different card from <name>;
                     aliasing it to the paper card would attach wrong text.
  absent             Forge scripts cards Scryfall does not have yet (the pin
                     tracks an upcoming-set branch).
"""
from __future__ import annotations

import gzip
import json
import os
import sqlite3
import threading
import unicodedata

# Unicode punctuation Forge and Scryfall spell differently. Folding these is a
# normalization fix, not an alias: 'Human—Time Lord' vs 'Human-Time Lord',
# 'Ratonhnhaké꞉ton' (U+A789) vs 'Ratonhnhaké:ton'.
_PUNCT_FOLD = {
    "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-",
    "―": "-", "−": "-",                      # dashes / minus
    "꞉": ":", "﹕": ":",                      # modifier colons
    "‘": "'", "’": "'", "ʼ": "'",       # curly apostrophes
    "“": '"', "”": '"',
    "…": "...",                                   # ellipsis
    " ": " ", " ": " ", " ": " ",       # spaces
}

# Forge name prefixes that mark a variant of an existing card.
#   P-  playtest (Mystery Booster) printing of an otherwise normal card
#   A-  Alchemy rebalance — a DIFFERENT card; never strip this to join
PLAYTEST_PREFIX = "P-"
ALCHEMY_PREFIX = "A-"

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS cards (
    oracle_id      TEXT PRIMARY KEY,
    name           TEXT NOT NULL,
    layout         TEXT,
    mana_cost      TEXT,
    cmc            REAL,
    type_line      TEXT,
    oracle_text    TEXT,
    power          TEXT,
    toughness      TEXT,
    loyalty        TEXT,
    colors         TEXT,
    color_identity TEXT,
    keywords       TEXT,
    rarity         TEXT,
    set_code       TEXT,
    released_at    TEXT,
    edhrec_rank    INTEGER,
    reserved       INTEGER,
    game_changer   INTEGER,
    legalities     TEXT,
    image_uris     TEXT,
    card_faces     TEXT,
    scryfall_uri   TEXT
);
CREATE TABLE IF NOT EXISTS card_names (
    norm       TEXT NOT NULL,
    oracle_id  TEXT NOT NULL,
    face_index INTEGER NOT NULL DEFAULT -1,
    source     TEXT NOT NULL,
    PRIMARY KEY (norm, oracle_id, face_index)
);
CREATE INDEX IF NOT EXISTS idx_card_names_norm ON card_names (norm);
CREATE INDEX IF NOT EXISTS idx_cards_name ON cards (name);
"""


def fold_name(name: str) -> str:
    """Normalize a card name for joining: punctuation-folded, accent-stripped,
    lowercased. Strictly a *spelling* normalization — it never changes which
    card is meant."""
    s = "".join(_PUNCT_FOLD.get(ch, ch) for ch in name)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return " ".join(s.lower().split())


def classify_unmatched(name: str) -> str:
    """Miss class for a Forge name with no Scryfall counterpart."""
    if name.startswith(ALCHEMY_PREFIX):
        return "alchemy-rebalance"
    return "absent"


# --------------------------------------------------------------------------
# build

_COLS = ("oracle_id", "name", "layout", "mana_cost", "cmc", "type_line",
         "oracle_text", "power", "toughness", "loyalty", "colors",
         "color_identity", "keywords", "rarity", "set_code", "released_at",
         "edhrec_rank", "reserved", "game_changer", "legalities", "image_uris",
         "card_faces", "scryfall_uri")


def _row(c: dict) -> tuple:
    def js(v):
        return json.dumps(v, separators=(",", ":")) if v is not None else None
    return (
        c.get("oracle_id"), c.get("name"), c.get("layout"), c.get("mana_cost"),
        c.get("cmc"), c.get("type_line"), c.get("oracle_text"), c.get("power"),
        c.get("toughness"), c.get("loyalty"),
        "".join(c.get("colors") or []) or None,
        "".join(c.get("color_identity") or []) or None,
        js(c.get("keywords") or None), c.get("rarity"), c.get("set"),
        c.get("released_at"), c.get("edhrec_rank"),
        int(bool(c.get("reserved"))), int(bool(c.get("game_changer"))),
        js(c.get("legalities")), js(c.get("image_uris")), js(c.get("card_faces")),
        c.get("scryfall_uri"),
    )


def load_aliases(path: str | None) -> tuple[list[dict], list[dict]]:
    """Return (confirmed_aliases, declared_unmatched). Only rows with
    status == 'confirmed' are ever applied — fuzzy candidates are inert until
    a human promotes them."""
    if not path or not os.path.exists(path):
        return [], []
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    aliases = [a for a in doc.get("aliases", []) if a.get("status") == "confirmed"]
    return aliases, doc.get("unmatched", [])


def build(scryfall_path: str, db_path: str, snapshot_date: str | None = None,
          aliases_path: str | None = None) -> dict:
    """Build the SQLite card store from a Scryfall oracle-cards JSONL(.gz)."""
    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    stats = {"cards": 0, "names_card": 0, "names_face": 0, "names_alias": 0,
             "skipped_no_oracle_id": 0}

    opener = gzip.open if scryfall_path.endswith(".gz") else open
    by_name: dict[str, str] = {}
    with opener(scryfall_path, "rt", encoding="utf-8") as f:
        for line in f:
            c = json.loads(line)
            oid = c.get("oracle_id")
            if not oid or not c.get("name"):
                stats["skipped_no_oracle_id"] += 1
                continue
            conn.execute(
                f"INSERT OR IGNORE INTO cards ({','.join(_COLS)}) "
                f"VALUES ({','.join('?' * len(_COLS))})", _row(c))
            if conn.total_changes == 0:
                pass
            stats["cards"] += 1

            norm = fold_name(c["name"])
            by_name.setdefault(norm, oid)
            conn.execute("INSERT OR IGNORE INTO card_names VALUES (?,?,?,?)",
                         (norm, oid, -1, "card"))
            stats["names_card"] += 1
            for i, face in enumerate(c.get("card_faces") or []):
                fn = face.get("name")
                if not fn:
                    continue
                fnorm = fold_name(fn)
                by_name.setdefault(fnorm, oid)
                conn.execute("INSERT OR IGNORE INTO card_names VALUES (?,?,?,?)",
                             (fnorm, oid, i, "face"))
                stats["names_face"] += 1

    aliases, _ = load_aliases(aliases_path)
    for a in aliases:
        target = by_name.get(fold_name(a["scryfall"]))
        if not target:
            continue
        conn.execute("INSERT OR IGNORE INTO card_names VALUES (?,?,?,?)",
                     (fold_name(a["forge"]), target, -1, "alias"))
        stats["names_alias"] += 1

    meta = {"scryfall_snapshot": snapshot_date or "",
            "source": os.path.basename(scryfall_path),
            "aliases_applied": str(stats["names_alias"])}
    conn.executemany("INSERT OR REPLACE INTO meta VALUES (?,?)", list(meta.items()))
    conn.commit()
    conn.close()
    return stats


# --------------------------------------------------------------------------
# read


class CardStore:
    """Read-only accessor. Cheap to open; queries are indexed lookups.

    Connections are thread-local: SQLite forbids sharing a connection across
    threads, and the HTTP server hands each request to a new one. Read-only
    mode means concurrent readers need no locking.
    """

    def __init__(self, db_path: str):
        self.path = db_path
        self._local = threading.local()
        self.meta = {k: v for k, v in
                     self.conn.execute("SELECT key, value FROM meta")}

    @property
    def conn(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(f"file:{self.path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return conn

    @classmethod
    def open(cls, db_path: str) -> "CardStore | None":
        """Open the store, or None if it hasn't been built. Callers degrade
        gracefully — nothing in the graph search path requires this."""
        return cls(db_path) if os.path.exists(db_path) else None

    def resolve(self, name: str) -> sqlite3.Row | None:
        """Look up a Forge face name. Tries the name as given, then the
        playtest prefix stripped. Never strips the Alchemy prefix."""
        for candidate in self._candidates(name):
            row = self.conn.execute(
                "SELECT c.*, n.source AS match_source, n.face_index AS match_face "
                "FROM card_names n JOIN cards c USING (oracle_id) "
                "WHERE n.norm = ? ORDER BY n.face_index LIMIT 1",
                (candidate,)).fetchone()
            if row:
                return row
        return None

    @staticmethod
    def _candidates(name: str):
        yield fold_name(name)
        if name.startswith(PLAYTEST_PREFIX):
            yield fold_name(name[len(PLAYTEST_PREFIX):])

    def color_identity(self, name: str) -> str | None:
        row = self.resolve(name)
        return row["color_identity"] if row else None

    def hydrate(self, record: dict) -> dict:
        """Attach Scryfall display fields to a graph record. Returns a new
        dict; missing joins yield `scryfall: None` rather than raising, so the
        UI can render the graph result either way."""
        row = self.resolve(record.get("name") or "")
        out = dict(record)
        if row is None:
            out["scryfall"] = None
            out["join_status"] = classify_unmatched(record.get("name") or "")
            return out
        out["scryfall"] = {
            "oracle_id": row["oracle_id"], "name": row["name"],
            "mana_cost": row["mana_cost"], "cmc": row["cmc"],
            "type_line": row["type_line"], "oracle_text": row["oracle_text"],
            "colors": row["colors"], "color_identity": row["color_identity"],
            "rarity": row["rarity"], "set": row["set_code"],
            "edhrec_rank": row["edhrec_rank"],
            "legalities": json.loads(row["legalities"]) if row["legalities"] else None,
            "image_uris": json.loads(row["image_uris"]) if row["image_uris"] else None,
            "scryfall_uri": row["scryfall_uri"],
        }
        out["join_status"] = row["match_source"]
        return out

    def close(self):
        """Close this thread's connection, if it has one."""
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            self._local.conn = None
