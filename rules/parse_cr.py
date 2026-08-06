#!/usr/bin/env python3
"""Parse the Comprehensive Rules plain text into structured JSON.

The CR is a pre-authored ontology: numbered hierarchy (section 7 -> 702 ->
702.19 -> 702.19a), explicit cross-references ("see rule 702.19"), examples,
and a glossary. This parser turns it into:

  research/data/cr_rules.json
    {"effective": "...", "rules": {num: {"text", "title"?, "examples": [],
     "refs": [], "parent"}}, "glossary": {term: definition}}

Usage: python rules/parse_cr.py [MagicCompRules.txt] [out.json]
"""
from __future__ import annotations

import json
import re
import sys

RULE_RE = re.compile(r"^(\d{3})\.(\d+)([a-z])?\.?\s+(.*)$")   # 702.19a text / 702.19. Title
SECTION_RE = re.compile(r"^(\d{3})\.\s+(.*)$")                # 702. Keyword Abilities
CHAPTER_RE = re.compile(r"^(\d)\.\s+(.*)$")                   # 7. Additional Rules
REF_RE = re.compile(r"rule (\d{3}(?:\.\d+)?[a-z]?)")
EFFECTIVE_RE = re.compile(r"effective as of (.+?)\.")


def parent_of(num: str) -> str | None:
    m = re.match(r"^(\d{3})\.(\d+)([a-z])$", num)
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    m = re.match(r"^(\d{3})\.(\d+)$", num)
    if m:
        return m.group(1)
    m = re.match(r"^(\d{3})$", num)
    if m:
        return num[0]
    return None


def parse(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    lines = [l.rstrip() for l in text.splitlines()]

    effective = None
    for l in lines[:10]:
        m = EFFECTIVE_RE.search(l)
        if m:
            effective = m.group(1)
            break

    # The rules body runs from the first "1. Game Concepts" chapter heading
    # *after* the table of contents to the second "Glossary" line.
    glossary_positions = [i for i, l in enumerate(lines) if l.strip() == "Glossary"]
    body_end = glossary_positions[1] if len(glossary_positions) > 1 else len(lines)
    # skip the ToC: find the last occurrence of "1. Game Concepts" before body_end
    starts = [i for i, l in enumerate(lines[:body_end]) if l.strip() == "1. Game Concepts"]
    body_start = starts[-1] if starts else 0

    rules: dict[str, dict] = {}
    current = None
    for l in lines[body_start:body_end]:
        s = l.strip()
        if not s:
            continue
        m = RULE_RE.match(s)
        if m:
            num = f"{m.group(1)}.{m.group(2)}{m.group(3) or ''}"
            body = m.group(4)
            entry = {"text": body, "examples": [], "parent": parent_of(num)}
            # a rule with no subrule letter and a short capitalized body is a title
            if not m.group(3) and len(body) < 80 and not body.endswith("."):
                entry["title"] = body
                entry["text"] = ""
            rules[num] = entry
            current = num
            continue
        m = SECTION_RE.match(s)
        if m and m.group(1) in s[:5]:
            rules[m.group(1)] = {"title": m.group(2), "text": "", "examples": [],
                                 "parent": parent_of(m.group(1))}
            current = m.group(1)
            continue
        m = CHAPTER_RE.match(s)
        if m:
            rules[m.group(1)] = {"title": m.group(2), "text": "", "examples": [],
                                 "parent": None}
            current = m.group(1)
            continue
        if current:
            if s.startswith("Example:"):
                rules[current]["examples"].append(s[len("Example:"):].strip())
            else:
                rules[current]["text"] = (rules[current]["text"] + " " + s).strip()

    for num, entry in rules.items():
        refs = sorted({r for r in REF_RE.findall(entry["text"]) if r != num})
        entry["refs"] = refs

    # Glossary: after the second "Glossary" line; entries are term line(s)
    # followed by definition lines; terms are short lines with no period.
    glossary: dict[str, str] = {}
    if len(glossary_positions) > 1:
        term = None
        buf: list[str] = []
        for l in lines[glossary_positions[1] + 1:]:
            s = l.strip()
            if not s:
                continue
            if s == "Credits":
                break
            is_term = len(s) < 60 and not s.endswith(".") and not s.startswith("See")
            if is_term and (term is None or buf):
                if term and buf:
                    glossary[term] = " ".join(buf)
                term, buf = s, []
            elif term:
                buf.append(s)
        if term and buf:
            glossary[term] = " ".join(buf)

    return {"effective": effective, "rules": rules, "glossary": glossary}


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "/home/user/mse/data/MagicCompRules.txt"
    out = sys.argv[2] if len(sys.argv) > 2 else "research/data/cr_rules.json"
    data = parse(src)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    n_rules = len(data["rules"])
    n_sub = sum(1 for k in data["rules"] if re.match(r"\d{3}\.\d+[a-z]?$", k))
    n_refs = sum(len(r["refs"]) for r in data["rules"].values())
    n_ex = sum(len(r["examples"]) for r in data["rules"].values())
    print(json.dumps({"effective": data["effective"], "entries": n_rules,
                      "numbered_rules": n_sub, "cross_refs": n_refs,
                      "examples": n_ex, "glossary_terms": len(data["glossary"])},
                     indent=1))


if __name__ == "__main__":
    main()
