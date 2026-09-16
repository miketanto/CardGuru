# PHASE15-ARCH — bottom-up validation of the network: does it fit, does it discern cards, does it transfer? (runbook + pre-registration, 2026-09-16)

User (2026-09-16): "build from the bottom and validate whether the network architecture actually learns and
supports card discernment and transferability". No RL in this phase. Everything here is offline supervised work
on recordings we already have, except A4, which needs one new recording.

## Why these four rungs

Phase 14 left the architecture unexcluded: the offline critic (6.9 M parameters, `value_ev` 0.095) lost to ten
hand-picked scalars (0.196), which is as consistent with a fitting failure as with an information limit, and it
overfitted by epoch 2 on 1,125 training games. Meanwhile the **card embedding itself is known good**: a linear
probe on the frozen 128-d vector recovers mana value, P/T, colours and types at 0.99–1.00 (`rl/artifacts/card_emb_v8/README.md`,
gate G1). So the open question is what the *policy network* does with that vector: whether it can fit at all,
whether it keeps card identity, and whether anything it learns survives a change of deck.

Inputs that already exist: `rl/artifacts/v7/13/rec/rec13_*.jsonl` (25 files, 68,952 labelled consults, 1,250
BenchDimir games, CP7 teacher), `rl/artifacts/v7/13/bc/bc.pt` (the clone, 17.5 M parameters), `rl/v7_bc.py`,
`rl/p10_cardswap.py`, `rl/e2_features.tsv` (35,390 cards × 68 mechanical features), `rl/artifacts/card_emb_v8/`
(`emb.pt` [35478, 128], `split.json` = the 10 % of card ids held out before the embedding was trained),
`V7Policy(card_emb="random")` = a **card-blind control** that needs no new code. The 13b comparison rows: priority
top-1 0.876 (0.897 of its 0.977 copy ceiling), class top-1 0.890, type 0.919; text-only card-swap Δp 0.0424
[0.0375, 0.0477] against a fresh net's 0.0430 [0.0405, 0.0456], strict flips 0.207 vs 0.119, Δlogit 0.289 vs 0.235.

## A0 — can it fit at all? (~20 min, GPU)

Train the BC net on a deliberate memorisation task: 2,000 consults from 40 games, no weight decay, no early stop,
40 epochs, and separately the value head on those 40 games' outcomes.
* **Pass**: training top-1 ≥ 0.99 and training value EV ≥ 0.95.
* **Fail**: the plumbing is broken (masking, the frozen-table adapter, gradients reaching the card path). Stop the
  phase and find it — every later rung would be uninterpretable.
* Cannot: says nothing about generalisation; a pass only means the architecture can represent and reach the fit.

## A1 — is the fit data-limited or capacity-limited? (~1.5 h, GPU)

Retrain the clone at 12.5 / 25 / 50 / 100 % of the 1,250 games (game-grouped, the 13b hold-out, seed 0), and the D1
critic at the same fractions. Report held-out priority top-1, held-out CE, and value EV per fraction.
* **"Data-limited"** if top-1 (or value EV) is still rising at 100 % — the last doubling adds ≥ 0.01 top-1 or
  ≥ 0.03 EV. Then more recordings are the cheap fix (1,250 games ≈ 2 h of engine time).
* **"Saturated"** if the last doubling adds < 0.01 top-1 and < 0.03 EV → more of the same data will not help;
  the limit is the representation, the architecture, or the signal.
* Cannot: one seed per point; the critic's effective sample is games, not consults.

## A2 — does the policy network keep card identity? (~1.5 h, GPU)

Three probes on the SAME clone, each against two controls: the frozen embedding (ceiling) and a clone trained with
`card_emb="random"` (floor, one extra BC run ≈ 25 min).
1. **Representation probe.** Freeze the encoder; from the entity token of each card in hand, linear-probe the 68
   `e2_features` columns plus mana value, power, toughness and colours. Report macro accuracy / R² on held-out
   **games**.
2. **Behaviour probe.** `rl/p10_cardswap.py` unchanged: text-only Δp, Δlogit, strict flip rate, against the 13b
   rows above.
3. **Unseen-card probe.** Repeat probe 1 on the 10 % of card ids in `card_emb_v8/split.json` (never seen when the
   embedding was trained) and separately on cards that never appear in BenchDimir.
* **"Card identity survives the encoder"** if probe 1 reaches ≥ 0.80 of the frozen embedding's own probe score AND
  is ≥ 0.25 above the random-embedding floor, on held-out games.
* **"The encoder discards card identity"** if probe 1 is < 0.80 of the embedding's score or within 0.10 of the
  random floor → an architecture finding: card conditioning is being washed out. Remedy to test in A3.
* Report probes 2 and 3 beside it; a pass on 1 with a floor-level probe 2 means identity is present but unused.
* Cannot: linear probes lower-bound what is present; a fail can be non-linear encoding.

## A3 — remedy test, run ONLY if A2 reads "discards" (~1 h, GPU)

