"""Davy Back Fight v2 on Long Ring Long Land, redesigned with the Minecraft Builder skill.

Long Ring Long Land is a ring of long, flat grass islands, so the land here is a wide grassy ring round a lagoon on the
east, with its tail curling round; the trees are the island's stretched-out ones (trunks 20-30 tall with small round
crowns on top) and the long grass grows in drifts. In the middle: the Davy Back field, a flat open lawn (radius 30) for
the games, the Groggy Ring pitch marked out in white with a goal ring on a pole at each end of its long axis outside
the lawn. Round the field: two grandstands under striped awnings (north and south), Foxy's big striped command tent
(west) with the stage and his throne, party hall and Foxy's rooms, the Combat boxing ring under fairground lights, a
midway of food and game stalls with bunting, the Foxy Pirates' tents, and the Donut Race start on the south shore
with the pier, the race barrels-boats and the Sexy Foxy moored off it. 176 x 176. Ground = y 2, sea y 0. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, set_if_air, lamp_post, glyph, table
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb import sexy_foxy as FX

SID = "davy_back_stage"
TITLE = "Davy Back Fight Arena (Long Ring Long Land)"
CUTS = [3, 8, 14]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 176
C = 88                      # the field centre (x and z)
FIELD = 30                  # flat open lawn radius (the arena needs >= 30, buoys at 28)
TY = 2                      # ground
_ISLE = NT.outline(C, C - 4, 68, 5510, wobble=0.07)
_LAG = NT.outline(C + 62, C - 8, 26, 5511, wobble=0.12)    # the lagoon bite on the east (the "ring")
_BAY = NT.outline(C + 2, C + 92, 30, 5512, wobble=0.1)     # the south bay where the race starts and the ship lies
TENT = (C - 66, C - 16, C - 40, C + 16)                    # Foxy's command tent (x1, z1, x2, z2)
STRIPES = ("minecraft:red_wool", "minecraft:white_wool")
GRASS = [("minecraft:grass_block", 0.8), ("minecraft:moss_block", 0.05), ("minecraft:coarse_dirt", 0.05),
         ("minecraft:podzol", 0.04), ("minecraft:rooted_dirt", 0.06)]
SAND = [("minecraft:sand", 0.78), ("minecraft:sandstone", 0.08), ("minecraft:clay", 0.14)]
PATH = [("minecraft:dirt_path", 0.6), ("minecraft:coarse_dirt", 0.25), ("minecraft:gravel", 0.15)]


def shore(X, Z):
    return np.minimum(np.minimum(_ISLE(X, Z), -_LAG(X, Z)), -_BAY(X, Z))


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = shore(X, Z)
    roll = TY + NT.fbm(X, Z, 5513, 26) * 4 - 1.2
    h = np.where(d < 9, TY * np.clip(d / 9.0, 0, 1) + 0.3, roll)
    r = np.hypot(X - C, Z - C)
    h = np.where(r < FIELD + 14, TY + (roll - TY) * np.clip((r - FIELD - 2) / 12.0, 0, 1), h)
    return np.where(d < 1.5, -1, np.round(h))


def build_maps():
    X = np.arange(N)[:, None].astype(float)
    Z = np.arange(N)[None, :].astype(float)
    return _height(X, Z).astype(int), shore(X, Z)


HMAP, SHORE = build_maps()


def height(X, Z):
    return HMAP[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def land(X, Z):
    return SHORE[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)] > 1.5


def sh(X, Z):
    return SHORE[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def hy(x, z):
    return int(HMAP[min(max(x, 0), N - 1), min(max(z, 0), N - 1)])


def paths(X, Z):
    """Trodden paths: a ring road round the field and spokes to the tent, the midway, the pier."""
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    r = np.hypot(X - C, Z - C)
    m = (np.abs(r - (FIELD + 4)) <= 1.2)
    m |= (np.abs(Z - C) <= 1.5) & (X < C - FIELD) & (X > TENT[2])
    m |= (np.abs(X - (C + 10 + 3 * np.sin(Z * 0.08))) <= 1.5) & (Z > C + FIELD) & (Z < C + 66)
    m |= (np.abs(Z - (C - 44)) <= 1.5) & (X > C - 20) & (X < C + 40)
    return m


def terrain(bb):
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SAND, 5520, mask=lambda X, Z: land(X, Z) & (sh(X, Z) < 7),
             under="minecraft:sandstone", core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, GRASS, 5521, mask=lambda X, Z: land(X, Z) & (sh(X, Z) >= 7) & ~paths(X, Z) & (np.hypot(np.asarray(X, float) - C, np.asarray(Z, float) - C) > FIELD + 2),
             core="minecraft:stone")
    lawn = lambda X, Z: np.hypot(np.asarray(X, float) - C, np.asarray(Z, float) - C) <= FIELD + 2
    NT.cover(bb, 0, 0, N - 1, N - 1, height, [("minecraft:grass_block", 1.0)], 5523, mask=lambda X, Z: lawn(X, Z), core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, PATH, 5522, mask=lambda X, Z: land(X, Z) & (sh(X, Z) >= 7) & paths(X, Z),
             core="minecraft:stone")
    bed = lambda X, Z: np.round(-2 - np.clip(-sh(X, Z) * 0.5, 0, 9))
    sea = lambda X, Z: ~land(X, Z)
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: sea(X, Z) & (yy > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: sea(X, Z) & (yy == bed(X, Z)), "minecraft:sand")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: sea(X, Z) & (yy < bed(X, Z)) & (yy >= bed(X, Z) - 2), "minecraft:stone")


# ------------------------------------------------------------------ the field
def field(bb):
    """The lawn stays open: only flush white lines (the Groggy Ring pitch) in the grass, goal rings outside it."""
    y = TY
    # halfway line, centre circle, the pitch outline (an oval along x)
    for a in range(0, 360, 2):
        t = math.radians(a)
        bb.set(C + int(round(6 * math.cos(t))), y, C + int(round(6 * math.sin(t))), "minecraft:white_concrete")
        bb.set(C + int(round(27 * math.cos(t))), y, C + int(round(19 * math.sin(t))), "minecraft:white_concrete")
    bb.fill(C, y, C - 19, C, y, C + 19, "minecraft:white_concrete")
    for side in (-1, 1):
        for a in range(-60, 61, 3):
            t = math.radians(a)
            bb.set(C + side * (27 - int(round(8 * math.cos(t)))) , y, C + int(round(9 * math.sin(t))), "minecraft:white_concrete")
    # goal rings on tall poles past each end of the pitch (outside the open lawn)
    for side in (-1, 1):
        gx = C + side * (FIELD + 2)
        gy = hy(gx, C)
        bb.fill(gx, gy - 2, C, gx, gy + 12, C, "minecraft:stripped_birch_log[axis=y]")
        for a in range(0, 360, 6):
            t = math.radians(a)
            bb.set(gx, gy + 18 + int(round(5 * math.sin(t))), C + int(round(5 * math.cos(t))),
                   "minecraft:yellow_concrete" if a % 36 else "minecraft:red_concrete")
        bb.fill(gx, gy + 13, C, gx, gy + 13, C, "minecraft:yellow_concrete")
        for k in (-1, 1):
            bb.set(gx, gy + 14, C + k * 4, "minecraft:white_banner[rotation=0]") if False else None
    # corner flags round the lawn edge
    for a in range(0, 360, 45):
        t = math.radians(a + 22.5)
        x, z = C + int(round((FIELD + 1) * math.cos(t))), C + int(round((FIELD + 1) * math.sin(t)))
        bb.fill(x, hy(x, z) + 1, z, x, hy(x, z) + 3, z, "minecraft:birch_fence")
        bb.set(x, hy(x, z) + 4, z, ("minecraft:orange_wool", "minecraft:yellow_wool")[(a // 45) % 2])


def grandstand(bb, x1, x2, z0, facing, rows=7):
    """Stepped plank seats rising away from the field, a back wall and a striped awning on posts."""
    dz = -1 if facing == "south" else 1          # facing = the side the seats face (the field)
    y0 = TY
    for r in range(rows):
        z = z0 + dz * -r * -1 if False else z0 - dz * r * -1
        z = z0 + (-dz) * -r if False else z0 + (r if facing == "north" else -r)
        bb.fill(x1, y0 - 3, z, x2, y0 + r, z, "minecraft:spruce_planks")
        bb.fill(x1, y0 + r + 1, z, x2, y0 + r + 1, z, st("minecraft:spruce_stairs", "south" if facing == "north" else "north"))
        bb.fill(x1, y0 + r + 2, z, x2, y0 + r + 9, z, AIR)
    zb = z0 + (rows if facing == "north" else -rows)
    bb.fill(x1, y0 - 3, zb, x2, y0 + rows + 6, zb, "minecraft:spruce_planks")
    for x in range(x1, x2 + 1, 4):
        bb.fill(x, y0 + 1, zb, x, y0 + rows + 6, zb, "minecraft:stripped_spruce_log[axis=y]")
    for x in (x1, x2):
        for r in range(rows + 1):
            z = z0 + (r if facing == "north" else -r)
            bb.fill(x, y0 + r + 1, z, x, y0 + r + 1, z, "minecraft:spruce_planks")
            bb.set(x, y0 + r + 2, z, "minecraft:spruce_fence")
    # awning: striped wool sloping down toward the field, on posts at the front
    zf = z0 - (1 if facing == "north" else -1)
    for x in range(x1, x2 + 1, 6):
        bb.fill(x, y0 + 1, zf, x, y0 + 8, zf, "minecraft:spruce_fence")
    for r in range(rows + 2):
        z = zf + (r if facing == "north" else -r)
        y = y0 + 9 + r // 2
        for x in range(x1 - 1, x2 + 2):
            bb.set(x, y, z, STRIPES[(x // 2) % 2])
    for x in range(x1, x2 + 1, 6):
        bb.set(x, y0 + 8, zf, "minecraft:lantern[hanging=true]") if False else None
    # stair access at both ends
    for x in (x1 - 1, x2 + 1):
        for r in range(rows):
            z = z0 + (r if facing == "north" else -r)
            bb.set(x, y0 + r + 1, z, st("minecraft:spruce_stairs", "south" if facing == "north" else "north"))
    # Foxy Pirate banners on the back wall
    for x in range(x1 + 2, x2 - 1, 8):
        bb.fill(x, y0 + rows + 2, zb + (1 if facing == "north" else -1), x, y0 + rows + 4, zb + (1 if facing == "north" else -1),
                "minecraft:orange_wool")


# ------------------------------------------------------------------ Foxy's command tent
def striped_tent(bb, x1, z1, x2, z2, y, wall_h, peak_h, stripes=STRIPES, axis="x"):
    """A big marquee: striped wool walls, a ridge roof in stripes running down the slopes, a pennant on each pole."""
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            k = (x if axis == "z" else z)
            if edge:
                bb.fill(x, y + 1, z, x, y + wall_h, z, stripes[((x + z) // 2) % 2])
    half = (z2 - z1) / 2 if axis == "x" else (x2 - x1) / 2
    for i in range(int(math.ceil(half)) + 2):
        yy = y + wall_h + 1 + int(round(peak_h * min(1.0, i / max(1.0, half))))
        if axis == "x":
            for x in range(x1 - 1, x2 + 2):
                s = stripes[(x // 2) % 2]
                for z in (z1 - 1 + i, z2 + 1 - i):
                    if z1 - 1 <= z <= z2 + 1:
                        bb.set(x, yy, z, s)
    for x in range(x1, x2 + 1, max(1, (x2 - x1) // 3)):
        top = y + wall_h + 1 + peak_h
        bb.fill(x, top, (z1 + z2) // 2, x, top + 4, (z1 + z2) // 2, "minecraft:spruce_fence")
        bb.set(x, top + 4, (z1 + z2) // 2 + 1, "minecraft:orange_wool")
        bb.set(x, top + 3, (z1 + z2) // 2 + 1, "minecraft:orange_wool")


def command_tent(bb, tracker, audit):
    x1, z1, x2, z2 = TENT
    y = TY
    bb.fill(x1, y - 3, z1, x2, y, z2, "minecraft:dirt")
    bb.fill(x1, y, z1, x2, y, z2, "minecraft:spruce_planks")
    bb.fill(x1 + 1, y + 1, z1 + 1, x2 - 1, y + 16, z2 - 1, AIR)
    striped_tent(bb, x1, z1, x2, z2, y, 7, 9)
    # the stage at the west end with Foxy's throne
    bb.fill(x1 + 1, y + 1, z1 + 4, x1 + 6, y + 1, z2 - 4, "minecraft:red_carpet") if False else None
    bb.fill(x1 + 1, y + 1, z1 + 4, x1 + 6, y + 2, z2 - 4, "minecraft:dark_oak_planks")
    bb.fill(x1 + 7, y + 1, z1 + 4, x1 + 7, y + 1, z2 - 4, st("minecraft:dark_oak_stairs", "west"))
    bb.fill(x1 + 1, y + 3, z1 + 4, x1 + 6, y + 3, z2 - 4, "minecraft:red_carpet")
    cz = (z1 + z2) // 2
    bb.fill(x1 + 1, y + 3, cz - 1, x1 + 1, y + 6, cz + 1, "minecraft:gold_block")
    bb.set(x1 + 2, y + 3, cz, st("minecraft:dark_oak_stairs", "west"))
    bb.set(x1 + 2, y + 3, cz - 1, "minecraft:dark_oak_trapdoor[facing=north,half=bottom,open=true]") if False else None
    for z in (cz - 3, cz + 3):
        bb.fill(x1 + 2, y + 3, z, x1 + 2, y + 6, z, "minecraft:spruce_fence")
        bb.set(x1 + 2, y + 7, z, "minecraft:lantern[hanging=false]")
    bb.fill(x1 + 1, y + 4, cz - 2, x1 + 1, y + 7, cz + 2, "minecraft:orange_wool")
    # the party hall: long tables with food, barrels, bunting lights
    for zz in (z1 + 5, z2 - 5):
        for x in range(x1 + 10, x2 - 3):
            bb.set(x, y + 1, zz, "minecraft:spruce_fence")
            bb.set(x, y + 2, zz, "minecraft:spruce_pressure_plate") if x % 3 else bb.set(x, y + 2, zz, "minecraft:white_carpet")
            for dz in (-1, 1):
                if x % 2 == 0:
                    bb.set(x, y + 1, zz + dz, st("minecraft:spruce_stairs", "north" if dz > 0 else "south"))
    for x in range(x1 + 11, x2 - 3, 4):
        for zz in (z1 + 5, z2 - 5):
            bb.set(x, y + 2, zz, ("minecraft:pumpkin_pie" if False else "minecraft:candle[candles=3,lit=true]"))
    for (x, z) in ((x2 - 2, z1 + 2), (x2 - 3, z1 + 2), (x2 - 2, z1 + 3), (x2 - 2, z2 - 2), (x2 - 3, z2 - 2)):
        bb.set(x, y + 1, z, "minecraft:barrel[facing=up,open=false]")
    bb.set(x2 - 2, y + 2, z1 + 2, "onepiece:sake_barrel[axis=y]")
    for x in range(x1 + 4, x2 - 1, 5):
        bb.fill(x, y + 12, cz, x, y + 13, cz, "minecraft:iron_chain[axis=y]")
        bb.set(x, y + 11, cz, "minecraft:lantern[hanging=true]")
    # Foxy's rooms behind the stage: a lean-to block on the west with a bedroom and a trophy room
    rx1, rx2 = x1 - 12, x1 - 1
    bb.fill(rx1, y - 3, z1 + 2, rx2, y, z2 - 2, "minecraft:dirt")
    bb.fill(rx1, y, z1 + 2, rx2, y, z2 - 2, "minecraft:spruce_planks")
    bb.fill(rx1, y + 1, z1 + 2, rx2, y + 5, z2 - 2, "minecraft:orange_terracotta")
    for x in (rx1, rx2):
        for z in range(z1 + 2, z2 - 1, 4):
            bb.fill(x, y + 1, z, x, y + 5, z, "minecraft:stripped_spruce_log[axis=y]")
    bb.fill(rx1 + 1, y + 1, z1 + 3, rx2 - 1, y + 5, z2 - 3, AIR)
    bb.fill(rx1 + 1, y + 1, cz, rx2 - 1, y + 5, cz, "minecraft:orange_terracotta")
    rooms = [(rx1 + 1, z1 + 3, rx2 - 1, cz - 1), (rx1 + 1, cz + 1, rx2 - 1, z2 - 3)]
    bb.fill(rx2, y + 1, cz - 2, rx2, y + 2, cz - 2, AIR)
    bb.fill(rx2, y + 1, cz + 2, rx2, y + 2, cz + 2, AIR)
    bb.fill(x1, y + 1, cz - 2, x1, y + 2, cz - 2, AIR)
    bb.fill(x1, y + 1, cz + 2, x1, y + 2, cz + 2, AIR)
    for i, (r, k) in enumerate(zip(rooms, ("bedroom", "storage"))):
        P.furnish_room(bb, r, y + 1, k, height=5, seed=seed_of("foxy", i), doors=[(rx2, cz - 2), (rx2, cz + 2)], wood="spruce",
                       tracker=tracker)
        txt, ok = P.audit_props(bb, [r], y + 1, 5)
        if not ok:
            audit.append(txt)
    for z in range(z1 + 4, z2 - 3, 3):
        bb.fill(rx1, y + 2, z, rx1, y + 3, z, "minecraft:orange_stained_glass_pane")
    P.gable_roof(bb, rx1 - 1, z1 + 1, rx2, z2 - 1, y + 6, "minecraft:spruce_stairs", ridge_axis="z",
                 gable_fill="minecraft:orange_terracotta", overhang=0)
    # entrance from the field side (east) with an arch of torches
    bb.fill(x2, y + 1, cz - 2, x2, y + 5, cz + 2, AIR)
    for z in (cz - 3, cz + 3):
        bb.fill(x2 + 1, y + 1, z, x2 + 1, y + 6, z, "minecraft:stripped_spruce_log[axis=y]")
        bb.set(x2 + 1, y + 7, z, "minecraft:lantern[hanging=false]")
    bb.fill(x2 + 1, y + 6, cz - 2, x2 + 1, y + 6, cz + 2, "minecraft:orange_wool")
    word = "FOXY"
    font = {"F": ["###", "#..", "##.", "#..", "#.."], "O": ["###", "#.#", "#.#", "#.#", "###"], "X": ["#.#", "#.#", ".#.", "#.#", "#.#"],
            "Y": ["#.#", "#.#", ".#.", ".#.", ".#."]}
    rows = ["".join(font[ch][r] + "." for ch in word)[::-1] for r in range(5)]   # read from the east: +z runs leftwards
    glyph(bb, rows, x2 + 1, y + 12, cz - len(rows[0]) // 2, "minecraft:yellow_concrete", axis="z")
    return (rx1 - 2, z1 - 2, x2 + 3, z2 + 2)


# ------------------------------------------------------------------ the Combat ring, the midway, crew tents
def boxing_ring(bb, cx, cz):
    """The Combat boxing ring: a raised square with corner posts, rope fences and fairground lights over it."""
    y = hy(cx, cz)
    bb.fill(cx - 7, y - 2, cz - 7, cx + 7, y + 1, cz + 7, "minecraft:spruce_planks")
    bb.fill(cx - 6, y + 2, cz - 6, cx + 6, y + 2, cz + 6, "minecraft:white_wool")
    bb.fill(cx - 5, y + 2, cz - 5, cx + 5, y + 2, cz + 5, "minecraft:light_blue_wool")
    for (x, z, c) in ((cx - 6, cz - 6, "red"), (cx + 6, cz + 6, "blue"), (cx - 6, cz + 6, "white"), (cx + 6, cz - 6, "white")):
        bb.fill(x, y + 2, z, x, y + 5, z, f"minecraft:{c}_concrete")
    for k in range(-5, 6):
        for yy in (y + 3, y + 4):
            for (x, z) in ((cx + k, cz - 6), (cx + k, cz + 6), (cx - 6, cz + k), (cx + 6, cz + k)):
                bb.set(x, yy, z, "minecraft:white_stained_glass_pane" if False else "minecraft:iron_bars")
    for i in range(3):
        bb.set(cx, y + 2 - i - 0, cz + 7 + i, st("minecraft:spruce_stairs", "north")) if False else None
    bb.set(cx, y + 2, cz + 6, AIR); bb.set(cx, y + 3, cz + 6, AIR); bb.set(cx, y + 4, cz + 6, AIR)
    for i in range(3):
        bb.set(cx, y + 1 - i + 1, cz + 7 + i, st("minecraft:spruce_stairs", "north"))
    # lights: four tall poles with lanterns strung across
    for (x, z) in ((cx - 9, cz - 9), (cx + 9, cz - 9), (cx - 9, cz + 9), (cx + 9, cz + 9)):
        yy = hy(x, z)
        bb.fill(x, yy + 1, z, x, yy + 12, z, "minecraft:spruce_fence")
        bb.set(x, yy + 13, z, "minecraft:lantern[hanging=false]")
    for t in np.linspace(0, 1, 19):
        for (ax, az, bx, bz) in ((cx - 9, cz - 9, cx + 9, cz + 9), (cx + 9, cz - 9, cx - 9, cz + 9)):
            x = int(round(ax + (bx - ax) * t)); z = int(round(az + (bz - az) * t))
            sag = int(round(3 * math.sin(math.pi * t)))
            bb.set(x, y + 14 - sag, z, "minecraft:iron_chain[axis=y]" if int(t * 18) % 3 else "minecraft:lantern[hanging=true]")
    return (cx - 10, cz - 10, cx + 10, cz + 10)


def stall(bb, x, z, rot, kind, rng, k):
    """A market stall: a counter, posts, a striped awning, goods on the counter and crates behind."""
    y = hy(x, z)
    w, d = 5, 4
    x2, z2 = x + w - 1, z + d - 1
    bb.fill(x, y - 2, z, x2, y, z2, "minecraft:dirt")
    bb.fill(x, y, z, x2, y, z2, "minecraft:spruce_planks")
    cols = (("minecraft:red_wool", "minecraft:white_wool"), ("minecraft:orange_wool", "minecraft:yellow_wool"),
            ("minecraft:blue_wool", "minecraft:white_wool"), ("minecraft:lime_wool", "minecraft:white_wool"))[k % 4]
    for (px, pz) in ((x, z), (x2, z), (x, z2), (x2, z2)):
        bb.fill(px, y + 1, pz, px, y + 3, pz, "minecraft:spruce_fence")
    for xx in range(x - 1, x2 + 2):
        for zz in range(z - 1, z2 + 2):
            yy = y + 4 + (1 if z <= zz <= z2 - 1 else 0) if False else y + 4
            bb.set(xx, yy + (1 if z + 1 <= zz <= z2 - 1 else 0), zz, cols[(xx - x) % 2])
    front = z if rot == 0 else z2
    bb.fill(x + 1, y + 1, front, x2 - 1, y + 1, front, "minecraft:spruce_planks")
    goods = {"food": ("minecraft:melon", "minecraft:pumpkin", "minecraft:hay_block"),
             "game": ("minecraft:target", "minecraft:barrel[facing=up,open=false]", "minecraft:target"),
             "drink": ("onepiece:sake_barrel[axis=y]", "minecraft:barrel[facing=up,open=false]", "minecraft:brewing_stand"),
             "prize": ("minecraft:chiseled_bookshelf[facing=north]" if False else "minecraft:gold_block", "minecraft:barrel[facing=up,open=false]",
                       "minecraft:decorated_pot")}[kind]
    for i, xx in enumerate(range(x + 1, x2)):
        bb.set(xx, y + 2, front, goods[i % len(goods)] if "pot" not in goods[i % len(goods)] else "minecraft:decorated_pot")
    back = z2 if rot == 0 else z
    bb.set(x + 1, y + 1, back, "minecraft:barrel[facing=up,open=false]")
    bb.set(x2 - 1, y + 1, back, "minecraft:barrel[facing=up,open=false]")
    return (x - 1, z - 1, x2 + 1, z2 + 1)


def crew_tent(bb, x, z, rng, k):
    """A small A-frame crew tent in orange or white canvas, a bedroll and a lantern inside, a campfire out front."""
    y = hy(x, z)
    cloth = ("minecraft:orange_wool", "minecraft:white_wool", "minecraft:yellow_wool")[k % 3]
    for i in range(4):
        bb.fill(x - 3 + i, y + 1 + i, z, x - 3 + i, y + 1 + i, z + 5, cloth)
        bb.fill(x + 3 - i, y + 1 + i, z, x + 3 - i, y + 1 + i, z + 5, cloth)
    bb.fill(x - 2, y + 1, z + 5, x + 2, y + 3, z + 5, cloth)
    bb.set(x, y + 1, z + 5, cloth)
    bb.fill(x - 1, y + 1, z + 1, x - 1, y + 1, z + 2, "minecraft:white_carpet")
    bb.set(x + 1, y + 1, z + 3, "minecraft:lantern[hanging=false]")
    bb.set(x, y + 1, z - 3, "minecraft:campfire[lit=true,signal_fire=false]")
    bb.set(x - 2, y + 1, z - 3, "minecraft:spruce_log[axis=z]")
    return (x - 4, z - 4, x + 4, z + 6)


def bunting(bb, ax, az, bx, bz, y):
    n = int(max(abs(bx - ax), abs(bz - az)))
    for i in range(n + 1):
        t = i / max(1, n)
        x = int(round(ax + (bx - ax) * t)); z = int(round(az + (bz - az) * t))
        sag = int(round(2 * math.sin(math.pi * t)))
        bb.set(x, y - sag, z, ("minecraft:red_wool", "minecraft:yellow_wool", "minecraft:white_wool", "minecraft:orange_wool")[i % 4]
               if i % 2 else "minecraft:iron_chain[axis=x]" if abs(bx - ax) >= abs(bz - az) else "minecraft:iron_chain[axis=z]")


def midway(bb, rng, taken):
    """Food and game stalls in two rows either side of the path south-east of the field, bunting over the path."""
    kinds = ("food", "game", "drink", "prize", "food", "game", "drink", "food")
    k = 0
    for i, z in enumerate(range(C + FIELD + 8, C + 64, 8)):
        px = int(round(C + 10 + 3 * math.sin(z * 0.08)))
        for side in (-1, 1):
            x = px + (3 if side > 0 else -8)
            if not land(np.array([x, x + 5]), np.array([z, z + 4])).all():
                continue
            taken.append(stall(bb, x, z, 0, kinds[k % len(kinds)], rng, k))
            k += 1
        if i % 2 == 0:
            for x in (px - 3, px + 3):
                bb.fill(x, hy(x, z - 2) + 1, z - 2, x, hy(x, z - 2) + 6, z - 2, "minecraft:spruce_fence")
            bunting(bb, px - 3, z - 2, px + 3, z - 2, hy(px, z - 2) + 6)
    print("stalls:", k)


def pier(bb, rng):
    """The Donut Race start: a pier from the south shore, start flags, the barrel boats tied up, the Sexy Foxy anchored
    off the end."""
    x = C + 8
    zs = next(z for z in range(C + 40, N) if not land(np.array([x]), np.array([z]))[0])
    for z in range(zs - 4, zs + 16):
        bb.fill(x - 1, 1, z, x + 1, 1, z, "minecraft:spruce_planks")
        if z % 4 == 0:
            for xx in (x - 2, x + 2):
                bb.fill(xx, -6, z, xx, 2, z, "minecraft:spruce_log[axis=y]")
            bb.set(x + 2, 3, z, "minecraft:lantern[hanging=false]")
    # start gate with a banner of chequered wool
    for xx in (x - 3, x + 3):
        bb.fill(xx, 2, zs, xx, 9, zs, "minecraft:stripped_spruce_log[axis=y]")
    for xx in range(x - 3, x + 4):
        bb.set(xx, 10, zs, "minecraft:white_wool" if xx % 2 else "minecraft:black_wool")
        bb.set(xx, 9, zs, "minecraft:black_wool" if xx % 2 else "minecraft:white_wool")
    # three barrel-boats (the Cutie Wagon style tubs) on each side of the pier
    for i, z in enumerate((zs + 3, zs + 8, zs + 13)):
        for side in (-1, 1):
            bx = x + side * 5
            bb.fill(bx - 1, -1, z - 1, bx + 1, 0, z + 1, "minecraft:spruce_planks")
            bb.fill(bx - 1, 1, z - 1, bx + 1, 1, z + 1, "minecraft:spruce_fence")
            bb.set(bx, 1, z, "minecraft:barrel[facing=up,open=false]")
            bb.set(bx, 0, z, "minecraft:spruce_planks")
            bb.fill(bx, 2, z, bx, 5, z, "minecraft:spruce_fence")
            bb.set(bx, 6, z, ("minecraft:red_wool", "minecraft:yellow_wool", "minecraft:blue_wool")[i])
    return x, zs


def long_trees(bb, rng, taken):
    """Long Ring Long Land's stretched trees: very tall straight trunks with small round crowns."""
    k = 0
    for _ in range(6000):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        X, Z = np.array([x]), np.array([z])
        if not land(X, Z)[0] or sh(X, Z)[0] < 9 or paths(X, Z)[0] or math.hypot(x - C, z - C) < FIELD + 8:
            continue
        if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken):
            continue
        y = hy(x, z) + 1
        h = int(rng.integers(18, 30))
        wood = ("birch", "jungle", "oak")[k % 3]
        bb.fill(x, y, z, x, y + h, z, f"minecraft:{wood}_log[axis=y]")
        r = float(rng.uniform(2.4, 3.6))
        leaves = f"minecraft:{wood}_leaves[persistent=true]"
        bb.fill_where(x - 4, y + h - 2, z - 4, x + 4, y + h + 4, z + 4,
                      lambda X, Y, Z: ((X - x) ** 2 + ((Y - (y + h + 1)) * 1.3) ** 2 + (Z - z) ** 2 <= r * r), leaves, only_empty=True)
        taken.append((x - 3, z - 3, x + 3, z + 3))
        k += 1
        if k >= 55:
            break
    print("trees:", k)


