#!/bin/bash
# Phase 7c: regenerate per-checkpoint sample transcripts.
#
# Why this is a separate script rather than part of the lane: XMage's
# game log is a log4j stream, and surefire does not relay the forked
# JVM's console to maven's stdout - it lands in
# Mage.Tests/magetest.log. Capturing mvn stdout (what the lane's
# sample_game does) yields a 2-line file. Reading magetest.log is the
# reliable route, but it is a single shared append-only file, so this
# must NOT run concurrently with the training lane or the two runs
# interleave. Run it after the lane finishes, against the saved pool
# checkpoints.
#
# Usage: bash rl/p7c_transcripts.sh <port> [checkpoints...]
#        (default: every pool/ck_*.pt at a 512 boundary, plus final)
set -u
APORT=${1:-7851}
shift || true
RL=/home/user/CardGuru/rl
OUT=/tmp/rl_p7c_lstmattn_s0
ARCH=lstmattn
CDIM=91
DECK=BenchDimir.dck
FEATS=$RL/e2_features.tsv
CURRIC=${P7C_CURRICULUM:-$RL/p7c_curriculum.tsv}
INTRO_EVERY=${P7C_INTRO_EVERY:-512}
MAGELOG=/home/user/mage/Mage.Tests/magetest.log

# the archetype introduced most recently at this checkpoint - the same
# choice the lane's sample_game makes, so transcripts stay comparable
newest_deck() {
    local n=$(( $1 / INTRO_EVERY + 1 ))
    local total=$(grep -vc '^#' $CURRIC)
    [ "$n" -gt "$total" ] && n=$total
    awk -F'\t' -v n=$n '!/^#/ { i++; if (i == n) { print $2 "\t" $3 } }' $CURRIC
}

start_server() {
    local try
    for try in 1 2 3; do
        rm -f /tmp/p7c_ts_srv.log
        python3 $RL/policy_server.py --port $APORT --ckpt "$1" \
            --seed 0 --cdim $CDIM --arch $ARCH > /tmp/p7c_ts_srv.log 2>&1 &
        echo $! > /tmp/p7c_ts.srvpid
        local up=0; SECONDS=0
        while [ $SECONDS -lt 90 ]; do
            grep -q "policy server" /tmp/p7c_ts_srv.log 2>/dev/null && { up=1; break; }
            grep -q "Traceback" /tmp/p7c_ts_srv.log 2>/dev/null && break
        done
        [ "$up" = "1" ] && return 0
        kill $(cat /tmp/p7c_ts.srvpid) 2>/dev/null
        wait $(cat /tmp/p7c_ts.srvpid) 2>/dev/null
        grep -q "Address already in use" /tmp/p7c_ts_srv.log 2>/dev/null || break
    done
    echo "TS_FAILED|server_never_started"; exit 1
}

CKPTS=("$@")
if [ ${#CKPTS[@]} -eq 0 ]; then
    mapfile -t CKPTS < <(ls $OUT/pool/ck_*.pt 2>/dev/null \
        | sed 's/.*ck_//; s/\.pt//' | sort -n \
        | awk -v e=$INTRO_EVERY '$1 % e == 0')
fi

cd /home/user/mage
for T in "${CKPTS[@]}"; do
    CK=$OUT/pool/ck_${T}.pt
    [ -f "$CK" ] || CK=$OUT/p7c_final.pt
    [ -f "$CK" ] || { echo "TS_SKIP|trained=$T|no checkpoint"; continue; }
    IFS=$'\t' read -r NAME DCK < <(newest_deck $T)
    : > $MAGELOG
    start_server "$CK"
    SRV=$(cat /tmp/p7c_ts.srvpid)
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DargLine="-Dfile.encoding=UTF-8 -Xmx4500m" \
        -DfailIfNoTests=false -Drl.episodes=1 \
        -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
        -Drl.opponent=heuristic -Drl.cardFeatures=$FEATS \
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=$DECK -Drl.oppDeck=$DCK -Drl.stopTurn=80 \
        -Drl.mode=eval -Drl.seed=951000 -Drl.report=0 \
        -Dxmage.dataCollectors.printGameLogs=true > /dev/null 2>&1
    kill $SRV 2>/dev/null; wait $SRV 2>/dev/null
    {
        echo "# Phase 7c sample game - trained=$T, agent BenchDimir vs D0 piloting $NAME ($DCK), seed 951000, argmax"
        grep "\[LOG\]\[GAME\]" $MAGELOG | sed 's/ *=>\[main\].*//'
    } > $OUT/transcript_${T}.txt
    echo "TS|trained=$T|vs=$NAME|lines=$(wc -l < $OUT/transcript_${T}.txt)"
done
