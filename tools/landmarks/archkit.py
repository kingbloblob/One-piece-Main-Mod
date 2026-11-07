"""Architecture kit (BUILDING_GUIDE sections 10, 13, 14, 15): compound plans, multi-rect roofs with real valleys and
curved pitches, dormers, bays, balconies, porches, stair towers, awnings, vigas, parapets, wall recipes per style and
whole houses: house2 (European town house), desert_house (Alabasta), japanese_house (Wano), venetian_house (Water 7).

Conventions: rects are inclusive (x0, z0, x1, z1[, floors_delta]). A house's y is its floor level (the ground block
row); walls start at y + 1, every storey is FH = 4 high (3 rows of room + the beam/floor row). Nothing here assumes the
ground is y 0: when y is None the houses read ground_y() under their footprint, and foundations go down to the ground.
Texture mixing uses a hash of the position (stable when other code changes); layout choices use the rnd passed in."""
import math, random
from canvas import *

FH = 4
DIRV = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
CW = {"north": "east", "east": "south", "south": "west", "west": "north"}
CCW = {v: k for k, v in CW.items()}
GLASS = pane_of("minecraft:glass_pane")
GROUND = {"grass_block", "dirt", "podzol", "sand", "red_sand", "snow_block", "mycelium", "rooted_dirt", "moss_block", "mud",
          "coarse_dirt", "gravel", "clay", "packed_mud", "dirt_path", "stone", "andesite", "tuff"}
PLASTER = ("minecraft:white_terracotta", "minecraft:calcite", "minecraft:diorite", "minecraft:white_terracotta")
AWNING_COLORS = ("red", "orange", "yellow", "lime", "light_blue", "blue", "purple", "magenta", "pink", "cyan", "green")
PASTELS = ("minecraft:white_terracotta", "minecraft:pink_terracotta", "minecraft:yellow_terracotta", "minecraft:orange_terracotta",
           "minecraft:light_blue_terracotta", "minecraft:light_gray_terracotta", "minecraft:lime_terracotta")
DOME_BLOCKS = ("minecraft:smooth_quartz", "minecraft:light_blue_concrete", "minecraft:smooth_quartz", "minecraft:calcite")
SOFT = ("short_grass", "tall_grass", "fern", "dandelion", "poppy", "snow[layers", "trapdoor", "flower_box", "carpet")


# ------------------------------------------------------------------ small tools
def _h(x, y, z, seed=0):
    n = (int(x) * 73856093) ^ (int(y) * 19349663) ^ (int(z) * 83492791) ^ (seed * 2654435761)
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535


def noise(x, y, z, seed=0, cell=3.0):
    """Smooth 3D value noise in 0..1 (plaster patches, moss)."""
    fx, fy, fz = x / cell, y / cell, z / cell
    i, j, k = math.floor(fx), math.floor(fy), math.floor(fz)
    tx, ty, tz = [t * t * (3 - 2 * t) for t in (fx - i, fy - j, fz - k)]
    def L(a, b_, t): return a + (b_ - a) * t
    c = [[[_h(i + a, j + b_, k + c_, seed) for c_ in (0, 1)] for b_ in (0, 1)] for a in (0, 1)]
    return L(L(L(c[0][0][0], c[0][0][1], tz), L(c[0][1][0], c[0][1][1], tz), ty),
             L(L(c[1][0][0], c[1][0][1], tz), L(c[1][1][0], c[1][1][1], tz), ty), tx)


def mix(m, x, y, z, rough=0.0, seed=0):
    """A block from a palette: a string, a callable(x, y, z) or a tuple (main first, then variants). rough 0..1 raises
    the share of variants (used near the ground: rougher and darker low down, guide 3)."""
    if callable(m): return m(x, y, z)
    if isinstance(m, str): return m
    if len(m) == 1 or _h(x, y, z, seed) > 0.42 + 0.4 * rough: return m[0]
    return m[1 + int(_h(z, x, y, seed + 7) * (len(m) - 1)) % (len(m) - 1)]


def _soft(s):
    return s is None or s == AIR or any(k in s for k in SOFT)


def _solid(s):
    return s is not None and s != AIR and not any(k in s for k in ("pane", "door", "trapdoor", "fence", "carpet", "lantern", "water",
                                                                    "flower_box", "wall_lamp", "short_grass", "_wall["))


def _rl(r):
    return [tuple(q) for q in r] if r and isinstance(r[0], (tuple, list)) else [tuple(r)]


def _axis(block, axis):
    n = block.split("[")[0]
    return f"{n}[axis={axis}]" if any(k in n for k in ("_log", "_wood", "_stem", "basalt", "pillar", "bamboo_block", "hay_block")) else block


def _along(side):
    return "x" if side in ("north", "south") else "z"


def _loc(x, z, side):
    """A frame on a wall: P(u, v) -> world (x, z); v points out of the wall (toward side), +u runs toward CW[side]."""
    ox, oz = DIRV[side]; ux, uz = DIRV[CW[side]]
    return lambda u, v: (x + ux * u + ox * v, z + uz * u + oz * v)


def ground_y(b, x, z, lo=-16, hi=64):
    """Highest ground block in the column (grass, dirt, sand, stone...), or 0. Call it before building there."""
    for y in range(hi, lo - 1, -1):
        s = b.blocks.get((x, y, z))
        if s and s.split("[")[0].split(":")[-1] in GROUND: return y
    return 0


def site_y(b, rects, q=0.3):
    """Floor level for a footprint: a low percentile of the ground under it (sinking 1 into a rise looks natural,
    floating never does; foundation() fills what is lower)."""
    hs = sorted(ground_y(b, x, z) for r in _rl(rects) for x in range(r[0], r[2] + 1) for z in range(r[1], r[3] + 1))
    return hs[int(len(hs) * q)] if hs else 0


def foundation(b, rects, y, block="minecraft:cobblestone", depth=8):
    """Carry the base down under the footprint from y - 1 until it meets the ground (at most to y - depth), so no
    house corner hangs over lower ground (guide 9b.3)."""
    for r in _rl(rects):
        for x in range(r[0], r[2] + 1):
            for z in range(r[1], r[3] + 1):
                for yy in range(y - 1, y - depth - 1, -1):
                    if b.get(x, yy, z) not in (None, AIR): break
                    b.set(x, yy, z, block)


def outline(rects, every=4):
    """The outer wall of a union of rects: F (footprint cells), W {wall cell: outward sides} (a re-entrant corner has
    none) and the straight runs, each {side, cells (sorted along the face, corner posts included), posts (indices)}.
    Posts sit at both ends and every <= `every` blocks, spread evenly so panels are 1 to every-1 wide."""
    F = set()
    for r in _rl(rects): F.update((x, z) for x in range(r[0], r[2] + 1) for z in range(r[1], r[3] + 1))
    W = {}
    for (x, z) in F:
        ds = [s for s, (dx, dz) in DIRV.items() if (x + dx, z + dz) not in F]
        if ds or any((x + dx, z + dz) not in F for dx in (-1, 1) for dz in (-1, 1)): W[(x, z)] = ds
    runs = []
    for s in DIRV:
        ns = s in ("north", "south")
        cs = sorted((c for c, ds in W.items() if s in ds), key=lambda c: (c[1], c[0]) if ns else (c[0], c[1]))
        seqs = []
        for c in cs:
            p = seqs[-1][-1] if seqs else None
            if p and ((ns and c[1] == p[1] and c[0] == p[0] + 1) or (not ns and c[0] == p[0] and c[1] == p[1] + 1)): seqs[-1].append(c)
            else: seqs.append([c])
        a = (1, 0) if ns else (0, 1)
        for q in seqs:
            pre, post = (q[0][0] - a[0], q[0][1] - a[1]), (q[-1][0] + a[0], q[-1][1] + a[1])
            if W.get(pre) == []: q.insert(0, pre)
            if W.get(post) == []: q.append(post)
            n = len(q); k = max(1, math.ceil((n - 1) / every))
            runs.append({"side": s, "cells": q, "posts": sorted({round(i * (n - 1) / k) for i in range(k + 1)})})
    return F, W, runs


def panels(run):
    """Cells between consecutive posts of a run."""
    ps, q = run["posts"], run["cells"]
    return [q[a + 1:c] for a, c in zip(ps, ps[1:]) if c - a > 1]


def _postset(runs):
    return {r["cells"][i] for r in runs for i in r["posts"]}


def _ends(cells, side):
    a = (1, 0) if side in ("north", "south") else (0, 1)
    return (cells[0][0] - a[0], cells[0][1] - a[1]), (cells[-1][0] + a[0], cells[-1][1] + a[1])


def _window(b, cells, side, yb, yt, win=GLASS, sill=None, flower=False, trap=None, out=1):
    """Glass in the wall cells rows yb..yt; a sill stair or flower box under it on the outside and open trapdoor
    shutters either side (guide 4). out = how far out the fittings sit (2 when the glass is in a recess)."""
    ox, oz = DIRV[side]
    for (x, z) in cells:
        for yy in range(yb, yt + 1): b.set(x, yy, z, win)
        sx, sz = x + ox * out, z + oz * out
        if out == 1 and _soft(b.get(sx, yb - 1, sz)):
            if flower: b.set(sx, yb - 1, sz, f"onepiece:flower_box[facing={side}]")
            elif sill: b.set(sx, yb - 1, sz, stairs(sill, OPP[side], "top"))
    if trap:
        for (ex, ez) in _ends(cells, side):
            for yy in range(yb, yt + 1):
                tx, tz = ex + ox * (out - 1 if out > 1 else 1), ez + oz * (out - 1 if out > 1 else 1)
                if _soft(b.get(tx, yy, tz)): b.set(tx, yy, tz, trapdoor(trap, side, "bottom", "true"))


def _door(b, x, z, side, y0, wood="spruce", lamp=True, lamp_at=None):
    b.set(x, y0, z, door(f"minecraft:{wood}_door", side, "lower"))
    b.set(x, y0 + 1, z, door(f"minecraft:{wood}_door", side, "upper"))
    if lamp:
        ox, oz = DIRV[side]; a = (1, 0) if side in ("north", "south") else (0, 1)
        lx, lz = lamp_at or (x + a[0], z + a[1])
        if _soft(b.get(lx + ox, y0 + 2, lz + oz)): b.set(lx + ox, y0 + 2, lz + oz, f"onepiece:wall_lamp[facing={side}]")


