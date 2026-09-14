# Phase 11 drill-down controller (rl/PHASE11-DRILL.md B2): a copy of rl/league10.py with
# --from-state (seed from the Phase 10 state, lane dirs copied, --frozen mains never train),
# cross over every other main, a 100-game probe every +1,024 per main, the census
# (rl/record_census.sh) at --census-at, and a stop at +--episodes-per-main per main.
#!/usr/bin/env python3
"""Phase 10 league controller (rl/PHASE10-LEAGUE.md A4).

Owns the schedule and the pools; runs ONE learner block at a time through
rl/rung0_lane_league.sh (own OUT dir per learner/generation, resumed from its
agent.pt, R0_INIT only for the first block, budget raised by one block, a
single-entry R0_OPP_SPEC chosen here).  Learners: mains M_W (W0Base), M_D
(BenchDimir), M_L (G1Landfall) and exploiters X_W, X_D, X_L (each plays its
main's deck).  All from fresh P10INIT nets with --cand-refers-pool; recipe = C1
+ --adv-norm batch.

Per block it appends one row to <art>/results.tsv (wins / losses / draws /
stalls vs that opponent from the block's jobs.log RL|summary lines), snapshots
the learner (opt stripped) into <art>/pool/<name>.pt (gitignored) with an event
row in <art>/pool.tsv, and prints

    L10|block|n=..|h=..|stage=..|learner=..|gen=..|trained=a->b|bucket=..|opp=..|odeck=..|W/L/D/S=..|wr=..|probe=..|wall=..s|rc=..

plus L10|grad|..., L10|stage2|..., L10|reset|..., L10|error|..., and one
L10|done|reason=... line at exit.  Resumable: <art>/state.json (a block that was
running is re-run with the same opponent; the lane resumes from agent.pt).
Clean stop: touch <art>/STOP (finishes the current block).

Opponent selection (pre-stated in the runbook):
  main, stage 1: 40 % self latest, 30 % PFSP over its past snapshots + the
  exploiter snapshots added to its pool, weight (1-p)^2 with p = its win rate
  vs that snapshot in results.tsv (unplayed 0.5), 15 % its exploiter's latest,
  15 % heuristic (same deck).  First block of a fresh main = heuristic.
  main, stage 2: 30 / 20 / 10 / 10 + 30 % cross-deck (other graduated mains'
  latest, PFSP-weighted, opponent on its own deck).
  Fallbacks (logged in the bucket as a->b): pfsp/cross with an empty pool ->
  self; expl with no exploiter snapshot -> heur.
  exploiter: always the frozen latest of its main; reset to a fresh net when
  its block win rate >= 0.70 (snapshot added to the main's pool first) or
  after 4 blocks without that (snapshot added only if >= 0.55).
  Graduation: a main's 50-game development probe vs the heuristic on its own
  mirror after every 4th block, point >= 0.65.  Stage 2 when >= 2 mains
  graduated or at controller hour 5 (forced; then, if no other main has
  graduated, the cross pool is every other main).  Mains are snapshotted as
  <main>_s1end at the boundary.  Hard stop at controller hour 10.
Added (stated in the row): each fresh main also gets a 50-game probe at
trained=0 (the lane's start battery), the first development point.

Usage (WSL):  python3 rl/league10.py            (the real run)
              python3 rl/league10.py --tag smoke --learners M_W,X_W --schedule M_W,X_W \
                  --block 32 --chunk 32 --probe-every 1 --probe-games 4 --max-blocks 2
"""
import argparse
import json
import math
import os
import random
import shutil
import subprocess
import sys
import time

import torch

