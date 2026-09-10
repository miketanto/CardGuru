"""Phase 0b (v7 plan §2): the card index the shared embedder is built on.

Reads data/dataset.jsonl.gz (built from the Forge pin, docs/getting-started.md
§3) plus the Forge tokenscripts, and writes rl/artifacts/cards_v1/:

  index.json    meta (pin, counts, feature names, field schema) +
                names: normalised name -> id (every face name, every
                "A // B" joined name, every token name with and without
                the " Token" suffix)
  oracle.jsonl.gz  one line per id: {id, name, kind, oracle}
  fields.jsonl.gz  one line per id: printed fields (mv, mana_cost, colors,
                supertypes, types, subtypes, power, toughness, loyalty,
                defense, n_faces, face_index) and the 68-column graph
                readout from rl/e2_extract.py (reused, not rewritten)
  README.md     the gate readout: card count, unknowns per decklist

One id per dataset face (multi-face cards get one id per face; the joined
name resolves to the front face) and one id per tokenscript.  Ids are
dense integers, stable for a given pin: sorted by (file, faceIndex) for
cards, then by script name for tokens.

Gate (plan §2, 0b): >= 33k cards; 0 unknown across every .dck in rl/ and
every list in decks/; tokens resolved via tokenscripts.  The script exits
non-zero if the gate fails so it can sit in a test.

Run (WSL, repo root):
    python3 rl/cards/build_index.py [--dataset data/dataset.jsonl.gz]
        [--tokenscripts ~/forge-src/forge-gui/res/tokenscripts]
        [--out rl/artifacts/cards_v1]
"""
import argparse
import glob
import gzip
import json
import os
import re
import sys
from collections import Counter, defaultdict

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "rl"))

from cardguru.dataset import load, norm_name            # noqa: E402
from cardguru.deck import mana_value                    # noqa: E402
from cardguru.answers import load_token_scripts         # noqa: E402
from cardguru.forge_parser import parse_file             # noqa: E402
from e2_extract import FEATURES, face_vector            # noqa: E402

SUPERTYPES = {"Legendary", "Basic", "Snow", "World", "Ongoing", "Elite",
              "Host"}
CARD_TYPES = {"Creature", "Instant", "Sorcery", "Artifact", "Enchantment",
              "Land", "Planeswalker", "Battle", "Kindred", "Tribal",
              "Plane", "Phenomenon", "Vanguard", "Scheme", "Conspiracy",
              "Dungeon", "Emblem"}
COLOR_LETTERS = "WUBRG"
COLOR_WORDS = {"white": "W", "blue": "U", "black": "B", "red": "R",
               "green": "G"}

FIELD_SCHEMA = {
    "id": "int, dense, stable for the pin",
    "name": "Forge face name (as XMage reports it, modulo accents)",
    "kind": "card | token",
    "file": "Forge script path relative to cardsfolder/tokenscripts",
    "face_index": "0 for single-face; face order for multi-face",
    "n_faces": "faces sharing the same script",
    "mana_cost": "Forge mana string or null (no cost)",
    "mv": "mana value (X counts 0) or null",
    "colors": "WUBRG mask string, e.g. 'UB'; from cost symbols and Colors:",
    "supertypes": "list", "types": "list", "subtypes": "list",
    "power": "int or null", "toughness": "int or null",
    "pt_star": "1 if power or toughness is * / X / CDA-defined",
    "loyalty": "int or null", "defense": "int or null",
    "graph": "68 floats, rl/e2_extract.py FEATURES order, this face only",
    "graph_union": "68 floats, union over faces (multi-face only, else null)",
}


def split_types(type_line):
    words = (type_line or "").split()
    sup, typ, sub = [], [], []
    for w in words:
        if w in SUPERTYPES:
            sup.append(w)
        elif w in CARD_TYPES:
            typ.append(w)
        else:
            sub.append(w)
    return sup, typ, sub


def colors_of(mana_cost, other):
    mask = set()
    for tok in (mana_cost or "").split():
        for ch in tok:
            if ch in COLOR_LETTERS:
                mask.add(ch)
    for word, ch in COLOR_WORDS.items():
        if word in str((other or {}).get("Colors", "")).lower():
            mask.add(ch)
    return "".join(c for c in COLOR_LETTERS if c in mask)


def parse_pt(pt):
    if not pt or "/" not in pt:
        return None, None, 0
    p, t = pt.split("/", 1)
    star = 0
    out = []
    for s in (p, t):
        s = s.strip()
        try:
            out.append(int(s))
        except ValueError:
            out.append(None)
            star = 1
    return out[0], out[1], star


