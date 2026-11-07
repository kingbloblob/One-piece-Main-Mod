"""Franky House on the scrapyard shore of Water 7: the Franky Family's big blue-and-steel warehouse hideout with
the giant 'FRANKY' lettering and the star, built from salvage. Inside: the garage with the Franky Family's
machines and the Battle Franky robots, the party hall with the cola bar, the bunk room of the Franky Family, and
Franky's own workshop with the plans for the Adam ship. Outside: scrap heaps, cranes, cola crates, the canal with
the Square Sisters' boats and the Yagara Bull pens. ~84 x 72. Ground = y 0, the sea to the north."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "franky_house"
TITLE = "Franky House"
CUTS = [2, 8]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 84, 72
SEA_Z = 14
STEEL = "minecraft:iron_block"
BLUE = "minecraft:blue_concrete"
FAM = dict(wood="spruce", rug="blue", rug2="light_blue", bed="blue", light="minecraft:lantern", accent="onepiece:cola_crate",
           banner="blue", candle="light_blue")
X0, X1, Z0, Z1 = 18, 62, 26, 52


def scrap_heap(b, x, z, r, rnd):
    for y in range(0, int(r) + 2):
        rr = r * (1 - y / (r + 2))
        for i in range(int(rr * rr * 9) + 4):
            a = rnd.uniform(0, 2 * math.pi); d = rnd.uniform(0, rr)
            b.set(round(x + d * math.cos(a)), y + 1, round(z + d * math.sin(a)), rnd.choice(("minecraft:iron_block", "minecraft:anvil[facing=north]",
                  "minecraft:exposed_copper", "minecraft:weathered_copper", "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]",
                  "minecraft:chain[axis=x,waterlogged=false]", "minecraft:spruce_planks", "minecraft:barrel[facing=up,open=false]", "minecraft:coal_block")))


def build():
    rnd = random.Random(481)
    b = B()
    T.ground(b, NX, NZ, rnd, top="minecraft:gravel", deco=0.0)
    for x in range(NX):
        for z in range(NZ):
            if (x * 3 + z * 5) % 7 == 0: b.set(x, 0, z, "minecraft:coarse_dirt")
            elif z > 56 or x < 10: b.set(x, 0, z, "onepiece:water7_cobbles")
    T.sea(b, NX, NZ, lambda x, z: z < SEA_Z, depth=5)
    for x in range(NX): b.set(x, 0, SEA_Z, "onepiece:canal_bricks"); b.set(x, 1, SEA_Z, "onepiece:canal_bricks") if x % 5 == 0 else None
    # ---------------- the warehouse: steel frame, blue panels, sawtooth roof
    H = 14
    b.box(X0, 0, Z0, X1, 0, Z1, "minecraft:polished_andesite")
    b.walls(X0, 1, Z0, X1, H, Z1, BLUE)
    b.box(X0 + 1, 1, Z0 + 1, X1 - 1, H, Z1 - 1, AIR)
    for x in range(X0, X1 + 1, 4):
        for z in (Z0, Z1): b.column(x, z, 1, H, STEEL)
    for z in range(Z0, Z1 + 1, 4):
        for x in (X0, X1): b.column(x, z, 1, H, STEEL)
    for x in range(X0, X1 + 1):
        for z in (Z0, Z1): b.set(x, 6, z, STEEL); b.set(x, H, z, STEEL)
    for x in range(X0 + 2, X1 - 1, 4):
        for z in (Z0, Z1):
            for y in (8, 9, 10): b.set(x, y, z, "minecraft:light_blue_stained_glass_pane")
    for k, x in enumerate(range(X0, X1 + 1, 6)):  # sawtooth roof
        for dx in range(6):
            if x + dx > X1: break
            y = H + 1 + dx // 2
            for z in range(Z0, Z1 + 1): b.set(x + dx, y, z, "minecraft:light_blue_terracotta" if dx < 5 else "minecraft:glass")
            for yy in range(H + 1, y): b.set(x + dx, yy, Z0, BLUE); b.set(x + dx, yy, Z1, BLUE)
    # giant FRANKY lettering and the star on the facade
    b.text(X1 - 24, H + 5, Z1 + 1, "FRANKY", "minecraft:yellow_concrete")
    for x in range(X1 - 25, X1):
        for y in range(H + 4, H + 11): b.set(x, y, Z1, "minecraft:blue_concrete")
    sx, sy = X0 + 8, H + 7
    for a in range(5):  # a five-point star
        t = math.radians(90 + a * 72)
        b.line((sx, sy, Z1 + 1), (sx + 5 * math.cos(t), sy + 5 * math.sin(t), Z1 + 1), "minecraft:yellow_concrete")
    b.cyl(sx, Z1 + 1, 0, sy, sy, "minecraft:yellow_concrete")
    for x in range(sx - 6, sx + 7):
        for y in range(H + 1, H + 14): b.fill_if(x, y, Z1, BLUE)
    # big garage doors
    for x in range(X0 + 18, X0 + 27):
        for y in range(1, 7): b.set(x, y, Z1, AIR)
    for x in range(X0 + 18, X0 + 27): b.set(x, 6, Z1, "minecraft:iron_trapdoor[facing=south,half=top,open=false,powered=false,waterlogged=false]")
    # ---------------- inside: garage, party hall, bunks, Franky's workshop (and an upper gallery)
    b.box(X0 + 1, 6, Z0 + 1, X1 - 1, 6, Z0 + 9, "minecraft:spruce_planks")
    for x in range(X0 + 1, X1): b.set(x, 7, Z0 + 10, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]")
    for y in range(1, 7): b.set(X0 + 1, y, Z0 + 10, "minecraft:ladder[facing=east,waterlogged=false]")
    I.furnish(b, X0 + 15, 1, Z0 + 11, X0 + 30, Z1 - 1, 5, "workshop", FAM, seed=81)
    for (rx, rz) in ((X0 + 18, Z0 + 16), (X0 + 26, Z0 + 16)):  # Battle Franky robots under construction
        b.box(rx, 1, rz, rx + 2, 3, rz + 2, "minecraft:iron_block"); b.box(rx, 4, rz, rx + 2, 6, rz + 2, BLUE)
        b.set(rx + 1, 7, rz + 1, "minecraft:iron_block"); b.set(rx + 1, 7, rz + 3, "minecraft:redstone_lamp[lit=true]")
        b.column(rx - 1, rz + 1, 3, 5, STEEL); b.column(rx + 3, rz + 1, 3, 5, STEEL)
    b.walls(X0 + 14, 1, Z0 + 10, X0 + 14, 5, Z1 - 1, BLUE); b.set(X0 + 14, 1, Z0 + 18, AIR); b.set(X0 + 14, 2, Z0 + 18, AIR)
    b.walls(X0 + 31, 1, Z0 + 10, X0 + 31, 5, Z1 - 1, BLUE); b.set(X0 + 31, 1, Z0 + 18, AIR); b.set(X0 + 31, 2, Z0 + 18, AIR)
    I.furnish(b, X0 + 1, 1, Z0 + 11, X0 + 13, Z1 - 1, 5, "tavern", FAM, seed=82)
    I.furnish(b, X0 + 32, 1, Z0 + 11, X1 - 1, Z1 - 1, 5, "barracks", FAM, seed=83)
    I.subdivide(b, X0 + 1, 7, Z0 + 1, X1 - 1, Z0 + 9, 4, BLUE, ("study", "storage", "workshop", "bedroom"), FAM, cell=11, corridor=1,
                keepout=((X0 + 1, Z0 + 8, X0 + 3, Z0 + 9),), seed=84)
    for y in range(1, 6): b.set(X0 + 1, y, Z0 + 1, "minecraft:ladder[facing=south,waterlogged=false]")
    # ---------------- the scrapyard, cranes, cola crates
    for (x, z, r) in ((8, 30, 6), (70, 36, 7), (74, 62, 5), (10, 62, 5), (32, 64, 4), (54, 64, 4)): scrap_heap(b, x, z, r, rnd)
    for (cx, cz) in ((12, 18), (70, 18)):
        b.column(cx, cz, 1, 18, STEEL)
        for k in range(-3, 12): b.set(cx + k, 18, cz, STEEL)
        for y in range(10, 18): b.set(cx + 10, y, cz, "minecraft:chain[axis=y,waterlogged=false]")
        b.set(cx + 10, 9, cz, "minecraft:anvil[facing=north]")
    for i in range(10):
        x, z = rnd.randint(64, 80), rnd.randint(44, 54)
        if b.get(x, 1, z) is None: b.set(x, 1, z, "onepiece:cola_crate"); b.set(x, 2, z, "onepiece:cola_crate") if rnd.random() < 0.4 else None
    # ---------------- the canal dock with the Square Sisters' boats and Yagara pens
    T.pier(b, 34, SEA_Z - 10, 10, axis="z", boat=False)
    for (x0, c) in ((26, "blue"), (44, "light_blue")):
        b.box(x0, -1, 4, x0 + 6, -1, 8, "minecraft:spruce_planks"); b.box(x0, 0, 4, x0 + 6, 0, 8, f"minecraft:{c}_concrete")
        b.box(x0 + 1, 0, 5, x0 + 5, 0, 7, "minecraft:spruce_planks"); b.box(x0 + 2, 1, 5, x0 + 4, 2, 7, f"minecraft:{c}_concrete")
    for x in range(56, 74):
        for z in (4, 10): b.set(x, 1, z, "minecraft:spruce_fence") if b.get(x, 0, z) else b.set(x, 0, z, "minecraft:spruce_planks")
    T.path(b, [(X0 + 22, Z1 + 1), (X0 + 22, NZ - 2)], w=2, s="onepiece:water7_cobbles")
    T.path(b, [(X0 + 22, Z0 - 1), (X0 + 22, SEA_Z + 1)], w=2, s="onepiece:water7_cobbles")
    for x in range(X0, X1 + 1, 11): T.lamp_post(b, x, Z1 + 4)
    # ---------------- loot and the Franky Family
    b.chest(X1 - 3, 1, Z1 - 3, "medium", "west"); b.chest(X0 + 3, 7, Z0 + 3, "galley", "east")
    b.npc(X0 + 22, 1, Z0 + 20, "franky", False)
    b.guards("pirate", ((X0 + 6, Z0 + 20), (X0 + 40, Z0 + 20), (X0 + 22, Z1 + 6), (70, 30)))
    return b, 0
