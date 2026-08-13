# Phase 8 — zero-shot transfer of graph features to unseen cards

**Question.** The E2 encoding gives every card a 91-dim mechanical
feature vector read off the CardGuru ability graph (68 graph dims +
23 structural) — no name identity. If that representation carries the
load, a policy trained on it should transfer zero-shot to *unseen*
cards whose feature vectors are similar. The name-hash E0 encoding
cannot, by construction: an unseen name hashes to an arbitrary bucket.

**Subjects.** `attn_desp` (attn/91, Elo 1053, best graph-feature agent)
and `attn_bc` (attn/91, 1044, independent checkpoint). **Negative
control:** `e0_champ` (e0/38, name-hash, Elo 1083 — the strongest
policy in the stable). **Rulers:** D0 (heuristic) and D1 (1-ply×8
search) — encoding-blind Java seats that play any deck natively.

**Environment.** Fresh container; XMage pin `7554968c` + the local
bounded-`getAttackablePlayers` patch + mirrored benchmark/rl sources;
dataset rebuilt from Forge pin `670429bf` (34,519 faces);
`rl/e2_extract.py` output verified **byte-identical** to the committed
`rl/e2_features.tsv` (35,390 names, dim 68) — feature rows for unseen
cards are exactly what training-era extraction would have produced.
Smoke: 4-episode evals for attn/91 and e0/38 both clean.

**Protocol.** All evals: 200g, argmax, `rl.noYields`, consultBudget
4000, stopTurn 80, one fixed seed block per deck (970000–974000),
mirrors (both seats play the same deck). 200g 95% CI ≈ ±.069.

---

## Milestone 1 — swap decks + calibration

