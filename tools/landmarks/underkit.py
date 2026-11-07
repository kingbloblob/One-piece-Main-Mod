"""Shared pieces for the Nether and End rebuilds: carved caverns with a rock shell (the Impel Down levels sit in
the Nether rock just above the lava sea), rows of barred cells with furniture, support pillars down to the lava,
and the floating End islands the Holy Land buildings stand on."""
import math, random
from canvas import *
import interiors as I

BARS = "onepiece:prison_bars"


def cavern(b, cx, cz, rx, rz, h, shell, rnd, floor=None, thick=2, rough=0.08, below=4):
    """A domed cavern: AIR inside the half-ellipsoid, a rock shell `thick` deep round it and a solid floor slab.
    shell may be a block or a tuple to pick from. Returns inside(x, y, z)."""
    pick = (lambda: rnd.choice(shell)) if isinstance(shell, tuple) else (lambda: shell)
    def f(x, y, z, grow=0.0):
        return ((x - cx) / (rx + grow)) ** 2 + ((z - cz) / (rz + grow)) ** 2 + (max(0, y) / (h + grow)) ** 2
    for x in range(int(cx - rx - thick - 1), int(cx + rx + thick + 2)):
        for z in range(int(cz - rz - thick - 1), int(cz + rz + thick + 2)):
            n = 1 + rough * math.sin(x * 0.37 + z * 0.21) * math.cos(z * 0.29 - x * 0.13)
            for y in range(-below, int(h + thick + 2)):
                v = f(x, y, z) / n
                if y <= 0:
                    if f(x, 0, z, thick) / n < 1: b.set(x, y, z, (floor or pick()) if y == 0 and v < 1 else pick())
                elif v < 1: b.set(x, y, z, AIR)
                elif f(x, y, z, thick) / n < 1: b.set(x, y, z, pick())
    return lambda x, y, z: f(x, y, z) < 1


def cell(b, x0, y, z0, w, d, h, wall, facing, theme, seed, kind="cell", bars=BARS):
    """One barred cell opening toward `facing` (north/south/east/west), furnished inside."""
    x1, z1 = x0 + w - 1, z0 + d - 1
    b.walls(x0, y, z0, x1, y + h, z1, wall)
    b.box(x0 + 1, y, z0 + 1, x1 - 1, y + h - 1, z1 - 1, AIR)
    b.box(x0, y + h, z0, x1, y + h, z1, wall)
    b.box(x0, y - 1, z0, x1, y - 1, z1, wall)
    if facing in ("north", "south"):
        z = z0 if facing == "north" else z1
        for x in range(x0 + 1, x1):
            for yy in range(y, y + h): b.set(x, yy, z, bars)
    else:
        x = x0 if facing == "west" else x1
        for z in range(z0 + 1, z1):
            for yy in range(y, y + h): b.set(x, yy, z, bars)
    I.furnish(b, x0 + 1, y, z0 + 1, x1 - 1, z1 - 1, h - 1, kind, theme, seed=seed, lit=False)


def cell_row(b, x0, y, z0, n, w, d, h, wall, facing, theme, seed=0, axis="x", kind="cell"):
    for i in range(n):
        if axis == "x": cell(b, x0 + i * (w - 1), y, z0, w, d, h, wall, facing, theme, seed + i, kind)
        else: cell(b, x0, y, z0 + i * (d - 1), w, d, h, wall, facing, theme, seed + i, kind)


def pillars(b, pts, y_top, y_bot, s):
    for (x, z) in pts:
        for y in range(y_bot, y_top): b.set(x, y, z, s)


def floating_island(b, cx, cz, rx, rz, depth, rnd, top="minecraft:end_stone", body=("minecraft:end_stone",), dirt=None):
    """An End island under a build: flat top at y 0 (and dirt under it), tapering to a point `depth` below."""
    for x in range(int(cx - rx - 1), int(cx + rx + 2)):
        for z in range(int(cz - rz - 1), int(cz + rz + 2)):
            d = math.hypot((x - cx) / rx, (z - cz) / rz)
            n = 1 + 0.06 * math.sin(x * 0.4) * math.cos(z * 0.33)
            if d > n: continue
            bot = int(depth * (1 - (d / n) ** 1.6) + 2) + rnd.randint(0, 1)
            for y in range(-bot, 1):
                b.set(x, y, z, top if y == 0 else (dirt if dirt and y > -3 else rnd.choice(body)))
