#!/bin/bash
# 3b evidence on the v7 driver (7911), 5 episodes each:
#   PICK=1  first non-pass candidate (lands, mana abilities, first spell/attack/block)
#   PICK=99 last candidate (the largest attack subset / block assignment,
#           the last playable) - what puts damage and blocks on the board
# plus a v6-arm control recording on 7910.
[ -f ~/.profile ] && . ~/.profile
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
for D in W0Base W1Fly W4Inst W5Trick B1Fast W1Vig; do
    DECK=$D PICK=1 bash $LB/rl/wire_record.sh v7b_$D 7782 7 7911 5 | head -1
done
for D in W0Base B1Fast W5Trick W3Sorc; do
    DECK=$D PICK=99 bash $LB/rl/wire_record.sh v7c_$D 7782 7 7911 5 | head -1
done
bash $LB/rl/wire_record.sh v6_new3 7777 6 7910 3 | head -1
