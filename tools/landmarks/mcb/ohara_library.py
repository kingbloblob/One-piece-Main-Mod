"""Ohara v2, the island of archaeologists before the Buster Call, redesigned with the Minecraft Builder skill.

A green island with the sea on the east. In its middle the Tree of Knowledge, a giant tree 5,000 years old, hollowed
into the world's greatest library: a great doorway in the roots, bookshelves lining the inside of the trunk from the
floor up through six galleries joined by a stair that winds up the trunk wall, reading tables, lecterns, globes and
map tables on every level, the scholars' study, and the domed reading room under the crown, lit through a glass
cupola. Huge boughs carry the crown far out over the island. Round it the scholars' village of white houses with
blue roofs, lanes of pale stone, a little plaza with a well; the harbour with its quay, fishing boats and a
lighthouse on the east shore; and on the north-west cliff, the lone tree and the bench where young Robin read.
160 x 160. y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, furnish, set_if_air, house_module, place_house, lamp_post
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "ohara_library"
TITLE = "Ohara (Tree of Knowledge)"
CUTS = [8, 27, 63]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 160
SHORE = NT.outline(76, 80, 70, 2120, wobble=0.1)
TX, TZ = 70, 76
GY = 4
TOP = 66
GAL = 9                                   # gallery spacing
GALS = [GY + GAL * k for k in range(6)]    # floor of each level (ground + five galleries)
DOME_Y = GY + GAL * 6                      # the domed reading room floor
LOG = "minecraft:oak_log"
WOOD = "minecraft:oak_wood"
PLANK = "minecraft:spruce_planks"
LEAVES = ["minecraft:oak_leaves[distance=7,persistent=true,waterlogged=false]",
          "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]",
          "minecraft:azalea_leaves[distance=7,persistent=true,waterlogged=false]"]
VIL = (100, 40, 140, 112)
CLIFF = (30, 28)

MEADOW = NT.MEADOW
SAND = [("minecraft:sand", 0.7), ("minecraft:sandstone", 0.1), ("minecraft:gravel", 0.1), ("minecraft:clay", 0.1)]
ROCK = [("minecraft:stone", 0.4), ("minecraft:andesite", 0.18), ("minecraft:diorite", 0.12), ("minecraft:calcite", 0.1),
        ("minecraft:cobblestone", 0.1), ("minecraft:mossy_cobblestone", 0.1)]
LANE = [("minecraft:smooth_sandstone", 0.25), ("minecraft:cut_sandstone", 0.15), ("minecraft:calcite", 0.2),
        ("minecraft:diorite", 0.15), ("minecraft:dirt_path", 0.15), ("minecraft:polished_diorite", 0.1)]


def rect_d(X, Z, r):
    dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0)
    dz = np.maximum(np.maximum(r[1] - Z, Z - r[3]), 0)
    return np.hypot(dx, dz)


def seg_d(X, Z, a, b):
    ax, az = a; bx, bz = b
    vx, vz = bx - ax, bz - az
    t = np.clip(((X - ax) * vx + (Z - az) * vz) / float(vx * vx + vz * vz), 0, 1)
    return np.hypot(X - ax - t * vx, Z - az - t * vz)


LANES = [((TX, TZ + 20), (TX, 104)), ((TX, 104), (VIL[0], 104)), ((VIL[0], 76), (TX + 20, 76)), ((TX - 10, TZ - 16), (CLIFF[0] + 6, CLIFF[1] + 6)),
         ((VIL[0] + 20, VIL[1]), (VIL[0] + 20, VIL[3])), ((VIL[0], 58), (VIL[2], 58)), ((VIL[0], 92), (VIL[2] + 4, 92))]


def lane_d(X, Z):
    d = np.full(np.broadcast(X, Z).shape, 1e9)
    for a, b in LANES:
        d = np.minimum(d, seg_d(X, Z, a, b))
    return d


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = SHORE(X, Z)
    h = GY + NT.fbm(X, Z, 2121, 26) * 5 - 1.5
    h = h + 9 * np.exp(-((X - CLIFF[0]) ** 2 + (Z - CLIFF[1]) ** 2) / (2 * 16.0 ** 2))
    west = np.clip((70 - X) / 30.0, 0, 1) * np.clip((80 - Z) / 30.0, 0, 1)
    k = 3 * west + 10 * (1 - west)
    h = h * np.clip((d - 1.5) / k, 0, 1)
    for r in (VIL, (TX - 30, TZ - 30, TX + 30, TZ + 30)):
        w = np.clip(rect_d(X, Z, r) / 10.0, 0, 1)
        h = GY * (1 - w) + h * w
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
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SAND, 2131,
             mask=lambda X, Z: land(X, Z) & (height(X, Z) <= 1) & ~steep(X, Z), under="minecraft:sandstone", core="minecraft:sandstone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, ROCK, 2132, mask=lambda X, Z: land(X, Z) & steep(X, Z), under="minecraft:stone",
             core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, MEADOW, 2133, mask=lambda X, Z: land(X, Z) & (height(X, Z) > 1) & ~steep(X, Z),
             core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, LANE, 2134,
             mask=lambda X, Z: land(X, Z) & (height(X, Z) > 1) & (lane_d(X, Z) <= 1.6 + NT.noise(X, Z, 2135, 3)), core="minecraft:stone")
    for y in range(-12, 0):
        bb.fill_where(0, y, 0, N - 1, y, N - 1, lambda X, yy, Z: (SHORE(X, Z) <= 1.5) &
                      (yy > -2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10)), "minecraft:water")
        bb.fill_where(0, y, 0, N - 1, y, N - 1, lambda X, yy, Z: (SHORE(X, Z) <= 1.5) &
                      (yy == np.round(-2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10))), "minecraft:sand")


# ------------------------------------------------------------------ the Tree of Knowledge
def trunk_r(y, a):
    t = max(0, y - GY)
    base = 17 - 3 * t / TOP + 7 * math.exp(-t / 4.0)
    return base * (1 + 0.07 * np.sin(5 * a + y * 0.07) + 0.05 * np.sin(8 * a - y * 0.04) + 0.03 * np.sin(3 * a + 1))


def ring(bb, y, f, block, R=26, only_empty=False):
    bb.fill_where(TX - R, y, TZ - R, TX + R, y, TZ + R, lambda X, yy, Z: f(np.hypot(X - TX, Z - TZ), np.arctan2(Z - TZ, X - TX)),
                  block, only_empty=only_empty)


def trunk(bb, tracker, audit, rng):
    for y in range(GY - 4, TOP + 1):
        ring(bb, y, lambda d, a, y=y: d <= trunk_r(y, a), LOG + "[axis=y]")
        if GY + 1 <= y < TOP - 3:
            ring(bb, y, lambda d, a, y=y: d <= trunk_r(y, a) - 3, AIR)
    # floors: the ground floor (full), the gallery rings, the domed reading room floor (full)
    ring(bb, GY, lambda d, a: d <= trunk_r(GY, a) - 2.5, "minecraft:dark_oak_planks")
    for k, gy in enumerate(GALS[1:]):
        ring(bb, gy, lambda d, a, gy=gy: (d <= trunk_r(gy, a) - 2.5) & (d > trunk_r(gy, a) - 8), PLANK)
        ring(bb, gy + 1, lambda d, a, gy=gy: np.abs(d - (trunk_r(gy, a) - 8)) < 0.6, "minecraft:dark_oak_fence")
    ring(bb, DOME_Y, lambda d, a: d <= trunk_r(DOME_Y, a) - 2.5, "minecraft:dark_oak_planks")
    # bookshelves round the inner wall of every level, with gaps for windows; lanterns on the gallery rails
    for k, gy in enumerate(GALS):
        def shelf(d, a, gy=gy):
            r = trunk_r(gy, a) - 3
            return (d > r - 1.3) & (d <= r) & (((a + 3.2) * 7).astype(int) % 6 != 0)
        for yy in range(gy + 1, gy + GAL - 1):
            ring(bb, yy, shelf, "minecraft:bookshelf" if (yy + k) % 4 else "minecraft:chiseled_bookshelf[facing=north,slot_0_occupied=true,slot_1_occupied=true,slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=true,slot_5_occupied=false]", only_empty=True)
        # windows (knot holes) through the trunk at the gaps
        for j in range(6):
            a = (j * 6 + 3) / 7.0 - 3.2 + 0.05
            r = trunk_r(gy + 3, a)
            for t in np.linspace(r - 4, r + 1, 8):
                x, z = round(TX + t * math.cos(a)), round(TZ + t * math.sin(a))
                bb.fill(x, gy + 3, z, x, gy + 5, z, AIR)
        # tables, lecterns and globes on the galleries
        for j in range(5):
            a = j * 2 * math.pi / 5 + k * 0.6
            r = trunk_r(gy, a) - 5.5
            x, z = round(TX + r * math.cos(a)), round(TZ + r * math.sin(a))
            if k == 0:
                continue
            set_if_air(bb, x, gy + 1, z, "minecraft:lectern[facing=north,has_book=false,powered=false]" if j % 2 else "onepiece:chart_table[facing=north]")
    # the ground floor: reading tables round a great map table and a globe, the scholars' study behind
    gy = GY
    for j in range(8):
        a = j * math.pi / 4 + 0.3
        for r in (6, 10):
            x, z = round(TX + r * math.cos(a)), round(TZ + r * math.sin(a))
            bb.set(x, gy + 1, z, "minecraft:dark_oak_fence")
            bb.set(x, gy + 2, z, "minecraft:dark_oak_pressure_plate")
            bb.set(x + 1, gy + 1, z, st("minecraft:dark_oak_stairs", "west"))
            bb.set(x - 1, gy + 1, z, st("minecraft:dark_oak_stairs", "east"))
            set_if_air(bb, x, gy + 3, z, "minecraft:candle[candles=3,lit=true]") if False else None
    # free-standing bookcases running out from the wall like spokes, three high, aisles between
    for j in range(14):
        a = j * 2 * math.pi / 14 + 0.12
        if abs(((a - math.pi / 2) + math.pi) % (2 * math.pi) - math.pi) < 0.5:
            continue                                                     # keep the way in from the door clear
        for r in np.arange(12.5, trunk_r(gy, a) - 5.5, 0.5):
            x, z = round(TX + r * math.cos(a)), round(TZ + r * math.sin(a))
            bb.fill(x, gy + 1, z, x, gy + 3, z, "minecraft:bookshelf")
    bb.fill(TX - 2, gy + 1, TZ - 2, TX + 2, gy + 1, TZ + 2, "minecraft:dark_oak_planks")
    bb.fill(TX - 1, gy + 2, TZ - 1, TX + 1, gy + 2, TZ + 1, "minecraft:dark_oak_slab[type=bottom]")
    # a globe: a blue and green ball on a stand
    gx, gz = TX, TZ - 7
    bb.set(gx, gy + 1, gz, "minecraft:dark_oak_fence")
    bb.fill_where(gx - 2, gy + 2, gz - 2, gx + 2, gy + 6, gz + 2,
                  lambda X, yy, Z: (X - gx) ** 2 + (yy - gy - 4) ** 2 + (Z - gz) ** 2 <= 4.2,
                  "minecraft:light_blue_concrete")
    for (dx, dy, dz) in ((1, 0, 0), (0, 1, 1), (-1, -1, 0), (0, 0, -1)):
        bb.set(gx + dx, gy + 4 + dy, gz + dz, "minecraft:lime_concrete")
    # the stair winding up the inside of the trunk wall (two wide) from the ground floor to the reading room
    th, y = math.pi / 2 + 0.5, GY + 1
    while y <= DOME_Y:
        R = trunk_r(y, th) - 4.5
        for w in (0.0, 1.0):
            x, z = round(TX + (R - w) * math.cos(th)), round(TZ + (R - w) * math.sin(th))
            tx, tz = -math.sin(th), math.cos(th)
            f = ("east" if tx > 0 else "west") if abs(tx) > abs(tz) else ("south" if tz > 0 else "north")
            bb.fill(x, y + 1, z, x, y + 4, z, AIR)
            bb.set(x, y, z, f"minecraft:spruce_stairs[facing={f},half=bottom]")
            bb.set(x, y - 1, z, PLANK)
        th += 1.15 / R
        y += 1
    # chandeliers down the middle of the hollow
    for gy in GALS[1:]:
        bb.fill(TX, gy + 2, TZ, TX, gy + GAL - 1, TZ, "minecraft:chain")
        bb.set(TX, gy + 1, TZ, "minecraft:lantern[hanging=true]")
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            bb.set(TX + dx, gy + 2, TZ + dz, "minecraft:dark_oak_fence")
            bb.set(TX + dx, gy + 1, TZ + dz, "minecraft:lantern[hanging=true]")
    # the domed reading room: a glass cupola through the trunk top, a ring of desks, Clover's chair
    for k in range(10):
        rr = 9 * math.cos(math.asin(min(1, k / 10)))
        ring(bb, TOP - 3 + k, lambda d, a, rr=rr: d <= rr, "minecraft:glass")
        ring(bb, TOP - 3 + k, lambda d, a, rr=rr: d <= rr - 1.2, AIR)
    ring(bb, TOP - 3, lambda d, a: d <= 8, AIR)
    for j in range(10):
        a = j * math.pi / 5
        r = trunk_r(DOME_Y, a) - 6
        x, z = round(TX + r * math.cos(a)), round(TZ + r * math.sin(a))
        bb.set(x, DOME_Y + 1, z, "onepiece:dark_oak_table[facing=north]")
        bb.set(x, DOME_Y + 2, z, "minecraft:candle[candles=2,lit=true]")
    bb.fill(TX - 1, DOME_Y + 1, TZ - 1, TX + 1, DOME_Y + 1, TZ + 1, "minecraft:red_carpet")
    bb.set(TX, DOME_Y + 1, TZ - 3, st("minecraft:dark_oak_stairs", "south"))
    # the great doorway in the roots (south) with a lantern either side
    for y in range(GY + 1, GY + 10):
        hw = 3 if y <= GY + 6 else int(round(math.sqrt(max(0, 9 - (y - GY - 6) ** 2 * 1.5))))
        if hw:
            bb.fill(TX - hw, y, TZ + 8, TX + hw, y, TZ + 24, AIR)
    bb.fill(TX - 3, GY, TZ + 8, TX + 3, GY, TZ + 24, "minecraft:dark_oak_planks")
    for dx in (-4, 4):
        bb.set(TX + dx, GY + 4, TZ + int(trunk_r(GY + 4, math.pi / 2)) + 1, "minecraft:lantern[hanging=false]") if False else None
    # the scholars' study: a room built into the trunk wall on the ground floor (north side)
    sx1, sz1, sx2, sz2 = TX - 5, TZ - 16, TX + 5, TZ - 10
    bb.fill(sx1, GY + 1, sz1, sx2, GY + 5, sz2, AIR)
    bb.fill(sx1, GY, sz1, sx2, GY, sz2, "minecraft:dark_oak_planks")
    furnish(bb, [(sx1, sz1, sx2, sz2)], GY + 1, 4, ["library"], seed_of("ohstudy"), tracker, doors=[(TX, sz2 + 1)], wood="dark_oak",
            audit=audit)
    return (TX - 24, TZ - 24, TX + 24, TZ + 26)


def branch(bb, x0, y0, z0, a, L, rise, r0):
    tips = []
    for s in range(L):
        t = s / L
        x, z = x0 + s * math.cos(a), z0 + s * math.sin(a)
        y = y0 + s * rise - 5 * t * t
        r = r0 * (1 - 0.65 * t)
        R = int(r) + 1
        ax = "x" if abs(math.cos(a)) > 0.7 else "z" if abs(math.sin(a)) > 0.7 else "y"
        bb.fill_where(int(x) - R, int(y) - R, int(z) - R, int(x) + R, int(y) + R, int(z) + R,
                      lambda X, Y, Z, x=x, y=y, z=z, r=r: (X - x) ** 2 + (Y - y) ** 2 + (Z - z) ** 2 <= r * r, LOG + f"[axis={ax}]")
        if s > L * 0.45 and s % 6 == 0:
            tips.append((round(x), round(y), round(z)))
    tips.append((round(x0 + L * math.cos(a)), round(y0 + L * rise - 5), round(z0 + L * math.sin(a))))
    return tips


def leaf_cloud(bb, x, y, z, r, k):
    R = int(r) + 1
    seed = int(x * 31 + z * 17 + y)

    def f(X, Y, Z):
        return ((X - x) ** 2 + ((Y - y) * 1.7) ** 2 + (Z - z) ** 2 <= r * r) & (NT.noise(X * 2 + Y, Z * 2, seed, 3) > 0.2)
    bb.fill_where(x - R, y - R // 2 - 2, z - R, x + R, y + R // 2 + 2, z + R, f, LEAVES[k % 2], only_empty=True)
    bb.fill_where(x - R, y - R // 2 - 2, z - R, x + R, y + R // 2 + 2, z + R,
                  lambda X, Y, Z: f(X, Y, Z) & (NT.noise(X, Z + Y * 3, seed + 1, 4) > 0.75), LEAVES[2])


def crown(bb, rng):
    tips = []
    for k in range(8):
        a = k * 2 * math.pi / 8 + rng.uniform(-0.25, 0.25)
        y0 = TOP - 16 + int(rng.integers(0, 10))
        r = trunk_r(y0, a) - 2
        L = int(rng.integers(26, 38))
        tips += branch(bb, TX + r * math.cos(a), y0, TZ + r * math.sin(a), a, L, rng.uniform(0.22, 0.4), rng.uniform(2.6, 3.6))
    for k, (x, y, z) in enumerate(tips):
        leaf_cloud(bb, min(max(x, 10), N - 11), y + 3, min(max(z, 10), N - 11), rng.uniform(7, 10), k)
    for k in range(7):
        a = k * 2 * math.pi / 7 + 0.4
        leaf_cloud(bb, round(TX + 15 * math.cos(a)), TOP + 4, round(TZ + 15 * math.sin(a)), 11, k)


def roots(bb, rng):
    for k in range(8):
        a = k * 2 * math.pi / 8 + 0.4 + rng.uniform(-0.15, 0.15)
        if abs(((a - math.pi / 2) + math.pi) % (2 * math.pi) - math.pi) < 0.4:
            continue
        r0 = trunk_r(GY + 3, a) - 2
        L = int(rng.integers(14, 24))
        peak = rng.uniform(4, 8)
        for s in range(L):
            t = s / L
            x = TX + (r0 + s) * math.cos(a)
            z = TZ + (r0 + s) * math.sin(a)
            y = hy(int(x), int(z)) + peak * math.sin(math.pi * min(1, t * 1.1)) - 2 * t
            r = 3.2 * (1 - 0.6 * t)
            R = int(r) + 1
            bb.fill_where(int(x) - R, int(y) - R, int(z) - R, int(x) + R, int(y) + R, int(z) + R,
                          lambda X, Y, Z, x=x, y=y, z=z, r=r: (X - x) ** 2 + ((Y - y) * 1.2) ** 2 + (Z - z) ** 2 <= r * r, WOOD)


# ------------------------------------------------------------------ the scholars' village, harbour, cliff
PAL = dict(walls=["minecraft:white_concrete", "minecraft:calcite", "minecraft:white_terracotta"], frame="minecraft:stripped_birch_log",
           base=["minecraft:stone_bricks", "minecraft:cobblestone", "minecraft:mossy_cobblestone"], floor="minecraft:birch_planks",
           wood="birch", chimney="minecraft:stone_bricks")
ROOFS = ["minecraft:waxed_oxidized_cut_copper_stairs", "minecraft:dark_prismarine_stairs", "minecraft:waxed_weathered_cut_copper_stairs",
         "minecraft:prismarine_brick_stairs"]
KINDS = [["library", "bedroom"], ["kitchen", "library"], ["living", "bedroom"], ["library", "living", "bedroom"], ["workshop", "bedroom"]]


def village(bb, tracker, audit, rng):
    taken = []
    k = 0
    for (x, z, w, d, fl, rot) in ((102, 44, 9, 8, 2, 0), (114, 43, 8, 8, 2, 0), (126, 44, 10, 8, 2, 0),
                                  (102, 62, 9, 8, 2, 2), (126, 62, 9, 8, 3, 2), (102, 80, 10, 9, 2, 0),
                                  (126, 80, 9, 8, 2, 0), (102, 96, 9, 8, 2, 2), (126, 96, 10, 8, 2, 2), (88, 108, 8, 8, 1, 2),
                                  (84, 44, 8, 8, 2, 3)):
        if SHORE(np.array([[x + w // 2]]), np.array([[z + d // 2]]))[0, 0] < 6:
            continue
        mod, _, au = house_module(seed_of("ohv", k), w, d, fl, ROOFS[k % len(ROOFS)], tracker, KINDS[k % len(KINDS)], pal=PAL,
                                  timber=(k % 3 == 1), jetty=False)
        audit += au
        y = hy(x + w // 2, z + d // 2)
        place_house(bb, mod, w, d, x, y, z, rot)
        ww, dd = (w, d) if rot % 2 == 0 else (d, w)
        taken.append((x - 1, z - 1, x + ww, z + dd))
        k += 1
    # the plaza with the well
    px, pz = 120, 76
    NT.cover(bb, px - 6, pz - 4, px + 6, pz + 4, lambda X, Z: X * 0 + hy(px, pz), LANE, 2141)
    bb.fill(px - 1, GY + 1, pz - 1, px + 1, GY + 1, pz + 1, "minecraft:stone_brick_wall")
    bb.fill(px, GY - 6, pz, px, GY + 1, pz, "minecraft:water")
    for (x, z) in ((px - 1, pz - 1), (px + 1, pz + 1)):
        bb.fill(x, GY + 2, z, x, GY + 3, z, "minecraft:birch_fence")
    bb.fill(px - 1, GY + 4, pz - 1, px + 1, GY + 4, pz + 1, "minecraft:dark_prismarine_slab[type=bottom]")
    for (x, z) in ((px - 6, pz - 4), (px + 6, pz + 4), (px - 6, pz + 4), (px + 6, pz - 4)):
        lamp_post(bb, x, GY + 1, z, post="minecraft:birch_fence", h=3)
    taken.append((px - 7, pz - 5, px + 7, pz + 5))
    return taken


def harbour(bb, rng):
    """A stone quay on the east shore with bollards, fishing boats, nets and the lighthouse on the point."""
    z1, z2 = 60, 100
    xs = {}
    for z in range(z1, z2 + 1):
        x = 150
        while x > 90 and hy(x, z) < 1:
            x -= 1
        xs[z] = x
        bb.fill(x - 2, -6, z, x, GY, z, "minecraft:stone_bricks")
        bb.set(x, GY + 1, z, "minecraft:stone_brick_wall") if z % 6 == 0 else None
    for pz in (68, 90):
        x0 = xs[pz]
        for x in range(x0 + 1, x0 + 18):
            bb.fill(x, GY - 1, pz - 1, x, GY - 1, pz + 1, PLANK)
            if x % 4 == 0:
                bb.fill(x, -8, pz - 2, x, GY - 1, pz - 2, "minecraft:spruce_log[axis=y]")
                bb.fill(x, -8, pz + 2, x, GY - 1, pz + 2, "minecraft:spruce_log[axis=y]")
                bb.set(x, GY, pz + 2, "minecraft:lantern[hanging=false]")
        for (bx, bz) in ((x0 + 6, pz + 5), (x0 + 12, pz - 6)):
            L = 7
            for i in range(L):
                for j in (-1, 0, 1):
                    end = i in (0, L - 1)
                    if end and j:
                        continue
                    if j == 0 and not end:
                        bb.set(bx + i, 0, bz, "minecraft:oak_planks")
                    else:
                        bb.set(bx + i, 0, bz + j, "minecraft:oak_planks")
                        bb.set(bx + i, 1, bz + j, st("minecraft:oak_stairs", "north" if j > 0 else "south") if j else "minecraft:oak_planks")
            bb.set(bx + 3, 1, bz, "minecraft:barrel[facing=up,open=false]")
    # the lighthouse on the south point of the harbour
    lx, lz = xs[z2] + 4, z2 + 6
    y = max(1, hy(lx, lz))
    bb.fill(lx - 4, -6, lz - 4, lx + 4, y, lz + 4, "minecraft:stone_bricks")
    for k in range(22):
        r = 3.6 - k * 0.05
        blk = "minecraft:white_concrete" if (k // 4) % 2 == 0 else "minecraft:blue_concrete"
        bb.fill_where(lx - 4, y + 1 + k, lz - 4, lx + 4, y + 1 + k, lz + 4, lambda X, yy, Z, r=r: np.hypot(X - lx, Z - lz) <= r, blk)
        bb.fill_where(lx - 4, y + 1 + k, lz - 4, lx + 4, y + 1 + k, lz + 4, lambda X, yy, Z, r=r: np.hypot(X - lx, Z - lz) <= r - 1.2, AIR)
    bb.fill(lx - 1, y + 1, lz + 3, lx, y + 2, lz + 3, AIR)
    bb.fill(lx - 2, y + 1, lz - 2, lx - 2, y + 22, lz - 2, "minecraft:ladder[facing=east]")
    bb.fill(lx - 4, y + 23, lz - 4, lx + 4, y + 23, lz + 4, "minecraft:stone_bricks")
    bb.fill(lx - 2, y + 24, lz - 2, lx + 2, y + 26, lz + 2, "minecraft:glass")
    bb.fill(lx - 1, y + 24, lz - 1, lx + 1, y + 26, lz + 1, AIR)
    bb.set(lx, y + 24, lz, "minecraft:sea_lantern")
    bb.fill(lx - 2, y + 27, lz - 2, lx + 2, y + 27, lz + 2, "minecraft:blue_concrete")
    bb.set(lx, y + 28, lz, "minecraft:lightning_rod")
    bb.fill(lx - 4, y + 24, lz - 4, lx + 4, y + 24, lz + 4, "minecraft:iron_bars", only_empty=True) if False else None
    return (xs[z1] - 3, z1 - 2, N, z2 + 12)


def cliff(bb, rng):
    """Robin's reading spot: the lone tree on the north-west cliff with a bench and a stack of books."""
    x, z = CLIFF
    y = hy(x, z)
    P.tree(bb, x, y + 1, z, 9, "oak", rng)
    for dx in (2, 3):
        bb.set(x + dx, y + 1, z + 3, st("minecraft:spruce_stairs", "north"))
    bb.set(x + 4, y + 1, z + 3, "minecraft:bookshelf")
    bb.set(x + 4, y + 2, z + 3, "minecraft:lectern[facing=west,has_book=false,powered=false]") if False else None
    return (x - 6, z - 6, x + 8, z + 8)


