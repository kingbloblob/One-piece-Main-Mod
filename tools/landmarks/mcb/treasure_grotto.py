"""Hidden Treasure Grotto v2, redesigned with the Minecraft Builder skill: a pirate crew's secret sea cave under an
island (pirate hoards in the show: Buggy's buried treasure, the Krieg/Arlong hoards, the treasure caves of Jaya and
Skypiea's golden belfry) where their sloop lies hidden on a dark underground lake.

Silhouette first (inside a cave, the reveal from the entrance): a tall domed cavern with a still black lake; the
crew's sloop moored at a long plank dock with lanterns on every post; across the water, at the back, a glittering
mound of gold under a shaft of light from a crack in the roof, with the captain's chests on top.

Around it: the crew's camp on the shore (tents, plank tables and barrels round a fire pit, hammocks strung between
stalagmites, a powder store), a rope bridge over a side chasm, ledges with a lookout, skeletons of the last people
who came looking, stalactites and stalagmites, glow lichen, an inlet channel from the lake out under the rock, tunnels
into the island's caves. Canvas y 0 = the shore floor (world y -6). 112 x 80. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, steady
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.hulls import galleon, transfer

SID = "treasure_grotto"
TITLE = "Hidden Treasure Grotto"
CUTS = [4, 10, 18]
TILER = dict(terrain="none", sky_y=-6)

NX, NZ = 112, 80
DOME_H = 26
BLOBS = [(56, 40, 50, 34, DOME_H), (96, 40, 14, 16, 18), (16, 46, 14, 14, 14)]
LX, LZ = 50, 44                      # lake centre
_LAKE = NT.outline(LX, LZ, 20, 4301, wobble=0.15, lobes=((2, 0.3), (3, 0.08)))
HX, HZ = 94, 40                      # the hoard


def cavern(X, y, Z, grow=0.0):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    best = np.full(np.broadcast(X, Z, y).shape, 9.0)
    for (cx, cz, rx, rz, h) in BLOBS:
        v = ((X - cx) / (rx + grow)) ** 2 + ((Z - cz) / (rz + grow)) ** 2 + (np.maximum(0, y) / (h + grow)) ** 2
        best = np.minimum(best, v)
    n = 1 + 0.12 * np.sin(X * 0.31 + Z * 0.17 + y * 0.23) * np.cos(Z * 0.27 - X * 0.11 + y * 0.19)
    return best / n


def lake(X, Z):
    return _LAKE(np.asarray(X, float), np.asarray(Z, float)) > 0


def cave(bb):
    bb.fill_where(0, -8, 0, NX - 1, DOME_H + 4, NZ - 1, lambda X, y, Z: cavern(X, y, Z, 4) < 1, "minecraft:deepslate")
    bb.fill_where(0, -8, 0, NX - 1, DOME_H + 4, NZ - 1,
                  lambda X, y, Z: (cavern(X, y, Z, 4) < 1) & (NT.noise(X + y * 3, Z, 4302, 5) > 0.65), "minecraft:tuff")
    bb.fill_where(0, 1, 0, NX - 1, DOME_H + 1, NZ - 1, lambda X, y, Z: cavern(X, y, Z) < 1, AIR)
    floor = [("minecraft:gravel", 0.25), ("minecraft:coarse_dirt", 0.2), ("minecraft:cobbled_deepslate", 0.2), ("minecraft:sand", 0.15),
             ("minecraft:tuff", 0.1), ("minecraft:moss_block", 0.1)]
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, lambda X, Z: np.zeros(np.broadcast(X, Z).shape), floor, 4303,
             mask=lambda X, Z: (cavern(X, 1, Z) < 1) & ~lake(X, Z), under="minecraft:deepslate", base=-3)
    # the lake: water down to -6 in the middle, a gravel bed, a dark inlet channel out under the east-north rock
    depth = lambda X, Z: -1 - np.clip(_LAKE(X, Z) / 2.5, 0, 5).astype(int)
    bb.fill_where(0, -7, 0, NX - 1, 0, NZ - 1, lambda X, y, Z: lake(X, Z) & (y > depth(X, Z)), "minecraft:water")
    bb.fill_where(0, -7, 0, NX - 1, 0, NZ - 1, lambda X, y, Z: lake(X, Z) & (y == depth(X, Z)), "minecraft:gravel")
    # light shaft over the hoard: a crack in the roof filled with glass-capped light (shroomlight hidden in the rock)
    bb.fill_where(HX - 3, 10, HZ - 3, HX + 3, DOME_H + 3, HZ + 3, lambda X, y, Z: (np.abs(X - HX) + np.abs(Z - HZ) <= 1 + (y > 18)) & (cavern(X, y, Z) >= 1), AIR)
    bb.fill(HX, DOME_H + 3, HZ, HX, DOME_H + 3, HZ, "minecraft:shroomlight")


def formations(bb, rng):
    """Stalactites from the roof, stalagmites from the floor, glow lichen patches."""
    for _ in range(320):
        x, z = int(rng.integers(3, NX - 3)), int(rng.integers(3, NZ - 3))
        col = bb.get_region(x, 0, z, x, DOME_H + 2, z)[0, :, 0]
        air = np.nonzero(col == 1)[0]
        if len(air) < 6:
            continue
        top, bot = int(air[-1]), int(air[0])
        p = rng.random()
        if p < 0.45:
            L = int(rng.integers(2, 6))
            for k in range(L):
                th = "tip" if k == L - 1 else "frustum" if k < L - 2 else "middle"
                bb.set(x, top - k, z, f"minecraft:pointed_dripstone[thickness={th},vertical_direction=down,waterlogged=false]")
            bb.set(x, top + 1, z, "minecraft:dripstone_block")
        elif p < 0.7 and not lake(np.array(float(x)), np.array(float(z))):
            L = int(rng.integers(2, 5))
            bb.set(x, bot - 1, z, "minecraft:dripstone_block")
            for k in range(L):
                th = "tip" if k == L - 1 else "frustum" if k < L - 2 else "middle"
                bb.set(x, bot + k, z, f"minecraft:pointed_dripstone[thickness={th},vertical_direction=up,waterlogged=false]")
        else:
            bb.set(x, top, z, "minecraft:glow_lichen[down=false,east=false,north=false,south=false,up=true,waterlogged=false,west=false]")


def dock_and_sloop(bb):
    """A long plank dock on piles from the west shore into the lake, lanterns on posts, the sloop alongside."""
    z = LZ + 6
    x0 = LX - 22
    while x0 < LX and not lake(np.array(float(x0)), np.array(float(z))):
        x0 += 1
    x0 -= 4
    for x in range(x0, x0 + 24):
        bb.fill(x, 0, z - 1, x, 0, z + 1, "minecraft:spruce_planks")
        bb.fill(x, 1, z - 1, x, 3, z + 1, AIR)
        if x % 4 == 0:
            for dz in (-2, 2):
                bb.fill(x, -6, z + dz, x, 1, z + dz, "minecraft:stripped_spruce_log[axis=y]")
                bb.set(x, 2, z + dz, "minecraft:lantern")
    src = galleon(length=24, beam=9, depth=7, masts=1, hull="minecraft:dark_oak_planks", deck="minecraft:spruce_planks",
                  sail="minecraft:black_wool", castle=True, guns=False, figure="minecraft:bone_block")
    where = transfer(bb, src, -2, 30, x0 + 4, -4, z + 7, drop_above=21)
    # black sail with a white skull
    mx, my, mz = where(12, 13, 0)
    return where


def hoard(bb, rng):
    """The mound of gold: a heap of gold and raw gold blocks with pressure-plate "coins", goblets (lanterns), crowns,
    gems, the captain's chests on top, skeletons of treasure hunters round its foot."""
    for y in range(0, 7):
        r = 7.5 - y * 1.1
        bb.fill_where(HX - 9, y, HZ - 9, HX + 9, y, HZ + 9,
                      lambda X, yy, Z, r=r: ((X - HX) ** 2 + ((Z - HZ) * 1.2) ** 2 <= r * r) & (NT.noise(X * 2 + yy, Z * 2, 4304, 2) > 0.25),
                      "minecraft:gold_block")
        bb.fill_where(HX - 9, y, HZ - 9, HX + 9, y, HZ + 9,
                      lambda X, yy, Z, r=r: ((X - HX) ** 2 + ((Z - HZ) * 1.2) ** 2 <= r * r) & (NT.noise(X * 2 + yy, Z * 2, 4304, 2) <= 0.25),
                      "minecraft:raw_gold_block")
    for _ in range(90):
        a, d = rng.uniform(0, 6.283), rng.uniform(0, 11)
        x, z = int(round(HX + d * math.cos(a))), int(round(HZ + d * math.sin(a) / 1.2))
        col = bb.get_region(x, 0, z, x, 10, z)[0, :, 0]
        air = np.nonzero(col == 1)[0]
        if len(air) == 0:
            continue
        y = int(air[0])
        bb.set(x, y, z, ["minecraft:light_weighted_pressure_plate", "minecraft:light_weighted_pressure_plate", "minecraft:lantern",
                         "minecraft:emerald_block" if False else "minecraft:amethyst_cluster[facing=up,waterlogged=false]",
                         "minecraft:light_weighted_pressure_plate", "minecraft:candle[candles=2,lit=true]"][int(rng.integers(0, 6))])
    top = 7
    bb.fill(HX - 2, top, HZ - 2, HX + 2, top, HZ + 2, "minecraft:gold_block")
    bb.set(HX, top + 1, HZ + 3, "minecraft:skeleton_skull[rotation=8]")
    for (x, z, f) in ((HX - 12, HZ + 6, "east"), (HX - 11, HZ - 8, "north"), (HX - 4, HZ + 12, "south")):
        bb.set(x, 1, z, "minecraft:skeleton_skull[rotation=4]")
        bb.fill(x + 1, 1, z, x + 3, 1, z, "minecraft:bone_block[axis=x]")
        bb.set(x + 2, 1, z + 1, "minecraft:bone_block[axis=z]")
    return top


