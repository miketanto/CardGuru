# PHASE9-PROBES — does the v7 policy use card nuance, or only type and stats? (runbook + pre-registration, 2026-09-14; v7/lane-d = bd5ed2c)

Why (chat, after Phase 8): every v7 policy so far is describable without
card names (wall-then-race, attack-everything, never-block), the CP7 clone
matched action TYPE 0.89 but the card only 0.61 (ceiling 0.83), and the Dimir
policy plays a midrange deck as aggro. That is consistent with a scorer that
reads type, cost and power/toughness and nothing else — but nothing tests it.
Phase 9 measures it directly on existing checkpoints and recordings. No
training. No GPU lane. Four probes, each pre-registered below.

Rules that bind: CLAUDE.md; HANDOFF-V7.md §K environment + §M; the
operational lessons in rl/OVERNIGHT-7D.md STATE (WSL VM dies without an open
session — keep a `wsl -e bash -lc 'sleep 10800'` background task for any
detached job; two policy servers + two JVMs max; kill only via script files).
Wilson intervals / bootstrap CIs; pre-register readings; correct in the open;
commit + push after each probe; commit messages end with
`Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`. Append a dated
STATE line at the bottom of this file after every step.

Subjects (checkpoints on disk; confirm each path, fall back to the artifact copy):
- `init` = an untrained P10INIT net (`rl/artifacts/v7/7c1/s0`'s init shape: seed 10, cdim 94; regenerate with `p10_init_net.py` if no init.pt is kept) — the control.
- `C1s0` = rl/artifacts/v7/7c1/s0/ck_2048.pt (W0Base, scratch PPO).
- `L0` = /tmp/rl_7l_L0/ck_3072.pt or rl/artifacts/v7/7l/L0/ck_3072.pt (best W0Base).
- `BC` = rl/artifacts/v7/7d2/bc.pt (the CP7 clone).
- `DIM` = rl/artifacts/v7/8ab/s0/ck_512.pt (Dimir, 8a-b).
Recordings: `rl/artifacts/v7/wire3a/7c_W0Base_{p1,p99,sf}.jsonl` (1,101 consults),
`7c_BenchDimir_{p1,p99,sf}.jsonl` (903), `rl/artifacts/v7/7d1b/*.jsonl`
(20,735 CP7-labelled priority consults). Scoring tool: `rl/v7_init_logits.py`
loads a checkpoint and scores every candidate of a recorded consult — reuse
its loading path for every probe. Card data: the `cardguru` corpus (rules
text, types, keywords, cost, P/T) and the card embedding table the wire's
card ids index (`card_emb_v8`; find how a consult's candidate/entity rows
carry card identity — WIRE-V7 §2d identity arrays, §2f `v7_cand_refers`).

## P1 — card-swap counterfactual (the deciding probe)

Build ≥ 40 card PAIRS from the corpus + embedding table where both cards
are creatures with the SAME type line, SAME mana cost, SAME power/toughness
and DIFFERENT rules text (vanilla vs one keyword: flying, lifelink, first
strike, vigilance, deathtouch, menace; or two different keywords). Also
build three control pair sets of the same size: PT-only swaps (same
type/cost/text, P/T differs by 1), cost-only swaps, type-only swaps
(creature ↔ non-creature of the same cost). Record the pair lists
(`rl/artifacts/v7/9/pairs_*.txt`, committed).

For each subject and each consult in the W0Base + Dimir sets that offers a
SPELL candidate whose card is in a pair: rescore the consult with that
candidate's card identity swapped to its partner (embedding row and any
identity field; the afterstate row stays — state which fields you swap
and which you cannot), keep everything else fixed, and record
Δp = |p_after − p_before| on that candidate and whether the argmax flips.
Report per subject and per swap class: mean Δp with a bootstrap 95 % CI
(resample consults), argmax-flip rate, n.

Pre-registered readings, per subject:
* **text-blind** if mean Δp(text-only) is < 0.10 × mean Δp(PT-only) with
  the CIs disjoint;
