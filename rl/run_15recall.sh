#!/bin/bash
# Phase 15 A4L: record EVERY ladder deck, one deck at a time, engine only.
#   bash rl/run_15recall.sh [games per deck, default 1000]
# This is the ENGINE half of A4L and holds no GPU and no policy server, so it is
# meant to run BESIDE the GPU rungs (A1 / A2 / the ladder's clone steps) within the
# box rule: two driver JVMs + one GPU trainer. It records and gates only; every
# clone and every evaluation is left to rl/run_15a4.sh, which then skips the
# recording steps because each deck's DONE file is already there.
# RESUMABLE and IDEMPOTENT at deck AND job granularity (run_15rec.sh skips a job
# whose REC15| line is in the deck's counts.txt; a deck with DONE is skipped whole).
# Stop: touch rl/artifacts/v7/15/rec/STOPALL (checked between decks), or
# rl/stop_15rec.sh to stop immediately (the current 50-game job is lost, nothing else).
# Seeds match rl/run_15a4.sh's per-rung formula so the file tags agree.
[ -f ~/.profile ] && . ~/.profile
set -u
RL=/home/user/CardGuru/rl
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
A=$LB/rl/artifacts/v7/15/rec
G=${1:-1000}
mkdir -p $A
cd /home/user/CardGuru

# same order and indices as run_15a4.sh's RUNGS (white), then the black branch
DECKS=(W0Base W1Fly W1Fst W1Vig W1Lif W1Ctrl W2FlyLif W2Ctrl W3Sorc W4Inst W5Trick \
       B1Narrow B2Mid B3Open B1Fast B4Card)
echo "RECALL|start=$(date -u +%FT%TZ)|decks=${#DECKS[@]}|games=$G"
for i in "${!DECKS[@]}"; do
    D=${DECKS[$i]}
    [ -f $A/STOPALL ] && { echo "RECALL|stopall"; break; }
    if [ ! -f $RL/$D.dck ]; then echo "RECALL|$D|no deck file - skipped"; continue; fi
    if [ -f $A/$D/DONE ]; then echo "RECALL|$D|skip (DONE)"; else
        SEED=$((15000 + i * 1000))
        echo "RECALL|$D|record|seed=$SEED|$(date -u +%FT%TZ)"
        bash $RL/run_15rec.sh $D $G $SEED 2>&1 | grep '^RUN15REC|' | tail -3
    fi
    bash $RL/gate_15rec.sh $D 2>&1 | grep '^REC15GATE|' | cut -c1-320
    echo "RECALL|$D|done=$(date -u +%FT%TZ)"
done
# leave no driver JVM behind: the GPU rungs want the RAM
for p in 7911 7912; do bash $RL/driver_server.sh stop $p > /dev/null 2>&1; done
echo "RECALL|done=$(date -u +%FT%TZ)"
