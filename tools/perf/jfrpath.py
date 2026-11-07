import json, subprocess, sys, collections
f, thread, target, depth = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv)>4 else 8
out = subprocess.run(["/root/jdk25/bin/jfr", "print", "--stack-depth", "300", "--json", "--events", "jdk.ExecutionSample", f], capture_output=True, text=True).stdout
c = collections.Counter(); tot=0
for e in json.loads(out)["recording"]["events"]:
    v = e["values"]
    if v["sampledThread"]["javaName"] != thread: continue
    tot+=1
    names = [fr["method"]["type"]["name"].split("/")[-1] + "." + fr["method"]["name"] for fr in v["stackTrace"]["frames"]]
    for i,n in enumerate(names):
        if target in n:
            c[" < ".join(names[i:i+depth])] += 1; break
for p, n in c.most_common(8): print(f"{100*n/tot:5.1f}% {p}\n")
