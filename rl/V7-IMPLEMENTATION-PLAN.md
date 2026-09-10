# v7 implementation plan — phases, gates, rollbacks, parallel lanes

*2026-09-10. Executes `ARCHITECTURE-V7-DESIGN.md` (all eight decisions
resolved). Written for several agents working concurrently: every lane
has a contract it consumes, a gate it must pass, and a rollback that
leaves `main` running v6.*

## 0. Rules that hold for every phase

1. **`main` always runs v6.** Every phase lands behind a switch: the Java
   class-init flag `-Drl.encoderV=7`, the server flag `--arch v7`, and
   feature flags below it (`--belief`, `-Drl.oppTracker`). A phase is not
   merged until `entattn_check.py` passes bit-identical and the v6
   loopback smoke (§0e) still runs.
2. **Contracts are files, and only files.** Lanes talk through
   `rl/WIRE-V7.md` (the consult schema), the artifact READMEs under
   `rl/artifacts/<name>_vN/`, and the fixtures under `rl/fixtures/v7/`.
   A change to a contract is a commit that names both consumers.
3. **One branch per lane** (`v7/lane-a` … `v7/lane-d`), merged to `main`
   by PR after the lane's gate passes. Each phase gate gets a tag
   (`v7-p0` … `v7-p7`). Rollback ladder, cheapest first: flag off →
   artifact version pinned back → tag checkout → `v6-baseline` tag.
4. **Gates are numbers in a file**, never a sentence in chat: each phase
   appends its gate readout to `rl/V7-VALIDATION.md`.
5. **Ground rules from `HANDOFF-ATTACK-JOINT.md` §6 apply**: Wilson
   intervals, nothing from fewer than 100 games called a level,
   pre-register what a phase cannot move, a probe must not be able to
   write what it measures (`--frozen`).

## 1. Prerequisites found on 2026-09-10

| item | state | consequence |
|---|---|---|
| GPU | RTX 3060 12 GB, torch 2.7.1+cu126, CUDA available in WSL | embedder pretraining fits; batch sizes sized for 12 GB |
| model downloads | PyPI reachable (`sentence-transformers` downloads); huggingface.co returns 200 | a pretrained text encoder is obtainable |
| Forge sources | **absent** in WSL (`~/forge-src` missing) | rebuild from the documented pin: `git clone --depth 50 https://github.com/Card-Forge/forge.git ~/forge-src && git checkout 670429bf` (`docs/getting-started.md` §2) |
| graph dataset | **absent** (`data/dataset.jsonl.gz` is gitignored and not built) | `python -m cardguru.dataset --cardsfolder ~/forge-src/forge-gui/res/cardsfolder --out data/dataset.jsonl.gz` (~1 min, §3 of the same doc) |
| decklist corpus | **38 lists** (4 in `decks/`, 34 `.dck` in `rl/`) | far too few for masked-card-in-deck; §2 phase 0c is a go/no-go |
| engine | XMage pin via `rl/setup_engine.sh`; RL sources in `rl/xmage-src`, recompiled by `rl/sync_engine_src.sh` | all Java work lands in `rl/xmage-src` and is class-init flag-gated |
| existing checks to extend | `entattn_check.py`, `oracle_gate.py`, `consult_cost.py`, `batch_check.py`, `update_profile.py`, `position_probe.py`, `rung0_replay.sh` | reuse, do not rewrite |

## 2. Phases

### Phase 0 — Contracts and prerequisites (1–2 days, four agents in parallel)

