"""Irregular test island on the flat-ocean test world (water top 62, floor ~54): a noisy round island with sand
beaches sloping into the water and gentle rolling grass inland, so a land build is seen in natural-ish terrain instead
of on a square platform.  python3 /root/island.py cx cz radius"""
import sys, math
sys.path.insert(0, "/root"); sys.path.insert(0, "/root/mcb/landmarks")
from rcon import cmd
from landkit import noise2
cx, cz, R = map(int, sys.argv[1:4])
for x in range(cx - R - 20, cx + R + 20, 64):
    for z in range(cz - R - 20, cz + R + 20, 64):
        cmd(f"forceload add {x} {z} {x+63} {z+63}")
def h(x, z):
    a = math.atan2(z - cz, x - cx)
    rr = R * (0.85 + 0.22 * noise2(math.cos(a) * 40 + 100, math.sin(a) * 40 + 100, 77, 9))
    d = math.hypot(x - cx, z - cz) / rr
    if d < 0.72: return 62
    if d < 1.0: return int(round(62 + 7 * math.sin(math.pi * (d - 0.72) / 0.28) * (0.3 + 0.9 * noise2(x, z, 78, 17))))
    if d < 1.3: return int(round(62 - (d - 1.0) / 0.3 * 8))
    return None
n = 0
for x in range(cx - R - 40, cx + R + 40):
    runs = []
    for z in range(cz - R - 40, cz + R + 41):
        y = h(x, z)
        if runs and runs[-1][2] == y and runs[-1][1] == z - 1: runs[-1][1] = z
        else: runs.append([z, z, y])
    for z0, z1, y in runs:
        if y is None or y < 55: continue
        top = "minecraft:sand" if (y <= 62 and math.hypot(x - cx, z - cz) > R * 0.8) else "minecraft:grass_block"
        cmd(f"fill {x} 54 {z0} {x} {y-1} {z1} {'minecraft:sandstone' if top.endswith('sand') else 'minecraft:dirt'}")
        cmd(f"fill {x} {y} {z0} {x} {y} {z1} {top}")
        n += 2
print("cmds", n)
