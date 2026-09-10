"""Phase 1a (v7 plan §2): card record -> the three embedder channels.

Reads `rl/artifacts/cards_v1` (built by rl/cards/build_index.py) and turns
every face into:

  text     one string for the sentence encoder: type line, then oracle
           text with the card's own name replaced by CARDNAME, mana
           symbols spelled as tokens, every number bucketed (design L0:
           "numbers bucketed, never left raw").
  printed  an explicit float vector (PRINTED_DIM) that a linear probe can
           read exactly: mv, colours, supertypes, types, P/T, loyalty,
           defense, token/multi-face flags.  `printed_decode` inverts it;
           tests/test_cardemb_data.py checks the round trip on every
           ladder card.
  graph    the 68-column ability-graph readout from rl/e2_extract.py
           (v1 of the graph channel: a bag through an MLP; v1.5 = GNN
           over the ability tree, not built here).

Also the held-out split: 10 % of cards by name (multi-face cards travel
together, keyed by their Forge script), written to
rl/artifacts/card_emb_v1/split.json by `write_split`.

No torch import at module level: `to_tensors` imports it lazily so the
data layer is testable anywhere.
"""
import gzip
import hashlib
import json
import os
import re
from dataclasses import dataclass

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CARDS_V1 = os.path.join(REPO, "rl", "artifacts", "cards_v1")

# --- number bucketing -------------------------------------------------------
# exact 0..8, then 9-10, 11-15, 16-20, 21+ ; chosen from the oracle-text
# number histogram (1: 21k, 2: 7.5k, 3: 3.4k ... 9: 100, 10: 200, 11+: rare)
_BUCKET_EDGES = [(9, 10, "N9_10"), (11, 15, "N11_15"), (16, 20, "N16_20")]


def bucket_number(n):
    n = int(n)
    if n <= 8:
        return f"[N{n}]"
    for lo, hi, lab in _BUCKET_EDGES:
        if lo <= n <= hi:
            return f"[{lab}]"
    return "[N21P]"


_MANA_WORD = {"T": "[TAP]", "Q": "[UNTAP]", "E": "[ENERGY]", "C": "[MC]",
              "X": "[MX]", "S": "[MSNOW]", "P": "[MPHY]"}


def _mana_token(sym):
    s = sym.strip("{}")
    if s.isdigit():
        return "[M" + bucket_number(s)[2:]           # {2} -> [MN2]
    if s in _MANA_WORD:
        return _MANA_WORD[s]
    if "/" in s:                                     # hybrid / phyrexian: {W/U}, {2/W}, {B/P}
        return "[M" + s.replace("/", "") + "]"
    return "[M" + s + "]"                            # {W} -> [MW]


_NUM = re.compile(r"(?<![{\w])(\d+)(?![}\w])")
_MANA = re.compile(r"\{[^}]+\}")
_PT = re.compile(r"([+-])(\d+)/([+-])(\d+)")
_LOY = re.compile(r"\[([+\-−]?)(\d+)\]")


def _selfname_patterns(name):
    pats = []
    if name:
        pats.append(re.escape(name))
        short = name.split(",")[0].strip()
        if short != name and len(short) >= 4:
            pats.append(re.escape(short))
    return pats


_REMINDER = re.compile(r"\s*\([^()]*\)")


def strip_reminder(t):
    """Drop parenthetical reminder text ("(You may cast this spell for ...)").
    v3 data change (V7-VALIDATION.md §1d v2): reminder text dominated the
    text view of keyword-heavy cards (Sneak, blight) and pulled them away
    from their mechanical twins."""
    prev = None
    while prev != t:
        prev, t = t, _REMINDER.sub("", t)
    return t


def text_of(name, type_line, oracle, reminder=False):
    """The text channel for one face.  Deterministic; no learned pieces.
    reminder=False (v3 default) strips parenthetical reminder text."""
    t = (oracle or "").replace("\\n", " . ").replace("\n", " . ")
    if not reminder:
        t = strip_reminder(t)
    for p in _selfname_patterns(name):
        t = re.sub(r"(?<!\w)" + p + r"(?!\w)", "CARDNAME", t)   # \b fails on names ending in '!'
    t = t.replace("CARDNAME's", "CARDNAME's")
    t = _LOY.sub(lambda m: "[LOY" + {"+": "P", "-": "M", "−": "M", "": ""}[m.group(1)]
                 + bucket_number(m.group(2))[2:-1] + "]", t)          # [+1]: -> [LOYP1]:
    t = _PT.sub(lambda m: f"{m.group(1)}{bucket_number(m.group(2))}/{m.group(3)}{bucket_number(m.group(4))}", t)
    t = _MANA.sub(lambda m: _mana_token(m.group(0)), t)
    t = _NUM.sub(lambda m: bucket_number(m.group(1)), t)
    t = re.sub(r"\s+", " ", t).strip()
    head = (type_line or "").strip()
    return (head + " . " + t).strip(" .") if t else head


