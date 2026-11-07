# Townsfolk pathing test (test only, never copy TownTest.java into source/)

Measures how well townsfolk get around a real generated town over an in-game day.

1. Copy a buildable project to a local folder (e.g. /root/tnew), drop TownTest.java into src/main/java/com/onepiecemod/town/,
   add `static Town testRegister(String key, java.util.function.Supplier<Town> f) { return BY_KEY.computeIfAbsent(key, k -> f.get()); }`
   to Towns.java and `TownTest.init();` after the Towns::tick registration in TownFeature. `python3 patchtest.py TownRoutineGoal.java`
   makes watched() always true (so nobody is teleported while "seen") and counts forced arrivals / climb-outs.
   build.gradle: `loom { runs { server { vmArgs "-Xmx3G", "-Dtowntest.watched=true" } } }`
2. run/server.properties: online-mode=false, level-type=onepiece\:grand_line, enable-rcon=true, rcon.port, rcon.password=test.
   start.sh <dir> starts runServer; rcon.py <port> "cmd" ... talks to it.
3. `/locate structure onepiece:foosha_village`, `/forceload add` around it, `/towntest <x> <z>`, then
   run.sh <dir> <port> <x> <z> 24000 kills townsfolk, lets the town repopulate, sprints a day and prints the report
   (samples at target, stuck samples = >4 blocks from target and moved <1.5 blocks in 10 s, 30 s+ stuck events with a block dump).
   `/towntest dump x y z` prints the blocks around a spot, `/towntest doors` counts open/closed doors.
