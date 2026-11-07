"""A Marine branch base (the 153rd at Shells Town style): a walled fortress of white walls and blue trim with the
great MARINE letters on the tower, the main keep with the commander's office, Garp's guest room, mess hall,
barracks and armory, a drill yard with training posts and a flagpole, the jail block, watchtowers on the
corners, a cannon battery and the harbour with a Marine sloop. ~96 x 88. Ground = y 0, the sea to the south."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "marine_base"
TITLE = "Marine Branch Base"
CUTS = [2, 7, 13]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 96, 88
WALL = "minecraft:white_concrete"
BLUE = "minecraft:light_blue_concrete"
TRIM = "minecraft:blue_concrete"
X0, Z0, X1, Z1 = 8, 6, 88, 64
MAR = dict(wood="birch", rug="light_blue", rug2="white", bed="light_blue", light="minecraft:lantern", accent="onepiece:marine_bricks",
           banner="light_blue", candle="white")


def tower(b, x, z, h):
    b.box(x - 3, 0, z - 3, x + 3, h, z + 3, WALL); b.box(x - 2, 1, z - 2, x + 2, h, z + 2, AIR)
    for y in range(4, h, 4): b.box(x - 2, y, z - 2, x + 2, y, z + 2, "minecraft:birch_planks"); b.set(x - 2, y, z, AIR)
    for y in range(1, h + 1): b.set(x - 2, y, z, "minecraft:ladder[facing=east,waterlogged=false]")
    b.box(x - 4, h + 1, z - 4, x + 4, h + 1, z + 4, TRIM)
    for dx in range(-4, 5):
        for dz in (-4, 4):
            if dx % 2 == 0: b.set(x + dx, h + 2, z + dz, WALL); b.set(x + dz, h + 2, z + dx, WALL)
    b.set(x, h + 2, z, "onepiece:cannon[facing=south]")
    for y in range(3, h, 4): b.set(x + 3, y, z, "minecraft:glass_pane"); b.set(x, y, z - 3, "minecraft:glass_pane")


def build():
    rnd = random.Random(661)
    b = B()
    T.ground(b, NX, NZ, rnd, deco=0.05)
    T.sea(b, NX, NZ, lambda x, z: z > 72, depth=6)
    for x in range(NX): b.set(x, 0, 71, "minecraft:stone_bricks"); b.set(x, 0, 72, "minecraft:stone_bricks")
    # ---------------- the curtain wall and corner towers
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            b.set(x, 0, z, "minecraft:smooth_stone" if (x + z) % 2 else "minecraft:polished_andesite")
    b.walls(X0, 1, Z0, X1, 8, Z1, WALL)
    for x in range(X0, X1 + 1):
        for z in (Z0, Z1):
            b.set(x, 6, z, BLUE); b.set(x, 9, z, WALL if x % 2 == 0 else AIR)
    for z in range(Z0, Z1 + 1):
        for x in (X0, X1):
            b.set(x, 6, z, BLUE); b.set(x, 9, z, WALL if z % 2 == 0 else AIR)
    for x in range(X0 + 1, X1):  # wall walk
        b.set(x, 8, Z0 + 1, "minecraft:birch_slab[type=top,waterlogged=false]"); b.set(x, 8, Z1 - 1, "minecraft:birch_slab[type=top,waterlogged=false]")
    GX = (X0 + X1) // 2
    for x in range(GX - 3, GX + 4):  # main gate
        for y in range(1, 7): b.set(x, y, Z1, AIR)
    for x in range(GX - 4, GX + 5): b.set(x, 7, Z1, TRIM)
    b.text(GX + 3, 8, Z1, "153", BLUE, step=-1) if False else None
    for (x, z) in ((X0, Z0), (X1, Z0), (X0, Z1), (X1, Z1)): tower(b, x, z, 16)
    # ---------------- the keep: four floors at the back
    KX0, KX1, KZ0, KZ1 = GX - 20, GX + 20, Z0 + 4, Z0 + 22
    b.box(KX0, 0, KZ0, KX1, 0, KZ1, "minecraft:birch_planks")
    b.walls(KX0, 1, KZ0, KX1, 20, KZ1, WALL)
    b.box(KX0 + 1, 1, KZ0 + 1, KX1 - 1, 20, KZ1 - 1, AIR)
    for fy in (5, 10, 15, 20): b.box(KX0 + 1, fy, KZ0 + 1, KX1 - 1, fy, KZ1 - 1, "minecraft:birch_planks")
    b.box(KX0 - 1, 21, KZ0 - 1, KX1 + 1, 21, KZ1 + 1, TRIM)
    for x in range(KX0, KX1 + 1):
        for fy in (5, 10, 15): b.set(x, fy, KZ1, BLUE); b.set(x, fy, KZ0, BLUE)
        if x % 3 == 0:
            for fy in (2, 7, 12, 17): b.set(x, fy, KZ1, "minecraft:glass_pane"); b.set(x, fy + 1, KZ1, "minecraft:glass_pane"); b.set(x, fy, KZ0, "minecraft:glass_pane")
    for x in range(GX - 2, GX + 3):
        for y in range(1, 5): b.set(x, y, KZ1, AIR)
    for x in range(GX - 3, GX + 4): b.set(x, 5, KZ1 + 1, TRIM); b.set(x, 5, KZ1 + 2, TRIM)
    # the big MARINE letters and the gull emblem on the keep
    b.text(GX - 8, 23, KZ1, "MARINE", BLUE)
    b.box(KX0, 22, KZ1, KX1, 30, KZ1, WALL) if False else None
    b.box(GX - 16, 22, KZ1 - 1, GX + 16, 30, KZ1 - 1, WALL)
    b.text(GX - 8, 23, KZ1, "MARINE", BLUE)
    for k in range(4):  # stairs between floors in the west end
        for i in range(5): b.set(KX0 + 2 + i, k * 5 + 1 + i, KZ0 + 2, stairs("minecraft:birch_stairs", "east"))
        for i in range(5): b.set(KX0 + 2 + i, (k + 1) * 5, KZ0 + 2, AIR) if i < 4 else None
        for i in range(4): b.set(KX0 + 2 + i, (k + 1) * 5, KZ0 + 3, "minecraft:birch_planks")
    I.subdivide(b, KX0 + 8, 1, KZ0 + 1, KX1 - 1, KZ1 - 1, 4, WALL, ("dining", "kitchen", "dining"), MAR, cell=10, seed=1)
    I.subdivide(b, KX0 + 8, 6, KZ0 + 1, KX1 - 1, KZ1 - 1, 4, WALL, ("barracks", "barracks", "armory"), MAR, cell=10, seed=2)
    I.subdivide(b, KX0 + 8, 11, KZ0 + 1, KX1 - 1, KZ1 - 1, 4, WALL, ("barracks", "library", "bath"), MAR, cell=10, seed=3)
    I.subdivide(b, KX0 + 8, 16, KZ0 + 1, KX1 - 1, KZ1 - 1, 4, WALL, ("study", "bedroom", "throne"), MAR, cell=12, seed=4)
    for y in range(22, 32): b.set(GX, y, KZ0 + 9, "minecraft:white_concrete" if y < 31 else "minecraft:light_blue_wool")
    for y in range(22, 32): b.set(GX, y + 1, KZ0 + 9, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]") if y > 30 else None
    # ---------------- the drill yard
    YZ = KZ1 + 6
    for x in range(GX - 14, GX + 15, 4):
        b.set(x, 1, YZ + 4, "onepiece:training_post[facing=north]"); b.set(x, 1, YZ + 10, "onepiece:training_post[facing=south]")
    for y in range(1, 22): b.set(GX, y, YZ + 16, "minecraft:white_concrete" if y < 4 else "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
    b.box(GX + 1, 17, YZ + 16, GX + 7, 21, YZ + 16, "minecraft:light_blue_wool"); b.box(GX + 3, 18, YZ + 16, GX + 5, 20, YZ + 16, "minecraft:white_wool")
    for (x, z) in ((GX - 18, YZ + 4), (GX + 18, YZ + 4)):
        b.set(x, 1, z, "minecraft:armor_stand") if False else b.set(x, 1, z, "minecraft:target")
    # ---------------- jail block (west) and the store sheds (east)
    b.box(X0 + 2, 0, Z0 + 26, X0 + 18, 0, Z0 + 46, "minecraft:stone_bricks")
    b.walls(X0 + 2, 1, Z0 + 26, X0 + 18, 6, Z0 + 46, "onepiece:marine_bricks"); b.box(X0 + 2, 7, Z0 + 26, X0 + 18, 7, Z0 + 46, "minecraft:stone_brick_slab[type=bottom,waterlogged=false]")
    b.box(X0 + 3, 1, Z0 + 27, X0 + 17, 6, Z0 + 45, AIR)
    for z in range(Z0 + 28, Z0 + 45, 4):
        for y in (1, 2, 3):
            for x in range(X0 + 3, X0 + 9): b.set(x, y, z, "onepiece:prison_bars")
        b.set(X0 + 4, 1, z + 2, "minecraft:white_bed[facing=east,occupied=false,part=foot]") if False else b.set(X0 + 4, 1, z + 2, "minecraft:hay_block[axis=y]")
        b.set(X0 + 6, 1, z + 1, "minecraft:cauldron")
    for z in range(Z0 + 28, Z0 + 45, 4):
        for y in (1, 2, 3): b.set(X0 + 9, y, z, "onepiece:prison_bars")
    for z in range(Z0 + 29, Z0 + 44, 4):
        for y in (1, 2, 3): b.set(X0 + 9, y, z + 1, "onepiece:prison_bars")
    I.furnish(b, X0 + 11, 1, Z0 + 27, X0 + 17, Z0 + 45, 5, "study", MAR, seed=5)
    for y in (1, 2, 3): b.set(X0 + 18, y, Z0 + 36, AIR)
    for i, z in enumerate((Z0 + 26, Z0 + 38)):
        T.house(b, X1 - 18, z, 14, 10, floors=1, style="marine", rnd=random.Random(i), kinds=("storage" if i else "workshop",), door="west")
    # ---------------- cannon battery on the sea wall and the harbour
    for x in range(10, NX - 10, 8):
        b.set(x, 1, 70, "onepiece:cannon[facing=south]"); b.set(x + 1, 1, 70, "minecraft:stone_brick_wall")
    T.pier(b, GX - 1, 72, 12, axis="z")
    T.path(b, [(GX, Z1), (GX, 70)], w=3, s="minecraft:polished_andesite")
    # ---------------- loot, Garp and the garrison
    b.chest(KX1 - 3, 16, KZ0 + 3, "marine", "west"); b.chest(X0 + 16, 1, Z0 + 44, "marine", "north"); b.chest(X1 - 6, 1, Z0 + 30, "medium", "west")
    b.npc(GX + 6, 16, KZ0 + 10, "garp", False)
    b.guards("marine", ((GX - 8, YZ + 7), (GX + 8, YZ + 7), (GX - 4, Z1 + 4), (GX + 4, Z1 + 4), (X0 + 12, Z0 + 36)))
    b.guards("marine_rifle", ((X0 + 2, Z0 + 1), (X1 - 2, Z1 - 1)), y=17)
    b.guards("elite_marine", ((GX, KZ1 + 3),))
    return b, 0
