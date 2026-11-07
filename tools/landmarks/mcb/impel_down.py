"""Impel Down, the great underwater prison in the Calm Belt, redesigned with the Minecraft Builder skill
(dossier: mcb/dossiers/impel_down.md).

Above the sea: the round seastone fortress wall with buttresses, turrets and a corbelled parapet, the gatehouse over
the sea gate and the walled inner harbour, the jailers' barracks, armory and infirmary in the courtyard, and the great
stepped tower with the Marine flag over the central shaft. Below the sea, six levels going down, each a ring of
barred cells against the outer wall, a lit patrol corridor, a guard station of furnished rooms, and its own hell in the
middle: Lv1 Crimson Hell (blade-leaved red trees, needle grass), Lv2 Wild Beast Hell (beast pens, bones, moss), Lv3
Starvation Hell (scorching sand, dry wells, bleached bones), Lv4 Blazing Hell (the boiling lava cauldron with its
bridge, Magellan's office and the warden's rooms), Lv5 Freezing Hell (snow, ice, frozen prisoners, dead trees) with
Newkama Land hidden behind a crawl hole, and Lv6 Eternal Hell (black, silent cells of the worst criminals). A walled
stair winds down the central shaft through every level. ~126 x 126, 80 deep. y 0 = sea surface. (v2)"""
import math
import numpy as np
from mcb.kit import (BigBuild, P, AIR, seed_of, st, wing_floor, furnish, stair_core, set_if_air, lamp_post, tier,
                     cornice)
from mcb.bridge import to_canvas
from mcb.kit import ring_floor, wg_emblem, wg_flag
from mcb import nature as NT

SID = "impel_down"
TITLE = "Impel Down"
WATER_Y = 0
CUTS = [2, -14, -38, -62]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="none")

N = 126
CX, CZ = 63, 63
R = 50
SEA = "onepiece:seastone_bricks"
SEA_ST = "onepiece:seastone_brick_stairs"
SEA_W = "onepiece:seastone_brick_wall"
WALL = "minecraft:polished_deepslate"
BARS = "onepiece:prison_bars"
LH = 11                                     # level height (floor to floor)
LEVELS = [  # floor, wall, theme, guard kit
    ("minecraft:crimson_nylium", "minecraft:red_nether_bricks", "crimson", "jailer"),
    ("minecraft:moss_block", "minecraft:mossy_stone_bricks", "beast", "war_beast"),
    ("minecraft:sand", "minecraft:smooth_sandstone", "starve", "jailer"),
    ("minecraft:blackstone", "minecraft:polished_blackstone_bricks", "blaze", "warden_jailer"),
    ("minecraft:snow_block", "minecraft:packed_ice", "freeze", "warden_jailer"),
    ("minecraft:obsidian", "minecraft:obsidian", "eternal", "warden_jailer"),
]
SHAFT = (CX - 4, CZ - 4, 8)                 # stair well (x, z, size)
CELL_IN, CELL_OUT = R - 12, R - 2           # cell band radii
CORE = R - 15                                # radius of the open middle (inside the corridor)


def floor_y(k):
    return -8 - LH * (k + 1)


def dist(X, Z):
    return np.sqrt((X - CX) ** 2 + (Z - CZ) ** 2)


def ang(X, Z):
    return np.degrees(np.arctan2(Z - CZ, X - CX)) % 360


