"""ASCII slices round one cell of a finished build: python3 audit/peek.py sid x y z [r=3] [dy=-1..1]
Prints each y layer (north at top, x to the right) with a legend of short names."""
import sys, os, io, contextlib, pickle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pipeline
sid = sys.argv[1]; x, y, z = map(int, sys.argv[2:5]); r = int(sys.argv[5]) if len(sys.argv) > 5 else 3
ys = sys.argv[6] if len(sys.argv) > 6 else "-1..1"
lo, hi = map(int, ys.split(".."))
cache = f"/tmp/peek_{sid}.pkl"
if os.path.exists(cache) and "--fresh" not in sys.argv: B = pickle.load(open(cache, "rb"))
else:
    with contextlib.redirect_stdout(io.StringIO()):
        m, b, *_ = pipeline.prepare(sid, "--raw" not in sys.argv)
    B = b.blocks; pickle.dump(B, open(cache, "wb"))
leg = {}
def code(s):
    if s is None: return " ."
    if s.split("[")[0] in ("minecraft:air",): return " _"
    if s not in leg: leg[s] = f"{len(leg):2d}" if len(leg) < 100 else "##"
    return leg[s]
for dy in range(hi, lo - 1, -1):
    print(f"y={y+dy}   x {x-r}..{x+r}")
    for zz in range(z - r, z + r + 1):
        print(f"z{zz:4d} " + " ".join(code(B.get((xx, y + dy, zz))) + ("*" if (xx, y + dy, zz) == (x, y, z) else " ") for xx in range(x - r, x + r + 1)))
for s, c in leg.items(): print(c, s.replace("minecraft:", "")[:90])
