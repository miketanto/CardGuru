#!/bin/bash
# Swap in rl/record_census.sh.new atomically, only when no census recording is executing.
# A script file so that its own argv ("bash rl/swap_rc.sh") cannot match the pgrep pattern.
cd /home/user/CardGuru || exit 1
F=rl/record_$(echo census).sh
M=$(pgrep -fa 'record_censu[s]')
if [ -n "$M" ]; then
    echo "SWAPRC|busy|$M" | cut -c1-200
    exit 1
fi
sed -i 's/\r$//' $F.new && bash -n $F.new && chmod +x $F.new && mv $F.new $F \
    && echo "SWAPRC|swapped|$(date -u +%FT%TZ)|transcripts_lines=$(grep -c transcripts.txt $F)"
