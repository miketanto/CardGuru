#!/bin/bash
# Phase 14 D2b (rl/PHASE14-DIAG.md): 1,024 episodes of the Phase 13 recipe from bc.pt against CP7
# at ONE skill (SKILL, the D2a rung), no heuristic blocks, in 256-episode blocks, then 100-game
# sampled and two-stage levels vs CP7 at that skill.
#   SKILL=<n> bash rl/run_14d2b.sh
# Recipe = rl/league11.py SRVEXTRA (lr 3e-5, 1 epoch, logit bound 5, AdamW wd 0.01 on heads,
# --adv-norm batch, --target-kl 0.02, --argmax-classes, --cand-refers-pool), exactly as phase13.py
# passed it; lane rl/rung0_lane_league.sh on ports 7950 / 7960 / 7912, lane seed 41.
# Resumable: the lane resumes from $OUT/agent.pt (episodes counter), finished blocks are skipped,
# and a level row whose probe file exists is not replayed.
# Output: rl/artifacts/v7/14/d2b/run.log (D2B| lines), lane log /tmp/rl_14_d2b/lane.log.
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
SKILL=${SKILL:?set SKILL to the D2a rung}
RL=/home/user/CardGuru/rl
OUT=/tmp/rl_14_d2b
ART=$RL/artifacts/v7/14/d2b
BC=$RL/artifacts/v7/13/bc/bc.pt
SEED=41
mkdir -p $OUT $ART
L=$ART/run.log
say() { echo "D2B|$*" | tee -a $L; }
say "start|$(date -u +%FT%TZ)|skill=$SKILL|seed=$SEED|out=$OUT"

# agent.pt from bc.pt (a BC checkpoint carries opt=None; phase13.ensure_agent pops it so the lane resumes)
if [ ! -s $OUT/agent.pt ]; then
    python3 - "$BC" "$OUT/agent.pt" <<'PY'
import sys, torch
c = torch.load(sys.argv[1], map_location="cpu", weights_only=False)
if "opt" in c and c["opt"] is None:
    c.pop("opt")
torch.save(c, sys.argv[2] + ".tmp")
import os; os.replace(sys.argv[2] + ".tmp", sys.argv[2])
print("agent.pt episodes=%s" % c.get("episodes"))
PY
    say "agent|from=bc.pt"
fi

trained() { python3 -c "
import torch,sys
try: print(int(torch.load('$OUT/agent.pt',map_location='cpu',weights_only=False).get('episodes',0)))
except Exception: print(0)"; }

SRVEXTRA="--device cuda --epochs 1 --logit-bound 5 --weight-decay 0.01 --adv-norm batch --target-kl 0.02 --argmax-classes --cand-refers-pool"
n=0
for BUDGET in 256 512 768 1024; do
    n=$((n + 1))
    T0=$(trained)
    if [ "$T0" -ge "$BUDGET" ]; then say "block|n=$n|skip|trained=$T0"; continue; fi
    JL=$OUT/jobs.log; OFF=0; [ -f $JL ] && OFF=$(stat -c%s $JL)
    t0=$(date +%s)
    R0_ENCODER_V=7 R0_EVERY=256 R0_CHUNK=64 R0_CP7_G=0 R0_CONC=4 R0_LR=3e-5 RL_LOCK_STATS=1 \
    RL_DRIVER_PORT=7912 R0_PORT=7950 R0_OPP_PORT=7960 R0_OUT=$OUT R0_SRVEXTRA="$SRVEXTRA" \
    R0_OPP_SPEC="cp7::BenchDimir.dck" R0_CP7_SKILL=$SKILL R0_ROWS=none R0_ROWS_FINAL=none \
    R0_EVAL_G=100 R0_INIT=$BC \
        bash $RL/rung0_lane_league.sh BenchDimir BenchDimir $BUDGET $SEED >> $OUT/lane.log 2>&1
    rc=$?
    T1=$(trained)
    read W LO D S N <<< $(tail -c +$((OFF + 1)) $JL 2>/dev/null | awk -F'|' '/^RL\|summary/{
        for (i=3;i<=NF;i++){split($i,a,"="); v[a[1]]=a[2]}
        w+=v["wins"]; l+=v["losses"]; d+=v["draws"]; s+=v["stalls"]; n+=v["episodes"]}
        END{printf "%d %d %d %d %d", w, l, d, s, n}')
    wr=$(python3 -c "print('%.3f' % ($W/$N)) if $N else print('NA')")
    say "block|n=$n|trained=$T0->$T1|budget=$BUDGET|opp=cp7|skill=$SKILL|W/L/D/S=$W/$LO/$D/$S|episodes=$N|wr=$wr|wall=$(( $(date +%s) - t0 ))s|rc=$rc"
    cp $OUT/agent.pt $ART/ck_$T1.pt 2>/dev/null
done
say "trained|$(trained)"

# levels at the rung skill: sampled and two-stage, 100 games, in parallel (2 servers + 2 JVMs)
pkill -f "policy_serve[r].py --port 7950" 2>/dev/null
pkill -f "policy_serve[r].py --port 7960" 2>/dev/null
bash $RL/driver_server.sh stop 7912 > /dev/null 2>&1
sleep 5
CK=$ART/ck_1024.pt; [ -s "$CK" ] || CK=$OUT/agent.pt
TWO="--device cuda --logit-bound 5 --argmax-classes --argmax-two-stage"
( SKILL=$SKILL G=100 ROWS="cp7:BenchDimir" bash $RL/battery_p14s.sh $CK BenchDimir $ART/lvl_sampled 7949 7914 >> $ART/lvl_sampled.log 2>&1 ) &
sleep 30
( SKILL=$SKILL G=100 ROWS="cp7:BenchDimir" SRVEXTRA="$TWO" bash $RL/battery_x14.sh $CK BenchDimir $ART/lvl_twostage 7947 7913 >> $ART/lvl_twostage.log 2>&1 ) &
wait
grep -h '^XDECKS|ck\|^XDECK|ck' $ART/lvl_sampled.log $ART/lvl_twostage.log >> $L
say "done|$(date -u +%FT%TZ)"
