# Stack-depth search: a research plan

Branch: `build/stackwise-campaign`. Extends the live search in
`driver/CardGuruScenarioRunner.java` (arm (d): LLM value over
engine-executed leaves, see `docs/live-minimax.md`). Written after mirror
games 3–6; the evidence cited below is in `research/data/mirror/`.

The one-line version: **the search currently counts depth in priority
windows, which are mostly empty. Count it in stack exchanges instead, let
the opponent act on a determinized hand, give the pilot an interaction
window on their turn, and then add PokéChamp's other two LLM modules one at
a time, each as its own measured arm.**

---

## 1. The defect, precisely

`rolloutPriorityLeaf` casts my spell on a deep copy, calls `resolveStack`
— which only pops the stack and never gives anyone priority — and scores
the board. So:

- every threat resolves at full value with zero risk;
- holding mana does nothing in the rollout and scores as a pass;
- the opponent never acts, on this stack or on their own turn.

The search is therefore structurally biased toward tapping out. That is
not a prompt problem: the pilot only scores the leaves it is handed, and no
leaf ever shows the *cost* of tapping out. Games 3, 4 and 5 all lost the
same way — hellbent by turn 8, tapped out into a developing board, no
interaction when the opponent's engine resolved. `compactLeaf` carries five
fields (`line, our_life, opp_life, our_board, opp_board`): no open mana on
either side, no hand sizes, no stack. The pilot *cannot* price a tap-out
from what it sees, even when it wants to.

Two things this is NOT: it is not a hidden-information leak (the opponent
never acts in the copy, so it never uses its real hand), and it is not a
value-function problem (sonnet's leaf scores in g5/g6 were locally
sound). It is a tree-shape problem.

## 2. Depth in stack exchanges, not phases

A priority window is a unit of *engine bookkeeping*. A stack exchange is a
unit of *play*. The lines that decide a control mirror all look like:

> I cast Preacher → I'm tapped out → on their turn they draw a land → they
> cast Enduring Curiosity → I have no counter up → that is back-breaking.

Four links, spanning my main phase and their whole turn. Phase-depth 4
would enumerate dozens of empty windows to reach it; exchange-depth 2 gets
there directly. The tree per priority decision:

```
MAX₀    my action              pass | cast X | activate Y          (as today)
        [resolve, two windows -- see §3]
──────── their turn ────────
CHANCE  their draw             sampled from believed_remaining
MIN     their main-phase play  best castable play from (believed hand + draw)
MAX₁    MY response            counter | instant removal | nothing
LEAF    resolve → pilot scores the board
```

**`MAX₁` is the layer that gives holding mana a value.** It is the only
node where "hold" and "cast" produce a *different* leaf. Without it, hold
scores as "did nothing" in every line. With it, the search produces
exactly the three boards the line above is weighing:

| line | leaf the pilot sees |
|---|---|
| cast Preacher → they draw land → Curiosity resolves | Preacher on my board, **Curiosity on theirs**, my mana 0 |
| hold → Curiosity → **I counter it** | empty boards, each down a card, their engine in the graveyard |
| hold → they don't have it | empty boards, I wasted a turn |

Holding is right when `P(Curiosity) × (swing between rows 1 and 2)` beats
the cost of row 3. That is the calculation a human makes; the search
produces the rows and the pilot prices them.

**And when I have no answer, "do what you have to do" falls out
without a rule.** `MAX₁` only branches on moves I actually hold and can
pay for. With no counter and no instant removal it has one option,
nothing, and the two branches collapse to *Preacher + Curiosity* versus
*nothing + Curiosity*. The first strictly dominates. The value of holding
mana is *defined* as the difference `MAX₁` makes, so when there is nothing
to hold it for, that difference is zero and the search casts.

`MAX₁` must include **instant-speed removal**, not only counters. Holding
Cut Down is a real move on their turn — kill Curiosity at their end step
before it attacks or draws. That is in the same tiny set.

## 3. Their response to *my* spell is two windows, not one

Removal targets a creature **on the battlefield**. A creature spell on the
stack is not a creature. So "they answer my Preacher with Go for the
Throat" is never one response; it is:

```
cast Preacher        ← on the stack: only a COUNTER can touch it
  ↓ resolves
enters the battlefield
  ↓ ETB triggers and resolves
                     ← NOW removal is legal
```

Removal always lands **after the ETB has already happened**. The rollout
must sequence this explicitly — cast, resolve, let the ETB resolve, *then*
open the removal window — or the engine will either reject the removal for
lack of a legal target or, worse, the ETB will be silently skipped.

