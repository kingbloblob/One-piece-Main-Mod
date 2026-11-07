"""Killer's hideout in Kuri (Wano): where "Kamazo" hides. A walled samurai estate in a dark bamboo grove: the
gatehouse, a koi pond with a red bridge, stone lanterns, the main house with tatami rooms, a sword room and a
kitchen, the storehouse, the little shrine, and Killer's training yard full of slashed straw posts. ~90 x 90.
Ground = y 0."""
import math, random
from canvas import *
import interiors as I

SID = "kamazo_hideout"
TITLE = "Killer's Hideout (Kuri, Wano)"
CUTS = [5]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 92
CX, CZ = 46, 46
ROOF = "onepiece:wano_roof_tiles"
ROOF_ST = "onepiece:wano_roof_tile_stairs"
PLAST = "minecraft:white_concrete"
POST = "minecraft:dark_oak_log[axis=y]"
SHOJI = "onepiece:shoji_screen"
LAQ = "onepiece:wano_lacquer_planks"


def stone_lantern(b, x, z):
    b.set(x, 1, z, "minecraft:stone_brick_wall"); b.set(x, 2, z, "minecraft:stone_brick_wall")
    b.set(x, 3, z, "onepiece:paper_lantern[hanging=false]" if False else "minecraft:lantern[hanging=false,waterlogged=false]")
    b.set(x, 4, z, "minecraft:stone_brick_slab[type=bottom,waterlogged=false]")


