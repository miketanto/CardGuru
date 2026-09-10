# Where the Magic RL Project Actually Stands

*A level-set across all phases (through Phase 12 and the credit-assignment work), 2026-09-08. Synthesized from 144 extracted findings; sources are the `rl/` phase docs, now consolidated on `main`.*

## 1. Thesis

**We can make an agent that has transferable and accumulated knowledge of Magic: the Gathering using reinforcement learning methods.**

The evidence splits this thesis into three parts. The "using RL" part is supported: with nothing but a win/loss reward at game end, PPO reliably learns competent aggressive Magic in hundreds of games, and a from-scratch agent even discovered ninjutsu (a stealth-attack mechanic) on its own. The "transferable knowledge" part is where the evidence pushes back hardest: what transfers to unseen cards is generic statistics (cost, power, toughness) plus trained skills, not card understanding; our semantic card features have never bought a win-rate advantage over a meaningless hash, in four separate full-budget comparisons. The "accumulated knowledge" part is untested in the way that matters: every training run has plateaued against frozen opponents we wrote ourselves, and our first measurement against an external strong AI showed our best agents winning only about 25% of games. We have never run out of headroom, only out of opposition. The thesis is alive, but the transfer claim is currently losing to its null hypothesis, and the accumulation claim has never been tested against an opponent that keeps getting better.

## 2. What we have established

**Terminal-only reward is sufficient to learn real, competent Magic.** Five out of five seeds beat the scripted heuristic opponent on a burn mirror in a median of 512 training episodes (confirmed at 62–65% over 500 games each). A real 22-card control deck learned in fewer episodes (median 256), though counted in decision points — the correct unit — it was about 2x more expensive, not equal. A scratch agent later discovered instant-speed removal and ninjutsu, lines no teacher or scripted opponent ever demonstrated.

**But rare decisions get essentially no learning signal, and we measured the mechanism end to end.** Roughly 90% of the agent's decisions are "pass priority," and one bit of win/loss feedback spreads over ~45 consulted decisions per game. The clearest casualty: a trained agent offered an instant-speed removal spell 5,504 times across 100 games and cast it zero times, while casting the identical card at sorcery speed 20% of the time. Exploration is not the problem — sampled (non-greedy) play casts the spell roughly 87 times per 100 games (the exact rate is contaminated by a probe bug; the greedy-vs-sampled split is not), but at essentially random moments, because no credit ever reaches timing.

**Densifying the signal by hand does not work; improving the opponents does.** Reward shaping matched unshaped training exactly (.434 vs .442 against the 1-ply searcher, 500 games per arm), imitation plateaued well below its teacher, and on-policy corrective labels moved win rate by exactly zero. What did work: sampling opponents ~100 rating points above the agent roughly doubled improvement rate (one run), and rotating opponent decks lifted a frozen agent from rating 928 to 1096 in 1,536 episodes (one seed) — about five times the rating-per-episode of continued mirror self-play.

**Card features are heavily used, but as arbitrary identifiers, not meaning.** Scrambling the card-feature table at evaluation drops win rate from .64 to .26 (200 games, below the scripted-mirror floor), so the channel is load-bearing. Yet graph-derived mechanical features never beat a 16-bucket name hash on win rate — not on training decks, not zero-shot on unseen decks at two perturbation scales, with the hash control degrading exactly as much as the treatment.

**What actually transfers is generic stats and trained skills, not card identity.** Agents keep ~90% of their strength on unseen analog decks whether their identity features are meaningful or noise (600 zero-shot games per cell). Separately, skills learned against a diverse opponent-deck pool transferred zero-shot to never-seen decks (e.g. .650 against a deck the baseline scored .225 on, 100-game probes) and beat equal-budget single-deck specialists on the specialists' own decks — single seed, but consistent across six archetypes.

**Opponent depth, not deck complexity, has been the binding constraint on every measurement.** Strengthening the scripted opponent bought nothing; a real complex deck was no harder than synthetic burn; and the scripted search ladder has only two usable rungs, because 2-ply and 3-ply search are exactly as strong as 1-ply (.52 head-to-head) — the material evaluator underneath, not depth, is the ceiling.

