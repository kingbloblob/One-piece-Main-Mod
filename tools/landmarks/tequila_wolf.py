"""Tequila Wolf, the endless bridge in the East Blue built for 700 years by slaves of the World Government. A
massive stone bridge on great arched piers striding across the sea, wide enough for a town: the slave
labourers' barrack huts and soup kitchen along the deck, the overseers' guard towers and office, cranes hauling
stone blocks, scaffolding on the unfinished end that stops in mid-air, and the work boats tied below.
Water surface = y 0, the deck at y 16."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "tequila_wolf"
TITLE = "Tequila Wolf"
WATER_Y = 0
CUTS = [18, 22]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="none")

L = 104
W = 22
D = 16
CZ = 11
STONE = "minecraft:stone_bricks"
STONE2 = "minecraft:mossy_stone_bricks"
OVER = dict(wood="spruce", rug="gray", rug2="brown", bed="gray", light="minecraft:lantern", accent="minecraft:iron_bars",
            banner="light_blue", candle="white")


def build():
    rnd = random.Random(771)
    b = B()
    END = L - 14  # the unfinished end
    # piers and arches
    for px in range(0, END, 16):
        b.box(px, -10, 0, px + 5, D - 1, W - 1, STONE)
        for (x, z) in ((px - 1, 0), (px + 6, 0), (px - 1, W - 1), (px + 6, W - 1)): b.column(x, z, -10, D - 1, "minecraft:stone_brick_wall")
    for x in range(0, END):
        f = (x % 16) - 5
        if f > 0:
            t = (f - 0.5) / 11.0
            ay = int(1 + 11 * math.sqrt(max(0.0, 1 - (2 * t - 1) ** 2)))
            for z in range(W): b.box(x, ay, z, x, D - 1, z, STONE if (x + z) % 7 else STONE2)
    for x in range(END, L):  # the unfinished end: scaffolding only
        for z in range(W):
            if x < END + 4: b.set(x, D - 1, z, "minecraft:cobblestone" if rnd.random() < 0.6 else AIR)
        if x % 3 == 0:
            for z in (0, W - 1, CZ):
                for y in range(-2, D + 6): b.set(x, y, z, "minecraft:scaffolding[bottom=false,distance=0,waterlogged=false]")
    for x in range(0, END + 2):  # deck and parapets
        for z in range(W): b.set(x, D, z, "minecraft:polished_andesite" if 3 < z < W - 4 else "minecraft:stone_bricks")
        b.set(x, D + 1, 0, "minecraft:stone_brick_wall"); b.set(x, D + 1, W - 1, "minecraft:stone_brick_wall")
        if x % 8 == 0: b.set(x, D + 2, 0, lantern()); b.set(x, D + 2, W - 1, lantern())
    # ---------------- on the deck: barracks huts, soup kitchen, overseers
    for i, x in enumerate(range(4, END - 10, 14)):
        if i == 2:
            T.house(b, x, 1, 12, 7, floors=2, style="stone", rnd=random.Random(i), kinds=("study", "barracks"), y=D, door="south")
        elif i == 4:
            T.house(b, x, 1, 12, 7, floors=1, style="shack", rnd=random.Random(i), kinds=("kitchen",), y=D, door="south")
        else:
            T.house(b, x, 1, 10, 7, floors=1, style="shack", rnd=random.Random(i), kinds=("barracks",), y=D, door="south")
        if i % 2 == 0:
            T.house(b, x + 2, W - 8, 8, 6, floors=1, style="shack", rnd=random.Random(30 + i), kinds=("storage",), y=D, door="north")
    for (x, z) in ((10, CZ), (52, CZ)):  # guard towers astride the road
        for (dx, dz) in ((-2, -2), (2, -2), (-2, 2), (2, 2)): b.column(x + dx, z + dz, D + 1, D + 10, "minecraft:spruce_log[axis=y]")
        b.box(x - 3, D + 11, z - 3, x + 3, D + 11, z + 3, "minecraft:spruce_planks"); b.walls(x - 3, D + 12, z - 3, x + 3, D + 12, z + 3, "minecraft:spruce_fence")
        b.set(x, D + 12, z, "minecraft:bell[attachment=floor,facing=north,powered=false]")
        for y in range(D + 1, D + 11): b.set(x + 2, y, z + 3, "minecraft:ladder[facing=south,waterlogged=false]")
    # cranes and the stone blocks they haul
    for x in (36, 76):
        b.column(x, W - 2, D + 1, D + 18, "minecraft:spruce_log[axis=y]")
        for k in range(10): b.set(x, D + 18, W - 2 - k + 6, "minecraft:spruce_log[axis=z]") if False else b.set(x, D + 18, W - 2 + k - 9, "minecraft:spruce_log[axis=z]")
        for y in range(D + 6, D + 18): b.set(x, y, W - 11, "minecraft:iron_chain[axis=y]")
        b.box(x - 1, D + 3, W - 12, x + 1, D + 5, W - 10, "minecraft:stone")
    for i in range(14):
        b.set(rnd.randint(2, END - 2), D + 1, rnd.choice((3, 4, W - 5, W - 4)), rnd.choice(("minecraft:stone", "minecraft:cobblestone", "minecraft:barrel[facing=up,open=false]", "minecraft:stone_bricks")))
    # work boats tied under the bridge
    for x in (12, 44, 74):
        b.box(x, 0, W + 2, x + 6, 0, W + 4, "minecraft:spruce_planks"); b.box(x + 1, 0, W + 3, x + 5, 0, W + 3, AIR)
        b.set(x + 3, 0, W + 3, "minecraft:spruce_slab[type=top,waterlogged=false]")
    for y in range(1, D): b.set(14, y, W, "minecraft:ladder[facing=south,waterlogged=false]")
    # ---------------- loot and overseers
    b.chest(32, D + 1, 3, "medium", "east"); b.chest(END - 2, D + 1, CZ, "medium", "west")
    b.guards("marine", ((12, CZ + 2), (52, CZ + 2), (80, CZ)), y=D + 1)
    b.guards("marine_rifle", ((10, CZ),), y=D + 12)
    return b, 0
