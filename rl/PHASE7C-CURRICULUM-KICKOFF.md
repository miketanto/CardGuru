# Phase 7c kickoff — archetype-curriculum league (deck variety, slowly introduced)

You are a sibling session of the CardGuru MTG-RL project. Question:
does gradually widening the OPPONENT DECK POOL across archetypes make
the agent robust — specifically, does it force the skills the Dimir
mirror never demands (blocking, playing around sweepers, respecting
different clocks)? Work on branch `claude/cardguru-deck-curriculum`
(branch from the head of `claude/cardguru-phase-5-kickoff-2usq4s`);
commit+push there after every milestone; never push to the phase-5
branch.

Read first: rl/RESEARCH-REPORT.md (project arc), rl/PHASE7-SCRATCH.md
(the agent you start from + league mechanics), rl/PHASE5-M3.md (the
novel-deck assets and the OOM lessons), rl/PHASE6-ELO.md (rating
protocol).

## Setup

1. XMage pin 7554968c into /home/user/mage + overlay rl/xmage-src/ and
   benchmark/xmage/src/ mirrors; `mvn -pl Mage.Tests test-compile`
   (-Dfile.encoding=UTF-8). torch from PyPI. `bash
   rl/restore_artifacts.sh`.
2. Starting agent: **/tmp/rl_p7_lstmattn_s0/p7_final.pt** (lstmattn,
   cdim 91, Elo 916 — the emergent scratch agent). This is a frozen
   artifact snapshot: the main session's PFSP run continues from the
   same point on the Dimir mirror, so your run is a clean A/B —
   same start, diversity-curriculum vs mirror-PFSP.
3. Training: `rl/league_lane_p7.sh` mechanics (BPTT recurrent PPO via
   policy_server.py, LR 3e-4, no yields, consultBudget 4000). You will
   extend the lane — see below.

## Curriculum design

- Agent always pilots BenchDimir.dck (keep the piloting task fixed;
  the variable is what it faces).
- Opponent pool = PFSP-style Elo-weighted sampling (rl/pfsp_pick.py,
  optimism +100, sigma 150) over rows that now carry a DECK as well as
  a kind: scripted seats (heuristic/search/searchhold) piloting
  archetype decks, plus the agent's own snapshots and the attn
  champions on BenchDimir (rows as in the main session's
  pool_elo.tsv — seed from rl/artifacts).
- **Introduce one archetype every 512 episodes**, easiest-first:
  pick 4-6 decks spanning real archetype axes — fast mono-color
  aggro, durdly control with sweepers/counters, midrange/ramp with
  big top-end, a flash/tempo deck — drawn from the M3 deck pool
  (`rl/m3_decks.py` regenerates the .dck files) or newly built from
  Standard-legal cards in the XMage pin AND `data/dataset.jsonl.gz`.
  HARD RULES from M3: no delve/escape (getPlayable OOM — Gurmag
  incident), no graveyard-recursion/token-copy engines, budget-test
  every new deck with 4 episodes before trusting it.
- On introduction, calibrate each new (seat, deck) row: 100g D1(deck)
  vs D0(BenchDimir)-style cross-calibration is overkill — a 100g
  match vs the CURRENT agent suffices to seed its pool Elo (fit with
  rl/elo_fit.py against the agent's known rating; recompute at each
  checkpoint anyway).
- Lane extension you must implement: pool rows
  `name|kind|deck|elo` where kind is `heuristic`, `search`,
  `searchhold`, or `rl:<arch>:<ckpt>`; the chunk driver invocation
  sets `-Drl.opponent=<kind> -Drl.oppDeck=<deck>` for scripted rows
  (check RLEpisodeDriver for the opponent-deck sysprop; add one if
  missing — mirror the Java change into rl/xmage-src/).

## Measurement

1. **Comparability curve**: every 512 episodes, the standard mini-Elo
   vs D0/D1/D1h on the BenchDimir mirror (100g each, seed 950000,
   argmax) — directly comparable to the main session's curve
   (46/456/867/889/916 at 0/256/512/768/1024).
2. **Robustness matrix**: every 512 episodes, 100g vs D0 piloting
   EACH introduced archetype. Report win rate per archetype over
   time — the curriculum's whole point is that these climb without
   the mirror rating falling.
3. **Behavior counters**: from the probe logs, track blocks-declared
   per game (grep the game logs for "blocks" attributed to the agent
   — add a driver counter if grepping is unreliable) and the standing
   flashThreats/oppTurn counters. The never-blocks hole is the
   headline metric: report it at every checkpoint.
4. Sample game per checkpoint (printGameLogs=true, 1 episode,
   transcript committed).

## Budget and cadence

3072+ episodes overnight. Checkpoint/report every 512. Commit curves,
checkpoints (final + pool), transcripts, and the deck lists to
rl/artifacts on your branch. Deliverable: rl/PHASE7C-CURRICULUM.md
with the growth curve, robustness matrix, blocking counter over time,
and a verdict: does deck diversity buy robustness the mirror can't,
and at what cost to mirror Elo?

## Operational rules (non-negotiable, learned the hard way)

- mvn: `-q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver'
  -DargLine="-Dfile.encoding=UTF-8 -Xmx4500m" -DfailIfNoTests=false`.
- Foreground <=590s; long work = harness-tracked background tasks;
  never detached daemons. pgrep patterns: `policy_serve[r]`.
- Server lifecycle per match; bind-retry on "Address already in use"
  (copy serve() from rl/elo_tournament.sh).
- D0/D1 are frozen instruments — never modify their decision logic.
- 100g probes flatter ~.07 vs 500g; phrase claims accordingly.
- Commit and push after every milestone; report with data tables.
