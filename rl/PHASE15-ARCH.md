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

**And what the ANCHOR's weakness costs (measured 2026-09-16, after rung 0 ran; changes no threshold).** Rung 0's
clone turned out to equal its own trivial fixed-position predictor to five decimals on exact top-1 for both cloned
kinds - priority 0.67908 vs 0.67908 (position 1), target 0.82258 vs 0.82258 (first index) - while being genuinely
above it on class top-1 (0.777), type agreement (0.908) and copy-ceiling fraction (0.785, against 13b's 0.897 on
BenchDimir). It is not a bug: the log shows real training and an honest early stop. But every A4L clause is
measured against that anchor, so "the shared game transfers" can be satisfied by two models that have both learned
little more than a positional rule - it would then be measuring the shared POSITIONAL regularity of these decks,
not a shared game. Consequently every rung row reports **class top-1 and type agreement beside exact top-1**, the
trivial predictor is scored **both ways**, and each reading **names the metric it rests on**; a clause met on exact
index but not on class agreement is reported as such rather than as transfer. This is a limitation of the ladder
as instantiated on a sixty-card vanilla deck whose priority decisions are nearly positional, and it sits beside
the readings exactly as the uncloned combat kinds do.

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
- 2026-09-16 03:48Z WSL (third recorder pause; the night goes STRICTLY SEQUENTIAL from here, by decision):
  MemAvailable fell 6.5 -> 5.8 -> 5.1 -> 4.2 GB in five minutes with two recording JVMs growing beside A2's
  card-blind floor clone, and A2's heavy steps were still ahead - probe 3 pools the 25 13a recordings with the
  ladder and wire3a files, which is the largest load in the phase. Paused the recorder (STOPALL, then
  rl/stop_15rec.sh) with W0Base at 564/1,000 games kept and every finished 50-game job in counts.txt.
  DECISION, and it is a real trade: I am no longer trying to overlap the engine and the GPU. Three times now the
  pair has walked RAM down toward the bar, and each rescue costs attention that an unattended night does not have.
  `rl/run_15a4.sh` already serialises record -> drivers down -> clone -> eval per rung, so the ladder does its own
  recording safely; the cost is wall-clock (no engine/GPU overlap), the gain is that nothing gets OOM-killed at
  04:00 and every step stays resumable. `chain_15.sh` waits for the recorder to exit before the ladder, so with
  the recorder stopped the chain will go A2 -> ladder directly, which is exactly the sequential order wanted.
  EARLY A2 SIGNAL, not a reading (the clone has not finished, no probe has run): the CARD-BLIND floor clone
  reaches held-out top-1 0.815 after one epoch and 0.852 after two, against bc.pt's 0.884 with the real
  embedding. If that holds to convergence it says most of the clone's agreement with CP7 on this deck does not
  require card identity at all - which is the context every A2 number must be read in, and it is what probe 1's
  floor clause exists to expose.
- 2026-09-16 04:02Z WSL (A2 FLOOR CLONE DONE - a finding in its own right, committed before the probes land):
  `bc_random.pt` = the card-blind control (V7Policy(random_table=True), seed 13, cand_refers_pool, 13b's recipe
  and all four kinds, 68,500 labels, best epoch 6 of 9, 1,299 s-scale run). Held-out agreement, card-BLIND vs
  bc.pt (card-aware, the 13b row), on the SAME 13b hold-out:

  | kind | card-blind | bc.pt | difference |
  |---|---|---|---|
  | all | 0.861 (CE 0.3377) | 0.884 (CE 0.2920) | -0.023 |
  | priority | **0.848** | **0.876** | **-0.028** |
  | target | 0.884 | 0.889 | -0.005 |
  | joint attack | 0.968 | 0.977 | -0.009 |
  | joint block | 0.810 | 0.799 | **+0.011** (the card-blind net is BETTER) |

  Reading this as context, not as A2's pre-registered probe: **deleting card identity from the network costs
  0.028 priority top-1 and 0.023 overall, and nothing at all on blocks.** Whatever the clone is imitating on
  BenchDimir, ~97 % of it is reachable without knowing which card anything is - the wire's entity fields (zone,
  power, toughness, mana value, type flags, keyword bits, castable-now, legal-targets) plus position carry it.
  That is the honest frame for every A2 number: probe 1's floor clause exists precisely to expose this, and it
  also qualifies 13b's "card-level clone" discussion, where the ceiling fraction was read as evidence the clone
  follows CP7's CARD choice. A ceiling fraction cannot separate the two; a card-blind control can, and it says
  most of the agreement is not about card identity.
  Caveat that travels with it: the control is card-BLIND, not random-identity (CardTable clamps ids >= 1000 onto
  one shared zero row), one seed, one deck, and top-1 agreement is not a win rate. Probe 1 (the encoder-token
  probe) is running now over both checkpoints; probe 3 and the card-swap arm follow.
