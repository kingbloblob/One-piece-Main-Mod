"""A Celestial Dragon's mansion in the Holy Land, on its own floating garden island in the End: a gleaming white
palace of excess. A domed main house with a columned portico and a golden roof, a grand stair hall, ballroom
and banquet hall, the noble's bedchamber and bath, a trophy room and a vault of gold, a pool with a fountain,
rose gardens and hedges, the guards' lodge, and the slave quarters hidden at the back behind bars.
~96 x 88. Canvas y 0 = the island's top, world y 62."""
import math, random
from canvas import *
import interiors as I
import underkit as U

SID = "celestial_mansion"
TITLE = "Celestial Dragon Mansion"
CUTS = [3, 9, 15]
TILER = dict(terrain="none", sky_y=62)

NX, NZ = 96, 88
CX, CZ = 48, 40
WHITE = "minecraft:white_concrete"
SQ = "minecraft:smooth_quartz"
GOLD = "minecraft:gold_block"
PIL = "minecraft:quartz_pillar[axis=y]"
NOBLE = dict(wood="dark_oak", rug="red", rug2="yellow", bed="red", light="minecraft:lantern", accent="minecraft:gold_block",
             banner="yellow", candle="yellow")
SLAVE = dict(wood="spruce", rug="brown", rug2="gray", bed="brown", light="minecraft:lantern", accent="minecraft:iron_block",
             banner="brown", candle="white")


