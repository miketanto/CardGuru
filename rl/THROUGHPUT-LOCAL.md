# Training throughput on the local machine — CPU concurrency sweep and a `--device cuda` server (2026-09-10)

Branch `claude/gpu-throughput`. Companion to `SETUP-WSL-LOCAL.md`.
Raw files: `rl/artifacts/throughput/`.

## 0. Question

How many training episodes per second does the rung-0 lane deliver on
this machine, where does the wall clock go (engine, PPO update, lock
contention), and does moving the policy server to the RTX 3060 change
that without changing what the net does?

## 1. Machine

Ryzen 7 5800X (16 threads), 16 GB RAM, RTX 3060 12 GB. WSL2 Ubuntu
capped at 12 GB RAM + 8 GB swap (`.wslconfig`). Temurin 21, torch
2.7.1+cu126 (`torch.cuda.is_available()` True), system python 3.10.
Driver JVM `-Xmx4500m`. `RL_TORCH_THREADS=1` for every arm (the lane's
default; POOLED-ANALYSIS.md §3).

## 2. Method

- Lane: `rung0_lane.sh B0Base B0Twin 256 0`, encoder v6 (`entattn`,
  gdim 16 / edim 48 / emax 96, `--max-k 96`), opponent D0, mirror deck.
- Budget 256 training episodes per arm, `R0_EVERY=256 R0_CHUNK=64
  R0_EVAL_G=4 R0_CP7_G=0` so the two batteries (4 games each) are
  negligible and never enter the rate.
- `UPDATE_EPISODES=32`, so each arm writes 8 `train.csv` rows.
  **Episodes/s = (eps_row8 − eps_row1) / (t_row8 − t_row1)**: 224
  episodes, measured after the first update so the driver JVM's JIT
  warm-up and the first-chunk startup are excluded. Rows are stamped at
  the end of each update, so the window contains 7 updates and the 224
  episodes of play that fed them.
- Update seconds: new `train.csv` col 9 (commit f7836df), mean and max
  over the 8 updates.
- Lock timing: `RL_LOCK_STATS=1`; the server prints a cumulative
  `RLLOCK|` line every 2000 consults. The last line of the training
  server's lifetime is reported (preserved in `server_all.log`, commit
  d28448c). **Caveat:** `update()` runs under the same lock as
  inference, so `wait_s` includes every game thread stalled behind a
  PPO update, not only inference contention. The update share of wall
  clock is reported beside it for that reason.
- Memory: `free -m` used, JVM RSS and server RSS sampled every 5 s
  (`mem.log`), peak reported.
- One run per arm, seed 0, fresh driver JVM per arm (the lane kills it
  at start; encoder flags are class-init constants).

## 3. Pre-registration

Written before any cuda run.

1. `--device` moves where tensors live. It **cannot** move any behaviour
   counter or win rate of a deterministic eval probe (argmax policy,
   fixed checkpoint, fixed seed, sequential driver): `wins`, `blocks*`,
   `attacks*`, `turns_per_ep`, `consults_per_ep` must match the cpu run
   exactly. A difference is a bug — with one admissible exception, which
   must be shown rather than assumed: a float32 near-tie in the logits
   whose argmax flips between the two BLAS paths. If counters differ,
   the difference is explained by locating the first diverging consult
   or the change is not accepted.
2. Training on cuda is **not** a bitwise replay of cpu training:
   `Categorical.sample` draws from a different generator stream, so
   sampled trajectories, and therefore every later number, diverge. The
   cuda training arm is compared on throughput only, never on
   `batch_win_rate` or any battery row.
3. Throughput claims are single runs of 224 episodes each; the sweep can
   rank arms whose rates differ by more than the run-to-run noise it
   cannot itself measure. It is not a result about learning.
4. `entattn_check.py` must still pass on cpu after the change.

## 4. Step 1 — instrumentation

`update()` stamps its start; `_finish_update` appends `update_s=` to the
`TRAIN|` line and a 9th column to `train.csv`. Readers checked: the
`chunk_*.sh` lanes only count rows, `ev_probe.sh` reads columns 2–8 by
position; nothing reads by header. Backward compatible.

## 5. Step 2 — CPU concurrency sweep

Rates over 224 episodes (rows 1–8 of `train.csv`); update seconds over
8 updates; lock line = last cumulative `RLLOCK|` of the training
server; memory = peak of 5 s samples over the whole arm (JVM start,
batteries included). Single run each, seed 0.

| arm | eps/s | window s | update s mean (max) | update share of window | lock wait share | wait / held per consult | peak used / JVM / server MB |
|---|---|---|---|---|---|---|---|
| conc4 cpu | 0.535 | 419 | 48.6 (64.6) | 92.9 % | 90.6 % (16 000 consults) | 43.1 / 4.47 ms | 8004 / 2099 / 5970 |

