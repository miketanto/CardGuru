22:23:06 START a :: --struct tree --tree --piece-dropout 0.2 --fuse blocks --aux 1.0 --distill 10 --lr-text 2e-5 --llrd 0.85 --warmup 0.10 --epochs 40 --batch 256
22:46:56 a seed 0 exit 0
23:10:37 a seed 1 exit 0
23:34:27 a seed 2 exit 0
23:58:09 a seed 3 exit 0
averaged 2 seeds -> rl/artifacts/cardemb_sweep/a/emb.pt (35478, 128)
averaged 2 seeds -> rl/artifacts/cardemb_sweep/a/emb_seed1.pt (35478, 128)

## a  (2026-09-10 23:58)

flags: `--struct tree --tree --piece-dropout 0.2 --fuse blocks --aux 1.0 --distill 10 --lr-text 2e-5 --llrd 0.85 --warmup 0.10 --epochs 40 --batch 256`

### gates (artifact = mean of seeds 0+1; G3 vs mean of seeds 2+3)

| gate | threshold | measured (held-out) | train | result |
|---|---|---|---|---|
| G1 mv probe acc | ≥ 0.9 | 0.993 | 0.999 | pass |
| G1 power probe acc | ≥ 0.9 | 0.997 | 1.000 | pass |
| G1 toughness probe acc | ≥ 0.9 | 0.994 | 1.000 | pass |
| G1 colours (5 probes, acc) | each ≥ 0.97 | min 1.000 (color_W) | min 1.000 | pass |
| G1 types (6 probes, acc) | each ≥ 0.97 | min 1.000 (type_Creature) | min 1.000 | pass (3 skipped: too few positives) |
| G1 keywords (11 probes, f1) | each ≥ 0.8 | min 0.817 (kw_first_strike) | min 0.859 | pass (7 skipped: too few positives) |
| G1 answer classes (5 probes, f1) | each ≥ 0.8 | min 0.725 (ans_minus_toughness) | min 0.751 | **FAIL** (4 skipped: too few positives) |
| G2 Cancel / Counterspell cos | ≥ 0.85 | 0.983 | | pass |
| G2 Spell Snare / Force Spike (rank-based, v4+) | Spike ∉ Snare top-10 | rank 28, cos 0.911 | | pass |
| (info) Snare/Spike cos margin, old bar | ≤ 0.833 | 0.911 | | would fail |
| G2 functional reprints in top-3 | all 10 | 10 / 10 | | pass |
| G2 P8 swap pairs (rank-based, v3+) | ≥ 14/16 pairs with both directed ranks ≤ 500; median rank ≤ 50 | 16/16, median 29 | | pass |
| (info) swap pairs cos, old μ+kσ bar | min ≥ 0.703, mean ≥ 0.880 | min 0.779, mean 0.863 (random μ 0.525 σ 0.089) | | would fail |
| G3 seed 0 vs 1 top-10 Jaccard | ≥ 0.4, same G2 verdicts | 0.680, identical: True | | pass |
| **a overall** | all of the above | | | **FAIL** |

### per-slice seed overlap (artifact vs artifact)
```
whole            0.680
slice text      0.734
slice tree      0.475
slice bag       0.796
slice printed   0.872
without text     0.524
without tree     0.695
without bag      0.674
without printed  0.696
```
### raw single seeds 0 vs 1 (for reference)
```
whole            0.623
```
    rl/artifacts/cardemb_sweep/a/train_seed0.log:22:46:32 epoch=40/40 train_loss=0.2062 (infonce=0.0338 distill=0.0012 aux=0.1602) train_r@1=0.947 train_r@10=0.998 held_loss=0.3725 held_r@1=0.928 held_r@1
    rl/artifacts/cardemb_sweep/a/train_seed1.log:23:10:13 epoch=40/40 train_loss=0.2057 (infonce=0.0339 distill=0.0012 aux=0.1596) train_r@1=0.952 train_r@10=0.998 held_loss=0.3690 held_r@1=0.929 held_r@1
    rl/artifacts/cardemb_sweep/a/train_seed2.log:23:34:03 epoch=40/40 train_loss=0.2060 (infonce=0.0345 distill=0.0012 aux=0.1593) train_r@1=0.948 train_r@10=0.997 held_loss=0.3755 held_r@1=0.928 held_r@1
    rl/artifacts/cardemb_sweep/a/train_seed3.log:23:57:45 epoch=40/40 train_loss=0.2062 (infonce=0.0333 distill=0.0012 aux=0.1608) train_r@1=0.958 train_r@10=0.998 held_loss=0.3815 held_r@1=0.924 held_r@1
23:59:39 DONE a
23:59:39 START b :: --struct script --fuse blocks --aux 1.0 --distill 10 --lr-text 2e-5 --llrd 0.85 --warmup 0.10 --epochs 40 --batch 256
02:03:56 b seed 0 exit 0
04:05:33 b seed 1 exit 0
06:10:13 b seed 2 exit 0
