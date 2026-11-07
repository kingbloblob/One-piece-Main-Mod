"""Navarone, the Marine fortress G-8: an impregnable base built on a sheer rocky island. Cliffs ring a sheltered
inner harbour reached by a sea gate, with a dry dock where ships are refitted. On the clifftop the fortress
proper: the multi-storey headquarters with Commodore Jonathan's office and the radar room, the famous kitchen and
mess run by Jessica, barracks, armory, the infirmary, gun batteries on every face, searchlight towers and the
long stair cut down the rock to the harbour. ~112 x 104. Ground (clifftop) = y 0, the harbour water at y -14."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "navarone"
TITLE = "Navarone (G-8 Fortress)"
CUTS = [2, 8, -10]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 112, 104
WALL = "minecraft:white_concrete"
BLUE = "minecraft:light_blue_concrete"
ROCK = "minecraft:stone"
HY = -14  # harbour water level
HX, HZ, HRX, HRZ = 56, 74, 26, 18  # the inner harbour ellipse
MAR = dict(wood="birch", rug="light_blue", rug2="white", bed="light_blue", light="minecraft:lantern", accent="onepiece:marine_bricks",
           banner="light_blue", candle="white")


def harbour(x, z):
    return ((x - HX) / HRX) ** 2 + ((z - HZ) / HRZ) ** 2 < 1 or (abs(x - HX) < 6 and z > HZ)


def build():
    rnd = random.Random(691)
    b = B()
    # ---------------- the rock island
    for x in range(NX):
        for z in range(NZ):
            for y in range(HY - 8, -1): b.set(x, y, z, ROCK if (x + y * 3 + z) % 9 else rnd.choice(("minecraft:andesite", "minecraft:cobblestone", "minecraft:tuff")))
            b.set(x, -1, z, "minecraft:dirt"); b.set(x, 0, z, "minecraft:grass_block" if rnd.random() > 0.08 else "minecraft:coarse_dirt")
            if harbour(x, z):
                for y in range(HY - 6, 2): b.set(x, y, z, WATER if y <= HY else AIR)
                b.set(x, HY - 7, z, "minecraft:gravel")
    # quay round the harbour
    for a in range(0, 360, 1):
        t = math.radians(a)
        for k in (0.0, 0.6, 1.2):
            x, z = round(HX + (HRX - 1 - k) * math.cos(t)), round(HZ + (HRZ - 1 - k) * math.sin(t))
            if 0 <= z < NZ - 1 and b.get(x, HY + 1, z) == AIR: b.set(x, HY, z, "minecraft:stone_bricks")
    for a in range(200, 341, 20):  # bollards and harbour lamps
        t = math.radians(a)
        b.set(round(HX + (HRX - 2) * math.cos(t)), HY + 1, round(HZ + (HRZ - 2) * math.sin(t)), "minecraft:stone_brick_wall")
    # the sea gate
    for x in range(HX - 8, HX + 9):
        for y in range(HY - 2, 2): b.set(x, y, NZ - 3, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]" if y > HY + 6 or abs(x - HX) > 5 else (WATER if y <= HY else AIR))
        b.set(x, 2, NZ - 3, WALL); b.set(x, 3, NZ - 3, BLUE)
    # dry dock with a ship's hull in it (west of the harbour)
    for x in range(HX - 22, HX - 8):
        for z in range(HZ - 6, HZ + 2): b.set(x, HY, z, "minecraft:smooth_stone")
    b.hull(HX - 22, 15, HZ - 2, 7, HY + 1, HY + 5, "minecraft:white_concrete", bottom="minecraft:light_gray_concrete", rail="minecraft:birch_fence", bow_len=5, stern_len=2, fill_deck="minecraft:birch_planks")
    # the long stair down the rock
    for i in range(15):
        for dx in (0, 1, 2):
            b.set(20 + dx, -i, 48 + i, stairs("minecraft:stone_brick_stairs", "north"))
            for y in range(-i + 1, -i + 4): b.set(20 + dx, y, 48 + i, AIR)
    for y in range(HY, 1):
        for dx in (0, 1, 2):
            b.set(20 + dx, y, 63, "minecraft:stone_bricks") if y == HY else None
    # ---------------- the fortress on the clifftop
    FX0, FZ0, FX1, FZ1 = 28, 8, 84, 46
    b.box(FX0, 0, FZ0, FX1, 0, FZ1, "minecraft:polished_andesite")
    b.walls(FX0, 1, FZ0, FX1, 24, FZ1, WALL)
    b.box(FX0 + 1, 1, FZ0 + 1, FX1 - 1, 24, FZ1 - 1, AIR)
    for fy in (6, 12, 18, 24): b.box(FX0 + 1, fy, FZ0 + 1, FX1 - 1, fy, FZ1 - 1, "minecraft:birch_planks")
    b.box(FX0 - 1, 25, FZ0 - 1, FX1 + 1, 25, FZ1 + 1, BLUE)
    for x in range(FX0, FX1 + 1):
        for fy in (6, 12, 18): b.set(x, fy, FZ0, BLUE); b.set(x, fy, FZ1, BLUE)
        if x % 3 == 1:
            for fy in (2, 8, 14, 20):
                for z in (FZ0, FZ1): b.set(x, fy, z, "minecraft:glass_pane"); b.set(x, fy + 1, z, "minecraft:glass_pane"); b.set(x, fy + 2, z, "minecraft:glass_pane")
    for z in range(FZ0, FZ1 + 1):
        if z % 3 == 1:
            for fy in (2, 8, 14, 20):
                for x in (FX0, FX1): b.set(x, fy, z, "minecraft:glass_pane"); b.set(x, fy + 1, z, "minecraft:glass_pane")
    GX = (FX0 + FX1) // 2
    for x in range(GX - 2, GX + 3):
        for y in range(1, 5): b.set(x, y, FZ1, AIR)
    b.text(GX + 7, 27, FZ1, "G-8", BLUE, step=-1) if False else None
    b.box(GX - 9, 26, FZ1, GX + 9, 33, FZ1, WALL)
    b.text(GX + 6, 27, FZ1 + 1, "G8", "minecraft:blue_concrete", step=-1) if False else None
    for x in range(GX - 8, GX + 9):  # the gull mark on the front
        for y in range(27, 33):
            u, v = (x - GX) / 8.0, (y - 30) / 3.0
            if abs(v + 0.6 * abs(u) - 0.4) < 0.35 and abs(u) < 0.95: b.set(x, y, FZ1 + 1, "minecraft:blue_concrete")
    for k in range(4):  # stair core
        for i in range(6): b.set(FX0 + 2 + i, k * 6 + 1 + i, FZ0 + 2, stairs("minecraft:birch_stairs", "east"))
        for i in range(5): b.set(FX0 + 2 + i, (k + 1) * 6, FZ0 + 2, AIR)
    I.subdivide(b, FX0 + 9, 1, FZ0 + 1, FX1 - 1, FZ1 - 1, 5, WALL, ("kitchen", "dining", "dining", "storage", "bath", "kitchen"), MAR, cell=13, seed=1)
    I.subdivide(b, FX0 + 9, 7, FZ0 + 1, FX1 - 1, FZ1 - 1, 5, WALL, ("barracks", "barracks", "armory", "barracks", "barracks", "armory"), MAR, cell=13, seed=2)
    I.subdivide(b, FX0 + 9, 13, FZ0 + 1, FX1 - 1, FZ1 - 1, 5, WALL, ("lab", "bedroom", "library", "bedroom", "storage", "lab"), MAR, cell=13, seed=3)
    I.subdivide(b, FX0 + 9, 19, FZ0 + 1, FX1 - 1, FZ1 - 1, 5, WALL, ("study", "hall", "throne", "study"), MAR, cell=15, seed=4)
    # radar dome and searchlight towers on the roof
    b.dome(GX - 14, FZ0 + 14, 26, 6, h=6, s="minecraft:white_concrete", tip="minecraft:iron_block")
    for (x, z) in ((FX0, FZ0), (FX1, FZ0), (FX0, FZ1), (FX1, FZ1)):
        b.box(x - 2, 25, z - 2, x + 2, 34, z + 2, WALL); b.box(x - 3, 35, z - 3, x + 3, 35, z + 3, BLUE)
        b.set(x, 36, z, "minecraft:sea_lantern"); b.set(x, 37, z, "minecraft:iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
    # ---------------- gun batteries on every face of the cliffs
    for x in range(6, NX - 6, 10):
        b.set(x, 1, 3, "onepiece:cannon[facing=north]"); b.box(x - 1, 1, 2, x + 1, 1, 2, "minecraft:stone_brick_wall")
    for z in range(10, NZ - 30, 10):
        b.set(3, 1, z, "onepiece:cannon[facing=west]"); b.set(NX - 4, 1, z, "onepiece:cannon[facing=east]")
    for a in range(30, 160, 18):
        t = math.radians(a)
        b.set(round(HX + (HRX + 3) * math.cos(t)), 1, round(HZ - (HRZ + 3) * math.sin(t)), "onepiece:cannon[facing=south]") if False else None
    # helipad-like drill ground and the fuel shed
    for x in range(FX0 - 18, FX0 - 4, 4):
        for z in range(12, 40, 6): b.set(x, 1, z, "onepiece:training_post[facing=east]")
    T.house(b, FX1 + 6, 10, 14, 10, floors=2, style="marine", rnd=random.Random(1), kinds=("storage", "barracks"), door="west")
    T.house(b, FX1 + 6, 26, 14, 10, floors=1, style="marine", rnd=random.Random(2), kinds=("workshop",), door="west")
    for (x, z) in ((40, 52), (72, 52), (30, 54)): T.lamp_post(b, x, z)
    # ---------------- loot and garrison
    b.chest(GX + 10, 19, FZ0 + 4, "marine", "west"); b.chest(FX0 + 12, 7, FZ1 - 3, "marine", "north"); b.chest(HX - 12, HY + 6, HZ - 2, "medium", "east")
    b.guards("marine", ((GX - 6, FZ1 + 4), (GX + 6, FZ1 + 4), (HX - 18, HZ - 14), (HX + 18, HZ - 14), (GX, 20)))
    b.guards("marine_rifle", ((FX0, FZ0), (FX1, FZ1)), y=36)
    b.guards("elite_marine", ((GX, FZ0 + 20),), y=19)
    return b, 0
