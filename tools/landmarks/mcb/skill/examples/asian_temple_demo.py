"""Two-tier East Asian temple hall at the studied size (hall 43 x 23), plus a small
single-storey shrine at about half scale, to test mcasian.
Run: python asian_temple_demo.py [out_dir]"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
from mcbig import BigBuild
import mcasian as A

OUT = sys.argv[1] if len(sys.argv) > 1 else "out_temple"
os.makedirs(OUT, exist_ok=True)

b = BigBuild(seed=3, y_min=0, y_max=80)
info = A.temple_hall(b, 0, 1, 0, w=43, d=23, bays=5, two_storey=True)
print(info)
print(b.summary(14))
b.render_elevations(os.path.join(OUT, "elevations.png"))
px1, pz1, px2, pz2 = info["platform"]
b.render_section(os.path.join(OUT, "section.png"), axis="x", index=(px1 + px2) // 2, px=6)
n = b.save_function(os.path.join(OUT, "temple.mcfunction"))
print("commands", n)

s = BigBuild(seed=4, y_min=0, y_max=50)
i2 = A.temple_hall(s, 0, 1, 0, w=19, d=11, bays=3, two_storey=False)
print(i2)
s.render_elevations(os.path.join(OUT, "shrine_elevations.png"))
print("shrine commands", s.save_function(os.path.join(OUT, "shrine.mcfunction")))
