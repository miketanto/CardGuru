"""Run Dimir mirror games one or two at a time, for human review.

The mirror is the experiment that isolates piloting skill: both seats play
the same 60 cards, so any deviation from a 50% win rate is the pilot, not
the deck. This runner is deliberately small and interactive — it plays N
games (default 1), exports a playback replay for each, writes a review
digest, and prints a summary you can act on before deciding to run again.

Game i starts player A when i is odd and player B when i is even, so a
2-game run is balanced on the play/draw axis. Pass --seed to fix the deal:
with --paired, game i and game i+1 share a seed with the start swapped, so
the two arms see identical opening hands.

Usage:
  python3 benchmark/run_mirror.py --mage-repo ~/Documents/mage --games 2
  python3 benchmark/run_mirror.py --mage-repo ~/Documents/mage --games 2 \
      --seed 4242 --paired
"""
import argparse
import json
import os
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DECK = "dimir_midrange"
BRIEFING = "pilot_dimir_mirror.md"


def next_game_number(results_path):
    n = 0
    if os.path.exists(results_path):
        for line in open(results_path, encoding="utf-8"):
            try:
                n = max(n, json.loads(line).get("game", 0))
            except json.JSONDecodeError:
                pass
    return n + 1


def run_one(args, g, out_dir, results_path):
    """Play one mirror game; return its result row."""
    esc = os.path.join(out_dir, f"esc_g{g}")
    os.makedirs(esc, exist_ok=True)
    for fn in os.listdir(esc):
        os.remove(os.path.join(esc, fn))
    game_log = os.path.join(out_dir, f"g{g}.jsonl")
    daemon_log = os.path.join(out_dir, f"g{g}_daemon.jsonl")
    for p in (game_log, daemon_log):
        if os.path.exists(p):
            os.remove(p)

    start = "A" if g % 2 == 1 else "B"
    seed = None
    if args.seed is not None:
        # --paired: games 1&2 share a seed, 3&4 share the next, ... so each
        # pair sees the same deal from both sides of the play/draw split.
        seed = args.seed + ((g - 1) // 2 if args.paired else (g - 1))

    daemon = subprocess.Popen(
        [sys.executable, os.path.join(HERE, "pilot_daemon.py"),
         "--esc-dir", esc, "--log", daemon_log, "--model", args.model,
         "--system", os.path.join(HERE, BRIEFING), "--start", start],
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    cmd = [sys.executable, os.path.join(HERE, "llm_bridge.py"),
           "--mage-repo", args.mage_repo, "--esc-dir", esc,
           "--log", game_log, "--compact", "--search", args.search,
           "--timeout", str(args.timeout),
           "--deck-a", DECK, "--deck-b", DECK]
    if seed is not None:
        cmd += ["--seed", str(seed)]
    if args.opp_think_secs is not None:
        cmd += ["--opp-think-secs", str(args.opp_think_secs)]

    print(f"\n=== mirror game {g} — pilot on the "
          f"{'play' if start == 'A' else 'draw'}"
          f"{f', seed {seed}' if seed is not None else ''} ===", flush=True)
    t0 = time.time()
    result, err = None, ""
    stop_watch = threading.Event()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)

    def watchdog():
        # Real-time deadline: subprocess timeouts run off a monotonic clock
        # that does not advance while the machine sleeps.
        deadline = time.time() + args.game_timeout
        while not stop_watch.wait(20):
            if time.time() > deadline:
                try:
                    proc.kill()
                except Exception:
                    pass
                return

    threading.Thread(target=watchdog, daemon=True).start()
    try:
        out, errout = proc.communicate()
        if out and out.strip():
            try:
                result = json.loads(out.strip().splitlines()[-1])
            except json.JSONDecodeError:
                err = out[-300:]
        err = err or (errout or "")[-300:]
        if proc.returncode and proc.returncode < 0:
            err = f"killed by watchdog after {args.game_timeout}s"
    finally:
        stop_watch.set()
        daemon.terminate()

    wall = round(time.time() - t0, 1)
    sources = {}
    searches = {"attackers": 0, "blockers": 0, "priority": 0}
    if os.path.exists(game_log):
        for line in open(game_log, encoding="utf-8"):
            row = json.loads(line)
            s = row.get("source")
            if s:
                sources[s] = sources.get(s, 0) + 1
            req = row.get("request") or {}
            if req.get("kind") == "leaf_eval":
                d = req.get("decision")
                if d in searches:
                    searches[d] += 1

    row = {"game": g, "start": start, "seed": seed, "search": args.search,
           "result": result, "wall_s": wall, "sources": sources,
           "searches": searches, "ts": round(time.time(), 1)}
    if result is None or result.get("status") != "completed":
        row["error"] = err[-300:]
    with open(results_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")

    winner = (result or {}).get("winner")
    verdict = ("WIN" if winner == "A" else "loss" if winner == "B"
               else f"ERROR: {err[:120]}")
    print(f"game {g}: {verdict} in {wall / 60:.1f} min "
          f"({(result or {}).get('turns', '?')} turns)", flush=True)
    print(f"  decisions: {sources} | searches: {searches}", flush=True)

    if result and result.get("status") == "completed":
        subprocess.run(
            [sys.executable, os.path.join(HERE, "replay_export.py"),
             "--log", game_log,
             "--out", os.path.join(out_dir, f"g{g}.html"),
             "--title", f"Dimir Mirror g{g}",
             "--subtitle", f"Dimir midrange mirror, pilot on the "
                           f"{'play' if start == 'A' else 'draw'}"
                           f"{f', seed {seed}' if seed is not None else ''}. "
                           f"Winner: {'pilot' if winner == 'A' else 'MAD'}.",
             "--player-a", "Haiku — Dimir (A)",
             "--player-b", "MAD — Dimir (B)"],
            capture_output=True)
        subprocess.run(
            [sys.executable, os.path.join(HERE, "review_game.py"), game_log,
             "--out", os.path.join(out_dir, f"g{g}_review.md")],
            capture_output=True)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mage-repo", required=True)
    ap.add_argument("--out-dir", default="research/data/mirror")
    ap.add_argument("--games", type=int, default=1)
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--search", choices=["none", "attacks", "llm"],
                    default="llm")
    ap.add_argument("--timeout", type=float, default=240.0)
    ap.add_argument("--game-timeout", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=None,
                    help="fix the deal; game N uses seed+N (or seed+pair "
                         "index with --paired)")
    ap.add_argument("--paired", action="store_true",
                    help="consecutive games share a seed with the start "
                         "swapped, so a pair sees the same deal both ways")
    ap.add_argument("--opp-think-secs", type=int, default=None)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    results_path = os.path.join(args.out_dir, "mirror.jsonl")
    first = next_game_number(results_path)

    rows = [run_one(args, g, args.out_dir, results_path)
            for g in range(first, first + args.games)]

    print("\n=== session ===")
    for r in rows:
        w = (r.get("result") or {}).get("winner")
        print(f"  g{r['game']} ({'play' if r['start'] == 'A' else 'draw'}): "
              f"{'WIN' if w == 'A' else 'loss' if w == 'B' else 'error'}"
              f"  {r['wall_s'] / 60:.0f} min")
    # Standing record across every game recorded in this directory.
    wins = losses = 0
    for line in open(results_path, encoding="utf-8"):
        w = (json.loads(line).get("result") or {}).get("winner")
        wins += w == "A"
        losses += w == "B"
    n = wins + losses
    print(f"\nstanding mirror record: {wins}W-{losses}L"
          + (f" ({100 * wins / n:.0f}%)" if n else "")
          + "   [50% is the null — same deck both sides]")
    print(f"replays + reviews in {args.out_dir}/")


if __name__ == "__main__":
    main()
