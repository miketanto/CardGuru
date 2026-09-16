# HANDOFF — where CardGuru stands, 2026-09-16 (paste the block below into a fresh session)

---

You are continuing a Magic: The Gathering RL research project. Repo: C:\Users\sutanto4\Documents\CardGuru
(= /home/user/CardGuru inside WSL; Python, the XMage engine and the GPU live only in WSL). Branch `v7/lane-d`,
HEAD 797f527. Box: 11 GB WSL RAM, one RTX 3060.

READ FIRST: `LEVELSET.md`, then in `rl/V7-VALIDATION.md` the sections `15 / A0` … `15 / A4L`, `15 / C`, `15 / D`,
and the `13c` and `14` rows. Runbooks: `rl/PHASE15-ARCH.md`, `rl/PHASE14-DIAG.md`, `rl/PHASE13-BC.md`,
`rl/CURRICULUM-LADDER.md`. Ground rules are in `CLAUDE.md` (pre-register; Wilson intervals; never report a level
from < 100 games; correct in the open; keep tool output small).

## Where the research is

* **RL against the engine's strong player does not climb.** Phase 13c (PPO from a CP7 clone) failed its
  pre-registered make-or-break at 2,048 episodes and drifted below its own start. Phase 14 found why, as far as
  it goes: from what the agent sees, game outcomes are barely predictable (held-out EV 0.095 for a 6.9 M-parameter
  critic against 0.196 for ten hand-picked scalars), and the training win rate is the same (~0.27) against CP7
  skill 1 and skill 6, so opponent strength is not the block. A league is premature.
* **The network itself is sound.** It fits (memorises to 0.998 of its metric ceiling), its card path gets
  gradients, and imitation accuracy is still rising at full data (data-limited), while outcome prediction is flat.
* **Card identity contributes little on our decks.** A clone given RANDOM card vectors loses 0.028 priority top-1
  and nothing on blocks. The wire already carries power/toughness/cost/type/keywords, so identity adds little.
* **A real bug was found and fixed in principle:** the heads' logit bound (B = 5) freezes training once raw logits
  run past it (frozen clones sit at |raw| 54–110, gradient ~1e-9; healthy ones at 17–21). Relaxing it is worth
  +0.09–0.14 held-out top-1 and does not inflate healthy runs. **Measured, it does NOT affect `bc.pt` (7.57) or
  the 13c-twin trajectory (7.57 → 8.09)**, so it does not explain 13c.
* **The blocker for the combat curriculum:** `CombatMath` candidate coverage is **0.56–0.65 on the white ladder
  decks** (BenchDimir 0.948/0.974) and collapses to ~0.50 in a strong mirror. About 40 % of the declarations a
  strong player actually makes are not options our policy can pick. Combat labels therefore fail their gate, the
  A4L keyword rungs could not test their own aspects, and any combat-aspect result on these decks measures the hole.

## Owed, in the order I would take them

1. **Instrument which declarations CombatMath misses** (partial attacks? multi-blocks? trades down?), then extend
   the generator and re-measure coverage per deck. Everything combat-shaped waits on this.
2. **Re-run the A4L ladder with combat labels** once coverage passes its gate; rungs 1d–5 and the black branch are
   unrun, and the first series is void (logit-bound freeze), the second series answered only priority/target.
3. **Decide the logit bound's default** with one controlled re-clone on BenchDimir, and say whether every earlier
   clone should be re-read.
4. **Re-read Phases 8/10/13c against per-deck coverage** before trusting their combat conclusions.
5. Parked: 17Lands replay imitation (`rl/L17-CLOUD.md`, fidelity NO-GO, median 2 turns rebuilt).

## Operating rules that cost time when ignored

Kill only via a script file whose name cannot match its own pgrep patterns; never put a launch and a pkill in one
call; launch long jobs with `cmd //c start //min wsl -e bash -lc "..."` and verify with pgrep in a LATER call;
wait loops must key on FILES (an argv that contains another job's pgrep pattern jams it); at most two policy
servers + two driver JVMs + one GPU trainer, and wait if MemAvailable < 1.5 GB; never `git add` *.pt or *.jsonl;
end commit messages with: Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
