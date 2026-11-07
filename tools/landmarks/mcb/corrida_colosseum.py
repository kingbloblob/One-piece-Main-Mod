"""Corrida Colosseum v2, redesigned with the Minecraft Builder skill: Dressrosa's great round arena where the
gladiators fought for the Mera Mera fruit.

A green Dressrosa island with the harbour on the north. In the middle stands the colosseum: a Roman drum of three
storeys in sand-coloured stone with orange bands, 32 arched bays a storey between half-columns, the two lower
storeys open arcades, the top storey an attic with small windows and a crown of red and yellow flags. Inside, a
ring corridor on the ground and first floor (food kiosks upstairs), a stair tower in each diagonal, the seating
bowl climbing from the podium wall to an open promenade, radial aisles and the royal box with its red canopy on
the north side. In the middle the ROUND stone ring stands in a moat of fighting-fish water, reached by four
walkways from the four fighters' gates. Under the stands: gladiator barracks, armories, a kitchen, the doctor's
room, the toy prisoners' cells and the trophy room where the fruit waits. Round it the plaza, the town of
white and yellow houses with tile roofs, the sunflower fields on the south slopes, the quay with a Marine
warship of Fujitora's fleet. 176 x 176. y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, furnish, set_if_air, house_module, place_house, lamp_post, stair_core
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.shipstamp import stamp_ship

SID = "corrida_colosseum"
TITLE = "Corrida Colosseum"
CUTS = [3, 9, 16, 26]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 176
_S1 = NT.outline(88, 88, 74, 3120, wobble=0.08)
_S2 = NT.outline(66, 112, 44, 3121, wobble=0.07)
SHORE = lambda X, Z: np.maximum(_S1(X, Z), _S2(X, Z))
CX, CZ = 88, 86                     # colosseum centre
GY = 2                              # ground level of the plaza and town
QUAY_Z = 28                         # quay edge; harbour north of it
R_OUT = 46                          # outer face of the drum
R_WALL = 43                         # inner face of the outer wall
R_COR = 37                          # inner face of the ring corridor (cavea solid inside it)
R_POD = 23                          # podium wall (the arena code wants open flat floor to r 17)
R_MOAT = 18                         # stage edge
L1, L2, TOPY = GY + 11, GY + 22, GY + 34
NB = 32                             # arched bays round the drum
PLAZA = 54
TOWN = (10, QUAY_Z + 4, 166, 168)

STREET = [("minecraft:smooth_sandstone", 0.3), ("minecraft:cut_sandstone", 0.2), ("minecraft:sandstone", 0.15),
          ("minecraft:polished_granite", 0.15), ("minecraft:terracotta", 0.1), ("minecraft:white_terracotta", 0.1)]
SAND = [("minecraft:sand", 0.7), ("minecraft:sandstone", 0.15), ("minecraft:clay", 0.15)]
ROCK = [("minecraft:stone", 0.35), ("minecraft:granite", 0.25), ("minecraft:andesite", 0.2), ("minecraft:cobblestone", 0.2)]
PALS = [
    dict(walls=["minecraft:white_terracotta", "minecraft:calcite", "minecraft:white_terracotta"], frame="minecraft:stripped_spruce_log",
         base=["minecraft:cut_sandstone", "minecraft:smooth_sandstone", "minecraft:sandstone"], floor="minecraft:spruce_planks",
         wood="spruce", chimney="minecraft:bricks"),
    dict(walls=["minecraft:yellow_terracotta", "minecraft:smooth_sandstone", "minecraft:yellow_terracotta"], frame="minecraft:stripped_oak_log",
         base=["minecraft:cut_sandstone", "minecraft:smooth_sandstone", "minecraft:granite"], floor="minecraft:oak_planks",
         wood="oak", chimney="minecraft:bricks"),
    dict(walls=["minecraft:pink_terracotta", "minecraft:white_terracotta", "minecraft:calcite"], frame="minecraft:stripped_dark_oak_log",
         base=["minecraft:stone_bricks", "minecraft:cut_sandstone", "minecraft:smooth_sandstone"], floor="minecraft:dark_oak_planks",
         wood="dark_oak", chimney="minecraft:bricks"),
    dict(walls=["minecraft:orange_terracotta", "minecraft:white_terracotta", "minecraft:smooth_red_sandstone"], frame="minecraft:stripped_spruce_log",
         base=["minecraft:cut_red_sandstone", "minecraft:smooth_sandstone", "minecraft:cut_sandstone"], floor="minecraft:spruce_planks",
         wood="spruce", chimney="minecraft:bricks"),
]
ROOFS = ["minecraft:granite_stairs", "minecraft:red_sandstone_stairs", "minecraft:brick_stairs", "minecraft:mud_brick_stairs",
         "minecraft:granite_stairs", "minecraft:red_nether_brick_stairs"]
KINDS = [["kitchen", "living", "bedroom", "bedroom"], ["workshop", "storage", "bedroom"], ["dining", "living", "library", "bedroom"],
         ["kitchen", "bedroom", "living"], ["storage", "living", "bedroom", "dining"]]


def rect_d(X, Z, r):
    dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0)
    dz = np.maximum(np.maximum(r[1] - Z, Z - r[3]), 0)
    return np.hypot(dx, dz)


def rad(X, Z):
    return np.hypot(np.asarray(X, float) - CX, np.asarray(Z, float) - CZ)


def streets(X, Z):
    """Four avenues out from the gates, the ring round the plaza, the harbour front."""
    X = np.asarray(X); Z = np.asarray(Z)
    r = rad(X, Z)
    m = ((np.abs(X - CX) <= 2) | (np.abs(Z - CZ) <= 2)) & (r > R_OUT)
    m |= (np.abs(r - PLAZA - 2) <= 2)
    m |= (Z >= QUAY_Z) & (Z <= QUAY_Z + 4)
    m |= (np.abs(Z - 150) <= 2) & (X > 30) & (X < 150)
    return m


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = SHORE(X, Z)
    hill = GY + 2 + np.clip(NT.fbm(X, Z, 3122, 28) - 0.35, 0, 1) * 30
    h = hill * np.clip((d - 1.5) / 12.0, 0, 1)
    flat = np.clip((rad(X, Z) - 70) / 12.0, 0, 1)
    flat = np.maximum(flat, np.clip((Z - 150) / 10.0, 0, 1) * 0)
    h = GY * (1 - flat) + np.maximum(h, GY) * flat
    h = np.where(d < 10, np.minimum(h, GY * d / 10.0 + 0.4), h)
    h = np.where(Z < QUAY_Z, -4, h)
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
    return (SHORE(X, Z) > 1.5) & (np.asarray(Z) >= QUAY_Z)


def hy(x, z):
    return int(HMAP[min(max(x, 0), N - 1), min(max(z, 0), N - 1)])


def terrain(bb):
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SAND, 3131, mask=lambda X, Z: land(X, Z) & (height(X, Z) <= GY) & (SHORE(X, Z) < 8),
             under="minecraft:sandstone", core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, ROCK, 3132, mask=lambda X, Z: land(X, Z) & steep(X, Z), under="minecraft:stone",
             core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, NT.MEADOW, 3133,
             mask=lambda X, Z: land(X, Z) & ~steep(X, Z) & ((height(X, Z) > GY) | (SHORE(X, Z) >= 8)), core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, STREET, 3134,
             mask=lambda X, Z: land(X, Z) & (streets(X, Z) | (rad(X, Z) <= PLAZA)), core="minecraft:stone")
    bed = lambda X, Z: np.where(np.asarray(Z) < QUAY_Z, np.minimum(-4 - np.clip((QUAY_Z - np.asarray(Z)) * 0.5, 0, 6),
                                                                    np.round(-2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10))),
                                np.round(-2 - np.clip(-SHORE(X, Z) * 0.6, 0, 10)))
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy == bed(X, Z)), "minecraft:sand")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, yy, Z: (~land(X, Z)) & (yy < bed(X, Z)) & (yy >= bed(X, Z) - 2), "minecraft:stone")


# ------------------------------------------------------------------ the colosseum
def _bay(X, Z, r=R_OUT - 1):
    """Position across the bay at radius r: u = 0 in the middle of a bay, +-half at the half-columns."""
    a = np.arctan2(np.asarray(Z, float) - CZ, np.asarray(X, float) - CX)
    f = (a / (2 * math.pi / NB)) % 1.0
    return (f - 0.5) * (2 * math.pi * r / NB)


def _hash(X, yy, Z, s):
    return ((np.asarray(X) * 73856093 ^ np.asarray(yy) * 19349663 ^ np.asarray(Z) * 83492791 ^ s) & 1023) / 1023.0


def drum(bb):
    """The outer wall, its arcades and half-columns, the cornice bands, the attic and the flag crown."""
    x1, z1, x2, z2 = CX - R_OUT - 2, CZ - R_OUT - 2, CX + R_OUT + 2, CZ + R_OUT + 2
    bb.fill_where(x1, GY - 3, z1, x2, GY, z2, lambda X, yy, Z: rad(X, Z) <= R_OUT + 1, "minecraft:cut_sandstone")
    wall = lambda X, yy, Z: (rad(X, Z) > R_WALL - 0.5) & (rad(X, Z) <= R_OUT)
    bb.fill_where(x1, GY + 1, z1, x2, TOPY, z2, wall, "minecraft:smooth_sandstone")
    bb.fill_where(x1, GY + 1, z1, x2, TOPY, z2, lambda X, yy, Z: wall(X, yy, Z) & (_hash(X, yy, Z, 5) < 0.35), "minecraft:cut_sandstone")
    bb.fill_where(x1, GY + 1, z1, x2, TOPY, z2, lambda X, yy, Z: wall(X, yy, Z) & (_hash(X, yy, Z, 9) < 0.08), "minecraft:sandstone")
    # half-columns between the bays, standing proud of the wall
    half = math.pi * (R_OUT - 1) / NB
    col = lambda X, yy, Z: (rad(X, Z) > R_OUT - 0.5) & (rad(X, Z) <= R_OUT + 1) & (np.abs(_bay(X, Z)) >= half - 1.2)
    bb.fill_where(x1, GY + 1, z1, x2, TOPY - 1, z2, col, "minecraft:cut_red_sandstone")
    for k, y in enumerate((GY + 1, L1, L2, TOPY)):
        # orange cornice bands at each floor and the crown
        bb.fill_where(x1, y, z1, x2, y, z2, lambda X, yy, Z: (rad(X, Z) > R_WALL - 0.5) & (rad(X, Z) <= R_OUT + 1.6),
                      "minecraft:orange_terracotta" if k % 2 else "minecraft:smooth_red_sandstone")
    # the openings: round arches on the two lower storeys, square attic windows on the top one
    for k, y0 in enumerate((GY, L1, L2)):
        def opening(X, yy, Z, y0=y0, k=k):
            u = np.abs(_bay(X, Z))
            r = rad(X, Z)
            if k < 2:
                dy = yy - y0
                w = np.where(dy <= 6, 2.4, np.where(dy == 7, 1.6, np.where(dy == 8, 0.6, -1)))
                return (r > R_WALL - 0.5) & (r <= R_OUT + 1.6) & (dy >= 1) & (u <= w)
            dy = yy - y0
            return (r > R_WALL - 0.5) & (r <= R_OUT + 1.6) & (dy >= 4) & (dy <= 6) & (u <= 1.0)
        bb.fill_where(x1, y0 + 1, z1, x2, y0 + 9, z2, opening, AIR)
    # balustrade in the first-floor arches
    bb.fill_where(x1, L1 + 1, z1, x2, L1 + 1, z2,
                  lambda X, yy, Z: (rad(X, Z) > R_OUT - 1.5) & (rad(X, Z) <= R_OUT) & (np.abs(_bay(X, Z)) <= 2.4),
                  "minecraft:sandstone_wall")
    # crown: a parapet with merlons, flagpoles with red and yellow flags
    bb.fill_where(x1, TOPY + 1, z1, x2, TOPY + 2, z2,
                  lambda X, yy, Z: (rad(X, Z) > R_OUT - 1) & (rad(X, Z) <= R_OUT + 0.5) & ((yy == TOPY + 1) | (np.abs(_bay(X, Z)) < 1.5)),
                  "minecraft:cut_sandstone")
    for k in range(16):
        a = 2 * math.pi * (k + 0.5) / 16
        fx, fz = int(round(CX + (R_OUT - 1) * math.cos(a))), int(round(CZ + (R_OUT - 1) * math.sin(a)))
        bb.fill(fx, TOPY + 1, fz, fx, TOPY + 9, fz, "minecraft:spruce_fence")
        bb.set(fx, TOPY + 10, fz, "minecraft:gold_block") if k % 4 == 0 else None
        cols = ("minecraft:red_wool", "minecraft:yellow_wool") if k % 2 else ("minecraft:yellow_wool", "minecraft:red_wool")
        # the flag hangs off the side away from the wind, along the wall tangent
        tx, tz = -math.sin(a), math.cos(a)
        for s in range(1, 5):
            for h in range(3):
                px, pz = int(round(fx + tx * s)), int(round(fz + tz * s))
                bb.set(px, TOPY + 9 - h, pz, cols[(h + s // 2) % 2])


def bowl(bb):
    """Everything inside the outer wall: corridors, the cavea, the podium, the moat and the stage."""
    x1, z1, x2, z2 = CX - R_WALL, CZ - R_WALL, CX + R_WALL, CZ + R_WALL
    seat = lambda r: GY + 7 + np.round((np.clip(r, R_POD + 1, R_COR) - R_POD - 1) * 15.0 / (R_COR - R_POD - 1))
    # the solid of the stands from the podium to the corridor, under the seat surface
    bb.fill_where(x1, GY + 1, z1, x2, L2, z2,
                  lambda X, yy, Z: (rad(X, Z) > R_POD - 0.5) & (rad(X, Z) <= R_COR + 0.5) & (yy <= seat(rad(X, Z))),
                  "minecraft:sandstone")
    # seats: stair blocks facing the arena, a red row every fourth
    for face, cond in (("north", lambda dx, dz: (dz <= -np.abs(dx))), ("south", lambda dx, dz: (dz >= np.abs(dx))),
                       ("west", lambda dx, dz: (dx < -np.abs(dz))), ("east", lambda dx, dz: (dx > np.abs(dz)))):
        for blk, which in (("minecraft:sandstone_stairs", 0), ("minecraft:red_sandstone_stairs", 1)):
            def seatf(X, yy, Z, cond=cond, which=which):
                r = rad(X, Z)
                row = np.round((np.clip(r, R_POD + 1, R_COR) - R_POD - 1) * 15.0 / (R_COR - R_POD - 1))
                ok = (r > R_POD + 1.5) & (r <= R_COR - 0.5) & (yy == seat(r) + 1) & cond(np.asarray(X) - CX, np.asarray(Z) - CZ)
                return ok & (((row % 4) == 3) == bool(which))
            # stairs climb away from the centre: facing is the outward direction
            bb.fill_where(x1, GY + 8, z1, x2, L2 + 1, z2, seatf, f"{blk}[facing={face},half=bottom]")
    # radial aisles every 45 degrees (plain steps of solid block, a lantern post at the top)
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        for r in range(R_POD + 2, R_COR + 1):
            x, z = int(round(CX + r * math.cos(a))), int(round(CZ + r * math.sin(a)))
            for ox, oz in ((0, 0), (1, 0), (0, 1)):
                y = int(seat(np.hypot(x + ox - CX, z + oz - CZ)))
                bb.set(x + ox, y + 1, z + oz, "minecraft:cut_sandstone")
                bb.set(x + ox, y + 2, z + oz, AIR)
    # the promenade at the top of the bowl and the floor of the first-floor ring
    bb.fill_where(x1, L2, z1, x2, L2, z2, lambda X, yy, Z: (rad(X, Z) > R_COR - 0.5) & (rad(X, Z) <= R_WALL), "minecraft:polished_granite")
    bb.fill_where(x1, L2 + 1, z1, x2, L2 + 1, z2, lambda X, yy, Z: (rad(X, Z) > R_COR - 0.5) & (rad(X, Z) <= R_COR + 0.5),
                  "minecraft:sandstone_wall")
    bb.fill_where(x1, L1, z1, x2, L1, z2, lambda X, yy, Z: (rad(X, Z) > R_COR - 0.5) & (rad(X, Z) <= R_WALL), "minecraft:smooth_sandstone")
    bb.fill_where(x1, GY + 1, z1, x2, L2 - 1, z2, lambda X, yy, Z: (rad(X, Z) > R_COR - 0.5) & (rad(X, Z) <= R_COR + 0.5) & (yy != L1),
                  "minecraft:cut_sandstone")
    # podium wall with a railing; the moat of fighting fish; the round stage
    bb.fill_where(x1, GY - 6, z1, x2, GY + 7, z2, lambda X, yy, Z: (rad(X, Z) > R_POD - 0.5) & (rad(X, Z) <= R_POD + 1.5),
                  "minecraft:stone_bricks")
    bb.fill_where(x1, GY + 7, z1, x2, GY + 7, z2, lambda X, yy, Z: (rad(X, Z) > R_POD - 0.5) & (rad(X, Z) <= R_POD + 1.5),
                  "minecraft:smooth_red_sandstone")
    bb.fill_where(x1, GY + 8, z1, x2, GY + 8, z2, lambda X, yy, Z: (rad(X, Z) > R_POD + 0.5) & (rad(X, Z) <= R_POD + 1.5),
                  "minecraft:red_sandstone_wall")
    bb.fill_where(x1, GY - 7, z1, x2, GY - 7, z2, lambda X, yy, Z: rad(X, Z) <= R_POD + 1.5, "minecraft:stone")
    bb.fill_where(x1, GY - 6, z1, x2, GY, z2, lambda X, yy, Z: (rad(X, Z) > R_MOAT + 0.5) & (rad(X, Z) <= R_POD - 0.5) & (yy < GY),
                  "minecraft:water")
    bb.fill_where(x1, GY, z1, x2, GY, z2, lambda X, yy, Z: (rad(X, Z) > R_MOAT + 0.5) & (rad(X, Z) <= R_POD - 0.5), AIR)
    bb.fill_where(x1, GY - 6, z1, x2, GY - 6, z2, lambda X, yy, Z: (rad(X, Z) > R_MOAT + 0.5) & (rad(X, Z) <= R_POD - 0.5),
                  "minecraft:sand")
    bb.fill_where(x1, GY - 6, z1, x2, GY + 1, z2, lambda X, yy, Z: rad(X, Z) <= R_MOAT + 0.5, "minecraft:stone_bricks")
    bb.fill_where(x1, GY + 1, z1, x2, GY + 1, z2, lambda X, yy, Z: rad(X, Z) <= R_MOAT + 0.5, "minecraft:polished_andesite")
    bb.fill_where(x1, GY + 1, z1, x2, GY + 1, z2,
                  lambda X, yy, Z: (np.abs(rad(X, Z) - 9.5) < 0.6) | (np.abs(rad(X, Z) - 15.5) < 0.6) | (np.abs(rad(X, Z) - R_MOAT) < 0.6) | (rad(X, Z) < 1.6),
                  "minecraft:polished_deepslate")
    bb.fill_where(x1, GY + 1, z1, x2, GY + 1, z2, lambda X, yy, Z: (np.abs(rad(X, Z) - 4) < 0.6), "minecraft:smooth_red_sandstone")
    # kelp and sea grass in the moat
    rng = np.random.default_rng(3140)
    for _ in range(90):
        a = rng.random() * 2 * math.pi
        r = rng.uniform(R_MOAT + 1.5, R_POD - 1.5)
        x, z = int(round(CX + r * math.cos(a))), int(round(CZ + r * math.sin(a)))
        if rng.random() < 0.5:
            bb.set(x, GY - 5, z, "minecraft:seagrass")
        else:
            hgt = int(rng.integers(1, 4))
            for y in range(GY - 5, GY - 5 + hgt):
                bb.set(x, y, z, "minecraft:kelp_plant")
            bb.set(x, GY - 5 + hgt, z, "minecraft:kelp[age=20]")


def gates(bb):
    """The four fighters' gates: tunnels through the drum and the stands, walkways over the moat to the stage."""
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for r in range(R_POD - 1, R_OUT + 3):
            for p in range(-2, 3):
                x, z = CX + dx * r + (dz != 0) * p, CZ + dz * r + (dx != 0) * p
                bb.fill(x, GY + 1, z, x, GY + 5, z, AIR)
                bb.set(x, GY, z, "minecraft:polished_granite")
                if abs(p) == 2 and r > R_POD + 1 and r < R_COR:
                    bb.set(x, GY + 4, z, "minecraft:wall_torch[facing=" + ("east" if (p < 0) == (dz != 0) else "west") + "]") \
                        if False else None
            if r in (R_POD + 3, R_COR - 3):
                # a portcullis rail and lamps
                for p in (-2, 2):
                    x, z = CX + dx * r + (dz != 0) * p, CZ + dz * r + (dx != 0) * p
                    bb.set(x, GY + 5, z, "minecraft:lantern[hanging=true]")
        # arched head over the outer mouth
        for p in range(-3, 4):
            x, z = CX + dx * (R_OUT + 1) + (dz != 0) * p, CZ + dz * (R_OUT + 1) + (dx != 0) * p
            if abs(p) == 3:
                bb.fill(x, GY + 1, z, x, GY + 8, z, "minecraft:cut_red_sandstone")
            bb.set(x, GY + 8, z, "minecraft:smooth_red_sandstone")
        # walkway over the moat
        for r in range(R_MOAT, R_POD):
            for p in range(-1, 2):
                x, z = CX + dx * r + (dz != 0) * p, CZ + dz * r + (dx != 0) * p
                bb.set(x, GY + 1, z, "minecraft:spruce_planks")
                bb.fill(x, GY - 6, z, x, GY, z, "minecraft:stone_bricks") if r % 4 == 0 and p == 0 else None
            for p in (-2, 2):
                x, z = CX + dx * r + (dz != 0) * p, CZ + dz * r + (dx != 0) * p
                bb.set(x, GY + 1, z, "minecraft:spruce_slab[type=top]")
                bb.set(x, GY + 2, z, "minecraft:spruce_fence")