def body(bb):
    bottom = floor_y(5) - 1
    for y in range(bottom, 1):
        bb.fill_where(CX - R, y, CZ - R, CX + R, y, CZ + R, lambda X, yy, Z: dist(X, Z) <= R,
                      SEA if (y // 3) % 3 else WALL)
        bb.fill_where(CX - R, y, CZ - R, CX + R, y, CZ + R, lambda X, yy, Z: dist(X, Z) <= R - 2, AIR)
    bb.fill_where(CX - R, bottom, CZ - R, CX + R, bottom, CZ + R, lambda X, yy, Z: dist(X, Z) <= R, WALL)
    # the gap between the first level's ceiling and the courtyard: the jailers' undercroft (solid seastone)
    bb.fill_where(CX - R, floor_y(0) + LH, CZ - R, CX + R, 0, CZ + R, lambda X, yy, Z: dist(X, Z) <= R - 2, SEA)


def level(bb, k, rng, tracker, audit):
    fl, wl, theme, _ = LEVELS[k]
    y0 = floor_y(k)
    top = y0 + LH
    bb.fill_where(CX - R, y0, CZ - R, CX + R, y0, CZ + R, lambda X, y, Z: dist(X, Z) <= R - 2, fl)
    bb.fill_where(CX - R, top, CZ - R, CX + R, top, CZ + R, lambda X, y, Z: dist(X, Z) <= R - 2, WALL)
    bb.fill_where(CX - R, y0 + 1, CZ - R, CX + R, top - 1, CZ + R, lambda X, y, Z: dist(X, Z) <= R - 2, AIR)
    bb.fill_where(CX - R, y0 + 1, CZ - R, CX + R, top - 1, CZ + R,
                  lambda X, y, Z: (dist(X, Z) <= R - 1) & (dist(X, Z) > R - 2.5), wl)
    # the ring of cells: walls every 10 degrees, bars on the inner face, a door gap of bars, a bunk and a bucket
    def cellwall(X, y, Z):
        d = dist(X, Z)
        a = ang(X, Z)
        seg = a % 10
        arc = np.minimum(seg, 10 - seg) * np.pi / 180 * d
        return (d >= CELL_IN) & (d < CELL_OUT) & (arc < 0.6)
    for y in range(y0 + 1, y0 + 6):
        bb.fill_where(CX - R, y, CZ - R, CX + R, y, CZ + R, cellwall, wl)
        bb.fill_where(CX - R, y, CZ - R, CX + R, y, CZ + R,
                      lambda X, yy, Z: (dist(X, Z) >= CELL_IN) & (dist(X, Z) < CELL_IN + 1) & ~cellwall(X, yy, Z), BARS)
    bb.fill_where(CX - R, y0 + 6, CZ - R, CX + R, y0 + 6, CZ + R,
                  lambda X, y, Z: (dist(X, Z) >= CELL_IN) & (dist(X, Z) < CELL_OUT), wl)
    # an upper gallery walk over the cells with a railing
    bb.fill_where(CX - R, y0 + 7, CZ - R, CX + R, y0 + 7, CZ + R,
                  lambda X, y, Z: (dist(X, Z) >= CELL_IN) & (dist(X, Z) < CELL_IN + 1), "minecraft:iron_bars")
    for s in range(36):
        a = math.radians(s * 10 + 5)
        px, pz = round(CX + (R - 5) * math.cos(a)), round(CZ + (R - 5) * math.sin(a))
        bb.set(px, y0 + 1, pz, "minecraft:black_carpet" if theme == "eternal" else "minecraft:gray_carpet")
        qx, qz = round(CX + (R - 3) * math.cos(a)), round(CZ + (R - 3) * math.sin(a))
        bb.set(qx, y0 + 5, qz, "minecraft:iron_chain[axis=y]")
        bb.set(qx, y0 + 4, qz, "minecraft:iron_chain[axis=y]")
        if theme != "eternal" or s % 3 == 0:
            bb.set(qx, y0 + 1, qz, ["minecraft:cauldron", "minecraft:skeleton_skull[rotation=0]", "minecraft:cobweb",
                                    "minecraft:barrel[facing=up]"][int(rng.integers(4))])
    # the lit patrol corridor between the cells and the hell
    for s in range(24):
        a = math.radians(s * 15)
        x, z = round(CX + (CELL_IN - 2) * math.cos(a)), round(CZ + (CELL_IN - 2) * math.sin(a))
        bb.set(x, top - 1, z, "minecraft:lantern[hanging=true]" if theme != "eternal" else "minecraft:soul_lantern[hanging=true]")
    # the hell in the middle
    def core(X, y, Z):
        return dist(X, Z) <= CORE
    if theme == "crimson":
        for _ in range(26):
            a, r = rng.uniform(0, 2 * math.pi), rng.uniform(9, CORE - 3)
            x, z = round(CX + r * math.cos(a)), round(CZ + r * math.sin(a))
            h = int(rng.integers(5, 9))
            bb.fill(x, y0 + 1, z, x, y0 + h, z, "minecraft:crimson_stem[axis=y]")
            for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1), (2, 0), (-2, 0), (0, 2), (0, -2)):
                set_if_air(bb, x + dx, y0 + h - int(rng.integers(0, 2)), z + dz, "minecraft:nether_wart_block")
            set_if_air(bb, x, y0 + h + 1, z, "minecraft:nether_wart_block")
        for _ in range(300):
            a, r = rng.uniform(0, 2 * math.pi), rng.uniform(7, CORE)
            set_if_air(bb, round(CX + r * math.cos(a)), y0 + 1, round(CZ + r * math.sin(a)),
                       ["minecraft:crimson_roots", "minecraft:pointed_dripstone[thickness=tip,vertical_direction=up,waterlogged=false]"][int(rng.integers(2))])
    elif theme == "beast":
        for i in range(6):
            a = math.radians(i * 60 + 30)
            px, pz = round(CX + 22 * math.cos(a)), round(CZ + 22 * math.sin(a))
            bb.fill(px - 4, y0 + 1, pz - 4, px + 4, y0 + 6, pz + 4, "minecraft:iron_bars")
            bb.fill(px - 3, y0 + 1, pz - 3, px + 3, y0 + 6, pz + 3, AIR)
            bb.fill(px - 3, y0, pz - 3, px + 3, y0, pz + 3, "minecraft:coarse_dirt")
            bb.fill(px - 2, y0 + 1, pz - 2, px - 1, y0 + 1, pz - 1, "minecraft:hay_block[axis=y]")
            bb.set(px + 2, y0 + 1, pz + 2, "minecraft:bone_block[axis=y]")
            bb.fill(px - 4, y0 + 7, pz - 4, px + 4, y0 + 7, pz + 4, "minecraft:mossy_stone_bricks")
        for _ in range(120):
            a, r = rng.uniform(0, 2 * math.pi), rng.uniform(7, CORE)
            set_if_air(bb, round(CX + r * math.cos(a)), y0 + 1, round(CZ + r * math.sin(a)),
                       ["minecraft:fern", "minecraft:bone_block[axis=x]", "minecraft:moss_carpet", "minecraft:short_grass"][int(rng.integers(4))])
    elif theme == "starve":
        bb.fill_where(CX - CORE, y0, CZ - CORE, CX + CORE, y0, CZ + CORE, core, "minecraft:sand")
        for (dx, dz) in ((-16, 0), (16, 0), (0, 16), (0, -16)):
            bb.cylinder(CX + dx, y0 + 1, CZ + dz, 3, y0 + 2, "minecraft:cobblestone")
            bb.cylinder(CX + dx, y0 - 3, CZ + dz, 2, y0 + 2, AIR)
            bb.fill(CX + dx - 3, y0 + 3, CZ + dz, CX + dx + 3, y0 + 3, CZ + dz, "minecraft:spruce_planks")
        for _ in range(90):
            a, r = rng.uniform(0, 2 * math.pi), rng.uniform(7, CORE)
            set_if_air(bb, round(CX + r * math.cos(a)), y0 + 1, round(CZ + r * math.sin(a)),
                       ["minecraft:dead_bush", "minecraft:bone_block[axis=z]", "minecraft:skeleton_skull[rotation=4]"][int(rng.integers(3))])
        for s in range(0, 360, 30):
            a = math.radians(s)
            bb.set(round(CX + 12 * math.cos(a)), top - 1, round(CZ + 12 * math.sin(a)), "minecraft:shroomlight")
    elif theme == "blaze":
        bb.fill_where(CX - 24, y0 - 3, CZ - 24, CX + 24, y0 + 2, CZ + 24,
                      lambda X, y, Z: (dist(X, Z) <= 22) & (dist(X, Z) > 18) & (y >= y0), "minecraft:polished_blackstone_bricks")
        bb.fill_where(CX - 24, y0 - 3, CZ - 24, CX + 24, y0 - 3, CZ + 24, lambda X, y, Z: dist(X, Z) <= 19, "minecraft:blackstone")
        for y in range(y0 - 2, y0 + 2):
            bb.fill_where(CX - 24, y, CZ - 24, CX + 24, y, CZ + 24, lambda X, yy, Z: dist(X, Z) <= 18, "minecraft:lava[level=0]")
        bb.fill(CX - 1, y0 + 2, CZ - 22, CX + 1, y0 + 2, CZ - 6, "minecraft:polished_blackstone_bricks")
        bb.fill(CX - 1, y0 + 3, CZ - 22, CX - 1, y0 + 3, CZ - 6, "minecraft:polished_blackstone_wall")
        bb.fill(CX + 1, y0 + 3, CZ - 22, CX + 1, y0 + 3, CZ - 6, "minecraft:polished_blackstone_wall")
        bb.fill(CX - 1, y0 + 2, CZ + 6, CX + 1, y0 + 2, CZ + 22, "minecraft:polished_blackstone_bricks")
        for s in range(0, 360, 20):
            a = math.radians(s)
            bb.set(round(CX + 20 * math.cos(a)), y0 + 3, round(CZ + 20 * math.sin(a)),
                   "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    elif theme == "freeze":
        bb.fill_where(CX - CORE, y0, CZ - CORE, CX + CORE, y0, CZ + CORE, core, "minecraft:snow_block")
        for _ in range(16):
            a, r = rng.uniform(0, 2 * math.pi), rng.uniform(10, CORE - 3)
            x, z = round(CX + r * math.cos(a)), round(CZ + r * math.sin(a))
            if rng.random() < 0.5:
                bb.fill(x, y0 + 1, z, x, y0 + 2, z, "minecraft:blue_ice")            # a frozen prisoner
                bb.set(x, y0 + 3, z, "minecraft:packed_ice")
            else:
                h = int(rng.integers(4, 7))
                bb.fill(x, y0 + 1, z, x, y0 + h, z, "minecraft:stripped_spruce_log[axis=y]")
                for (dx, dz) in ((1, 0), (-1, 0), (0, 1)):
                    bb.set(x + dx, y0 + h - 1, z + dz, "minecraft:spruce_fence")
                    set_if_air(bb, x + dx, y0 + h, z + dz, "minecraft:snow[layers=1]")
        for _ in range(250):
            a, r = rng.uniform(0, 2 * math.pi), rng.uniform(7, CORE)
            set_if_air(bb, round(CX + r * math.cos(a)), y0 + 1, round(CZ + r * math.sin(a)), "minecraft:snow[layers=2]")
    elif theme == "eternal":
        bb.fill_where(CX - CORE, y0, CZ - CORE, CX + CORE, y0, CZ + CORE, core, "minecraft:polished_blackstone")
        for i in range(8):                       # the solitary cells of the worst criminals in the middle
            a = math.radians(i * 45 + 22.5)
            px, pz = round(CX + 20 * math.cos(a)), round(CZ + 20 * math.sin(a))
            bb.fill(px - 3, y0 + 1, pz - 3, px + 3, y0 + 5, pz + 3, "minecraft:obsidian")
            bb.fill(px - 2, y0 + 1, pz - 2, px + 2, y0 + 4, pz + 2, AIR)
            dx = -1 if px > CX else 1
            bb.fill(px + 3 * dx, y0 + 1, pz - 1, px + 3 * dx, y0 + 3, pz + 1, BARS)
            bb.set(px, y0 + 4, pz, "minecraft:soul_lantern[hanging=true]")
            bb.set(px - dx, y0 + 1, pz, "minecraft:black_carpet")
    # the guard station on every level: a block of furnished rooms on the east side of the shaft
    gx1, gz1, gx2, gz2 = CX + 8, CZ - 8, CX + 22, CZ + 8
    if theme == "blaze":
        gx1, gz1, gx2, gz2 = CX - 14, CZ - 30, CX + 14, CZ - 24
    bb.fill(gx1, y0 + 1, gz1, gx2, y0 + 6, gz2, WALL)
    bb.fill(gx1 + 1, y0 + 1, gz1 + 1, gx2 - 1, y0 + 5, gz2 - 1, AIR)
    bb.fill(gx1 + 1, y0, gz1 + 1, gx2 - 1, y0, gz2 - 1, "minecraft:dark_oak_planks")
    rooms, doors = P.bsp_rooms(bb, gx1 + 1, gz1 + 1, gx2 - 1, gz2 - 1, y0 + 1, 5, WALL, min_room=5,
                               seed=seed_of("idg", k), max_room=9)
    dz_ = (gz1 + gz2) // 2
    if theme == "blaze":
        bb.fill(CX - 1, y0 + 1, gz2, CX + 1, y0 + 3, gz2, AIR)
        doors = doors + [(CX, gz2)]
    else:
        bb.fill(gx1, y0 + 1, dz_, gx1, y0 + 3, dz_, AIR)
        doors = doors + [(gx1, dz_)]
    furnish(bb, rooms, y0 + 1, 5, ["workshop", "bedroom", "storage", "kitchen"] if theme != "blaze" else
            ["library", "living", "bedroom"], seed_of("idgf", k), tracker, doors=doors, wood="dark_oak", audit=audit)
    for r in rooms:
        bb.set((r[0] + r[2]) // 2, y0 + 5, (r[1] + r[3]) // 2, "minecraft:lantern[hanging=true]")
    for x in range(gx1 + 2, gx2 - 1, 3):
        bb.set(x, y0 + 3, gz1, "minecraft:iron_bars")
        bb.set(x, y0 + 3, gz2, "minecraft:iron_bars")
    if theme == "freeze":
        newkama(bb, y0, tracker, audit)


def newkama(bb, y0, tracker, audit):
    """Newkama Land: a hidden pink party hall west of the shaft on Lv5, behind a crawl hole in an ice wall."""
    x1, z1, x2, z2 = CX - 30, CZ - 10, CX - 10, CZ + 10
    bb.fill(x1, y0 + 1, z1, x2, y0 + 8, z2, "minecraft:packed_ice")
    bb.fill(x1 + 1, y0 + 1, z1 + 1, x2 - 1, y0 + 7, z2 - 1, AIR)
    bb.fill(x1 + 1, y0, z1 + 1, x2 - 1, y0, z2 - 1, "minecraft:pink_wool")
    bb.fill(x1 + 1, y0 + 1, z1 + 1, x2 - 1, y0 + 7, z1 + 1, "minecraft:pink_concrete")
    bb.fill(x1 + 1, y0 + 1, z2 - 1, x2 - 1, y0 + 7, z2 - 1, "minecraft:magenta_concrete")
    bb.fill(x1 + 1, y0 + 1, z1 + 1, x1 + 1, y0 + 7, z2 - 1, "minecraft:purple_concrete")
    # the stage, a bar, disco lights, the crawl hole
    bb.fill(x1 + 2, y0 + 1, z1 + 4, x1 + 5, y0 + 1, z2 - 4, "minecraft:gold_block")
    for z in range(z1 + 3, z2 - 2, 3):
        bb.set(x1 + 3, y0 + 7, z, "minecraft:pearlescent_froglight[axis=y]")
        bb.set(x2 - 4, y0 + 7, z, "minecraft:verdant_froglight[axis=y]")
    for z in range(z1 + 3, z2 - 2):
        bb.set(x2 - 3, y0 + 1, z, "minecraft:cherry_planks")
    rooms = [(x1 + 7, z1 + 3, x2 - 5, (z1 + z2) // 2 - 1)]
    furnish(bb, rooms, y0 + 1, 6, ["living"], seed_of("newk"), tracker, wood="cherry", audit=audit)
    bb.fill(x2, y0 + 1, CZ, x2, y0 + 1, CZ, AIR)
    bb.set(x2, y0 + 2, CZ, "minecraft:packed_ice")


def shaft(bb):
    x, z, size = SHAFT
    floors = [floor_y(k) + 1 for k in range(6)] + [1]
    stair_core(bb, x, z, size, floor_y(5) + 1, 0, floors, WALL, "minecraft:polished_deepslate_stairs", slit=None)
    bb.fill(x - 1, 1, z - 1, x + size, 4, z + size, WALL)
    bb.fill(x, 1, z, x + size - 1, 3, z + size - 1, AIR)


GREY = ["minecraft:stone_bricks", "minecraft:cracked_stone_bricks", "minecraft:andesite", "minecraft:polished_andesite",
        "minecraft:tuff_bricks"]
TOP = 88                                     # v3: the great tower's roof deck
UP = (14, TOP + 22)                          # upper tower radius, its roof


def rad(y):
    """Outer radius of the tower at height y: a slight batter from R at the sea to R - 8 at the top."""
    return R - 8 * max(0, y) / TOP


def grey(X, y, Z, seed):
    """Index into GREY by smooth noise patches (no stripes, no modulo patterns)."""
    v = NT.noise(X * 2 + y, Z * 2 - y, seed, 5) * 0.7 + NT.noise(X + y * 3, Z, seed + 1, 2) * 0.3
    return np.clip((v * 6.5 - 1.6).astype(int), 0, len(GREY) - 1)


def surface(bb, rng, tracker, audit):
    """v3 (2026-10-30 audit: the v2 teal castle with witch-hat spires missed the show). Impel Down above the sea is
    one massive plain grey stone tower rising out of the Calm Belt: a battered drum ~100 across and 88 high, ribbed
    with flat buttresses, banded every 16 blocks, pierced only by small barred slits, crowned by a corbelled
    battlement, a smaller upper tower on the roof, and one great sea gate at the waterline on the south face that
    leads into the inner harbour. The jailers live and work inside: eight furnished floors round the central shaft."""
    # --- the drum: a 4-thick shell, grey stone in noise patches
    for y in range(1, TOP + 1):
        r = rad(y)
        sh = lambda X, yy, Z, r=r: (dist(X, Z) <= r) & (dist(X, Z) > r - 4)
        idx = None
        for k, blk in enumerate(GREY):
            bb.fill_where(CX - R, y, CZ - R, CX + R, y, CZ + R, lambda X, yy, Z, k=k, sh=sh: sh(X, yy, Z) & (grey(X, yy, Z, 5111) == k), blk)
    # flat buttress ribs every 20 degrees, 1 proud, and band courses every 16
    for s_ in range(0, 360, 20):
        t = math.radians(s_)
        for y in range(-6, TOP - 1):
            r = rad(y) + 0.6
            for w in (-1, 0, 1):
                px = round(CX + r * math.cos(t) - w * math.sin(t)); pz = round(CZ + r * math.sin(t) + w * math.cos(t))
                bb.set(px, y, pz, "minecraft:polished_andesite" if w == 0 else "minecraft:stone_bricks")
    for yb in range(16, TOP - 4, 16):
        bb.fill_where(CX - R - 1, yb, CZ - R - 1, CX + R + 1, yb, CZ + R + 1,
                      lambda X, y, Z, yb=yb: (dist(X, Z) <= rad(yb) + 1) & (dist(X, Z) > rad(yb) - 1), "minecraft:polished_deepslate")
    # small barred slit windows between the ribs
    for s_ in range(10, 360, 20):
        t = math.radians(s_)
        for y in range(26, TOP - 6, 8):
            r = rad(y) - 0.5
            x, z = round(CX + r * math.cos(t)), round(CZ + r * math.sin(t))
            if 60 < s_ < 120 and y < 30:
                continue
            bb.fill(x, y, z, x, y + 1, z, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
    # --- the crown: corbels out, a crenellated parapet, the roof deck
    for i, y in enumerate((TOP - 2, TOP - 1, TOP)):
        bb.fill_where(CX - R, y, CZ - R, CX + R, y, CZ + R,
                      lambda X, yy, Z, i=i: (dist(X, Z) <= rad(TOP) + 1 + i) & (dist(X, Z) > rad(TOP) - 3), "minecraft:stone_bricks")
    bb.fill_where(CX - R, TOP, CZ - R, CX + R, TOP, CZ + R, lambda X, y, Z: dist(X, Z) <= rad(TOP) + 3, "minecraft:smooth_stone")
    bb.fill_where(CX - R, TOP + 1, CZ - R, CX + R, TOP + 2, CZ + R,
                  lambda X, y, Z: (dist(X, Z) <= rad(TOP) + 3) & (dist(X, Z) > rad(TOP) + 1.6), "minecraft:stone_bricks")
    bb.fill_where(CX - R, TOP + 2, CZ - R, CX + R, TOP + 2, CZ + R,
                  lambda X, y, Z: (dist(X, Z) <= rad(TOP) + 3) & (dist(X, Z) > rad(TOP) + 1.6) & ((np.round(ang(X, Z) / 3).astype(int) % 2) == 0), AIR)
    # --- the upper tower on the roof (the warden's lookout), same grey, crenellated, the WG flag
    ur, ut = UP
    for y in range(TOP + 1, ut + 1):
        for k, blk in enumerate(GREY):
            bb.fill_where(CX - ur, y, CZ - ur, CX + ur, y, CZ + ur,
                          lambda X, yy, Z, k=k: (dist(X, Z) <= ur) & (dist(X, Z) > ur - 2) & (grey(X, yy, Z, 5112) == k), blk)
    bb.fill_where(CX - ur, TOP + 11, CZ - ur, CX + ur, TOP + 11, CZ + ur, lambda X, y, Z: dist(X, Z) <= ur - 2, "minecraft:spruce_planks")
    bb.fill_where(CX - ur - 1, ut, CZ - ur - 1, CX + ur + 1, ut, CZ + ur + 1, lambda X, y, Z: dist(X, Z) <= ur + 1, "minecraft:smooth_stone")
    bb.fill_where(CX - ur - 1, ut + 1, CZ - ur - 1, CX + ur + 1, ut + 1, CZ + ur + 1,
                  lambda X, y, Z: (dist(X, Z) <= ur + 1) & (dist(X, Z) > ur) & ((np.round(ang(X, Z) / 8).astype(int) % 2) == 0), "minecraft:stone_brick_wall")
    for y in range(TOP + 4, ut - 2, 6):
        for a_ in range(0, 360, 45):
            t = math.radians(a_)
            x, z = round(CX + (ur - 0.5) * math.cos(t)), round(CZ + (ur - 0.5) * math.sin(t))
            bb.fill(x, y, z, x, y + 1, z, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
    bb.fill(CX - 1, TOP + 1, CZ + ur - 1, CX + 1, TOP + 3, CZ + ur - 1, AIR)           # door from the roof deck
    bb.fill(CX, ut + 1, CZ, CX, ut + 14, CZ, "minecraft:dark_oak_fence")
    wg_flag(bb, CX + 1, ut + 14, CZ, w=9, h=6)
    # --- inside: hollow, eight furnished floors round the shaft, solid fill where the square floors meet the drum
    H2 = 27
    core = (SHAFT[0] - 1, SHAFT[1] - 1, SHAFT[0] + SHAFT[2], SHAFT[1] + SHAFT[2])
    kinds_up = [["bedroom", "bedroom", "storeroom"], ["office", "library"], ["armory", "storeroom"], ["mess", "kitchen"],
                ["infirmary", "bedroom"], ["office", "radio"], ["barracks", "storeroom"], ["captain", "library"]]
    for i, fy in enumerate(range(22, 79, 8)):
        bb.fill_where(CX - R, fy, CZ - R, CX + R, fy, CZ + R, lambda X, y, Z, fy=fy: dist(X, Z) <= rad(fy) - 3.5, "minecraft:smooth_stone")
        bb.fill_where(CX - R, fy + 1, CZ - R, CX + R, fy + 7, CZ + R,
                      lambda X, y, Z: (dist(X, Z) <= rad(y) - 3.5) & ((np.abs(X - CX) > H2) | (np.abs(Z - CZ) > H2)), "minecraft:stone")
        ring_floor(bb, CX - H2, CZ - H2, CX + H2, CZ + H2, fy + 1, 6, core, "minecraft:stone_bricks", seed_of("idf", fy), tracker,
                   kinds_up[i], cw=2, audit=audit, wood="dark_oak", kit=True)
    bb.fill_where(CX - R, TOP - 2, CZ - R, CX + R, TOP - 1, CZ + R, lambda X, y, Z: dist(X, Z) <= rad(TOP) - 3, "minecraft:stone")
    # --- the ground hall: the inner harbour behind the sea gate, guard halls to the sides and north
    bb.fill_where(CX - R, 0, CZ - R, CX + R, 0, CZ + R, lambda X, y, Z: dist(X, Z) <= rad(0) - 3.5, "minecraft:polished_andesite")
    hx1, hx2, hz1 = CX - 13, CX + 13, CZ + 7
    bb.fill(hx1, -6, hz1, hx2, -1, CZ + R + 2, "minecraft:water[level=0]")
    bb.fill(hx1 + 3, 0, hz1, hx2 - 3, 0, CZ + R + 2, "minecraft:water[level=0]")      # quays 3 wide either side
    bb.fill(hx1 - 1, -7, hz1 - 1, hx2 + 1, -7, CZ + R + 2, "minecraft:stone_bricks")
    bb.fill(hx1 - 1, 1, hz1 - 1, hx2 + 1, 21, hz1 - 1, "minecraft:stone_bricks")      # the hall's back wall
    bb.fill(CX - 1, 1, hz1 - 1, CX + 1, 3, hz1 - 1, AIR)                               # to the shaft
    for (a1, a2) in ((CX - H2, hx1 - 2), (hx2 + 2, CX + H2)):
        bb.fill(a1 - 1 if a1 < CX else a1 - 1, 1, CZ - H2, a1 - 1 if a1 < CX else a1 - 1, 21, CZ + H2, "minecraft:stone_bricks")
        bb.fill(a2 + 1, 1, CZ - H2, a2 + 1, 21, CZ + H2, "minecraft:stone_bricks")
        for k, y in enumerate((1, 8, 15)):
            if y > 1:
                bb.fill(a1, y - 1, CZ - H2, a2, y - 1, CZ + H2, "minecraft:smooth_stone")
            wing_floor(bb, a1, CZ - H2, a2, CZ + H2, y, 6, "minecraft:stone_bricks", seed_of("idg", a1, y), tracker,
                       [["barracks", "storeroom"], ["armory", "office"], ["bedroom", "infirmary"]][k], corridor="z", cw=3,
                       audit=audit, max_room=9, wood="dark_oak", kit=True)
        door_x = a2 + 1 if a1 < CX else a1 - 1
        bb.fill(door_x, 1, CZ + 16, door_x, 3, CZ + 18, AIR)
        bb.fill(a1 + 1, 1, CZ - H2 + 1, a1 + 1, 15, CZ - H2 + 1, "minecraft:ladder[facing=south]")
    for y in (1, 8, 15):                                                                 # north block, links the halls
        if y > 1:
            bb.fill(hx1 - 1, y - 1, CZ - H2, hx2 + 1, y - 1, core[1] - 2, "minecraft:smooth_stone")
        wing_floor(bb, hx1 - 1, CZ - H2, hx2 + 1, core[1] - 2, y, 6, "minecraft:stone_bricks", seed_of("idn", y), tracker,
                   [["office", "library"], ["storeroom", "radio"], ["bedroom"]][(y - 1) // 7], corridor="x", cw=3, audit=audit,
                   max_room=9, wood="dark_oak", kit=True)
    bb.fill(hx1 - 1, 21, hz1 - 1, hx2 + 1, 21, CZ + R, "minecraft:stone_bricks")        # harbour hall ceiling
    # mooring posts, crates and lamps on the quays, the hall lit by wall lights
    for z in range(hz1 + 2, CZ + 44, 6):
        for x in (hx1 + 1, hx2 - 1):
            bb.set(x, 1, z, "minecraft:polished_andesite_wall")
        for x in (hx1 - 1, hx2 + 1):
            bb.set(x, 6, z, "minecraft:lantern[hanging=false]" if False else "minecraft:sea_lantern")
    for (x, z) in ((hx1 + 1, hz1 + 4), (hx2 - 1, hz1 + 10), (hx1 + 2, hz1 + 16)):
        bb.set(x, 1, z, "onepiece:crate_stack[facing=east]")
    # --- the great sea gate (south): an arched opening at the waterline, a raised portcullis, the WG emblem above
    gz = CZ + int(rad(0)) - 5
    for y in range(-6, 19):
        half = 10 if y <= 12 else int(round(math.sqrt(max(0, 100 - ((y - 12) * 1.6) ** 2))))
        bb.fill(CX - half, y, gz, CX + half, y, CZ + R + 2, AIR if y > 0 else "minecraft:water[level=0]")
        bb.fill(CX - half - 1, y, gz - 1, CX - half - 1, y, CZ + R + 2, "minecraft:polished_deepslate")
        bb.fill(CX + half + 1, y, gz - 1, CX + half + 1, y, CZ + R + 2, "minecraft:polished_deepslate")
    for x in range(CX - 9, CX + 10, 2):
        bb.fill(x, 14, gz + 2, x, 18, gz + 2, BARS)
    wg_emblem(bb, CX, 30, CZ + int(rad(30)) + 1, "minecraft:white_concrete", k=1.3, axis="x")
    # the shaft's stair continues up through every floor to the roof
    x, z, size = SHAFT
    floors = [1, 8, 15] + [fy + 1 for fy in range(22, 79, 8)]
    stair_core(bb, x, z, size, 1, 78, floors, WALL, "minecraft:polished_deepslate_stairs", slit=None)
    bb.fill(x + 1, 79, z + 1, x + 1, TOP + 1, z + 1, "minecraft:ladder[facing=south]")
    bb.fill(x, 80, z, x + size - 1, TOP - 1, z + size - 1, AIR)
    bb.fill(x + 1, 79, z + 1, x + 1, TOP + 1, z + 1, "minecraft:ladder[facing=south]")
    bb.fill(x + 1, TOP, z + 1, x + 1, TOP, z + 1, "minecraft:ladder[facing=south]")


def design():
    bb = BigBuild(seed=511, y_min=floor_y(5) - 4, y_max=140)
    tracker = P.PropTracker(511)
    audit = []
    rng = np.random.default_rng(511)
    body(bb)
    for k in range(6):
        level(bb, k, rng, tracker, audit)
    shaft(bb)
    surface(bb, rng, tracker, audit)
    return bb, audit


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    b.chest(CX + 12, floor_y(0) + 1, CZ - 6, "impel_down", "west")
    b.chest(CX + 12, floor_y(2) + 1, CZ + 6, "hard", "west")
    b.chest(CX - 12, floor_y(3) + 1, CZ - 26, "impel_down", "south")
    b.chest(CX - 4, floor_y(5) + 1, CZ - 12, "eternal_hell", "south")
    b.chest(CX + 4, floor_y(5) + 1, CZ - 12, "legendary", "south")
    b.chest(CX - 28, floor_y(4) + 1, CZ - 8, "newkama", "east")
    for k in range(6):
        y0 = floor_y(k)
        kit = LEVELS[k][3]
        b.guards(kit, ((CX, CZ + 30), (CX, CZ - 30), (CX + 30, CZ), (CX - 30, CZ))[:2 + k // 2], y=y0 + 1)
    b.guards("pacifista", ((CX + 12, CZ + 22),), y=floor_y(5) + 1)
    b.guards("jailer", ((CX - 10, CZ + 20), (CX + 10, CZ + 20)), y=1)
    return b, 0
