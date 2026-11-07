"""Shared pieces for the v3 Impel Down levels under the Nether (Blazing Hell, Freezing Hell, Newkama Land, Eternal
Hell; 2026-10-30 audit: the v1 caverns were small rock shells). Everything is BigBuild + numpy masks:

- cavern(): a big noisy domed cave, its rock in clustered noise patches (no stripes), with stalactites
- gallery(): the prison's signature look, tiers of barred cells on four sides round an open hall, a walkway with a
  rail in front of every upper tier, stairs between tiers and furnished cells (kit_interiors "cell")
- shaft(): the sealed lift shaft up to the next level
Canvas y 0 = the cavern floor (world y 33 in the Nether, TILER sky_y=33)."""
import math

import numpy as np

from mcb import nature as NT
from mcb.kit import st
from mcb.kit_interiors import furnish_kit

AIR = "minecraft:air"


def patches(blocks, seed, cell=7):
    """A fill_where painter: picks blocks[i] in smooth noise patches (3D, offset by y so there are no columns)."""
    k = len(blocks)
    def pick(i):
        return lambda X, y, Z: np.minimum((NT.noise(X + y * 2, Z - y, seed, cell) * k).astype(int), k - 1) == i
    return [(pick(i), b) for i, b in enumerate(blocks)]


def cavern(bb, cx, cz, rx, rz, h, rock, seed, floor, thick=4, below=3, drips="minecraft:pointed_dripstone"):
    """Carve a domed cave: air inside a wobbly half-ellipsoid, a rock shell `thick` deep, a floor slab painted in
    `floor` patches. Returns inside(X, y, Z) (numpy mask)."""
    def f(X, y, Z, grow=0.0):
        a = np.arctan2(Z - cz, X - cx)
        wob = 1 + 0.10 * (NT.noise(np.cos(a) * 30 + 50 + y * 0.3, np.sin(a) * 30 + 50, seed, 9) - 0.5) * 2
        return (((X - cx) / (rx + grow)) ** 2 + ((Z - cz) / (rz + grow)) ** 2) / wob ** 2 + (max(0, y) / (h + grow)) ** 2
    x1, x2 = int(cx - rx - thick - 3), int(cx + rx + thick + 3)
    z1, z2 = int(cz - rz - thick - 3), int(cz + rz + thick + 3)
    shell = lambda X, y, Z: (f(X, y, Z, thick) < 1) & (f(X, y, Z) >= 1)
    for test, blk in patches(rock, seed + 1):
        bb.fill_where(x1, 1, z1, x2, int(h + thick + 1), z2, lambda X, y, Z, t=test: shell(X, y, Z) & t(X, y, Z), blk)
        bb.fill_where(x1, -below, z1, x2, -1, z2, lambda X, y, Z, t=test: (f(X, 0, Z, thick) < 1) & t(X, y, Z), blk)
    for test, blk in patches(floor, seed + 2, 5):
        bb.fill_where(x1, 0, z1, x2, 0, z2, lambda X, y, Z, t=test: (f(X, 0, Z, thick) < 1) & t(X, y, Z), blk)
    bb.fill_where(x1, 1, z1, x2, int(h + 1), z2, lambda X, y, Z: f(X, y, Z) < 1, AIR)
    # stalactites hanging from the dome: rock cones with a dripstone tip
    rng = np.random.default_rng(seed)
    for _ in range(int(rx * rz / 60)):
        x, z = int(rng.integers(x1 + 8, x2 - 8)), int(rng.integers(z1 + 8, z2 - 8))
        top = None
        for y in range(int(h + 1), 1, -1):
            if f(np.array([[x]]), y, np.array([[z]]))[0, 0] < 1:
                top = y
                break
        if top is None or top < h * 0.45:
            continue
        L = int(rng.integers(3, 9))
        blk = rock[int(rng.integers(0, len(rock)))]
        for i in range(L):
            r = max(0.0, 1.8 * (1 - i / L))
            ri = int(r) + 1
            bb.fill_where(x - ri, top - i, z - ri, x + ri, top - i, z + ri,
                          lambda X, y, Z, r=r: (X - x) ** 2 + (Z - z) ** 2 <= r * r + 0.3, blk)
        if drips:
            bb.set(x, top - L, z, drips + "[thickness=tip,vertical_direction=down,waterlogged=false]")
    return lambda X, y, Z: f(X, y, Z) < 1


