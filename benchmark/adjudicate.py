#!/usr/bin/env python3
"""Turn the contested pool into denser goldens, by judging cards against the
question rather than against any query.

Why this and not more seeds: across six runs only 2 of 37 question verdicts
ever flip. Nineteen pass every time, sixteen fail every time. The benchmark is
saturated, not noisy — so extra seeds buy nothing, and the resolution has to
come from inside the questions. Each question carries ~3 `expect_present`
cards, so "found 2 of 3" and "found 0 of 3" score identically on the headline
and every partial improvement is invisible.

    python benchmark/adjudicate.py tasks   --out benchmark/adjudication/
    python benchmark/adjudicate.py merge   --out benchmark/candidate_questions.dense.json

The adjudicator sees the question, its `trap` and `notes`, and each card's name,
type line and oracle text. It does NOT see any query, which system returned the
card, or how many did — an assessor who can see the vote count ratifies the
majority instead of reading the card, and the goldens would then only ever
confirm what the current compiler already does.

`unclear` is a first-class verdict and stays unjudged. A card nobody can call
from the question wording is evidence the QUESTION is underdetermined, which is
worth recording rather than forcing to a side.
"""
import argparse
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru import dataset as ds  # noqa: E402
from cardguru import evalset  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATASET = os.environ.get("CARDGURU_DATASET",
                         os.path.join(HERE, "..", "data", "dataset.jsonl.gz"))
POOL = os.path.join(HERE, "pool.json")
ADJ = os.path.join(HERE, "adjudication")

# Cap per question so this finishes. Sampling is deterministic and spread
# evenly over the name-sorted pool, so it is not biased toward the cards the
# systems happened to agree about.
MAX_PER_QUESTION = 30


def card_text(dataset_path):
    _meta, records = ds.load(dataset_path)
    out = {}
    for r in records:
        n = r.get("name")
        if n and n not in out:
            out[n] = {"types": r.get("types") or "",
                      "manaCost": r.get("manaCost") or "",
                      "oracle": (r.get("oracle") or "").replace("\n", " ")}
    return out


def sample(names, k):
    if len(names) <= k:
        return list(names)
    step = len(names) / k
    return [names[int(i * step)] for i in range(k)]


def cmd_tasks(args):
    with open(args.pool, encoding="utf-8") as f:
        pool = json.load(f)
    questions = {q["id"]: q for q in evalset.load_questions(args.questions)}
    text = card_text(args.dataset)
    os.makedirs(args.out, exist_ok=True)
    os.makedirs(os.path.join(args.out, "verdicts"), exist_ok=True)

    total = 0
    for qid, entry in sorted(pool.items()):
        picks = sample(entry["contested"], args.max_per_question)
        if not picks:
            continue
        q = questions[qid]
        lines = [
            f"# Adjudication: `{qid}`", "",
            "Decide, for each card below, whether it satisfies the QUESTION.",
            "Judge the card on its own text. There is no query here and you do "
            "not know which search returned it — that is deliberate.", "",
            "## Question", "",
            f"> {q['question']}", "",
        ]
        if q.get("trap"):
            lines += [f"**What makes it tricky:** {q['trap']}", ""]
        if q.get("notes"):
            lines += [f"**Author's notes:** {q['notes']}", ""]
        already = q.get("expect_present") or []
        if already:
            lines += ["**Cards already accepted as satisfying it** (for a "
                      "consistent reading, not as a pattern to match): "
                      + ", ".join(already), ""]
        nope = q.get("expect_absent") or []
        if nope:
            lines += ["**Cards already rejected**: " + ", ".join(nope), ""]
        lines += [
            "## Cards", "",
            "| # | card | type | text |", "|---|---|---|---|",
        ]
        for i, name in enumerate(picks, 1):
            t = text.get(name, {})
            lines.append(f"| {i} | {name} | {t.get('types','?')} | "
                         f"{t.get('oracle','?')[:300]} |")
        lines += [
            "", "## Answer format", "",
            f"Write JSON to `verdicts/{qid}.json`: an object mapping each card "
            "name to `\"present\"`, `\"absent\"` or `\"unclear\"`.", "",
            "- `present` — it clearly satisfies the question.",
            "- `absent`  — it clearly does not.",
            "- `unclear` — the question wording genuinely does not decide it. "
            "Use this freely; a forced call is worse than no call.", "",
            "Every one of the cards listed must appear exactly once.",
        ]
        with open(os.path.join(args.out, f"{qid}.md"), "w",
                  encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        total += len(picks)
    print(f"wrote {len(pool)} task files, {total} cards to adjudicate -> {args.out}")


def cmd_merge(args):
    questions = evalset.load_questions(args.questions)
    vdir = os.path.join(args.adjudication, "verdicts")
    verdicts = {}
    for fn in sorted(os.listdir(vdir)):
        if fn.endswith(".json"):
            with open(os.path.join(vdir, fn), encoding="utf-8") as f:
                verdicts[os.path.splitext(fn)[0]] = json.load(f)

    tally = Counter()
    for q in questions:
        v = verdicts.get(q["id"])
        if not v:
            continue
        present = list(q.get("expect_present") or [])
        absent = list(q.get("expect_absent") or [])
        unclear = list(q.get("unclear") or [])
        for name, verdict in sorted(v.items()):
            if name in present or name in absent:
                continue
            if verdict == "present":
                present.append(name)
            elif verdict == "absent":
                absent.append(name)
            else:
                unclear.append(name)
            tally[verdict] += 1
        q["expect_present"] = present
        q["expect_absent"] = absent
        if unclear:
            # Kept out of scoring on purpose: a card the question wording does
            # not decide is a fact about the QUESTION, and burying it would
            # lose the only record that the question is underdetermined.
            q["unclear"] = unclear

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=1, ensure_ascii=False)
        f.write("\n")
    p = sum(len(q.get("expect_present") or []) for q in questions)
    a = sum(len(q.get("expect_absent") or []) for q in questions)
    u = sum(len(q.get("unclear") or []) for q in questions)
    print(f"merged {sum(tally.values())} verdicts: {dict(tally)}")
    print(f"goldens now: present={p} absent={a} unclear(excluded)={u}")
    print(f"wrote {args.out}")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tasks")
    t.add_argument("--out", default=ADJ)
    t.add_argument("--pool", default=POOL)
    t.add_argument("--questions", default=evalset.QUESTIONS_PATH)
    t.add_argument("--dataset", default=DATASET)
    t.add_argument("--max-per-question", type=int, default=MAX_PER_QUESTION)
    t.set_defaults(fn=cmd_tasks)
    m = sub.add_parser("merge")
    m.add_argument("--adjudication", default=ADJ)
    m.add_argument("--questions", default=evalset.QUESTIONS_PATH)
    m.add_argument("--out", default=os.path.join(HERE,
                                                 "candidate_questions.dense.json"))
    m.set_defaults(fn=cmd_merge)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
