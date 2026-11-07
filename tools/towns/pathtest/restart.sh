#!/bin/sh
# restart.sh <dir> <rconport>
python3 /root/testhook/rcon.py $2 stop >/dev/null 2>&1
while ps aux | grep -v grep | grep -q "$1/.gradle/loom-cache/launch\.cfg"; do sleep 2; done
/root/testhook/start.sh $1
while ! grep -q "Done (\|FAILED" $1/server.log; do sleep 3; done
grep -m1 "Done (\|FAILED" $1/server.log
