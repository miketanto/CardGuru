# Handoff — the encoder is not the constraint, and now neither is exploration

Successor to `HANDOFF-STACK-TIMING.md`. Read this, then
`TIMING-GATE-RESULT.md`, then `B1-TIMING-AB.md`, then
`ORACLE-GUIDING.md`.

That handoff asked three questions. All three are answered, and the
answers move the project's bottleneck one layer up — to **credit
assignment**, which is where an independent codebase working on the same
problem (Talor-A's `anvil`, Forge-based, V-trace self-play from a BC
init) arrived from the other direction.

## 0. What is settled

**§2a — the collision is real, the stop condition was wrong.**
Minimum within-card cross-step distance **0.000000**; `Cruel Cut` emits
one candidate row across all 20 steps it is offered in. But §2a's
inference — "no amount of training can learn the difference" — does not
follow: v6's globals carry a dedicated `DECLARE_ATTACKERS` bucket, the
state token is `glob_in(g) + pool(entities)`, and candidates attend to
it, so the step moves the cast-vs-hold margin at every seed. A timing
decision **is** representable; it just cannot be per-candidate.

**§2b — instant speed buys nothing, and the rung cannot say more.**
`.595` vs `.585` pooled n=200, **z=−0.20, p=0.84**. The useful half is
beside it: `B1Narrow` cast its removal 86 times and `B1Fast` zero, and
they finished level — **the removal has no measurable win-rate value on
this rung even when used.** `B1Fast` vs `B1Narrow` is therefore not a
powered test of timing, and the same objection applies to the white
branch's `W3 → W4` pair.

**The mechanism, measured end to end.**

| ck_1024, 100 games | Cruel Cut (instant) | Defeat (sorcery) |
|---|---|---|
| on the menu | 5,504 | 470 |
| **chosen** | **0 (0.00%)** | **92 (19.6%)** |
| chose `PASS` there | 4,949 | **0** |

An instant is legal in ~20 step contexts and a sorcery only in a main
phase with an empty stack, so **legality does the timing work for the
sorcery and nothing does it for the instant.** The identical
timing-blind row arrives overwhelmingly in pass-contexts, the policy
learns "this vector → do not act" (right 90% of the time it sees it),
and argmax converges on never casting.

**Exploration is not the failure.** Served sampled, the same checkpoint
casts Cruel Cut **87 times per 100 games** across nine steps almost
uniformly — 10 of 87 on the opponent's turn. The behaviour exists with
~zero mass at the mode, and the casts have **no aim**. (Rate contaminated
— see `B1-TIMING-AB.md` §7a — but the qualitative split is not in
doubt.)

## 1. The elimination ledger — do not re-run these

CardGuru:

| lever | verdict | doc |
|---|---|---|
| card encoder → zero-shot transfer | null, 2 scales, control transfers as well | `PHASE8-TRANSFER.md` |
| v6 entity tokens + relations | no win-rate gain 1024→2048 | `DIMIR-V6-2K-RESULT.md` |
| imitation from a search teacher | .36–.40 vs a ~.50 teacher | `PHASE5-VERDICT.md` C1 |
| **hand-written potential shaping** | **NULL, shaped == unshaped** | `PHASE5-VERDICT.md` C2a |
| DAgger, on-policy labels | **exactly 0.000** | `PHASE5-VERDICT.md` C3 |
| exploration | not the failure | `TIMING-GATE-RESULT.md` §4c |

`anvil`, independently, at much larger scale:

| lever | verdict |
|---|---|
| BC → V-trace self-play | **+6.69pp ± 1.55 over BC** — the loop works |
| ...vs the heuristic | parity (+1.21 ± 1.10) |
| cycling the loop unmodified | −0.58pp — "one-shot verdict" (ADR-0035) |
| best-ever curation + composition | **TIE** 0.5199 vs 0.5316 (ADR-0048) |
| representation (5 probes) | "never the binding constraint" (ADR-0050) |
| **its own diagnosis** | **learning-signal density** (ADR-0049) |

