# Answer frames, timing windows, and the deck-fingerprint proposal

Session notes, 2026-08-07. Companion to
[generalized-discovery.md](generalized-discovery.md); records what the
KG-improvement session built, the conceptual gap it exposed, and the design
direction agreed for the next phase.

## What was built (all pushed, 79 tests green)

- **Texture-based gameplans** (`a196a6a`): `control` and `ramp_aggro` join
  the gameplan taxonomy. They are invisible to synergy-hook voting (control
  decks are deliberately low-synergy), so they score from deck *texture* —
  answer density + card-advantage engines for control, ramp + top-end mass
  for ramp_aggro. Jeskai Lessons reclassified graveyard→control, Selesnya
  Gearhulk engine→ramp_aggro; each gets DISRUPTION guidance (hand attack and
  uncounterable threats derive Commence the Endgame against UB control).
- **counter_spell answer class** (`a196a6a`): the stack window is now an
  answer class in `find_answers`, with `_counter_target_legal` evaluating
  ValidTgts as stack restrictions — type gates (Annul), cmc gates
  (Disdainful Stroke), color gates (Flashfreeze), soft counters (UnlessCost
  → conditional), and threat-side uncounterability (Surrak-style R:Counter
  CantHappen → excluded).
- **Recursive-threat profiling** (`eb11884`): threats with self-return death
  triggers (the Enduring cycle: `T:ChangesZone Battlefield→Graveyard
  ValidCard Card.Self` chaining to `ChangeZone →Battlefield`) or
  Persist/Undying demote destroy/damage/edict answers to conditional
  ("returns when it dies — prefer an exile effect"). `ReplaceDyingDefined`
  riders (Combustion Technique) are recognized as clean kills. XMage
  receipt: Doom Blade kills Enduring Curiosity; it returns as an enchantment.
- **Stack-window contests** (`eb11884`): opposing decks are scanned for
  cards that *grant* uncounterability to other spells (Mistrise Village's
  `ReplacementEffects$ AntiMagic` effect) vs cards that are themselves
  uncounterable — the counter class's own answer-window analysis.
- **Battlefield target legality** (`daa064b`): `_battlefield_target_legal`
  evaluates removal ValidTgts restriction vocabulary — type heads, `+`/`.`
  conjunctions, comma alternatives, power/toughness/cmc gates,
  withFlying/withoutFlying, controller words, situational words
  (attacking/tapped → conditional). Unknown vocabulary degrades to
  conditional, never to a confident verdict. Kills the Aerial
  Predation / Arbor Colossus false-positive class.

## The conceptual finding: taxonomic vs ontological gaps

The counter_spell class exists because a human noticed Annul and Disdainful
Stroke were missing from answer output. Post-mortem: this was **not a data
gap**. `SP$ Counter | TargetType$ Spell` is one of the tightest structural
clusters in the dataset, and the gap miner would have proposed
"counterspell" as a concept in its first sweep. What the pipeline could not
do is connect that concept to the *answers task* — realize that "counter
target spell" occupies the same functional slot as "destroy target creature"
when the question is "how do I beat this threat."

Two distinct gap kinds, only the first of which is currently automated:

1. **Taxonomic gap** — a structural cluster no concept explains.
   `gaps.py` mines these (bottom-up, mechanism-level).
2. **Ontological gap** — an induced concept with no mapping to a task role.
   The answer taxonomy (`ANSWER_QUERIES`) is a hand-written intensional
   list; nothing tasks the system with asking whether an induced concept
   belongs in it. The graph encodes what cards *do*, not what doing that is
   *for*.

Three routes to closing ontological gaps autonomously, in rising cost:

- **Lifecycle-frame induction on the graph** (cheapest): classify every
  effect by which zone-transition edge of a threat's lifecycle it cuts
  (Hand→Stack→Battlefield, plus back-edges like Graveyard→Battlefield).
  "Answer" becomes one abstract concept — *an edge cut on the threat's
  zone trajectory* — and discard, counter, removal, and exile-vs-recursion
  all fall out of one rule.
- **Extensional task definitions via the engine**: define the answers task
  by an outcome predicate ("any card whose play yields an engine state
  where the threat is not in play") and search card space against it in
  XMage, with the concept layer pruning. Essence Scatter falls out
  automatically; verification infrastructure inverted into discovery.
- **Functional clustering from usage**: with a decklist corpus, cards that
  co-occupy sideboard slots against the same matchups reveal functional
  equivalence distributionally. (No decklist corpus wired in yet.)

## History matters, not just state

Two refinements from discussion that any lifecycle model must encode:

- **Triggers fire on history, not state.** Countering Enduring Curiosity
  and Doom-Blading it both end with the card in the graveyard, but "when
  this **dies**" means battlefield→graveyard specifically; the countered
  spell never lived, so the return trigger never existed. Counter > destroy
  against the Enduring cycle for a reason derivable from edge history.
  The invariant to track is *which edges were traversed*, not final zone.
- **Edge cuts have cost profiles.** Hand attack: proactive, full
  information, your schedule, but decays to topdecks. Counter: permanent
  and history-clean, but reactive, holds mana on their schedule, and is
  the one window an opposing permanent can close (Mistrise). Battlefield
  removal: most flexible window, but leakiest — ETB value already banked,
  recursion makes it rental. Each cut needs annotations: when you must
  act, what you know then, what value the threat already extracted,
  whether the cut is permanent.

## Proposal: per-deck fingerprint graphs

Direction agreed in discussion (not yet built): project the global KG onto
one deck and keep only intra-deck structure — a causal "what makes this
deck run" graph.

- **Nodes**: the deck's cards, weighted by expected availability (copies,
  cost). A commander is a hub with availability ~1.0 — why Commander decks
  are the legible test bed.
