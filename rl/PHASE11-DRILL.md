# PHASE11-DRILL — can the Dimir and landfall mains keep growing, and do they use their cards? (runbook + pre-registration, 2026-09-14; v7/lane-d)

Why (chat, 2026-09-14, after the Phase 10 replays): the white main graduated
at 1,024 episodes and held ~0.72 vs the heuristic; the Dimir main sat at
0.48 / 0.46 and rose to 0.58 only after cross-deck games; the landfall main
sat at 0.44 / 0.42 / 0.44 (untrained 0.28). The replays show why it matters
to look past the win rate: Dimir aimed removal at the best creature in one
game and at tapped 1/1s in the other, developed three creatures in fifteen
turns, and cast counterspells only at 5 life; landfall blocked pumped
attackers with smaller creatures three times where the combat search would
not block. The user asked two things: **drill down on Dimir and landfall to
see whether they keep growing**, and **how to check whether Dimir uses
flash, ninjutsu (Kaito) and its other instant-speed cards**.

Rules that bind: CLAUDE.md; HANDOFF-V7.md §K and the latest section;
rl/PHASE10-LEAGUE.md (the controller, the quota amendment, the STATE lines);
the operational lessons in rl/OVERNIGHT-7D.md / rl/PHASE8-DECKS.md STATE
(WSL VM dies without an open session — a 12 h session-independent keepalive
was started 2026-09-14 ~12:10Z; at most two policy servers + two driver
JVMs; kill only via script files whose name cannot match their pattern;
never edit a lane script or server-side Python while a lane runs). Wilson;
≥ 100 games per level (50-game rows are development probes); pre-register;
correct in the open; commit + push after each finding; commit messages end
with `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`. Append a dated
STATE line at the bottom of this file after every step.

**Coordination with Phase 10 (binding):** the Phase 10 league runs until
controller hour 10.2 (~14:15Z WSL), then the Phase 10 agent runs its
evaluation `rl/p10_eval.sh` (prints `E10|…` lines, ends `E10|done`) and
writes its rows. Part A below is CPU-only file work and may run during
that. Part B starts only after `E10|done` appears in the evaluation log AND
`pgrep -fa 'policy_serve[r]|RLDriverServe[r]|league1[0]'` shows nothing
resident. Do not edit `rl/league10.py`, `rl/p10_eval.sh`, `rl/probes/*` or
any Phase 10 file while Phase 10 is running (copy what you need).

Engine facts (checked in the pinned XMage card classes):
- flash: Floodpits Drowner, Enduring Curiosity, The Wondrous Wasp
  (creatures), Nowhere to Run (enchantment, removal-like);