* **text-sensitive** if mean Δp(text-only) ≥ 0.5 × mean Δp(PT-only);
* otherwise "weakly text-sensitive", with the ratio.
* **Training effect**: compare each trained subject with `init` on the
  text-only class — "training sharpened / preserved / erased text
  sensitivity" by whether the trained CI is above / overlapping / below
  init's. BC is the interesting one: it had supervised card labels.
Cannots: sensitivity of the scorer is not strategic use (a policy can be
text-sensitive and still play type-level strategies); the swap is on the
policy's input, so it measures what the network reads, not what the game
rewarded; pairs are limited to the cards the embedding table knows.

## P2 — removal targeting (Dimir)

From the Dimir set (and a fresh 8-game argmax recording of DIM on 7911 if
the echo sets lack removal consults), take every TARGET consult with k ≥ 2
legal creature targets. For DIM, C1s0 and init: P(policy picks the
largest-power target) vs 1/k; P(picks the target the combat optimiser
would attack with next) if that reference is cheap; and, on the subset
where two targets have EQUAL power/toughness and different text (n
reported), P(picks the keyworded one).
Readings: **size-aware** if P(largest) − 1/k is clear above 0 (bootstrap
CI); **text-aware on equal-stat targets** if the keyworded-target rate is
clear above 0.5 — if n < 30 write "not testable at this n" and stop.
Cannot: say anything about non-creature targets.

## P3 — instant-speed play (behaviour counter)

Over the 7d1b CP7 recording (reference) and fresh 8-game argmax recordings
of DIM and of the heuristic on Dimir: for every instant cast, was it cast
at instant speed (opponent's turn / in response, from the consult's
step/active fields) or at sorcery speed in a main phase? Report the
instant-speed fraction with Wilson for CP7, heuristic, DIM. Reading: DIM is
"instant-aware" if its fraction is clear above the heuristic's; the CP7
number is the reference, not a bar. Cannot: distinguish "held it on
purpose" from "had no mana"; small n on 8 games (say the n).

## P4 — linear probes on the entity tokens

Encode the W0Base + Dimir consult sets with each subject's encoder and
collect the entity-token vectors for battlefield creatures (WIRE §2d rows)
with labels from the corpus: has-flying, has-lifelink, has-first-strike,
any-keyword (binary), power bucket, toughness bucket. Train an L2 logistic
probe per label (5-fold CV over consults, not rows), report balanced
accuracy with CI, for `init`, C1s0, L0, BC, DIM. The raw wire row (before
the encoder) is the second control: what the input already exposes.
Readings, per label class: training **erases** keyword information if a
trained subject's balanced accuracy is clear below `init`'s; **preserves**
if overlapping; **sharpens** if above. Note whether the raw wire row already
carries keywords (if the wire has no keyword field and the probe is at
chance on the raw row, then the only route is the card embedding — say so).
Cannot: linear decodability is not use.

## Deliverables

Scripts under `rl/probes/` (`cardswap.py`, `target_probe.py`,
`instant_speed.py`, `token_probe.py`), artifacts under
`rl/artifacts/v7/9/`, one V7-VALIDATION.md section per probe with the table
and the pre-registered reading, a closing "Phase 9 verdict" paragraph that
answers the user's question in two sentences with the numbers, a dated
UPDATE line + §N prompt in rl/HANDOFF-V7.md. Order: P1 (deciding), P4, P2,
P3. If a probe cannot be built in two attempts (an identity field that is
not swappable, a missing corpus attribute), record why and move on.

## STATE (append dated lines; newest last)
- 2026-09-14 (start): nothing running; P1 not started.
- 2026-09-14 (P1 DONE): rl/probes/cardswap.py + run_p1.sh; artifacts rl/artifacts/v7/9/ (pairs 19/12/6/120, cardswap_<subject>.tsv, cardswap_summary.txt). Result: every identity swap class at floor in every subject (text dp <= 0.00004, pt <= 0.00002, cost <= 0.00004, type <= 0.00014; strict argmax flips 0/all), 219/219 different-card same-row SPELL pairs tied to <1e-4; mechanism = the refers_to attention bias never left its zero init (<= 0.0027). Reading "identity-blind" (pre-registered ratio void: the PT control is at floor). Section "9 / P1" in V7-VALIDATION.md. Next: P4.
