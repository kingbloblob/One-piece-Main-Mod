#!/bin/sh
# usage: measure.sh name seconds
N=$1; S=${2:-60}; PID=$(/root/jdk25/bin/jcmd -l 2>/dev/null | awk '/devlaunchinjector/{print $1}')
mkdir -p /root/jfr
/root/jdk25/bin/jcmd $PID JFR.start name=$N settings=profile >/dev/null 2>&1
i=0; while [ $i -lt $((S/10)) ]; do sleep 10; /root/cmd.sh "/tick query"; i=$((i+1)); done
/root/jdk25/bin/jcmd $PID JFR.stop name=$N filename=/root/jfr/$N.jfr >/dev/null 2>&1
echo "== $N"; grep "Average time per tick" /root/client1.log | tail -$((S/10)) | sed 's/.*Average time per tick: //'
