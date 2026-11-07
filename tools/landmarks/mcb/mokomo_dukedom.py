"""Mokomo Dukedom v2 on Zou, redesigned with the Minecraft Builder skill: the Mink kingdom on the back of Zunesha, the
thousand-year elephant that walks the sea.

The whole island is Zunesha: a long grey back of wrinkled skin rising from the sea like a cliff, four legs wading in
the water, the great head at the north end with fan ears, curving tusks and the trunk reaching down into the sea, a
little tail at the south. On the back grows the Whale Forest of giant trees, and at its heart the Whale Tree, whose
trunk bends upward like a baleen whale with its head in the canopy: inside it the Duke's palace rooms and, in the tail
at its foot, the secret room with the Road Poneglyph under the Kozuki crest. West of it Kurau City, round houses
built into the rock outcrops and round mink houses with conical roofs round a market; east the Right Flank camp of the
Guardians, Nekomamushi's night camp of tents, a bonfire and paper lanterns. ~176 x 176. The back is y 20 above the sea.
(v2)

v3 (2026-10-30, audit: "Zunesha is hidden, it reads as a flat island"): Zunesha now stands clear of the sea. The back
is y 70 up on a rounded body with a belly at y ~34, four huge wrinkled legs wading in a round patch of sea (the front
left one lifted mid-stride, so he is walking), a big head with fan ears and long tusks, the trunk hanging down into
the water and a tail at the rump. A wooden stair winds round the back right leg from a landing at the waterline and
climbs a tunnel through the flank onto the back. 200 x 200."""
from mcb import terrain3 as T3
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, set_if_air, lamp_post, glyph, steady
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "mokomo_dukedom"
TITLE = "Mokomo Dukedom (Zou, on Zunesha's back)"
CUTS = [4, 22, 30, 50]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 200
TOP = 70
BELLY = 34                               # underside of the body at its middle
CX, CZ, A, B = 100, 114, 58, 60          # Zunesha's back: an oval
HEAD = (100, 46, TOP - 4)                # head centre (x, z, y)
WT = (100, 126)                           # the Whale Tree's foot (tail end)
CITY = (74, 104)
CAMP = (130, 90)
LEGS = ((CX - A * 0.66, CZ - B * 0.52, True), (CX + A * 0.66, CZ - B * 0.52, False),
        (CX - A * 0.64, CZ + B * 0.56, False), (CX + A * 0.64, CZ + B * 0.56, False))   # (x, z, lifted)
STAIR_LEG = 3
STAIR_TOP = (137, 110)                   # where the leg stair's tunnel comes out on the back
SKIN = "minecraft:tuff"
ZOU = [("minecraft:grass_block", 0.5), ("minecraft:moss_block", 0.14), ("minecraft:podzol", 0.12), ("onepiece:jungle_loam", 0.1),
       ("minecraft:rooted_dirt", 0.08), ("minecraft:coarse_dirt", 0.06)]
PATH = [("minecraft:dirt_path", 0.45), ("minecraft:coarse_dirt", 0.25), ("minecraft:packed_mud", 0.2), ("minecraft:rooted_dirt", 0.1)]
BARK = ["minecraft:stripped_spruce_wood[axis=y]", "minecraft:spruce_wood[axis=y]", "minecraft:mangrove_wood[axis=y]"]


