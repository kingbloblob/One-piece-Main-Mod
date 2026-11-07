"""The Ruins of the Ancient Kingdom v3 (2026-10-30 audit: the v1 ruins were a flat plate of low walls). Redone with the
Minecraft Builder skill: the great kingdom erased in the Void Century, its broken island drifting in the End with
chunks bitten out of its rim and rock islets hanging round it. Silhouette first: a ring of sixteen colossal columns
round the plaza, snapped at all heights, three of them fallen across the streets; the great stepped temple on the
north rising in five tiers to a shrine; the fallen great gate on the south, its lintel lying in two pieces; and the
toppled giant statue, its head lying on its cheek in the east and its open hand in the west. Between them streets
of roofless stone houses, old trees grown up through them, moss and ferns everywhere. Inside the temple: the hall
of murals and, down a stair, the sealed archive where a Poneglyph stands on its plinth with the scholars' reading
room round it and the kingdom's last treasure. 170 x 170. Canvas y 0 = the island top, world y 62."""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, st, set_if_air
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb import holy_kit as HK
from mcb import impel_kit as K

SID = "void_century_ruins"
TITLE = "Ruins of the Ancient Kingdom (Void Century)"
CUTS = [3, -8, 14]
TILER = dict(terrain="none", sky_y=62)

N = 170
CX, CZ = 85, 85
RUIN = ("minecraft:stone_bricks", "minecraft:cracked_stone_bricks", "minecraft:mossy_stone_bricks", "onepiece:shandian_ruin_stone",
        "minecraft:stone_bricks", "onepiece:ancient_glyph_stone", "minecraft:mossy_cobblestone")
PAVE = [("onepiece:shandian_ruin_stone", 0.3), ("minecraft:stone_bricks", 0.2), ("minecraft:cracked_stone_bricks", 0.15),
        ("minecraft:mossy_stone_bricks", 0.15), ("minecraft:moss_block", 0.1), ("minecraft:gravel", 0.1)]
ROCK = ("minecraft:end_stone", "minecraft:stone", "minecraft:end_stone", "minecraft:andesite", "minecraft:tuff", "minecraft:end_stone")
LAWN = [("minecraft:grass_block", 0.55), ("minecraft:moss_block", 0.18), ("minecraft:coarse_dirt", 0.1), ("minecraft:podzol", 0.09),
        ("minecraft:rooted_dirt", 0.08)]


def broken(X, Z):
    """Chunks bitten out of the rim: three round bites and a ragged crack."""
    m = np.zeros(np.broadcast(X, Z).shape, bool)
    for (bx, bz, r) in ((CX + 74, CZ - 30, 22), (CX - 60, CZ + 60, 20), (CX + 20, CZ + 82, 16)):
        m |= np.hypot(X - bx, Z - bz) < r + 4 * NT.noise(X, Z, 4601, 6)
    return m


def column(bb, x, z, h, r, rng):
    """A colossal column snapped at h: a base, a fluted shaft, a jagged broken top."""
    bb.fill(x - r - 1, 0, z - r - 1, x + r + 1, 1, z + r + 1, "onepiece:shandian_ruin_stone")
    for y in range(2, h + 1):
        rr = r if y < h - 3 else r - 0.4 * (y - h + 3) * rng.random()
        blk = RUIN[int(NT.noise(x + y, z, 4610, 3) * len(RUIN)) % len(RUIN)]
        bb.fill_where(x - r, y, z - r, x + r, y, z + r, lambda X, yy, Z, rr=rr: ((X - x) ** 2 + (Z - z) ** 2 <= rr * rr + 0.4)
                      & ((y < h - 2) | (NT.noise(X, Z, 4611 + y, 2) > 0.35)), blk)
    for (dx, dz) in ((r, 0), (-r, 0), (0, r), (0, -r)):          # flutes
        for y in range(3, h - 3, 2):
            bb.set(x + dx, y, z + dz, "minecraft:chiseled_stone_bricks" if y % 6 == 3 else "minecraft:cracked_stone_bricks")
    if h > 12:
        bb.fill(x - r, h + 1, z, x - r, h + 2, z, "minecraft:vine[east=true,north=false,south=false,up=false,west=false]")