- 2026-09-16 04:07Z WSL (A2 probe CRASHED on its floor arm; fixed; A2 re-run): `A2RUN|probe1|rc=1` with
  `IndexError: index 27817 is out of bounds for dimension 0 with size 1001` at `net.table.table[cid]` - the probe
  took the EMB ceiling row from THE PROBED CHECKPOINT's own card table, and the card-blind control's table has
  1,001 rows while card ids run to 35,477. Two faults in one line, and the second is worse than the crash: even
  where it did not crash, the ceiling for the RAND arm would have been a RANDOM row rather than the frozen
  embedding, so the control's own ceiling would have been meaningless. FIX: `rl/artifacts/card_emb_v8/emb.pt` is
  loaded ONCE in main and shared by every arm's EMB control, with a bounds guard; `rand_distinct_frac` now counts
  the probed entities that keep a row of their own under CardTable's clamp. Verified on a two-deck smoke: both
  arms complete, and the EMB control is now IDENTICAL for BC and RAND (0.8622 both), which is the signature of a
  shared frozen table and could not have happened before. Stopped chain + A2 steps with `rl/stop_chain15.sh
  --steps` BEFORE editing (the rule: never edit a script a running job is executing); the expensive artifact
  `bc_random.pt` survives, so the re-run skips the floor clone and redoes probe 1 / probe 3 / card-swap only.
  SMOKE NUMBERS, EXPLICITLY NOT A READING (577 unseen-card entities over 17 informative columns - far too thin,
  and the real run pools the full 13a set): token 0.8552, frozen-embedding ceiling 0.8622, card-blind floor
  0.7674. If that shape held at scale it would satisfy A2's first clause (0.992 of ceiling, bar 0.80) and FAIL
  the floor clause (0.088 above the floor, bar 0.25; and within 0.10 of the floor is the explicit "discards"
  branch). That is why `rl/p15_a3.py` was written ahead of the reading. No reading is made until the real run.
  Also visible and behaving as designed: the card-blind net reads the WIRE's 18 keyword bits nearly perfectly
  (on-wire 0.9983) while scoring 0.7674 off-wire - the on-wire/off-wire split is doing exactly the job it was
  added for.
- 2026-09-16 04:11Z WSL (A2 PROBE 1 COMPLETE -> reading is **"the encoder discards card identity"**, so A3 IS
  TRIGGERED): full 13a set, 68,952 consults / 1,250 games, 60,003 probed hand entities, 22 distinct cards,
  6 held-out card identities, 15,571 unseen-card entities.

  | measurement | BC (card-aware) | frozen embedding (ceiling) | card-blind floor |
  |---|---|---|---|
  | `pre` - the bar AS WRITTEN (41 cols, held GAMES) | **1.0000** | **1.0000** | **0.9792** |
  | `card` unseen cards, OFF-WIRE (12 cols) | **0.8590** | **0.8727** | **0.7824** |
  | `card` unseen cards, on-wire (2 cols) | 0.8515 | 0.7968 | **1.0000** |
  | `card` seen cards, off-wire | 1.0000 | 1.0000 | 0.9739 |

  READINGS, as pre-registered: clause 1 **MET** - 0.8590 / 0.8727 = **0.984 of the frozen embedding's own probe
  score** (bar 0.80). Clause 2 **NOT MET** - the token is **0.0766 above the card-blind floor** (bar 0.25), and
  the runbook's explicit discard branch is "within 0.10 of the random floor", which 0.0766 satisfies. So probe 1
  reads **"the encoder discards card identity"**, and A3 (already written, `rl/p15_a3.py`) is required. Note both
  clauses are decided on the SAME number, which is why the pair is not contradictory: the token is near the
  embedding's ceiling, but so is a network that cannot see the embedding at all.
  The saturation I reported at 03:01Z is now settled as fact rather than suspicion: on the bar as written the
  CARD-BLIND net scores **0.9792** against the card-aware net's 1.0000. A probe that a card-blind network passes
  at 0.98 cannot be evidence that card identity survives, and that is why the off-wire card-identity split was
  added beside it rather than instead of it.
  CAVEAT RESOLVED: `rand_distinct_frac = 0.0` - every probed BenchDimir entity is clamped onto CardTable's shared
  zero row, so on this deck the control is a TRUE card-blind floor, not a partially random-identity one.
  ODD AND WORTH REPORTING, not a claim: on the 2 on-wire keyword columns the card-blind net is PERFECT (1.0000)
  on unseen cards while the card-aware net is 0.8515 and the frozen embedding 0.7968. A net with no identity
  channel echoes the wire's keyword bits exactly; the one with an identity channel does so less faithfully.
  CANNOTS for probe 1: 22 distinct cards and only 6 held-out identities, 12 informative off-wire columns - thin,
  and probe 3 (pooled over ladder and wire3a decks) exists to widen exactly that. Linear probes lower-bound what
  is present; a fail can be non-linear encoding. One deck, one seed.
