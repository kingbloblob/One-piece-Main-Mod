"""Baltigo, the white-sand island that was the Revolutionary Army's headquarters: a fortress-town carved from pale
stone and bone-white sand, walled against the desert winds. The great stone headquarters climbs in terraces to
Dragon's tower room with its map of the world, Sabo's command office, the war room round a giant table, a
library of intelligence files, barracks and mess halls, the training courtyard, the radio mast with its
Den Den Mushi relay, and the dragon-wing banners on the walls. ~104 x 96. Ground = y 0."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "baltigo"
TITLE = "Baltigo (Revolutionary HQ)"
CUTS = [2, 8, 20]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 104, 96
STONE = "minecraft:smooth_sandstone"
STONE2 = "minecraft:cut_sandstone"
BONE = "minecraft:bone_block[axis=y]"
CX, CZ = 52, 44
REV = dict(wood="spruce", rug="black", rug2="gray", bed="black", light="minecraft:lantern", accent="minecraft:chiseled_sandstone",
           banner="black", candle="white")


def build():
    rnd = random.Random(681)
    b = B()
    T.ground(b, NX, NZ, rnd, top="minecraft:sand", deco=0.02, decos=("minecraft:dead_bush",))
    for x in range(NX):
        for z in range(NZ):
            for y in (-3, -2, -1): b.set(x, y, z, "minecraft:sandstone")
            if (x * 5 + z * 3) % 11 == 0: b.set(x, 0, z, "minecraft:white_concrete_powder")
    # dunes outside the walls
    for (x, z, r) in ((8, 84, 9), (94, 82, 8), (6, 10, 7), (96, 8, 8)):
        b.shape(lambda xx, y, zz, x=x, z=z, r=r: ((xx - x) / r) ** 2 + ((y) / 3.5) ** 2 + ((zz - z) / r) ** 2 < 1, x - r, 1, z - r, x + r, 4, z + r, "minecraft:sand", interior=None)
    # ---------------- the town wall
    WX0, WZ0, WX1, WZ1 = 6, 4, NX - 7, NZ - 10
    b.walls(WX0, 1, WZ0, WX1, 9, WZ1, STONE2)
    for x in range(WX0, WX1 + 1):
        for z in (WZ0, WZ1):
            if x % 2 == 0: b.set(x, 10, z, STONE)
    for z in range(WZ0, WZ1 + 1):
        for x in (WX0, WX1):
            if z % 2 == 0: b.set(x, 10, z, STONE)
    for x in range(CX - 3, CX + 4):
        for y in range(1, 8): b.set(x, y, WZ1, AIR)
    for (x, z) in ((WX0, WZ0), (WX1, WZ0), (WX0, WZ1), (WX1, WZ1), (CX - 6, WZ1), (CX + 6, WZ1)):
        b.cyl(x, z, 3, 0, 13, STONE2); b.cyl(x, z, 2, 1, 13, AIR); b.cyl(x, z, 3.5, 14, 14, STONE); b.cyl(x, z, 3.5, 15, 15, STONE, hollow=True)
        for y in range(1, 14): b.set(x, y, z, "minecraft:ladder[facing=north,waterlogged=false]") if False else None
    for x in range(WX0 + 6, WX1 - 4, 14):  # dragon-wing banners: black banners down the wall
        for y in range(3, 9): b.set(x, y, WZ1 + 1, "minecraft:black_wool")
        b.set(x - 1, 8, WZ1 + 1, "minecraft:black_wool"); b.set(x + 1, 8, WZ1 + 1, "minecraft:black_wool"); b.set(x, 5, WZ1 + 1, "minecraft:red_wool")
    # ---------------- the headquarters: four terraces
    tiers = ((24, 18, 0, 8), (18, 14, 8, 7), (12, 10, 15, 7), (6, 6, 22, 9))
    for i, (hx, hz, y0, h) in enumerate(tiers):
        b.box(CX - hx, y0, CZ - hz, CX + hx, y0, CZ + hz, "minecraft:spruce_planks" if i else "minecraft:polished_diorite")
        b.walls(CX - hx, y0 + 1, CZ - hz, CX + hx, y0 + h, CZ + hz, STONE)
        b.box(CX - hx + 1, y0 + 1, CZ - hz + 1, CX + hx - 1, y0 + h, CZ + hz - 1, AIR)
        b.box(CX - hx, y0 + h, CZ - hz, CX + hx, y0 + h, CZ + hz, STONE2)
        for x in range(CX - hx + 2, CX + hx - 1, 3):
            for z in (CZ - hz, CZ + hz):
                b.set(x, y0 + 2, z, "minecraft:black_stained_glass_pane"); b.set(x, y0 + 3, z, "minecraft:black_stained_glass_pane")
        for x in range(CX - hx, CX + hx + 1): b.set(x, y0 + h + 1, CZ + hz, "minecraft:sandstone_wall" if x % 2 else AIR)
        for dx in (-1, 0, 1):
            for y in range(y0 + 1, y0 + 4): b.set(CX + dx, y, CZ + hz, AIR)
    for (y0, a, b2) in ((8, 0, 1), (15, 1, 2), (22, 2, 3)):  # outside stairs climbing the terraces (east side)
        hx0 = tiers[a][0]; hx1 = tiers[b2][0]
        for i in range(tiers[a][3] + 1):
            b.set(CX + hx0 - 2 - i, tiers[a][2] + 1 + i, CZ + tiers[a][1] - 2, stairs("minecraft:sandstone_stairs", "west")) if False else None
    for i, (hx, hz, y0, h) in enumerate(tiers[:-1]):
        for k in range(h):
            b.set(CX + hx - 2, y0 + 1 + k, CZ - hz + 2, "minecraft:ladder[facing=south,waterlogged=false]")
        b.set(CX + hx - 2, y0 + h, CZ - hz + 2, AIR)
    # ground: mess hall and barracks; 2: war room and library; 3: Sabo's office; top: Dragon's tower room
    I.subdivide(b, CX - 23, 1, CZ - 17, CX + 23, CZ + 17, 6, STONE2, ("dining", "kitchen", "barracks", "barracks", "armory", "storage", "bath", "barracks"), REV, cell=11, seed=1,
                keepout=((CX - 2, CZ + 13, CX + 2, CZ + 17), (CX + 20, CZ - 17, CX + 23, CZ - 13)))
    I.subdivide(b, CX - 17, 9, CZ - 13, CX + 17, CZ + 13, 5, STONE2, ("hall", "library", "study", "library"), REV, cell=13, seed=2,
                keepout=((CX - 2, CZ + 10, CX + 2, CZ + 13), (CX + 14, CZ - 13, CX + 17, CZ - 10)))
    b.box(CX - 5, 10, CZ - 3, CX + 5, 10, CZ + 3, "minecraft:spruce_planks") if False else None
    I.furnish(b, CX - 11, 16, CZ - 9, CX + 11, CZ + 9, 6, "study", REV, seed=3)
    I.furnish(b, CX - 5, 23, CZ - 5, CX + 5, CZ + 5, 8, "throne", REV, seed=4)
    for x in range(CX - 4, CX + 5):  # the world map on Dragon's wall
        for y in range(25, 29): b.set(x, y, CZ - 5, "minecraft:blue_concrete" if (x * 3 + y) % 5 else "minecraft:lime_concrete")
    # the radio mast
    for y in range(31, 46): b.set(CX + 3, y, CZ + 3, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
    b.set(CX + 3, 46, CZ + 3, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]"); b.set(CX + 2, 31, CZ + 3, "onepiece:den_den_relay")
    # ---------------- the training courtyard and the outer houses
    for x in range(CX - 20, CX + 21, 5):
        b.set(x, 1, CZ + 26, "onepiece:training_post[facing=north]")
    for (x, z) in ((CX - 18, CZ + 30), (CX + 18, CZ + 30)): b.set(x, 1, z, "minecraft:target")
    hs = [(10, 8), (10, 26), (10, 50), (84, 8), (84, 26), (84, 50), (12, 68), (82, 68)]
    for i, (x, z) in enumerate(hs):
        T.house(b, x, z, 10, 9, floors=1 + (i % 2), style="sand", rnd=random.Random(i), kinds=("barracks", "kitchen") if i % 2 else ("workshop",),
                door="east" if x < CX else "west", flat_roof=True)
    T.path(b, [(CX, WZ1), (CX, CZ + 18)], w=3, s="minecraft:smooth_sandstone")
    # ---------------- loot and leaders
    b.chest(CX + 3, 23, CZ - 3, "medium", "west"); b.chest(CX + 9, 16, CZ + 7, "medium", "north"); b.chest(CX - 20, 1, CZ - 14, "easy", "east")
    b.npc(CX, 23, CZ, "dragon", False); b.npc(CX - 6, 16, CZ, "sabo", False)
    return b, 0
