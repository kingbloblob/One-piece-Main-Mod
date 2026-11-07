"""Marineford: Marine Headquarters. The great stepped HQ with 海 [gull] 軍 on its face, castle eaves on every tier and a
Japanese castle keep on top, the execution tower on the admirals' wall, Oris Plaza with the Ox Bell, the crescent bay
with docked battleships, and the Encircling Wall with its cannons. ~224 x 224, HQ ~99 tall. Ground = y 0, the bay opens to +z (south)."""
import math, random
from canvas import *

SID = "marineford"
TITLE = "Marineford (Marine Headquarters)"
CUTS = []
TILER = dict(terrain="beard_thin")

WHITE = "onepiece:marine_bricks"
WHITE_ST = "onepiece:marine_brick_stairs"
WHITE_W = "onepiece:marine_brick_wall"
TILE = "onepiece:marine_tiles"
TILE_ST = "onepiece:marine_tile_stairs"
PIL = "onepiece:marine_pillar[axis=y]"
BLUE = "minecraft:blue_terracotta"
ROOF_ST = "onepiece:wano_roof_tile_stairs"
ROOF = "onepiece:wano_roof_tiles"
PAVE = "minecraft:polished_andesite"
N = 224
CX = 112
BAY_C, BAY_R = (CX, 262), 112


def in_bay(x, z):
    return math.hypot(x - BAY_C[0], z - BAY_C[1]) <= BAY_R


