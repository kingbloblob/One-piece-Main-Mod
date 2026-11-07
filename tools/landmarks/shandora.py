"""Shandora, the lost City of Gold, carried up to the sky on the Knock Up Stream (Upper Yard, Skypiea).

What the show has, and where it is here:
- Upper Yard is solid land (not cloud) floating on the clouds: a jungle of giant trees over the stone ruins of
  Shandora, grey-tan carved stone with gold trim, stepped Mesoamerican-style buildings and the great temple;
- Giant Jack, the colossal twisted beanstalk, stands in the centre of Upper Yard and runs up through the main ruins,
  towering over everything; its roots spread over the old city's plaza;
- partway up the vine an Island Cloud holds the Upper Ruins (the upper parts of Shandora's buildings);
- at the very top of Giant Jack, on its own cloud, the Golden Belfry: the huge golden bell of Shandora hanging in the
  remains of its stone belfry, where Enel found it and where Luffy rang it.
A ladder runs up inside the vine (doors at the Upper Ruins and the top). ~124 x 124, floats at a fixed height
(canvas y 0 = world y 162)."""
import math, random
from canvas import *
import interiors as I

SID = "shandora"
TITLE = "Shandora (City of Gold in the sky)"
CUTS = [4]
TILER = dict(terrain="none", sky_y=162)

N = 124
CX, CZ = 62, 62
CLOUD = "onepiece:island_cloud"
PUFF = "onepiece:cloud_puff"
RUIN = "onepiece:shandian_ruin_stone"
RUIN_ST = "onepiece:shandian_ruin_stone_stairs"
RUIN_SL = "onepiece:shandian_ruin_stone_slab"
RUIN_W = "onepiece:shandian_ruin_stone_wall"
GOLDB = "onepiece:shandora_gold_bricks"
GOLDB_ST = "onepiece:shandora_gold_brick_stairs"
MOSS = "minecraft:moss_block"
# Giant Jack
JACK = "minecraft:moss_block"
JACK_DARK = "minecraft:green_concrete"
JACK_LIGHT = "minecraft:lime_concrete"
JACKS = (JACK, JACK_DARK, JACK_LIGHT)
LEAF = "minecraft:azalea_leaves[distance=7,persistent=true,waterlogged=false]"
TOPJ = 82          # tip of Giant Jack
TWIST = 0.085      # turn of the strands per block of height
U_Y = 30           # top of the Upper Ruins cloud
T_Y = 58           # top of the Golden Belfry cloud


