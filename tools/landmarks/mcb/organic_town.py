"""Organic town plan (2026-10-30, for the audit's 'grid town' redos): winding streets that wander out from a focus
(plaza, gate, palace stair) plus optional wobbly ring streets, paved, and furnished houses packed onto the land between
them with their doors turned to the nearest street.

    S, placed = organic_town(bb, area, focus, ok, seed, tracker, pal, roofs, pave, n_houses, ...)

ok(x, z) -> True where town may be (land, not reserved). hy(x, z) -> ground y. S is a bool array over area
(indexed [x - x1, z - z1]) marking street cells; placed is pack_houses' lot list."""
import math

import numpy as np

from mcb import nature as NT
from mcb.lotpack import pack_houses


def street_mask(area, focus, seed, spokes=7, rings=(), width=2.4, wander=0.22, base=0.0, arc=None):
    x1, z1, x2, z2 = area
    nx, nz = x2 - x1 + 1, z2 - z1 + 1
    S = np.zeros((nx, nz), bool)
    rng = np.random.default_rng(seed)
    fx, fz = focus

    def mark(x, z, w):
        ix, iz = int(round(x - x1)), int(round(z - z1))
        r = int(math.ceil(w))
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if dx * dx + dz * dz <= w * w and 0 <= ix + dx < nx and 0 <= iz + dz < nz:
                    S[ix + dx, iz + dz] = True
    lo, hi = arc if arc else (0.0, 2 * math.pi)
    for k in range(spokes):
        a = base + lo + (hi - lo) * (k + 0.5) / spokes + rng.uniform(-0.15, 0.15)
        x, z = float(fx), float(fz)
        da = 0.0
        for _ in range(400):
            da = da * 0.85 + rng.normal(0, wander)
            a += da * 0.25
            x += math.cos(a); z += math.sin(a)
            if not (x1 <= x <= x2 and z1 <= z <= z2):
                break
            mark(x, z, width)
    for (r, w) in rings:
        for t in np.linspace(0, 2 * math.pi, int(2 * math.pi * r * 1.5)):
            if arc and not (lo <= (t - base) % (2 * math.pi) <= hi):
                continue
            rr = r * (1 + 0.06 * math.sin(3 * t + seed % 5) + 0.04 * math.sin(7 * t))
            mark(fx + rr * math.cos(t), fz + rr * math.sin(t), w)
    return S


def organic_town(bb, area, focus, ok, seed, tracker, pal, roofs, pave, n_houses, hy=lambda x, z: 0, spokes=7, rings=(),
                 width=2.4, sizes=(7, 10), floors=(1, 3), kinds=("kitchen", "bedroom", "dining", "storeroom"),
                 plinth="minecraft:cobblestone", fh=5, timber=True, reserved=(), arc=None, base=0.0, max_step=3):
    x1, z1, x2, z2 = area
    S = street_mask(area, focus, seed, spokes, rings, width, arc=arc, base=base)
    X = np.arange(x1, x2 + 1)[:, None]; Z = np.arange(z1, z2 + 1)[None, :]
    okm = np.vectorize(lambda a, b: bool(ok(int(a), int(b))))(X + 0 * Z, Z + 0 * X)
    S &= okm
    # pave the streets (noise mix of the pave blocks), on the ground at hy
    n = NT.noise(X + 0 * Z, Z + 0 * X, seed, 3)
    for (i, j) in zip(*np.nonzero(S)):
        x, z = x1 + int(i), z1 + int(j)
        k = min(len(pave) - 1, int(n[i, j] * len(pave)))
        bb.set(x, hy(x, z), z, pave[k])
    near = np.zeros_like(S)
    near[1:, :] |= S[:-1, :]; near[:-1, :] |= S[1:, :]; near[:, 1:] |= S[:, :-1]; near[:, :-1] |= S[:, 1:]
    free = okm & ~S & ~near

    def face(cx, cz):
        best, rot = 99, 0
        for (dx, dz, r) in ((0, 1, 0), (0, -1, 2), (1, 0, 3), (-1, 0, 1)):  # place_house: rot 1 = door west, 3 = door east
            for s in range(1, 14):
                i, j = int(cx + dx * s) - x1, int(cz + dz * s) - z1
                if 0 <= i < S.shape[0] and 0 <= j < S.shape[1] and S[i, j]:
                    if s < best:
                        best, rot = s, r
                    break
        return rot
    okf = lambda x, z: 0 <= x - x1 < S.shape[0] and 0 <= z - z1 < S.shape[1] and bool(free[x - x1, z - z1])
    placed = pack_houses(bb, hy, okf, area, n_houses, seed, tracker, pal, roofs, focus=focus, reserved=reserved,
                         sizes=sizes, floors=floors, kinds=kinds, gap=2, max_step=max_step, plinth=plinth, fh=fh,
                         face=face, timber=timber)
    return S, placed
