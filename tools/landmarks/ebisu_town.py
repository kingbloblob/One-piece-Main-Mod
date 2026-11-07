"""Ebisu Town in Wano: the poorest town in the land, where everyone smiles because of the fake SMILE fruit.
Patched shacks and lean-tos of grey boards and straw along a muddy lane by a polluted river, the dango stall of
little Toko, Kyoshiro's gambling den, a soup kitchen, the tiny shrine, laundry lines and broken carts, and the
grave mound of Kozuki Oden's retainers on the hill. ~84 x 80. Ground = y 0, the river to the south."""
import math, random
from canvas import *
import interiors as I
import townkit as T
import kamazo_hideout as KH

SID = "ebisu_town"
TITLE = "Ebisu Town (Wano)"
CUTS = [3]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 84, 80
RIVER_Z = 66
POOR = dict(wood="spruce", rug="brown", rug2="gray", bed="brown", light="onepiece:paper_lantern[hanging=true]", accent="minecraft:hay_block[axis=y]",
            banner="gray", candle="white")


def shack(b, x0, z0, w, d, rnd, kind, door="south"):
    wood = rnd.choice(("minecraft:stripped_spruce_log[axis=y]", "minecraft:spruce_planks", "minecraft:stripped_oak_log[axis=y]", "minecraft:mud_bricks"))
    b.box(x0, 0, z0, x0 + w - 1, 0, z0 + d - 1, "minecraft:coarse_dirt")
    b.walls(x0, 1, z0, x0 + w - 1, 4, z0 + d - 1, wood)
    b.box(x0 + 1, 1, z0 + 1, x0 + w - 2, 4, z0 + d - 2, AIR)
    for i in range(4):  # patches
        b.set(rnd.randint(x0, x0 + w - 1), rnd.randint(1, 4), rnd.choice((z0, z0 + d - 1)), rnd.choice(("minecraft:oak_planks", "minecraft:birch_planks", "minecraft:hay_block[axis=y]")))
    for x in range(x0 - 1, x0 + w + 1):  # slumped straw roof
        for z in range(z0 - 1, z0 + d + 1):
            y = 5 + (1 if z0 + 1 < z < z0 + d - 2 else 0)
            b.set(x, y, z, ("minecraft:hay_block[axis=y]", "minecraft:spruce_slab[type=bottom,waterlogged=false]", "minecraft:dark_oak_slab[type=bottom,waterlogged=false]",
                            "minecraft:spruce_slab[type=bottom,waterlogged=false]")[(x * 3 + z * 7 + x0) % 4])
    fz = z0 + d - 1 if door == "south" else z0
    mx = x0 + w // 2
    for y in (1, 2): b.set(mx, y, fz, AIR)
    b.set(mx + 1, 2, fz, "minecraft:spruce_trapdoor[facing=north,half=top,open=true,powered=false,waterlogged=false]")
    I.furnish(b, x0 + 1, 1, z0 + 1, x0 + w - 2, z0 + d - 2, 3, kind, POOR, seed=x0 * 5 + z0)


