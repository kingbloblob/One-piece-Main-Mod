"""Loguetown v2, the Town of the Beginning and the End, redesigned with the Minecraft Builder skill
(dossier: mcb/dossiers/loguetown.md).

The coast of a green island whose ground fades out to its beaches; the harbour to the south. In the middle the
great execution square, paved in worn stone, with the tall wooden scaffold where Gol D. Roger died. Brick, stone and
plaster townhouses of three and four storeys ring it (shops on the ground floor: Ipponmatsu's sword shop, the
tailor, the bar, the restaurant, the bakery), streets run off it, a clock tower stands on its corner. The Marine
base where Captain Smoker is stationed lies on the west: a walled compound with its white headquarters, gate,
flagpole and drill yard. The harbour has quays, piers, warehouses, a Marine warship and the Going Merry tied up.
160 x 160. y 0 = ground / sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, furnish, set_if_air, cornice, tier, wing_floor, \
    house_module, place_house, lamp_post, wg_flag
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.shipstamp import stamp_ship

SID = "loguetown"
TITLE = "Loguetown Execution Square"
# v3 (2026-10-30): the execution scaffold is the square's hero, in the middle, 22 high with a 36-tall frame.
CUTS = [3, 14, 26]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 160
CX, CZ = 80, 72
SQ = (58, 50, 104, 86)                  # execution square (x1, z1, x2, z2)
BASE = (8, 82, 42, 118)                 # Marine base compound
QUAY_Z = 126                            # the quay edge (sea south of it)
TOWN = (14, 16, 146, 124)                # flat town ground

SHORE = NT.outline(CX, 76, 70, 1520, wobble=0.1)

PAVE = [("minecraft:stone_bricks", 0.34), ("minecraft:cobblestone", 0.22), ("minecraft:andesite", 0.14),
        ("minecraft:mossy_cobblestone", 0.08), ("minecraft:cracked_stone_bricks", 0.10), ("minecraft:gravel", 0.06),
        ("minecraft:polished_andesite", 0.06)]
STREET = [("minecraft:cobblestone", 0.4), ("minecraft:stone_bricks", 0.2), ("minecraft:gravel", 0.14),
          ("minecraft:mossy_cobblestone", 0.12), ("minecraft:andesite", 0.14)]
SAND = [("minecraft:sand", 0.7), ("minecraft:gravel", 0.12), ("minecraft:sandstone", 0.08), ("minecraft:clay", 0.10)]


def rect_d(X, Z, r):
    dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0)
    dz = np.maximum(np.maximum(r[1] - Z, Z - r[3]), 0)
    return np.hypot(dx, dz)


def sea(X, Z):
    """The harbour water south of the quay (with the shore line round it)."""
    return (Z > QUAY_Z) | (SHORE(X, Z) <= 0)


def height(X, Z):
    d = SHORE(X, Z)
    inland = np.clip((d - 3) / 14.0, 0, 1)
    hills = NT.fbm(X, Z, 1531, 28) * 9 * inland
    flat = np.clip(rect_d(X, Z, TOWN) / 12.0, 0, 1)
    h = hills * flat + (NT.noise(X, Z, 1532, 7) > 0.8) * 0
    h = np.where(d < 2.5, -1, h)
    return np.round(h)


def land(X, Z):
    return ~sea(X, Z)


def hy(x, z):
    return int(height(np.array([[x]]), np.array([[z]]))[0, 0])


def terrain(bb):
    H = height
    NT.cover(bb, 0, 0, N - 1, N - 1, H, SAND, 1541, mask=lambda X, Z: land(X, Z) & (SHORE(X, Z) < 6) & (rect_d(X, Z, TOWN) > 0),
             under="minecraft:sandstone", core="minecraft:sandstone")
    NT.cover(bb, 0, 0, N - 1, N - 1, H, NT.MEADOW, 1542,
             mask=lambda X, Z: land(X, Z) & ((SHORE(X, Z) >= 6) | (rect_d(X, Z, TOWN) == 0)), core="minecraft:stone")
    # the harbour basin: deepening water south of the quay
    for y in range(-10, 1):
        bb.fill_where(0, y, QUAY_Z + 1, N - 1, y, N - 1,
                      lambda X, yy, Z: (yy > -3 - np.clip((Z - QUAY_Z) * 0.6, 0, 7)) & (SHORE(X, Z) > -12), "minecraft:water")
        bb.fill_where(0, y, QUAY_Z + 1, N - 1, y, N - 1,
                      lambda X, yy, Z: (yy == np.round(-3 - np.clip((Z - QUAY_Z) * 0.6, 0, 7))) & (SHORE(X, Z) > -12), "minecraft:sand")


# ------------------------------------------------------------------ the square and the scaffold
def square(bb):
    x1, z1, x2, z2 = SQ
    NT.cover(bb, x1 - 2, z1 - 2, x2 + 2, z2 + 2, lambda X, Z: X * 0, PAVE, 1551,
             mask=lambda X, Z: rect_d(X, Z, SQ) <= 1 + 2 * NT.noise(X, Z, 1552, 3), under="minecraft:stone", core="minecraft:stone")
    # a ring of darker paving round a central rose
    cx, cz = (x1 + x2) // 2, (z1 + z2) // 2 + 4
    # lamp posts round the square, market stalls down its east and west sides, benches
    for (x, z) in ((x1 + 1, z1 + 1), (x2 - 1, z1 + 1), (x1 + 1, z2 - 1), (x2 - 1, z2 - 1), (x1 + 1, cz), (x2 - 1, cz)):
        lamp_post(bb, x, 1, z, post="minecraft:dark_oak_fence", h=4)
    cols = ["red", "white", "blue", "yellow", "green", "orange"]
    for i, z in enumerate(range(z1 + 6, z2 - 6, 7)):
        for (x, face, d) in ((x1 + 3, "east", 1), (x2 - 6, "west", -1)):
            c = cols[(i + (d > 0)) % len(cols)]
            bb.fill(x, 1, z, x + 3, 1, z, "minecraft:spruce_planks")
            bb.fill(x, 2, z, x + 3, 2, z, "minecraft:spruce_trapdoor[facing=north,half=bottom,open=false]")
            for xx in (x, x + 3):
                bb.fill(xx, 1, z + 2, xx, 3, z + 2, "minecraft:spruce_fence")
            bb.fill(x - 1, 4, z - 1, x + 4, 4, z + 2, f"minecraft:{c}_wool")
            bb.set(x + 1, 2, z, ("minecraft:melon", "minecraft:pumpkin", "minecraft:hay_block[axis=y]", "minecraft:barrel[facing=up,open=false]")[i % 4])
            bb.set(x + 2, 2, z, "minecraft:flower_pot")
    for x in range(x1 + 8, x2 - 8, 6):
        if abs(x - (x1 + x2) // 2) > 10:
            bb.set(x, 1, z2 - 2, st("minecraft:spruce_stairs", "south"))
            bb.set(x + 1, 1, z2 - 2, st("minecraft:spruce_stairs", "south"))


def scaffold(bb):
    """Roger's execution scaffold, the hero of the square (v3: was a small stand at the north edge): a tall timber
    platform (22 up) right in the middle on X-braced log legs standing on stone footings, one long stair rising along its
    south face, railings, the execution frame with the kneeling board on top, Marine banners hanging off the beam,
    flag poles on the corners, a crowd barrier round it and a ring of paving that draws the eye in."""
    x1, z1, x2, z2 = SQ
    cx, cz = (x1 + x2) // 2, z1 + 15
    top = 22
    px1, px2, pz1, pz2 = cx - 9, cx + 9, cz - 6, cz + 6
    LOG = "minecraft:dark_oak_log[axis=y]"
    # paving rings round it
    for x in range(x1 + 1, x2):
        for z in range(z1 + 1, z2):
            d = math.hypot(x - cx, (z - cz - 3) * 1.2)
            if int(d) % 6 == 0:
                bb.set(x, 0, z, "minecraft:polished_andesite")
            elif int(d) % 6 == 3 and (x + z) % 2:
                bb.set(x, 0, z, "minecraft:polished_basalt[axis=y]")
    legs = [(x, z) for x in range(px1, px2 + 1, 6) for z in range(pz1, pz2 + 1, 6)]
    for (x, z) in legs:
        bb.fill(x - 1, -2, z - 1, x + 1, 1, z + 1, "minecraft:stone_bricks")
        bb.set(x - 1, 2, z - 1, "minecraft:stone_brick_slab[type=bottom]")
        bb.fill(x, 2, z, x, top - 1, z, LOG)
    # X bracing on the four outer faces, two tiers
    for tier_ in ((2, top // 2), (top // 2, top - 1)):
        y0, y1 = tier_
        for (fx, fz, ax) in ((None, pz1, "x"), (None, pz2, "x"), (px1, None, "z"), (px2, None, "z")):
            lo, hi = (px1, px2) if ax == "x" else (pz1, pz2)
            for a0 in range(lo, hi, 6):
                for i in range(1, 6):
                    ya = y0 + round((y1 - y0) * i / 6)
                    yb = y1 - round((y1 - y0) * i / 6)
                    for (uu, yy) in ((a0 + i, ya), (a0 + i, yb)):
                        X, Z = (uu, fz) if ax == "x" else (fx, uu)
                        bb.set(X, yy, Z, "minecraft:spruce_fence")
        if y0 > 2:
            bb.fill(px1, y0, pz1, px2, y0, pz1, "minecraft:dark_oak_log[axis=x]")
            bb.fill(px1, y0, pz2, px2, y0, pz2, "minecraft:dark_oak_log[axis=x]")
            bb.fill(px1, y0, pz1, px1, y0, pz2, "minecraft:dark_oak_log[axis=z]")
            bb.fill(px2, y0, pz1, px2, y0, pz2, "minecraft:dark_oak_log[axis=z]")
    # the deck, a beam rim and railings
    bb.fill(px1 - 1, top, pz1 - 1, px2 + 1, top, pz2 + 1, "minecraft:spruce_planks")
    bb.fill(px1 - 1, top - 1, pz1 - 1, px2 + 1, top - 1, pz1 - 1, "minecraft:dark_oak_log[axis=x]")
    bb.fill(px1 - 1, top - 1, pz2 + 1, px2 + 1, top - 1, pz2 + 1, "minecraft:dark_oak_log[axis=x]")
    bb.fill(px1 - 1, top - 1, pz1 - 1, px1 - 1, top - 1, pz2 + 1, "minecraft:dark_oak_log[axis=z]")
    bb.fill(px2 + 1, top - 1, pz1 - 1, px2 + 1, top - 1, pz2 + 1, "minecraft:dark_oak_log[axis=z]")
    for (a_, b_, c_, d_) in ((px1 - 1, pz1 - 1, px2 + 1, pz1 - 1), (px1 - 1, pz1 - 1, px1 - 1, pz2 + 1),
                             (px2 + 1, pz1 - 1, px2 + 1, pz2 + 1), (px1 - 1, pz2 + 1, px2 - 2, pz2 + 1)):
        bb.fill(a_, top + 1, b_, c_, top + 1, d_, "minecraft:dark_oak_fence")
    # flag poles on the corners with Marine colours
    for (x, z) in ((px1 - 1, pz1 - 1), (px2 + 1, pz1 - 1), (px1 - 1, pz2 + 1), (px2 + 1, pz2 + 1)):
        bb.fill(x, top + 1, z, x, top + 9, z, "minecraft:dark_oak_fence")
        bb.set(x, top + 10, z, "minecraft:gold_block")
        d = 1 if x < cx else -1
        bb.fill(x + d, top + 6, z, x + 3 * d, top + 9, z, "minecraft:white_wool")
        bb.fill(x + d, top + 7, z, x + 3 * d, top + 7, z, "minecraft:blue_wool")
    # the execution frame: two tall posts, a double crossbeam, the kneeling board; banners off the beam
    fz = cz - 2
    for x in (cx - 4, cx + 4):
        bb.fill(x, top + 1, fz, x, top + 13, fz, "minecraft:dark_oak_log[axis=y]")
        bb.set(x, top + 1, fz + 1, "minecraft:dark_oak_stairs[facing=north,half=bottom]")
        bb.set(x, top + 1, fz - 1, "minecraft:dark_oak_stairs[facing=south,half=bottom]")
    bb.fill(cx - 6, top + 14, fz, cx + 6, top + 14, fz, "minecraft:dark_oak_log[axis=x]")
    bb.fill(cx - 4, top + 10, fz, cx + 4, top + 10, fz, "minecraft:dark_oak_log[axis=x]")
    for x in (cx - 6, cx + 6):
        bb.set(x, top + 13, fz + 1, "minecraft:red_wall_banner[facing=south]")
    for x in (cx - 2, cx + 2):
        bb.set(x, top + 13, fz + 1, "minecraft:white_wall_banner[facing=south]")
    bb.fill(cx - 1, top + 1, fz, cx + 1, top + 2, fz, "minecraft:spruce_planks")
    bb.set(cx, top + 2, fz, "minecraft:spruce_trapdoor[facing=south,half=top,open=false]")
    bb.set(cx, top + 1, fz + 2, "minecraft:spruce_slab[type=bottom]")
    # the stair: one long flight along the south face, rising east, landing onto the deck at the east end
    sz1, sz2 = pz2 + 2, pz2 + 4
    for i in range(top):
        x = px1 - 2 + i
        y = i + 1
        bb.fill(x, y, sz1, x, y, sz2, "minecraft:spruce_stairs[facing=west,half=bottom]")
        bb.fill(x, y - 1, sz1, x, y - 1, sz2, "minecraft:spruce_slab[type=top]") if y > 1 else None
        bb.set(x, y + 1, sz2 + 1, "minecraft:spruce_fence")
        if i % 4 == 0:
            bb.fill(x, 1, sz2 + 1, x, y, sz2 + 1, "minecraft:dark_oak_fence")
    bb.fill(px1 - 2 + top, top, sz1 - 2, px2 + 1, top, sz2, "minecraft:spruce_planks")
    bb.fill(px2 + 2, top + 1, sz1 - 2, px2 + 2, top + 1, sz2 + 1, "minecraft:dark_oak_fence")
    bb.fill(px1 - 2 + top, top + 1, sz2 + 1, px2 + 1, top + 1, sz2 + 1, "minecraft:dark_oak_fence")
    for x in (px1 - 2 + top, px2 + 1):
        bb.fill(x, 1, sz2, x, top - 1, sz2, "minecraft:dark_oak_log[axis=y]")
    # lanterns under the deck and on the frame
    for (x, z) in legs:
        bb.set(x, top - 2, z + 1 if z < cz else z - 1, "minecraft:lantern[hanging=true]")
    # crowd barrier round it, open at the stair foot
    bx1, bz1, bx2, bz2 = px1 - 5, pz1 - 4, px2 + 5, sz2 + 4
    for x in range(bx1, bx2 + 1):
        for z in (bz1, bz2):
            if not (z == bz2 and px1 - 4 <= x <= px1 + 1):
                bb.set(x, 1, z, "minecraft:spruce_fence")
    for z in range(bz1, bz2 + 1):
        bb.set(bx1, 1, z, "minecraft:spruce_fence")
        bb.set(bx2, 1, z, "minecraft:spruce_fence")


def clock_tower(bb, x, z):
    """A brick clock tower on the corner of the square, clock faces on four sides, an open belfry and a spire."""
    s = 9
    bb.fill(x - 1, -3, z - 1, x + s, 0, z + s, "minecraft:stone_bricks")
    bb.mix(x, 1, z, x + s - 1, 30, z + s - 1, ["minecraft:bricks", "minecraft:bricks", "minecraft:granite"], [0.7, 0.2, 0.1])
    bb.fill(x + 1, 1, z + 1, x + s - 2, 29, z + s - 2, AIR)
    for y in (8, 16, 24):
        bb.fill(x - 1, y, z - 1, x + s, y, z + s, "minecraft:stone_brick_slab[type=top]") if False else None
        bb.fill(x, y, z, x + s - 1, y, z, "minecraft:stone_bricks"); bb.fill(x, y, z + s - 1, x + s - 1, y, z + s - 1, "minecraft:stone_bricks")
        bb.fill(x, y, z, x, y, z + s - 1, "minecraft:stone_bricks"); bb.fill(x + s - 1, y, z, x + s - 1, y, z + s - 1, "minecraft:stone_bricks")
    c = x + s // 2
    cz = z + s // 2
    for (fx, fz, axis) in ((c, z - 1, "x"), (c, z + s, "x"), (x - 1, cz, "z"), (x + s, cz, "z")):
        for dy in range(-2, 3):
            for dd in range(-2, 3):
                if dy * dy + dd * dd <= 5:
                    if axis == "x":
                        bb.set(fx + dd, 21 + dy, fz, "minecraft:white_concrete")
                    else:
                        bb.set(fx, 21 + dy, fz + dd, "minecraft:white_concrete")
        if axis == "x":
            bb.set(fx, 21, fz, "minecraft:black_concrete"); bb.set(fx, 22, fz, "minecraft:black_concrete"); bb.set(fx + 1, 21, fz, "minecraft:black_concrete")
        else:
            bb.set(fx, 21, fz, "minecraft:black_concrete"); bb.set(fx, 22, fz, "minecraft:black_concrete"); bb.set(fx, 21, fz + 1, "minecraft:black_concrete")
    # belfry: open arches, a bell, then a copper spire
    for y in range(26, 30):
        for k in range(2, s - 2):
            bb.set(x + k, y, z, AIR); bb.set(x + k, y, z + s - 1, AIR); bb.set(x, y, z + k, AIR); bb.set(x + s - 1, y, z + k, AIR)
    bb.fill(x, 30, z, x + s - 1, 30, z + s - 1, "minecraft:stone_bricks")
    bb.set(c, 29, cz, "minecraft:bell[attachment=ceiling,facing=north]")
    for k in range(0, 10):
        r = (s - 1) / 2 * (1 - k / 10) + 0.3
        bb.fill_where(x - 1, 31 + k, z - 1, x + s, 31 + k, z + s,
                      lambda X, yy, Z, r=r: (np.abs(X - (x + (s - 1) / 2)) <= r) & (np.abs(Z - (z + (s - 1) / 2)) <= r),
                      "minecraft:oxidized_cut_copper" if k < 9 else "minecraft:lightning_rod")
    # a ladder inside to the belfry
    bb.fill(x + 1, 1, z + 1, x + 1, 30, z + 1, "minecraft:ladder[facing=east]")
    bb.fill(x + 1, 30, z + 1, x + 1, 30, z + 1, "minecraft:ladder[facing=east]")
    bb.fill(c, 1, z + s - 1, c, 3, z + s - 1, AIR)
    return (x - 2, z - 2, x + s + 2, z + s + 2)


# ------------------------------------------------------------------ townhouses
PALS = [
    dict(walls=["minecraft:bricks", "minecraft:bricks", "minecraft:granite"], frame="minecraft:stone_bricks",
         base=["minecraft:stone_bricks", "minecraft:cobblestone", "minecraft:andesite"], floor="minecraft:spruce_planks",
         wood="spruce", chimney="minecraft:bricks"),
    dict(walls=["minecraft:white_terracotta", "minecraft:calcite", "minecraft:smooth_sandstone"], frame="minecraft:dark_oak_log",
         base=["minecraft:cobblestone", "minecraft:stone_bricks", "minecraft:mossy_cobblestone"], floor="minecraft:oak_planks",
         wood="dark_oak", chimney="minecraft:bricks"),
    dict(walls=["minecraft:stone_bricks", "minecraft:andesite", "minecraft:stone_bricks"], frame="minecraft:polished_andesite",
         base=["minecraft:cobblestone", "minecraft:stone_bricks", "minecraft:andesite"], floor="minecraft:spruce_planks",
         wood="spruce", chimney="minecraft:stone_bricks"),
    dict(walls=["minecraft:yellow_terracotta", "minecraft:smooth_sandstone", "minecraft:white_terracotta"], frame="minecraft:spruce_log",
         base=["minecraft:cobblestone", "minecraft:stone_bricks", "minecraft:mossy_cobblestone"], floor="minecraft:birch_planks",
         wood="spruce", chimney="minecraft:bricks"),
]
ROOFS = ["minecraft:dark_oak_stairs", "minecraft:deepslate_tile_stairs", "minecraft:brick_stairs", "minecraft:spruce_stairs",
         "minecraft:mud_brick_stairs"]
SHOPS = [["kitchen", "living", "bedroom", "bedroom"], ["workshop", "storage", "bedroom"], ["storage", "living", "library", "bedroom"],
         ["kitchen", "bedroom", "living"], ["library", "living", "bedroom", "storage"]]


def row(bb, x1, x2, z0, d, rot, rng, tracker, audit, taken, k0):
    """A row of townhouses between x1 and x2 (or z1..z2 for rot 1/3), varying width, height and palette."""
    x = x1
    k = k0
    while x < x2 - 6:
        w = int(rng.integers(8, 12))
        if x + w > x2:
            w = x2 - x
        if w < 7:
            break
        fl = int(rng.integers(3, 5))
        mod, _, au = house_module(seed_of("lt", k), w if rot % 2 == 0 else d, d if rot % 2 == 0 else w, fl,
                                  ROOFS[k % len(ROOFS)], tracker, SHOPS[k % len(SHOPS)], pal=PALS[k % len(PALS)],
                                  timber=(k % 4 == 1), jetty=(k % 3 == 0))
        audit += au
        if rot % 2 == 0:
            place_house(bb, mod, w, d, x, 0, z0, rot)
            taken.append((x - 1, z0 - 2, x + w, z0 + d + 1))
        else:
            place_house(bb, mod, w, d, z0, 0, x, rot)
            taken.append((z0 - 2, x - 1, z0 + d + 1, x + w))
        x += w + (1 if rng.random() < 0.5 else 0)
        k += 1
    return k


def town(bb, rng, tracker, audit):
    taken = []
    x1, z1, x2, z2 = SQ
    k = 0
    # north side (facing the square), west and east sides, a gap in the south side for the harbour street
    k = row(bb, x1 - 12, x2 + 12, z1 - 13, 11, 0, rng, tracker, audit, taken, k)
    k = row(bb, z1, z2, x1 - 13, 11, 3, rng, tracker, audit, taken, k)        # west side, doors east
    k = row(bb, z1 + 12, z2, x2 + 3, 11, 1, rng, tracker, audit, taken, k)    # east side, doors west
    k = row(bb, x1 - 12, CX - 6, z2 + 4, 10, 2, rng, tracker, audit, taken, k)  # south side, doors north
    k = row(bb, CX + 6, x2 + 12, z2 + 4, 10, 2, rng, tracker, audit, taken, k)
    # outer streets: a second ring of smaller houses
    k = row(bb, 46, 150, 18, 10, 0, rng, tracker, audit, taken, k)
    k = row(bb, 40, 86, 127, 10, 1, rng, tracker, audit, taken, k)
    k = row(bb, 116, 146, 96, 10, 2, rng, tracker, audit, taken, k)
    k = row(bb, 46, 74, 108, 9, 2, rng, tracker, audit, taken, k)
    taken.append(clock_tower(bb, x2 + 3, z1))
    return taken


def streets(bb):
    """Cobbled streets: round the square's houses, the harbour street south, a street east."""
    x1, z1, x2, z2 = SQ
    def st_mask(X, Z):
        m = (rect_d(X, Z, (x1 - 16, z1 - 16, x2 + 16, z2 + 16)) == 0) & (rect_d(X, Z, SQ) > 0)
        m |= (np.abs(X - CX) <= 4) & (Z > z2) & (Z <= QUAY_Z)
        m |= (Z >= 31) & (Z <= 36) & (X > 40) & (X < 152)
        m |= (Z >= 88) & (Z <= 93) & (X > 40) & (X < 152)
        m |= (X >= 120) & (X <= 124) & (Z > 30) & (Z < QUAY_Z)
        return m & land(X, Z)
    NT.cover(bb, 0, 0, N - 1, N - 1, lambda X, Z: X * 0, STREET, 1561, mask=st_mask, under="minecraft:stone", core="minecraft:stone")


