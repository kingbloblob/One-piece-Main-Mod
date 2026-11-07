"""Cocoyasi Village v2, Nami's home village on the Conomi Islands, redesigned with the Minecraft Builder skill.

A warm green island with the sea on the west. The village sits on level ground round its square, where Genzo's
pinwheels turn on their posts: bright cottages of the East Blue (white, orange and sky-blue walls under copper,
teal and terracotta roofs), Doctor Nako's two-storey clinic, Genzo's little police post, the store and the inn.
To the east, up the hill inside its fence, Bellemere's small house stands among the rows of her tangerine grove,
which Nojiko still tends. On the cliff to the north-west, looking out over the sea, Bellemere's grave with its
pinwheel and flowers. On the west shore the fishing pier, the boats drawn up on the sand and the Going Merry tied
up. 160 x 160. y 0 = sea surface. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, furnish, set_if_air, house_module, place_house, lamp_post
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.shipstamp import stamp_ship

SID = "cocoyasi_village"
TITLE = "Cocoyasi Village (Tangerine Grove)"
# v3 (2026-10-30): Bellemere's grove is dense with big, fruit-heavy tangerine trees in staggered rows, ladders,
# baskets, a path from the gate and a harvest cart.
CUTS = [5, 11]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 160
_SH1 = NT.outline(98, 82, 60, 1720, wobble=0.08)
_SH2 = NT.outline(52, 42, 22, 1721, wobble=0.12)          # the grave headland


def SHORE(X, Z):
    return np.maximum(_SH1(X, Z), _SH2(X, Z))


VIL = (50, 62, 112, 112)
VY = 3
SQ = (70, 78, 94, 98)                                     # the square
GROVE = (116, 52, 146, 104)                               # Bellemere's tangerine grove
GY = 9
GRAVE = (46, 36)
GRAVE_Y = 12
PIER_Z = 92

SAND = [("minecraft:sand", 0.74), ("minecraft:sandstone", 0.08), ("minecraft:gravel", 0.08), ("minecraft:clay", 0.10)]
ROCK = [("minecraft:stone", 0.36), ("minecraft:andesite", 0.18), ("minecraft:diorite", 0.12), ("minecraft:tuff", 0.1),
        ("minecraft:cobblestone", 0.1), ("minecraft:mossy_cobblestone", 0.08), ("minecraft:gravel", 0.06)]
LANE = [("minecraft:dirt_path", 0.45), ("minecraft:coarse_dirt", 0.2), ("minecraft:packed_mud", 0.15), ("minecraft:gravel", 0.2)]
PAVE = [("minecraft:smooth_sandstone", 0.3), ("minecraft:sandstone", 0.18), ("minecraft:cut_sandstone", 0.16),
        ("minecraft:packed_mud", 0.12), ("minecraft:mud_bricks", 0.12), ("minecraft:dirt_path", 0.12)]


def rect_d(X, Z, r):
    dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0)
    dz = np.maximum(np.maximum(r[1] - Z, Z - r[3]), 0)
    return np.hypot(dx, dz)


def seg_d(X, Z, a, b):
    ax, az = a; bx, bz = b
    vx, vz = bx - ax, bz - az
    t = np.clip(((X - ax) * vx + (Z - az) * vz) / float(vx * vx + vz * vz), 0, 1)
    return np.hypot(X - ax - t * vx, Z - az - t * vz)


LANES = [((32, PIER_Z), (SQ[0], (SQ[1] + SQ[3]) // 2)), ((SQ[2], 88), (GROVE[0], 80)), ((82, SQ[1]), (60, 52)),
         ((60, 52), (GRAVE[0] + 4, GRAVE[1] + 6))]


def lane_d(X, Z):
    d = np.full(np.broadcast(X, Z).shape, 1e9)
    for a, b in LANES:
        d = np.minimum(d, seg_d(X, Z, a, b))
    return d


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = SHORE(X, Z)
    h = 4 + 6 * np.exp(-((X - 134) ** 2 + (Z - 78) ** 2) / (2 * 26.0 ** 2)) + NT.fbm(X, Z, 1722, 24) * 4 - 1
    head = np.exp(-((X - GRAVE[0]) ** 2 + (Z - GRAVE[1]) ** 2) / (2 * 14.0 ** 2))
    h = h + head * (GRAVE_Y - 4)
    # cliffs on the headland and the north, a beach on the west where the pier is
    beach = np.exp(-((Z - PIER_Z) ** 2) / (2 * 22.0 ** 2)) * (X < 70)
    k = 3 + 12 * beach + 6 * (Z > 110)
    h = h * np.clip((d - 1.5) / k, 0, 1)
    for (r, y, s) in ((VIL, VY, 9.0), (GROVE, GY, 8.0)):
        w = np.clip(rect_d(X, Z, r) / s, 0, 1)
        h = y * (1 - w) + h * w
    w = np.clip((np.hypot(X - GRAVE[0], Z - GRAVE[1]) - 5) / 6.0, 0, 1)
    h = GRAVE_Y * (1 - w) + h * w
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
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SAND, 1731,
             mask=lambda X, Z: land(X, Z) & (height(X, Z) <= 1) & ~steep(X, Z), under="minecraft:sandstone", core="minecraft:sandstone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, ROCK, 1732, mask=lambda X, Z: land(X, Z) & steep(X, Z), under="minecraft:stone",
             core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, NT.MEADOW, 1733,
             mask=lambda X, Z: land(X, Z) & (height(X, Z) > 1) & ~steep(X, Z), core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, height, LANE, 1734,
             mask=lambda X, Z: land(X, Z) & (height(X, Z) > 1) & (lane_d(X, Z) <= 1.6 + NT.noise(X, Z, 1735, 3)), core="minecraft:stone")
    for y in range(-12, 0):
        bb.fill_where(0, y, 0, N - 1, y, N - 1, lambda X, yy, Z: (SHORE(X, Z) <= 1.5) &
                      (yy > -2 - np.clip(-SHORE(X, Z) * 0.7, 0, 10)), "minecraft:water")
        bb.fill_where(0, y, 0, N - 1, y, N - 1, lambda X, yy, Z: (SHORE(X, Z) <= 1.5) &
                      (yy == np.round(-2 - np.clip(-SHORE(X, Z) * 0.7, 0, 10))), "minecraft:sand")


# ------------------------------------------------------------------ the village
PALS = [
    dict(walls=["minecraft:white_terracotta", "minecraft:calcite", "minecraft:white_concrete"], frame="minecraft:stripped_spruce_log",
         base=["minecraft:cobblestone", "minecraft:stone_bricks", "minecraft:mossy_cobblestone"], floor="minecraft:spruce_planks",
         wood="spruce", chimney="minecraft:bricks"),
    dict(walls=["minecraft:orange_terracotta", "minecraft:orange_terracotta", "minecraft:white_terracotta"], frame="minecraft:dark_oak_log",
         base=["minecraft:cobblestone", "minecraft:stone_bricks", "minecraft:andesite"], floor="minecraft:oak_planks",
         wood="dark_oak", chimney="minecraft:bricks"),
    dict(walls=["minecraft:light_blue_terracotta", "minecraft:white_terracotta", "minecraft:light_blue_terracotta"],
         frame="minecraft:stripped_birch_log", base=["minecraft:cobblestone", "minecraft:stone_bricks", "minecraft:mossy_cobblestone"],
         floor="minecraft:birch_planks", wood="birch", chimney="minecraft:stone_bricks"),
    dict(walls=["minecraft:smooth_sandstone", "minecraft:white_terracotta", "minecraft:smooth_sandstone"], frame="minecraft:spruce_log",
         base=["minecraft:cobblestone", "minecraft:mossy_cobblestone", "minecraft:stone_bricks"], floor="minecraft:spruce_planks",
         wood="spruce", chimney="minecraft:bricks"),
]
ROOFS = ["minecraft:waxed_cut_copper_stairs", "minecraft:dark_prismarine_stairs", "minecraft:brick_stairs", "minecraft:warped_stairs",
         "minecraft:red_sandstone_stairs", "minecraft:waxed_cut_copper_stairs"]
KINDS = [["kitchen", "bedroom"], ["living", "bedroom"], ["workshop", "bedroom", "storage"], ["kitchen", "living", "bedroom"]]
# (x, z, w, d, floors, rot): rot 0 door south, 2 door north, 1 door west, 3 door east
HOUSES = [(54, 64, 9, 8, 2, 0), (66, 65, 8, 8, 2, 0), (78, 64, 10, 9, 2, 0), (92, 65, 8, 8, 2, 0), (102, 64, 9, 8, 2, 0),
          (54, 104, 9, 8, 2, 2), (66, 105, 8, 8, 1, 2), (92, 104, 9, 8, 2, 2), (104, 105, 8, 8, 1, 2),
          (52, 78, 8, 8, 2, 3), (101, 78, 9, 8, 2, 1), (101, 92, 8, 8, 1, 1)]


def pinwheel(bb, x, y, z, h, cols, axis="z"):
    """One of Genzo's pinwheels: a post with four coloured vanes round the hub."""
    bb.fill(x, y, z, x, y + h - 1, z, "minecraft:spruce_fence")
    hub = (x, y + h, z)
    bb.set(*hub, "minecraft:white_wool")
    vanes = [(0, 1, 1), (1, 0, -1), (0, -1, -1), (-1, 0, 1)]
    for k, (du, dv, s) in enumerate(vanes):
        c = cols[k % len(cols)]
        for (a, b) in ((du, dv), (du + (dv * s if dv else 0), dv + (du * -s if du else 0))):
            if axis == "z":
                bb.set(x + a, y + h + b, z, f"minecraft:{c}_wool")
            else:
                bb.set(x, y + h + b, z + a, f"minecraft:{c}_wool")