def royal_box(bb):
    """The royal box on the north side: a carved loge in the stands with a red canopy, gold posts and the throne."""
    y = GY + 12
    x1, x2 = CX - 7, CX + 7
    z1, z2 = CZ - R_COR + 2, CZ - R_POD - 2
    bb.fill(x1, GY + 1, z1, x2, y, z2, "minecraft:sandstone")
    bb.fill(x1, y + 1, z1, x2, y + 7, z2, AIR)
    bb.fill(x1, y, z1, x2, y, z2, "minecraft:smooth_quartz")
    bb.fill(x1 + 1, y, z1 + 1, x2 - 1, y, z2 - 1, "minecraft:red_wool")
    bb.fill(x1, y + 1, z2, x2, y + 1, z2, "minecraft:gold_block")
    bb.fill(x1 + 1, y + 2, z2, x2 - 1, y + 2, z2, "minecraft:red_stained_glass_pane")
    for x in (x1, x2):
        bb.fill(x, y + 1, z1, x, y + 7, z2, "minecraft:cut_sandstone")
        bb.fill(x, y + 1, z2, x, y + 6, z2, "minecraft:gold_block")
    bb.fill(x1 - 1, y + 7, z1, x2 + 1, y + 7, z2 + 1, "minecraft:red_wool")
    bb.fill(x1, y + 8, z1 + 1, x2, y + 8, z2, "minecraft:red_wool")
    bb.fill(x1 + 2, y + 9, z1 + 3, x2 - 2, y + 9, z2 - 1, "minecraft:yellow_wool")
    for x in range(x1 - 1, x2 + 2):
        if x % 2 == 0:
            bb.set(x, y + 6, z2 + 1, "minecraft:yellow_wool")
    # throne and the king's seats
    bb.set(CX, y + 1, z1 + 2, st("minecraft:quartz_stairs", "north"))
    bb.fill(CX - 1, y + 1, z1 + 1, CX + 1, y + 3, z1 + 1, "minecraft:gold_block")
    bb.set(CX, y + 4, z1 + 1, "minecraft:gold_block")
    bb.set(CX - 1, y + 1, z1 + 2, "minecraft:red_carpet"); bb.set(CX + 1, y + 1, z1 + 2, "minecraft:red_carpet")
    for x in (CX - 5, CX - 3, CX + 3, CX + 5):
        bb.set(x, y + 1, z1 + 3, st("minecraft:dark_oak_stairs", "north"))
    bb.set(CX - 6, y + 1, z1 + 1, "minecraft:potted_red_tulip"); bb.set(CX + 6, y + 1, z1 + 1, "minecraft:potted_orange_tulip")
    bb.set(x1 + 1, y + 6, z1 + 3, "minecraft:lantern[hanging=true]"); bb.set(x2 - 1, y + 6, z1 + 3, "minecraft:lantern[hanging=true]")
    # a passage from the promenade into the back of the box
    bb.fill(CX - 1, y + 1, CZ - R_WALL + 1, CX + 1, y + 3, z1, AIR)
    bb.fill(CX - 1, L1 + 1, CZ - R_WALL + 1, CX + 1, y, CZ - R_COR + 1, AIR)
    for i in range(y - L1):
        bb.fill(CX - 1, L1 + 1 + i, CZ - R_COR - 1 + i, CX + 1, L1 + 1 + i, CZ - R_COR - 1 + i, st("minecraft:sandstone_stairs", "south"))
        bb.fill(CX - 1, L1 + 2 + i, CZ - R_COR - 1 + i, CX + 1, L1 + 4 + i, CZ - R_COR - 1 + i, AIR)


