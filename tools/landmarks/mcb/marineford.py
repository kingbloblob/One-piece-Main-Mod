"""Marineford, Marine Headquarters, redesigned with the Minecraft Builder skill (dossier: mcb/dossiers/marineford.md).

A crescent island round a bay that opens south. At the back the stepped white HQ fortress: four tiers under blue
castle eaves, a two-storey castle keep with gold ridge fish on top, the big 海 [gull] 軍 sign on its face and the gull
over the main gate. Every floor is real (offices, barracks, mess, libraries, armories, the war room, the Fleet
Admiral's office in the keep), linked by two spiral stair towers and a keep stair. In front: the high scaffold wall
with the admirals' seats and the execution tower; Oris Plaza with the Ox Bell; the raised Encircling Wall with
cannons in the bay; docked battleships; a town of Marine family houses on both arms; barracks with training yards
and watchtowers at the bay mouth. 220 x 220, keep ridge ~108. Ground = y 0. (v2, 2026-10-29)"""
import math
import numpy as np
from mcb.kit import (BigBuild, P, AIR, seed_of, st, wing_floor, furnish, house_module, place_house, lamp_post,
                     table, glyph, castle_eave, window_grid, marine_battleship, set_if_air)
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.shipstamp import stamp_ship

SID = "marineford"
TITLE = "Marineford (Marine Headquarters)"
CUTS = [8, 20, 40]
TILER = dict(terrain="beard_thin")
EDGE_REACH = 2
SOFT_EDGES = False                          # v3: the site is an island in open sea, edges are designed

# ---------------------------------------------------------------- palette roles
WHITE = "onepiece:marine_bricks"
WHITE_ST = "onepiece:marine_brick_stairs"
WHITE_SL = "onepiece:marine_brick_slab"
WHITE_W = "onepiece:marine_brick_wall"
WALLMIX = ["onepiece:marine_bricks", "minecraft:white_concrete", "minecraft:smooth_quartz"]
TILE = "onepiece:marine_tiles"
TILE_ST = "onepiece:marine_tile_stairs"
PIL = "onepiece:marine_pillar[axis=y]"
BLUE = "minecraft:blue_terracotta"
ROOF = "onepiece:wano_roof_tiles"
ROOF_ST = "onepiece:wano_roof_tile_stairs"
ROOF_SL = "onepiece:wano_roof_tile_slab"
PLINTH = "minecraft:polished_andesite"
PAVE = ["minecraft:polished_andesite", "minecraft:andesite", "minecraft:stone_bricks"]
GLASS = "minecraft:light_blue_stained_glass_pane"
WATER = "minecraft:water[level=0]"
STEEL = "minecraft:light_gray_concrete"
INNER = "minecraft:white_concrete"          # partition walls inside the HQ

# ---------------------------------------------------------------- layout
N = 220
CX = 110
BAY_C, BAY_R = (110, 164), 62              # v3: a full round bay inside the crescent, opening south
SEA = -3                                    # sea / bay surface (the island's paving is 3 above it)
FLOOR = -15                                 # bay and sea floor
FH = 6                                      # storey: 5 clear + floor plate
# HQ tiers: (half width, z1, z2, base plate y, storeys)
TIERS = [(56, 4, 70, 0, 4), (44, 10, 64, 24, 4), (31, 16, 58, 48, 3), (19, 22, 52, 66, 2)]
KEEP = (12, 27, 47, 78, 2)                  # castle keep lower storeys (plates 78, 84; top 90)
KEEP_TOP = (8, 31, 43, 90)                  # upper keep: walls 91..97, roof from 98
HALL = (CX - 12, CX + 12)                   # the great hall (x) on the ground floor, two storeys tall
CORES = [(82, 22), (132, 22)]               # spiral stair towers (north-west corner, size 7), y 1 -> 66
CORE_C = (113, 34)                          # keep stair (size 5), y 67 -> 90
SW = (80, 140, 76, 88, 17)                 # scaffold wall x1, x2, z1, z2, top block y
TW = (105, 115, 79, 87)                     # execution tower
TT = 60                                     # tower top
BELL = (54, 108)


def in_bay(x, z, pad=0):
    return math.hypot(x - BAY_C[0], z - BAY_C[1]) <= BAY_R + pad


# ---------------------------------------------------------------- ground, bay, quay
_ISLE = NT.outline(110, 110, 100, 5911, wobble=0.07, lobes=((3, 0.03), (5, 0.03), (9, 0.02)))
_HQ_BOX = (CX - 60, 0, CX + 60, 74)          # the HQ's back wall is the island's north sea wall


def _squircle(X, Z):
    """The island before the bay is cut out: a rounded, slightly wobbly squircle (keeps the HQ corners on land)."""
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    w = 1 + 0.05 * (NT.noise(X, Z, 5912, 17) - 0.5) + 0.03 * (NT.noise(X, Z, 5913, 6) - 0.5)
    d = ((np.abs(X - CX) / 100) ** 6 + (np.abs(Z - 108) / (104 if True else 0)) ** 6) ** (1 / 6)
    return d * w <= 1.0