def to_int(s):
    try:
        return int(str(s).strip())
    except (TypeError, ValueError):
        return None


def face_fields(rec, kind, face_index, n_faces):
    sup, typ, sub = split_types(rec.get("types"))
    p, t, star = parse_pt(rec.get("pt"))
    other = rec.get("other") or {}
    return {
        "name": rec["name"], "kind": kind, "file": rec.get("file"),
        "face_index": face_index, "n_faces": n_faces,
        "mana_cost": rec.get("manaCost") or None,
        "mv": mana_value(rec.get("manaCost")),
        "colors": colors_of(rec.get("manaCost"), other),
        "supertypes": sup, "types": typ, "subtypes": sub,
        "power": p, "toughness": t, "pt_star": star,
        "loyalty": to_int(rec.get("loyalty")),
        "defense": to_int(other.get("Defense")),
        "graph": face_vector(rec), "graph_union": None,
    }


# --- decklists ----------------------------------------------------------------

_DCK = re.compile(r"^\s*(?:SB:\s*)?(\d+)\s+\[[^\]]*\]\s+(.+?)\s*$")
_TXT = re.compile(r"^\s*(\d+)x?\s+(.+?)\s*$")


def parse_deck(path):
    names = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(("NAME:", "LAYOUT:", "//", "#")):
                continue
            if line.lower().rstrip(":") in ("sideboard", "maybeboard"):
                break
            m = _DCK.match(line) or _TXT.match(line)
            if m:
                names.append(m.group(2))
    return names


def deck_files():
    return sorted(glob.glob(os.path.join(REPO, "rl", "*.dck"))
                  + glob.glob(os.path.join(REPO, "decks", "*.txt")))


