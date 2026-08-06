#!/usr/bin/env python3
"""Seed the simulated-scenario corpus from XMage's own regression suite.

Walks Mage.Tests/src/test/java/org/mage/test/cards/**, extracts each @Test
method's setup calls, scripted actions, and assertions into structured
records — thousands of human-reviewed scenario→assertion pairs for free.

Usage:
  python corpus/parse_mage_tests.py <mage-repo> [out.jsonl]

Writes JSONL records plus a stats summary (printed and saved next to the
output). Records are heuristic regex extractions: `coverage` on each record
reports recognized vs total harness calls in that method, so downstream
consumers can filter to fully-parsed scenarios.
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter

CALL_PATTERNS = {
    "add_card": re.compile(
        r'addCard\(Zone\.(\w+),\s*(player\w+),\s*"([^"]+)"(?:,\s*(\d+))?(?:,\s*(true|false))?\)'),
    "set_life": re.compile(r'setLife\((player\w+),\s*(\d+)\)'),
    "cast": re.compile(r'castSpell\((\d+),\s*PhaseStep\.(\w+),\s*(player\w+),\s*"([^"]+)"'),
    "activate": re.compile(
        r'activateAbility\((\d+),\s*PhaseStep\.(\w+),\s*(player\w+),\s*"([^"]+)"'),
    "play_land": re.compile(r'playLand\((\d+),\s*PhaseStep\.(\w+),\s*(player\w+),\s*"([^"]+)"'),
    "attack": re.compile(r'attack\((\d+),\s*(player\w+),\s*"([^"]+)"'),
    "block": re.compile(r'block\((\d+),\s*(player\w+),\s*"([^"]+)",\s*"([^"]+)"'),
    "choice": re.compile(r'setChoice\((player\w+),\s*(?:"([^"]*)"|(\w+))'),
    "target": re.compile(r'addTarget\((player\w+),\s*"([^"]*)"'),
    "mode": re.compile(r'setModeChoice\((player\w+),\s*"([^"]*)"'),
}
ASSERT_RE = re.compile(r'\b(assert\w+)\(([^;]*)\);')
TEST_RE = re.compile(r'@Test\s+public\s+void\s+(\w+)\s*\([^)]*\)[^{]*\{')
HARNESS_CALL_RE = re.compile(
    r'\b(addCard|setLife|castSpell|activateAbility|playLand|attack|block|setChoice|'
    r'addTarget|setModeChoice|assert\w+)\s*\(')


def method_body(src: str, start: int) -> str:
    depth = 0
    for i in range(start, len(src)):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return src[start:i + 1]
    return src[start:]


def parse_method(name: str, body: str, rel: str, cls: str) -> dict:
    setup, actions, assertions = [], [], []
    for kind, rx in CALL_PATTERNS.items():
        for m in rx.finditer(body):
            g = m.groups()
            if kind == "add_card":
                item = {"kind": kind, "zone": g[0], "player": g[1], "card": g[2],
                        "count": int(g[3] or 1), "tapped": g[4] == "true"}
                setup.append(item)
            elif kind == "set_life":
                setup.append({"kind": kind, "player": g[0], "value": int(g[1])})
            elif kind in ("cast", "activate", "play_land"):
                actions.append({"kind": kind, "turn": int(g[0]), "phase": g[1],
                                "player": g[2], "what": g[3]})
            elif kind == "attack":
                actions.append({"kind": kind, "turn": int(g[0]), "player": g[1],
                                "attacker": g[2]})
            elif kind == "block":
                actions.append({"kind": kind, "turn": int(g[0]), "player": g[1],
                                "blocker": g[2], "attacker": g[3]})
            else:
                actions.append({"kind": kind, "player": g[0],
                                "value": g[1] if g[1] is not None else g[-1]})
    for m in ASSERT_RE.finditer(body):
        assertions.append({"assert": m.group(1), "args": m.group(2).strip()})

    total_calls = len(HARNESS_CALL_RE.findall(body))
    recognized = len(setup) + len(actions) + len(assertions)
    return {
        "source": f"{rel}#{name}", "class": cls, "method": name,
        "setup": setup, "actions": actions, "assertions": assertions,
        "coverage": {"recognized": recognized, "total_calls": total_calls},
    }


def main():
    mage_repo = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("CARDGURU_MAGE_REPO")
    out_path = sys.argv[2] if len(sys.argv) > 2 else "corpus/mage_tests_seed.jsonl"
    root = os.path.join(mage_repo, "Mage.Tests/src/test/java/org/mage/test/cards")

    stats = Counter()
    cards_referenced = set()
    with open(out_path, "w", encoding="utf-8") as out:
        for dirpath, _dirs, files in os.walk(root):
            for fn in sorted(files):
                if not fn.endswith(".java"):
                    continue
                stats["files"] += 1
                path = os.path.join(dirpath, fn)
                rel = os.path.relpath(path, root)
                src = open(path, encoding="utf-8", errors="replace").read()
                cls = fn[:-5]
                for m in TEST_RE.finditer(src):
                    body = method_body(src, m.end() - 1)
                    rec = parse_method(m.group(1), body, rel, cls)
                    stats["methods"] += 1
                    stats["setup_calls"] += len(rec["setup"])
                    stats["actions"] += len(rec["actions"])
                    stats["assertions"] += len(rec["assertions"])
                    cov = rec["coverage"]
                    if cov["total_calls"] and cov["recognized"] >= cov["total_calls"]:
                        stats["fully_parsed_methods"] += 1
                    for s in rec["setup"]:
                        if s["kind"] == "add_card":
                            cards_referenced.add(s["card"])
                    out.write(json.dumps(rec) + "\n")

    stats["distinct_cards_referenced"] = len(cards_referenced)
    summary = dict(stats)
    with open(out_path.replace(".jsonl", "_stats.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
