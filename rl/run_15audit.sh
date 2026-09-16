#!/bin/bash
# Phase 15 A4L: the LABEL-FREE combat comparison for the keyword rungs.
#   bash rl/run_15audit.sh <deck> "<aspect card[,card]>" <name=ckpt> [<name=ckpt> ...]
#
# NOT part of any pre-registered A4L reading and it cannot become one. It exists
# because the W-deck recordings cannot clone joint attack/block (the rung-0 gate:
# attack 0.831, block 0.869), so the ladder's keyword rungs say nothing about combat
# through labels. This says something about combat WITHOUT labels: it plays a
# checkpoint on the rung's own deck and counts how often its declared attack and its
# blocks agree with CombatMath's reference.
#
# Uses rl/record_census.sh UNCHANGED (it already passes -Drl.debug=true
# -Drl.blockAudit=true -Drl.attackAudit=true and writes rec_<tag>.audit.txt for any
# deck; its per-deck census step simply does not fire for the W decks). One policy
# server + one driver JVM, so do NOT run this while a GPU trainer is up.
#
# Split: an audit line is ASPECT when one of the rung's new card names appears in it,
# SHARED otherwise - the names are printed in the line itself
# ("policy Leonin Skyhunter 2/2 + ... | ref ...  MATCH"), so no transcript parsing.
# Verdicts counted: MATCH / GAP / OVER, for [atkaudit] (attacks) and [audit] (blocks).
# Resumable: a checkpoint whose audit file already exists is not replayed.
[ -f ~/.profile ] && . ~/.profile
set -u
RL=/home/user/CardGuru/rl
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
OUT=$LB/rl/artifacts/v7/15/audit
P11=$LB/rl/artifacts/v7/11
DECK=${1:?deck}; ASPECT=${2:-}; shift 2
GAMES=${GAMES:-50}; SEED=${SEED:-15900}
mkdir -p $OUT
cd /home/user/CardGuru
echo "A15AUD|start|deck=$DECK|aspect=$ASPECT|games=$GAMES|$(date -u +%FT%TZ)"

for spec in "$@"; do
    NAME=${spec%%=*}; CK=${spec#*=}
    [ -s "$CK" ] || { echo "A15AUD|$DECK|$NAME|no checkpoint $CK"; continue; }
    TAG=a15_${DECK}_${NAME}
    if [ -s $OUT/$TAG.audit.txt ]; then
        echo "A15AUD|$DECK|$NAME|replay|skip"
    else
        bash $RL/record_census.sh "$CK" $DECK heuristic $GAMES $TAG $SEED > $OUT/$TAG.census.log 2>&1
        echo "A15AUD|$DECK|$NAME|census|$(grep '^CENSUSREC|'$TAG'|' $OUT/$TAG.census.log | grep -o 'rc=[0-9]*\|games=[0-9]*\|wins=[0-9]*\|losses=[0-9]*\|audit_lines=[0-9]*' | paste -sd' ')"
        cp -f $P11/rec_$TAG.audit.txt $OUT/$TAG.audit.txt 2>/dev/null
    fi
    [ -s $OUT/$TAG.audit.txt ] || { echo "A15AUD|$DECK|$NAME|no audit lines"; continue; }
    ASPECT="$ASPECT" python3 - "$OUT/$TAG.audit.txt" "$DECK" "$NAME" <<'PY'
import os, re, sys, collections
path, deck, name = sys.argv[1], sys.argv[2], sys.argv[3]
cards = [c.strip().lower() for c in os.environ.get("ASPECT", "").split(",") if c.strip()]
cnt = collections.Counter()
for line in open(path, encoding="utf-8", errors="ignore"):
    if "[atkaudit]" in line:
        kind = "attack"
    elif "[audit]" in line:
        kind = "block"
    else:
        continue
    low = line.lower()
    pop = "aspect" if any(c in low for c in cards) else "shared"
    v = "MATCH" if re.search(r"\bMATCH\b", line) else ("GAP" if re.search(r"\bGAP\b", line)
         else ("OVER" if re.search(r"\bOVER\b", line) else "OTHER"))
    cnt[(kind, pop, v)] += 1
    cnt[(kind, "all", v)] += 1
for kind in ("attack", "block"):
    for pop in ("all", "aspect", "shared"):
        tot = sum(cnt[(kind, pop, v)] for v in ("MATCH", "GAP", "OVER", "OTHER"))
        if not tot:
            continue
        m = cnt[(kind, pop, "MATCH")]
        print(f"A15AUD|{deck}|{name}|{kind}|pop={pop}|n={tot}|match={m}|match_frac={m/tot:.3f}"
              f"|gap={cnt[(kind, pop, 'GAP')]}|over={cnt[(kind, pop, 'OVER')]}|other={cnt[(kind, pop, 'OTHER')]}",
              flush=True)
PY
done
echo "A15AUD|done|deck=$DECK|$(date -u +%FT%TZ)"
