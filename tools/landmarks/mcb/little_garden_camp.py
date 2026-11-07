"""Little Garden v2, redesigned with the Minecraft Builder skill: the prehistoric jungle island where the giants Dorry
and Brogy of Elbaf have fought their duel for a hundred years.

A steaming jungle of giant trees, ferns taller than a man and clover the size of tables, ringed by a beach. In the
north the volcano, a black-and-ash cone with a glowing crater and smoke: each time it erupts the duel goes on. Below it
the duel ground, a clearing trampled bare with craters, split trees and the giants' marks. West: Dorry's camp, a
giant's tent of hides on a frame of whole tree trunks, a fur bed, a barrel of booze bigger than a house, a bonfire
with a dinosaur on the spit, his sword and round shield. East: Brogy's camp under the bleached skeleton of a giant Sea
King (ribs arching over the camp, the skull on the ground), his bonfire, barrels, axe and shield. A long-necked
dinosaur skeleton lies in the jungle; a river runs from the volcano's foot to the sea. South in the jungle Mr. 3's
Candle House, a wax hut, and the Candle Service Set, a tiered wax cake-stage with a spiral stair and a pumpkin top.
Giants are ~20 m tall, so their things are built to that scale. ~176 x 176. Ground = y 2, sea y 0. (v2)

v3 (2026-10-30, audit: "the trees are normal size, the show has a colossal prehistoric jungle"): 18 colossal trees
50-80 tall with trunks up to 13 across, buttress fins and wide flat crowns tower over the jungle, under them ~40
ordinary giant trees; the sea now fills only a round patch inside a wobbly rim."""
from mcb import terrain3 as T3
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, set_if_air, lamp_post, steady
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "little_garden_camp"
TITLE = "Little Garden (Dorry and Brogy's duel ground)"
CUTS = [3, 12, 24]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 176
TY = 2
VOLC = (88, 50, 42, 82)            # x, z, base radius, height
DUEL = (88, 106, 18)
DORRY = (42, 108)
BROGY = (134, 108)
CANDLE = (62, 146)
SERVICE = (112, 146)
DINO = (126, 70)
_ISLE = NT.outline(88, 90, 70, 13010, wobble=0.08)
JUNGLE = [("minecraft:grass_block", 0.5), ("onepiece:jungle_loam", 0.14), ("minecraft:moss_block", 0.12), ("minecraft:podzol", 0.12),
          ("minecraft:rooted_dirt", 0.06), ("minecraft:coarse_dirt", 0.06)]
DUELG = [("minecraft:coarse_dirt", 0.4), ("minecraft:dirt", 0.2), ("minecraft:grass_block", 0.18), ("minecraft:rooted_dirt", 0.12),
         ("minecraft:gravel", 0.1)]
SAND = [("minecraft:sand", 0.82), ("minecraft:clay", 0.12), ("minecraft:gravel", 0.06)]
ASH = [("minecraft:tuff", 0.3), ("onepiece:volcanic_ash", 0.25), ("minecraft:basalt[axis=y]", 0.15), ("minecraft:blackstone", 0.15),
       ("minecraft:andesite", 0.15)]


def _river(X, Z):
    """Distance to the river's centre line: from the volcano foot (70, 74) west and south to the sea."""
    t = np.clip((70 - X) / 60.0, 0, 1)
    cz = 74 + 40 * t ** 1.4 + 6 * np.sin(t * 6)
    return np.where((X <= 72) & (X >= 4), np.abs(Z - cz), 99)


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = _ISLE(X, Z)
    vx, vz, vr, vh = VOLC
    r = np.hypot(X - vx, Z - vz) * (1 + 0.08 * NT.noise(X, Z, 13011, 7))
    cone = vh * np.clip(1 - r / vr, 0, 1) ** 1.25
    crater = np.where(r < 7, vh - 6 - (7 - r) * 0.4 - cone, 0)
    roll = TY + NT.fbm(X, Z, 13012, 20) * 5 - 1.5
    h = np.where(d < 10, TY * np.clip(d / 10.0, 0, 1) + 0.3, roll)
    h = np.maximum(h, np.where(d >= 6, TY + cone + crater, h))
    # the duel ground and the camps are flat
    for (cx, cz, rr) in ((DUEL[0], DUEL[1], DUEL[2] + 6), (DORRY[0], DORRY[1], 22), (BROGY[0], BROGY[1], 24), (CANDLE[0], CANDLE[1], 12),
                         (SERVICE[0], SERVICE[1], 13)):
        f = np.clip(1 - (np.hypot(X - cx, Z - cz) - rr) / 8.0, 0, 1)
        h = h * (1 - f) + TY * f
    rv = _river(X, Z)
    h = np.where((rv < 3.5) & (d >= 3), np.minimum(h, TY - 2), h)
    return np.where(d < 1.5, -1, np.round(h))


X_, Z_ = np.arange(N)[:, None].astype(float), np.arange(N)[None, :].astype(float)
HMAP, SHORE = _height(X_, Z_).astype(int), _ISLE(X_, Z_)
RIVER = _river(X_, Z_)


