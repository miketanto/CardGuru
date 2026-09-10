# CardGuru — standing instructions

An RL project training agents to play Magic against the XMage engine.
Work happens in `rl/`. Runs are long (hours), so a session's context
will fill before the work is done. Both sections below exist because of
that.

## Context management — the protocol

**Assume this session will end before the work does.** Context is the
scarce resource, not time. Treat durable files as memory and the
conversation as a cache that will be dropped.

### Write state down as you go, never only in chat

- A finding is not recorded until it is in a file under `rl/`. Numbers
  quoted only in conversation are lost at the first compaction.
- Commit and push after each finding, not at the end. Small commits
  with real messages are the memory.
- Long-running work writes to a log the next session can read
  (`/tmp/...` is container-local and dies with it — anything that
  matters gets copied into `rl/artifacts/`).

### Keep output small on purpose

Most context in this project is burned by tool output, not by prose.

- Never `cat` a probe file, a driver log, or a `.java` file. Grep for
  the counters you need: `grep -o 'win_rate=[0-9.]*\|under_over=[^ ]*'`.
- Read files with `offset`/`limit` when you know the region. The
  engine sources (`RLPlayer.java`, `StateEncoder.java`,
  `EpisodeRunner.java`) are large enough that a full read is a
  meaningful fraction of a window.
- Summarise a battery row into a table in your reply; do not paste
  three of them raw.
- Prefer one command that prints a computed answer over three that
  print data you then reason over.

### Report when context is filling

**At roughly 70% context used, stop and checkpoint** — do not wait
until it is critical, and do not start a new expensive investigation.
Say plainly that context is filling, then produce a **handoff block**:

```
## Context checkpoint

STATE:      what is running right now, where its output lands, how to check it
DONE:       findings so far, each with the file they are recorded in
OPEN:       what is unfinished, in priority order
NEXT:       the single next action, concrete enough to execute cold
GOTCHAS:    anything learned this session that is not yet in a doc
COMMITS:    what is pushed, what is still uncommitted
```

Then commit everything, push, and offer to continue in a new session.
If the user wants to keep going in this one, keep going — but the
checkpoint exists on disk from then on and gets updated, not rewritten
from memory.

### Low-context mode

When context is tight and the user wants to continue anyway:

- Do the work, report the result, skip the narration.
- Do not re-derive or re-verify what a doc already records — read the
  doc.
- Do not re-read files already summarised in the conversation.
- Keep replies to the finding and its caveat.

## Ground rules for results

These are the project's standing rules; `rl/HANDOFF-ATTACK-JOINT.md`
§6 is the source and later handoffs extend it.

- **Wilson intervals, not Wald.** Wald reports 0.000 half-width at p=0
  and p=1, which made every untrained row in old lane logs claim
  certainty about 0/100.
- **Never report a level from fewer than 100 games.** A learning curve
  built from 10-game probes was published and retracted in
  `rl/DIMIR-V6-2K-RESULT.md` §0. A rate is not a result until its
  interval is narrower than the effect claimed.
- **Pre-register what a change cannot do.** State in advance which
  metrics are incapable of moving. An improvement on one of them is a
  bug to find, not a result to write up.
- **A regression is not "flat".** Say which it is.
- **State what a number cannot support.** Confounds go in the doc, not
  only in chat.
- **Pool only finished seeds.**
- **A behaviour counter beats a win rate.** The load-bearing findings
  in this project came from per-decision censuses, not win rates.
- **Correct in the open.** When a published claim turns out wrong, mark
  it as a correction in the file rather than silently editing it.

## Operational gotchas

- `rl.encoderV`, `rl.legacyTieBreak`, `rl.debug`, `rl.cardFeatures` are
  **class-init constants** — a driver JVM that served one arm cannot
  serve another. Kill `[R]LDriverServer` between arms.
- **Do not put a launch command and a `pkill` in the same Bash call.**
  `pkill -f` matches the wrapper shell's own argv and kills your shell.
  Write the script with the Write tool, launch it in a separate call.
- **Never edit `rung0_lane.sh` while a lane is running.** Bash reads a
  script incrementally as it executes.
- The container recycles on **session** inactivity, not process
  activity. Long runs need a heartbeat — `rl/dimir2k_alive.sh` works.
  `Monitor` clamps to a 30-minute timeout regardless of `persistent`.
- The `RLGAME` transcript lands in `/tmp/rl_p9/driver_server_<port>.log`,
  not the client log.
- The policy server grows ~5 MB/episode (allocator fragmentation). It
  survives only because the lane restarts it every 512 episodes.

## Where to start

`LEVELSET.md` (repo root) is the synthesis of everything through
Phase 12; read it first. `rl/HANDOFF-CREDIT.md` is the current handoff
(it supersedes `HANDOFF-STACK-TIMING.md`, whose three questions it
answers). Then `rl/THROUGHPUT-LOCAL.md` for how fast the local machine
runs and why `--device cuda` is the default now, and
`rl/SETUP-WSL-LOCAL.md` for the environment. The lane scripts still
resolve `/home/user/CardGuru` and `/home/user/mage`; on this machine
those are symlinks inside WSL.
