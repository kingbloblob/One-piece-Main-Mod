"""mcasian: East Asian (Chinese / Japanese) temple parts for mcbig.BigBuild.

    import sys; sys.path.insert(0, "<skill>/scripts")
    from mcbig import BigBuild
    import mcasian as A

Learned from a studied two-tier temple hall (references/techniques/east-asian-temple.md).
Coordinates: x east+, y up+, z south+. Long axis of a hall runs along x.
Stair `facing` = the direction the stair ASCENDS toward (same rule as mcparts).

Roofs     curved_roof (hip / gable / irimoya = hip-and-gable), concave profile, lifted corners
Timber    bay_positions, column_row, brackets, lattice_wall
Site      stone_platform, front_steps, stone_lantern
Recipe    temple_hall (platform + veranda hall + pent roof + upper storey + irimoya roof)
Palette   TEMPLE (roles -> block ids)
"""
import math

import numpy as np

TEMPLE = dict(
    roof="minecraft:deepslate_tiles", roof_stairs="minecraft:deepslate_tile_stairs",
    roof_alt="minecraft:deepslate_bricks", edge="minecraft:smooth_stone",
    ridge="minecraft:polished_blackstone_bricks", ridge_cap="minecraft:smooth_stone_slab[type=bottom]",
    ornament="minecraft:mangrove_planks", soffit="minecraft:spruce_planks",
    bracket="minecraft:stripped_spruce_log", bracket_stairs="minecraft:spruce_stairs",
    column="minecraft:stripped_mangrove_log", beam="minecraft:spruce_planks",
    panel="minecraft:white_wool", lattice="minecraft:spruce_planks", wall_low="minecraft:red_terracotta",
    floor="minecraft:spruce_planks", platform="minecraft:andesite",
    platform_mix=("minecraft:andesite", "minecraft:cobblestone", "minecraft:stone_bricks", "minecraft:stone"),
    platform_edge="minecraft:stone_bricks", step="minecraft:stone_brick_stairs",
    lantern="minecraft:stone_bricks", lantern_cap="minecraft:deepslate_tiles",
    lantern_light="minecraft:lantern")

# Measured bay rhythm of the studied facade: 8, 10, 12, 10, 8 (centre bay widest).
BAY_WEIGHTS = {1: [1], 3: [0.83, 1, 0.83], 5: [0.67, 0.83, 1, 0.83, 0.67],
               7: [0.6, 0.72, 0.86, 1, 0.86, 0.72, 0.6]}


def _stairs(base, facing, half="bottom"):
    return f"{base}[facing={facing},half={half}]"


