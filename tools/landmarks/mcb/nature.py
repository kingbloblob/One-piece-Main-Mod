"""Natural ground for the v2 designs (ryan's batch 4 feedback, team memory build-feedback-batch4):
  * no build sits on a square plate: the site's land follows an irregular outline and its relief fades out to y 0
    (or to a beach just under it) before the site edge, so pipeline.soften_edges can blend it into the world;
  * ground cover is never a modulo pattern: grass with clustered patches (moss, podzol, coarse dirt, rooted dirt,
    gravel ...) from smooth value noise, plants in drifts and one-kind clumps.

All functions paint into a mcbig.BigBuild and are numpy-vectorised (fill_where / heightfield), so 200 x 200 sites
stay fast. Coordinates: x east+, z south+, y 0 = the site's ground level."""
import math

import numpy as np

AIR = "minecraft:air"


def _hash(i, j, seed):
    n = (i * 73856093) ^ (j * 19349663) ^ (seed * 83492791)
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return (n & 0xFFFF) / 65535.0


def noise(X, Z, seed, cell=11):
    """Smooth value noise in 0..1 for int arrays X (n,1) and Z (1,m) (or scalars)."""
    X = np.asarray(X, dtype=np.int64)
    Z = np.asarray(Z, dtype=np.int64)
    fx, fz = X / cell, Z / cell
    i, j = np.floor(fx).astype(np.int64), np.floor(fz).astype(np.int64)
    tx, tz = fx - i, fz - j
    tx, tz = tx * tx * (3 - 2 * tx), tz * tz * (3 - 2 * tz)
    a, b = _hash(i, j, seed), _hash(i + 1, j, seed)
    c, d = _hash(i, j + 1, seed), _hash(i + 1, j + 1, seed)
    top = a + (b - a) * tx
    bot = c + (d - c) * tx
    return top + (bot - top) * tz


def fbm(X, Z, seed, cell=24, octaves=3):
    """Layered noise 0..1 (big shapes plus smaller wobble)."""
    v, amp, tot = 0.0, 1.0, 0.0
    for k in range(octaves):
        v = v + amp * noise(X, Z, seed + 31 * k, max(2, int(cell / 2 ** k)))
        tot += amp
        amp *= 0.5
    return v / tot


def outline(cx, cz, r, seed, wobble=0.12, lobes=((3, 0.06), (5, 0.04), (9, 0.025))):
    """Irregular island outline: returns f(X, Z) -> how far inside the shore (blocks, negative outside)."""
    ph = [(_hash(k, 7, seed) * 6.283) for k in range(len(lobes))]

    def inside(X, Z):
        dx, dz = X - cx, Z - cz
        a = np.arctan2(dz, dx)
        rr = r * (1 + sum(w * np.sin(n * a + p) for (n, w), p in zip(lobes, ph)))
        rr = rr * (1 - wobble / 2 + wobble * noise(X, Z, seed + 5, 13))
        return rr - np.hypot(dx, dz)
    return inside


# ground cover recipes: (block, share) in order; a column picks by smooth noise, so each block forms patches
JUNGLE = [("minecraft:grass_block", 0.58), ("minecraft:moss_block", 0.14), ("minecraft:podzol", 0.12),
          ("minecraft:rooted_dirt", 0.06), ("minecraft:coarse_dirt", 0.06), ("minecraft:mud", 0.04)]
MEADOW = [("minecraft:grass_block", 0.74), ("minecraft:podzol", 0.06), ("minecraft:coarse_dirt", 0.08),
          ("minecraft:moss_block", 0.06), ("minecraft:rooted_dirt", 0.06)]
BADLANDS = [("minecraft:red_sand", 0.42), ("minecraft:terracotta", 0.18), ("minecraft:coarse_dirt", 0.16),
            ("minecraft:grass_block", 0.16), ("minecraft:gravel", 0.08)]
PLANTS_JUNGLE = ["minecraft:fern", "minecraft:short_grass", "minecraft:large_fern", "minecraft:tall_grass",
                 "minecraft:bush", "minecraft:moss_carpet"]
PLANTS_MEADOW = ["minecraft:short_grass", "minecraft:short_grass", "minecraft:tall_grass", "minecraft:fern",
                 "minecraft:bush"]
FLOWERS = ["minecraft:poppy", "minecraft:dandelion", "minecraft:oxeye_daisy", "minecraft:azure_bluet",
           "minecraft:blue_orchid", "minecraft:cornflower"]


