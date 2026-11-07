"""Franky House v2, redesigned with the Minecraft Builder skill: the Franky Family's hideout on the scrapyard shore
of Water 7, where Franky built the Thousand Sunny.

A Water 7 island with the sea on the north. On the shore stands Franky House: a big three-storey warehouse built
from salvage, walls patched from planks, blue terracotta, copper and iron, iron posts, a long blue roof with roof
lights, FRANKY painted along the sea front and the big yellow star on the gable. Inside: the garage with the
Franky Family's machines, a Battle Franky robot and the workbench; upstairs the party hall with the cola bar and the
Franky Family's bunks; on top Franky's own workshop with the plans of the dream ship and the crate of Adam wood.
Beside it the slipway and fitting-out dock where the Thousand Sunny lies, two harbour cranes, scrap heaps round the
yard, cola crates, the canal with the Yagara Bull pens and the Square Sisters' boats, and a row of Water 7 houses
along the canal behind. 168 x 168. y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, set_if_air, wing_floor, house_module, place_house, lamp_post, glyph
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.shipstamp import stamp_ship

SID = "franky_house"
TITLE = "Franky House"
CUTS = [4, 10, 16, 24]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 168
_S1 = NT.outline(84, 88, 69, 3220, wobble=0.08)
_S2 = NT.outline(116, 106, 38, 3221, wobble=0.07)
SHORE = lambda X, Z: np.maximum(_S1(X, Z), _S2(X, Z))
GY = 2
QUAY_Z = 34                         # the shore quay; sea north of it
HOUSE = (50, 46, 108, 82)           # Franky House footprint
FH = 6
DOCK = (102, 8, 150, QUAY_Z)        # the fitting-out dock (water) where the Sunny lies
CANAL_X = 32                        # the canal runs south from the sea at x 30..34
YARD = (14, 38, 160, 150)

STREET = [("minecraft:stone_bricks", 0.3), ("minecraft:cobblestone", 0.2), ("minecraft:andesite", 0.15),
          ("minecraft:polished_andesite", 0.15), ("minecraft:gravel", 0.0), ("minecraft:cracked_stone_bricks", 0.1),
          ("minecraft:mossy_cobblestone", 0.1)]
YARDG = [("minecraft:coarse_dirt", 0.3), ("minecraft:packed_mud", 0.2), ("minecraft:dirt", 0.15), ("minecraft:andesite", 0.15),
         ("minecraft:cobblestone", 0.1), ("minecraft:rooted_dirt", 0.1)]
SAND = [("minecraft:sand", 0.7), ("minecraft:sandstone", 0.15), ("minecraft:clay", 0.15)]
JUNK = [("minecraft:iron_block", 0.08), ("minecraft:waxed_weathered_copper", 0.1), ("minecraft:waxed_oxidized_cut_copper", 0.06),
        ("minecraft:spruce_planks", 0.14), ("minecraft:dark_oak_planks", 0.1), ("minecraft:stripped_spruce_log", 0.08),
        ("minecraft:anvil[facing=north]", 0.03), ("minecraft:cobblestone", 0.12), ("minecraft:light_blue_terracotta", 0.06),
        ("minecraft:blue_terracotta", 0.05), ("minecraft:barrel[facing=up,open=false]", 0.08), ("minecraft:coal_block", 0.04),
        ("minecraft:chiseled_copper", 0.06)]
DEBRIS = ["minecraft:iron_bars", "minecraft:chain[axis=x]", "minecraft:iron_trapdoor[facing=north,half=bottom,open=false]",
          "minecraft:spruce_trapdoor[facing=east,half=bottom,open=true]", "minecraft:copper_bulb[lit=false]",
          "minecraft:barrel[facing=up,open=false]", "minecraft:chain[axis=z]"]
PALS = [
    dict(walls=["minecraft:stone_bricks", "minecraft:smooth_stone", "minecraft:light_gray_terracotta"], frame="minecraft:stone_bricks",
         base=["minecraft:stone_bricks", "minecraft:cobblestone", "minecraft:andesite"], floor="minecraft:spruce_planks",
         wood="spruce", chimney="minecraft:bricks"),
    dict(walls=["minecraft:white_terracotta", "minecraft:calcite", "minecraft:smooth_sandstone"], frame="minecraft:stripped_spruce_log",
         base=["minecraft:stone_bricks", "minecraft:cobblestone", "minecraft:mossy_stone_bricks"], floor="minecraft:oak_planks",
         wood="spruce", chimney="minecraft:bricks"),
    dict(walls=["minecraft:light_blue_terracotta", "minecraft:white_terracotta", "minecraft:calcite"], frame="minecraft:stripped_dark_oak_log",
         base=["minecraft:stone_bricks", "minecraft:andesite", "minecraft:cobblestone"], floor="minecraft:spruce_planks",
         wood="dark_oak", chimney="minecraft:bricks"),
]
ROOFS = ["minecraft:dark_prismarine_stairs", "minecraft:deepslate_tile_stairs", "minecraft:prismarine_brick_stairs",
         "minecraft:brick_stairs"]
KINDS = [["kitchen", "living", "bedroom"], ["workshop", "storage", "bedroom"], ["dining", "living", "bedroom"]]
FONT = {"F": ["#####", "#....", "####.", "#....", "#...."], "R": ["####.", "#...#", "####.", "#..#.", "#...#"],
        "A": [".###.", "#...#", "#####", "#...#", "#...#"], "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#"],
        "K": ["#...#", "#..#.", "###..", "#..#.", "#...#"], "Y": ["#...#", ".#.#.", "..#..", "..#..", "..#.."]}


def rect_d(X, Z, r):
    dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0)
    dz = np.maximum(np.maximum(r[1] - Z, Z - r[3]), 0)
    return np.hypot(dx, dz)


def canal(X, Z):
    X = np.asarray(X); Z = np.asarray(Z)
    return (np.abs(X - CANAL_X) <= 2) & (Z < 150) | (np.abs(Z - 150) <= 2) & (X >= CANAL_X - 2) & (X < 100)


def streets(X, Z):
    X = np.asarray(X); Z = np.asarray(Z)
    m = (Z >= QUAY_Z) & (Z <= QUAY_Z + 4) & (X >= 0)
    m |= (np.abs(X - CANAL_X - 5) <= 1) & (Z > QUAY_Z) & (Z < 147)
    m |= (np.abs(Z - 145) <= 1) & (X > CANAL_X) & (X < 104)
    m |= (np.abs(X - 79) <= 2) & (Z > HOUSE[3]) & (Z < 145)
    return m


def heap(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    h = np.clip(NT.fbm(X, Z, 3241, 14) - 0.42, 0, 1) * 34 + np.clip(NT.noise(X, Z, 3242, 5) - 0.55, 0, 1) * 5
    h = h * np.clip((rect_d(X, Z, HOUSE) - 5) / 6.0, 0, 1) * np.clip((Z - QUAY_Z - 8) / 6.0, 0, 1)
    h = h * (Z < 128)
    h = np.where(streets(X, Z) | canal(X, Z) | (np.abs(X - CANAL_X) <= 6), 0, h)
    return np.round(h)


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = SHORE(X, Z)
    h = GY + np.clip(NT.fbm(X, Z, 3222, 26) - 0.45, 0, 1) * 16
    h = np.where(Z > 128, h, GY)
    h = np.where(d < 8, np.minimum(h, GY * d / 8.0 + 0.4), h)
    h = np.where(Z < QUAY_Z, -4, h)
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
HEAP = heap(np.arange(N)[:, None], np.arange(N)[None, :]).astype(int)


def height(X, Z):
    return HMAP[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def steep(X, Z):
    return GRAD[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)] >= 2


def land(X, Z):
    return (SHORE(X, Z) > 1.5) & (np.asarray(Z) >= QUAY_Z)


def hy(x, z):
    return int(HMAP[min(max(x, 0), N - 1), min(max(z, 0), N - 1)])


def terrain(bb):
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SAND, 3231, mask=lambda X, Z: land(X, Z) & (SHORE(X, Z) < 6) & (np.asarray(Z) > QUAY_Z + 4),
             under="minecraft:sandstone", core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, NT.MEADOW, 3233,
             mask=lambda X, Z: land(X, Z) & (SHORE(X, Z) >= 6) & (np.asarray(Z) > 126), core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, YARDG, 3232,
             mask=lambda X, Z: land(X, Z) & (SHORE(X, Z) >= 6) & (np.asarray(Z) <= 126), core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, STREET, 3234, mask=lambda X, Z: land(X, Z) & streets(X, Z), core="minecraft:stone")
    bed = lambda X, Z: np.where(np.asarray(Z) < QUAY_Z, np.minimum(-5 - np.clip((QUAY_Z - np.asarray(Z)) * 0.4, 0, 5),
                                                                    np.round(-2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10))),
                                np.round(-2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10)))
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy == bed(X, Z)), "minecraft:sand")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy < bed(X, Z)) & (yy >= bed(X, Z) - 2), "minecraft:stone")
    # the canal: stone banks, water to y 0
    bb.fill_where(0, -4, 0, N - 1, GY, N - 1, lambda X, yy, Z: canal(X, Z) & land(X, Z), "minecraft:stone_bricks")
    bb.fill_where(0, -3, 0, N - 1, GY, N - 1,
                  lambda X, yy, Z: canal(X, Z) & land(X, Z) & ((np.abs(np.asarray(X) - CANAL_X) <= 1) & (np.asarray(Z) < 149)
                                                                | (np.abs(np.asarray(Z) - 150) <= 1) & (np.asarray(X) > CANAL_X - 2)),
                  "minecraft:water")
    bb.fill_where(0, 1, 0, N - 1, GY, N - 1,
                  lambda X, yy, Z: canal(X, Z) & land(X, Z) & ((np.abs(np.asarray(X) - CANAL_X) <= 1) & (np.asarray(Z) < 149)
                                                                | (np.abs(np.asarray(Z) - 150) <= 1) & (np.asarray(X) > CANAL_X - 2)),
                  AIR)


# ------------------------------------------------------------------ Franky House
def franky_house(bb, tracker, audit):
    x1, z1, x2, z2 = HOUSE
    y0 = GY
    top = y0 + 3 * FH
    bb.fill(x1, y0 - 3, z1, x2, y0, z2, "minecraft:stone_bricks")
    bb.fill(x1, y0, z1, x2, y0, z2, "minecraft:polished_andesite")
    # patchwork walls: big salvage panels picked by noise, iron posts every 6
    pan = ["minecraft:spruce_planks", "minecraft:blue_terracotta", "minecraft:light_blue_terracotta", "minecraft:waxed_weathered_copper",
           "minecraft:dark_oak_planks", "minecraft:waxed_exposed_cut_copper", "minecraft:spruce_planks", "minecraft:cyan_terracotta"]
    for i, blk in enumerate(pan):
        def f(X, Y, Z, i=i):
            v = NT.noise(np.asarray(X) + np.asarray(Z), np.asarray(Y) * 3.0 + 7, 3250, 4)
            on = (np.asarray(X) == x1) | (np.asarray(X) == x2) | (np.asarray(Z) == z1) | (np.asarray(Z) == z2)
            return on & (np.clip((v - 0.15) / 0.7, 0, 0.999) * len(pan) // 1 == i)
        bb.fill_where(x1, y0 + 1, z1, x2, top, z2, f, blk)
    for x in range(x1, x2 + 1, 6):
        for z in (z1, z2):
            bb.fill(x, y0 + 1, z, x, top, z, "minecraft:iron_block")
    for z in range(z1, z2 + 1, 6):
        for x in (x1, x2):
            bb.fill(x, y0 + 1, z, x, top, z, "minecraft:iron_block")
    for k in range(1, 3):
        y = y0 + FH * k
        bb.fill(x1, y, z1, x2, y, z2, "minecraft:spruce_planks")
        for (a, b, c, d) in ((x1, z1, x2, z1), (x1, z2, x2, z2), (x1, z1, x1, z2), (x2, z1, x2, z2)):
            bb.fill(a, y, b, c, y, d, "minecraft:iron_block")
    bb.fill(x1, top, z1, x2, top, z2, "minecraft:spruce_planks")
    # windows: round portholes upstairs, wide garage doors on the ground floor
    for k in range(1, 3):
        y = y0 + FH * k + 2
        for x in range(x1 + 3, x2 - 1, 6):
            for z in (z1, z2):
                bb.fill(x - 1, y, z, x + 1, y + 1, z, "minecraft:glass_pane")
                bb.set(x, y + 2, z, "minecraft:glass_pane")
        for z in range(z1 + 3, z2 - 1, 6):
            for x in (x1, x2):
                bb.fill(x, y, z - 1, x, y + 1, z + 1, "minecraft:glass_pane")
    for gx in (x1 + 8, x1 + 20, x2 - 20):
        bb.fill(gx, y0 + 1, z1, gx + 6, y0 + 5, z1, AIR)
        bb.fill(gx, y0 + 5, z1 - 1, gx + 6, y0 + 5, z1 - 1, "minecraft:iron_trapdoor[facing=north,half=top,open=false]")
    bb.fill(79 - 2, y0 + 1, z2, 79 + 2, y0 + 4, z2, AIR)
    # roof: long blue gable with roof lights, a ridge walk
    P.gable_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, top + 1, "minecraft:dark_prismarine_stairs", ridge_axis="x",
                 gable_fill="minecraft:light_blue_terracotta", overhang=1)
    for x in range(x1 + 4, x2 - 3, 8):
        for z in (z1 + 6, z2 - 6):
            bb.set(x, top + 1 + min(z - z1, z2 - z) - 0, z, "minecraft:glass") if False else None
    # FRANKY along the sea front, the big star on the east gable
    word = "FRANKY"
    rows = ["".join(FONT[ch][r] + "." for ch in word) for r in range(5)]
    glyph(bb, rows, (x1 + x2) // 2 - len(rows[0]) // 2, top - 2, z1 - 1, "minecraft:yellow_concrete", axis="x")
    glyph(bb, rows, (x1 + x2) // 2 - len(rows[0]) // 2, top - 2, z2 + 1, "minecraft:yellow_concrete", axis="x")
    star = ["....#....", "...###...", "#########", ".#######.", "..#####..", ".###.###.", "##.....##"]
    glyph(bb, star, x2 + 2, top + 12, (z1 + z2) // 2 - 4, "minecraft:yellow_concrete", axis="z")
    glyph(bb, star, x1 - 2, top + 12, (z1 + z2) // 2 - 4, "minecraft:yellow_concrete", axis="z")
    # inside, ground floor: the garage
    garage(bb, x1, z1, x2, z2, y0)
    # first floor: party hall + bar + bunks; second floor: workshop and stores
    bb.fill(x1 + 2, y0 + 1, z2 - 4, x1 + 2, top - 1, z2 - 4, "minecraft:ladder[facing=north]")
    bb.fill(x1 + 1, y0 + FH, z2 - 4, x1 + 3, y0 + FH, z2 - 4, "minecraft:spruce_planks")
    bb.fill(x1 + 1, y0 + 2 * FH, z2 - 4, x1 + 3, y0 + 2 * FH, z2 - 4, "minecraft:spruce_planks")
    for k in (1, 2):
        bb.set(x1 + 2, y0 + FH * k, z2 - 4, "minecraft:ladder[facing=north]")
    hall(bb, x1 + 1, z1 + 1, x1 + 30, z2 - 1, y0 + FH + 1)
    wing_floor(bb, x1 + 31, z1 + 1, x2 - 1, z2 - 1, y0 + FH + 1, FH - 1, "minecraft:spruce_planks", seed_of("fkb"), tracker,
               ["bedroom", "bedroom", "bedroom", "dining", "bedroom", "storage"], corridor="z", cw=3, wood="spruce", audit=audit)
    bb.fill(x1 + 30, y0 + FH + 1, (z1 + z2) // 2 - 1, x1 + 31, y0 + FH + 3, (z1 + z2) // 2 + 1, AIR)
    wing_floor(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, y0 + 2 * FH + 1, FH - 1, "minecraft:spruce_planks", seed_of("fkw"), tracker,
               ["workshop", "workshop", "storage", "library", "workshop", "storage", "living"], corridor="x", cw=3, wood="dark_oak",
               audit=audit, keep=[(x1 + 1, z2 - 6, x1 + 4, z2 - 1)])
    # Franky's dream-ship plans and the Adam wood crate in the workshop corridor
    cz = (z1 + z2) // 2
    bb.fill(x2 - 10, y0 + 2 * FH + 1, cz - 1, x2 - 6, y0 + 2 * FH + 1, cz + 1, "minecraft:dark_oak_log[axis=x]")
    bb.set(x2 - 8, y0 + 2 * FH + 2, cz, "minecraft:cartography_table")
    for k in range(3):
        bb.set(x1 + 10 + k * 14, y0 + 3 * FH - 1, cz, "minecraft:lantern[hanging=true]")
    return (x1 - 3, z1 - 3, x2 + 3, z2 + 3)


def battle_franky(bb, x, y, z):
    """A Battle Franky robot: a boxy iron body on two legs, a blue visor, one cannon arm."""
    for dz in (-2, 2):
        bb.fill(x, y, z + dz, x, y + 3, z + dz, "minecraft:iron_block")
    bb.fill(x - 1, y + 4, z - 3, x + 1, y + 8, z + 3, "minecraft:iron_block")
    bb.fill(x + 2, y + 6, z - 2, x + 2, y + 7, z + 2, "minecraft:light_blue_stained_glass")
    bb.fill(x, y + 9, z - 1, x, y + 10, z + 1, "minecraft:iron_block")
    bb.set(x + 1, y + 10, z, "minecraft:redstone_lamp[lit=true]")
    bb.fill(x, y + 7, z + 4, x + 4, y + 7, z + 4, "minecraft:polished_blackstone")
    bb.fill(x, y + 4, z - 4, x, y + 7, z - 4, "minecraft:iron_block")
    bb.set(x + 1, y + 4, z - 4, "minecraft:iron_bars")


def garage(bb, x1, z1, x2, z2, y):
    """The garage: an open hall with lifts, a robot, workbenches, tool walls and the Franky Family's carts."""
    cz = (z1 + z2) // 2
    battle_franky(bb, x1 + 34, y + 1, cz)
    for x in range(x1 + 3, x2 - 2, 4):
        bb.set(x, y + 1, z2 - 1, ("minecraft:crafting_table", "minecraft:smithing_table", "minecraft:anvil[facing=east]",
                                   "minecraft:grindstone[face=floor,facing=north]", "minecraft:blast_furnace[facing=north,lit=true]")[x % 5])
        bb.set(x, y + 3, z2 - 1, "minecraft:chain[axis=y]") if x % 8 == 3 else None
    for x in range(x1 + 4, x2 - 3, 12):
        # car lift: four posts and a platform with a cart on it
        bb.fill(x, y + 1, z1 + 6, x, y + 4, z1 + 6, "minecraft:iron_bars"); bb.fill(x + 5, y + 1, z1 + 6, x + 5, y + 4, z1 + 6, "minecraft:iron_bars")
        bb.fill(x, y + 1, z1 + 12, x, y + 4, z1 + 12, "minecraft:iron_bars"); bb.fill(x + 5, y + 1, z1 + 12, x + 5, y + 4, z1 + 12, "minecraft:iron_bars")
        bb.fill(x + 1, y + 3, z1 + 7, x + 4, y + 3, z1 + 11, "minecraft:iron_trapdoor[facing=north,half=top,open=false]")
        bb.fill(x + 1, y + 4, z1 + 8, x + 4, y + 4, z1 + 10, "minecraft:red_terracotta")
        bb.set(x + 1, y + 5, z1 + 9, "minecraft:red_stained_glass")
    for z in range(z1 + 2, z2 - 1, 3):
        bb.set(x2 - 1, y + 1, z, "minecraft:barrel[facing=up,open=false]")
        bb.set(x2 - 1, y + 2, z, "minecraft:blue_terracotta" if z % 2 else "minecraft:barrel[facing=up,open=false]")
    for k in range(4):
        bb.set(x1 + 8 + k * 12, y + FH - 1, cz, "minecraft:lantern[hanging=true]")
        bb.set(x1 + 8 + k * 12, y + FH - 1, z1 + 4, "minecraft:lantern[hanging=true]")


