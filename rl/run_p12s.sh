#!/bin/bash
# Phase 12 Amendment 4 side job: SAMPLED levels (rl/battery_p12s.sh, frozen server 7949, driver 7914)
# of the three M_D level snapshots, one evaluation at a time: CP7 100 then heuristic 50 per point
# (each row seed 930000 = the argmax level's seed). Resumable (a finished row's probe file is kept).
# Log: rl/artifacts/v7/12/sampled/p12s.log; lines P12S|<point>|XDECKS|...  and P12S|done.
[ -f ~/.profile ] && . ~/.profile
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
RL=/home/user/CardGuru/rl
S=$LB/rl/artifacts/v7/12/sampled
mkdir -p $S
for pt in start:$LB/rl/artifacts/v7/11/drill/pool/M_D_06400.pt p1024:$LB/rl/artifacts/v7/12/pool/M_D_07424.pt p2048:$LB/rl/artifacts/v7/12/pool/M_D_08448.pt p3072:$LB/rl/artifacts/v7/12/pool/M_D_09472.pt p4096:$LB/rl/artifacts/v7/12/pool/M_D_10496.pt p5120:$LB/rl/artifacts/v7/12/pool/M_D_11520.pt; do
    name=${pt%%:*}; ck=${pt#*:}
    [ -s "$ck" ] || { echo "P12S|$name|missing $ck"; continue; }
    G=100 ROWS="cp7:BenchDimir" bash $RL/battery_p12s.sh "$ck" BenchDimir $S/${name}_cp7 2>&1 | grep '^XDECKS' | grep -v done | sed "s/^/P12S|$name|/"
    G=50 ROWS="heuristic:BenchDimir" bash $RL/battery_p12s.sh "$ck" BenchDimir $S/${name}_heur 2>&1 | grep '^XDECKS' | grep -v done | sed "s/^/P12S|$name|/"
done
echo "P12S|done|$(date -u +%FT%TZ)"