# ---------------------------------------------------------------------- roof
def curved_roof(b, x1, z1, x2, z2, y, rise, style="irimoya", gable_inset=None, power=2.0,
                corner_lift=2, lift_run=None, max_y=None, pal=None, ridge=True, ornaments=True,
                gable_fill=None):
    """Concave East Asian roof over the eave rectangle [x1..x2] x [z1..z2] (long axis x).

    y: eave height; rise: ridge height above y. power > 1 makes the slope flat at the eaves
    and steep near the ridge (measured: ~2). corner_lift: how far the corners curl up
    (measured 1-2 at this size); lift_run: distance over which the curl fades (default
    ~depth/5). style: 'hip', 'gable' or 'irimoya' (hip skirt at the ends below a gable;
    gable_inset = distance from end eave to the gable wall, default ~depth/5.5).
    max_y clips the roof flat (a pent/skirt roof under an upper storey).
    Returns the integer height map (x2-x1+1, z2-z1+1)."""
    p = dict(TEMPLE, **(pal or {}))
    x1, x2 = sorted((x1, x2)); z1, z2 = sorted((z1, z2))
    nx, nz = x2 - x1 + 1, z2 - z1 + 1
    D = (nz - 1) / 2.0
    X = np.arange(nx)[:, None]
    Z = np.arange(nz)[None, :]
    dz = np.minimum(Z, nz - 1 - Z).astype(float) + 0 * X
    dx = np.minimum(X, nx - 1 - X).astype(float) + 0 * Z
    f = lambda d: rise * np.clip(d / max(D, 1), 0, 1) ** power
    hz = f(dz)
    if style == "gable":
        Hf = hz
        g = 0
    else:
        g = gable_inset if gable_inset is not None else (max(2, int(round(nz / 5.5))) if style == "irimoya" else 10 ** 6)
        hx = f(dx)
        Hf = np.where(dx >= g, hz, np.minimum(hz, hx))
    run = lift_run or max(3, nz // 5)
    lift = corner_lift * np.clip(1 - dx / run, 0, 1) ** 2 * np.clip(1 - dz / run, 0, 1) ** 2
    # also lift the whole eave line slightly toward the corners along each edge
    edge_lift = corner_lift * 0.5 * (np.clip(1 - dx / (run * 1.5), 0, 1) ** 2 * (dz < 1.5)
                                     + np.clip(1 - dz / (run * 1.5), 0, 1) ** 2 * (dx < 1.5))
    Ht = y + np.round(Hf + np.maximum(lift, edge_lift)).astype(int)
    if max_y is not None:
        Ht = np.minimum(Ht, max_y)
    # column bottoms: no gaps on steep parts
    pad = np.pad(Ht, 1, mode="edge")
    nmin = np.minimum.reduce([pad[:-2, 1:-1], pad[2:, 1:-1], pad[1:-1, :-2], pad[1:-1, 2:]])
    bottom = np.minimum(Ht, nmin + 1)
    for i in range(nx):
        for k in range(nz):
            xx, zz = x1 + i, z1 + k
            top, bot = int(Ht[i, k]), int(bottom[i, k])
            edge = dz[i, k] < 1 or dx[i, k] < 1
            hip_line = style != "gable" and dx[i, k] < g and abs(dx[i, k] - dz[i, k]) < 0.5
            blk = p["edge"] if (edge or hip_line) else (p["roof"] if (i + k) % 7 else p["roof_alt"])
            b.fill(xx, bot, zz, xx, top, zz, blk)
            b.set(xx, bot - 1, zz, p["soffit"])          # wooden underside (soffit)
    # stair steps where the uphill neighbour is exactly one higher (smooth slope look)
    dirs = [("east", 1, 0), ("west", -1, 0), ("south", 0, 1), ("north", 0, -1)]
    for i in range(nx):
        for k in range(nz):
            if max_y is not None and Ht[i, k] >= max_y:
                continue
            best = None
            for name, di, dk in dirs:
                ii, kk = i + di, k + dk
                if 0 <= ii < nx and 0 <= kk < nz and Ht[ii, kk] == Ht[i, k] + 1:
                    best = name
                    break
            if best:
                b.set(x1 + i, int(Ht[i, k]) + 1, z1 + k, _stairs(p["roof_stairs"], best))
    # gable triangles (irimoya / gable): fill the vertical face under the gable slope
    if style in ("irimoya", "gable") and g < nx // 2:
        for side in (g, nx - 1 - g):
            for k in range(nz):
                lo = int(y + f(float(g))) if style == "irimoya" else y
                top = int(Ht[side, k]) - 1
                if top > lo:
                    b.fill(x1 + side, lo, z1 + k, x1 + side, top, z1 + k, gable_fill or p["soffit"])
    # ridge: a raised crest along the top, ornaments (chiwei / shibi) at the ends
    if ridge and max_y is None:
        kmid = [int(math.floor(D)), int(math.ceil(D))]
        ytop = int(Ht[nx // 2, kmid[0]])
        xa = x1 + (g if style != "hip" else int(round(D)))
        xb = x2 - (g if style != "hip" else int(round(D)))
        for k in set(kmid):
            b.fill(xa, ytop + 1, z1 + k, xb, ytop + 1, z1 + k, p["ridge"])
            b.fill(xa, ytop + 2, z1 + k, xb, ytop + 2, z1 + k, p["ridge_cap"])
        if ornaments:
            for xe, out in ((xa, -1), (xb, 1)):
                for k in set(kmid):
                    b.fill(xe, ytop + 2, z1 + k, xe, ytop + 3, z1 + k, p["ornament"])
                    b.set(xe - out, ytop + 4, z1 + k, p["ornament"])        # horn curls inward
            b.fill(x1 + nx // 2, ytop + 2, z1 + kmid[0], x1 + nx // 2, ytop + 3, z1 + kmid[0], p["ornament"])
    return Ht


# -------------------------------------------------------------------- timber
def bay_positions(start, end, bays=5):
    """Column positions from start to end with the measured rhythm (centre bay widest)."""
    w = BAY_WEIGHTS.get(bays) or [1] * bays
    total = end - start
    cum = np.r_[0, np.cumsum(w)] / sum(w) * total
    return [int(round(start + c)) for c in cum]


def column_row(b, positions, axis, other, y1, y2, pal=None, base="minecraft:stone_bricks"):
    """Round-feeling columns (1 block + stone base) at positions along `axis` ('x' or 'z')."""
    p = dict(TEMPLE, **(pal or {}))
    for c in positions:
        x, z = (c, other) if axis == "x" else (other, c)
        b.set(x, y1, z, base)
        b.fill(x, y1 + 1, z, x, y2, z, p["column"] + "[axis=y]")


def brackets(b, x, y, z, out_dir, steps=2, pal=None):
    """Stepped bracket set (dougong / tokyo) on a column top at (x, y, z), projecting
    `steps` blocks toward out_dir ('north','south','east','west') to carry the eave."""
    p = dict(TEMPLE, **(pal or {}))
    dx, dz = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}[out_dir]
    back = {"north": "south", "south": "north", "east": "west", "west": "east"}[out_dir]
    for s in range(steps + 1):
        b.set(x + dx * s, y + s, z + dz * s, p["bracket"] + ("[axis=y]" if s == 0 else ("[axis=x]" if dx else "[axis=z]")))
        if s:
            b.set(x + dx * s, y + s - 1, z + dz * s, _stairs(p["bracket_stairs"], back, "top"))


def lattice_wall(b, axis, a1, a2, other, y1, y2, pal=None, low=3):
    """Wall panel between columns: solid low part (`low` high), lattice above (white paper
    with a wooden grid, like the white-and-dark lattice bands of the studied hall)."""
    p = dict(TEMPLE, **(pal or {}))
    a1, a2 = sorted((a1, a2))
    for a in range(a1, a2 + 1):
        x, z = (a, other) if axis == "x" else (other, a)
        b.fill(x, y1, z, x, min(y1 + low - 1, y2), z, p["wall_low"])
        for yy in range(y1 + low, y2 + 1):
            u, v = a - a1, yy - (y1 + low)
            grid = (u % 3 == 0) or (v % 3 == 0) or yy == y2
            b.set(x, yy, z, p["lattice"] if grid else p["panel"])


# ---------------------------------------------------------------------- site
def stone_platform(b, x1, z1, x2, z2, y, height=3, pal=None, rng=None):
    """Raised stone base with a darker capping course (measured 3 high)."""
    p = dict(TEMPLE, **(pal or {}))
    b.mix(x1, y, z1, x2, y + height - 2, z2, list(p["platform_mix"]))
    b.walls(x1, y + height - 1, z1, x2, y + height - 1, z2, p["platform_edge"])
    b.fill(x1 + 1, y + height - 1, z1 + 1, x2 - 1, y + height - 1, z2 - 1, p["platform"])


def front_steps(b, x1, x2, z_edge, y_bottom, y_top, direction="north", pal=None):
    """Full-width flight from y_bottom up to the platform top at z_edge, descending away
    from the building toward `direction` (stairs ascend toward the building)."""
    p = dict(TEMPLE, **(pal or {}))
    up = {"north": "south", "south": "north"}[direction]
    sgn = -1 if direction == "north" else 1
    for i, yy in enumerate(range(y_top - 1, y_bottom - 1, -1)):
        z = z_edge + sgn * (i + 1)
        b.fill(x1, y_bottom, z, x2, yy - 1, z, p["platform"]) if yy - 1 >= y_bottom else None
        b.fill(x1, yy, z, x2, yy, z, _stairs(p["step"], up))
    for xs in (x1 - 1, x2 + 1):                                   # side cheeks
        b.fill(xs, y_bottom, z_edge + sgn, xs, y_top - 1, z_edge + sgn * (y_top - y_bottom), p["platform_edge"])


def stone_lantern(b, x, y, z, pal=None):
    """Stone lantern (toro), measured ~7 tall on its plinth: base, post, firebox with a
    light, wide cap (5x5 in the studied build), finial."""
    p = dict(TEMPLE, **(pal or {}))
    b.fill(x - 1, y, z - 1, x + 1, y, z + 1, p["lantern"])
    b.fill(x, y + 1, z, x, y + 2, z, "minecraft:stone_brick_wall")
    b.fill(x - 1, y + 3, z - 1, x + 1, y + 3, z + 1, "minecraft:stone_brick_slab[type=top]")
    b.set(x, y + 4, z, p["lantern_light"])
    for cx, cz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        b.set(x + cx, y + 4, z + cz, "minecraft:stone_brick_wall")
    b.fill(x - 2, y + 5, z - 2, x + 2, y + 5, z + 2, p["lantern_cap"])
    b.fill(x - 1, y + 6, z - 1, x + 1, y + 6, z + 1, "minecraft:deepslate_tile_slab[type=bottom]")
    b.set(x, y + 6, z, p["lantern_cap"])
    b.set(x, y + 7, z, "minecraft:stone_button[face=floor]")


# -------------------------------------------------------------------- recipe
def temple_hall(b, x0, y0, z0, w=43, d=23, bays=5, two_storey=True, pal=None, lanterns=True):
    """Full two-tier hall (proportions of the studied temple, scaled from the hall size).

    (x0, y0, z0) = north-west corner of the PLATFORM at ground level. w x d = enclosed hall
    (measured 43 x 23). Everything else derives from it:
      platform 3 high, veranda columns 3-4 outside the walls, ground storey 10 high,
      lower eave overhang ~6 past the veranda, upper storey inset 4-6 and 8 high,
      upper eave overhang ~ upper storey height, irimoya rise ~0.55 x half depth."""
    p = dict(TEMPLE, **(pal or {}))
    s = d / 23.0                                   # scale factor vs the studied hall
    ver = max(2, round(4 * s))                     # veranda margin
    ov1 = max(3, round(6 * s))                     # lower eave overhang past veranda
    ph = 3 if s > 0.6 else 2                       # platform height
    h1 = max(5, round(10 * s))                     # ground storey wall height
    pm = ver + ov1 - 1                             # platform reaches nearly to the eave drip line
    # footprint coordinates
    hx1, hz1 = x0 + pm + ver, z0 + pm + ver + 2    # +2 leaves room for the front steps
    hx2, hz2 = hx1 + w - 1, hz1 + d - 1
    vx1, vz1, vx2, vz2 = hx1 - ver, hz1 - ver, hx2 + ver, hz2 + ver
    px1, pz1, px2, pz2 = vx1 - pm + ver - 1, vz1 - pm + ver - 1, vx2 + pm - ver + 1, vz2 + pm - ver + 1
    stone_platform(b, px1, pz1, px2, pz2, y0, ph, p)
    yf = y0 + ph                                   # floor level
    b.fill(vx1, yf - 1, vz1, vx2, yf - 1, vz2, p["floor"])
    xs = bay_positions(hx1, hx2, bays)
    ctr = (xs[bays // 2], xs[bays // 2 + 1])
    front_steps(b, ctr[0], ctr[1], pz1, y0 - 0, yf, "north", p)
    front_steps(b, ctr[0], ctr[1], pz2, y0 - 0, yf, "south", p)
    # walls with columns, lattice between, open centre doors
    yt = yf + h1 - 1
    for z in (hz1, hz2):
        column_row(b, xs, "x", z, yf, yt, p)
        for a, c in zip(xs, xs[1:]):
            lattice_wall(b, "x", a + 1, c - 1, z, yf, yt - 1, p, low=max(2, round(3 * s)))
        b.fill(ctr[0] + 1, yf, z, ctr[1] - 1, yf + max(3, round(h1 * 0.6)), z, "minecraft:air")
    zs = bay_positions(hz1, hz2, 3)
    for x in (hx1, hx2):
        column_row(b, zs, "z", x, yf, yt, p)
        for a, c in zip(zs, zs[1:]):
            lattice_wall(b, "z", a + 1, c - 1, x, yf, yt - 1, p, low=max(2, round(3 * s)))
    b.walls(hx1, yt, hz1, hx2, yt, hz2, p["beam"])
    # veranda column ring + brackets
    vxs = [vx1] + xs + [vx2]
    for z, out in ((vz1, "north"), (vz2, "south")):
        column_row(b, vxs, "x", z, yf, yt, p)
        for c in vxs:
            brackets(b, c, yt + 1, z, out, steps=2, pal=p)
    vzs = [vz1] + zs + [vz2]
    for x, out in ((vx1, "west"), (vx2, "east")):
        column_row(b, vzs, "z", x, yf, yt, p)
        for c in vzs[1:-1]:
            brackets(b, x, yt + 1, c, out, steps=2, pal=p)
    b.walls(vx1, yt + 1, vz1, vx2, yt + 1, vz2, p["beam"])
    b.fill(vx1, yt + 2, vz1, vx2, yt + 2, vz2, p["soffit"])
    ye1 = yt + 3                                    # lower eave height
    ex1, ez1, ex2, ez2 = vx1 - ov1, vz1 - ov1, vx2 + ov1, vz2 + ov1
    top = {"lower_eave": ye1, "floor": yf}
    if two_storey:
        ins = max(2, round(5 * s))
        h2 = max(4, round(8 * s))
        ux1, uz1, ux2, uz2 = hx1 + ins, hz1 + max(1, round(2 * s)), hx2 - ins, hz2 - max(1, round(2 * s))
        yu = ye1 + max(2, round(4 * s))              # upper floor sits above the pent roof
        curved_roof(b, ex1, ez1, ex2, ez2, ye1, rise=(ez2 - ez1) * 0.4, style="hip", power=1.6,
                    corner_lift=max(1, round(1.5 * s)), max_y=yu - 1, pal=p, ridge=False)
        b.fill(ux1, yu - 1, uz1, ux2, yu - 1, uz2, p["floor"])
        uxs = bay_positions(ux1, ux2, bays)
        yut = yu + h2 - 1
        for z in (uz1, uz2):
            column_row(b, uxs, "x", z, yu, yut, p)
            for a, c in zip(uxs, uxs[1:]):
                lattice_wall(b, "x", a + 1, c - 1, z, yu, yut - 1, p, low=1)
        for x in (ux1, ux2):
            column_row(b, [uz1, uz2], "z", x, yu, yut, p)
            lattice_wall(b, "z", uz1 + 1, uz2 - 1, x, yu, yut - 1, p, low=1)
        b.walls(ux1, yut, uz1, ux2, yut, uz2, p["beam"])
        b.fill(ux1, yut + 1, uz1, ux2, yut + 1, uz2, p["soffit"])
        ov2 = h2 + 1                                 # measured: overhang ~ upper storey height
        rx1, rz1, rx2, rz2 = ux1 - ov2, uz1 - ov2 - 1, ux2 + ov2, uz2 + ov2 + 1
        Ht = curved_roof(b, rx1, rz1, rx2, rz2, yut + 2, rise=round((rz2 - rz1) / 2 * 0.55),
                         style="irimoya", power=2.0, corner_lift=max(1, round(2 * s)), pal=p)
        top.update(upper_floor=yu, ridge=int(Ht.max()))
    else:
        Ht = curved_roof(b, ex1, ez1, ex2, ez2, ye1, rise=round((ez2 - ez1) / 2 * 0.55),
                         style="irimoya", corner_lift=max(1, round(2 * s)), pal=p)
        top.update(ridge=int(Ht.max()))
    if lanterns:   # flank the steps on open ground, clear of the eaves (they collide at small scale)
        for lz in (pz1 - ph - 2, pz2 + ph + 2):
            for lx in (ctr[0] - 3, ctr[1] + 3):
                stone_lantern(b, lx, y0, lz, p)
    top.update(platform=(px1, pz1, px2, pz2), hall=(hx1, hz1, hx2, hz2))
    return top
