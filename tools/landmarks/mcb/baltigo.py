"""Baltigo v2, redesigned with the Minecraft Builder skill: the white-sand island that was the Revolutionary
Army's headquarters.

A pale desert island of white sand and bone-white rock, dunes rolling down to the sea. In the middle, walled
against the desert winds by a thick stone curtain with round towers and a gate, stands the headquarters: a stepped
fortress of pale stone climbing in three terraces, each terrace a full storeyed block with rooms (barracks, mess
hall, armory, the library of intelligence files, the war room round its giant map table, Sabo's command office),
and on top Dragon's tower with the map of the world on its floor and a balcony over the island. The dragon-wing
banners hang from the walls. Inside the curtain: the training courtyard with targets and sparring rings, more
barracks and stores, a water cistern, and the radio mast with its Den Den Mushi relay. A small landing on the north
shore. 168 x 168. y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, set_if_air, wing_floor, tier, cornice, lamp_post, glyph
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "baltigo"
TITLE = "Baltigo (Revolutionary HQ)"
CUTS = [5, 15, 25, 35]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 168
_S1 = NT.outline(84, 86, 70, 3520, wobble=0.07)
SHORE = _S1
GY = 4
CX, CZ = 84, 88
WALL = (40, 44, 128, 132)           # the curtain wall
GATE_X = CX
TIERS = [(CX - 26, CZ - 22, CX + 26, CZ + 22, 2), (CX - 19, CZ - 15, CX + 19, CZ + 15, 2), (CX - 12, CZ - 9, CX + 12, CZ + 9, 2)]
FH = 5
STONE = ["minecraft:calcite", "minecraft:diorite", "minecraft:polished_diorite", "minecraft:white_terracotta", "minecraft:smooth_quartz"]
SAND = [("minecraft:sand", 0.55), ("minecraft:smooth_sandstone", 0.12), ("minecraft:calcite", 0.12), ("minecraft:sandstone", 0.1),
        ("minecraft:white_concrete_powder", 0.0), ("minecraft:bone_block[axis=y]", 0.03), ("minecraft:diorite", 0.08)]
YARD = [("minecraft:smooth_sandstone", 0.3), ("minecraft:cut_sandstone", 0.2), ("minecraft:calcite", 0.2),
        ("minecraft:polished_diorite", 0.15), ("minecraft:sand", 0.15)]


def rect_d(X, Z, r):
    dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0)
    dz = np.maximum(np.maximum(r[1] - Z, Z - r[3]), 0)
    return np.hypot(dx, dz)


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = SHORE(X, Z)
    dune = GY + (NT.fbm(X * 0.6 + Z * 0.4, Z * 0.9, 3522, 18) - 0.45) * 14
    h = dune * np.clip((d - 1.5) / 14.0, 0, 1)
    w = np.clip((rect_d(X, Z, WALL) - 2) / 10.0, 0, 1)
    h = GY * (1 - w) + h * w
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
    return GRAD[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)] >= 3


def land(X, Z):
    return SHORE(X, Z) > 1.5


def hy(x, z):
    return int(HMAP[min(max(x, 0), N - 1), min(max(z, 0), N - 1)])


def terrain(bb):
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SAND, 3531, mask=lambda X, Z: land(X, Z) & (rect_d(X, Z, WALL) > 0),
             under="minecraft:sandstone", core="minecraft:stone", base=-6)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, [("minecraft:calcite", 0.4), ("minecraft:diorite", 0.3), ("minecraft:tuff", 0.1),
                                              ("minecraft:smooth_sandstone", 0.2)], 3532,
             mask=lambda X, Z: land(X, Z) & steep(X, Z), under="minecraft:stone", core="minecraft:stone", base=-6)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, YARD, 3533, mask=lambda X, Z: rect_d(X, Z, WALL) <= 0, under="minecraft:sandstone",
             core="minecraft:stone", base=-6)
    bed = lambda X, Z: np.round(-2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10))
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy == bed(X, Z)), "minecraft:sand")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy < bed(X, Z)) & (yy >= bed(X, Z) - 2), "minecraft:stone")


def banner(bb, x, y, z, axis, h=7):
    """A dragon-wing banner: a long black cloth with a red border and a white wing shape, hung from a beam."""
    wing = ["#.....", "##....", "###...", ".####.", "..####", "...###", "....##"]
    for r in range(h):
        for c in range(5):
            edge = c in (0, 4) or r == h - 1
            col = "minecraft:red_wool" if edge else ("minecraft:white_wool" if wing[r % len(wing)][c] == "#" else "minecraft:black_wool")
            if axis == "x":
                bb.set(x + c, y - r, z, col)
            else:
                bb.set(x, y - r, z + c, col)
    if axis == "x":
        bb.fill(x - 1, y + 1, z, x + 5, y + 1, z, "minecraft:dark_oak_fence")
    else:
        bb.fill(x, y + 1, z - 1, x, y + 1, z + 5, "minecraft:dark_oak_fence")


# ------------------------------------------------------------------ the curtain wall
def curtain(bb):
    x1, z1, x2, z2 = WALL
    y = GY
    for (a, b, c, d) in ((x1, z1, x2, z1 + 2), (x1, z2 - 2, x2, z2), (x1, z1, x1 + 2, z2), (x2 - 2, z1, x2, z2)):
        bb.mix(a, y - 2, b, c, y + 12, d, STONE[:4], [0.35, 0.3, 0.2, 0.15])
        bb.fill(a, y + 13, b, c, y + 13, d, "minecraft:smooth_quartz")
    # wall walk: hollow the middle row above y+6 and edge it with merlons
    for (a, b, c, d) in ((x1 + 1, z1 + 1, x2 - 1, z1 + 1), (x1 + 1, z2 - 1, x2 - 1, z2 - 1), (x1 + 1, z1 + 1, x1 + 1, z2 - 1),
                         (x2 - 1, z1 + 1, x2 - 1, z2 - 1)):
        bb.fill(a, y + 14, b, c, y + 14, d, AIR)
    for x in range(x1, x2 + 1):
        for z in (z1, z2):
            if x % 2 == 0:
                bb.set(x, y + 14, z, "minecraft:calcite")
    for z in range(z1, z2 + 1):
        for x in (x1, x2):
            if z % 2 == 0:
                bb.set(x, y + 14, z, "minecraft:calcite")
    # round towers on the corners and the middles of the sides
    for (tx, tz) in ((x1 + 1, z1 + 1), (x2 - 1, z1 + 1), (x1 + 1, z2 - 1), (x2 - 1, z2 - 1), ((x1 + x2) // 2, z1 + 1),
                     (x1 + 1, (z1 + z2) // 2), (x2 - 1, (z1 + z2) // 2)):
        bb.cylinder(tx, y - 2, tz, 5, y + 19, "minecraft:calcite")
        bb.cylinder(tx, y + 1, tz, 3, y + 18, AIR)
        bb.cylinder(tx, y + 1, tz, 3, y + 1, "minecraft:polished_diorite")
        bb.cylinder(tx, y + 10, tz, 3, y + 10, "minecraft:polished_diorite")
        bb.fill(tx, y + 1, tz - 3, tx, y + 19, tz - 3, "minecraft:ladder[facing=south]")
        bb.cylinder(tx, y + 19, tz, 4, y + 19, "minecraft:smooth_quartz")
        for k in range(16):
            a = 2 * math.pi * k / 16
            if k % 2 == 0:
                bb.set(tx + int(round(5 * math.cos(a))), y + 20, tz + int(round(5 * math.sin(a))), "minecraft:calcite")
        for k in range(4):
            a = 2 * math.pi * k / 4 + 0.4
            bb.fill(tx + int(round(5 * math.cos(a))), y + 13, tz + int(round(5 * math.sin(a))),
                    tx + int(round(5 * math.cos(a))), y + 14, tz + int(round(5 * math.sin(a))), "minecraft:iron_bars")
        bb.set(tx, y + 18, tz, "minecraft:lantern[hanging=true]")
    # the gate on the south side, with a barbican and two banners
    bb.fill(GATE_X - 3, y + 1, z2 - 2, GATE_X + 3, y + 8, z2, AIR)
    bb.fill(GATE_X - 3, y + 9, z2 - 2, GATE_X + 3, y + 9, z2, "minecraft:smooth_quartz")
    for gx in (GATE_X - 6, GATE_X + 6):
        bb.cylinder(gx, y - 2, z2 + 1, 3, y + 17, "minecraft:calcite")
        bb.cylinder(gx, y + 18, z2 + 1, 4, y + 18, "minecraft:smooth_quartz")
    banner(bb, GATE_X - 10, y + 12, z2 + 1, "x")
    banner(bb, GATE_X + 6, y + 12, z2 + 1, "x")
    for x in range(GATE_X - 3, GATE_X + 4):
        bb.set(x, y + 8, z2, "minecraft:iron_bars")
    # banners along the outside of the north and side walls
    for x in range(x1 + 12, x2 - 12, 24):
        banner(bb, x, y + 11, z1 - 1, "x")
    for z in range(z1 + 12, z2 - 12, 24):
        banner(bb, x1 - 1, y + 11, z, "z")
        banner(bb, x2 + 1, y + 11, z, "z")


# ------------------------------------------------------------------ the headquarters
def headquarters(bb, tracker, audit):
    kinds = [["bedroom", "bedroom", "dining", "kitchen", "storage", "bedroom", "bedroom", "storage"],
             ["library", "library", "living", "storage", "workshop", "bedroom"],
             ["library", "living", "dining", "storage"]]
    y = GY
    tops = []
    for k, (x1, z1, x2, z2, n) in enumerate(TIERS):
        top = tier(bb, x1, z1, x2, z2, y, n, FH, STONE[:4], "minecraft:glass_pane", "minecraft:diorite_stairs",
                   pilaster="minecraft:quartz_pillar[axis=y]", band="minecraft:light_gray_concrete", top_plate="minecraft:smooth_quartz",
                   weights=[0.4, 0.3, 0.2, 0.1], every=3, pil_every=6)
        cornice(bb, x1, z1, x2, z2, top, "minecraft:quartz_stairs", parapet="minecraft:diorite_wall")
        for f in range(n):
            fy = y + 1 + FH * f
            wing_floor(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, fy, FH - 1, "minecraft:calcite", seed_of("blt", k, f), tracker,
                       kinds[k][f * 3:f * 3 + 5] or kinds[k], corridor="x", cw=3, wood="dark_oak",
                       carpet=(None, "minecraft:red_carpet"), audit=audit,
                       keep=[(x1 + 1, z2 - 5, x1 + 5, z2 - 1), (CX - 2, z2 - 6, CX + 2, z2 - 1)])
        # stairs: a ladder well in the SW corner of every tier; doors on the south face
        bb.fill(x1 + 2, y + 1, z2 - 2, x1 + 2, top, z2 - 2, "minecraft:ladder[facing=north]")
        for f in range(1, n + 1):
            bb.set(x1 + 2, y + FH * f, z2 - 2, "minecraft:ladder[facing=north]")
        bb.set(x1 + 2, top + 1, z2 - 2, AIR)
        bb.fill(CX - 1, y + 1, z2, CX + 1, y + 3, z2, AIR)
        bb.fill(CX - 2, y + 4, z2 + 1, CX + 2, y + 4, z2 + 1, "minecraft:quartz_slab[type=bottom]")
        banner(bb, x1 + 4, top - 1, z2 + 1, "x")
        banner(bb, x2 - 8, top - 1, z2 + 1, "x")
        tops.append(top)
        y = top
    # the grand stair up the south front from the yard to the first terrace
    x1, z1, x2, z2, _ = TIERS[0]
    z2b = TIERS[1][3]
    t0 = tops[0]
    for i in range(t0 - GY):
        bb.fill(CX - 3, GY + 1 + i, z2 + 1 + (t0 - GY) - i, CX + 3, GY + 1 + i, z2 + 1 + (t0 - GY) - i, st("minecraft:quartz_stairs", "north"))
        bb.fill(CX - 3, GY + 1, z2 + 1 + (t0 - GY) - i, CX + 3, GY + i, z2 + 1 + (t0 - GY) - i, "minecraft:calcite")
    for i in range(tops[1] - t0):
        z = z2b + 1 + (tops[1] - t0) - i
        bb.fill(CX - 2, t0 + 1 + i, z, CX + 2, t0 + 1 + i, z, st("minecraft:quartz_stairs", "north"))
        bb.fill(CX - 2, t0 + 1, z, CX + 2, t0 + i, z, "minecraft:calcite")
    # the war room table and Sabo's office get their pieces in the middle tier corridor
    mx1, mz1, mx2, mz2, _ = TIERS[1]
    wy = tops[0] + 1
    bb.fill(CX - 4, wy, (mz1 + mz2) // 2 - 1, CX + 4, wy, (mz1 + mz2) // 2 + 1, "minecraft:dark_oak_planks")
    bb.fill(CX - 3, wy + 1, (mz1 + mz2) // 2 - 1, CX + 3, wy + 1, (mz1 + mz2) // 2 + 1, "minecraft:dark_oak_pressure_plate") if False else None
    for x in range(CX - 4, CX + 5):
        bb.set(x, wy + 1, (mz1 + mz2) // 2, ("minecraft:blue_carpet", "minecraft:green_carpet", "minecraft:yellow_carpet")[x % 3])
    dragon_tower(bb, tops[2])
    return (WALL[0] + 4, WALL[1] + 4, WALL[2] - 4, WALL[3] - 4), tops


def dragon_tower(bb, y0):
    """Dragon's tower on the top terrace: a square tower with a balcony, the room with the world map on its floor."""
    x1, z1, x2, z2 = CX - 6, CZ - 6, CX + 6, CZ + 6
    top = y0 + 12
    bb.fill(x1, y0 + 1, z1, x2, top, z2, "minecraft:calcite")
    bb.fill(x1 + 1, y0 + 1, z1 + 1, x2 - 1, top - 1, z2 - 1, AIR)
    for x in range(x1 + 2, x2 - 1, 3):
        for z in (z1, z2):
            bb.fill(x, y0 + 3, z, x, y0 + 9, z, "minecraft:glass_pane")
    for z in range(z1 + 2, z2 - 1, 3):
        for x in (x1, x2):
            bb.fill(x, y0 + 3, z, x, y0 + 9, z, "minecraft:glass_pane")
    bb.fill(CX - 1, y0 + 1, z2, CX + 1, y0 + 4, z2, AIR)
    # the world map on the floor: blue sea, the red line, the Grand Line, four blues, islands
    for x in range(x1 + 1, x2):
        for z in range(z1 + 1, z2):
            dx, dz = x - CX, z - CZ
            s = "minecraft:blue_concrete"
            if abs(dz) <= 0:
                s = "minecraft:light_blue_concrete"
            if abs(dx) <= 0:
                s = "minecraft:red_concrete"
            if (dx * 7 + dz * 13) % 11 == 0 and abs(dx) > 1 and abs(dz) > 1:
                s = "minecraft:lime_concrete"
            bb.set(x, y0, z, s)
    bb.set(CX - 4, y0 + 1, CZ - 4, "minecraft:lectern[facing=south]")
    bb.set(CX + 4, y0 + 1, CZ - 4, "minecraft:turtle_egg[eggs=1]")
    bb.fill(x1 + 1, top - 1, z1 + 1, x2 - 1, top - 1, z2 - 1, "minecraft:dark_oak_planks") if False else None
    bb.set(CX, top - 1, CZ, "minecraft:lantern[hanging=true]")
    # balcony round the tower and the stepped roof
    bb.fill(x1 - 2, y0 + 8, z1 - 2, x2 + 2, y0 + 8, z2 + 2, "minecraft:smooth_quartz")
    bb.fill(x1, y0 + 8, z1, x2, y0 + 8, z2, "minecraft:calcite")
    for (a, b, c, d) in ((x1 - 2, z1 - 2, x2 + 2, z1 - 2), (x1 - 2, z2 + 2, x2 + 2, z2 + 2), (x1 - 2, z1 - 2, x1 - 2, z2 + 2),
                         (x2 + 2, z1 - 2, x2 + 2, z2 + 2)):
        bb.fill(a, y0 + 9, b, c, y0 + 9, d, "minecraft:diorite_wall")
    bb.fill(CX - 1, y0 + 9, z2, CX + 1, y0 + 11, z2, AIR)
    bb.fill(x1 + 1, y0 + 8, z1 + 1, x2 - 1, y0 + 8, z2 - 1, AIR)
    bb.fill(x1 + 1, y0 + 8, z1 + 1, x1 + 2, y0 + 8, z1 + 2, "minecraft:calcite")
    bb.fill(x1 + 1, y0 + 1, z1 + 1, x1 + 1, y0 + 8, z1 + 1, "minecraft:ladder[facing=south]")
    for k in range(4):
        bb.fill(x1 + k, top + k, z1 + k, x2 - k, top + k, z2 - k, "minecraft:smooth_quartz" if k % 2 else "minecraft:calcite")
    bb.fill(CX, top + 4, CZ, CX, top + 12, CZ, "minecraft:iron_bars")
    bb.set(CX, top + 13, CZ, "minecraft:lightning_rod")
    banner(bb, x2 + 1, y0 + 7, CZ - 2, "z")
    banner(bb, x1 - 1, y0 + 7, CZ - 2, "z")


