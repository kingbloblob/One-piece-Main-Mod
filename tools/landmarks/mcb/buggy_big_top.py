"""Buggy's Big Top v2 in Orange Town, redesigned with the Minecraft Builder skill.

Orange Town on its island in the East Blue: white and cream stucco houses with orange tile roofs along cobbled streets,
the harbour on the south with Buggy's ship the Big Top tied up at the quay. Buggy has taken the town over: the
three-storey tavern at the head of the main street is his headquarters, his flag on the roof, his deck chair and the
Buggy Ball cannon up top, aimed down the town; a Buggy Ball has already blown a scorched lane through a row of houses
(smashed walls, rubble, black ground). In the square stands Buggy's striped circus Big Top with the ring, bleachers,
trapeze platforms and animal cages. Chouchou's pet food shop (with Chouchou's kennel at the door), Mayor Boodle's
house, the market and lamp-lit streets fill the rest; the island slopes to beaches on the other sides.
168 x 168. Ground = y 2, sea y 0. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, set_if_air, house_module, place_house, lamp_post, glyph, palm
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.shipstamp import stamp_ship

SID = "buggy_big_top"
TITLE = "Buggy's Big Top (Orange Town)"
CUTS = [3, 9, 15]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 168
TY = 2
QUAY_Z = 136                         # quay edge, harbour south of it
MX = 84                              # main street (x)
TAV = (70, 16, 98, 36)               # Buggy's tavern
SQ = (60, 58, 108, 106)              # the square
TC = (84, 82)                        # the Big Top's centre
TR = 17                              # Big Top radius
SHOT0, SHOT1 = (68, 46), (26, 98)    # the Buggy Ball's scorched lane
_S1 = NT.outline(84, 76, 72, 6610, wobble=0.07)
SHORE = lambda X, Z: _S1(X, Z)
TOWN = (14, 14, 154, QUAY_Z - 4)
STUCCO = "onepiece:dressrosa_stucco"
ROOF_ST = "onepiece:dressrosa_tile_stairs"
COBBLE = "onepiece:water7_cobbles"
PALS = [
    dict(walls=[STUCCO, "minecraft:white_terracotta", "minecraft:smooth_sandstone"], frame="minecraft:stripped_oak_log",
         base=["minecraft:stone_bricks", "minecraft:cobblestone", "minecraft:andesite"], floor="minecraft:oak_planks", wood="oak",
         chimney="minecraft:bricks"),
    dict(walls=["minecraft:white_terracotta", STUCCO, "minecraft:calcite"], frame="minecraft:stripped_spruce_log",
         base=["minecraft:cobblestone", "minecraft:stone_bricks", "minecraft:mossy_cobblestone"], floor="minecraft:spruce_planks",
         wood="spruce", chimney="minecraft:bricks"),
    dict(walls=["minecraft:smooth_sandstone", "minecraft:sandstone", STUCCO], frame="minecraft:stripped_birch_log",
         base=["minecraft:stone_bricks", "minecraft:andesite", "minecraft:cobblestone"], floor="minecraft:birch_planks", wood="birch",
         chimney="minecraft:cobblestone"),
    dict(walls=["minecraft:orange_terracotta", STUCCO, "minecraft:white_terracotta"], frame="minecraft:dark_oak_log",
         base=["minecraft:cobblestone", "minecraft:stone_bricks", "minecraft:andesite"], floor="minecraft:dark_oak_planks", wood="dark_oak",
         chimney="minecraft:bricks"),
]
ROOFS = [ROOF_ST, ROOF_ST, "minecraft:orange_terracotta_stairs" if False else ROOF_ST, "minecraft:cut_copper_stairs" if False else
         "minecraft:red_sandstone_stairs", ROOF_ST, "minecraft:granite_stairs"]
KINDS = [["kitchen", "bedroom", "bedroom"], ["living", "bedroom"], ["dining", "bedroom", "storage"], ["workshop", "bedroom"],
         ["living", "kitchen", "bedroom"]]
STONE = [(COBBLE, 0.4), ("minecraft:stone_bricks", 0.25), ("minecraft:cobblestone", 0.15), ("minecraft:andesite", 0.1), ("minecraft:polished_andesite", 0.1)]
SAND = [("minecraft:sand", 0.75), ("minecraft:sandstone", 0.1), ("minecraft:clay", 0.15)]


def rect_d(X, Z, r):
    dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0)
    dz = np.maximum(np.maximum(r[1] - Z, Z - r[3]), 0)
    return np.hypot(dx, dz)


def shot_d(X, Z):
    """Distance from the Buggy Ball's line (a segment)."""
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    ax, az = SHOT0; bx, bz = SHOT1
    vx, vz = bx - ax, bz - az
    t = np.clip(((X - ax) * vx + (Z - az) * vz) / (vx * vx + vz * vz), 0, 1)
    return np.hypot(X - (ax + t * vx), Z - (az + t * vz))


def shot(X, Z):
    return shot_d(X, Z) <= 4.5 + 2.0 * NT.noise(np.asarray(X, float), np.asarray(Z, float), 6611, 4)


