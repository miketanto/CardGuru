#!/bin/bash
# Auto-answer dead windows during opponent phases: pass unless the request is
# non-priority kind OR their battlefield gained a nonland permanent OR it's our
# active turn main/attack window. Runs until one of those appears, then exits
# printing the seq that needs the pilot.
cd /tmp/claude-501/llm-esc5
while true; do
  next=$(ls req-*.json 2>/dev/null | sed 's/req-//;s/.json//' | sort -n | while read n; do
    [ -f "resp-$n.json" ] || { echo "$n"; break; }; done)
  [ -z "$next" ] && { [ -f DONE ] && { echo "DONE"; exit 0; }; sleep 1; continue; }
  verdict=$(python3 - "$next" << 'PYEOF'
import json, sys
n = sys.argv[1]
d = json.load(open(f"req-{n}.json"))
r = d['request']
kind = r.get('kind'); phase = r.get('phase'); active = r.get('active')
b = r['state'].get('B', {})
creatures = [c for c in b.get('battlefield', []) if '[Land]' not in str(c.get('types', '')) and 'Forest' not in c.get('name','')]
if kind != 'priority':
    print('ESCALATE'); raise SystemExit
if active == 'B' and not creatures:
    print('PASS'); raise SystemExit
if phase in ('End Turn', 'End Combat', 'Combat Damage', 'Upkeep', 'Draw', 'Begin Combat', 'Declare Blockers', 'Declare Attackers') and not creatures:
    print('PASS'); raise SystemExit
print('ESCALATE')
PYEOF
)
  if [ "$verdict" = "PASS" ]; then
    printf '%s' '{"choice": 0, "why": "Relay auto-pass (standing policy): dead window, no enemy creatures."}' > "resp-$next.json.tmp"
    mv "resp-$next.json.tmp" "resp-$next.json"
  else
    echo "NEEDS_PILOT seq=$next"
    exit 0
  fi
done
