"""Toy House v2, redesigned with the Minecraft Builder skill: Dressrosa's cheerful toy-box building at the foot of
the King's Plateau, and the secret it sits on.

A Dressrosa island: the King's Plateau climbs in stone cliffs across the north, the town and flower beds spread over
the rest, the sea on every side. At the foot of the plateau stands the Toy House: a stack of painted toy blocks
(red, yellow, blue, green, orange cubes with white edges and coloured window frames) three blocks high and stepped
down at the ends, four round candy-striped corner towers with pink and yellow caps, a huge gear and a clock face
over the arched door, a red-and-yellow roof and a carousel-horse weathervane. Inside, the toy show room with its
shelves and the wide stair down; upstairs Sugar's grape room and the Donquixote officers' lounge. Underneath: the
SMILE factory hall with its conveyor lines, vats and crates, the cramped dormitory of the toys and dwarves, and the
underground trade port, a canal from a barred sea gate in the west cliff with a plank quay and cargo.
168 x 168. y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, set_if_air, wing_floor, house_module, place_house, lamp_post, glyph
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "toy_house"
TITLE = "Toy House (Dressrosa)"
CUTS = [3, 12, 18, 24]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 168
_S1 = NT.outline(84, 86, 70, 3420, wobble=0.08)
SHORE = _S1
GY = 10                             # ground level of the town
TOY = (60, 66, 101, 89)             # Toy House footprint (inclusive): 42 x 24
CUBE = 6
FAC = (46, 60, 116, 96)             # the factory hall under it
FY = 0                              # factory floor
CANAL_Z = 78                        # trade port canal centre line (runs west to the sea gate)
PLATEAU_Z = 44                      # cliffs of the King's Plateau north of this

STREET = [("minecraft:smooth_sandstone", 0.3), ("minecraft:cut_sandstone", 0.2), ("minecraft:sandstone", 0.15),
          ("minecraft:polished_granite", 0.15), ("minecraft:terracotta", 0.1), ("minecraft:white_terracotta", 0.1)]
SAND = [("minecraft:sand", 0.7), ("minecraft:sandstone", 0.15), ("minecraft:clay", 0.15)]
ROCK = [("minecraft:stone", 0.35), ("minecraft:granite", 0.2), ("minecraft:andesite", 0.2), ("minecraft:cobblestone", 0.1),
        ("minecraft:tuff", 0.15)]
COLORS = ["red", "yellow", "blue", "lime", "orange", "light_blue", "magenta", "green", "pink", "cyan"]
PALS = [
    dict(walls=["minecraft:white_terracotta", "minecraft:calcite", "minecraft:white_terracotta"], frame="minecraft:stripped_spruce_log",
         base=["minecraft:cut_sandstone", "minecraft:smooth_sandstone", "minecraft:sandstone"], floor="minecraft:spruce_planks",
         wood="spruce", chimney="minecraft:bricks"),
    dict(walls=["minecraft:yellow_terracotta", "minecraft:smooth_sandstone", "minecraft:yellow_terracotta"], frame="minecraft:stripped_oak_log",
         base=["minecraft:cut_sandstone", "minecraft:smooth_sandstone", "minecraft:granite"], floor="minecraft:oak_planks",
         wood="oak", chimney="minecraft:bricks"),
    dict(walls=["minecraft:pink_terracotta", "minecraft:white_terracotta", "minecraft:calcite"], frame="minecraft:stripped_dark_oak_log",
         base=["minecraft:stone_bricks", "minecraft:cut_sandstone", "minecraft:smooth_sandstone"], floor="minecraft:dark_oak_planks",
         wood="dark_oak", chimney="minecraft:bricks"),
]
ROOFS = ["minecraft:granite_stairs", "minecraft:red_sandstone_stairs", "minecraft:brick_stairs", "minecraft:mud_brick_stairs"]
KINDS = [["kitchen", "living", "bedroom", "bedroom"], ["workshop", "storage", "bedroom"], ["dining", "living", "library", "bedroom"]]


def rect_d(X, Z, r):
    dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0)
    dz = np.maximum(np.maximum(r[1] - Z, Z - r[3]), 0)
    return np.hypot(dx, dz)


def streets(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    m = (np.abs(X - 80) <= 2) & (Z > TOY[3]) & (Z < 160)
    m |= (np.abs(Z - 112) <= 2) & (X > 16) & (X < 152)
    m |= (np.abs(Z - 138) <= 2) & (X > 24) & (X < 144)
    m |= (np.abs(X - 40) <= 2) & (Z > 56) & (Z < 150)
    m |= (np.abs(X - 124) <= 2) & (Z > 56) & (Z < 150)
    m |= rect_d(X, Z, (TOY[0] - 6, TOY[3] + 1, TOY[2] + 6, TOY[3] + 10)) <= 0
    return m


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = SHORE(X, Z)
    h = GY + NT.fbm(X, Z, 3422, 26) * 4 - 1
    w = np.clip(rect_d(X, Z, (30, PLATEAU_Z + 4, 140, 160)) / 6.0, 0, 1)
    h = GY * (1 - w) + h * w
    # the King's Plateau: stone cliffs rising in two steps north of PLATEAU_Z
    plat = np.clip((PLATEAU_Z - Z) / 3.0, 0, 1) * 16 + np.clip((PLATEAU_Z - 14 - Z) / 3.0, 0, 1) * 14
    plat = plat + NT.fbm(X, Z, 3423, 12) * 3 * (plat > 0)
    h = h + plat
    h = h * np.clip((d - 1.5) / 14.0, 0, 1)
    h = np.where(d < 1.5, -1, h)
    return np.round(h)


def build_maps():
    X = np.arange(N)[:, None]
    Z = np.arange(N)[None, :]
    H = _height(X, Z).astype(int)
    g = np.zeros_like(H)
    for a, b in (((slice(1, None), slice(None)), (slice(None, -1), slice(None))),
                 ((slice(None), slice(1, None)), (slice(None), slice(None, -1)))):
        dd = np.abs(H[a] - H[b])
        g[a] = np.maximum(g[a], dd); g[b] = np.maximum(g[b], dd)
    return H, g


HMAP, GRAD = build_maps()


def height(X, Z):
    return HMAP[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def steep(X, Z):
    return GRAD[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)] >= 2


def land(X, Z):
    return SHORE(X, Z) > 1.5


def hy(x, z):
    return int(HMAP[min(max(x, 0), N - 1), min(max(z, 0), N - 1)])


def terrain(bb):
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SAND, 3431, mask=lambda X, Z: land(X, Z) & (height(X, Z) <= 3),
             under="minecraft:sandstone", core="minecraft:stone", base=-6)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, ROCK, 3432, mask=lambda X, Z: land(X, Z) & steep(X, Z) & (height(X, Z) > 3),
             under="minecraft:stone", core="minecraft:stone", base=-6)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, NT.MEADOW, 3433, mask=lambda X, Z: land(X, Z) & ~steep(X, Z) & (height(X, Z) > 3),
             core="minecraft:stone", base=-6)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, STREET, 3434, mask=lambda X, Z: land(X, Z) & streets(X, Z), core="minecraft:stone", base=-6)
    bed = lambda X, Z: np.round(-2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10))
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy == bed(X, Z)), "minecraft:sand")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy < bed(X, Z)) & (yy >= bed(X, Z) - 2), "minecraft:stone")


# ------------------------------------------------------------------ the Toy House
def toy_house(bb, tracker, audit):
    x1, z1, x2, z2 = TOY
    y0 = GY
    rng = np.random.default_rng(3440)
    bb.fill(x1 - 2, y0 - 3, z1 - 2, x2 + 2, y0, z2 + 2, "minecraft:smooth_quartz")
    nx, nz = (x2 - x1 + 1) // CUBE, (z2 - z1 + 1) // CUBE
    # the stack: three layers of cubes, the top layer stepped in at the ends
    tops = {}
    for i in range(nx):
        for j in range(nz):
            layers = 3 if 1 <= i <= nx - 2 else 2
            if (i in (0, nx - 1)) and (j in (0, nz - 1)):
                layers = 2
            tops[(i, j)] = layers
            for L in range(layers):
                c = COLORS[(i * 3 + j * 5 + L * 7 + int(rng.integers(0, 2))) % len(COLORS)]
                ax, az, ay = x1 + i * CUBE, z1 + j * CUBE, y0 + 1 + L * CUBE
                bb.fill(ax, ay, az, ax + CUBE - 1, ay + CUBE - 1, az + CUBE - 1, f"minecraft:{c}_concrete")
                # white edges on every cube
                for (a, b) in ((ax, az), (ax + CUBE - 1, az), (ax, az + CUBE - 1), (ax + CUBE - 1, az + CUBE - 1)):
                    bb.fill(a, ay, b, a, ay + CUBE - 1, b, "minecraft:white_concrete")
                for yy in (ay, ay + CUBE - 1):
                    bb.fill(ax, yy, az, ax + CUBE - 1, yy, az, "minecraft:white_concrete")
                    bb.fill(ax, yy, az + CUBE - 1, ax + CUBE - 1, yy, az + CUBE - 1, "minecraft:white_concrete")
                    bb.fill(ax, yy, az, ax, yy, az + CUBE - 1, "minecraft:white_concrete")
                    bb.fill(ax + CUBE - 1, yy, az, ax + CUBE - 1, yy, az + CUBE - 1, "minecraft:white_concrete")
    # hollow it out: three floors, red floor beams
    for i in range(nx):
        for j in range(nz):
            for L in range(tops[(i, j)]):
                ax, az, ay = x1 + i * CUBE, z1 + j * CUBE, y0 + 1 + L * CUBE
                bb.fill(max(ax, x1 + 1), ay + (1 if L else 0), max(az, z1 + 1), min(ax + CUBE - 1, x2 - 1), ay + CUBE - 2,
                        min(az + CUBE - 1, z2 - 1), AIR)
    for L in range(1, 3):
        y = y0 + L * CUBE
        bb.fill_where(x1 + 1, y, z1 + 1, x2 - 1, y, z2 - 1,
                      lambda X, Y, Z: np.vectorize(lambda a, b: tops[((a - x1) // CUBE, (b - z1) // CUBE)] > L)(X, Z),
                      "minecraft:spruce_planks")
        for x in (x1, x2):
            bb.fill(x, y, z1, x, y, z2, "minecraft:red_concrete")
        for z in (z1, z2):
            bb.fill(x1, y, z, x2, y, z, "minecraft:red_concrete")
    bb.fill(x1 + 1, y0, z1 + 1, x2 - 1, y0, z2 - 1, "minecraft:birch_planks")
    # windows: a 2 x 2 window with a coloured frame in the middle of each outer cube face
    for i in range(nx):
        for j in range(nz):
            for L in range(tops[(i, j)]):
                ax, az, ay = x1 + i * CUBE, z1 + j * CUBE, y0 + 1 + L * CUBE
                fr = f"minecraft:{COLORS[(i + j + L + 3) % len(COLORS)]}_terracotta"
                faces = []
                if j == 0: faces.append(("z", z1, ax))
                if j == nz - 1: faces.append(("z", z2, ax))
                if i == 0: faces.append(("x", x1, az))
                if i == nx - 1: faces.append(("x", x2, az))
                for (axis, line, a0) in faces:
                    for u in range(1, 5):
                        for v in range(1, 5):
                            pos = (a0 + u, ay + v, line) if axis == "z" else (line, ay + v, a0 + u)
                            edge = u in (1, 4) or v in (1, 4)
                            bb.set(pos[0], pos[1], pos[2], fr if edge else "minecraft:glass_pane")
    # the arched door on the south front with the big gear and the clock above
    cx = (x1 + x2) // 2
    bb.fill(cx - 2, y0 + 1, z2, cx + 3, y0 + 4, z2, AIR)
    bb.fill(cx - 1, y0 + 5, z2, cx + 2, y0 + 5, z2, AIR)
    bb.fill(cx - 3, y0 + 1, z2 + 1, cx - 3, y0 + 6, z2 + 1, "minecraft:red_concrete")
    bb.fill(cx + 4, y0 + 1, z2 + 1, cx + 4, y0 + 6, z2 + 1, "minecraft:red_concrete")
    bb.fill(cx - 3, y0 + 6, z2 + 1, cx + 4, y0 + 6, z2 + 1, "minecraft:yellow_concrete")
    gear(bb, x1 + 9, y0 + 11, z2 + 1, 5)
    clock(bb, cx, y0 + 13, z2 + 1, 4)
    gear(bb, x2 - 7, y0 + 9, z2 + 1, 3)
    # corner towers: candy-striped round towers with pointed caps
    for (tx, tz) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        for y in range(y0 + 1, y0 + 25):
            bb.cylinder(tx, y, tz, 3, y, "minecraft:white_concrete" if (y // 2) % 2 else "minecraft:pink_concrete", hollow=True)
        bb.cylinder(tx, y0 + 25, tz, 4, y0 + 25, "minecraft:yellow_concrete")
        P.cone_roof(bb, tx, y0 + 26, tz, 4, 9, "minecraft:magenta_concrete" if (tx + tz) % 2 else "minecraft:yellow_concrete")
        bb.set(tx, y0 + 35, tz, "minecraft:gold_block")
        for y in (y0 + 8, y0 + 14, y0 + 20):
            for (ox, oz) in ((3, 0), (-3, 0), (0, 3), (0, -3)):
                bb.set(tx + ox, y, tz + oz, "minecraft:light_blue_stained_glass_pane")
    # the roof: a red and yellow striped gable over the middle, the carousel horse on top
    mx1, mx2 = x1 + CUBE, x2 - CUBE
    ytop = y0 + 1 + 3 * CUBE
    for x in range(mx1 - 1, mx2 + 2):
        P.gable_roof(bb, x, z1 - 1, x, z2 + 1, ytop, "minecraft:red_nether_brick_stairs" if (x // 2) % 2 else "minecraft:smooth_sandstone_stairs",
                     ridge_axis="x", overhang=0)
    bb.fill(mx1 - 1, ytop, z1, mx1 - 1, ytop + 12, z2, AIR) if False else None
    for x in (mx1 - 1, mx2 + 1):
        for z in range(z1, z2 + 1):
            hgt = min(z - z1, z2 - z) + 1
            bb.fill(x, ytop, z, x, ytop + hgt - 1, z, "minecraft:yellow_concrete")
    ridge = ytop + (z2 - z1) // 2 + 1
    hx, hz = (x1 + x2) // 2, (z1 + z2) // 2
    bb.fill(hx, ridge, hz, hx, ridge + 6, hz, "minecraft:gold_block")
    horse = [".##....", "####...", "..#####", "..#####", "..#...#", "..#...#"]
    glyph(bb, horse, hx - 3, ridge + 13, hz, "minecraft:white_concrete", axis="x")
    bb.set(hx, ridge + 7, hz, "minecraft:gold_block")
    interior(bb, tracker, audit, tops)
    return (x1 - 5, z1 - 5, x2 + 5, z2 + 5)


def gear(bb, x, y, z, r):
    """A gear on the facade (in the x-y plane at z): a ring with square teeth and a hub."""
    for dx in range(-r - 1, r + 2):
        for dy in range(-r - 1, r + 2):
            d = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            tooth = (int((a + math.pi) / (2 * math.pi) * 12) % 2 == 0)
            if r - 1.5 < d <= r + 0.4 or (tooth and r + 0.4 < d <= r + 1.4) or d <= 1.2:
                bb.set(x + dx, y + dy, z, "minecraft:gold_block" if d <= 1.2 else "minecraft:iron_block")
            elif d <= r - 1.5 and (abs(dx) <= 0 or abs(dy) <= 0):
                bb.set(x + dx, y + dy, z, "minecraft:iron_block")


def clock(bb, x, y, z, r):
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            d = math.hypot(dx, dy)
            if d <= r + 0.3:
                bb.set(x + dx, y + dy, z, "minecraft:red_concrete" if d > r - 0.8 else "minecraft:white_concrete")
    for k in range(12):
        a = 2 * math.pi * k / 12
        bb.set(x + int(round((r - 1.3) * math.cos(a))), y + int(round((r - 1.3) * math.sin(a))), z, "minecraft:black_concrete") \
            if k % 3 == 0 else None
    for t in range(1, r - 1):
        bb.set(x, y + t, z, "minecraft:black_concrete")
    for t in range(1, r - 2):
        bb.set(x + t, y, z, "minecraft:black_concrete")


def interior(bb, tracker, audit, tops):
    x1, z1, x2, z2 = TOY
    y = GY + 1
    # show room: shelves of toys along the walls, toy figures, a carousel model, the wide stair down at the back
    for x in range(x1 + 2, x2 - 1):
        if x % 3 == 0:
            for z in (z1 + 1,):
                bb.set(x, y, z, "minecraft:spruce_planks"); bb.set(x, y + 1, z, f"minecraft:{COLORS[x % len(COLORS)]}_wool")
                bb.set(x, y + 2, z, "minecraft:spruce_slab[type=bottom]")
                bb.set(x, y + 3, z, f"minecraft:{COLORS[(x + 4) % len(COLORS)]}_carpet")
    for k, (tx, tz) in enumerate(((x1 + 6, z2 - 5), (x1 + 10, z2 - 6), (x2 - 6, z2 - 5), (x2 - 10, z2 - 6))):
        # toy soldiers and dolls: a block body with a little head
        bb.set(tx, y, tz, f"minecraft:{COLORS[k * 2 % len(COLORS)]}_wool")
        bb.set(tx, y + 1, tz, "minecraft:white_concrete_powder" if False else "minecraft:smooth_quartz_slab[type=bottom]")
    cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
    bb.cylinder(cx, y, cz, 3, y, "minecraft:yellow_concrete")
    bb.fill(cx, y + 1, cz, cx, y + 3, cz, "minecraft:gold_block")
    bb.cylinder(cx, y + 4, cz, 3, y + 4, "minecraft:red_concrete")
    for (ox, oz) in ((2, 0), (-2, 0), (0, 2), (0, -2)):
        bb.set(cx + ox, y + 1, cz + oz, "minecraft:white_wool")
        bb.fill(cx + ox, y + 2, cz + oz, cx + ox, y + 3, cz + oz, "minecraft:end_rod[facing=up]")
    # the wide stair down to the factory (6 wide, behind the carousel)
    sx1, sx2 = cx - 3, cx + 2
    for i in range(GY - FY):
        z = z1 + 2 + i
        bb.fill(sx1, GY - i, z, sx2, GY - i, z, st("minecraft:quartz_stairs", "north"))
        bb.fill(sx1, GY - i + 1, z, sx2, GY - i + 4, z, AIR)
        bb.fill(sx1 - 1, GY - i - 1, z, sx1 - 1, GY - i + 4, z, "minecraft:smooth_quartz")
        bb.fill(sx2 + 1, GY - i - 1, z, sx2 + 1, GY - i + 4, z, "minecraft:smooth_quartz")
    for x in range(sx1 - 1, sx2 + 2):
        bb.set(x, GY + 1, z1 + 2 + GY - FY, "minecraft:white_concrete") if False else None
    for x in (sx1 - 1, sx2 + 1):
        for z in range(z1 + 2, z1 + 3 + GY - FY):
            bb.set(x, GY + 1, z, "minecraft:quartz_slab[type=bottom]") if z < z1 + 3 + GY - FY - 1 else None
    # first floor: Sugar's grape room in the west half, the officers' lounge in the east
    y1 = GY + CUBE + 1
    for i in range(CUBE - 1):
        bb.set(x2 - 2, GY + 1 + i, z1 + 2 + i, st("minecraft:spruce_stairs", "south"))
        bb.fill(x2 - 2, GY + 2 + i, z1 + 2 + i, x2 - 2, GY + 5 + i, z1 + 2 + i, AIR)
    bb.fill(x2 - 2, y1 - 1, z1 + 2, x2 - 2, y1 - 1, z1 + 2 + CUBE - 1, AIR)
    bb.fill(x1 + 1, y1, cz, x2 - 1, y1 + CUBE - 3, cz, "minecraft:white_concrete")
    bb.fill(cx - 1, y1, cz, cx + 1, y1 + 2, cz, AIR)
    bb.fill(x1 + 2, y1 - 1, z1 + 1, cx - 1, y1 - 1, cz - 1, "minecraft:purple_wool")
    bb.fill(x1 + 2, y1 - 1, cz + 1, cx - 1, y1 - 1, z2 - 1, "minecraft:purple_wool")
    for (gx, gz) in ((x1 + 4, z1 + 3), (x1 + 8, z1 + 4), (x1 + 6, z2 - 4), (x1 + 12, z2 - 3)):
        bb.set(gx, y1, gz, "minecraft:dark_oak_fence")
        bb.set(gx, y1 + 1, gz, "minecraft:purple_concrete"); bb.set(gx + 1, y1 + 1, gz, "minecraft:magenta_concrete")
        bb.set(gx, y1 + 1, gz + 1, "minecraft:purple_concrete"); bb.set(gx, y1 + 2, gz, "minecraft:purple_concrete")
    bb.fill(x1 + 14, y1, z1 + 3, x1 + 16, y1, z1 + 5, "minecraft:purple_wool")
    bb.set(x1 + 15, y1 + 1, z1 + 4, "minecraft:cake")
    for x in range(cx + 3, x2 - 3, 6):
        # pink sofas round low tables
        bb.set(x, y1, cz - 4, "minecraft:dark_oak_fence"); bb.set(x, y1 + 1, cz - 4, "minecraft:pink_carpet")
        bb.set(x - 1, y1, cz - 4, st("minecraft:cherry_stairs", "east")); bb.set(x + 1, y1, cz - 4, st("minecraft:cherry_stairs", "west"))
        bb.set(x, y1, cz + 4, "minecraft:dark_oak_fence"); bb.set(x, y1 + 1, cz + 4, "minecraft:pink_carpet")
        bb.set(x - 1, y1, cz + 4, st("minecraft:cherry_stairs", "east")); bb.set(x + 1, y1, cz + 4, st("minecraft:cherry_stairs", "west"))
    bb.fill(cx + 2, y1 - 1, z1 + 1, x2 - 1, y1 - 1, z2 - 1, "minecraft:pink_wool")
    bb.fill(cx + 3, y1 - 1, z1 + 2, x2 - 2, y1 - 1, z2 - 2, "minecraft:magenta_wool") if False else None
    for k in range(4):
        bb.set(x1 + 5 + k * 10, y1 + CUBE - 3, cz + (2 if k % 2 else -2), "minecraft:lantern[hanging=true]")
        bb.set(x1 + 5 + k * 10, GY + CUBE - 1, cz + 3, "minecraft:lantern[hanging=true]")


# ------------------------------------------------------------------ underneath: the factory and the port
def factory(bb, tracker, audit):
    x1, z1, x2, z2 = FAC
    y = FY
    top = GY - 1
    bb.fill(x1 - 1, y - 4, z1 - 1, x2 + 1, top, z2 + 1, "minecraft:stone_bricks")
    bb.fill(x1, y + 1, z1, x2, top - 1, z2, AIR)
    bb.fill(x1, y, z1, x2, y, z2, "minecraft:polished_andesite")
    for x in range(x1 + 4, x2 - 2, 8):
        for z in (z1 + 8, z2 - 8):
            bb.fill(x, y + 1, z, x, top - 1, z, "minecraft:iron_block")
    # the conveyor lines: rails on smooth stone with hoppers and droppers, workbenches either side
    for z in (z1 + 4, z1 + 12, z2 - 12):
        bb.fill(x1 + 6, y + 1, z, x2 - 20, y + 1, z, "minecraft:smooth_stone")
        bb.fill(x1 + 6, y + 2, z, x2 - 20, y + 2, z, "minecraft:rail[shape=east_west]")
        for x in range(x1 + 8, x2 - 20, 6):
            bb.set(x, y + 3, z, "minecraft:hopper[facing=down]") if False else bb.set(x, y + 4, z, "minecraft:hopper[facing=down]")
            bb.set(x, y + 5, z, "minecraft:dropper[facing=down]")
            bb.set(x, y + 1, z - 1, "minecraft:crafting_table" if x % 12 == 0 else "minecraft:smithing_table")
            bb.set(x + 2, y + 1, z + 1, "minecraft:barrel[facing=up,open=false]")
    # vats along the east end
    for z in range(z1 + 3, z2 - 2, 5):
        bb.fill(x2 - 8, y + 1, z - 1, x2 - 6, y + 3, z + 1, "minecraft:iron_block")
        bb.fill(x2 - 7, y + 2, z, x2 - 7, y + 3, z, "minecraft:water") if False else bb.set(x2 - 7, y + 3, z, "minecraft:water_cauldron[level=3]")
        bb.set(x2 - 7, y + 4, z, "minecraft:chain[axis=y]"); bb.set(x2 - 7, y + 5, z, "minecraft:chain[axis=y]")
        bb.set(x2 - 3, y + 1, z, "minecraft:blast_furnace[facing=west,lit=true]")
    # crates of SMILE fruit stacked by the port
    for (cx, cz) in ((x1 + 3, z1 + 18), (x1 + 4, z1 + 18), (x1 + 3, z1 + 19), (x1 + 9, z2 - 2), (x1 + 10, z2 - 2), (x1 + 9, z2 - 3)):
        bb.set(cx, y + 1, cz, "minecraft:barrel[facing=up,open=false]")
        bb.set(cx, y + 2, cz, "minecraft:barrel[facing=up,open=false]") if (cx + cz) % 2 else None
    for x in range(x1 + 4, x2, 8):
        for z in (z1 + 4, z2 - 4, (z1 + z2) // 2):
            bb.set(x, top - 1, z, "minecraft:lantern[hanging=true]")
    # the dormitory: a long room on the south side with bunks
    dz1 = z2 + 2
    bb.fill(x1 + 20 - 1, y - 1, dz1 - 1, x1 + 50 + 1, y + 6, dz1 + 7, "minecraft:stone_bricks")
    bb.fill(x1 + 20, y, dz1, x1 + 50, y, dz1 + 6, "minecraft:spruce_planks")
    bb.fill(x1 + 20, y + 1, dz1, x1 + 50, y + 5, dz1 + 6, AIR)
    bb.fill(x1 + 34, y + 1, z2 + 1, x1 + 35, y + 2, z2 + 1, AIR)
    bb.fill(x1 + 34, y + 1, z2 + 2 - 1, x1 + 35, y + 2, z2 + 2 - 1, AIR)
    for x in range(x1 + 21, x1 + 50, 3):
        for (zz, f) in ((dz1, "north"), (dz1 + 6, "south")):
            # bunk: bed below, bed on top of a slab frame
            bb.set(x, y + 1, zz, f"minecraft:brown_bed[facing={'south' if f == 'north' else 'north'},part=head]")
            bb.set(x, y + 1, zz + (1 if f == "north" else -1), f"minecraft:brown_bed[facing={'south' if f == 'north' else 'north'},part=foot]")
            bb.set(x + 1, y + 1, zz, "minecraft:spruce_fence"); bb.set(x + 1, y + 2, zz, "minecraft:spruce_fence")
            bb.set(x, y + 3, zz, "minecraft:spruce_slab[type=bottom]")
            bb.set(x, y + 3, zz + (1 if f == "north" else -1), "minecraft:spruce_slab[type=bottom]")
    for x in range(x1 + 23, x1 + 50, 7):
        bb.set(x, y + 5, dz1 + 3, "minecraft:lantern[hanging=true]")
    return (x1 - 2, z1 - 2, x2 + 2, dz1 + 8)


def port(bb):
    """The trade port: the canal from the factory's west end to a barred sea gate in the shore, a quay with cargo."""
    x1, z1, x2, z2 = FAC
    y = FY
    gate_x = None
    for x in range(x1, -1, -1):
        if SHORE(np.array([[x]]), np.array([[CANAL_Z]]))[0, 0] < 1.5 or HMAP[x, CANAL_Z] <= 0:
            gate_x = x
            break
    gate_x = gate_x if gate_x is not None else 0
    for x in range(gate_x, x1 + 14):
        for z in range(CANAL_Z - 4, CANAL_Z + 5):
            hi = max(HMAP[min(x, N - 1), z] - 1, 6) if x < x1 else GY - 1
            if abs(z - CANAL_Z) <= 2:
                bb.fill(x, -4, z, x, 0, z, "minecraft:water")
                bb.set(x, -5, z, "minecraft:stone_bricks")
                bb.fill(x, 1, z, x, 6, z, AIR)
            elif abs(z - CANAL_Z) <= 3:
                bb.fill(x, -5, z, x, y, z, "minecraft:stone_bricks")
                bb.set(x, y, z, "minecraft:spruce_planks")
                bb.fill(x, y + 1, z, x, 6, z, AIR)
            else:
                bb.fill(x, -5, z, x, 6, z, "minecraft:stone_bricks")
            bb.set(x, 7, z, "minecraft:stone_bricks")
            if x < x1:
                bb.fill(x, 8, z, x, hi, z, "minecraft:stone") if hi >= 8 else None
        if (x - gate_x) % 6 == 3:
            bb.set(x, 6, CANAL_Z, "minecraft:lantern[hanging=true]")
    # the barred sea gate
    for z in range(CANAL_Z - 3, CANAL_Z + 4):
        bb.fill(gate_x + 1, 1, z, gate_x + 1, 6, z, "minecraft:iron_bars")
        bb.set(gate_x + 1, -1, z, "minecraft:iron_bars") if False else None
    bb.fill(gate_x, 7, CANAL_Z - 4, gate_x + 2, 8, CANAL_Z + 4, "minecraft:stone_bricks")
    # quay cargo and a moored barge
    for x in range(x1 + 2, x1 + 12, 2):
        bb.set(x, y + 1, CANAL_Z + 3, "minecraft:barrel[facing=up,open=false]")
        bb.set(x, y + 1, CANAL_Z - 3, "minecraft:chest[facing=north]" if False else "minecraft:barrel[facing=up,open=false]")
    bb.fill(x1 - 10, 0, CANAL_Z - 1, x1 - 3, 0, CANAL_Z + 1, "minecraft:spruce_planks")
    bb.fill(x1 - 10, 1, CANAL_Z - 1, x1 - 3, 1, CANAL_Z + 1, "minecraft:spruce_slab[type=bottom]")
    bb.fill(x1 - 9, 1, CANAL_Z, x1 - 4, 1, CANAL_Z, AIR)
    bb.set(x1 - 6, 1, CANAL_Z, "minecraft:barrel[facing=up,open=false]")
    return gate_x


