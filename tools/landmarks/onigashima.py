"""Onigashima: Kaido's island. The giant horned Skull Dome rising out of a rocky mountain base: a flat-faced skull
with deep black eye sockets under a brow, an upside-down-heart nose, cheekbones and a curved row of great teeth with
the gate between the front teeth, two huge horns sweeping up from the temples and the wide flat rooftop on the
crown (the rooftop battle) that Kaido's castle opens onto through a huge pair of doors. Inside: the ground hall with
the War Beast pens, the Live Floor banquet hall with buildings lining its left and right walls, and Kaido's
five-storey castle against the far (back) wall of the dome, its treasure room holding the Road Poneglyph. Outside
a rocky island with crags, a torii path from the pier to the gate, watch pagodas and a storehouse.
~210 x 210, horns ~112. Ground = y 0, the skull faces -z."""
import math, random
from functools import lru_cache
from canvas import *

SID = "onigashima"
TITLE = "Onigashima (Skull Dome)"
CUTS = [30, 60]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

BONE = "minecraft:bone_block[axis=y]"
CALC = "minecraft:calcite"
DARK = "minecraft:black_concrete"
ROOF = "onepiece:wano_roof_tiles"
ROOF_ST = "onepiece:wano_roof_tile_stairs"
LAQ = "onepiece:wano_lacquer_planks"
LAQ_ST = "onepiece:wano_lacquer_stairs"
SHOJI = "onepiece:shoji_screen"
PLAST = "minecraft:white_concrete"
POST = "minecraft:dark_oak_log[axis=y]"
BEAM = "minecraft:dark_oak_planks"
BRACKET = "minecraft:dark_oak_stairs"
LANT = "onepiece:paper_lantern[hanging=false]"
HLANT = "onepiece:paper_lantern[hanging=true]"
RED = "minecraft:red_concrete"
PBB = "minecraft:polished_blackstone_bricks"
TOOTH = "minecraft:smooth_quartz"

CX, CZ = 110, 110          # island centre
SZ = 122                   # skull centre z
RXC, RYC, RZC, YC = 46, 50, 42, 50   # cranium: an ellipsoid cut flat at TOP (the rooftop)
TOP = 92                   # flat top of the skull (the rooftop battleground)
FACE_Y = 40                # below this the face drops straight down (cheeks, upper jaw, teeth)
ROCKS = ("minecraft:stone", "minecraft:andesite", "minecraft:tuff", "minecraft:blackstone", "minecraft:cobblestone", "minecraft:stone",
         "minecraft:basalt[axis=y]", "minecraft:andesite")


def _g(y):
    """How much the lower skull (sides and back) narrows toward the ground."""
    return 0.74 + 0.26 * math.sin(math.pi / 2 * min(1.0, max(0.0, y / FACE_Y)))


def _front40(dx):
    k = 1 - (dx / RXC) ** 2 - ((FACE_Y - YC) / RYC) ** 2
    return SZ + 2 - RZC * math.sqrt(k) if k > 0 else 1e9


def _wface(y):
    """Half width of the face below the eyes: upper jaw at the bottom, widening to the cheekbones."""
    if y <= 16: return 25
    if y <= 34: return 25 + (y - 16) / 18 * 14
    return 39 + (y - 34) / 6 * 3


def in_skull(x, y, z):
    if y < 0 or y > TOP: return False
    dx, dz = x - CX, z - SZ - 2
    if (dx / RXC) ** 2 + ((y - YC) / RYC) ** 2 + (dz / RZC) ** 2 <= 1: return True
    if y > FACE_Y: return False
    g = _g(y)
    if (dx / (RXC * g)) ** 2 + (dz / (RZC * g)) ** 2 <= 1: return True   # sides and back of the skull
    return abs(dx) <= _wface(y) and z >= _front40(dx) and dz <= 0       # the face: cheeks and the upper jaw


@lru_cache(maxsize=None)
def front_z(dx, y):
    """z of the skull's front surface at this column (1e9 when the column misses the skull)."""
    for z in range(SZ - RZC - 4, SZ + 3):
        if in_skull(CX + dx, y, z): return z
    return 1e9


def side_x(sx, y, z):
    """x of the skull's outer side surface (sx = -1 west, +1 east) on row (y, z), or None."""
    for k in range(RXC + 3, -1, -1):
        if in_skull(CX + sx * k, y, z): return CX + sx * k
    return None


def rock(x, y, z):
    return ROCKS[(x * 7349 ^ z * 2671 ^ y * 13) % len(ROCKS)]


def torii(b, cx, z, w=5, h=10):
    for x in (cx - w, cx + w):
        b.column(x, z, 1, h, RED, base="minecraft:polished_blackstone")
    for x in range(cx - w - 2, cx + w + 3): b.set(x, h, z, RED)
    for x in range(cx - w - 3, cx + w + 4): b.set(x, h + 2, z, "minecraft:black_concrete")
    b.set(cx - w - 4, h + 3, z, "minecraft:black_concrete"); b.set(cx + w + 4, h + 3, z, "minecraft:black_concrete")
    for x in range(cx - w + 1, cx + w): b.set(x, h + 1, z, "minecraft:black_concrete" if x == cx else AIR)
    b.set(cx, h + 1, z, RED)


