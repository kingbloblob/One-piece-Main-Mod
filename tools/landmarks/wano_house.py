"""The Kozuki samurai manor of Wano: Oden's family estate in Kuri. A white plastered wall with a tiled gatehouse
encloses a great two-storey main house with sweeping tiled roofs and verandas, its tatami rooms (the audience
hall, the sword room, Oden's study, the family bedrooms, the kitchen), a dojo with training posts, the
storehouse, a little Shinto shrine with a red torii, the bell tower, and a garden of sakura, stone lanterns and
a koi pond crossed by a red bridge. ~84 x 84. Ground = y 0."""
import math, random
from canvas import *
import interiors as I
import townkit as T
import kamazo_hideout as KH
import onigashima as OG

SID = "wano_house"
TITLE = "Wano Samurai House"
CUTS = [3, 9]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 84
CX, CZ = 42, 38
PLAST = "minecraft:white_concrete"
ROOF = "onepiece:wano_roof_tiles"
ROOF_ST = "onepiece:wano_roof_tile_stairs"


def sakura(b, x, z, rnd, h=6):
    for y in range(1, h): b.set(x, y, z, "onepiece:sakura_log[axis=y]")
    b.sphere(x, h + 1, z, rnd.uniform(3, 4.2), "onepiece:sakura_leaves[distance=7,persistent=true,waterlogged=false]", ry=2.4)
    for i in range(6):
        px, pz = x + rnd.randint(-4, 4), z + rnd.randint(-4, 4)
        if b.get(px, 1, pz) is None: b.set(px, 1, pz, "minecraft:pink_petals[facing=north,flower_amount=3]")


