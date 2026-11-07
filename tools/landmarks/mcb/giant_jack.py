"""Giant Jack v3, the colossal beanstalk of Upper Yard, redone with the Minecraft Builder skill (2026-10-30 audit: the
v1 stalk was tiny next to the show).

The same beanstalk as the Shandora build (shandora.py v1 code, scaled up in mcb/shandora.py): three twisted strands,
15 thick at the roots tapering to 7, rising 150 blocks, broad bean leaves on stalks all the way up, a ladder shaft
inside with doors at the Upper Ruins cloud (64) and the top cloud (120). Round its foot a patch of Upper Yard
jungle: giant trees with plank buttresses, the Sky Priests' four ordeal grounds (Balls, Swamp, Strings, Iron), and
on the top cloud the priests' shrine with the sky treasure. The ground fades out at an irregular edge. 140 x 140.
Ground = y 0."""
import math
import random

import numpy as np

from canvas import B, AIR
from mcb.kit import BigBuild, P, seed_of, set_if_air
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb import shandora as SH
import shandora as OLD

SID = "giant_jack"
TITLE = "Giant Jack (the giant beanstalk)"
CUTS = [3, 64]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 10

N = 140
CX, CZ = 70, 70
ISLE = NT.outline(70, 70, 58, 4210, wobble=0.1)
ORDEALS = {"balls": (34, 40), "swamp": (106, 38), "strings": (32, 104), "iron": (108, 102)}


def land(X, Z):
    return ISLE(X, Z) > 0


def ground(bb):
    NT.cover(bb, 0, 0, N - 1, N - 1, lambda X, Z: np.zeros_like(X + Z), NT.JUNGLE, 4211, mask=land, core="minecraft:stone", base=-4)
    NT.plants(bb, 0, 0, N - 1, N - 1, lambda X, Z: np.zeros_like(X + Z), 4212, density=0.35, kinds=NT.PLANTS_JUNGLE,
              mask=lambda X, Z: land(X, Z) & (np.hypot(X - CX, Z - CZ) > 22))


def ordeal(bb, kind, x, z, rng):
    """One of the Sky Priests' four ordeal grounds, as a clearing with a stone marker."""
    r = 9
    bb.fill_where(x - r, 0, z - r, x + r, 0, z + r, lambda X, y, Z: np.hypot(X - x, Z - z) <= r, "onepiece:shandian_ruin_stone")
    bb.fill_where(x - r, 1, z - r, x + r, 6, z + r, lambda X, y, Z: np.hypot(X - x, Z - z) <= r, AIR)
    if kind == "balls":                 # Satori's ordeal: cloud balls, some hiding surprises
        for k in range(9):
            bx, bz = x + int(rng.integers(-6, 7)), z + int(rng.integers(-6, 7))
            bb.fill_where(bx - 2, 1, bz - 2, bx + 2, 5, bz + 2, lambda X, y, Z, bx=bx, bz=bz: (X - bx) ** 2 + (y - 3) ** 2 + (Z - bz) ** 2 <= 4,
                          "onepiece:cloud_puff" if k % 3 else "onepiece:island_cloud")
    elif kind == "swamp":               # Gedatsu's ordeal: a cloud swamp that swallows you
        bb.fill_where(x - r, -2, z - r, x + r, 0, z + r, lambda X, y, Z: np.hypot(X - x, Z - z) <= r - 1, "minecraft:mud")
        bb.fill_where(x - r, 0, z - r, x + r, 0, z + r, lambda X, y, Z: (np.hypot(X - x, Z - z) <= r - 2) & (NT.noise(X, Z, 4213, 3) > 0.45), "minecraft:water")
        for k in range(10):
            lx, lz = x + int(rng.integers(-6, 7)), z + int(rng.integers(-6, 7))
            set_if_air(bb, lx, 1, lz, "minecraft:lily_pad")
    elif kind == "strings":             # Shura's ordeal: strings strung between posts
        posts = [(x + round(7 * math.cos(a)), z + round(7 * math.sin(a))) for a in np.linspace(0, 2 * math.pi, 7)[:-1]]
        for (px, pz) in posts:
            bb.fill(px, 1, pz, px, 6, pz, "minecraft:jungle_log[axis=y]")
        for i, (px, pz) in enumerate(posts):
            qx, qz = posts[(i + 2) % len(posts)]
            for t in np.linspace(0, 1, 16):
                bb.set(round(px + (qx - px) * t), 4 + (i % 2), round(pz + (qz - pz) * t), "minecraft:cobweb")
    else:                               # Ohm's ordeal: the iron thorn maze
        for k in range(-6, 7, 3):
            bb.fill(x + k, 1, z - 6, x + k, 3, z + 6, "minecraft:iron_bars[east=false,north=true,south=true,west=false,waterlogged=false]")
            bb.fill(x + k, 1, z + (2 if k % 6 else -2), x + k, 3, z + (2 if k % 6 else -2), AIR)
    # the marker stone with a gold cap
    bb.fill(x - 1, 1, z - r - 1, x + 1, 3, z - r - 1, "onepiece:shandian_ruin_stone")
    bb.set(x, 4, z - r - 1, "onepiece:shandora_gold_bricks")


