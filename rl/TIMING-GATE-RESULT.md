# §2a — the candidate channel is timing-blind, but the observation is not

`HANDOFF-STACK-TIMING.md` §2a asks whether the policy can *represent* a
timing decision at all, and pre-registers that if the same card produces
the same candidate vector in a main phase and in the opponent's
declare-attackers step, "no amount of training can learn the difference"
and every downstream experiment is void.

**The collision is real: minimum within-card cross-step distance is
0.000000.** The conclusion drawn from it in §2a is not, and this doc
separates the two, because acting on the stop condition without checking
the rest of the observation would have been the same class of error the
ground rules exist to prevent.

A third finding, not asked for, turned out to matter more than either:
**the agent reaches an opponent declare-attackers window with anything
castable 4 times in 451.** See §4.

## 0. The container was empty — what had to be rebuilt

This session started with none of the state the handoff assumes.

- **`/home/user/mage` did not exist.** Every lane, driver and dump path
  in `rl/` resolves against that checkout; `rl/xmage-src/` is a patch
  overlay, not a build. Rebuilt from `engine-patches/README.md`'s recipe
  (pin `7554968c` + `phase9-engine.patch` + the two overlays) and
  scripted this time as `rl/setup_engine.sh`, with
  `rl/sync_engine_src.sh` for the Mage.Tests-only recompile an edit to
  an `rl/` source actually needs.
- **torch was not installed.** `download.pytorch.org` is refused by this
  environment's egress proxy (403); PyPI is allowed, so torch comes from
  there with its declared CUDA deps and runs on CPU.
- **`B1Fast`'s `ck_1086` weights are gone.** `artifacts/v6/black/`
  carries its *probe logs* (`b1fast_ck1086_games.txt`,
  `rl_b1_v6_probe_D0_1086.txt`) but no `.pt`. There is no B1 checkpoint
  anywhere in the repo. §2b's "re-probe `ck_1086` at 100 games" is
  therefore not a probe — it is a retrain. Recorded in §6.

`/tmp/rl_*` is container-local and this is the second time that has cost
a session. Checkpoints that a later phase is expected to re-probe belong
in `rl/artifacts/`.

## 1. What was built

| file | what it is |
|---|---|
| `rl/timing_gate.py` | the gate, modelled on `entity_gate.py` |
| `rl/cand_dump.sh` | collects real emission (random policy, no server, no torch) |
| `-Drl.candDump=<file>` | new hook in `RLPlayer`: one JSON line per priority consult |

`-Drl.entityDump` could not answer §2a: it writes the v6 view and the v5
state vector and **nothing about candidates**, no card identity and no
step. The new hook writes, per consult, the candidate rows, the card
name behind each row, the step, whether it was the agent's turn, and the
flat state — plus (§4) a census line for every priority *window*,
including the `k=0` ones that never reach a consult.

The gate has two levels on purpose. Level A alone would have licensed
the stop condition; Level B is what shows the stop condition does not
follow.

## 2. LEVEL A — the test §2a specifies

Group real emission by card name, split by step, report the minimum
within-card cross-step distance.

```
GATE|A|consults=11647|in_scope=1028|cards=10|cards_in_both_steps=1
GATE|A|card=Swamp|own_main_rows=2|opp_atk_rows=1|min_dist=0.000000
GATE|A|pairs=2|min_cross_step_distance=0.000000|colliding_cards=1/1
```

**Minimum within-card cross-step distance: 0.000000.**

State plainly what that rests on: **one card, two pairs, and the card is
a Swamp.** In 60 games only 4 opponent-declare-attackers windows carried
any castable candidate at all (§4), so the *removal spell* the rung is
built around never appeared in that step. Read alone, this row is thin.

## 3. LEVEL A-wide — the same question, properly powered

The §2a pair is the sharpest form of the question and the rarest in real
emission. The better-powered form is: is a card's candidate row the same
in **every** step it was offered in?

```
GATE|AW|card=Cruel Cut       |steps=4  |distinct_rows=1|STEP-INVARIANT
GATE|AW|card=Barony Vampire  |steps=2  |distinct_rows=1|STEP-INVARIANT
GATE|AW|card=Cabal Evangel   |steps=2  |distinct_rows=1|STEP-INVARIANT
GATE|AW|card=Dakmor Scorpion |steps=2  |distinct_rows=1|STEP-INVARIANT
GATE|AW|card=Felhide Minotaur|steps=2  |distinct_rows=1|STEP-INVARIANT
GATE|AW|card=Moriok Reaver   |steps=2  |distinct_rows=1|STEP-INVARIANT
GATE|AW|card=Swamp           |steps=17 |distinct_rows=2|varies
GATE|AW|step_invariant=6/7 cards
```

**`Cruel Cut` — the instant the ladder rung exists to test — was offered
in 4 different steps and emitted exactly one distinct candidate row.**

The single exception is a land, and it is not a timing signal: Swamp's
two rows differ in **slots 1 and 2 only**, which are `T_LAND` and
`T_SPELL`. That is the land-drop candidate (legal in an own main phase)
versus the mana-ability candidate (legal everywhere) — the decision-type
slot, a legality artifact. No spell has a second row anywhere.

This is what the emitter says it should do. `StateEncoder.forCard` is

```java
c[6]  = card.getManaValue() / 6f;
c[7..9] = power / toughness / isCreature
c[10] = card.isInstant(game);   c[11] = card.isSorcery(game);
identity(c, card.getName());
```

Every term is a function of the **card**. `game` is passed only to the
card-type predicates. There is no turn, step, phase, active-player or
stack term, so the invariance is a property of the emitter and not of
this sample. `c[10] isInstant` records that a card *can* be cast at
instant speed; nothing records whether it *is being* cast at instant
speed.