- ninjutsu: Kaito, Bane of Nightmares (planeswalker; ninjutsu is an
  activated ability from hand, legal only after blockers are declared on
  the seat's own turn, returning an unblocked attacker to hand);
- instant removal: Bitter Triumph, Requiting Hex, Shoot the Sheriff;
- counterspells: Spell Snare, Spell Pierce, We Say Thee Nay!;
- G1Landfall: landfall creatures (Scute Mob, Plated Geopede, Scythe
  Leopard, Snapping Gnarlid, Grazing Gladehart, Valakut Predator, Lotus
  Cobra, Rampaging Baloths, …), land search (Evolving Wilds, Harrow,
  Nissa's Pilgrimage, Rampant Growth, …), Adventuring Gear (read the deck).

## Part A — measurement tools (CPU only; may run while Phase 10 finishes)

A1. **Dimir card-play census** `rl/dimir_census.py` over v7 recordings that
    carry the seat's choice (a teacher `y` or the `{"a":k}` reply after the
    consult; `rl/probes/instant_speed.py` shows how to read game token
    step/active/stack and the chosen candidate; card names via
    `rl/artifacts/cards_v1/index.json` from the referents' card ids). Per
    game and pooled, with Wilson intervals:
    * **ninjutsu**: consults on the seat's own turn in a combat step after
      blockers where a Kaito ACTIVATE candidate (ability from hand) is
      offered → offered count, taken count; Kaito cast as a spell (main
      phase) separately;
    * **flash**: for each flash card, offers at instant speed (opponent's
      turn, a non-main step, or stack non-empty) vs taken; and every cast of
      a flash card classified by timing (instant speed vs own main phase);
    * **counterspells**: offers (they are only legal with a spell on the
      stack) vs taken;
    * **removal targeting**: on TARGET consults for the four removal cards,
      whether the chosen target is the highest-power legal enemy creature,
      and the rate of targeting a tapped creature when an untapped one of
      equal or higher power was legal;
    * **board development**: creatures cast per game, turn of the first
      creature, lands played by turn 4.
    Validate it on the Phase 9 recordings `rl/artifacts/v7/9/rec_cp7_dimir*.jsonl`
    (CP7 in the seat, the reference) and `rec_dim_dimir*.jsonl` (the 8a-b
    policy). **Pre-registered check that comes first:** if ninjutsu is never
    OFFERED to either seat across those recordings, the gap is in the driver
    (the seat is not consulted after blockers, or `getPlayable` omits the
    hand ability) — record that as an engine finding with the evidence (grep
    the step distribution of consults) and do not report ninjutsu "use" at
    all until it is fixed; the fix is a Java change that waits for no lane
    to run.
A2. **Landfall census** `rl/landfall_census.py` (same inputs, G1Landfall):
    land drops per game and per turn; share of land drops made in the
    precombat main phase on turns the seat attacks (a landfall deck wants
    the trigger before combat); land-search spells cast and their timing;
    attacks by landfall creatures on turns with a land drop vs without;
    Adventuring Gear cast / equipped; blocks where the blocker is smaller
    than the attacker (both P and T) and the rate the combat search would
    not have blocked (from the debug transcript's `[audit]` lines if the
    recording has none — say which source).
A3. **Recorder** `rl/record_census.sh <ckpt> <deck> <opp> <games> <tag>`:
    argmax games through a frozen eval server (`--argmax-classes`) and the
    record proxy (the `record_p9.sh dim` path), own ports 7947 / 7948 /
    driver 7913, output `rl/artifacts/v7/11/rec_<tag>.jsonl` (gitignored) +
    a committed counts file. Smoke 2 games.

## Part B — after `E10|done` and nothing resident

B1. **Baseline census**: 50 argmax games vs the heuristic and 25 vs CP7
    (own deck mirror) for each of `M_D_s1end`, the Phase 10 final `M_D`,
    `M_L_s1end`, the final `M_L` (pool snapshots in
    `rl/artifacts/v7/10/pool/`). One recording at a time. Rows "11 / Dimir
    census" and "11 / landfall census".
B2. **Drill-down continuation** (`rl/run_drill11.sh`): the Phase 10 league
    controller with only `M_D, M_L, X_D, X_L` training (copy the controller
    as `rl/league11.py` if it needs a learner-subset / schedule flag; M_W
    enters as a frozen cross-deck pool member at its Phase 10 final
    snapshot), resumed from the Phase 10 state of those four learners,
    stage 2 mix with the quota (cross 30 % over {M_W, the other main}, heur
    10 %), block 256, schedule `M_D, M_L, X_D, M_D, M_L, X_L`, +4,096
    episodes per main or controller hour 10, whichever first. Growth
    yardstick: a **100-game** probe vs the heuristic on the own mirror at
    +1,024 / +2,048 / +3,072 / +4,096 (levels, not development probes), and
    the A1/A2 census (50 heuristic games) at +2,048 and +4,096.
B3. Rows, verdict, handoff (§ below).

**Pre-registered readings (per main; one seed each):**
* **Keeps growing**: the +4,096 level is clear above the Phase 10 final
  home level (the 100-game row from `p10_eval.sh`); **plateau**: every
  point inside the first point's interval; **regresses**: the last point
  clear below the first.
* **Dimir card use** (A1 counters, final vs `M_D_s1end` vs CP7 reference):
  ninjutsu taken when offered > 0 (and whether it rises); flash cards cast
  at instant speed at a rate clear above the Phase 9 floor 0.077 [0.047,
  0.123]; counterspells taken when offered; removal on the highest-power
  target clear above chance (the Phase 9 P2 bar, +0.16 for the 8a-b
  policy); creatures per game rising. A win-rate rise with none of these
  moving is recorded as "wins more without using its cards differently".
* **Landfall card use**: precombat land-drop share on attack turns,
  small-into-big block rate falling, land-search spells cast before the
  landfall payoff attacks.
Cannots: one seed; the continuation cannot separate cross-deck pressure
from more episodes (no no-cross control on one GPU); M_W is frozen, so the
cross-deck opponent does not adapt; the payment sub-consult is still the
engine's; census recordings are argmax play, not the sampled training
policy.

## Part C — write-up

Sections in rl/V7-VALIDATION.md for A1/A2 validation, B1, B2 (the growth
table per main with the census columns), a "Phase 11 verdict" paragraph (two
sentences per deck with numbers), a dated UPDATE line + new section prompt
in rl/HANDOFF-V7.md.

## Amendment 1 (2026-09-14, before any Part B data): the flash bar

The "Phase 9 floor 0.077 [0.047, 0.123]" came from `rl/probes/instant_speed.py`, whose main-phase
test was mis-indexed (correction in V7-VALIDATION "11 / A1-A2"). Corrected, the 8a-b policy casts
96/120 flash cards "at instant speed" by the literal rule, all in its own upkeep / draw / damage
step, and 0/120 = 0.000 [0.000, 0.031] on the opponent's turn or in response. The flash reading
becomes: **flash casts on the opponent's turn or in response, clear above 0/120 [0.000, 0.031]**
(the strategic use); the literal-rule rate (0.800 for 8a-b) is reported beside it and is not a bar,
because casting in one's own upkeep inflates it. Ninjutsu: the pre-registered first check passed
(offered to both seats: CP7 2 windows, took 1; 8a-b 7 windows, took 0), so ninjutsu use is reported.
Removal targeting: the census counts enemy creatures only (8a-b: +0.192 [+0.077, +0.308] over
chance); P2's +0.16 included own-side targets. CP7 gives no removal reference (no TARGET consults
through the teacher seat).

## STATE (append dated lines; newest last)
- 2026-09-14 (start, ~12:45Z WSL): Phase 10 league running to hour 10.2, its evaluation follows; Part A may start now.
- 2026-09-14 (WSL ~13:10Z): A1 + A2 DONE, A3 WRITTEN (263e2a7 + this commit). rl/dimir_census.py, rl/landfall_census.py, rl/record_census.sh; validation outputs rl/artifacts/v7/11/validation/; section "11 / A1-A2" in V7-VALIDATION.md. Pre-registered check: ninjutsu IS offered (CP7 2 windows took 1; 8a-b 7 windows took 0) - no engine finding, no Java change. FOUND a bug in 9 / P3 (main-phase test mis-indexed): correction in the open under P3 and in 11 / A1-A2; flash bar re-based (Amendment 1). Landfall census parse-checked only (wire echo + M_L transcript audit lines). A3 smoke NOT run: Phase 10 league at h~8.9 of 10.2, evaluation after. NEXT (after E10|done and nothing resident): bash rl/record_census.sh <ck> BenchDimir heuristic 2 smoke_d, then G1Landfall 2 smoke_l; check rlgame_blocks/audit_lines and the census lines; then B1.