Three variants of BenchDimir, 12 cards swapped each, chosen by
`rl/p8_swap_pick.py`: E2-nearest neighbors under same mana value, same
cost colors, same type split; candidates restricted to cards that are
(a) implemented at the XMage pin, (b) in the dataset + feature TSV
with a nonzero row, (c) in **no** committed deck (Bench, M3, Holdout —
the training-exposure superset), (d) free of graveyard-cast mechanics
(the PHASE5-M3 `getPlayable` OOM class), (e) single-faced. Lands,
Kaito, Cecil, Nowhere to Run, Day of Black Sun, Enduring Curiosity
stay fixed (core engine or no acceptable unseen analog: planeswalker
pool starts at d=5, Cecil's nearest is a 1/1 vs his 2/3). `d` =
feature mismatch count out of 68 graph dims.

### P8SwapInteraction (interaction suite, 12 cards)

| out | in | d | n |
|---|---|---|---|
| Bitter Triumph | Go for the Throat | 0 | 2 |
| Requiting Hex | Cut Down | 2 | 4 |
| Shoot the Sheriff | Eliminate | 0 | 1 |
| Spell Snare | Dispel | 0 | 1 |
| We Say Thee Nay! | Don't Make a Sound | 0 | 3 |
| Spell Pierce | Stubborn Denial | 0 | 1 |

### P8SwapThreats (threats, flash kept flash, 12 cards)

| out | in | d | n |
|---|---|---|---|
| Floodpits Drowner | Zephyr Sentinel | 4 | 4 |
| The Wondrous Wasp | Plumecreed Escort | 1 | 3 |
| Spyglass Siren | Faerie Seer | 2 | 4 |
| Elektra, Daughter of the Hand | Fathom Fleet Cutthroat | 0 | 1 |

### P8SwapMixed (both halves, replacements disjoint from A/B, 12 cards)

| out | in | d | n |
|---|---|---|---|
| Bitter Triumph | Easy Prey | 0 | 2 |
| Shoot the Sheriff | Cradle to Grave | 0 | 1 |
| We Say Thee Nay! | Clash of Wills | 0 | 3 |
| Spell Pierce | Concerted Defense | 0 | 1 |
| Spyglass Siren | Faerie Miscreant | 2 | 4 |
| Elektra, Daughter of the Hand | Ravenous Chupacabra | 0 | 1 |

### Calibration: 200g scripted D1 vs D0 per deck (seed 960000)

| deck | D1 win rate | Δ vs anchor | turns/ep |
|---|---|---|---|
| BenchDimir (anchor) | **.620** | — (replicates .614 @500g) | 17.0 |
| P8SwapInteraction (final) | .675 | +.055 (1.6σ) | 15.5 |
| P8SwapThreats | .685 | +.065 (1.9σ) | 17.0 |
| P8SwapMixed | .635 | +.015 (0.4σ) | 16.5 |
| P8Faeries (M2b, below) | .595 | −.025 (0.7σ) | — |

Instrument health: nodes/decision 2.87–3.0 (Phase 4 signature 2.9),
zero stalls anywhere in the phase (5,000+ games).

**Rebalance record.** The first interaction variant used Force Spike
for Spell Snare (d=0) and calibrated **.730** (+.110, 3.2σ) — too hot.
Bisect at 200g each: removal swaps only .675, counter swaps only
**.735** — the counter group carried the whole spike. Mechanism:
against scripted opponents that deploy on-curve with mana tapped out,
"counter unless its controller pays {1}" is a de-facto hard counter on
*any* spell, where Spell Snare only ever hits mana value 2 — a big
functional upgrade the feature space cannot see (it has `tgt_spell`
and cost bits, but no "counter-condition breadth" dim). Replacing that
single card with Dispel (d=0, narrow slice: instants, like Snare's
MV=2) brought the variant to .675.

## Milestone 2 — zero-shot matrix, 12-card variants

200g per cell. Transfer delta Δ = (win rate on variant) − (win rate on
BenchDimir), per policy per ruler.

| policy | deck | vs D0 | Δ | vs D1 | Δ |
|---|---|---|---|---|---|
| attn_desp | BenchDimir | .640 | — | .445 | — |
| attn_desp | Interaction | .660 | +.020 | .470 | +.025 |
| attn_desp | Threats | .665 | +.025 | .470 | +.025 |
| attn_desp | Mixed | .690 | +.050 | .540 | +.095 |
| attn_bc | BenchDimir | .590 | — | .435 | — |
| attn_bc | Interaction | .635 | +.045 | .525 | +.090 |
| attn_bc | Threats | .640 | +.050 | .460 | +.025 |
| attn_bc | Mixed | .615 | +.025 | .435 | .000 |
| e0_champ | BenchDimir | .670 | — | .425 | — |
| e0_champ | variants | *not run* | | *not run* | |

**All 12 graph-policy deltas are ≥ 0** (mean +.039, range .000 to
+.095): swapping 12/60 cards for unseen ones costs the graph-feature
policies *nothing*, on two independent checkpoints. Part of the small
positive drift is deck power (the variants calibrated +.015–.065 hot
for D1 too).

**Missing control.** The e0_champ 12-card-variant cells were skipped
when the phase was redirected to the full-archetype test (M2b) —
by user direction, mid-run. Without them, the variant-level flatness
of attn cannot by itself be credited to graph features; M2b (which has
the full 3-policy contrast) is the decisive comparison, and its result
(below) makes the skipped cells unlikely to have separated the arms.

## Milestone 2b — full-archetype transfer (user-directed): P8Faeries

The 12-card variants perturb 20% of the deck. M2b rebuilds the whole
archetype: **P8Faeries** — same *concept* as BenchDimir (UB
flash-tempo: cheap evasive flash threats, counters, instant-speed
removal, a card-advantage engine), **zero spell overlap** with any
committed deck. 37/37 spells unseen by every policy (Spellstutter
Sprite, Quickling, Pestermite, Slitherwisp, Obyra, Faerie Vandal,
Spectral Sailor, Peppersmoke, Agony Warp, …); same 23-land manabase to
isolate spell-side transfer; role structure mirrors the trained deck
(22 threats / 15 interaction). Calibration: D1 vs D0 **.595** —
statistically at the .620 anchor, so the scripted game is comparable
and policy deltas are policy-side effects.

| policy | vs D0 | Δ vs trained | vs D1 | Δ vs trained |
|---|---|---|---|---|
| attn_desp | .485 | **−.155** | .370 | −.075 |
| attn_bc | .380 | **−.210** | .325 | −.110 |
| e0_champ | .470 | **−.200** | .365 | −.060 |

Two facts:

1. **Archetype distance costs real win rate** — every policy drops
   (D0 column drops are all ≳2σ individually). The 12-card result does
   not extrapolate: transfer is fine at 20% deck perturbation and
   measurably degraded at 100%, even when the archetype's *plan* is
   the same.
2. **The drop is encoding-independent.** e0_champ — whose encoding
   maps every faerie spell to an arbitrary hash bucket — lands at
   .470/.365, statistically indistinguishable from attn_desp's
   .485/.370 (Δ of drops ≪ CI). The graph features bought no
   measurable protection against archetype novelty; conversely,
   name-hash bought no extra penalty.

The corollary is uncomfortable and important: if a policy with
*meaningless* card identity still plays a fully-unseen deck at
.47 vs D0 (well above the .386 D0-mirror floor, below D1's .595),
then most of what these ~43k–300k-param policies use is the
**structural/state channel** (mana, timing, board arithmetic, window
context) — card identity of either flavor is a minor term. That is
consistent with every E0-vs-E2 win-rate parity measured in Phases 3–5;
Phase 8 extends the parity to fully-unseen card sets.

Side observation: on the most flash-dense deck we've ever run (~1,500
flash windows per 200 eps), the policies cast flash threats on the
opponent's turn 2–8 times per 200 episodes — the C5 "no draw-go
emergence" finding survives a deck built to reward it.

## Verdict

**Do graph features buy measurable zero-shot transfer? No — not
detectably at 200g resolution, at either perturbation scale tested.**

- At 12-card (20%) perturbation with feature-matched swaps, graph
  policies transfer *perfectly* (12/12 deltas ≥ 0, two checkpoints) —
  but the redirected e0 control leaves open whether name-hash would
  have too, and M2b strongly suggests it would have.
- At full-archetype (100%) perturbation, all three policies degrade
  together (−.06 to −.21) with **no encoding contrast** — the
  negative control transfers as well as the treatment.
- Confidence: the M2b null contrast is 3 policies × 2 rulers at 200g
  each; the attn-vs-e0 drop differences (.01–.05) are far inside the
  ±.07 CI. A 5-seed, 500g gate could still find a small real gap, but
  nothing here motivates spending it.
- Mechanistically, Phase 8 adds two reasons the feature space
  *shouldn't* have separated the arms: (a) the policies' competence
  rides mostly on encoding-independent structural features (the e0
  faeries result); (b) E2 similarity is coarse on exactly the axis
  that matters — the Force Spike incident showed two d=0 cards moving
  a scripted mirror by 11 points because conditionality breadth isn't
  a feature dimension.

**Standing conclusion for the project:** the graph representation's
demonstrated value remains the Phase 5 robustness/liveness story
(lower freeze rates), not win-rate strength and now not zero-shot
transfer either. If transfer is the goal, the lever is not the card
encoder at this capacity — it is either (i) feature dimensions that
capture *conditions* (what a counter can counter, what removal can
hit), or (ii) enough network capacity that card identity becomes
load-bearing at all.

## Reproduction

```
python3 rl/p8_decks.py            # 12-card variants (+ rebalance note)
python3 rl/p8_faeries.py          # full-archetype deck
bash rl/p8_calib.sh <deck>.dck 200 960000 <tag>
bash rl/p8_matrix.sh 200 9020     # resumable 24-cell matrix
bash rl/p8_eval.sh <name> <arch> <ckpt> <opp> <deck> 200 <seed> <port>
```
Raw logs: /tmp/rl_p8/{calib_log.txt,eval_log.txt} (this container).
Cost: ~6,600 games (1,600 calibration + 200 bisect/load + 4,400 eval +
smoke) ≈ 2.5h wall-clock.
