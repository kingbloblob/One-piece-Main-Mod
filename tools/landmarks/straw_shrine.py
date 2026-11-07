"""Basil Hawkins' Straw Shrine: the magician's hideaway in a misty swamp forest. A towering straw effigy of the
Straw Man (Hawkins' Devil Fruit form) sits behind a shrine hall full of tarot cards, candles and straw dolls;
a torii path over the swamp on boardwalks, a fortune-teller's hut, his crew's camp and a ring of hanging straw
dolls in the dead trees. ~90 x 90. Ground = y 0."""
import math, random
from canvas import *
import interiors as I

SID = "straw_shrine"
TITLE = "Hawkins' Straw Shrine"
CUTS = [4]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 92
CX, CZ = 46, 40
STRAW = "minecraft:hay_block[axis=y]"
STRAW_X = "minecraft:hay_block[axis=x]"
ROOF = "onepiece:wano_roof_tiles"
ROOF_ST = "onepiece:wano_roof_tile_stairs"
WOOD = "onepiece:gloom_planks"


def straw_doll(b, x, y, z):
    b.set(x, y, z, STRAW); b.set(x, y + 1, z, STRAW)
    b.set(x - 1, y + 1, z, "minecraft:wheat[age=7]" if False else "minecraft:spruce_fence"); b.set(x + 1, y + 1, z, "minecraft:spruce_fence")
    b.set(x, y + 2, z, "minecraft:carved_pumpkin[facing=south]" if (x + z) % 5 == 0 else STRAW)