def height(X, Z):
    return HMAP[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def sh(X, Z):
    return SHORE[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def riv(X, Z):
    return RIVER[np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)]


def land(X, Z):
    return sh(X, Z) > 1.5


def hy(x, z):
    return int(HMAP[min(max(int(x), 0), N - 1), min(max(int(z), 0), N - 1)])


def volc_r(X, Z):
    return np.hypot(np.asarray(X, float) - VOLC[0], np.asarray(Z, float) - VOLC[1])


def duel(X, Z):
    return np.hypot(np.asarray(X, float) - DUEL[0], np.asarray(Z, float) - DUEL[1]) < DUEL[2] + 3 * NT.noise(np.asarray(X, float), np.asarray(Z, float), 13013, 6)


def terrain(bb):
    vol = lambda X, Z: land(X, Z) & (volc_r(X, Z) < VOLC[2] * (0.72 + 0.2 * NT.noise(X, Z, 13014, 6)))
    beach = lambda X, Z: land(X, Z) & (sh(X, Z) < 8)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SAND, 13020, mask=lambda X, Z: beach(X, Z) & ~vol(X, Z), under="minecraft:sandstone", core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, ASH, 13021, mask=lambda X, Z: land(X, Z) & vol(X, Z), under="minecraft:tuff", core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, DUELG, 13022, mask=lambda X, Z: land(X, Z) & ~beach(X, Z) & ~vol(X, Z) & duel(X, Z),
             core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, JUNGLE, 13023, mask=lambda X, Z: land(X, Z) & ~beach(X, Z) & ~vol(X, Z) & ~duel(X, Z),
             core="minecraft:stone")
    T3.sea(bb, N, land(X_, Z_), 88, 88, 87, 13019, deep=-14, shelf=12, y_min=-14)
    # the river: water down to sea level in its bed (explicit air above so nothing covers it)
    rm = lambda X, Z: land(X, Z) & (riv(X, Z) < 3.5)
    bb.fill_where(0, -3, 0, N - 1, TY + 6, N - 1, lambda X, Y, Z: rm(X, Z) & (Y > height(X, Z)) & (Y > 0), AIR)
    bb.fill_where(0, -3, 0, N - 1, 0, N - 1, lambda X, Y, Z: rm(X, Z) & (riv(X, Z) < 2.6) & (Y >= -1) & (Y <= 0), "minecraft:water")
    bb.fill_where(0, -3, 0, N - 1, 0, N - 1, lambda X, Y, Z: rm(X, Z) & (riv(X, Z) < 2.6) & (Y == -2), "minecraft:mud")
    bb.fill_where(0, -3, 0, N - 1, 0, N - 1, lambda X, Y, Z: rm(X, Z) & (riv(X, Z) >= 2.6) & (Y <= 0) & (Y >= -2), "minecraft:mud")


# ------------------------------------------------------------------ the volcano
def volcano(bb, rng):
    vx, vz, vr, vh = VOLC
    top = TY + vh
    # the crater: a bowl of magma with a lava pool sealed in basalt, glowing rim, smoke from campfires on hay
    bb.fill_where(vx - 14, top - 12, vz - 14, vx + 14, top + 2, vz + 14, lambda X, Y, Z: (np.hypot(X - vx, Z - vz) < 5.2 + np.maximum(Y - (top - 6), 0) * 0.9) & (Y > top - 9), AIR)
    bb.fill_where(vx - 8, top - 12, vz - 8, vx + 8, top - 9, vz + 8, lambda X, Y, Z: np.hypot(X - vx, Z - vz) < 6.2, "minecraft:basalt[axis=y]")
    bb.fill_where(vx - 8, top - 9, vz - 8, vx + 8, top - 9, vz + 8, lambda X, Y, Z: np.hypot(X - vx, Z - vz) < 4.2, "minecraft:lava")
    bb.fill_where(vx - 8, top - 9, vz - 8, vx + 8, top - 9, vz + 8,
                  lambda X, Y, Z: (np.hypot(X - vx, Z - vz) >= 4.2) & (np.hypot(X - vx, Z - vz) < 5.4), "minecraft:magma_block")
    for k in range(7):
        a = 2 * math.pi * k / 7 + 0.3
        x, z = int(round(vx + 3 * math.cos(a))), int(round(vz + 3 * math.sin(a)))
        if k % 2 == 0:
            bb.set(x, top - 10, z, "minecraft:hay_block")
            bb.set(x, top - 9, z, "minecraft:campfire[lit=true,signal_fire=true,facing=north]")
    # lava streaks down the slope (magma + blackstone channels) and scattered obsidian
    for k in range(5):
        a = rng.uniform(0, 2 * math.pi)
        for s in range(6, int(vr * 0.7)):
            x, z = int(round(vx + s * math.cos(a) + 1.5 * math.sin(s / 3))), int(round(vz + s * math.sin(a)))
            if not land(np.array([x]), np.array([z]))[0]:
                break
            y = hy(x, z)
            bb.set(x, y, z, "minecraft:magma_block" if s < vr * 0.45 else "minecraft:blackstone")
            if s % 4 == 0:
                bb.set(x + 1, y, z, "minecraft:obsidian")


