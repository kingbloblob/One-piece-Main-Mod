"""mcparts: reusable architectural parts for mcbig.BigBuild.

    import sys; sys.path.insert(0, "<skill>/scripts")
    from mcbig import BigBuild
    import mcparts as P

Every function takes the BigBuild `b` first and paints into it. Coordinates are
build-local integers (x east+, y up+, z south+). Stair `facing` = the direction the
stair ASCENDS toward (so a roof's north slope uses facing=south).

Roofs      gable_roof, hip_roof, cone_roof
Openings   arched_opening, arcade
Columns    colonnade
Stairs     square_spiral_stair, stair_run
Nature     tree, scatter_trees
Vehicles   ship
Surface    weather
Interiors  bsp_rooms, furnish_room, PropTracker, audit_props
Gothic     pointed_opening, square_spire, pinnacle, flying_buttress, ridge_cresting
Helpers    slab_of, family_blocks
"""
import math
from collections import Counter

import numpy as np

from mcbig import AIR_ID
from mcbuild import _norm, _id


# ------------------------------------------------------------------ helpers
def slab_of(stairs):
    """oak_stairs -> oak_slab (works for vanilla and for mod blocks named *_stairs)."""
    return _id(_norm(stairs)).replace("_stairs", "_slab")


def family_blocks(palette, block_id):
    """Sibling blocks of a modded block via palette.json 'family'/'kind' fields.
    Returns {kind: id} (e.g. 'stairs', 'slab', 'wall') plus 'block' = block_id."""
    fam = palette.blocks[block_id].get("family")
    out = {}
    for bid, info in palette.blocks.items():
        if info.get("family") == fam and bid != block_id:
            out[info.get("kind", "block")] = bid
    out["block"] = block_id
    return out


# -------------------------------------------------------------------- roofs
def gable_roof(b, x1, z1, x2, z2, y, stairs, ridge=None, ridge_axis="x",
               gable_fill=None, overhang=0, ends_overhang=0):
    """Two sloping sides meeting at a ridge. First stair layer sits at height y.
    ridge_axis 'x': ridge runs along x (slopes face north/south); 'z': along z.
    ridge: block for the odd-width ridge line (default: matching slab).
    gable_fill: block closing the triangular end walls. overhang: eave extension on the
    sloping sides; ends_overhang: extension past the gable ends."""
    x1, x2 = sorted((x1, x2)); z1, z2 = sorted((z1, z2))
    sid = _id(_norm(stairs))
    ridge = ridge or slab_of(sid) + "[type=bottom]"
    if ridge_axis == "x":
        lo, hi = z1 - overhang, z2 + overhang
        e1, e2 = x1 - ends_overhang, x2 + ends_overhang
    else:
        lo, hi = x1 - overhang, x2 + overhang
        e1, e2 = z1 - ends_overhang, z2 + ends_overhang
    i = 0
    while lo + i <= hi - i:
        a, c, yy = lo + i, hi - i, y + i
        if ridge_axis == "x":
            if a == c:
                b.fill(e1, yy, a, e2, yy, a, ridge)
            else:
                b.fill(e1, yy, a, e2, yy, a, f"{sid}[facing=south,half=bottom]")
                b.fill(e1, yy, c, e2, yy, c, f"{sid}[facing=north,half=bottom]")
                if gable_fill and a + 1 <= c - 1:
                    for gx in (x1, x2):
                        b.fill(gx, yy, a + 1, gx, yy, c - 1, gable_fill)
        else:
            if a == c:
                b.fill(a, yy, e1, a, yy, e2, ridge)
            else:
                b.fill(a, yy, e1, a, yy, e2, f"{sid}[facing=east,half=bottom]")
                b.fill(c, yy, e1, c, yy, e2, f"{sid}[facing=west,half=bottom]")
                if gable_fill and a + 1 <= c - 1:
                    for gz in (z1, z2):
                        b.fill(a + 1, yy, gz, c - 1, yy, gz, gable_fill)
        i += 1
    return y + i - 1  # height of the ridge layer


def hip_roof(b, x1, z1, x2, z2, y, stairs, ridge=None, overhang=0):
    """Roof sloping on all four sides (pyramid when square). Corner stairs use the
    outer_left/outer_right shapes. Returns the top layer height."""
    x1, x2 = sorted((x1, x2)); z1, z2 = sorted((z1, z2))
    x1 -= overhang; z1 -= overhang; x2 += overhang; z2 += overhang
    sid = _id(_norm(stairs))
    ridge = ridge or slab_of(sid) + "[type=bottom]"
    i = 0
    while x1 + i <= x2 - i and z1 + i <= z2 - i:
        a, c = x1 + i, x2 - i
        d, e = z1 + i, z2 - i
        yy = y + i
        if a == c or d == e:
            b.fill(a, yy, d, c, yy, e, ridge)
        else:
            if a + 1 <= c - 1:
                b.fill(a + 1, yy, d, c - 1, yy, d, f"{sid}[facing=south,half=bottom]")
                b.fill(a + 1, yy, e, c - 1, yy, e, f"{sid}[facing=north,half=bottom]")
            if d + 1 <= e - 1:
                b.fill(a, yy, d + 1, a, yy, e - 1, f"{sid}[facing=east,half=bottom]")
                b.fill(c, yy, d + 1, c, yy, e - 1, f"{sid}[facing=west,half=bottom]")
            b.set(a, yy, d, f"{sid}[facing=south,half=bottom,shape=outer_left]")
            b.set(c, yy, d, f"{sid}[facing=south,half=bottom,shape=outer_right]")
            b.set(a, yy, e, f"{sid}[facing=north,half=bottom,shape=outer_right]")
            b.set(c, yy, e, f"{sid}[facing=north,half=bottom,shape=outer_left]")
        i += 1
    return y + i - 1


def cone_roof(b, cx, y, cz, r, height, block, hollow=True):
    """Round tower roof (blocky cone) with base radius r."""
    b.tapered_cylinder(cx, y, cz, y + height, r, 0, block, hollow=hollow, thickness=1)


