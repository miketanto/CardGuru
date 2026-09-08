#!/usr/bin/env python3
"""End-to-end NL -> DSL execution-accuracy harness.

Compiles all 40 questions in `benchmark/candidate_questions.json` from scratch,
runs each compiled query against the card corpus, scores the result set against
the `expect_present` / `expect_absent` goldens, and prints one number.

    python benchmark/eval_compile.py --source reference   # offline: the ceiling
    python benchmark/eval_compile.py --signals off        # live, validate-only
    python benchmark/eval_compile.py --signals zero       # live, + zero-hit repair
    python benchmark/eval_compile.py --signals full       # live, + dead predicates
    python benchmark/eval_compile.py --source agent       # in-session agents, no API spend

`--source agent` replaces only the model turn: in-session agents answer the
same requests the API would have received, through the same system prompt,
validator gate and execution feedback, so the score is directly comparable to a
`--source live` run. It is run repeatedly — each invocation folds in whatever
answers exist, advances every question as far as it can, and writes task files
for the turns still owed. See `cardguru/agent_bridge.py`.

`--source reference` scores the hand-vetted queries already recorded in
`benchmark/compiled_questions.json` instead of calling the API. It needs no
credentials and answers a different question: how well can this DSL, driven by a
careful human, satisfy these goldens at all? That is the ceiling every live run
is measured against, and it is also the regression test for the scorer itself.

`--signals` selects the execution feedback wired into the compile loop, and is
part of the on-disk cache key, so the arms of an A/B never serve each other's
cached compiles.

Exit code is 0 unless the run itself failed; a low score is a result, not an
error, so this is not a pass/fail gate like `benchmark/run.py`.
"""
import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru import evalset  # noqa: E402
from cardguru.index import SearchIndex  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATASET = os.environ.get("CARDGURU_DATASET",
                         os.path.join(HERE, "..", "data", "dataset.jsonl.gz"))
ONTOLOGY = os.path.join(HERE, "..", "research", "data", "ontology.json")


def run_query(index, query):
    """Returns (names, error). A query can pass `validate()` and still explode
    at evaluation time — the validator checks vocabulary, not value-predicate
    shape, so e.g. {"not": ...} used where a value predicate goes gets through
    and raises in `match_value`. That is a real defect to report, not a reason
    to lose the other 39 questions."""
    if query is None:
        return set(), None
    try:
        return {h["record"]["name"] for h in index.search(query)}, None
    except Exception as e:
        return set(), f"{type(e).__name__}: {e}"


def compile_all(questions, index, args):
    """Compile every question, in parallel. Returns {id: CompileResult-ish}."""
    from cardguru.nl_compiler import MODEL, compile_question
    from cardguru.repair import make_checker

    model = args.model or MODEL
    out = {}

    def one(q):
        # One checker per question: it accumulates a log, and sharing it across
        # threads would interleave the records.
        checker = make_checker(index, args.signals)
        try:
            res = compile_question(q["question"], ONTOLOGY, model=model,
                                   max_retries=args.max_retries,
                                   use_cache=not args.no_cache,
                                   checker=checker)
            return q["id"], res, None
        except Exception as e:                      # one bad question must not
            return q["id"], None, f"{type(e).__name__}: {e}"   # kill the run

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for qid, res, err in pool.map(one, questions):
            out[qid] = (res, err)
            done = len(out)
            print(f"  [{done}/{len(questions)}] {qid}"
                  + (f"  ERROR {err}" if err else ""), file=sys.stderr)
    return out


