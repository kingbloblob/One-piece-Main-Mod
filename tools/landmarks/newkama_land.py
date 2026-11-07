"""Newkama Land, Impel Down's secret Level 5.5: a hidden paradise of escaped prisoners carved out between Freezing
Hell and Eternal Hell by Emporio Ivankov. A bright, warm cavern decked in pink and purple: the great party hall
with its disco floor, stage and spotlights, the long bar and the kitchen that feeds everyone, a dining hall,
dressing rooms full of costumes, bedrooms and a hot spring bath, Ivankov's throne room where he works his
Hormone powers, a garden of crimson fungus and flowers lit by froglights, and the secret tunnel back up.
Canvas y 0 = the cavern floor, world y 33."""
import math, random
from canvas import *
import interiors as I
import underkit as U

SID = "newkama_land"
TITLE = "Newkama Land (Impel Down Level 5.5)"
CUTS = [3, 8, 14]
TILER = dict(terrain="none", sky_y=33)

N = 92
CX, CZ = 46, 46
RX, RZ, H = 42, 40, 26
ROCK = ("minecraft:pink_terracotta", "minecraft:magenta_terracotta", "minecraft:pink_terracotta", "minecraft:purple_terracotta", "minecraft:crimson_nylium")
NEWK = dict(wood="cherry", rug="pink", rug2="purple", bed="pink", light="minecraft:pearlescent_froglight[axis=y]", accent="minecraft:gold_block",
            banner="pink", candle="pink")
COLS = ("minecraft:pink_concrete", "minecraft:magenta_concrete", "minecraft:purple_concrete", "minecraft:light_blue_concrete", "minecraft:yellow_concrete")


def hall(b, x0, z0, x1, z1, h, wall, roof, door="south"):
    b.box(x0, 0, z0, x1, 0, z1, "minecraft:polished_blackstone")
    b.walls(x0, 1, z0, x1, h, z1, wall); b.box(x0 + 1, 1, z0 + 1, x1 - 1, h, z1 - 1, AIR)
    b.box(x0, h + 1, z0, x1, h + 1, z1, roof)
    for x in range(x0 + 2, x1 - 1, 3):
        for z in (z0, z1): b.set(x, 3, z, "minecraft:pink_stained_glass"); b.set(x, 4, z, "minecraft:pink_stained_glass")
    for x in range(x0, x1 + 1):
        for z in (z0, z1): b.set(x, h, z, "minecraft:gold_block" if x % 2 else wall)


