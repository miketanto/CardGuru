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

## Amendment 2 (2026-09-14 15:25Z, coordinator + user, before any Part B data): self-removal

The Phase 10 pairing games (`rl/artifacts/v7/10/pairs/`) show the Dimir main casting Requiting Hex
on turn 3 with its own Spyglass Siren as the only legal target, destroying its own creature, in
both of its games. New pre-registered Dimir counter (census + B2 readings): **removal cast when the
only legal targets are its own creatures** - offered = consults offering Requiting Hex (creature
MV <= 2, any controller), Bitter Triumph (creature or planeswalker) or Shoot the Sheriff (creature;
the outlaw clause ignored) while every legal permanent target is the seat's own (>= 1 own, 0 enemy;
enemy hexproof / shroud excluded); taken = that spell chosen. Target-level check beside it: the
first TARGET consult after casting one of the three, with an own creature chosen. Map-token
explores (and any ability that is not one of the three spells) are not counted. Reading: a correct
policy takes this at 0; B2 records whether the rate falls, with Wilson intervals, per checkpoint.
Reference levels (Phase 10 evaluation, 100 games, own mirror): M_D final 0.59 [0.492, 0.681] vs
heuristic, 0.17 vs CP7; M_L final 0.49 [0.394, 0.587] vs heuristic, 0.37 vs CP7.

## Amendment 3 (2026-09-14 ~16:20Z, the user via the coordinator, before any B2 census data): per-block checks

The user changed the cadence. After EVERY main block (M_D or M_L; not exploiter blocks) the
controller records a 50-game argmax census vs the heuristic on the main's own mirror with the fresh
snapshot (`rl/record_census.sh`, game seed 11000 every time = paired seeds across blocks; the lane's
idle driver JVM is stopped first so nothing else is resident) and prints ONE line per check:
`L11|check|M_D|n=..|h=..|trained=..|opp=heuristic|wr=k/50 = p [lo,hi]|selfrem=taken/offered|counter=taken/offered|flash_opp=k/n|ninja=taken/offered|biggest=k/n|cpg=..|consults_pg=..`
(flash_opp = flash casts on the opponent's turn or in response / all flash casts; biggest = the
highest-power enemy creature chosen on removal target consults) and
`L11|check|M_L|n=..|h=..|trained=..|opp=heuristic|wr=..|smallbig=k/n(solver_no_block=k/n)|landsearch=cast/offered|cpg=..|consults_pg=..`.
The per-block rows are **50-game development probes, not levels**. The levels stay the 100-game
lane probes at +1,024 / +2,048 / +3,072 / +4,096 (the `probe=` field of the `L11|block` line), and
the CP7 census (25 games, seed 11500) runs at +2,048 and +4,096 (an extra check line with
`opp=cp7`). The landfall precombat-share and landfall-attack counters are left out of the check
line until verified against a transcript (they read 1.000 on every B1 row). Stop: controller
hour 13 from the drill start (15:50:21Z, so ~04:50Z) or +4,096 episodes per main, whichever comes
first (was hour 10; the census adds ~3-5 min per main block). The pre-registered readings are
unchanged and are read on the 100-game levels. Flag: `rl/league11.py --census-every-block`
(default off keeps the old cadence: one 50-game heuristic census at +2,048 / +4,096). When this
was written B2 had completed blocks 0-2 and no B2 census had run (the old cadence's first was due
at +2,048).

