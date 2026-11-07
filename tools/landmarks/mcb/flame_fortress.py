"""King's Flame Fortress v3 (2026-10-30 audit: the v1 fort was a small square with a stubby keep). Redone with the
Minecraft Builder skill: the stronghold of King the Wildfire, Kaido's right hand, on a burnt plain split by lava.
Silhouette first: a black five-tier Wano keep with red-lacquered posts and tiled eaves, and on its top the great
black pteranodon spreading burning wings 33 across; four squat round towers crowned with fire at the corners of a
black curtain wall, all inside a lava moat. A lowered drawbridge on chains crosses to the red gatehouse. In the
courtyard: the war-beast pens, the forge with its anvils and lava basin under a smoking chimney, two barracks, the
training ground with straw dummies, and red Beast Pirates banners. The keep has five floors of furnished rooms up to
King's war room with its map table. Round the fortress: scorched ground, basalt spires, dead trees and two lava rivers
feeding the moat. 150 x 150. Ground = y 0."""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, set_if_air, castle_eave, wing_floor, furnish, lamp_post
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.blazing_hell_furnace import block_house

SID = "flame_fortress"
TITLE = "King's Flame Fortress"
CUTS = [3, 18, 34]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 8

N = 150
CX, CZ = 75, 75
LAND = NT.outline(75, 75, 70, 4801, wobble=0.08)
SCORCH = "onepiece:scorched_stone"
BLACK = "minecraft:polished_blackstone_bricks"
BLACK2 = ["minecraft:polished_blackstone_bricks", "minecraft:cracked_polished_blackstone_bricks", "onepiece:scorched_stone",
          "minecraft:blackstone"]
ROOF = "onepiece:wano_roof_tiles"
ROOF_ST = "onepiece:wano_roof_tile_stairs"
LAVA = "minecraft:lava"
RED = "minecraft:red_concrete"
POST = "minecraft:crimson_stem[axis=y]"
BURNT = [("minecraft:blackstone", 0.22), ("minecraft:basalt[axis=y]", 0.14), ("minecraft:coarse_dirt", 0.2), ("onepiece:scorched_stone", 0.14),
         ("minecraft:gravel", 0.1), ("minecraft:magma_block", 0.04), ("minecraft:tuff", 0.1), ("minecraft:soul_soil", 0.06)]
W = 40          # curtain wall half size
MOAT = (44, 49)  # moat ring (inner, outer half size)
FH = 7


def sq(X, Z):
    return np.maximum(np.abs(X - CX), np.abs(Z - CZ))


def lava_river(X, Z):
    """Two lava rivers winding in from the east and the north-west to the moat."""
    a = np.abs(Z - (CZ + 8 + 9 * np.sin(X / 13.0))) < 2.2
    b = np.abs(X - (CX - 10 + 8 * np.sin(Z / 11.0))) < 2.0
    return ((a & (X > CX + MOAT[1] - 1)) | (b & (Z < CZ - MOAT[1] + 1))) & (LAND(X, Z) > 3)