def village(bb, tracker, audit, rng):
    taken = []
    NT.cover(bb, SQ[0] - 3, SQ[1] - 3, SQ[2] + 3, SQ[3] + 3, lambda X, Z: X * 0 + VY, PAVE, 1741,
             mask=lambda X, Z: rect_d(X, Z, SQ) <= 1.5 + 2 * NT.noise(X, Z, 1742, 3), core="minecraft:stone")
    for k, (x, z, w, d, fl, rot) in enumerate(HOUSES):
        mod, _, au = house_module(seed_of("cv", k), w, d, fl, ROOFS[k % len(ROOFS)], tracker, KINDS[k % len(KINDS)],
                                  pal=PALS[k % len(PALS)], timber=(k % 3 == 0), jetty=False)
        audit += au
        place_house(bb, mod, w, d, x, VY, z, rot)
        ww, dd = (w, d) if rot % 2 == 0 else (d, w)
        taken.append((x - 1, z - 1, x + ww, z + dd))
    # Doctor Nako's clinic: two storeys, white with a red cross sign
    mod, _, au = house_module(seed_of("cvclinic"), 12, 10, 2, "minecraft:brick_stairs", tracker, ["bedroom", "storage", "living"],
                              pal=PALS[0], timber=False, jetty=False)
    audit += au
    place_house(bb, mod, 12, 10, 82, VY, 104, 2)
    taken.append((81, 103, 94, 114))
    for (dx, dy) in ((0, 0), (-1, 0), (1, 0), (0, 1), (0, -1)):
        bb.set(88 + dx, VY + 7 + dy, 103, "minecraft:red_concrete")
    # Genzo's police post: a tiny house with a lamp and a signboard
    mod, _, au = house_module(seed_of("cvgenzo"), 6, 6, 1, "minecraft:dark_prismarine_stairs", tracker, ["storage"], pal=PALS[2],
                              timber=False, jetty=False)
    audit += au
    place_house(bb, mod, 6, 6, 62, VY, 90, 3)
    taken.append((61, 89, 68, 96))
    # the square: pinwheels round it and on the houses, the well, benches, a fruit stall
    cols = [("red", "yellow", "blue", "white"), ("orange", "light_blue", "lime", "pink"), ("yellow", "red", "white", "cyan")]
    k = 0
    for x in range(SQ[0] + 1, SQ[2], 4):
        for z in (SQ[1] + 1, SQ[3] - 1):
            pinwheel(bb, x, VY + 1, z, 3 + (k % 2), cols[k % 3], axis="z")
            k += 1
    for z in range(SQ[1] + 5, SQ[3] - 3, 4):
        for x in (SQ[0] + 1, SQ[2] - 1):
            pinwheel(bb, x, VY + 1, z, 3 + (k % 2), cols[k % 3], axis="x")
            k += 1
    cx, cz = (SQ[0] + SQ[2]) // 2, (SQ[1] + SQ[3]) // 2
    bb.fill(cx - 1, VY + 1, cz - 1, cx + 1, VY + 1, cz + 1, "minecraft:cobblestone_wall")
    bb.fill(cx, VY - 6, cz, cx, VY + 1, cz, "minecraft:water")
    for (x, z) in ((cx - 1, cz - 1), (cx + 1, cz + 1)):
        bb.fill(x, VY + 2, z, x, VY + 3, z, "minecraft:spruce_fence")
    bb.fill(cx - 1, VY + 4, cz - 1, cx + 1, VY + 4, cz + 1, "minecraft:waxed_cut_copper_slab[type=bottom]")
    pinwheel(bb, cx, VY + 5, cz, 2, cols[0], axis="z")
    for (x, z, f) in ((cx - 5, cz - 4, "south"), (cx - 4, cz - 4, "south"), (cx + 4, cz + 4, "north"), (cx + 5, cz + 4, "north")):
        bb.set(x, VY + 1, z, st("minecraft:spruce_stairs", f))
    # the tangerine stall
    sx, sz = cx + 4, cz - 3
    bb.fill(sx, VY + 1, sz, sx + 3, VY + 1, sz, "minecraft:spruce_planks")
    bb.fill(sx, VY + 2, sz, sx + 3, VY + 2, sz, "minecraft:spruce_trapdoor[facing=north,half=bottom,open=false]")
    for x in (sx, sx + 3):
        bb.fill(x, VY + 1, sz + 2, x, VY + 3, sz + 2, "minecraft:spruce_fence")
    bb.fill(sx - 1, VY + 4, sz - 1, sx + 4, VY + 4, sz + 2, "minecraft:orange_wool")
    bb.set(sx + 1, VY + 2, sz, "minecraft:barrel[facing=up,open=false]")
    for (x, z) in ((SQ[0] - 2, SQ[1] - 2), (SQ[2] + 2, SQ[1] - 2), (SQ[0] - 2, SQ[3] + 2), (SQ[2] + 2, SQ[3] + 2)):
        lamp_post(bb, x, VY + 1, z, post="minecraft:spruce_fence", h=3)
    # flower boxes and palms round the village
    for (x, z) in ((48, 90), (114, 70), (114, 112), (48, 112), (70, 120)):
        if land(np.array([[x]]), np.array([[z]]))[0, 0]:
            from mcb.kit import palm
            palm(bb, x, hy(x, z) + 1, z, 8, lean=(1 if x < 80 else -1, 0))
            taken.append((x - 3, z - 3, x + 3, z + 3))
    return taken