## STATE (append dated lines; newest last)
- 2026-09-14 (start, ~12:45Z WSL): Phase 10 league running to hour 10.2, its evaluation follows; Part A may start now.
- 2026-09-14 (WSL ~13:10Z): A1 + A2 DONE, A3 WRITTEN (263e2a7 + this commit). rl/dimir_census.py, rl/landfall_census.py, rl/record_census.sh; validation outputs rl/artifacts/v7/11/validation/; section "11 / A1-A2" in V7-VALIDATION.md. Pre-registered check: ninjutsu IS offered (CP7 2 windows took 1; 8a-b 7 windows took 0) - no engine finding, no Java change. FOUND a bug in 9 / P3 (main-phase test mis-indexed): correction in the open under P3 and in 11 / A1-A2; flash bar re-based (Amendment 1). Landfall census parse-checked only (wire echo + M_L transcript audit lines). A3 smoke NOT run: Phase 10 league at h~8.9 of 10.2, evaluation after. NEXT (after E10|done and nothing resident): bash rl/record_census.sh <ck> BenchDimir heuristic 2 smoke_d, then G1Landfall 2 smoke_l; check rlgame_blocks/audit_lines and the census lines; then B1.
- 2026-09-14 (WSL ~15:40Z): E10|done (coordinator, 15:20:25Z); nothing resident verified. AMENDMENT 2 (self-removal counter, from the Phase 10 pairing games) written before any Part B data; counter in rl/dimir_census.py (Phase 9 check: 8a-b cast removal with only own legal targets 14/19 = 0.737 [0.512,0.882]; CP7 0/164). A3 SMOKE PASSED: rec_smoke_d (M_D_04096) / rec_smoke_l (M_L_03840), 2 games each vs heuristic: rc=0, consults=acts (56/32), 2 ends each, cand_refers_pool=True, 2 RLGAME blocks, audit lines 2/3, DC|/LC| lines print. B2 controller rl/league11.py = rl/league10.py + asserted patch (seed from 10/state.json with lane dirs copied to /tmp/rl_11_*, M_W frozen, cross over every other main, 100-game probe every +1,024, census 50 heur games at +2,048/+4,096 via record_census.sh, stop at +4,096 per main or hour 10); dry run OK (start M_D 4096 / M_L 3840; cross draws M_W_04096 or the other main; exploiters vs their main). LAUNCHED rl/chain11.sh (B1 = rl/run_b1_census.sh, 8 recordings one at a time, then B2 = rl/run_drill11.sh only after B1|done): logs rl/artifacts/v7/11/chain11.log, b1.log, drill/league11.log. V7-VALIDATION untouched until the Phase 10 verdict commit.
- 2026-09-14 (WSL ~15:45Z): RECORDER FAITHFULNESS CHECK (coordinator: M_D_s1end census 10/50 = 0.20 [0.11,0.33] vs the league probes 0.48 / 0.46). Cause: the checkpoint, not the recorder. (1) Flags: record_census.sh = battery_xdeck.sh server flags exactly (frozen, --seed 0, --threads 1, --device cuda --logit-bound 5 --argmax-classes, cand_refers_pool=True from the ckpt config, printed by the server) and the same job flags (eval, noYields, consultBudget 4000, stopTurn 60, deck = oppDeck = BenchDimir, searchPlies 1 / breadth 8, block + attack audit); differences: game seeds 11000 vs 930000, and -Drl.debug=true (logging only: every rl.debug branch in RLPlayer / EpisodeRunner / StateEncoder prints, none decides). (2) Proxy: forwards only; 5,090 consults = 5,090 replies, no server or driver errors. (3) Wins are the seat's: probe wins=10 = 10 RLGAME reward=+1 = 10 end r=+1. (4) M_D_s1end.pt holds 1,792 episodes (cand_refers_pool True); the league probes were of the 1,024 (0.48) and 2,048 (0.46) checkpoints, and p10_eval never scored s1end at home. Direct test: battery_xdeck.sh (the evaluation path) on M_D_s1end, 100 home games vs heuristic = 27/100 = 0.270 [0.193,0.364] (rl/artifacts/v7/11/check_s1end_battery/), overlapping the census 0.20; and the recorder on M_D_04096 = 25/50 = 0.50 [0.37,0.63] vs the evaluation 59/100 = 0.59 [0.49,0.68]. FINDING (carried, not a correction): M_D at its stage-1 end (1,792 ep) is a ~0.2-0.3 policy at home, well below the neighbouring 50-game probes; the league probes are single-checkpoint 50-game draws and do not describe their neighbours. B1 rows stand; nothing re-recorded.
- 2026-09-14 (WSL 16:02Z): B1 DONE (15:27-15:50Z, 8 recordings, all rc=0, consults = acts, every game ended; table rl/artifacts/v7/11/b1_summary.txt, per-row rec_b1_*.counts.txt + census txt/tsv + audit.txt). Headlines: M_D final vs M_D_s1end vs heuristic 25/50 = 0.50 vs 10/50 = 0.20; the final casts removal whose only legal targets are its own creatures 23/23 (s1end 2/432), counterspells 54/56 (s1end 4/102), flash on the opponent turn or in response 1/173 (s1end 9/56), ninjutsu taken 6/6, largest enemy target 37/44, creatures per game 4.34 (s1end 2.40). M_L final vs s1end vs heuristic 0.58 vs 0.32; small-into-big blocks 9/13 vs 121/187, of which the solver would not block 1/6 vs 43/106; land search 98 of 248 offers vs 127 of 282; creatures per game 4.12 vs 5.26. CAVEAT: the landfall precombat-share and landfall-attack counters read 1.000 on every row (saturated; not yet cross-checked against a transcript). B2 RUNNING (chain11 -> run_drill11.sh at 15:50:21Z): verified by pgrep at 15:51Z (league11.py, rung0_lane_league.sh BenchDimir 4352, servers 7950 / 7960, JVM 7912); first block n=0 M_D cross(quota) vs M_L_03840 141/256, 618 s, rc=0. Log rl/artifacts/v7/11/drill/league11.log; keepalive 70437 to ~03:22Z covers controller hour 10 (~01:50Z).
- 2026-09-14 (WSL 16:40Z): AMENDMENT 3 (user: per-block checks) applied. STOP touched 16:20Z; the controller finished block n=2 (X_D exploit vs M_D_04352, 0/256, 1,780 s) and exited L11|done|reason=stopfile|blocks=3|h=0.81 at 16:39Z; nothing resident. rl/league11.py patched behind --census-every-block (default off = the old cadence): after every M_D / M_L block the idle driver 7912 is stopped, rl/record_census.sh records 50 heuristic games (seed 11000) with the fresh snapshot, and one L11|check line is printed (full census lines appended to rl/artifacts/v7/11/drill/census_lines.txt); CP7 census 25 games (seed 11500) at +2,048 / +4,096; the census runs after the block state is saved. rl/landfall_census.py gained creatures per game (LC|..|board|). Check line tested on the B1 recordings of both mains. RESUMED 16:39:49Z: setsid nohup bash rl/run_drill11.sh --census-every-block --hours 13 >> rl/artifacts/v7/11/drill/league11.log (controller clock kept from the drill start 15:50:21Z, so the stop is hour 13 = ~04:50Z, or +4,096 per main). Keepalive: sleep 64800 started ~16:21Z (to ~10:20Z next day) plus 70437 to ~03:22Z. Note: check_line takes the first |consults= in the census text; record_census.sh prints CENSUSREC first, so the per-game consult count is right in real runs (a test file with LC lines first read the block-consult count instead).
- 2026-09-14 (WSL 17:34Z): rl/record_census.sh now also saves every full RLGAME block of a recording to rl/artifacts/v7/11/rec_<tag>.transcripts.txt (awk over the driver-server log lines written during the recording, as replay_ck.sh does; the driver log is overwritten by the next census) and adds |transcript_games=N to the CENSUSREC line (the L11|check parser reads fields by name, unaffected). Swapped in atomically (mv of a checked .new file) at 17:34:26Z by rl/swap_rc.sh in a gap (after L11|check|M_L n=7, while X_L trains; no census executing - a first attempt from an inline wsl command refused because its own argv matched the pgrep pattern). First census with transcripts = the next M_D check. Transcripts are gitignored (~7k lines per 50-game census); the M_D n006 transcripts were already overwritten before this change.
- 2026-09-14 (WSL ~18:25Z): transcripts verified on a real census: rec_drill_M_D_n009_t05120.transcripts.txt holds 50 RLGAME blocks, CENSUSREC transcript_games=50 (gitignored; local only). FIRST 100-GAME LEVEL: M_D +1,024 (5,120 ep, block n=9) = 0.620 [0.522,0.709] vs the heuristic, inside the Phase 10 final home level 0.590 [0.492,0.681] - one point, no reading yet. Per-block 50-game checks so far M_D n3 0.54 / n6 0.44 / n9 0.48; exploiter X_D blocks n2 / n8 at 0/256 and 5/256 (7 stalls), 1,780 / 2,137 s each (the slowest blocks; they eat into the hour-13 budget).
- 2026-09-14 (WSL ~18:45Z): MEASUREMENT CHECK (coordinator): Requiting Hex blight vs destroy. The published self-removal figures STAND (spell-level: all legal destroy targets own; 0 engine mismatches over Phase 9, B1 and drill n003/n006/n009); the census line's secondary target-level "own creature chosen" field DID include blight choices (the transcript KILL label marks every creature target, blight included) and is replaced by a split: forced self-destroy / destroy-target consults / blight paid (on an X/1 = killed) - B1 final vs heuristic 13 forced / 29 blights (13 killing an X/1, 13 during forced casts); n009 18 / 29 (15, 18). Section "11 - measurement check" in V7-VALIDATION. Also: the census *_games.tsv header lacked the 3 self-removal column names (18 vs 21) - fixed. rl/dimir_census.py swapped atomically in a drill gap via rl/swap_dc.sh; the L11|check selfrem field (spell-level) is unchanged, the blight split goes to drill/census_lines.txt via the DC line.
- 2026-09-14 (WSL ~22:30Z): PHASE 11 CLOSED. B2 STOPPED EARLY BY USER DECISION at the +2,048 point (~21:55Z). The main session killed the drill-down mid-exploiter-block (rl/stop_drill11.sh): X_D block n=26 lost, no learner state lost, last main blocks n=24 M_D 6,400 / n=25 M_L 6,144, no L11|done line. Part C written in V7-VALIDATION: "11 / B1"; "11 / B2" (levels M_D 0.59 / 0.62 / 0.59 and M_L 0.49 / 0.41 / 0.53 = plateau on 2 of 4 points; CP7 checks 0.20 / 0.12 over 25 games; the per-block census table; self-play drift as the leading hypothesis with its limits); "Phase 11 verdict"; plus the HANDOFF-V7 UPDATE line. Nothing of Phase 11 is resident. At 22:25Z a policy server on 7947 (drill pool M_D_06400) and a driver JVM, both started ~22:24Z after the kill, belong to another session and were left alone. Next phase: rl/PHASE12-CP7.md (main session / Phase 12 agent).
