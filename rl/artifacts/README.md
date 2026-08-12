# RL training artifacts — fresh-environment pickup

Everything under `tmp/` mirrors the `/tmp/...` layout the rl/ scripts
expect. To restore on a fresh machine:

```bash
bash rl/restore_artifacts.sh
```

That copies the tree to `/tmp` and gunzips the datasets in place. The
XMage engine itself is rebuilt separately (see the Phase 5 handoff /
PHASE5-*.md: clone pin 7554968c into /home/user/mage, apply
rl/xmage-src + benchmark/xmage/src mirrors, `mvn -pl Mage.Tests
test-compile`).

## Checkpoints (leaderboard names → files)

| name | arch/cdim | path (after restore) |
|------|-----------|----------------------|
| e0_bc | e0/38 | /tmp/rl_p5_c1/student_v3.pt |
| e0_ppo | e0/38 | /tmp/rl_c2v3_noshape_s0/net.pt |
| e0_champ | e0/38 | /tmp/rl_league_bc_s0/e0_league_final.pt |
| attn_bc | attn/91 | /tmp/rl_p5_c1/student_e2attn.pt |
| attn_v2 | attn/91 | /tmp/rl_c6_attn_s0/attn_v2_final.pt |
| attn_desp | attn/91 | /tmp/rl_c6_attn_s7/attn_desp_final.pt |
| lstm zero-hidden BC (superseded) | lstmattn/91 | /tmp/rl_p5_c1/student_e2lstm.pt |
| lstmattn sequence-BC (Phase 7 init) | lstmattn/91 | /tmp/rl_p5_c1/student_e2lstm_seq.pt |
| exploiter vs e0_champ | e0/38 | /tmp/rl_exploit_e0_s0/net.pt |

`net.pt` inside a league dir is the live (latest) net of that lane;
`pool/ck_N.pt` are the self-play snapshot opponents (restoring them
plus `trained.txt` lets a league lane resume mid-run).

## Datasets

- `rl_p5_c1/train_e2.ndjson.gz` — 600 episodes / 118,877 examples,
  E2 encoding (cdim 91), D1 teacher. BC source for attn/lstmattn.
- `rl_p5_c1/train_v3.ndjson.gz` — E0 encoding (cdim 38), D1 teacher,
  v3 instruments. BC source for e0_bc.

## Curves / metrics

- `rl_elo/matches.tsv` — Phase 6 tournament win matrix
  (`python3 rl/elo_fit.py` reproduces the leaderboard).
- per-lane `curve.txt` (probe/Elo checkpoints), `train.csv` (per-update
  rows), `trained.txt` (episode counter for resume).
- `rl_p5_c1/imitate_*.csv` — BC training logs per arch.

## Not included (and why)

- XMage build tree (/home/user/mage) — rebuilt from pin + mirrors.
- DAgger/aggregate/legacy-v2 datasets (train.ndjson, train_v3_agg*.
  ndjson, train_dagger1.ndjson) — lines of inquiry that were closed
  (C3 verdict: capacity, not covariate shift; v2 encoding obsolete).
- Superseded lane dirs (C2 v2-era, M3 per-config nets) — headline
  numbers live in the PHASE5-*.md docs.
