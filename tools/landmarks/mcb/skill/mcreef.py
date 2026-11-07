"""mcreef: underwater scenes and giant cage/bubble domes for mcbig.BigBuild.

    import sys; sys.path.insert(0, "<skill>/scripts")
    from mcbig import BigBuild
    import mcreef as R

Learned from a studied underwater birdcage build (see
references/techniques/underwater-birdcage-reef.md). Coordinates are build-local
integers: x east+, y up+, z south+. Every function takes the BigBuild `b` first.

Domes      birdcage_dome, bubble_dome, chandelier
Seabed     seabed, sand_channel
Life       kelp, kelp_forest, coral_cluster, coral_garden, coral_spire, gazebo
Creatures  jellyfish, manta_ray, fish, fish_school
Water      waterlog, flood
Palettes   CAGE, CORAL, KELP, SEABED (block lists with roles)
"""
import math

import numpy as np

from mcbig import AIR_ID

# ------------------------------------------------------------------ palettes
# Measured roles from the studied build, translated to modern (1.20+) block IDs.
CAGE = dict(frame="minecraft:quartz_block", trim="minecraft:quartz_stairs",
            slab="minecraft:smooth_stone_slab", glass="minecraft:light_gray_stained_glass",
            light="minecraft:sea_lantern", metal="minecraft:iron_block", chain="minecraft:chain")
CORAL = ["minecraft:magenta_wool", "minecraft:orange_wool", "minecraft:purple_terracotta",
         "minecraft:cyan_terracotta", "minecraft:brown_wool", "minecraft:pink_wool",
         "minecraft:light_blue_terracotta", "minecraft:red_terracotta",
         "minecraft:yellow_terracotta", "minecraft:fire_coral_block",
         "minecraft:tube_coral_block", "minecraft:brain_coral_block"]
KELP = ["minecraft:green_wool", "minecraft:slime_block", "minecraft:lime_terracotta",
        "minecraft:emerald_block", "minecraft:green_stained_glass", "minecraft:melon",
        "minecraft:green_terracotta", "minecraft:moss_block"]
SEABED = ["minecraft:prismarine", "minecraft:mossy_cobblestone", "minecraft:brown_wool",
          "minecraft:cyan_terracotta", "minecraft:stone", "minecraft:clay", "minecraft:gravel",
          "minecraft:sand"]

# Birdcage outer profile, measured: (height fraction, radius fraction), base->top.
# Vertical bars to 0.66, flared lower dome to 0.81, inward ledge, short drum,
# upper dome closing at 0.98, finial above.
CAGE_PROFILE = [(0.00, 1.00), (0.66, 1.00), (0.70, 0.97), (0.75, 0.92), (0.78, 0.86),
                (0.81, 0.78), (0.82, 0.66), (0.86, 0.62), (0.89, 0.59), (0.91, 0.51),
                (0.93, 0.45), (0.95, 0.32), (0.96, 0.25), (0.97, 0.17), (0.98, 0.0)]


def _rng(b, rng):
    return rng if rng is not None else b.rng


def _pick(rng, blocks, shape=None):
    return blocks[rng.integers(len(blocks))] if shape is None else rng.integers(len(blocks), size=shape)


