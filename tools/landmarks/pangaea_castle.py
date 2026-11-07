"""Pangaea Castle, the heart of the Holy Land Mary Geoise, floating on its own island in the End: the white and
gold palace of the World Government's rulers. A walled palace on a garden island with four gold-domed corner
towers and a great central keep. Inside: the Room of Authority with the Empty Throne on its stair and the swords
of the twenty founding kingdoms planted round it, the Five Elders' chamber with their long table, the hall of
flowers with Imu's flower-wall of wanted posters and the giant straw hat kept in the cold room, the royal
library of forbidden records, the CP0 barracks, banquet hall, and Imu's private chamber at the top of the keep.
~112 x 112. Canvas y 0 = the island's top, world y 62."""
import math, random
from canvas import *
import interiors as I
import underkit as U

SID = "pangaea_castle"
TITLE = "Pangaea Castle (Holy Land)"
CUTS = [3, 10, 20, 34]
TILER = dict(terrain="none", sky_y=62)

N = 112
CX, CZ = 56, 56
QB = "minecraft:quartz_bricks"
SQ = "minecraft:smooth_quartz"
GOLD = "minecraft:gold_block"
PIL = "minecraft:quartz_pillar[axis=y]"
CEL = dict(wood="dark_oak", rug="red", rug2="yellow", bed="white", light="minecraft:lantern", accent="minecraft:gold_block",
           banner="white", candle="white")
ELDER = dict(wood="dark_oak", rug="black", rug2="yellow", bed="black", light="minecraft:lantern", accent="minecraft:gold_block",
             banner="black", candle="yellow")
W0, W1 = 18, 94   # palace walls
K0, K1 = 38, 74   # the keep


