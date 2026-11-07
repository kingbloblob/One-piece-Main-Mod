"""Rain Dinners v2 in Rainbase, redesigned with the Minecraft Builder skill: Crocodile's casino.

A golden sandstone pyramid (the show's design follows the Luxor in Las Vegas) on an island in the oasis lake of
Rainbase, the giant Bananawani statue sprawled over its top with the banana crest on its head and its jaws open
over the entrance. A causeway crosses the lake to the portico under the RAIN DINNERS sign. Inside, storey by storey:
the casino floor (card and roulette tables, slot machines, the bar, the stage), the VIP floor with the Baroque Works
meeting room, Crocodile's office, the vault under the peak; and below the lake the seastone cage room with its glass
wall where the Bananawani swim. Round the lake, Rainbase: flat-roofed desert houses with awnings, palms, a market,
dunes rolling away at the edges. 176 x 176, desert ground y 0. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, furnish, set_if_air, house_module, place_house, lamp_post, wing_floor, \
    palm, glyph
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "rain_dinners"
TITLE = "Rain Dinners (Rainbase)"
CUTS = [3, 14, 24, -6]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 176
CX, CZ = 88, 76
P0 = 34                                     # half width of the pyramid at its foot
PTOP = 36                                   # the flat top the crocodile lies on
ISLE = 40                                   # the casino island (rounded square radius)
LAKE = 54                                   # outer radius of the lake ring
SAND = "onepiece:alabasta_sandstone_bricks"
SAND_ST = "onepiece:alabasta_sandstone_brick_stairs"
CUT = "minecraft:cut_sandstone"
SMOOTH = "minecraft:smooth_sandstone"
GOLD = "minecraft:gold_block"
CROC = "minecraft:green_concrete"
CROC2 = "minecraft:lime_terracotta"
CROC3 = "minecraft:green_terracotta"
SEA = "onepiece:seastone_bricks"
DUNE = [("minecraft:sand", 0.6), ("minecraft:sandstone", 0.12), ("minecraft:smooth_sandstone", 0.08), ("minecraft:red_sand", 0.1),
        ("minecraft:coarse_dirt", 0.04), ("minecraft:terracotta", 0.06)]
PAVE = [(SMOOTH, 0.35), (CUT, 0.25), ("minecraft:sandstone", 0.2), (SAND, 0.2)]
TOWN = dict(walls=[SMOOTH, "minecraft:sandstone", CUT], frame=CUT, base=["minecraft:sandstone", CUT, SMOOTH],
            floor="minecraft:birch_planks", wood="jungle", chimney=SAND, parapet=SMOOTH)
FONT = {"R": ["####.", "#...#", "####.", "#..#.", "#...#"], "A": [".###.", "#...#", "#####", "#...#", "#...#"],
        "I": ["###", ".#.", ".#.", ".#.", "###"], "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#"],
        "D": ["####.", "#...#", "#...#", "#...#", "####."], "E": ["####", "#...", "###.", "#...", "####"],
        "S": [".####", "#....", ".###.", "....#", "####."], " ": ["..", "..", "..", "..", ".."]}


def sq(X, Z, cx=CX, cz=CZ, p=8):
    return (np.abs(np.asarray(X) - cx) ** p + np.abs(np.asarray(Z) - cz) ** p) ** (1.0 / p)


def H(y):
    """Half width of the pyramid at height y (3 up for every 2 in, about the Luxor's slope)."""
    return P0 - (max(y, 1) - 1) * 2 // 3


def lake(X, Z):
    s = sq(X, Z)
    return (s > ISLE) & (s <= LAKE + 2 * NT.noise(X, Z, 2821, 8))


def causeway(X, Z):
    return (np.abs(np.asarray(X) - CX) <= 3) & (np.asarray(Z) > CZ + P0) & (np.asarray(Z) <= CZ + LAKE + 4)


def town_zone(X, Z):
    s = sq(X, Z, p=4)
    return (s > LAKE + 3) & (s < LAKE + 34)


def streets(X, Z):
    s = sq(X, Z, p=4)
    m = (np.abs(s - (LAKE + 5)) <= 2)
    m |= causeway(X, Z) | ((np.abs(np.asarray(X) - CX) <= 3) & (np.asarray(Z) > CZ))
    m |= (np.abs(np.asarray(Z) - CZ) <= 2) & (s > LAKE)
    return m


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    s = sq(X, Z, p=4)
    dunes = np.clip(NT.fbm(X, Z, 2822, 20) - 0.3, 0, 1) * 16
    w = np.clip((s - (LAKE + 30)) / 10.0, 0, 1)
    edge = np.clip(np.minimum(np.minimum(X, N - 1 - X), np.minimum(Z, N - 1 - Z)) / 14.0, 0, 1)    # dunes sink to 0 at the site edge
    h = dunes * w * edge
    return np.round(h)


def build_maps():
    X = np.arange(N)[:, None]
    Z = np.arange(N)[None, :]
    return _height(X, Z).astype(int)


HMAP = build_maps()


def height(X, Z):
    return HMAP[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def hy(x, z):
    return int(HMAP[min(max(x, 0), N - 1), min(max(z, 0), N - 1)])


def terrain(bb):
    NT.cover(bb, 0, 0, N - 1, N - 1, height, DUNE, 2831, mask=lambda X, Z: ~lake(X, Z), under="minecraft:sandstone",
             core="minecraft:sandstone")
    NT.cover(bb, 0, 0, N - 1, N - 1, lambda X, Z: X * 0, PAVE, 2832, mask=lambda X, Z: streets(X, Z) & ~lake(X, Z),
             under="minecraft:sandstone", core="minecraft:sandstone")
    NT.cover(bb, 0, 0, N - 1, N - 1, lambda X, Z: X * 0, [("minecraft:grass_block", 0.6), ("minecraft:moss_block", 0.15),
                                                          ("minecraft:sand", 0.25)], 2833,
             mask=lambda X, Z: (sq(X, Z) > LAKE - 1) & (sq(X, Z) <= LAKE + 3) & ~lake(X, Z) & ~streets(X, Z))
    # the lake: deep, with a sandy shelf and reeds
    bed = lambda X, Z: np.where(sq(X, Z) > LAKE - 3, -2, -9)
    bb.fill_where(0, -10, 0, N - 1, 0, N - 1, lambda X, yy, Z: lake(X, Z) & (yy > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: lake(X, Z) & (yy <= bed(X, Z)) & (yy >= bed(X, Z) - 2), "minecraft:sand")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: lake(X, Z) & (yy < bed(X, Z) - 2), "minecraft:sandstone")
    # island rim: a sandstone quay round the casino island
    bb.fill_where(0, -9, 0, N - 1, 0, N - 1, lambda X, yy, Z: (np.abs(sq(X, Z) - ISLE) <= 0.8), SAND)
    bb.fill_where(0, 1, 0, N - 1, 1, N - 1, lambda X, yy, Z: (np.abs(sq(X, Z) - ISLE) <= 0.6) & ((np.asarray(X) + np.asarray(Z)) % 3 == 0),
                  "onepiece:alabasta_sandstone_brick_wall")
    NT.cover(bb, CX - ISLE, CZ - ISLE, CX + ISLE, CZ + ISLE, lambda X, Z: X * 0, PAVE, 2834, mask=lambda X, Z: sq(X, Z) < ISLE - 0.5)


def pyramid(bb, tracker, audit):
    """The pyramid shell: two-thick stepped sandstone walls with gold seams at every course of floors, window slits,
    the flat top; floors inside with rooms; the portico on the south."""
    for y in range(0, PTOP + 1):
        h = H(y)
        bb.fill(CX - h, y, CZ - h, CX + h, y, CZ + h, SMOOTH if y % 2 else CUT)
        if y > 0 and y < PTOP:
            bb.fill(CX - h + 2, y, CZ - h + 2, CX + h - 2, y, CZ + h - 2, AIR)
        # stepped edge: a stair lip where the width changes
        if y > 0 and H(y + 1) < h:
            for k in range(-h, h + 1):
                for (x, z, f) in ((CX + k, CZ - h, "north"), (CX + k, CZ + h, "south"), (CX - h, CZ + k, "west"), (CX + h, CZ + k, "east")):
                    bb.set(x, y + 1, z, st(SAND_ST, {"north": "south", "south": "north", "west": "east", "east": "west"}[f]))
    # gold trim on the four ridges and at three courses
    for y in range(1, PTOP + 1):
        h = H(y)
        for (x, z) in ((CX - h, CZ - h), (CX + h, CZ - h), (CX - h, CZ + h), (CX + h, CZ + h)):
            bb.set(x, y, z, GOLD)
    FLOORS = (0, 11, 21, 29)
    for fy in FLOORS[1:]:
        h = H(fy)
        bb.fill(CX - h + 2, fy, CZ - h + 2, CX + h - 2, fy, CZ + h - 2, "minecraft:dark_oak_planks")
        for k in range(-h, h + 1):
            for (x, z) in ((CX + k, CZ - h), (CX + k, CZ + h), (CX - h, CZ + k), (CX + h, CZ + k)):
                bb.set(x, fy, z, "minecraft:yellow_terracotta" if k % 3 else GOLD)
    # window slits (orange glass) on every face between the floors
    for (fy, top) in ((0, 11), (11, 21), (21, 29)):
        for y in range(fy + 3, top - 2):
            h = H(y)
            for k in range(-h + 3, h - 2, 4):
                for (x, z) in ((CX + k, CZ - h), (CX + k, CZ + h), (CX - h, CZ + k), (CX + h, CZ + k)):
                    if bb.names[bb.get_region(x, y, z, x, y, z)[0, 0, 0]] not in ("minecraft:air", "", None):
                        bb.set(x, y, z, "minecraft:orange_stained_glass")
    bb.fill(CX - H(PTOP), PTOP, CZ - H(PTOP), CX + H(PTOP), PTOP, CZ + H(PTOP), SAND)
    # ------------------------------------------------------------ the casino floor (0..10)
    h = H(9) - 2
    x1, z1, x2, z2 = CX - h, CZ - h, CX + h, CZ + h
    bb.fill(CX - P0 + 2, 0, CZ - P0 + 2, CX + P0 - 2, 0, CZ + P0 - 2, "minecraft:polished_blackstone")
    bb.fill_where(CX - P0 + 3, 0, CZ - P0 + 3, CX + P0 - 3, 0, CZ + P0 - 3,
                  lambda X, Y, Z: ((X + Z) % 6 == 0) | ((X - Z) % 6 == 0), "minecraft:red_terracotta")
    for tz in range(z1 + 6, z2 - 6, 7):
        for tx in range(x1 + 6, x2 - 6, 8):
            if abs(tx - CX) < 5 and tz > CZ:
                continue
            k = (tx + tz) % 3
            if k == 0:                                   # card table
                bb.fill(tx - 1, 1, tz, tx + 1, 1, tz, "onepiece:dark_oak_table")
                bb.fill(tx - 1, 2, tz, tx + 1, 2, tz, "minecraft:green_carpet")
                for x in (tx - 1, tx, tx + 1):
                    bb.set(x, 1, tz - 1, "onepiece:bar_stool"); bb.set(x, 1, tz + 1, "onepiece:bar_stool")
            elif k == 1:                                 # roulette wheel
                bb.set(tx, 1, tz, "minecraft:dark_oak_planks"); bb.set(tx, 2, tz, "minecraft:red_carpet")
                for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    bb.set(tx + dx, 1, tz + dz, "minecraft:green_terracotta"); bb.set(tx + dx, 2, tz + dz, "minecraft:black_carpet")
                for (dx, dz) in ((2, 0), (-2, 0), (0, 2)):
                    bb.set(tx + dx, 1, tz + dz, "onepiece:bar_stool")
            else:                                        # a row of slot machines
                for x in range(tx - 2, tx + 3):
                    bb.set(x, 1, tz, "minecraft:dispenser[facing=south,triggered=false]")
                    bb.set(x, 2, tz, "minecraft:yellow_stained_glass")
                    bb.set(x, 1, tz + 1, "onepiece:bar_stool")
    bb.fill(x1 + 4, 1, z1 + 3, x2 - 4, 1, z1 + 3, "onepiece:tavern_bar[facing=south]")
    for x in range(x1 + 4, x2 - 3):
        bb.set(x, 1, z1 + 1, "onepiece:keg[facing=south]" if x % 2 else "minecraft:barrel[facing=south,open=false]")
        if x % 2 == 0:
            bb.set(x, 1, z1 + 4, "onepiece:bar_stool")
    for x in range(x1 + 4, x2 - 3, 6):
        for z in range(z1 + 6, z2 - 3, 8):
            bb.fill(x, 6, z, x, 9, z, "minecraft:chain[axis=y]")
            bb.set(x, 5, z, "minecraft:lantern[hanging=true]")
    for x in range(x1 + 1, x2, 4):                       # pillars
        for z in (z1 + 1, z2 - 1):
            bb.fill(x, 1, z, x, 10, z, "onepiece:alubarna_pillar[axis=y]")
    # the big doors in the south face and the portico
    bb.fill(CX - 3, 1, CZ + P0 - 2, CX + 3, 7, CZ + P0 + 1, AIR)
    for x in (CX - 6, CX - 4, CX + 4, CX + 6):
        bb.fill(x, 1, CZ + P0 + 2, x, 10, CZ + P0 + 2, "onepiece:alubarna_pillar[axis=y]")
        bb.set(x, 11, CZ + P0 + 2, GOLD)
    bb.fill(CX - 7, 11, CZ + P0 - 1, CX + 7, 11, CZ + P0 + 3, SAND)
    bb.fill(CX - 7, 12, CZ + P0 + 3, CX + 7, 12, CZ + P0 + 3, "onepiece:alabasta_sandstone_brick_wall")
    for x in range(CX - 2, CX + 3):
        bb.set(x, 8, CZ + P0 + 2, "minecraft:red_wool")
    word = "RAIN DINNERS"
    rows = ["".join(FONT[ch][r] + "." for ch in word) for r in range(5)]
    glyph(bb, rows, CX - len(rows[0]) // 2, 18, CZ + H(14) + 1, GOLD)
    # VIP stair: a ladder well in the north-west corner up through every floor
    lx, lz = CX - H(PTOP) + 2, CZ - H(PTOP) + 2
    bb.fill(lx, 1, lz, lx, 29, lz, "minecraft:ladder[facing=south]")
    for fy in FLOORS[1:]:
        bb.set(lx, fy, lz, "minecraft:ladder[facing=south]")
    # ------------------------------------------------------------ the VIP floor, the office, the vault
    for (fy, top, kinds, seed) in ((11, 21, ["living", "library", "dining", "living", "storage"], 2841),
                                   (21, 29, ["library", "living", "bedroom"], 2842)):
        h = H(top - 1) - 2
        wing_floor(bb, CX - h, CZ - h, CX + h, CZ + h, fy + 1, top - fy - 2, SAND, seed, tracker, kinds, corridor="x", cw=3,
                   carpet=(None, "minecraft:red_carpet"), keep=[(lx - 1, lz - 1, lx + 2, lz + 2)], wood="dark_oak", audit=audit)
    # the Baroque Works meeting table (round, numbered seats) in the middle of the VIP floor
    bb.fill(CX - 6, 12, CZ - 4, CX + 6, 16, CZ + 4, AIR)
    bb.fill_where(CX - 4, 12, CZ - 3, CX + 4, 12, CZ + 3, lambda X, Y, Z: ((X - CX) / 4.2) ** 2 + ((Z - CZ) / 3.0) ** 2 <= 1,
                  "onepiece:dark_oak_table")
    for k in range(10):
        a = k * math.pi / 5
        bb.set(round(CX + 5.5 * math.cos(a)), 12, round(CZ + 4 * math.sin(a)), "onepiece:bar_stool")
    bb.set(CX, 15, CZ, "minecraft:lantern[hanging=true]")
    # the vault under the peak
    h = H(35) - 1
    bb.fill(CX - h, 30, CZ - h, CX + h, 35, CZ + h, AIR)
    for x in range(CX - h, CX + h + 1):
        for z in (CZ - h, CZ + h):
            bb.set(x, 30, z, GOLD if (x + z) % 2 else "minecraft:gold_ore") if False else bb.set(x, 30, z, "minecraft:raw_gold_block")
    bb.fill(CX - 2, 30, CZ - 2, CX + 2, 30, CZ + 2, GOLD)
    return (CX - P0 - 2, CZ - P0 - 2, CX + P0 + 2, CZ + P0 + 6)


def cage_room(bb):
    """Under the casino: the seastone cage room. A hall of seastone bricks with iron-bar cages, a glass wall on the
    south looking into the lake (the Bananawani pool), a trapdoor ladder down from the casino floor."""
    y0, y1 = -8, -1
    x1, x2, z1, z2 = CX - 16, CX + 16, CZ + 14, CZ + 30
    bb.fill(x1 - 1, y0 - 1, z1 - 1, x2 + 1, y1, z2 + 1, SEA)
    bb.fill(x1, y0, z1, x2, y1, z2, AIR)
    bb.fill(x1, y0 - 1, z1, x2, y0 - 1, z2, "minecraft:polished_blackstone_bricks")
    for x in range(x1 + 2, x2 - 1, 6):
        bb.fill(x, y0, z1 + 2, x + 3, y0 + 4, z1 + 2, "minecraft:iron_bars")
        bb.fill(x, y0, z1 + 2, x, y0 + 4, z1 + 6, "minecraft:iron_bars")
        bb.fill(x + 3, y0, z1 + 2, x + 3, y0 + 4, z1 + 6, "minecraft:iron_bars")
        bb.fill(x, y0 + 4, z1 + 2, x + 3, y0 + 4, z1 + 6, SEA)
        bb.fill(x + 1, y0, z1 + 6, x + 2, y0 + 3, z1 + 6, "minecraft:iron_bars")
    # the glass wall: it faces a pool of lake water dug out past the island rim
    bb.fill(x1 + 2, y0, z2 + 1, x2 - 2, y1, z2 + 1, "minecraft:glass")
    bb.fill(x1 + 2, y0 - 1, z2 + 2, x2 - 2, y1, CZ + ISLE - 1, "minecraft:water")
    bb.fill(x1 + 2, y0 - 2, z2 + 2, x2 - 2, y0 - 2, CZ + ISLE + 1, "minecraft:sand")
    for x in range(x1 + 4, x2 - 3, 5):
        bb.set(x, y1, (z1 + z2) // 2, "minecraft:soul_lantern[hanging=true]")
    bb.fill(CX + 10, y0, z1, CX + 10, 0, z1, "minecraft:ladder[facing=south]")
    bb.set(CX + 10, 0, z1, "minecraft:spruce_trapdoor[facing=south,half=top,open=false]") if False else None
    bb.fill(CX + 10, y0, z1 - 1, CX + 10, 0, z1 - 1, SEA)
    bb.fill(x1 + 6, y0, z2 - 3, x2 - 6, y0, z2 - 3, "minecraft:red_carpet")


def bananawani(bb):
    """The statue sprawled over the top: a long ridged body along z, legs gripping the top tier, the tail curling down
    the north face, the head reaching over the south face with jaws open, the banana crest on its head."""
    y = PTOP + 1
    L = 48
    z0 = CZ - 26
    for i in range(L):
        z = z0 + i
        t = i / L
        w = 5.5 * math.sin(math.pi * min(1, (t + 0.08) / 0.9)) + 1.2
        hh = 3.5 * math.sin(math.pi * min(1, (t + 0.05) / 0.92)) + 1
        zc = z
        ybase = y if abs(z - CZ) <= H(PTOP) else max(1, y - (abs(z - CZ) - H(PTOP)) * 3 // 2)
        if z < CZ - H(PTOP):                            # the tail drapes down the north slope
            ybase = PTOP + 1 - int((CZ - H(PTOP) - z) * 1.5)
        bb.fill_where(CX - 7, ybase, zc, CX + 7, ybase + 6, zc,
                      lambda X, Y, Z: ((X - CX) / w) ** 2 + ((Y - ybase) / hh) ** 2 <= 1, CROC)
        bb.fill_where(CX - 7, ybase, zc, CX + 7, ybase + 7, zc,
                      lambda X, Y, Z: (np.abs(X - CX) <= 1) & (Y >= ybase + hh - 0.5) & (Y <= ybase + hh + 0.6) & ((Z % 2) == 0), CROC3)
        bb.fill_where(CX - 7, ybase, zc, CX + 7, ybase + 1, zc,
                      lambda X, Y, Z: (((X - CX) / w) ** 2 <= 1) & (Y == ybase), CROC2)
    # legs on the four corners of the top
    for (dx, dz) in ((-6, -8), (6, -8), (-6, 8), (6, 8)):
        for k in range(4):
            bb.fill(CX + dx + (k if dx > 0 else -k) // 2, y - k, CZ + dz, CX + dx + (k if dx > 0 else -k) // 2 + (1 if dx > 0 else -1),
                    y - k + 1, CZ + dz + 1, CROC)
    # head over the south face, jaws open, teeth, eyes, the banana crest
    hz = z0 + L
    hyb = y - 4
    for i in range(12):
        z = hz + i
        hw = 4 - i // 4
        bb.fill(CX - hw, hyb + 3, z, CX + hw, hyb + 5, z, CROC)                 # upper jaw, raised
        bb.fill(CX - hw, hyb - 1, z, CX + hw, hyb, z, CROC)                     # lower jaw
        bb.fill(CX - hw + 1, hyb + 1, z, CX + hw - 1, hyb + 2, z, AIR)
        if i % 2 == 0:
            bb.set(CX - hw, hyb + 2, z, "minecraft:white_concrete"); bb.set(CX + hw, hyb + 2, z, "minecraft:white_concrete")
            bb.set(CX - hw, hyb + 1, z, "minecraft:white_concrete") if i % 4 == 0 else None
            bb.set(CX + hw, hyb + 1, z, "minecraft:white_concrete") if i % 4 == 0 else None
        bb.fill(CX - hw + 1, hyb, z, CX + hw - 1, hyb, z, "minecraft:red_terracotta")
    bb.fill(CX - 4, hyb - 1, hz - 3, CX + 4, hyb + 6, hz, CROC)
    for dx in (-3, 3):
        bb.set(CX + dx, hyb + 6, hz + 1, "minecraft:yellow_concrete"); bb.set(CX + dx, hyb + 7, hz + 1, "minecraft:black_concrete")
    for k in range(9):                                                          # the banana crest
        a = math.pi * k / 8
        bb.set(CX, round(hyb + 7 + 3 * math.sin(a)), round(hz - 4 + 6 * k / 8), "minecraft:yellow_concrete")
        bb.set(CX, round(hyb + 6 + 3 * math.sin(a)), round(hz - 4 + 6 * k / 8), "minecraft:yellow_concrete")
    bb.set(CX, hyb + 7, hz - 5, "minecraft:brown_concrete")


def causeway_bridge(bb):
    for z in range(CZ + ISLE - 1, CZ + LAKE + 4):
        bb.fill(CX - 3, 0, z, CX + 3, 0, z, SAND)
        bb.fill(CX - 3, -9, z, CX - 3, -1, z, SAND) if (z - CZ) % 5 == 0 else None
        bb.fill(CX + 3, -9, z, CX + 3, -1, z, SAND) if (z - CZ) % 5 == 0 else None
        bb.set(CX - 4, 1, z, "onepiece:alabasta_sandstone_brick_wall"); bb.set(CX + 4, 1, z, "onepiece:alabasta_sandstone_brick_wall")
        bb.set(CX - 4, 0, z, SAND); bb.set(CX + 4, 0, z, SAND)
        if (z - CZ) % 6 == 0:
            bb.set(CX - 4, 2, z, "minecraft:lantern[hanging=false]"); bb.set(CX + 4, 2, z, "minecraft:lantern[hanging=false]")
    # palms on the island round the pyramid
    for (x, z) in ((CX - 8, CZ + P0 + 4), (CX + 8, CZ + P0 + 4), (CX - 36, CZ - 30), (CX + 36, CZ - 30), (CX - 36, CZ + 30),
                   (CX + 36, CZ + 30), (CX - 37, CZ), (CX + 37, CZ)):
        palm(bb, x, 1, z, 9, (1 if x < CX else -1, 0))


def rainbase(bb, tracker, audit, rng):
    placed = []
    k = 0
    for _ in range(4000):
        w, d = int(rng.integers(8, 13)), int(rng.integers(8, 11))
        x0, z0 = int(rng.integers(4, N - w - 4)), int(rng.integers(4, N - d - 4))
        xs = np.arange(x0 - 1, x0 + w + 1)[:, None]; zs = np.arange(z0 - 1, z0 + d + 1)[None, :]
        if not town_zone(xs, zs).all() or streets(xs, zs).any() or (HMAP[np.clip(xs, 0, N - 1), np.clip(zs, 0, N - 1)] > 0).any():
            continue
        box = (x0 - 2, z0 - 2, x0 + w + 1, z0 + d + 1)
        if any(box[0] <= r[2] and r[0] <= box[2] and box[1] <= r[3] and r[1] <= box[3] for r in placed):
            continue
        cxx, czz = x0 + w / 2 - CX, z0 + d / 2 - CZ
        rot = (0 if czz < 0 else 2) if abs(czz) > abs(cxx) else (3 if cxx < 0 else 1)      # doors toward the lake
        W, D = (w, d) if rot % 2 == 0 else (d, w)
        if W != w:
            continue
        fl = int(rng.integers(1, 4))
        m, _, au = house_module(seed_of("rb", x0, z0), w, d, fl, "flat:" + ("orange", "red", "light_blue", "white", "yellow")[k % 5],
                                tracker, [["kitchen", "living", "workshop", "dining"][k % 4], "bedroom", "storage"],
                                pal=TOWN, timber=False, jetty=False, chimney=False)
        audit += au
        place_house(bb, m, w, d, x0, 0, z0, rot)
        placed.append(box)
        k += 1
        if k >= 44:
            break
    print("houses:", k)
    # market stalls along the lake road
    for a in range(0, 360, 20):
        t = math.radians(a)
        x, z = round(CX + (LAKE + 9) * math.cos(t)), round(CZ + (LAKE + 9) * math.sin(t))
        if any(r[0] - 1 <= x <= r[2] + 1 and r[1] - 1 <= z <= r[3] + 1 for r in placed) or streets(np.array([[x]]), np.array([[z]]))[0, 0]:
            continue
        if not (0 < x < N - 3 and 0 < z < N - 3):
            continue
        for (dx, dz) in ((0, 0), (2, 0), (0, 2), (2, 2)):
            bb.fill(x + dx, 1, z + dz, x + dx, 3, z + dz, "minecraft:jungle_fence")
        bb.fill(x, 4, z, x + 2, 4, z + 2, ("minecraft:red_wool", "minecraft:orange_wool", "minecraft:light_blue_wool", "minecraft:white_wool")[a // 20 % 4])
        bb.set(x + 1, 1, z + 1, "minecraft:barrel[facing=up,open=false]")
        placed.append((x - 1, z - 1, x + 3, z + 3))
    for _ in range(300):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        if lake(np.array([[x]]), np.array([[z]]))[0, 0] or streets(np.array([[x]]), np.array([[z]]))[0, 0]:
            continue
        if not (LAKE - 1 < sq(np.array([[x]]), np.array([[z]]))[0, 0] < LAKE + 40):
            continue
        if any(r[0] - 2 <= x <= r[2] + 2 and r[1] - 2 <= z <= r[3] + 2 for r in placed):
            continue
        palm(bb, x, hy(x, z) + 1, z, int(rng.integers(7, 11)), (int(rng.integers(-1, 2)), int(rng.integers(-1, 2))))
        placed.append((x - 3, z - 3, x + 3, z + 3))
        if len(placed) > 120:
            break


def design():
    bb = BigBuild(seed=2820, y_min=-14, y_max=70)
    tracker = P.PropTracker(2820)
    audit = []
    rng = np.random.default_rng(2820)
    terrain(bb)
    pyramid(bb, tracker, audit)
    cage_room(bb)
    bananawani(bb)
    causeway_bridge(bb)
    rainbase(bb, tracker, audit, rng)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 2890, density=0.08,
              kinds=["minecraft:dead_bush", "minecraft:short_dry_grass", "minecraft:tall_dry_grass"], flowers=["minecraft:cactus[age=0]"],
              mask=lambda X, Z: (sq(X, Z, p=4) > LAKE + 30))
    return bb, audit


def steady(b):
    """Sand with nothing solid under it would fall when the build generates: turn it into blocks that stay put."""
    import render
    for (x, y, z), s in list(b.blocks.items()):
        n = s.split("[")[0]
        if n.endswith(("gravel", "sand", "concrete_powder")) and "sandstone" not in n:
            below = b.blocks.get((x, y - 1, z))
            if (below is None and y >= -14) or (below is not None and render.shape_of(below) != "full"):
                b.blocks[(x, y, z)] = "minecraft:coarse_dirt" if "gravel" in n else "minecraft:smooth_sandstone" if n == "minecraft:sand" \
                    else "minecraft:smooth_red_sandstone" if "red_sand" in n else n.replace("concrete_powder", "concrete")


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    steady(b)
    b.npc(CX - 9, 22, CZ - 11, "crocodile", True)
    b.chest(CX + 1, 31, CZ - 1, "treasure", "south")
    b.chest(CX - 14, 1, CZ - 20, "treasure", "south")
    b.guards("baroque_agent", ((CX - 6, CZ + P0 + 8), (CX + 6, CZ + P0 + 8), (CX - 14, CZ), (CX + 14, CZ), (CX, CZ - 10)), y=1)
    b.guards("baroque_agent", ((CX + 8, CZ + 8), (CX - 8, CZ + 8)), y=12)
    b.guards("baroque_agent", ((CX - 4, CZ + 22), (CX + 4, CZ + 22)), y=-7)
    return b, 0
