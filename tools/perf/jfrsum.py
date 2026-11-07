import json, subprocess, sys, collections
f, thread = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "Server thread")
out = subprocess.run(["/root/jdk25/bin/jfr", "print", "--stack-depth", "300", "--json", "--events", "jdk.ExecutionSample", f], capture_output=True, text=True).stdout
ev = json.loads(out)["recording"]["events"]
tot = 0; mod = collections.Counter(); modtop = collections.Counter(); top = collections.Counter(); anymod = 0
for e in ev:
    v = e["values"]
    if v["sampledThread"]["javaName"] != thread: continue
    tot += 1
    frames = v["stackTrace"]["frames"]
    names = [fr["method"]["type"]["name"].replace("/",".") + "." + fr["method"]["name"] for fr in frames]
    top[names[0]] += 1
    seen = set()
    for n in names:
        if n.startswith("com.onepiecemod") and n not in seen:
            seen.add(n); mod[n] += 1
    for n in reversed(names):  # outermost mod frame
        pass
    mods = [n for n in names if n.startswith("com.onepiecemod")]
    if mods:
        anymod += 1; modtop[mods[-1]] += 1
print(f"{thread}: {tot} samples, {anymod} ({100*anymod/max(tot,1):.1f}%) inside mod code")
print("-- outermost mod entry points:")
for n, c in modtop.most_common(15): print(f"{100*c/tot:5.1f}% {n}")
print("-- inclusive mod methods:")
for n, c in mod.most_common(25): print(f"{100*c/tot:5.1f}% {n}")
print("-- top frames:")
for n, c in top.most_common(12): print(f"{100*c/tot:5.1f}% {n}")
