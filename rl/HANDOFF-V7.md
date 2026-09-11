# Handoff — v7 build (design settled, nothing built)

*2026-09-10. Two prompts follow: a system prompt for any agent session on
this work, and the handoff prompt that starts a lane. Copy them verbatim;
fill `<LANE>`.*

---

## A. System prompt

```
You are working in the CardGuru repository (C:\Users\sutanto4\Documents\CardGuru,
symlinked as /home/user/CardGuru inside WSL), an RL project training agents to
play Magic: the Gathering against the XMage engine. Read CLAUDE.md first and
follow its context protocol: durable files over chat, small tool output, a
checkpoint block at ~70% context, Wilson intervals, nothing from fewer than
100 games called a level, pre-register what a change cannot move.

CODE EXPLORATION USES THE CODEBASE-MEMORY MCP, NOT grep/cat/find.
Two projects are indexed:
  - C-Users-sutanto4-Documents-CardGuru   (this repo: rl/, cardguru/, rl/xmage-src/)
  - C-Users-sutanto4-xmage-pin            (the XMage engine pin: GameEvent, Player,
                                           Permanent, StackObject, ContinuousEffects ...)
Rules:
  1. Call list_projects once at the start; index_status if results look stale.
  2. To find a symbol: search_graph (query= for natural language, name_pattern=
     for exact). Then get_code_snippet with the exact qualified_name. Never read
     a whole .java or .py file to find one function.
  3. For callers/callees, impact, or "who writes this field": trace_path
     (direction inbound/outbound, mode calls or data_flow). Not grep.
  4. For multi-hop questions (every emitter of a wire key, every reader of a
     flag, every Java class touching game.getCombat()): query_graph with Cypher.
  5. For orientation in an unfamiliar area: get_architecture with a path scope.
  6. Before any negative or exhaustive claim ("nothing writes g[15]", "no other
     caller"), run check_index_coverage on the paths or scopes involved and say
     whether the index had gaps. Coverage is best-effort, never proof.
  7. search_code (graph-enriched grep) only for literal strings: wire keys,
     flag names, log prefixes, error text.
  8. Engine questions (what events fire on a reveal, how a Permanent reports
     granted abilities, what Player.getPlayable returns) go to the xmage-pin
     project, not to guesses.
  9. Read source with offset/limit when the graph has already told you the
     line range. Grep for counters in logs, never cat a log.
 10. If a subagent explores for you, hand it these same rules and ask for
     qualified names and line ranges back, not file dumps.

Standing project rules you must not violate:
  - rl.encoderV, rl.legacyTieBreak, rl.debug, rl.cardFeatures, rl.oracle are
    class-init constants: a driver JVM that served one arm cannot serve another.
  - Never put a launch command and a pkill in the same shell call.
  - Never edit a lane script while a lane is running.
  - Findings go in files under rl/ and are committed with real messages;
    numbers only in chat are lost.
  - A probe must not be able to write what it measures (--frozen).
  - Commit messages end with: Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

---

## B. Handoff prompt

```
You are picking up the CardGuru v7 build as <LANE>  (A = ML/GPU, B = Java
engine, C = Python server, D = infra/test). Read, in this order, and do not
start work before finishing them:

  1. CLAUDE.md                              (context protocol, ground rules)
  2. rl/ARCHITECTURE.md                     (what exists: v6/entattn, measured)
  3. rl/ARCHITECTURE-V7-DESIGN.md           (what we are building; all 8 decisions resolved)
  4. rl/V7-IMPLEMENTATION-PLAN.md           (phases, gates, rollbacks, your lane's rows)
  5. LEVELSET.md §6                         (dead ends: do not re-run these)

## Context checkpoint

STATE:   Nothing of v7 is built. main = 38216a2 (clean, pushed). No lane
         branches exist yet. No run is in progress. Two published figures:
         https://claude.ai/code/artifact/65a42516-315d-4ae9-93b8-ef57f6003af0 (design)
         https://claude.ai/code/artifact/5ddc5f28-2fb3-4bd0-b081-cec44f95719d (roadmap)

DONE:    v6 architecture measured and written up (rl/ARCHITECTURE.md; params by
         instantiation: entattn 715,806; gap list §6, incl. g[15] never written and
         rung0_lane.sh defaulting to encoderV=2).
         v7 design agreed (rl/ARCHITECTURE-V7-DESIGN.md): shared card embedder
         (frozen + adapter, GPU-heavy pretraining), deck context, engine operators
         as features, per-zone MLPs over a shared identity, one state-graph
         transformer with refers_to/stack_above/can_block edges, LSTM on the game
         token, pointer + bilinear scorer, fully separate value trunk, opponent
         tokens (hand slots / remaining deck / actions) with a leak-gated tracker,
         a separate supervised belief module. Pass afterstate deferred. Open
         decklist in v1.
         Prerequisites checked (plan §1): RTX 3060 12 GB, torch 2.7.1+cu126, PyPI
         and huggingface.co reachable; Forge sources ABSENT in WSL; graph dataset
         ABSENT; decklist corpus = 38 lists.

OPEN:    Phase 0 in full (plan §2): 0a wire contract + fixtures + validator (D),
         0b Forge clone at pin 670429bf + dataset build + card index (A),
         0c decklist corpus go/no-go at 3,000 lists (A), 0d probe harness (D),
         0e v6 baseline freeze + tag (D). Then your lane's phase.

NEXT:    Lane A: clone Forge at the pin, build data/dataset.jsonl.gz per
                 docs/getting-started.md §2–3, then rl/cards/build_index.py (0b).
         Lane B: read rl/WIRE-V7.md when it exists; until then, map the v6
                 emission path with the graph tools (StateEncoder.encodeEntityView,
                 RLPlayer candidate builders, SocketPolicyClient hello) and draft
                 the encoderV=7 skeleton (3a) without changing the v6 path.
         Lane C: read rl/WIRE-V7.md when it exists; until then, map
                 policy_server.py (EntityAttnPolicy, Trainer._entity_obs, act,
                 _update_body, check_hello) and draft V7Obs + handshake (4a).
         Lane D: write rl/WIRE-V7.md from ARCHITECTURE-V7-DESIGN.md §L2/L3/§8
                 first; it unblocks B and C. Then wire_fixtures.py, wire_validate.py,
                 the probe harness, the v6-baseline tag.

GOTCHAS: - Every phase lands behind a flag (-Drl.encoderV=7, --arch v7, --belief,
           -Drl.oppTracker); main must keep running v6 and entattn_check.py must
           stay bit-identical.
         - Contracts are files (WIRE-V7.md, artifact READMEs, fixtures). A change to
           one is a commit that names both consumers.
         - One branch per lane (v7/lane-a .. v7/lane-d); merge by PR after the gate;
           tag v7-pN at each gate. Gates are numbers appended to rl/V7-VALIDATION.md.
         - /tmp dies with the container; anything that matters goes to rl/artifacts/.
         - The driver JVM is persistent; kill [R]LDriverServer between arms.
         - Long heredocs in the Bash tool get truncated; write scripts to a file
           with the Write tool and run the file.
         - The in-app browser cannot open published artifacts; preview local HTML
           via python -m http.server if you need to look.

COMMITS: All pushed to origin/main through 38216a2. Nothing uncommitted.

Start by confirming which lane you are, then execute NEXT for that lane.
At ~70% context, stop, write the checkpoint block above into
rl/HANDOFF-V7.md (update it, do not rewrite from memory), commit, push.
```

---

## C. Lane A checkpoint (2026-09-10, branch `v7/lane-a`)

Updated in place by the Lane A session; the block in §B is the generic
starting prompt and stays as written.

```
STATE:   - EMBEDDER ACCEPTED: rl/artifacts/card_emb_v8 (= overnight sweep config a: v6
           structure + literature stability recipe + 2-seed Procrustes-averaged artifact).
           G2 all pass (swap 16/16), G3 0.680, G1 32/33 probes; the one miss
           (ans_minus_toughness F1 0.725, 33 positives) is a stated deviation accepted by
           the user 2026-09-11 (V7-VALIDATION.md §1d v8). Consumers record card_emb_v8.
         - Sweep still running in WSL for the record: config b (serialised script view)
           seeds done 0-2, seed 3 running; then sweep2.sh runs c (= a + pos-weighted BCE
           readout) and d (= b + same). Results: rl/artifacts/cardemb_sweep/RESULTS.md.
           If c or d passes every gate: stage it as card_emb_v9 exactly as v8 was staged
           (copy emb.pt, emb_seed1.pt, gates.json, split.json, logs; index.json; README
           from v8 with numbers), retrain deck context (8 min), commit. Drop-in for consumers.
         - deck_ctx_v1 RETRAINED on card_emb_v8 and recorded (V7-VALIDATION.md §1c/2b and
           §2c correction rows): masked top-1 0.409 / top-10 0.746; roles 0.987 / 0.969 /
           0.770. Tags v7-p1 (embedder) and v7-p2 (deck context) on the lane branch.
         - PR: gh is not installed here; description in rl/PR-V7-LANE-A.md, open at
           https://github.com/miketanto/CardGuru/pull/new/v7/lane-a
         - Deck tensors for masked training cached: rl/artifacts/deck_ctx_v1/decks_cache.pt
           (12,612 decks, 85 s, gitignored; train_masked.py rebuilds it when the corpus
           changes). train_masked.py smoke-tested end to end.
         - 0c corpus FINAL: rl/artifacts/decklists_v1 (12,612 clean unique lists,
           Jul+Aug+Sep 2026, committed f403ddb). MTGO fetch finished; raw/ is gitignored.

DONE:    0b PASS  rl/artifacts/cards_v1 (34,642 faces + 836 tokens, 0 unknown over 38
                  decks; 123 post-pin Forge scripts overlaid from rl/cards/extra_scripts)
                  -> rl/V7-VALIDATION.md §0b
         1a PASS  rl/cardemb/data.py + tests/test_cardemb_data.py (printed round-trip
                  35,478/35,478; split.json 10.0 %) -> §1a
         1b code  rl/cardemb/model.py, train_contrastive.py (smoke: 5 s/epoch on 2k
                  cards; full: 33 s/epoch, held r@1 0.69 at epoch 8 — NOT a result)
         1d code  rl/cardemb/gates.py PRE-REGISTERED (commit 929e5b2) before any
                  epoch line was read
         2a PASS  rl/deckctx/model.py + data.py + tests/test_deckctx.py -> §2a
         1c/2b/2c code  rl/cardemb/train_masked.py, rl/deckctx/probe_roles.py
                  (thresholds pre-registered, commit fcff38a)
         0c code  rl/decklists/fetch_mtgo.py, build_corpus.py (mtgo.com month
                  archives: 250-450 events/month, ~20 lists/event, cold page = 25 s)

OPEN:    1. User opens the PR (link in STATE). Merge after review; main must still run v6
            (nothing under rl/xmage-src or the server changed on this branch).
         2. Sweep b/c/d results as they land: record each in V7-VALIDATION.md; v9 only if a
            config passes every gate (then retrain deck context, 8 min, and bump tags).
         3. Lane A next phase: 6 (belief module) waits on Lanes B/C (3d, 4f). -> table
            into V7-VALIDATION.md §1d (v4); if PASS: move rl/artifacts/card_emb_v1/README.md
            to the passing version with numbers, commit emb.pt (18 MB fp32) + gates.json +
            index.json + emb_seed1.pt (not model.pt/ckpt), and point train_masked.py
            --emb at it (absolute path accepted). Rename README: rl/artifacts/card_emb_v6/
            README.md is the contract text (written for v6) — move it to the accepted
            version's directory and fix the version string and the gate numbers.
            If v7 fails G3: next lever is the tree slice (0.263): a fitted vocabulary
            instead of hashed pieces (tree.py), pre-registered in V7-VALIDATION.md.
         2. when a version is accepted: rerun train_masked.py and probe_roles.py on it
            (see STATE), append correction rows to §1c/2b and §2c, update
            rl/artifacts/deck_ctx_v1/README.md dependency line, commit model_seed0.pt.
         3. Open a PR v7/lane-a -> main after the embedder is accepted (tag v7-p1 for
            Phase 1, v7-p2 for Phase 2 once 2b/2c are rerun).
         4. Phase 6 (belief) waits on Lanes B/C (3d, 4f).

NEXT:    Read rl/artifacts/card_emb_v1/train_runner.log; if ALLDONE, run gates.py.

GOTCHAS: - Driving WSL from the Bash tool: `$VAR`/`$(...)` inside wsl.exe -- bash -c
           are expanded by the Windows Git Bash first. Write the script to a file
           and run `wsl.exe -d Ubuntu -- bash -c 'bash /mnt/c/.../x.sh'`.
         - `nohup ... &` inside wsl.exe dies when wsl.exe returns. Detach with
           PowerShell Start-Process wsl.exe ... -WindowStyle Hidden (train_full.sh
           runs that way); same for long Windows python jobs (fetch_mtgo.py).
         - Forge short SHA is not fetchable: `git fetch --depth 1 origin <full sha>`.
         - mtgo.com event pages: 25 s cold, 0.3 s cached; urllib needs
           ProxyHandler({}) or it spends 1 s/request on proxy autodetect.
         - Heredocs with `\n` inside python -c strings get mangled by the Bash
           tool; use the Edit tool for lines containing escapes.

COMMITS: v7/lane-a pushed through the sweep-launch commit (git log). Uncommitted: rl/artifacts/card_emb_v1/README.md
         (draft), rl/artifacts/decklists_v1/raw (gitignored).
```
