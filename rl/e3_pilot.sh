#!/bin/bash
# E3 pilot: 512-episode FROM-SCRATCH self-play lane on the E3 encoder,
# then the ablation battery that asks whether the new dims are read.
#
# Encoder: sdim 29 (E2's 24 + the four known-top dims + hand diff),
# cdim 123 = 22 + (68 mechanical + 32 text) + 1 unknown flag. The pip
# dims ride in candidate slots 17-21, which were already allocated.
#
# Fast path (PHASE9-PERF.md): persistent driver JVM, rl.concurrency=4
# for training, eval probes strictly sequential. rl-vs-rl needs
# per-worker policy connections (--threads) and NO playableCache.
#
# Usage: bash rl/e3_pilot.sh [budget=512] [seed=0]
set -u
BUDGET=${1:-512}
SEED=${2:-0}
ARCH=lstmattn
CG=/home/user/CardGuru
FEATS=$CG/rl/e3_features.tsv
SDIM=29
CDIM=123
APORT=7941
OPORT=7942
DPORT=7940
DECK=BenchDimir.dck
OUT=/tmp/rl_e3_s${SEED}
LRVAL=${E3_LR:-1e-4}
mkdir -p $OUT/pool

# from scratch: materialize the random-init net so the first chunk has a
# self-play opponent (the p7 lane gets this for free from its init ckpt)
if [ ! -f $OUT/net.pt ]; then
    python3 - "$OUT/net.pt" $SDIM $CDIM $ARCH $SEED <<'PY' || exit 1
import sys, torch
sys.path.insert(0, "/home/user/CardGuru/rl")
import policy_server as ps
path, sdim, cdim, arch, seed = sys.argv[1], int(sys.argv[2]), \
    int(sys.argv[3]), sys.argv[4], int(sys.argv[5])
torch.manual_seed(seed)
net = ps.build_net(arch, sdim, cdim)
torch.save({"net": net.state_dict(),
            "opt": torch.optim.Adam(net.parameters()).state_dict(),
            "episodes": 0, "updates": 0, "arch": arch}, path)
print("random-init net ->", path,
      sum(p.numel() for p in net.parameters()), "params")
PY
fi

start_policy() {   # $1 ckpt $2 port $3 log [$4 extra]
    rm -f $3
    python3 $CG/rl/policy_server.py --port $2 --ckpt "$1" --seed $SEED \
        --sdim $SDIM --cdim $CDIM --arch $ARCH ${4:-} > $3 2>&1 &
    echo $! > $OUT/.srvpid
    SECONDS=0
    while [ $SECONDS -lt 120 ]; do
        grep -q "policy server" $3 2>/dev/null && return 0
        grep -q "Traceback" $3 2>/dev/null && { cat $3; exit 1; }
        sleep 1
    done
    echo "E3_FAILED|policy server never started ($3)"; cat $3; exit 1
}

stop_policy() { kill $1 2>/dev/null; wait $1 2>/dev/null; }

probe() {   # $1 tag $2 opponent $3 games -> win_rate
    start_policy $OUT/net.pt $APORT $OUT/aserver.log
    local ASRV=$(cat $OUT/.srvpid)
    RL_PERSIST=1 RL_DRIVER_PORT=$DPORT RL_AUTOSTART=1 \
    bash $CG/rl/run_driver.sh \
        -Drl.episodes=$3 \
        -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
        -Drl.cardFeatures=$FEATS -Drl.e3=on \
        -Drl.opponent=$2 -Drl.searchPlies=1 -Drl.searchBreadth=8 \
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=$DECK -Drl.stopTurn=80 \
        -Drl.mode=eval -Drl.seed=950000 -Drl.report=0 \
        -Drl.out=$OUT/probe_$1.txt > /dev/null 2>&1
    stop_policy $ASRV
    grep -o 'win_rate=[0-9.]*' $OUT/probe_$1.txt | head -1 | cut -d= -f2
}

rate() {   # $1 trained
    local d0=$(probe d0_$1 heuristic 100)
    local d1=$(probe d1_$1 search 100)
    echo "E3PILOT|trained=$1|d0=$d0|d1=$d1" | tee -a $OUT/curve.txt
}

# the driver server pins CAND_DIM and the feature file at its FIRST job,
# so the lane owns its own server on its own port
bash $CG/rl/driver_server.sh stop $DPORT > /dev/null 2>&1
bash $CG/rl/driver_server.sh start $DPORT \
    "-Dmage.randomPerThread=true -XX:+UseParallelGC" || exit 1

while true; do
    trained=$(cat $OUT/trained.txt 2>/dev/null || echo 0)
    [ "$trained" -ge "$BUDGET" ] && break

    # snapshots every 128 (opponent pool); rated probes only every 256 -
    # a 100g probe pair costs ~6 min sequential and the pilot is 512 eps
    if [ $((trained % 128)) -eq 0 ] && [ ! -f $OUT/pool/ck_${trained}.pt ]; then
        [ -f $OUT/net.pt ] && cp $OUT/net.pt $OUT/pool/ck_${trained}.pt
        if [ "$trained" -gt 0 ] && [ $((trained % 256)) -eq 0 ]; then
            rate $trained
        fi
    fi
    # self-play against a snapshot from the pool (round-robin), exactly
    # the p7 skeleton minus PFSP - 512 episodes is too short to rate
    CHUNK=$((trained / 64))
    mapfile -t POOLCKS < <(ls $OUT/pool/*.pt 2>/dev/null | sort -V)
    OPPCK=${POOLCKS[$((CHUNK % ${#POOLCKS[@]}))]:-$OUT/net.pt}

    start_policy $OUT/net.pt $APORT $OUT/aserver.log \
        "--lr $LRVAL --log $OUT/train.csv --threads 4"
    ASRV=$(cat $OUT/.srvpid)
    start_policy "$OPPCK" $OPORT $OUT/oserver.log "--threads 4"
    OSRV=$(cat $OUT/.srvpid)
    rows_before=$(wc -l < $OUT/train.csv 2>/dev/null || echo 0)
    RL_PERSIST=1 RL_DRIVER_PORT=$DPORT RL_AUTOSTART=1 RL_CONC=4 \
    bash $CG/rl/run_driver.sh \
        -Drl.episodes=64 \
        -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
        -Drl.opponent=rl -Drl.oppPort=$OPORT \
        -Drl.cardFeatures=$FEATS -Drl.e3=on \
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=$DECK -Drl.stopTurn=80 \
        -Drl.mode=train -Drl.seed=$((70000000 + SEED*1000000 + trained)) \
        -Drl.report=0 > $OUT/last_chunk.log 2>&1
    rows_after=$(wc -l < $OUT/train.csv 2>/dev/null || echo 0)
    stop_policy $ASRV
    stop_policy $OSRV
    if [ "$rows_after" -le "$rows_before" ]; then
        echo "E3_FAILED|no_training_rows at trained=$trained"
        tail -20 $OUT/last_chunk.log
        exit 1
    fi
    trained=$((trained + 64))
    echo $trained > $OUT/trained.txt
    echo "E3|trained=$trained|opp=$(basename $OPPCK)"
done
cp $OUT/net.pt $OUT/e3_pilot_final.pt
rate $(cat $OUT/trained.txt)
bash $CG/rl/driver_server.sh stop $DPORT > /dev/null 2>&1
echo "E3_DONE|trained=$(cat $OUT/trained.txt)|net=$OUT/e3_pilot_final.pt"