def _pick(recipe, v):
    """Index into recipe for noise values v (cumulative shares)."""
    cum = np.cumsum([s for _, s in recipe])
    cum = cum / cum[-1]
    return np.searchsorted(cum, np.clip(v, 0, 0.9999))


def cover(bb, x1, z1, x2, z2, top_y, recipe, seed, mask=None, under="minecraft:dirt", depth=3, core=None, base=-4):
    """Paint ground: columns where mask(X, Z) is True get `recipe` blocks at y = top_y(X, Z) in noise patches, with
    `under` below for `depth` layers. top_y, mask: functions of (X, Z) arrays. The patch noise mixes two scales and
    is stretched by a rank transform, so patches are clusters, never stripes or checkerboards."""
    X = np.arange(x1, x2 + 1)[:, None]
    Z = np.arange(z1, z2 + 1)[None, :]
    H = np.broadcast_to(np.floor(top_y(X, Z)).astype(int), (len(X), Z.shape[1]))
    M = np.ones(H.shape, bool) if mask is None else np.broadcast_to(mask(X, Z), H.shape)
    v = 0.65 * noise(X, Z, seed, 9) + 0.35 * noise(X, Z, seed + 1, 4)
    flat = np.sort(v[M]) if M.any() else np.array([0.5])
    rank = np.searchsorted(flat, v) / max(len(flat), 1)          # uniform 0..1, so shares are what the recipe says
    idx = _pick(recipe, rank)
    for k, (blk, _) in enumerate(recipe):
        m = M & (idx == k)
        if not m.any():
            continue
        for y in np.unique(H[m]):
            bb.fill_where(x1, int(y), z1, x2, int(y), z2, lambda XX, yy, ZZ, m=m, y=y: m & (H == y), blk)
    lo, hi = int(H[M].min()) if M.any() else 0, int(H[M].max()) if M.any() else 0
    for y in range(lo - depth, hi):
        bb.fill_where(x1, y, z1, x2, y, z2, lambda XX, yy, ZZ: M & (H > yy) & (H - depth <= yy), under, only_empty=True)
    if core:                                                        # solid rock inside raised ground
        for y in range(base, hi - depth):
            bb.fill_where(x1, y, z1, x2, y, z2, lambda XX, yy, ZZ: M & (H - depth > yy), core, only_empty=True)
    return H


