#!/bin/bash
# Download the one-set 17Lands inputs for rl/L17-CLOUD.md (user permission 2026-09-15).
set -u
D=/home/user/CardGuru/rl/data/l17; mkdir -p $D; cd $D
B=https://17lands-public.s3.amazonaws.com/analysis_data
curl -sS -f -C - -o cards.csv $B/cards/cards.csv && echo "cards.csv $(stat -c %s cards.csv)"
curl -sS -f -C - -o replay_data_public.DSK.PremierDraft.csv.gz $B/replay_data/replay_data_public.DSK.PremierDraft.csv.gz && echo "replay $(stat -c %s replay_data_public.DSK.PremierDraft.csv.gz)"
echo L17DL_DONE