This makes "sometimes removal is fine" fall out of the engine rather than
a rule. Whether removal-after-ETB is a net positive depends on whether the
ETB is durable or tethered, and the engine already resolves both
correctly, so the leaf is right by construction:

- **Floodpits Drowner** — ETB taps and stuns. Kill it and the stun counter
  stays. They spent a removal spell for a tapped, stunned creature.
- **Deep-Cavern Bat** — ETB exiles "until this leaves the battlefield".
  Kill it and the card comes back. Removal undoes the ETB entirely.

The search does not need to know the difference. It resolves the ETB then
the removal; the leaf shows a stun counter in one case and a returned card
in the other; the pilot prices it from the card text. Two correct
consequences follow: counters are worth more than removal against ETB
creatures (the counter is the only thing that denies the ETB), and the
"Drowner cast into an empty board" misplay from g4 gets priced — *cast
now, ETB has no target* versus *hold, cast when they have a creature, keep
the stun even if they kill it* are visibly different leaves.

## 4. Belief-weighted expectimax, not minimax

Pure min-over-responses assumes they *always* hold the counter. That
produces the opposite failure — a pilot that never casts anything — and
is the naive outcome of "just model the opponent". Instead, weight each
response by the hypergeometric probability they hold it, given their hand
size and the remaining library:

```
value(candidate) = Σᵢ P(hold rᵢ)·score(leafᵢ) + P(hold none)·score(leaf_nothing)
```

In the mirror the deck is fully known, so `believed_remaining(deck, seen)`
is 60 minus everything we have watched leave their library, and the
weights are grounded rather than guessed. A 2-of counter in a 40-card
remaining library against a 4-card hand is ~19%; a 4-of removal ~36%. The
weights *fall* as copies are seen, which is the right shape.

Keep the pure worst-case value in the trace as a second signal. It is the
calibration instrument: when EV and worst-case disagree on a decision,
that is where miscalibrated weights would tip a coin-flip the wrong way,
and the seed 7 / seed 23 replays are where to tune it.

## 5. Determinization is mandatory and closes two leaks

The deep copy contains the opponent's **real** hand and library order.
Letting the built-in AI play their turn on the copy as-is would use hidden
information — inflating results in a way that never generalises. Before
any rollout that lets the opponent act, overwrite their hidden zones with
a sample: draw names from `believed_remaining`, find those cards in the
copy's library∪hand, put them in hand, everything else to library,
shuffle. `cardguru/believe.py` already has `sample_hidden`; the batch
generator already "seats the trick + a matching untapped land so each
scripted cast is legal". This is that pattern moved into the live driver.

It also closes a leak that exists **today**: Deep-Cavern Bat's ETB in a
rollout reads the opponent's real hand, and the built-in AI picks the
exile from cards it should not know. Determinize first and the Bat sees a
sampled hand.

Assert it: after determinization, the copy's opponent hand must not equal
the real hand, logged per rollout. Cheap, and the only way to be sure the
result is honest.

## 6. Leaf enrichment (small, high value)

Add to `compactLeaf`: my untapped mana, their untapped mana, both hand
sizes, **my remaining hand**, and what is on the stack. Two reasons:

- It is the information needed to price *"I'm tapped out into their turn
  holding nothing"*, which is the whole point of §2.
- It lets the pilot price *"I'll answer it next turn"* without the search
  going deeper. If I hold Go for the Throat at sorcery timing, the honest
  line is *cast Preacher now, kill Curiosity on my turn*. The leaf shows
  Curiosity resolved **and** the answer in my hand **and** my mana next
  turn; the pilot judges it. It also knows Curiosity returns as an
  enchantment, so it discounts that answer correctly — which is exactly
  the judgment the LLM is for.

## 7. What the LLM is for — PokéChamp's three modules, mapped

PokéChamp replaces three modules of minimax with the LLM: (1) player
action sampling, (2) opponent modeling, (3) the value function. Its state
transitions come from a statistical world model built on historical data,
which it needs because Pokémon hides movesets, items and EVs. We have one
of the three, and a strictly stronger transition function:

| module | PokéChamp | here today | plan |
|---|---|---|---|
| state transition | statistical world model | **real XMage engine** | keep |
| value function | LLM | **LLM** (arm d) | keep; one call/decision |
| opponent modeling | LLM from history + skill | enumerate blocks, take worst | arm (g) |
| action sampling | LLM proposes diverse lines | `attack-none/all/hold-one`, `getPlayable()` | arm (h) |

