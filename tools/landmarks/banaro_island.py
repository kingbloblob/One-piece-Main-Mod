"""Banaro Island after Ace and Blackbeard's duel: a desert-edge town of stone houses half blasted away by Ace's
fire and swallowed by Blackbeard's darkness. A huge scorched crater with glassy edges in the town square, burnt
and roofless houses with charred furniture, a ruined clock tower, a well, the Blackbeard Pirates' camp in the
one surviving tavern with their flag on the roof, and the Marines' wanted posters peeling off the walls.
~96 x 88. Ground = y 0."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "banaro_island"
TITLE = "Banaro Island (burnt town)"
CUTS = [2, 6]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 96, 88
CX, CZ = 48, 44
BURNT = ("minecraft:blackstone", "minecraft:basalt[axis=y]", "onepiece:scorched_stone", "minecraft:coal_block", "minecraft:smooth_basalt", "minecraft:cobbled_deepslate")
BB = dict(wood="dark_oak", rug="black", rug2="gray", bed="black", light="minecraft:lantern", accent="minecraft:blackstone",
          banner="black", candle="black")


def build():
    rnd = random.Random(741)
    b = B()
    T.ground(b, NX, NZ, rnd, top="minecraft:sand", deco=0.03, decos=("minecraft:dead_bush",))
    for x in range(NX):
        for z in range(NZ):
            for y in (-3, -2, -1): b.set(x, y, z, "minecraft:sandstone")
            if rnd.random() < 0.15: b.set(x, 0, z, "minecraft:coarse_dirt")
    # ---------------- the stone houses, many burnt
    hs = [(6, 6), (22, 4), (62, 6), (78, 8), (6, 24), (82, 26), (6, 62), (22, 72), (62, 72), (78, 64), (36, 74), (80, 44)]
    for i, (x, z) in enumerate(hs):
        T.house(b, x, z, 11, 9, floors=1 + (i % 2), style="sand", rnd=random.Random(i), door="south" if z < CZ else "north", flat_roof=True)
    for k, v in list(b.blocks.items()):  # fire damage: the nearer the crater, the worse
        x, y, z = k
        d = math.hypot(x - CX, z - CZ)
        if y < 1 or v == AIR: continue
        burn = max(0.0, 1.2 - d / 45)
        if rnd.random() < burn * 0.55: b.blocks[k] = AIR if y > 2 and rnd.random() < 0.6 else rnd.choice(BURNT)
        elif "planks" in v or "wool" in v or "carpet" in v or "bed" in v: b.blocks[k] = rnd.choice(("minecraft:coal_block", "minecraft:blackstone", AIR)) if rnd.random() < burn else v
    # ---------------- the crater
    for x in range(CX - 20, CX + 21):
        for z in range(CZ - 20, CZ + 21):
            d = math.hypot(x - CX, z - CZ)
            if d > 20: continue
            depth = int(8 * (1 - (d / 20) ** 2))
            for y in range(-depth + 1, 14): b.set(x, y, z, AIR)
            b.set(x, -depth, z, rnd.choice(BURNT) if d > 6 else "minecraft:obsidian")
            if d > 17 and rnd.random() < 0.5: b.set(x, 1, z, rnd.choice(("minecraft:blackstone", "minecraft:magma_block", "minecraft:tinted_glass")))
            if d < 14 and rnd.random() < 0.04: b.set(x, -depth + 1, z, "minecraft:fire" if False else "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    # ruined clock tower
    TX, TZ = 72, 26
    b.box(TX - 3, 0, TZ - 3, TX + 3, 0, TZ + 3, "minecraft:cut_sandstone")
    for y in range(1, 22):
        for (dx, dz) in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
            if y < 22 - abs(dx + dz) * 2: b.set(TX + dx, y, TZ + dz, "minecraft:cut_sandstone")
        for d in range(-2, 3):
            if y < 16 - d * 2: b.set(TX + d, y, TZ - 3, "minecraft:smooth_sandstone"); b.set(TX - 3, y, TZ + d, "minecraft:smooth_sandstone")
    b.cyl(TX, TZ - 4, 2, 11, 11, "minecraft:white_concrete") if False else None
    for (dx, dy) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)): b.set(TX + dx, 12 + dy, TZ - 4, "minecraft:quartz_block")
    b.set(TX, 12, TZ - 5, "minecraft:black_concrete"); b.set(TX, 13, TZ - 5, "minecraft:black_concrete")
    T.well(b, 24, 40)
    # ---------------- the surviving tavern: Blackbeard's camp
    T.house(b, 30, 4, 18, 12, floors=1, style="stone", rnd=random.Random(99), kinds=("tavern",), door="south")
    for y in range(6, 12): b.set(39, y, 9, "minecraft:dark_oak_fence")
    b.jolly_roger(39, 11, 10, 5, 4)
    for x in range(32, 47, 4): b.set(x, 3, 3, "minecraft:paper" if False else "minecraft:white_wool")
    for (x, z) in ((34, 18), (40, 19), (44, 17)): b.set(x, 1, z, rnd.choice(("onepiece:sake_barrel", "minecraft:barrel[facing=up,open=false]", "onepiece:cola_crate")))
    # ---------------- loot and the stragglers
    b.chest(32, 1, 6, "medium", "east"); b.chest(CX, -7, CZ, "medium", "south"); b.chest(8, 1, 8, "easy", "east")
    b.guards("pirate", ((CX - 22, CZ), (CX + 22, CZ + 10), (20, 60)))
    b.guards("blackbeard_pirate", ((38, 20), (44, 10)))
    return b, 0