def body_q(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    return ((X - CX) / A) ** 2 + ((Z - CZ) / B) ** 2 * (1 + 0.05 * np.sin(np.arctan2(Z - CZ, X - CX) * 3))


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    q = body_q(X, Z)
    dome = TOP - 8 + 30 * np.sqrt(np.clip(1 - q, 0, 1))
    plateau = TOP + NT.fbm(X, Z, 16011, 18) * 3 - 1
    h = np.minimum(dome, plateau)
    return np.where(q >= 1, -30, np.round(h))


def _belly(X, Z):
    q = body_q(X, Z)
    return np.round(BELLY + (TOP - 9 - BELLY) * (1 - np.sqrt(np.clip(1 - q, 0, 1))) ** 0.8)


X_, Z_ = np.arange(N)[:, None].astype(float), np.arange(N)[None, :].astype(float)
HMAP = _height(X_, Z_).astype(int)
QMAP = body_q(X_, Z_)
BMAP = _belly(X_, Z_).astype(int)


def height(X, Z):
    return HMAP[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def q_(X, Z):
    return QMAP[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def top_land(X, Z):
    """The plateau of the back (forest ground), not the skin flanks."""
    return (q_(X, Z) < 1) & (height(X, Z) >= TOP - 2)


def hy(x, z):
    return int(HMAP[min(max(int(x), 0), N - 1), min(max(int(z), 0), N - 1)])


def paths(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    m = np.zeros(np.broadcast(X, Z).shape, bool)
    for (a, b) in ((CITY, (WT[0], WT[1] + 14)), ((WT[0], WT[1] + 14), CAMP), (CITY, (CX, 72)), ((CX, 72), CAMP),
                   ((WT[0], WT[1] + 14), STAIR_TOP)):
        ax, az = a; bx, bz = b
        L = math.hypot(bx - ax, bz - az)
        t = np.clip(((X - ax) * (bx - ax) + (Z - az) * (bz - az)) / L ** 2, 0, 1)
        d = np.hypot(X - (ax + t * (bx - ax)), Z - (az + t * (bz - az)))
        m |= d <= 1.6 + 0.6 * NT.noise(X, Z, 16012, 5)
    m |= np.hypot(X - CITY[0], Z - CITY[1]) <= 7
    return m & top_land(X, Z)


# ------------------------------------------------------------------ Zunesha
def skin(bb, x1, y1, z1, x2, y2, z2, f):
    """Grey elephant skin with horizontal wrinkles and lighter / darker patches, painted wherever f(X, Y, Z)."""
    bb.fill_where(x1, y1, z1, x2, y2, z2, f, SKIN)
    bb.fill_where(x1, y1, z1, x2, y2, z2, lambda X, Y, Z: f(X, Y, Z) & ((Y + np.round(2 * NT.noise(X, Z, 16020, 9))) % 3 == 0) &
                  (NT.noise(X * 2, Z * 2, 16021, 3) > 0.35), "minecraft:polished_tuff")
    bb.fill_where(x1, y1, z1, x2, y2, z2, lambda X, Y, Z: f(X, Y, Z) & (NT.noise(X + Y, Z - Y, 16022, 6) > 0.72), "minecraft:stone")
    bb.fill_where(x1, y1, z1, x2, y2, z2, lambda X, Y, Z: f(X, Y, Z) & (NT.noise(X - Y, Z + Y, 16023, 7) > 0.84), "minecraft:andesite")


def leg_axis(lx, lz, lifted, y):
    """Centre of a leg at height y: straight down, or for the lifted leg swung forward (north) below the knee."""
    if not lifted:
        return lx, lz
    k = BELLY - 4                                  # knee
    if y >= k:
        return lx, lz - (k - y) * 0 - (BELLY + 6 - y) * 0.12
    return lx, lz - (BELLY + 6 - k) * 0.12 - (k - y) * 0.55


def leg_r(y, foot):
    return 11.5 - 1.6 * min(1, max(0, (y - foot) / 30.0)) + 1.6 * max(0, 1 - (y - foot) / 4.0)


def leg_stair(bb):
    """A plank landing at the waterline by the back right leg, a railed stair winding up round the leg to the belly,
    then a lit tunnel climbing north through the flank onto the back."""
    lx, lz, _ = LEGS[STAIR_LEG]
    Rh, top_y = 15.0, 44
    end = -math.pi / 2
    th0 = end - top_y / Rh
    # landing and mooring posts on the south-east side
    a0 = th0
    px, pz = lx + Rh * math.cos(a0), lz + Rh * math.sin(a0)
    bb.fill_where(int(px) - 8, 1, int(pz) - 8, int(px) + 8, 1, int(pz) + 8,
                  lambda X, Y, Z: (np.hypot(X - px, Z - pz) <= 7) & (np.hypot(X - lx, Z - lz) > 13), "minecraft:spruce_planks")
    for (dx, dz) in ((-6, -2), (6, 2), (-2, 6), (3, -6)):
        if math.hypot(px + dx - lx, pz + dz - lz) > 14:
            bb.fill(int(px) + dx, -10, int(pz) + dz, int(px) + dx, 2, int(pz) + dz, "minecraft:spruce_log[axis=y]")
    for y in range(1, top_y + 1):
        th = th0 + (y - 1) / Rh
        tx, tz = -math.sin(th), math.cos(th)
        f = ("east" if tx > 0 else "west") if abs(tx) > abs(tz) else ("south" if tz > 0 else "north")
        for w in (-1.0, 0.0, 1.0):
            x, z = round(lx + (Rh + w) * math.cos(th)), round(lz + (Rh + w) * math.sin(th))
            bb.set(x, y, z, f"minecraft:spruce_stairs[facing={f},half=bottom]")
            bb.fill(x, y + 1, z, x, y + 4, z, AIR)
            bb.set(x, y - 1, z, "minecraft:spruce_planks") if y > 1 else None
        x, z = round(lx + (Rh + 2) * math.cos(th)), round(lz + (Rh + 2) * math.sin(th))
        bb.set(x, y + 1, z, "minecraft:spruce_fence")
        if y % 5 == 0:                                        # brackets into the leg
            for t in range(10, 15):
                bb.set(round(lx + t * math.cos(th)), y - 2, round(lz + t * math.sin(th)), "minecraft:spruce_log[axis=y]")
        if y % 9 == 0:
            bb.fill(x, y + 2, z, x, y + 2, z, "onepiece:paper_lantern[hanging=false]")
    # the tunnel: 3 wide, straight north, one up per block, until it reaches the surface of the back
    x0 = round(lx)
    z = round(lz - Rh)
    y = top_y + 1
    while True:
        bb.fill(x0 - 1, y, z, x0 + 1, y, z, "minecraft:spruce_stairs[facing=north,half=bottom]")
        bb.fill(x0 - 1, y - 1, z, x0 + 1, y - 1, z, "minecraft:spruce_planks")
        bb.fill(x0 - 1, y + 1, z, x0 + 1, y + 4, z, AIR)
        bb.fill(x0 - 2, y + 5, z, x0 + 2, y + 5, z, "minecraft:stripped_spruce_log[axis=x]") if y % 6 == 0 else None
        if y > hy(x0, z) or z <= STAIR_TOP[1]:
            break
        y += 1
        z -= 1
    # a timber gate frame where it comes out
    g = hy(x0, z - 1) + 1
    for dx in (-2, 2):
        bb.fill(x0 + dx, g, z - 1, x0 + dx, g + 5, z - 1, "minecraft:spruce_log[axis=y]")
    bb.fill(x0 - 3, g + 6, z - 1, x0 + 3, g + 6, z - 1, "minecraft:stripped_spruce_log[axis=x]")
    bb.set(x0, g + 5, z - 1, "onepiece:paper_lantern[hanging=true]")


def zunesha(bb):
    # the sea: a round patch of water only inside a wobbly rim, the feet standing in it
    legmask = np.zeros((N, N), bool)
    for (lx, lz, lifted) in LEGS:
        if not lifted:
            legmask |= np.hypot(X_ - lx, Z_ - lz) <= 13.5
    T3.sea(bb, N, legmask, 100, 100, 97, 16019, deep=-16, shelf=10, y_min=-24)
    # the body: skin between the belly and the back
    skin(bb, 0, BELLY - 2, 0, N - 1, TOP + 24, N - 1,
         lambda X, Y, Z: (QMAP[X.astype(int).clip(0, N - 1), Z.astype(int).clip(0, N - 1)] < 1) &
                         (Y <= height(X, Z)) & (Y >= BMAP[X.astype(int).clip(0, N - 1), Z.astype(int).clip(0, N - 1)]))
    # four legs: three planted in the sea, the front left one lifted mid-stride
    for (lx, lz, lifted) in LEGS:
        foot = 8 if lifted else -16
        for y in range(foot, BELLY + 14):
            x, z = leg_axis(lx, lz, lifted, y)
            r = leg_r(y, foot if lifted else 0)
            R_ = int(r) + 2
            skin(bb, int(x) - R_, y, int(z) - R_, int(x) + R_, y, int(z) + R_,
                 lambda X, Y, Z, x=x, z=z, r=r: np.hypot(X - x, Z - z) <= r + 0.6 * np.sin(np.arctan2(Z - z, X - x) * 5 + Y * 0.3))
        # toenails: pale half-moons round the front of the foot
        fy = foot if lifted else 0
        x, z = leg_axis(lx, lz, lifted, fy)
        r = leg_r(fy, fy)
        for a in (-0.7, -0.25, 0.25, 0.7):
            t = -math.pi / 2 + a
            nx, nz = round(x + (r - 0.5) * math.cos(t)), round(z + (r - 0.5) * math.sin(t))
            bb.fill(nx - 1, fy + 1, nz, nx + 1, fy + 3, nz, "minecraft:calcite")
        if lifted:                                  # water dripping off the raised foot
            bb.fill_where(int(x) - 12, fy - 1, int(z) - 12, int(x) + 12, fy - 1, int(z) + 12,
                          lambda X, Y, Z, x=x, z=z: np.hypot(X - x, Z - z) <= r - 1, "minecraft:mud")
    leg_stair(bb)
    # the tail at the south, hanging down the rump
    tz = CZ + B
    for i in range(30):
        bb.fill(CX - 1 + (i > 18), TOP - 12 - i, tz - 4 + i // 3, CX + 1 - (i > 24), TOP - 12 - i, tz - 2 + i // 3, SKIN)
    bb.fill(CX - 2, TOP - 46, tz + 6, CX + 2, TOP - 41, tz + 9, "minecraft:gray_wool")
    # the head
    hx, hz, hy0 = HEAD
    head = lambda X, Y, Z: ((X - hx) / 24.0) ** 2 + ((Y - hy0) / 22.0) ** 2 + ((Z - hz) / 19.0) ** 2 <= 1
    skin(bb, hx - 25, hy0 - 23, hz - 20, hx + 25, hy0 + 23, hz + 20, head)
    # the neck joining head and body
    skin(bb, hx - 26, hy0 - 20, hz, hx + 26, hy0 + 18, hz + 30,
         lambda X, Y, Z: ((X - hx) / 25.0) ** 2 + ((Y - hy0 + 2) / 19.0) ** 2 <= 1)
    # brow ridge and eyes (looking north-ish, on the sides)
    for sx in (-1, 1):
        ex, ez, ey = hx + sx * 17, hz - 11, hy0 + 5
        bb.fill(ex - 1, ey, ez - 1, ex + 1, ey + 1, ez + 1, "minecraft:black_concrete")
        bb.fill(ex - 2, ey + 2, ez - 2, ex + 2, ey + 2, ez + 1, "minecraft:light_gray_terracotta")
    # the fan ears: huge flat discs out to each side, pink inside
    for sx in (-1, 1):
        ecx, ecz, ecy = hx + sx * 38, hz + 4, hy0 - 2
        ear = lambda X, Y, Z, ecx=ecx, ecz=ecz, ecy=ecy: (((X - ecx) / 18.0) ** 2 + ((Y - ecy) / 24.0) ** 2 <= 1) & \
                                                         (np.abs(Z - (ecz + (X - ecx) * sx * 0.25)) <= 1.2)
        skin(bb, ecx - 19, ecy - 25, ecz - 8, ecx + 19, ecy + 25, ecz + 10, ear)
        bb.fill_where(ecx - 19, ecy - 25, ecz - 8, ecx + 19, ecy + 25, ecz + 10,
                      lambda X, Y, Z, ecx=ecx, ecz=ecz, ecy=ecy: (((X - ecx) / 15.0) ** 2 + ((Y - ecy) / 20.5) ** 2 <= 1) &
                                                                  (np.abs(Z - (ecz + (X - ecx) * sx * 0.25) + 1) <= 0.6), "minecraft:pink_terracotta")
    # tusks: white, curving forward and up
    for sx in (-1, 1):
        for i in range(44):
            t = i / 43
            x = hx + sx * (9 + 5 * t)
            z = hz - 15 - 28 * t
            y = hy0 - 12 - 9 * math.sin(t * math.pi * 0.9) + 20 * t ** 2
            r = 3.4 - 2.3 * t
            bb.fill_where(int(x - 3), int(y - 3), int(z - 3), int(x + 3), int(y + 3), int(z + 3),
                          lambda X, Y, Z, x=x, y=y, z=z, r=r: (X - x) ** 2 + (Y - y) ** 2 + (Z - z) ** 2 <= r * r, "minecraft:bone_block[axis=y]")
    # the trunk: from the face down into the sea, curling at the end
    pts = []
    for i in range(120):
        t = i / 119
        z = hz - 17 - 20 * math.sin(t * math.pi * 0.5) + 6 * max(0, t - 0.85) / 0.15
        y = hy0 - 8 - (hy0 + 2) * t
        pts.append((hx + 2 * math.sin(t * 5), y, z, 8.0 - 4.5 * t))
    for (x, y, z, r) in pts:
        skin(bb, int(x - 9), int(y - 9), int(z - 9), int(x + 9), int(y + 9), int(z + 9),
             lambda X, Y, Z, x=x, y=y, z=z, r=r: (X - x) ** 2 + (Y - y) ** 2 + (Z - z) ** 2 <= r * r)
    return (hx - 58, 4, hx + 58, hz + 20)


# ------------------------------------------------------------------ the Whale Tree
def whale_tree(bb, tracker, audit, rng):
    """A trunk like a baleen whale bending upward: tail at the foot (south), body rising north, head up in the
    canopy. Hollow inside: the Duke's rooms on three floors, the Poneglyph room in the tail."""
    bx, bz = WT
    base = hy(bx, bz) + 1
    pts = []
    for i in range(90):
        t = i / 89
        y = base + 2 + 42 * t ** 1.5
        z = bz - 36 * math.sin(t * math.pi / 2) ** 0.9
        r = 4 + 8.5 * math.sin(math.pi * min(1.0, 0.1 + t * 0.95)) ** 0.9
        if t > 0.85:
            r *= 1 - (t - 0.85) * 2.2
        pts.append((bx, y, z, r))
    for (x, y, z, r) in pts:
        R = int(r) + 2
        bb.fill_where(int(x) - R, int(y) - R, int(z) - R, int(x) + R, int(y) + R, int(z) + R,
                      lambda X, Y, Z, x=x, y=y, z=z, r=r: ((X - x) ** 2 + (Y - y) ** 2 + (Z - z) ** 2 <= r * r) &
                                                          (NT.noise(X * 2 + Y, Z * 2, 16030, 3) < 0.7), BARK[0])
        bb.fill_where(int(x) - R, int(y) - R, int(z) - R, int(x) + R, int(y) + R, int(z) + R,
                      lambda X, Y, Z, x=x, y=y, z=z, r=r: ((X - x) ** 2 + (Y - y) ** 2 + (Z - z) ** 2 <= r * r) &
                                                          (NT.noise(X * 2 + Y, Z * 2, 16030, 3) >= 0.7), BARK[1])
    # throat pleats: pale grooves along the underside (the south-facing belly)
    for (x, y, z, r) in pts[20:75:2]:
        for k in (-4, -2, 0, 2, 4):
            if abs(k) < r - 1:
                bb.set(int(x) + k, int(y), int(round(z + math.sqrt(max(r * r - k * k, 0)))), "minecraft:stripped_birch_wood[axis=y]")
    # the head: a mouth line and an eye on each side
    hx, hy_, hz, hr = pts[80]
    for sx in (-1, 1):
        bb.fill(int(hx + sx * (hr - 0.5)), int(hy_) + 1, int(hz) - 1, int(hx + sx * (hr - 0.5)), int(hy_) + 2, int(hz), "minecraft:black_concrete")
    # the tail flukes spread flat on the ground either side of the foot
    for sx in (-1, 1):
        fx, fz = bx + sx * 8, bz + 5
        bb.fill_where(fx - 8, base, fz - 5, fx + 8, base + 2, fz + 5,
                      lambda X, Y, Z, fx=fx, fz=fz: (((X - fx) / 7.5) ** 2 + ((Z - fz - (X - fx) * sx * 0.3) / 3.5) ** 2 <= 1) &
                                                    (Y <= base + 1 + (np.abs(X - fx) < 4)), BARK[1])
    # roots splaying from the tail
    for a in range(0, 360, 40):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        for s in range(3, 14):
            x, z = int(round(bx + s * ca)), int(round(bz + s * sa))
            y = hy(x, z) + (1 if s < 9 else 0)
            bb.set(x, y, z, "minecraft:mangrove_wood[axis=y]")
            bb.set(x, y - 1, z, "minecraft:mangrove_wood[axis=y]")
    # the canopy over the head and long branches
    cx, cy, cz = int(hx), int(hy_) + 6, int(hz)
    for (dx, dz, dy, rr) in ((0, 0, 6, 13), (-14, 6, 0, 8), (14, 4, 1, 8), (0, -12, 2, 9), (0, 14, -2, 9), (-10, -8, 4, 7), (10, -8, 3, 7)):
        ox, oy, oz = cx + dx, cy + dy, cz + dz
        for s in range(0, 9):
            px, pz = int(round(cx + dx * s / 9)), int(round(cz + dz * s / 9))
            bb.set(px, cy + int(dy * s / 9), pz, "minecraft:spruce_wood[axis=y]")
        bb.fill_where(ox - rr - 1, oy - rr, oz - rr - 1, ox + rr + 1, oy + rr, oz + rr + 1,
                      lambda X, Y, Z, ox=ox, oy=oy, oz=oz, rr=rr: ((X - ox) ** 2 + ((Y - oy) * 1.7) ** 2 + (Z - oz) ** 2 <= rr * rr) &
                                                                  (NT.noise(X * 2 + Y, Z * 2, 16031, 2) > 0.2),
                      "minecraft:dark_oak_leaves[distance=7,persistent=true,waterlogged=false]", only_empty=True)
    # hollow inside the lower body
    for (x, y, z, r) in pts[4:60]:
        ri = r - 2.4
        if ri < 2:
            continue
        R = int(ri) + 1
        bb.fill_where(int(x) - R, int(y) - R, int(z) - R, int(x) + R, int(y) + R, int(z) + R,
                      lambda X, Y, Z, x=x, y=y, z=z, ri=ri: ((X - x) ** 2 + (Y - y) ** 2 + (Z - z) ** 2 <= ri * ri) & (Y >= base), AIR)
    # floors in the hollow every 6, furnished; a ladder shaft up the middle
    rooms = []
    for k, fy in enumerate(range(base, base + 30, 7)):
        reg = bb.get_region(bx - 14, fy, bz - 40, bx + 14, fy, bz + 12)[:, 0, :]
        ii, jj = np.nonzero(reg == 1)
        if len(ii) < 20:
            continue
        x1, x2 = bx - 14 + int(np.percentile(ii, 10)), bx - 14 + int(np.percentile(ii, 90))
        z1, z2 = bz - 40 + int(np.percentile(jj, 10)), bz - 40 + int(np.percentile(jj, 90))
        if k > 0:
            bb.fill_where(bx - 14, fy - 1, bz - 40, bx + 14, fy - 1, bz + 12, lambda X, Y, Z: True, "minecraft:spruce_planks", only_empty=False) if False else None
            fl = bb.get_region(bx - 14, fy - 1, bz - 40, bx + 14, fy - 1, bz + 12)[:, 0, :]
            for (a_, b_) in zip(*np.nonzero(fl == 1)):
                bb.set(bx - 14 + int(a_), fy - 1, bz - 40 + int(b_), "minecraft:spruce_planks")
        else:
            fl = bb.get_region(bx - 14, fy - 1, bz - 40, bx + 14, fy - 1, bz + 12)[:, 0, :]
            for (a_, b_) in zip(*np.nonzero(fl <= 1)):
                pass
        if x2 - x1 >= 4 and z2 - z1 >= 4:
            rooms.append(((x1, z1, x2, z2), fy, k))
    sz = None
    for (room, fy, k) in rooms:
        x1, z1, x2, z2 = room
        if sz is None:
            sz = (z1 + z2) // 2
    if sz is not None:
        top_floor = rooms[-1][1]
        for (room, fy, k) in rooms:
            x1, z1, x2, z2 = room
            zz = min(max(sz, z1 + 1), z2 - 1)
        bb.fill(bx - 1, base, sz - 1, bx + 1, top_floor + 2, sz + 1, AIR)
        bb.fill(bx, base, sz - 1, bx, top_floor, sz - 1, "minecraft:ladder[facing=south]")
        bb.fill(bx - 1, base, sz - 2, bx + 1, top_floor + 2, sz - 2, BARK[0])
    kinds = ["living", "library", "bedroom", "storage", "living"]
    for (room, fy, k) in rooms:
        x1, z1, x2, z2 = room
        if k == 0:
            continue
        P.furnish_room(bb, room, fy, kind=kinds[k % len(kinds)], height=5, seed=seed_of("whale", k), wood="spruce", tracker=tracker,
                       doors=[(bx, sz)] if sz else ())
        txt, ok = P.audit_props(bb, [room], fy, 5)
        if not ok:
            audit.append(txt)
    # the tail room: the Road Poneglyph under the Kozuki crest, lit by lanterns; the door in the tail
    bb.fill(bx - 1, base, bz - 4, bx + 1, base + 2, bz - 4, "onepiece:poneglyph")
    crest = [".#.#.#.", "#######", ".#####.", "..###.."]
    glyph(bb, crest, bx - 3, base + 7, bz - 4, "minecraft:red_concrete")
    for dx in (-3, 3):
        set_if_air(bb, bx + dx, base, bz - 3, "minecraft:lantern[hanging=false]")
    bb.fill(bx - 1, base, bz + 2, bx + 1, base + 3, bz + 14, AIR)
    bb.fill(bx - 1, base - 1, bz + 2, bx + 1, base - 1, bz + 14, "minecraft:spruce_planks")
    for dx in (-2, 2):
        bb.fill(bx + dx, base, bz + 10, bx + dx, base + 3, bz + 10, "minecraft:stripped_spruce_log[axis=y]")
        bb.set(bx + dx, base + 4, bz + 11, "onepiece:paper_lantern[hanging=false]") if False else None
    return (bx - 15, bz - 15, bx + 15, bz + 15)


# ------------------------------------------------------------------ Kurau City
def rock_house(bb, x, z, r, door, tracker, audit, seed):
    """A round house hollowed into a rock outcrop: the rock dome with grass on top, a round room inside, a door with a
    stone lintel and paper lanterns, round windows."""
    y = hy(x, z) + 1
    ROCK = lambda X, Y, Z: ((X - x) / r) ** 2 + ((Y - (y - 2)) / (r * 0.95)) ** 2 + ((Z - z) / r) ** 2 + 0.25 * NT.noise(X + Y, Z, seed, 3) <= 1
    bb.fill_where(x - r - 1, y - 3, z - r - 1, x + r + 1, y + r, z + r + 1, ROCK, "minecraft:stone")
    bb.fill_where(x - r - 1, y - 3, z - r - 1, x + r + 1, y + r, z + r + 1, lambda X, Y, Z: ROCK(X, Y, Z) & (NT.noise(X * 2, Z * 2 + Y, seed + 1, 3) > 0.55),
                  "minecraft:andesite")
    bb.fill_where(x - r - 1, y - 3, z - r - 1, x + r + 1, y + r, z + r + 1, lambda X, Y, Z: ROCK(X, Y, Z) & (NT.noise(X * 2 - Y, Z * 2, seed + 2, 3) > 0.75),
                  "minecraft:mossy_cobblestone")
    ri = r - 2
    bb.fill_where(x - ri, y, z - ri, x + ri, y + 4, z + ri, lambda X, Y, Z: np.hypot(X - x, Z - z) <= ri + 0.3, AIR)
    bb.fill_where(x - ri, y - 1, z - ri, x + ri, y - 1, z + ri, lambda X, Y, Z: np.hypot(X - x, Z - z) <= ri + 0.3, "minecraft:spruce_planks")
    # moss and grass on top of the rock
    reg = bb.get_region(x - r - 1, y, z - r - 1, x + r + 1, y + r + 1, z + r + 1)
    for (ix, iz) in zip(*np.nonzero((reg > 1).any(axis=1))):
        col = reg[ix, :, iz]
        k = int(np.nonzero(col > 1)[0].max())
        if k >= 4 and NT.noise(np.array([ix + x]), np.array([iz + z]), seed + 3, 3)[0] > 0.35:
            bb.set(x - r - 1 + int(ix), y + k, z - r - 1 + int(iz), "minecraft:moss_block")
    dx, dz = {"south": (0, 1), "north": (0, -1), "east": (1, 0), "west": (-1, 0)}[door]
    for s in range(ri, r + 2):
        bb.fill(x + dx * s, y, z + dz * s, x + dx * s, y + 2, z + dz * s, AIR)
    ex, ez = x + dx * (r - 1), z + dz * (r - 1)
    bb.set(ex, y, ez, f"minecraft:spruce_door[facing={door},half=lower,hinge=left]")
    bb.set(ex, y + 1, ez, f"minecraft:spruce_door[facing={door},half=upper,hinge=left]")
    bb.set(ex, y + 2, ez, "minecraft:polished_andesite")
    for s in (-1, 1):
        set_if_air(bb, ex + dx + dz * s * 2, y + 2, ez + dz + dx * s * 2, "onepiece:paper_lantern[hanging=false]") if False else None
    px, pz = x + dx * (r + 2) + dz * 2, z + dz * (r + 2) + dx * 2
    bb.fill(px, hy(px, pz) + 1, pz, px, hy(px, pz) + 3, pz, "minecraft:spruce_fence")
    bb.set(px, hy(px, pz) + 4, pz, "onepiece:paper_lantern[hanging=false]")
    for a in (60, 180, 300):
        t = math.radians(a + {"south": 90, "north": 270, "east": 0, "west": 180}[door])
        wx, wz = int(round(x + (ri + 1) * math.cos(t))), int(round(z + (ri + 1) * math.sin(t)))
        for s in range(0, 3):
            bb.set(int(round(x + (ri + 1 + s) * math.cos(t))), y + 2, int(round(z + (ri + 1 + s) * math.sin(t))), "minecraft:glass_pane")
    q = int(ri / 1.42)
    room = (x - q, z - q, x + q, z + q)
    P.furnish_room(bb, room, y, kind=["living", "kitchen", "bedroom", "storage"][seed % 4], height=4, seed=seed, wood="spruce", tracker=tracker,
                   doors=[(ex - dx, ez - dz)])
    txt, ok = P.audit_props(bb, [room], y, 4)
    if not ok:
        audit.append(txt)
    bb.set(x, y + 3, z, "onepiece:paper_lantern[hanging=true]")
    return (x - r - 3, z - r - 3, x + r + 3, z + r + 3)


def mink_house(bb, x, z, r, door, tracker, audit, seed):
    """A round mink house: mud-brick drum on a stone ring, timber posts, a conical roof with a finial."""
    y = hy(x, z) + 1
    bb.fill_where(x - r - 1, y - 3, z - r - 1, x + r + 1, y - 1, z + r + 1, lambda X, Y, Z: np.hypot(X - x, Z - z) <= r + 1.2, "minecraft:cobblestone")
    bb.fill_where(x - r, y, z - r, x + r, y + 4, z + r, lambda X, Y, Z: np.hypot(X - x, Z - z) <= r + 0.4, "minecraft:mud_bricks")
    bb.fill_where(x - r, y, z - r, x + r, y + 4, z + r, lambda X, Y, Z: (np.hypot(X - x, Z - z) <= r + 0.4) & (NT.noise(X + Y, Z, seed, 2) > 0.7),
                  "minecraft:packed_mud")
    bb.fill_where(x - r, y, z - r, x + r, y + 4, z + r, lambda X, Y, Z: np.hypot(X - x, Z - z) <= r - 0.8, AIR)
    bb.fill_where(x - r, y - 1, z - r, x + r, y - 1, z + r, lambda X, Y, Z: np.hypot(X - x, Z - z) <= r - 0.8, "minecraft:spruce_planks")
    for a in range(0, 360, 60):
        t = math.radians(a)
        px, pz = int(round(x + (r + 0.4) * math.cos(t))), int(round(z + (r + 0.4) * math.sin(t)))
        bb.fill(px, y, pz, px, y + 4, pz, "minecraft:stripped_spruce_log[axis=y]")
    for a in range(30, 360, 60):
        t = math.radians(a)
        bb.set(int(round(x + r * math.cos(t))), y + 2, int(round(z + r * math.sin(t))), "minecraft:glass_pane")
    P.cone_roof(bb, x, y + 5, z, r + 2, r + 4, "minecraft:spruce_planks", hollow=True)
    bb.fill_where(x - r - 2, y + 5, z - r - 2, x + r + 2, y + 5, z + r + 2, lambda X, Y, Z: np.abs(np.hypot(X - x, Z - z) - (r + 2)) < 0.7,
                  "minecraft:spruce_slab[type=top]")
    bb.set(x, y + r + 9, z, "minecraft:spruce_fence")
    bb.set(x, y + r + 10, z, "minecraft:lightning_rod")
    dx, dz = {"south": (0, r), "north": (0, -r), "east": (r, 0), "west": (-r, 0)}[door]
    bb.fill(x + dx, y, z + dz, x + dx, y + 2, z + dz, AIR)
    bb.set(x + dx, y, z + dz, f"minecraft:spruce_door[facing={door},half=lower,hinge=left]")
    bb.set(x + dx, y + 1, z + dz, f"minecraft:spruce_door[facing={door},half=upper,hinge=left]")
    q = int((r - 1) / 1.42)
    room = (x - q, z - q, x + q, z + q)
    P.furnish_room(bb, room, y, kind=["bedroom", "living", "kitchen"][seed % 3], height=4, seed=seed, wood="spruce", tracker=tracker,
                   doors=[(x + dx - np.sign(dx), z + dz - np.sign(dz))])
    txt, ok = P.audit_props(bb, [room], y, 4)
    if not ok:
        audit.append(txt)
    return (x - r - 3, z - r - 3, x + r + 3, z + r + 3)


def kurau_city(bb, tracker, audit, taken, rng):
    cx, cz = CITY
    # the market in the middle: stalls round a stone lantern
    y = hy(cx, cz) + 1
    bb.fill(cx, y, cz, cx, y + 2, cz, "minecraft:stone_bricks")
    bb.set(cx, y + 3, cz, "onepiece:paper_lantern[hanging=false]")
    for k, a in enumerate(range(0, 360, 60)):
        x, z = int(round(cx + 6 * math.cos(math.radians(a)))), int(round(cz + 6 * math.sin(math.radians(a))))
        yy = hy(x, z) + 1
        bb.set(x, yy, z, "minecraft:barrel[facing=up]")
        bb.fill(x + 1, yy, z, x + 1, yy + 2, z, "minecraft:spruce_fence")
        bb.set(x + 1, yy + 3, z, ("minecraft:orange_wool", "minecraft:yellow_wool", "minecraft:lime_wool")[k % 3])
        bb.set(x, yy + 3, z, ("minecraft:orange_wool", "minecraft:yellow_wool", "minecraft:lime_wool")[k % 3])
    taken.append((cx - 7, cz - 7, cx + 7, cz + 7))
    n = 0
    for ring, step, kind in ((14, 40, "mink"), (25, 26, "rock"), (36, 20, "mink"), (46, 16, "rock")):
        for a in range(0, 360, step):
            x, z = int(round(cx + ring * math.cos(math.radians(a + 13 * n % 20)))), int(round(cz + ring * math.sin(math.radians(a + 13 * n % 20))))
            r = int(rng.integers(6, 9)) if kind == "rock" else int(rng.integers(4, 6))
            xs, zs = np.array([x - r - 2, x + r + 2, x, x]), np.array([z, z, z - r - 2, z + r + 2])
            xi, zi = np.array([x - r, x + r, x, x, x]), np.array([z, z, z - r, z + r, z])
            if not top_land(xs, zs).all() or paths(xi, zi).any():
                continue
            if any(t[0] <= x + r and x - r <= t[2] and t[1] <= z + r and z - r <= t[3] for t in taken):
                continue
            vx, vz = cx - x, cz - z
            door = ("east" if vx > 0 else "west") if abs(vx) > abs(vz) else ("south" if vz > 0 else "north")
            f = rock_house if kind == "rock" else mink_house
            taken.append(f(bb, x, z, r, door, tracker, audit, seed_of("kurau", x, z) % 1000))
            n += 1
    # the outskirts: more houses wherever the forest floor is free, facing the market
    for gz in range(62, 168, 11):
        for gx in range(48, 154, 11):
            x, z = gx + int(rng.integers(-2, 3)), gz + int(rng.integers(-2, 3))
            kind = "rock" if (gx + gz) % 3 == 0 else "mink"
            r = int(rng.integers(6, 8)) if kind == "rock" else int(rng.integers(4, 6))
            if math.hypot(x - cx, z - cz) > 70:
                continue
            xs, zs = np.array([x - r - 2, x + r + 2, x, x]), np.array([z, z, z - r - 2, z + r + 2])
            xi, zi = np.array([x - r, x + r, x, x, x]), np.array([z, z, z - r, z + r, z])
            if not top_land(xs, zs).all() or paths(xi, zi).any():
                continue
            if any(t[0] <= x + r and x - r <= t[2] and t[1] <= z + r and z - r <= t[3] for t in taken):
                continue
            vx, vz = cx - x, cz - z
            door = ("east" if vx > 0 else "west") if abs(vx) > abs(vz) else ("south" if vz > 0 else "north")
            f = rock_house if kind == "rock" else mink_house
            taken.append(f(bb, x, z, r, door, tracker, audit, seed_of("kurau", x, z) % 1000))
            n += 1
    print("Kurau houses:", n)


def right_flank_camp(bb, taken):
    cx, cz = CAMP
    y = hy(cx, cz) + 1
    bb.fill_where(cx - 5, y - 1, cz - 5, cx + 5, y - 1, cz + 5, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= 4.6, "minecraft:cobblestone")
    for (dx, dz) in ((0, 0), (1, 1), (-1, 1), (1, -1)):
        bb.set(cx + dx, y, cz + dz, "minecraft:campfire[lit=true,signal_fire=false,facing=north]")
    # Guardians' tents in a ring, Nekomamushi's big leopard-cloth tent at the head
    for k, a in enumerate(range(20, 360, 55)):
        t = math.radians(a)
        tx, tz = int(round(cx + 13 * math.cos(t))), int(round(cz + 13 * math.sin(t)))
        ty = hy(tx, tz) + 1
        big = k == 0
        L, W = (9, 5) if big else (6, 3)
        cloth = "minecraft:yellow_wool" if big else ("minecraft:green_wool", "minecraft:brown_wool", "minecraft:light_gray_wool")[k % 3]
        for i in range(W + 1):
            bb.fill(tx - i, ty + W - i, tz - L // 2, tx - i, ty + W - i, tz + L // 2, cloth)
            bb.fill(tx + i, ty + W - i, tz - L // 2, tx + i, ty + W - i, tz + L // 2, cloth)
            if big:
                for zz in range(tz - L // 2, tz + L // 2 + 1, 2):
                    bb.set(tx - i, ty + W - i, zz + (i % 2), "minecraft:black_wool")
                    bb.set(tx + i, ty + W - i, zz + ((i + 1) % 2), "minecraft:black_wool")
        bb.fill(tx, ty + W, tz - L // 2 - 1, tx, ty + W, tz + L // 2 + 1, "minecraft:spruce_fence")
        bb.fill(tx, ty, tz - L // 2 - 1, tx, ty + W - 1, tz - L // 2 - 1, "minecraft:spruce_fence")
        bb.fill(tx, ty, tz + L // 2 + 1, tx, ty + W - 1, tz + L // 2 + 1, "minecraft:spruce_fence")
        bb.fill(tx - W, ty - 3, tz - L // 2 - 1, tx + W, ty - 1, tz + L // 2 + 1, "minecraft:dirt")
        bb.fill(tx - W + 1, ty, tz - L // 2, tx + W - 1, ty, tz + L // 2, "minecraft:brown_carpet")
        if big:
            bb.fill(tx - 2, ty, tz - 2, tx - 1, ty, tz + 2, "minecraft:yellow_carpet")
    for a in range(0, 360, 36):
        t = math.radians(a)
        px, pz = int(round(cx + 21 * math.cos(t))), int(round(cz + 21 * math.sin(t)))
        if top_land(np.array([px]), np.array([pz]))[0]:
            py = hy(px, pz) + 1
            bb.fill(px, py, pz, px, py + 3, pz, "minecraft:spruce_fence")
            bb.set(px, py + 4, pz, "onepiece:paper_lantern[hanging=false]")
    # weapon racks and a lookout platform
    lx, lz = cx + 8, cz - 18
    ly = hy(lx, lz) + 1
    for (dx, dz) in ((0, 0), (3, 0), (0, 3), (3, 3)):
        bb.fill(lx + dx, ly, lz + dz, lx + dx, ly + 8, lz + dz, "minecraft:spruce_log[axis=y]")
    bb.fill(lx - 1, ly + 9, lz - 1, lx + 4, ly + 9, lz + 4, "minecraft:spruce_planks")
    bb.fill(lx + 1, ly, lz + 1, lx + 1, ly + 9, lz + 1, "minecraft:ladder[facing=south]") if False else None
    bb.fill(lx + 1, ly, lz + 4, lx + 1, ly + 8, lz + 4, "minecraft:ladder[facing=south]")
    bb.set(lx + 1, ly + 9, lz + 4, AIR)
    for (dx, dz) in ((-1, -1), (4, -1), (-1, 4), (4, 4)):
        bb.set(lx + dx, ly + 10, lz + dz, "minecraft:spruce_fence")
    taken.append((cx - 17, cz - 17, cx + 17, cz + 17))


def design():
    bb = BigBuild(seed=16010, y_min=-26, y_max=TOP + 80)
    tracker = P.PropTracker(16010)
    audit = []
    rng = np.random.default_rng(16010)
    zunesha(bb)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, ZOU, 16040, mask=lambda X, Z: top_land(X, Z) & ~paths(X, Z), under="minecraft:dirt")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, PATH, 16041, mask=lambda X, Z: paths(X, Z), under="minecraft:dirt")
    taken = [(STAIR_TOP[0] - 4, STAIR_TOP[1] - 4, STAIR_TOP[0] + 4, CZ + B)]
    taken.append(whale_tree(bb, tracker, audit, rng))
    right_flank_camp(bb, taken)
    kurau_city(bb, tracker, audit, taken, rng)
    # the Whale Forest: giant trees over the back, thick round the Whale Tree, kept off the paths and the edges
    k = 0
    for _ in range(5000):
        x, z = int(rng.integers(40, N - 40)), int(rng.integers(60, N - 26))
        X, Z = np.array([x, x + 1, x - 4, x + 5]), np.array([z, z + 1, z - 4, z + 5])
        if not top_land(X, Z).all() or q_(x, z) > 0.8 or paths(X, Z).any():
            continue
        if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken):
            continue
        NT.giant_tree(bb, x, hy(x, z) + 1, z, int(rng.integers(14, 26)), rng, kind=("jungle", "dark_oak", "spruce")[k % 3] if k % 4 else "jungle")
        taken.append((x - 4, z - 4, x + 5, z + 5))
        k += 1
        if k >= 46:
            break
    print("trees:", k)
    # lanterns along the paths
    reg_done = set()
    for x in range(0, N, 9):
        for z in range(0, N, 9):
            for (ox, oz) in ((0, 0), (3, 2)):
                px, pz = x + ox, z + oz
                if paths(np.array([px]), np.array([pz]))[0] and not paths(np.array([px + 3]), np.array([pz]))[0]:
                    lx = px + 3
                    if (bb.get_region(lx, hy(lx, pz) + 1, pz, lx, hy(lx, pz) + 4, pz) <= 1).all() and top_land(np.array([lx]), np.array([pz]))[0]:
                        bb.fill(lx, hy(lx, pz) + 1, pz, lx, hy(lx, pz) + 2, pz, "minecraft:spruce_fence")
                        bb.set(lx, hy(lx, pz) + 3, pz, "onepiece:paper_lantern[hanging=false]")
                    break
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 16090, density=0.5,
              kinds=["onepiece:mink_fern", "minecraft:fern", "onepiece:giant_fern", "minecraft:short_grass", "minecraft:large_fern", "minecraft:bush"],
              flowers=["minecraft:blue_orchid", "minecraft:oxeye_daisy", "minecraft:cornflower"],
              mask=lambda X, Z: top_land(X, Z) & ~paths(X, Z),
              ground=("grass_block", "moss_block", "podzol", "rooted_dirt", "jungle_loam", "coarse_dirt"))
    # zunesha moss lying on the forest floor in patches (a cover: only on top of soil)
    top = bb.get_region(0, TOP - 3, 0, N - 1, TOP + 6, N - 1)  # (the back sits between TOP - 8 and TOP + 3)
    for (ix, iz) in zip(*np.nonzero(top_land(X_, Z_))):
        x, z = int(ix), int(iz)
        y = hy(x, z)
        k_ = y - (TOP - 3)
        if not (0 <= k_ < top.shape[1] - 1) or top[x, k_ + 1, z] != 0:
            continue
        if NT.noise(np.array([x]), np.array([z]), 16095, 5)[0] < 0.7:
            continue
        if bb.names[int(top[x, k_, z])].split("[")[0] in ("minecraft:grass_block", "minecraft:moss_block", "minecraft:podzol"):
            bb.set(x, y + 1, z, "onepiece:zunesha_moss")
    return bb, audit


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    steady(b)
    b.chest(WT[0] + 2, hy(*WT) + 1, WT[1] - 3, "treasure", "west")
    b.chest(CITY[0] + 2, hy(*CITY) + 1, CITY[1] + 2, "medium", "south")
    b.chest(CAMP[0] - 3, hy(*CAMP) + 1, CAMP[1] + 3, "easy", "north")
    return b, 0
