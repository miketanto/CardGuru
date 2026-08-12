# Phase 8 kickoff — zero-shot transfer of the graph-feature (E2) net to unseen-but-similar cards

You are continuing the CardGuru MTG-RL research project. Work on branch
`claude/cardguru-phase-5-kickoff-2usq4s` of miketanto/CardGuru (or a
fresh branch from its head if instructed). Commit and push after every
milestone. Read `rl/RESEARCH-REPORT.md` first for the project arc, then
`rl/PHASE6-ELO.md` (metric) and `rl/PHASE5-M3.md` (novelty precedent).

## The question

Our E2 encoding represents each card as a 91-dim mechanical feature
vector read off the CardGuru ability graph (`rl/e2_extract.py`) — no
name identity, no text embeddings. If that representation is doing its
job, a policy trained on it should **transfer zero-shot to cards it has
never seen** whose feature vectors are similar (a different 2-mana
counterspell, a different flash threat, a slightly different removal
spell). The name-hash E0 encoding cannot do this by construction. Test
it.

## Environment setup (fresh container)

1. XMage engine: clone pin `7554968c` into `/home/user/mage`, overlay
   the committed mirrors `rl/xmage-src/` (into
   Mage.Tests/src/test/java/org/mage/test/rl/) and
   `benchmark/xmage/src/` (players into Mage.Sets or the module the
   originals live in — follow the paths recorded in
   `rl/PHASE5-C0.md`), then `mvn -pl Mage.Tests test-compile` (needs
   `-Dfile.encoding=UTF-8`).
2. Python: torch installs from PyPI (pytorch.org is proxy-blocked).
3. `bash rl/restore_artifacts.sh` — restores checkpoints, datasets,
   curves to /tmp.
4. Smoke: serve a checkpoint with `rl/policy_server.py` and run a
   4-episode eval via RLEpisodeDriver before anything long.

## Subject and controls

- **Subject**: `attn_desp` = /tmp/rl_c6_attn_s7/attn_desp_final.pt
  (arch `attn`, cdim 91, our best graph-feature agent, Elo 1053).
  Also run `attn_bc` (/tmp/rl_p5_c1/student_e2attn.pt, 1044) to check
  the result isn't specific to one checkpoint.
- **Negative control**: `e0_champ` = /tmp/rl_league_bc_s0/
  e0_league_final.pt (arch `e0`, cdim 38, name-hash buckets, Elo 1083).
  Unseen names hash to arbitrary buckets, so it should degrade — if it
  transfers just as well, the graph features aren't the reason for
  anything.
- **Rulers**: D0 (`-Drl.opponent=heuristic`) and D1
  (`-Drl.opponent=search -Drl.searchPlies=1 -Drl.searchBreadth=8`)
  are encoding-blind Java seats — they play the swapped decks natively
  and anchor every comparison.

## Experimental design

1. **Build swap decks.** Start from BenchDimir.dck (the training deck).
   Create 3 variants, each replacing 8–12 cards with *functionally
   similar but unseen* cards (similar mana value, role, and feature
   vector; verify the replacements appear in nobody's training data —
   the training deck list and the M3 deck pool in `rl/m3_decks.py` are
   the exclusion list). One variant should swap the interaction suite
   (counterspells/removal), one the threats (including flash threats),
   one mixed. Cards must exist in the XMage pin AND in
   `data/dataset.jsonl.gz`. `rl/holdout_pick.py` may already implement
   similar-card selection — read it before writing a new picker;
   feature-space nearest-neighbor over e2 vectors is the intended
   notion of "similar".
2. **Regenerate features**: `python3 rl/e2_extract.py --out
   rl/e2_features.tsv` covers every dataset card, so new cards get
   rows automatically. Confirm each swapped card has a row (a missing
   row silently becomes the unknown-flag vector and would fake a
   transfer failure).
3. **Calibrate the deck**: 200g D1-vs-D0 on each swap deck (both seats
   scripted). If a variant's D1 win rate departs wildly from .614 the
   deck's power level shifted — rebalance the swaps until the scripted
   game looks similar, otherwise policy deltas confound with deck
   deltas.
4. **Zero-shot eval**: each policy × each deck (original + 3 variants)
   × {D0, D1}, 200g, argmax, `-Drl.noYields=true`,
   `-Drl.consultBudget=4000`, fixed eval seed per deck. Report the
   **transfer delta**: (win rate on variant) − (win rate on original),
   per policy. The hypothesis: attn deltas ≈ 0 ≥ e0 deltas ≪ 0.
5. **Optional follow-up** (only if zero-shot shows signal): 256-episode
   fine-tune of attn_desp on the mixed variant vs D0-probe curve, to
   measure adaptation speed vs from-scratch.

## Operational rules (hard-won — do not relearn these)

- mvn: `mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver'
  -DargLine="-Dfile.encoding=UTF-8 -Xmx4500m" -DfailIfNoTests=false`,
  simple class names only.
- Serve cdim-91 policies with `--arch attn --cdim 91` and pass
  `-Drl.cardFeatures=/home/user/CardGuru/rl/e2_features.tsv`; e0 with
  `--arch e0 --cdim 38` and NO cardFeatures flag.
- Foreground commands ≤590s; anything longer runs as a harness-tracked
  background task (never detached daemons). pgrep/pkill patterns must
  bracket a letter (`policy_serve[r]`) or they match themselves.
- Kill servers between matches; on "Address already in use" wait and
  retry the bind (see serve() in rl/elo_tournament.sh for the pattern).
- Delve/graveyard-recursion cards explode `getPlayable` → OOM (Gurmag
  Angler incident, PHASE5-M3.md). Avoid delve/escape/flashback-heavy
  swaps or budget-test them at 4 episodes first.
- 100g probes flatter by up to ~.07 vs 500g; use ≥200g for claims.
- D0 is frozen (v3 instruments) — never retune it.
- Report at every milestone with data tables; commit + push docs to
  `rl/PHASE8-*.md`.

## Deliverable

`rl/PHASE8-TRANSFER.md`: swap-deck lists with feature-distance of each
replacement, calibration table, the policy × deck win-rate matrix,
transfer deltas with the e0-vs-attn contrast called out, and a verdict:
do graph features buy measurable zero-shot transfer, yes or no, at what
confidence.