def design():
    bb = BigBuild(seed=421, y_min=-6, y_max=60)
    rng = np.random.default_rng(421)
    ground(bb)
    for k, (x, z) in ORDEALS.items():
        ordeal(bb, k, x, z, rng)
    taken = [(x - 11, z - 11, x + 11, z + 11) for (x, z) in ORDEALS.values()] + [(CX - 20, CZ - 20, CX + 20, CZ + 20)]
    n = 0
    for _ in range(2000):
        a, rr = rng.uniform(0, 2 * math.pi), rng.uniform(24, 52)
        x, z = round(CX + rr * math.cos(a)), round(CZ + rr * math.sin(a))
        if ISLE(np.array([x]), np.array([z]))[0] < 10 or any(t[0] - 3 <= x <= t[2] + 3 and t[1] - 3 <= z <= t[3] + 3 for t in taken):
            continue
        SH.sky_tree(bb, x, z, int(rng.integers(30, 48)), float(rng.uniform(2.2, 3.2)), rng)
        taken.append((x - 7, z - 7, x + 7, z + 7))
        n += 1
        if n >= 12:
            break
    return bb, []


def build():
    # the v1 Shandora beanstalk builders read these globals (mcb/shandora sets them for its own site at import)
    OLD.N, OLD.CX, OLD.CZ = N, CX, CZ
    OLD.TOPJ, OLD.U_Y, OLD.T_Y = 150, 64, 120
    OLD.jack_R = lambda y: 15.0 - 8.0 * min(1.0, max(0, y) / OLD.TOPJ)
    bb, audit = design()
    b = to_canvas(bb)
    rnd = random.Random(4214)
    OLD.giant_jack(b, rnd)
    OLD.upper_ruins(b, rnd)
    # the top cloud and the priests' shrine with the sky treasure
    OLD.cloud_shelf(b, CX + 11, CZ, 20, 15, OLD.T_Y, 6, rnd)
    top = BigBuild(seed=4215, y_min=-2, y_max=20)
    top.fill(CX + 4, 0, CZ - 8, CX + 22, 0, CZ + 8, SH.RUIN)
    SH.shrine(top, CX + 14, CZ, 7)
    to_canvas(top, b, dy=OLD.T_Y)
    b.chest(CX + 14, OLD.T_Y + 1, CZ - 4, "sky_treasure", "south")
    b.chest(CX - 7, OLD.U_Y + 1, CZ + 3, "medium", "east")
    b.guards("sky_priest", ((ORDEALS["balls"][0], ORDEALS["balls"][1] + 3), (ORDEALS["swamp"][0], ORDEALS["swamp"][1] + 3),
                            (ORDEALS["strings"][0], ORDEALS["strings"][1] + 3), (ORDEALS["iron"][0] + 3, ORDEALS["iron"][1])))
    return b, 0
