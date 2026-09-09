"""Campaign health + results matrix.

Reads campaign.jsonl and every per-game log in the same directory and
reports: the win matrix by cell, and the failure classes worth fixing
(errors, fallback-timeouts, heuristic-fallback leaf evals, daemon schema
misses, and rules-slippage phrases in the pilot's own reasoning).

Usage: python3 benchmark/analyze_campaign.py research/data/campaign
"""
import json
import os
import sys
from collections import defaultdict

# Phrases in a pilot "why" that usually mean it invented a rule.
# Only the beliefs that are actually WRONG: a creature that cannot block
# for a reason other than being tapped, or a forced block. "Summoning sick
# so it can't ATTACK" is correct and must not be flagged.
SLIPPAGE = [
    "sick, can't block", "sick and can't block", "sick so it can't block",
    "summoning sick — cannot block", "summoning sick, cannot block",
    "unable to block", "forced to block", "must block", "has to block",
    "forced to declare as blocker", "forced to declare a blocker",
    "cannot block because it is summoning", "no blockers available",
]
OK_WITH = []


def load(path):
    rows = []
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "research/data/campaign"
    camp = load(os.path.join(out_dir, "campaign.jsonl"))
    if not camp:
        print("no campaign.jsonl rows yet")
        return

    print("=== RESULTS MATRIX ===")
    cells = defaultdict(lambda: {"W": 0, "L": 0, "E": 0, "wall": 0.0,
                                 "play": [0, 0], "draw": [0, 0]})
    for r in camp:
        c = cells[r["cell"]]
        res = r.get("result") or {}
        c["wall"] += r.get("wall_s", 0)
        if res.get("status") != "completed":
            c["E"] += 1
            continue
        won = res.get("winner") == "A"
        c["W" if won else "L"] += 1
        side = "play" if r.get("start") == "A" else "draw"
        c[side][0 if won else 1] += 1
    for name, c in cells.items():
        n = c["W"] + c["L"]
        played = n + c["E"]
        rate = f"{100 * c['W'] / n:.0f}%" if n else "-"
        print(f"{name:26s} {c['W']}W-{c['L']}L ({rate})"
              f"  errors={c['E']}  play={c['play'][0]}-{c['play'][1]}"
              f" draw={c['draw'][0]}-{c['draw'][1]}"
              f"  avg={c['wall'] / max(1, played) / 60:.0f}min")

    print("\n=== FAILURES ===")
    for r in camp:
        if (r.get("result") or {}).get("status") != "completed":
            print(f"ERROR {r['cell']} g{r['game']}: "
                  f"{str(r.get('error'))[:200]}")

    totals = defaultdict(int)
    slips = []
    for r in camp:
        log = os.path.join(out_dir, f"{r['cell']}_g{r['game']}.jsonl")
        for row in load(log):
            src = row.get("source")
            req = row.get("request") or {}
            if src == "fallback-timeout":
                totals["fallback_timeout"] += 1
            if req.get("kind") == "leaf_eval":
                totals["leaf_eval"] += 1
                if src != "llm":
                    totals["leaf_eval_heuristic_fallback"] += 1
            why = str((row.get("response") or {}).get("why", "")).lower()
            blocky = "block" in why
            if blocky and (any(p in why for p in SLIPPAGE) or (
                    "sick" in why and "can't block" in why) or (
                    "sick" in why and "cannot block" in why)):
                slips.append((r["cell"], r["game"], req.get("turn"),
                              req.get("kind"), why[:120]))
        dlog = os.path.join(out_dir, f"{r['cell']}_g{r['game']}_daemon.jsonl")
        for row in load(dlog):
            if row.get("error"):
                totals["daemon_error"] += 1
            if row.get("attempt", 1) > 1:
                totals["schema_retry"] += 1
            if row.get("session_reset"):
                totals["session_reset_recovery"] += 1
            raw = str(row.get("raw", "")).lower()
            if "exiting this game" in raw or "not providing json" in raw \
                    or "stopping this conversation" in raw:
                totals["pilot_refusal"] += 1

    for k, v in sorted(totals.items()):
        print(f"{k}: {v}")
    print(f"rules_slippage: {len(slips)}")
    for s in slips[:8]:
        print(f"  {s[0]} g{s[1]} T{s[2]} [{s[3]}] {s[4]}")


if __name__ == "__main__":
    main()