# ------------------------------------------------------------------ the town
def town(bb, tracker, audit, rng, taken):
    k = 0
    for _ in range(6000):
        w, d = int(rng.integers(8, 12)), int(rng.integers(8, 11))
        x0, z0 = int(rng.integers(8, N - 8 - w)), int(rng.integers(PLATEAU_Z + 6, N - 8 - d))
        xs = np.arange(x0 - 1, x0 + w + 1)[:, None]; zs = np.arange(z0 - 1, z0 + d + 1)[None, :]
        if streets(xs, zs).any() or (~land(xs, zs)).any() or (SHORE(xs, zs) < 10).any():
            continue
        hs = HMAP[np.clip(xs, 0, N - 1), np.clip(zs, 0, N - 1)]
        if hs.max() - hs.min() > 2:
            continue
        box = (x0 - 1, z0 - 1, x0 + w, z0 + d)
        if any(box[0] <= r[2] and r[0] <= box[2] and box[1] <= r[3] and r[1] <= box[3] for r in taken):
            continue
        dz = {0: min(abs(z0 + d - s) for s in (110, 136)), 2: min(abs(z0 - s) for s in (114, 140)),
              3: min(abs(x0 + w - s) for s in (38, 78, 122)), 1: min(abs(x0 - s) for s in (42, 82, 126))}
        rot = min(dz, key=dz.get)
        mw, md = (w, d) if rot % 2 == 0 else (d, w)
        y = int(hs.max())
        roof = ROOFS[k % len(ROOFS)] if k % 4 else "flat:" + ("red", "yellow", "orange")[k % 3]
        m, top, au = house_module(seed_of("th", x0, z0), mw, md, int(rng.integers(2, 4)), roof, tracker, KINDS[k % len(KINDS)],
                                  pal=PALS[k % len(PALS)], timber=False, jetty=(k % 3 == 0), chimney=(k % 2 == 0))
        audit += au
        bb.fill(x0, y - 3, z0, x0 + w - 1, y, z0 + d - 1, "minecraft:cut_sandstone")
        place_house(bb, m, mw, md, x0, y, z0, rot)
        taken.append(box)
        k += 1
        if k >= 34:
            break
    print("houses:", k)
    for z in range(TOY[3] + 12, 158, 9):
        lamp_post(bb, 77, GY + 1, z); lamp_post(bb, 83, GY + 1, z)