| id | deliverable | owner lane | gate |
|---|---|---|---|
| 0a | `rl/WIRE-V7.md`: consult schema (token groups, per-token field order, edge type index incl. `can_block`, `stack_above`, `refers_to`; hello carries `wire:7`, `card_emb` version, `d_c`); `rl/wire_fixtures.py` generating `rl/fixtures/v7/*.jsonl` (synthetic but schema-valid); `rl/wire_validate.py` | D (author); B and C consume | validator passes on every fixture; a deliberately broken fixture is rejected with the field named |
| 0b | Forge pin cloned; dataset built; `rl/cards/build_index.py` → `rl/artifacts/cards_v1/{index.json, oracle.jsonl, fields.jsonl}` (name and id → oracle text, printed fields, graph readouts) | A | ≥ 33k cards; **0 unknown** across every `.dck` in `rl/` and `decks/`; tokens resolved via tokenscripts |
| 0c | decklist corpus inventory and acquisition (MetaSurf snapshot export, public dumps, anything network allows); `rl/artifacts/decklists_v1/` | A | **go/no-go**: ≥ 3,000 lists → masked-card objective is in; below that, 1c is dropped and deck context is trained inside RL only |
| 0d | probe harness: `rl/probes/faithfulness.py` (linear readout over tokens, game-grouped hold-out), `rl/probes/leak.py` (generalises `oracle_gate.py` levels 1–3 to any hidden channel) | D | self-test on synthetic tokens: recovers planted fields at 1.0, refuses a planted leak |
| 0e | baseline freeze: tag `v6-baseline`; `rl/artifacts/v7/baseline.md` with `entattn_check` output, `consult_cost.py` numbers on cuda, and a 100-game rung-0 **smoke** of an existing v6 checkpoint (a smoke, not a level) | D | file exists; numbers recorded |

Phase 0 is the only phase with no code on the critical path that can be
skipped; everything downstream reads its contracts.

### Phase 1 — Card embedder L0 (Lane A, GPU; 4–6 days; after 0b)

