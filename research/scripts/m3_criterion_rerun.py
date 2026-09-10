"""Score a frozen adversarial slice against the Forge and oracle graphs.

Generalises research/scripts/m2_adversarial_rerun.py to take the slice as an
argument, so the burned a01-a05 file is no longer hard-coded. Each question
carries its own structural query, and that query is run verbatim against both
derivations -- nothing is rewritten to suit the grammar.

Pass criteria are the ablation's own: the witness must be returned and the foil
must not. A question that returns nothing "rejects the foil" vacuously and is
reported as such rather than counted as a pass.

Usage:
    python3 research/scripts/m3_criterion_rerun.py <slice.json> <forge.jsonl.gz> <oracle.jsonl.gz> [out.json]
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir)
sys.path.insert(0, os.path.abspath(ROOT))

from cardguru.index import SearchIndex  # noqa: E402


def hits(index, query):
    out = set()
    for r in index.search(query):
        nm = r["record"].get("canonicalName") or r["record"].get("name")
        if nm:
            out.add(nm)
    return out


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 2
    with open(argv[1], encoding="utf-8") as f:
        slice_ = json.load(f)
    forge = SearchIndex.load(argv[2])
    oracle = SearchIndex.load(argv[3])

    rows, passed, vacuous = [], 0, 0
    for q in slice_["questions"]:
        query = q["agent_query"]
        fh, oh = hits(forge, query), hits(oracle, query)
        wit = set(q.get("witness") or [])
        foil = set(q.get("absent") or [])
        o_wit = bool(wit & oh)
        o_foil_ok = not (foil & oh)
        is_vacuous = not oh
        if o_wit and o_foil_ok and not is_vacuous:
            passed += 1
        if is_vacuous:
            vacuous += 1
        inter = fh & oh
        rows.append({
            "id": q["id"], "family": q.get("family"), "q": q["q"],
            "forge": {"hits": len(fh), "witness_found": bool(wit & fh),
                      "foil_rejected": not (foil & fh)},
            "oracle": {"hits": len(oh), "witness_found": o_wit,
                       "foil_rejected": o_foil_ok, "vacuous": is_vacuous},
            "recall_of_forge_hits_pct": round(100 * len(inter) / len(fh), 1) if fh else None,
            "jaccard_pct": round(100 * len(inter) / len(fh | oh), 1) if (fh | oh) else None,
        })

    n = len(rows)
    agg = [r["recall_of_forge_hits_pct"] for r in rows
           if r["recall_of_forge_hits_pct"] is not None]
    report = {
        "slice": os.path.basename(argv[1]),
        "questions": n,
        "oracle_passed": passed,
        "oracle_pass_pct": round(100 * passed / n, 1) if n else None,
        "oracle_vacuous_empty_results": vacuous,
        "forge_passed": sum(1 for r in rows if r["forge"]["witness_found"]
                            and r["forge"]["foil_rejected"]),
        "mean_recall_of_forge_hits_pct": round(sum(agg) / len(agg), 1) if agg else None,
        "rows": rows,
    }
    text = json.dumps(report, indent=1)
    print(text)
    if len(argv) > 4:
        with open(argv[4], "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"\n-> {argv[4]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