## 4. The finding that was not asked for, and outranks both

The census counts every priority window, including the `k=0` ones that
auto-pass before any consult — so it can separate "the engine never
offered the window" from "the agent had nothing castable in it".
60 games, `B1Fast`, random policy:

| opponent's declare-attackers windows | 451 |
|---|---|
| ...with **anything** castable | **4 (0.9%)** |
| ...where the agent **held an instant in hand** | 116 (25.7%) |
| ...held an instant and still could not cast it | **115 / 116** |

The agent is offered the instant-speed window constantly, holds a legal
instant in a quarter of them, and can cast in essentially none: **it is
tapped out.** The binding constraint at the opponent's declare-attackers
step is *mana availability*, which is decided one turn earlier in the
agent's own main phase, not the encoding of the spell.

That reframes the handoff's headline. "~90% of instants cast on its own
turn" is consistent with a policy that cannot see timing — and equally
consistent with a policy that has no mana left when the window arrives.
These counters do not separate those, and neither did the 2K run's.

**Caveat, and it is a large one: this census is from a RANDOM policy.**
A random policy taps out for uninteresting reasons. It is the right
collector for a question about the *emitter* (§2–3), and it is *not*
authority on what a trained policy does. The same census on a trained
checkpoint is cheap — it is one `-Drl.candDump` run — and it is the
single highest-value measurement left open by this doc. It is not run
here because there is no trained B1 checkpoint left to run it on (§0).

## 5. LEVEL B — does the step reach the logits at all?

§2a's stop condition assumes a colliding candidate means the difference
is unlearnable. That does not follow, because the candidate row is not
the observation. Three facts, from the code:

1. **v6's globals carry the step, more finely than the flat state does.**
   `encodeGlobals` sets `g[1]` active-player and a step one-hot in
   `g[2..7]`, with **`g[3]` a dedicated `DECLARE_ATTACKERS` bucket**.
2. **The state token is built from them**:
   `state_token = glob_in(g) + pool(entities)`.
3. **Candidates are scored after attending to that token.** The
   transformer takes `[state] + candidates` and `logits =
   scorer(y[:, 1:])`, so a candidate's logit is a function of the state.

The path also *fires* in practice — checked on the dumped states rather
than trusted from the code, because a live path the emitter never
exercises would be worth nothing:

```
GATE|S|own_main             |consult_patterns=1|s[15..19]=(1.0, 1.0, 0.0, 0.0, 0.0)
GATE|S|opp_declare_attackers|consult_patterns=1|s[15..19]=(0.0, 0.0, 1.0, 0.0, 0.0)
GATE|S|PASS
```

Both buckets are perfectly consistent internally (one pattern each,
across 1024 and 4 consults) and share none. v6 reads the finer `globals`
one-hot, but from the same `getTurnStepType()` call.

So the path exists. Measured, on the quantity that actually decides
cast-or-hold — `logit(spell) − logit(PASS)` — holding the candidate list
and the board fixed and moving only the step channels, at random init:

```
GATE|B|seeds=5|delta_min=0.000244|delta_max=0.018597|below_tol=0
GATE|B|scale_reference|one extra enemy creature moves the same margin by
                       0.003121-0.017544, vs 0.000244-0.018597 for the step
```

**The step moves the cast-vs-hold margin at every seed, by the same
order of magnitude as an extra enemy creature does.** A random-init net
is the right instrument for this: the question is whether the
architecture *routes* the step, and a trained net could hide a live path
behind learned indifference.

## 6. Verdict, and why the stop condition should not fire

- **§2a's collision is confirmed.** The candidate channel carries zero
  timing information: `min_cross_step_distance = 0.000000`, and every
  spell in the dump is step-invariant across every step it appeared in.
- **§2a's inference from it is wrong.** "No amount of training can learn
  the difference" would hold if the candidate row were the observation.
  It is not: the step is in the globals, the globals are in the state
  token, and every candidate attends to it before being scored. A timing
  decision **is** representable.
- **So the downstream work is not void**, and §2b is not blocked. What
  §2a does establish is narrower and still useful: any timing preference
  must be learned as a *state-conditioned* rescoring of a step-blind
  candidate, so it cannot be per-candidate. "Hold *this* removal but
  cast *that* one" is not expressible; "in this state prefer instants"
  is.
- **The mana census (§4) is the more likely explanation of the observed
  behaviour**, and it is not an encoding problem at all.

Pre-registration honoured: §3 of the handoff says an improvement on a
metric a change cannot move is a bug. Nothing was trained here, so
nothing could move. The gate is a property of the emission, exactly as
§2a says.

## 7. What this does not support

- The census is **one policy (random), one deck, 60 games**. It bounds
  nothing about a trained policy.
- Level A's *specified* pair rests on **one card and two pairs**. §3 is
  the load-bearing evidence, and it is a weaker statement (all steps,
  not the §2a pair specifically) reached with far more data.
- Level B says the step **can** move a logit at random init. It says
  nothing about whether any trained checkpoint uses it, and the
  magnitudes are init-scale, not a bound on what training reaches.
- Nothing here is a win rate, and nothing here bears on attack- or
  block-optimality.

## 8. Reproduction

```bash
bash rl/setup_engine.sh                 # once per container (~10 min)
bash rl/sync_engine_src.sh              # after any rl/xmage-src edit
bash rl/cand_dump.sh B1Fast 60 940003 /tmp/cand_win.jsonl   # ~40 s
python3 rl/timing_gate.py /tmp/cand_win.jsonl
python3 rl/timing_gate.py               # LEVEL B only, torch alone
```

Artifacts: `rl/artifacts/v6/timing/`.