# ------------------------------------------------------------------ Bellemere's house and the tangerine grove
def tangerine_tree(bb, x, y, z, rng):
    """A full, round-crowned tangerine tree (v3: bigger and heavier with fruit): a short forked trunk, a dense dome of
    leaves with two lobes, and a dozen or more tangerines hanging on its outside."""
    log = "minecraft:jungle_log[axis=y]"
    leaves = ["minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]",
              "minecraft:azalea_leaves[distance=7,persistent=true,waterlogged=false]"]
    h = int(rng.integers(3, 5))
    bb.fill(x, y, z, x, y + h - 1, z, log)
    r = rng.uniform(3.0, 3.8)
    cy = y + h + 1
    lobes = [(x, cy, z, r)]
    for k in range(2):
        a = rng.uniform(0, 6.283)
        lx, lz = x + round(1.6 * math.cos(a)), z + round(1.6 * math.sin(a))
        bb.set(lx if abs(lx - x) <= 1 else x + (1 if lx > x else -1), y + h - 1, lz if abs(lz - z) <= 1 else z + (1 if lz > z else -1),
               "minecraft:jungle_wood[axis=y]")
        lobes.append((lx, cy + 1, lz, r * 0.75))
    R = int(r) + 3
    for i, (lx, ly, lz, rr) in enumerate(lobes):
        bb.fill_where(lx - R, ly - R, lz - R, lx + R, ly + R, lz + R,
                      lambda X, yy, Z, lx=lx, ly=ly, lz=lz, rr=rr: ((X - lx) ** 2 + ((yy - ly) * 1.35) ** 2 + (Z - lz) ** 2 <= rr * rr)
                      & (NT.noise(X * 3 + yy, Z * 3, int(x * 13 + z + i), 1) < 0.93), leaves[i % 2 if i else 0], only_empty=True)
    for k in range(int(rng.integers(12, 19))):                    # the fruit, set into the outside of the canopy
        a = rng.uniform(0, 6.283)
        fy = cy + int(rng.integers(-2, 2))
        rr = r - 0.6 - abs(fy - cy) * 0.5
        fx, fz = x + int(round(math.cos(a) * rr)), z + int(round(math.sin(a) * rr))
        bb.set(fx, fy, fz, "minecraft:orange_terracotta" if k % 3 else "minecraft:orange_concrete")


