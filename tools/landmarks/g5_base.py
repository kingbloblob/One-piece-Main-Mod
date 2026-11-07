"""G-5, the rowdiest Marine base of the New World, on a snowy shore: a grey fortress wall with watchtowers and
cannons, the big HQ block with 'G-5' painted on it and the Marine gull, the barracks where Vice Admiral Vergo's
unruly soldiers live, the mess hall, the armory, the brig, the officers' quarters, a training yard and the frozen
dock with a Marine warship. ~104 x 96. Ground = y 0, sea to the south."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "g5_base"
TITLE = "G-5 Marine Base"
CUTS = [2, 9]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 104, 96
SEA_Z = 78
WALLB = "onepiece:marine_bricks"
GRAY = "minecraft:gray_concrete"
X0, X1, Z0, Z1 = 8, 96, 6, 72


def build():
    rnd = random.Random(541)
    b = B()
    T.ground(b, NX, NZ, rnd, top="minecraft:snow_block", deco=0.25, decos=("minecraft:snow[layers=1]", "minecraft:snow[layers=2]"))
    T.sea(b, NX, NZ, lambda x, z: z > SEA_Z, depth=7)
    for x in range(NX):
        for z in range(SEA_Z + 1, NZ):
            if rnd.random() < 0.35: b.set(x, 0, z, "minecraft:ice")
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1): b.set(x, 0, z, "minecraft:polished_andesite" if (x + z) % 9 else "minecraft:andesite")
            # (the parade ground)
    # ---------------- the fortress wall with watchtowers and cannons
    for x in range(X0, X1 + 1):
        for z in (Z0, Z1):
            for y in range(1, 10): b.set(x, y, z, GRAY if y < 9 else WALLB)
            b.set(x, 10, z, WALLB if x % 2 else AIR)
            b.set(x, 9, z + (1 if z == Z0 else -1), "minecraft:smooth_stone_slab[type=bottom,waterlogged=false]")
    for z in range(Z0, Z1 + 1):
        for x in (X0, X1):
            for y in range(1, 10): b.set(x, y, z, GRAY if y < 9 else WALLB)
            b.set(x, 10, z, WALLB if z % 2 else AIR)
    for x in range(X0, X1 + 1): b.set(x, 5, Z1, "minecraft:blue_concrete")
    for (tx, tz) in ((X0, Z0), (X1, Z0), (X0, Z1), (X1, Z1), ((X0 + X1) // 2, Z0)):
        b.box(tx - 3, 1, tz - 3, tx + 3, 16, tz + 3, GRAY); b.box(tx - 2, 1, tz - 2, tx + 2, 15, tz + 2, AIR)
        for y in range(1, 16): b.set(tx, y, tz - 2, "minecraft:ladder[facing=south,waterlogged=false]")
        b.box(tx - 4, 16, tz - 4, tx + 4, 16, tz + 4, WALLB)
        for k in range(-4, 5, 2):
            for (x, z) in ((tx + k, tz - 4), (tx + k, tz + 4), (tx - 4, tz + k), (tx + 4, tz + k)): b.set(x, 17, z, WALLB)
        b.set(tx, 17, tz, "onepiece:cannon[facing=south]" if tz == Z1 else "onepiece:cannon[facing=north]")
        b.set(tx + 2, 17, tz + 2, "minecraft:lantern[hanging=false,waterlogged=false]")
    GX = (X0 + X1) // 2  # the main gate onto the dock
    for x in range(GX - 3, GX + 4):
        for y in range(1, 7): b.set(x, y, Z1, AIR)
    for x in range(GX - 4, GX + 5): b.set(x, 7, Z1 + 1, WALLB)
    # ---------------- the HQ block with G-5 painted on it
    HX0, HX1, HZ0, HZ1 = 30, 74, 10, 30
    b.walls(HX0, 1, HZ0, HX1, 20, HZ1, "minecraft:light_gray_concrete")
    b.box(HX0 + 1, 1, HZ0 + 1, HX1 - 1, 20, HZ1 - 1, AIR)
    for y in (7, 14): b.box(HX0 + 1, y, HZ0 + 1, HX1 - 1, y, HZ1 - 1, "minecraft:smooth_stone")
    b.box(HX0, 21, HZ0, HX1, 21, HZ1, "minecraft:gray_concrete")
    for x in range(HX0, HX1 + 1):
        for y in (7, 14, 21): b.set(x, y, HZ1, "minecraft:blue_concrete")
    for x in range(HX0 + 2, HX1 - 1, 3):
        for y0 in (2, 9, 16):
            for y in (y0 + 1, y0 + 2): b.set(x, y, HZ1, "minecraft:glass_pane"); b.set(x, y, HZ0, "minecraft:glass_pane")
    for x in range(HX0 + 15, HX1 - 13):
        for y in range(22, 30): b.set(x, y, HZ1, "minecraft:light_gray_concrete")
    b.text(HX1 - 24, 23, HZ1 + 1, "G-5", "minecraft:blue_concrete")
    for x in range(HX0 + 1, HX0 + 14):
        for y in range(15, 21): b.set(x, y, HZ1, "minecraft:white_concrete") if False else None
    for x in range((HX0 + HX1) // 2 - 2, (HX0 + HX1) // 2 + 3):
        for y in range(1, 5): b.set(x, y, HZ1, AIR)
    for y in range(1, 21): b.set(HX0 + 1, y, HZ0 + 1, "minecraft:ladder[facing=south,waterlogged=false]")
    for y in (7, 14): b.set(HX0 + 1, y, HZ0 + 1, "minecraft:ladder[facing=south,waterlogged=false]")
    I.subdivide(b, HX0 + 1, 1, HZ0 + 1, HX1 - 1, HZ1 - 1, 5, "minecraft:light_gray_concrete", ("hall", "dining", "kitchen", "armory", "storage", "cell"), "marine", cell=11, corridor=3,
                keepout=((HX0 + 1, HZ0 + 1, HX0 + 3, HZ0 + 3),), seed=1)
    I.subdivide(b, HX0 + 1, 8, HZ0 + 1, HX1 - 1, HZ1 - 1, 5, "minecraft:light_gray_concrete", ("barracks", "barracks", "bath", "barracks", "barracks", "storage"), "marine", cell=11, corridor=3,
                keepout=((HX0 + 1, HZ0 + 1, HX0 + 3, HZ0 + 3),), seed=2)
    I.subdivide(b, HX0 + 1, 15, HZ0 + 1, HX1 - 1, HZ1 - 1, 5, "minecraft:light_gray_concrete", ("study", "bedroom", "library", "study", "bedroom", "treasure"), "marine", cell=11, corridor=3,
                keepout=((HX0 + 1, HZ0 + 1, HX0 + 3, HZ0 + 3),), seed=3)
    b.column(HX1 - 3, HZ0 + 3, 22, 34, "minecraft:white_concrete")  # the Marine flag
    b.box(HX1 - 2, 30, HZ0 + 3, HX1 + 5, 34, HZ0 + 3, "minecraft:white_wool"); b.box(HX1, 31, HZ0 + 3, HX1 + 3, 33, HZ0 + 3, "minecraft:blue_wool")
    # ---------------- barracks huts, mess hall, training yard and the brig
    for (x0, z0, kind) in ((14, 36, "barracks"), (14, 50, "barracks"), (78, 36, "kitchen"), (78, 50, "armory")):
        T.house(b, x0, z0, 12, 10, 1, "marine", rnd, kinds=[kind], theme="marine", door="east" if x0 < 50 else "west", flat_roof=False,
                plan="plain", addons=["porch"])  # clean barrack blocks: one plain roof and a porch, not a jumble of wings
    for x in range(36, 66, 4):  # training yard with dummies and racks
        for z in (42, 50): b.set(x, 1, z, "onepiece:training_post[facing=north]")
    for x in range(36, 66): b.set(x, 1, 58, "minecraft:spruce_fence") if x % 2 else None
    for (x, z) in ((36, 46), (64, 46)): b.set(x, 1, z, "minecraft:hay_block[axis=y]"); b.set(x, 2, z, "minecraft:target[power=0]")
    T.lamp_post(b, 34, 62); T.lamp_post(b, 70, 62)
    # ---------------- the frozen dock and a Marine warship
    T.pier(b, GX - 2, Z1 + 1, 12, axis="z", w=5, boat=False)
    b.ship(GX - 30, -3, SEA_Z + 9, 36, 12, masts=((10, 18), (24, 20)), sail="minecraft:white_wool", cabin=(7, 4, "minecraft:birch_planks"))
    for x in range(GX - 28, GX + 4, 3): b.set(x, 6, SEA_Z + 9, "minecraft:blue_wool") if False else None
    # ---------------- loot and Marines
    b.chest(HX0 + 3, 15, HZ1 - 3, "marine", "east"); b.chest(HX1 - 3, 1, HZ0 + 3, "hard", "west")
    b.guards("elite_marine", ((GX, 36), (GX - 6, 40), (GX + 6, 40)))
    b.guards("marine_rifle", ((X0, Z0), (X1, Z0), (X0, Z1), (X1, Z1)), y=17)
    b.guards("marine", ((GX - 3, Z1 - 3), (GX + 3, Z1 - 3), (40, 46), (60, 46)))
    T.landscape(b, 0, 0, NX - 1, NZ - 1, rnd, amp=4, cell=16, edge=8)  # the open snow rolls (guide 9b.1, 11a); last, so it knows where everything stands
    return b, 0