# --------------------------------------------------------------------- domes
def birdcage_dome(b, cx, y0, cz, r, height, bars=16, pal=None, bar_w=2,
                  open_walls=True, ribs=True, finial=True, base=True):
    """Giant birdcage pavilion (the studied build: r=67, height=251, 16 bars).

    Bars run from y0 to 0.58*height, collar rings at 0.30 and 0.37, round arches
    between bars spring at 0.58 and crown at 0.66 where a cornice ring sits; above
    that the shell follows CAGE_PROFILE in glass with frame ribs over each bar.
    open_walls=False glazes the walls too (use for a dry air pocket underwater).
    Keep bay width (2*pi*r/bars) about 20-26 blocks; ~r/2.6 is the measured value."""
    p = dict(CAGE, **(pal or {}))
    H = height
    ys = lambda f: y0 + int(round(f * H))
    y_spring, y_crown = ys(0.58), ys(0.66)
    prof = np.array(CAGE_PROFILE)

    def rad(y):
        return r * np.interp((y - y0) / H, prof[:, 0], prof[:, 1])

    def ang_mask(X, Z, width):
        th = np.arctan2(Z - cz, X - cx)
        step = 2 * math.pi / bars
        d = np.abs(((th + step / 2) % step) - step / 2)
        R = np.hypot(X - cx, Z - cz) + 1e-6
        return d * R <= width / 2

    def shell(X, Z, rr, t=1.0):
        R = np.hypot(X - cx, Z - cz)
        return (R <= rr + 0.5) & (R > rr - 0.5 - t)

    # base plinth with a lit ring (the studied build lights its rim with sea lanterns)
    if base:
        b.cylinder(cx, y0 - 1, cz, r + 3, y0 - 1, p["frame"])
        b.ring(cx, y0 - 1, cz, r + 1, r + 2, y0 - 1, p["light"])
    # bars
    b.fill_where(cx - r - 1, y0, cz - r - 1, cx + r + 1, y_spring, cz + r + 1,
                 lambda X, y, Z: shell(X, Z, r, 1) & ang_mask(X, Z, bar_w), p["frame"])
    if not open_walls:
        b.fill_where(cx - r - 1, y0, cz - r - 1, cx + r + 1, y_spring, cz + r + 1,
                     lambda X, y, Z: shell(X, Z, r, 0) & ~ang_mask(X, Z, bar_w), p["glass"])
    # collar rings: 2-layer bands that stick out 1 (relief)
    for f in (0.30, 0.37):
        yc = ys(f)
        b.ring(cx, yc, cz, r - 2, r + 1, yc + 1, p["frame"])
        b.ring(cx, yc + 2, cz, r - 1, r + 1, yc + 2, p["slab"] + "[type=bottom]")
    # arches between bars: semicircle per bay, glass spandrels above, cornice on top
    bay = 2 * math.pi * r / bars
    ar = bay / 2

    def arch_band(X, y, Z, solid):
        th = np.arctan2(Z - cz, X - cx)
        step = 2 * math.pi / bars
        s = (((th) % step) - step / 2) * r          # arc distance from bay centre
        rise = y - y_spring
        inside = (s ** 2 + (rise * ar / max(y_crown - y_spring, 1)) ** 2) <= (ar - bar_w / 2) ** 2
        ring = (s ** 2 + (rise * ar / max(y_crown - y_spring, 1)) ** 2) <= (ar - bar_w / 2 + 1.2) ** 2
        return shell(X, Z, r, 1) & ((ring & ~inside) if solid else ~ring)
    b.fill_where(cx - r - 1, y_spring, cz - r - 1, cx + r + 1, y_crown, cz + r + 1,
                 lambda X, y, Z: arch_band(X, y, Z, False), p["glass"])
    b.fill_where(cx - r - 1, y_spring, cz - r - 1, cx + r + 1, y_crown, cz + r + 1,
                 lambda X, y, Z: arch_band(X, y, Z, True), p["frame"])
    b.ring(cx, y_spring, cz, r - 2, r + 1, y_spring, p["frame"])           # impost collars
    b.ring(cx, y_crown, cz, r - 2, r + 1, y_crown, p["frame"])             # cornice
    b.ring(cx, y_crown + 1, cz, r - 1, r + 2, y_crown + 1, p["slab"] + "[type=bottom]")
    # upper shell: glass skin following the profile, ribs over each bar
    top = ys(0.98)

    def skin(X, y, Z):
        rr = rad(y)
        rr2 = rad(y + 1)
        R = np.hypot(X - cx, Z - cz)
        lo = min(rr, rr2)
        return (R <= max(rr, rr2) + 0.5) & (R > lo - 1.0)
    b.fill_where(cx - r - 1, y_crown + 1, cz - r - 1, cx + r + 1, top, cz + r + 1, skin, p["glass"])
    if ribs:
        b.fill_where(cx - r - 1, y_crown + 1, cz - r - 1, cx + r + 1, top, cz + r + 1,
                     lambda X, y, Z: skin(X, y, Z) & ang_mask(X, Z, bar_w), p["frame"])
    # ledge band where the profile steps in (0.81 -> 0.82)
    yl = ys(0.815)
    b.ring(cx, yl, cz, int(rad(yl + 2)) - 1, int(rad(yl - 1)) + 1, yl, p["frame"])
    yd = ys(0.86)
    b.ring(cx, yd, cz, int(rad(yd)) - 1, int(rad(yd)) + 1, yd, p["slab"] + "[type=bottom]")
    if finial:
        cap_r = max(2, int(r * 0.1))
        b.cylinder(cx, top, cz, cap_r, top, p["frame"])
        fy = top + 1
        hook = max(3, int(r * 0.08))
        b.fill(cx, fy, cz, cx, fy + hook, cz, p["metal"])
        # ring/hook on top (circle in the x-y plane), like the studied iron finial
        for a in range(0, 360, 8):
            x = cx + int(round(hook * math.cos(math.radians(a))))
            y = fy + hook * 2 + int(round(hook * math.sin(math.radians(a))))
            b.set(x, y, cz, p["metal"])
    return dict(y_spring=y_spring, y_crown=y_crown, y_top=top, radius_at=rad)


