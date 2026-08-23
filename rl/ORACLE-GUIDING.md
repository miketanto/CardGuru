# Oracle guiding — an asymmetric critic for a terminal-only reward

Suphx's *oracle guiding* and AlphaStar's opponent-conditioned value,
applied to CardGuru. Built and gated this session; the A/B is running.

## 0. Why this lever, after the others were priced

The elimination record across two codebases is unusually complete, and
it is what selects this lever rather than another:

| lever | verdict | where |
|---|---|---|
| better card encoder → transfer | null at two perturbation scales | `PHASE8-TRANSFER.md` |
| entity tokens + relations (v6) | no win-rate gain past 1024 ep | `DIMIR-V6-2K-RESULT.md` |
| imitation from a search teacher | .36–.40 vs a ~.50 teacher | `PHASE5-VERDICT.md` C1 |
| **potential-based shaping, hand-written Φ** | **NULL — shaped == unshaped** | `PHASE5-VERDICT.md` C2a |
| DAgger, true on-policy labels | **exactly 0.000** | `PHASE5-VERDICT.md` C3 |
| exploration | **not the failure** — the policy casts 87×/100g sampled, 0 argmax | `TIMING-GATE-RESULT.md` §4c |
| representation (independently, on a larger system) | "never the binding constraint" | anvil ADR-0050 |
| curation / composition | one-shot; never adds signal | anvil ADR-0035/0048 |

`anvil`'s audit (ADR-0049) names what is left: **learning-signal
density**. CardGuru's own measurements agree from a different angle —
the policy explores the cast and the credit never reaches its timing.

**And the shaping null is why this is not more shaping.** With
terminal-only reward and GAE(λ=0.95), every non-terminal residual is
already `γV(s′) − V(s)` — which is *identically* potential-based shaping
with Φ = V. The dense credit path is not missing; **it exists and is
fed by the critic.** Hand-writing a Φ does not add a mechanism, it
overwrites a learned quantity with an opinion, and C2a measured that as
null. The question is therefore not "add a dense signal" but **"is the
dense signal that already exists any good?"**

## 1. What is built

| piece | what it does |
|---|---|
| `-Drl.oracle=true` (`StateEncoder`) | emits the **opponent's hand** as entity rows into a separate list |
| wire key `"oe"` (`SocketPolicyClient`) | carries them alongside — never inside — the policy's `"e"` |
| `OracleCritic` (`policy_server.py`) | a **separate** network: privileged state → value |
| `--oracle` | recomputes the GAE baseline from that critic before the advantage loop |
| `rl/oracle_gate.py` | the anti-leak gate, 3 levels |
| `rl/oracle_ab.sh` | baseline vs oracle at matched budget |

**Why a separate network and not a privileged input.**
`EntityAttnPolicy` shares its trunk: `logits = scorer(y[:, 1:])` and
`value = value_head(y[:, 0])` read the *same* transformer output.
Privileged rows in that observation would land in the policy logits — a
cheating agent, and out of distribution at eval where the oracle is
absent. Separate parameters make the isolation structural.

**There is nothing to withdraw.** Suphx anneals its oracle away because
it distils into the policy. Here the critic only produces `values[t]`
for GAE and is never consulted at inference, so no annealing schedule
exists. This is the one place CardGuru's problem is *easier* than
Suphx's.

## 2. The gate, which passed before the run started

```
GATE|O1|PASS|"oe" does not reach the policy path
GATE|O2|PASS|a future leak WOULD be detectable (delta 0.021)
GATE|O3|PASS|the critic reads the oracle channel (value delta 0.058)
GATE|ORACLE|PASS
```

Level 3 exists because levels 1–2 alone would pass **trivially** if the
oracle rows went nowhere. A gate that only proves isolation cannot tell
"contained" from "inert".

## 3. Pre-registration — written before any result

Per `HANDOFF-STACK-TIMING.md` §3. A move on any of these is a bug:

1. **This cannot change any existing checkpoint's eval behaviour.** The
   critic is training-only. An eval arm with `-Drl.oracle` off must
   reproduce exactly.
2. **This cannot move `ck_0`.** Untrained is untrained.
3. **This cannot improve offline imitation accuracy** — it touches no
   supervised path.
4. **This cannot fix the §2a collision.** That is a property of
   `forCard`, which no critic touches.
5. **The policy's logits must be invariant to the oracle channel.**
   Gated, not assumed (§2). If this ever fails, every number from the
   arm is void — it is a cheating agent, not a better one.

**The readout is explained variance, not a win rate.**
`EV = 1 − Var(mc − V)/Var(mc)` against the actual per-consult-discounted
outcome. The claim is *lower value variance → better advantages*; if EV
does not move, the mechanism did not fire and **no win-rate run is
earned.** Reporting a win rate from an arm whose EV was flat would be
reading a lottery ticket.

