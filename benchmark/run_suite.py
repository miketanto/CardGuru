"""Overnight suite runner: a queue of (model, seed) mirror games vs MAD,
N at a time, each one committed and pushed the moment it finishes.

See docs/overnight-suite-plan.md. Every job is one run_mirror.py call in
its OWN out-dir (so concurrent games never collide on game numbering),
with the driver properties for the chosen search arm in the environment.
After each game one self-describing row goes to research/data/suite.jsonl
-- model, seed, arm, result, turns, wall, and the process metrics the
search plan measures (tap-out count, hellbent turn, lands at turn 7) --
and that game's files are committed and pushed, so nothing finished is
lost if the container is reclaimed. Re-running skips jobs already done.

research/data/suite_status.json is rewritten every 60 s with what is
running, its turn and life totals, and the last event; the session
heartbeat reads that file and nothing else.

Usage:
  python3 benchmark/run_suite.py --mage-repo /home/user/magefree/mage \
      --models claude-haiku-4-5 claude-sonnet-5 claude-opus-4-7 claude-opus-5 \
      --seeds 23 31 --workers 2 \
      --props "cardguru.project_turn=3 cardguru.respond=true"
"""
import argparse
import fcntl
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SUITE = os.path.join(ROOT, "research", "data", "suite.jsonl")
STATUS = os.path.join(ROOT, "research", "data", "suite_status.json")
LOG = os.path.join(ROOT, "research", "data", "suite.log")
GIT_LOCK = os.path.join(ROOT, "research", "data", ".suite.gitlock")
LANDS = {"Island", "Swamp", "Darkslick Shores", "Undercity Sewers", "Restless Reef"}

state = {"jobs": {}, "done": 0, "failed": 0, "last_event": "", "consec_fail": 0}
state_lock = threading.Lock()


def now():
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def log(msg):
    line = f"{now()} {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    with state_lock:
        state["last_event"] = line


def short(model):
    return model.replace("claude-", "").replace("-", "")


def done_keys():
    keys = set()
    if os.path.exists(SUITE):
        for line in open(SUITE, encoding="utf-8"):
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("status") == "completed":
                keys.add((r.get("model"), r.get("seed"), r.get("opponent")))
    return keys


