"""Amazon Lily, the island of women in the Calm Belt: the Kuja capital ringed by sheer jungle cliffs. The Kuja
Palace with purple and gold onion domes and giant coiled snake statues at its gate, Hancock's throne room, bath
and bedchamber; the Kuja Battle Arena where the snakes were turned to stone; the market street of round
huts with conical roofs, the warriors' longhouse and archery range; and the Perfume Yuda, the snake-headed ship
pulled by two giant serpents, moored in the cove. ~112 x 112. Ground = y 0, the cove to the south."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "amazon_lily"
TITLE = "Amazon Lily Kuja Palace"
CUTS = [2, 10]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 112
CX, CZ = 56, 50
PURP = "minecraft:purple_terracotta"
GOLD = "minecraft:gold_block"
SNAKE = "minecraft:green_terracotta"
KUJA = dict(wood="jungle", rug="purple", rug2="pink", bed="purple", light="minecraft:lantern", accent="minecraft:gold_block",
            banner="purple", candle="purple")


def snake_statue(b, x, z, h, facing=1):
    """A great stone snake coiled upward, head reared and facing +z (facing=1) or -z."""
    for y in range(1, h):
        a = y / 3.0
        sx, sz = x + 2.5 * math.cos(a), z + 2.5 * math.sin(a)
        b.cyl(sx, sz, 1.4, y, y, SNAKE if y % 3 else "minecraft:lime_terracotta")
    hx, hz = round(x + 2.5 * math.cos((h - 1) / 3.0)), round(z + 2.5 * math.sin((h - 1) / 3.0))
    b.box(hx - 1, h, hz - 1, hx + 1, h + 2, hz + 1 + facing * 2, SNAKE)
    b.set(hx - 1, h + 2, hz + 1 + facing * 2, "minecraft:gold_block"); b.set(hx + 1, h + 2, hz + 1 + facing * 2, "minecraft:gold_block")
    b.set(hx, h, hz + 2 + facing * 2, "minecraft:red_wool")


def hut(b, x, z, r, rnd, kind, door="south"):
    b.cyl(x, z, r, 0, 0, "minecraft:jungle_planks")
    b.cyl(x, z, r, 1, 4, "minecraft:mud_bricks" if rnd.random() < 0.5 else "minecraft:packed_mud", hollow=True)
    b.cyl(x, z, r - 1, 1, 4, AIR)
    for k in range(int(r) + 3):
        b.cyl(x, z, max(0.5, r + 1 - k), 5 + k, 5 + k, "minecraft:purple_wool" if k % 2 else "minecraft:hay_block[axis=y]")
    dz = r if door == "south" else -r
    for y in (1, 2): b.set(x, y, z + dz, AIR)
    for a in (60, 120, 240, 300):
        t = math.radians(a)
        b.set(round(x + r * math.cos(t)), 2, round(z + r * math.sin(t)), "minecraft:jungle_trapdoor[facing=north,half=top,open=true,powered=false,waterlogged=false]")
    q = max(2, int((r - 1) / 1.42))
    I.furnish(b, x - q, 1, z - q, x + q, z + q, 4, kind, KUJA, seed=x * 13 + z)


def build():
    rnd = random.Random(501)
    b = B()
    T.ground(b, N, N, rnd, deco=0.12, decos=("minecraft:short_grass", "onepiece:amazon_flower", "minecraft:fern", "minecraft:short_grass"))
    T.sea(b, N, N, lambda x, z: ((x - CX) / 26) ** 2 + ((z - N - 4) / 22) ** 2 < 1, depth=7)
    # ---------------- the ring of cliffs round the city, open to the cove
    for x in range(N):
        for z in range(N):
            d = math.hypot((x - CX) / 52, (z - CZ) / 50)
            if d > 0.84 and not (z > 80 and abs(x - CX) < 30):
                h = int(34 * math.exp(-((d - 0.98) / 0.09) ** 2) + 3 * math.sin(x * 0.4) * math.cos(z * 0.3)) + rnd.randint(0, 2)
                if h < 2: continue
                for y in range(1, h + 1): b.set(x, y, z, "minecraft:stone" if y < h - 1 else "minecraft:grass_block")
                if rnd.random() < 0.08 and h > 2: b.set(x, h + 1, z, "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]")
    # ---------------- the Kuja Palace (north of the city)
    PX0, PX1, PZ0, PZ1 = CX - 22, CX + 22, 14, 42
    H = 14
    b.box(PX0 - 2, 0, PZ0 - 2, PX1 + 2, 1, PZ1 + 2, "minecraft:smooth_quartz")
    b.walls(PX0, 2, PZ0, PX1, H, PZ1, PURP)
    b.box(PX0 + 1, 2, PZ0 + 1, PX1 - 1, H, PZ1 - 1, AIR)
    for x in range(PX0, PX1 + 1, 4):
        for z in (PZ0, PZ1): b.column(x, z, 2, H, "minecraft:quartz_pillar[axis=y]")
        b.set(x, H + 1, PZ1, GOLD); b.set(x, H + 1, PZ0, GOLD)
    for x in range(PX0 + 2, PX1 - 1, 4):
        for z in (PZ0, PZ1):
            for y in range(5, 10): b.set(x, y, z, "minecraft:purple_stained_glass_pane")
    b.box(PX0, H + 1, PZ0, PX1, H + 1, PZ1, "minecraft:smooth_quartz")
    b.dome(CX, (PZ0 + PZ1) // 2, H + 2, 11, s="minecraft:purple_concrete", onion=True, tip=GOLD)
    for (dx, dz) in ((-18, -10), (18, -10), (-18, 10), (18, 10)):
        tx, tz = CX + dx, (PZ0 + PZ1) // 2 + dz
        b.cyl(tx, tz, 3, 2, H + 8, "minecraft:smooth_quartz", hollow=True)
        b.dome(tx, tz, H + 9, 4, s="minecraft:gold_block", onion=True, tip="minecraft:purple_concrete")
    for x in range(CX - 3, CX + 4):  # grand entrance
        for y in range(2, 9): b.set(x, y, PZ1, AIR)
    for k in range(8): b.box(CX - 4, 1, PZ1 + 1 + k, CX + 4, 1, PZ1 + 1 + k, "minecraft:quartz_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]" if k == 7 else "minecraft:smooth_quartz")
    snake_statue(b, CX - 9, PZ1 + 6, 16); snake_statue(b, CX + 9, PZ1 + 6, 16)
    # inside: throne hall in the middle, bath, bedchamber, the sisters' rooms, kitchen
    for z in range(PZ0 + 1, PZ1):
        for y in range(2, 9): b.set(CX - 9, y, z, PURP); b.set(CX + 9, y, z, PURP)
    for y in (2, 3, 4):
        b.set(CX - 9, y, PZ1 - 4, AIR); b.set(CX + 9, y, PZ1 - 4, AIR)
    b.box(PX0 + 1, 8, PZ0 + 1, CX - 10, 8, PZ1 - 1, "minecraft:jungle_planks"); b.box(CX + 10, 8, PZ0 + 1, PX1 - 1, 8, PZ1 - 1, "minecraft:jungle_planks")
    r = I.furnish(b, CX - 8, 2, PZ0 + 1, CX + 8, PZ1 - 1, 11, "throne", KUJA, seed=1)
    for z in range(PZ0 + 4, PZ1 - 1, 4):
        for x in (CX - 7, CX + 7): b.column(x, z, 2, 12, "minecraft:quartz_pillar[axis=y]"); b.set(x, 13, z, GOLD)
    I.furnish(b, PX0 + 1, 2, PZ0 + 1, CX - 10, (PZ0 + PZ1) // 2, 5, "bath", KUJA, seed=2)
    I.furnish(b, PX0 + 1, 2, (PZ0 + PZ1) // 2 + 1, CX - 10, PZ1 - 1, 5, "kitchen", KUJA, seed=3)
    I.furnish(b, CX + 10, 2, PZ0 + 1, PX1 - 1, (PZ0 + PZ1) // 2, 5, "treasure", KUJA, seed=4)
    I.furnish(b, CX + 10, 2, (PZ0 + PZ1) // 2 + 1, PX1 - 1, PZ1 - 1, 5, "dining", KUJA, seed=5)
    I.subdivide(b, PX0 + 1, 9, PZ0 + 1, CX - 10, PZ1 - 1, 5, PURP, ("bedroom", "bedroom", "library"), KUJA, cell=10, corridor=2, seed=6,
                keepout=((PX0 + 1, PZ1 - 3, PX0 + 3, PZ1 - 1),))
    I.subdivide(b, CX + 10, 9, PZ0 + 1, PX1 - 1, PZ1 - 1, 5, PURP, ("bedroom", "study", "armory"), KUJA, cell=10, corridor=2, seed=7,
                keepout=((PX1 - 3, PZ1 - 3, PX1 - 1, PZ1 - 1),))
    for y in range(2, 9): b.set(PX0 + 2, y, PZ1 - 2, "minecraft:ladder[facing=north,waterlogged=false]"); b.set(PX1 - 2, y, PZ1 - 2, "minecraft:ladder[facing=north,waterlogged=false]")
    # ---------------- the Kuja Battle Arena (east)
    AX, AZ = 80, 62
    b.cyl(AX, AZ, 14, 0, 0, "minecraft:sandstone")
    for ring in range(5):
        b.cyl(AX, AZ, 14 - ring * 0.0 + ring, 1 + ring, 1 + ring, "minecraft:smooth_sandstone", hollow=True) if False else None
    for y in range(1, 7):
        b.cyl(AX, AZ, 9 + y, y, y, "minecraft:smooth_sandstone", hollow=True)
        b.cyl(AX, AZ, 9 + y - 0.5, y, y, "minecraft:cut_sandstone_slab[type=bottom,waterlogged=false]", hollow=True) if y % 2 else None
    b.cyl(AX, AZ, 9, 0, 0, "minecraft:sand")
    for (dx, dz) in ((-5, 0), (5, 0)): b.sphere(AX + dx, 2, AZ + dz, 1.8, "minecraft:stone")  # the petrified snakes
    snake_statue(b, AX, AZ - 16, 10, facing=1)
    # ---------------- the town: round huts and the market street
    kinds = ("kitchen", "bedroom", "dining", "storage", "bedroom", "workshop", "kitchen", "bedroom", "tavern", "armory")
    k = 0
    for (x, z) in ((22, 56), (34, 60), (46, 62), (46, 84), (24, 70), (36, 74), (70, 84), (20, 84), (82, 90), (32, 88)):
        hut(b, x, z, rnd.choice((4, 5)), rnd, kinds[k % len(kinds)], door="south" if z < 70 else "north"); k += 1
    for i, x in enumerate(range(40, 74, 6)):
        T.stall(b, x, 70, ("purple", "pink", "magenta", "yellow", "lime", "orange")[i], (("minecraft:melon", "onepiece:amazon_flower", None), ("minecraft:hay_block[axis=y]", "minecraft:pumpkin", None))[i % 2])
    T.path(b, [(CX, PZ1 + 9), (CX, 92)], w=2, s="minecraft:smooth_sandstone")
    # the warriors' longhouse and the archery range
    T.house(b, 8, 30, 14, 9, 1, "plaster", rnd, kinds=["barracks"], theme=KUJA, door="east")
    for z in range(20, 46, 5): b.set(28, 1, z, "minecraft:target[power=0]"); b.set(28, 2, z, "minecraft:hay_block[axis=y]")
    # ---------------- the Perfume Yuda in the cove, with its two serpents
    b.ship(CX - 14, -3, 100, 28, 10, masts=((14, 16),), sail="minecraft:purple_wool", cabin=(6, 4, "minecraft:jungle_planks"))
    for dz in (-4, 4):  # serpents pulling it
        for i in range(24):
            sx = CX + 14 + i; sz = 100 + dz + 2 * math.sin(i * 0.5)
            b.cyl(sx, sz, 1.6, -2, -1 + (i > 20) * 3, "minecraft:lime_terracotta" if i % 2 else SNAKE)
    for (x, z) in ((CX - 14, 99), (CX - 13, 101)): b.set(x, 3, z, "minecraft:purple_concrete")
    # ---------------- Hancock, warriors and loot
    b.npc(CX, 3, PZ0 + 5, "hancock", False)
    b.chest(CX + 18, 2, PZ0 + 3, "treasure", "west"); b.chest(AX, 1, AZ + 7, "medium", "north")
    b.guards("kuja_warrior", ((CX - 4, PZ1 + 10), (CX + 4, PZ1 + 10), (AX - 4, AZ), (30, 66), (CX, PZ0 + 12), (60, 92)))
    return b, 0
