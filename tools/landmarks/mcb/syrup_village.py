"""Syrup Village v2, Usopp's home village on the Gecko Islands, redesigned with the Minecraft Builder skill.

A green farming island. On the hill to the north-east, behind its wall and iron gate, Kaya's grand white mansion: a
main block of three storeys with two forward wings round a gravel court, a garden with the fountain, hedges and
roses (entrance hall, dining room, library, Kaya's bedroom, servants' quarters, all furnished). Below it the village
on its level ground: plaster and timber cottages round a little green with the well, the inn, Usopp's house, the
bakery and the farm; fields and the orchard to the south; the Usopp Pirates' hideout in a big hollow tree at the edge
of the wood. On the north the coast rises to cliffs, and the famous slope road climbs from the little cove (where
the Going Merry lies at anchor) up to the village. 160 x 160. y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, furnish, set_if_air, cornice, tier, wing_floor, \
    house_module, place_house, lamp_post
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.shipstamp import stamp_ship

SID = "syrup_village"
TITLE = "Syrup Village (Kaya's Mansion)"
CUTS = [5, 13, 19]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 160
_SH1 = NT.outline(80, 84, 70, 1620, wobble=0.1)
_SH2 = NT.outline(116, 48, 40, 1625, wobble=0.08)


def SHORE(X, Z):
    return np.maximum(_SH1(X, Z), _SH2(X, Z))
VIL = (34, 66, 104, 122)            # the village ground, level at VY
VY = 4
MAN = (88, 24, 140, 72)             # the mansion grounds, level at MY
MY = 11
COVE = (30, 22)                     # the cove the slope road climbs from

ROAD = [("minecraft:dirt_path", 0.5), ("minecraft:coarse_dirt", 0.2), ("minecraft:gravel", 0.15), ("minecraft:packed_mud", 0.15)]
SAND = [("minecraft:sand", 0.72), ("minecraft:gravel", 0.1), ("minecraft:sandstone", 0.08), ("minecraft:clay", 0.10)]
ROCK = [("minecraft:stone", 0.42), ("minecraft:andesite", 0.2), ("minecraft:tuff", 0.12), ("minecraft:cobblestone", 0.1),
        ("minecraft:mossy_cobblestone", 0.1), ("minecraft:gravel", 0.06)]


def rect_d(X, Z, r):
    dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0)
    dz = np.maximum(np.maximum(r[1] - Z, Z - r[3]), 0)
    return np.hypot(dx, dz)


def seg_d(X, Z, a, b):
    ax, az = a; bx, bz = b
    vx, vz = bx - ax, bz - az
    t = np.clip(((X - ax) * vx + (Z - az) * vz) / float(vx * vx + vz * vz), 0, 1)
    return np.hypot(X - ax - t * vx, Z - az - t * vz), t


ROAD_PTS = [(COVE[0] + 4, COVE[1] + 8), (46, 40), (58, 56), (66, 68)]


def road_d(X, Z):
    d = np.full(np.broadcast(X, Z).shape, 1e9)
    for a, b in zip(ROAD_PTS, ROAD_PTS[1:]):
        d = np.minimum(d, seg_d(X, Z, a, b)[0])
    return d


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = SHORE(X, Z)
    hill = 4 + 7 * np.exp(-((X - 118) ** 2 + (Z - 46) ** 2) / (2 * 30.0 ** 2)) + NT.fbm(X, Z, 1621, 26) * 4 - 1
    # the cove: low ground round it, the road climbing out of it
    cw = np.clip(1 - np.hypot(X - COVE[0], Z - COVE[1]) / 34.0, 0, 1)
    hill = hill * (1 - cw) + cw * np.clip(np.hypot(X - COVE[0], Z - COVE[1]) / 34.0 * 4, 0.6, 4)
    # cliffs on the north and east coasts, gentle beaches to the south and west and in the cove
    north = np.clip((60 - Z) / 20.0, 0, 1) * (1 - cw)
    k = 3 * north + 12 * (1 - north)
    h = hill * np.clip((d - 1.5) / k, 0, 1)
    # level the village and the mansion grounds
    w = np.clip(rect_d(X, Z, VIL) / 10.0, 0, 1)
    h = VY * (1 - w) + h * w
    w = np.clip(rect_d(X, Z, MAN) / 9.0, 0, 1)
    h = MY * (1 - w) + h * w
    # the road: a smooth ramp from the cove beach to the village
    rd = road_d(X, Z)
    t = np.zeros_like(rd)
    best = np.full(rd.shape, 1e9)
    L = [math.dist(a, b) for a, b in zip(ROAD_PTS, ROAD_PTS[1:])]
    acc = 0.0
    for (a, b), l in zip(zip(ROAD_PTS, ROAD_PTS[1:]), L):
        dd, tt = seg_d(X, Z, a, b)
        m = dd < best
        t = np.where(m, (acc + tt * l) / sum(L), t)
        best = np.minimum(best, dd)
        acc += l
    ry = 0.6 + t * (VY - 0.6)
    rw = np.clip((rd - 2.5) / 5.0, 0, 1)
    h = ry * (1 - rw) + h * rw
    h = np.where(d < 1.5, -1, h)
    return np.round(h)


def build_maps():
    X = np.arange(N)[:, None]
    Z = np.arange(N)[None, :]
    H = _height(X, Z).astype(int)
    g = np.zeros_like(H)
    g[1:, :] = np.maximum(g[1:, :], np.abs(H[1:, :] - H[:-1, :]))
    g[:-1, :] = np.maximum(g[:-1, :], np.abs(H[1:, :] - H[:-1, :]))
    g[:, 1:] = np.maximum(g[:, 1:], np.abs(H[:, 1:] - H[:, :-1]))
    g[:, :-1] = np.maximum(g[:, :-1], np.abs(H[:, 1:] - H[:, :-1]))
    return H, g


HMAP, GRAD = build_maps()


def height(X, Z):
    X = np.clip(np.asarray(X).astype(int), 0, N - 1)
    Z = np.clip(np.asarray(Z).astype(int), 0, N - 1)
    return HMAP[X, Z]


def steep(X, Z):
    X = np.clip(np.asarray(X).astype(int), 0, N - 1)
    Z = np.clip(np.asarray(Z).astype(int), 0, N - 1)
    return GRAD[X, Z] >= 2


def land(X, Z):
    return SHORE(X, Z) > 1.5


def hy(x, z):
    return int(HMAP[min(max(x, 0), N - 1), min(max(z, 0), N - 1)])


def terrain(bb):
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SAND, 1631,
             mask=lambda X, Z: land(X, Z) & (height(X, Z) <= 1) & ~steep(X, Z), under="minecraft:sandstone", core="minecraft:sandstone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, ROCK, 1632, mask=lambda X, Z: land(X, Z) & steep(X, Z), under="minecraft:stone",
             core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, NT.MEADOW, 1633,
             mask=lambda X, Z: land(X, Z) & (height(X, Z) > 1) & ~steep(X, Z), core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, ROAD, 1634,
             mask=lambda X, Z: land(X, Z) & (road_d(X, Z) <= 2.2 + NT.noise(X, Z, 1635, 3)), core="minecraft:stone")
    # sea floor shelving away from the shore (deep in the cove for the ship)
    for y in range(-12, 0):
        bb.fill_where(0, y, 0, N - 1, y, N - 1, lambda X, yy, Z: (SHORE(X, Z) <= 1.5) &
                      (yy > -2 - np.clip(-SHORE(X, Z) * 0.8, 0, 10)), "minecraft:water")
        bb.fill_where(0, y, 0, N - 1, y, N - 1, lambda X, yy, Z: (SHORE(X, Z) <= 1.5) &
                      (yy == np.round(-2 - np.clip(-SHORE(X, Z) * 0.8, 0, 10))), "minecraft:sand")


# ------------------------------------------------------------------ Kaya's mansion
WHITE = ["minecraft:white_concrete", "minecraft:calcite", "minecraft:white_concrete"]


def mansion(bb, tracker, audit):
    x1, z1, x2, z2 = MAN
    y0 = MY
    # the wall round the grounds with brick piers, the iron gate on the south-west (toward the village)
    for (a, b, c, d) in ((x1, z1, x2, z1), (x1, z2, x2, z2), (x1, z1, x1, z2), (x2, z1, x2, z2)):
        bb.fill(a, y0 + 1, b, c, y0 + 2, d, "minecraft:stone_bricks")
        bb.fill(a, y0 + 3, b, c, y0 + 3, d, "minecraft:iron_bars")
    for x in range(x1, x2 + 1, 6):
        for z in (z1, z2):
            bb.fill(x, y0 + 1, z, x, y0 + 4, z, "minecraft:bricks")
            bb.set(x, y0 + 5, z, "minecraft:stone_brick_slab[type=bottom]")
    for z in range(z1, z2 + 1, 6):
        for x in (x1, x2):
            bb.fill(x, y0 + 1, z, x, y0 + 4, z, "minecraft:bricks")
            bb.set(x, y0 + 5, z, "minecraft:stone_brick_slab[type=bottom]")
    gx = 104
    bb.fill(gx - 3, y0 + 1, z2, gx + 3, y0 + 3, z2, AIR)
    bb.fill(gx - 3, y0 + 1, z2, gx + 3, y0 + 3, z2, "minecraft:iron_bars")
    bb.fill(gx - 1, y0 + 1, z2, gx + 1, y0 + 3, z2, AIR)
    for x in (gx - 4, gx + 4):
        bb.fill(x, y0 + 1, z2, x, y0 + 6, z2, "minecraft:stone_bricks")
        bb.set(x, y0 + 7, z2, "minecraft:lantern[hanging=false]")
    bb.fill(gx - 3, y0 + 5, z2, gx + 3, y0 + 5, z2, "minecraft:iron_bars")
    # lawn and gravel court
    NT.cover(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, lambda X, Z: X * 0 + y0,
             [("minecraft:grass_block", 0.9), ("minecraft:moss_block", 0.1)], 1641)
    # the house: main block across the north, two wings coming forward
    FH = 5
    A = (100, 28, 136, 42)
    W1 = (100, 43, 110, 56)
    W2 = (126, 43, 136, 56)
    for (bx1, bz1, bx2, bz2) in (A, W1, W2):
        top = tier(bb, bx1, bz1, bx2, bz2, y0, 3, FH, WHITE, "minecraft:glass_pane", "minecraft:quartz_stairs",
                   pilaster="minecraft:quartz_pillar[axis=y]", band="minecraft:smooth_quartz", plate="minecraft:spruce_planks",
                   top_plate="minecraft:spruce_planks", every=2, pil_every=6, win_h=3)
        bb.fill(bx1 - 1, y0, bz1 - 1, bx2 + 1, y0, bz2 + 1, "minecraft:stone_bricks")
        cornice(bb, bx1, bz1, bx2, bz2, top, "minecraft:quartz_stairs")
    top = y0 + 3 * FH
    P.gable_roof(bb, A[0] - 1, A[1] - 1, A[2] + 1, A[3] + 1, top + 1, "minecraft:nether_brick_stairs", ridge_axis="x",
                 gable_fill="minecraft:white_concrete", overhang=1, ends_overhang=1)
    for W in (W1, W2):
        P.gable_roof(bb, W[0] - 1, W[1], W[2] + 1, W[3] + 1, top + 1, "minecraft:nether_brick_stairs", ridge_axis="z",
                     gable_fill="minecraft:white_concrete", overhang=1, ends_overhang=1)
    # chimneys and dormer-ish roof lights
    for x in (A[0] + 3, A[2] - 3):
        bb.fill(x, top + 1, A[1] + 3, x + 1, top + 12, A[1] + 4, "minecraft:bricks")
    # the portico on the main door (south face of the main block, between the wings)
    cx = (A[0] + A[2]) // 2
    bb.fill(cx - 1, y0 + 1, A[3], cx + 1, y0 + 3, A[3], AIR)
    for x in (cx - 4, cx + 4):
        bb.fill(x, y0 + 1, A[3] + 4, x, y0 + 6, A[3] + 4, "minecraft:quartz_pillar[axis=y]")
    bb.fill(cx - 5, y0 + 7, A[3] + 1, cx + 5, y0 + 7, A[3] + 5, "minecraft:smooth_quartz")
    bb.fill(cx - 5, y0 + 8, A[3] + 1, cx + 5, y0 + 8, A[3] + 5, "minecraft:quartz_slab[type=bottom]")
    bb.fill(cx - 3, y0 + 1, A[3] + 1, cx + 3, y0 + 1, A[3] + 5, "minecraft:red_carpet")
    # inside: entrance hall (double height, a grand stair), dining room, library, Kaya's bedroom, servants' rooms
    hall = (cx - 6, A[1] + 1, cx + 6, A[3] - 1)
    bb.fill(hall[0], y0 + FH, hall[1], hall[2], y0 + FH, hall[3], AIR)
    bb.fill(hall[0], y0 + 1, hall[1], hall[2], y0 + 1, hall[3], AIR)
    for z in range(hall[1], hall[3] + 1):
        for x in range(hall[0], hall[2] + 1):
            bb.set(x, y0, z, "minecraft:polished_diorite" if (x + z) % 2 else "minecraft:polished_andesite")
    for k in range(FH):
        bb.fill(cx - 1, y0 + 1 + k, hall[1] + 1 + k, cx + 1, y0 + 1 + k, hall[1] + 1 + k, st("minecraft:dark_oak_stairs", "south"))
        bb.fill(cx - 1, y0 + 1, hall[1] + 1 + k, cx + 1, y0 + k, hall[1] + 1 + k, "minecraft:dark_oak_planks")
    bb.fill(cx - 1, y0 + FH, hall[1], cx + 1, y0 + FH, hall[1], "minecraft:dark_oak_planks")
    bb.fill(hall[0], y0 + FH, hall[1], hall[2], y0 + FH, hall[1], "minecraft:dark_oak_planks")
    bb.fill(hall[0], y0 + FH + 1, hall[1] + 1, hall[2], y0 + FH + 1, hall[1] + 1, "minecraft:dark_oak_fence")
    bb.fill(cx - 1, y0 + FH + 1, hall[1] + 1, cx + 1, y0 + FH + 1, hall[1] + 1, AIR)
    bb.set(cx, y0 + 2 * FH - 1, (hall[1] + hall[3]) // 2 + 2, "minecraft:chain")
    bb.set(cx, y0 + 2 * FH - 2, (hall[1] + hall[3]) // 2 + 2, "minecraft:lantern[hanging=true]")
    for x in (hall[0], hall[2]):
        for z in (hall[1] + 3, hall[3] - 1):
            bb.set(x, y0 + 1, z, "minecraft:potted_azalea_bush")
    bb.fill(hall[0] + 1, y0 + 1, hall[3] - 3, hall[0] + 1, y0 + 1, hall[3] - 1, "minecraft:red_carpet")
    keep = [(hall[0] - 1, hall[1] - 1, hall[2] + 1, hall[3] + 1)]
    kinds = [("kitchen", "storage", "living"), ("bedroom", "library", "living"), ("bedroom", "bedroom", "storage")]
    for k in range(3):
        y = y0 + 1 + FH * k
        wing_floor(bb, A[0] + 1, A[1] + 1, A[2] - 1, A[3] - 1, y, FH - 1, "minecraft:white_concrete", seed_of("syk", k), tracker,
                   kinds[k], corridor="x", cw=3, carpet=(None, "minecraft:red_carpet"), keep=keep if k < 2 else (),
                   wood="dark_oak", audit=audit)
        for j, W in enumerate((W1, W2)):
            wing_floor(bb, W[0] + 1, W[1] + 1, W[2] - 1, W[3] - 1, y, FH - 1, "minecraft:white_concrete", seed_of("syw", k, j),
                       tracker, (("living", "kitchen"), ("library", "bedroom"), ("bedroom", "storage"))[k], corridor="z", cw=3,
                       carpet=(None, "minecraft:red_carpet"), wood="dark_oak", audit=audit)
        # openings from the wings into the main block's corridor
        for W in (W1, W2):
            wx = (W[0] + W[2]) // 2
            bb.fill(wx - 1, y, A[3], wx + 1, y + 2, A[3], AIR)
            bb.fill(wx - 1, y, W[1], wx + 1, y + 2, W[1], AIR)
    # a ladder well in each wing so every floor is reached
    for W in (W1, W2):
        bb.fill(W[0] + 1, y0 + 1, W[3] - 1, W[0] + 1, y0 + 2 * FH + 1, W[3] - 1, "minecraft:ladder[facing=east]")
        for k in (1, 2):
            bb.set(W[0] + 1, y0 + FH * k, W[3] - 1, "minecraft:ladder[facing=east]")
    # Kaya's balcony on the main block (her window looks out over the court: Usopp's lies were told under it)
    bb.fill(cx - 3, y0 + 2 * FH, A[3] + 1, cx + 3, y0 + 2 * FH, A[3] + 1, "minecraft:smooth_quartz")
    bb.fill(cx - 3, y0 + 2 * FH + 1, A[3] + 1, cx + 3, y0 + 2 * FH + 1, A[3] + 1, "minecraft:quartz_slab[type=bottom]") if False else None
    bb.fill(cx - 1, y0 + 2 * FH + 1, A[3], cx + 1, y0 + 2 * FH + 3, A[3], "minecraft:glass_pane")
    # the court: fountain, gravel, hedges, rose beds, the big tree outside Kaya's window
    fx, fz = cx, 62
    NT.cover(bb, W1[2] + 2, A[3] + 6, W2[0] - 2, z2 - 1, lambda X, Z: X * 0 + y0,
             [("minecraft:gravel", 0.6), ("minecraft:light_gray_concrete_powder", 0.2), ("minecraft:andesite", 0.2)], 1642,
             mask=lambda X, Z: (np.abs(X - cx) <= 5) | (np.hypot(X - fx, Z - fz) < 8.5))
    bb.fill_where(fx - 6, y0 + 1, fz - 6, fx + 6, y0 + 1, fz + 6, lambda X, yy, Z: np.abs(np.hypot(X - fx, Z - fz) - 5) < 0.7,
                  "minecraft:stone_brick_wall")
    bb.fill_where(fx - 6, y0, fz - 6, fx + 6, y0, fz + 6, lambda X, yy, Z: np.hypot(X - fx, Z - fz) < 4.6, "minecraft:water")
    bb.fill(fx, y0 + 1, fz, fx, y0 + 3, fz, "minecraft:quartz_pillar[axis=y]")
    bb.set(fx, y0 + 4, fz, "minecraft:water")
    for (hx1, hz1, hx2, hz2) in ((x1 + 2, A[3] + 6, W1[2], z2 - 3), (W2[0], A[3] + 6, x2 - 2, z2 - 3)):
        for x in range(hx1, hx2 + 1):
            for z in range(hz1, hz2 + 1):
                if (x - hx1) % 5 == 0 or (z - hz1) % 5 == 0:
                    bb.set(x, y0 + 1, z, "minecraft:oak_leaves[distance=7,persistent=true,waterlogged=false]")
                elif (x + z) % 3 == 0:
                    bb.set(x, y0, z, "minecraft:grass_block")
                    bb.set(x, y0 + 1, z, ("minecraft:rose_bush[half=lower]", "minecraft:peony[half=lower]")[(x // 5) % 2])
                    bb.set(x, y0 + 2, z, ("minecraft:rose_bush[half=upper]", "minecraft:peony[half=upper]")[(x // 5) % 2])
    for (x, z) in ((cx - 9, z2 - 3), (cx + 9, z2 - 3), (cx - 9, A[3] + 7), (cx + 9, A[3] + 7)):
        lamp_post(bb, x, y0 + 1, z, post="minecraft:dark_oak_fence", h=4)
    # back garden: a greenhouse and the kitchen garden
    bb.fill(x1 + 3, y0 + 1, z1 + 3, x1 + 9, y0 + 4, z1 + 9, "minecraft:glass")
    bb.fill(x1 + 4, y0 + 1, z1 + 4, x1 + 8, y0 + 3, z1 + 8, AIR)
    bb.fill(x1 + 4, y0, z1 + 4, x1 + 8, y0, z1 + 8, "minecraft:farmland[moisture=7]")
    bb.fill(x1 + 4, y0 + 1, z1 + 4, x1 + 8, y0 + 1, z1 + 8, "minecraft:carrots[age=7]")
    bb.fill(x1 + 6, y0 + 1, z1 + 9, x1 + 6, y0 + 2, z1 + 9, AIR)
    bb.fill(x1 + 6, y0, z1 + 4, x1 + 6, y0, z1 + 8, "minecraft:water")
    bb.fill(x1 + 6, y0 + 1, z1 + 4, x1 + 6, y0 + 1, z1 + 8, AIR)
    P.tree(bb, x2 - 6, y0 + 1, z2 - 6, 9, "oak", np.random.default_rng(1643))
    P.tree(bb, x2 - 5, y0 + 1, z1 + 5, 8, "birch", np.random.default_rng(1644))
    return (x1 - 2, z1 - 2, x2 + 2, z2 + 2)


# ------------------------------------------------------------------ the village
PALS = [
    dict(walls=["minecraft:white_terracotta", "minecraft:calcite", "minecraft:smooth_sandstone"], frame="minecraft:stripped_oak_log",
         base=["minecraft:cobblestone", "minecraft:mossy_cobblestone", "minecraft:stone_bricks"], floor="minecraft:oak_planks",
         wood="oak", chimney="minecraft:bricks"),
    dict(walls=["minecraft:smooth_sandstone", "minecraft:sandstone", "minecraft:white_terracotta"], frame="minecraft:spruce_log",
         base=["minecraft:cobblestone", "minecraft:stone_bricks", "minecraft:mossy_cobblestone"], floor="minecraft:spruce_planks",
         wood="spruce", chimney="minecraft:bricks"),
    dict(walls=["minecraft:oak_planks", "minecraft:stripped_oak_wood", "minecraft:oak_planks"], frame="minecraft:oak_log",
         base=["minecraft:cobblestone", "minecraft:mossy_cobblestone", "minecraft:cobblestone"], floor="minecraft:oak_planks",
         wood="oak", chimney="minecraft:cobblestone"),
    dict(walls=["minecraft:light_gray_terracotta", "minecraft:white_terracotta", "minecraft:calcite"], frame="minecraft:dark_oak_log",
         base=["minecraft:cobblestone", "minecraft:stone_bricks", "minecraft:andesite"], floor="minecraft:spruce_planks",
         wood="dark_oak", chimney="minecraft:bricks"),
]
ROOFS = ["minecraft:spruce_stairs", "minecraft:brick_stairs", "minecraft:dark_oak_stairs", "minecraft:mud_brick_stairs",
         "minecraft:oak_stairs"]
KINDS = [["kitchen", "bedroom"], ["living", "bedroom", "storage"], ["workshop", "bedroom"], ["kitchen", "living", "bedroom"],
         ["storage", "bedroom"]]

# (x, z, w, d, floors, rot) round the green; rot turns the door: 0 south, 2 north, 1 west, 3 east
HOUSES = [(40, 70, 9, 8, 2, 0), (52, 69, 8, 8, 2, 0), (62, 70, 11, 9, 3, 0), (76, 69, 8, 8, 2, 0), (86, 70, 9, 8, 2, 0),
          (40, 108, 9, 8, 2, 2), (52, 109, 10, 8, 2, 2), (78, 108, 9, 8, 2, 2), (90, 109, 8, 8, 2, 2),
          (36, 84, 8, 9, 2, 3), (36, 95, 8, 8, 2, 3), (96, 84, 8, 9, 2, 1), (96, 95, 8, 8, 2, 1)]


def village(bb, tracker, audit, rng):
    taken = []
    x1, z1, x2, z2 = VIL
    # the green: grass with a well, a big oak, benches; cobbled lane round it
    gx1, gz1, gx2, gz2 = 50, 82, 90, 104
    NT.cover(bb, x1, z1, x2, z2, lambda X, Z: X * 0 + VY, ROAD, 1651,
             mask=lambda X, Z: (rect_d(X, Z, (gx1 - 4, gz1 - 4, gx2 + 4, gz2 + 4)) == 0) & (rect_d(X, Z, (gx1, gz1, gx2, gz2)) > 0))
    for k, (x, z, w, d, fl, rot) in enumerate(HOUSES):
        mod, _, au = house_module(seed_of("syv", k), w, d, fl, ROOFS[k % len(ROOFS)], tracker, KINDS[k % len(KINDS)],
                                  pal=PALS[k % len(PALS)], timber=(k % 3 != 2), jetty=(k % 4 == 0))
        audit += au
        place_house(bb, mod, w, d, x, VY, z, rot)
        ww, dd = (w, d) if rot % 2 == 0 else (d, w)
        taken.append((x - 1, z - 1, x + ww, z + dd))
    # the well
    wx, wz = 70, 93
    bb.fill(wx - 1, VY + 1, wz - 1, wx + 1, VY + 1, wz + 1, "minecraft:cobblestone_wall")
    bb.fill(wx, VY - 6, wz, wx, VY + 1, wz, "minecraft:water")
    for (x, z) in ((wx - 1, wz - 1), (wx + 1, wz + 1)):
        bb.fill(x, VY + 2, z, x, VY + 3, z, "minecraft:oak_fence")
    bb.fill(wx - 1, VY + 4, wz - 1, wx + 1, VY + 4, wz + 1, "minecraft:oak_slab[type=bottom]")
    bb.set(wx, VY + 3, wz, "minecraft:chain")
    P.tree(bb, 58, VY + 1, 88, 10, "oak", np.random.default_rng(1652))
    taken.append((54, 84, 62, 92))
    for (x, z, f) in ((76, 86, "south"), (78, 86, "south"), (64, 100, "north"), (66, 100, "north")):
        bb.set(x, VY + 1, z, st("minecraft:oak_stairs", f))
    for (x, z) in ((gx1 - 2, gz1 - 2), (gx2 + 2, gz1 - 2), (gx1 - 2, gz2 + 2), (gx2 + 2, gz2 + 2)):
        lamp_post(bb, x, VY + 1, z, post="minecraft:spruce_fence", h=3)
    # flower beds on the green
    for (x, z) in ((82, 96), (54, 98), (84, 86)):
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                bb.set(x + dx, VY + 1, z + dz, ("minecraft:poppy", "minecraft:dandelion", "minecraft:cornflower")[(dx + dz) % 3])
    # Usopp's house: a small cottage by itself at the west edge of the village, his workbench and targets outside
    mod, _, au = house_module(seed_of("syusopp"), 7, 7, 1, "minecraft:spruce_stairs", tracker, ["workshop"], pal=PALS[2],
                              timber=True, jetty=False)
    audit += au
    place_house(bb, mod, 7, 7, 22, hy(25, 100), 97, 3)
    taken.append((20, 95, 31, 106))
    for z in (96, 99, 102):
        bb.set(32, hy(32, z) + 1, z, "minecraft:target")
    return taken


def farms(bb, rng):
    """Fields and the orchard south of the village."""
    taken = []
    crops = ["minecraft:wheat[age=7]", "minecraft:carrots[age=7]", "minecraft:potatoes[age=7]", "minecraft:beetroots[age=3]"]
    for k, (x1, z1, x2, z2) in enumerate(((40, 126, 58, 140), (62, 126, 80, 138), (84, 126, 100, 136))):
        y = hy((x1 + x2) // 2, (z1 + z2) // 2)
        if y < 2:
            continue
        bb.fill(x1 - 1, y + 1, z1 - 1, x2 + 1, y + 6, z2 + 1, AIR)
        bb.fill(x1 - 1, y - 2, z1 - 1, x2 + 1, y, z2 + 1, "minecraft:dirt")
        bb.fill(x1 - 1, y, z1 - 1, x2 + 1, y, z2 + 1, "minecraft:grass_block")
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if (x - x1) % 5 == 2:
                    bb.set(x, y, z, "minecraft:water")
                else:
                    bb.set(x, y, z, "minecraft:farmland[moisture=7]")
                    bb.set(x, y + 1, z, crops[(k + (z - z1) // 5) % len(crops)])
        for x in range(x1 - 1, x2 + 2):
            bb.set(x, y + 1, z1 - 1, "minecraft:oak_fence"); bb.set(x, y + 1, z2 + 1, "minecraft:oak_fence")
        for z in range(z1 - 1, z2 + 2):
            bb.set(x1 - 1, y + 1, z, "minecraft:oak_fence"); bb.set(x2 + 1, y + 1, z, "minecraft:oak_fence")
        bb.set((x1 + x2) // 2, y + 1, z1 - 1, "minecraft:oak_fence_gate[facing=north,open=false]")
        bb.set(x2 + 2, y + 1, z1 + 1, "minecraft:hay_block[axis=y]")
        bb.set(x2 + 2, y + 2, z1 + 1, "minecraft:carved_pumpkin[facing=east]")
        taken.append((x1 - 2, z1 - 2, x2 + 3, z2 + 2))
    # orchard: rows of small fruit trees east of the village
    k = 0
    for x in range(112, 140, 6):
        for z in range(82, 118, 6):
            if SHORE(np.array([[x]]), np.array([[z]]))[0, 0] < 8 or GRAD[x, z] >= 2:
                continue
            y = hy(x, z)
            P.tree(bb, x, y + 1, z, int(rng.integers(4, 6)), ("oak", "cherry", "oak")[k % 3], rng)
            k += 1
    taken.append((108, 78, 144, 122))
    return taken


def hideout(bb, x, z):
    """The Usopp Pirates' hideout: a hollow giant tree with a door in its roots, a ladder inside and a lookout."""
    y = hy(x, z)
    log = "minecraft:oak_log[axis=y]"
    h = 18
    for k in range(-2, h):
        r = 3.6 - k * 0.06
        bb.fill_where(x - 5, y + k, z - 5, x + 5, y + k, z + 5, lambda X, yy, Z: np.hypot(X - x, Z - z) <= r, log)
        bb.fill_where(x - 5, y + k, z - 5, x + 5, y + k, z + 5, lambda X, yy, Z: np.hypot(X - x, Z - z) <= r - 1.4, AIR)
    bb.fill(x - 2, y, z - 2, x + 2, y, z + 2, "minecraft:spruce_planks")
    bb.fill(x, y + 1, z + 3, x, y + 2, z + 3, AIR)
    bb.fill(x, y + 1, z + 4, x, y + 2, z + 4, AIR)
    bb.fill(x - 1, y + 1, z - 2, x - 1, y + h - 1, z - 2, "minecraft:ladder[facing=south]")
    for yy in (y + 7, y + 13):
        bb.fill(x - 2, yy, z - 1, x + 2, yy, z + 2, "minecraft:spruce_planks")
        bb.set(x + 1, yy + 1, z + 1, "minecraft:barrel[facing=up,open=false]")
        bb.set(x, yy + 1, z + 2, "minecraft:candle[candles=3,lit=true]")
    bb.set(x + 2, y + 1, z, "minecraft:barrel[facing=up,open=false]")
    bb.set(x + 1, y + 1, z - 1, "minecraft:crafting_table")
    for (dx, dz) in ((4, 0), (-4, 0), (0, -4)):
        bb.set(x + dx, y + 9, z + dz, AIR)
    # crown of leaves on top with a lookout platform and the Usopp Pirates' flag
    leaf = "minecraft:oak_leaves[distance=7,persistent=true,waterlogged=false]"
    bb.fill_where(x - 8, y + h, z - 8, x + 8, y + h + 6, z + 8,
                  lambda X, yy, Z: ((X - x) ** 2 + ((yy - y - h - 2) * 1.6) ** 2 + (Z - z) ** 2 < 7.5 ** 2)
                  & (NT.noise(X + yy * 3, Z, 1661, 2) < 0.8), leaf)
    bb.fill(x - 2, y + h, z - 2, x + 2, y + h, z + 2, "minecraft:spruce_planks")
    bb.fill(x - 2, y + h + 1, z - 2, x + 2, y + h + 3, z + 2, AIR)
    bb.fill(x - 2, y + h + 1, z - 2, x + 2, y + h + 1, z - 2, "minecraft:oak_fence")
    bb.fill(x - 2, y + h + 1, z + 2, x + 2, y + h + 1, z + 2, "minecraft:oak_fence")
    bb.fill(x + 2, y + h + 1, z - 2, x + 2, y + h + 7, z - 2, "minecraft:oak_fence")
    bb.fill(x + 3, y + h + 5, z - 2, x + 5, y + h + 7, z - 2, "minecraft:black_wool")
    bb.set(x + 4, y + h + 6, z - 2, "minecraft:white_wool")
    for (dx, dz) in ((-4, 2), (3, 3), (2, -4), (-3, -3)):                 # roots
        bb.fill(x + dx, y - 1, z + dz, x + dx, y + 1, z + dz, log)
    return (x - 8, z - 8, x + 8, z + 8)


