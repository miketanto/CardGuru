"""Score agent-compiled DSL queries against a question set with witnesses.

Usage: python3 eval/score_nl_poc.py <compiled_queries.json> [questions.json] [out.json]
where compiled_queries maps question id -> query DSL object (compiler output).

For each query: validate against the ontology (the same gate the API-based
compiler uses), run it over the index, and check witness cards appear.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from cardguru.index import SearchIndex          # noqa: E402
from cardguru.validate import Ontology, validate  # noqa: E402

QUESTIONS = os.path.join(HERE, "nl_questions_poc.json")
ONTOLOGY = os.path.join(ROOT, "research", "data", "ontology.json")
DATASET = os.path.join(ROOT, "data", "dataset.jsonl.gz")


def main(compiled_path: str, questions_path: str = QUESTIONS,
         out_path: str | None = None):
    compiled = json.load(open(compiled_path, encoding="utf-8"))
    qs = {q["id"]: q for q in json.load(open(questions_path, encoding="utf-8"))["questions"]}
    onto = Ontology(json.load(open(ONTOLOGY, encoding="utf-8")))
    idx = SearchIndex.load(DATASET)

    results, n_valid, n_witness = [], 0, 0
    for qid, spec in qs.items():
        query = compiled.get(qid)
        row = {"id": qid, "q": spec["q"], "query": query}
        if query is None:
            row.update(valid=False, errors=["missing from compiler output"],
                       hits=0, witness_found=[], witness_missing=spec["witness"])
            results.append(row)
            continue
        errors = validate(query, onto)
        row["valid"] = not errors
        row["errors"] = errors
        if errors:
            row.update(hits=0, witness_found=[], witness_missing=spec["witness"])
        else:
            n_valid += 1
            names = {h["record"]["name"] for h in idx.search(query)}
            found = [w for w in spec["witness"] if w in names]
            missing = [w for w in spec["witness"] if w not in names]
            absent_ok = [a for a in spec.get("absent", []) if a not in names]
            row.update(hits=len(names), witness_found=found,
                       witness_missing=missing)
            if spec.get("absent"):
                row["absent_ok"] = absent_ok
            if not missing:
                n_witness += 1
        results.append(row)

    print(f"{'id':4} {'valid':6} {'hits':6} witness")
    for r in results:
        wit = "OK" if r["valid"] and not r["witness_missing"] else \
              ("MISS: " + ", ".join(r["witness_missing"]))
        print(f"{r['id']:4} {str(r['valid']):6} {r['hits']:6} {wit}")
        if r["errors"]:
            for e in r["errors"][:3]:
                print(f"       ! {e}")
    n = len(results)
    print(f"\nvalidated: {n_valid}/{n}   witness-correct: {n_witness}/{n}")
    out = out_path or os.path.join(ROOT, "research", "data", "nl_poc_results.json")
    json.dump({"results": results, "validated": n_valid,
               "witness_correct": n_witness, "n": n},
              open(out, "w", encoding="utf-8"), indent=1)
    print(f"wrote {out}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