def hall(bb, x1, z1, x2, z2, y):
    """The party hall: the cola bar with its fridge wall, tables, a stage with a speaker stack, a pool table."""
    bb.fill(x1, y, z1, x2, y + FH - 2, z2, AIR)
    bb.fill(x1, y - 1, z1, x2, y - 1, z2, "minecraft:dark_oak_planks")
    bb.fill(x1 + 4, y - 1, z1 + 4, x2 - 4, y - 1, z2 - 4, "minecraft:polished_deepslate")
    # bar along the north wall
    bb.fill(x1 + 3, y, z1 + 3, x2 - 6, y, z1 + 3, "minecraft:polished_andesite")
    bb.fill(x1 + 3, y + 1, z1 + 3, x2 - 6, y + 1, z1 + 3, "minecraft:smooth_stone_slab[type=bottom]")
    for x in range(x1 + 3, x2 - 5):
        bb.set(x, y, z1 + 1, "minecraft:blue_ice" if x % 3 == 0 else "minecraft:barrel[facing=south,open=false]")
        bb.set(x, y + 1, z1 + 1, "minecraft:light_blue_stained_glass" if x % 2 else "minecraft:brewing_stand")
        if x % 3 == 1:
            bb.set(x, y, z1 + 4, st("minecraft:dark_oak_stairs", "north"))
    for (tx, tz) in ((x1 + 6, z1 + 10), (x1 + 14, z1 + 10), (x1 + 22, z1 + 10), (x1 + 6, z1 + 18), (x1 + 14, z1 + 18), (x1 + 22, z1 + 18)):
        bb.set(tx, y, tz, "minecraft:spruce_fence"); bb.set(tx, y + 1, tz, "minecraft:spruce_pressure_plate")
        for (ox, oz, f) in ((-1, 0, "east"), (1, 0, "west"), (0, -1, "south"), (0, 1, "north")):
            bb.set(tx + ox, y, tz + oz, st("minecraft:spruce_stairs", f))
    # the stage and speakers in the south-east corner
    bb.fill(x2 - 9, y, z2 - 7, x2 - 1, y, z2 - 1, "minecraft:spruce_slab[type=bottom]")
    for (sx, sz) in ((x2 - 9, z2 - 1), (x2 - 1, z2 - 7)):
        bb.fill(sx, y + 1, sz, sx, y + 3, sz, "minecraft:note_block")
        bb.set(sx, y + 4, sz, "minecraft:jukebox")
    bb.set(x2 - 5, y + 1, z2 - 4, "minecraft:jukebox")
    # the pool table
    bb.fill(x1 + 8, y, z2 - 6, x1 + 12, y, z2 - 4, "minecraft:green_wool")
    for (a, b) in ((x1 + 8, z2 - 6), (x1 + 12, z2 - 6), (x1 + 8, z2 - 4), (x1 + 12, z2 - 4)):
        bb.set(a, y, b, "minecraft:dark_oak_planks")
    for x in range(x1 + 4, x2 - 2, 7):
        bb.set(x, y + FH - 3, (z1 + z2) // 2, "minecraft:lantern[hanging=true]")
    # streamers
    for x in range(x1, x2 + 1):
        bb.set(x, y + FH - 3, z1 + 6, ("minecraft:red_carpet", "minecraft:yellow_carpet", "minecraft:light_blue_carpet")[x % 3]) \
            if False else None


# ------------------------------------------------------------------ the dock, the yard
def dock(bb, rng):
    """The fitting-out dock: stone walls round a basin, the Thousand Sunny moored in it, two harbour cranes, the quay."""
    x1, z1, x2, z2 = DOCK
    for x in range(0, N):
        if SHORE(np.array([[x]]), np.array([[QUAY_Z + 2]]))[0, 0] < 1.5:
            continue
        bb.fill(x, -6, QUAY_Z, x, GY, QUAY_Z, "minecraft:stone_bricks")
        bb.set(x, GY, QUAY_Z, "minecraft:polished_andesite")
        if x % 6 == 0:
            bb.set(x, GY + 1, QUAY_Z, "minecraft:stone_brick_wall")
    # two dock arms out to sea
    for x in (x1 - 2, x2 + 2):
        bb.fill(x - 1, -8, z1, x + 1, GY, QUAY_Z, "minecraft:stone_bricks")
        bb.fill(x - 1, GY, z1, x + 1, GY, QUAY_Z, "minecraft:polished_andesite")
        for z in range(z1, QUAY_Z, 6):
            bb.set(x, GY + 1, z, "minecraft:lantern[hanging=false]") if z % 12 == z1 % 12 else bb.set(x + (1 if x > x1 else -1), GY + 1, z,
                                                                                                         "minecraft:stone_brick_wall")
    stamp_ship(bb, "thousand_sunny", (x1 + x2) // 2, QUAY_Z - 12, water_y=0, rot=0)
    for cx in (x1 - 2, x2 + 2):
        crane(bb, cx, GY + 1, QUAY_Z - 8, 1 if cx < x1 else -1)
    # the ship's timber stack and a gangway
    for k in range(4):
        bb.fill(112, GY + 1 + k, QUAY_Z + 6, 121, GY + 1 + k, QUAY_Z + 7, "minecraft:stripped_dark_oak_log[axis=x]")
        bb.fill(112, GY + 1 + k, QUAY_Z + 9, 121 - k * 2, GY + 1 + k, QUAY_Z + 10, "minecraft:dark_oak_log[axis=x]") if k < 3 else None


def crane(bb, x, y, z, side):
    """A harbour crane: a lattice tower of iron bars with a cab, a long jib out over the water and a hook on a chain."""
    for (a, b) in ((x - 1, z - 1), (x + 1, z - 1), (x - 1, z + 1), (x + 1, z + 1)):
        bb.fill(a, y, b, a, y + 18, b, "minecraft:iron_block" if (a + b) % 2 == 0 else "minecraft:iron_bars")
    for yy in range(y + 3, y + 18, 4):
        bb.fill(x - 1, yy, z - 1, x + 1, yy, z + 1, "minecraft:iron_trapdoor[facing=north,half=top,open=false]")
    bb.fill(x - 2, y + 19, z - 2, x + 2, y + 22, z + 2, "minecraft:yellow_terracotta")
    bb.fill(x - 1, y + 20, z - 2, x + 1, y + 21, z - 2, "minecraft:glass_pane")
    bb.fill(x, y + 23, z - 14, x, y + 23, z + 5, "minecraft:yellow_concrete")
    bb.fill(x, y + 24, z - 12, x, y + 24, z + 4, "minecraft:iron_bars")
    bb.fill(x - 1, y + 21, z + 3, x + 1, y + 23, z + 5, "minecraft:iron_block")
    bb.fill(x, y + 13, z - 13, x, y + 22, z - 13, "minecraft:chain[axis=y]")
    bb.set(x, y + 12, z - 13, "minecraft:tripwire_hook[facing=north]") if False else bb.set(x, y + 12, z - 13, "minecraft:iron_bars")


def junk(bb, rng, taken):
    def blocked(x, z):
        return any(t[0] <= x <= t[2] and t[1] <= z <= t[3] for t in taken)
    mask = np.zeros((N, N), bool)
    for x in range(N):
        for z in range(N):
            mask[x, z] = HEAP[x, z] > 0 and land(np.array([[x]]), np.array([[z]]))[0, 0] and not blocked(x, z) \
                and SHORE(np.array([[x]]), np.array([[z]]))[0, 0] > 4
    TOP = HMAP + np.where(mask, HEAP, 0)
    cum = np.cumsum([w for _, w in JUNK]); cum = cum / cum[-1]
    for i, (blk, _) in enumerate(JUNK):
        lo, hi = (cum[i - 1] if i else 0.0), cum[i]

        def f(X, Y, Z, lo=lo, hi=hi):
            Xc, Zc = np.clip(X, 0, N - 1), np.clip(Z, 0, N - 1)
            r = (NT.noise(X + Y * 2, Z - Y, 3252, 8) * 0.6 + NT.noise(X, Z + Y, 3253, 16) * 0.4)
            r = np.clip((r - 0.2) / 0.6, 0, 0.999)
            return mask[Xc, Zc] & (Y <= TOP[Xc, Zc]) & (Y > HMAP[Xc, Zc]) & (r >= lo) & (r < hi)
        bb.fill_where(0, GY, 0, N - 1, int(TOP.max()) + 1, N - 1, f, blk)
    k = 0
    for _ in range(3000):
        x, z = int(rng.integers(2, N - 2)), int(rng.integers(2, N - 2))
        if not mask[x, z]:
            continue
        y = int(TOP[x, z])
        if rng.random() < 0.04:
            bb.set(x, y + 1, z, "minecraft:campfire[lit=true,signal_fire=true]")
        else:
            bb.set(x, y + 1, z, DEBRIS[int(rng.integers(len(DEBRIS)))])
        k += 1
        if k > 500:
            break
    return mask


def yard(bb, rng, taken):
    """Cola crates, a cola tank, the Yagara Bull pens on the canal, the Square Sisters' boats, lamps."""
    x1, z1, x2, z2 = HOUSE
    for (x, z) in ((x2 + 4, z1 + 2), (x2 + 5, z1 + 2), (x2 + 4, z1 + 3), (x2 + 6, z1 + 2), (x1 - 4, z2 - 2), (x1 - 5, z2 - 2)):
        bb.set(x, GY + 1, z, "minecraft:barrel[facing=up,open=false]")
        bb.set(x, GY + 2, z, "minecraft:barrel[facing=up,open=false]") if (x + z) % 2 else None
    # the cola tank
    tx, tz = x1 - 7, z1 + 8
    bb.cylinder(tx, GY + 1, tz, 3, GY + 9, "minecraft:waxed_weathered_copper", hollow=True)
    bb.fill(tx, GY + 10, tz, tx, GY + 10, tz, "minecraft:waxed_weathered_cut_copper")
    bb.fill(tx + 3, GY + 1, tz, tx + 6, GY + 1, tz, "minecraft:waxed_copper_grate") if False else None
    bb.fill(tx - 3, GY + 1, tz - 1, tx - 3, GY + 9, tz - 1, "minecraft:ladder[facing=west]")
    taken.append((tx - 4, tz - 4, tx + 4, tz + 4))
    # Yagara Bull pens: fenced water bays off the canal with moored bull-boats
    for pz in (60, 84, 108):
        bb.fill(CANAL_X + 3, -3, pz - 4, CANAL_X + 8, GY, pz + 4, "minecraft:stone_bricks")
        bb.fill(CANAL_X + 2, -2, pz - 3, CANAL_X + 7, 0, pz + 3, "minecraft:water")
        bb.fill(CANAL_X + 2, 1, pz - 3, CANAL_X + 7, GY, pz + 3, AIR)
        for z in range(pz - 4, pz + 5):
            bb.set(CANAL_X + 8, GY + 1, z, "minecraft:spruce_fence")
        for x in range(CANAL_X + 3, CANAL_X + 9):
            bb.set(x, GY + 1, pz - 4, "minecraft:spruce_fence"); bb.set(x, GY + 1, pz + 4, "minecraft:spruce_fence")
        bb.set(CANAL_X + 8, GY + 1, pz, "minecraft:spruce_fence_gate[facing=east,open=false]")
        bb.set(CANAL_X + 7, GY + 1, pz - 4, "minecraft:lantern[hanging=false]")
        bb.fill(CANAL_X + 4, 0, pz - 1, CANAL_X + 5, 0, pz + 1, "minecraft:spruce_slab[type=top]")
        bb.set(CANAL_X + 4, 1, pz, st("minecraft:spruce_stairs", "east"))
        taken.append((CANAL_X + 2, pz - 5, CANAL_X + 9, pz + 5))
    # the Square Sisters' boats on the canal mouth
    for (bx, bz) in ((CANAL_X, QUAY_Z - 6), (CANAL_X - 4, QUAY_Z - 12)):
        bb.fill(bx - 1, 0, bz - 3, bx + 1, 0, bz + 3, "minecraft:pink_terracotta")
        bb.fill(bx - 1, 1, bz - 3, bx + 1, 1, bz + 3, "minecraft:spruce_slab[type=bottom]")
        bb.fill(bx, 1, bz - 2, bx, 1, bz + 2, AIR)
    # bridges over the canal
    for bz in (QUAY_Z + 2, 120):
        bb.fill(CANAL_X - 2, GY + 1, bz - 1, CANAL_X + 2, GY + 1, bz + 1, "minecraft:spruce_planks")
        for x in (CANAL_X - 2, CANAL_X + 2):
            pass
        bb.fill(CANAL_X - 2, GY + 2, bz - 1, CANAL_X + 2, GY + 2, bz - 1, "minecraft:spruce_fence")
        bb.fill(CANAL_X - 2, GY + 2, bz + 1, CANAL_X + 2, GY + 2, bz + 1, "minecraft:spruce_fence")
    for z in range(QUAY_Z + 8, 146, 10):
        lamp_post(bb, CANAL_X + 4, GY + 1, z)


def houses(bb, tracker, audit, rng, taken):
    """Water 7 houses: rows along the canal street and behind the scrapyard."""
    k = 0
    for _ in range(5000):
        w, d = int(rng.integers(8, 12)), int(rng.integers(8, 11))
        x0, z0 = int(rng.integers(CANAL_X + 8, N - 10 - w)), int(rng.integers(118, N - 8 - d))
        if rng.random() < 0.3:
            x0, z0 = int(rng.integers(4, CANAL_X - 3 - w)) if CANAL_X - 3 - w > 4 else 4, int(rng.integers(QUAY_Z + 6, N - 8 - d))
        xs = np.arange(x0 - 1, x0 + w + 1)[:, None]; zs = np.arange(z0 - 1, z0 + d + 1)[None, :]
        if streets(xs, zs).any() or canal(xs, zs).any() or (~land(xs, zs)).any() or (SHORE(xs, zs) < 5).any() or (HEAP[np.clip(xs, 0, N - 1), np.clip(zs, 0, N - 1)] > 0).any():
            continue
        hs = HMAP[np.clip(xs, 0, N - 1), np.clip(zs, 0, N - 1)]
        if hs.max() - hs.min() > 2:
            continue
        box = (x0 - 1, z0 - 1, x0 + w, z0 + d)
        if any(box[0] <= r[2] and r[0] <= box[2] and box[1] <= r[3] and r[1] <= box[3] for r in taken):
            continue
        if x0 < CANAL_X:
            rot = 3
        else:
            rot = 2 if abs(z0 - 147) < abs(z0 + d - 143) else 0
        mw, md = (w, d) if rot % 2 == 0 else (d, w)
        y = int(hs.max())
        m, top, au = house_module(seed_of("fk", x0, z0), mw, md, int(rng.integers(2, 4)), ROOFS[k % len(ROOFS)], tracker,
                                  KINDS[k % len(KINDS)], pal=PALS[k % len(PALS)], timber=False, jetty=(k % 3 == 0))
        audit += au
        bb.fill(x0, y - 3, z0, x0 + w - 1, y, z0 + d - 1, "minecraft:stone_bricks")
        place_house(bb, m, mw, md, x0, y, z0, rot)
        taken.append(box)
        k += 1
        if k >= 24:
            break
    print("houses:", k)


def scenery(bb, rng, taken, mask):
    k = 0
    for _ in range(3000):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(QUAY_Z + 6, N - 4))
        X, Z = np.array([[x]]), np.array([[z]])
        if not land(X, Z)[0, 0] or SHORE(X, Z)[0, 0] < 5 or GRAD[x, z] >= 2 or streets(X, Z)[0, 0] or canal(X, Z)[0, 0] or mask[x, z]:
            continue
        if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken):
            continue
        if z < 126 and rng.random() < 0.85:
            continue
        P.tree(bb, x, hy(x, z) + 1, z, int(rng.integers(5, 9)), ("oak", "birch", "oak", "spruce")[k % 4], rng)
        taken.append((x - 3, z - 3, x + 3, z + 3))
        k += 1
        if k >= 40:
            break
    print("trees:", k)


