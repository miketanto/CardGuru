"""M3 agreement: trigger modes, replacement events and static modes, on holdout.

Same posture as m2_param_agreement.py -- a corpus-wide measure over M1's
dev/holdout split, not a rerun of any adversarial question. Productions were
developed against dev; the reported number is holdout.

Usage:
    python3 research/scripts/m3_mode_agreement.py <forge.jsonl.gz> <oracle.jsonl.gz> [out.json]
    python3 research/scripts/m3_mode_agreement.py ... --split dev
"""
from __future__ import annotations

import collections
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from m1_effect_verbs import split_of  # noqa: E402


def load_map(path):
    out = {}
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        f.readline()
        for line in f:
            r = json.loads(line)
            out[r.get("canonicalName") or r.get("name")] = r
    return out


def modes(rec, kind):
    return {n.get("mode") for n in (rec or {}).get("nodes", [])
            if n.get("kind") == kind and n.get("mode")}


def events(rec):
    return {(n.get("params") or {}).get("Event")
            for n in (rec or {}).get("nodes", [])
            if n.get("kind") == "R" and (n.get("params") or {}).get("Event")}


def kind_count(rec, kind):
    return sum(1 for n in (rec or {}).get("nodes", []) if n.get("kind") == kind)


def prf(tp, fp, fn):
    return {"tp": tp, "fp": fp, "fn": fn,
            "precision_pct": round(100 * tp / (tp + fp), 2) if tp + fp else None,
            "recall_pct": round(100 * tp / (tp + fn), 2) if tp + fn else None}


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    want = "holdout"
    if "--split" in argv:
        want = argv[argv.index("--split") + 1]
    F, O = load_map(argv[1]), load_map(argv[2])
    c = collections.Counter()
    per_mode = collections.defaultdict(collections.Counter)

    for nm, f in F.items():
        if want != "all" and split_of(f) != want:
            continue
        o = O.get(nm)
        c["faces"] += 1
        for label, fs, os_ in (("tmode", modes(f, "T"), modes(o, "T")),
                               ("smode", modes(f, "S"), modes(o, "S")),
                               ("revent", events(f), events(o))):
            c[f"{label}_tp"] += len(fs & os_)
            c[f"{label}_fp"] += len(os_ - fs)
            c[f"{label}_fn"] += len(fs - os_)
            if fs or os_:
                c[f"{label}_faces"] += 1
                c[f"{label}_exact"] += 1 if fs == os_ else 0
            if label == "smode":
                for m in fs & os_:
                    per_mode[m]["tp"] += 1
                for m in os_ - fs:
                    per_mode[m]["fp"] += 1
                for m in fs - os_:
                    per_mode[m]["fn"] += 1
        for k in ("R", "S"):
            c[f"n_forge_{k}"] += kind_count(f, k)
            c[f"n_oracle_{k}"] += kind_count(o, k)

    report = {"split": want, "faces_scored": c["faces"]}
    for label, title in (("tmode", "trigger_modes"), ("smode", "static_modes"),
                         ("revent", "replacement_events")):
        report[title] = {
            **prf(c[f"{label}_tp"], c[f"{label}_fp"], c[f"{label}_fn"]),
            "faces_with_any": c[f"{label}_faces"],
            "exact_set_agreement_pct": round(
                100 * c[f"{label}_exact"] / c[f"{label}_faces"], 2)
            if c[f"{label}_faces"] else None,
        }
    report["node_counts"] = {
        "R": {"forge": c["n_forge_R"], "oracle": c["n_oracle_R"]},
        "S": {"forge": c["n_forge_S"], "oracle": c["n_oracle_S"]},
    }
    report["static_mode_detail"] = [
        {"mode": m, "support": v["tp"] + v["fn"], "fp": v["fp"],
         "recall_pct": round(100 * v["tp"] / (v["tp"] + v["fn"]), 1)
         if (v["tp"] + v["fn"]) else None,
         "precision_pct": round(100 * v["tp"] / (v["tp"] + v["fp"]), 1)
         if (v["tp"] + v["fp"]) else None}
        for m, v in sorted(per_mode.items(),
                           key=lambda kv: -(kv[1]["tp"] + kv[1]["fn"]))[:12]]
    text = json.dumps(report, indent=1)
    print(text)
    if len(argv) > 3 and not argv[3].startswith("--"):
        with open(argv[3], "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"\n-> {argv[3]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
