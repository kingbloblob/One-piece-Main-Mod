"""Shared pieces for the v3 floating-island builds in the End (Pangaea Castle, the Celestial Dragon mansion, the
Void Century ruins; 2026-10-30 audit: the v1 islands were flat plates with a box on top). BigBuild + numpy masks:

- floating_island(): a wobbly island outline, a lawn top at y 0 with worn edges, and an underside that hangs in a
  noisy cone of banded rock (red Red Line strata or end stone), with drip spikes and roots poking out
- balustrade(): a white rail along the island's rim so the garden edge reads as built, not cut
- hedge(), rose_bed(), topiary(): garden pieces
Canvas y 0 = the island top (world y 62 in the End, TILER sky_y=62)."""
import math

import numpy as np

from mcb import nature as NT

AIR = "minecraft:air"
RED_LINE = ("minecraft:red_terracotta", "minecraft:red_terracotta", "minecraft:orange_terracotta", "minecraft:terracotta",
            "minecraft:red_terracotta", "minecraft:brown_terracotta")
END_ROCK = ("minecraft:end_stone", "minecraft:end_stone", "minecraft:stone", "minecraft:andesite", "minecraft:end_stone",
            "minecraft:tuff")
LAWN = [("minecraft:grass_block", 0.82), ("minecraft:moss_block", 0.06), ("minecraft:rooted_dirt", 0.05),
        ("minecraft:coarse_dirt", 0.04), ("minecraft:podzol", 0.03)]


