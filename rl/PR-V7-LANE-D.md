# PR text for v7/lane-d -> main (gh is not installed here; open at https://github.com/miketanto/CardGuru/pull/new/v7/lane-d and paste)

## v7 Lanes D and C — Phases 0a, 0d, 0e, 4a–4g: wire contract, probes, baseline, the `--arch v7` server

All gates are numbers in `rl/V7-VALIDATION.md`; every failed run is a row there, not a deletion. Phase 4 is closed: the two cuda gates that were open at the last handoff are in (§4g correction rows).

### Delivered
- **0a** `rl/WIRE-V7.md` — the consult contract between `-Drl.encoderV=7` and `--arch v7` (token groups, field orders, edge types, candidate types, opponent tokens, hello widths); `rl/wire_validate.py` (schema + semantics, names the first violation), `rl/wire_fixtures.py` → `rl/fixtures/v7` (7 valid, 14 deliberately broken), `tests/test_wire_v7.py` (22).
- **0d** `rl/probes/faithfulness.py`, `rl/probes/leak.py` — the probe harness (linear readouts with game-grouped hold-out; the leak gate levels 1–3 for any hidden channel), self-tests in `tests/test_probes.py`.
- **0e** tag `v6-baseline` = 9ad2a1a; `rl/artifacts/v7/baseline.md` (`entattn_check` 23 checks with the pre-existing R0-NOBIAS 3.05e-5 state, `consult_cost` cuda, a 100-game rung-0 smoke).
- **4a–4f** `rl/v7_obs.py` (parse + `V7Obs` + collate + hello check), `rl/v7_net.py` (card table + adapter, per-zone MLPs, player/game/candidate/opponent builders), `rl/v7_encoder.py` (edge-typed attention, exact identity at init by design), `rl/v7_heads.py` (pointer + bilinear, LSTM on the game token), `rl/v7_value.py` (separate value trunk; leak gate 1–3), `rl/v7_belief.py` (belief module; off = bit-identical; stop-gradient), each with its test file.
- **4g** `rl/v7_policy.py` + `rl/v7_check.py` (15 checks, all pass, includes `entattn_check` = `baseline.md`); `policy_server.py --arch v7` (handshake, `act_v7`, PPO over `V7Obs` with BPTT windows, batcher, `--frozen`, checkpoints with dims + config); `rl/v7_deckctx.py` (deck context at hello); `p10_init_net.py --arch v7`, `update_profile.py --arch v7`, `consult_cost.py --arch v7`; `tests/test_v7_server.py` (10).
- **4g cuda gates** — memory gate passes (RSS 2.0 GB); cuda peak 11.4 GB at `--tbptt 32 --ep-batch 4` vs 2.85 GB at 16/2 at the same rate (489 vs 582 ms/step: the per-window compute is the cost); consult 18.1 ms single / 2.1 ms per row batched. A 5,000-step update is ~40 min at either setting — recorded for Phase 7's budget, not fixed here.
- **3d server side** `rl/v7_leak_real.py` — the leak gate over a real `-Drl.oracle` recording; passes on three recordings from the Lane B tracker (`v7/lane-b`).
- **1d bookkeeping** sweep config (b) FAIL row; configs c/d backlogged by decision (2026-09-12); `card_emb_v8` stays the accepted embedder.

### What changed on `main`
Nothing that runs by default: every path is behind `--arch v7` (server) or lives in new `rl/v7_*.py`, `rl/probes`, `rl/fixtures/v7` files. `rl/entattn_check.py` reports the same 23 lines as `rl/artifacts/v7/baseline.md` after every server edit (checked by `rl/v7_check.py`'s V6-SAME).

### Pre-registered
The v7 server cannot change any v6 number (the v6 arms are untouched and V6-SAME holds). Nothing here trains: Phase 5 integration against the Lane B driver (`v7/lane-b`, Phases 3a–3d done) is the gate that authorises training.

### Known open items (recorded in `rl/HANDOFF-V7.md` §G)
Server defaults should move to `--tbptt 16 --ep-batch 2`; WIRE §2c player width 21 is a cross-lane commit still to make; the PASS afterstate at the joint sites is a WIRE amendment to propose.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