# ------------------------------------------------------------------ plans (guide 10)
def plan_rects(kind, x0, z0, w, d, rnd=None, front="south", min_d=8):
    """Footprints in the w x d box as [(x0, z0, x1, z1, floors_delta)]: the main block first, then wings one floor
    lower (cross gables, guide 10). kind: plain | L | T | offset | U. Wings reach toward `front` and start at the main
    block's middle line, so their inner gable ends hide under the main ridge. Sizes are odd where possible. min_d: the
    least depth that still gets a wing (7 lets small town plots have one; 8 keeps wings at least 3 deep)."""
    rnd = rnd or random.Random(x0 * 7 + z0)
    tr = front in ("east", "west")
    W, D = (d, w) if tr else (w, d)
    def odd(n, lo):
        n = max(lo, int(round(n)))
        return n if n % 2 else n - 1 if n - 1 >= lo else n + 1
    if kind == "plain" or W < 7 or D < min_d:
        rs = [(0, 0, W - 1, D - 1, 0)]
    elif kind in ("L", "T"):
        dm = odd(D * 0.6, 5); ww = odd(W * (0.45 if kind == "L" else 0.42), 5)
        wx = (0 if rnd.random() < 0.5 else W - ww) if kind == "L" else (W - ww) // 2
        rs = [(0, 0, W - 1, dm - 1, 0), (wx, dm // 2, wx + ww - 1, D - 1, -1)]
    elif kind == "U":
        dm = odd(D * 0.55, 5); ww = odd(W * 0.3, 5)
        rs = [(0, 0, W - 1, dm - 1, 0), (0, dm // 2, ww - 1, D - 1, -1), (W - ww, dm // 2, W - 1, D - 1, -1)]
    else:  # offset: two blocks overlapping by 2 to 4
        wm = odd(W * 0.6, 5); dm = odd(D * 0.72, 5)
        w2 = min(W, odd(W - wm + rnd.randint(2, 4), 5)); d2 = odd(D * 0.66, 5)
        dl = -1 if rnd.random() < 0.6 else 0
        if rnd.random() < 0.5: rs = [(0, 0, wm - 1, dm - 1, 0), (W - w2, D - d2, W - 1, D - 1, dl)]
        else: rs = [(W - wm, 0, W - 1, dm - 1, 0), (0, D - d2, w2 - 1, D - 1, dl)]
    out = []
    for (a, c, e, g, dl) in rs:
        if front == "south": q = (x0 + a, z0 + c, x0 + e, z0 + g)
        elif front == "north": q = (x0 + a, z0 + D - 1 - g, x0 + e, z0 + D - 1 - c)
        elif front == "east": q = (x0 + c, z0 + a, x0 + g, z0 + e)
        else: q = (x0 + D - 1 - g, z0 + a, x0 + D - 1 - c, z0 + e)
        out.append(q + (dl,))
    return out


def _grow(r, sides, k=1):
    x0, z0, x1, z1 = r[:4]
    return (x0 - k * ("west" in sides), z0 - k * ("north" in sides), x1 + k * ("east" in sides), z1 + k * ("south" in sides)) + tuple(r[4:])


def _side_free(r, s, others, gap=1):
    """True when no other rect touches or comes within `gap` of side s of r."""
    x0, z0, x1, z1 = r[:4]
    strip = {"north": (x0, z0 - gap, x1, z0), "south": (x0, z1, x1, z1 + gap), "west": (x0 - gap, z0, x0, z1), "east": (x1, z0, x1 + gap, z1)}[s]
    return not any(o[0] <= strip[2] and o[2] >= strip[0] and o[1] <= strip[3] and o[3] >= strip[1] for o in others)


def _rooms(rects, inset=1):
    """Interior rects of a union, cut so they don't overlap (callers furnish each with interiors.furnish)."""
    out = []
    for r in rects:
        a = [r[0] + inset, r[1] + inset, r[2] - inset, r[3] - inset]
        for o in out:
            if a[0] <= o[2] and a[2] >= o[0] and a[1] <= o[3] and a[3] >= o[1]:
                cand = [(a[0], o[3] + 1, a[2], a[3]), (a[0], a[1], a[2], o[1] - 1), (o[2] + 1, a[1], a[2], a[3]), (a[0], a[1], o[0] - 1, a[3])]
                cand = [c for c in cand if c[0] <= c[2] and c[1] <= c[3]]
                a = list(max(cand, key=lambda c: (c[2] - c[0] + 1) * (c[3] - c[1] + 1))) if cand else [1, 1, 0, 0]
        if a[0] <= a[2] and a[1] <= a[3]: out.append(tuple(a))
    return out


# ------------------------------------------------------------------ roofs (guide 2, 13)
def _incs(kind, n, curve, span):
    """Rise of each roof row in half blocks, from the eave (row 0) to the ridge. 2 = a stair (45 degrees), 1 = a
    slab step (shallow), 4 = a stair on a full block (steep). Curves only read on roofs 9 or more wide."""
    if kind == "hip_low": return [1] * (n + 3)
    if kind in ("mansard", "gambrel"):
        k = max(1, int(round(n * (0.5 if kind == "mansard" else 0.45))))
        return [2] + [4] * k + [1 if kind == "mansard" else 2] * (n + 3)
    inc = [2] * (n + 3)
    if curve in ("flare", "bell") and span >= 9:
        inc[0] = inc[1] = 1
        if curve == "bell":
            for i in range(max(3, int(math.ceil(n * 0.67))), len(inc)): inc[i] = 4
    return inc


def _cum(inc):
    out, t = [], 0
    for v in inc: t += v; out.append(t)
    return lambda d: out[d] if d < len(out) else out[-1] + 2 * (d - len(out) + 1)


def _rect_roof(r, kind, oh, curve, axis):
    """Height field of one rect's roof: {(x, z): (T, active sides, gable-face flag)} with T in half blocks above the
    base. T is the lowest of the slopes rising from each eave (a gable has 2, a hip 4), which gives hips, half-hips,
    saltbox and irimoya shapes from one rule."""
    x0, z0, x1, z1 = r[:4]
    X0, Z0, X1, Z1 = x0 - oh, z0 - oh, x1 + oh, z1 + oh
    along_x = (axis == "x") if axis else (x1 - x0 >= z1 - z0)
    span = (Z1 - Z0 + 1) if along_x else (X1 - X0 + 1)
    n = (span - 1) // 2
    ev = ("north", "south") if along_x else ("west", "east")
    en = ("west", "east") if along_x else ("north", "south")
    P = _cum(_incs(kind, n, curve, span))
    prof = {ev[0]: P, ev[1]: P}
    k = 0
    if kind == "saltbox":  # the long low slope at the back (north / west), the steep short one at the front
        prof[ev[0]] = _cum([1] * (span + 2))
    if kind in ("hip", "mansard", "hip_low", "pyramid"):
        prof[en[0]] = prof[en[1]] = P
    elif kind == "half_hip" and n >= 3:
        pk = P(n); prof[en[0]] = prof[en[1]] = lambda d: max(1, pk - 4 + 2 * d)
    elif kind == "irimoya":
        k = max(1, (n + 1) // 2)
        prof[en[0]] = prof[en[1]] = lambda d: P(d) if d < k else None
    out = {}
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            dist = {"north": z - Z0, "south": Z1 - z, "west": x - X0, "east": X1 - x}
            vals = {s: f(dist[s]) for s, f in prof.items()}
            vals = {s: v for s, v in vals.items() if v is not None}
            t = min(vals.values())
            out[(x, z)] = (t, [s for s, v in vals.items() if v == t], kind == "irimoya" and min(dist[en[0]], dist[en[1]]) == k)
    return out


def roof(b, rects, kind="gable", st="minecraft:spruce_stairs", full="minecraft:spruce_planks", y=0, overhang=1, curve=None, trim=None,
         gable=None, ridge=None, alt=None, axis=None, fh=FH):
    """Roof over a list of rects (main + wings, as plan_rects gives them: a 5th item is a floors delta, so a wing's
    eave is fh lower per floor). kind: gable | hip | half_hip | saltbox | mansard | gambrel | irimoya | hip_low | pyramid,
    or a list, one per rect. Each rect is built as a height field, the higher one wins in every column, and where two
    roofs meet the stairs turn into inner corners: real valleys (guide 13). Cells hidden inside a taller part's walls are
    dropped. Full blocks close every steep step, gable ends (and the irimoya gable face) are filled with `gable` (a block
    or callable(x, y, z); default full) so there are no holes. Eaves overhang by `overhang` with a cornice row under
    them (trim: a stairs id, a trapdoor id, or False). curve 'flare' / 'bell' changes the pitch per row on roofs 9+
    wide. ridge: slab (or full) block for the ridge cap; alt: a second stairs id mixed in, mostly in the lowest rows.
    Returns the top y. The height field is kept on b._roof for dormers and chimneys."""
    rects = _rl(rects)
    kinds = list(kind) if isinstance(kind, (list, tuple)) else [kind] * len(rects)
    axes = list(axis) if isinstance(axis, (list, tuple)) else [axis] * len(rects)
    sl = st.replace("_stairs", "_slab")
    ridge = ridge or sl
    G = gable if callable(gable) else (lambda x, yy, z, g=(gable or full): g)
    bases = [y + (r[4] * fh if len(r) > 4 else 0) for r in rects]
    allT, allY, allown, allinfo = {}, {}, {}, {}

    def mass(c):
        m = None
        for j, r in enumerate(rects):
            if r[0] <= c[0] <= r[2] and r[1] <= c[1] <= r[3]: m = bases[j] if m is None else max(m, bases[j])
        return m
    nb = lambda c: [((c[0] + dx, c[1] + dz), s) for s, (dx, dz) in DIRV.items()]
    # parts with the same eave height merge into one surface (valleys); a lower part is built first as its own layer,
    # so it runs on under the eaves of a taller one instead of being swallowed by it
    for gb in sorted(set(bases)):
        idx = [i for i in range(len(rects)) if bases[i] == gb and kinds[i] not in (None, "flat")]
        T, own, info = {}, {}, {}
        for i in idx:
            for c, (t, act, gf) in _rect_roof(rects[i], kinds[i], overhang, curve, axes[i]).items():
                ta = 2 * bases[i] + t
                if c not in T or ta > T[c]: T[c], own[c], info[c] = ta, i, (act, gf)
        Y = {c: (t - 1) // 2 if t % 2 else t // 2 - 1 for c, t in T.items()}
        for c in list(T):
            m = mass(c)
            if m is not None and m > gb and Y[c] <= m: del T[c], Y[c]
        for c, t in T.items():
            x, z = c; yy = Y[c]; act, gf = info[c]
            hi = [s for n, s in nb(c) if n in T and 0 < T[n] - t <= (4 if own[n] == own[c] else 2)]
            s_ = st
            if alt and (t - 2 * gb <= 2 and _h(x, yy, z, 5) < 0.6 or noise(x, yy, z, 5, 2.5) > 0.82): s_ = alt
            if t % 2: blk = slab(s_.replace("_stairs", "_slab"))
            elif len(hi) == 2 and hi[1] in (CW[hi[0]], CCW[hi[0]]):
                blk = stairs(s_, hi[0], shape="inner_right" if hi[1] == CW[hi[0]] else "inner_left")
            elif len(hi) == 1: blk = stairs(s_, hi[0])
            elif not hi:
                ups = [OPP[s] for s in act]
                if len(ups) == 1: blk = stairs(s_, ups[0])
                elif len(ups) == 2 and ups[1] in (CW[ups[0]], CCW[ups[0]]):
                    blk = stairs(s_, ups[0], shape="outer_right" if ups[1] == CW[ups[0]] else "outer_left")
                else:
                    blk = ridge if "slab" not in ridge else slab(ridge)
                    if yy - 1 > gb: b.fill_if(x, yy - 1, z, full)
            else: blk = full
            b.set(x, yy, z, blk)
        # close the steps: a column is filled down to its lowest neighbour, never into the walls or rooms below
        for c in T:
            x, z = c; yy = Y[c]
            lo = min([Y[n] for n, s in nb(c) if n in Y] + [yy])
            m = mass(c)
            for k in range(lo + 1 if m is None else max(lo + 1, m + 1), yy):
                b.fill_if(x, k, z, G(x, k, z) if info[c][1] else full)
        # gable ends: the wall line of every rect is filled up to the roof
        for i in idx:
            r = rects[i]
            for x in range(r[0], r[2] + 1):
                for z in range(r[1], r[3] + 1):
                    if x not in (r[0], r[2]) and z not in (r[1], r[3]) or (x, z) not in Y: continue
                    if any(j != i and o[0] < x < o[2] and o[1] < z < o[3] for j, o in enumerate(rects)): continue
                    for k in range(bases[i] + 1, Y[(x, z)]): b.fill_if(x, k, z, G(x, k, z))
        # cornice under the eaves, against the wall
        if trim is not False:
            for c in T:
                act = info[c][0]
                if mass(c) is not None or len(act) != 1: continue
                up = OPP[act[0]]; w_ = (c[0] + DIRV[up][0], c[1] + DIRV[up][1])
                yy = Y[c] - 1
                if mass(w_) is None or not _solid(b.get(w_[0], yy, w_[1])) or "glass" in (b.get(w_[0], yy, w_[1]) or ""): continue
                if b.get(c[0], yy, c[1]) not in (None, AIR): continue
                b.set(c[0], yy, c[1], trapdoor(trim, up, "top") if trim and "trapdoor" in trim else stairs(trim or st, up, "top"))
        allT.update(T); allY.update(Y); allown.update(own); allinfo.update(info)
    b._roof = dict(T=allT, Y=allY, own=allown, info=allinfo, bases=bases, rects=rects)
    return max(allY.values()) if allY else y


def roof_ridge(b):
    """Ridge cells of the last roof: [(x, y, z)] where the roof has no higher neighbour."""
    R = getattr(b, "_roof", None)
    if not R: return []
    T, Y = R["T"], R["Y"]
    return [(c[0], Y[c], c[1]) for c in T if all(T.get((c[0] + dx, c[1] + dz), -99) <= T[c] for dx, dz in DIRV.values())]


def surface(b, x, z, y_hi, y_lo):
    """Highest non-air y in the column between y_lo and y_hi (the roof surface), or y_lo."""
    for yy in range(y_hi, y_lo - 1, -1):
        if b.get(x, yy, z) not in (None, AIR): return yy
    return y_lo


def chimney(b, x, z, y0, y1, block="minecraft:bricks", cap="campfire", base=None):
    """A stack from y0 to y1 with a cap: 'campfire' (smoke), 'funnel' (Venetian: a ring of upside-down corbel stairs around a campfire)."""
    for yy in range(y0, y1 + 1): b.set(x, yy, z, base if (base and yy < y0 + 1) else block)
    if cap == "funnel":
        stn = block.replace("bricks", "brick_stairs") if "bricks" in block else "minecraft:brick_stairs"
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == dz == 0: continue
                f = "west" if dx > 0 else "east" if dx < 0 else "north" if dz > 0 else "south"
                b.set(x + dx, y1 + 1, z + dz, stairs(stn, f, "top"))
        b.set(x, y1 + 1, z, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    elif cap == "campfire":
        b.set(x, y1 + 1, z, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")


def snow_ridge(b, layers=2):
    """A snow layer on every full ridge block of the last roof (snow can lie on a full block; on a slab it can't)."""
    for (x, yy, z) in roof_ridge(b):
        if _solid(b.get(x, yy, z)) and "slab" not in b.get(x, yy, z) and "stairs" not in b.get(x, yy, z) and b.get(x, yy + 1, z) in (None, AIR):
            b.set(x, yy + 1, z, f"minecraft:snow[layers={layers}]")


def back_ladder(b, lad, block):
    """Give every ladder cell a solid block behind it (guide 6: nothing hangs on air or glass). A window behind the
    ladder is walled up whole (its panes, and the sill, flower box and shutters outside it); on a jettied storey,
    where the wall stepped out, a column of `block` goes behind the ladder."""
    lx, lz, ya, yb, s = lad
    f = s.split("facing=")[1].split(",")[0].split("]")[0]
    bx, bz = lx - DIRV[f][0], lz - DIRV[f][1]
    ax, az = (1, 0) if f in ("north", "south") else (0, 1)
    for yy in range(ya, yb + 1):
        q = b.get(bx, yy, bz) or AIR
        if "pane" in q or "glass" in q:
            row = [(bx, bz)]
            for sg in (1, -1):
                k = 1
                while any("pane" in (b.get(bx + ax * sg * k, y2, bz + az * sg * k) or "") for y2 in (yy - 1, yy, yy + 1)): row.append((bx + ax * sg * k, bz + az * sg * k)); k += 1
            nb = next((b.get(bx + ax * sg * k, yy, bz + az * sg * k) for k in range(1, 4) for sg in (1, -1)
                       if _solid(b.get(bx + ax * sg * k, yy, bz + az * sg * k)) and "pane" not in b.get(bx + ax * sg * k, yy, bz + az * sg * k)), block)
            ox, oz = bx - lx, bz - lz
            for (cx, cz) in row:
                for y2 in range(yy - 2, yy + 3):
                    if "pane" in (b.get(cx, y2, cz) or "") or "glass" in (b.get(cx, y2, cz) or ""): b.set(cx, y2, cz, nb)
            for (cx, cz) in row + [(row[0][0] - ax, row[0][1] - az)] + [(c[0] + ax, c[1] + az) for c in row]:
                for y2 in range(yy - 2, yy + 3):
                    o = b.get(cx + ox, y2, cz + oz) or ""
                    if "trapdoor" in o or "flower_box" in o or ("stairs" in o and "half=top" in o and y2 < yy): b.set(cx + ox, y2, cz + oz, AIR)
        elif not _solid(q) or any(k in q for k in ("door", "fence", "carpet", "ladder", "slab", "stairs")):
            b.set(bx, yy, bz, block)


def pent(b, rect, y, st, out=2):
    """A skirt roof (Japanese hisashi) round a storey at height y, `out` deep: a slab row outside, stairs at the wall."""
    F, W, runs = outline(_rl(rect))
    sl = st.replace("_stairs", "_slab")
    for (x, z), ds in W.items():
        for s in ds:
            ox, oz = DIRV[s]
            for v in range(1, out + 1):
                b.fill_if(x + ox * v, y, z + oz * v, slab(sl) if v == out else stairs(st, OPP[s]))
        if len(ds) == 2:
            (ax, az), (cx, cz) = DIRV[ds[0]], DIRV[ds[1]]
            for i in range(1, out + 1):
                for j in range(1, out + 1):
                    blk = slab(sl) if max(i, j) == out else stairs(st, OPP[ds[0]], shape="outer_right" if OPP[ds[1]] == CW[OPP[ds[0]]] else "outer_left")
                    b.fill_if(x + ax * i + cx * j, y, z + az * i + cz * j, blk)


# ------------------------------------------------------------------ add-ons (guide 10, 13)
def dormer(b, x, z, side, y, st, full, wall, win=GLASS, frame=None, flower=True):
    """3-wide dormer cut into a roof slope: its front stands on the wall line at (x, z) facing `side`, y = the roof base
    (top of the wall below). A sill course, framed window (2 tall when the roof is high enough), its own gable roof with
    a front overhang running back until it dies into the main slope, cheeks closing the sides."""
    P = _loc(x, z, side); frame = frame or wall; sl = st.replace("_stairs", "_slab")
    S = {}
    for u in range(-2, 3):
        for v in range(-9, 2):
            wx, wz = P(u, v); S[(u, v)] = surface(b, wx, wz, y + 16, y)
    wh = 2 if max(S[(0, v)] for v in range(-9, 0)) >= y + 5 else 1
    yr = y + 1 + wh
    h = {-2: yr, -1: yr + 1, 0: yr + 2, 1: yr + 1, 2: yr}
    face = {-2: CW[side], -1: CW[side], 1: CCW[side], 2: CCW[side]}
    for u in (-1, 0, 1):
        wx, wz = P(u, 0); b.set(wx, y + 1, wz, wall)
    for k in range(1, wh + 1):
        for u in (-1, 1): wx, wz = P(u, 0); b.set(wx, y + 1 + k, wz, frame)
        wx, wz = P(0, 0); b.set(wx, y + 1 + k, wz, win)
    wx, wz = P(0, 0); b.set(wx, yr + 1, wz, wall)
    if flower:
        fx, fz = P(0, 1); b.set(fx, y + 1, fz, f"onepiece:flower_box[facing={side}]")
    for v in range(1, -10, -1):
        for u in range(-2, 3):
            if v <= 0 and S[(u, v)] >= h[u]: continue
            wx, wz = P(u, v)
            b.set(wx, h[u], wz, slab(sl) if u == 0 else stairs(st, face[u]))
            if v <= 0:
                if u == 0:
                    b.set(wx, yr + 1, wz, full)
                    if v < 0:
                        for yy in range(y + 1, yr + 1): b.set(wx, yy, wz, AIR)
                elif abs(u) == 1 and v < 0:
                    for yy in range(max(y + 1, S[(u, v)]), yr + 1): b.set(wx, yy, wz, wall)
                elif abs(u) == 2 and v < 0:
                    for yy in range(S[(u, v)] + 1, h[u]): b.set(wx, yy, wz, full)


def bay(b, x, z, side, y, floors=1, wall="minecraft:white_terracotta", st="minecraft:spruce_stairs", win=GLASS, frame=None, base=None):
    """3-wide, 1-out bay window on the wall at (x, z) facing `side`, from floor level y up `floors` storeys: an apron,
    glazing on three sides, a head beam per storey, stair brackets under it when it starts above the ground (or a
    base course down to the ground), and its own little hip roof (guide 10)."""
    P = _loc(x, z, side); frame = frame or wall; inn = OPP[side]
    gx, gz = P(0, 1)
    grounded = _solid(b.get(gx, y, gz)) or _solid(b.get(gx, y - 1, gz))
    for f in range(floors):
        fy = y + f * FH
        for u in (-1, 0, 1):
            wx, wz = P(u, 1)
            b.set(wx, fy + 1, wz, base if (grounded and f == 0 and base) else wall)
            for k in (2, 3): b.set(wx, fy + k, wz, win)
            b.set(wx, fy + 4, wz, _axis(frame, _along(side)))
        ix, iz = P(0, 0)
        for k in (1, 2, 3): b.set(ix, fy + k, iz, AIR)
    for u in (-1, 0, 1):
        wx, wz = P(u, 1)
        if grounded: b.set(wx, y, wz, base or wall); foundation(b, [(wx, wz, wx, wz)], y, base or wall)
        else: b.set(wx, y, wz, stairs(st, inn, "top"))
    if not grounded:
        wx, wz = P(0, 1); b.fill_if(wx, y - 1, wz, stairs(st, inn, "top"))
    top = y + floors * FH
    for u in range(-2, 3):
        wx, wz = P(u, 2)
        sh = "straight" if abs(u) < 2 else ("outer_right" if (CW[side] if u < 0 else CCW[side]) == CW[inn] else "outer_left")
        b.set(wx, top, wz, stairs(st, inn, shape=sh))
    for u in (-2, 2):
        wx, wz = P(u, 1); b.fill_if(wx, top, wz, stairs(st, CW[side] if u < 0 else CCW[side]))
    for u in (-1, 0, 1):
        wx, wz = P(u, 1)
        sh = "straight" if u == 0 else ("outer_right" if (CW[side] if u < 0 else CCW[side]) == CW[inn] else "outer_left")
        b.set(wx, top + 1, wz, stairs(st, inn, shape=sh))


def balcony(b, x, z, side, y, w=3, out=1, rail=None, wood="spruce", floor=None, door_=True, lamp=True):
    """Balcony on the wall at (x, z) facing `side`, floor at y (an upper floor's level): a plank floor `out` deep on
    upside-down stair brackets against the wall, a rail round it, a door onto it and a lantern hung under it."""
    P = _loc(x, z, side); hw = w // 2; inn = OPP[side]
    floor = floor or f"minecraft:{wood}_planks"; rail = rail or fence(wood); st = f"minecraft:{wood}_stairs"
    for u in range(-hw, hw + 1):
        for v in range(1, out + 1):
            wx, wz = P(u, v); b.set(wx, y, wz, floor)
            b.set(wx, y + 1, wz, rail if (v == out or abs(u) == hw) else AIR)
            b.set(wx, y + 2, wz, AIR) if _soft(b.get(wx, y + 2, wz)) else None
        if (u + hw) % 2 == 0 or out > 1:
            wx, wz = P(u, 1); b.set(wx, y - 1, wz, stairs(st, inn, "top"))
            if out > 1 and abs(u) == hw: b.fill_if(wx, y - 2, wz, stairs(st, inn, "top"))
    if door_:
        dx, dz = P(0, 0); _door(b, dx, dz, side, y + 1, wood, lamp=False)
    if lamp:
        lx, lz = P(0, out)
        if b.get(lx, y - 1, lz) in (None, AIR): b.set(lx, y - 1, lz, lantern(True))


def porch(b, x, z, side, y, w=5, depth=2, wood="spruce", st=None, post=None, floor=None, rail=True):
    """Lean-to porch in front of the wall cell (x, z) facing `side`, floor at y: a plank deck, posts at the outer
    corners, a roof of slabs and stairs (half pitch) rising from the posts to the wall, a lantern under it."""
    P = _loc(x, z, side); hw = w // 2; inn = OPP[side]
    st = st or f"minecraft:{wood}_stairs"; sl = st.replace("_stairs", "_slab")
    post = post or f"minecraft:stripped_{wood}_log[axis=y]" if wood not in ("bamboo",) else fence(wood)
    floor = floor or f"minecraft:{wood}_planks"
    for u in range(-hw, hw + 1):
        for v in range(1, depth + 1):
            wx, wz = P(u, v); b.set(wx, y, wz, floor)
            for yy in range(y + 1, y + 4):
                if _soft(b.get(wx, yy, wz)) and not (abs(u) == hw and v == depth): b.set(wx, yy, wz, AIR)
    for u in (-hw, hw):
        wx, wz = P(u, depth)
        for yy in range(y + 1, y + 4): b.set(wx, yy, wz, post)
        if rail:
            for v in range(1, depth):
                rx, rz = P(u, v); b.set(rx, y + 1, rz, fence(wood))
    for u in range(-hw - 1, hw + 2):
        for v in range(depth + 1, 0, -1):
            r = depth + 1 - v; t = r + 1
            wx, wz = P(u, v)
            yy = y + 4 + (t - 1) // 2 if t % 2 else y + 4 + t // 2 - 1
            if _soft(b.get(wx, yy, wz)): b.set(wx, yy, wz, slab(sl) if t % 2 else stairs(st, inn))
    lx, lz = P(0, depth)
    b.set(lx, y + 3, lz, lantern(True))


def stair_tower(b, x0, z0, y, h, size=5, wall="minecraft:stone_bricks", st="minecraft:spruce_stairs", full="minecraft:spruce_planks",
                frame=None, door_side="south", win=GLASS, kind="hip", step="minecraft:spruce_stairs", floor="minecraft:spruce_planks",
                base="minecraft:cobblestone", open_to=None):
    """Square tower size x size from floor y, walls h high, with corner posts, slit windows climbing with the stair,
    a spiral stair round a newel (size 5) or a ladder (size 3), a door, and a pyramid roof with a finial.
    open_to: [(x, z, y)] wall cells to open 2 high (doorways into the house). Returns the top y."""
    x1, z1 = x0 + size - 1, z0 + size - 1
    frame = frame or wall
    b.box(x0, y, z0, x1, y, z1, base)
    foundation(b, [(x0, z0, x1, z1)], y, base)
    for xx in range(x0, x1 + 1):
        for zz in range(z0, z1 + 1):
            edge = xx in (x0, x1) or zz in (z0, z1)
            corner = xx in (x0, x1) and zz in (z0, z1)
            for yy in range(y + 1, y + h + 1):
                b.set(xx, yy, zz, (frame if corner else base if yy == y + 1 else mix(wall, xx, yy, zz, rough=max(0, 1 - (yy - y) / 8))) if edge else AIR)
    cx, cz = x0 + size // 2, z0 + size // 2
    for k in range(4, h - 1, 4):
        for s, (dx, dz) in DIRV.items():
            b.set(cx + dx * (size // 2), y + k, cz + dz * (size // 2), win)
    if size >= 5:
        ring = [(-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1)]
        for yy in range(y + 1, y + h): b.set(cx, yy, cz, _axis(frame, "y"))
        for k in range(h - 1):
            (a, c), (a2, c2) = ring[k % 8], ring[(k + 1) % 8]
            f = {(1, 0): "east", (-1, 0): "west", (0, 1): "south", (0, -1): "north"}[(a2 - a, c2 - c)]
            b.set(cx + a, y + 1 + k, cz + c, stairs(step, f))
    else:
        lad = OPP[door_side]
        for yy in range(y + 1, y + h): b.set(cx, yy, cz, f"minecraft:ladder[facing={door_side},waterlogged=false]")
    dx, dz = DIRV[door_side]
    _door(b, cx + dx * (size // 2), cz + dz * (size // 2), door_side, y + 1, wood="spruce")
    for (ox, oz, oy) in open_to or ():
        for k in (0, 1): b.set(ox, oy + k, oz, AIR)
    top = roof(b, [(x0, z0, x1, z1)], kind, st, full, y + h, overhang=1)
    b.set(cx, top + 1, cz, fence("spruce")); b.set(cx, top + 2, cz, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
    return top


def awning(b, cells, y, colors=("red", "white"), out=2):
    """Striped cloth awning. cells = (x0, z0, x1, z1, side): a span of wall cells; the cloth leaves the wall at y and
    drops one per block out (wool with carpet on each step, so it reads as a slope), every cell touching the last.
    cells = [(x, z), ...]: a flat cloth across a lane at y, only placed when both ends touch a solid block.
    Returns the cells placed."""
    placed = []
    if isinstance(cells, tuple) and len(cells) == 5 and isinstance(cells[4], str):
        x0, z0, x1, z1, side = cells
        ox, oz = DIRV[side]
        span = [(x, z) for x in range(min(x0, x1), max(x0, x1) + 1) for z in range(min(z0, z1), max(z0, z1) + 1)]
        for i, (x, z) in enumerate(span):
            c = colors[i % len(colors)]
            for v in range(1, out + 1):
                px, pz = x + ox * v, z + oz * v
                b.set(px, y - v + 1, pz, f"minecraft:{c}_wool"); placed.append((px, y - v + 1, pz))
                if v > 1: b.set(px, y - v + 2, pz, f"minecraft:{c}_carpet"); placed.append((px, y - v + 2, pz))
        return placed
    cells = list(cells)
    if len(cells) < 2: return placed
    def held(c, prev):
        return any(_solid(b.get(c[0] + dx, y, c[1] + dz)) for dx, dz in DIRV.values() if (c[0] + dx, c[1] + dz) not in cells) or \
            _solid(b.get(c[0], y + 1, c[1]))
    if not (held(cells[0], None) and held(cells[-1], None)): return placed
    for i, (x, z) in enumerate(cells):
        b.set(x, y, z, f"minecraft:{colors[i % len(colors)]}_wool"); placed.append((x, y, z))
    return placed


def vigas(b, rect, y, every=2, out=1, wood="minecraft:stripped_jungle_log", skip=()):
    """Beam ends (vigas) through the wall at height y, sticking `out` blocks out every `every` cells (guide 14c)."""
    F, W, runs = outline(_rl(rect), every=99)
    for run in runs:
        s = run["side"]; ox, oz = DIRV[s]; ax = "x" if s in ("east", "west") else "z"
        for i, (x, z) in enumerate(run["cells"][1:-1], 1):
            if i % every or (x, z) in skip: continue
            if not _solid(b.get(x, y, z)): continue
            b.set(x, y, z, _axis(wood, ax))
            for k in range(1, out + 1):
                if _soft(b.get(x + ox * k, y, z + oz * k)): b.set(x + ox * k, y, z + oz * k, _axis(wood, ax))


def parapet(b, rect, y, kind="plain", block="minecraft:smooth_sandstone", cap="minecraft:smooth_sandstone_slab",
            wallb="minecraft:sandstone_wall", skip=(), gap=()):
    """Parapet on the rim of a flat roof at deck level y (blocks from y + 1): plain (block + slab coping), stepped (2 high
    in the middle of each side, 1 at the corners), rounded (wall-block posts at the corners) or crenellated (forts only,
    guide 14c). skip: rim cells covered by an upper storey; gap: rim cells left open (a stair arrives there)."""
    F, W, runs = outline(_rl(rect), every=99)
    for (x, z), ds in W.items():
        if (x, z) in skip or (x, z) in gap: continue
        corner = len(ds) >= 2 or ds == []
        if kind == "rounded" and corner:
            b.set(x, y + 1, z, wall(wallb)); b.set(x, y + 2, z, wall(wallb)); continue
        b.set(x, y + 1, z, block)
        tall = False
        if kind == "stepped" and not corner:
            for run in runs:
                if (x, z) in run["cells"]:
                    n = len(run["cells"]); i = run["cells"].index((x, z))
                    tall = n >= 5 and n // 3 <= i <= n - 1 - n // 3
        if kind == "crenellated": tall = (x + z) % 2 == 0
        if tall: b.set(x, y + 2, z, block); b.set(x, y + 3, z, slab(cap))
        elif kind != "crenellated": b.set(x, y + 2, z, slab(cap))


def arcade(b, x, z, side, y, n=6, h=4, col="minecraft:cut_sandstone", capb="minecraft:chiseled_sandstone",
           st="minecraft:smooth_sandstone_stairs", deck="minecraft:smooth_sandstone", depth=2, floor="minecraft:smooth_sandstone"):
    """Arcade along a wall (guide 14c): columns every 4 at `depth` out from the wall cell (x, z), spanning u = -n..n
    (n = 2 + 4k so the middle is an opening), arch heads of upside-down stairs, a deck on top tied into the wall."""
    P = _loc(x, z, side)
    cols = [u for u in range(-n, n + 1) if (u + n) % 4 == 0]
    for u in range(-n, n + 1):
        for v in range(1, depth + 1):
            wx, wz = P(u, v); b.set(wx, y, wz, floor); b.set(wx, y + h, wz, deck)
            for yy in range(y + 1, y + h): b.set(wx, yy, wz, AIR)
        wx, wz = P(u, depth)
        if u in cols:
            for yy in range(y + 1, y + h - 1): b.set(wx, yy, wz, col)
            b.set(wx, y + h - 1, wz, capb)
        elif u - 1 in cols: b.set(wx, y + h - 1, wz, stairs(st, CCW[side], "top"))
        elif u + 1 in cols: b.set(wx, y + h - 1, wz, stairs(st, CW[side], "top"))
        else: b.set(wx, y + h - 1, wz, slab(st.replace("_stairs", "_slab"), "top"))
        b.set(wx, y + h + 1, wz, slab(st.replace("_stairs", "_slab")))
    for u in (-n, n):
        for v in range(1, depth):
            wx, wz = P(u, v); b.set(wx, y + h + 1, wz, slab(st.replace("_stairs", "_slab")))
    foundation(b, [(min(P(-n, 1)[0], P(n, depth)[0]), min(P(-n, 1)[1], P(n, depth)[1]), max(P(-n, 1)[0], P(n, depth)[0]),
                    max(P(-n, 1)[1], P(n, depth)[1]))], y, floor)


# ------------------------------------------------------------------ wall recipes (guide 14)
def _bands(fn):
    fn.__doc__ = (fn.__doc__ or "") + ("\n    Common arguments: rect (a rect or list of rects: the outline of their union is walled), y0..y1 the storey (y1 is "
                                       "the beam / floor row), openings [(x, z, kind)] with kind door | window | none (other panels get windows "
                                       "at random). Returns {'windows': [...], 'doors': [...]}.")
    return fn


@_bands
def timber_wall(b, rect, y0, y1, rnd, openings=None, frame="minecraft:stripped_spruce_log", infill=PLASTER, base=None, win=GLASS,
                wood="spruce", every=4, brace=0.5, pwin=0.75, flowers=True, recess=(), lamp=True):
    """Timber frame (14a): posts at corners and every 3-4, a beam ring at y1, diagonal braces in some blank panels,
    plaster infill mixed from its variants (rougher low down). recess: sides whose infill sits 1 behind the frame (the
    posts and beam then stand out; glass, doors and braces sit in the recess)."""
    rects = _rl(rect); F, W, runs = outline(rects, every)
    ops = {(o[0], o[1]): o[2] for o in (openings or ())}
    posts = _postset(runs); res = {"windows": [], "doors": []}
    rec = set(DIRV) if recess is True else set(recess or ())
    trap = f"minecraft:{wood}_trapdoor"; sill = f"minecraft:{wood}_stairs"
    for (x, z), ds in W.items():
        post = (x, z) in posts or len(ds) != 1
        for yy in range(y0, y1):
            b.set(x, yy, z, _axis(frame, "y") if post else base if (base and yy == y0) else mix(infill, x, yy, z, rough=0.5 if yy < y0 + 2 and base else 0))
        b.set(x, y1, z, _axis(frame, "y" if post else _along(ds[0])))
    for ri, run in enumerate(runs):
        s = run["side"]; ox, oz = DIRV[s]; R = s in rec
        for pi, pc in enumerate(panels(run)):
            fc = [(x - ox, z - oz) for (x, z) in pc] if R else pc
            if R:
                for (x, z), (ix, iz) in zip(pc, fc):
                    for yy in range(y0, y1):
                        if base and yy == y0: continue
                        b.set(x, yy, z, AIR); b.set(ix, yy, iz, mix(infill, ix, yy, iz, rough=0.4))
            kinds = [ops.get(c) for c in pc]
            L = len(pc)
            if "door" in kinds:
                i = kinds.index("door"); dx, dz = fc[i]
                if R:
                    for yy in (y0, y0 + 1): b.set(pc[i][0], yy, pc[i][1], AIR)
                    b.set(pc[i][0], y0 + 2, pc[i][1], _axis(frame, _along(s)))
                _door(b, dx, dz, s, y0, wood, lamp=lamp and not R, lamp_at=None)
                if lamp and R and L > 1:
                    j = i + 1 if i + 1 < L else i - 1
                    b.set(pc[j][0], y0 + 2, pc[j][1], f"onepiece:wall_lamp[facing={s}]")
                res["doors"].append((dx, y0, dz, s)); continue
            if "none" in kinds: continue
            want = "window" in kinds or rnd.random() < pwin
            if want:
                sel = [fc[i] for i in ([0] if L == 1 else ([0, 1] if rnd.random() < 0.4 else [rnd.randint(0, 1)]) if L == 2 else [1] if L == 3 else [1, L - 2])]
                shut = rnd.random() < 0.4
                if L >= 4:
                    for c in sel: _window(b, [c], s, y0 + 1, y1 - 1, win, sill=sill, flower=flowers and not base, trap=None, out=2 if R else 1)
                else:
                    _window(b, sel, s, y0 + 1, y1 - 1, win, sill=sill, flower=flowers and not base, trap=trap if (L == 3 and shut) else None, out=2 if R else 1)
                if R and L >= 2 and shut:
                    for (x, z) in pc:
                        if (x - ox, z - oz) not in sel and b.get(x, y0 + 1, z) == AIR:
                            for yy in range(y0 + 1, y1): b.set(x, yy, z, trapdoor(trap, s, "bottom", "true"))
                res["windows"] += [(c[0], y0 + 1, c[1], s) for c in sel]
            elif L >= 2 and rnd.random() < brace / max(0.01, 1 - pwin) + 0.3:
                seq = pc if (ri + pi) % 2 else pc[::-1]
                H = y1 - y0
                lasty = y0 - 1
                for i, (x, z) in enumerate(seq):
                    ty = y0 + round(i * (H - 1) / (L - 1))
                    for yy in range(max(y0, lasty + 1 if i else y0), ty + 1): b.set(x, yy, z, _axis(frame, "y"))
                    lasty = ty
    return res


@_bands
def stone_wall(b, rect, y0, y1, rnd, openings=None, main=("minecraft:stone_bricks", "minecraft:cracked_stone_bricks", "minecraft:mossy_stone_bricks",
               "minecraft:stone_bricks", "minecraft:andesite"), quoin="minecraft:polished_andesite", trim="minecraft:stone_brick_stairs",
               win=GLASS, every=4, pwin=0.8, ground=None, plinth=True, string=True, pilasters=True, keystone="minecraft:chiseled_stone_bricks",
               wood="spruce", lamp=True, flowers=False, top=False):
    """Stone (14b): quoins at the corners (alternating 1 and 2 wide), mossy and cracked bricks low down fading out
    higher up, pilasters 1 out on long runs, a plinth of stairs at the foot, a string course at the floor line, windows
    with a stair sill, a keystone over them, vines on some north faces. ground = the y the gradient counts from."""
    rects = _rl(rect); F, W, runs = outline(rects, every)
    ops = {(o[0], o[1]): o[2] for o in (openings or ())}
    gy = y0 if ground is None else ground
    res = {"windows": [], "doors": []}
    tsl = trim.replace("_stairs", "_slab")
    for (x, z), ds in W.items():
        for yy in range(y0, y1 + 1):
            rough = max(0.0, 1 - (yy - gy) / 9)
            m = mix(main, x, yy, z, rough=rough) if rough > 0.05 else main[0] if not isinstance(main, str) else main
            b.set(x, yy, z, quoin if (len(ds) != 1 and quoin) else m)
    for run in runs:
        s = run["side"]; ox, oz = DIRV[s]; q = run["cells"]; n = len(q)
        if quoin:  # second quoin block on alternate rows
            for end, nxt in ((0, 1), (n - 1, n - 2)):
                if 0 <= nxt < n and len(W.get(q[end], [])) != 1:
                    for yy in range(y0, y1 + 1):
                        if (yy + (0 if s in ("north", "south") else 1)) % 2 == 0: b.set(q[nxt][0], yy, q[nxt][1], quoin)
        if pilasters and n >= 9:
            for i in run["posts"][1:-1]:
                px, pz = q[i][0] + ox, q[i][1] + oz
                for yy in range(y0, y1): b.set(px, yy, pz, quoin or main[0])
                if top: b.set(px, y1, pz, stairs(trim, OPP[s]))
        for (x, z) in q:
            ex, ez = x + ox, z + oz
            if plinth and _soft(b.get(ex, y0, ez)) and (_solid(b.get(ex, y0 - 1, ez)) or b.get(ex, y0 - 1, ez) is None and y0 <= gy + 1):
                b.set(ex, y0, ez, stairs(trim, OPP[s]))
            if string and _soft(b.get(ex, y1, ez)): b.set(ex, y1, ez, slab(tsl, "top"))
        if string:
            for end in (q[0], q[-1]):
                if len(W.get(end, [])) == 2:
                    o2 = [d for d in W[end] if d != s][0]
                    cx, cz = end[0] + ox + DIRV[o2][0], end[1] + oz + DIRV[o2][1]
                    b.fill_if(cx, y1, cz, slab(tsl, "top"))
        for pc in panels(run):
            kinds = [ops.get(c) for c in pc]; L = len(pc)
            if "door" in kinds:
                i = kinds.index("door"); dx, dz = pc[i]
                _door(b, dx, dz, s, y0, wood, lamp=lamp)
                b.set(dx, y0 + 2, dz, keystone)
                if _soft(b.get(dx + ox, y0 - 1, dz + oz)) or "stairs" in (b.get(dx + ox, y0, dz + oz) or ""): b.set(dx + ox, y0, dz + oz, AIR)
                res["doors"].append((dx, y0, dz, s)); continue
            if "none" in kinds or not ("window" in kinds or rnd.random() < pwin): continue
            sel = [pc[L // 2]] if L % 2 else pc[L // 2 - 1:L // 2 + 1]
            _window(b, sel, s, y0 + 1, y1 - 1, win, sill=None if plinth else trim, flower=flowers)
            if len(sel) == 1 and keystone: b.set(sel[0][0], y1, sel[0][1], keystone)
            res["windows"] += [(c[0], y0 + 1, c[1], s) for c in sel]
        if s == "north":  # vines on some north faces
            for (x, z) in q:
                if _h(x, y0, z, 31) < 0.12:
                    for yy in range(y1 - 1, y0 - 1 - int(_h(x, 0, z, 3) * 2), -1):
                        if _soft(b.get(x, yy, z - 1)) and _solid(b.get(x, yy, z)):
                            b.set(x, yy, z - 1, "minecraft:vine[east=false,north=false,south=true,up=false,west=false]")
    return res


@_bands
def desert_wall(b, rect, y0, y1, rnd, openings=None, level=0, color=None, chamfer=True, shutter="minecraft:jungle_trapdoor",
                base="minecraft:sandstone", every=3, pwin=0.5, mashrabiya=0.25, wood="jungle", lamp=True):
    """Desert / Alabasta (14c): smooth and cut sandstone low, whiter higher (calcite, white terracotta, quartz), patchy
    plaster render with the rough stone showing through, rounded (wall-block) corners, arched windows with a hood of
    stairs or jungle shutters, mashrabiya screens on brackets upstairs, an arched portal at the door. color: a
    terracotta for a painted band house."""
    rects = _rl(rect); F, W, runs = outline(rects, every)
    ops = {(o[0], o[1]): o[2] for o in (openings or ())}
    res = {"windows": [], "doors": []}
    low = ("minecraft:smooth_sandstone", "minecraft:sandstone", "minecraft:cut_sandstone", "minecraft:smooth_sandstone")
    high = ("minecraft:smooth_sandstone", "minecraft:white_terracotta", "minecraft:calcite", "minecraft:smooth_quartz", "minecraft:smooth_sandstone")
    big = max(r[2] - r[0] for r in rects) >= 6 and max(r[3] - r[1] for r in rects) >= 6
    for (x, z), ds in W.items():
        for yy in range(y0, y1 + 1):
            if level == 0 and yy == y0 and base: blk = base
            elif color and yy < y1: blk = color if _h(x, yy, z, 4) > 0.1 else "minecraft:white_terracotta"
            else:
                pal = high if level >= 1 or yy > y0 + 2 else low
                blk = pal[0] if noise(x, yy, z, 9, 2.2) < 0.55 else mix(pal, x, yy, z, rough=0.8)
            if chamfer and big and len(ds) == 2: blk = wall("minecraft:sandstone_wall" if yy < y1 else "minecraft:smooth_sandstone")
            b.set(x, yy, z, blk)
    st = "minecraft:smooth_sandstone_stairs"
    for run in runs:
        s = run["side"]; ox, oz = DIRV[s]
        for pc in panels(run):
            kinds = [ops.get(c) for c in pc]; L = len(pc)
            if "door" in kinds:
                i = kinds.index("door"); dx, dz = pc[i]
                _door(b, dx, dz, s, y0, wood, lamp=False)
                P = _loc(dx, dz, s)
                for u in (-1, 1):
                    jx, jz = P(u, 1)
                    for yy in (y0, y0 + 1): b.set(jx, yy, jz, wall("minecraft:sandstone_wall"))
                    b.set(jx, y0 + 2, jz, stairs(st, CW[s] if u < 0 else CCW[s], "top"))
                b.set(dx, y0 + 2, dz, "minecraft:chiseled_sandstone")
                res["doors"].append((dx, y0, dz, s)); continue
            if "none" in kinds or not ("window" in kinds or rnd.random() < pwin): continue
            sel = [pc[L // 2]]
            wx, wz = sel[0]
            P = _loc(wx, wz, s)
            if level >= 1 and rnd.random() < mashrabiya:  # a screen of trapdoors 1 out, on a bracket, with a slab hood
                _window(b, sel, s, y0 + 1, y0 + 2, win=GLASS)
                mx, mz = P(0, 1)
                b.set(mx, y0, mz, stairs(st, OPP[s], "top"))
                for yy in (y0 + 1, y0 + 2): b.set(mx, yy, mz, trapdoor(shutter, OPP[s], "bottom", "true"))
                b.set(mx, y0 + 3, mz, slab("minecraft:smooth_sandstone_slab"))
            elif level >= 1 or rnd.random() < 0.75:  # arched: springers either side of the head, a slab sill
                _window(b, sel, s, y0 + 1, y0 + 2, win=GLASS)
                for u in (-1, 1):
                    hx, hz = P(u, 1)
                    if _soft(b.get(hx, y0 + 2, hz)): b.set(hx, y0 + 2, hz, stairs(st, CW[s] if u < 0 else CCW[s], "top"))
                sx, sz = P(0, 1); b.fill_if(sx, y0, sz, slab("minecraft:smooth_sandstone_slab", "top"))
            else:
                _window(b, sel, s, y0 + 1, y0 + 2, win=GLASS, sill=st, trap=shutter)
            res["windows"] += [(wx, y0 + 1, wz, s)]
    return res


@_bands
def japanese_wall(b, rect, y0, y1, rnd, openings=None, frame="minecraft:stripped_dark_oak_log", infill=("minecraft:white_terracotta", "minecraft:calcite"),
                  shoji="minecraft:white_stained_glass_pane", shoji_sides=("south",), every=3, wood="spruce", pwin=0.6):
    """Japanese / Wano (14d): a dark wood frame on a strict grid (posts every 2 to 3, beam ring at y1, a rail one row
    under it), white plaster panels; on shoji_sides the lower rows are sliding paper screens, elsewhere small paper
    windows with a lattice of trapdoors outside some of them."""
    rects = _rl(rect); F, W, runs = outline(rects, every)
    ops = {(o[0], o[1]): o[2] for o in (openings or ())}
    posts = _postset(runs); res = {"windows": [], "doors": []}
    sh = pane_of(shoji)
    for (x, z), ds in W.items():
        post = (x, z) in posts or len(ds) != 1
        for yy in range(y0, y1):
            b.set(x, yy, z, _axis(frame, "y") if post else mix(infill, x, yy, z))
        b.set(x, y1, z, _axis(frame, "y" if post else _along(ds[0])))
    for run in runs:
        s = run["side"]; ox, oz = DIRV[s]
        for pc in panels(run):
            kinds = [ops.get(c) for c in pc]
            for (x, z) in pc: b.set(x, y1 - 1, z, _axis(frame, _along(s)))  # the rail (nageshi)
            if "door" in kinds:
                i = kinds.index("door"); dx, dz = pc[i]
                _door(b, dx, dz, s, y0, "spruce", lamp=False)
                for j, (x, z) in enumerate(pc):
                    if j != i:
                        for yy in (y0, y0 + 1): b.set(x, yy, z, sh)
                res["doors"].append((dx, y0, dz, s)); continue
            if "none" in kinds: continue
            if s in shoji_sides:
                for (x, z) in pc:
                    for yy in (y0, y0 + 1): b.set(x, yy, z, sh)
                res["windows"] += [(x, y0, z, s) for (x, z) in pc]
            elif "window" in kinds or rnd.random() < pwin:
                c = pc[len(pc) // 2]
                b.set(c[0], y0 + 1, c[1], sh)
                if rnd.random() < 0.5 and _soft(b.get(c[0] + ox, y0 + 1, c[1] + oz)):
                    b.set(c[0] + ox, y0 + 1, c[1] + oz, trapdoor("minecraft:spruce_trapdoor", OPP[s], "bottom", "true"))
                res["windows"].append((c[0], y0 + 1, c[1], s))
    return res


@_bands
def venetian_wall(b, rect, y0, y1, rnd, openings=None, stucco="minecraft:pink_terracotta", trim="minecraft:polished_andesite",
                  trim_st="minecraft:polished_andesite_stairs", level=1, win=GLASS, flowers=True, wood="dark_oak", water=False):
    """Venetian / Water 7 (14e): pastel stucco upstairs, a rusticated stone ground floor with a mossy waterline course,
    stone quoins and a stone band at every floor line. Windows follow the Venetian rhythm along each face: jamb, glass,
    jamb, stucco pier (two windows share a jamb on narrow fronts), each with an arched head of stairs in the band, a
    stone sill and a flower box upstairs."""
    rects = _rl(rect); F, W, runs = outline(rects, 99)
    ops = {(o[0], o[1]): o[2] for o in (openings or ())}
    res = {"windows": [], "doors": []}
    var = {"minecraft:white_terracotta": "minecraft:calcite"}.get(stucco, "minecraft:white_terracotta")
    for (x, z), ds in W.items():
        corner = len(ds) != 1
        for yy in range(y0, y1 + 1):
            if level == 0:
                blk = "minecraft:mossy_stone_bricks" if yy == y0 and (water or _h(x, yy, z) < 0.5) else \
                    ("minecraft:stone_bricks" if (yy - y0) % 2 else "minecraft:polished_andesite") if not corner else trim
            elif yy == y1 or corner and (yy + x + z) % 2 == 0: blk = trim
            else: blk = stucco if _h(x, yy, z, 2) > 0.12 else var
            b.set(x, yy, z, blk)
    for run in runs:
        s = run["side"]; ox, oz = DIRV[s]
        inner = run["cells"][1:-1]; n = len(inner)
        off = 1 if (n - 3) % 4 == 2 else 0
        role = {}
        for i, c in enumerate(inner):
            k = (i - off) % 4 if off <= i < n - off else 3
            role[c] = "jgjs"[k]
        if role and list(role.values())[-1] == "j" and n % 4 == 0: role[inner[-1]] = "s"
        for c in inner:
            if ops.get(c) == "door":
                _door(b, c[0], c[1], s, y0, wood, lamp=True)
                b.set(c[0], y0 + 2, c[1], stairs(trim_st, OPP[s], "top") if level else "minecraft:chiseled_stone_bricks")
                res["doors"].append((c[0], y0, c[1], s))
        for i, c in enumerate(inner):
            if role[c] != "g" or ops.get(c) in ("door", "none"): continue
            nb = [inner[j] for j in (i - 1, i + 1) if 0 <= j < n]
            if any(ops.get(q) == "door" for q in nb): continue
            if level == 0 and rnd.random() < 0.5: continue
            _window(b, [c], s, y0 + 1, y1 - 1, win, sill=trim_st, flower=flowers and level >= 1)
            for q in nb:
                for yy in range(y0 + 1, y1): b.set(q[0], yy, q[1], trim)
            if level >= 1:
                b.set(c[0], y1, c[1], "minecraft:chiseled_stone_bricks")
                a = (1, 0) if s in ("north", "south") else (0, 1)
                for q in nb:
                    away = ("east" if q[0] > c[0] else "west") if a == (1, 0) else ("south" if q[1] > c[1] else "north")
                    b.set(q[0], y1, q[1], stairs(trim_st, away, "top"))
            res["windows"].append((c[0], y0 + 1, c[1], s))
    return res


# ------------------------------------------------------------------ houses
PAL = {
    # recipe, frame, infill/main, roof stairs, roof full, ridge, alt stairs, floor, door wood, base, roof kinds
    "east_blue": dict(rec="timber", frame="minecraft:stripped_dark_oak_log", infill=PLASTER, st="minecraft:spruce_stairs",
                      full="minecraft:spruce_planks", ridge="minecraft:dark_oak_slab", alt="minecraft:dark_oak_stairs",
                      floor="minecraft:spruce_planks", wood="spruce", base="minecraft:cobblestone", roofs=("gable", "half_hip", "gambrel")),
    "cottage": dict(rec="timber", frame="minecraft:oak_log", infill=("minecraft:packed_mud", "minecraft:mud_bricks", "minecraft:packed_mud"),
                    st="minecraft:dark_oak_stairs", full="minecraft:dark_oak_planks", ridge="minecraft:spruce_slab", alt="minecraft:spruce_stairs",
                    floor="minecraft:oak_planks", wood="oak", base="minecraft:cobblestone", roofs=("saltbox", "gable", "half_hip")),
    "brick": dict(rec="timber", frame="minecraft:dark_oak_log", infill=("minecraft:bricks", "minecraft:bricks", "minecraft:granite"),
                  st="minecraft:deepslate_tile_stairs", full="minecraft:deepslate_tiles", ridge="minecraft:polished_blackstone_slab",
                  alt="minecraft:cobbled_deepslate_stairs", floor="minecraft:spruce_planks", wood="dark_oak", base="minecraft:stone_bricks",
                  roofs=("gable", "gambrel", "half_hip")),
    "plaster": dict(rec="timber", frame="minecraft:stripped_dark_oak_log", infill=("minecraft:white_concrete_powder", "minecraft:calcite", "minecraft:white_terracotta"),
                    st="minecraft:brick_stairs", full="minecraft:bricks", ridge="minecraft:red_nether_brick_slab",
                    alt="minecraft:red_nether_brick_stairs", floor="minecraft:birch_planks", wood="dark_oak", base="minecraft:stone_bricks",
                    roofs=("mansard", "half_hip", "hip")),
    "orange": dict(rec="timber", frame="minecraft:stripped_spruce_log", infill=("minecraft:orange_terracotta", "minecraft:terracotta", "minecraft:orange_terracotta"),
                   st="minecraft:spruce_stairs", full="minecraft:spruce_planks", ridge="minecraft:dark_oak_slab", alt="minecraft:dark_oak_stairs",
                   floor="minecraft:spruce_planks", wood="spruce", base="minecraft:cobblestone", roofs=("gable", "saltbox", "gambrel")),
    "snow": dict(rec="timber", frame="minecraft:stripped_spruce_log", infill=("minecraft:spruce_planks", "minecraft:stripped_spruce_wood[axis=y]"),
                 st="minecraft:dark_oak_stairs", full="minecraft:dark_oak_planks", ridge="minecraft:dark_oak_planks", alt="minecraft:spruce_stairs",
                 floor="minecraft:spruce_planks", wood="spruce", base="minecraft:cobblestone", roofs=("gable", "gambrel")),
    "stone": dict(rec="stone", frame="minecraft:polished_andesite", infill=("minecraft:stone_bricks", "minecraft:cracked_stone_bricks",
                  "minecraft:mossy_stone_bricks", "minecraft:stone_bricks", "minecraft:andesite"), st="minecraft:deepslate_tile_stairs",
                  full="minecraft:deepslate_tiles", ridge="minecraft:deepslate_brick_slab", alt="minecraft:cobbled_deepslate_stairs",
                  floor="minecraft:spruce_planks", wood="spruce", base="minecraft:cobblestone", roofs=("hip", "mansard", "half_hip")),
}
WING_ROOF = {"gable": "gable", "half_hip": "gable", "gambrel": "gable", "saltbox": "gable", "hip": "hip", "mansard": "hip",
             "hip_low": "hip_low", "irimoya": "hip"}


def _wpick(rnd, pairs):
    t = rnd.random() * sum(w for _, w in pairs)
    for v, w in pairs:
        t -= w
        if t <= 0: return v
    return pairs[-1][0]


def _carve(b, F, W, y0, y1, ceiling):
    """Air inside the storey, the floor/ceiling row at y1 inside the walls."""
    for c in F:
        if c in W: continue
        for yy in range(y0, y1): b.set(c[0], yy, c[1], AIR)
        b.set(c[0], y1, c[1], ceiling)


def _gable_fn(P):
    """Gable infill: plaster with a post every 3 and a tie beam, so a timber gable stays framed (no flat triangle)."""
    if P["rec"] != "timber": return lambda x, y, z: mix(P["infill"], x, y, z)
    fr = P["frame"]
    return lambda x, y, z: _axis(fr, "y") if (x + z) % 3 == 0 else mix(P["infill"], x, y, z)


def _door_near(fronts, door, at):
    """The panel cell of a front run nearest the along-coordinate `at` (never a post), or None when `at` is None."""
    if at is None or not fronts: return None
    k = 0 if door in ("north", "south") else 1
    cells = [(i, c) for i, f in enumerate(fronts) for p in panels(f) for c in p] or [(i, c) for i, f in enumerate(fronts) for c in f["cells"]]
    return min(cells, key=lambda ic: (abs(ic[1][k] - at), ic[0]))[1]


def house2(b, x0, z0, w, d, floors=2, style="east_blue", rnd=None, y=None, door="south", plan=None, roof_kind=None,
           addons=None, curve=None, jetty=None, stone_ground=None, chimney_=True, min_d=8, addon_sides=None, dormer_min=8, recess=None, door_at=None,
           jetty_sides=None):
    """European town house (guide 10, 13, 14a/b): a compound plan (L / T / offset / U / plain, wings one floor lower),
    a timber or stone wall recipe per storey (a stone ground floor on 1 in 3 timber houses), a jettied upper floor on
    stair brackets, a roof with cross gables and valleys, a chimney through the roof, and two or more add-ons from
    bay / porch / dormer / balcony / tower. The interior is left empty with a ladder between floors. addon_sides: the
    only sides a bay, balcony or tower may stick out of (a town row keeps them off the sides that face neighbours);
    dormer_min: the least roof depth across the ridge that gets dormers. recess: False keeps the ground-floor infill
    flush (on small plots a recess eats a block of room on every side), None picks it on 60 % of timber houses.
    plan may also be a list of rects (main first, as plan_rects returns them). door_at: the x (north/south door) or z
    (east/west) the door should be nearest (a town caller whose street runs to the middle of the plot). jetty_sides: the
    only sides the upper floors may overhang (a neighbour close by on the others: its roof would be built into).
    Returns {door: (x, y, z, side), floors: [standing y per storey], rooms: [[rects] per storey], rects, top, y,
    ladder: [(x, z)], addons: [...]} so callers can furnish it with interiors.furnish()."""
    rnd = rnd or random.Random(x0 * 7919 + z0 * 104729)
    P = PAL[style]
    kind = plan or _wpick(rnd, (("L", 4), ("T", 3), ("offset", 3), ("plain", 1), ("U", 1)))
    if isinstance(kind, (list, tuple)):  # the caller's own rects, main first: [(x0, z0, x1, z1, floors_delta), ...]
        rects, kind = [tuple(r) if len(r) > 4 else tuple(r) + (0,) for r in kind], "custom"
    else: rects = plan_rects(kind, x0, z0, w, d, rnd, front=door, min_d=min_d)
    y = site_y(b, rects) if y is None else y
    fr = [max(1, floors + r[4]) for r in rects]
    timber = P["rec"] == "timber"
    jetty = (timber and floors > 1) if jetty is None else jetty
    stone_ground = (timber and floors > 1 and rnd.random() < 0.33) if stone_ground is None else stone_ground
    main = rects[0][:4]
    free = [s for s in DIRV if _side_free(main, s, [r[:4] for r in rects[1:]])]
    xfree = [s for s in free if addon_sides is None or s in addon_sides]  # sides a bay / balcony / tower may use
    up = _grow(main, [s for s in free if s != door and (jetty_sides is None or s in jetty_sides)] if jetty else [], 1)
    back = OPP[door]
    roofk = roof_kind or rnd.choice(P["roofs"])

    def band(f):
        return [(up if (i == 0 and f >= 1) else r[:4]) for i, r in enumerate(rects) if fr[i] > f]
    # the door: middle of the longest front run of the ground floor
    F0, W0, runs0 = outline(band(0))
    fronts = sorted((r for r in runs0 if r["side"] == door), key=lambda r: -len(r["cells"]))
    pans = panels(fronts[0]) if fronts else []
    pc = pans[len(pans) // 2] if pans else [fronts[0]["cells"][len(fronts[0]["cells"]) // 2]]
    dcell = _door_near(fronts, door, door_at) or pc[len(pc) // 2]
    used = {door} if True else set()
    rec = [s for s in DIRV if s != back] if (timber and not stone_ground and rnd.random() < 0.6) else []
    if recess is False: rec = []
    foundation(b, [r[:4] for r in rects], y, P["base"])
    for r in rects: b.box(r[0], y, r[1], r[2], y, r[3], P["floor"])
    res_floors, rooms = [], []
    nf = max(fr)
    for f in range(nf):
        rs = band(f)
        y0, y1 = y + 1 + f * FH, y + (f + 1) * FH
        F, W, runs = outline(rs)
        _carve(b, F, W, y0, y1, P["floor"])
        ops = [(dcell[0], dcell[1], "door")] if f == 0 else []
        if timber and not (stone_ground and f == 0):
            timber_wall(b, rs, y0, y1, rnd, ops, frame=P["frame"], infill=P["infill"], base=P["base"] if f == 0 else None,
                        wood=P["wood"], recess=rec if f == 0 else ())
        else:
            stone_wall(b, rs, y0, y1, rnd, ops, main=P["infill"] if not timber else PAL["stone"]["infill"], ground=y + 1,
                       plinth=f == 0, string=True, wood=P["wood"], top=f == nf - 1)
            if timber:  # the timber storeys above sit on a beam ring
                for (x, z), ds in W.items(): b.set(x, y1, z, _axis(P["frame"], "y" if len(ds) != 1 else _along(ds[0])))
        if f >= 1 and jetty:  # moulding of upside-down stairs under the overhang, brackets below at the posts
            Fl, Wl, runsl = outline(band(f - 1))
            for (x, z), ds in W.items():
                if (x, z) in Fl: continue
                ins = [s for s, (dx, dz) in DIRV.items() if (x + dx, z + dz) in Fl]
                if len(ins) == 1:
                    b.set(x, y0 - 1, z, stairs(P["st"].replace("deepslate_tile", "spruce") if "deepslate" in P["st"] else P["st"], ins[0], "top"))
                    if (x + z) % 3 == 0 and _soft(b.get(x, y0 - 2, z)):
                        b.set(x, y0 - 2, z, stairs(f"minecraft:{P['wood']}_stairs", ins[0], "top"))
                else: b.set(x, y0 - 1, z, _axis(P["frame"], "y"))
        res_floors.append(y0)
        rooms.append(_rooms(rs, 2 if (f == 0 and rec) else 1))
    # ladder in a back corner of the main block
    if back in ("north", "south"):
        lx, lz = main[0] + 1, (main[1] + 1 if back == "north" else main[3] - 1); lf = door
    else:
        lx, lz = (main[0] + 1 if back == "west" else main[2] - 1), main[1] + 1; lf = door
    lad = (lx, lz, y + 1, y + (fr[0] - 1) * FH, f"minecraft:ladder[facing={lf},waterlogged=false]")
    if fr[0] > 1:
        for yy in range(lad[2], lad[3] + 1): b.set(lx, yy, lz, lad[4])
        back_ladder(b, lad, P["floor"])
    # roof
    rr = [(up if i == 0 else r[:4]) + (fr[i] - fr[0],) for i, r in enumerate(rects)]
    kinds = [roofk] + [WING_ROOF.get(roofk, "gable")] * (len(rects) - 1)
    top = roof(b, rr, kinds, P["st"], P["full"], y + fr[0] * FH, overhang=1, curve=curve, gable=_gable_fn(P), ridge=P["ridge"], alt=P["alt"])
    R = b._roof
    if style.split("/")[0] == "snow": snow_ridge(b)
    ytop = y + fr[0] * FH
    ux0, uz0, ux1, uz1 = up[:4]
    along_x = (ux1 - ux0) >= (uz1 - uz0)
    # chimney through the roof near one gable end, on the ridge line
    chx = None
    if chimney_:
        if along_x:
            chx = ux0 + 2 if rnd.random() < 0.5 else ux1 - 2; chz = (uz0 + uz1) // 2 + (1 if (uz1 - uz0) % 2 else 0)
            cc = (chx, chz)
        else:
            chz = uz0 + 2 if rnd.random() < 0.5 else uz1 - 2; chx_ = (ux0 + ux1) // 2; cc = (chx_, chz)
        sy = R["Y"].get(cc, ytop + 3)
        chimney(b, cc[0], cc[1], ytop + 1, sy + 2, "minecraft:bricks", cap="campfire")
    # add-ons
    want = list(addons) if addons is not None else rnd.sample(["bay", "porch", "dormer", "balcony", "tower"], 3)
    done = []
    eave_sides = ("north", "south") if along_x else ("west", "east")
    end_sides = ("west", "east") if along_x else ("north", "south")
    for a in want:
        if a == "porch" and "porch" not in done:
            if fr[0] >= 1:
                porch(b, dcell[0], dcell[1], door, y, w=5, depth=2, wood=P["wood"], st=P["st"],
                      floor=None if timber else "minecraft:polished_andesite")
                done.append("porch")
        elif a == "dormer" and roofk in ("gable", "half_hip", "hip") and (uz1 - uz0 if along_x else ux1 - ux0) >= dormer_min:
            sides = [s for s in eave_sides if s in free and not (roofk == "saltbox" and s in ("north", "west"))]
            if not sides: continue
            s = door if door in sides else sides[0]
            lo, hi = (ux0, ux1) if along_x else (uz0, uz1)
            n = 0
            # one dormer per 5-6 blocks of roof, spread from the middle out, never on the chimney (a chimney near
            # one end used to knock out the only slot on a 9-11 long roof)
            cu = (cc[0] if along_x else cc[1]) if chx is not None else None
            mid_ = (lo + hi) / 2; picks = []
            for u in sorted(range(lo + 2, hi - 1), key=lambda u: abs(u - mid_)):
                if cu is not None and abs(u - cu) <= 2 or any(abs(u - p) < 5 for p in picks): continue
                if len(picks) < max(1, (hi - lo + 1) // 6): picks.append(u)
            for u in sorted(picks):
                wx, wz = (u, uz1 if s == "south" else uz0) if along_x else (ux1 if s == "east" else ux0, u)
                dormer(b, wx, wz, s, ytop, P["st"], P["full"], mix(P["infill"], wx, 0, wz) if timber else P["infill"][0],
                       frame=_axis(P["frame"], "y")); n += 1
            if n: done.append("dormer")
        elif a == "bay" and "bay" not in done:
            sides = [s for s in end_sides if s in xfree and s not in used] + [s for s in eave_sides if s in xfree and s not in used]
            if not sides: continue
            s = sides[0]; used.add(s)
            onup = jetty and floors > 1
            rr_ = up if onup else main
            x_, z_ = {"north": ((rr_[0] + rr_[2]) // 2, rr_[1]), "south": ((rr_[0] + rr_[2]) // 2, rr_[3]),
                      "west": (rr_[0], (rr_[1] + rr_[3]) // 2), "east": (rr_[2], (rr_[1] + rr_[3]) // 2)}[s]
            bay(b, x_, z_, s, y + FH if onup else y, 1, wall=mix(P["infill"], x_, 1, z_), st=P["st"], frame=P["frame"], base=P["base"])
            done.append("bay")
        elif a == "balcony" and floors >= 2 and "balcony" not in done:
            sides = [s for s in (back,) + tuple(end_sides) if s in xfree and s not in used]
            if not sides: continue
            s = sides[0]; used.add(s)
            x_, z_ = {"north": ((ux0 + ux1) // 2, uz0), "south": ((ux0 + ux1) // 2, uz1), "west": (ux0, (uz0 + uz1) // 2),
                      "east": (ux1, (uz0 + uz1) // 2)}[s]
            balcony(b, x_, z_, s, y + FH, w=3, out=1, wood=P["wood"], rail=None if timber else wall("minecraft:stone_brick_wall"),
                    floor=None if timber else "minecraft:polished_andesite")
            done.append("balcony")
        elif a == "tower" and "tower" not in done:
            sz = 5 if min(w, d) >= 11 else 3
            cands = []
            for s in end_sides:
                if s not in xfree or s in used: continue
                for zz in ((main[1], main[3] - sz + 1) if s in ("west", "east") else (main[0], main[2] - sz + 1)):
                    if s in ("west", "east"):
                        tx = main[0] - sz if s == "west" else main[2] + 1; tz = zz
                    else:
                        tz = main[1] - sz if s == "north" else main[3] + 1; tx = zz
                    box = (tx - 1, tz - 1, tx + sz, tz + sz)
                    if any(o[0] <= box[2] and o[2] >= box[0] and o[1] <= box[3] and o[3] >= box[1] for o in [r[:4] for r in rects[1:]]): continue
                    cands.append((s, tx, tz))
            if not cands: continue
            s, tx, tz = cands[0] if (cands[0][2] == main[1] or len(cands) == 1) else cands[1]
            used.add(s)
            opens = []
            for f in range(fr[0]):
                if s in ("west", "east"):
                    hx = main[0] if s == "west" else main[2]; hz = tz + sz // 2
                    opens += [(hx, hz, y + 1 + f * FH), (hx + (-1 if s == "west" else 1), hz, y + 1 + f * FH)]
                else:
                    hz = main[1] if s == "north" else main[3]; hx = tx + sz // 2
                    opens += [(hx, hz, y + 1 + f * FH), (hx, hz + (-1 if s == "north" else 1), y + 1 + f * FH)]
            stair_tower(b, tx, tz, y, fr[0] * FH + 4, size=sz, wall=P["infill"],
                        st=P["st"], full=P["full"], frame=_axis(P["frame"], "y"), door_side=door, base=P["base"], open_to=opens[2:] if sz >= 5 else [])
            done.append("tower")
    if "porch" not in done:  # a small awning of top slabs over the door
        Pd = _loc(dcell[0], dcell[1], door)
        for u in (-1, 0, 1):
            ax, az = Pd(u, 1)
            if _soft(b.get(ax, y + 4, az)): b.set(ax, y + 4, az, slab(P["st"].replace("_stairs", "_slab"), "top"))
    ox, oz = DIRV[door]
    if not _solid(b.get(dcell[0] + ox, y, dcell[1] + oz)): b.set(dcell[0] + ox, y, dcell[1] + oz, P["base"])
    for k in (1, 2):
        if "stairs" in (b.get(dcell[0] + ox, y + k, dcell[1] + oz) or "") or "slab" in (b.get(dcell[0] + ox, y + k, dcell[1] + oz) or ""):
            b.set(dcell[0] + ox, y + k, dcell[1] + oz, AIR)
    # a skirt of slabs along the foot of the walls where the ground is level
    for (x, z), ds in W0.items():
        for s in ds:
            ex, ez = x + DIRV[s][0], z + DIRV[s][1]
            if _soft(b.get(ex, y + 1, ez)) and _solid(b.get(ex, y, ez)) and abs(ex - dcell[0]) + abs(ez - dcell[1]) > 2 and _h(ex, y, ez, 8) < 0.7 \
                    and not any("_door[" in (b.get(ex + i, y + 1, ez + k) or "") for i in (-1, 0, 1) for k in (-1, 0, 1)):  # nor a neighbour's door step
                b.set(ex, y + 1, ez, slab(P["base"].replace("cobblestone", "cobblestone_slab").replace("stone_bricks", "stone_brick_slab")))
    return {"door": (dcell[0], y + 1, dcell[1], door), "outside": (dcell[0] + ox, y + 1, dcell[1] + oz), "floors": res_floors,
            "rooms": rooms, "rects": rects, "top": top, "y": y, "ladder": [lad] if fr[0] > 1 else [], "addons": done, "roof": roofk, "plan": kind}


def _roof_items(b, area, y, rnd, n=2, colors=None, skip=()):
    """Things on a flat roof (guide 14c): pick n of canopy / tank / rugs / pergola / wind catcher / hut within the deck
    rect `area` (inside the parapet) at deck level y. Every piece stands on the deck."""
    x0, z0, x1, z1 = area
    if x1 - x0 < 2 or z1 - z0 < 2: return []
    colors = colors or rnd.sample(AWNING_COLORS, 2)
    opts = ["canopy", "tank", "rugs", "pergola", "wind_catcher"]
    opts = [o for o in opts if o not in skip]
    picks = rnd.sample(opts, min(n, len(opts)))
    cells = [(x, z) for x in range(x0, x1 - 1) for z in range(z0, z1 - 1)]
    rnd.shuffle(cells)
    taken = set(); out = []
    def fits(x, z, a, c):
        return x + a - 1 <= x1 and z + c - 1 <= z1 and not any((xx, zz) in taken for xx in range(x - 1, x + a + 1) for zz in range(z - 1, z + c + 1))
    for p in picks:
        a, c = {"canopy": (3, 3), "tank": (2, 2), "rugs": (3, 2), "pergola": (3, 3), "wind_catcher": (2, 2)}[p]
        spot = next(((x, z) for (x, z) in cells if fits(x, z, a, c)), None)
        if not spot: continue
        x, z = spot
        taken.update((xx, zz) for xx in range(x, x + a) for zz in range(z, z + c))
        if p == "canopy":
            for (px, pz) in ((x, z), (x + 2, z), (x, z + 2), (x + 2, z + 2)):
                for yy in range(y + 1, y + 4): b.set(px, yy, pz, fence("jungle"))
            for xx in range(x, x + 3):
                for zz in range(z, z + 3): b.set(xx, y + 4, zz, f"minecraft:{colors[(xx - x) % 2]}_wool")
            b.set(x + 1, y + 1, z + 1, f"minecraft:{colors[1]}_carpet")
        elif p == "tank":
            for (px, pz) in ((x, z), (x + 1, z), (x, z + 1)): b.set(px, y + 1, pz, "minecraft:barrel[facing=up,open=false]")
            b.set(x, y + 2, z, "minecraft:barrel[facing=up,open=false]"); b.set(x + 1, y + 1, z + 1, "minecraft:cauldron")
        elif p == "rugs":
            for xx in range(x, x + 3):
                for zz in range(z, z + 2): b.set(xx, y + 1, zz, f"minecraft:{colors[(xx + zz) % 2]}_carpet")
            b.set(x + 2, y + 1, z + 1, "minecraft:decorated_pot[cracked=false,facing=north,waterlogged=false]")
        elif p == "pergola":
            for (px, pz) in ((x, z), (x + 2, z), (x, z + 2), (x + 2, z + 2)):
                for yy in range(y + 1, y + 4): b.set(px, yy, pz, fence("jungle"))
            for xx in range(x, x + 3):
                for zz in range(z, z + 3):
                    if (xx - x) % 2 == 0 or (zz - z) % 2 == 0: b.set(xx, y + 4, zz, slab("minecraft:jungle_slab"))
            b.set(x + 1, y + 4, z, "minecraft:flowering_azalea_leaves[distance=7,persistent=true,waterlogged=false]")
            b.set(x + 1, y + 1, z + 1, "minecraft:potted_cactus")
        elif p == "wind_catcher":
            for xx in range(x, x + 2):
                for zz in range(z, z + 2):
                    for yy in range(y + 1, y + 4): b.set(xx, yy, zz, "minecraft:smooth_sandstone")
                    b.set(xx, y + 4, zz, slab("minecraft:smooth_sandstone_slab"))
            b.set(x, y + 3, z, AIR); b.set(x + 1, y + 3, z, AIR)  # open to the wind on one side
            b.set(x, y + 3, z, wall("minecraft:sandstone_wall")); b.set(x + 1, y + 3, z, AIR)
        out.append(p)
    return out


def desert_house(b, x0, z0, w, d, floors=2, rnd=None, y=None, door="south", dome=None, color=None, plan=None, outside_stair=True,
                 arcade_=None, door_at=None):
    """Alabasta house (14c): stacked cubic volumes (wings a floor lower, the top storey stepped back for a roof
    terrace), sand-to-white walls with plaster patches and rounded corners, vigas under every roof line, a different
    parapet per volume, an arched portal with a striped awning, a dome on a windowed drum on 1 in 3 (or dome=True),
    two or more roof items on every flat roof, stairs up the outside wall to a terrace, an optional arcade.
    Returns the same dict as house2."""
    rnd = rnd or random.Random(x0 * 131 + z0 * 17)
    kind = plan or rnd.choice(("L", "offset", "L", "T", "plain"))
    if isinstance(kind, (list, tuple)): rects, kind = [tuple(r) if len(r) > 4 else tuple(r) + (0,) for r in kind], "custom"
    else: rects = plan_rects(kind, x0, z0, w, d, rnd, front=door)
    y = site_y(b, rects) if y is None else y
    fr = [max(1, floors + r[4]) for r in rects]
    main = rects[0][:4]
    back = OPP[door]
    # the top storey of the main block steps back from the front, leaving a terrace
    topr = main
    if fr[0] >= 2:
        k = 2 if (main[3] - main[1] if door in ("north", "south") else main[2] - main[0]) >= 8 else 0
        topr = _grow(main, [door], -k) if k else main
        if rnd.random() < 0.5 and (main[2] - main[0] if door in ("north", "south") else main[3] - main[1]) >= 8:
            topr = _grow(topr, [CW[door]], -2)
    def band(f):
        return [(topr if (i == 0 and f == fr[0] - 1) else r[:4]) for i, r in enumerate(rects) if fr[i] > f]
    F0, W0, runs0 = outline(band(0), 3)  # every=3 as desert_wall, so the door cell is a panel, never a post
    fronts = sorted((r for r in runs0 if r["side"] == door), key=lambda r: -len(r["cells"]))
    q = fronts[0]["cells"]; pans = panels(fronts[0])
    pc = pans[len(pans) // 2] if pans else [q[len(q) // 2]]
    dcell = _door_near(fronts, door, door_at) or pc[len(pc) // 2]
    foundation(b, [r[:4] for r in rects], y, "minecraft:sandstone")
    for r in rects: b.box(r[0], y, r[1], r[2], y, r[3], "minecraft:smooth_sandstone")
    floors_y, rooms = [], []
    nf = max(fr)
    paint = color if color is not None else (rnd.choice(("minecraft:white_terracotta", "minecraft:calcite", "minecraft:white_terracotta"))
                                             if rnd.random() < 0.33 else None)  # pink / orange terracotta on sandstone read as flesh
    beams = rnd.random() < 0.5  # vigas on 1 house in 2: on every house and every storey they pock the walls
    for f in range(nf):
        rs = band(f)
        y0, y1 = y + 1 + f * FH, y + (f + 1) * FH
        F, W, runs = outline(rs)
        _carve(b, F, W, y0, y1, "minecraft:smooth_sandstone" if f == nf - 1 else "minecraft:jungle_planks")
        desert_wall(b, rs, y0, y1, rnd, [(dcell[0], dcell[1], "door")] if f == 0 else [], level=f, color=paint if f >= 1 else None)
        floors_y.append(y0); rooms.append(_rooms(rs, 1))
    # flat roofs: vigas, parapets and roof items on every volume's exposed deck
    items = []
    dome_on = dome if dome is not None else rnd.random() < 0.4
    roof_tops = []
    for f in range(nf):
        rs = band(f); y1 = y + (f + 1) * FH
        Fu = outline(band(f + 1))[0] if f + 1 < nf else set()
        F, W, runs = outline(rs)
        exposed = [c for c in F if c not in Fu]
        if not exposed: continue
        if beams and f == nf - 1: vigas(b, rs, y1, every=2, out=1, skip=Fu)
        for r in rs:
            if all((x, z) in Fu for x in range(r[0], r[2] + 1) for z in range(r[1], r[3] + 1)): continue
            pk = rnd.choice(("plain", "stepped", "rounded", "plain"))
            parapet(b, r, y1, pk, skip=Fu | {c for c in F if c not in outline([r])[1]})
            roof_tops.append((r, y1, Fu))
    # the top volume: a dome on a drum, or two roof items
    tr, ty = band(nf - 1)[0], y + nf * FH
    cx, cz = (tr[0] + tr[2]) // 2, (tr[1] + tr[3]) // 2
    span = min(tr[2] - tr[0], tr[3] - tr[1]) + 1
    skip_items = set()
    if dome_on and span >= 7:
        r_ = 2 if span < 9 else 3 if span < 13 else 4
        b.cyl(cx, cz, r_ + 0.4, ty + 1, ty + 2, "minecraft:smooth_sandstone", hollow=True)
        for s, (dx, dz) in DIRV.items(): b.set(cx + dx * r_, ty + 2, cz + dz * r_, "minecraft:orange_stained_glass")
        b.cyl(cx, cz, r_ + 1.2, ty + 3, ty + 3, "minecraft:cut_sandstone"); b.cyl(cx, cz, r_ + 0.2, ty + 3, ty + 3, AIR)
        b.dome(cx, cz, ty + 3, r_ + 0.4, h=r_ + 2, s=rnd.choice(DOME_BLOCKS), tip="minecraft:gold_block")
        items.append("dome")
        skip_items = {(x, z) for x in range(cx - r_ - 1, cx + r_ + 2) for z in range(cz - r_ - 1, cz + r_ + 2)}
    for (r, y1, Fu) in roof_tops:
        area = (r[0] + 1, r[1] + 1, r[2] - 1, r[3] - 1)
        cells_blocked = Fu | (skip_items if y1 == ty else set())
        # shrink the area away from blocked cells (walls of the storey above, the dome)
        xs = [x for x in range(area[0], area[2] + 1) if all((x, z) not in cells_blocked for z in range(area[1], area[3] + 1))]
        zs = [z for z in range(area[1], area[3] + 1) if all((x, z) not in cells_blocked for x in range(area[0], area[2] + 1))]
        if len(xs) >= len(zs) * 0 + 3 and xs and (max(xs) - min(xs) + 1) * (area[3] - area[1] + 1) >= (max(zs) - min(zs) + 1 if zs else 0) * (area[2] - area[0] + 1):
            a2 = (min(xs), area[1], max(xs), area[3])
        elif zs: a2 = (area[0], min(zs), area[2], max(zs))
        else: continue
        items += _roof_items(b, a2, y1, rnd, n=2 if "dome" not in items or y1 != ty else 1)
    # arched portal with a striped awning over the door
    cols = rnd.sample(AWNING_COLORS, 2)
    a = (1, 0) if door in ("north", "south") else (0, 1)
    awning(b, (dcell[0] - a[0] * 2, dcell[1] - a[1] * 2, dcell[0] + a[0] * 2, dcell[1] + a[1] * 2, door), y + 4, colors=cols, out=2)
    ox, oz = DIRV[door]
    b.set(dcell[0] + ox, y, dcell[1] + oz, "minecraft:smooth_sandstone")
    # stairs up the outside of a one-storey wing (or the main block) to its roof terrace
    if outside_stair:
        cand = [(i, r) for i, r in enumerate(rects) if fr[i] == 1 and i > 0] or [(0, main)]
        i, r = cand[0]
        ry = y + fr[i] * FH
        for s in (CW[door], CCW[door], back):
            run = [rn for rn in outline([r[:4]])[2] if rn["side"] == s]
            if not run: continue
            cells = run[0]["cells"]
            ox2, oz2 = DIRV[s]
            n_ = ry - y
            if len(cells) < n_ + 2: continue
            outside = [(c[0] + ox2, c[1] + oz2) for c in cells[1:n_ + 1]]
            if any(not _soft(b.get(cx_, y + 1, cz_)) for cx_, cz_ in outside) or any((cx_, cz_) in F0 for cx_, cz_ in outside): continue
            seq = outside if s in ("east", "south") else outside
            dirn = {(1, 0): "east", (-1, 0): "west", (0, 1): "south", (0, -1): "north"}[(seq[1][0] - seq[0][0], seq[1][1] - seq[0][1])]
            for k, (sx, sz) in enumerate(seq):
                for yy in range(y + 1, y + 1 + k): b.set(sx, yy, sz, "minecraft:smooth_sandstone")
                b.set(sx, y + 1 + k, sz, stairs("minecraft:smooth_sandstone_stairs", dirn))
                b.set(sx + ox2, y + 2 + k, sz + oz2, wall("minecraft:sandstone_wall")) if _soft(b.get(sx + ox2, y + 2 + k, sz + oz2)) else None
                for yy in range(y + 2 + k, y + 5 + k): b.set(sx, yy, sz, AIR) if _soft(b.get(sx, yy, sz)) else None
            # the landing: open the parapet where the stair arrives
            lx, lz = cells[n_ + 1] if n_ + 1 < len(cells) else cells[-1]
            last = seq[-1]
            gx, gz = last[0] - ox2, last[1] - oz2
            for yy in (ry + 1, ry + 2): b.set(gx, yy, gz, AIR)
            nx_, nz_ = last[0] + (last[0] - seq[-2][0]), last[1] + (last[1] - seq[-2][1])
            b.set(nx_, ry, nz_, "minecraft:smooth_sandstone"); foundation(b, [(nx_, nz_, nx_, nz_)], ry, "minecraft:smooth_sandstone", depth=ry - y + 1)
            for yy in (ry + 1, ry + 2, ry + 3): b.set(nx_, yy, nz_, AIR) if _soft(b.get(nx_, yy, nz_)) else None
            gx2, gz2 = nx_ - ox2, nz_ - oz2
            for yy in (ry + 1, ry + 2): b.set(gx2, yy, gz2, AIR)
            items.append("outside_stair")
            break
    if arcade_ or (arcade_ is None and rnd.random() < 0.4 and fr[0] >= 2):
        sides = [s for s in (CW[door], CCW[door], back) if _side_free(main, s, [r[:4] for r in rects[1:]], gap=3)]
        if sides:
            s = sides[0]
            L = (main[2] - main[0] + 1) if s in ("north", "south") else (main[3] - main[1] + 1)
            n = 2 + 4 * max(0, (L - 6) // 8)
            if 2 * n + 1 <= L:
                x_, z_ = {"north": ((main[0] + main[2]) // 2, main[1]), "south": ((main[0] + main[2]) // 2, main[3]),
                          "west": (main[0], (main[1] + main[3]) // 2), "east": (main[2], (main[1] + main[3]) // 2)}[s]
                arcade(b, x_, z_, s, y, n=n, h=4)
                Pa = _loc(x_, z_, s); ax_, az_ = Pa(0, 0)
                for yy in (y + 1, y + 2): b.set(ax_, yy, az_, AIR)
                items.append("arcade")
    return {"door": (dcell[0], y + 1, dcell[1], door), "outside": (dcell[0] + ox, y + 1, dcell[1] + oz), "floors": floors_y,
            "rooms": rooms, "rects": rects, "top": y + nf * FH + (5 if "dome" in items else 1), "y": y, "ladder": [], "addons": items, "plan": kind}


def japanese_house(b, x0, z0, w, d, floors=1, rnd=None, y=None, door="south", st="minecraft:deepslate_tile_stairs",
                   full="minecraft:deepslate_tiles", plan=None, garden=True):
    """Wano house (14d): a stone base wider than the house, the floor raised on it, a 2-wide engawa veranda on posts
    along the front under deep (2-block) eaves, a dark frame with white plaster and shoji screens, a pent roof between
    storeys, and an irimoya (hip-and-gable) roof with flared eaves, a full-block ridge with end ornaments.
    Returns the same dict as house2."""
    rnd = rnd or random.Random(x0 * 53 + z0 * 97)
    kind = plan or rnd.choice(("plain", "L", "plain"))
    rects = plan_rects(kind, x0, z0, w, d, rnd, front=door)
    y = site_y(b, rects) if y is None else y
    fr = [max(1, floors + r[4]) for r in rects]
    main = rects[0][:4]
    stone = ("minecraft:cobblestone", "minecraft:stone_bricks", "minecraft:tuff", "minecraft:mossy_cobblestone")
    # stone base 1 out round the house, the floor 1 above it
    for r in rects:
        g = _grow(r[:4], list(DIRV), 1)
        for x in range(g[0], g[2] + 1):
            for z in range(g[1], g[3] + 1): b.set(x, y + 1, z, mix(stone, x, y + 1, z, rough=0.6))
        foundation(b, [g], y + 1, "minecraft:cobblestone")
    yf = y + 2
    for r in rects: b.box(r[0], yf, r[1], r[2], yf, r[3], "minecraft:spruce_planks")
    F0, W0, runs0 = outline([r[:4] for r in rects if True])
    fronts = sorted((r for r in runs0 if r["side"] == door), key=lambda r: -len(r["cells"]))
    q = fronts[0]["cells"]
    dcell = q[len(q) // 2]
    floors_y, rooms = [], []
    nf = max(fr)
    for f in range(nf):
        rs = [r[:4] for i, r in enumerate(rects) if fr[i] > f]
        y0, y1 = yf + 1 + f * FH, yf + (f + 1) * FH
        F, W, runs = outline(rs, 3)
        _carve(b, F, W, y0, y1, "minecraft:spruce_planks")
        japanese_wall(b, rs, y0, y1, rnd, [(dcell[0], dcell[1], "door")] if f == 0 else [], shoji_sides=(door, CW[door]) if f == 0 else ())
        floors_y.append(y0); rooms.append(_rooms(rs, 1))
        if f < nf - 1: pent(b, rs, y1, st, out=2)
    # engawa: 2 wide along the front, slab deck level with the floor, posts at its edge up to the eave
    fr0 = fronts[0]; ox, oz = DIRV[door]
    span = fr0["cells"]
    top_y = yf + fr[0] * FH
    for i, (x, z) in enumerate(span):
        for v in (1, 2):
            ex, ez = x + ox * v, z + oz * v
            if any(r[0] <= ex <= r[2] and r[1] <= ez <= r[3] for r in rects): continue  # an L wing: keep its wall
            b.set(ex, yf, ez, slab("minecraft:spruce_slab", "top"))
            b.set(ex, yf - 1, ez, fence("dark_oak") if v == 2 and i % 3 == 0 else b.get(ex, yf - 1, ez) or AIR)
            for yy in range(yf + 1, yf + 3): b.set(ex, yy, ez, AIR)
        if i % 3 == 0 or i == len(span) - 1:
            px, pz = x + ox * 2, z + oz * 2
            if any(r[0] <= px <= r[2] and r[1] <= pz <= r[3] for r in rects): continue
            for yy in range(yf + 1, yf + FH): b.set(px, yy, pz, "minecraft:stripped_dark_oak_log[axis=y]")
    b.set(dcell[0] + ox * 3, yf - 1, dcell[1] + oz * 3, slab("minecraft:stone_brick_slab", "top"))
    b.set(dcell[0] + ox * 4, y, dcell[1] + oz * 4, "minecraft:stone_bricks")
    # roof: irimoya with deep flared eaves
    rr = [r[:4] + (fr[i] - fr[0],) for i, r in enumerate(rects)]
    top = roof(b, rr, ["irimoya"] + ["hip"] * (len(rects) - 1), st, full, top_y, overhang=2, curve="flare",
               gable=lambda x, yy, z: "minecraft:stripped_dark_oak_log[axis=y]" if (x + z) % 2 == 0 else "minecraft:white_terracotta",
               ridge=full, trim=False)
    R = b._roof
    # lift the four eave corners of the main roof one block (the flare)
    g = _grow(rects[0][:4], list(DIRV), 2)
    for (cx, cz) in ((g[0], g[1]), (g[2], g[1]), (g[0], g[3]), (g[2], g[3])):
        if (cx, cz) in R["Y"]:
            yy = R["Y"][(cx, cz)]
            dx = 1 if cx == g[0] else -1; dz = 1 if cz == g[1] else -1
            fx = "east" if dx > 0 else "west"
            b.set(cx, yy, cz, stairs(st, fx, "top"))
    # ridge end ornaments: a stair standing on each end of the ridge
    ridge = [c for c in roof_ridge(b) if R["own"][(c[0], c[2])] == 0 and c[1] == top]
    if ridge:
        along_x = (main[2] - main[0]) >= (main[3] - main[1])
        key = (lambda c: c[0]) if along_x else (lambda c: c[2])
        lo, hi = min(ridge, key=key), max(ridge, key=key)
        b.set(lo[0], lo[1] + 1, lo[2], stairs(st, "east" if along_x else "south"))
        b.set(hi[0], hi[1] + 1, hi[2], stairs(st, "west" if along_x else "north"))
    if garden:  # a stone lantern by the path and stepping stones to the engawa step
        P = _loc(dcell[0], dcell[1], door)
        lx, lz = P(-3, 5)
        if _solid(b.get(lx, y, lz)) or ground_y(b, lx, lz) == y:
            b.set(lx, y + 1, lz, wall("minecraft:stone_brick_wall")); b.set(lx, y + 2, lz, lantern())
            b.set(lx, y + 3, lz, slab("minecraft:stone_brick_slab"))
        for v in (5, 6, 7):
            sx, sz = P((v % 2) - 0, v)
            b.set(sx, y, sz, "minecraft:smooth_stone")
    return {"door": (dcell[0], yf + 1, dcell[1], door), "outside": (dcell[0] + ox, yf + 1, dcell[1] + oz), "floors": floors_y,
            "rooms": rooms, "rects": rects, "top": top + 1, "y": y, "ladder": [], "addons": ["engawa", "pent" if nf > 1 else "irimoya"], "plan": kind}


def venetian_house(b, x0, z0, w, d, floors=3, rnd=None, y=None, door="south", color=None, roof_kind="hip_low", plan="plain",
                   water=False, shop=None):
    """Water 7 house (14e): tall and narrow, a rusticated stone ground floor with a mossy waterline, pastel stucco above
    with stone quoins and floor bands, arched paired windows with flower boxes, a balcony on the main floor, an awning
    over a shop front or the door, a low hipped brick roof with a stone cornice and funnel chimneys.
    Returns the same dict as house2."""
    rnd = rnd or random.Random(x0 * 211 + z0 * 7)
    rects = plan_rects(plan, x0, z0, w, d, rnd, front=door)
    y = site_y(b, rects) if y is None else y
    fr = [max(1, floors + r[4]) for r in rects]
    main = rects[0][:4]
    color = color or rnd.choice(PASTELS)
    F0, W0, runs0 = outline([r[:4] for r in rects])
    fronts = sorted((r for r in runs0 if r["side"] == door), key=lambda r: -len(r["cells"]))
    pans = panels(fronts[0])
    pc = pans[len(pans) // 2] if pans else fronts[0]["cells"][1:-1]
    dcell = pc[0] if len(pc) <= 2 else pc[len(pc) // 2]
    foundation(b, [r[:4] for r in rects], y, "minecraft:stone_bricks")
    for r in rects: b.box(r[0], y, r[1], r[2], y, r[3], "minecraft:polished_andesite")
    floors_y, rooms = [], []
    nf = max(fr)
    for f in range(nf):
        rs = [r[:4] for i, r in enumerate(rects) if fr[i] > f]
        y0, y1 = y + 1 + f * FH, y + (f + 1) * FH
        F, W, runs = outline(rs, 3)
        _carve(b, F, W, y0, y1, "minecraft:dark_oak_planks")
        venetian_wall(b, rs, y0, y1, rnd, [(dcell[0], dcell[1], "door")] if f == 0 else [], stucco=color, level=f, water=water)
        if f == 1:  # a thin stone ledge under the main floor
            for (x, z), ds in W.items():
                for s in ds:
                    ex, ez = x + DIRV[s][0], z + DIRV[s][1]
                    b.fill_if(ex, y0 - 1, ez, slab("minecraft:polished_andesite_slab", "top"))
        floors_y.append(y0); rooms.append(_rooms(rs, 1))
    # ladder in a back corner
    back = OPP[door]
    lx, lz = (main[0] + 1, main[1] + 1 if back == "north" else main[3] - 1) if back in ("north", "south") else ((main[0] + 1 if back == "west" else main[2] - 1), main[1] + 1)
    lad = (lx, lz, y + 1, y + (fr[0] - 1) * FH, f"minecraft:ladder[facing={door},waterlogged=false]")
    for yy in range(lad[2], lad[3] + 1): b.set(lx, yy, lz, lad[4])
    if fr[0] > 1: back_ladder(b, lad, color)
    ytop = y + fr[0] * FH
    rr = [r[:4] + (fr[i] - fr[0],) for i, r in enumerate(rects)]
    top = roof(b, rr, roof_kind, "minecraft:brick_stairs", "minecraft:bricks", ytop, overhang=1, trim="minecraft:polished_andesite_stairs",
               gable=color, ridge="minecraft:mud_brick_slab", alt="minecraft:granite_stairs")
    # balcony on the main floor, centred on the front
    P = _loc(dcell[0], dcell[1], door)
    mid = ((main[0] + main[2]) // 2, main[3] if door == "south" else main[1]) if door in ("north", "south") else \
          (main[2] if door == "east" else main[0], (main[1] + main[3]) // 2)
    if nf >= 2:
        balcony(b, mid[0], mid[1], door, y + FH, w=3 if w < 7 else 5, out=1, rail=wall("minecraft:stone_brick_wall"), wood="dark_oak",
                floor="minecraft:polished_andesite")
    # awning over the door
    a = (1, 0) if door in ("north", "south") else (0, 1)
    cols = rnd.sample(AWNING_COLORS, 1) + ["white"]
    awning(b, (dcell[0] - a[0], dcell[1] - a[1], dcell[0] + a[0], dcell[1] + a[1], door), y + 3, colors=cols, out=2)
    ox, oz = DIRV[door]
    b.set(dcell[0] + ox, y, dcell[1] + oz, "minecraft:polished_andesite")
    # funnel chimneys from the attic floor through the roof
    R = b._roof
    cx, cz = (main[0] + 1 if rnd.random() < 0.5 else main[2] - 1), (main[1] + 1 if door == "south" else main[3] - 1)
    sy = R["Y"].get((cx, cz), ytop + 2)
    chimney(b, cx, cz, ytop + 1, sy + 1, "minecraft:bricks", cap="funnel")
    return {"door": (dcell[0], y + 1, dcell[1], door), "outside": (dcell[0] + ox, y + 1, dcell[1] + oz), "floors": floors_y,
            "rooms": rooms, "rects": rects, "top": top + 3, "y": y, "ladder": [lad] if fr[0] > 1 else [], "addons": ["balcony", "awning", "funnel"], "plan": plan}
