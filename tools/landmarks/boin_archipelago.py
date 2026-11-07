"""The Boin Archipelago where Usopp was sent: islands of colossal, living plants. Pitcher plants big enough to swallow
a man, giant mushrooms and puffballs, vines thick as tree trunks, a giant sunflower and lily pads on the lagoon,
carnivorous snapper plants, the treehouse lab of Heracles(un) the bug-hunter with his specimen jars and a
greenhouse, and the 'Pop Green' seed garden. ~100 x 96. Ground = y 0, a lagoon in the middle."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "boin_archipelago"
TITLE = "Boin Archipelago"
CUTS = [2, 10, 22]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 100, 96
LX, LZ = 50, 54
JUNGLE = dict(wood="jungle", rug="green", rug2="lime", bed="green", light="minecraft:lantern", accent="minecraft:moss_block",
              banner="green", candle="lime")


def pitcher(b, x, z, h, r):
    for y in range(1, h + 1):
        rr = r * (0.7 + 0.5 * math.sin(math.pi * y / (h + 2)))
        b.cyl(x, z, rr, y, y, "minecraft:lime_concrete" if y % 4 else "minecraft:green_concrete", hollow=True)
    b.cyl(x, z, r * 0.8, h, h, "minecraft:red_concrete", hollow=True)
    b.cyl(x, z, r * 0.6, 1, 2, WATER)
    for k in range(4): b.set(x + r + 1, h + 1 + k, z, "minecraft:green_concrete" if k < 3 else "minecraft:red_concrete")


def mushroom(b, x, z, h, r, cap):
    b.cyl(x, z, max(1, r / 4), 1, h, "minecraft:mushroom_stem[down=true,east=true,north=true,south=true,up=true,west=true]")
    b.shape(lambda xx, y, zz: ((xx - x) / r) ** 2 + ((y - h) / (r * 0.45)) ** 2 + ((zz - z) / r) ** 2 < 1 and y >= h, x - r, h, z - r, x + r, h + r, z + r, cap, interior=AIR)


def build():
    rnd = random.Random(751)
    b = B()
    T.ground(b, NX, NZ, rnd, deco=0.4, decos=("minecraft:fern", "minecraft:short_grass", "onepiece:giant_fern", "minecraft:moss_carpet", "minecraft:short_grass"))
    for x in range(NX):
        for z in range(NZ):
            if rnd.random() < 0.3: b.set(x, 0, z, "minecraft:moss_block")
    T.sea(b, NX, NZ, lambda x, z: ((x - LX) / 18) ** 2 + ((z - LZ) / 13) ** 2 < 1, depth=4, floor="minecraft:mud")
    for i in range(14):  # lily pads
        a, r = rnd.uniform(0, 6.28), rnd.uniform(0, 14)
        x, z = round(LX + r * math.cos(a)), round(LZ + r * 0.7 * math.sin(a))
        b.cyl(x, z, rnd.uniform(1.2, 2.6), 1, 1, "minecraft:lily_pad") if False else b.cyl(x, z, rnd.uniform(1.2, 2.6), 0, 0, "minecraft:lime_terracotta")
    # ---------------- giant plants
    for (x, z, h, r) in ((14, 20, 14, 4), (82, 18, 18, 5), (86, 80, 12, 4)): pitcher(b, x, z, h, r)
    for (x, z, h, r, cap) in ((30, 12, 16, 8, "minecraft:red_mushroom_block[down=true,east=true,north=true,south=true,up=true,west=true]"),
                              (70, 34, 12, 6, "minecraft:brown_mushroom_block[down=true,east=true,north=true,south=true,up=true,west=true]"),
                              (12, 76, 20, 9, "minecraft:red_mushroom_block[down=true,east=true,north=true,south=true,up=true,west=true]"),
                              (90, 50, 10, 5, "minecraft:brown_mushroom_block[down=true,east=true,north=true,south=true,up=true,west=true]")):
        mushroom(b, x, z, h, r, cap)
    for (x, z) in ((60, 86), (36, 84)):  # puffballs
        b.sphere(x, 4, z, 4, "minecraft:white_concrete", ry=3.5)
    # the giant sunflower
    SX, SZ = 50, 22
    for y in range(1, 30): b.set(SX, y, SZ, "minecraft:green_concrete"); b.set(SX + 1, y, SZ, "minecraft:green_concrete")
    for a in range(0, 360, 4):
        t = math.radians(a)
        for r in range(0, 9):
            b.set(round(SX + r * math.cos(t)), 30 + round(r * math.sin(t)), SZ + 1, "minecraft:brown_concrete" if r < 4 else "minecraft:yellow_concrete")
    for k in range(10): b.set(SX - 1 - k, 12 + k // 3, SZ, "minecraft:green_concrete"); b.set(SX + 2 + k, 18 + k // 3, SZ, "minecraft:green_concrete")
    # trunk-thick vines arching over the island
    for (p0, p1) in (((4, 1, 40), (40, 26, 36)), ((40, 26, 36), (70, 1, 60)), ((96, 1, 30), (64, 22, 8))):
        steps = 40
        for t in range(steps + 1):
            f = t / steps
            x = p0[0] + (p1[0] - p0[0]) * f; z = p0[2] + (p1[2] - p0[2]) * f
            y = p0[1] + (p1[1] - p0[1]) * f + 10 * math.sin(math.pi * f)
            b.sphere(x, y, z, 1.5, "minecraft:jungle_log[axis=y]" if t % 7 else "minecraft:moss_block")
    # snapper plants
    for (x, z) in ((24, 44), (76, 70), (66, 10)):
        b.column(x, z, 1, 4, "minecraft:green_concrete")
        b.box(x - 2, 5, z - 1, x + 2, 5, z + 1, "minecraft:red_concrete"); b.box(x - 2, 7, z - 1, x + 2, 7, z + 1, "minecraft:red_concrete")
        for dx in (-2, 0, 2): b.set(x + dx, 6, z - 1, "minecraft:white_concrete"); b.set(x + dx, 6, z + 1, "minecraft:white_concrete")
    # ---------------- Heracles' treehouse lab and greenhouse
    TX, TZ = 26, 60
    b.cyl(TX, TZ, 2.2, 1, 22, "minecraft:jungle_log[axis=y]")
    b.box(TX - 7, 12, TZ - 6, TX + 7, 12, TZ + 6, "minecraft:jungle_planks")
    b.walls(TX - 7, 13, TZ - 6, TX + 7, 17, TZ + 6, "minecraft:jungle_planks"); b.box(TX - 6, 13, TZ - 5, TX + 6, 17, TZ + 5, AIR)
    b.cyl(TX, TZ, 2.2, 13, 17, "minecraft:jungle_log[axis=y]")
    for x in range(TX - 6, TX + 7, 3): b.set(x, 15, TZ + 6, "minecraft:glass_pane"); b.set(x, 15, TZ - 6, "minecraft:glass_pane")
    b.hip_roof(TX - 7, TZ - 6, TX + 7, TZ + 6, 18, "minecraft:jungle_stairs", "minecraft:jungle_planks")
    I.furnish(b, TX - 6, 13, TZ - 5, TX - 3, TZ + 5, 4, "lab", JUNGLE, seed=1)
    I.furnish(b, TX + 3, 13, TZ - 5, TX + 6, TZ + 5, 4, "bedroom", JUNGLE, seed=2)
    for y in range(1, 13): b.set(TX + 3, y, TZ, "minecraft:ladder[facing=east,waterlogged=false]")
    b.set(TX + 3, 12, TZ, AIR)
    b.sphere(TX, 25, TZ, 8, "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]", ry=4)
    GX0, GZ0 = 70, 82
    b.box(GX0, 0, GZ0, GX0 + 12, 0, GZ0 + 8, "minecraft:mossy_stone_bricks")
    b.walls(GX0, 1, GZ0, GX0 + 12, 5, GZ0 + 8, "minecraft:glass"); b.box(GX0, 6, GZ0, GX0 + 12, 6, GZ0 + 8, "minecraft:glass")
    b.box(GX0 + 1, 1, GZ0 + 1, GX0 + 11, 5, GZ0 + 7, AIR)
    for x in range(GX0 + 1, GX0 + 12):
        for z in (GZ0 + 2, GZ0 + 6): b.set(x, 1, z, rnd.choice(("minecraft:potted_fern", "minecraft:potted_red_mushroom", "minecraft:potted_cactus", "minecraft:potted_azure_bluet", "minecraft:flowering_azalea")))
    b.set(GX0 + 6, 1, GZ0 + 8, AIR); b.set(GX0 + 6, 2, GZ0 + 8, AIR)
    # ---------------- loot
    b.chest(TX - 4, 13, TZ + 4, "easy", "east"); b.chest(GX0 + 10, 1, GZ0 + 4, "easy", "west"); b.chest(82, 1, 23, "easy", "south")
    return b, 0
