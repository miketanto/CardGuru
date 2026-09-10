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
