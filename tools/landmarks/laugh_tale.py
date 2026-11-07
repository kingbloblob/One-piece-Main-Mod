"""Laugh Tale, the final island at the end of the Grand Line. A cove where the Oro Jackson once anchored, a
jungle swallowing the ruins of a vast ancient city, the great Sun Gate of Joy Boy, a labyrinth of ancient walls
guarded by the Ancient Guardians, and at the heart the stepped temple of the Void Century: inside it the
chamber of the final Poneglyph, the hall of murals, and the treasure vault where Gol D. Roger waits beside the
One Piece. ~112 x 112. Ground = y 0, the cove to the south."""
import math, random
from canvas import *
import interiors as I
import townkit as T

SID = "laugh_tale"
TITLE = "Laugh Tale (the final island)"
CUTS = [3, 12, 22]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 112
CX, CZ = 56, 46
ANC = "minecraft:mossy_stone_bricks"
ANC2 = "minecraft:cracked_stone_bricks"
CHIS = "minecraft:chiseled_stone_bricks"
GOLD = "minecraft:gold_block"
VOID = dict(wood="dark_oak", rug="yellow", rug2="black", bed="yellow", light="minecraft:lantern", accent="minecraft:gold_block",
            banner="yellow", candle="yellow")


def ruin(b, x0, z0, w, d, h, rnd):
    for x in range(x0, x0 + w):
        for z in (z0, z0 + d - 1):
            for y in range(1, rnd.randint(1, h) + 1): b.set(x, y, z, rnd.choice((ANC, ANC2, "minecraft:stone_bricks")))
    for z in range(z0, z0 + d):
        for x in (x0, x0 + w - 1):
            for y in range(1, rnd.randint(1, h) + 1): b.set(x, y, z, rnd.choice((ANC, ANC2, "minecraft:stone_bricks")))
    for i in range(3):
        b.fill_if(rnd.randint(x0, x0 + w - 1), 1, rnd.randint(z0, z0 + d - 1), "minecraft:mossy_cobblestone")


