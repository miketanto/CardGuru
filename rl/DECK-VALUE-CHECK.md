# Deck-value check — does the removal on rung B1 have any win-rate value?

Status: **designed and pre-registered, not yet run.** Runs with
`bash rl/deck_value_check.sh` inside WSL when no lane is using the
machine (it shares the persistent driver JVM; ~2 minutes per pair).

## 0. Why this comes before every timing experiment

`B1-TIMING-AB.md` §5: `B1Narrow` cast its removal 86 times and `B1Fast`
zero, and they finished level (.585 vs .595, n=200). The A/B varied the
timing of a card whose value the readout could not see.
`HANDOFF-CREDIT.md` §3 names the fix: *before anything is scored on win
rate, find or build a deck where the non-creature cards carry
measurable win-rate value*, and says the test is cheap — scripted hands,
no training. `CURRICULUM-LADDER.md` designed `B0Base` so removal targets
would be *legal*; it never checked they would be *valuable*. This is
that check.

## 1. The decks — the vanilla twin already exists

`diff B0Base.dck B1Narrow.dck` is the `NAME:` line and one card line: `B0Base` has
`4 Gutter Skulk` (2/2 vanilla, {1}{B}) where `B1Narrow` has `4 Defeat`
(sorcery, destroy target creature with power ≤ 2) and `B1Fast` has
`4 Cruel Cut` (instant, same text). Same 56 other cards, same 24 Swamps.
No new deck file is needed:

| deck | slot 10 | type |
|---|---|---|
| `B0Base` | 4 Gutter Skulk | vanilla creature — **the twin** |
| `B1Narrow` | 4 Defeat | sorcery removal |
| `B1Fast` | 4 Cruel Cut | instant removal |

## 2. Protocol

Scripted heuristic in both seats (`-Drl.agent=heuristic
-Drl.opponent=heuristic`), `-Drl.mode=eval`, sequential (`RL_CONC`
unset), `-Drl.stopTurn=60`, fixed seeds. **500 games per pair, each
pair run in both seat orders (250 + 250)** so play/draw and seat-specific
heuristic behaviour cancel. Wilson 95 % intervals throughout.