| id | deliverable | gate |
|---|---|---|
| 1a | `rl/cardemb/data.py`: card record → three channels (text tokens with numbers bucketed; graph channel from the dataset's ability tree — v1 as the readout bag over answer classes / effect APIs / triggers / targets / synergy hooks through an MLP, v1.5 a GNN over the tree; printed fields explicit) | unit: every ladder card round-trips; held-out split written to disk (10%, by name) |
| 1b | `rl/cardemb/model.py`, `train_contrastive.py`: pretrained text encoder (MiniLM / DeBERTa-small class) **fine-tuned** jointly with the graph encoder, InfoNCE text↔graph, hours on the 3060; artifact `rl/artifacts/card_emb_v1/{emb.pt (N×128), model.pt, index.json, README.md}` | 1d gates |
| 1c | `train_masked.py`: masked-card-in-deck, only if 0c is go | held-out masked accuracy vs frequency baseline |
| 1d | `rl/cardemb/gates.py` — **the acceptance file**: linear probes on `e_card` recover P/T, MV, colours, types, 18 keywords, answer classes (thresholds per field, written before training); neighbour gates: Spell Snare / Force Spike apart, Cancel / Counterspell together, functional reprints nearest, PHASE8 swap pairs close; same probes on the held-out 10%; determinism across two seeds within tolerance | all pass → `card_emb_v1` is frozen and versioned |

Rollback: nothing consumes the artifact until Phase 4; a failed version
is simply not referenced. Pre-registered: cannot move any RL number.

### Phase 2 — Deck context L1 (Lane A; 2–3 days; after 1)

| id | deliverable | gate |
|---|---|---|
| 2a | `rl/deckctx/model.py`: 2-layer transformer over deck `e_card` + copy count, attention bias from `cardguru/fingerprint.py` enabler→payoff edges; outputs `c'_i`, `D`; ends with a per-card MLP | permutation invariance ≤ 1e-6; copy-count sensitivity > 0 |
| 2b | pretraining on the decklist corpus if 0c is go; else identity-initialised and trained in RL | held-out masked accuracy (if trained) |
| 2c | role probe: linear head reads wincon / enabler / answer off `c'_i` against fingerprint role labels | ≥ pre-set accuracy on held-out decks |

Artifact `rl/artifacts/deck_ctx_v1/`. Rollback as Phase 1.

### Phase 3 — Engine emission L2 (Lane B, Java; 6–8 days; after 0a; parallel with 1, 2, 4)

All behind `-Drl.encoderV=7`; the v6 path is not touched. Each sub-phase
is its own commit and its own tag.

| id | deliverable | gate |
|---|---|---|
| 3a | wire skeleton: `encoderV=7` emits v6 content **plus card identity per entity** (name / id, no features), hello `wire:7`; `SocketPolicyClient` writes the new keys | schema-valid on 100 recorded consults (`wire_validate.py`); v6 arm byte-identical to `v6-baseline` |
| 3b | fields and operators: P/T and abilities **after effects**, damage, counters, tapped / sick / attacking / blocking, castable, mana left if cast, legal targets, can attack / block, dies-to-SBA-as-is; player tokens with mana by colour; game token with decision type | per-operator unit checks in `Mage.Tests` style (`CombatMathCheck.java` precedent), one scenario each |
| 3c | edges: `can_block`, `stack_above`, `refers_to` (every candidate builder in `RLPlayer` carries the entity indices it acts on), stack modes / X | every edge endpoint valid; `refers_to` coverage = 100% of non-pass candidates over 1,000 consults |
| 3d | opponent knowledge tracker: game-event listener (reveal, zone change into hand from public zones, tutor, look-at, known top, face-down) → per-card knowledge; hand-slot tokens (origin, age, seen, known id); remaining-deck from the open decklist; opponent-action history | **leak gate** (`probes/leak.py`): policy-path emission invariant to the true hand; consistency: known ⊆ truth on every consult, checked against `-Drl.oracle` |
| 3e | dump and replay: `-Drl.entityDump` v7 format; `rung0_replay.sh` equality; counters `entityTrunc`, `unknownId` | replay byte-equal over 20 games; unknown ids = 0 on ladder decks |

Rollback: flag; tag per sub-phase. Pre-registered: cannot change any
v6 number.

### Phase 4 — Server L3–L6 (Lane C, Python; 6–8 days; after 0a using fixtures; parallel with 3)

All behind `--arch v7`; `e0` / `attn` / `lstmattn` / `entattn` untouched.

| id | deliverable | gate |
|---|---|---|
| 4a | wire v7 parse + validate; `V7Obs` (token groups, edge matrix over all groups, masks); handshake dims incl. `card_emb` version and `d_c`; checkpoint `dims` record extended | fixtures parse; every malformed fixture refused with the reason; `entattn_check.py` still bit-identical |
| 4b | token builders: **per-zone MLPs** (hand, battlefield, stack, graveyard, exile, library-known) + player / game / candidate / opponent builders; embedding lookup by id from `card_emb_vN` with the linear adapter; random-embedding mode for shape tests | shape tests; faithfulness probe after L3 recovers every planted field |
| 4c | encoder: edge-typed attention bias across all token groups, stack depth embedding, pre-LN, d 256 × 8 heads × 6 layers; no pooling | permutation invariance; masking; zero-edge arm equals plain attention exactly (R0 precedent); faithfulness probe after L4 |
| 4d | heads: pointer MLP + bilinear term; LSTM on the game token; masked softmax | logits invariant to padding; candidate-count probe from the game token |
| 4e | value trunk: own token builders, 4 layers, privileged rows enter here only | leak gate level 1–3 on the oracle channel |
| 4f | belief module: 2 layers, own optimiser, stop-gradient into shared builders, outputs → features on opponent tokens; `--belief off` masks them to zero | leak gate; with `--belief off` the net is bit-identical to 4e |
| 4g | PPO plumbing: buffers for `V7Obs`, BPTT windows, `p10_init_net.py --arch v7`, `--frozen`, `--device cuda`, batcher | `update_profile.py` peak RSS within the 16 GB cgroup at 5,000 steps; `consult_cost.py` per-consult cost recorded |

`rl/v7_check.py` collects every gate above into one runnable, exit 1 on
any failure, as `entattn_check.py` does for v6.

### Phase 5 — Integration and offline validation (Lanes B + C + D; 3–4 days; after 1, 3, 4)

| id | deliverable | gate |
|---|---|---|
| 5a | loopback: engine v7 → server v7, real embeddings | 100 consults, no refusals; handshake refuses a v6 driver and a wrong `card_emb` version |
| 5b | faithfulness on **real** dumps: 10k consults from heuristic-vs-heuristic games, game-grouped hold-out, after L3 and after L4 | every field and edge recovered above threshold; known-card set, remaining-deck multiset, instant-speed threat count recovered |
| 5c | leak gates end to end: oracle, tracker, belief | all three pass |
| 5d | throughput: `THROUGHPUT-LOCAL.md` protocol, v7 vs v6 on cuda | consults/s within a pre-set budget of v6 (the extra emission is the cost to watch) |
| 5e | replay determinism end to end | byte-equal |

Results into `rl/V7-VALIDATION.md`; tag `v7-p5`. This is the gate that
authorises any training.

### Phase 6 — Belief module training (Lane A; 2–3 days; after 3d, 4f)

Collect self-play with `-Drl.oracle` (the labels), **train offline
first** (the oracle-critic lesson: label count is the budget), probe
held-out log-likelihood of the true hand against the uniform-over-
remaining baseline; only then enable online. Rollback: `--belief off`.
Pre-registered: cannot change any policy logit (leak gate).

### Phase 7 — RL bring-up (after 5; needs the spell-value deck from Lane D)

| id | deliverable | gate |
|---|---|---|
| 7a | rung-0 smoke: 256 episodes on `--arch v7`; entropy, `value_ev`, counters, memory, throughput healthy | no crash, no OOM, `value_ev` not diverging; **pre-registered: cannot beat v6 on rungs 0–3 beyond noise** |
| 7b | the rung whose spells carry value (`DECK-VALUE-CHECK.md` follow-up, built by Lane D during phases 1–5) | heuristic-vs-heuristic shows measurable removal value before any agent is trained on it |
| 7c | counter readout on 7b: instant-speed and opponent-turn cast rates, target choice | the numbers, with intervals, in a result file |
| 7d | decision 7: target episode scale → throughput target and league design (`PHASE12-PERF-SCOPE.md`, `ENGINE-REWRITE-FEASIBILITY.md`) | a written scope, not a run |

## 3. Lanes, parallelism, and what each agent needs

```
Lane A  ML / GPU        0b 0c ──► 1a 1b 1c 1d ──► 2a 2b 2c ──────────────► 6
Lane B  Java engine     0a(consume) ──► 3a ─► 3b ─► 3c ─► 3d ─► 3e ──┐
Lane C  Python server   0a(consume) 0d ──► 4a 4b 4c 4d 4e 4f 4g ─────┼──► 5 ──► 7
Lane D  Infra / test    0a(author) 0d 0e ──► fixtures, 5d harness, 7b deck ┘
```

- **Critical path:** 0a → Phase 3 (Java) → 5 → 7. Lane B should start
  first and be staffed continuously.
- **Lane C can finish Phase 4 without Lane B** by working against the
  fixtures; the only Lane-B dependency is 5a.
- **Lane A is independent** until 5b (which needs real embeddings) and 6.
- **Lane D** owns the contracts and the instruments, and builds the
  spell-value deck for 7b while the others build.

Per-agent brief, minimum: the lane's rows above, `ARCHITECTURE-V7-DESIGN.md`,
`WIRE-V7.md`, the CLAUDE.md context protocol, and the rule that a gate
is a number in `V7-VALIDATION.md`.

## 4. Estimates

| phase | calendar, with lanes in parallel |
|---|---|
| 0 | 1–2 days |
| 1 + 3 + 4 concurrently | 6–8 days (Java is the long pole) |
| 2 | inside the same window, after 1 |
| 5 | 3–4 days |
| 6 | 2–3 days, overlaps 7a |
| 7a–7c | 1 week |
| **total to first pre-registered RL readout** | **~4–5 weeks** with 3–4 agents |

## 5. Risks, with the mitigation that is already in the plan

| risk | mitigation |
|---|---|
| decklist corpus stays tiny | 0c go/no-go; contrastive-only embedder; deck context trained in RL |
| knowledge tracker gets Magic's visibility rules wrong | leak gate before every merge; known ⊆ truth check against `-Drl.oracle`; tracker behind its own flag |
| per-consult emission cost grows (operators, edges, opponent tokens) | 5d budget pre-set; operators that miss it move to lazy emission |
| 290 tokens × d 256 × BPTT on a 12 GB GPU / 16 GB cgroup | 4g memory gate with `update_profile.py`; window size is a knob |
| class-init flags and a persistent driver JVM serving the wrong arm | handshake refuses; `wire:7` is checked, not assumed |
| agents drift on the contract | contracts are files; a contract change names both consumers; `wire_validate.py` runs in every lane's tests |
| a phase "passes" on a 10-game read | gates are numbers with intervals or exact checks; §0 rule 5 |