def commentator_box(bb):
    """Gatz's commentator box on the south side: a glazed booth over the stands with a Den Den Mushi microphone."""
    y = GY + 11
    x1, x2 = CX - 4, CX + 4
    z1, z2 = CZ + R_POD + 6, CZ + R_POD + 11
    bb.fill(x1, GY + 6, z1, x2, y, z2, "minecraft:sandstone")
    bb.fill(x1, y + 1, z1, x2, y + 5, z2, "minecraft:cut_sandstone")
    bb.fill(x1 + 1, y + 1, z1 + 1, x2 - 1, y + 4, z2 - 1, AIR)
    bb.fill(x1 + 1, y + 2, z1, x2 - 1, y + 4, z1, "minecraft:glass_pane")
    bb.fill(x1, y + 6, z1 - 1, x2, y + 6, z2, "minecraft:orange_terracotta")
    bb.fill(x1 + 1, y + 1, z1 + 1, x2 - 1, y + 1, z1 + 1, "minecraft:spruce_slab[type=top]")
    bb.set(CX, y + 2, z1 + 1, "minecraft:snail_shell" if False else "minecraft:turtle_egg[eggs=1]")
    bb.set(CX - 1, y + 1, z1 + 2, st("minecraft:spruce_stairs", "south")); bb.set(CX + 1, y + 1, z1 + 2, st("minecraft:spruce_stairs", "south"))
    bb.set(CX, y + 4, CZ + R_POD + 8, "minecraft:lantern[hanging=true]")
    bb.fill(CX, y + 1, z2, CX, y + 2, z2 + 6, AIR)


