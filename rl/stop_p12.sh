#!/bin/bash
# Graceful stop of Phase 12: the controller finishes its current step (block / check / level) and exits
# with L12|done|reason=stopfile (no end phase). Resume: remove the STOP file, relaunch rl/run_phase12.sh.
touch /mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/12/STOP && echo "STOP touched $(date -u +%FT%TZ)"
