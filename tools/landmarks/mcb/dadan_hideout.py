"""Dadan's Hideout v2 on Mt. Colubo (Dawn Island), redesigned with the Minecraft Builder skill.

A wild forested island whose ground climbs to Mt. Colubo in the north and falls away to rocky beaches. On a level
shelf in the forest the mountain bandits' big log lodge: a stone footing, two storeys of stacked spruce logs, a
porch with the hunting trophies, a steep plank roof with two stone chimneys; inside, the dining hall with the long
table and hearth, the kitchen, the bunk rooms, Dadan's room and the boys' corner room upstairs. Round it the
smokehouse, the woodpile and chopping block, a well, a lookout platform on stilts. A stream comes down the mountain
past the lodge to a pool and the sea. Up the slope, in a giant tree, the treehouse Ace, Sabo and Luffy built:
platforms, a little cabin, rope ladders and the pirate flag; and below it the stump with the three sake cups where
they swore to be brothers. 160 x 160. y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, furnish, set_if_air, place_house, lamp_post, wing_floor
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "dadan_hideout"
TITLE = "Dadan's Hideout"
CUTS = [10, 16]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 160
SHORE = NT.outline(80, 82, 72, 2620, wobble=0.1)
LY = 10                                     # the lodge shelf
LODGE = (52, 78, 92, 102)
YARD = (40, 70, 112, 118)
PEAK = (76, 24)
TREE = (104, 52)                            # the treehouse tree
STUMP = (98, 64)

FOREST = [("minecraft:grass_block", 0.38), ("minecraft:podzol", 0.2), ("minecraft:moss_block", 0.1), ("minecraft:coarse_dirt", 0.1),
          ("minecraft:rooted_dirt", 0.08), ("minecraft:dirt", 0.06), ("minecraft:mossy_cobblestone", 0.04), ("minecraft:mud", 0.04)]
ROCK = [("minecraft:stone", 0.4), ("minecraft:andesite", 0.2), ("minecraft:tuff", 0.1), ("minecraft:cobblestone", 0.15),
        ("minecraft:mossy_cobblestone", 0.15)]
SAND = [("minecraft:sand", 0.5), ("minecraft:stone", 0.2), ("minecraft:clay", 0.15), ("minecraft:sandstone", 0.15)]
YARD_G = [("minecraft:coarse_dirt", 0.3), ("minecraft:dirt_path", 0.25), ("minecraft:packed_mud", 0.15), ("minecraft:grass_block", 0.2),
          ("minecraft:rooted_dirt", 0.1)]


def rect_d(X, Z, r):
    dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0)
    dz = np.maximum(np.maximum(r[1] - Z, Z - r[3]), 0)
    return np.hypot(dx, dz)


def stream_x(Z):
    Z = np.asarray(Z, float)
    return 40 + 6 * np.sin(Z * 0.06) + (Z - 30) * 0.05


def stream(X, Z):
    return (np.abs(np.asarray(X) - stream_x(Z)) <= 1.6) & (np.asarray(Z) > 30)


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = SHORE(X, Z)
    h = 6 + NT.fbm(X, Z, 2622, 22) * 12 - 3
    h = h + 30 * np.exp(-((X - PEAK[0]) ** 2 + (Z - PEAK[1]) ** 2) / (2 * 22.0 ** 2))
    h = h + 10 * np.exp(-((X - TREE[0]) ** 2 + (Z - TREE[1]) ** 2) / (2 * 14.0 ** 2))
    h = h * np.clip((d - 1.5) / 12.0, 0, 1)
    y = rect_d(X, Z, YARD)
    h = np.where(y <= 0, LY, np.where(y < 12, LY * (1 - y / 12) + h * (y / 12), h))
    sd = np.abs(X - stream_x(Z))
    h = np.where((sd < 5) & (Z > 30), h - np.clip(5 - sd, 0, 3), h)
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
    return SHORE(X, Z) > 1.5


def hy(x, z):
    return int(HMAP[min(max(x, 0), N - 1), min(max(z, 0), N - 1)])


def terrain(bb):
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SAND, 2631, mask=lambda X, Z: land(X, Z) & (height(X, Z) <= 1) & ~steep(X, Z),
             under="minecraft:stone", core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, ROCK, 2632, mask=lambda X, Z: land(X, Z) & (steep(X, Z) | (height(X, Z) > 30)),
             under="minecraft:stone", core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, FOREST, 2633,
             mask=lambda X, Z: land(X, Z) & (height(X, Z) > 1) & ~steep(X, Z) & (height(X, Z) <= 30), core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, YARD_G, 2634, mask=lambda X, Z: land(X, Z) & (rect_d(X, Z, YARD) <= 0), core="minecraft:stone")
    bed = lambda X, Z: np.round(-2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10))
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy == bed(X, Z)), "minecraft:sand")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy < bed(X, Z)) & (yy >= bed(X, Z) - 2), "minecraft:stone")


def creek(bb):
    """The stream: a one-deep channel of water stepping down the slope over little stone weirs, to the sea."""
    for z in range(31, N - 2):
        cx = float(stream_x(z))
        for x in range(int(cx - 2), int(cx + 3)):
            X, Z = np.array([[x]]), np.array([[z]])
            if not stream(X, Z)[0, 0] or not land(X, Z)[0, 0]:
                continue
            y = hy(x, z)
            bb.set(x, y, z, "minecraft:water")
            bb.set(x, y - 1, z, "minecraft:gravel" if False else "minecraft:mossy_cobblestone")
            bb.fill(x, y + 1, z, x, y + 3, z, AIR)
    # banks: stones and reeds
    for z in range(32, N - 4, 3):
        cx = int(stream_x(z))
        for x in (cx - 3, cx + 3):
            if land(np.array([[x]]), np.array([[z]]))[0, 0]:
                set_if_air(bb, x, hy(x, z) + 1, z, "minecraft:mossy_cobblestone" if z % 2 else "minecraft:fern")


def lodge(bb, tracker, audit):
    """The bandits' log lodge: stone footing, two storeys of logs, a long porch, a steep plank roof, two chimneys."""
    x1, z1, x2, z2 = LODGE
    y0 = LY
    FH = 6
    bb.fill(x1 - 1, y0 - 3, z1 - 1, x2 + 1, y0, z2 + 1, "minecraft:cobblestone")
    bb.fill(x1, y0, z1, x2, y0, z2, "minecraft:spruce_planks")
    for f in range(2):
        a = y0 + f * FH
        for y in range(a + 1, a + FH + 1):
            for x in range(x1, x2 + 1):
                bb.set(x, y, z1, "minecraft:spruce_log[axis=x]" if (y % 2) else "minecraft:stripped_spruce_log[axis=x]")
                bb.set(x, y, z2, "minecraft:spruce_log[axis=x]" if (y % 2) else "minecraft:stripped_spruce_log[axis=x]")
            for z in range(z1, z2 + 1):
                bb.set(x1, y, z, "minecraft:spruce_log[axis=z]" if (y % 2) else "minecraft:stripped_spruce_log[axis=z]")
                bb.set(x2, y, z, "minecraft:spruce_log[axis=z]" if (y % 2) else "minecraft:stripped_spruce_log[axis=z]")
        bb.fill(x1 + 1, a + 1, z1 + 1, x2 - 1, a + FH, z2 - 1, AIR)
        if f:
            bb.fill(x1 + 1, a, z1 + 1, x2 - 1, a, z2 - 1, "minecraft:spruce_planks")
        # corner posts sticking out like a log cabin's notched ends
        for (x, z) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
            bb.fill(x, a + 1, z, x, a + FH, z, "minecraft:spruce_wood")
        # windows with shutters
        for x in range(x1 + 3, x2 - 1, 5):
            for z, f_ in ((z1, "north"), (z2, "south")):
                bb.fill(x, a + 2, z, x + 1, a + 3, z, "minecraft:glass_pane")
                bb.set(x - 1, a + 2, z + (1 if f_ == "south" else -1), f"minecraft:spruce_trapdoor[facing={f_},half=bottom,open=true]") if False else None
        for z in range(z1 + 3, z2 - 1, 5):
            bb.fill(x1, a + 2, z, x1, a + 3, z + 1, "minecraft:glass_pane")
            bb.fill(x2, a + 2, z, x2, a + 3, z + 1, "minecraft:glass_pane")
    cx = (x1 + x2) // 2
    # interior: ground floor = dining hall (middle) + kitchen + store; upper floor = bunk rooms, Dadan's room, the boys' room
    hall = (cx - 7, z1 + 1, cx + 7, z2 - 1)
    wing_floor(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, y0 + 1, FH - 1, "minecraft:spruce_planks", 2641, tracker,
               ["kitchen", "storage", "kitchen", "storage"], corridor="z", cw=3, keep=[hall, (x1 + 1, z1 + 1, x1 + 3, z1 + 3)],
               wood="spruce", audit=audit)
    for x in (hall[0] - 1, hall[2] + 1):
        bb.fill(x, y0 + 1, z1 + 1, x, y0 + FH, z2 - 1, "minecraft:stripped_spruce_log[axis=y]")
        bb.fill(x, y0 + 1, (z1 + z2) // 2 - 1, x, y0 + 2, (z1 + z2) // 2, AIR)
    # the long table, stools, the hearth on the back wall, antlers and a bear skin
    bb.fill(cx - 5, y0 + 1, (z1 + z2) // 2, cx + 5, y0 + 1, (z1 + z2) // 2, "onepiece:dark_oak_table")
    for x in range(cx - 5, cx + 6):
        bb.set(x, y0 + 1, (z1 + z2) // 2 - 1, "onepiece:bar_stool"); bb.set(x, y0 + 1, (z1 + z2) // 2 + 1, "onepiece:bar_stool")
        if x % 3 == 0:
            bb.set(x, y0 + 2, (z1 + z2) // 2, ("minecraft:cake[bites=2]", "minecraft:candle[candles=2,lit=true]", "minecraft:flower_pot")[x % 3])
    bb.fill(cx - 2, y0 + 1, z1 + 1, cx + 2, y0 + 3, z1 + 1, "minecraft:cobblestone")
    bb.set(cx, y0 + 1, z1 + 1, "minecraft:campfire[lit=true,signal_fire=false]")
    bb.set(cx, y0 + 2, z1 + 1, "minecraft:cobblestone")
    bb.fill(cx - 3, y0 + 1, z2 - 3, cx + 3, y0 + 1, z2 - 2, "minecraft:brown_carpet")
    for x in (cx - 4, cx + 4):
        bb.set(x, y0 + 4, z1 + 1, "minecraft:lantern[hanging=false]") if False else bb.set(x, y0 + FH - 1, (z1 + z2) // 2, "minecraft:lantern[hanging=true]")
    bb.fill(cx - 1, y0 + 1, z2, cx + 1, y0 + 3, z2, AIR)
    bb.set(cx, y0 + 1, z2, "minecraft:spruce_door[facing=south,half=lower,hinge=left,open=false]")
    bb.set(cx, y0 + 2, z2, "minecraft:spruce_door[facing=south,half=upper,hinge=left,open=false]")
    bb.set(cx - 1, y0 + 1, z2, "minecraft:stripped_spruce_log[axis=y]"); bb.set(cx + 1, y0 + 1, z2, "minecraft:stripped_spruce_log[axis=y]")
    bb.fill(cx - 1, y0 + 2, z2, cx + 1, y0 + 3, z2, "minecraft:stripped_spruce_log[axis=x]")
    bb.set(cx, y0 + 2, z2, "minecraft:spruce_door[facing=south,half=upper,hinge=left,open=false]")
    wing_floor(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, y0 + FH + 1, FH - 1, "minecraft:spruce_planks", 2642, tracker,
               ["bedroom", "bedroom", "bedroom", "storage", "bedroom", "living"], corridor="x", cw=3,
               keep=[(x1 + 1, z1 + 1, x1 + 3, z1 + 3)], wood="spruce", audit=audit)
    bb.fill(x1 + 2, y0 + 1, z1 + 2, x1 + 2, y0 + FH, z1 + 2, "minecraft:ladder[facing=south]")
    # porch along the south front
    bb.fill(x1 - 1, y0, z2 + 1, x2 + 1, y0, z2 + 5, "minecraft:spruce_planks")
    for x in range(x1 - 1, x2 + 2, 4):
        bb.fill(x, y0 + 1, z2 + 5, x, y0 + 4, z2 + 5, "minecraft:spruce_log[axis=y]")
    bb.fill(x1 - 1, y0 + 5, z2 + 1, x2 + 1, y0 + 5, z2 + 5, "minecraft:spruce_slab[type=bottom]")
    for x in range(x1, x2 + 1):
        if abs(x - cx) > 2:
            bb.set(x, y0 + 1, z2 + 5, "minecraft:spruce_fence") if (x - x1) % 4 else None
    for (x, b) in ((x1 + 2, "minecraft:barrel[facing=up,open=false]"), (x1 + 3, "onepiece:keg[facing=south]"),
                   (x2 - 3, "minecraft:barrel[facing=up,open=false]"), (x2 - 6, st("minecraft:spruce_stairs", "south"))):
        bb.set(x, y0 + 1, z2 + 2, b)
    bb.set(cx - 4, y0 + 4, z2 + 1, "minecraft:skeleton_skull[rotation=8]") if False else None
    for x in (cx - 5, cx + 5):
        bb.set(x, y0 + 4, z2 + 1, "minecraft:lantern[hanging=true]") if False else bb.set(x, y0 + 4, z2 + 2, "minecraft:lantern[hanging=true]")
    # steep plank roof and chimneys
    P.gable_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, y0 + 2 * FH + 1, "minecraft:spruce_stairs", gable_fill="minecraft:stripped_spruce_log",
                 overhang=1)
    for x in (x1 + 4, x2 - 4):
        bb.fill(x, y0 + 1, z1 - 2, x + 1, y0 + 2 * FH + 9, z1 - 1, "minecraft:cobblestone")
        bb.set(x, y0 + 2 * FH + 10, z1 - 2, "minecraft:campfire[lit=true,signal_fire=false]")
    bb.set(cx, y0 + 2 * FH + 1, (z1 + z2) // 2, "minecraft:lantern[hanging=true]") if False else None
    return (x1 - 3, z1 - 4, x2 + 3, z2 + 7)


def yard(bb, rng):
    """Smokehouse, woodpile and chopping block, well, a lookout on stilts, a meat-drying rack."""
    y = LY
    # smokehouse
    sx, sz = 98, 84
    bb.fill(sx, y, sz, sx + 6, y, sz + 6, "minecraft:cobblestone")
    bb.fill(sx, y + 1, sz, sx + 6, y + 4, sz + 6, "minecraft:mud_bricks")
    bb.fill(sx + 1, y + 1, sz + 1, sx + 5, y + 4, sz + 5, AIR)
    bb.fill(sx + 3, y + 1, sz + 6, sx + 3, y + 2, sz + 6, AIR)
    P.gable_roof(bb, sx - 1, sz - 1, sx + 7, sz + 7, y + 5, "minecraft:spruce_stairs", gable_fill="minecraft:mud_bricks", overhang=0)
    bb.set(sx + 3, y + 1, sz + 3, "minecraft:campfire[lit=true,signal_fire=false]")
    for x in range(sx + 1, sx + 6, 2):
        bb.set(x, y + 4, sz + 2, "minecraft:chain[axis=y]"); bb.set(x, y + 3, sz + 2, "minecraft:dried_kelp_block")
    # woodpile and chopping block
    for k in range(10):
        bb.fill(44 + k, y + 1, 96, 44 + k, y + 1 + (k % 3 == 0) + 1, 97, "minecraft:spruce_log[axis=z]" if k % 2 else "minecraft:oak_log[axis=z]")
    bb.set(48, y + 1, 100, "minecraft:stripped_oak_log[axis=y]")
    bb.set(48, y + 2, 100, "minecraft:iron_trapdoor[facing=north,half=bottom,open=false]") if False else None
    # well
    wx, wz = 74, 112
    bb.fill(wx - 1, y - 6, wz - 1, wx + 1, y, wz + 1, "minecraft:water")
    for (a, b) in ((wx - 2, wz - 2), (wx + 2, wz - 2), (wx - 2, wz + 2), (wx + 2, wz + 2)):
        bb.set(a, y + 1, b, "minecraft:cobblestone_wall")
    for x in range(wx - 2, wx + 3):
        for z in range(wz - 2, wz + 3):
            if max(abs(x - wx), abs(z - wz)) == 2:
                bb.set(x, y + 1, z, "minecraft:cobblestone")
    for (a, b) in ((wx - 2, wz), (wx + 2, wz)):
        bb.fill(a, y + 2, b, a, y + 4, b, "minecraft:spruce_fence")
    bb.fill(wx - 2, y + 5, wz, wx + 2, y + 5, wz, "minecraft:spruce_slab[type=bottom]")
    bb.set(wx, y + 4, wz, "minecraft:chain[axis=y]")
    # lookout platform on stilts, at the yard edge
    lx, lz = 110, 104
    for (a, b) in ((lx, lz), (lx + 4, lz), (lx, lz + 4), (lx + 4, lz + 4)):
        bb.fill(a, hy(a, b) + 1, b, a, y + 12, b, "minecraft:spruce_log[axis=y]")
    bb.fill(lx, y + 12, lz, lx + 4, y + 12, lz + 4, "minecraft:spruce_planks")
    for k in range(5):
        for (a, b) in ((lx + k, lz), (lx + k, lz + 4), (lx, lz + k), (lx + 4, lz + k)):
            set_if_air(bb, a, y + 13, b, "minecraft:spruce_fence")
    bb.fill(lx + 2, hy(lx + 2, lz - 1) + 1, lz - 1, lx + 2, y + 12, lz - 1, "minecraft:ladder[facing=north]")
    bb.set(lx + 2, y + 13, lz, AIR)
    bb.set(lx + 2, y + 13, lz + 2, "minecraft:bell[attachment=floor,facing=south]")
    # drying rack
    for x in (60, 66):
        bb.fill(x, y + 1, 72, x, y + 3, 72, "minecraft:spruce_fence")
    bb.fill(61, y + 3, 72, 65, y + 3, 72, "minecraft:spruce_fence")
    for x in range(61, 66, 2):
        bb.set(x, y + 2, 72, "minecraft:dried_kelp_block") if False else bb.set(x, y + 2, 72, "minecraft:brown_banner[rotation=0]")
    return [(sx - 2, sz - 2, sx + 8, sz + 8), (42, 94, 56, 102), (wx - 4, wz - 4, wx + 4, wz + 4), (lx - 2, lz - 2, lx + 6, lz + 6),
            (58, 70, 68, 74)]


def big_tree(bb, x, z, h, rng):
    """A giant broadleaf: buttress roots, a 3x3 trunk, big boughs and a wide crown."""
    g = hy(x, z)
    for k in range(8):
        a = k * math.pi / 4
        for t in range(1, 6):
            rx, rz = round(x + t * math.cos(a)), round(z + t * math.sin(a))
            ry = hy(rx, rz) + max(0, 4 - t)
            bb.fill(rx, hy(rx, rz), rz, rx, ry, rz, "minecraft:oak_wood")
    bb.fill_where(x - 3, g, z - 3, x + 3, g + h, z + 3, lambda X, Y, Z: np.hypot(X - x, Z - z) <= 2.2 - (Y - g) / (3.0 * h), "minecraft:oak_log[axis=y]")
    for k in range(6):
        a = k * math.pi / 3 + 0.4
        by = g + h - 6 + (k % 3) * 2
        L = 9
        for t in np.linspace(0, 1, 18):
            px, py, pz = x + L * t * math.cos(a), by + 4 * t, z + L * t * math.sin(a)
            bb.set(round(px), round(py), round(pz), "minecraft:oak_wood")
        cx, cy, cz = x + L * math.cos(a), by + 4, z + L * math.sin(a)
        bb.fill_where(int(cx - 6), int(cy - 3), int(cz - 6), int(cx + 6), int(cy + 4), int(cz + 6),
                      lambda X, Y, Z: (((X - cx) / 5.5) ** 2 + ((Y - cy - 1) / 3.0) ** 2 + ((Z - cz) / 5.5) ** 2 <= 1)
                      & (NT.noise(X + Y, Z, 2681, 2) > 0.15), "minecraft:oak_leaves[distance=7,persistent=true,waterlogged=false]")
    bb.fill_where(x - 8, g + h - 2, z - 8, x + 8, g + h + 6, z + 8,
                  lambda X, Y, Z: ((X - x) / 7.5) ** 2 + ((Y - g - h - 2) / 4.0) ** 2 + ((Z - z) / 7.5) ** 2 <= 1,
                  "minecraft:oak_leaves[distance=7,persistent=true,waterlogged=false]")
    return g


def treehouse(bb, rng):
    """The boys' treehouse: two platforms round the trunk joined by a rope bridge-ladder, a little patched cabin on the
    top one with the flag they made, ladders down to the ground."""
    x, z = TREE
    g = big_tree(bb, x, z, 30, rng)
    for (py, r) in ((g + 12, 5), (g + 20, 4)):
        bb.fill_where(x - r, py, z - r, x + r, py, z + r, lambda X, Y, Z: (np.hypot(X - x, Z - z) <= r + 0.4) & (np.hypot(X - x, Z - z) > 2.3),
                      "minecraft:spruce_planks")
        for k in range(16):
            a = k * math.pi / 8
            set_if_air(bb, round(x + r * math.cos(a)), py + 1, round(z + r * math.sin(a)), "minecraft:spruce_fence")
        for k in range(4):                                         # braces
            a = k * math.pi / 2 + math.pi / 4
            for t in range(1, 4):
                bb.set(round(x + (2 + t * (r - 2) / 3) * math.cos(a)), py - 4 + t, round(z + (2 + t * (r - 2) / 3) * math.sin(a)),
                       "minecraft:spruce_fence")
    # the little cabin on the top platform: boards of all kinds, a tarp roof, a flag with a skull
    cy = g + 21
    for (a, b) in ((x + 2, z - 3), (x + 4, z - 3), (x + 2, z - 1), (x + 4, z - 1)):
        bb.fill(a, cy, b, a, cy + 2, b, "minecraft:spruce_fence")
    bb.fill(x + 2, cy, z - 3, x + 4, cy + 2, z - 3, "minecraft:oak_planks")
    bb.fill(x + 2, cy + 3, z - 4, x + 4, cy + 3, z, "minecraft:spruce_slab[type=bottom]")
    bb.set(x + 3, cy + 3, z - 2, "minecraft:blue_carpet") if False else bb.set(x + 3, cy + 4, z - 2, "minecraft:blue_carpet")
    bb.set(x + 3, cy, z - 2, "minecraft:barrel[facing=up,open=false]")
    bb.fill(x - 2, g + 21, z + 3, x - 2, g + 30, z + 3, "minecraft:spruce_fence")
    bb.fill(x - 1, g + 27, z + 3, x + 2, g + 29, z + 3, "minecraft:black_wool")
    bb.set(x, g + 28, z + 3, "minecraft:white_wool"); bb.set(x + 1, g + 28, z + 3, "minecraft:white_wool")
    # ladders: ground to the first platform, first to the second (on the trunk's south face)
    bb.fill(x, g, z + 3, x, g + 12, z + 3, "minecraft:ladder[facing=south]") if False else None
    for yy in range(g + 1, g + 21):
        bb.set(x, yy, z + 3, "minecraft:ladder[facing=south]") if yy <= g + 12 or yy > g + 12 else None
    bb.fill(x, g + 1, z + 2, x, g + 21, z + 2, "minecraft:oak_log[axis=y]")
    bb.set(x, g + 12, z + 3, "minecraft:ladder[facing=south]"); bb.set(x, g + 20, z + 3, "minecraft:ladder[facing=south]")
    return (x - 10, z - 10, x + 10, z + 10)


def stump(bb):
    """The sake-cup stump in a little clearing: three cups (flower pots) and a jar."""
    x, z = STUMP
    y = hy(x, z)
    bb.fill_where(x - 2, y + 1, z - 2, x + 2, y + 1, z + 2, lambda X, Y, Z: np.hypot(X - x, Z - z) <= 2.2, "minecraft:stripped_oak_wood")
    bb.fill_where(x - 2, y, z - 2, x + 2, y, z + 2, lambda X, Y, Z: np.hypot(X - x, Z - z) <= 2.2, "minecraft:oak_wood")
    for (dx, dz) in ((-1, 0), (1, 0), (0, -1)):
        bb.set(x + dx, y + 2, z + dz, "minecraft:flower_pot")
    bb.set(x, y + 2, z + 1, "minecraft:decorated_pot[cracked=false,facing=north,waterlogged=false]")
    for (dx, dz) in ((-3, -1), (3, 1), (0, 4)):
        bb.set(x + dx, y + 1, z + dz, "minecraft:spruce_log[axis=x]")
    return (x - 5, z - 5, x + 5, z + 5)


def forest(bb, rng, taken):
    k = 0
    for _ in range(8000):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        X, Z = np.array([[x]]), np.array([[z]])
        if not land(X, Z)[0, 0] or SHORE(X, Z)[0, 0] < 4 or GRAD[x, z] >= 3 or stream(X, Z)[0, 0] or HMAP[x, z] > 34:
            continue
        if rect_d(X, Z, YARD)[0, 0] <= 1:
            continue
        if any(t[0] - 1 <= x <= t[2] + 1 and t[1] - 1 <= z <= t[3] + 1 for t in taken):
            continue
        y = hy(x, z)
        if k % 9 == 0 and SHORE(X, Z)[0, 0] > 14:
            big_tree(bb, x, z, int(rng.integers(16, 22)), rng)
            taken.append((x - 9, z - 9, x + 9, z + 9))
        else:
            P.tree(bb, x, y + 1, z, int(rng.integers(7, 13)), ("oak", "spruce", "dark_oak", "birch", "spruce")[k % 5], rng)
            taken.append((x - 3, z - 3, x + 3, z + 3))
        k += 1
        if k >= 150:
            break
    print("trees:", k)


def design():
    bb = BigBuild(seed=2620, y_min=-14, y_max=90)
    tracker = P.PropTracker(2620)
    audit = []
    rng = np.random.default_rng(2620)
    terrain(bb)
    creek(bb)
    taken = [lodge(bb, tracker, audit)]
    taken += yard(bb, rng)
    taken.append(treehouse(bb, rng))
    taken.append(stump(bb))
    taken.append((YARD[0] - 1, YARD[1] - 1, YARD[2] + 1, YARD[3] + 1))
    forest(bb, rng, taken)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 2690, density=0.3,
              kinds=["minecraft:short_grass", "minecraft:fern", "minecraft:large_fern", "minecraft:short_grass", "minecraft:sweet_berry_bush[age=3]"],
              flowers=["minecraft:poppy", "minecraft:dandelion", "minecraft:lily_of_the_valley"],
              mask=lambda X, Z: land(X, Z) & ~stream(X, Z) & (rect_d(X, Z, LODGE) > 4))
    return bb, audit


def steady(b):
    """Sand and gravel with nothing solid under it would fall when the build generates (at sea the world's water
    fills in under it): turn those into blocks that stay put."""
    import render
    for (x, y, z), s in list(b.blocks.items()):
        n = s.split("[")[0]
        if n.endswith(("gravel", "sand", "concrete_powder")) and "sandstone" not in n:
            below = b.blocks.get((x, y - 1, z))
            if below is None or (below is not None and render.shape_of(below) != "full"):
                b.blocks[(x, y, z)] = "minecraft:coarse_dirt" if "gravel" in n else "minecraft:smooth_sandstone" if "sand" in n else \
                    n.replace("concrete_powder", "concrete")


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    steady(b)
    x1, z1, x2, z2 = LODGE
    b.chest(x2 - 2, LY + 7, z1 + 2, "easy", "west")
    b.chest(TREE[0] - 3, hy(*TREE) + 13, TREE[1], "easy", "east")
    b.guards("bandit", (((x1 + x2) // 2 - 4, z2 + 8), ((x1 + x2) // 2 + 4, z2 + 8), (100, 96)), y=LY + 1)
    return b, 0
