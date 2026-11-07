"""Half-scale underwater birdcage reef, testing every mcreef part.

Proportions follow references/techniques/underwater-birdcage-reef.md
(studied build: cage r=67, height 251, 16 bars, 309 x 303 scene).
Run: python underwater_cage_demo.py  -> renders + a sharded datapack in ./out_reef
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import numpy as np

from mcbig import BigBuild
import mcreef as R

OUT = sys.argv[1] if len(sys.argv) > 1 else "out_reef"
os.makedirs(OUT, exist_ok=True)

S = 154                 # scene side (half of 309)
C = S // 2              # cage centre
r, H = 33, 125          # half of 67 / 251; keeps H : 2r ~= 1.9
y0 = 6

b = BigBuild(seed=7, y_min=0, y_max=150)
inside = lambda x, z: (x - C) ** 2 + (z - C) ** 2 <= (r + 3) ** 2

R.seabed(b, 0, 0, S - 1, S - 1, 1, relief=5)
R.sand_channel(b, [(5, 140), (40, 120), (60, 128), (100, 140), (150, 118)], 5, width=6)
info = R.birdcage_dome(b, C, y0, C, r, H, bars=16)
R.chandelier(b, C, info["y_top"] - 2, C, drop=8, r=11)
# centrepiece: coral spire inside the cage
top = R.coral_spire(b, C, y0, C, height=int(H * 0.33), radius=7)
R.gazebo(b, *top, r=6, height=7)
R.coral_garden(b, 2, 2, S - 3, S - 3, 4, 70, size=(4, 12), avoid=inside)
R.kelp_forest(b, 2, 2, S - 3, S - 3, 4, 70, h_min=20, h_max=120, avoid=inside)
R.jellyfish(b, 30, 115, 30, bell_r=7)
R.jellyfish(b, 125, 100, 40, bell_r=4, bell="minecraft:light_blue_stained_glass",
            rim="minecraft:blue_terracotta", tentacle="minecraft:light_blue_stained_glass_pane")
R.manta_ray(b, 120, 70, 120, span=14)
R.manta_ray(b, 30, 85, 115, span=12, facing="east")
R.fish_school(b, [(10, 60, 20), (50, 66, 30), (80, 70, 25), (120, 64, 35)], 40)
R.fish_school(b, [(20, 40, 140), (70, 45, 132), (110, 50, 145)], 30)

print(b.summary(12))
b.render_top(os.path.join(OUT, "top.png"), px=3)
b.render_section(os.path.join(OUT, "section.png"), axis="z", index=C, px=3)
b.render_elevations(os.path.join(OUT, "elevations.png"))

# Underwater version: flood the scene, keep the cage dry only if it is glazed.
# Here the walls are open bars, so everything floods; waterlog the partial blocks.
R.flood(b, 0, 1, 0, S - 1, 140, S - 1)
print("waterlogged block types:", R.waterlog(b))
n = b.save_sharded(os.path.join(OUT, "datapack"), namespace="reef", name="cage",
                   origin=(0, 60, 0))
print("datapack written", n)
