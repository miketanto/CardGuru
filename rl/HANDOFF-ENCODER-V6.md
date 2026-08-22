# Handoff — the attack fix landed, and the encoder is the next thing

Read `rl/ATTACK-JOINT-RESULT.md` then `rl/ENCODING-DESIGN.md`, then this.
The build plan you are executing is `rl/ENCODER-V6-BUILD.md`.

> **Superseded for new work.** v6 landed, gated, and was trained to 2048
> episodes on a constructed deck; the board encoding is no longer the
> binding constraint. See `rl/DIMIR-V6-2K-RESULT.md` for that run and
> `rl/HANDOFF-STACK-TIMING.md` for the current handoff. This file
> remains the reference for the v6 build itself, and its §5 gotchas and
> §6 ground rules still govern.

---

## 0. State of the world

Branches `claude/cardguru-joint-attacks-7l0182` and
`claude/cardguru-p10-flagship-48r5lg` are identical and both pushed.
Never push to phase-5.

Encoder arms, `-Drl.encoderV`, read at class-init so all arms run from
one build:

| v | what |
|---|---|
| v1–v3 | see `ENCODER-AB-RESULT.md` |
| v4 | joint BLOCK assignment, outcome-featurized |
| **v5** | **v4 + joint ATTACK subsets, valued under a best-replying defender** |
| v6 | `ENCODER-V6-BUILD.md`. Net + server wire built (§1b); the Java emission side is not |

Committed checkpoints, all 32/94:

| file | what |
|---|---|
| `artifacts/rung0/W0Base/v4_ck512.pt` | pre-fix baseline, D0 .940 |
| `artifacts/rung0/W0Base/v5_ck1024.pt` | v5 fine-tuned 512→1024 |
| `artifacts/rung0/W0Base/v4ctl_ck1024.pt` | the matched v4 control |

## 1. What this session settled

Do not re-derive these; they are measured and written up.

- **Attacking is now one joint decision** over subsets, minimax one ply
  (`jointAttacks`, `CombatMath.bestAttack`). Policy search costs 0.09%
  of wall clock — the pre-registered 15% fallback did not fire.
- **`auditAttacks` exists** and is the instrument that did not before.
  Eval-only: it is **76% of wall clock**.
- **Trained A/B, budget- and seed-matched:** attack rate z=+18.7,
  attack-optimality z=−0.4, block-optimality z=−3.8, win rate identical
  at .810 both arms. The .940→.810 drop was the extra 512 episodes, not
  v5 — the control is what proved that.
- **v5 fixes lethal recognition and the control does not.** v5 declines
  nothing at LETHAL; both fail COMMIT.
- **`resolve()` had a tie-break bug** the search was exploiting. Fixed;
  `-Drl.legacyTieBreak=true` restores it and reproduces the committed
  lane row exactly.
- **The state encoding is provably irrelevant to the current metric**
  (§6c). This is the finding that reorders everything below.

## 1b. Stream B has landed — the server side of the wire is ready

`claude/v6-network`, commit `e2ae6fd`. Steps 3 and 4 of the build plan's
§7 are done on the **Python side only**: `EntityAttnPolicy`
(`--arch entattn`), the v6 consult and hello, arm `--r0`, and 23 checks
in `rl/entattn_check.py` that run with no engine and no Java
(`python3 rl/entattn_check.py`, ~4 s). Nothing Java was touched;
`rung0_lane.sh` and friends are untouched too, because the §4e lane
switch belongs with the wire-up commit. Merge B before writing that
commit.

**What the server now accepts**, i.e. what `SocketPolicyClient` has to
emit:

```
hello   {"t":"hello","mode":..,"episodes":..,"sdim":..,"cdim":94,
         "gdim":16,"edim":48,"emax":24,"rtypes":6}
consult {"t":"consult","g":[16],"e":[[48],...],"r":[[s,d,t],...],
         "c":[[94],...],"phi":f}     ->  {"a":<idx>}
```