RL = "/home/user/CardGuru/rl"
LB = "/mnt/c/Users/sutanto4/Documents/CardGuru"
MAIN_DECK = {"M_W": "W0Base", "M_D": "BenchDimir", "M_L": "G1Landfall"}
EXPL_OF = {"X_W": "M_W", "X_D": "M_D", "X_L": "M_L"}
MAIN_EXPL = {v: k for k, v in EXPL_OF.items()}
SCHEDULE = ["M_W", "M_D", "M_L", "X_W", "M_W", "M_D", "M_L", "X_D", "M_W", "M_D", "M_L", "X_L"]
LANE_SEED = {"M_W": 1, "M_D": 2, "M_L": 3, "X_W": 4, "X_D": 5, "X_L": 6}   # + 10 * exploiter generation
SRVEXTRA = ("--device cuda --epochs 1 --logit-bound 5 --weight-decay 0.01 --adv-norm batch "
            "--target-kl 0.02 --argmax-classes --cand-refers-pool")
MIX1 = [("self", .40), ("pfsp", .30), ("expl", .15), ("heur", .15)]
MIX2 = [("self", .30), ("pfsp", .20), ("expl", .10), ("heur", .10), ("cross", .30)]
RES_COLS = ["n", "time_utc", "hour", "stage", "learner", "gen", "trained_before", "trained_after",
            "bucket", "draw", "opp_kind", "opp", "opp_deck", "episodes", "wins", "losses", "draws",
            "stalls", "win_rate", "job_errors", "probe_games", "probe_wr", "probe_lo", "probe_hi",
            "snapshot", "wall_s", "rc"]
POOL_COLS = ["event", "name", "learner", "gen", "deck", "trained", "n", "pool", "time_utc", "path"]


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def wilson(k, n, z=1.96):
    if n <= 0:
        return 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def say(*parts):
    print("|".join(str(p) for p in parts), flush=True)


def ck_episodes(path):
    if not os.path.exists(path):
        return 0
    try:
        return int(torch.load(path, map_location="cpu", weights_only=False).get("episodes", 0))
    except Exception:
        return -1


def field(path, key):
    try:
        for tok in open(path).read().replace("|", " ").split():
            if tok.startswith(key + "="):
                return tok.split("=", 1)[1]
    except OSError:
        pass
    return None


