"""Elbaph v2, the land of the giants, redesigned with the Minecraft Builder skill
(dossier: mcb/dossiers/elbaph_tree.md).

An irregular northern island whose ground fades out to its beaches: snowy pine hills in the north, a green valley
in the south. The Treasure Tree Adam rises from it: a trunk 30 across and 110 tall with roots like hills that arch
over the ground, a giants' doorway into the hollow trunk, a spiral stair along its inner wall to the Owl Library
(three galleries of books) and the Lookout Hall, which opens onto the first great bough. Its crown spreads like a
land of its own. In the valley the giants' village is built to their size: two great longhouses with dragon-headed
gables, giant tables and benches, a hearth like a house, mead barrels; a few human-size guest houses, the warriors'
training ring with giant weapons, rune stones and a long jetty. 176 x 176. y 0 = ground / sea surface. (v2)

v3 (2026-10-30, audit: "the tree is too small"): site 220 x 220, trunk ~1.5x as thick (about 46 across at the
top, 70 at the flared foot) and 170 tall, so the crown sits above the clouds. The spiral stair now climbs the whole
trunk to the Crown Village: a railed plank deck on top of the trunk under a high leaf canopy, with giant-timber
cottages, a bonfire and a bell, ringed by twelve great boughs whose leaf clouds spread over most of the island."""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, furnish, set_if_air, house_module, place_house, lamp_post
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "elbaph_tree"
TITLE = "Elbaph Great Tree"
CUTS = [3, 40, 76]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 220
CX, CZ = 110, 110
TX, TZ = 112, 92                       # the tree
TOP = 170                              # trunk top (crown starts lower)
LIB, LOOK = 44, 96                     # floors inside the trunk
RB = 40                                # half-size of the box round the trunk
HALLS = [(26, 150, 44, 18), (120, 168, 40, 16)]  # longhouses (x0, z0, L, W) along x
RING = (182, 124, 14)                  # training ring
JETTY = (100, 196)

ADAM = "onepiece:adam_log"
ADAMP = "onepiece:adam_planks"
LEAVES = ["minecraft:oak_leaves[distance=7,persistent=true,waterlogged=false]",
          "minecraft:dark_oak_leaves[distance=7,persistent=true,waterlogged=false]",
          "minecraft:azalea_leaves[distance=7,persistent=true,waterlogged=false]"]

SHORE = NT.outline(CX, CZ, 100, 1126)

SNOWY = [("minecraft:snow_block", 0.30), ("minecraft:grass_block[snowy=true]", 0.20), ("minecraft:podzol[snowy=true]", 0.16),
         ("minecraft:coarse_dirt", 0.10), ("minecraft:moss_block", 0.08), ("minecraft:stone", 0.09), ("minecraft:gravel", 0.07)]
VALLEY = [("minecraft:grass_block", 0.62), ("minecraft:podzol", 0.08), ("minecraft:coarse_dirt", 0.08),
          ("minecraft:moss_block", 0.10), ("minecraft:rooted_dirt", 0.06), ("onepiece:giant_clover_patch" if False else "minecraft:grass_block", 0.06)]
ROCK = [("minecraft:stone", 0.4), ("minecraft:andesite", 0.18), ("minecraft:tuff", 0.14), ("minecraft:snow_block", 0.16),
        ("minecraft:gravel", 0.12)]
SAND = [("minecraft:gravel", 0.4), ("minecraft:sand", 0.3), ("minecraft:stone", 0.15), ("minecraft:andesite", 0.15)]


def north(X, Z):
    return Z + 10 * (NT.noise(X, Z * 0 + 3, 1127, 23) - 0.5) < 100


def rect_d(X, Z, r):
    dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0)
    dz = np.maximum(np.maximum(r[1] - Z, Z - r[3]), 0)
    return np.hypot(dx, dz)


def flatness(X, Z):
    d = np.hypot(X - TX, Z - TZ) - 40
    for (x0, z0, L, W) in HALLS:
        d = np.minimum(d, rect_d(X, Z, (x0 - 6, z0 - 6, x0 + L + 6, z0 + W + 6)))
    d = np.minimum(d, np.hypot(X - RING[0], Z - RING[1]) - RING[2] - 4)
    d = np.minimum(d, rect_d(X, Z, (14, 100, 200, 190)) + 6)
    d = np.minimum(d, rect_d(X, Z, (JETTY[0] - 6, JETTY[1] - 12, JETTY[0] + 6, N)))
    return np.clip(d / 14.0, 0, 1)


def height(X, Z):
    d = SHORE(X, Z)
    inland = np.clip((d - 3) / 16.0, 0, 1)
    hills = NT.fbm(X, Z, 1131, 30) * 13 * inland
    a = np.arctan2(Z - CZ, X - CX)
    w = np.clip(np.cos(a + 1.9) * 1.5 - 0.2, 0, 1)                 # higher fells in the north-west
    rise = np.clip((d - 4) / 8.0, 0, 1) * np.clip((44 - d) / 18.0, 0, 1)
    fells = w * rise * (16 + 12 * NT.fbm(X, Z, 1132, 16))
    h = np.maximum(hills, fells) * flatness(X, Z)
    h = h + 1.5 * NT.noise(X, Z, 1133, 6) * (1 - flatness(X, Z)) * inland
    h = np.where(d < 2.5, -1, h)
    return np.round(h)


def land(X, Z):
    return SHORE(X, Z) > 0


def hy(x, z):
    return int(height(np.array([[x]]), np.array([[z]]))[0, 0])


def terrain(bb):
    H = height
    NT.cover(bb, 0, 0, N - 1, N - 1, H, SAND, 1141, mask=lambda X, Z: land(X, Z) & (SHORE(X, Z) < 6),
             under="minecraft:stone", core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, H, ROCK, 1142, mask=lambda X, Z: land(X, Z) & (SHORE(X, Z) >= 6) & (H(X, Z) >= 14),
             under="minecraft:stone", core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, H, SNOWY, 1143,
             mask=lambda X, Z: land(X, Z) & (SHORE(X, Z) >= 6) & (H(X, Z) < 14) & north(X, Z), core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, H, VALLEY, 1144,
             mask=lambda X, Z: land(X, Z) & (SHORE(X, Z) >= 6) & (H(X, Z) < 14) & ~north(X, Z), core="minecraft:stone")


