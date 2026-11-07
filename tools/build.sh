#!/bin/sh
# Compiles the shared source in a local copy (so build/ and .gradle/ never land on the shared folder).
# Usage (needs the Fabric/Mojang/Gradle/Adoptium hosts reachable from your sandbox):
#   sh /mnt/project-files/one-piece-mod/tools/build.sh [gradle task, default: build]
# Downloads Java 25 into /root/jdk on first use. Errors are printed at the end; full log in /root/opbuild/build.log.
set -e
SRC=/mnt/project-files/one-piece-mod/source
W=/root/opbuild
JDK=$(ls -d /root/jdk/jdk-25* 2>/dev/null | head -1)
if [ -z "$JDK" ]; then
	mkdir -p /root/jdk
	curl -sSL "https://api.adoptium.net/v3/binary/latest/25/ga/linux/x64/jdk/hotspot/normal/eclipse" | tar xz -C /root/jdk
	JDK=$(ls -d /root/jdk/jdk-25* | head -1)
fi
mkdir -p $W && rm -rf $W/src
cp -r $SRC/src $SRC/libs $SRC/build.gradle $SRC/settings.gradle $SRC/gradle.properties $SRC/gradle $SRC/gradlew $SRC/LICENSE $W/
chmod +x $W/gradlew
cd $W
set +e
JAVA_HOME=$JDK PATH=$JDK/bin:$PATH ./gradlew ${1:-build} --no-configuration-cache -q > $W/build.log 2>&1
code=$?
grep -A2 ' error:' $W/build.log | sed "s|$W/src/||" | head -150
[ $code = 0 ] && echo "BUILD OK: $W/build/libs" || echo "BUILD FAILED (exit $code), see $W/build.log"
exit $code
