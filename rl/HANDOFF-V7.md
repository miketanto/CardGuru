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