def design():
    bb = BigBuild(seed=5510, y_min=-14, y_max=70)
    tracker = P.PropTracker(5510)
    audit = []
    rng = np.random.default_rng(5510)
    terrain(bb)
    field(bb)
    taken = [(C - FIELD - 4, C - FIELD - 4, C + FIELD + 4, C + FIELD + 4)]
    grandstand(bb, C - 24, C + 12, C - FIELD - 6, "south")
    grandstand(bb, C - 26, C + 2, C + FIELD + 6, "north")
    taken.append(command_tent(bb, tracker, audit))
    taken.append(boxing_ring(bb, C + 28, C - 46))
    midway(bb, rng, taken)
    for i, (x, z) in enumerate(((C - 40, C - 52), (C - 28, C - 60), (C - 14, C - 64), (C + 8, C - 66), (C - 52, C + 40),
                                (C - 40, C + 50), (C - 26, C + 56))):
        if land(np.array([x - 4, x + 4]), np.array([z - 4, z + 6])).all():
            taken.append(crew_tent(bb, x, z, rng, i))
    px, pz = pier(bb, rng)
    taken.append((px - 8, pz - 6, px + 56, N))
    long_trees(bb, rng, taken)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 5590, density=0.32, kinds=["minecraft:tall_grass", "minecraft:short_grass",
                                                                          "minecraft:tall_grass", "minecraft:large_fern"],
              flowers=NT.FLOWERS,
              mask=lambda X, Z: land(X, Z) & (sh(X, Z) >= 7) & ~paths(X, Z) & (np.hypot(np.asarray(X) - C, np.asarray(Z) - C) > FIELD + 6))
    return bb, audit


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    px = C + 8
    zs = next(z for z in range(C + 40, N) if not land(np.array([px]), np.array([z]))[0])
    FX.place(b, px + 10, zs + 14)
    x1, z1, x2, z2 = TENT
    b.chest(x1 - 3, TY + 1, z1 + 4, "medium", "east")
    b.chest(x1 + 3, TY + 3, (z1 + z2) // 2 + 2, "easy", "east")
    b.guards("rookie_pirate", ((C - 30, C - 40), (C + 30, C - 40), (C - 34, C + 30), (C + 22, C + 50)), y=TY + 1)
    b.guards("pirate", ((x2 + 3, (z1 + z2) // 2 + 5), (x2 + 3, (z1 + z2) // 2 - 5)), y=TY + 1)
    return b, 0
