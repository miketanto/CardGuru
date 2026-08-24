"""Triage every disagreement between the Forge-derived and oracle-derived graphs.

M2 (research/oracle-grammar-m2.md) reported 76-87% agreement on the three
adversarial questions the oracle grammar can answer, and flagged the residual as
"either a grammar gap or a Forge scripting quirk" -- untriaged. This script
triages it, over the full population rather than a sample.

For each adversarial question it partitions the symmetric difference of the two
hit sets and assigns each card a mechanical cause, so the headline question --
*is the disagreement grammar debt, or is it Forge being odd?* -- gets a number
instead of an impression.

Causes are decided from the two graphs' own structure, never from a hand list of
card names.

Usage:
    python3 research/scripts/m2_triage_disagreements.py <forge.jsonl.gz> <oracle.jsonl.gz> [out.json]
"""
from __future__ import annotations

import collections
import gzip
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir)
sys.path.insert(0, os.path.abspath(ROOT))

from cardguru.index import SearchIndex  # noqa: E402

ABLATION = os.path.join(ROOT, "research", "data", "ablation_adversarial.json")
QUALIFIED_RE = re.compile(r"[.+,]")   # Forge selector qualifier: Card.cmcGE4


def load_map(path):
    out = {}
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        f.readline()
        for line in f:
            r = json.loads(line)
            out[r.get("canonicalName") or r.get("name")] = r
    return out


def apis(rec, api=None):
    return [n for n in (rec or {}).get("nodes", [])
            if n.get("api") and (api is None or n["api"] == api)]


def cost_of(node):
    return (node.get("params") or {}).get("Cost") or ""


# --- per-question cause rules -------------------------------------------------

def cause_a01(nm, F, O, forge_side):
    f, o = F.get(nm), O.get(nm)
    f_sac = [n for n in apis(f) if "Sac<" in cost_of(n)]
    o_sac = [n for n in apis(o) if "Sac<" in cost_of(n)]
    if forge_side:
        if not apis(o):
            return "no node emitted (missing effect production)"
        f_atom = next((re.search(r"Sac<[^>]*>", cost_of(n)).group(0)
                       for n in f_sac if re.search(r"Sac<[^>]*>", cost_of(n))), "")
        if not o_sac:
            if "Other" in f_atom or "other" in f_atom:
                return "cost-atom gap: 'another/other X'"
            if ";" in f_atom:
                return "cost-atom gap: compound type ('artifact or creature')"
            if "CARDNAME" in f_atom or "NICKNAME" in f_atom:
                return "cost-atom gap: self-sacrifice by card name"
            return "cost-atom gap: qualified or uncommon type"
        return "cost present but node/kind mismatch"
    # oracle-only
    if any("CARDNAME" in cost_of(n) for n in o_sac):
        f_atom = " ".join(cost_of(n) for n in f_sac)
        if "NICKNAME" in f_atom:
            return "query-vocabulary artifact: Forge uses NICKNAME"
        if f_sac:
            return "grammar FP: CARDNAME over-detected (card named after a type)"
    if f_sac and all(n.get("kind") == "SVar" for n in f_sac):
        return "structure artifact: Forge stores ability as SVar, query wants kind A"
    return "other"


def cause_a05(nm, F, O, forge_side):
    f, o = F.get(nm), O.get(nm)
    f_c, o_c = apis(f, "Counter"), apis(o, "Counter")
    if forge_side:
        if o_c and all(n.get("apiKind") != "SP" for n in o_c):
            return "node-ordering bug: Counter demoted to sub-ability"
        if not o_c:
            return "no Counter node emitted"
        return "other"
    f_valid = [(n.get("params") or {}).get("ValidTgts") or "" for n in f_c]
    if any(QUALIFIED_RE.search(v) for v in f_valid):
        return "grammar FP: post-nominal restriction ignored ('with mana value N')"
    if f_c and all(n.get("kind") == "SVar" for n in f_c):
        return "structure artifact: modal spell, Forge nests Counter under Charm"
    if not f_c:
        return "Forge emits no Counter node"
    return "other"


def cause_a04(nm, F, O, forge_side):
    f, o = F.get(nm), O.get(nm)
    if forge_side:
        if not apis(o):
            return "no node emitted (missing effect production)"
        if not any("T" in cost_of(n).split() for n in apis(o)):
            return "cost-atom gap: {T} not recovered"
        return "cost present but node/kind mismatch"
    if not apis(f):
        return "Forge emits no api node"
    return "other"


CAUSE = {"a01": cause_a01, "a04": cause_a04, "a05": cause_a05}

# Which causes are the grammar's fault vs. an artifact of Forge's modelling or
# of the compiled query's vocabulary.
def bucket(cause: str) -> str:
    if cause.startswith(("cost-atom gap", "no node emitted", "no Counter node",
                         "grammar FP", "node-ordering bug")):
        return "grammar debt"
    if cause.startswith(("structure artifact", "query-vocabulary artifact",
                         "Forge emits no")):
        return "forge/query artifact"
    return "unclassified"


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    with open(ABLATION, encoding="utf-8") as f:
        ablation = json.load(f)
    forge_ix, oracle_ix = SearchIndex.load(argv[1]), SearchIndex.load(argv[2])
    F, O = load_map(argv[1]), load_map(argv[2])

    def hits(ix, q):
        return {(r["record"].get("canonicalName") or r["record"].get("name"))
                for r in ix.search(q)}

    report = {"questions": {}, "totals": collections.Counter()}
    for qid in ("a01", "a04", "a05"):
        q = ablation[qid]["agent_query"]
        fh, oh = hits(forge_ix, q), hits(oracle_ix, q)
        block = {"forge_hits": len(fh), "oracle_hits": len(oh),
                 "agreed": len(fh & oh), "forge_only": {}, "oracle_only": {}}
        for side, names, is_forge in (("forge_only", fh - oh, True),
                                      ("oracle_only", oh - fh, False)):
            counts = collections.Counter()
            examples = collections.defaultdict(list)
            for nm in sorted(names):
                c = CAUSE[qid](nm, F, O, is_forge)
                counts[c] += 1
                report["totals"][bucket(c)] += 1
                if len(examples[c]) < 3:
                    examples[c].append(nm)
            block[side] = {"n": len(names),
                           "causes": [{"cause": c, "n": n,
                                       "bucket": bucket(c),
                                       "examples": examples[c]}
                                      for c, n in counts.most_common()]}
        report["questions"][qid] = block

    total = sum(report["totals"].values())
    report["totals"] = dict(report["totals"])
    report["total_disagreements"] = total
    report["grammar_debt_pct"] = round(
        100 * report["totals"].get("grammar debt", 0) / total, 1) if total else None
    text = json.dumps(report, indent=1)
    print(text)
    if len(argv) > 3:
        with open(argv[3], "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"\n-> {argv[3]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
