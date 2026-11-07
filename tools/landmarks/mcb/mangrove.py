"""The giant Yarukiman mangrove of Sabaody, shared by sabaody_park, shakky_bar and auction_house.

The 2026-10-30 audit found the old trees read as grey mushrooms: a smooth round trunk under one big leaf cap. The
show's trees are tall, lumpy-barked trunks that stand on a tent of huge arching prop roots (you can walk under the
trunk between them), with a broken, clumpy crown high above and soap bubbles welling up from the roots. So:
  * the trunk ends at a root junction about a third of the way up; below it only the prop roots touch the ground,
    each arching out and down to a foot 2-3 trunk radii away, with a few forked side roots and hanging tendrils;
  * bark is fluted and lumpy (radius noise + ridges), log mixed with wood knots and a few darker stripped patches;
  * the crown is 6-9 boughs, each ending in a flattened leaf pad filled ~60 %, plus a smaller top pad: a broken
    canopy, not a cap;
  * bubbles rise in short columns from the root feet, bubble lichen and bubble blooms grow round them."""
import math

import numpy as np

from mcb import nature as NT

YLOG = "onepiece:yarukiman_log[axis=y]"
YWOOD = "onepiece:yarukiman_wood"
YSTRIP = "onepiece:stripped_yarukiman_wood"
YLEAF = "onepiece:yarukiman_leaves[distance=7,persistent=true,waterlogged=false]"
BUB = "onepiece:bubble_glass"
ROOTS = "minecraft:mangrove_roots[waterlogged=false]"


def _get(bb, x, y, z):
    """Block name at a cell, or None for empty / outside the build's height range."""
    if not (bb.y_min <= y <= bb.y_max):
        return None
    v = int(bb.get_region(x, y, z, x, y, z)[0, 0, 0])
    return None if v == 0 else bb.names[v]


def _blob(bb, cx, cy, cz, rr, block, only_empty=False, squash=1.2):
    """A round lump of radius rr at a float centre (roots and boughs are chains of these)."""
    R = int(math.ceil(rr)) + 1
    bb.fill_where(int(cx) - R, int(round(cy)) - R, int(cz) - R, int(cx) + R, int(round(cy)) + R, int(cz) + R,
                  lambda X, Y, Z: (X - cx) ** 2 + (Z - cz) ** 2 + ((Y - cy) * squash) ** 2 <= rr * rr, block,
                  only_empty=only_empty)