def flowers(bb, rng, taken):
    """Flower beds: drifts of tulips, alliums, cornflowers and roses on the open ground."""
    n = 0
    fl = ["minecraft:red_tulip", "minecraft:orange_tulip", "minecraft:pink_tulip", "minecraft:white_tulip", "minecraft:allium",
          "minecraft:cornflower", "minecraft:poppy", "minecraft:oxeye_daisy"]
    for x in range(4, N - 4):
        for z in range(PLATEAU_Z + 4, N - 4):
            X, Z = np.array([[x]]), np.array([[z]])
            if not land(X, Z)[0, 0] or SHORE(X, Z)[0, 0] < 8 or GRAD[x, z] >= 2 or streets(X, Z)[0, 0]:
                continue
            if any(t[0] - 1 <= x <= t[2] + 1 and t[1] - 1 <= z <= t[3] + 1 for t in taken):
                continue
            v = NT.fbm(X, Z, 3450, 14)[0, 0]
            if v < 0.56:
                continue
            bb.set(x, hy(x, z) + 1, z, fl[int(NT.noise(X, Z, 3451, 6)[0, 0] * len(fl)) % len(fl)])
            n += 1
    print("flowers:", n)


def scenery(bb, rng, taken):
    k = 0
    for _ in range(4000):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        X, Z = np.array([[x]]), np.array([[z]])
        if not land(X, Z)[0, 0] or SHORE(X, Z)[0, 0] < 6 or GRAD[x, z] >= 2 or streets(X, Z)[0, 0]:
            continue
        if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken):
            continue
        P.tree(bb, x, hy(x, z) + 1, z, int(rng.integers(5, 9)), ("oak", "cherry", "birch", "acacia")[k % 4], rng)
        taken.append((x - 3, z - 3, x + 3, z + 3))
        k += 1
        if k >= 60:
            break
    print("trees:", k)


