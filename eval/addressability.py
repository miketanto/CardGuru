"""RulesGuru corpus addressability: what fraction of the held-out benchmark
could the simulator even attempt today?

HELD-OUT DISCIPLINE: this script reads ONLY per-question metadata — card
names, level, complexity, tags. It never touches questionSimple/answerSimple/
citedRules content, and it verifies the freeze hash before reading anything.

A question is classified by the implementation status of its cards:
  engine_ready    every included card is implemented (and finished) in XMage
  engine_partial  some cards implemented, some not
  engine_blocked  no included card is implemented
  no_cards        pure rules question (no cards) — CR-retrieval territory
Graph coverage (does our Forge-derived ability graph know the card?) is
reported alongside, since search/citations run off the graph even when the
engine can't simulate.
"""
from __future__ import annotations

import collections
import gzip
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CORPUS = os.path.join(HERE, "rulesguru", "rulesguru_full.json")
FROZEN = os.path.join(HERE, "rulesguru", "FROZEN.sha256")
XMAGE_CARDS = os.environ.get("CARDGURU_XMAGE_CARDS", "/home/user/mse/data/xmage_cards.txt")
CANONICAL = os.environ.get("CARDGURU_CANONICAL", "/home/user/mse/index/index.json")
UNFINISHED = os.path.join(ROOT, "research", "data", "xmage_unfinished.json")
DATASET = os.path.join(ROOT, "data", "dataset.jsonl.gz")


def verify_freeze():
    want = open(FROZEN, encoding="utf-8").read().split()[0]
    h = hashlib.sha256()
    with open(CORPUS, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    if h.hexdigest() != want:
        sys.exit("FROZEN.sha256 mismatch - benchmark is void, refusing to run")


def load_names():
    xmage = set()
    with open(XMAGE_CARDS, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2:
                xmage.add(parts[1])
    unfinished = set()
    for names in json.load(open(UNFINISHED, encoding="utf-8"))["sets"].values():
        unfinished.update(names)
    graph = set()
    if os.path.exists(DATASET):
        with gzip.open(DATASET, "rt", encoding="utf-8") as f:
            for line in f:
                graph.add(json.loads(line).get("name"))
    return xmage, unfinished, graph


def load_face_groups():
    """name -> all names of the same physical card (from the canonical index's
    `ns` face lists), so 'Insectile Aberration' resolves to 'Delver of Secrets'."""
    groups = {}
    if os.path.exists(CANONICAL):
        for name, card in json.load(open(CANONICAL, encoding="utf-8"))["cards"].items():
            ns = card.get("ns")
            if ns:
                groups[name] = list(ns)
    return groups


FACE_GROUPS = {}


def lookup(name: str, pool: set) -> bool:
    """Match a RulesGuru card name against a name pool, tolerating multi-face
    naming splits: 'A // B' vs front-face-only vs back-face names."""
    if name in pool:
        return True
    parts = name.split(" // ") if " // " in name else [name]
    for part in parts:
        if part in pool:
            return True
        for alias in FACE_GROUPS.get(part, []):
            if alias in pool:
                return True
    return False


def classify(card_names, xmage, unfinished, graph):
    if not card_names:
        return "no_cards", [], []
    impl, missing = [], []
    for n in card_names:
        ok = lookup(n, xmage) and not lookup(n, unfinished)
        (impl if ok else missing).append(n)
    if not missing:
        status = "engine_ready"
    elif impl:
        status = "engine_partial"
    else:
        status = "engine_blocked"
    return status, impl, missing


def main():
    verify_freeze()
    FACE_GROUPS.update(load_face_groups())
    xmage, unfinished, graph = load_names()
    questions = json.load(open(CORPUS, encoding="utf-8"))

    per_q = []
    for q in questions:
        names = [c["name"] for c in q.get("includedCards") or []]
        status, impl, missing = classify(names, xmage, unfinished, graph)
        graph_known = [n for n in names if lookup(n, graph)]
        per_q.append({
            "id": q["id"],
            "level": str(q.get("level")),
            "complexity": q.get("complexity"),
            "tags": q.get("tags") or [],
            "n_cards": len(names),
            "status": status,
            "missing_cards": missing,
            "graph_known": len(graph_known),
            "graph_full": len(graph_known) == len(names) and bool(names),
        })

    def dist(rows, key):
        out = collections.defaultdict(collections.Counter)
        for r in rows:
            for k in ([r[key]] if isinstance(r[key], str) else r[key]):
                out[k][r["status"]] += 1
                out[k]["total"] += 1
        return {k: dict(v) for k, v in sorted(out.items())}

    status_counts = collections.Counter(r["status"] for r in per_q)
    graph_full = sum(1 for r in per_q if r["graph_full"])
    missing_counter = collections.Counter(
        n for r in per_q for n in r["missing_cards"])

    report = {
        "generated_from": "eval/rulesguru/rulesguru_full.json (frozen)",
        "pools": {"xmage_implemented": len(xmage),
                  "xmage_unfinished": len(unfinished),
                  "forge_graph": len(graph)},
        "questions": len(per_q),
        "status": dict(status_counts),
        "graph_full_coverage": graph_full,
        "by_level": dist(per_q, "level"),
        "by_complexity": dist(per_q, "complexity"),
        "by_tag": dist(per_q, "tags"),
        "top_missing_cards": missing_counter.most_common(40),
        "per_question": per_q,
    }
    out_path = os.path.join(ROOT, "research", "data", "rulesguru_addressability.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)

    n = len(per_q)
    print(f"questions: {n}")
    for s in ("engine_ready", "engine_partial", "engine_blocked", "no_cards"):
        c = status_counts.get(s, 0)
        print(f"  {s:15} {c:5}  ({100*c/n:.1f}%)")
    print(f"  graph full-coverage {graph_full:5}  ({100*graph_full/n:.1f}%)")
    print(f"\ntop missing cards: "
          f"{', '.join(f'{k} x{v}' for k, v in missing_counter.most_common(10))}")
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
