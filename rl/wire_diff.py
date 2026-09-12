#!/usr/bin/env python3
"""Byte-identity check of two wire recordings (wire_echo_server.py output).

    python3 rl/wire_diff.py A.jsonl B.jsonl [--ignore-keys k1,k2]

Prints IDENTICAL, or the first differing line with the first differing key
(and index inside it) so the cause is named, not just the fact.  Keys listed
in --ignore-keys are dropped from both sides before comparing (e.g. the v7
keys, to check that a v7 line's v6 content equals the v6 line's).
"""
import argparse
import json
import sys


def first_diff(a, b, path=""):
    if type(a) != type(b):
        return f"{path}: type {type(a).__name__} vs {type(b).__name__}"
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                return f"{path}.{k}: only in {'B' if k not in a else 'A'}"
            d = first_diff(a[k], b[k], f"{path}.{k}")
            if d:
                return d
        return None
    if isinstance(a, list):
        if len(a) != len(b):
            return f"{path}: len {len(a)} vs {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            d = first_diff(x, y, f"{path}[{i}]")
            if d:
                return d
        return None
    return None if a == b else f"{path}: {a!r} vs {b!r}"


def all_diffs(a, b, path, out):
    """Every differing leaf path, indices replaced by * for the summary."""
    if type(a) != type(b):
        out.append(path + ": type")
    elif isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(f"{path}.{k}: missing")
            else:
                all_diffs(a[k], b[k], f"{path}.{k}", out)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append(path + ": len")
        for i, (x, y) in enumerate(zip(a, b)):
            all_diffs(x, y, f"{path}[{i}]", out)
    elif a != b:
        out.append(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--ignore-keys", default="")
    ap.add_argument("--all", action="store_true",
                    help="summarise EVERY differing path (row index -> *) with counts")
    args = ap.parse_args()
    ign = set(k for k in args.ignore_keys.split(",") if k)
    la = open(args.a, "rb").read().split(b"\n")
    lb = open(args.b, "rb").read().split(b"\n")
    n = min(len(la), len(lb))
    ndiff = 0
    summary = {}
    colsum = {}
    for i in range(n):
        x, y = la[i], lb[i]
        if x == y:
            continue
        try:
            ja, jb = json.loads(x), json.loads(y)
        except Exception:
            print(f"line {i + 1}: raw bytes differ and not JSON")
            ndiff += 1
            continue
        for k in ign:
            ja.pop(k, None)
            jb.pop(k, None)
        d = first_diff(ja, jb)
        if d is None:
            continue
        ndiff += 1
        if args.all:
            paths = []
            all_diffs(ja, jb, "", paths)
            import re
            for p in paths:
                # row index -> *, column index kept: ".e[*][16]" names the field
                key = re.sub(r"\[\d+\](?=\[)", "[*]", p)
                summary[key] = summary.get(key, 0) + 1
                # is it WHICH row carries the value or HOW MANY rows do? A
                # column whose per-line sum agrees differs only in row
                # identity (e.g. which of several identical lands was tapped)
                mm = re.fullmatch(r"\.(\w+)\[\d+\]\[(\d+)\]", p)
                if mm and mm.group(1) in ja and isinstance(ja[mm.group(1)], list):
                    k, c = mm.group(1), int(mm.group(2))
                    sa = sum(r[c] for r in ja[k])
                    sb_ = sum(r[c] for r in jb[k])
                    tag = f"{key} column-sum {'equal' if abs(sa - sb_) < 1e-9 else 'DIFFERS'}"
                    colsum[tag] = colsum.get(tag, 0) + 1
        elif ndiff <= 3:
            print(f"line {i + 1}: {d}")
    if len(la) != len(lb):
        print(f"line counts differ: {len(la)} vs {len(lb)}")
        ndiff += 1
    for p, c in sorted(summary.items(), key=lambda kv: -kv[1]):
        print(f"  {c:5d} x {p}")
    for p, c in sorted(colsum.items()):
        print(f"  {c:5d} x {p}")
    print("IDENTICAL" if ndiff == 0 else f"DIFFER: {ndiff} lines")
    sys.exit(0 if ndiff == 0 else 1)


if __name__ == "__main__":
    main()