def grove(bb, tracker, audit, rng):
    x1, z1, x2, z2 = GROVE
    y = GY
    # the fence and gate
    for x in range(x1, x2 + 1):
        bb.set(x, y + 1, z1, "minecraft:spruce_fence"); bb.set(x, y + 1, z2, "minecraft:spruce_fence")
    for z in range(z1, z2 + 1):
        bb.set(x1, y + 1, z, "minecraft:spruce_fence"); bb.set(x2, y + 1, z, "minecraft:spruce_fence")
    gz = 80
    bb.set(x1, y + 1, gz, "minecraft:spruce_fence_gate[facing=east,open=true]")
    bb.set(x1, y + 1, gz + 1, "minecraft:spruce_fence_gate[facing=east,open=true]")
    for z in (gz - 1, gz + 2):
        bb.fill(x1, y + 1, z, x1, y + 3, z, "minecraft:spruce_log[axis=y]")
    bb.fill(x1, y + 4, gz - 1, x1, y + 4, gz + 2, "minecraft:spruce_slab[type=bottom]")
    # the house: a little one-storey cottage with a porch, orange walls, sky-blue roof
    pal = dict(walls=["minecraft:white_terracotta", "minecraft:white_terracotta", "minecraft:calcite"], frame="minecraft:stripped_oak_log",
               base=["minecraft:cobblestone", "minecraft:mossy_cobblestone", "minecraft:stone_bricks"], floor="minecraft:oak_planks",
               wood="oak", chimney="minecraft:bricks")
    hx, hz = 128, 70
    mod, _, au = house_module(seed_of("cvbelle"), 11, 9, 1, "minecraft:dark_prismarine_stairs", tracker, ["kitchen", "bedroom"], pal=pal,
                              timber=True, jetty=False)
    audit += au
    place_house(bb, mod, 11, 9, hx, y, hz, 0)
    for x in range(hx, hx + 11):                                       # porch
        bb.set(x, y + 1, hz + 10, "minecraft:oak_slab[type=bottom]") if False else None
    bb.fill(hx - 1, y + 4, hz + 9, hx + 11, y + 4, hz + 11, "minecraft:spruce_slab[type=bottom]")
    for x in (hx - 1, hx + 11):
        bb.fill(x, y + 1, hz + 11, x, y + 3, hz + 11, "minecraft:spruce_fence")
    bb.set(hx + 2, y + 1, hz + 10, st("minecraft:spruce_stairs", "west"))
    bb.set(hx + 8, y + 1, hz + 10, "minecraft:barrel[facing=up,open=false]")
    bb.set(hx + 9, y + 1, hz + 10, "minecraft:composter")
    # the washing line
    bb.fill(hx + 13, y + 1, hz + 2, hx + 13, y + 3, hz + 2, "minecraft:spruce_fence")
    bb.fill(hx + 19, y + 1, hz + 2, hx + 19, y + 3, hz + 2, "minecraft:spruce_fence")
    bb.fill(hx + 14, y + 3, hz + 2, hx + 18, y + 3, hz + 2, "minecraft:spruce_fence")
    for (x, c) in ((hx + 15, "white"), (hx + 16, "light_blue"), (hx + 17, "orange")):
        bb.set(x, y + 2, hz + 2, f"minecraft:{c}_carpet") if False else bb.set(x, y + 2, hz + 2, f"minecraft:{c}_banner[rotation=0]") if False else None
    taken = [(hx - 2, hz - 2, hx + 20, hz + 13)]
    # rows of tangerine trees, a path down the middle
    k = 0
    for i, x in enumerate(range(x1 + 4, x2 - 2, 6)):                    # staggered rows, crowns touching
        for z in range(z1 + 4 + (3 if i % 2 else 0), z2 - 2, 6):
            if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken) or abs(z - gz) < 4:
                continue
            tangerine_tree(bb, x, y + 1, z, rng)
            k += 1
            if k % 5 == 2:                                                # a ladder against the tree, a basket below
                bb.fill(x + 1, y + 1, z, x + 1, y + 3, z, "minecraft:ladder[facing=east]")
                bb.set(x + 2, y + 1, z + 1, "minecraft:composter")
            elif k % 5 == 4:
                bb.set(x - 2, y + 1, z + 1, "minecraft:barrel[facing=up,open=false]")
                bb.set(x - 2, y + 2, z + 1, "minecraft:orange_carpet")
    # the path through the grove from the gate, and a harvest cart by the house
    for x in range(x1 + 1, x2):
        for z in (gz, gz + 1):
            if not any(t[0] <= x <= t[2] and t[1] <= z <= t[3] for t in taken):
                bb.set(x, y, z, "minecraft:dirt_path")
    cx_, cz_ = hx - 4, hz + 12
    bb.fill(cx_, y + 1, cz_, cx_ + 2, y + 1, cz_ + 1, "minecraft:spruce_slab[type=top]")
    bb.fill(cx_, y + 2, cz_, cx_ + 2, y + 2, cz_ + 1, "minecraft:orange_concrete")
    bb.set(cx_ - 1, y + 1, cz_, "minecraft:spruce_fence"); bb.set(cx_ + 3, y + 1, cz_ + 1, "minecraft:spruce_trapdoor[facing=west,half=bottom,open=true]")
    for (x, z) in ((x1 + 4, gz + 3), (x1 + 9, gz + 3)):
        bb.set(x, y + 1, z, "minecraft:barrel[facing=up,open=false]")
    print("tangerine trees:", k)
    return (x1 - 1, z1 - 1, x2 + 1, z2 + 1)


