# v6 baseline freeze (v7 plan §2, 0e) — 2026-09-11

Tag `v6-baseline` = commit 9ad2a1a, the last `main` commit before any v7
code. `rl/policy_server.py` and `rl/entattn_check.py` are byte-identical
between that tag and this branch (`git diff v6-baseline HEAD -- rl/policy_server.py rl/entattn_check.py` is empty).
Environment: WSL2 Ubuntu, Python 3.10, torch 2.7.1+cu126, RTX 3060.

## entattn_check.py (CPU, `rl/artifacts/v7/entattn_check.out`)

`ENTATTN|checks=23|failures=1|4.9s` — 22 pass; one **pre-existing**
failure on the v6 code as it stands:

```
CHECK|R0-NOBIAS  |FAIL|96 entities, no padding: max|biased - plain| = 3.052e-05
```

The check asserts that the relation-biased attention with the no-edge
bias row equals plain attention to 1e-6 at 96 entities; on this
machine's torch build the difference is 3.05e-5 (float32 accumulation
order over 96 tokens; the tolerance was set on the cloud build). It is
recorded here as the baseline state, not fixed on this branch: Lane C's
gate 4a ("`entattn_check.py` still bit-identical") is to be read as
"the same 23 lines with the same results as this file", and the
tolerance question belongs to whoever next touches `entattn_check.py`
(one line, `d_full < 1e-6` at line 259).

## consult_cost.py --device cuda (`rl/artifacts/v7/consult_cost_cuda.out`)

```
CONSULT|device=cuda|entities=30|k=10|wire_bytes=16701|json_ms=0.15|obs_ms=24.85|fwd1_ms=15.54|fwd8_ms=15.73|fwd8_per_row_ms=1.97|sample_ms=41.57
```

**Caveat:** measured while the overnight embedder sweep held the GPU at
99 % utilisation and 11.8 GB; `obs_ms`, `fwd*` and `sample_ms` are
contaminated. Rerun on an idle GPU before using these as the 5d budget
reference. `wire_bytes` and `json_ms` are valid as they stand.

## 100-game rung-0 smoke (a smoke, not a level)

Checkpoint: `/tmp/rl_smoke_lane/agent.pt` (arch entattn, dims cdim 94 /
gdim 16 / edim 48 / rtypes 6), inference only; opponent D0 heuristic;
W0Base mirror; `-Drl.encoderV=6 -Drl.blockAudit=true -Drl.attackAudit=true`;
seed 900000; 100 games. Script: the battery `probe` of `rung0_lane.sh`,
run standalone. Result recorded below when the run ends
(`rl/artifacts/v7/smoke.log`, `smoke_probe_D0.txt`).

RESULT (08:26, `rl/artifacts/v7/smoke_probe_D0.txt`):

```
RL|summary|episodes=100|wins=0|losses=100|draws=0|stalls=0|win_rate=0.0000|games_per_sec=3.367|agent_consults_per_ep=19.5|agent_windows_per_ep=96.0|agent_actions_per_ep=0.0|turns_per_ep=10.9
RL|ipc|round_trips=1947|avg_rtt_us=6257.8|ipc_sec_total=12.2
```

What it shows: the v6 pipeline runs end to end on this machine (driver
JVM, entattn policy server, 100 games, 3.4 games/s, 6.3 ms IPC round
trip). What it does not show: a policy. The checkpoint is a 64-episode
smoke-lane net that never acted (`agent_actions_per_ep=0.0`), hence
0/100 — a property of that checkpoint, not of the pipeline. A scan of
every `.pt` on this machine (`rl/artifacts/rung0`, `/tmp/rl_*`) found no
entattn checkpoint beyond 256 episodes (the throughput runs); the
2,111-episode rung-0 checkpoints are `lstmattn` (encoder v4/v5) and do
not fit the v6 wire. A trained v6 checkpoint would have to
be restored from the cloud artifacts (`rl/restore_artifacts.sh` lists
none for entattn) or produced by a rung-0 lane run; recorded as a gap.

Gotchas found: the persistent driver JVM needs `java` on PATH, which
lives in `~/.profile` (start it from a login shell: `bash -lc
"bash rl/driver_server.sh start 7910 ..."`); `RL_AUTOSTART=1` from a
non-login shell fails silently as `RL_DRIVER|server_start_failed`.