- **Typed edges** minable from existing hooks: *enables* (ramp→payoff),
  *feeds* (cheap evasive bodies→Curiosity draw trigger), *protects*
  (Mistrise→key spell), *recurs*, *tutors*, *pays off*. The synergy-hook
  detector already finds the pairwise raw material; the fingerprint is the
  assembled network rather than a summed score.
- **Analysis = graph theory**: betweenness centrality → linchpins; min-cut
  between resource sources and win conditions → the incisive answer;
  parallel-path counts → redundancy (a killable linchpin only matters if
  the deck can't route around it). Output changes class: not "what kills
  card X" but "*which* card needs killing" — currently hand-artisanship in
  sideboard guides.
- **Timing layer**: each node carries exposure windows (hand/stack/
  battlefield/graveyard) with the cost profiles above; window state is
  modified by other nodes (recursion leaks the battlefield window, Mistrise
  closes the stack window). Break-the-deck query: for each high-centrality
  node, find the cheapest window where interdiction is *permanent*, match
  the user's card pool to that window.
- **Receipts via engine ablation**: goldfish the deck N times in XMage,
  re-run with a candidate linchpin neutralized, measure kill-turn
  degradation — empirical centrality (lesion study), validating the
  graph's load-bearing claims exactly as scenario receipts validate
  card-level claims. (Ablation importance already prototyped at deck level
  in generalized-discovery.md; this extends it to fingerprint validation.)
- **Known challenges**: emergent resources (board width, mana float, life)
  are not nodes in card text; some cohesion is statistical (curve, land
  count), not mechanical; 60-card availability makes centrality fuzzier
  than singleton-plus-commander.

**First increment built** (`cardguru/fingerprint.py`, `cardguru
fingerprint --list decks/dimir_deck.txt`): nodes weighted by copies, edges
from hook complements (enabler→payoff), Brandes betweenness + weighted
degree, sole-provider detection (min-cut lite: dependencies with no
parallel path), and a break plan attaching exposure windows + preferred
interdiction to each linchpin.

Result on live Standard Dimir Midrange: top linchpin **Enduring Curiosity
x4** (score 24, next card 13); spine `combat_damage_matters` — Deep-Cavern
Bat and Flitterwing Nuisance feed its draw trigger; break plan says AVOID
battlefield-destroy (Enduring recursion → rental), preferred cut **stack
(counter)**, with exile-class removal as the battlefield fallback — piping
the linchpin into `cardguru answers` lists the concrete cards (exile
effects and exile-rider burn YES, all 735 plain destroys demoted). This
matches expert consensus on the matchup, derived with zero deck-specific
code. Golden tests: `tests/test_fingerprint.py`.

Found and fixed en route: the reanimator hook detector counted
self-return death triggers (Enduring cycle) as "reanimator wants fodder";
now a return executed by a `ValidCard Card.Self` trigger is recursion, not
a reanimation hook — the false `reanimator` spine family disappeared from
the Dimir fingerprint.

**Second increment — the Kaito/Sheoldred's Edict derivation.** The user
named the real matchup answer (Sheoldred's Edict) and asked whether the
system could have found it. Post-mortem: every needed fact was one S node
Forge already encodes —

    S:Continuous | Affected Permanent.Self+counters_GE1_LOYALTY
      | Condition PlayerTurn | AddType Creature & Ninja
      | RemoveCardTypes True | AddKeyword Hexproof

— but threat_profile only read K nodes, so conditionally self-granted
hexproof and phase-dependent types were invisible. Now implemented:

- `self_statics` in threat_profile capture conditional self-grants;
- targeted-removal evaluation is per-phase: creature removal vs Kaito =
  "no open targeting window" (hexproof creature on their turn, not a
  creature on yours); planeswalker-capable removal = "YOUR turn only";
- edicts extended to modal/untargeted forms (Charm nodes with
  `Defined$ Opponent` + `SacValid`), per-mode class precision, and
  find_answers takes a modal card's BEST mode;
- fingerprint deck-context sharpening: a class-restricted edict is a
  GUARANTEED hit when the linchpin is the deck's only card of its class —
  Kaito's break plan now reads "preferred cut: edict/sacrifice", with
  Sheoldred's Edict's SacPW mode the canonical instance.

The general lesson repeats the Annul one at the state level: the profile
was *state-static* while the card is *phase-dependent*. Timing is not an
annotation on answers only; threats have time-varying shapes, and windows
must be evaluated per phase. Known residual: ninjutsu (empty K node)
bypasses the stack window, so "counter it" overclaims vs a ninjutsu
deployment; keyword-param parsing for ninjutsu is future work.

Still open from the proposal: timing-annotated edges, engine-ablation
receipts (goldfish with linchpin neutralized), emergent-resource nodes,
and the Commander-deck run where availability weighting matters most.

## Open work / recoverable state

- **Induction sweep 3 partially complete**: 5 of 7 concept drafts done and
  cached (forced_attack_static, cant_block_drawback, creature_class_anthem,
  cost_taxer, phase_life_drain — each with examples and a counterexample);
  2 drafters (CantBeCast locks, library-play engines) and all 7 validation
  gates never ran. None registered yet. Resume:
  `Workflow({scriptPath: <scratchpad>/induction_sweep3.js,
  resumeFromRunId: "wf_dfc75874-728"})` — or validate the 5 inline.
- Backlog carried from generalized-discovery.md: S:Continuous sub-signature
  refinement; amplifier/cost-reducer modeling in the goldfish sim.
