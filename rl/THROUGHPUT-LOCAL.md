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
| conc4 cpu | 0.535 | 419 | 48.6 (64.6) | 84.2 % | 90.6 % (16 000 consults) | 43.1 / 4.47 ms | 8004 / 2099 / 5970 |
| conc8 cpu | 0.419 | 534 | 60.2 (98.0) | 83.7 % | 95.9 % (18 000 consults) | 107.9 / 4.57 ms | 9822 / 2169 / 7850 |
| conc12 cpu | 0.433 | 517 | 58.3 (94.3) | 84.1 % | 97.3 % (18 000 consults) | 165.5 / 4.55 ms | 9973 / 2139 / 8048 |

(Update share is Σupdate over rows 2–8 divided by the window, the same
rows the rate uses; an earlier draft of this table quoted 92.9 % for
conc4 by summing all 8 rows over the 7-row window.)

Decomposed (rows 2–8: update seconds from col 9, consults from col 4,
play time = window − Σupdate):

| arm | Σ consults stored | update ms per consult | play s | consults/s during play | play-only eps/s |
|---|---|---|---|---|---|
| conc4 cpu | 14 569 | 24.3 | 66 | 220 | 3.4 |
| conc8 cpu | 18 493 | 24.2 | 86 | 213 | 2.6 |
| conc12 cpu | 17 814 | 24.4 | 82 | 217 | 2.7 |

**conc12 outcome against the registered prediction:** play-phase
consults/s 217 (predicted ≈ 220 — confirmed); eps/s 0.433 (predicted
≤ 0.42 — 3 % over, inside what episode length alone moves between
runs); peak memory 9.97 GB (predicted ≥ 10.5 GB — **wrong**: server
RSS grew 200 MB from conc8 to conc12, so the per-session pending
buffers are not the RSS driver; the stacked PPO batch and allocator
retention are). No OOM, no swap. `conn: mode=train` = 48 = 12 × 4.

**Step-2 verdict.** conc4 is the best CPU arm (0.535 eps/s). conc8 and
conc12 are regressions of 22 % and 19 %, not flat. Three arms agree on
two invariants — 24.3 ± 0.1 ms of update per stored consult, and
213–220 consults/s of play — so the wall clock is (a) a single-threaded
PPO update taking 84 % of the window and (b) a play phase pinned at the
serialized inference rate. More game threads cannot move either.

**conc8 is a regression in eps/s (−22 %), and the decomposition says
why it is not noise in the update:** the update costs the same 24 ms
per stored consult on both arms; this run's episodes were longer (the
sampled trajectories diverge with thread interleaving, so the two arms
did not play the same games — batch win rate reached .31 at row 8 vs
.03), so it stored 27 % more consults and spent 27 % longer updating.
The play phase tells the real story: **~215 consults/s on both arms,
which is 1 / (4.5 ms held per consult)**. The serialized inference lock
is the ceiling of the play phase from conc4 onward; eight game threads
queue behind it (wait per consult 43 → 108 ms) and add nothing.

Prediction for conc12, registered before it ran: play ≈ 220 consults/s
again, eps/s ≤ 0.42, peak memory ≥ 10.5 GB (server RSS grows with
per-session pending buffers; 7.85 GB at conc8).

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

Fixed checkpoint `/tmp/rl_eq/init.pt` (the conc4 arm's init net,
md5 `2211cf4adde3…`, unchanged after every run — eval must not write
it), `--threads 1`, sequential driver, `-Drl.mode=eval`, seed 123456,
20 games vs D0 on B0Base, same persistent v6 JVM. Three runs: cpu, cpu
again, cuda. Files: `artifacts/throughput/gates/eq_probe_*.txt`.

| comparison | keys differing in `RL\|summary` |
|---|---|
| cpu vs cpu (determinism) | `entityConsults` only (19 960 vs 20 338) |
| cpu vs cuda | `entityConsults` only (19 960 vs 20 716) |

Every behaviour counter and rate — `wins/losses/draws`, `win_rate`,
`turns_per_ep`, `agent_consults_per_ep`, `agent_actions_per_ep`, all
`block*` and `attack*` counters — is **identical** on cpu and cuda.
The one differing key is explained, not waved away: `entityConsults`
is `StateEncoder.entityConsults`, a **static** field of the persistent
driver JVM, so it is cumulative over the JVM's lifetime; it rose by 378
per 20-game probe in launch order (cpu → cpu2 → cuda) and differs
between the two cpu runs by the same step. It is not a per-probe
behaviour count. Gate (b) passes: no argmax flipped in 20 games ×
~19 consults.

