"""M0 probe: can oracle text alone recover the Forge ability-kind inventory?

The grammar hypothesis (research/graphify-comparison territory): oracle text is
templated tightly enough that a hand-written grammar can derive the same ability
graph Forge's hand-authored scripts encode. M0 tests only the cheapest, most
falsifiable part of that: *segmentation and ability-type classification*.

Predictor input:  oracle text + type line. Nothing else.
Ground truth:     the Forge-derived node-kind bag for the same face.
Unit:             one face; a face "agrees" when the predicted multiset of
                  ability kinds {A,T,S,R,K} equals Forge's.

Kill criterion (pre-committed in the M0 design): if bag agreement is well under
~95%, oracle text is less templated than the grammar plan assumes and the plan
should be reconsidered before any grammar work starts.

The keyword lexicon is taken from the mined ontology (research/data/ontology.json),
which is the same posture cardguru/validate.py already takes toward compiled
queries: the ontology is the language's vocabulary. It is a lexicon of the
language, not per-card knowledge.

Usage:
    python3 research/scripts/m0_oracle_segment.py <cards.jsonl[.gz]> [out.json]
"""
from __future__ import annotations

import collections
import gzip
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ONTOLOGY = os.path.join(HERE, os.pardir, "data", "ontology.json")

# --- lexicon -----------------------------------------------------------------

# Forge "keywords" that are implementation hooks with no oracle-text counterpart.
# Kept as an explicit list so the report can separate grammar error from
# implementation-ontology noise.
IMPL_KEYWORDS = {
    "etbCounter", "ETBReplacement", "CARDNAME", "Undiscoverable",
    "HIDDEN", "MayFlashSac", "AllNonLegendaryCreatureNames",
}

ROMAN = r"(?:I{1,3}|IV|V?I{0,3})"
CHAPTER_RE = re.compile(rf"^{ROMAN}(?:\s*,\s*{ROMAN})*\s*(?:,|—|--|-)\s*", re.I)
LOYALTY_RE = re.compile(r"^[+−–\-]?\d+\s*:")
LEVEL_RE = re.compile(r"^LEVEL\s+\d+", re.I)
BULLET_RE = re.compile(r"^\s*[•*]")

# CR 207.2c ability words ("Landfall — ...") and Universes Beyond flavor names
# ("Heavy Power Hammer — Whenever ...") are italic, non-functional prefixes.
ABILITY_WORD_RE = re.compile(r"^[^—\n]{1,44}—\s*(?=[A-Z{])")

# 'X enters with N +1/+1 counters' is folded into Forge's implementation-only
# etbCounter keyword, which the truth bag excludes -- so it yields no node.
ETB_COUNTER_RE = re.compile(r"\benters?\b[^.]*\bwith\b[^.]*\bcounters?\b", re.I)
# 'enters tapped [unless ...]' IS a replacement effect in Forge (R:Event$ Moved).
ETB_TAPPED_RE = re.compile(r"\benters?\b[^.]*\btapped\b", re.I)
# Additional and alternative casting costs are S:Mode$ statics in Forge.
ALT_COST_RE = re.compile(
    r"(?:^as an additional cost to cast|\brather than pay\b[^.]*\bmana cost\b"
    r"|\byou may pay\b[^.]*\brather than\b)", re.I)

# A cost is what can appear left of the colon in an activated ability: mana
# symbols, a loyalty number, a cost verb, or a named cost-keyword ("Waterbend {8}").
COST_LEAD_RE = re.compile(
    r"^(?:\{[^}]*\}|[+−–\-]?\d+|"
    r"(?:tap|untap|sacrifice|discard|pay|exile|remove|return|reveal|put)\b)",
    re.I,
)
NAMED_COST_RE = re.compile(r"^[A-Z][A-Za-z'\- ]{1,24}\s*(?:\{[^}]*\}|\d+)\s*$")
# Planeswalker loyalty abilities are printed '[+1]:' / '[-2]:' in oracle text.
LOYALTY_BRACKET_RE = re.compile(r"^\[[+−–\-]?\d+\]\s*:")

