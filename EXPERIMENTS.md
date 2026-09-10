# Experiment Registry

*Every experiment in the project, in order: what the hypothesis was, how it was tested (control vs treatment), what came back, and what went wrong in the process. Compiled 2026-09-08 from the phase docs across all branches. Companion to `LEVELSET.md` (the synthesis); this is the traceback.*

**Verdict tags:** CONFIRMED (held up at claim-grade sample sizes) · NULL (no effect found by an adequate test) · REFUTED (hypothesis killed) · MIXED · UNDERPOWERED (test could not decide) · CONTAMINATED (instrument or checkpoint fault voids the number) · NOT RUN (designed only). **[user-directed]** marks experiments the docs record as your idea/redirect.

**Instrument glossary:** D0 = scripted heuristic opponent (Elo anchor 1000). D1 = 1-ply minimax search over a material evaluator (does NOT search combat). D1h = D1 forced to hold instants for opponent turns. CP7 = XMage's shipped depth-6 alpha-beta AI (held-out external benchmark). E0 = name-hash card features (control encoder); E2 = graph mechanical features; E3 = E2 + text embeddings. v1–v6 = state/action encoder generations (v2 conditioned blocking, v4 joint blocks, v5 joint attacks, v6 entity tokens + relations). Convention (adopted mid-project, often violated before and after): 500 games + Wilson CI for claims, ≥5 seeds, behavior counters with opportunity denominators.

---

## Era 0 — Pre-RL: card graph and feasibility

**1. Mechanical-search benchmark (20 structural queries).** Hypothesis: graph queries retrieve mechanically-defined card sets that text search cannot (post-hoc; goldens eyeballed). Design: 20 queries over 34,519 cards, 1–4 golden cards each; regex baseline run for only ~9/20. Result: 20/20 goldens pass; large disagreement with regex where compared. **CONFIRMED as smoke test only** — precision/recall never measured; regex "extras" never verified as false positives. ⚠ Tiny author-chosen goldens; asymmetric adjudication.

**2. XMage RL-environment feasibility (B1–B5).** Hypothesis: XMage is viable as an RL environment; PRE-REGISTERED kill criteria (throughput, copy cost, coverage, determinism). Design: random policy on real games, no control (characterization vs thresholds). Result: 647 decisions/sec/core (13x the kill floor), 97.6% coverage, 100/100 determinism. **CONFIRMED.** ⚠ Parallel-scaling criterion left ambiguous; decision density understated (heuristics handled sub-actions).

**3. Yield-interface act-rate study (B6–B8).** Hypothesis: act/pass/yield interface worth ~7x consult cut; PRE-REGISTERED kill line (act-rate ≥~40%). Design: 800 games, 3 regimes, plus a genuine replay-equivalence control. Result: act-rate ~10%, consults 880→244 (3.3x), zero divergence beyond engine noise. **CONFIRMED.** ⚠ Heuristic floor understates real act-rates (admitted); phantom-land instrument bug found.

**4. Agent-compiler POC rounds 1–2.** Hypothesis: NL→query-DSL and NL→scenario compilation work end-to-end (kill line: <80% accuracy). Design: dev sets n=8+2 then 20+8, no control. Result: cumulative 26/28 DSL witness-correct, 10/10 scenarios valid. **CONFIRMED for viability only.** ⚠ Spec tuned on round-1 results, so round-2 not independent; the eval questions themselves were wrong twice (caught by the engine).

**5. Graph vs flat BM25 retrieval ablation.** Hypothesis: PRE-REGISTERED — graph must beat flat text by ≥5 points on an adversarial slice or be cut. Design: BM25 control vs compiled graph queries; 20 dev + 5 adversarial questions. Result: adversarial witness recall 5/5 vs 2/5. **CONFIRMED per rule.** ⚠ n=5 adversarial questions authored by the graph's builder where flat should fail — the rule governed the decision, not the sampling.

**6. Graph vs LLM parametric recall.** Post-hoc ablation. Result: memory-only LLM won on witness recall (20/20 vs 19/20); graph won coverage 1,123 vs 109 cards. **MIXED**, honestly read. ⚠ Coverage denominator is the graph's own unaudited output.

**7. Generality probe + concept induction loop.** Result: 61.7% of legends hooked; defensive features on 4.4% of creatures; autonomous loop raised coverage 85.7%→92.6%. **MIXED.** ⚠ 20/20 golden score reached by fixing detectors against the same goldens (circular); coverage semantics redefined mid-run (metric change after seeing data); the 17/17 gate pass rate suggests a gate that never rejects.

---

## Era 1 — RL foundations (Phases 0–3)

