#!/bin/bash
[ -f ~/.profile ] && . ~/.profile
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
for P in 1 99; do DECK=W0Base PICK=$P bash $LB/rl/wire_record.sh 7c_W0Base_p$P 7784 7 7911 8 | head -1; done
DECK=W0Base PICK=1 PREFER=2,1 BUDGET=300 bash $LB/rl/wire_record.sh 7c_W0Base_sf 7784 7 7911 8 | head -1
echo REC_DONE