**The PPO update is the wall clock at this stage of training.** With an
untrained net the games are short (13–14 turns, ~20 agent consults, the
untrained eval probe plays 2.1 games/s sequentially), so the 32
episodes between two updates are played in 5–10 s at conc4 and the
update that follows takes 35–65 s. The update cost is linear in steps:
36.4 s for 1459 steps, 64.6 s for 2611 steps, i.e. ~25 ms per stored
consult, for the true-BPTT recurrent update (`EPOCHS` passes, `tbptt`
64, `ep_batch` 8) on **one** torch thread — `RL_TORCH_THREADS=1` is
set for inference and never raised for the update, during which no
inference runs.

Consequence for the lock numbers: 690 s of cumulative wait against 72 s
held is not inference contention. The four game threads sit on the lock
for the whole update (8 × 48.6 s × up to 3 waiting threads ≈ 690 s
accounts for essentially all of it). Inference itself is 4.5 ms held
per consult at conc4 — the same 4.5 ms Phase 12 measured.

Pre-registration for the rest of the sweep, written after conc4 and
before conc8: raising `R0_CONC` cannot shorten the update, so it can at
best compress the 7–10 % of the window that is play. **Episodes/s at
conc8 and conc12 is predicted to stay within ~10 % of 0.535** unless
memory pressure or oversubscription makes it worse. The batteries at 0
and 256 in this arm ran the `--device`-capable server on the default
device after the edit landed (the training server had loaded the
pre-edit file); both completed, `ck_eps=256`.

## 6. Step 3 — `--device` flag and equivalence gate

Implementation (`policy_server.py`): module global `DEVICE`, set from
`--device {cpu,cuda}` (default cpu). The net and the oracle critic are
moved to the device before their Adam optimizers are built, so
optimizer state is created there; `torch.load` uses `map_location=cpu`
and `load_state_dict` copies into the device params (Adam's
`load_state_dict` moves its state to the params' device). Per-consult
tensors are built on CPU from the wire lists exactly as before, the
CPU copies go into the trajectory buffer, and device copies go to the
net; the recurrent hidden state stays on the device between consults
and is copied to CPU for the buffer. `update()` stacks the buffer on
CPU, runs GAE and the explained-variance bookkeeping on CPU (a python
loop over `values`), then moves `states/cands/masks/actions/old_logp/
adv/ret` to the device in one bulk move. `initial_hidden` allocates on
the net's device. Checkpoints are written as CPU tensors (`_to_cpu`),
so `p10_init_net.py`, the lane's `torch.load(..., map_location='cpu')`
and every probe script stay device-agnostic. `EntityObs` gained a
`.to(device)`. On `--device cpu` every `.to` is a no-op returning the
same tensor.

### Gate (a): `entattn_check.py` on cpu

22/23 checks pass on the new build. The one failure, `R0-NOBIAS`
(`max|biased − plain| = 3.052e-05` against a 1e-6 tolerance), is
**identical on the unmodified `main` server** run under the same
interpreter (`/tmp/rl_eq/base`, same 3.052e-05): it is a property of
torch 2.7.1's CPU attention kernel — an all-zero additive attention
bias and no bias take different fused paths — not of this change. The
check was written against the container's torch; it needs a tolerance
of ~1e-4 on this build, which is a separate one-line fix I have not
made so that the numbers in this doc are from an unmodified check.

### Gate (b): eval equivalence cpu vs cuda

(filled in below)

## 7. Step 4 — best CPU arm on cuda

(filled in below)

## 8. What these numbers do not support

(filled in below)

## 9. Gotchas found while running this

- **A discarded conc8 run.** The first conc8 arm was launched twice, 13 s
  apart (two `TP_ARM_START` stamps in the two outputs; the second
  `rm -rf`'d the first's directory). Two lanes then drove one port and
  one JVM: the driver log shows 3 + 8 + 3 jobs where the lane can only
  issue 3 + 4 + 3, three of the eight training jobs died in ~1 s when
  the other lane's `stop_server` killed the policy server under them,
  and the server counted 320 episodes for a lane budget of 256. Its
  numbers (0.497 eps/s, 11.2 GB peak, 95.8 % wait share) are
  contaminated and are not reported. The arm script now holds an
  `flock` so a second instance refuses to start, and the arm is re-run.
  The tell for this failure in any lane: `conn: mode=train` lines in
  `server_all.log` not equal to `CONC × chunks`.
- `RLLOCK|` wait share is not an inference-contention number while
  `update()` runs under the consult lock (§5).
- `entattn_check.py` `R0-NOBIAS` fails at 3.05e-05 on torch 2.7.1 CPU
  for the unmodified server too (§6).
- Driving WSL from Git Bash: `$VAR` inside `bash -c '...'` was expanded
  by MSYS once here and ran `mkdir` with no operand; scripts only.