def camp(bb, rng):
    """Crew camp on the south shore: tents, a long table with benches and barrels, the fire pit, hammocks, the powder
    store, a lookout ledge with a ladder."""
    cx, cz = 30, 68
    for (x, z) in ((cx - 10, cz - 4), (cx + 6, cz - 2)):
        for s in range(3):
            bb.fill(x, 1 + s, z + s, x + 5, 1 + s, z + s, "minecraft:red_wool" if s % 2 else "minecraft:white_wool")
            bb.fill(x, 1 + s, z + 5 - s, x + 5, 1 + s, z + 5 - s, "minecraft:red_wool" if s % 2 else "minecraft:white_wool")
        bb.fill(x + 1, 1, z + 1, x + 4, 2, z + 4, AIR)
        bb.set(x + 2, 1, z + 2, "minecraft:red_bed[facing=east,part=foot]"); bb.set(x + 3, 1, z + 2, "minecraft:red_bed[facing=east,part=head]")
    bb.set(cx, 1, cz - 8, "minecraft:campfire[lit=true]")
    for a in range(0, 360, 45):
        t = math.radians(a)
        bb.set(cx + int(round(2 * math.cos(t))), 1, cz - 8 + int(round(2 * math.sin(t))), "minecraft:cobblestone_slab[type=bottom,waterlogged=false]")
    tx, tz = cx - 4, cz - 14
    bb.fill(tx, 1, tz, tx + 8, 1, tz, "minecraft:spruce_fence"); bb.fill(tx, 2, tz, tx + 8, 2, tz, "minecraft:spruce_slab[type=bottom,waterlogged=false]")
    for x in range(tx, tx + 9, 2):
        bb.set(x, 1, tz - 1, "minecraft:spruce_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
        bb.set(x, 1, tz + 1, "minecraft:spruce_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
    for (x, z) in ((tx + 2, tz), (tx + 6, tz)):
        bb.set(x, 3, z, "minecraft:candle[candles=3,lit=true]")
    for (x, z) in ((tx + 10, tz - 2), (tx + 10, tz - 1), (tx + 11, tz - 2), (tx + 10, tz + 1)):
        bb.set(x, 1, z, "minecraft:barrel[facing=up]")
    bb.set(tx + 10, 2, tz - 2, "minecraft:barrel[facing=up]")
    # powder store: kegs behind a plank screen with a no-fire sign (red banner)
    px, pz = 10, 58
    bb.fill(px, 1, pz, px + 6, 3, pz, "minecraft:spruce_planks")
    for x in range(px, px + 7):
        for k in range(2):
            bb.set(x, 1 + k, pz - 1 - (x % 2), "minecraft:barrel[facing=up]")
    bb.set(px + 3, 4, pz, "minecraft:red_banner[rotation=8]")
    for (x, z) in ((px + 1, pz + 2), (px + 3, pz + 2)):
        bb.set(x, 1, z, "onepiece:cannonball_pile")


def design():
    bb = BigBuild(seed=4300, y_min=-10, y_max=DOME_H + 6)
    rng = np.random.default_rng(4305)
    cave(bb)
    where = dock_and_sloop(bb)
    htop = hoard(bb, rng)
    camp(bb, rng)
    formations(bb, rng)
    # tunnels into the island's caves
    for (a, b, c) in (((8, 2, 46), (0, 6, 40), 2), ((104, 2, 28), (NX - 1, 7, 20), 2)):
        n = abs(b[0] - a[0])
        for k in range(n + 1):
            t = k / max(n, 1)
            x, y, z = (int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))
            bb.fill(x, y, z - c, x, y + 3, z + c, AIR)
    return bb, [], where, htop


def build():
    bb, audit, where, htop = design()
    b = to_canvas(bb)
    x, y, z = where(4, 6, 0)
    b.chest(x, y, z, "underground_treasure", "east")
    b.chest(HX, htop + 1, HZ, "underground_treasure", "west")
    b.chest(HX - 2, htop + 1, HZ - 2, "treasure", "east")
    b.chest(HX - 2, htop + 1, HZ + 2, "underground_treasure", "east")
    for (x, z, kit) in ((26, 56, "pirate"), (34, 60, "pirate"), (60, 68, "pirate"), (12, 52, "pirate_gunner"), (80, 50, "pirate_gunner")):
        b.guard(x, 1, z, kit)
    return b, 0
