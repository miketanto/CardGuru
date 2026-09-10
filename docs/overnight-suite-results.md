# Overnight suite results: four pilots vs MAD, two seeds each

Branch `build/stackwise-campaign`, 2026-09-10 05:22–10:57 UTC. Plan in
`docs/overnight-suite-plan.md`; search arms in `docs/stack-search-plan.md`.
Every game: Dimir midrange mirror vs XMage's MAD, pilot on the play, arm (f)
props (`cardguru.project_turn=3 cardguru.respond=true`), plans required,
baseline briefing, one fresh `claude -p` session per game, inherited
`CLAUDE_EFFORT=high`. Raw data: `research/data/suite.jsonl` (one row per
game) and `research/data/suite/<model>_s<seed>/` (game log, daemon log,
replay `g1.html`, decision digest `g1_review.md`).

**Read this as a qualitative sample, not a ranking with error bars.** Two
games per model cannot separate four pilots; the handoff's power table
(~40 games for a 70% rate) still applies to any win-rate claim.

## Records

| pilot | seed 23 | seed 31 | record | final life (A−B) | tapped-out main phases | hellbent turn | wall |
|---|---|---|---|---|---|---|---|
| Sonnet 5 | **WIN** T21 | **WIN** T18 | 2–0 | +6, +9 | 10, 25 | —, — | 37, 52 min |
| Opus 5 | **WIN** T29 | **WIN** T17 | 2–0 | +3, +7 | 9, 14 | 12, — | 59, 52 min |
| Haiku 4.5 | **WIN** T25 | loss T16 | 1–1 | +14, −2 | 7, 14 | —, — | 99, 72 min |
| Opus 4.7 | loss T26 | **WIN** T26 | 1–1 | −4, +9 | 6, 28 | 12, 24 | 54, 122 min |

Both seeds passed the fairness screen (≥3 lands each side at turn 7) in
every game except haiku s31, where the pilot had 2 lands at turn 7 with a
land in hand on turns 5, 9 and 11 — play, not screw (see below).

Pilot call latency (mean / median seconds per decision): sonnet 12.7/6.9
and 22.1/11.2; opus 5 16.7/11.8 and 19.7/16.5; opus 4.7 25.0/13.2 and
33.2/22.6; haiku 32.2/24.1 and 56.2/45.9. Haiku is the slowest pilot
because it writes the most thinking per decision, not because of context.

## Selection for items 5–8

Rule from the plan: wins, then mean final life margin, then tap-out rate.

1. **Sonnet 5** — 2–0, margin +7.5
2. **Opus 5** — 2–0, margin +5.0
3. **Haiku 4.5** — 1–1, margin +6.0 (Opus 4.7: 1–1, margin +2.5)

Pairings for the LLM-vs-LLM games: Sonnet–Opus 5, Sonnet–Haiku, Opus
5–Haiku, each with the higher-ranked pilot on the play, plus Sonnet–Opus 5
with seats swapped. Honest caveat: Haiku over Opus 4.7 rests on one life
margin from a game Haiku took nine turns to close from 24–4; the two are
not separable on this data, and Opus 4.7's s31 win was actually delivered
by MAD decking itself into Sheoldred triggers.

The pilot-vs-pilot harness (plan build item 3: seat B interactive,
self-relative state, seat-routed daemons) is **not built**. It needs the
daylight validation the plan calls for before it runs unattended.

## How each pilot played (from the digests)

**Sonnet 5** — patient, value-first. Develops mainly into tapped-out
windows, holds flash creatures and removal, blocks well: the s23 game was
decided by waiting through MAD's whole turn, flashing Curiosity at
declare-attackers and double-blocking the second Sheoldred; s31 by Bat
taking Kaito on T3 and Sheoldred's drain against an empty-handed MAD.
Repeats the same class of error the user flagged in g6/g7: misreads its
own cards' interactions — attacked Sheoldred into an untapped deathtouch
Preacher on s23 T9 ("Sheoldred easily survives 2 damage"), bounced the Bat
with ninjutsu on s31 T7 and chump-blocked with it on T14, both returning
the exiled card; activated ninjutsu twice on s23 T19 because "Kaito never
actually appears" while the first was on the stack. Over-holds when
already winning (10 lands, 7 cards in hand, T19–T20 of s23). Its written
plans were actually followed ("hold exactly 4 for Curiosity" for six
straight turns).

