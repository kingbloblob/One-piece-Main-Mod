"""Whisky Peak v2, redesigned with the Minecraft Builder skill: the 'welcoming' town of music and liquor at the start
of the Grand Line, really a Baroque Works bounty-hunter nest.

An island of dry hills ringed by giant cactus-shaped rock spires, ribbed green-grey stone with arms branching off,
every ledge crowded with the crosses of dead pirates. A river runs down from the hills through the middle of town to a
harbour basin on the south, where the Going Merry is tied up at the quay. Along both banks the stone-and-plaster town:
two- and three-storey houses, inns and bars with coloured roofs, streets hung with banners and strings of lanterns,
two bridges over the river. On the west bank the huge party hall where the welcome feast is thrown (long tables, the
bar, the stage, the kitchens, a gallery), on the east bank the mayor Igaram's house, and up the slopes the bounty
hunters' lookout. 176 x 176. y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, furnish, set_if_air, house_module, place_house, lamp_post, wing_floor
from mcb.bridge import to_canvas
from mcb.shipstamp import stamp_ship
from mcb import nature as NT

SID = "whisky_peak"
TITLE = "Whisky Peak"
CUTS = [6, 12]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 176
SHORE = NT.outline(88, 86, 80, 2420, wobble=0.08)
TY = 4                                     # town level
TOWN = (26, 34, 150, 124)
HARB = (66, 126, 110, 168)                 # harbour basin
RX = lambda Z: 88 + 3 * np.sin(np.asarray(Z) * 0.08)
HALL = (32, 58, 64, 84)
IGARAM = (112, 60, 132, 76)
SPIRES = [(149, 98, 52), (139, 131, 44), (47, 132, 50), (24, 108, 36), (27, 74, 56), (37, 41, 46), (68, 27, 42), (102, 19, 54), (129, 40, 38), (152, 64, 48)]

DRY = [("minecraft:grass_block", 0.3), ("minecraft:coarse_dirt", 0.22), ("minecraft:dirt", 0.08), ("minecraft:podzol", 0.08),
       ("minecraft:rooted_dirt", 0.08), ("minecraft:terracotta", 0.08), ("minecraft:packed_mud", 0.08), ("minecraft:moss_block", 0.08)]
ROCK = [("minecraft:terracotta", 0.25), ("minecraft:stone", 0.25), ("minecraft:andesite", 0.15), ("minecraft:light_gray_terracotta", 0.15),
        ("minecraft:cobblestone", 0.2)]
SAND = [("minecraft:sand", 0.6), ("minecraft:sandstone", 0.2), ("minecraft:clay", 0.2)]
PAVE = [("minecraft:stone_bricks", 0.3), ("minecraft:cracked_stone_bricks", 0.1), ("minecraft:andesite", 0.15),
        ("minecraft:polished_andesite", 0.15), ("minecraft:cobblestone", 0.15), ("minecraft:packed_mud", 0.15)]
PAL = dict(walls=["minecraft:smooth_sandstone", "minecraft:white_terracotta", "minecraft:calcite"], frame="minecraft:stone_bricks",
           base=["minecraft:cobblestone", "minecraft:stone_bricks", "minecraft:andesite"], floor="minecraft:spruce_planks", wood="spruce",
           chimney="minecraft:bricks")
PAL2 = dict(walls=["minecraft:light_gray_terracotta", "minecraft:white_terracotta", "minecraft:terracotta"],
            frame="minecraft:stripped_spruce_log", base=["minecraft:cobblestone", "minecraft:stone_bricks", "minecraft:mossy_cobblestone"],
            floor="minecraft:oak_planks", wood="oak", chimney="minecraft:bricks")
ROOFS = ["minecraft:red_nether_brick_stairs", "minecraft:brick_stairs", "minecraft:spruce_stairs", "minecraft:mud_brick_stairs",
         "minecraft:dark_oak_stairs", "minecraft:granite_stairs"]


def rect_d(X, Z, r):
    dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0)
    dz = np.maximum(np.maximum(r[1] - Z, Z - r[3]), 0)
    return np.hypot(dx, dz)


def river(X, Z):
    X = np.asarray(X); Z = np.asarray(Z)
    return ((np.abs(X - RX(Z)) <= 4) & (Z > 22)) | (rect_d(X, Z, HARB) == 0)


def streets(X, Z):
    X = np.asarray(X); Z = np.asarray(Z)
    m = (np.abs(X - RX(Z)) <= 8) & ~river(X, Z) & (Z > TOWN[1]) & (Z < HARB[1] + 6)         # embankments
    for z in (48, 96):
        m |= (np.abs(Z - z) <= 2) & (X > TOWN[0]) & (X < TOWN[2])
    for x in (46, 130):
        m |= (np.abs(X - x) <= 2) & (Z > TOWN[1]) & (Z < TOWN[3])
    m |= (np.abs(Z - 122) <= 3) & (X > TOWN[0] + 10) & (X < TOWN[2] - 10)                  # the quay
    return m


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = SHORE(X, Z)
    h = 6 + NT.fbm(X, Z, 2422, 24) * 18 - 4
    h = h * np.clip((d - 1.5) / 10.0, 0, 1)
    w = np.clip(rect_d(X, Z, TOWN) / 12.0, 0, 1)
    h = TY * (1 - w) + h * w
    rv = np.abs(X - RX(Z))
    h = np.where((rv < 12) & (Z > 16), np.minimum(h, TY + np.clip((rv - 6) / 2, 0, 20)), h)
    h = np.where(river(X, Z), -3, h)
    h = np.where(rect_d(X, Z, HARB) == 0, -6, h)
    h = np.where(d < 1.5, -1, h)
    return np.round(h)


def build_maps():
    X = np.arange(N)[:, None]
    Z = np.arange(N)[None, :]
    H = _height(X, Z).astype(int)
    g = np.zeros_like(H)
    for a, b in (((slice(1, None), slice(None)), (slice(None, -1), slice(None))),
                 ((slice(None), slice(1, None)), (slice(None), slice(None, -1)))):
        dd = np.abs(H[a] - H[b])
        g[a] = np.maximum(g[a], dd); g[b] = np.maximum(g[b], dd)
    return H, g


HMAP, GRAD = build_maps()


def height(X, Z):
    return HMAP[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def steep(X, Z):
    return GRAD[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)] >= 2


def land(X, Z):
    return (SHORE(X, Z) > 1.5) & ~river(X, Z)


def hy(x, z):
    return int(HMAP[min(max(x, 0), N - 1), min(max(z, 0), N - 1)])


def terrain(bb):
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SAND, 2431, mask=lambda X, Z: land(X, Z) & (height(X, Z) <= 1) & ~steep(X, Z),
             under="minecraft:sandstone", core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, ROCK, 2432, mask=lambda X, Z: land(X, Z) & steep(X, Z), under="minecraft:stone",
             core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, DRY, 2433, mask=lambda X, Z: land(X, Z) & (height(X, Z) > 1) & ~steep(X, Z),
             core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, PAVE, 2434, mask=lambda X, Z: land(X, Z) & streets(X, Z), core="minecraft:stone")
    inland = lambda X, Z: SHORE(X, Z) > 1.5
    bed = lambda X, Z: np.where(inland(X, Z), height(X, Z), np.minimum(np.round(-2 - np.clip(-SHORE(X, Z) * 0.6, 0, 12)),
                                                                        np.where(rect_d(X, Z, HARB) == 0, -6, 0)))
    bb.fill_where(0, -14, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -16, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy == bed(X, Z)),
                  "minecraft:mud" if False else "minecraft:clay")
    bb.fill_where(0, -16, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy < bed(X, Z)) & (yy >= bed(X, Z) - 2), "minecraft:stone")
    # stone quay walls along the river and the harbour
    bb.fill_where(0, -6, 0, N - 1, TY, N - 1, lambda X, yy, Z: inland(X, Z) & ~river(X, Z) & (yy <= height(X, Z))
                  & (river(X + 1, Z) | river(X - 1, Z) | river(X, Z + 1) | river(X, Z - 1)) & (Z > 30),
                  "minecraft:stone_bricks")
    # the river runs down from a spring in the hills: a little waterfall pool at its head
    bb.fill_where(78, -3, 14, 98, 12, 26, lambda X, yy, Z: (np.hypot(X - RX(Z), Z - 22) <= 5) & (yy <= 0) & (yy >= -3), "minecraft:water")


def spire(bb, x, z, h, rng):
    """A giant cactus rock: a ribbed column (stripes of green-grey and tan stone), two or three arms branching off and
    turning up, every ledge and arm-top crowded with grave crosses."""
    g = hy(x, z) - 2
    r = 4 + h // 18
    graves = []
    ribs = ["minecraft:green_terracotta", "minecraft:lime_terracotta", None, "minecraft:moss_block"]

    def column(cx, cz, y1, y2, rr):
        for yy in range(y1, y2 + 1):
            rr2 = rr + (0.6 if yy - y1 < 2 else 0) - max(0, (yy - (y2 - rr)) / 1.2) * (yy > y2 - rr)
            bb.fill_where(cx - rr - 1, yy, cz - rr - 1, cx + rr + 1, yy, cz + rr + 1,
                          lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= rr2, ribs[0])
            bb.fill_where(cx - rr - 1, yy, cz - rr - 1, cx + rr + 1, yy, cz + rr + 1,
                          lambda X, Y, Z: (np.hypot(X - cx, Z - cz) <= rr2)
                          & ((np.round(np.arctan2(Z - cz, X - cx) * 5 / math.pi + 10) % 2) == 0),
                          ribs[1] if (yy + cx) % 11 else ribs[3])
        graves.append((cx, y2 + 1, cz, rr - 1))

    column(x, z, g, g + h, r)
    na = 2 + int(rng.integers(0, 2))
    for k in range(na):
        a = rng.uniform(0, 2 * math.pi) if k == 0 else a + rng.uniform(1.8, 2.6)
        ay = g + int(h * rng.uniform(0.35, 0.6))
        ar = max(2, r - 2)
        L = r + 4
        ex, ez = int(round(x + L * math.cos(a))), int(round(z + L * math.sin(a)))
        for t in np.linspace(0, 1, 3 * L):
            cx_, cz_ = x + (ex - x) * t, z + (ez - z) * t
            bb.fill_where(int(cx_) - ar - 1, ay - ar, int(cz_) - ar - 1, int(cx_) + ar + 1, ay + ar, int(cz_) + ar + 1,
                          lambda X, Y, Z: np.hypot(np.hypot(X - cx_, Z - cz_), Y - ay) <= ar, ribs[0])
        column(ex, ez, ay, ay + int(h * rng.uniform(0.25, 0.4)), ar)
    # ledges round the trunk with crosses on them
    for ly in range(g + 10, g + h - 4, 9):
        for k in range(10):
            a = k * 2 * math.pi / 10 + ly
            lx, lz = round(x + (r + 1) * math.cos(a)), round(z + (r + 1) * math.sin(a))
            bb.set(lx, ly, lz, "minecraft:stone_brick_slab[type=top]")
            if k % 2 == 0:
                cross(bb, lx, ly + 1, lz, int(k / 2 + ly))
    for (cx, y, cz, rr) in graves:
        for k in range(int(rng.integers(4, 9))):
            ox, oz = int(rng.integers(-rr, rr + 1)), int(rng.integers(-rr, rr + 1))
            if ox * ox + oz * oz <= rr * rr:
                cross(bb, cx + ox, y, cz + oz, k)
    return (x - r - 4, z - r - 4, x + r + 4, z + r + 4)


def cross(bb, x, y, z, k):
    """A grave marker: a post and a cross-bar, of stone or wood, now and then with a sword stuck in beside it."""
    if k % 3 == 0:
        bb.fill(x, y, z, x, y + 2, z, "minecraft:spruce_fence")
        bb.set(x, y + 1, z, "minecraft:stripped_spruce_wood")
    else:
        bb.fill(x, y, z, x, y + 1, z, "minecraft:stone_brick_wall")
        bb.set(x, y + 2, z, "minecraft:cobblestone_wall")


def party_hall(bb, tracker, audit):
    """The welcome hall: a long stone hall under a great gable roof, a gallery round three sides, long feast tables,
    the bar along the back, a stage at the far end, kitchens and the cellar."""
    x1, z1, x2, z2 = HALL
    y0 = TY
    H = 12
    bb.fill(x1 - 1, y0 - 4, z1 - 1, x2 + 1, y0, z2 + 1, "minecraft:stone_bricks")
    bb.fill(x1, y0, z1, x2, y0, z2, "minecraft:spruce_planks")
    bb.mix(x1, y0 + 1, z1, x2, y0 + H, z2, PAL["walls"], [0.6, 0.25, 0.15])
    bb.fill(x1 + 1, y0 + 1, z1 + 1, x2 - 1, y0 + H, z2 - 1, AIR)
    for x in range(x1, x2 + 1, 4):
        for z in (z1, z2):
            bb.fill(x, y0 + 1, z, x, y0 + H, z, "minecraft:stone_bricks")
    for z in range(z1, z2 + 1, 4):
        for x in (x1, x2):
            bb.fill(x, y0 + 1, z, x, y0 + H, z, "minecraft:stone_bricks")
    # tall arched windows
    for x in range(x1 + 2, x2 - 1, 4):
        for z in (z1, z2):
            bb.fill(x, y0 + 2, z, x + 1, y0 + 5, z, "minecraft:yellow_stained_glass_pane")
            bb.fill(x, y0 + 8, z, x + 1, y0 + 10, z, "minecraft:orange_stained_glass_pane")
    # big double doors on the east (river) side
    cz = (z1 + z2) // 2
    bb.fill(x2, y0 + 1, cz - 2, x2, y0 + 5, cz + 2, AIR)
    bb.fill(x2 + 1, y0 + 6, cz - 3, x2 + 1, y0 + 6, cz + 3, "minecraft:stone_brick_slab[type=top]")
    for z in (cz - 3, cz + 3):
        bb.fill(x2 + 1, y0 + 1, z, x2 + 1, y0 + 5, z, "minecraft:stone_brick_wall")
        bb.set(x2 + 2, y0 + 4, z, "minecraft:lantern[hanging=false]") if False else bb.set(x2 + 1, y0 + 6, z, "minecraft:lantern[hanging=false]")
    # sign over the door: big wine barrel and the word WELCOME in banners
    for k, z in enumerate(range(cz - 3, cz + 4)):
        bb.set(x2 + 1, y0 + 8, z, ("minecraft:red_wall_banner[facing=east]", "minecraft:yellow_wall_banner[facing=east]")[k % 2])
    # gallery round three sides
    gy = y0 + 6
    for x in range(x1 + 1, x2):
        for z in range(z1 + 1, z2):
            if x < x1 + 4 or z < z1 + 4 or z > z2 - 4:
                bb.set(x, gy, z, "minecraft:spruce_planks")
    for x in range(x1 + 4, x2):
        bb.set(x, gy + 1, z1 + 4, "minecraft:spruce_fence"); bb.set(x, gy + 1, z2 - 4, "minecraft:spruce_fence")
    for z in range(z1 + 4, z2 - 3):
        bb.set(x1 + 4, gy + 1, z, "minecraft:spruce_fence")
    for (x, z) in ((x1 + 4, z1 + 4), (x1 + 4, z2 - 4), (x2 - 1, z1 + 4), (x2 - 1, z2 - 4)):
        bb.fill(x, y0 + 1, z, x, gy - 1, z, "minecraft:stripped_spruce_log[axis=y]")
    for x in range(x1 + 8, x2 - 1, 6):
        bb.fill(x, y0 + 1, z1 + 4, x, gy - 1, z1 + 4, "minecraft:stripped_spruce_log[axis=y]")
        bb.fill(x, y0 + 1, z2 - 4, x, gy - 1, z2 - 4, "minecraft:stripped_spruce_log[axis=y]")
    bb.fill(x1 + 1, y0 + 1, z1 + 1, x1 + 1, gy, z1 + 1, "minecraft:ladder[facing=south]")
    bb.fill(x1 + 1, gy, z1 + 1, x1 + 1, gy, z1 + 1, "minecraft:ladder[facing=south]")
    # gallery seating
    for x in range(x1 + 6, x2 - 2, 3):
        bb.set(x, gy + 1, z1 + 2, "onepiece:barrel_table"); bb.set(x, gy + 1, z2 - 2, "onepiece:barrel_table")
        bb.set(x + 1, gy + 1, z1 + 2, "onepiece:bar_stool"); bb.set(x + 1, gy + 1, z2 - 2, "onepiece:bar_stool")
    # long feast tables down the middle with stools and food
    for z in (cz - 3, cz + 3):
        bb.fill(x1 + 8, y0 + 1, z, x2 - 6, y0 + 1, z, "onepiece:dark_oak_table")
        for x in range(x1 + 8, x2 - 5):
            bb.set(x, y0 + 1, z - 1, "onepiece:bar_stool"); bb.set(x, y0 + 1, z + 1, "onepiece:bar_stool")
            if x % 3 == 0:
                bb.set(x, y0 + 2, z, ("minecraft:cake[bites=0]", "minecraft:white_candle[candles=3,lit=true]", "minecraft:flower_pot")[x % 3 - 0])
    # the bar along the north wall (under the gallery), kegs behind
    bb.fill(x1 + 6, y0 + 1, z1 + 3, x2 - 6, y0 + 1, z1 + 3, "onepiece:tavern_bar[facing=south]")
    for x in range(x1 + 6, x2 - 5):
        bb.set(x, y0 + 1, z1 + 1, "onepiece:keg[facing=south]" if x % 2 else "minecraft:barrel[facing=south,open=false]")
        bb.set(x, y0 + 2, z1 + 1, "onepiece:keg[facing=south]" if x % 3 == 0 else AIR)
        if x % 2 == 0:
            bb.set(x, y0 + 1, z1 + 4, "onepiece:bar_stool")
    # stage at the west end with curtains
    bb.fill(x1 + 1, y0 + 1, z1 + 5, x1 + 5, y0 + 1, z2 - 5, "minecraft:spruce_slab[type=top]") if False else None
    bb.fill(x1 + 1, y0 + 1, cz - 5, x1 + 6, y0 + 1, cz + 5, "minecraft:dark_oak_planks")
    for z in range(cz - 5, cz + 6):
        bb.set(x1 + 7, y0 + 1, z, st("minecraft:dark_oak_stairs", "east")) if abs(z - cz) <= 1 else None
        bb.set(x1 + 1, y0 + 2, z, "minecraft:red_wool")
        bb.set(x1 + 1, y0 + 3, z, "minecraft:red_wool")
    bb.set(x1 + 3, y0 + 2, cz, "minecraft:jukebox[has_record=false]"); bb.set(x1 + 3, y0 + 2, cz - 2, "minecraft:note_block")
    bb.set(x1 + 3, y0 + 2, cz + 2, "minecraft:note_block")
    # chandeliers
    for x in range(x1 + 10, x2 - 3, 8):
        bb.fill(x, gy + 3, cz, x, y0 + H - 1, cz, "minecraft:chain[axis=y]")
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            bb.set(x + dx, gy + 2, cz + dz, "minecraft:lantern[hanging=true]") if False else None
        bb.set(x, gy + 2, cz, "minecraft:lantern[hanging=true]")
    P.gable_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, y0 + H + 1, "minecraft:red_nether_brick_stairs",
                 gable_fill="minecraft:smooth_sandstone", overhang=1)
    # kitchens: a lean-to on the south side
    kx1, kz1, kx2, kz2 = x1 + 2, z2 + 1, x1 + 16, z2 + 8
    bb.fill(kx1, y0, kz1, kx2, y0, kz2, "minecraft:stone_bricks")
    bb.mix(kx1, y0 + 1, kz1, kx2, y0 + 4, kz2, PAL["walls"], [0.6, 0.25, 0.15])
    bb.fill(kx1 + 1, y0 + 1, kz1, kx2 - 1, y0 + 4, kz2 - 1, AIR)
    bb.fill(kx1 + 4, y0 + 1, z2, kx1 + 5, y0 + 2, z2, AIR)
    bb.fill(kx2, y0 + 1, kz1 + 3, kx2, y0 + 2, kz1 + 3, AIR)
    bb.fill(kx1 - 1, y0 + 5, kz1, kx2 + 1, y0 + 5, kz2 + 1, "minecraft:brick_slab[type=bottom]")
    P.furnish_room(bb, (kx1 + 1, kz1 + 1, kx2 - 1, kz2 - 1), y0 + 1, kind="kitchen", height=4, seed=2461, wood="spruce", tracker=tracker,
                   doors=[(kx1 + 4, kz1), (kx1 + 5, kz1), (kx2, kz1 + 3)])
    txt, ok = P.audit_props(bb, [(kx1 + 1, kz1 + 1, kx2 - 1, kz2 - 1)], y0 + 1, 4)
    if not ok:
        audit.append(txt)
    bb.fill(kx2 - 2, y0 + 5, kz1 + 2, kx2 - 2, y0 + 8, kz1 + 2, "minecraft:bricks")
    bb.set(kx2 - 2, y0 + 9, kz1 + 2, "minecraft:campfire[lit=true,signal_fire=false]")
    return (x1 - 3, z1 - 3, x2 + 4, kz2 + 2)


def igaram_house(bb, tracker, audit):
    m, top, au = house_module(seed_of("igaram"), 20, 14, 3, "minecraft:dark_oak_stairs", tracker,
                              ["living", "dining", "library", "bedroom", "bedroom", "storage"], pal=PAL, timber=False, jetty=False)
    audit += au
    place_house(bb, m, 20, 14, IGARAM[0], TY, IGARAM[1], 3)
    # a walled front garden with a flagpole
    x1, z1, x2, z2 = IGARAM[0] - 6, IGARAM[1] - 2, IGARAM[0] - 1, IGARAM[1] + 21
    for x in range(x1, x2 + 1):
        bb.set(x, TY + 1, z1, "minecraft:stone_brick_wall"); bb.set(x, TY + 1, z2, "minecraft:stone_brick_wall")
    for z in range(z1, z2 + 1):
        if abs(z - (z1 + z2) // 2) > 1:
            bb.set(x1, TY + 1, z, "minecraft:stone_brick_wall")
    bb.fill(x1 + 2, TY + 1, z1 + 2, x1 + 2, TY + 12, z1 + 2, "minecraft:iron_bars")
    bb.fill(x1 + 3, TY + 9, z1 + 2, x1 + 6, TY + 11, z1 + 2, "minecraft:white_wool")
    bb.fill(x1 + 4, TY + 10, z1 + 2, x1 + 5, TY + 10, z1 + 2, "minecraft:red_wool")
    for z in range(z1 + 4, z2 - 1, 3):
        bb.set(x1 + 2, TY + 1, z, "minecraft:rose_bush[half=lower]"); bb.set(x1 + 2, TY + 2, z, "minecraft:rose_bush[half=upper]")
    return (x1 - 1, z1 - 1, IGARAM[0] + 16, IGARAM[1] + 22)


def town(bb, tracker, audit, rng, avoid):
    """Houses in rows facing the streets and the river embankments, doors onto the street."""
    placed = []
    k = 0
    cands = []
    for sz in (48, 96):
        for x in range(TOWN[0], TOWN[2], 2):
            cands.append(("n", x, sz)); cands.append(("s", x, sz))
    for z in range(TOWN[1], HARB[1] - 4, 2):
        cands.append(("w", None, z)); cands.append(("e", None, z))
    for (side, x, z) in cands:
        w, d = int(rng.integers(8, 12)), int(rng.integers(8, 11))
        if side == "n":
            rot, x0, z0, W, D = 0, x, z - 3 - d, w, d
        elif side == "s":
            rot, x0, z0, W, D = 2, x, z + 3, w, d
        elif side == "w":
            rot, W, D = 1, d, w
            x0, z0 = int(RX(z)) - 9 - W, z
        else:
            rot, W, D = 3, d, w
            x0, z0 = int(RX(z)) + 9, z
        box = (x0 - 1, z0 - 1, x0 + W, z0 + D)
        if any(box[0] <= r[2] and r[0] <= box[2] and box[1] <= r[3] and r[1] <= box[3] for r in avoid + placed):
            continue
        xs = np.arange(x0, x0 + W)[:, None]
        zs = np.arange(z0, z0 + D)[None, :]
        if streets(xs, zs).any() or (~land(xs, zs)).any() or (SHORE(xs, zs) < 4).any() or (np.abs(height(xs, zs) - TY) > 1).any():
            continue
        floors = int(rng.integers(2, 4))
        roof = ROOFS[int(rng.integers(len(ROOFS)))] if rng.random() < 0.8 else "flat:" + ("red", "orange", "yellow")[k % 3]
        kinds = [["kitchen", "living", "dining", "workshop"][k % 4], "bedroom", "storage"]
        if k % 5 == 0:
            kinds = ["dining", "bedroom", "bedroom"]           # an inn
        m, top, au = house_module(seed_of("wp", x0, z0), w, d, floors, roof, tracker, kinds, pal=(PAL, PAL2)[k % 2],
                                  timber=k % 2 == 1, jetty=False, chimney=k % 3 == 0)
        audit += au
        bb.fill(x0, TY - 2, z0, x0 + W - 1, TY, z0 + D - 1, "minecraft:stone_bricks")
        bb.fill(x0, TY + 1, z0, x0 + W - 1, TY + 3, z0 + D - 1, AIR)
        place_house(bb, m, w, d, x0, TY, z0, rot)
        placed.append((box[0] - int(rng.integers(0, 2)), box[1], box[2] + int(rng.integers(0, 3)), box[3]))
        k += 1
    print("houses:", k)
    return placed


def bridges(bb):
    for z in (48, 96):
        x0, x1 = int(RX(z)) - 7, int(RX(z)) + 7
        for k, x in enumerate(range(x0, x1 + 1)):
            yy = TY + int(round(2 * math.sin(math.pi * k / (x1 - x0))))
            bb.fill(x, yy, z - 2, x, yy, z + 2, "minecraft:stone_bricks")
            bb.fill(x, TY - 3, z - 2, x, yy - 1, z + 2, AIR) if 2 <= k <= x1 - x0 - 2 else None
            bb.set(x, yy + 1, z - 2, "minecraft:stone_brick_wall"); bb.set(x, yy + 1, z + 2, "minecraft:stone_brick_wall")
        for x in (x0, x1):
            lamp_post(bb, x, TY + 2, z - 2, h=3); lamp_post(bb, x, TY + 2, z + 2, h=3)


def festoons(bb, rng):
    """Banners and strings of lanterns across the streets, between posts."""
    for z in range(40, 120, 12):
        xr = int(RX(z))
        for (xa, xb) in ((xr - 13, xr - 6), (xr + 6, xr + 13)):
            if any(abs(z - s) < 4 for s in (48, 96)):
                continue
            for x in (xa, xb):
                bb.fill(x, TY + 1, z, x, TY + 6, z, "minecraft:spruce_fence")
            bb.fill(xa + 1, TY + 6, z, xb - 1, TY + 6, z, "minecraft:spruce_fence")
            for x in range(xa + 1, xb, 2):
                bb.set(x, TY + 5, z, "minecraft:lantern[hanging=true]")
            for x in range(xa + 2, xb, 2):
                bb.set(x, TY + 5, z, ("minecraft:red_wool", "minecraft:yellow_wool", "minecraft:lime_wool", "minecraft:orange_wool")[(x + z) % 4]) \
                    if False else None


def harbour(bb):
    # wooden jetties into the basin, bollards, crates and the Going Merry at the quay
    for x in (HARB[0] + 4, HARB[2] - 4):
        bb.fill(x - 1, TY - 1, HARB[1], x + 1, TY - 1, HARB[1] + 22, "minecraft:spruce_planks")
        for z in range(HARB[1], HARB[1] + 23, 4):
            bb.fill(x - 1, -6, z, x - 1, TY - 2, z, "minecraft:spruce_log[axis=y]")
            bb.fill(x + 1, -6, z, x + 1, TY - 2, z, "minecraft:spruce_log[axis=y]")
            bb.set(x + 1, TY, z, "minecraft:spruce_fence")
    for x in range(HARB[0] + 8, HARB[2] - 8, 6):
        bb.set(x, TY + 1, HARB[1] - 2, "minecraft:polished_andesite_wall") if False else bb.set(x, TY + 1, HARB[1] - 1, "minecraft:stone_brick_wall")
    for (x, z) in ((HARB[0] - 4, HARB[1] - 4), (HARB[0] - 3, HARB[1] - 4), (HARB[2] + 3, HARB[1] - 4), (HARB[2] + 4, HARB[1] - 5)):
        bb.set(x, TY + 1, z, "minecraft:barrel[facing=up,open=false]")
    stamp_ship(bb, "going_merry", (HARB[0] + HARB[2]) // 2 - 2, HARB[1] + 22, water_y=0, rot=3)
    # a lighthouse on the west point of the harbour mouth
    lx, lz = HARB[0] - 6, HARB[3] - 4
    if SHORE(np.array([[lx]]), np.array([[lz]]))[0, 0] > 1.5:
        y = hy(lx, lz)
        for yy in range(y + 1, y + 16):
            bb.fill_where(lx - 3, yy, lz - 3, lx + 3, yy, lz + 3, lambda X, Y, Z: np.hypot(X - lx, Z - lz) <= 2.4,
                          "minecraft:white_terracotta" if (yy // 3) % 2 else "minecraft:red_terracotta")
        bb.set(lx, y + 16, lz, "minecraft:glowstone")
        bb.fill(lx - 1, y + 17, lz - 1, lx + 1, y + 17, lz + 1, "minecraft:red_nether_brick_slab[type=bottom]")


def lookout(bb):
    """The bounty hunters' lookout on the hill: a stone watch hut and a tall post with a spyglass platform."""
    x, z = 140, 40
    y = hy(x, z)
    bb.fill(x - 4, y - 1, z - 4, x + 4, y, z + 4, "minecraft:cobblestone")
    bb.fill(x - 3, y + 1, z - 3, x + 3, y + 4, z + 3, "minecraft:stone_bricks")
    bb.fill(x - 2, y + 1, z - 2, x + 2, y + 4, z + 2, AIR)
    bb.fill(x, y + 1, z + 3, x, y + 2, z + 3, AIR)
    for (a, b) in ((x - 3, z), (x + 3, z), (x, z - 3)):
        bb.set(a, y + 3, b, "minecraft:iron_bars")
    bb.fill(x - 4, y + 5, z - 4, x + 4, y + 5, z + 4, "minecraft:spruce_slab[type=bottom]")
    bb.fill(x + 2, y + 1, z - 2, x + 2, y + 9, z - 2, "minecraft:ladder[facing=south]") if False else None
    bb.fill(x - 2, y + 1, z - 2, x - 2, y + 5, z - 2, "minecraft:ladder[facing=south]")
    bb.fill(x - 2, y + 5, z - 2, x - 2, y + 5, z - 2, "minecraft:ladder[facing=south]")
    bb.fill(x - 4, y + 6, z - 4, x + 4, y + 6, z - 4, "minecraft:spruce_fence"); bb.fill(x - 4, y + 6, z + 4, x + 4, y + 6, z + 4, "minecraft:spruce_fence")
    bb.fill(x - 4, y + 6, z - 4, x - 4, y + 6, z + 4, "minecraft:spruce_fence"); bb.fill(x + 4, y + 6, z - 4, x + 4, y + 6, z + 4, "minecraft:spruce_fence")
    bb.set(x + 2, y + 1, z + 1, "onepiece:chart_table[facing=north]") if False else bb.set(x + 2, y + 1, z + 1, "minecraft:barrel[facing=up,open=false]")
    bb.set(x + 2, y + 1, z - 2, "minecraft:red_bed[facing=south,occupied=false,part=foot]") if False else None
    bb.set(x, y + 4, z, "minecraft:lantern[hanging=true]")
    bb.set(x + 3, y + 7, z + 3, "minecraft:bell[attachment=floor,facing=south]")
    return (x - 6, z - 6, x + 6, z + 6)


