#!/bin/bash
# Phase 12 Amendment 5: the TWO-STAGE argmax levels of the six M_D level snapshots, run after the
# sampled battery (Amendment 4) finishes: rl/battery_xdeck.sh unchanged with
# SRVEXTRA="--device cuda --logit-bound 5 --argmax-classes --argmax-two-stage" (two-stage wins on
# the eval branch), eval mode, the level seeds (row seed 930000), ports 7949 / 7914, CP7 100 then
# heuristic 50 per point, one evaluation at a time (box rule: at most one model-holding job).
# Then the CPU readouts (rl/p12_readout.py) on the recorded censuses n=8 (owed), 11, 15, 19, 20.
# Resumable (a finished row's probe file is skipped). Log: rl/artifacts/v7/12/twostage/p12t.log.
[ -f ~/.profile ] && . ~/.profile
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
RL=/home/user/CardGuru/rl
A=$LB/rl/artifacts/v7
S=$A/12/sampled
T=$A/12/twostage
mkdir -p $T
until grep -q 'P12S|done' $S/p12s.log 2>/dev/null; do sleep 60; done
until ! pgrep -f 'policy_serve[r].py --port 7949' > /dev/null; do sleep 30; done
echo "# run_p12t start $(date -u +%FT%TZ)"
X="--device cuda --logit-bound 5 --argmax-classes --argmax-two-stage"
for pt in start:$A/11/drill/pool/M_D_06400.pt p1024:$A/12/pool/M_D_07424.pt p2048:$A/12/pool/M_D_08448.pt p3072:$A/12/pool/M_D_09472.pt p4096:$A/12/pool/M_D_10496.pt p5120:$A/12/pool/M_D_11520.pt; do
    name=${pt%%:*}; ck=${pt#*:}
    [ -s "$ck" ] || { echo "P12T|$name|missing $ck"; continue; }
    SRVEXTRA="$X" G=100 ROWS="cp7:BenchDimir" bash $RL/battery_xdeck.sh "$ck" BenchDimir $T/${name}_cp7 7949 7914 2>&1 | grep '^XDECK|ck' | sed "s/^/P12T|$name|/"
    SRVEXTRA="$X" G=50 ROWS="heuristic:BenchDimir" bash $RL/battery_xdeck.sh "$ck" BenchDimir $T/${name}_heur 7949 7914 2>&1 | grep '^XDECK|ck' | sed "s/^/P12T|$name|/"
done
echo "P12T|batteries_done|$(date -u +%FT%TZ)"
cd /home/user/CardGuru
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 python3 rl/p12_readout.py \
    n008=$A/12/pool/M_D_08704.pt=$A/11/rec_p12_M_D_n008_t08704.jsonl \
    n011=$A/12/pool/M_D_09472.pt=$A/11/rec_p12_M_D_n011_t09472.jsonl \
    n015=$A/12/pool/M_D_10496.pt=$A/11/rec_p12_M_D_n015_t10496.jsonl \
    n019=$A/12/pool/M_D_11520.pt=$A/11/rec_p12_M_D_n019_t11520.jsonl \
    n020=$A/12/pool/M_D_11776.pt=$A/11/rec_p12_M_D_n020_t11776.jsonl 2>&1 | grep '^READOUT' | tee -a $A/12/sampled/readout.txt | sed 's/^/P12T|/'
echo "P12T|done|$(date -u +%FT%TZ)"