def metrics(game_log):
    """Process metrics off one game log, same definitions as the plan."""
    g = [json.loads(l) for l in open(game_log, encoding="utf-8")]
    tap = 0
    hands, lands7 = {}, {}
    for r in g:
        q = r.get("request") or {}
        st = q.get("state") or {}
        t = q.get("turn")
        if (q.get("kind") == "priority" and r.get("source") == "auto"
                and q.get("active") == "A" and "Main" in str(q.get("phase"))):
            hand = [c.get("name") for c in (st.get("A") or {}).get("hand", [])]
            if [h for h in hand if h not in LANDS] \
                    and q.get("mana_available") in ("[]", "[{}]", ""):
                tap += 1
        if t and t not in hands:
            h = (st.get("A") or {}).get("hand_count")
            if h is not None:
                hands[t] = h
        if t == 7 and "A" not in lands7:
            for p in ("A", "B"):
                lands7[p] = sum(1 for c in (st.get(p) or {}).get("battlefield", [])
                                if c.get("name") in LANDS)
    hb = None
    ts = sorted(hands)
    for i, t in enumerate(ts):
        if hands[t] == 0 and all(hands.get(x, 9) <= 1 for x in ts[i:i + 3]):
            hb = t
            break
    plans = sum(1 for r in g if isinstance(r.get("response"), dict)
                and r["response"].get("plan"))
    return {"tap_out_main_phases": tap, "hellbent_turn": hb,
            "lands_t7": lands7, "plans": plans, "rows": len(g)}


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def commit_push(paths, message):
    """Serialised across workers; a failed push is logged, never fatal."""
    with open(GIT_LOCK, "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        try:
            git("add", *paths)
            c = git("-c", "user.email=mikesutanto1812@gmail.com",
                    "-c", "user.name=Mike Tanto", "commit", "-q", "-m", message)
            if c.returncode != 0 and "nothing to commit" not in (c.stdout + c.stderr):
                log(f"git commit failed: {(c.stderr or c.stdout)[-200:]}")
                return
            for attempt in range(4):
                p = git("push", "origin", "HEAD:build/stackwise-campaign")
                if p.returncode == 0:
                    return
                time.sleep(2 ** (attempt + 1))
            log(f"git push failed after retries: {(p.stderr or p.stdout)[-200:]}")
        finally:
            fcntl.flock(lk, fcntl.LOCK_UN)


def run_job(args, model, seed, opponent):
    key = f"{short(model)}_s{seed}"
    out_dir = os.path.join(ROOT, "research", "data", "suite", key)
    os.makedirs(out_dir, exist_ok=True)
    with state_lock:
        state["jobs"][key] = {"model": model, "seed": seed, "started": time.time(),
                              "out_dir": out_dir, "status": "running"}
    log(f"START {key}")
    env = dict(os.environ)
    env["CARDGURU_DRIVER_PROPS"] = args.props
    timeout = args.game_timeout_opus if "opus" in model else args.game_timeout
    cmd = [sys.executable, os.path.join(HERE, "run_mirror.py"),
           "--mage-repo", args.mage_repo, "--out-dir", out_dir,
           "--games", "1", "--seed", str(seed), "--same-seed", "--start", "A",
           "--model", model, "--game-timeout", str(timeout)]
    t0 = time.time()
    with open(os.path.join(out_dir, "runner.log"), "w") as lf:
        proc = subprocess.run(cmd, cwd=ROOT, env=env, stdout=lf, stderr=subprocess.STDOUT)
    wall = round(time.time() - t0, 1)

    row = {"model": model, "seed": seed, "opponent": opponent, "arm_props": args.props,
           "wall_s": wall, "ts": round(time.time(), 1), "out_dir": os.path.relpath(out_dir, ROOT)}
    mirror = os.path.join(out_dir, "mirror.jsonl")
    game_log = os.path.join(out_dir, "g1.jsonl")
    res = None
    if os.path.exists(mirror):
        for line in open(mirror, encoding="utf-8"):
            try:
                res = json.loads(line)
            except json.JSONDecodeError:
                pass
    result = (res or {}).get("result") or {}
    if proc.returncode == 0 and result.get("status") == "completed":
        row.update({"status": "completed", "winner": result.get("winner"),
                    "pilot_won": result.get("winner") == "A",
                    "turns": result.get("turns"), "sources": (res or {}).get("sources"),
                    "searches": (res or {}).get("searches")})
        try:
            row.update(metrics(game_log))
        except Exception as e:
            row["metrics_error"] = str(e)[:200]
        with state_lock:
            state["done"] += 1
            state["consec_fail"] = 0
        log(f"DONE  {key}: {'WIN' if row['pilot_won'] else 'loss'} in {row['turns']} turns, "
            f"{wall / 60:.0f} min, tap-out={row.get('tap_out_main_phases')} hellbent={row.get('hellbent_turn')}")
    else:
        tail = ""
        try:
            tail = open(os.path.join(out_dir, "runner.log")).read()[-300:]
        except OSError:
            pass
        row.update({"status": "failed", "rc": proc.returncode,
                    "error": ((res or {}).get("error") or tail)[-300:]})
        with state_lock:
            state["failed"] += 1
            state["consec_fail"] += 1
        log(f"FAIL  {key}: rc={proc.returncode} {row['error'][-120:]}")
    with open(SUITE, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    with state_lock:
        state["jobs"][key]["status"] = row["status"]
    paths = [os.path.relpath(SUITE, ROOT)]
    for fn in ("g1.jsonl", "g1_daemon.jsonl", "g1_review.md", "g1.html", "mirror.jsonl", "runner.log"):
        p = os.path.join(out_dir, fn)
        if os.path.exists(p):
            paths.append(os.path.relpath(p, ROOT))
    commit_push(paths, f"suite: {key} {row['status']}"
                + (f" -- {'WIN' if row.get('pilot_won') else 'loss'} turn {row.get('turns')}"
                   if row["status"] == "completed" else "")
                + "\n\nCo-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>\n"
                  "Claude-Session: https://claude.ai/code/session_01JuwHrMUQhHsQru1ASawH8p")


def status_writer(total, stop):
    while not stop.is_set():
        snap = {"ts": round(time.time(), 1), "time": now(), "total": total}
        with state_lock:
            snap.update({"done": state["done"], "failed": state["failed"],
                         "last_event": state["last_event"]})
            running = []
            for key, j in state["jobs"].items():
                if j["status"] != "running":
                    continue
                info = {"job": key, "model": j["model"], "seed": j["seed"],
                        "elapsed_min": round((time.time() - j["started"]) / 60, 1)}
                gl = os.path.join(j["out_dir"], "g1.jsonl")
                try:
                    last = None
                    with open(gl, encoding="utf-8") as f:
                        for line in f:
                            last = line
                    r = json.loads(last) if last else {}
                    q = r.get("request") or {}
                    st = q.get("state") or {}
                    info.update({"turn": q.get("turn"),
                                 "life_A": (st.get("A") or {}).get("life"),
                                 "life_B": (st.get("B") or {}).get("life")})
                except Exception:
                    info["turn"] = None
                running.append(info)
            snap["running"] = running
        tmp = STATUS + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(snap, f, indent=1)
        os.replace(tmp, STATUS)
        stop.wait(60)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mage-repo", required=True)
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--seeds", nargs="+", type=int, required=True)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--props", default="cardguru.project_turn=3 cardguru.respond=true")
    ap.add_argument("--game-timeout", type=int, default=9000)
    ap.add_argument("--game-timeout-opus", type=int, default=10800)
    ap.add_argument("--opponent", default="MAD")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(SUITE), exist_ok=True)
    skip = done_keys()
    jobs = [(m, s) for m in args.models for s in args.seeds
            if (m, s, args.opponent) not in skip]
    log(f"suite: {len(jobs)} jobs queued ({len(skip)} already done), workers={args.workers}, props='{args.props}'")

    stop = threading.Event()
    threading.Thread(target=status_writer, args=(len(jobs) + len(skip), stop), daemon=True).start()

    queue = list(jobs)
    qlock = threading.Lock()

    def worker(wid):
        while True:
            with qlock:
                # Back off to one worker after two consecutive failures: a
                # rate-limited login burns the night retrying, and one game at
                # a time at least completes.
                with state_lock:
                    cf = state["consec_fail"]
                if wid > 0 and cf >= 2:
                    log(f"worker {wid} standing down after {cf} consecutive failures")
                    return
                if not queue:
                    return
                m, s = queue.pop(0)
            try:
                run_job(args, m, s, args.opponent)
            except Exception as e:
                log(f"worker {wid} job {m} s{s} raised: {e}")
                with state_lock:
                    state["failed"] += 1
                    state["consec_fail"] += 1
            # stagger so two JVMs do not warm up on the same second
            time.sleep(5)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(args.workers)]
    for i, t in enumerate(threads):
        t.start()
        time.sleep(90 * i)   # stagger worker starts by 90 s
    for t in threads:
        t.join()
    stop.set()
    log(f"suite finished: done={state['done']} failed={state['failed']}")


if __name__ == "__main__":
    main()