**Opus 5** — information-first. Reads card text literally and self-corrects
(s23 T24: "their Curiosity already spent its stun counter during their
untap step... Drowner's ability has no legal target"). Treats stun
counters and exile-until-leaves as a resource: the s31 game was won on T9
by stunning Curiosity with one Drowner and shuffling it away with the
other in the same main phase, bypassing its return clause; it declined
ninjutsu on T7 because bouncing the Bat "hands their exiled Kaito straight
back" — the exact mistake Sonnet made on the same seed. Discounted engine
leaves where a hellbent opponent "casts" spells as "fiction". Ground back
from hellbent at T11 and 12–12 at T26 in s23 through Kaito +1 emblems and
Restless Reef to an exact-lethal line it had written in its plan two turns
earlier. No rules errors found in either game. Weaknesses: slow to close,
holds removal it never casts (Cut Down drawn s31 T11, never used).

**Haiku 4.5** — swings between tapping out for the biggest sorcery-speed
play and a rigid "hold everything" mode driven by whatever plan it last
wrote. The s23 win took nine turns from 24–4 because of three Restless Reef
misplays (animated a tapped land and claimed it could attack; passed
through declare-attackers to "preserve mana" then animated postcombat;
attacked into a summoning-sick blocker) and four turns of lethal math with
a creature it no longer had. The s31 loss: on 3 lands at T11 with a land in
hand on T5, T9 and T11, skipping the drop each time to "preserve full mana"
for a four-drop it could not cast. Rules slips: "Floodpits has vigilance",
"Sheoldred's draw fires on cast", "Cut Down cannot kill my main threats"
(it then lost both Bats to Cut Down). Its removal timing was fine.

**Opus 4.7** — cautious, trade-everything midrange that values Sheoldred and
Kaito as "blocker" or "engine" rather than as a clock. s23: led 21–13 at
T17, chose attack-none from ahead on T9, T11 and T13, spent both Preachers
blocking, and on T18 scored "Cast Go for the Throat" 95 with MAD's Sheoldred
on the stack — the spell hit the only legal target, a Siren — then wrote
"Successfully killed opp's Sheoldred!" against a leaf that plainly listed
Sheoldred on their board. s31: Kaito died three times because it always
used −2 and left him at 2 loyalty undefended; animated Restless Reef twice
and chose attack-none both times; the win came on MAD's turn 26 when
MAD's two Curiosities drew it six cards into Sheoldred triggers. 28
tapped-out main phases, and plans that changed within the same turn.
"Cut Down only kills 2-cost creatures" (it keys off power+toughness ≤ 5).

## What the night cost in harness fixes (all on the branch)

These are the bugs the suite exposed before the clean run. Every game in
the table above ran with all of them fixed; g1–g10 in `research/data/mirror/`
did not.

- **One shared pilot session for every game since the daemon was written**
  (173be2d). A `claude -p` child inherits the launching Claude Code
  session's id; g1–g10 and the aborted dry run all resumed one 89 MB
  transcript with 40 auto-compactions, and concurrent games interleaved
  their decisions in it. Now a fresh `--session-id` per game.
- **`getAsInt()` on a JSON null** killed a 69-minute haiku game when the
  pilot answered `"choice": null` (9db2e3a). Driver reads are now
  null-tolerant; the daemon retries a null required key.
- **Short leaf-score lists** — with no prior examples in a fresh session,
  sonnet scored one number per candidate instead of per leaf for eight
  searches; the driver dropped the list and escalated, and the yield the
  pilot had attached to the search reply auto-passed the escalation, so it
  played no land for nine turns (c70be2d). Schema spells out the count,
  daemon retries short lists, YieldGate skips the same window's
  escalation.
- **Runner reads g1** — a stale directory from a failed attempt made the
  retry g2 (40686bc). Old attempts now move to `suite/aborted/`.
- In-session `CronCreate` heartbeats fired twice in eight hours and were
  replaced by a 10-minute Monitor line plus an hourly server-side Routine;
  the Routine restarted nothing because nothing died.

Archived, not counted: `suite/aborted/haiku45_s23_shared_session`,
`haiku45_s23_jsonnull`, `sonnet5_s23_short_scores`; g10 in `mirror/`
(sonnet s31, arm f, loss) is tainted by the shared session.

## A/B: search vs leaf memo vs turn plans (Sonnet 5, seed 23, on the play)

Four arms on the same deal, one game each, run 13:07–14:35 UTC. Data in
`research/data/dp/`. One game per arm: read the speed columns as real
(they are structural) and the result column as anecdote.

| arm | switch | result | wall | pilot calls | of which searches | pilot time |
|---|---|---|---|---|---|---|
| A search (suite baseline) | default | **WIN** T21 | 36 min | 165 | 139 | 35 min |
| A′ search + leaf memo | `cardguru.leaf_cache=true` (default now) | **WIN** T21 | 52 min | 126 | 89 | 43 min |
| B pure turn plan | `cardguru.turn_plan=true cardguru.plan_combat_search=false` | loss T30 | 20 min | 89 | 0 (30 plans) | 18 min |
| B′ plan + combat search | `cardguru.turn_plan=true` | loss T20 | 16 min | 51 | 12 (17 plans) | 16 min |

**Leaf memo (A′).** Did what it was built for on volume — 50 fewer
searches from the position-keyed hold memo, 643 duplicate leaves folded
inside requests — but not on time: the pilot wrote twice as much per call
under the absolute rubric (why 246→448 chars, median output tokens
337→704), and cross-window hits were 3 because mid-turn leaves were keyed
on the exact step. Both fixed after the run (combat-bucket key, "two
sentences" instruction); needs a re-run before it counts.

**Turn plans (B, B′).** Three times fewer calls and half the wall time,
and the bridge executed every plan faithfully (the per-turn trace shows
each planned land and cast landing when the menu offered it; B′ ran 180
windows from 17 plans with 34 escalations). Both games were lost. B's
plans were written at upkeep before the draw, passed over cards drawn
afterwards, and chose `attack_none` 11 turns of 15 with nothing
simulated — fixed in f86ecc3 (plan after the draw, `hold` list plus
escalate-once for unplanned castables, combat search kept on). B′ curved
out on plan (Preacher T5, Sheoldred T7, Bat+Preacher T9, Curiosity T11)
and lost every one of them to MAD's removal while its own removal came
late; the search arm on the same seed flashed Drowner into their T4
Mastermind and blocked Sheoldred with Curiosity+token. What the plan
arms lack is exactly what arm (e) gives the search: a projection of the
opponent's turn before committing. Their `they_cast:removal → ask` rule
fires after the spell is already on the stack.

**Next step that follows from this**: plan-scoped search. When the pilot
writes its plan it names two or three candidate lines; the driver rolls
each out through the opponent's projected turn (the arm (e) machinery,
which already exists) and the pilot scores the leaves and picks the plan.
One extra leaf_eval per turn, the plan gets the foresight the search had,
and the per-window cost stays at zero. Not built.

## Observations that cut across pilots

- **Deep-Cavern Bat's leave clause** is the most common rules error
  (Sonnet ×2, Haiku's g6/g7 earlier). Opus 5 is the only pilot that
  reasoned about it correctly, and it turned the same clause into a win.
- **Deathtouch blockers**: Sonnet and Haiku both attacked a big creature
  into an untapped deathtouch Preacher; Opus 5 explicitly declined to.
- **Restless Reef** is a trap for the weaker pilots (Haiku ×3, Opus 4.7 ×2):
  animate-then-can't-attack, or animate postcombat. The card_reference text
  is there; the pilots misread "enters tapped" and summoning sickness on a
  land that became a creature this turn.
- **Score/choice divergence**: in several windows the pilot's `why` argues
  for one line while its scores pick another (Opus 5 s23 T9, s31 T15;
  Opus 4.7 s23 T11). The driver acts on the scores. Worth a check in the
  digest tool: flag windows where the highest-scored candidate is not the
  one the reasoning names.
- **Arm (f) stayed inert** against MAD in all eight games (`resp_fired=0`),
  as predicted: MAD taps out every turn. Its first real test is items 5–8.
- **Closing speed** is the shared weakness: four of the six wins took five
  or more turns from a dominant board (Haiku 24–4, Opus 4.7 21–6, Sonnet
  T19–T21 over-hold, Opus 5 s23 grind). Lethal-finding is a candidate for
  an explicit search mode: enumerate attack sets against the actual
  blockers and score "opponent at 0" leaves as terminal.
