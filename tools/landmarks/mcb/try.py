"""Quick look at a v2 design: python3 /root/mcb/try.py <sid> [sections...]  -> /root/mcb/prev/<sid>_top.png etc."""
import sys, time, importlib
sys.path.insert(0, "/root/mcb/landmarks")
sid = sys.argv[1]
t = time.time()
m = importlib.import_module(f"mcb.{sid}")
res = m.design()
bb = res[0]
print("design", round(time.time() - t, 1), "s")
audit = res[1]
print("audit fails", len(audit))
for a in audit[:8]: print("  ", a[:200])
print(bb.summary(top=12))
bb.render_top(f"/root/mcb/prev/{sid}_top.png", px=3, max_side=900)
for s in sys.argv[2:]:
    ax, i = s[0], int(s[1:])
    bb.render_section(f"/root/mcb/prev/{sid}_{s}.png", axis=ax, index=i, px=3, max_side=900)
bb.render_elevations(f"/root/mcb/prev/{sid}_elev.png", max_side=1200)
print("total", round(time.time() - t, 1), "s")