def build():
    rnd = random.Random(951)
    b = B()
    U.floating_island(b, CX, NZ // 2, 46, 42, 28, rnd, top="minecraft:grass_block", body=("minecraft:end_stone", "minecraft:end_stone", "minecraft:red_terracotta"), dirt="minecraft:dirt")
    # ---------------- the main house: two floors, portico, gold roof and dome
    X0, Z0, X1, Z1 = 20, 18, 76, 48
    b.box(X0, 0, Z0, X1, 0, Z1, "minecraft:polished_diorite")
    b.walls(X0, 1, Z0, X1, 14, Z1, WHITE); b.box(X0 + 1, 1, Z0 + 1, X1 - 1, 14, Z1 - 1, AIR)
    b.box(X0 + 1, 7, Z0 + 1, X1 - 1, 7, Z1 - 1, "minecraft:dark_oak_planks")
    b.hip_roof(X0, Z0, X1, Z1, 15, "minecraft:smooth_sandstone_stairs", "minecraft:gold_block", trim=GOLD) if False else None
    b.box(X0 - 1, 15, Z0 - 1, X1 + 1, 15, Z1 + 1, GOLD)
    for x in range(X0, X1 + 1):
        for z in (Z0, Z1):
            b.set(x, 7, z, GOLD); b.set(x, 16, z, SQ if x % 2 else AIR)
            if x % 4 == 2:
                for y in (2, 3, 4, 9, 10, 11): b.set(x, y, z, "minecraft:glass_pane")
    for z in range(Z0, Z1 + 1):
        for x in (X0, X1):
            b.set(x, 7, z, GOLD); b.set(x, 16, z, SQ if z % 2 else AIR)
            if z % 4 == 2:
                for y in (2, 3, 4, 9, 10, 11): b.set(x, y, z, "minecraft:glass_pane")
    b.dome(CX, (Z0 + Z1) // 2, 16, 9, s=GOLD, tip=GOLD)
    b.shape(lambda x, y, z: ((x - CX) / 8) ** 2 + ((y - 16) / 8) ** 2 + ((z - 33) / 8) ** 2 < 1 and y >= 16, CX - 9, 16, 24, CX + 9, 25, 42, AIR, interior=None)
    b.cyl(CX, 33, 8, 15, 15, AIR); b.box(CX - 8, 8, 25, CX + 8, 14, 41, AIR) if False else None
    for x in range(CX - 12, CX + 13, 3):  # the portico
        b.column(x, Z1 + 5, 1, 12, PIL)
    b.box(CX - 14, 13, Z1 + 1, CX + 14, 13, Z1 + 6, SQ)
    for k in range(5): b.box(CX - 14 + k * 2, 14 + k, Z1 + 6, CX + 14 - k * 2, 14 + k, Z1 + 6, SQ)
    b.set(CX, 17, Z1 + 7, GOLD)
    for k in range(3): b.box(CX - 10 - k, 0, Z1 + 1 + k * 2, CX + 10 + k, 0, Z1 + 2 + k * 2, SQ)
    for x in range(CX - 2, CX + 3):
        for y in range(1, 6): b.set(x, y, Z1, AIR)
    # inside: stair hall, ballroom, banquet hall, bedchamber, bath, trophy room, vault
    for i in range(6):
        for dx in range(-2, 3): b.set(CX + dx, 1 + i, Z0 + 12 + i, stairs("minecraft:quartz_stairs", "south")) if False else None
    for i in range(6):
        for dx in range(-1, 2): b.set(CX + dx, 1 + i, Z1 - 2 - i, stairs("minecraft:quartz_stairs", "south")); b.set(CX + dx, 7, Z1 - 2 - i, AIR)
    I.furnish(b, X0 + 1, 1, Z0 + 1, CX - 4, Z1 - 1, 5, "hall", NOBLE, seed=1)        # ballroom
    I.furnish(b, CX + 4, 1, Z0 + 1, X1 - 1, Z1 - 1, 5, "dining", NOBLE, seed=2)      # banquet hall
    for z in range(Z0 + 1, Z1):
        for y in range(1, 7): b.set(CX - 4, y, z, WHITE); b.set(CX + 4, y, z, WHITE)
    for (x, z) in ((CX - 4, Z1 - 4), (CX + 4, Z1 - 4)):
        for y in (1, 2, 3): b.set(x, y, z, AIR); b.set(x, y, z - 1, AIR)
    I.subdivide(b, X0 + 1, 8, Z0 + 1, X1 - 1, Z1 - 1, 5, WHITE, ("bedroom", "bath", "throne", "treasure", "study", "library"), NOBLE, cell=13, seed=3,
                keepout=((CX - 2, Z1 - 8, CX + 2, Z1 - 1),))
    # ---------------- gardens: pool and fountain, rose beds, hedges and gold statues
    PZ = 64
    b.box(CX - 10, -1, PZ - 4, CX + 10, -1, PZ + 4, SQ); b.box(CX - 9, 0, PZ - 3, CX + 9, 0, PZ + 3, WATER)
    b.walls(CX - 10, 0, PZ - 4, CX + 10, 0, PZ + 4, SQ)
    b.column(CX, PZ, 0, 4, PIL); b.set(CX, 5, PZ, GOLD); b.set(CX, 6, PZ, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    for x in range(14, 84, 2):
        for z in (56, 74):
            if abs(x - CX) > 12: b.set(x, 1, z, "minecraft:rose_bush[half=lower]"); b.set(x, 2, z, "minecraft:rose_bush[half=upper]")
    for z in range(54, 78):
        for x in (12, 84): b.set(x, 1, z, "minecraft:azalea_leaves[distance=7,persistent=true,waterlogged=false]"); b.set(x, 2, z, "minecraft:azalea_leaves[distance=7,persistent=true,waterlogged=false]")
    for (x, z) in ((22, 64), (74, 64)):
        b.box(x - 1, 1, z - 1, x + 1, 1, z + 1, SQ); b.column(x, z, 2, 5, GOLD); b.set(x, 6, z, "minecraft:gold_block")
    T_Z = 80
    for z in range(Z1 + 7, NZ - 4): b.set(CX, 0, z, "minecraft:red_concrete"); b.set(CX - 1, 0, z, GOLD); b.set(CX + 1, 0, z, GOLD)
    # ---------------- the guards' lodge (east) and the slave quarters behind bars (north)
    b.box(80, 0, 22, 92, 0, 40, "minecraft:polished_diorite"); b.walls(80, 1, 22, 92, 5, 40, WHITE); b.box(81, 1, 23, 91, 5, 39, AIR)
    b.box(80, 6, 22, 92, 6, 40, GOLD)
    for z in range(30, 33):
        for y in (1, 2): b.set(80, y, z, AIR)
    I.subdivide(b, 81, 1, 23, 91, 39, 4, WHITE, ("barracks", "armory"), NOBLE, cell=8, seed=4, door="west")
    b.box(28, 0, 6, 68, 0, 15, "minecraft:cobblestone"); b.walls(28, 1, 6, 68, 4, 15, "minecraft:stone_bricks"); b.box(29, 1, 7, 67, 4, 14, AIR)
    b.box(28, 5, 6, 68, 5, 15, "minecraft:stone_brick_slab[type=bottom,waterlogged=false]")
    for i in range(8):
        x0 = 29 + i * 5
        for z in range(7, 15): b.set(x0 + 4, 1, z, "minecraft:stone_bricks") if i < 7 else None
        for x in range(x0, x0 + 4):
            for y in (1, 2, 3): b.set(x, y, 14, "onepiece:prison_bars")
        I.furnish(b, x0, 1, 7, x0 + 3, 12, 3, "cell", SLAVE, seed=10 + i, lit=False)
    for x in range(29, 68): b.set(x, 0, 15, "minecraft:cobblestone")
    # ---------------- loot and guards
    b.chest(X1 - 3, 8, Z0 + 3, "celestial", "west"); b.chest(X0 + 3, 1, Z0 + 3, "celestial", "east"); b.chest(90, 1, 24, "hard", "west")
    b.guards("cp_agent", ((CX - 8, Z1 + 10), (CX + 8, Z1 + 10), (30, 30), (66, 30)))
    b.guards("pacifista", ((CX, 70),))
    return b, 0
