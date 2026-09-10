# Batched inference for the policy server — a test-driven plan

Status: **queued behind the `--device cuda` arm** in `THROUGHPUT-LOCAL.md`.
Do not start step 3 until that arm's equivalence gate has passed and
its update-duration row is in the table; the value of batching depends
on the update no longer being 90 % of the window.

## 0. Why, in numbers

`THROUGHPUT-LOCAL.md` §5 (conc4 and conc8, CPU, untrained net):

| what | measured |
|---|---|
| PPO update per 32 episodes | 48.6 s mean at conc4, 60.2 s at conc8 |
| update share of wall clock | 90–93 % |
| play for 32 episodes at conc4 | 5–10 s |
| inference per consult, held under the lock | 4.5 ms, unchanged from Phase 12 |
| consults per game (untrained, B0Base) | ~20 |

Inference is 30–40 % of *play* (`ENGINE-REWRITE-FEASIBILITY.md` §5).
Today every consult is a batch-of-one forward pass serialised by one
`threading.Lock` (`policy_server.py:1217`, `handle()` at `:1098`), so
adding concurrent games adds waiting, not throughput. Batching turns N
waiting consults into one forward pass whose cost is nearly flat in N.

**What batching cannot fix, stated first:** the update still holds the
lock while it runs. Batching helps only once the update is short (the
cuda arm) — which is why this is queued, not started.

## 1. Pre-registration — what this change cannot move

Written before any code. A move on any of these is a bug to find, not a
result.

1. **No behaviour counter and no win rate changes at eval on a fixed
   checkpoint, sequential.** With `RL_CONC` unset there is one consult
   in flight at a time, so a batch is always size 1 and the numerics
   must be bit-identical to the unbatched path on CPU. Gate G2 below.
2. **Update duration does not change.** `update()` is untouched.
3. **Stored trajectories are identical in content** for the same
   decisions: the buffer stores `(store, c_cpu, m_cpu, a, logp, v, …)`
   per request, not per batch. Gate G1 checks `logp`/`v` agree within
   tolerance between batched and single forward.
4. **Throughput at conc4 may not improve.** With ≤4 games there are
   rarely enough simultaneous consults to fill a batch; the queue wait
   (`--batch-wait-ms`) is pure added latency there. The prediction is:
   flat at conc4, gain at conc8+, on cuda. If conc4 *improves*, explain
   why before believing it.
5. **`--batch-max 1` (the default) must be the existing code path**, not
   a batched path with N=1. Behaviour of every current lane is unchanged
   until a lane opts in.

## 2. Design

### 2a. Shape of the change

One new object, `InferenceBatcher`, owned by the trainer when
`--batch-max > 1`:

```
handler thread (one per connection, unchanged):
    req = Request(session, s, c, m, sample, phi, ent_store, oracle_rows)
    batcher.submit(req)          # enqueue + wait on req.done (Event)
    -> req.logits, req.value, req.hidden_out set by the batcher
    the rest of act() (sampling, buffer append) runs per-request as now

batcher thread:
    loop:
        first = queue.get()                      # block
        batch = [first] + drain(queue, until len == batch_max
                                        or batch_wait_ms elapsed)
        with lock:                               # same lock update() takes
            S  = cat(r.s for r in batch)         # (B, ...) EntityObs or state
            C  = cat(r.c ...)  (B, MAX_K, cdim); M = cat(r.m ...) (B, MAX_K)
            H  = stack per-session hidden, initial_hidden(1) where None
                 -> (h, c) each (B, d)          # policy_server.py:131
            logits, value, H2 = net(S, C, M, H)
        scatter row i -> batch[i]; write session.hidden = H2[i]; set done
```

Facts that make this small:

- `initial_hidden(batch)` already returns `(B, d)` tensors
  (`policy_server.py:131`); per-session hidden is `(1, d)`, so stacking
  is `torch.cat` along dim 0 and scattering is row indexing.
- `EntityObs` (`:167`) is already padded to `EMAX` entities and `MAX_K`
  candidates per row (`_entity_obs`, `:499`; `act()`, `:620–626`), so a
  batch is a plain `cat` — no ragged handling.
- The network's `forward` already takes a batch dimension with a mask;
  `update()` calls it with B>1 today (`:839`, `:893`). No model change.
- A connection issues one consult at a time, so a session never has two
  requests in one batch; no reordering logic is needed.

### 2b. Flags

| flag | default | meaning |
|---|---|---|
| `--batch-max N` | 1 | 1 = existing path, untouched. N>1 enables the batcher |
| `--batch-wait-ms T` | 1.0 | max time the batcher waits for more requests after the first |

Lane pass-through via `R0_SRVEXTRA` (added in `d28448c`).

### 2c. Instrumentation (before optimisation, per the project rule)

Reported on the `stats` message and at shutdown next to `RLLOCK|`
(`:1005`): `RLBATCH|batches=…|consults=…|mean_b=…|p50_b=…|max_b=…|`
`queue_wait_ms_mean=…|forward_ms_mean=…`. A batch-size histogram is the
number that tells us whether concurrency is actually producing
simultaneous consults; without it a flat result is uninterpretable.

## 3. Tests — written before the batcher, in this order

New file `rl/batch_check.py`, modelled on `rl/entattn_check.py` (no
engine, ~seconds, `check(name, ok, detail)` rows, exit 1 on any fail).
`entattn_check.py` must keep passing unchanged.