def under_rooms(bb, tracker, audit):
    """Eight rooms under the stands, each with a passage out to the ground ring corridor."""
    kinds = ["bedroom", "storage", "kitchen", "workshop", "bedroom", "library", "storage", "dining"]
    names = ["barracks", "armory", "kitchen", "doctor", "barracks2", "trophy", "cells", "mess"]
    rooms = []
    h = 5
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        rx, rz = int(round(CX + 28 * math.cos(a))), int(round(CZ + 28 * math.sin(a)))
        x1, z1, x2, z2 = rx - 4, rz - 4, rx + 4, rz + 4
        bb.fill(x1 - 1, GY, z1 - 1, x2 + 1, GY + h + 1, z2 + 1, "minecraft:stone_bricks")
        bb.fill(x1, GY, z1, x2, GY, z2, "minecraft:spruce_planks" if k % 2 else "minecraft:polished_andesite")
        bb.fill(x1, GY + 1, z1, x2, GY + h, z2, AIR)
        # passage outward along the dominant axis to the corridor
        dx, dz = (1 if rx > CX else -1, 0) if abs(rx - CX) > abs(rz - CZ) else (0, 1 if rz > CZ else -1)
        if dx:
            xa = x2 + 1 if dx > 0 else x1 - 1
            xb = CX + dx * (R_COR + 1)
            bb.fill(min(xa, xb), GY + 1, rz, max(xa, xb), GY + 2, rz, AIR)
            doors = [(xa, rz)]
        else:
            za = z2 + 1 if dz > 0 else z1 - 1
            zb = CZ + dz * (R_COR + 1)
            bb.fill(rx, GY + 1, min(za, zb), rx, GY + 2, max(za, zb), AIR)
            doors = [(rx, za)]
        if names[k] == "cells":
            for x in range(x1, x2 + 1, 3):
                bb.fill(x, GY + 1, z1, x, GY + h, z2, "minecraft:iron_bars")
            bb.fill(x1, GY + 1, rz, x2, GY + 3, rz, AIR)
            for x in range(x1 + 1, x2, 3):
                bb.set(x, GY + 1, z1, "minecraft:white_wool"); bb.set(x, GY + 1, z2, "minecraft:chain[axis=y]") if False else None
            bb.set(rx, GY + h, rz, "minecraft:lantern[hanging=true]")
        elif names[k] == "trophy":
            bb.fill(rx - 1, GY + 1, rz - 1, rx + 1, GY + 1, rz + 1, "minecraft:polished_deepslate")
            bb.set(rx, GY + 2, rz, "minecraft:gold_block")
            bb.set(rx, GY + 3, rz, "onepiece:mera_mera_fruit" if False else "minecraft:candle[candles=4,lit=true]")
            for (ox, oz) in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
                bb.set(rx + ox, GY + 1, rz + oz, "minecraft:armor_stand" if False else "minecraft:polished_blackstone_wall")
                bb.set(rx + ox, GY + 2, rz + oz, "minecraft:lantern[hanging=false]")
            bb.fill(x1, GY + 1, z1, x2, GY + 1, z1, "minecraft:red_carpet") if False else None
        else:
            rooms.append(((x1, z1, x2, z2), kinds[k], doors))
    for (r, kind, doors) in rooms:
        P.furnish_room(bb, r, GY + 1, kind, height=h, seed=seed_of("ccr", r[0], r[1]), doors=doors, wood="spruce", tracker=tracker)
        txt, ok = P.audit_props(bb, [r], GY + 1, h)
        if not ok:
            audit.append(txt)