Re-clone with an auxiliary loss: each entity token also predicts its 68 `e2_features` (weight 0.1, stated in
advance), everything else as 13b.
* **"The remedy works"** if probe 1 recovers to ≥ 0.90 of the embedding's score AND held-out priority top-1 drops
  by ≤ 0.02 from 0.876. Then card conditioning is fixable by training, not by redesign.
* Otherwise report what it cost.

## A4 (SUPERSEDED 2026-09-16, before it ran, by A4L below — user redirect: prove transfer level by level on the minimal-deck ladder, not on one complex deck. Kept here as written.)

The existing non-Dimir recordings (`rl/artifacts/v7/11/rec_b1_M_*.jsonl`) carry **no teacher labels** (checked:
no `y`), so record one new CP7-labelled set on a second deck with the 13a machinery: **G1Landfall**, 1,250 games,
same job shape as 13a.
* (a) **Zero-shot**: the Dimir clone evaluated on the second deck's held-out games (priority top-1 vs that deck's
  own copy ceiling and its trivial predictor).
* (b) **Deck-specific**: a clone trained on the second deck only, same recipe.
* (c) **Joint**: a clone trained on both, evaluated on each.
* **"Transfers"** if zero-shot reaches ≥ 0.75 of the deck-specific clone's ceiling fraction AND beats that deck's
  trivial predictor by ≥ 0.15.
* **"Deck-specific memorisation"** if zero-shot is within 0.05 of the trivial predictor.
* **"Joint helps / hurts"**: (c) against (b) on the same hold-out, stated either way.
* Cannot: two decks is not a claim about decks in general; one seed; CP7's play differs by deck, so a transfer
  failure mixes representation and teacher-policy differences — say so.

## Order, budget, box

A0 → A1 → A2 (→ A3 only on a "discards" reading) → A4; A4's recording may run beside A1/A2 (engine + one GPU
process is within the box rule: at most two policy servers + two driver JVMs, MemAvailable ≥ 1.5 GB). Total ≈ 6 h,
mostly unattended. No RL run, no league, nothing that needs the lane.

## What this phase cannot settle

Nothing here says whether the agent can beat CP7; it says whether the network can fit, keep card identity and
transfer. A clean sweep of A0–A4 would leave the Phase 14 verdict (the win/loss signal is too weak) standing as
the RL-side explanation; a failure at A2 or A4 would mean Phase 13's clone and every RL run on top of it were
built on a representation that does not carry cards, and the fix is architectural.

## STATE (append-only)
- 2026-09-15 ~21:40Z WSL (phase start, A0 launched): box clear at launch (MemAvailable 11.3 GB, GPU 1.0 GB used / idle,
  no policy server, no driver JVM, no controller). Tools written: `rl/p15_a0.py` (the memorisation test; reuses
  `rl/v7_bc.py` load/run_epoch/ceilings and `rl/p14_d1.py`'s value path and EV, so A0 measures the same code
  13b and 14/D1 measured), `rl/run_15a0.sh` (resumable: skips when `a0.json` exists). A0 slice = 40 games taken
  ROUND-ROBIN over the two 13a lanes (20 from `rec13_H_s13000` = CP7 vs the heuristic, 20 from `rec13_C_s13500`
  = the CP7 mirror), capped at 2,000 labelled consults, 40 epochs, AdamW weight_decay 0, lr 1e-4, batch 32, no
  early stop, `--cand-refers-pool` init `rl/artifacts/v7/13/init_on_s13.pt` (the 13b start). Two lanes rather than
  one because a single lane's 40 games are ~0.83 wins and the value half needs outcome variance in its denominator.
  A0 also prints the grad norms on the card path after epoch 1 (adapter / cand_ref / zone MLP / pointer) - the
  "gradients reaching the card path" clause of the fail branch, checked directly rather than inferred.
  Smokes (4 games, 2 epochs, /tmp): round-robin picks 2 games per file; grads non-zero on adapter and cand_ref.
  A4 ON HOLD by coordinator message (the transfer rung is being rewritten as a ladder over the minimal W-decks);
  nothing for A4 was launched or written.

## A4L — transfer, level by level, along the curriculum ladder (replaces A4; ~5–6 h, no RL)

User (2026-09-16): "go with simpler decks to prove different aspects of the game to prove transferability in
each level". The ladder already exists and was built for exactly this discipline (`rl/CURRICULUM-LADDER.md`):
**each rung is the previous deck with four cards of sixty changed**, and every keyword rung has a no-keyword
control with the same swap. Nothing new is designed here; A4L measures transfer along it.

White branch (combat), each rung = `W0Base` + 4 copies of one card:

