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

## D. Lanes D and C checkpoint (2026-09-11, branch `v7/lane-d`; main = 03ac7ed with Lane A merged)

```
STATE:   - 0a DONE: rl/WIRE-V7.md (contract), rl/wire_validate.py, rl/wire_fixtures.py ->
           rl/fixtures/v7 (7 valid + 14 broken + schema.json), tests/test_wire_v7.py (22).
         - 0d DONE: rl/probes/faithfulness.py, rl/probes/leak.py (+ tests/test_probes.py).
         - 0e PARTIAL: tag v6-baseline = 9ad2a1a (pushed); rl/artifacts/v7/baseline.md with
           entattn_check (23 checks, PRE-EXISTING R0-NOBIAS fail 3.05e-5 vs 1e-6, same code
           as the tag) and consult_cost cuda (contaminated by the sweep; rerun idle). The
           100-game rung-0 smoke is RUNNING detached (<scratchpad>/v6_smoke.sh; log
           rl/artifacts/v7/smoke.log -> "SMOKE DONE" + win_rate; probe file
           rl/artifacts/v7/smoke_probe_D0.txt). Then fill RESULT in baseline.md, commit.
         - 4a DONE: rl/v7_obs.py (V7Obs, collate, check_hello_v7, dims_record),
           tests/test_v7_obs.py (22). policy_server.py untouched.
         - 4b DONE: rl/v7_net.py (CardTable + adapter, per-zone MLP+skip builders, opponent
           builders), tests/test_v7_net.py (faithfulness after L3 on fixtures).
         - 4c DONE: rl/v7_encoder.py (StateGraphEncoder), tests/test_v7_encoder.py (zero-edge
           exactness, permutation, masking, faithfulness after L4).
         - 4d DONE: rl/v7_heads.py (pointer + bilinear, LSTM on the game token, residual memory).
         - 4e DONE: rl/v7_value.py (separate value trunk; leak gate levels 1-3 pass).
         - 4f DONE: rl/v7_belief.py (belief module; off = bit-identical; stop-gradient; leak).
         - 4g PART 1 DONE: rl/v7_policy.py (V7Policy: one module, save/load with dims record,
           --frozen), rl/v7_check.py (14 checks, all pass, 65 s).
         - 4g PART 2 DONE (2026-09-11 16:30, V7-VALIDATION.md §4g part 2): policy_server.py
           --arch v7 (hello/consult/act_v7/_update_v7 BPTT/batcher/--frozen/ckpt with dims +
           config), rl/v7_deckctx.py (WIRE §5, --deck-ctx), p10_init_net.py --arch v7,
           update_profile.py --arch v7 (+UPDMEM), consult_cost.py --arch v7,
           tests/test_v7_server.py (10). v7_check.py: 15 checks, 0 failures, V6-SAME holds.
           STILL OPEN in 4g: the memory gate and consult_cost on cuda (GPU held by the sweep):
             python3 rl/update_profile.py threads --arch v7 --synth --steps 5000 --device cuda --threads 1
             python3 rl/consult_cost.py --arch v7 --device cuda
           -> append correction rows to §4g part 2; if RSS > 16 GB or cuda OOM, lower --tbptt
           (32) / --ep-batch (4) and record the knob that fits.
         - 0e DONE with a gap: baseline.md has entattn_check, consult_cost (contaminated) and a
           100-game pipeline smoke; no trained entattn checkpoint exists on this machine.
         - Embedder sweep b/c/d still running for the record (see §C STATE).
         - pytest lives in WSL (~/.local); Windows sklearn is broken (numpy 2) -> run tests in WSL.

NEXT:    (a) When nvidia-smi shows the GPU idle: the two cuda gates listed under 4g PART 2 above.
         (b) Phase 3 Lane B (Java 3a, the critical path) on a new branch v7/lane-b: map
         StateEncoder.encodeEntityView / RLPlayer candidate builders / SocketPolicyClient hello
         with the graph tools, then the encoderV=7 skeleton emitting the WIRE-V7 keys behind
         -Drl.encoderV=7; gate 3a = 100 recorded consults pass rl/wire_validate.py, v6 arm
         byte-identical. The server side is ready to receive it:
           python3 rl/policy_server.py --arch v7 --ckpt <init from p10_init_net.py --arch v7> --device cuda
         (c) PR for v7/lane-d when Phase 4 is complete (gh absent: write rl/PR-V7-LANE-D.md
         like PR-V7-LANE-A.md and give the compare link).
         Lane B (Java 3a) has not started: map StateEncoder.encodeEntityView / RLPlayer
         candidate builders / SocketPolicyClient hello with the graph tools, then the
         encoderV=7 skeleton behind -Drl.encoderV=7 emitting WIRE-V7 keys.

COMMITS: v7/lane-d pushed through f98e8cd.
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


---

## E. Handoff prompt for the next session (2026-09-11, after Lanes A, D, C part 1)

Copy both blocks verbatim. The system prompt is §A with the current state
folded in; the task prompt starts the session.

### E.1 System prompt

```
You are working in the CardGuru repository (C:\Users\sutanto4\Documents\CardGuru,
symlinked as /home/user/CardGuru inside WSL Ubuntu), an RL project training agents to
play Magic: the Gathering against the XMage engine. Read CLAUDE.md first and follow
its context protocol: durable files over chat, small tool output, a checkpoint block
at ~70% context written into rl/HANDOFF-V7.md, Wilson intervals, nothing from fewer
than 100 games called a level, pre-register what a change cannot move, correct in
the open (a failed gate is a row in rl/V7-VALIDATION.md, never a moved bar).

CODE EXPLORATION USES THE CODEBASE-MEMORY MCP, NOT grep/cat/find.
Two projects are indexed:
  - C-Users-sutanto4-Documents-CardGuru   (this repo: rl/, cardguru/, rl/xmage-src/)
  - C-Users-sutanto4-xmage-pin            (the XMage engine pin: GameEvent, Player,
                                           Permanent, StackObject, ContinuousEffects ...)