def build():
    rnd = random.Random(921)
    b = B()
    U.cavern(b, CX, CZ, RX, RZ, H, ROCK, rnd, floor="minecraft:crimson_nylium", thick=3, below=3)
    for x in range(N):
        for z in range(N):
            if b.get(x, 0, z) == "minecraft:crimson_nylium" and b.get(x, 1, z) == AIR and rnd.random() < 0.12:
                b.set(x, 1, z, rnd.choice(("minecraft:crimson_roots", "minecraft:crimson_fungus", "minecraft:pink_tulip", "minecraft:allium", "minecraft:pink_petals[facing=north,flower_amount=4]")))
    # ---------------- the great party hall: disco floor, stage, spotlights
    PX0, PZ0, PX1, PZ1 = 26, 10, 66, 40
    hall(b, PX0, PZ0, PX1, PZ1, 12, "minecraft:magenta_terracotta", "minecraft:purple_terracotta")
    for x in range(PX0 + 6, PX1 - 5):
        for z in range(PZ0 + 9, PZ1 - 3):
            b.set(x, 0, z, COLS[(x // 2 + z // 2) % 5] if (x + z) % 2 else "minecraft:shroomlight")
    b.box(PX0 + 8, 1, PZ0 + 1, PX1 - 8, 2, PZ0 + 6, "minecraft:polished_blackstone_bricks")  # the stage
    b.box(PX0 + 8, 3, PZ0 + 1, PX1 - 8, 3, PZ0 + 1, "minecraft:pink_stained_glass")
    for x in (PX0 + 8, PX1 - 8):
        for y in range(3, 12): b.set(x, y, PZ0 + 1, "minecraft:gold_block" if y % 3 == 0 else "minecraft:crimson_stem[axis=y]")
    for x in range(PX0 + 9, PX1 - 8): b.set(x, 11, PZ0 + 2, "minecraft:red_wool"); b.set(x, 10, PZ0 + 2, "minecraft:red_wool" if x % 3 else AIR)
    for i in range(5): b.set(PX0 + 12 + i * 4, 3, PZ0 + 3, "minecraft:jukebox[has_record=false]" if i % 2 else "minecraft:note_block[instrument=harp,note=0,powered=false]")
    for (x, z) in ((PX0 + 10, PZ0 + 16), (PX1 - 10, PZ0 + 16), (CX, PZ0 + 22)):  # spotlights and the mirror ball
        b.set(x, 12, z, "minecraft:end_rod[facing=down]"); b.set(x, 11, z, "minecraft:end_rod[facing=down]")
    b.sphere(CX, 9, PZ0 + 16, 1.5, "minecraft:glass")
    for y in (11, 12): b.set(CX, y, PZ0 + 16, "minecraft:iron_chain[axis=y]")
    for z in range(PZ0 + 9, PZ1 - 1, 4):
        for x in (PX0 + 2, PX1 - 2): b.table_set(x, 1, z, "cherry", cloth="pink")
    for x in range(CX - 2, CX + 3):
        for y in range(1, 5): b.set(x, y, PZ1, AIR)
    # ---------------- the long bar and kitchen, dining hall (west)
    I.subdivide(b, 8, 1, 30, 24, 66, 5, "minecraft:pink_terracotta", ("tavern", "kitchen", "dining"), NEWK, cell=12, seed=1, door="east")
    b.box(8, 0, 30, 24, 0, 66, "minecraft:cherry_planks"); b.box(8, 6, 30, 24, 6, 66, "minecraft:magenta_terracotta")
    b.walls(8, 1, 30, 24, 5, 66, "minecraft:pink_terracotta")
    for z in (40, 52, 62):
        for y in (1, 2): b.set(24, y, z, AIR)
    # ---------------- dressing rooms, bedrooms, the hot spring (east)
    I.subdivide(b, 68, 1, 30, 84, 70, 5, "minecraft:magenta_terracotta", ("bedroom", "workshop", "bedroom", "bath", "bedroom"), NEWK, cell=10, seed=2, door="west")
    b.box(68, 0, 30, 84, 0, 70, "minecraft:cherry_planks"); b.box(68, 6, 30, 84, 6, 70, "minecraft:purple_terracotta")
    b.walls(68, 1, 30, 84, 5, 70, "minecraft:magenta_terracotta")
    for z in (36, 46, 56, 66):
        for y in (1, 2): b.set(68, y, z, AIR)
    HX, HZ = 54, 64
    b.cyl(HX, HZ, 6, 0, 0, "minecraft:smooth_quartz"); b.cyl(HX, HZ, 5, 0, 0, WATER); b.cyl(HX, HZ, 5, -1, -1, "minecraft:magma_block")
    b.cyl(HX, HZ, 6.4, 1, 1, "minecraft:pink_concrete", hollow=True)
    for a in range(0, 360, 60):
        t = math.radians(a); b.set(round(HX + 7 * math.cos(t)), 1, round(HZ + 7 * math.sin(t)), "minecraft:pearlescent_froglight[axis=y]")
    # ---------------- Ivankov's throne room (south)
    TX0, TZ0, TX1, TZ1 = 30, 70, 50, 84
    hall(b, TX0, TZ0, TX1, TZ1, 8, "minecraft:purple_terracotta", "minecraft:magenta_terracotta")
    I.furnish(b, TX0 + 1, 1, TZ0 + 1, TX1 - 1, TZ1 - 1, 7, "throne", NEWK, seed=3)
    b.box(38, 1, TZ1 - 3, 42, 1, TZ1 - 2, "minecraft:gold_block"); b.set(40, 2, TZ1 - 2, "minecraft:purple_wool"); b.set(40, 3, TZ1 - 1, "minecraft:gold_block")
    for x in range(38, 43):
        for y in (1, 2, 3): b.set(x, y, TZ0, AIR)
    # garden lights and the secret tunnel up to Freezing Hell (north-east)
    for i in range(16):
        a = rnd.uniform(0, 6.28); r = rnd.uniform(10, 34)
        x, z = round(CX + r * math.cos(a)), round(CZ + r * math.sin(a))
        if b.get(x, 1, z) in (None, AIR) and b.get(x, 0, z) == "minecraft:crimson_nylium":
            h = rnd.randint(4, 8)
            for y in range(1, h): b.set(x, y, z, "minecraft:crimson_stem[axis=y]")
            b.sphere(x, h, z, 2.2, "minecraft:nether_wart_block", ry=1.4); b.set(x, h - 2, z, "minecraft:shroomlight")
    for k in range(14):
        x, z = 76 + k // 2, 8 + k // 2
        for y in range(1 + k // 2, 4 + k // 2): b.set(x, y, z, AIR)
    for (x, z) in ((CX - 20, CZ), (CX + 20, CZ), (CX, CZ + 14)):
        b.set(x, H - 6 - abs(x - CX) // 4, z, "minecraft:pearlescent_froglight[axis=y]")
    # ---------------- loot and Ivankov
    b.chest(10, 1, 32, "newkama", "east"); b.chest(TX0 + 2, 1, TZ0 + 2, "newkama", "east"); b.chest(82, 1, 68, "newkama", "west")
    b.npc(40, 2, TZ1 - 4, "ivankov", False)
    return b, 0
