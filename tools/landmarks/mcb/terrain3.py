"""Shared terrain helpers for the v3 'big feature' redos (2026-10-30): banded rock strata from a heightmap, distance
fields, and a sea that only fills a wobbly round rim (so the build's water blends into the world's ocean, L106)."""
import numpy as np

from mcb import nature as NT

RED_STRATA = ["minecraft:red_terracotta", "minecraft:red_terracotta", "minecraft:orange_terracotta",
              "minecraft:red_terracotta", "minecraft:terracotta", "minecraft:red_terracotta", "minecraft:red_terracotta",
              "minecraft:brown_terracotta", "minecraft:red_terracotta", "minecraft:red_sandstone", "minecraft:red_terracotta",
              "minecraft:granite"]


def grid(n):
    return np.arange(n)[:, None].astype(float), np.arange(n)[None, :].astype(float)


def dist_to(mask, steps=40):
    """Approximate distance (blocks, 8-neighbour) from every cell to the nearest True cell of mask, capped at steps."""
    d = np.where(mask, 0.0, float(steps))
    cur = mask.copy()
    for k in range(1, steps):
        nxt = cur.copy()
        nxt[1:, :] |= cur[:-1, :]; nxt[:-1, :] |= cur[1:, :]
        nxt[:, 1:] |= cur[:, :-1]; nxt[:, :-1] |= cur[:, 1:]
        new = nxt & ~cur
        if not new.any():
            break
        d[new] = k
        cur = nxt
    return d


def strata(bb, H, M, base, seed, blocks=RED_STRATA, band=5, wobble=4.0, x0=0, z0=0, skin=None):
    """Fill columns M from y=base up to H (inclusive) with horizontal rock bands that wave with noise. H, M: arrays
    indexed [x - x0, z - z0]. skin: optional (block, depth) painted on the top `depth` layers instead (snow, grass)."""
    nx, nz = H.shape
    X = np.arange(x0, x0 + nx)[:, None]; Z = np.arange(z0, z0 + nz)[None, :]
    off = NT.fbm(X, Z, seed, 30) * wobble * 2 + NT.noise(X, Z, seed + 7, 7) * 1.5
    top = int(H[M].max()) if M.any() else base
    nb = len(blocks)
    for y in range(base, top + 1):
        col = M & (H >= y)
        if not col.any():
            continue
        idx = (np.floor((y + off) / band).astype(int)) % nb
        if skin:
            sk = col & (H - y < skin[1])
            idx = np.where(sk, -1, idx)
        for k in range(-1 if skin else 0, nb):
            m = col & (idx == k)
            if m.any():
                bb.fill_where(x0, y, z0, x0 + nx - 1, y, z0 + nz - 1, lambda XX, yy, ZZ, m=m: m,
                              skin[0] if k == -1 else blocks[k])


def sea(bb, n, land, cx, cz, r, seed, top=0, deep=-20, shelf=14, extra_deep=None, floor="minecraft:sand",
        keep=None, y_min=-30, x0=0, z0=0):
    """Water from the sea bed up to `top` everywhere inside a wobbly round rim (and not on land). The bed slopes from
    the shore (-2) down to `deep` over `shelf` blocks, and rises back to the world's floor near the rim. extra_deep:
    optional array (deeper bed, e.g. a bay for a whale). keep: optional mask never written. x0, z0: world position of
    the grid's [0, 0] (arrays are indexed [x - x0, z - z0])."""
    X, Z = grid(n)
    X, Z = X + x0, Z + z0
    a = np.arctan2(Z - cz, X - cx)
    rr = np.hypot(X - cx, Z - cz) / (r * (0.94 + 0.06 * np.sin(3 * a + seed % 7) + 0.05 * NT.noise(X, Z, seed, 17)))
    d = dist_to(land, shelf + 2)
    bed = -2 - (deep + 2) * -1 * np.clip(d / shelf, 0, 1)
    bed = np.minimum(bed, -2)
    rim = np.clip((1 - rr) / 0.2, 0, 1)
    bed = np.round(np.maximum(bed, -12 + (bed + 12) * rim)).astype(int)
    if extra_deep is not None:
        bed = np.minimum(bed, extra_deep.astype(int))
    W = (~land) & (rr < 1)
    if keep is not None:
        W &= ~keep
    lo = int(bed[W].min()) if W.any() else -6
    for y in range(max(lo - 2, y_min), top + 1):
        bb.fill_where(x0, y, z0, x0 + n - 1, y, z0 + n - 1, lambda XX, yy, ZZ: W & (bed < yy), "minecraft:water")
        bb.fill_where(x0, y, z0, x0 + n - 1, y, z0 + n - 1, lambda XX, yy, ZZ: W & (bed == yy), floor)
        bb.fill_where(x0, y, z0, x0 + n - 1, y, z0 + n - 1, lambda XX, yy, ZZ: W & (bed > yy) & (bed - 3 <= yy), "minecraft:gravel")
        bb.fill_where(x0, y, z0, x0 + n - 1, y, z0 + n - 1, lambda XX, yy, ZZ: W & (bed - 3 > yy), "minecraft:stone")
    return W, bed, rr