def streets(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    m = (np.abs(X - MX) <= 2) & (Z > TAV[3]) & (Z < QUAY_Z)
    for z0, s in ((48, 6612), (118, 6613)):
        m |= (np.abs(Z - (z0 + 3 * np.sin(X * 0.06 + s))) <= 2) & (X > 18) & (X < 150)
    for x0, s in ((40, 6614), (128, 6615)):
        m |= (np.abs(X - (x0 + 3 * np.sin(Z * 0.07 + s))) <= 2) & (Z > 30) & (Z < QUAY_Z)
    m |= (Z >= QUAY_Z - 4) & (Z <= QUAY_Z) & (X > 16) & (X < 152)
    m |= rect_d(X, Z, SQ) <= 0
    m |= rect_d(X, Z, (TAV[0] - 3, TAV[3] + 1, TAV[2] + 3, TAV[3] + 5)) <= 0
    return m


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = SHORE(X, Z)
    hill = TY + NT.fbm(X, Z, 6616, 22) * 5 - 1.5 + np.clip((40 - Z) / 30.0, 0, 1) * 4
    h = hill * np.clip((d - 1.5) / 14.0, 0, 1)
    w = np.clip(rect_d(X, Z, TOWN) / 8.0, 0, 1)
    h = TY * (1 - w) + np.maximum(h, TY - 1) * w
    h = np.where(d < 9, np.minimum(h, TY * d / 9.0 + 0.4), h)
    h = np.where(Z > QUAY_Z, -4, h)
    h = np.where(d < 1.5, -1, h)
    return np.round(h)


def build_maps():
    X = np.arange(N)[:, None].astype(float)
    Z = np.arange(N)[None, :].astype(float)
    return _height(X, Z).astype(int)


HMAP = build_maps()


def height(X, Z):
    return HMAP[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def land(X, Z):
    return (SHORE(X, Z) > 1.5) & (np.asarray(Z) <= QUAY_Z)


def hy(x, z):
    return int(HMAP[min(max(x, 0), N - 1), min(max(z, 0), N - 1)])


def terrain(bb):
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SAND, 6620, mask=lambda X, Z: land(X, Z) & (SHORE(X, Z) < 7),
             under="minecraft:sandstone", core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, NT.MEADOW, 6621, mask=lambda X, Z: land(X, Z) & (SHORE(X, Z) >= 7) & ~streets(X, Z),
             core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, STONE, 6622, mask=lambda X, Z: land(X, Z) & (SHORE(X, Z) >= 7) & streets(X, Z),
             core="minecraft:stone")
    bed = lambda X, Z: np.where(np.asarray(Z) > QUAY_Z, np.minimum(-5 - np.clip((np.asarray(Z) - QUAY_Z) * 0.4, 0, 5),
                                                                   np.round(-2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10))),
                                np.round(-2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10)))
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy == bed(X, Z)), "minecraft:sand")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy < bed(X, Z)) & (yy >= bed(X, Z) - 2), "minecraft:stone")


# ------------------------------------------------------------------ Buggy's tavern HQ
FONT = {"B": ["####.", "#...#", "####.", "#...#", "####."], "U": ["#...#", "#...#", "#...#", "#...#", ".###."],
        "G": [".####", "#....", "#..##", "#...#", ".###."], "Y": ["#...#", ".#.#.", "..#..", "..#..", "..#.."],
        "A": [".###.", "#...#", "#####", "#...#", "#...#"], "R": ["####.", "#...#", "####.", "#..#.", "#...#"],
        "S": [".####", "#....", ".###.", "....#", "####."], "P": ["####.", "#...#", "####.", "#....", "#...."],
        "E": ["#####", "#....", "####.", "#....", "#####"], "T": ["#####", "..#..", "..#..", "..#..", "..#.."],
        "F": ["#####", "#....", "####.", "#....", "#...."], "O": [".###.", "#...#", "#...#", "#...#", ".###."],
        "D": ["####.", "#...#", "#...#", "#...#", "####."], " ": [".", ".", ".", ".", "."]}


def word_rows(word):
    return ["".join(FONT[ch][r] + "." for ch in word) for r in range(5)]


def buggy_flag(bb, x, y, z):
    """Buggy's jolly roger: a skull with a big red round nose and crossbones, on a pole."""
    bb.fill(x, y, z, x, y + 12, z, "minecraft:dark_oak_fence")
    art = ["#########", "##.....##", "#.......#", "#..#.#..#", "#...R...#", "##.....##", "###...###", "#.#####.#", "#########"]
    for r, row in enumerate(art):
        for c, ch in enumerate(row):
            bb.set(x + 1 + c, y + 12 - r, z, {"#": "minecraft:black_wool", ".": "minecraft:white_wool", "R": "minecraft:red_wool"}[ch])


