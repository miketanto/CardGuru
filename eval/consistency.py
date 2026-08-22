"""Consistency harness — plan/nl-dsl-consistency.md Phase C0.

Measures whether five paraphrases of ONE intent compile to queries that return
the SAME cards. The unit is the intent, not the question.

Decision rules enforced here (see plan/nl-dsl-consistency.md):
  R1  consistency is Jaccard over RESULT SETS, never over query JSON. Two
      structurally different queries with identical hit sets are the same query.
  R2  PC is never emitted without agreement@witness alongside it. A compiler
      that returns {} for everything scores PC = 1.0, and this is the guard.
  R3  intents flagged "inverted" (H09 ambiguity) are excluded from headline PC
      and scored by disagreement instead — consistency there is a failure.

The LLM stage is pluggable, because who performs it is not the harness's
business:

  ApiBackend      anthropic API (needs ANTHROPIC_API_KEY + `anthropic`)
  RecordedBackend reads pre-recorded compilations from a JSONL log — this is
                  what makes the repo's established agent-as-compiler route
                  (research/agent-compiler-poc.md) scoreable, and what makes
                  the harness testable with no credentials at all
  StubBackend     canned queries, for the offline unit tests

Every compilation is cached to disk by (question, sample_index, backend), so
re-runs and resumed runs cost nothing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru.index import SearchIndex          # noqa: E402
from cardguru.querydsl import QueryError        # noqa: E402
from cardguru.validate import Ontology, validate  # noqa: E402

RUNGS = ("P1", "P2", "P3", "P4", "P5")


# ------------------------------------------------------------------ backends

class StubBackend:
    """Canned {question: query} map. Offline tests only."""

    name = "stub"

    def __init__(self, table: dict):
        self.table = table

    def compile(self, question: str, sample: int):
        q = self.table.get(question)
        if q is None:
            return None, ["stub: no canned query"]
        return q, []


class RecordedBackend:
    """Replays compilations from a JSONL log.

    Each line: {"question": str, "sample": int, "query": {...}|null,
                "errors": [str]}
    Missing (question, sample) pairs are reported as gaps rather than silently
    scored — a partially-recorded run must not masquerade as a complete one.
    """

    name = "recorded"

    def __init__(self, path: str):
        self.rows = {}
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                self.rows[(r["question"], int(r.get("sample", 0)))] = r
        self.missing: list[tuple[str, int]] = []

    def compile(self, question: str, sample: int):
        r = self.rows.get((question, sample))
        if r is None:
            self.missing.append((question, sample))
            return None, ["recorded: no entry for this (question, sample)"]
        return r.get("query"), list(r.get("errors") or [])


class ApiBackend:
    """The production compiler (cardguru.nl_compiler) via the anthropic API."""

    name = "api"

    def __init__(self, ontology_path: str, model: str | None = None,
                 temperature: float = 1.0, max_retries: int = 2):
        from cardguru.nl_compiler import MODEL
        self.ontology_path = ontology_path
        self.model = model or MODEL
        self.temperature = temperature
        self.max_retries = max_retries

    def compile(self, question: str, sample: int):
        from cardguru.nl_compiler import compile_question
        res = compile_question(question, self.ontology_path, model=self.model,
                               max_retries=self.max_retries)
        return res.query, list(res.errors)


# ------------------------------------------------------------------- caching

class Cache:
    def __init__(self, path: str | None):
        self.path = path
        self.data = {}
        if path and os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                self.data = json.load(f)

    @staticmethod
    def key(backend: str, question: str, sample: int) -> str:
        h = hashlib.sha256(f"{backend}\x00{question}\x00{sample}".encode()).hexdigest()
        return h[:32]

    def get(self, backend, question, sample):
        return self.data.get(self.key(backend, question, sample))

    def put(self, backend, question, sample, value):
        self.data[self.key(backend, question, sample)] = value

    def save(self):
        if not self.path:
            return
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f)


# ------------------------------------------------------------------- scoring

def jaccard(a: frozenset, b: frozenset) -> float:
    """Both-empty is agreement (1.0); one-empty is total disagreement (0.0)."""
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 1.0
    return len(a & b) / len(union)


def mean_pairwise_jaccard(sets: list[frozenset]) -> float | None:
    if len(sets) < 2:
        return None
    vals = [jaccard(sets[i], sets[j])
            for i in range(len(sets)) for j in range(i + 1, len(sets))]
    return statistics.mean(vals)


def modal(items: list):
    """Most common item; ties broken deterministically by sorted order."""
    if not items:
        return None, 0
    counts = Counter(items)
    top = max(counts.values())
    winner = sorted((i for i, c in counts.items() if c == top), key=repr)[0]
    return winner, top


def size_regime(n: int) -> str:
    if n <= 20:
        return "D1"
    if n <= 300:
        return "D2"
    return "D3"


# ------------------------------------------------------------------- runner

class Runner:
    def __init__(self, index: SearchIndex, onto: Ontology, backend,
                 cache: Cache, samples: int = 3):
        self.index = index
        self.onto = onto
        self.backend = backend
        self.cache = cache
        self.samples = samples
        self.name_to_faces = defaultdict(set)
        for i, rec in enumerate(index.records):
            nm = (rec.get("name") or "").strip().lower()
            if nm:
                self.name_to_faces[nm].add(i)

    def faces_for(self, card_names: list[str]) -> set[int]:
        out: set[int] = set()
        for nm in card_names or []:
            out |= self.name_to_faces.get(nm.strip().lower(), set())
        return out

    def execute(self, query) -> tuple[frozenset, str | None]:
        """Run a validated query, return (face-id set, error)."""
        try:
            hits = {i for i in self.index.candidates(query)
                    if self.index_match(i, query)}
        except (QueryError, Exception) as e:  # noqa: BLE001 - report, never crash a run
            return frozenset(), f"execution error: {type(e).__name__}: {e}"
        return frozenset(hits), None

    def index_match(self, i: int, query) -> bool:
        from cardguru.querydsl import CardGraph, evaluate
        ok, _ = evaluate(query, CardGraph(self.index.records[i]))
        return ok

    def compile_one(self, question: str, sample: int) -> dict:
        cached = self.cache.get(self.backend.name, question, sample)
        if cached is not None:
            return cached
        query, errors = self.backend.compile(question, sample)
        if query is not None and not errors:
            errors = validate(query, self.onto)
            if errors:
                query = None
        rec = {"query": query, "errors": errors}
        self.cache.put(self.backend.name, question, sample, rec)
        return rec

    def run_intent(self, intent: dict) -> dict:
        paras = intent.get("paraphrases") or {}
        witness = self.faces_for(intent.get("witness"))
        foil = self.faces_for(intent.get("absent_foil"))
        per_rung = {}
        all_sets: list[frozenset] = []
        compile_fails = 0
        total = 0

        rep_sets: list[frozenset] = []

        for rung in RUNGS:
            q_text = paras.get(rung)
            if not q_text:
                continue
            sets, notes = [], []
            for s in range(self.samples):
                total += 1
                c = self.compile_one(q_text, s)
                if c["query"] is None:
                    compile_fails += 1
                    notes.append({"sample": s, "error": c["errors"][:1]})
                    continue
                rs, err = self.execute(c["query"])
                if err:
                    compile_fails += 1
                    notes.append({"sample": s, "error": [err]})
                    continue
                sets.append(rs)
                all_sets.append(rs)
            # The rung's representative is its MODAL result set across samples —
            # the same consensus operation C1 proposes to ship in production.
            rep, _ = modal(sets)
            if rep is not None:
                rep_sets.append(rep)
            per_rung[rung] = {
                "question": q_text,
                "n_ok": len(sets),
                "SC": mean_pairwise_jaccard(sets),
                "rep_size": (len(rep) if rep is not None else None),
                "rep_has_witness": (bool(rep & witness) if rep is not None and witness else None),
                "rep_has_foil": (bool(rep & foil) if rep is not None and foil else None),
                "notes": notes,
            }

        reps = [per_rung[r]["rep_size"] for r in per_rung
                if per_rung[r]["rep_size"] is not None]
        pc = mean_pairwise_jaccard(rep_sets)
        correct = [r for r in rep_sets if witness and (r & witness)]
        pc_correct = mean_pairwise_jaccard(correct)
        _, modal_count = modal(all_sets)
        n_with_witness = sum(1 for s in all_sets if witness and (s & witness))
        n_with_foil = sum(1 for s in all_sets if foil and (s & foil))

        return {
            "id": intent["id"],
            "S": intent.get("S"), "H": intent.get("H"),
            "D_declared": intent.get("D"), "prov": intent.get("prov"),
            "inverted": bool(intent.get("inverted")),
            "n_compilations": total,
            "compile_fail": compile_fails,
            "PC": pc,
            "PC_correct": pc_correct,
            "agreement_at_witness": (n_with_witness / len(all_sets)) if all_sets and witness else None,
            "foil_rate": (n_with_foil / len(all_sets)) if all_sets and foil else None,
            "modal_share": (modal_count / len(all_sets)) if all_sets else None,
            "disagreement": (1 - modal_count / len(all_sets)) if all_sets else None,
            "median_hits": (statistics.median(reps) if reps else None),
            "D_observed": (size_regime(int(statistics.median(reps))) if reps else None),
            "witness_resolved": bool(witness) if intent.get("witness") else None,
            "rungs": per_rung,
        }


# ------------------------------------------------------------------ reporting

def aggregate(rows: list[dict]) -> dict:
    headline = [r for r in rows if not r["inverted"]]
    inverted = [r for r in rows if r["inverted"]]

    def m(vals):
        vals = [v for v in vals if v is not None]
        return round(statistics.mean(vals), 3) if vals else None

    out = {
        "n_intents": len(rows),
        "n_headline": len(headline),
        "PC": m(r["PC"] for r in headline),
        "PC_correct": m(r["PC_correct"] for r in headline),
        "agreement_at_witness": m(r["agreement_at_witness"] for r in headline),
        "foil_rate": m(r["foil_rate"] for r in headline),
        "SC": m(sc for r in headline for sc in
                (v["SC"] for v in r["rungs"].values())),
        "modal_share": m(r["modal_share"] for r in headline),
        "compile_fail_rate": (
            sum(r["compile_fail"] for r in rows) / sum(r["n_compilations"] for r in rows)
            if sum(r["n_compilations"] for r in rows) else None),
        "inverted_disagreement": m(r["disagreement"] for r in inverted),
        "by_stratum": {},
    }
    for axis in ("S", "H", "prov", "D_observed"):
        buckets = defaultdict(list)
        for r in headline:
            buckets[r.get(axis)].append(r)
        out["by_stratum"][axis] = {
            str(k): {"n": len(v), "PC": m(x["PC"] for x in v),
                     "PC_correct": m(x["PC_correct"] for x in v),
                     "agreement_at_witness": m(x["agreement_at_witness"] for x in v)}
            for k, v in sorted(buckets.items(), key=lambda t: str(t[0]))
        }
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--intents", default="eval/nl_consistency_intents.json")
    ap.add_argument("--ontology", default="research/data/ontology.json")
    ap.add_argument("--dataset", default=os.environ.get("CARDGURU_DATASET",
                                                        "data/dataset.jsonl.gz"))
    ap.add_argument("--backend", choices=["api", "recorded", "stub"], default="recorded")
    ap.add_argument("--recorded", help="JSONL of pre-recorded compilations")
    ap.add_argument("--samples", type=int, default=3)
    ap.add_argument("--cache", default="eval/consistency/cache.json")
    ap.add_argument("--out", default="eval/consistency/results.json")
    ap.add_argument("--only", help="comma-separated intent ids")
    args = ap.parse_args(argv)

    with open(args.intents, encoding="utf-8") as f:
        spec = json.load(f)
    intents = spec["intents"]
    if args.only:
        want = {s.strip() for s in args.only.split(",")}
        intents = [i for i in intents if i["id"] in want]

    onto = Ontology.load(args.ontology)
    index = SearchIndex.load(args.dataset)

    if args.backend == "recorded":
        if not args.recorded:
            ap.error("--backend recorded needs --recorded PATH")
        backend = RecordedBackend(args.recorded)
    elif args.backend == "api":
        backend = ApiBackend(args.ontology)
    else:
        backend = StubBackend({})

    runner = Runner(index, onto, backend, Cache(args.cache), samples=args.samples)
    rows = [runner.run_intent(i) for i in intents if i.get("paraphrases")]
    runner.cache.save()

    report = {"version": spec.get("_version"), "backend": backend.name,
              "samples": args.samples, "summary": aggregate(rows), "intents": rows}
    if getattr(backend, "missing", None):
        report["missing_compilations"] = len(backend.missing)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)

    s = report["summary"]
    print(f"intents scored: {s['n_intents']}  (headline {s['n_headline']})")
    print(f"PC             {s['PC']}")
    print(f"PC_correct     {s['PC_correct']}   <- R2: read with agreement below")
    print(f"agreement@wit  {s['agreement_at_witness']}")
    print(f"SC             {s['SC']}")
    print(f"foil rate      {s['foil_rate']}")
    print(f"compile fail   {round(s['compile_fail_rate'], 3) if s['compile_fail_rate'] is not None else None}")
    print(f"inverted disag {s['inverted_disagreement']}   <- R3: HIGH is correct here")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
