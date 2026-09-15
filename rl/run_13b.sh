#!/bin/bash
# Phase 13b pipeline (rl/PHASE13-BC.md 13b), one model-holding process at a time, resumable per step
# (a step whose output exists is skipped). Needs the 13a recording finished and drivers 7911/7912 stopped.
#   bash rl/run_13b.sh            (KINDS env: decision kinds to clone, default all four)
#  1. BC      rl/v7_bc.py --init rl/artifacts/v7/13/init_on_s13.pt (fresh P10INIT, --cand-refers-pool, seed 13),
#             v7_bc.py defaults (lr 1e-4, batch 32, patience 3, <= 20 epochs, seed 0, 10 % of games held out)
#             -> rl/artifacts/v7/13/bc/bc.pt (gitignored), bc.log
#  2. swap    rl/p10_cardswap.py --ckpt FRESH=init --ckpt BC=bc.pt on the 10/A2 consult sets -> 13/bc/cardswap/
#  3. census  CP7 reference = rl/dimir_census.py over the recording (teacher labels) -> 13/bc/census_cp7ref*;
#             bc.pt = rl/record_census.sh bc.pt BenchDimir cp7 25 p13_bc 13700 (argmax-classes play,
#             transcripts kept; the same seed as the 13c per-block checks) -> 13/bc/census_bc.txt
#  4. levels  rl/run_13_levels.sh bc.pt bc (sampled, two-stage, argmax-classes; CP7 100 + heuristic 50)
# Lines: B13|<step>|... ; log: launch with > rl/artifacts/v7/13/bc/run_13b.log
[ -f ~/.profile ] && . ~/.profile
set -u
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
RL=/home/user/CardGuru/rl
A=$LB/rl/artifacts/v7
O=$A/13/bc
INIT=$A/13/init_on_s13.pt
KINDS=${KINDS:-prio,target,attack,block}
mkdir -p $O
cd /home/user/CardGuru
echo "B13|start|$(date -u +%FT%TZ)|kinds=$KINDS"

if [ -s $O/bc.pt ]; then echo "B13|bc|skip"; else
    python3 $RL/v7_bc.py --init $INIT --out $O/bc.pt --device cuda --kinds $KINDS $A/13/rec/rec13_*.jsonl > $O/bc.log 2>&1
    echo "B13|bc|rc=$?|$(grep '^BC|saved' $O/bc.log | cut -c1-200)"
    grep '^BC|best|\|^BC|ceiling|held' $O/bc.log | sed 's/^/B13|bc|/'
fi

if [ -s $O/cardswap/cardswap_summary.txt ]; then echo "B13|swap|skip"; else
    mkdir -p $O/cardswap
    python3 $RL/p10_cardswap.py --out $O/cardswap --ckpt FRESH=$INIT --ckpt BC=$O/bc.pt \
        "$A/wire3a/7c_W0Base_*.jsonl" "$A/wire3a/7c_BenchDimir_*.jsonl" > $O/cardswap/run.log 2>&1
    echo "B13|swap|rc=$?"
fi

if [ -s $O/census_cp7ref.txt ]; then echo "B13|cp7ref|skip"; else
    python3 $RL/dimir_census.py "CP7=$(ls $A/13/rec/rec13_*.jsonl | paste -sd,)" --out $O/census_cp7ref > $O/census_cp7ref.txt 2>&1
    echo "B13|cp7ref|rc=$?|lines=$(grep -c '^DC|' $O/census_cp7ref.txt)"
fi

if [ -s $O/census_bc.txt ]; then echo "B13|census|skip"; else
    bash $RL/record_census.sh $O/bc.pt BenchDimir cp7 25 p13_bc 13700 > $O/census_bc.txt 2>&1
    echo "B13|census|$(grep '^CENSUSREC|p13_bc' $O/census_bc.txt | grep -o 'rc=[0-9]*\|games=[0-9]*\|wins=[0-9]*\|losses=[0-9]*' | paste -sd' ')"
fi

bash $RL/run_13_levels.sh $O/bc.pt bc 2>&1 | sed 's/^/B13|levels|/'
echo "B13|done|$(date -u +%FT%TZ)"
