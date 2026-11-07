"""King's Flame Fortress: the stronghold of King the Wildfire, Kaido's right hand. A black basalt fortress on a burnt
plain split by lava rivers. A lava moat and drawbridge, a curtain wall with braziers and four flame-crowned towers,
a courtyard with the war-beast pens, the forge and the barracks, and the black-and-red keep with Wano roofs: four
floors of furnished rooms up to King's war room, with a great stone pteranodon spreading its burning wings over
the top. ~96 x 96. Ground = y 0."""
import math, random
from canvas import *
import interiors as I

SID = "flame_fortress"
TITLE = "King's Flame Fortress"
CUTS = [3, 16]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 96
CX, CZ = 48, 46
SCORCH = "onepiece:scorched_stone"
SCORCH_W = "onepiece:scorched_stone_wall"
BASALT = "minecraft:polished_basalt[axis=y]"
BLACK = "minecraft:polished_blackstone_bricks"
ROOF = "onepiece:wano_roof_tiles"
ROOF_ST = "onepiece:wano_roof_tile_stairs"
LAVA = "minecraft:lava[level=0]"
FIRE = dict(wood="crimson", rug="red", rug2="black", bed="red", light="minecraft:lantern", accent="minecraft:gilded_blackstone",
            banner="red", candle="red")
KAIDO = I.THEMES["kaido"]
W0, W1 = CX - 30, CX + 30      # curtain wall square
Z0w, Z1w = CZ - 30, CZ + 30
KX0, KX1, KZ0, KZ1 = CX - 13, CX + 13, CZ - 22, CZ + 2   # the keep
FLOORS = (1, 9, 17, 25)
KTOP = 33


def brazier(b, x, y, z):
    b.set(x, y, z, "minecraft:chiseled_polished_blackstone"); b.set(x, y + 1, z, "minecraft:magma_block"); b.set(x, y + 2, z, "minecraft:fire")


def tower(b, cx, cz, r, h):
    b.cyl(cx, cz, r, 1, h, BLACK, hollow=True)
    b.cyl(cx, cz, r - 1, 0, 0, SCORCH)
    for f in range(8, h, 8): b.cyl(cx, cz, r - 1, f, f, "minecraft:crimson_planks")
    for y in range(1, h + 1): b.set(cx, y, cz - r + 1, "minecraft:ladder[facing=south,waterlogged=false]")
    for y in range(5, h, 8):
        for (dx, dz) in ((r, 0), (-r, 0), (0, r), (0, -r)): b.set(cx + dx, y, cz + dz, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
    b.cyl(cx, cz, r + 1, h + 1, h + 1, SCORCH)
    for a in range(0, 360, 30):
        t = math.radians(a); b.set(round(cx + (r + 1) * math.cos(t)), h + 2, round(cz + (r + 1) * math.sin(t)), SCORCH_W if a % 60 else SCORCH)
    b.cyl(cx, cz, 1.5, h + 1, h + 1, "minecraft:magma_block")
    for (dx, dz) in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)): b.set(cx + dx, h + 2, cz + dz, "minecraft:fire")
    b.set(cx, h + 1, cz - r + 1, AIR)


