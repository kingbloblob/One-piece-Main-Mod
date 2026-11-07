"""Shells Town v2, redesigned with the Minecraft Builder skill: the East Blue Marine base (153rd Branch) once run by
Axe-Hand Morgan, and the town below it.

A green island with the harbour on the east. On a raised stone terrace on the west stands the Marine base: a white
wall with blue coping, corner watchtowers and a gate; inside, the tall white headquarters (five storeys, blue floor
bands, MARINE across the top, the gull crest over the door) with Morgan's huge stone statue on its roof, axe-hand
raised; the dirt yard with the wooden post Zoro was tied to, the flagpole and training posts; the barracks, the
armory and the stores. A ramp runs from the gate down into the town: streets of plaster and brick houses, Rika's
family restaurant with its terrace, shops, a little church, and the quay with piers, a Marine warship and boats.
168 x 168. y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, furnish, set_if_air, cornice, tier, wing_floor, \
    house_module, place_house, lamp_post, wg_flag, glyph
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.shipstamp import stamp_ship

SID = "shells_town"
TITLE = "Shells Town Marine Base"
CUTS = [3, 10, 22]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 168
_S1 = NT.outline(84, 86, 76, 2520, wobble=0.09)
_S2 = NT.outline(54, 56, 50, 2521, wobble=0.06)
SHORE = lambda X, Z: np.maximum(_S1(X, Z), _S2(X, Z))
QUAY_X = 138                        # the quay edge; harbour water east of it
TY = 1                              # town level
BY = 8                              # base terrace level
BASE = (18, 28, 74, 80)
TOWN = (78, 18, 136, 148)
TOWN2 = (18, 88, 136, 148)
GATE_Z = 54

STREET = [("minecraft:cobblestone", 0.35), ("minecraft:stone_bricks", 0.2), ("minecraft:andesite", 0.15),
          ("minecraft:mossy_cobblestone", 0.1), ("minecraft:packed_mud", 0.1), ("minecraft:polished_andesite", 0.1)]
SAND = [("minecraft:sand", 0.7), ("minecraft:sandstone", 0.15), ("minecraft:clay", 0.15)]
ROCK = [("minecraft:stone", 0.4), ("minecraft:andesite", 0.25), ("minecraft:cobblestone", 0.2), ("minecraft:mossy_cobblestone", 0.15)]
PALS = [
    dict(walls=["minecraft:white_terracotta", "minecraft:calcite", "minecraft:smooth_sandstone"], frame="minecraft:dark_oak_log",
         base=["minecraft:cobblestone", "minecraft:stone_bricks", "minecraft:mossy_cobblestone"], floor="minecraft:oak_planks",
         wood="dark_oak", chimney="minecraft:bricks"),
    dict(walls=["minecraft:bricks", "minecraft:bricks", "minecraft:granite"], frame="minecraft:stone_bricks",
         base=["minecraft:stone_bricks", "minecraft:cobblestone", "minecraft:andesite"], floor="minecraft:spruce_planks",
         wood="spruce", chimney="minecraft:bricks"),
    dict(walls=["minecraft:yellow_terracotta", "minecraft:smooth_sandstone", "minecraft:white_terracotta"], frame="minecraft:spruce_log",
         base=["minecraft:cobblestone", "minecraft:stone_bricks", "minecraft:mossy_cobblestone"], floor="minecraft:birch_planks",
         wood="spruce", chimney="minecraft:bricks"),
    dict(walls=["minecraft:light_blue_terracotta", "minecraft:white_terracotta", "minecraft:calcite"], frame="minecraft:stripped_oak_log",
         base=["minecraft:cobblestone", "minecraft:stone_bricks", "minecraft:andesite"], floor="minecraft:oak_planks",
         wood="oak", chimney="minecraft:bricks"),
]
ROOFS = ["minecraft:brick_stairs", "minecraft:dark_oak_stairs", "minecraft:deepslate_tile_stairs", "minecraft:red_nether_brick_stairs",
         "minecraft:spruce_stairs", "minecraft:mud_brick_stairs"]
KINDS = [["kitchen", "living", "bedroom", "bedroom"], ["workshop", "storage", "bedroom"], ["storage", "living", "library", "bedroom"],
         ["kitchen", "bedroom", "living"], ["dining", "living", "bedroom", "storage"]]
FONT = {"M": ["#...#", "##.##", "#.#.#", "#...#", "#...#"], "A": [".###.", "#...#", "#####", "#...#", "#...#"],
        "R": ["####.", "#...#", "####.", "#..#.", "#...#"], "I": ["#####", "..#..", "..#..", "..#..", "#####"],
        "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#"], "E": ["#####", "#....", "####.", "#....", "#####"]}


def rect_d(X, Z, r):
    dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0)
    dz = np.maximum(np.maximum(r[1] - Z, Z - r[3]), 0)
    return np.hypot(dx, dz)


def street_mask(X, Z):
    X = np.asarray(X); Z = np.asarray(Z)
    m = (np.abs(Z - GATE_Z) <= 3) & (X > BASE[2]) & (X <= QUAY_X)
    m |= (np.abs(X - 108) <= 2) & (Z > TOWN[1]) & (Z < TOWN[3])
    m |= (np.abs(Z - 98) <= 2) & (X > TOWN2[0]) & (X < QUAY_X)
    m |= (np.abs(Z - 126) <= 2) & (X > TOWN2[0] + 6) & (X < QUAY_X)
    m |= (np.abs(X - 50) <= 2) & (Z > 98) & (Z < TOWN2[3])
    m |= (X >= QUAY_X - 6) & (X <= QUAY_X) & (Z > 22) & (Z < 146)
    return m


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = SHORE(X, Z)
    h = 4 + NT.fbm(X, Z, 2522, 26) * 14 - 3
    h = h * np.clip((d - 1.5) / 10.0, 0, 1)
    flat = np.minimum(rect_d(X, Z, TOWN), rect_d(X, Z, TOWN2))
    w = np.clip(flat / 10.0, 0, 1)
    h = TY * (1 - w) + h * w
    b = rect_d(X, Z, (BASE[0] - 4, BASE[1] - 4, BASE[2] + 4, BASE[3] + 4))
    h = np.where(b <= 0, BY, np.where(b < 8, np.maximum(h, BY - b * 0.9), h))
    # the ramp from the gate down to the town street
    ramp = (np.abs(Z - GATE_Z) <= 3) & (X > BASE[2] + 3) & (X < BASE[2] + 3 + (BY - TY) * 2 + 1)
    h = np.where(ramp, BY - (X - BASE[2] - 3) / 2.0, h)
    h = np.where(X > QUAY_X, -3, h)
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
    return (SHORE(X, Z) > 1.5) & (np.asarray(X) <= QUAY_X)


def hy(x, z):
    return int(HMAP[min(max(x, 0), N - 1), min(max(z, 0), N - 1)])


def terrain(bb):
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SAND, 2531, mask=lambda X, Z: land(X, Z) & (height(X, Z) <= 1) & (SHORE(X, Z) < 7),
             under="minecraft:sandstone", core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, ROCK, 2532, mask=lambda X, Z: land(X, Z) & steep(X, Z), under="minecraft:stone",
             core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, NT.MEADOW, 2533,
             mask=lambda X, Z: land(X, Z) & ~steep(X, Z) & ((height(X, Z) > 1) | (SHORE(X, Z) >= 7)), core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, STREET, 2534, mask=lambda X, Z: land(X, Z) & street_mask(X, Z), core="minecraft:stone")
    bed = lambda X, Z: np.where(np.asarray(X) > QUAY_X, np.minimum(-3 - np.clip((np.asarray(X) - QUAY_X) * 0.5, 0, 7),
                                                                    np.round(-2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10))),
                                np.round(-2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10)))
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy == bed(X, Z)), "minecraft:sand")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy < bed(X, Z)) & (yy >= bed(X, Z) - 2), "minecraft:stone")
    # stone retaining wall round the base terrace
    x1, z1, x2, z2 = BASE[0] - 4, BASE[1] - 4, BASE[2] + 4, BASE[3] + 4
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if (x in (x1, x2) or z in (z1, z2)) and not (x == x2 and abs(z - GATE_Z) <= 3):
                bb.fill(x, -2, z, x, BY, z, ("minecraft:stone_bricks", "minecraft:mossy_stone_bricks", "minecraft:cracked_stone_bricks")[(x * 7 + z * 3) % 5 % 3])
    NT.cover(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, lambda X, Z: X * 0 + BY,
             [("minecraft:coarse_dirt", 0.35), ("minecraft:dirt", 0.2), ("minecraft:packed_mud", 0.2), ("minecraft:dirt_path", 0.15),
              ("minecraft:rooted_dirt", 0.1)], 2535)


# ------------------------------------------------------------------ the Marine base
def morgan_statue(bb, x, y, z):
    """Axe-Hand Morgan in stone, facing east: boots, long coat, broad chest, iron jaw, left fist on the hip, the right
    arm raised high with the great axe in place of the hand."""
    S = "minecraft:smooth_stone"
    C = "minecraft:polished_andesite"
    for dz in (-2, 2):                                                    # legs and boots
        bb.fill(x - 1, y, z + dz - 1, x + 1, y + 1, z + dz, "minecraft:polished_deepslate")
        bb.fill(x - 1, y + 2, z + dz - 1, x, y + 5, z + dz, S)
    bb.fill(x - 2, y + 4, z - 4, x + 1, y + 8, z + 4, C)                  # coat skirt
    bb.fill(x - 2, y + 9, z - 4, x + 1, y + 13, z + 4, S)                 # chest
    bb.fill(x + 2, y + 10, z - 2, x + 2, y + 12, z + 2, S)
    bb.fill(x - 2, y + 9, z - 5, x + 1, y + 9, z + 5, C)                  # belt line
    bb.fill(x - 2, y + 13, z - 5, x + 1, y + 13, z + 5, C)                # epaulettes
    bb.fill(x - 1, y + 14, z - 1, x + 1, y + 17, z + 1, S)                # head
    bb.fill(x + 2, y + 14, z - 1, x + 2, y + 15, z + 1, "minecraft:iron_block")   # the iron jaw
    bb.set(x + 2, y + 16, z - 1, "minecraft:polished_blackstone"); bb.set(x + 2, y + 16, z + 1, "minecraft:polished_blackstone")
    bb.fill(x - 2, y + 18, z - 2, x + 1, y + 18, z + 2, C)                # cap
    bb.fill(x - 1, y + 19, z - 1, x, y + 19, z + 1, C)
    bb.fill(x - 1, y + 6, z - 6, x, y + 12, z - 5, S)                     # left arm, fist on hip
    bb.fill(x - 1, y + 6, z - 5, x + 1, y + 7, z - 4, S)
    bb.fill(x - 1, y + 12, z + 5, x, y + 22, z + 6, S)                    # right arm raised
    bb.fill(x - 1, y + 23, z + 5, x, y + 23, z + 6, "minecraft:iron_block")
    for k in range(-3, 4):                                                # the axe blade, a broad half-moon
        hgt = 4 - abs(k) // 2
        bb.fill(x - 1 + k * 0 , y + 23, z + 7, x, y + 23 + 0, z + 7, "minecraft:iron_block")
        bb.fill(x + k - 0, y + 24 - hgt // 2, z + 6, x + k, y + 24 + hgt, z + 6, "minecraft:iron_block")
    bb.fill(x - 3, y + 26, z + 6, x + 3, y + 26, z + 6, "minecraft:iron_block")


def hq(bb, tracker, audit):
    """The headquarters: five white storeys with blue bands and pilasters, a porch with the gull crest, MARINE on top."""
    x1, z1, x2, z2 = 26, 38, 50, 70
    y0 = BY
    top = tier(bb, x1, z1, x2, z2, y0, 5, 5, "minecraft:white_concrete", "minecraft:glass_pane", "minecraft:quartz_stairs",
               pilaster="minecraft:quartz_pillar[axis=y]", band="minecraft:light_blue_concrete", top_plate="minecraft:light_gray_concrete",
               every=3, pil_every=4)
    cornice(bb, x1, z1, x2, z2, top, "minecraft:quartz_stairs", parapet="minecraft:white_concrete")
    cz = (z1 + z2) // 2
    kinds = [("storage", "kitchen", "dining"), ("bedroom", "bedroom", "living"), ("library", "workshop", "living"),
             ("bedroom", "living", "library"), ("library", "living", "storage")]
    for k in range(5):
        wing_floor(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, y0 + 1 + 5 * k, 4, "minecraft:white_concrete", seed_of("stmb", k), tracker,
                   kinds[k], corridor="z", cw=3, carpet=(None, "minecraft:light_blue_carpet"), wood="spruce", audit=audit,
                   keep=[(x1 + 1, z1 + 1, x1 + 3, z1 + 3)])
    bb.fill(x1 + 2, y0 + 1, z1 + 2, x1 + 2, top, z1 + 2, "minecraft:ladder[facing=south]")
    for k in range(1, 6):
        bb.set(x1 + 2, y0 + 5 * k, z1 + 2, "minecraft:ladder[facing=south]")
    bb.set(x1 + 2, top, z1 + 2, "minecraft:ladder[facing=south]")
    bb.set(x1 + 2, top + 1, z1 + 2, AIR)
    # the door and porch on the east face
    bb.fill(x2, y0 + 1, cz - 1, x2, y0 + 3, cz + 1, AIR)
    bb.fill(x2 + 1, y0, cz - 4, x2 + 4, y0, cz + 4, "minecraft:polished_andesite")
    for z in (cz - 4, cz + 4):
        bb.fill(x2 + 4, y0 + 1, z, x2 + 4, y0 + 5, z, "minecraft:quartz_pillar[axis=y]")
    bb.fill(x2 + 1, y0 + 6, cz - 5, x2 + 4, y0 + 6, cz + 5, "minecraft:light_blue_concrete")
    bb.fill(x2 + 1, y0 + 7, cz - 4, x2 + 4, y0 + 7, cz + 4, "minecraft:quartz_slab[type=bottom]")
    gull = ["..#.....#..", ".###...###.", "#####.#####", "....###....", ".....#....."]
    glyph(bb, [r for r in gull], x2 + 1, y0 + 12, cz - 5, "minecraft:blue_concrete", axis="z")
    # MARINE across the top floor
    word = "MARINE"
    rows = ["".join(FONT[ch][r] + "." for ch in word) for r in range(5)]
    glyph(bb, rows, x2 + 1, top - 1, cz - len(rows[0]) // 2, "minecraft:blue_concrete", axis="z")
    glyph(bb, rows, x1 - 1, top - 1, cz - len(rows[0]) // 2, "minecraft:blue_concrete", axis="z")
    morgan_statue(bb, (x1 + x2) // 2, top + 1, cz)
    return (x1 - 2, z1 - 2, x2 + 6, z2 + 2), top


def barracks(bb, tracker, audit, x1, z1, x2, z2, kinds, floors, seed):
    top = tier(bb, x1, z1, x2, z2, BY, floors, 5, "minecraft:white_concrete", "minecraft:glass_pane", "minecraft:smooth_stone_slab",
               band="minecraft:light_blue_concrete", top_plate="minecraft:light_gray_concrete", every=3)
    for k in range(floors):
        wing_floor(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, BY + 1 + 5 * k, 4, "minecraft:white_concrete", seed_of(seed, k), tracker,
                   kinds, corridor="x" if x2 - x1 > z2 - z1 else "z", cw=3, wood="spruce", audit=audit,
                   keep=[(x1 + 1, z1 + 1, x1 + 3, z1 + 3)])
    bb.fill(x1 + 2, BY + 1, z1 + 2, x1 + 2, top - 1, z1 + 2, "minecraft:ladder[facing=south]")
    bb.fill(x1 - 1, top, z1 - 1, x2 + 1, top, z2 + 1, "minecraft:light_blue_concrete")
    P.gable_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, top + 1, "minecraft:deepslate_tile_stairs", gable_fill="minecraft:white_concrete",
                 overhang=1)
    return top


def marine_base(bb, tracker, audit):
    x1, z1, x2, z2 = BASE
    y = BY
    for (a, b, c, d) in ((x1, z1, x2, z1), (x1, z2, x2, z2), (x1, z1, x1, z2), (x2, z1, x2, z2)):
        bb.fill(a, y + 1, b, c, y + 6, d, "minecraft:white_concrete")
        bb.fill(a, y + 7, b, c, y + 7, d, "minecraft:light_blue_concrete")
    # the gate on the east, toward the town
    bb.fill(x2, y + 1, GATE_Z - 3, x2, y + 6, GATE_Z + 3, AIR)
    for z in (GATE_Z - 4, GATE_Z + 4):
        bb.fill(x2 - 1, y + 1, z, x2 + 1, y + 10, z, "minecraft:white_concrete")
        bb.set(x2, y + 11, z, "minecraft:light_blue_concrete")
    bb.fill(x2, y + 7, GATE_Z - 4, x2, y + 9, GATE_Z + 4, "minecraft:white_concrete")
    bb.fill(x2 + 1, y + 8, GATE_Z - 2, x2 + 1, y + 8, GATE_Z + 2, "minecraft:light_blue_concrete")
    bb.fill(x2 - 1, y + 1, GATE_Z - 3, x2 - 1, y + 4, GATE_Z - 3, "minecraft:iron_bars") if False else None
    # corner watchtowers
    for (tx, tz) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        bb.fill(tx - 2, y + 1, tz - 2, tx + 2, y + 12, tz + 2, "minecraft:white_concrete")
        bb.fill(tx - 1, y + 1, tz - 1, tx + 1, y + 12, tz + 1, AIR)
        bb.fill(tx, y + 1, tz - 1, tx, y + 12, tz - 1, "minecraft:ladder[facing=south]")
        bb.fill(tx - 3, y + 12, tz - 3, tx + 3, y + 12, tz + 3, "minecraft:light_gray_concrete")
        bb.set(tx, y + 12, tz - 1, "minecraft:ladder[facing=south]")
        for k in range(-3, 4):
            for (a, b) in ((tx + k, tz - 3), (tx + k, tz + 3), (tx - 3, tz + k), (tx + 3, tz + k)):
                bb.set(a, y + 13, b, "minecraft:white_concrete" if k % 2 == 0 else "minecraft:iron_bars")
        bb.set(tx, y + 13, tz, "minecraft:lantern[hanging=false]")
        for k in (-1, 1):
            bb.set(tx + k * 2, y + 7, tz, "minecraft:glass_pane"); bb.set(tx, y + 7, tz + k * 2, "minecraft:glass_pane")
        bb.fill(tx, y + 1, tz + (2 if tz == z1 else -2), tx, y + 2, tz + (2 if tz == z1 else -2), AIR)
    taken = []
    box, top = hq(bb, tracker, audit)
    taken.append(box)
    # barracks on the north side, armory and stores on the south
    barracks(bb, tracker, audit, 26, 30, 56, 36, ("bedroom", "bedroom", "bedroom", "dining"), 2, "stbr")
    barracks(bb, tracker, audit, 26, 72, 44, 78, ("storage", "workshop", "storage"), 2, "star")
    barracks(bb, tracker, audit, 60, 70, 72, 78, ("kitchen", "dining"), 1, "stmh")
    # the yard: Zoro's post, the flagpole, training posts, a well
    zx, zz = 64, 42
    bb.fill(zx, y + 1, zz, zx, y + 6, zz, "minecraft:stripped_oak_log[axis=y]")
    bb.fill(zx, y + 5, zz - 2, zx, y + 5, zz + 2, "minecraft:stripped_oak_log[axis=z]")
    bb.set(zx, y + 4, zz - 2, "minecraft:chain[axis=y]"); bb.set(zx, y + 4, zz + 2, "minecraft:chain[axis=y]")
    bb.set(zx + 1, y + 1, zz, "minecraft:green_carpet")           # the bandana in the dirt
    bb.set(zx + 2, y + 1, zz + 1, "minecraft:white_carpet")       # Rika's rice balls, wrapped
    fx, fz = 58, GATE_Z
    bb.fill(fx, y + 1, fz, fx, y + 22, fz, "minecraft:iron_bars")
    bb.set(fx, y + 23, fz, "minecraft:lightning_rod")
    wg_flag(bb, fx, y + 22, fz + 1, w=9, h=6, axis="z")
    for z in range(58, 68, 3):
        bb.set(66, y + 1, z, "minecraft:target"); bb.set(66, y + 2, z, "minecraft:hay_block[axis=y]")
    for x in range(56, 70, 3):
        bb.fill(x, y + 1, 64, x, y + 2, 64, "minecraft:oak_fence") if x % 2 else None
    for (x, z) in ((70, 34), (71, 34), (70, 35), (54, 76), (55, 76)):
        bb.set(x, y + 1, z, "minecraft:barrel[facing=up,open=false]")
    taken.append((BASE[0] - 5, BASE[1] - 5, BASE[2] + 5, BASE[3] + 5))
    return taken


# ------------------------------------------------------------------ the town
def row(bb, x1, x2, z0, d, rot, rng, tracker, audit, taken, k0, axis="x"):
    """Houses along a line: axis x walks x1..x2 at z0; axis z walks z x1..x2 at x0=z0."""
    a = x1
    k = k0
    while a < x2 - 6:
        w = int(rng.integers(8, 12))
        if a + w > x2:
            w = x2 - a
        if w < 7:
            break
        if axis == "x":
            box = (a - 1, z0 - 1, a + w, z0 + d)
        else:
            box = (z0 - 1, a - 1, z0 + d, a + w)
        xs = np.arange(box[0] + 1, box[2])[:, None]; zs = np.arange(box[1] + 1, box[3])[None, :]
        if any(box[0] <= r[2] and r[0] <= box[2] and box[1] <= r[3] and r[1] <= box[3] for r in taken) \
                or street_mask(xs, zs).any() or (~land(xs, zs)).any() or (np.abs(height(xs, zs) - TY) > 1).any():
            a += 3
            continue
        fl = int(rng.integers(2, 4))
        mod, _, au = house_module(seed_of("st", k), w if axis == "x" else d, d if axis == "x" else w, fl, ROOFS[k % len(ROOFS)],
                                  tracker, KINDS[k % len(KINDS)], pal=PALS[k % len(PALS)], timber=(k % 4 == 1), jetty=(k % 3 == 0))
        audit += au
        if axis == "x":
            place_house(bb, mod, w, d, a, TY, z0, rot)
        else:
            place_house(bb, mod, d, w, z0, TY, a, rot)
        taken.append(box)
        a += w + int(rng.integers(0, 3))
        k += 1
    return k


def rika_restaurant(bb, tracker, audit):
    """Rika's family restaurant: a two-storey yellow house with a striped awning and a terrace of tables."""
    x0, z0, w, d = 24, 104, 16, 12
    mod, _, au = house_module(seed_of("rika"), w, d, 2, "minecraft:red_nether_brick_stairs", tracker,
                              ["dining", "kitchen", "bedroom", "bedroom"], pal=PALS[2], timber=True, jetty=False)
    audit += au
    place_house(bb, mod, w, d, x0, TY, z0, 2)
    # terrace on the north (street) side with tables under an awning
    for x in range(x0, x0 + w):
        for z in range(z0 - 5, z0):
            bb.set(x, TY, z, "minecraft:spruce_planks")
        bb.set(x, TY + 4, z0 - 5, "minecraft:red_wool" if x % 2 else "minecraft:white_wool")
        bb.set(x, TY + 4, z0 - 4, "minecraft:red_carpet" if x % 2 else "minecraft:white_carpet")
    for x in (x0, x0 + w - 1):
        bb.fill(x, TY + 1, z0 - 5, x, TY + 3, z0 - 5, "minecraft:spruce_fence")
    for x in range(x0 + 2, x0 + w - 2, 4):
        bb.set(x, TY + 1, z0 - 3, "minecraft:spruce_fence"); bb.set(x, TY + 2, z0 - 3, "minecraft:white_carpet")
        bb.set(x - 1, TY + 1, z0 - 3, st("minecraft:spruce_stairs", "east")); bb.set(x + 1, TY + 1, z0 - 3, st("minecraft:spruce_stairs", "west"))
    bb.set(x0 + w // 2, TY + 5, z0 - 1, "minecraft:yellow_wall_banner[facing=north]") if False else None
    return (x0 - 1, z0 - 6, x0 + w, z0 + d)


def church(bb, x, z):
    w, d = 11, 17
    y = TY
    bb.fill(x, y, z, x + w - 1, y, z + d - 1, "minecraft:stone_bricks")
    bb.fill(x, y + 1, z, x + w - 1, y + 7, z + d - 1, "minecraft:white_terracotta")
    bb.fill(x + 1, y + 1, z + 1, x + w - 2, y + 7, z + d - 2, AIR)
    for zz in range(z + 2, z + d - 2, 3):
        bb.fill(x, y + 3, zz, x, y + 5, zz, "minecraft:light_blue_stained_glass_pane")
        bb.fill(x + w - 1, y + 3, zz, x + w - 1, y + 5, zz, "minecraft:light_blue_stained_glass_pane")
    bb.fill(x + w // 2, y + 1, z + d - 1, x + w // 2, y + 3, z + d - 1, AIR)
    P.gable_roof(bb, x - 1, z - 1, x + w, z + d, y + 8, "minecraft:deepslate_tile_stairs", gable_fill="minecraft:white_terracotta",
                 overhang=1)
    # bell tower over the front
    tx, tz = x + w // 2, z + d - 3
    bb.fill(tx - 2, y + 1, tz - 2, tx + 2, y + 18, tz + 2, "minecraft:white_terracotta")
    bb.fill(tx - 1, y + 1, tz - 1, tx + 1, y + 18, tz + 1, AIR)
    bb.fill(tx, y + 1, tz + 2, tx, y + 3, tz + 2, AIR)
    for (a, b) in ((tx - 2, tz), (tx + 2, tz), (tx, tz - 2), (tx, tz + 2)):
        bb.fill(a, y + 14, b, a, y + 16, b, AIR)
    bb.set(tx, y + 17, tz, "minecraft:bell[attachment=ceiling,facing=south]")
    bb.fill(tx - 2, y + 19, tz - 2, tx + 2, y + 19, tz + 2, "minecraft:deepslate_tiles")
    bb.fill(tx - 1, y + 20, tz - 1, tx + 1, y + 21, tz + 1, "minecraft:deepslate_tiles")
    bb.fill(tx, y + 22, tz, tx, y + 24, tz, "minecraft:deepslate_tiles")
    bb.set(tx, y + 25, tz, "minecraft:lightning_rod")
    for zz in range(z + 3, z + d - 4, 3):
        for xx in (x + 2, x + 3, x + w - 4, x + w - 3):
            bb.set(xx, y + 1, zz, st("minecraft:spruce_stairs", "south"))
    bb.fill(x + 4, y + 1, z + 1, x + w - 5, y + 1, z + 1, "minecraft:smooth_quartz")
    bb.set(x + w // 2, y + 2, z + 1, "minecraft:candle[candles=3,lit=true]")
    return (x - 2, z - 2, x + w + 1, z + d + 1)


def town(bb, rng, tracker, audit, taken):
    k = 0
    taken.append(rika_restaurant(bb, tracker, audit))
    taken.append(church(bb, 60, 130))
    k = row(bb, 82, 104, GATE_Z - 4 - 10, 10, 0, rng, tracker, audit, taken, k)          # main street, north side
    k = row(bb, 112, 132, GATE_Z - 4 - 10, 10, 0, rng, tracker, audit, taken, k)
    k = row(bb, 82, 104, GATE_Z + 4, 10, 2, rng, tracker, audit, taken, k)               # main street, south side
    k = row(bb, 112, 130, GATE_Z + 4, 10, 2, rng, tracker, audit, taken, k)
    k = row(bb, 20, GATE_Z - 16, 111, 10, 1, rng, tracker, audit, taken, k, axis="z")    # x=108 street, east side
    k = row(bb, 20, GATE_Z - 16, 95, 10, 3, rng, tracker, audit, taken, k, axis="z")
    k = row(bb, 66, 96, 95, 10, 3, rng, tracker, audit, taken, k, axis="z")
    k = row(bb, 66, 96, 111, 10, 1, rng, tracker, audit, taken, k, axis="z")
    k = row(bb, 54, 134, 98 - 3 - 10, 10, 0, rng, tracker, audit, taken, k)              # z=98 street
    k = row(bb, 54, 134, 101, 10, 2, rng, tracker, audit, taken, k)
    k = row(bb, 22, 46, 101 + 16, 8, 2, rng, tracker, audit, taken, k) if False else k
    k = row(bb, 54, 134, 126 - 3 - 10, 10, 0, rng, tracker, audit, taken, k)             # z=126 street
    k = row(bb, 22, 134, 129, 10, 2, rng, tracker, audit, taken, k)
    print("houses:", k)
    # lamps along the streets
    for x in range(BASE[2] + 22, QUAY_X - 4, 10):
        lamp_post(bb, x, TY + 1, GATE_Z - 3); lamp_post(bb, x, TY + 1, GATE_Z + 3)
    for x in range(26, QUAY_X - 4, 12):
        lamp_post(bb, x, TY + 1, 96)


def harbour(bb, rng):
    for z in range(20, 150):
        X, Z = np.array([[QUAY_X]]), np.array([[z]])
        if SHORE(X, Z)[0, 0] < 2:
            continue
        bb.fill(QUAY_X, -6, z, QUAY_X, TY, z, "minecraft:stone_bricks")
        bb.set(QUAY_X, TY, z, "minecraft:polished_andesite")
        if z % 8 == 0:
            bb.set(QUAY_X, TY + 1, z, "minecraft:stone_brick_wall")
    for pz in (36, 82, 132):
        for x in range(QUAY_X + 1, QUAY_X + 20):
            bb.fill(x, TY, pz - 1, x, TY, pz + 1, "minecraft:spruce_planks")
            if (x - QUAY_X) % 5 == 0:
                bb.fill(x, -9, pz - 2, x, TY, pz - 2, "minecraft:spruce_log[axis=y]")
                bb.fill(x, -9, pz + 2, x, TY, pz + 2, "minecraft:spruce_log[axis=y]")
                bb.set(x, TY + 1, pz + 2, "minecraft:lantern[hanging=false]")
    stamp_ship(bb, "marine_warship", QUAY_X + 14, 60, water_y=0, rot=1)
    for (x, z) in ((QUAY_X + 4, 112), (QUAY_X + 4, 120)):
        bb.fill(x - 3, 0, z - 1, x + 3, 0, z + 1, "minecraft:spruce_planks")
        bb.fill(x - 4, 1, z - 1, x + 4, 1, z + 1, "minecraft:spruce_slab[type=bottom]")
        bb.fill(x - 3, 1, z, x + 3, 1, z, AIR)
    for (x, z) in ((QUAY_X - 3, 40), (QUAY_X - 3, 41), (QUAY_X - 4, 40), (QUAY_X - 3, 88), (QUAY_X - 4, 88)):
        bb.set(x, TY + 1, z, "minecraft:barrel[facing=up,open=false]")


def scenery(bb, rng, taken):
    k = 0
    for _ in range(4000):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        X, Z = np.array([[x]]), np.array([[z]])
        if not land(X, Z)[0, 0] or SHORE(X, Z)[0, 0] < 6 or GRAD[x, z] >= 2 or street_mask(X, Z)[0, 0]:
            continue
        inside = min(rect_d(X, Z, TOWN)[0, 0], rect_d(X, Z, TOWN2)[0, 0]) == 0
        if inside and rng.random() < 0.85:
            continue
        if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken):
            continue
        P.tree(bb, x, hy(x, z) + 1, z, int(rng.integers(6, 10)), ("oak", "birch", "oak", "spruce")[k % 4], rng)
        taken.append((x - 3, z - 3, x + 3, z + 3))
        k += 1
        if k >= 60:
            break
    print("trees:", k)


def design():
    bb = BigBuild(seed=2520, y_min=-14, y_max=70)
    tracker = P.PropTracker(2520)
    audit = []
    rng = np.random.default_rng(2520)
    terrain(bb)
    taken = marine_base(bb, tracker, audit)
    town(bb, rng, tracker, audit, taken)
    harbour(bb, rng)
    taken.append((QUAY_X - 7, 0, N, N))
    scenery(bb, rng, taken)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 2590, density=0.25, kinds=NT.PLANTS_MEADOW, flowers=NT.FLOWERS,
              mask=lambda X, Z: land(X, Z) & ~street_mask(X, Z) & (rect_d(X, Z, (BASE[0] - 4, BASE[1] - 4, BASE[2] + 4, BASE[3] + 4)) > 0))
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
    b.npc(60, BY + 1, GATE_Z + 6, "koby", False)
    b.chest(28, BY + 1, 40, "marine", "east")
    b.chest(27, TY + 1, 108, "easy", "east")
    b.guards("marine_recruit", ((BASE[2] - 3, GATE_Z - 6), (BASE[2] - 3, GATE_Z + 6), (60, 50), (40, 74)), y=BY + 1)
    return b, 0
