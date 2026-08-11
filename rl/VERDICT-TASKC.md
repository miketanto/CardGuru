# VERDICT — Task C (the graph A/B)

## The answer to the question we asked

**The knowledge graph does not buy zero-shot win rate at this task
depth.** The spec's decision rule (E2 > E0 by CI-excluded margins on
>=2/3 holdout decks, or 2x faster recovery) was not met. Parity was
listed in the spec as "also a real answer," and it is the answer.

## Why - and what it actually teaches

The holdout decks are functional ANALOGS of trained decks, and the
base candidate features (mana value, stats, card type) already carry
archetype play across analogs: both arms keep ~90% of their
in-distribution strength on holdout burn/midrange with identity
features that are respectively noise (E0) and semantics (E2). At this
depth, MTG-vs-a-heuristic is played on curve-and-stats, not on card
identity. Identity should start to matter when the OPPONENT punishes
mechanical misreads (counterspell timing, edict edges, death triggers)
- i.e., against deeper opposition, not deeper decks. This mirrors the
Task D conclusion: opponent depth, not card-pool sophistication, is
the binding constraint on every measurement so far.

## What the graph DID buy (robust, unplanned findings)

1. **Determinism of transfer.** E2's holdout-control results are
   nearly identical across seeds (.235/.245/.235); E0's are a lottery
   (.205/.455/.215). If you need predictable behavior on unseen cards
   - and any deployed system does - the graph delivers it and the
   hash cannot.
2. **Half the freeze rate.** E0 stalls out (endless passing) in 15.5%
   of holdout-control games vs E2's 7%. Unknown-hash candidates all
   look worthless, so passing wins the argmax; graph features keep
   novel cards playable. This is the concrete, mechanical form of
   "the graph understands the card."

Both effects are exactly what the fingerprint/answer-class work
predicted qualitatively: the graph's value is in knowing WHAT a card
is when experience is absent - which shows up first as variance and
liveness, not as mean win rate against a shallow floor.

## Recommendation

1. **Stop scaling this ladder.** E1 (flat mechanical features without
   graph relations) would measure nothing new at this depth; a GNN
   state encoder likewise (VERDICT-DIMIR: flat state already beats
   this opponent).
2. The next informative experiment is **opponent depth**: self-play
   or an MCTS/search opponent that punishes mechanical mistakes. Rerun
   THIS SAME A/B there; the prediction (from findings 1-2) is that the
   consistency and liveness gaps widen into a win-rate gap.
3. Meanwhile the graph's proven, shippable value remains on the
   search/analysis side (fingerprints, answer classes, deck-breaking)
   - which never depended on this A/B.

## Cost ledger

~11,000 games, 2 arms x 3 seeds x 1344 episodes + 5,400 eval games +
768 fine-tune episodes, ~5 hours wall-clock on 4 cores, chunked with
zero lost work across 3 harness incidents (all caught by the
verify-rows/dead-server guards added mid-run).
