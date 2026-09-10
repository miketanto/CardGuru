# What we learned: LLM pilots for Magic (Dimir mirror vs MAD)

Branch `build/stackwise-campaign`, 2026-09-09/10. Companion docs:
`docs/stack-search-plan.md` (search design and status),
`docs/overnight-suite-plan.md` and `docs/overnight-suite-results.md` (the
four-model suite and the A/B arms). This is the cross-cutting summary.

## 1. The pilot's mistakes are mostly *reading* mistakes, not strategy

Across every model, the losses and the near-losses trace to a card or a
rule read wrong, not to a wrong plan:

- **Deep-Cavern Bat's exile clause** (the card comes back when the Bat
  leaves) was missed by Haiku twice, by Sonnet twice on one seed
  (ninjutsu-bouncing the Bat, then chump-blocking with it), and handled
  correctly only by Opus 5, which turned the same clause into a win by
  declining the bounce.
- **Deathtouch on the blocker**: Sonnet and Haiku each attacked their best
  creature into an untapped deathtouch Preacher; Opus 5 explicitly did not.
- **Cut Down's "total power and toughness 5 or less"**: Haiku and Opus 4.7
  both believed it "cannot kill my main threats" and lost Bats to it.
- **Restless Reef**: animate-then-cannot-attack (enters tapped, summoning
  sick) cost Haiku and Opus 4.7 several turns each while ahead.
- **Legend rule**, **Kaito being a creature only on your turn**, **Go for
  the Throat cannot target Kaito**, **"Sheoldred's draw fires on cast"**:
  all seen at least once.

What fixed part of this: sending the full card text of every visible card
on every request (`card_reference`), emitting supertypes in the type
line, and a briefing that makes "read the card before deciding" step one.
What did not fix it: a hand-written matchup guide (most of it was wrong,
and we cut it). The residual errors are the pilot not applying text it
was given, which is a model property; the harness cannot read for it.

## 2. A standing plan changes behaviour, but only when it is required

Offered as optional, the `plan` field was used zero times in 199
requests. Made required on the decisions that shape a game (mulligan,
priority, attackers, blockers, target, leaf_eval), it was used every time
and the digests show it being followed: Sonnet "hold exactly 4 for
Curiosity" for six straight turns and then executing it; Opus 5 writing
"animate Reef and attack with Kaito" two turns before doing it for exact
lethal. Free text the model may ignore is indistinguishable from no
feature.

## 3. Search: what helped, what was inert, what cost

- **Per-window search with LLM-scored leaves** (arm d) works as a decision
  mechanism but is expensive: every priority window is a fresh question.
- **Projecting the opponent's turn** (arm e: reseat their hand, let them
  play land plus best spell, give me an instant-speed response window) is
  what made the pilot hold mana: tap-outs 17→6, hold-decisions 16%→44% on
  the same seed, for about +20% cost. This is the single search feature
  that changed play.
- **Opponent responses to my spell** (arm f) is correct and inert against
  MAD, which taps out every turn; its first real test is LLM vs LLM.
- **Determinization** (reseating the opponent's hand from their library in
  every copy) closed a real leak: the original copies carried their real
  hand and library order.
- **Closing speed** is the shared weakness of every pilot: four of the six
  suite wins took five or more turns from a dominant board. Lethal-finding
  wants an explicit terminal check in the search, not more thinking.

## 4. Where the time goes, and the DP work

- Time is pilot latency, not compute. CPU sat near idle all night.
- A decision's cost is **thinking output** (1.3k–12k tokens on hard
  windows) plus **context growth** (a per-game session reaches 400–800k
  tokens by the late turns). Haiku is the slowest pilot because it writes
  the most per decision.
- 30–53% of leaves a pilot scored were states it had scored earlier the
  same turn; 20–33% were duplicates inside one request; re-scores of the
  same state within a turn moved by a median of 0–3 points. That justified
  a **leaf value memo**: dedup inside a request, `prior_score` anchors on
  leaves seen earlier this turn, answer-from-cache when every leaf is
  cached and the decision is clear-cut, and a hold memo keyed on the
  position rather than the step (46 of 113 searches in the two-hour game
  were re-asking an identical candidate set at a later step).
