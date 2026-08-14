# Handoff — black branch (threat assessment), rung 0

You are running the **black branch** of the curriculum ladder. A parallel
session is running the white branch. The two are independent by
construction — different colours, different skills, no shared card, no
shared instrument — so neither of us has to wait for the other.

Read `rl/CURRICULUM-LADDER.md` first. §5 is your branch, §6 is why we
are running them at the same time. Everything below assumes it.

---

## 1. What you are doing

```
bash rl/rung0_sweep.sh B0Base B0Twin 2048 5
```

with

```
R0_EVERY=512 R0_EVAL_G=200 R0_CP7_G=50
```

exported first — that is the exact configuration the white branch is
running, and matching it is the point. Rung 0 is the same experiment on
both branches (can a from-scratch net learn combat in a minimal game),
so anything that differs between the two lanes other than the deck is a
confound in a comparison we will want to make later.

Expect **roughly 2.5-3 hours per seed** at budget 2048, five seeds.
The white branch measured the real cost: **0.37 episodes/sec at conc4**
for training, plus ~10 min per 200-game battery. The gate's 12-16
games/sec is a SCRIPTED mirror with no policy round-trips and does not
apply to a training lane - and it gets slower as the agent improves
(policy consults/ep went 19.6 -> 165.1 between trained=0 and 512).
Budget 2048 rather than 4096 because the white branch beat 1-ply search
at 512 episodes, so the plateau in this minimal game is early.

Launch it detached and do not sit on it:

```
export R0_EVERY=512 R0_EVAL_G=200 R0_CP7_G=50
setsid nohup bash rl/rung0_sweep.sh B0Base B0Twin 2048 5 \
    > /tmp/rl_rung0_B0Base_sweep.out 2>&1 &
```

Progress lines land in `/tmp/rl_rung0_B0Base_sweep.out` and
`/tmp/rl_rung0_B0Base_sweep.log`; checkpoints and probe files under
`/tmp/rl_rung0_B0Base_s<seed>/`.

### If you are on the same machine as the white branch

Check first — `pgrep -af rung0_lane`. If the white lane is running here,
**do not start a second one at conc4.** The box has 4 cores, each lane
already runs the engine at conc4, and three separate branches have
independently discovered what happens when you oversubscribe it
(`POOLED-ANALYSIS.md` §3). Either wait for the white sweep to finish or
run yours at `R0_CONC=2`, and say in your report which you did, because
it changes the wall-clock numbers and nothing else.

If you are in your own container, ignore this and run at the default.

---

## 2. Setup, if the container is fresh

Per `rl/CHECKPOINT-PHASE10.md` §5: XMage pinned at `7554968c`, plus
`rl/engine-patches/phase9-engine.patch`, the `rl/xmage-src` overlays, and
the Phase 9 fast path (`rl/PHASE9-PERF.md`). Two things that have cost
this project time before:

- clone with `--filter=blob:none --no-checkout` and then
  `git checkout 7554968c`; a `--depth 1` clone cannot resolve an
  abbreviated SHA;
- `pip install --break-system-packages torch`, or the install silently
  does nothing.

Then rebuild the decks and re-run the gate before training anything:

```
python3 rl/bladder_decks.py
bash rl/wladder_gate.sh 40 B0Base B0Twin B1Narrow B2Mid B3Open B1Fast B4Card
```

You should reproduce the table in `CURRICULUM-LADDER.md` §9 — 0 stalls
everywhere, ~13 turns, every mirror inside ±.155 of .5. If a deck comes
back with a load failure or a stall, stop and fix that first; a 0-card
deck still "runs" and produces perfectly healthy-looking nonsense.

---

## 3. What the lane does, so you can read its output

`rl/rung0_lane.sh` is deliberately small — a fixed opponent, a fixed
deck, a battery. Every reported number is **sequential**; only training
runs at conc4.

```
R0|B0Base|s0|trained=1024|D0=0.71±0.063|D1=0.58±0.068|TWIN=0.66±0.066|blocks=412/430|turns=15.2
```

| column | what it is |
|---|---|
| `D0` | vs the scripted heuristic on `B0Base` — the training opponent, so this is the learning curve and nothing more |
| `D1` | vs 1-ply search. Phase 4 recorded terminal-reward PPO failing to beat it; rung 0 is the smallest game in which to re-ask |
| `TWIN` | vs D0 on `B0Twin` — same costs, same stat lines, **no shared card**. A drop here is card-identity dependence with no strategic story available |
| `blocks` | blocks declared / block opportunities |
| `CP7` | once, at the end. XMage's shipped alpha-beta AI, **held out** |

**Do not train against CP7.** It is the only externally uncontaminated
number this project has (`PHASE12-XMAGE-AI.md`); the moment it enters a
training pool we are measuring training performance. Our best agents
score ~.25 against it, and the research question is whether anything we
build moves that past .50.