def build():
    rnd = random.Random(53)
    b = B()
    # ---------------- burnt plain, lava rivers, ash
    for x in range(N):
        for z in range(N):
            for y in (-4, -3, -2, -1): b.set(x, y, z, "minecraft:blackstone")
            r = rnd.random()
            b.set(x, 0, z, "minecraft:basalt[axis=y]" if r < 0.3 else ("minecraft:blackstone" if r < 0.6 else ("minecraft:magma_block" if r < 0.63 else "minecraft:coarse_dirt")))
            river = abs((x - 10) - 0.4 * (z - 0) - 8 * math.sin(z * 0.1)) < 1.6 or abs((z - 80) + 0.3 * (x - 50) + 6 * math.sin(x * 0.13)) < 1.4
            if river and not (W0 - 6 <= x <= W1 + 6 and Z0w - 6 <= z <= Z1w + 6):
                b.set(x, 0, z, LAVA); b.set(x, -1, z, "minecraft:magma_block")
            elif r > 0.97 and not (W0 - 6 <= x <= W1 + 6 and Z0w - 6 <= z <= Z1w + 6):  # dead trees and basalt spikes
                if rnd.random() < 0.5:
                    for y in range(1, rnd.randint(3, 7)): b.set(x, y, z, "minecraft:basalt[axis=y]")
                else:
                    for y in range(1, 5): b.set(x, y, z, "minecraft:stripped_dark_oak_log[axis=y]")
                    b.set(x + 1, 4, z, "minecraft:stripped_dark_oak_log[axis=x]")
    # ---------------- lava moat around the curtain wall, drawbridge on the south
    for x in range(W0 - 5, W1 + 6):
        for z in range(Z0w - 5, Z1w + 6):
            if not (W0 - 1 <= x <= W1 + 1 and Z0w - 1 <= z <= Z1w + 1):
                if not (W0 - 3 <= x <= W1 + 3 and Z0w - 3 <= z <= Z1w + 3):
                    b.set(x, 0, z, "minecraft:polished_blackstone"); continue
                b.set(x, 0, z, LAVA); b.set(x, -1, z, LAVA); b.set(x, -2, z, "minecraft:magma_block")
    for z in range(Z1w - 1, Z1w + 6):
        for x in range(CX - 3, CX + 4): b.set(x, 1, z, "minecraft:crimson_planks" if abs(x - CX) < 3 else "minecraft:crimson_log[axis=z]") if z > Z1w else None
    for x in (CX - 4, CX + 4):
        for k in range(6): b.set(x, 2 + k, Z1w + 1 + k // 2, "minecraft:iron_chain[axis=y]") if False else b.set(x, 2 + k, Z1w + 1, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
    # ---------------- curtain wall, walkway, braziers, the gatehouse
    WH = 14
    for x in range(W0, W1 + 1):
        for z in range(Z0w, Z1w + 1):
            if x in (W0, W0 + 1, W1 - 1, W1) or z in (Z0w, Z0w + 1, Z1w - 1, Z1w):
                for y in range(0, WH + 1): b.set(x, y, z, BLACK if y % 5 else SCORCH)
                outer = x in (W0, W1) or z in (Z0w, Z1w)
                if outer and (x + z) % 2 == 0: b.set(x, WH + 1, z, SCORCH)
                elif outer: b.set(x, WH + 1, z, SCORCH_W)
                if outer and (x + z) % 12 == 0: brazier(b, x, WH + 1, z)
    for x in range(W0 + 2, W1 - 1):  # walkway on the inside of the wall
        for z in (Z0w + 2, Z1w - 2): b.set(x, WH, z, "minecraft:polished_blackstone_slab[type=top,waterlogged=false]")
    for z in range(Z0w + 2, Z1w - 1):
        for x in (W0 + 2, W1 - 2): b.set(x, WH, z, "minecraft:polished_blackstone_slab[type=top,waterlogged=false]")
    for x in range(CX - 3, CX + 4):  # gate tunnel
        for z in range(Z1w - 2, Z1w + 1):
            for y in range(1, 8): b.set(x, y, z, AIR)
            b.set(x, 0, z, "minecraft:polished_blackstone")
    for x in range(CX - 3, CX + 4): b.set(x, 7, Z1w, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]")
    for x in (CX - 6, CX + 6): tower(b, x, Z1w, 3, WH + 8)
    b.pagoda_roof(CX, Z1w, 8, 4, WH + 2, ROOF_ST, ROOF, layers=2)
    for i in range(WH - 1):  # stairs up to the wall walk inside the gate
        for w in (0, 1): b.set(CX - 10 - i, 1 + i, Z1w - 3 - w, stairs("minecraft:polished_blackstone_brick_stairs", "west"))
    for (tx, tz) in ((W0, Z0w), (W1, Z0w), (W0, Z1w), (W1, Z1w)): tower(b, tx, tz, 5, WH + 14)
    # Kaido banners hanging off the wall
    for x in range(W0 + 6, W1 - 5, 8):
        for y in range(WH - 6, WH): b.set(x, y, Z1w + 1, "minecraft:purple_wool" if y > WH - 3 else "minecraft:black_wool")
    # ---------------- courtyard: war-beast pens, the forge, barracks
    for x in range(W0 + 2, W1 - 1):
        for z in range(Z0w + 2, Z1w - 1):
            b.set(x, 0, z, "minecraft:polished_blackstone" if (x + z) % 4 else "minecraft:blackstone")
    for z in range(KZ1, Z1w - 1):
        for x in range(CX - 2, CX + 3): b.set(x, 0, z, SCORCH)
    for i, px in enumerate(range(W0 + 4, W0 + 22, 6)):  # pens with iron bars
        b.walls(px, 1, Z1w - 14, px + 5, 5, Z1w - 4, "minecraft:iron_bars[east=true,north=true,south=true,west=true,waterlogged=false]")
        b.box(px + 1, 1, Z1w - 13, px + 4, 4, Z1w - 5, AIR)
        b.box(px, 6, Z1w - 14, px + 5, 6, Z1w - 4, "minecraft:dark_oak_planks")
        b.set(px + 2, 1, Z1w - 8, "minecraft:hay_block[axis=y]"); b.set(px + 3, 1, Z1w - 12, "minecraft:bone_block[axis=y]")
        b.set(px + 2, 1, Z1w - 4, AIR); b.set(px + 2, 2, Z1w - 4, AIR)
    # forge
    fx0, fz0 = CX + 16, Z1w - 16
    b.box(fx0, 0, fz0, fx0 + 11, 0, fz0 + 11, SCORCH)
    b.walls(fx0, 1, fz0, fx0 + 11, 6, fz0 + 11, BLACK); b.box(fx0 + 1, 1, fz0 + 1, fx0 + 10, 6, fz0 + 10, AIR)
    b.hip_roof(fx0 - 1, fz0 - 1, fx0 + 12, fz0 + 12, 7, ROOF_ST, ROOF)
    for x in (fx0 + 5, fx0 + 6):
        for y in (1, 2, 3): b.set(x, y, fz0, AIR)
    I.furnish(b, fx0 + 1, 1, fz0 + 1, fx0 + 10, fz0 + 10, 5, "workshop", FIRE)
    b.set(fx0 + 2, 1, fz0 + 9, "onepiece:swordsmith_forge"); b.set(fx0 + 4, 1, fz0 + 9, "minecraft:blast_furnace[facing=north,lit=true]")
    b.set(fx0 + 6, 1, fz0 + 9, "minecraft:lava_cauldron"); b.set(fx0 + 8, 1, fz0 + 9, "minecraft:anvil[facing=north]")
    for y in range(7, 12): b.set(fx0 + 2, y, fz0 + 9, "minecraft:polished_blackstone_bricks")
    b.set(fx0 + 2, 12, fz0 + 9, "minecraft:campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
    # barracks along the west wall
    bx0, bz0 = W0 + 3, Z0w + 4
    b.box(bx0, 0, bz0, bx0 + 9, 0, bz0 + 28, SCORCH)
    b.walls(bx0, 1, bz0, bx0 + 9, 6, bz0 + 28, BLACK); b.box(bx0 + 1, 1, bz0 + 1, bx0 + 8, 6, bz0 + 27, AIR)
    for z in (bz0 + 9, bz0 + 19):
        for x in range(bx0 + 1, bx0 + 9):
            for y in range(1, 6): b.set(x, y, z, BLACK)
        for y in (1, 2, 3): b.set(bx0 + 8, y, z, AIR) if False else b.set(bx0 + 4, y, z, AIR)
    b.hip_roof(bx0 - 1, bz0 - 1, bx0 + 10, bz0 + 29, 7, ROOF_ST, ROOF)
    for y in (1, 2, 3): b.set(bx0 + 9, y, bz0 + 4, AIR); b.set(bx0 + 9, y, bz0 + 24, AIR)
    I.furnish(b, bx0 + 1, 1, bz0 + 1, bx0 + 8, bz0 + 8, 5, "barracks", KAIDO)
    I.furnish(b, bx0 + 1, 1, bz0 + 10, bx0 + 8, bz0 + 18, 5, "kitchen", KAIDO)
    I.furnish(b, bx0 + 1, 1, bz0 + 20, bx0 + 8, bz0 + 27, 5, "barracks", KAIDO)
    # ---------------- the keep: four floors with Wano roofs
    b.box(KX0, 0, KZ0, KX1, 0, KZ1, SCORCH)
    b.walls(KX0, 1, KZ0, KX1, KTOP, KZ1, BLACK)
    b.box(KX0 + 1, 1, KZ0 + 1, KX1 - 1, KTOP, KZ1 - 1, AIR)
    for f in FLOORS[1:]: b.box(KX0 + 1, f - 1, KZ0 + 1, KX1 - 1, f - 1, KZ1 - 1, "minecraft:crimson_planks")
    b.box(KX0 + 1, KTOP, KZ0 + 1, KX1 - 1, KTOP, KZ1 - 1, BLACK)
    for f in FLOORS:
        for x in range(KX0 + 3, KX1 - 2, 4):
            for z in (KZ0, KZ1): b.set(x, f + 2, z, "minecraft:red_stained_glass_pane"); b.set(x, f + 3, z, "minecraft:red_stained_glass_pane")
        for z in range(KZ0 + 3, KZ1 - 2, 4):
            for x in (KX0, KX1): b.set(x, f + 2, z, "minecraft:red_stained_glass_pane"); b.set(x, f + 3, z, "minecraft:red_stained_glass_pane")
        if f > 1:  # flared roof skirts at each floor line
            for x in range(KX0 - 2, KX1 + 3):
                for z in (KZ0 - 2, KZ1 + 2): b.set(x, f - 1, z, ROOF)
                for z in (KZ0 - 1, KZ1 + 1): b.set(x, f - 1, z, ROOF)
            for z in range(KZ0 - 2, KZ1 + 3):
                for x in (KX0 - 2, KX1 + 2): b.set(x, f - 1, z, ROOF)
                for x in (KX0 - 1, KX1 + 1): b.set(x, f - 1, z, ROOF)
            for (x, z) in ((KX0 - 2, KZ0 - 2), (KX1 + 2, KZ0 - 2), (KX0 - 2, KZ1 + 2), (KX1 + 2, KZ1 + 2)): b.set(x, f, z, ROOF)
    b.pagoda_roof(CX, (KZ0 + KZ1) // 2, 16, 14, KTOP + 1, ROOF_ST, ROOF, layers=3)
    for x in (CX - 1, CX, CX + 1):
        for y in (1, 2, 3, 4): b.set(x, y, KZ1, AIR)
    # stairs: a stair block in the north-east corner, keepout
    SX = KX1 - 4
    for f, nf in zip(FLOORS, FLOORS[1:]):
        for i in range(nf - f):
            for w in (0, 1, 2): b.set(SX + w, f + i, KZ0 + 2 + i, stairs("minecraft:crimson_stairs", "south"))
            for w in (0, 1, 2): b.set(SX + w, nf - 1, KZ0 + 2 + i, AIR) if i < nf - f - 1 else None
            for w in (0, 1, 2):
                for k in (1, 2, 3):
                    if b.get(SX + w, f + i + k, KZ0 + 2 + i) not in (None, AIR) and "crimson_stairs" not in b.get(SX + w, f + i + k, KZ0 + 2 + i): b.set(SX + w, f + i + k, KZ0 + 2 + i, AIR)
    KEEP = ((SX - 1, KZ0 + 1, SX + 3, KZ0 + 11),)
    hh = 7
    # ground: great hall with a fire pit
    r = I.furnish(b, KX0 + 1, 1, KZ0 + 12, KX1 - 1, KZ1 - 1, hh, "hall", KAIDO)
    for x in range(CX - 2, CX + 3):
        for z in range(KZ0 + 5, KZ0 + 9): b.set(x, 0, z, "minecraft:magma_block")
    b.set(CX, 1, KZ0 + 7, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    I.furnish(b, KX0 + 1, 1, KZ0 + 1, SX - 2, KZ0 + 10, hh, "armory", KAIDO)
    for x in range(KX0 + 1, KX1):
        if not (KEEP[0][0] <= x <= KEEP[0][2]):
            for y in range(1, 8): b.set(x, y, KZ0 + 11, BLACK)
    for y in (1, 2, 3): b.set(CX - 4, y, KZ0 + 11, AIR); b.set(CX - 3, y, KZ0 + 11, AIR)
    I.subdivide(b, KX0 + 1, FLOORS[1], KZ0 + 1, KX1 - 1, KZ1 - 1, hh, BLACK, ("barracks", "storage", "armory", "bedroom"), KAIDO, cell=12,
                keepout=KEEP, seed=8)
    I.subdivide(b, KX0 + 1, FLOORS[2], KZ0 + 1, KX1 - 1, KZ1 - 1, hh, BLACK, ("library", "lab", "dining", "treasure"), FIRE, cell=12,
                keepout=KEEP, seed=9)
    r = I.furnish(b, KX0 + 1, FLOORS[3], KZ0 + 1, KX1 - 1, KZ1 - 1, KTOP - FLOORS[3], "throne", FIRE)
    b.box(CX - 5, FLOORS[3], CZ - 6, CX + 5, FLOORS[3], CZ - 2, "minecraft:red_carpet") if False else None
    b.box(CX - 4, FLOORS[3], KZ0 + 14, CX + 4, FLOORS[3], KZ0 + 18, "minecraft:dark_oak_planks")  # the war table with the map
    for x in range(CX - 4, CX + 5): b.set(x, FLOORS[3] + 1, KZ0 + 16, "minecraft:white_carpet" if x % 2 else "minecraft:brown_carpet")
    # ---------------- the stone pteranodon on the keep roof, wings ablaze
    PY = KTOP + 14
    PZ = (KZ0 + KZ1) // 2
    b.shape(lambda x, y, z: ((x - CX) / 2.5) ** 2 + ((y - PY) / 2.5) ** 2 + ((z - PZ) / 6) ** 2 <= 1, CX - 3, PY - 3, PZ - 7, CX + 3, PY + 3, PZ + 7, "minecraft:polished_blackstone", interior=None)
    for k in range(10):  # long beak and the head crest
        b.set(CX, PY + 1, PZ + 6 + k, "minecraft:polished_blackstone"); b.set(CX, PY + 2 + k // 3, PZ + 5 - k // 2, "minecraft:polished_blackstone") if k < 7 else None
    b.set(CX - 1, PY + 2, PZ + 6, "minecraft:magma_block"); b.set(CX + 1, PY + 2, PZ + 6, "minecraft:magma_block")
    for side in (-1, 1):
        for i in range(24):
            x = CX + side * (2 + i); top = PY + 2 + int(4 * math.sin(i / 23 * math.pi)) - i // 8
            depth = max(1, 7 - i // 4)
            for z in range(PZ - depth, PZ + 2):
                b.set(x, top, z, "minecraft:polished_blackstone" if z > PZ - depth else "minecraft:magma_block")
            if i % 3 == 0: b.set(x, top + 1, PZ - depth, "minecraft:fire")
    for y in range(KTOP + 6, PY - 2): b.set(CX, y, PZ, "minecraft:polished_blackstone_wall") if False else b.set(CX, y, PZ, "minecraft:chiseled_polished_blackstone")
    # ---------------- people and loot
    b.npc(CX, FLOORS[3], KZ0 + 5, "king", True)
    b.chest(KX0 + 2, FLOORS[3], KZ0 + 2, "hard", "east"); b.chest(fx0 + 9, 1, fz0 + 2, "hard", "west"); b.chest(bx0 + 7, 1, bz0 + 2, "hard", "west")
    b.guards("gifter", ((CX - 4, Z1w - 5), (CX + 4, Z1w - 5), (CX - 8, KZ1 + 4), (CX + 8, KZ1 + 4)))
    b.guards("flame_guard", ((CX - 6, KZ0 + 18), (CX + 6, KZ0 + 18)), y=FLOORS[3])
    b.guards("flame_guard", ((W0 + 8, Z0w + 2), (W1 - 8, Z0w + 2)), y=WH + 1)
    return b, 0