| rung | deck | the four cards | the aspect | control |
|---|---|---|---|---|
| 0 | `W0Base` | — | vanilla attack / block / trade math | — |
| 1a | `W1Fly` | Leonin Skyhunter | flying: changes which blocks are **legal** | `W1Ctrl` (Shrine Keeper, no keyword) |
| 1b | `W1Fst` | Head of Security | first strike: changes the **math** of a trade | `W1Ctrl` |
| 1c | `W1Vig` | Sun Sentinel | vigilance: removes the attack-vs-hold-back tradeoff | `W1Ctrl` |
| 1d | `W1Lif` | Mesa Unicorn | lifelink: changes the arithmetic of a race | `W1Ctrl` |
| 2 | `W2FlyLif` | Skyhunter + Unicorn | composition: two keywords at once | `W2Ctrl` |
| 3 | `W3Sorc` | Take Vengeance (sorcery) | removal exists; tapping is a liability | — |
| 4 | `W4Inst` | Swift Response (instant, **identical text and cost** to rung 3's) | **timing, and nothing else** | rung 3 is the control |
| 5 | `W5Trick` | Aegis of the Heavens (instant, +1/+7) | hidden information while blocking | — |

Black branch (threat assessment), run only if the white branch finishes inside budget: `B1Narrow` (power ≤ 2),
`B2Mid` (≤ 3), `B3Open` (any creature), `B1Fast` (Defeat's instant twin), `B4Card` (no board effect at all).

### What the rung-0 gate costs this ladder (added 2026-09-16, before any rung was cloned; changes no threshold)

The W-deck recordings do NOT support cloning the joint attack and joint block decisions: on `W0Base` the 13a
per-kind gate reads priority 1.000 and target 1.000 but **joint attack 0.831 and joint block 0.869**, both below
the 0.9 bar, because on a pure-creature deck CP7 frequently declares attack/block sets that are outside
CombatMath's candidate list (on BenchDimir the same counters are 0.948 / 0.974). 13a's convention applies - a kind
that fails the gate is not cloned - and the cloned kind set is **fixed across every rung at `prio,target`** so
rung-to-rung comparisons mean anything.

**The consequence, which must appear in every keyword rung's row and not as a footnote.** Rungs 1a-1d exist to
change combat itself: `W1Fly` changes which blocks are **legal**, `W1Fst` changes the **math of a trade**,
`W1Vig` removes the **attack-vs-hold-back tradeoff**, `W1Lif` changes the **arithmetic of a race**. With attack
and block uncloned, those rungs no longer measure any of that. What they measure is the much weaker question
of whether the new card's **presence** changes priority and target decisions - which creature to cast, which
spell to cast, what to target. Every rung reading is to be written in those terms: "the aspect does not transfer"
can only mean "it does not transfer through priority and target choice", and says nothing about blocking or
attacking, which were not labelled well enough on these decks to clone. Where that makes a rung's reading
**meaningless rather than merely weaker**, the row says so instead of reporting a number that looks like a result.

A label-free combat comparison is reported separately for the keyword rungs where it is cheap (the driver's
`[atkaudit]` / `[audit]` lines against CombatMath's reference, from `rl/record_census.sh`'s audit output). It is
**not part of any pre-registered A4L reading** and cannot become one.

### Data

CP7-labelled recordings per rung, the 13a job shape, **1,000 games per rung** (these decks run ~2 games/s, about
20× BenchDimir, so a rung is ~10–15 min). Rung 0 may reuse `rl/artifacts/v7/7d1b/*.jsonl` (15 files, 1,500
W0Base games, `teacher=cp7`, labels present) **if** its wire/label version matches 13a's gate; check, and say
which was used. Each rung's gate: ≥ 0.9 labelled per kind, as 13a.

### The split that makes a rung readable (definition fixed here, before any data)

For rung R, every held-out consult is **aspect** if the rung's new card is in the agent's hand, on either
battlefield, or is a candidate in that consult; otherwise **shared**. Report both separately, always.

### Measurements per rung

1. **Zero-shot**: the rung-0 clone (trained on `W0Base` only) evaluated on rung R's held-out games.
2. **Rung-specific**: a clone trained on rung R only, same 13b recipe.
3. **Joint**: a clone trained on rungs 0..R.
4. **Card-swap** (`rl/p10_cardswap.py`) restricted to the rung's new card against its control card.
Each with top-1, copy ceiling, ceiling fraction, and that rung's trivial predictor — on aspect and shared consults.

### Pre-registered readings (per rung; none may be changed after seeing data)

* **"The shared game transfers"** if zero-shot top-1 on **shared** consults ≥ 0.95 × the rung-specific clone's
  top-1 on the same consults.
* **"The aspect does not transfer"** if zero-shot top-1 on **aspect** consults is ≥ 0.10 below its own shared
  top-1 AND within 0.05 of the rung's trivial predictor there.
* **"The aspect is learnable at all"** if the rung-specific clone reaches ≥ 0.8 of its aspect copy ceiling. A
  rung that fails this says the aspect is not learnable from CP7 labels by this network — a stronger finding
  than a transfer failure, and it makes that rung's transfer reading void.
* **Control discipline (the point of the ladder)**: the same three numbers for `W1Ctrl` / `W2Ctrl`. If a control
  rung's zero-shot drop is within 0.03 of a keyword rung's, that rung's drop is **deck-change noise, not the
  aspect** — say so and withdraw the aspect claim for it.
* **Rung 4 against rung 3** isolates timing: same text, same cost, sorcery vs instant. Reading: **"timing is
  represented"** if the rung-4 clone's aspect top-1 is within 0.05 of the rung-3 clone's aspect top-1 AND
  zero-shot from a rung-3 clone to rung 4 loses ≥ 0.10 specifically on instant-speed consults (opponent's turn
  or declare-blockers windows).
* **Ladder-level reading**: the highest rung whose shared part transfers and whose aspect is learnable. State it
  as a level, e.g. "combat transfers through rung 2; removal timing does not".

### Cannots

Labels are CP7's choices, not optimal play — a rung failure mixes the network with CP7's own weakness at that
aspect; one seed per clone; top-1 against copy ceilings, not win rates, so nothing here is a claim about winning;
the aspect/shared split is by card presence, not by whether the decision actually turned on the aspect; two
control decks cannot separate every confound, only the one-card-swap ones; the black branch is optional and its
absence is not a negative result.
- 2026-09-16 02:33Z WSL (A4L read; rung-0 reuse CHECKED and DECLINED; ladder recording tooling written, nothing
  launched): `rl/artifacts/v7/7d1b/*.jsonl` matches 13a on the WIRE exactly (hello: wire 7, v7_dims identical,
  v7_rtypes 8 / v7_ctypes 8 / v7_zones 7, v7_emax 160 / v7_kmax 96, card_emb_v8, d_c 128, teacher=cp7) but NOT on
  the LABEL version: a per-kind census of `7d1b_s7400.jsonl` (100 games) finds priority consults only - prio
  1,488/1,488 = 1.000 labelled, and ZERO target / attack / block consults in the file, because 7d1b predates the
  13a teacher build (target and joint attack/block labels were added 2026-09-15 12:50Z). A rung-0 clone trained on
  priority-only labels would not be comparable with the four-kind clones every other rung gets, and A4L's gate is
  per decision kind. DECISION: re-record rung 0 on W0Base with the 13a job shape (`rl/run_15rec.sh W0Base`);
  7d1b is not used. Tooling written (not yet run): `rl/record_15.sh` (13a's job, deck as an argument),
  `rl/run_15rec.sh` (two lanes H/C, 50-game jobs, resumable per job, idempotent per deck via a DONE file, starts
  drivers 7911/7912 if down), `rl/gate_15rec.sh` (the 13a per-kind gate through `rl/rec13_summary.py` unchanged),
  `rl/stop_15rec.sh` (kill-by-script-file; its own name matches none of its patterns). Ladder decks all exist and
  each is W0Base with exactly 4 of 60 cards swapped: W1Fly Leonin Skyhunter / W1Fst Head of Security / W1Vig Sun
  Sentinel / W1Lif Mesa Unicorn / W1Ctrl Shrine Keeper (all for Silvercoat Lion); W2FlyLif Skyhunter + Unicorn and
  W2Ctrl Shrine Keeper + Traveling Philosopher (both for Glory Seeker + Silvercoat Lion); W3Sorc Take Vengeance /
  W4Inst Swift Response / W5Trick Aegis of the Heavens. Those names are the aspect/shared split keys.
  `rl/p15_a1.py` written (A1: policy and value stages, nested fractions of the 13b training games against the 13b
  hold-out, one JSON per point, resumable).
- 2026-09-16 02:36Z WSL (A0 DONE, reading PARTIAL, phase continues; A1 policy launched; A4L rung 0 recording
  launched): A0 = training CE 0.0476 (copy floor 0.0408), exact top-1 0.9795, class top-1 0.9960, type 0.9980,
  value EV 0.9908 (MSE 0.0086, Var(r) 0.9351), 328 s. The value bar (>= 0.95) is MET; the top-1 bar (>= 0.99) is
  NOT met by the letter, but this slice's pooled exact-top-1 COPY CEILING is 0.9810, i.e. the bar is above what
  the metric can reach here at any fit quality; 0.9795 is 0.9984 of the ceiling and attack/block sit exactly on
  theirs. DECISION I made without the user: continue to A1, record the rung as PARTIAL, leave the bar as written.
  Defence: the fail branch is specifically "the plumbing is broken (masking, the frozen-table adapter, gradients
  reaching the card path)", and all three are checked clean - adapter grad 0.118 and cand_ref grad 0.204 after
  epoch 1 (printed, not inferred), attack/block top-1 exactly 1.000 (masking), CE within 0.007 of the copy floor.
  Row written to rl/V7-VALIDATION.md '## 15 — architecture validation' / '15 / A0'. A1 policy stage launched
  02:38Z over all 25 recordings (one JSON per fraction, resumable); A4L rung 0 (W0Base, 1,000 games, two lanes,
  drivers 7911/7912) launched 02:37Z beside it - engine + one GPU trainer, within the box rule.
- 2026-09-16 02:41Z WSL (box decision + A2 definitions pre-registered BEFORE A2 runs): CONCURRENCY - A1's load of
  all 25 recordings plus the two recording JVMs took MemAvailable from 11.4 GB to 4.9 GB and falling (JVM RSS
  2.5 GB each, A1 1.8 GB mid-load). A1 is the in-order rung and a 40-min GPU run that would reload from scratch;
  the ladder recording is resumable at 50-game job granularity and idempotent. DECISION: stop the recording with
  `rl/stop_15rec.sh` (the stop-script file), let A1 own the box, resume the recording when A1's policy stage ends.
  Nothing is lost but the in-flight job.
  RUNG-0 GATE RISK (observed on the first 7 jobs, ~350 games, NOT the gate - the gate runs on the finished
  recording): priority 3,013/3,013 = 1.000 and target 1.000, but joint attack (986 exact + 9 alias)/1,184 = 0.840
  and joint block (1,058 + 141)/1,371 = 0.875, both below the 0.9 bar (on BenchDimir 13a got 0.948 / 0.974). On a
  pure-creature deck CP7 declares attacks and blocks outside CombatMath's candidate list more often. If the
  finished recording confirms it, I will apply 13a's own convention - "a kind that fails the gate is not cloned" -
  and clone the passing kinds only, UNIFORMLY on every rung so the rungs stay comparable, rather than skipping the
  rung; the ladder's aspect/shared split is by card presence, not by decision kind, so a priority+target clone
  still measures transfer. That is my decision if it comes to it; recorded here in advance.
  A2 DEFINITIONS, fixed before any A2 data (definitions, not thresholds): probe 1's SCORE = macro accuracy over
  INFORMATIVE binary columns - the 68 e2_features columns plus 5 colour bits, keeping only columns carrying both
  classes in the training AND held-out entity sets; the column set depends only on the targets, so BC / EMB / RAND
  are scored on identical columns. R^2 for mana value / power / toughness is reported beside it and is NOT the
  gate. Probed entities = cards in the recorded seat's OWN HAND (zone one-hot hand, mine=1, face-up, card id
  resolved), fit on training games, scored on held-out games. CEILING = a probe on the frozen card_emb_v8 row
  itself (128-d, pre-adapter) over the same entity instances and split. FLOOR = a clone trained from
  `V7Policy(random_table=True)` (rl/artifacts/v7/15/a2/init_random.pt built, seed 13, cand_refers_pool=True,
  17.5 M params - the same shape as bc.pt). CAVEAT that must travel with the floor: that table has 1,000 random
  rows and CardTable clamps ids, so every card id >= 1000 lands on the same zero row - the control is card-BLIND
  (identity removed) rather than random-identity; the fraction of probed entities keeping a distinct row is
  reported as rand_distinct_frac. `rl/p15_a2.py` written and syntax-checked.
- 2026-09-16 02:43Z WSL (A1 running; A4L evaluator written and smoked): A1 policy stage is at frac 0.125 epoch 5
  (held_top1 0.833) and owns the box; its hold-out reproduces 13b exactly (125 games, 7,167 held consults - the
  same 7,167 the 13b row reports), which is the check that the split rule was reproduced rather than re-drawn.
  `rl/p15_a4.py` written, compiled and smoked on the 350 already-recorded W0Base games with 13b's Dimir clone:
  the smoke is the zero-shot shape and the whole pipeline works (aspect/shared split, per-kind copy ceilings,
  trivial predictor chosen on TRAINING games and applied unchanged to the held population). Smoke numbers are 133
  consults and carry no reading. DECISION on the JOINT clone, taken for cost and recorded in advance: A4L asks for
  "trained on rungs 0..R"; a true cumulative clone at rung 5 would be ~11,000 games (13b's 1,250 took 1,299 s), so
  JOINT = rung 0 + the rung's own recording for every rung. Defence: every white rung is W0Base with exactly one
  card swapped, so the union {0, R} carries the same content as 0..R except for the other one-card decks; the one
  rung where that is NOT true is rung 2 (composition = 1a + 1d), and the true cumulative joint is run there if the
  night has room. Stated as a deviation, not as the runbook's text.
- 2026-09-16 02:45Z WSL (rung 0 GATE MEASURED on the 437 games recorded before the box pause; A1 frac 0.125 point
  in): `rl/gate_15rec.sh W0Base` -> priority 5,184/5,184 = 1.000 **pass**, target 213/213 = 1.000 **pass**,
  joint attack 1,687/2,031 = 0.831 **FAIL** (exact 1,675, alias 12, miss 344), joint block 2,079/2,393 = 0.869
  **FAIL** (exact 1,846, alias 233, miss 314). This confirms the risk logged at 02:41Z and is a property of the
  DECK, not of the tooling: on a pure-creature deck CP7 declares attack/block sets outside CombatMath's candidate
  list far more often than on BenchDimir (0.948 / 0.974 there). Applying 13a's convention as pre-registered: the
  failing kinds are NOT cloned. Further decision taken now, before any rung is cloned: the cloned kind set is
  FIXED ACROSS RUNGS at rung 0's passing kinds (prio,target) rather than re-derived per rung - a per-rung set
  would clone different decision kinds on different rungs and no rung-to-rung comparison would mean anything.
  Each rung's own gate is still measured, recorded in its row, and warned about if it disagrees with the fixed
  set. `rl/run_15a4.sh` changed accordingly before it has ever run.
  WHAT THIS COSTS, stated plainly: the white ladder's aspects are COMBAT keywords (flying, first strike,
  vigilance, lifelink) and the joint attack/block decisions are exactly where they would show most directly. With
  those kinds uncloneable on this deck family, A4L measures transfer through priority and target decisions only -
  which creature to cast, which spell to cast, what to target - where the aspect still enters (A4L's split is by
  card presence, not by decision kind). Any rung reading must carry this: "the aspect does not transfer" would
  mean it does not transfer THROUGH PRIORITY AND TARGET CHOICE, and says nothing about blocking decisions, which
  were not labelled well enough to clone on these decks.
  A1: frac 0.125 POINT = held CE 0.4033, held top-1 0.8436, priority top-1 0.8415, best epoch 7 of 10 (141
  training games); frac 0.25 running.
- 2026-09-16 02:50Z WSL (the night is now self-driving): three things run without further input.
  (1) ENGINE: `rl/run_15recall.sh` records and gates all 16 ladder decks one at a time (W0Base resuming from the
  437 games recorded before the 02:41Z pause; 531 at this line), two driver JVMs, no GPU, resumable per deck and
  per 50-game job. (2) GPU: `rl/p15_a1.py --stage policy` is on its third fraction. (3) `rl/chain_15.sh` launched
  02:50Z waits for the policy stage to exit, then runs the A1 VALUE stage, then `rl/run_15a2.sh` (A2), then
  `rl/run_15a4.sh` (the A4L ladder) - one GPU process at a time, and it holds the ladder until the recorder is
  finished so engine and GPU never compete for RAM. Every step is skipped when its own output exists, so killing
  anything costs the step in flight, not the night. Clean stops: `rl/artifacts/v7/15/CHAINSTOP` (between chain
  steps), `rl/artifacts/v7/15/rec/STOPALL` (between decks), `rl/stop_15rec.sh` (immediate, engine only).
  A1 points so far, against the 13b hold-out (125 games / 7,167 consults, reproduced exactly): 12.5 % (141
  training games) held CE 0.4033, held top-1 0.8436, priority top-1 0.8415, best epoch 7; 25 % (281 games) held CE
  0.3656, held top-1 0.8573, priority top-1 0.8524, best epoch 5. The last doubling so far adds +0.0137 top-1;
  the A1 reading needs the 50 % and 100 % points and is not made here. Box at this line: MemAvailable 4.6 GB with
  two JVMs plus the trainer, GPU 2.9 GB of 12.
- 2026-09-16 02:52Z WSL (second box decision, same cause): MemAvailable fell 11.4 -> 8.8 -> 6.4 -> 4.6 -> 3.7 GB
  over five minutes as the two recording JVMs grew toward their 4.5 GB heaps beside the A1 trainer, and A1's two
  LARGEST fractions (50 %, 100 %) had not started. The box bar is 1.5 GB and the trend would have crossed it
  mid-fraction. DECISION: pause the engine recorder again - `touch rl/artifacts/v7/15/rec/STOPALL` FIRST, then
  `rl/stop_15rec.sh`. Both are needed and the reason is worth recording: stop_15rec.sh's patterns are deliberately
  written so they cannot match its own shell, and `run_15recall.sh` does not contain the string `run_15rec.sh`, so
  the stop script kills the inner per-deck recorder but NOT the outer loop, which would simply start the next deck
  and bring the JVMs back. STOPALL is the loop's own between-decks check. Nothing is lost: W0Base keeps its 541
  recorded games, every finished 50-game job is in counts.txt, and `rl/run_15a4.sh` records whatever is missing
  per rung (skipping finished jobs) when the chain reaches the ladder. Consequence, stated: `chain_15.sh` waits
  for `run_15recall.sh` to exit before starting the ladder, so stopping the loop lets the chain reach the ladder
  sooner - which is correct, because run_15a4.sh serialises record -> drivers down -> clone by itself and never
  holds the engine and a GPU trainer at once.
- 2026-09-16 03:01Z WSL (A2 probe 1 was MEASURING THE WRONG THING; caught by smoking it before the chain reached
  it, fixed, and the flaw is reported rather than hidden). Three defects, in the order the smokes found them:
  (1) SATURATION - the pre-registered probe splits by GAME, but a recording uses ONE deck, so the held-out games
  contain the SAME card identities the probe was fit on (BenchDimir: 38 distinct cards). Worse, mana value, power,
  toughness, the type flags and the 18 keyword bits are FIELDS OF THE ENTITY ROW (WIRE-V7 2d 10-17, 30-33, 34-51)
  that the token is built from, and `v7_net.MLPSkip` exists precisely to keep every input field linearly
  recoverable. Measured: token macro accuracy 1.0000 AND frozen-embedding 1.0000, R^2 1.000/1.000/1.000. A
  card-BLIND net would also score ~1.0 on those columns, so the probe as written cannot discriminate BC from EMB
  from RAND and its "pass" would have been an artefact. (2) TRUNCATION - `--max-entities` filled the budget from
  the first recording, so pooling a second deck contributed zero entities (off_deck and unseen_id both empty).
  (3) COLUMN-VARIANCE COLLAPSE - fitting on BenchDimir and scoring on W0Base left exactly ONE informative
  off-wire column, because the minimal white decks are vanilla creatures and every ans_/api_/trig_ column is
  constant zero there; a 1-column macro accuracy of 1.0000 is meaningless. The cause of (3) being unfixable in
  place was that `v7_bc.load` DROPS every consult without a teacher label, which locked the probe out of the 125
  label-free wire recordings (`rl/artifacts/v7/wire3a/`) that span several decks - and A2 uses no labels at all.
  FIXES (definitions added, NO pre-registered threshold changed): the probe now reports TWO measurements side by
  side - `pre`, the bar exactly as written (kept, and reported as saturated), and `card`, split by CARD IDENTITY
  (fit on one set of ids, scored on ids never seen, plus an off_deck mode whose test set is exactly the cards
  absent from the baseline deck) and scored on OFF-WIRE columns only: the 50 e2 columns the entity row does not
  carry plus the 5 colour bits, which appear nowhere in WIRE-V7 2d. What survives there can only have come
  through the card embedding, which is what A2 asks. Entities are interleaved across files; loading is label-free.
  Smoke after the fixes (13a + W0Base + three wire3a decks, 53 distinct cards, 18 informative off-wire columns,
  7,515 unseen-card entities): `pre` token 1.0000 / embedding 1.0000 (saturated, as diagnosed); `card` unseen
  cards token off-wire 0.9641 vs embedding 0.9738, seen cards 1.0000 for both (memorised, as expected). The
  floor arm (RAND) is trained by the chain and is not in the smoke. Also worth reporting rather than hiding: the
  mv / power / toughness R^2 goes NEGATIVE on unseen cards (token -0.56 / -0.05 / +0.26, embedding -1.08 / -0.39 /
  -0.03) - a ridge fit on one set of identities extrapolates badly to new ones, which is itself a statement about
  how card-specific these readouts are.
- 2026-09-16 03:21Z WSL (A1 POLICY HALF COMPLETE; the chain had DIED and was relaunched): A1 policy stage, four
  nested fractions of the 13b training games against the 13b hold-out (125 games / 7,167 consults, reproduced
  exactly):

  | frac | train games | train consults | best epoch | held CE | all top-1 | cls1 | type1 | priority top-1 | target | attack | block |
  |---|---|---|---|---|---|---|---|---|---|---|---|
  | 0.125 | 141 | 7,375 | 7 | 0.4033 | 0.8436 | 0.8571 | 0.9051 | 0.8415 | 0.8496 | 0.9298 | 0.5920 |
  | 0.25 | 281 | 14,893 | 5 | 0.3656 | 0.8573 | 0.8721 | 0.9146 | 0.8524 | 0.8872 | 0.9632 | 0.5287 |
  | 0.5 | 562 | 28,949 | 7 | 0.3191 | 0.8753 | 0.8889 | 0.9290 | 0.8677 | 0.8969 | 0.9699 | 0.7069 |
  | 1.0 | 1,125 | 58,304 | 6 | 0.2922 | 0.8871 | 0.9022 | 0.9393 | 0.8793 | 0.8872 | 0.9783 | 0.8276 |

  Doubling increments in all-kinds top-1: +0.0137, +0.0180, **+0.0118** - monotone, decelerating, and the LAST one
  is above A1's 0.01 "still rising" bar, so the POLICY half reads **data-limited**. Checked rather than assumed.
  13b REPRODUCTION CHECK (the row must state it, because a mismatch would be a tooling fault rather than a
  finding): A1's 100 % point is the 13b recipe on the 13b data and hold-out, and it lands on 13b's published
  numbers - all-kinds top-1 0.8871 vs 0.884, held CE 0.2922 vs 0.2920, cls1 0.9022 vs 0.898, type1 0.9393 vs
  0.932, priority 0.8793 vs 0.876, best epoch 6 vs 6. Largest gap 0.004 on a rate and 0.0002 on CE - single-seed
  and cuda-nondeterminism scale. It reproduces; the A1 tooling is measuring what 13b measured.
  The VALUE half (>= 0.03 EV on the last doubling) is the other half of A1's bar and is NOT run yet, so no A1
  reading is written here; if the halves disagree they are reported separately, not reconciled.
  INCIDENT: `chain_15.sh` was launched 02:50Z, logged `C15|start`, was alive at 03:04Z, and was GONE by 03:21Z
  having written no further line - it died while sitting in its 30 s wait loop, so the value stage it had queued
  never started and the box sat idle for roughly two minutes after the policy stage finished. No OOM (dmesg
  clean), no error line, cause unexplained. It is the project's known detached-job failure (CLAUDE.md: the
  container recycles on SESSION inactivity, not process activity; long runs need a heartbeat). Remedy applied:
  relaunched the chain and started an 8 h `cmd //c start //min wsl -e bash -lc "sleep 28800"` keepalive beside it,
  which is what Phase 13 used. The chain is resumable, so nothing was lost but the idle minutes.