# ------------------------------------------------------------------ the Treasure Tree Adam
def trunk_r(y, a):
    base = 23 - 6 * max(0, y) / TOP + 13 * math.exp(-max(0, y) / 7.0)
    return base * (1 + 0.07 * np.sin(5 * a + y * 0.06) + 0.05 * np.sin(9 * a - y * 0.03) + 0.04 * np.sin(3 * a + 1))


def trunk(bb):
    R = RB
    for y in range(-4, TOP + 1):
        def shell(X, yy, Z, y=y):
            a = np.arctan2(Z - TZ, X - TX)
            d = np.hypot(X - TX, Z - TZ)
            r = trunk_r(y, a)
            return d <= r
        def hollow(X, yy, Z, y=y):
            a = np.arctan2(Z - TZ, X - TX)
            d = np.hypot(X - TX, Z - TZ)
            return d <= trunk_r(y, a) - 4
        bb.fill_where(TX - R, y, TZ - R, TX + R, y, TZ + R, shell, ADAM + "[axis=y]")
        if 1 <= y < TOP - 4:
            bb.fill_where(TX - R, y, TZ - R, TX + R, y, TZ + R, hollow, AIR)
    # ground floor, Owl Library floor, Lookout Hall floor
    for fy in (0, LIB, LOOK):
        bb.fill_where(TX - R, fy, TZ - R, TX + R, fy, TZ + R,
                      lambda X, yy, Z, fy=fy: np.hypot(X - TX, Z - TZ) <= trunk_r(fy, np.arctan2(Z - TZ, X - TX)) - 3.5,
                      ADAMP)
    bb.fill_where(TX - R, TOP - 4, TZ - R, TX + R, TOP - 4, TZ + R,
                  lambda X, yy, Z: np.hypot(X - TX, Z - TZ) <= trunk_r(TOP - 4, np.arctan2(Z - TZ, X - TX)) - 3.5, ADAM + "[axis=y]")
    # the giants' doorway (south): 7 wide, 13 tall with a rounded head
    for y in range(1, 15):
        hw = 3 if y <= 10 else int(round(math.sqrt(max(0, 9 - (y - 10) ** 2 * 2))))
        bb.fill(TX - hw, y, TZ + 12, TX + hw, y, TZ + 42, AIR) if hw > 0 else None
    bb.fill(TX - 4, 0, TZ + 14, TX + 4, 0, TZ + 42, ADAMP)
    # windows: knot holes up the trunk
    for (y, a) in ((LIB + 8, 0.3), (LIB + 14, 2.4), (LIB + 20, 4.1), (LOOK + 4, 1.2), (LOOK + 4, 3.6), (20, 5.2),
                   (124, 0.9), (138, 3.0), (152, 4.9), (TOP - 10, 2.0)):
        r = trunk_r(y, a)
        for t in np.linspace(r - 6, r + 1, 11):
            x, z = round(TX + t * math.cos(a)), round(TZ + t * math.sin(a))
            bb.fill(x - 1, y, z - 1, x + 1, y + 3, z + 1, AIR)
    spiral_stair(bb)
    hall_of_adam(bb)
    owl_library(bb)
    lookout(bb)
    crown_village(bb)


def spiral_stair(bb):
    """A two-wide stair winding up the inside of the trunk wall from the ground to the Lookout Hall."""
    th = 0.0
    y = 1
    while y <= TOP - 5:
        R = trunk_r(y, th) - 5.5
        for w in (0.0, 1.0):
            x, z = round(TX + (R - w) * math.cos(th)), round(TZ + (R - w) * math.sin(th))
            tx, tz = -math.sin(th), math.cos(th)
            f = ("east" if tx > 0 else "west") if abs(tx) > abs(tz) else ("south" if tz > 0 else "north")
            bb.fill(x, y + 1, z, x, y + 4, z, AIR)
            bb.set(x, y, z, f"onepiece:adam_stairs[facing={f},half=bottom]")
            bb.fill(x, max(1, y - 3), z, x, y - 1, z, ADAMP) if y > 1 else None
        th += 1.25 / R
        y += 1
    # handrail posts on the open side every few steps would block the walk; lanterns on the trunk wall instead
    for k in range(0, LOOK, 6):
        a = k * 0.09
        r = trunk_r(k, a) - 4
        x, z = round(TX + r * math.cos(a)), round(TZ + r * math.sin(a))
        if 2 < k:
            bb.set(x, k + 4, z, "minecraft:lantern[hanging=false]") if False else None