# ------------------------------------------------------------------ the Marine base
def marine_base(bb, tracker, audit):
    x1, z1, x2, z2 = BASE
    bb.fill(x1, 0, z1, x2, 0, z2, "minecraft:smooth_stone")
    NT.cover(bb, x1, z1, x2, z2, lambda X, Z: X * 0, [("minecraft:smooth_stone", 0.6), ("minecraft:polished_andesite", 0.25),
                                                      ("minecraft:andesite", 0.15)], 1571)
    # the wall with a gate on the east (toward the square)
    for (a, b, c, d) in ((x1, z1, x2, z1), (x1, z2, x2, z2), (x1, z1, x1, z2), (x2, z1, x2, z2)):
        bb.fill(a, 1, b, c, 5, d, "minecraft:white_concrete")
        bb.fill(a, 6, b, c, 6, d, "minecraft:light_blue_concrete")
    gz = (z1 + z2) // 2
    bb.fill(x2, 1, gz - 3, x2, 5, gz + 3, AIR)
    for z in (gz - 4, gz + 4):
        bb.fill(x2, 1, z, x2 + 1, 9, z, "minecraft:white_concrete")
        bb.set(x2, 10, z, "minecraft:light_blue_concrete")
    bb.fill(x2, 7, gz - 4, x2, 8, gz + 4, "minecraft:white_concrete")
    bb.fill(x2 + 1, 7, gz - 2, x2 + 1, 8, gz + 2, "minecraft:light_blue_concrete")
    # headquarters: three storeys, white with blue bands, the MARINE sign over the door
    hx1, hz1, hx2, hz2 = x1 + 3, z1 + 3, x1 + 22, z1 + 18
    top = tier(bb, hx1, hz1, hx2, hz2, 0, 3, 5, "minecraft:white_concrete", "minecraft:glass_pane", "minecraft:quartz_stairs",
               pilaster="minecraft:quartz_pillar[axis=y]", band="minecraft:light_blue_concrete", top_plate="minecraft:light_gray_concrete",
               every=3, pil_every=5)
    cornice(bb, hx1, hz1, hx2, hz2, top, "minecraft:quartz_stairs", parapet="minecraft:white_concrete")
    for k in range(3):
        wing_floor(bb, hx1 + 1, hz1 + 1, hx2 - 1, hz2 - 1, 1 + 5 * k, 4, "minecraft:white_concrete", seed_of("ltmb", k), tracker,
                   [("storage", "kitchen", "living"), ("bedroom", "bedroom", "living"), ("library", "workshop", "living")][k],
                   corridor="x", cw=3, carpet=(None, "minecraft:light_blue_carpet"), wood="spruce", audit=audit)
    cz = (hz1 + hz2) // 2
    bb.fill(hx2, 1, cz - 1, hx2, 3, cz + 1, AIR)
    bb.fill(hx1 + 1, 1, cz - 1, hx1 + 1, 16, cz - 1, "minecraft:ladder[facing=east]")
    for k in range(3):
        bb.fill(hx1 + 1, 5 * k + 5, cz - 1, hx1 + 1, 5 * k + 5, cz - 1, "minecraft:ladder[facing=east]") if k < 2 else None
    for (ch, dx) in (("M", 0),):
        pass
    bb.fill(hx2 + 1, 12, cz - 4, hx2 + 1, 13, cz + 4, "minecraft:light_blue_concrete")
    bb.fill(hx2 + 1, 12, cz - 3, hx2 + 1, 13, cz + 3, "minecraft:white_concrete")
    # flagpole with the World Government flag
    fx, fz = x1 + 28, z1 + 6
    bb.fill(fx, 1, fz, fx, 18, fz, "minecraft:iron_bars")
    bb.set(fx, 19, fz, "minecraft:lightning_rod")
    wg_flag(bb, fx, 18, fz + 1, w=9, h=6, axis="z")
    # drill yard: targets, racks, crates
    for z in range(z2 - 12, z2 - 2, 4):
        bb.set(x1 + 26, 1, z, "minecraft:target")
        bb.set(x1 + 26, 2, z, "minecraft:hay_block[axis=y]")
    for (x, z) in ((x1 + 4, z2 - 3), (x1 + 5, z2 - 3), (x1 + 4, z2 - 4), (x1 + 8, z2 - 3)):
        bb.set(x, 1, z, "minecraft:barrel[facing=up,open=false]")
    bb.fill(x1 + 10, 1, z2 - 2, x1 + 16, 1, z2 - 2, "minecraft:spruce_fence")
    # watchtowers on the corners
    for (tx, tz) in ((x1, z1), (x1, z2)):
        bb.fill(tx - 1, 1, tz - 1, tx + 1, 9, tz + 1, "minecraft:white_concrete")
        bb.fill(tx - 2, 10, tz - 2, tx + 2, 10, tz + 2, "minecraft:light_gray_concrete")
        bb.fill(tx - 2, 11, tz - 2, tx + 2, 11, tz + 2, "minecraft:white_concrete_powder" if False else "minecraft:iron_bars")
        bb.fill(tx - 1, 11, tz - 1, tx + 1, 11, tz + 1, AIR)
        bb.set(tx, 12, tz, "minecraft:lantern[hanging=false]")
    return (x1 - 3, z1 - 3, x2 + 3, z2 + 3)


