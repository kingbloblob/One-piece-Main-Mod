"""Sea King Graveyard v2, redesigned with the Minecraft Builder skill: the skeleton of a colossal Sea King on the
sea floor (Sea Kings in the Calm Belt, ep 71/ch 101 and the giant ones round Fish-Man Island, ch 608+: serpents
hundreds of metres long with horned, fanged heads).

Silhouette first: an S-curve spine 150 blocks long that dives into the sand and rises out again, rib pairs arching
up like the vaults of a cathedral (tallest behind the head, shrinking to the tail), a dorsal crest of long spines,
and the great horned skull lying on its side with the jaws gaping wide, rows of fangs, deep eye sockets; bone fins
fanned out on the sand.

Around it: the bed of a sea-floor valley (sand, gravel, rock outcrops), coral grown over the ribs, kelp forests
between them, seagrass meadows, sea pickles glowing in the eye sockets, a school of fish through the ribs, a sunken
treasure inside the skull's mouth. 160 x 112, sea floor y 0; everything inside is flooded. (v2)"""
import math
import sys

import numpy as np

from mcb.kit import BigBuild, P, AIR, steady
from mcb.bridge import to_canvas
from mcb import nature as NT
from mcb.hulls import air_to_water

import mcreef as R

SID = "sea_king_bones"
TITLE = "Sea King Graveyard"
CUTS = [3, 10, 20]
TILER = dict(heightmap="OCEAN_FLOOR_WG", terrain="none")
EDGE_REACH = 2

NX, NZ = 160, 112
_BED = NT.outline(80, 56, 70, 6401, wobble=0.12, lobes=((2, 0.25), (3, 0.06), (5, 0.04)))
BONE = "minecraft:bone_block[axis=y]"
BONEX = "minecraft:bone_block[axis=x]"
BONEZ = "minecraft:bone_block[axis=z]"
SAND = [("minecraft:sand", 0.6), ("minecraft:gravel", 0.15), ("minecraft:sandstone", 0.06), ("minecraft:clay", 0.07),
        ("minecraft:sand", 0.08), ("minecraft:suspicious_gravel", 0.04)]


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    return np.round(NT.fbm(X, Z, 6402, 18) * 5 - 1.5)


def hy(x, z):
    return int(_height(np.array(float(x)), np.array(float(z))))


def onbed(X, Z):
    return _BED(np.asarray(X, float), np.asarray(Z, float)) > 0


def spine(t):
    """Point, heading and the spine's height at t (0 = tail tip, 1 = the neck)."""
    x = 12 + t * 106
    z = 56 + 28 * math.sin(t * math.pi * 1.7 + 0.2)
    dz = 28 * math.pi * 1.7 * math.cos(t * math.pi * 1.7 + 0.2) / 106
    y = 2 + 4 * math.sin(math.pi * t) ** 0.6 + 2 * math.sin(t * 9)     # dips under the sand in places
    return x, z, math.atan2(dz, 1), y