def land(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    hq = (X >= _HQ_BOX[0]) & (X <= _HQ_BOX[2]) & (Z >= 3) & (Z <= _HQ_BOX[3])
    return (_squircle(X, Z) | hq) & (np.hypot(X - BAY_C[0], Z - BAY_C[1]) > BAY_R + 1.5) & (X >= 4) & (X <= N - 5) & (Z >= 3) & (Z <= N - 6)


def on_land(x1, z1, x2, z2, pad=2):
    xs = np.array([x1 - pad, x2 + pad, x1 - pad, x2 + pad, (x1 + x2) / 2]); zs = np.array([z1 - pad, z1 - pad, z2 + pad, z2 + pad, (z1 + z2) / 2])
    return bool(land(xs, zs).all())


def ground(bb):
    """A crescent island: paved plateau 3 above the sea, ringed by a white sea wall, the round bay cut into its
    south side and opening to the sea. Everything outside the island is open sea to the site edge."""
    L = lambda X, y, Z: land(X, Z)
    # the open sea is only written inside a wobbly round rim, and its floor rises to the natural sea floor there,
    # so no square of deep water shows round the island
    rr = lambda X, Z: np.hypot(X - CX, Z - (N - 1) / 2) / (104 + 5 * NT.noise(X, Z, 5907, 24))
    floor = lambda X, Z: np.where(land(X, Z) | (np.hypot(X - BAY_C[0], Z - BAY_C[1]) < BAY_R), FLOOR,
                                  FLOOR + np.clip((rr(X, Z) - 0.78) / 0.22, 0, 1) * 6).astype(int)
    rim = lambda X, Z: land(X, Z) | (rr(X, Z) < 1)
    sea = lambda X, y, Z: ~land(X, Z) & rim(X, Z) & (y > floor(X, Z))
    bb.fill_where(0, FLOOR - 2, 0, N - 1, FLOOR + 6, N - 1, lambda X, y, Z: rim(X, Z) & (y <= floor(X, Z)), "minecraft:stone")
    bb.fill_where(0, FLOOR + 1, 0, N - 1, FLOOR + 7, N - 1, lambda X, y, Z: ~land(X, Z) & rim(X, Z) & (y == floor(X, Z)), "minecraft:sand")
    bb.fill_where(0, FLOOR - 2, 0, N - 1, -1, N - 1, L, "minecraft:stone")
    bb.mix(0, 0, 0, N - 1, 0, N - 1, PAVE, [0.6, 0.25, 0.15])
    bb.fill_where(0, 0, 0, N - 1, 0, N - 1, lambda X, y, Z: ~land(X, Z), AIR)
    # Oris Plaza: a big checker of diorite and andesite between the scaffold wall and the bay
    bb.fill_where(0, 0, 88, N - 1, 0, N - 1,
                  lambda X, y, Z: ((X // 4 + Z // 4) % 2 == 0) & (np.abs(X - CX) < 72) & land(X, Z), "minecraft:polished_diorite")
    bb.fill_where(0, FLOOR - 1, 0, N - 1, SEA, N - 1, sea, WATER)
    # sea wall: two blocks of white brick round the whole shore, a pillared balustrade on the bay side, a low wall outside
    edge = lambda X, Z: land(X, Z) & ~(land(X - 2, Z) & land(X + 2, Z) & land(X, Z - 2) & land(X, Z + 2))
    bb.fill_where(0, FLOOR + 1, 0, N - 1, 0, N - 1, lambda X, y, Z: edge(X, Z), WHITE)
    bb.fill_where(0, SEA + 1, 0, N - 1, SEA + 1, N - 1, lambda X, y, Z: edge(X, Z), BLUE)      # blue waterline band
    bb.fill_where(0, 1, 0, N - 1, 1, N - 1, lambda X, y, Z: edge(X, Z) & ~(np.hypot(X - BAY_C[0], Z - BAY_C[1]) < BAY_R + 4), WHITE_W)
    ring = lambda X, y, Z: edge(X, Z) & (np.hypot(X - BAY_C[0], Z - BAY_C[1]) < BAY_R + 4)
    bb.fill_where(0, 1, 0, N - 1, 1, N - 1, ring, WHITE_W)
    for a in range(-170, 171, 6):
        t = math.radians(a)
        x = round(BAY_C[0] + (BAY_R + 2) * math.sin(t)); z = round(BAY_C[1] - (BAY_R + 2) * math.cos(t))
        if 0 <= x < N and z < N - 6 and land(np.array([x]), np.array([z]))[0]:
            bb.fill(x, 1, z, x, 2, z, PIL)
            bb.set(x, 3, z, "minecraft:lantern[hanging=false]")
    # the bay floor is deeper (warships anchor there) and lit by sea lanterns along the encircling wall's foot
    bb.fill_where(0, FLOOR + 1, 90, N - 1, FLOOR + 1, N - 1, lambda X, y, Z: (np.abs(np.hypot(X - BAY_C[0], Z - BAY_C[1]) - (BAY_R - 9)) < 0.6)
                  & ((X + Z) % 9 == 0), "minecraft:sea_lantern")


def encircling_wall(bb):
    """Steel panels risen from the bay edge, iron bands, cannon windows near the top, gaps between the panels."""
    for a10 in range(-1400, 1401, 3):
        a = a10 / 10.0
        if (a10 // 3) % 70 in (0, 1, 2, 3):
            continue                                     # the gaps between panels
        t = math.radians(a)
        for r in (BAY_R - 3, BAY_R - 4, BAY_R - 5):
            x = round(BAY_C[0] + r * math.sin(t)); z = round(BAY_C[1] - r * math.cos(t))
            if not (0 <= x < N and 0 <= z < N) or abs(x - 70) <= 3 or abs(x - 150) <= 3:
                continue
            bb.fill(x, FLOOR + 1, z, x, 18, z, STEEL)
            for y in (SEA, 9, 18):
                bb.set(x, y, z, "minecraft:iron_block")
        x = round(BAY_C[0] + (BAY_R - 3) * math.sin(t)); z = round(BAY_C[1] - (BAY_R - 3) * math.cos(t))
        if 0 <= x < N and 0 <= z < N and (a10 // 3) % 8 == 4:
            bb.set(x, 14, z, "minecraft:black_concrete")      # gun port
            xi = round(BAY_C[0] + (BAY_R - 4) * math.sin(t)); zi = round(BAY_C[1] - (BAY_R - 4) * math.cos(t))
            if (a10 // 3) % 16 == 4:
                bb.set(xi, 19, zi, "onepiece:cannon[facing=south]")


def pier(bb, x, z1, z2):
    """A wooden pier from the quay out into the bay, on log piles, with bollards and lanterns."""
    bb.fill(x - 2, 0, z1, x + 2, 0, z2, "minecraft:spruce_planks")
    for z in range(z1, z2 + 1, 4):
        for dx in (-2, 2):
            bb.fill(x + dx, FLOOR + 1, z, x + dx, -1, z, "minecraft:spruce_log[axis=y]")
            bb.set(x + dx, 1, z, "minecraft:spruce_fence")
        if (z - z1) % 8 == 0:
            bb.set(x - 2, 2, z, "minecraft:lantern[hanging=false]")
    for (dx, dz) in ((-1, 1), (1, 3), (0, 6)):
        bb.set(x + dx, 1, z1 + dz, "minecraft:barrel[facing=up]")
    bb.set(x + 1, 1, z2 - 2, "onepiece:crate_stack[facing=east]")


# ---------------------------------------------------------------- HQ
def tier_box(bb, hw, z1, z2, y0, n, last):
    """One tier: plinth, walls with pilasters and blue floor bands, windows on every storey, floor plates, a tiled
    terrace on top and a castle eave round its wall top."""
    x1, x2 = CX - hw, CX + hw
    top = y0 + FH * n
    bb.fill(x1, y0, z1, x2, y0, z2, TILE)
    bb.mix(x1, y0 + 1, z1, x2, top - 1, z2, WALLMIX, [0.75, 0.15, 0.10])
    bb.fill(x1 + 1, y0 + 1, z1 + 1, x2 - 1, top - 1, z2 - 1, AIR)
    for k in range(1, n + 1):
        bb.fill(x1 + 1, y0 + FH * k, z1 + 1, x2 - 1, y0 + FH * k, z2 - 1, "minecraft:smooth_stone" if k < n else TILE)
    for k in range(1, n):
        y = y0 + FH * k
        bb.fill(x1, y, z1, x2, y, z1, BLUE); bb.fill(x1, y, z2, x2, y, z2, BLUE)
        bb.fill(x1, y, z1, x1, y, z2, BLUE); bb.fill(x2, y, z1, x2, y, z2, BLUE)
    # windows: 2 tall, every 3, glass + sills
    for k in range(n):
        wy = y0 + FH * k + 2
        for x in range(x1 + 2, x2 - 1, 3):
            if (x - CX) % 8 == 0:
                continue
            for z, out in ((z1, -1), (z2, 1)):
                bb.fill(x, wy, z, x, wy + 1, z, GLASS)
                bb.set(x, wy - 1, z + out, st(WHITE_ST, "south" if out < 0 else "north", "top"))
        for z in range(z1 + 2, z2 - 1, 3):
            if (z - z1) % 8 == 0:
                continue
            for x, out in ((x1, -1), (x2, 1)):
                bb.fill(x, wy, z, x, wy + 1, z, GLASS)
                bb.set(x + out, wy - 1, z, st(WHITE_ST, "east" if out < 0 else "west", "top"))
    # pilasters standing proud of the wall every 8
    for x in range(x1, x2 + 1, 8):
        for z, out in ((z1, -1), (z2, 1)):
            bb.fill(x, y0 + 1, z + out, x, top - 1, z + out, PIL)
    for z in range(z1, z2 + 1, 8):
        for x, out in ((x1, -1), (x2, 1)):
            bb.fill(x + out, y0 + 1, z, x + out, top - 1, z, PIL)
    castle_eave(bb, x1 - 1, z1 - 1, x2 + 1, z2 + 1, top - 1, ROOF_ST, ROOF, depth=3, bracket=WHITE_ST)
    bb.fill(x1, top, z1, x2, top, z2, TILE)
    return top


def core_ring(bb, x, z, size, y1, y2, floors):
    """A stair tower: wall ring round a size x size square spiral, opened on every floor where the stair arrives."""
    bb.fill(x - 1, y1, z - 1, x + size, y2 + 3, z + size, WHITE)
    bb.fill(x, y1, z, x + size - 1, y2 + 3, z + size - 1, AIR)
    P.square_spiral_stair(bb, x, y1, z, size, y2, WHITE_ST, core=WHITE, support=None, headroom=3)
    x2, z2 = x + size - 1, z + size - 1
    cells = [(xx, z) for xx in range(x, x2)] + [(x2, zz) for zz in range(z, z2)] \
        + [(xx, z2) for xx in range(x2, x, -1)] + [(x, zz) for zz in range(z2, z, -1)]
    for fy in floors:                     # fy = the floor's first air layer
        n = fy - 1 - y1                   # the step whose top is level with this floor
        if n < 0:
            continue
        cx, cz = cells[n % len(cells)]
        # open the ring wall beside that step, plus the next cell along, to the outside
        for (ox, oz) in ((cx - 1, cz), (cx + 1, cz), (cx, cz - 1), (cx, cz + 1)):
            if ox in (x - 1, x + size) or oz in (z - 1, z + size):
                bb.fill(ox, fy, oz, ox, fy + 2, oz, AIR)
                bb.set(ox, fy - 1, oz, WHITE)
        bb.set(cx, fy + 2, cz, AIR)
    for y in range(y1 + 3, y2, 5):
        bb.set(x + size // 2, y, z - 1, "minecraft:light_blue_stained_glass")
    return cells


def great_hall(bb, tracker, audit):
    """Ground floor centre: two storeys, rows of pillars, blue carpet runner, banners, a reception desk and the
    Marine gull mosaic on the far wall. Mess hall above (y 13) and the HQ library above that (y 19)."""
    x1, x2 = HALL
    z1, z2 = 5, 69
    bb.fill(x1, 6, z1, x2, 6, z2, AIR)                     # no floor plate at 6: double height
    bb.fill(x1 - 1, 1, z1, x1 - 1, 11, z2, WHITE); bb.fill(x2 + 1, 1, z1, x2 + 1, 11, z2, WHITE)
    for z in range(z1 + 6, z2 - 3, 8):                     # arches into the wings
        for y in (1, 7):
            P.arched_opening(bb, "z", z, y, x1 - 1, 3, 4, depth=1)
            P.arched_opening(bb, "z", z, y, x2 + 1, 3, 4, depth=1)
    bb.fill(CX - 2, 0, z1, CX + 2, 0, z2, "minecraft:blue_concrete")
    bb.fill(CX - 1, 1, z1 + 4, CX + 1, 1, z2 - 1, "minecraft:blue_carpet")
    for z in range(z1 + 4, z2 - 1, 8):
        for x in (x1 + 3, x2 - 3):
            bb.fill(x, 1, z, x, 10, z, PIL)
            bb.set(x, 11, z, WHITE)
        bb.set(CX, 10, z, "onepiece:chandelier[facing=north]")
    # balconies along both sides at the first floor, with railings
    for (a, b) in ((x1, x1 + 1), (x2 - 1, x2)):
        bb.fill(a, 6, z1, b, 6, z2, "minecraft:smooth_stone")
        rail = x1 + 2 if a == x1 else x2 - 2
        bb.fill(rail, 7, z1, rail, 7, z2, "minecraft:white_stained_glass_pane")
    # reception desk and the gull mosaic at the north end
    bb.fill(CX - 6, 1, z1 + 2, CX + 6, 1, z1 + 2, "minecraft:polished_diorite")
    bb.fill(CX - 6, 2, z1 + 2, CX + 6, 2, z1 + 2, "minecraft:white_carpet")
    bb.set(CX, 1, z1 + 1, "onepiece:captains_chair[facing=south]")
    bb.set(CX - 4, 3, z1 + 2, "onepiece:globe[facing=south]")
    bb.fill(CX - 10, 2, z1, CX + 10, 11, z1, "minecraft:white_concrete")
    glyph(bb, GULL, CX - 9, 10, z1, "minecraft:blue_concrete")
    for x in (CX - 9, CX + 9):
        bb.set(x, 1, z1 + 1, "minecraft:potted_azalea_bush")
    for z in (20, 40, 60):
        for x in (x1 + 1, x2 - 1):
            bb.set(x, 1, z, "minecraft:potted_fern")
    # mess hall above (floor at 12) and library (floor at 18): big rooms furnished as one
    furnish(bb, [(x1, z1, x2, z2)], 13, 5, ["kitchen"], seed_of("mess"), tracker, audit=audit)
    for z in range(z1 + 4, z2 - 3, 6):
        table(bb, CX - 6, 13, z, "minecraft:blue_carpet")
        table(bb, CX + 6, 13, z, "minecraft:blue_carpet")
    furnish(bb, [(x1, z1, x2, z2)], 19, 5, ["library"], seed_of("hqlib"), tracker, audit=audit)


def war_room(bb, tracker, audit):
    """T3 ground floor (y 67): the war room, a long map table with chairs, den den mushi, maps on the walls."""
    hw, z1, z2, y0, n = TIERS[3]
    x1, x2 = CX - hw + 1, CX + hw - 1
    y = y0 + 1
    bb.fill(CX - 10, y, 44, CX + 10, y, 47, "minecraft:dark_oak_planks")
    bb.fill(CX - 10, y + 1, 44, CX + 10, y + 1, 47, "minecraft:blue_carpet")
    for x in range(CX - 9, CX + 10, 3):
        bb.set(x, y, 43, "minecraft:dark_oak_stairs[facing=south,half=bottom]")
        bb.set(x, y, 48, "minecraft:dark_oak_stairs[facing=north,half=bottom]")
    bb.set(CX - 11, y, 45, "onepiece:captains_chair[facing=east]")
    bb.set(CX - 4, y + 2, 45, "onepiece:globe[facing=south]")
    bb.set(CX + 5, y + 2, 46, "minecraft:lantern[hanging=false]")
    for x in range(x1 + 2, x2 - 1, 4):
        if x % 8 == 0:
            bb.set(x, y, z1 + 1, "onepiece:navigators_desk[facing=south]")
    furnish(bb, [(x1, z1 + 1, CX - 13, z2 - 1), (CX + 13, z1 + 1, x2, z2 - 1)], y, 5, ["library", "workshop"],
            seed_of("war"), tracker, audit=audit)
    for x in (CX - 6, CX + 6):
        bb.set(x, y + 4, 45, "onepiece:chandelier[facing=north]")


def keep(bb, tracker, audit):
    hw, z1, z2, y0, n = KEEP
    top = tier_box(bb, hw, z1, z2, y0, n, False)
    # lower keep: trophy hall (y 79) and the admirals' lounge (y 85)
    x1, x2 = CX - hw + 1, CX + hw - 1
    furnish(bb, [(x1, z1 + 1, x2, z2 - 1)], y0 + 1, 5, ["living"], seed_of("trophy"), tracker, audit=audit)
    furnish(bb, [(x1, z1 + 1, x2, z2 - 1)], y0 + 7, 5, ["library"], seed_of("lounge"), tracker, audit=audit)
    # upper keep: the Fleet Admiral's office
    hw2, a1, a2, b0 = KEEP_TOP
    u1, u2 = CX - hw2, CX + hw2
    bb.fill(u1, b0, a1, u2, b0, a2, TILE)
    bb.mix(u1, b0 + 1, a1, u2, b0 + 7, a2, WALLMIX, [0.75, 0.15, 0.10])
    bb.fill(u1 + 1, b0 + 1, a1 + 1, u2 - 1, b0 + 7, a2 - 1, AIR)
    for (x, z) in ((u1, a1), (u2, a1), (u1, a2), (u2, a2)):
        bb.fill(x, b0 + 1, z, x, b0 + 7, z, PIL)
    for x in range(u1 + 2, u2 - 1, 3):
        bb.fill(x, b0 + 3, a1, x, b0 + 5, a1, GLASS); bb.fill(x, b0 + 3, a2, x, b0 + 5, a2, GLASS)
    for z in range(a1 + 2, a2 - 1, 3):
        bb.fill(u1, b0 + 3, z, u1, b0 + 5, z, GLASS); bb.fill(u2, b0 + 3, z, u2, b0 + 5, z, GLASS)
    # the balcony walk round the upper keep on the lower keep's roof
    bb.fill(CX - hw, top + 1, z1, CX + hw, top + 1, z1, WHITE_W); bb.fill(CX - hw, top + 1, z2, CX + hw, top + 1, z2, WHITE_W)
    bb.fill(CX - hw, top + 1, z1, CX - hw, top + 1, z2, WHITE_W); bb.fill(CX + hw, top + 1, z1, CX + hw, top + 1, z2, WHITE_W)
    bb.fill(CX - 1, b0 + 1, a2, CX + 1, b0 + 3, a2, AIR)
    bb.set(CX, b0 + 1, a2, "minecraft:dark_oak_door[facing=south,half=lower,hinge=left,open=false]")
    bb.set(CX, b0 + 2, a2, "minecraft:dark_oak_door[facing=south,half=upper,hinge=left,open=false]")
    bb.fill(CX - 1, b0 + 1, a2, CX - 1, b0 + 3, a2, PIL); bb.fill(CX + 1, b0 + 1, a2, CX + 1, b0 + 3, a2, PIL)
    oy = b0 + 1
    bb.fill(CX - 3, oy, a1 + 4, CX + 3, oy, a1 + 4, "minecraft:dark_oak_planks")      # the big desk
    bb.fill(CX - 3, oy + 1, a1 + 4, CX + 3, oy + 1, a1 + 4, "minecraft:dark_oak_slab[type=bottom]")
    bb.set(CX, oy, a1 + 2, "onepiece:captains_chair[facing=south]")
    bb.set(CX - 2, oy + 1, a1 + 4, "minecraft:lantern[hanging=false]")
    bb.fill(u1 + 1, oy, a1 + 1, u1 + 1, oy + 3, a1 + 6, "minecraft:bookshelf")
    bb.fill(u2 - 1, oy, a1 + 1, u2 - 1, oy + 3, a1 + 6, "minecraft:bookshelf")
    bb.set(u2 - 2, oy, a2 - 2, "onepiece:globe[facing=west]")
    bb.set(u1 + 2, oy, a2 - 2, "minecraft:potted_bamboo")
    bb.fill(CX - 2, oy - 1, a1 + 6, CX + 2, oy - 1, a2 - 3, "minecraft:blue_wool")
    bb.set(CX, oy + 5, (a1 + a2) // 2, "onepiece:chandelier[facing=north]")
    # castle roof: hip roof with deep overhang, gold ridge fish on both ends
    P.hip_roof(bb, u1, a1, u2, a2, b0 + 8, ROOF_ST, overhang=3)
    half = (a2 - a1 + 6) // 2
    ridge = b0 + 8 + half
    for x in (u1 - 3 + half, u2 + 3 - half):          # the golden shachihoko at both ends of the ridge
        bb.fill(x, ridge, (a1 + a2) // 2, x, ridge + 2, (a1 + a2) // 2, "minecraft:gold_block")
    return ridge


# Marine gull emblem and 海 / 軍
KAI = (".#...#.......",
       "..#.#........",
       "....#########",
       "...#.........",
       "#...#######..",
       ".#..#.....#..",
       "....#..#..#..",
       "...##########",
       "....#.....#..",
       "..#.#..#..#..",
       ".#..#######..",
       "#.........#..",
       "#........##..")
GUN = ("#############",
       "#...........#",
       "#...........#",
       "..#########..",
       "......#......",
       "...#######...",
       "...#..#..#...",
       "...#######...",
       "...#..#..#...",
       "...#######...",
       "......#......",
       ".###########.",
       "......#......")
GULL = ("#.................#",
        "##...............##",
        ".###.....#.....###.",
        "..####..###..####..",
        "...#############...",
        ".....#########.....",
        ".......#####.......",
        "........###........",
        ".......#.#.#.......")


def big(rows, k):
    """Scale a pixel picture up k times."""
    return tuple("".join(ch * k for ch in r) for r in rows for _ in range(k))


def hq(bb, tracker, audit):
    tops = []
    for i, (hw, z1, z2, y0, n) in enumerate(TIERS):
        tops.append(tier_box(bb, hw, z1, z2, y0, n, i == len(TIERS) - 1))
    # ---- T0 wings, 4 floors: armory + stores, offices, barracks, officers
    hw, z1, z2, y0, n = TIERS[0]
    kinds = [["storage", "workshop"], ["living", "library"], ["bedroom", "bedroom", "living"], ["bedroom", "library"]]
    keep_out = [(c[0] - 1, c[1] - 1, c[0] + 7, c[1] + 7) for c in CORES]
    for k in range(n):
        y = y0 + FH * k + 1
        for (a, b2) in ((CX - hw + 1, HALL[0] - 2), (HALL[1] + 2, CX + hw - 1)):
            wing_floor(bb, a, z1 + 1, b2, z2 - 1, y, FH - 1, INNER, seed_of("t0", k, a), tracker, kinds[k],
                       corridor="z", cw=3, carpet=("minecraft:polished_andesite", "minecraft:blue_carpet"),
                       keep=keep_out, audit=audit)
    great_hall(bb, tracker, audit)
    # ---- T1 and T2: office floors with an x corridor
    for t, kinds in ((1, [["living", "library"], ["bedroom", "living"], ["library", "workshop"], ["bedroom", "storage"]]),
                     (2, [["living", "library"], ["workshop", "living"], ["bedroom", "library"]])):
        hw, z1, z2, y0, n = TIERS[t]
        for k in range(n):
            y = y0 + FH * k + 1
            wing_floor(bb, CX - hw + 1, z1 + 1, CX + hw - 1, z2 - 1, y, FH - 1, INNER, seed_of("t", t, k), tracker,
                       kinds[k], corridor="x", cw=3, carpet=("minecraft:polished_andesite", "minecraft:blue_carpet"),
                       keep=keep_out, audit=audit)
    # ---- T3: war room, then offices
    war_room(bb, tracker, audit)
    hw, z1, z2, y0, n = TIERS[3]
    wing_floor(bb, CX - hw + 1, z1 + 1, CX + hw - 1, z2 - 1, y0 + FH + 1, FH - 1, INNER, seed_of("t3"), tracker,
               ["living", "library"], corridor="z", keep=[(CORE_C[0] - 1, CORE_C[1] - 1, CORE_C[0] + 5, CORE_C[1] + 5)],
               audit=audit)
    ridge = keep(bb, tracker, audit)
    # ---- stair towers
    floors = [y0 + FH * k + 1 for (hw, z1, z2, y0, n) in TIERS[:3] for k in range(n + 1)]
    for (x, z) in CORES:
        core_ring(bb, x, z, 7, 1, 66, sorted(set(floors)))
        bb.fill(x - 1, 67, z - 1, x + 7, 70, z + 7, WHITE)        # stair hut on the T2 terrace
        bb.fill(x, 67, z, x + 6, 69, z + 6, AIR)
        bb.fill(x + 3, 67, z + 7, x + 3, 68, z + 7, AIR)
        P.hip_roof(bb, x - 1, z - 1, x + 7, z + 7, 71, ROOF_ST, overhang=1)
    core_ring(bb, CORE_C[0], CORE_C[1], 5, 67, 90, [73, 79, 85, 91])
    # doors from the T2 terrace into T3 (east and west)
    hw, z1, z2, y0, n = TIERS[3]
    for x in (CX - hw, CX + hw):
        bb.fill(x, 67, 36, x, 68, 37, AIR)
    # ---- the sign: 海 [gull] 軍 on the face of T1, the gull over the main gate
    hw, z1, z2, y0, n = TIERS[1]
    zf = z2 + 1
    bb.fill(CX - 42, 25, zf, CX + 42, 54, zf, "minecraft:white_concrete")
    bb.fill(CX - 43, 24, zf, CX + 43, 24, zf, BLUE); bb.fill(CX - 43, 55, zf, CX + 43, 55, zf, BLUE)
    bb.fill(CX - 43, 24, zf, CX - 43, 55, zf, BLUE); bb.fill(CX + 43, 24, zf, CX + 43, 55, zf, BLUE)
    bb.fill(CX - 42, 25, zf - 1, CX + 42, 54, zf - 1, WHITE)            # backing, so the eave doesn't show through
    glyph(bb, big(KAI, 2), CX - 40, 52, zf + 1, "minecraft:black_concrete")
    glyph(bb, big(GUN, 2), CX + 15, 52, zf + 1, "minecraft:black_concrete")
    glyph(bb, GULL, CX - 9, 44, zf + 1, "minecraft:blue_concrete")
    # main gate: a tall arch, double doors, a pillared porch with a castle roof, the gull above
    hw, z1, z2, y0, n = TIERS[0]
    P.arched_opening(bb, "x", CX, 1, z2, 9, 11, depth=1, trim=PIL)
    for x, hinge in ((CX - 1, "left"), (CX, "right")):
        bb.set(x, 1, z2, f"minecraft:dark_oak_door[facing=south,half=lower,hinge={hinge},open=false]")
        bb.set(x, 2, z2, f"minecraft:dark_oak_door[facing=south,half=upper,hinge={hinge},open=false]")
    glyph(bb, GULL, CX - 9, 23, z2, "minecraft:blue_concrete")
    for x in (CX - 14, CX - 8, CX + 8, CX + 14):
        bb.fill(x, 1, z2 + 5, x, 12, z2 + 5, PIL)
        bb.set(x, 0, z2 + 5, WHITE)
    bb.fill(CX - 15, 13, z2 + 1, CX + 15, 13, z2 + 6, WHITE)
    castle_eave(bb, CX - 15, z2 + 1, CX + 15, z2 + 6, 12, ROOF_ST, ROOF, depth=2)
    P.hip_roof(bb, CX - 15, z2 + 1, CX + 15, z2 + 6, 14, ROOF_ST, overhang=0)
    for x in (CX - 4, CX + 4):
        bb.set(x, 12, z2 + 3, "minecraft:lantern[hanging=true]")
    bb.fill(CX - 5, 0, z2 + 1, CX + 5, 0, z2 + 10, "minecraft:blue_concrete")
    for x in (CX - 11, CX + 11):
        bb.set(x, 1, z2 + 3, "minecraft:potted_azalea_bush")
    return ridge


# ---------------------------------------------------------------- scaffold wall and execution tower
def scaffold(bb, tracker, audit):
    x1, x2, z1, z2, top = SW
    bb.fill(x1, 0, z1, x2, top, z2, WHITE)
    bb.fill(x1 + 1, 1, z1 + 1, x2 - 1, top - 1, z2 - 1, AIR)
    bb.fill(x1 + 1, 9, z1 + 1, x2 - 1, 9, z2 - 1, "minecraft:smooth_stone")
    bb.fill(x1, top, z1, x2, top, z2, TILE)
    # guard rooms on two floors inside the wall
    for (y, h) in ((1, 8), (10, 7)):
        wing_floor(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, y, h, INNER, seed_of("sw", y), tracker,
                   ["storage", "bedroom", "workshop"], corridor="x", cw=3, audit=audit,
                   keep=[(TW[0] - 1, TW[2] - 1, TW[1] + 1, TW[3] + 1)])
    for x in (CX - 8, CX + 8):                                      # doors in the back of the wall
        bb.fill(x, 1, z1, x + 1, 3, z1, AIR)
    bb.fill(x1 + 2, 1, z1 + 1, x1 + 2, 9, z1 + 1, "minecraft:ladder[facing=south]")
    bb.fill(x2 - 2, 1, z1 + 1, x2 - 2, 9, z1 + 1, "minecraft:ladder[facing=south]")
    # the front face: pilasters, blue bands, slit windows
    for x in range(x1, x2 + 1, 5):
        bb.fill(x, 1, z2 + 1, x, top - 1, z2 + 1, PIL)
    for y in (8, top - 1):
        bb.fill(x1, y, z2, x2, y, z2, BLUE)
    for x in range(x1 + 2, x2 - 1, 5):
        bb.fill(x + 1, 3, z2, x + 1, 5, z2, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
        bb.fill(x + 1, 12, z2, x + 1, 14, z2, "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
    # parapet and the three admirals' seats at the front edge
    for (a, b2, c, d) in ((x1, x2, z2, z2), (x1, x2, z1, z1), (x1, x1, z1, z2), (x2, x2, z1, z2)):
        bb.fill(a, top + 1, c, b2, top + 1, d, WHITE_W)
    for x in (CX - 9, CX + 9, CX - 18, CX + 18):
        bb.set(x, top + 1, z2, WHITE)
        bb.set(x, top + 2, z2, "minecraft:lantern[hanging=false]")
    for x in (CX - 8, CX, CX + 8):                                  # the three admirals' seats
        bb.set(x, top + 1, z2 - 1, "onepiece:captains_chair[facing=south]")
    # wide flights up the back of the wall from the courtyard, both sides
    for (sx, d) in ((x1 + 4, "east"), (x2 - 4, "west")):
        P.stair_run(bb, sx, 1, z1 - 3, top, 3, d, WHITE_ST, base_y=0, support=WHITE)
        for i in range(top):
            xx = sx + (i if d == "east" else -i)
            bb.fill(xx, 2 + i, z1 - 3, xx, 4 + i, z1 - 1, AIR)
            bb.fill(xx, 1, z1 - 4, xx, i + 1, z1 - 4, WHITE)
            bb.set(xx, i + 2, z1 - 4, WHITE_W)
        end = sx + (top if d == "east" else -top)
        bb.fill(min(sx, end), top + 1, z1, max(sx, end), top + 1, z1, AIR)
    # ---- the execution tower
    a1, a2, c1, c2 = TW
    bb.fill(a1, top + 1, c1, a2, TT, c2, WHITE)
    bb.fill(a1 + 1, top + 1, c1 + 1, a2 - 1, TT, c2 - 1, AIR)
    for (x, z) in ((a1, c1), (a2, c1), (a1, c2), (a2, c2)):
        bb.fill(x, top + 1, z, x, TT, z, PIL)
    for y in range(top + 6, TT - 2, 5):
        for k in (-2, 2):
            bb.fill(CX + k, y, c1, CX + k, y + 1, c1, GLASS); bb.fill(CX + k, y, c2, CX + k, y + 1, c2, GLASS)
            bb.fill(a1, y, (c1 + c2) // 2 + k, a1, y + 1, (c1 + c2) // 2 + k, GLASS)
            bb.fill(a2, y, (c1 + c2) // 2 + k, a2, y + 1, (c1 + c2) // 2 + k, GLASS)
    for y in (top + 12, top + 25, top + 38):
        bb.fill(a1, y, c1, a2, y, c1, BLUE); bb.fill(a1, y, c2, a2, y, c2, BLUE)
        bb.fill(a1, y, c1, a1, y, c2, BLUE); bb.fill(a2, y, c1, a2, y, c2, BLUE)
    bb.fill(CX, top + 1, c1, CX, top + 3, c1, AIR)                 # door from the wall top (north side)
    bb.set(CX, top + 1, c1, "minecraft:iron_door[facing=north,half=lower,hinge=left,open=false,powered=false]")
    bb.set(CX, top + 2, c1, "minecraft:iron_door[facing=north,half=upper,hinge=left,open=false,powered=false]")
    # the top flares out on stepped corbels into the wide execution floor
    for d, y in ((1, TT - 2), (2, TT - 1), (3, TT)):
        bb.fill(a1 - d, y, c1 - d, a2 + d, y, c1 - d, st(WHITE_ST, "south", "top"))
        bb.fill(a1 - d, y, c2 + d, a2 + d, y, c2 + d, st(WHITE_ST, "north", "top"))
        bb.fill(a1 - d, y, c1 - d + 1, a1 - d, y, c2 + d - 1, st(WHITE_ST, "east", "top"))
        bb.fill(a2 + d, y, c1 - d + 1, a2 + d, y, c2 + d - 1, st(WHITE_ST, "west", "top"))
        if d > 1:      # fill inside the corbel ring (keeps the stair well open)
            bb.fill(a1 - d + 1, y, c1 - d + 1, a2 + d - 1, y, c1, WHITE); bb.fill(a1 - d + 1, y, c2, a2 + d - 1, y, c2 + d - 1, WHITE)
            bb.fill(a1 - d + 1, y, c1, a1, y, c2, WHITE); bb.fill(a2, y, c1, a2 + d - 1, y, c2, WHITE)
    FL = TT + 1
    bb.fill(a1 - 5, FL, c1 - 5, a2 + 5, FL, c2 + 5, TILE)
    for (a, b2, c, d) in ((a1 - 5, a2 + 5, c1 - 5, c1 - 5), (a1 - 5, a2 + 5, c2 + 5, c2 + 5),
                          (a1 - 5, a1 - 5, c1 - 5, c2 + 5), (a2 + 5, a2 + 5, c1 - 5, c2 + 5)):
        bb.fill(a, FL + 1, c, b2, FL + 1, d, WHITE_W)
    P.square_spiral_stair(bb, a1 + 1, top + 1, c1 + 1, a2 - a1 - 1, FL, WHITE_ST, core=None, headroom=3)
    # the condemned's stand facing the plaza, with the iron stocks
    bb.fill(CX - 2, FL + 1, c2 + 1, CX + 2, FL + 1, c2 + 3, "minecraft:dark_oak_planks")
    bb.fill(CX - 1, FL + 2, c2 + 3, CX + 1, FL + 2, c2 + 3, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]")
    for x in (CX - 3, CX + 3):
        bb.fill(x, FL + 1, c2 + 2, x, FL + 4, c2 + 2, "minecraft:dark_oak_fence")
        bb.set(x, FL + 5, c2 + 2, "minecraft:lantern[hanging=false]")
    for (x, z) in ((a1 - 5, c1 - 5), (a2 + 5, c1 - 5), (a1 - 5, c2 + 5), (a2 + 5, c2 + 5)):
        bb.set(x, FL + 2, z, "minecraft:lantern[hanging=false]")
    # Marine flags either side of the tower
    for x in (a1 - 4, a2 + 4):
        bb.fill(x, FL + 1, c1 - 4, x, FL + 12, c1 - 4, "minecraft:white_concrete")
        bb.fill(x + (1 if x > CX else -5), FL + 8, c1 - 4, x + (5 if x > CX else -1), FL + 11, c1 - 4, "minecraft:white_wool")
        bb.fill(x + (2 if x > CX else -4), FL + 9, c1 - 4, x + (4 if x > CX else -2), FL + 10, c1 - 4, "minecraft:blue_wool")
    return FL


# ---------------------------------------------------------------- Ox Bell, barracks, watchtowers, town
def ox_bell(bb, x, z):
    """The Ox Bell: a huge bronze temple bell in a timber frame under a tiled roof, on a white platform."""
    bb.fill(x - 7, 0, z - 7, x + 7, 1, z + 7, WHITE)
    bb.fill(x - 6, 1, z - 6, x + 6, 1, z + 6, TILE)
    P.stair_run(bb, x - 2, 1, z + 8, 1, 5, "north", WHITE_ST)
    for sx in (-5, 5):
        for sz in (-5, 5):
            bb.fill(x + sx, 2, z + sz, x + sx, 15, z + sz, "minecraft:dark_oak_log[axis=y]")
    for y in (15, 16):
        bb.fill(x - 6, y, z - 5, x + 6, y, z - 5, "minecraft:dark_oak_log[axis=x]")
        bb.fill(x - 6, y, z + 5, x + 6, y, z + 5, "minecraft:dark_oak_log[axis=x]")
        bb.fill(x - 5, y, z - 6, x - 5, y, z + 6, "minecraft:dark_oak_log[axis=z]")
        bb.fill(x + 5, y, z - 6, x + 5, y, z + 6, "minecraft:dark_oak_log[axis=z]")
    bb.fill(x - 5, 16, z, x + 5, 16, z, "minecraft:dark_oak_log[axis=x]")
    P.hip_roof(bb, x - 7, z - 7, x + 7, z + 7, 17, ROOF_ST, overhang=1)
    bb.fill(x, 14, z, x, 15, z, "minecraft:iron_chain[axis=y,waterlogged=false]")
    for (y, r) in ((13, 1), (12, 2), (11, 2), (10, 2), (9, 3), (8, 3), (7, 3), (6, 3), (5, 3)):
        bb.cylinder(x, y, z, r, y, "minecraft:waxed_cut_copper" if y in (11, 7) else "minecraft:waxed_copper_block")
    bb.cylinder(x, 5, z, 2, 9, AIR)
    bb.fill(x + 4, 10, z, x + 4, 14, z, "minecraft:spruce_fence")
    bb.fill(x + 4, 9, z, x + 6, 9, z, "minecraft:stripped_spruce_log[axis=x]")


def barracks(bb, x1, z1, x2, z2, tracker, audit, door_x):
    """A three-storey Marine barracks: white walls with pilasters, blue hip roof, bunk floors and a mess."""
    bb.fill(x1, 0, z1, x2, 0, z2, TILE)
    bb.mix(x1, 1, z1, x2, 17, z2, WALLMIX, [0.75, 0.15, 0.10])
    bb.fill(x1 + 1, 1, z1 + 1, x2 - 1, 17, z2 - 1, AIR)
    for y in (6, 12):
        bb.fill(x1 + 1, y, z1 + 1, x2 - 1, y, z2 - 1, "minecraft:smooth_stone")
        bb.fill(x1, y, z1, x2, y, z1, BLUE); bb.fill(x1, y, z2, x2, y, z2, BLUE)
        bb.fill(x1, y, z1, x1, y, z2, BLUE); bb.fill(x2, y, z1, x2, y, z2, BLUE)
    for y in (2, 8, 14):
        for x in range(x1 + 2, x2 - 1, 3):
            bb.fill(x, y, z1, x, y + 1, z1, GLASS); bb.fill(x, y, z2, x, y + 1, z2, GLASS)
        for z in range(z1 + 2, z2 - 1, 3):
            bb.fill(x1, y, z, x1, y + 1, z, GLASS); bb.fill(x2, y, z, x2, y + 1, z, GLASS)
    for x in range(x1, x2 + 1, 6):
        bb.fill(x, 1, z2 + 1, x, 17, z2 + 1, PIL); bb.fill(x, 1, z1 - 1, x, 17, z1 - 1, PIL)
    for i, y in enumerate((1, 7, 13)):
        wing_floor(bb, x1 + 1, z1 + 1, x2 - 1, z2 - 1, y, 5, INNER, seed_of("bar", x1, y), tracker,
                   [["kitchen", "storage"], ["bedroom"], ["bedroom", "living"]][i], corridor="z", cw=3, audit=audit,
                   max_room=10)
    # ladders up beside the corridor
    cxm = (x1 + x2) // 2
    bb.fill(cxm + 2, 1, z1 + 1, cxm + 2, 13, z1 + 1, "minecraft:ladder[facing=south]")
    bb.fill(cxm + 2, 6, z1 + 1, cxm + 2, 6, z1 + 1, "minecraft:ladder[facing=south]")
    bb.fill(cxm + 2, 12, z1 + 1, cxm + 2, 12, z1 + 1, "minecraft:ladder[facing=south]")
    bb.fill(door_x - 1, 1, z2, door_x + 1, 3, z2, AIR)
    bb.set(door_x, 1, z2, "minecraft:spruce_door[facing=south,half=lower,hinge=left,open=false]")
    bb.set(door_x, 2, z2, "minecraft:spruce_door[facing=south,half=upper,hinge=left,open=false]")
    castle_eave(bb, x1, z1, x2, z2, 17, ROOF_ST, ROOF, depth=2)
    P.hip_roof(bb, x1, z1, x2, z2, 19, ROOF_ST, overhang=1)


def training_yard(bb, x1, z1, x2, z2, rng):
    bb.fill(x1, 0, z1, x2, 0, z2, "minecraft:coarse_dirt")
    bb.mix(x1, 0, z1, x2, 0, z2, ["minecraft:coarse_dirt", "minecraft:dirt_path", "minecraft:packed_mud"], [0.5, 0.3, 0.2])
    for x in range(x1, x2 + 1):
        bb.set(x, 1, z1, "minecraft:spruce_fence"); bb.set(x, 1, z2, "minecraft:spruce_fence")
    for z in range(z1, z2 + 1):
        bb.set(x1, 1, z, "minecraft:spruce_fence"); bb.set(x2, 1, z, "minecraft:spruce_fence")
    bb.fill((x1 + x2) // 2 - 1, 1, z1, (x1 + x2) // 2 + 1, 1, z1, AIR)
    for i, x in enumerate(range(x1 + 4, x2 - 2, 5)):           # straw dummies
        bb.set(x, 1, z1 + 4, "minecraft:hay_block[axis=y]")
        bb.set(x, 2, z1 + 4, "minecraft:carved_pumpkin[facing=south]")
        bb.set(x, 1, z2 - 4, "minecraft:target")
    for z in range(z1 + 7, z2 - 6, 4):
        bb.set(x1 + 1, 1, z, "onepiece:weapon_rack[facing=east]")
    bb.set(x2 - 2, 1, z1 + 8, "onepiece:cannonball_pile[facing=west]")
    bb.set(x2 - 2, 1, z1 + 10, "onepiece:cannon[facing=west]")


def watchtower(bb, x, z, h=34):
    """A round white watchtower with a spiral stair, a cannon on top and the Marine flag."""
    bb.cylinder(x, 0, z, 5, h, WHITE)
    bb.cylinder(x, 1, z, 4, h - 1, AIR)
    bb.cylinder(x, h, z, 6, h, TILE)
    P.square_spiral_stair(bb, x - 2, 1, z - 2, 5, h, WHITE_ST, core=WHITE)
    for a in range(0, 360, 20):
        t = math.radians(a)
        bb.set(round(x + 6 * math.cos(t)), h + 1, round(z + 6 * math.sin(t)), WHITE_W)
    bb.fill(x, 1, z + 5, x, 2, z + 5, AIR); bb.fill(x, 1, z - 5, x, 2, z - 5, AIR)
    for y in range(6, h - 2, 7):
        for (dx, dz) in ((5, 0), (-5, 0), (0, 5), (0, -5)):
            bb.set(x + dx, y, z + dz, GLASS)
    bb.set(x + 3, h + 1, z, "onepiece:cannon[facing=south]")
    bb.fill(x - 3, h + 1, z + 2, x - 3, h + 9, z + 2, "minecraft:white_concrete")
    bb.fill(x - 3, h + 6, z + 3, x - 3, h + 9, z + 7, "minecraft:white_wool")
    bb.fill(x - 3, h + 7, z + 4, x - 3, h + 8, z + 6, "minecraft:blue_wool")
    bb.set(x, h + 1, z - 3, "minecraft:lantern[hanging=false]")


TOWN = dict(walls=["minecraft:white_concrete", "minecraft:calcite", "minecraft:white_terracotta"],
            frame="minecraft:stripped_birch_log", base=["minecraft:stone_bricks", "minecraft:polished_andesite",
                                                        "minecraft:andesite"],
            floor="minecraft:spruce_planks", wood="spruce", chimney="minecraft:stone_bricks")
ROOFS = ["minecraft:brick_stairs", "minecraft:dark_prismarine_stairs", "minecraft:mud_brick_stairs",
         "minecraft:deepslate_tile_stairs"]


def town(bb, tracker, audit, reserved):
    """Marine family houses on both arms of the crescent and beside the plaza, doors facing the plaza."""
    rng = np.random.default_rng(seed_of("mftown"))
    placed = []
    cands = []
    for z0 in range(60, 214, 3):
        for x0 in list(range(4, 70, 3)) + list(range(150, 216, 3)):
            cands.append((x0, z0))
    # random-order lot packing, lots nearest the plaza first (lesson L103: a packed town, 1-2 block alleys)
    rng.shuffle(cands)
    cands.sort(key=lambda c: math.hypot(c[0] - CX, c[1] - 100) + float(rng.uniform(0, 20)))
    for (x0, z0) in cands:
        w = int(rng.integers(8, 12)); d = int(rng.integers(7, 11))
        floors = int(rng.integers(2, 4))
        cx, cz = x0 + w / 2, z0 + d / 2
        # door toward the plaza / bay
        dxp, dzp = CX - cx, BAY_C[1] - cz
        rot = (0 if dzp > 0 else 2) if abs(dzp) > abs(dxp) * 0.8 else (3 if dxp > 0 else 1)
        W, D = (w, d) if rot % 2 == 0 else (d, w)
        box = (x0 - 1, z0 - 1, x0 + W, z0 + D)
        if box[2] >= N - 2 or box[3] >= N - 2 or not on_land(box[0], box[1], box[2], box[3], pad=2):
            continue
        if any(in_bay(x, z, 7) for x in (box[0], box[2]) for z in (box[1], box[3])) or in_bay(cx, cz, 7):
            continue
        if any(box[0] <= r[2] and r[0] <= box[2] and box[1] <= r[3] and r[1] <= box[3] for r in reserved + placed):
            continue
        roof = ROOFS[int(rng.integers(len(ROOFS)))]
        m, top, au = house_module(seed_of("mfh", x0, z0), w, d, floors, roof, tracker,
                                  [["kitchen", "living"][int(rng.integers(2))], "bedroom", "bedroom"], pal=TOWN,
                                  timber=False, jetty=False)
        audit += au
        place_house(bb, m, w, d, x0, 0, z0, rot)
        placed.append(box)
        # a little garden / bench / lamp at the door side
        lx = x0 - 2 if rot != 3 else x0 + W + 1
        lamp_post(bb, lx, 1, z0 + D // 2)
    # little gardens with a tree in the gaps between the houses
    for _ in range(140):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(92, N - 4))
        if in_bay(x, z, 6) or not on_land(x - 2, z - 2, x + 2, z + 2, 1) or any(r[0] - 2 <= x <= r[2] + 2 and r[1] - 2 <= z <= r[3] + 2 for r in reserved + placed):
            continue
        reg = bb.get_region(x - 2, 1, z - 2, x + 2, 8, z + 2)
        if (reg > 1).any():
            continue
        bb.fill(x - 2, 0, z - 2, x + 2, 0, z + 2, "minecraft:grass_block[snowy=false]")
        for (dx, dz) in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
            bb.set(x + dx, 1, z + dz, "minecraft:potted_red_tulip" if (dx + dz) % 4 else "minecraft:potted_oxeye_daisy")
        P.tree(bb, x, 1, z, height=int(rng.integers(5, 8)), kind=["oak", "birch", "cherry"][int(rng.integers(3))], rng=rng)
        bb.set(x + 1, 1, z + 2, "minecraft:spruce_stairs[facing=north,half=bottom]")
        placed.append((x - 3, z - 3, x + 3, z + 3))
    return placed


# ---------------------------------------------------------------- assembly
def design():
    bb = BigBuild(seed=59, y_min=FLOOR - 3, y_max=130)
    tracker = P.PropTracker(59)
    audit = []
    rng = np.random.default_rng(59)
    ground(bb)
    ridge = hq(bb, tracker, audit)
    FL = scaffold(bb, tracker, audit)
    encircling_wall(bb)
    ox_bell(bb, *BELL)
    barracks(bb, 16, 22, 50, 64, tracker, audit, 33)
    barracks(bb, 170, 22, 204, 64, tracker, audit, 187)
    training_yard(bb, 16, 70, 48, 94, rng)
    training_yard(bb, 172, 70, 204, 94, rng)
    for (x, z) in ((38, 194), (182, 194)):
        watchtower(bb, x, z)
    # piers and the warships at anchor inside the encircling wall (the show-accurate Marine warship template)
    for px in (70, 150):
        edge = round(BAY_C[1] - math.sqrt(BAY_R ** 2 - (px - BAY_C[0]) ** 2))
        pier(bb, px, edge - 1, edge + 34)
    stamp_ship(bb, "marine_warship", 91, 152, water_y=SEA, rot=1)
    stamp_ship(bb, "marine_warship", 129, 152, water_y=SEA, rot=3)
    stamp_ship(bb, "marine_warship", 110, 192, water_y=SEA, rot=0)
    # plaza: lamp posts, flag poles, the quay battery, planters with trees
    for x in range(56, 165, 9):
        if abs(x - CX) > 32 and land(np.array([x]), np.array([94]))[0]:
            lamp_post(bb, x, 1, 94, post="minecraft:dark_oak_fence", h=4)
    for (x, z) in ((54, 96), (166, 96), (40, 120), (180, 120)):
        bb.fill(x, 1, z, x, 14, z, "minecraft:white_concrete")
        bb.fill(x + 1, 10, z, x + 6, 13, z, "minecraft:white_wool")
        bb.fill(x + 2, 11, z, x + 5, 12, z, "minecraft:blue_wool")
    for a in range(-150, 151, 8):
        t = math.radians(a)
        x = round(BAY_C[0] + (BAY_R + 5) * math.sin(t)); z = round(BAY_C[1] - (BAY_R + 5) * math.cos(t))
        if 0 < x < N - 1 and z < N - 1 and abs(x - 70) > 4 and abs(x - 150) > 4 and land(np.array([x]), np.array([z]))[0]:
            bb.set(x, 1, z, "onepiece:cannon[facing=%s]" % ("south" if abs(a) < 45 else "east" if a < 0 else "west"))
            if a % 16 == 0:
                bb.set(x, 1, z + (-1 if abs(a) < 90 else 1), "onepiece:cannonball_pile[facing=south]")
    for (x, z) in ((58, 82), (162, 82), (36, 140), (184, 140), (86, 96), (134, 96)):
        bb.fill(x - 2, 1, z - 2, x + 2, 1, z + 2, WHITE_W)
        bb.fill(x - 1, 1, z - 1, x + 1, 1, z + 1, "minecraft:grass_block[snowy=false]")
        P.tree(bb, x, 2, z, height=6, kind="oak", rng=rng)
    reserved = [(10, 18, 54, 98), (166, 18, 210, 98), (48, 0, 172, 76), (74, 70, 146, 92), (44, 98, 64, 118),
                (28, 184, 48, 204), (172, 184, 192, 204)]
    town(bb, tracker, audit, reserved)
    # benches along the quay
    for x in (84, 96, 124, 136):
        bb.set(x, 1, 98, "minecraft:spruce_stairs[facing=north,half=bottom]")
        bb.set(x + 1, 1, 98, "minecraft:spruce_stairs[facing=north,half=bottom]")
    return bb, audit, ridge, FL


def build():
    bb, audit, ridge, FL = design()
    for a in audit[:20]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    hw, z1, z2, y0, n = TIERS[0]
    b.chest(CX - 30, 1, 40, "marine", "east"); b.chest(CX + 30, 1, 30, "marine", "west")
    hw2, a1, a2, b0 = KEEP_TOP
    b.chest(CX + 3, b0 + 1, a1 + 2, "legendary", "south")
    b.flag(CX, ridge + 2, (a1 + a2) // 2, h=10, colors=("minecraft:white_wool", "minecraft:blue_wool"), skull=False)
    x1, x2, sz1, sz2, top = SW
    b.npc(CX, top + 1, sz2 - 2, "akainu", True)
    b.guards("vice_admiral", ((CX - 14, sz2 + 6), (CX + 14, sz2 + 6)))
    b.guards("pacifista", ((CX - 26, sz2 + 14), (CX + 26, sz2 + 14)))
    b.guards("elite_marine", ((CX - 22, 92), (CX + 22, 92), (CX, 98)))
    b.guards("marine", ((60, 108), (160, 108), (CX - 40, 96), (CX + 40, 96), (CX, 30), (32, 82), (188, 82)))
    b.guards("marine_rifle", ((70, 115), (150, 115)))
    b.guards("marine_rifle", ((CX - 6, 92), (CX + 6, 92)), y=FL + 1)
    return b, SEA