Two principles for adding the missing two:

**Keep it to one LLM call per decision wherever possible.** `askLeafScores`
already flattens every leaf across every candidate into a single
`leaf_eval` request; sonnet scored 22 leaves cleanly in g6. The tree can
get deeper without more calls. Every added call is ~7–12s at sonnet and
must earn its place in a measured arm.

**Piggyback on the required plan.** The pilot already writes a `plan` on
every real decision. That is a free channel for the opponent model.

The concrete LLM uses, in the order they earn their cost:

**(a) Value function — have it.** Unchanged. The pilot scores resolved
boards; the search reaches the fork, the LLM prices what it means
(Curiosity resolved vs countered is a huge swing the LLM sees from the
card text; the search never needs a five-turn lookahead to show it).

**(b) Opponent model as a persistent structured read — arm (g).** Add a
required `read` alongside `plan`: what the pilot believes they hold, as
weights the search can consume, e.g. `{"We Say Thee Nay": 0.6, "Go for the
Throat": 0.3}`. Echoed back like `standing_plan`, updated by the pilot,
and **used to reweight the MIN layer** in place of (or blended with) the
hypergeometric prior. This is what a human does and the hypergeometric
cannot: *they passed with `{1}{U}` open twice and cast nothing — that is
Bayesian evidence for a counter.* Zero extra calls; it rides on the
existing required field. This is PokéChamp's module (2) done cheaply.

**(c) Action proposer — arm (h).** At windows with many castable spells,
ask the pilot which 2–3 lines are worth searching before rolling out. It
prunes the MAX₀ branching and it is the only stage that plausibly needs a
second call. Also the riskiest: pruning the right line is a silent error.
Measure quality and cost against mechanical enumeration before keeping.

**(d) Threat-directed MIN pruning — folded into (b).** The `read` also
says which responses are *worth simulating*. A weight near zero is a
response we skip. So (b) both reweights and prunes, and no separate
"what am I afraid of" call is needed.

**(e) Plan-conditioned value — already partially there.** The standing
plan is in the request the pilot scores leaves from, so leaves consistent
with a stated intention get that context. Nothing to build; note it as an
ablation axis (score leaves with and without the plan in context).

## 8. Arms

Each arm changes **one** thing against the previous, so a difference is
attributable. Arms (d)–(h) are cumulative; (i) is an independent axis.
All run on seeds 7 and 23 first (both passed the fairness screen, both
have a known outcome under arm (d)), then unseeded.

| arm | change | what it tests |
|---|---|---|
| **(d)** | *baseline, exists* — LLM value, depth-1, no opponent | — |
| **(e)** | turn projection: CHANCE draw + MIN play on a determinized hand + `MAX₁` interaction window; hypergeometric weights; leaf enrichment | does modeling their turn fix the tap-out pattern? |
| **(f)** | (e) + two-window response to my spell (counter on stack / removal post-ETB) | marginal value of modeling responses to my own play |
| **(g)** | (f) + persistent structured `read` reweights and prunes MIN | PokéChamp module (2), at zero extra calls |
| **(h)** | (g) + LLM prunes MAX₀ to k lines | PokéChamp module (1); cost/quality trade |
| **(i)** | targets searched inside rollouts (close the `searching` gap) | independent; affects ETB creatures most |

Arm (e) is first because it is the line that actually lost games 3–5, and
because (f) is the smaller effect: "my threat got countered" was never the
failure; "I tapped out and they resolved a bomb" was.

### Status

- **Steps 1–2** (leaf enrichment, determinization) — built, verified live
  on seed 7 (`d63c325`): all six new leaf fields present on every leaf;
  11 rollouts reseated, 0 identical to the real hand. Re-baseline g7 under
  arm (d) + these two: WIN on turn 27, on the seed that lost g4 and g5.
