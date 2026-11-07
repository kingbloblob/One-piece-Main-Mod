#!/bin/sh
# mk.sh <dest> <town-src-dir>
set -e
D=$1; S=$2
rm -rf $D; mkdir -p $D
cd /root/tw && tar --exclude=./build --exclude=./run -cf - . | tar -xf - -C $D
cp $S/*.java $D/src/main/java/com/onepiecemod/town/
[ "$S" = /root/oldtown ] && rm -f $D/src/main/java/com/onepiecemod/town/TownNavigation.java $D/src/main/java/com/onepiecemod/town/TownDoorGoal.java
cp /root/testhook/TownTest.java $D/src/main/java/com/onepiecemod/town/
cd $D/src/main/java/com/onepiecemod/town
python3 - <<'PY'
import re
s=open('Towns.java').read()
s=s.replace("\tstatic void tick(MinecraftServer server) {","\tstatic Town testRegister(String key, java.util.function.Supplier<Town> f) { return BY_KEY.computeIfAbsent(key, k -> f.get()); }\n\n\tstatic void tick(MinecraftServer server) {",1)
open('Towns.java','w').write(s)
s=open('TownFeature.java').read()
s=s.replace("ServerTickEvents.END_SERVER_TICK.register(Towns::tick);","ServerTickEvents.END_SERVER_TICK.register(Towns::tick);\n\t\tTownTest.init();",1)
open('TownFeature.java','w').write(s)
s=open('TownRoutineGoal.java').read()
s=s.replace("Player player = mob.level().getNearestPlayer(mob, 24.0);","if (Boolean.getBoolean(\"towntest.watched\")) return true;\n\t\tPlayer player = mob.level().getNearestPlayer(mob, 24.0);",1)
open('TownRoutineGoal.java','w').write(s)
PY
cd $D && cat >> build.gradle <<'G'
loom { runs { server { vmArgs "-Xmx3G", "-Dtowntest.watched=true" } } }
G