Timing seen in passing (not a gate): the probe ran at 5.96 / 5.99
games/s with the server on cpu and 4.99 games/s on cuda. Batch-1
inference is slower on the GPU (kernel-launch bound), which
pre-registers a prediction for step 4: the cuda arm's play phase will
be no faster than cpu, and any gain must come from the update.

## 7. Step 4 — best CPU arm on cuda

conc4, `R0_SRVEXTRA="--device cuda"`, everything else identical to the
conc4 cpu arm (same seed; trajectories still diverge, see §3.2).
`conn: mode=train` = 16 = 4 × 4, `R0_DONE`, `ck_eps=256`, no errors.

| arm | eps/s | window s | update s mean (max) | update ms / consult | update share | play consults/s | held / consult | peak host used / JVM / server MB | GPU MB |
|---|---|---|---|---|---|---|---|---|---|
| conc4 cpu | 0.535 | 419 | 48.6 (64.6) | 24.3 | 84 % | 220 | 4.47 ms | 8004 / 2099 / 5970 | — |
| conc4 cuda | **1.120** | 200 | 18.9 (26.9) | **10.5** | 66 % | 190 | 5.16 ms | 3925 / 2122 / **1978** | 2751 |

- **2.1× episodes/s**, from a **2.3× cheaper update** (10.5 vs 24.3 ms
  per stored consult). Part of the eps/s ratio is episode length — the
  cuda run stored 12 741 consults in rows 2–8 against 14 569 — so the
  per-consult update cost is the number to carry, not the 2.1×.
- **Play got slower, as pre-registered in §6:** 190 consults/s vs 220,
  held time 5.16 vs 4.47 ms. Batch-1 inference on the GPU is
  kernel-launch bound; the ~50 small kernels per consult cost more than
  the CPU's arithmetic.
- **Host memory fell from 6.0 GB to 2.0 GB** because the stacked PPO
  batch and its activations live on the GPU. This alone lifts the OOM
  ceiling the project has hit repeatedly (HANDOFF-STACK-TIMING.md §5,
  the 383/512 episode-mismatch story in the lane comments), and it is
  what would make conc8+ affordable — if inference were not serialized.
- The update is still 66 % of the window on cuda. The lock wait share
  (84 %) is still mostly threads parked behind `update()`.

### Is batched inference the next ceiling?

The condition set for describing it was: lock wait clearly the ceiling
at conc8+ on both devices. What the data says is more specific. The
**play phase** is pinned at the serialized inference rate on both
devices from conc4 onward (cpu 213–220 consults/s = 1/4.5 ms; cuda 190
= 1/5.2 ms); adding game threads only lengthens the queue. But the
**wall clock** is the update on both devices (84 % cpu, 66 % cuda), so
batching inference would today move at most the remaining third. It
becomes the ceiling only after the update is made cheaper or moved off
the consult lock. `rl/BATCHED-INFERENCE-PLAN.md` (written by another
session while this sweep ran; not part of this branch) already frames
it that way — queued behind this arm. What a batched path needs, in
one paragraph so this doc stands alone: a request queue in the server
that collects the consults arriving within a short window (or up to
`CONC` of them) and runs one padded forward pass over them — the v6
`EntityObs` already stacks, and `MAX_K`/`EMAX` already pad; per-session
LSTM hidden states would be gathered/scattered by session id; the
sample and `log_prob` are per-row and stay as they are; the
trajectory buffer append stays per-session. On cuda the batch amortizes
the launch overhead that made batch-1 slower than the CPU, so the
190 → N×190 gain is real there and mostly absent on cpu. The
equivalence gate for it is the one used here: sequential eval must be
identical, because a batch of one must equal today's path.

## 8. What these numbers do not support

- **n = 1 run per arm, 224 episodes each, seed 0.** Run-to-run
  variation was not measured. The one repeated arm (conc8, the
  contaminated run, §9) differed by 19 % in eps/s from the clean one,
  but that pair is not a variance estimate because the runs differed
  in kind. Rankings that rest on 3 % (conc8 vs conc12) are not rankings.
- **Untrained-net regime.** Episodes are 13–15 turns and ~20 agent
  consults; the update share, the consults/s ceiling and the memory
  figures will all move as the net learns to play longer games (more
  consults per episode raises the update cost per episode linearly,
  and lengthens the play phase). The 24.3 → 10.5 ms per consult update
  cost is the number most likely to transfer.