def ground(bb):
    zero = lambda X, Z: np.zeros(np.broadcast(X, Z).shape)
    NT.cover(bb, 0, 0, N - 1, N - 1, zero, BURNT, 4802, mask=lambda X, Z: LAND(X, Z) > 0, core="minecraft:stone", base=-6)
    moat = lambda X, Z: (sq(X, Z) >= MOAT[0]) & (sq(X, Z) <= MOAT[1])
    bb.fill_where(0, -4, 0, N - 1, -4, N - 1, lambda X, y, Z: moat(X, Z) | lava_river(X, Z), "minecraft:basalt[axis=y]")
    bb.fill_where(0, -3, 0, N - 1, -1, N - 1, lambda X, y, Z: moat(X, Z) | lava_river(X, Z), LAVA)
    bb.fill_where(0, 0, 0, N - 1, 0, N - 1, lambda X, y, Z: moat(X, Z) | lava_river(X, Z), AIR)
    bb.fill_where(0, 0, 0, N - 1, 0, N - 1, lambda X, y, Z: (sq(X, Z) == MOAT[1] + 1) & (LAND(X, Z) > 0), "minecraft:polished_blackstone")
    # basalt spires and dead trees on the plain
    rng = np.random.default_rng(4804)
    for _ in range(18):
        x, z = int(rng.integers(6, N - 6)), int(rng.integers(6, N - 6))
        if sq(np.array([[x]]), np.array([[z]]))[0, 0] < MOAT[1] + 4 or LAND(np.array([[x]]), np.array([[z]]))[0, 0] < 4:
            continue
        h = int(rng.integers(4, 13))
        for y in range(1, h + 1):
            r = 1.8 * (1 - y / (h + 1)) + 0.3
            bb.fill_where(x - 2, y, z - 2, x + 2, y, z + 2, lambda X, yy, Z, r=r: (X - x) ** 2 + (Z - z) ** 2 <= r * r + 0.3,
                          "minecraft:basalt[axis=y]" if y % 3 else "minecraft:blackstone")
    for _ in range(30):
        x, z = int(rng.integers(6, N - 6)), int(rng.integers(6, N - 6))
        if sq(np.array([[x]]), np.array([[z]]))[0, 0] < MOAT[1] + 3 or LAND(np.array([[x]]), np.array([[z]]))[0, 0] < 3 \
                or lava_river(np.array([[x]]), np.array([[z]]))[0, 0]:
            continue
        h = int(rng.integers(4, 9))
        bb.fill(x, 1, z, x, h, z, "minecraft:dark_oak_log[axis=y]" if rng.random() < 0.5 else "minecraft:stripped_dark_oak_log[axis=y]")
        for k in range(2):
            a = rng.uniform(0, 2 * math.pi)
            bb.set(round(x + math.cos(a)), h - k, round(z + math.sin(a)), "minecraft:dark_oak_fence")
    NT.plants(bb, 0, 0, N - 1, N - 1, zero, 4805, density=0.12, kinds=["minecraft:dead_bush", "minecraft:short_dry_grass"],
              mask=lambda X, Z: (sq(X, Z) > MOAT[1] + 1) & (LAND(X, Z) > 1), ground=("coarse_dirt", "gravel", "soul_soil"))


def fire_crown(bb, x, y, z, r):
    """A ring of fire on netherrack set into blackstone, so it burns for ever and spreads nowhere."""
    bb.cylinder(x, y, z, r, y, "minecraft:polished_blackstone")
    for a in range(0, 360, 30):
        t = math.radians(a)
        fx, fz = round(x + (r - 1) * math.cos(t)), round(z + (r - 1) * math.sin(t))
        bb.set(fx, y, fz, "minecraft:netherrack")
        bb.set(fx, y + 1, fz, "minecraft:fire")
    bb.set(x, y, z, "minecraft:magma_block")


