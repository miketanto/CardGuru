#!/usr/bin/env python3
"""v6-identity check for the rl.manaCands filter (7a amendment, RLPlayer.priority).
    python3 rl/manacands_check.py ON.jsonl ON2.jsonl OFF.jsonl [OFF.probe.txt]
ON, ON2 = two recordings with -Drl.manaCands=true (the old candidate set),
OFF = the default (mana abilities filtered); same deck / seed / episodes, echo
policy PREFER=1 (play the first land drop, else PASS) so all three games follow
the same trajectory and no mana ability is ever chosen. Two runs of the same
build already differ by the 5e replay residual (which of several identical
lands the engine taps to pay; which identical object a candidate refers to),
so the control is ON vs ON2 and the claim is:
  1. every OFF consult aligns, in order, with an ON consult (candidate rows
     keyed by (v7 type, v6 row); OFF's list is a subsequence of ON's); an ON
     consult without an OFF partner offered only mana abilities besides PASS;
  2. every removed candidate is v7 type ACTIVATE whose referents are land
     entities, and (with the probe) their number equals manaCandsDropped;
  3. the per-key / per-column census of all other differences in ON vs OFF is
     a subset of the ON vs ON2 census (the residual) plus the fields defined by
     the candidate list / consult count (game token idx 12-21, opp-action consult
     age), and ON vs ON2 drops no consult and no candidate.
Exit 1 on any failure.
"""
import json
import re
import sys
from collections import Counter, defaultdict

C_ACTIVATE, ENT_LAND, TOK_ENT0 = 3, 30, 3
CAND_KEYS = ("c", "v7_cand_type", "v7_cand", "v7_cand_refers")
KEY_ROW = ("v7_cand_type", "c")   # alignment key per candidate


def consults(path):
    return [m for m in (json.loads(l) for l in open(path)) if m.get("t") == "consult"]


def cand_keys(m):
    keys = [k for k in KEY_ROW if k in m]
    return [tuple(json.dumps(m[k][i]) for k in keys) for i in range(len(m["c"]))]


def is_mana(m, i):
    if m["v7_cand_type"][i] != C_ACTIVATE:
        return False
    refs = m["v7_cand_refers"][i]
    return bool(refs) and all(m["v7_ent"][r - TOK_ENT0][ENT_LAND] == 1 for r in refs)


def subseq(on, off):
    idx, j = [], 0
    for r in off:
        while j < len(on) and on[j] != r:
            j += 1
        if j == len(on):
            return None
        idx.append(j)
        j += 1
    return idx


def census(a, b, idx, cen):
    """add every differing (key, column) outside the removed candidates to cen."""
    for k in sorted(set(a) | set(b)):
        va, vb = a.get(k), b.get(k)
        if k in CAND_KEYS:
            va = [va[i] for i in idx]          # ON rows kept by OFF, in order
        if va == vb:
            continue
        if isinstance(va, list) and va and isinstance(va[0], list):
            if len(va) != len(vb):
                cen[k]["len"] += 1
            for r in range(min(len(va), len(vb))):
                for c in range(max(len(va[r]), len(vb[r]))):
                    if (va[r][c] if c < len(va[r]) else None) != (vb[r][c] if c < len(vb[r]) else None):
                        cen[k][c] += 1
        elif isinstance(va, list):
            for c in range(max(len(va), len(vb))):
                if (va[c] if c < len(va) else None) != (vb[c] if c < len(vb) else None):
                    cen[k][c] += 1
        elif isinstance(va, dict):
            for x in set(va) | set(vb):
                if va.get(x) != vb.get(x):
                    cen[k][x] += 1
        else:
            cen[k]["scalar"] += 1


def compare(on, off, tag):
    fails, i, j = [], 0, 0
    pairs = vanished = removed = removed_mana = 0
    cen = defaultdict(Counter)
    while i < len(on):
        a = on[i]
        rows = cand_keys(a)
        idx = subseq(rows, cand_keys(off[j])) if j < len(off) else None
        if idx is None:
            kinds = [is_mana(a, k) for k in range(1, len(rows))]
            if kinds and all(kinds):
                vanished += 1
                removed += len(kinds)
                removed_mana += len(kinds)
            else:
                fails.append(f"{tag} ON#{i}: no OFF partner; types {a['v7_cand_type']}")
            i += 1
            continue
        pairs += 1
        for k in range(len(rows)):
            if k in idx:
                continue
            removed += 1
            if is_mana(a, k):
                removed_mana += 1
            else:
                fails.append(f"{tag} ON#{i}/OFF#{j}: removed candidate {k} is not a land mana ability (type {a['v7_cand_type'][k]})")
        census(a, off[j], idx, cen)
        i += 1
        j += 1
    if j != len(off):
        fails.append(f"{tag}: OFF has {len(off) - j} consults with no ON partner")
    print(f"MC|{tag}|on={len(on)}|off={len(off)}|pairs={pairs}|vanished={vanished}"
          f"|removed={removed}|removed_mana={removed_mana}")
    for k in sorted(cen):
        print(f"MC|{tag}|census|{k}|" + " ".join(f"{c}:{n}" for c, n in sorted(cen[k].items(), key=str)))
    return fails, cen, removed, vanished


def probe_dropped(path):
    n = [int(x) for x in re.findall(r"manaCandsDropped[=: ]+(\d+)", open(path, errors="replace").read())]
    return sum(n) if n else None


def main():
    on, on2, off = consults(sys.argv[1]), consults(sys.argv[2]), consults(sys.argv[3])
    f_ctl, cen_ctl, rem_ctl, van_ctl = compare(on, on2, "control")
    f_off, cen_off, rem_off, van_off = compare(on, off, "filter")
    fails = f_ctl + f_off
    if rem_ctl or van_ctl:
        fails.append(f"control removed {rem_ctl} candidates / {van_ctl} consults; expected 0")
    # fields defined by the candidate list or the consult count (WIRE 2b idx
    # 12-19 decision type, 20 K, 21 consults so far; opp action idx 7 = consult
    # age): they move with the filter by construction and are reported, not failed
    DERIVED = {('v7_game', c) for c in range(12, 22)} | {('v7_opp_actions', 7)}
    extra = {(k, c) for k in cen_off for c in cen_off[k]} - {(k, c) for k in cen_ctl for c in cen_ctl[k]}
    print('MC|derived_only|' + ' '.join(f'{k}:{c}' for k, c in sorted(extra & DERIVED, key=str)))
    extra -= DERIVED
    if extra:
        fails.append(f"filter diff census outside the control residual: {sorted(extra, key=str)[:12]}")
    if len(sys.argv) >= 5:
        d = probe_dropped(sys.argv[4])
        print(f"MC|probe|manaCandsDropped={d}|removed={rem_off}")
        if d is not None and d != rem_off:
            fails.append(f"OFF probe manaCandsDropped={d} != removed candidates {rem_off}")
    for f in fails[:20]:
        print("FAIL", f)
    print(f"MC|{'PASS' if not fails else 'FAIL'}|fails={len(fails)}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
