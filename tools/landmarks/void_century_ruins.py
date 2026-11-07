"""The Ruins of the Ancient Kingdom, the great kingdom erased in the Void Century, drifting on a broken island in
the End. A ring of colossal broken columns round the plaza, the fallen great gate, the head and hand of a giant
toppled statue, streets of roofless stone houses, and the great stepped temple. Inside the temple: the hall of
murals, the shrine, and down a stair the sealed archive where a Poneglyph tells what the world was made to
forget, with its scholars' reading room and the kingdom's last treasure. ~104 x 104. Canvas y 0 = island top,
world y 62."""
import math, random
from canvas import *
import interiors as I
import underkit as U

SID = "void_century_ruins"
TITLE = "Ruins of the Ancient Kingdom"
CUTS = [3, -6, 12]
TILER = dict(terrain="none", sky_y=62)

N = 104
CX, CZ = 52, 52
TUFF = ("minecraft:tuff_bricks", "minecraft:tuff_bricks", "minecraft:cracked_stone_bricks", "minecraft:polished_tuff", "minecraft:mossy_stone_bricks")
CHIS = "minecraft:chiseled_tuff"
ANCIENT = dict(wood="dark_oak", rug="yellow", rug2="black", bed="black", light="minecraft:soul_lantern", accent="minecraft:chiseled_tuff_bricks",
               banner="black", candle="yellow")


def ruin(b, x0, z0, w, d, h, rnd):
    for x in range(x0, x0 + w):
        for z in range(z0, z0 + d):
            b.set(x, 0, z, "minecraft:polished_tuff")
            if x in (x0, x0 + w - 1) or z in (z0, z0 + d - 1):
                for y in range(1, max(1, int(h * (0.3 + 0.7 * abs(math.sin(x * 0.7 + z * 0.4))))) + 1): b.set(x, y, z, rnd.choice(TUFF))
    for i in range(4): b.set(rnd.randint(x0 + 1, x0 + w - 2), 1, rnd.randint(z0 + 1, z0 + d - 2), rnd.choice(("minecraft:cobbled_deepslate", "minecraft:tuff_brick_slab[type=bottom,waterlogged=false]", "minecraft:decorated_pot[cracked=true,facing=north,waterlogged=false]")))