**Small evaluations and denominator-free metrics have repeatedly produced false findings.** Ten-game probes moved .40 to .54 on identical weights; 100-game blocks flatter by ~7 points versus 500-game confirmations and caused two false competence passes. Nearly every decisive diagnosis (never-casts-removal, always-blocks, the refuted "kills its own creatures" claim) came from per-decision counters with explicit opportunity denominators, not from win rate at any sample size.

## 3. Challenge 1: Credit assignment (the "priority problem")

The feared version — terminal reward can't reach any decision through hundreds of priority passes — is false. Frequent, on-turn decisions (play threats, attack, aim burn at the face) are learned quickly and bimodally: seeds sit at a low plateau, then discover the aggressive package and jump through the competence gate within one 256-episode window.

The real version is narrower and nastier: decisions that are rare per game, or whose value never appears on the board, get starved. Removal is cast into empty boards (and training made that worse), and instants are held for the opponent's turn once in 1,027 opportunities. Opponent-turn casting stays near zero under greedy play in almost every regime; the two partial exceptions are self-play mirrors (instant casting rose to 57% of casts, though hold-mana reactive play never appeared) and per-episode deck randomization (~10x more flash casts, win rate unchanged). The one measured critic explains only about a third of outcome variance, and since advantage estimation with terminal reward is mathematically equivalent to shaping with the learned value function as potential, hand-written shaping was provably redundant — which the null results confirmed. An independent project on Forge (another open-source Magic engine) reached the identical diagnosis.

One structural fix worked without touching the reward: restructuring blocking as a single joint decision per combat, described by simulated consequences, gained +27 points of block-optimality, replicated across seeds. The same treatment applied to attacking changed behavior but improved nothing. Making combat state observable was part of that fix — so some "credit assignment" failures were really observability and action-structure failures.

Open: the act/pass/yield-until-condition interface (measured to cut consults ~3.3x, never trained on); the pre-registered curriculum rung testing pure card advantage — a spell whose value never appears on the board, predicted to be unlearnable under terminal reward; the privileged-value-critic ("oracle") question, whose first probe came back underpowered (256 independent episode labels cannot fit a 700k-parameter critic — a validated ridge-probe replacement is built but unrun); and league design — ungated self-play drifts and regresses, champion-gated pools starve (zero promotions in 12,288 episodes), and the AlphaStar-style ~35% live self-play mix is designed but unrun.

## 4. Challenge 2: Card representation and transfer

Brutal honesty first: the graph card encoder has never won on win rate. Four full-budget comparisons found parity on training decks; zero-shot transfer was null with the noise control transferring as well as the treatment; fine-tuning recovery was null; a text-embedding channel was actively harmful (deleting it improved play — one of only two findings that replicated across seeds). The one durable advantage is liveness: on unseen decks the hash agent's value estimates collapse and it pass-loops to the turn limit, while graph features cut that freeze rate ~40% (2.5% vs 4.1%, pooled over 6,000 games per arm, third replication). One short-budget zero-shot win-rate edge exists (.401 vs .365) but is two seeds against our own five-seed convention — suggestive, not claimable.

Two diagnoses explain the nulls. First, single-deck training converts any feature into a local card ID; deck diversity must be present from the first episode, and when it was, the agent gained cross-deck competence that mirror-specialization never had. Second, the feature space is blind on the axis that decides function: two counterspells at feature distance zero differ by 6 win-rate points in scripted play (.735 vs .675, 200-game calibrations) because counter-condition breadth is not a dimension, and candidate vectors carry no timing or target-availability information.

We also fixed a genuine representation defect — the flat encoding collapsed 86–97% of distinct boards into shared vectors; entity tokens made them distinct — and it bought no win rate at current opponent depth. Open and cheap: the built-but-unrun twin-deck test (same stats, all-new names — any drop is pure identity memorization), and the designed condition-feature experiment read out through behavior counters, not win rate. Whether card identity starts mattering against opponents that punish mechanical misreads is the standing untested prediction.

## 5. Challenge 3: Benchmarking

What each instrument actually measures:

