"""Killer's hideout in Kuri v2 (Wano), redesigned with the Minecraft Builder skill: where the masked assassin "Kamazo"
lies low between jobs for the Beasts Pirates.

A dark bamboo grove on the Kuri hills, thick and gloomy, with dark pines and mossy rocks; paths of stepping stones
lead to a walled samurai estate. A white plaster wall with black posts and a tiled coping runs round it; on the south
the two-storey gatehouse with its curved roof. Inside: the main house on a stone base (dark posts, white paper
lattice, an engawa all round under deep curved eaves) with tatami rooms: the sitting room, the sword room, the
kitchen, Killer's room with the laughing mask on the wall and the bedrooms; the koi pond with a red arched bridge and
stone lanterns; the white storehouse (kura); a little shrine with a red torii; and Killer's training yard: slashed
straw posts, sliced bamboo, a rack of the scythe blades of his Punisher, and the targets cut to ribbons.
160 x 160. Ground = y 3, sea y 0. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, set_if_air, lamp_post, glyph
from mcb.bridge import to_canvas
from mcb import nature as NT
import mcasian as A  # noqa: E402  (the skill folder is on sys.path once mcb.kit is imported)

SID = "kamazo_hideout"
TITLE = "Killer's Hideout (Kuri, Wano)"
CUTS = [4, 9]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 160
TY = 3
EST = (44, 40, 116, 116)        # estate wall x1, z1, x2, z2
HOUSE = (58, 50, 92, 68)        # main house body x1, z1, x2, z2
GATE_X = 80
YARD = (96, 76, 112, 108)       # training yard
POND = (66, 94)
PLASTER = "minecraft:white_terracotta"
POST = "minecraft:dark_oak_log[axis=y]"
TILE_ST = "minecraft:deepslate_tile_stairs"
TATAMI = "minecraft:bamboo_mosaic"
WANO = dict(column="minecraft:stripped_dark_oak_log", beam="minecraft:dark_oak_planks", soffit="minecraft:dark_oak_planks",
            panel="minecraft:white_wool", lattice="minecraft:dark_oak_planks", wall_low="minecraft:white_terracotta",
            floor="minecraft:dark_oak_planks", ornament="minecraft:dark_oak_planks", bracket="minecraft:stripped_dark_oak_log",
            bracket_stairs="minecraft:dark_oak_stairs")
MASK = [".#####.",
        "#.....#",
        "#.#.#.#",
        "#.....#",
        "#.###.#",
        ".#####."]
_ISLE = NT.outline(80, 80, 66, 8410, wobble=0.08)
GRASS = [("minecraft:podzol", 0.35), ("minecraft:moss_block", 0.2), ("minecraft:grass_block", 0.25), ("minecraft:coarse_dirt", 0.1),
         ("minecraft:rooted_dirt", 0.1)]
SAND = [("minecraft:gravel", 0.35), ("minecraft:stone", 0.3), ("minecraft:andesite", 0.2), ("minecraft:sand", 0.15)]
GRAVEL = [("minecraft:gravel", 0.55), ("minecraft:light_gray_concrete_powder", 0.2), ("minecraft:andesite", 0.15), ("minecraft:tuff", 0.1)]


def shore(X, Z):
    return _ISLE(X, Z)


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = shore(X, Z)
    hills = TY + NT.fbm(X, Z, 8411, 26) * 9 - 2 + 4 * np.clip(d / 30.0, 0, 1)
    h = np.where(d < 10, TY * np.clip(d / 10.0, 0, 1) + 0.3, hills)
    x1, z1, x2, z2 = EST
    dx = np.maximum(np.maximum(x1 - 6 - X, X - x2 - 6), 0)
    dz = np.maximum(np.maximum(z1 - 6 - Z, Z - z2 - 14), 0)
    flat = np.clip(1 - np.hypot(dx, dz) / 12.0, 0, 1)
    h = np.where(d >= 10, h * (1 - flat) + TY * flat, h)
    return np.where(d < 1.5, -1, np.round(h))


X_, Z_ = np.arange(N)[:, None].astype(float), np.arange(N)[None, :].astype(float)
HMAP, SHORE = _height(X_, Z_).astype(int), shore(X_, Z_)


def height(X, Z):
    return HMAP[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def sh(X, Z):
    return SHORE[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def land(X, Z):
    return sh(X, Z) > 1.5


def hy(x, z):
    return int(HMAP[min(max(x, 0), N - 1), min(max(z, 0), N - 1)])


def inside(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    return (X > EST[0]) & (X < EST[2]) & (Z > EST[1]) & (Z < EST[3])


def raked(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    m = inside(X, Z) & (np.abs(X - GATE_X) <= 2) & (Z > HOUSE[3])
    m |= (X >= YARD[0]) & (X <= YARD[2]) & (Z >= YARD[1]) & (Z <= YARD[3])
    m |= inside(X, Z) & (Z > HOUSE[3]) & (Z < HOUSE[3] + 8) & (X > HOUSE[0] - 4) & (X < HOUSE[2] + 4)
    return m


def path(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    return (np.abs(X - (GATE_X + 4 * np.sin(Z * 0.09))) <= 1.4) & (Z > EST[3])


def terrain(bb):
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SAND, 8420, mask=lambda X, Z: land(X, Z) & (sh(X, Z) < 8), under="minecraft:stone",
             core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, GRASS, 8421, mask=lambda X, Z: land(X, Z) & (sh(X, Z) >= 8) & ~raked(X, Z) & ~path(X, Z),
             core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, GRAVEL, 8422, mask=lambda X, Z: land(X, Z) & (sh(X, Z) >= 8) & (raked(X, Z) | path(X, Z)),
             core="minecraft:stone")
    bed = lambda X, Z: np.round(-2 - np.clip(-sh(X, Z) * 0.45, 0, 9))
    sea = lambda X, Z: ~land(X, Z)
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: sea(X, Z) & (yy > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: sea(X, Z) & (yy == bed(X, Z)), "minecraft:gravel")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: sea(X, Z) & (yy < bed(X, Z)) & (yy >= bed(X, Z) - 2), "minecraft:stone")
    # stepping stones along the path
    for z in range(EST[3] + 2, N - 4, 2):
        x = int(round(GATE_X + 4 * math.sin(z * 0.09)))
        if land(np.array([x]), np.array([z]))[0] and sh(np.array([x]), np.array([z]))[0] >= 8:
            bb.set(x, hy(x, z), z, "minecraft:polished_andesite")


# ------------------------------------------------------------------ estate wall and gatehouse
def estate_wall(bb):
    x1, z1, x2, z2 = EST
    for (ax, az, bx, bz) in ((x1, z1, x2, z1), (x1, z2, x2, z2), (x1, z1, x1, z2), (x2, z1, x2, z2)):
        bb.fill(ax, TY - 2, az, bx, TY, bz, "minecraft:stone_bricks")
        bb.fill(ax, TY + 1, az, bx, TY + 4, bz, PLASTER)
        bb.fill(ax, TY + 1, az, bx, TY + 1, bz, "minecraft:polished_andesite")
    for x in range(x1, x2 + 1, 4):
        for z in (z1, z2):
            bb.fill(x, TY + 1, z, x, TY + 4, z, POST)
    for z in range(z1, z2 + 1, 4):
        for x in (x1, x2):
            bb.fill(x, TY + 1, z, x, TY + 4, z, POST)
    # tiled coping
    for x in range(x1 - 1, x2 + 2):
        bb.set(x, TY + 5, z1, "minecraft:deepslate_tile_slab[type=bottom]")
        bb.set(x, TY + 5, z2, "minecraft:deepslate_tile_slab[type=bottom]")
        bb.set(x, TY + 4, z1 - 1, st(TILE_ST, "south", "top")) if False else None
        bb.set(x, TY + 5, z1 - 1, st(TILE_ST, "south"))
        bb.set(x, TY + 5, z1 + 1, st(TILE_ST, "north"))
        bb.set(x, TY + 5, z2 - 1, st(TILE_ST, "south"))
        bb.set(x, TY + 5, z2 + 1, st(TILE_ST, "north"))
    for z in range(z1, z2 + 1):
        bb.set(x1, TY + 5, z, "minecraft:deepslate_tile_slab[type=bottom]")
        bb.set(x2, TY + 5, z, "minecraft:deepslate_tile_slab[type=bottom]")
        bb.set(x1 - 1, TY + 5, z, st(TILE_ST, "east"))
        bb.set(x1 + 1, TY + 5, z, st(TILE_ST, "west"))
        bb.set(x2 - 1, TY + 5, z, st(TILE_ST, "east"))
        bb.set(x2 + 1, TY + 5, z, st(TILE_ST, "west"))
    # the gatehouse on the south wall
    gx1, gx2, gz1, gz2 = GATE_X - 6, GATE_X + 6, z2 - 3, z2 + 3
    bb.fill(gx1, TY - 2, gz1, gx2, TY, gz2, "minecraft:stone_bricks")
    bb.fill(gx1, TY + 1, gz1, gx2, TY + 10, gz2, PLASTER)
    bb.fill(gx1 + 1, TY + 1, gz1 + 1, gx2 - 1, TY + 10, gz2 - 1, AIR)
    for (x, z) in ((gx1, gz1), (gx2, gz1), (gx1, gz2), (gx2, gz2), (GATE_X - 2, gz1), (GATE_X + 2, gz1), (GATE_X - 2, gz2), (GATE_X + 2, gz2)):
        bb.fill(x, TY + 1, z, x, TY + 10, z, POST)
    bb.fill(GATE_X - 1, TY + 1, gz1, GATE_X + 1, TY + 4, gz2, AIR)
    bb.fill(gx1 + 1, TY + 5, gz1 + 1, gx2 - 1, TY + 5, gz2 - 1, "minecraft:dark_oak_planks")
    bb.fill(GATE_X - 1, TY + 5, gz1, GATE_X + 1, TY + 5, gz2, "minecraft:dark_oak_planks")
    for x in (GATE_X - 1, GATE_X + 1):
        bb.set(x, TY + 1, gz2, f"minecraft:dark_oak_door[facing=south,half=lower,hinge={'left' if x < GATE_X else 'right'},open=true]")
        bb.set(x, TY + 2, gz2, f"minecraft:dark_oak_door[facing=south,half=upper,hinge={'left' if x < GATE_X else 'right'},open=true]")
    for x in range(gx1 + 2, gx2 - 1, 3):
        bb.fill(x, TY + 7, gz2, x, TY + 8, gz2, "minecraft:white_stained_glass_pane") if abs(x - GATE_X) > 1 else None
    bb.set(gx1 + 1, TY + 6, gz1 + 1, "minecraft:barrel[facing=up,open=false]")
    bb.fill(gx1 + 1, TY + 1, gz1 + 1, gx1 + 1, TY + 5, gz1 + 1, "minecraft:ladder[facing=east]")
    bb.set(gx1 + 1, TY + 6, gz1 + 2, "minecraft:lantern[hanging=false]")
    A.curved_roof(bb, gx1 - 3, gz1 - 3, gx2 + 3, gz2 + 3, TY + 11, 5, style="irimoya", pal=WANO)
    for x in (GATE_X - 3, GATE_X + 3):
        bb.set(x, TY + 4, gz2 + 1, "minecraft:lantern[hanging=false]") if False else None
        bb.set(x, TY + 4, gz2 + 1, "minecraft:soul_lantern[hanging=false]")


# ------------------------------------------------------------------ the main house
def main_house(bb, tracker, audit):
    x1, z1, x2, z2 = HOUSE
    A.stone_platform(bb, x1 - 4, z1 - 4, x2 + 4, z2 + 4, TY - 1, 3, pal=WANO)
    fy = TY + 2                                    # floor level (on the platform)
    # engawa: plank deck round the house under the eaves
    bb.fill(x1 - 3, fy - 1, z1 - 3, x2 + 3, fy - 1, z2 + 3, "minecraft:dark_oak_planks")
    for x in range(x1 - 3, x2 + 4, 4):
        for z in (z1 - 3, z2 + 3):
            bb.fill(x, fy, z, x, fy + 5, z, POST)
    for z in range(z1 - 3, z2 + 4, 4):
        for x in (x1 - 3, x2 + 3):
            bb.fill(x, fy, z, x, fy + 5, z, POST)
    # walls: posts every 4, white paper lattice panels with a plaster dado
    H = 6
    bb.fill(x1, fy, z1, x2, fy + H - 1, z2, PLASTER)
    bb.fill(x1 + 1, fy, z1 + 1, x2 - 1, fy + H - 1, z2 - 1, AIR)
    for (ax, az, bx, bz, axis) in ((x1, z1, x2, z1, "x"), (x1, z2, x2, z2, "x"), (x1, z1, x1, z2, "z"), (x2, z1, x2, z2, "z")):
        if axis == "x":
            for x in range(ax, bx + 1):
                if (x - ax) % 4:
                    bb.fill(x, fy + 2, az, x, fy + 4, az, "minecraft:white_stained_glass_pane" if (x - ax) % 2 else "minecraft:dark_oak_fence")
                else:
                    bb.fill(x, fy, az, x, fy + H - 1, az, POST)
        else:
            for z in range(az, bz + 1):
                if (z - az) % 4:
                    bb.fill(ax, fy + 2, z, ax, fy + 4, z, "minecraft:white_stained_glass_pane" if (z - az) % 2 else "minecraft:dark_oak_fence")
                else:
                    bb.fill(ax, fy, z, ax, fy + H - 1, z, POST)
    bb.fill(x1, fy + H, z1, x2, fy + H, z2, "minecraft:dark_oak_planks")
    bb.fill(x1 + 1, fy - 1, z1 + 1, x2 - 1, fy - 1, z2 - 1, TATAMI)
    # rooms: a corridor along the south side, rooms behind; sliding-door gaps
    rooms, doors = P.bsp_rooms(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 4, fy, H - 1, "minecraft:white_wool", seed=8430, min_room=6, max_room=11)
    bb.fill(x1 + 1, fy, z2 - 3, x2 - 1, fy + H - 2, z2 - 3, "minecraft:white_wool")
    cdoors = []
    for r in rooms:
        if r[3] >= z2 - 5:
            dx = (r[0] + r[2]) // 2
            bb.fill(dx, fy, z2 - 3, dx + 1, fy + 1, z2 - 3, AIR)
            cdoors.append((dx, z2 - 3))
    kinds = ["living", "workshop", "kitchen", "bedroom", "bedroom", "library", "storage"]
    for i, r in enumerate(rooms):
        P.furnish_room(bb, r, fy, kind=kinds[i % len(kinds)], height=H - 1, seed=8431 + i, wood="dark_oak", tracker=tracker,
                       doors=doors + cdoors)
        txt, ok = P.audit_props(bb, [r], fy, H - 1)
        if not ok:
            audit.append(txt)
    # the sword room (first room): a rack of katanas = iron bars on dark oak, and Killer's laughing mask on the wall
    r0 = rooms[0]
    for x in range(r0[0] + 1, r0[2], 2):
        set_if_air(bb, x, fy + 2, r0[1], "minecraft:iron_bars")
    glyph(bb, MASK, (r0[0] + r0[2]) // 2 - 3, fy + H - 1, z1 + 1, "minecraft:white_concrete") if r0[1] == z1 + 1 else None
    # the entrance: steps up to the engawa and the door gap in the south wall
    ex = (x1 + x2) // 2
    bb.fill(ex - 1, fy, z2, ex + 1, fy + 2, z2, AIR)
    for i in range(3):
        bb.fill(ex - 2, TY - 1 + i, z2 + 6 - i, ex + 2, TY - 1 + i, z2 + 6 - i, st("minecraft:stone_brick_stairs", "north"))
    # big curved irimoya roof over everything
    A.curved_roof(bb, x1 - 6, z1 - 6, x2 + 6, z2 + 6, fy + H + 1, 10, style="irimoya", pal=WANO)
    return (x1 - 7, z1 - 7, x2 + 7, z2 + 7)


def kura(bb, x, z):
    """The white storehouse: black stone base, thick white walls, a small iron door, tiled roof."""
    y = TY
    bb.fill(x, y - 2, z, x + 9, y + 1, z + 7, "minecraft:polished_blackstone_bricks")
    bb.fill(x, y + 2, z, x + 9, y + 8, z + 7, "minecraft:white_concrete")
    bb.fill(x + 1, y + 2, z + 1, x + 8, y + 7, z + 6, AIR)
    bb.fill(x + 1, y + 1, z + 1, x + 8, y + 1, z + 6, "minecraft:spruce_planks")
    bb.fill(x, y + 4, z, x + 9, y + 4, z, "minecraft:black_concrete")
    bb.fill(x, y + 4, z + 7, x + 9, y + 4, z + 7, "minecraft:black_concrete")
    bb.set(x + 4, y + 2, z + 7, "minecraft:iron_door[facing=south,half=lower,hinge=left,open=false]")
    bb.set(x + 4, y + 3, z + 7, "minecraft:iron_door[facing=south,half=upper,hinge=left,open=false]")
    bb.set(x + 4, y + 1, z + 8, "minecraft:polished_blackstone_stairs[facing=north,half=bottom]")
    for (dx, dz) in ((1, 1), (2, 1), (8, 1), (8, 2), (1, 6)):
        bb.set(x + dx, y + 2, z + dz, "minecraft:barrel[facing=up,open=false]")
    bb.set(x + 7, y + 2, z + 5, "minecraft:chest[facing=west]") if False else None
    A.curved_roof(bb, x - 2, z - 2, x + 11, z + 9, y + 9, 4, style="gable", pal=WANO)
    return (x - 3, z - 3, x + 12, z + 10)


def shrine(bb, x, z):
    y = TY
    bb.fill(x - 3, y, z - 3, x + 3, y, z + 3, "minecraft:smooth_stone")
    bb.fill(x - 2, y + 1, z - 2, x + 2, y + 4, z + 1, "minecraft:dark_oak_planks")
    bb.fill(x - 1, y + 1, z + 1, x + 1, y + 3, z + 1, AIR)
    bb.set(x, y + 1, z, "minecraft:candle[candles=3,lit=true]")
    A.curved_roof(bb, x - 4, z - 4, x + 4, z + 3, y + 5, 3, style="gable", pal=WANO)
    # torii in front
    tz = z + 8
    for tx in (x - 3, x + 3):
        bb.fill(tx, y + 1, tz, tx, y + 6, tz, "minecraft:red_concrete")
    bb.fill(x - 4, y + 5, tz, x + 4, y + 5, tz, "minecraft:red_concrete")
    bb.fill(x - 5, y + 7, tz, x + 5, y + 7, tz, "minecraft:black_concrete")
    bb.set(x, y + 6, tz, "minecraft:red_concrete")
    return (x - 6, z - 5, x + 6, tz + 2)


def koi_pond(bb):
    cx, cz = POND
    mask = lambda X, Z: (((X - cx) / 12.0) ** 2 + ((Z - cz) / 7.5) ** 2 + 0.25 * NT.noise(X, Z, 8440, 4)) <= 1
    bb.fill_where(cx - 14, TY - 3, cz - 10, cx + 14, TY, cz + 10, lambda X, Y, Z: mask(X, Z) & (Y == TY - 3), "minecraft:clay")
    bb.fill_where(cx - 14, TY - 2, cz - 10, cx + 14, TY, cz + 10, lambda X, Y, Z: mask(X, Z), "minecraft:water")
    for (dx, dz) in ((-6, -2), (5, 3), (-2, 4), (8, -3)):
        bb.set(cx + dx, TY + 1, cz + dz, "minecraft:lily_pad")
    for (dx, dz) in ((-9, -4), (10, 5), (-11, 3)):
        NT.boulder(bb, cx + dx, TY, cz + dz, 1.4, np.random.default_rng(abs(dx * 7 + dz) + 1), blocks=("minecraft:mossy_cobblestone", "minecraft:andesite", "minecraft:stone"))
    # red arched bridge across the middle (north-south)
    for i in range(-8, 9):
        y = TY + 1 + int(round(2.2 * math.cos(i / 8 * math.pi / 2)))
        bb.fill(cx - 1, y, cz + i, cx + 1, y, cz + i, "minecraft:mangrove_slab[type=top]")
        for x in (cx - 2, cx + 2):
            bb.set(x, y + 1, cz + i, "minecraft:mangrove_fence" if i % 2 else "minecraft:red_concrete")
    for (dx, dz) in ((-15, -6), (15, 6), (-14, 7)):
        A.stone_lantern(bb, cx + dx, TY + 1, cz + dz)
    return (cx - 16, cz - 11, cx + 16, cz + 11)


def training_yard(bb, rng):
    x1, z1, x2, z2 = YARD
    # slashed straw posts: hay on a fence, some cut in half (the top lying beside it)
    for x in range(x1 + 2, x2 - 1, 4):
        for z in range(z1 + 3, z1 + 14, 5):
            bb.set(x, TY + 1, z, "minecraft:dark_oak_fence")
            if rng.random() < 0.5:
                bb.fill(x, TY + 2, z, x, TY + 3, z, "minecraft:hay_block[axis=y]")
            else:
                bb.set(x, TY + 2, z, "minecraft:hay_block[axis=y]")
                set_if_air(bb, x + 1, TY + 1, z, "minecraft:hay_block[axis=x]")
    # sliced bamboo canes
    for x in range(x1 + 2, x2 - 1, 3):
        bb.fill(x, TY + 1, z2 - 6, x, TY + int(rng.integers(1, 4)), z2 - 6, "minecraft:bamboo_block[axis=y]")
    # the rack of Punisher scythe blades: curved iron blades on a dark oak frame
    rx = x2 - 2
    bb.fill(rx, TY + 1, z2 - 4, rx, TY + 5, z2 - 4, "minecraft:dark_oak_fence")
    bb.fill(rx, TY + 1, z2 - 1, rx, TY + 5, z2 - 1, "minecraft:dark_oak_fence")
    bb.fill(rx, TY + 5, z2 - 4, rx, TY + 5, z2 - 1, "minecraft:dark_oak_planks")
    for i, z in enumerate((z2 - 3, z2 - 2)):
        for k in range(4):
            bb.set(rx - 1 - (k // 2), TY + 4 - k, z, "minecraft:iron_block" if k < 3 else "minecraft:iron_bars")
    # targets cut to ribbons
    for z in (z1 + 18, z1 + 22):
        bb.set(x1 + 1, TY + 1, z, "minecraft:dark_oak_fence")
        bb.set(x1 + 1, TY + 2, z, "minecraft:target")
        set_if_air(bb, x1 + 2, TY + 1, z, "minecraft:white_carpet")
    bb.set(x1 + 6, TY + 1, z2 - 2, "minecraft:grindstone[face=floor,facing=north]")
    bb.set(x1 + 8, TY + 1, z2 - 2, "minecraft:water_cauldron[level=3]")


def bamboo_grove(bb, rng, taken):
    """Dense dark bamboo with pines in it, outside the estate."""
    k = 0
    X = np.arange(N)
    for x in range(4, N - 4):
        for z in range(4, N - 4):
            if not land(np.array([x]), np.array([z]))[0] or sh(np.array([x]), np.array([z]))[0] < 9:
                continue
            if EST[0] - 3 <= x <= EST[2] + 3 and EST[1] - 3 <= z <= EST[3] + 3:
                continue
            if path(np.array([x]), np.array([z]))[0] or abs(x - GATE_X) < 4 and z > EST[3]:
                continue
            dens = NT.noise(np.array([x]), np.array([z]), 8450, 9)[0]
            if dens > 0.38 and rng.random() < 0.4 * dens:
                y = hy(x, z) + 1
                h = int(rng.integers(8, 17))
                bb.fill(x, y, z, x, y + h, z, "minecraft:bamboo[age=1,leaves=none,stage=0]")
                bb.set(x, y + h + 1, z, "minecraft:bamboo[age=1,leaves=large,stage=0]")
                bb.set(x, y + h, z, "minecraft:bamboo[age=1,leaves=small,stage=0]")
                k += 1
    # dark pines
    p = 0
    for _ in range(600):
        x, z = int(rng.integers(8, N - 8)), int(rng.integers(8, N - 8))
        Xa, Za = np.array([x]), np.array([z])
        if not land(Xa, Za)[0] or sh(Xa, Za)[0] < 12:
            continue
        if EST[0] - 6 <= x <= EST[2] + 6 and EST[1] - 6 <= z <= EST[3] + 6:
            continue
        y = hy(x, z) + 1
        h = int(rng.integers(10, 17))
        bb.fill(x, y, z, x, y + h, z, "minecraft:dark_oak_log[axis=y]")
        for i in range(4):
            ly = y + h - 6 + i * 2
            r = 3.4 - i * 0.7
            bb.fill_where(x - 4, ly, z - 4, x + 4, ly, z + 4, lambda X_, Y, Z_, r=r: np.hypot(X_ - x, Z_ - z) <= r,
                          "minecraft:spruce_leaves[persistent=true]", only_empty=True)
        bb.set(x, y + h + 1, z, "minecraft:spruce_leaves[persistent=true]")
        p += 1
        if p >= 30:
            break
    print("bamboo:", k, "pines:", p)


def design():
    bb = BigBuild(seed=8410, y_min=-14, y_max=60)
    tracker = P.PropTracker(8410)
    audit = []
    rng = np.random.default_rng(8410)
    terrain(bb)
    estate_wall(bb)
    taken = [main_house(bb, tracker, audit)]
    taken.append(kura(bb, EST[0] + 4, EST[1] + 4))
    taken.append(shrine(bb, EST[2] - 10, EST[1] + 8))
    taken.append(koi_pond(bb))
    training_yard(bb, rng)
    for (x, z) in ((GATE_X - 5, EST[3] - 8), (GATE_X + 5, EST[3] - 8), (HOUSE[0] - 6, HOUSE[3] + 10), (HOUSE[2] + 6, HOUSE[3] + 10)):
        A.stone_lantern(bb, x, TY + 1, z)
    # a couple of maples and a pine inside the walls
    for (x, z) in ((EST[0] + 6, EST[3] - 8), (EST[2] - 22, EST[3] - 6), (EST[0] + 18, EST[1] + 22)):
        y = TY + 1
        bb.fill(x, y, z, x, y + 5, z, "minecraft:dark_oak_log[axis=y]")
        bb.fill_where(x - 4, y + 4, z - 4, x + 4, y + 8, z + 4, lambda X, Y, Z: (X - x) ** 2 + ((Y - (y + 6)) * 1.6) ** 2 + (Z - z) ** 2 <= 12,
                      "minecraft:mangrove_leaves[persistent=true]" if x % 2 else "minecraft:cherry_leaves[persistent=true]", only_empty=True)
    bamboo_grove(bb, rng, taken)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 8490, density=0.3, kinds=["minecraft:fern", "minecraft:large_fern", "minecraft:short_grass"],
              flowers=["minecraft:lily_of_the_valley", "minecraft:white_tulip"],
              mask=lambda X, Z: land(X, Z) & (sh(X, Z) >= 8) & ~raked(X, Z) & ~path(X, Z))
    return bb, audit


def steady(b):
    import render
    for (x, y, z), s in list(b.blocks.items()):
        n = s.split("[")[0]
        if n.endswith(("gravel", "sand", "concrete_powder")) and "sandstone" not in n:
            below = b.blocks.get((x, y - 1, z))
            if below is None or render.shape_of(below) != "full":
                b.blocks[(x, y, z)] = "minecraft:coarse_dirt" if "gravel" in n else "minecraft:smooth_sandstone" if "sand" in n else \
                    n.replace("concrete_powder", "concrete")


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    steady(b)
    b.chest(EST[0] + 11, TY + 2, EST[1] + 6, "wano", "south")
    b.chest(HOUSE[0] + 2, TY + 2, HOUSE[1] + 2, "medium", "south")
    b.npc((YARD[0] + YARD[2]) // 2, TY + 1, YARD[1] + 16, "killer", True)
    b.guards("gifter", ((GATE_X - 4, EST[3] + 6), (GATE_X + 4, EST[3] + 6), (EST[0] + 10, HOUSE[3] + 12), (EST[2] - 10, HOUSE[3] + 2)), y=TY + 1)
    return b, 0
