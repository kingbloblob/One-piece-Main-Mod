#!/bin/bash
set -x
export JAVA_HOME=/root/jdk/jdk-25.0.5+8 PATH=/root/jdk/jdk-25.0.5+8/bin:$PATH
cd /root/stage_src && rm -rf src && cp -a /mnt/project-files/one-piece-mod/source/src . && echo copied
timeout 1500 sh ./gradlew build --no-daemon -q > /root/build.log 2>&1; echo "build exit $?"
grep -E "error:|FAILED" /root/build.log | head
python3 /root/rcon.py "forceload remove all" >/dev/null 2>&1
rm -rf /root/opbuild/src && cp -a /root/stage_src/src /root/opbuild/ && echo synced
/root/restart.sh
grep -E "FAILED during APPLY|was not applied" /root/server.log | head -5
echo VERIFY_END