def compile_all_agent(questions, index, args):
    """Advance an agent-driven run by one round.

    Returns ({id: (result, error)}, pending_ids). A non-empty pending list means
    the round is not finished: agents must answer the task files before the
    same command is run again.
    """
    from cardguru.agent_bridge import RunDir, step
    from cardguru.nl_compiler import build_system_prompt
    from cardguru.repair import make_checker

    run = RunDir(args.run_dir or os.path.join(HERE, "agent_runs", args.signals))
    with open(ONTOLOGY, encoding="utf-8") as f:
        run.write_system_prompt(build_system_prompt(json.load(f)))

    state = run.load_state()
    folded = run.collect_answers(state)
    run.save_state(state)
    if folded:
        print(f"folded in {folded} answer(s)", file=sys.stderr)
    run.clear_pending()

    out, pending = {}, []
    for q in questions:
        qid = q["id"]
        answers = state.get(qid, [])
        try:
            res, request = step(q["question"], qid, answers, ONTOLOGY,
                                checker=make_checker(index, args.signals),
                                max_retries=args.max_retries)
        except Exception as e:
            out[qid] = (None, f"{type(e).__name__}: {e}")
            continue
        if request is not None:
            run.write_task(qid, q["question"], request, turn=len(answers) + 1)
            pending.append(qid)
        else:
            out[qid] = (res, None)
    return out, pending, run


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--source", choices=("live", "reference", "agent"),
                   default="live",
                   help="live = compile via the API; reference = score the "
                        "hand-vetted queries in compiled_questions.json; "
                        "agent = in-session agents answer the model turns "
                        "(no API spend). Re-run the same command each round.")
    p.add_argument("--run-dir", default=None,
                   help="agent source: state directory "
                        "(default benchmark/agent_runs/<signals>)")
    p.add_argument("--signals", choices=("off", "zero", "full"), default="zero",
                   help="execution feedback in the compile loop (live only)")
    p.add_argument("--model", default=None)
    p.add_argument("--max-retries", type=int, default=2)
    p.add_argument("--no-cache", action="store_true",
                   help="force live API calls instead of reusing cached compiles")
    p.add_argument("--jobs", type=int, default=4)
    p.add_argument("--limit", type=int, default=None,
                   help="only the first N questions (smoke test)")
    p.add_argument("--dataset", default=DATASET)
    p.add_argument("--questions", default=None,
                   help="golden set (default benchmark/candidate_questions.json; "
                        "pass candidate_questions.dense.json for the pooled, "
                        "adjudicated goldens — see research/benchmark-density.md)")
    p.add_argument("--out", default=None,
                   help="markdown report path (default: derived from the run)")
    p.add_argument("--json-out", default=None, help="raw per-question rows")
    args = p.parse_args()

    questions = (evalset.load_questions(args.questions) if args.questions
                 else evalset.load_questions())
    if args.limit:
        questions = questions[:args.limit]
    reference = evalset.load_reference()

    t0 = time.time()
    index = SearchIndex.load(args.dataset)
    print(f"index: {len(index.records)} faces in {time.time()-t0:.1f}s",
          file=sys.stderr)

    label = {"reference": "reference",
             "live": f"live/{args.signals}",
             "agent": f"agent/{args.signals}"}[args.source]

    compiled = {}
    if args.source == "live":
        t0 = time.time()
        compiled = compile_all(questions, index, args)
        print(f"compiled {len(compiled)} questions in {time.time()-t0:.0f}s",
              file=sys.stderr)
    elif args.source == "agent":
        compiled, pending, run = compile_all_agent(questions, index, args)
        if pending:
            # Not a partial score: scoring now would count unanswered questions
            # as failures and report a number that means nothing.
            print(f"\n{len(pending)} question(s) need a model turn.\n"
                  f"  system prompt : {os.path.join(run.path, 'system_prompt.md')}\n"
                  f"  task files    : {os.path.join(run.path, 'pending')}/\n"
                  f"  write answers : {os.path.join(run.path, 'answers')}/<id>.txt\n"
                  f"Then re-run this exact command to advance the round.")
            print(f"pending: {', '.join(pending)}", file=sys.stderr)
            return

    rows = []
    for q in questions:
        ref_entry = reference.get(q["id"], {})
        ref_query = ref_entry.get("query")
        ref_hits = run_query(index, ref_query)[0] if ref_query else None

        if args.source == "reference":
            query, err = ref_query, None
            ok = ref_query is not None
            trace = []
            # Comparing the reference against itself would report 1.00 for every
            # row and say nothing.
            ref_hits = None
        else:                                   # live or agent
            res, err = compiled.get(q["id"], (None, "not compiled"))
            query = res.query if res else None
            ok = bool(res and res.ok)
            trace = []
            if res:
                trace = [f"attempts={len(res.attempts)} checks={res.checks}"
                         f" exhausted={res.exhausted}"]
                for text, errs in res.attempts:
                    if errs:
                        trace.append(f"  rejected: {errs}")

        hits, run_err = (run_query(index, query) if ok else (set(), None))
        if run_err:
            # It compiled and validated but cannot be executed, so it is not a
            # usable query — count it as a compile failure and say why.
            ok, err = False, run_err
        row = evalset.score_one(q, hits, reference_hits=ref_hits,
                                compiled=ok, error=err)
        row["query"] = query
        row["trace"] = trace
        rows.append(row)

    agg = evalset.aggregate(rows)
    print()
    print(evalset.headline(agg, label))

    preamble = [
        f"Source: **{label}**"
        + (f" · model `{args.model or os.environ.get('CARDGURU_MODEL', 'default')}`"
           if args.source == "live" else ""),
        "",
        "Graded on execution: a compiled query is scored by the card names it "
        "returns, not by its text. Two different queries returning the same "
        "cards are both correct.",
    ]
    out = args.out or os.path.join(
        HERE, f"eval_report_{label.replace('/', '_')}.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(evalset.render_report(rows, agg, f"NL->DSL execution accuracy ({label})",
                                      preamble))
    print(f"\nwrote {out}", file=sys.stderr)

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump({"label": label, "aggregate": agg, "rows": rows}, f, indent=1)
        print(f"wrote {args.json_out}", file=sys.stderr)


if __name__ == "__main__":
    main()