- 2026-09-16 03:24Z WSL (**CORRECTION IN THE OPEN** to the 03:21Z entry and to commit a47e53d): I wrote there
  that `chain_15.sh` "DIED" and "was GONE by 03:21Z". **That was wrong, and the diagnosis was wrong.** The chain
  never died: at 03:21Z I checked for a *value-stage* process and read the chain log, but never pgrep'd for
  `chain_15.sh` itself; it was alive the whole time (pids 159987/159993), stuck in its wait loop. The 03:21Z
  entry's "unexplained detached-job death" and its appeal to the container-recycling gotcha are withdrawn.
  THE REAL CAUSE, which is a better lesson than the wrong one: the loop polled
  `pgrep -f "p15_a1.py --stage policy"`, and **my own watcher process matched it** - a
  `bash -lc timeout 2400 bash -c 'while pgrep -f "p15_a1.py --stage policy" ...'` launched from outside the
  script to notify me when the stage ended. Its argv CONTAINS the pattern, so the chain saw "the policy stage is
  still running" for as long as my watcher lived, and the box sat idle ~20 minutes with A1's value stage queued
  behind a stage that had already finished. This is the CLAUDE.md hazard ("pkill -f matches the wrapper shell's
  own argv") in POLLING form rather than killing form, and the usual [b]racket trick does not help, because the
  text is genuinely present in the other process's command line.
  FIXES: (1) `chain_15.sh` now waits on the stage's OUTPUT - the four `a1_policy_*.json` points - which no command
  line can spoof; (2) `rl/stop_chain15.sh` added (its name matches none of its own patterns, per the rule) and
  used to stop BOTH chains, because my erroneous "it died" relaunch had left two running, which would have put
  two GPU trainers on one box; (3) one chain relaunched afterwards. Cost: ~20 idle minutes, nothing lost - every
  chain step is resumable and all four A1 policy points were already on disk. Lesson for the rest of this phase:
  a watcher's argv is part of the system; wait on artifacts, not on process names.
- 2026-09-16 03:40Z WSL (A1 COMPLETE, both halves; row written): value EV by fraction −0.0314 / −0.0575 / 0.0970 /
  0.0951 (AUC 0.701 / 0.764 / 0.770 / 0.788), 930 s. Last doubling: policy +0.0118 top-1 (>= 0.01) and value
  −0.0019 EV (< 0.03) -> by the pre-registered OR rule the reading is **DATA-LIMITED**, carried entirely by the
  policy half; the value half alone would read saturated. Reported separately, not reconciled. Both halves
  reproduce their parents (policy = 13b to <= 0.004; value = D1's N1 EV 0.095, best epoch 2, val_mse 0.5600, same
  hold-out), so A1 measures what 13b and 14/D1 measured. IMPORTANT and stated in the row: A1 does NOT support
  "more data fixes the critic" - it tests D1's "this fit is data-limited" inference directly by doubling the data
  and EV does not move; that D1 remark is qualified in the open. Every value interval straddles zero and is ~0.4
  wide, so the value half has almost no power and nothing should rest on it alone. Row: rl/V7-VALIDATION.md
  '15 / A1'. A3 is not triggered by A1 (it depends only on A2's reading). Chain moves to A2 next.
- 2026-09-16 03:41Z WSL (recorder restarted; the order for the rest of the night, stated because the ladder is
  the part most at risk of not finishing). ANSWER to "did run_15recall.sh exit early?": it exited BY MY DECISION
  at 02:52Z (STOPALL then rl/stop_15rec.sh), to keep two growing JVMs off A1's two largest fractions when
  MemAvailable had fallen 11.4 -> 3.7 GB. I cleared STOPALL at 03:02Z but did not restart it, so it was idle
  ~50 min - that idleness was an omission, not a design, and it is now corrected: restarted 03:41Z with A2's
  floor clone running, because recording is ENGINE-ONLY and A2's clone is lighter than A1's policy stage
  (MemAvailable 10.3 GB at restart).
  THE ORDER THIS PRODUCES, which is the one we want: the recorder works through the 16 ladder decks on the engine
  while the GPU does A2; `chain_15.sh`'s ladder step already WAITS for the recorder to exit (6 h cap) before
  starting `run_15a4.sh`, so the ladder's clone steps never share the box with two JVMs. When the ladder does
  start, every deck whose DONE file exists is skipped straight to gate -> clone -> eval, which is the whole point
  of recording ahead. If RAM falls under ~2.5 GB the recorder is paused again (STOPALL then stop_15rec.sh) - it
  is resumable per 50-game job and costs nothing but the job in flight.
  TRAP TO AVOID FOR THE REST OF THE PHASE (this is how the chain jammed once already): the chain polls
  `pgrep -f "run_15recal[l]\.sh"` for the recorder, so no long-lived process of mine may carry that literal
  string in its argv - a monitoring loop that does would make the chain believe the recorder is still running and
  hold the ladder indefinitely. Short polls are fine (worst case the chain sleeps one more cycle); wait loops
  must key on files.