Four details §4b left to the implementation, now fixed by the server —
`ENCODER-V6-NETWORK.md` §2 is the full list:

1. An edge `[s,d,t]` biases the attention of **query `s` toward key
   `d`**. The reverse edge is a separate type on purpose.
2. `t` indexes `RTYPES` in the §2 order (`blocks, blocked_by,
   attacking_player, targets, controls, attached_to`). **The index is
   the contract**; append only.
3. Edges index the **emitted** entities, not the padded buffer. An edge
   into a padding slot is rejected per consult — that is the
   order/edge-list drift a handshake cannot catch.
4. `sdim` is not enforced for `entattn` (nothing reads it); `cdim` is.

**Mismatches die at the handshake, loudly and on both sides**: a v1–v5
driver against a v6 server, a v6 driver against a flat one, gdim / edim
/ rtypes / cdim drift, or an `emax` above the server's buffer. The
server prints the reason and also sends it as `{"ok":0,"err":...}`
before the connection dies, so it lands in the driver's log too. Note
that `SocketPolicyClient` currently discards the hello reply — reading
it is worth the three lines.

Bring the server up and point a driver at it:

```bash
python3 rl/policy_server.py --port 7960 --arch entattn --cdim 94 \
    --ckpt /tmp/rl_v6/agent.pt --max-k 64        # add --r0 for arm R0
```

`--gdim/--edim/--emax` override 16/48/24. `emax` is a buffer like
`MAX_K`: if emission exceeds 24 entities the handshake says so and names
the flag, and raising it changes no weights.

**What B did NOT establish**, because it cannot: any audit number, any
win rate, and the §5b gate itself. B's collision check runs on synthetic
rows built to §1's layout and shows only that *given* correct rows the
pooling separates the six 3/7/7 boards (closest pair 0.0049 at token
scale 6.67, untrained init). The gate is still yours, against real
emission.

## 2. The task

`ENCODER-V6-BUILD.md` §7, in order. Steps 1–2 first: emit entity tokens
and relations, then run the invariance and collision tests. **Stop if the
collision test fails** — nothing downstream is worth building on an
encoder that still collides.

**The one thing that must not be forgotten:** §0 of the build plan.
Attack- and block-optimality **cannot** improve from a state change,
because the reference's answer is a linear function of three candidate
features and recovers from candidates alone in 400/400 positions with
the state discarded. If a v6 arm posts better audit numbers, that is
noise or a bug, not a result. The gate is the collision probe.

Ship arm **R0** (relations zeroed) at the same time or v6 repeats v5's
confound of moving two things at once.

## 3. Environment, because the container will be recycled

`/home/user/mage` does not survive. Rebuild (~15 min):

```bash
git clone https://github.com/magefree/mage.git /home/user/mage
cd /home/user/mage && git checkout 7554968c
git apply /home/user/CardGuru/rl/engine-patches/phase9-engine.patch
mkdir -p Mage.Tests/src/test/java/org/mage/test/benchmark/rl
cp /home/user/CardGuru/benchmark/xmage/src/*.java Mage.Tests/src/test/java/org/mage/test/benchmark/
cp /home/user/CardGuru/rl/xmage-src/*.java        Mage.Tests/src/test/java/org/mage/test/benchmark/rl/
cp /home/user/CardGuru/rl/*.dck /home/user/CardGuru/benchmark/xmage/*.dck \
   /home/user/CardGuru/rl/m3_decks/*.dck Mage.Tests/
mvn -q -pl Mage.Tests -am install -DskipTests -Dfile.encoding=UTF-8
pip install torch
```

**Do not apply `phase12-mana-recopy.patch`** — its hunks land fuzzy and
duplicate the phase9 playable-memo block. What is needed from it is
already in `phase9-engine.patch`.

After editing `rl/xmage-src/` only: `mvn -q -pl Mage.Tests test-compile`.

## 4. Running things