anvil's audit found *"the behavior exists; no credit reaches its
timing"* — hold-then-cast abundant in exploration, **flat across 20
iterations**, and 46% of changed cast-decisions going cast→pass. Two
codebases, one failure.

## 2. Why the next lever is not more shaping

With terminal-only reward and GAE(λ=0.95), the TD residual at every
non-terminal consult is `δ_t = γV(s_{t+1}) − V(s_t)` — **identically the
potential-based shaping term with Φ = V**. The dense credit path is not
missing. It exists, and the critic feeds it. Hand-writing a Φ adds a
second term of the same functional form with a *worse*, human-authored
potential — which is what C2a measured as null.

So the question is not "add dense signal" but **"is the dense signal
already there any good?"** — and nobody has measured it. That is
`value_ev` (§3).

## 3. What is running / what is next

- **Oracle guiding** (`ORACLE-GUIDING.md`) — an asymmetric critic that
  sees the opponent's hand at training time only. Built, gated (3/3),
  A/B running. Readout is explained variance, **not** a win rate.
- **Rollout-delta value targets** — anvil's ranked #1 and the bias-free
  form of dense credit: force act/hold branches with paired seeds and
  use the empirical win-rate delta. **Their `forge` fork already
  implements the harness** (`-forcebranch`, `forbid_decline`,
  per-fork-point `w_act`/`w_hold`). Read it before writing our own.
- **Expert iteration, not one-shot BC.** Phase 5 distilled a *fixed*
  1-ply searcher capped at ~.50, so cloning it could never exceed .50 —
  and didn't. AlphaZero's recipe re-runs the search with the *current*
  net as evaluator every iteration, so the teacher improves with the
  student. That is also why anvil says tier-3 search "needs a
  ranking-capable critic upstream" — and why a better value function is
  a prerequisite, not an alternative.
- **A rung whose spells matter.** Before any of the above is scored on
  win rate, build or find a deck where the non-creature cards carry
  measurable win-rate value. Cheap test, no training: heuristic vs
  heuristic, removal deck against the same deck with vanilla creatures
  in those slots. `CURRICULUM-LADDER.md` designed B0Base so targets
  would be *legal*; it never checked they would be *valuable*.

## 4. Gotchas this session paid for

- **A probe can train its subject.** `training=(mode == "train")` was
  independent of `--lr`, and `_finish_update` calls `save()`. A sampled
  probe took `/tmp/rl_b1fast/ck_1024.pt` from 1024 to 1129 episodes
  *while measuring it*. Fixed with `--frozen`; `cand_census.sh` also
  serves a `mktemp` copy now. **Prefer `--frozen` for every probe.**
- **`1 − Var(ret − V)/Var(ret)` is circular.** `ret ≡ gae + values`, so
  that ratio measures nothing about the critic. Score against the
  Monte-Carlo return.
- **`EpisodeRunner` gates counter blocks on `> 0`** — `instCasts` and the
  whole `tgt*` family are **absent, not zero**, when the policy never
  casts. Absent means zero; it does not mean broken.
- **The driver JVM is persistent.** Waiting for `RLDriverServer` to exit
  is waiting forever; check the job, not the server.
- **`/tmp/rl_*` dies with the container**, and this is the second time
  it has cost a session — `B1Fast ck_1086` was already gone when this
  one started. Checkpoints a later phase must re-probe belong in
  `rl/artifacts/`.
- **`/home/user/mage` may not exist.** `rl/setup_engine.sh` rebuilds it
  from the pin; `rl/sync_engine_src.sh` is the Mage.Tests-only recompile.
  `download.pytorch.org` is blocked by the egress proxy; PyPI is not.

## 5. Ground rules

`HANDOFF-ATTACK-JOINT.md` §6 still governs, plus the two this session
added the hard way: **a probe must not be able to write what it
measures**, and **an instrument gets a validity check before its first
number is quoted** — the circular EV read 0.7664 and looked healthy.
