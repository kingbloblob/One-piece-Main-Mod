"""Thriller Bark, Gecko Moria's island-sized ghost ship, redesigned with the Minecraft Builder skill
(dossier: mcb/dossiers/thriller_bark.md).

A colossal dark hull (gun ports, lit stern gallery, a hold deck of storerooms and zombie cells) carrying a haunted
island inside a crenellated wall. From the bow: the great bow gate with its two spired towers, the misty gloom
forest with its twisted trees and lanterns, the graveyard (tombstones, crosses, open graves, a mausoleum with crypts)
and Absalom's chapel, Hogback's mansion (lab, operating room, freezer, bedrooms) and the great mast with tattered
sails and Moria's bat-winged flag; at the stern Moria's castle: four spired towers, the giant throne hall, Perona's
pink room, the dining hall and rooms on four floors. ~224 x 112, mast ~124. Water surface = y 0, bow points +x. (v2)

v3 (2026-10-30, audit: "the deck is a carpet of purple trees; the show has Hogback's mansion and Oars' freezer as
clear centres"): Hogback's mansion is now a big gothic house on its own walled hill in the middle of the deck (four
storeys, a central clock tower, corner turrets, a grand stair up the terrace), and Oars' freezer is a frosted hall
between the forest and the gate with the giant's body laid out on an ice slab inside under frost-lit windows. The
gloom forest is cut back to scattered groves with open lawns and lanterns between them."""
import math
import numpy as np
from mcb.kit import (BigBuild, P, AIR, seed_of, st, wing_floor, furnish, lamp_post, table, tier, cornice,
                     stair_core, set_if_air, glyph)
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "thriller_bark"
TITLE = "Thriller Bark"
WATER_Y = 0
CUTS = [6, 17, 30]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="none")

HULL = "minecraft:dark_oak_planks"
HULL2 = "minecraft:mangrove_planks"
TRIM = "minecraft:stripped_dark_oak_log"
GLOOM_LOG = "onepiece:gloom_log[axis=y]"
GLOOM_LEAF = "onepiece:gloom_leaves[distance=7,persistent=true,waterlogged=false]"
CASTLE = ["minecraft:deepslate_bricks", "minecraft:cracked_deepslate_bricks", "minecraft:polished_blackstone_bricks"]
CASTLE_W = [0.6, 0.2, 0.2]
STONE = "minecraft:deepslate_bricks"
STONE_ST = "minecraft:deepslate_brick_stairs"
STONE_W = "minecraft:deepslate_brick_wall"
ROOF = "minecraft:deepslate_tiles"
ROOF_ST = "minecraft:deepslate_tile_stairs"
SPIRE = "minecraft:purple_terracotta"
GLASS = "minecraft:purple_stained_glass_pane"
GRASS = "onepiece:gloom_grass"
INNER = "minecraft:dark_oak_planks"

L0, L1 = 4, 219          # stern / bow tip x
CZ, NZ = 56, 112
HALF = 50
KEEL, DECK = -14, 12
WALL_TOP = DECK + 10
MAST = (100, CZ)
CASTLE_BOX = (12, 22, 60, 90)              # x1, z1, x2, z2
MANSION = (62, 64, 100, 98)
HILL = 6                                    # the mansion's terrace stands this far above the deck soil
FREEZER = (146, 66, 182, 98)
CHAPEL = (112, 10, 134, 30)
GATE_X = 196

FLAG = [  # Moria's Jolly Roger: white skull crowned with two purple bat wings, flanked by pale flames
    ".PP...................PP.",
    ".PPPP...............PPPP.",
    "..PPPPPP.........PPPPPP..",
    "..PPPPPPPP.WWW.PPPPPPPP..",
    "...PP.PPPWWWWWWWPPP.PP...",
    "...P...PWWWWWWWWWP...P...",
    "..F....WW..WWW..WW....F..",
    ".FF....WW..WWW..WW....FF.",
    ".FFF...WWWWW.WWWWW...FFF.",
    "FFFF....WWWWWWWWW....FFFF",
    "FFFF.....W.W.W.W.....FFFF",
    ".FF......WWWWWWW......FF.",
]


def hw(X):
    """Half-width of the hull at deck level along x (array friendly)."""
    t = (np.asarray(X, dtype=float) - L0) / (L1 - L0)
    w = np.where(t < 0.08, HALF * (0.82 + 0.18 * t / 0.08), HALF)
    bow = np.clip((t - 0.62) / 0.38, 0, 1)
    w = np.where(t > 0.62, HALF * np.sqrt(np.clip(1 - bow ** 2, 0, 1)), w)
    return np.where((t < 0) | (t > 1), -1, w)


def width_at(X, y):
    k = 0.55 + 0.45 * np.clip((y - KEEL) / (DECK - KEEL), 0, 1)
    return hw(X) * k


def on_deck(x, z, pad=0):
    return abs(z - CZ) <= float(hw(x)) - pad