def build():
    rnd = random.Random(621)
    b = B()
    T.ground(b, N, N, rnd, deco=0.25, decos=("minecraft:fern", "minecraft:short_grass", "minecraft:moss_carpet", "minecraft:short_grass"))
    T.sea(b, N, N, lambda x, z: ((x - CX) / 30) ** 2 + ((z - N - 6) / 22) ** 2 < 1, depth=7)
    for x in range(N):
        for z in range(N):
            d = ((x - CX) / 30) ** 2 + ((z - N - 6) / 22) ** 2
            if 1 <= d < 1.35: b.set(x, 0, z, "minecraft:sand"); b.set(x, 1, z, AIR) if b.get(x, 1, z) else None
    # the jungle round the edge
    for i in range(70):
        x, z = rnd.randint(2, N - 3), rnd.randint(2, N - 3)
        if math.hypot(x - CX, z - CZ) < 36 or z > N - 26: continue
        h = rnd.randint(10, 18)
        b.cyl(x, z, 1.0, 1, h, "minecraft:jungle_log[axis=y]")
        b.sphere(x, h + 1, z, rnd.uniform(3.5, 5), "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]", ry=2.6)
        for k in range(3):
            vx, vz = x + rnd.randint(-3, 3), z + rnd.randint(-3, 3)
            for y in range(h - 1, h - 1 - rnd.randint(3, 9), -1): b.fill_if(vx, y, vz, "minecraft:vine[east=false,north=true,south=false,up=false,west=false]")
    # broken ruins of the ancient city in the jungle
    for i in range(14):
        x0, z0 = rnd.randint(4, N - 16), rnd.randint(4, N - 34)
        if math.hypot(x0 + 5 - CX, z0 + 5 - CZ) < 38: continue
        ruin(b, x0, z0, rnd.randint(6, 11), rnd.randint(6, 11), rnd.randint(3, 8), rnd)
    # the cove: the old anchor stone and the Oro Jackson's mooring
    b.box(CX - 3, 1, N - 30, CX + 3, 2, N - 27, ANC); b.set(CX, 3, N - 28, "onepiece:anchor[facing=south]")
    T.pier(b, CX - 2, N - 26, 12, axis="z", boat=False)
    # ---------------- the labyrinth: concentric ancient walls with gaps
    for ring_r, gap_a in ((34, 270), (28, 90), (22, 200), (16, 20)):
        for a in range(0, 360, 2):
            if abs((a - gap_a + 180) % 360 - 180) < 8: continue
            t = math.radians(a)
            x, z = round(CX + ring_r * math.cos(t)), round(CZ + ring_r * math.sin(t))
            for y in range(1, 7): b.set(x, y, z, ANC if (y + a) % 5 else CHIS)
            b.set(x, 7, z, "minecraft:mossy_stone_brick_wall" if a % 6 == 0 else AIR)
        for a in range(0, 360, 45):  # radial blockers make it a maze
            if abs((a - gap_a + 180) % 360 - 180) < 30: continue
            t = math.radians(a + 22)
            for rr in range(ring_r - 5, ring_r):
                for y in range(1, 6): b.set(round(CX + rr * math.cos(t)), y, round(CZ + rr * math.sin(t)), ANC2)
    for a in range(0, 360, 2):  # paving inside the labyrinth
        for rr in range(0, 35):
            t = math.radians(a)
            x, z = round(CX + rr * math.cos(t)), round(CZ + rr * math.sin(t))
            if b.get(x, 1, z) not in (ANC, CHIS, ANC2): b.set(x, 0, z, "minecraft:stone_bricks" if (x + z) % 4 else "minecraft:mossy_stone_bricks"); b.set(x, 1, z, AIR) if b.get(x, 1, z) else None
    # ---------------- the Sun Gate of Joy Boy (on the south edge of the labyrinth)
    gx, gz = CX, CZ + 36
    for dx in (-7, 7): b.box(gx + dx - 1, 1, gz - 1, gx + dx + 1, 16, gz + 1, CHIS)
    b.box(gx - 9, 17, gz - 1, gx + 9, 19, gz + 1, ANC)
    for a in range(0, 360, 6):
        t = math.radians(a)
        for rr in (3, 4, 5):
            b.set(gx + round(rr * math.cos(t)), 23 + round(rr * math.sin(t)), gz, GOLD if rr == 5 or a % 30 == 0 else "minecraft:yellow_concrete")
    b.set(gx, 23, gz, GOLD)
    # ---------------- the stepped temple at the centre
    for k in range(5):
        hw = 12 - k * 2
        b.box(CX - hw, 1 + k * 4, CZ - hw, CX + hw, 4 + k * 4, CZ + hw, ANC if k % 2 else "minecraft:stone_bricks")
        for x in range(CX - hw, CX + hw + 1, 2):
            b.set(x, 4 + k * 4, CZ + hw, CHIS); b.set(x, 4 + k * 4, CZ - hw, CHIS)
    for k in range(5):  # stairs up each step of the east face
        hw = 12 - k * 2
        for j in range(4):
            for z in (CZ - 1, CZ, CZ + 1): b.set(CX + hw + 2 - j // 2 if False else CX + hw + 1, 1 + k * 4 + j, z, "minecraft:ladder[facing=east,waterlogged=false]")
    b.box(CX - 2, 21, CZ - 2, CX + 2, 25, CZ + 2, GOLD); b.box(CX - 1, 21, CZ - 1, CX + 1, 24, CZ + 1, AIR)
    b.set(CX, 26, CZ, "minecraft:beacon") if False else b.set(CX, 26, CZ, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    # inside the temple: the hall of murals, the Poneglyph chamber, the treasure vault
    b.box(CX - 10, 1, CZ - 10, CX + 10, 8, CZ + 10, AIR)
    b.walls(CX - 11, 1, CZ - 11, CX + 11, 9, CZ + 11, CHIS)
    b.box(CX - 10, 9, CZ - 10, CX + 10, 9, CZ + 10, "minecraft:stone_bricks")
    for x in range(CX - 2, CX + 3):
        for y in range(1, 5): b.set(x, y, CZ + 11, AIR); b.set(x, y, CZ + 12, AIR)
    for z in range(CZ - 10, CZ + 11):
        for y in range(1, 9): b.set(CX - 3, y, z, ANC); b.set(CX + 3, y, z, ANC)
    for y in (1, 2, 3):
        b.set(CX - 3, y, CZ + 6, AIR); b.set(CX + 3, y, CZ + 6, AIR)
    for z in range(CZ - 10, CZ + 11, 3):  # murals: gold and black panels
        for y in (3, 4, 5):
            b.set(CX - 11, y, z, "minecraft:yellow_glazed_terracotta" if (y + z) % 2 else "minecraft:black_glazed_terracotta")
            b.set(CX + 11, y, z, "minecraft:yellow_glazed_terracotta" if (y + z) % 2 else "minecraft:black_glazed_terracotta")
    I.furnish(b, CX - 2, 1, CZ - 10, CX + 2, CZ + 10, 7, "chapel", VOID, seed=1)
    I.furnish(b, CX - 10, 1, CZ - 10, CX - 4, CZ + 10, 7, "library", VOID, seed=2)
    I.furnish(b, CX + 4, 1, CZ - 10, CX + 10, CZ + 10, 7, "treasure", VOID, seed=3)
    b.set(CX, 1, CZ - 8, "onepiece:poneglyph"); b.set(CX, 2, CZ - 8, "onepiece:poneglyph")
    for (dx, dz) in ((-1, -8), (1, -8)): b.set(CX + dx, 1, CZ + dz, "minecraft:candle[candles=4,lit=true,waterlogged=false]")
    for i in range(30):  # the One Piece: heaps of gold in the vault
        x, z = rnd.randint(CX + 5, CX + 9), rnd.randint(CZ - 8, CZ + 8)
        b.set(x, 1, z, rnd.choice((GOLD, "minecraft:raw_gold_block", "minecraft:gold_block", "onepiece:berry_block")))
    # ---------------- loot, Roger and the guardians
    b.chest(CX + 8, 2, CZ, "laugh_tale", "west"); b.chest(CX + 8, 2, CZ + 2, "legendary", "west")
    b.chest(CX - 8, 1, CZ, "void_century", "east")
    b.npc(CX + 6, 1, CZ, "roger", False)
    b.guards("ancient_guardian", ((CX + 31, CZ), (CX - 31, CZ), (CX, CZ - 25), (CX + 19, CZ + 10), (CX - 19, CZ - 10), (CX, CZ + 19)))
    b.guards("warden_jailer", ((gx - 4, gz + 3), (gx + 4, gz + 3)))
    return b, 0