def body(bb):
    n = 420
    for i in range(n + 1):
        t = i / n
        x, z, h, y = spine(t)
        size = 1.6 + 6.5 * math.sin(math.pi * min(1, t * 1.05)) ** 0.7
        r = 1.2 + 1.2 * t
        R_ = int(r) + 1
        xi, zi, yi = int(round(x)), int(round(z)), int(round(y))
        bb.fill_where(xi - R_, yi - R_, zi - R_, xi + R_, yi + R_, zi + R_,
                      lambda X, Y, Z: (X - x) ** 2 + (Y - y) ** 2 + (Z - z) ** 2 <= r * r, BONE)
        if i % 7 == 0:                                            # vertebra discs
            nx, nz = -math.sin(h), math.cos(h)
            for d in range(-int(r + 1.5), int(r + 2)):
                bb.set(int(round(x + nx * d)), yi, int(round(z + nz * d)), "minecraft:bone_block[axis=y]")
        if i % 14 == 0 and 0.07 < t < 0.95:                       # rib pair arching over the body
            nx, nz = -math.sin(h), math.cos(h)
            Rr = size * 2.3
            for a in range(-10, 191, 3):
                ar = math.radians(a)
                px = x + nx * Rr * math.cos(ar) * 1.05
                pz = z + nz * Rr * math.cos(ar) * 1.05
                py = y + Rr * 1.0 * math.sin(ar) - Rr * 0.2
                if py >= hy(px, pz) - 1:
                    bb.set(int(round(px)), int(round(py)), int(round(pz)), BONE)
                    bb.set(int(round(px)), int(round(py)) + 1, int(round(pz)), BONE) if abs(a - 90) > 60 else None
        if i % 10 == 0 and 0.12 < t < 0.9:                        # dorsal crest spines leaning back
            Ls = int(size * 1.8)
            for k in range(Ls):
                bb.set(int(round(x - math.cos(h) * k * 0.4)), yi + int(r) + 1 + k, int(round(z - math.sin(h) * k * 0.4)), BONE)
    # bone fins fanned on the sand
    for t in (0.78, 0.36):
        x, z, h, y = spine(t)
        for side in (-1, 1):
            for k in range(14):
                for s in range(-k // 3, k // 3 + 1):
                    if (k + s) % 3 == 2:
                        continue
                    px = int(round(x - math.cos(h) * k * 0.7 + s))
                    pz = int(round(z + side * (7 + k)))
                    bb.set(px, hy(px, pz) + 1, pz, BONEX if k % 2 else BONEZ)


def skull(bb):
    """Horned skull, jaws gaping, rows of fangs, eye sockets glowing with sea pickles. Returns the mouth centre."""
    x0, z0, h, y0 = spine(1.0)
    ux, uz = math.cos(h), math.sin(h)
    nx, nz = -uz, ux
    LEN = 34
    for k in range(LEN):
        f = k / (LEN - 1)
        cx, cz = x0 + ux * k, z0 + uz * k
        rw = 11 * (1 - 0.5 * f)
        for (yc, ry, th) in ((y0 + 9 + 6 * f, 6.5 * (1 - 0.45 * f), 1.4), (y0 - 1 - 1.5 * f, 2.6 * (1 - 0.3 * f), 1.4)):
            xi, zi = int(round(cx)), int(round(cz))
            bb.fill_where(xi - 2, int(yc - ry) - 1, int(cz - rw) - 2, xi + 2, int(yc + ry) + 1, int(cz + rw) + 2,
                          lambda X, Y, Z, cx=cx, cz=cz, yc=yc, ry=ry, rw=rw, th=th:
                          ((((X - cx) * ux + (Z - cz) * uz) / 1.3) ** 2 + ((Y - yc) / ry) ** 2 + (((X - cx) * nx + (Z - cz) * nz) / rw) ** 2 <= 1)
                          & ((((X - cx) * ux + (Z - cz) * uz) / 1.3) ** 2 + ((Y - yc) / max(ry - th, 0.6)) ** 2
                             + (((X - cx) * nx + (Z - cz) * nz) / max(rw - th, 0.6)) ** 2 > 1), "minecraft:bone_block")
        if k % 2 == 0 and 3 < k < LEN - 1:                         # fangs top and bottom along both jaw edges
            for side in (-1, 1):
                fx, fz = cx + nx * side * (rw - 1.5), cz + nz * side * (rw - 1.5)
                ytop = int(round(y0 + 9 + 6 * f - 6.5 * (1 - 0.45 * f)))
                for d in range(4 if k < 20 else 3):
                    bb.set(int(round(fx)), ytop - d, int(round(fz)),
                           "minecraft:calcite" if d < 2 else "minecraft:pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=true]" if d == 3 or (k >= 20 and d == 2) else "minecraft:pointed_dripstone[thickness=frustum,vertical_direction=down,waterlogged=true]")
                ybot = int(round(y0 - 1 - 1.5 * f + 2.6 * (1 - 0.3 * f)))
                for d in range(3):
                    bb.set(int(round(fx)), ybot + d, int(round(fz)),
                           "minecraft:calcite" if d < 1 else "minecraft:pointed_dripstone[thickness=tip,vertical_direction=up,waterlogged=true]" if d == 2 else "minecraft:pointed_dripstone[thickness=frustum,vertical_direction=up,waterlogged=true]")
    # eye sockets and horns
    for side in (-1, 1):
        ex, ez, ey = x0 + ux * 8 + nx * side * 7, z0 + uz * 8 + nz * side * 7, y0 + 14
        bb.fill_where(int(ex) - 3, int(ey) - 3, int(ez) - 3, int(ex) + 3, int(ey) + 3, int(ez) + 3,
                      lambda X, Y, Z, ex=ex, ey=ey, ez=ez: (X - ex) ** 2 + (Y - ey) ** 2 + (Z - ez) ** 2 <= 5.5, AIR)
        bb.set(int(round(ex)), int(round(ey)) - 3, int(round(ez)), "minecraft:bone_block")     # pickles need a solid floor
        bb.set(int(round(ex)), int(round(ey)) - 2, int(round(ez)), "minecraft:sea_pickle[pickles=4,waterlogged=true]")
        for k in range(20):
            hx = x0 + ux * (6 - k * 0.8) + nx * side * (7 + k * 0.55)
            hz = z0 + uz * (6 - k * 0.8) + nz * side * (7 + k * 0.55)
            hyy = y0 + 15 + k * 0.5 - (k / 19) ** 2 * 3
            rr = 1.6 - k * 0.06
            bb.fill_where(int(hx) - 2, int(hyy) - 2, int(hz) - 2, int(hx) + 2, int(hyy) + 2, int(hz) + 2,
                          lambda X, Y, Z, hx=hx, hyy=hyy, hz=hz, rr=rr: (X - hx) ** 2 + (Y - hyy) ** 2 + (Z - hz) ** 2 <= rr * rr, BONE)
    # nostril holes near the snout
    for side in (-1, 1):
        sx, sz = x0 + ux * (LEN - 4) + nx * side * 2, z0 + uz * (LEN - 4) + nz * side * 2
        bb.fill(int(sx), int(y0 + 13), int(sz), int(sx), int(y0 + 15), int(sz), AIR)
    return (x0 + ux * 14, z0 + uz * 14, y0)


def floor(bb):
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, _height, SAND, 6403, mask=onbed, under="minecraft:sand", core="minecraft:sandstone", base=-6)
    rng = np.random.default_rng(6404)
    for _ in range(16):
        x, z = int(rng.integers(6, NX - 6)), int(rng.integers(6, NZ - 6))
        if _BED(np.array(float(x)), np.array(float(z))) > 8:
            NT.boulder(bb, x, hy(x, z), z, rng.uniform(2, 4.5), rng,
                       blocks=("minecraft:stone", "minecraft:andesite", "minecraft:tuff", "minecraft:mossy_cobblestone"))


