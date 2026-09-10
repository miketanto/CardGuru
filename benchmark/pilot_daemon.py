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
import uuid

SCHEMAS = {
    "mulligan": '{"mulligan": true|false, "why": "...", "plan": "..."}',
    "priority": '{"choice": <option index>, "why": "...", "plan": "..."}',
    "attackers": '{"attackers": [<indices>], "why": "...", "plan": "..."}',
    "blockers": '{"blocks": [[blockerIdx, attackerIdx], ...], "why": "...", '
                '"plan": "..."}',
    "target": '{"targets": [<indices>], "why": "...", "plan": "..."}',
    "choose": '{"targets": [<index>], "why": "..."}',
    "announce_x": '{"x": <int>}',
    "mode": '{"choice": <index>}',
    "use": '{"use": true|false}',
    "leaf_eval": '{"scores": [<0-100 for each leaf, in leaf_index order>], '
                 '"why": "...", "plan": "..."}',
}
KEY_FOR = {"mulligan": "mulligan", "priority": "choice",
           "attackers": "attackers", "blockers": "blocks",
           "target": "targets", "choose": "targets",
           "announce_x": "x", "mode": "choice", "use": "use",
           "leaf_eval": "scores"}

# Decision kinds that MUST carry a standing plan.
#
# Offered as optional, "plan" was never once used: zero plans across 199
# requests in mirror game 4, through a game the pilot lost from an even
# position by tapping out every turn and never holding a board. An optional
# field a model never fills is indistinguishable from no feature, so on the
# decisions that actually shape a game it is now part of the schema and a
# reply without it is retried like any other schema violation.
#
# Excluded are the sub-choices that fire INSIDE a cast the pilot already
# committed to (mode, use, announce_x, choose): the plan was set at the
# priority window that began the cast, and re-asking mid-resolution buys
# nothing but latency.
PLAN_REQUIRED = {"mulligan", "priority", "attackers", "blockers", "target",
                 "leaf_eval"}


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
            # Pin a fresh session id. Without this, a `claude -p` child
            # launched from inside a Claude Code session inherits that
            # session's id from the environment, and every game (and every
            # concurrent game) resumes one shared transcript: the pilot's
            # context fills with other games' decisions, compacts every few
            # calls, and a decision can cost 60-150 s instead of 5-20 s.
            fresh = str(uuid.uuid4())
            cmd += ["--session-id", fresh,
                    "--append-system-prompt-file", args.system]
        # The CLI fails transiently (empty stderr, non-zero exit) often
        # enough that a single failure used to cost a decision — the bridge
        # then fell back to dumb_policy. Retry with backoff; only give up
        # after the last attempt.
        last = ""
        for attempt in range(3):
            out = subprocess.run(cmd, input=prompt, capture_output=True,
                                 text=True, timeout=args.call_timeout)
            if out.returncode == 0:
                try:
                    body = json.loads(out.stdout)
                except json.JSONDecodeError:
                    last = f"unparseable CLI json: {out.stdout[:200]}"
                else:
                    session_id = body.get("session_id") or session_id
                    return body.get("result", "")
            else:
                last = out.stderr[-300:] or f"exit {out.returncode}, no stderr"
            time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"claude -p failed after 3 tries: {last}")

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
        nonlocal session_id
        t0 = time.time()
        base_prompt = prompt
        # Attempt 3 starts a FRESH session: a persistent pilot that is losing
        # can decide to quit outright ("I'm exiting this game", red_vs_dimir
        # g1 seq 55) and no amount of schema nagging inside that conversation
        # recovers it. A new session has the briefing and this decision, but
        # none of the accumulated context it soured on.
        for attempt in (1, 2, 3):
            if attempt == 3:
                session_id = None
                prompt = base_prompt
            text = call_pilot(prompt)
            resp = extract_json(text)
            missing = None
            if resp is None or KEY_FOR.get(kind, "choice") not in resp:
                missing = f"the required key for kind '{kind}'"
            elif kind in PLAN_REQUIRED:
                p = resp.get("plan")
                if not isinstance(p, str) or not p.strip():
                    missing = ('a non-empty "plan"')
            if missing is None:
                tmp = os.path.join(args.esc_dir, f"resp-{n}.json.tmp")
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(resp, f)
                os.rename(tmp, os.path.join(args.esc_dir, f"resp-{n}.json"))
                log({"seq": n, "kind": kind, "attempt": attempt,
                     "latency_s": round(time.time() - t0, 1),
                     "response": resp, "session": session_id,
                     **({"session_reset": True} if attempt == 3 else {})})
                return
            prompt = (f"That reply was missing {missing}. Reply with ONLY one "
                      f"JSON object: {schema}"
                      + (' The "plan" field is REQUIRED on this decision: one '
                         'or two sentences on what you are holding, what you '
                         'are waiting for, and what would change your mind. '
                         'If your standing plan still applies, restate it.'
                         if kind in PLAN_REQUIRED else ""))
        log({"seq": n, "kind": kind,
             "error": "unparseable after retry and session reset",
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
