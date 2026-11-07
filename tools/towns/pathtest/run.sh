#!/bin/sh
# run.sh <dir> <rconport> <x> <z> <ticks>
R="python3 /root/testhook/rcon.py $2"
$R "kill @e[type=onepiece:townsfolk]" >/dev/null; $R "towntest $3 $4" >/dev/null
sleep 45
$R "time set 0" >/dev/null; $R "weather clear 30000" >/dev/null
$R "tick sprint $5" >/dev/null
while ! grep -q "Sprint completed" $1/server.log; do sleep 5; done
$R "towntest report" >/dev/null
sleep 1
grep "Sprint completed" $1/server.log
grep "TOWNTEST report\|TOWNTEST   " $1/server.log
echo "stuck lines: $(grep -c 'TOWNTEST stuck30s' $1/server.log)"