def grave(bb):
    x, z = GRAVE
    y = GRAVE_Y
    bb.fill(x - 1, y + 1, z, x + 1, y + 1, z, "minecraft:stone_bricks")
    bb.fill(x, y + 2, z, x, y + 3, z, "minecraft:stone_bricks")
    bb.set(x - 1, y + 3, z, "minecraft:stone_brick_wall"); bb.set(x + 1, y + 3, z, "minecraft:stone_brick_wall")
    bb.set(x, y + 4, z, "minecraft:stone_brick_slab[type=bottom]")
    for (dx, dz, f) in ((-1, 1, "minecraft:poppy"), (0, 1, "minecraft:dandelion"), (1, 1, "minecraft:cornflower"),
                        (-2, 1, "minecraft:oxeye_daisy"), (2, 1, "minecraft:poppy"), (1, 2, "minecraft:allium")):
        bb.set(x + dx, y, z + dz, "minecraft:grass_block")
        bb.set(x + dx, y + 1, z + dz, f)
    pinwheel(bb, x + 2, y + 1, z, 2, ("red", "yellow", "blue", "white"), axis="z")
    bb.set(x - 2, y + 1, z + 1, "minecraft:candle[candles=3,lit=true]") if False else None
    # a bench facing the sea
    bb.set(x - 3, y + 1, z - 3, st("minecraft:spruce_stairs", "south"))
    bb.set(x - 2, y + 1, z - 3, st("minecraft:spruce_stairs", "south"))
    return (x - 6, z - 6, x + 6, z + 6)


