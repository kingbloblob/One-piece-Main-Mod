"""God Valley, life size: the holy island where the World Nobles held their human hunt and where Roger and Garp
fought the Rocks Pirates 38 years ago. In the middle the scorched battlefield arena, ringed by broken white
columns, where Rocks D. Xebec waits. North of it the Celestial Dragons' hunting palace with its viewing terrace
and thrones, banquet hall, trophy room and bedchambers; the ruined cathedral of the island's faith; the burnt
village of the natives with their huts and the well; the Rocks Pirates' camp beside the wreck of their ship on
the beach; Garp's half-buried anchor, craters and soul fire scars all round. ~112 x 112. Ground = y 0, sea south."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "god_valley"
TITLE = "God Valley"
CUTS = [2, 8, 16]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 112
AX, AZ, AR = 56, 54, 26     # the arena
SEA_Z = 96
SQ = "minecraft:smooth_quartz"
GOLD = "minecraft:gold_block"
PIL = "minecraft:quartz_pillar[axis=y]"
NOBLE = dict(wood="dark_oak", rug="red", rug2="yellow", bed="red", light="minecraft:lantern", accent="minecraft:gold_block",
             banner="white", candle="yellow")
NATIVE = dict(wood="spruce", rug="brown", rug2="green", bed="brown", light="minecraft:lantern", accent="minecraft:hay_block[axis=y]",
              banner="brown", candle="white")
ROCKS = dict(wood="dark_oak", rug="black", rug2="red", bed="black", light="minecraft:lantern", accent="minecraft:barrel[facing=up,open=false]",
             banner="black", candle="red")
SCORCH = ("minecraft:blackstone", "minecraft:basalt[axis=y]", "minecraft:coarse_dirt", "minecraft:cracked_polished_blackstone_bricks", "minecraft:blackstone", "onepiece:scorched_stone")


def build():
    rnd = random.Random(971)
    b = B()
    T.ground(b, N, N, rnd, deco=0.2, decos=("minecraft:lily_of_the_valley", "minecraft:oxeye_daisy", "minecraft:white_tulip", "minecraft:short_grass", "minecraft:short_grass"))
    T.sea(b, N, N, lambda x, z: z > SEA_Z + 2 * math.sin(x * 0.15), depth=6)
    for x in range(N):
        for z in range(N):
            s = SEA_Z + 2 * math.sin(x * 0.15)
            if s - 7 < z <= s: b.set(x, 0, z, "minecraft:sand"); b.set(x, -1, z, "minecraft:sandstone"); b.set(x, 1, z, AIR) if b.get(x, 1, z) else None
    # ---------------- the arena: scorched and cracked, the fighting space kept clear
    for x in range(AX - AR - 1, AX + AR + 2):
        for z in range(AZ - AR - 1, AZ + AR + 2):
            d = math.hypot(x - AX, z - AZ)
            if d > AR: continue
            b.set(x, 0, z, rnd.choice(SCORCH) if d < AR - 4 else rnd.choice(("minecraft:polished_diorite", "minecraft:calcite", "minecraft:cracked_stone_bricks")))
            for y in range(1, 24): b.set(x, y, z, AIR)
    for (cx, cz, r) in ((44, 48, 4), (68, 62, 5), (52, 66, 3), (66, 42, 3), (40, 62, 2.5)):
        for x in range(int(cx - r), int(cx + r) + 1):
            for z in range(int(cz - r), int(cz + r) + 1):
                d = math.hypot(x - cx, z - cz)
                if d <= r: b.set(x, 0, z, "minecraft:soul_soil" if d > 1 else "minecraft:magma_block"); b.set(x, -1, z, "minecraft:blackstone")
    for i, a in enumerate(range(0, 360, 15)):  # the ring of broken columns
        if 80 < a < 100: continue
        t = math.radians(a)
        x, z = round(AX + (AR - 2) * math.cos(t)), round(AZ + (AR - 2) * math.sin(t))
        h = (3, 14, 7, 18, 5, 11, 2, 16, 9, 20, 4, 12)[i % 12]
        b.round_column(x, z, 1.1, 1, h, PIL)
        if h >= 14: b.set(x, h + 1, z, GOLD)
        else:
            for k in range(2, 7): b.set(round(x + k * math.cos(t + 1.57)), 1, round(z + k * math.sin(t + 1.57)), "minecraft:quartz_pillar[axis=x]" if abs(math.cos(t + 1.57)) > 0.7 else "minecraft:quartz_pillar[axis=z]")
    for (x, z) in ((AX - 16, AZ), (AX + 16, AZ), (AX, AZ + 16), (AX - 10, AZ + 12), (AX + 10, AZ - 12)): b.set(x, 1, z, "minecraft:soul_fire")
    # Garp's half-buried anchor, a broken Rocks flag
    for y in range(1, 9): b.set(AX + 18, y, AZ + 6, "minecraft:iron_block")
    b.box(AX + 15, 1, AZ + 6, AX + 21, 1, AZ + 6, "minecraft:iron_block"); b.set(AX + 15, 2, AZ + 6, "minecraft:iron_block"); b.set(AX + 21, 2, AZ + 6, "minecraft:iron_block")
    b.cyl(AX + 18, AZ + 6, 1.6, 9, 9, "minecraft:iron_block", hollow=True)
    for y in range(1, 12): b.set(AX - 20, y, AZ - 4, "minecraft:dark_oak_fence")
    b.jolly_roger(AX - 20, 11, AZ - 3, 6, 4)
    # ---------------- the Celestial Dragons' hunting palace (north)
    PX0, PZ0, PX1, PZ1 = 30, 4, 82, 24
    b.box(PX0, 0, PZ0, PX1, 3, PZ1, SQ)  # raised terrace
    b.walls(PX0 + 2, 4, PZ0, PX1 - 2, 15, PZ1 - 6, "minecraft:white_concrete"); b.box(PX0 + 3, 4, PZ0 + 1, PX1 - 3, 15, PZ1 - 7, AIR)
    b.box(PX0 + 3, 10, PZ0 + 1, PX1 - 3, 10, PZ1 - 7, "minecraft:dark_oak_planks")
    b.box(PX0 + 1, 16, PZ0 - 1, PX1 - 1, 16, PZ1 - 5, GOLD)
    for x in range(PX0 + 2, PX1 - 1):
        b.set(x, 17, PZ0, SQ if x % 2 else AIR); b.set(x, 17, PZ1 - 6, SQ if x % 2 else AIR)
        if x % 4 == 0:
            for y in (5, 6, 7, 12, 13): b.set(x, y, PZ1 - 6, "minecraft:glass_pane"); b.set(x, y, PZ0, "minecraft:glass_pane")
    for x in range(PX0 + 3, PX1 - 2, 4): b.column(x, PZ1 - 2, 4, 15, PIL)  # the columned viewing terrace
    b.box(PX0 + 2, 16, PZ1 - 5, PX1 - 2, 16, PZ1 - 1, SQ)
    for x in range(PX0 + 2, PX1 - 1): b.set(x, 4, PZ1, "minecraft:quartz_slab[type=bottom,waterlogged=false]") if x % 2 else b.set(x, 4, PZ1, GOLD)
    for x in range(48, 65, 4):  # the World Nobles' viewing thrones
        b.set(x, 4, PZ1 - 3, "minecraft:quartz_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]"); b.set(x, 5, PZ1 - 4, GOLD); b.set(x, 4, PZ1 - 4, GOLD)
    for x in range(PX0 + 3, PX1 - 2): b.set(x, 4, PZ1 - 2 if x % 4 else PZ1 - 1, "minecraft:red_carpet") if x % 4 else None
    for k in range(4):  # the grand stair down to the arena
        for x in range(50, 63): b.set(x, 3 - k, PZ1 + 1 + k, stairs("minecraft:quartz_stairs", "north"))
    for x in range(54, 59):
        for y in range(4, 8): b.set(x, y, PZ1 - 6, AIR)
    I.furnish(b, PX0 + 3, 4, PZ0 + 1, 52, PZ1 - 7, 5, "dining", NOBLE, seed=1)
    I.furnish(b, 60, 4, PZ0 + 1, PX1 - 3, PZ1 - 7, 5, "treasure", NOBLE, seed=2)
    for z in range(PZ0 + 1, PZ1 - 6):
        for y in range(4, 10): b.set(53, y, z, "minecraft:white_concrete"); b.set(59, y, z, "minecraft:white_concrete")
    for x in (53, 59):
        for y in (4, 5, 6): b.set(x, y, PZ1 - 9, AIR)
    I.subdivide(b, PX0 + 3, 11, PZ0 + 1, PX1 - 3, PZ1 - 7, 4, "minecraft:white_concrete", ("bedroom", "bath", "bedroom", "study", "bedroom"), NOBLE, cell=10, seed=3)
    for y in range(4, 11): b.set(PX0 + 4, y, PZ1 - 8, "minecraft:ladder[facing=north,waterlogged=false]")
    for (dx,) in ((PX0 + 2,), (PX1 - 2,)):
        b.dome(dx, PZ0 + 4, 17, 4, s=GOLD, onion=True, tip=GOLD)
    # ---------------- the ruined cathedral (west)
    CX0, CZ0, CX1, CZ1 = 4, 30, 22, 70
    b.box(CX0, 0, CZ0, CX1, 0, CZ1, "minecraft:polished_andesite")
    for z in range(CZ0, CZ1 + 1):
        for x in (CX0, CX1):
            hh = int(12 + 6 * math.sin(z * 0.4)) if z < 56 else rnd.randint(2, 6)
            for y in range(1, hh): b.set(x, y, z, "minecraft:stone_bricks" if (y + z) % 5 else "minecraft:cracked_stone_bricks")
            if z % 5 == 0 and hh > 8: b.set(x, 6, z, "minecraft:white_stained_glass_pane"); b.set(x, 7, z, "minecraft:yellow_stained_glass_pane")
    for x in range(CX0, CX1 + 1):
        for y in range(1, 20 - abs(x - 13)): b.set(x, y, CZ0, "minecraft:stone_bricks")
    b.cyl(13, CZ0, 3, 12, 12, "minecraft:white_stained_glass"); b.cyl(13, CZ0, 1, 12, 12, "minecraft:yellow_stained_glass")
    for z in range(CZ0 + 4, CZ1 - 2, 5): b.round_column(9, z, 0.8, 1, 14 if z < 56 else 4, "minecraft:stone_bricks"); b.round_column(17, z, 0.8, 1, 14 if z < 56 else 5, "minecraft:stone_bricks")
    I.furnish(b, CX0 + 1, 1, CZ0 + 1, CX1 - 1, CZ1 - 1, 10, "chapel", NATIVE, seed=4)
    for i in range(30): b.set(rnd.randint(CX0, CX1), 1, rnd.randint(56, CZ1), rnd.choice(("minecraft:cobblestone", "minecraft:cracked_stone_bricks", "minecraft:stone_brick_slab[type=bottom,waterlogged=false]")))
    # ---------------- the burnt native village (east)
    for i, (x, z) in enumerate(((88, 30), (98, 30), (88, 44), (98, 46), (90, 60), (100, 62), (88, 76))):
        T.house(b, x, z, 9, 8, floors=1, style="shack", rnd=random.Random(i), kinds=(("kitchen", "bedroom", "storage", "workshop")[i % 4],), door="west")
    for k, v in list(b.blocks.items()):
        if k[0] >= 86 and k[1] >= 3 and rnd.random() < 0.25 and v != AIR and ("planks" in v or "stairs" in v): b.blocks[k] = rnd.choice(("minecraft:coal_block", AIR, AIR))
    T.well(b, 96, 54)
    T.garden(b, 100, 76, 108, 84, rnd=rnd)
    # ---------------- the Rocks Pirates' camp by the wreck of their ship (south-west beach)
    hw = b.hull(4, 34, SEA_Z + 4, 12, -4, 4, "minecraft:dark_oak_planks", bottom="minecraft:spruce_planks", rail="minecraft:dark_oak_fence",
                bow_len=10, stern_len=4, fill_deck="minecraft:dark_oak_planks", waterline=None)
    for k, v in list(b.blocks.items()):
        if 4 <= k[0] < 38 and abs(k[2] - SEA_Z - 4) < 8 and k[1] >= 1 and rnd.random() < 0.12 and v != AIR and "water" not in v: b.blocks[k] = AIR
    for k, v in list(b.blocks.items()):  # the wreck is holed: below the sea surface its hold is full of sea water
        if 4 <= k[0] < 38 and abs(k[2] - SEA_Z - 4) < 8 and k[1] <= 0 and v == AIR: b.blocks[k] = WATER
    b.line((20, 4, SEA_Z + 4), (34, 1, SEA_Z - 6), "minecraft:dark_oak_log[axis=x]")
    for (x, z) in ((10, 82), (20, 80), (30, 84)):
        for k in range(3):
            for xx in range(x, x + 6): b.set(xx, 1 + k, z + k, "minecraft:black_wool"); b.set(xx, 1 + k, z + 6 - k, "minecraft:black_wool")
        I.furnish(b, x + 1, 1, z + 2, x + 4, z + 4, 1, "barracks", ROCKS, seed=x)
    b.set(22, 1, 88, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (x, z) in ((18, 88), (26, 88), (22, 85)): b.set(x, 1, z, "onepiece:sake_barrel")
    # ---------------- loot and the superboss
    b.chest(PX0 + 5, 4, PZ0 + 3, "legendary", "east"); b.chest(PX1 - 5, 4, PZ0 + 3, "treasure", "west"); b.chest(13, 1, CZ0 + 3, "treasure", "south")
    b.chest(12, 1, 84, "hard", "east")
    b.npc(AX, 1, AZ + 2, "xebec", True)
    return b, 0
