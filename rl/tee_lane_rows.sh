#!/bin/bash
# Mirror the R0| / R0_ / R0_OPP| rows of WSL-local lane logs into one file on /mnt/c so
# a Windows-side Monitor can tail them.  bash rl/tee_lane_rows.sh <out on /mnt/c> <lane.log>...
# tail -F copes with files that do not exist yet (the lane creates them later).
OUT=$1; shift
tail -n +1 -F "$@" 2>/dev/null | grep --line-buffered '^R0\|==> ' >> "$OUT"