def cell(bb, x1, z1, x2, z2, y, fh, face, wall, bars, wood, seed, kind="cell"):
    """One barred cell (x1..x2, z1..z2 incl. walls) with its bars on `face`, furnished with the kit."""
    bb.fill(x1, y - 1, z1, x2, y + fh - 1, z2, wall)
    bb.fill(x1 + 1, y, z1 + 1, x2 - 1, y + fh - 2, z2 - 1, AIR)
    if face in ("north", "south"):
        z = z1 if face == "north" else z2
        bb.fill(x1 + 1, y, z, x2 - 1, y + fh - 2, z, bars)
    else:
        x = x1 if face == "west" else x2
        bb.fill(x, y, z1 + 1, x, y + fh - 2, z2 - 1, bars)
    furnish_kit(bb, (x1 + 1, z1 + 1, x2 - 1, z2 - 1), y, fh - 1, kind, wood=wood, seed=seed)


def gallery(bb, cx, cz, half, depth, tiers, fh, wall, bars, walk, rail, wood, seed, cw=7, light=None, kinds=("cell",),
            sides=("north", "south", "west", "east"), gaps=()):
    """Tiers of cells on the four sides of a square hall (half = distance from the centre to the cell fronts).
    Each side: a row of cells `cw` wide and `depth` deep, facing the hall; an open walkway 3 wide on every tier above
    the floor, with a rail; stairs at the row's west/north end climbing tier to tier. gaps = [(side, a1, a2)] leaves
    openings (gates) along a side (a = offset along the side from the centre)."""
    n = 0
    for side in sides:
        for t in range(tiers):
            y = 1 + t * fh
            for a in range(-half + 4, half - 4 - cw + 2, cw - 1):
                if any(g[0] == side and g[1] <= a + cw and a <= g[2] for g in gaps):
                    continue
                if side == "north":
                    box = (cx + a, cz - half - depth, cx + a + cw - 1, cz - half)
                    face = "south"
                elif side == "south":
                    box = (cx + a, cz + half, cx + a + cw - 1, cz + half + depth)
                    face = "north"
                elif side == "west":
                    box = (cx - half - depth, cz + a, cx - half, cz + a + cw - 1)
                    face = "east"
                else:
                    box = (cx + half, cz + a, cx + half + depth, cz + a + cw - 1)
                    face = "west"
                cell(bb, *box, y, fh, face, wall, bars, wood, seed + n, kinds[n % len(kinds)])
                n += 1
            # the walkway (3 wide) in front of the tier above the floor, with a rail and hanging lights
            if t > 0:
                lo, hi = -half + 3, half - 3
                if side in ("north", "south"):
                    s = -1 if side == "north" else 1
                    z0 = cz + s * (half - 1)
                    bb.fill(cx + lo, y - 1, min(z0, z0 - s * 2), cx + hi, y - 1, max(z0, z0 - s * 2), walk)
                    zr = z0 - s * 3
                    bb.fill(cx + lo, y, zr, cx + hi, y, zr, rail)
                    for a in range(lo, hi + 1, 8):
                        bb.fill(cx + a, 1 if t == 1 else y - fh, zr, cx + a, y - 2, zr, wall)
                        if light:
                            bb.set(cx + a, y - 2, zr - s, light)
                else:
                    s = -1 if side == "west" else 1
                    x0 = cx + s * (half - 1)
                    bb.fill(min(x0, x0 - s * 2), y - 1, cz + lo, max(x0, x0 - s * 2), y - 1, cz + hi, walk)
                    xr = x0 - s * 3
                    bb.fill(xr, y, cz + lo, xr, y, cz + hi, rail)
                    for a in range(lo, hi + 1, 8):
                        bb.fill(xr, 1 if t == 1 else y - fh, cz + a, xr, y - 2, cz + a, wall)
                        if light:
                            bb.set(xr - s, y - 2, cz + a, light)
        # stairs up the tiers, against the cell fronts at the row's low end
        for t in range(1, tiers):
            y0 = 1 + (t - 1) * fh
            for i in range(fh):
                if side in ("north", "south"):
                    s = -1 if side == "north" else 1
                    x = cx - half + 4 + i
                    z = cz + s * (half - 2)
                    for dz in (0, -s):
                        bb.set(x, y0 + i - 1, z + dz, walk)
                        bb.set(x, y0 + i, z + dz, st(stair_of(walk), "east"))
                        bb.fill(x, y0 + i + 1, z + dz, x, y0 + i + 3, z + dz, AIR)
                else:
                    s = -1 if side == "west" else 1
                    z = cz - half + 4 + i
                    x = cx + s * (half - 2)
                    for dx in (0, -s):
                        bb.set(x + dx, y0 + i - 1, z, walk)
                        bb.set(x + dx, y0 + i, z, st(stair_of(walk), "south"))
                        bb.fill(x + dx, y0 + i + 1, z, x + dx, y0 + i + 3, z, AIR)
    return n


