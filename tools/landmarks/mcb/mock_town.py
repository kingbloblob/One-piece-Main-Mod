"""Mock Town v2, redesigned with the Minecraft Builder skill: the lawless pirate town on Jaya where dreamers get
laughed at.

A jungle island with the harbour on the west, crowded with pirate ships (Blackbeard's raft-ship among them, the
Going Merry at the far pier). Crooked, patched timber buildings of two to four storeys lean over muddy streets:
the Tavern, Bellamy's gang's hangout, with its brawl hall, bar and gallery; rowdy bars, the inn, the gunsmith,
the pawn shop; the town hall burnt black and roofless; the gallows on the square; wanted-poster boards, crates,
barrels and broken furniture everywhere. Behind the town the Jaya jungle climbs a hill with giant trees.
168 x 168. y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, set_if_air, house_module, place_house, lamp_post, glyph
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.shipstamp import stamp_ship

SID = "mock_town"
TITLE = "Mock Town (Jaya)"
CUTS = [4, 10, 16]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 168
_S1 = NT.outline(86, 84, 67, 3320, wobble=0.09)
_S2 = NT.outline(62, 116, 36, 3321, wobble=0.08)
SHORE = lambda X, Z: np.maximum(_S1(X, Z), _S2(X, Z))
TY = 2
QUAY_X = 34                         # quay edge; harbour west of it
TOWN = (QUAY_X + 4, 20, 124, 150)
SQUARE = (64, 74, 86, 96)           # the square with the gallows
TAVERN = (92, 70, 118, 92)

MUD = [("minecraft:mud", 0.18), ("minecraft:packed_mud", 0.22), ("minecraft:coarse_dirt", 0.22), ("minecraft:dirt", 0.12),
       ("minecraft:rooted_dirt", 0.1), ("minecraft:dirt_path", 0.16)]
SAND = [("minecraft:sand", 0.7), ("minecraft:sandstone", 0.15), ("minecraft:clay", 0.15)]
ROCK = [("minecraft:stone", 0.35), ("minecraft:andesite", 0.25), ("minecraft:mossy_cobblestone", 0.2), ("minecraft:tuff", 0.2)]
PALS = [
    dict(walls=["minecraft:spruce_planks", "minecraft:oak_planks", "minecraft:stripped_spruce_wood"], frame="minecraft:dark_oak_log",
         base=["minecraft:cobblestone", "minecraft:mossy_cobblestone", "minecraft:andesite"], floor="minecraft:spruce_planks",
         wood="spruce", chimney="minecraft:cobblestone"),
    dict(walls=["minecraft:dark_oak_planks", "minecraft:spruce_planks", "minecraft:mud_bricks"], frame="minecraft:spruce_log",
         base=["minecraft:cobblestone", "minecraft:tuff", "minecraft:mossy_cobblestone"], floor="minecraft:dark_oak_planks",
         wood="dark_oak", chimney="minecraft:bricks"),
    dict(walls=["minecraft:jungle_planks", "minecraft:oak_planks", "minecraft:stripped_jungle_wood"], frame="minecraft:jungle_log",
         base=["minecraft:mossy_cobblestone", "minecraft:cobblestone", "minecraft:andesite"], floor="minecraft:jungle_planks",
         wood="jungle", chimney="minecraft:cobblestone"),
    dict(walls=["minecraft:white_terracotta", "minecraft:oak_planks", "minecraft:light_gray_terracotta"], frame="minecraft:stripped_dark_oak_log",
         base=["minecraft:cobblestone", "minecraft:stone_bricks", "minecraft:mossy_cobblestone"], floor="minecraft:oak_planks",
         wood="oak", chimney="minecraft:bricks"),
]
ROOFS = ["minecraft:spruce_stairs", "minecraft:dark_oak_stairs", "minecraft:mud_brick_stairs", "minecraft:jungle_stairs",
         "minecraft:cobblestone_stairs", "minecraft:mangrove_stairs"]
KINDS = [["dining", "kitchen", "bedroom", "bedroom"], ["storage", "workshop", "bedroom"], ["living", "dining", "bedroom", "storage"],
         ["kitchen", "bedroom", "bedroom"], ["storage", "living", "bedroom"]]
FONT = {"T": ["#####", "..#..", "..#..", "..#..", "..#.."], "A": [".###.", "#...#", "#####", "#...#", "#...#"],
        "V": ["#...#", "#...#", "#...#", ".#.#.", "..#.."], "E": ["#####", "#....", "####.", "#....", "#####"],
        "R": ["####.", "#...#", "####.", "#..#.", "#...#"], "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#"]}


def rect_d(X, Z, r):
    dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0)
    dz = np.maximum(np.maximum(r[1] - Z, Z - r[3]), 0)
    return np.hypot(dx, dz)


def streets(X, Z):
    """Crooked muddy streets: a harbour front, three wobbling east-west lanes, two north-south ones."""
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    m = (X >= QUAY_X) & (X <= QUAY_X + 4) & (Z > 14) & (Z < 154)
    m = m | (X * 0 + Z * 0 > 0)
    for z0, s in ((44, 3331), (85, 3332), (124, 3333)):
        m |= (np.abs(Z - (z0 + 4 * np.sin(X * 0.07 + s))) <= 2) & (X > QUAY_X) & (X < 128)
    for x0, s in ((60, 3334), (90, 3335)):
        m |= (np.abs(X - (x0 + 3 * np.sin(Z * 0.08 + s))) <= 2) & (Z > 22) & (Z < 150)
    m |= rect_d(X, Z, SQUARE) <= 0
    return m


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = SHORE(X, Z)
    hill = TY + np.clip((X - 118) / 30.0, 0, 1) * 15 + NT.fbm(X, Z, 3322, 22) * 6 - 2
    h = hill * np.clip((d - 1.5) / 20.0, 0, 1)
    w = np.clip(rect_d(X, Z, TOWN) / 10.0, 0, 1)
    h = TY * (1 - w) + np.maximum(h, TY - 1) * w
    h = np.where(d < 10, np.minimum(h, TY * d / 10.0 + 0.4), h)
    h = np.where(X < QUAY_X, -4, h)
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
    return (SHORE(X, Z) > 1.5) & (np.asarray(X) >= QUAY_X)


def hy(x, z):
    return int(HMAP[min(max(x, 0), N - 1), min(max(z, 0), N - 1)])


def terrain(bb):
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SAND, 3341, mask=lambda X, Z: land(X, Z) & (SHORE(X, Z) < 7),
             under="minecraft:sandstone", core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, ROCK, 3342, mask=lambda X, Z: land(X, Z) & steep(X, Z) & (SHORE(X, Z) >= 7),
             under="minecraft:stone", core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, NT.JUNGLE if hasattr(NT, "JUNGLE") else NT.MEADOW, 3343,
             mask=lambda X, Z: land(X, Z) & ~steep(X, Z) & (SHORE(X, Z) >= 7), core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, MUD, 3344, mask=lambda X, Z: land(X, Z) & streets(X, Z), core="minecraft:stone")
    bed = lambda X, Z: np.where(np.asarray(X) < QUAY_X, np.minimum(-5 - np.clip((QUAY_X - np.asarray(X)) * 0.4, 0, 5),
                                                                    np.round(-2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10))),
                                np.round(-2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10)))
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy == bed(X, Z)), "minecraft:sand")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy < bed(X, Z)) & (yy >= bed(X, Z) - 2), "minecraft:stone")


# ------------------------------------------------------------------ the Tavern, the town hall, the gallows
def tavern(bb, tracker, audit):
    """Bellamy's hangout: a three-storey timber hall, the ground floor one big brawl hall with the bar, a gallery
    round it, rooms upstairs, TAVERN across the front and a skull flag on the roof."""
    x1, z1, x2, z2 = TAVERN
    y = TY
    top = y + 15
    bb.fill(x1, y - 2, z1, x2, y, z2, "minecraft:cobblestone")
    bb.fill(x1, y, z1, x2, y, z2, "minecraft:dark_oak_planks")
    bb.fill(x1, y + 1, z1, x2, top, z2, "minecraft:spruce_planks")
    bb.fill(x1 + 1, y + 1, z1 + 1, x2 - 1, top - 1, z2 - 1, AIR)
    for x in range(x1, x2 + 1, 4):
        for z in (z1, z2):
            bb.fill(x, y + 1, z, x, top, z, "minecraft:dark_oak_log[axis=y]")
    for z in range(z1, z2 + 1, 4):
        for x in (x1, x2):
            bb.fill(x, y + 1, z, x, top, z, "minecraft:dark_oak_log[axis=y]")
    for yy in (y + 5, y + 10, top):
        for (a, b, c, d) in ((x1, z1, x2, z1), (x1, z2, x2, z2)):
            bb.fill(a, yy, b, c, yy, d, "minecraft:dark_oak_log[axis=x]")
        for (a, b, c, d) in ((x1, z1, x1, z2), (x2, z1, x2, z2)):
            bb.fill(a, yy, b, c, yy, d, "minecraft:dark_oak_log[axis=z]")
    # windows
    for yy in (y + 2, y + 7, y + 12):
        for x in range(x1 + 2, x2 - 1, 4):
            for z in (z1, z2):
                bb.fill(x, yy, z, x + 1, yy + 1, z, "minecraft:glass_pane")
        for z in range(z1 + 2, z2 - 1, 4):
            bb.fill(x2, yy, z, x2, yy + 1, z + 1, "minecraft:glass_pane")
    # the swing doors on the west front, to the lane
    cz = (z1 + z2) // 2
    bb.fill(x1, y + 1, cz - 1, x1, y + 3, cz + 1, AIR)
    bb.set(x1, y + 1, cz - 1, "minecraft:spruce_fence_gate[facing=west,open=true]")
    bb.set(x1, y + 1, cz + 1, "minecraft:spruce_fence_gate[facing=west,open=true]")
    bb.fill(x1 - 3, y, z1, x1 - 1, y, z2, "minecraft:spruce_planks")
    for z in range(z1, z2 + 1, 4):
        bb.fill(x1 - 3, y + 1, z, x1 - 3, y + 4, z, "minecraft:spruce_fence")
    bb.fill(x1 - 3, y + 5, z1, x1 - 1, y + 5, z2, "minecraft:spruce_slab[type=bottom]")
    word = "TAVERN"
    rows = ["".join(FONT[ch][r] + "." for ch in word) for r in range(5)]
    glyph(bb, rows, x1 - 1, y + 11, cz - len(rows[0]) // 2, "minecraft:yellow_terracotta", axis="z")
    # the brawl hall: one tall floor (the first floor is only a gallery round it)
    bb.fill(x1 + 1, y + 5, z1 + 1, x2 - 1, y + 5, z2 - 1, "minecraft:spruce_planks")
    bb.fill(x1 + 5, y + 5, z1 + 5, x2 - 5, y + 5, z2 - 5, AIR)
    for x in range(x1 + 5, x2 - 4):
        bb.set(x, y + 6, z1 + 5, "minecraft:spruce_fence"); bb.set(x, y + 6, z2 - 5, "minecraft:spruce_fence")
    for z in range(z1 + 5, z2 - 4):
        bb.set(x1 + 5, y + 6, z, "minecraft:spruce_fence"); bb.set(x2 - 5, y + 6, z, "minecraft:spruce_fence")
    bb.set(x1 + 5, y + 6, cz, AIR)
    # bar along the east wall
    bb.fill(x2 - 4, y + 1, z1 + 3, x2 - 4, y + 1, z2 - 3, "minecraft:dark_oak_planks")
    bb.fill(x2 - 4, y + 2, z1 + 3, x2 - 4, y + 2, z2 - 3, "minecraft:dark_oak_slab[type=bottom]")
    for z in range(z1 + 2, z2 - 1):
        bb.set(x2 - 1, y + 1, z, "minecraft:barrel[facing=west,open=false]")
        bb.set(x2 - 1, y + 2, z, "minecraft:barrel[facing=west,open=false]" if z % 2 else "minecraft:brewing_stand")
        if z % 3 == 0 and z1 + 3 <= z <= z2 - 3:
            bb.set(x2 - 5, y + 1, z, st("minecraft:spruce_stairs", "east"))
    # tables, some knocked over
    rng = np.random.default_rng(3350)
    for tx in range(x1 + 4, x2 - 7, 5):
        for tz in range(z1 + 4, z2 - 3, 5):
            if rng.random() < 0.25:
                bb.set(tx, y + 1, tz, "minecraft:spruce_trapdoor[facing=east,half=bottom,open=true]")
                bb.set(tx + 1, y + 1, tz, "minecraft:spruce_slab[type=bottom]")
                continue
            bb.set(tx, y + 1, tz, "minecraft:spruce_fence"); bb.set(tx, y + 2, tz, "minecraft:spruce_pressure_plate")
            for (ox, oz, f) in ((-1, 0, "east"), (1, 0, "west"), (0, 1, "north")):
                if rng.random() < 0.8:
                    bb.set(tx + ox, y + 1, tz + oz, st("minecraft:spruce_stairs", f))
    for k in range(4):
        bb.set(x1 + 5 + k * 5, y + 9, cz, "minecraft:lantern[hanging=true]")
    # stairs to the gallery and the rooms floor
    for i in range(5):
        bb.set(x1 + 2, y + 1 + i, z2 - 2 - i, st("minecraft:spruce_stairs", "north"))
        bb.fill(x1 + 2, y + 2 + i, z2 - 2 - i, x1 + 2, y + 4 + i, z2 - 2 - i, AIR) if i < 4 else None
    bb.fill(x1 + 1, y + 5, z2 - 6, x1 + 3, y + 5, z2 - 2, AIR)
    bb.fill(x1 + 1, y + 10, z1 + 1, x2 - 1, y + 10, z2 - 1, "minecraft:spruce_planks")
    rooms = []
    for (a, b, c, d) in ((x1 + 1, z1 + 1, x1 + 8, z1 + 9), (x1 + 9, z1 + 1, x1 + 16, z1 + 9), (x1 + 17, z1 + 1, x2 - 1, z1 + 9),
                         (x1 + 1, z1 + 13, x1 + 8, z2 - 1), (x1 + 9, z1 + 13, x1 + 16, z2 - 1), (x1 + 17, z1 + 13, x2 - 1, z2 - 1)):
        bb.fill(a - 1, y + 11, b - 1, c + 1, top - 1, d + 1, "minecraft:spruce_planks")
        bb.fill(a, y + 11, b, c, top - 1, d, AIR)
        rooms.append((a, b, c, d))
    bb.fill(x1 + 1, y + 11, z1 + 10, x2 - 1, top - 1, z1 + 12, AIR)
    doors = []
    for (a, b, c, d) in rooms:
        dz = d + 1 if b < z1 + 10 else b - 1
        bb.fill((a + c) // 2, y + 11, dz, (a + c) // 2, y + 12, dz, AIR)
        doors.append(((a + c) // 2, dz))
    for i, r in enumerate(rooms):
        P.furnish_room(bb, r, y + 11, ("bedroom", "bedroom", "storage", "living", "bedroom", "dining")[i], height=top - y - 11,
                       seed=seed_of("tav", i), doors=doors, wood="spruce", tracker=tracker)
    for i in range(5):
        bb.set(x2 - 2, y + 6 + i, z1 + 2 + i, st("minecraft:spruce_stairs", "south"))
        bb.fill(x2 - 2, y + 7 + i, z1 + 2 + i, x2 - 2, y + 9 + i, z1 + 2 + i, AIR)
    bb.fill(x2 - 2, y + 10, z1 + 3, x2 - 2, y + 10, z1 + 7, AIR)
    # roof and the skull flag
    P.gable_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, top + 1, "minecraft:dark_oak_stairs", ridge_axis="x",
                 gable_fill="minecraft:spruce_planks", overhang=1)
    fx, fz = x2 - 4, cz
    bb.fill(fx, top + 10, fz, fx, top + 20, fz, "minecraft:dark_oak_fence")
    flag = ["#########", "###...###", "##.#.#.##", "###...###", "####.####", "#.#####.#", "#########"]
    for r, row in enumerate(flag):
        for c, ch in enumerate(row):
            bb.set(fx, top + 19 - r, fz + 1 + c, "minecraft:white_wool" if ch == "." else "minecraft:black_wool")
    return (x1 - 4, z1 - 2, x2 + 2, z2 + 2)


def burnt_town_hall(bb, x1, z1, x2, z2):
    """The town hall burnt out: black stone walls standing to uneven heights, no roof, charred beams, ash."""
    y = TY
    rng = np.random.default_rng(3360)
    bb.fill(x1, y - 2, z1, x2, y, z2, "minecraft:cobbled_deepslate")
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if x in (x1, x2) or z in (z1, z2):
                h = int(4 + 8 * NT.noise(np.array([[x]]), np.array([[z]]), 3361, 4)[0, 0])
                for yy in range(y + 1, y + 1 + h):
                    bb.set(x, yy, z, ("minecraft:blackstone", "minecraft:polished_blackstone_bricks", "minecraft:cracked_polished_blackstone_bricks",
                                      "minecraft:coal_block", "minecraft:basalt[axis=y]")[int(rng.integers(5))])
            elif rng.random() < 0.3:
                bb.set(x, y + 1, z, ("minecraft:black_carpet", "minecraft:gray_carpet", "minecraft:coal_block")[int(rng.integers(3))])
    for z in range(z1 + 3, z2 - 2, 4):
        bb.fill(x1 + 1, y + 1 + (z % 3), z, x2 - 1, y + 1 + (z % 3), z, "minecraft:stripped_dark_oak_log[axis=x]") if z % 8 == 3 else None
    for x in range(x1 + 2, x2 - 1, 3):
        for z in (z1, z2):
            bb.fill(x, y + 3, z, x, y + 4, z, AIR)
    bb.fill((x1 + x2) // 2 - 1, y + 1, z2, (x1 + x2) // 2 + 1, y + 4, z2, AIR)
    for _ in range(6):
        bb.set(int(rng.integers(x1 + 1, x2)), y + 1, int(rng.integers(z1 + 1, z2)), "minecraft:campfire[lit=false,signal_fire=false]")
    return (x1 - 2, z1 - 2, x2 + 2, z2 + 2)


def square(bb):
    """The square: the gallows, a wanted-poster board, a well, broken crates."""
    x1, z1, x2, z2 = SQUARE
    cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
    y = TY
    bb.fill(cx - 3, y + 1, cz - 2, cx + 3, y + 3, cz + 2, "minecraft:spruce_planks")
    bb.fill(cx - 2, y + 1, cz - 1, cx + 2, y + 2, cz + 1, AIR)
    for (a, b) in ((cx - 3, cz - 2), (cx + 3, cz - 2), (cx - 3, cz + 2), (cx + 3, cz + 2)):
        bb.fill(a, y + 1, b, a, y + 3, b, "minecraft:dark_oak_log[axis=y]")
    for i in range(3):
        bb.set(cx - 3 + i * 0, y + 1 + i, cz + 3 + i, st("minecraft:spruce_stairs", "north")) if False else None
    for i in range(3):
        bb.set(cx, y + 1 + i, cz + 5 - i, st("minecraft:spruce_stairs", "north"))
    bb.fill(cx - 2, y + 4, cz, cx - 2, y + 9, cz, "minecraft:dark_oak_log[axis=y]")
    bb.fill(cx + 2, y + 4, cz, cx + 2, y + 9, cz, "minecraft:dark_oak_log[axis=y]")
    bb.fill(cx - 2, y + 10, cz, cx + 2, y + 10, cz, "minecraft:dark_oak_log[axis=x]")
    for x in (cx - 1, cx + 1):
        bb.fill(x, y + 7, cz, x, y + 9, cz, "minecraft:chain[axis=y]")
    # poster board
    bb.fill(x1 + 2, y + 1, z1 + 2, x1 + 2, y + 3, z1 + 2, "minecraft:spruce_fence")
    bb.fill(x1 + 6, y + 1, z1 + 2, x1 + 6, y + 3, z1 + 2, "minecraft:spruce_fence")
    bb.fill(x1 + 2, y + 4, z1 + 2, x1 + 6, y + 5, z1 + 2, "minecraft:spruce_planks")
    for x in range(x1 + 2, x1 + 7):
        bb.set(x, y + 4, z1 + 3, "minecraft:white_carpet") if False else None
    bb.fill(x1 + 2, y + 6, z1 + 2, x1 + 6, y + 6, z1 + 2, "minecraft:spruce_slab[type=bottom]")
    # well
    wx, wz = x2 - 3, z2 - 3
    bb.fill(wx - 1, y + 1, wz - 1, wx + 1, y + 1, wz + 1, "minecraft:mossy_cobblestone")
    bb.set(wx, y + 1, wz, "minecraft:water")
    for (a, b) in ((wx - 1, wz - 1), (wx + 1, wz + 1)):
        bb.fill(a, y + 2, b, a, y + 3, b, "minecraft:spruce_fence")
    bb.fill(wx - 1, y + 4, wz - 1, wx + 1, y + 4, wz + 1, "minecraft:spruce_slab[type=bottom]")
    for (a, b) in ((x1 + 1, z2 - 1), (x1 + 2, z2 - 1), (x1 + 1, z2 - 2)):
        bb.set(a, y + 1, b, "minecraft:barrel[facing=up,open=false]")


# ------------------------------------------------------------------ the town, the harbour, the jungle
def town(bb, tracker, audit, rng, taken):
    k = 0
    for _ in range(7000):
        w, d = int(rng.integers(8, 12)), int(rng.integers(7, 10))
        x0, z0 = int(rng.integers(TOWN[0], TOWN[2] - w)), int(rng.integers(TOWN[1], TOWN[3] - d))
        xs = np.arange(x0 - 1, x0 + w + 1)[:, None]; zs = np.arange(z0 - 1, z0 + d + 1)[None, :]
        if streets(xs, zs).any() or (~land(xs, zs)).any() or (SHORE(xs, zs) < 4).any():
            continue
        hs = HMAP[np.clip(xs, 0, N - 1), np.clip(zs, 0, N - 1)]
        if hs.max() - hs.min() > 2:
            continue
        box = (x0 - 1, z0 - 1, x0 + w, z0 + d)
        if any(box[0] <= r[2] and r[0] <= box[2] and box[1] <= r[3] and r[1] <= box[3] for r in taken):
            continue
        # face the nearest street edge
        cand = {}
        for rot, (px, pz) in {0: (x0 + w // 2, z0 + d + 1), 2: (x0 + w // 2, z0 - 2), 1: (x0 - 2, z0 + d // 2), 3: (x0 + w + 1, z0 + d // 2)}.items():
            ok = False
            for s in range(0, 3):
                qx = px + (0 if rot in (0, 2) else (-s if rot == 1 else s))
                qz = pz + (s if rot == 0 else -s if rot == 2 else 0)
                if streets(np.array([[qx]]), np.array([[qz]]))[0, 0]:
                    ok = True
                    cand[rot] = s
                    break
        if not cand:
            continue
        rot = min(cand, key=cand.get)
        mw, md = (w, d) if rot % 2 == 0 else (d, w)
        y = int(hs.max())
        fl = int(rng.integers(2, 5))
        m, top, au = house_module(seed_of("mk", x0, z0), mw, md, fl, ROOFS[k % len(ROOFS)], tracker, KINDS[k % len(KINDS)],
                                  pal=PALS[k % len(PALS)], timber=(k % 2 == 0), jetty=(k % 3 != 2), chimney=(k % 2 == 1))
        audit += au
        bb.fill(x0, y - 3, z0, x0 + w - 1, y, z0 + d - 1, "minecraft:cobblestone")
        place_house(bb, m, mw, md, x0, y, z0, rot)
        # patches: odd planks hammered over the walls
        for _p in range(int(rng.integers(3, 8))):
            px, pz = int(rng.integers(x0, x0 + w)), int(rng.integers(z0, z0 + d))
            py = y + 1 + int(rng.integers(0, fl * 5))
            if px in (x0, x0 + w - 1) or pz in (z0, z0 + d - 1):
                bb.set(px, py, pz, ("minecraft:oak_planks", "minecraft:birch_planks", "minecraft:mangrove_planks", "minecraft:crimson_planks")[_p % 4])
        taken.append(box)
        k += 1
        if k >= 60:
            break
    print("houses:", k)
    for x in range(QUAY_X + 6, 124, 11):
        lamp_post(bb, x, TY + 1, 44 + int(4 * math.sin(x * 0.07 + 3331)) + 3) if not streets(np.array([[x]]), np.array([[44 + int(4 * math.sin(x * 0.07 + 3331)) + 3]]))[0, 0] else None


def harbour(bb, rng):
    for z in range(0, N):
        if SHORE(np.array([[QUAY_X + 2]]), np.array([[z]]))[0, 0] < 1.5:
            continue
        bb.fill(QUAY_X, -6, z, QUAY_X, TY, z, "minecraft:cobblestone")
        bb.set(QUAY_X, TY, z, "minecraft:spruce_planks")
        if z % 6 == 0:
            bb.set(QUAY_X, TY + 1, z, "minecraft:spruce_fence")
    piers = (26, 90, 150)
    for pz in piers:
        for x in range(QUAY_X - 22, QUAY_X):
            bb.fill(x, TY - 1, pz - 1, x, TY - 1, pz + 1, "minecraft:spruce_planks")
            if (QUAY_X - x) % 5 == 0:
                for p in (pz - 2, pz + 2):
                    bb.fill(x, -9, p, x, TY - 1, p, "minecraft:spruce_log[axis=y]")
                bb.set(x, TY, pz + 2, "minecraft:lantern[hanging=false]")
    stamp_ship(bb, "bezan_black", QUAY_X - 14, 56, water_y=0, rot=3)
    stamp_ship(bb, "going_merry", QUAY_X - 13, 120, water_y=0, rot=3)
    for (x, z) in ((QUAY_X + 2, 30), (QUAY_X + 2, 31), (QUAY_X + 3, 30), (QUAY_X + 2, 90), (QUAY_X + 2, 91), (QUAY_X + 2, 140)):
        bb.set(x, TY + 1, z, "minecraft:barrel[facing=up,open=false]")


def jungle(bb, rng, taken):
    k = 0
    for _ in range(6000):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        X, Z = np.array([[x]]), np.array([[z]])
        if not land(X, Z)[0, 0] or SHORE(X, Z)[0, 0] < 5 or GRAD[x, z] >= 3 or streets(X, Z)[0, 0]:
            continue
        if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken):
            continue
        inside = rect_d(X, Z, TOWN)[0, 0] == 0
        if inside and rng.random() < 0.9:
            continue
        if not inside and x > 126 and k % 7 == 0:
            NT.giant_tree(bb, x, hy(x, z) + 1, z, int(rng.integers(22, 32)), rng, kind="jungle")
            taken.append((x - 7, z - 7, x + 7, z + 7))
        else:
            P.tree(bb, x, hy(x, z) + 1, z, int(rng.integers(7, 12)), ("jungle", "jungle", "oak", "acacia")[k % 4], rng)
            taken.append((x - 3, z - 3, x + 3, z + 3))
        k += 1
        if k >= 120:
            break
    print("trees:", k)


def design():
    bb = BigBuild(seed=3320, y_min=-14, y_max=78)
    tracker = P.PropTracker(3320)
    audit = []
    rng = np.random.default_rng(3320)
    terrain(bb)
    taken = [tavern(bb, tracker, audit), burnt_town_hall(bb, 66, 104, 84, 118), (SQUARE[0] - 1, SQUARE[1] - 1, SQUARE[2] + 1, SQUARE[3] + 1),
             (0, 0, QUAY_X + 4, N)]
    square(bb)
    harbour(bb, rng)
    town(bb, tracker, audit, rng, taken)
    jungle(bb, rng, taken)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 3390, density=0.3, kinds=NT.PLANTS_JUNGLE, flowers=NT.FLOWERS,
              mask=lambda X, Z: land(X, Z) & ~streets(X, Z) & (rect_d(X, Z, TOWN) > 1))
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
    x1, z1, x2, z2 = TAVERN
    b.chest(x2 - 2, TY + 1, z1 + 2, "pirate", "west")
    b.guards("pirate", ((x1 + 8, (z1 + z2) // 2), (x1 + 14, z1 + 6), (70, 40), (60, 120)), y=TY + 1)
    b.guards("pirate_gunner", ((QUAY_X + 3, 50), (QUAY_X + 3, 100), (86, 86)), y=TY + 1)
    return b, 0
