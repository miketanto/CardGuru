"""Dataset build pipeline: cardsfolder -> parsed faces -> canonical-name join
-> gzipped JSONL dataset."""
from __future__ import annotations

import gzip
import json
import os
import unicodedata

from .forge_parser import parse_cardsfolder


def norm_name(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return s.lower().strip()


def load_canonical(index_path: str) -> dict[str, dict]:
    """Load the canonical card DB (taw/magic-search-engine index.json, an
    MTGJSON derivative; swap for Scryfall bulk when network allows).
    Returns {normalized_name: {name, layout}}."""
    with open(index_path, encoding="utf-8") as f:
        db = json.load(f)["cards"]
    return {norm_name(n): {"name": n, "layout": rec.get("l")}
            for n, rec in db.items()}


def build(cardsfolder: str, out_path: str, canonical_index: str | None = None,
          source_pin: str | None = None) -> dict:
    canonical = load_canonical(canonical_index) if canonical_index else {}
    stats = {"faces": 0, "canonical_matched": 0}
    parent = os.path.dirname(out_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    opener = gzip.open if out_path.endswith(".gz") else open
    with opener(out_path, "wt", encoding="utf-8") as out:
        header = {"_meta": {"source_pin": source_pin, "format": 1}}
        out.write(json.dumps(header) + "\n")
        for face in parse_cardsfolder(cardsfolder):
            rec = face.to_record()
            if face.name:
                canon = canonical.get(norm_name(face.name))
                if canon:
                    rec["canonicalName"] = canon["name"]
                    rec["layout"] = canon["layout"]
                    stats["canonical_matched"] += 1
            out.write(json.dumps(rec) + "\n")
            stats["faces"] += 1
    return stats


def load(path: str):
    """Yield (meta, records-iterator). Meta is the header dict (or {})."""
    opener = gzip.open if path.endswith(".gz") else open
    f = opener(path, "rt", encoding="utf-8")
    first = f.readline()
    meta = {}
    records = []
    if first:
        obj = json.loads(first)
        if "_meta" in obj:
            meta = obj["_meta"]
        else:
            records.append(obj)

    def gen():
        yield from records
        for line in f:
            yield json.loads(line)
    return meta, gen()