**8. Consults-per-game reconciliation.** Post-hoc audit. Result: ~42 agent consults/episode; Phase 1's 495 was contaminated (accidental 50-turn topdeck games) and both prior phases summed BOTH seats through shared static counters. **CONFIRMED** (discrepancy explained). ⚠ Two prior instrument bugs surfaced; no n or variance reported on the corrected number.

**9. Driver throughput gates (M2/M3).** Result: 3.01 games/sec in-process; socket IPC costs 6.6%. **CONFIRMED.** ⚠ Baseline not apples-to-apples; acceptance thresholds implicit; single runs.

**10. Task A — sanity vs random opponent.** PRE-REGISTERED gate ≥70%. Result: 93/100 at 512 episodes; burn gameplan visibly reconstructed. **CONFIRMED.** ⚠ Single seed (fine for a plumbing gate).

**11. Task B — episodes to competence, burn mirror.** PRE-REGISTERED: ≥55% over 500 games, CI excluding .50; decision table written first. Design: 5 seeds vs D0; rolling 100g gate + 500g confirmation. Result: 5/5 pass, median 512 episodes, confirmed .62–.65; the "task too easy" branch fired as pre-registered. **CONFIRMED.** ⚠ One false gate at 100g caught only by the 500g confirmation; a counter bug misreported one seed's episode count (corrected).

**12. Task D — real Dimir control deck.** Same criterion; vs a STRENGTHENED heuristic (instrument v2). Result: 4/4 seeds, median 256 episodes, confirmed .57–.66. **CONFIRMED, headline partially overclaimed:** "real deck not harder" compares across two different yardsticks — the same doc forbids that comparison — and in decision points (the corrected unit) it was ~2x more expensive. ⚠ Stopped at 4 seeds after seeing the distribution (data-dependent stopping, admitted); one seed's CI barely clears.

**13. State-encoding lossiness audit.** Post-hoc. Result: the flat encoding collapses 86% of 3-creature and 97% of 5-creature boards into shared vectors; the 68-dim card features were never plumbed into the state. **CONFIRMED as capacity fact** — but no experiment ever showed the collisions cost win rate, and the one-combat reference provably can't see the fix.

---

## Era 2 — Task C and Phase 4: the encoder A/B and the depth ladder

**14. Task C in-distribution parity.** Pre-registered sanity axis. Result: E0/E2 parity on the pool — but "parity" on the control deck is parity at near-total failure (.08/.06): pooled training starved the slow archetype. **CONFIRMED (arms matched).** ⚠ Budget cut mid-run on seed-0 evidence; the unlearned control deck contaminates every downstream holdout-control comparison.

**15. Task C zero-shot holdout A/B.** PRE-REGISTERED rule: E2 beats E0 by CI-excluded margin on ≥2 of 3 holdout decks. Design: 3 seeds/arm, 600 pooled games/arm/deck, graph-built analog decks. Result: rule NOT MET (parity); post-hoc findings — E2 seed-consistency and freeze rate 7.0% vs 15.5%. **NULL on the registered rule; the famous liveness finding was born post-hoc here.** ⚠ n=3 seeds; consistency/freeze metrics chosen after seeing data (docs admit it); stalls entangled with win rate.

**16. Task C few-shot recovery.** Pre-registered axis. Result: both arms land ~.25–.38 after 128 fine-tune episodes; no advantage. **NULL.** ⚠ The spec asked for time-to-recovery; a single fixed dose was run instead — a weaker design that can't measure the registered quantity.

**17. Phase 4 M0 — the "4x throughput gap" audit.** PRE-REGISTERED gate. Result: the gap dissolved (cross-workload comparison); IPC is 2% of wall-clock; IPC V2 correctly not built. **REFUTED (the gap), instrument audit CONFIRMED.** ⚠ The original 4x claim was itself a process failure; also retro-corrected Task D's "equal difficulty" to ~2x in decision points.

