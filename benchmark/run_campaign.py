"""Overnight campaign: run many matchups sequentially, one JVM at a time.

Each cell is (pilot deck, opponent deck, pilot briefing, search mode) played
N games with alternating play/draw. Results append to campaign.jsonl and are
resumable — a completed (cell, game) is skipped on restart, so the runner
can be killed and relaunched freely.

Usage:
  python3 benchmark/run_campaign.py --mage-repo ~/Documents/mage \
      --out-dir research/data/campaign --games 5
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))

# (cell id, deck_a, deck_b, briefing, search)
CELLS = [
    ("red_vs_stompy_search", "mono_red_aggro", "mono_green_stompy",
     "pilot_system.md", "llm"),
    ("dimir_vs_stompy", "dimir_midrange", "mono_green_stompy",
     "pilot_dimir.md", "llm"),
    ("red_vs_dimir", "mono_red_aggro", "dimir_midrange",
     "pilot_vs_dimir.md", "llm"),
    ("prowess_vs_dimir", "mono_red_prowess", "dimir_midrange",
     "pilot_vs_dimir.md", "llm"),
    ("dimir_vs_prowess", "dimir_midrange", "mono_red_prowess",
     "pilot_dimir.md", "llm"),
    ("white_vs_stompy", "mono_white_control", "mono_green_stompy",
     "pilot_white.md", "llm"),
]


def done_cells(path):
    done = set()
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            try:
                r = json.loads(line)
                done.add((r["cell"], r["game"]))
            except (json.JSONDecodeError, KeyError):
                pass
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mage-repo", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--games", type=int, default=5)
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--timeout", type=float, default=240.0)
    ap.add_argument("--game-timeout", type=int, default=2400)
    ap.add_argument("--claude-bin", default="claude",
                    help="pilot binary; point at a stub for baseline runs")
    ap.add_argument("--only", default="",
                    help="comma-separated cell ids to run (default: all)")
    ap.add_argument("--tag", default="",
                    help="suffix appended to cell ids in results/logs, so a "
                         "baseline run does not collide with the LLM run")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    results = os.path.join(args.out_dir, "campaign.jsonl")
    done = done_cells(results)

    only = {x for x in args.only.split(",") if x}
    for cell, deck_a, deck_b, briefing, search in CELLS:
        if only and cell not in only:
            continue
        cell = cell + args.tag
        brief_path = os.path.join(HERE, briefing)
        if not os.path.exists(brief_path):
            print(f"{cell}: briefing {briefing} missing, skipping cell",
                  flush=True)
            continue
        for g in range(1, args.games + 1):
            if (cell, g) in done:
                print(f"{cell} g{g}: recorded, skip", flush=True)
                continue
            esc = os.path.join(args.out_dir, f"esc_{cell}_{g}")
            os.makedirs(esc, exist_ok=True)
            for fn in os.listdir(esc):
                os.remove(os.path.join(esc, fn))
            game_log = os.path.join(args.out_dir, f"{cell}_g{g}.jsonl")
            daemon_log = os.path.join(args.out_dir, f"{cell}_g{g}_daemon.jsonl")
            for p in (game_log, daemon_log):
                if os.path.exists(p):
                    os.remove(p)
            start = "A" if g % 2 == 1 else "B"

            daemon = subprocess.Popen(
                [sys.executable, os.path.join(HERE, "pilot_daemon.py"),
                 "--esc-dir", esc, "--log", daemon_log, "--model", args.model,
                 "--system", brief_path, "--start", start,
                 "--claude-bin", args.claude_bin],
                stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            t0 = time.time()
            result, err = None, ""
            try:
                bridge = subprocess.run(
                    [sys.executable, os.path.join(HERE, "llm_bridge.py"),
                     "--mage-repo", args.mage_repo, "--esc-dir", esc,
                     "--log", game_log, "--compact",
                     "--timeout", str(args.timeout), "--search", search,
                     "--deck-a", deck_a, "--deck-b", deck_b],
                    capture_output=True, text=True, timeout=args.game_timeout)
                if bridge.stdout.strip():
                    try:
                        result = json.loads(bridge.stdout.strip().splitlines()[-1])
                    except json.JSONDecodeError:
                        err = bridge.stdout[-300:]
                err = err or bridge.stderr[-300:]
            except subprocess.TimeoutExpired:
                err = f"game exceeded {args.game_timeout}s"
            finally:
                daemon.terminate()
            wall = round(time.time() - t0, 1)

            sources = {}
            if os.path.exists(game_log):
                for line in open(game_log, encoding="utf-8"):
                    s = json.loads(line).get("source")
                    if s:
                        sources[s] = sources.get(s, 0) + 1
            row = {"cell": cell, "game": g, "deck_a": deck_a,
                   "deck_b": deck_b, "search": search, "start": start,
                   "result": result, "wall_s": wall, "sources": sources,
                   "ts": round(time.time(), 1)}
            if result is None or result.get("status") != "completed":
                row["error"] = err[-300:]
            with open(results, "a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")
            status = (result or {}).get("winner") or (result or {}).get("status") \
                or "ERROR"
            print(f"{cell} g{g}: {status} start={start} {wall}s {sources}",
                  flush=True)

            if result and result.get("status") == "completed":
                subprocess.run(
                    [sys.executable, os.path.join(HERE, "replay_export.py"),
                     "--log", game_log,
                     "--out", os.path.join(args.out_dir, f"{cell}_g{g}.html"),
                     "--title", f"{cell} g{g}",
                     "--subtitle", f"{deck_a} (pilot) vs {deck_b} (MAD), "
                                   f"search={search}, "
                                   f"{'on the play' if start == 'A' else 'on the draw'}. "
                                   f"Winner: {result.get('winner')}.",
                     "--player-a", f"Haiku — {deck_a} (A)",
                     "--player-b", f"MAD — {deck_b} (B)"],
                    capture_output=True)
    print("CAMPAIGN PASS COMPLETE", flush=True)


if __name__ == "__main__":
    main()
