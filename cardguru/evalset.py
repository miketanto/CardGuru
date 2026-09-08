"""Execution-accuracy scoring for the 40-question NL->DSL eval set.

`benchmark/candidate_questions.json` carries 40 questions with
`expect_present` / `expect_absent` goldens. Until now nothing ran them against
a live compile — `benchmark/compiled_questions.json` records the result of one
hand-vetted compile, and the goldens were checked once, by hand, at that time.
This module turns that pair of files into a repeatable measurement.

Grading is on EXECUTION, not on the query string. Two different queries that
return the same cards are both correct, so a compiled query is scored purely by
the card names it returns:

  golden pass   every `expect_present` name is in the result set and no
                `expect_absent` name is  (the headline, all-or-nothing)
  recall        fraction of `expect_present` names found (partial credit,
                moves smoothly, so a small improvement is visible)
  overlap       Jaccard of the result set against the hand-vetted reference
                query's result set — an unsupervised agreement signal that
                needs no goldens

Three of the 40 are marked `unexpressible` in the reference file and carry no
goldens at all (both lists empty), so no query can pass or fail them. They are
reported separately and excluded from the denominator rather than silently
counted as failures — a question the DSL provably cannot express is not a
compiler error.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUESTIONS_PATH = os.path.join(HERE, "benchmark", "candidate_questions.json")
REFERENCE_PATH = os.path.join(HERE, "benchmark", "compiled_questions.json")


def load_questions(path: str = QUESTIONS_PATH) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_reference(path: str = REFERENCE_PATH) -> dict[str, dict]:
    with open(path, encoding="utf-8") as f:
        return {e["id"]: e for e in json.load(f)}


def is_scorable(q: dict) -> bool:
    """A question with no goldens on either side cannot be scored at all."""
    return bool(q.get("expect_present") or q.get("expect_absent"))


def jaccard(a: set, b: set) -> float | None:
    """None when there is nothing to compare — 0.0 would read as disagreement."""
    if not a and not b:
        return None
    return len(a & b) / len(a | b)


def score_one(question: dict, hits: set[str], reference_hits: set[str] | None = None,
              compiled: bool = True, error: str | None = None) -> dict:
    """Score one compiled+executed question against its goldens."""
    present = list(question.get("expect_present") or [])
    absent = list(question.get("expect_absent") or [])
    missing = [n for n in present if n not in hits]
    leaked = [n for n in absent if n in hits]
    scorable = is_scorable(question)
    return {
        "id": question["id"],
        "question": question["question"],
        "difficulty": question.get("difficulty"),
        "area": question.get("mechanical_area"),
        "compiled": compiled,
        "error": error,
        "hits": len(hits),
        "scorable": scorable,
        "present_total": len(present),
        "present_found": len(present) - len(missing),
        "missing": missing,
        "absent_total": len(absent),
        "absent_leaked": leaked,
        # A question that failed to compile fails its goldens; one with no
        # goldens is neither pass nor fail.
        "passed": bool(scorable and compiled and not missing and not leaked),
        "overlap": (jaccard(hits, reference_hits)
                    if reference_hits is not None and compiled else None),
    }


def aggregate(rows: list[dict]) -> dict:
    scorable = [r for r in rows if r["scorable"]]
    present_total = sum(r["present_total"] for r in scorable)
    present_found = sum(r["present_found"] for r in scorable)
    absent_total = sum(r["absent_total"] for r in scorable)
    absent_leaked = sum(len(r["absent_leaked"]) for r in scorable)
    overlaps = [r["overlap"] for r in scorable if r["overlap"] is not None]
    return {
        "n": len(rows),
        "n_scorable": len(scorable),
        "n_excluded": len(rows) - len(scorable),
        "excluded_ids": [r["id"] for r in rows if not r["scorable"]],
        "compiled": sum(1 for r in rows if r["compiled"]),
        "passed": sum(1 for r in scorable if r["passed"]),
        "pass_rate": (sum(1 for r in scorable if r["passed"]) / len(scorable)
                      if scorable else 0.0),
        "present_total": present_total,
        "present_found": present_found,
        "recall": present_found / present_total if present_total else 0.0,
        "absent_total": absent_total,
        "absent_respected": absent_total - absent_leaked,
        "absent_rate": ((absent_total - absent_leaked) / absent_total
                        if absent_total else 0.0),
        "mean_overlap": (sum(overlaps) / len(overlaps)) if overlaps else None,
        "n_overlap": len(overlaps),
        "zero_hit": sum(1 for r in rows if r["compiled"] and r["hits"] == 0),
    }


def headline(agg: dict, label: str = "") -> str:
    """The one number the harness exists to print, plus what backs it."""
    tag = f" [{label}]" if label else ""
    ov = ("n/a" if agg["mean_overlap"] is None
          else f"{agg['mean_overlap']:.3f} (n={agg['n_overlap']})")
    return "\n".join([
        f"EXECUTION ACCURACY{tag}: "
        f"{agg['passed']}/{agg['n_scorable']} ({agg['pass_rate']*100:.1f}%) "
        f"questions pass every golden",
        f"  golden recall     {agg['present_found']}/{agg['present_total']} "
        f"expect_present cards found ({agg['recall']*100:.1f}%)",
        f"  absent respected  {agg['absent_respected']}/{agg['absent_total']} "
        f"({agg['absent_rate']*100:.1f}%)",
        f"  compiled ok       {agg['compiled']}/{agg['n']}",
        f"  zero-hit queries  {agg['zero_hit']}/{agg['n']}",
        f"  set overlap       mean Jaccard vs vetted reference = {ov}",
        f"  excluded          {agg['n_excluded']} question(s) with no goldens: "
        + (", ".join(agg["excluded_ids"]) or "none"),
    ])


def render_report(rows: list[dict], agg: dict, title: str,
                  preamble: list[str] | None = None) -> str:
    lines = [f"# {title}", ""]
    lines += (preamble or [])
    lines += ["", "```", headline(agg), "```", "",
              "| id | difficulty | hits | present | absent | overlap | result |",
              "|---|---|---:|---:|---:|---:|---|"]
    for r in rows:
        if not r["scorable"]:
            verdict = "excluded (no goldens)"
        elif not r["compiled"]:
            verdict = "COMPILE FAIL"
        else:
            verdict = "pass" if r["passed"] else "FAIL"
        ov = "-" if r["overlap"] is None else f"{r['overlap']:.2f}"
        lines.append(
            f"| {r['id']} | {r['difficulty']} | {r['hits']} | "
            f"{r['present_found']}/{r['present_total']} | "
            f"{r['absent_total']-len(r['absent_leaked'])}/{r['absent_total']} | "
            f"{ov} | {verdict} |")
    lines.append("")

    bad = [r for r in rows if r["scorable"] and not r["passed"]]
    if bad:
        lines += ["## Failures", ""]
        for r in bad:
            lines.append(f"### {r['id']}")
            lines.append("")
            lines.append(f"*{r['question']}*")
            lines.append("")
            if r["error"]:
                lines.append(f"- compile error: {r['error']}")
            lines.append(f"- hits: {r['hits']}")
            if r["missing"]:
                lines.append(f"- MISSING: {r['missing']}")
            if r["absent_leaked"]:
                lines.append(f"- LEAKED (expected absent): {r['absent_leaked']}")
            if r.get("query") is not None:
                lines.append("- query:")
                lines.append("")
                lines.append("```json")
                lines.append(json.dumps(r["query"], indent=1))
                lines.append("```")
            if r.get("trace"):
                lines.append("- compile trace:")
                lines.append("")
                lines.append("```")
                lines += r["trace"]
                lines.append("```")
            lines.append("")
    return "\n".join(lines) + "\n"