| id | test | passes when |
|---|---|---|
| T1 | **collate/scatter round-trip.** Build 1..B random requests with varying `k` (1..MAX_K) and entity counts (1..EMAX), random per-session hidden or None. Batched forward vs each single forward. | `logits[m]` and `value` agree to `atol=1e-5` on CPU; argmax identical for every row; padding rows of `logits` never selected |
| T2 | **recurrent state isolation.** Two sessions, alternating consults, batched together; compare each session's hidden trajectory with the same sessions run unbatched. | per-session hidden equal (`atol=1e-5`) after every step; swapping the batch order changes nothing |
| T3 | **queue semantics.** Fake net with a sleep; submit 1 request → returns after ≤ wait; submit `batch_max` at once → one forward; submit `batch_max+1` → two forwards; a request never waits for a *later* batch. | asserted counts and latencies |
| T4 | **`--batch-max 1` is the old path.** Monkeypatch-count calls to `InferenceBatcher`; run `act()` with default flags. | zero calls |
| T5 | **device parity of T1** with `--device cuda` (skipped with a clear message when cuda is absent). | `atol=1e-4`; count argmax flips and *report the count* — the tolerance question is decided by the number, not assumed |
| T6 | **error surfacing.** One malformed request in a batch (wrong `gdim`). | only that request's connection gets the error; the others complete |

Engine gates, run after the unit tests pass:

| id | gate | passes when |
|---|---|---|
| G1 | `python3 rl/entattn_check.py` and `python3 rl/batch_check.py` | all rows ok |
| G2 | **sequential equivalence.** Init checkpoint from a lane, `-Drl.mode=eval`, 20 games, `RL_CONC` unset, same seed: server with `--batch-max 1` vs `--batch-max 8 --device cpu`. | `RL|summary` counters identical (pre-registration §1.1) |
| G3 | **concurrent sanity.** Same checkpoint, `RL_CONC=8`, 64 eval games, batched vs unbatched. Game order is nondeterministic at conc, so counters may differ; compare win rate and consults/game as Wilson intervals, and read `RLBATCH|` mean batch size. | intervals overlap; mean batch size > 1 (else the batcher never engaged and the throughput arm is void) |

## 4. Throughput arms — same protocol as `THROUGHPUT-LOCAL.md`

B0Base/B0Twin, v6 encoder, budget 256, `R0_EVERY=256`, `R0_EVAL_G=4`,
`R0_CP7_G=0`, rates from `train.csv` rows 2–8, `--device cuda` (the
update fix is a precondition; on CPU the update masks everything).

| arm | R0_CONC | batch-max | prediction (§1.4) |
|---|---|---|---|
| A | 4 | 1 | baseline from the cuda arm |
| B | 4 | 8 | flat |
| C | 8 | 8 | gain |
| D | 12 | 12 | gain, if memory allows (conc8 CPU peaked at 9.8 GB; cuda moves update tensors off RAM — verify) |
| E | 8 | 8, `--batch-wait-ms 0.25` | sensitivity of the wait knob |

Report: eps/s, update s, `RLBATCH|` mean and p50 batch size, queue wait,
peak memory. One run each, seed 0, and say so.

## 5. Order of work, with stop conditions

1. Wait for the cuda arm. If its equivalence gate fails, stop: fix that first.
2. Write `rl/batch_check.py` T1–T6 against a stub `InferenceBatcher`
   interface; all must *fail* for the right reason (not import errors).
3. Implement `InferenceBatcher` + flags + `RLBATCH|` stats. T1–T6 pass.
4. G1, G2. If G2 shows any counter differing at batch size 1: stop, it is a bug.
5. G3. If mean batch size ≤ 1.2 at conc8: the batcher is not engaging;
   instrument before running arms.
6. Arms A–E. Write results into `THROUGHPUT-LOCAL.md` §9 (new section),
   copy `train.csv`s to `rl/artifacts/throughput/`.
7. Commit after each numbered step. Branch `claude/gpu-throughput`
   (continues the throughput work) unless that branch has been merged,
   then `claude/batched-inference` from main.

## 6. Working method — keep the context small

The codebase graph for this repo is indexed in codebase-memory-mcp
(project `C-Users-sutanto4-Documents-CardGuru`; XMage core is
`C-Users-sutanto4-xmage-pin`). Use it instead of reading files:

```
CBM=C:/Users/sutanto4/tools/codebase-memory-mcp/codebase-memory-mcp.exe
$CBM cli --json search_graph --project C-Users-sutanto4-Documents-CardGuru \
    --query "act hidden session"            # find symbols
$CBM cli --json get_code_snippet --project C-Users-sutanto4-Documents-CardGuru \
    --qualified-name policy_server.Trainer.act   # read one function, not the file
$CBM cli --json trace_path ...              # who calls what
```

Filter its stderr with `2>&1 | grep -v '^level=\|^hint:'`. Re-index
after editing (`cli index_repository --repo_path=C:/Users/sutanto4/Documents/CardGuru`,
~seconds). When the MCP server is loaded in a session the same tools
exist as `mcp__codebase-memory-mcp__*` and the installed hook augments
Grep/Glob automatically. Read a whole file only when the graph cannot
answer; `policy_server.py` is 1,300 lines and a full read is a
meaningful fraction of a window.

## 7. What this plan does not cover

- **Asynchronous updates** (act on a stale weight snapshot while
  `update()` runs). Removes the stall entirely but makes PPO slightly
  off-policy. An algorithm decision; out of scope here, and the cuda
  arm's update duration decides whether it is worth raising.
- **Cross-process batching** (several driver JVMs, one server). Not
  needed until one JVM's `RL_CONC` ceiling is the limit.
- **Eval batteries.** They stay sequential by design (reproducible
  ratings); batching is a training-lane feature.
