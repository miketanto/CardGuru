#!/bin/bash
# Phase 12 Amendment 4: reschedule the sampled battery (rl/run_p12s.sh, resumable) for after the
# controller's FINAL L12|done (reason hours / all_graduated / errors, i.e. after the end phase), and
# only once no policy server is resident (box rule: lane + at most one other model-holding process).
# A stopfile L12|done does not trigger it. Log: rl/artifacts/v7/12/sampled/p12s.log.
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
L=$LB/rl/artifacts/v7/12/phase12.log
S=$LB/rl/artifacts/v7/12/sampled
until grep -q 'L12|done|reason=\(hours\|all_graduated\|errors\)' $L 2>/dev/null; do sleep 120; done
until ! pgrep -f 'policy_serve[r].py' > /dev/null; do sleep 60; done
for f in $S/*/probe_*.txt; do [ -f "$f" ] && ! grep -q 'episodes=' "$f" && rm -f "$f"; done   # a paused row's partial file
echo "# after_p12: controller done and no server resident, launching run_p12s $(date -u +%FT%TZ)" >> $S/p12s.log
bash /home/user/CardGuru/rl/run_p12s.sh >> $S/p12s.log 2>&1
