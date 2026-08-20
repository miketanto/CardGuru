# Four parallel streams, and the prompts to start them

Written to run four sessions at once without them stepping on each other.
Read `rl/HANDOFF-ENCODER-V6.md` for the state of the world; this file is
only about how the work splits.

---

## Why this needs planning at all

**Engine sessions cannot share a machine.** Every lane script runs
`pkill -f "[R]LDriverServer"`, and `rl.encoderV` / `rl.legacyTieBreak`
are read at class-init, so a JVM that served one arm cannot serve
another. Two engine sessions in one container will kill each other's
JVMs mid-run and record nothing. Separate sessions get separate
containers, so this is fine **provided each rebuilds its own
`/home/user/mage`** (~15 min, §3 of the handoff).

**They must not share a branch**, and they should not share files.

## The split

| stream | owns | needs engine? | blocks / blocked by |
|---|---|---|---|
| **A · entity emission** | `StateEncoder.java`, new `EntityView.java` | yes | blocks C6-wire; nothing blocks it |
| **B · the network** | `policy_server.py` | **no** | merges with A at wire-up |
| **C · second seed** | docs + artifacts only | yes | independent |
| **D · k-turn reference** | `CombatMath.java`, new doc | yes (validation) | independent; unblocks *everything* being measurable |

Branches, pre-created off `0d2eef6` (the commit that added this file):

```
claude/v6-entity-emission     (A)
claude/v6-network             (B)
claude/v5-seed2               (C)
claude/kturn-reference        (D)
```

**File conflicts to avoid.** A does *not* touch `policy_server.py`; B
does *not* touch Java. The wire contract they share is already written
down in `ENCODER-V6-BUILD.md` §4b/§4c — treat it as the interface spec
and change it only by agreement. D owns `CombatMath.java` outright: a
later rung-1 keyword extension touches the same file, so it must wait
for D to land rather than run beside it.

**Merge order:** C and D are additive and can land any time. B lands
next (Python only). A lands last of the four, because the wire-up commit
touches both sides and wants B already in.

---

## Prompt · Stream A — entity emission and the collision gate

```
Repo: miketanto/CardGuru, branch claude/v6-entity-emission
(develop and push there; never push to phase-5).

Read rl/HANDOFF-ENCODER-V6.md, then rl/ENCODER-V6-BUILD.md end to end
before coding. Rebuild the engine first — §3 of the handoff, ~15 min,
and note the phase12 patch trap.

YOUR TASK is steps 1 and 2 of the build plan, and only those.

1. In rl/xmage-src/StateEncoder.java, behind an ENCODER_V >= 6 gate,
   emit: the 48-dim entity token exactly as specified in §1 of the build
   plan, the ~16-dim globals vector, and the typed relation edge list
   from §2. Build the entity index map and the relations in ONE pass so
   the edge indices cannot drift from the token order. Pull the fourteen
   combat keyword bits by indexing the existing e2_features table — do
   not re-derive them; there must be one definition of "deathtouch" in
   this codebase.

2. Then write the two gate tests as runnable committed files, in the
   style of CombatMathCheck.java:
   - INVARIANCE: shuffle a board's emission order, the sum-pooled
     embedding must be identical to float tolerance.
   - COLLISION: the six W0Base boards named in ATTACK-JOINT-RESULT.md
     §6c — all count 3 / power 7 / toughness 7 — must produce SIX
     DISTINCT embeddings. Today they produce one.

STOP AT THE COLLISION TEST. If it fails, nothing downstream is worth
building; report why rather than pressing on.

DO NOT touch rl/policy_server.py — stream B owns it. The wire format in
§4b/§4c is a contract; if you need it changed, say so rather than
changing it unilaterally.

Ground rules are §6 of rl/HANDOFF-ATTACK-JOINT.md plus §6 of the new
handoff. The one that bites here: §0 of the build plan says attack- and
block-optimality CANNOT improve from a state change. Do not report them
as evidence for this work.
```

## Prompt · Stream B — the network, no engine required

```
Repo: miketanto/CardGuru, branch claude/v6-network
(develop and push there; never push to phase-5).

Read rl/HANDOFF-ENCODER-V6.md and rl/ENCODER-V6-BUILD.md §3 and §4c.

YOU DO NOT NEED THE XMAGE ENGINE. This stream is pure PyTorch and runs
against synthetic tensors, so skip the 15-minute rebuild entirely —
`pip install torch` is all you need.

YOUR TASK: build EntityAttnPolicy in rl/policy_server.py, selected by
--arch entattn, to the shapes in §3:

  ent_in    Linear(EDIM=48 -> d)
  rel_emb   Embedding(len(RTYPES)+1, heads)  scattered into a
            (B, heads, EMAX, EMAX) additive attention bias, reshaped to
            (B*heads, E, E) for TransformerEncoder's mask argument
  ent_enc   TransformerEncoder(d, heads=4, layers=2)
  pool      MASKED SUM over entity tokens -> Linear(d -> d)
  state_tok = glob_in(globals) + pool(entities)

From state_tok onward the existing AttnPolicy path is UNCHANGED — LSTM
cell, cat with candidate tokens, encoder, scorer, value head. Do not
alter the candidate path; it is already correct and is not what is
missing.

SUM, NOT MEAN. Mean-pooling one 2/2 and three 2/2s gives the identical
vector — that is the exact bug this whole effort exists to fix, rebuilt
with extra steps. Write a unit test that asserts sum-pooling
distinguishes those two boards.

Also: the --edim/--emax/--gdim args, the existing k > MAX_K guard
extended to entities, dims recorded in the checkpoint so a mismatched
load fails loudly at handshake rather than silently mispredicting, and
an all-zero relation edge list must degrade EXACTLY to plain
self-attention (that is arm R0, and it must be verified by test, not by
argument).

DO NOT touch any Java. Stream A owns the emission side. §4b/§4c is the
contract between you.
```

