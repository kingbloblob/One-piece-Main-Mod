"""Shakky's Rip-off Bar v2, Grove 13 of the Sabaody Archipelago, redesigned with the Minecraft Builder skill.

A grove of giant Yarukiman mangroves rising from the sea on arching roots, their floor a soft mat of grass, moss and
mud, soap bubbles welling up from the roots. Against the roots of the great tree of Grove 13 (the number painted
big on its trunk) stands Shakky's bar: a two-storey timber house with a deep gable roof and the SHAKKY sign on its
front. Inside, the dim bar room with the long bar (kegs, shelves and bottles behind, stools in front where Rayleigh
sits), tables and a hearth; Shakky's and Rayleigh's rooms upstairs; the rum cellar below. Outside: terrace tables
under the roots with bubble lamps, the coating workshop where ships get their bubble coat (the Thousand Sunny in
the slip, half coated), the boardwalk and the dock on the mangrove channel, and the neighbouring groves 12 and 14.
144 x 144. y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, furnish, set_if_air, house_module, place_house, lamp_post, glyph
from mcb.bridge import to_canvas
from mcb.mangrove import yarukiman as shared_yarukiman
from mcb import nature as NT
from mcb.shipstamp import stamp_ship

SID = "shakky_bar"
TITLE = "Shakky's Rip-off Bar (Grove 13)"
CUTS = [5, 10]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 144
SHORE = NT.outline(72, 70, 62, 2020, wobble=0.1)
GY = 3                                         # grove floor
TREE = (64, 50, 7.0, 44)                       # x, z, trunk radius, height (Grove 13)
OTHERS = [(26, 96, 5.0, 34, 12), (124, 50, 5.5, 36, 14), (96, 24, 4.5, 30, None)]
BAR = (52, 68, 76, 84)                         # x1, z1, x2, z2 (door on the south)
FH = 5
CHAN_X = 104                                   # the channel to the dock (east)

YLOG = "onepiece:yarukiman_log[axis=y]"
YWOOD = "onepiece:yarukiman_wood[axis=y]"
YLEAF = "onepiece:yarukiman_leaves[distance=7,persistent=true,waterlogged=false]"
BUB = "onepiece:bubble_glass"
GROVE = [("minecraft:grass_block", 0.5), ("minecraft:moss_block", 0.16), ("minecraft:podzol", 0.1), ("minecraft:rooted_dirt", 0.07),
         ("minecraft:mud", 0.08), ("minecraft:coarse_dirt", 0.05), ("minecraft:muddy_mangrove_roots", 0.04)]
SHOREMIX = [("minecraft:mud", 0.35), ("minecraft:muddy_mangrove_roots", 0.2), ("minecraft:sand", 0.25), ("minecraft:clay", 0.2)]
BOARD = "minecraft:spruce_planks"


def rect_d(X, Z, r):
    dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0)
    dz = np.maximum(np.maximum(r[1] - Z, Z - r[3]), 0)
    return np.hypot(dx, dz)


def chan(X, Z):
    return (np.abs(X - CHAN_X) <= 11 + 2 * NT.noise(X, Z, 2021, 6)) & (Z > 64)


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = SHORE(X, Z)
    h = GY + NT.fbm(X, Z, 2022, 18) * 1.8
    h = h * np.clip((d - 1.5) / 8.0, 0, 1)
    h = np.where(rect_d(X, Z, (BAR[0] - 6, BAR[1] - 4, BAR[2] + 14, BAR[3] + 14)) <= 3, GY, h)
    h = np.where(chan(X, Z), -2, h)
    h = np.where(d < 1.5, -1, h)
    return np.round(h)


X0 = np.arange(N)[:, None]
Z0 = np.arange(N)[None, :]
HMAP = _height(X0, Z0).astype(int)


def height(X, Z):
    return HMAP[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def land(X, Z):
    return (SHORE(X, Z) > 1.5) & ~chan(X, Z)


def hy(x, z):
    return int(HMAP[min(max(x, 0), N - 1), min(max(z, 0), N - 1)])


def terrain(bb):
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SHOREMIX, 2031, mask=lambda X, Z: land(X, Z) & (height(X, Z) <= 1),
             under="minecraft:mud", core="minecraft:mud")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, GROVE, 2032, mask=lambda X, Z: land(X, Z) & (height(X, Z) > 1), under="minecraft:mud",
             core="minecraft:mud")
    for y in range(-10, 0):
        bb.fill_where(0, y, 0, N - 1, y, N - 1, lambda X, yy, Z: ~land(X, Z) & (yy > -2 - np.clip(-SHORE(X, Z) * 0.7, 0, 8)
                                                                             - 6 * chan(X, Z)), "minecraft:water")
        bb.fill_where(0, y, 0, N - 1, y, N - 1, lambda X, yy, Z: ~land(X, Z) & (yy == np.round(-2 - np.clip(-SHORE(X, Z) * 0.7, 0, 8)
                                                                                                  - 6 * chan(X, Z))), "minecraft:mud")


def mangrove(bb, x, z, r, h, rng, number=None, skip=None):
    """A giant Yarukiman (v3, shared with the other Sabaody builds: mcb/mangrove.py): a lumpy trunk standing on a
    tent of arching prop roots, a broken crown high up, bubbles welling from the roots, the grove number on a board."""
    return shared_yarukiman(bb, x, hy(x, z), z, r, h, rng, number=number, skip=skip)


# ------------------------------------------------------------------ the bar
def bar(bb, tracker, audit, rng):
    x1, z1, x2, z2 = BAR
    y0 = GY
    # cellar: rum barrels and kegs
    bb.fill(x1 + 1, y0 - 6, z1 + 1, x2 - 1, y0 - 1, z2 - 1, "minecraft:stone_bricks")
    bb.fill(x1 + 2, y0 - 5, z1 + 2, x2 - 2, y0 - 1, z2 - 2, AIR)
    bb.fill(x1 + 2, y0 - 6, z1 + 2, x2 - 2, y0 - 6, z2 - 2, "minecraft:spruce_planks")
    for x in range(x1 + 2, x2 - 1):
        for z in (z1 + 2, z2 - 2):
            for yy in (y0 - 5, y0 - 4):
                bb.set(x, yy, z, "minecraft:barrel[facing=" + ("south" if z == z1 + 2 else "north") + ",open=false]")
    for x in range(x1 + 4, x2 - 3, 4):
        bb.set(x, y0 - 5, (z1 + z2) // 2, "onepiece:keg[facing=north]")
        bb.set(x, y0 - 2, (z1 + z2) // 2, "minecraft:lantern[hanging=true]")
    # the house: stone plinth, timber frame with plaster infill, two storeys
    bb.fill(x1 - 1, y0 - 1, z1 - 1, x2 + 1, y0, z2 + 1, "minecraft:cobblestone")
    bb.fill(x1, y0, z1, x2, y0, z2, "minecraft:dark_oak_planks")
    top = y0 + 2 * FH
    bb.mix(x1, y0 + 1, z1, x2, top, z2, ["minecraft:stripped_spruce_wood", "minecraft:spruce_planks"], [0.6, 0.4])
    for y in range(y0 + FH + 1, top):
        bb.fill(x1, y, z1, x2, y, z2, "minecraft:white_terracotta")
    bb.fill(x1 + 1, y0 + 1, z1 + 1, x2 - 1, top, z2 - 1, AIR)
    bb.fill(x1 + 1, y0 + FH, z1 + 1, x2 - 1, y0 + FH, z2 - 1, "minecraft:spruce_planks")
    bb.fill(x1 + 1, top, z1 + 1, x2 - 1, top, z2 - 1, "minecraft:spruce_planks")
    for x in range(x1, x2 + 1, 4):
        for z in (z1, z2):
            bb.fill(x, y0 + 1, z, x, top, z, "minecraft:dark_oak_log[axis=y]")
    for z in range(z1, z2 + 1, 4):
        for x in (x1, x2):
            bb.fill(x, y0 + 1, z, x, top, z, "minecraft:dark_oak_log[axis=y]")
    for y in (y0 + FH, top):
        bb.fill(x1, y, z1, x2, y, z1, "minecraft:dark_oak_log[axis=x]"); bb.fill(x1, y, z2, x2, y, z2, "minecraft:dark_oak_log[axis=x]")
        bb.fill(x1, y, z1, x1, y, z2, "minecraft:dark_oak_log[axis=z]"); bb.fill(x2, y, z1, x2, y, z2, "minecraft:dark_oak_log[axis=z]")
    # framed, shuttered windows
    for k in range(2):
        wy = y0 + FH * k + 2
        for x in range(x1 + 2, x2 - 1, 4):
            for (z, o, f) in ((z1, -1, "north"), (z2, 1, "south")):
                bb.fill(x, wy, z, x + 1, wy + 1, z, "minecraft:glass_pane")
                bb.set(x - 1, wy, z + o, f"minecraft:spruce_trapdoor[facing={f},half=bottom,open=true]") if False else None
                bb.set(x, wy - 1, z + o, st("minecraft:spruce_stairs", "south" if o < 0 else "north", "top"))
                bb.set(x + 1, wy - 1, z + o, st("minecraft:spruce_stairs", "south" if o < 0 else "north", "top"))
        for z in range(z1 + 2, z2 - 1, 4):
            for x in (x1, x2):
                bb.fill(x, wy, z, x, wy + 1, z + 1, "minecraft:glass_pane")
    # the door and the sign
    cx = (x1 + x2) // 2
    bb.fill(cx - 1, y0 + 1, z2, cx, y0 + 2, z2, AIR)
    bb.set(cx - 1, y0 + 1, z2, "minecraft:spruce_door[facing=south,half=lower,hinge=left,open=false]")
    bb.set(cx - 1, y0 + 2, z2, "minecraft:spruce_door[facing=south,half=upper,hinge=left,open=false]")
    bb.set(cx, y0 + 1, z2, "minecraft:spruce_door[facing=south,half=lower,hinge=right,open=false]")
    bb.set(cx, y0 + 2, z2, "minecraft:spruce_door[facing=south,half=upper,hinge=right,open=false]")
    bb.fill(cx - 2, y0 + 3, z2 + 1, cx + 1, y0 + 3, z2 + 2, "minecraft:spruce_slab[type=top]")
    sign = {"S": ["011", "100", "010", "001", "110"], "H": ["101", "101", "111", "101", "101"], "A": ["010", "101", "111", "101", "101"],
            "K": ["101", "110", "100", "110", "101"], "Y": ["101", "101", "010", "010", "010"], "B": ["110", "101", "110", "101", "110"],
            "R": ["110", "101", "110", "101", "101"]}
    word = "SHAKKY"
    sx = cx - (len(word) * 4) // 2
    bb.fill(sx - 1, y0 + FH + 1, z2 + 1, sx + len(word) * 4 - 1, y0 + FH + 7, z2 + 1, "minecraft:dark_oak_planks")
    for i, ch in enumerate(word):
        rows = ["".join("#" if b == "1" else "." for b in r) for r in sign[ch]]
        glyph(bb, rows, sx + i * 4, y0 + FH + 6, z2 + 2, "minecraft:white_concrete")
    word = "BAR"
    for i, ch in enumerate(word):
        rows = ["".join("#" if b == "1" else "." for b in r) for r in sign[ch]]
        glyph(bb, rows, x1 - 1, top + 5, z1 + 5 + i * 4, "minecraft:white_concrete", axis="z") if False else \
            glyph(bb, [r for r in rows], x2 + 1, top - 1, z1 + 4 + i * 4, "minecraft:white_concrete", axis="z")
    # roof
    P.gable_roof(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, top + 1, "minecraft:dark_oak_stairs", ridge_axis="x",
                 gable_fill="minecraft:white_terracotta", overhang=1, ends_overhang=1)
    bb.fill(x2 - 3, top + 1, z1 + 2, x2 - 2, top + 9, z1 + 3, "minecraft:bricks")
    # inside: the long bar along the north wall, shelves behind, stools in front, tables and a hearth
    by = y0 + 1
    for x in range(x1 + 3, x2 - 6):
        bb.set(x, by, z1 + 4, "onepiece:tavern_bar[facing=south]")
        bb.set(x, by, z1 + 6, "onepiece:bar_stool[facing=north]") if (x - x1) % 2 == 1 else None
        bb.set(x, by, z1 + 1, "minecraft:barrel[facing=south,open=false]" if x % 3 else "onepiece:keg[facing=south]")
        bb.set(x, by + 3, z1 + 1, "onepiece:dark_oak_wall_shelf[facing=south]")
    bb.set(x2 - 6, by, z1 + 4, "minecraft:dark_oak_fence_gate[facing=east,open=false]")
    for x in range(x1 + 3, x2 - 6, 2):
        bb.set(x, by + 1, z1 + 1, "minecraft:brewing_stand")
    for (tx, tz) in ((x1 + 4, z2 - 5), (x1 + 10, z2 - 5), (x2 - 5, z2 - 5), (x2 - 4, z1 + 6)):
        bb.set(tx, by, tz, "onepiece:barrel_table[facing=north]")
        bb.set(tx + 1, by, tz, "onepiece:bar_stool[facing=west]")
        bb.set(tx - 1, by, tz, "onepiece:bar_stool[facing=east]")
        bb.set(tx, by + 1, tz, "minecraft:candle[candles=2,lit=true]")
    bb.fill(x1 + 1, by, z2 - 2, x1 + 2, by + 3, z2 - 1, "minecraft:bricks")
    bb.set(x1 + 1, by, (z1 + z2) // 2, "minecraft:campfire[lit=true]") if False else None
    for x in range(x1 + 4, x2 - 2, 6):
        bb.fill(x, top - FH - 2, (z1 + z2) // 2, x, y0 + FH - 1, (z1 + z2) // 2, "minecraft:chain") if False else \
            bb.set(x, y0 + FH - 1, (z1 + z2) // 2, "minecraft:lantern[hanging=true]")
    bb.fill(cx - 4, by - 1, z2 - 3, cx + 3, by - 1, z2 - 1, "minecraft:dark_oak_planks")
    bb.fill(cx - 2, by, z2 - 3, cx + 1, by, z2 - 1, "minecraft:red_carpet")
    # cellar hatch and ladder, stair ladder to the upstairs
    bb.set(x2 - 2, y0, z1 + 2, "minecraft:spruce_trapdoor[facing=south,half=top,open=false]")
    bb.fill(x2 - 2, y0 - 5, z1 + 2, x2 - 2, y0 - 1, z1 + 2, "minecraft:ladder[facing=south]")
    bb.fill(x2 - 1, y0 + 1, z2 - 2, x2 - 1, y0 + FH, z2 - 2, "minecraft:ladder[facing=west]")
    bb.set(x2 - 1, y0 + FH, z2 - 2, "minecraft:ladder[facing=west]")
    # upstairs: Shakky's and Rayleigh's rooms
    rooms = [(x1 + 1, z1 + 1, cx - 1, z2 - 1), (cx + 1, z1 + 1, x2 - 1, z2 - 1)]
    bb.fill(cx, y0 + FH + 1, z1 + 1, cx, top - 1, z2 - 1, "minecraft:spruce_planks")
    bb.fill(cx, y0 + FH + 1, z2 - 3, cx, y0 + FH + 2, z2 - 3, AIR)
    furnish(bb, rooms, y0 + FH + 1, FH - 1, ["bedroom", "bedroom"], seed_of("skup"), tracker, doors=[(cx, z2 - 3), (x2 - 1, z2 - 2)],
            wood="dark_oak", audit=audit)
    return (x1 - 3, z1 - 3, x2 + 3, z2 + 3)


def terrace(bb, rng):
    """Boardwalk terrace in front of the bar under the roots, tables with umbrellas, bubble lamps."""
    x1, z1, x2, z2 = BAR[0] - 4, BAR[3] + 2, BAR[2] + 12, BAR[3] + 12
    bb.fill(x1, GY, z1, x2, GY, z2, BOARD)
    for x in range(x1, x2 + 1):
        bb.set(x, GY + 1, z2, "minecraft:spruce_fence")
    for z in range(z1, z2 + 1):
        bb.set(x1, GY + 1, z, "minecraft:spruce_fence")
    bb.fill((BAR[0] + BAR[2]) // 2 - 2, GY + 1, z2, (BAR[0] + BAR[2]) // 2 + 1, GY + 1, z2, AIR)
    cols = ["red", "white", "light_blue", "yellow"]
    for i, (tx, tz) in enumerate(((x1 + 4, z1 + 4), (x1 + 12, z1 + 6), (x1 + 20, z1 + 4), (x2 - 6, z1 + 5), (x2 - 3, z2 - 3))):
        bb.set(tx, GY + 1, tz, "onepiece:barrel_table[facing=north]")
        bb.set(tx + 1, GY + 1, tz, "onepiece:bar_stool[facing=west]")
        bb.set(tx - 1, GY + 1, tz, "onepiece:bar_stool[facing=east]")
        bb.fill(tx, GY + 2, tz, tx, GY + 3, tz, "minecraft:spruce_fence")
        bb.fill(tx - 1, GY + 4, tz - 1, tx + 1, GY + 4, tz + 1, f"minecraft:{cols[i % 4]}_wool")
    # bubble lamps: a post with a bubble round a lantern
    for (lx, lz) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2), (x1 + 14, z2)):
        bb.fill(lx, GY + 1, lz, lx, GY + 4, lz, "minecraft:spruce_fence")
        bb.set(lx, GY + 5, lz, "minecraft:lantern[hanging=false]")
        for (dx, dy, dz) in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, 1, 0)):
            bb.set(lx + dx, GY + 5 + dy, lz + dz, BUB)
    return (x1, z1, x2, z2)


def workshop(bb, tracker, audit):
    """The coating workshop on the channel: an open timber shed with a slipway and the Sunny in it, half coated."""
    x = CHAN_X
    z0 = 70
    stamp_ship(bb, "thousand_sunny", x, z0 + 30, water_y=0, rot=1)
    # a partial bubble coat: a few bubble arcs over the ship's bow
    for k in range(3):
        R = 12 - k
        zz = z0 + 6 + k * 2
        bb.fill_where(x - R, 0, zz, x + R, R + 2, zz, lambda X, yy, Z, R=R: np.abs(np.hypot(X - x, yy - 2) - R) < 0.6, BUB,
                      only_empty=True)
    # work platforms either side with resin barrels and the coating tools
    for (px, f) in ((x - 15, "east"), (x + 15, "west")):
        bb.fill(px - 2, 0, z0, px + 2, 0, z0 + 24, BOARD)
        for zz in range(z0, z0 + 25, 4):
            bb.fill(px - 2, -8, zz, px - 2, 0, zz, "minecraft:spruce_log[axis=y]")
            bb.fill(px + 2, -8, zz, px + 2, 0, zz, "minecraft:spruce_log[axis=y]")
        for zz in (z0 + 3, z0 + 4, z0 + 12, z0 + 20):
            bb.set(px, 1, zz, "minecraft:barrel[facing=up,open=false]")
        bb.set(px, 1, z0 + 8, "minecraft:cauldron")
        bb.set(px, 1, z0 + 16, "onepiece:keg[facing=north]")
    return (x - 18, z0 - 2, x + 18, N)


def boardwalk(bb):
    """A boardwalk on posts from the bar terrace over the mud to the workshop platform."""
    z = BAR[3] + 7
    for x in range(BAR[2] + 12, CHAN_X - 16):
        bb.fill(x, GY, z - 1, x, GY, z + 1, BOARD)
        if x % 4 == 0:
            bb.fill(x, -6, z - 2, x, GY + 1, z - 2, "minecraft:spruce_log[axis=y]")
            bb.fill(x, -6, z + 2, x, GY + 1, z + 2, "minecraft:spruce_log[axis=y]")
    # steps down from GY to the platform at 0
    for k in range(GY):
        bb.fill(CHAN_X - 16 - k + 0, GY - k, z - 1, CHAN_X - 16 - k, GY - k, z + 1, BOARD) if False else None
    for k in range(GY + 1):
        x = CHAN_X - 17 + k
        bb.fill(x, GY - k, z - 1, x, GY - k, z + 1, st("minecraft:spruce_stairs", "west"))
        bb.fill(x, -6, z - 1, x, GY - k - 1, z + 1, "minecraft:spruce_planks")


def bubbles(bb, rng, taken):
    k = 0
    for _ in range(300):
        x, z = int(rng.integers(8, N - 8)), int(rng.integers(8, N - 8))
        if not land(np.array([[x]]), np.array([[z]]))[0, 0]:
            continue
        g = hy(x, z)
        # a bubble welling up from the roots, resting on the ground (one block of it touches the floor)
        r = rng.uniform(1.2, 2.2)
        cy = g + 1 + r
        if any(t[0] <= x <= t[2] and t[1] <= z <= t[3] for t in taken[1:]):
            continue
        R = int(r) + 1
        bb.fill_where(x - R, g + 1, z - R, x + R, int(cy + R), z + R,
                      lambda X, yy, Z, r=r, cy=cy: np.abs(np.sqrt((X - x) ** 2 + (yy - cy) ** 2 + (Z - z) ** 2) - r) < 0.5, BUB,
                      only_empty=True)
        bb.set(x, g + 1, z, BUB)
        k += 1
        if k >= 22:
            break
    print("bubbles:", k)


def design():
    bb = BigBuild(seed=2020, y_min=-14, y_max=112)
    tracker = P.PropTracker(2020)
    audit = []
    rng = np.random.default_rng(2020)
    terrain(bb)
    x, z, r, h = TREE
    taken = [mangrove(bb, x, z, r, h, rng, number=13, skip=(50, 130))]      # the bar stands at its south foot
    taken.append(bar(bb, tracker, audit, rng))
    taken.append(terrace(bb, rng))
    taken.append(workshop(bb, tracker, audit))
    boardwalk(bb)
    for (x, z, r, h, n) in OTHERS:
        taken.append(mangrove(bb, x, z, r, h, rng, number=n))
    # little mangroves and shrubs on the floor
    k = 0
    for _ in range(2000):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        if not land(np.array([[x]]), np.array([[z]]))[0, 0] or any(t[0] <= x <= t[2] and t[1] <= z <= t[3] for t in taken):
            continue
        P.tree(bb, x, hy(x, z) + 1, z, int(rng.integers(5, 8)), ("oak", "jungle", "oak")[k % 3], rng)
        taken.append((x - 3, z - 3, x + 3, z + 3))
        k += 1
        if k >= 22:
            break
    bubbles(bb, rng, taken)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 2090, density=0.3,
              kinds=["minecraft:short_grass", "minecraft:fern", "minecraft:short_grass", "minecraft:large_fern", "minecraft:tall_grass"],
              flowers=["minecraft:blue_orchid", "minecraft:azure_bluet", "minecraft:pink_tulip", "minecraft:oxeye_daisy"],
              mask=lambda X, Z: land(X, Z) & (rect_d(X, Z, (BAR[0] - 6, BAR[1] - 4, BAR[2] + 14, BAR[3] + 14)) > 1))
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
    x1, z1, x2, z2 = BAR
    b.npc(x1 + 6, GY + 1, z1 + 6, "rayleigh", False)
    b.chest(x1 + 4, GY - 5, z1 + 4, "pirate", "east")
    return b, 0