- **Scripted heuristic opponent** (internal Elo anchor, 1000): a liveness and basic-competence gate. It has fixed exploitable gaps PPO finds in hundreds of episodes; making it stronger changed nothing.
- **1-ply search opponent**: the main yardstick, a real rung (.614 over the heuristic at 500 games after auditing). Caveats: it does not search combat at all, it is a *worse* pilot than the heuristic on four of six archetype decks, and its hidden-information advantage is worth ~0 (honest variant: .482 head-to-head). The audit itself was a finding: shared blindness to instant-speed play had inflated its edge by 16 points.
- **Depth ladder**: does not exist above 1 ply. Deeper search over a material evaluator adds nothing, so a graded ladder must vary evaluator quality, not depth.
- **Internal Elo**: orders agents (win rate alone couldn't), but is anchored entirely to opponents we wrote. Every "saturation" at 1.5k–6k episodes was saturation against that pool.
- **The engine's shipped depth-6 alpha-beta AI**: the only externally uncontaminated strength measure. Best agents score .22–.28 against it (50 games, ±.13). Caveat: on the simplest curriculum deck one agent already matched or exceeded it (.782 vs .650, underpowered), so the gap is a benchmark-deck number. Keep it held out; never train against it. This should be the headline metric.
- **Behavior counters with denominators, and freeze rate**: the instruments that diagnosed every failure and killed every false hypothesis. Standing rules: 500 games for claims, Wilson intervals, pre-register what a change cannot move, calibrate every opponent-deck pair empirically (archetype intuition ran backwards).

## 6. Dead ends — do not re-run these

- Reward shaping on a material evaluator: null twice, theoretically redundant, worsens stalls.
- Behavioral cloning scale-up and DAgger (on-policy imitation): capacity-limited ceiling; corrective labels moved win rate 0.000.
- Deeper search (2–3 ply) as ladder rungs: flat at .52; the evaluator is the ceiling.
- Strengthening or per-deck tuning the scripted opponent: nothing measurable.
- Graph-vs-hash encoder A/Bs at shallow opponent depth: null four times; the design can't separate condition-reading from name-reading.
- Text-embedding card channel under single-deck training: fitted noise; deleting it helps.
- Ungated self-play (drifts, regresses) and champion-gating alone (starves the league).
- Single-deck specialists and short cross-deck fine-tunes: brittle exploits, domain-shift failure at .20–.40.
- 10/25/100-game probes as evidence; behavior counts without opportunity denominators.
- Win rate as the readout for timing experiments on decks where the spell has no win-rate value (a 0-cast arm and a 127-cast arm finished dead even).
- An online neural critic probe at small episode counts (256 labels vs 700k parameters — underpowered by construction).
- IPC/batched-inference optimization: the engine dominates wall-clock; the thread-pinning config fix beat an engine patch (1.54x vs 1.28x).

## 7. The decision in front of us

**Direction A: put search on top of the learned network.** The held-out strong AI is our own 1-ply opponent's architecture at depth 6; the missing ingredient may be search, not learning. Test: wrap the current policy/value in shallow search (or expert iteration) and measure against the held-out AI. Falsified if policy-plus-search does not clearly beat the raw policy there.

**Direction B: build the adaptive league.** Every plateau was opponent starvation. Test: ~35% live self-play, scheduled pool entry, win-probability-weighted opponent sampling, deck diversity from episode one. One known hazard: pooled multi-deck training starves slow archetypes (control mirrors sat at .06–.08 while burn hit .64–.77 in the same run), so the sampler must correct for it. Success is breaking the ~6,000-episode plateau on the held-out-AI metric; falsified if it plateaus at the same place.

**Direction C: settle the card-understanding question cheaply.** The 5–6x cheaper curriculum decks finally make five-seed runs affordable. Test: the twin-deck identity probe plus condition-aware candidate features, read out through target-choice and timing counters rather than win rate (win rate is unpowerable here — see dead ends). Falsified if the twin gap is zero and condition features move no counter.

**Direction D: attack the starved decisions structurally.** Joint-consequence decisions fixed blocking without touching reward. Test: the yield-based interface plus candidates that carry timing and target-availability features, judged on instant-speed and opponent-turn cast rates. Falsified if those rates stay at effectively zero.

A and B test the thesis's "accumulated" half, C and D its "transferable" half. The evidence supports funding at most two before the next level-set.
