# Branch archive (consolidation of 2026-09-10)

Every branch below was merged into `main` and then deleted. Each tip commit is
reachable from `main` (it is a parent of a merge commit there), so `git checkout <sha>`
recovers the branch exactly; `git branch <name> <sha>` re-creates it.

| branch | tip | date | last subject |
|---|---|---|---|
| `claude/card-guru-no-llm-d1zogb` | `7a09b7f` | 2026-08-31 | Add cardguru find: lexicon-driven NL-ish search, no LLM, any game |
| `claude/card-search-nl-dsl-pmunx7` | `0b3cf9f` | 2026-08-23 | Arm D: foil 0.110 -> 0.014 and H03 +0.039, but the revert rule fired. Reverted. |
| `claude/cardguru-deck-curriculum-f7vsnm` | `d2ab546` | 2026-08-13 | Phase 7c: PI-facing summary report |
| `claude/cardguru-e3-features-topn0q` | `a1c491f` | 2026-08-13 | PHASE-E3: two-seed scramble battery - the text block is a distractor on one deck |
| `claude/cardguru-engine-perf-sl17fn` | `13632fc` | 2026-08-13 | Phase 9 handoff doc: rebuild recipe, flag semantics, open items |
| `claude/cardguru-joint-attacks-7l0182` | `31d707c` | 2026-08-20 | Stream B is the priority: make its prompt self-sufficient |
| `claude/cardguru-p10-flagship-48r5lg` | `31d707c` | 2026-08-20 | Stream B is the priority: make its prompt self-sufficient |
| `claude/cardguru-phase-5-kickoff-2usq4s` | `b2fb329` | 2026-08-13 | Flagship spec: add P8Meta rows + fresh-meta deck pipeline to the league pool |
| `claude/cardguru-phase-8-transfer-65ili2` | `5397086` | 2026-08-13 | P8b final: re-eval tables + verdict - sub-CI transfer hint, real flash-timing shift |
| `claude/cardguru-pilots-2-17r9vj` | `7016b17` | 2026-08-13 | Phase 10 (4.4): resume-safe supervisor for the three pilots |
| `claude/cardguru-pilots-phase-10-g4ov6z` | `4184ee6` | 2026-08-14 | Pilot 2 (M3SelesnyaTokens): trained pilot barely beats the scripted one |
| `claude/graphify-ast-parsing-relevance-8xmeo8` | `ef05feb` | 2026-08-24 | Cycle 6: two ordering bugs; static modes 71.5/81.9 -> 76.2/80.8 |
| `claude/kturn-reference` | `31d707c` | 2026-08-20 | Stream B is the priority: make its prompt self-sufficient |
| `claude/metasurf-cardguru-consolidation-1sn75x` | `08e9171` | 2026-08-23 | Meta Lab meta-deck mode: sideboard planning against a real metagame |
| `claude/mtg-rules-search-feasibility-05siv8` | `5cfafeb` | 2026-08-11 | Phase 4 complete (M0-M2, M4): depth A/B written up, hard-stop verdict |
| `claude/repo-status-check-v92t78` | `6034b93` | 2026-09-08 | EXPERIMENTS.md: full experiment registry with process-failure ledger |
| `claude/v5-seed2` | `31d707c` | 2026-08-20 | Stream B is the priority: make its prompt self-sufficient |
| `claude/v6-entity-emission` | `31d707c` | 2026-08-20 | Stream B is the priority: make its prompt self-sufficient |
| `claude/v6-network` | `9e813bc` | 2026-08-23 | Oracle probe: both arms complete, verdict UNDERPOWERED as pre-registered |

Kept as live branches: `main` (everything above, consolidated) and `build/stackwise-campaign`
(the LLM-pilot / PokeChamp track, deliberately separate).

Note on E3: the `-Drl.e3` Java gate was not ported into the v6 encoder (state-layout
conflict, see README). It lives at `archive/claude/cardguru-e3-features-topn0q` tip
`a1c491f` — files `rl/xmage-src/{StateEncoder,RLPlayer,EpisodeRunner,RLDriverServer}.java`.