def curtain(bb):
    """The curtain wall, 15 high with merlons and red bands; four round towers crowned with fire; the gatehouse."""
    H = 15
    x1, x2, z1, z2 = CX - W, CX + W, CZ - W, CZ + W
    bb.fill(x1, -3, z1, x2, H, z2, BLACK)
    bb.mix(x1, 1, z1, x2, H, z2, BLACK2, [0.5, 0.2, 0.2, 0.1])
    bb.fill(x1 + 3, -3, z1 + 3, x2 - 3, H + 1, z2 - 3, AIR)
    bb.fill(x1 + 3, -3, z1 + 3, x2 - 3, 0, z2 - 3, "minecraft:stone")
    for y in (5, H - 2):
        for (a, b, c, d) in ((x1, z1, x2, z1), (x1, z2, x2, z2), (x1, z1, x1, z2), (x2, z1, x2, z2)):
            bb.fill(a, y, b, c, y, d, RED)
    for i in range(x1, x2 + 1, 2):
        for zz in (z1, z2):
            bb.set(i, H + 1, zz, BLACK)
    for i in range(z1, z2 + 1, 2):
        for xx in (x1, x2):
            bb.set(xx, H + 1, i, BLACK)
    for i in range(x1 + 6, x2 - 5, 9):                                   # braziers on the wall walk
        for zz in (z1 + 1, z2 - 1):
            bb.set(i, H + 1, zz, "minecraft:netherrack"); bb.set(i, H + 2, zz, "minecraft:fire")
    for i in range(z1 + 6, z2 - 5, 9):
        for xx in (x1 + 1, x2 - 1):
            bb.set(xx, H + 1, i, "minecraft:netherrack"); bb.set(xx, H + 2, i, "minecraft:fire")
    for (tx, tz) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        bb.cylinder(tx, -3, tz, 7, H + 10, BLACK)
        bb.cylinder(tx, 1, tz, 5, H + 9, AIR)
        for y in (H, H + 9):
            bb.ring(tx, y, tz, 6, 8, y, RED if y == H else BLACK)
        for y in (6, 13, 19):
            if y != 19:
                bb.cylinder(tx, y, tz, 5, y, "minecraft:crimson_planks")
        for (dx, dz) in ((7, 0), (-7, 0), (0, 7), (0, -7)):
            bb.fill(tx + dx, 8, tz + dz, tx + dx, 10, tz + dz, "minecraft:iron_bars[east=true,north=true,south=true,west=true,waterlogged=false]")
            bb.fill(tx + dx, 16, tz + dz, tx + dx, 17, tz + dz, "minecraft:iron_bars[east=true,north=true,south=true,west=true,waterlogged=false]")
        bb.cylinder(tx, H + 10, tz, 7, H + 10, BLACK)
        for a in range(0, 360, 20):
            t = math.radians(a)
            bb.set(round(tx + 7 * math.cos(t)), H + 11, round(tz + 7 * math.sin(t)), BLACK)
        fire_crown(bb, tx, H + 10, tz, 5)
        sx, sz = int(np.sign(CX - tx)), int(np.sign(CZ - tz))
        bb.fill(tx + sx * 5, 1, tz + sz * 2, tx + sx * 8, 3, tz + sz * 3, AIR)
        bb.fill(tx, 1, tz - 5, tx, H + 9, tz - 5, "minecraft:ladder[facing=south,waterlogged=false]")
        bb.fill(tx - 1, 6, tz - 4, tx + 1, 6, tz - 4, AIR); bb.fill(tx - 1, 13, tz - 4, tx + 1, 13, tz - 4, AIR)
    # the gatehouse: a red two-storey Wano gate over the south wall, the drawbridge lowered on chains
    gx1, gx2, gz1, gz2 = CX - 9, CX + 9, z2 - 5, z2 + 3
    bb.fill(gx1, -3, gz1, gx2, H + 7, gz2, BLACK)
    bb.fill(gx1 + 1, 1, gz1 + 1, gx2 - 1, H + 6, gz2 - 1, AIR)
    bb.fill(gx1 + 1, H, gz1 + 1, gx2 - 1, H, gz2 - 1, "minecraft:crimson_planks")
    for x in (gx1, gx2):
        for z in (gz1, gz2):
            bb.fill(x, 1, z, x, H + 6, z, POST)
    bb.fill(gx1, H + 7, gz1, gx2, H + 7, gz2, "minecraft:crimson_planks")
    castle_eave(bb, gx1, gz1, gx2, gz2, H + 7, ROOF_ST, ROOF, depth=2, bracket="minecraft:crimson_stairs")
    P.hip_roof(bb, gx1 - 1, gz1 - 1, gx2 + 1, gz2 + 1, H + 9, ROOF_ST)
    bb.fill(CX - 3, 1, gz1, CX + 3, 8, gz2, AIR)
    bb.fill(CX - 4, 9, gz2, CX + 4, 9, gz2, RED)
    for x in (CX - 4, CX + 4):
        bb.fill(x, 1, gz2, x, 8, gz2, POST)
    for y in range(10, 14):                                              # the Beast Pirates' skull sign over the gate
        bb.fill(CX - 2, y, gz2 + 1, CX + 2, y, gz2 + 1, "minecraft:bone_block[axis=y]" if y in (11, 12) else "minecraft:white_concrete")
    bb.set(CX - 1, 12, gz2 + 1, "minecraft:black_concrete"); bb.set(CX + 1, 12, gz2 + 1, "minecraft:black_concrete")
    bb.fill(CX - 3, 0, gz2, CX + 3, 0, CZ + MOAT[1] + 2, "minecraft:dark_oak_planks")   # the lowered drawbridge
    for z in range(gz2 + 1, CZ + MOAT[1] + 2, 3):
        bb.set(CX - 4, 0, z, "minecraft:polished_blackstone"); bb.set(CX + 4, 0, z, "minecraft:polished_blackstone")
    for i in range(1, 9):
        z = CZ + MOAT[1] + 1 - i
        y = i
        if z > gz2:
            bb.set(CX - 4, y, z, "minecraft:iron_chain[axis=y]"); bb.set(CX + 4, y, z, "minecraft:iron_chain[axis=y]")
    bb.fill(CX - 3, -1, gz2 + 1, CX + 3, -1, CZ + MOAT[1] + 1, "minecraft:polished_blackstone")