def corridors(bb, tracker):
    """Lamps in the ground ring, kiosks on the first floor, a stair tower in each diagonal."""
    for k in range(24):
        a = 2 * math.pi * k / 24
        x, z = int(round(CX + (R_COR + 1.5) * math.cos(a))), int(round(CZ + (R_COR + 1.5) * math.sin(a)))
        bb.set(x, L1 - 1, z, "minecraft:lantern[hanging=true]")
        bb.set(x, L2 - 1, z, "minecraft:lantern[hanging=true]")
    stalls = [("minecraft:red_wool", "minecraft:white_wool"), ("minecraft:yellow_wool", "minecraft:red_wool"),
              ("minecraft:lime_wool", "minecraft:white_wool")]
    for k in range(12):
        a = 2 * math.pi * (k + 0.25) / 12
        x, z = int(round(CX + (R_COR + 1.5) * math.cos(a))), int(round(CZ + (R_COR + 1.5) * math.sin(a)))
        bb.set(x, L1 + 1, z, "minecraft:barrel[facing=up,open=false]")
        bb.set(x, L1 + 2, z, "minecraft:spruce_fence")
        c1, c2 = stalls[k % 3]
        bb.set(x, L1 + 3, z, c1)
        for (ox, oz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if rad(x + ox, z + oz) > R_COR + 0.5:
                bb.set(x + ox, L1 + 1, z + oz, "minecraft:smoker[facing=north,lit=false]" if k % 2 else "minecraft:barrel[facing=up,open=false]")
                bb.set(x + ox, L1 + 3, z + oz, c2)
                break
    for k in range(4):
        a = 2 * math.pi * (k + 0.5) / 4
        x, z = int(round(CX + 40 * math.cos(a))) - 1, int(round(CZ + 40 * math.sin(a))) - 1
        stair_core(bb, x, z, 3, GY + 1, L2, [L1 + 1, L2 + 1], "minecraft:cut_sandstone", "minecraft:sandstone_stairs")


# ------------------------------------------------------------------ the town
def town(bb, tracker, audit, rng, taken):
    k = 0
    for _ in range(6000):
        w, d = int(rng.integers(8, 13)), int(rng.integers(8, 11))
        x0, z0 = int(rng.integers(TOWN[0], TOWN[2] - w)), int(rng.integers(TOWN[1], TOWN[3] - d))
        xs = np.arange(x0 - 1, x0 + w + 1)[:, None]; zs = np.arange(z0 - 1, z0 + d + 1)[None, :]
        if streets(xs, zs).any() or (~land(xs, zs)).any() or (SHORE(xs, zs) < 5).any() or (rad(xs, zs) < PLAZA + 5).any():
            continue
        hs = HMAP[np.clip(xs, 0, N - 1), np.clip(zs, 0, N - 1)]
        if hs.max() - hs.min() > 2:
            continue
        box = (x0 - 1, z0 - 1, x0 + w, z0 + d)
        if any(box[0] <= r[2] and r[0] <= box[2] and box[1] <= r[3] and r[1] <= box[3] for r in taken):
            continue
        # face the colosseum (or the harbour front when close to it)
        mx, mz = x0 + w / 2 - CX, z0 + d / 2 - CZ
        if z0 < QUAY_Z + 18:
            rot = 2
        elif abs(mx) > abs(mz):
            rot = 3 if mx < 0 else 1
        else:
            rot = 0 if mz < 0 else 2
        mw, md = (w, d) if rot % 2 == 0 else (d, w)
        fl = int(rng.integers(2, 4))
        y = int(hs.max())
        roof = ROOFS[k % len(ROOFS)] if k % 4 else "flat:" + ("red", "yellow", "orange")[k % 3]
        m, top, au = house_module(seed_of("cc", x0, z0), mw, md, fl, roof, tracker, KINDS[k % len(KINDS)], pal=PALS[k % len(PALS)],
                                  timber=(k % 5 == 2), jetty=(k % 3 == 0), chimney=(k % 2 == 0))
        audit += au
        bb.fill(x0, y - 3, z0, x0 + w - 1, y, z0 + d - 1, "minecraft:cut_sandstone")
        place_house(bb, m, mw, md, x0, y, z0, rot)
        taken.append(box)
        k += 1
        if k >= 46:
            break
    print("houses:", k)


def plaza(bb, rng):
    """The plaza round the drum: lamp posts, flower beds, orange trees in planters, a fountain at each avenue."""
    for k in range(32):
        a = 2 * math.pi * (k + 0.5) / 32
        x, z = int(round(CX + (R_OUT + 4) * math.cos(a))), int(round(CZ + (R_OUT + 4) * math.sin(a)))
        if k % 2:
            lamp_post(bb, x, GY + 1, z)
        else:
            bb.set(x, GY + 1, z, "minecraft:flowering_azalea_leaves[persistent=true]")
            bb.set(x, GY + 2, z, "minecraft:flowering_azalea_leaves[persistent=true]") if k % 4 == 0 else None
    for (dx, dz) in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        fx, fz = int(CX + dx * (R_OUT + 6) * 0.7071), int(CZ + dz * (R_OUT + 6) * 0.7071)
        bb.cylinder(fx, GY + 1, fz, 3, GY + 1, "minecraft:cut_sandstone")
        bb.cylinder(fx, GY + 1, fz, 2, GY + 1, "minecraft:water")
        bb.fill(fx, GY + 1, fz, fx, GY + 3, fz, "minecraft:cut_sandstone")
        bb.set(fx, GY + 4, fz, "minecraft:water")
        bb.set(fx, GY + 5, fz, AIR) if False else None


def harbour(bb, rng):
    for x in range(0, N):
        if SHORE(np.array([[x]]), np.array([[QUAY_Z + 2]]))[0, 0] < 1.5:
            continue
        bb.fill(x, -6, QUAY_Z, x, GY, QUAY_Z, "minecraft:stone_bricks")
        bb.set(x, GY, QUAY_Z, "minecraft:polished_granite")
        if x % 7 == 0:
            bb.set(x, GY + 1, QUAY_Z, "minecraft:stone_brick_wall")
    for px in (40, 132):
        for z in range(QUAY_Z - 16, QUAY_Z):
            bb.fill(px - 1, GY - 1, z, px + 1, GY - 1, z, "minecraft:spruce_planks")
            if (QUAY_Z - z) % 5 == 0:
                for p in (px - 2, px + 2):
                    bb.fill(p, -9, z, p, GY - 1, z, "minecraft:spruce_log[axis=y]")
                    bb.set(p, GY, z, "minecraft:lantern[hanging=false]")
    stamp_ship(bb, "marine_warship", 88, QUAY_Z - 14, water_y=0, rot=0)
    for x in (20, 26, 150, 156):
        bb.fill(x - 1, 0, QUAY_Z - 5, x + 1, 0, QUAY_Z - 2, "minecraft:spruce_planks")
        bb.fill(x - 1, 1, QUAY_Z - 6, x + 1, 1, QUAY_Z - 1, "minecraft:spruce_slab[type=bottom]")
        bb.fill(x, 1, QUAY_Z - 5, x, 1, QUAY_Z - 2, AIR)
    for (x, z) in ((60, QUAY_Z + 2), (61, QUAY_Z + 2), (114, QUAY_Z + 2), (115, QUAY_Z + 3)):
        bb.set(x, GY + 1, z, "minecraft:barrel[facing=up,open=false]")


def sunflowers(bb, rng, taken):
    """The sunflower fields on the southern slopes: rows of sunflowers between hay-coloured paths."""
    n = 0
    for x in range(6, N - 6):
        for z in range(110, N - 6):
            X, Z = np.array([[x]]), np.array([[z]])
            if not land(X, Z)[0, 0] or SHORE(X, Z)[0, 0] < 6 or GRAD[x, z] >= 2 or streets(X, Z)[0, 0] or rad(X, Z)[0, 0] < PLAZA + 4:
                continue
            if any(t[0] - 1 <= x <= t[2] + 1 and t[1] - 1 <= z <= t[3] + 1 for t in taken):
                continue
            if NT.fbm(X, Z, 3150, 22)[0, 0] < 0.5:
                continue
            y = hy(x, z)
            if z % 3 == 0:
                bb.set(x, y, z, "minecraft:farmland[moisture=7]") if False else bb.set(x, y, z, "minecraft:coarse_dirt")
                continue
            bb.set(x, y + 1, z, "minecraft:sunflower[half=lower]")
            bb.set(x, y + 2, z, "minecraft:sunflower[half=upper]")
            n += 1
    print("sunflowers:", n)


def scenery(bb, rng, taken):
    k = 0
    for _ in range(4000):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(QUAY_Z + 6, N - 4))
        X, Z = np.array([[x]]), np.array([[z]])
        if not land(X, Z)[0, 0] or SHORE(X, Z)[0, 0] < 6 or GRAD[x, z] >= 2 or streets(X, Z)[0, 0] or rad(X, Z)[0, 0] < PLAZA + 3:
            continue
        if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken):
            continue
        P.tree(bb, x, hy(x, z) + 1, z, int(rng.integers(5, 9)), ("oak", "birch", "acacia", "oak", "cherry")[k % 5], rng)
        taken.append((x - 3, z - 3, x + 3, z + 3))
        k += 1
        if k >= 55:
            break
    print("trees:", k)