def build():
    rnd = random.Random(31)
    b = B()
    # ---------------- swamp: mud, water channels, dead trees, mist
    for x in range(N):
        for z in range(N):
            for y in (-4, -3, -2, -1): b.set(x, y, z, "minecraft:mud" if y > -3 else "minecraft:dirt")
            wet = (math.sin(x * 0.21) + math.cos(z * 0.17) + math.sin((x + z) * 0.11)) > 1.1 and math.hypot(x - CX, z - CZ) > 22
            b.set(x, 0, z, WATER if wet else ("minecraft:mud" if (x * z) % 7 == 0 else "minecraft:grass_block"))
            if wet: b.set(x, -1, z, WATER)
            elif rnd.random() < 0.04: b.set(x, 1, z, rnd.choice(("minecraft:short_grass", "minecraft:fern", "minecraft:brown_mushroom")))
            if wet and rnd.random() < 0.06: b.set(x, 1, z, "minecraft:lily_pad")
    for i in range(36):
        a = rnd.uniform(0, 2 * math.pi); rr = rnd.uniform(28, 44)
        x, z = round(CX + rr * math.cos(a)), round(CZ + rr * math.sin(a) * 0.95)
        if not (2 < x < N - 3 and 2 < z < N - 3): continue
        h = rnd.randint(7, 13)
        for y in range(1, h): b.set(x, y, z, "minecraft:mangrove_log[axis=y]" if i % 3 else "onepiece:gloom_log[axis=y]")
        for k in range(3):
            ax, az = rnd.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
            for j in range(1, 4): b.set(x + ax * j, h - 2 - k + j // 2, z + az * j, "minecraft:mangrove_log[axis=x]" if ax else "minecraft:mangrove_log[axis=z]")
            if k == 0:
                for j in range(1, 3): b.set(x + ax * 3, h - 2 - j, z + az * 3, "minecraft:iron_chain[axis=y]" if False else "minecraft:spruce_fence")
                b.set(x + ax * 3, h - 5, z + az * 3, STRAW)  # a straw doll hanging from the branch
        for k in range(5):
            b.set(x + rnd.randint(-1, 1), h - rnd.randint(0, 6), z + rnd.randint(-1, 1), "minecraft:vine[east=false,north=true,south=false,up=false,west=false]") if False else None
    # ---------------- boardwalk path with torii from the south edge to the shrine
    for z in range(CZ + 18, N):
        for x in range(CX - 2, CX + 3): b.set(x, 1 if b.get(x, 0, z) == WATER else 0, z, "minecraft:spruce_planks" if abs(x - CX) < 2 else "minecraft:stripped_spruce_log[axis=z]")
        if z % 4 == 0:
            for x in (CX - 3, CX + 3): b.column(x, z, 0, 2, "minecraft:spruce_fence"); b.set(x, 3, z, I.candle_str("white", 2))
    for z in range(CZ + 22, N - 2, 10):
        for x in (CX - 4, CX + 4): b.column(x, z, 1, 9, "minecraft:red_concrete")
        for x in range(CX - 6, CX + 7): b.set(x, 9, z, "minecraft:red_concrete"); b.set(x, 11, z, "minecraft:black_concrete")
        b.set(CX, 10, z, "minecraft:red_concrete")
        for x in range(CX - 3, CX + 4, 2): b.set(x, 8, z, "minecraft:spruce_fence"); b.set(x, 7, z, STRAW)  # straw tassels
    # ---------------- the shrine platform and hall
    b.box(CX - 16, 0, CZ - 16, CX + 16, 1, CZ + 16, "minecraft:stone_bricks")
    for x in range(CX - 16, CX + 17):
        for z in (CZ - 16, CZ + 16): b.set(x, 2, z, "minecraft:stone_brick_wall") if x % 2 else None
    HX0, HX1, HZ0, HZ1 = CX - 11, CX + 11, CZ + 0, CZ + 14
    b.walls(HX0, 2, HZ0, HX1, 8, HZ1, WOOD)
    b.box(HX0 + 1, 2, HZ0 + 1, HX1 - 1, 8, HZ1 - 1, AIR)
    b.box(HX0 + 1, 1, HZ0 + 1, HX1 - 1, 1, HZ1 - 1, "onepiece:tatami")
    for x in range(HX0, HX1 + 1, 4):
        for z in (HZ0, HZ1): b.column(x, z, 2, 8, "minecraft:red_concrete")
    for x in range(HX0 + 2, HX1 - 1, 4):
        for z in (HZ0, HZ1): b.set(x, 4, z, "onepiece:shoji_screen"); b.set(x, 5, z, "onepiece:shoji_screen")
    b.box(HX0 + 1, 9, HZ0 + 1, HX1 - 1, 9, HZ1 - 1, "minecraft:dark_oak_planks")
    b.pagoda_roof(CX, (HZ0 + HZ1) // 2, 14, 10, 9, ROOF_ST, ROOF, layers=3)
    for x in (CX - 1, CX, CX + 1):
        for y in (2, 3, 4): b.set(x, y, HZ1, AIR)
    r = I.furnish(b, HX0 + 1, 2, HZ0 + 1, HX1 - 1, HZ1 - 1, 6, "shrine", "gloom")
    for x in range(HX0 + 2, HX1 - 1, 2):  # rows of candles and straw dolls on low altars
        b.set(x, 2, HZ0 + 2, "minecraft:dark_oak_slab[type=top,waterlogged=false]"); b.set(x, 3, HZ0 + 2, I.candle_str("white", rnd.randint(1, 4)) if x % 4 else STRAW)
    b.box(CX - 2, 2, HZ0 + 4, CX + 2, 2, HZ0 + 6, "minecraft:dark_oak_planks")  # the tarot table
    for x in range(CX - 2, CX + 3): b.set(x, 3, HZ0 + 5, "minecraft:white_carpet" if x % 2 else "minecraft:black_carpet")
    r.paintings(6)
    # ---------------- the giant Straw Man effigy behind the shrine
    SX, SZ = CX, CZ - 12
    def body(x, y, z):
        dx, dz = x - SX, z - SZ
        if 1 <= y <= 14 and (dx / 2.8) ** 2 + (dz / 2.2) ** 2 <= 1 and abs(dx) >= 1: return True  # legs (two)
        if 14 <= y <= 28 and (dx / 6.5) ** 2 + (dz / 4.0) ** 2 <= 1: return True   # torso
        if 29 <= y <= 36 and dx * dx + dz * dz + ((y - 32) * 1.1) ** 2 <= 16: return True  # head
        return False
    for x in range(SX - 8, SX + 9):
        for y in range(1, 37):
            for z in range(SZ - 6, SZ + 7):
                if body(x, y, z): b.set(x, y, z, STRAW if (y + x) % 5 else STRAW_X)
    for side in (-1, 1):  # arms reaching out, nails driven in
        for i in range(14):
            x = SX + side * (6 + i); y = 26 - i // 3
            b.cyl(x, SZ, 1.6, y, y + 1, STRAW_X)
        b.set(SX + side * 20, 22, SZ, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]")
    for (dx, dy) in ((-2, 33), (2, 33)): b.set(SX + dx, dy, SZ + 4, "minecraft:black_concrete")
    b.set(SX - 1, 31, SZ + 4, "minecraft:black_concrete"); b.set(SX, 30, SZ + 4, "minecraft:black_concrete"); b.set(SX + 1, 31, SZ + 4, "minecraft:black_concrete")
    for y in range(14, 30, 4):  # rope binding
        for a in range(0, 360, 20):
            t = math.radians(a); b.set(round(SX + 6.8 * math.cos(t)), y, round(SZ + 4.3 * math.sin(t)), "minecraft:brown_wool")
    for y in range(36, 40): b.set(SX, y, SZ, "minecraft:hay_block[axis=y]")
    # ---------------- fortune teller's hut and the crew's camp
    fx, fz = CX + 26, CZ + 2
    b.box(fx - 4, 0, fz - 4, fx + 4, 0, fz + 4, "minecraft:spruce_planks")
    b.walls(fx - 4, 1, fz - 4, fx + 4, 4, fz + 4, WOOD); b.box(fx - 3, 1, fz - 3, fx + 3, 4, fz + 3, AIR)
    b.gable_roof(fx - 4, fz - 4, fx + 4, fz + 4, 5, ROOF_ST, ROOF)
    b.set(fx, 1, fz + 4, AIR); b.set(fx, 2, fz + 4, AIR)
    I.furnish(b, fx - 3, 1, fz - 3, fx + 3, fz + 3, 4, "study", "gloom")
    b.set(fx, 1, fz, "minecraft:enchanting_table"); b.set(fx - 1, 1, fz, "minecraft:brewing_stand")
    for (x, z) in ((CX - 28, CZ + 4), (CX - 30, CZ - 8), (CX - 22, CZ + 12)):
        for dx in range(-2, 3):
            for dy in range(0, 3 - abs(dx)): b.set(x + dx, 1 + dy, z, "minecraft:white_wool")  # tents
        b.set(x, 1, z + 3, CAMPFIRE)
    # ring of straw dolls around the platform
    for a in range(0, 360, 24):
        t = math.radians(a); x, z = round(CX + 19 * math.cos(t)), round(CZ + 19 * math.sin(t))
        if b.get(x, 0, z) != WATER and abs(x - CX) > 3: straw_doll(b, x, 1, z)
    # ---------------- people
    b.npc(CX, 2, HZ0 + 8, "hawkins", True)
    b.chest(CX + 8, 2, HZ0 + 2, "medium", "south"); b.chest(fx + 2, 1, fz - 2, "medium", "west")
    b.guards("pirate", ((CX - 6, CZ + 20), (CX + 6, CZ + 20), (CX - 26, CZ + 8), (CX + 20, CZ - 10)))
    return b, 0
