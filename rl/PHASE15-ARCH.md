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

## A4 — does anything transfer across decks? (~3 h: 2 h recording + 1 h training)

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