- First result: 165→126 calls and 139→89 searches, but wall time went up
  because the absolute-scale rubric doubled the pilot's output per call
  and mid-turn leaves were keyed too finely for cross-window hits. Both
  are fixed; not yet re-measured.
- **Scale**: leaf scores are relative within a request, so a memo needs an
  anchor. The status-quo leaf is in almost every request and the pilots
  already trend absolute (pass-score climbs over a won game, falls over a
  lost one), so anchor-relative deltas plus a margin gate is safe enough;
  the calibrated version (map score → eventual outcome over the ~12k
  scored leaves we now have) is the research result waiting to be run.

## 5. Turn plans: the LLM can be asked once per turn

Contingent plans (steps by phase, attack/block spec, if→then rules over a
fixed event vocabulary, `otherwise`, a `hold` list) executed by the
bridge cut calls by three times and wall time by half, and the bridge
executed them faithfully. Two games lost where the search arm won on the
same seed. The cause is not execution: a plan has no foresight. "If they
cast removal, ask me" fires after the spell is on the stack, whereas the
search's projection showed the pilot the opponent's turn before it
committed. The obvious next arm is **plan-scoped search**: the pilot
proposes two or three lines, the engine rolls each through the opponent's
projected turn, the pilot scores and picks. That is the PokéChamp shape
(LLM proposes, engine simulates, LLM values) at one call per turn.

## 6. Model comparison (two seeds each vs MAD, one configuration)

Sonnet 5 2–0, Opus 5 2–0, Haiku 4.5 1–1, Opus 4.7 1–1. Qualitatively:
Opus 5 read cards best and made no rules errors; Sonnet won on value and
blocks while repeating the Bat mistake; Haiku alternates between tapping
out and a rigid "hold everything" mode, and skipped land drops to
"preserve mana" for a spell it could not cast; Opus 4.7 treats its best
permanent as a blocker rather than a clock and chose attack-none from
ahead. Two games per model is a qualitative read; ~40 games is the number
for a win-rate claim.

## 7. Harness lessons (each one cost a game or a night)

- **A `claude -p` child inherits the launching session's id.** Every game
  for a day resumed one shared 89 MB transcript with 40 compactions, and
  concurrent games interleaved their decisions in it. Pin `--session-id`.
- **Validate the pilot's reply shape, and treat null as missing.** A
  `"choice": null` killed a 69-minute game in the driver's `getAsInt`. A
  short `scores` list (one per candidate, not per leaf) went unnoticed
  for eight searches; the driver dropped it, escalated, and the yield the
  pilot had attached auto-passed the escalation — nine turns with no
  land played. Fresh sessions have no prior examples of your format: the
  schema must say exactly what it wants.
- **A yield must not cover the escalation of the window it was set in.**
- **Fairness screening** (both sides ≥3 lands at turn 7) is worth the
  probe: several early "results" were mana screws.
- **`pgrep -f name` matches the shell that runs it.** Bracket the pattern.
- **In-session cron heartbeats did not fire; server-side Routines did.**
  Monitors that print an alive line every 10 minutes and re-arm every 30
  were what actually kept the overnight run observable.
- **Archive a failed job's directory before retrying**, or the runner
  reads the stale game.
- **Per-game commit and push** meant nothing was lost across three
  restarts of the suite.

## 8. Open questions worth an experiment each

1. Plan-scoped search (section 5): does one projected search per turn
   recover the search arm's play at the plan arm's cost?
2. Leaf memo re-run with the bucket key and the brevity instruction: does
   call count drop *and* wall time?
3. Calibrate the value function: score → outcome over the suite's leaves,
   per model. Which pilot's values are best calibrated is itself a result.
4. Thinking budget as a variable: same model, low vs high effort, same
   seed. Latency is dominated by output length, so this is the cheapest
   lever we have not pulled.
5. LLM vs LLM (the suite's items 5–8): the first setting where arm (f)
   and held-mana matter, since MAD never punishes a tap-out.
