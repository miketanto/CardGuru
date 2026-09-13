#!/bin/bash
# 7d correction follow-up: re-battery the C1 checkpoints under the FIXED
# argmax-classes protocol (paired game seeds with the lane's plain-argmax
# batteries) via rl/battery_ck.sh. Server 7947 (cuda, inference), driver 7913 -
# never the lanes' 7910/7912 or the recording driver 7911. Order: s0 2048, s1 2048
# (the Q1 endpoints), then 512/1024/1536 of both seeds from /tmp. Resumable
# (battery_ck.sh skips probes that exist). Output rl/artifacts/v7/7c1/rebattery/s<seed>/.
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
RL=/home/user/CardGuru/rl
ART=/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7c1/rebattery
mkdir -p $ART/s0 $ART/s1
echo "REBAT|start=$(date -u +%FT%TZ)"
one() {   # $1 seed $2 tr $3 ckpt
    [ -s "$3" ] || { echo "REBAT|missing|$3"; return; }
    if [ -s $ART/s$1/probe_TWIN_$2.txt ] && grep -q "trained=$2|" $ART/s$1/rows.txt 2>/dev/null; then echo "REBAT|skip|s$1|$2"; return; fi
    line=$(bash $RL/battery_ck.sh "$3" $ART/s$1 $2 7947 7913 | grep '^R0|')
    echo "s$1 $line" | tee -a $ART/s$1/rows.txt
}
one 0 2048 /mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7c1/s0/ck_2048.pt
one 1 2048 /mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7c1/s1/ck_2048.pt
for tr in 512 1024 1536; do
    one 0 $tr /tmp/rl_7c1_s0/ck_$tr.pt
    one 1 $tr /tmp/rl_7c1_s1/ck_$tr.pt
done
bash $RL/driver_server.sh stop 7913 > /dev/null 2>&1
echo "REBAT|done=$(date -u +%FT%TZ)"
