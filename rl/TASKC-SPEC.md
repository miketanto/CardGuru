# Task C spec — the graph A/B (draft for review)

## The question

Does the CardGuru knowledge graph make an RL agent better at MTG in the
only regime where an encoder can matter: **cards it never trained on?**

Tasks A/B/D established that the stack learns and that E0 (name-hash
identity) reaches competence in 256-768 episodes on ANY fixed deck —
real or synthetic. On a fixed pool the name-hash IS a per-card learned
embedding, so a graph encoder cannot win there by construction. The A/B
must therefore be run where identity memorization is impossible.

## Arms

Identical everything — PPO hyperparameters, harness, HeuristicPlayer v2
opponent, seeds, eval blocks — except the per-candidate feature vector:

| Arm | Card identity features | Source |
|---|---|---|
| E0 (control) | 16-bucket name hash | current encoder, unchanged |
| E2 (treatment) | mechanical feature vector | CardGuru Forge ability graph |

E2 feature sketch (per card, ~32-64 dims, all derivable from the
existing graph): effect-class one-hots (counter/removal/edict/burn/
draw/recursion/pump/tutor), target-domain flags (creature/player/any/
noncreature-spell), trigger axes (on-death/on-cast/on-attack/on-etb),
static axes (anthem/cost-mod/prevention), zone deltas, and the
threat_profile bits (uncounterable, phase-shifter, recursion-engine).
No text embeddings, no learned card vectors — pure graph readout, so
the ablation isolates the graph's contribution.

## Protocol

1. **Training pool**: N mirror-match decks (start N=4: burn, the bench
   control list, Dimir Midrange v2, one aggro-midrange list), cards
   partitioned so a HOLDOUT set (~20 cards spanning the same effect
   classes) never appears in any training deck.
2. **Train** each arm x 3 seeds, interleaving decks per episode, to a
   fixed budget (2048 episodes — 2-4x the Task D competence point).
3. **Eval axes** (both arms, argmax, fixed seed blocks):
   a. **In-distribution**: held-out eval seeds on training decks —
      expect parity (sanity check, and evidence the arms are matched).
   b. **Zero-shot**: decks built from HOLDOUT cards (same archetypes,
      swapped functional analogs, e.g. Doom Blade for Shoot the
      Sheriff). The headline: E2 zero-shot win rate - E0 zero-shot
      win rate, 500 games/deck with CI.
   c. **Few-shot recovery**: fine-tune each arm 128 episodes on the
      holdout deck; episodes to recover in-distribution win rate.
4. **Decision rule**: the graph "pays rent" if E2 beats E0 zero-shot by
   a CI-excluded margin on >=2 of 3 holdout decks, or recovers in
   <=half the episodes. Parity everywhere = the graph adds nothing at
   this task depth (also a real answer — it would redirect effort to
   search/analysis uses of the graph).

## Build list (only new work)

- E2 feature extractor: CardGuru graph -> per-card static feature file
  (JSON), loaded by StateEncoder; hash buckets replaced by the vector.
  The Java side reads a file; no new IPC.
- Holdout partition tool: pick functional analogs from the graph so
  holdout decks stay archetype-equivalent (the graph itself selects
  the swaps — a nice dogfood).
- Deck files for the training pool + holdout variants.

Everything else (RLPlayer, driver, policy server, chunk scripts,
confirmation protocol) is frozen and reused.

## Cost estimate

Dimir-speed games (~0.3-0.8/sec) x 2 arms x 3 seeds x 2048 episodes +
evals ≈ 1.5-2 days of wall-clock on this 4-core box, chunked the same
way Task D was. Feasible but the first multi-day run of the project —
worth confirming the spec before starting.

## Open questions for review

1. Holdout composition: strictly functional analogs (clean, narrow) vs
   including genuinely novel effects like Rooms (harder, more honest)?
2. Is 3 seeds/arm enough for the first pass? (5 doubles the cost.)
3. Should E1 (flat mechanical features WITHOUT graph relations) run as
   a third arm to separate "any mechanics beat hashing" from "the
   graph's relational structure matters"? Adds ~50% cost but makes the
   attribution airtight.