# ----------------------------------------------------------------- openings
def arched_opening(b, axis, c, y0, w0, width, height, depth=1, trim=None,
                   trim_width=1, fill=None):
    """Carve a round-topped doorway/window through a wall (paint the wall first).

    axis 'x': the wall runs along x and is `depth` thick along z starting at z=w0;
              c is the centre x of the opening.
    axis 'z': the wall runs along z, thick along x from x=w0; c is the centre z.
    y0: bottom of the opening. width/height in blocks (height includes the round top).
    trim: block for a decorative ring around the opening. fill: block (glass, pane,
    door-less gate...) to fill the opening instead of leaving air."""
    r = (width - 1) / 2.0
    hs = height - 1 - r                       # height where the curve starts

    def inside(u, v, rad):
        return (np.abs(u) <= rad) & (v >= 0) & ((v <= hs) | (u * u + (v - hs) ** 2 <= (rad + 0.5) ** 2))

    rt = r + (trim_width if trim else 0)
    span = int(math.ceil(rt)) + 1
    top = int(math.ceil(hs + rt)) + 2
    cx_lo, cx_hi = int(math.floor(c - span)), int(math.ceil(c + span))

    def make(rad):
        if axis == "x":
            return lambda X, y, Z: inside(X - c, y - y0, rad)
        return lambda X, y, Z: inside(Z - c, y - y0, rad)

    if axis == "x":
        reg = (cx_lo, y0, w0, cx_hi, y0 + top, w0 + depth - 1)
    else:
        reg = (w0, y0, cx_lo, w0 + depth - 1, y0 + top, cx_hi)
    if trim:
        outer = make(rt); inner = make(r)
        b.fill_where(*reg, lambda X, y, Z: outer(X, y, Z) & ~inner(X, y, Z), trim)
    b.fill_where(*reg, make(r), fill or "minecraft:air")


def arcade(b, axis, start, end, y0, w0, bay_width, height, pier=2, depth=1, trim=None, fill=None):
    """A row of arched openings along a wall, from `start` to `end` along the wall axis.
    bay_width: opening width; pier: solid width between openings."""
    pos = start + pier + (bay_width - 1) / 2.0
    while pos + (bay_width - 1) / 2.0 + pier <= end + 1:
        arched_opening(b, axis, pos, y0, w0, bay_width, height, depth, trim, fill=fill)
        pos += bay_width + pier


# ------------------------------------------------------------------ columns
def colonnade(b, axis, start, end, other, y, spacing, height, column, base=None,
              capital=None, beam=None, girth=1):
    """Row of columns from `start` to `end` along `axis` at fixed `other` coordinate.
    Columns every `spacing` blocks (start and end included). beam: block for a lintel
    running along the top (one layer above the columns)."""
    n = max(1, round((end - start) / spacing))
    xs = sorted({int(round(start + k * (end - start) / n)) for k in range(n + 1)})
    for p in xs:
        if axis == "x":
            box = (p, y, other, p + girth - 1, y + height - 1, other + girth - 1)
        else:
            box = (other, y, p, other + girth - 1, y + height - 1, p + girth - 1)
        b.fill(*box, column)
        if base:
            b.fill(box[0], y, box[2], box[3], y, box[5], base)
        if capital:
            b.fill(box[0], y + height - 1, box[2], box[3], y + height - 1, box[5], capital)
    if beam:
        if axis == "x":
            b.fill(start, y + height, other, end + girth - 1, y + height, other + girth - 1, beam)
        else:
            b.fill(other, y + height, start, other + girth - 1, y + height, end + girth - 1, beam)


# ------------------------------------------------------------------- stairs
_DIRS = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}


def square_spiral_stair(b, x, y1, z, size, y2, stairs, core=None, clockwise=True,
                        support=None, headroom=3):
    """Spiral staircase winding around the perimeter of a size x size square whose
    north-west corner is (x, z), rising from y1 to y2 (one block per step).
    core: block for a central column. support: block to fill under each step (solid
    look). headroom: air carved above each step. Interior must be >= 3 wide."""
    x2, z2 = x + size - 1, z + size - 1
    cells = [(xx, z) for xx in range(x, x2)] + [(x2, zz) for zz in range(z, z2)] \
        + [(xx, z2) for xx in range(x2, x, -1)] + [(x, zz) for zz in range(z2, z, -1)]
    if not clockwise:
        cells = cells[::-1]
    n_steps = y2 - y1 + 1
    for n in range(n_steps):
        cx, cz = cells[n % len(cells)]
        b.fill(cx, y1 + n + 1, cz, cx, y1 + n + headroom, cz, "minecraft:air")
    for n in range(n_steps):
        cx, cz = cells[n % len(cells)]
        nx, nz = cells[(n + 1) % len(cells)]
        facing = {v: k for k, v in _DIRS.items()}[(nx - cx, nz - cz)]
        if support and n > 0:
            b.fill(cx, y1, cz, cx, y1 + n - 1, cz, support)
        b.set(cx, y1 + n, cz, f"{_id(_norm(stairs))}[facing={facing},half=bottom]")
    if core and size >= 3:
        b.fill(x + 1, y1, z + 1, x2 - 1, y2, z2 - 1, core)


def stair_run(b, x, y, z, length, width, direction, stairs, base_y=None, support=None):
    """Straight flight of stairs. First (lowest) step at (x, y, z); rises one block per
    step along `direction`; `width` extends toward +z (east/west runs) or +x
    (north/south runs). support fills the column under each step down to base_y."""
    dx, dz = _DIRS[direction]
    sid = _id(_norm(stairs))
    for i in range(length):
        px, pz, py = x + dx * i, z + dz * i, y + i
        if dx:
            box = (px, py, pz, px, py, pz + width - 1)
        else:
            box = (px, py, pz, px + width - 1, py, pz)
        b.fill(*box, f"{sid}[facing={direction},half=bottom]")
        if support and base_y is not None and py > base_y:
            b.fill(box[0], base_y, box[2], box[3], py - 1, box[5], support)


# ------------------------------------------------------------------- nature
_TREES = {
    "oak": ("minecraft:oak_log", "minecraft:oak_leaves", "round"),
    "birch": ("minecraft:birch_log", "minecraft:birch_leaves", "round"),
    "spruce": ("minecraft:spruce_log", "minecraft:spruce_leaves", "cone"),
    "jungle": ("minecraft:jungle_log", "minecraft:jungle_leaves", "round"),
    "acacia": ("minecraft:acacia_log", "minecraft:acacia_leaves", "flat"),
    "dark_oak": ("minecraft:dark_oak_log", "minecraft:dark_oak_leaves", "round"),
    "cherry": ("minecraft:cherry_log", "minecraft:cherry_leaves", "round"),
}


