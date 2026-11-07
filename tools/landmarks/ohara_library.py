"""Ohara, the island of archaeologists, before the Buster Call: the Tree of Knowledge, a giant hollow tree 5,000
years old turned into the world's greatest library. Bookshelves line the hollow trunk from the floor up six
galleries joined by spiral stairs, reading tables and globes on every level, a domed reading room in the crown
and a scholars' study. Round it the scholars' village of white houses with blue roofs, the harbour and the
cliff where young Robin read. ~100 x 100. Ground = y 0, the sea to the east."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "ohara_library"
TITLE = "Ohara Tree of Knowledge"
CUTS = [2, 12, 28]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 100
CX, CZ = 44, 48
R = 14
OAK = "minecraft:oak_wood[axis=y]"
SCHOLAR = dict(wood="oak", rug="green", rug2="brown", bed="green", light="minecraft:lantern", accent="minecraft:chiseled_bookshelf[facing=north,slot_0_occupied=true,slot_1_occupied=true,slot_2_occupied=true,slot_3_occupied=true,slot_4_occupied=true,slot_5_occupied=true]",
               banner="green", candle="white")
GALLERY = 7


def build():
    rnd = random.Random(651)
    b = B()
    T.ground(b, N, N, rnd, deco=0.12)
    T.sea(b, N, N, lambda x, z: x > 84 + 3 * math.sin(z * 0.12), depth=6)
    for z in range(N):
        sx = int(84 + 3 * math.sin(z * 0.12))
        for x in range(sx - 3, sx + 1): b.set(x, 0, z, "minecraft:sand"); b.set(x, 1, z, AIR) if b.get(x, 1, z) else None
    # ---------------- the Tree of Knowledge
    TOP = 48
    for y in range(-2, TOP):
        r = R + max(0, 4 - y) * 1.2 - y * 0.03
        b.cyl(CX, CZ, r, y, y, OAK)
    for k in range(7):  # buttress roots
        a = k * 2 * math.pi / 7
        for t in range(0, 14):
            b.cyl(CX + (R + t) * math.cos(a), CZ + (R + t) * math.sin(a), max(1, 3.5 - t * 0.2), 0, max(0, int(5 - t * 0.4)), OAK)
    b.cyl(CX, CZ, R - 2, 1, TOP - 4, AIR)
    b.cyl(CX, CZ, R - 1, 0, 0, "minecraft:polished_andesite"); b.cyl(CX, CZ, 5, 0, 0, "minecraft:mossy_stone_bricks")
    # bookshelves all round the inner wall, six galleries
    for y in range(1, TOP - 4):
        for a in range(0, 360, 3):
            t = math.radians(a)
            x, z = round(CX + (R - 2) * math.cos(t)), round(CZ + (R - 2) * math.sin(t))
            if y % GALLERY in (0,): continue
            b.set(x, y, z, "minecraft:bookshelf" if (a // 3 + y) % 11 else "minecraft:chiseled_bookshelf[facing=north,slot_0_occupied=true,slot_1_occupied=true,slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=true,slot_5_occupied=false]")
    for g in range(1, 6):
        gy = g * GALLERY
        b.cyl(CX, CZ, R - 2, gy, gy, "minecraft:spruce_planks"); b.cyl(CX, CZ, R - 6, gy, gy, AIR)
        b.cyl(CX, CZ, R - 6.5, gy + 1, gy + 1, "minecraft:spruce_fence", hollow=True)
        for a in range(0, 360, 40):  # reading lamps and desks on the gallery
            t = math.radians(a + g * 13)
            x, z = round(CX + (R - 4) * math.cos(t)), round(CZ + (R - 4) * math.sin(t))
            b.set(x, gy + 1, z, "minecraft:lectern[facing=north,has_book=true,powered=false]" if a % 80 else "minecraft:spruce_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
        for a in range(0, 360, 60):
            t = math.radians(a + g * 7)
            b.set(round(CX + (R - 6) * math.cos(t)), gy - 1, round(CZ + (R - 6) * math.sin(t)), lantern(True))
    for y in range(1, 5 * GALLERY + 1):  # spiral stair round a central column
        a = y / 3.0
        for w in (2, 3, 4):
            b.set(round(CX + w * math.cos(a)), y, round(CZ + w * math.sin(a)), "minecraft:spruce_slab[type=top,waterlogged=false]" if w == 4 else "minecraft:spruce_planks")
    b.cyl(CX, CZ, 1, 1, 5 * GALLERY + 2, "minecraft:stripped_oak_log[axis=y]")
    for g in range(1, 6):  # bridges from the stair to each gallery
        gy = g * GALLERY
        a = gy / 3.0
        for w in range(4, R - 5):
            b.set(round(CX + w * math.cos(a)), gy, round(CZ + w * math.sin(a)), "minecraft:spruce_planks")
    # ground floor: reading tables, globe, the front door
    for (dx, dz) in ((-7, -2), (-7, 3), (7, -2), (7, 3), (-2, -8), (3, -8), (-2, 8), (3, 8)):
        b.table_set(CX + dx, 1, CZ + dz, "oak", cloth="green")
    b.set(CX + 6, 1, CZ - 6, "minecraft:spruce_fence"); b.set(CX + 6, 2, CZ - 6, "minecraft:light_blue_glazed_terracotta")
    for x in range(CX - R - 5, CX - R + 4):
        for y in range(1, 6):
            for dz in (-1, 0, 1): b.set(x, y, CZ + dz, AIR)
    b.arch_x(CX - R - 2, CX - R - 2, CZ, 6, 2, "minecraft:stripped_oak_log[axis=y]") if False else None
    # the domed reading room in the crown and the scholars' study
    b.cyl(CX, CZ, R - 2, TOP - 4, TOP - 4, "minecraft:spruce_planks")
    b.dome(CX, CZ, TOP - 3, R - 1, h=10, s="minecraft:glass", tip="minecraft:gold_block")
    I.furnish(b, CX - 7, TOP - 3, CZ - 7, CX + 7, CZ + 7, 6, "library", SCHOLAR, seed=1)
    for (cx, cy, cz, r) in ((CX, TOP + 14, CZ, 26), (CX - 18, TOP + 6, CZ + 10, 14), (CX + 16, TOP + 8, CZ - 12, 15), (CX + 4, TOP + 4, CZ + 22, 12)):
        b.sphere(cx, cy, cz, r, "minecraft:oak_leaves[distance=7,persistent=true,waterlogged=false]", ry=r * 0.42)
    b.dome(CX, CZ, TOP - 3, R - 1, h=10, s=AIR, tip=AIR) if False else None
    b.shape(lambda x, y, z: ((x - CX) / (R - 2)) ** 2 + ((y - TOP + 3) / 9) ** 2 + ((z - CZ) / (R - 2)) ** 2 < 1, CX - R, TOP - 3, CZ - R, CX + R, TOP + 8, CZ + R, AIR, interior=None)
    b.dome(CX, CZ, TOP - 3, R - 1, h=10, s="minecraft:glass", tip="minecraft:gold_block")
    b.shape(lambda x, y, z: ((x - CX) / (R - 2.2)) ** 2 + ((y - TOP + 3) / 8.8) ** 2 + ((z - CZ) / (R - 2.2)) ** 2 < 1, CX - R, TOP - 3, CZ - R, CX + R, TOP + 8, CZ + R, AIR, interior=None)
    I.furnish(b, CX - 7, TOP - 3, CZ - 7, CX + 7, CZ + 7, 6, "library", SCHOLAR, seed=1)
    for y in range(5 * GALLERY, TOP - 3): b.set(CX + 1, y, CZ, "minecraft:ladder[facing=east,waterlogged=false]")
    b.set(CX + 1, TOP - 4, CZ, AIR); b.set(CX + 2, TOP - 4, CZ, AIR) if False else None
    # ---------------- the scholars' village and the harbour
    hs = [(8, 8), (22, 6), (68, 10), (70, 26), (66, 72), (72, 86), (14, 80), (28, 88), (8, 64)]
    for i, (x, z) in enumerate(hs):
        T.house(b, x, z, 10, 8, floors=1 + (i % 2), style="plaster", rnd=random.Random(i), kinds=("study", "library") if i % 2 else ("library",),
                door="south" if z < CZ else "north")
    for (x, z) in ((40, 12), (56, 84), (76, 50)): T.lamp_post(b, x, z)
    T.path(b, [(CX - R - 5, CZ), (6, CZ), (6, 20)], w=2, s="minecraft:gravel")
    T.path(b, [(CX + R + 2, CZ), (80, CZ)], w=2, s="minecraft:dirt_path")
    T.pier(b, 81, CZ - 1, 14, axis="x")
    # Robin's reading cliff on the shore
    b.box(74, 1, 4, 82, 4, 10, "minecraft:stone"); b.box(75, 5, 5, 81, 6, 9, "minecraft:grass_block")
    b.set(78, 7, 7, "minecraft:oak_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
    # ---------------- loot and the quest giver
    b.chest(CX + 6, 1, CZ + 5, "library", "west"); b.chest(CX - 4, TOP - 3, CZ + 4, "library", "east"); b.chest(CX + 9, 4 * GALLERY + 1, CZ, "medium", "west")
    b.npc(CX - 5, 1, CZ, "robin", False)
    T.landscape(b, 0, 0, N - 1, N - 1, rnd, amp=4, cell=16, edge=8)  # the open ground rolls (guide 9b.1, 11a); last, so it knows where everything stands
    return b, 0
