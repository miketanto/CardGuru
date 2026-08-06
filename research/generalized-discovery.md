# Generalized discovery: finding the next Badgermole Cub without a human

Every concept improvement this project made (amplifies_mana, punishers, the
landfall/creature-ETB split, the entomb/mass-reanimation idioms, ...) followed
one template: **a structural signature existed in the data, no concept covered
it, and it surfaced only when a human noticed a wrong output.** Because the
ontology is closed, that residual is computable. Three mechanisms now
triangulate it:

## 1. Concept-gap mining (`cardguru gaps`, cardguru/gaps.py)

Signature every card (trigger-mode→reached-api chains, static modes,
replacement events, activated-cost archetypes); mark cards explained by ANY
concept library (hooks, roles, axes); cluster the unexplained by signature.

First run: **85.7% of 34,519 cards are concept-covered**; the 14.3% residual
clusters into a ranked concept roadmap: `S:ReduceCost` (246 — cost reducers,
the spellslinger analog of mana amplifiers), `T:Phase->X` upkeep-engine
families, `R:DamageDone->replace` (damage replacement), evasion/combat statics
(`CantBlockBy` 214), pinger abilities (`AB:TapCost->DealDamage` 76), and —
proving the method — `R:Counter` (59): **can't-be-countered effects**, which
the answer-windows model was silently wrong about. That cluster became a
concept the same hour: Banefire now reports its stack window SHUT
(conditionally, X>=5 visible in the reason). A discovered gap became a product
fix with no anecdote involved.

## 2. Ablation importance (concept-free measurement)

Remove each nonland card (replaced by a vanilla bystander to hold deck size,
land count, and curve mass constant), re-measure synergy edges + simulated
commander-on-curve. On the Standard landfall list: Earthbender Ascension,
Llanowar Elves (-6.8% on-curve when cut — the largest measured mana hit), and
Icetill Explorer rank top with zero concepts involved.

Instructive divergence: ablation ranks Badgermole Cub only #6 while the
concept-driven enabler weighting ranks him #1 — because the goldfish simulator
does not yet model mana *multipliers*, so ablation cannot see what it cannot
simulate. **Ablation is fully general but bounded by simulator fidelity;
concepts capture what simulation doesn't model yet; the gap miner proposes the
concepts.** Each mechanism covers the others' blind spots, and each
improvement to the simulator converts concept-knowledge into measurement.

## 3. The eval loop (already standing)

Golden intuition tests (High Noon shape, Tinker shape) freeze every discovered
concept as a regression test; the burned-sample RulesGuru protocol does the
same for the judge pipeline.

## The pipeline this enables

gap miner → cluster brief (signature + example cards) → concept induction
(agent drafts detector/complements/hate mapping; the in-session agent pattern)
→ automatic validation (detector matches cluster, not everything; complements
nonempty) → golden test → merged. Human review shrinks to approving digests.
The refinement backlog from run #1: sub-signature the S:Continuous catch-all
(1,864 cards) by param families, and model amplifiers/cost-reducers in the
goldfish sim so ablation can measure enablement directly.