def build():
    rnd = random.Random(961)
    b = B()
    U.floating_island(b, CX, CZ, 50, 48, 36, rnd, top="minecraft:tuff", body=("minecraft:end_stone", "minecraft:tuff", "minecraft:end_stone", "minecraft:deepslate"))
    for x in range(N):
        for z in range(N):
            if b.get(x, 0, z) == "minecraft:tuff" and rnd.random() < 0.25: b.set(x, 0, z, rnd.choice(("minecraft:moss_block", "minecraft:gravel", "minecraft:end_stone")))
            if b.get(x, 0, z) == "minecraft:moss_block" and rnd.random() < 0.3: b.set(x, 1, z, "minecraft:moss_carpet")
    # ---------------- the plaza and the ring of colossal broken columns
    b.cyl(CX, CZ, 30, 0, 0, "minecraft:polished_tuff"); b.cyl(CX, CZ, 30, 1, 2, AIR)
    for r in (10, 20):
        b.cyl(CX, CZ, r + 0.5, 0, 0, "minecraft:chiseled_tuff_bricks", hollow=True)
    for i, a in enumerate(range(0, 360, 24)):
        t = math.radians(a)
        x, z = CX + 27 * math.cos(t), CZ + 27 * math.sin(t)
        h = (6, 22, 14, 3, 18, 26, 9, 2, 20, 12, 5, 24, 16, 8, 1)[i]
        b.round_column(round(x), round(z), 1.6, 1, h, "minecraft:tuff_bricks", cap=CHIS if h > 15 else None)
        if h < 10:  # the fallen top lies beside it
            for k in range(3, 14): b.cyl(x + k * math.cos(t + 1.2), z + k * math.sin(t + 1.2), 1.4, 1, 2, "minecraft:tuff_bricks")
    # ---------------- the great stepped temple in the middle
    for k in range(4):
        hw = 16 - k * 3
        b.box(CX - hw, 1 + k * 4, CZ - hw, CX + hw, 4 + k * 4, CZ + hw, "minecraft:tuff_bricks" if k % 2 == 0 else "minecraft:polished_tuff")
        for x in range(CX - hw, CX + hw + 1, 2): b.set(x, 4 + k * 4, CZ + hw, CHIS); b.set(x, 4 + k * 4, CZ - hw, CHIS)
    for k in range(16):  # the grand stair up the south face
        for dx in range(-2, 3): b.set(CX + dx, 1 + k, CZ + 16 + 3 - k // 1 if False else CZ + 19 - k, stairs("minecraft:tuff_brick_stairs", "north"))
    b.box(CX - 3, 17, CZ - 3, CX + 3, 23, CZ + 3, "minecraft:chiseled_tuff_bricks"); b.box(CX - 2, 17, CZ - 2, CX + 2, 22, CZ + 2, AIR)
    for dx in (-1, 0, 1):
        for y in (17, 18, 19): b.set(CX + dx, y, CZ + 3, AIR)
    b.set(CX, 24, CZ, "minecraft:crying_obsidian")
    # inside: hall of murals, shrine
    b.box(CX - 14, 1, CZ - 14, CX + 14, 10, CZ + 14, AIR)
    b.walls(CX - 15, 1, CZ - 15, CX + 15, 11, CZ + 15, "minecraft:tuff_bricks")
    b.box(CX - 14, 11, CZ - 14, CX + 14, 11, CZ + 14, "minecraft:polished_tuff")
    for x in range(CX - 2, CX + 3):
        for y in range(1, 6): b.set(x, y, CZ + 15, AIR); b.set(x, y, CZ + 16, AIR)
    for z in range(CZ - 14, CZ + 15, 2):
        for y in (3, 4, 5, 6):
            v = "minecraft:yellow_glazed_terracotta" if (y + z) % 3 == 0 else ("minecraft:black_glazed_terracotta" if (y + z) % 3 == 1 else "minecraft:orange_glazed_terracotta")
            b.set(CX - 15, y, z, v); b.set(CX + 15, y, z, v)
    for (x, z) in ((CX - 8, CZ - 8), (CX + 8, CZ - 8), (CX - 8, CZ + 8), (CX + 8, CZ + 8)): b.round_column(x, z, 1.2, 1, 10, "minecraft:chiseled_tuff_bricks")
    I.furnish(b, CX - 6, 1, CZ - 14, CX + 6, CZ - 4, 9, "shrine", ANCIENT, seed=1)
    I.furnish(b, CX - 14, 1, CZ - 14, CX - 9, CZ + 14, 9, "hall", ANCIENT, seed=2)
    I.furnish(b, CX + 9, 1, CZ - 14, CX + 14, CZ + 14, 9, "chapel", ANCIENT, seed=3)
    # the stair down to the sealed archive
    for k in range(9):
        for dx in (-1, 0, 1):
            b.set(CX + dx, -k, CZ + 6 - k, stairs("minecraft:tuff_brick_stairs", "north"))
            for y in range(-k + 1, -k + 4): b.set(CX + dx, y, CZ + 6 - k, AIR)
    AY = -10
    b.box(CX - 13, AY - 1, CZ - 13, CX + 13, AY + 6, CZ - 2, "minecraft:deepslate_tiles")
    b.box(CX - 12, AY, CZ - 12, CX + 12, AY + 5, CZ - 3, AIR)
    for x in range(CX - 1, CX + 2):
        for y in range(AY, AY + 4): b.set(x, y, CZ - 2, AIR)
        b.set(x, AY - 1, CZ - 2, "minecraft:deepslate_tiles")
    b.box(CX - 1, AY, CZ - 2, CX + 1, AY, CZ - 2, "minecraft:polished_deepslate")
    I.furnish(b, CX - 12, AY, CZ - 12, CX - 2, CZ - 3, 5, "library", ANCIENT, seed=4)
    I.furnish(b, CX + 2, AY, CZ - 12, CX + 12, CZ - 3, 5, "treasure", ANCIENT, seed=5)
    b.set(CX, AY, CZ - 11, "onepiece:poneglyph"); b.set(CX, AY + 1, CZ - 11, "onepiece:poneglyph")
    for dx in (-2, 2): b.set(CX + dx, AY, CZ - 10, "minecraft:candle[candles=4,lit=true,waterlogged=false]")
    # ---------------- the fallen great gate, the toppled statue, streets of roofless houses
    gx, gz = CX, CZ + 40
    for dx in (-8, 8): b.box(gx + dx - 1, 1, gz - 1, gx + dx + 1, 18 if dx < 0 else 9, gz + 1, "minecraft:polished_blackstone_bricks")
    b.box(gx - 9, 19, gz - 1, gx - 2, 20, gz + 1, "minecraft:chiseled_polished_blackstone")
    for k in range(12): b.set(gx + 1 + k, 1 + (k % 2), gz + 3 + k // 4, "minecraft:cracked_polished_blackstone_bricks")
    SX, SZ = 86, 30  # the giant statue's head and hand
    b.sphere(SX, 5, SZ, 6, "minecraft:polished_tuff", ry=5)
    b.set(SX - 3, 6, SZ + 5, "minecraft:black_concrete"); b.set(SX + 3, 6, SZ + 5, "minecraft:black_concrete")
    for k in range(-3, 4): b.set(SX + k, 3, SZ + 6, "minecraft:chiseled_tuff")
    b.box(SX - 7, 10, SZ - 2, SX + 7, 11, SZ + 2, "minecraft:tuff_bricks")  # the broken crown
    HX, HZ = 20, 76
    b.box(HX - 5, 1, HZ - 3, HX + 5, 2, HZ + 3, "minecraft:polished_tuff")
    for k in range(4): b.box(HX - 5 + k * 3, 3, HZ - 3, HX - 4 + k * 3, 5, HZ - 2, "minecraft:polished_tuff")
    b.box(HX + 6, 1, HZ - 1, HX + 8, 5, HZ + 1, "minecraft:polished_tuff")
    for (x0, z0) in ((8, 14), (22, 10), (8, 30), (80, 60), (84, 76), (66, 86), (30, 88), (72, 12), (10, 50)):
        ruin(b, x0, z0, rnd.randint(8, 12), rnd.randint(7, 11), rnd.randint(3, 7), rnd)
    # ---------------- loot and guardians
    b.chest(CX + 10, AY, CZ - 6, "void_century", "west"); b.chest(CX - 4, 1, CZ - 12, "void_century", "south"); b.chest(SX, 1, SZ - 8, "hard", "south")
    b.guards("ancient_guardian", ((CX - 22, CZ), (CX + 22, CZ), (CX, CZ + 24), (CX, AY + 0 if False else CZ - 24), (gx, gz - 4)))
    b.guards("ancient_guardian", ((CX, CZ - 6),), y=AY)
    return b, 0
