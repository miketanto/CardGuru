# IDEA — 17Lands replay data as an imitation prior (parked, 2026-09-15; not started)

Raised by the user while Phase 13's recording ran. Parked until Phase 13
(CP7 clone + training against CP7) is finished. Nothing downloaded.

## What the data is (checked 2026-09-15)

17Lands public datasets (`https://17lands-public.s3.amazonaws.com/analysis_data/`),
column definitions in `helper_files/replay_dtypes.py`:

* **Replay data** — per game: metadata (expansion, event type, rank, user
  win-rate and games-played buckets), the user's full deck (`deck_*`), cards
  drawn (`drawn_*`), opening hand, mulligans (both players), on the play, turns,
  result; **per turn, for both players** (`{user|oppo}_turn_N_*`): cards drawn /
  discarded / tutored, lands played, creatures cast, non-creatures cast,
  instants and sorceries cast, creatures attacked / blocked / unblocked /
  blocking, combat damage taken, creatures killed (combat / non-combat), mana
  spent, abilities activated, end-of-turn hand / lands / creatures /
  non-creatures / life / poison.
* **Not recorded:** order of plays within a turn, targets, which blocker took
  which attacker, the step an instant was cast in (only whose turn), the
  opponent's hidden hand and library.
* Sizes (PremierDraft, compressed): DSK replay 570 MB / game 77 MB; FIN 452 / 65;
  ECL 307 / 43; FDN 438 / 60; MKM 557 / 76. Very wide CSVs — parse in chunks on
  the 11 GB box.
* Most of BenchDimir's cards come from sets 17Lands covers (DSK, FIN, MSH, ECL);
  the pinned XMage implements every recent set checked (Foundations, Bloomburrow,
  OTJ, MKM, LCI, WOE, Aetherdrift, Tarkir Dragonstorm, Edge of Eternities, Final
  Fantasy, Spider-Man, Avatar, Lorwyn Eclipsed; Duskmourn via BenchDimir's cards).
* **License / terms: not verified** (the terms page is JavaScript-rendered). Check
  before building on it.

## How it could be used

Reconstruct each game in XMage for the user's seat: build the logged deck, stack
the library in the logged draw order (exact draws), give the opponent its
observed cards plus filler and force its logged plays, and at each decision pick
an option consistent with what the user did that turn (set-valued labels where
the order is ambiguous; block assignment inferred by matching the logged combat
results). Compare the rebuilt end-of-turn state with the log every turn and keep
each game only up to its first mismatch — a built-in faithfulness metric.
Labels: card-level land / spell / attack / block / hold decisions by strong
humans (filter by win-rate bucket and rank), in the same per-candidate BC format
as Phase 13.

## The question it answers

Does Limited play teach card understanding and play patterns that transfer to
constructed? Expected to transfer: card function (removal on threats, holding
instants, trades and blocks), curve / sequencing / race-vs-block patterns, and
the shared card embedding; expected not to: card valuation (power level differs
by format), deck-level synergy and constructed pace. Test, to be pre-registered:
pre-train on 17Lands labels, then run the Phase 13 constructed pipeline (CP7 clone
→ training vs CP7) against the same pipeline without pre-training, on the
constructed yardsticks (sampled / two-stage levels vs CP7 and the heuristic), the
card-swap probe and the Dimir card-habit census.

## Feasibility spike (when un-parked; CPU-only)

1. With permission: download `game_data_public.DSK.PremierDraft.csv.gz` (77 MB);
   measure the share of top-bucket games whose full decks exist in XMage.
2. Download `replay_data_public.DSK.PremierDraft.csv.gz` (570 MB); rebuild 200
   games; report turns matched before the first mismatch and labels per game.
3. Go / no-go: most games rebuild cleanly for ≥ 8 turns → build it properly.
Risks: weeks of engineering; Limited (40-card) vs constructed; Arena-only
(rebalanced / Alchemy) cards must be filtered.
