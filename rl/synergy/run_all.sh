#!/usr/bin/env bash
# Rebuild everything from the Forge checkout (fetch_forge.sh does the fetch
# and the parse; this does signals -> graph -> report). ~30 s.
set -euo pipefail
export PYTHONHASHSEED=0  # set/partition iteration order feeds Louvain and tie-breaks
cd "$(dirname "$(readlink -f "$0")")"
FORGE=${FORGE:-/home/user/forge}
python3 tally.py fra_parsed.json TALLIES.md tallies.json > /dev/null
python3 signals.py fra_parsed.json "$FORGE/forge-gui/res/tokenscripts" fra_signals.json > /dev/null
python3 graph.py fra_signals.json
python3 evaluate.py > /dev/null
echo "report: GRAPH-REPORT.md  metrics: eval.json"
