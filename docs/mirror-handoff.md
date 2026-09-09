# Handoff — Dimir mirror benchmark

Branch: `build/stackwise-campaign`. Everything below is committed and pushed.

## What we are trying to prove

That our LLM pilot is a **better Magic player than XMage's built-in AI
(MAD, ComputerPlayer7 at skill 6)** in a *Dimir midrange mirror* — same 60
cards on both sides, so any deviation from a 50% win rate is piloting skill
and not deck strength. Earlier cross-deck matchups (mono-red vs stompy,
etc.) are abandoned: they confounded pilot skill with deck strength and
could not answer this question. See `docs/dimir-mirror-plan.md`.

Working mode is deliberately **1–2 games at a time, reviewed by a human**
before running more. Do not launch big batches until the qualitative bar is
met.

## How to run a game

```bash
# one game, pilot on the play, fixed deal
python3 benchmark/run_mirror.py --mage-repo ~/Documents/mage --games 1 \
    --seed 4242 --same-seed --start A

# a paired pair: same deal played from both sides (best variance control)
python3 benchmark/run_mirror.py --mage-repo ~/Documents/mage --games 2 \
    --seed 4242 --paired
```

Each game writes to `research/data/mirror/`: `gN.jsonl` (every decision),
`gN_daemon.jsonl` (pilot latency/errors), `gN.html` (auto-playing replay),
`gN_review.md` (decision digest), and appends to `mirror.jsonl`.

Prerequisites: an XMage checkout (the driver auto-copies into
`Mage.Tests/` at launch) and a working `claude login` — the pilot runs
through `claude -p --resume`, no API key, zero spend.

## The review loop (this is the point)

1. Run 1–2 games.
2. Read `gN_review.md` — it keeps only decisions where the pilot had a real
   choice (~30 of ~180 requests), each with both boards, the hand, the menu,
   the choice, and the pilot's stated reasoning. Search decisions render as
   candidate lines with the pilot's own 0–100 leaf scores.
3. Have a subagent rate them questionable/minor/moderate/major and say what
   it should have done instead.
4. Fix what the review finds — usually the **briefing**
   (`benchmark/pilot_dimir_mirror.md`), sometimes the harness.
5. Repeat. Only scale up when the pilot stops making category errors.

## Standing state

Mirror record: **0W–1L, plus one game killed by the watchdog.** Both games
predate the fixes below, so neither is a fair sample. Effectively we have
**no valid mirror data yet.**

- g1: loss, turn 11, 1 life vs 16. Review found three of our own briefing
  errors (below) plus a rules error by the pilot.
- g2: killed at the 50-minute watchdog cap while winning 23–17 on turn 11.
  MAD was stuck on two lands all game — which is what exposed the mulligan
  bug.

## Harness bugs fixed (all were inflating our results)

1. **The opponent never mulliganed** (`38606c9`) — the big one.
   `ComputerPlayer.chooseMulligan` short-circuits to "keep" when
   `isTestMode()`, which `CardTestPlayerAPIImpl` sets on every player. MAD
   kept every opening seven, including one-landers, in *every game this
   harness has ever run*, while our pilot mulliganed normally. **All
   previously reported win rates are inflated and should not be cited.**
   Fixed by seating the opponent as `MulliganingTestPlayer`, which
   re-applies the engine's own rule without the test bypass.
2. **Seeding did not pin the deal** (`38606c9`). `Deck.getMaindeckCards()`
   collects the deck's ordered `LinkedHashSet` through `Collectors.toSet()`,
   so the library was built from a `HashSet` ordered by random card UUIDs.
   The driver now sorts both libraries by card name before `setSeed`.
   Verified: two runs at seed 999 deal identical hands.
3. **Priority search double-asked** (`f8eb813`). A "hold" verdict fell
   through to a normal escalation, asking the pilot the same question twice
   — 15% of all pilot calls. Now a three-way verdict, plus a memo so an
   unchanged position is not re-searched (the counterspell question was
   re-asked 16 times in 6 turns).
4. **MAD's search was wall-clock bounded** (`27307ae`), so the opponent got
   weaker whenever the machine was busy. Now node-bounded (5000-node cap);
   `-Dcardguru.opp.think_secs=18` restores stock behaviour.

## Briefing errors fixed (found by reviewing g1)

Our own briefing was giving the pilot false card text — worse than none.
Verify card text against `~/Documents/mage/Mage.Sets/src/` before writing it.

- **Anoint with Affliction** exiles only mana value **3 or less** — it can
  never touch Sheoldred or Kaito (both MV 4). We had described it as
  unconditional removal, and the pilot held it eleven turns for targets it
  was rules-incapable of hitting.
- **Cut Down** kills total power+toughness 5 or less. **Go for the Throat**
  is the only unconditional answer in the deck.
- **Kaito** is a `{2}{U}{B}` **planeswalker**, not a creature; a 3/4
  hexproof Ninja only on his controller's turn.
- **Sheoldred's drain is not delayed by summoning sickness** — the pilot
  built a race plan on the belief that it was.

## Known open issues

- **50-minute watchdog is too tight** for control mirrors; g2 died at the
  cap while winning. Raise `--game-timeout` (it is real-time, sleep-proof).
- **Games are slow** (~20–50 min). Dominated by pilot latency (~10s/decision
  × 150–250 decisions). The `f8eb813` fix should cut roughly a third; not
  yet measured on a full game.
- **Targets are not searched.** Target sub-choices inside rollouts fall to
  the built-in AI via the `searching` guard. This is the obvious next
  increment of "search every relevant decision" — but let the reviews say
  whether it is what is costing games.
- **No MAD-vs-MAD reference arm.** Worth running to confirm the mirror's
  null really is 50% and to measure the play/draw advantage.
- **Statistical power**: ~40 games detects a true 70% win rate at p<0.05,
  ~74 detects 65%, ~158 detects 60%. Do not run these until the pilot stops
  making category errors — and re-baseline, since the mulligan fix makes the
  opponent meaningfully stronger.

## Architecture, briefly

`run_mirror.py` → `pilot_daemon.py` (persistent `claude -p` session, one per
game) + `llm_bridge.py` (spool bridge, yields, auto-pass) → the XMage driver
`driver/CardGuruScenarioRunner.java` (interactive game, LLM-leaf search at
attacks/blocks/main-phase). Decisions escalate as JSON over a file spool.
`replay_export.py` and `review_game.py` turn a game log into a replay page
and a review digest. `analyze_campaign.py` reports matrices and failure
classes for batch runs.