def bubble_dome(b, cx, cy, cz, r, glass="minecraft:light_blue_stained_glass", ry=None,
                frame=None, ribs=0, below=0.0, thickness=1):
    """Sphere or ellipsoid shell (an air bubble / glass bubble city). cy is the centre.
    ry: vertical radius (default r). below: fraction of the lower half kept (0 = only the
    upper hemisphere, 1 = full sphere). ribs: number of meridian frame ribs (0 = none)."""
    ry = ry or r
    y_lo = cy - int(ry * below)

    def f(X, y, Z):
        d = ((X - cx) / r) ** 2 + ((y - cy) / ry) ** 2 + ((Z - cz) / r) ** 2
        inner = ((X - cx) / (r - thickness)) ** 2 + ((y - cy) / (ry - thickness)) ** 2 + ((Z - cz) / (r - thickness)) ** 2
        return (d <= 1.0) & (inner > 1.0)
    b.fill_where(cx - r, y_lo, cz - r, cx + r, cy + ry, cz + r, f, glass)
    if ribs and frame:
        step = 2 * math.pi / ribs

        def g(X, y, Z):
            th = np.arctan2(Z - cz, X - cx)
            R = np.hypot(X - cx, Z - cz) + 1e-6
            return f(X, y, Z) & (np.abs(((th + step / 2) % step) - step / 2) * R <= 0.75)
        b.fill_where(cx - r, y_lo, cz - r, cx + r, cy + ry, cz + r, g, frame)


def chandelier(b, cx, y_top, cz, drop, r, pal=None):
    """Hanging chandelier: chain from y_top down `drop` blocks, an onion body, a gold ring
    and lit arms. The studied one is ~47 wide and hangs ~80 blocks under a 67-radius dome
    (r ~= 0.35 * dome radius, drop ~= 0.3 * dome height)."""
    p = dict(CAGE, **(pal or {}))
    yb = y_top - drop
    b.fill(cx, yb, cz, cx, y_top, cz, p["chain"])
    body_h = max(4, r)
    for i in range(body_h):                      # onion / teardrop body
        t = i / max(body_h - 1, 1)
        rr = max(0, int(round(r * 0.45 * math.sin(math.pi * (0.15 + 0.85 * t)))))
        y = yb - body_h + i
        if rr:
            b.cylinder(cx, y, cz, rr, y, p["frame"], hollow=True)
        else:
            b.set(cx, y, cz, p["frame"])
    yr = yb - body_h // 2
    b.ring(cx, yr, cz, r - 1, r, yr, "minecraft:gold_block")
    for a in range(0, 360, 45):                   # arms with lights
        x = cx + int(round(r * math.cos(math.radians(a))))
        z = cz + int(round(r * math.sin(math.radians(a))))
        b.set(x, yr + 1, z, p["frame"])
        b.set(x, yr + 2, z, p["light"])
    b.set(cx, yb - body_h - 1, cz, p["light"])


