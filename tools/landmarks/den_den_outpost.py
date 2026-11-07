"""A Marine Den Den Mushi relay outpost: a lonely signal station on a headland that passes the Marines' calls
across the sea. A stone signal tower carrying a giant Den Den Mushi relay snail in its glass lantern room, the
radio room full of snails and receivers, the operators' bunkhouse and mess, a supply shed, snail pens with
lettuce beds, the antenna mast and a small landing jetty. ~64 x 56. Ground = y 0, the sea to the east."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "den_den_outpost"
TITLE = "Den Den Mushi Relay Outpost"
CUTS = [2, 8, 18]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 64, 56
MAR = dict(wood="birch", rug="light_blue", rug2="white", bed="light_blue", light="minecraft:lantern", accent="onepiece:den_den_relay",
           banner="light_blue", candle="white")


def build():
    rnd = random.Random(711)
    b = B()
    T.ground(b, NX, NZ, rnd, deco=0.1)
    T.sea(b, NX, NZ, lambda x, z: x > 50 + 2 * math.sin(z * 0.25), depth=5)
    # ---------------- the signal tower
    TX, TZ = 24, 22
    b.cyl(TX, TZ, 5, 0, 22, "minecraft:stone_bricks"); b.cyl(TX, TZ, 4, 1, 22, AIR)
    for y in (6, 12, 18): b.cyl(TX, TZ, 4, y, y, "minecraft:birch_planks"); b.cyl(TX, TZ, 5.3, y, y, "minecraft:light_blue_concrete", hollow=True)
    for y in range(1, 23):  # spiral ladder up the inside
        a = math.radians(y * 40)
        b.set(round(TX + 3 * math.cos(a)), y, round(TZ + 3 * math.sin(a)), "minecraft:birch_slab[type=top,waterlogged=false]")
    for y in (6, 12, 18):
        b.set(TX + 3, y, TZ, AIR); b.set(TX + 2, y, TZ, AIR); b.set(TX + 3, y, TZ + 1, AIR)
    for (dx, dz) in ((5, 0), (-5, 0), (0, 5), (0, -5)):
        for y in (3, 9, 15): b.set(TX + dx, y, TZ + dz, "minecraft:glass_pane"); b.set(TX + dx, y + 1, TZ + dz, "minecraft:glass_pane")
    b.set(TX, 1, TZ + 5, AIR); b.set(TX, 2, TZ + 5, AIR)
    I.furnish(b, TX - 3, 7, TZ - 3, TX + 3, TZ + 3, 4, "study", MAR, seed=1)
    I.furnish(b, TX - 3, 13, TZ - 3, TX + 3, TZ + 3, 4, "lab", MAR, seed=2)
    b.cyl(TX, TZ, 6, 23, 23, "minecraft:white_concrete")
    b.cyl(TX, TZ, 5, 24, 29, "minecraft:glass", hollow=True); b.cyl(TX, TZ, 6, 30, 30, "minecraft:light_blue_concrete")
    b.dome(TX, TZ, 31, 5, h=4, s="minecraft:light_blue_concrete", tip="minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    # the giant relay snail in the lantern room
    b.shape(lambda x, y, z: ((x - TX) / 3.2) ** 2 + ((y - 27) / 3) ** 2 + ((z - TZ) / 3.2) ** 2 < 1, TX - 4, 24, TZ - 4, TX + 4, 30, TZ + 4, "minecraft:orange_terracotta", interior=None)
    for (dx, dz) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)): b.set(TX + dx, 27, TZ + dz, "minecraft:yellow_terracotta") if False else None
    b.box(TX - 3, 24, TZ + 2, TX + 3, 24, TZ + 3, "minecraft:white_terracotta")
    b.set(TX + 2, 25, TZ + 3, "minecraft:white_terracotta"); b.set(TX + 2, 26, TZ + 3, "minecraft:end_rod[facing=up]"); b.set(TX - 2, 26, TZ + 3, "minecraft:end_rod[facing=up]") if False else None
    b.set(TX, 24, TZ - 4, "onepiece:den_den_relay")
    # the antenna mast
    MX, MZ = 40, 10
    for y in range(1, 30): b.set(MX, y, MZ, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]" if y > 3 else "minecraft:iron_block")
    for y in range(8, 30, 6):
        for d in (-2, -1, 1, 2): b.set(MX + d, y, MZ, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]"); b.set(MX, y, MZ + d, "minecraft:iron_bars[east=false,north=true,south=true,west=false,waterlogged=false]")
    b.set(MX, 30, MZ, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    # ---------------- bunkhouse with radio room, supply shed, snail pens
    T.house(b, 6, 34, 14, 10, floors=2, style="marine", rnd=random.Random(1), kinds=("lab", "barracks"), door="north")
    T.house(b, 30, 38, 10, 8, floors=1, style="marine", rnd=random.Random(2), kinds=("kitchen",), door="north")
    T.house(b, 4, 6, 9, 8, floors=1, style="stone", rnd=random.Random(3), kinds=("storage",), door="east")
    for (x0, z0) in ((34, 22), (34, 28)):  # snail pens with lettuce
        b.box(x0, 1, z0, x0 + 8, 1, z0 + 4, "minecraft:birch_fence"); b.box(x0 + 1, 1, z0 + 1, x0 + 7, 1, z0 + 3, AIR)
        b.box(x0 + 1, 0, z0 + 1, x0 + 7, 0, z0 + 3, "minecraft:farmland[moisture=7]")
        for x in range(x0 + 1, x0 + 8): b.set(x, 1, z0 + 2, "minecraft:carrots[age=7]" if x % 2 else "minecraft:beetroots[age=3]")
        b.set(x0 + 2, 1, z0 + 1, "minecraft:orange_terracotta"); b.set(x0 + 6, 1, z0 + 3, "minecraft:pink_terracotta")
    T.pier(b, 49, 24, 12, axis="x")
    T.path(b, [(TX, TZ + 6), (TX, 32), (48, 26)], w=1, s="minecraft:gravel")
    T.path(b, [(TX - 6, TZ), (12, TZ), (12, 14)], w=1, s="minecraft:gravel")
    # ---------------- loot and the recruit
    b.chest(TX + 2, 7, TZ - 2, "easy", "west"); b.chest(6, 1, 9, "easy", "east")
    b.guards("marine_recruit", ((TX + 2, TZ + 8), (36, 34)))
    return b, 0
