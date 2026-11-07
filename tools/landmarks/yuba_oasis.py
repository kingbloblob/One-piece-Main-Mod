"""Yuba, the dying oasis of Alabasta. Sand dunes have swallowed half of the town: houses buried up to their roofs,
dead palms, the dry lake bed where old Toto keeps digging for water, his tent and well, the remains of the
Rebel Army camp with tents and weapon racks, and a single spring of water bubbling up again at the bottom of
Toto's pit. ~80 x 80. Ground = y 0."""
import math, random
from canvas import *
import interiors as I
import townkit as T
import alubarna as AL

SID = "yuba_oasis"
TITLE = "Yuba Oasis"
CUTS = [2]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 80
CX, CZ = 40, 40


def dune(x, z):
    return max(0, int(4 * math.sin(x * 0.09 + 1) * math.cos(z * 0.07) + 3 * math.sin((x + z) * 0.05) + 1))


def build():
    rnd = random.Random(301)
    b = B()
    for x in range(N):
        for z in range(N):
            for y in (-4, -3, -2, -1): b.set(x, y, z, "minecraft:sandstone")
            b.set(x, 0, z, "minecraft:sand")
    # the dry lake bed in the middle, Toto's pit with water at the bottom
    for x in range(CX - 12, CX + 13):
        for z in range(CZ - 10, CZ + 11):
            d = ((x - CX) / 12) ** 2 + ((z - CZ) / 10) ** 2
            if d < 1:
                depth = int(3 * (1 - d))
                for y in range(-depth, 1): b.set(x, y, z, AIR)
                b.set(x, -depth - 1, z, "minecraft:mud" if d < 0.15 else ("minecraft:packed_mud" if (x + z) % 3 else "minecraft:coarse_dirt"))
    for x in range(CX - 1, CX + 2):
        for z in range(CZ - 1, CZ + 2):
            for y in range(-8, -3): b.set(x, y, z, AIR)
            b.set(x, -8, z, WATER); b.set(x, -9, z, "minecraft:mud")
    b.set(CX + 2, -3, CZ, "minecraft:iron_shovel" if False else "minecraft:ladder[facing=west,waterlogged=false]")
    for y in range(-8, -3): b.set(CX + 1, y, CZ, "minecraft:ladder[facing=west,waterlogged=false]")
    # Toto's tent
    for dx in range(-3, 4):
        for dy in range(0, 4 - abs(dx)):
            for dz in range(0, 6): b.set(CX + 18 + dx, 1 + dy, CZ - 3 + dz, "minecraft:white_wool" if dy < 2 else "minecraft:light_gray_wool")
    for dz in range(0, 6):
        for dy in (0, 1): b.set(CX + 18, 1 + dy, CZ - 3 + dz, AIR)
    b.set(CX + 18, 1, CZ - 2, "minecraft:white_bed[facing=north,occupied=false,part=head]"); b.set(CX + 18, 1, CZ - 1, "minecraft:white_bed[facing=north,occupied=false,part=foot]")
    b.set(CX + 17, 1, CZ + 1, "minecraft:barrel[facing=up,open=false]"); b.set(CX + 19, 1, CZ + 1, "minecraft:cauldron")
    # the half-buried town: houses with sand piled to their windows
    seeds = 0
    for (x0, z0, w, d, h) in ((4, 4, 9, 8, 6), (18, 6, 8, 8, 5), (52, 4, 10, 9, 6), (66, 8, 9, 8, 5), (4, 60, 9, 8, 6), (18, 66, 10, 9, 5),
                              (54, 62, 9, 9, 6), (68, 66, 8, 8, 5), (4, 30, 8, 9, 5), (68, 34, 9, 8, 6), (30, 68, 9, 8, 5)):
        AL.house(b, x0, z0, w, d, h, seeds * 11 + 5); seeds += 1
    # drifts: sand dunes poured over everything outside the lake bed
    for x in range(N):
        for z in range(N):
            if ((x - CX) / 13) ** 2 + ((z - CZ) / 11) ** 2 < 1: continue
            h = dune(x, z)
            for y in range(1, h + 1):
                s = b.get(x, y, z)
                if s is None or s == AIR or "carpet" in (s or "") or "bed" in (s or "") or "pot" in (s or ""):
                    b.set(x, y, z, "minecraft:sand" if y < h else ("minecraft:sand" if rnd.random() < 0.8 else "minecraft:smooth_sandstone_slab[type=bottom,waterlogged=false]"))
            if h == 0 and rnd.random() < 0.02: b.set(x, 1, z, "minecraft:dead_bush")
    # dead palms
    for i in range(12):
        a = rnd.uniform(0, 2 * math.pi); r = rnd.uniform(13, 18)
        x, z = round(CX + r * math.cos(a)), round(CZ + r * math.sin(a))
        h0 = dune(x, z)
        for y in range(h0 + 1, h0 + rnd.randint(4, 8)): b.set(x, y, z, "onepiece:stripped_palm_log[axis=y]")
    # the old Rebel Army camp
    for (tx, tz) in ((20, 34), (20, 44), (28, 50)):
        y0 = dune(tx, tz)
        for dx in range(-2, 3):
            for dy in range(0, 3 - abs(dx)):
                for dz in range(0, 5): b.set(tx + dx, y0 + 1 + dy, tz + dz, "minecraft:brown_wool" if dy < 2 else "minecraft:orange_wool")
        for dz in range(0, 5): b.set(tx, y0 + 1, tz + dz, AIR)
    y0 = dune(30, 38)
    for i in range(4): b.set(30 + i, y0 + 1, 38, "minecraft:spruce_fence"); b.set(30 + i, y0 + 2, 38, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]")
    b.set(26, dune(26, 40) + 1, 40, "minecraft:campfire[facing=north,lit=false,signal_fire=false,waterlogged=false]")
    # ---------------- loot
    b.chest(CX + 20, 1, CZ + 1, "easy", "west")
    return b, 0