TRIGGER_RE = re.compile(r"^(?:when|whenever|at\s+the\s+beginning|at\s+end\s+of)\b", re.I)
# Replacement / prevention templating (CR 614/615). A one-shot 'prevent the next
# N damage' on an instant is a spell ability, not an R node, so prevention only
# counts on permanents (handled in classify()).
REPLACEMENT_RE = re.compile(
    r"(?:\bwould\b[^.]*\binstead\b|\binstead\b[^.]*\bwould\b"
    r"|\bprevent\b[^.]*\bwould\b|\bif\b[^.]*\bwould\b[^.]*,\s*(?:that|it|they)\b)",
    re.I,
)
# Forge splits a multi-condition trigger ('enters or attacks') into one T node
# per condition; the rules read it as a single ability. Mirrored here so the
# comparison measures grammar quality rather than this known modelling split.
# Only a disjunction of *event verbs* splits -- 'an instant or sorcery spell'
# is a disjunction inside the event's object and stays one trigger.
EVENT_VERB = (r"enters?|attacks?|blocks?|dies|deals?|becomes?|taps?|untaps?|"
              r"leaves?|is\s+put|cycles?|discards?|draws?|gains?|loses?")
TRIGGER_OR_RE = re.compile(rf"\s+or\s+(?={EVENT_VERB})\b", re.I)


def load_keyword_lexicon() -> set[str]:
    with open(ONTOLOGY, encoding="utf-8") as f:
        ont = json.load(f)
    kws = set(ont.get("keywords") or {})
    return {k for k in kws if k not in IMPL_KEYWORDS}


# --- text normalisation ------------------------------------------------------

def strip_reminder(text: str) -> str:
    """Remove balanced parenthetical reminder text."""
    out, depth = [], 0
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def oracle_lines(oracle: str) -> list[str]:
    """Forge stores oracle text with literal backslash-n separators."""
    text = oracle.replace("\\n", "\n")
    lines = []
    for raw in text.split("\n"):
        line = strip_reminder(raw).strip()
        if not line:
            continue
        # Modal bullets and 'Choose one' continuations belong to the parent
        # ability, not to a new one.
        if BULLET_RE.match(line):
            if lines:
                lines[-1] += " " + line
            continue
        lines.append(line)
    return lines


def keyword_tokens(line: str, lexicon: set[str], lower_lex: dict[str, str]):
    """If the whole line is a comma-separated keyword list, return the keywords."""
    if len(line) > 120:
        return None
    # 'Cumulative upkeep—Put a -1/-1 counter': keyword with an em-dash cost.
    dash_parts = re.split(r"—|--", line, 1)
    if len(dash_parts) == 2:
        key = lower_lex.get(dash_parts[0].strip().lower())
        if key:
            return [key]
    parts = [p.strip().rstrip(".") for p in line.split(",")]
    if not parts or any(not p for p in parts):
        return None
    found = []
    for p in parts:
        # Keywords may carry a cost/number: 'Toxic 1', 'Ward {2}', 'Kicker {1}{R}'
        base = re.split(r"[\s{]", p, 1)[0].strip()
        for cand in (p, base):
            key = lower_lex.get(cand.lower())
            if key:
                found.append(key)
                break
        else:
            return None
    return found


def trigger_conditions(line: str) -> int:
    """Count Forge-style trigger nodes for one triggered-ability line."""
    event, _, _ = line.partition(",")
    return 1 + len(TRIGGER_OR_RE.findall(event))


def classify(line: str, is_spell: bool) -> str | None:
    """Classify one non-keyword ability line into a Forge node kind.

    Returns None for text that Forge folds into an implementation keyword and
    therefore contributes no node of its own.
    """
    if CHAPTER_RE.match(line) or LEVEL_RE.match(line):
        return "K"          # Saga/Class chapters are K:Chapter/K:Class in Forge
    if TRIGGER_RE.match(line):
        return "T"
    if LOYALTY_RE.match(line) or LOYALTY_BRACKET_RE.match(line):
        return "A"
    head, sep, _ = line.partition(":")
    if sep and len(head) <= 80:
        h = head.strip()
        if COST_LEAD_RE.match(h) or NAMED_COST_RE.match(h):
            return "A"
    if not is_spell:
        if ETB_COUNTER_RE.search(line):
            return None     # folded into K:etbCounter, excluded from truth
        if ETB_TAPPED_RE.search(line):
            return "R"
        if REPLACEMENT_RE.search(line):
            return "R"
    if is_spell:
        return "A"          # spell ability: A:SP$ in Forge
    return "S"


def predict(rec: dict, lexicon: set[str], lower_lex: dict[str, str]) -> collections.Counter:
    types = rec.get("types") or ""
    is_spell = ("Instant" in types) or ("Sorcery" in types)
    bag: collections.Counter = collections.Counter()
    spell_body = 0
    for line in oracle_lines(rec.get("oracle") or ""):
        kws = keyword_tokens(line, lexicon, lower_lex)
        if kws:
            bag["K"] += len(kws)
            continue
        line = ABILITY_WORD_RE.sub("", line, count=1)
        if ALT_COST_RE.search(line):
            bag["S"] += 1   # Forge models additional/alternative costs as S
            continue
        kind = classify(line, is_spell)
        if kind is None:
            continue
        if kind == "T":
            bag["T"] += trigger_conditions(line)
        elif is_spell and kind == "A":
            # A spell has exactly one spell ability; further sentences are its
            # sub-abilities, which Forge stores as SVar nodes, not A roots.
            spell_body += 1
        else:
            bag[kind] += 1
    if spell_body:
        bag["A"] += 1
    return bag


