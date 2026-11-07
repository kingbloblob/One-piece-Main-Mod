"""G-5 v2, redesigned with the Minecraft Builder skill: the New World's rowdiest Marine branch (Vergo's, then
Smoker's men).

A low snowy island with spruce woods and grey rocks, frozen floes along the shore. The base is a walled compound of
grey concrete: a curtain wall with square watchtowers and gun platforms, the south side opening onto a harbour basin
between two long breakwater moles, where two Marine warships lie at the quay under the cranes.

Inside: the brutalist headquarters (four storeys of offices, barracks, armory, records and an infirmary round a
central tower with Smoker's office and the radio room, a radar mast on top) with a huge "G-5" painted on the tower;
two long barracks blocks; the canteen, more bar than mess hall (a long counter, barrels, rowdy tables, the kitchen
behind); the brig with its cell row; a training yard with a boxing ring, sandbags and targets; fuel tanks and the
vehicle shed. 168 x 160, y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, set_if_air, wing_floor, tier, cornice, lamp_post, stair_core, steady
from mcb.kit_interiors import furnish_kit, table_group, bar_counter, bench, wall_lights
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.shipstamp import stamp_ship

SID = "g5_base"
TITLE = "G-5 Marine Base"
CUTS = [3, 10, 20, 30]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

NX, NZ = 168, 160
GY = 3                                   # compound ground
WALL = (28, 20, 140, 114)                # curtain wall (x1, z1, x2, z2); south side = harbour quay
BASIN = (40, 116, 128, 146)              # harbour basin between the moles
_ISLE = NT.outline(84, 78, 70, 5050, wobble=0.07)
CON = ["minecraft:light_gray_concrete", "minecraft:smooth_stone", "minecraft:polished_andesite", "minecraft:gray_concrete"]
SNOW = [("minecraft:snow_block", 0.62), ("minecraft:powder_snow", 0.0), ("minecraft:packed_ice", 0.04), ("minecraft:stone", 0.08),
        ("minecraft:gravel", 0.0), ("minecraft:coarse_dirt", 0.06), ("minecraft:podzol", 0.06), ("minecraft:grass_block", 0.14)]
ROCK = [("minecraft:stone", 0.4), ("minecraft:andesite", 0.25), ("minecraft:tuff", 0.1), ("minecraft:cobblestone", 0.1),
        ("minecraft:snow_block", 0.15)]
YARD = [("minecraft:gray_concrete", 0.25), ("minecraft:light_gray_concrete", 0.2), ("minecraft:stone", 0.15),
        ("minecraft:andesite", 0.15), ("minecraft:snow_block", 0.25)]
HQ = (58, 30, 110, 66)
TOWER = (74, 38, 94, 58)
FH = 6


def rect_d(X, Z, r):
    dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0)
    dz = np.maximum(np.maximum(r[1] - Z, Z - r[3]), 0)
    return np.hypot(dx, dz)


def basin(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    return (X >= BASIN[0]) & (X <= BASIN[2]) & (Z >= BASIN[1])


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = _ISLE(X, Z)
    hills = 4 + NT.fbm(X, Z, 5051, 26) * 12 * np.clip((60 - Z) / 40.0, 0.2, 1)
    h = np.where(d < 10, 1 + (hills - 1) * np.clip(d / 10.0, 0, 1) ** 1.5, hills)
    wall = np.clip((rect_d(X, Z, WALL) - 2) / 12.0, 0, 1)
    h = GY * (1 - wall) + h * wall
    h = np.where(basin(X, Z), -7, h)
    h = np.where(d < 1.5, -5 - np.clip(-d, 0, 6), h)
    return np.round(h)


X_, Z_ = np.arange(NX)[:, None].astype(float), np.arange(NZ)[None, :].astype(float)
HMAP = _height(X_, Z_).astype(int)
G = np.zeros_like(HMAP)
for _a, _b in (((slice(1, None), slice(None)), (slice(None, -1), slice(None))), ((slice(None), slice(1, None)), (slice(None), slice(None, -1)))):
    _d = np.abs(HMAP[_a] - HMAP[_b]); G[_a] = np.maximum(G[_a], _d); G[_b] = np.maximum(G[_b], _d)


def _ix(X, Z):
    return np.clip(np.asarray(X).astype(int), 0, NX - 1), np.clip(np.asarray(Z).astype(int), 0, NZ - 1)


def height(X, Z):
    return HMAP[_ix(X, Z)]


def land(X, Z):
    return HMAP[_ix(X, Z)] >= 1


def hy(x, z):
    return int(HMAP[min(max(int(x), 0), NX - 1), min(max(int(z), 0), NZ - 1)])


def terrain(bb):
    inside = lambda X, Z: rect_d(X, Z, WALL) <= 0
    steep = lambda X, Z: G[_ix(X, Z)] >= 3
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, height, SNOW, 5052, mask=lambda X, Z: land(X, Z) & ~inside(X, Z) & ~steep(X, Z),
             under="minecraft:dirt", core="minecraft:stone", base=-8)
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, height, ROCK, 5053, mask=lambda X, Z: land(X, Z) & ~inside(X, Z) & steep(X, Z),
             under="minecraft:stone", core="minecraft:stone", base=-8)
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, height, YARD, 5054, mask=lambda X, Z: inside(X, Z) & land(X, Z), under="minecraft:stone",
             core="minecraft:stone", base=-8)
    wet = lambda X, Z: ~land(X, Z)
    bed = lambda X, Z: np.minimum(height(X, Z), -2)
    bb.fill_where(0, -12, 0, NX - 1, 0, NZ - 1, lambda X, y, Z: wet(X, Z) & (y > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, NX - 1, 0, NZ - 1, lambda X, y, Z: wet(X, Z) & (y == bed(X, Z)), "minecraft:gravel")
    bb.fill_where(0, -12, 0, NX - 1, 0, NZ - 1, lambda X, y, Z: wet(X, Z) & (y < bed(X, Z)) & (y >= bed(X, Z) - 3), "minecraft:stone")
    # ice floes on the open sea near the shore (packed ice never melts)
    sh = lambda X, Z: _ISLE(X, Z)
    bb.fill_where(0, 0, 0, NX - 1, 0, NZ - 1, lambda X, y, Z: wet(X, Z) & ~basin(X, Z) & (sh(X, Z) > -9) &
                  (NT.noise(X, Z, 5055, 5) > 0.66), "minecraft:packed_ice")
    # snow layers on the snow outside the walls
    bb.fill_where(0, 1, 0, NX - 1, 40, NZ - 1, lambda X, y, Z: land(X, Z) & ~inside(X, Z) & ~steep(X, Z) & (y == height(X, Z) + 1)
                  & (NT.noise(X, Z, 5056, 6) > 0.45), "minecraft:snow[layers=1]")


# ------------------------------------------------------------------ walls, quay, moles
def curtain(bb):
    x1, z1, x2, z2 = WALL
    y = GY
    for (a, b, c, d) in ((x1, z1, x2, z1 + 2), (x1, z1, x1 + 2, z2), (x2 - 2, z1, x2, z2)):
        bb.mix(a, y - 4, b, c, y + 9, d, CON, [0.7, 0.18, 0.08, 0.04])
        bb.fill(a, y - 4, b, c, y + 1, d, "minecraft:gray_concrete")
        bb.fill(a, y + 10, b, c, y + 10, d, "minecraft:gray_concrete")
    for (a, b, c, d) in ((x1 + 1, z1 + 1, x2 - 1, z1 + 1), (x1 + 1, z1 + 1, x1 + 1, z2), (x2 - 1, z1 + 1, x2 - 1, z2)):
        bb.fill(a, y + 11, b, c, y + 11, d, AIR)
    for x in range(x1, x2 + 1, 2):
        bb.set(x, y + 11, z1, "minecraft:stone_brick_wall")
    for z in range(z1, z2 + 1, 2):
        bb.set(x1, y + 11, z, "minecraft:stone_brick_wall"); bb.set(x2, y + 11, z, "minecraft:stone_brick_wall")
    # rusted streaks and repairs: G-5 is not tidy
    rng = np.random.default_rng(5057)
    for _ in range(22):
        side = int(rng.integers(3))
        if side == 0:
            x, z = int(rng.integers(x1 + 2, x2 - 2)), z1 - 0
        else:
            x, z = (x1 if side == 1 else x2), int(rng.integers(z1 + 2, z2 - 2))
        yy = int(rng.integers(y + 2, y + 8))
        bb.fill(x, yy - int(rng.integers(1, 4)), z, x, yy, z, "minecraft:brown_terracotta" if rng.random() < 0.5 else "minecraft:cracked_stone_bricks")
    # watchtowers on the corners and the middle of the long sides
    for (tx, tz) in ((x1 + 1, z1 + 1), (x2 - 1, z1 + 1), (x1 + 1, z2 - 2), (x2 - 1, z2 - 2), ((x1 + x2) // 2, z1 + 1), (x1 + 1, (z1 + z2) // 2),
                     (x2 - 1, (z1 + z2) // 2)):
        bb.fill(tx - 3, y - 4, tz - 3, tx + 3, y + 16, tz + 3, "minecraft:gray_concrete")
        bb.fill(tx - 2, y + 1, tz - 2, tx + 2, y + 15, tz + 2, AIR)
        bb.fill(tx - 2, y + 11, tz - 2, tx + 2, y + 11, tz + 2, "minecraft:spruce_planks")
        bb.fill(tx - 4, y + 17, tz - 4, tx + 4, y + 17, tz + 4, "minecraft:light_gray_concrete")
        for (a, b) in ((tx - 4, tz - 4), (tx + 4, tz - 4), (tx - 4, tz + 4), (tx + 4, tz + 4)):
            bb.fill(a, y + 18, b, a, y + 19, b, "minecraft:iron_bars")
        bb.fill(tx - 4, y + 20, tz - 4, tx + 4, y + 20, tz + 4, "minecraft:gray_concrete_powder" if False else "minecraft:smooth_stone_slab[type=bottom]")
        for k in range(-3, 4, 2):
            for (a, b) in ((tx + k, tz - 3), (tx + k, tz + 3), (tx - 3, tz + k), (tx + 3, tz + k)):
                bb.fill(a, y + 13, b, a, y + 14, b, "minecraft:glass_pane")
        bb.fill(tx, y + 1, tz + 2, tx, y + 17, tz + 2, "minecraft:ladder[facing=north]")
        bb.set(tx, y + 11, tz + 2, "minecraft:ladder[facing=north]")
        bb.fill(tx - 1, y + 17, tz + 2, tx + 1, y + 17, tz + 2, AIR); bb.set(tx, y + 17, tz + 2, "minecraft:ladder[facing=north]")
        bb.set(tx - 2, y + 18, tz - 2, "minecraft:sea_lantern")
        bb.set(tx + 2, y + 18, tz - 2, "onepiece:cannon[facing=north]" if tz < (z1 + z2) // 2 else "onepiece:cannon[facing=south]")
        bb.set(tx, y + 15, tz, "minecraft:lantern[hanging=true]")
        bb.fill(tx, y + 1, tz - 3 if tz > z1 + 1 else tz + 3, tx, y + 2, tz - 3 if tz > z1 + 1 else tz + 3, AIR)
    # the main gate in the north wall
    gx = (x1 + x2) // 2 + 14
    bb.fill(gx - 3, y + 1, z1, gx + 3, y + 7, z1 + 2, AIR)
    bb.fill(gx - 3, y + 8, z1, gx + 3, y + 8, z1 + 2, "minecraft:gray_concrete")
    for x in range(gx - 3, gx + 4):
        bb.fill(x, y + 5, z1, x, y + 7, z1, "minecraft:iron_bars")


def harbour(bb):
    x1, z1, x2, z2 = BASIN
    y = GY
    # the quay along the south of the compound
    bb.fill(WALL[0], -6, WALL[3], WALL[2], y, WALL[3] + 1, "minecraft:stone_bricks")
    bb.mix(WALL[0], y, WALL[3] - 1, WALL[2], y, WALL[3] + 1, ["minecraft:polished_andesite", "minecraft:smooth_stone", "minecraft:andesite"], [0.5, 0.3, 0.2])
    bb.fill(WALL[0], y + 1, WALL[3] - 1, WALL[2], y + 20, WALL[3] + 1, AIR)
    # the moles: long walls out into the sea with a light at each end
    for mx in (x1 - 4, x2 + 1):
        bb.fill(mx, -8, WALL[3], mx + 3, y, NZ - 12, "minecraft:stone_bricks")
        bb.mix(mx, y, WALL[3], mx + 3, y, NZ - 12, ["minecraft:polished_andesite", "minecraft:stone_bricks", "minecraft:cracked_stone_bricks"], [0.4, 0.4, 0.2])
        bb.fill(mx, y + 1, WALL[3], mx + 3, y + 12, NZ - 12, AIR)
        bb.fill(mx + (0 if mx < x1 else 3), y + 1, WALL[3] + 2, mx + (0 if mx < x1 else 3), y + 1, NZ - 12, "minecraft:stone_brick_wall")
        bb.fill(mx, y + 1, NZ - 15, mx + 3, y + 8, NZ - 12, "minecraft:white_concrete")
        bb.fill(mx, y + 3, NZ - 15, mx + 3, y + 3, NZ - 12, "minecraft:red_concrete")
        bb.fill(mx, y + 6, NZ - 15, mx + 3, y + 6, NZ - 12, "minecraft:red_concrete")
        bb.fill(mx + 1, y + 9, NZ - 14, mx + 2, y + 9, NZ - 13, "minecraft:sea_lantern")
        for z in range(WALL[3] + 6, NZ - 16, 8):
            lamp_post(bb, mx + (3 if mx < x1 else 0), y + 1, z, post="minecraft:iron_bars", h=3)
    for x in range(x1, x2 + 1, 6):
        bb.set(x, y + 1, WALL[3] + 1, "minecraft:stone_brick_wall")
    # cranes on the quay
    for cx in (x1 + 18, x2 - 18):
        cz = WALL[3] - 1
        for (a, b) in ((cx - 2, cz - 2), (cx + 2, cz - 2), (cx - 2, cz + 1), (cx + 2, cz + 1)):
            bb.fill(a, y + 1, b, a, y + 14, b, "minecraft:yellow_concrete" if (a + b) % 2 else "minecraft:black_concrete")
        bb.fill(cx - 2, y + 15, cz - 2, cx + 2, y + 15, cz + 1, "minecraft:yellow_concrete")
        bb.fill(cx, y + 15, cz + 2, cx, y + 15, cz + 14, "minecraft:yellow_concrete")
        bb.fill(cx, y + 6, cz + 13, cx, y + 14, cz + 13, "minecraft:iron_chain[axis=y]")
        bb.set(cx, y + 5, cz + 13, "minecraft:iron_block")
        bb.fill(cx - 1, y + 16, cz - 2, cx + 1, y + 18, cz, "minecraft:yellow_concrete")
    stamp_ship(bb, "marine_warship", (x1 + x2) // 2 - 22, z1 + 16, water_y=0, rot=1)
    stamp_ship(bb, "marine_warship", (x1 + x2) // 2 + 22, z1 + 18, water_y=0, rot=1)


# ------------------------------------------------------------------ buildings
def headquarters(bb, audit, tracker):
    x1, z1, x2, z2 = HQ
    y = GY
    top = tier(bb, x1, z1, x2, z2, y, 4, FH, CON[:3], "minecraft:glass_pane", "minecraft:smooth_stone_slab" if False else "minecraft:stone_stairs",
               pilaster="minecraft:gray_concrete", band="minecraft:blue_concrete", plate="minecraft:smooth_stone",
               top_plate="minecraft:gray_concrete", weights=[0.72, 0.18, 0.1], every=3, pil_every=6)
    cornice(bb, x1, z1, x2, z2, top, "minecraft:stone_stairs", parapet="minecraft:light_gray_concrete")
    kinds = [["office", "storeroom", "armory", "storeroom", "workshop", "office", "infirmary"],
             ["barracks", "barracks", "infirmary", "barracks", "armory", "barracks"],
             ["office", "library", "radio", "office", "bedroom", "storeroom"],
             ["barracks", "bedroom", "office", "bedroom", "barracks", "captain"]]
    for f in range(4):
        fy = y + 1 + FH * f
        wing_floor(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, fy, FH - 1, "minecraft:light_gray_concrete", seed_of("g5", f), tracker, kinds[f],
                   corridor="x", cw=3, wood="spruce", carpet=("minecraft:gray_concrete", "minecraft:blue_carpet"), audit=audit, kit=True,
                   keep=[TOWER, (x1 + 1, z1 + 1, x1 + 6, z1 + 6)], min_room=6, max_room=12)
    stair_core(bb, x1 + 2, z1 + 2, 4, y + 1, top, [y + 1 + FH * k for k in range(1, 4)] + [top + 1], "minecraft:light_gray_concrete",
               "minecraft:stone_stairs", slit=None)
    # the tower: through all four storeys and three more above, Smoker's office + radio room on top
    tx1, tz1, tx2, tz2 = TOWER
    ttop = tier(bb, tx1, tz1, tx2, tz2, y, 7, FH, CON[:3], "minecraft:glass_pane", "minecraft:stone_stairs", band="minecraft:blue_concrete",
                plate="minecraft:smooth_stone", top_plate="minecraft:gray_concrete", weights=[0.72, 0.18, 0.1], every=3)
    cornice(bb, tx1, tz1, tx2, tz2, ttop, "minecraft:stone_stairs", parapet="minecraft:light_gray_concrete")
    for f, k in enumerate(["tavern", "storeroom", "armory", "office", "radio", "library", "captain"]):
        furnish_kit(bb, (tx1 + 1, tz1 + 6, tx2 - 1, tz2 - 1), y + 1 + FH * f, FH - 1, k, wood="spruce", seed=5060 + f,
                    doors=[(tx1 + 3, tz1 + 5)], accent="blue")
    stair_core(bb, tx1 + 2, tz1 + 1, 4, y + 1, ttop, [y + 1 + FH * k for k in range(1, 7)] + [ttop + 1], "minecraft:light_gray_concrete",
               "minecraft:stone_stairs", slit=None)
    for f in range(7):
        bb.fill(tx1 + 1, y + 1 + FH * f, tz1 + 5, tx2 - 1, y + FH * (f + 1) - 1, tz1 + 5, "minecraft:light_gray_concrete")
        bb.fill(tx1 + 3, y + 1 + FH * f, tz1 + 5, tx1 + 3, y + 2 + FH * f, tz1 + 5, AIR)
    # doors from the HQ corridor into the tower on the four HQ floors
    cz = (z1 + z2) // 2
    for f in range(4):
        fy = y + 1 + FH * f
        bb.fill(tx1, fy, cz, tx1, fy + 1, cz, AIR); bb.fill(tx2, fy, cz, tx2, fy + 1, cz, AIR)
    # the big G-5 on the south face of the tower (painted letters, 3x3 pixels)
    glyphs = {"G": ["01110", "10000", "10011", "10001", "01111"], "-": ["00000", "00000", "11111", "00000", "00000"],
              "5": ["11111", "10000", "11110", "00001", "11110"]}
    px = tx1 + 1
    for ch in "G-5":
        rows = glyphs[ch]
        for r, row in enumerate(rows):
            for c, v in enumerate(row):
                if v == "1":
                    yy = ttop - 4 - r * 2
                    bb.fill(px + c, yy - 1, tz2 + 1, px + c, yy, tz2 + 1, "minecraft:blue_concrete")
        px += 6 if ch != "-" else 6
    # radar mast and the Marine flag
    mx, mz = (tx1 + tx2) // 2, (tz1 + tz2) // 2
    for yy in range(ttop + 1, ttop + 22):
        for (a, b) in ((mx - 1, mz - 1), (mx + 1, mz - 1), (mx - 1, mz + 1), (mx + 1, mz + 1)):
            if yy < ttop + 20 - (yy - ttop) // 8:
                bb.set(a, yy, b, "minecraft:iron_block" if yy % 5 == 0 else "minecraft:iron_bars")
    bb.fill(mx, ttop + 1, mz, mx, ttop + 26, mz, "minecraft:iron_bars")
    bb.fill(mx - 4, ttop + 22, mz, mx + 4, ttop + 22, mz, "minecraft:iron_bars")
    bb.set(mx, ttop + 27, mz, "minecraft:lightning_rod")
    for r in range(5):
        for c in range(8):
            gull = (r == 2 and 2 <= c <= 5) or (r == 1 and c in (1, 6)) or (r == 3 and c in (3, 4))
            bb.set(tx2 - 2 - c, ttop + 9 - r, tz1 + 1, "minecraft:blue_wool" if gull else "minecraft:white_wool")
    bb.fill(tx2 - 1, ttop + 1, tz1 + 1, tx2 - 1, ttop + 10, tz1 + 1, "minecraft:iron_bars")
    # entrance porch on the south side
    cx = (x1 + x2) // 2
    bb.fill(cx - 5, y + 1, z2 + 1, cx + 5, y + 1, z2 + 4, "minecraft:smooth_stone_slab[type=bottom]")
    bb.fill(cx - 5, y + 6, z2 + 1, cx + 5, y + 6, z2 + 5, "minecraft:gray_concrete")
    for xx in (cx - 5, cx + 5):
        bb.fill(xx, y + 1, z2 + 5, xx, y + 5, z2 + 5, "minecraft:polished_andesite")
    bb.fill(cx - 1, y + 1, z2, cx + 1, y + 3, z2, AIR)
    return top, ttop


def long_block(bb, audit, tracker, x1, z1, x2, z2, kinds, tag):
    y = GY
    top = tier(bb, x1, z1, x2, z2, y, 2, FH, CON[:3], "minecraft:glass_pane", "minecraft:stone_stairs", band="minecraft:blue_concrete",
               top_plate="minecraft:gray_concrete", weights=[0.72, 0.18, 0.1], every=3)
    cornice(bb, x1, z1, x2, z2, top, "minecraft:stone_stairs", parapet="minecraft:light_gray_concrete")
    for f in range(2):
        wing_floor(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, y + 1 + FH * f, FH - 1, "minecraft:light_gray_concrete", seed_of(tag, f), tracker,
                   kinds[f], corridor="z", cw=3, wood="spruce", audit=audit, keep=[(x1 + 1, z1 + 1, x1 + 4, z1 + 4)], kit=True, min_room=6)
    bb.fill(x1 + 2, y + 1, z1 + 2, x1 + 2, top, z1 + 2, "minecraft:ladder[facing=south]")
    bb.set(x1 + 2, y + FH, z1 + 2, "minecraft:ladder[facing=south]")
    side = x2 if x1 < 84 else x1
    for zz in ((z1 + z2) // 2, z1 + 6, z2 - 6):
        bb.fill(side, y + 1, zz - 1, side, y + 3, zz + 1, AIR)
    return top


def canteen(bb):
    """The canteen: a long bar room with the kitchen behind, barrels everywhere."""
    x1, z1, x2, z2 = 58, 74, 86, 96
    y = GY
    bb.fill(x1, y, z1, x2, y, z2, "minecraft:spruce_planks")
    bb.mix(x1, y + 1, z1, x2, y + 6, z2, ["minecraft:spruce_planks", "minecraft:stripped_spruce_log[axis=y]", "minecraft:light_gray_concrete"], [0.5, 0.2, 0.3])
    bb.fill(x1 + 1, y + 1, z1 + 1, x2 - 1, y + 6, z2 - 1, AIR)
    for x in range(x1, x2 + 1, 4):
        bb.fill(x, y + 1, z1, x, y + 6, z1, "minecraft:stripped_spruce_log[axis=y]"); bb.fill(x, y + 1, z2, x, y + 6, z2, "minecraft:stripped_spruce_log[axis=y]")
        if x + 2 < x2:
            bb.fill(x + 2, y + 3, z1, x + 2, y + 4, z1, "minecraft:glass_pane"); bb.fill(x + 2, y + 3, z2, x + 2, y + 4, z2, "minecraft:glass_pane")
    P.gable_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, y + 7, "minecraft:deepslate_tile_stairs", ridge="minecraft:deepslate_tiles", ridge_axis="x",
                 gable_fill="minecraft:spruce_planks", overhang=0)
    bb.fill(x1 + 1, y + 7, z1 + 1, x2 - 1, y + 7, z2 - 1, "minecraft:spruce_planks")
    bb.fill(x1 + 1, y + 1, z1 + 7, x2 - 1, y + 6, z1 + 7, "minecraft:spruce_planks")
    for xx in (x1 + 5, x2 - 5):
        bb.fill(xx, y + 1, z1 + 7, xx, y + 2, z1 + 7, AIR)
    furnish_kit(bb, (x1 + 1, z1 + 1, x2 - 1, z1 + 6), y + 1, 6, "kitchen", wood="spruce", seed=5070, doors=[(x1 + 5, z1 + 7), (x2 - 5, z1 + 7)])
    furnish_kit(bb, (x1 + 1, z1 + 8, x2 - 1, z2 - 1), y + 1, 6, "tavern", wood="spruce", seed=5071,
                doors=[(x1 + 5, z1 + 7), (x2 - 5, z1 + 7), ((x1 + x2) // 2, z2)], accent="blue")
    bb.fill((x1 + x2) // 2 - 1, y + 1, z2, (x1 + x2) // 2 + 1, y + 3, z2, AIR)
    # sign board over the door: "CANTEEN" is just a dark board with lanterns
    bb.fill((x1 + x2) // 2 - 4, y + 5, z2 + 1, (x1 + x2) // 2 + 4, y + 6, z2 + 1, "minecraft:dark_oak_planks")
    bb.set((x1 + x2) // 2 - 5, y + 5, z2 + 1, "minecraft:lantern[hanging=false]") if False else None


def brig(bb):
    """The brig: a stone block with a corridor and a row of barred cells each side."""
    x1, z1, x2, z2 = 92, 74, 116, 96
    y = GY
    bb.fill(x1, y, z1, x2, y, z2, "minecraft:polished_andesite")
    bb.mix(x1, y + 1, z1, x2, y + 6, z2, ["minecraft:stone_bricks", "minecraft:cracked_stone_bricks", "minecraft:gray_concrete"], [0.5, 0.2, 0.3])
    bb.fill(x1 + 1, y + 1, z1 + 1, x2 - 1, y + 5, z2 - 1, AIR)
    bb.fill(x1, y + 6, z1, x2, y + 6, z2, "minecraft:gray_concrete")
    cz = (z1 + z2) // 2
    for z in (cz - 2, cz + 2):
        bb.fill(x1 + 1, y + 1, z, x2 - 1, y + 5, z, "minecraft:iron_bars")
    for x in range(x1 + 5, x2, 5):
        bb.fill(x, y + 1, z1 + 1, x, y + 5, cz - 3, "minecraft:stone_bricks"); bb.fill(x, y + 1, cz + 3, x, y + 5, z2 - 1, "minecraft:stone_bricks")
    for x in range(x1 + 1, x2 - 3, 5):
        for (za, zb) in ((z1 + 1, cz - 3), (cz + 3, z2 - 1)):
            furnish_kit(bb, (x, za, x + 3, zb), y + 1, 5, "cell", seed=x * 7 + za)
            bb.set(x + 1, y + 5, (za + zb) // 2, "minecraft:lantern[hanging=true]")
    for x in range(x1 + 3, x2 - 1, 5):
        bb.set(x, y + 5, cz, "minecraft:lantern[hanging=true]")
    bb.fill(x1, y + 1, cz - 1, x1, y + 3, cz + 1, AIR)
    bb.set(x1 + 1, y + 1, cz - 1, "minecraft:chest[facing=east,type=single]")
    for zz in range(z1 + 3, z2, 4):
        bb.fill(x2, y + 3, zz, x2, y + 4, zz, "minecraft:iron_bars"); bb.fill(x1, y + 3, zz, x1, y + 4, zz, "minecraft:iron_bars")


def yard(bb, rng):
    y = GY
    # boxing ring in the yard
    rx, rz = 50, 100
    bb.fill(rx - 5, y + 1, rz - 5, rx + 5, y + 1, rz + 5, "minecraft:white_concrete")
    bb.fill(rx - 4, y + 1, rz - 4, rx + 4, y + 1, rz + 4, "minecraft:blue_wool" if False else "minecraft:light_gray_concrete")
    for (a, b) in ((rx - 5, rz - 5), (rx + 5, rz - 5), (rx - 5, rz + 5), (rx + 5, rz + 5)):
        bb.fill(a, y + 2, b, a, y + 4, b, "minecraft:red_concrete")
    for k in range(-4, 5):
        for (a, b) in ((rx + k, rz - 5), (rx + k, rz + 5), (rx - 5, rz + k), (rx + 5, rz + k)):
            bb.set(a, y + 3, b, "minecraft:white_wool" if False else "minecraft:iron_bars")
    # sandbags and targets by the west barracks
    for z in range(68, 96, 4):
        bb.fill(38, y + 1, z, 38, y + 2, z, "minecraft:hay_block[axis=y]"); bb.set(38, y + 3, z, "minecraft:target")
    for x in range(120, 134, 3):
        bb.fill(x, y + 1, 100, x, y + 2, 100, "minecraft:spruce_fence"); bb.set(x, y + 3, 100, "minecraft:carved_pumpkin[facing=north]")
    # fuel tanks and a vehicle shed in the north-east corner
    for (fx, fz) in ((124, 30), (132, 30), (124, 38)):
        bb.cylinder(fx, y + 1, fz, 3, y + 7, "minecraft:white_concrete")
        bb.cylinder(fx, y + 8, fz, 2, y + 8, "minecraft:white_concrete")
        bb.fill(fx - 3, y + 4, fz, fx + 3, y + 4, fz, "minecraft:red_concrete") if False else None
    # lamps and crates round the yard
    for (lx, lz) in ((56, 70), (112, 70), (56, 104), (112, 104), (88, 104), (34, 60), (134, 60)):
        lamp_post(bb, lx, y + 1, lz, post="minecraft:iron_bars", h=4)
    for _ in range(26):
        x, z = int(rng.integers(36, 132)), int(rng.integers(98, 110))
        if bb.get_region(x, y + 1, z, x, y + 1, z)[0, 0, 0] in (0, 1):
            bb.set(x, y + 1, z, "minecraft:barrel[facing=up,open=false]" if rng.random() < 0.6 else "minecraft:spruce_planks")


def scenery(bb, rng):
    """Spruce woods and boulders on the snowy hills outside the walls."""
    for _ in range(2200):
        x, z = int(rng.integers(6, NX - 6)), int(rng.integers(6, NZ - 6))
        X, Z = np.array([[x]]), np.array([[z]])
        if not land(X, Z)[0, 0] or _ISLE(X, Z)[0, 0] < 8 or rect_d(X, Z, WALL)[0, 0] < 5 or basin(X, Z)[0, 0]:
            continue
        y = hy(x, z)
        if NT.noise(X, Z, 5058, 14)[0, 0] > 0.5 and rng.random() < 0.18:
            P.tree(bb, x, y + 1, z, height=int(rng.integers(7, 13)), kind="spruce", rng=rng)
        elif rng.random() < 0.012:
            NT.boulder(bb, x, y, z, int(rng.integers(2, 4)), rng, blocks=("minecraft:stone", "minecraft:andesite", "minecraft:snow_block"))


def roof_clutter(bb, x1, z1, x2, z2, y, rng):
    """Flat-roof kit: vents, a water tank, an aerial and sandbag nests so the roofs aren't bare slabs."""
    taken = []
    for _ in range(max(3, (x2 - x1) * (z2 - z1) // 120)):
        x, z = int(rng.integers(x1 + 2, x2 - 2)), int(rng.integers(z1 + 2, z2 - 2))
        if any(abs(x - a) < 5 and abs(z - b) < 5 for a, b in taken) or bb.get_region(x, y + 1, z, x, y + 1, z)[0, 0, 0] > 1:
            continue
        taken.append((x, z))
        r = rng.random()
        if r < 0.45:
            bb.fill(x, y + 1, z, x + 1, y + 1, z + 1, "minecraft:polished_andesite")
            bb.fill(x, y + 2, z, x + 1, y + 2, z + 1, "minecraft:iron_trapdoor[facing=north,half=bottom,open=false]")
        elif r < 0.65:
            bb.fill(x - 1, y + 1, z - 1, x + 1, y + 2, z + 1, "minecraft:spruce_fence")
            bb.fill(x - 1, y + 3, z - 1, x + 1, y + 5, z + 1, "minecraft:spruce_planks")
            bb.fill(x - 1, y + 6, z - 1, x + 1, y + 6, z + 1, "minecraft:spruce_slab[type=bottom]")
        elif r < 0.8:
            bb.fill(x, y + 1, z, x, y + 7, z, "minecraft:iron_bars")
            bb.fill(x - 1, y + 5, z, x + 1, y + 5, z, "minecraft:iron_bars")
            bb.set(x, y + 8, z, "minecraft:lightning_rod")
        else:
            for (a, b) in ((x - 1, z - 1), (x, z - 1), (x + 1, z - 1), (x - 1, z), (x - 1, z + 1)):
                bb.set(a, y + 1, b, "minecraft:brown_wool" if False else "minecraft:mud_brick_wall")
            bb.set(x, y + 1, z, "minecraft:sea_lantern")


def design():
    bb = BigBuild(seed=5050, y_min=-14, y_max=96)
    tracker = P.PropTracker(5050)
    audit = []
    rng = np.random.default_rng(5050)
    terrain(bb)
    curtain(bb)
    harbour(bb)
    top, ttop = headquarters(bb, audit, tracker)
    long_block(bb, audit, tracker, 34, 36, 52, 92, [["barracks", "barracks", "mess", "barracks", "storeroom"], ["barracks", "barracks", "infirmary", "bedroom"]], "g5w")
    long_block(bb, audit, tracker, 116, 44, 134, 92, [["barracks", "armory", "barracks", "workshop", "storeroom"], ["barracks", "office", "barracks", "bedroom"]], "g5e")
    canteen(bb)
    brig(bb)
    roof_clutter(bb, HQ[0], HQ[1], HQ[2], HQ[3], top, rng)
    roof_clutter(bb, 34, 36, 52, 92, GY + 2 * FH, rng)
    roof_clutter(bb, 116, 44, 134, 92, GY + 2 * FH, rng)
    roof_clutter(bb, 92, 74, 116, 96, GY + 6, rng)
    yard(bb, rng)
    scenery(bb, rng)
    return bb, audit, top, ttop


def build():
    bb, audit, top, ttop = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    steady(b)
    b.chest(TOWER[0] + 4, GY + 1 + FH * 6, TOWER[3] - 2, "marine", "north")
    b.chest(HQ[0] + 10, GY + 1 + FH, HQ[1] + 3, "marine", "south")
    b.chest(114, GY + 1, 76, "hard", "west")
    b.chest(60, GY + 1, 76, "easy", "south")
    for (x, z) in ((84 - 4, HQ[3] + 6), (84 + 4, HQ[3] + 6), (70, 104), (100, 104), (WALL[0] + 26, WALL[3] + 1), (WALL[2] - 26, WALL[3] + 1)):
        b.guard(x, GY + 1, z, "marine")
    for (x, z) in ((WALL[0] + 1, WALL[1] + 1), (WALL[2] - 1, WALL[1] + 1)):
        b.guard(x, GY + 18, z, "marine_rifle")
    b.guard(TOWER[0] + 8, GY + 1 + FH * 6, TOWER[1] + 10, "elite_marine")
    b.guard(50, GY + 2, 100, "elite_marine")
    return b, 0
