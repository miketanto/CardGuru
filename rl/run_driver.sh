#!/bin/bash
# Phase 9 drop-in for one driver invocation. Takes exactly the -Drl.*
# flags the mvn command took and routes them either to the old surefire
# path (default) or to the persistent driver JVM.
#
# In a league runner, replace
#     mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
#         -DargLine="-Dfile.encoding=UTF-8 -Xmx4500m" -DfailIfNoTests=false \
#         -Drl.episodes=64 ... > /dev/null 2>&1
# with
#     bash /home/user/CardGuru/rl/run_driver.sh -Drl.episodes=64 ... \
#         > /dev/null 2>&1
# and nothing else changes: same properties, same -Drl.out file, same
# exit code, same RL|summary on stdout.
#
# Environment:
#   RL_PERSIST=1        use the persistent JVM (default 0 = mvn, exactly
#                       as before - the main session's runners are
#                       unaffected until they opt in)
#   RL_DRIVER_PORT      persistent server port (default 7910)
#   RL_CONC=N           play N episodes concurrently INSIDE the job.
#                       TRAINING LANES ONLY - an eval/Elo lane must leave
#                       this unset so the run stays sequential and
#                       reproducible. Requires the server to have been
#                       started with -Dmage.randomPerThread=true and, for
#                       agent=rl, a policy server run with --threads >= N.
#   RL_AUTOSTART=1      start the persistent server if it is not up
# The server must be started once per training session:
#   bash rl/driver_server.sh start 7910 \
#       "-Dmage.randomPerThread=true -XX:+UseParallelGC -Dmage.playableCache=on"
set -u
CG=$(cd "$(dirname "$0")" && pwd)
PORT=${RL_DRIVER_PORT:-7910}

if [ "${RL_PERSIST:-0}" != "1" ]; then
    cd /home/user/mage
    exec mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DfailIfNoTests=false \
        -DargLine="-Dfile.encoding=UTF-8 -Xmx4500m" "$@"
fi

if ! python3 $CG/driver_client.py --port $PORT --ping > /dev/null 2>&1; then
    if [ "${RL_AUTOSTART:-0}" = "1" ]; then
        bash $CG/driver_server.sh start $PORT \
            "-Dmage.randomPerThread=true -XX:+UseParallelGC -Dmage.playableCache=on" \
            > /dev/null 2>&1 || { echo "RL_DRIVER|server_start_failed"; exit 1; }
    else
        echo "RL_DRIVER|no_server_on_${PORT} (start it with rl/driver_server.sh"
        echo "           or set RL_AUTOSTART=1)"
        exit 1
    fi
fi

CONC=""
[ -n "${RL_CONC:-}" ] && CONC="-Drl.concurrency=$RL_CONC"
cd /home/user/mage
exec python3 $CG/driver_client.py --port $PORT "$@" $CONC