# ------------------------------------------------------------------ giant-scale props
def giant_bonfire(bb, x, z, roast=True):
    y = hy(x, z) + 1
    bb.fill_where(x - 5, y - 1, z - 5, x + 5, y - 1, z + 5, lambda X, Y, Z: np.hypot(X - x, Z - z) <= 5.2, "minecraft:cobblestone")
    bb.fill_where(x - 5, y, z - 5, x + 5, y, z + 5, lambda X, Y, Z: np.abs(np.hypot(X - x, Z - z) - 4.6) < 0.7, "minecraft:mossy_cobblestone")
    bb.fill_where(x - 4, y - 1, z - 4, x + 4, y - 1, z + 4, lambda X, Y, Z: np.hypot(X - x, Z - z) <= 3.2, "minecraft:magma_block")
    for (dx, dz) in ((-2, -1), (1, -2), (2, 1), (-1, 2), (0, 0)):
        bb.set(x + dx, y, z + dz, "minecraft:campfire[lit=true,signal_fire=false,facing=north]")
    # crossed whole logs
    for i in range(-4, 5):
        bb.set(x + i, y + 1 + (abs(i) < 2), z - i, "minecraft:stripped_spruce_log[axis=x]") if abs(i) > 1 else None
        bb.set(x + i, y + 1 + (abs(i) < 2), z + i, "minecraft:stripped_spruce_log[axis=x]") if abs(i) > 1 else None
    if roast:
        # a dinosaur on a spit over the fire, on two forked posts
        for dx in (-7, 7):
            bb.fill(x + dx, y, z, x + dx, y + 7, z, "minecraft:spruce_log[axis=y]")
            bb.set(x + dx, y + 8, z - 1, "minecraft:spruce_fence"); bb.set(x + dx, y + 8, z + 1, "minecraft:spruce_fence")
        bb.fill(x - 8, y + 8, z, x + 8, y + 8, z, "minecraft:stripped_spruce_log[axis=x]")
        bb.fill_where(x - 5, y + 6, z - 3, x + 5, y + 11, z + 3,
                      lambda X, Y, Z: ((X - x) / 5.0) ** 2 + ((Y - (y + 8.5)) / 2.4) ** 2 + ((Z - z) / 2.6) ** 2 <= 1, "minecraft:brown_terracotta")
        bb.fill_where(x - 5, y + 6, z - 3, x + 5, y + 11, z + 3,
                      lambda X, Y, Z: (((X - x) / 5.0) ** 2 + ((Y - (y + 8.5)) / 2.4) ** 2 + ((Z - z) / 2.6) ** 2 <= 1) &
                                      (NT.noise(X * 3, Z * 3 + Y, 13030, 2) > 0.6), "minecraft:orange_terracotta")
        bb.fill(x + 5, y + 9, z, x + 8, y + 10, z, "minecraft:brown_terracotta")        # neck and head
        bb.fill(x - 8, y + 8, z, x - 5, y + 8, z, "minecraft:brown_terracotta")         # tail
        for dx in (-2, 2):
            bb.fill(x + dx, y + 5, z - 2, x + dx, y + 6, z - 2, "minecraft:bone_block[axis=y]")
            bb.fill(x + dx, y + 5, z + 2, x + dx, y + 6, z + 2, "minecraft:bone_block[axis=y]")
    return (x - 9, z - 6, x + 9, z + 6)