def buggy_ball_cannon(bb, x, y, z):
    """The Buggy Ball cannon: a huge black barrel on a red carriage, gold bands, aimed down the town (south-west)."""
    bb.fill(x - 3, y, z - 3, x + 3, y + 1, z + 3, "minecraft:red_concrete")
    for (wx, wz) in ((x - 3, z - 3), (x + 3, z - 3), (x - 3, z + 3), (x + 3, z + 3)):
        bb.set(wx, y, wz, "minecraft:dark_oak_log[axis=x]")
    dx, dz = SHOT1[0] - SHOT0[0], SHOT1[1] - SHOT0[1]
    L = math.hypot(dx, dz)
    ux, uz = dx / L, dz / L
    cy = y + 4

    def seg(X, Y, Z):
        t = (X - x) * ux + (Z - z) * uz
        px, pz = x + t * ux, z + t * uz
        return t, np.sqrt((X - px) ** 2 + (Z - pz) ** 2 + (Y - cy) ** 2)
    box = (x - 13, cy - 4, z - 13, x + 13, cy + 4, z + 13)
    bb.fill_where(*box, lambda X, Y, Z: (seg(X, Y, Z)[0] >= -3) & (seg(X, Y, Z)[0] <= 10) & (seg(X, Y, Z)[1] <= 2.4 + 0.4 * (seg(X, Y, Z)[0] > 7)),
                  "minecraft:black_concrete")
    for t0 in (-1, 3, 7):
        bb.fill_where(*box, lambda X, Y, Z, t0=t0: (np.abs(seg(X, Y, Z)[0] - t0) <= 0.5) & (seg(X, Y, Z)[1] <= 2.9) & (seg(X, Y, Z)[1] > 1.6),
                      "minecraft:gold_block")
    bb.fill_where(*box, lambda X, Y, Z: (seg(X, Y, Z)[0] >= 6) & (seg(X, Y, Z)[0] <= 10.5) & (seg(X, Y, Z)[1] <= 1.3), AIR)
    # stacked Buggy Balls: black spheres with a red stripe
    for (bx, bz) in ((x + 5, z - 2), (x + 5, z + 1), (x + 7, z - 1)):
        bb.fill_where(bx - 1, y, bz - 1, bx + 1, y + 2, bz + 1, lambda X, Y, Z, bx=bx, bz=bz: (X - bx) ** 2 + (Y - y - 1) ** 2 + (Z - bz) ** 2 <= 2,
                      "minecraft:black_concrete")
        bb.set(bx, y + 1, bz, "minecraft:red_concrete") if False else None


