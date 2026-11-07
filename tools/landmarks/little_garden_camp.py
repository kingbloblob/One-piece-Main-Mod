"""Little Garden: the prehistoric jungle island where the giants Dorry and Brogy have fought their duel for a
hundred years. Two giant-sized camps face each other across the duel ground at the foot of the smoking volcano:
Dorry's giant hut and Brogy's cave camp with giant bonfires, beds of furs, barrels and the huge sword and axe,
plus a dinosaur skeleton, giant ferns, Mr. 3's wax 'Candle Service Set' cake and the jungle all round.
~100 x 100. Ground = y 0. Giants are ~20 m tall, so their things are built to that scale."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "little_garden_camp"
TITLE = "Little Garden Giants' Camp"
CUTS = [3]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 100
CX, CZ = 50, 54
GIANT = dict(wood="spruce", rug="brown", rug2="orange", bed="brown", light="minecraft:lantern", accent="minecraft:bone_block[axis=y]",
             banner="brown", candle="orange")


def bonfire(b, x, z, r=4):
    b.cyl(x, z, r + 1, 0, 0, "minecraft:cobblestone")
    for i in range(10):
        a = math.radians(i * 36)
        b.line((x, 1, z), (x + r * math.cos(a), 1 + (i % 2) * 2, z + r * math.sin(a)), "minecraft:stripped_oak_log[axis=y]")
    b.cyl(x, z, 1.5, 1, 1, "minecraft:magma_block"); b.cyl(x, z, 1.5, 2, 2, "minecraft:fire")


def build():
    rnd = random.Random(311)
    b = B()
    T.ground(b, N, N, rnd, deco=0.2, decos=("minecraft:fern", "minecraft:large_fern[half=lower]", "minecraft:short_grass", "onepiece:giant_fern"))
    for x in range(N):
        for z in range(N):
            s = b.get(x, 1, z)
            if s and "large_fern[half=lower]" in s: b.set(x, 2, z, "minecraft:large_fern[half=upper]")
    # jungle trees round the edge
    for i in range(70):
        x, z = rnd.randint(2, N - 3), rnd.randint(2, N - 3)
        if math.hypot(x - CX, z - CZ) < 34 or (x > 66 and z < 34): continue
        h = rnd.randint(10, 18)
        b.cyl(x, z, 1.0, 1, h, "minecraft:jungle_log[axis=y]")
        b.sphere(x, h + 1, z, rnd.uniform(3.5, 5.5), "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]", ry=2.8)
        for k in range(rnd.randint(2, 6)):
            vx, vz = x + rnd.randint(-3, 3), z + rnd.randint(-3, 3)
            for y in range(h - 1, h - 1 - rnd.randint(3, 8), -1):
                if b.get(vx, y, vz) is None: b.set(vx, y, vz, "minecraft:vine[east=false,north=true,south=false,up=false,west=false]")
    # the smoking volcano (north-east)
    VX, VZ = 84, 16
    for y in range(0, 40):
        r = 22 * (1 - y / 44)
        b.cyl(VX, VZ, r, y, y, "minecraft:basalt[axis=y]" if y > 28 else ("minecraft:stone" if (y // 3) % 2 else "minecraft:tuff"))
    b.cyl(VX, VZ, 3.5, 30, 40, "minecraft:lava[level=0]"); b.cyl(VX, VZ, 4.5, 39, 40, "minecraft:basalt[axis=y]", hollow=True)
    for y in range(41, 48): b.set(VX + rnd.randint(-1, 1), y, VZ + rnd.randint(-1, 1), "minecraft:campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]") if y == 41 else None
    # the duel ground: trampled earth
    for x in range(CX - 26, CX + 27):
        for z in range(CZ - 20, CZ + 21):
            if ((x - CX) / 26) ** 2 + ((z - CZ) / 20) ** 2 < 1:
                b.set(x, 0, z, "minecraft:coarse_dirt" if (x * z) % 5 else "minecraft:rooted_dirt")
                if b.get(x, 1, z) is not None: b.set(x, 1, z, AIR)
                if b.get(x, 2, z) is not None: b.set(x, 2, z, AIR)
    # ---------------- Dorry's camp (west): a giant hut of logs and hides
    DX, DZ = 16, 54
    b.cyl(DX, DZ, 10, 0, 0, "minecraft:spruce_planks")
    for a in range(0, 360, 20):  # conical hut of giant poles
        t = math.radians(a)
        b.line((DX + 10 * math.cos(t), 1, DZ + 10 * math.sin(t)), (DX, 22, DZ), "minecraft:spruce_log[axis=y]")
    for y in range(1, 20):
        r = 10 * (1 - y / 22)
        for a in range(0, 360, 3):
            t = math.radians(a)
            if not (a < 30 or a > 330) or y > 9:  # opening facing east
                b.set(round(DX + r * math.cos(t)), y, round(DZ + r * math.sin(t)), "minecraft:brown_wool" if (y // 4) % 2 else "minecraft:light_gray_wool")
    for x in range(DX - 6, DX + 4):  # giant fur bed
        for z in range(DZ - 6, DZ - 1): b.set(x, 1, z, "minecraft:brown_wool"); b.set(x, 2, z, "minecraft:brown_carpet")
    for (x, z) in ((DX + 5, DZ + 5), (DX + 2, DZ + 7)):
        b.cyl(x, z, 1.5, 1, 4, "minecraft:spruce_planks"); b.set(x, 5, z, "minecraft:spruce_slab[type=bottom,waterlogged=false]")  # giant barrels of sake
    I.furnish(b, DX - 4, 1, DZ + 1, DX + 4, DZ + 6, 6, "storage", GIANT, seed=5)
    bonfire(b, DX + 16, DZ)
    # Dorry's giant sword stuck in the ground
    sx, sz = DX + 14, DZ - 10
    for y in range(1, 22): b.set(sx, y, sz, "minecraft:iron_block"); b.set(sx, y, sz + 1, "minecraft:iron_block") if y < 18 else None
    for z in range(sz - 3, sz + 5): b.set(sx, 22, z, "minecraft:gold_block")
    for y in range(23, 28): b.set(sx, y, sz, "minecraft:brown_wool")
    # ---------------- Brogy's camp (east): a cave in a rock outcrop
    BX, BZ = 84, 62
    b.shape(lambda x, y, z: ((x - BX) / 14) ** 2 + (y / 14) ** 2 + ((z - BZ) / 14) ** 2 <= 1 and y >= 0, BX - 15, 0, BZ - 15, BX + 15, 15, BZ + 15,
            lambda x, y, z: "minecraft:mossy_cobblestone" if (x + y + z) % 5 == 0 else "minecraft:stone", interior=AIR)
    for x in range(BX - 14, BX - 4):
        for y in range(1, 11):
            for z in range(BZ - 5, BZ + 6):
                if ((y - 1) / 10) ** 2 + ((z - BZ) / 5.5) ** 2 < 1: b.set(x, y, z, AIR)
    b.cyl(BX, BZ, 12, 0, 0, "minecraft:coarse_dirt")
    for x in range(BX - 4, BX + 6):
        for z in range(BZ - 2, BZ + 6): b.set(x, 1, z, "minecraft:orange_wool"); b.set(x, 2, z, "minecraft:brown_carpet")
    I.furnish(b, BX - 6, 1, BZ - 8, BX + 6, BZ - 3, 8, "kitchen", GIANT, seed=6)
    bonfire(b, BX - 20, BZ)
    ax, az = BX - 18, BZ + 12  # Brogy's giant axe
    for y in range(1, 20): b.set(ax, y, az, "minecraft:stripped_spruce_log[axis=y]")
    for y in range(14, 22):
        for k in range(1, 7 - abs(y - 18)): b.set(ax + k, y, az, "minecraft:iron_block")
    # ---------------- dinosaur skeleton on the duel ground
    b.bones(CX - 8, 1, CZ + 14, 24, axis="x", height=8)
    # ---------------- Mr. 3's candle cake (a wax platform with spinning candle)
    MX, MZ = CX + 2, CZ - 10
    b.cyl(MX, MZ, 5, 1, 2, "minecraft:white_concrete"); b.cyl(MX, MZ, 3.5, 3, 4, "minecraft:white_concrete"); b.cyl(MX, MZ, 1, 5, 12, "minecraft:white_wool")
    b.set(MX, 13, MZ, "minecraft:fire") if False else b.set(MX, 13, MZ, "minecraft:candle[candles=1,lit=true,waterlogged=false]")
    for (dx, dz) in ((-5, 0), (5, 0), (0, 5), (0, -5)):
        b.set(MX + dx, 3, MZ + dz, "minecraft:white_candle[candles=3,lit=true,waterlogged=false]")
    # ---------------- loot and hunters
    b.chest(DX - 2, 1, DZ + 7, "medium", "north"); b.chest(BX + 6, 1, BZ + 7, "medium", "north")
    b.guards("bounty_hunter", ((CX + 2, CZ - 4), (CX - 4, CZ - 8)))
    return b, 0
