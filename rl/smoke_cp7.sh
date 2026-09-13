#!/bin/bash
# 7d piece (1b) smoke (OVERNIGHT-7D B2): 4 games of rl.agent=cp7 through the echo
# server on driver 7911 (v7 flags), then: the consults carry y, the counters print,
# wire_validate passes on the file, the 5b faithfulness probe runs on it
# (rl/v7_faith_real.py; outputs 7d1b/smoke_faith.{json,md}).
[ -f ~/.profile ] && . ~/.profile
set -u
RL=/home/user/CardGuru/rl
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
OUT=$LB/rl/artifacts/v7/7d1b
mkdir -p $OUT
python3 $RL/driver_client.py --port 7911 --ping > /dev/null 2>&1 || { echo "SMOKE|no driver on 7911"; exit 1; }
bash $RL/record_cp7.sh smoke 7783 ${EP:-4} 7300 7911
F=$OUT/smoke.jsonl
python3 - $F <<'EOF'
import json, sys, collections
f = sys.argv[1]; hello = None; ys = collections.Counter(); types = collections.Counter(); k0 = 0; n = 0
for raw in open(f, 'rb'):
    if not raw.strip(): continue
    m = json.loads(raw)
    if m.get('t') == 'hello': hello = m
    elif m.get('t') == 'consult':
        n += 1
        y = m.get('y'); ys['none' if y is None else ('neg' if y < 0 else ('pass' if y == 0 else 'act'))] += 1
        if y is not None and y >= 0: types[m['v7_cand_type'][y]] += 1
print(f"SMOKE|hello_teacher={hello.get('teacher') if hello else None}|consults={n}|y={dict(ys)}|label_types={dict(sorted(types.items()))}")
EOF
python3 $RL/wire_validate.py $F 2>&1 | tail -2 | sed 's/^/SMOKE|validate|/'
timeout 1800 python3 $RL/v7_faith_real.py $F --out $OUT/smoke_faith.json --md $OUT/smoke_faith.md 2>&1 | grep 'FAITH5B' | tail -8 | sed 's/^/SMOKE|faith|/'
echo "SMOKE|done=$(date -u +%FT%TZ)"
