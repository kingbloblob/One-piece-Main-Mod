"""Quick look at a canvas build (m.build()): python3 tryc.py <sid> -> /root/mcb/prev/<sid>_celev.png"""
import sys, time, importlib
sys.path.insert(0, "/root/mcb/landmarks")
from mcb.kit import BigBuild
sid = sys.argv[1]
t = time.time()
m = importlib.import_module(f"mcb.{sid}")
b, g = m.build()
ys = [p[1] for p in b.blocks]
bb = BigBuild(seed=1, y_min=min(ys), y_max=max(ys))
for (x, y, z), s in b.blocks.items():
    if s != "minecraft:air":
        bb.set(x, y, z, s)
print("blocks", len(b.blocks), "build", round(time.time() - t, 1), "s")
bb.render_elevations(f"/root/mcb/prev/{sid}_celev.png", max_side=1200)
