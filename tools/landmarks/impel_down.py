"""Impel Down, the great underwater prison in the Calm Belt. Above the sea: a round fortress wall of seastone and
the central tower with the Marine flag, the guarded sea gate and the inner harbour. Below the sea, six levels
going down, each a ring of barred cells round a themed hell, linked by the central shaft:
Lv1 Crimson Hell (a forest of blade-leaved red trees), Lv2 Wild Beast Hell (beast cages and bones), Lv3
Starvation Hell (scorching sand and dry wells), Lv4 Blazing Hell (the great boiling lava cauldron and the warden's
office), Lv5 Freezing Hell (snow, ice and frozen prisoners) with the hidden Newkama Land behind a secret door,
and Lv6 Eternal Hell (black, silent, the worst criminals of all). ~84 x 84, 60 deep.
Canvas y 0 = sea surface (or the ground on a beach)."""
import math, random
from canvas import *
import interiors as I

SID = "impel_down"
TITLE = "Impel Down"
CUTS = [2, -10, -28, -46, -55]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="none")

N = 84
CX, CZ = 42, 42
R = 34
SEA = "onepiece:seastone_bricks"
WALL = "minecraft:polished_deepslate"
BARS = "onepiece:prison_bars"
JAIL = dict(wood="dark_oak", rug="gray", rug2="black", bed="gray", light="minecraft:lantern", accent="onepiece:seastone_block",
            banner="blue", candle="white")
NEWK = dict(wood="cherry", rug="pink", rug2="purple", bed="pink", light="minecraft:pearlescent_froglight[axis=y]", accent="minecraft:gold_block",
            banner="pink", candle="pink")
LEVELS = [  # floor, wall, theme name
    ("minecraft:crimson_nylium", "minecraft:red_nether_bricks", "crimson"),
    ("minecraft:moss_block", "minecraft:mossy_stone_bricks", "beast"),
    ("minecraft:sand", "minecraft:smooth_sandstone", "starve"),
    ("minecraft:blackstone", "minecraft:polished_blackstone_bricks", "blaze"),
    ("minecraft:snow_block", "minecraft:packed_ice", "freeze"),
    ("minecraft:obsidian", "minecraft:obsidian", "eternal"),
]


def floor_y(k):
    return -6 - 9 * (k + 1)


def ring(x, z):
    return math.hypot(x - CX, z - CZ)


