"""Nanohana, Alabasta's port of perfume and trade. White flat-roofed houses in narrow lanes, the covered bazaar
with dozens of stalls (spices, perfume, fruit, cloth), the perfume shop, inns and the restaurant where Ace and
Luffy ate, palm-lined quays with dhows moored at long piers, and the lighthouse at the harbour mouth.
~100 x 96. Ground = y 0, sea to the north."""
import math, random
from canvas import *
import interiors as I
import townkit as T
import alubarna as AL

SID = "nanohana_port"
TITLE = "Nanohana Market"
CUTS = [3]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 100, 96
SEA_Z = 16


def dhow(b, x0, z0, L=16):
    for i in range(L):
        hw = 2 if 2 < i < L - 3 else 1
        for dz in range(-hw, hw + 1):
            b.set(x0 + i, -1, z0 + dz, "minecraft:jungle_planks"); b.set(x0 + i, 0, z0 + dz, "minecraft:jungle_planks" if abs(dz) == hw else "minecraft:spruce_planks")
        b.set(x0 + i, 1, z0 - hw, fence("jungle")); b.set(x0 + i, 1, z0 + hw, fence("jungle"))
    mx = x0 + L // 2
    for y in range(1, 12): b.set(mx, y, z0, "minecraft:jungle_log[axis=y]")
    for k in range(9):  # triangular lateen sail
        for y in range(4 + k // 2, 12 - k // 3): b.set(mx + 1 + k - 4, y, z0, "minecraft:white_wool") if 0 <= k else None


def build():
    rnd = random.Random(291)
    b = B()
    T.ground(b, NX, NZ, rnd, top="minecraft:sand", deco=0)
    T.sea(b, NX, NZ, lambda x, z: z < SEA_Z, depth=5)
    for x in range(NX):  # stone quay
        for z in (SEA_Z, SEA_Z + 1, SEA_Z + 2): b.set(x, 0, z, "minecraft:cut_sandstone" if z > SEA_Z else "minecraft:smooth_sandstone")
        if x % 6 == 0: b.set(x, 1, SEA_Z, "minecraft:sandstone_wall")
    for x0 in (14, 40, 66):
        T.pier(b, x0, SEA_Z - 12, 12, y=1, boat=False)
        dhow(b, x0 + 4, SEA_Z - 7)
    for x in range(4, NX - 4, 7):
        T.tree(b, x, SEA_Z + 4, h=6, kind="jungle", r=2.4) if False else None
        for y in range(1, 7): b.set(x, y, SEA_Z + 4, "onepiece:palm_log[axis=y]")
        for (dx, dz) in ((1, 0), (2, 0), (-1, 0), (-2, 0), (0, 1), (0, 2), (0, -1), (0, -2), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            b.set(x + dx, 7 if abs(dx) + abs(dz) < 2 else 6, SEA_Z + 4 + dz, "onepiece:palm_leaves[distance=7,persistent=true,waterlogged=false]")
    # the lighthouse on the harbour mole (east)
    lx, lz = NX - 8, 6
    for z in range(lz, SEA_Z):
        for x in range(lx - 2, lx + 3): b.set(x, 0, z, "minecraft:cut_sandstone")
    b.cyl(lx, lz, 3, 1, 18, "minecraft:smooth_sandstone", hollow=True)
    for y in range(1, 18): b.set(lx, y, lz - 2, "minecraft:ladder[facing=south,waterlogged=false]")
    b.cyl(lx, lz, 2, 18, 18, "minecraft:cut_sandstone"); b.set(lx, 19, lz, "minecraft:sea_lantern")
    b.dome(lx, lz, 20, 2, s="minecraft:cut_sandstone", tip=None)
    b.set(lx, 1, lz + 3, AIR); b.set(lx, 2, lz + 3, AIR)
    # ---------------- the covered bazaar: a long arcade of stalls under striped awnings
    BZ0, BZ1 = 30, 44
    for x in range(10, 90):
        for z in range(BZ0, BZ1 + 1): b.set(x, 0, z, "minecraft:smooth_sandstone" if (x + z) % 2 else "minecraft:sandstone")
    colors = ("red", "orange", "yellow", "white", "light_blue", "purple")
    goods = (("minecraft:melon", "minecraft:pumpkin", "onepiece:mikan_crate"), ("minecraft:hay_block[axis=y]", "minecraft:barrel[facing=up,open=false]", None),
             ("minecraft:decorated_pot[cracked=false,facing=north,waterlogged=false]", "minecraft:flower_pot", None),
             ("minecraft:red_wool", "minecraft:yellow_wool", "minecraft:blue_wool"), ("minecraft:brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=true]", "minecraft:potted_blue_orchid", None))
    for i, x in enumerate(range(12, 86, 6)):
        T.stall(b, x, BZ0 + 1, colors[i % len(colors)], goods[i % len(goods)])
        T.stall(b, x, BZ1 - 3, colors[(i + 3) % len(colors)], goods[(i + 2) % len(goods)])
    for x in range(10, 90, 4):  # lantern strings
        b.set(x, 6, (BZ0 + BZ1) // 2, lantern(True))
        for z in range(BZ0 + 3, BZ1 - 2): b.set(x, 7, z, "minecraft:white_wool" if x % 8 else "minecraft:orange_wool")
    # ---------------- town blocks of white houses south of the bazaar and along the quay
    seeds = 0
    for (x0, z0, w, d, h) in ((8, 20, 9, 8, 5), (20, 20, 8, 8, 4), (52, 20, 9, 8, 6), (78, 20, 8, 8, 4),
                              (8, 50, 9, 9, 6), (20, 50, 8, 8, 5), (32, 50, 10, 9, 4), (46, 50, 9, 8, 5), (58, 50, 8, 8, 6), (70, 50, 9, 9, 4), (82, 50, 9, 8, 5),
                              (8, 66, 9, 8, 4), (22, 66, 10, 9, 6), (36, 66, 9, 9, 5), (50, 66, 9, 8, 4), (62, 66, 10, 9, 6), (76, 66, 9, 8, 5),
                              (10, 82, 9, 8, 5), (24, 82, 9, 8, 4), (40, 82, 10, 9, 5), (56, 82, 9, 8, 6), (72, 82, 9, 8, 4), (86, 82, 8, 8, 5)):
        if x0 + w >= NX - 1 or z0 + d >= NZ - 1: continue
        AL.house(b, x0, z0, w, d, h, seeds * 7 + 3); seeds += 1
    # the perfume shop and the restaurant: bigger two-storey houses
    T.house(b, 32, 19, 12, 9, 2, "sand", rnd, kinds=["dining", "bedroom"], theme="desert", flat_roof=True, sign="minecraft:orange_wool")
    T.house(b, 64, 19, 10, 9, 2, "sand", rnd, kinds=["lab", "storage"], theme="desert", flat_roof=True, sign="minecraft:purple_wool")
    # lanes between the blocks
    for z in (47, 63, 79):
        for x in range(4, NX - 4): b.set(x, 0, z, "minecraft:smooth_sandstone")
    # ---------------- loot
    b.chest(33, 1, 20, "easy", "east")
    return b, 0