def scenery(bb, rng, taken):
    k = 0
    for _ in range(5000):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        X, Z = np.array([[x]]), np.array([[z]])
        if SHORE(X, Z)[0, 0] < 6 or GRAD[x, z] >= 2 or lane_d(X, Z)[0, 0] < 3:
            continue
        if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken):
            continue
        if NT.noise(X, Z, 2171, 20)[0, 0] < 0.4 and rng.random() < 0.7:
            continue
        P.tree(bb, x, hy(x, z) + 1, z, int(rng.integers(6, 10)), ("oak", "birch", "oak", "spruce")[k % 4], rng)
        taken.append((x - 3, z - 3, x + 3, z + 3))
        k += 1
        if k >= 55:
            break
    print("trees:", k)


def design():
    bb = BigBuild(seed=2120, y_min=-14, y_max=110)
    tracker = P.PropTracker(2120)
    audit = []
    rng = np.random.default_rng(2120)
    terrain(bb)
    roots(bb, rng)
    taken = [trunk(bb, tracker, audit, rng)]
    crown(bb, rng)
    taken += village(bb, tracker, audit, rng)
    taken.append(harbour(bb, rng))
    taken.append(cliff(bb, rng))
    scenery(bb, rng, taken)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 2190, density=0.28, kinds=NT.PLANTS_MEADOW, flowers=NT.FLOWERS,
              mask=lambda X, Z: land(X, Z) & (lane_d(X, Z) > 2.5))
    return bb, audit


def steady(b):
    """Sand and gravel with nothing solid under it would fall when the build generates (at sea the world's water
    fills in under it): turn those into blocks that stay put."""
    import render
    for (x, y, z), s in list(b.blocks.items()):
        n = s.split("[")[0]
        if n.endswith(("gravel", "sand", "concrete_powder")) and "sandstone" not in n:
            below = b.blocks.get((x, y - 1, z))
            if (below is None and y >= 0) or (below is not None and render.shape_of(below) != "full"):
                b.blocks[(x, y, z)] = "minecraft:coarse_dirt" if "gravel" in n else "minecraft:smooth_sandstone" if "sand" in n else \
                    n.replace("concrete_powder", "concrete")


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    steady(b)
    b.npc(TX - 5, GY + 1, TZ + 2, "robin", False)
    b.chest(TX + 6, GY + 1, TZ + 5, "library", "west")
    b.chest(TX - 4, DOME_Y + 1, TZ + 4, "library", "east")
    b.chest(TX + 3, GY + 1, TZ - 14, "medium", "west")
    return b, 0