def giant_tree(b, x, z, h, rnd):
    r = rnd.uniform(2.2, 3.2)
    for y in range(1, h):
        rr = r * (1 - y / h * 0.5) + (1.5 if y < 3 else 0)
        b.cyl(x, z, rr, y, y, "minecraft:jungle_log[axis=y]")
    for k in range(5):
        a = rnd.uniform(0, 2 * math.pi); ln = rnd.randint(6, 11); by = h - rnd.randint(0, 8)
        for i in range(ln):
            b.set(round(x + math.cos(a) * i), by + i // 3, round(z + math.sin(a) * i), "minecraft:jungle_log[axis=x]")
        b.sphere(round(x + math.cos(a) * ln), by + ln // 3 + 1, round(z + math.sin(a) * ln), 3.5, "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]", ry=2.4)
    b.sphere(x, h + 1, z, 5.5, "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]", ry=3.5)
    for y in range(h - 12, h, 3):
        a = rnd.uniform(0, 6.28)
        for k in range(rnd.randint(4, 9)):
            vx, vz = round(x + (r + 1) * math.cos(a)), round(z + (r + 1) * math.sin(a))
            if b.get(vx, y - k, vz) in (None, AIR): b.set(vx, y - k, vz, "minecraft:vine[east=false,north=true,south=false,up=false,west=false]")


def ruin_house(b, x0, z0, w, d, h, rnd):
    b.box(x0, 0, z0, x0 + w, 0, z0 + d, RUIN)
    for x in range(x0, x0 + w + 1):
        for z in range(z0, z0 + d + 1):
            if x in (x0, x0 + w) or z in (z0, z0 + d):
                top = h - int(abs(math.sin(x * 1.3 + z * 0.7)) * h * 0.7)  # broken, uneven wall tops
                for y in range(1, top + 1): b.set(x, y, z, GOLDB if y == top and rnd.random() < 0.3 else (MOSS if rnd.random() < 0.08 else RUIN))
    b.set(x0 + w // 2, 1, z0, AIR); b.set(x0 + w // 2, 2, z0, AIR); b.set(x0 + w // 2, 3, z0, AIR)
    for x in range(x0 + 2, x0 + w - 1, 3): b.set(x, 2, z0 + d, AIR)
    b.set(x0 + 1, 1, z0 + 1, "minecraft:decorated_pot"); b.set(x0 + w - 1, 1, z0 + d - 1, rnd.choice(("minecraft:chiseled_stone_bricks", GOLDB, "minecraft:decorated_pot")))
    if rnd.random() < 0.5: b.set(x0 + w // 2, 1, z0 + d // 2, "minecraft:gold_block")


# ---------------------------------------------------------------- Giant Jack
def jack_R(y):
    """Radius of the beanstalk's bundle at height y (thick at the roots, thinner at the top)."""
    return 10.0 - 5.0 * min(1.0, max(0, y) / TOPJ)


def jack_cell(x, y, z):
    """Block of Giant Jack at a cell, or None: three strands twisted round each other, dark grooves between them
    and a thin light ridge spiralling up each strand."""
    R = jack_R(y)
    flare = (5 - y) * 1.1 if y < 5 else 0.0
    rr = 0.62 * R + flare
    hit = False
    for k in range(3):
        a = k * 2 * math.pi / 3 + y * TWIST
        sx, sz = CX + 0.42 * R * math.cos(a), CZ + 0.42 * R * math.sin(a)
        if math.hypot(x - sx, z - sz) <= rr: hit = True; break
    if not hit: return None
    ph = (math.atan2(z - CZ, x - CX) - y * TWIST) % (2 * math.pi / 3)
    if abs(ph - math.pi / 3) < 0.26: return JACK_DARK
    if ph < 0.13 or ph > 2 * math.pi / 3 - 0.13: return JACK_LIGHT
    return JACK


def giant_jack(b, rnd):
    for y in range(-3, TOPJ + 1):
        R = jack_R(y) + (7 if y < 5 else 1)
        for x in range(int(CX - R) - 1, int(CX + R) + 2):
            for z in range(int(CZ - R) - 1, int(CZ + R) + 2):
                s = jack_cell(x, y, z)
                if s: b.set(x, y, z, s)
    # roots crawling over the plaza
    for k in range(7):
        a = k * 2 * math.pi / 7 + 0.3
        for i in range(8, 17):
            yy = 2 - (i - 8) // 3
            for w in (0, 1):
                b.set(round(CX + math.cos(a) * i + w * math.sin(a)), yy, round(CZ + math.sin(a) * i - w * math.cos(a)), JACK if i % 3 else JACK_DARK)
            if yy > 1: b.set(round(CX + math.cos(a) * i), yy - 1, round(CZ + math.sin(a) * i), JACK)
    # broad bean leaves on short stalks all the way up, and tendrils curling off the top
    def leaf_cells(y, a):
        R = jack_R(y) + 0.5
        stalk = [(round(CX + math.cos(a) * (R + j)), y + max(0, j) // 2, round(CZ + math.sin(a) * (R + j))) for j in range(-int(R * 0.45), 4)]
        lx, lz = CX + math.cos(a) * (R + 6), CZ + math.sin(a) * (R + 6)
        blade = []
        for dx in range(-4, 5):
            for dz in range(-4, 5):
                u = dx * math.cos(a) + dz * math.sin(a); v = -dx * math.sin(a) + dz * math.cos(a)
                if (u / 3.6) ** 2 + (v / 2.6) ** 2 <= 1:
                    blade.append((round(lx + dx), y + 2 + (1 if u > 1.5 else 0), round(lz + dz)))
        return stalk, blade

    BX, BZ = CX + 18, CZ  # the Golden Belfry (see golden_belfry): keep its bell chamber and arches clear of leaves

    def in_belfry(p):
        x, y, z = p
        return BX - 10 <= x <= BX + 10 and BZ - 9 <= z <= BZ + 9 and y >= T_Y

    for i, y in enumerate(range(10, TOPJ - 4, 7)):
        if abs(y - U_Y) < 5 or abs(y - T_Y) < 6: continue
        a0 = i * 2.4
        for da in (0, 0.6, -0.6, 1.2, -1.2, 1.8, -1.8, 2.4, -2.4, math.pi):  # turn a leaf that would grow into the belfry
            stalk, blade = leaf_cells(y, a0 + da)
            if not any(in_belfry(p) for p in stalk + blade): break
        else:
            continue  # no way round it: leave this leaf out
        for p in stalk: b.set(*p, JACK_DARK)
        for p in blade: b.set(*p, LEAF)
    for k in range(3):  # tendrils at the tip
        a = k * 2.1 + 0.5
        for i in range(36):
            t = i / 35
            r = 2 + 6 * t
            b.set(round(CX + r * math.cos(a + t * 2.5)), TOPJ - 2 + int(4 * math.sin(t * math.pi)), round(CZ + r * math.sin(a + t * 2.5)), JACK_LIGHT if i % 8 else JACK_DARK)
    b.sphere(CX, TOPJ + 1, CZ, 3.2, LEAF, ry=2.2)
    # the climb: a ladder shaft up the heart of the vine, with doors at the ground, the Upper Ruins and the top
    for y in range(1, T_Y + 4):
        for x in range(CX - 1, CX + 2):
            for z in range(CZ - 1, CZ + 1): b.set(x, y, z, AIR)
        b.set(CX - 1, y, CZ + 1, AIR); b.set(CX + 1, y, CZ + 1, AIR)
    for y in range(1, T_Y + 3): b.set(CX, y, CZ + 1, ladder("north"))
    for y in range(3, T_Y + 3, 5): b.set(CX + 2, y, CZ - 1 + (y // 5) % 2, "minecraft:shroomlight")  # glowing nodes light the climb
    for (y0, sx) in ((1, -1), (U_Y + 1, -1), (T_Y + 1, 1)):
        for i in range(2, 16):
            x = CX + sx * i
            if b.get(x, y0, CZ) not in JACKS and b.get(x, y0, CZ - 1) not in JACKS and i > 4: break
            for y in range(y0, y0 + 3):
                for z in (CZ - 1, CZ): b.set(x, y, z, AIR)
            for z in (CZ - 1, CZ):
                if b.get(x, y0 + 3, z) in (None, AIR): b.set(x, y0 + 3, z, JACK_DARK)


def cloud_shelf(b, cx, cz, rx, rz, ytop, th, rnd):
    """An Island Cloud clinging round the vine: flat walkable top, puffy rounded underside."""
    for x in range(int(cx - rx) - 2, int(cx + rx) + 3):
        for z in range(int(cz - rz) - 2, int(cz + rz) + 3):
            a = math.atan2(z - cz, x - cx)
            d = math.hypot((x - cx) / rx, (z - cz) / rz) / (1 + 0.08 * math.sin(a * 5 + cx))
            if d > 1: continue
            depth = int(1 + th * (1 - d) ** 0.6)
            for y in range(ytop - depth, ytop + 1):
                if b.get(x, y, z) in (None, AIR): b.set(x, y, z, PUFF if d > 0.85 or y == ytop - depth else CLOUD)
    for i in range(10):
        a = rnd.uniform(0, 2 * math.pi)
        b.sphere(round(cx + rx * 0.75 * math.cos(a)), ytop - th + 1, round(cz + rz * 0.75 * math.sin(a)), rnd.uniform(2, 3.4), PUFF, ry=1.6)


def upper_ruins(b, rnd):
    """The Upper Ruins: broken tops of Shandora's buildings stranded on the cloud halfway up the vine."""
    cx, cz, y = CX - 7, CZ + 3, U_Y
    cloud_shelf(b, cx, cz, 17, 13, y, 5, rnd)
    for x in range(cx - 13, cx + 12):  # cracked stone paving
        for z in range(cz - 9, cz + 10):
            if b.get(x, y, z) == CLOUD and math.hypot((x - cx) / 13, (z - cz) / 10) < 1 and math.sin(x * 0.9) * math.cos(z * 0.8) < 0.75:
                b.set(x, y, z, RUIN if rnd.random() < 0.82 else MOSS)
    # a broken colonnade with gold capitals carrying a stretch of lintel
    for i, (x, z) in enumerate(((cx - 11, cz - 6), (cx - 11, cz), (cx - 11, cz + 6), (cx - 5, cz + 9), (cx + 1, cz + 9), (cx + 7, cz + 8))):
        h = (7, 7, 7, 2, 7, 5)[i]
        for yy in range(y + 1, y + h + 1): b.set(x, yy, z, RUIN if yy % 3 else "minecraft:chiseled_stone_bricks")
        b.set(x, y + h + 1, z, GOLDB if h >= 6 else slab(RUIN_SL))
    for z in range(cz - 6, cz + 4): b.set(cx - 11, y + 9, z, RUIN)
    for z in range(cz - 6, cz + 4, 3): b.set(cx - 11, y + 10, z, slab(RUIN_SL))
    for x in range(cx - 3, cx + 4): b.set(x, y + 1, cz + 7, stairs(RUIN_ST, "north"))  # fallen lintel
    # a stepped wall fragment with a golden frieze
    for x in range(cx + 3, cx + 11):
        top = 6 - abs(x - (cx + 6))
        for yy in range(y + 1, y + 2 + max(1, top)): b.set(x, yy, cz - 8, GOLDB if yy == y + 3 else RUIN)
    for x in range(cx + 3, cx + 11): b.set(x, y + 1, cz - 7, stairs(RUIN_ST, "south"))


def golden_belfry(b, rnd):
    """The top cloud: the remains of Shandora's belfry with the great golden bell."""
    cloud_shelf(b, CX + 11, CZ, 21, 15, T_Y, 6, rnd)
    BX, BZ, Y = CX + 18, CZ, T_Y
    b.box(BX - 10, Y, BZ - 10, BX + 9, Y, BZ + 10, RUIN)  # stone court
    for x in range(BX - 10, BX + 10):
        for z in (BZ - 10, BZ + 10): b.set(x, Y, z, GOLDB if x % 3 == 0 else RUIN)
    b.box(BX - 7, Y + 1, BZ - 6, BX + 7, Y + 1, BZ + 6, RUIN)  # raised plinth
    b.box(BX - 6, Y + 1, BZ - 5, BX + 6, Y + 1, BZ + 5, "minecraft:chiseled_stone_bricks")
    for x in range(BX - 3, BX + 4): b.set(x, Y + 1, BZ + 7, stairs(RUIN_ST, "north"))
    for z in range(BZ - 2, BZ + 3): b.set(BX - 8, Y + 1, z, stairs(RUIN_ST, "east"))
    PY = Y + 1
    # four massive piers, gold bands, arched openings on every side
    piers = ((BX - 7, BZ - 6), (BX + 7, BZ - 6), (BX - 7, BZ + 6), (BX + 7, BZ + 6))
    for (px, pz) in piers:
        for yy in range(PY + 1, PY + 17):
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    edge = abs(dx) == 1 and abs(dz) == 1
                    s = GOLDB if yy in (PY + 1, PY + 8, PY + 14) else ("minecraft:chiseled_stone_bricks" if edge and yy % 4 == 0 else RUIN)
                    b.set(px + dx, yy, pz + dz, s)
    for z in (BZ - 6, BZ + 6):  # arches along x
        for x in range(BX - 6, BX + 7):
            spring = PY + 10 + int(round(math.sqrt(max(0, 36 - (x - BX) ** 2)) * 0.75))
            for yy in range(spring, PY + 17):
                for dz in (-1, 0, 1): b.set(x, yy, z + dz, RUIN)
            b.set(x, spring, z + (1 if z > BZ else -1), GOLDB)
    for x in (BX - 7, BX + 7):  # arches along z
        for z in range(BZ - 5, BZ + 6):
            spring = PY + 10 + int(round(math.sqrt(max(0, 25 - (z - BZ) ** 2)) * 0.75))
            for yy in range(spring, PY + 17):
                for dx in (-1, 0, 1): b.set(x + dx, yy, z, RUIN)
            b.set(x + (1 if x > BX else -1), spring, z, GOLDB)
    # the bell deck and the stepped roof (one corner broken away)
    b.box(BX - 8, PY + 17, BZ - 7, BX + 8, PY + 17, BZ + 7, RUIN)
    for x in range(BX - 8, BX + 9):
        for z in (BZ - 7, BZ + 7): b.set(x, PY + 17, z, GOLDB)
    for k, (hx, hz, s) in enumerate(((7, 6, RUIN), (5, 4, GOLDB), (3, 2, RUIN), (1, 1, GOLDB))):
        y = PY + 18 + k
        for x in range(BX - hx, BX + hx + 1):
            for z in range(BZ - hz, BZ + hz + 1):
                if x - BX + z - BZ > hx + hz - 3 and k < 2: continue  # the broken corner
                b.set(x, y, z, s)
    for x in range(BX - 8, BX + 9):  # cornice under the deck
        for z in (BZ - 8, BZ + 8): b.set(x, PY + 16, z, stairs(RUIN_ST, "north" if z < BZ else "south", "top"))
    for z in range(BZ - 7, BZ + 8):
        for x in (BX - 9, BX + 9): b.set(x, PY + 16, z, stairs(RUIN_ST, "east" if x > BX else "west", "top"))
    b.set(BX, PY + 22, BZ, "minecraft:gold_block")
    # the great golden bell: flared lip, two raised bands, crown and yoke under the bell deck
    top, lip = PY + 15, PY + 4
    H = top - lip
    for y in range(lip, top + 1):
        t = (top - y) / H
        r = 2.0 + 1.5 * t ** 1.2 + 1.0 * t ** 6
        s = "minecraft:raw_gold_block" if (abs(t - 0.38) < 0.06 or abs(t - 0.72) < 0.06 or t > 0.93) else "minecraft:gold_block"
        b.cyl(BX, BZ, r, y, y, s, hollow=y < top)
    for (dx, dz) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)): b.set(BX + dx, PY + 16, BZ + dz, "minecraft:gold_block")
    for y in range(PY + 7, top): b.set(BX, y, BZ, "minecraft:iron_chain[axis=y,waterlogged=false]")
    b.set(BX, PY + 6, BZ, "minecraft:bell[attachment=ceiling,facing=north,powered=false]")
    return BX, BZ, PY


def build():
    rnd = random.Random(16)
    b = B()
    # ---------------- the floating island: cloud base with a rocky ruined crust
    for x in range(N):
        for z in range(N):
            d = math.hypot(x - CX, z - CZ); a = math.atan2(z - CZ, x - CX)
            r = 56 + 4 * math.sin(3 * a) + 2 * math.sin(8 * a + 1)
            if d > r: continue
            depth = int(4 + (r - d) * 0.35 + 2 * math.sin(x * 0.3) * math.cos(z * 0.27))
            for y in range(-depth, -2): b.set(x, y, z, CLOUD)
            for y in (-2, -1): b.set(x, y, z, "minecraft:dirt")
            b.set(x, 0, z, "minecraft:grass_block" if d > 12 and (x + z) % 7 else MOSS)
    for i in range(30):  # cloud puffs drifting around the edge
        a = rnd.uniform(0, 2 * math.pi); rr = rnd.uniform(58, 62)
        b.sphere(round(CX + rr * math.cos(a)), rnd.randint(-6, 2), round(CZ + rr * math.sin(a)), rnd.uniform(2, 4), "onepiece:cloud_puff", ry=1.5)
    # ---------------- the city ruins: a ring of broken houses along old stone avenues with gold inlay
    r2 = random.Random(1616)
    for x in range(CX - 2, CX + 3):
        for z in range(10, N - 10):
            b.set(x, 0, z, GOLDB if (x == CX and z % 3 == 0) or (abs(x - CX) == 2 and z % 6 == 0) else (MOSS if r2.random() < 0.1 else RUIN))
    for z in range(CZ - 2, CZ + 3):
        for x in range(10, N - 10):
            b.set(x, 0, z, GOLDB if (z == CZ and x % 3 == 0) or (abs(z - CZ) == 2 and x % 6 == 0) else (MOSS if r2.random() < 0.1 else RUIN))
    for i in range(26):
        a = 2 * math.pi * i / 26 + rnd.uniform(-0.05, 0.05)
        rr = rnd.uniform(28, 44)
        x, z = round(CX + rr * math.cos(a)), round(CZ + rr * math.sin(a))
        if abs(x - CX) < 6 or abs(z - CZ) < 6: continue
        ruin_house(b, x - 4, z - 3, rnd.randint(6, 9), rnd.randint(5, 8), rnd.randint(5, 9), rnd)
    # ---------------- giant Upper Yard trees growing through the city
    for i in range(11):
        a = rnd.uniform(0, 2 * math.pi); rr = rnd.uniform(30, 52)
        x, z = round(CX + rr * math.cos(a)), round(CZ + rr * math.sin(a))
        if abs(x - CX) < 8 or abs(z - CZ) < 8: continue
        giant_tree(b, x, z, rnd.randint(26, 40), rnd)
    for i in range(140):
        x, z = rnd.randint(8, N - 8), rnd.randint(8, N - 8)
        if b.get(x, 0, z) == "minecraft:grass_block" and b.get(x, 1, z) in (None, AIR):
            b.set(x, 1, z, rnd.choice(("minecraft:fern", "minecraft:short_grass", "onepiece:sky_lotus", "minecraft:large_fern[half=lower]")))
    # ---------------- the great temple (stepped, shandian stone with golden friezes)
    TX, TZ = CX - 26, CZ - 24
    for i, hw in enumerate((14, 11, 8, 5)):
        y0 = i * 5
        b.box(TX - hw, y0 + 1, TZ - hw, TX + hw, y0 + 5, TZ + hw, RUIN)
        for k in range(-hw, hw + 1):
            for (x, z) in ((TX + k, TZ - hw), (TX + k, TZ + hw), (TX - hw, TZ + k), (TX + hw, TZ + k)):
                if k % 3 == 0: b.set(x, y0 + 4, z, GOLDB)
                if rnd.random() < 0.12: b.set(x, y0 + 5, z, MOSS)
    b.box(TX - 12, 1, TZ - 12, TX + 12, 9, TZ + 12, AIR)  # hollow: treasure chamber and shrine inside
    for i in range(20):  # stair: rises 1 per block toward the top shrine
        for x in range(TX - 2, TX + 3):
            z = TZ + 15 - i
            if z < TZ + 6: break
            b.set(x, 1 + i, z, stairs(RUIN_ST, "north"))
    for x in range(TX - 2, TX + 3):
        for y in range(1, 5): b.set(x, y, TZ + 14, AIR); b.set(x, y, TZ + 13, AIR); b.set(x, y, TZ + 12, AIR)
    b.box(TX - 3, 20, TZ - 3, TX + 3, 20, TZ + 3, GOLDB)
    for (x, z) in ((TX - 3, TZ - 3), (TX + 3, TZ - 3), (TX - 3, TZ + 3), (TX + 3, TZ + 3)): b.column(x, z, 21, 26, GOLDB)
    b.box(TX - 4, 27, TZ - 4, TX + 4, 27, TZ + 4, GOLDB); b.box(TX - 2, 28, TZ - 2, TX + 2, 28, TZ + 2, GOLDB); b.set(TX, 29, TZ, "minecraft:gold_block")
    I.furnish(b, TX - 11, 1, TZ - 11, TX + 11, TZ - 1, 8, "treasure", "royal")
    I.furnish(b, TX - 11, 1, TZ + 1, TX + 11, TZ + 11, 8, "chapel", "desert")
    for x in range(TX - 11, TX + 12):
        for y in range(1, 9): b.set(x, y, TZ, RUIN) if b.get(x, y, TZ) in (None, AIR) and abs(x - TX) > 2 else None
    # carved stone tablet by the temple stair (the Shandora inscription, not a Poneglyph for the story)
    b.set(TX + 6, 1, TZ + 16, "minecraft:chiseled_stone_bricks"); b.set(TX + 6, 2, TZ + 16, "minecraft:chiseled_stone_bricks")
    # ---------------- the old city plaza where Giant Jack bursts out of the ruins
    for x in range(CX - 17, CX + 18):
        for z in range(CZ - 17, CZ + 18):
            d = math.hypot(x - CX, z - CZ)
            if d <= 16.5:
                ring = abs(d - 15) < 0.6 or abs(d - 11) < 0.6
                b.set(x, 0, z, GOLDB if ring and (x + z) % 2 else (MOSS if r2.random() < 0.12 else RUIN))
                for y in range(1, 3):
                    if b.get(x, y, z) not in (None, AIR): b.set(x, y, z, AIR)
    for k in range(12):  # a ring of broken columns round the plaza
        a = k * math.pi / 6 + 0.13
        x, z = round(CX + 15 * math.cos(a)), round(CZ + 15 * math.sin(a))
        if abs(x - CX) < 4 or abs(z - CZ) < 4: continue
        h = (8, 3, 6, 2, 8, 5, 7, 2, 8, 4, 6, 3)[k]
        for y in range(1, h + 1): b.set(x, y, z, RUIN if y % 3 else "minecraft:chiseled_stone_bricks")
        if h >= 6: b.set(x, h + 1, z, GOLDB); b.set(x, h + 2, z, slab(RUIN_SL))
        else: b.set(x, h + 1, z, slab(RUIN_SL)); b.set(x + 1, 1, z, slab(RUIN_SL))
    # ---------------- Giant Jack, the Upper Ruins on its cloud, and the Golden Belfry at the top
    giant_jack(b, rnd)
    upper_ruins(b, rnd)
    BX, BZ, PY = golden_belfry(b, rnd)
    # ---------------- people
    b.npc(BX, PY, BZ + 9, "enel", True)
    b.chest(TX, 1, TZ - 6, "sky_treasure", "south"); b.chest(BX + 7, PY + 1, BZ, "sky_treasure", "west")
    b.guards("sky_priest", ((CX - 20, CZ + 7), (CX + 20, CZ - 7), (TX, TZ + 20), (CX + 7, CZ + 20), (CX - 9, CZ + 20)))
    return b, 0
