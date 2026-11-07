#!/bin/sh
# start.sh <dir>: runs the dev server with commands from <dir>/cmd fifo, log in <dir>/server.log
D=$1
mkdir -p $D/run && cd $D/run
echo eula=true > eula.txt
[ -f server.properties ] || printf 'online-mode=false\nlevel-seed=4242\nserver-port=%s\nspawn-protection=0\nmax-tick-time=-1\nsync-chunk-writes=false\n' $2 > server.properties
rm -f $D/cmd; mkfifo $D/cmd
cd $D
export JAVA_HOME=/root/jdk25 PATH=/root/jdk25/bin:$PATH
(sh ./gradlew runServer --no-daemon -q > $D/server.log 2>&1 </dev/null) &
