#!/usr/bin/env python3
"""Extract per-set 'unfinished' card lists from XMage set definitions.

XMage marks partially-implemented cards in a set-file list; those cards are
excluded from the playable card DB and fail loudly at scenario setup. This
extractor turns the lists into data so the product can pre-screen: 'the
engine cannot verify this card yet' before attempting execution.

Usage: python corpus/extract_unfinished.py <mage-repo> [out.json]
"""
from __future__ import annotations

import json
import os
import re
import sys

LIST_RE = re.compile(
    r'List<String>\s+unfinished\s*=\s*Arrays\.asList\(([^;]*)\);', re.DOTALL)
NAME_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')
SET_RE = re.compile(r'super\("([^"]+)",\s*"([^"]+)"')


def main():
    mage_repo = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("CARDGURU_MAGE_REPO")
    out_path = sys.argv[2] if len(sys.argv) > 2 else "research/data/xmage_unfinished.json"
    sets_dir = os.path.join(mage_repo, "Mage.Sets/src/mage/sets")

    result = {}
    total = 0
    for fn in sorted(os.listdir(sets_dir)):
        if not fn.endswith(".java"):
            continue
        src = open(os.path.join(sets_dir, fn), encoding="utf-8", errors="replace").read()
        m = LIST_RE.search(src)
        if not m:
            continue
        names = [n.replace('\\"', '"') for n in NAME_RE.findall(m.group(1))]
        if not names:
            continue
        sm = SET_RE.search(src)
        key = f"{sm.group(2)} ({sm.group(1)})" if sm else fn[:-5]
        result[key] = sorted(names)
        total += len(names)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"_total_unfinished": total, "sets": result}, f, indent=1)
    print(f"{total} unfinished cards across {len(result)} sets -> {out_path}")
    for k, v in result.items():
        print(f"  {k}: {len(v)}")


if __name__ == "__main__":
    main()
