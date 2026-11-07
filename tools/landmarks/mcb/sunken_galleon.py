"""Sunken Treasure Galleon v2, redesigned with the Minecraft Builder skill: a great treasure galleon lying on the sea
floor (like the Flying Pirates' wreck Luffy's crew dive to in Jaya, ep 145-146: a three-master broken apart,
listing, masts snapped, sails rotted, the treasure spilling out).

Silhouette first: the hull broken in two at the mainmast, the stern half heeled over hard on its side with its
two-tier stern castle and gold-framed windows, the bow half a little apart, turned and sunk nose-down in the sand
with the gold figurehead; one mast still standing with rags of sail, the snapped masts lying across the sand.

Around it: the torn hold spilling chests, barrels, gold and cannons across the sand, a debris trail, a ring of sea
lanterns, coral and sponges grown over the timbers, kelp forests and seagrass, sea-floor dunes and rocks, two
Fish-Men picking over it. Captain's cabin (stern castle) and the hold keep the treasure chests.
120 x 84, sea floor y 0; everything inside is flooded. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, steady
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.hulls import galleon, transfer, tatter, air_to_water

SID = "sunken_galleon"
TITLE = "Sunken Treasure Galleon"
CUTS = [3, 8, 14]
TILER = dict(heightmap="OCEAN_FLOOR_WG", terrain="none")
EDGE_REACH = 2

NX, NZ = 120, 84
_BED = NT.outline(60, 42, 50, 5301, wobble=0.12)
SAND = [("minecraft:sand", 0.55), ("minecraft:gravel", 0.15), ("minecraft:clay", 0.08), ("minecraft:suspicious_sand", 0.02),
        ("minecraft:sandstone", 0.08), ("minecraft:sand", 0.08), ("minecraft:mud", 0.04)]
L = 48


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    h = NT.fbm(X, Z, 5302, 16) * 4 - 1
    return np.round(h)


def hy(x, z):
    return int(_height(np.array(float(x)), np.array(float(z))))


def onbed(X, Z):
    return _BED(np.asarray(X, float), np.asarray(Z, float)) > 0


def seabed(bb):
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, _height, SAND, 5303, mask=onbed, under="minecraft:sand", core="minecraft:sandstone", base=-6)
    rng = np.random.default_rng(5304)
    for _ in range(12):
        x, z = int(rng.integers(6, NX - 6)), int(rng.integers(6, NZ - 6))
        if _BED(np.array(float(x)), np.array(float(z))) > 6 and not (30 < x < 96 and 22 < z < 62):
            NT.boulder(bb, x, hy(x, z), z, rng.uniform(1.8, 3.5), rng,
                       blocks=("minecraft:stone", "minecraft:andesite", "minecraft:mossy_cobblestone", "minecraft:tuff"))


def wreck(bb):
    src = galleon(length=L, beam=15, depth=10, masts=3, sail="minecraft:white_wool")
    # stern half: heeled over hard to the north, sunk 3 into the sand
    stern = transfer(bb, src, -2, 22, 30, -3, 40, lean=-0.6, decay=0.08, seed=5305, drop_above=19)
    # bow half: a gap, turned a little and sunk bow-first
    bow = transfer(bb, src, 27, L + 6, 38, -4, 44, lean=-0.15, yaw=0.32, pivot=(27, 0), decay=0.1, seed=5306, drop_above=24)
    # splintered timbers at the break, planks and logs scattered
    rng = np.random.default_rng(5307)
    for _ in range(70):
        x, z = 52 + int(rng.integers(-6, 9)), 40 + int(rng.integers(-10, 12))
        y = hy(x, z) + 1
        bb.set(x, y + int(rng.integers(0, 3)), z, ["minecraft:dark_oak_planks", "minecraft:stripped_dark_oak_log[axis=y]",
                                                    "minecraft:dark_oak_slab[type=bottom]", "minecraft:spruce_planks",
                                                    "minecraft:dark_oak_fence"][int(rng.integers(0, 5))])
    # snapped masts lying on the sand with rotten yards
    for (x0, z0, a, n) in ((60, 66, 0.15, 26), (40, 16, -0.25, 22)):
        for k in range(n):
            x, z = int(round(x0 + k * math.cos(a))), int(round(z0 + k * math.sin(a)))
            y = hy(x, z) + 1
            bb.set(x, y, z, "minecraft:stripped_spruce_log[axis=x]")
            if k in (8, 17):
                for d in range(-5, 6):
                    bb.set(x, y + (1 if abs(d) < 3 else 0), z + d, "minecraft:stripped_spruce_log[axis=z]")
                    if abs(d) < 5 and rng.random() < 0.5:
                        bb.set(x + 1, y, z + d, "minecraft:brown_wool" if rng.random() < 0.5 else "minecraft:white_wool")
    tatter(bb, 20, 0, 0, 110, 60, NZ - 1, 5308)
    return stern, bow


def treasure(bb):
    """The spill from the torn hold: gold piles, chests, barrels, cannons and cannonballs on the sand."""
    rng = np.random.default_rng(5309)
    cx, cz = 54, 52
    for _ in range(80):
        a, r = rng.uniform(0, 6.28), abs(rng.normal(0, 5))
        x, z = int(round(cx + r * math.cos(a) * 1.3)), int(round(cz + r * math.sin(a)))
        y = hy(x, z) + 1
        p = rng.random()
        if r < 3 and p < 0.4:
            bb.set(x, y, z, "minecraft:gold_block")
            bb.set(x, y + 1, z, "minecraft:light_weighted_pressure_plate") if rng.random() < 0.3 else None
        elif p < 0.6:
            bb.set(x, y, z, "minecraft:raw_gold_block" if rng.random() < 0.4 else "minecraft:light_weighted_pressure_plate")
        elif p < 0.75:
            bb.set(x, y, z, "minecraft:barrel[facing=up]")
        elif p < 0.85:
            bb.set(x, y, z, "onepiece:cannonball_pile")
        elif p < 0.92:
            bb.set(x, y, z, "minecraft:decorated_pot")
        else:
            bb.set(x, y, z, "minecraft:emerald_block" if rng.random() < 0.3 else "minecraft:amethyst_cluster[facing=up]")
    for (x, z, f) in ((46, 60, "east"), (66, 30, "south"), (72, 58, "north")):
        bb.set(x, hy(x, z) + 1, z, f"onepiece:cannon[facing={f}]")
    # sea lanterns marking the wreck in a ring, set into the sand
    for a in range(0, 360, 24):
        t = math.radians(a)
        x, z = int(round(60 + 46 * math.cos(t))), int(round(42 + 32 * math.sin(t)))
        if onbed(np.array(float(x)), np.array(float(z))):
            bb.set(x, hy(x, z), z, "minecraft:sea_lantern")


def life(bb):
    """Coral and sponges on the timbers' tops, kelp forests, seagrass, sea pickles."""
    rng = np.random.default_rng(5310)
    corals = ["minecraft:tube_coral_block", "minecraft:brain_coral_block", "minecraft:fire_coral_block", "minecraft:horn_coral_block",
              "minecraft:bubble_coral_block", "minecraft:wet_sponge"]
    fans = ["minecraft:tube_coral", "minecraft:brain_coral", "minecraft:fire_coral", "minecraft:horn_coral", "minecraft:bubble_coral",
            "minecraft:sea_pickle[pickles=3,waterlogged=true]", "minecraft:seagrass"]
    reg = bb.get_region(20, -6, 0, 110, 40, NZ - 1)
    names = bb.names
    wood = np.zeros(len(names), bool)
    for i, n in enumerate(names):
        wood[i] = i > 1 and ("planks" in n or "log" in n)
    sx, sy, sz = reg.shape
    top = wood[reg[:, :-1, :]] & (reg[:, 1:, :] <= 1)
    for (i, j, k) in zip(*np.nonzero(top)):
        if rng.random() < 0.09:
            x, y, z = 20 + int(i), -6 + int(j), int(k)
            if rng.random() < 0.35:
                bb.set(x, y, z, corals[int(rng.integers(0, len(corals)))])
            bb.set(x, y + 1, z, fans[int(rng.integers(0, len(fans)))])
    for _ in range(320):
        x, z = int(rng.integers(2, NX - 2)), int(rng.integers(2, NZ - 2))
        if not onbed(np.array(float(x)), np.array(float(z))):
            continue
        y = hy(x, z) + 1
        if bb.get_region(x, y, z, x, y, z)[0, 0, 0] > 1:
            continue
        if (x < 28 or x > 98 or z < 14 or z > 70) and rng.random() < 0.55:
            h = int(rng.integers(4, 16))
            bb.fill(x, y, z, x, y + h - 1, z, "minecraft:kelp_plant")
            bb.set(x, y + h, z, "minecraft:kelp")
        else:
            bb.set(x, y, z, "minecraft:seagrass" if rng.random() < 0.7 else fans[int(rng.integers(0, len(fans)))])


