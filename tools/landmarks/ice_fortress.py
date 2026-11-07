"""Aokiji's Ice Fortress: a citadel frozen out of the sea by Kuzan's Ice Age. Walls of packed and blue ice over
frozen-stone footings, crystal towers with ice spikes, a frozen bay with two Marine ships locked in the ice and
a frozen wave curling over the gate. Inside the snow-brick keep: the frost soldiers' barracks, kitchen and cold
store, the armory, a library, and Aokiji's lazy bedroom with his sleep mask and his bicycle parked by the bed.
~96 x 96. Ground = y 0."""
import math, random
from canvas import *
import interiors as I

SID = "ice_fortress"
TITLE = "Aokiji's Ice Fortress"
CUTS = [3, 12]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 96
CX, CZ = 48, 40
PICE = "minecraft:packed_ice"
BICE = "minecraft:blue_ice"
SNOWB = "onepiece:snow_bricks"
FROZ = "onepiece:frozen_stone"
FROZ_W = "onepiece:frozen_stone_wall"
FROST = dict(wood="spruce", rug="light_blue", rug2="white", bed="light_blue", light="minecraft:sea_lantern", accent="minecraft:packed_ice",
             banner="light_blue", candle="light_blue")
W0, W1, Z0, Z1 = CX - 24, CX + 24, CZ - 22, CZ + 20
KX0, KX1, KZ0, KZ1 = CX - 12, CX + 12, CZ - 16, CZ + 4
FL = (1, 9, 17)
KTOP = 25


def ice_tower(b, cx, cz, r, h):
    b.cyl(cx, cz, r, 0, h, PICE, hollow=True)
    for y in range(0, h + 1, 7): b.cyl(cx, cz, r + 0.6, y, y, BICE, hollow=True)
    b.cyl(cx, cz, r - 1, 0, 0, SNOWB)
    for f in range(7, h, 7): b.cyl(cx, cz, r - 1, f, f, "minecraft:spruce_planks")
    for y in range(1, h + 1): b.set(cx, y, cz - r + 1, "minecraft:ladder[facing=south,waterlogged=false]")
    for k in range(int(r * 3)):  # crystal spike roof
        rr = (r + 0.8) * (1 - k / (r * 3)) + 0.2
        b.cyl(cx, cz, rr, h + 1 + k, h + 1 + k, "minecraft:light_blue_stained_glass" if k % 3 == 2 else PICE, hollow=rr > 1.4)
    b.set(cx, h + 1, cz - r + 1, AIR)
    for (dx, dz) in ((r, 0), (-r, 0), (0, r), (0, -r)):
        for y in range(3, h, 7): b.set(cx + dx, y, cz + dz, "minecraft:light_blue_stained_glass_pane")


def ice_spike(b, x, z, h, r):
    for y in range(1, h + 1):
        rr = r * (1 - (y - 1) / h)
        if rr < 0.5: b.set(x, y, z, PICE); continue
        b.cyl(x, z, rr, y, y, PICE)


