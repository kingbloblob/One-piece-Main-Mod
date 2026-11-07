"""Mirror Hall v2, redesigned with the Minecraft Builder skill: Charlotte Brulee's Mirror Hall on a Totto Land sweet
island, the doorway into the Mirro-World where Luffy and Katakuri fought (manga ch. 880-896, anime 850-871).

Silhouette first: a round frosting-white palace with a huge pink glass dome on gold ribs, ringed by slim pink-capped
towers, its walls set with tall framed mirrors that catch the sky; sweet gardens of candy-cane trees, cotton-candy
trees and a chocolate fountain round it on a sugar-sand island.

Inside, the Mirro-World arena under the dome: a checkered pink and white floor, dozens of framed mirrors of every
shape hanging at every height (as in the anime, where the whole world is mirrors), Katakuri's mochi pillars rising
out of the floor, and Brulee's own giant oval mirror. Off the arena: a mirror maze corridor, Brulee's dressing room,
the kitchen and pantry, and up a hidden stair Katakuri's secret snack room (his big armchair and the donut feast).
150 x 150, y 0 = sea surface, island ground ~y 3. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, set_if_air, tier, cornice, lamp_post, steady
from mcb.kit_interiors import furnish_kit, table_group, wall_lights, bench
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "mirror_hall"
TITLE = "Brulee's Mirror Hall"
CUTS = [5, 14, 26]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 150
CX, CZ = 75, 72
GY = 3
R = 30                      # palace radius (outer wall)
WH = 22                     # wall height
_ISLE = NT.outline(75, 75, 64, 8801, wobble=0.08)
FROST = "onepiece:frosting_block"
CHOC = "onepiece:chocolate_block"
COOKIE = "onepiece:cookie_bricks"
MIRROR = "minecraft:light_blue_stained_glass"
FRAME = "minecraft:gold_block"
SWEET = [("minecraft:grass_block", 0.45), ("onepiece:sugar_sand", 0.25), ("minecraft:moss_block", 0.1),
         ("onepiece:chocolate_moss", 0.0), ("minecraft:pink_concrete_powder", 0.0), ("minecraft:podzol", 0.08), ("minecraft:rooted_dirt", 0.12)]


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = _ISLE(X, Z)
    h = GY + NT.fbm(X, Z, 8802, 20) * 4 * np.clip((np.hypot(X - CX, Z - CZ) - R - 8) / 10.0, 0, 1)
    h = np.where(d < 10, -5 + (h + 5) * np.clip(d / 10.0, 0, 1) ** 1.2, h)
    return np.round(h)


X_, Z_ = np.arange(N)[:, None].astype(float), np.arange(N)[None, :].astype(float)
HMAP = _height(X_, Z_).astype(int)


def _ix(X, Z):
    return np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)


def height(X, Z):
    return HMAP[_ix(X, Z)]


def land(X, Z):
    return HMAP[_ix(X, Z)] >= 1


def hy(x, z):
    return int(HMAP[min(max(int(x), 0), N - 1), min(max(int(z), 0), N - 1)])


def terrain(bb):
    beach = lambda X, Z: land(X, Z) & (_ISLE(X, Z) < 12)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, SWEET, 8803, mask=lambda X, Z: land(X, Z) & ~beach(X, Z), core="minecraft:stone", base=-6)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, [("onepiece:sugar_sand", 0.7), ("minecraft:sand", 0.2), ("minecraft:white_concrete_powder", 0.0),
                                              ("minecraft:sandstone", 0.1)], 8804, mask=beach, under="minecraft:sandstone", core="minecraft:stone", base=-6)
    wet = lambda X, Z: ~land(X, Z)
    bed = lambda X, Z: np.minimum(height(X, Z), -2) - np.clip(-_ISLE(X, Z) / 5.0, 0, 5).astype(int)
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, y, Z: wet(X, Z) & (y > bed(X, Z)), "minecraft:water")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, y, Z: wet(X, Z) & (y == bed(X, Z)), "minecraft:sand")
    bb.fill_where(0, -12, 0, N - 1, 0, N - 1, lambda X, y, Z: wet(X, Z) & (y < bed(X, Z)) & (y >= bed(X, Z) - 3), "minecraft:sandstone")


def ring_d(X, Z):
    return np.hypot(np.asarray(X, float) - CX, np.asarray(Z, float) - CZ)


def annulus(bb, cx, y1, cz, rin, rout, y2, block):
    """Ring between rin (exclusive) and rout (inclusive), float radii allowed."""
    m = int(math.ceil(rout)) + 1
    for y in range(int(y1), int(y2) + 1):
        bb.fill_where(cx - m, y, cz - m, cx + m, y, cz + m,
                      lambda X, yy, Z: (np.hypot(X - cx, Z - cz) > rin) & (np.hypot(X - cx, Z - cz) <= rout), block)


def palace(bb):
    """Round outer wall with mirror bays between frosting pilasters, a chocolate base course, a cookie cornice."""
    y = GY
    bb.fill_where(CX - R - 3, y - 3, CZ - R - 3, CX + R + 3, y, CZ + R + 3, lambda X, yy, Z: ring_d(X, Z) <= R + 2, COOKIE)
    bb.fill_where(CX - R, y, CZ - R, CX + R, y, CZ + R, lambda X, yy, Z: ring_d(X, Z) <= R - 1,
                  "minecraft:pink_glazed_terracotta" if False else "minecraft:white_concrete")
    bb.fill_where(CX - R, y, CZ - R, CX + R, y, CZ + R, lambda X, yy, Z: (ring_d(X, Z) <= R - 1) & (((X // 3) + (Z // 3)) % 2 == 0),
                  "minecraft:pink_concrete")
    annulus(bb, CX, y + 1, CZ, R - 1.5, R, y + WH, FROST)
    annulus(bb, CX, y + 1, CZ, R - 1.5, R, y + 2, CHOC)
    annulus(bb, CX, y + WH - 1, CZ, R - 1.5, R + 1, y + WH, COOKIE)
    # mirror bays: 24 tall framed mirrors round the wall, pilasters standing proud between them
    n = 24
    for i in range(n):
        a = 2 * math.pi * i / n
        for k in range(-1, 2):
            t = a + k * 0.035
            x, z = CX + int(round((R + 0.2) * math.cos(t))), CZ + int(round((R + 0.2) * math.sin(t)))
            bb.fill(x, y + 4, z, x, y + 16, z, MIRROR)
        x0, z0 = CX + int(round((R + 0.2) * math.cos(a))), CZ + int(round((R + 0.2) * math.sin(a)))
        bb.set(x0, y + 17, z0, FRAME); bb.set(x0, y + 3, z0, FRAME)
        ap = a + math.pi / n
        px, pz = CX + int(round((R + 1) * math.cos(ap))), CZ + int(round((R + 1) * math.sin(ap)))
        bb.fill(px, y + 1, pz, px, y + WH, pz, "minecraft:quartz_pillar[axis=y]")
        bb.set(px, y + WH + 1, pz, "minecraft:pink_stained_glass")
        bb.set(px, y + 12, pz, "minecraft:pearlescent_froglight[axis=y]")
    # the dome: pink glass shell on gold ribs, a lantern cupola with a heart finial
    dy = y + WH
    for yy in range(0, R):
        rr = math.sqrt(max(R * R - yy * yy * (R * R) / (R * 0.75) ** 2, 0))
        if rr < 1:
            break
        annulus(bb, CX, dy + yy, CZ, max(rr - 1.2, 0), rr, dy + yy, "minecraft:pink_stained_glass")
    for i in range(12):
        a = 2 * math.pi * i / 12
        for yy in range(0, int(R * 0.75) + 1):
            rr = math.sqrt(max(R * R - yy * yy * (R * R) / (R * 0.75) ** 2, 0))
            bb.set(CX + int(round(rr * math.cos(a))), dy + yy, CZ + int(round(rr * math.sin(a))), FRAME)
    top = dy + int(R * 0.75)
    bb.cylinder(CX, top - 1, CZ, 4, top + 4, "minecraft:quartz_block", hollow=True)
    bb.cylinder(CX, top, CZ, 3, top + 4, "minecraft:pink_stained_glass")
    P.cone_roof(bb, CX, top + 5, CZ, 5, 6, "minecraft:pink_terracotta")
    bb.fill(CX, top + 11, CZ, CX, top + 13, CZ, FRAME)
    for (dx, dy2) in ((-1, 0), (1, 0), (-1, 1), (1, 1), (0, -1), (-2, 1), (2, 1)):
        bb.set(CX + dx, top + 15 + dy2, CZ, "minecraft:red_concrete")
    # entrance: a tall arched portal on the south with a frosting porch and chocolate steps
    for x in range(CX - 4, CX + 5):
        for yy in range(y + 1, y + 13):
            if (x - CX) ** 2 / 16.0 + max(yy - y - 8, 0) ** 2 / 16.0 <= 1:
                bb.fill(x, yy, CZ + R - 3, x, yy, CZ + R + 1, AIR)
    for k in range(6):
        bb.fill(CX - 6, y - k, CZ + R + 2 + k, CX + 6, y - k, CZ + R + 2 + k, "onepiece:chocolate_stairs[facing=north]")
    for xx in (CX - 6, CX + 6):
        bb.fill(xx, y + 1, CZ + R + 1, xx, y + 14, CZ + R + 2, "minecraft:quartz_pillar[axis=y]")
    bb.fill(CX - 7, y + 15, CZ + R + 1, CX + 7, y + 15, CZ + R + 3, "onepiece:frosting_slab[type=bottom]")
    return top


def towers(bb):
    """Six slim towers round the palace: frosting shafts, mirror windows, pink cone caps with gold balls."""
    for i in range(6):
        a = 2 * math.pi * i / 6 + math.pi / 6
        tx, tz = CX + int(round((R + 3) * math.cos(a))), CZ + int(round((R + 3) * math.sin(a)))
        h = 32 if i % 2 else 38
        bb.cylinder(tx, GY - 2, tz, 4, GY + h, FROST, hollow=True)
        bb.cylinder(tx, GY, tz, 3, GY, "minecraft:white_concrete")
        for yy in range(GY + 6, GY + h - 2, 7):
            annulus(bb, tx, yy, tz, 3.2, 5, yy, COOKIE)
            for (dx, dz) in ((4, 0), (-4, 0), (0, 4), (0, -4)):
                bb.fill(tx + dx, yy + 2, tz + dz, tx + dx, yy + 4, tz + dz, MIRROR)
            bb.cylinder(tx, yy, tz, 3, yy, "minecraft:white_concrete")
            bb.set(tx, yy + 5, tz, "minecraft:pearlescent_froglight[axis=y]")
        P.cone_roof(bb, tx, GY + h + 1, tz, 6, 9, "minecraft:pink_terracotta")
        bb.set(tx, GY + h + 10, tz, FRAME)
        bb.fill(tx, GY + 1, tz, tx, GY + h, tz, "minecraft:ladder[facing=north]") if False else None
        # spiral of chocolate stairs inside
        for yy in range(GY + 1, GY + h - 2):
            k = yy % 8
            dx, dz = [(2, 0), (2, 1), (1, 2), (0, 2), (-1, 2), (-2, 1), (-2, 0), (-2, -1)][k]
            bb.set(tx + dx, yy, tz + dz, "onepiece:chocolate_block")


def mirror(bb, x, y, z, w, h, axis, shape, chain_to=None):
    """A framed mirror of the given shape ('rect', 'oval', 'round', 'arch'), hung from a chain up to chain_to."""
    cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
    for u in range(-1, w + 1):
        for v in range(-1, h + 1):
            if shape == "rect":
                inside = 0 <= u < w and 0 <= v < h
                edge = not inside and -1 <= u <= w and -1 <= v <= h
            else:
                ry = cy + (0 if shape != "arch" else 0)
                q = ((u - cx) / (cx + 0.6)) ** 2 + ((v - cy) / (cy + 0.6)) ** 2
                if shape == "arch" and v < cy:
                    q = ((u - cx) / (cx + 0.6)) ** 2 if 0 <= v else 9
                inside = q <= 1.0
                q2 = ((u - cx) / (cx + 1.6)) ** 2 + ((v - cy) / (cy + 1.6)) ** 2
                if shape == "arch" and v < cy:
                    q2 = ((u - cx) / (cx + 1.6)) ** 2 if v >= -1 else 9
                edge = not inside and q2 <= 1.0
            if not (inside or edge):
                continue
            px, pz = (x + u, z) if axis == "x" else (x, z + u)
            bb.set(px, y + v, pz, MIRROR if inside else FRAME)
    if chain_to is not None:
        px, pz = (x + int(cx), z) if axis == "x" else (x, z + int(cx))
        bb.fill(px, y + h + 1, pz, px, chain_to, pz, "minecraft:iron_chain[axis=y]")


def arena(bb, rng):
    """The Mirro-World under the dome: hanging mirrors at every height, mochi pillars, Brulee's great oval mirror."""
    y = GY
    inner = R - 8
    # inner ring wall separating the arena (r < 20) from the side rooms (r 21..28)
    annulus(bb, CX, y + 1, CZ, inner, inner + 1.5, y + 9, FROST)
    bb.fill_where(CX - R, y + 10, CZ - R, CX + R, y + 10, CZ + R, lambda X, yy, Z: (ring_d(X, Z) > inner) & (ring_d(X, Z) < R - 1),
                  "minecraft:white_concrete")
    for a in range(0, 360, 30):
        t = math.radians(a + 15)
        x, z = CX + int(round((inner + 0.7) * math.cos(t))), CZ + int(round((inner + 0.7) * math.sin(t)))
        bb.fill(x, y + 1, z, x, y + 3, z, AIR)
    # hanging mirrors: varied shapes and sizes in a loose spiral, chains up to the dome
    shapes = ["rect", "oval", "round", "arch"]
    for k in range(34):
        a = rng.random() * 6.283
        r = 4 + rng.random() * (inner - 7)
        x, z = CX + int(round(r * math.cos(a))), CZ + int(round(r * math.sin(a)))
        w = int(rng.integers(3, 8)); h = int(rng.integers(4, 10))
        yy = y + 4 + int(rng.integers(0, 22))
        axis = "x" if rng.random() < 0.5 else "z"
        ceiling = y + WH + int(math.sqrt(max(R * R - (r + w) ** 2, 0)) * 0.75) - 1
        mirror(bb, x - w // 2 if axis == "x" else x, yy, z - w // 2 if axis == "z" else z, w, h, axis, shapes[k % 4], chain_to=ceiling)
    # Brulee's giant oval mirror on the north side, standing on a cookie plinth
    bb.fill(CX - 8, y + 1, CZ - inner + 2, CX + 8, y + 2, CZ - inner + 4, COOKIE)
    mirror(bb, CX - 6, y + 3, CZ - inner + 3, 13, 17, "x", "oval")
    # Katakuri's mochi: thick white pillars that bulge and fuse, from the floor up into the air
    for (mx, mz, h) in ((CX - 10, CZ + 6, 14), (CX + 11, CZ - 4, 18), (CX + 4, CZ + 12, 10), (CX - 6, CZ - 10, 16)):
        for yy in range(y + 1, y + h + 1):
            rr = 2.2 + 0.9 * math.sin(yy * 0.6 + mx)
            bb.fill_where(mx - 4, yy, mz - 4, mx + 4, yy, mz + 4, lambda X, q, Z: (X - mx) ** 2 + (Z - mz) ** 2 <= rr * rr,
                          "minecraft:white_wool" if (yy % 5) else "minecraft:white_concrete_powder")
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                for dy in range(0, 4):
                    if dx * dx + dz * dz + (dy * 1.4) ** 2 <= 10:
                        bb.set(mx + dx, y + h + dy, mz + dz, "minecraft:white_wool")
    # light: froglights flush in the floor ring and lanterns on the inner ring wall
    for a in range(0, 360, 20):
        t = math.radians(a)
        bb.set(CX + int(round((inner - 2) * math.cos(t))), y, CZ + int(round((inner - 2) * math.sin(t))), "minecraft:pearlescent_froglight[axis=y]")
        bb.set(CX + int(round((inner - 0.4) * math.cos(t))), y + 6, CZ + int(round((inner - 0.4) * math.sin(t))), "minecraft:pearlescent_froglight[axis=y]")


def side_rooms(bb):
    """The ring of rooms between the arena wall and the outer wall: mirror maze, Brulee's dressing room, kitchen,
    pantry, guards' room; Katakuri's snack room on the gallery floor above (y GY+11)."""
    y = GY + 1
    walls = [20, 75, 130, 200, 255, 320]          # radial walls (degrees)
    kinds = ["library", "bedroom", "kitchen", "storeroom", "barracks", "mess"]
    inner, outer = R - 6.5, R - 2
    for a in walls:
        t = math.radians(a)
        for r in np.arange(inner, outer + 0.5, 0.5):
            x, z = CX + int(round(r * math.cos(t))), CZ + int(round(r * math.sin(t)))
            bb.fill(x, y, z, x, y + 8, z, FROST)
    for i, (a0, a1) in enumerate(zip(walls, walls[1:] + [walls[0] + 360])):
        am = math.radians((a0 + a1) / 2)
        rx, rz = CX + int(round((R - 4.5) * math.cos(am))), CZ + int(round((R - 4.5) * math.sin(am)))
        box = (rx - 3, rz - 3, rx + 3, rz + 3)
        if kinds[i] != "library":
            furnish_kit(bb, box, y, 8, kinds[i], wood="cherry", seed=8810 + i, doors=[], accent="pink")
        else:                       # the mirror maze: short mirror wall stubs
            for (dx, dz) in ((-2, -2), (2, 2), (0, -1), (-2, 2), (2, -2)):
                bb.fill(rx + dx, y, rz + dz, rx + dx, y + 3, rz + dz, MIRROR)
    # the gallery floor (y GY+11) carries Katakuri's secret snack room on the north-west
    gy = GY + 11
    for a in range(0, 360, 3):
        t = math.radians(a)
        for r in (R - 6.5, R - 7):
            x, z = CX + int(round(r * math.cos(t))), CZ + int(round(r * math.sin(t)))
            bb.set(x, gy, z, "minecraft:quartz_slab[type=bottom]")
    sx, sz = CX - 16, CZ - 16
    bb.fill(sx - 3, gy, sz - 3, sx + 4, gy + 5, sz + 4, FROST)
    bb.fill(sx - 2, gy, sz - 2, sx + 3, gy + 4, sz + 3, AIR)
    bb.fill(sx - 2, gy - 1, sz - 2, sx + 3, gy - 1, sz + 3, "minecraft:pink_carpet") if False else None
    # Katakuri's big armchair (red velvet) and the donut feast on a low table
    bb.fill(sx - 2, gy, sz - 2, sx, gy, sz - 2, "minecraft:red_wool"); bb.fill(sx - 2, gy + 1, sz - 2, sx, gy + 2, sz - 2, "minecraft:red_wool")
    bb.set(sx - 1, gy, sz - 1, "minecraft:red_carpet") if False else bb.set(sx - 1, gy, sz - 1, "minecraft:red_wool")
    bb.set(sx - 2, gy, sz - 1, "minecraft:spruce_trapdoor[facing=east,half=bottom,open=true]"); bb.set(sx, gy, sz - 1, "minecraft:spruce_trapdoor[facing=west,half=bottom,open=true]")
    bb.fill(sx, gy, sz + 1, sx + 2, gy, sz + 2, "minecraft:dark_oak_slab[type=bottom]")
    for (dx, dz, c) in ((0, 1, "pink"), (1, 2, "brown"), (2, 1, "magenta"), (1, 1, "yellow")):
        bb.set(sx + dx, gy + 1, sz + dz, f"minecraft:{c}_carpet")
    bb.set(sx + 3, gy + 3, sz, "minecraft:lantern[hanging=false]") if False else bb.set(sx + 1, gy + 4, sz, "minecraft:lantern[hanging=true]")
    bb.fill(sx + 3, gy, sz + 3, sx + 3, gy + 2, sz + 3, "minecraft:barrel[facing=up]")
    # a hidden stair up to it from the pantry side (ladder in the wall)
    bb.fill(sx + 4, y, sz + 1, sx + 4, gy, sz + 1, "minecraft:ladder[facing=east]")
    bb.set(sx + 4, gy, sz + 1, AIR); bb.set(sx + 4, gy + 1, sz + 1, AIR); bb.set(sx + 3, gy + 1, sz + 1, AIR)
    # lights in every side room on the outer wall
    for a in range(0, 360, 15):
        t = math.radians(a)
        bb.set(CX + int(round((R - 2.2) * math.cos(t))), y + 3, CZ + int(round((R - 2.2) * math.sin(t))), "minecraft:pearlescent_froglight[axis=y]")


def gardens(bb, rng):
    """Candy gardens round the palace: candy-cane trees, cotton-candy trees, lollipop flowers, a chocolate fountain,
    sugar paths to the portal, frosting lamp posts."""
    # path from the portal to the south shore
    for z in range(CZ + R + 8, N - 14):
        for x in range(CX - 3, CX + 4):
            if land(x, z):
                bb.set(x, hy(x, z), z, "onepiece:cookie_bricks" if (x + z) % 4 else "minecraft:pink_concrete")
        if z % 7 == 0:
            for x in (CX - 5, CX + 5):
                if land(x, z):
                    lamp_post(bb, x, hy(x, z) + 1, z, post="minecraft:white_concrete" if False else "minecraft:quartz_pillar", h=3,
                              light="minecraft:pearlescent_froglight[axis=y]")
    # chocolate fountain on the plaza south of the portal
    fx, fz = CX, CZ + R + 16
    fy = hy(fx, fz)
    bb.cylinder(fx, fy, fz, 6, fy + 1, COOKIE)
    bb.cylinder(fx, fy + 1, fz, 5, fy + 1, "minecraft:brown_terracotta")
    for (rr, yy) in ((3, fy + 4), (2, fy + 7)):
        bb.cylinder(fx, yy - 2, fz, 1, yy - 1, CHOC)
        bb.cylinder(fx, yy, fz, rr, yy, CHOC)
    bb.fill(fx, fy + 8, fz, fx, fy + 9, fz, "minecraft:brown_terracotta")
    # cotton-candy trees (pink/blue wool puffs on striped sticks) and candy-cane trees
    placed = 0
    for _ in range(400):
        if placed >= 46:
            break
        x, z = int(rng.integers(10, N - 10)), int(rng.integers(10, N - 10))
        if not land(x, z) or ring_d(x, z) < R + 7 or abs(x - CX) < 8 and z > CZ + R or _ISLE(np.array(float(x)), np.array(float(z))) < 14:
            continue
        y = hy(x, z)
        h = int(rng.integers(5, 9))
        if placed % 3 == 2:
            bb.fill(x, y + 1, z, x, y + h, z, "onepiece:candy_cane_block")
            bb.fill(x + 1, y + h, z, x + 2, y + h, z, "onepiece:candy_cane_block"); bb.set(x + 2, y + h - 1, z, "onepiece:candy_cane_block")
        else:
            for yy in range(y + 1, y + h):
                bb.set(x, yy, z, "minecraft:white_concrete" if yy % 2 else "minecraft:pink_concrete")
            c = ["minecraft:pink_wool", "minecraft:light_blue_wool", "minecraft:magenta_wool", "minecraft:white_wool"][placed % 4]
            r = 2.6 + rng.random()
            for dx in range(-4, 5):
                for dy in range(-3, 4):
                    for dz in range(-4, 5):
                        if dx * dx + (dy * 1.3) ** 2 + dz * dz <= r * r and rng.random() < 0.9:
                            bb.set(x + dx, y + h + 1 + dy, z + dz, c)
        placed += 1
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 8805, density=0.25,
              kinds=["onepiece:wafer_grass", "onepiece:candy_shrub", "minecraft:short_grass", "onepiece:wafer_grass"],
              flowers=["onepiece:lollipop_flower", "minecraft:pink_tulip", "minecraft:allium"],
              mask=lambda X, Z: land(X, Z) & (ring_d(X, Z) > R + 4), ground=("grass_block", "sugar_sand", "moss_block"))


def design():
    bb = BigBuild(seed=8800, y_min=-14, y_max=96)
    rng = np.random.default_rng(8800)
    terrain(bb)
    top = palace(bb)
    towers(bb)
    arena(bb, rng)
    side_rooms(bb)
    gardens(bb, rng)
    return bb, [], top


def build():
    bb, audit, top = design()
    b = to_canvas(bb)
    steady(b)
    b.npc(CX, GY + 1, CZ + 2, "katakuri", True)
    b.chest(CX - 3, GY + 1, CZ - (R - 8) + 6, "candy", "south")
    b.chest(CX - 15, GY + 11, CZ - 13, "candy", "east")
    b.chest(CX + 3, GY + 1, CZ - (R - 8) + 6, "candy", "south")
    for (x, z) in ((CX - 8, CZ + R + 10), (CX + 8, CZ + R + 10), (CX + 22, CZ + 2), (CX - 22, CZ - 2)):
        b.guard(x, hy(x, z) + 1 if R + 4 < ring_d(x, z) else GY + 1, z, "homie")
    return b, 0