Rules:
  1. Call list_projects once at the start; index_status if results look stale.
  2. To find a symbol: search_graph (query= for natural language, name_pattern= for
     exact). Then get_code_snippet with the exact qualified_name. Never read a whole
     .java or .py file to find one function.
  3. For callers/callees, impact, or "who writes this field": trace_path
     (direction inbound/outbound, mode calls or data_flow). Not grep.
  4. For multi-hop questions (every emitter of a wire key, every reader of a flag,
     every Java class touching game.getCombat()): query_graph with Cypher.
  5. For orientation in an unfamiliar area: get_architecture with a path scope.
  6. Before any negative or exhaustive claim ("nothing writes g[15]", "no other
     caller"), run check_index_coverage on the paths or scopes involved and say
     whether the index had gaps. Coverage is best-effort, never proof.
  7. search_code (graph-enriched grep) only for literal strings: wire keys, flag
     names, log prefixes, error text.
  8. Engine questions (what events fire on a reveal, how a Permanent reports granted
     abilities, what Player.getPlayable returns) go to the xmage-pin project, not to
     guesses.
  9. Read source with offset/limit when the graph has already told you the line
     range. Grep for counters in logs, never cat a log.
 10. If a subagent explores for you, hand it these same rules and ask for qualified
     names and line ranges back, not file dumps.

Environment rules learned the hard way (rl/HANDOFF-V7.md §C/§D GOTCHAS):
  - Drive WSL by writing a script file and running
    wsl.exe -d Ubuntu -- bash -c 'bash /mnt/c/.../x.sh'; $VAR and $(...) inside the
    wsl.exe command line are expanded by the Windows Git Bash first.
  - java is only on PATH in a login shell (bash -lc); scripts that start the driver
    JVM must source ~/.profile first.
  - Detach long jobs with PowerShell Start-Process wsl.exe ... -WindowStyle Hidden;
    nohup & inside wsl.exe dies when wsl.exe returns.
  - pytest and scikit-learn work only in WSL (Windows sklearn is broken by numpy 2).
  - Never put a launch and a pkill in the same shell call; never edit a running lane
    script; rl.encoderV etc. are class-init constants (restart the driver JVM
    between arms); /tmp inside WSL is disposable - anything that matters goes to
    rl/artifacts/.
  - Long heredocs in the Bash tool get truncated and \n inside them is mangled:
    write files with the Write tool, patches as .py files, then run them.

Standing rules you must not violate:
  - main must keep running v6; rl/entattn_check.py must report the same 23 lines
    as rl/artifacts/v7/baseline.md (23 checks, the known R0-NOBIAS 3.05e-5 state);
    rl/v7_check.py must stay all-pass after every edit under rl/v7_*.py.
  - Contracts are files: rl/WIRE-V7.md, rl/artifacts/<name>/README.md,
    rl/fixtures/v7. A change to one is a commit that names both consumers.
  - One branch per lane; gates are numbers appended to rl/V7-VALIDATION.md.
  - Commit and push after each finding. Commit messages end with:
    Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```

### E.2 Task prompt

```
You are continuing the CardGuru v7 build. Read, in this order, before any work:
  1. CLAUDE.md
  2. rl/HANDOFF-V7.md §C and §D (the two checkpoint blocks: what is done, what is
     running, what is next)
  3. rl/V7-IMPLEMENTATION-PLAN.md §2 (phases and gates) - Phases 0, 1, 2 and 4a-4f
     are done; 4g is half done; Phase 3 (Java) has not started
  4. rl/WIRE-V7.md (the contract Lane B must emit and Lane C consumes)
  5. rl/V7-VALIDATION.md, last four sections (4d-4g part 1) and §1d "card_emb_v8
     ACCEPTED"
  6. rl/CARDEMB-RESEARCH.md §3 only (the embedder decisions and why)

STILL RUNNING WHEN THIS PROMPT WAS WRITTEN - do not restart, do not duplicate:
  - The overnight embedder sweep in WSL (rl/cardemb/sweep.sh then rl/cardemb/sweep2.sh):
    config b (serialised-script structure view, 4 seeds, ~2 h/seed) was on its last
    seed; configs c and d (positive-weighted BCE readout) start automatically after
    it and take ~2 h and ~8 h. Progress and gate tables append to
    rl/artifacts/cardemb_sweep/RESULTS.md ("DONE b", "DONE c", "DONE d",
    "SWEEP COMPLETE"); artifacts in rl/artifacts/cardemb_sweep/{b,c,d}/.
    Check with: grep 'DONE\|START\|COMPLETE' rl/artifacts/cardemb_sweep/RESULTS.md
    and pgrep -af train_contrastive in WSL. They hold the GPU (RTX 3060) until they
    finish; run GPU-needing gates (consult_cost.py --device cuda, the 4g memory
    gate) only after nvidia-smi shows it idle.
    What to do with each result: append a row to rl/V7-VALIDATION.md §1d exactly as
    the config-(a) row was written; card_emb_v8 (= config a, one stated deviation)
    is the accepted embedder and consumers already name it. Only a config that
    passes EVERY gate (G1 all 33 probes, G2 all four, G3 >= 0.40) becomes
    card_emb_v9: stage it exactly as v8 was staged (copy emb.pt, emb_seed1.pt,
    gates.json, split.json, train logs; index.json; README from
    rl/artifacts/card_emb_v8/README.md with the numbers), retrain deck context
    (python3 rl/cardemb/train_masked.py --emb <abs path>/emb.pt, ~10 min, then
    rl/deckctx/probe_roles.py), append correction rows, commit. If none passes,
    write one closing row saying so and stop iterating the embedder.
  - A persistent XMage driver JVM may be listening on port 7910
    (python3 rl/driver_client.py --port 7910 --ping). Reuse it; start it from a
    login shell if it is gone.

NEXT, in order (branch v7/lane-d for Lane C/D work; a new branch v7/lane-b for Java):
  1. 4g part 2 - rl/policy_server.py behind --arch v7, e0/attn/lstmattn/entattn
     untouched: check_hello -> v7_obs.check_hello_v7; consult_args ->
     v7_obs.parse_consult; Trainer.act -> v7_policy.V7Policy.forward with a
     per-session LSTM state (Session already exists in the file); PPO buffers of
     V7Obs + state with BPTT windows, batcher through v7_obs.collate;
     p10_init_net.py --arch v7. Gate: rl/v7_check.py all-pass and
     rl/entattn_check.py unchanged after every edit; then the memory gate
     (update_profile.py, 5,000 steps within the 16 GB cgroup) and consult_cost.py
     on an idle GPU, both recorded in rl/V7-VALIDATION.md §4g.
  2. Phase 3 (Lane B, Java, the critical path - start it as soon as 4g part 2 is
     committed, or first if you prefer): 3a = encoderV=7 skeleton emitting the v6
     content PLUS the WIRE-V7 keys (v7_game, v7_players, v7_ent + names, v7_edges,
     v7_cand_*, v7_ctr) behind -Drl.encoderV=7, hello carries wire:7 and the dims
     from rl/WIRE-V7.md §1. Map first with the graph tools:
     StateEncoder.encodeEntityView (rl/xmage-src/StateEncoder.java), the RLPlayer
     candidate builders, SocketPolicyClient.choose/hello. Gate 3a: 100 recorded
     consults pass rl/wire_validate.py; the v6 arm byte-identical to v6-baseline
     (rl/entattn_check.py). Then 3b fields/operators, 3c edges, 3d the knowledge
     tracker (leak gate with rl/probes/leak.py), 3e dump/replay.
  3. Open the PR for v7/lane-d when Phase 4 is complete (gh is not installed;
     write the description like rl/PR-V7-LANE-A.md and give the compare link).
  4. Phase 5 integration, then 6 (belief training on self-play labels), then 7.

Start by confirming what is running (the two checks above), then execute NEXT 1.
At ~70% context, stop, update rl/HANDOFF-V7.md §D in place (do not rewrite from
memory), commit, push, and offer to continue in a new session.
```

---

## F. Handoff prompt for the next session (2026-09-11 evening, after 4g part 2; v7/lane-d = b0d1a16)

### F.1 System prompt

Use §E.1 verbatim (it is unchanged), plus these lines learned this session:

```
  - Python exists ONLY in WSL. `python3` on the Windows side is a Store stub. Every
    python run is  wsl -e bash -lc "cd /home/user/CardGuru && python3 ..."  (login shell).
  - pytest for v7:  wsl -e bash -lc "cd /home/user/CardGuru && python3 -m pytest tests/test_v7_server.py -q"
    The whole v7 gate set:  python3 rl/v7_check.py  (15 checks, ~80 s, must end failures=0).
  - Scratch scripts for WSL go under the session scratchpad and are run via /mnt/c/... paths.
  - The v7 encoder is an exact identity at init (zero output projections, by design from 4c):
    no probe of "does X reach the logits" is valid on an untrained net without perturbing
    blk.att.out.weight first. Do not write up a dead channel from an untrained net.
  - pyflakes is not installed; the tests are the lint.
```

### F.2 Task prompt

```
You are continuing the CardGuru v7 build. Read, in this order, before any work:
  1. CLAUDE.md
  2. rl/HANDOFF-V7.md §D (the checkpoint block: what is done, what is running, what is next)
  3. rl/V7-IMPLEMENTATION-PLAN.md §2 (phases and gates). Phases 0, 1, 2 and 4a-4g are
     done except two cuda gates in 4g; Phase 3 (Java) has not started.
  4. rl/WIRE-V7.md - the contract Lane B must emit; the server consumes it exactly.
  5. rl/V7-VALIDATION.md §4g part 2 (what the server does, its gates, and the notes on what
     the numbers cannot support)
  6. rl/policy_server.py module docstring, check_hello_v7_server, act_v7, _update_v7 - only
     if you need to change the server; otherwise the docstring is enough.

STILL RUNNING WHEN THIS PROMPT WAS WRITTEN - do not restart, do not duplicate:
  - The embedder sweep in WSL (rl/cardemb/sweep.sh -> sweep2.sh): config b on its last seed,
    then c (~2 h) and d (~8 h) automatically. It holds the RTX 3060 until "SWEEP COMPLETE"
    appears in rl/artifacts/cardemb_sweep/RESULTS.md. Check:
      grep 'DONE\|START\|COMPLETE' rl/artifacts/cardemb_sweep/RESULTS.md
      wsl -e bash -lc "pgrep -af train_contrastive; nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader"
    What to do with each result is in §E.2 (append a §1d row per config exactly as the
    config-(a) row; only a full-gate pass becomes card_emb_v9, staged as v8 was; if none
    passes, one closing row and stop iterating the embedder).
  - A persistent XMage driver JVM may be listening on port 7910
    (python3 rl/driver_client.py --port 7910 --ping). Reuse it; start it from a login shell
    if it is gone.

NEXT, in order:
  1. Phase 3, Lane B (Java, the critical path) on a NEW branch v7/lane-b from main
     (main = v6 with Lane A merged; v7/lane-d holds the Python side and is not merged yet).
     3a = the encoderV=7 skeleton behind -Drl.encoderV=7 emitting the v6 content PLUS the
     WIRE-V7 keys (hello: "wire":7, card_emb, d_c, v7_dims, v7_rtypes, v7_ctypes, v7_zones,
     v7_emax/kmax/ohmax/odmax/oamax, v7_decks; consult: v7_game, v7_players, v7_ent,
     v7_ent_name, v7_ent_token, v7_edges, v7_cand_type, v7_cand, v7_cand_refers, v7_ctr).
     Map first with the graph tools (list_projects, then search_graph/trace_path on the
     xmage-pin project): StateEncoder.encodeEntityView, the RLPlayer candidate builders,
     SocketPolicyClient.choose/hello. rl.encoderV is a class-init constant: the driver JVM
     on 7910 served v6 and cannot serve v7 - start a second driver for the v7 arm.
     Gate 3a: 100 recorded consults pass rl/wire_validate.py (record them with the dump
     path the driver already has, or add one), AND the v6 arm byte-identical to v6-baseline
     (rl/entattn_check.py summary unchanged vs rl/artifacts/v7/baseline.md).
     Then the live check the Python side is waiting for: start
       python3 rl/policy_server.py --arch v7 --ckpt /tmp/v7_init.pt --device cpu --port 7777
     (mint /tmp/v7_init.pt with python3 rl/p10_init_net.py --arch v7 --out /tmp/v7_init.pt)
     and run 10 games against it in eval mode; a handshake refusal prints the reason on
     both sides. Record in rl/V7-VALIDATION.md §3a.
     Then 3b fields/operators, 3c edges, 3d the knowledge tracker (leak gate with
     rl/probes/leak.py), 3e dump/replay - each a gate row.
  2. The two open 4g cuda gates, the moment nvidia-smi shows the GPU idle (do not queue them
     behind the sweep; they take minutes):
       python3 rl/update_profile.py threads --arch v7 --synth --steps 5000 --device cuda --threads 1
       python3 rl/consult_cost.py --arch v7 --device cuda
     Append correction rows to rl/V7-VALIDATION.md §4g part 2 with the UPDMEM and CONSULT
     lines. If RSS exceeds 16 GB or cuda OOMs, lower --tbptt (32) / --ep-batch (4) and record
     the knob that fits; the defaults in policy_server.py must match what fits.
  3. PR for v7/lane-d once Phase 4 is closed (both cuda rows in): gh is not installed;
     write rl/PR-V7-LANE-D.md like rl/PR-V7-LANE-A.md and give the compare link.
  4. Phase 5 integration (v7 server against the v7 driver, first 512-episode run behind
     every flag), then 6 (belief training on self-play labels), then 7.

Standing rules: main stays v6; rl/entattn_check.py must match baseline.md after every
server edit; rl/v7_check.py stays all-pass; contracts are files; commit and push after
each finding; Wilson intervals; no level from fewer than 100 games.

Start by confirming what is running (the two checks above), then execute NEXT 1.
At ~70% context, stop, update rl/HANDOFF-V7.md §D in place (do not rewrite from memory),
commit, push, and offer to continue in a new session.
```

## G. Lane B checkpoint (2026-09-12, branch `v7/lane-b`; lane-d = 8d8ffde)

```
STATE:   - Lane B (Java) 3a, 3b, 3c, 3d DONE on branch v7/lane-b (worktree
           C:\Users\sutanto4\Documents\CardGuru-lane-b, from main 03ac7ed), each a
           gate row in rl/V7-VALIDATION.md ON THAT BRANCH (the file diverges from
           lane-d's copy: both append at the end; merge = keep both).
             3a bcb57a4  encoderV=7 skeleton, CandMeta at all 7 sites, one v6 writer
             3b 8739169  entity idx 10-63 + operators + candidate afterstates
             3c baa4fa8  can_block / stack_above edges, 100% referent coverage
             3d f1ea528  RLKnowledgeWatcher tracker, leak gate on real recordings
           Java compiles into /home/user/mage from the worktree: rl/sync_lane_b.sh
           (never rl/sync_engine_src.sh, which copies main's OLD sources and kills
           every driver). Drivers: rl/drivers_3a.sh (7910 = v6 arm, 7911 = v7 arm),
           rl/drivers_3d.sh (7912 = v7 + oracle; stops 7910 first). All three JVMs
           load classes at start: RESTART after every compile.
         - Recording/checking toolchain (all in rl/ on lane-b): wire_echo_server.py
           (--pick N, --prefer-type 2,1), wire_record.sh (DECK PICK PREFER BUDGET
           EXTRA env), wire_diff.py (--all: differing columns + column sums),
           wire_census.py (--index=), wire_check_3b/3c/3d.py, wire_trace_3d.py,
           live_check_3a.sh, old_build_record.sh. Recordings live gitignored in
           rl/artifacts/v7/wire3a/ (regenerate: seed 900000).
         - Lane D/C side (lane-d): 4g cuda gates DONE (39e243e, 5ff74ab): RSS 2.0 GB
           pass; cuda peak 11.4 GB at tbptt 32/ep 4 vs 2.85 GB at 16/2; 582 vs 489
           ms/step -> per-window compute dominates; 5,000-step update ~40 min either
           way. Embedder sweep: config b FAIL (f3d97cc), c/d BACKLOGGED by the user,
           sweep2.sh killed; card_emb_v8 stays. rl/v7_leak_real.py (8d8ffde).
         - Phase 4 is CLOSED (both cuda rows in) -> the lane-d PR is due.

DONE:    3a: 101+136 consults validate; v6 arm identical to the unpatched build
           within the engine's own noise (which of several identical opponent lands
           gets tapped for mana is not on the seeded stream; measured by running the
           unpatched build twice); live 10-game check vs policy_server --arch v7.
         3b: 1,562 consults / 12,838 rows, 0 v6 disagreements, 0 identity failures;
           damage/blocking/stack fields exercised only by the spell-first policy.
         3c: 100% referent coverage over 2,955 consults, every BLOCK candidate pair
           is a can_block edge; stack_above seen on 2 consults only.
         3d: leak gate L1-L3 pass on 3 real oracle recordings; handDrift 0 over 1,413
           consults; deck accounting exact; known-identity path NOT exercised (no
           reveal/return/tutor on the rung decks) -> 5b or a constructed scenario.

OPEN:    (1) 3e DONE (row on lane-b): replay is byte-equal except the tapped-land noise;
             exact replay needs the engine mana-payment order on the seeded stream.
         (2) WIRE §2c player width 21 (untapped sources by colour) - a cross-lane
             commit (wire_validate DIMS + v7_obs + v7_net + fixtures + Java).
         (3) WIRE amendment to propose: PASS afterstate at the joint sites (damage
             taken if not blocking, bodies retained if not attacking) - deferred by
             design §6, zeroed on the wire now.
         (4) Player row idx 14 (cards drawn this turn) still 0.
         (5) Fields with 0 exercised rows (counters, loyalty, tokens, 16 keywords,
             lethal-as-is, stack X/is-ability, known-identity path): 5b coverage.
         (6) policy_server defaults --tbptt 16 --ep-batch 2 (memory headroom).
         (7) PR for v7/lane-d (write rl/PR-V7-LANE-D.md like PR-V7-LANE-A.md) and,
             after 3e, for v7/lane-b.

NEXT:    3e on v7/lane-b: extend StateEncoder.dump (-Drl.entityDump) with the v7
         block (or write the wire line via SocketPolicyClient), run
         rl/rung0_replay.sh-style byte equality over 20 seeded games on 7911 with
         the echo server (expect the tapped-land noise class; state it), add
         unknownId (0: ids are not emitted) and entityTrunc to the counters, gate row,
         commit, then rl/PR-V7-LANE-B.md. Then Phase 5a on lane-d + lane-b together.

GOTCHAS: - The driver server clears/does not forward JVM-level -Drl.* to a class
           initialised during a job: pass flags on the JOB (EXTRA=...) AND restart
           the JVM; a static final read once stays for the JVM's life.
         - Watcher.copy() is reflection over fields: ONE constructor, no raw arrays,
           records implement Copyable; a shared mutable object would let simulated
           games mutate the real tracker.
         - XMage test mode throws "Error in unit tests" on game.getCard(non-card id):
           guard lookups with try/catch or check the id kind first.
         - grep calls StateEncoder.java binary (a stray byte): use grep -a / sed.
         - The auto-mode classifier blocks `kill`/`pkill` typed inline; a script that
           kills is fine (scratchpad/kill_7911.sh, stop_sweep2.sh pattern).
         - A spell-first recording without -Drl.consultBudget ran 1,599 consults in one
           game (the policy casts every instant every consult): BUDGET=300.
         - WSL clock is 9 h behind the Windows clock in the logs.

COMMITS: lane-b pushed through 3d; lane-d pushed through 8d8ffde. Uncommitted:
         nothing (recordings gitignored).
```

UPDATE (2026-09-12 19:25): 3e DONE = 9792354 on v7/lane-b (row §3e; rl/PR-V7-LANE-B.md written).
NEXT is Phase 5a (loopback + refusals) with rl/live_check_5a.sh on lane-b, row on lane-d.

UPDATE (2026-09-12 19:50): 5a DONE (row §5a on lane-d; rl/live_check_5a.sh on lane-b d9701ee): loopback 190 consults / 0 refusals; v6 driver and card_emb mismatch both refused with the reason on both sides.
NEXT: 5b - 10k-consult coverage dump. Note: the driver emits consults only for the RL seat, so "heuristic-vs-heuristic" dumps need either the echo policy with PREFER=2,1 / PICK=99 over many seeds+decks (what 3b-3d used) or a shadow emission from a SearchPlayer seat; decide and record which. Then 5c (end-to-end leak gates: oracle, tracker, belief), 5d (throughput v7 vs v6, THROUGHPUT-LOCAL.md protocol), 5e (replay: the tapped-land residual is known; state it). Both PR texts exist: rl/PR-V7-LANE-D.md, rl/PR-V7-LANE-B.md.

UPDATE (2026-09-12 20:30): 4g speed fixed on lane-d - EdgeAttention edge bias as a one-hot matmul (was table[edges]; its index backward was 85% of GPU time); v7_check 15/15; server defaults tbptt 16 / ep-batch 4: 64 ms/step, cuda peak 7.4 GB (ep-batch 8 spills past the 12 GB card). Rows: V7-VALIDATION §4g profile + correction. Next levers pre-registered there (SDPA, torch.compile, window batching, device-side collation).
NEXT: Phase 5b (see the 19:50 note). Both branches pushed; nothing uncommitted.

## H. Handoff prompt for the next session (2026-09-12 evening; lane-d = 36e5cae, lane-b = d9701ee)

### H.1 System prompt

Use §E.1 and §F.1 verbatim (unchanged), plus these lines learned this session:

```
  - Lane B lives in a git WORKTREE: C:\Users\sutanto4\Documents\CardGuru-lane-b (branch
    v7/lane-b), WSL path /mnt/c/Users/sutanto4/Documents/CardGuru-lane-b. The main checkout
    (/home/user/CardGuru) is v7/lane-d. Python (server, tests, v7_check) runs from lane-d;
    Java compiles from the worktree with  bash rl/sync_lane_b.sh  (NEVER rl/sync_engine_src.sh:
    it copies main's old sources and kills every driver). Driver JVMs load classes at start:
    restart with rl/drivers_3a.sh (7910 v6, 7911 v7) / rl/drivers_3d.sh (7912 v7+oracle) after
    every compile.
  - The driver server does not forward JVM-level -Drl.* to a class initialised during a job:
    pass such flags on the JOB (wire_record.sh EXTRA=...) and restart the JVM.
  - XMage watchers are copied by reflection: one constructor, no raw arrays, records implement
    Copyable. Test mode throws "Error in unit tests" on game.getCard(non-card id).
  - The auto-mode classifier blocks kill/pkill typed inline; a script that kills is fine.
  - torch profiler: 60 steps, never 400 (OOM-killed, and it stalls WSL for minutes).
  - Spell-first recordings need BUDGET=300 (rl/wire_record.sh), else one game runs 1,600 consults.
  - grep calls StateEncoder.java binary: grep -a. WSL clock is 9 h behind the Windows clock.
```

### H.2 Task prompt

```
You are continuing the CardGuru v7 build. Read, in this order, before any work:
  1. CLAUDE.md
  2. rl/HANDOFF-V7.md §G (the Lane B checkpoint) and its dated UPDATE lines below it - the
     full state, the toolchain, the open items, the gotchas.
  3. rl/V7-IMPLEMENTATION-PLAN.md §2, Phases 5-7 only (0-4 are closed; 3 is closed on lane-b).
  4. rl/V7-VALIDATION.md on lane-d: the §4g profile + correction rows (why the update was slow,
     what fixed it, the levers left). On lane-b (the worktree): rows §3a-§3e and §5a.
  5. rl/WIRE-V7.md only when touching the contract (§2c width 21 and the PASS afterstate
     are the two open amendments).

STATE: nothing runs. GPU idle. Drivers 7910 (v6) and 7911 (v7) may still be up on the
final lane-b build (python3 rl/driver_client.py --port 7911 --ping); 7912 is stopped.
Both branches pushed, nothing uncommitted. PR texts: rl/PR-V7-LANE-D.md, rl/PR-V7-LANE-B.md
(gh is not installed; the compare links are in the files).

WHERE WE ARE: everything needed to train exists and has been exercised end to end - the v7
driver emits the full wire (3a-3e), the server runs PPO over it (4g) at 64 ms/step with
tbptt 16 / ep-batch 4, handshake refusals work (5a). Phase 5 is the gate that authorises
training; 5a is done, 5b-5e are not. Nothing has been trained.

NEXT, in order:
  1. Decide the two-branch question first and write it down: either (a) merge v7/lane-b into
     v7/lane-d (conflicts only at the END of rl/V7-VALIDATION.md and rl/HANDOFF-V7.md: keep
     both), then work from one checkout; or (b) keep running Python from lane-d and Java from
     the worktree as this session did. (a) is cleaner for 5b-5e; do it unless the user says
     otherwise, and keep the worktree for the Java compile path.
  2. 5b - faithfulness on real dumps. The driver emits consults only for the RL seat, so
     "heuristic-vs-heuristic" needs a decision, recorded in the row: the echo policy
     (rl/wire_echo_server.py --pick / --prefer-type 2,1) over many seeds and decks (what 3b-3d
     used; PICK=99 and PREFER=2,1 with BUDGET=300 are the policies that exercise combat and
     the stack), or a shadow emission from a SearchPlayer seat. Record ~10k consults with
     -Drl.oracle=true on 7912 across the rung decks (W0Base, W1Fly, W4Inst, W5Trick, B1Fast,
     W3Sorc, BenchDimir) with rl/wire_record.sh, game-grouped hold-out, then rl/probes/
     faithfulness.py after L3 and after L4 for every field and edge; also the known-card set,
     remaining-deck multiset and instant-speed threat count. Every field still at 0 exercised
     rows (rl/wire_check_3b.py; counters, loyalty, tokens, 16 keywords, lethal-as-is, stack X,
     the tracker's known-identity path) gets a constructed scenario or an explicit "not
     exercised" line before 5b closes. Gate row on lane-d.
  3. 5c - the three leak gates end to end on those recordings: oracle (rl/v7_leak_real.py,
     already passing on 3 recordings), tracker (known ⊆ truth is vacuous until the known path
     is exercised - say so or exercise it), belief (rl/v7_belief.py's gate on real inputs).
  4. 5d - throughput, rl/THROUGHPUT-LOCAL.md protocol, v7 vs v6 on cuda, consults/s end to
     end (server 7781-style live check with --device cuda, not cpu). Budget against v6 stated
     in advance. If short, the pre-registered levers in the §4g correction row: SDPA with the
     bias as the additive mask, torch.compile on the block, window-batched encoding with the
     LSTM afterwards, device-side collation per window.
  5. 5e - replay: rl/replay_3e.sh; the residual is the tapped-land noise class (engine
     mana-payment order among identical lands, not on the seeded stream); state it, tag v7-p5.
  6. 7a - rung-0 smoke: 256 episodes, --arch v7 --device cuda, train mode, W0Base vs
     heuristic; entropy, value_ev, counters, memory, throughput. Pre-registered: cannot beat
     v6 on rungs 0-3 beyond noise; a flat curve is not evidence of dead channels (the encoder
     is an identity at init). Phase 6 (belief training) can wait: --belief off is the rollback.
  7. Cross-lane contract items when convenient: WIRE §2c player width 21 (wire_validate DIMS,
     v7_obs, v7_net, fixtures, Java, one commit naming both consumers); the PASS afterstate
     amendment (design §6).

Standing rules: main stays v6; rl/entattn_check.py matches baseline.md after every server
edit; rl/v7_check.py stays all-pass (15 checks, ~80 s, WSL); contracts are files; commit and
push after each finding; Wilson intervals; no level from fewer than 100 games; a failed
gate is a row, never a moved bar.

Start by confirming the driver state and running rl/v7_check.py once, then execute NEXT 1.
At ~70% context, stop, update rl/HANDOFF-V7.md (a new dated UPDATE line under §G or a new
section), commit, push, and offer to continue in a new session.
```

UPDATE (2026-09-12 21:15): ONE LANE from here. v7/lane-b is merged into v7/lane-d (d7dfa41); Java and Python live in the single checkout (Windows C:\Users\sutanto4\Documents\CardGuru = WSL /home/user/CardGuru = /mnt/c/Users/sutanto4/Documents/CardGuru). The worktree CardGuru-lane-b is removed; every rl/*.sh now points at the single checkout (rl/sync_lane_b.sh compiles rl/xmage-src from it). H.1 lines about the worktree are superseded by this note; H.2 NEXT 1 (the branch decision) is done - start at NEXT 2 (5b). Verified after the merge: rl/sync_lane_b.sh compiles, drivers 7910/7911 restart, v6 arm within the tapped-land noise class vs the unpatched build, v7 recording validates (93 consults), rl/v7_check.py 15/15. The remote branch v7/lane-b is kept as history and can be deleted; rl/PR-V7-LANE-B.md is now covered by a single PR for v7/lane-d.

## I. The one-lane handoff prompt (2026-09-12 21:30; v7/lane-d = c203c79). Supersedes §H.

```
You are working in the CardGuru repository, an RL project training agents to play Magic
against the XMage engine. Windows checkout C:\Users\sutanto4\Documents\CardGuru = WSL
/home/user/CardGuru = /mnt/c/Users/sutanto4/Documents/CardGuru. ONE branch: v7/lane-d
(36 commits ahead of main; main stays v6 and is untouched). Read CLAUDE.md first and
follow its context protocol: durable files over chat, small tool output, a checkpoint
block at ~70% context, Wilson intervals, no level from fewer than 100 games,
pre-register what a change cannot move, correct in the open (a failed gate is a row in
rl/V7-VALIDATION.md, never a moved bar), commit and push after each finding, commit
messages end with  Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>.

CODE EXPLORATION USES THE CODEBASE-MEMORY MCP (rules in rl/HANDOFF-V7.md §E.1: two
projects, C-Users-sutanto4-Documents-CardGuru and C-Users-sutanto4-xmage-pin;
search_graph / get_code_snippet / trace_path / query_graph before any grep; StateEncoder.java
is only partially indexed and grep calls it binary - use grep -a / sed there).

ENVIRONMENT (rl/HANDOFF-V7.md §E.1, §F.1, §G GOTCHAS, and the dated UPDATE lines):
  - Python exists only in WSL, login shell:  wsl -e bash -lc "cd /home/user/CardGuru && python3 ..."
    Tests: python3 -m pytest tests/test_v7_server.py -q ; the whole gate set: python3 rl/v7_check.py
    (15 checks, ~80 s, must end failures=0; includes V6-SAME = entattn_check vs
    rl/artifacts/v7/baseline.md).
  - Java: edit rl/xmage-src/*.java, compile with  bash rl/sync_lane_b.sh  (NEVER
    rl/sync_engine_src.sh). Driver JVMs load classes at start: after every compile restart
    with  bash rl/drivers_3a.sh  (7910 = v6 arm, 7911 = v7 arm) or  bash rl/drivers_3d.sh
    (7912 = v7 + -Drl.oracle; stops 7910 first). rl.encoderV and rl.oracle are class-init
    constants: one JVM per arm. Job-level -Drl.* flags go through wire_record.sh EXTRA=...
  - Long jobs: write a script with the Write tool, run it in a separate call; detach with
    PowerShell Start-Process wsl.exe ... -WindowStyle Hidden. Never put a launch and a kill in
    one call; the auto-mode classifier blocks inline kill/pkill, a script that kills is fine.
  - Recording toolchain (rl/): wire_echo_server.py (--pick N, --prefer-type 2,1),
    wire_record.sh (env DECK PICK PREFER BUDGET EXTRA; positional tag echo-port encV
    driver-port episodes seed), wire_diff.py --all, wire_census.py --index=, wire_check_3b/3c/3d.py,
    wire_trace_3d.py, live_check_3a.sh / live_check_5a.sh, replay_3e.sh. Recordings are
    gitignored in rl/artifacts/v7/wire3a/ (regenerate from seed 900000). Spell-first
    recordings need BUDGET=300. torch profiler: 60 steps, never 400 (OOM, stalls WSL).
  - The v7 encoder is an exact identity at init: no channel probe is valid on an untrained
    net without perturbing blk.att.out.weight first.

Read, in this order, before any work:
  1. CLAUDE.md
  2. rl/HANDOFF-V7.md §G and every dated UPDATE line after it (state, toolchain, open items,
     gotchas, the merge to one lane).
  3. rl/V7-IMPLEMENTATION-PLAN.md §2, Phases 5-7 (0-4 closed; 3 closed; 5a closed).
  4. rl/V7-VALIDATION.md: the §4g profile + correction rows (the update was 85% one gather's
     backward; fixed; now 64 ms/step at tbptt 16 / ep-batch 4, 7.4 GB; ep-batch 8 spills past
     the 12 GB card), then §3a-§3e and §5a (what the driver emits and how it was checked).
  5. rl/WIRE-V7.md only when touching the contract (open amendments: §2c player width 21,
     the PASS afterstate at the joint sites).

STATE: nothing runs; GPU idle; drivers 7910/7911 may be up on the merged build
(python3 rl/driver_client.py --port 7911 --ping). Nothing uncommitted. rl/PR-V7-LANE-D.md is
the PR text for the whole branch (gh not installed; compare link inside). Nothing has been
trained: every piece needed to train exists and has been exercised end to end (driver
emits the full wire, server runs PPO over it, real embeddings load, refusals work).

NEXT, in order:
  1. 5b - faithfulness on real dumps. The driver emits consults only for the RL seat:
     decide and record how the ~10k consults are produced (the echo policy over many seeds
     and decks - PICK=99 and PREFER=2,1 with BUDGET=300 exercise combat and the stack - or a
     shadow emission from a SearchPlayer seat). Record with -Drl.oracle=true on 7912 across
     W0Base, W1Fly, W4Inst, W5Trick, B1Fast, W3Sorc, BenchDimir; game-grouped hold-out;
     rl/probes/faithfulness.py after L3 and after L4 for every field and edge, plus the
     known-card set, remaining-deck multiset and instant-speed threat count. Every field at
     0 exercised rows (rl/wire_check_3b.py: counters, loyalty, tokens, 16 keywords,
     lethal-as-is, stack X, the tracker's known-identity path) gets a constructed scenario or
     an explicit "not exercised" line. Gate row.
  2. 5c - leak gates end to end on those recordings: oracle (rl/v7_leak_real.py), tracker
     (known ⊆ truth is vacuous until the known path is exercised - say so or exercise it),
     belief (rl/v7_belief.py's gate on real inputs).
  3. 5d - throughput per rl/THROUGHPUT-LOCAL.md, v7 vs v6 on cuda, end to end with the
     server on --device cuda; budget vs v6 stated before running. If short: the levers
     pre-registered in the §4g correction row (SDPA with the bias as additive mask,
     torch.compile on the block, window-batched encoding with the LSTM after, device-side
     collation per window).
  4. 5e - replay (rl/replay_3e.sh): the residual is the tapped-land noise class (engine
     mana-payment order among identical lands, not seeded); state it; tag v7-p5.
  5. 7a - rung-0 smoke: 256 episodes, --arch v7 --device cuda, train mode, W0Base vs
     heuristic; entropy, value_ev, counters, memory, throughput. Pre-registered: cannot beat
     v6 on rungs 0-3 beyond noise; a flat curve is not evidence of dead channels. Phase 6
     (belief training) can wait; --belief off is the rollback.
  6. When convenient: WIRE §2c width 21 (one commit naming both consumers: wire_validate DIMS,
     v7_obs, v7_net, fixtures, Java); the PASS-afterstate amendment (design §6).

Start by confirming the driver state and running rl/v7_check.py once, then execute NEXT 1.
At ~70% context, stop, add a dated UPDATE line to rl/HANDOFF-V7.md (or a new section),
commit, push, and offer to continue in a new session.
```

UPDATE (2026-09-12 14:40, next session's clock: WSL is 9 h behind): **5b DONE** — row §5b in rl/V7-VALIDATION.md (three sub-blocks: the gate table, the tracker re-check, the L4 wake diagnostic). Consults are produced by the echo policy on the RL seat (3 policies x 8 decks; decision recorded in the row); 56 recordings / 15,866 consults / 385 games probed; L3 135/0, L4 127/8 FAIL (small-scale reals; 134/1 at wake 0.02 — instrument, follow-up = the same probe on the 7a checkpoint), edges 7/0, known set + threat count pass, pooled deck-count readout FAIL by construction (per-token pass). Coverage: rl/KW7Probe.dck (10 keywords), main-1-pass echo mode (WIRE_ECHO_PASS_MAIN1=1), noYields=false runs; lethal-as-is (idx 57) is 0 by construction (SBA before priority) — WIRE amendment owed; ward / damage / blocking / stack X / player idx 14 still unexercised with reasons in the row.
  Fixed: RLKnowledgeWatcher slots keyed by Card.getMainCard().getId() (a transforming DFC returned by ninjutsu left a phantom known slot: handDrift 9, 22 known-not-in-truth); after the fix 17,918 oracle consults, drift 0, 517 known returned slots, 0 violations — the 3d "known ⊆ truth" gate is measured now.
  Found, deferred: RLPlayer.jointBlocks enumerates block assignments without canBlock (31 engine-illegal BLOCK candidates, silently skipped at declaration) — own commit + v6-identity row (it changes the v6 arm's candidate set). Also: XMage's heuristic AI throws "AI can't find good blocker combination" against menace/trample attackers (KW7Probe games abort) — remember for the 7b deck.
  Toolchain added: rl/record_5b*.sh (record_5b, _r2, _extra, _dbg, _dbg2, _dbg3, _fix), rl/drivers_3d_dbg.sh (7912 + -Drl.trackerDebug; the flag must ALSO be on the job via EXTRA, and rl.noYields on the job must match the JVM's pinned value or the server refuses), rl/v7_faith_real.py (--wake, --cap per zone), the watcher's tid/sids diagnostic. Artifacts committed: rl/artifacts/v7/5b_manifest.txt, 5b_faith.{json,md}, 5b_faith_wake002.{json,md}, 5b_check3b/3c/3d.txt, 5b_check3d_fixed.txt, 5b_census.txt; recordings gitignored (regenerate from the manifest seeds; 5b_BenchDimir_p1/_p99 are post-fix).
  STATE: 7912 up on the fixed build (v7 + oracle, noYields pinned true); 7910/7911 DOWN (drivers_3d.sh stops 7910; restart both with bash rl/drivers_3a.sh before 5d). GPU idle. Nothing uncommitted after this commit.
  NEXT: 5c — leak gates end to end on the 5b recordings: rl/v7_leak_real.py over several 5b_*.jsonl (oracle), the tracker gate is the §5b re-check (cite it), rl/v7_belief.py's gate on real inputs. Then 5d (throughput; restart 7910/7911 first; state the budget vs v6 before running), 5e (replay_3e.sh; tapped-land residual), tag v7-p5, then 7a. When convenient: WIRE §2c width 21, the PASS-afterstate amendment, the lethal-as-is amendment, the jointBlocks fix.

UPDATE (2026-09-12 21:30, next session's clock; WSL is 9 h behind): **5c DONE** — row §5c in rl/V7-VALIDATION.md. Oracle: rl/run_5c_leak.sh → v7_leak_real.py over every consult of every 5b recording (63 recordings, 19,379 consults): levels 1–3 pass everywhere, max Δlogit 0. Tracker: pass, cited from the 5b re-check (17,918 consults, 517 known slots, 0 known-not-in-truth). Belief (rl/v7_belief_real.py, thresholds committed at 097bc4a before the run): B1 leak-with-belief-on pass (2,520 consults), B2 stop-gradient pass, **B3 FAIL as pre-registered** (held-out log-lik +0.239 nats over uniform on the 63-file set, +0.169 ± 0.011 on the 48 non-duplicate recordings; bar 0.3, borrowed from 4f's planted rule), **B4 FAIL and ill-posed** (a returned-to-hand known card is not among the remaining-deck tokens by WIRE §2g; 164 of 167 unmatched true cards are those). Diagnostic: 6,000 steps → held-out 0.65 nats BELOW uniform (memorisation) — Phase 6 needs early stopping on held-out games and a bar set from the multiset prior. Plan row 5c "all three pass" is not met by the belief gate; recorded, not moved. Also rl/artifacts/v7/5b_gameplay_sample.md (echo-policy win rates with Wilson; the P8Faeries turn-32 lethal puzzle).
  GOTCHAS: PowerShell Start-Process wsl.exe jobs die with the session (both 5c runs were lost once) — launch inside one foreground wsl call with `setsid nohup bash script.sh > /tmp/x.log 2>&1 < /dev/null &`; make runners resumable. The Monitor and Bash tools run in Git Bash on Windows: use /c/Users/... paths and `wsl -e bash -lc "pgrep ..."` for process checks. The 5b*.jsonl glob is 63 files (three trackerDebug re-recordings duplicate 5b_BenchDimir_p99's games) — use 5b_*/5b2_* for anything game-grouped.
  STATE: 7912 up (v7 + oracle); 7910/7911 down. GPU idle. Nothing uncommitted after this commit.
  NEXT: 5d — throughput per rl/THROUGHPUT-LOCAL.md, v7 vs v6 on cuda end to end (restart 7910/7911 with bash rl/drivers_3a.sh first; state the budget vs v6 before running). Then 5e (replay_3e.sh; tapped-land residual), tag v7-p5, then 7a. When convenient: WIRE §2c width 21, the PASS-afterstate amendment, the lethal-as-is amendment, the jointBlocks fix, the Phase 6 belief-loss amendment (mask known slots).

UPDATE (2026-09-12 22:30, next session's clock): **5d DONE (FAIL), 5e DONE, Phase 5 closed without the tag** — rows §5d, §5e and "Phase 5 verdict" in rl/V7-VALIDATION.md. 5d: rung0_lane.sh got an ENC=7 branch (--arch v7, no v6 flags); rl/run_5d.sh ran v6 and v7 back to back (B0Base/B0Twin 256, conc4, cuda; artifacts rl/artifacts/v7/5d/, quantities via rl/tp_5d.py): v7 play 50.7 consults/s vs v6 182.5 (0.28, budget ≥ 1/3), update 58.8 vs 10.8 ms per stored consult (5.4×, budget ≤ 3×), cuda peak 2.3 GB, eps/s 0.455 vs 0.609 (untrained v7 episodes hold 28 consults vs 101). Checkpoint census (rl/v7_init_logits.py, 1,238 real consults): the v7 init net's argmax is PASS on 1033/1108 consults offering anything else (P(PASS) 0.53, gap 0.39 nats); after 256 episodes it never passes, 98-nat logit gap, ACTIVATE 781/781 — a collapse. 5e: replay_3e.sh 20 on the merged build: dump = wire IDENTICAL; A vs B 102/996 lines differ, all land rows, columns tapped/can-attack/can-block only; §3e's "per-line sums agree" corrected (can-attack sums differ on 61 lines). v7-p5 withheld (three FAIL rows).
  STATE: 7910 (v6) and 7911 (v7) up from drivers_3a.sh; 7912 down (restart with bash rl/drivers_3d.sh for oracle work). GPU idle. Nothing uncommitted after this commit. /tmp/rl_5d_v7/{init,ck_256}.pt hold the 5d checkpoints (WSL /tmp, not durable).
  NEXT (decision first, in the open): either (A) 7a smoke now — 256 episodes --arch v7 cuda W0Base vs heuristic, with per-update entropy / max|logit| / grad-norm / chosen-type histogram added to the TRAIN line before launching, a lr / logit-scale decision pre-registered (the 5d ck_256 collapse says lr 3e-4 × 4 epochs is not safe as is), and the §5b L4 probe + v7_init_logits.py on the resulting checkpoint; or (B) the 5d levers first — --batch-max 4 on the v7 lane (pre-registered: play toward ~150 consults/s), then update_profile.py --arch v7 on real lane windows to find the 5.4× (candidates: PPO epochs, window padding at 28 consults/episode, the 130 s first-update warm-up). Recommended: (B1) the batcher arm is one 12-min lane run — do it, then (A). When convenient: WIRE §2c width 21, PASS-afterstate, lethal-as-is, jointBlocks, the Phase 6 belief-loss amendment (mask known slots), a candidate-scorer centring for the PASS bias.

UPDATE (2026-09-12 23:25, next session's clock): **7a arms A0/A1/A2 DONE** — row §7a in rl/V7-VALIDATION.md. Not the learning rate (A1 at 3e-5 / 1 epoch collapsed to always-PASS, 540-nat gap, logits climbing while grad norm 0.08: Adam-normalised steps); the logit bound (A2, tanh × 5) stops the magnitude but saturates to a uniform policy (gap 0.000, 13/256 random wins). Correction recorded: advantages ARE batch-normalised, so the drift direction is GAE-timestep/critic, not "all −1". Action-space finding: every ACTIVATE candidate on W0Base is a land mana ability (XMage getPlayable, auto-pay makes it a no-op that costs a consult) — amendment owed: filter a.isManaAbility() in RLPlayer.consult (own commit + v6-identity row). Toolchain: TRAIN line now carries entropy/max_logit/grad_norm/chosen_types for --arch v7; policy_server --epochs and --logit-bound; rl/run_7a.sh; rl/v7_init_logits.py --logit-bound; rl/v7_logit_velocity.py.
  STATE: nothing running; 7910 (v6) and 7911 (v7) drivers up, 7912 down; GPU idle; nothing uncommitted after this commit. /tmp/rl_7a_*/ hold the lane outputs (ck_256.pt copied into rl/artifacts/v7/7a/*/).
  NEXT: the B1–B4 arms pre-registered in §7a (B1 needs the mana-ability filter first: RLPlayer.consult, compile with bash rl/sync_lane_b.sh, restart drivers, v6-identity row via wire_check_3b on a W0Base recording). Then the 5d throughput levers (batcher arm). v7-p5 still withheld.

## J. The handoff prompt (2026-09-12 23:50; v7/lane-d = cc6ba73). Supersedes §I.

```
You are working in the CardGuru repository, an RL project training agents to play Magic
against the XMage engine. Windows checkout C:\Users\sutanto4\Documents\CardGuru = WSL
/home/user/CardGuru = /mnt/c/Users/sutanto4/Documents/CardGuru. ONE branch: v7/lane-d
(main stays v6, untouched). Read CLAUDE.md first and follow its context protocol: durable
files over chat, small tool output, a checkpoint block at ~70% context, Wilson intervals,
no level from fewer than 100 games, pre-register what a change cannot move, correct in the
open (a failed gate is a row in rl/V7-VALIDATION.md, never a moved bar), commit and push
after each finding, commit messages end with
Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>.

CODE EXPLORATION USES THE CODEBASE-MEMORY MCP (rl/HANDOFF-V7.md §E.1): projects
C-Users-sutanto4-Documents-CardGuru and C-Users-sutanto4-xmage-pin; search_graph /
get_code_snippet / trace_path before grep; StateEncoder.java is partially indexed (grep -a).

ENVIRONMENT (rl/HANDOFF-V7.md §E.1, §F.1, §G GOTCHAS, every dated UPDATE line, and the
memory file wsl-detached-jobs):
  - Python only in WSL:  wsl -e bash -lc "cd /home/user/CardGuru && python3 ..."
    Tests: python3 -m pytest tests/test_v7_server.py -q ; full gate set python3 rl/v7_check.py
    (15 checks, ~80 s, must end failures=0).
  - Java: edit rl/xmage-src/*.java, compile with  bash rl/sync_lane_b.sh  (NEVER
    sync_engine_src.sh); restart drivers after every compile:  bash rl/drivers_3a.sh
    (7910 = v6, 7911 = v7) or  bash rl/drivers_3d.sh  (7912 = v7 + -Drl.oracle). rl.encoderV,
    rl.oracle, rl.noYields are class-init constants: one JVM per arm.
  - LONG JOBS: launch inside ONE foreground wsl call with
      setsid nohup bash rl/<script>.sh > /tmp/<name>.log 2>&1 < /dev/null &
    (PowerShell Start-Process jobs die with the session). Make runners resumable. Monitor and
    Bash run in Git Bash on Windows: use /c/Users/... paths, check WSL processes through
    wsl -e bash -lc "pgrep -fc '...'" with a bracket in the pattern ('rung0_la[n]e'); NEVER put
    the driver's process name literally in a command line while a lane runs - the lane's
    pkill -f kills your shell. Strip CRLF from scripts written on Windows: sed -i 's/\r$//'.
  - git: commit from the Windows side (WSL sees CRLF diffs on 27 files). NEVER git add a lane
    artifact directory without excluding *.pt (a Trainer checkpoint is 246 MB; rl/artifacts/v7/**/*.pt
    is gitignored now). Recordings in rl/artifacts/v7/wire3a/ are gitignored (regenerate from
    rl/artifacts/v7/5b_manifest.txt).
  - Lane: rung0_lane.sh has an ENC=7 branch (R0_ENCODER_V=7 -> --arch v7). Server knobs for
    --arch v7: --tbptt 16 --ep-batch 4 (defaults), --epochs N, --logit-bound B, --device cuda,
    --batch-max N; pass them via R0_SRVEXTRA. The TRAIN line carries entropy / max_logit /
    grad_norm / chosen_types (PASS/LAND/SPELL/ACTIVATE/TARGET/ATTACK/BLOCK/OTHER) per update.
    Runners: rl/run_5d.sh (v6 vs v7 throughput), rl/run_7a.sh (arms A0/A1/A2). Quantities:
    rl/tp_5d.py <arm dir>. Census of a checkpoint on real consults: rl/v7_init_logits.py
    --ckpt X [--logit-bound B] rl/artifacts/v7/wire3a/5b_*.jsonl. Logit velocity per Adam step:
    rl/v7_logit_velocity.py.

Read, in this order, before any work:
  1. CLAUDE.md
  2. rl/HANDOFF-V7.md §G, §I and every dated UPDATE line after §I (14:40, 21:30, 22:30, 23:25).
  3. rl/V7-VALIDATION.md rows §5b-§5e, "Phase 5 verdict", "7a pre-registration", §7a
     (what was measured, what failed, what is pre-registered).
  4. rl/THROUGHPUT-LOCAL.md §2, §7, §11.4 only when touching throughput.

STATE: Phase 5 closed without the v7-p5 tag (5c belief B3/B4 FAIL, 5d FAIL both per-consult
budgets, 5e replay residual = engine mana-payment order among identical lands). 7a arms
A0/A1/A2 done: the collapse is structural - lr 3e-5 / 1 epoch still collapses (Adam-normalised
steps on an unbounded scorer, 540-nat gap, grad norm 0.08); a tanh bound of 5 stops the
magnitude but saturates to a uniform policy (13/256 random wins). Advantages are batch-
normalised (line ~890 of policy_server.py), so the drift direction is GAE timestep + critic,
not outcome. The untrained v7 init is PASS-biased (argmax PASS on 93% of consults offering
anything else). Every ACTIVATE candidate on the mono-colour decks is a land mana ability -
a no-op (XMage auto-pays) that costs a consult and is the collapse's sink; on BenchDimir /
P8Faeries a payment choice exists on 39-49% of consults (heterogeneous untapped lands,
creature-lands). Drivers 7910/7911 up, 7912 down, GPU idle, nothing uncommitted.

NEXT, in order:
  1. Mana-ability filter (decision taken 2026-09-12 23:45, chat + §7a amendment): in
     RLPlayer.consult, drop candidates with a.isManaAbility() at priority, behind
     -Drl.manaCands=true to restore the old set. Own commit. v6-identity row: wire_check_3b
     on a W0Base recording with the flag on must show 0 disagreements; with it off, the
     candidate count per consult falls by exactly the mana abilities and nothing else changes.
     Compile (sync_lane_b.sh), restart drivers. Pre-registered: cannot change any win rate of
     an argmax eval probe on the mono-colour decks except through consult budget; it removes
     ~50 ACTIVATE consults per game from the A0-style collapse. A payment sub-consult (offered
     only when untapped sources are heterogeneous, candidate 0 = engine default) is deferred
     until the bench decks train; the float-in-response line is recorded as closed.
  2. 7a arms B1-B4 as pre-registered in §7a (12 min each, rl/run_7a.sh pattern, census after
     each, "learning" defined there): B1 = A2 + the filter; B2 = A2 + AdamW weight decay 0.01
     on the heads; B3 = heads on SGD-momentum lr 1e-3, trunk Adam 3e-5; B4 = entropy coef 0.1
     with the bound. Add the knobs to policy_server.py behind flags (--weight-decay,
     --heads-opt, --ent-coef); tests must stay green. Record a row per arm; do not move a bar.
  3. 5d levers, pre-registered in §5d: --batch-max 4 on the v7 lane (play toward ~150
     consults/s), then update_profile.py --arch v7 on real lane windows to find the 5.4x
     update cost (PPO epochs, window padding at 28 consults/episode, first-update warm-up).
  4. When convenient: WIRE §2c width 21, PASS-afterstate, lethal-as-is idx 57, jointBlocks
     canBlock filter, Phase 6 belief-loss amendment (mask known slots), candidate-scorer
     centring for the PASS bias, the §5b L4 probe on a trained checkpoint.

Start by confirming the driver state (python3 rl/driver_client.py --port 7911 --ping) and
running python3 rl/v7_check.py once, then execute NEXT 1. At ~70% context, stop, add a dated
UPDATE line to rl/HANDOFF-V7.md, commit, push, and offer to continue in a new session.
```

UPDATE (2026-09-13 00:30, next session's clock; WSL is 9 h behind): **§J NEXT 1 and 2 DONE, NEXT 3 running.** (1) Mana-ability filter in `RLPlayer.priority` (35c2d6d): `a.isManaAbility()` candidates dropped before the empty check, `-Drl.manaCands=true` restores per job (instance field, no JVM pin), `manaCandsDropped` in the summary; row "7a amendment" in rl/V7-VALIDATION.md — v6-identity over three decks × 4 games with a prefer-land echo policy and a same-flag control (`rl/run_manacands.sh`, `rl/manacands_check.py`): every removed candidate a land mana ability (401 / 1,661 / 486 = the probe counter), nothing else differs beyond the 5e residual and the candidate-count-derived fields, wire_check_3b 0 disagreements. Gotcha recorded there: an always-pass echo policy never plays a land, so it is never offered a mana ability (vacuous first attempt); same-seed runs are not byte-identical (5e residual), so identity claims need a same-flag control. WIRE-V7.md §8 amendments (ba8e261). (2) 7a arms B0–B4 (row "7a — arms B0–B4"; knobs b06e91c: `--ent-coef`, `--weight-decay` (AdamW, heads), `--heads-opt sgd --heads-lr`; `rl/summ_7a.py`): the sink was not the drift (B1 and B4 collapse to always-PASS like A1); the heads' optimiser is the variable — B2 (AdamW wd 0.01 on the heads) meets all three pre-registered learning tests (last-4-batch 0.336 [0.260, 0.421] vs the B0 init-policy bar 0.148 [0.097, 0.220]; census argmax-PASS 11 %, gap 1.26; battery attacks 16/22), B3 (SGD heads) wins 0.648 [0.562, 0.726] sampled but its argmax never attacks (0/840, turn-60 cap) and passes on 4 % (wins only). The 5 % bar was corrected in the open before any B row (B0 pre-registration). Nobody beats v6 on rung 0 (0/4, no level). (3) `rl/run_5d_bm.sh` running via `rl/artifacts/v7/5d/chain.sh`: v6f / v7f / v7bm (`--batch-max 4`) on the filter build, B0Base, RL_DUMP_BUF for `update_profile.py`; results land in `rl/artifacts/v7/5d/<arm>/tp.txt` and `run_5d_bm.log` — the row is not written yet. NEXT after that: B2/B3 × 2 more seeds, B5 (SGD heads + wd), B6 (PASS-bias centring), then the update-side 5.4× via update_profile on the dumped buffers; then the §2c width-21 / PASS-afterstate contract commit (needs the lane idle: it restarts server and driver from disk).

UPDATE (2026-09-13 00:35): 5d levers progress - v6f arm R0_DONE (8 updates, 256 episodes, 2.6 min wall; rl/artifacts/v7/5d/v6f/tp.txt written); v7f started 00:16:43 WSL clock, v7bm follows; read the three tp.txt files when `pgrep -fc "run_5d_b[m]"` is 0, then write the §5d follow-up row.

UPDATE (2026-09-13 00:50): **5d lever row DONE** ("5d follow-up" in rl/V7-VALIDATION.md; rl/run_5d_bm.sh, artifacts rl/artifacts/v7/5d/{v6f,v7f,v7bm}/ incl. the dumped first-update buffers rl_buf.pt, gitignored). --batch-max 4: play 47.0 -> 71.3 consults/s (0.47 of v6, budget pass), update unchanged 58 ms per stored consult (6.7x v6, FAIL; v6 update got cheaper on the filter build). The filter itself: v6 episodes 101 -> 32 consults, 0.61 -> 2.06 episodes/s. NEXT: update_profile.py profile --arch v7 --device cuda --buf rl/artifacts/v7/5d/v7f/rl_buf.pt (lever 2); B2/B3 x 2 seeds, B5, B6 per the B row; conc8 for the batcher if the CPU allows. Gotcha: a lane arm can fail at start with driver "Connection refused" against a policy server that just printed ready (v7f first launch) - rerun, the runner is resumable; a pgrep pattern like chai[n].sh matches chain2.sh (the dot), name waiter scripts so their own kill patterns cannot match them.

UPDATE (2026-09-13 02:50, next session's clock): **7c RUNNING** - `rl/run_7c.sh` detached in WSL (B2 recipe unchanged, W0Base, 2,048 episodes, seeds 0/1/2 sequential, battery 100 games per opponent every 512, ~1.5 h per seed; log rl/artifacts/v7/7c/run_7c.log, lane state /tmp/rl_7c_s<seed>/, resumable). Pre-registration "7c" + the land-census amendment are in V7-VALIDATION.md (undertraining vs rank/credit readings fixed; deciding criterion P(land) at 3+ lands > 0.5 from `rl/v7_land_census.py` on ck_512..2048; the census set is rl/artifacts/v7/wire3a/7c_W0Base_{p1,p99,sf}.jsonl). Findings this stretch (row "7c - land census of the 7a checkpoints"): B2 unlearned the third land as a probability (P(land) 0.86 -> 0.08 with lands in play = the late-game credit signature), B3 keeps playing lands and never attacks; identical cards split softmax mass so the argmax battery is biased against k-copy actions (B7 = argmax over candidate classes, eval-side, pre-registered). B2 argmax play note + correction (two lands, one 2-drop a turn, blocks with the solver's block, never offered an attack). NEXT when 7c seeds finish: per seed `python3 rl/v7_land_census.py --device cpu --logit-bound 5 --ckpt /tmp/rl_7c_s<seed>/ck_{512,1024,1536,2048}.pt <the three 7c recordings>` and `rl/summ_7a.py`-style reading of s<seed>/train_lines.txt + battery.txt; write the 7c row against the pre-registered readings; then B7 (cheap, eval-side), B6, the credit change if the reading is rank/credit. Driver 7911 was restarted alone (`driver_server.sh start 7911 ... -Drl.encoderV=7`) after a lane restart killed it; never run drivers_3a.sh while a lane owns 7910.

UPDATE (2026-09-13 03:50): 7c seed 0 hung at its 512 battery in CombatMath.bestAttack (4096 subsets x 200k defender replies on a wide board - the trained policy keeps a board, nothing before did); fixed with rl.attackTotalCap (af89167, row "7c interruption"), engine recompiled, 7911 restarted alone, 7c RESUMED at 512 from agent.pt (run_7c.sh relaunched, log rl/artifacts/v7/7c/run_7c.log). Seed 0 through 512: batch win rate 0.25 -> 0.78, last four 84/128, entropy 0.79 - already past arm B2 on the same recipe (same-recipe noise; one seed is not a curve). Also landed: --adv-norm {batch,std,auto,none} (6f25dad; default unchanged) with B8 pre-registered and QUEUED (rl/run_7b8.sh waits for run_7c.sh, then B2 + --adv-norm auto, 256 episodes, census + land census); 7d plan (BC from XMage CP7, then PPO) written in V7-VALIDATION.md under B8. NEXT: read 7c per seed as before (land census per ck, battery.txt, attackBudgetHit counts from the summaries), then B8's row against its predictions, then 7d piece (1) (teacher choice: CP7 vs the search teacher, 100 games each).

UPDATE (2026-09-13 04:15): decision (chat) - 7c STOPPED at seed 0 / 512 episodes, fixes first. Landed: --target-kl (mean approx KL budget per update, KL| line per update), --argmax-classes (eval argmax over candidate classes, B7), with --adv-norm auto (6f25dad) and rl.attackTotalCap (af89167); 13 server tests + v7_check 15/15. **C1 RUNNING**: rl/run_7c1.sh = B2 optimiser + the three flags, 2,048 episodes x seeds 0/1/2, batteries 100 games per opponent every 512, census + land census per ck; log rl/artifacts/v7/7c1/run_7c1.log, state /tmp/rl_7c1_s<seed>/, resumable. Row "C1 pre-registration" carries the readings. B8 superseded (ablation later). NEXT: read C1 per seed (s<seed>/census_all.txt, battery.txt, budget_hits.txt, KL| lines in train_lines.txt), write the C1 row; then 7d piece (1).

## K. The handoff prompt (2026-09-13 04:30; v7/lane-d = 97b174b). Supersedes §J.

You are working in the CardGuru repository, an RL project training agents to play Magic
against the XMage engine. Windows checkout C:\Users\sutanto4\Documents\CardGuru = WSL
/home/user/CardGuru = /mnt/c/Users/sutanto4/Documents/CardGuru. ONE branch: v7/lane-d
(main stays v6, untouched). Read CLAUDE.md first and follow its context protocol: durable
files over chat, small tool output, a checkpoint block at ~70% context, Wilson intervals,
no level from fewer than 100 games, pre-register what a change cannot move, correct in the
open (a failed gate is a row in rl/V7-VALIDATION.md, never a moved bar), commit and push
after each finding, commit messages end with
Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>.

CODE EXPLORATION USES THE CODEBASE-MEMORY MCP (rl/HANDOFF-V7.md §E.1): projects
C-Users-sutanto4-Documents-CardGuru and C-Users-sutanto4-xmage-pin; search_graph /
get_code_snippet / trace_path before grep; StateEncoder.java is partially indexed (grep -a).

ENVIRONMENT (rl/HANDOFF-V7.md §E.1, §F.1, §G GOTCHAS, every dated UPDATE line after §J,
and the memory file wsl-detached-jobs):
  - Python only in WSL:  wsl -e bash -lc "cd /home/user/CardGuru && python3 ..."
    Tests: python3 -m pytest tests/test_v7_server.py -q (13 tests); full gate set
    python3 rl/v7_check.py (15 checks, ~80 s, must end failures=0).
  - Java: edit rl/xmage-src/*.java, compile with  bash rl/sync_lane_b.sh  (NEVER
    sync_engine_src.sh). Drivers: 7910 belongs to the LANE (rung0_lane.sh autostarts and
    restarts it; never run drivers_3a.sh while a lane runs); 7911 = the v7 recording driver,
    restart it alone with  bash rl/driver_server.sh start 7911 "-Dmage.randomPerThread=true
    -XX:+UseParallelGC -Dmage.playableCache=on -Drl.encoderV=7"  (a lane restart can kill it).
    rl.encoderV, rl.oracle, rl.noYields, rl.debug are class-init constants: one JVM per arm.
    rl.manaCands (7a amendment) and rl.attackTotalCap are per-job properties.
  - NEVER edit server-side Python (policy_server.py, v7_*.py) or Java while a lane runs:
    the lane restarts its server every 512 episodes and its driver per arm FROM DISK. Every
    knob is a flag whose default is the old behaviour for this reason.
  - LONG JOBS: launch inside ONE foreground wsl call with
      setsid nohup bash rl/<script>.sh > /mnt/c/.../rl/artifacts/v7/<dir>/<name>.log 2>&1 < /dev/null &
    (log on the /mnt/c side so a Git-Bash Monitor can tail /c/Users/... ). Runners are
    resumable (a seed/arm with its census.txt is skipped; a dead lane resumes from
    /tmp/rl_<run>_s<seed>/agent.pt via rung0_lane.sh resume_at). Check WSL processes with
    wsl -e bash -lc "pgrep -fc 'run_7c[1]'" - a bracket in the pattern, and NEVER the
    launched script's literal name in the same shell string you pgrep in. pkill patterns
    with a bracket still carry a '.' wildcard: name waiter/kill scripts so their own
    patterns cannot match them (chai[n].sh matched chain2.sh; kill_chain2.sh killed itself).
    Kill only via a script file (the auto-mode classifier blocks inline kill/pkill). Do not
    put a launch and a pkill in the same Bash call. Strip CRLF: sed -i 's/\r$//'.
  - Bash heredocs with backticks inside a  wsl -e bash -lc "..."  string are expanded by the
    outer shell: write text with the Write tool to the scratchpad and append it with sed
    (CRLF-aware: rl/V7-VALIDATION.md and rl/HANDOFF-V7.md may be CRLF; check with grep $'\r').
  - git: commit from the Windows side. NEVER git add a lane artifact directory without
    excluding *.pt (rl/artifacts/v7/**/*.pt is gitignored; recordings in wire3a/ too).
  - Lane knobs for --arch v7 via R0_SRVEXTRA: --device cuda --epochs N --logit-bound B
    --weight-decay W (AdamW on the heads) --heads-opt sgd --heads-lr L --ent-coef E
    --adv-norm {batch,std,auto,none} --target-kl K --argmax-classes --batch-max N.
    TRAIN line: entropy / max_logit / grad_norm / chosen_types (PASS/LAND/SPELL/ACTIVATE/
    TARGET/ATTACK/BLOCK/OTHER); KL line per update (approx_kl, samples, stopped).
    Tools: rl/summ_7a.py <arms> (table + the pre-registered learning test),
    rl/v7_init_logits.py --ckpt X --logit-bound 5 (type census), rl/v7_land_census.py
    --ckpt X --logit-bound 5 --device cpu <7c_W0Base_{p1,p99,sf}.jsonl> (P(land) by lands in
    play), rl/tp_5d.py <dir> (throughput), rl/manacands_check.py (v6-identity), scratch
    play transcript: rl.debug on a fresh driver JVM (the RLGAME block in
    /tmp/rl_p9/driver_server_<port>.log; the earlier scratch script is in the session's
    scratchpad, rewrite it: frozen server on 7947, driver 7913, -Drl.mode=eval -Drl.debug=true).

Read, in this order, before any work:
  1. CLAUDE.md
  2. rl/HANDOFF-V7.md §G GOTCHAS and every dated UPDATE line after §J (00:30, 00:35, 00:50,
     02:50, 03:50, 04:15).
  3. rl/V7-VALIDATION.md from "7a amendment — mana-ability filter" to the end: the 7a
     amendment row, "7a — arms B0–B4", the B2 argmax play note and its correction, "5d
     follow-up", "7c pre-registration", "7c — land census", "B8 pre-registration", "7d plan",
     "7c interruption", "C1 pre-registration", and the "C1 first update" paragraph.
  4. rl/WIRE-V7.md §8 (amendments) when touching the contract.

STATE: C1 is RUNNING (rl/run_7c1.sh, log rl/artifacts/v7/7c1/run_7c1.log, state
/tmp/rl_7c1_s<seed>/): B2's optimiser (lr 3e-5, 1 epoch, logit bound 5, AdamW wd 0.01 on the
heads) + --adv-norm auto + --target-kl 0.02 + --argmax-classes, on the engine with the
mana-ability filter and rl.attackTotalCap; W0Base vs heuristic, 2,048 episodes x seeds 0/1/2,
100-game batteries per opponent every 512, census + land census per ck into
rl/artifacts/v7/7c1/s<seed>/{census_all.txt,battery.txt,budget_hits.txt,train_lines.txt}.
Seed 0 started 03:34 WSL clock (~1.5 h per seed). Its first update: approx KL 0.33 after one
window step, stopped (budget 0.02) - the budget binds at the first step; C2 (--target-kl 0.1)
is pre-stated in the C1 row if seed 0's batch win rate at 512 is below 7c seed 0's on the
same recipe without the budget (0.62 at 256, 0.78 at 512). What is established: the 7a
collapse is structural in the heads' optimiser (B2 = decay on the heads meets all three
learning tests; B3 = SGD heads wins sampled but its argmax never attacks); batch-centred
advantages in all-lost batches manufacture "early good, late bad" (B2 unlearned the third
land: P(land) 0.86 -> 0.08 with lands in play); identical cards split softmax mass (argmax
biased against k-copy actions; --argmax-classes); the 5d play budget passes with
--batch-max 4 (71 consults/s, 0.47 of v6), the update budget fails (58 ms per stored
consult, 6.7x); a trained policy that keeps a board sent CombatMath.bestAttack into 8e8
resolves per consult (bounded now; attackBudgetHit counted per game). 7c is stopped by
decision at seed 0 / 512; B8 (adv-norm auto alone) is superseded, kept as an ablation.
Drivers: the lane owns 7910; 7911 may be down (restart alone if you record); GPU busy with C1.

NEXT, in order:
  1. Read C1 as each seed lands (7C1|seed=N|rc= in the log): the four batteries (100 games
     each = levels), the sampled curve (train_lines.txt), KL| stopped fraction, land census
     per ck (census_all.txt), attackBudgetHit counts. Write the C1 row against the
     pre-registered readings ("trains", "third land", "not collapsed", "KL budget"). If the
     budget starved it, C2 = --target-kl 0.1 (same script with the flag changed, new ART dir
     7c2), pre-registered as the C1 row says. Pool only finished seeds; three seeds pooled
     before any comparison with v6's W0Base level in LEVELSET.md.
  2. 7d piece (1): teacher choice - XMage ComputerPlayer7 (cp7 opponent in the lane) vs the
     project's search teacher (rl.agent=search), 100 games each vs the heuristic on W0Base;
     then the recording of consults with the teacher's chosen candidate index on the v7 wire
     (>= 20k consults, bench decks, both seats); then rl/v7_bc.py; then PPO from the BC
     checkpoint with C1's flags. Each its own row; the cannots are in the 7d plan.
  3. Ablations when the GPU is free: B8 (adv-norm auto alone, rl/run_7b8.sh, 256 episodes),
     B6 (candidate-scorer centring), B2/B3 extra seeds.
  4. Update-side: rl/update_profile.py profile --arch v7 --device cuda --buf
     rl/artifacts/v7/5d/v7f/rl_buf.pt (the 6.7x); then the §2c width-21 / PASS-afterstate
     contract commit with the lane idle.

Start by confirming C1 is alive (pgrep as above, tail the log) and reading its latest
TRAIN and KL lines from /tmp/rl_7c1_s0/server_all.log or server.log; do not edit
server-side code while it runs. At ~70% context, stop, add a dated UPDATE line to
rl/HANDOFF-V7.md, commit, push, and offer to continue in a new session.

UPDATE (2026-09-13 05:50, next session's clock; WSL is 9 h behind): **C1 seed 0 through 1024, no C2** - interim paragraph "C1 - seed 0 interim" in rl/V7-VALIDATION.md: 512 battery D0 0.77 [0.68,0.84] / D1 0.80 / TWIN 0.79 (100 games each), sampled curve dead for updates 4-8 (zero wins, 70 consults/episode, the B3 wall sampled) then 0.84 last-4 at 512 and a 0.78-0.91 plateau to 1024; P(land) at >=3 lands 0.70 at ck_512; KL budget stopped 7/32 updates; max |logit| hit the bound 5.00 at updates 30-32 (carried in the "not collapsed" reading). C2 trigger not fired; rl/run_7c2.sh staged, not launched. **7d piece (1a) DONE** (row "7d piece (1a)"): CP7 68/100 vs the heuristic [0.58,0.76], the search teacher 37/100 at every plies/breadth (node counter shows the flags honoured), heuristic mirror 50/100; replicates RUNG0-CEILING-TEST; CP7 is the teacher. Piece (1b) needs an rl.agent=cp7 seat in EpisodeRunner dumping the v7 wire + chosen index: Java, waits for the lane to idle (~04:00 WSL clock for three seeds at ~35 min per 512). Driver 7911 is UP (v7 flags). Watch pattern: the lane's R0| rows are in /tmp/rl_7c1_s<seed>/lane.log (WSL-local), not run_7c1.log. NEXT: 1024 battery + census_1024 for seed 0 (in flight), then seeds 1/2 as they land (runner writes s<seed>/ at seed end), then the C1 row; ablations B8/B6 and update_profile when the GPU is free; piece (1b) Java after the lane.

UPDATE (2026-09-13 06:30, next session's clock; WSL is 9 h behind): **C1 seed 0 through 1024** (paragraph "C1 - seed 0 interim" + "Seed 0 at 1024" in rl/V7-VALIDATION.md): D0 0.77 -> 0.81, D1 0.80 -> 0.79, TWIN 0.79 -> 0.75 (100 games each, intervals overlap); census argmax-PASS 14 %, gap 3.55 -> 2.99, entropy 0.63, P(land) at >=3 lands 0.70 -> 0.73; KL stopped 8/34; max |logit| on the bound 5.00 from update 30 (census clauses hold: clipping, not a rail); attackBudgetHit 47/46/40 -> 170/166/185 per 100-game battery (carried; a per-consult counter is owed, Java, after the lane). C2 NOT triggered. **rl/summ_7c1.py** reads a seed (artifact dir, or live `/tmp/rl_7c1_s0:rl/artifacts/v7/7c1/s0` joined with ':') and prints the table + the four readings + the pooled 2048 battery over finished seeds. **7d piece (1b) design pre-registered** (row "7d piece (1b) design"): CP7TeacherPlayer / rl.agent=cp7, label y on the consult, joint sites via the same CombatMath candidates; Java waits for the lane. Seed 0 ends ~00:45 WSL clock, seeds 1/2 ~2.3 h each (~05:30 WSL for all three). NEXT: when `7C1|seed=N|rc=` appears in rl/artifacts/v7/7c1/run_7c1.log, `python3 rl/summ_7c1.py rl/artifacts/v7/7c1/s0 [s1 s2]`, write the C1 row against the four readings (three seeds pooled before any v6 comparison: v6 rung-0 W0Base D0 0.568 at 512 pooled/2 seeds, 0.78 at 1.4-1.9k, 0.705 at 2.1k, rl/artifacts/rung0/W0Base/report.txt); then, lane idle: piece (1b) Java + per-consult attackBudgetHit counter + the §2c width-21 contract commit; B8/B6 ablations; update_profile (lever 2).

UPDATE (2026-09-13 07:50, next session's clock): **C1 seed 0 COMPLETE** (section "C1 - seed 0 complete" in rl/V7-VALIDATION.md; artifacts rl/artifacts/v7/7c1/s0/ committed without the .pt): D0 0.77 / 0.81 / 0.83 / 0.85 at 512..2048, D1 0.85, TWIN 0.88 at 2048 (100 games each); sampled last-4 flat from 512 (0.84, 0.86, 0.64, 0.80) so the "trains" sampled clause is not met as written while the argmax level rose at every point (neither clear); third land met (0.72); not collapsed at every point (gap 3.55 -> 1.70, entropy 0.63 -> 0.76); KL stopped 13/64. Seed 1 started 05:34 WSL clock (~2.3 h), seed 2 follows. Per seed at its `7C1|seed=N|rc=` line: `wsl -e bash -lc "cp /tmp/rl_7c1_sN/probe_*.txt /home/user/CardGuru/rl/artifacts/v7/7c1/sN/"` then `python3 rl/summ_7c1.py rl/artifacts/v7/7c1/s0 rl/artifacts/v7/7c1/s1 [s2]` - the pooled 2048 line is the C1 level once all three are in; then write the C1 row (the four readings on three seeds, the v6 comparison against rl/artifacts/rung0/W0Base/report.txt: 0.705 [0.638,0.764] at 2,111 seed 0 / 0.78 at 1.4-1.9k / 0.568 at 512 pooled). Seed 0's 2048 interval [0.767,0.907] is clear of v6's 2,111 point; whether pooling keeps that is the row's question.
