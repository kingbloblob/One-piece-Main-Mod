#!/bin/bash
# build stage, copy into opbuild, start the test server, wait for Done
export JAVA_HOME=/root/jdk/jdk-25.0.5+8 PATH=/root/jdk/jdk-25.0.5+8/bin:$PATH
cd /root/stage_src && sh ./gradlew build --no-daemon -q 2>&1 | grep -iE "error|FAIL" | head
ls -la /root/stage_src/build/libs/onepiece-0.1.0.jar
cp -a /root/stage_src/src/. /root/opbuild/src/
cd /root/opbuild && : > /root/server.log
(setsid nohup sh ./gradlew runServer --no-daemon > /root/server.log 2>&1 &)
sleep 5
timeout 900 bash -c "until grep -qE 'Done \(|BUILD FAILED|Exception in server tick' /root/server.log; do sleep 3; done"
grep -E "Done \(|BUILD FAILED|ERROR|FAILED during APPLY" /root/server.log | head