# --- main ---------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default=os.path.join(REPO, "data", "dataset.jsonl.gz"))
    ap.add_argument("--tokenscripts", default=None,
                    help="Forge tokenscripts dir (default $CARDGURU_TOKENSCRIPTS)")
    ap.add_argument("--out", default=os.path.join(REPO, "rl", "artifacts", "cards_v1"))
    ap.add_argument("--extra", default=os.path.join(REPO, "rl", "cards", "extra_scripts"),
                    help="dir of Forge card scripts newer than the pin (README there)")
    ap.add_argument("--min-cards", type=int, default=33000)
    args = ap.parse_args()

    meta, records = load(args.dataset)
    by_file = defaultdict(list)
    for rec in records:
        by_file[rec.get("file") or rec["name"]].append(rec)
    n_extra = 0
    if args.extra and os.path.isdir(args.extra):
        for fn in sorted(os.listdir(args.extra)):
            if fn.endswith(".txt"):
                for face in parse_file(os.path.join(args.extra, fn), relroot=args.extra):
                    rec = face.to_record()
                    rec["file"] = "extra/" + fn
                    by_file[rec["file"]].append(rec)
                    n_extra += 1

    entries = []                        # id == position
    names = {}                          # norm name -> id
    collisions = Counter()

    def register(name, cid, weak=False):
        key = norm_name(name)
        if key in names and names[key] != cid:
            collisions[key] += 1
            if weak:
                return
        names[key] = cid

    for file in sorted(by_file):
        faces = sorted(by_file[file], key=lambda r: r.get("faceIndex") or 0)
        n = len(faces)
        vecs = []
        first_id = len(entries)
        for i, rec in enumerate(faces):
            fld = face_fields(rec, "card", i, n)
            vecs.append(fld["graph"])
            fld["id"] = len(entries)
            fld["oracle"] = rec.get("oracle") or ""
            entries.append(fld)
            register(rec["name"], fld["id"])
        if n > 1:
            union = [max(col) for col in zip(*vecs)]
            union[FEATURES.index("multi_face")] = 1.0
            for e in entries[first_id:first_id + n]:
                e["graph_union"] = union
            register(" // ".join(r["name"] for r in faces), first_id)

    n_cards = len(entries)

    toks = load_token_scripts(args.tokenscripts)
    for script in sorted(toks):
        rec = toks[script]
        rec["file"] = script + ".txt"
        fld = face_fields(rec, "token", 0, 1)
        fld["id"] = len(entries)
        fld["oracle"] = rec.get("oracle") or ""
        entries.append(fld)
        tname = rec.get("name") or script
        register(tname, fld["id"], weak=True)
        register("token:" + script, fld["id"])
        if tname.endswith(" Token"):
            register(tname[:-len(" Token")], fld["id"], weak=True)
    n_tokens = len(entries) - n_cards

    seen = Counter(norm_name(e["name"]) for e in entries[:n_cards])
    n_card_dups = sum(1 for v in seen.values() if v > 1)

    # --- decklist gate
    unknown = {}
    per_deck = []
    for path in deck_files():
        cards = parse_deck(path)
        miss = [c for c in cards if norm_name(c) not in names]
        per_deck.append((os.path.relpath(path, REPO), len(cards), len(miss)))
        for c in miss:
            unknown[c] = os.path.relpath(path, REPO)

    os.makedirs(args.out, exist_ok=True)
    with gzip.open(os.path.join(args.out, "oracle.jsonl.gz"), "wt", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps({"id": e["id"], "name": e["name"],
                                "kind": e["kind"], "oracle": e["oracle"]}) + "\n")
    with gzip.open(os.path.join(args.out, "fields.jsonl.gz"), "wt", encoding="utf-8") as f:
        for e in entries:
            row = {k: v for k, v in e.items() if k != "oracle"}
            f.write(json.dumps(row) + "\n")
    index = {
        "version": "cards_v1",
        "source_pin": meta.get("source_pin"),
        "n_ids": len(entries), "n_cards": n_cards, "n_tokens": n_tokens,
        "n_names": len(names), "n_extra_faces": n_extra,
        "extra_scripts": "rl/cards/extra_scripts (post-pin cards; see its README)",
        "graph_features": FEATURES,
        "field_schema": FIELD_SCHEMA,
        "name_norm": "cardguru.dataset.norm_name (NFKD, ascii, lower, strip)",
        "names": names,
    }
    with open(os.path.join(args.out, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f)

    ok = n_cards >= args.min_cards and not unknown
    lines = [
        "# cards_v1 — card index for the v7 shared embedder",
        "",
        f"Built by `rl/cards/build_index.py` from `data/dataset.jsonl.gz` "
        f"(Forge pin `{meta.get('source_pin')}`) and the Forge tokenscripts.",
        "",
        "| count | value |", "|---|---|",
        f"| card faces (ids) | {n_cards} |",
        f"| token scripts (ids) | {n_tokens} |",
        f"| of which post-pin overlay faces (rl/cards/extra_scripts) | {n_extra} |",
        f"| card names shared by >1 card script (Variant/basic reprints) | {n_card_dups} |",
        f"| resolvable names | {len(names)} |",
        f"| name collisions (later face kept) | {sum(collisions.values())} |",
        "",
        "## Decklist gate (plan §2, 0b: 0 unknown)",
        "",
        "| deck | cards | unknown |", "|---|---|---|",
    ] + [f"| {p} | {n} | {m} |" for p, n, m in per_deck] + [
        "",
        f"**Gate: {'PASS' if ok else 'FAIL'}** — cards ≥ {args.min_cards}: "
        f"{n_cards >= args.min_cards}; unknown names: {len(unknown)}.",
    ]
    if unknown:
        lines += ["", "Unknown:", ""] + [f"- `{c}` ({p})" for c, p in sorted(unknown.items())]
    lines += [
        "", "Files: `index.json` (meta + name→id), `oracle.jsonl.gz`, "
        "`fields.jsonl.gz` (schema in `index.json.field_schema`). "
        "Graph readout = `rl/e2_extract.py` FEATURES (68 cols).",
        "",
        "Consumer notes:",
        "- Token names are not unique across tokenscripts (e.g. three "
        "`Elemental Token` scripts); a bare token name resolves to the "
        "alphabetically first script, `token:<script>` is exact.",
        "- Back faces of transform cards have `mana_cost = null`, `mv = null`; "
        "the embedder's data layer decides whether to inherit the front face's.",
        "- Rebuild: `python3 rl/cards/build_index.py` (5 s) after "
        "`python3 -m cardguru build ...` (docs/getting-started.md §3).",
    ]
    with open(os.path.join(args.out, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"cards={n_cards} tokens={n_tokens} names={len(names)} "
          f"collisions={sum(collisions.values())} card_dups={n_card_dups} "
          f"extra={n_extra} decks={len(per_deck)} "
          f"unknown={len(unknown)} gate={'PASS' if ok else 'FAIL'}")
    for c, p in sorted(unknown.items())[:20]:
        print(f"  unknown: {c!r} in {p}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