def build():
    rnd = random.Random(97)
    b = B()
    # ---------------- snowfield, frozen bay to the south, ice spikes
    for x in range(N):
        for z in range(N):
            bay = z > 72 + 4 * math.sin(x * 0.12)
            for y in (-4, -3, -2): b.set(x, y, z, "minecraft:stone")
            if bay:
                b.set(x, -1, z, WATER); b.set(x, 0, z, "minecraft:ice" if (x * z) % 7 else PICE)
            else:
                b.set(x, -1, z, "minecraft:dirt")
                b.set(x, 0, z, "minecraft:snow_block" if (x + z) % 5 else "minecraft:powder_snow" if False else "minecraft:snow_block")
                if rnd.random() < 0.35: b.set(x, 1, z, "minecraft:snow[layers=1]")
    for (x, z, h, r) in ((8, 10, 18, 2.5), (14, 54, 12, 2), (86, 12, 22, 3), (90, 50, 14, 2), (6, 30, 9, 1.5), (80, 66, 10, 1.5), (30, 8, 8, 1.5)):
        ice_spike(b, x, z, h, r)
    # two Marine ships frozen into the bay
    for (sx, sz, L) in ((10, 80, 26), (58, 82, 30)):
        dy = b.ship(sx, -4, sz, L, 9, hull="minecraft:white_terracotta", deck="minecraft:birch_planks", masts=((L // 2 - 2, 14), (L // 2 + 6, 10)),
                    sail="minecraft:white_wool", flag=("minecraft:blue_wool", "minecraft:white_wool"), cabin=(5, 3, "minecraft:white_concrete"))
        for x in range(sx - 1, sx + L + 1):  # ice crust climbing the hull
            for z in range(sz - 1, sz + 11):
                for y in (1, 2):
                    if b.get(x, y, z) is None and rnd.random() < 0.5 and b.get(x, y - 1, z) not in (None, AIR): b.set(x, y, z, "minecraft:ice")
    # ---------------- curtain wall of ice on frozen-stone footings
    WH = 12
    for x in range(W0, W1 + 1):
        for z in range(Z0, Z1 + 1):
            if x in (W0, W0 + 1, W1 - 1, W1) or z in (Z0, Z0 + 1, Z1 - 1, Z1):
                for y in range(0, WH + 1): b.set(x, y, z, FROZ if y < 3 else (BICE if y % 4 == 0 else PICE))
                if x in (W0, W1) or z in (Z0, Z1):
                    b.set(x, WH + 1, z, PICE if (x + z) % 2 else FROZ_W)
                    if (x + z) % 4 == 0 and rnd.random() < 0.5:  # icicles hanging off the outside
                        ox = -1 if x == W0 else 1 if x == W1 else 0; oz = -1 if z == Z0 else 1 if z == Z1 else 0
                        for k in range(rnd.randint(1, 3)): b.set(x + ox, WH - k, z + oz, "minecraft:pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]" if False else "minecraft:ice")
    for (tx, tz) in ((W0, Z0), (W1, Z0), (W0, Z1), (W1, Z1)): ice_tower(b, tx, tz, 4, WH + 8)
    # gate with the frozen wave arching over it
    for x in range(CX - 3, CX + 4):
        for z in (Z1 - 1, Z1):
            for y in range(1, 7): b.set(x, y, z, AIR)
            b.set(x, 0, z, SNOWB)
    zc, yc = Z1 + 9, 12
    for i in range(400):  # a curling wave of ice, frozen as it breaks towards the gate
        th = i / 399 * 1.55 * math.pi
        r = 11 - 6 * th / (1.55 * math.pi)
        zz = zc + r * math.sin(th); yy = yc - r * math.cos(th)
        half = 11 - int(3 * abs(math.sin(th / 2)))
        for x in range(CX - half, CX + half + 1):
            for (dy, dz) in ((0, 0), (1, 0), (0, 1)):
                y, z = round(yy) + dy, round(zz) + dz
                if y >= 1: b.set(x, y, z, BICE if (x * 3 + y) % 7 == 0 else ("minecraft:snow_block" if th > 1.3 * math.pi and (x + y) % 3 == 0 else PICE))
    for x in range(CX - 2, CX + 3):  # a tunnel through the foot of the wave to the gate
        for z in range(Z1 + 1, Z1 + 16):
            for y in range(1, 5): b.set(x, y, z, AIR)
    for x in range(CX - 10, CX + 11):  # foam of snow under the crest
        b.set(x, 1, Z1 + 3, "minecraft:snow_block") if abs(x - CX) > 4 else None
    # courtyard: snow-brick paving, ice statues of Marines, Aokiji's bicycle track
    for x in range(W0 + 2, W1 - 1):
        for z in range(Z0 + 2, Z1 - 1): b.set(x, 0, z, SNOWB if (x + z) % 3 else "minecraft:polished_diorite")
    for (x, z) in ((CX - 16, CZ + 12), (CX + 16, CZ + 12), (CX - 16, CZ + 6), (CX + 16, CZ + 6)):
        b.set(x, 1, z, PICE); b.set(x, 2, z, PICE); b.set(x, 3, z, BICE); b.set(x - 1, 2, z, "minecraft:ice"); b.set(x + 1, 2, z, "minecraft:ice")
    for z in range(KZ1 + 1, Z1 - 1):
        for x in range(CX - 1, CX + 2): b.set(x, 0, z, "minecraft:light_blue_concrete")
    # ---------------- the keep: snow brick with ice crown, three floors
    b.box(KX0, 0, KZ0, KX1, 0, KZ1, FROZ)
    b.walls(KX0, 1, KZ0, KX1, KTOP, KZ1, SNOWB)
    b.box(KX0 + 1, 1, KZ0 + 1, KX1 - 1, KTOP, KZ1 - 1, AIR)
    for f in FL[1:]: b.box(KX0 + 1, f - 1, KZ0 + 1, KX1 - 1, f - 1, KZ1 - 1, "minecraft:spruce_planks")
    b.box(KX0 + 1, KTOP, KZ0 + 1, KX1 - 1, KTOP, KZ1 - 1, PICE)
    for f in FL:
        for x in range(KX0 + 2, KX1 - 1, 3):
            for z in (KZ0, KZ1): b.set(x, f + 2, z, "minecraft:light_blue_stained_glass_pane"); b.set(x, f + 3, z, "minecraft:light_blue_stained_glass_pane")
        for z in range(KZ0 + 2, KZ1 - 1, 3):
            for x in (KX0, KX1): b.set(x, f + 2, z, "minecraft:light_blue_stained_glass_pane"); b.set(x, f + 3, z, "minecraft:light_blue_stained_glass_pane")
    for x in range(KX0, KX1 + 1):  # jagged ice crown
        for z in (KZ0, KZ1):
            for k in range(1, 2 + (x * 7 + z) % 4): b.set(x, KTOP + k, z, PICE if k < 3 else BICE)
    for z in range(KZ0, KZ1 + 1):
        for x in (KX0, KX1):
            for k in range(1, 2 + (z * 5 + x) % 4): b.set(x, KTOP + k, z, PICE if k < 3 else BICE)
    ice_spike(b, CX, (KZ0 + KZ1) // 2, 0, 0) if False else None
    for y in range(KTOP + 1, KTOP + 18):  # central crystal spire
        rr = 4 * (1 - (y - KTOP - 1) / 17) + 0.3
        b.cyl(CX, (KZ0 + KZ1) // 2, rr, y, y, PICE if y % 4 else BICE)
    for y in range(1, 5):
        for x in (CX - 1, CX, CX + 1): b.set(x, y, KZ1, AIR)
    # stairs in the west end
    SX = KX0 + 2
    for f, nf in zip(FL, FL[1:]):
        for i in range(nf - f):
            for w in (0, 1, 2): b.set(SX + w, f + i, KZ0 + 2 + i, stairs("minecraft:spruce_stairs", "south"))
            for w in (0, 1, 2):
                for k in (1, 2, 3):
                    c = b.get(SX + w, f + i + k, KZ0 + 2 + i)
                    if c not in (None, AIR) and "spruce_stairs" not in c: b.set(SX + w, f + i + k, KZ0 + 2 + i, AIR)
    KEEP = ((SX - 1, KZ0 + 1, SX + 3, KZ0 + 11),)
    I.subdivide(b, KX0 + 1, FL[0], KZ0 + 1, KX1 - 1, KZ1 - 1, 7, SNOWB, ("barracks", "kitchen", "storage", "armory"), FROST, cell=12, keepout=KEEP, seed=11)
    I.subdivide(b, KX0 + 1, FL[1], KZ0 + 1, KX1 - 1, KZ1 - 1, 7, SNOWB, ("library", "barracks", "study", "bath"), FROST, cell=12, keepout=KEEP, seed=12)
    r = I.furnish(b, KX0 + 1, FL[2], KZ0 + 1, KX1 - 1, KZ1 - 1, KTOP - FL[2], "bedroom", FROST)
    r.chandelier(CX, (KZ0 + KZ1) // 2, 2, 2)
    # Aokiji's bicycle beside the bed: two wheels and a frame
    bx, bz = CX + 6, KZ1 - 3
    for (dx, dy) in ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)):
        b.set(bx + dx, FL[2] + dy, bz, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]") if dy != 1 or dx != 1 else None
    for (dx, dy) in ((4, 0), (4, 1), (4, 2), (5, 0), (5, 2), (6, 0), (6, 1), (6, 2)):
        b.set(bx + dx - 1, FL[2] + dy, bz, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
    b.set(bx + 3, FL[2] + 3, bz, "minecraft:black_carpet") if False else b.set(bx + 2, FL[2] + 3, bz, "minecraft:light_blue_concrete")
    # ---------------- people and loot
    b.npc(CX, FL[2], (KZ0 + KZ1) // 2, "aokiji", True)
    b.chest(KX1 - 2, FL[2], KZ0 + 2, "hard", "west"); b.chest(KX0 + 6, FL[0], KZ1 - 2, "hard", "north")
    b.guards("frost_soldier", ((CX - 4, Z1 - 4), (CX + 4, Z1 - 4), (CX - 10, CZ + 10), (CX + 10, CZ + 10)))
    b.guards("frost_soldier", ((W0 + 6, Z0 + 1), (W1 - 6, Z0 + 1)), y=WH + 1)
    return b, 0
