#!/usr/bin/env python3
"""Behaviour counters over a v7 wire recording (wire_echo_server.py output).

    python3 rl/wire_census.py FILE [FILE ...]

Per file: consults, hello widths, candidate-type histogram, decision-type
histogram (game token idx 12..19), entities per consult, edges per consult
by type, referent coverage (non-PASS candidates whose refers hit an entity
token vs fell back to the player token), and the v7_ctr sums.  This is
the 3a/3c evidence: counts, not a win rate.
"""
import json
import sys
from collections import Counter

CT = ["PASS", "LAND", "SPELL", "ACTIVATE", "TARGET", "ATTACK", "BLOCK", "OTHER"]


def census(path):
    n = 0
    ctype = Counter()
    dtype = Counter()
    etype = Counter()
    ents, edges, ks = [], [], []
    ok_refs = fallback = meta_missing = trunc = 0
    ref_to_player = 0
    hello = None
    for raw in open(path, "rb"):
        if not raw.strip():
            continue
        m = json.loads(raw)
        if m.get("t") == "hello":
            hello = m
            continue
        if m.get("t") != "consult":
            continue
        n += 1
        ents.append(len(m["v7_ent"]))
        edges.append(len(m["v7_edges"]))
        ks.append(len(m["v7_cand"]))
        for e in m["v7_edges"]:
            etype[e[2]] += 1
        g = m["v7_game"]
        dtype[CT[max(range(8), key=lambda i: g[12 + i])]] += 1
        ctr = m["v7_ctr"]
        fallback += ctr.get("refersFallback", 0)
        meta_missing += ctr.get("metaMissing", 0)
        trunc += ctr.get("entityTrunc", 0)
        for t, refs in zip(m["v7_cand_type"], m["v7_cand_refers"]):
            ctype[CT[t]] += 1
            if t != 0:
                if any(r >= 3 for r in refs):
                    ok_refs += 1
                elif refs:
                    ref_to_player += 1
    nonpass = sum(v for k, v in ctype.items() if k != "PASS")
    print(f"== {path}")
    if hello:
        print(f"hello: wire={hello.get('wire')} card_emb={hello.get('card_emb')} "
              f"dims={hello.get('v7_dims')} emax={hello.get('v7_emax')}")
    print(f"consults={n}  ent/consult mean={sum(ents) / max(n, 1):.1f} max={max(ents or [0])}  "
          f"edges/consult mean={sum(edges) / max(n, 1):.1f}  k mean={sum(ks) / max(n, 1):.1f} max={max(ks or [0])}")
    print("cand types:", dict(ctype))
    print("decision types:", dict(dtype))
    print("edge types:", dict(sorted(etype.items())))
    print(f"non-PASS candidates={nonpass}: refers->entity {ok_refs}, refers->player-only {ref_to_player}, "
          f"fallback(counter)={fallback}, metaMissing={meta_missing}, entityTrunc={trunc}")
    if nonpass:
        print(f"refers coverage (entity or player referent, non-PASS) = {(ok_refs + ref_to_player - fallback) / nonpass:.4f}")


def names_check(paths, index_path):
    """Every v7_ent_name resolved through cards_v1 (WIRE rule 4): the
    server's unresolvedName counter, computed offline."""
    idx = json.load(open(index_path))
    names = idx["names"] if "names" in idx else idx
    seen, bad = Counter(), Counter()
    for path in paths:
        for raw in open(path, "rb"):
            if not raw.startswith(b'{"t":"consult"'):
                continue
            m = json.loads(raw)
            for nm, tok in zip(m["v7_ent_name"], m["v7_ent_token"]):
                seen[nm] += 1
                key = nm.lower()
                if tok:
                    key = "token:" + key
                if key not in names and nm.lower() not in names and nm != "?":
                    bad[nm] += 1
    print(f"names: {len(seen)} distinct over {sum(seen.values())} entity rows; "
          f"unresolved {len(bad)} distinct / {sum(bad.values())} rows: {dict(bad.most_common(10))}")


if __name__ == "__main__":
    files = [a for a in sys.argv[1:] if not a.startswith("--index=")]
    index = [a[8:] for a in sys.argv[1:] if a.startswith("--index=")]
    for p in files:
        census(p)
    if index:
        names_check(files, index[0])
