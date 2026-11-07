"""Buggy's Big Top in Orange Town: the town Buggy took over. Orange-roofed houses on cobbled streets (all furnished),
the tavern with Buggy's rooftop throne and flag, the striped circus Big Top in the square with its ring, bleachers,
trapeze and cages, the Buggy Ball cannon aimed down the main street, and Chouchou's pet food shop.
~110 x 110. Ground = y 0."""
import math, random
from canvas import *
import interiors as I

SID = "buggy_big_top"
TITLE = "Buggy's Big Top (Orange Town)"
CUTS = [6]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 110
CX, CZ = 55, 58
ROOF = "onepiece:dressrosa_tiles"
ROOF_ST = "onepiece:dressrosa_tile_stairs"
STUCCO = "onepiece:dressrosa_stucco"
COBBLE = "onepiece:water7_cobbles"


def town_house(b, x0, z0, w, d, floors, rnd, door="south"):
    wallm = rnd.choice((STUCCO, "minecraft:white_terracotta", "minecraft:smooth_sandstone", "minecraft:orange_terracotta", STUCCO))
    h = floors * 5
    b.box(x0, 0, z0, x0 + w - 1, 0, z0 + d - 1, "minecraft:spruce_planks")
    b.walls(x0, 1, z0, x0 + w - 1, h, z0 + d - 1, wallm)
    b.box(x0 + 1, 1, z0 + 1, x0 + w - 2, h, z0 + d - 2, AIR)
    for (px, pz) in ((x0, z0), (x0 + w - 1, z0), (x0, z0 + d - 1), (x0 + w - 1, z0 + d - 1)): b.column(px, pz, 1, h, "minecraft:stripped_dark_oak_log[axis=y]")
    for f in range(floors):
        fy = f * 5
        if f: b.box(x0 + 1, fy, z0 + 1, x0 + w - 2, fy, z0 + d - 2, "minecraft:spruce_planks")
        for x in range(x0 + 2, x0 + w - 2, 2):
            for z in (z0, z0 + d - 1): b.set(x, fy + 2, z, PANE); b.set(x, fy + 3, z, PANE)
        for z in range(z0 + 2, z0 + d - 2, 2):
            for x in (x0, x0 + w - 1): b.set(x, fy + 2, z, PANE); b.set(x, fy + 3, z, PANE)
        for x in range(x0 + 2, x0 + w - 2, 2):  # flower boxes under the upstairs windows
            if f: b.set(x, fy + 1, z0 + d, "minecraft:spruce_trapdoor[facing=south,half=top,open=false,powered=false,waterlogged=false]")
    if floors > 1:
        b.box(x0 + w - 2, 5, z0 + 1, x0 + w - 2, 5, z0 + 5, AIR)
        b.stairs_up(x0 + w - 2, 1, z0 + 6, 5, "minecraft:spruce_stairs", "north")
    dx = x0 + w // 2; dz = z0 + d - 1 if door == "south" else z0
    b.set(dx, 1, dz, f"minecraft:spruce_door[facing={door},half=lower,hinge=left,open=false,powered=false]")
    b.set(dx, 2, dz, f"minecraft:spruce_door[facing={door},half=upper,hinge=left,open=false,powered=false]")
    b.set(dx, 3, dz + (1 if door == "south" else -1), lantern())
    b.gable_roof(x0, z0, x0 + w - 1, z0 + d - 1, h + 1, ROOF_ST, ROOF)
    b.set(x0 + 1, h + 4, z0 + 1, "minecraft:bricks"); b.set(x0 + 1, h + 5, z0 + 1, "minecraft:bricks")
    for f in range(floors):
        kind = rnd.choice(("kitchen", "tavern", "storage", "workshop", "dining")) if f == 0 else rnd.choice(("bedroom", "bedroom", "study"))
        I.furnish(b, x0 + 1, f * 5 + 1, z0 + 1, x0 + w - 2, z0 + d - 2, 4, kind, "pirate", seed=rnd.randint(0, 99999))
    return h


def stripes(x, y, z):
    a = math.atan2(z - CZ, x - CX)
    return "minecraft:red_wool" if int((a + math.pi) / (2 * math.pi) * 24) % 2 else "minecraft:white_wool"


