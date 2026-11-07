#!/bin/bash
# restart the test server (picks up regenerated templates)
python3 /root/rcon.py stop >/dev/null 2>&1
timeout 120 bash -c 'while pgrep -f "runServer" >/dev/null; do sleep 2; done'
cd /root/opbuild && : > /root/server.log
(JAVA_HOME=/root/jdk/jdk-25.0.5+8 PATH=/root/jdk/jdk-25.0.5+8/bin:$PATH setsid nohup sh ./gradlew runServer --no-daemon > /root/server.log 2>&1 &)
sleep 5
timeout 900 bash -c "until grep -qE 'Done \(|BUILD FAILED|Exception in server tick' /root/server.log; do sleep 3; done"
grep -E "Done \(|BUILD FAILED|FAILED during APPLY" /root/server.log | head -3