def cove(bb):
    """The cove at the foot of the slope road: a small jetty and the Going Merry at anchor."""
    x, z = COVE
    for k in range(14):
        bb.fill(x - 1 - k, 0, z + 2, x - 1 - k, 0, z + 4, "minecraft:spruce_planks") if False else None
    for zz in range(z - 12, z + 4):
        bb.fill(x + 6, 0, zz, x + 8, 0, zz, "minecraft:spruce_planks")
        if zz % 4 == 0:
            bb.fill(x + 5, -8, zz, x + 5, 0, zz, "minecraft:spruce_log[axis=y]")
            bb.fill(x + 9, -8, zz, x + 9, 0, zz, "minecraft:spruce_log[axis=y]")
            bb.set(x + 9, 1, zz, "minecraft:lantern[hanging=false]")
    stamp_ship(bb, "going_merry", 18, 18, water_y=0, rot=3)
    for (bx, bz) in ((x + 10, z + 3), (x + 11, z + 4)):
        bb.set(bx, hy(bx, bz) + 1, bz, "minecraft:barrel[facing=up,open=false]")


def scenery(bb, rng, taken):
    k = 0
    for _ in range(4000):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        X, Z = np.array([[x]]), np.array([[z]])
        if SHORE(X, Z)[0, 0] < 6 or GRAD[x, z] >= 2 or road_d(X, Z)[0, 0] < 5:
            continue
        if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken):
            continue
        y = hy(x, z)
        if y < 2:
            continue
        # a wood on the west and north, scattered trees elsewhere
        wood = NT.noise(X, Z, 1671, 22)[0, 0] > 0.45 or (x < 34)
        if not wood and rng.random() > 0.2:
            continue
        P.tree(bb, x, y + 1, z, int(rng.integers(6, 11)), ("oak", "birch", "oak", "dark_oak")[k % 4], rng)
        taken.append((x - 3, z - 3, x + 3, z + 3))
        k += 1
        if k >= 70:
            break
    rocks = 0
    for _ in range(400):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        if GRAD[x, z] >= 2 and hy(x, z) > 2 and rocks < 10:
            NT.boulder(bb, x, hy(x, z), z, rng.uniform(1.5, 2.6), rng)
            rocks += 1
    print("trees:", k, "rocks:", rocks)


def design():
    bb = BigBuild(seed=1620, y_min=-14, y_max=70)
    tracker = P.PropTracker(1620)
    audit = []
    rng = np.random.default_rng(1620)
    terrain(bb)
    taken = [mansion(bb, tracker, audit)]
    taken += village(bb, tracker, audit, rng)
    taken += farms(bb, rng)
    taken.append(hideout(bb, 26, 66))
    cove(bb)
    taken.append((COVE[0] - 30, 0, COVE[0] + 14, COVE[1] + 8))
    taken.append((VIL[0], VIL[1], VIL[2], VIL[3]))
    scenery(bb, rng, taken)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 1690, density=0.3, kinds=NT.PLANTS_MEADOW, flowers=NT.FLOWERS,
              mask=lambda X, Z: land(X, Z) & (rect_d(X, Z, MAN) > 0) & (road_d(X, Z) > 3))
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
    b.npc(72, VY + 1, 96, "usopp", False)
    b.chest(MAN[0] + 14, MY + 1, MAN[1] + 8, "easy", "east")
    b.chest(25, hy(25, 100) + 1, 100, "easy", "west")
    return b, 0