# ------------------------------------------------------------------ the harbour
def harbour(bb, rng, tracker, audit):
    # the quay: stone edge with bollards and lamps, timber piers out into the water
    for x in range(2, N - 2):
        X, Z = np.array([[x]]), np.array([[QUAY_Z]])
        if SHORE(X, Z)[0, 0] < -8:
            continue
        bb.fill(x, -8, QUAY_Z - 2, x, 0, QUAY_Z, "minecraft:stone_bricks")
        bb.set(x, 0, QUAY_Z, "minecraft:polished_andesite")
        if x % 9 == 0:
            bb.set(x, 1, QUAY_Z, "minecraft:andesite_wall")
    for px in (36, 64, 122):
        for z in range(QUAY_Z + 1, QUAY_Z + 24):
            bb.fill(px - 1, 1, z, px + 1, 1, z, "minecraft:spruce_planks")
            if (z - QUAY_Z) % 5 == 0:
                bb.fill(px - 2, -9, z, px - 2, 1, z, "minecraft:spruce_log[axis=y]")
                bb.fill(px + 2, -9, z, px + 2, 1, z, "minecraft:spruce_log[axis=y]")
                bb.set(px + 2, 2, z, "minecraft:lantern[hanging=false]")
    stamp_ship(bb, "marine_warship", 46, QUAY_Z + 20, water_y=0, rot=0)
    stamp_ship(bb, "going_merry", 104, QUAY_Z + 15, water_y=0, rot=0)
    # warehouses along the quay
    for k, (x0, w) in enumerate(((118, 14), (136, 12))):
        mod, _, au = house_module(seed_of("ltwh", k), w, 10, 2, "minecraft:spruce_stairs", tracker, ["storage", "storage"],
                                  pal=PALS[2], timber=False, jetty=False)
        audit += au
        place_house(bb, mod, w, 10, x0, 0, QUAY_Z - 15, 0)
    for x in range(6, N - 6, 13):
        if abs(x - CX) > 6:
            lamp_post(bb, x, 1, QUAY_Z - 3, post="minecraft:dark_oak_fence", h=3)
    for (x, z) in ((90, QUAY_Z - 4), (91, QUAY_Z - 4), (90, QUAY_Z - 5), (70, QUAY_Z - 4)):
        bb.set(x, 1, z, "minecraft:barrel[facing=up,open=false]")