- **Step 3 / arm (e)** — built behind `cardguru.project_turn=K`
  (`8945c19`, `9756252`), verified live on seed 7 as g8 with K=3, first
  three priority decisions: `project_turn_k=3`, 24 copies reseated, 0
  identical, **0 failed samples**; every leaf carries `sample` and
  `response`; both `MAX₁` windows fire (4 on-stack, 4 post-resolution).
  The window sorting works without naming card types — Cut Down appears
  only post-resolution, flash creatures appear on the stack.

  The asymmetry in the first real decision is the mechanism doing its job:
  `pass` produced 11 leaves (they cast Faerie Mastermind; I could flash in
  a Drowner or Mastermind on the stack, or Cut Down it after), while each
  cast candidate produced 3 — one per sample, all "nothing", because
  casting on turn 3 left no mana to respond with. That IS the tap-out cost,
  represented for the first time. The pilot still chose Cast Deep-Cavern
  Bat (mean-of-max 59 vs 57 for holding) into an empty board — correct, and
  the first evidence the expectimax backup does not push it passive.

  Deviation from §2 as written: their play is a deterministic heuristic
  (land, then most expensive castable spell), not MAD's search — nesting
  `calculateActions` per leaf is prohibitive. Also skipped: my combat and
  end step between my action and their untap.

## 9. Measurement

Win rate is the headline and the weakest signal: same 60 cards both sides,
null is 50%, and the handoff's own table says ~40 games to detect a true
70%. Do not read a win rate off fewer than that, and never off a mix of
configurations (the `1W-4L` line in `mirror.jsonl` spans four).

The process metrics are what move per arm, and we already compute most:

- **tap-out rate** — own main phases ended with 0 mana and spells in hand
  (13 in g4)
- **interaction rate** — instants cast on the opponent's turn
- **hellbent turn** — first turn the hand hits 0 and stays there (turn 8
  in g5)
- **hold-vs-cast decisions** — windows where a counter was possible: did
  the trace show EV and worst-case diverge, and which way did it go
- **leak assertion** — determinized hand ≠ real hand, every rollout
- **cost** — sims per window, wall-clock per game, LLM calls per game

Plus one synthetic case per arm: they have `{1}{U}` open, I choose between
casting Sheoldred and holding. Arm (d) casts every time. Arm (e) should
weigh the ~20% counter and the answer should depend on what I hold.

## 10. Cost budget

Per priority window with *k* castable actions and K draw samples:
`(k+1) × K × (their best play) × |MAX₁|`. With k=2, K=3, MAD's single
best play per sample, and `|MAX₁| ≤ 3`, that is ~24 leaves — still **one**
`leaf_eval` call. The added cost is ~20 deep copies per window; the docs
put a copy at 0.1–12s marginal, so this must be measured before arm (e)
is declared usable. Prune first by branching the draw only on land-vs-not
(the thing that changes what is castable) and by taking MAD's best play
rather than enumerating. Cap K and `|MIN|` and log both.

## 11. Risks

- **Injected-card legality.** A response card not findable in the copy's
  library∪hand → skip that response. Never fabricate a card.
- **ETB sequencing.** Removal activated with the spell still on the stack
  fails or skips the ETB. Sequence explicitly and assert the ETB resolved.
- **Over-pessimism → paralysis.** Miscalibrated weights push the pilot
  passive. EV + worst-case in the trace; tune on seed 7 / 23.
- **Cost creep.** Measure per-window wall time from day one; cap K.
- **Proposer pruning the right line (arm h).** Log what was pruned and
  spot-check against full enumeration on the replays.
- **Sub-choices in rollouts still go to the built-in AI** until arm (i):
  what my Bat exiles or my Drowner taps in a leaf is MAD's pick. Affects
  leaf quality for exactly the ETB creatures §3 is about. Known; tracked.

## 12. Exit criteria

- **(e)** tap-out rate and hellbent turn move in the right direction on
  both replay seeds; leak assertion never fires; per-window cost recorded.
- **(f)** the synthetic Sheoldred-vs-counter case answers "hold" when I
  hold the `{2}`, "cast" when I do not; no regression on (e)'s metrics.
- **(g)** the `read` is set on ≥ 90% of real decisions and the MIN
  weights it produces differ from the hypergeometric prior in at least the
  "held mana up and cast nothing" situations; hold-vs-cast decisions shift.
- **(h)** decision quality on the replays within noise of full enumeration
  at strictly lower sims per window; otherwise drop it.
- Then, and only then, the 40-game run.

## 13. Not doing, and why

- Five-turn lookahead — the LLM value function prices future value from
  card text; the search only has to reach the fork.
- LLM inside every tree node — each call is seconds; arms (g) and (h)
  add at most one, and (g) adds none.
- Non-mirror belief — the corpus classifier only matters once the deck is
  unknown. The mirror makes `believed_remaining` exact.
- Rewriting the attack search — its MIN layer already exists and works;
  this plan is about priority, where there is none.