## Prompt · Stream C — does the v5 result hold on a second seed

```
Repo: miketanto/CardGuru, branch claude/v5-seed2
(develop and push there; never push to phase-5).

Read rl/ATTACK-JOINT-RESULT.md §6b, then rl/HANDOFF-ENCODER-V6.md §3-4.
Rebuild the engine (~15 min, mind the phase12 patch trap).

YOUR TASK: repeat the v5-vs-v4-control A/B on SEED 1 and report whether
it replicates. No code changes — this is a measurement.

Both arms fine-tune from the committed rl/artifacts/rung0/W0Base/
v4_ck512.pt for 512 episodes (512 -> 1024), matched budget, matched eval
seed, CP7 skipped symmetrically:

  mkdir -p /tmp/rl_ft_v5_s1 && cp <v4_ck512.pt> /tmp/rl_ft_v5_s1/agent.pt
  R0_ENCODER_V=5 R0_OUT=/tmp/rl_ft_v5_s1 R0_EVERY=512 R0_CP7_G=0 \
      R0_PORT=7950 bash rl/rung0_lane.sh W0Base W0Twin 1024 1
  ...and the same with R0_ENCODER_V=4 into /tmp/rl_ft_v4_s1, port 7951.

Run them SEQUENTIALLY — the lane kills the driver JVM, so two at once
destroy each other.

Then rl/attack_audit.sh on both final checkpoints and write the result
into a new section of ATTACK-JOINT-RESULT.md.

WHAT SEED 0 FOUND, which you are testing: attack rate z=+18.7,
attack-optimality z=-0.4, block-optimality z=-3.8, win rate identical at
.810 in both arms, and v5 taking the LETHAL constructed position where
the control declines it.

Ground rules: Wilson never Wald, pool only finished seeds, and a
regression is not "flat". If seed 1 disagrees with seed 0, THAT IS THE
RESULT — this project has withdrawn five claims for want of saying so.
Do not average them into a story.
```

## Prompt · Stream D — the k-turn reference

```
Repo: miketanto/CardGuru, branch claude/kturn-reference
(develop and push there; never push to phase-5).

Read rl/ATTACK-JOINT-RESULT.md §3, §5 and §7, then
rl/HANDOFF-ENCODER-V6.md. Rebuild the engine (~15 min, phase12 trap).

WHY THIS IS THE MOST VALUABLE STREAM. Every combat number this project
reports comes from a reference that is ONE COMBAT DEEP. §7 shows its two
biases run in opposite directions — it over-credits attacking by pricing
the tapped-out cost at zero, and under-credits it by pricing material at
3 against damage at 2 — so the net cannot be signed. §6c shows the
current reference's answer is a linear function of three candidate
features, which means NO ENCODING WORK CAN BE MEASURED until a deeper
reference exists. You are unblocking everyone else.

YOUR TASK: extend rl/xmage-src/CombatMath.java with a k-turn rollout
reference, and validate it.

Design decisions to make deliberately and write down, not assume:
  - what the opponent is assumed to do on their turn (the same minimax
    one-ply reply? a fixed heuristic? the current policy?);
  - whether creatures deployed from hand are modelled at all, given the
    state carries only hand SIZE;
  - k, and the cost per combat, MEASURED not assumed — the one-combat
    audit already costs 76% of wall clock, so budget this honestly and
    pre-register a fallback if it dominates.

Validate it the way bestDeduped was: a committed runnable self-test, and
agreement with the one-combat reference where k=1.

YOU OWN CombatMath.java. Nobody else may touch it while this is open — a
rung-1 keyword extension wants the same file and must wait for you.

Ground rules: §6 of rl/HANDOFF-ATTACK-JOINT.md. Name it "best by this
evaluator at depth k", never "optimal play".
```

---

## What is deliberately NOT parallelised

- **Rung-1 keyword support in `CombatMath`** — same file as stream D.
  Queue it behind D.
- **Option C, the card-graph encoder** — gated on deck diversity per the
  E3 precedent (`ENCODING-DESIGN.md` §4d, `POOLED-ANALYSIS.md` §5), and
  a vanilla creature's ability graph is empty, so rung 0 cannot test it.
- **The probe port and the behavioural pair** (`ENCODER-V6-BUILD.md`
  §4d, §5c) — they depend on A's emission format existing. Queue behind
  A rather than guessing at the format.
