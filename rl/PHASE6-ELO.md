# Phase 6 — Elo-based evaluation (AlphaStar-inspired metric reform)

## Why the metric changed

User question that triggered this phase: *"is the metric against D0 and D1
even the right metric?"* — followed by the direction to take inspiration
from AlphaStar's league: Elo-based ratings plus exploiter agents, "only
then could we really say if something got better."

Problems with the old probe metric (win rate vs D0 / D1 at a fixed seed
block):

1. **Two opponents is a 2-D projection.** A policy can climb vs D0 while
   flatlining vs D1 (seen repeatedly in C5/C6 curves); neither number
   orders the whole population.
2. **No transitivity.** attn_bc beat attn_v2 head-to-head (.56) while
   their D0/D1 probes said the opposite ordering — probes can't resolve
   this, a rating fit can.
3. **No robustness measure.** A high probe score says nothing about
   whether a targeted adversary folds the policy — AlphaStar's exploiter
   idea fills that hole.

## Method

- **Tournament**: every learned policy meets every scripted anchor
  (D0, D1, D1h) for 100g (argmax, no-yields, fixed seed block 980000),
  plus within-family policy-vs-policy round robins
  (`rl/elo_tournament.sh`, resumable via matches.tsv, two lanes split
  the field by family).
- **Bridging**: the scripted anchors are Java seats, encoding-agnostic —
  they carry the cdim-38 (E0) and cdim-91 (E2/attn) families onto one
  scale. Scripted-vs-scripted pairs use the existing 500g v3
  calibrations (D1>D0 .614, D1h>D0 .596, D1h>D1 .504).
- **Fit**: logistic MLE over the win matrix (`rl/elo_fit.py`), draws =
  half win, D0 anchored at 1000, scale 400/ln10.
- **Exploiter**: a BC-init same-arch net trains *only* against a frozen
  target (`rl/exploiter_lane.sh`); its eval win rate vs the target =
  the target's exploitability.

## Leaderboard (2,400 tournament games + 1,500 calibration games)

| agent      | Elo  | what it is |
|------------|------|------------|
| D1h        | 1088 | scripted 1-ply search, draw-go hold |
| D1         | 1085 | scripted 1-ply search |
| e0_champ   | 1083 | E0 MLP, BC-init + 2,560-ep clean self-play league |
| attn_desp  | 1053 | attn + desperation exploration, 832 eps (truncated) |
| attn_bc    | 1044 | attn transformer, BC only |
| attn_v2    | 1039 | attn + league fine-tune (LR 1e-4, BC anchor) |
| D0         | 1000 | scripted heuristic (anchor) |
| e0_bc      |  995 | E0 MLP, BC only |
| e0_ppo     |  943 | E0 MLP, yield-era PPO (legacy caveat) |

## What the ratings say

1. **e0_champ is at yardstick parity** (1083 vs D1's 1085) — the clean
   self-play league genuinely closed the gap to the search instrument,
   and the rating confirms what the probes suggested.
2. **League fine-tune was NEGATIVE for the attention family**:
   attn_bc (1044) > attn_v2 (1039) despite 1k league episodes. The
   self-play gradient at this scale erodes the BC prior faster than it
   adds skill for the big net. (Motivates Phase 7: better opponents +
   BPTT so the extra capacity earns its keep.)
3. **Desperation exploration is rating-neutral-to-positive**
   (attn_desp 1053, best attention agent) while being the only agent
   with nonzero opp-turn threat casts — the emergence experiment did
   not cost strength.
4. **The whole learned field sits inside ~140 Elo** — these are all
   still "same league" agents; nothing has broken away from the
   instruments.

## Exploitability (final)

Exploiter (e0 arch, BC-init, trains ONLY vs frozen e0_champ, 640 eps):

| trained | win vs e0_champ |
|---------|-----------------|
| 256     | .33 |
| 512     | .42 |
| 640     | .42 |

**Verdict: e0_champ is not cheaply exploitable.** A same-capacity
adversary given 640 dedicated episodes never reaches .50 against it
(plateau at .42), far below the ≥.65 hole threshold. The champion's
1083 rating is robust, not a probe artifact — the strongest evidence
yet that the clean self-play league produced genuine, non-brittle
skill. The trained exploiter still joins the Phase 7 opponent
population (a .42 adversary is a useful sparring partner even without
a winning record).

## Consequences for Phase 7

- Growth benchmark for the new lstm+attention league = **per-checkpoint
  Elo** (100g vs each scripted anchor, same MLE fit, D0=1000), appended
  as a ratings-over-time curve — not D0/D1 win rates alone.
- Exploiters join the opponent population (dropped into the league's
  external-opponent rotation as they are trained).