def life(bb, mouth):
    rng = np.random.default_rng(6405)
    corals = ["minecraft:tube_coral_block", "minecraft:brain_coral_block", "minecraft:fire_coral_block", "minecraft:horn_coral_block",
              "minecraft:bubble_coral_block", "minecraft:dead_horn_coral_block"]
    fans = ["minecraft:tube_coral", "minecraft:brain_coral", "minecraft:fire_coral", "minecraft:horn_coral", "minecraft:bubble_coral",
            "minecraft:sea_pickle[pickles=3,waterlogged=true]", "minecraft:seagrass"]
    bid = [i for i, n in enumerate(bb.names) if n.startswith("minecraft:bone_block")]
    reg = bb.get_region(0, -6, 0, NX - 1, 50, NZ - 1)
    isb = np.isin(reg[:, :-1, :], bid) & (reg[:, 1:, :] <= 1)
    for (i, j, k) in zip(*np.nonzero(isb)):
        if rng.random() < 0.12:
            x, y, z = int(i), -6 + int(j), int(k)
            if rng.random() < 0.4:
                bb.set(x, y, z, corals[int(rng.integers(0, len(corals)))])
            bb.set(x, y + 1, z, fans[int(rng.integers(0, len(fans)))])
    for _ in range(700):
        x, z = int(rng.integers(1, NX - 1)), int(rng.integers(1, NZ - 1))
        if not onbed(np.array(float(x)), np.array(float(z))):
            continue
        y = hy(x, z) + 1
        if bb.get_region(x, y, z, x, y, z)[0, 0, 0] > 1:
            continue
        v = NT.noise(np.array(float(x)), np.array(float(z)), 6406, 12)
        if v > 0.78 and _BED(np.array(float(x)), np.array(float(z))) < 22:
            h = int(rng.integers(5, 20))
            if bb.get_region(x, y, z, x, y + h, z).max() > 1:
                continue
            bb.fill(x, y, z, x, y + h - 1, z, "minecraft:kelp_plant")
            bb.set(x, y + h, z, "minecraft:kelp")
        elif v > 0.3:
            bb.set(x, y, z, "minecraft:seagrass" if rng.random() < 0.8 else "minecraft:tall_seagrass[half=lower]")
        elif rng.random() < 0.15:
            bb.set(x, y, z, fans[int(rng.integers(0, len(fans)))])
    # a school of fish weaving through the ribs
    path = []
    for k in range(18):
        x, z, h, y = spine(0.2 + k * 0.035)
        path.append((int(x), int(y + 8 + 2 * math.sin(k)), int(z)))
    R.fish_school(bb, path, 26, rng=rng)
    # the treasure in the mouth
    mx, mz, my = mouth
    for (dx, dz) in ((0, 0), (1, 1), (-1, 1), (1, -1), (2, 0), (-2, -1)):
        x, z = int(round(mx)) + dx, int(round(mz)) + dz
        bb.set(x, hy(x, z) + 1, z, "minecraft:gold_block" if (dx + dz) % 2 == 0 else "minecraft:raw_gold_block")
    bb.set(int(round(mx)), hy(int(mx), int(mz)) + 2, int(round(mz)), "minecraft:light_weighted_pressure_plate")


def design():
    bb = BigBuild(seed=6400, y_min=-10, y_max=60)
    floor(bb)
    body(bb)
    mouth = skull(bb)
    life(bb, mouth)
    air_to_water(bb, top=12)
    return bb, [], mouth


def build():
    bb, audit, mouth = design()
    b = to_canvas(bb)
    steady(b)
    mx, mz = int(round(mouth[0])), int(round(mouth[1]))
    b.chest(mx + 3, hy(mx + 3, mz) + 1, mz, "easy", "south")
    b.chest(mx - 2, hy(mx - 2, mz + 2) + 1, mz + 2, "easy", "north")
    return b, 0