def stair_of(block):
    """The stair block of a full block (polished_blackstone_bricks -> polished_blackstone_brick_stairs ...)."""
    b = block.split("[")[0]
    for a, s in (("_bricks", "_brick_stairs"), ("_tiles", "_tile_stairs"), ("_planks", "_stairs"), ("_slab", "_stairs")):
        if b.endswith(a):
            return b[: -len(a)] + s
    return b + "_stairs"


def shaft(bb, x, z, y2, wall, ladder_face="south"):
    """The sealed lift shaft to the level above: a 7x7 tower to the dome with a ladder and an iron hatch."""
    bb.fill(x - 3, 0, z - 3, x + 3, y2, z + 3, wall)
    bb.fill(x - 2, 1, z - 2, x + 2, y2, z + 2, AIR)
    lz = z - 2 if ladder_face == "south" else z + 2
    bb.fill(x, 1, lz, x, y2, lz, f"minecraft:ladder[facing={ladder_face},waterlogged=false]")
    bb.fill(x - 1, 1, z + 3, x + 1, 3, z + 3, AIR)
    bb.fill(x - 1, y2 - 6, z - 1, x + 1, y2 - 6, z + 1, "minecraft:iron_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]")


def chains(bb, pts, y1, inside):
    """Iron chains from the dome down to y1 at each (x, z)."""
    for (x, z) in pts:
        y = y1
        while y < 120 and inside(np.array([[x]]), y + 1, np.array([[z]]))[0, 0]:
            bb.set(x, y, z, "minecraft:iron_chain[axis=y]")
            y += 1


def ceiling_lights(bb, cx, cz, r, inside, light, step=9, seed=0):
    """Light blocks set into the dome on a loose grid (Nether caves have no sky light)."""
    rng = np.random.default_rng(seed)
    for x in range(cx - r, cx + r + 1, step):
        for z in range(cz - r, cz + r + 1, step):
            xx, zz = x + int(rng.integers(-2, 3)), z + int(rng.integers(-2, 3))
            for y in range(120, 3, -1):
                if inside(np.array([[xx]]), y, np.array([[zz]]))[0, 0]:
                    bb.set(xx, y + 1, zz, light)
                    break


def floor_lights(bb, x1, z1, x2, z2, ys, step=8, level=15):
    """Hidden light blocks on a grid, standing on the floor at each level in `ys` wherever there is open air over a
    solid block, so the finish pass need not hang dozens of chandeliers on long chains from a high cave roof."""
    n = 0
    for y in ys:
        for x in range(x1, x2 + 1, step):
            for z in range(z1 + (step // 2 if (x // step) % 2 else 0), z2 + 1, step):
                here = int(bb.get_region(x, y, z, x, y, z)[0, 0, 0])
                below = int(bb.get_region(x, y - 1, z, x, y - 1, z)[0, 0, 0])
                if here == 1 and below > 1 and "air" not in bb.names[below] and "water" not in bb.names[below] \
                        and "lava" not in bb.names[below]:
                    bb.set(x, y, z, f"minecraft:light[level={level},waterlogged=false]")
                    n += 1
    return n