def yarukiman(bb, x, yb, z, r, h, rng, number=None, bubbles=True, roots=12, skip=None):
    """A Yarukiman mangrove with its root feet on ground level yb. r = trunk radius, h = height to the crown.
    rng: numpy Generator. skip = (deg1, deg2): no roots in that direction (0 = east, 90 = south), e.g. where a
    building stands at the tree's foot. Returns the footprint box (x1, z1, x2, z2) the roots and bubbles take."""
    seed = int(x * 31 + z * 17 + h) & 0xFFFF
    J = yb + max(7, int(h * 0.32))             # root junction: the trunk's underside
    top = yb + h
    spread = r * 2.6 + 4                        # how far out the root feet land
    # --- prop roots: out and slightly up from the trunk, then arching down into the ground
    feet = []
    for k in range(roots):
        a = k * 2 * math.pi / roots + rng.uniform(-0.18, 0.18)
        if skip and skip[0] <= math.degrees(a) % 360 <= skip[1]:
            continue
        D = spread * rng.uniform(0.8, 1.15)
        y0 = J + rng.uniform(-1.5, 2.5)
        th = 1.9 + 0.25 * r / 4
        steps = int(D * 2.2) + 8
        for i in range(steps + 1):
            t = i / steps
            d = r * 0.55 + D * (1 - (1 - t) ** 1.7)
            y = y0 + 2.5 * math.sin(t * math.pi) - (y0 - yb + 2) * t ** 2.2
            _blob(bb, x + d * math.cos(a), y, z + d * math.sin(a), th * (1 - 0.45 * t), YWOOD)
        fx, fz = x + (r * 0.55 + D) * math.cos(a), z + (r * 0.55 + D) * math.sin(a)
        feet.append((fx, fz))
        _blob(bb, fx, yb, fz, 1.9, YWOOD)                     # a knotted foot where it grips the ground
        if k % 3 == 1:                                         # a forked side root from the middle of the arch
            a2 = a + rng.choice((-0.45, 0.45))
            ts = 0.45
            sd = r * 0.55 + D * (1 - (1 - ts) ** 1.7)
            sy = y0 + 2.5 * math.sin(ts * math.pi) - (y0 - yb + 2) * ts ** 2.2
            for i in range(14):
                t = i / 13
                d = sd + D * 0.45 * t
                _blob(bb, x + d * math.cos(a2), sy - (sy - yb + 1.5) * t ** 1.5, z + d * math.sin(a2), 1.1, YWOOD)
    # --- the trunk: lumpy, fluted, a little wider where the roots join
    ri = int(math.ceil(r * 1.5)) + 2

    def trunk(X, Y, Z):
        ang = np.arctan2(Z - z, X - x)
        t = (Y - J) / max(1, top - J)
        rad = r * (1 - 0.28 * t) * (1 + 0.10 * np.sin(7 * ang + 0.15 * Y) + 0.07 * np.sin(3 * ang - 0.07 * Y))
        rad = rad + 0.9 * NT.noise(X * 2 + Y, Z * 2, seed, 3) - 0.3
        if Y < J + 4:
            rad = rad + (J + 4 - Y) * 0.35                    # flare into the roots
        return np.hypot(X - x, Z - z) <= rad
    bb.fill_where(x - ri, J - 1, z - ri, x + ri, top, z + ri, trunk, YLOG)
    # bark: wood knots and pale stripped scars in noise patches on the outer skin
    bb.fill_where(x - ri, J - 1, z - ri, x + ri, top, z + ri,
                  lambda X, Y, Z: (NT.noise(X + Y * 2, Z - Y, seed + 1, 3) > 0.74) & (bb.get_region(x - ri, Y, z - ri, x + ri, Y, z + ri)[:, 0, :] > 1)
                  & (np.hypot(X - x, Z - z) > r * 0.6), YWOOD)
    bb.fill_where(x - ri, J + 2, z - ri, x + ri, top - 4, z + ri,
                  lambda X, Y, Z: (NT.noise(X * 3, Z * 3 + Y, seed + 2, 4) > 0.86) & (bb.get_region(x - ri, Y, z - ri, x + ri, Y, z + ri)[:, 0, :] > 1)
                  & (np.hypot(X - x, Z - z) > r * 0.6), YSTRIP)
    # thin hanging root tendrils under the junction (they hang, they do not reach the ground)
    for k in range(int(r * 3)):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(r * 0.4, r * 1.1)
        tx, tz = int(round(x + d * math.cos(a))), int(round(z + d * math.sin(a)))
        ln = int(rng.integers(2, max(3, (J - yb) // 2)))
        for yy in range(J - 2, J - 2 - ln, -1):
            if yy <= yb + 2:
                break
            if _get(bb, tx, yy, tz) not in (None, "minecraft:air"):
                break
            if _get(bb, tx, yy + 1, tz) in (None, "minecraft:air") and yy != J - 2:
                break
            bb.set(tx, yy, tz, ROOTS)
    # --- the crown: boughs out and up, each ending in a flat clumpy pad
    nb = 6 + int(r // 2)
    for k in range(nb):
        a = k * 2 * math.pi / nb + rng.uniform(-0.25, 0.25)
        ys = top - h * rng.uniform(0.08, 0.22)
        L = r * rng.uniform(2.2, 3.2) + 3
        for i in range(int(L * 1.6) + 1):
            t = i / (L * 1.6)
            _blob(bb, x + (r * 0.5 + L * t) * math.cos(a), ys + L * 0.55 * t ** 0.8, z + (r * 0.5 + L * t) * math.sin(a),
                  max(0.8, 1.6 - t), YWOOD)
        cx, cz, cy = x + (r * 0.5 + L) * math.cos(a), z + (r * 0.5 + L) * math.sin(a), ys + L * 0.55 + 2
        R = r * 1.25 + rng.uniform(2.5, 4.5)
        Hh = R / 1.6
        bb.fill_where(int(cx - R - 1), int(cy - Hh - 1), int(cz - R - 1), int(cx + R + 1), int(cy + Hh + 1), int(cz + R + 1),
                      lambda X, Y, Z, cx=cx, cy=cy, cz=cz, R=R, Hh=Hh:
                      (((X - cx) ** 2 + (Z - cz) ** 2) / R ** 2 + ((Y - cy) / Hh) ** 2 + 0.35 * NT.noise(X + Y * 5, Z, seed + k, 2) <= 1.0)
                      & (NT.noise(X * 2 + Y, Z * 2 - Y, seed + 7 + k, 2) < 0.72), YLEAF, only_empty=True)
    R = r * 1.6 + 3
    bb.fill_where(int(x - R - 1), top - 1, int(z - R - 1), int(x + R + 1), top + int(R / 1.5) + 2, int(z + R + 1),
                  lambda X, Y, Z: (((X - x) ** 2 + (Z - z) ** 2) / R ** 2 + ((Y - top - 2) / (R / 1.6)) ** 2
                                   + 0.3 * NT.noise(X + Y * 5, Z, seed + 30, 2) <= 1.0), YLEAF, only_empty=True)
    # --- the grove number: a painted board on the trunk facing south
    if number is not None:
        FONT = {"1": ["010", "110", "010", "010", "111"], "2": ["111", "001", "111", "100", "111"],
                "3": ["111", "001", "111", "001", "111"], "4": ["101", "101", "111", "001", "001"],
                "5": ["111", "100", "111", "001", "111"], "6": ["111", "100", "111", "101", "111"],
                "7": ["111", "001", "010", "010", "010"], "8": ["111", "101", "111", "101", "111"],
                "9": ["111", "101", "111", "001", "111"], "0": ["111", "101", "101", "101", "111"]}
        txt = str(number)
        yc = J + max(6, (top - J) // 3)
        w = len(txt) * 8 - 2
        zf = z
        while _get(bb, x, yc, zf + 1) not in (None, "minecraft:air"):
            zf += 1
        zf += 1
        bx0 = x - w // 2
        bb.fill(bx0 - 2, yc - 12, zf, bx0 + w + 1, yc + 1, zf, "minecraft:dark_oak_planks")
        for ci, ch in enumerate(txt):
            for ry, row in enumerate(FONT.get(ch, FONT["0"])):
                for cxi, bit in enumerate(row):
                    if bit == "1":
                        bb.fill(bx0 + ci * 8 + cxi * 2, yc - 1 - ry * 2 - 1, zf + 1, bx0 + ci * 8 + cxi * 2 + 1, yc - 1 - ry * 2, zf + 1,
                                "minecraft:white_concrete")
    # --- bubbles welling up from the root feet, bubble lichen and blooms round them
    if bubbles:
        for (fx, fz) in feet[::2]:
            a = rng.uniform(0, 2 * math.pi)
            bx, bz = fx + 2.5 * math.cos(a), fz + 2.5 * math.sin(a)
            yy = yb + 3
            for n in range(int(rng.integers(2, 5))):
                br = float(rng.uniform(0.9, 2.0))
                yy += br + rng.uniform(1.5, 4.5)
                bx += rng.uniform(-1, 1)
                bz += rng.uniform(-1, 1)
                if yy > J + 6:
                    break
                R2 = int(br) + 2
                cx_, cy_, cz_ = bx, yy, bz
                reg = bb.get_region(int(cx_) - R2, int(cy_) - R2, int(cz_) - R2, int(cx_) + R2, int(cy_) + R2, int(cz_) + R2)
                if (reg > 1).any():
                    continue
                bb.fill_where(int(cx_) - R2, int(cy_) - R2, int(cz_) - R2, int(cx_) + R2, int(cy_) + R2, int(cz_) + R2,
                              lambda X, Y, Z, cx_=cx_, cy_=cy_, cz_=cz_, br=br:
                              np.abs(np.sqrt((X - cx_) ** 2 + (Y - cy_) ** 2 + (Z - cz_) ** 2) - br) < 0.55, BUB, only_empty=True)
            for j in range(5):
                lx, lz = int(round(fx + rng.uniform(-4, 4))), int(round(fz + rng.uniform(-4, 4)))
                below = _get(bb, lx, yb, lz)
                if _get(bb, lx, yb + 1, lz) in (None, "minecraft:air") and below and "grass" in below:
                    bb.set(lx, yb + 1, lz, "onepiece:sabaody_bubble_bloom" if j % 2 else
                           "onepiece:bubble_lichen[facing=%s,flower_amount=%d]" % (("north", "east", "south", "west")[j % 4], 1 + j % 4))
    E = int(spread + r + 4)
    return (x - E, z - E, x + E, z + E)
