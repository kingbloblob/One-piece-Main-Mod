"""The Davy Back Fight on Long Ring Long Land: Foxy the Silver Fox's games grounds on the stretched-out island of
long grass and tall, thin trees. The Groggy Ring pitch with goal rings and grandstands full of Foxy Pirates, the
Combat boxing ring under fairground lights, the start of the Donut Race on the shore, food and game stalls,
Foxy's big striped command tent (furnished like a party hall), the crew's tents, and the Sexy Foxy moored at the
shore. ~104 x 80. Ground = y 0, sea to the south."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "davy_back_stage"
TITLE = "Davy Back Fight Arena (Long Ring Long Land)"
CUTS = [2]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 104, 80
SEA_Z = 66
FOXY = dict(wood="acacia", rug="red", rug2="yellow", bed="red", light="minecraft:lantern", accent="minecraft:orange_glazed_terracotta",
            banner="orange", candle="orange")


def grandstand(b, x0, x1, z, rows, facing, color):
    """Stepped wooden seats rising away from the pitch, with a striped awning."""
    dz = -1 if facing == "south" else 1
    for r in range(rows):
        zz = z + dz * r * 1
        for x in range(x0, x1 + 1):
            for y in range(0, r + 1): b.set(x, y, zz, "minecraft:acacia_planks")
            b.set(x, r + 1, zz, f"minecraft:acacia_stairs[facing={'north' if facing == 'south' else 'south'},half=bottom,shape=straight,waterlogged=false]" if False else
                  f"minecraft:acacia_slab[type=bottom,waterlogged=false]")
    zb = z + dz * rows
    for x in range(x0, x1 + 1, 4): b.column(x, zb, rows + 1, rows + 6, "minecraft:stripped_acacia_log[axis=y]")
    for x in range(x0, x1 + 1):
        for k in range(rows):
            b.set(x, rows + 6 - k // 2, zb - dz * k, f"minecraft:{color}_wool" if (x // 2) % 2 else "minecraft:white_wool")


def build():
    rnd = random.Random(441)
    b = B()
    T.ground(b, NX, NZ, rnd, deco=0.3, decos=("minecraft:tall_grass[half=lower]", "minecraft:short_grass", "minecraft:short_grass", "minecraft:dandelion"))
    for x in range(NX):
        for z in range(NZ):
            if b.get(x, 1, z) == "minecraft:tall_grass[half=lower]": b.set(x, 2, z, "minecraft:tall_grass[half=upper]")
    T.sea(b, NX, NZ, lambda x, z: z > SEA_Z + math.sin(x * 0.1) * 2, depth=6)
    # the long, thin trees of Long Ring Long Land
    for i in range(24):
        x, z = rnd.randint(2, NX - 3), rnd.randint(2, 10)
        h = rnd.randint(16, 24)
        for y in range(1, h): b.set(x, y, z, "minecraft:birch_log[axis=y]")
        b.sphere(x, h, z, 1.8, "minecraft:birch_leaves[distance=7,persistent=true,waterlogged=false]", ry=3.5)
    # ---------------- the Groggy Ring pitch
    PX0, PX1, PZ0, PZ1 = 16, 72, 20, 46
    for x in range(PX0, PX1 + 1):
        for z in range(PZ0, PZ1 + 1):
            b.set(x, 0, z, "minecraft:grass_block" if ((x - PX0) // 4) % 2 else "minecraft:moss_block")
            for y in (1, 2): b.set(x, y, z, AIR)
            if x in (PX0, PX1) or z in (PZ0, PZ1) or x == (PX0 + PX1) // 2: b.set(x, 0, z, "minecraft:white_concrete")
    for gx in (PX0 + 2, PX1 - 2):  # the goal rings on tall posts
        gz = (PZ0 + PZ1) // 2
        b.column(gx, gz, 1, 9, "minecraft:stripped_acacia_log[axis=y]")
        for a in range(0, 360, 20):
            t = math.radians(a)
            b.set(gx, round(12 + 3 * math.sin(t)), round(gz + 3 * math.cos(t)), "minecraft:orange_concrete")
    grandstand(b, PX0, PX1, PZ0 - 1, 6, "south", "orange")
    grandstand(b, PX0, PX1, PZ1 + 1, 4, "north", "red")
    # the commentators' booth with Itomimizu's microphone
    b.box(42, 11, PZ0 - 9, 46, 11, PZ0 - 6, "minecraft:acacia_planks"); b.walls(42, 12, PZ0 - 9, 46, 14, PZ0 - 6, "minecraft:acacia_planks")
    b.box(43, 12, PZ0 - 8, 45, 14, PZ0 - 7, AIR); b.set(44, 13, PZ0 - 6, "minecraft:glass_pane"); b.set(43, 12, PZ0 - 7, "onepiece:den_den_relay[facing=south]")
    # ---------------- the Combat ring
    RX, RZ = 88, 32
    b.box(RX - 6, 1, RZ - 6, RX + 6, 2, RZ + 6, "minecraft:acacia_planks"); b.box(RX - 5, 3, RZ - 5, RX + 5, 3, RZ + 5, "minecraft:white_wool")
    for (dx, dz) in ((-5, -5), (5, -5), (-5, 5), (5, 5)): b.column(RX + dx, RZ + dz, 3, 7, "minecraft:red_concrete" if dx < 0 else "minecraft:blue_concrete")
    for k in range(-4, 5):
        for y in (5, 6):
            for (x, z) in ((RX + k, RZ - 5), (RX + k, RZ + 5), (RX - 5, RZ + k), (RX + 5, RZ + k)): b.set(x, y, z, "minecraft:white_carpet" if False else "minecraft:chain[axis=x,waterlogged=false]" if z in (RZ - 5, RZ + 5) else "minecraft:chain[axis=z,waterlogged=false]")
    for (dx, dz) in ((-8, -8), (8, -8), (-8, 8), (8, 8)):  # floodlight towers
        b.column(RX + dx, RZ + dz, 1, 12, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
        b.box(RX + dx - 1, 13, RZ + dz - 1, RX + dx + 1, 13, RZ + dz + 1, "minecraft:redstone_lamp[lit=true]")
    for x in range(RX - 9, RX + 10):  # ringside benches
        if abs(x - RX) > 7 or True:
            b.set(x, 1, RZ - 9, "minecraft:acacia_slab[type=bottom,waterlogged=false]"); b.set(x, 1, RZ + 9, "minecraft:acacia_slab[type=bottom,waterlogged=false]")
    # ---------------- Foxy's command tent
    TX0, TZ0, TX1, TZ1 = 76, 46, 98, 60
    for x in range(TX0, TX1 + 1):
        for z in range(TZ0, TZ1 + 1):
            b.set(x, 0, z, "minecraft:acacia_planks")
            for y in (1, 2): b.set(x, y, z, AIR)
    cxz = ((TX0 + TX1) / 2, (TZ0 + TZ1) / 2)
    for y in range(1, 13):
        k = max(0, y - 5)
        for x in range(TX0 + k, TX1 - k + 1):
            for z in range(TZ0 + k, TZ1 - k + 1):
                edge = x in (TX0 + k, TX1 - k) or z in (TZ0 + k, TZ1 - k)
                if edge: b.set(x, y, z, "minecraft:orange_wool" if (x + z) // 3 % 2 else "minecraft:white_wool")
    for z in range(TZ0 + 5, TZ0 + 10):
        for y in (1, 2, 3): b.set(TX0, y, z, AIR)
    b.set(round(cxz[0]), 13, round(cxz[1]), "minecraft:orange_wool")
    for y in range(13, 18): b.set(round(cxz[0]), y, round(cxz[1]), "minecraft:acacia_fence")
    b.jolly_roger(round(cxz[0]) + 1, 15, round(cxz[1]), 5, 3, axis="x")
    I.furnish(b, TX0 + 1, 1, TZ0 + 1, (TX0 + TX1) // 2, TZ1 - 1, 5, "tavern", FOXY, seed=51)
    I.furnish(b, (TX0 + TX1) // 2 + 1, 1, TZ0 + 1, TX1 - 1, TZ1 - 1, 5, "throne", FOXY, seed=52)
    # the crew's tents and the stalls of the fair
    for (x, z, c) in ((8, 52, "red"), (16, 54, "yellow"), (24, 52, "orange"), (32, 54, "red"), (40, 52, "yellow")):
        for dx in range(-2, 3):
            for dy in range(0, 3 - abs(dx)):
                for dz in range(0, 6): b.set(x + dx, 1 + dy, z + dz, f"minecraft:{c}_wool" if dy < 2 else "minecraft:white_wool")
        for dz in range(0, 6): b.set(x, 1, z + dz, AIR)
        b.set(x, 1, z + 3, f"minecraft:{c}_bed[facing=north,occupied=false,part=head]"); b.set(x, 1, z + 4, f"minecraft:{c}_bed[facing=north,occupied=false,part=foot]")
    goods = (("minecraft:cake[bites=0]", "minecraft:melon", None), ("onepiece:sake_barrel[axis=y]", "minecraft:barrel[facing=up,open=false]", None),
             ("minecraft:target[power=0]", "minecraft:hay_block[axis=y]", None), ("minecraft:pumpkin", "onepiece:mikan_crate", None))
    for i, x in enumerate(range(50, 74, 6)):
        T.stall(b, x, 52, ("red", "orange", "yellow", "white")[i], goods[i])
    for x in range(8, 74, 5):  # bunting strings
        b.set(x, 7, 50, lantern(True)); b.set(x + 1, 8, 50, "minecraft:orange_wool"); b.set(x + 3, 8, 50, "minecraft:yellow_wool")
    # ---------------- the Donut Race start on the shore and the Sexy Foxy
    for x in range(8, 40):
        b.set(x, 0, SEA_Z - 1, "minecraft:white_concrete" if x % 2 else "minecraft:black_concrete")
    T.pier(b, 50, SEA_Z - 2, 10, axis="z", boat=False)
    b.ship(52, -3, SEA_Z + 8, 30, 10, masts=((10, 16), (20, 14)), sail="minecraft:orange_wool", cabin=(6, 4, "minecraft:acacia_planks"))
    for (x, z) in ((14, 62), (30, 62)):  # race barrels-boats
        b.cyl(x, z + 6, 2, -1, 0, "minecraft:barrel[facing=up,open=false]")
    # ---------------- loot and Foxy's crew
    b.chest(TX1 - 2, 1, TZ1 - 2, "medium", "west"); b.chest(46, 12, PZ0 - 8, "easy", "west")
    b.guards("rookie_pirate", ((30, 33), (58, 33), (RX, RZ), (60, 56)), y=1)
    b.guards("pirate", ((TX0 + 4, TZ0 + 7),))
    return b, 0
