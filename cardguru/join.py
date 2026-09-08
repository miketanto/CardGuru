"""Forge ↔ Scryfall join: bulk download, match reporting, alias candidates.

The join is measured, never assumed. `report()` classifies every Forge face and
emits counts plus the full miss list; misses are the input to a *hand-reviewed*
alias table (data/aliases.json). Fuzzy API resolution generates candidates only
— nothing is applied until a human sets status='confirmed', because the fuzzy
endpoint happily returns near-name false positives ('Drake Stone' -> 'Stone
Drake') alongside genuine Universes-Within matches.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter

from . import dataset as ds
from .cardstore import CardStore, classify_unmatched

BULK_ENDPOINT = "https://api.scryfall.com/bulk-data"
USER_AGENT = "CardGuru/0.1 (research; https://github.com/miketanto/CardGuru)"
# Scryfall asks for 50-100 ms between requests; 250 ms plus backoff keeps a
# 60-second rate-limit lockout from eating a whole resolve pass.
REQUEST_DELAY = 0.25


def _get(url: str, retries: int = 3) -> dict:
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT, "Accept": "application/json"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                time.sleep(float(e.headers.get("Retry-After") or 5) + 1)
                continue
            raise
    raise RuntimeError("unreachable")


def download_bulk(out_path: str, kind: str = "oracle_cards") -> dict:
    """Fetch a Scryfall bulk file. Returns {path, updated_at, size}.

    Note: Scryfall now publishes `jsonl_download_uri` (line-delimited, gzipped);
    the older `download_uri` JSON field is gone.
    """
    entries = _get(BULK_ENDPOINT)["data"]
    entry = next((e for e in entries if e["type"] == kind), None)
    if entry is None:
        raise SystemExit(f"no bulk data of type {kind!r}; "
                         f"available: {sorted(e['type'] for e in entries)}")
    uri = entry.get("jsonl_download_uri") or entry.get("download_uri")
    parent = os.path.dirname(out_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    req = urllib.request.Request(uri, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=300) as r, open(out_path, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    return {"path": out_path, "updated_at": entry["updated_at"],
            "size": os.path.getsize(out_path), "uri": uri}


def report(dataset_path: str, store: CardStore) -> dict:
    """Classify every Forge face against the card store."""
    meta, records = ds.load(dataset_path)
    classes = Counter()
    misses: list[dict] = []
    for rec in records:
        name = rec.get("name")
        if not name:
            classes["no_name"] += 1
            continue
        row = store.resolve(name)
        if row is None:
            klass = classify_unmatched(name)
            classes[klass] += 1
            misses.append({"name": name, "class": klass,
                           "alternateMode": rec.get("alternateMode"),
                           "types": rec.get("types")})
        else:
            classes[row["match_source"]] += 1

    total = sum(classes.values())
    matched = total - len(misses) - classes["no_name"]
    return {
        "forge_pin": meta.get("source_pin"),
        "scryfall_snapshot": store.meta.get("scryfall_snapshot"),
        "total_faces": total,
        "matched": matched,
        "match_rate": round(matched / total, 5) if total else 0.0,
        "by_class": dict(classes.most_common()),
        "misses": sorted(misses, key=lambda m: (m["class"], m["name"])),
    }


def resolve_candidates(misses: list[dict], out_path: str,
                       delay: float = REQUEST_DELAY) -> dict:
    """Ask Scryfall's fuzzy endpoint for a counterpart to each miss.

    Writes an aliases.json-shaped document with every row status='candidate'.
    A human promotes rows to 'confirmed'; nothing here is authoritative.
    Alchemy rebalances are never proposed as aliases — they are mechanically
    distinct cards and inheriting the paper card's text would be wrong.
    """
    candidates, unmatched, errors = [], [], []
    for m in misses:
        name = m["name"]
        if m["class"] == "alchemy-rebalance":
            unmatched.append({
                "forge": name, "class": "alchemy-rebalance",
                "reason": "Alchemy rebalance is a mechanically distinct card; "
                          "must not inherit the paper card's oracle text",
            })
            continue
        url = "https://api.scryfall.com/cards/named?" + urllib.parse.urlencode(
            {"fuzzy": name})
        try:
            d = _get(url)
            candidates.append({
                "forge": name, "scryfall": d.get("name"),
                "oracle_id": d.get("oracle_id"), "set": d.get("set"),
                "class": "fuzzy", "status": "candidate",
                "review": "verify this is the same card, not a near-name",
            })
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = json.load(e).get("details", "")[:120]
            except Exception:
                detail = f"HTTP {e.code}"
            (unmatched if e.code == 404 else errors).append({
                "forge": name, "class": "absent" if e.code == 404 else "error",
                "reason": detail})
        time.sleep(delay)

    doc = {
        "_meta": {
            "note": "Generated candidates. Only rows with status='confirmed' "
                    "are applied by cardstore.build(). Review each one.",
            "generated_from": "scryfall /cards/named?fuzzy",
        },
        "aliases": candidates,
        "unmatched": unmatched,
        "errors": errors,
    }
    parent = os.path.dirname(out_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write("\n")
    return {"candidates": len(candidates), "unmatched": len(unmatched),
            "errors": len(errors), "path": out_path}
