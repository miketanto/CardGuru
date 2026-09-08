# Research brief: a PokeChamp-style gameplay agent for MTG

**Question:** PokeChamp ([arXiv 2503.04094](https://arxiv.org/abs/2503.04094), ICML 2025 spotlight) plays Pokémon at ~1300–1500 Elo with an untrained LLM. Can we build the MTG equivalent on top of CardGuru, and is there a paper/video in it?

**Verdict:** Yes, and we are unusually well positioned — but not for the reason one might guess. The hard part of PokeChamp was never the LLM; it was (a) a fast rules-enforcing simulator, (b) priors over hidden information, and (c) an honest evaluation harness. We already have credible versions of all three. What we lack entirely is the agent loop itself: nothing in CardGuru makes a decision during a game.

---

## 1. What PokeChamp actually is

Strip the branding and it is depth-limited minimax where an LLM replaces three modules, with **no training**:

1. **Action sampling** — the LLM proposes a handful of candidate moves per node (plus two heuristic baselines: best one-step-lookahead move, best rule-based switch), pruning a ~10^354 state space to a searchable tree.
2. **Opponent modeling** — hidden stats/sets are estimated from a 3M-game Showdown dataset (empirical distributions over EV spreads, items, movepools); likely opponent *actions* are predicted by the LLM prompted from the opponent's perspective.
3. **Value estimation** — leaf nodes are scored by an LLM prompt over explicit factors (move effectiveness, Pokémon remaining, speed, win probability) instead of rollouts to terminal states.

Supporting machinery: a **local Showdown simulator** for one-step lookahead ("turns to KO" per move is computed and put in the prompt — the LLM never does damage math), and **expected-value determinization** of stochastic transitions (damage rolls, miss chance) to keep the tree deterministic.

Results: 76% vs the best prior LLM bot (PokéLLMon), 84% vs the best rule-based bot, top 10–30% of the human ladder. Llama 3.1 8B inside the same harness still beats GPT-4o without the harness — **the scaffold, not the model, carries the result**. Known failure modes: stall matchups, excessive switching, and losing ~1/3 of ladder games to the 15s/turn clock.

## 2. Why MTG is harder — and where it's actually easier

**Harder:**
- **Branching.** Pokémon offers ≤9 actions per simultaneous turn. An MTG turn is dozens of sequential decision points (mulligan, land, casts, targets, modes, combat assignments) with priority windows on both turns; attack/block declaration alone is combinatorial. Naive minimax over priority passes is dead on arrival — search must operate over *lines* (sequenced plans), not individual priority actions.
- **Simulation cost.** Showdown resolves a turn in microseconds. XMage/Forge resolve in milliseconds-to-seconds, and Forge's own simulation AI spends ~80% of its time in `GameCopier`. Deep rollouts are unaffordable; the design must lean on shallow lookahead plus a strong static evaluation — which is exactly PokeChamp's shape anyway.
- **Game length.** 10–25 turns and both players act constantly, multiplying LLM calls per game.

**Easier:**
- **Hidden-information inference is *simpler* in constructed MTG.** PokeChamp needed 3M games to infer continuous EV spreads. In a defined meta, seeing 5–8 cards usually identifies the archetype, and the archetype's 60/75 is public (MTGTop8, MTGO/Melee decklists). Deck inference is a classification problem over a small prior, after which the opponent's *entire list* is approximately known — a stronger information position than PokeChamp ever reaches.
- **No clock (initially).** Offline matches vs bots have no turn timer, removing the constraint that cost PokeChamp a third of its ladder games.

## 3. What we already have, mapped onto PokeChamp's modules

| PokeChamp module | CardGuru asset | Gap |
|---|---|---|
| Local simulator | XMage in-process driver (`driver/CardGuruScenarioRunner.java`, ~100–330 ms/scenario) + scenario JSON spec | Driver is strict-scripted: executes predetermined lines, no interactive decisions |
| 3M-game priors over hidden state | Fingerprint graphs, threat profiles, break plans (`fingerprint.py`, `answers.py`, `threats.py`) — structural priors from decklist + KG | All pre-game/static; no in-game belief update from observed cards |
| "Turns to KO" lookahead heuristic in prompt | `answers.py` connect-verdicts (does answer X actually beat threat Y, with machine-readable reason), `intuition.py` answer windows, `goldfish.py` clock/consistency | Not yet computed *from a live board state* |
| Value-function prompt factors | Same modules supply computable factors: clock differential, linchpins on board, answers held vs threats presented, sole-provider exposure | No board-state encoder feeding them |
| 1,000-puzzle benchmark | 6,021 scenario records harvested from XMage's test suite + 32 hand-built scenarios + frozen RulesGuru set | Records are rules tests, not decision puzzles; need "find the winning line" curation |
| Elo evaluation vs baselines | The whole `benchmark/` methodology: execution-based grading, TREC pooling, blind adjudication, exact permutation tests, `agent_bridge.py` replay (zero-API-spend iteration) | Directly reusable; nothing missing |

The genuinely absent pieces: an **interactive engine bridge** (legal-action enumeration + decision injection at priority), a **board-state → prompt encoder**, an **in-game opponent belief tracker**, and the **search/policy loop**.

One non-obvious reuse: the strict-choose scenario runner is already a *line simulator*. An agent that proposes 3–5 candidate lines as scenario scripts can have each executed by the existing adjudicator (~300 ms each) and compare resulting states. That is PokeChamp's one-step lookahead, implemented with code we already ship — no interactive bridge needed for the *search* half, only for the *play* half.

## 4. The environment decision

Three options, not mutually exclusive:

1. **[mage-bench](https://github.com/GregorStocks/mage-bench)** (GregorStocks) — an existing XMage fork where LLMs play full games via MCP tools: 1v1 + Commander, Elo tracking, replays, blunder analysis, XMage's `COMPUTER_MAD` AI as baseline. This is MTG's Pokémon Showdown moment: a ready environment *and* a leaderboard of raw-LLM baselines to beat. Fastest path to a playing agent and to comparable numbers. Risk: young project; unclear how cleanly a custom agent loop plugs in — needs a day of code-reading to confirm.
2. **Extend our XMage driver** from strict-scripted to interactive: at each priority, serialize state + legal actions over stdio/IPC, block for a decision. Full control, integrates the adjudicator and cite machinery, works offline. Cost: real Java work inside `Mage.Tests`, and we re-implement match orchestration mage-bench already has.
3. **mtg-engine** (`~/Documents/mtg-engine`) — its `createBranch`/`rewindToEvent` timeline is *exactly* the fork-simulate-rewind primitive minimax wants, and it's ours. But effect coverage is 4 handlers out of ~200 Forge effect APIs; months from playing real decks. Long-term search substrate, not the starting point. (CardGuru's shapes/families mining can prioritize which effect handlers to implement — both projects consume Forge cardscripts.)

**Recommendation:** Phase 1 on mage-bench (or option 2 if its agent interface proves rigid), with our line-simulator lookahead running against our own XMage driver in parallel. Revisit mtg-engine when the agent's search depth, not the environment, becomes the bottleneck.

## 5. Proposed phases

- **Phase 0 — environment spike (days).** Run mage-bench locally; play one full game with a trivial agent; confirm we can substitute our own decision loop for theirs. Kill criterion: if the MCP bridge can't host a custom harness, fall back to extending our driver.
- **Phase 1 — policy-only agent (the PokéLLMon equivalent).** Board state → structured prompt → action. Tool access to CardGuru: pre-game `fingerprint`/`break_plan` on both decklists injected as strategy context; `answers` verdicts for interaction decisions. Fixed pair of well-understood meta decks (e.g. an aggro–midrange Standard pairing) to bound complexity, mirroring PokeChamp's 1v1 format. Baseline: win rate vs `COMPUTER_MAD` and vs a raw-LLM agent with no CardGuru tools. **This A/B is the paper's core claim in miniature: structured domain knowledge beats prose prompting at gameplay, extending the repo's existing thesis from retrieval to play.**
- **Phase 2 — opponent modeling.** Archetype classifier over cards seen (prior = meta decklist corpus); maintain believed-remaining-list; predict opponent's likely responses LLM-from-their-perspective, PokeChamp-style. Break plans recomputed against the *believed* list mid-game.
- **Phase 3 — lookahead + value.** Candidate-line generation (LLM proposes 3–5 lines including combat variants) → strict-choose simulation of each → LLM value prompt over computed factors (clock differential, linchpin delta, answers spent/held, life trajectory). Expected-value determinization for draws, exactly as PokeChamp handles damage rolls.
- **Phase 4 — benchmark + writeup.** Curate a decision-puzzle suite ("find the line": lethal puzzles, correct-block puzzles, counter-or-tap-out) from the 6,021-record corpus + RulesGuru; grade by execution through the adjudicator. Elo vs the mage-bench ladder. Apply the house methodology: fixed model across arms (the repo's own finding — model choice dominates interventions), ≥7 seeds, exact permutation tests, blind adjudication of blunder calls.

## 6. Paper / video angle

- **Novelty is real but has a clock on it.** PokeChamp covers Pokémon; mage-bench is a *benchmark of raw LLMs*, not an agent — nobody has published an expert-level structured MTG agent. "LLM minimax + machine-mined knowledge graph plays Magic" is a defensible paper; a raw-LLM-vs-harnessed-agent ladder run is an extremely legible video (mage-bench even publishes replays).
- **The claim to sell** is not "LLM plays Magic" (mage-bench already shows that, badly) but PokeChamp's claim transposed: *a small model in the right harness beats a frontier model without one* — with the harness built from a knowledge graph mined from the game's own machine-readable encoding. That is CardGuru's thesis with a win rate attached to it.
- **Honest risks:** MTG's branching may keep even a good agent well below expert play in open formats — constrain the format and say so; Commander multiplayer (mage-bench's marquee mode) adds politics, which PokeChamp's two-player minimax does not model — stay 1v1; and per-game LLM cost is 10–50× Pokémon's turn count — the `agent_bridge` replay trick and puzzle-first evaluation keep iteration cheap.

## Sources

- [PokéChamp paper (arXiv 2503.04094)](https://arxiv.org/abs/2503.04094) · [HTML version](https://arxiv.org/html/2503.04094v1) · [official repo](https://github.com/sethkarten/pokechamp) · [ICML 2025 poster](https://icml.cc/virtual/2025/poster/45207)
- [mage-bench](https://github.com/GregorStocks/mage-bench) · [project site](https://mage-bench.com/)
- [XMage](https://github.com/magefree/mage) · [Forge](https://github.com/Card-Forge/forge) · [Forge simulation-AI thread (GameCopier cost)](https://slightlymagic.net/forum/viewtopic.php?f=52&t=18041) · [open-mtg (Python MCTS subset)](https://github.com/hlynurd/open-mtg)
