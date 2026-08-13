# Phase 7 — scratch lstm+attention vs the mixed league (no BC, no teacher)

User direction: keep lstm+attention for self-play, give it "the correct
opponents and a way to benchmark growth," and run the agent **from
random init** — no BC prior — "for it to explore completely."

## Setup

- Agent: lstmattn (429k params, transformer + LSTM state token, cdim 91
  E2 graph features), random init, **true-BPTT recurrent PPO**
  (episodes replayed as sequences, hidden carried, detached every 64
  steps — policy_server.py `_update_recurrent`), LR 3e-4 (no prior to
  protect), no shaping, no yields, no desperation.
- Opponents per 64-episode chunk: 75% own snapshot ladder (ck_N every
  256), 25% externals — attn_bc / attn_v2 / attn_desp champions + the
  Phase 6 exploiter. No BC anchor slot (nothing to anchor to).
- Growth benchmark: every 256 episodes, 100g vs each scripted anchor
  (D0/D1/D1h) → logistic-MLE Elo on the Phase 6 scale (D0=1000).
- Budget 1024 episodes (~1088 trained due to one restart-replayed
  chunk). Runner: `rl/league_lane_p7.sh` with P7_NOANCHOR=1.

## Growth curve

| trained | Elo | vs D0 | vs D1 | vs D1h | argmax opp-turn threat casts |
|---------|-----|-------|-------|--------|------------------------------|
| 0    | 46  | .00 | .00 | .00 | 0 |
| 256  | 456 | .05 | .03 | .02 | 0 |
| 512  | 867 | .35 | .20 | .23 | 0 |
| 768  | 889 | .36 | .22 | .27 | 0 |
| 1024 | **916** | .43 | .25 | .26 | **1** |

Phases visible in the curve and the per-checkpoint sample games (all on
the same eval seed):

1. **0–256: the passivity basin.** Argmax play = pass every window
   (the ck256 transcript shows 0 actions in 11 turns). Self-play vs a
   passive twin rewards passing; the only pressure came from the
   external-champion chunks (batch win rate .09–.13 vs attn_bc).
2. **256–512: takeoff (+411 Elo).** Curve-out aggro appears: 1-drop →
   3-drop → attacks, Map-token explores, instant-speed casts in its own
   upkeep/draw step, and — never taught anywhere — **Kaito ninjutsu**
   with follow-up emblem activations. Neither BC'd family ever found
   ninjutsu; it emerged from exploration against real opponents.
3. **512–1024: grind (+49 Elo).** Same game plan, executed tighter
   (ninjutsu turn 7 instead of 11; the final checkpoint wins the
   benchmark-seed game on turn 13, using Nowhere to Run as draw-step
   removal). Known holes at budget end: never blocks (pure race),
   over-activates Kaito's emblem, and opponent-turn casts are still
   essentially absent under argmax (one in 300 rating games).

## Verdict

- **Scratch + mixed league + BPTT works** — 46 → 916 Elo in 1024
  episodes is the fastest sustained climb of the project, and the
  mechanics it found (ninjutsu, instant-speed removal timing) include
  ones the D1 teacher never used. The user's exploration hypothesis is
  confirmed at the mechanism level.
- **It does not reach the teacher-seeded agents at this budget**: 916
  final vs e0_bc 995, attn_bc 1044, e0_champ 1083. The 512→1024 slope
  (+0.1 Elo/episode) says closing that ~130-point gap needs either a
  much larger budget, stronger mid-tier opponents (the gap between its
  snapshots and the champions is too wide to learn from efficiently),
  or a BC init — the deferred comparison arm
  (student_e2lstm_seq.pt, sequence-BC val .965) is staged for exactly
  that.
- League mechanics that mattered: the external-champion chunks broke
  the passivity basin (self-play alone plateaued the C5 scratch arms
  far lower); batch win rates vs its own ladder settling to ~.3–.4
  show genuine self-competition by the end.

## Artifacts

/tmp/rl_p7_lstmattn_s0/: p7_final.pt, pool/ck_{0..1024}.pt,
elo_curve.txt, elo_matches.tsv, per-checkpoint probe files and
transcript_{256,512,768,1024}.txt (all mirrored in rl/artifacts).
