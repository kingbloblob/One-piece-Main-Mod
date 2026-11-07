"""Rusukaina, the Island of Women's calm belt neighbour where Luffy trained for two years with Rayleigh: a
brutal jungle island ruled by giant beasts. Towering trees and vines, a cliff-ringed central mountain with a
waterfall, the giant beasts' nests of bones, the training camp clearing with a hut, sparring stones, a fire pit
and a boulder field smashed by Haki punches, Rayleigh's campsite on the beach, and the huge tree Luffy knocked
down. ~104 x 104. Ground = y 0."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "rusukaina"
TITLE = "Rusukaina Training Grounds"
CUTS = [2, 8, 22]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 104
MX, MZ = 66, 40
CAMP = dict(wood="jungle", rug="brown", rug2="green", bed="brown", light="minecraft:lantern", accent="minecraft:bone_block",
            banner="brown", candle="brown")


def build():
    rnd = random.Random(731)
    b = B()
    T.ground(b, N, N, rnd, deco=0.35, decos=("minecraft:fern", "minecraft:large_fern[half=lower]", "minecraft:short_grass", "onepiece:giant_fern"))
    for x in range(N):
        for z in range(N):
            if b.get(x, 1, z) == "minecraft:large_fern[half=lower]": b.set(x, 2, z, "minecraft:large_fern[half=upper]")
    T.sea(b, N, N, lambda x, z: z > 92 + 2 * math.sin(x * 0.2), depth=5)
    for x in range(N):
        for z in range(84, 96):
            if b.get(x, 0, z) not in (WATER,) and z > 86 + math.sin(x * 0.3): b.set(x, 0, z, "minecraft:sand"); b.set(x, 1, z, AIR) if b.get(x, 1, z) else None
    # ---------------- the central mountain and its waterfall
    for x in range(MX - 26, MX + 27):
        for z in range(MZ - 26, MZ + 27):
            d = math.hypot(x - MX, z - MZ)
            if d > 26 or not (0 <= x < N and 0 <= z < N): continue
            h = int(36 * math.exp(-(d / 13) ** 2)) + rnd.randint(0, 1)
            for y in range(1, h + 1): b.set(x, y, z, "minecraft:stone" if y < h - 1 else ("minecraft:moss_block" if h > 4 else "minecraft:grass_block"))
    # the falls down the south face: a stepped channel of water with rock lips at the sides, so the water runs down
    # into the plunge pool instead of spreading over the hillside
    fz = lambda y: MZ + int(13 * math.sqrt(max(0.01, math.log(36 / max(1, y))))) + 1
    for y in range(1, 30):
        z_a, z_b = fz(y), (fz(y - 1) if y > 1 else MZ + 22)
        for z in range(z_a, max(z_a, z_b) + 1):
            for dx in (-1, 0, 1):
                b.set(MX + dx, y, z, WATER); b.set(MX + dx, y - 1, z, "minecraft:stone") if b.get(MX + dx, y - 1, z) in (None, AIR) else None
            for dx in (-2, 2):
                b.set(MX + dx, y, z, "minecraft:mossy_cobblestone"); b.set(MX + dx, y - 1, z, "minecraft:stone")
    b.cyl(MX, MZ + 26, 5, 0, 0, WATER); b.cyl(MX, MZ + 26, 5, -2, -1, WATER)
    # giant trees and vines
    for i in range(26):
        x, z = rnd.randint(3, N - 4), rnd.randint(3, 80)
        if math.hypot(x - MX, z - MZ) < 28 or (8 < x < 44 and 40 < z < 74): continue
        h = rnd.randint(18, 30)
        b.cyl(x, z, 1.6, 1, h, "minecraft:jungle_log[axis=y]")
        b.sphere(x, h + 2, z, rnd.uniform(6, 8), "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]", ry=3.5)
        for k in range(6):
            vx, vz = x + rnd.randint(-5, 5), z + rnd.randint(-5, 5)
            for y in range(h - 1, h - rnd.randint(6, 14), -1): b.fill_if(vx, y, vz, "minecraft:vine[east=false,north=true,south=false,up=false,west=false]")
    # the giant fallen tree
    b.line((10, 2, 14), (40, 3, 30), "minecraft:jungle_log[axis=x]")
    for t in range(0, 31):
        x, z = 10 + t, 14 + t * 16 // 30
        b.cyl(x, z, 1.8, 1, 4, "minecraft:jungle_log[axis=x]")
    b.sphere(42, 4, 31, 5, "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]", ry=3)
    # beasts' bone nests
    for (x, z) in ((84, 74), (90, 12), (30, 8)):
        b.cyl(x, z, 5, 1, 1, "minecraft:hay_block[axis=y]"); b.cyl(x, z, 5.5, 2, 3, "minecraft:bone_block[axis=y]", hollow=True)
        for k in range(4): b.line((x - 5 + k * 3, 1, z - 5), (x - 2 + k, 6, z), "minecraft:bone_block[axis=y]")
    # ---------------- the training camp clearing
    TX, TZ = 26, 56
    b.cyl(TX, TZ, 15, 0, 0, "minecraft:coarse_dirt"); b.cyl(TX, TZ, 15, 1, 3, AIR)
    b.box(TX - 4, 0, TZ - 12, TX + 5, 0, TZ - 6, "minecraft:jungle_planks")
    b.walls(TX - 4, 1, TZ - 12, TX + 5, 4, TZ - 6, "minecraft:jungle_log[axis=y]")
    b.box(TX - 3, 1, TZ - 11, TX + 4, 4, TZ - 7, AIR)
    b.gable_roof(TX - 4, TZ - 12, TX + 5, TZ - 6, 5, "minecraft:jungle_stairs", "minecraft:jungle_planks", gable_wall="minecraft:jungle_planks")
    b.set(TX, 1, TZ - 6, AIR); b.set(TX, 2, TZ - 6, AIR)
    I.furnish(b, TX - 3, 1, TZ - 11, TX + 4, TZ - 7, 3, "bedroom", CAMP, seed=1)
    b.set(TX, 1, TZ, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"); b.cyl(TX, TZ, 1.5, 0, 0, "minecraft:cobblestone")
    for (dx, dz) in ((-3, 0), (3, 0), (0, 3)): b.set(TX + dx, 1, TZ + dz, "minecraft:stripped_jungle_log[axis=x]")
    for (dx, dz) in ((-10, 4), (-8, 9), (8, 6), (10, 1)):  # sparring stones, some cracked
        b.box(TX + dx, 1, TZ + dz, TX + dx + 1, 3, TZ + dz + 1, rnd.choice(("minecraft:stone", "minecraft:cracked_stone_bricks", "minecraft:andesite")))
    for i in range(24):  # boulder field smashed by punches
        x, z = TX + rnd.randint(-13, 13), TZ + rnd.randint(6, 14)
        b.set(x, 1, z, rnd.choice(("minecraft:cobblestone", "minecraft:gravel", "minecraft:stone", "minecraft:cobblestone_slab[type=bottom,waterlogged=false]")))
    for x in range(TX - 4, TX + 5, 4): b.set(x, 1, TZ - 3, "onepiece:training_post[facing=south]")
    # Rayleigh's beach camp
    RX, RZ = 60, 86
    for k in range(3):
        for x in range(RX, RX + 6): b.set(x, 1 + k, RZ + k, "minecraft:brown_wool"); b.set(x, 1 + k, RZ + 6 - k, "minecraft:brown_wool")
    b.set(RX + 3, 1, RZ + 3, "minecraft:white_bed[facing=east,occupied=false,part=foot]"); b.set(RX + 4, 1, RZ + 3, "minecraft:white_bed[facing=east,occupied=false,part=head]")
    b.set(RX - 3, 1, RZ + 3, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"); b.set(RX - 4, 1, RZ + 1, "onepiece:sake_barrel")
    # ---------------- loot and beasts
    b.chest(TX + 3, 1, TZ - 10, "hard", "west"); b.chest(84, 2, 74, "hard", "north"); b.chest(MX, 37, MZ, "medium", "south")
    b.guards("war_beast", ((84, 70), (88, 16), (34, 12), (46, 70), (MX - 20, MZ)))
    return b, 0
