#!/bin/bash
# Phase 10 A2 (rl/PHASE10-LEAGUE.md): the Phase 9 P1 card-swap probe on a fresh
# untrained net with --cand-refers-pool OFF vs ON, W0Base + Dimir consult sets.
# OFF = rl/artifacts/v7/9/init.pt (P10INIT seed 10, the Phase 9 init subject);
# ON  = the SAME trunk + the new cand_ref/opp_act_ref (default init, loaded strict=False),
#       saved as rl/artifacts/v7/10/a2/init_on.pt (gitignored .pt).
# The probe is a frozen COPY of rl/probes/cardswap.py (rl/p10_cardswap.py) so the
# Phase 9 agent's file is never touched.  Gate: ON's mean dp on text-only swaps
# >= 0.01 AND >= 10x OFF's.  Usage: bash rl/p10_a2.sh [tag]   (tag names the out dir)
cd /home/user/CardGuru || exit 1
A=rl/artifacts/v7
TAG=${1:-a2}
OUT=$A/10/$TAG
mkdir -p $OUT
[ -s rl/p10_cardswap.py ] || cp rl/probes/cardswap.py rl/p10_cardswap.py
python3 - <<EOF
import sys; sys.path.insert(0, "rl")
import torch, v7_policy as P
net = P.V7Policy.load("$A/9/init.pt", cand_refers_pool=True)
net.save("$OUT/init_on.pt", episodes=0)
w = net.build.cand_ref.weight
print("A2|init_on|cand_ref_w_absmean=%.5f|config=%s" % (w.abs().mean().item(), net.config))
EOF
python3 rl/p10_cardswap.py --out $OUT --ckpt OFF=$A/9/init.pt --ckpt ON=$OUT/init_on.pt \
  "$A/wire3a/7c_W0Base_*.jsonl" "$A/wire3a/7c_BenchDimir_*.jsonl" > $OUT/a2_run.log 2>&1
echo "A2|rc=$?|out=$OUT"
grep -h 'text\|self_mana' $OUT/cardswap_summary.txt 2>/dev/null | head -20