# ------------------------------------------------------------------ the courtyard
def courtyard(bb, tracker, audit, rng):
    x1, z1, x2, z2 = WALL
    y = GY
    # barracks blocks along the inside of the east and west walls
    for (bx1, bz1, bx2, bz2) in ((x1 + 8, z1 + 10, x1 + 20, z1 + 42), (x2 - 20, z1 + 10, x2 - 8, z1 + 42),
                                 (x1 + 8, z2 - 46, x1 + 20, z2 - 16), (x2 - 20, z2 - 46, x2 - 8, z2 - 16)):
        top = tier(bb, bx1, bz1, bx2, bz2, y, 2, FH, STONE[:3], "minecraft:glass_pane", "minecraft:diorite_stairs",
                   band="minecraft:light_gray_concrete", top_plate="minecraft:smooth_quartz", weights=[0.5, 0.3, 0.2], every=3)
        cornice(bb, bx1, bz1, bx2, bz2, top, "minecraft:quartz_stairs", parapet="minecraft:diorite_wall")
        for f in range(2):
            wing_floor(bb, bx1 + 1, bz1 + 1, bx2 - 1, bz2 - 1, y + 1 + FH * f, FH - 1, "minecraft:calcite", seed_of("bltb", bx1, bz1, f),
                       tracker, ["bedroom", "bedroom", "dining", "bedroom", "storage", "bedroom"], corridor="z", cw=3, wood="dark_oak",
                       audit=audit, keep=[(bx1 + 1, bz1 + 1, bx1 + 3, bz1 + 3)])
        bb.fill(bx1 + 2, y + 1, bz1 + 2, bx1 + 2, top, bz1 + 2, "minecraft:ladder[facing=south]")
        bb.set(bx1 + 2, y + FH, bz1 + 2, "minecraft:ladder[facing=south]")
        side = bx2 if bx1 < CX else bx1
        bb.fill(side, y + 1, (bz1 + bz2) // 2 - 1, side, y + 3, (bz1 + bz2) // 2 + 1, AIR)
    # training ground in the south-east of the yard: sparring rings and targets
    for (rx, rz) in ((CX + 20, z2 - 12), (CX + 34, z2 - 12)):
        bb.fill_where(rx - 5, y, rz - 5, rx + 5, y, rz + 5, lambda X, Y, Z: np.hypot(X - rx, Z - rz) <= 4.5, "minecraft:coarse_dirt")
        for k in range(16):
            a = 2 * math.pi * k / 16
            bb.set(rx + int(round(5 * math.cos(a))), y + 1, rz + int(round(5 * math.sin(a))), "minecraft:dark_oak_fence")
    for x in range(CX - 40, CX - 22, 4):
        bb.set(x, y + 1, z2 - 8, "minecraft:hay_block[axis=y]"); bb.set(x, y + 2, z2 - 8, "minecraft:target")
    for x in range(CX - 40, CX - 22, 6):
        bb.fill(x, y + 1, z2 - 14, x, y + 2, z2 - 14, "minecraft:dark_oak_fence")
        bb.set(x, y + 3, z2 - 14, "minecraft:carved_pumpkin[facing=south]")
    # the cistern
    cx, cz = CX + 34, z1 + 14
    bb.cylinder(cx, y - 3, cz, 5, y + 1, "minecraft:calcite")
    bb.cylinder(cx, y - 2, cz, 4, y, "minecraft:water")
    bb.cylinder(cx, y + 1, cz, 4, y + 1, AIR)
    # the radio mast with the relay snail
    mx, mz = CX - 34, z1 + 14
    for yy in range(y + 1, y + 32):
        for (a, b) in ((mx - 1, mz - 1), (mx + 1, mz - 1), (mx - 1, mz + 1), (mx + 1, mz + 1)):
            if yy < y + 30 - (yy - y) // 12:
                bb.set(a, yy, b, "minecraft:iron_block" if yy % 5 == 0 else "minecraft:iron_bars")
    bb.fill(mx, y + 1, mz, mx, y + 36, mz, "minecraft:iron_bars")
    bb.set(mx, y + 37, mz, "minecraft:lightning_rod")
    for yy in (y + 10, y + 20, y + 28):
        bb.fill(mx - 3, yy, mz, mx + 3, yy, mz, "minecraft:iron_bars")
    bb.fill(mx - 3, y + 1, mz + 3, mx + 3, y + 5, mz + 7, "minecraft:calcite")
    bb.fill(mx - 2, y + 1, mz + 4, mx + 2, y + 4, mz + 6, AIR)
    bb.fill(mx, y + 1, mz + 7, mx, y + 2, mz + 7, AIR)
    bb.set(mx - 1, y + 1, mz + 4, "minecraft:turtle_egg[eggs=3]"); bb.set(mx + 1, y + 1, mz + 4, "minecraft:lectern[facing=south]")
    bb.set(mx, y + 4, mz + 5, "minecraft:lantern[hanging=true]")
    # stores, crates and lamps
    for (sx, sz) in ((CX - 30, CZ + 30), (CX - 29, CZ + 30), (CX + 29, CZ - 30), (CX + 30, CZ - 30), (CX + 30, CZ - 29)):
        bb.set(sx, y + 1, sz, "minecraft:barrel[facing=up,open=false]")
    for k in range(0, 360, 30):
        a = math.radians(k)
        lx, lz = int(CX + 36 * math.cos(a)), int(CZ + 36 * math.sin(a))
        if rect_d(np.array([[lx]]), np.array([[lz]]), (TIERS[0][0] - 2, TIERS[0][1] - 2, TIERS[0][2] + 2, TIERS[0][3] + 16))[0, 0] > 0:
            lamp_post(bb, lx, y + 1, lz, post="minecraft:diorite_wall")


def landing(bb):
    """A stone landing on the north shore with a path of slabs to the north wall postern."""
    x = CX
    zs = None
    for z in range(0, WALL[1]):
        if SHORE(np.array([[x]]), np.array([[z]]))[0, 0] > 1.5:
            zs = z
            break
    if zs is None:
        return
    bb.fill(x - 3, -3, zs - 10, x + 3, 0, zs + 1, "minecraft:calcite")
    bb.fill(x - 3, 1, zs - 10, x + 3, 1, zs + 1, "minecraft:smooth_quartz_slab[type=bottom]")
    for z in (zs - 10, zs - 5):
        bb.set(x - 3, 2, z, "minecraft:lantern[hanging=false]"); bb.set(x + 3, 2, z, "minecraft:lantern[hanging=false]")
    for z in range(zs + 2, WALL[1]):
        bb.fill(x - 1, hy(x, z), z, x + 1, hy(x, z), z, "minecraft:smooth_sandstone")
    bb.fill(x - 1, GY + 1, WALL[1], x + 1, GY + 3, WALL[1] + 2, AIR)
    bb.fill(x - 3, -2, zs - 16, x + 3, 0, zs - 11, "minecraft:spruce_planks") if False else None


def scenery(bb, rng, taken):
    """Bone-white rocks and dead bushes on the dunes; a few bleached ribs half buried in the sand."""
    k = 0
    for _ in range(3000):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        X, Z = np.array([[x]]), np.array([[z]])
        if not land(X, Z)[0, 0] or SHORE(X, Z)[0, 0] < 6 or rect_d(X, Z, WALL)[0, 0] < 4:
            continue
        r = rng.random()
        y = hy(x, z)
        if r < 0.15:
            NT.boulder(bb, x, y, z, int(rng.integers(2, 4)), rng, blocks=("minecraft:calcite", "minecraft:diorite", "minecraft:smooth_sandstone"))
        elif r < 0.2:
            for i in range(5):
                a = -0.6 + i * 0.3
                bb.fill(x + i * 2, y + 1, z, x + i * 2, y + 4 - abs(i - 2), z, "minecraft:bone_block[axis=y]")
        else:
            bb.set(x, y + 1, z, "minecraft:dead_bush" if r < 0.85 else "minecraft:short_dry_grass")
        k += 1
        if k >= 260:
            break


def design():
    bb = BigBuild(seed=3520, y_min=-14, y_max=80)
    tracker = P.PropTracker(3520)
    audit = []
    rng = np.random.default_rng(3520)
    terrain(bb)
    curtain(bb)
    box, tops = headquarters(bb, tracker, audit)
    courtyard(bb, tracker, audit, rng)
    landing(bb)
    scenery(bb, rng, [])
    return bb, audit, tops


def steady(b):
    """Sand and gravel with nothing solid under it would fall when the build generates: turn those into blocks that
    stay put."""
    import render
    for (x, y, z), s in list(b.blocks.items()):
        n = s.split("[")[0]
        if n.endswith(("gravel", "sand", "concrete_powder")) and "sandstone" not in n:
            below = b.blocks.get((x, y - 1, z))
            if below is None or render.shape_of(below) != "full":
                b.blocks[(x, y, z)] = "minecraft:coarse_dirt" if "gravel" in n else "minecraft:smooth_sandstone" if "sand" in n else \
                    n.replace("concrete_powder", "concrete")


def build():
    bb, audit, tops = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    steady(b)
    b.chest(CX + 3, tops[2] + 1, CZ - 3, "medium", "west")
    b.chest(CX + 9, tops[0] + 1, CZ + 7, "medium", "north")
    b.chest(CX - 30, GY + 1, CZ - 34, "easy", "east")
    b.npc(CX, tops[2] + 1, CZ, "dragon", False)
    b.npc(CX - 6, tops[0] + 1, CZ, "sabo", False)
    return b, 0
