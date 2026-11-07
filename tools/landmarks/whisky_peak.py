"""Whisky Peak: the 'welcoming' town of music and liquor at the entrance of the Grand Line, really a Baroque Works
bounty-hunter nest. Giant cactus-shaped rock spires (covered in the graves of pirates) surround a stone town with
banners and lanterns strung across the streets, the huge party hall where the welcome feast is thrown, its bar
and kitchens, the mayor Igaram's house, inns and bars, and the river harbour. ~96 x 96. Ground = y 0."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "whisky_peak"
TITLE = "Whisky Peak"
CUTS = [3]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 96
CX, CZ = 50, 48
WARM = dict(wood="spruce", rug="orange", rug2="yellow", bed="orange", light="minecraft:lantern", accent="minecraft:cut_red_sandstone",
            banner="orange", candle="orange")


def cactus_rock(b, x, z, h, r, rnd):
    for y in range(0, h):
        rr = r * (1 - 0.15 * y / h)
        b.cyl(x, z, rr, y, y, "minecraft:terracotta" if (y // 3) % 2 else "minecraft:green_terracotta")
    b.sphere(x, h, z, r * 0.85, "minecraft:green_terracotta", upper=True)
    for side in (-1, 1):  # the arms
        ay = rnd.randint(h // 3, h // 2); al = rnd.randint(3, 5)
        for k in range(1, int(r) + al):
            b.cyl(x + side * k, z, max(1.2, r * 0.45), ay, ay + 1, "minecraft:green_terracotta")
        b.cyl(x + side * (int(r) + al), z, max(1.2, r * 0.45), ay, ay + rnd.randint(5, 9), "minecraft:green_terracotta")
    for i in range(int(h * 1.5)):  # gravestones crowd the rock
        a = rnd.uniform(0, 2 * math.pi); y = rnd.randint(2, h - 2)
        rr = r * (1 - 0.15 * y / h) + 1
        gx, gz = round(x + rr * math.cos(a)), round(z + rr * math.sin(a))
        if b.get(gx, y - 1, gz) is not None and b.get(gx, y, gz) is None: b.set(gx, y, gz, "minecraft:stone_brick_wall")


def build():
    rnd = random.Random(271)
    b = B()
    T.ground(b, N, N, rnd, top="minecraft:red_sand", deco=0.02, decos=("minecraft:dead_bush", "minecraft:cactus"))
    # river through the west side, with a little harbour
    T.sea(b, N, N, lambda x, z: abs(x - 8 - 3 * math.sin(z * 0.1)) < 4, depth=3)
    for (x, z, h, r) in ((20, 14, 34, 5), (82, 12, 40, 6), (88, 50, 30, 5), (78, 86, 36, 5), (22, 84, 28, 4), (50, 8, 26, 4), (12, 50, 24, 4)):
        cactus_rock(b, x, z, h, r, rnd)
    # town streets: sandstone paving in a cross with the plaza
    for x in range(14, N - 6):
        for z in range(CZ - 2, CZ + 3): b.set(x, 0, z, "minecraft:smooth_sandstone" if (x + z) % 3 else "minecraft:cut_sandstone")
    for z in range(16, N - 6):
        for x in range(CX - 2, CX + 3): b.set(x, 0, z, "minecraft:smooth_sandstone" if (x + z) % 3 else "minecraft:cut_sandstone")
    # the party hall: a long two-storey hall with a stage, the bar and the kitchen
    hx0, hz0, hx1, hz1 = CX - 15, CZ + 8, CX + 15, CZ + 26
    b.box(hx0, 0, hz0, hx1, 0, hz1, "minecraft:spruce_planks")
    b.walls(hx0, 1, hz0, hx1, 10, hz1, "minecraft:cut_red_sandstone")
    b.box(hx0 + 1, 1, hz0 + 1, hx1 - 1, 10, hz1 - 1, AIR)
    for x in range(hx0, hx1 + 1, 4):
        for z in (hz0, hz1): b.column(x, z, 1, 10, "minecraft:stripped_spruce_log[axis=y]")
    for x in range(hx0 + 2, hx1 - 1, 4):
        for z in (hz0, hz1):
            for k in (3, 4, 5): b.set(x, k, z, "minecraft:orange_stained_glass_pane")
    b.gable_roof(hx0, hz0, hx1, hz1, 11, "minecraft:spruce_stairs", "minecraft:spruce_planks", gable_wall="minecraft:cut_red_sandstone")
    for x in range(CX - 2, CX + 3):
        for y in (1, 2, 3, 4): b.set(x, y, hz0, AIR)
    r = I.furnish(b, hx0 + 1, 1, hz0 + 1, hx1 - 1, hz1 - 1, 9, "banquet", WARM)
    r.chandelier(CX - 7, (hz0 + hz1) // 2, 3, 3); r.chandelier(CX + 7, (hz0 + hz1) // 2, 3, 3)
    b.box(CX - 6, 1, hz1 - 4, CX + 6, 1, hz1 - 1, "minecraft:spruce_planks")  # stage
    for x in range(CX - 6, CX + 7, 3): b.set(x, 2, hz1 - 1, "minecraft:note_block[instrument=harp,note=0,powered=false]") if x % 2 else b.set(x, 2, hz1 - 1, "minecraft:jukebox[has_record=false]")
    for z in range(hz0 + 2, hz1 - 5):  # bar along the east wall
        b.set(hx1 - 3, 1, z, "minecraft:spruce_planks"); b.set(hx1 - 2, 1, z, "minecraft:barrel[facing=up,open=false]")
        if z % 3 == 0: b.set(hx1 - 2, 2, z, "minecraft:brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]")
    # houses, inns and bars
    spots = [(16, 18, "tavern"), (30, 18, None), (58, 18, "tavern"), (70, 20, None), (16, 30, None), (30, 30, "dining"), (58, 30, None), (70, 32, "kitchen"),
             (16, 58, None), (28, 60, "tavern"), (64, 60, None), (16, 72, None), (30, 74, None), (58, 74, "study"), (70, 72, None), (42, 76, None)]
    for (x0, z0, kind) in spots:
        if hx0 - 1 <= x0 + 9 and x0 <= hx1 + 1 and hz0 - 1 <= z0 + 9 and z0 <= hz1 + 1: continue
        w, d = rnd.randint(8, 10), rnd.randint(7, 9)
        T.house(b, x0, z0, w, d, rnd.choice((2, 2, 3)), rnd.choice(("sand", "brick", "plaster")), rnd,
                kinds=[kind, "bedroom", "bedroom"] if kind else None, door="south" if z0 < CZ else "north",
                sign="minecraft:orange_wool" if kind == "tavern" else None)
    # strings of lanterns and banners across the streets
    for x in range(16, N - 8, 6):
        for z in (CZ - 3, CZ + 3): b.column(x, z, 1, 6, fence("spruce"))
        b.set(x, 6, CZ - 2, "minecraft:orange_wool"); b.set(x, 6, CZ + 2, "minecraft:yellow_wool")
        for z in range(CZ - 2, CZ + 3): b.set(x, 7, z, "minecraft:chain[axis=z,waterlogged=false]" if False else fence("spruce"))
        b.set(x, 6, CZ, lantern(True))
    T.pier(b, 5, 30, 12)
    # ---------------- loot and the hunters
    b.chest(hx0 + 2, 1, hz1 - 2, "medium", "east")
    b.guards("bounty_hunter", ((CX - 6, CZ + 4), (CX + 6, CZ + 4), (CX, CZ - 10), (CX - 20, CZ), (CX + 20, CZ)))
    T.landscape(b, 0, 0, N - 1, N - 1, rnd, amp=4, cell=16, edge=8)  # the open sand rolls (guide 9b.1, 11a); last, so it knows where everything stands
    return b, 0
