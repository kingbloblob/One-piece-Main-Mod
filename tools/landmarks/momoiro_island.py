"""Momoiro Island in the Kamabakka Kingdom, where Sanji was sent: a lurid pink island of giant flowers and heart
shapes. The Queen's pink castle with heart-topped towers and a ballroom, the Okama academy of "Attack Cuisine"
with its training kitchen and dance hall, pink cottages with frilly interiors, heart-shaped hedges and fountains,
hydrangea gardens and giant pink flowers. ~96 x 88. Ground = y 0."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "momoiro_island"
TITLE = "Momoiro Island"
CUTS = [2, 8, 16]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 96, 88
PINK = "minecraft:pink_concrete"
PINK2 = "minecraft:pink_terracotta"
MAG = "minecraft:magenta_concrete"
OKAMA = dict(wood="cherry", rug="pink", rug2="magenta", bed="pink", light="minecraft:lantern", accent="minecraft:pink_glazed_terracotta",
             banner="pink", candle="pink")


def heart(u, v):
    return (u * u + v * v - 1) ** 3 - u * u * v ** 3 <= 0


def heart_top(b, x, y, z, s, block):
    for du in range(-s - 1, s + 2):
        for dv in range(-s - 1, s + 2):
            if heart(du / s * 1.2, dv / s * 1.2): b.set(x + du, y + dv, z, block)


def giant_flower(b, x, z, h, petal, rnd):
    for y in range(1, h): b.set(x, y, z, "minecraft:moss_block" if y % 3 else "minecraft:green_concrete")
    for a in range(0, 360, 45):
        t = math.radians(a)
        for r in (1, 2, 3):
            b.set(round(x + r * math.cos(t)), h + (1 if r == 3 else 0), round(z + r * math.sin(t)), petal)
    b.set(x, h, z, "minecraft:yellow_concrete"); b.set(x, h + 1, z, "minecraft:yellow_concrete")


def build():
    rnd = random.Random(721)
    b = B()
    T.ground(b, NX, NZ, rnd, deco=0.25, decos=("minecraft:pink_tulip", "minecraft:peony[half=lower]", "minecraft:allium", "minecraft:pink_petals[facing=north,flower_amount=4]", "minecraft:short_grass"))
    for x in range(NX):
        for z in range(NZ):
            if b.get(x, 1, z) == "minecraft:peony[half=lower]": b.set(x, 2, z, "minecraft:peony[half=upper]")
    # ---------------- the Queen's pink castle
    CX0, CZ0, CX1, CZ1 = 30, 6, 66, 34
    b.box(CX0, 0, CZ0, CX1, 0, CZ1, "minecraft:pink_glazed_terracotta" if False else "minecraft:quartz_block")
    b.walls(CX0, 1, CZ0, CX1, 14, CZ1, PINK)
    b.box(CX0 + 1, 1, CZ0 + 1, CX1 - 1, 14, CZ1 - 1, AIR)
    b.box(CX0 + 1, 7, CZ0 + 1, CX1 - 1, 7, CZ1 - 1, "minecraft:cherry_planks")
    b.box(CX0, 15, CZ0, CX1, 15, CZ1, MAG)
    for x in range(CX0, CX1 + 1):
        b.set(x, 16, CZ1, "minecraft:white_concrete" if x % 2 else AIR); b.set(x, 16, CZ0, "minecraft:white_concrete" if x % 2 else AIR)
        if x % 4 == 2:
            for y in (3, 4, 10, 11): b.set(x, y, CZ1, "minecraft:pink_stained_glass_pane"); b.set(x, y, CZ0, "minecraft:pink_stained_glass_pane")
    for z in range(CZ0, CZ1 + 1):
        b.set(CX0, 16, z, "minecraft:white_concrete" if z % 2 else AIR); b.set(CX1, 16, z, "minecraft:white_concrete" if z % 2 else AIR)
    for x in range(46, 51):
        for y in range(1, 6): b.set(x, y, CZ1, AIR)
    heart_top(b, 48, 9, CZ1 + 1, 4, "minecraft:red_concrete")
    for (x, z) in ((CX0, CZ0), (CX1, CZ0), (CX0, CZ1), (CX1, CZ1)):
        b.cyl(x, z, 3, 0, 22, PINK2); b.cyl(x, z, 2, 1, 22, AIR); b.cyl(x, z, 3.5, 23, 23, MAG)
        b.dome(x, z, 24, 3, h=4, s="minecraft:magenta_concrete", tip="minecraft:gold_block")
        heart_top(b, x, 31, z, 2, "minecraft:red_concrete")
    for i in range(7): b.set(CX0 + 2 + i, 1 + i, CZ0 + 2, stairs("minecraft:cherry_stairs", "east"))
    for i in range(6): b.set(CX0 + 2 + i, 7, CZ0 + 2, AIR)
    I.furnish(b, CX0 + 10, 1, CZ0 + 1, CX1 - 1, CZ1 - 1, 5, "hall", OKAMA, seed=1)         # the ballroom
    I.subdivide(b, CX0 + 1, 8, CZ0 + 1, CX1 - 1, CZ1 - 1, 6, PINK2, ("throne", "bedroom", "bath", "bedroom", "dining"), OKAMA, cell=12, seed=2,
                keepout=((CX0 + 1, CZ0 + 1, CX0 + 9, CZ0 + 4),))
    # ---------------- the Attack Cuisine academy (west)
    T.house(b, 4, 40, 18, 14, floors=2, style="plaster", rnd=random.Random(1), kinds=("kitchen", "hall"), door="east")
    T.house(b, 4, 58, 14, 12, floors=1, style="plaster", rnd=random.Random(2), kinds=("dining",), door="east")
    # pink cottages
    for i, (x, z) in enumerate(((72, 40), (72, 56), (72, 72), (28, 64), (44, 70), (58, 64))):
        T.house(b, x, z, 10, 8, floors=1 + (i % 2), style="plaster", rnd=random.Random(10 + i), kinds=("bedroom", "bath") if i % 2 else ("bedroom",),
                door="west" if x > 60 else "north")
    for k, v in list(b.blocks.items()):  # pink walls and cherry roofs on every house
        if v == "minecraft:white_concrete": b.blocks[k] = PINK
        elif v.startswith("minecraft:red_nether_brick_stairs"): b.blocks[k] = v.replace("red_nether_brick_stairs", "cherry_stairs")
        elif v == "minecraft:red_nether_bricks": b.blocks[k] = "minecraft:cherry_planks"
        elif v.startswith("minecraft:red_nether_brick_slab"): b.blocks[k] = v.replace("red_nether_brick_slab", "cherry_slab")
    # heart hedge and fountain in the plaza
    PX, PZ = 48, 48
    for du in range(-9, 10):
        for dv in range(-9, 10):
            u, v = du / 7.0, -dv / 7.0
            if heart(u, v) and not heart(u * 1.25, v * 1.25):
                b.set(PX + du, 1, PZ + dv, "minecraft:azalea_leaves[distance=7,persistent=true,waterlogged=false]")
                b.set(PX + du, 2, PZ + dv, "minecraft:flowering_azalea_leaves[distance=7,persistent=true,waterlogged=false]")
    b.cyl(PX, PZ, 3, 1, 1, "minecraft:quartz_block", hollow=True); b.cyl(PX, PZ, 2.5, 1, 1, WATER)
    for x in range(PX - 4, PX + 5):  # close the rim wherever the water touches the plaza (it spilled at the corners)
        for z in range(PZ - 4, PZ + 5):
            if b.get(x, 1, z) == WATER:
                for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if b.get(x + dx, 1, z + dz) != WATER: b.set(x + dx, 1, z + dz, "minecraft:quartz_block")
    b.column(PX, PZ, 1, 4, "minecraft:quartz_pillar[axis=y]"); heart_top(b, PX, 6, PZ, 2, "minecraft:pink_concrete")
    for (x, z) in ((84, 10), (88, 26), (12, 12), (20, 26), (90, 84), (6, 82), (36, 84)): giant_flower(b, x, z, rnd.randint(6, 10), rnd.choice(("minecraft:pink_wool", "minecraft:magenta_wool", "minecraft:white_wool")), rnd)
    T.path(b, [(48, CZ1 + 1), (48, PZ - 8)], w=2, s="minecraft:pink_concrete_powder" if False else "minecraft:smooth_quartz")
    T.path(b, [(PX - 8, PZ), (22, PZ)], w=2, s="minecraft:smooth_quartz")
    # ---------------- loot
    b.chest(CX1 - 3, 8, CZ0 + 3, "easy", "west"); b.chest(6, 1, 42, "easy", "east"); b.chest(PX + 4, 1, PZ + 2, "easy", "north")
    return b, 0