def design():
    bb = BigBuild(seed=3120, y_min=-14, y_max=70)
    tracker = P.PropTracker(3120)
    audit = []
    rng = np.random.default_rng(3120)
    terrain(bb)
    drum(bb)
    bowl(bb)
    royal_box(bb)
    commentator_box(bb)
    under_rooms(bb, tracker, audit)
    corridors(bb, tracker)
    gates(bb)
    plaza(bb, rng)
    harbour(bb, rng)
    taken = [(0, 0, N, QUAY_Z + 5), (CX - PLAZA - 4, CZ - PLAZA - 4, CX + PLAZA + 4, CZ + PLAZA + 4)]
    taken = [(0, 0, N, QUAY_Z + 5)]
    town(bb, tracker, audit, rng, taken)
    sunflowers(bb, rng, taken)
    scenery(bb, rng, taken)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 3190, density=0.22, kinds=NT.PLANTS_MEADOW, flowers=NT.FLOWERS,
              mask=lambda X, Z: land(X, Z) & ~streets(X, Z) & (rad(X, Z) > PLAZA + 1))
    return bb, audit


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
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    steady(b)
    b.npc(CX, GY + 2, CZ, "fujitora", True)
    b.chest(CX, GY + 13, CZ - R_COR + 3, "hard", "south")
    tr = 2 * math.pi * 5.5 / 8
    b.chest(int(round(CX + 28 * math.cos(tr))) + 2, GY + 1, int(round(CZ + 28 * math.sin(tr))), "hard", "south")
    b.guards("gladiator", ((CX - 6, CZ - 6), (CX + 6, CZ - 6), (CX - 6, CZ + 6), (CX + 6, CZ + 6)), y=GY + 2)
    b.guards("gladiator", ((CX + R_OUT + 5, CZ), (CX - R_OUT - 5, CZ), (CX, CZ + R_OUT + 5)), y=GY + 1)
    return b, 0