def hall_of_adam(bb):
    """The ground floor inside the trunk: a giant hearth ring, benches, banners and giant mead barrels."""
    bb.cylinder(TX, 0, TZ, 3, 0, "minecraft:stone_bricks")
    bb.ring(TX, 1, TZ, 2, 3, 1, "minecraft:stone_brick_wall")
    bb.set(TX, 1, TZ, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        bb.set(TX + dx, 1, TZ + dz, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    for k in range(8):
        a = k * math.pi / 4 + 0.4
        x, z = round(TX + 7 * math.cos(a)), round(TZ + 7 * math.sin(a))
        f = ("west" if math.cos(a) > 0 else "east") if abs(math.cos(a)) > abs(math.sin(a)) else ("north" if math.sin(a) > 0 else "south")
        bb.set(x, 1, z, f"minecraft:spruce_stairs[facing={f},half=bottom]")
    for (dx, dz) in ((-9, -6), (9, -6)):                            # giant barrels
        bb.cylinder(TX + dx, 1, TZ + dz, 2, 5, "minecraft:barrel[facing=up,open=false]")
        bb.ring(TX + dx, 3, TZ + dz, 1, 2, 3, "minecraft:stripped_spruce_log[axis=y]")
    for y in (10, 22):                                              # lantern rings high up
        for k in range(10):
            a = k * math.pi / 5
            r = trunk_r(y, a) - 4.2
            x, z = round(TX + r * math.cos(a)), round(TZ + r * math.sin(a))
            set_if_air(bb, x, y, z, "minecraft:lantern[hanging=false]")


def owl_library(bb):
    """Three galleries of books round the inner wall, an owl of wood and feathers at the centre, reading tables."""
    y0 = LIB + 1
    for g, gy in enumerate((y0, y0 + 9, y0 + 18)):
        def wall_ring(X, yy, Z, gy=gy):
            a = np.arctan2(Z - TZ, X - TX)
            d = np.hypot(X - TX, Z - TZ)
            r = trunk_r(gy, a) - 4
            return (d > r - 1.2) & (d <= r)
        bb.fill_where(TX - RB, gy, TZ - RB, TX + RB, gy + 6, TZ + RB, lambda X, yy, Z: wall_ring(X, yy, Z) & ((np.arctan2(Z - TZ, X - TX) * 6).astype(int) % 5 != 0), "minecraft:bookshelf", only_empty=True)
        if g:
            def gallery(X, yy, Z, gy=gy):
                a = np.arctan2(Z - TZ, X - TX)
                d = np.hypot(X - TX, Z - TZ)
                r = trunk_r(gy, a) - 4
                return (d > r - 4) & (d <= r)
            bb.fill_where(TX - RB, gy - 1, TZ - RB, TX + RB, gy - 1, TZ + RB, gallery, ADAMP, only_empty=True)
            bb.fill_where(TX - RB, gy, TZ - RB, TX + RB, gy, TZ + RB,
                          lambda X, yy, Z, gy=gy: (np.abs(np.hypot(X - TX, Z - TZ) - (trunk_r(gy, np.arctan2(Z - TZ, X - TX)) - 8)) < 0.6),
                          "onepiece:adam_fence", only_empty=True)
        for k in range(8):
            a = k * math.pi / 4 + 0.2 * g
            r = trunk_r(gy, a) - 6
            x, z = round(TX + r * math.cos(a)), round(TZ + r * math.sin(a))
            set_if_air(bb, x, gy + 5, z, "minecraft:lantern[hanging=false]") if False else None
    # the owl: a squat wooden body, white face disc, big eyes, ear tufts, on a book plinth
    ox, oz, oy = TX, TZ - 2, y0
    bb.fill(ox - 2, oy, oz - 2, ox + 2, oy + 1, oz + 2, "minecraft:bookshelf")
    bb.fill_where(ox - 4, oy + 2, oz - 4, ox + 4, oy + 11, oz + 4,
                  lambda X, yy, Z: ((X - ox) / 2.7) ** 2 + ((yy - oy - 6) / 3.8) ** 2 + ((Z - oz) / 2.4) ** 2 <= 1,
                  "minecraft:brown_wool")
    bb.fill(ox - 1, oy + 6, oz + 3, ox + 1, oy + 8, oz + 3, "minecraft:white_wool")
    for dx in (-1, 1):
        bb.set(ox + dx, oy + 8, oz + 4, "minecraft:black_wool")
        bb.set(ox + dx, oy + 8, oz + 3, "minecraft:yellow_wool")
        bb.fill(ox + 2 * dx, oy + 9, oz, ox + 2 * dx, oy + 10, oz, "minecraft:brown_wool")
    bb.set(ox, oy + 7, oz + 4, "minecraft:orange_wool")
    # reading tables round it
    for k in range(6):
        a = k * math.pi / 3 + 0.5
        x, z = round(TX + 9 * math.cos(a)), round(TZ + 9 * math.sin(a))
        bb.set(x, y0, z, "minecraft:spruce_fence")
        bb.set(x, y0 + 1, z, "minecraft:spruce_pressure_plate")
        bb.set(x + 1, y0, z, "minecraft:spruce_stairs[facing=west,half=bottom]")
        bb.set(x - 1, y0, z, "minecraft:lectern[facing=east,has_book=false,powered=false]")
    for y in (y0 + 7, y0 + 16, y0 + 25):
        bb.fill(TX, y, TZ, TX, y0 + 28, TZ, "minecraft:iron_chain[axis=y]") if y == y0 + 7 else None
    for (dx, dz) in ((0, 0),):
        bb.set(TX + dx, y0 + 6, TZ + 6, "minecraft:lantern[hanging=false]") if False else None


def lookout(bb):
    """The Lookout Hall on the third floor, a doorway out onto the first great bough, and a railed platform on it."""
    y0 = LOOK + 1
    a = 0.15                                                         # east
    r = trunk_r(y0, a)
    bx = TX + int(r) - 4
    for k in range(0, 46):
        x = bx + k
        z = TZ + round(3 * math.sin(k * 0.12))
        yy = LOOK - 2 + round(k * 0.18)
        bb.fill_where(x - 1, yy - 4, z - 4, x + 1, yy + 1, z + 4,
                      lambda X, Y, Z, z=z, yy=yy, k=k: (((Y - yy + 1.5) / 2.6) ** 2 + ((Z - z) / (3.6 - k * 0.04)) ** 2 <= 1),
                      ADAM + "[axis=x]")
    bb.fill(bx - 6, y0, TZ - 1, bx + 2, y0 + 4, TZ + 1, AIR)
    for k in range(0, 34):
        x = bx + k
        z = TZ + round(3 * math.sin(k * 0.12))
        yy = LOOK - 2 + round(k * 0.18) + 1
        bb.fill(x, yy + 1, z - 1, x, yy + 1, z + 1, ADAMP)
        bb.fill(x, yy + 2, z - 1, x, yy + 4, z + 1, AIR)
    ex = bx + 34
    ey = LOOK - 2 + round(34 * 0.18) + 2
    bb.cylinder(ex, ey, TZ + 1, 5, ey, ADAMP)
    bb.ring(ex, ey + 1, TZ + 1, 4, 5, ey + 1, "onepiece:adam_fence")
    bb.set(ex, ey + 1, TZ + 1, "minecraft:spruce_fence")
    bb.set(ex, ey + 2, TZ + 1, "minecraft:lantern[hanging=false]")
    # inside the hall: benches round a map table, banners, lanterns
    bb.set(TX, y0, TZ, "minecraft:cartography_table")
    for (dx, dz, f) in ((2, 0, "west"), (-2, 0, "east"), (0, 2, "north"), (0, -2, "south")):
        bb.set(TX + dx, y0, TZ + dz, f"minecraft:spruce_stairs[facing={f},half=bottom]")
    for k in range(8):
        a = k * math.pi / 4
        r = trunk_r(y0, a) - 4.5
        x, z = round(TX + r * math.cos(a)), round(TZ + r * math.sin(a))
        set_if_air(bb, x, y0, z, "minecraft:lantern[hanging=false]")
    return (ex, ey)


def branch(bb, x0, y0, z0, a, L, rise, r0, rng):
    tips = []
    for s in range(L):
        t = s / L
        x = x0 + s * math.cos(a)
        z = z0 + s * math.sin(a)
        y = y0 + s * rise - 6 * t * t
        r = r0 * (1 - 0.65 * t)
        R = int(r) + 1
        ax = "x" if abs(math.cos(a)) > 0.7 else "z" if abs(math.sin(a)) > 0.7 else "y"
        bb.fill_where(int(x) - R, int(y) - R, int(z) - R, int(x) + R, int(y) + R, int(z) + R,
                      lambda X, Y, Z, x=x, y=y, z=z, r=r: (X - x) ** 2 + (Y - y) ** 2 + (Z - z) ** 2 <= r * r,
                      ADAM + f"[axis={ax}]")
        if s > L * 0.45 and s % 7 == 0:
            tips.append((round(x), round(y), round(z)))
    tips.append((round(x0 + L * math.cos(a)), round(y0 + L * rise - 6), round(z0 + L * math.sin(a))))
    return tips


def leaf_cloud(bb, x, y, z, r, rng, k):
    R = int(r) + 1
    seed = int(x * 31 + z * 17 + y)

    def f(X, Y, Z):
        d2 = (X - x) ** 2 + ((Y - y) * 1.7) ** 2 + (Z - z) ** 2
        return (d2 <= r * r) & (NT.noise(X * 2 + Y, Z * 2, seed, 3) > 0.22)
    bb.fill_where(x - R, y - R // 2 - 2, z - R, x + R, y + R // 2 + 2, z + R, f, LEAVES[k % 2], only_empty=True)
    bb.fill_where(x - R, y - R // 2 - 2, z - R, x + R, y + R // 2 + 2, z + R,
                  lambda X, Y, Z: f(X, Y, Z) & (NT.noise(X, Z + Y * 3, seed + 1, 4) > 0.72), LEAVES[2])


def crown(bb, rng):
    """Twelve great boughs from high on the trunk, each ending in leaf clouds, and a high canopy over the Crown
    Village so the deck on top of the trunk sits in a sheltered clearing."""
    tips = []
    n = 12
    for k in range(n):
        a = k * 2 * math.pi / n + rng.uniform(-0.18, 0.18)
        y0 = TOP - 34 + int(rng.integers(0, 24))
        r = trunk_r(y0, a) - 3
        L = int(rng.integers(52, 74))
        tips += branch(bb, TX + r * math.cos(a), y0, TZ + r * math.sin(a), a, L, rng.uniform(0.16, 0.34),
                       rng.uniform(4.6, 6.2), rng)
    for k in range(6):                                           # lower boughs break up the long trunk
        a = k * 2 * math.pi / 6 + 0.9 + rng.uniform(-0.2, 0.2)
        y0 = TOP - 78 + k * 7
        r = trunk_r(y0, a) - 3
        tips += branch(bb, TX + r * math.cos(a), y0, TZ + r * math.sin(a), a, int(rng.integers(30, 42)),
                       rng.uniform(0.3, 0.5), rng.uniform(3.2, 4.0), rng)[-2:]
    for k, (x, y, z) in enumerate(tips):
        x = min(max(x, 14), N - 15)
        z = min(max(z, 14), N - 15)
        leaf_cloud(bb, x, y + 3, z, rng.uniform(10, 15), rng, k)
    leaf_cloud(bb, TX, TOP + 34, TZ, 30, rng, 1)
    for k in range(8):
        a = k * math.pi / 4 + 0.4
        leaf_cloud(bb, round(TX + 34 * math.cos(a)), TOP + 20, round(TZ + 34 * math.sin(a)), 17, rng, k)
    # the clearing over the deck: leaves form a ceiling, never a wall inside the village
    leaf = np.array([i for i, n in enumerate(bb.names) if n and "leaves" in n])
    x1, z1, x2, z2 = TX - DECK - 2, TZ - DECK - 2, TX + DECK + 2, TZ + DECK + 2
    X, Z = np.arange(x1, x2 + 1)[:, None], np.arange(z1, z2 + 1)[None, :]
    for y in range(TOP + 1, TOP + 22):
        m = np.isin(bb.get_region(x1, y, z1, x2, y, z2)[:, 0, :], leaf) & \
            (np.hypot(X - TX, Z - TZ) <= DECK + 1 - max(0, y - TOP - 14) * 1.5)
        bb.fill_where(x1, y, z1, x2, y, z2, lambda XX, yy, ZZ, m=m: m, AIR)


DECK = 30                              # radius of the Crown Village deck on top of the trunk


def crown_village(bb):
    """The deck on the trunk top: adam planks out to DECK, held up by log struts, a log rail, a bonfire ring and a
    great bell in the middle, giant-timber cottages round the edge, and the stair hatch from inside the trunk."""
    y = TOP
    bb.fill_where(TX - DECK, y, TZ - DECK, TX + DECK, y, TZ + DECK,
                  lambda X, Y, Z: np.hypot(X - TX, Z - TZ) <= DECK - 0.5 * np.sin(np.arctan2(Z - TZ, X - TX) * 7), ADAMP)
    bb.fill_where(TX - DECK, y + 1, TZ - DECK, TX + DECK, y + 1, TZ + DECK,
                  lambda X, Y, Z: np.abs(np.hypot(X - TX, Z - TZ) - (DECK - 0.5 * np.sin(np.arctan2(Z - TZ, X - TX) * 7)) + 0.6) < 0.6,
                  "onepiece:adam_fence")
    for k in range(16):                                          # struts from the trunk out under the deck rim
        a = k * math.pi / 8
        r0 = trunk_r(y - 14, a) - 2
        for s in range(0, 40):
            t = s / 39
            r = r0 + (DECK - 2 - r0) * t
            yy = y - 14 + 13 * t
            x, z = TX + r * math.cos(a), TZ + r * math.sin(a)
            bb.fill_where(int(x) - 2, int(yy) - 2, int(z) - 2, int(x) + 2, int(yy) + 2, int(z) + 2,
                          lambda X, Y, Z, x=x, yy=yy, z=z: (X - x) ** 2 + (Y - yy) ** 2 + (Z - z) ** 2 <= 2.4,
                          ADAM + "[axis=y]")
    # the stair hatch: the spiral ends at TOP - 5 just inside the wall; cut a way up through the cap
    th, yy = 0.0, 1
    while yy < TOP - 5:
        th += 1.25 / (trunk_r(yy, th) - 5.5)
        yy += 1
    for k in range(6):
        r = trunk_r(yy, th) - 6
        x, z = round(TX + r * math.cos(th + k * 0.06)), round(TZ + r * math.sin(th + k * 0.06))
        bb.fill(x - 1, TOP - 4 + k, z - 1, x + 1, TOP + 3, z + 1, AIR)
        bb.fill(x, TOP - 5 + k, z, x, TOP - 5 + k, z, ADAMP)
    # bonfire ring and the great bell on a timber frame
    bb.cylinder(TX, y, TZ, 4, y, "minecraft:stone_bricks")
    bb.ring(TX, y + 1, TZ, 3, 4, y + 1, "minecraft:cobblestone_wall")
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            bb.set(TX + dx, y + 1, TZ + dz, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    bx, bz = TX, TZ - 12
    for dx in (-4, 4):
        bb.fill(bx + dx, y + 1, bz, bx + dx, y + 11, bz, "minecraft:spruce_log[axis=y]")
    bb.fill(bx - 5, y + 12, bz, bx + 5, y + 12, bz, "minecraft:stripped_dark_oak_log[axis=x]")
    bb.fill(bx, y + 11, bz, bx, y + 11, bz, "minecraft:iron_chain[axis=y]")
    bb.fill_where(bx - 3, y + 4, bz - 3, bx + 3, y + 10, bz + 3,
                  lambda X, Y, Z: (np.hypot(X - bx, Z - bz) <= 1.2 + (y + 10 - Y) * 0.35) & (np.hypot(X - bx, Z - bz) > (y + 10 - Y) * 0.35 - 0.2) | ((Y == y + 10) & (np.hypot(X - bx, Z - bz) <= 1.2)),
                  "minecraft:gold_block")
    bb.set(bx, y + 4, bz, "minecraft:bell[attachment=ceiling,facing=north,powered=false]") if False else None
    # giant-timber cottages round the rim, doors facing the bonfire
    pal = dict(walls=["minecraft:spruce_planks", "minecraft:stripped_spruce_log[axis=y]", "onepiece:adam_planks"],
               frame="onepiece:adam_log", base=["minecraft:mossy_cobblestone", "minecraft:cobblestone", "minecraft:stone_bricks"],
               floor="onepiece:adam_planks", wood="spruce", chimney="minecraft:cobblestone")
    tracker = P.PropTracker(1170)
    audit = []
    for k, a in enumerate((0.35, 1.45, 2.55, 3.75, 4.85)):
        w, d = (11, 9) if k % 2 else (10, 8)
        cx, cz = TX + 20 * math.cos(a), TZ + 20 * math.sin(a)
        x0, z0 = round(cx - w / 2), round(cz - d / 2)
        rot = (0 if math.sin(a) < -0.7 else 2 if math.sin(a) > 0.7 else 1 if math.cos(a) > 0 else 3)
        mod, _, au = house_module(seed_of("elbaph_crown", k), w, d, 1 + k % 2, "minecraft:dark_oak_stairs", tracker,
                                  [["living", "bedroom"], ["kitchen", "storeroom"], ["dining", "bedroom"]][k % 3], pal=pal)
        audit += au
        place_house(bb, mod, w, d, x0, y, z0, rot)
    for k in range(10):
        a = k * math.pi / 5 + 0.15
        lamp_post(bb, round(TX + 11 * math.cos(a)), y + 1, round(TZ + 11 * math.sin(a)), post="onepiece:adam_fence", h=3)
    return audit


def roots(bb, rng):
    out = []
    for k in range(9):
        a = k * 2 * math.pi / 9 + rng.uniform(-0.2, 0.2)
        if abs(((a - math.pi / 2) + math.pi) % (2 * math.pi) - math.pi) < 0.35:
            continue                                                 # keep the doorway clear
        r0 = trunk_r(4, a) - 3
        L = int(rng.integers(26, 40))
        peak = rng.uniform(8, 16)
        for s in range(L):
            t = s / L
            x = TX + (r0 + s) * math.cos(a) + 3 * math.sin(s * 0.15 + k)
            z = TZ + (r0 + s) * math.sin(a) + 3 * math.cos(s * 0.13 + k)
            g = hy(int(x), int(z))
            y = g + peak * math.sin(math.pi * min(1, t * 1.15)) - 3 * t
            r = 6.0 * (1 - 0.6 * t)
            R = int(r) + 1
            ax = "x" if abs(math.cos(a)) > 0.7 else "z" if abs(math.sin(a)) > 0.7 else "y"
            bb.fill_where(int(x) - R, int(y) - R, int(z) - R, int(x) + R, int(y) + R, int(z) + R,
                          lambda X, Y, Z, x=x, y=y, z=z, r=r: (X - x) ** 2 + ((Y - y) * 1.2) ** 2 + (Z - z) ** 2 <= r * r,
                          ADAM + f"[axis={ax}]")
        out.append((int(TX + (r0 + L) * math.cos(a)), int(TZ + (r0 + L) * math.sin(a))))
    return out


# ------------------------------------------------------------------ the giants' village
def longhouse(bb, x0, z0, L, W, tracker, audit, seed):
    """A giants' longhouse along x: stone footing, timber posts, plank walls, a steep roof with crossed dragon-head
    gables, a giant table and benches, a hearth pit, mead barrels, and a human-size loft at the east end."""
    H = 14
    g = max(0, max(hy(x, z) for x in (x0, x0 + L) for z in (z0, z0 + W)))
    bb.fill(x0 - 1, g - 4, z0 - 1, x0 + L + 1, g, z0 + W + 1, "minecraft:cobblestone")
    bb.fill(x0, g, z0, x0 + L, g, z0 + W, "minecraft:spruce_planks")
    bb.mix(x0, g + 1, z0, x0 + L, g + H, z0 + W, ["minecraft:spruce_planks", "minecraft:stripped_spruce_log[axis=x]"], [0.7, 0.3])
    bb.fill(x0, g + 1, z0, x0 + L, g + 2, z0 + W, "minecraft:mossy_cobblestone")
    bb.fill(x0 + 1, g + 1, z0 + 1, x0 + L - 1, g + H + 12, z0 + W - 1, AIR)
    for x in range(x0, x0 + L + 1, 6):
        bb.fill(x, g + 1, z0, x, g + H, z0, "minecraft:spruce_log[axis=y]")
        bb.fill(x, g + 1, z0 + W, x, g + H, z0 + W, "minecraft:spruce_log[axis=y]")
        if x not in (x0, x0 + L):
            for zz in (z0, z0 + W):                                 # tall slit windows between the posts
                bb.fill(x + 3, g + 6, zz, x + 3, g + 10, zz, "minecraft:glass_pane" if False else AIR)
                bb.fill(x + 3, g + 6, zz, x + 3, g + 10, zz, "minecraft:spruce_fence")
    P.gable_roof(bb, x0, z0, x0 + L, z0 + W, g + H + 1, "minecraft:dark_oak_stairs", ridge_axis="x",
                 gable_fill="minecraft:spruce_planks", overhang=2, ends_overhang=1)
    top = g + H + 1 + (W + 4) // 2
    for xe in (x0 - 1, x0 + L + 1):                                # crossed gable beams with dragon heads
        for k in range(6):
            bb.set(xe, top - 2 + k, z0 + W // 2 - 2 - k // 2 + 2 - (k % 2), "minecraft:spruce_log[axis=y]")
            bb.set(xe, top - 2 + k, z0 + W // 2 + 2 + k // 2 - 2 + (k % 2), "minecraft:spruce_log[axis=y]")
        for side in (-1, 1):
            hz = z0 + W // 2 + side * 3
            bb.fill(xe, top + 4, hz, xe, top + 5, hz, "minecraft:dark_oak_planks")
            bb.set(xe, top + 6, hz, "minecraft:dark_oak_fence")
            bb.set(xe + (1 if xe > x0 else -1), top + 4, hz, "minecraft:dark_oak_trapdoor[facing=%s,half=top,open=false]" % ("east" if xe > x0 else "west"))
    # giant doors at the west end (8 wide, 11 tall)
    zc = z0 + W // 2
    bb.fill(x0, g + 1, zc - 4, x0, g + 11, zc + 3, AIR)
    bb.fill(x0, g + 12, zc - 4, x0, g + 12, zc + 3, "minecraft:stripped_dark_oak_log[axis=z]")
    # the giant table down the middle, benches either side, giant tankards and plates
    ty = g + 7
    for x in range(x0 + 8, x0 + L - 10, 7):
        for z in (zc - 2, zc + 1):
            bb.fill(x, g + 1, z, x, ty - 1, z, "minecraft:stripped_spruce_log[axis=y]")
    bb.fill(x0 + 7, ty, zc - 3, x0 + L - 10, ty, zc + 2, ADAMP)
    for zb in (zc - 6, zc + 5):
        bb.fill(x0 + 7, g + 4, zb, x0 + L - 10, g + 4, zb, "onepiece:adam_slab[type=top]" if False else "minecraft:spruce_slab[type=top]")
        for x in range(x0 + 8, x0 + L - 10, 7):
            bb.fill(x, g + 1, zb, x, g + 3, zb, "minecraft:spruce_log[axis=y]")
    for x in range(x0 + 9, x0 + L - 11, 9):
        bb.cylinder(x, ty + 1, zc - 1, 1, ty + 3, "minecraft:barrel[facing=up,open=false]")
        bb.set(x + 4, ty + 1, zc, "minecraft:white_carpet")
        bb.set(x + 4, ty + 1, zc - 1, "minecraft:white_carpet")
    # hearth pit and giant barrels by the walls
    hx = x0 + L - 8
    bb.fill(hx - 2, g, zc - 3, hx + 2, g, zc + 3, "minecraft:stone_bricks")
    for z in range(zc - 2, zc + 3, 2):
        bb.set(hx, g + 1, z, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        bb.set(hx - 1, g + 1, z, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    bb.fill(hx - 2, g + 1, zc - 3, hx + 2, g + 1, zc - 3, "minecraft:stone_brick_wall")
    bb.fill(hx - 2, g + 1, zc + 3, hx + 2, g + 1, zc + 3, "minecraft:stone_brick_wall")
    for (x, z) in ((x0 + 4, z0 + 3), (x0 + 4, z0 + W - 3)):
        bb.cylinder(x, g + 1, z, 2, g + 5, "minecraft:barrel[facing=up,open=false]")
        bb.ring(x, g + 2, z, 1, 2, g + 2, "minecraft:stripped_spruce_log[axis=y]")
    # a human-size loft over the east end with rooms, reached by a ladder
    ly = g + 8
    bb.fill(x0 + L - 12, ly, z0 + 1, x0 + L - 1, ly, z0 + W - 1, "minecraft:spruce_planks")
    furnish(bb, [(x0 + L - 11, z0 + 1, x0 + L - 1, zc - 1), (x0 + L - 11, zc + 1, x0 + L - 1, z0 + W - 1)], ly + 1, 4,
            ["bedroom", "storage"], seed, tracker, audit=audit)
    bb.fill(x0 + L - 11, ly + 1, zc, x0 + L - 1, ly + 1, zc, "minecraft:red_carpet")
    bb.fill(x0 + L - 13, g + 1, zc, x0 + L - 13, ly + 1, zc, "minecraft:ladder[facing=west]")
    # light: lantern chandeliers on chains from the roof
    for x in range(x0 + 6, x0 + L - 4, 8):
        bb.fill(x, g + H, zc, x, g + H + 3, zc, "minecraft:iron_chain[axis=y]")
        bb.set(x, g + H - 1, zc, "minecraft:spruce_planks")
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            bb.set(x + dx, g + H - 1, zc + dz, "minecraft:spruce_fence")
            bb.set(x + dx, g + H - 2, zc + dz, "minecraft:lantern[hanging=true]")
    return (x0 - 4, z0 - 4, x0 + L + 4, z0 + W + 4)


def training_ring(bb, rng):
    x, z, r = RING
    g = max(0, hy(x, z))
    bb.fill_where(x - r - 1, g, z - r - 1, x + r + 1, g, z + r + 1,
                  lambda X, Y, Z: ((X - x) ** 2 + (Z - z) ** 2 <= r * r) & (NT.noise(X, Z, 1151, 3) > 0.3), "minecraft:coarse_dirt")
    bb.fill_where(x - r - 1, g, z - r - 1, x + r + 1, g, z + r + 1,
                  lambda X, Y, Z: ((X - x) ** 2 + (Z - z) ** 2 <= r * r) & (NT.noise(X, Z, 1151, 3) <= 0.3), "minecraft:packed_mud")
    bb.fill_where(x - r - 1, g + 1, z - r - 1, x + r + 1, g + 4, z + r + 1,
                  lambda X, Y, Z: (np.abs(np.hypot(X - x, Z - z) - r) < 0.7) & ((Y - g) <= 2 + (X + Z) % 2), "minecraft:spruce_log[axis=y]")
    bb.fill(x - 2, g + 1, z + r, x + 2, g + 4, z + r, AIR)
    # a giant sword thrust into the ground
    sx, sz = x - 4, z - 3
    bb.fill(sx, g - 2, sz - 1, sx, g + 16, sz + 1, "minecraft:iron_block")
    bb.fill(sx, g + 17, sz, sx, g + 17, sz, "minecraft:iron_block")
    bb.fill(sx, g + 14, sz - 4, sx, g + 14, sz + 4, "minecraft:gold_block")
    bb.fill(sx, g + 15, sz, sx, g + 20, sz, "minecraft:stripped_dark_oak_log[axis=y]")
    bb.set(sx, g + 21, sz, "minecraft:gold_block")
    # a giant axe on a block, a giant round shield leaning
    ax, az = x + 5, z + 2
    bb.fill(ax, g + 1, az, ax, g + 2, az + 1, "minecraft:spruce_log[axis=y]")
    bb.fill(ax - 6, g + 3, az, ax + 6, g + 3, az, "minecraft:stripped_dark_oak_log[axis=x]")
    bb.fill(ax + 4, g + 2, az - 1, ax + 7, g + 6, az - 1, "minecraft:iron_block")
    bb.fill(ax + 7, g + 1, az - 1, ax + 7, g + 7, az - 1, "minecraft:iron_block")
    cx, cz = x + 1, z - 8
    bb.fill_where(cx - 5, g + 1, cz, cx + 5, g + 11, cz, lambda X, Y, Z: (X - cx) ** 2 + (Y - g - 6) ** 2 <= 25, "minecraft:spruce_planks")
    bb.fill_where(cx - 5, g + 1, cz, cx + 5, g + 11, cz, lambda X, Y, Z: (np.abs(np.hypot(X - cx, Y - g - 6) - 5) < 0.6), "minecraft:iron_block")
    bb.fill(cx - 1, g + 5, cz - 1, cx + 1, g + 7, cz - 1, "minecraft:gold_block")
    bb.fill_where(cx - 5, g + 1, cz, cx + 5, g + 11, cz, lambda X, Y, Z: (np.abs(Y - g - 6) <= 0) & ((X - cx) ** 2 <= 16), "minecraft:red_wool")
    return (x - r - 3, z - r - 3, x + r + 3, z + r + 3)


def rune_stone(bb, x, z, h, rng):
    g = hy(x, z)
    for y in range(g - 2, g + h + 1):
        w = 1 if y < g + h - 1 else 0
        bb.fill(x - w, y, z, x + w, y, z + 1, "minecraft:stone" if (y * 7 + x) % 5 else "minecraft:tuff")
    for y in range(g + 2, g + h - 1, 2):
        bb.set(x, y, z + 2, "minecraft:chiseled_stone_bricks") if False else bb.set(x + int(rng.integers(-1, 2)), y, z + 1, "minecraft:chiseled_tuff")
    bb.set(x, g + h + 1, z, "minecraft:moss_carpet")


def jetty(bb):
    x, z = JETTY
    g = 0
    for zz in range(z - 6, N):
        X, Z = np.array([[x]]), np.array([[zz]])
        for dx in range(-3, 4):
            bb.set(x + dx, 1, zz, "minecraft:spruce_planks" if abs(dx) < 3 else "minecraft:spruce_slab[type=bottom]" if False else "minecraft:spruce_planks")
            bb.fill(x + dx, 2, zz, x + dx, 4, zz, AIR)
        if zz % 6 == 0:
            for dx in (-3, 3):
                bb.fill(x + dx, -8, zz, x + dx, 2, zz, "minecraft:spruce_log[axis=y]")
                bb.set(x + dx, 3, zz, "minecraft:lantern[hanging=false]") if zz % 12 == 0 else None
    # giant boat sheds on the shore either side of the jetty
    return (x - 6, z - 8, x + 6, N - 1)


def village(bb, rng, tracker, audit):
    taken = []
    for i, (x0, z0, L, W) in enumerate(HALLS):
        taken.append(longhouse(bb, x0, z0, L, W, tracker, audit, seed_of("hall", i)))
    # human-size guest houses (snowy timber cottages)
    pal = dict(walls=["minecraft:spruce_planks", "minecraft:stripped_spruce_log[axis=y]", "minecraft:spruce_planks"],
               frame="minecraft:dark_oak_log", base=["minecraft:cobblestone", "minecraft:mossy_cobblestone", "minecraft:stone_bricks"],
               floor="minecraft:spruce_planks", wood="spruce", chimney="minecraft:cobblestone")
    houses = [(16, 104, 10, 8, 2, 1), (32, 110, 9, 8, 1, 0), (14, 122, 10, 8, 1, 2), (34, 128, 9, 7, 2, 3),
              (186, 152, 10, 8, 1, 3), (176, 170, 9, 8, 2, 0)]
    for k, (x0, z0, w, d, fl, rot) in enumerate(houses):
        mod, _, au = house_module(seed_of("elbaph_house", k), w, d, fl, "minecraft:dark_oak_stairs", tracker,
                                  [["living", "bedroom"], ["kitchen", "storeroom"]][k % 2], pal=pal)
        audit += au
        g = max(0, max(hy(x, z) for x in (x0, x0 + w) for z in (z0, z0 + d)))
        bb.fill(x0 - 1, g - 3, z0 - 1, x0 + w + 1, g, z0 + d + 1, "minecraft:cobblestone")
        place_house(bb, mod, w, d, x0, g, z0, rot)
        taken.append((x0 - 3, z0 - 3, x0 + w + 3, z0 + d + 3))
    taken.append(training_ring(bb, rng))
    for (x, z, h) in ((56, 140, 9), (168, 146, 11), (88, 186, 8), (196, 104, 10), (24, 90, 7), (60, 196, 8)):
        rune_stone(bb, x, z, h, rng)
        taken.append((x - 3, z - 3, x + 3, z + 3))
    for (x, z) in ((28, 120), (46, 140), (92, 176), (112, 180), (160, 160), (176, 140)):
        g = max(0, hy(x, z))
        lamp_post(bb, x, g + 1, z, post="minecraft:spruce_fence", h=3)
    taken.append(jetty(bb))
    return taken


def forest(bb, rng, taken):
    k = 0
    for _ in range(4000):
        x, z = int(rng.integers(6, N - 6)), int(rng.integers(6, N - 6))
        X, Z = np.array([[x]]), np.array([[z]])
        if SHORE(X, Z)[0, 0] < 8 or flatness(X, Z)[0, 0] < 0.5:
            continue
        if np.hypot(x - TX, z - TZ) < 58:
            continue
        if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken):
            continue
        y = hy(x, z)
        n = north(X, Z)[0, 0]
        if rng.random() < 0.18:
            NT.giant_tree(bb, x, y + 1, z, int(rng.integers(16, 24)), rng, kind="spruce", vines=False)
            taken.append((x - 5, z - 5, x + 6, z + 6))
        else:
            P.tree(bb, x, y + 1, z, int(rng.integers(8, 15)), "spruce" if n or rng.random() < 0.5 else "birch", rng)
            taken.append((x - 2, z - 2, x + 2, z + 2))
        k += 1
        if k >= 110:
            break
    for _ in range(26):
        x, z = int(rng.integers(8, N - 8)), int(rng.integers(8, N - 8))
        X, Z = np.array([[x]]), np.array([[z]])
        if SHORE(X, Z)[0, 0] < 5 or flatness(X, Z)[0, 0] < 0.5 or np.hypot(x - TX, z - TZ) < 56:
            continue
        NT.boulder(bb, x, hy(x, z), z, rng.uniform(1.5, 3.4), rng, blocks=("minecraft:stone", "minecraft:andesite", "minecraft:mossy_cobblestone"))
    print("trees:", k)


def design():
    bb = BigBuild(seed=1126, y_min=-12, y_max=TOP + 52)
    tracker = P.PropTracker(1126)
    audit = []
    rng = np.random.default_rng(1126)
    terrain(bb)
    trunk(bb)
    roots(bb, rng)
    taken = village(bb, rng, tracker, audit)
    taken.append((TX - 56, TZ - 56, TX + 56, TZ + 56))
    forest(bb, rng, taken)
    crown(bb, rng)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 1160, density=0.3,
              kinds=["minecraft:short_grass", "minecraft:fern", "onepiece:giant_fern", "minecraft:short_grass", "onepiece:giant_barley", "minecraft:sweet_berry_bush[age=2]"],
              flowers=["onepiece:giants_clover", "minecraft:cornflower", "minecraft:oxeye_daisy", "minecraft:dandelion"],
              mask=lambda X, Z: land(X, Z) & ~north(X, Z))
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 1161, density=0.18, kinds=["minecraft:fern", "minecraft:large_fern", "minecraft:sweet_berry_bush[age=1]"],
              mask=lambda X, Z: land(X, Z) & north(X, Z))
    return bb, audit


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    x0, z0, L, W = HALLS[0]
    b.chest(x0 + L - 3, max(0, hy(x0 + L, z0)) + 9, z0 + 2, "medium", "west")
    b.chest(TX + 3, LOOK + 1, TZ - 6, "treasure", "west")
    b.chest(TX - 4, LIB + 1, TZ + 6, "medium", "south")
    for (gx, gz) in ((RING[0], RING[1] + 4), (40, 120), (TX - 6, TZ + 48)):
        b.guard(gx, max(0, hy(gx, gz)) + 1, gz, "bounty_hunter")
    return b, 0
