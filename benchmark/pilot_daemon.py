"""Headless persistent pilot: answers llm_bridge escalations via `claude -p`.

The mage-bench pilot is an async loop over MCP tools; ours is the same loop
over the file spool. One `claude -p` session per game (created on the first
decision, resumed by session id for every later one) keeps the pilot's
context accumulating exactly like a persistent subagent — card_reference
dedup, prior turns, its own stated plans — with zero API spend (the CLI uses
the local Claude Code login).

Loop: wait for the next unanswered req-<n>.json -> render a prompt -> call
`claude -p [--resume <sid>]` -> parse the JSON decision -> write
resp-<n>.json atomically. Exits when the bridge writes DONE. A reply the
daemon cannot parse is retried once with a schema reminder; after that the
request is left for the bridge's own timeout fallback (logged here).

Usage:
  python3 benchmark/pilot_daemon.py --esc-dir /tmp/esc --log daemon.jsonl \
      [--system benchmark/pilot_system.md] [--model haiku]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

SCHEMAS = {
    "mulligan": '{"mulligan": true|false, "why": "..."}',
    "priority": '{"choice": <option index>, "why": "..."}',
    "attackers": '{"attackers": [<indices>], "why": "..."}',
    "blockers": '{"blocks": [[blockerIdx, attackerIdx], ...], "why": "..."}',
    "target": '{"targets": [<indices>], "why": "..."}',
    "choose": '{"targets": [<index>], "why": "..."}',
    "announce_x": '{"x": <int>}',
    "mode": '{"choice": <index>}',
    "use": '{"use": true|false}',
    "leaf_eval": '{"scores": [<0-100 for each leaf, in leaf_index order>], '
                 '"why": "..."}',
}
KEY_FOR = {"mulligan": "mulligan", "priority": "choice",
           "attackers": "attackers", "blockers": "blocks",
           "target": "targets", "choose": "targets",
           "announce_x": "x", "mode": "choice", "use": "use",
           "leaf_eval": "scores"}


def extract_json(text):
    """First balanced {...} object in text, parsed."""
    start = text.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break
        start = text.find("{", start + 1)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--esc-dir", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--system", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "pilot_system.md"))
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--claude-bin", default="claude")
    ap.add_argument("--call-timeout", type=float, default=180.0)
    ap.add_argument("--start", choices=["A", "B", "pilot"], default="pilot",
                    help="answer the 'Select a starting player' choice "
                         "deterministically (for alternating play/draw in "
                         "batches) instead of asking the pilot")
    args = ap.parse_args()

    session_id = None
    answered = set()

    def log(row):
        row["ts"] = round(time.time(), 1)
        with open(args.log, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")

    def call_pilot(prompt):
        nonlocal session_id
        cmd = [args.claude_bin, "-p", "--output-format", "json",
               "--model", args.model]
        if session_id:
            cmd += ["--resume", session_id]
        else:
            cmd += ["--append-system-prompt-file", args.system]
        out = subprocess.run(cmd, input=prompt, capture_output=True,
                             text=True, timeout=args.call_timeout)
        if out.returncode != 0:
            raise RuntimeError(f"claude -p failed: {out.stderr[-500:]}")
        body = json.loads(out.stdout)
        session_id = body.get("session_id") or session_id
        return body.get("result", "")

    def answer(n, req_path):
        with open(req_path, encoding="utf-8") as f:
            payload = json.load(f)
        request = payload.get("request") or {}
        kind = request.get("kind", "priority")
        if (args.start != "pilot" and kind == "choose"
                and "starting player" in (request.get("prompt") or "")):
            idx = next((o.get("index") for o in request.get("options", [])
                        if o.get("owner") == args.start), 0)
            resp = {"targets": [idx], "why": f"batch: player {args.start} starts"}
            tmp = os.path.join(args.esc_dir, f"resp-{n}.json.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(resp, f)
            os.rename(tmp, os.path.join(args.esc_dir, f"resp-{n}.json"))
            log({"seq": n, "kind": kind, "response": resp, "source": "batch"})
            return
        schema = SCHEMAS.get(kind, SCHEMAS["priority"])
        prompt = (f"Decision {n}. Reply with ONLY the JSON response object, "
                  f"schema {schema}. You may add \"yield_until\": \"my_turn\" "
                  f"or \"end_of_turn\" to skip dead windows.\n"
                  + json.dumps(payload))
        t0 = time.time()
        for attempt in (1, 2):
            text = call_pilot(prompt)
            resp = extract_json(text)
            if resp is not None and KEY_FOR.get(kind, "choice") in resp:
                tmp = os.path.join(args.esc_dir, f"resp-{n}.json.tmp")
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(resp, f)
                os.rename(tmp, os.path.join(args.esc_dir, f"resp-{n}.json"))
                log({"seq": n, "kind": kind, "attempt": attempt,
                     "latency_s": round(time.time() - t0, 1),
                     "response": resp, "session": session_id})
                return
            prompt = (f"That reply did not match the schema for kind "
                      f"'{kind}'. Reply with ONLY one JSON object: {schema}")
        log({"seq": n, "kind": kind, "error": "unparseable after retry",
             "raw": text[:400]})

    print(f"pilot daemon up: esc-dir={args.esc_dir} model={args.model}",
          flush=True)
    while True:
        if os.path.exists(os.path.join(args.esc_dir, "DONE")):
            with open(os.path.join(args.esc_dir, "DONE")) as f:
                print("game over:", f.read(), flush=True)
            log({"event": "done"})
            return
        pending = []
        for fn in os.listdir(args.esc_dir):
            m = re.fullmatch(r"req-(\d+)\.json", fn)
            if m:
                n = int(m.group(1))
                if n not in answered and not os.path.exists(
                        os.path.join(args.esc_dir, f"resp-{n}.json")):
                    pending.append(n)
        for n in sorted(pending):
            try:
                answer(n, os.path.join(args.esc_dir, f"req-{n}.json"))
            except subprocess.TimeoutExpired:
                log({"seq": n, "error": "claude -p call timeout"})
            except Exception as e:  # keep the game alive; bridge falls back
                log({"seq": n, "error": str(e)[:400]})
            answered.add(n)
        time.sleep(0.3)


if __name__ == "__main__":
    main()