def colossal_tree(bb, x, y, z, h, rng, kind="jungle", r0=4.0, spread=1.0, leaves=None):
    """A prehistoric-size tree: a round trunk r0 thick that tapers, flares at the foot into buttress fins, a few heavy
    branches rising out from the upper half and wide flattened leaf clouds on them and on top. Returns the footprint
    (x1, z1, x2, z2) of the crown."""
    import math
    log = f"minecraft:{kind}_log"
    wood = f"minecraft:{kind}_wood"
    leaves = leaves or [f"minecraft:{kind}_leaves[distance=7,persistent=true,waterlogged=false]"]
    seed = int(x * 73 + z * 31) & 0xFFFF
    for yy in range(y - 3, y + h + 1):
        t = (yy - y) / h
        r = r0 * (1 - 0.4 * max(0.0, t)) + 3.2 * math.exp(-max(0, yy - y) / 3.0)
        R = int(r) + 2
        bb.fill_where(x - R, yy, z - R, x + R, yy, z + R,
                      lambda X, Y, Z, r=r: np.hypot(X - x, Z - z) <= r * (1 + 0.12 * np.sin(np.arctan2(Z - z, X - x) * 5 + seed)),
                      log + "[axis=y]")
    nf = int(rng.integers(4, 7))
    for k in range(nf):                                   # buttress fins
        a = k * 2 * math.pi / nf + rng.uniform(-0.3, 0.3)
        L = r0 + rng.uniform(4, 8)
        for s in np.arange(r0 * 0.6, L, 0.5):
            fh = int((1 - s / L) * (6 + r0))
            fx, fz = round(x + s * math.cos(a)), round(z + s * math.sin(a))
            bb.fill(fx, y - 3, fz, fx, y + fh, fz, wood)
    tips = [(x, y + h + 2, z, (9 + r0) * spread)]
    nb = int(rng.integers(4, 7))
    for k in range(nb):
        a = k * 2 * math.pi / nb + rng.uniform(-0.4, 0.4)
        by = y + h * rng.uniform(0.55, 0.9)
        L = rng.uniform(10, 18) * spread
        rise = rng.uniform(0.35, 0.7)
        rb = max(1.2, r0 * 0.4)
        for s in np.arange(0, L, 0.7):
            t = s / L
            bx, bz = x + (r0 * 0.6 + s) * math.cos(a), z + (r0 * 0.6 + s) * math.sin(a)
            byy = by + s * rise
            rr = rb * (1 - 0.5 * t)
            Rr = int(rr) + 1
            bb.fill_where(int(bx) - Rr, int(byy) - Rr, int(bz) - Rr, int(bx) + Rr, int(byy) + Rr, int(bz) + Rr,
                          lambda X, Y, Z, bx=bx, byy=byy, bz=bz, rr=rr: (X - bx) ** 2 + (Y - byy) ** 2 + (Z - bz) ** 2 <= rr * rr + 0.3,
                          wood)
        tips.append((round(bx), round(byy) + 1, round(bz), rng.uniform(6.5, 9.5) * spread))
    x1, z1, x2, z2 = x, z, x, z
    for k, (tx, ty, tz, r) in enumerate(tips):
        Rr = int(r) + 1
        sd = seed + k * 11

        def f(X, Y, Z, tx=tx, ty=ty, tz=tz, r=r, sd=sd):
            d2 = (X - tx) ** 2 + ((Y - ty) * 2.0) ** 2 + (Z - tz) ** 2
            return (d2 <= r * r) & (NT.noise(X * 2 + Y, Z * 2, sd, 3) > 0.2)
        bb.fill_where(tx - Rr, ty - Rr // 2 - 1, tz - Rr, tx + Rr, ty + Rr // 2 + 1, tz + Rr, f, leaves[k % len(leaves)],
                      only_empty=True)
        x1, z1, x2, z2 = min(x1, tx - Rr), min(z1, tz - Rr), max(x2, tx + Rr), max(z2, tz + Rr)
    return (x1, z1, x2, z2)


