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

Instrument health: nodes/decision 2.87–3.0 (Phase 4 signature 2.9),
zero stalls anywhere.

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
MV=2) brought the variant to .675. All three variants now sit within
2σ of the anchor; accepted.

*Aside for the verdict: the Force Spike incident is itself evidence
about the representation — two cards at d=0 can differ enough in
conditionality to move a scripted mirror by 11 points. E2 similarity
is necessary-ish, not sufficient, for functional similarity.*

## Milestone 2 — zero-shot win-rate matrix

*(pending: 3 policies × 4 decks × {D0, D1}, 200g, argmax,
noYields, consultBudget 4000, seeds 970000/971000/972000/973000 per
deck)*

## Verdict

*(pending)*
