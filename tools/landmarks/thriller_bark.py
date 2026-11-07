"""Thriller Bark: Gecko Moria's island-sized ghost ship. A giant hull carrying a haunted island: the bow gate,
the misty forest, the graveyard, Hogback's mansion, the great mast with Moria's bat flag and Moria's castle at the
stern. ~230 x 110, mast ~110 tall. Water surface = y 0, bow points +x."""
import math, random
from canvas import *

SID = "thriller_bark"
TITLE = "Thriller Bark"
WATER_Y = 0
CUTS = []
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="none")

HULL = "minecraft:dark_oak_planks"
HULL2 = "minecraft:mangrove_planks"
TRIM = "minecraft:stripped_dark_oak_log[axis=x]"
GLOOM_LOG = "onepiece:gloom_log[axis=y]"
GLOOM_LEAF = "onepiece:gloom_leaves[distance=7,persistent=true,waterlogged=false]"
CASTLE = "minecraft:deepslate_bricks"
CASTLE2 = "minecraft:polished_blackstone_bricks"
ROOF_ST = "minecraft:deepslate_tile_stairs"   # slate-dark roofs, as in the show's night-time haunted island
ROOF = "minecraft:deepslate_tiles"
SPIRE = "minecraft:purple_terracotta"         # plum spires: the arc's purple haze palette
BONE = "minecraft:bone_block[axis=y]"
L, BEAM, CZ = 212, 104, 52
KEEL, DECK = -14, 12
WALL_TOP = DECK + 10    # the great outer wall that rings the whole island
GX0, GX1, GW, GT = L - 5, L, 18, DECK + 26   # the mouth gatehouse at the bow