- 2026-09-16 04:44Z WSL (A3 TRAINING DONE - the agreement clause is MET at no cost): rl/p15_a3.py, 13b's recipe
  plus the pre-registered auxiliary loss (every encoded entity token predicts its card's 68 e2_features, BCE,
  weight 0.1 fixed in the runbook before any A3 data), 65,471 labelled consults, 1,250 games, the 13b hold-out,
  aux coverage 0.942 of probed entities, early stop at epoch 11 with best epoch 8, 1,680 s.
  Held-out at best epoch: CE 0.2821, all-kinds top-1 0.8846, cls1 0.8979, type1 0.9327; priority top-1 0.8767.
  A3 CLAUSE ONE: priority 0.8767 against 13b's 0.876 = a drop of -0.0007, i.e. the remedy costs NOTHING in
  agreement (bar: drop <= 0.02). MET.
  The auxiliary objective was solved almost immediately and completely - held-out aux BCE 0.0034 after one epoch,
  0.0000 from epoch 7 - so the mechanism was fully active and the entity tokens certainly encode the e2 columns
  now. Whether that RECOVERS the probe score is clause two and is not known yet.
  Worth recording because it affects which checkpoint the clause is read on: held-out TOP-1 kept climbing to
  epoch 10 (0.8919) while held-out CE worsened after epoch 8, and v7_bc/p15_a3 select on CE. The saved checkpoint
  is therefore the CONSERVATIVE one for this clause; selecting on top-1 would have made the remedy look better,
  and that choice was inherited from 13b rather than made here.
  Next: the combined BC / RAND / AUX probe pass on the probe-1 population (where the "discards" reading was made)
  for clause two, which also produces the majority-class diagnostic the A2 row records as owed.