def build():
    rnd = random.Random(581)
    b = B()
    T.ground(b, NX, NZ, rnd, top="minecraft:coarse_dirt", deco=0.05, decos=("minecraft:dead_bush", "minecraft:short_grass"))
    for x in range(NX):
        for z in range(NZ):
            if (x * 7 + z * 3) % 6 == 0: b.set(x, 0, z, "minecraft:mud")
    T.sea(b, NX, NZ, lambda x, z: z > RIVER_Z + 2 * math.sin(x * 0.12) and z < RIVER_Z + 10, depth=3, floor="minecraft:mud")
    for x in range(NX):  # the polluted river is murky
        for z in range(RIVER_Z, RIVER_Z + 11):
            if b.get(x, -1, z) == WATER and (x + z) % 4 == 0: b.set(x, -2, z, "minecraft:soul_soil")
    # the muddy main lane and side lanes
    T.path(b, [(2, 40), (NX - 3, 40)], w=2, s="minecraft:mud", alt="minecraft:packed_mud")
    T.path(b, [(30, 6), (30, RIVER_Z)], w=1, s="minecraft:mud", alt="minecraft:coarse_dirt")
    T.path(b, [(58, 6), (58, RIVER_Z)], w=1, s="minecraft:mud", alt="minecraft:coarse_dirt")
    kinds = ("kitchen", "bedroom", "storage", "bedroom", "dining", "bedroom", "workshop", "kitchen", "bedroom", "storage", "bedroom", "dining")
    k = 0
    for z0, door in ((30, "south"), (44, "north"), (18, "south"), (54, "north")):
        for x0 in range(4, NX - 9, 9):
            if abs(x0 + 3 - 30) < 5 or abs(x0 + 3 - 58) < 5: continue
            w, d = rnd.randint(6, 8), rnd.randint(6, 8)
            shack(b, x0, z0, w, d, rnd, kinds[k % len(kinds)], door=door); k += 1
    # Toko's dango stall and the soup kitchen on the lane
    T.stall(b, 34, 37, "red", ("minecraft:cake[bites=3]", "minecraft:pumpkin_pie" if False else "minecraft:hay_block[axis=y]", None))
    T.stall(b, 50, 37, "white", ("minecraft:cauldron", "minecraft:barrel[facing=up,open=false]", None))
    for x in range(36, 50, 3): b.set(x, 1, 38, "minecraft:spruce_slab[type=bottom,waterlogged=false]")
    # Kyoshiro's gambling den: a bigger, nicer house at the east end
    cx, cz = KH.wano_house(b, 66, 4, 80, 14, 4, roof_layers=1, door_side="south")
    I.furnish(b, 67, 2, 5, 79, 13, 4, "tavern", "wano", seed=9)
    # laundry lines, broken carts, the shrine and the grave mound
    for (x, z) in ((10, 26), (40, 50), (70, 26)):
        b.column(x, z, 1, 3, "minecraft:spruce_fence"); b.column(x + 6, z, 1, 3, "minecraft:spruce_fence")
        for xx in range(x + 1, x + 6): b.set(xx, 3, z, rnd.choice(("minecraft:white_carpet", "minecraft:light_blue_carpet", "minecraft:brown_carpet", "minecraft:white_banner[rotation=0]" if False else "minecraft:gray_carpet")))
    for (x, z) in ((24, 36), (62, 46)):
        b.set(x, 1, z, "minecraft:spruce_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]"); b.set(x + 1, 1, z, "minecraft:spruce_slab[type=bottom,waterlogged=false]")
        b.set(x + 2, 1, z, "minecraft:spruce_trapdoor[facing=east,half=bottom,open=true,powered=false,waterlogged=false]")
    b.box(6, 0, 6, 12, 0, 12, "minecraft:stone_bricks"); b.box(8, 1, 8, 10, 3, 10, "minecraft:red_concrete"); b.box(8, 2, 8, 10, 2, 10, AIR)
    b.set(9, 1, 8, AIR); b.set(9, 2, 9, "minecraft:candle[candles=3,lit=true,waterlogged=false]"); b.set(9, 4, 9, "onepiece:wano_roof_tiles")
    for x in range(7, 12): b.set(x, 4, 8, "onepiece:wano_roof_tile_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]") if False else b.set(x, 4, 8, "onepiece:wano_roof_tiles")
    gx, gz = 44, 8
    b.sphere(gx, -1, gz, 5, "minecraft:coarse_dirt", ry=3)
    for (dx, dz) in ((-2, 0), (0, 0), (2, 0), (-1, 2), (1, 2)): b.column(gx + dx, gz + dz, 2, 3 + (dx == 0), "minecraft:stone_brick_wall")
    # a rickety footbridge over the river
    for z in range(RIVER_Z - 1, RIVER_Z + 12):
        for x in (43, 44, 45): b.set(x, 1, z, "minecraft:spruce_planks" if z % 3 else "minecraft:oak_planks")
        if z % 3 == 0: b.set(42, 2, z, "minecraft:spruce_fence"); b.set(46, 2, z, "minecraft:spruce_fence")
    for x in range(4, NX - 4, 12): T.lamp_post(b, x, 42)
    # ---------------- loot
    b.chest(70, 2, 6, "wano", "east"); b.chest(9, 1, 10, "easy", "north")
    return b, 0
