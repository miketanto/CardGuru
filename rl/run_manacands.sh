#!/bin/bash
# 7a amendment: v6-identity recordings for the rl.manaCands filter (RLPlayer.priority).
# Echo policy PREFER=1 (play the first land drop, else PASS): lands get played so
# mana abilities are offered, none is ever chosen, and ON (-Drl.manaCands=true,
# old set, recorded twice = the run-to-run residual control) and OFF (default)
# follow the same trajectory. Then rl/wire_check_3b.py and rl/manacands_check.py.
# Driver 7911 (v7) must be on the compiled build (bash rl/drivers_3a.sh).
[ -f ~/.profile ] && . ~/.profile
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
OUT=$LB/rl/artifacts/v7/manacands
W=$LB/rl/artifacts/v7/wire3a
EP=${EP:-4}
mkdir -p $OUT
{
for D in W0Base BenchDimir B1Fast; do
    DECK=$D PICK=0 PREFER=1 EXTRA="-Drl.manaCands=true" bash $LB/rl/wire_record.sh mcL_on_$D 7783 7 7911 $EP
    DECK=$D PICK=0 PREFER=1 EXTRA="-Drl.manaCands=true" bash $LB/rl/wire_record.sh mcL_on2_$D 7783 7 7911 $EP
    DECK=$D PICK=0 PREFER=1 bash $LB/rl/wire_record.sh mcL_off_$D 7783 7 7911 $EP
done
cd $LB
python3 rl/wire_check_3b.py $W/mcL_on_*.jsonl $W/mcL_off_*.jsonl $W/mc_p1_off_W0Base.jsonl > $OUT/check3b.txt 2>&1
echo "CHECK3B rc=$?"; grep -i 'disagree\|fail\|identity' $OUT/check3b.txt | tail -4
for D in W0Base BenchDimir B1Fast; do
    python3 rl/manacands_check.py $W/mcL_on_$D.jsonl $W/mcL_on2_$D.jsonl $W/mcL_off_$D.jsonl $W/mcL_off_$D.probe.txt
    echo "MCCHECK $D rc=$?"
done
for T in mcL_on_W0Base mcL_off_W0Base mc_p1_off_W0Base mcL_on_BenchDimir mcL_off_BenchDimir mcL_on_B1Fast mcL_off_B1Fast; do
    echo "TYPES $T $(python3 rl/manacands_types.py $W/$T.jsonl)"
done
echo DONE
} > $OUT/run.log 2>&1