- 2026-09-16 04:48Z WSL (A3 COMPLETE; A2 diagnostic done; LADDER STARTED): A3 clause 1 MET (priority 0.8767 vs 13b 0.876, drop -0.0007) and clause 2 MET (off-wire 0.8232 / ceiling 0.8727 = 0.943, bar 0.90), so the reading of record is 'the remedy works'. Stated beside it: bc.pt was ALREADY at 0.984 of that ceiling, so clause 2 was satisfied before the remedy; what A2 failed was the FLOOR clause, and there AUX is +0.0408 over the card-blind floor against bc.pt's +0.0766 - the remedy halved the very gap it was proposed to widen, while costing no agreement (CE even improves). Majority-class diagnostic (owed by the A2 row): no-model baseline 0.6537 on unseen cards, so across the 0.6537-0.8727 span the card-blind floor captures 59 percent, AUX 77, the clone 94 - the floor is part imbalance and part genuine wire-field information, not an artefact. OWED: probe 2 (card-swap) was not re-run on bc_aux.pt. Rows written to V7-VALIDATION '15 / A3' and the A2 addendum. CHAINSTOP cleared and chain relaunched 04:48Z for the A4L ladder.
- 2026-09-16 05:04Z WSL (A3 probe 2 done - the OWED item is closed, and it reverses the natural reading): rl/p10_cardswap.py unchanged on bc_aux.pt with bc.pt re-run beside it on identical swaps. Embedding-row-only swaps move the remedied clone 1.7x more than the un-remedied one (0.06730 [0.05522,0.07956] vs 0.03975 [0.03476,0.04511], DISJOINT), P/T and cost sensitivity roughly double, and reliance on the wire keyword bits FALLS (0.00604 vs 0.00997, disjoint). So the auxiliary loss did shift weight from wire fields toward card identity - the direction it was proposed to produce - while its off-wire linear probe score went the other way (0.8590 -> 0.8232). Both are reported; A3's reading of record is unchanged (the remedy works, both clauses met), but the caveat now cuts both ways and the joint statement is that probe 1 is the weak instrument, the same conclusion A2 reached from the other side. Addendum written to V7-VALIDATION '15 / A3'. Ladder rung 0 recording at 713/1000 games.
- 2026-09-16 05:13Z WSL (housekeeping + a caveat promoted): REMOVED the leftover rl/artifacts/v7/15/rec/STOPALL (left by my 03:48Z third recorder pause; the 03:02Z one had already been cleared). The ladder never reads it - run_15a4.sh records through run_15rec.sh, which keys on its own per-deck STOP file - but run_15recall.sh does, and a bulk-recorder fallback that exits instantly would LOOK like 'recording finished' rather than 'recording refused to start'. That silent-success failure mode is worse than an unexpected start, so the file is gone rather than kept deliberately. Also PROMOTED the flip-rate disagreement out of the A3 addendum's cannots into its body: dp rises 0.03975 -> 0.06730 (disjoint) while strict flips fall 0.207 -> 0.149, the yardstick top gaps are nearly equal (4.233 vs 4.209) so sharper logits do not explain it, and the 'remedy increased card sensitivity' claim therefore rests on dp alone while flips point the other way. Two behavioural measures disagreeing in sign is exactly what gets quietly dropped; it is now stated as plainly as the dp result.
- 2026-09-16 05:32Z WSL (rung 0 recording DONE - 1,000 games, 31,281 labelled consults - and a GATE CORRECTION): the ladder runner printed 'gate|skip' because a gate.txt already existed from my earlier PARTIAL run, so it derived the fixed kind set from 437 games. Re-ran rl/gate_15rec.sh on the full recording; the kind set is unchanged (prio,target pass, attack/block fail, so the fixed set stands and no rung is affected) but the numbers of record are much worse than the partial ones I had been quoting: priority 19,070/19,070 = 1.000 pass, target 594/594 = 1.000 pass, joint ATTACK 6,084/10,179 = 0.598 FAIL (exact 6,018, alias 66, miss 4,095), joint BLOCK 5,533/9,157 = 0.604 FAIL (exact 4,782, alias 751, miss 3,624). The partial-run figures were 0.831 and 0.869; the full-recording figures are 0.598 and 0.604, i.e. CP7 declares attack/block sets outside CombatMath's candidate list about 40 percent of the time on this deck, not 15. Every rung row must carry the severity at this level: with two of four decision kinds uncloneable, the white ladder measures ONLY whether the new card's presence shifts priority and target choice, and says nothing whatever about blocking or attacking. TOOLING NOTE for the rest of the ladder: gate_15rec.sh is skip-if-exists, so a deck partially recorded before its gate ran will keep a stale gate.txt - the gate is re-run per deck after DONE and before the row is written. Also observed, not yet a reading: the rung-0 clone's held-out CE is pinned at 0.5758 with identical top-1 0.684 across epochs 1-3 while train CE barely moves, so the W0Base clone looks saturated just above that deck's trivial predictor (about 0.61).
- 2026-09-16 05:36Z WSL (RUNG 0 ROW WRITTEN; ladder on rung 1; throughput measured): rung 0 = 1,000 games / 31,281 labelled consults; gate prio 1.000 and target 1.000 pass, attack 0.598 and block 0.604 FAIL; fixed kinds prio,target. Clone best epoch 1 of 4 (saturates immediately), held CE 0.5758, held top-1 0.684. Eval on its own 100 held-out games / 2,902 consults: priority 0.6791 of a 0.8652 ceiling = 0.785, target 0.8226 of 0.9355 = 0.879, trivial predictor 0.6151. MEASUREMENT NOTE carried into every rung row: p15_a4.py scores all four kinds but the clone is trained on prio,target only, so the attack (0.2563) and block (0.5830) rows come from untrained heads and the 'all' row (0.5796) mixes them in - which is why 'all' sits BELOW the trivial predictor. The rung's numbers are priority and target; 'all' is documented once and never used in a reading. Reading: rung 0 is a reference, not a transfer test, and it sets a LOW bar - priority top-1 is only +0.064 above a fixed-position rule and the clone stopped improving after one epoch, so the headroom any later rung can show against it is small by construction. THROUGHPUT: with the box to itself the engine records ~75 games/min (50-game jobs in 28 s, two lanes) against ~11/min while it shared the box with A1/A2/A3, so a rung is about 30 min end to end (15 record + 4 clone + 8 joint clone + 2 eval) and the remaining white branch fits the night; no budget change needed.
- 2026-09-16 06:20Z WSL (RUNG 1a W1Fly COMPLETE - the aspect is NOT learnable at this rung, which VOIDS its transfer reading): 1,000 games / 27,663 labelled consults; this deck coverage 0.641 attack / 0.645 block (W0Base 0.598 / 0.604), carried per rung. Eval on 100 held games / 2,746 consults, aspect 1,663 / shared 1,083. THE GOVERNING READING: the rung-specific clone reaches 0.734 of its aspect copy ceiling on priority (0.600 all kinds) against a 0.80 bar, so by A4L own rule the aspect is not learnable from CP7 labels by this network at this rung and the transfer reading is VOID. Recorded for completeness: shared-transfer is met by the letter (0.5775 / 0.5775 = ratio 1.000, bar 0.95) but EMPTY - ZERO and RUNG are the same numbers to four decimals in every cell but one despite being clones of DIFFERENT decks, both sit at the trivial predictor on exact index and BELOW it on class agreement (shared class 0.6556 vs trivial 0.7073), which is exactly the degenerate case the preamble was amended to warn about; aspect-does-not-transfer is NOT met. JOINT is the informative column: trained on both decks (2,000 games) it reaches aspect priority 0.8006 = 0.906 of ceiling against the rung clone 0.6489 = 0.734, and shared priority 0.7341 = 0.902 against 0.5775 = 0.710 - it clears the very learnability bar the rung clone fails. OPERATIONAL CONSEQUENCE: 1,000 games per rung does not train a clone fit to serve as the rung-specific comparand the design requires; at that volume it collapses to a positional rule. This is A1 data-limited finding met from the other side. Later rungs run UNCHANGED (the volume is pre-registered and is not altered mid-ladder), but the learnability clause should be expected to fail for the same reason and the JOINT column is the one to read. Rung 2 (W1Fst, Head of Security) recording since 06:18Z.
- 2026-09-16 06:24Z WSL (rung 1a amendment; a stronger finding than the one asked for): checked the arms rather than relay them. ZERO and RUNG are distinct checkpoints (md5 8f990d59 vs 70a5c2bf) that genuinely behave identically - a clone trained ON the flying deck matches one trained without it. Training sizes and epochs now stated in the row: RUNG 1,000 games / 17,625 labelled / best epoch 1 of 4; JOINT 2,000 games / 37,289 labelled / best epoch 5 of 8. THE PREMATURE-EARLY-STOP HYPOTHESIS IS REFUTED by free evidence: TRAIN CE is frozen to four decimals from epoch 2 in both single-deck runs (0.6167, 0.6167, 0.6167 and 0.5535, 0.5535, 0.5535) with every held-out metric identical across epochs, so the runs stopped MOVING, not merely stopped early, and raising patience cannot help. The joint clone trains normally for eight epochs on the same recipe. HYPOTHESIS for the stall: logit bound B=5 with logits = B*tanh(logits/B) saturating and killing gradients on the smallest easiest set. OWED DIAGNOSTIC (not run tonight, GPU is the ladder): re-clone one rung with --logit-bound 0 or a lower LR and report beside the patience-3 number as a diagnostic, never a bar. The pre-registered NOT MET stays the reading of record, now stated as not-learnable-from-1000-games-by-this-recipe-in-a-stalled-run.
- 2026-09-16 06:36Z WSL (SATURATION CONFIRMED - rl/p15_sat.py): frozen bc_W0Base.pt has mean abs raw logit 54.45 with 95.1 percent beyond +/-20; the healthy joint clone 21.30 with 46.4 percent. Gradient through B*tanh(raw/B) at B=5 is about 1e-9 versus 8e-4 - six orders of magnitude - so the frozen clone is gradient-dead and the stall mechanism is supported. REGIME-DEPENDENT, from free log evidence: A0, A1 fractions, A2 floor clone, A3 aux clone and the A4L joint clone all show moving train CE; ONLY the two single-deck rung clones froze, so B=5 is not an unconditional freeze - the ~17,600-consult single-deck regime is. CANDIDATE cross-phase implication (not demonstrated): 13c per-update KL of ~0.0012 against a 0.02 target may be the same effect, since bounded logits barely move when raw logits are far outside the bound; measuring raw logits on 13c checkpoints is cheap and is OWED. FIX IS OWED, NOT APPLIED: a --logit-bound 0 or lower-LR re-clone, reported as a diagnostic; changing the bound mid-ladder would make rungs incomparable. Ladder continues unchanged (rung 2 W1Fst recording, 661/1000).
- 2026-09-16 07:15Z WSL (saturation dose-response, three frozen clones): bc_W1Fst.pt mean abs raw logit 90.8 (99.1 percent beyond +/-20, max 155) and bc_W1Fly.pt 109.9 (100 percent beyond +/-20, max 157), against bc_W0Base.pt 54.4 and the healthy joint clone 21.3. Gradient factors through B*tanh(raw/B) at B=5: about 8e-4 for the joint clone, 1e-9 / 1e-16 / 1e-19 for the three frozen ones. Three for three, with saturation depth ordered with the stall - a dose-response measured on independent checkpoints, not an inference from one. Rung 2 W1Fst is also a confirmed freeze (held CE 0.5823 identical epochs 1-4, train CE 0.5623 from epoch 2, best epoch 1 of 4), so the pattern is systematic and the ladder-level reading will state it ONCE rather than per rung. Its deck coverage is the worst so far: attack 0.590, block 0.559 (W0Base 0.598/0.604, W1Fly 0.641/0.645). Joint clone for rung 2 training now (2,000 games, 38,911 labelled).
- 2026-09-16 07:21Z WSL (SATURATION IS THE STALL, five checkpoints; rung 1a attribution REVISED in the open): rung 2 JOINT clone froze too (held CE 0.5862 identical epochs 1-4, train CE 0.5767 from epoch 2, best epoch 1 of 4) where rung 1 joint clone trained eight epochs. Raw-logit measurement: frozen clones 54.4 / 90.8 / 92.95 / 109.9 mean abs with 95-100 percent beyond +/-20; the two that trained, 17.15 and 21.30 with 36-46 percent. Clean separation across five independent runs, CUTTING ACROSS the data axis - both JOINT arms have 2,000 games and ~38,000 labelled consults and the same recipe, yet one trained at mean 17.2 and the other died at mean 93.0. CONSEQUENCE: rung 1a attribution of the JOINT-over-RUNG gap to data volume alone is too simple and is revised in the row; doubling the data made escaping saturation more likely, not certain. The A4L arms measure the interaction of the logit bound with this regime at least as much as transfer, and a rung whose arms all froze cannot speak about its aspect. The --logit-bound 0 re-clone is now the load-bearing owed diagnostic; still NOT run tonight because changing the bound mid-ladder would make rungs incomparable.
- 2026-09-16 07:22Z WSL (RUNG 1b W1Fst COMPLETE - degenerate: all three arms froze AND coincide): recording 1,000 games / 30,142 labelled; coverage 0.590 attack / 0.559 block, worst of three decks. Rung clone best epoch 1 of 4 (held CE 0.5823 flat, train CE 0.5623 from epoch 2, saturation mean abs 90.8); JOINT clone ALSO best epoch 1 of 4 (held CE 0.5862 flat, train CE ROSE 0.5655 to 0.5767, saturation 93.0). Eval on 100 held games / 2,793 consults (aspect 2,122 / shared 671): ZERO, RUNG and JOINT are IDENTICAL to four decimals on priority (aspect 0.6814, shared 0.5687) and on every shared cell - three clones trained on different data making the same predictions. JOINT aspect exact 0.5556 is BELOW aspect trivial 0.6013 and its class 0.6037 below trivial class 0.6616. READINGS: aspect-is-learnable NOT MET (0.766 of aspect ceiling vs 0.80 bar) which VOIDS the transfer reading; shared-transfers met by the letter and empty for the second rung running (ratio exactly 1.000 because the arms are the same policy); aspect-does-not-transfer NOT met; JOINT-HELPS is NO here, reversing rung 1a - the joint arm froze too. The rung establishes nothing about first strike and cannot: it establishes that when every arm saturates at epoch 1 the clauses become arithmetic on identical numbers. Rung 3 (W1Vig, Sun Sentinel) recording since 07:20Z.
- 2026-09-16 07:23Z WSL (PRE-REGISTRATION, written BEFORE the --logit-bound 0 diagnostic reports; ladder PAUSED): STOP file set at rl/artifacts/v7/15/a4/STOP so run_15a4.sh finishes the rung in flight (W1Vig) and does not start W1Lif. Reason: three consecutive rungs produced gradient-dead clones, and on rung 1b all three arms froze and coincided to four decimals, so further rungs of the same kind cost hours and answer nothing. DIAGNOSTIC LAUNCHED: bc_W1Fly re-cloned with --logit-bound 0, everything else identical (same init rl/artifacts/v7/13/init_on_s13.pt, same seed 0, same 10 percent game hold-out, same kinds prio,target, same lr/batch/patience), on the same W1Fly recording. W1Fly chosen because its JOINT arm trained properly (best epoch 5, saturation 17.2), so the rung has a healthy comparison already on record. FIXED IN ADVANCE, whatever the diagnostic shows: (1) every reading of record already committed for the FIRST series - rung 0, rung 1a W1Fly, rung 1b W1Fst, and their clauses - STANDS AS WRITTEN and is not rewritten, re-scored or withdrawn; corrections are appended as marked amendments, never silent edits. (2) If the relaxed bound UNFREEZES training (train CE keeps falling past epoch 2 and best epoch > 1), the first series is written up as a measurement of a TRAINING PATHOLOGY rather than of transfer, and any re-run of rungs 0 / 1a / 1b with the relaxed bound is published as a clearly-labelled SECOND SERIES beside the first, never replacing it; the two series are never pooled. (3) If it does NOT unfreeze training, that is reported plainly and the ladder resumes as originally planned with the remaining rungs. (4) The diagnostic is a DIAGNOSTIC: it creates no new bar, and no pre-registered A4L threshold changes on the strength of it.
- 2026-09-16 07:33Z WSL (DIAGNOSTIC DECISIVE - the logit bound was freezing training): bc_W1Fly re-cloned with --logit-bound 0, everything else identical. Best epoch 1 -> 12, run length 4 -> 15 epochs, held CE 0.6239 -> 0.4006, held top-1 0.632 -> 0.775, class 0.725 -> 0.916, type 0.892 -> 0.951, priority 0.621 -> 0.768 with class 0.914. +0.143 top-1 and +0.191 class agreement from one flag, on identical data / seed / hold-out / recipe. The bounded run was not just stopped early, it was 0.14 WORSE at its best and never moved after epoch 1, with raw logits at mean 109.9 against a bound of 5 (gradient ~1e-19). CONSEQUENCE: the A4L first series measured a TRAINING PATHOLOGY, not transfer - five of six clones across rungs 0/1a/1b froze and their arms collapsed onto one near-trivial policy. Per the 07:23Z pre-registration, first-series readings STAND AS WRITTEN and any relaxed-bound re-run is a labelled SECOND SERIES, never pooled. NEXT: saturation check on bc.pt itself (the 13b clone 13c trained from) - if it is comparably saturated, 13c per-update KL of ~0.0012 against a 0.02 target has a mechanism rather than a recipe explanation. Ladder still paused by STOP; W1Vig recording at 604/1000.
- 2026-09-16 07:36Z WSL (13c checkpoints ABSENT; measuring its twin instead; bc_aux healthy): rl/artifacts/v7/13/c/ holds only logs / levels / census / state.json - the .pt files were gitignored and not retained, so ck_1024 and ck_2048 cannot be measured and the 13c saturation question is unanswerable from its own artifacts. Recorded as such rather than left pending. SUBSTITUTE: rl/artifacts/v7/14/d2b/ck_{256,512,768,1024}.pt were trained FROM bc.pt with the Phase 13 recipe unchanged (lr 3e-5, logit bound 5, adv-norm batch, target-kl 0.02) over 1,024 episodes - same start, same recipe, same bound, opponent CP7 skill 1 instead of 6 - so the raw-logit trajectory across them answers whether PPO under this bound drives logits into saturation. Measuring now. Also: bc_aux.pt measures 9.09 mean abs raw logit (7.4 percent beyond +/-20), the same healthy band as bc.pt 7.57, so every published clone sits at 7-10 and only the bounded single-deck ladder clones sit at 54-110.
- 2026-09-16 07:37Z WSL (CORRECTION IN THE OPEN - my saturation explanation for 13c KL is REFUTED by the measurement I proposed for it): D2b trajectory from bc.pt with the Phase 13 recipe and bound unchanged - mean abs raw logit 7.57 (start) / 7.24 (256) / 7.70 (512) / 7.86 (768) / 8.09 (1,024), share beyond +/-20 rising only 0.0095 to 0.019. PPO under B=5 does NOT drive logits into saturation: +7 percent drift over 1,024 episodes, nowhere near the 54-110 band of the frozen ladder clones. The candidate mechanism for 13c approx_kl ~0.0012 against a 0.02 target is WITHDRAWN and the 13c recipe-based account STANDS AS WRITTEN, unamended. What survives, quantified: at mean ~8 with B=5 the gradient factor is ~0.15, so bounded updates are compressed about 6.7x relative to unbounded - a real constant-factor effect on every bounded run here, but not the exponential death (1e-9 to 1e-19) that froze the ladder clones, and not an explanation for a KL two orders of magnitude below target. The saturation finding stays scoped to the A4L single-deck regime where it is decisive.
- 2026-09-16 07:39Z WSL (SECOND SERIES pre-registration - written BEFORE any second-series number is produced or read): the --logit-bound 0 diagnostic met the trigger fixed at 07:23Z (bounded best epoch 1 of 4 vs unbounded best epoch 12 of 15; held top-1 0.632 -> 0.775), so the ladder gets a second series. WHAT WILL BE RE-RUN: rungs 0 (W0Base), 1a (W1Fly) and 1b (W1Fst) only - the three whose recordings already exist and whose first-series rows are committed. Each gets its RUNG clone and its JOINT clone re-trained with --logit-bound 0 and NOTHING else changed (same init rl/artifacts/v7/13/init_on_s13.pt, same seed 0, same 10 percent game hold-out, same kinds prio,target, same lr 1e-4 / batch 32 / patience 3 / weight decay 0.01 on heads, same recordings), then re-evaluated with rl/p15_a4.py unchanged on the same held-out games and the same aspect/shared split. WHICH CLAUSES ARE RE-SCORED, named now so the list cannot grow after seeing data: (a) 'the aspect is learnable at all' - rung clone reaches >= 0.8 of its aspect copy ceiling; (b) 'the shared game transfers' - zero-shot shared top-1 >= 0.95 x the rung clone's on the same consults; (c) 'the aspect does not transfer' - zero-shot aspect top-1 >= 0.10 below its own shared top-1 AND within 0.05 of the trivial predictor there; (d) 'joint helps or hurts'. NO OTHER clause is re-scored and no threshold changes. WHAT STAYS FIXED: the first series remains THE READING OF RECORD for rungs 0, 1a and 1b; second-series numbers are published in their own clearly-labelled rows beside it; the two series are NEVER pooled, averaged or compared as if they were seeds of one experiment. EXPECTED AND STATED IN ADVANCE so it cannot be claimed as a discovery afterwards: the second-series clones should train for many epochs rather than one and should score materially higher than the first series on every arm - that is what the diagnostic already showed on W1Fly, and it is NOT itself evidence about transfer. The transfer question is only whether the CLAUSES change once the arms are no longer frozen. If a rung's arms still coincide once unbounded, that rung is still reported as carrying no information about its aspect.
- 2026-09-16 08:14Z WSL (rung 1c W1Vig recording DONE + gate): 1,000 games, 31,121 labelled consults. Gate on the FULL recording (run by me before the runner reached its gate step, so no stale-partial repeat of the rung-0 mistake): priority 19,036/19,036 = 1.000 pass, target 569/569 = 1.000 pass, joint attack 6,279/10,290 = 0.610 FAIL (exact 6,200, alias 79, miss 4,011), joint block 5,237/8,797 = 0.595 FAIL (exact 4,592, alias 645, miss 3,560). CombatMath coverage by deck so far: W0Base 0.598/0.604, W1Fly 0.641/0.645, W1Fst 0.590/0.559, W1Vig 0.610/0.595 - all four in a narrow 0.56-0.65 band, so roughly 40 percent of CP7 combat declarations are outside the candidate list our own policy selects from on every deck of this family. Ladder is alive (run_15a4.sh under chain_15.sh) and between steps; STOP present, so W1Vig completes and W1Lif does not start. Clone, joint clone and eval follow, then the box frees for the pre-registered second series.
- 2026-09-16 08:20Z WSL (FOURTH consecutive freeze - the first series is uninterpretable AS A WHOLE, not rung by rung): bc_W1Vig.pt best epoch 1 of 4, held CE 0.5920 identical across epochs 1-4, train CE pinned at 0.5498 from epoch 2. That is four of four single-deck rung clones stalled at epoch 1 (W0Base, W1Fly, W1Fst, W1Vig), plus one of two joint clones (W1Fst). The freeze is not a property of a deck or an aspect: it is what the bounded recipe does in this regime, and the --logit-bound 0 diagnostic showed the same data and recipe trains for 12 epochs and scores +0.143 held-out top-1 when the bound is removed. CONSEQUENCE for how the ladder is read: the first series is best described as one measurement of a training pathology repeated four times, rather than four independent rung readings. Each rung row keeps its own committed reading (per the 07:23Z pre-registration, nothing is rewritten), but the ladder-level statement - owed once the second series exists - is that A4L as instantiated measured the logit bound interacting with 1,000-game single-deck training, and that no rung of the first series can speak about its aspect. Coverage stays per deck: W0Base 0.598/0.604, W1Fly 0.641/0.645, W1Fst 0.590/0.559, W1Vig 0.610/0.595.
- 2026-09-16 08:28Z WSL (RUNG 1c W1Vig COMPLETE - most degenerate yet; LADDER EXITED CLEANLY): ladder logged RUN15A4|stopfile then done at 08:27:42Z, W1Lif never started, all processes zero, box free. Rung 1c: both arms froze (rung clone best epoch 1 of 4 held CE 0.5920 flat; joint clone best epoch 1 of 4 held CE 0.5568 flat), making six frozen clones of seven trained across four rungs. Eval on 100 held games / 2,884 consults (aspect 1,736 / shared 1,148): ZERO, RUNG and JOINT identical to four decimals in EVERY cell including aspect all-kinds. The shared policy IS the trivial rule - aspect priority 0.7085 against trivial pos1 0.7085, shared priority 0.5971 against trivial 0.5971, equal to four decimals as rung 0's anchor was. All four clauses recorded NOT INTERPRETABLE; aspect-is-learnable would nominally read 0.803 of ceiling and recording that as a pass would be exactly the artefact the preamble guards against. Coverage 0.610/0.595. SECOND SERIES STARTED: s2_bc_W0Base clone launched at --logit-bound 0 per the b512184 pre-registration.
- 2026-09-16 08:38Z WSL (SECOND SERIES anchor done - the unfreeze reproduces on a second deck): s2_bc_W0Base.pt at --logit-bound 0, everything else identical to the first-series clone: best epoch 12 of 15 (first series: 1 of 4), held CE 0.3816 (0.5758), held top-1 0.776 (0.684), class 0.913 (0.777), type 0.954 (0.908); per kind priority 0.771 with class 0.910 (first series priority 0.679 - which equalled its trivial rule to five decimals), target 0.919 with class 0.984. So +0.092 held top-1 and +0.136 class agreement on W0Base, against +0.143 and +0.191 on W1Fly - the unfreeze is not a W1Fly peculiarity, it reproduces on the anchor deck. Note the first-series W0Base clone was the ANCHOR every A4L transfer clause was measured against, and it was a fixed-position rule; its second-series replacement is not. Remaining second-series clones launched sequentially (one GPU trainer at a time): s2_bc_W1Fst, then s2_bcj_W1Fly, then s2_bcj_W1Fst. Evaluation follows with p15_a4.py unchanged against exactly the four clauses fixed in b512184; first-series readings stand as written and the series are never pooled.
- 2026-09-16 08:49Z WSL (second series, third deck - the unfreeze is general): s2_bc_W1Fst.pt at --logit-bound 0, everything else identical: best epoch 11 of 14 (first series 1 of 4), held CE 0.3897 (0.5823), top-1 0.764 (0.661), class 0.907 (0.756), type 0.943 (0.901); per kind priority 0.758 with class 0.904 (first-series priority was 0.681, equal to its trivial rule), target 0.950 with class 1.000. Three decks now measured at the relaxed bound - W0Base +0.092 top-1 / +0.136 class, W1Fly +0.143 / +0.191, W1Fst +0.103 / +0.151 - and in every case the bounded twin stopped at epoch 1 while the unbounded one ran 11-15 epochs. The freeze is a property of the bounded recipe in this regime, not of any deck. Joint clones s2_bcj_W1Fly and s2_bcj_W1Fst running in sequence; evaluation follows against the four clauses fixed in b512184.
- 2026-09-16 09:01Z WSL (second series, the CONTROL pair - relaxing the bound rescues frozen runs without inflating healthy ones): s2_bcj_W1Fly.pt at --logit-bound 0 saved at best epoch 6 of 9, held CE 0.3814, top-1 0.780, class 0.914, type 0.953; per kind priority 0.773 with class 0.911, target 0.967. Its FIRST-series counterpart bcj_W1Fly.pt is the single arm of the seven that never froze (best epoch 5, held CE 0.3723, top-1 0.791, class 0.910), and the two land level - the unbounded version is +0.004 class and -0.011 top-1, i.e. no material change. That is the control the second series needed: where the bounded run was already training, removing the bound changes nothing; where it was gradient-dead (W0Base, W1Fly rung, W1Fst rung and joint, W1Vig rung and joint), removing the bound is worth +0.09 to +0.14 held-out top-1 and +0.14 to +0.19 class agreement. The effect is a rescue, not a uniform lift, which is exactly what a saturation mechanism predicts and what a confound like 'unbounded logits simply score better' would not. Final second-series clone s2_bcj_W1Fst running; evaluation follows against the four clauses fixed in b512184.
- 2026-09-16 09:06Z WSL (second series: rung 1a's rung clone is the DIAGNOSTIC clone, stated rather than aliased silently): the second series needs an s2 rung clone for W1Fly, and rl/artifacts/v7/15/a4/bc_W1Fly_nobound.pt IS that artefact - produced earlier tonight as the standalone --logit-bound 0 diagnostic, before the series was formalised. Verified identical in every respect that matters: 20 files, 1,000 games, 100 held games, 17,625 labelled consults, kinds prio:17047 target:578, same init rl/artifacts/v7/13/init_on_s13.pt, same seed 0, same 10 percent game hold-out, same lr/batch/patience, --logit-bound 0. Only the filename differs. It is therefore used as RUNG for rung 1a's second-series evaluation with no retraining, and it is named explicitly in the row so the provenance is reproducible rather than hidden behind a rename. Its numbers: best epoch 12 of 15, held CE 0.4006, top-1 0.775, class 0.916, type 0.951; priority 0.768 with class 0.914, target 1.000. Final clone s2_bcj_W1Fst is training (epoch 1 already at held CE 0.4358 / top-1 0.776 / class 0.897 against its bounded twin's frozen final 0.5862 / 0.678 / 0.766) - the second joint-scale rescue.