# -------------------------------------------------------------------- seabed
def _value_noise(shape, scale, rng):
    gx, gz = shape[0] // scale + 2, shape[1] // scale + 2
    g = rng.random((gx, gz))
    xs = np.arange(shape[0]) / scale
    zs = np.arange(shape[1]) / scale
    x0, z0 = xs.astype(int), zs.astype(int)
    fx, fz = (xs - x0)[:, None], (zs - z0)[None, :]
    fx, fz = fx * fx * (3 - 2 * fx), fz * fz * (3 - 2 * fz)
    a = g[x0][:, z0]; c = g[x0 + 1][:, z0]; d = g[x0][:, z0 + 1]; e = g[x0 + 1][:, z0 + 1]
    return a * (1 - fx) * (1 - fz) + c * fx * (1 - fz) + d * (1 - fx) * fz + e * fx * fz


def seabed(b, x1, z1, x2, z2, y, relief=6, blocks=None, rng=None, scale=14):
    """Rolling sea floor from y up to y+relief, top surface mixed from `blocks`.
    Measured: the studied seabed is shallow (most of it 2-10 blocks of relief); the
    visual depth comes from coral and kelp, not from terrain."""
    rng = _rng(b, rng)
    blocks = blocks or SEABED
    nx, nz = x2 - x1 + 1, z2 - z1 + 1
    n = 0.65 * _value_noise((nx, nz), scale, rng) + 0.35 * _value_noise((nx, nz), max(3, scale // 3), rng)
    H = (y + n * relief).astype(int)
    # material patches: low-frequency noise picks the block, a little jitter at the borders
    m = _value_noise((nx, nz), max(4, scale // 2), rng) + rng.normal(0, 0.04, (nx, nz))
    pick = np.clip((m - m.min()) / (np.ptp(m) + 1e-9) * len(blocks), 0, len(blocks) - 1).astype(int)
    for k, blk in enumerate(blocks):
        Hk = np.where(pick == k, H, y - 1)
        b.heightfield(x1, z1, x2, z2, y, lambda X, Z, Hk=Hk: Hk[X - x1, Z - z1], blk)
    return H


def sand_channel(b, points, y, width=5, block="minecraft:blue_stained_glass", rng=None):
    """Winding channel along a polyline of (x, z) points, painted at height y. The studied
    build traces its 'rivers' in blue stained glass laid flat on the seabed."""
    rng = _rng(b, rng)
    for (xa, za), (xb, zb) in zip(points, points[1:]):
        n = int(max(abs(xb - xa), abs(zb - za))) + 1
        for i in range(n):
            t = i / max(n - 1, 1)
            x, z = int(xa + (xb - xa) * t), int(za + (zb - za) * t)
            w = width / 2 + rng.integers(-1, 2) * 0.5
            b.cylinder(x, y, z, max(1, int(w)), y, block)


# ---------------------------------------------------------------------- life
def kelp(b, x, y, z, height, blocks=None, rng=None, sway=3, leaf_every=(1, 3)):
    """One giant kelp stalk: a 1-wide stem that drifts sideways (sway = max drift) with
    leaf blades (2-4 long, angled up) every few blocks, colours mixed from `blocks`."""
    rng = _rng(b, rng)
    blocks = blocks or KELP
    phase, freq = rng.random() * 6.28, 0.04 + rng.random() * 0.05
    nxt = y + int(rng.integers(*leaf_every))
    for yy in range(y, y + height):
        t = yy - y
        dx = int(round(sway * math.sin(phase + t * freq)))
        dz = int(round(sway * 0.6 * math.cos(phase * 1.3 + t * freq * 0.7)))
        stem = blocks[(t // 3 + int(phase * 10)) % min(3, len(blocks))]
        b.set(x + dx, yy, z + dz, stem)
        if yy >= nxt:
            ang = rng.random() * 6.28
            ln = int(rng.integers(2, 6 if yy - y > height * 0.3 else 4))
            leaf = _pick(rng, blocks)
            for k in range(1, ln + 1):
                b.set(x + dx + int(round(k * math.cos(ang))), yy + k // 2,
                      z + dz + int(round(k * math.sin(ang))), leaf)
            nxt = yy + int(rng.integers(*leaf_every))


def kelp_forest(b, x1, z1, x2, z2, y, count, h_min=40, h_max=140, blocks=None, rng=None,
                avoid=None):
    """Scatter kelp stalks. Measured heights: median ~80, 90th percentile ~140, tallest
    reach the top of the scene. avoid(x, z) -> True skips a spot (e.g. inside a dome)."""
    rng = _rng(b, rng)
    placed = 0
    for _ in range(count * 20):
        if placed >= count:
            break
        x, z = int(rng.integers(x1, x2 + 1)), int(rng.integers(z1, z2 + 1))
        if avoid and avoid(x, z):
            continue
        h = int(h_min + (h_max - h_min) * rng.random() ** 1.5)    # skewed: many short, few tall
        if y + h > b.y_max:
            h = b.y_max - y
        kelp(b, x, y, z, h, blocks, rng)
        placed += 1


def coral_cluster(b, x, y, z, size, blocks=None, rng=None, branches=None):
    """Branching coral: random-walk limbs of small blobs, each limb one colour, limbs
    leaning outward and up. size ~ overall height."""
    rng = _rng(b, rng)
    blocks = blocks or CORAL
    branches = branches or max(3, size // 3)
    for _ in range(branches):
        blk = _pick(rng, blocks)
        px, py, pz = float(x), float(y), float(z)
        ang = rng.random() * 6.28
        for s in range(size):
            px += math.cos(ang) * 0.6 + rng.normal(0, 0.3)
            pz += math.sin(ang) * 0.6 + rng.normal(0, 0.3)
            py += 0.8
            ang += rng.normal(0, 0.4)
            rr = 1 if s < size * 0.7 else int(rng.integers(1, 3))
            X, Y, Z = int(px), int(py), int(pz)
            b.fill_where(X - rr, Y - rr, Z - rr, X + rr, Y + rr, Z + rr,
                         lambda A, yy, C: (A - X) ** 2 + (yy - Y) ** 2 + (C - Z) ** 2 <= rr * rr, blk)


def coral_spire(b, x, y, z, height, radius, rock=("minecraft:gray_wool", "minecraft:stone",
                "minecraft:andesite"), blocks=None, rng=None, coral_count=None):
    """Centrepiece rock spire wrapped in coral (the studied cage has one rising to ~0.33 of
    the cage height, carrying a small gazebo on top). Leaning, lumpy column that narrows
    to ~45% of its base radius; returns the (x, y, z) of its top for whatever sits on it."""
    rng = _rng(b, rng)
    lean = rng.normal(0, 0.12, 2)
    for yy in range(y, y + height):
        t = (yy - y) / max(height - 1, 1)
        rr = radius * (1 - 0.55 * t) + rng.normal(0, 0.5)
        ox, oz = x + lean[0] * (yy - y), z + lean[1] * (yy - y)
        X0, Z0 = int(round(ox)), int(round(oz))
        R = int(math.ceil(rr)) + 1
        blk = rock[rng.integers(len(rock))]
        b.fill_where(X0 - R, yy, Z0 - R, X0 + R, yy, Z0 + R,
                     lambda A, _y, C: (A - ox) ** 2 + (C - oz) ** 2 <= rr * rr, blk)
    top = (int(round(x + lean[0] * height)), y + height, int(round(z + lean[1] * height)))
    for _ in range(coral_count or max(6, height // 3)):
        t = rng.random() ** 0.7
        yy = int(y + t * height * 0.9)
        a = rng.random() * 6.28
        rr = radius * (1 - 0.55 * t) + 0.5
        cxx = int(x + lean[0] * (yy - y) + rr * math.cos(a))
        czz = int(z + lean[1] * (yy - y) + rr * math.sin(a))
        coral_cluster(b, cxx, yy, czz, int(rng.integers(3, 8)), blocks, rng, branches=3)
    return top


def gazebo(b, x, y, z, r=5, height=6, columns=8, frame="minecraft:quartz_block",
           roof="minecraft:gold_block", floor="minecraft:smooth_stone_slab[type=bottom]"):
    """Small round pavilion (the centrepiece on the studied coral spire is ~ this shape:
    column ring, gold rim, tiny spire)."""
    b.cylinder(x, y, z, r + 1, y, frame)
    b.cylinder(x, y + 1, z, r, y + 1, floor)
    for i in range(columns):
        a = 2 * math.pi * i / columns
        b.fill(x + int(round(r * math.cos(a))), y + 1, z + int(round(r * math.sin(a))),
               x + int(round(r * math.cos(a))), y + height, z + int(round(r * math.sin(a))), frame)
    b.ring(x, y + height + 1, z, r - 1, r + 1, y + height + 1, roof)
    b.dome(x, y + height + 1, z, r, frame, hollow=True)
    b.fill(x, y + height + r + 1, z, x, y + height + r + 3, z, "minecraft:iron_bars")


def coral_garden(b, x1, z1, x2, z2, y, count, size=(4, 12), blocks=None, rng=None, avoid=None):
    rng = _rng(b, rng)
    for _ in range(count):
        x, z = int(rng.integers(x1, x2 + 1)), int(rng.integers(z1, z2 + 1))
        if avoid and avoid(x, z):
            continue
        coral_cluster(b, x, y, z, int(rng.integers(*size)), blocks, rng)


# ----------------------------------------------------------------- creatures
def jellyfish(b, x, y, z, bell_r=6, tentacles=None, bell="minecraft:pink_stained_glass",
              rim="minecraft:magenta_terracotta", tentacle="minecraft:pink_stained_glass_pane",
              core="minecraft:sea_lantern", rng=None):
    """Bell (flattened hemisphere) at top y, frilled rim, hanging tentacles.
    Measured: big ones 29 wide x 59 tall (tentacles ~1.5x bell height),
    small ones 8 x 8. tentacles = length (default 3 * bell_r)."""
    rng = _rng(b, rng)
    L = tentacles or bell_r * 3
    yc = y - bell_r                                    # bell base
    b.fill_where(x - bell_r, yc, z - bell_r, x + bell_r, y, z + bell_r,
                 lambda X, yy, Z: ((X - x) ** 2 + (Z - z) ** 2 + ((yy - yc) * 1.4) ** 2 <= bell_r ** 2 + bell_r)
                 & ((X - x) ** 2 + (Z - z) ** 2 + ((yy - yc) * 1.4) ** 2 > (bell_r - 1.5) ** 2), bell)
    b.ring(x, yc, z, bell_r - 2, bell_r, yc, rim)
    if bell_r >= 4:
        b.set(x, yc + 1, z, core)
    n = max(4, bell_r * 2)
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = bell_r * (0.4 + 0.5 * rng.random())
        tx, tz = x + rr * math.cos(a), z + rr * math.sin(a)
        ln = int(L * (0.6 + 0.4 * rng.random()))
        ph = rng.random() * 6.28
        for k in range(1, ln):
            b.set(int(tx + math.sin(ph + k * 0.25)), yc - k, int(tz + math.cos(ph + k * 0.2)), tentacle)


def manta_ray(b, x, y, z, span=24, top="minecraft:black_concrete", belly="minecraft:quartz_block",
              facing="south"):
    """Manta ray gliding level. Countershaded like the studied ones: dark top layer, pale
    belly layer, wingtips curling up 1-2 blocks, thin tail. Measured span 24-27."""
    half = span // 2
    length = int(span * 0.55)
    for i in range(-half, half + 1):
        t = abs(i) / half
        chord = int(round(length * (1 - t ** 1.3)))
        if chord <= 0:
            continue
        lift = int(round(2 * t ** 3))
        a0 = int(-chord * 0.35 - t * length * 0.25)
        for j in range(a0, a0 + chord):
            dx, dz = (i, j) if facing in ("south", "north") else (j, i)
            if facing == "north":
                dz = -dz
            if facing == "west":
                dx = -dx
            b.set(x + dx, y + lift, z + dz, top)
            b.set(x + dx, y + lift - 1, z + dz, belly)
    for k in range(length // 2):                       # thin tail behind the body
        back = int(length * 0.35) + k
        off = {"south": (0, -back), "north": (0, back), "east": (-back, 0), "west": (back, 0)}[facing]
        b.set(x + off[0], y, z + off[1], top)


def fish(b, x, y, z, length=5, body="minecraft:yellow_terracotta", fin="minecraft:light_blue_wool",
         axis="x", tall=False):
    """Small fish along +axis: spindle body (1 block, 3 tall in the middle if tall),
    tail fin of 2-3 blocks. Measured: most fish are 3-5 blocks; showpiece fish ~20."""
    for i in range(length):
        dx, dz = (i, 0) if axis == "x" else (0, i)
        mid = 0 < i < length - 1
        b.set(x + dx, y, z + dz, body)
        if tall and mid and length >= 5:
            b.set(x + dx, y + 1, z + dz, body)
            b.set(x + dx, y - 1, z + dz, body)
    tx, tz = (x - 1, z) if axis == "x" else (x, z - 1)
    for dy in (-1, 1):
        b.set(tx, y + dy, tz, fin)


def fish_school(b, path, count, spread=3, rng=None, colors=None, length=(3, 5)):
    """A school strung along a curved path (list of (x, y, z)), all facing the same way.
    The studied build places schools as long curving ribbons, not round clouds."""
    rng = _rng(b, rng)
    colors = colors or [("minecraft:yellow_terracotta", "minecraft:light_blue_wool"),
                        ("minecraft:orange_wool", "minecraft:white_wool"),
                        ("minecraft:light_blue_terracotta", "minecraft:yellow_wool")]
    body, fin = colors[rng.integers(len(colors))]
    pts = np.array(path, float)
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    for _ in range(count):
        s = rng.random() * seg[-1]
        p = np.array([np.interp(s, seg, pts[:, k]) for k in range(3)])
        p += rng.normal(0, spread, 3) * [1, 0.4, 1]
        d = pts[-1] - pts[0]
        fish(b, int(p[0]), int(p[1]), int(p[2]), int(rng.integers(*length)), body, fin,
             axis="x" if abs(d[0]) >= abs(d[2]) else "z")


# --------------------------------------------------------------------- water
_WATERLOGGABLE = ("_stairs", "_slab", "_fence", "_wall", "_pane", "iron_bars", "chain",
                  "lantern", "_trapdoor", "sea_pickle", "_coral", "_coral_fan", "glow_lichen",
                  "conduit", "ladder", "_sign", "lightning_rod", "scaffolding", "candle")


def waterlog(b, keep_dry=None):
    """Add waterlogged=true to waterloggable blocks (stairs, slabs, panes, fences, walls,
    chains, lanterns, trapdoors...) so they do not leave dry pockets underwater.
    keep_dry(X, y, Z) -> bool: cells there are NOT waterlogged (inside a bubble or dry
    cage); pass the same function you gave flood(), or water appears inside the bubble."""
    from mcbig import T
    remap = {}
    for i, nm in enumerate(list(b.names)):
        base = nm.split("[")[0]
        if any(base.endswith(s) or s in base for s in _WATERLOGGABLE) and "waterlogged" not in nm:
            new = nm[:-1] + ",waterlogged=true]" if "[" in nm else nm + "[waterlogged=true]"
            remap[i] = b.register(new)
    if not remap:
        return 0
    lut = np.arange(len(b.names), dtype=np.uint16)
    for k, v in remap.items():
        lut[k] = v
    for (tx, tz), arr in b.tiles.items():
        new = lut[arr]
        if keep_dry is not None:
            X = np.arange(tx * T, tx * T + T)[:, None]
            Z = np.arange(tz * T, tz * T + T)[None, :]
            for j in range(arr.shape[1]):
                dry = np.broadcast_to(np.asarray(keep_dry(X, j + b.y_min, Z), bool), (T, T))
                new[:, j, :][dry] = arr[:, j, :][dry]
        b.tiles[(tx, tz)] = new
    return len(remap)


def flood(b, x1, y1, z1, x2, y2, z2, keep_dry=None):
    """Fill every unset or air cell in the box with water. keep_dry(X, y, Z) -> bool mask
    of cells that stay air (e.g. the inside of a bubble or a dry cage)."""
    wid = b.register("minecraft:water")

    def f(X, y, Z):
        m = np.ones(np.broadcast(X, Z).shape, bool)
        if keep_dry is not None:
            m &= ~np.asarray(keep_dry(X, y, Z), bool)
        return m
    b.fill_where(x1, y1, z1, x2, y2, z2, f, "minecraft:water", only_empty=True)
    if keep_dry is not None:      # dry cells are written as explicit air so old water is removed
        b.fill_where(x1, y1, z1, x2, y2, z2, keep_dry, "minecraft:air", only_empty=True)
    return wid
