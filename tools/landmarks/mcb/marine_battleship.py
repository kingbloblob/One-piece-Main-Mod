"""Marine Battleship v2, redesigned with the Minecraft Builder skill: a Marine task force on patrol in open sea, the
way the Navy shows up in the anime (a big flagship with escorts sailing in a wedge, gull sails full).

Silhouette first: the show-accurate Marine Battleship template (white hull, royal-blue band, three birch masts with
"MARINE" under the gull, three-storey stern castle, the gull figurehead) leading, two Marine Warships (the smaller
two-masters) a little astern on either quarter, all bows the same way; between them a supply tender and two
longboats being rowed across, and a Marine marker buoy. Ships come from the ship kit templates
(tools/ships/*.py -> structure/ships/*.nbt), never box hulls.

Inside the flagship (from its template): captain's cabin, crew barracks, chart room and the bridge; the gun deck
with the brig; the hold with guns on catwalks and the stores. 132 x 96, y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, steady
from mcb.bridge import to_canvas
from mcb.shipstamp import stamp_ship

SID = "marine_battleship"
TITLE = "Marine Battleship"
WATER_Y = 0
CUTS = [3, 9, 15]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="none")
EDGE_REACH = 2

NX, NZ = 132, 96
FLAG = (70, 48)                 # flagship hull centre (bow +x)
ESCORTS = [(36, 20), (36, 76)]


def tender(bb, x, z):
    """A flat supply tender: a plank barge with crates, barrels and a small cabin, a blue pennant."""
    for dx in range(16):
        half = 3 if 1 <= dx <= 14 else 2
        bb.fill(x + dx, -1, z - half, x + dx, 0, z + half, "minecraft:spruce_planks")
        bb.set(x + dx, 1, z - half, "minecraft:white_concrete"); bb.set(x + dx, 1, z + half, "minecraft:white_concrete")
    bb.fill(x + 1, -2, z - 2, x + 14, -2, z + 2, "minecraft:light_gray_concrete")
    bb.fill(x + 2, 1, z - 2, x + 5, 4, z + 2, "minecraft:white_concrete")
    bb.fill(x + 3, 1, z - 1, x + 4, 3, z + 1, AIR)
    bb.fill(x + 2, 5, z - 2, x + 5, 5, z + 2, "minecraft:blue_concrete")
    bb.set(x + 5, 1, z, AIR); bb.set(x + 5, 2, z, AIR)
    for (dx, dz) in ((8, -2), (9, -2), (8, 2), (11, 1), (12, -1), (12, 2), (10, 0)):
        bb.set(x + dx, 1, z + dz, "minecraft:barrel[facing=up]" if (dx + dz) % 2 else "minecraft:chest[facing=north]")
    bb.fill(x + 13, 1, z, x + 13, 7, z, "minecraft:birch_fence")
    bb.fill(x + 13, 6, z + 1, x + 13, 7, z + 3, "minecraft:blue_wool")


def longboat(bb, x, z, axis="z"):
    for k in range(9):
        half = 1 if 1 <= k <= 7 else 0
        for s in range(-half, half + 1):
            px, pz = (x + s, z + k) if axis == "z" else (x + k, z + s)
            bb.set(px, 0, pz, "minecraft:white_concrete" if abs(s) == half else "minecraft:spruce_planks")
        if 2 <= k <= 6 and k % 2 == 0:
            px, pz = (x, z + k) if axis == "z" else (x + k, z)
            bb.set(px, 1, pz, "minecraft:spruce_slab[type=bottom]")
            for s in (-2, 2):
                ox, oz = (x + s, z + k) if axis == "z" else (x + k, z + s)
                bb.set(ox, 0, oz, "minecraft:spruce_fence")


def buoy(bb, x, z):
    bb.fill(x - 1, -1, z - 1, x + 1, 0, z + 1, "minecraft:white_concrete")
    bb.fill(x, -6, z, x, -2, z, "minecraft:iron_chain[axis=y]")
    bb.fill(x, 1, z, x, 3, z, "minecraft:blue_concrete")
    bb.set(x, 4, z, "minecraft:white_concrete"); bb.set(x, 5, z, "minecraft:redstone_lamp[lit=true]")
    bb.set(x, 6, z, "minecraft:lightning_rod")


def deck_y(bb, x, z, top=24):
    """Highest plank block in the column (the deck a guard can stand on), or None."""
    col = bb.get_region(x, -4, z, x, top, z)[0, :, 0]
    for k in range(len(col) - 1, 0, -1):
        n = bb.names[col[k]] if col[k] else ""
        if "planks" in n and col[k + 1 if k + 1 < len(col) else k] in (0, 1):
            return k - 4
    return None


def design():
    bb = BigBuild(seed=5200, y_min=-14, y_max=60)
    stamp_ship(bb, "marine_battleship", FLAG[0], FLAG[1], water_y=0, rot=0)
    for (x, z) in ESCORTS:
        stamp_ship(bb, "marine_warship", x, z, water_y=0, rot=0)
    tender(bb, 12, 44)
    longboat(bb, 56, 28, "z")
    longboat(bb, 50, 64, "x")
    buoy(bb, 118, 14)
    return bb, []


def build():
    bb, audit = design()
    b = to_canvas(bb)
    steady(b)
    b.chest(16, 1, 44, "marine", "north")
    spots = [(FLAG[0] - 4, FLAG[1] - 3, "marine"), (FLAG[0] + 4, FLAG[1] + 3, "marine_rifle"), (FLAG[0] + 10, FLAG[1], "elite_marine"),
             (FLAG[0] - 14, FLAG[1], "vice_admiral")] + [(x + dx, z, "marine") for (x, z) in ESCORTS for dx in (-4, 6)]
    for (x, z, kit) in spots:
        y = deck_y(bb, x, z)
        if y is not None:
            b.guard(x, y + 1, z, kit)
    return b, 0
