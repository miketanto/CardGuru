"""Run a batch of haiku-pilot games vs MAD, alternating play/draw.

Per game: fresh spool dir, a pilot_daemon (its own persistent claude -p
session), and an llm_bridge game. Results append to <out-dir>/results.jsonl
(resumable: already-recorded games are skipped), decision logs land in
<out-dir>/game<N>.jsonl, and a playback HTML is exported per game.

Usage:
  python3 benchmark/run_pilot_batch.py --mage-repo ~/Documents/mage \
      --out-dir research/data/pilot_batch --games 10
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def done_games(results_path):
    games = set()
    if os.path.exists(results_path):
        for line in open(results_path, encoding="utf-8"):
            games.add(json.loads(line)["game"])
    return games


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mage-repo", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--games", type=int, default=10)
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--timeout", type=float, default=240.0)
    ap.add_argument("--search", choices=["none", "attacks", "llm"],
                    default="none", help="combat search mode (see llm_bridge)")
    ap.add_argument("--deck-b", default="mono_green_stompy")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    results_path = os.path.join(args.out_dir, "results.jsonl")
    already = done_games(results_path)

    for g in range(1, args.games + 1):
        if g in already:
            print(f"game {g}: already recorded, skipping", flush=True)
            continue
        esc = os.path.join(args.out_dir, f"esc{g}")
        os.makedirs(esc, exist_ok=True)
        for fn in os.listdir(esc):
            os.remove(os.path.join(esc, fn))
        game_log = os.path.join(args.out_dir, f"game{g}.jsonl")
        daemon_log = os.path.join(args.out_dir, f"daemon{g}.jsonl")
        for p in (game_log, daemon_log):
            if os.path.exists(p):
                os.remove(p)
        start = "A" if g % 2 == 1 else "B"  # odd games on the play

        daemon = subprocess.Popen(
            [sys.executable, os.path.join(HERE, "pilot_daemon.py"),
             "--esc-dir", esc, "--log", daemon_log,
             "--model", args.model, "--start", start],
            stdout=open(os.path.join(args.out_dir, f"daemon{g}.out"), "w"),
            stderr=subprocess.STDOUT)
        t0 = time.time()
        try:
            bridge = subprocess.run(
                [sys.executable, os.path.join(HERE, "llm_bridge.py"),
                 "--mage-repo", args.mage_repo, "--esc-dir", esc,
                 "--log", game_log, "--compact",
                 "--timeout", str(args.timeout),
                 "--search", args.search, "--deck-b", args.deck_b],
                capture_output=True, text=True, timeout=3600)
        finally:
            daemon.terminate()
        wall = round(time.time() - t0, 1)

        result = None
        if bridge.returncode == 0 and bridge.stdout.strip():
            try:
                result = json.loads(bridge.stdout.strip().splitlines()[-1])
            except json.JSONDecodeError:
                pass
        sources = {}
        if os.path.exists(game_log):
            for line in open(game_log, encoding="utf-8"):
                s = json.loads(line).get("source")
                if s:
                    sources[s] = sources.get(s, 0) + 1
        row = {"game": g, "start": start, "result": result, "wall_s": wall,
               "sources": sources, "ts": round(time.time(), 1)}
        if result is None:
            row["bridge_stderr"] = bridge.stderr[-400:]
        with open(results_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        winner = (result or {}).get("winner", "?")
        print(f"game {g}: winner={winner} start={start} wall={wall}s "
              f"sources={sources}", flush=True)

        if result is not None:
            subprocess.run(
                [sys.executable, os.path.join(HERE, "replay_export.py"),
                 "--log", game_log,
                 "--out", os.path.join(args.out_dir, f"game{g}_replay.html"),
                 "--title", f"Pilot Batch — Game {g}",
                 "--subtitle",
                 f"Haiku daemon pilot vs MAD, {'on the play' if start == 'A' else 'on the draw'}. "
                 f"Winner: {winner}, {wall}s wall clock.",
                 "--player-a", "Haiku — Mono-Red (A)",
                 "--player-b", "MAD — Stompy (B)"],
                capture_output=True)

    wins = losses = 0
    for line in open(results_path, encoding="utf-8"):
        w = (json.loads(line).get("result") or {}).get("winner")
        wins += w == "A"
        losses += w == "B"
    print(f"BATCH DONE: {wins}W-{losses}L of {args.games}", flush=True)


if __name__ == "__main__":
    main()
