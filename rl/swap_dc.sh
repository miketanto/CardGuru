#!/bin/bash
# Swap in rl/dimir_census.py.new atomically, only when no census recording is executing
# (rl/record_census.sh runs the census tool at the end of each recording).
# A script file so that its own argv ("bash rl/swap_dc.sh") cannot match the pgrep pattern.
cd /home/user/CardGuru || exit 1
F=rl/dimir_$(echo census).py
M=$(pgrep -fa 'record_censu[s]|dimir_censu[s]')
if [ -n "$M" ]; then
    echo "SWAPDC|busy|$M" | cut -c1-200
    exit 1
fi
sed -i 's/\r$//' $F.new && python3 -m py_compile $F.new && mv $F.new $F \
    && echo "SWAPDC|swapped|$(date -u +%FT%TZ)|blight_lines=$(grep -c rh_blight $F)"