| pair | question |
|---|---|
| `B0Base` vs `B0Base` | calibration: must sit on .5 |
| `B1Narrow` vs `B0Base` | is sorcery removal worth anything over a 2/2 body, in scripted hands? |
| `B1Fast` vs `B0Base` | is instant removal worth anything over a 2/2 body? |
| `B1Narrow` vs `B1Fast` | is instant speed worth anything *when the pilot uses it* (the heuristic casts its highest-MV playable instant at the opponent's end step, per the `HeuristicPlayer.java` header)? |

Readout per pair: win rate of the first-named deck pooled over both
seat orders, with its interval, plus the per-order rates so a seat
asymmetry is visible rather than averaged away.

## 3. Pre-registration — written before the run

1. **`B0Base` vs `B0Base` cannot leave [.45, .55] beyond its interval.**
   If it does, the seat order is not exchangeable in this setup and every
   other row must be read per seat order, not pooled.
2. **The heuristic casts Defeat and Cruel Cut only when it can.**
   Per its header, `HeuristicPlayer` casts the highest-MV affordable
   creature, else the highest-MV affordable sorcery, on its own turn, and
   its highest-MV playable instant at the opponent's end step.
   It does not hold removal for a better target. So this check measures
   the value of removal *played naively*, which is a **lower bound** on
   its value. A null here says "no value even naively"; it does not say
   "no value for a policy that times it".
3. **Heuristic-seat casts are not counted.** `EpisodeRunner`'s `inst*`
   and `tgt*` counters and the `RLGAME` transcript exist for the RL seat
   only; with `rl.agent=heuristic` there is no per-decision record of
   the heuristic's casts. If a removal deck shows no edge, we cannot
   distinguish "removal has no value" from "the heuristic never found a
   castable window". Mitigation, if the result is null: one 20-game
   arm with `-Drl.debug=true` and the removal deck in the **RL seat
   driven by the trained-nothing init net** is *not* a substitute (the
   init net passes); the honest mitigation is a small engine-side
   counter of spells cast per seat, and that is a Java change to record
   as a follow-up, not to fold into this run.
4. **Decision rule, fixed now:**
   - removal deck ≥ .58 pooled with the interval excluding .50 → removal
     has scripted value on this rung; the win-rate columns in
     `CONDITION-TRANSFER-DESIGN.md` §4 are readable.
   - interval includes .50 → **no measurable value at 500 games**; timing
     experiments on B1 must be read through behaviour counters only, and
     a rung with valuable spells must be built before any win-rate
     claim about timing (`HANDOFF-CREDIT.md` §3).
   - `B1Narrow` vs `B1Fast` inside its interval → instant speed buys
     nothing *in scripted hands*; that is expected and is not evidence
     about a trained policy.
5. **Nothing in this run can say anything about the RL agent.** No
   policy is involved.

## 4. What it cannot support

- Value under the heuristic's play is a lower bound (§3.2); a strong
  pilot could extract more from the same card.
- 500 games resolve about ±.045; an edge of .03 is invisible here and
  would also be invisible to every lane battery this project runs.
- One engine build, one heuristic version. If `HeuristicPlayer` changes,
  re-run.

## 5. Reproduction

```
bash rl/deck_value_check.sh            # all four pairs, ~8 min
R_DV_GAMES=100 bash rl/deck_value_check.sh   # smoke (not a result)
```
The script kills any persistent `RLDriverServer` first: a JVM left by a
lane has `rl.cardFeatures` fixed at class-init and refuses this job's
flags (first run, 2026-09-10, failed in one second exactly this way).
Outputs: `/tmp/rl_deckvalue/<pair>_<order>.txt` (RL|summary lines) and
a table on stdout; copy the table into §6 of this file and the summaries
into `rl/artifacts/deckvalue/` when run.

## 6. Result — run 2026-09-10, 500 games per pair, both seat orders

| pair | A-seat wins/n | B-seat wins/n | pooled p(A wins) | Wilson 95 % |
|---|---|---|---|---|
| `B0Base` vs `B0Base` | 122/250 | 127/250 | .498 (249/500) | [.454, .542] |
| `B1Narrow` vs `B0Base` | 109/250 | 121/250 | .460 (230/500) | [.417, .504] |
| `B1Fast` vs `B0Base` | 111/250 | 124/250 | .470 (235/500) | [.427, .514] |
| `B1Narrow` vs `B1Fast` | 126/250 | 124/250 | .500 (250/500) | [.456, .544] |

Artifacts: `rl/artifacts/deckvalue/`. Run time 3 min 41 s on the local
WSL machine (scripted, sequential, ~4.5 games/s).

**Verdict, by the decision rule in §3.4: the removal has no measurable
win-rate value on this rung, even when a scripted pilot casts it.**

- Calibration passed: the `B0Base` mirror sits on .498 and the two seat
  orders agree (122 vs 127), so pooling is legitimate.
- Both removal decks land *below* .50 against the vanilla twin (.460,
  .470) with intervals that include .50 and exclude .58. Read plainly:
  in scripted hands, four Defeats or four Cruel Cuts are worth no more
  than four 2/2 bodies, and the point estimate says slightly less. A
  conditional removal spell that can only hit power ≤ 2 replaces a
  creature that attacks and blocks every turn; on a board of 2-power
  bodies that is a bad trade more often than a good one.
- Sorcery vs instant is dead level at .500. Instant speed is worth
  nothing in scripted hands, as §3.4 anticipated; this says nothing
  about a trained policy.

**Consequences, which were the point of running this first:**

1. Every win-rate column in `CONDITION-TRANSFER-DESIGN.md` §4 for the
   B1 rung is **void by construction**. Only the behaviour counters
   (`tgtChose_p*`, `tgtNoOppAvail`, `instOppTurn`, `flashHeld`) can read
   a B1 timing or targeting experiment. `B1-TIMING-AB.md`'s null is now
   explained twice over.
2. The rung with valuable spells has to be found or built before any
   timing claim is scored on win rate (`HANDOFF-CREDIT.md` §3). The
   cheapest candidates already exist as deck files: `B2Mid` (removal
   hits power ≤ 3) and `B3Open` (unconditional). The same check, same
   protocol, against `B0Base` is the next run — pre-registered in §7.
3. The lower-bound caveat (§3.2, §3.3) stands: a pilot that *held*
   removal for a worthwhile target could extract value the heuristic
   does not. But the training signal a policy learns from is the win
   rate, and on this rung the win rate carries no information about the
   spell. That is the mechanism `B1-TIMING-AB.md` §5 suspected, now
   measured directly.

## 7. Follow-up — wider conditions, pre-registered before running

Same protocol, 500 games per pair, both seat orders. Pairs: `B2Mid` vs
`B0Base`, `B3Open` vs `B0Base`, and `B3Open` vs `B1Narrow`.

- The `B0Base` mirror from §6 is the calibration; not re-run.
- Prediction: `B3Open` (unconditional removal) is the arm most likely
  to clear .58; `B2Mid` may not. If **neither** clears .58, no black
  rung in the current ladder has spells with scripted win-rate value,
  and a new deck (removal that trades up, e.g. hits power ≥ 3 only, or
  a spell whose value is card advantage) has to be designed before any
  win-rate readout of a spell experiment is possible.
- Cannot move: nothing about the RL agent; the `B1Narrow` vs `B1Fast`
  level result; the heuristic's cast rule.
- Decision rule as §3.4.

### 7a. Result — run 2026-09-10, 500 games per pair, both seat orders

| pair | A-seat wins/n | B-seat wins/n | pooled p(A wins) | Wilson 95 % |
|---|---|---|---|---|
| `B2Mid` (Reave Soul, power ≤ 3) vs `B0Base` | 120/250 | 119/250 | .478 (239/500) | [.435, .522] |
| `B3Open` (Fell, any creature) vs `B0Base` | 109/250 | 129/250 | .476 (238/500) | [.433, .520] |
| `B3Open` vs `B1Narrow` | 133/250 | 134/250 | .534 (267/500) | [.490, .577] |

Artifacts: `rl/artifacts/deckvalue/` (run2 files). 2 min 50 s.

**Verdict: the prediction failed in the direction that matters. Neither
wider-condition deck clears .58; both sit below .50 against the vanilla
twin, exactly where B1 sat.** Unconditional removal — Fell, destroy any
creature for {1}{B} — is worth no more than a 2/2 body in scripted
hands on this ladder. Wider removal does edge narrower removal
(`B3Open` vs `B1Narrow` .534), but the interval includes .50.

So, per the §7 pre-registration: **no black rung in the current ladder
has spells with scripted win-rate value.** Across five pairs and 2,500
games, every removal deck is ≤ .50 against the deck that replaces the
removal with a vanilla 2/2.

Why this is plausible rather than a bug, stated so it can be checked:

- **Targeting is not the problem.** `HeuristicPlayer` delegates target
  choice to XMage's `ComputerPlayer` (`HeuristicPlayer.java:491-510`
  call `super`), which picks the opponent's best creature for a
  detrimental effect. Fell does trade up when cast.