def pagoda(b, x, z, hw, floors, y=1):
    for f in range(floors):
        w = hw - f
        y0 = y + f * 6
        b.walls(x - w, y0, z - w, x + w, y0 + 4, z + w, PLAST)
        for (px, pz) in ((x - w, z - w), (x + w, z - w), (x - w, z + w), (x + w, z + w)): b.column(px, pz, y0, y0 + 4, POST)
        for k in range(-w + 2, w - 1, 2):
            for (px, pz) in ((x + k, z - w), (x + k, z + w), (x - w, z + k), (x + w, z + k)): b.set(px, y0 + 2, pz, SHOJI)
        b.box(x - w + 1, y0 + 5, z - w + 1, x + w - 1, y0 + 5, z + w - 1, LAQ)
        b.pagoda_roof(x, z, w + 2, w + 2, y0 + 5, ROOF_ST, ROOF, layers=2)
    b.set(x, y + floors * 6 + 1, z, "minecraft:gold_block"); b.set(x, y + floors * 6 + 2, z, "minecraft:lightning_rod")
    b.set(x, y, z - hw, AIR); b.set(x, y + 1, z - hw, AIR)


def eave(b, x0, x1, z0, z1, top, depth=3):
    """Japanese castle eave round a tier whose wall top is y=top: tiles over the wall line, stairs stepping out and down,
    the corner tips turned up, and dark brackets under the eave."""
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
        if d == depth:  # turned-up tips at the four corners
            b.set(ex0, y + 1, ez0, stairs(ROOF_ST, "west", "top")); b.set(ex1, y + 1, ez0, stairs(ROOF_ST, "east", "top"))
            b.set(ex0, y + 1, ez1, stairs(ROOF_ST, "west", "top")); b.set(ex1, y + 1, ez1, stairs(ROOF_ST, "east", "top"))
    for x in range(x0 + 1, x1, 3):
        b.set(x, top - 1, z0 - 1, stairs(BRACKET, "south", "top")); b.set(x, top - 1, z1 + 1, stairs(BRACKET, "north", "top"))
    for z in range(z0 + 1, z1, 3):
        b.set(x0 - 1, top - 1, z, stairs(BRACKET, "east", "top")); b.set(x1 + 1, top - 1, z, stairs(BRACKET, "west", "top"))


def chidori(b, cx, z0, top, w, side=-1):
    """A triangular dormer gable (chidori-hafu) standing on the front eave of a tier, white face, gold finial.
    z0 = the wall line of that front; side = -1 for a front facing -z (north), +1 for one facing +z (south)."""
    for i in range(w + 1):
        y = top + 1 + i
        xa, xb = cx - w + i, cx + w - i
        for k in range(4):
            z = z0 + side * (2 - k)
            if xa == xb:
                b.set(xa, y, z, ROOF); continue
            b.set(xa, y, z, stairs(ROOF_ST, "east")); b.set(xb, y, z, stairs(ROOF_ST, "west"))
            for x in range(xa + 1, xb):
                b.set(x, y, z, AIR if k == 0 else PLAST if k == 1 else ROOF)
    b.set(cx, top + w + 2, z0 + side * 2, "minecraft:gold_block")
    b.set(cx, top + 2, z0 + side, LAQ)  # the hanging fish board under the apex


def tier(b, x0, x1, z0, z1, y0, h, floor=None, lower="minecraft:dark_oak_planks", sparse=False):
    """One storey of a Japanese castle: dark lower boards, white plaster, timber posts every 3, shoji windows with sills.
    sparse=True: a plain white storey (posts at the corners only) with single framed windows every 3 blocks."""
    if floor: b.box(x0 + 1, y0 - 1, z0 + 1, x1 - 1, y0 - 1, z1 - 1, floor)
    b.walls(x0, y0, z0, x1, y0 + h - 1, z1, PLAST)
    if lower: b.walls(x0, y0, z0, x1, y0 + 1, z1, lower)
    b.box(x0 + 1, y0, z0 + 1, x1 - 1, y0 + h - 1, z1 - 1, AIR)
    for x in range(x0, x1 + 1):
        b.set(x, y0 + h - 1, z0, BEAM); b.set(x, y0 + h - 1, z1, BEAM)
    for z in range(z0, z1 + 1):
        b.set(x0, y0 + h - 1, z, BEAM); b.set(x1, y0 + h - 1, z, BEAM)
    wy = y0 + 2 + (h - 5) // 2
    for (px, pz) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)): b.column(px, pz, y0, y0 + h - 2, POST)
    if not sparse:
        for x in range(x0, x1 + 1, 3):
            b.column(x, z0, y0, y0 + h - 2, POST); b.column(x, z1, y0, y0 + h - 2, POST)
        for z in range(z0, z1 + 1, 3):
            b.column(x0, z, y0, y0 + h - 2, POST); b.column(x1, z, y0, y0 + h - 2, POST)

    def window(x, y, z, f):  # f = the way the wall faces
        dx, dz = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}[f]
        b.set(x, y, z, SHOJI); b.set(x, y + 1, z, SHOJI)
        b.set(x + dx, y - 1, z + dz, stairs(BRACKET, OPP[f], "top"))
        if sparse: b.set(x, y + 2, z, BEAM); b.set(x, y - 1, z, BEAM)
    for x in range(x0 + 1, x1):
        if (x - x0) % 3 == 0 if not sparse else (x - x0) % 3 or x1 - x < 2: continue
        window(x, wy, z0, "north"); window(x, wy, z1, "south")
    for z in range(z0 + 1, z1):
        if (z - z0) % 3 == 0 if not sparse else (z - z0) % 3 or z1 - z < 2: continue
        window(x0, wy, z, "west"); window(x1, wy, z, "east")


