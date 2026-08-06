# First RulesGuru probe: 24 burned questions, end-to-end

The first measured run of the full adjudication pipeline against real judge
questions: stratified seeded sample (n=24, seed 42, engine-ready only) from the
frozen corpus, IDs recorded in `eval/rulesguru_burned_ids.json` and excluded from
any future final benchmark. Pipeline: agent compiles question → scenario JSON
(spec frozen at `research/data/compiler_spec_freeze.txt`, ≤2 engine-feedback
retries) → XMage executes in strict-choose mode → independent grader agent scores
the predicted answer against the official judge answer (ruling-equivalence
rubric, blind to engine state). Full per-question data:
`research/data/rulesguru_probe1.json`.

## Results

**Overall: 20/24 correct + 1 partial (83% strict).** By difficulty: levels 0–1
perfect (12/12), level 2 5/6, level 3 1+1p/4, Corner Case 2/2.

The number that matters more than the average:

| bucket | n | graded correct |
|---|---|---|
| **engine-confirmed** (scenario ran, all expectations met) | 8 | **8/8 (100%)** |
| **engine-flagged** (scenario ran, expectations missed) | 1 | 0/1 — the engine caught it |
| not simulatable (best-effort answer, labeled) | 15 | 12/15 + 1 partial |

**On this sample, engine confirmation and answer correctness agree perfectly.**
Every answer the engine confirmed was right. The one simulatable answer that was
wrong (q69: an Aura put onto the battlefield simultaneously with the permanent it
would enchant — the official answer is that the premise itself is impossible) is
exactly the one where the engine refused to confirm the prediction. Zero
confidently-wrong engine-verified answers — the property the whole product rests
on, holding in its first contact with real judge questions.

The engine-confirmed set is not softballs: Notion Thief hijacking all three
Brainstorm draws, The Mimeoplasm entering as a 0/0 when its exile rider can't be
paid, Progenitor Mimic dying and NOT returning transformed, Vesuva copying a
Border Guard that Song of the Dryads turned into a land (through a Grafdigger's
Cage), and a five-turn engineered combat proving a Rockslide Elemental survives a
Tephraderm block by one trigger-order rule. Each is now a stored, replayable
engine record in `scenarios/rulesguru/`.

## Where the misses live — and what they say

All four non-correct verdicts sit in the **unverified** buckets, concentrated at
level 3: the mutate/merged-permanent corner (partial), the Panglacial Wurm
token-in-library corner, the double-replacement ordering question, and the flagged
q69. This is the trust-label design validating itself: the danger zone is
precisely *hard + unsimulatable*, so the product's Simulated/Best-effort split
puts the warning label exactly where the errors are.

Simulatability: 9/24 attempted (8 confirmed), 15 declined. Decline reasons are a
capability roadmap, not noise — ranked by frequency:

1. **Driver gaps** (amount-division prompts for trample/divided damage; a
   pass-priority action for mid-stack response windows; empty-library setup;
   trigger-order scripting shortcuts) — each is a bounded driver feature that
   converts known question classes to simulatable.
2. **Setup vocabulary gaps** (face-down/manifested permanents, preset counters,
   token copies in setup) — scenario-spec extensions.
3. **Structural** (multiplayer/Commander/monarch; no observable board outcome;
   information-visibility questions) — honest Best-effort territory.

## Caveats

Dev-probe scale (n=24) and the grader is a single agent per half. The retry loop
consumed at most 2 engine-feedback rounds per scenario, matching the production
design. One executed-with-miss (q69) may also involve an engine-behavior
divergence on simultaneous Aura entry (Binding Grasp was not sacrificed at the
upkeep in-engine) — logged for the rulings spot-check pipeline rather than
diagnosed here, since the answer was wrong for a premise-level reason anyway.

## Implication

Phase 2b's kill criterion (~80% compilation accuracy) is comfortably cleared at
this probe's scale, and the eval discipline held: spec frozen before the run,
sample burned, no tuning on question content. The next accuracy gains are
mechanical: driver features from the decline list convert more of the corpus to
the engine-confirmed bucket, where measured accuracy is 100%.