def build():
    rnd = random.Random(1)
    b = B()
    # ---------------- ground: grass edges, cobbled streets
    for x in range(N):
        for z in range(N):
            for y in (-3, -2, -1): b.set(x, y, z, "minecraft:dirt")
            street = abs(x - CX) <= 4 or abs(z - CZ) <= 4 or 14 <= x <= 18 or 92 <= x <= 96 or 14 <= z <= 18 or 96 <= z <= 100
            sq = math.hypot(x - CX, z - CZ) < 30
            b.set(x, 0, z, COBBLE if (street or sq) else "minecraft:grass_block")
    # ---------------- houses: blocks between the streets
    lots = []
    for (xa, xb) in ((19, 50), (60, 91)):
        for (za, zb) in ((19, 53), (63, 95)):
            lots.append((xa, za, xb, zb))
    for (xa, za, xb, zb) in lots:
        for x in range(xa, xb - 8, 11):
            for (z, door) in ((za, "north"), (zb - 9, "south")):
                if math.hypot(x + 4 - CX, z + 4 - CZ) < 34: continue
                town_house(b, x, z, 9, 9, rnd.choice((1, 2, 2)), rnd, door)
    for z in range(22, 92, 12):
        for x in (3, 101):
            if 50 < z < 66: continue
            town_house(b, x, z, 8, 9, rnd.choice((1, 2)), rnd, "south")
    # ---------------- the tavern Buggy took over (north of the square), roof terrace with his throne
    TX0, TZ0, TX1, TZ1 = CX - 9, 8, CX + 9, 22
    b.box(TX0, 0, TZ0, TX1, 0, TZ1, "minecraft:spruce_planks")
    b.walls(TX0, 1, TZ0, TX1, 10, TZ1, STUCCO)
    b.box(TX0 + 1, 1, TZ0 + 1, TX1 - 1, 10, TZ1 - 1, AIR)
    b.box(TX0 + 1, 5, TZ0 + 1, TX1 - 1, 5, TZ1 - 1, "minecraft:spruce_planks")
    b.box(TX0, 11, TZ0, TX1, 11, TZ1, "minecraft:spruce_planks")
    for x in range(TX0, TX1 + 1):
        for z in (TZ0, TZ1): b.set(x, 12, z, fence("dark_oak"))
    for z in range(TZ0, TZ1 + 1):
        for x in (TX0, TX1): b.set(x, 12, z, fence("dark_oak"))
    for (px, pz) in ((TX0, TZ0), (TX1, TZ0), (TX0, TZ1), (TX1, TZ1)): b.column(px, pz, 1, 12, "minecraft:stripped_dark_oak_log[axis=y]")
    for x in range(TX0 + 2, TX1 - 1, 3):
        for y in (2, 3, 7, 8): b.set(x, y, TZ1, PANE); b.set(x, y, TZ0, PANE)
    for x in (CX - 1, CX, CX + 1):
        for y in (1, 2, 3): b.set(x, y, TZ1, AIR)
    b.box(CX - 3, 4, TZ1 + 1, CX + 3, 4, TZ1 + 2, "minecraft:red_wool")  # awning
    b.box(CX - 5, 6, TZ1 + 1, CX + 5, 9, TZ1 + 1, "minecraft:dark_oak_planks")
    b.text(CX - 4, 7, TZ1 + 2, "BAR", "minecraft:yellow_concrete") if hasattr(b, "text") else None
    b.stairs_up(TX1 - 2, 1, TZ0 + 2, 4, "minecraft:spruce_stairs", "south")
    b.box(TX1 - 2, 5, TZ0 + 2, TX1 - 2, 5, TZ0 + 5, AIR)
    for y in range(6, 12): b.set(TX0 + 2, y, TZ0 + 1, ladder("south"))
    b.set(TX0 + 2, 11, TZ0 + 1, trapdoor("minecraft:spruce_trapdoor", "south"))
    I.furnish(b, TX0 + 1, 1, TZ0 + 1, TX1 - 1, TZ1 - 1, 4, "tavern", "pirate")
    I.furnish(b, TX0 + 1, 6, TZ0 + 1, TX1 - 1, TZ1 - 1, 5, "captain", "pirate")
    # Buggy's throne on the roof, flag behind
    b.box(CX - 2, 12, TZ0 + 4, CX + 2, 12, TZ0 + 6, "minecraft:red_wool")
    b.set(CX, 13, TZ0 + 5, stairs("minecraft:dark_oak_stairs", "north")); b.set(CX - 1, 13, TZ0 + 5, "minecraft:yellow_wool"); b.set(CX + 1, 13, TZ0 + 5, "minecraft:yellow_wool")
    b.box(CX - 1, 14, TZ0 + 4, CX + 1, 15, TZ0 + 4, "minecraft:red_wool")
    for (x, z) in ((CX - 6, TZ0 + 9), (CX + 6, TZ0 + 9)): b.set(x, 12, z, "onepiece:sake_barrel[axis=y]"); b.set(x, 13, z, lantern())
    for y in range(12, 28): b.set(CX, y, TZ0 + 1, fence("dark_oak"))
    b.jolly_roger(CX, 21, TZ0 + 1, 11, 7, axis="x") if False else None
    for x in range(CX - 6, CX + 1):  # Buggy's flag: skull with a red nose
        for y in range(21, 28): b.set(x, y, TZ0 + 1, "minecraft:black_wool")
    for (dx, dy) in ((-3, 25), (-4, 25), (-2, 25), (-3, 26), (-4, 26), (-2, 26), (-3, 24), (-4, 23), (-2, 23), (-5, 22), (-1, 22)):
        b.set(CX + dx, dy, TZ0 + 1, "minecraft:white_wool")
    b.set(CX - 3, 24, TZ0 + 1, "minecraft:red_wool")
    # ---------------- the Big Top in the square
    R, H = 19, 24
    def in_tent(x, y, z):
        d = math.hypot(x - CX, z - CZ)
        if y < 1 or d > R: return False
        if y <= 8: return True
        return d <= R * (1 - (y - 8) / (H - 8)) ** 0.8 + 0.5
    b.shape(in_tent, CX - R - 1, 1, CZ - R - 1, CX + R + 1, H, CZ + R + 1, stripes, interior=AIR)
    b.cyl(CX, CZ, R, 9, 9, "minecraft:yellow_wool", hollow=True)  # scalloped trim
    for a in range(0, 360, 15):
        t = math.radians(a); b.set(round(CX + (R + 1) * math.cos(t)), 8, round(CZ + (R + 1) * math.sin(t)), "minecraft:yellow_wool")
    for y in range(1, H + 6): b.set(CX, y, CZ, "minecraft:stripped_spruce_log[axis=y]")
    b.box(CX, H + 3, CZ + 1, CX, H + 5, CZ + 4, "minecraft:red_wool")
    for a in range(0, 360, 60):
        t = math.radians(a)
        px, pz = round(CX + R * 0.6 * math.cos(t)), round(CZ + R * 0.6 * math.sin(t))
        for y in range(1, 15): b.set(px, y, pz, "minecraft:stripped_spruce_log[axis=y]")
    for x in range(CX - 3, CX + 4):  # entrance flap facing the main street (south)
        for y in range(1, 7):
            z = round(CZ + math.sqrt(max(0, R * R - (x - CX) ** 2)))
            for zz in (z, z - 1): b.set(x, y, zz, AIR)
    b.set(CX - 4, 7, CZ + R, "minecraft:red_banner[rotation=0]"); b.set(CX + 4, 7, CZ + R, "minecraft:red_banner[rotation=0]")
    # inside: the ring, bleachers, trapeze, cages, the cannon act
    b.disk(CX, 0, CZ, 8, "minecraft:sand")
    b.cyl(CX, CZ, 8, 1, 1, "minecraft:red_concrete", hollow=True)
    for a in range(0, 360, 20):
        t = math.radians(a); b.set(round(CX + 8 * math.cos(t)), 1, round(CZ + 8 * math.sin(t)), "minecraft:white_concrete")
    for step in range(4):
        rr = 11 + step * 2
        for a in range(0, 3600, 7):
            t = math.radians(a / 10)
            if abs(math.degrees(t) - 90) < 18: continue  # aisle at the entrance
            x, z = round(CX + rr * math.cos(t)), round(CZ + rr * math.sin(t))
            for k in range(2):
                xx, zz = round(CX + (rr + k) * math.cos(t)), round(CZ + (rr + k) * math.sin(t))
                b.set(xx, step + 1, zz, "minecraft:red_concrete" if k else stairs("minecraft:dark_oak_stairs", "north"))
                for y in range(1, step + 1): b.set(xx, y, zz, "minecraft:dark_oak_planks")
    for (x, z) in ((CX - 6, CZ), (CX + 6, CZ)):
        b.column(x, z, 1, 14, "minecraft:iron_bars[east=false,north=true,south=true,west=false,waterlogged=false]")
        b.box(x - 1, 14, z - 1, x + 1, 14, z + 1, "minecraft:spruce_planks")
    for x in range(CX - 5, CX + 6): b.set(x, 13, CZ, "minecraft:iron_chain[axis=x]")
    b.set(CX, 12, CZ, "minecraft:dark_oak_fence")
    for (x, z) in ((CX - 4, CZ - 4), (CX + 4, CZ + 3)):  # Richie's cage and props
        b.walls(x - 1, 1, z - 1, x + 1, 3, z + 1, "minecraft:iron_bars")
        b.set(x, 4, z, "minecraft:gold_block")
    for (x, z, c) in ((CX + 3, CZ - 5, "red"), (CX - 2, CZ + 5, "yellow"), (CX + 5, CZ + 1, "blue")):
        b.sphere(x, 2, z, 1.4, f"minecraft:{c}_concrete")
    b.set(CX, 1, CZ - 6, "onepiece:cannon[facing=south]")
    for (dx, dz) in ((0, -3), (3, 0), (-3, 0)): b.set(CX + dx, 14, CZ + dz, lantern(True))
    # ---------------- the Buggy Ball cannon aimed down the main street
    bx, bz = CX, 92
    b.box(bx - 4, 0, bz - 4, bx + 4, 1, bz + 4, "minecraft:polished_andesite")
    b.cyl(bx, bz, 2.5, 2, 3, "minecraft:dark_oak_planks")
    for i in range(10):
        b.cyl(bx, bz - 2 + i, 1.8 if i < 8 else 2.3, 4, 4, "minecraft:black_concrete") if False else None
        for (dy, dx) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            b.set(bx + dx, 4 + dy, bz + 2 - i, "minecraft:black_concrete" if i < 9 else "minecraft:gray_concrete")
    for (x, z) in ((bx - 4, bz + 5), (bx - 3, bz + 6), (bx + 4, bz + 5)): b.sphere(x, 1, z, 1.2, "minecraft:black_concrete")
    # the blasted street: a crater and rubble behind the cannon's line of fire
    for (x, z) in ((CX - 2, 104), (CX + 3, 106)):
        b.sphere(x, 0, z, 3, AIR); b.set(x, -2, z, "minecraft:cobblestone")
    # ---------------- Chouchou's pet food shop
    sx, sz = 80, 100
    b.box(sx, 0, sz, sx + 8, 0, sz + 6, "minecraft:spruce_planks")
    b.walls(sx, 1, sz, sx + 8, 5, sz + 6, "minecraft:white_terracotta")
    b.box(sx + 1, 1, sz + 1, sx + 7, 5, sz + 5, AIR)
    b.gable_roof(sx, sz, sx + 8, sz + 6, 6, ROOF_ST, ROOF)
    b.set(sx + 4, 1, sz, AIR); b.set(sx + 4, 2, sz, AIR)
    b.box(sx + 2, 4, sz - 1, sx + 6, 4, sz - 1, "minecraft:light_blue_wool")
    I.furnish(b, sx + 1, 1, sz + 1, sx + 7, sz + 5, 4, "storage", "pirate", seed=3)
    b.entities.append(("minecraft:wolf", sx + 4, 1, sz - 2, {"Sitting": Byte(1), "PersistenceRequired": Byte(1), "CustomName": "Chouchou"}))
    # ---------------- town dressing: lamps, crates, posters
    for x in range(8, N - 4, 10):
        for z in (CZ - 6, CZ + 6):
            if abs(x - CX) > R + 2: b.column(x, z, 1, 3, fence("dark_oak")); b.set(x, 4, z, lantern())
    for i in range(30):
        x, z = rnd.randint(6, N - 6), rnd.randint(6, N - 6)
        if b.get(x, 1, z) in (None, AIR) and b.get(x, 0, z) == COBBLE: b.set(x, 1, z, rnd.choice((BARREL, "onepiece:mikan_crate[axis=y]", "minecraft:hay_block[axis=y]", "minecraft:composter[level=0]")))
    # ---------------- people
    b.npc(CX, 12, TZ0 + 7, "buggy", True)
    b.chest(CX + 3, 12, TZ0 + 5, "easy", "south"); b.chest(CX - 7, 1, CZ + 2, "easy", "east")
    b.guards("buggy_pirate", ((CX - 3, 12 + 0), (CX + 3, CZ + 22), (CX - 8, CZ + 12), (CX + 10, CZ - 12)), y=1) if False else None
    b.guards("buggy_pirate", ((CX - 6, TZ1 + 4), (CX + 6, TZ1 + 4), (CX - 10, CZ + 24), (CX + 10, CZ + 24), (CX, 88), (CX - 12, CZ)))
    return b, 0