def wano_keep(bb, x1, z1, x2, z2, tiers, tracker, audit):
    """The keep: a battered black stone base, then `tiers` storeys stepping in, black walls with red posts every 4,
    windows, a tiled castle eave on each, chidori gables on the south; floors furnished; a ladder in the west."""
    by = 6
    for y in range(-3, by + 1):                                  # the battered base (ishigaki), stepping in
        d = max(0, (y - 0) // 3)
        bb.fill(x1 - 3 + d, y, z1 - 3 + d, x2 + 3 - d, y, z2 + 3 - d, "minecraft:blackstone" if y % 2 else BLACK)
    for k in range(4):
        bb.fill(CX - 4 + k, by - 1 - k, z2 + 2 + k * 1, CX + 4 - k, by - 1 - k, z2 + 2 + k, st("minecraft:polished_blackstone_brick_stairs", "north"))
    bb.fill(CX - 3, 1, z2 + 3, CX + 3, by - 1, z2 + 5, AIR)
    for i in range(by):
        bb.fill(CX - 2, i + 1, z2 + 7 - i, CX + 2, i + 1, z2 + 7 - i, st("minecraft:polished_blackstone_brick_stairs", "north"))
        bb.fill(CX - 2, i + 2, z2 + 7 - i, CX + 2, i + 5, z2 + 7 - i, AIR)
    y = by
    out = []
    for k in range(tiers):
        a1, c1, a2, c2 = x1 + 3 * k, z1 + 2 * k, x2 - 3 * k, z2 - 2 * k
        top = y + FH
        bb.fill(a1, y, c1, a2, y, c2, "minecraft:crimson_planks" if k else "minecraft:polished_blackstone")
        bb.fill(a1, y + 1, c1, a2, top - 1, c2, BLACK)
        bb.fill(a1 + 1, y + 1, c1 + 1, a2 - 1, top - 1, c2 - 1, AIR)
        for x in range(a1, a2 + 1, 4):
            for z in (c1, c2):
                bb.fill(x, y + 1, z, x, top - 1, z, POST)
        for z in range(c1, c2 + 1, 4):
            for x in (a1, a2):
                bb.fill(x, y + 1, z, x, top - 1, z, POST)
        for x in range(a1 + 2, a2 - 1, 4):
            for z in (c1, c2):
                bb.fill(x, y + 2, z, x, y + 3, z, "minecraft:red_stained_glass_pane")
        for z in range(c1 + 2, c2 - 1, 4):
            for x in (a1, a2):
                bb.fill(x, y + 2, z, x, y + 3, z, "minecraft:red_stained_glass_pane")
        for (a, b, c, d) in ((a1, c1, a2, c1), (a1, c2, a2, c2), (a1, c1, a1, c2), (a2, c1, a2, c2)):
            bb.fill(a, top - 1, b, c, top - 1, d, RED)
        castle_eave(bb, a1, c1, a2, c2, top - 1, ROOF_ST, ROOF, depth=2, bracket="minecraft:crimson_stairs")
        if k in (0, 2):
            gx = (a1 + a2) // 2
            for i in range(5):
                bb.fill(gx - 4 + i, top + i, c2 + 1, gx + 4 - i, top + i, c2 + 1, BLACK)
                bb.set(gx - 5 + i, top + i, c2 + 1, st(ROOF_ST, "east")); bb.set(gx + 5 - i, top + i, c2 + 1, st(ROOF_ST, "west"))
                bb.set(gx - 5 + i, top + i, c2 + 2, st(ROOF_ST, "east")); bb.set(gx + 5 - i, top + i, c2 + 2, st(ROOF_ST, "west"))
            bb.set(gx, top + 2, c2 + 1, "minecraft:shroomlight")
        out.append((a1, c1, a2, c2, y, top))
        y = top
    a1, c1, a2, c2, _, top = out[-1]
    bb.fill(a1 - 1, top, c1 - 1, a2 + 1, top, c2 + 1, BLACK)
    kinds = [("armory", "storage", "kitchen"), ("living", "bedroom", "library"), ("bedroom", "living", "storage"),
             ("library", "living"), ("living",)]
    for k, (b1, d1, b2, d2, fy, ftop) in enumerate(out):
        if k < 3:
            wing_floor(bb, b1 + 1, d1 + 1, b2 - 1, d2 - 1, fy + 1, FH - 2, BLACK, seed_of("ff", k), tracker, kinds[k], corridor="x", cw=3,
                       carpet=(None, "minecraft:red_carpet"), keep=[(x1 + 13, z1 + 9, x1 + 15, z1 + 12)], wood="crimson", audit=audit,
                       lamp="minecraft:lantern[hanging=true]")
        elif k < tiers - 1:
            furnish(bb, [(b1 + 1, d1 + 1, b2 - 1, d2 - 1)], fy + 1, FH - 2, list(kinds[k]), seed_of("fff", k), tracker,
                    doors=[(x1 + 14, z1 + 10)], wood="crimson", audit=audit)
    # the war room on the top floor: a map table, banners, weapon racks
    b1, d1, b2, d2, fy, ftop = out[-1]
    mx, mz = (b1 + b2) // 2, (d1 + d2) // 2
    bb.fill(mx - 2, fy + 1, mz - 1, mx + 2, fy + 1, mz + 1, "minecraft:crimson_planks")
    for (dx, dz) in ((-2, -1), (2, -1), (-2, 1), (2, 1)):
        bb.set(mx + dx, fy + 1, mz + dz, "minecraft:crimson_fence")
    bb.fill(mx - 2, fy + 2, mz - 1, mx + 2, fy + 2, mz + 1, "minecraft:brown_carpet")
    bb.set(mx, fy + 2, mz, "minecraft:red_carpet")
    for x in (b1 + 1, b2 - 1):
        bb.set(x, fy + 1, mz, "minecraft:polished_blackstone_wall")
        bb.set(x, fy + 2, mz, "minecraft:lantern[hanging=false,waterlogged=false]")
    lx, lz = x1 + 14, z1 + 10
    bb.fill(lx, by + 1, lz, lx, top - 1, lz, "minecraft:ladder[facing=south,waterlogged=false]")
    bb.fill(lx, by + 1, lz - 1, lx, top - 1, lz - 1, BLACK)
    bb.fill(CX - 1, by + 1, z2, CX + 1, by + 3, z2, AIR)
    return top


def pteranodon(bb, y0, z0):
    """King's pteranodon on the keep roof, wings spread east-west 55 across: a blackstone body, a long beak and swept
    crest pointing south, wings with a thick bony leading edge, finger claws and a dark membrane whose trailing edge
    burns (magma, shroomlight, fire on netherrack)."""
    cx = CX
    PB = "minecraft:polished_blackstone"
    bb.fill_where(cx - 5, y0, z0 - 10, cx + 5, y0 + 9, z0 + 10, lambda X, y, Z: ((X - cx) / 4.0) ** 2 + ((y - y0 - 4) / 4.5) ** 2 + ((Z - z0) / 9.0) ** 2 <= 1,
                  "minecraft:blackstone")
    for i in range(6):                                              # neck rising south
        bb.fill(cx - 2, y0 + 7 + i, z0 + 7 + i, cx + 2, y0 + 9 + i, z0 + 8 + i, "minecraft:blackstone")
    bb.fill_where(cx - 4, y0 + 11, z0 + 11, cx + 4, y0 + 18, z0 + 19, lambda X, y, Z: ((X - cx) / 3.0) ** 2 + ((y - y0 - 14) / 3.0) ** 2 + ((Z - z0 - 15) / 4.0) ** 2 <= 1, PB)
    for i in range(12):                                             # the long beak
        w = 1 if i < 7 else 0
        bb.fill(cx - w, y0 + 14 - i // 4, z0 + 19 + i, cx + w, y0 + 14 - i // 4, z0 + 19 + i, PB)
        if i < 8:
            bb.fill(cx - w, y0 + 12 - i // 4, z0 + 19 + i, cx + w, y0 + 12 - i // 4, z0 + 19 + i, PB)
    for i in range(14):                                             # the swept crest
        bb.fill(cx, y0 + 16 + i // 2, z0 + 12 - i, cx, y0 + 17 + i // 2, z0 + 12 - i, PB)
    for s in (-1, 1):                                               # burning eyes
        bb.set(cx + s * 3, y0 + 15, z0 + 17, "minecraft:shroomlight")
    for i in range(9):                                              # tail
        bb.set(cx, y0 + 3, z0 - 10 - i, "minecraft:blackstone_wall")
    for s in (-1, 1):
        for i in range(1, 25):
            x = cx + s * (3 + i)
            lift = int(5 * math.sin(i / 24 * math.pi)) + i // 4
            yl = y0 + 6 + lift
            chord = max(3, 15 - i // 2)
            bb.fill(x, yl, z0 + 3, x, yl + (1 if i < 16 else 0), z0 + 4, "minecraft:polished_blackstone_bricks")
            for c in range(1, chord):
                bb.set(x, yl - c // 3, z0 + 3 - c, "minecraft:black_stained_glass" if c < chord - 2 else "minecraft:magma_block")
            te = z0 + 3 - chord
            yt = yl - (chord - 1) // 3
            if i % 3 == 1:
                bb.set(x, yt, te, "minecraft:netherrack")
                bb.set(x, yt + 1, te, "minecraft:fire")
            elif i % 3 == 2:
                bb.set(x, yt, te, "minecraft:shroomlight")
            else:
                bb.set(x, yt, te, "minecraft:magma_block")
            if i in (8, 16):                                        # wing bones across the membrane
                for c in range(1, chord):
                    bb.set(x, yl - c // 3 + 1, z0 + 3 - c, PB)
        wx = cx + s * 28
        bb.fill(wx, y0 + 9, z0 + 3, wx + s, y0 + 13, z0 + 5, PB)       # the wing claws
        for (dz, dy) in ((6, 0), (5, 3)):
            bb.set(wx + s, y0 + 12 + dy, z0 + dz, PB)
    for s in (-1, 1):                                               # legs gripping the roof
        bb.fill(cx + s * 3, y0 - 2, z0 - 2, cx + s * 3, y0, z0 - 2, "minecraft:polished_blackstone_wall")
        bb.fill(cx + s * 3, y0 - 2, z0 - 1, cx + s * 3, y0 - 2, z0, PB)


def courtyard(bb, tracker, audit):
    """Inside the wall: beast pens (west), the forge (east), two barracks (south corners), the training ground,
    banners on poles."""
    zero = lambda X, Z: np.zeros(np.broadcast(X, Z).shape)
    NT.cover(bb, CX - W + 3, CZ - W + 3, CX + W - 3, CZ + W - 3, zero,
             [("minecraft:polished_blackstone", 0.3), ("minecraft:gravel", 0.2), ("minecraft:coarse_dirt", 0.2),
              ("minecraft:blackstone", 0.2), ("minecraft:packed_mud", 0.1)], 4810)
    # the war-beast pens: barred pens on a dirt yard along the west wall
    bars = "minecraft:iron_bars[east=true,north=true,south=true,west=true,waterlogged=false]"
    for i, z in enumerate(range(CZ - 30, CZ + 22, 9)):
        x1, x2 = CX - W + 3, CX - W + 10
        bb.fill(x1, 0, z, x2, 0, z + 8, "minecraft:coarse_dirt")
        bb.fill(x2, 1, z, x2, 4, z + 8, bars)
        bb.fill(x1, 1, z, x2, 1, z, BLACK); bb.fill(x1, 1, z + 8, x2, 1, z + 8, BLACK)
        bb.fill(x1, 2, z, x2, 4, z, bars); bb.fill(x1, 2, z + 8, x2, 4, z + 8, bars)
        bb.fill(x1, 5, z, x2, 5, z + 8, "minecraft:blackstone_slab[type=bottom,waterlogged=false]")
        bb.fill(x2, 1, z + 3, x2, 3, z + 4, AIR)
        bb.set(x2, 1, z + 3, "minecraft:iron_door[facing=east,half=lower,hinge=left,open=false,powered=false]")
        bb.set(x2, 2, z + 3, "minecraft:iron_door[facing=east,half=upper,hinge=left,open=false,powered=false]")
        bb.set(x2, 1, z + 4, bars); bb.set(x2, 2, z + 4, bars); bb.set(x2, 3, z + 3, bars); bb.set(x2, 3, z + 4, bars)
        bb.set(x1 + 1, 1, z + 2, "minecraft:hay_block[axis=x]"); bb.set(x1 + 1, 1, z + 6, "minecraft:bone_block[axis=y]")
        bb.set(x1 + 2, 1, z + 4, "minecraft:cauldron")
    # the forge: a black hall with an open front, anvils, blast furnaces, a lava basin and a tall chimney
    fx1, fx2, fz1, fz2 = CX + W - 18, CX + W - 3, CZ - 30, CZ - 14
    bb.fill(fx1, 0, fz1, fx2, 8, fz2, BLACK)
    bb.fill(fx1 + 1, 1, fz1 + 1, fx2 - 1, 7, fz2 - 1, AIR)
    bb.fill(fx1, 1, fz1 + 3, fx1, 6, fz2 - 3, AIR)
    for z in range(fz1 + 3, fz2 - 2, 3):
        bb.fill(fx1, 1, z, fx1, 7, z, POST)
    castle_eave(bb, fx1, fz1, fx2, fz2, 8, ROOF_ST, ROOF, depth=1)
    P.hip_roof(bb, fx1 - 1, fz1 - 1, fx2 + 1, fz2 + 1, 9, ROOF_ST)
    bb.fill(fx2 - 4, 0, fz1 + 2, fx2 - 2, 0, fz1 + 4, LAVA)
    bb.fill(fx2 - 5, 1, fz1 + 1, fx2 - 1, 1, fz1 + 5, "minecraft:polished_blackstone_bricks")
    bb.fill(fx2 - 4, 1, fz1 + 2, fx2 - 2, 1, fz1 + 4, "minecraft:iron_bars[east=true,north=true,south=true,west=true,waterlogged=false]")
    bb.fill(fx2 - 4, 1, fz1 + 2, fx2 - 2, 1, fz1 + 4, AIR)
    bb.fill(fx2 - 4, 1, fz1 + 2, fx2 - 2, 1, fz1 + 2, "minecraft:polished_blackstone_bricks")
    bb.fill(fx2 - 3, 9, fz1 + 3, fx2 - 3, 20, fz1 + 3, "minecraft:bricks")
    bb.fill(fx2 - 4, 9, fz1 + 2, fx2 - 2, 14, fz1 + 4, "minecraft:bricks")
    bb.set(fx2 - 3, 21, fz1 + 3, "minecraft:campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]")
    for (x, z, blk) in ((fx1 + 3, fz1 + 3, "minecraft:anvil[facing=north]"), (fx1 + 6, fz1 + 3, "minecraft:damaged_anvil[facing=east]"),
                        (fx1 + 3, fz2 - 3, "minecraft:blast_furnace[facing=east,lit=true]"), (fx1 + 4, fz2 - 3, "minecraft:blast_furnace[facing=east,lit=true]"),
                        (fx1 + 6, fz2 - 2, "minecraft:grindstone[face=floor,facing=north]"), (fx1 + 8, fz2 - 2, "minecraft:smithing_table"),
                        (fx2 - 2, fz2 - 2, "minecraft:barrel[facing=up,open=false]"), (fx2 - 3, fz2 - 2, "minecraft:barrel[facing=up,open=false]"),
                        (fx1 + 9, fz1 + 3, "minecraft:water_cauldron[level=3]")):
        bb.set(x, 1, z, blk)
    for x in range(fx1 + 2, fx2 - 1, 4):
        bb.set(x, 7, (fz1 + fz2) // 2, "minecraft:lantern[hanging=true,waterlogged=false]")
    # two barracks in the south corners, a training ground with straw dummies between them
    block_house(bb, CX - W + 4, CZ + W - 17, CX - W + 17, CZ + W - 4, 2, BLACK, "minecraft:crimson_planks", "minecraft:blackstone_slab[type=bottom,waterlogged=false]",
                "minecraft:red_stained_glass_pane", ("barracks", "mess"), "crimson", "north", 4820)
    block_house(bb, CX + W - 17, CZ + W - 17, CX + W - 4, CZ + W - 4, 2, BLACK, "minecraft:crimson_planks", "minecraft:blackstone_slab[type=bottom,waterlogged=false]",
                "minecraft:red_stained_glass_pane", ("barracks", "armory"), "crimson", "north", 4821)
    for x in range(CX + 18, CX + W - 6, 4):
        for z in (CZ + 2, CZ + 8):
            bb.set(x, 1, z, "minecraft:oak_fence"); bb.set(x, 2, z, "minecraft:hay_block[axis=y]"); bb.set(x, 3, z, "minecraft:carved_pumpkin[facing=south]")
    # Beast Pirates banners on poles along the approach
    for z in range(CZ + 14, CZ + W - 4, 8):
        for x in (CX - 7, CX + 7):
            bb.fill(x, 1, z, x, 9, z, "minecraft:dark_oak_fence")
            bb.fill(x + (1 if x > CX else -1), 5, z, x + (1 if x > CX else -1), 8, z, "minecraft:red_wool")
            bb.set(x + (1 if x > CX else -1), 7, z, "minecraft:bone_block[axis=y]")
            bb.set(x, 10, z, "minecraft:lantern[hanging=false,waterlogged=false]")


def design():
    bb = BigBuild(seed=4800, y_min=-8, y_max=80)
    tracker = P.PropTracker(4800)
    audit = []
    ground(bb)
    curtain(bb)
    courtyard(bb, tracker, audit)
    top = wano_keep(bb, CX - 17, CZ - 32, CX + 17, CZ - 6, 5, tracker, audit)
    pteranodon(bb, top + 1, CZ - 19)
    return bb, audit


def build():
    bb, audit = design()
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    b.chest(CX + 3, 6 + 4 * FH + 1, CZ - 18, "treasure", "west")
    b.chest(CX - 14, 7, CZ - 29, "hard", "east")
    b.chest(CX + W - 6, 1, CZ - 16, "medium", "west")
    b.guards("gifter", ((CX - 6, CZ + 20), (CX + 6, CZ + 20), (CX + 20, CZ - 6)), y=1)
    b.guards("flame_guard", ((CX - 20, CZ), (CX, CZ - 2)), y=1)
    b.npc(CX, 6 + 4 * FH + 1, CZ - 16, "king", True)
    b.guards("headliner", ((CX, CZ + 34),), y=1)
    return b, 0
