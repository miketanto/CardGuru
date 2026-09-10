"""Corpus-wide agreement on the cost and target params, scored on M1's holdout.

Why this exists: the six bugs fixed after the triage were *found* by inspecting
a01/a04/a05 disagreements, which burns those questions as a clean measure
(research/oracle-grammar-triage.md). Rerunning them shows the bugs are gone but
is debugging, not scoring.

This measures the same fields over the **whole corpus** instead of over three
query hit sets, split dev/holdout by M1's stable card-name hash, and reports the
holdout half. That is a different population and a different measure.

It is NOT an independent confirmation of the M2 kill criterion. It cannot be:
it scores fields whose bugs were discovered via the burned slice. Re-deciding
the kill criterion needs a fresh adversarial slice, per plan/eval.md §B rule 2.
What this *can* honestly say is whether the fixes generalise beyond the ~700
cards that motivated them.

Usage:
    python3 research/scripts/m2_param_agreement.py <forge.jsonl.gz> <oracle.jsonl.gz> [out.json]
    python3 research/scripts/m2_param_agreement.py ... --split dev
"""
from __future__ import annotations

import collections
import gzip
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from m1_effect_verbs import split_of  # noqa: E402

SAC_RE = re.compile(r"Sac<([^/>]*)/([^/>]*)")


def load_map(path):
    out = {}
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        f.readline()
        for line in f:
            r = json.loads(line)
            out[r.get("canonicalName") or r.get("name")] = r
    return out


def sac_atoms(rec) -> set[str]:
    """Normalised Sac atoms: count and type only, dropping Forge's cosmetic
    trailing description ('Sac<1/Creature.Other/another creature>')."""
    out = set()
    for n in (rec or {}).get("nodes", []):
        cost = (n.get("params") or {}).get("Cost") or ""
        for cnt, typ in SAC_RE.findall(cost):
            out.add(f"{cnt}/{typ}")
    return out


def taps_as_cost(rec) -> bool:
    for n in (rec or {}).get("nodes", []):
        if n.get("kind") == "A" and n.get("apiKind") == "AB":
            if "T" in ((n.get("params") or {}).get("Cost") or "").split():
                return True
    return False


def counter_valid(rec) -> set[str]:
    return {(n.get("params") or {}).get("ValidTgts")
            for n in (rec or {}).get("nodes", [])
            if n.get("api") == "Counter" and (n.get("params") or {}).get("ValidTgts")}


def prf(tp, fp, fn):
    return {
        "tp": tp, "fp": fp, "fn": fn,
        "precision_pct": round(100 * tp / (tp + fp), 2) if tp + fp else None,
        "recall_pct": round(100 * tp / (tp + fn), 2) if tp + fn else None,
    }


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    want = "holdout"
    if "--split" in argv:
        want = argv[argv.index("--split") + 1]
    F, O = load_map(argv[1]), load_map(argv[2])

    c = collections.Counter()
    for nm, f in F.items():
        if want != "all" and split_of(f) != want:
            continue
        o = O.get(nm)
        c["faces"] += 1

        fs, os_ = sac_atoms(f), sac_atoms(o)
        c["sac_tp"] += len(fs & os_)
        c["sac_fp"] += len(os_ - fs)
        c["sac_fn"] += len(fs - os_)
        if fs or os_:
            c["sac_faces"] += 1
            c["sac_exact"] += 1 if fs == os_ else 0

        ft, ot = taps_as_cost(f), taps_as_cost(o)
        c["tap_tp"] += 1 if (ft and ot) else 0
        c["tap_fp"] += 1 if (ot and not ft) else 0
        c["tap_fn"] += 1 if (ft and not ot) else 0

        fv, ov = counter_valid(f), counter_valid(o)
        if fv or ov:
            c["ctr_faces"] += 1
            c["ctr_exact"] += 1 if fv == ov else 0
            # the a05 property: does either side call the target unrestricted?
            f_unres = "Card" in fv
            o_unres = "Card" in ov
            c["unres_tp"] += 1 if (f_unres and o_unres) else 0
            c["unres_fp"] += 1 if (o_unres and not f_unres) else 0
            c["unres_fn"] += 1 if (f_unres and not o_unres) else 0

    report = {
        "split": want,
        "faces_scored": c["faces"],
        "sacrifice_cost_atoms": {
            **prf(c["sac_tp"], c["sac_fp"], c["sac_fn"]),
            "faces_with_any": c["sac_faces"],
            "exact_set_agreement_pct": round(100 * c["sac_exact"] / c["sac_faces"], 2)
            if c["sac_faces"] else None,
        },
        "tap_in_activation_cost": prf(c["tap_tp"], c["tap_fp"], c["tap_fn"]),
        "counter_valid_tgts": {
            "faces_with_any": c["ctr_faces"],
            "exact_set_agreement_pct": round(100 * c["ctr_exact"] / c["ctr_faces"], 2)
            if c["ctr_faces"] else None,
            "unrestricted_flag": prf(c["unres_tp"], c["unres_fp"], c["unres_fn"]),
        },
    }
    text = json.dumps(report, indent=1)
    print(text)
    if len(argv) > 3 and not argv[3].startswith("--"):
        with open(argv[3], "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"\n-> {argv[3]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
