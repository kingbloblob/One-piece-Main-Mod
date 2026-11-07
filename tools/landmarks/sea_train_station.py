"""Shift Station, the Puffing Tom's terminal on the edge of Water 7's sea: a brick station hall with a clock tower,
the covered platform with benches and lamps, the Puffing Tom itself (the paddle-wheel steam train that runs on
rails just under the sea), the tracks heading out over the water on trestles, Kokoro's house-bar next door,
the ticket office, the waiting room, the stationmaster's office and the coal yard and water tower.
~96 x 64. Ground = y 0, the sea to the east."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "sea_train_station"
TITLE = "Puffing Tom Station"
CUTS = [2, 9]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 96, 64
SEA_X = 56
TZ = 32  # track line
BRICK = "minecraft:bricks"
STA = dict(wood="spruce", rug="green", rug2="yellow", bed="green", light="minecraft:lantern", accent="minecraft:copper_block",
           banner="green", candle="yellow")


def puffing_tom(b, x0, z):
    """The locomotive and two carriages, facing +x, sitting on the rails at y 1."""
    L = 14
    b.box(x0, 1, z - 2, x0 + L, 1, z + 2, "minecraft:black_concrete")
    b.shape(lambda x, y, zz: (y - 4) ** 2 / 9 + (zz - z) ** 2 / 4 <= 1, x0 + 4, 2, z - 2, x0 + L, 7, z + 2, lambda *_: "minecraft:black_concrete", interior="minecraft:black_concrete")
    b.cyl(x0 + L + 0.5, z, 0, 3, 5, "minecraft:copper_block") if False else b.box(x0 + L + 1, 2, z - 1, x0 + L + 1, 5, z + 1, "minecraft:cut_copper")
    b.set(x0 + L + 2, 4, z, "minecraft:redstone_lamp[lit=true]")
    b.box(x0 + L - 3, 8, z - 1, x0 + L - 2, 10, z, "minecraft:black_concrete"); b.box(x0 + L - 3, 11, z - 1, x0 + L - 2, 11, z, "minecraft:cut_copper")
    b.set(x0 + L - 3, 12, z, "minecraft:campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
    b.walls(x0, 2, z - 2, x0 + 4, 7, z + 2, "minecraft:red_concrete"); b.box(x0 + 1, 2, z - 1, x0 + 3, 6, z + 1, AIR)
    b.box(x0, 8, z - 2, x0 + 4, 8, z + 2, "minecraft:black_concrete")
    for y in (4, 5): b.set(x0 + 2, y, z - 2, "minecraft:glass_pane"); b.set(x0 + 2, y, z + 2, "minecraft:glass_pane")
    b.set(x0 + 2, 2, z, "onepiece:ships_wheel[facing=east]"); b.set(x0 + 1, 2, z + 1, "minecraft:blast_furnace[facing=east,lit=true]")
    for dx in (5, 9, 13):  # the paddle wheels
        for side in (-3, 3):
            for a in range(0, 360, 30):
                t = math.radians(a)
                b.set(x0 + dx + round(2 * math.cos(t)), 3 + round(2 * math.sin(t)), z + side, "minecraft:red_concrete" if a % 60 else "minecraft:iron_block")
            b.set(x0 + dx, 3, z + side, "minecraft:iron_block")
    for c in range(2):  # carriages
        cx0 = x0 - 13 - c * 13
        b.box(cx0, 1, z - 2, cx0 + 11, 1, z + 2, "minecraft:black_concrete")
        b.walls(cx0, 2, z - 2, cx0 + 11, 6, z + 2, "minecraft:green_concrete"); b.box(cx0 + 1, 2, z - 1, cx0 + 10, 6, z + 1, AIR)
        b.box(cx0, 7, z - 2, cx0 + 11, 7, z + 2, "minecraft:dark_oak_slab[type=bottom,waterlogged=false]")
        for x in range(cx0 + 2, cx0 + 11, 2):
            b.set(x, 4, z - 2, "minecraft:glass_pane"); b.set(x, 4, z + 2, "minecraft:glass_pane")
            b.set(x, 2, z - 1, "minecraft:spruce_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
            b.set(x, 2, z + 1, "minecraft:spruce_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
        b.set(cx0 + 6, 6, z, lantern(True))
        for y in (2, 3): b.set(cx0 + 6, y, z - 2, AIR)


def build():
    rnd = random.Random(491)
    b = B()
    T.ground(b, NX, NZ, rnd, top="onepiece:water7_cobbles", deco=0)
    T.sea(b, NX, NZ, lambda x, z: x > SEA_X, depth=6)
    for z in range(NZ): b.set(SEA_X, 0, z, "onepiece:canal_bricks"); b.set(SEA_X, 1, z, "onepiece:canal_bricks") if z % 4 == 0 else None
    # ---------------- the track: on the ground through the station, then on trestles just under the sea surface
    for x in range(0, NX):
        for dz in (-2, -1, 0, 1, 2):
            if x <= SEA_X: b.set(x, 0, TZ + dz, "minecraft:gravel" if abs(dz) < 2 else "minecraft:polished_andesite")
        b.set(x, 0 if x > SEA_X else 1, TZ - 1, "minecraft:rail[shape=east_west,waterlogged=false]" if x <= SEA_X else "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=true]")
        b.set(x, 0 if x > SEA_X else 1, TZ + 1, "minecraft:rail[shape=east_west,waterlogged=false]" if x <= SEA_X else "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=true]")
        if x > SEA_X:
            b.set(x, -1, TZ, "minecraft:spruce_planks"); b.set(x, -1, TZ - 1, "minecraft:spruce_planks"); b.set(x, -1, TZ + 1, "minecraft:spruce_planks")
            if x % 6 == 0:
                for y in range(-6, -1): b.set(x, y, TZ - 2, "minecraft:spruce_log[axis=y]"); b.set(x, y, TZ + 2, "minecraft:spruce_log[axis=y]")
    puffing_tom(b, 40, TZ)
    # ---------------- the covered platform
    PZ0, PZ1 = TZ + 3, TZ + 9
    b.box(6, 1, PZ0, 54, 1, PZ1, "minecraft:polished_andesite")
    for x in range(6, 55, 6):
        b.column(x, PZ0, 2, 8, "minecraft:dark_oak_fence"); b.column(x, PZ1, 2, 8, "minecraft:dark_oak_log[axis=y]")
        b.set(x, 7, PZ0, lantern(True))
    for x in range(4, 57):
        for z in range(TZ - 3, PZ1 + 1): b.set(x, 9, z, "minecraft:green_terracotta" if (x // 2) % 2 else "minecraft:white_terracotta")
    for x in range(8, 54, 6):
        b.set(x + 2, 2, PZ1 - 1, "minecraft:spruce_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]"); b.set(x + 3, 2, PZ1 - 1, "minecraft:spruce_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
        b.set(x + 4, 2, PZ1 - 1, "minecraft:flower_pot") if x % 12 == 2 else None
    # ---------------- the station hall with the clock tower
    HX0, HX1, HZ0, HZ1 = 10, 44, PZ1 + 1, PZ1 + 16
    b.box(HX0, 1, HZ0, HX1, 1, HZ1, "minecraft:spruce_planks")
    b.walls(HX0, 2, HZ0, HX1, 11, HZ1, BRICK)
    b.box(HX0 + 1, 2, HZ0 + 1, HX1 - 1, 11, HZ1 - 1, AIR)
    for x in range(HX0, HX1 + 1, 5):
        for z in (HZ0, HZ1): b.column(x, z, 2, 11, "minecraft:stone_bricks")
    for x in range(HX0 + 2, HX1 - 1, 5):
        for z in (HZ0, HZ1):
            for y in range(4, 9): b.set(x, y, z, "minecraft:glass_pane"); b.set(x + 1, y, z, "minecraft:glass_pane")
            b.set(x, 9, z, "minecraft:stone_brick_stairs[facing=east,half=top,shape=straight,waterlogged=false]"); b.set(x + 1, 9, z, "minecraft:stone_brick_stairs[facing=west,half=top,shape=straight,waterlogged=false]")
    b.gable_roof(HX0 - 1, HZ0, HX1 + 1, HZ1, 12, "minecraft:deepslate_tile_stairs", "minecraft:deepslate_tiles", gable_wall=BRICK)
    for x in (26, 27, 28):
        for y in (2, 3, 4): b.set(x, y, HZ0, AIR); b.set(x, y, HZ1, AIR)
    b.box(HX0 + 1, 7, HZ0 + 1, HX1 - 1, 7, HZ0 + 5, "minecraft:spruce_planks")  # mezzanine office
    I.furnish(b, HX0 + 1, 2, HZ0 + 6, 24, HZ1 - 1, 5, "dining", STA, seed=91)  # waiting room
    I.furnish(b, 30, 2, HZ0 + 6, HX1 - 1, HZ1 - 1, 5, "storage", STA, seed=92)  # ticket office and luggage
    I.furnish(b, HX0 + 1, 8, HZ0 + 1, HX1 - 1, HZ0 + 5, 3, "study", STA, seed=93)
    for y in range(2, 8): b.set(HX0 + 1, y, HZ0 + 6, "minecraft:ladder[facing=south,waterlogged=false]")
    for x in range(30, HX1): b.set(x, 2, HZ0 + 6, "minecraft:spruce_slab[type=top,waterlogged=false]") if x % 3 else None  # ticket counter
    TX, TZW = HX1 - 3, HZ1 - 3  # clock tower
    b.box(TX - 3, 12, TZW - 3, TX + 3, 24, TZW + 3, BRICK); b.box(TX - 2, 12, TZW - 2, TX + 2, 24, TZW + 2, AIR)
    for (fx, fz) in ((TX, TZW + 3), (TX, TZW - 3), (TX + 3, TZW), (TX - 3, TZW)):
        b.set(fx, 21, fz, "minecraft:white_concrete"); b.set(fx, 20, fz, "minecraft:quartz_block")
        b.set(fx, 22, fz, "minecraft:white_concrete")
    b.hip_roof(TX - 3, TZW - 3, TX + 3, TZW + 3, 25, "minecraft:deepslate_tile_stairs", "minecraft:deepslate_tiles")
    b.set(TX, 22, TZW, "minecraft:bell[attachment=ceiling,facing=north,powered=false]")
    # ---------------- Kokoro's house-bar, the water tower and the coal yard
    T.house(b, 4, 4, 12, 9, 2, "brick", rnd, kinds=["tavern", "bedroom"], theme=STA, door="south", sign="minecraft:green_wool")
    WX, WZ = 30, 12
    for (dx, dz) in ((-2, -2), (2, -2), (-2, 2), (2, 2)): b.column(WX + dx, WZ + dz, 1, 10, "minecraft:dark_oak_log[axis=y]")
    b.cyl(WX, WZ, 3, 11, 15, "minecraft:spruce_planks", hollow=True); b.cyl(WX, WZ, 2, 12, 15, "minecraft:water[level=0]")
    b.cyl(WX, WZ, 3, 11, 11, "minecraft:spruce_planks")  # the tank's floor (without it the water poured through)
    b.cone(WX, 16, WZ, 3.5, 3, "minecraft:dark_oak_planks") if hasattr(b, "cone") else b.cyl(WX, WZ, 3.2, 16, 16, "minecraft:dark_oak_slab[type=bottom,waterlogged=false]")
    for x in range(WX, WX + 5): b.set(x, 11, WZ + 4, "minecraft:spruce_planks") if False else None
    for i in range(30):
        x, z = rnd.randint(36, 50), rnd.randint(6, 18)
        h = max(1, 3 - abs(x - 43) // 3)
        for y in range(1, h + 1): b.set(x, y, z, "minecraft:coal_block")
    T.path(b, [(27, HZ1 + 1), (27, NZ - 2)], w=2, s="onepiece:water7_cobbles")
    for x in range(8, 52, 8): T.lamp_post(b, x, HZ1 + 3)
    # ---------------- loot
    b.chest(HX1 - 2, 2, HZ0 + 8, "easy", "west"); b.chest(HX0 + 3, 8, HZ0 + 2, "galley", "east")
    return b, 0