**Prediction, recorded up front.** EV improves — the opponent's hand is
genuinely load-bearing information about who wins — but **the win rate
does not follow**, because `B1-TIMING-AB.md` §5 showed this rung cannot
detect removal use at all (86 casts and 0 casts produced the same win
rate). A better critic on a deck whose decisions do not matter should
buy a better *estimate* and no *strength*. If strength moves here, look
for the confound before celebrating.

## 4. Known caveats, before results

- **The critic starts from scratch on a trained policy.** Its first
  advantages are untrained-critic noise. The server announces this
  rather than letting it read as a null; a fair test needs enough
  episodes for the critic to converge, which is why the arm is 256
  episodes and not 64.
- **One seed per arm**, on one deck. `POOLED-ANALYSIS.md` §6 holds:
  between-net single-seed comparisons are provisional as a class.
- **Oracle coverage is reported** (`oracle_cover` on every `TRAIN|`
  line) because an oracle that silently fails to reach the critic — an
  un-recompiled driver, a class-init flag that never fired — would
  otherwise look exactly like a negative result.
- **The opponent's hand is the only privileged channel.** Libraries and
  future draws are not emitted; the oracle is partial, so this is a
  lower bound on what full privileged information could buy.

## 5. Reproduction

```bash
python3 rl/oracle_gate.py                       # 3 levels, no engine
nohup bash rl/oracle_ab.sh > /tmp/oracle_ab.log 2>&1 &
```

## 6. Results

### 6a. The baseline the whole design turns on

**First corrected reading, `B1Narrow` ck_1024, 32 episodes:
`value_ev = 0.3465`.**

The critic explains about a third of the variance in the discounted
terminal outcome. Not zero — it is not predicting a constant — and not
close to saturated.

**What this number does NOT have is a known ceiling**, and that governs
how the oracle arm is read. A perfect critic cannot reach 1.0 here: the
outcome carries irreducible stochasticity from shuffles, the opponent's
decisions, and hidden information. So "EV went from .35 to .5" cannot be
scored against 1.0.

That is exactly why the oracle arm is the right comparison rather than
an absolute target. Removing the agent's uncertainty about the
opponent's hand — and nothing else — makes the difference between the
two arms a **decomposition of the unexplained variance**: how much of
the 65% the critic misses is attributable to hidden information, and
how much is irreducible or a modelling failure. A small gap says hidden
information was never the critic's problem, which would be a real
finding and would send the next lever elsewhere (rollout-delta targets,
where the signal is measured rather than estimated).

### 6b. Three implementation failures, and what each one teaches

The first three attempts to run this arm all failed, none reached a
published number, and the failures are more useful than a clean run
would have been.

**1. The fresh critic diverged.** Wired straight into GAE and trained on
`ret`, it went **EV −1.47 → −6.05 over two updates**. The cause is
structural: `ret = gae + values` and `gae` is computed *from the
critic's own values*, so a randomly-initialised critic bootstraps off
its own noise with nothing anchoring it. Fixed with **Monte-Carlo
targets** — with terminal-only reward `mc[t] = R·γ^(end−1−t)` is exact,
so bootstrapping buys nothing here and costs stability.

**2. The question did not need the policy in the loop.** "Does
privileged information predict the outcome better" is *supervised*.
`--oracle-probe` now trains and scores the critic without letting it
supply GAE, so the policy trajectory is identical across arms and the
only difference is what the critic sees. This also removed the risk of
a diverging critic damaging the policy mid-measurement.

**3. The server was OOM-killed.** Storing a parallel `EntityObs` per
step doubled its largest allocation — `rel` is `(emax, emax)` int64,
~73 KB per step — and the kernel took it down after one update. The
first fix would have repeated the fault: indexing `states.rel[hidx]`
copies ~368 MB at n=5000. Now `act()` stores only the few privileged
**rows** and `update()` rebuilds the critic's batch in chunks from the
policy's own stored entities, sharing `rel` rather than copying it.

**A fourth, smaller:** `oracle_cover` initially read 1.000 in both arms
because the stored value was a list rather than `None`. It now counts
steps with **non-empty** privileged rows, so the control reads 0.000 and
the treatment ~0.67 — which is the whole point of having the counter.

### 6c. Validity, established

`oracle_cover=0.669` on the treatment arm and `0.000` on the control.
The Java emission, the `"oe"` wire key, the server routing and the
critic all work end to end, and the control genuinely has no privileged
input. An inert channel cannot masquerade as a negative result here.

### 6d. Where it stands

| arm | critic | privileged | status |
|---|---|---|---|
| baseline | policy value head, 1024 ep trained | no | **EV 0.361** (8 updates, range .312–.455) |
| probe0 | fresh, MC targets | no (`cover 0.000`) | running |
| probe1 | fresh, MC targets | yes (`cover ~0.67`) | queued |