def scenery(bb, rng, taken):
    k = 0
    for _ in range(3000):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        X, Z = np.array([[x]]), np.array([[z]])
        if not land(X, Z)[0, 0] or SHORE(X, Z)[0, 0] < 6:
            continue
        if rect_d(X, Z, TOWN)[0, 0] == 0 and not (rng.random() < 0.15):
            continue
        if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken):
            continue
        name = bb.names[bb.get_region(x, hy(x, z), z, x, hy(x, z), z)[0, 0, 0]] or ""
        if "grass" not in name and "podzol" not in name and "moss" not in name:
            continue
        P.tree(bb, x, hy(x, z) + 1, z, int(rng.integers(6, 10)), ("oak", "birch", "oak", "spruce")[k % 4], rng)
        taken.append((x - 3, z - 3, x + 3, z + 3))
        k += 1
        if k >= 40:
            break
    print("trees:", k)


def design():
    bb = BigBuild(seed=1520, y_min=-12, y_max=60)
    tracker = P.PropTracker(1520)
    audit = []
    rng = np.random.default_rng(1520)
    terrain(bb)
    streets(bb)
    square(bb)
    scaffold(bb)
    taken = town(bb, rng, tracker, audit)
    taken.append(marine_base(bb, tracker, audit))
    harbour(bb, rng, tracker, audit)
    taken.append((0, QUAY_Z - 16, N, N))
    taken.append((SQ[0] - 16, SQ[1] - 16, SQ[2] + 16, SQ[3] + 16))
    scenery(bb, rng, taken)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 1590, density=0.25, kinds=NT.PLANTS_MEADOW, flowers=NT.FLOWERS,
              mask=lambda X, Z: land(X, Z) & (rect_d(X, Z, (SQ[0] - 16, SQ[1] - 16, SQ[2] + 16, SQ[3] + 16)) > 0))
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
    x1, z1, x2, z2 = BASE
    b.npc(x1 + 26, 1, (z1 + z2) // 2, "smoker", True)
    b.chest(x1 + 5, 1, z1 + 5, "marine", "east")
    for (gx, gz) in ((x2 + 3, (z1 + z2) // 2 - 3), (x2 + 3, (z1 + z2) // 2 + 3), (x1 + 20, z2 - 6)):
        b.guard(gx, 1, gz, "marine")
    cx = (SQ[0] + SQ[2]) // 2
    for (gx, gz) in ((cx - 12, SQ[1] + 32), (cx + 12, SQ[1] + 32)):
        b.guard(gx, 1, gz, "marine_rifle")
    return b, 0
