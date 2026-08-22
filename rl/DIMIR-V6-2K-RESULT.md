# Dimir v6 to 2048 episodes — the win rate stopped, and the behaviour
# counters say why

Continuation of `ENCODER-V6-RESULT.md`. That doc ends with the v6
encoder landed and gated. This one is what happened when the resulting
policy was trained four times longer on a real constructed deck, and it
is mostly a negative result with two positive findings hiding in the
per-decision counters.

Arm: `entattn`, `BenchDimir` mirror, heuristic opponent, PPO with
terminal-only reward, 1024 → 2048 episodes. Batteries at 1024 (anchor),
1536, 2048, 100 games per probe.

## 0. The measurement bug that comes first

**Every earlier probe in this line of work was 10 games, and 10 games
was not enough to state a level.** Re-probing the *same* `ck_1024`
weights at 100 games moved the numbers substantially:

| arm | 10 games | 100 games |
|---|---|---|
| D0 (heuristic) | .400 | .540 |
| TWIN (same matchup, 2nd sample) | .400 | .570 |
| D1 (1-ply search) | .200 | .290 |

Same checkpoint, same decks, same opponents. The `.00 / .20 / .40`
progression previously reported across 0 / 512 / 1024 is noise around a
higher level, and **no conclusion should be carried forward from it**.
The lane's default `R0_EVAL_G` is 100; the 10 was a deliberate
cost-saving on my part and it bought a wrong number, not a cheap one.

Second measurement note, smaller but load-bearing for anyone reading the
lane log: `rung0_lane.sh BenchDimir BenchDimir` was invoked with the
same deck in both slots, because no `BenchDimirTwin.dck` exists. **TWIN
is therefore a second sample of D0, not a second matchup.** D0 and TWIN
agreeing is one arm sampled twice. They are pooled to n=200 below, which
is the only honest way to use them.

## 1. Win rate — flat against the trained opponent

Pooled heuristic arm, n=200 per point, Wilson 95%:

| trained | pooled | 95% CI |
|---|---|---|
| 1024 | .555 (111/200) | [.486, .622] |
| 1536 | .590 (118/200) | [.521, .656] |
| 2048 | .585 (117/200) | [.516, .651] |

1024 → 2048: **+.030, z=0.61, p=0.54.**

Per-update training win rate over the final block (the only block whose
`server.log` survived — see §5): .562, .562, .469, .562, .500, .438.
Flat around .51, and below the eval figure because training samples
while eval is greedy.

**1024 additional episodes produced no measurable win-rate change
against the opponent they were trained against.**

## 2. The one arm that moved, and why it should not be believed yet

D1, the 1-ply search opponent, n=100:

| trained | win rate | 95% CI |
|---|---|---|
| 1024 | .290 | [.210, .385] |
| 1536 | .310 | [.228, .406] |
| 2048 | **.430** | [.337, .528] |

1024 → 2048: +.140, z=2.06, **p=0.039**. 1536 → 2048: +.120, p=0.079.

Recorded, not claimed. Three reasons to withhold:

- it is the arm with **a quarter of the games** of the pooled heuristic
  arm, which is flat;
- roughly six comparisons were run across this session, and a lone
  p=.039 among six is close to what noise alone delivers;
- the entire move is in the **final block**, after two flat ones. That
  is the shape of a lucky sample at least as much as a learning curve.

The case *for* it being real, stated so it is not lost: a search
opponent punishes over-attacking harder than the heuristic does, so
genuine attack restraint would surface on D1 first and on the heuristic
arm not at all — which is the observed pattern. §3 argues against that
story. **One seed settles it; it has not been run.**

## 3. Attack behaviour — the policy collapsed, and the counter names it

| | 1536 | 2048 |
|---|---|---|
| attacks declared | .950 (574/604) | .961 (565/588) |
| ATKOPT | .908 (385/424) | .901 (366/406) |
| ATKOPTCA | .877 (372/424) | .860 (349/406) |
| **attack under / over** | **0 / 39** | **0 / 40** |
| blocks declared | .879 (123/140) | .937 (133/142) |
| BLOCKOPT | .736 (81/110) | .765 (101/132) |
| turns/game | 20.2 | 19.7 |

BLOCKOPT 1536 → 2048 is +.029, p=0.61.

**`under_over = 0/39` then `0/40` is the finding.** Across both
batteries, every single suboptimal attack decision is an *over*-attack
and not one is an under-attack, at 95–96% of attack opportunities taken.
A policy making genuine mistakes in a hard decision errs in both
directions. A policy that errs in exactly one direction, at that rate,
is not deciding — it has collapsed onto "attack with everything".

This matches the transcript evidence from the same checkpoint
(`artifacts/v6/dimir_ck1024_trace_seed980005.txt`, and §4 below): 83 of
92 priority windows passed, 26 of them with 3+ real candidates. Pass
everywhere, attack with everything. Same collapse, two decision sites.

Caveat kept in the doc rather than in chat: ATKOPT's reference is one
combat deep and cannot see that an attacker will not be home to block,
so it structurally over-credits attacking and .90 is flattering. It
cannot, however, manufacture a 0/40 asymmetry, so that part stands
independent of the reference's bias.

## 4. What the per-decision counters *do* show — two real findings

### 4a. The self-targeting story is dead, and the correction is now numeric

