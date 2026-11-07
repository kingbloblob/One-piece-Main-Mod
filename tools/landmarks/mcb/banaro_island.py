"""Banaro Island v2, redesigned with the Minecraft Builder skill: the desert-edge island town where Portgas D. Ace
caught up with Blackbeard, and where their Mera Mera against Yami Yami duel left the town in ruins.

A sandy, scrubby island with a grid of plain sandstone-and-stone houses round a market square with a well and a
clock tower. The west quarter has been swallowed by Blackbeard's darkness: a black swirling pit where houses have sunk
to their windows, their walls cut off by the dark. The east quarter burnt in Ace's fire: roofless, charred houses,
ash in the streets, smouldering embers and a glassy fire crater where Dai Enkai: Entei struck. The clock tower's
top was blown away (rubble round its foot). In the north-east the one tavern still standing, where the Blackbeard
Pirates wait under their three-skull flag, wanted posters on the notice board. A pier on the south shore.
~160 x 160. Ground = y 2, sea y 0. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, set_if_air, house_module, place_house, lamp_post, steady
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "banaro_island"
TITLE = "Banaro Island (after Ace vs Blackbeard)"
CUTS = [3, 9, 15]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 160
TY = 2
_ISLE = NT.outline(80, 80, 62, 14010, wobble=0.08)
XS = [36, 58, 80, 102, 124]          # north-south streets
ZS = [38, 60, 82, 104, 126]          # east-west streets
SQ = (69, 71, 91, 93)                 # the market square
DARK = (56, 72, 17)                   # the darkness pit
FIRE = (106, 100, 30)                 # the burnt quarter (centre, radius)
ENTEI = (110, 106, 9)                 # the fire crater
TAV = (106, 44)                       # tavern lot centre
SANDS = [("minecraft:sand", 0.62), ("minecraft:sandstone", 0.1), ("minecraft:clay", 0.12), ("minecraft:gravel", 0.06), ("minecraft:red_sand", 0.1)]
SCRUB = [("minecraft:sand", 0.34), ("minecraft:coarse_dirt", 0.2), ("minecraft:grass_block", 0.16), ("minecraft:red_sand", 0.12),
         ("minecraft:terracotta", 0.08), ("minecraft:rooted_dirt", 0.1)]
PAVE = [("minecraft:smooth_sandstone", 0.35), ("minecraft:sandstone", 0.25), ("minecraft:packed_mud", 0.2), ("minecraft:cut_sandstone", 0.2)]
PAL = dict(walls=["minecraft:smooth_sandstone", "minecraft:sandstone", "minecraft:mud_bricks"], frame="minecraft:stripped_oak_log",
           base=["minecraft:stone_bricks", "minecraft:cobblestone", "minecraft:cracked_stone_bricks"], floor="minecraft:oak_planks", wood="oak",
           chimney="minecraft:bricks", parapet="minecraft:cut_sandstone")
PAL2 = dict(walls=["minecraft:stone_bricks", "minecraft:smooth_sandstone", "minecraft:cracked_stone_bricks"], frame="minecraft:stripped_spruce_log",
            base=["minecraft:cobblestone", "minecraft:stone_bricks", "minecraft:mossy_cobblestone"], floor="minecraft:spruce_planks", wood="spruce",
            chimney="minecraft:bricks", parapet="minecraft:stone_bricks")
ROOFS = ["minecraft:granite_stairs", "minecraft:brick_stairs", "minecraft:mud_brick_stairs", "minecraft:sandstone_stairs"]


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = _ISLE(X, Z)
    dunes = TY + NT.fbm(X, Z, 14011, 16) * 5 - 1.5
    h = np.where(d < 10, TY * np.clip(d / 10.0, 0, 1) + 0.3, dunes)
    town = np.clip(1 - (np.maximum(np.abs(X - 80), np.abs(Z - 82)) - 50) / 8.0, 0, 1)
    h = np.where(d >= 10, h * (1 - town) + TY * town, h)
    return np.where(d < 1.5, -1, np.round(h))


X_, Z_ = np.arange(N)[:, None].astype(float), np.arange(N)[None, :].astype(float)
HMAP, SHORE = _height(X_, Z_).astype(int), _ISLE(X_, Z_)


def height(X, Z):
    return HMAP[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def sh(X, Z):
    return SHORE[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def land(X, Z):
    return sh(X, Z) > 1.5


def hy(x, z):
    return int(HMAP[min(max(int(x), 0), N - 1), min(max(int(z), 0), N - 1)])


def street(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    inside = (X >= XS[0] - 2) & (X <= XS[-1] + 2) & (Z >= ZS[0] - 2) & (Z <= ZS[-1] + 2)
    m = np.zeros(np.broadcast(X, Z).shape, bool)
    for x in XS:
        m |= np.abs(X - x) <= 1.5
    for z in ZS:
        m |= np.abs(Z - z) <= 1.5
    m &= inside
    m |= (X >= SQ[0]) & (X <= SQ[2]) & (Z >= SQ[1]) & (Z <= SQ[3])
    m |= (np.abs(X - 80) <= 1.5) & (Z > ZS[-1]) & (sh(X, Z) > 1.5)
    return m


def dist(X, Z, c):
    return np.hypot(np.asarray(X, float) - c[0], np.asarray(Z, float) - c[1])


def terrain(bb):
    beach = lambda X, Z: land(X, Z) & (sh(X, Z) < 9)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SANDS, 14020, mask=lambda X, Z: beach(X, Z), under="minecraft:sandstone", core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SCRUB, 14021, mask=lambda X, Z: land(X, Z) & ~beach(X, Z) & ~street(X, Z), under="minecraft:sandstone",
             core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, PAVE, 14022, mask=lambda X, Z: land(X, Z) & ~beach(X, Z) & street(X, Z), under="minecraft:sandstone",
             core="minecraft:stone")
    bed = lambda X, Z: np.round(-2 - np.clip(-sh(X, Z) * 0.45, 0, 9))
    sea = lambda X, Z: ~land(X, Z)
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: sea(X, Z) & (yy > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: sea(X, Z) & (yy == bed(X, Z)), "minecraft:sand")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: sea(X, Z) & (yy < bed(X, Z)) & (yy >= bed(X, Z) - 2), "minecraft:stone")


# ------------------------------------------------------------------ the town
def town(bb, tracker, audit, rng):
    """Houses in the street blocks: two rows per block, doors to the street. Returns the list of houses placed."""
    houses = []
    k = 0
    for i in range(len(XS) - 1):
        for j in range(len(ZS) - 1):
            bx1, bx2 = XS[i] + 3, XS[i + 1] - 3
            bz1, bz2 = ZS[j] + 3, ZS[j + 1] - 3
            if bx1 <= SQ[2] and SQ[0] <= bx2 and bz1 <= SQ[3] and SQ[1] <= bz2:
                continue                                                # the square
            if bx1 <= TAV[0] <= bx2 and bz1 <= TAV[1] <= bz2:
                continue                                                # the tavern's block
            for row, rot in ((0, 2), (1, 0)):                           # north row faces north, south row faces south
                x = bx1
                while x < bx2 - 6:
                    w = int(rng.integers(7, 10))
                    if x + w - 1 > bx2:
                        break
                    d = 7
                    z0 = bz1 if row == 0 else bz2 - d + 1
                    corners = (np.array([x, x + w, x, x + w]), np.array([z0, z0, z0 + d, z0 + d]))
                    if not land(*corners).all() or sh(*corners).min() < 10:
                        x += w + 1
                        continue
                    floors = 2 if rng.random() < 0.45 else 1
                    m, top, au = house_module(seed_of("banaro", x, z0), w, d, floors, ROOFS[k % len(ROOFS)], tracker,
                                              [["living", "bedroom"], ["kitchen", "bedroom"], ["storage", "living"]][k % 3][:floors],
                                              pal=PAL if k % 3 else PAL2, fh=4, timber=k % 2 == 0, jetty=False)
                    audit += au
                    place_house(bb, m, w, d, x, hy(x + w // 2, z0 + d // 2), z0, rot)
                    houses.append((x, z0, x + w - 1, z0 + d - 1))
                    x += w + int(rng.integers(1, 3))
                    k += 1
    print("houses:", k)
    return houses


def clock_tower(bb, rng):
    cx, cz = 80, SQ[1] + 5
    s = 4
    y = TY + 1
    bb.fill(cx - s - 1, y - 4, cz - s - 1, cx + s + 1, y - 1, cz + s + 1, "minecraft:stone_bricks")
    H = 30
    bb.fill(cx - s, y, cz - s, cx + s, y + H, cz + s, "minecraft:smooth_sandstone")
    bb.fill_where(cx - s, y, cz - s, cx + s, y + H, cz + s,
                  lambda X, Y, Z: ((np.abs(X - cx) == s) & (np.abs(Z - cz) == s)) | ((Y - y) % 9 == 0), "minecraft:cut_sandstone")
    bb.fill(cx - s + 1, y, cz - s + 1, cx + s - 1, y + H, cz + s - 1, AIR)
    for fy in range(y + 9, y + H, 9):
        bb.fill(cx - s + 1, fy, cz - s + 1, cx + s - 1, fy, cz + s - 1, "minecraft:oak_planks")
        bb.fill(cx - s + 1, fy, cz - s + 1, cx - s + 1, fy, cz - s + 1, AIR)
    bb.fill(cx - s + 1, y, cz - s + 1, cx - s + 1, y + H - 1, cz - s + 1, "minecraft:ladder[facing=south]")
    bb.fill(cx, y, cz + s, cx, y + 2, cz + s, AIR)
    bb.set(cx, y, cz + s, "minecraft:oak_door[facing=south,half=lower,hinge=left]")
    bb.set(cx, y + 1, cz + s, "minecraft:oak_door[facing=south,half=upper,hinge=left]")
    # the clock face on the south side, stopped, with one hand gone
    fy = y + 20
    bb.fill_where(cx - 4, fy - 4, cz + s, cx + 4, fy + 4, cz + s, lambda X, Y, Z: np.hypot(X - cx, Y - fy) <= 3.6, "minecraft:quartz_block")
    bb.fill_where(cx - 4, fy - 4, cz + s, cx + 4, fy + 4, cz + s, lambda X, Y, Z: np.abs(np.hypot(X - cx, Y - fy) - 3.6) < 0.6, "minecraft:gold_block")
    bb.fill(cx, fy, cz + s + 1, cx, fy + 2, cz + s + 1, "minecraft:black_concrete") if False else None
    bb.fill(cx, fy, cz + s, cx, fy + 2, cz + s, "minecraft:black_concrete")
    # the top blown away: a ragged broken edge, rubble below
    bb.fill_where(cx - s - 1, y + 21, cz - s - 1, cx + s + 1, y + H + 2, cz + s + 1,
                  lambda X, Y, Z: (Y > y + 23 + 6 * NT.noise(X * 3, Z * 3, 14030, 2) - 3 * (X - cx) / s), AIR)
    for _ in range(40):
        a, r = rng.uniform(-0.6, 2.4), rng.uniform(s + 2, s + 11)
        x, z = int(cx + r * math.cos(a)), int(cz - 2 + r * math.sin(a) * 0.6)
        b = ["minecraft:cut_sandstone", "minecraft:smooth_sandstone", "minecraft:cobblestone", "minecraft:sandstone_slab[type=bottom]"][int(rng.integers(0, 4))]
        set_if_air(bb, x, hy(x, z) + 1, z, b)
    return (cx - s - 12, cz - s - 6, cx + s + 12, cz + s + 4)


def well(bb, cx, cz):
    y = TY + 1
    bb.fill_where(cx - 3, y - 6, cz - 3, cx + 3, y, cz + 3, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= 2.6, "minecraft:cobblestone")
    bb.fill_where(cx - 3, y - 5, cz - 3, cx + 3, y - 1, cz + 3, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= 1.5, "minecraft:water")
    bb.fill_where(cx - 3, y, cz - 3, cx + 3, y, cz + 3, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= 1.5, AIR)
    for dx in (-2, 2):
        bb.fill(cx + dx, y + 1, cz, cx + dx, y + 3, cz, "minecraft:oak_fence")
    bb.fill(cx - 2, y + 4, cz, cx + 2, y + 4, cz, "minecraft:oak_slab[type=bottom]")
    bb.set(cx, y + 3, cz, "minecraft:iron_chain[axis=y]")
    bb.set(cx, y + 2, cz, "minecraft:cauldron")


def notice_board(bb, cx, cz):
    y = TY + 1
    for dx in (-3, 3):
        bb.fill(cx + dx, y, cz, cx + dx, y + 3, cz, "minecraft:spruce_log[axis=y]")
    bb.fill(cx - 2, y + 1, cz, cx + 2, y + 3, cz, "minecraft:spruce_planks")
    bb.fill(cx - 3, y + 4, cz, cx + 3, y + 4, cz, "minecraft:spruce_slab[type=bottom]")
    for dx in (-2, 0, 2):
        bb.set(cx + dx, y + 2, cz + 1, "onepiece:wall_wanted_poster[facing=south]")
    bb.set(cx - 1, y + 3, cz + 1, "onepiece:wall_wanted_poster[facing=south]")
    bb.set(cx + 1, y + 1, cz + 1, "onepiece:wall_wanted_poster[facing=south]")


def flag_blackbeard(bb, x, y, z, w=13, h=9):
    """Blackbeard's flag (plane z, cloth running +x from the pole): black with three white skulls and crossbones."""
    for i in range(w):
        for j in range(h):
            bb.set(x + i, y - j, z, "minecraft:black_wool")
    for (sx, sy) in ((x + w // 2, y - 2), (x + w // 2 - 3, y - 6), (x + w // 2 + 3, y - 6)):
        for dx in (-1, 0, 1):
            for dy in (0, 1):
                bb.set(sx + dx, sy - dy, z, "minecraft:white_wool")
        bb.set(sx, sy - 2, z, "minecraft:white_wool")
        bb.set(sx - 1, sy, z, "minecraft:black_wool") if False else None
    for k in range(-4, 5):
        bb.set(x + w // 2 + k, y - 4 + (k // 3), z, "minecraft:white_wool") if abs(k) > 1 else None


def tavern(bb, tracker, audit):
    w, d = 15, 11
    x0, z0 = TAV[0] - w // 2, TAV[1] - d // 2
    m, top, au = house_module(seed_of("banaro_tav", x0, z0), w, d, 2, "minecraft:dark_oak_stairs", tracker, ["living", "kitchen", "bedroom", "storage"],
                              pal=dict(walls=["minecraft:stone_bricks", "minecraft:smooth_sandstone", "minecraft:stone_bricks"],
                                       frame="minecraft:stripped_dark_oak_log", base=["minecraft:cobblestone", "minecraft:stone_bricks", "minecraft:cobblestone"],
                                       floor="minecraft:dark_oak_planks", wood="dark_oak", chimney="minecraft:bricks", parapet="minecraft:stone_bricks"),
                              fh=5, timber=True, jetty=True)
    audit += au
    place_house(bb, m, w, d, x0, TY, z0, 0)
    # a terrace with tables in front, the swinging sign, the flag on a pole on the roof
    y = TY + 1
    for (tx, tz) in ((x0 + 3, z0 + d + 3), (x0 + 9, z0 + d + 3)):
        bb.set(tx, y, tz, "minecraft:dark_oak_fence"); bb.set(tx, y + 1, tz, "minecraft:dark_oak_pressure_plate")
        for dx in (-1, 1):
            bb.set(tx + dx, y, tz, "minecraft:dark_oak_stairs[facing=" + ("east" if dx < 0 else "west") + ",half=bottom]")
    bb.fill(x0 + w, y, z0 + d + 1, x0 + w, y + 4, z0 + d + 1, "minecraft:dark_oak_fence")
    bb.set(x0 + w - 1, y + 4, z0 + d + 1, "minecraft:dark_oak_fence")
    bb.set(x0 + w - 1, y + 3, z0 + d + 1, "minecraft:dark_oak_hanging_sign[rotation=0,attached=false]") if False else None
    for (bx, bz) in ((x0 + 1, z0 + d + 1), (x0 + 2, z0 + d + 1), (x0 + 1, z0 + d + 2)):
        bb.set(bx, y, bz, "minecraft:barrel[facing=up]")
    px, pz = x0 + w - 2, z0 + 2
    bb.fill(px, y, pz, px, top + 14, pz, "minecraft:dark_oak_fence")
    flag_blackbeard(bb, px + 1, top + 14, pz)
    return (x0 - 3, z0 - 3, x0 + w + 16, z0 + d + 6)


# ------------------------------------------------------------------ the damage
WOODY = ("planks", "log", "_wood", "fence", "door", "trapdoor", "bookshelf", "barrel", "crafting", "lectern", "loom", "composter", "ladder",
         "wool", "carpet", "_bed", "pane", "glass", "flower_pot", "potted", "lantern", "candle", "banner", "chain", "hay", "onepiece:")
STONY = ("sandstone", "stone_bricks", "mud_bricks", "bricks", "cobblestone", "terracotta", "granite", "stone")


def burn(bb, cx, cz, r, seed):
    """Ace's fire: within r of (cx, cz), timber and cloth burn away (roofs go, windows burst), stone walls char and
    crack, upper storeys collapse. Stronger toward the centre."""
    x1, z1, x2, z2 = cx - r, cz - r, cx + r, cz + r
    y1, y2 = TY - 1, TY + 30
    reg = bb.get_region(x1, y1, z1, x2, y2, z2)
    names = bb.names
    burnt = {}
    for i in np.unique(reg):
        if i < 2:
            continue
        n = names[int(i)]
        s = n.split("[")[0]
        if any(k in s for k in WOODY) or s.endswith(("_stairs", "_slab")) and any(k in s for k in ("oak", "spruce", "birch", "jungle", "acacia", "mangrove")):
            burnt[int(i)] = "wood"
        elif s.endswith(("_stairs", "_slab", "_wall")):
            burnt[int(i)] = "trim"
        elif any(k in s for k in STONY):
            burnt[int(i)] = "stone"
    for (ix, iy, iz) in zip(*np.nonzero(reg > 1)):
        kind = burnt.get(int(reg[ix, iy, iz]))
        if not kind:
            continue
        x, y, z = x1 + int(ix), y1 + int(iy), z1 + int(iz)
        dd = math.hypot(x - cx, z - cz)
        heat = 1 - dd / r + 0.35 * (NT.noise(np.array([x]), np.array([z]), seed, 7)[0] - 0.5)
        if heat <= 0.05:
            continue
        nz = NT.noise(np.array([x * 3 + y]), np.array([z * 3 - y]), seed + 1, 2)[0]
        up = y - TY
        if kind == "wood":
            if nz < 0.25 + heat * 0.6 or up > 5:
                bb.set(x, y, z, AIR)
            elif "planks" in names[int(reg[ix, iy, iz])] or "log" in names[int(reg[ix, iy, iz])]:
                bb.set(x, y, z, "minecraft:stripped_dark_oak_log[axis=y]" if "log" in names[int(reg[ix, iy, iz])] else "minecraft:dark_oak_planks")
        elif kind == "trim":
            if up > 5 and nz < 0.9 * heat + 0.2:
                bb.set(x, y, z, AIR)
        else:
            if up > 4 and nz < 0.5 * heat + (up - 4) * 0.12:
                bb.set(x, y, z, AIR)                                   # upper storeys fallen in
            elif nz < 0.3 + heat * 0.5:
                bb.set(x, y, z, "onepiece:scorched_stone" if nz < 0.22 + heat * 0.3 else "minecraft:blackstone")
    # ash on the ground and smouldering embers
    top = bb.get_region(x1, TY - 2, z1, x2, TY + 3, z2)
    for (ix, iz) in zip(*np.nonzero(np.ones((x2 - x1 + 1, z2 - z1 + 1), bool))):
        x, z = x1 + int(ix), z1 + int(iz)
        if math.hypot(x - cx, z - cz) > r * (0.8 + 0.25 * NT.noise(np.array([x]), np.array([z]), seed + 2, 6)[0]):
            continue
        col = top[ix, :, iz]
        for k in range(len(col) - 2, -1, -1):
            if col[k] > 1:
                if col[k + 1] in (0, 1) and k + 1 < len(col):
                    gy = TY - 2 + k
                    nm = bb.names[int(col[k])].split("[")[0]
                    if nm.endswith(("sand", "dirt", "grass_block", "sandstone", "packed_mud", "terracotta", "gravel")):
                        v = NT.noise(np.array([x]), np.array([z]), seed + 3, 3)[0]
                        if v > 0.55:
                            bb.set(x, gy, z, "onepiece:scorched_stone")
                        elif v > 0.35:
                            bb.set(x, gy, z, "minecraft:coarse_dirt")
                        if NT.noise(np.array([x * 2]), np.array([z * 2]), seed + 4, 2)[0] > 0.86:
                            bb.set(x, gy + 1, z, "minecraft:campfire[lit=true,signal_fire=false,facing=north]")
                break


def fire_crater(bb, cx, cz, r):
    y = TY
    bowl = lambda X, Z: np.round(y - 7 * np.clip(1 - (np.hypot(X - cx, Z - cz) / r) ** 2, 0, 1))
    bb.fill_where(cx - r - 3, y - 9, cz - r - 3, cx + r + 3, y + 12, cz + r + 3, lambda X, Y, Z: (np.hypot(X - cx, Z - cz) <= r) & (Y > bowl(X, Z)), AIR)
    bb.fill_where(cx - r - 3, y - 9, cz - r - 3, cx + r + 3, y, cz + r + 3,
                  lambda X, Y, Z: (np.hypot(X - cx, Z - cz) <= r) & (Y <= bowl(X, Z)) & (Y >= bowl(X, Z) - 1), "minecraft:obsidian")
    bb.fill_where(cx - r - 3, y - 9, cz - r - 3, cx + r + 3, y, cz + r + 3,
                  lambda X, Y, Z: (np.hypot(X - cx, Z - cz) <= r) & (Y == bowl(X, Z)) & (NT.noise(X * 2, Z * 2, 14040, 3) > 0.5), "minecraft:tinted_glass")
    bb.fill_where(cx - r - 3, y - 9, cz - r - 3, cx + r + 3, y, cz + r + 3,
                  lambda X, Y, Z: (np.hypot(X - cx, Z - cz) <= r * 0.45) & (Y == bowl(X, Z)), "minecraft:magma_block")
    bb.fill_where(cx - r - 3, y - 1, cz - r - 3, cx + r + 3, y + 1, cz + r + 3,
                  lambda X, Y, Z: (np.abs(np.hypot(X - cx, Z - cz) - r - 1) < 1.3) & (Y <= y + (NT.noise(X * 3, Z * 3, 14041, 2) > 0.6)),
                  "minecraft:blackstone")


def darkness(bb, cx, cz, r):
    """Blackbeard's Black Hole: a swirling pit of darkness the houses have sunk into. Everything above the bowl inside r
    is gone; the darkness (black concrete, blackstone, obsidian in a spiral) laps over what is left."""
    y = TY
    bowl = lambda X, Z: np.round(y - 9 * np.clip(1 - (np.hypot(X - cx, Z - cz) / r) ** 1.6, 0, 1))
    edge = lambda X, Z: r * (1 + 0.12 * (NT.noise(X, Z, 14050, 5) - 0.5))
    inside = lambda X, Z: np.hypot(X - cx, Z - cz) <= edge(X, Z)
    # the houses that sank: keep only their lower part, cut off by a tilted plane toward the centre
    bb.fill_where(cx - r - 3, y + 1, cz - r - 3, cx + r + 3, y + 30, cz + r + 3,
                  lambda X, Y, Z: inside(X, Z) & (Y > bowl(X, Z) + 3 + 3 * (np.hypot(X - cx, Z - cz) / r)), AIR)
    bb.fill_where(cx - r - 3, y - 12, cz - r - 3, cx + r + 3, y + 3, cz + r + 3,
                  lambda X, Y, Z: inside(X, Z) & (Y > bowl(X, Z)) & (np.hypot(X - cx, Z - cz) < r * 0.55), AIR)
    swirl = lambda X, Z: (np.arctan2(Z - cz, X - cx) * 2 + np.hypot(X - cx, Z - cz) * 0.45) % (2 * math.pi)
    for blk, lo, hi in (("minecraft:black_concrete", 0, 2.6), ("minecraft:blackstone", 2.6, 4.2), ("minecraft:obsidian", 4.2, 5.2),
                        ("minecraft:black_concrete", 5.2, 7)):
        bb.fill_where(cx - r - 3, y - 12, cz - r - 3, cx + r + 3, y + 3, cz + r + 3,
                      lambda X, Y, Z, lo=lo, hi=hi: inside(X, Z) & (Y <= bowl(X, Z)) & (Y >= bowl(X, Z) - 2) & (swirl(X, Z) >= lo) & (swirl(X, Z) < hi), blk)
    # the darkness lapping over the sunk walls: a black skin one block thick on the lowest rows
    bb.fill_where(cx - r - 3, y - 12, cz - r - 3, cx + r + 3, y + 4, cz + r + 3,
                  lambda X, Y, Z: inside(X, Z) & (np.hypot(X - cx, Z - cz) >= r * 0.55) & (Y > bowl(X, Z)) & (Y <= bowl(X, Z) + 1),
                  "minecraft:black_concrete")
    bb.fill_where(cx - 2, y - 14, cz - 2, cx + 2, y - 8, cz + 2, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= 1.6, "minecraft:black_concrete")


def pier(bb):
    z_sea = next(z for z in range(ZS[-1], N) if not land(np.array([80]), np.array([z]))[0])
    z_end = min(N - 14, z_sea + 16)
    bb.fill(78, 0, z_sea - 4, 82, 0, z_end, "minecraft:spruce_planks")
    for z in range(z_sea - 2, z_end + 1, 4):
        for x in (78, 82):
            bb.fill(x, -8, z, x, -1, z, "minecraft:stripped_spruce_log[axis=y]")
            bb.set(x, 1, z, "minecraft:spruce_fence")
    bb.fill(77, 1, z_end, 83, 1, z_end, "minecraft:spruce_fence")
    # an overturned boat and crates on the pier
    bb.fill(84, 0, z_sea + 4, 87, 0, z_sea + 10, "minecraft:spruce_planks") if False else None
    for (x, z) in ((79, z_sea + 3), (81, z_sea + 6), (79, z_sea + 7)):
        bb.set(x, 1, z, "minecraft:barrel[facing=up]")


def design():
    bb = BigBuild(seed=14010, y_min=-16, y_max=60)
    tracker = P.PropTracker(14010)
    audit = []
    rng = np.random.default_rng(14010)
    terrain(bb)
    houses = town(bb, tracker, audit, rng)
    taken = list(houses)
    taken.append(clock_tower(bb, rng))
    well(bb, 86, SQ[3] - 6)
    notice_board(bb, 74, SQ[3] - 4)
    taken.append(tavern(bb, tracker, audit))
    # market stalls left standing in the square, a few overturned
    for k, (x, z) in enumerate(((SQ[0] + 3, SQ[1] + 14), (SQ[2] - 3, SQ[1] + 13), (SQ[0] + 4, SQ[3] - 2))):
        y = TY + 1
        bb.fill(x - 1, y, z, x + 1, y, z, "minecraft:spruce_planks")
        for dx in (-1, 1):
            bb.fill(x + dx, y + 1, z + 1, x + dx, y + 2, z + 1, "minecraft:spruce_fence")
        if k != 1:
            bb.fill(x - 1, y + 3, z, x + 1, y + 3, z + 1, ("minecraft:orange_wool", "minecraft:red_wool", "minecraft:yellow_wool")[k])
        bb.set(x, y + 1, z, "minecraft:melon" if k else "minecraft:pumpkin")
    burn(bb, FIRE[0], FIRE[1], FIRE[2], 14060)
    fire_crater(bb, *ENTEI)
    darkness(bb, *DARK)
    pier(bb)
    # lamp posts along the main streets (outside the damage)
    for x in XS:
        for z in range(ZS[0], ZS[-1] + 1, 11):
            px, pz = x + 2, z + 4
            if dist(px, pz, DARK) < DARK[2] + 3 or dist(px, pz, FIRE) < FIRE[2] * 0.8:
                continue
            if (bb.get_region(px, TY + 1, pz, px, TY + 4, pz) <= 1).all() and land(np.array([px]), np.array([pz]))[0]:
                lamp_post(bb, px, hy(px, pz) + 1, pz, post="minecraft:spruce_fence", h=3)
    # palms and scrub on the dunes outside the town
    from mcb.kit import palm
    k = 0
    for _ in range(1500):
        x, z = int(rng.integers(10, N - 10)), int(rng.integers(10, N - 10))
        X, Z = np.array([x]), np.array([z])
        if not land(X, Z)[0] or sh(X, Z)[0] < 6 or street(X, Z)[0] or (XS[0] - 4 <= x <= XS[-1] + 4 and ZS[0] - 4 <= z <= ZS[-1] + 4):
            continue
        palm(bb, x, hy(x, z) + 1, z, int(rng.integers(7, 12)), ((1, 0), (0, 1), (-1, 0), (0, -1))[k % 4])
        k += 1
        if k >= 22:
            break
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 14090, density=0.3,
              kinds=["minecraft:dead_bush", "onepiece:dune_scrub", "minecraft:short_dry_grass", "onepiece:sand_sage", "onepiece:desert_thistle",
                     "minecraft:tall_dry_grass"],
              flowers=["onepiece:desert_bloom", "onepiece:sand_rose"],
              mask=lambda X, Z: land(X, Z) & ~street(X, Z) & (dist(X, Z, FIRE) > FIRE[2]) & (dist(X, Z, DARK) > DARK[2] + 2),
              ground=("sand", "red_sand", "coarse_dirt", "grass_block", "rooted_dirt", "terracotta"))
    return bb, audit


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    steady(b)
    b.chest(TAV[0] + 4, TY + 1, TAV[1] - 3, "pirate", "west")
    b.chest(DARK[0], TY - 8, DARK[1], "medium", "south")
    b.chest(ENTEI[0] + 2, TY - 6, ENTEI[1], "medium", "north")
    b.chest(80 - 3, TY + 1, SQ[1] + 5, "easy", "east")
    b.npc(TAV[0], TY + 1, TAV[1] + 8, "blackbeard", False)
    b.guards("blackbeard_pirate", ((TAV[0] - 6, TAV[1] + 9), (TAV[0] + 7, TAV[1] + 10), (80, SQ[3] - 1), (DARK[0] + DARK[2] + 3, DARK[1])), y=TY + 1)
    return b, 0
