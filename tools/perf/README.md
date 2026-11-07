# Profiling the mod (speed pass, 2026-10-24)

Runs the real client headless (see headless-client-testing) with JFR, then sums where the Server thread / Render thread spend time.

1. Copy source to a local folder (e.g. /root/perf), add to build.gradle:
   `loom { runs { client { vmArgs "-XX:FlightRecorderOptions:stackdepth=512", "-Xmx3G"; programArgs "--username", "Tester", "--quickPlaySingleplayer", "test", "--width", "1280", "--height", "720" } } }`
   stackdepth=512 matters: the default 64 cuts off the mod frames.
2. Java 25 (Temurin from api.adoptium.net). If Maven Central answers 429, add a Gradle init script with the mirror
   https://maven-central.storage-download.googleapis.com/maven2/ (in ~/.gradle/init.d, not in the project).
3. Start the client, then `measure.sh <name> 60`: records JFR for 60 s and runs `/tick query` every 10 s (ms per server tick).
4. `python3 jfrsum.py <file.jfr> ["Render thread"]` = share of time in mod code + biggest mod entry points.
   `python3 jfrcallee.py <file.jfr> "Server thread" <Method> 3` = what that method spends its time on (with line numbers).
   `jfr print` shows only 5 frames unless you pass --stack-depth (the scripts do).
Never upload profiles anywhere (no spark uploads).