def spire_cone(b, cx, cz, r, y, h, mat=SPIRE, eave=ROOF, tip=True):
    """Pointed gothic tower roof: a dark eave ring at y, then a cone of `mat` h tall. Returns the top y."""
    b.cyl(cx, cz, r + 1, y, y, eave)
    for k in range(h):
        rr = r * (1 - k / h) + 0.3
        b.cyl(cx, cz, rr, y + 1 + k, y + 1 + k, mat, hollow=rr > 1.6)
    if tip: b.set(cx, y + h + 1, cz, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    return y + h + 1


FLAG = [  # Moria's Jolly Roger: white skull crowned with two purple bat wings, flanked by pale flames

    ".PP...................PP.",
    ".PPPP...............PPPP.",
    "..PPPPPP.........PPPPPP..",
    "..PPPPPPPP.WWW.PPPPPPPP..",
    "...PP.PPPWWWWWWWPPP.PP...",
    "...P...PWWWWWWWWWP...P...",
    "..F....WW..WWW..WW....F..",
    ".FF....WW..WWW..WW....FF.",
    ".FFF...WWWWW.WWWWW...FFF.",
    "FFFF....WWWWWWWWW....FFFF",
    "FFFF.....W.W.W.W.....FFFF",
    ".FF......WWWWWWW......FF.",
]


def hw(x):
    f = x / L
    if f < 0 or f > 1: return 0
    k = 1.0
    if f > 0.78: k = math.sqrt(max(0.0, 1 - ((f - 0.78) / 0.24) ** 2))
    if f < 0.06: k = 0.85 + 0.15 * f / 0.06
    return BEAM / 2 * k


def hull_in(x, y, z):
    if y > DECK: return False
    t = (y - KEEL) / (DECK - KEEL)
    if t < 0: return False
    f = x / L
    rise = (f - 0.85) / 0.15 * 10 if f > 0.85 else 0
    if y < KEEL + rise: return False
    return abs(z - CZ) <= hw(x) * math.sin(min(1, t) * math.pi / 2) ** 0.4


def gloom_tree(b, x, y, z, h, rnd):
    for yy in range(y, y + h): b.set(x, yy, z, GLOOM_LOG)
    for k in range(3):  # twisted bare branches
        a = rnd.uniform(0, 6.28); ln = rnd.randint(3, 5); by = y + h - 2 - k * 2
        for i in range(1, ln):
            b.set(round(x + math.cos(a) * i), by + i // 2, round(z + math.sin(a) * i), "onepiece:gloom_wood[axis=y]" if False else "onepiece:gloom_log[axis=x]")
    b.sphere(x, y + h, z, 2.2, GLOOM_LEAF, ry=1.6)


def build():
    rnd = random.Random(13)
    b = B()
    # ---------------- hull
    def mat(x, y, z):
        if y == DECK: return "minecraft:mud"
        if y in (DECK - 2, 4, -4): return TRIM
        return HULL2 if (y // 3) % 2 else HULL
    b.shape(hull_in, -1, KEEL, 0, L + 1, DECK, BEAM, mat, interior=None)
    # (the great outer wall round the deck edge is built after the island ground, below)
    for x in range(10, L - 20, 10):  # portholes glowing green
        for side in (-1, 1):
            zz = CZ + side * int(hw(x) * math.sin((4 - KEEL) / (DECK - KEEL) * math.pi / 2) ** 0.4)
            b.set(x, 6, zz, "minecraft:lime_stained_glass"); b.set(x, 7, zz, "minecraft:lime_stained_glass")
    # ---------------- the island on deck: hills of mud and podzol
    def hill(x, z):
        return 6 * math.exp(-(((x - 70) / 30) ** 2 + ((z - CZ - 18) / 20) ** 2)) + 4 * math.exp(-(((x - 140) / 25) ** 2 + ((z - CZ + 20) / 16) ** 2)) \
            + 1.5 * math.sin(x * 0.2) * math.cos(z * 0.17)
    ground = {}
    for x in range(2, L - 2):
        w = int(hw(x)) - 2
        for z in range(CZ - w, CZ + w + 1):
            if not hull_in(x, DECK, z): continue
            h = max(0, int(hill(x, z)))
            for y in range(DECK, DECK + h + 1):
                b.set(x, y, z, "minecraft:mud" if y < DECK + h else rnd.choice(("minecraft:podzol[snowy=false]", "minecraft:coarse_dirt", "minecraft:podzol[snowy=false]", "minecraft:mycelium[snowy=false]")))
            ground[(x, z)] = DECK + h
    # paths
    for x in range(20, L - 5):
        for dz in range(-2, 3):
            z = CZ + dz
            if (x, z) in ground:
                b.set(x, ground[(x, z)], z, "minecraft:dirt_path")
    # ---------------- the great outer wall: a dark stone rampart rings the whole island on the deck edge
    deck = {(x, z) for x in range(0, L + 1) for z in range(0, BEAM + 1) if hull_in(x, DECK, z)}
    def dist(x, z):
        for d in (1, 2):
            if any((x + i, z + j) not in deck for i in range(-d, d + 1) for j in range(-d, d + 1)): return d
        return 3
    ring = {p: dist(*p) for p in deck}
    ring = {p: d for p, d in ring.items() if d <= 2}
    wrnd = random.Random(31)
    def wmat(y):
        if y <= DECK + 2: return "minecraft:polished_blackstone_bricks"
        return "minecraft:cracked_deepslate_bricks" if wrnd.random() < 0.14 else CASTLE
    for (x, z), d in ring.items():
        for y in range(DECK + 1, WALL_TOP + 1): b.set(x, y, z, wmat(y))
        b.set(x, WALL_TOP, z, "minecraft:polished_blackstone")  # wall-walk
    # outside the wall face: buttresses, a corbelled parapet with merlons, arrow-slit recesses
    out = {}
    for (x, z), d in ring.items():
        if d != 1: continue
        for (i, j, f) in ((1, 0, "west"), (-1, 0, "east"), (0, 1, "north"), (0, -1, "south")):
            q = (x + i, z + j)
            if q not in deck and q not in out: out[q] = (f, j != 0)
    for (x, z), (f, side) in out.items():
        if x >= GX0 - 1 and abs(z - CZ) <= GW: continue  # the gatehouse face has its own trim
        k = x if side else z
        if k % 12 == 0:  # buttress down the face onto the hull
            for y in range(DECK - 3, WALL_TOP - 1): b.set(x, y, z, CASTLE2)
        else:
            b.set(x, WALL_TOP - 1, z, stairs("minecraft:polished_blackstone_brick_stairs", f, "top"))
        b.set(x, WALL_TOP, z, CASTLE2); b.set(x, WALL_TOP + 1, z, CASTLE2)
        if (x + z) % 2 == 0: b.set(x, WALL_TOP + 2, z, CASTLE2)
        if k % 24 == 12 and (x + z) % 2 == 0: b.set(x, WALL_TOP + 3, z, "minecraft:soul_lantern[hanging=false,waterlogged=false]")
        if k % 12 == 6:  # arrow slit: a dark recess in the outer course
            ox, oz = {"west": (-1, 0), "east": (1, 0), "north": (0, -1), "south": (0, 1)}[f]
            for y in range(WALL_TOP - 5, WALL_TOP - 2): b.set(x + ox, y, z + oz, "minecraft:black_stained_glass")
    # ---------------- graveyard (zombies rise from here)
    gy0, gz0 = 92, CZ + 12
    for i in range(6):
        for j in range(4):
            x, z = gy0 + i * 5, gz0 + j * 5
            if (x, z) not in ground: continue
            g = ground[(x, z)]
            b.set(x, g + 1, z, "minecraft:cobblestone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]" if (i + j) % 2 else "minecraft:mossy_stone_bricks")
            b.set(x, g + 2, z, "minecraft:stone_brick_slab[type=bottom,waterlogged=false]" if (i + j) % 2 == 0 else "minecraft:cobblestone_wall[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
            if (i + j) % 3 == 0:
                b.set(x - 1, g + 2, z, fence("dark_oak")); b.set(x + 1, g + 2, z, fence("dark_oak"))  # cross arms
            b.set(x, g, z + 1, "minecraft:coarse_dirt")
            b.set(x, g + 1, z + 1, "minecraft:cobweb" if (i * j) % 5 == 1 else AIR)
    for x in range(gy0 - 3, gy0 + 30):
        for z in (gz0 - 3, gz0 + 18):
            if (x, z) in ground: b.set(x, ground[(x, z)] + 1, z, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]")
    # ---------------- the forest: gloom trees, ghost mushrooms, cobwebs
    for _ in range(170):
        x = rnd.randint(14, L - 30); z = rnd.randint(CZ - 45, CZ + 45)
        if (x, z) not in ground or abs(z - CZ) < 4 or (gy0 - 4 <= x <= gy0 + 31 and gz0 - 4 <= z <= gz0 + 19): continue
        if 60 <= x <= 84 and CZ - 26 <= z <= CZ - 4: continue  # mansion lot
        if x < 50: continue  # castle lot
        if abs(x - 120) < 7 and abs(z - CZ) < 7: continue  # mast
        g = ground[(x, z)]
        r = rnd.random()
        if r < 0.45: gloom_tree(b, x, g + 1, z, rnd.randint(6, 11), rnd)
        elif r < 0.75: b.set(x, g + 1, z, "onepiece:ghost_mushroom")
        elif r < 0.9: b.set(x, g + 1, z, "minecraft:cobweb")
        else: b.set(x, g + 1, z, "minecraft:dead_bush")
    # ---------------- Hogback's mansion (doctor's mansion, near the middle)
    hx0, hz0, hx1, hz1 = 62, CZ - 26, 84, CZ - 6
    gbase = DECK + 1
    for x in range(hx0 - 2, hx1 + 3):
        for z in range(hz0 - 2, hz1 + 3): b.set(x, gbase - 1, z, "minecraft:polished_blackstone")
        for z in range(hz0 - 2, hz1 + 3):
            for y in range(gbase, gbase + 25): b.set(x, y, z, AIR) if (x, z) in ground else None
    b.walls(hx0, gbase, hz0, hx1, gbase + 13, hz1, CASTLE2)
    b.box(hx0 + 1, gbase, hz0 + 1, hx1 - 1, gbase + 13, hz1 - 1, AIR)
    b.box(hx0 + 1, gbase + 6, hz0 + 1, hx1 - 1, gbase + 6, hz1 - 1, "minecraft:dark_oak_planks")
    for x in range(hx0 + 2, hx1 - 1, 3):
        for (z, o, f) in ((hz0, -1, "south"), (hz1, 1, "north")):
            for y in (gbase + 2, gbase + 3, gbase + 8, gbase + 9): b.set(x, y, z, pane_of("minecraft:purple_stained_glass_pane"))
            for yb in (gbase + 1, gbase + 7):  # sill under each window, a pointed hood over it
                b.set(x, yb, z + o, stairs("minecraft:polished_blackstone_brick_stairs", f, "top"))
                b.set(x, yb + 3, z + o, slab("minecraft:polished_blackstone_brick_slab"))
    for z in range(hz0, hz1 + 1):  # floor band between the storeys
        b.set(hx0 - 1, gbase + 6, z, stairs("minecraft:polished_blackstone_brick_stairs", "east", "top"))
        b.set(hx1 + 1, gbase + 6, z, stairs("minecraft:polished_blackstone_brick_stairs", "west", "top"))
    for x in range(hx0, hx1 + 1):
        b.set(x, gbase + 6, hz0 - 1, stairs("minecraft:polished_blackstone_brick_stairs", "south", "top"))
        b.set(x, gbase + 6, hz1 + 1, stairs("minecraft:polished_blackstone_brick_stairs", "north", "top"))
    b.hip_roof(hx0, hz0, hx1, hz1, gbase + 14, ROOF_ST, ROOF, overhang=1)
    for x in range(hx0 + 4, hx1 - 3, 7):  # a pair of chimneys
        b.column(x, (hz0 + hz1) // 2 - 3, gbase + 14, gbase + 23, "minecraft:polished_blackstone_bricks")
        b.set(x, gbase + 24, (hz0 + hz1) // 2 - 3, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for (tx, tz) in ((hx0, hz0), (hx1, hz0), (hx0, hz1), (hx1, hz1)):
        b.cyl(tx, tz, 2, gbase, gbase + 18, CASTLE)
        for y in (gbase + 3, gbase + 9, gbase + 15):
            b.set(tx + (2 if tx == hx1 else -2), y, tz, "minecraft:purple_stained_glass"); b.set(tx + (2 if tx == hx1 else -2), y + 1, tz, "minecraft:purple_stained_glass")
        spire_cone(b, tx, tz, 2, gbase + 19, 10)
    dzm = (hz0 + hz1) // 2
    for z in range(dzm - 1, dzm + 2):
        for y in range(gbase, gbase + 3): b.set(hx1, y, z, AIR)
    for z in (dzm - 2, dzm + 2):  # porch: two pillars carrying a little pointed gable over the front door
        b.column(hx1 + 2, z, gbase, gbase + 3, "minecraft:polished_basalt[axis=y]")
    for x in (hx1 + 1, hx1 + 2):
        for z in range(dzm - 2, dzm + 3): b.set(x, gbase + 4, z, CASTLE2)
        b.set(x, gbase + 5, dzm - 2, stairs(ROOF_ST, "south")); b.set(x, gbase + 5, dzm + 2, stairs(ROOF_ST, "north"))
        b.set(x, gbase + 5, dzm - 1, stairs(ROOF_ST, "south")); b.set(x, gbase + 5, dzm + 1, stairs(ROOF_ST, "north"))
        b.set(x, gbase + 5, dzm, ROOF); b.set(x, gbase + 6, dzm, slab("minecraft:deepslate_tile_slab"))
    b.set(hx1 + 2, gbase + 3, dzm, "minecraft:soul_lantern[hanging=true,waterlogged=false]")
    for z in range(dzm - 1, dzm + 2): b.set(hx1 + 1, gbase - 1, z, "minecraft:polished_blackstone"); b.set(hx1 + 3, gbase - 1, z, "minecraft:polished_blackstone")
    for z in range(hz0 + 2, hz1 - 1, 3):  # the lab: operating tables, freezers, cauldrons
        b.set(hx0 + 4, gbase, z, "minecraft:white_concrete"); b.set(hx0 + 5, gbase, z, "minecraft:white_concrete")
        b.set(hx0 + 2, gbase, z, "minecraft:cauldron"); b.set(hx0 + 2, gbase + 1, z, "minecraft:brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
        b.set(hx1 - 2, gbase, z, "minecraft:blue_ice")
    for x in range(hx0 + 3, hx1 - 2, 4): b.set(x, gbase + 5, CZ - 16, "minecraft:soul_lantern[hanging=true,waterlogged=false]")
    # ---------------- the great mast with the bat-winged Jolly Roger
    MX = 120
    b.cyl(MX, CZ, 3, KEEL + 2, DECK + 95, "minecraft:dark_oak_log[axis=y]")
    for (y0, half) in ((DECK + 30, 34), (DECK + 58, 26)):
        for z in range(CZ - half - 2, CZ + half + 3): b.set(MX + 1, y0 + 22, z, "minecraft:dark_oak_log[axis=z]")
        for y in range(y0, y0 + 22):
            for z in range(CZ - half, CZ + half + 1):
                if rnd.random() < 0.86 and not (y < y0 + 4 and abs(z - CZ) % 9 < 3):  # tattered
                    b.set(MX + 2 + int(2 * math.sin((y - y0) / 22 * math.pi)), y, z, "minecraft:gray_wool" if (y + z) % 11 else "minecraft:light_gray_wool")
    # Moria's flag: a white skull crowned with two purple bat wings, flanked by pale flames (symmetric, so it
    # reads the same from both sides)
    FY = DECK + 108
    for y in range(DECK + 95, FY + 1): b.set(MX, y, CZ, fence("dark_oak"))
    FCOL = {".": "minecraft:black_wool", "W": "minecraft:white_wool", "P": "minecraft:purple_wool", "F": "minecraft:light_blue_wool"}
    for j, row in enumerate(FLAG):
        assert len(row) == 25, row
        for i, ch in enumerate(row): b.set(MX, FY - j, CZ + 1 + i, FCOL[ch])
    # ---------------- Moria's castle at the stern
    C0, C1 = 4, 46
    Z0, Z1 = CZ - 30, CZ + 30
    cb = DECK + 1
    for x in range(C0 - 2, C1 + 3):
        for z in range(Z0 - 2, Z1 + 3):
            if hull_in(x, DECK, z):
                b.set(x, cb - 1, z, "minecraft:polished_blackstone_bricks")
                for y in range(cb, cb + 12): b.set(x, y, z, AIR)
    for (y0, inset, h) in ((cb, 0, 16), (cb + 17, 6, 14), (cb + 32, 12, 12)):
        x0, x1, z0, z1 = C0 + inset, C1 - inset, Z0 + inset, Z1 - inset
        b.walls(x0, y0, z0, x1, y0 + h, z1, CASTLE)
        b.box(x0 + 1, y0, z0 + 1, x1 - 1, y0 + h - 1, z1 - 1, AIR)
        b.box(x0, y0 + h, z0, x1, y0 + h, z1, CASTLE2)
        for x in range(x0, x1 + 1, 2):
            b.set(x, y0 + h + 1, z0, CASTLE2); b.set(x, y0 + h + 1, z1, CASTLE2)
        for z in range(z0, z1 + 1, 2):
            b.set(x0, y0 + h + 1, z, CASTLE2); b.set(x1, y0 + h + 1, z, CASTLE2)
        for x in range(x0 + 3, x1 - 2, 4):
            for z in (z0, z1):
                for y in range(y0 + 3, y0 + h - 3): b.set(x, y, z, pane_of("minecraft:purple_stained_glass_pane") if y % 4 else pane_of("minecraft:black_stained_glass_pane"))
        for z in range(z0 + 3, z1 - 2, 4):
            for y in range(y0 + 3, y0 + h - 3): b.set(x1, y, z, pane_of("minecraft:purple_stained_glass_pane"))
        for x in range(x0 + 5, x1 - 3, 4):  # pilasters between the windows on the long faces
            for (z, o) in ((z0, -1), (z1, 1)):
                for y in range(y0, y0 + h): b.set(x, y, z + o, CASTLE2)
                b.set(x, y0 + h - 1, z + o + o, stairs("minecraft:polished_blackstone_brick_stairs", "south" if o < 0 else "north", "top"))
        for z in range(z0 + 5, z1 - 3, 4):  # and on the front and back faces
            for (x, o) in ((x1, 1), (x0, -1)):
                if y0 == cb and abs(z - CZ) <= 5: continue  # keep the gate clear
                for y in range(y0, y0 + h): b.set(x + o, y, z, CASTLE2)
        for (tx, tz) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
            b.cyl(tx, tz, 3, y0, y0 + h + 8, CASTLE2)
            for y in range(y0 + 4, y0 + h + 6, 5):
                for (dx, dz) in ((3, 0), (-3, 0), (0, 3), (0, -3)):
                    b.set(tx + dx, y, tz + dz, "minecraft:purple_stained_glass"); b.set(tx + dx, y + 1, tz + dz, "minecraft:purple_stained_glass")
            spire_cone(b, tx, tz, 3, y0 + h + 9, 13)
        b.stairs_up(x0 + 2, y0, z0 + 2, h, "minecraft:deepslate_brick_stairs", "south")
    # Moria's keep: a tall round tower in the middle of the top terrace, under the tallest spire
    KX = (C0 + C1) // 2
    b.cyl(KX, CZ, 6, cb + 45, cb + 58, CASTLE2)
    for y in range(cb + 47, cb + 57, 5):
        for (dx, dz) in ((6, 0), (-6, 0), (0, 6), (0, -6)):
            for k in (0, 1, 2): b.set(KX + dx, y + k, CZ + dz, "minecraft:purple_stained_glass")
    for a in range(0, 360, 20):
        t = math.radians(a)
        b.set(round(KX + 6 * math.cos(t)), cb + 58, round(CZ + 6 * math.sin(t)), "minecraft:chiseled_polished_blackstone")
    spire_cone(b, KX, CZ, 6, cb + 59, 20)
    # castle gate and Moria's throne hall (giant chair, he is 6.9 m tall)
    for z in range(CZ - 3, CZ + 4):
        for y in range(cb, cb + 8): b.set(C1, y, z, AIR)
    b.box(C0 + 3, cb, CZ - 5, C0 + 7, cb + 1, CZ + 5, "minecraft:crying_obsidian")
    b.box(C0 + 3, cb + 2, CZ - 5, C0 + 3, cb + 12, CZ + 5, "minecraft:purple_concrete")
    b.box(C0 + 4, cb + 2, CZ - 4, C0 + 7, cb + 2, CZ + 4, "minecraft:purple_wool")
    for x in range(C0 + 9, C1 - 1, 5):
        b.set(x, cb + 14, CZ, CHAIN); b.set(x, cb + 13, CZ, "minecraft:soul_lantern[hanging=true,waterlogged=false]")
        for z in (CZ - 12, CZ + 12): b.column(x, z, cb, cb + 15, "minecraft:polished_basalt[axis=y]")
    for x in range(C0 + 8, C1): b.set(x, cb, CZ, "minecraft:purple_carpet")
    b.chest(C0 + 5, cb + 2 - 2, CZ - 7, "hard", "south")
    # ---------------- the bow: the great gate that swallows ships
    # the gatehouse is built into the outer wall at the bow and its gate is a giant fanged mouth
    grnd = random.Random(5)
    for x in range(GX0, GX1 + 1):
        for z in range(CZ - GW, CZ + GW + 1):
            if (x, z) not in deck: continue
            for y in range(DECK + 1, GT + 1):
                b.set(x, y, z, "minecraft:cracked_deepslate_bricks" if grnd.random() < 0.15 else CASTLE)
            if x in (GX0, GX1) and (z + x) % 2 == 0: b.set(x, GT + 1, z, CASTLE2)  # merlons
    for z in range(CZ - GW, CZ + GW + 1):  # string course and a plinth on the sea face
        b.set(GX1 + 1, DECK + 15, z, stairs("minecraft:polished_blackstone_brick_stairs", "west", "top"))
        b.set(GX1 + 1, GT, z, CASTLE2)
    def mouth_top(dz):  # wide grin: tall in the middle, narrowing to the corners
        return DECK + 1 + int(round(12 - 6 * (abs(dz) / 10.5) ** 2))
    for dz in range(-10, 11):
        for x in range(GX0, GX1 + 1):
            for y in range(DECK + 1, mouth_top(dz) + 1): b.set(x, y, CZ + dz, AIR)
        b.set(GX1 + 1, mouth_top(dz) + 1, CZ + dz, CASTLE2)  # upper lip
        b.set(GX1 + 1, DECK, CZ + dz, CASTLE2)                 # lower lip
    for dz in (-11, 11):
        for y in range(DECK, mouth_top(10) + 2): b.set(GX1 + 1, y, CZ + dz, CASTLE2)
    # fangs hanging from the upper jaw (two big canines), teeth rising from the lower jaw at the sides
    for dz in range(-9, 10, 3):
        n = 5 if abs(dz) == 6 else 3
        for k in range(n):
            for x in (GX1, GX1 - 1):
                b.set(x, mouth_top(dz) - k, CZ + dz, BONE)
                if abs(dz) == 6 and k < 2: b.set(x, mouth_top(dz) - k, CZ + dz + (1 if dz > 0 else -1), BONE)
    for dz in (-9, -7, 7, 9):
        for k in range(2 if abs(dz) == 9 else 3):
            for x in (GX1, GX1 - 1): b.set(x, DECK + 1 + k, CZ + dz, BONE)
    # flanking towers with pointed roofs
    for side in (-1, 1):
        tz = CZ + side * (GW + 2)
        b.cyl(GX0 + 2, tz, 4, DECK - 3, GT + 5, CASTLE2)
        for y in range(DECK + 6, GT + 4, 6):
            b.set(GX0 + 6, y, tz, "minecraft:purple_stained_glass"); b.set(GX0 + 6, y + 1, tz, "minecraft:purple_stained_glass")
        spire_cone(b, GX0 + 2, tz, 4, GT + 6, 14)
    # the skull crest above the mouth, on the sea face
    sx, sy = GX1 + 1, DECK + 20
    for dz in range(-6, 7):
        for dy in range(-6, 7):
            if (dz / 6.5) ** 2 + ((dy - 1) / 6.2) ** 2 <= 1 or (abs(dz) <= 3 and -6 <= dy <= -3):
                b.set(sx, sy + dy, CZ + dz, BONE)
    for dz in (-3, -2, 2, 3):
        for dy in (0, 1, 2): b.set(sx, sy + dy, CZ + dz, "minecraft:black_concrete")
    b.set(sx, sy - 2, CZ, "minecraft:black_concrete"); b.set(sx, sy - 1, CZ, "minecraft:black_concrete")
    for dz in (-2, 0, 2): b.set(sx, sy - 5, CZ + dz, "minecraft:black_concrete")
    # fog: soul lanterns and cobwebs along the rails, purple glow
    for x in range(8, L - 16, 16):
        for z in (CZ - 30, CZ + 30):
            if (x, z) in ground: b.column(x, z, ground[(x, z)] + 1, ground[(x, z)] + 4, fence("dark_oak")); b.set(x, ground[(x, z)] + 5, z, "minecraft:soul_lantern[hanging=false,waterlogged=false]")
    # ---------------- people
    b.npc(C0 + 6, cb + 3, CZ, "moria", True)  # on the seat of his giant throne
    spots = [(95, CZ + 15), (105, CZ + 22), (115, CZ + 10), (70, CZ + 2), (150, CZ - 10), (60, CZ)]
    for (x, z) in spots:
        b.guard(x, ground.get((x, z), DECK) + 1, z, "zombie_soldier")
    # ---------------- furnished rooms
    import interiors as I
    I.furnish(b, hx0 + 1, gbase, hz0 + 1, hx1 - 1, hz1 - 1, 6, "lab", "gloom")
    mx = (hx0 + hx1) // 2
    for z in range(hz0 + 1, hz1):
        for y in range(gbase + 7, gbase + 13): b.set(mx, y, z, CASTLE2)
    for y in (gbase + 7, gbase + 8): b.set(mx, y, (hz0 + hz1) // 2, AIR)
    b.box(hx1 - 3, gbase + 6, hz0 + 2, hx1 - 2, gbase + 6, hz0 + 2, AIR)
    b.stairs_up(hx1 - 3, gbase, hz0 + 8, 6, "minecraft:dark_oak_stairs", "north", w=2)
    I.furnish(b, hx0 + 1, gbase + 7, hz0 + 1, mx - 1, hz1 - 1, 6, "bedroom", "gloom")
    I.furnish(b, mx + 1, gbase + 7, hz0 + 1, hx1 - 1, hz1 - 1, 6, "library", "gloom")
    r = I.Room(b, C0 + 1, cb, Z0 + 1, C1 - 1, Z1 - 1, 15, "gloom", random.Random(9))
    r.wall_banners(4, 4); r.paintings(6); r.plants(6); r.lights(6)
    for (y0, inset, h, kinds) in ((cb + 17, 6, 14, ("dining", "bedroom")), (cb + 32, 12, 12, ("library", "treasure"))):
        x0, x1, z0, z1 = C0 + inset, C1 - inset, Z0 + inset, Z1 - inset
        for x in range(x0 + 1, x1):
            for y in range(y0, y0 + h): b.set(x, y, CZ, CASTLE)
        for x in ((x0 + x1) // 2, (x0 + x1) // 2 + 1):
            for y in (y0, y0 + 1, y0 + 2): b.set(x, y, CZ, AIR)
        I.furnish(b, x0 + 1, y0, z0 + 1, x1 - 1, CZ - 1, h - 1, kinds[0], "gloom")
        I.furnish(b, x0 + 1, y0, CZ + 1, x1 - 1, z1 - 1, h - 1, kinds[1], "gloom")
    return b, 0
