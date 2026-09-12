# PR text for v7/lane-b -> main (gh is not installed here; open at https://github.com/miketanto/CardGuru/pull/new/v7/lane-b and paste)

## v7 Lane B — Phase 3 (3a–3e): engine emission behind `-Drl.encoderV=7`

All gates are numbers in `rl/V7-VALIDATION.md` (rows §3a–§3e on this branch; the file also grows on `v7/lane-d`, both append at the end — merge keeps both). Every deviation from a pre-registered gate is stated in its row, not moved.

### Delivered (`rl/xmage-src`, all additive, nothing under `encoderV < 7` changes)
- **3a** the WIRE-V7 skeleton: `StateEncoder` V7 block (game / player / entity tokens, names, token flags, the v6 edges shifted into the token index space), `CandMeta` built at all seven `RLPlayer` consult sites, `SocketPolicyClient` v7 hello + consult through one shared v6 writer. Gate: 101 + 136 recorded consults validate; the v6 arm is identical to the unpatched build within the engine's own run-to-run noise (measured by running the unpatched build twice: which of several identical opponent lands is tapped for mana is not on the seeded stream); live 10-game check against `policy_server.py --arch v7`.
- **3b** entity idx 10–63 (body now / printed, damage, counters, status, type, 18 keyword bits off the object's live abilities, castable / mana-left / legal-targets / can-attack / can-block / lethal-as-is, stack X / modes / mine / is-ability) and the candidate afterstates for LAND / SPELL / ACTIVATE / TARGET / ATTACK / BLOCK. Gate: 1,562 consults, 12,838 rows, 0 disagreements with the v6 row, 0 failed identities; a further 972-consult spell-first run exercised damage, blocking and stack rows (0 disagreements).
- **3c** `can_block` (6) and `stack_above` (7) edges. Gate: 100 % referent coverage over 2,955 consults, every BLOCK candidate's (blocker, attacker) pair is a `can_block` edge, `stack_above` chain correct on the 2 two-object consults observed.
- **3d** `RLKnowledgeWatcher`: the opponent knowledge tracker as an engine watcher (hand slots by origin / age / known / seen, remaining deck from the open list, opponent-action history, `v7_oe_hand` under `-Drl.oracle`). Gate: leak gate levels 1–3 pass on three real oracle-labelled recordings; `handDrift` 0 over 1,413 consults; deck accounting exact; the identity-known path is not exercised on the rung decks (stated).
- **3e** `-Drl.wireDump` (the v7 dump = the wire, byte-identical to a recording), v7 counters in the driver summary, `rl/replay_3e.sh`. Gate: 20 games × 2, 477 consults each, 384 lines byte-identical and every differing field in the tapped-land noise class with equal column sums; not byte-equal literally, and the reason is measured (engine mana-payment order), not argued.
- Toolchain: `rl/wire_echo_server.py`, `wire_record.sh`, `wire_diff.py`, `wire_census.py`, `wire_check_3b/3c/3d.py`, `wire_trace_3d.py`, `live_check_3a.sh`, `sync_lane_b.sh`, `drivers_3a.sh`, `drivers_3d.sh`, `old_build_record.sh`, `record_3b.sh`, `replay_3e.sh`.

### What changed on `main`
The v6 arm: nothing observable. `encodeEntityView` builds the v7 block only when `ENCODER_V >= 7`; the v6 consult bytes come from the same writer as before (verified against recordings of the unpatched build). `cardEnt` gained two parameters; `PolicyClient` gained a defaulted 4-arg `choose`; `RLPlayer.consult` gained a `CandMeta` overload. A driver JVM started without `-Drl.encoderV=7` behaves as before.

### Pre-registered
Phase 3 cannot change any v6 number (checked: the v6 arm recordings). Nothing here trains; Phase 5 integration against `v7/lane-d`'s server is the gate that authorises training.

### Open (recorded in `rl/HANDOFF-V7.md` §G on lane-d)
WIRE §2c player width 21 (a cross-lane commit); the PASS afterstate at the joint sites (a WIRE amendment to propose); player idx 14; fields with 0 exercised rows and the tracker's known-identity path go to 5b's coverage run.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