```bash
# attack + block audit off any checkpoint (sequential, ~13 min / 100 games)
bash rl/attack_audit.sh <ckpt> <encV> W0Base heuristic 100 901024 <out.txt>
ATTACK_AUDIT=false ...                      # measures the POLICY's search alone
AUDIT_EXTRA=-Drl.legacyTieBreak=true ...    # pre-fix damage tie-break

# constructed positions
python3 rl/position_probe.py --coverage           # no server needed
python3 rl/position_probe.py --port <p> --v4|--v5

# annotated replay: [atkjoint] candidates + [atkaudit] verdict per combat
bash rl/rung0_replay.sh <ckpt> <encV> W0Base heuristic 6001 <out.txt>

# search self-test
java -cp "$(cat /tmp/rl_p9/cp.txt):Mage.Tests/target/test-classes" \
     org.mage.test.benchmark.rl.CombatMathCheck 5000

# a matched fine-tune pair (what produced the v5 A/B)
mkdir -p /tmp/rl_ft_v5_s0 && cp <init.pt> /tmp/rl_ft_v5_s0/agent.pt
R0_ENCODER_V=5 R0_OUT=/tmp/rl_ft_v5_s0 R0_EVERY=512 R0_CP7_G=0 R0_PORT=7950 \
    bash rl/rung0_lane.sh W0Base W0Twin 1024 0
```

## 5. Gotchas this session paid for

- **`rl.encoderV` AND `rl.legacyTieBreak` are class-init constants.** A
  driver JVM that served one arm cannot serve another. Every script
  kills `[R]LDriverServer` first; that is not optional.
- **`pkill -f` bracketing is not always enough.** Bracketing protects
  against the pattern text matching itself, but if the *real* launch
  command is in the same shell's command line, `pkill` kills the shell.
  Put the launch in a separate script file. This cost a silent failure.
- **The attack audit is eval-only** in the lane. Putting it in shared
  flags quadruples every training chunk.
- **Egress blocks most academic domains** — arxiv, annals-csis,
  huggingface, ronaldo.games. **GitHub and raw.githubusercontent work**,
  so read encodings from implementation source; it is authoritative for
  that question anyway.
- **Chromium is at `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`**
  and renders HTML to PNG headlessly — useful for checking a diagram
  actually draws before claiming it does.
- The `RLGAME` transcript lands in
  `/tmp/rl_p9/driver_server_<port>.log`, not the client log.

## 6. Ground rules

`HANDOFF-ATTACK-JOINT.md` §6 still governs — Wilson not Wald, pool only
finished seeds, a regression is not "flat", state what a number cannot
support, confounds in the doc not just in chat. This session added one:

- **Pre-register what the change cannot do.** §0 of the build plan is
  the model: it says in advance which metric is incapable of moving, so
  a later improvement on it is read as a bug rather than a win.

## 7. Files

| file | why |
|---|---|
| `rl/ATTACK-JOINT-RESULT.md` | the attack work end to end; §6b the trained A/B, §6c the encoding proof |
| `rl/ENCODING-DESIGN.md` | LOCM/Hearthstone encodings, the E2 finding, the ByteRL adaptation |
| `rl/ENCODER-V6-BUILD.md` | **the plan you are executing** |
| `rl/ENCODER-V6-NETWORK.md` | stream B's result: the wire as implemented (§2 is the contract), the decisions, what the checks cannot show |
| `rl/entattn_check.py` | 23 checks over the v6 net and wire; no engine, no Java, ~4 s |
| `rl/artifacts/encoding-*.html` | the diagrams, renderable with the chromium note above |
| `rl/xmage-src/RLPlayer.java` | `jointAttacks`, `auditAttacks`, `jointBlocks`, `auditBlocks` |
| `rl/xmage-src/CombatMath.java` | `bestAttack`, `bestDeduped`, the tie-break fix |
| `rl/xmage-src/CombatMathCheck.java` | the search self-test |
| `rl/attack_audit.sh` / `attack_audit_report.py` | the instrument and its Wilson report |
| `rl/HANDOFF-BLACK-BRANCH.md` | the other branch, still unclaimed |
