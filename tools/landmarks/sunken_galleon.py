"""A sunken treasure galleon on the sea floor: a great three-masted galleon broken in two and lying on its side in
the sand, its masts snapped, sails rotted to rags, coral and kelp growing over the timbers. The stern castle
still holds the captain's cabin with its treasure, the gun deck has rows of rusted cannons, chests and barrels
spill out of the torn hold onto the sand, and a ring of sea lanterns marks the wreck. Fish-Men pick over it.
Sea floor = y 0; everything inside is flooded."""
import math, random
from canvas import *
import interiors as I

SID = "sunken_galleon"
TITLE = "Sunken Treasure Galleon"
CUTS = [3, 8]
TILER = dict(heightmap="OCEAN_FLOOR_WG", terrain="none")

NX, NZ = 76, 44
CZ = 20
WRECK = dict(wood="dark_oak", rug="cyan", rug2="brown", bed="brown", light="minecraft:sea_lantern", accent="minecraft:prismarine",
             banner="cyan", candle="cyan")
ROT = ("minecraft:dark_oak_planks", "minecraft:spruce_planks", "minecraft:stripped_dark_oak_log[axis=x]", "minecraft:mud_bricks", "minecraft:dark_oak_planks")


def build():
    rnd = random.Random(781)
    b = B()
    for x in range(NX):
        for z in range(NZ):
            for y in (-3, -2, -1): b.set(x, y, z, "minecraft:sandstone")
            b.set(x, 0, z, "minecraft:sand" if rnd.random() > 0.15 else rnd.choice(("minecraft:gravel", "minecraft:clay")))
    # two hull halves, tilted (listing to the south) and broken apart
    for (x0, L, tilt, dx) in ((4, 36, 0.35, 0), (44, 28, -0.2, 0)):
        hw = b.hull(x0, L, CZ, 14, 1, 9, "minecraft:dark_oak_planks", bottom="minecraft:spruce_planks", rail="minecraft:dark_oak_fence",
                    bow_len=10 if x0 > 20 else 3, stern_len=6 if x0 < 20 else 2, fill_deck="minecraft:spruce_planks", waterline=None)
        for k, v in list(b.blocks.items()):  # list the half over and rot it
            x, y, z = k
            if not (x0 <= x < x0 + L) or y < 1: continue
            if rnd.random() < 0.08: b.blocks[k] = AIR
            elif v.startswith("minecraft:dark_oak_planks") and rnd.random() < 0.3: b.blocks[k] = rnd.choice(ROT)
        b.set(x0 + L // 2, 9, CZ, "minecraft:dark_oak_planks")
    for x in range(40, 44):  # the break: splintered timbers
        for z in range(CZ - 6, CZ + 7):
            if rnd.random() < 0.4: b.set(x, rnd.randint(1, 5), z, rnd.choice(ROT + ("minecraft:dark_oak_fence",)))
    # decks inside
    for x in range(10, 40):
        for z in range(CZ - 5, CZ + 6): b.set(x, 4, z, "minecraft:spruce_planks" if rnd.random() > 0.1 else AIR)
    for x in range(14, 38, 4):
        for side in (-1, 1): b.set(x, 5, CZ + side * 5, f"onepiece:cannon[facing={'south' if side > 0 else 'north'}]")
    # stern castle: the captain's cabin
    b.walls(4, 10, CZ - 5, 14, 15, CZ + 5, "minecraft:dark_oak_planks"); b.box(5, 10, CZ - 4, 13, 15, CZ + 4, WATER)
    b.box(4, 16, CZ - 5, 14, 16, CZ + 5, "minecraft:spruce_planks")
    for z in range(CZ - 3, CZ + 4, 2): b.set(4, 13, z, "minecraft:glass_pane")
    b.set(14, 10, CZ, WATER); b.set(14, 11, CZ, WATER)
    I.furnish(b, 5, 10, CZ - 4, 13, CZ + 4, 5, "captain", WRECK, lit=False)
    # snapped masts lying on the sand, rags of sail
    b.cyl(22, CZ, 0.8, 9, 18, "minecraft:dark_oak_log[axis=y]")
    b.line((50, 1, CZ + 8), (68, 1, CZ + 20), "minecraft:dark_oak_log[axis=x]")
    b.line((30, 10, CZ), (34, 1, CZ + 18), "minecraft:dark_oak_log[axis=z]")
    for (x, z) in ((32, CZ + 12), (33, CZ + 14), (31, CZ + 16), (56, CZ + 14), (60, CZ + 16)):
        for dy in range(rnd.randint(1, 3)): b.set(x + dy, 1 + dy, z, "minecraft:white_wool" if rnd.random() > 0.4 else "minecraft:light_gray_wool")
    # treasure spilling out onto the sand
    for i in range(18):
        x, z = rnd.randint(34, 50), rnd.randint(CZ - 14, CZ - 8)
        b.set(x, 1, z, rnd.choice(("minecraft:gold_block", "minecraft:barrel[facing=up,open=false]", "minecraft:raw_gold_block", "onepiece:berry_block", "minecraft:barrel[facing=east,open=false]")))
    # coral and kelp over the wreck, sea lanterns round it
    for i in range(140):
        x, z = rnd.randint(1, NX - 2), rnd.randint(1, NZ - 2)
        if b.get(x, 1, z) not in (None, AIR): continue
        b.set(x, 1, z, rnd.choice(("minecraft:tube_coral", "minecraft:brain_coral", "minecraft:fire_coral", "minecraft:horn_coral", "minecraft:seagrass", "minecraft:seagrass", "minecraft:sea_pickle[pickles=3,waterlogged=true]")))
    for i in range(30):
        x, z = rnd.randint(1, NX - 2), rnd.randint(1, NZ - 2)
        h = rnd.randint(3, 10)
        if b.get(x, 1, z) not in (None, AIR): continue
        for y in range(1, h): b.set(x, y, z, "minecraft:kelp_plant")
        b.set(x, h, z, "minecraft:kelp[age=20]")
    for k, v in list(b.blocks.items()):
        if k[1] > 0 and rnd.random() < 0.03 and "planks" in v: b.blocks[k] = rnd.choice(("minecraft:tube_coral_block", "minecraft:brain_coral_block", "minecraft:prismarine"))
    for a in range(0, 360, 30):
        t = math.radians(a); b.set(round(38 + 34 * math.cos(t)), 0, round(CZ + 18 * math.sin(t)), "minecraft:sea_lantern")
    # ---------------- flood every space inside the build
    for k, v in list(b.blocks.items()):
        if v == AIR: b.blocks[k] = WATER
    b.chest(8, 10, CZ, "treasure", "east"); b.chest(42, 1, CZ - 10, "easy", "north"); b.chest(26, 5, CZ, "treasure", "south")
    b.guards("fishman", ((40, CZ - 12), (60, CZ)), y=1)
    return b, 0