def harbour(bb, rng):
    z = PIER_Z
    x0 = 44
    while x0 > 2 and hy(x0, z) > 0:
        x0 -= 1
    for x in range(x0 - 26, x0 + 3):
        bb.fill(x, 0, z - 1, x, 0, z + 1, "minecraft:spruce_planks")
        if x % 4 == 0:
            for zz in (z - 2, z + 2):
                bb.fill(x, -10, zz, x, 1, zz, "minecraft:spruce_log[axis=y]")
            bb.set(x, 2, z + 2, "minecraft:lantern[hanging=false]")
    bb.fill(x0 - 30, 0, z - 4, x0 - 26, 0, z + 4, "minecraft:spruce_planks")
    stamp_ship(bb, "going_merry", x0 - 18, z + 20, water_y=0, rot=3)
    # fishing boats drawn up on the beach and moored by the pier
    for (bx, bz, ax) in ((x0 - 8, z - 6, "x"), (x0 + 2, z - 12, "z"), (x0 + 4, z + 8, "z")):
        y = max(0, hy(bx, bz))
        L = 6
        for i in range(L):
            for j in (-1, 0, 1):
                xx, zz = (bx + i, bz + j) if ax == "x" else (bx + j, bz + i)
                end = i in (0, L - 1)
                if end and j:
                    continue
                if j == 0 and not end:
                    bb.set(xx, y, zz, "minecraft:oak_planks")
                    bb.set(xx, y + 1, zz, AIR)
                else:
                    bb.set(xx, y + 1, zz, st("minecraft:oak_stairs", ("north" if j > 0 else "south") if ax == "x" else
                                             ("west" if j > 0 else "east")) if j else "minecraft:oak_planks")
                    bb.set(xx, y, zz, "minecraft:oak_planks")
        bb.set(bx + (2 if ax == "x" else 0), y + 1, bz + (0 if ax == "x" else 2), "minecraft:barrel[facing=up,open=false]")
    # nets drying on poles
    for k in range(3):
        px = x0 + 6 + k * 4
        bb.fill(px, hy(px, z - 8) + 1, z - 8, px, hy(px, z - 8) + 3, z - 8, "minecraft:spruce_fence")
    return (x0 - 32, z - 14, x0 + 12, z + 22)