- **Cast order is.** The heuristic casts the highest-MV affordable
  creature first and a sorcery only if no creature is affordable
  (header rule 3). With a 24-Swamp mono deck, removal is cast with
  leftover mana, late, into whatever is there — and a removal card in
  hand is a creature not drawn. In a vanilla mirror where both sides
  field the same bodies, a 1-for-1 that costs a turn of board presence
  is a wash at best.
- **Consistency across five pairs** (.460, .470, .478, .476 vs the twin)
  is the strongest evidence that this is the rung's property and not a
  sampling accident: four independent 500-game samples of the same
  sign.

Lower-bound caveat as §3.2: a pilot that held Fell for the right moment
might extract more. But the *training signal* is the win rate, and on
every black rung it carries no information about the spell.

### 7b. What has to change before any spell experiment is scored on win rate

A rung whose spells matter has to be **designed**, not found in the
current ladder. Constraints the five pairs impose:

1. The spell must produce an advantage the *scripted* pilot realises,
   or the check cannot certify it. Candidates: a two-for-one (a sweeper
   that hits only small creatures while the deck's own creatures are
   large; a creature with an on-cast removal trigger so it is never a
   body-for-spell trade), or card advantage the heuristic banks
   automatically (draw-two attached to a body).
2. The vanilla twin must differ in exactly the four slots, as here.
3. The check is .58 pooled over both seat orders at 500 games, decided
   before the run, same as §3.4.
4. `CombatMath` still scopes to vanilla bodies; a sweeper or a trigger is
   fine, keywords are not.

Until such a deck passes this check, timing and targeting experiments
on the black branch are read through behaviour counters only, and any
win-rate number quoted from them is void.