def scenery(bb, rng, taken):
    k = 0
    for _ in range(5000):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        X, Z = np.array([[x]]), np.array([[z]])
        if not land(X, Z)[0, 0] or SHORE(X, Z)[0, 0] < 5 or GRAD[x, z] >= 3 or streets(X, Z)[0, 0]:
            continue
        if rect_d(X, Z, TOWN)[0, 0] == 0 and rng.random() < 0.9:
            continue
        if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken):
            continue
        y = hy(x, z)
        if k % 3 == 2:                    # little cacti and dry bushes on the hills
            for dy in range(1, 1 + int(rng.integers(1, 4))):
                bb.set(x, y, z, "minecraft:sand") if dy == 1 else None
                bb.set(x, y + dy, z, "minecraft:cactus[age=0]")
            set_if_air(bb, x + 1, y + 1, z, AIR)
        else:
            P.tree(bb, x, y + 1, z, int(rng.integers(5, 9)), ("acacia", "oak", "spruce")[k % 3], rng)
        taken.append((x - 3, z - 3, x + 3, z + 3))
        k += 1
        if k >= 70:
            break
    print("trees:", k)


def design():
    bb = BigBuild(seed=2420, y_min=-16, y_max=100)
    tracker = P.PropTracker(2420)
    audit = []
    rng = np.random.default_rng(2420)
    terrain(bb)
    taken = [party_hall(bb, tracker, audit), igaram_house(bb, tracker, audit), lookout(bb)]
    for (x, z, h) in SPIRES:
        if SHORE(np.array([[x]]), np.array([[z]]))[0, 0] > 6:
            taken.append(spire(bb, x, z, h, rng))
    taken += town(bb, tracker, audit, rng, list(taken))
    bridges(bb)
    festoons(bb, rng)
    harbour(bb)
    scenery(bb, rng, taken)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 2490, density=0.2,
              kinds=["minecraft:short_grass", "minecraft:short_dry_grass", "minecraft:dead_bush", "minecraft:tall_dry_grass"],
              flowers=["minecraft:dandelion", "minecraft:poppy"],
              mask=lambda X, Z: land(X, Z) & ~streets(X, Z) & (rect_d(X, Z, TOWN) > 2))
    return bb, audit