class League:
    def __init__(self, a):
        self.a = a
        self.art = a.art
        self.pool_dir = os.path.join(self.art, "pool")
        os.makedirs(self.pool_dir, exist_ok=True)
        os.makedirs(os.path.join(self.art, "inits"), exist_ok=True)
        self.state_path = os.path.join(self.art, "state.json")
        self.res_path = os.path.join(self.art, "results.tsv")
        self.poolidx_path = os.path.join(self.art, "pool.tsv")
        for p, cols in ((self.res_path, RES_COLS), (self.poolidx_path, POOL_COLS)):
            if not os.path.exists(p):
                with open(p, "w") as fh:
                    fh.write("\t".join(cols) + "\n")
        if os.path.exists(self.state_path):
            self.st = json.load(open(self.state_path))
            say("L11", "resume", f"n={self.st['n']}", f"sched_i={self.st['sched_i']}", f"stage={self.st['stage']}",
                f"h={self.hour():.2f}", f"pending={bool(self.st.get('pending'))}")
        elif a.from_state:
            src = json.load(open(a.from_state))
            self.st = {"start": time.time(), "start_utc": utc(), "n": 0, "sched_i": 0, "stage": src["stage"],
                       "stage2": src.get("stage2"), "learners": {}, "pools": src["pools"], "snaps": src["snaps"],
                       "pending": None, "fails": 0, "expl_latest": src.get("expl_latest", {}),
                       "probe0": src.get("probe0", {}),
                       "drill": {"from": a.from_state, "start_trained": {}, "frozen": a.frozen}}
            for name in list(a.learners) + [f for f in a.frozen if f not in a.learners]:
                L = dict(src["learners"][name])
                if name in a.learners:
                    new_out = a.out_root + name + (f"_g{L['gen']}" if L["gen"] else "")
                    if not os.path.exists(new_out):
                        shutil.copytree(L["out"], new_out)
                    L["out"] = new_out
                    L["trained"] = ck_episodes(os.path.join(new_out, "agent.pt"))
                    if name in MAIN_DECK:
                        self.st["drill"]["start_trained"][name] = L["trained"]
                self.st["learners"][name] = L
            say("L11", "seed", f"from={a.from_state}", f"art={self.art}", f"learners={','.join(a.learners)}",
                f"frozen={','.join(a.frozen)}", f"schedule={','.join(a.schedule)}", f"block={a.block}", f"hours={a.hours}",
                "start_trained=" + ",".join(f"{k}:{v}" for k, v in self.st["drill"]["start_trained"].items()),
                "latest=" + ",".join(f"{k}:{v['latest']}" for k, v in self.st["learners"].items()),
                f"stage={self.st['stage']}", f"srvextra={SRVEXTRA}")
            self.save()
        else:
            self.st = {"start": time.time(), "start_utc": utc(), "n": 0, "sched_i": 0, "stage": 1,
                       "stage2": None, "learners": {}, "pools": {m: [] for m in MAIN_DECK},
                       "snaps": {}, "pending": None, "fails": 0}
            for name in a.learners:
                self.st["learners"][name] = self.new_learner(name, 0)
            say("L11", "start", f"art={self.art}", f"learners={','.join(a.learners)}",
                f"schedule={','.join(a.schedule)}", f"block={a.block}", f"hours={a.hours}", f"srvextra={SRVEXTRA}")
            self.save()

    # ---------------------------------------------------------------- state
    def hour(self):
        return (time.time() - self.st["start"]) / 3600.0

    def save(self):
        tmp = self.state_path + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(self.st, fh, indent=1)
        os.replace(tmp, self.state_path)

    def new_learner(self, name, gen):
        seed = LANE_SEED[name] + 10 * gen
        deck = MAIN_DECK.get(name) or MAIN_DECK[EXPL_OF[name]]
        return {"deck": deck, "gen": gen, "lane_seed": seed, "init_seed": 1000 + seed,
                "out": self.a.out_root + name + (f"_g{gen}" if gen else ""),
                "blocks": 0, "gen_blocks": 0, "graduated": False, "grad": None, "latest": None}

    def pool_event(self, ev, name, pool=""):
        s = self.st["snaps"][name]
        with open(self.poolidx_path, "a") as fh:
            fh.write("\t".join(str(x) for x in [ev, name, s["learner"], s["gen"], s["deck"], s["trained"],
                                                   self.st["n"], pool, utc(), s["path"]]) + "\n")

    def results(self):
        rows = []
        with open(self.res_path) as fh:
            head = fh.readline().rstrip("\n").split("\t")
            for line in fh:
                rows.append(dict(zip(head, line.rstrip("\n").split("\t"))))
        return rows

    def p_vs(self, learner, opp):
        w = n = 0
        for r in self.results():
            if r["learner"] == learner and r["opp"] == opp:
                w += int(r["wins"] or 0)
                n += int(r["episodes"] or 0)
        return w / n if n else 0.5

    def pfsp(self, learner, cands, rng):
        ws = [(1.0 - self.p_vs(learner, c)) ** 2 for c in cands]
        if sum(ws) <= 0:
            ws = [1.0] * len(cands)
        return rng.choices(cands, weights=ws, k=1)[0]

    # ---------------------------------------------------------------- opponents
    def choose(self, name, rng):
        """-> (bucket, draw, snapshot name or None for the heuristic)."""
        L = self.st["learners"][name]
        if name in EXPL_OF:
            return "exploit", -1.0, self.st["learners"][EXPL_OF[name]]["latest"]
        if L["blocks"] == 0 or not L["latest"]:
            return "first", -1.0, None
        mix = MIX2 if self.st["stage"] == 2 else MIX1
        r = rng.random()
        acc, bucket = 0.0, mix[-1][0]
        for b, w in mix:
            acc += w
            if r < acc:
                bucket = b
                break
        # Amendment 3 (sampling shortfall, rl/PHASE10-LEAGUE.md): in stage 2 each main
        # gets a quota on its REALIZED stage-2 shares - cross below 0.30 forces cross,
        # else heur below 0.10 forces heur, else the MIX2 draw above stands. The draw is
        # still consumed, so seeding / PFSP / resolve are unchanged.
        label = bucket
        if self.st["stage"] == 2:
            cross_s, heur_s = self.stage2_shares(name)
            if cross_s < 0.30:
                bucket, label = "cross", "cross(quota)"
            elif heur_s < 0.10:
                bucket, label = "heur", "heur(quota)"
        opp, eff = self.resolve(name, bucket, rng)
        return (label if eff == bucket else f"{label}->{eff}"), r, opp

    def stage2_shares(self, name):
        """Realized stage-2 shares of effective cross / heur blocks for a main (rc 0 rows;
        a fallback counts as what it fell back to)."""
        rows = [x for x in self.results() if x["learner"] == name and x["stage"] == "2" and x["rc"] == "0"]
        if not rows:
            return 0.0, 0.0
        eff = [x["bucket"].split("->")[-1].replace("(quota)", "") for x in rows]
        return eff.count("cross") / len(rows), eff.count("heur") / len(rows)

    def resolve(self, name, bucket, rng):
        L = self.st["learners"][name]
        if bucket == "self":
            return L["latest"], "self"
        if bucket == "heur":
            return None, "heur"
        if bucket == "pfsp":
            cands = [s for s in self.st["pools"][name] if s != L["latest"]]
            return (self.pfsp(name, cands, rng), "pfsp") if cands else self.resolve(name, "self", rng)
        if bucket == "expl":
            x = self.st.get("expl_latest", {}).get(MAIN_EXPL[name])
            return (x, "expl") if x else self.resolve(name, "heur", rng)
        if bucket == "cross":
            others = [m for m in MAIN_DECK if m != name and m in self.st["learners"]
                      and self.st["learners"][m]["latest"]]      # Phase 11: {M_W, the other main}, graduated or not
            if not others and (self.st.get("stage2") or {}).get("forced"):
                others = [m for m in MAIN_DECK if m != name and m in self.st["learners"]
                          and self.st["learners"][m]["latest"]]
            cands = [self.st["learners"][m]["latest"] for m in others]
            return (self.pfsp(name, cands, rng), "cross") if cands else self.resolve(name, "self", rng)
        raise ValueError(bucket)

    # ---------------------------------------------------------------- one block
    def mint_init(self, name, L):
        path = os.path.join(self.art, "inits", f"{name}_g{L['gen']}.pt")
        if not os.path.exists(path):
            out = subprocess.run([sys.executable, f"{RL}/p10_init_net.py", "--out", path, "--arch", "v7",
                                  "--seed", str(L["init_seed"]), "--sdim", "32", "--cdim", "94",
                                  "--cand-refers-pool"], capture_output=True, text=True, cwd="/home/user/CardGuru")
            line = [x for x in out.stdout.splitlines() if x.startswith("P10INIT")]
            say("L11", "init", name, f"gen={L['gen']}", f"seed={L['init_seed']}", line[-1] if line else out.stderr[-300:])
        return path

    def snapshot(self, name, L, trained):
        sname = (f"{name}.g{L['gen']}" if name in EXPL_OF else name) + f"_{trained:05d}"
        path = os.path.join(self.pool_dir, sname + ".pt")
        ck = torch.load(os.path.join(L["out"], "agent.pt"), map_location="cpu", weights_only=False)
        ck.pop("opt", None)                               # a frozen opponent needs the net only
        torch.save(ck, path + ".tmp")
        os.replace(path + ".tmp", path)
        self.st["snaps"][sname] = {"path": path, "learner": name, "gen": L["gen"], "deck": L["deck"], "trained": trained}
        for f in os.listdir(L["out"]):                    # the lane's per-block ck copies (246 MB each)
            if f.startswith("ck_") and f.endswith(".pt"):
                os.remove(os.path.join(L["out"], f))
        return sname

    def run_block(self, name):
        a, L = self.a, self.st["learners"][name]
        is_main = name in MAIN_DECK
        pend = self.st.get("pending")
        if pend and pend["learner"] == name and pend["gen"] == L["gen"]:
            spec = pend
            say("L11", "rerun", name, f"budget={spec['budget']}", f"opp={spec['opp']}")
        else:
            if name in EXPL_OF and not self.st["learners"][EXPL_OF[name]]["latest"]:
                say("L11", "skip", name, "main has no snapshot yet")
                return True
            rng = random.Random(10_000 + self.st["n"])
            bucket, draw, opp = self.choose(name, rng)
            os.makedirs(L["out"], exist_ok=True)
            agent = os.path.join(L["out"], "agent.pt")
            tb = ck_episodes(agent)
            spec = {"learner": name, "gen": L["gen"], "bucket": bucket, "draw": round(draw, 4), "opp": opp,
                    "first": not os.path.exists(agent), "trained_before": tb, "budget": tb + a.block,
                    "probe_due": bool(is_main and (tb + a.block - self.st.get("drill", {}).get("start_trained", {}).get(name, 0))
                                      % (a.probe_every * a.block) == 0),
                    "jobs_off": os.path.getsize(os.path.join(L["out"], "jobs.log")) if os.path.exists(os.path.join(L["out"], "jobs.log")) else 0,
                    "t0": time.time()}
            self.st["pending"] = spec
            self.save()
        opp = spec["opp"]
        if opp is None:
            kind, odeck, ospec = "heuristic", L["deck"], f"heuristic::{L['deck']}.dck"
        else:
            s = self.st["snaps"][opp]
            kind, odeck, ospec = "rl", s["deck"], f"rl:{s['path']}:{s['deck']}.dck"
        env = dict(os.environ)
        env.update({"R0_ENCODER_V": "7", "R0_EVERY": str(a.block), "R0_CHUNK": str(a.chunk), "R0_CP7_G": "0",
                    "R0_CONC": "4", "R0_LR": "3e-5", "RL_LOCK_STATS": "1", "RL_DRIVER_PORT": str(a.dport),
                    "R0_PORT": str(a.port), "R0_OPP_PORT": str(a.oport), "R0_OUT": L["out"],
                    "R0_SRVEXTRA": SRVEXTRA, "R0_OPP_SPEC": ospec,
                    "R0_ROWS": "D0" if (is_main and spec["first"]) else "none",
                    "R0_ROWS_FINAL": "D0" if spec["probe_due"] else "none",
                    "R0_EVAL_G": str(a.probe_games), "R0_EVAL_G_INTERIM": str(a.probe_games)})
        env.pop("R0_INIT", None)
        if spec["first"] or not os.path.exists(os.path.join(L["out"], "agent.pt")):
            env["R0_INIT"] = self.mint_init(name, L)
        os.makedirs(L["out"], exist_ok=True)
        cmd = ["bash", f"{RL}/rung0_lane_league.sh", L["deck"], L["deck"], str(spec["budget"]), str(L["lane_seed"])]
        t0 = time.time()
        rc = -1
        for attempt in (1, 2):
            with open(os.path.join(L["out"], "lane.log"), "a") as fh:
                fh.write(f"# L10 block n={self.st['n']} attempt={attempt} {utc()} opp={ospec}\n")
                fh.flush()
                rc = subprocess.call(cmd, env=env, stdout=fh, stderr=subprocess.STDOUT, cwd="/home/user/CardGuru")
            ta = ck_episodes(os.path.join(L["out"], "agent.pt"))
            if rc == 0 and ta >= spec["budget"] - a.chunk:
                break
            say("L11", "error", name, f"attempt={attempt}", f"rc={rc}", f"trained={ta}", f"lane_log={L['out']}/lane.log")
            if "R0_INIT" in env and os.path.exists(os.path.join(L["out"], "agent.pt")):
                env.pop("R0_INIT")                        # the retry resumes from agent.pt
        ta = ck_episodes(os.path.join(L["out"], "agent.pt"))
        ok = rc == 0 and ta >= spec["budget"] - a.chunk
        # the block's jobs (offset recorded before the first attempt)
        W = Lo = D = S = E = N = 0
        jl = os.path.join(L["out"], "jobs.log")
        if os.path.exists(jl):
            with open(jl) as fh:
                fh.seek(spec["jobs_off"])
                for line in fh:
                    if line.startswith("RLJOB|error"):
                        E += 1
                    if not line.startswith("RL|summary"):
                        continue
                    kv = dict(t.split("=", 1) for t in line.strip().split("|")[2:] if "=" in t)
                    N += int(kv.get("episodes", 0)); W += int(kv.get("wins", 0)); Lo += int(kv.get("losses", 0))
                    D += int(kv.get("draws", 0)); S += int(kv.get("stalls", 0))
        wr = W / N if N else float("nan")
        pg = pw = plo = phi = ""
        if spec["probe_due"] and ok:
            v = field(os.path.join(L["out"], f"probe_D0_{spec['budget']}.txt"), "win_rate")
            g = field(os.path.join(L["out"], f"probe_D0_{spec['budget']}.txt"), "episodes")
            if v is not None:
                pw, pg = float(v), int(g or a.probe_games)
                plo, phi = wilson(round(pw * pg), pg)
        if spec["first"] and is_main:
            v0 = field(os.path.join(L["out"], "probe_D0_0.txt"), "win_rate")
            if v0 is not None:
                lo0, hi0 = wilson(round(float(v0) * a.probe_games), a.probe_games)
                say("L11", "probe0", name, f"wr={float(v0):.3f} [{lo0:.3f},{hi0:.3f}]", f"games={a.probe_games}")
                self.st.setdefault("probe0", {})[name] = float(v0)
        sname = self.snapshot(name, L, ta) if ok else ""
        if ok and is_main and self.st.get("drill"):
            gained = spec["budget"] - self.st["drill"]["start_trained"].get(name, 0)
            if gained in self.a.census_at:
                self.census(name, L, sname, gained)
        wall = time.time() - t0
        row = [self.st["n"], utc(), f"{self.hour():.3f}", self.st["stage"], name, L["gen"], spec["trained_before"], ta,
               spec["bucket"], spec["draw"], kind, opp or "heuristic", odeck, N, W, Lo, D, S,
               f"{wr:.4f}" if N else "NA", E, pg, f"{pw:.3f}" if pw != "" else "", f"{plo:.3f}" if plo != "" else "",
               f"{phi:.3f}" if phi != "" else "", sname, f"{wall:.0f}", rc]
        with open(self.res_path, "a") as fh:
            fh.write("\t".join(str(x) for x in row) + "\n")
        say("L11", "block", f"n={self.st['n']}", f"h={self.hour():.2f}", f"stage={self.st['stage']}", f"learner={name}",
            f"gen={L['gen']}", f"trained={spec['trained_before']}->{ta}", f"bucket={spec['bucket']}",
            f"opp={opp or 'heuristic'}", f"odeck={odeck}", f"W/L/D/S={W}/{Lo}/{D}/{S}",
            f"wr={wr:.3f}" if N else "wr=NA",
            f"probe={pw:.3f} [{plo:.3f},{phi:.3f}]" if pw != "" else "probe=-", f"wall={wall:.0f}s", f"rc={rc}")
        self.st["pending"] = None
        if not ok:
            self.st["fails"] += 1
            self.save()
            return False
        self.st["fails"] = 0
        L["blocks"] += 1
        L["trained"] = ta
        L["latest"] = sname
        if is_main:
            self.st["pools"][name].append(sname)
            self.pool_event("snap", sname, pool=name)
            if pw != "" and pw >= 0.65 and not L["graduated"]:
                L["graduated"], L["grad"] = True, {"n": self.st["n"], "trained": ta, "probe": pw, "h": round(self.hour(), 3)}
                say("L11", "grad", name, f"trained={ta}", f"probe={pw:.3f} [{plo:.3f},{phi:.3f}]", f"h={self.hour():.2f}")
        else:
            self.pool_event("snap", sname, pool="")
            self.st.setdefault("expl_latest", {})[name] = sname
            L["gen_blocks"] += 1
            m = EXPL_OF[name]
            reset = add = None
            if N and wr >= 0.70:
                reset, add = "won", True
            elif L["gen_blocks"] >= 4:
                reset, add = "4blocks", (N > 0 and wr >= 0.55)
            if reset:
                if add:
                    self.st["pools"][m].append(sname)
                    self.pool_event("pool_add", sname, pool=m)
                self.st["learners"][name] = self.new_learner(name, L["gen"] + 1)
                say("L11", "reset", name, f"gen={L['gen']}->{L['gen'] + 1}", f"why={reset}", f"wr={wr:.3f}",
                    f"added_to_{m}={'yes' if add else 'no'}")
        self.check_stage2()
        self.save()
        return True

    def drill_done(self, name):
        d = self.st.get("drill")
        if not d:
            return False
        m = name if name in MAIN_DECK else EXPL_OF.get(name)
        if m not in d["start_trained"]:
            return False
        return self.st["learners"][m].get("trained", 0) >= d["start_trained"][m] + self.a.episodes_per_main

    def census(self, name, L, sname, gained):
        tag = f"drill_{name}_p{gained}"
        path = self.st["snaps"][sname]["path"]
        say("L11", "census_start", name, f"tag={tag}", f"ckpt={os.path.basename(path)}", f"games={self.a.census_games}")
        out = subprocess.run(["bash", f"{RL}/record_census.sh", path, L["deck"], "heuristic", str(self.a.census_games),
                              tag, "11000"], capture_output=True, text=True, cwd="/home/user/CardGuru")
        for ln in out.stdout.splitlines():
            if ln.startswith(("CENSUSREC|", "DC|", "LC|")):
                say("L11", "census", ln)

    def dry(self, n):
        for i in range(n):
            name = self.a.schedule[i % len(self.a.schedule)]
            L = self.st["learners"][name]
            rng = random.Random(10_000 + self.st["n"] + i)
            bucket, draw, opp = self.choose(name, rng)
            tb = L.get("trained", 0)
            start = self.st["drill"]["start_trained"].get(name, 0)
            due = name in MAIN_DECK and (tb + self.a.block - start) % (self.a.probe_every * self.a.block) == 0
            say("L11", "dry", name, f"out={L['out']}", f"trained={tb}", f"start={start}", f"bucket={bucket}",
                f"opp={opp or 'heuristic'}", f"probe_due={due}", f"done={self.drill_done(name)}")

    def check_stage2(self):
        if self.st["stage"] != 1:
            return
        grads = [m for m in MAIN_DECK if m in self.st["learners"] and self.st["learners"][m]["graduated"]]
        forced = self.hour() >= self.a.stage2_hour
        if len(grads) >= 2 or forced:
            self.st["stage"] = 2
            self.st["stage2"] = {"n": self.st["n"], "h": round(self.hour(), 3), "graduated": grads,
                                 "forced": len(grads) < 2}
            for m in MAIN_DECK:
                L = self.st["learners"].get(m)
                if not L or not L["latest"]:
                    continue
                src = self.st["snaps"][L["latest"]]
                name = f"{m}_s1end"
                path = os.path.join(self.pool_dir, name + ".pt")
                shutil.copyfile(src["path"], path)
                self.st["snaps"][name] = dict(src, path=path)
                self.pool_event("s1end", name, pool="")
            say("L11", "stage2", f"n={self.st['n']}", f"h={self.hour():.2f}", f"graduated={','.join(grads) or 'none'}",
                f"forced={int(len(grads) < 2)}")

    # ---------------------------------------------------------------- loop
    def run(self):
        a = self.a
        blocks_here = 0
        reason = "?"
        while True:
            if os.path.exists(os.path.join(self.art, "STOP")):
                reason = "stopfile"
                break
            if self.hour() >= a.hours:
                reason = "hours"
                break
            if a.max_blocks and blocks_here >= a.max_blocks:
                reason = "max_blocks"
                break
            if self.st["fails"] >= 3:
                reason = "errors"
                break
            if self.st.get("drill") and all(self.drill_done(m) for m in self.st["drill"]["start_trained"]):
                reason = "episodes"
                break
            name = a.schedule[self.st["sched_i"] % len(a.schedule)]
            if name not in self.st["learners"] or self.drill_done(name):
                self.st["sched_i"] += 1
                continue
            ok = self.run_block(name)
            blocks_here += 1
            self.st["n"] += 1
            if ok:
                self.st["sched_i"] += 1
            self.save()
        subprocess.call(["bash", f"{RL}/driver_server.sh", "stop", str(a.dport)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        grads = ",".join(m for m in MAIN_DECK if m in self.st["learners"] and self.st["learners"][m]["graduated"])
        say("L11", "done", f"reason={reason}", f"blocks={self.st['n']}", f"h={self.hour():.2f}",
            f"stage={self.st['stage']}", f"graduated={grads or 'none'}", f"results={self.res_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="main")
    ap.add_argument("--art", default=None, help="default rl/artifacts/v7/10 (tag main) or .../10/<tag>")
    ap.add_argument("--out-root", default=None, help="lane state prefix; default /tmp/rl_10_ (or /tmp/rl_10<tag>_)")
    ap.add_argument("--learners", default="M_D,M_L,X_D,X_L")
    ap.add_argument("--schedule", default="M_D,M_L,X_D,M_D,M_L,X_L")
    ap.add_argument("--from-state", default=None, help="seed a fresh drill state from this Phase 10 state.json")
    ap.add_argument("--frozen", default="M_W", help="mains copied from --from-state that never train")
    ap.add_argument("--episodes-per-main", type=int, default=4096)
    ap.add_argument("--census-at", default="2048,4096")
    ap.add_argument("--census-games", type=int, default=50)
    ap.add_argument("--dry-run", type=int, default=0, help="print N schedule steps' opponent choices and exit")
    ap.add_argument("--block", type=int, default=256)
    ap.add_argument("--chunk", type=int, default=64)
    ap.add_argument("--probe-every", type=int, default=4)
    ap.add_argument("--probe-games", type=int, default=100)
    ap.add_argument("--hours", type=float, default=10.0)
    ap.add_argument("--stage2-hour", type=float, default=5.0)
    ap.add_argument("--max-blocks", type=int, default=0)
    ap.add_argument("--dport", type=int, default=7912)
    ap.add_argument("--port", type=int, default=7950)
    ap.add_argument("--oport", type=int, default=7960)
    a = ap.parse_args()
    a.learners = a.learners.split(",")
    a.schedule = [s for s in a.schedule.split(",") if s in a.learners]
    a.art = a.art or (f"{LB}/rl/artifacts/v7/11/drill" if a.tag == "main" else f"{LB}/rl/artifacts/v7/11/drill_{a.tag}")
    a.out_root = a.out_root or ("/tmp/rl_11_" if a.tag == "main" else f"/tmp/rl_11{a.tag}_")
    a.frozen = [x for x in a.frozen.split(",") if x]
    a.census_at = {int(x) for x in a.census_at.split(",") if x}
    assert a.block % a.chunk == 0, "block must be a multiple of chunk"
    lg = League(a)
    if a.dry_run:
        lg.dry(a.dry_run)
    else:
        lg.run()


if __name__ == "__main__":
    main()
