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
Outputs: `/tmp/rl_deckvalue/<pair>_<order>.txt` (RL|summary lines) and
a table on stdout; copy the table into §6 of this file and the summaries
into `rl/artifacts/deckvalue/` when run.

## 6. Result

*Not yet run.*