def build():
    rnd = random.Random(941)
    b = B()
    U.floating_island(b, CX, CZ, 54, 54, 34, rnd, top="minecraft:grass_block", body=("minecraft:end_stone", "minecraft:end_stone", "minecraft:red_terracotta"), dirt="minecraft:dirt")
    for x in range(N):  # white flower meadow
        for z in range(N):
            if b.get(x, 0, z) == "minecraft:grass_block" and rnd.random() < 0.3:
                b.set(x, 1, z, rnd.choice(("minecraft:lily_of_the_valley", "minecraft:white_tulip", "minecraft:oxeye_daisy", "minecraft:short_grass", "minecraft:azure_bluet")))
    # ---------------- the palace wall and four gold-domed towers
    b.box(W0, 0, W0, W1, 0, W1, "minecraft:polished_diorite")
    for x in range(W0, W1 + 1):
        for z in range(W0, W1 + 1):
            if (x + z) % 4 == 0 and W0 < x < W1 and W0 < z < W1: b.set(x, 0, z, SQ)
            for y in range(1, 3): b.set(x, y, z, AIR) if b.get(x, y, z) else None
    b.walls(W0, 1, W0, W1, 12, W1, QB)
    for x in range(W0, W1 + 1):
        for z in (W0, W1):
            b.set(x, 13, z, GOLD if x % 3 == 0 else (SQ if x % 3 == 1 else AIR)); b.set(x, 10, z, GOLD)
    for z in range(W0, W1 + 1):
        for x in (W0, W1):
            b.set(x, 13, z, GOLD if z % 3 == 0 else (SQ if z % 3 == 1 else AIR)); b.set(x, 10, z, GOLD)
    for x in range(CX - 4, CX + 5):  # the grand gate
        for y in range(1, 10): b.set(x, y, W1, AIR)
    b.arch_x(CX - 5, CX + 5, W1, 10, 3, GOLD)
    for (tx, tz) in ((W0, W0), (W1, W0), (W0, W1), (W1, W1)):
        b.cyl(tx, tz, 6, 0, 30, QB); b.cyl(tx, tz, 5, 1, 30, AIR)
        for y in range(5, 30, 6): b.cyl(tx, tz, 5, y, y, "minecraft:dark_oak_planks")
        for y in range(1, 30): b.set(tx + 4, y, tz, "minecraft:ladder[facing=west,waterlogged=false]")
        for y in range(5, 30, 6): b.set(tx + 4, y, tz, "minecraft:ladder[facing=west,waterlogged=false]")
        b.cyl(tx, tz, 6.5, 31, 31, GOLD); b.dome(tx, tz, 32, 6, s=GOLD, onion=True, tip=GOLD)
        for a in range(0, 360, 45):
            t = math.radians(a)
            for y in (8, 14, 20, 26): b.set(round(tx + 6 * math.cos(t)), y, round(tz + 6 * math.sin(t)), "minecraft:glass_pane")
        I.furnish(b, tx - 3, 6, tz - 3, tx + 3, tz + 3, 4, "barracks", CEL, seed=tx * 3 + tz)
    # ---------------- gardens: hedges, fountains and statues between the wall and the keep
    for (fx, fz) in ((28, 84), (84, 84), (28, 28), (84, 28)):
        b.cyl(fx, fz, 4, 1, 1, SQ, hollow=True); b.cyl(fx, fz, 3.5, 1, 1, WATER)
        b.column(fx, fz, 1, 4, PIL); b.set(fx, 5, fz, GOLD)
    for x in range(W0 + 3, W1 - 2):
        for z in (W0 + 3, W1 - 3):
            if abs(x - CX) > 6: b.set(x, 1, z, "minecraft:azalea_leaves[distance=7,persistent=true,waterlogged=false]")
    for x in range(CX - 2, CX + 3):
        for z in range(K1 + 1, W1): b.set(x, 0, z, "minecraft:red_concrete" if abs(x - CX) < 2 else GOLD)
    # ---------------- the keep
    b.box(K0, 0, K0, K1, 0, K1, "minecraft:polished_diorite")
    b.walls(K0, 1, K0, K1, 30, K1, QB); b.box(K0 + 1, 1, K0 + 1, K1 - 1, 30, K1 - 1, AIR)
    for fy in (10, 20): b.box(K0 + 1, fy, K0 + 1, K1 - 1, fy, K1 - 1, "minecraft:polished_diorite")
    b.box(K0 - 1, 31, K0 - 1, K1 + 1, 31, K1 + 1, GOLD)
    for x in range(K0, K1 + 1):
        for z in (K0, K1):
            if x % 3 == 0:
                for y in (3, 4, 5, 6, 13, 14, 15, 23, 24, 25): b.set(x, y, z, "minecraft:yellow_stained_glass_pane" if y in (6, 15, 25) else "minecraft:glass_pane")
            b.set(x, 10, z, GOLD); b.set(x, 20, z, GOLD)
    for z in range(K0, K1 + 1):
        for x in (K0, K1):
            if z % 3 == 0:
                for y in (3, 4, 5, 13, 14, 15, 23, 24, 25): b.set(x, y, z, "minecraft:glass_pane")
    for (px, pz) in ((K0, K0), (K1, K0), (K0, K1), (K1, K1)): b.round_column(px, pz, 1.6, 1, 31, PIL)
    for x in range(CX - 3, CX + 4):
        for y in range(1, 8): b.set(x, y, K1, AIR)
    # ground floor: the Room of Authority, the Empty Throne and the twenty swords
    for z in range(K0 + 2, K1): b.set(CX, 1, z, "minecraft:red_carpet"); b.set(CX - 1, 1, z, "minecraft:red_carpet"); b.set(CX + 1, 1, z, "minecraft:red_carpet")
    TZ = K0 + 6
    for k in range(5):  # the stair to the throne
        b.box(CX - 7 + k, 1 + k, TZ - 4, CX + 7 - k, 1 + k, TZ + 3 - k, SQ)
    b.box(CX - 2, 6, TZ - 3, CX + 2, 6, TZ - 1, GOLD)
    b.box(CX - 2, 7, TZ - 4, CX + 2, 14, TZ - 4, GOLD); b.set(CX, 7, TZ - 2, "minecraft:quartz_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
    b.set(CX - 2, 7, TZ - 2, GOLD); b.set(CX + 2, 7, TZ - 2, GOLD)
    b.sphere(CX, 15, TZ - 4, 2.2, GOLD)
    for i in range(20):  # swords of the twenty kingdoms round the throne
        a = math.radians(200 + i * 7)
        x, z = round(CX + 12 * math.cos(a)), round(TZ + 3 + 12 * math.sin(a)) if False else round(TZ + 6 + 12 * math.sin(a) * -1)
        b.set(x, 1, z, "minecraft:iron_block"); b.set(x, 2, z, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]"); b.set(x, 3, z, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    for z in range(K0 + 14, K1 - 1, 6):
        for x in (K0 + 4, K1 - 4): b.round_column(x, z, 1.2, 1, 9, PIL)
    I.furnish(b, K0 + 1, 1, K0 + 18, K0 + 10, K1 - 1, 8, "hall", CEL, seed=1)
    I.furnish(b, K1 - 10, 1, K0 + 18, K1 - 1, K1 - 1, 8, "hall", CEL, seed=2)
    # stairs between floors (east wall)
    for k in range(3):
        y0 = 1 + k * 10
        for i in range(9): b.set(K1 - 2, y0 + i, K0 + 3 + i, stairs("minecraft:quartz_stairs", "south"))
        for i in range(9): b.set(K1 - 2, y0 + 9, K0 + 3 + i, AIR) if k < 2 and i < 8 else None
    # first floor: the Five Elders' chamber, the hall of flowers, the cold room with the giant straw hat
    I.furnish(b, K0 + 1, 11, K0 + 1, CX - 1, CX - 1, 8, "dining", ELDER, seed=3)
    for x in range(K0 + 4, CX - 3): b.set(x, 11, CX - 9, "minecraft:dark_oak_planks"); b.set(x, 12, CX - 9, "minecraft:dark_oak_slab[type=bottom,waterlogged=false]")
    for x in range(K0 + 1, K1):
        for y in range(11, 20): b.set(x, y, CX, QB)
    for z in range(K0 + 1, K1):
        for y in range(11, 20): b.set(CX, y, z, QB)
    for (x, z) in ((CX - 3, CX), (CX + 3, CX), (CX, CX - 3), (CX, CX + 3)):
        b.set(x, 11, z, AIR); b.set(x, 12, z, AIR); b.set(x, 13, z, AIR)
    I.furnish(b, CX + 1, 11, K0 + 1, K1 - 3, CX - 1, 8, "library", ELDER, seed=4)
    for x in range(K0 + 1, CX):  # the hall of flowers: a flower wall dotted with wanted posters
        for y in range(12, 19):
            b.set(x, y, K1 - 1, rnd.choice(("minecraft:flowering_azalea_leaves[distance=7,persistent=true,waterlogged=false]", "minecraft:azalea_leaves[distance=7,persistent=true,waterlogged=false]", "minecraft:white_wool")))
    for k in range(5): b.set(K0 + 3 + k * 3, 15, K1 - 2, "minecraft:white_wall_banner[facing=north]")
    I.furnish(b, K0 + 1, 11, CX + 1, CX - 1, K1 - 2, 8, "hall", CEL, seed=5)
    CR = (CX + 1, CX + 1, K1 - 1, K1 - 1)
    for x in range(CR[0], CR[2] + 1):
        for z in range(CR[1], CR[3] + 1):
            b.set(x, 10, z, "minecraft:packed_ice")
            if x in (CR[0], CR[2]) or z in (CR[1], CR[3]):
                for y in range(11, 20): b.set(x, y, z, "minecraft:blue_ice") if b.get(x, y, z) in (None, AIR) else None
    HX, HZ = CX + 9, CX + 9  # the giant straw hat in the freezer
    b.cyl(HX, HZ, 6, 11, 11, "minecraft:hay_block[axis=y]"); b.cyl(HX, HZ, 3.2, 12, 15, "minecraft:hay_block[axis=y]")
    b.cyl(HX, HZ, 3.3, 12, 12, "minecraft:red_wool", hollow=True)
    # second floor: Imu's chamber
    I.furnish(b, K0 + 1, 21, K0 + 1, K1 - 3, K1 - 1, 9, "throne", CEL, seed=6)
    for x in range(K0 + 2, K1 - 2, 2):
        for z in (K0 + 1,): b.set(x, 24, z, "minecraft:white_banner[rotation=0]") if False else None
    # the central dome over the keep and its gold spire
    b.dome(CX, CZ, 32, 14, s=SQ, tip=GOLD)
    b.shape(lambda x, y, z: ((x - CX) / 13) ** 2 + ((y - 32) / 13) ** 2 + ((z - CZ) / 13) ** 2 < 1 and y >= 32, CX - 14, 32, CZ - 14, CX + 14, 46, CZ + 14, AIR, interior=None)
    b.cyl(CX, CZ, 13, 31, 31, "minecraft:polished_diorite")
    for y in range(47, 56): b.set(CX, y, CZ, GOLD)
    b.set(CX, 30, CZ, "minecraft:lantern[hanging=true,waterlogged=false]")
    for y in range(21, 31): b.set(K1 - 2, y, K1 - 3, "minecraft:ladder[facing=north,waterlogged=false]")
    b.set(K1 - 2, 31, K1 - 3, AIR)
    # ---------------- loot, Imu and the guards
    b.chest(K0 + 3, 1, K0 + 18, "celestial", "east"); b.chest(K1 - 3, 21, K0 + 3, "celestial", "west"); b.chest(HX - 4, 11, HZ, "legendary", "east")
    b.npc(CX, 7, TZ - 2, "imu", True)
    b.guards("cp0_agent", ((CX - 6, K1 + 4), (CX + 6, K1 + 4), (CX - 8, K0 + 20), (CX + 8, K0 + 20), (W0 + 8, CZ), (W1 - 8, CZ)))
    b.guards("seraphim", ((CX - 4, K0 + 14), (CX + 4, K0 + 14)))
    return b, 0