---

## 4. What to report back

Use `rl/rung0_report.py --base B0Base`, not the lane's own log lines.

**The lane's inline `±` is a Wald interval and is wrong at the edges.**
It collapses to `±0.000` when a checkpoint goes 0/200 or 200/200, and
the untrained baseline does exactly that — the first row of your log
will claim zero uncertainty about a result it has no right to be certain
of. The report script uses a Wilson score interval, which stays finite
there (0/200 → `[0.000, 0.019]`). Treat the report script as
authoritative and do not quote the raw `±` from the log. The lane itself
is left alone while a sweep is running — bash reads a script
incrementally and editing one mid-run has corrupted a run here before.

The per-seed lines are raw material, not the result. What is wanted:

1. **Pooled across 5 seeds**, with 95% bands: D0, D1, TWIN, CP7 at the
   final checkpoint. Pooled CP7 is 250 games (±.06) against the ±.13 of
   the single 50-game rows in `PHASE12-XMAGE-AI.md` — that is the number
   worth carrying.
2. **Where it saturates.** Every run in `POOLED-ANALYSIS.md` §4
   plateaued between 1.5k and 6k episodes against a fixed population.
   Rung 0 is a far smaller game - the white branch was already beating
   1-ply search at 512 - so if it saturates there, say so and say the
   remaining budget bought nothing.
3. **The transfer gap, D0 − TWIN, per seed and pooled.** This is the
   branch's sharpest single number. 8b inferred card-identity dependence
   from a 12-card swap where roles only approximately matched; `B0Twin`
   is that question asked properly.
4. **Between-seed spread on every claim.** If a result does not survive
   5 seeds, report it as not surviving. That is the whole reason we are
   paying for 5.

Commit and push after each seed finishes — the container gets reclaimed
during idle and this has cost us runs twice.

---

## 5. After rung 0 — your branch's actual question

Rung 0 is shared groundwork. The black branch exists for §5 of
`CURRICULUM-LADDER.md`: `B1Narrow → B2Mid → B3Open` widens the legal
target set at fixed cost, colour, count, type and slot, so **only the
card name changes**.

Two things to know before you get there:

**There is an instrumentation gap and it is on the critical path.** The
strong measurement for this branch is not win rate — it is the
distribution of chosen targets by power (threat assessment concentrates
kills on high power; a board-blind policy is uniform over the legal
set). That is a chi-square on fixed weights, a within-net measurement,
the class `POOLED-ANALYSIS.md` §6 found actually replicates, and it
needs no second training run. **But the action log records the spell and
not the target it was pointed at.** `EpisodeRunner` needs a small change
to log the chosen target's power. Build that before running B1/B2/B3,
not after — otherwise the rungs produce only win rates and the branch's
best instrument is unavailable.

**`B4Card` carries a prediction that was recorded before any training.**
Mind Knives costs the same, sits in the same slot, does nothing to the
board, and offers no choice. It is pure card advantage — value that
never becomes visible, which is the hardest possible case for a terminal
reward signal. The prediction on record is that **this is the rung the
agent fails**. If it casts Mind Knives at a sensible rate, the
prediction is wrong, and that is a more interesting result than any win
rate in the document. Report it either way, and do not quietly drop the
rung if it looks uninteresting.

---

## 6. Ground rules

- Branch: develop and push to `claude/cardguru-p10-flagship-48r5lg`
  unless you have been given your own. **Never push to the phase-5
  branch.**
- `RL_TORCH_THREADS=1` on every policy server. The lane already does it;
  if you write a new one, keep it. It is worth 1.54x and three branches
  found it the hard way.
- Sequential for anything you report. conc4 for training only.
- State the 95% band with every rate. At 100 games it is ±.098, at 200
  it is ±.069, at 50 it is ±.13 — several past claims in this project
  were inside their own noise band and were not labelled as such.
- Record falsification tests with candidate findings. The flagship
  logged a blocking result at 4096 with the test that would kill it, and
  the test killed it at 6144. That is the standard.

---

## 7. Files you will want

| file | what |
|---|---|
| `rl/CURRICULUM-LADDER.md` | both branches, the design and why |
| `rl/bladder_decks.py` | builds your 7 decks, with the reasoning in the docstring |
| `rl/rung0_lane.sh` | the lane (shared with the white branch) |
| `rl/rung0_sweep.sh` | seeds 0-4, sequential |
| `rl/wladder_gate.sh` | load + stall + seat-balance gate, takes any deck list |
| `rl/POOLED-ANALYSIS.md` | what five prior work streams jointly established |
| `rl/PHASE12-XMAGE-AI.md` | CP7, what it is, and why it stays held out |
| `rl/CHECKPOINT-PHASE10.md` §5 | environment setup |