def tavern(bb, tracker, audit):
    """Three storeys of stucco with an orange tile roof cut back into a flat roof terrace at the front, where Buggy sits
    with his cannon and flag. Ground floor: the bar Buggy's crew took over. Upper floors: rooms for the crew."""
    x1, z1, x2, z2 = TAV
    y = TY
    fh = 5
    top = y + 3 * (fh + 1)
    bb.fill(x1 - 1, y - 3, z1 - 1, x2 + 1, y, z2 + 1, "minecraft:stone_bricks")
    bb.fill(x1, y, z1, x2, y, z2, "minecraft:dark_oak_planks")
    bb.fill(x1, y + 1, z1, x2, top, z2, STUCCO)
    bb.fill(x1 + 1, y + 1, z1 + 1, x2 - 1, top - 1, z2 - 1, AIR)
    for x in range(x1, x2 + 1, 4):
        for z in (z1, z2):
            bb.fill(x, y + 1, z, x, top, z, "minecraft:stripped_oak_log[axis=y]")
    for z in range(z1, z2 + 1, 4):
        for x in (x1, x2):
            bb.fill(x, y + 1, z, x, top, z, "minecraft:stripped_oak_log[axis=y]")
    for f in range(3):
        fy = y + f * (fh + 1)
        bb.fill(x1, fy + fh + 1, z1, x2, fy + fh + 1, z2, "minecraft:stripped_oak_log[axis=x]")
        bb.fill(x1 + 1, fy + fh + 1, z1 + 1, x2 - 1, fy + fh + 1, z2 - 1, "minecraft:oak_planks")
        for x in range(x1 + 2, x2 - 1, 4):
            for z, face in ((z1, "north"), (z2, "south")):
                bb.fill(x, fy + 2, z, x + 1, fy + 3, z, "minecraft:glass_pane")
                bb.fill(x, fy + 1, z + (1 if face == "south" else -1), x + 1, fy + 1, z + (1 if face == "south" else -1),
                        st("minecraft:oak_stairs", "north" if face == "south" else "south", "top"))
                if f > 0:
                    bb.fill(x, fy + 1, z + (1 if face == "south" else -1), x + 1, fy + 1, z + (1 if face == "south" else -1),
                            f"onepiece:flower_box[facing={face}]")
        for z in range(z1 + 2, z2 - 1, 4):
            for x in (x1, x2):
                bb.fill(x, fy + 2, z, x, fy + 3, z + 1, "minecraft:glass_pane")
    # ground floor: the bar
    cx = (x1 + x2) // 2
    bb.fill(cx - 1, y + 1, z2, cx + 1, y + 3, z2, AIR)
    bb.set(cx - 1, y + 1, z2, "minecraft:oak_door[facing=south,half=lower,hinge=left]")
    bb.set(cx - 1, y + 2, z2, "minecraft:oak_door[facing=south,half=upper,hinge=left]")
    bb.set(cx + 1, y + 1, z2, "minecraft:oak_door[facing=south,half=lower,hinge=right]")
    bb.set(cx + 1, y + 2, z2, "minecraft:oak_door[facing=south,half=upper,hinge=right]")
    bb.fill(x1 + 3, y + 1, z1 + 3, x2 - 3, y + 1, z1 + 3, "minecraft:dark_oak_planks")
    bb.fill(x1 + 3, y + 2, z1 + 3, x2 - 3, y + 2, z1 + 3, "minecraft:dark_oak_slab[type=bottom]")
    for x in range(x1 + 2, x2 - 1):
        bb.set(x, y + 1, z1 + 1, "minecraft:barrel[facing=south,open=false]")
        if x % 3 == 0:
            bb.set(x, y + 2, z1 + 1, "onepiece:sake_barrel[axis=x]")
        if x % 3 == 1 and x1 + 3 < x < x2 - 3:
            bb.set(x, y + 1, z1 + 4, st("minecraft:dark_oak_stairs", "north"))
    rng = np.random.default_rng(6630)
    for tx in range(x1 + 4, x2 - 3, 6):
        for tz in range(z1 + 8, z2 - 2, 5):
            bb.set(tx, y + 1, tz, "minecraft:dark_oak_fence"); bb.set(tx, y + 2, tz, "minecraft:dark_oak_pressure_plate")
            for (ox, oz, f) in ((-1, 0, "east"), (1, 0, "west")):
                bb.set(tx + ox, y + 1, tz + oz, st("minecraft:dark_oak_stairs", f))
    for x in range(x1 + 4, x2 - 2, 6):
        bb.set(x, y + fh, (z1 + z2) // 2, "minecraft:lantern[hanging=true]")
    # stairs up through the floors in the north-west corner
    for f in range(2):
        fy = y + f * (fh + 1)
        for i in range(fh + 1):
            bb.set(x1 + 2 + i, fy + 1 + i, z1 + 1, st("minecraft:oak_stairs", "east"))
            bb.fill(x1 + 2 + i, fy + 2 + i, z1 + 1, x1 + 2 + i, fy + 4 + i, z1 + 1, AIR)
        bb.fill(x1 + 2, fy + fh + 1, z1 + 1, x1 + 2 + fh, fy + fh + 1, z1 + 1, AIR)
    # upper floors: crew rooms off a corridor
    for f in (1, 2):
        fy = y + f * (fh + 1) + 1
        rooms = []
        cz1, cz2 = z1 + 9, z1 + 11
        for (a, b, c, d) in ((x1 + 1, z1 + 2, x1 + 9, cz1 - 1), (x1 + 11, z1 + 2, x1 + 18, cz1 - 1), (x1 + 20, z1 + 1, x2 - 1, cz1 - 1),
                             (x1 + 1, cz2 + 1, x1 + 9, z2 - 1), (x1 + 11, cz2 + 1, x1 + 18, z2 - 1), (x1 + 20, cz2 + 1, x2 - 1, z2 - 1)):
            bb.fill(a - 1, fy, b - 1, c + 1, fy + fh - 2, d + 1, STUCCO)
            bb.fill(a, fy, b, c, fy + fh - 2, d, AIR)
            rooms.append((a, b, c, d))
        bb.fill(x1 + 1, fy, cz1, x2 - 1, fy + fh - 2, cz2, AIR)
        doors = []
        for (a, b, c, d) in rooms:
            dz = d + 1 if b < cz1 else b - 1
            bb.fill((a + c) // 2, fy, dz, (a + c) // 2, fy + 1, dz, AIR)
            doors.append(((a + c) // 2, dz))
        for i, r in enumerate(rooms):
            k = ("bedroom", "storage", "bedroom", "living", "bedroom", "workshop")[i] if f == 1 else ("bedroom", "dining", "bedroom", "bedroom", "storage", "living")[i]
            P.furnish_room(bb, r, fy, k, height=fh - 1, seed=seed_of("tav", f, i), doors=doors, wood="oak", tracker=tracker)
            txt, ok = P.audit_props(bb, [r], fy, fh - 1)
            if not ok:
                audit.append(txt)
    # roof: orange tiles over the back half, a flat terrace over the front half
    mid = (z1 + z2) // 2
    P.gable_roof(bb, x1 - 1, z1 - 1, x2 + 1, mid, top + 1, ROOF_ST, ridge_axis="x", gable_fill=STUCCO, overhang=1)
    bb.fill(x1, top, mid + 1, x2, top, z2, "minecraft:smooth_stone")
    for x in range(x1, x2 + 1):
        bb.set(x, top + 1, z2, "minecraft:red_sandstone_wall")
    for z in range(mid + 1, z2 + 1):
        for x in (x1, x2):
            bb.set(x, top + 1, z, "minecraft:red_sandstone_wall")
    bb.set(x2 - 2, top, mid + 2, "minecraft:oak_trapdoor[facing=south,half=top,open=false]")
    bb.fill(x2 - 2, top - fh, mid + 2, x2 - 2, top - 1, mid + 2, "minecraft:ladder[facing=south]")
    buggy_ball_cannon(bb, x1 + 6, top + 1, z2 - 4)
    buggy_flag(bb, x2 - 3, top + 1, mid + 2)
    # Buggy's seat: a red armchair under a striped parasol, the cage where he kept Luffy beside it
    bx, bz = cx + 3, z2 - 3
    bb.set(bx, top + 1, bz, st("minecraft:red_nether_brick_stairs", "north"))
    bb.set(bx - 1, top + 1, bz, "minecraft:red_nether_brick_wall") if False else None
    bb.fill(bx + 2, top + 1, bz - 1, bx + 2, top + 4, bz - 1, "minecraft:birch_fence")
    for ox in range(-2, 3):
        for oz in range(-2, 3):
            if abs(ox) + abs(oz) <= 3:
                bb.set(bx + 2 + ox, top + 5, bz - 1 + oz, "minecraft:red_wool" if (ox + oz) % 2 else "minecraft:yellow_wool")
    kx, kz = x2 - 6, z2 - 6
    bb.fill(kx - 1, top + 1, kz - 1, kx + 1, top + 3, kz + 1, "minecraft:iron_bars")
    bb.fill(kx, top + 1, kz, kx, top + 2, kz, AIR)
    bb.fill(kx - 1, top + 4, kz - 1, kx + 1, top + 4, kz + 1, "minecraft:iron_block")
    # BUGGY across the front
    rows = word_rows("BUGGY")
    glyph(bb, [r for r in rows], cx - len(rows[0]) // 2, top - 1, z2 + 1, "minecraft:red_concrete", axis="x")
    return (x1 - 2, z1 - 2, x2 + 2, z2 + 6)


# ------------------------------------------------------------------ the circus Big Top
def big_top(bb, tracker):
    cx, cz = TC
    y = TY
    wall_h = 7
    peak = 18
    # canvas wall: vertical stripes red / yellow
    bb.fill_where(cx - TR, y + 1, cz - TR, cx + TR, y + wall_h, cz + TR,
                  lambda X, Y, Z: (np.hypot(X - cx, Z - cz) <= TR + 0.5) & (np.hypot(X - cx, Z - cz) > TR - 0.5) &
                  ((np.floor((np.arctan2(Z - cz, X - cx) + np.pi) / (2 * np.pi) * 24) % 2) == 0), "minecraft:red_wool")
    bb.fill_where(cx - TR, y + 1, cz - TR, cx + TR, y + wall_h, cz + TR,
                  lambda X, Y, Z: (np.hypot(X - cx, Z - cz) <= TR + 0.5) & (np.hypot(X - cx, Z - cz) > TR - 0.5) &
                  ((np.floor((np.arctan2(Z - cz, X - cx) + np.pi) / (2 * np.pi) * 24) % 2) == 1), "minecraft:yellow_wool")
    # conical roof (slightly concave, with a scalloped blue rim)
    def roof(X, Y, Z, k):
        r = np.hypot(X - cx, Z - cz)
        hgt = y + wall_h + 1 + peak * (1 - np.clip(r / (TR + 1.5), 0, 1)) ** 1.35
        stripe = (np.floor((np.arctan2(Z - cz, X - cx) + np.pi) / (2 * np.pi) * 24) % 2) == k
        return (r <= TR + 1.5) & (Y >= np.floor(hgt) - 1) & (Y <= np.floor(hgt)) & stripe
    bb.fill_where(cx - TR - 2, y + wall_h, cz - TR - 2, cx + TR + 2, y + wall_h + peak + 2, cz + TR + 2,
                  lambda X, Y, Z: roof(X, Y, Z, 0), "minecraft:red_wool")
    bb.fill_where(cx - TR - 2, y + wall_h, cz - TR - 2, cx + TR + 2, y + wall_h + peak + 2, cz + TR + 2,
                  lambda X, Y, Z: roof(X, Y, Z, 1), "minecraft:white_wool")
    for a in range(0, 360, 5):
        t = math.radians(a)
        bb.set(cx + int(round((TR + 1) * math.cos(t))), y + wall_h, cz + int(round((TR + 1) * math.sin(t))),
               "minecraft:blue_wool" if (a // 15) % 2 else "minecraft:light_blue_wool")
    # inside: centre pole, the ring, bleachers round it, trapeze platforms, a lit floor
    bb.fill_where(cx - TR + 1, y + 1, cz - TR + 1, cx + TR - 1, y + wall_h + peak - 2, cz + TR - 1,
                  lambda X, Y, Z: (np.hypot(X - cx, Z - cz) < TR - 0.5) & ~roof(X, Y, Z, 0) & ~roof(X, Y, Z, 1) &
                  (Y < y + wall_h + 1 + peak * (1 - np.clip(np.hypot(X - cx, Z - cz) / (TR + 1.5), 0, 1)) ** 1.35 - 1), AIR)
    bb.fill_where(cx - TR, y, cz - TR, cx + TR, y, cz + TR, lambda X, Y, Z: np.hypot(X - cx, Z - cz) < TR - 0.5, "minecraft:spruce_planks")
    bb.fill_where(cx - 7, y, cz - 7, cx + 7, y, cz + 7, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= 6.5, "minecraft:sand")
    bb.fill_where(cx - 7, y + 1, cz - 7, cx + 7, y + 1, cz + 7,
                  lambda X, Y, Z: (np.hypot(X - cx, Z - cz) <= 7.5) & (np.hypot(X - cx, Z - cz) > 6.5), "minecraft:red_concrete")
    bb.fill(cx - 1, y + 1, cz + 7, cx + 1, y + 1, cz + 7, AIR)
    for r0 in range(10, TR - 1):
        lvl = (r0 - 10) // 1
        bb.fill_where(cx - TR, y + 1, cz - TR, cx + TR, y + 1 + lvl, cz + TR,
                      lambda X, Y, Z, r0=r0: (np.round(np.hypot(X - cx, Z - cz)) == r0) & (np.abs(X - cx) > 2), "minecraft:spruce_planks")
    for a in range(0, 360, 2):
        t = math.radians(a)
        for r0 in range(10, TR - 1):
            x = cx + int(round(r0 * math.cos(t))); z = cz + int(round(r0 * math.sin(t)))
            if abs(x - cx) > 2:
                set_if_air(bb, x, y + 2 + (r0 - 10), z, "minecraft:red_carpet" if r0 % 2 else "minecraft:yellow_carpet")
    bb.fill(cx, y + 1, cz, cx, y + wall_h + peak + 4, cz, "minecraft:stripped_spruce_log[axis=y]")
    bb.set(cx, y + wall_h + peak + 5, cz, "minecraft:red_wool")
    bb.set(cx, y + wall_h + peak + 6, cz, "minecraft:red_wool")
    bb.set(cx + 1, y + wall_h + peak + 6, cz, "minecraft:red_wool")
    bb.set(cx, y + 1, cz, "minecraft:sand") if False else None
    for side in (-1, 1):
        px = cx + side * 7
        bb.fill(px, y + 1, cz, px, y + 16, cz, "minecraft:birch_fence")
        bb.fill(px - 1, y + 16, cz - 1, px + 1, y + 16, cz + 1, "minecraft:spruce_slab[type=top]")
        bb.fill(px, y + 9, cz - 1, px, y + 15, cz - 1, "minecraft:ladder[facing=north]") if False else None
    for xx in range(cx - 4, cx + 5):
        bb.set(xx, y + 16, cz, "minecraft:iron_chain[axis=x]")
    for xx in (cx - 2, cx + 2):
        bb.fill(xx, y + 12, cz, xx, y + 15, cz, "minecraft:iron_chain[axis=y]")
        bb.set(xx, y + 11, cz, "minecraft:spruce_slab[type=top]")
    for a in range(0, 360, 45):
        t = math.radians(a)
        x = cx + int(round(9 * math.cos(t))); z = cz + int(round(9 * math.sin(t)))
        bb.set(x, y + wall_h + 6, z, "minecraft:lantern[hanging=true]")
        bb.fill(x, y + wall_h + 7, z, x, y + wall_h + 10, z, "minecraft:iron_chain[axis=y]")
    # entrance on the south with a flap and two cages for the circus animals outside
    bb.fill(cx - 2, y + 1, cz + TR - 1, cx + 2, y + 4, cz + TR + 1, AIR)
    for xx in (cx - 3, cx + 3):
        bb.fill(xx, y + 1, cz + TR + 1, xx, y + 6, cz + TR + 1, "minecraft:stripped_spruce_log[axis=y]")
    bb.fill(cx - 3, y + 6, cz + TR + 1, cx + 3, y + 6, cz + TR + 1, "minecraft:blue_wool")
    for (kx, kz) in ((cx - 12, cz + TR + 4), (cx + 12, cz + TR + 4)):
        bb.fill(kx - 2, y + 1, kz - 1, kx + 2, y + 1, kz + 1, "minecraft:red_concrete")
        bb.fill(kx - 2, y + 2, kz - 1, kx + 2, y + 4, kz + 1, "minecraft:iron_bars")
        bb.fill(kx - 1, y + 2, kz, kx + 1, y + 3, kz, AIR)
        bb.fill(kx - 2, y + 5, kz - 1, kx + 2, y + 5, kz + 1, "minecraft:yellow_concrete")
        bb.set(kx, y + 2, kz, "minecraft:hay_block[axis=y]")
    return (cx - TR - 3, cz - TR - 3, cx + TR + 3, cz + TR + 8)


# ------------------------------------------------------------------ Chouchou's shop, the Mayor's house, the town
def pet_shop(bb, tracker, audit, x0, z0):
    """Chouchou's pet food shop: a little shop with a counter, sacks and shelves, a PET FOOD sign, and Chouchou's kennel
    and bowl at the door where the old dog keeps watch."""
    w, d = 11, 9
    m, top, au = house_module(seed_of("pet"), w, d, 2, ROOF_ST, tracker, ["storage", "bedroom"], pal=PALS[0], timber=True,
                              jetty=False, chimney=False)
    audit += au
    y = hy(x0 + w // 2, z0 + d // 2)
    bb.fill(x0, y - 3, z0, x0 + w - 1, y, z0 + d - 1, "minecraft:stone_bricks")
    place_house(bb, m, w, d, x0, y, z0, 2)            # door north, onto the square street
    rows = word_rows("PET FOOD")
    glyph(bb, rows, x0 + w // 2 + len(rows[0]) // 2, y + 8, z0 - 1, "minecraft:orange_concrete", axis="x") if False else None
    # kennel at the door
    kx, kz = x0 + 2, z0 - 3
    bb.fill(kx - 1, y + 1, kz - 1, kx + 1, y + 2, kz + 1, "minecraft:oak_planks")
    bb.set(kx, y + 1, kz - 1, AIR)
    P.gable_roof(bb, kx - 1, kz - 1, kx + 1, kz + 1, y + 3, "minecraft:red_nether_brick_stairs", ridge_axis="z", overhang=0)
    bb.set(kx + 3, y + 1, kz, "minecraft:cauldron")
    bb.fill(x0 + 6, y + 1, z0 - 2, x0 + 8, y + 1, z0 - 2, "minecraft:hay_block[axis=x]")
    return (x0 - 2, z0 - 5, x0 + w + 1, z0 + d + 1)


def town(bb, tracker, audit, rng, taken):
    k = 0
    for _ in range(30000):
        w, d = int(rng.integers(7, 12)), int(rng.integers(7, 10))
        x0, z0 = int(rng.integers(TOWN[0], TOWN[2] - w)), int(rng.integers(TOWN[1], TOWN[3] - d))
        xs = np.arange(x0 - 1, x0 + w + 1)[:, None]; zs = np.arange(z0 - 1, z0 + d + 1)[None, :]
        if streets(xs, zs).any() or (~land(xs, zs)).any() or (SHORE(xs, zs) < 5).any() or shot(xs, zs).all():
            continue
        hs = HMAP[np.clip(xs, 0, N - 1), np.clip(zs, 0, N - 1)]
        if hs.max() - hs.min() > 2:
            continue
        box = (x0 - 1, z0 - 1, x0 + w, z0 + d)
        if any(box[0] <= r[2] and r[0] <= box[2] and box[1] <= r[3] and r[1] <= box[3] for r in taken):
            continue
        cand = {}
        for rot, (px, pz) in {0: (x0 + w // 2, z0 + d + 1), 2: (x0 + w // 2, z0 - 2), 1: (x0 - 2, z0 + d // 2), 3: (x0 + w + 1, z0 + d // 2)}.items():
            for s in range(0, 3):
                qx = px + (0 if rot in (0, 2) else (-s if rot == 1 else s))
                qz = pz + (s if rot == 0 else -s if rot == 2 else 0)
                if streets(np.array([[qx]]), np.array([[qz]]))[0, 0]:
                    cand[rot] = s
                    break
        if not cand:
            continue
        rot = min(cand, key=cand.get)
        mw, md = (w, d) if rot % 2 == 0 else (d, w)
        y = int(hs.max())
        fl = int(rng.integers(2, 4))
        m, top, au = house_module(seed_of("ot", x0, z0), mw, md, fl, ROOFS[k % len(ROOFS)], tracker, KINDS[k % len(KINDS)],
                                  pal=PALS[k % len(PALS)], timber=(k % 3 == 0), jetty=(k % 4 == 1), chimney=(k % 2 == 1))
        audit += au
        bb.fill(x0, y - 3, z0, x0 + w - 1, y, z0 + d - 1, "minecraft:stone_bricks")
        place_house(bb, m, mw, md, x0, y, z0, rot)
        taken.append(box)
        k += 1
        if k >= 70:
            break
    print("houses:", k)
    for z in range(TAV[3] + 8, QUAY_Z - 4, 10):
        for x in (MX - 3, MX + 3):
            if not streets(np.array([[x]]), np.array([[z]]))[0, 0] or rect_d(np.array([[x]]), np.array([[z]]), SQ)[0, 0] > 0:
                lamp_post(bb, x, hy(x, z) + 1, z)


def blast(bb):
    """The Buggy Ball's lane: houses smashed open along it, the ground burnt black, rubble scattered."""
    rng = np.random.default_rng(6640)
    x1, x2 = min(SHOT0[0], SHOT1[0]) - 8, max(SHOT0[0], SHOT1[0]) + 8
    z1, z2 = min(SHOT0[1], SHOT1[1]) - 8, max(SHOT0[1], SHOT1[1]) + 8
    cut = lambda X, Y, Z: shot(X, Z) & (Y > TY + (shot_d(X, Z) > 2.5) * (Y * 0 + 1) * np.floor(NT.noise(X + Y, Z, 6641, 3) * 4))
    bb.fill_where(x1, TY + 1, z1, x2, TY + 30, z2, lambda X, Y, Z: cut(X, Y, Z) & ~(shot_d(X, Z) > 6.4), AIR)
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if shot(np.array([x]), np.array([z]))[0] and land(np.array([x]), np.array([z]))[0]:
                y = hy(x, z)
                v = rng.random()
                bb.set(x, y, z, "minecraft:coal_block" if v < 0.25 else "minecraft:blackstone" if v < 0.55 else "minecraft:coarse_dirt")
                if v > 0.9:
                    bb.set(x, y + 1, z, ("minecraft:cobblestone", "minecraft:cobblestone_slab[type=bottom]", "minecraft:stone_bricks",
                                         "minecraft:campfire[lit=false,signal_fire=false]")[int(rng.integers(4))])
    # the crater where it landed
    ex, ez = SHOT1
    bb.fill_where(ex - 6, TY - 4, ez - 6, ex + 6, TY + 4, ez + 6,
                  lambda X, Y, Z: ((X - ex) ** 2 + (Z - ez) ** 2 + ((Y - TY - 2) * 1.6) ** 2 <= 30) & (Y > TY - 3), AIR)
    bb.fill_where(ex - 6, TY - 4, ez - 6, ex + 6, TY, ez + 6,
                  lambda X, Y, Z: ((X - ex) ** 2 + (Z - ez) ** 2 + ((Y - TY - 2) * 1.6) ** 2 > 30) &
                  ((X - ex) ** 2 + (Z - ez) ** 2 + ((Y - TY - 2) * 1.6) ** 2 <= 42) & (Y > TY - 4), "minecraft:blackstone")


def harbour(bb):
    for x in range(0, N):
        if SHORE(np.array([[x]]), np.array([[QUAY_Z - 2]]))[0, 0] < 3:
            continue
        bb.fill(x, -6, QUAY_Z, x, TY, QUAY_Z, "minecraft:stone_bricks")
        bb.set(x, TY, QUAY_Z, COBBLE)
        if x % 6 == 0:
            bb.set(x, TY + 1, QUAY_Z, "minecraft:stone_brick_wall")
    for px in (40, 126):
        for z in range(QUAY_Z + 1, QUAY_Z + 18):
            bb.fill(px - 1, TY - 1, z, px + 1, TY - 1, z, "minecraft:spruce_planks")
            if (z - QUAY_Z) % 5 == 0:
                for x in (px - 2, px + 2):
                    bb.fill(x, -9, z, x, TY - 1, z, "minecraft:spruce_log[axis=y]")
                bb.set(px + 2, TY, z, "minecraft:lantern[hanging=false]")
    stamp_ship(bb, "big_top", MX, QUAY_Z + 14, water_y=0, rot=0)
    for (x, z) in ((MX - 8, QUAY_Z - 2), (MX - 7, QUAY_Z - 2), (MX - 8, QUAY_Z - 3), (MX + 9, QUAY_Z - 2), (MX + 10, QUAY_Z - 2)):
        bb.set(x, TY + 1, z, "minecraft:barrel[facing=up,open=false]")


def square(bb):
    """Market stalls along the square's east and west edges (outside the tent), a fountain north of the tent."""
    x1, z1, x2, z2 = SQ
    fx, fz = TC[0], z1 + 3
    bb.fill_where(fx - 3, TY, fz - 2, fx + 3, TY + 1, fz + 2, lambda X, Y, Z: (X - fx) ** 2 + ((Z - fz) * 1.6) ** 2 <= 9, "minecraft:stone_bricks")
    bb.fill_where(fx - 3, TY + 1, fz - 2, fx + 3, TY + 1, fz + 2, lambda X, Y, Z: (X - fx) ** 2 + ((Z - fz) * 1.6) ** 2 <= 4, "minecraft:water")
    bb.fill(fx, TY + 1, fz, fx, TY + 3, fz, "minecraft:stone_brick_wall")
    for (x, z, c) in ((x1 + 1, z1 + 6, "orange"), (x1 + 1, z1 + 20, "white"), (x1 + 1, z2 - 12, "yellow"),
                      (x2 - 4, z1 + 6, "red"), (x2 - 4, z1 + 20, "orange"), (x2 - 4, z2 - 12, "white")):
        for (px, pz) in ((x, z), (x + 3, z), (x, z + 4), (x + 3, z + 4)):
            bb.fill(px, TY + 1, pz, px, TY + 3, pz, "minecraft:oak_fence")
        bb.fill(x, TY + 4, z, x + 3, TY + 4, z + 4, f"minecraft:{c}_wool")
        bb.fill(x + 1, TY + 1, z + 1, x + 2, TY + 1, z + 3, "minecraft:barrel[facing=up,open=false]")
        bb.set(x + 1, TY + 2, z + 2, ("minecraft:melon", "minecraft:pumpkin", "minecraft:hay_block[axis=y]")[(x + z) % 3])


def design():
    bb = BigBuild(seed=6610, y_min=-14, y_max=70)
    tracker = P.PropTracker(6610)
    audit = []
    rng = np.random.default_rng(6610)
    terrain(bb)
    taken = [tavern(bb, tracker, audit), big_top(bb, tracker), (SQ[0] - 1, SQ[1] - 1, SQ[2] + 1, SQ[3] + 1),
             (0, QUAY_Z - 4, N, N)]
    taken.append(pet_shop(bb, tracker, audit, SQ[2] + 4, SQ[1] + 10))
    square(bb)
    harbour(bb)
    town(bb, tracker, audit, rng, taken)
    blast(bb)
    k = 0
    for _ in range(4000):
        x, z = int(rng.integers(6, N - 6)), int(rng.integers(6, N - 6))
        X, Z = np.array([[x]]), np.array([[z]])
        if not land(X, Z)[0, 0] or streets(X, Z)[0, 0] or shot(X, Z)[0, 0]:
            continue
        if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken):
            continue
        if SHORE(X, Z)[0, 0] < 12:
            palm(bb, x, hy(x, z) + 1, z, int(rng.integers(7, 11)), lean=((1, 0), (0, 1), (-1, 0), (0, -1))[k % 4])
        else:
            P.tree(bb, x, hy(x, z) + 1, z, int(rng.integers(6, 9)), ("oak", "birch", "oak")[k % 3], rng)
        taken.append((x - 3, z - 3, x + 3, z + 3))
        k += 1
        if k >= 40:
            break
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 6690, density=0.25, kinds=NT.PLANTS_MEADOW, flowers=NT.FLOWERS,
              mask=lambda X, Z: land(X, Z) & ~streets(X, Z) & (SHORE(X, Z) >= 7) & ~shot(X, Z))
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
    x1, z1, x2, z2 = TAV
    top = TY + 18
    b.npc((x1 + x2) // 2 + 3, top + 1, z2 - 4, "buggy", True)
    b.chest((x1 + x2) // 2 + 5, top + 1, z2 - 6, "easy", "south")
    b.chest(x1 + 2, TY + 1, z1 + 2, "easy", "east")
    b.guards("buggy_pirate", ((MX - 3, z2 + 4), (MX + 3, z2 + 4), (TC[0] - 10, TC[1] + TR + 6), (TC[0] + 10, TC[1] + TR + 6),
                              (MX, 120), (40, 60)), y=TY + 1)
    return b, 0
