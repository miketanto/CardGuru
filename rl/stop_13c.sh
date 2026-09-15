#!/bin/bash
# Graceful stop of Phase 13c: the controller finishes its current step (block / check / level) and exits
# with L13|done|reason=stopfile. Resume: remove the STOP file and relaunch the 13c controller.
touch /mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/13/c/STOP && echo "STOP touched $(date -u +%FT%TZ)"
