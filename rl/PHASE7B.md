# Phase 7b — optimistic Elo self-play league, scratch line to 9216 episodes

Continuation of PHASE7-SCRATCH.md at the user's direction: "a longer
budget and a league that is optimistic Elo based self play." Same
scratch lstmattn line (no BC, no teacher, ever), same growth benchmark
(100g vs D0/D1/D1h per checkpoint, logistic-MLE Elo on the Phase 6
scale, D0=1000).

## League design

- **PFSP opponent selection** (rl/pfsp_pick.py): every pool member
  carries an Elo (pool_elo.tsv); each 64-episode chunk samples an
  opponent with weight exp(-((elo_opp - (self+100))^2)/(2*150^2)) +
  .02 floor — mass on opponents ~100 Elo ABOVE the agent's current
  rating. Snapshots enter the pool at their checkpoint rating (or the
  self-Elo estimate when snapshotted between ratings, P7_SNAP <
  P7_RATE). Encoding-family filter: only cdim-91 arches may seat
  (the driver's candidate encoding is global per JVM).
- **Phase 9 fast path** from episode ~2400: persistent driver JVM,
  4 concurrent games/chunk with per-worker opponent connections
  (EpisodeRunner ThreadLocal oppPolicy + policy_server --threads 4),
  ParallelGC. In-chunk throughput ~25-30 eps/min, ~3.5x the mvn path.
  Elo probes stayed sequential for curve comparability.

## The full curve (one seed, scratch lstmattn, BPTT recurrent PPO)

| trained | Elo | vs D0 | vs D1 | vs D1h | era |
|---------|-----|-------|-------|--------|-----|
| 0    | 46   | .00 | .00 | .00 | random init |
| 256  | 456  | .05 | .03 | .02 | mixed rotation |
| 512  | 867  | .35 | .20 | .23 | mixed rotation |
| 768  | 889  | .36 | .22 | .27 | mixed rotation |
| 1024 | 916  | .43 | .25 | .26 | mixed rotation |
| 1280 | 976  | .48 | .33 | .36 | PFSP |
| 1536 | 1002 | .56 | .37 | .34 | PFSP - passes D0, e0_bc |
| 1792 | 1014 | .57 | .37 | .37 | PFSP |
| 2048 | 1022 | .58 | .38 | .38 | PFSP |
| 2304 | 1068 | .63 | .47 | .43 | PFSP - passes all attn champs |
| 2560 | 1065 | .63 | .44 | .44 | PFSP |
| 4096 | 1093 | .64 | .47 | .52 | fast path - passes e0_champ |
| **6144** | **1101** | .67 | **.50** | .49 | **peak - parity with D1** |
| 8192 | 1085 | .69 | .42 | .47 | plateau |
| 9216 | 1044 | .62 | .40 | .38 | **late drift** |

**Champion: ck_6144 (p7b_champion.pt), Elo 1101** — parity with the
D1 search instrument (.50 head-to-head), .67 vs D0, above every
learned agent in the project (e0_champ 1083, attn_desp 1053, attn_bc
1044). A random-init net reached the teacher tier in 6144 episodes
without a single teacher label. Its benchmark-seed game vs D0 is a
turn-9 kill (22 actions, curve-out + ninjutsu + instant-speed
removal); transcript_champion6144.txt.

## PFSP effect

Slope in the 512 episodes before PFSP: +49 Elo. In the 512 after:
+86. The optimistic ladder (exploiter and champions at the +100
target) broke the 1022 stall and carried the line from 916 to 1101.
Chunk batch win rates vs the champions moved from ~.10 (rotation era,
too-wide gap) to .12-.44 (PFSP era) — the gap the agent trains
against is the design variable that mattered most in this project.

## Blocking (measurement correction, then a finding)

Earlier reports claimed the agent "never blocks" — a log-parsing
artifact (XMage logs blocks as "Attacker: X blocked by Y" without
naming the defender). Corrected audit at 2432: the current net
blocked 41% of attackers faced in mirror games vs its 128-episode-old
snapshot's 12% — blocking emerges and accelerates exactly when the
PFSP pool becomes self-dominated. Racing vs D0 (where its clock is
faster) is selective, not pathological. A logged self-mirror
(selfmirror_2432.txt) shows gang-blocks, chump-blocks, deathtouch
manland defense, and instant-speed threats in the opponent's upkeep.

## Late drift — the run's cautionary finding

After 6144 the curve flattens then falls (1101 -> 1085 -> 1044).
Head-to-head confirms genuine regression, not anchor-blindness: the
9216 net loses to ck_6144 **16-24 (.40) over 40 games**. Diagnosis:
once the agent outrated everything external, the +100 optimism target
pointed above the whole pool, sampling collapsed onto its own
near-equal snapshots (some entering at estimated ratings), and
anchor-relevant skill decayed while it chased mirror minutiae —
textbook self-play drift with no gating.

The AlphaStar-style fixes, in order of leverage, all supported by
infrastructure that already exists:
1. **Champion gating**: only promote a snapshot into the pool (or to
   "current best") if it beats the reigning champion head-to-head —
   would have frozen ck_6144's line instead of drifting past it.
2. **Fresh exploiters** trained against the current champion, entering
   the pool at its level (exploiter_lane.sh, needs an attn-family
   target run).
3. **Archetype opponents** (the Phase 7c curriculum session) —
   external pressure self-mirrors cannot supply.
4. A small **anchor fraction** (1 chunk in 8 vs D1h) as cheap drift
   insurance.

## Infrastructure this phase hardened

- Per-worker opponent connections -> concurrent rl-vs-rl (the perf
  report's "obvious next step", done and validated: contiguous episode
  splice, one PPO update per 32 episodes, BPTT intact).
- Atomic checkpoint saves (a SIGKILL mid-torch.save corrupted net.pt
  and cost 448 episodes; tmp+os.replace makes it impossible).
- Orphan-port cleanup at lane start; encoding-family guard in the
  picker; P7_RATE/P7_SNAP decoupling (dense ladder, sparse ratings).

## Artifacts

rl/artifacts/tmp/rl_p7_lstmattn_s0/: p7b_champion.pt (= ck_6144),
p7_final.pt (9216, kept for the drift record), full snapshot pool,
elo_curve.txt, elo_matches.tsv, pool_elo.tsv, train.csv, transcripts
(per-checkpoint, champion, self-mirror), h2h_9216_vs_6144.txt.