# ---------------------------------------------------------------- hull, hold, deck, island wall
def hull(bb, tracker, audit):
    for y in range(KEEL, DECK + 1):
        inside = lambda X, yy, Z, y=y: np.abs(Z - CZ) <= width_at(X, y)
        shell = lambda X, yy, Z, y=y: (np.abs(Z - CZ) <= width_at(X, y)) & \
            ((np.abs(Z - CZ) > width_at(X, y) - 2.2) | (X <= L0 + 1) | (width_at(X + 2, y) < np.abs(Z - CZ)))
        mat = HULL2 if y in (DECK - 1, 0) else HULL
        if y < 0:
            bb.fill_where(L0 - 1, y, 0, L1 + 1, y, NZ - 1, inside, HULL)        # solid below the waterline
        else:
            bb.fill_where(L0 - 1, y, 0, L1 + 1, y, NZ - 1, shell, mat)
    bb.fill_where(L0, 0, 0, L1, 0, NZ - 1, lambda X, y, Z: np.abs(Z - CZ) <= width_at(X, 0), "minecraft:spruce_planks")
    bb.fill_where(L0, DECK, 0, L1, DECK, NZ - 1, lambda X, y, Z: np.abs(Z - CZ) <= width_at(X, DECK), HULL)
    # gun ports and the trim strake
    for x in range(L0 + 8, L1 - 20, 6):
        w = float(width_at(x, 5))
        for s in (-1, 1):
            z = round(CZ + s * w)
            bb.fill(x, 5, z, x + 1, 6, z, "minecraft:black_concrete")
            bb.set(x, 4, z + s, st("minecraft:dark_oak_stairs", "north" if s > 0 else "south", "top"))
    bb.fill_where(L0 - 1, 9, 0, L1 + 1, 9, NZ - 1,
                  lambda X, y, Z: np.abs(np.abs(Z - CZ) - width_at(X, 9)) < 1.0, f"{TRIM}[axis=x]")
    # the stern gallery: lit windows across the transom
    for z in range(CZ - 36, CZ + 37, 4):
        bb.fill(L0, 3, z, L0, 7, z + 1, "minecraft:yellow_stained_glass")
    # the hold: storerooms, the zombie cells, the hull workshop
    wing_floor(bb, L0 + 70, CZ - 34, L1 - 50, CZ + 34, 1, 9, INNER, seed_of("tbhold"), tracker,
               ["storage", "workshop", "storage", "bedroom"], corridor="x", cw=4, audit=audit, max_room=12,
               wood="dark_oak", carpet=(None, None))
    for x in range(L0 + 74, L1 - 54, 8):
        bb.fill(x, 1, CZ + 3, x, 3, CZ + 3, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]")
    # the hatch down from the deck, with a ladder
    bb.fill(L0 + 72, 1, CZ - 1, L0 + 72, DECK + 2, CZ - 1, "minecraft:ladder[facing=east]")
    bb.fill(L0 + 72, DECK, CZ - 1, L0 + 72, DECK + 4, CZ - 1, "minecraft:ladder[facing=east]")


def island_ground(bb, rng):
    """Soil on the deck: gloom grass with gentle humps, a stone path from the gate to the castle."""
    X, Z = np.meshgrid(np.arange(L0 - 1, L1 + 2), np.arange(NZ), indexing="ij")
    hump = 1.5 + 1.2 * np.sin(X * 0.09) * np.cos(Z * 0.11) + 0.8 * np.sin(X * 0.23 + Z * 0.05)
    for k in range(1, 4):
        bb.fill_where(L0 - 1, DECK + k, 0, L1 + 1, DECK + k, NZ - 1,
                      lambda XX, y, ZZ, k=k: (np.abs(ZZ - CZ) <= hw(XX) - 2) & (hump[XX - L0 + 1, ZZ] >= k), "minecraft:dirt")
    for k in range(0, 4):
        bb.fill_where(L0 - 1, DECK + k, 0, L1 + 1, DECK + k, NZ - 1,
                      lambda XX, y, ZZ, k=k: (np.abs(ZZ - CZ) <= hw(XX) - 2) & (np.floor(hump[XX - L0 + 1, ZZ]) == k), GRASS)
    # the path: flat cobbles from the gate to the castle doors
    bb.fill(CASTLE_BOX[2], DECK + 1, CZ - 3, GATE_X, DECK + 4, CZ + 3, AIR)
    bb.fill(CASTLE_BOX[2], DECK, CZ - 3, GATE_X, DECK, CZ + 3, "minecraft:mossy_cobblestone")
    bb.fill_where(CASTLE_BOX[2], DECK, CZ - 3, GATE_X, DECK, CZ + 3, lambda XX, y, ZZ: (XX + ZZ) % 3 == 0, "minecraft:cobblestone")


def island_wall(bb):
    """A crenellated wall on the deck edge all round the island, with soul lanterns on posts."""
    rim = lambda X, y, Z: (np.abs(Z - CZ) <= hw(X)) & (np.abs(Z - CZ) > hw(X) - 3)
    bb.fill_where(L0 - 1, DECK + 1, 0, L1 + 1, WALL_TOP, NZ - 1, rim, STONE)
    bb.fill_where(L0 - 1, WALL_TOP + 1, 0, L1 + 1, WALL_TOP + 1, NZ - 1,
                  lambda X, y, Z: rim(X, y, Z) & ((X + Z) % 2 == 0) & (np.abs(Z - CZ) > hw(X) - 1.2), STONE)
    bb.fill_where(L0 - 1, WALL_TOP, 0, L1 + 1, WALL_TOP, NZ - 1, rim, "minecraft:polished_blackstone_bricks")
    for x in range(L0 + 6, L1 - 6, 12):
        for s in (-1, 1):
            z = round(CZ + s * (float(hw(x)) - 2))
            bb.set(x, WALL_TOP + 1, z, "minecraft:soul_lantern[hanging=false]")