def steady(b):
    """Sand and gravel with nothing solid under it would fall when the build generates (at sea the world's water
    fills in under it): turn those into blocks that stay put."""
    import render
    for (x, y, z), s in list(b.blocks.items()):
        n = s.split("[")[0]
        if n.endswith(("gravel", "sand", "concrete_powder")) and "sandstone" not in n:
            below = b.blocks.get((x, y - 1, z))
            if (below is None and y >= 0) or (below is not None and render.shape_of(below) != "full"):
                b.blocks[(x, y, z)] = "minecraft:coarse_dirt" if "gravel" in n else "minecraft:smooth_sandstone" if "sand" in n else \
                    n.replace("concrete_powder", "concrete")


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    steady(b)
    hx1, hz1, hx2, hz2 = HALL
    b.chest(hx1 + 2, TY + 1, hz2 - 2, "medium", "east")
    b.chest(IGARAM[0] + 3, TY + 1, IGARAM[1] + 3, "easy", "south")
    b.guards("bounty_hunter", ((hx2 + 4, (hz1 + hz2) // 2 - 4), (hx2 + 4, (hz1 + hz2) // 2 + 4), (hx1 + 14, (hz1 + hz2) // 2)), y=TY + 1)
    b.guards("bounty_hunter", ((int(RX(70)) - 9, 70), (int(RX(110)) + 9, 110), (HARB[0] - 2, HARB[1] - 3)), y=TY + 1)
    return b, 0