def scenery(bb, rng, taken):
    k = 0
    for _ in range(4000):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        X, Z = np.array([[x]]), np.array([[z]])
        if SHORE(X, Z)[0, 0] < 5 or GRAD[x, z] >= 2 or lane_d(X, Z)[0, 0] < 3:
            continue
        if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken):
            continue
        y = hy(x, z)
        if y < 1:
            continue
        near = SHORE(X, Z)[0, 0] < 12
        if near:
            from mcb.kit import palm
            palm(bb, x, y + 1, z, int(rng.integers(6, 10)), lean=(int(rng.integers(-1, 2)), int(rng.integers(-1, 2))))
        else:
            if NT.noise(X, Z, 1771, 20)[0, 0] < 0.4 and rng.random() > 0.25:
                continue
            P.tree(bb, x, y + 1, z, int(rng.integers(5, 9)), ("oak", "jungle", "oak", "birch")[k % 4], rng)
        taken.append((x - 3, z - 3, x + 3, z + 3))
        k += 1
        if k >= 60:
            break
    rocks = 0
    for _ in range(400):
        x, z = int(rng.integers(4, N - 4)), int(rng.integers(4, N - 4))
        if GRAD[x, z] >= 2 and hy(x, z) > 2 and rocks < 10:
            NT.boulder(bb, x, hy(x, z), z, rng.uniform(1.5, 2.6), rng)
            rocks += 1
    print("trees:", k, "rocks:", rocks)


def design():
    bb = BigBuild(seed=1720, y_min=-14, y_max=60)
    tracker = P.PropTracker(1720)
    audit = []
    rng = np.random.default_rng(1720)
    terrain(bb)
    taken = village(bb, tracker, audit, rng)
    taken.append(grove(bb, tracker, audit, rng))
    taken.append(grave(bb))
    taken.append(harbour(bb, rng))
    taken.append(VIL)
    scenery(bb, rng, taken)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 1790, density=0.3, kinds=NT.PLANTS_MEADOW, flowers=NT.FLOWERS,
              mask=lambda X, Z: land(X, Z) & (rect_d(X, Z, SQ) > 4) & (lane_d(X, Z) > 2.5))
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
    b.npc(134, GY + 1, 83, "nami", False)
    b.chest(130, GY + 1, 72, "easy", "south")
    return b, 0