def giant_barrel(bb, x, z, r=4, h=9):
    y = hy(x, z) + 1
    bb.fill_where(x - r - 1, y - 2, z - r - 1, x + r + 1, y - 1, z + r + 1, lambda X, Y, Z: np.hypot(X - x, Z - z) <= r + 0.4, "minecraft:dirt")
    bulge = lambda Y: r + 0.4 + 0.8 * np.sin(np.clip((Y - y) / h, 0, 1) * math.pi)
    bb.fill_where(x - r - 2, y, z - r - 2, x + r + 2, y + h, z + r + 2, lambda X, Y, Z: np.hypot(X - x, Z - z) <= bulge(Y), "minecraft:spruce_planks")
    bb.fill_where(x - r - 2, y, z - r - 2, x + r + 2, y + h, z + r + 2,
                  lambda X, Y, Z: (np.hypot(X - x, Z - z) <= bulge(Y)) & (np.hypot(X - x, Z - z) > bulge(Y) - 1.2) &
                                  ((Y == y + 1) | (Y == y + h // 2) | (Y == y + h - 1)), "minecraft:iron_block")
    bb.fill_where(x - r - 2, y + h, z - r - 2, x + r + 2, y + h, z + r + 2, lambda X, Y, Z: np.hypot(X - x, Z - z) <= r - 0.5, "minecraft:dark_oak_planks")
    bb.set(x + r + 1, y + 3, z, "minecraft:spruce_trapdoor[facing=east,half=top,open=true]")
    return (x - r - 3, z - r - 3, x + r + 3, z + r + 3)


def giant_shield(bb, x, z, axis, col):
    """A round shield 15 across, standing on its rim against the camp, iron rim and boss."""
    y = hy(x, z) + 1
    R = 7.4
    cy = y + 7
    if axis == "x":
        bb.fill_where(x - 8, y, z, x + 8, y + 15, z + 1,
                      lambda X, Y, Z: np.hypot(X - x, Y - cy) <= R + (Z - z) * -0.9, "minecraft:spruce_planks")
        bb.fill_where(x - 8, y, z, x + 8, y + 15, z, lambda X, Y, Z: np.abs(np.hypot(X - x, Y - cy) - R) < 0.8, "minecraft:iron_block")
        bb.fill_where(x - 8, y, z, x + 8, y + 15, z,
                      lambda X, Y, Z: (np.hypot(X - x, Y - cy) < R - 1) & ((np.abs(X - x) <= 0) | (np.abs(Y - cy) <= 0)), f"minecraft:{col}_concrete")
        bb.fill(x - 1, cy - 1, z - 1, x + 1, cy + 1, z - 1, "minecraft:iron_block")
    else:
        bb.fill_where(x, y, z - 8, x + 1, y + 15, z + 8,
                      lambda X, Y, Z: np.hypot(Z - z, Y - cy) <= R + (X - x) * -0.9, "minecraft:spruce_planks")
        bb.fill_where(x, y, z - 8, x, y + 15, z + 8, lambda X, Y, Z: np.abs(np.hypot(Z - z, Y - cy) - R) < 0.8, "minecraft:iron_block")
        bb.fill_where(x, y, z - 8, x, y + 15, z + 8,
                      lambda X, Y, Z: (np.hypot(Z - z, Y - cy) < R - 1) & ((np.abs(Z - z) <= 0) | (np.abs(Y - cy) <= 0)), f"minecraft:{col}_concrete")
        bb.fill(x - 1, cy - 1, z - 1, x - 1, cy + 1, z + 1, "minecraft:iron_block")


def giant_sword(bb, x, z):
    """Dorry's sword driven into the ground: a broad blade, crossguard, wrapped grip and pommel."""
    y = hy(x, z) - 2
    bb.fill(x - 1, y, z, x + 1, y + 22, z, "minecraft:iron_block")
    bb.fill(x, y, z, x, y + 22, z, "minecraft:light_gray_concrete") if False else None
    bb.fill(x - 1, y + 21, z, x + 1, y + 21, z, "minecraft:iron_block")
    bb.fill(x - 5, y + 23, z - 1, x + 5, y + 24, z + 1, "minecraft:gold_block")
    bb.fill(x, y + 25, z, x, y + 31, z, "minecraft:brown_wool")
    bb.fill(x - 1, y + 32, z - 1, x + 1, y + 33, z + 1, "minecraft:gold_block")


def giant_axe(bb, x, z):
    """Brogy's axe buried head-first: a two-block haft rising out of a crater, the iron head half in the ground."""
    y = hy(x, z)
    bb.fill_where(x - 5, y - 2, z - 5, x + 5, y, z + 5, lambda X, Y, Z: np.hypot(X - x, Z - z) <= 4.5 - (y - Y) * 0.6, AIR)
    bb.fill_where(x - 6, y - 3, z - 6, x + 6, y - 2, z + 6, lambda X, Y, Z: np.hypot(X - x, Z - z) <= 5.5, "minecraft:coarse_dirt")
    bb.fill(x - 6, y - 2, z, x + 2, y + 4, z, "minecraft:iron_block")
    bb.fill(x - 7, y - 2, z, x - 7, y + 3, z, "minecraft:polished_andesite")
    bb.fill(x, y + 5, z, x + 1, y + 28, z + 1, "minecraft:stripped_dark_oak_log[axis=y]")
    for yy in (y + 12, y + 20):
        bb.fill(x, yy, z, x + 1, yy, z + 1, "minecraft:red_wool")


# ------------------------------------------------------------------ the camps
def dorry_camp(bb, tracker, audit, rng):
    cx, cz = DORRY
    y = hy(cx, cz) + 1
    # a giant's round hut: a dome of hides on whole-trunk ribs, a big arched doorway to the east (the duel ground)
    R, Ht = 13, 17
    z1, z2 = cz - R, cz + R
    W = R
    HIDE = ["minecraft:brown_wool", "minecraft:brown_terracotta", "minecraft:white_terracotta", "minecraft:light_gray_wool"]
    shell = lambda X, Y, Z: (((X - cx) ** 2 + (Z - cz) ** 2) / R ** 2 + ((Y - y) / Ht) ** 2 <= 1) & \
                            (((X - cx) ** 2 + (Z - cz) ** 2) / (R - 1.3) ** 2 + ((Y - y) / (Ht - 1.3)) ** 2 > 1)
    bb.fill_where(cx - R - 1, y, cz - R - 1, cx + R + 1, y + Ht, cz + R + 1, shell, HIDE[0])
    for k, hb in enumerate(HIDE[1:]):
        bb.fill_where(cx - R - 1, y, cz - R - 1, cx + R + 1, y + Ht, cz + R + 1,
                      lambda X, Y, Z, k=k: shell(X, Y, Z) & (NT.noise(X + 2 * Y, Z - Y, 13040 + k, 5) > 0.68 + 0.04 * k), hb)
    # stitched seams + trunk ribs standing proud of the hides
    for a in range(0, 360, 45):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        for k in range(0, Ht + 1):
            rr = (R + 0.6) * math.sqrt(max(0, 1 - (k / Ht) ** 2))
            bb.set(cx + int(round(rr * ca)), y + k, cz + int(round(rr * sa)), "minecraft:spruce_log[axis=y]")
    bb.fill(cx - 1, y + Ht - 1, cz - 1, cx + 1, y + Ht + 2, cz + 1, "minecraft:spruce_log[axis=y]")
    bb.fill(cx, y + Ht + 1, cz, cx, y + Ht + 3, cz, "minecraft:campfire[lit=true,signal_fire=false,facing=north]") if False else None
    # the doorway: a tall arch on the east side, framed with logs, a rolled-up hide flap above
    for k in range(0, 11):
        half = int(round(4 * math.sqrt(max(0, 1 - (k / 10.5) ** 2))))
        bb.fill(cx + R - 3, y + k, cz - half, cx + R + 1, y + k, cz + half, AIR)
    for s_ in (-5, 5):
        bb.fill(cx + R - 1, y, cz + s_, cx + R - 1, y + 9, cz + s_, "minecraft:spruce_log[axis=y]")
    bb.fill(cx + R - 1, y + 11, cz - 5, cx + R, y + 11, cz + 5, "minecraft:white_wool")
    bb.fill_where(cx - R, y - 1, cz - R, cx + R, y - 1, cz + R, lambda X, Y, Z: np.hypot(X - cx, Z - cz) <= R, "minecraft:coarse_dirt")
    # inside: a giant fur bed (a mound of wool), a giant's mug, a bone pile, a chest
    bb.fill_where(cx - 9, y, z1 + 2, cx - 1, y + 2, z1 + 16,
                  lambda X, Y, Z: ((X - (cx - 5)) / 4.5) ** 2 + ((Y - y) / 2.4) ** 2 + ((Z - (z1 + 9)) / 7.5) ** 2 <= 1, "minecraft:brown_wool")
    bb.fill_where(cx - 9, y, z1 + 2, cx - 1, y + 3, z1 + 16,
                  lambda X, Y, Z: (((X - (cx - 5)) / 3) ** 2 + ((Y - y - 1) / 1.5) ** 2 + ((Z - (z1 + 4)) / 2) ** 2 <= 1), "minecraft:white_wool")
    mx, mz = cx + 3, z2 - 6
    bb.fill_where(mx - 3, y, mz - 3, mx + 3, y + 5, mz + 3, lambda X, Y, Z: np.abs(np.hypot(X - mx, Z - mz) - 2.4) < 0.8, "minecraft:spruce_planks")
    bb.fill_where(mx - 3, y, mz - 3, mx + 3, y, mz + 3, lambda X, Y, Z: np.hypot(X - mx, Z - mz) < 2.4, "minecraft:spruce_planks")
    bb.fill(mx + 3, y + 1, mz, mx + 4, y + 4, mz, "minecraft:spruce_planks")
    for (dx, dz) in ((-6, 4), (-4, 6), (-7, 7)):
        bb.set(cx + dx, y, z2 - 12 + dz, "minecraft:bone_block[axis=x]")
    for zz in range(z1 + 6, z2 - 3, 7):
        bb.fill(cx, y + 9, zz, cx, y + Ht - 3, zz, "minecraft:iron_chain[axis=y]"); bb.set(cx, y + 8, zz, "minecraft:lantern[hanging=true]")
    bfx = cx + W + 9
    box = giant_bonfire(bb, bfx, cz, roast=True)
    giant_barrel(bb, cx + W + 4, z1 - 4, 4, 9)
    giant_barrel(bb, cx + W - 4, z1 - 7, 3, 7)
    giant_sword(bb, cx + W + 6, z2 + 6)
    giant_shield(bb, cx - W - 2, cz + 4, "z", "red")
    return (cx - W - 4, z1 - 12, bfx + 9, z2 + 9)


def sea_king_skeleton(bb, x0, z0, L=56):
    """The bleached skeleton of a giant Sea King lying along x: a spine, ribs arching high over the camp, the skull."""
    y = hy(x0 + L // 2, z0) + 1
    BONE = "minecraft:bone_block[axis=x]"
    BONEY = "minecraft:bone_block[axis=y]"
    sp = lambda i: y + 15 - int(4 * math.sin(i / L * math.pi))      # the spine sags
    for i in range(0, L):
        x = x0 + i
        top = y + 2 + int(15 * math.sin(min(1, (i + 6) / (L * 0.9)) * math.pi)) if i < L - 4 else y + 3
        bb.fill(x, top, z0, x, top + 1, z0, BONE)
        if i % 4 == 2 and 3 < i < L - 6:
            # a rib pair: an arch from the spine down to the ground each side
            R = top - y + 1
            for a in np.linspace(0, math.pi / 2, 30):
                for s in (-1, 1):
                    rz = z0 + s * int(round(R * 0.85 * math.sin(a)))
                    ry = y + int(round(R * math.cos(a))) - 1
                    if ry <= top:
                        bb.set(x, ry, rz, BONEY)
    # the skull at the head end (east): a long snout with the jaw open, eye holes
    hx = x0 + L
    bb.fill_where(hx - 2, y - 1, z0 - 7, hx + 18, y + 9, z0 + 7,
                  lambda X, Y, Z: (((X - (hx + 6)) / 10.0) ** 2 + ((Y - (y + 4)) / 4.5) ** 2 + ((Z - z0) / 6.0) ** 2 <= 1) &
                                  ((((X - (hx + 6)) / 8.6) ** 2 + ((Y - (y + 4)) / 3.4) ** 2 + ((Z - z0) / 4.8) ** 2) > 1), "minecraft:bone_block[axis=y]")
    bb.fill(hx + 3, y + 5, z0 - 6, hx + 4, y + 6, z0 - 4, AIR); bb.fill(hx + 3, y + 5, z0 + 4, hx + 4, y + 6, z0 + 6, AIR)
    bb.fill(hx + 10, y + 1, z0 - 4, hx + 18, y + 3, z0 + 4, AIR)
    for i in range(hx + 9, hx + 19, 2):
        bb.set(i, y + 3, z0 - 3, "minecraft:pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]") if False else None
        bb.set(i, y, z0 - 3, "minecraft:bone_block[axis=y]"); bb.set(i, y, z0 + 3, "minecraft:bone_block[axis=y]")
    bb.fill(hx + 8, y - 1, z0 - 5, hx + 22, y - 1, z0 + 5, "minecraft:bone_block[axis=x]") if False else None
    # tail bones trailing west, half buried
    for i in range(1, 14):
        bb.set(x0 - i, y + 1 - i // 6, z0 + int(2 * math.sin(i / 3)), BONE)
    return (x0 - 15, z0 - 16, hx + 20, z0 + 16)


def brogy_camp(bb, tracker, audit, rng):
    cx, cz = BROGY
    box = sea_king_skeleton(bb, cx - 40, cz - 2, 44)
    y = hy(cx, cz) + 1
    # under the ribs: a hide floor, fur bedding, a ring of rocks, the bonfire on the duel side
    bb.fill_where(cx - 24, y - 1, cz - 10, cx + 4, y - 1, cz + 6,
                  lambda X, Y, Z: (((X - (cx - 10)) / 14.0) ** 2 + ((Z - (cz - 2)) / 8.0) ** 2) <= 1, "minecraft:coarse_dirt")
    bb.fill_where(cx - 22, y, cz - 8, cx - 8, y + 2, cz + 4,
                  lambda X, Y, Z: ((X - (cx - 15)) / 6.5) ** 2 + ((Y - y) / 2.2) ** 2 + ((Z - (cz - 3)) / 4.5) ** 2 <= 1, "minecraft:light_gray_wool")
    bb.fill_where(cx - 22, y, cz - 8, cx - 8, y + 2, cz + 4,
                  lambda X, Y, Z: (((X - (cx - 15)) / 6.5) ** 2 + ((Y - y) / 2.2) ** 2 + ((Z - (cz - 3)) / 4.5) ** 2 <= 1) &
                                  (NT.noise(X * 2, Z * 2, 13050, 2) > 0.55), "minecraft:brown_wool")
    giant_bonfire(bb, cx - 18, cz + 17, roast=False)
    giant_barrel(bb, cx + 6, cz + 14, 4, 9)
    giant_barrel(bb, cx - 2, cz + 17, 3, 7)
    giant_barrel(bb, cx + 13, cz + 9, 3, 6)
    giant_axe(bb, cx - 38, cz + 17)
    giant_shield(bb, cx + 16, cz - 10, "x", "blue")
    for (dx, dz) in ((-4, -12), (-12, 10), (2, 8)):
        lamp_post(bb, cx + dx, hy(cx + dx, cz + dz) + 1, cz + dz, post="minecraft:spruce_fence", h=3)
    return (min(box[0], cx - 50), box[1], max(box[2], cx + 18), cz + 24)


def duel_ground(bb, rng):
    cx, cz, r = DUEL
    # craters and split stumps from a hundred years of blows
    for _ in range(9):
        a, d = rng.uniform(0, 2 * math.pi), rng.uniform(0, r - 3)
        x, z = int(cx + d * math.cos(a)), int(cz + d * math.sin(a))
        rr = float(rng.uniform(2, 4))
        y = hy(x, z)
        bb.fill_where(x - 5, y - 2, z - 5, x + 5, y, z + 5, lambda X, Y, Z, x=x, z=z, rr=rr, y=y: np.hypot(X - x, Z - z) <= rr - (y - Y) * 0.8, AIR)
        bb.fill_where(x - 5, y - 3, z - 5, x + 5, y, z + 5,
                      lambda X, Y, Z, x=x, z=z, rr=rr, y=y: (np.hypot(X - x, Z - z) <= rr + 0.6 - (y - Y) * 0.8) &
                                                            (np.hypot(X - x, Z - z) > rr - 0.6 - (y - Y) * 0.8), "minecraft:coarse_dirt")
    for _ in range(6):
        a = rng.uniform(0, 2 * math.pi)
        x, z = int(cx + (r + 2) * math.cos(a)), int(cz + (r + 2) * math.sin(a))
        y = hy(x, z) + 1
        bb.fill(x, y, z, x + 1, y + int(rng.integers(2, 6)), z + 1, "minecraft:jungle_log[axis=y]")
        L = int(rng.integers(8, 14))
        dx, dz = (1, 0) if rng.random() < 0.5 else (0, 1)
        for s in range(2, L):
            bb.set(x + dx * s, y, z + dz * s, f"minecraft:jungle_log[axis={'x' if dx else 'z'}]")


def dino_skeleton(bb):
    """A long-necked dinosaur skeleton fallen in the jungle: spine, ribs, a neck curving up, the skull, leg bones."""
    x0, z0 = DINO
    y = hy(x0, z0) + 1
    B = "minecraft:bone_block[axis=x]"
    for i in range(-16, 14):
        yy = y + 6 + int(2 * math.cos(i / 10))
        bb.set(x0 + i, yy, z0, B)
        if -8 < i < 7 and i % 2 == 0:
            for k in range(1, 6):
                bb.set(x0 + i, yy - k, z0 - (k if k < 4 else 4), "minecraft:bone_block[axis=y]")
                bb.set(x0 + i, yy - k, z0 + (k if k < 4 else 4), "minecraft:bone_block[axis=y]")
    for i in range(14):                                       # the neck curling up and back
        bb.set(x0 + 14 + i // 2, y + 6 + i, z0 + int(2 * math.sin(i / 4)), "minecraft:bone_block[axis=y]")
    hx, hyy = x0 + 21, y + 20
    bb.fill(hx, hyy, z0 - 1, hx + 3, hyy + 1, z0 + 1, "minecraft:bone_block[axis=x]")
    bb.set(hx + 1, hyy + 1, z0, AIR)
    for (dx, dz) in ((-6, -3), (-6, 3), (5, -3), (5, 3)):
        bb.fill(x0 + dx, y, z0 + dz, x0 + dx, y + 4, z0 + dz, "minecraft:bone_block[axis=y]")
    return (x0 - 18, z0 - 6, x0 + 26, z0 + 6)


# ------------------------------------------------------------------ Mr. 3's wax works
def candle_house(bb, tracker, audit):
    cx, cz = CANDLE
    x1, z1, x2, z2 = cx - 8, cz - 6, cx + 8, cz + 6
    y = hy(cx, cz) + 1
    WAX = "minecraft:white_concrete"
    bb.fill(x1 - 1, y - 3, z1 - 1, x2 + 1, y - 1, z2 + 1, "minecraft:white_terracotta")
    bb.fill(x1, y, z1, x2, y + 5, z2, WAX)
    bb.fill(x1 + 1, y, z1 + 1, x2 - 1, y + 5, z2 - 1, AIR)
    bb.fill(x1 + 1, y - 1, z1 + 1, x2 - 1, y - 1, z2 - 1, "minecraft:smooth_quartz")
    # drips of wax down the walls and a rounded wax roof with a wick chimney
    for x in range(x1, x2 + 1, 3):
        for z in (z1, z2):
            bb.set(x, y + 6, z, WAX)
    bb.fill_where(x1 - 1, y + 6, z1 - 1, x2 + 1, y + 12, z2 + 1,
                  lambda X, Y, Z: (((X - cx) / 9.5) ** 2 + ((Y - (y + 5)) / 6.0) ** 2 + ((Z - cz) / 7.5) ** 2) <= 1, "minecraft:white_concrete")
    bb.fill_where(x1, y + 5, z1, x2, y + 11, z2,
                  lambda X, Y, Z: (((X - cx) / 8.3) ** 2 + ((Y - (y + 5)) / 4.9) ** 2 + ((Z - cz) / 6.3) ** 2) <= 1, AIR)
    bb.fill(cx + 4, y + 9, cz, cx + 4, y + 13, cz, "minecraft:white_concrete")
    bb.set(cx + 4, y + 14, cz, "minecraft:candle[candles=1,lit=true]")
    for x in range(x1 + 2, x2 - 1, 4):
        bb.fill(x, y + 1, z2, x, y + 2, z2, "minecraft:white_stained_glass_pane")
        bb.fill(x, y + 1, z1, x, y + 2, z1, "minecraft:white_stained_glass_pane")
    bb.fill(cx, y, z2, cx, y + 1, z2, AIR)
    bb.set(cx, y, z2, "minecraft:birch_door[facing=south,half=lower,hinge=left]")
    bb.set(cx, y + 1, z2, "minecraft:birch_door[facing=south,half=upper,hinge=left]")
    P.furnish_room(bb, (x1 + 1, z1 + 1, x2 - 1, z2 - 1), y, kind="living", height=5, seed=13060, wood="birch", tracker=tracker, doors=[(cx, z2 - 1)])
    txt, ok = P.audit_props(bb, [(x1 + 1, z1 + 1, x2 - 1, z2 - 1)], y, 5)
    if not ok:
        audit.append(txt)
    for (dx, dz) in ((-3, -3), (3, -3), (-5, 2), (5, 2)):
        set_if_air(bb, cx + dx, y, cz + dz, "minecraft:white_candle[candles=3,lit=true]")
    # Miss Goldenweek's picnic spread on the grass outside: a rug, a parasol, tea
    px1, pz1 = x1 - 9, cz - 3                                  # on the flat lawn west of the hut
    for x in range(px1, px1 + 6):
        for z in range(pz1, pz1 + 5):
            inner = px1 < x < px1 + 5 and pz1 < z < pz1 + 4
            bb.set(x, hy(x, z) + 1, z, "minecraft:white_carpet" if inner else "minecraft:red_carpet")
    ux, uz = px1 + 7, pz1 + 2
    bb.fill(ux, hy(ux, uz) + 1, uz, ux, hy(ux, uz) + 4, uz, "minecraft:birch_fence")
    for (dx, dz) in ((-1, 0), (1, 0), (0, -1), (0, 1), (0, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        bb.set(ux + dx, hy(ux, uz) + 5, uz + dz, "minecraft:pink_wool" if (dx + dz) % 2 else "minecraft:white_wool")
    return (px1 - 2, z1 - 3, x2 + 3, z2 + 4)


def service_set(bb):
    """The Candle Service Set: a three-tier round wax stage like a cake, a spiral stair up the side, a big pumpkin-
    shaped spinner on top."""
    cx, cz = SERVICE
    y = hy(cx, cz) + 1
    WAX = "minecraft:white_concrete"
    tiers = [(11, 4), (8, 4), (5, 4)]
    yy = y
    for r, h in tiers:
        bb.fill_where(cx - r - 1, yy, cz - r - 1, cx + r + 1, yy + h - 1, cz + r + 1, lambda X, Y, Z, r=r: np.hypot(X - cx, Z - cz) <= r + 0.4, WAX)
        bb.fill_where(cx - r - 1, yy + h - 1, cz - r - 1, cx + r + 1, yy + h - 1, cz + r + 1,
                      lambda X, Y, Z, r=r: np.abs(np.hypot(X - cx, Z - cz) - r) < 0.7, "minecraft:white_wool")
        # wax drips down each tier
        for k in range(0, 360, 20):
            a = math.radians(k)
            dx, dz = int(round((r + 1) * math.cos(a))), int(round((r + 1) * math.sin(a)))
            d = 1 + (k // 20) % 3
            bb.fill(cx + dx, yy + h - d, cz + dz, cx + dx, yy + h - 1, cz + dz, WAX)
        yy += h
    # a spiral stair round the outside
    for i in range(40):
        a = math.radians(i * 14)
        r = 12.5 - 4.5 * (i / 40)
        sx, sz = int(round(cx + r * math.cos(a))), int(round(cz + r * math.sin(a)))
        sy = y + int(i * (yy - y) / 40)
        bb.set(sx, sy, sz, "minecraft:smooth_quartz_slab[type=top]")
        bb.fill(sx, sy + 1, sz, sx, sy + 3, sz, AIR)
    # the pumpkin-shaped spinner on top
    bb.fill(cx, yy, cz, cx, yy + 3, cz, "minecraft:white_concrete")
    bb.fill_where(cx - 5, yy + 3, cz - 5, cx + 5, yy + 10, cz + 5,
                  lambda X, Y, Z: (((X - cx) / 5.0) ** 2 + ((Y - (yy + 6.5)) / 3.6) ** 2 + ((Z - cz) / 5.0) ** 2) <= 1, "minecraft:orange_terracotta")
    bb.fill_where(cx - 5, yy + 3, cz - 5, cx + 5, yy + 10, cz + 5,
                  lambda X, Y, Z: ((((X - cx) / 5.0) ** 2 + ((Y - (yy + 6.5)) / 3.6) ** 2 + ((Z - cz) / 5.0) ** 2) <= 1) &
                                  ((X == cx) | (Z == cz)), "minecraft:orange_concrete")
    bb.fill(cx, yy + 10, cz, cx, yy + 12, cz, "minecraft:white_concrete")
    bb.set(cx, yy + 13, cz, "minecraft:candle[candles=1,lit=true]")
    return (cx - 15, cz - 15, cx + 15, cz + 15)


def design():
    bb = BigBuild(seed=13010, y_min=-16, y_max=124)
    tracker = P.PropTracker(13010)
    audit = []
    rng = np.random.default_rng(13010)
    terrain(bb)
    volcano(bb, rng)
    duel_ground(bb, rng)
    taken = [(DUEL[0] - DUEL[2] - 3, DUEL[1] - DUEL[2] - 3, DUEL[0] + DUEL[2] + 3, DUEL[1] + DUEL[2] + 3)]
    taken.append(dorry_camp(bb, tracker, audit, rng))
    taken.append(brogy_camp(bb, tracker, audit, rng))
    taken.append(dino_skeleton(bb))
    taken.append(candle_house(bb, tracker, audit))
    taken.append(service_set(bb))
    # colossal prehistoric trees first (well inland), then ordinary giant trees below them
    big = 0
    for _ in range(3000):
        x, z = int(rng.integers(14, N - 14)), int(rng.integers(14, N - 14))
        X, Z = np.array([x]), np.array([z])
        if not land(X, Z)[0] or sh(X, Z)[0] < 11 or riv(X, Z)[0] < 7 or volc_r(x, z) < VOLC[2] * 0.85:
            continue
        if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken):
            continue
        h = int(rng.integers(50, 80))
        T3.colossal_tree(bb, x, hy(x, z) + 1, z, h, rng, kind=("jungle", "jungle", "mangrove")[big % 3] if big % 4 else "dark_oak",
                         r0=rng.uniform(3.5, 6.5), spread=1.0 + (h - 50) / 60,
                         leaves=["minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]",
                                 "minecraft:mangrove_leaves[distance=7,persistent=true,waterlogged=false]",
                                 "minecraft:dark_oak_leaves[distance=7,persistent=true,waterlogged=false]"])
        taken.append((x - 7, z - 7, x + 7, z + 7))
        big += 1
        if big >= 15:
            break
    print("colossal trees:", big)
    # giant jungle trees, kept off the volcano, the river, the camps and the beach
    k = 0
    for _ in range(4000):
        x, z = int(rng.integers(10, N - 10)), int(rng.integers(10, N - 10))
        X, Z = np.array([x]), np.array([z])
        if not land(X, Z)[0] or sh(X, Z)[0] < 12 or riv(X, Z)[0] < 6 or volc_r(x, z) < VOLC[2] * 0.75:
            continue
        if any(t[0] - 3 <= x <= t[2] + 3 and t[1] - 3 <= z <= t[3] + 3 for t in taken):
            continue
        h = int(rng.integers(16, 30)) if sh(X, Z)[0] > 20 else int(rng.integers(10, 16))
        NT.giant_tree(bb, x, hy(x, z) + 1, z, h, rng, kind="jungle")
        taken.append((x - 4, z - 4, x + 5, z + 5))
        k += 1
        if k >= 42:
            break
    print("giant trees:", k)
    # giant ferns, clover and drifts of undergrowth
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 13090, density=0.55,
              kinds=["onepiece:giant_fern", "onepiece:dino_fern", "minecraft:large_fern", "onepiece:giants_clover", "minecraft:fern",
                     "onepiece:jungle_shrub", "minecraft:short_grass"],
              flowers=["minecraft:blue_orchid", "minecraft:allium", "minecraft:orange_tulip"],
              mask=lambda X, Z: land(X, Z) & (sh(X, Z) >= 8) & ~duel(X, Z) & (volc_r(X, Z) > VOLC[2] * 0.6) & (riv(X, Z) > 3.5),
              ground=("grass_block", "moss_block", "podzol", "rooted_dirt", "coarse_dirt", "jungle_loam"))
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 13091, density=0.18, kinds=["minecraft:short_grass", "minecraft:dead_bush"],
              mask=lambda X, Z: land(X, Z) & duel(X, Z), ground=("grass_block", "coarse_dirt", "dirt", "rooted_dirt"))
    return bb, audit


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    steady(b)
    b.chest(DORRY[0] - 3, hy(*DORRY) + 1, DORRY[1] + 8, "medium", "east")
    b.chest(BROGY[0] - 6, hy(*BROGY) + 1, BROGY[1] + 2, "medium", "south")
    b.chest(CANDLE[0] + 6, hy(*CANDLE) + 1, CANDLE[1] - 4, "easy", "west")
    b.chest(SERVICE[0], hy(*SERVICE) + 13, SERVICE[1] + 3, "treasure", "south")
    b.guards("baroque_agent", ((CANDLE[0] - 4, CANDLE[1] + 12), (CANDLE[0] + 10, CANDLE[1] + 8), (SERVICE[0] - 14, SERVICE[1])),
             y=TY + 1)
    return b, 0