- **Trajectories are not shared across arms** (§3.2, thread
  interleaving and, for cuda, a different sampler stream). Episode
  length differs between arms and enters eps/s directly. Per-consult
  numbers are comparable; eps/s only roughly.
- **JIT warm-up is excluded, not measured.** Row 1 is skipped; the
  first 32 episodes of each arm are not in any rate.
- **Batteries are 4 games** and carry no information about play. No
  win rate in this doc is a result; none is reported as one.
- **Gate (b) is 20 games** of a fixed untrained net (~380 consults).
  It shows no argmax flip in those consults; it does not bound the
  rate of float32 near-tie flips for a trained net over thousands of
  games. Before a cuda-trained checkpoint is compared against a
  cpu-trained one on any behaviour counter, repeat the gate on that
  checkpoint.
- The lock-stats `wait_share` conflates update stalls with inference
  contention (§2) and should not be quoted alone.

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

## 10. Step 0 — cheap update levers (pre-registered before running)

The cuda arm left the update at 66 % of the window (§7). Before batched
inference (§11) two levers that change **no algorithm**: same `EPOCHS`,
`ep_batch`, `tbptt`, `LR`, same loss, same data. Both are bounded to
half a day of machine time.

### 10.0 Pre-registration

- **Neither lever can move a behaviour counter or a win rate at eval on
  a fixed checkpoint.** Eval never calls `update()`. If an eval counter
  differs between a server with and without `--update-threads`, that is
  a bug.
- **Neither lever changes what the update computes.** The weights after
  one update from a fixed buffer and fixed seed must agree across
  thread counts to within `1e-6` (max |Δ| over all parameters). A
  larger difference is a float reduction-order effect and is reported
  as a number, not rounded to "identical".
- **0a cannot help the cuda arm** (the update runs on the GPU there; the
  Python loop is the CPU work and is single-threaded by nature). It can
  only shorten the CPU update. Prediction: conc4 cpu update ms per
  stored consult falls from 24.3; the play phase (~220 consults/s) does
  not move because inference threads are restored on exit.
- **0b changes nothing**; it measures. Verdict criterion written in
  advance: the update is *launch-bound* if the number of CUDA kernel
  launches per stored consult is in the hundreds and the top ops by
  CUDA time are small elementwise/`copy_`/`index` kernels with
  mean duration well under 20 µs; *compute-bound* if the top ops are
  GEMM/attention kernels with GPU busy time near the wall time.
- Throughput rows use the §5 protocol (B0Base/B0Twin v6, budget 256,
  `R0_EVERY=256`, `R0_EVAL_G=4`, `R0_CP7_G=0`, rows 2–8, seed 0, one
  run each). n = 1 per arm; the §8 caveats apply unchanged.

### 10a. `--update-threads N`

`policy_server.py`: `--update-threads N` (default 0 = unchanged). On
entry to `update()` the server calls `torch.set_num_threads(N)` and on
exit restores the count it found (the inference count,
`RL_TORCH_THREADS`). No inference runs during `update()` — every
handler thread is parked on the consult lock — so the oversubscription
argument for `RL_TORCH_THREADS=1` does not apply inside it.

### 10b. Profile of the cuda update

`rl/update_profile.py` runs one `update()` on a recorded buffer (the
first update of a lane, dumped by `RL_DUMP_BUF=<path>`) under
`torch.profiler`, and reports top-10 ops by CUDA time and by CPU time
plus kernel launches per stored consult. Finding and candidate fix go
below; **the update is not restructured in this step.**

### 10c. Results

(filled in after the runs)

## 12. Recommendation (written after §7; §10–§11 test items 2 and 3)

1. Run training with `--device cuda` (`R0_SRVEXTRA="--device cuda"` on
   the lane): 2.3× cheaper update, 3× less host memory, eval-identical.
2. Next lever is the update, not the game threads: it is 66 % of the
   window on cuda and runs on one torch thread under the consult lock.
   Two cheap experiments before any architecture work: raise torch
   threads for the duration of `update()` on cpu (no inference runs
   then, so the oversubscription argument for `RL_TORCH_THREADS=1` does
   not apply), and measure `EPOCHS`/`ep_batch` sensitivity on cuda.
3. Only then batched inference (§7), which lifts the play phase from
   190 consults/s and makes conc8+ worth the memory it no longer costs.