def gull(b, x, y, z, s="minecraft:blue_concrete", axis="x"):
    """The Marine seagull emblem (spread wings), drawn on the plane z facing +z (axis x)."""
    pts = [(0, 0), (0, 1), (-1, 1), (1, 1), (0, 2)]
    for k in range(1, 9):
        dy = int(round(2 - abs(k - 4) * 0.6 + (k > 4) * 0.0))
        for side in (-1, 1): pts.append((side * k, 2 + (1 if k < 5 else 0) - k // 4)); pts.append((side * k, 1 + (1 if k < 3 else 0)))
    for (dx, dy) in pts:
        b.set(x + dx, y + dy, z, s)


# 海軍 (Kaigun, "Marines"): the two characters on the face of the HQ in the show, with the gull emblem between them.
KAI = (".#...#.......",
       "..#.#........",
       "....#########",
       "...#.........",
       "#...#######..",
       ".#..#.....#..",
       "....#..#..#..",
       "...##########",
       "....#.....#..",
       "..#.#..#..#..",
       ".#..#######..",
       "#.........#..",
       "#........##..")
GUN = ("#############",
       "#...........#",
       "#...........#",
       "..#########..",
       "......#......",
       "...#######...",
       "...#..#..#...",
       "...#######...",
       "...#..#..#...",
       "...#######...",
       "......#......",
       ".###########.",
       "......#......")
GULL = ("#.................#",
        "##...............##",
        ".###.....#.....###.",
        "..####..###..####..",
        "...#############...",
        ".....#########.....",
        ".......#####.......",
        "........###........",
        ".......#.#.#.......")


def glyph(b, g, x, y, z, s):
    """A pixel picture on the plane z, read the right way round from +z (south). (x, y) = top left."""
    for row, bits in enumerate(g):
        for col, ch in enumerate(bits):
            if ch == "#": b.set(x + col, y - row, z, s)


def castle_eave(b, x0, x1, z0, z1, top, depth=3):
    """Japanese castle eave all round a tier whose wall top is y=top: tiles over the wall top, stairs stepping out
    and down, corners turned up at the tips, and white brackets under the eave line."""
    for d in range(depth + 1):
        y = top + 1 - d
        ex0, ex1, ez0, ez1 = x0 - d, x1 + d, z0 - d, z1 + d
        if d == 0:
            for x in range(ex0, ex1 + 1): b.set(x, y, ez0, ROOF); b.set(x, y, ez1, ROOF)
            for z in range(ez0, ez1 + 1): b.set(ex0, y, z, ROOF); b.set(ex1, y, z, ROOF)
            continue
        for x in range(ex0 + 1, ex1):
            b.set(x, y, ez0, stairs(ROOF_ST, "south")); b.set(x, y, ez1, stairs(ROOF_ST, "north"))
        for z in range(ez0 + 1, ez1):
            b.set(ex0, y, z, stairs(ROOF_ST, "east")); b.set(ex1, y, z, stairs(ROOF_ST, "west"))
        b.set(ex0, y, ez0, stairs(ROOF_ST, "east", shape="outer_right")); b.set(ex1, y, ez0, stairs(ROOF_ST, "south", shape="outer_right"))
        b.set(ex0, y, ez1, stairs(ROOF_ST, "north", shape="outer_right")); b.set(ex1, y, ez1, stairs(ROOF_ST, "west", shape="outer_right"))
    y = top + 1 - depth  # up-turned tips
    for (cx, cz) in ((x0 - depth, z0 - depth), (x1 + depth, z0 - depth), (x0 - depth, z1 + depth), (x1 + depth, z1 + depth)):
        b.set(cx, y, cz, AIR); b.set(cx, y + 1, cz, slab(ROOF.replace("tiles", "tile_slab"), "bottom"))
    for x in range(x0, x1 + 1, 4):
        b.set(x, top - 1, z0 - 1, stairs(WHITE_ST, "south", "top")); b.set(x, top - 1, z1 + 1, stairs(WHITE_ST, "north", "top"))
    for z in range(z0, z1 + 1, 4):
        b.set(x0 - 1, top - 1, z, stairs(WHITE_ST, "east", "top")); b.set(x1 + 1, top - 1, z, stairs(WHITE_ST, "west", "top"))


def ox_bell(b, x, z):
    """The Ox Bell at the front of Oris Plaza: a huge bronze temple bell in a timber bell frame with a tiled roof."""
    b.box(x - 6, 0, z - 6, x + 6, 1, z + 6, WHITE)
    for sx in (-5, 5):
        for sz in (-5, 5): b.column(x + sx, z + sz, 2, 14, "minecraft:dark_oak_log[axis=y]")
    for y in (15, 16):
        for k in range(-6, 7):
            b.set(x + k, y, z - 5, "minecraft:dark_oak_log[axis=x]"); b.set(x + k, y, z + 5, "minecraft:dark_oak_log[axis=x]")
            b.set(x - 5, y, z + k, "minecraft:dark_oak_log[axis=z]"); b.set(x + 5, y, z + k, "minecraft:dark_oak_log[axis=z]")
    for k in range(-5, 6): b.set(x, 16, z + k, "minecraft:dark_oak_log[axis=z]"); b.set(x + 4, 15, z + k, "minecraft:dark_oak_log[axis=z]")
    b.pagoda_roof(x, z, 8, 8, 17, ROOF_ST, ROOF, layers=4)
    for y in (14, 15): b.set(x, y, z, "minecraft:iron_chain[axis=y,waterlogged=false]")
    for (y, r) in ((13, 1), (12, 2), (11, 2), (10, 2), (9, 3), (8, 3), (7, 3), (6, 3), (5, 3)):  # top to lip
        b.cyl(x, z, r, y, y, "minecraft:waxed_cut_copper" if y in (11, 7) else "minecraft:waxed_copper_block")
    b.cyl(x, z, 2, 5, 8, AIR)
    # the striking log, hung on a rope from the side beam and pointing at the bell
    for y in range(10, 15): b.set(x + 4, y, z, fence("spruce"))
    b.set(x + 4, 9, z, "minecraft:stripped_spruce_log[axis=x]"); b.set(x + 5, 9, z, "minecraft:stripped_spruce_log[axis=x]")


def battleship(b, x0, z0, L=40):
    W = 11
    dy = b.ship(x0, -6, z0, L, W, hull="minecraft:white_concrete", deck="minecraft:spruce_planks", masts=((L // 3, 18), (2 * L // 3, 20)),
                sail="minecraft:white_wool", flag=("minecraft:white_wool", "minecraft:blue_wool"), cabin=(L // 4, 5, "minecraft:white_concrete"), depth=6)
    cz = z0 + W // 2
    for x in range(x0 + 2, x0 + L - 6, 4):  # blue stripe and cannons
        for side in (-1, 1): b.set(x, -1, cz + side * (W // 2 - 1) + side * 0, "minecraft:blue_concrete")
    for x in range(x0 + 8, x0 + L - 8, 6):
        b.set(x, dy + 1, cz - 3, "onepiece:cannon[facing=north]"); b.set(x, dy + 1, cz + 3, "onepiece:cannon[facing=south]")
    # the seagull figurehead
    b.set(x0 + L, dy, cz, "minecraft:white_concrete"); b.set(x0 + L + 1, dy + 1, cz, "minecraft:white_concrete"); b.set(x0 + L, dy + 1, cz - 1, "minecraft:white_concrete"); b.set(x0 + L, dy + 1, cz + 1, "minecraft:white_concrete")


def build():
    b = B()
    # ---------------- ground, bay, plaza
    for x in range(0, N + 1):
        for z in range(0, N + 1):
            b.box(x, -10, z, x, -1, z, "minecraft:stone")
            if in_bay(x, z):
                b.box(x, -9, z, x, 0, z, WATER); b.set(x, -10, z, "minecraft:sand")
            else:
                b.set(x, 0, z, PAVE if z > 96 else "minecraft:stone_bricks")
    for x in range(0, N + 1):  # plaza pattern
        for z in range(96, 160):
            if not in_bay(x, z) and (x // 4 + z // 4) % 2 == 0: b.set(x, 0, z, "minecraft:polished_diorite")
    # quay wall along the bay
    for x in range(0, N + 1):
        for z in range(96, N + 1):
            if not in_bay(x, z) and any(in_bay(x + dx, z + dz) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                for y in range(-9, 1): b.set(x, y, z, WHITE)
                b.set(x, 1, z, PIL if x % 9 == 0 else wall(WHITE_W))  # balustrade: also keeps a high sea off the plaza
    # a low kerb round the island's edge, so the sea can't spill onto the plaza when the island sits at sea level
    for k in range(N + 1):
        for (x, z) in ((k, 0), (k, N), (0, k), (N, k)):
            if not in_bay(x, z): b.set(x, 1, z, slab("onepiece:marine_brick_slab", "bottom"))
    # ---------------- the Encircling Wall: a ring of wall segments around the bay edge, with cannons on top
    for a in range(-80, 81, 1):
        t = math.radians(a)
        r = BAY_R - 2
        x = round(BAY_C[0] + r * math.sin(t)); z = round(BAY_C[1] - r * math.cos(t))
        if not (0 <= x <= N and 0 <= z <= N) or a % 22 in (0, 1, 2): continue  # gaps between the panels
        for k in range(3):
            xx = round(BAY_C[0] + (r - k) * math.sin(t)); zz = round(BAY_C[1] - (r - k) * math.cos(t))
            for y in range(-9, 17): b.set(xx, y, zz, "minecraft:iron_block" if y in (0, 8, 16) else "minecraft:light_gray_concrete")
        if a % 6 == 0:
            xx = round(BAY_C[0] + (r - 1) * math.sin(t)); zz = round(BAY_C[1] - (r - 1) * math.cos(t))
            b.set(xx, 17, zz, "onepiece:cannon[facing=south]")
    # ---------------- docked battleships in the bay
    battleship(b, 20, 190, 44)
    battleship(b, 150, 196, 44)
    battleship(b, 86, 214, 40)
    # ---------------- the execution platform (where Ace was to be executed): a tall white tower standing on the
    # raised wall where the three admirals sat, looking down over Oris Plaza
    EX, EZ = CX, 112
    PX0, PX1, PZ0, PZ1, PT = EX - 22, EX + 22, EZ - 10, EZ + 8, 12
    b.box(PX0, 1, PZ0, PX1, PT, PZ1, WHITE)
    b.box(PX0, PT, PZ0, PX1, PT, PZ1, TILE)
    for x in range(PX0, PX1 + 1, 4):
        b.column(x, PZ1 + 1, 1, PT - 1, PIL); b.column(x, PZ0 - 1, 1, PT - 1, PIL)
    for z in range(PZ0, PZ1 + 1, 4):
        b.column(PX0 - 1, z, 1, PT - 1, PIL); b.column(PX1 + 1, z, 1, PT - 1, PIL)
    for x in range(PX0 - 1, PX1 + 2):
        for z in (PZ0 - 1, PZ1 + 1): b.set(x, PT - 2, z, BLUE); b.set(x, PT, z, TILE)
        b.set(x, PT + 1, PZ1 + 1, wall(WHITE_W)); b.set(x, PT + 1, PZ0 - 1, wall(WHITE_W))
    for z in range(PZ0 - 1, PZ1 + 2):
        for x in (PX0 - 1, PX1 + 1): b.set(x, PT - 2, z, BLUE); b.set(x, PT, z, TILE); b.set(x, PT + 1, z, wall(WHITE_W))
    # wide steps up the back of the wall, from the HQ side
    for i in range(PT):
        for x in range(EX - 4, EX + 5):
            z = PZ0 - 1 - PT + i
            b.set(x, 1 + i, z, stairs(WHITE_ST, "south"))
            if i: b.box(x, 1, z, x, i, z, WHITE)
            for y in range(2 + i, 5 + i): b.set(x, y, z, AIR)
    for i in range(PT):
        for x in (EX - 5, EX + 5):
            b.box(x, 1, PZ0 - 1 - PT + i, x, 1 + i, PZ0 - 1 - PT + i, WHITE); b.set(x, 2 + i, PZ0 - 1 - PT + i, wall(WHITE_W))
    for x in range(EX - 4, EX + 5): b.set(x, PT + 1, PZ0 - 1, AIR)
    # the three admirals' chairs on the front edge of the wall
    for x in (EX - 6, EX, EX + 6): b.set(x, PT + 1, PZ1 - 1, "onepiece:captains_chair[facing=south]")
    # the tower
    TT = 50
    b.walls(EX - 4, PT + 1, EZ - 4, EX + 4, TT, EZ + 4, WHITE)
    for (cx, cz) in ((EX - 4, EZ - 4), (EX + 4, EZ - 4), (EX - 4, EZ + 4), (EX + 4, EZ + 4)): b.column(cx, cz, PT + 1, TT, PIL)
    for y in range(PT + 6, TT - 1, 6):
        for k in (-2, 2):
            b.set(EX + k, y, EZ + 4, PANE); b.set(EX + k, y, EZ - 4, PANE); b.set(EX + 4, y, EZ + k, PANE); b.set(EX - 4, y, EZ + k, PANE)
    for y in (PT + 9, PT + 18):
        for k in range(-4, 5):
            b.set(EX + k, y, EZ - 4, BLUE); b.set(EX + k, y, EZ + 4, BLUE); b.set(EX - 4, y, EZ + k, BLUE); b.set(EX + 4, y, EZ + k, BLUE)
    for y in range(PT + 1, PT + 4): b.set(EX, y, EZ - 4, AIR)
    b.set(EX, PT + 4, EZ - 4, LANTERN)
    # the top flares out on stepped corbels into the wide execution floor
    def ring(d, y, s, up=False):
        for k in range(-d, d + 1):
            for (x, z, f) in ((EX + k, EZ - d, "south"), (EX + k, EZ + d, "north"), (EX - d, EZ + k, "east"), (EX + d, EZ + k, "west")):
                b.set(x, y, z, stairs(WHITE_ST, f, "top") if up else s)
    ring(5, TT - 2, None, True)
    ring(5, TT - 1, WHITE); ring(6, TT - 1, None, True)
    ring(5, TT, WHITE); ring(6, TT, WHITE); ring(7, TT, None, True)
    FL = TT + 1
    b.box(EX - 8, FL, EZ - 8, EX + 8, FL, EZ + 8, TILE)
    for d in (8,):
        for k in range(-d, d + 1):
            for (x, z) in ((EX + k, EZ - d), (EX + k, EZ + d), (EX - d, EZ + k), (EX + d, EZ + k)): b.set(x, FL + 1, z, wall(WHITE_W))
    for y in range(PT + 1, FL + 1): b.set(EX - 3, y, EZ, ladder("east"))
    # the condemned's stand: a dark wooden dais with the stocks, facing the plaza
    b.box(EX - 2, FL + 1, EZ, EX + 2, FL + 1, EZ + 2, "minecraft:dark_oak_planks")
    b.set(EX, FL + 2, EZ + 2, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]")
    b.set(EX - 1, FL + 2, EZ + 2, "minecraft:iron_bars[east=true,north=false,south=false,west=false,waterlogged=false]")
    b.set(EX + 1, FL + 2, EZ + 2, "minecraft:iron_bars[east=false,north=false,south=false,west=true,waterlogged=false]")
    for (x, z) in ((EX - 8, EZ - 8), (EX + 8, EZ - 8), (EX - 8, EZ + 8), (EX + 8, EZ + 8)):
        b.set(x, FL + 2, z, LANTERN)
    # ---------------- the Ox Bell at the front of the plaza
    ox_bell(b, CX - 44, 138)
    # ---------------- Marine Headquarters
    HZ0 = 8
    tiers = ((CX - 52, CX + 52, HZ0, HZ0 + 70, 0, 22), (CX - 40, CX + 40, HZ0 + 6, HZ0 + 58, 22, 22), (CX - 26, CX + 26, HZ0 + 12, HZ0 + 48, 44, 18),
             (CX - 14, CX + 14, HZ0 + 18, HZ0 + 40, 62, 10))
    for i, (x0, x1, z0, z1, y0, h) in enumerate(tiers):
        b.box(x0, y0, z0, x1, y0, z1, TILE)
        b.walls(x0, y0 + 1, z0, x1, y0 + h, z1, WHITE)
        b.box(x0 + 1, y0 + 1, z0 + 1, x1 - 1, y0 + h, z1 - 1, AIR)
        for f in range(y0 + 6, y0 + h, 6): b.box(x0 + 1, f, z0 + 1, x1 - 1, f, z1 - 1, TILE)
        for x in range(x0 + 2, x1 - 1, 3):
            for z in (z0, z1):
                for f in range(y0 + 2, y0 + h - 1, 6):
                    b.set(x, f, z, pane_of("minecraft:light_blue_stained_glass_pane")); b.set(x, f + 1, z, pane_of("minecraft:light_blue_stained_glass_pane")); b.set(x, f + 2, z, PANE)
        for z in range(z0 + 2, z1 - 1, 3):
            for x in (x0, x1):
                for f in range(y0 + 2, y0 + h - 1, 6):
                    b.set(x, f, z, pane_of("minecraft:light_blue_stained_glass_pane")); b.set(x, f + 1, z, PANE)
        for x in range(x0, x1 + 1, 8):
            for z in (z0, z1): b.column(x, z, y0 + 1, y0 + h, PIL)
        # each tier ends in a sloped blue-tiled castle eave, like the stacked roofs of the HQ in the show
        b.box(x0, y0 + h + 1, z0, x1, y0 + h + 1, z1, TILE)
        castle_eave(b, x0, x1, z0, z1, y0 + h, depth=3)
        b.stairs_up(x1 - 3, y0 + 1, z0 + 2, 6, WHITE_ST, "south")
    # the Japanese castle keep (the pagoda on top of the HQ): two white storeys under stacked roofs, gold ridge fish
    KZ = HZ0 + 29
    b.walls(CX - 10, 74, KZ - 8, CX + 10, 81, KZ + 8, WHITE)
    b.box(CX - 9, 74, KZ - 7, CX + 9, 81, KZ + 7, AIR)
    for (cx, cz) in ((CX - 10, KZ - 8), (CX + 10, KZ - 8), (CX - 10, KZ + 8), (CX + 10, KZ + 8)): b.column(cx, cz, 74, 81, PIL)
    for x in range(CX - 8, CX + 9, 4):
        for z in (KZ - 8, KZ + 8): b.set(x, 77, z, PANE); b.set(x, 78, z, PANE)
    for z in range(KZ - 4, KZ + 5, 4):
        for x in (CX - 10, CX + 10): b.set(x, 77, z, PANE); b.set(x, 78, z, PANE)
    for y in range(74, 77): b.set(CX, y, KZ + 8, AIR)
    castle_eave(b, CX - 10, CX + 10, KZ - 8, KZ + 8, 81, depth=3)
    b.box(CX - 9, 82, KZ - 7, CX + 9, 82, KZ + 7, ROOF)
    b.walls(CX - 6, 83, KZ - 5, CX + 6, 89, KZ + 5, WHITE)
    b.box(CX - 5, 83, KZ - 4, CX + 5, 89, KZ + 4, AIR)
    for (cx, cz) in ((CX - 6, KZ - 5), (CX + 6, KZ - 5), (CX - 6, KZ + 5), (CX + 6, KZ + 5)): b.column(cx, cz, 83, 89, PIL)
    for x in range(CX - 4, CX + 5, 4):
        for z in (KZ - 5, KZ + 5): b.set(x, 86, z, PANE); b.set(x, 87, z, PANE)
    b.column(CX - 6, KZ, 74, 82, PIL)  # ladder up into the top storey
    for y in range(74, 90): b.set(CX - 5, y, KZ, ladder("east"))
    b.hip_roof(CX - 6, KZ - 5, CX + 6, KZ + 5, 90, ROOF_ST, ROOF, overhang=3)
    ridge_y = 90 + 8
    for x in (CX - 2, CX + 2): b.column(x, KZ, ridge_y, ridge_y + 1, "minecraft:gold_block")  # the golden ridge fish
    # 海 [gull] 軍 across the front of the second tier, as on the HQ in the show
    zf = HZ0 + 59
    b.box(CX - 30, 26, zf, CX + 30, 42, zf, "minecraft:white_concrete")
    for x in range(CX - 31, CX + 32): b.set(x, 25, zf, BLUE); b.set(x, 43, zf, BLUE)
    for y in range(25, 44): b.set(CX - 31, y, zf, BLUE); b.set(CX + 31, y, zf, BLUE)
    glyph(b, KAI, CX - 27, 40, zf + 1, "minecraft:black_concrete")
    glyph(b, GULL, CX - 9, 38, zf + 1, "minecraft:blue_concrete")
    glyph(b, GUN, CX + 15, 40, zf + 1, "minecraft:black_concrete")
    gull(b, CX, 14, HZ0 + 71, "minecraft:blue_concrete")
    # grand gate and front steps
    for x in range(CX - 7, CX + 8):
        for y in range(1, 12): b.set(x, y, HZ0 + 70, AIR)
    for i in range(6):
        for x in range(CX - 12, CX + 13): b.set(x, 0 if i == 0 else 0, HZ0 + 71 + i, PAVE)
    for x in (CX - 9, CX + 9, CX - 15, CX + 15):
        b.column(x, HZ0 + 72, 1, 18, PIL)
    b.box(CX - 16, 19, HZ0 + 71, CX + 16, 19, HZ0 + 74, WHITE)
    for x in range(CX - 16, CX + 17): b.set(x, 20, HZ0 + 74, stairs(ROOF_ST, "north"))
    # inside the ground floor: the great hall with blue carpet, the fleet admiral's office on top
    for z in range(HZ0 + 2, HZ0 + 70): b.set(CX, 1, z, "minecraft:blue_carpet"); b.set(CX - 1, 1, z, "minecraft:blue_carpet"); b.set(CX + 1, 1, z, "minecraft:blue_carpet")
    for z in range(HZ0 + 8, HZ0 + 66, 8):
        for x in (CX - 10, CX + 10): b.column(x, z, 1, 5, PIL)
        b.set(CX, 5, z, HANG)
    b.chest(CX - 30, 1, HZ0 + 20, "marine", "east"); b.chest(CX + 30, 1, HZ0 + 30, "marine", "west")
    b.set(CX, 63, HZ0 + 25, "onepiece:navigators_desk[facing=south]"); b.chest(CX + 3, 63, HZ0 + 22, "legendary", "south")
    for x in range(CX - 10, CX + 11, 4): b.set(x, 63, HZ0 + 36, "minecraft:bookshelf"); b.set(x, 64, HZ0 + 36, "minecraft:bookshelf")
    # ---------------- side barracks, watchtowers and cannon batteries on the plaza
    for (x0, x1) in ((6, 44), (180, 218)):
        b.box(x0, 0, 40, x1, 0, 92, TILE)
        b.walls(x0, 1, 40, x1, 12, 92, WHITE)
        b.box(x0 + 1, 1, 41, x1 - 1, 12, 91, AIR)
        b.box(x0 + 1, 6, 41, x1 - 1, 6, 91, TILE)
        b.hip_roof(x0, 40, x1, 92, 13, ROOF_ST, ROOF, overhang=1)
        for z in range(42, 91, 3):
            bed("blue", x0 + 2, 1, z, b, "east") if x0 < CX else bed("blue", x1 - 3, 1, z, b, "east")
            bed("white", x0 + 2, 7, z, b, "east") if x0 < CX else bed("white", x1 - 3, 7, z, b, "east")
        for z in range(43, 91, 4):
            for x in (x0, x1): b.set(x, 3, z, PANE); b.set(x, 9, z, PANE)
        for y in range(1, 4):
            for z in range(64, 68): b.set(x1 if x0 < CX else x0, y, z, AIR)
        b.stairs_up(x0 + 6, 1, 44, 5, WHITE_ST, "south")
    for (tx, tz) in ((10, 10), (214, 10), (24, 140), (200, 140)):
        b.cyl(tx, tz, 4, 1, 34, WHITE); b.cyl(tx, tz, 3, 1, 34, AIR)
        b.cyl(tx, tz, 5, 35, 35, TILE)
        for a in range(0, 360, 30):
            t = math.radians(a); b.set(round(tx + 5 * math.cos(t)), 36, round(tz + 5 * math.sin(t)), wall(WHITE_W))
        b.set(tx, 36, tz, "onepiece:cannon[facing=south]")
        for y in range(1, 35): b.set(tx, y, tz - 3, ladder("south"))
        b.set(tx, 37, tz, fence("dark_oak")); b.set(tx, 38, tz, fence("dark_oak")); b.box(tx, 38, tz + 1, tx, 39, tz + 3, "minecraft:blue_wool")
    for x in range(30, 200, 10):  # front battery along the quay
        z = 150
        if not in_bay(x, z) and not (CX - 20 < x < CX + 20):
            b.set(x, 1, z, "onepiece:cannon[facing=south]")
            b.set(x - 1, 1, z, "minecraft:polished_andesite_slab[type=bottom,waterlogged=false]"); b.set(x + 1, 1, z, "minecraft:polished_andesite_slab[type=bottom,waterlogged=false]")
    for x in range(4, N - 3, 8):  # lamp posts
        if EX - 24 <= x <= EX + 24: continue
        b.column(x, 98, 1, 4, fence("dark_oak")); b.set(x, 5, 98, LANTERN)
    # ---------------- people
    b.npc(EX, PT + 1, PZ1 - 2, "akainu", True)
    b.guards("vice_admiral", ((EX - 12, EZ + 10), (EX + 12, EZ + 10)))
    b.guards("pacifista", ((EX - 20, EZ + 20), (EX + 20, EZ + 20)))
    b.guards("elite_marine", ((CX - 6, 92), (CX + 6, 92), (CX, 140)))
    b.guards("marine", ((40, 120), (70, 130), (150, 130), (180, 120), (CX, 82)))
    b.guards("marine_rifle", ((24, 140), (200, 140)), y=36)
    b.guards("marine_rifle", ((CX - 30, 150), (CX + 30, 150)))
    # ---------------- HQ stairs between every floor and furnished offices on each floor
    import interiors as I
    plates = []
    for (x0, x1, z0, z1, y0, h) in tiers:
        plates += [(p, (x0, x1, z0, z1, y0, h)) for p in range(y0, y0 + h, 6)]
    for k, (p, t) in enumerate(plates):
        nxt = plates[k + 1][0] if k + 1 < len(plates) else None
        if nxt is None: break
        sx = CX + 8 if k % 2 == 0 else CX + 11
        b.stairs_up(sx, p + 1, HZ0 + 20, nxt - p, WHITE_ST, "south", w=2, clear=3)
    marine_rooms = ("study", "barracks", "library", "dining", "armory", "kitchen", "bedroom", "storage", "study", "library")
    for k, (p, (x0, x1, z0, z1, y0, h)) in enumerate(plates):
        nxt = plates[k + 1][0] if k + 1 < len(plates) else y0 + h
        if k == 0:
            r = I.Room(b, x0 + 1, 1, z0 + 1, x1 - 1, z1 - 1, nxt - 1, "marine", random.Random(4))
            r.wall_banners(5, 3); r.paintings(8); r.plants(10)
            continue
        if k == len(plates) - 1:
            I.furnish(b, x0 + 1, p + 1, z0 + 1, x1 - 1, z1 - 1, nxt - p - 1, "study", "marine")
            continue
        I.subdivide(b, x0 + 1, p + 1, z0 + 1, x1 - 1, z1 - 1, nxt - p - 1, WHITE, marine_rooms[k % len(marine_rooms):] + marine_rooms[:k % len(marine_rooms)],
                    "marine", cell=13, keepout=((CX + 6, HZ0 + 18, CX + 13, HZ0 + 18 + 8),), seed=k)
    b.stairs_up(CX - 8, 69, HZ0 + 21, 4, WHITE_ST, "south", w=2)  # from the fleet admiral's floor up to the keep
    # barracks: both floors
    for (x0, x1) in ((6, 44), (180, 218)):
        I.furnish(b, x0 + 1, 1, 41, x1 - 1, 91, 5, "barracks", "marine")
        I.furnish(b, x0 + 1, 7, 41, x1 - 1, 91, 5, "barracks", "marine")
    return b, 0