def truth(rec: dict, count_impl: bool = True) -> collections.Counter:
    bag: collections.Counter = collections.Counter()
    for n in rec["nodes"]:
        kind = n.get("kind")
        if kind not in ("A", "T", "S", "R", "K"):
            continue
        if kind == "K" and not count_impl and n.get("keyword") in IMPL_KEYWORDS:
            continue
        bag[kind] += 1
    return bag


# --- driver ------------------------------------------------------------------

def load_records(path: str):
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        first = f.readline()
        if first:
            obj = json.loads(first)
            if "_meta" not in obj:
                yield obj
        for line in f:
            yield json.loads(line)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    lexicon = load_keyword_lexicon()
    lower_lex = {k.lower(): k for k in lexicon}

    stats = collections.Counter()
    per_kind = {k: collections.Counter() for k in "ATSRK"}
    mismatch_examples: dict[str, list] = collections.defaultdict(list)
    delta_hist = collections.Counter()

    for rec in load_records(argv[1]):
        oracle = (rec.get("oracle") or "").strip()
        t_all = truth(rec, count_impl=True)
        t_real = truth(rec, count_impl=False)

        if not oracle:
            stats["no_oracle"] += 1
            if not t_all:
                stats["no_oracle_and_no_nodes"] += 1
            continue

        stats["scored"] += 1
        p = predict(rec, lexicon, lower_lex)

        for k in "ATSRK":
            per_kind[k]["pred"] += p[k]
            per_kind[k]["true"] += t_real[k]
            per_kind[k]["hit"] += min(p[k], t_real[k])

        if p == t_real:
            stats["exact_bag_match"] += 1
        elif {k: v for k, v in p.items() if k != "K"} == {
                k: v for k, v in t_real.items() if k != "K"}:
            stats["match_ignoring_keywords"] += 1

        if p == t_all:
            stats["exact_bag_match_impl_counted"] += 1

        if p != t_real:
            diff = tuple(sorted(
                (k, p[k] - t_real[k]) for k in "ATSRK" if p[k] != t_real[k]))
            delta_hist[diff] += 1
            if len(mismatch_examples[diff]) < 4:
                mismatch_examples[diff].append({
                    "name": rec.get("name"), "types": rec.get("types"),
                    "oracle": (rec.get("oracle") or "")[:220],
                    "pred": dict(p), "true": dict(t_real),
                })

    scored = stats["scored"] or 1
    report = {
        "scored_faces": stats["scored"],
        "skipped_no_oracle": stats["no_oracle"],
        "skipped_no_oracle_and_no_nodes": stats["no_oracle_and_no_nodes"],
        "exact_bag_match": stats["exact_bag_match"],
        "exact_bag_match_pct": round(100 * stats["exact_bag_match"] / scored, 2),
        "exact_bag_match_impl_keywords_counted_pct": round(
            100 * stats["exact_bag_match_impl_counted"] / scored, 2),
        "match_ignoring_keyword_counts_pct": round(
            100 * (stats["exact_bag_match"] + stats["match_ignoring_keywords"]) / scored, 2),
        "per_kind": {},
        "top_mismatch_shapes": [],
    }
    for k in "ATSRK":
        c = per_kind[k]
        report["per_kind"][k] = {
            "true": c["true"], "pred": c["pred"], "matched": c["hit"],
            "recall_pct": round(100 * c["hit"] / c["true"], 2) if c["true"] else None,
            "precision_pct": round(100 * c["hit"] / c["pred"], 2) if c["pred"] else None,
        }
    for diff, n in delta_hist.most_common(15):
        report["top_mismatch_shapes"].append({
            "delta": {k: v for k, v in diff},
            "faces": n,
            "pct": round(100 * n / scored, 2),
            "examples": mismatch_examples[diff],
        })

    out = argv[2] if len(argv) > 2 else None
    text = json.dumps(report, indent=1)
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        slim = dict(report)
        slim["top_mismatch_shapes"] = [
            {kk: vv for kk, vv in s.items() if kk != "examples"}
            for s in report["top_mismatch_shapes"]]
        print(json.dumps(slim, indent=1))
        print(f"\nfull report (with examples) -> {out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
