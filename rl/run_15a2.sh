#!/bin/bash
# Phase 15 A2 (rl/PHASE15-ARCH.md): does the policy network keep card identity?
#   bash rl/run_15a2.sh
# One GPU process at a time, every step skipped when its output exists:
#   1. floor   rl/v7_bc.py from rl/artifacts/v7/15/a2/init_random.pt (V7Policy(random_table=True),
#              seed 13, cand_refers_pool) on the 13a recordings, 13b's recipe and all four
#              kinds - the CARD-BLIND clone. ~25 min.
#   2. probe1  rl/p15_a2.py on the 13a recordings: entity tokens of the cards in the seat's
#              own hand, linear probe to the 68 e2_features columns + 5 colour bits (the
#              score) and mv / power / toughness (R^2, reported), for BC and RAND, each
#              beside the frozen-embedding ceiling computed on the same entities and split.
#   3. probe3  the same probe on a ladder-deck recording (W0Base): those cards never appear
#              in BenchDimir, which is the "unseen cards" population the 13a recordings
#              cannot supply on their own. Needs rl/artifacts/v7/15/rec/W0Base to exist.
#   4. probe2  rl/p10_cardswap.py UNCHANGED on the 10/A2 consult sets: FRESH (13b's init),
#              BC and RAND, so the 13b card-swap row is extended by the card-blind arm.
# Log: launch detached with > rl/artifacts/v7/15/a2/run_15a2.log
[ -f ~/.profile ] && . ~/.profile
set -u
RL=/home/user/CardGuru/rl
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
A=$LB/rl/artifacts/v7
O=$A/15/a2
REC=$A/13/rec
INIT=$A/13/init_on_s13.pt
BC=$A/13/bc/bc.pt
mkdir -p $O
cd /home/user/CardGuru
echo "A2RUN|start=$(date -u +%FT%TZ)"

if [ -s $O/bc_random.pt ]; then
    echo "A2RUN|floor|skip"
else
    python3 $RL/v7_bc.py --init $O/init_random.pt --out $O/bc_random.pt --device cuda \
        --kinds prio,target,attack,block $REC/rec13_*.jsonl > $O/bc_random.log 2>&1
    echo "A2RUN|floor|rc=$?|$(grep '^BC|saved' $O/bc_random.log | cut -c1-180)"
    grep '^BC|best|' $O/bc_random.log | sed 's/^/A2RUN|floor|/'
fi

if [ -s $O/a2_probe1.json ]; then
    echo "A2RUN|probe1|skip"
else
    python3 $RL/p15_a2.py --ckpt BC=$BC --ckpt RAND=$O/bc_random.pt --out $O --tag probe1 \
        --device cuda --baseline-names $RL/BenchDimir.dck $REC/rec13_*.jsonl > $O/probe1.log 2>&1
    echo "A2RUN|probe1|rc=$?"
    grep '^A2|' $O/probe1.log | grep -v '^A2|setup' | sed 's/^/A2RUN|probe1|/'
fi

if [ -s $O/a2_offdeck.json ]; then
    echo "A2RUN|probe3|skip"
elif ls $A/15/rec/W0Base/rec15_W0Base_*.jsonl > /dev/null 2>&1; then
    python3 $RL/p15_a2.py --ckpt BC=$BC --ckpt RAND=$O/bc_random.pt --out $O --tag offdeck \
        --device cuda --baseline-names $RL/BenchDimir.dck \
        $A/15/rec/W0Base/rec15_W0Base_*.jsonl > $O/probe3.log 2>&1
    echo "A2RUN|probe3|rc=$?"
    grep '^A2|' $O/probe3.log | grep -v '^A2|setup' | sed 's/^/A2RUN|probe3|/'
else
    echo "A2RUN|probe3|no W0Base recording yet"
fi

if [ -s $O/cardswap/cardswap_summary.txt ]; then
    echo "A2RUN|probe2|skip"
else
    mkdir -p $O/cardswap
    python3 $RL/p10_cardswap.py --out $O/cardswap --ckpt FRESH=$INIT --ckpt BC=$BC \
        --ckpt RAND=$O/bc_random.pt \
        "$A/wire3a/7c_W0Base_*.jsonl" "$A/wire3a/7c_BenchDimir_*.jsonl" > $O/cardswap/run.log 2>&1
    echo "A2RUN|probe2|rc=$?"
fi
echo "A2RUN|done=$(date -u +%FT%TZ)"