**18. D1 calibration.** Pre-registered gate. Result: D1 beats D0 .776 [.74–.81], n=500. **CONFIRMED** — later cut to .614 by the v3 instrument fix (#24).

**19. Ladder monotonicity above D1.** Pre-registered branch. Result: D2 vs D1 .52 (n=100), D3 vs D1 .52 (n=60) — flat; the material evaluator, not depth, is the ceiling. **REFUTED (two rungs, not five).** ⚠ n=60/100 for a null that killed the entire planned depth sweep — a modest real edge wasn't excluded; possible breadth/depth confound in the dial never discussed.

**20. Phase 4 M4 — depth A/B (E0 vs E2 at D1).** PRE-REGISTERED predictions: freeze gap persists/widens at depth; win gap opens at D2–D3. Result: win-rate parity again; pooled freeze gap persists (17.2% vs 22.8%) but per-seed the Task C consistency story did NOT replicate — one seed reversed. **MIXED / UNDERPOWERED.** ⚠ 3 seeds instead of the spec's 5 (user-directed cut, exactly where it bit); D0 row reused from Task C rather than run concurrently; both arms trained below parity vs D1, so the instrument bites into the measurement; M3 novelty sweep displaced and unrun.

---

## Era 3 — Phase 5–6: teachers, imitation, shaping, self-play

**21. C0 environment rebuild validation.** Result: D1 vs D0 .71 @100g vs the .776 target; nodes/decision exact match; two latent harness bugs (empty card DB, field drift) caught. **CONFIRMED (within noise).** ⚠ .71 is below the original CI — only the 100g width saves the reading; no tolerance was pre-stated.

**22. C0 — SearchPlayerIP: is perfect information load-bearing?** PRE-REGISTERED gate. Design: honest determinized search (K=4) vs perfect-info D1, 500g arms. Result: D1ip vs D1 .482 — even; the "cheat" is worth ~0 at 1 ply; D1 licensed as teacher. **CONFIRMED.** ⚠ Depth-2 arms only 100g; K=4 unjustified.

**23. C1 — behavioral cloning of D1.** Result: 96.8% offline agreement → only .396 vs D1 online (500g); teacher .50; compounding error 0.97^73 ≈ 10% on-trajectory. **CONFIRMED-as-negative.** ⚠ Data-scaling sub-arm confounded (different eval sizes); the covariate-shift diagnosis was inference — C3 later refuted it. Design flaw admitted post-hoc: a fixed ~.50 teacher caps the student by construction.

**24. v3 instrument recalibration — the flash/ninjutsu blindness. [user-directed]** Discovery: three stacked layers made every instrument unable to cast at flash speed. Result: D1 vs D0 fell .776 → .614 @500g — 16 points of the ladder was artifact; only the Dimir deck affected. **CONFIRMED (bug real; all work re-anchored).** ⚠ The blindness shipped through Phase 4, C0, and C1, and was caught by manual transcript reading, not by any automated check. The single largest instrument failure in the project.

**25. C2a — BC-init PPO ± potential-based shaping.** PRE-REGISTERED gate: >.45 vs D1 @500g + stall cut. Result: no-shape .442, shaped .434/.434; stalls worsened. Gate FAILED; **shaping NULL** (twice — a v2-era "edge" from 100g rolling evals did not survive 500g). ⚠ Seed asymmetry (2 shaped vs 1 unshaped control); rolling 100g flattered every arm ~.07. Later shown theoretically redundant: GAE's residual already IS potential shaping with Φ=V.

**26. C3 — DAgger: is covariate shift the bottleneck?** Effectively pre-registered falsification of C1's diagnosis. Design: noise-injected then true on-policy shadow labels; the covariate gap itself measured (35% vs 8%). Result: exactly 0.000 win-rate movement; the net underfits its OWN distribution — capacity, not covariate shift, is the wall. **REFUTED (the diagnosis) — the cleanest experiment in the RL program.** ⚠ An earlier "collapse" battery was voided: a path bug served a random-init net in evals (caught via implausibility). Single retraining run per round.

**27. C4 — is draw-go timing worth anything? [user-directed]** Design: D1h (holds instants) vs D1 and D0, 500g each. Result: .504 and .596 — worth ~0 against non-adaptive opposition. **NULL (correctly bounded:** the value can only exist against opponents that model held mana). ⚠ One deck by necessity; the exploitability upper-bound probe was designed but never run.

**28. M3 — novelty sweep (pool diversity × encoder).** PRE-REGISTERED: diversity amplifies E2's liveness edge. Design: 5 nested pools × 2 encoders × 2 seeds, 640-episode budget, 6,000 eval games/arm. Result: freeze edge replicates (2.5% vs 4.1%, third time) but does NOT grow with diversity — the registered hypothesis failed; a post-hoc zero-shot win edge (.401 vs .365) surfaced. **MIXED.** ⚠ 2 seeds vs the 5-seed rule; the pooled CI treats 6,000 games as independent when the effective n is 2 seeds; win-edge metric surfaced after seeing data (held below the gate, correctly).

**29. C5 — clean self-play league. [user-directed]** Result: best agent yet (+.12 over its BC origin; probes above both rulers), saturating after ~1,000 episodes exactly where C3's capacity diagnosis predicted; opponent-turn instant casting rose to 57% of casts. **CONFIRMED.** ⚠ Single deck; peak-vs-final reporting; scratch arms abandoned at 384 episodes so "self-play needs BC init" is suggested, not tested.

**30. Phase 6 — Elo tournament + exploiter probe. [user-directed]** Result: fitted Elo ordered the field (e0_champ 1083 ≈ D1 1085); exploiter plateaued at .42 vs the champion. **CONFIRMED (ordering); exploiter robustness bounded.** ⚠ 100g pairings then narrated as 3–5-Elo orderings (inside noise); anchor-bridging across encoder families asserted, not tested; the ≥.65 "hole" threshold appears post-hoc; the exploiter's own capacity ceiling (C3) confounds "not exploitable."

---

## Era 4 — Phase 7: scratch, PFSP, curriculum

**31. Phase 7 scratch run.** Hypothesis **[user-directed]**: a scratch agent with the right opponents can learn by exploration alone. Result: Elo 46→916 in 1,024 episodes; discovered ninjutsu and instant-speed removal with no teacher. **CONFIRMED at mechanism level; refuted as a route to teacher-tier at this budget.** ⚠ Single seed; the "never blocks" headline was a log-parsing bug (published, then corrected); the staged BC-init comparison arm never ran.

**32. Phase 7b — PFSP self-play to 9,216 episodes.** Result: peak Elo 1101 at 6,144 (D1 parity), then drift to 1044 as the pool filled with its own snapshots; a 40-game head-to-head confirmed real regression (.40). **CONFIRMED (PFSP breaks stalls); REFUTED (ungated self-play is safe).** ⚠ Single seed; the "+49 vs +86 slope" PFSP claim is a before/after confounded with infrastructure changes — no control; drift was foreseeable and uninsured; a SIGKILL corrupted a checkpoint (fixed with atomic saves).

**33. Blocking audits (7b, 7c).** The "never blocks" claim died twice more: block rate was 41% by corrected parsing, then 100% (121/121) once opportunity denominators existed — the real phenomenon was opportunity scarcity. **REFUTED (the hole).** ⚠ Three generations of instrument error on the same metric; the phase's pre-registered headline metric was saturated before the phase began.

**34. 7c curriculum-ordering screen.** Result: measured difficulty ordering was the REVERSE of archetype folklore (the anti-board control deck was easiest, ramp hardest). **REFUTED (intuition).** Standing rule since: calibrate every opponent-deck pair empirically.

**35. 7c main curriculum run.** Hypothesis: widening opponent-deck diversity buys robustness the mirror can't. Result: Elo 928→1096 peak in 1,536 episodes (~5x prior rate); robustness residuals improved on all six decks; redrush zero-shot .650 vs .225 baseline. **CONFIRMED per doc, with a hole:** ⚠ the designed A/B control (mirror-PFSP from the same frozen checkpoint) was never closed — the "5x" compares against history; single seed; headline metric switched post-hoc (block rate was saturated, so the verdict migrated to a residual metric built after the data); a latent deck-assignment driver bug found mid-phase.

**36. 7c pilot/deck-power calibration.** Result: D1 is a WORSE pilot than D0 on four of six archetypes — the entire D0<D1<D1h Elo anchoring is BenchDimir-specific. **REFUTED (the repilot plan); one of the cheapest, highest-value controls run.**

**37. 7c specialists (blocked practice vs curriculum).** Equal-budget design. Result: specialists lost on their OWN decks by mean .154; five of six ended at or below the starting Elo. **REFUTED (depth-vs-breadth trade)** — "diversity is the mechanism by which anything is learned at all." ⚠ Total-training vs per-deck-exposure confound acknowledged; single seeds.

**38. 7c exploiters.** Result: .20–.40 regardless of deck — the arm measured its own init mismatch (Dimir prior, 512 episodes), not the agent's robustness. **REFUTED (its own design)**; the robustness-matrix caveat it was built to lift stands unlifted.

---

## Era 5 — Phase 8: the transfer program

**39. Swap-deck calibration + Force Spike bisect.** Result: two counterspells at feature distance ZERO moved a scripted mirror 6 points (.735 vs .675, 200g) — condition breadth is not a feature dimension. **CONFIRMED (and the seed of the condition-transfer design).** ⚠ Two decks accepted 1.6–1.9σ hot, contaminating M2's deltas; "departs wildly" was never quantified.

**40. M2 — 12-card zero-shot transfer matrix.** PRE-REGISTERED: graph deltas ≈ 0 ≥ hash deltas ≪ 0. Result: all 12 graph deltas ≥ 0 — but the hash negative-control cells were NEVER RUN (dropped mid-run by redirection to M2b). **UNRESOLVED — the contrast the experiment existed for was not collected.** ⚠ The registry's clearest case of a dropped control; positive deltas partly deck-power artifact.

**41. M2b — full-archetype transfer (Faeries).** Result: every encoder dropped ~.06–.21, differences inside CI — the noise control transferred as well as the treatment. **REFUTED (encoding-dependent transfer).** ⚠ The doc's corollary ("card identity is a minor channel") was REVERSED weeks later by #42.

**42. Feature-scramble diagnostic.** Result: scrambling the card table at eval drops the policy .640→.260 — 38 points, below the scripted floor; zeroed beats scrambled. **REFUTED (Phase 8's mechanism claim); card features are load-bearing — as identifiers.** Effect size swamps the single-seed concern.

**43. Deck-randomized fine-tune.** Hypothesis: per-episode deck randomization forces compositional feature use. Result: all lanes destabilized; transfer unchanged (deltas inside CI); opponent-turn flash casts rose ~10x (behavioral shift real, win-rate value nil). **NULL on the headline.** ⚠ Training probes at 100g against the project's own rule; fine-tune shock means the mechanism was tested under its worst condition; meta decks were unverifiable reconstructions.

---

## Era 6 — Phase 9–10: performance and the flagship league

**44. Phase 9 performance battery.** JFR profiling (getPlayable = 82%, the old Game.copy assumption refuted), persistent JVM (1.09x), in-JVM concurrency (4.14x at N=4), getPlayable memo (verified with 0 mismatches in 122k calls; +13–20% but 0 hits on policy lanes), ParallelGC (adopted on admittedly weak evidence), TokenRepository race fixed. **CONFIRMED (well-validated); the memo's verify-mode is the template for safe engine patches.**

**45. Crown matches.** ck_6144 vs D1 .48 @500g (parity, correctly not "beats"); beats both curriculum champions ~.56 @200g. **CONFIRMED.**

**46. Phase 10 flagship — champion-gated league.** Hypothesis (pre-specified design): gating prevents 7b's drift; deck diversity from init buys robustness. Result: no drift (Elo flat) — but 0/24 gate promotions, saturation at ~6,144 episodes, final 6,144 episodes bought nothing. **MIXED: gating-as-anti-drift CONFIRMED; "gating is enough" REFUTED (a frozen pool starves the league).** ⚠ PFSP targeted Elo 299 for the first 2,048 episodes (stale self-rating file — selection bug, admitted); the DESIGNED rotation-off control arm never reported results, so the diversity claim rests on cross-phase comparison; single seed; author admits reading four noisy gate points as a trend.

**47. Selective-blocking candidate.** Logged at ck_4096 WITH its falsification test named in advance; at ck_6144 every deck returned to ~100% blocking. **REFUTED — the project's model case of pre-registration working.**

**48. Gate-as-rating-probe validation.** Implied Elo agrees with the full fit within 3–21 points. **CONFIRMED (for its operational use).**

---

## Era 7 — The encoder ladder (v1→v6) and combat

**49. v1 vs v2 — conditioned blocking A/B.** Result: block-optimality .829 vs .557 (z=16.2, replicated across 2 seeds); v1 had blocked 15,674/15,674 opportunities without one decline — an OBSERVABILITY failure, not a learning failure. Win rate: not a finding (z=1.27). **CONFIRMED (behavior); NULL (win rate).** ⚠ v2 trained under a controller-blind combat channel (numbers are floors); block-optimality later shown not to track strength and retired as primary.

**50. v4 — joint block assignment.** Result: solves the two-attacker allocation positions v2 provably couldn't; D0 .940 @512 episodes. **CONFIRMED (commitment fixed); "v4 wins more" correctly never claimed** — three simultaneous changes, one seed. ⚠ First checkpoint lost to container restart; reference blind to over-piling.

**51. Attack-audit baseline.** Result: the v4 agent attacks in 30% of real choices, and DECLINES A LETHAL ATTACK against an empty board. **CONFIRMED (attacking broken at the decision level).**

**52. resolve() tie-break bug + re-baseline.** The reference broke ties by list order and the search exploited it. Fix re-measured against the legacy path (exact reproduction), published numbers moved ≤.005. **CONFIRMED (numbers stand); clean handling of a reference-integrity bug.**

**53. v5 — joint attacks vs budget-matched v4 control.** The control arm the v4 run lacked. Result: attack rate z=+18.7, attack-optimality unchanged, block-optimality regressed, win rate identical (.810 both); the .940→.810 drop was the extra training, not v5 — ONLY the control revealed this. v5 alone takes the lethal. **REFUTED (quality gain); one causal win (lethal recognition).** ⚠ One seed pair; joint-candidates confounded with credit-assignment change.

**54. Encoding-irrelevance proof.** The attack reference's answer recovered from candidate features alone, 400/400 positions. **CONFIRMED** — no measured attack error is a representation failure; but the v6 pre-registration later drawn from it was stronger than this premise (admitted).

**55. v6 build gates.** Network invariant checks (23/23, incl. a deliberate negative control), emission collision gate (853 v5-identical state pairs all distinct under v6, PASS with nothing trained), EMAX buffer refuted twice by truncation counters (24→48→96). **CONFIRMED (the information is now in the observation — nothing yet about whether the agent uses it).**

**56. v5/v6/v6-R0 three-arm training A/B.** PRE-REGISTERED: attack/block-optimality cannot improve from the state change. Result: win rates unresolvable at 25g; relations null at rung 0 (as predicted); attack-optimality moved when the registration said it couldn't — recorded as an ANOMALY (unpaired metric across arms), not a result. **NULL / anomaly quarantined — exemplary refusal to claim.** ⚠ One seed; 25-game batteries; v6's own attack search made it 5–50x slower per game.

**57. v6 vs v5 head-to-head.** 4–5–11 in 20 games with 43% of consults truncated at EMAX 48. **CONTAMINATED AND UNDERPOWERED** — the doc itself disqualifies it pending EMAX 96.

**58. Rung-0 ceiling test.** PRE-REGISTERED three-branch decision rule written before the CP7 number. Result: agent plateau .782 [.72–.83] @200g; CP7 .650 @60g — overlapping, reading A (ceiling is the deck's); the agent numerically EXCEEDED the shipped AI on this deck. **CONFIRMED per rule, with admitted caveats:** interval overlap at n=60 structurally favors reading A; the D1 row was then invalidated by the combat audit (#59), leaving the reading on one comparison; the original seat-asymmetry caveat was wrong and is visibly withdrawn.

**59. Rung-0 depth ladder + SearchPlayer combat audit.** 2-ply and 3-ply probe files came back byte-identical — the search bottoms out because SearchPlayer NEVER SEARCHES COMBAT (inherits D0's attack/block rules); on a vanilla-combat deck D1 searches nothing that matters. **CONTAMINATED (instrument invalid for the deck); three prior statements formally withdrawn.** Retroactively narrows what "D1" measured everywhere.

**60. Dimir v6 runs (512→2048) + the targeting finding.** The "destroys its own creatures" finding was PUBLISHED WRONG (the quoted windows had no legal enemy target — denominator neglect), then corrected by a controller-split census: enemy chosen 10/11 when available; the real failure is casting removal into empty boards. 10-game probes retracted after a 100-game re-probe moved every level (D0 .40→.54); 1024→2048: +.030, p=.54 — **NULL on win rate (adequately powered at n=200);** attack policy collapsed to "attack with everything" (0 under / 40 over); flash held for opponent's turn 1/1,027 opportunities. ⚠ TWIN was accidentally the same matchup sampled twice; no v5 control arm; a lone p=.039 on the D1 arm correctly withheld (multiple comparisons); no durable training curve for most of the project (a two-line logging fix left undone).

---

## Era 8 — Phase 11–12: the external benchmark and the credit program

**61. Phase 12 performance.** The JFR profile transferred (getPlayable 77.8%) but was misleading as a speedup budget — JFR samples on-CPU only, so "IPC = 2%" hid the real conc4 bottleneck. The deeply-profiled engine patch bought 1.05x at conc4 (verified safe, 22,825 checks); a one-line `RL_TORCH_THREADS=1` fix bought 1.54x. **CONFIRMED / self-indicting:** "the expensive, risky, deeply-profiled engine work was worth a twentieth of a one-line configuration fix." Independently rediscovered by three parallel branches (no shared registry).

**62. First external benchmark — CP7.** After ten phases, the first measurement against an opponent the project didn't write: ck_6144 .28, p10_final .22 vs CP7 (50g each, ±.13); the D1 column reproduced as a same-session control. **REFUTED (the internal Elo ladder as a strength measure):** every "saturation" was saturation against our own weak pool; deck diversity bought nothing here. Held-out discipline declared: never train on CP7. Caveat from #58: on the simplest deck one agent already matched/exceeded CP7 — the gap is a benchmark-deck number.

**63. Timing gate (Levels A/B).** PRE-REGISTERED stop condition: if candidate vectors are timing-identical, "no training can learn the difference" — void everything. Result: the collision is real (one distinct row across 20 steps) but the stop condition's premise was FALSE — the step reaches the logits through the state token (perturbation probe, 5 seeds). **CONFIRMED (collision); the registration's inference correctly refused.**

**64. "The gap is mana" census.** Random-policy census said instant windows are always tapped out; the trained-checkpoint census INVERTED it (678/1158 windows castable, zero casts). **REFUTED — retracted inside its own document; the pre-written caveat fired.** Model behavior for being wrong in public.

**65. The 5,504/0 argmax census.** Design: same card at instant speed (B1Fast) vs sorcery speed (B1Narrow), same checkpoint protocol. Result: instant offered 5,504 times, cast 0; sorcery offered 470 times, cast 92 (19.6%). Mechanism: the timing-blind candidate row arrives 90% in pass-contexts for the instant — instant speed is a LIABILITY under this encoding. **CONFIRMED (the sharpest single measurement in the credit program).**

**66. Sampled-exploration census.** Result: ~87 casts/100 games under sampling, aimed at essentially random moments — exploration exists, credit doesn't reach timing. **CONFIRMED qualitatively; rate CONTAMINATED:** ⚠ the probe TRAINED ITS SUBJECT (server updated and overwrote ck_1024 in place; the pristine checkpoint no longer exists). Fixed with `--frozen` + serving a copy; origin of the ground rule "a probe must not be able to write what it measures."

**67. B1Fast vs B1Narrow — the instant-speed A/B.** PRE-REGISTERED (four clauses, prediction: no separation), the tightest twin design in the project: same seed, same budget, decks differing in exactly four card slots. Result: .595 vs .585 pooled n=200 — null as predicted. Deeper verdict: **UNPOWERED BY CONSTRUCTION** — one arm cast the removal 86 times, the other 0, and they finished dead even, so the removal has no win-rate value on this rung; the A/B varied the timing of a card the metric cannot see. ⚠ The curriculum designed for target legality and never checked target VALUE — discoverable cheaply beforehand; a mid-run battery point (.020) would have been published as a collapse without the new dense logging.

**68. Circular value_ev instrument.** First reading 0.7664 — plausible and meaningless (the metric scored GAE against its own bootstrapped return). Corrected to Monte-Carlo targets: **critic explains ~0.34 of outcome variance** — the project's first real critic measurement. **REFUTED (instrument); origin of the rule "an instrument gets a validity check before its first number is quoted."**

**69. Oracle-guiding critic probe.** PRE-REGISTERED with five cannot-move clauses AND a pre-committed reading rule (both arms near zero = underpowered, not null) written before results. Design: matched fresh critics, control blind / treatment sees opponent's hand, identical trajectories. Result: both arms ~0 EV — 256 independent episode labels cannot fit a 700k-parameter critic. **UNDERPOWERED, exactly per the rule — the hypothesis is untested, not dead.** Five implementation failures en route, all documented: GAE bootstrap divergence; policy needlessly in the loop; OOM from storing parallel observations; the coverage counter itself broken (read 1.000 in both arms); and the divergence being architectural — which ONLY the control arm caught ("privileged info destabilises the critic" would have been the published conclusion without it). Replacement (`oracle_ridge.py`) built and validated against positive AND negative controls before use. **NOT RUN yet.**

**70. B3 threat-assessment census.** Result: the agent kills the BIGGEST creatures less often than chance (χ²=9.39, p=.024) — no threat assessment. **CONFIRMED (narrow claim), with admitted caveats:** within-game correlation makes p optimistic; each census alone non-significant; one seed; no ground truth that killing big is even correct.

---

## Designed but never run

The cheapest standing experiments, all with designs already written:
- **Condition-axis transfer A/B** (`CONDITION-TRANSFER-DESIGN.md`): four falsification predictions pre-registered; the design doc itself flags that its §4 matrix confounds two levers and must run as separate arms.
- **Twin-deck identity probe** (B0Twin): same stats, all-new names — any drop is pure identity memorization.
- **Oracle ridge probe** (`oracle_ridge.py`): validated instrument, data collection needs no Java change.
- **Phase 10 rotation-off control arm** (`PHASE10-CONTROL-ARM.md`): the missing attribution for the diversity claim.
- **7c curriculum-vs-mirror A/B** from the shared frozen checkpoint: the missing control for the "5x" claim.
- **M3 novelty sweep at 5 seeds**: the liveness differentiator has never been run at the project's own evidence bar.

---

## Failures in scientific process — the consolidated ledger

Ranked by damage done. Each pattern names its incidents so it can be checked against, not just regretted.

**1. Instruments trusted before validation (the most damaging class).** The flash/ninjutsu blindness inflated the main yardstick by 16 points through three full phases (#24). SearchPlayer never searched combat, silently invalidating what "1-ply search" meant on combat decks (#59). The block metric was wrong three times in a row — parse bug, missing denominator, saturated headline (#31–33). value_ev was circular on first reading (#68). The oracle coverage counter read 1.000 in both arms (#69). JFR's on-CPU-only sampling sent a week of engine work at the wrong bottleneck (#61). Shared static counters double-counted both seats from the project's first days (#8). Every one was caught by manual transcript reading, anomaly-chasing, or luck — none by a routine guard. The corrective rule now on the books: **an instrument gets a validity check before its first number is quoted.**

**2. Underpowered evals quoted as levels.** 10-game probes produced a published learning curve that was pure noise (retracted, #60); 25-game probes produced the B1Fast "responded to training" story that inverted at n=100 (#65-adjacent); 100-game rolling evals flatter by ~.07 and caused two false competence gates (#11, #25); n=60 underpins both the depth-ladder null (#19) and the CP7 ceiling reading (#58); Elo orderings of 3–5 points were narrated from 100-game pairings (#30). The 500-game/Wilson convention exists because of these — and was still overridden for cost afterward ("bought a wrong number, not a cheap one").

**3. Controls dropped, skipped, or never closed.** The Phase 8 M2 negative-control cells — the entire point of the pre-registered contrast — were dropped mid-run (#40). The Phase 10 rotation control was designed and never reported (#46). The 7c curriculum's designed A/B was never closed; its headline "5x" rests on historical comparison (#35). The Phase 7 BC-init comparison arm was staged and never run (#31). Conversely, the two moments a control arm was most valuable — the oracle probe's control diverging identically (#69) and the v5/v4 matched pair exposing that the win-rate drop was fine-tuning (#53) — are the strongest arguments in the project for never skipping one.

**4. The seed convention honored in the breach.** The project wrote a ≥5-seed rule and then ran 1–3 seeds almost everywhere: 3 in the pivotal Phase 4 depth A/B (where one seed reversed the finding, #20), 2 in M3 (#28), 2-vs-1 asymmetric in C2a (#25), 1 in every Phase 7–12 training run. The E3 case is the cautionary tale: seed 0 showed +.175, seed 1 showed +.020 and reversed a second finding — numbers that earlier phases would have published (#POOLED). Between-run variance is the project's dominant noise source, and most headline runs cannot exclude it.

**5. Metrics chosen or switched after seeing data.** Task C's consistency and freeze findings were surfaced post-hoc (honestly labeled, then correctly hardened by replication, #15). 7c's headline switched from the saturated block rate to a residual metric constructed after the data (#35). M3's win-rate edge was surfaced by the sweep designed around freezes (#28). Concept-induction coverage was redefined mid-run, inflating the improvement (#7). The distinction that matters: post-hoc findings that were then labeled and replicated (freeze rate) became real; those quoted directly (M3's edge) stayed provisional.

**6. Contamination of subjects and checkpoints.** A measurement probe trained and overwrote the checkpoint it was measuring (#66). An eval battery served a random-init net through a path bug (#26). Three checkpoints lost to container-local /tmp storage, one forcing a full re-train (#67). A SIGKILL mid-save corrupted a checkpoint (#32). Fixes now standard: `--frozen` probes serving copies, atomic saves, per-checkpoint commits.

**7. Designs that could not answer their own question.** Imitation from a ~.50-capped teacher could never exceed .50 (#23). Exploiters initialized from a mismatched prior measured their own handicap (#38). The recovery experiment ran a fixed dose where the spec asked for time-to-threshold (#16). The timing A/B varied the timing of a card whose value the readout cannot see (#67) — and the deck-value check that would have caught it in advance was cheap. The online oracle probe's 256-label/700k-parameter mismatch was foreseeable arithmetic (#69).

**8. Data-dependent protocol decisions.** Task C's budget cut on seed-0 evidence (#14); Task D stopping at 4 seeds after seeing the distribution (#12); Phase 4 M4's seed cut landing exactly where the spec warned (#20). All admitted in the docs; all applied to both arms, which limits but does not eliminate the bias.

**9. No external calibration for ten phases.** Every opponent, anchor, and Elo point was project-written until the CP7 benchmark (#62) revealed the best agents at .22–.28 against the first outsider. Every "saturation" and "parity" before that is a statement about our own pool. Related: duplicated discovery across parallel sessions (three branches independently found the torch oversubscription) for want of a shared findings registry.

**What worked — keep doing these.** Pre-registration with named kill conditions (the selective-blocking candidate died cleanly, #47; the rung-0 rule acted itself, #58; the oracle reading rule prevented a false null, #69). The 500-game CI confirmation (caught every false gate it ever saw). Matched control arms (#53, #69). Verify-modes for engine changes (0 mismatches in 145k+ checks, #44, #61). Truncation and coverage counters (caught EMAX twice, #55). Behavior counters with opportunity denominators (produced nearly every decisive diagnosis in the project). Publishing corrections in place instead of rewriting history (#60, #64). The failure ledger habit itself — this document exists because the docs recorded their own mistakes.