def design():
    bb = BigBuild(seed=5300, y_min=-10, y_max=60)
    seabed(bb)
    stern, bow = wreck(bb)
    treasure(bb)
    life(bb)
    # flood every air cell (the cabins, the hold, the gaps): seafloor builds are wholly under the sea
    air_to_water(bb, top=12)
    return bb, [], stern, bow


def build():
    bb, audit, stern, bow = design()
    b = to_canvas(bb)
    steady(b)
    # captain's cabin in the stern castle (src x 3, y 9, z 0), the hold (src x 34, y 3, z 0), the spill on the sand
    for (pt, loot, f) in (((3, 9, 0), "treasure", "east"), ((34, 3, 0), "treasure", "south")):
        x, y, z = (stern if pt[0] < 23 else bow)(*pt)
        b.chest(x, y, z, loot, f)
    b.chest(56, hy(56, 50) + 1, 50, "easy", "north")
    for (x, z) in ((62, 62), (40, 24), (80, 52)):
        y = hy(x, z) + 1                                   # first two free (air or water) cells above the sand
        col = bb.get_region(x, y, z, x, y + 30, z)[0, :, 0]
        free = [bb.names[c] in ("", "minecraft:air", "minecraft:water") for c in col]
        k = next((i for i in range(len(free) - 2) if free[i] and free[i + 1] and free[i + 2]), None)
        if k is not None:
            b.guard(x, y + k, z, "fishman")
    return b, 0
