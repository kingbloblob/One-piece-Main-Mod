"""Rookie Pirate Camp v2, redesigned with the Minecraft Builder skill: a rookie crew's beach camp the way the East
Blue arcs show them (Buggy's, Alvida's and the Krieg crew camps, ep 4-8 / 20-30): their battered caravel run up on
the sand, sailcloth tents in the crew colours, a bonfire and a lot of grog.

Silhouette first: the caravel lying beached and heeled over in a lagoon with its striped red sails half furled and
the Jolly Roger flying, a tall palm-trunk lookout tree with a crow's nest, a big red-and-white striped captain's
tent, palms leaning over the beach.

Around it: crew tents with bedrolls and sea chests, the cook tent with a stew pot and smoker, the bonfire ring with
log benches and a grog barrel stand, a wanted poster board, a target range, stacks of crates, powder kegs and
cannon balls, a dinghy on the sand, a rope bridge plank to the ship, footpaths, dune grass. 112 x 96, land site,
ground y 0; the lagoon is closed by sand bars so its water never meets the site edge. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, steady, lamp_post
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.hulls import galleon, transfer, tatter

SID = "pirate_camp"
TITLE = "Rookie Pirate Camp"
CUTS = [2, 6, 12]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

NX, NZ = 112, 96
_LAND = NT.outline(56, 48, 50, 4501, wobble=0.12)
_LAG = NT.outline(60, 70, 15, 4502, wobble=0.15, lobes=((2, 0.35), (3, 0.06)))
CX, CZ = 50, 38                     # bonfire
BEACH = [("minecraft:sand", 0.75), ("minecraft:sandstone", 0.05), ("minecraft:gravel", 0.05), ("minecraft:sand", 0.15)]
LEAF = "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]"


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = _LAND(X, Z)
    h = 1 + NT.fbm(X, Z, 4503, 16) * 3 + np.clip((40 - Z) / 12.0, 0, 2.5)
    h = np.where(d < 10, h * np.clip(d / 10.0, 0, 1), h)
    lg = _LAG(X, Z)
    h = np.where(lg > 0, -1 - np.clip(lg / 3.0, 0, 3), h)
    h = np.where((lg <= 0) & (lg > -5), np.minimum(h, 1), h)
    return np.round(h)


X_, Z_ = np.arange(NX)[:, None].astype(float), np.arange(NZ)[None, :].astype(float)
HMAP = _height(X_, Z_).astype(int)


def height(X, Z):
    return HMAP[np.clip(np.asarray(X).astype(int), 0, NX - 1), np.clip(np.asarray(Z).astype(int), 0, NZ - 1)]


def hy(x, z):
    return int(HMAP[min(max(int(x), 0), NX - 1), min(max(int(z), 0), NZ - 1)])


def onland(X, Z):
    return _LAND(np.asarray(X, float), np.asarray(Z, float)) > 0


def terrain(bb):
    lag = lambda X, Z: _LAG(X, Z) > 0
    sand = lambda X, Z: onland(X, Z) & ~lag(X, Z) & ((Z > 46) | (_LAND(X, Z) < 12) | (_LAG(X, Z) > -9))
    grass = lambda X, Z: onland(X, Z) & ~lag(X, Z) & ~sand(X, Z)
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, height, BEACH, 4504, mask=sand, under="minecraft:sandstone", core="minecraft:stone", base=-6)
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, height, NT.MEADOW, 4505, mask=grass, core="minecraft:stone", base=-6)
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, height, [("minecraft:sand", 0.7), ("minecraft:gravel", 0.2), ("minecraft:clay", 0.1)], 4506,
             mask=lag, under="minecraft:sandstone", core="minecraft:stone", base=-6)
    bb.fill_where(36, -5, 50, 86, 0, 92, lambda X, y, Z: lag(X, Z) & (y > height(X, Z)), "minecraft:water")
    NT.plants(bb, 0, 0, NX - 1, NZ - 1, height, 4507, density=0.3, kinds=NT.PLANTS_MEADOW, flowers=["minecraft:dandelion", "minecraft:poppy"],
              mask=grass)
    NT.plants(bb, 0, 0, NX - 1, NZ - 1, height, 4508, density=0.08, kinds=["minecraft:short_dry_grass", "minecraft:tall_dry_grass", "minecraft:dead_bush"],
              mask=sand, ground=("sand",))


def palm(bb, x, z, h, lean, rng):
    """A coconut palm: a curving trunk of stripped jungle logs, a crown of drooping fronds, coconuts."""
    y = hy(x, z)
    px, pz = float(x), float(z)
    for k in range(h):
        px += lean[0] * (k / h) * 0.6
        pz += lean[1] * (k / h) * 0.6
        bb.set(int(round(px)), y + 1 + k, int(round(pz)), "minecraft:jungle_log[axis=y]" if k % 3 else "minecraft:stripped_jungle_log[axis=y]")
    tx, ty, tz = int(round(px)), y + h, int(round(pz))
    bb.set(tx, ty + 1, tz, LEAF)
    for a in range(0, 360, 45):
        t = math.radians(a + rng.uniform(-10, 10))
        for s in range(1, 6):
            fx, fz = tx + int(round(s * math.cos(t))), tz + int(round(s * math.sin(t)))
            fy = ty + 1 - (s * s) // 9
            bb.set(fx, fy, fz, LEAF)
    for (dx, dz) in ((1, 0), (0, 1), (-1, 0)):
        bb.set(tx + dx, ty - 1, tz + dz, "minecraft:cocoa[age=2,facing=" + {(1, 0): "west", (0, 1): "north", (-1, 0): "east"}[(dx, dz)] + "]")


def tent(bb, x, z, w, d, cols, door="south", furnish=True, rng=None):
    """An A-frame sailcloth tent along x (ridge along x), striped in two colours, open at the door end with flaps."""
    y = hy(x + w // 2, z + d // 2)
    bb.fill(x, y, z, x + w - 1, y, z + d - 1, "minecraft:spruce_planks" if w > 7 else "minecraft:coarse_dirt")
    bb.fill(x, y + 1, z, x + w - 1, y + d // 2 + 2, z + d - 1, AIR)
    half = d // 2
    for k in range(half + 1):
        for x_ in range(x, x + w):
            c = cols[(x_ - x) // 2 % 2]
            bb.set(x_, y + 1 + k, z + k, c)
            bb.set(x_, y + 1 + k, z + d - 1 - k, c)
    bb.fill(x - 1, y + 1 + half + 1, z + half, x + w, y + 1 + half + 1, z + half, "minecraft:stripped_spruce_log[axis=x]")
    for x_ in (x - 1, x + w):
        bb.fill(x_, y + 1, z + half, x_, y + 1 + half, z + half, "minecraft:spruce_fence")
    # back wall closed, front open with flaps tied back
    for k in range(half):
        bb.fill(x, y + 1, z + k + 1, x, y + k + 1, z + d - 2 - k, cols[0]) if k == 0 else None
    for zz in range(z + 1, z + d - 1):
        top = y + min(zz - z, z + d - 1 - zz)
        bb.fill(x, y + 1, zz, x, top, zz, cols[1])
    if furnish:
        bb.set(x + 1, y + 1, z + 1, "minecraft:red_bed[facing=east,part=foot]"); bb.set(x + 2, y + 1, z + 1, "minecraft:red_bed[facing=east,part=head]")
        if d > 4:
            bb.set(x + 1, y + 1, z + d - 2, "minecraft:brown_bed[facing=east,part=foot]"); bb.set(x + 2, y + 1, z + d - 2, "minecraft:brown_bed[facing=east,part=head]")
        bb.set(x + w - 2, y + 1, z + 1, "minecraft:barrel[facing=up]")
        bb.set(x + w - 2, y + 1, z + d - 2, "minecraft:lantern")
    return y


def caravel(bb):
    """The crew's caravel beached in the lagoon: heeled over, bow on the sand, red striped sails half furled."""
    src = galleon(length=32, beam=11, depth=8, masts=2, hull="minecraft:spruce_planks", deck="minecraft:oak_planks",
                  sail="minecraft:red_wool", castle=True, guns=True, figure="minecraft:carved_pumpkin[facing=east]")
    # stripes on the sails: every other column white
    reg = src.get_region(0, 0, -12, 40, 40, 12)
    rid = src.ids.get("minecraft:red_wool")
    wid = src.register("minecraft:white_wool")
    if rid:
        m = (reg == rid) & ((np.arange(reg.shape[2])[None, None, :] // 2) % 2 == 0)
        reg2 = reg.copy(); reg2[m] = wid
        src._write(0, 0, -12, 40, 40, 12, reg2, mask=m)
    where = transfer(bb, src, -2, 40, 44, -4, 70, lean=0.28, yaw=-0.12, pivot=(16, 0), decay=0.02, seed=4509)
    # the Jolly Roger at the main mast top
    mx, my, mz = where(int(0.68 * 31), 6 + 24, 0)
    for u in range(5):
        for v in range(4):
            skull = (u, v) in ((2, 1), (1, 1), (3, 1), (2, 2), (1, 3), (3, 3), (2, 0))
            bb.set(mx, my - v, mz + 1 + u, "minecraft:white_wool" if skull else "minecraft:black_wool")
    # plank gangway from the beach to the deck
    gx, gy, gz = where(16, 7, -5)
    for k in range(7):
        bb.set(gx, max(gy - k // 2, hy(gx, gz - k) + 1), gz - k, "minecraft:spruce_slab[type=bottom]")
    # dinghy on the sand
    dx, dz = 34, 58
    dy = hy(dx, dz)
    for k in range(6):
        hw = 1 if 0 < k < 5 else 0
        for s in range(-hw, hw + 1):
            bb.set(dx + k, dy + 1, dz + s, "minecraft:oak_planks" if abs(s) == hw else "minecraft:oak_slab[type=bottom]")
    bb.set(dx + 2, dy + 2, dz - 2, "minecraft:spruce_fence")
    return where


def lookout(bb):
    """The lookout tree: a tall palm trunk with ladder and a crow's nest barrel platform."""
    x, z = 22, 30
    y = hy(x, z)
    bb.fill(x, y + 1, z, x, y + 22, z, "minecraft:jungle_log[axis=y]")
    bb.fill(x, y + 1, z + 1, x, y + 21, z + 1, "minecraft:ladder[facing=south]")
    bb.fill_where(x - 3, y + 22, z - 3, x + 3, y + 22, z + 3, lambda X, yy, Z: (X - x) ** 2 + (Z - z) ** 2 <= 8, "minecraft:spruce_planks")
    bb.fill_where(x - 3, y + 23, z - 3, x + 3, y + 23, z + 3, lambda X, yy, Z: ((X - x) ** 2 + (Z - z) ** 2 <= 8) & ((X - x) ** 2 + (Z - z) ** 2 > 3),
                  "minecraft:spruce_fence")
    bb.set(x, y + 22, z + 1, "minecraft:ladder[facing=south]")
    bb.fill(x, y + 23, z, x, y + 28, z, "minecraft:spruce_fence")
    bb.fill(x + 1, y + 26, z, x + 4, y + 28, z, "minecraft:black_wool")
    bb.set(x + 2, y + 27, z, "minecraft:white_wool")
    for a in range(0, 360, 60):
        t = math.radians(a)
        for s in range(1, 5):
            bb.set(x + int(round(s * math.cos(t))), y + 24 - (s * s) // 8, z + int(round(s * math.sin(t))), LEAF)


def camp(bb, rng):
    """Bonfire ring, tents, captain's tent, cook tent, poster board, target range, crates and kegs."""
    y = hy(CX, CZ)
    bb.fill_where(CX - 9, y, CZ - 9, CX + 9, y, CZ + 9, lambda X, yy, Z: np.hypot(X - CX, Z - CZ) < 8.5, "minecraft:coarse_dirt")
    bb.fill_where(CX - 9, y + 1, CZ - 9, CX + 9, y + 5, CZ + 9, lambda X, yy, Z: np.hypot(X - CX, Z - CZ) < 8.5, AIR)
    bb.fill(CX - 1, y, CZ - 1, CX + 1, y, CZ + 1, "minecraft:cobblestone")
    bb.set(CX, y + 1, CZ, "minecraft:campfire[lit=true]")
    for (a, b) in ((-1, -1), (1, 1)):
        bb.set(CX + a, y + 1, CZ + b, "minecraft:campfire[lit=true]")
    for (dx, dz, ax) in ((-5, 0, "z"), (5, 0, "z"), (0, -5, "x"), (0, 5, "x")):
        for k in (-1, 0, 1):
            bb.set(CX + dx + (k if ax == "x" else 0), y + 1, CZ + dz + (k if ax == "z" else 0), f"minecraft:stripped_oak_log[axis={ax}]")
    # grog stand
    for (dx, dz) in ((6, -5), (7, -5), (6, -4)):
        bb.set(CX + dx, y + 1, CZ + dz, "minecraft:barrel[facing=east]")
    bb.set(CX + 7, y + 2, CZ - 5, "minecraft:barrel[facing=up]")
    bb.fill(CX + 5, y + 1, CZ - 7, CX + 7, y + 1, CZ - 7, "minecraft:spruce_slab[type=top]")
    # crew tents round the fire
    cols = [("minecraft:red_wool", "minecraft:white_wool"), ("minecraft:white_wool", "minecraft:light_gray_wool"),
            ("minecraft:red_wool", "minecraft:brown_wool")]
    for k, (x, z) in enumerate(((CX - 22, CZ - 10), (CX - 22, CZ + 1), (CX - 12, CZ - 22), (CX + 2, CZ - 22), (CX + 14, CZ - 18))):
        tent(bb, x, z, 6, 7, cols[k % 3], rng=rng)
    # the captain's tent: big, striped, a map table, a throne chair, the stolen treasure
    tx, tz = CX + 14, CZ - 4
    ty = tent(bb, tx, tz, 12, 11, ("minecraft:red_wool", "minecraft:white_wool"), furnish=False)
    bb.set(tx + 5, ty + 1, tz + 5, "minecraft:cartography_table"); bb.set(tx + 6, ty + 1, tz + 5, "minecraft:cartography_table")
    bb.set(tx + 4, ty + 1, tz + 5, "minecraft:spruce_stairs[facing=east]")
    bb.set(tx + 9, ty + 1, tz + 2, "minecraft:gold_block"); bb.set(tx + 10, ty + 1, tz + 2, "minecraft:gold_block"); bb.set(tx + 10, ty + 2, tz + 2, "minecraft:light_weighted_pressure_plate")
    bb.set(tx + 10, ty + 1, tz + 8, "minecraft:red_bed[facing=west,part=head]"); bb.set(tx + 9, ty + 1, tz + 8, "minecraft:red_bed[facing=west,part=foot]")
    bb.set(tx + 2, ty + 1, tz + 8, "minecraft:lantern")
    bb.fill(tx + 6, ty + 7, tz + 5, tx + 6, ty + 12, tz + 5, "minecraft:spruce_fence")
    bb.fill(tx + 7, ty + 10, tz + 5, tx + 9, ty + 12, tz + 5, "minecraft:black_wool")
    # the cook tent (open sided canopy) with stew pot, smoker, fish rack
    kx, kz = CX - 6, CZ + 12
    ky = hy(kx, kz)
    for (a, b) in ((0, 0), (8, 0), (0, 6), (8, 6)):
        bb.fill(kx + a, ky + 1, kz + b, kx + a, ky + 4, kz + b, "minecraft:spruce_fence")
    bb.fill(kx, ky + 5, kz, kx + 8, ky + 5, kz + 6, "minecraft:white_wool")
    bb.fill(kx + 1, ky + 5, kz + 1, kx + 7, ky + 5, kz + 5, "minecraft:light_gray_wool")
    bb.set(kx + 3, ky + 1, kz + 3, "minecraft:campfire[lit=true]"); bb.set(kx + 3, ky + 2, kz + 3, "minecraft:cauldron") if False else None
    bb.set(kx + 4, ky + 1, kz + 3, "minecraft:water_cauldron[level=3]")
    bb.set(kx + 6, ky + 1, kz + 1, "minecraft:smoker[facing=south,lit=true]")
    bb.set(kx + 7, ky + 1, kz + 1, "minecraft:barrel[facing=up]")
    bb.fill(kx + 1, ky + 1, kz + 5, kx + 3, ky + 1, kz + 5, "minecraft:spruce_slab[type=top]")
    for k in range(3):
        bb.set(kx + 1 + k, ky + 4, kz + 5, "minecraft:iron_chain[axis=y]")
    # wanted poster board
    wx, wz = CX - 4, CZ - 10
    wy = hy(wx, wz)
    bb.fill(wx, wy + 1, wz, wx, wy + 4, wz, "minecraft:spruce_fence"); bb.fill(wx + 6, wy + 1, wz, wx + 6, wy + 4, wz, "minecraft:spruce_fence")
    bb.fill(wx, wy + 3, wz, wx + 6, wy + 5, wz, "minecraft:spruce_planks")
    for (a, b) in ((1, 4), (3, 4), (5, 4), (2, 3), (4, 3)):
        bb.set(wx + a, wy + b, wz + 1, "minecraft:white_terracotta" if (a + b) % 2 else "minecraft:yellow_terracotta")
    bb.fill(wx, wy + 6, wz, wx + 6, wy + 6, wz, "minecraft:spruce_slab[type=bottom]")
    # target range on the grass to the north-west
    for k in range(4):
        x, z = 12 + k * 5, 14
        h = hy(x, z)
        bb.set(x, h + 1, z, "minecraft:hay_block"); bb.set(x, h + 2, z, "minecraft:target")
    for k in range(4):
        bb.set(12 + k * 5, hy(12 + k * 5, 24) + 1, 24, "minecraft:spruce_fence")
    # crates, kegs and cannon balls in stacks near the beach
    for (x, z, h) in ((70, 40, 2), (71, 40, 1), (70, 41, 1), (74, 43, 3), (75, 43, 2), (74, 44, 1), (30, 44, 2), (31, 44, 1)):
        yb = hy(x, z)
        for k in range(h):
            bb.set(x, yb + 1 + k, z, "minecraft:barrel[facing=up]" if (x + k) % 2 else "minecraft:spruce_planks")
    for (x, z) in ((72, 46), (34, 46), (66, 42)):
        bb.set(x, hy(x, z) + 1, z, "onepiece:cannonball_pile")
    bb.set(68, hy(68, 44) + 1, 44, "onepiece:cannon[facing=south]")
    # paths
    for (a, b) in (((CX, CZ + 8), (52, 56)), ((CX - 8, CZ), (24, 32)), ((CX + 8, CZ), (tx, tz + 5))):
        n = int(math.hypot(b[0] - a[0], b[1] - a[1]))
        for k in range(n):
            t = k / max(n, 1)
            x, z = int(round(a[0] + (b[0] - a[0]) * t)), int(round(a[1] + (b[1] - a[1]) * t))
            if _LAG(np.array(float(x)), np.array(float(z))) > -1:
                continue
            bb.set(x, hy(x, z), z, "minecraft:dirt_path" if hy(x, z) > 0 and k % 4 else "minecraft:coarse_dirt")
    for (x, z) in ((CX - 9, CZ - 9), (CX + 9, CZ + 9), (CX - 9, CZ + 9)):
        lamp_post(bb, x, hy(x, z) + 1, z, post="minecraft:spruce_fence", h=3)
    return (tx, tz, ty), (kx, kz, ky)


def design():
    bb = BigBuild(seed=4500, y_min=-10, y_max=60)
    rng = np.random.default_rng(4510)
    terrain(bb)
    where = caravel(bb)
    cap, cook = camp(bb, rng)
    lookout(bb)
    placed = []
    for _ in range(400):
        if len(placed) >= 16:
            break
        x, z = int(rng.integers(6, NX - 6)), int(rng.integers(6, NZ - 6))
        d = _LAND(np.array(float(x)), np.array(float(z)))
        if d < 4 or _LAG(np.array(float(x)), np.array(float(z))) > -3 or hy(x, z) < 1:
            continue
        if (CX - 26 < x < CX + 30 and CZ - 26 < z < CZ + 20) or (30 < x < 92 and 52 < z < 90) or any(math.hypot(x - a, z - b) < 7 for (a, b) in placed):
            continue
        placed.append((x, z))
        palm(bb, x, z, int(rng.integers(9, 15)), (int(rng.integers(-4, 5)), 3 if z > 48 else int(rng.integers(-3, 4))), rng)
    return bb, [], where, cap, cook


def build():
    bb, audit, where, cap, cook = design()
    b = to_canvas(bb)
    steady(b)
    b.chest(cap[0] + 9, cap[2] + 1, cap[1] + 3, "pirate", "west")
    b.chest(cook[0] + 7, cook[2] + 2, cook[1] + 1, "easy", "south")
    x, y, z = where(5, 8, 0)
    b.chest(x, y, z, "pirate", "east")
    for (x, z, kit) in ((CX + 3, CZ + 3, "rookie_pirate"), (CX - 3, CZ - 4, "rookie_pirate"), (CX + 10, CZ + 4, "pirate_gunner"),
                        (24, 36, "rookie_pirate")):
        b.guard(x, hy(x, z) + 1, z, kit)
    return b, 0
