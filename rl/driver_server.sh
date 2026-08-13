#!/bin/bash
# Start/stop the Phase 9 persistent driver JVM.
#   bash rl/driver_server.sh start [port] [extra JVM flags...]
#   bash rl/driver_server.sh stop  [port]
# The classpath is built once with dependency:build-classpath and cached
# at /tmp/rl_p9/cp.txt; delete that file after changing dependencies.
# cwd is Mage.Tests so decks and config/config.xml resolve exactly as
# they did under surefire.
set -u
CMD=${1:-start}
PORT=${2:-7910}
shift 2 2>/dev/null || shift 1 2>/dev/null || true
JVM_EXTRA="${*:-}"
OUT=/tmp/rl_p9
CP=$OUT/cp.txt
LOG=$OUT/driver_server_${PORT}.log
PIDF=$OUT/driver_server_${PORT}.pid
mkdir -p $OUT

case $CMD in
stop)
    if [ -f $PIDF ]; then
        python3 /home/user/CardGuru/rl/driver_client.py --port $PORT --shutdown \
            > /dev/null 2>&1
        pid=$(cat $PIDF)
        for _ in $(seq 1 20); do
            kill -0 "$pid" 2>/dev/null || break
            sleep 0.5
        done
        kill -9 "$pid" 2>/dev/null
        rm -f $PIDF
    fi
    # belt and braces: a server whose pid file was lost still owns the
    # port, and the next start would silently hand jobs to the OLD JVM
    # (with the old flags) - so match on the port in the command line
    pkill -f "RLDriverServe[r] --port $PORT" 2>/dev/null
    sleep 1
    echo "driver server on :$PORT stopped"
    exit 0 ;;
start) ;;
*)  echo "usage: driver_server.sh start|stop [port] [jvm flags]"; exit 2 ;;
esac

cd /home/user/mage
if [ ! -s $CP ]; then
    mvn -q -pl Mage.Tests dependency:build-classpath \
        -Dmdep.outputFile=$CP -DincludeScope=test > $OUT/cp_build.log 2>&1 \
        || { echo "classpath build failed"; tail -5 $OUT/cp_build.log; exit 1; }
fi
FULLCP="/home/user/mage/Mage.Tests/target/test-classes:/home/user/mage/Mage.Tests/target/classes:$(cat $CP)"

cd /home/user/mage/Mage.Tests
rm -f $LOG
nohup java -cp "$FULLCP" -Dfile.encoding=UTF-8 -Xmx4500m $JVM_EXTRA \
    org.mage.test.benchmark.rl.RLDriverServer --port $PORT > $LOG 2>&1 &
echo $! > $PIDF
SECONDS=0
while [ $SECONDS -lt 300 ]; do
    grep -q "RLSRV|ready" $LOG 2>/dev/null && { grep "RLSRV|ready" $LOG; exit 0; }
    grep -qi "exception\|error:" $LOG 2>/dev/null && { cat $LOG; exit 1; }
    sleep 1
done
echo "driver server never became ready"; tail -20 $LOG; exit 1