def design():
    bb = BigBuild(seed=3220, y_min=-14, y_max=70)
    tracker = P.PropTracker(3220)
    audit = []
    rng = np.random.default_rng(3220)
    terrain(bb)
    taken = [franky_house(bb, tracker, audit), (DOCK[0] - 6, 0, DOCK[2] + 16, QUAY_Z + 12), (0, 0, N, QUAY_Z + 4)]
    dock(bb, rng)
    yard(bb, rng, taken)
    houses(bb, tracker, audit, rng, taken)
    mask = junk(bb, rng, taken)
    scenery(bb, rng, taken, mask)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 3290, density=0.15, kinds=NT.PLANTS_MEADOW, flowers=NT.FLOWERS,
              mask=lambda X, Z: land(X, Z) & ~streets(X, Z) & ~canal(X, Z) & (np.asarray(Z) > 126))
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
    x1, z1, x2, z2 = HOUSE
    b.chest(x2 - 3, GY + 1, z2 - 3, "medium", "west")
    b.chest(x2 - 12, GY + 2 * FH + 1, (z1 + z2) // 2 + 1, "galley", "east")
    b.npc(x1 + 22, GY + 1, (z1 + z2) // 2, "franky", False)
    b.guards("pirate", ((x1 + 6, z1 - 4), (x1 + 40, z1 - 4), (79, z2 + 6), (DOCK[0] - 4, QUAY_Z + 4)))
    return b, 0