`V6-TARGETING-FINDING.md` was published claiming the policy destroys its
own creatures and then corrected once it turned out the quoted windows
had no enemy legal target. This run closes it quantitatively. Splitting
target windows by whether an enemy creature was legal at all:

| ck | target windows | no enemy legal | chose enemy | **chose enemy when one existed** |
|---|---|---|---|---|
| 1024 | 255 | 131 (51%) | 104 | 104/124 = **.839** |
| 1536 | 289 | 157 (54%) | 132 | 132/132 = **1.000** |
| 2048 | 329 | 222 (67%) | 107 | 107/107 = **1.000** |

**When an enemy creature is targetable, the policy targets it — every
time, at both later checkpoints.** There is no ownership blindness. The
whole apparent pathology was the denominator.

Two caveats that bound this:

- **Cost legs are counted as target decisions.** The transcript proved
  it: Requiting Hex takes *two* `target` consults for one cast — the
  kill and the additional cost — and the cost leg typically has one
  legal option. So `no enemy legal` is an upper bound on "cast removal
  into an empty board", and the split by leg is still not built.
- The two exact 1.000s cannot rule out a swap (enemy chosen on the cost
  leg, own creature on the kill leg) without that same split. Unlikely,
  unverified.

### 4b. The real gap is *when* removal is cast, not *what* it targets

The share of target windows with no enemy option **rose** across
training: 51% → 54% → **67%**, while enemy targets legal fell 232 → 266
→ 202. The policy increasingly fires removal when there is nothing worth
hitting. Read with the cost-leg caveat above — but the direction is
wrong and it is the direction that matters here.

The instant-timing counters say the same thing from the other side:

| ck | instants cast | on opponent's turn | in combat | flash-capable held for opp turn |
|---|---|---|---|---|
| 1024 | 180 | 18 (10%) | 6 (3%) | 0 / 331 |
| 1536 | 193 | 23 (12%) | 12 (6%) | 1 / 350 |
| 2048 | 187 | 15 (8%) | 9 (5%) | 0 / 346 |

**~90% of instants are cast on the agent's own turn, and flash-capable
permanents are held for the opponent's turn essentially never — 1 time
in 1,027 opportunities across three checkpoints.** The agent has an
instant-speed deck and plays it at sorcery speed. Training did not move
this; if anything 2048 is worse than 1536.

This is not an encoder gap in the sense v6 addressed. The entity tokens
describe the board fine. What the candidate features do not carry is
*conditions* — that a removal spell has something worth hitting, that
holding it costs nothing, that the opponent's turn is coming.
`ENCODER-V6-RESULT.md` §5c and `PHASE8-TRANSFER.md`'s verdict both point
at the same missing axis from different directions.

## 5. Infrastructure findings

- **The policy server grows ~5 MB/episode.** Floor RSS 3.8 GB → 5.1 GB
  over 256 episodes; peak 4.9 → 6.2 GB. `_finish_update` does clear
  `buf`, `completed` and `ep_start`, and `Session.pending` is cleared
  per episode, so this is not a reference leak — the signature fits
  glibc arena fragmentation from the ~550 MB transient `update()`
  stacks every 32 episodes. **It is survivable only because
  `battery()` and the block loop restart the server every 512
  episodes**, which resets it (measured: 6107 MB → 655 MB across the
  1536 battery). Raising `UPDATE_EPISODES`, or running a block longer
  than 512, needs this fixed first.
- **No run in this project has a durable dense training curve.**
  `server.log` is truncated on every `start_server`, and the lane never
  passes `policy_server.py`'s `log_path`. Six `TRAIN|` lines survived
  this entire 1024-episode run. Wiring `--log` into `rung0_lane.sh` is
  a two-line change and would have made §1 a curve rather than three
  points. *Do not edit that script while a lane is running* — bash
  reads a script incrementally as it executes.
- `-Drl.trace` (this session, `RLPlayer.java`) logs one line per consult
  through a single `consult()` funnel, with seven site labels. It is the
  only instrument that shows decisions where the policy chose to do
  nothing, which is 83 of 92 priority windows.

## 6. What this run does not support

- Nothing here compares v6 to v5. **There is no encoder-arm control in
  this run at all.** "v6 plateaus at .585" is not "v6 is the reason".
- One seed, unreplicated.
- BLOCKOPT's denominator (110, 132) is small, and the transcript shows
  most block windows in these games are forced (`k=1`, no untapped
  creatures). It is not measuring 132 free choices.
- The 2048 → no-improvement result is specific to this deck, this
  opponent, and terminal-only reward. It is evidence about *this*
  configuration's ceiling, not about episode counts in general.

## 7. Reproduction

```
bash rl/dimir_trace.sh                     # one game, every consult
# the 1024->2048 run (anchor battery + lane):
#   scratchpad run_dimir_2k.sh, preserved in this commit as
#   rl/run_dimir_2k.sh
R0_ENCODER_V=6 R0_OUT=/tmp/rl_dimir_v6 R0_EVERY=512 R0_EVAL_G=100 \
    R0_CP7_G=0 R0_PORT=7995 \
    bash rl/rung0_lane.sh BenchDimir BenchDimir 2048 0
```

Artifacts: `rl/artifacts/v6/dimir_ck1024_trace_seed980005.txt`,
`rl/artifacts/v6/dimir_2k_batteries.txt`. Checkpoints and probes in
`/tmp/rl_dimir_v6/` (this container only).