`probe1 − probe0` is the privileged-information effect with the
fresh-network confound removed. Early held-out readings from a
randomly-initialised critic are negative by construction (−0.86, −1.06
on update 1) and say nothing; the comparison is the trajectory across
eight updates, and **neither arm's number should be quoted before both
finish.**


## 7. A fifth failure, and the reading rule it forces

**The divergence was architectural, not the oracle.** The CONTROL arm —
fresh critic, no privileged input whatsoever — diverged identically
(**−1.39 → −5.56**), which rules the channel out as the cause.
`state_token` is `glob_in(g) + pool(SUM over up to EMAX entities)`, so an
untrained head sits on a large-magnitude input and emits wildly scaled
values; the policy's own head had 1024 episodes to learn that scale.
Zero-initialising the output layer fixes it: the control now opens at
exactly 0.0000 and stays near zero instead of collapsing.

Running the control is the only reason this was caught. Without it the
night's conclusion would have been *"privileged information destabilises
the critic"* — which is false.

It also broke the gate, informatively: level 3 asserted the critic's
**value** moves when the hand appears, and a zero-initialised head emits
0 either way, so the gate would have failed a correctly-wired critic.
The rows enter at `state_token`, so that is where the test belongs
(delta 7.29).

### The reading rule, committed before the result

After 3 updates the fresh critic sits at **EV ≈ 0** while the trained
policy head reads **0.33–0.35**. A fresh critic given 256 episodes is
not going to catch a head trained on 1024, and it is not supposed to —
**the comparison is `probe1 − probe0`, two fresh critics at identical
budget, not either against the baseline.**

So, pre-committed:

- If **both arms end near 0**, the honest verdict is **underpowered, not
  null.** 256 episodes may simply be too few for either critic to learn
  anything, in which case the experiment has not tested the hypothesis
  and must be re-run longer before anyone writes "hidden information
  does not help".
- Only if **at least one arm clearly leaves zero** does the gap between
  them mean anything.
- The absolute level is not the readout and must not be compared to the
  0.361 baseline as though it were.


## 8. The control arm answered a different question, and it is the real result

`probe0` (fresh critic, no privileged input, 256 episodes) finished
**flat at zero**: `critic_ev` mean **−0.016**, range −0.099 to +0.029
across eight updates, while the trained policy head read **0.344** in
the very same runs.

The reason is arithmetic, and it invalidates the design rather than the
hypothesis:

| | |
|---|---|
| states the critic trained on | **40,809** |
| **independent labels** | **256** |
| critic parameters | ~700k |

**Every state in an episode carries the same terminal outcome**, so the
effective sample size for predicting that outcome is the number of
EPISODES, not the number of states. Fitting a 700k-parameter transformer
to 256 independent labels cannot work, and it did not. The trained
policy head reaches 0.344 only because it has seen 1024 episodes — still
just 1024 labels — accumulated across a whole lane.

Per §7's pre-committed rule: **this is underpowered, not null.** Nothing
here says hidden information fails to predict the outcome. It says this
instrument cannot tell.

### What the right instrument is

Match capacity to the label count. `anvil` hit the same wall and its
answer (ADR-0039, ADR-0043) was a **frozen-trunk ridge probe** — ridge /
kNN / small MLP on a pooled state representation, with a learning-curve
guard — precisely because a few thousand labels will not support a
network.

The CardGuru version, and the next thing to build:

1. **Collect once.** One engine run with `-Drl.oracle=true` dumping, per
   consult, the pooled state features, the privileged rows, and the
   episode's outcome. Thousands of episodes, not hundreds — the label
   count is the budget, and it is cheap because no learning happens
   during collection.
2. **Fit offline, twice.** Ridge on `[state]` and ridge on
   `[state ‖ oracle]`, same split, game-grouped holdout so states from
   one episode cannot straddle train and test — otherwise the shared
   label leaks and every R² is inflated.
3. **Compare held-out R².** That is the privileged-information effect,
   measured at a capacity the data can support, repeatable in seconds,
   and with no policy in the loop at all.

This is strictly better than what ran tonight: cheaper, better powered,
seedable, and it isolates the question completely. The online critic is
only worth building **after** the offline probe says the signal is
there — which is the same probe-before-build discipline that made
`timing_gate.py` worth writing.

### What tonight's oracle work does establish

- The full privileged path works end to end: Java emission → `"oe"` wire
  key → server routing → critic (`oracle_cover` 0.669 treatment /
  0.000 control).
- The policy is provably isolated from it (gate levels 1–2).
- Five implementation failures are documented with their causes, four of
  which would have produced a plausible-looking wrong number.
- **`value_ev ≈ 0.34` for the trained policy head is a real, new
  measurement** — the first time this project has measured what fraction
  of the outcome its critic explains. That number is what any future
  credit-assignment work has to beat, and it did not exist yesterday.