def canvas_island_sea(b, cx, cz, coast_r, rim_r, lift=2, rock="minecraft:stone", shore=("minecraft:sand", "minecraft:sand",
                      "minecraft:gravel", "minecraft:stone"), size=None):
    """For an old canvas build whose ground is a flat disc at y 0: cut the disc back to coast_r(angle), give the land
    rock down to the sea bed, a sloping shore, lift everything `lift` up, and fill a round patch of sea (wobbly rim at
    rim_r) round it, so the island stands in the sea instead of on a square of grass."""
    import math
    cols = {}
    for (x, y, z) in b.blocks:
        cols.setdefault((x, z), []).append(y)
    for (x, z), ys in cols.items():
        d = math.hypot(x - cx, z - cz)
        e = coast_r(math.atan2(z - cz, x - cx)) - d
        if e < 0:
            for y in ys:
                if y <= 0:
                    del b.blocks[(x, y, z)]; b.nbt.pop((x, y, z), None)
            up = [y for y in ys if y > 0 and b.blocks.get((x, y, z)) not in (None, "minecraft:air")]
            if up:
                for y in up:
                    del b.blocks[(x, y, z)]; b.nbt.pop((x, y, z), None)
        else:
            for y in range(-16, min(ys)):
                b.set(x, y, z, rock)
            if e < 4 and max(ys) <= 1:
                t = int(-lift + e * 0.6)
                for y in ys:
                    if t < y <= 0:
                        del b.blocks[(x, y, z)]; b.nbt.pop((x, y, z), None)
                b.set(x, t, z, shore[(x * 7 + z * 3) % len(shore)])
                b.set(x, t - 1, z, "minecraft:sandstone")
    b.blocks = {(x, y + lift, z): s for (x, y, z), s in b.blocks.items()}
    b.nbt = {(x, y + lift, z): v for (x, y, z), v in b.nbt.items()}
    b.entities = [(e[0], e[1], e[2] + lift, e[3]) + tuple(e[4:]) for e in b.entities]
    n = size or int(2 * rim_r + 8)
    for x in range(int(cx - rim_r - 4), int(cx + rim_r + 5)):
        for z in range(int(cz - rim_r - 4), int(cz + rim_r + 5)):
            d = math.hypot(x - cx, z - cz)
            a = math.atan2(z - cz, x - cx)
            rim = rim_r * (0.95 + 0.04 * math.sin(3 * a + 2) + 0.02 * math.sin(7 * a))
            if d > rim:
                continue
            e = d - coast_r(a)
            if e < -1:
                continue
            bed = -2 - min(12, max(0, e) * 0.8)
            bed = int(round(max(bed, -12 + (bed + 12) * min(1, (rim - d) / 10))))
            for y in range(bed + 1, 1):
                if (x, y, z) not in b.blocks:
                    b.set(x, y, z, "minecraft:water")
            if (x, bed, z) not in b.blocks:
                b.set(x, bed, z, "minecraft:sand" if (x + z) % 5 else "minecraft:gravel")
                b.set(x, bed - 1, z, "minecraft:stone")