def fallen_column(bb, x, z, L, r, ang):
    """A column lying on the ground along angle ang, cracked into drums."""
    ca, sa = math.cos(ang), math.sin(ang)
    for i in range(L):
        if i % 7 == 6:
            continue
        cx, cz = x + i * ca, z + i * sa
        blk = RUIN[i % len(RUIN)]
        bb.fill_where(int(cx - r - 1), 1, int(cz - r - 1), int(cx + r + 1), 2 * r + 1, int(cz + r + 1),
                      lambda X, y, Z, cx=cx, cz=cz: ((-(X - cx) * sa + (Z - cz) * ca) ** 2 + (y - r) ** 2 <= r * r + 0.5)
                      & (np.abs((X - cx) * ca + (Z - cz) * sa) <= 0.6), blk)


def temple(bb):
    """The stepped temple (north): five tiers, a stair up the south face, the shrine on top; the hall of murals in the
    bottom tier; the archive with the Poneglyph down a stair beneath."""
    tx, tz = CX, CZ - 44
    half = 24
    y = 0
    for k in range(5):
        h = 5
        hb = half - k * 4
        bb.fill(tx - hb, y + 1, tz - hb, tx + hb, y + h, tz + hb, RUIN[k % 3])
        bb.mix(tx - hb, y + 1, tz - hb, tx + hb, y + h, tz + hb, list(RUIN[:4]), [0.4, 0.25, 0.2, 0.15]) if k < 4 else None
        bb.fill(tx - hb, y + h, tz - hb, tx + hb, y + h, tz + hb, "onepiece:shandian_ruin_stone")
        for i in range(-hb, hb + 1, 4):                          # glyph band on every tier
            for (gx, gz) in ((tx + i, tz + hb), (tx + i, tz - hb), (tx + hb, tz + i), (tx - hb, tz + i)):
                bb.set(gx, y + 3, gz, "onepiece:ancient_glyph_stone")
        y += h
    # the stair up the south face
    for i in range(y):
        bb.fill(tx - 3, i + 1, tz + half - i * 4 // 5 + 1, tx + 3, i + 1, tz + half - i * 4 // 5 + 1,
                st("minecraft:stone_brick_stairs", "north"))
        bb.fill(tx - 3, i + 2, tz + half - i * 4 // 5 + 1, tx + 3, i + 5, tz + half - i * 4 // 5 + 1, AIR)
        bb.fill(tx - 3, 1, tz + half - i * 4 // 5 + 1, tx + 3, i, tz + half - i * 4 // 5 + 1, "minecraft:stone_bricks")
    for sx in (-4, 4):
        for i in range(0, y, 2):
            bb.set(tx + sx, i + 2, tz + half - i * 4 // 5 + 1, "minecraft:stone_brick_wall")
    # the shrine on top: a pillared hall with a broken roof, an altar and braziers
    sy = y + 1
    bb.fill(tx - 6, sy, tz - 6, tx + 6, sy, tz + 6, "minecraft:polished_andesite")
    for (dx, dz) in ((-6, -6), (6, -6), (-6, 6), (6, 6), (-6, 0), (6, 0), (0, -6), (-2, 6), (2, 6)):
        bb.fill(tx + dx, sy + 1, tz + dz, tx + dx, sy + 7 - (abs(dx + dz) % 3), tz + dz, "minecraft:chiseled_stone_bricks")
    bb.fill(tx - 6, sy + 7, tz - 6, tx + 1, sy + 7, tz - 2, "minecraft:stone_brick_slab[type=bottom,waterlogged=false]")
    bb.fill(tx - 1, sy + 1, tz - 2, tx + 1, sy + 1, tz - 2, "onepiece:ancient_glyph_stone")
    bb.set(tx, sy + 2, tz - 2, "minecraft:candle[candles=4,lit=true,waterlogged=false]")
    for dx in (-4, 4):
        bb.set(tx + dx, sy + 1, tz + 3, "minecraft:polished_blackstone_wall")
        bb.set(tx + dx, sy + 2, tz + 3, "minecraft:soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    # the hall of murals in the bottom tier: a long nave with glyph-stone walls, an entrance on the south
    hx1, hx2, hz1, hz2 = tx - 10, tx + 10, tz - 18, tz + 14
    bb.fill(hx1, 1, hz1, hx2, 8, hz2, AIR)
    bb.fill(hx1 - 1, 1, hz1, hx1 - 1, 8, hz2, "onepiece:ancient_glyph_stone")
    bb.fill(hx2 + 1, 1, hz1, hx2 + 1, 8, hz2, "onepiece:ancient_glyph_stone")
    bb.fill(hx1, 0, hz1, hx2, 0, hz2, "minecraft:polished_andesite")
    bb.fill(tx - 2, 1, hz2, tx + 2, 6, tz + half + 1, AIR)            # entrance under the stair
    bb.fill(tx - 2, 0, hz2, tx + 2, 0, tz + half + 1, "minecraft:polished_andesite")
    for z in range(hz1 + 3, hz2, 6):
        for x in (hx1 + 1, hx2 - 1):
            bb.fill(x, 1, z, x, 8, z, "minecraft:chiseled_stone_bricks")
        bb.set(tx - 6, 1, z, "minecraft:stone_brick_wall"); bb.set(tx - 6, 2, z, "minecraft:soul_lantern[hanging=false,waterlogged=false]")
        bb.set(tx + 6, 1, z, "minecraft:stone_brick_wall"); bb.set(tx + 6, 2, z, "minecraft:soul_lantern[hanging=false,waterlogged=false]")
    # murals: glyph pictures in contrasting stone on both walls (a giant, a ship, a crown, the sun)
    for (ox, pic) in ((hz1 + 4, ((0, 0, 0, 1, 0, 0, 0), (0, 0, 1, 1, 1, 0, 0), (0, 1, 0, 1, 0, 1, 0), (0, 0, 0, 1, 0, 0, 0), (0, 0, 1, 0, 1, 0, 0))),
                      (hz1 + 14, ((1, 0, 1, 0, 1, 0, 1), (1, 1, 1, 1, 1, 1, 1), (0, 1, 1, 1, 1, 1, 0), (0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0))),
                      (hz1 + 24, ((0, 0, 0, 1, 0, 0, 0), (1, 1, 1, 1, 1, 1, 1), (0, 1, 1, 1, 1, 1, 0), (0, 0, 1, 1, 1, 0, 0), (0, 0, 0, 0, 0, 0, 0)))):
        for j, row in enumerate(pic):
            for i, v in enumerate(row):
                if v:
                    bb.set(hx1 - 1, 7 - j, ox + i, "minecraft:gilded_blackstone")
                    bb.set(hx2 + 1, 7 - j, ox + i, "minecraft:gilded_blackstone")
    # down to the archive: a stair from the hall's north end
    ay = -12
    ax1, ax2, az1, az2 = tx - 12, tx + 12, tz - 18, tz + 4
    bb.fill(ax1 - 1, ay - 1, az1 - 1, ax2 + 1, -1, az2 + 1, "minecraft:deepslate_bricks")
    bb.fill(ax1, ay, az1, ax2, -2, az2, AIR)
    bb.fill(ax1, ay - 1, az1, ax2, ay - 1, az2, "minecraft:polished_deepslate")
    for i in range(11):
        bb.fill(tx - 1, -1 - i, hz1 + 1 + i, tx + 1, -1 - i, hz1 + 1 + i, st("minecraft:deepslate_brick_stairs", "south"))
        bb.fill(tx - 1, -i, hz1 + 1 + i, tx + 1, 1, hz1 + 1 + i, AIR) if i < 2 else bb.fill(tx - 1, -i, hz1 + 1 + i, tx + 1, -i + 3, hz1 + 1 + i, AIR)
        bb.fill(tx - 2, -i - 1, hz1 + 1 + i, tx - 2, -i + 3, hz1 + 1 + i, "minecraft:deepslate_bricks")
        bb.fill(tx + 2, -i - 1, hz1 + 1 + i, tx + 2, -i + 3, hz1 + 1 + i, "minecraft:deepslate_bricks")
    pz = az1 + 6
    bb.fill(tx - 3, ay, pz - 3, tx + 3, ay, pz + 3, "minecraft:polished_blackstone_bricks")
    bb.fill(tx - 2, ay + 1, pz - 2, tx + 2, ay + 1, pz + 2, "minecraft:polished_blackstone")
    bb.fill(tx - 1, ay + 2, pz, tx + 1, ay + 6, pz, "onepiece:poneglyph")
    bb.set(tx, ay + 7, pz, "onepiece:poneglyph")
    for dx in (-5, 5):
        bb.set(tx + dx, ay, pz, "minecraft:polished_blackstone_wall")
        bb.set(tx + dx, ay + 1, pz, "minecraft:soul_lantern[hanging=false,waterlogged=false]")
    # the reading room: shelves along the walls, reading desks, scrolls
    for x in range(ax1, ax2 + 1):
        if abs(x - tx) > 2:
            bb.fill(x, ay, az1, x, ay + 4, az1, "minecraft:bookshelf" if x % 5 else "minecraft:chiseled_bookshelf[facing=south,slot_0_occupied=true,slot_1_occupied=false,slot_2_occupied=true,slot_3_occupied=true,slot_4_occupied=false,slot_5_occupied=true]")
    for z in range(az1 + 1, az2 + 1):
        bb.fill(ax1, ay, z, ax1, ay + 3, z, "minecraft:bookshelf")
        bb.fill(ax2, ay, z, ax2, ay + 3, z, "minecraft:bookshelf")
    for (dx, dz) in ((-8, 0), (8, 0), (-8, -5), (8, -5)):
        x, z = tx + dx, az2 - 4 + dz
        bb.set(x, ay, z, "minecraft:spruce_fence"); bb.set(x, ay + 1, z, "minecraft:spruce_pressure_plate")
        bb.set(x + 1, ay, z, "minecraft:lectern[facing=west,has_book=true,powered=false]")
        bb.set(x - 1, ay, z, "minecraft:spruce_stairs[facing=east,half=bottom,shape=straight,waterlogged=false]")
    for x in range(ax1 + 3, ax2 - 2, 6):
        bb.set(x, -2, (az1 + az2) // 2, "minecraft:soul_lantern[hanging=true,waterlogged=false]")
    return (tx, tz, half)


def gate(bb):
    """The fallen great gate (south): two pylons with glyph bands, the lintel lying broken in front."""
    gz = CZ + 46
    for sx in (-1, 1):
        x = CX + sx * 9
        bb.fill(x - 3, 0, gz - 3, x + 3, 22 - (4 if sx > 0 else 0), gz + 3, RUIN[0])
        bb.mix(x - 3, 1, gz - 3, x + 3, 22 - (4 if sx > 0 else 0), gz + 3, list(RUIN[:4]), [0.4, 0.3, 0.2, 0.1])
        for y in (6, 12):
            bb.fill(x - 3, y, gz - 3, x + 3, y, gz + 3, "onepiece:ancient_glyph_stone")
    bb.fill(CX - 9, 1, gz + 6, CX - 1, 3, gz + 8, "onepiece:shandian_ruin_stone")
    bb.fill(CX + 2, 1, gz + 7, CX + 11, 3, gz + 9, "onepiece:shandian_ruin_stone")
    bb.fill(CX - 8, 2, gz + 6, CX - 2, 2, gz + 6, "onepiece:ancient_glyph_stone")
    bb.set(CX, 1, gz + 7, "minecraft:cracked_stone_bricks")


def statue_head(bb, x, z):
    """The toppled giant's head, lying on its right cheek facing south: a 15-block blocky head with brow, eye
    sockets, nose and lips, a crack and moss over it."""
    R = 8
    def head(X, y, Z):
        return ((X - x) / 7.0) ** 2 + ((y - 7) / 7.5) ** 2 + ((Z - z) / 8.5) ** 2 <= 1
    bb.fill_where(x - R, 0, z - R - 1, x + R, 15, z + R + 1, head, "minecraft:stone")
    bb.fill_where(x - R, 0, z - R - 1, x + R, 15, z + R + 1, lambda X, y, Z: head(X, y, Z) & (NT.noise(X + y, Z, 4620, 4) > 0.62),
                  "minecraft:mossy_cobblestone")
    # the face looks south (+z): eye sockets, the nose, the mouth, the brow line
    fz = z + 8
    for ey in (9, 5):
        bb.fill(x - 1, ey - 1, fz - 1, x + 1, ey, fz, AIR)
        bb.set(x, ey - 1, fz - 1, "minecraft:black_concrete")
    bb.fill(x + 2, 6, fz, x + 3, 8, fz + 1, "minecraft:stone")              # the nose
    bb.fill(x + 5, 5, fz - 1, x + 5, 9, fz - 1, "minecraft:polished_andesite")  # lips
    bb.fill(x - 3, 4, fz - 1, x - 3, 10, fz - 1, "minecraft:cobblestone")     # brow
    bb.fill(x - 7, 3, z - 6, x - 6, 11, z + 6, "minecraft:gold_block")          # the crown band, half buried
    bb.fill(x, 0, z - 2, x, 14, z - 2, AIR)                                      # a crack through it


def statue_hand(bb, x, z):
    """The giant's open hand palm up: the palm slab, four fingers and a thumb, cracked and mossy."""
    bb.fill(x - 6, 0, z - 5, x + 4, 3, z + 5, "minecraft:stone")
    for i, (dz, L) in enumerate(((-4, 9), (-1, 11), (2, 10), (5, 8))):
        bb.fill(x + 5, 1, z + dz - 1, x + 4 + L, 2 + (i % 2), z + dz, "minecraft:stone" if i % 2 else "minecraft:andesite")
        bb.fill(x + 4 + L - 2, 3 + (i % 2), z + dz - 1, x + 4 + L, 4 + (i % 2), z + dz, "minecraft:stone")
    bb.fill(x - 4, 1, z - 8, x - 1, 3, z - 6, "minecraft:stone")
    bb.fill(x - 3, 4, z - 10, x - 1, 5, z - 8, "minecraft:stone")
    bb.mix(x - 6, 3, z - 5, x + 4, 3, z + 5, ["minecraft:moss_carpet", "minecraft:air", "minecraft:air"], [0.4, 0.3, 0.3])
    bb.fill(x - 8, 0, z - 4, x - 6, 2, z + 4, "minecraft:cracked_stone_bricks")          # the wrist, broken off


def house_ruin(bb, x1, z1, w, d, rng):
    """A roofless stone house: walls snapped at 1-5 blocks, a doorway, a window, rubble and a fallen beam."""
    x2, z2 = x1 + w - 1, z1 + d - 1
    bb.fill(x1, 0, z1, x2, 0, z2, "minecraft:cobblestone")
    for (a, b, c, e) in ((x1, z1, x2, z1), (x1, z2, x2, z2), (x1, z1, x1, z2), (x2, z1, x2, z2)):
        for xx in range(a, c + 1):
            for zz in range(b, e + 1):
                h = int(1 + 4 * NT.noise(xx, zz, 4630, 4) ** 1.4)
                for y in range(1, h + 1):
                    bb.set(xx, y, zz, RUIN[int(rng.integers(0, len(RUIN)))])
    dx = x1 + w // 2
    bb.fill(dx, 1, z2, dx, 3, z2, AIR)
    bb.fill(x1 + 1, 0, z1 + 1, x2 - 1, 0, z2 - 1, "minecraft:coarse_dirt")
    bb.mix(x1 + 1, 1, z1 + 1, x2 - 1, 1, z2 - 1, ["minecraft:air", "minecraft:cobblestone_slab[type=bottom,waterlogged=false]",
                                                   "minecraft:moss_carpet", "minecraft:fern"], [0.6, 0.15, 0.15, 0.1])
    if rng.random() < 0.5:
        bb.fill(x1, 4, (z1 + z2) // 2, x2, 4, (z1 + z2) // 2, "minecraft:stripped_oak_log[axis=x]")


def islets(bb, rng):
    """Rock islets hanging round the island, some with a ruin on top."""
    for (ix, iz, r, y) in ((8, 30, 7, 10), (160, 70, 6, -8), (30, 160, 8, 6), (150, 150, 5, 16), (100, 4, 6, -4)):
        for yy in range(y - r * 2, y + 1):
            t = (y - yy) / (r * 2)
            rr = r * (1 - t) ** 0.8
            blk = "minecraft:grass_block" if yy == y else ROCK[(yy // 2) % len(ROCK)]
            bb.fill_where(ix - r - 1, yy, iz - r - 1, ix + r + 1, yy, iz + r + 1,
                          lambda X, _, Z, rr=rr: (X - ix) ** 2 + (Z - iz) ** 2 <= rr * rr * (0.8 + 0.4 * NT.noise(X, Z, 4640, 3)), blk)
        if r > 6:
            bb.fill(ix - 1, y + 1, iz - 1, ix + 1, y + 4, iz - 1, "minecraft:cracked_stone_bricks")
            bb.set(ix, y + 5, iz - 1, "minecraft:stone_brick_slab[type=bottom,waterlogged=false]")


def design():
    bb = BigBuild(seed=4600, y_min=-60, y_max=60)
    rng = np.random.default_rng(4600)
    shp = HK.floating_island(bb, CX, CZ, 76, 4603, depth=46, strata=ROCK, lawn=LAWN, broken=broken)
    islets(bb, rng)
    zero = lambda X, Z: np.zeros(np.broadcast(X, Z).shape)
    # the plaza and the main streets (cross + ring), paved and worn
    NT.cover(bb, CX - 24, CZ - 22, CX + 24, CZ + 26, zero, PAVE, 4604, mask=lambda X, Z: np.hypot(X - CX, Z - CZ) < 23)
    for (a, b, c, d) in ((CX - 3, CZ, CX + 3, CZ + 70), (CX - 72, CZ - 3, CX + 72, CZ + 3)):
        NT.cover(bb, a, b, c, d, zero, PAVE, 4605, mask=lambda X, Z: shp(X, Z) > 1)
    NT.cover(bb, 0, 0, N - 1, N - 1, zero, PAVE, 4606, mask=lambda X, Z: (np.abs(np.hypot(X - CX, Z - CZ) - 40) < 2) & (shp(X, Z) > 1))
    # the ring of sixteen colossal columns, snapped at all heights, three fallen
    for k in range(16):
        a = math.radians(k * 22.5 + 11)
        x, z = round(CX + 31 * math.cos(a)), round(CZ + 31 * math.sin(a))
        if k in (3, 9, 13):
            fallen_column(bb, x, z, int(rng.integers(16, 26)), 2, a + math.pi / 2 * (1 if k % 2 else -1))
            bb.fill(x - 3, 0, z - 3, x + 3, 2, z + 3, "onepiece:shandian_ruin_stone")
            continue
        column(bb, x, z, int(rng.integers(14, 38)), 3, rng)
    # the plaza's centre: a cracked round dais with the base of a statue
    bb.cylinder(CX, 0, CZ, 8, 1, "onepiece:shandian_ruin_stone")
    bb.cylinder(CX, 2, CZ, 5, 2, "minecraft:polished_andesite")
    bb.fill(CX - 2, 3, CZ - 1, CX - 1, 5, CZ + 1, "minecraft:stone")
    bb.fill(CX + 1, 3, CZ - 1, CX + 2, 4, CZ + 1, "minecraft:stone")
    temple(bb)
    gate(bb)
    statue_head(bb, CX + 50, CZ + 8)
    statue_hand(bb, CX - 52, CZ - 6)
    # streets of roofless houses in the outer ring
    taken = [(CX - 34, CZ - 70, CX + 34, CZ - 18), (CX - 36, CZ - 36, CX + 36, CZ + 36), (CX - 16, CZ + 40, CX + 16, CZ + 58),
             (CX + 38, CZ - 6, CX + 62, CZ + 24), (CX - 66, CZ - 20, CX - 40, CZ + 8)]
    n = 0
    for _ in range(3000):
        w, d = int(rng.integers(6, 11)), int(rng.integers(6, 10))
        x, z = int(rng.integers(6, N - 16)), int(rng.integers(6, N - 16))
        corners = np.array([[shp(np.array([[xx]]), np.array([[zz]]))[0, 0] for xx in (x, x + w) for zz in (z, z + d)]])
        if corners.min() < 4 or abs(x + w / 2 - CX) < 6 or abs(z + d / 2 - CZ) < 6 or abs(math.hypot(x + w / 2 - CX, z + d / 2 - CZ) - 40) < 7:
            continue
        if any(not (x + w + 2 < t[0] or x - 2 > t[2] or z + d + 2 < t[1] or z - 2 > t[3]) for t in taken):
            continue
        house_ruin(bb, x, z, w, d, rng)
        taken.append((x, z, x + w, z + d))
        n += 1
        if n >= 44:
            break
    # old trees grown up through the streets, moss and ferns everywhere
    t = 0
    for _ in range(800):
        x, z = int(rng.integers(6, N - 6)), int(rng.integers(6, N - 6))
        if shp(np.array([[x]]), np.array([[z]]))[0, 0] < 5 or any(a[0] - 2 <= x <= a[2] + 2 and a[1] - 2 <= z <= a[3] + 2 for a in taken):
            continue
        if int(bb.get_region(x, 1, z, x, 1, z)[0, 0, 0]) > 1:
            continue
        P.tree(bb, x, 1, z, height=int(rng.integers(7, 12)), kind="dark_oak" if rng.random() < 0.4 else "oak", rng=rng)
        t += 1
        if t >= 18:
            break
    NT.plants(bb, 0, 0, N - 1, N - 1, zero, 4650, density=0.3, kinds=["minecraft:fern", "minecraft:short_grass", "minecraft:large_fern",
              "minecraft:moss_carpet"], flowers=["minecraft:blue_orchid", "minecraft:azure_bluet"], mask=lambda X, Z: shp(X, Z) > 1)
    bb.fill_where(0, 1, 0, N - 1, 1, N - 1, lambda X, y, Z: (NT.noise(X, Z, 4651, 5) > 0.8) & (shp(X, Z) > 2), "minecraft:moss_carpet", only_empty=True)
    return bb


def build():
    bb = design()
    b = to_canvas(bb)
    b.chest(CX + 4, -12, CZ - 44 - 12, "legendary", "west")
    b.chest(CX - 4, -12, CZ - 44 - 12, "void_century", "east")
    b.chest(CX + 2, 1, CZ - 44 - 16, "treasure", "south")
    b.chest(CX - 50, 4, CZ - 6, "hard", "east")
    return b, 0
