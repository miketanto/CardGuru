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

*(pending)*
