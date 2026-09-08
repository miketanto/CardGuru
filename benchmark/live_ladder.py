"""Phase 1 live-match ladder: no-LLM policies vs the MAD AI.

Plays GAMES real games per (policy, opponent-deck) cell against XMage's
ComputerPlayer7, our seat always on mono_red_aggro. Policies are the
scaffold-only ladder: dumb (fixed heuristics), belief (plays around
believed removal), belief+minimax (sim-backed attack search in the JVM).
No language model makes any decision — this is the control condition the
LLM policy must beat.

One JVM per game (fresh MatchClient). Results append to a JSONL as each
game ends, so an interrupted run resumes: completed (deck_b, policy, game)
rows are skipped on restart. Run two workers on separate mage checkouts to
parallelize pairings (one checkout per concurrent engine user — the driver
copy clobbers otherwise).

  python3 benchmark/live_ladder.py --deck-b mono_red_aggro \
      --mage-repo ~/Documents/mage --out research/data/live_ladder_mirror.jsonl
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru.play import MatchClient, belief_policy, dumb_policy  # noqa: E402

POLICIES = ["dumb", "belief", "belief_minimax"]


def make_policy(name):
    if name == "dumb":
        return dumb_policy, False
    if name == "belief":
        return belief_policy(), False
    if name == "belief_minimax":
        return belief_policy(), True
    raise ValueError(name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck-b", required=True)
    ap.add_argument("--deck-a", default="mono_red_aggro")
    ap.add_argument("--games", type=int, default=20)
    ap.add_argument("--policies", default=",".join(POLICIES))
    ap.add_argument("--mage-repo", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    done = set()
    if os.path.exists(args.out):
        with open(args.out, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                done.add((r["deck_b"], r["policy"], r["game"]))

    for policy_name in args.policies.split(","):
        for i in range(args.games):
            key = (args.deck_b, policy_name, i)
            if key in done:
                continue
            policy, minimax = make_policy(policy_name)
            t0 = time.time()
            row = {"deck_a": args.deck_a, "deck_b": args.deck_b,
                   "policy": policy_name, "game": i}
            try:
                with MatchClient(args.mage_repo, minimax=minimax,
                                 deck_a=args.deck_a,
                                 deck_b=args.deck_b) as m:
                    result = m.play(policy)
                    if minimax:
                        trace = m.read_trace()
                        result = dict(result)
                        result["minimax_decisions"] = len(trace)
                row.update(result)
            except Exception as e:
                row.update({"status": "harness_error", "error": str(e)[:300]})
            row["seconds"] = round(time.time() - t0, 1)
            with open(args.out, "a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")
            print(f"{policy_name} vs {args.deck_b} game {i}: "
                  f"{row.get('winner', row['status'])} "
                  f"({row['seconds']}s)", flush=True)


if __name__ == "__main__":
    main()