def wano_house(b, x0, z0, x1, z1, h, roof_layers=3, door_side="south"):
    b.box(x0, 0, z0, x1, 0, z1, "minecraft:stone_bricks")
    b.box(x0 + 1, 1, z0 + 1, x1 - 1, 1, z1 - 1, "minecraft:spruce_planks")
    b.walls(x0, 2, z0, x1, h + 1, z1, PLAST)
    b.box(x0 + 1, 2, z0 + 1, x1 - 1, h + 1, z1 - 1, AIR)
    for x in range(x0, x1 + 1, 3):
        for z in (z0, z1): b.column(x, z, 2, h + 1, POST)
    for z in range(z0, z1 + 1, 3):
        for x in (x0, x1): b.column(x, z, 2, h + 1, POST)
    for x in range(x0 + 1, x1):
        for z in (z0, z1):
            if b.get(x, 3, z) == PLAST: b.set(x, 3, z, SHOJI); b.set(x, 4, z, SHOJI)
    for z in range(z0 + 1, z1):
        for x in (x0, x1):
            if b.get(x, 3, z) == PLAST: b.set(x, 3, z, SHOJI); b.set(x, 4, z, SHOJI)
    b.box(x0 + 1, h + 1, z0 + 1, x1 - 1, h + 1, z1 - 1, "minecraft:dark_oak_planks")
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
    b.pagoda_roof(cx, cz, (x1 - x0) // 2 + 2, (z1 - z0) // 2 + 2, h + 2, ROOF_ST, ROOF, layers=roof_layers)
    # engawa veranda all round
    for x in range(x0 - 1, x1 + 2):
        for z in (z0 - 1, z1 + 1): b.set(x, 1, z, "minecraft:spruce_slab[type=top,waterlogged=false]")
    for z in range(z0 - 1, z1 + 2):
        for x in (x0 - 1, x1 + 1): b.set(x, 1, z, "minecraft:spruce_slab[type=top,waterlogged=false]")
    dz = z1 if door_side == "south" else z0
    for x in (cx - 1, cx, cx + 1):
        for y in (2, 3, 4): b.set(x, y, dz, AIR)
    return cx, cz


def build():
    rnd = random.Random(23)
    b = B()
    # ---------------- ground and the bamboo grove
    for x in range(N):
        for z in range(N):
            for y in (-3, -2, -1): b.set(x, y, z, "minecraft:dirt")
            inside = 12 <= x <= N - 13 and 12 <= z <= N - 13
            b.set(x, 0, z, ("minecraft:moss_block" if (x * z) % 5 == 0 else "minecraft:grass_block") if inside else "minecraft:podzol")
            if not inside and rnd.random() < 0.22 and (x < 10 or x > N - 11 or z < 10 or z > N - 11):
                for y in range(1, rnd.randint(8, 16)): b.set(x, y, z, "minecraft:bamboo[age=1,leaves=large,stage=0]" if y > 4 else "minecraft:bamboo[age=1,leaves=none,stage=0]")
    # ---------------- estate wall with roof tiles, the gatehouse (south)
    for x in range(12, N - 12):
        for z in (12, N - 13):
            for y in range(1, 5): b.set(x, y, z, PLAST if y > 1 else "minecraft:stone_bricks")
            b.set(x, 5, z, ROOF)
    for z in range(12, N - 12):
        for x in (12, N - 13):
            for y in range(1, 5): b.set(x, y, z, PLAST if y > 1 else "minecraft:stone_bricks")
            b.set(x, 5, z, ROOF)
    for x in range(CX - 2, CX + 3):
        for y in range(1, 5): b.set(x, y, N - 13, AIR)
    for x in (CX - 4, CX + 4): b.column(x, N - 13, 1, 7, POST)
    b.pagoda_roof(CX, N - 13, 6, 3, 8, ROOF_ST, ROOF, layers=2)
    b.set(CX - 5, 1, N - 11, "onepiece:paper_lantern[hanging=false]"); b.set(CX + 5, 1, N - 11, "onepiece:paper_lantern[hanging=false]")
    # gravel path to the main house
    for z in range(30, N - 12):
        for x in range(CX - 1, CX + 2): b.set(x, 0, z, "minecraft:gravel" if (x + z) % 3 else "minecraft:cobblestone")
    # ---------------- koi pond with a red arched bridge (east garden)
    PX, PZ = CX + 18, CZ + 14
    for x in range(PX - 9, PX + 10):
        for z in range(PZ - 6, PZ + 7):
            d = ((x - PX) / 9) ** 2 + ((z - PZ) / 6) ** 2
            if d < 1:
                b.set(x, 0, z, WATER); b.set(x, -1, z, WATER); b.set(x, -2, z, "minecraft:clay")
                if rnd.random() < 0.05: b.set(x, 1, z, "minecraft:lily_pad")
            elif d < 1.3: b.set(x, 0, z, "minecraft:mossy_cobblestone")
    for i in range(13):
        x = PX - 6 + i
        y = 1 + int(round(1.5 * math.sin(i / 12 * math.pi)))
        for z in (PZ - 1, PZ, PZ + 1): b.set(x, y, z, "minecraft:dark_oak_slab[type=bottom,waterlogged=false]" if False else "onepiece:wano_lacquer_slab[type=bottom,waterlogged=false]")
        for z in (PZ - 2, PZ + 2): b.set(x, y + 1, z, "minecraft:red_concrete" if i % 3 == 0 else "minecraft:crimson_fence")
    for (x, z) in ((PX - 9, PZ - 7), (PX + 9, PZ + 7), (CX - 6, 40), (CX + 6, 40), (CX - 6, 70), (CX + 6, 70)): stone_lantern(b, x, z)
    for i in range(5):  # koi
        b.entities.append(("minecraft:tropical_fish", PX - 5 + i * 2, -1, PZ + (i % 3) - 1, {"PersistenceRequired": Byte(1), "Variant": Int(65536 * (1 + i) + 1)}))
    # sakura trees in the garden
    for (x, z) in ((CX - 24, CZ + 20), (CX + 26, CZ - 20), (CX - 26, CZ - 22), (PX + 12, PZ - 8)):
        for y in range(1, 6): b.set(x, y, z, "onepiece:sakura_log[axis=y]")
        b.sphere(x, 7, z, 4, "onepiece:sakura_leaves[distance=7,persistent=true,waterlogged=false]", ry=2.5)
        for k in range(6): b.set(x + rnd.randint(-4, 4), 1, z + rnd.randint(-4, 4), "onepiece:sakura_petals[facing=north,flower_amount=3]" if False else "minecraft:pink_petals[facing=north,flower_amount=3]")
    # ---------------- the main house (north): tatami rooms, sword room, kitchen
    hx, hz = wano_house(b, CX - 20, 16, CX + 20, 34, 6, 3)
    for x in (CX - 7, CX + 7):  # inner shoji partitions
        for z in range(17, 34):
            for y in range(2, 7): b.set(x, y, z, SHOJI if z % 4 else POST)
        for y in (2, 3, 4): b.set(x, y, 25, AIR)
    for x in range(CX - 19, CX + 20):
        for z in range(17, 34):
            if abs(x - CX) < 7: b.set(x, 1, z, "onepiece:tatami")
    I.furnish(b, CX - 19, 2, 17, CX - 8, 33, 5, "kitchen", "wano")
    I.furnish(b, CX - 6, 2, 17, CX + 6, 33, 5, "shrine", "wano")
    I.furnish(b, CX + 8, 2, 17, CX + 19, 33, 5, "armory", "wano")
    b.chest(CX + 18, 2, 18, "wano", "south")
    # Killer's sleeping room: the storehouse next to the house
    kx0, kz0 = CX - 30, 40
    wano_house(b, kx0, kz0, kx0 + 10, kz0 + 10, 5, 2)
    I.furnish(b, kx0 + 1, 2, kz0 + 1, kx0 + 9, kz0 + 9, 4, "bedroom", "wano")
    # the small shrine (west garden)
    sx, sz = CX - 22, CZ + 22
    b.box(sx - 3, 0, sz - 3, sx + 3, 1, sz + 3, "minecraft:stone_bricks")
    b.walls(sx - 2, 2, sz - 2, sx + 2, 4, sz + 2, LAQ)
    b.box(sx - 1, 2, sz - 1, sx + 1, 4, sz + 1, AIR)
    b.set(sx, 2, sz + 2, AIR); b.set(sx, 3, sz + 2, AIR)
    b.pagoda_roof(sx, sz, 4, 4, 5, ROOF_ST, ROOF, layers=2)
    b.set(sx, 2, sz - 1, "minecraft:bell[attachment=floor,facing=south,powered=false]")
    b.set(sx - 1, 2, sz - 1, I.candle_str("red", 3)); b.set(sx + 1, 2, sz - 1, I.candle_str("red", 3))
    for x in (sx - 2, sx + 2): b.column(x, sz + 6, 1, 6, "minecraft:red_concrete")
    for x in range(sx - 3, sx + 4): b.set(x, 6, sz + 6, "minecraft:red_concrete"); b.set(x, 7, sz + 6, "minecraft:black_concrete")
    # Killer's training yard: slashed straw posts and blades
    for i in range(10):
        x = CX + 10 + (i % 5) * 3; z = 44 + (i // 5) * 4
        b.set(x, 1, z, "onepiece:training_post[facing=south]")
        if i % 2: b.set(x, 2, z, "minecraft:hay_block[axis=y]")
    for x in range(CX + 8, CX + 24, 2): b.set(x, 1, 52, "minecraft:spruce_fence"); b.set(x, 2, 52, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]")
    b.entities.append(("minecraft:armor_stand", CX + 16, 1, 41, {"ShowArms": Byte(1), "Invulnerable": Byte(1),
                       "equipment": {"head": {"id": "minecraft:iron_helmet", "count": Int(1)}, "mainhand": {"id": "minecraft:iron_sword", "count": Int(1)},
                                     "offhand": {"id": "minecraft:iron_sword", "count": Int(1)}}}))
    # ---------------- people
    b.npc(CX, 2, 26, "killer", True)
    b.guards("gifter", ((CX - 4, N - 16), (CX + 4, N - 16), (CX - 14, 38), (CX + 14, 38)))
    return b, 0