def build():
    rnd = random.Random(561)
    b = B()
    T.ground(b, N, N, rnd, deco=0.06)
    # ---------------- the compound wall and gatehouse
    W0, W1 = 4, N - 5
    for x in range(W0, W1 + 1):
        for z in (W0, W1):
            for y in range(1, 5): b.set(x, y, z, PLAST if y > 1 else "minecraft:stone_bricks")
            b.set(x, 5, z, ROOF)
    for z in range(W0, W1 + 1):
        for x in (W0, W1):
            for y in range(1, 5): b.set(x, y, z, PLAST if y > 1 else "minecraft:stone_bricks")
            b.set(x, 5, z, ROOF)
    for x in range(CX - 3, CX + 4):
        for y in range(1, 5): b.set(x, y, W1, AIR)
    for (px, pz) in ((CX - 4, W1), (CX + 4, W1), (CX - 4, W1 + 3), (CX + 4, W1 + 3)): b.column(px, pz, 1, 7, "minecraft:dark_oak_log[axis=y]")
    b.box(CX - 4, 8, W1, CX + 4, 8, W1 + 3, "onepiece:wano_lacquer_planks")
    b.pagoda_roof(CX, W1 + 1, 7, 4, 9, ROOF_ST, ROOF, layers=2)
    b.set(CX - 3, 6, W1 + 3, "onepiece:paper_lantern[hanging=true]"); b.set(CX + 3, 6, W1 + 3, "onepiece:paper_lantern[hanging=true]")
    # ---------------- the main house: two storeys, grand roofs
    HX0, HX1, HZ0, HZ1 = CX - 20, CX + 20, 12, 40
    cx, cz = KH.wano_house(b, HX0, HZ0, HX1, HZ1, 6, roof_layers=1)
    # second storey set back
    b.box(HX0 + 1, 7, HZ0 + 1, HX1 - 1, 7, HZ1 - 1, "minecraft:dark_oak_planks")
    for x in range(HX0 - 3, HX1 + 4):
        for z in range(HZ0 - 3, HZ1 + 4):
            for y in range(8, 14):
                s = b.get(x, y, z)
                if s and ("roof" in s or "tile" in s): b.set(x, y, z, AIR)
    b.pagoda_roof(cx, cz, (HX1 - HX0) // 2 + 2, (HZ1 - HZ0) // 2 + 2, 8, ROOF_ST, ROOF, layers=1)
    U0, U1, V0, V1 = HX0 + 6, HX1 - 6, HZ0 + 5, HZ1 - 5
    b.walls(U0, 9, V0, U1, 13, V1, PLAST); b.box(U0 + 1, 9, V0 + 1, U1 - 1, 13, V1 - 1, AIR)
    for x in range(U0, U1 + 1, 3):
        for z in (V0, V1): b.column(x, z, 9, 13, "minecraft:dark_oak_log[axis=y]")
    for x in range(U0 + 1, U1):
        for z in (V0, V1):
            if b.get(x, 10, z) == PLAST: b.set(x, 10, z, "onepiece:shoji_screen"); b.set(x, 11, z, "onepiece:shoji_screen")
    b.box(U0, 9, V0, U1, 9, V1, "minecraft:dark_oak_planks") if False else None
    b.box(U0 + 1, 8, V0 + 1, U1 - 1, 8, V1 - 1, "minecraft:dark_oak_planks")
    b.pagoda_roof(cx, cz, (U1 - U0) // 2 + 3, (V1 - V0) // 2 + 3, 14, ROOF_ST, ROOF, layers=3)
    b.set(cx - 2, 18, cz, "minecraft:gold_block"); b.set(cx + 2, 18, cz, "minecraft:gold_block")
    # ground floor rooms (y 2): audience hall in the middle, wings either side
    for z in range(HZ0 + 1, HZ1):
        for y in range(2, 7):
            b.set(cx - 8, y, z, "onepiece:shoji_screen" if y < 5 else PLAST); b.set(cx + 8, y, z, "onepiece:shoji_screen" if y < 5 else PLAST)
    for y in (2, 3, 4):
        b.set(cx - 8, y, cz, AIR); b.set(cx + 8, y, cz, AIR)
    r = I.furnish(b, cx - 7, 2, HZ0 + 1, cx + 7, HZ1 - 1, 5, "throne", "wano", seed=1)
    I.subdivide(b, HX0 + 1, 2, HZ0 + 1, cx - 9, HZ1 - 1, 5, "onepiece:shoji_screen", ("armory", "kitchen"), "wano", cell=13, corridor=2, seed=2)
    I.subdivide(b, cx + 9, 2, HZ0 + 1, HX1 - 1, HZ1 - 1, 5, "onepiece:shoji_screen", ("study", "dining"), "wano", cell=13, corridor=2, seed=3)
    I.subdivide(b, U0 + 1, 9, V0 + 1, U1 - 1, V1 - 1, 5, "onepiece:shoji_screen", ("bedroom", "library", "bedroom"), "wano", cell=9, corridor=2,
                keepout=((U0 + 1, V0 + 1, U0 + 2, V0 + 2),), seed=4)
    for y in range(2, 10): b.set(U0 + 1, y, V0 + 1, "minecraft:ladder[facing=south,waterlogged=false]")
    b.set(U0 + 1, 7, V0 + 1, "minecraft:ladder[facing=south,waterlogged=false]"); b.set(U0 + 1, 8, V0 + 1, "minecraft:ladder[facing=south,waterlogged=false]")
    # ---------------- the dojo, storehouse, shrine and bell tower
    dcx, dcz = KH.wano_house(b, 8, 46, 26, 60, 4, roof_layers=2, door_side="north")
    I.furnish(b, 9, 2, 47, 25, 59, 4, "barracks", "wano", seed=5)
    for x in range(10, 25, 3): b.set(x, 2, 53, "onepiece:training_post[facing=north]")
    scx, scz = KH.wano_house(b, 60, 48, 72, 58, 4, roof_layers=1, door_side="north")
    I.furnish(b, 61, 2, 49, 71, 57, 4, "storage", "wano", seed=6)
    # shrine with a torii (north-east corner)
    b.box(64, 1, 8, 74, 1, 16, "minecraft:stone_bricks")
    b.walls(66, 2, 9, 72, 5, 14, "minecraft:red_concrete"); b.box(67, 2, 10, 71, 5, 13, AIR)
    b.pagoda_roof(69, 11, 5, 4, 6, ROOF_ST, ROOF, layers=2)
    for y in (2, 3, 4): b.set(69, y, 14, AIR)
    I.furnish(b, 67, 2, 10, 71, 13, 4, "shrine", "wano", seed=7)
    OG.torii(b, 69, 20, w=3, h=7)
    # bell tower
    bx, bz = 10, 14
    for (dx, dz) in ((-2, -2), (2, -2), (-2, 2), (2, 2)): b.column(bx + dx, bz + dz, 1, 9, "minecraft:dark_oak_log[axis=y]")
    b.box(bx - 2, 10, bz - 2, bx + 2, 10, bz + 2, "onepiece:wano_lacquer_planks")
    b.pagoda_roof(bx, bz, 4, 4, 11, ROOF_ST, ROOF, layers=2)
    b.set(bx, 9, bz, "minecraft:bell[attachment=ceiling,facing=north,powered=false]")
    # ---------------- the garden: koi pond, red bridge, stone lanterns, sakura
    PX, PZ = 46, 62
    for x in range(PX - 12, PX + 13):
        for z in range(PZ - 7, PZ + 8):
            if ((x - PX) / 12) ** 2 + ((z - PZ) / 7) ** 2 < 1:
                b.set(x, 0, z, WATER); b.set(x, -1, z, WATER if ((x - PX) / 12) ** 2 + ((z - PZ) / 7) ** 2 < 0.5 else "minecraft:gravel")
                b.set(x, -2, z, "minecraft:gravel" if False else "minecraft:clay")
                b.set(x, 1, z, AIR)
            elif ((x - PX) / 13) ** 2 + ((z - PZ) / 8) ** 2 < 1:
                b.set(x, 0, z, "minecraft:mossy_cobblestone" if (x + z) % 2 else "minecraft:cobblestone"); b.set(x, 1, z, AIR)
    for i in range(6): b.set(PX + rnd.randint(-8, 8), -1, PZ + rnd.randint(-3, 3), "minecraft:sea_pickle[pickles=2,waterlogged=true]")
    for i in range(8): b.set(PX + rnd.randint(-9, 9), 1, PZ + rnd.randint(-4, 4), "minecraft:lily_pad") if b.get(PX, 0, PZ) == WATER else None
    for z in range(PZ - 8, PZ + 9):
        dy = 2 if abs(z - PZ) < 3 else (1 if abs(z - PZ) < 6 else 0)
        for x in (PX - 1, PX, PX + 1): b.set(x, dy + 1, z, "minecraft:red_concrete" if dy else "minecraft:spruce_planks")
        b.set(PX - 2, dy + 2, z, "minecraft:red_concrete" if z % 2 else "minecraft:dark_oak_fence")
        b.set(PX + 2, dy + 2, z, "minecraft:red_concrete" if z % 2 else "minecraft:dark_oak_fence")
    for (x, z) in ((PX - 16, PZ - 4), (PX + 16, PZ + 4), (CX - 6, 72), (CX + 6, 72), (CX - 6, 44), (CX + 6, 44)): KH.stone_lantern(b, x, z)
    for (x, z) in ((12, 70), (24, 74), (64, 70), (74, 64), (34, 52), (58, 44), (74, 30), (10, 32)): sakura(b, x, z, rnd)
    T.path(b, [(CX, W1 - 1), (CX, 72), (PX, PZ + 9)], w=1, s="minecraft:gravel")
    T.path(b, [(PX, PZ - 9), (CX, HZ1 + 2)], w=1, s="minecraft:gravel")
    # ---------------- people and loot
    b.npc(cx, 2, HZ0 + 4, "oden", False); b.npc(dcx, 2, dcz, "yamato", False)
    b.chest(HX1 - 3, 2, HZ0 + 3, "wano", "west"); b.chest(70, 2, 12, "easy", "west")
    b.guards("samurai", ((CX - 3, W1 + 4), (CX + 3, W1 + 4)))
    return b, 0