# ---------------------------------------------------------------- bow gate, forest, graveyard, chapel
def bow_gate(bb):
    x = GATE_X
    w = int(float(hw(x))) - 2
    bb.fill(x, DECK + 1, CZ - w, x + 6, DECK + 28, CZ + w, STONE)
    bb.mix(x, DECK + 1, CZ - w, x + 6, DECK + 28, CZ + w, CASTLE, CASTLE_W)
    P.arched_opening(bb, "z", CZ, DECK + 1, x, 11, 18, depth=7, trim="minecraft:polished_blackstone_bricks")
    cornice(bb, x, CZ - w, x + 6, CZ + w, DECK + 28, STONE_ST, parapet=STONE, merlons=STONE)
    for z in range(CZ - 4, CZ + 5, 2):
        bb.fill(x + 7, DECK + 14, z, x + 7, DECK + 18, z, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
    for s in (-1, 1):
        tz = CZ + s * (w - 2)
        bb.cylinder(x + 3, DECK + 1, tz, 5, DECK + 40, STONE)
        bb.cylinder(x + 3, DECK + 2, tz, 4, DECK + 39, AIR)
        P.square_spiral_stair(bb, x + 1, DECK + 1, tz - 2, 5, DECK + 40, STONE_ST, core=STONE)
        bb.cylinder(x + 3, DECK + 40, tz, 6, DECK + 40, ROOF)
        P.cone_roof(bb, x + 3, DECK + 41, tz, 5, 16, SPIRE, hollow=False)
        bb.fill(x + 3, DECK + 57, tz, x + 3, DECK + 59, tz, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
        for y in range(DECK + 8, DECK + 36, 7):
            bb.set(x + 8, y, tz, GLASS); bb.set(x - 2, y, tz, GLASS)
    # the doors themselves, standing open
    for s in (-1, 1):
        bb.fill(x - 4, DECK + 1, CZ + s * 6, x - 1, DECK + 14, CZ + s * 6, "minecraft:dark_oak_planks")
        bb.fill(x - 4, DECK + 5, CZ + s * 6, x - 1, DECK + 5, CZ + s * 6, "minecraft:iron_block")
    # bow rail and the crow figure on the stem
    bb.fill(L1 - 6, DECK + 1, CZ - 1, L1, DECK + 5, CZ + 1, STONE)


def gloom_tree(bb, x, y, z, h, rng):
    """A twisted dead-looking gloom tree: bent trunk, crooked branches, sparse dark leaves, a cobweb or two."""
    px, pz = x, z
    for k in range(h):
        if k > 2 and rng.random() < 0.35:
            px += int(rng.integers(-1, 2)); pz += int(rng.integers(-1, 2))
        bb.set(px, y + k, pz, GLOOM_LOG)
    top = y + h
    for _ in range(int(rng.integers(3, 6))):
        dx, dz = int(rng.integers(-1, 2)), int(rng.integers(-1, 2))
        if dx == dz == 0:
            continue
        bx, bz, by = px, pz, top - int(rng.integers(1, 4))
        for k in range(int(rng.integers(2, 5))):
            bx += dx; bz += dz; by += int(rng.random() < 0.5)
            bb.set(bx, by, bz, "onepiece:gloom_log[axis=x]" if dx else "onepiece:gloom_log[axis=z]")
        for (ax, ay, az) in ((0, 1, 0), (1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)):
            if rng.random() < 0.6:
                set_if_air(bb, bx + ax, by + ay, bz + az, GLOOM_LEAF)
        if rng.random() < 0.3:
            set_if_air(bb, bx, by - 1, bz, "minecraft:cobweb")


def forest(bb, rng):
    x1, x2 = 140, GATE_X - 3
    fx1, fz1, fx2, fz2 = FREEZER
    for _ in range(260):
        x = int(rng.integers(x1, x2)); z = int(rng.integers(CZ - 46, CZ + 46))
        if abs(z - CZ) < 6 or not on_deck(x, z, 6):
            continue
        if fx1 - 4 <= x <= fx2 + 4 and fz1 - 6 <= z <= fz2 + 4:
            continue
        if float(np.asarray(NT.noise(np.array([x]), np.array([z]), 667, 14))[0]) < 0.5:   # groves, with lawns between
            continue
        reg = bb.get_region(x - 1, DECK + 5, z - 1, x + 1, DECK + 10, z + 1)
        if (reg > 1).any():
            continue
        g = DECK + 4
        while g > DECK and bb.get_region(x, g, z, x, g, z)[0, 0, 0] in (0, 1):
            g -= 1
        gloom_tree(bb, x, g + 1, z, int(rng.integers(9, 17)), rng)
    for _ in range(80):                     # pumpkins, mushrooms, mossy rocks
        x = int(rng.integers(x1, x2)); z = int(rng.integers(CZ - 44, CZ + 44))
        if abs(z - CZ) < 5 or not on_deck(x, z, 5):
            continue
        g = DECK + 4
        while g > DECK and bb.get_region(x, g, z, x, g, z)[0, 0, 0] in (0, 1):
            g -= 1
        pick = ["minecraft:carved_pumpkin[facing=south]", "minecraft:jack_o_lantern[facing=west]", "minecraft:red_mushroom",
                "minecraft:mossy_cobblestone", "minecraft:brown_mushroom", "minecraft:pumpkin"][int(rng.integers(6))]
        set_if_air(bb, x, g + 1, z, pick)
    for x in range(x1, x2, 9):              # soul lanterns along the path
        for s in (-1, 1):
            bb.fill(x, DECK + 1, CZ + s * 4, x, DECK + 3, CZ + s * 4, "minecraft:dark_oak_fence")
            bb.set(x, DECK + 4, CZ + s * 4, "minecraft:soul_lantern[hanging=false]")


def graveyard(bb, rng, tracker, audit):
    x1, x2 = 104, 138
    for x in range(x1, x2, 3):
        for z in range(CZ - 44, CZ + 45, 3):
            if abs(z - CZ) < 6 or not on_deck(x, z, 5) or (CHAPEL[0] - 2 <= x <= CHAPEL[2] + 2 and z <= CHAPEL[3] + 2):
                continue
            g = DECK + 4
            while g > DECK and bb.get_region(x, g, z, x, g, z)[0, 0, 0] in (0, 1):
                g -= 1
            r = rng.random()
            if r < 0.4:
                bb.set(x, g + 1, z, "minecraft:cobblestone_wall"); bb.set(x, g + 2, z, "minecraft:stone_brick_slab[type=bottom]")
            elif r < 0.65:
                bb.fill(x, g + 1, z, x, g + 3, z, "minecraft:dark_oak_fence")
                bb.set(x - 1, g + 2, z, "minecraft:dark_oak_fence"); bb.set(x + 1, g + 2, z, "minecraft:dark_oak_fence")
            elif r < 0.8:
                bb.fill(x, g, z, x, g, z + 1, "minecraft:coarse_dirt")       # an open grave
                bb.fill(x, g, z, x, g, z, AIR)
            elif r < 0.9:
                bb.set(x, g + 1, z, "minecraft:mossy_stone_brick_wall")
                bb.set(x, g + 2, z, "minecraft:candle[candles=2,lit=true,waterlogged=false]")
    # the mausoleum with crypts below
    mx1, mz1, mx2, mz2 = 118, 70, 134, 86
    top = tier(bb, mx1, mz1, mx2, mz2, DECK + 3, 1, 9, CASTLE, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]",
               STONE_ST, pilaster="minecraft:polished_blackstone_bricks", plate="minecraft:polished_blackstone",
               weights=CASTLE_W, every=4, pil_every=4)
    P.gable_roof(bb, mx1 - 1, mz1 - 1, mx2 + 1, mz2 + 1, top + 1, ROOF_ST, gable_fill=STONE, ridge_axis="x")
    bb.fill(mx1 + 6, DECK + 4, mz1, mx1 + 10, DECK + 8, mz1, AIR)
    for z in range(mz1 + 3, mz2 - 1, 4):
        for x in (mx1 + 2, mx2 - 4):
            bb.fill(x, DECK + 4, z, x + 2, DECK + 4, z + 1, "minecraft:polished_blackstone")
            bb.fill(x, DECK + 5, z, x + 2, DECK + 5, z + 1, "minecraft:polished_blackstone_slab[type=bottom]")
    bb.set((mx1 + mx2) // 2, DECK + 11, (mz1 + mz2) // 2, "minecraft:soul_lantern[hanging=true]")


def chapel(bb, tracker, audit):
    """Absalom's wedding chapel: a gothic nave with a bell spire, pews, an altar, purple glass."""
    x1, z1, x2, z2 = CHAPEL
    base = DECK + 3
    top = tier(bb, x1, z1, x2, z2, base, 1, 12, CASTLE, GLASS, STONE_ST, pilaster="minecraft:polished_blackstone_bricks",
               plate="minecraft:polished_blackstone", weights=CASTLE_W, every=3, pil_every=4, win_h=6)
    P.gable_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, top + 1, ROOF_ST, gable_fill=STONE, ridge_axis="x")
    for z in range(z1 + 2, z2 - 1, 2):                          # pews facing the altar (west)
        bb.fill(x1 + 5, base + 1, z, x2 - 3, base + 1, z, AIR)
    for x in range(x1 + 6, x2 - 2, 2):
        for z in list(range(z1 + 2, (z1 + z2) // 2 - 1)) + list(range((z1 + z2) // 2 + 2, z2 - 1)):
            bb.set(x, base + 1, z, "minecraft:dark_oak_stairs[facing=east,half=bottom]")
    bb.fill(x1 + 1, base + 1, z1 + 4, x1 + 3, base + 1, z2 - 4, "minecraft:purple_wool")
    bb.set(x1 + 2, base + 2, (z1 + z2) // 2, "minecraft:candle[candles=4,lit=true,waterlogged=false]")
    bb.fill(x1 + 4, base, z1 + 1, x2 - 1, base, z2 - 1, "minecraft:polished_blackstone")
    bb.fill(x1 + 4, base + 1, (z1 + z2) // 2, x2 - 1, base + 1, (z1 + z2) // 2, "minecraft:purple_carpet")
    for x in range(x1 + 4, x2, 4):
        bb.set(x, top - 1, (z1 + z2) // 2, "minecraft:soul_lantern[hanging=true]")
    bb.fill(x2, base + 1, (z1 + z2) // 2 - 1, x2, base + 5, (z1 + z2) // 2 + 1, AIR)
    # the spire over the door end
    sx, sz = x2 - 3, (z1 + z2) // 2
    bb.fill(sx - 3, top, sz - 3, sx + 3, top + 14, sz + 3, STONE)
    bb.fill(sx - 2, top + 1, sz - 2, sx + 2, top + 13, sz + 2, AIR)
    for (dx, dz) in ((3, 0), (-3, 0), (0, 3), (0, -3)):
        bb.fill(sx + dx, top + 9, sz + dz, sx + dx, top + 12, sz + dz, AIR)
    bb.set(sx, top + 12, sz, "minecraft:bell[attachment=ceiling,facing=north,powered=false]")
    P.cone_roof(bb, sx, top + 15, sz, 4, 14, SPIRE, hollow=False)


def mansion(bb, tracker, audit):
    """Hogback's mansion on its own terrace: four gothic storeys, purple-glass windows, a central clock tower and four
    corner turrets; the lab, the operating room and a cold room on the ground floor, bedrooms and a library above."""
    x1, z1, x2, z2 = MANSION
    base = DECK + 3 + HILL
    # the terrace: a stepped stone hill with a balustrade, a grand stair down to the path (north side, -z)
    for k in range(HILL + 1):
        o = 6 - k // 2
        bb.fill(x1 - o, DECK + 1 + k, z1 - o, x2 + o, DECK + 1 + k, z2 + o, STONE if k < HILL else "minecraft:polished_deepslate")
    bb.fill(x1 - 3, base + 1, z1 - 3, x2 + 3, base + 1, z1 - 3, STONE_W)
    bb.fill(x1 - 3, base + 1, z2 + 3, x2 + 3, base + 1, z2 + 3, STONE_W)
    bb.fill(x1 - 3, base + 1, z1 - 3, x1 - 3, base + 1, z2 + 3, STONE_W)
    bb.fill(x2 + 3, base + 1, z1 - 3, x2 + 3, base + 1, z2 + 3, STONE_W)
    mx = (x1 + x2) // 2
    for i in range(HILL + 4):
        z = z1 - 4 - i
        y = base - i
        bb.fill(mx - 3, y, z, mx + 3, y, z, st(STONE_ST, "south"))
        bb.fill(mx - 3, DECK + 1, z, mx + 3, y - 1, z, STONE)
        bb.fill(mx - 3, y + 1, z, mx + 3, y + 4, z, AIR)
    for dx in (-4, 4):
        bb.fill(mx + dx, base + 1, z1 - 3, mx + dx, base + 3, z1 - 3, "minecraft:polished_blackstone_bricks")
        bb.set(mx + dx, base + 4, z1 - 3, "minecraft:soul_lantern[hanging=false]")
    bb.fill(mx - 3, base + 1, z1 - 3, mx + 3, base + 1, z1 - 3, AIR)
    top = tier(bb, x1, z1, x2, z2, base, 4, 7, CASTLE, GLASS, STONE_ST, pilaster="minecraft:polished_blackstone_bricks",
               band="minecraft:purple_terracotta", plate=INNER, weights=CASTLE_W, every=3, pil_every=5, win_h=3)
    cornice(bb, x1, z1, x2, z2, top - 1, STONE_ST)
    P.hip_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, top, ROOF_ST, overhang=1)
    for k in range(4):
        y = base + 7 * k + 1
        wing_floor(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, y, 6, INNER, seed_of("hog", k), tracker,
                   [["workshop", "storeroom"], ["bedroom", "library"], ["library", "living"], ["bedroom", "dining"]][k],
                   corridor="x", cw=3, audit=audit, max_room=10, wood="dark_oak", carpet=(None, "minecraft:purple_carpet"))
    # the lab, the operating tables and the cold room (ground floor, north side)
    for x in range(x1 + 3, x2 - 2, 4):
        bb.set(x, base + 1, z1 + 2, "minecraft:white_concrete")
        bb.set(x + 1, base + 1, z1 + 2, "minecraft:white_concrete")
        bb.set(x, base + 1, z1 + 4, "minecraft:cauldron")
    bb.set(x1 + 2, base + 2, z1 + 2, "minecraft:brewing_stand[has_bottle_0=true,has_bottle_1=false,has_bottle_2=true]")
    bb.fill(x2 - 4, base + 1, z1 + 1, x2 - 1, base + 3, z1 + 5, "minecraft:packed_ice")
    bb.fill(x2 - 3, base + 1, z1 + 2, x2 - 2, base + 2, z1 + 4, AIR)
    bb.fill(x1 + 1, base + 1, z2 - 1, x1 + 1, base + 21, z2 - 1, "minecraft:ladder[facing=north]")
    # four corner turrets with purple spires, a central clock tower over the front
    for (tx, tz) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        bb.cylinder(tx, base, tz, 3, top + 6, STONE)
        bb.cylinder(tx, base + 1, tz, 2, top + 5, AIR)
        for y in range(base + 4, top + 5, 6):
            bb.set(tx, y, tz + (3 if tz == z2 else -3), GLASS)
        P.cone_roof(bb, tx, top + 7, tz, 4, 11, SPIRE, hollow=False)
    cz_ = z1 + 4
    bb.fill(mx - 4, base, cz_ - 4, mx + 4, top + 14, cz_ + 4, STONE)
    bb.fill(mx - 3, base + 1, cz_ - 3, mx + 3, top + 13, cz_ + 3, AIR)
    for y in (top + 4, top + 10):
        bb.fill(mx - 4, y, cz_ - 4, mx + 4, y, cz_ + 4, "minecraft:purple_terracotta")
    for (fx, fz, f) in ((mx, cz_ - 5, "north"), (mx, cz_ + 5, "south")):    # clock faces
        bb.fill(fx - 2, top + 6, fz, fx + 2, top + 9, fz, "minecraft:white_concrete")
        bb.set(fx, top + 8, fz, "minecraft:black_concrete")
        bb.set(fx, top + 7, fz, "minecraft:black_concrete")
        bb.set(fx + 1, top + 8, fz, "minecraft:black_concrete")
    P.cone_roof(bb, mx, top + 15, cz_, 6, 16, SPIRE, hollow=False)
    bb.fill(mx - 1, base + 1, z1, mx + 1, base + 4, z1, AIR)
    bb.fill(mx - 1, base + 1, cz_ - 4, mx + 1, base + 4, cz_ - 4, AIR)


def freezer(bb, rng):
    """Oars' freezer: a frosted stone hall with iron doors; inside the giant lies on an ice slab under blue light."""
    x1, z1, x2, z2 = FREEZER
    base = DECK + 1
    bb.fill(x1 - 2, DECK + 1, z1 - 2, x2 + 2, DECK + 4, z2 + 2, AIR)
    bb.fill(x1 - 2, DECK, z1 - 2, x2 + 2, DECK, z2 + 2, "minecraft:polished_deepslate")
    H = 16
    bb.fill(x1, base, z1, x2, base + H, z2, "minecraft:light_gray_concrete")
    bb.mix(x1, base, z1, x2, base + H, z2, ["minecraft:light_gray_concrete", "minecraft:packed_ice", "minecraft:iron_block"], [0.6, 0.28, 0.12])
    bb.fill(x1 + 1, base + 1, z1 + 1, x2 - 1, base + H - 1, z2 - 1, AIR)
    bb.fill(x1 + 1, base, z1 + 1, x2 - 1, base, z2 - 1, "minecraft:blue_ice")
    for x in range(x1, x2 + 1, 4):                                   # buttress ribs
        for z in (z1, z2):
            bb.fill(x, base, z, x, base + H, z, "minecraft:polished_blackstone_bricks")
    for z in range(z1, z2 + 1, 4):
        for x in (x1, x2):
            bb.fill(x, base, z, x, base + H, z, "minecraft:polished_blackstone_bricks")
    for x in range(x1 + 2, x2 - 1, 4):                               # frosted high windows
        for z in (z1, z2):
            bb.fill(x, base + 8, z, x + 1, base + 12, z, "minecraft:light_blue_stained_glass")
    # barrel-vault roof of packed ice and deepslate tiles
    W = (z2 - z1) / 2
    zc = (z1 + z2) / 2
    bb.fill_where(x1 - 1, base + H, z1 - 1, x2 + 1, base + H + int(W * 0.6) + 1, z2 + 1,
                  lambda X, Y, Z: (Y - base - H) <= (W + 1 - np.abs(Z - zc)) * 0.6, ROOF)
    bb.fill_where(x1 + 1, base + H, z1 + 1, x2 - 1, base + H + int(W * 0.6), z2 - 1,
                  lambda X, Y, Z: (Y - base - H) <= (W - 1 - np.abs(Z - zc)) * 0.6 - 1, AIR)
    # the iron doors facing the path (north side), a frost sign
    mx = (x1 + x2) // 2
    bb.fill(mx - 3, base + 1, z1, mx + 3, base + 7, z1, AIR)
    bb.fill(mx - 4, base + 8, z1 - 1, mx + 4, base + 8, z1 - 1, "minecraft:iron_block")
    for dx in (-4, 4):
        bb.fill(mx + dx, base, z1 - 1, mx + dx, base + 8, z1 - 1, "minecraft:iron_block")
    for z in range(CZ + 4, z1):
        bb.fill(mx - 2, DECK, z, mx + 2, DECK, z, "minecraft:mossy_cobblestone")
        bb.fill(mx - 2, DECK + 1, z, mx + 2, DECK + 4, z, AIR)
    # Oars: a giant lying face up on an ice slab, head to the west
    sy = base + 3
    bx0, bx1 = x1 + 4, x2 - 4
    bb.fill(bx0 - 1, base + 1, int(zc) - 6, bx1 + 1, sy - 1, int(zc) + 6, "minecraft:packed_ice")
    skin, cloth = "minecraft:light_blue_terracotta", "minecraft:brown_wool"
    L = bx1 - bx0
    hx = bx0 + 3
    bb.fill_where(hx - 3, sy, int(zc) - 3, hx + 3, sy + 6, int(zc) + 3,
                  lambda X, Y, Z: ((X - hx) / 3.2) ** 2 + ((Y - sy - 2.5) / 3.0) ** 2 + ((Z - zc) / 3.2) ** 2 <= 1, skin)
    bb.fill(hx - 1, sy + 5, int(zc) - 1, hx + 1, sy + 5, int(zc) + 1, "minecraft:black_wool")   # stitches / hair
    tx0, tx1 = hx + 4, hx + 4 + L // 3
    bb.fill_where(tx0, sy, int(zc) - 6, tx1, sy + 4, int(zc) + 6,
                  lambda X, Y, Z: ((Y - sy - 1.5) / 3.0) ** 2 + ((Z - zc) / 5.6) ** 2 <= 1, cloth)
    for s in (-1, 1):                                                  # arms along the sides, legs
        bb.fill(tx0, sy, int(zc) + s * 7, tx1, sy + 1, int(zc) + s * 7, skin)
        bb.fill(tx1 + 1, sy, int(zc) + s * 3 - 1, bx1, sy + 2, int(zc) + s * 3 + 1, skin if s < 0 else "minecraft:gray_wool")
    bb.fill(tx0 + 2, sy + 4, int(zc) - 1, tx0 + 4, sy + 5, int(zc) + 1, "minecraft:red_wool")   # the star-shaped stitched chest
    for x in range(x1 + 3, x2 - 2, 5):
        bb.set(x, base + H - 1, int(zc), "minecraft:sea_lantern")
    return (x1 - 3, z1 - 3, x2 + 3, z2 + 3)


def barracks_and_garden(bb, rng, tracker, audit):
    """The zombie barracks (two gloomy longhouses of bunk rooms) and Perona's garden with its pink gazebo."""
    for i, (x1, z1, x2, z2) in enumerate(((66, 12, 96, 24), (66, 27, 84, 37))):
        base = DECK + 3
        bb.fill(x1 - 1, DECK + 1, z1 - 1, x2 + 1, base, z2 + 1, STONE)
        top = tier(bb, x1, z1, x2, z2, base, 2, 6, ["minecraft:dark_oak_planks", "minecraft:mangrove_planks"],
                   GLASS, "minecraft:dark_oak_stairs", pilaster=TRIM + "[axis=y]", plate=INNER, weights=[0.7, 0.3],
                   every=3, pil_every=4, win_h=2)
        P.gable_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, top + 1, ROOF_ST, gable_fill=HULL, ridge_axis="x")
        for k in range(2):
            wing_floor(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, base + 6 * k + 1, 5, INNER, seed_of("bar", i, k), tracker,
                       ["bedroom", "storage"] if k else ["kitchen", "bedroom"], corridor="x", cw=3, audit=audit,
                       max_room=9, wood="dark_oak", carpet=(None, None))
        bb.fill(x2 - 2, base + 1, (z1 + z2) // 2, x2 - 2, base + 12, (z1 + z2) // 2, "minecraft:ladder[facing=west]")
        bb.fill(x2, base + 1, (z1 + z2) // 2 - 1, x2, base + 4, (z1 + z2) // 2 + 1, AIR)
    # Perona's garden: pumpkin beds, hedges, ghost lanterns and a pink gazebo
    gx1, gz1, gx2, gz2 = 86, 27, 98, 44
    for x in range(gx1, gx2 + 1):
        for z in range(gz1, gz2 + 1):
            edge = x in (gx1, gx2) or z in (gz1, gz2)
            if edge and not (z == gz2 and abs(x - (gx1 + gx2) // 2) <= 1):
                bb.fill(x, DECK + 1, z, x, DECK + 5, z, AIR); bb.set(x, DECK, z, GRASS)
                bb.set(x, DECK + 1, z, GLOOM_LEAF)
            elif not edge:
                bb.fill(x, DECK + 1, z, x, DECK + 5, z, AIR)
                bb.set(x, DECK, z, "minecraft:farmland[moisture=7]" if (x + z) % 3 else "minecraft:moss_block")
                if (x + z) % 3 and rng.random() < 0.45:
                    bb.set(x, DECK + 1, z, "minecraft:pumpkin" if rng.random() < 0.7 else "minecraft:jack_o_lantern[facing=south]")
    cx, cz = (gx1 + gx2) // 2, (gz1 + gz2) // 2
    for (dx, dz) in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
        bb.fill(cx + dx, DECK + 1, cz + dz, cx + dx, DECK + 4, cz + dz, "minecraft:cherry_fence")
    bb.fill(cx - 2, DECK, cz - 2, cx + 2, DECK, cz + 2, "minecraft:pink_terracotta")
    bb.fill(cx - 1, DECK + 1, cz - 1, cx + 1, DECK + 1, cz + 1, AIR)
    bb.fill(cx - 3, DECK + 5, cz - 3, cx + 3, DECK + 5, cz + 3, "minecraft:pink_wool")
    bb.fill(cx - 2, DECK + 6, cz - 2, cx + 2, DECK + 6, cz + 2, "minecraft:pink_wool")
    bb.set(cx, DECK + 7, cz, "minecraft:pink_wool")
    bb.set(cx, DECK + 4, cz, "minecraft:soul_lantern[hanging=true]")
    bb.set(cx, DECK + 1, cz + 1, "minecraft:cherry_stairs[facing=north,half=bottom]")
    bb.set(cx - 1, DECK + 1, cz - 1, "minecraft:pink_wool")


def great_mast(bb, rng):
    mx, mz = MAST
    bb.cylinder(mx, KEEL + 2, mz, 3, DECK + 100, "minecraft:dark_oak_log[axis=y]")
    for (y0, half) in ((DECK + 34, 34), (DECK + 62, 26)):
        bb.fill(mx + 1, y0 + 22, mz - half - 2, mx + 1, y0 + 22, mz + half + 2, "minecraft:dark_oak_log[axis=z]")
        for y in range(y0, y0 + 22):
            for z in range(mz - half, mz + half + 1):
                if rng.random() < 0.86 and not (y < y0 + 4 and abs(z - mz) % 9 < 3):     # tattered
                    bb.set(mx + 2 + int(2 * math.sin((y - y0) / 22 * math.pi)), y, z,
                           "minecraft:gray_wool" if (y + z) % 11 else "minecraft:light_gray_wool")
    # crow's nest
    bb.cylinder(mx, DECK + 90, mz, 4, DECK + 90, "minecraft:dark_oak_planks")
    for a in range(0, 360, 30):
        t = math.radians(a)
        bb.set(round(mx + 4 * math.cos(t)), DECK + 91, round(mz + 4 * math.sin(t)), "minecraft:dark_oak_fence")
    bb.fill(mx - 4, DECK + 1, mz, mx - 4, DECK + 90, mz, "minecraft:ladder[facing=west]")
    # Moria's flag
    fy = DECK + 112
    bb.fill(mx, DECK + 100, mz, mx, fy, mz, "minecraft:dark_oak_fence")
    col = {".": "minecraft:black_wool", "W": "minecraft:white_wool", "P": "minecraft:purple_wool", "F": "minecraft:light_blue_wool"}
    for j, row in enumerate(FLAG):
        for i, ch in enumerate(row):
            bb.set(mx, fy - j, mz + 1 + i, col[ch])


# ---------------------------------------------------------------- Moria's castle
def castle(bb, tracker, audit):
    x1, z1, x2, z2 = CASTLE_BOX
    base = DECK + 3
    bb.fill(x1 - 3, DECK + 1, z1 - 3, x2 + 3, base, z2 + 3, "minecraft:polished_blackstone_bricks")
    bb.fill(x1 - 3, base + 1, z1 - 3, x2 + 3, base + 30, z2 + 3, AIR)
    top = tier(bb, x1, z1, x2, z2, base, 4, 7, CASTLE, GLASS, STONE_ST, pilaster="minecraft:polished_blackstone_bricks",
               band="minecraft:purple_terracotta", plate=INNER, top_plate=STONE, weights=CASTLE_W, every=3, pil_every=6,
               win_h=3)
    cornice(bb, x1, z1, x2, z2, top, STONE_ST, parapet=STONE, merlons=STONE)
    # the throne hall: three storeys tall in the middle of the castle
    hx1, hx2, hz1, hz2 = x1 + 12, x2 - 4, CZ - 12, CZ + 12
    bb.fill(hx1, base + 7, hz1, hx2, base + 14, hz2, AIR)
    bb.fill(hx1 - 1, base + 1, hz1 - 1, hx2 + 1, base + 21, hz1 - 1, STONE)
    bb.fill(hx1 - 1, base + 1, hz2 + 1, hx2 + 1, base + 21, hz2 + 1, STONE)
    bb.fill(hx1 - 1, base + 1, hz1 - 1, hx1 - 1, base + 21, hz2 + 1, STONE)
    for x in range(hx1 + 4, hx2 - 1, 6):
        for z in (hz1 + 2, hz2 - 2):
            bb.fill(x, base + 1, z, x, base + 20, z, "minecraft:polished_blackstone_bricks")
        bb.set(x, base + 19, CZ, "onepiece:chandelier[facing=north]")
    bb.fill(hx1, base, hz1, hx2, base, hz2, "minecraft:polished_blackstone")
    bb.fill(hx1 + 6, base, CZ - 2, x2 - 1, base, CZ + 2, "minecraft:purple_wool")
    # Moria's giant throne at the west end
    tx = hx1 + 1
    bb.fill(tx, base + 1, CZ - 5, tx + 3, base + 2, CZ + 5, "minecraft:polished_blackstone_bricks")
    bb.fill(tx, base + 3, CZ - 4, tx + 2, base + 3, CZ + 4, "minecraft:purple_wool")
    bb.fill(tx, base + 3, CZ - 5, tx, base + 16, CZ + 5, "minecraft:dark_oak_planks")
    bb.fill(tx, base + 4, CZ - 4, tx, base + 14, CZ + 4, "minecraft:purple_wool")
    for s in (-1, 1):
        bb.fill(tx, base + 3, CZ + s * 5, tx + 3, base + 6, CZ + s * 5, "minecraft:dark_oak_planks")
        bb.fill(tx, base + 17, CZ + s * 5, tx, base + 19, CZ + s * 5, "minecraft:gold_block")
    bb.fill(tx, base + 17, CZ - 1, tx, base + 18, CZ + 1, "minecraft:gold_block")
    for x in (tx + 5,):
        bb.set(x, base + 1, CZ - 7, "minecraft:soul_lantern[hanging=false]")
        bb.set(x, base + 1, CZ + 7, "minecraft:soul_lantern[hanging=false]")
    # the rest of the castle: rooms on four floors round the hall
    for k in range(4):
        y = base + 7 * k + 1
        for (a, b, c, d) in ((x1 + 1, z1 + 1, x2 - 1, hz1 - 2), (x1 + 1, hz2 + 2, x2 - 1, z2 - 1)):
            wing_floor(bb, a, b, c, d, y, 6, INNER, seed_of("mor", k, b), tracker,
                       [["kitchen", "storage"], ["bedroom", "living"], ["library", "bedroom"], ["bedroom", "storage"]][k],
                       corridor="x", cw=3, audit=audit, max_room=10, wood="dark_oak",
                       carpet=(None, "minecraft:purple_carpet"))
        wing_floor(bb, x1 + 1, hz1, hx1 - 2, hz2, y, 6, INNER, seed_of("morw", k), tracker,
                   ["living", "library"], corridor="z", cw=3, audit=audit, max_room=10, wood="dark_oak")
    # Perona's room: the biggest room on the second floor goes pink
    pr = (x1 + 2, hz2 + 3, x1 + 14, z2 - 2)
    y = base + 8
    bb.fill(pr[0], y - 1, pr[1], pr[2], y - 1, pr[3], "minecraft:pink_wool")
    for (x, z) in ((pr[0] + 1, pr[1] + 1), (pr[2] - 1, pr[1] + 1), (pr[0] + 3, pr[3] - 1)):
        bb.set(x, y, z, "minecraft:pink_wool"); bb.set(x, y + 1, z, "minecraft:white_wool")
    bb.set(pr[2] - 2, y, pr[3] - 2, "minecraft:pink_bed[facing=north,part=foot,occupied=false]")
    bb.set(pr[2] - 2, y, pr[3] - 3, "minecraft:pink_bed[facing=north,part=head,occupied=false]")
    # stair towers at the four corners, spires
    floors = [base + 7 * k + 1 for k in range(5)]
    for (cx, cz) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        bb.cylinder(cx, DECK + 1, cz, 6, top + 18, STONE)
        bb.cylinder(cx, base + 1, cz, 5, top + 17, AIR)
        P.square_spiral_stair(bb, cx - 3, base + 1, cz - 3, 7, top + 1, STONE_ST, core=STONE)
        for y in range(base + 6, top + 16, 6):
            for (dx, dz) in ((6, 0), (-6, 0), (0, 6), (0, -6)):
                bb.fill(cx + dx, y, cz + dz, cx + dx, y + 1, cz + dz, GLASS)
        for fy in floors:
            for (dx, dz) in ((4 if cx == x1 else -4, 0), (0, 4 if cz == z1 else -4)):
                bb.fill(cx + dx, fy, cz + dz, cx + dx + (1 if dx > 0 else -1 if dx < 0 else 0), fy + 1,
                        cz + dz + (1 if dz > 0 else -1 if dz < 0 else 0), AIR)
        bb.cylinder(cx, top + 18, cz, 7, top + 18, ROOF)
        for a in range(0, 360, 20):
            t = math.radians(a)
            bb.set(round(cx + 7 * math.cos(t)), top + 19, round(cz + 7 * math.sin(t)), STONE_W)
        P.cone_roof(bb, cx, top + 20, cz, 6, 20, SPIRE, hollow=False)
        bb.fill(cx, top + 40, cz, cx, top + 42, cz, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    # the central keep tower rising over the hall, with a pointed roof
    P.hip_roof(bb, x1 + 14, z1 + 10, x2 - 6, z2 - 10, top + 1, ROOF_ST, overhang=1)
    # castle doors facing the path (east)
    bb.fill(x2, base + 1, CZ - 3, x2, base + 9, CZ + 3, AIR)
    P.arched_opening(bb, "z", CZ, base + 1, x2, 7, 9, depth=1, trim="minecraft:polished_blackstone_bricks")
    for i in range(3):
        bb.fill(x2 + 1 + i, base - i, CZ - 4, x2 + 1 + i, base - i, CZ + 4, st(STONE_ST, "west"))
    return top, (tx + 1, base + 3)


# ---------------------------------------------------------------- assembly
def design():
    bb = BigBuild(seed=666, y_min=-18, y_max=140)
    tracker = P.PropTracker(666)
    audit = []
    rng = np.random.default_rng(666)
    hull(bb, tracker, audit)
    island_ground(bb, rng)
    island_wall(bb)
    top, (tx, ty) = castle(bb, tracker, audit)
    mansion(bb, tracker, audit)
    chapel(bb, tracker, audit)
    graveyard(bb, rng, tracker, audit)
    barracks_and_garden(bb, rng, tracker, audit)
    great_mast(bb, rng)
    bow_gate(bb)
    freezer(bb, rng)
    forest(bb, rng)
    return bb, audit, (tx, ty)


def build():
    bb, audit, (tx, ty) = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    x1, z1, x2, z2 = CASTLE_BOX
    b.chest(x1 + 16, DECK + 4, CZ - 9, "hard", "south")
    b.npc(tx, ty, CZ, "moria", True)
    return b, 0
