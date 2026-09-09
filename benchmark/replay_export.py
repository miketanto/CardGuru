"""Export a bridge decision log to a self-contained auto-playing replay page.

mage-bench renders replays from per-decision state snapshots plus the action
log; our JSONL rows carry a full snapshot per decision, which is enough for
a video-like playback: every frame is a board state, frames advance on a
timer with per-source durations (auto-passes flick by, pilot decisions
linger), and the viewer has play/pause, speed, a scrubber, and a step list.

Usage:
  python3 benchmark/replay_export.py --log research/data/game.jsonl \
      --out replay.html --title "Game title" [--subtitle "..."]
"""
import argparse
import json
import os

TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "replay_template.html")


def classify(row):
    src = row.get("source")
    if src == "fallback-timeout":
        return "fallback"
    if src in ("auto", "yield"):
        return "auto"
    why = json.dumps(row.get("response") or {})
    if "uto-pass" in why:
        return "auto"
    return "pilot"


def build_frames(log_path):
    frames, result = [], None
    for line in open(log_path, encoding="utf-8"):
        row = json.loads(line)
        if row.get("source") == "result":
            result = row.get("result")
            continue
        req = row.get("request") or {}
        state = req.get("state")
        if not state:
            continue
        frames.append({
            "src": classify(row),
            "turn": req.get("turn"), "phase": req.get("phase"),
            "kind": req.get("kind"), "active": req.get("active"),
            "state": state,
            "response": row.get("response"),
            "why": (row.get("response") or {}).get("why", ""),
            "options": [
                {"index": o.get("index"), "text": o.get("text") or o.get("name")}
                for o in (req.get("options") or [])],
        })
    return frames, result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--player-a", default="Pilot — Mono-Red (A)")
    ap.add_argument("--player-b", default="MAD — Stompy (B)")
    args = ap.parse_args()

    frames, result = build_frames(args.log)
    meta = {"title": args.title, "subtitle": args.subtitle,
            "playerA": args.player_a, "playerB": args.player_b,
            "result": result,
            "counts": {k: sum(1 for f in frames if f["src"] == k)
                       for k in ("pilot", "auto", "fallback")}}
    html = open(TEMPLATE, encoding="utf-8").read()
    html = html.replace("/*__META__*/{}", json.dumps(meta))
    html = html.replace("/*__FRAMES__*/[]", json.dumps(frames))
    html = html.replace("__TITLE__", args.title)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"{args.out}: {len(frames)} frames, "
          f"{os.path.getsize(args.out) // 1024} KB")


if __name__ == "__main__":
    main()