# --- printed channel ----------------------------------------------------------

MV_MAX = 12          # exact one-hot 0..12, then a "13+" bin
PT_MAX = 12
LOY_MAX = 7
SUPERTYPES = ["Legendary", "Basic", "Snow"]
TYPES = ["Creature", "Instant", "Sorcery", "Artifact", "Enchantment", "Land",
         "Planeswalker", "Battle", "Kindred"]
_TYPE_ALIAS = {"Tribal": "Kindred"}
COLORS = "WUBRG"


def _layout():
    slots = []

    def block(name, n):
        start = len(slots)
        slots.extend((name, i) for i in range(n))
        return start

    L = {}
    L["mv"] = block("mv", MV_MAX + 3)          # null, 0..12, 13+
    L["mv_raw"] = block("mv_raw", 1)
    L["x_cost"] = block("x_cost", 1)
    L["colors"] = block("colors", 5)
    L["colorless"] = block("colorless", 1)
    L["supertypes"] = block("supertypes", len(SUPERTYPES))
    L["types"] = block("types", len(TYPES))
    L["power"] = block("power", PT_MAX + 3)     # null, 0..12, 13+
    L["power_raw"] = block("power_raw", 1)
    L["toughness"] = block("toughness", PT_MAX + 3)
    L["toughness_raw"] = block("toughness_raw", 1)
    L["pt_star"] = block("pt_star", 1)
    L["loyalty"] = block("loyalty", LOY_MAX + 3)  # null, 0..7, 8+
    L["defense"] = block("defense", 2)           # present flag, raw/10
    L["flags"] = block("flags", 3)               # token, multi_face, back_face
    return L, len(slots)


LAYOUT, PRINTED_DIM = _layout()


def _onehot(vec, start, value, vmax):
    """null -> slot 0; 0..vmax -> slot value+1; > vmax -> slot vmax+2."""
    if value is None:
        vec[start] = 1.0
    elif value <= vmax:
        vec[start + 1 + max(0, value)] = 1.0
    else:
        vec[start + vmax + 2] = 1.0


def _unhot(vec, start, vmax):
    seg = vec[start:start + vmax + 3]
    k = max(range(len(seg)), key=lambda i: seg[i])
    if k == 0:
        return None
    if k == vmax + 2:
        return f"{vmax + 1}+"
    return k - 1


def printed_encode(f):
    """f: one row of fields.jsonl.gz.  Returns a list of PRINTED_DIM floats."""
    v = [0.0] * PRINTED_DIM
    L = LAYOUT
    _onehot(v, L["mv"], f.get("mv"), MV_MAX)
    v[L["mv_raw"]] = (f.get("mv") or 0) / 10.0
    v[L["x_cost"]] = 1.0 if "X" in (f.get("mana_cost") or "").split() else 0.0
    for i, c in enumerate(COLORS):
        v[L["colors"] + i] = 1.0 if c in (f.get("colors") or "") else 0.0
    v[L["colorless"]] = 0.0 if f.get("colors") else 1.0
    for i, s in enumerate(SUPERTYPES):
        v[L["supertypes"] + i] = 1.0 if s in (f.get("supertypes") or []) else 0.0
    types = {_TYPE_ALIAS.get(t, t) for t in (f.get("types") or [])}
    for i, t in enumerate(TYPES):
        v[L["types"] + i] = 1.0 if t in types else 0.0
    p, t = f.get("power"), f.get("toughness")
    _onehot(v, L["power"], p if p is None else max(0, p), PT_MAX)
    v[L["power_raw"]] = (p or 0) / 10.0
    _onehot(v, L["toughness"], t if t is None else max(0, t), PT_MAX)
    v[L["toughness_raw"]] = (t or 0) / 10.0
    v[L["pt_star"]] = float(f.get("pt_star") or 0)
    _onehot(v, L["loyalty"], f.get("loyalty"), LOY_MAX)
    d = f.get("defense")
    v[L["defense"]] = 0.0 if d is None else 1.0
    v[L["defense"] + 1] = (d or 0) / 10.0
    v[L["flags"]] = 1.0 if f.get("kind") == "token" else 0.0
    v[L["flags"] + 1] = 1.0 if (f.get("n_faces") or 1) > 1 else 0.0
    v[L["flags"] + 2] = 1.0 if (f.get("face_index") or 0) > 0 else 0.0
    return v