def build():
    rnd = random.Random(511)
    b = B()
    bottom = floor_y(5) - 1
    # ---------------- the prison body: a seastone drum from the sea floor to the surface
    for y in range(bottom, 1):
        b.cyl(CX, CZ, R, y, y, SEA if (y // 3) % 3 else WALL)
        b.cyl(CX, CZ, R - 2, y, y, AIR)
    b.cyl(CX, CZ, R - 2, 0, 0, "minecraft:polished_andesite")
    # ---------------- the six levels
    for k, (fl, wl, theme) in enumerate(LEVELS):
        y0 = floor_y(k)
        b.cyl(CX, CZ, R - 2, y0, y0, fl if theme not in ("starve",) else "minecraft:smooth_sandstone")
        b.cyl(CX, CZ, R - 2, y0 + 8, y0 + 8, WALL)
        b.cyl(CX, CZ, R - 1.5, y0 + 1, y0 + 7, wl, hollow=True)
        # the ring of cells against the outer wall, bars facing in
        for x in range(CX - R, CX + R + 1):
            for z in range(CZ - R, CZ + R + 1):
                d = ring(x, z)
                if not (R - 9 <= d < R - 2): continue
                a = math.degrees(math.atan2(z - CZ, x - CX)) % 360
                seg = a % 15
                arc = min(seg, 15 - seg) * math.pi / 180 * d
                for y in range(y0 + 1, y0 + 5):
                    if d < R - 8: b.set(x, y, z, BARS if arc > 0.6 else wl)
                    elif arc < 0.6: b.set(x, y, z, wl)
                b.set(x, y0 + 5, z, wl)
        for s in range(24):  # cell furnishings: a bunk, a bucket, chains, sometimes a skull
            a = math.radians(s * 15 + 7.5)
            px, pz = round(CX + (R - 4) * math.cos(a)), round(CZ + (R - 4) * math.sin(a))
            b.set(px, y0 + 1, pz, "minecraft:gray_carpet" if theme != "eternal" else "minecraft:black_carpet")
            qx, qz = round(CX + (R - 3) * math.cos(a)), round(CZ + (R - 3) * math.sin(a))
            b.set(qx, y0 + 4, qz, "minecraft:iron_chain[axis=y]")
            b.set(qx, y0 + 1, qz, rnd.choice(("minecraft:cauldron", "minecraft:skeleton_skull[rotation=0]", "minecraft:cobweb", "minecraft:barrel[facing=up,open=false]")))
        # the corridor round the cells, lit
        for s in range(0, 360, 20):
            a = math.radians(s)
            b.set(round(CX + (R - 10) * math.cos(a)), y0 + 7, round(CZ + (R - 10) * math.sin(a)), lantern(True) if theme != "eternal" else lantern(True, soul=True))
        # ---------------- the hell in the middle
        core = R - 12
        if theme == "crimson":  # blade forest
            for i in range(26):
                a = rnd.uniform(0, 2 * math.pi); d = rnd.uniform(5, core - 1)
                x, z = round(CX + d * math.cos(a)), round(CZ + d * math.sin(a))
                for y in range(y0 + 1, y0 + 5): b.set(x, y, z, "minecraft:crimson_stem[axis=y]")
                for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                    b.set(x + dx, y0 + 5, z + dz, "minecraft:nether_wart_block")
                    b.set(x + dx, y0 + 4, z + dz, "minecraft:pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]")
                b.set(x, y0 + 6, z, "minecraft:shroomlight")
            for x in range(CX - core, CX + core + 1):  # the grass of Crimson Hell is sharp as needles
                for z in range(CZ - core, CZ + core + 1):
                    if 4 < ring(x, z) < core and b.get(x, y0 + 1, z) in (None, AIR) and rnd.random() < 0.45:
                        b.set(x, y0 + 1, z, "minecraft:crimson_roots")
        elif theme == "beast":
            for (dx, dz) in ((-12, -6), (12, -6), (-12, 8), (12, 8), (0, 14)):
                x, z = CX + dx, CZ + dz
                b.walls(x - 3, y0 + 1, z - 3, x + 3, y0 + 5, z + 3, "minecraft:iron_bars[east=true,north=true,south=true,west=true,waterlogged=false]")
                b.box(x - 3, y0 + 6, z - 3, x + 3, y0 + 6, z + 3, "minecraft:iron_block")
                b.set(x, y0 + 1, z, "minecraft:bone_block[axis=x]"); b.set(x + 1, y0 + 1, z, "minecraft:hay_block[axis=y]")
            b.bones(CX - 8, y0 + 1, CZ - 14, 14, axis="x", height=4)
        elif theme == "starve":
            for i in range(40):
                x, z = CX + rnd.randint(-core, core), CZ + rnd.randint(-core, core)
                if ring(x, z) < core and ring(x, z) > 5:
                    b.set(x, y0, z, "minecraft:magma_block" if i % 3 == 0 else "minecraft:sand")
                    if i % 4 == 0: b.set(x, y0 + 1, z, "minecraft:dead_bush")
            for (dx, dz) in ((-10, 0), (10, 0)):  # dry wells
                b.cyl(CX + dx, CZ + dz, 2, y0 + 1, y0 + 1, "minecraft:cobblestone_wall", hollow=True)
        elif theme == "blaze":  # the boiling cauldron
            b.cyl(CX, CZ + 12, 6, y0, y0 + 2, "minecraft:iron_block", hollow=True)
            b.cyl(CX, CZ + 12, 5, y0, y0 + 1, "minecraft:lava[level=0]")
            b.cyl(CX, CZ + 12, 6.5, y0 - 1, y0 - 1, "minecraft:magma_block")
            for i in range(20):
                x, z = CX + rnd.randint(-core, core), CZ + rnd.randint(-core, core)
                if 6 < ring(x, z) < core and abs(z - CZ - 12) > 7: b.set(x, y0, z, "minecraft:magma_block")
            # the warden's office
            b.walls(CX - 14, y0 + 1, CZ - 14, CX - 4, y0 + 6, CZ - 6, "minecraft:polished_blackstone_bricks")
            b.box(CX - 13, y0 + 1, CZ - 13, CX - 5, y0 + 6, CZ - 7, AIR)
            b.set(CX - 9, y0 + 1, CZ - 6, AIR); b.set(CX - 9, y0 + 2, CZ - 6, AIR)
            I.furnish(b, CX - 13, y0 + 1, CZ - 13, CX - 5, CZ - 7, 5, "study", "justice", seed=k)
        elif theme == "freeze":
            for i in range(14):
                a = rnd.uniform(0, 2 * math.pi); d = rnd.uniform(6, core - 1)
                x, z = round(CX + d * math.cos(a)), round(CZ + d * math.sin(a))
                if i % 2:  # a dead spruce frozen stiff, snow on its branches
                    for y in range(y0 + 1, y0 + 6): b.set(x, y, z, "minecraft:spruce_log[axis=y]")
                    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        b.set(x + dx, y0 + 4, z + dz, leaves("spruce")); b.set(x + dx, y0 + 5, z + dz, "minecraft:snow_block")
                        b.set(x + 2 * dx, y0 + 3, z + 2 * dz, "minecraft:spruce_log[axis=x]" if dx else "minecraft:spruce_log[axis=z]") if (i + dx + dz) % 3 == 0 else None
                    b.set(x, y0 + 6, z, "minecraft:snow_block"); b.set(x, y0 + 7, z, "minecraft:snow[layers=2]")
                    continue
                h = rnd.randint(2, 6)
                for y in range(y0 + 1, y0 + 1 + h): b.set(x, y, z, "minecraft:packed_ice" if y < y0 + h else "minecraft:blue_ice")
            for i in range(60):
                x, z = CX + rnd.randint(-core, core), CZ + rnd.randint(-core, core)
                if 4 < ring(x, z) < core and b.get(x, y0 + 1, z) in (None, AIR): b.set(x, y0 + 1, z, "minecraft:snow[layers=2]")
            # Newkama Land, hidden in a sealed vault reached through a secret trapdoor
            nx0, nz0, nx1, nz1 = CX + 4, CZ - 17, CX + 17, CZ - 5
            b.walls(nx0, y0 + 1, nz0, nx1, y0 + 7, nz1, "minecraft:packed_ice")
            b.box(nx0 + 1, y0 + 1, nz0 + 1, nx1 - 1, y0 + 7, nz1 - 1, AIR)
            b.box(nx0 + 1, y0, nz0 + 1, nx1 - 1, y0, nz1 - 1, "minecraft:pink_concrete")
            I.furnish(b, nx0 + 1, y0 + 1, nz0 + 1, nx1 - 1, nz1 - 1, 6, "tavern", NEWK, seed=55)
            b.set(nx0 + 6, y0 + 1, nz1, AIR); b.set(nx0 + 6, y0 + 2, nz1, "minecraft:packed_ice")  # a crawl hole
            b.chest(nx1 - 2, y0 + 1, nz0 + 2, "newkama", "west")
        elif theme == "eternal":
            for i in range(30):
                x, z = CX + rnd.randint(-core, core), CZ + rnd.randint(-core, core)
                if 4 < ring(x, z) < core: b.set(x, y0, z, "minecraft:crying_obsidian")
            for s in range(0, 360, 45):
                a = math.radians(s)
                b.column(round(CX + 12 * math.cos(a)), round(CZ + 12 * math.sin(a)), y0 + 1, y0 + 7, "minecraft:obsidian")
        # a guard post on every level
        gx0, gz0 = CX - 16 if theme != "blaze" else CX + 6, CZ + 4
        if theme not in ("freeze",) or True:
            b.walls(gx0, y0 + 1, gz0, gx0 + 8, y0 + 5, gz0 + 7, WALL)
            b.box(gx0 + 1, y0 + 1, gz0 + 1, gx0 + 7, y0 + 5, gz0 + 6, AIR)
            for y in (y0 + 1, y0 + 2): b.set(gx0 + 4, y, gz0, AIR)
            b.set(gx0 + 2, y0 + 3, gz0, "minecraft:glass_pane"); b.set(gx0 + 6, y0 + 3, gz0, "minecraft:glass_pane")
            I.furnish(b, gx0 + 1, y0 + 1, gz0 + 1, gx0 + 7, gz0 + 6, 4, ("barracks", "armory", "kitchen", "barracks", "armory", "storage")[k], JAIL, seed=100 + k)
    # ---------------- the central shaft: a ladder well through every level up into the tower
    for y in range(bottom + 1, 30):
        b.cyl(CX, CZ, 3, y, y, "onepiece:seastone_bricks", hollow=True)
        b.cyl(CX, CZ, 2, y, y, AIR)
        b.set(CX, y, CZ - 2, "minecraft:ladder[facing=south,waterlogged=false]")
    for k in range(6):
        y0 = floor_y(k)
        for y in (y0 + 1, y0 + 2, y0 + 3):
            for dx in (-1, 0, 1): b.set(CX + dx, y, CZ + 3, AIR)
        b.set(CX, y0 + 4, CZ + 3, "minecraft:iron_trapdoor[facing=south,half=top,open=true,powered=false,waterlogged=false]")
    # ---------------- above the sea: courtyard, outer wall, sea gate, harbour and the great tower
    for y in range(1, 13):
        b.cyl(CX, CZ, R, y, y, SEA, hollow=True); b.cyl(CX, CZ, R - 1, y, y, SEA, hollow=True)
    for a in range(0, 360, 4):
        t = math.radians(a)
        b.set(round(CX + R * math.cos(t)), 13, round(CZ + R * math.sin(t)), "minecraft:deepslate_brick_wall")
    def gateway(a): return abs((a - 90 + 180) % 360 - 180) < 13
    for a10 in range(0, 3600, 5):  # a corbelled parapet round the wall top, merlons every few blocks
        a = a10 / 10; t = math.radians(a)
        x, z = round(CX + (R + 1) * math.cos(t)), round(CZ + (R + 1) * math.sin(t))
        b.set(x, 12, z, WALL); b.set(x, 11, z, "minecraft:polished_deepslate_slab[type=top,waterlogged=false]") if b.get(x, 11, z) is None else None
        if int(a // 3) % 2: b.set(x, 13, z, WALL)
    for a in range(0, 360, 12):  # buttresses: deepslate piers standing proud of the seastone
        if gateway(a): continue
        t = math.radians(a)
        for dr in (1, 2):
            x, z = round(CX + (R + dr) * math.cos(t)), round(CZ + (R + dr) * math.sin(t))
            for y in range(1, 12 - 2 * (dr - 1)): b.set(x, y, z, WALL)
            b.set(x, 12 - 2 * (dr - 1), z, "minecraft:polished_deepslate_slab[type=bottom,waterlogged=false]") if dr == 2 else None
        for y in (4, 8):  # arrow slits between the piers
            t2 = math.radians(a + 6)
            b.set(round(CX + R * math.cos(t2)), y, round(CZ + R * math.sin(t2)), "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
            b.set(round(CX + R * math.cos(t2)), y + 1, round(CZ + R * math.sin(t2)), "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
    for a in range(0, 360, 45):  # turrets (none in the gateway: the gatehouse stands there)
        if gateway(a): continue
        t = math.radians(a)
        tx, tz = round(CX + R * math.cos(t)), round(CZ + R * math.sin(t))
        b.cyl(tx, tz, 3, 1, 17, SEA); b.cyl(tx, tz, 3.5, 18, 18, "minecraft:polished_deepslate")
        for a2 in range(0, 360, 30):
            t2 = math.radians(a2)
            b.set(round(tx + 3.5 * math.cos(t2)), 19, round(tz + 3.5 * math.sin(t2)), WALL)
        for y in (6, 12):
            for (dx, dz) in ((3, 0), (-3, 0), (0, 3), (0, -3)): b.set(tx + dx, y, tz + dz, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
        b.set(tx, 19, tz, lantern())
    # the gatehouse over the sea gate: two round towers flanking the channel, a lintel and a portcullis
    for sx in (-1, 1):
        gx, gz = CX + sx * 9, CZ + R - 1
        b.cyl(gx, gz, 3.5, 1, 21, SEA); b.cyl(gx, gz, 4, 22, 22, WALL)
        for y in range(2, 22, 5): b.cyl(gx, gz, 3.5, y, y, WALL)
        for a2 in range(0, 360, 30):
            t2 = math.radians(a2)
            b.set(round(gx + 4 * math.cos(t2)), 23, round(gz + 4 * math.sin(t2)), WALL)
        for y in (8, 9, 15, 16): b.set(gx, y, gz + 3, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
        b.set(gx, 23, gz, lantern())
    # the sea gate (south) and the inner harbour basin
    hx0, hx1, hz0 = CX - 6, CX + 6, CZ + 14
    for x in range(hx0, hx1 + 1):
        for z in range(hz0, CZ + R + 1):
            for y in range(-5, 1): b.set(x, y, z, WATER if ring(x, z) <= R + 0.5 else None) if ring(x, z) <= R else None
            b.set(x, -6, z, SEA)
        for y in range(1, 11):
            for z in range(CZ + R - 3, CZ + R + 1): b.set(x, y, z, AIR if abs(x - CX) < 5 else SEA)
    for z in range(hz0, CZ + R - 1):
        for x in (hx0 - 1, hx1 + 1):
            for y in range(-6, 1): b.set(x, y, z, SEA)
    for x in range(hx0 - 1, hx1 + 2):  # the basin's inner end wall (without it the harbour poured into the prison below)
        for y in range(-6, 1): b.set(x, y, hz0 - 1, SEA)
    for x in range(CX - 6, CX + 7):  # the lintel over the gateway, and the raised portcullis of prison bars
        for z in range(CZ + R - 3, CZ + R + 2):
            for y in (11, 12, 13): b.set(x, y, z, WALL if y == 11 or z in (CZ + R - 3, CZ + R + 1) else SEA)
        b.set(x, 14, CZ + R + 1, WALL if x % 2 else AIR); b.set(x, 14, CZ + R - 3, WALL if x % 2 else AIR)
    for x in range(CX - 4, CX + 5):
        for y in (9, 10): b.set(x, y, CZ + R - 1, BARS)
    for x in range(hx0, hx1 + 1): b.set(x, 1, hz0 - 1, "minecraft:polished_andesite_slab[type=bottom,waterlogged=false]")
    for (x, z) in ((hx0 - 3, hz0 + 4), (hx1 + 3, hz0 + 4)): b.set(x, 1, z, "minecraft:spruce_fence")
    # the great tower over the shaft
    TR = 9
    for y in range(1, 46):
        b.cyl(CX, CZ, TR - (1 if y > 36 else 0), y, y, WALL if (y // 4) % 2 else SEA, hollow=True)
    b.cyl(CX, CZ, TR - 1, 1, 45, AIR); b.cyl(CX, CZ, TR - 1, 0, 0, "minecraft:polished_andesite")
    for y in range(1, 30): b.cyl(CX, CZ, 3, y, y, "onepiece:seastone_bricks", hollow=True); b.cyl(CX, CZ, 2, y, y, AIR); b.set(CX, y, CZ - 2, "minecraft:ladder[facing=south,waterlogged=false]")
    for fy in (10, 20, 30):
        b.cyl(CX, CZ, TR - 1, fy, fy, "minecraft:dark_oak_planks"); b.cyl(CX, CZ, 2, fy, fy, AIR)
        for dx in (-1, 0, 1):
            for y in (fy + 1, fy + 2, fy + 3): b.set(CX + dx, y, CZ + 3, AIR) if fy < 30 else None
    for y in (1, 2, 3):
        for dx in (-1, 0, 1): b.set(CX + dx, y, CZ + 3, AIR); b.set(CX + dx, y, CZ + TR, AIR)
    for y in range(5, 44, 5):
        for a in (0, 90, 180, 270):
            t = math.radians(a + 45)
            b.set(round(CX + TR * math.cos(t)), y, round(CZ + TR * math.sin(t)), "minecraft:light_blue_stained_glass_pane")
    for a in range(0, 360, 45):  # ribs up the tower between the windows
        t = math.radians(a)
        for y in range(4 if a == 90 else 1, 46):
            rr = TR + 1 if y <= 36 else TR   # the tower steps in above y 36
            b.set(round(CX + rr * math.cos(t)), y, round(CZ + rr * math.sin(t)), WALL)
    for (y0, kinds) in ((1, ("hall",)), (11, ("study",)), (21, ("library",))):
        I.furnish(b, CX - 6, y0, CZ + 4, CX + 6, CZ + 6, 7, kinds[0], JAIL, seed=y0)
    b.cyl(CX, CZ, TR + 1, 46, 46, "minecraft:polished_deepslate")
    for a in range(0, 360, 10):
        t = math.radians(a)
        b.set(round(CX + (TR + 1) * math.cos(t)), 47, round(CZ + (TR + 1) * math.sin(t)), "minecraft:deepslate_brick_wall")
    b.column(CX + 4, CZ, 47, 56, "minecraft:white_concrete")
    b.box(CX + 5, 52, CZ, CX + 10, 56, CZ, "minecraft:white_wool"); b.box(CX + 6, 53, CZ, CX + 9, 55, CZ, "minecraft:blue_wool")
    # the jailers' barracks and the armoury in the courtyard
    for (bx0, kind) in ((CX - 25, "barracks"), (CX + 13, "armory")):
        b.walls(bx0, 1, CZ - 22, bx0 + 12, 7, CZ - 12, WALL); b.box(bx0 + 1, 1, CZ - 21, bx0 + 11, 7, CZ - 13, AIR)
        b.box(bx0, 8, CZ - 22, bx0 + 12, 8, CZ - 12, SEA)
        for x in range(bx0, bx0 + 13, 2): b.set(x, 9, CZ - 22, "minecraft:deepslate_brick_wall"); b.set(x, 9, CZ - 12, "minecraft:deepslate_brick_wall")
        for y in (1, 2, 3): b.set(bx0 + 6, y, CZ - 12, AIR)
        for x in (bx0 + 3, bx0 + 9): b.set(x, 4, CZ - 12, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]")
        I.furnish(b, bx0 + 1, 1, CZ - 21, bx0 + 11, CZ - 13, 6, kind, JAIL, seed=bx0)
    for x in range(CX - 28, CX + 29, 7):
        if abs(x - CX) > 10: b.set(x, 1, CZ + 8, "minecraft:polished_deepslate_wall"); b.set(x, 2, CZ + 8, lantern())
    # ---------------- loot, jailers and the guard
    b.chest(CX - 10, floor_y(0) + 1, CZ - 14, "impel_down", "east")
    b.chest(CX + 8, floor_y(2) + 1, CZ + 8, "hard", "west")
    b.chest(CX - 12, floor_y(3) + 1, CZ - 12, "impel_down", "east")
    b.chest(CX - 4, floor_y(5) + 1, CZ - 10, "eternal_hell", "south")
    b.chest(CX + 4, floor_y(5) + 1, CZ - 10, "legendary", "south")
    for k in range(6):
        y0 = floor_y(k)
        kit = ("jailer", "war_beast", "jailer", "warden_jailer", "warden_jailer", "warden_jailer")[k]
        b.guards(kit, ((CX + 22, CZ), (CX - 22, CZ), (CX, CZ + 22), (CX, CZ - 22))[:2 + k // 2], y=y0 + 1)
    b.guards("pacifista", ((CX + 10, CZ + 10),), y=floor_y(5) + 1)
    b.guards("jailer", ((CX - 4, hz0 - 3), (CX + 4, hz0 - 3)), y=1)
    return b, 0