def floating_island(bb, cx, cz, r, seed, depth=40, strata=RED_LINE, lawn=LAWN, wobble=0.16, broken=None):
    """The island: shp(X, Z) > 0 inside the rim. Top y 0 (lawn + 3 dirt), then rock in bands of `strata` (one band
    per 3 blocks, the band edges wavy) down a cone whose depth is `depth` at the middle and ~4 at the rim, its
    bottom ragged by noise. broken = f(X, Z) mask of pieces bitten out of the island (for ruins). Returns shp."""
    shp0 = NT.outline(cx, cz, r, seed, wobble=wobble)
    shp = shp0 if broken is None else (lambda X, Z: np.where(broken(X, Z), -1.0, shp0(X, Z)))
    x1, x2, z1, z2 = int(cx - r * 1.3), int(cx + r * 1.3), int(cz - r * 1.3), int(cz + r * 1.3)

    def bottom(X, Z):          # how deep the island hangs under (X, Z), negative y
        s = np.clip(shp(X, Z) / r, 0, 1)
        n = NT.fbm(X, Z, seed + 11, 10)
        return -(3 + (depth - 3) * s ** 0.7 * (0.75 + 0.5 * n))
    NT.cover(bb, x1, z1, x2, z2, lambda X, Z: np.zeros(np.broadcast(X, Z).shape), lawn, seed + 1,
             mask=lambda X, Z: shp(X, Z) > 0, depth=3)
    k = len(strata)
    GX = np.arange(x1, x2 + 1)[:, None]
    GZ = np.arange(z1, z2 + 1)[None, :]
    IN = shp(GX, GZ) > 0
    BOT = bottom(GX, GZ)
    WAV = 2 * NT.noise(GX, GZ, seed + 3, 17)
    for y in range(-4, int(BOT.min()) - 1, -1):
        band = ((y + WAV) // 3).astype(int) % k
        for i, blk in enumerate(strata):
            m = IN & (BOT <= y) & (band == i)
            if m.any():
                bb.fill_where(x1, y, z1, x2, y, z2, lambda X, yy, Z, m=m: m, blk)
    # hanging spikes under the cone and roots out of the side
    rng = np.random.default_rng(seed)
    for _ in range(int(r * 0.6)):
        x, z = int(rng.integers(x1, x2)), int(rng.integers(z1, z2))
        s = shp(np.array([[x]]), np.array([[z]]))[0, 0]
        if s < 3:
            continue
        b = int(math.floor(bottom(np.array([[x]]), np.array([[z]]))[0, 0]))
        L = int(rng.integers(3, 10))
        blk = strata[int(rng.integers(0, k))]
        for i in range(L):
            rr = max(0.0, 2.2 * (1 - i / L))
            ri = int(rr) + 1
            bb.fill_where(x - ri, b - i, z - ri, x + ri, b - i, z + ri,
                          lambda X, yy, Z, rr=rr: (X - x) ** 2 + (Z - z) ** 2 <= rr * rr + 0.3, blk)
    for _ in range(int(r * 0.4)):
        a = rng.uniform(0, 2 * math.pi)
        for d in range(int(r * 1.2), 0, -1):
            x, z = round(cx + d * math.cos(a)), round(cz + d * math.sin(a))
            if shp(np.array([[x]]), np.array([[z]]))[0, 0] > 0:
                break
        y = -int(rng.integers(2, 6))
        for i in range(int(rng.integers(2, 6))):
            bb.set(x + round(i * math.cos(a) * 0.6), y - i, z + round(i * math.sin(a) * 0.6), "minecraft:hanging_roots"
                   if i else "minecraft:rooted_dirt")
    return shp


def balustrade(bb, shp, x1, z1, x2, z2, rail="minecraft:quartz_slab[type=bottom,waterlogged=false]",
               post="minecraft:quartz_pillar[axis=y]", step=6, skip=None):
    """A rail on the rim: on every top block whose neighbour is off the island, a slab; a pillar post every `step`.
    skip(X, Z) -> True leaves a gap (stairs, gates)."""
    X = np.arange(x1, x2 + 1)[:, None]
    Z = np.arange(z1, z2 + 1)[None, :]
    s = shp(X, Z)
    rim = (s > 0) & (s <= 1.6)
    if skip is not None:
        rim &= ~np.broadcast_to(skip(X, Z), rim.shape)
    for i, j in zip(*np.nonzero(rim)):
        x, z = x1 + int(i), z1 + int(j)
        if int(bb.get_region(x, 1, z, x, 1, z)[0, 0, 0]) > 1:
            continue
        if (x * 7 + z * 13) % step == 0:
            bb.set(x, 1, z, post)
            bb.set(x, 2, z, "minecraft:quartz_slab[type=bottom,waterlogged=false]")
        else:
            bb.set(x, 1, z, rail)


def hedge(bb, x1, z1, x2, z2, h=2, leaf="minecraft:azalea_leaves[persistent=true,waterlogged=false]"):
    bb.fill(x1, 1, z1, x2, h, z2, leaf)


def rose_bed(bb, x1, z1, x2, z2, seed, flowers=("minecraft:rose_bush", "minecraft:peony", "minecraft:lilac")):
    """A raised bed of tall flowers in a quartz curb."""
    bb.fill(x1, 0, z1, x2, 0, z2, "minecraft:quartz_bricks")
    bb.fill(x1 + 1, 0, z1 + 1, x2 - 1, 0, z2 - 1, "minecraft:grass_block")
    rng = np.random.default_rng(seed)
    f = flowers[int(rng.integers(0, len(flowers)))]
    for x in range(x1 + 1, x2):
        for z in range(z1 + 1, z2):
            bb.set(x, 1, z, f + "[half=lower]")
            bb.set(x, 2, z, f + "[half=upper]")


def topiary(bb, x, z, h=4, leaf="minecraft:azalea_leaves[persistent=true,waterlogged=false]"):
    """A clipped cone tree in a quartz pot."""
    bb.set(x, 1, z, "minecraft:quartz_bricks")
    for y in range(2, 2 + h):
        r = max(0, (h - (y - 2)) // 2)
        bb.fill(x - r, y, z - r, x + r, y, z + r, leaf)
    bb.set(x, 2 + h, z, leaf)