def plants(bb, x1, z1, x2, z2, top_y, seed, density=0.25, kinds=PLANTS_JUNGLE, flowers=(), mask=None,
           ground=("grass_block", "moss_block", "podzol", "rooted_dirt", "coarse_dirt", "mud")):
    """Plants in drifts: a smooth density field (some patches thick, some bare), each drift one or two kinds, flower
    clumps of one colour. Only on air above natural ground. Two-block plants get their upper half."""
    rng = np.random.default_rng(seed)
    X = np.arange(x1, x2 + 1)[:, None]
    Z = np.arange(z1, z2 + 1)[None, :]
    H = np.broadcast_to(np.floor(top_y(X, Z)).astype(int), (len(X), Z.shape[1]))
    dens = np.clip(1.6 * noise(X, Z, seed, 8) - 0.45, 0, 1) * density
    hit = rng.random(H.shape) < dens
    if mask is not None:
        hit &= np.broadcast_to(mask(X, Z), H.shape)
    kind_n = noise(X, Z, seed + 3, 6)
    flower_n = noise(X, Z, seed + 9, 5)
    tall = ("large_fern", "tall_grass", "rose_bush", "peony", "lilac", "sunflower", "giant_barley", "giant_fern")
    names = bb.names
    for i, j in zip(*np.nonzero(hit)):
        x, z, y = x1 + int(i), z1 + int(j), int(H[i, j])
        below = bb.get_region(x, y, z, x, y + 2, z)[0, :, 0]
        if below[1] not in (0, 1) or not names[below[0]] or names[below[0]].split("[")[0].split(":")[-1] not in ground:
            continue
        if flowers and flower_n[i, j] > 0.78:
            p = flowers[int(noise(x // 9, z // 9, seed + 4, 1) * len(flowers) * 0.999) % len(flowers)]
        else:
            p = kinds[int(kind_n[i, j] * len(kinds) * 0.999)]
        short = p.split(":")[-1]
        if short in tall:
            if below[2] not in (0, 1):
                continue
            bb.set(x, y + 1, z, p + "[half=lower]")
            bb.set(x, y + 2, z, p + "[half=upper]")
        else:
            bb.set(x, y + 1, z, p)


def boulder(bb, x, y, z, r, rng, blocks=("minecraft:stone", "minecraft:andesite", "minecraft:mossy_cobblestone")):
    """A half-sunk lumpy boulder (mixed stone)."""
    r = max(1.2, r)
    R = int(math.ceil(r)) + 1

    def f(X, yy, Z):
        d = ((X - x) ** 2 + ((yy - y) * 1.3) ** 2 + (Z - z) ** 2) ** 0.5
        return d <= r * (0.8 + 0.4 * noise(X * 3 + yy, Z * 3, int(x * 7 + z), 2))
    for k, blk in enumerate(blocks):
        bb.fill_where(x - R, y - R, z - R, x + R, y + R, z + R,
                      lambda X, yy, Z, k=k: f(X, yy, Z) & (noise(X + yy * 5, Z, int(x + z) + k, 2) * len(blocks) // 1 == k),
                      blk)
    bb.fill_where(x - R, y - R, z - R, x + R, y + R, z + R, f, blocks[0], only_empty=True)


def giant_tree(bb, x, y, z, h, rng, kind="jungle", vines=True):
    """A big jungle-style tree: 2x2 trunk, buttress roots, two or three branches with leaf clusters, vines."""
    log = f"minecraft:{kind}_log"
    leaf = f"minecraft:{kind}_leaves[distance=7,persistent=true,waterlogged=false]"
    bb.fill(x, y - 2, z, x + 1, y + h, z + 1, log + "[axis=y]")
    for (dx, dz, ax) in ((-1, 0, "x"), (2, 1, "x"), (1, -1, "z"), (0, 2, "z")):         # buttress roots
        k = int(rng.integers(2, 4))
        bb.fill(x + dx, y - 1, z + dz, x + dx, y + k - 1, z + dz, log + "[axis=y]")
        ox, oz = (dx - (1 if dx < 0 else 0), dz) if ax == "x" else (dx, dz - (1 if dz < 0 else 0))
        ox = x + dx + (-1 if dx < 0 else 1 if dx > 1 else 0)
        oz = z + dz + (-1 if dz < 0 else 1 if dz > 1 else 0)
        bb.set(ox, y, oz, log + f"[axis={ax}]")
    tops = [(x, y + h + 1, z)]
    for k in range(int(rng.integers(2, 4))):
        a = rng.uniform(0, 6.283)
        L = int(rng.integers(3, 6))
        by = y + int(h * rng.uniform(0.55, 0.85))
        for s in range(1, L + 1):
            bx, bz = x + round(math.cos(a) * s), z + round(math.sin(a) * s)
            bb.set(bx, by + s // 2, bz, log + ("[axis=x]" if abs(math.cos(a)) > 0.7 else "[axis=z]" if abs(math.sin(a)) > 0.7 else "[axis=y]"))
        tops.append((x + round(math.cos(a) * L), by + L // 2 + 1, z + round(math.sin(a) * L)))
    for (tx, ty, tz) in tops:
        r = rng.uniform(3.5, 5.5)
        R = int(r) + 1

        def f(X, yy, Z, tx=tx, ty=ty, tz=tz, r=r):
            d2 = (X - tx) ** 2 + ((yy - ty) * 1.8) ** 2 + (Z - tz) ** 2
            return (d2 <= r * r) & (noise(X * 2 + yy, Z * 2, tx * 3 + tz, 2) > 0.18)
        bb.fill_where(tx - R, ty - 3, tz - R, tx + R, ty + 3, tz + R, f, leaf, only_empty=True)
        if vines:
            pass
    if vines:                                                       # vines on the trunk, attached to the bark
        for (vx, vz, side) in ((x - 1, z, "east"), (x + 2, z + 1, "west"), (x + 1, z - 1, "south"), (x, z + 2, "north")):
            if rng.random() < 0.6:
                st = "minecraft:vine[" + ",".join(f"{d}={'true' if d == side else 'false'}" for d in ("east", "north", "south", "up", "west")) + "]"
                y2 = y + h - 1
                y1 = y2 - int(rng.integers(3, max(4, h - 3)))
                for yy in range(max(y1, y + 3), y2 + 1):
                    if bb.get_region(vx, yy, vz, vx, yy, vz)[0, 0, 0] in (0, 1):
                        bb.set(vx, yy, vz, st)