def live_house(b, sx, z0, rnd):
    """A two-storey Wano building lining a side wall of the Live Floor, its front facing the middle of the hall."""
    xf = CX + sx * 30          # the street front
    xb = CX + sx * 37          # back, up against the dome wall
    z1 = z0 + 7
    lo, hi = min(xf, xb), max(xf, xb)

    def put(x, y, z, s):
        if in_skull(x, y, z) and b.get(x, y, z) in (None, AIR): b.set(x, y, z, s)
    for x in range(lo, hi + 1):
        for z in range(z0, z1 + 1):
            for y in range(25, 37):
                edge = x in (lo, hi) or z in (z0, z1)
                put(x, y, z, (POST if (z in (z0, z1) and x == xf) else PLAST) if edge else AIR)
            put(x, 30, z, BEAM)
    # shop front: open ground floor with a noren curtain, balcony with a red railing, shoji upstairs
    cloth = rnd.choice(("minecraft:purple_wool", "minecraft:red_wool", "minecraft:black_wool"))
    for z in range(z0 + 1, z1):
        for y in (25, 26, 27): b.set(xf, y, z, AIR)
        b.set(xf, 28, z, cloth); b.set(xf, 29, z, BEAM)
        b.set(xf, 32, z, SHOJI); b.set(xf, 33, z, SHOJI)
        b.set(xf - sx, 31, z, slab("minecraft:dark_oak_slab", "top")); b.set(xf - sx, 32, z, fence("dark_oak") if z % 2 else LAQ)
    b.set(xf - sx, 31, z0, slab("minecraft:dark_oak_slab", "top")); b.set(xf - sx, 31, z1, slab("minecraft:dark_oak_slab", "top"))
    for z in (z0, z1): b.column(xf, z, 25, 35, POST)
    # lean-to roof sloping down toward the street
    for k, x in enumerate(range(xf - sx * 2, xb + sx, sx)):
        y = 36 + min(3, k // 2)
        for z in range(z0 - 1, z1 + 2):
            if in_skull(x, y, z) and b.get(x, y, z) in (None, AIR):
                b.set(x, y, z, stairs(ROOF_ST, "east" if sx > 0 else "west") if k % 2 == 0 else ROOF)
    b.set(xf - sx * 2, 35, z0 + 3, HLANT)


def build():
    rnd = random.Random(42)
    b = B()
    # ---------------- the island: rocky ground with a ragged shore
    tops = ("minecraft:coarse_dirt", "minecraft:podzol", "minecraft:stone", "minecraft:andesite", "minecraft:blackstone", "minecraft:coarse_dirt", "minecraft:tuff")
    for x in range(0, 221):
        for z in range(0, 221):
            dx, dz = x - CX, z - CZ
            d = math.hypot(dx, dz); a = math.atan2(dz, dx)
            r = 97 + 5 * math.sin(3 * a + 1) + 3 * math.sin(7 * a)
            if d > r: continue
            edge = r - d
            top = 0 if edge > 6 else -1 if edge > 3 else -2
            for y in range(-6, top): b.set(x, y, z, "minecraft:stone")
            h = (x * 73856093 ^ z * 19349663) % 97
            b.set(x, top, z, tops[h % len(tops)] if edge > 3 else "minecraft:cobblestone")
    # crags along the shore
    for i in range(26):
        a = i / 26 * 2 * math.pi + rnd.uniform(-0.08, 0.08)
        if abs(math.atan2(math.sin(a + math.pi / 2), math.cos(a + math.pi / 2))) < 0.25: continue  # keep the pier open
        rr = rnd.uniform(80, 90)
        x, z = round(CX + rr * math.cos(a)), round(CZ + rr * math.sin(a))
        hgt = rnd.randint(8, 26)
        for y in range(0, hgt):
            rad = (1 - y / hgt) * rnd.uniform(3.5, 5.5) + 0.6
            b.cyl(x + (y // 6) % 2, z, rad, y, y, rnd.choice(("minecraft:stone", "minecraft:blackstone", "minecraft:basalt[axis=y]", "minecraft:tuff")))
    # dead trees and a few sakura near the path
    for i in range(70):
        a = rnd.uniform(0, 2 * math.pi); rr = rnd.uniform(62, 78)
        x, z = round(CX + rr * math.cos(a)), round(CZ + rr * math.sin(a))
        if abs(x - CX) < 12 and z < SZ: continue
        if rnd.random() < 0.3:
            h = rnd.randint(5, 8)
            for y in range(1, h): b.set(x, y, z, "onepiece:sakura_log[axis=y]")
            b.sphere(x, h, z, 3, "onepiece:sakura_leaves[distance=7,persistent=true,waterlogged=false]", ry=2)
        else:
            h = rnd.randint(4, 9)
            for y in range(1, h): b.set(x, y, z, "minecraft:spruce_log[axis=y]")
            for k in range(2):
                ax = rnd.choice((-1, 1)); az = rnd.choice((-1, 1))
                b.set(x + ax, h - 1 - k * 2, z, "minecraft:spruce_log[axis=x]"); b.set(x + ax * 2, h - k * 2, z + az, "minecraft:spruce_log[axis=x]")
    # ---------------- the Skull Dome
    def mat(x, y, z):
        h = (x * 7 + y * 13 + z * 5 + (x * y) % 11) % 23
        if y < 14 and h < 5: return "minecraft:diorite"   # weathered toward the rocks at its foot
        return CALC if h < 4 else "minecraft:smooth_quartz" if h < 6 else BONE
    ins = b.shape(in_skull, CX - RXC - 1, 0, SZ - RZC - 4, CX + RXC + 1, TOP, SZ + RZC + 3, mat, interior=AIR)
    # the rocky mountain the skull sits in: rock under the overhang of the sides and back, scree sloping away from it
    low = {}
    for (x, y, z) in ins:
        if y < low.get((x, z), 999): low[(x, z)] = y

    def front_zone(x, z): return abs(x - CX) <= 27 and z < SZ - 14
    skirt = {}
    for (x, z), yl in low.items():
        if yl <= 1 or front_zone(x, z): continue
        a = math.atan2(z - SZ, x - CX)
        hmax = min(27, max(14, int(18 + 6 * math.sin(3 * a + 1) + 3 * math.sin(7 * a + 2))))  # high enough that no deep, dark hollow is left under the bulge
        top = min(yl - 1, hmax)
        for y in range(1, top + 1): b.set(x, y, z, rock(x, y, z))
        skirt[(x, z)] = top
    dist = {k: 0 for k in skirt}
    frontier = list(skirt)
    hgt = dict(skirt)
    for step in range(1, 14):
        nxt = []
        for (x, z) in frontier:
            for (ddx, ddz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + ddx, z + ddz)
                if q in dist or q in low or front_zone(*q): continue
                dist[q] = step; hgt[q] = hgt[(x, z)]; nxt.append(q)
        frontier = nxt
    for (x, z), d in dist.items():
        if d == 0: continue
        n = ((x * 92821 ^ z * 68917) % 7) - 3
        h = int(hgt[(x, z)] * (1 - d / 14) ** 1.6) + n
        for y in range(1, h + 1): b.set(x, y, z, rock(x, y, z))
    # eye sockets: big black hollows under a heavy brow (sunk 5 deep, so daylight still reaches their floor)
    EY, ER = 57, 13
    for ex in (CX - 20, CX + 20):
        for x in range(ex - ER, ex + ER + 1):
            for y in range(EY - ER, EY + ER + 1):
                rr = math.hypot(x - ex, (y - EY) * 1.15) / ER
                if rr > 1: continue
                fz = front_z(x - CX, y)
                if fz > 1e8: continue
                deep = 2 + int(round(3.5 * math.sqrt(1 - rr * rr)))
                for z in range(fz, fz + deep): b.set(x, y, z, AIR)
                b.set(x, y, fz + deep, DARK)
                b.set(x, y, fz + deep + 1, DARK)
        b.set(ex, EY, front_z(ex - CX, EY) + 6, "minecraft:red_stained_glass")  # a glint deep in the socket
    for dx in range(-35, 36):
        yb = EY + 12 + (1 if 12 <= abs(dx) <= 28 else 0)
        for y in (yb, yb + 1):
            fz = front_z(dx, y)
            if fz < 1e8 and b.get(CX + dx, y, fz) not in (None, AIR, DARK): b.set(CX + dx, y, fz - 1, CALC)
    # nose: an upside-down heart, pointed at the top, two lobes at the bottom
    def in_nose(dx, y):
        X, Y = dx / 6.6, (36 - y) / 7.6
        return (X * X + Y * Y - 1) ** 3 - X * X * Y ** 3 <= 0
    for y in range(25, 46):
        for dx in range(-10, 11):
            if not in_nose(dx, y): continue
            fz = front_z(dx, y)
            if fz > 1e8: continue
            rim = not all(in_nose(dx + a, y + c) for a, c in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            for z in range(fz - 1, fz + 2): b.set(CX + dx, y, z, AIR)
            b.set(CX + dx, y, fz + 2, DARK)  # a black back wall 3 deep, joined to the face by a black lining round the rim
            if rim: b.set(CX + dx, y, fz + 1, DARK)
    # the upper jaw: a curved row of great teeth with the gate between the front teeth
    for dx in range(-25, 26):
        for y in range(1, 18):
            fz = front_z(dx, y)
            if fz > 1e8: continue
            if abs(dx) <= 3:  # the gate
                for z in range(fz - 1, fz + 3): b.set(CX + dx, y, z, AIR)
                continue
            k = (abs(dx) - 4) % 6  # teeth 4 wide with 2 wide dark gaps
            if k >= 4 or (y == 1 and k in (0, 3)) or (y == 2 and k in (0, 3) and abs(dx) > 9):
                b.set(CX + dx, y, fz, AIR); b.set(CX + dx, y, fz + 1, DARK)
            else:
                b.set(CX + dx, y, fz, TOOTH); b.set(CX + dx, y, fz - 1, TOOTH)
        for y in (18, 19):  # gum ridge above the teeth
            fz = front_z(dx, y)
            if fz < 1e8: b.set(CX + dx, y, fz - 1, CALC)
    for x in range(CX - 3, CX + 4):
        for y in (16, 17): b.set(x, y, front_z(0, y), DARK)
    # cheekbones: a ridge under each eye that runs back along the side of the skull
    for sx in (-1, 1):
        for dx in range(26, 40):
            for y in (37, 38, 39):
                fz = front_z(sx * dx, y)
                if fz < 1e8: b.set(CX + sx * dx, y, fz - 1, CALC)
        for z in range(SZ - 28, SZ - 10):
            for y in (36, 37, 38, 39):
                xs = side_x(sx, y, z)
                if xs is None: continue
                b.set(xs + sx, y, z, CALC if y in (37, 38) else BONE)
                if y in (37, 38) and z < SZ - 4: b.set(xs + 2 * sx, y, z, CALC)
    # horns sweeping up from the temples
    for sx in (-1, 1):
        for i in range(-12, 44):  # (i < 0: the root of the horn, blending into the temple)
            t = i / 43
            x = CX + sx * (38 + 18 * math.sin(t * math.pi * 0.55))
            y = 74 + 36 * t
            z = SZ - 2 - 9 * t ** 2
            r = 8.5 * (1 - max(0.0, t)) + 1.0
            hm = "minecraft:smooth_sandstone" if t > 0.75 else BONE if i % 3 else CALC
            cx_, cy_, cz_ = round(x), round(y), round(z)
            for hx in range(int(cx_ - r) - 1, int(cx_ + r) + 2):  # only outside the dome: the horn never pokes into the hall
                for hy in range(int(cy_ - r) - 1, int(cy_ + r) + 2):
                    for hz in range(int(cz_ - r) - 1, int(cz_ + r) + 2):
                        if (hx - cx_) ** 2 + (hy - cy_) ** 2 + (hz - cz_) ** 2 <= r * r and not in_skull(hx, hy, hz): b.set(hx, hy, hz, hm)
    # ---------------- inside: ground hall, Live Floor
    for x in range(CX - 46, CX + 47):
        for z in range(SZ - 42, SZ + 43):
            if in_skull(x, 1, z) and b.get(x, 1, z) == AIR: b.set(x, 0, z, "minecraft:polished_blackstone")
            if in_skull(x, 24, z) and b.get(x, 24, z) == AIR and z > front_z(x - CX, 24) + 2:
                b.set(x, 24, z, "minecraft:dark_oak_planks" if (x + z) % 2 else "minecraft:spruce_planks")
    # stair from the gate up to the Live Floor
    b.stairs_up(CX - 4, 1, SZ - 18, 24, "minecraft:polished_blackstone_brick_stairs", "south", w=9, clear=4)
    for z in range(SZ - 18, SZ + 6):
        b.set(CX - 5, (z - (SZ - 18)) + 2, z, wall("minecraft:polished_blackstone_brick_wall")); b.set(CX + 5, (z - (SZ - 18)) + 2, z, wall("minecraft:polished_blackstone_brick_wall"))
    # war beast pens on the ground floor
    for sx in (-1, 1):
        for k in range(3):
            px = CX + sx * 22; pz = SZ - 14 + k * 12
            b.walls(px - 5, 1, pz - 4, px + 5, 5, pz + 4, "minecraft:iron_bars")
            b.box(px - 4, 0, pz - 3, px + 4, 0, pz + 3, "minecraft:hay_block[axis=y]")
    for (x, z) in ((CX - 12, SZ - 26), (CX + 12, SZ - 26), (CX - 30, SZ + 4), (CX + 30, SZ + 4)):
        b.set(x, 1, z, CAMPFIRE)
    # Live Floor: banquet tables, lanterns, sake, and buildings lining the left and right walls
    for x in range(CX - 26, CX + 27, 8):
        for z in range(SZ - 22, SZ + 9, 7):
            if abs(x - CX) < 8 and z < SZ + 8: continue
            if b.get(x, 24, z) != AIR and b.get(x, 24, z) is not None:
                b.table_set(x, 25, z, "dark_oak", cloth="red")
    for x in range(CX - 28, CX + 29, 6):
        for z in range(SZ - 26, SZ + 9, 10):
            if b.get(x, 24, z) not in (None, AIR) and b.get(x, 25, z) in (None, AIR):
                b.set(x, 25, z, fence("dark_oak")); b.set(x, 26, z, fence("dark_oak")); b.set(x, 27, z, LANT)
    for i in range(14):
        x = CX + rnd.randint(-28, 28); z = SZ + rnd.randint(-20, 8)
        if b.get(x, 24, z) not in (None, AIR) and b.get(x, 25, z) in (None, AIR): b.set(x, 25, z, "onepiece:sake_barrel[axis=y]")
    for sx in (-1, 1):
        for z0 in (SZ - 22, SZ - 13, SZ - 4):
            live_house(b, sx, z0, rnd)
    # ---------------- Kaido's castle, built against the far wall of the dome, five storeys up to the rooftop
    # (the sixth, top storey stands on the fifth and carries the stair tower that runs up into the dome's crown)
    tiers = ((22, SZ + 11, SZ + 33, 25, 12), (18, SZ + 14, SZ + 32, 38, 9), (14, SZ + 17, SZ + 31, 48, 8),
             (11, SZ + 19, SZ + 30, 57, 7), (8, SZ + 21, SZ + 29, 65, 6), (6, SZ + 22, SZ + 28, 72, 6))
    for i, (hw, z0, z1, y0, h) in enumerate(tiers):
        tier(b, CX - hw, CX + hw, z0, z1, y0, h, floor=None if i == 0 else "onepiece:tatami")
        top = y0 + h - 1
        if i < len(tiers) - 1:
            b.box(CX - hw, top + 1, z0, CX + hw, top + 1, z1, ROOF)
            eave(b, CX - hw, CX + hw, z0, z1, top, depth=3)
        if i in (1, 3):
            chidori(b, CX, z0, top, 4 if i == 1 else 3)
    hw, z0, z1, y0, h = tiers[-1]
    b.hip_roof(CX - hw, z0, CX + hw, z1, y0 + h, ROOF_ST, ROOF, overhang=3)
    ridge = y0 + h + (z1 - z0 + 6) // 2 + 1
    for sx in (-1, 1):  # golden shachihoko at the ends of the ridge
        b.set(CX + sx * 3, ridge, SZ + 25, "minecraft:gold_block"); b.set(CX + sx * 3, ridge + 1, SZ + 25, "minecraft:gold_block")
        b.set(CX + sx * 3, ridge + 2, SZ + 25, stairs("minecraft:smooth_sandstone_stairs", "east" if sx < 0 else "west"))
    # the main gate of the castle onto the Live Floor, with the name board over it
    f0 = tiers[0][1]
    for x in range(CX - 3, CX + 4):
        for y in range(25, 29): b.set(x, y, f0, AIR)
    for y in range(25, 30): b.set(CX - 4, y, f0 - 1, LAQ); b.set(CX + 4, y, f0 - 1, LAQ)
    for x in range(CX - 4, CX + 5): b.set(x, 29, f0 - 1, LAQ)
    b.box(CX - 11, 30, f0 - 1, CX + 11, 34, f0 - 1, "minecraft:black_concrete")
    b.text(CX + 9, 30, f0 - 2, "KAIDO", "minecraft:gold_block", step=-1)  # faces the hall (-z), so it runs from high x
    for x in (CX - 8, CX + 8): b.set(x, 25, f0 - 2, LANT)
    # the treasure room (third storey) with the Road Poneglyph
    t3 = tiers[2]
    b.box(CX - 1, t3[3], t3[2] - 3, CX + 1, t3[3], t3[2] - 1, "minecraft:polished_blackstone")
    b.set(CX, t3[3] + 1, t3[2] - 2, "onepiece:poneglyph"); b.set(CX, t3[3] + 2, t3[2] - 2, "onepiece:poneglyph")
    for (dx, dz) in ((-9, 4), (9, 4), (-9, 10), (9, 10)): b.set(CX + dx, t3[3], t3[1] + dz, "minecraft:gold_block")
    # the climb: one ladder up through every storey of the castle and out onto the rooftop
    LX, LZ = CX, SZ + 24
    for y in range(25, TOP + 2):
        b.set(LX, y, LZ + 1, PBB); b.set(LX, y, LZ, ladder("north"))
    # the castle's top: a stair tower rises from the top storey through its roof and joins the crown of the dome, so
    # the climb stays inside the castle all the way and comes out through a hatch in the gatehouse floor on the roof.
    # White plaster on a dark plinth, dark posts at the corners, beam rings, shoji windows and a small eave halfway up.
    t6 = tiers[-1]
    tx0, tx1, tz0, tz1 = CX - 2, CX + 2, LZ - 3, LZ + 1
    ty0 = t6[3] + t6[4]                      # from the top storey's ceiling (the base of its roof) up
    for y in range(ty0, TOP + 1):
        for x in range(tx0, tx1 + 1):
            for z in range(tz0, tz1 + 1):
                if not (in_skull(x, y, z) and in_skull(x, y + 1, z)): continue   # stop under the dome shell
                edge = x in (tx0, tx1) or z in (tz0, tz1)
                if (x, z) == (LX, LZ): b.set(x, y, z, ladder("north")); continue
                if (x, z) == (LX, LZ + 1): b.set(x, y, z, PBB); continue
                if not edge: b.set(x, y, z, AIR); continue
                corner = x in (tx0, tx1) and z in (tz0, tz1)
                k = y - ty0
                if corner: s = POST
                elif k <= 1: s = BEAM
                elif k % 5 == 0: s = BEAM
                elif k % 5 in (2, 3) and (x == CX or z == LZ - 1) and z != tz1: s = SHOJI
                else: s = PLAST
                b.set(x, y, z, s)
    eave(b, tx0, tx1, tz0, tz1, ty0 + 10, depth=1)   # a tiled cornice round the tower just under the dome
    # ---------------- the rooftop: the wide flat crown of the skull, and the huge doors from the castle
    gz0, gz1 = SZ + 16, SZ + 25
    for x in range(CX - 8, CX + 9):
        for z in range(gz0 - 1, gz1 + 1):
            b.set(x, TOP, z, PBB if b.get(x, TOP, z) in (None, AIR) else b.get(x, TOP, z))
            y = TOP - 1
            while y > TOP - 8 and not in_skull(x, y, z) and b.get(x, y, z) in (None, AIR):
                b.set(x, y, z, BONE); y -= 1
    b.walls(CX - 7, TOP + 1, gz0, CX + 7, TOP + 8, gz1, PLAST)
    b.walls(CX - 7, TOP + 1, gz0, CX + 7, TOP + 2, gz1, "minecraft:dark_oak_planks")
    b.box(CX - 6, TOP + 1, gz0 + 1, CX + 6, TOP + 8, gz1 - 1, AIR)
    for (px, pz) in ((CX - 7, gz0), (CX + 7, gz0), (CX - 7, gz1), (CX + 7, gz1), (CX - 7, (gz0 + gz1) // 2), (CX + 7, (gz0 + gz1) // 2)):
        b.column(px, pz, TOP + 1, TOP + 8, POST)
    for x in range(CX - 7, CX + 8): b.set(x, TOP + 8, gz0, BEAM); b.set(x, TOP + 8, gz1, BEAM)
    for x in range(CX - 3, CX + 4):  # the huge doorway
        for y in range(TOP + 1, TOP + 8): b.set(x, y, gz0, AIR)
    for y in range(TOP + 1, TOP + 9): b.set(CX - 4, y, gz0 - 1, LAQ); b.set(CX + 4, y, gz0 - 1, LAQ)
    for x in range(CX - 4, CX + 5): b.set(x, TOP + 8, gz0 - 1, LAQ)
    for sx in (-1, 1):  # the two great door leaves swung open against the front wall, studded with gold
        for k in range(1, 4):
            for y in range(TOP + 1, TOP + 8):
                b.set(CX + sx * (4 + k), y, gz0 - 1, "minecraft:gold_block" if (y - TOP) % 3 == 0 and k == 2 else "minecraft:dark_oak_planks")
    b.set(LX, TOP + 1, LZ + 1, PBB); b.set(LX, TOP + 1, LZ, ladder("north"))
    eave(b, CX - 7, CX + 7, gz0, gz1, TOP + 8, depth=2)
    b.hip_roof(CX - 7, gz0, CX + 7, gz1, TOP + 9, ROOF_ST, ROOF, overhang=0)
    for sx in (-1, 1): b.column(CX + sx * 2, (gz0 + gz1) // 2, TOP + 14, TOP + 14, "minecraft:gold_block")
    for (x, z) in ((CX - 14, SZ - 16), (CX + 14, SZ - 16)): b.set(x, TOP + 1, z, LANT)
    # ---------------- outside: pier, torii path, watch pagodas, storehouse
    gate_z = int(front_z(0, 10))
    for z in range(4, gate_z):
        for x in range(CX - 4, CX + 5):
            if b.get(x, 0, z) not in (None,): b.set(x, 0, z, "minecraft:stone_bricks" if (x + z) % 3 else "minecraft:cracked_stone_bricks")
        b.set(CX - 5, 1, z, "minecraft:stone_brick_wall") if z % 3 == 0 else None
        b.set(CX + 5, 1, z, "minecraft:stone_brick_wall") if z % 3 == 0 else None
    for z in range(20, gate_z - 8, 9): torii(b, CX, z)
    for z in range(-12, 12):  # pier out into the sea
        for x in range(CX - 4, CX + 5): b.set(x, 0, z, "minecraft:dark_oak_planks")
        if z % 4 == 0:
            for x in (CX - 5, CX + 5):
                for y in range(-6, 2): b.set(x, y, z, "minecraft:dark_oak_log[axis=y]")
                b.set(x, 2, z, LANT)
    for (x, z) in ((CX - 58, CZ - 40), (CX + 58, CZ - 40), (CX - 62, CZ + 44), (CX + 62, CZ + 44)):
        pagoda(b, x, z, 4, 3)
    # treasure storehouse (kura)
    kx, kz = CX + 60, CZ + 4
    b.walls(kx - 6, 1, kz - 8, kx + 6, 9, kz + 8, PLAST); b.walls(kx - 6, 1, kz - 8, kx + 6, 2, kz + 8, "minecraft:polished_blackstone_bricks")
    b.box(kx - 5, 0, kz - 7, kx + 5, 0, kz + 7, "minecraft:dark_oak_planks")
    b.gable_roof(kx - 7, kz - 9, kx + 7, kz + 9, 10, ROOF_ST, ROOF)
    b.set(kx - 6, 1, kz, AIR); b.set(kx - 6, 2, kz, AIR)
    b.chest(kx + 3, 1, kz - 5, "hard", "west")
    for k in range(6): b.set(kx + 4, 1, kz - 3 + k, BARREL)
    # ---------------- people
    b.npc(CX, TOP + 1, SZ - 10, "kaido", True)
    b.guards("headliner", ((CX - 16, SZ - 8), (CX + 16, SZ - 8), (CX - 8, SZ + 6), (CX + 8, SZ + 6)), y=25)
    b.guards("gifter", ((CX - 6, gate_z - 4), (CX + 6, gate_z - 4), (CX - 14, SZ - 30), (CX + 14, SZ - 30)))
    b.guards("gifter", ((CX - 20, SZ - 2), (CX + 20, SZ - 2), (CX - 6, 30), (CX + 6, 30)))
    b.guards("war_beast", ((CX - 22, SZ - 2), (CX + 22, SZ - 2)))
    t5 = tiers[4]
    b.chest(CX - 4, t5[3], t5[1] + 5, "legendary", "north")
    b.chest(CX - 4, t3[3], t3[2] - 2, "hard", "north"); b.chest(CX + 4, t3[3], t3[2] - 2, "hard", "north")
    # ---------------- furnished rooms
    import interiors as I
    for (hw, z0, z1, y0, h), kind in zip(tiers, ("hall", "dining", "treasure", "throne", "bedroom", "shrine")):
        I.furnish(b, CX - hw + 1, y0, z0 + 1, CX + hw - 1, z1 - 1, h - 2, kind, "kaido")
        if y0 > 25 and b.get(LX, y0 - 1, LZ) != ladder("north"):   # the shrine lays tatami over its floor: keep the ladder hole
            b.set(LX, y0 - 1, LZ, ladder("north")); b.set(LX, y0 - 1, LZ + 1, PBB)
    r = I.Room(b, CX - 34, 1, SZ - 36, CX + 34, SZ + 36, 22, "kaido", random.Random(11))
    r.scatter(("onepiece:sake_barrel[axis=y]", "minecraft:barrel[facing=up,open=false]", "minecraft:bone_block[axis=y]", "minecraft:skeleton_skull[rotation=4]",
               "onepiece:cannon[facing=south]", "minecraft:hay_block[axis=y]", "onepiece:paper_lantern[hanging=false]"), 70)
    r = I.Room(b, CX - 28, 25, SZ - 30, CX + 28, SZ + 8, 20, "kaido", random.Random(12))
    r.scatter(("onepiece:sake_barrel[axis=y]", "onepiece:feast_table[facing=north]", "minecraft:cake", I.candle_str("red", 3), "onepiece:paper_lantern[hanging=false]"), 50)
    I.furnish(b, kx - 5, 1, kz - 7, kx + 5, kz + 7, 8, "treasure", "kaido")
    for (x, z) in ((CX - 58, CZ - 40), (CX + 58, CZ - 40), (CX - 62, CZ + 44), (CX + 62, CZ + 44)):
        I.furnish(b, x - 3, 1, z - 3, x + 3, z + 3, 4, "shrine", "wano", lit=False)
    return b, 0