def design():
    bb = BigBuild(seed=3420, y_min=-14, y_max=80)
    tracker = P.PropTracker(3420)
    audit = []
    rng = np.random.default_rng(3420)
    terrain(bb)
    taken = [factory(bb, tracker, audit)]
    gate_x = port(bb)
    taken = [toy_house(bb, tracker, audit), (gate_x - 2, CANAL_Z - 6, FAC[0], CANAL_Z + 6)]
    town(bb, tracker, audit, rng, taken)
    flowers(bb, rng, taken)
    scenery(bb, rng, taken)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 3490, density=0.18, kinds=NT.PLANTS_MEADOW, flowers=NT.FLOWERS,
              mask=lambda X, Z: land(X, Z) & ~streets(X, Z))
    return bb, audit


def steady(b):
    """Sand and gravel with nothing solid under it would fall when the build generates: turn those into blocks that
    stay put."""
    import render
    for (x, y, z), s in list(b.blocks.items()):
        n = s.split("[")[0]
        if n.endswith(("gravel", "sand", "concrete_powder")) and "sandstone" not in n:
            below = b.blocks.get((x, y - 1, z))
            if below is None or render.shape_of(below) != "full":
                b.blocks[(x, y, z)] = "minecraft:coarse_dirt" if "gravel" in n else "minecraft:smooth_sandstone" if "sand" in n else \
                    n.replace("concrete_powder", "concrete")


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    steady(b)
    x1, z1, x2, z2 = TOY
    b.chest(x2 - 3, GY + CUBE + 1, z1 + 3, "medium", "west")
    b.chest(FAC[2] - 3, FY + 1, FAC[1] + 2, "easy", "west")
    b.guards("donquixote", (((x1 + x2) // 2 - 3, z2 + 4), ((x1 + x2) // 2 + 3, z2 + 4), (x1 + 6, z2 - 3)), y=GY + 1)
    b.guards("donquixote", ((FAC[0] + 10, FAC[1] + 8), (FAC[0] + 40, FAC[1] + 16)), y=FY + 1)
    return b, 0