def tree(b, x, y, z, height=7, kind="oak", rng=None, only_empty=True):
    """Procedural tree with trunk base at (x, y, z). Leaves are persistent=true so they
    never decay. kind: oak, birch, spruce, jungle, acacia, dark_oak, cherry."""
    log, leaf, shape = _TREES[kind]
    leaf = leaf + "[persistent=true]"
    rng = rng or b.rng
    h = max(int(height), 3)
    if shape == "round":
        rc = max(2, h // 3 + 1)
        cy = y + h - 2
        def f(X, yy, Z):
            d2 = (X - x) ** 2 + ((yy - cy) * 1.25) ** 2 + (Z - z) ** 2
            keep = rng.random(np.broadcast(X, Z).shape) > 0.12
            return (d2 <= rc * rc + 1) & keep
        b.fill_where(x - rc, cy - rc, z - rc, x + rc, cy + rc + 1, z + rc, f, leaf, only_empty=only_empty)
    elif shape == "cone":
        top = y + h + 1
        rbase = max(2, h // 3 + 1)
        def f(X, yy, Z):
            t = (yy - (y + 2)) / max(top - (y + 2), 1)
            rr = rbase * (1 - t) + 0.4
            d2 = (X - x) ** 2 + (Z - z) ** 2
            keep = rng.random(np.broadcast(X, Z).shape) > 0.1
            return (d2 <= rr * rr + rr * 0.5) & keep & (((yy - y) % 2 == 0) | (d2 <= (rr - 1) ** 2 + 1))
        b.fill_where(x - rbase - 1, y + 2, z - rbase - 1, x + rbase + 1, top, z + rbase + 1, f, leaf, only_empty=only_empty)
    else:  # flat canopy
        rc = max(3, h // 2)
        def f(X, yy, Z):
            d2 = (X - x) ** 2 + (Z - z) ** 2
            keep = rng.random(np.broadcast(X, Z).shape) > 0.1
            return (d2 <= rc * rc) & keep
        b.fill_where(x - rc, y + h - 1, z - rc, x + rc, y + h, z + rc, f, leaf, only_empty=only_empty)
    b.fill(x, y, z, x, y + h - 1, z, log)


def scatter_trees(b, x1, z1, x2, z2, ground_y, count, kinds=("oak",), min_spacing=4,
                  height_range=(5, 9), seed=None, attempts=None):
    """Place up to `count` trees in a rectangle, at least min_spacing apart.
    ground_y: int, or function (x, z) -> y of the ground surface (the tree's base y)."""
    rng = np.random.default_rng(seed) if seed is not None else b.rng
    pts = []
    for _ in range(attempts or count * 10):
        if len(pts) >= count:
            break
        px = int(rng.integers(min(x1, x2), max(x1, x2) + 1))
        pz = int(rng.integers(min(z1, z2), max(z1, z2) + 1))
        if any((px - qx) ** 2 + (pz - qz) ** 2 < min_spacing ** 2 for qx, qz in pts):
            continue
        pts.append((px, pz))
        gy = ground_y(px, pz) if callable(ground_y) else ground_y
        tree(b, px, gy, pz, int(rng.integers(height_range[0], height_range[1] + 1)),
             kinds[int(rng.integers(len(kinds)))], rng)
    return pts


# ------------------------------------------------------------------- ships
def ship(b, x, y, z, length=25, beam=9, depth=5, masts=2, hull="minecraft:dark_oak_planks",
         deck="minecraft:spruce_planks", rail="minecraft:dark_oak_fence",
         mast="minecraft:stripped_spruce_log", sail="minecraft:white_wool",
         cabin=True, bowsprit=True):
    """Sailing ship pointing toward +x. (x, y, z) = stern end, keel bottom, centreline.
    Use stamp(..., rot=...) to point it elsewhere. Water line is about y + depth - 3."""
    hw_max = (beam - 1) // 2
    deck_y = y + depth - 2
    halfw = []
    for i in range(length):
        t = i / (length - 1)
        p = math.sqrt(max(0.0, 1 - abs(2 * t - 1) ** 3))
        h = hw_max * p
        if t < 0.5:
            h = max(h, hw_max * 0.6)          # blunt stern
        halfw.append(h)
    for i in range(length):
        for d in range(depth):
            frac = 0.45 + 0.55 * d / max(depth - 1, 1)
            hwd = int(round(halfw[i] * frac))
            yy = y + d
            if d == depth - 1:
                b.set(x + i, yy, z - hwd, hull); b.set(x + i, yy, z + hwd, hull)
                b.set(x + i, yy + 1, z - hwd, rail); b.set(x + i, yy + 1, z + hwd, rail)
            elif d == depth - 2:
                b.fill(x + i, yy, z - hwd, x + i, yy, z + hwd, hull)   # hull sides
                if hwd >= 1:
                    b.fill(x + i, yy, z - hwd + 1, x + i, yy, z + hwd - 1, deck)
            else:
                b.fill(x + i, yy, z - hwd, x + i, yy, z + hwd, hull)
                if d >= 1 and hwd >= 2:
                    b.fill(x + i, yy, z - hwd + 1, x + i, yy, z + hwd - 1, "minecraft:air")
    if cabin and length >= 15:
        cl = max(4, int(length * 0.22))
        hwc = max(1, int(round(halfw[cl // 2] * 0.85)) - 1)
        b.fill(x + 1, deck_y + 1, z - hwc, x + cl, deck_y + 3, z + hwc, hull)
        b.fill(x + 2, deck_y + 1, z - hwc + 1, x + cl - 1, deck_y + 3, z + hwc - 1, "minecraft:air")
        b.fill(x + 1, deck_y + 4, z - hwc, x + cl, deck_y + 4, z + hwc, deck)
        b.fill(x + cl, deck_y + 1, z, x + cl, deck_y + 2, z, "minecraft:air")  # door forward
    mast_pos = {1: [0.5], 2: [0.38, 0.68], 3: [0.3, 0.52, 0.74]}.get(masts, [0.5])
    mh = max(8, int(length * 0.75))
    for k, f in enumerate(mast_pos):
        mx = x + int(round(f * (length - 1)))
        top = deck_y + mh - (2 if k == len(mast_pos) - 1 and len(mast_pos) > 1 else 0)
        b.fill(mx, deck_y + 1, z, mx, top, z, mast)
        n_sails = 2 if top - deck_y > 12 else 1
        seg = (top - deck_y - 3) // n_sails
        for s in range(n_sails):
            y_top = top - s * seg - 1
            y_bot = y_top - seg + 2
            sw = hw_max + 2 - s
            b.fill(mx, y_top + 1, z - sw - 1, mx, y_top + 1, z + sw + 1, mast)
            for dz in range(-sw, sw + 1):
                bulge = 1 if abs(dz) <= sw // 2 else 0
                b.fill(mx + 1 + bulge, y_bot, z + dz, mx + 1 + bulge, y_top, z + dz, sail)
    if bowsprit:
        for k in range(4):
            b.set(x + length + k, deck_y + 1 + k // 2, z, mast)


# ---------------------------------------------------------------- weathering
def weather(b, x1, y1, z1, x2, y2, z2, rules, height_bias=0.0, seed=None):
    """Randomly age blocks in a region.

    rules: {"minecraft:stone_bricks": [("minecraft:mossy_stone_bricks", 0.15),
                                       ("minecraft:cracked_stone_bricks", 0.10)], ...}
    Each source block becomes the listed variants with those probabilities (they must
    sum to <= 1). height_bias > 0 concentrates the effect near the bottom of the region
    (damp moss, grime near water); 0 = uniform. Blocks with block states are matched by
    their exact string, so list them as they were painted."""
    x1, x2 = sorted((x1, x2)); y1, y2 = sorted((y1, y2)); z1, z2 = sorted((z1, z2))
    rng = np.random.default_rng(seed) if seed is not None else b.rng
    reg = b.get_region(x1, y1, z1, x2, y2, z2)
    out = reg.copy()
    ys = np.arange(y1, y2 + 1)[None, :, None]
    fall = (1.0 - (ys - y1) / max(y2 - y1, 1)) ** height_bias if height_bias else 1.0
    r = rng.random(reg.shape)
    for src, options in rules.items():
        sid = b.ids.get(_norm(src))
        if sid is None:
            continue
        m = reg == sid
        acc = 0.0
        for blk, p in options:
            pid = b.register(blk)
            sel = m & (r >= acc * fall) & (r < (acc + p) * fall)
            out[sel] = pid
            acc += p
    changed = out != reg
    if changed.any():
        b._write(x1, y1, z1, x2, y2, z2, out, mask=changed)
    return int(changed.sum())


STONE_AGING = {
    "minecraft:stone_bricks": [("minecraft:mossy_stone_bricks", 0.14), ("minecraft:cracked_stone_bricks", 0.10)],
    "minecraft:cobblestone": [("minecraft:mossy_cobblestone", 0.2)],
}


# ------------------------------------------------------------------- gothic
def pointed_opening(b, axis, c, y0, w0, width, height, depth=1, trim=None, fill=None):
    """Lancet (pointed-arch) window or door cut through a wall; same arguments as
    arched_opening. The top narrows by one block per layer to a single block."""
    r = (width - 1) / 2.0
    hs = height - 1 - int(math.ceil(r))

    def inside(u, v, rad):
        return (np.abs(u) <= rad) & (v >= 0) & ((v <= hs) | (np.abs(u) <= rad - (v - hs) + 0.01))

    rt = r + (1 if trim else 0)
    span = int(math.ceil(rt)) + 1
    top = int(math.ceil(hs + rt)) + 2

    def make(rad):
        if axis == "x":
            return lambda X, y, Z: inside(X - c, y - y0, rad)
        return lambda X, y, Z: inside(Z - c, y - y0, rad)

    lo, hi = int(math.floor(c - span)), int(math.ceil(c + span))
    reg = (lo, y0, w0, hi, y0 + top, w0 + depth - 1) if axis == "x" else (w0, y0, lo, w0 + depth - 1, y0 + top, hi)
    if trim:
        outer, inner = make(rt), make(r)
        b.fill_where(*reg, lambda X, y, Z: outer(X, y, Z) & ~inner(X, y, Z), trim)
    b.fill_where(*reg, make(r), fill or "minecraft:air")


def square_spire(b, cx, cz, y0, base_w, height, block, top_w=1, hollow=False):
    """Square tapering spire: width shrinks linearly from base_w to top_w over `height`
    layers (stepped by the block grid). Typical measured ratio: height about 3.4 x base
    width, e.g. base 15, height 51, narrowing by 1 block per side per ~10 layers at the top."""
    def f(rad_off):
        def g(X, y, Z):
            t = (y - y0) / max(height, 1)
            r = (base_w - 1) / 2 * (1 - t) + (top_w - 1) / 2 * t - rad_off
            return (np.abs(X - cx) <= r + 0.01) & (np.abs(Z - cz) <= r + 0.01)
        return g
    rr = base_w // 2 + 1
    b.fill_where(cx - rr, y0, cz - rr, cx + rr, y0 + height, cz + rr, f(0), block)
    if hollow:
        b.fill_where(cx - rr, y0, cz - rr, cx + rr, y0 + height - 3, cz + rr, f(1), "minecraft:air")


def pinnacle(b, x, y, z, height, block, cap="minecraft:iron_bars"):
    """Small pinnacle: 3x3 base two layers high, a 1-block shaft, and a bar finial."""
    b.fill(x - 1, y, z - 1, x + 1, y + 1, z + 1, block)
    if height > 2:
        b.fill(x, y + 2, z, x, y + height - 1, z, block)
    b.set(x, y + height, z, cap)
    b.set(x, y + height + 1, z, cap)


def flying_buttress(b, x_pier, y_pier, x_wall, y_wall, z, block, width=1, thickness=2):
    """Stepped diagonal strut along x from a pier top up to the clerestory wall."""
    n = abs(x_wall - x_pier)
    dx = 1 if x_wall >= x_pier else -1
    for i in range(n + 1):
        x = x_pier + dx * i
        y = int(round(y_pier + (y_wall - y_pier) * i / max(n, 1)))
        b.fill(x, y - thickness + 1, z, x, y, z + width - 1, block)


def ridge_cresting(b, x1, z1, x2, z2, y, axis="x", block="minecraft:iron_bars", period=2):
    """Decorative crest along a ridge: a bar at height y, with a taller bar every `period`
    blocks (measured roofs alternate +41/+44, a 3-block sawtooth every 2 blocks)."""
    if axis == "x":
        for i, x in enumerate(range(min(x1, x2), max(x1, x2) + 1)):
            b.set(x, y, z1, block)
            if i % period == 0:
                b.set(x, y + 1, z1, block)
    else:
        for i, z in enumerate(range(min(z1, z2), max(z1, z2) + 1)):
            b.set(x1, y, z, block)
            if i % period == 0:
                b.set(x1, y + 1, z, block)


# ---------------------------------------------------------------- interiors
def bsp_rooms(b, x1, z1, x2, z2, y, height, wall, min_room=5, seed=None,
              door_height=2, split_chance=0.85, max_room=12):
    """Divide a floor area into rooms with partition walls and doorways.

    (x1,z1)-(x2,z2) is the INTERIOR space inside the outer walls; y is the floor-surface
    level (first air layer); height is wall height. Partitions are `wall` blocks with a
    doorway gap that is never blocked by a later partition. Returns (rooms, doors):
    rooms = [(x1,z1,x2,z2)] interior rectangles, doors = [(x,z)] doorway cells.
    Every room is reachable from every other. Rooms are at least min_room wide; areas larger than max_room are always split."""
    rng = np.random.default_rng(seed) if seed is not None else b.rng
    rooms, doors = [], []
    air = "minecraft:air"

    def pick(lo, hi, forbidden):
        cand = [v for v in range(lo, hi + 1) if v not in forbidden]
        return int(cand[int(rng.integers(len(cand)))]) if cand else None

    def split(a1, c1, a2, c2, first=False):
        w, d = a2 - a1 + 1, c2 - c1 + 1
        can_x, can_z = w >= 2 * min_room + 1, d >= 2 * min_room + 1
        if not (can_x or can_z) or (not first and w <= max_room and d <= max_room
                                    and rng.random() > split_chance):
            rooms.append((a1, c1, a2, c2)); return
        if can_x and (not can_z or w >= d):
            forb = {dx for dx, dz in doors if dz in (c1 - 1, c2 + 1)}
            sx = pick(a1 + min_room, a2 - min_room, forb)
            if sx is None:
                rooms.append((a1, c1, a2, c2)); return
            b.fill(sx, y, c1, sx, y + height - 1, c2, wall)
            dz = int(rng.integers(c1 + 1, c2)) if c2 - c1 >= 2 else c1
            b.fill(sx, y, dz, sx, y + door_height - 1, dz, air)
            doors.append((sx, dz))
            split(a1, c1, sx - 1, c2); split(sx + 1, c1, a2, c2)
        elif can_z:
            forb = {dz for dx, dz in doors if dx in (a1 - 1, a2 + 1)}
            sz = pick(c1 + min_room, c2 - min_room, forb)
            if sz is None:
                rooms.append((a1, c1, a2, c2)); return
            b.fill(a1, y, sz, a2, y + height - 1, sz, wall)
            dx = int(rng.integers(a1 + 1, a2)) if a2 - a1 >= 2 else a1
            b.fill(dx, y, sz, dx, y + door_height - 1, sz, air)
            doors.append((dx, sz))
            split(a1, c1, a2, sz - 1); split(a1, sz + 1, a2, c2)
        else:
            rooms.append((a1, c1, a2, c2))

    split(x1, z1, x2, z2, first=True)
    return rooms, doors


class PropTracker:
    """Keeps variety across a whole building: counts how often each prop has been used,
    prefers rarely used ones, and enforces hard caps on novelty props (a building gets at
    most one brewing stand, one jukebox... and no cake at all). Create one per building
    and pass it to every furnish_room call."""
    LIMITS = {"brewing_stand": 1, "cake": 0, "cartography_table": 1, "fletching_table": 1,
              "stonecutter": 1, "jukebox": 1, "blast_furnace": 1, "cauldron": 2, "composter": 2,
              "loom": 2, "lectern": 2, "anvil": 2, "grindstone": 2, "enchanting_table": 1,
              "lodestone": 1, "campfire": 2, "note_block": 2}

    def __init__(self, seed=None):
        self.counts = Counter()
        self.rng = np.random.default_rng(seed)

    def allowed(self, name):
        lim = self.LIMITS.get(name)
        return lim is None or self.counts[name] < lim

    def pick(self, pool, exclude=()):
        opts = [p for p in pool if p not in exclude and self.allowed(p)]
        if not opts:
            return None
        w = np.array([1.0 / (1 + self.counts[p]) ** 2 for p in opts])
        return opts[int(self.rng.choice(len(opts), p=w / w.sum()))]

    def use(self, name):
        self.counts[name] += 1


_BULK = {"bookshelf", "barrel", "hay"}                      # may repeat (up to 3 per room)
_FULL = {"barrel", "crafting_table", "smithing_table", "cartography_table", "fletching_table",
         "stonecutter", "loom", "blast_furnace", "furnace", "smoker", "bookshelf", "hay",
         "composter", "chest", "jukebox", "dispenser", "dropper", "note_block", "lodestone"}                    # solid hosts an accent can sit on
_KIND = {
    "bedroom": dict(anchor=["bed"], secondary=["chest", "bookshelf", "loom", "barrel", "note_block"], table=0.0, density=0.07),
    "workshop": dict(anchor=["smithing_table"], secondary=["crafting_table", "anvil", "grindstone", "barrel", "chest", "stonecutter", "dispenser", "dropper", "lodestone"], table=0.9, density=0.10),
    "library": dict(anchor=["bookshelf"], secondary=["bookshelf", "bookshelf", "lectern", "chest", "cartography_table", "enchanting_table", "lodestone"], table=0.7, density=0.12),
    "kitchen": dict(anchor=["furnace"], secondary=["smoker", "barrel", "crafting_table", "cauldron", "composter", "hay", "campfire", "dispenser"], table=0.8, density=0.10),
    "storage": dict(anchor=["barrel"], secondary=["barrel", "chest", "hay", "barrel", "composter"], table=0.0, density=0.14),
    "living": dict(anchor=["bookshelf"], secondary=["chest", "loom", "jukebox", "barrel", "bookshelf", "campfire", "note_block"], table=1.0, density=0.06),
}
_STORY = ["cartography_table", "fletching_table", "stonecutter", "jukebox", "blast_furnace", "brewing_stand"]
_ACCENT = ["pot", "candle", "lantern_floor"]
_PLANTS = ["dandelion", "poppy", "blue_orchid", "azure_bluet", "red_tulip", "oxeye_daisy",
           "cornflower", "lily_of_the_valley", "fern"]
_RUGS = ["red", "brown", "gray", "light_gray", "green", "blue", "white", "orange", "cyan"]


def _render(name, f, rng):
    """Block string(s) for a prop name; returns (block, height_in_blocks)."""
    if name in ("bookshelf",):
        return "minecraft:bookshelf", 2
    simple = {"chest": f"minecraft:chest[facing={f}]", "barrel": "minecraft:barrel[facing=up]",
              "hay": "minecraft:hay_block[axis=y]", "crafting_table": "minecraft:crafting_table",
              "smithing_table": "minecraft:smithing_table", "cartography_table": "minecraft:cartography_table",
              "fletching_table": "minecraft:fletching_table", "stonecutter": f"minecraft:stonecutter[facing={f}]",
              "loom": f"minecraft:loom[facing={f}]", "blast_furnace": f"minecraft:blast_furnace[facing={f},lit=false]",
              "furnace": f"minecraft:furnace[facing={f},lit=false]", "smoker": f"minecraft:smoker[facing={f},lit=false]",
              "anvil": f"minecraft:anvil[facing={'east' if f in ('north', 'south') else 'north'}]",
              "grindstone": f"minecraft:grindstone[face=floor,facing={f}]", "lectern": f"minecraft:lectern[facing={f},has_book=false]",
              "jukebox": "minecraft:jukebox", "composter": "minecraft:composter", "cauldron": "minecraft:cauldron",
              "brewing_stand": "minecraft:brewing_stand",
              "campfire": f"minecraft:campfire[lit=false,facing={f}]", "dispenser": f"minecraft:dispenser[facing={f}]",
              "dropper": f"minecraft:dropper[facing={f}]", "note_block": "minecraft:note_block",
              "enchanting_table": "minecraft:enchanting_table", "lodestone": "minecraft:lodestone"}
    return simple[name], 1


_VIGS = {
    "living": ["seating", "pedestal", "shelf_row", "seating", "counter_island"],
    "bedroom": ["seating", "shelf_row", "storage_stack", "pedestal"],
    "workshop": ["workbench", "counter_island", "storage_stack", "shelf_row", "workbench"],
    "library": ["shelf_row", "seating", "pedestal", "shelf_row"],
    "kitchen": ["counter_island", "storage_stack", "seating", "counter_island"],
    "storage": ["storage_stack", "shelf_row", "counter_island", "storage_stack"],
}
_FULL |= {"counter", "pedestal"}


def _zone_points(x1, z1, x2, z2, rng, cell=8):
    """One jittered point per ~cell x cell zone, shuffled."""
    W, D = x2 - x1 + 1, z2 - z1 + 1
    cols, rows = max(1, W // cell), max(1, D // cell)
    pts = []
    for i in range(cols):
        for j in range(rows):
            ax, bx = x1 + i * W // cols, x1 + (i + 1) * W // cols - 1
            az, bz = z1 + j * D // rows, z1 + (j + 1) * D // rows - 1
            pts.append((int(rng.integers(ax + 1, max(ax + 2, bx))), int(rng.integers(az + 1, max(az + 2, bz)))))
    rng.shuffle(pts)
    return pts


def furnish_room(b, room, y, kind="living", height=4, seed=None, doors=(), wood="oak",
                 tracker=None, large_room=17):
    """Furnish one room so it looks lived in, never spammed (and never empty).

    Every room: one anchor piece, a small budget of secondary pieces (no repeats except
    bookshelves/barrels/hay, max 3), spacing so props never touch, intentional empty wall
    stretches, at most two small accents (small rooms), accents placed ON solid props or the
    floor, an occasional single "story" prop (limited per building by `tracker`), varied rug
    colours, and hanging lanterns at random spots.

    LARGE rooms (longer side > large_room, default 17) additionally get: the room split into
    ~8x8 zones, each with its own vignette (seating group, counter island, shelf unit,
    workbench, storage stack, pedestal) that differs from its neighbours, a few zones left
    empty on purpose, more accents/story props/rugs, several lights (some chandeliers) and,
    in very big halls, free-standing pillars. Pass one PropTracker per building.
    kind: bedroom, workshop, library, kitchen, storage, living.
    y = floor-surface level (first air layer). Make a ceiling at y+height."""
    rng = np.random.default_rng(seed) if seed is not None else b.rng
    tracker = tracker or PropTracker(seed)
    spec = _KIND.get(kind, _KIND["living"])
    x1, z1, x2, z2 = room
    W, D = x2 - x1 + 1, z2 - z1 + 1
    area = W * D
    is_large = max(W, D) > large_room
    cells = [(x, z) for x in range(x1, x2 + 1) for z in range(z1, z2 + 1)]
    reserved = {(dx + i, dz + j) for dx, dz in doors for i in (-1, 0, 1) for j in (-1, 0, 1)}
    free = {c for c in cells if c not in reserved}
    edge = [c for c in cells if c[0] in (x1, x2) or c[1] in (z1, z2)]
    blocked, placed = set(), []                         # placed: (name, x, z)

    def inward(x, z):
        return "south" if z == z1 else "north" if z == z2 else "east" if x == x1 else "west"

    def claim(c, r=1):
        free.discard(c)
        for i in range(-r, r + 1):
            for j in range(-r, r + 1):
                blocked.add((c[0] + i, c[1] + j))

    def ok(cs):
        return all(c in free and c not in blocked for c in cs)

    allow_room = 2 + (area // 150 if is_large else 0)

    def put(name, c, f=None):
        x, z = c
        f = f or inward(x, z)
        if name not in _BULK and name != "bed":
            if sum(1 for q in placed if q[0] == name) >= min(allow_room, 3 if name != 'chest' else 2):
                return False
            if any(q[0] == name and max(abs(q[1] - x), abs(q[2] - z)) <= 2 for q in placed):
                return False
        if name == "bed":
            hx, hz = {"south": (0, 1), "north": (0, -1), "east": (1, 0), "west": (-1, 0)}[f]
            if (x + hx, z + hz) not in free:
                return False
            col = ["red", "white", "blue", "brown", "green"][int(rng.integers(5))]
            b.set(x, y, z, f"minecraft:{col}_bed[facing={f},part=foot]")
            b.set(x + hx, y, z + hz, f"minecraft:{col}_bed[facing={f},part=head]")
            claim((x + hx, z + hz)); claim(c)
        else:
            blk, h = _render(name, f, rng)
            b.set(x, y, z, blk)
            if h == 2 and height >= 4:
                b.set(x, y + 1, z, blk)
            claim(c)
        placed.append((name, x, z))
        tracker.use(name)
        return True

    def spot(name=None):
        opts = [c for c in edge if c in free and c not in blocked]
        if name and name not in _BULK:
            opts = [c for c in opts if not any(q[0] == name and max(abs(q[1] - c[0]), abs(q[2] - c[1])) <= 2 for q in placed)]
        return opts[int(rng.integers(len(opts)))] if opts else None

    # ---- anchor + secondary props (budget scales with room area)
    for nm in spec["anchor"]:
        c = spot()
        if c:
            put(nm, c)
    cap = min(6 + area // 40, 22) if is_large else 6
    n_second = int(np.clip(round(area * spec["density"]), 1, cap))
    picked = set()
    for _ in range(n_second):
        excl = {p for p in picked if p not in _BULK} | {p for p in picked if sum(1 for q in placed if q[0] == p) >= 3}
        nm = tracker.pick(spec["secondary"], exclude=excl)
        c = spot(nm)
        if nm and c and rng.random() < 0.85:
            if put(nm, c):
                picked.add(nm)
    for _ in range(1 + (area // 150 if is_large else 0)):             # unique story prop(s)
        if rng.random() < 0.5:
            nm = tracker.pick(_STORY)
            c = spot(nm)
            if nm and c:
                put(nm, c)
    # ---- one low table with chairs for rooms that suit one
    inner = [c for c in free if x1 < c[0] < x2 and z1 < c[1] < z2 and c not in blocked]
    if inner and rng.random() < spec["table"] and area >= 24:
        tx, tz = inner[int(rng.integers(len(inner)))]
        b.set(tx, y, tz, f"minecraft:{wood}_fence")
        b.set(tx, y + 1, tz, f"minecraft:{wood}_slab[type=bottom]")
        claim((tx, tz), 1)
        sides = [(1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")]
        rng.shuffle(sides)
        for dx, dz, face in sides[:int(rng.integers(0, 3))]:
            if (tx + dx, tz + dz) in free:
                b.set(tx + dx, y, tz + dz, f"minecraft:{wood}_stairs[facing={face},half=bottom]")
                free.discard((tx + dx, tz + dz))

    # ---- LARGE rooms: zoned vignettes so the middle never feels empty
    def vignette(name, cx, cz):
        if name == "seating":
            if not ok([(cx, cz)]):
                return False
            cs = [(cx + i, cz + j) for i in (-1, 0, 1) for j in (-1, 0, 1)]
            rugc = tracker.pick([f"rug_{c}" for c in _RUGS])
            if rugc and ok(cs):
                b.fill(cx - 1, y, cz - 1, cx + 1, y, cz + 1, f"minecraft:{rugc[4:]}_carpet")
                tracker.use(rugc); placed.append(("rug", cx, cz))
            b.set(cx, y, cz, f"minecraft:{wood}_fence")
            b.set(cx, y + 1, cz, f"minecraft:{wood}_slab[type=bottom]")
            sides = [(1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")]
            rng.shuffle(sides)
            for dx, dz, face in sides[:int(rng.integers(2, 4))]:
                if (cx + dx, cz + dz) in free:
                    b.set(cx + dx, y, cz + dz, f"minecraft:{wood}_stairs[facing={face},half=bottom]")
            if not any(q[0] == "rug" and q[1] == cx and q[2] == cz for q in placed):
                for dx, dz in ((2, 0), (-2, 0), (0, 2), (0, -2)):
                    if (cx + dx, cz + dz) in free and (cx + dx, cz + dz) not in blocked:
                        b.set(cx + dx, y, cz + dz, f"minecraft:potted_{_PLANTS[int(rng.integers(len(_PLANTS)))]}")
                        placed.append(("potted", cx + dx, cz + dz)); free.discard((cx + dx, cz + dz))
                        break
            for c in cs:
                claim(c, 0)
            claim((cx, cz), 2)
            return True
        if name == "counter_island":
            horiz = bool(rng.integers(2))
            n = int(rng.integers(2, 5))
            cs = [(cx + (i if horiz else 0), cz + (0 if horiz else i)) for i in range(n)]
            if not ok(cs):
                return False
            for c in cs:
                b.set(c[0], y, c[1], f"minecraft:{wood}_planks")
                placed.append(("counter", c[0], c[1])); claim(c, 1)
            return True
        if name == "shelf_row":
            horiz = bool(rng.integers(2))
            n = int(rng.integers(3, 5))
            cs = [(cx + (i if horiz else j), cz + (j if horiz else i)) for i in range(n) for j in range(2)]
            if not ok(cs):
                return False
            for c in cs:
                blk = "minecraft:barrel[facing=up]" if kind == "storage" else "minecraft:bookshelf"
                b.set(c[0], y, c[1], blk)
                if height >= 4:
                    b.set(c[0], y + 1, c[1], blk)
                placed.append(("barrel" if kind == "storage" else "bookshelf", c[0], c[1]))
                claim(c, 1)
            return True
        if name == "workbench":
            horiz = bool(rng.integers(2))
            names = ["smithing_table", "anvil", "grindstone", "crafting_table", "stonecutter"]
            rng.shuffle(names)
            cs = [(cx + (i * 2 if horiz else 0), cz + (0 if horiz else i * 2)) for i in range(3)]
            if not ok(cs):
                return False
            f = ["north", "south", "east", "west"][int(rng.integers(4))]
            for c, nm in zip(cs, names):
                if tracker.allowed(nm):
                    put(nm, c, f)
            return True
        if name == "storage_stack":
            cs = [(cx, cz), (cx + 1, cz), (cx, cz + 1), (cx + 1, cz + 1)]
            if not ok(cs):
                return False
            opts = []
            for _ in range(4):
                nm = tracker.pick(["barrel", "chest", "hay", "composter", "barrel", "hay"],
                                  exclude={o for o in opts if o not in _BULK})
                opts.append(nm or "barrel")
            for c, nm in zip(cs, opts):
                put(nm, c, ["north", "south", "east", "west"][int(rng.integers(4))])
            if "barrel" in opts:
                c = cs[opts.index("barrel")]
                b.set(c[0], y + 1, c[1], "minecraft:barrel[facing=up]")
            return True
        if name == "pedestal":
            if not ok([(cx, cz)]):
                return False
            b.set(cx, y, cz, f"minecraft:stripped_{wood}_log[axis=y]")
            b.set(cx, y + 1, cz, f"minecraft:stripped_{wood}_log[axis=y]")
            placed.append(("pedestal", cx, cz)); claim((cx, cz), 2)
            return True
        return False

    if is_large:
        pts = _zone_points(x1, z1, x2, z2, rng, cell=8 if area < 400 else 6)
        n_v = min(len(pts), int(np.clip(area // 35, 2, 40)))
        pool = [f"vig_{n}" for n in _VIGS.get(kind, _VIGS["living"])]
        for (cx, cz) in pts[:n_v]:
            if rng.random() < 0.10:                      # leave a few zones empty on purpose
                continue
            for attempt in range(5):                     # jitter and retry if the spot is taken
                v = tracker.pick(pool)
                jx, jz = cx + int(rng.integers(-2, 3)), cz + int(rng.integers(-2, 3))
                if v and vignette(v[4:], jx, jz):
                    tracker.use(v)
                    break
        # fill any 6x6 patch that is still bare (most of them), keeping some calm space
        for pi in range((W + 5) // 6):
            for pj in range((D + 5) // 6):
                if any((q[1] - x1) // 6 == pi and (q[2] - z1) // 6 == pj for q in placed):
                    continue
                if rng.random() < 0.2:
                    continue
                cand = [c for c in free if (c[0] - x1) // 6 == pi and (c[1] - z1) // 6 == pj and c not in blocked]
                rng.shuffle(cand)
                for c in cand[:6]:
                    v = tracker.pick(["vig_pedestal", "vig_storage_stack", "vig_seating", "vig_counter_island"])
                    if v and vignette(v[4:], c[0], c[1]):
                        tracker.use(v)
                        break
        if max(W, D) > 26:                               # free-standing pillars in grand halls
            for _ in range(area // 150):
                c = (int(rng.integers(x1 + 2, x2 - 1)), int(rng.integers(z1 + 2, z2 - 1)))
                if ok([c]):
                    b.fill(c[0], y, c[1], c[0], y + height - 1, c[1], f"minecraft:stripped_{wood}_log[axis=y]")
                    claim(c, 3)

    # ---- accents: small rooms 0-2, large rooms scale with area; each on a solid prop or floor
    hosts = [p for p in placed if p[0] in _FULL]
    used_acc = Counter()
    acc_pos = []                                       # (name, x, z) of accents already set
    n_acc = int(rng.integers(2, 3 + area // 80)) if is_large else int(rng.integers(0, 3))
    for _ in range(n_acc):
        nm = tracker.pick(_ACCENT, exclude={k for k, v in used_acc.items() if v >= (2 if is_large else 1)})
        if not nm:
            break
        if nm == "pot":
            blk = f"minecraft:potted_{_PLANTS[int(rng.integers(len(_PLANTS)))]}"
        elif nm == "candle":
            blk = f"minecraft:candle[candles={int(rng.integers(1, 4))},lit=false]"
        else:
            blk = "minecraft:lantern[hanging=false]"
        far = [h for h in hosts if all(not (a_[0] == nm and max(abs(a_[1] - h[1]), abs(a_[2] - h[2])) <= 3) for a_ in acc_pos)]
        if far:
            h = far[int(rng.integers(len(far)))]
            hosts.remove(h)
            b.set(h[1], y + (2 if h[0] in ("bookshelf", "pedestal") and height >= 4 else 1), h[2], blk)
            acc_pos.append((nm, h[1], h[2]))
        else:
            fl = [c for c in edge if c in free and c not in blocked and
                  all(not (a_[0] == nm and max(abs(a_[1] - c[0]), abs(a_[2] - c[1])) <= 3) for a_ in acc_pos)]
            if not fl:
                continue
            c = fl[int(rng.integers(len(fl)))]
            b.set(c[0], y, c[1], blk); claim(c)
            acc_pos.append((nm, c[0], c[1]))
        used_acc[nm] += 1; tracker.use(nm)
    # ---- rugs (small rooms: at most one; large rooms: seating groups already add some)
    if kind in ("living", "bedroom", "library") and area >= 24:
        for _ in range(1 + (area // 150 if is_large else 0)):
            col = tracker.pick([f"rug_{c}" for c in _RUGS])
            w, d = (int(rng.integers(2, 4)), int(rng.integers(2, 4)))
            ox = int(rng.integers(x1 + 1, max(x1 + 2, x2 - w + 1)))
            oz = int(rng.integers(z1 + 1, max(z1 + 2, z2 - d + 1)))
            cellsr = [(ox + i, oz + j) for i in range(w) for j in range(d)]
            if col and ok(cellsr):
                b.fill(ox, y, oz, ox + w - 1, y, oz + d - 1, f"minecraft:{col[4:]}_carpet")
                for c in cellsr:
                    claim(c, 0)
                tracker.use(col)
    # ---- light: hanging lanterns / chandeliers at random spots (large rooms: several)
    if height >= 3:
        spots = []
        for _ in range(1 + (area // 90 if is_large else 0)):
            for _try in range(12):
                lx = int(rng.integers(x1 + (x2 - x1) // 4, x2 - (x2 - x1) // 4 + 1))
                lz = int(rng.integers(z1 + (z2 - z1) // 4, z2 - (z2 - z1) // 4 + 1))
                if all(abs(lx - a) + abs(lz - c) >= 5 for a, c in spots):
                    break
            spots.append((lx, lz))
            if height >= 5 and rng.random() < 0.5:                      # chandelier
                b.set(lx, y + height - 1, lz, "minecraft:chain[axis=y]")
                b.set(lx, y + height - 2, lz, "minecraft:lantern[hanging=true]")
            else:
                b.set(lx, y + height - 1, lz, "minecraft:lantern[hanging=true]")
    return placed


_PROP_KEYS = ["campfire", "dispenser", "dropper", "note_block", "enchanting_table", "lodestone", "bookshelf", "barrel", "chest", "crafting_table", "smithing_table", "anvil", "grindstone",
              "furnace", "smoker", "blast_furnace", "cauldron", "lectern", "lantern", "candle",
              "potted_", "flower_pot", "brewing_stand", "cake", "hay_block", "_bed", "loom", "composter",
              "jukebox", "cartography_table", "fletching_table", "stonecutter", "carpet"]
_AUDIT_BULK = ("bookshelf", "barrel", "hay_block", "carpet", "_bed", "potted_")


def audit_props(b, rooms, y, height=4, large_room=17):
    """Check interior detail for spam AND emptiness. Returns (report_text, ok).

    FAIL: more than the allowed count of any non-bulk prop in a room (2, plus 1 per 150
    floor cells in large rooms), identical non-bulk props within 2 blocks, or a repeated
    novelty prop (cake, a second brewing stand).
    WARN: a prop type over 30% of a building's non-bulk props; a room over-crowded (> 18 props
    per 100 cells, bulk props count half) or bare; and for LARGE rooms (longer side >
    large_room) fewer than 60% of 6x6 patches containing anything, or under 4 props per 100
    cells (the room will feel empty)."""
    lines, ok = [], True
    total = Counter()
    for i, (x1, z1, x2, z2) in enumerate(rooms):
        reg = b.get_region(x1, y, z1, x2, y + height - 1, z2)
        props = []
        for xi in range(reg.shape[0]):
            for yi in range(reg.shape[1]):
                for zi in range(reg.shape[2]):
                    v = int(reg[xi, yi, zi])
                    if v < 2:
                        continue
                    st = b.names[v]
                    n = st.split(":")[1].split("[")[0]
                    if n == "lantern" and "hanging=true" in st:
                        continue          # ceiling light is part of lighting, not decor
                    if n == "chain":
                        continue
                    if any(k in n for k in _PROP_KEYS):
                        props.append((n, xi, yi, zi))
        W, D = x2 - x1 + 1, z2 - z1 + 1
        area = W * D
        large = max(W, D) > large_room
        allow = 2 + (area // 150 if large else 0)
        cnt = Counter(p[0] for p in props)
        for n, c in cnt.items():
            if not any(k in n for k in _AUDIT_BULK):
                total[n] += c
                if c > allow:
                    lines.append(f"FAIL room {i}: {c} x {n} (max {allow})"); ok = False
                if n == "cake" or (n == "brewing_stand" and c > 1):
                    lines.append(f"FAIL room {i}: novelty prop {n} x{c}"); ok = False
        non_bulk = [p for p in props if not any(k in p[0] for k in _AUDIT_BULK)]
        flagged = False
        for a_ in range(len(non_bulk)):
            for c2 in range(a_ + 1, len(non_bulk)):
                p, q = non_bulk[a_], non_bulk[c2]
                if p[0] == q[0] and max(abs(p[1] - q[1]), abs(p[3] - q[3])) <= 2 and not flagged:
                    lines.append(f"FAIL room {i}: identical {p[0]} within 2 blocks"); ok = False
                    flagged = True
        bulk_n = len(props) - len(non_bulk)
        density = 100 * (len(non_bulk) + 0.5 * bulk_n) / max(area, 1)
        if density > 18:
            lines.append(f"WARN room {i}: crowded ({density:.0f} props per 100 cells)")
        elif not props:
            lines.append(f"WARN room {i}: bare")
        if large:
            patches = {(p[1] // 6, p[3] // 6) for p in props}
            total_patches = ((W + 5) // 6) * ((D + 5) // 6)
            cover = len(patches) / max(total_patches, 1)
            if cover < 0.6 or density < 4:
                lines.append(f"WARN room {i}: large room may feel empty (coverage {cover:.0%}, "
                             f"{density:.1f} props per 100 cells)")
    grand = sum(total.values())
    if grand >= 8:
        for n, c in total.items():
            if c / grand > 0.30:
                lines.append(f"WARN building: {n} is {100 * c // grand}% of non-bulk props")
    lines.append(f"{'PASS' if ok else 'FAIL'}: {len(rooms)} rooms, {len(total)} distinct non-bulk prop types")
    return "\n".join(lines), ok