def printed_decode(v):
    """Inverse of printed_encode on the exactly-recoverable fields."""
    L = LAYOUT
    return {
        "mv": _unhot(v, L["mv"], MV_MAX),
        "x_cost": v[L["x_cost"]] > 0.5,
        "colors": "".join(c for i, c in enumerate(COLORS) if v[L["colors"] + i] > 0.5),
        "supertypes": [s for i, s in enumerate(SUPERTYPES) if v[L["supertypes"] + i] > 0.5],
        "types": [t for i, t in enumerate(TYPES) if v[L["types"] + i] > 0.5],
        "power": _unhot(v, L["power"], PT_MAX),
        "toughness": _unhot(v, L["toughness"], PT_MAX),
        "pt_star": v[L["pt_star"]] > 0.5,
        "loyalty": _unhot(v, L["loyalty"], LOY_MAX),
        "defense": None if v[L["defense"]] < 0.5 else round(v[L["defense"] + 1] * 10),
        "token": v[L["flags"]] > 0.5,
        "multi_face": v[L["flags"] + 1] > 0.5,
        "back_face": v[L["flags"] + 2] > 0.5,
    }


def printed_expected(f):
    """What printed_decode must return for a fields row (the test oracle)."""
    def clip(x, vmax):
        if x is None:
            return None
        x = max(0, x)
        return x if x <= vmax else f"{vmax + 1}+"
    return {
        "mv": clip(f.get("mv"), MV_MAX),
        "x_cost": "X" in (f.get("mana_cost") or "").split(),
        "colors": f.get("colors") or "",
        "supertypes": [s for s in SUPERTYPES if s in (f.get("supertypes") or [])],
        "types": [t for t in TYPES if t in {_TYPE_ALIAS.get(x, x) for x in (f.get("types") or [])}],
        "power": clip(f.get("power"), PT_MAX),
        "toughness": clip(f.get("toughness"), PT_MAX),
        "pt_star": bool(f.get("pt_star")),
        "loyalty": clip(f.get("loyalty"), LOY_MAX),
        "defense": f.get("defense"),
        "token": f.get("kind") == "token",
        "multi_face": (f.get("n_faces") or 1) > 1,
        "back_face": (f.get("face_index") or 0) > 0,
    }


# --- records ------------------------------------------------------------------

@dataclass
class CardRecord:
    id: int
    name: str
    kind: str
    file: str
    text: str
    printed: list
    graph: list
    fields: dict


def type_line(f):
    return " ".join((f.get("supertypes") or []) + (f.get("types") or [])
                    + (["—"] + f["subtypes"] if f.get("subtypes") else []))


def load_cards(artifact_dir=CARDS_V1):
    """Returns (records: list[CardRecord] indexed by id, names: dict norm-name -> id)."""
    idx = json.load(open(os.path.join(artifact_dir, "index.json"), encoding="utf-8"))
    oracle = {}
    with gzip.open(os.path.join(artifact_dir, "oracle.jsonl.gz"), "rt", encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            oracle[r["id"]] = r["oracle"]
    out = []
    with gzip.open(os.path.join(artifact_dir, "fields.jsonl.gz"), "rt", encoding="utf-8") as fh:
        for line in fh:
            f = json.loads(line)
            out.append(CardRecord(
                id=f["id"], name=f["name"], kind=f["kind"], file=f.get("file") or "",
                text=text_of(f["name"], type_line(f), oracle.get(f["id"], "")),
                printed=printed_encode(f), graph=list(f["graph"]), fields=f))
    assert all(r.id == i for i, r in enumerate(out)), "ids must be dense"
    return out, idx["names"]


# --- split --------------------------------------------------------------------

def split_key(rec):
    """Multi-face cards travel together: key on the script, i.e. the name for
    single-face cards and the shared file for multi-face ones."""
    return rec.file or rec.name


def is_heldout(rec, frac=0.10, seed=0):
    h = hashlib.sha1(f"{seed}:{split_key(rec)}".encode("utf-8")).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF < frac


def write_split(records, out_path, frac=0.10, seed=0):
    held = [r.id for r in records if is_heldout(r, frac, seed)]
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    doc = {"frac": frac, "seed": seed, "key": "script file (name for single-face cards)",
           "n_total": len(records), "n_heldout": len(held), "heldout_ids": held}
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)
    return doc


# --- tensors (lazy torch) -------------------------------------------------------

def to_tensors(records):
    import torch
    printed = torch.tensor([r.printed for r in records], dtype=torch.float32)
    graph = torch.tensor([r.graph for r in records], dtype=torch.float32)
    return [r.text for r in records], printed, graph


if __name__ == "__main__":
    recs, names = load_cards()
    doc = write_split(recs, os.path.join(REPO, "rl", "artifacts", "card_emb_v1", "split.json"))
    print(f"cards={len(recs)} printed_dim={PRINTED_DIM} graph_dim={len(recs[0].graph)} "
          f"heldout={doc['n_heldout']} ({100.0 * doc['n_heldout'] / len(recs):.1f}%)")
    for q in ("counterspell", "kaito, bane of nightmares", "zombie army token"):
        r = recs[names[q]]
        print(f"  {r.name}: {r.text[:150]}")
