"""mcbig: build HUGE Minecraft structures (hundreds of blocks across, millions of blocks).

Differences from mcbuild.Build (which stays best for small builds):
  * Voxels live in numpy tiles (64 x height x 64), allocated lazily -> low memory.
  * Shape macros are vectorized (fill_where, cylinder, tapered_cylinder, dome, ring...).
  * Export is a *datapack* of many small step files that run one after another using
    `schedule function`, with `forceload` around each 64x64 tile so commands never hit
    unloaded chunks and never exceed the maxCommandChainLength cap (65,536).
  * Absolute world coordinates (you choose `origin` at export time).
  * Preview renders (top view / cross-section PNGs) so the design can be inspected
    without launching the game.

Coordinates are build-local integers: x east+, y up+, z south+. y must lie in
[y_min, y_max] given at construction. At export, `origin` is the world position of
local (0,0,0).

Typical use:
    import sys; sys.path.insert(0, "<skill>/scripts")
    from mcbig import BigBuild
    b = BigBuild(palette=None, seed=1, y_min=0, y_max=200)
    b.cylinder(0, 0, 0, 150, 12, "minecraft:stone_bricks")
    b.render_top("top.png")
    b.save_sharded("out", namespace="water7", name="hull", origin=(1000, 64, 1000))
"""
import json
import math
import os
import zlib

import numpy as np

from mcbuild import Palette, _norm, _id, AIR  # noqa: F401  (shared helpers)

T = 64                 # tile size in blocks (x and z)
FILL_LIMIT = 32768     # vanilla /fill volume cap
AIR_ID = 1


_DYES = {"white": (234, 236, 237), "orange": (241, 118, 20), "magenta": (189, 68, 179),
         "light_blue": (58, 175, 217), "yellow": (248, 198, 40), "lime": (112, 185, 26),
         "pink": (237, 141, 172), "gray": (63, 68, 72), "light_gray": (142, 142, 135),
         "cyan": (21, 138, 145), "purple": (122, 42, 173), "blue": (53, 57, 157),
         "brown": (114, 72, 41), "green": (85, 110, 28), "red": (161, 39, 35), "black": (25, 25, 30)}
_SPECIAL = {"mangrove": (125, 52, 48), "crimson": (120, 40, 60), "cherry": (225, 175, 175),
            "slime": (120, 200, 90), "emerald": (40, 190, 90), "melon": (110, 150, 40),
            "sea_lantern": (210, 230, 220), "tube_coral": (50, 90, 220), "brain_coral": (210, 90, 160),
            "bubble_coral": (160, 30, 160), "fire_coral": (200, 40, 50), "horn_coral": (220, 200, 60),
            "kelp": (60, 120, 40), "gold": (245, 210, 70), "obsidian": (25, 20, 40), "clay": (160, 166, 180),
            "sponge": (200, 190, 80), "magma": (150, 60, 20), "purpur": (170, 125, 170),
            "amethyst": (140, 100, 200), "packed_ice": (140, 180, 240), "dark_prismarine": (50, 90, 75),
            "prismarine": (90, 160, 145)}


def block_color(name):
    """Deterministic RGB for a block id (keyword heuristics, hash fallback)."""
    n = _id(name).split(":")[-1]
    dye = sorted(_DYES, key=len, reverse=True)
    for d in dye:                                   # coloured wool/glass/concrete/terracotta
        if n.startswith(d + "_"):                    # longest names first, so light_gray beats gray
            r, g, bl = _DYES[d]
            if "terracotta" in n:                       # terracotta is muted and brownish
                r, g, bl = int(r * 0.6 + 60), int(g * 0.5 + 40), int(bl * 0.45 + 35)
            if "glass" in n:
                r, g, bl = int(r * 0.7 + 70), int(g * 0.7 + 70), int(bl * 0.7 + 70)
            return (r, g, bl)
    for k, col in _SPECIAL.items():
        if k in n:
            return col
    table = [
        (("water",), (40, 100, 200)), (("glass", "ice"), (150, 200, 230)),
        (("deepslate", "blackstone", "basalt", "coal"), (60, 60, 70)),
        (("sand", "yellow"), (220, 205, 150)),
        (("stone", "andesite", "diorite", "cobble", "tuff", "concrete"), (140, 140, 145)),
        (("oxidized",), (82, 162, 132)), (("weathered",), (108, 153, 110)), (("exposed",), (161, 125, 103)),
        (("terracotta", "brick", "copper", "orange"), (190, 100, 60)),
        (("quartz", "calcite", "white", "snow"), (230, 230, 230)),
        (("grass", "leaves", "moss", "green"), (80, 140, 60)),
        (("oak", "spruce", "birch", "jungle", "acacia", "plank", "log", "wood"), (140, 100, 60)),
        (("blue", "prismarine", "lapis", "cyan"), (50, 110, 190)),
        (("lantern", "glowstone", "torch", "lamp", "light"), (255, 220, 120)),
        (("iron", "chain", "bars"), (170, 170, 175)),
        (("dirt", "podzol", "mud", "gravel"), (110, 85, 60)),
    ]
    for keys, col in table:
        if any(k in n for k in keys):
            return col
    h = zlib.crc32(n.encode())
    return (80 + h % 150, 80 + (h >> 8) % 150, 80 + (h >> 16) % 150)


_FACING = ["north", "east", "south", "west"]


def transform_block(name, rot=0, mirror=False):
    """Rotate (90-degree steps clockwise seen from above) and/or mirror (east<->west)
    a block string's directional state: facing, axis, wall/fence/pane connections,
    stair shape and door hinge."""
    base, sep, state = name.partition("[")
    if not sep:
        return name
    out = []
    for p in state.rstrip("]").split(","):
        k, _, v = p.partition("=")
        if k == "facing" and v in _FACING:
            if mirror and v in ("east", "west"):
                v = "west" if v == "east" else "east"
            v = _FACING[(_FACING.index(v) + rot) % 4]
        elif k in _FACING:                      # connection flags: north=true etc.
            if mirror and k in ("east", "west"):
                k = "west" if k == "east" else "east"
            k = _FACING[(_FACING.index(k) + rot) % 4]
        elif k == "axis" and v in ("x", "z") and rot % 2:
            v = "z" if v == "x" else "x"
        elif mirror and k == "shape" and v.endswith(("_left", "_right")):
            v = v.replace("left", "@").replace("right", "left").replace("@", "right")
        elif mirror and k == "hinge":
            v = "right" if v == "left" else "left"
        out.append(f"{k}={v}")
    return base + "[" + ",".join(out) + "]"


def _save_png(img, path, max_side):
    """Save an RGB array as PNG, downscaling (nearest) so the longest side <= max_side.
    Small images cost far fewer tokens when viewed."""
    from PIL import Image
    im = Image.fromarray(img)
    w, h = im.size
    if max(w, h) > max_side:
        s = max_side / max(w, h)
        im = im.resize((max(1, int(w * s)), max(1, int(h * s))), Image.NEAREST)
    im.save(path)


class BigBuild:
    def __init__(self, palette=None, seed=0, y_min=0, y_max=255):
        self.palette = palette
        self.rng = np.random.default_rng(seed)
        self.y_min, self.y_max = y_min, y_max
        self.ny = y_max - y_min + 1
        self.tiles = {}                     # (tx, tz) -> uint16 array (T, ny, T)
        self.names = ["", AIR]              # id -> block string (0 = unset)
        self.ids = {AIR: AIR_ID}

    # ------------------------------------------------------------------ core
    def register(self, block):
        block = _norm(block)
        if block not in self.ids:
            if self.palette:
                self.palette.check(block)
            self.ids[block] = len(self.names)
            self.names.append(block)
            if len(self.names) >= 65535:
                raise ValueError("too many distinct block strings (65k limit)")
        return self.ids[block]

    def _tile(self, tx, tz):
        t = self.tiles.get((tx, tz))
        if t is None:
            t = np.zeros((T, self.ny, T), dtype=np.uint16)
            self.tiles[(tx, tz)] = t
        return t

    def _write(self, x1, y1, z1, x2, y2, z2, value, mask=None):
        """Write constant or array `value` (region-shaped) into [x1..x2]x[y1..y2]x[z1..z2],
        optionally only where bool `mask` (region-shaped, broadcastable) is True."""
        x1, x2 = sorted((x1, x2)); y1, y2 = sorted((y1, y2)); z1, z2 = sorted((z1, z2))
        if y1 < self.y_min or y2 > self.y_max:
            raise ValueError(f"y range {y1}..{y2} outside build limits {self.y_min}..{self.y_max}")
        shape = (x2 - x1 + 1, y2 - y1 + 1, z2 - z1 + 1)
        if mask is not None:
            mask = np.broadcast_to(mask, shape)
        if isinstance(value, np.ndarray):
            value = np.broadcast_to(value, shape)
        ys = slice(y1 - self.y_min, y2 - self.y_min + 1)
        for tx in range(x1 // T, x2 // T + 1):
            ax1, ax2 = max(x1, tx * T), min(x2, tx * T + T - 1)
            for tz in range(z1 // T, z2 // T + 1):
                az1, az2 = max(z1, tz * T), min(z2, tz * T + T - 1)
                sx = slice(ax1 - x1, ax2 - x1 + 1)
                sz = slice(az1 - z1, az2 - z1 + 1)
                tile = self._tile(tx, tz)
                dst = tile[ax1 - tx * T:ax2 - tx * T + 1, ys, az1 - tz * T:az2 - tz * T + 1]
                v = value[sx, :, sz] if isinstance(value, np.ndarray) else value
                if mask is None:
                    dst[...] = v
                else:
                    m = mask[sx, :, sz]
                    if isinstance(v, np.ndarray):
                        dst[m] = v[m]
                    else:
                        dst[m] = v

    # ------------------------------------------------------------ primitives
    def set(self, x, y, z, block):
        self._write(x, y, z, x, y, z, self.register(block))

    def fill(self, x1, y1, z1, x2, y2, z2, block):
        self._write(x1, y1, z1, x2, y2, z2, self.register(block))

    def box(self, x1, y1, z1, x2, y2, z2, block):
        self.fill(x1, y1, z1, x2, y2, z2, block)

    def clear(self, x1, y1, z1, x2, y2, z2):
        self._write(x1, y1, z1, x2, y2, z2, AIR_ID)

    def hollow_box(self, x1, y1, z1, x2, y2, z2, block):
        x1, x2 = sorted((x1, x2)); y1, y2 = sorted((y1, y2)); z1, z2 = sorted((z1, z2))
        self.fill(x1, y1, z1, x2, y2, z2, block)
        if x2 - x1 >= 2 and y2 - y1 >= 2 and z2 - z1 >= 2:
            self.clear(x1 + 1, y1 + 1, z1 + 1, x2 - 1, y2 - 1, z2 - 1)

    def walls(self, x1, y1, z1, x2, y2, z2, block):
        x1, x2 = sorted((x1, x2)); z1, z2 = sorted((z1, z2))
        self.fill(x1, y1, z1, x2, y2, z1, block)
        self.fill(x1, y1, z2, x2, y2, z2, block)
        self.fill(x1, y1, z1, x1, y2, z2, block)
        self.fill(x2, y1, z1, x2, y2, z2, block)

    def pillar(self, x, y1, z, y2, block):
        self.fill(x, y1, z, x, y2, z, block)

    def mix(self, x1, y1, z1, x2, y2, z2, blocks, weights=None):
        ids = np.array([self.register(b) for b in blocks], dtype=np.uint16)
        p = None
        if weights:
            p = np.array(weights, float); p = p / p.sum()
        shape = (abs(x2 - x1) + 1, abs(y2 - y1) + 1, abs(z2 - z1) + 1)
        choice = self.rng.choice(len(ids), size=shape, p=p)
        self._write(x1, y1, z1, x2, y2, z2, ids[choice])

    # ---------------------------------------------------------- vectorized
    def get_region(self, x1, y1, z1, x2, y2, z2):
        """Block ids (0 = unset, 1 = air) for a region as a uint16 array (nx, ny, nz)."""
        x1, x2 = sorted((x1, x2)); y1, y2 = sorted((y1, y2)); z1, z2 = sorted((z1, z2))
        out = np.zeros((x2 - x1 + 1, y2 - y1 + 1, z2 - z1 + 1), dtype=np.uint16)
        ys = slice(y1 - self.y_min, y2 - self.y_min + 1)
        for tx in range(x1 // T, x2 // T + 1):
            ax1, ax2 = max(x1, tx * T), min(x2, tx * T + T - 1)
            for tz in range(z1 // T, z2 // T + 1):
                tile = self.tiles.get((tx, tz))
                if tile is None:
                    continue
                az1, az2 = max(z1, tz * T), min(z2, tz * T + T - 1)
                out[ax1 - x1:ax2 - x1 + 1, :, az1 - z1:az2 - z1 + 1] = \
                    tile[ax1 - tx * T:ax2 - tx * T + 1, ys, az1 - tz * T:az2 - tz * T + 1]
        return out

    def fill_where(self, x1, y1, z1, x2, y2, z2, func, block, only_empty=False):
        """Paint `block` wherever func(X, y, Z) is True, evaluated layer by layer.
        X is shape (nx,1), Z is (1,nz) (open grids), y is an int. Return a bool array
        broadcastable to (nx, nz). Memory-light even for 400x400 footprints."""
        x1, x2 = sorted((x1, x2)); y1, y2 = sorted((y1, y2)); z1, z2 = sorted((z1, z2))
        bid = self.register(block)
        X = np.arange(x1, x2 + 1)[:, None]
        Z = np.arange(z1, z2 + 1)[None, :]
        nx, nz = x2 - x1 + 1, z2 - z1 + 1
        for y in range(y1, y2 + 1):
            m = np.broadcast_to(np.asarray(func(X, y, Z), dtype=bool), (nx, nz))
            if only_empty and m.any():
                cur = self.get_region(x1, y, z1, x2, y, z2)[:, 0, :]
                m = m & ((cur == 0) | (cur == AIR_ID))
            if m.any():
                self._write(x1, y, z1, x2, y, z2, bid, m[:, None, :])

    def cylinder(self, cx, y1, cz, r, y2, block, hollow=False, thickness=1):
        lim = r * r + r
        inner = (r - thickness) ** 2 + (r - thickness)

        def f(X, y, Z):
            d2 = (X - cx) ** 2 + (Z - cz) ** 2
            return (d2 <= lim) & (d2 > inner) if hollow else d2 <= lim
        self.fill_where(cx - r, y1, cz - r, cx + r, y2, cz + r, f, block)

    def ring(self, cx, y1, cz, r_in, r_out, y2, block):
        """Annulus between r_in (exclusive) and r_out (inclusive)."""
        def f(X, y, Z):
            d2 = (X - cx) ** 2 + (Z - cz) ** 2
            return (d2 <= r_out * r_out + r_out) & (d2 > r_in * r_in + r_in)
        self.fill_where(cx - r_out, y1, cz - r_out, cx + r_out, y2, cz + r_out, f, block)

    def tapered_cylinder(self, cx, y1, cz, y2, r_bottom, r_top, block, hollow=False, thickness=1):
        """Cone / frustum: radius interpolates linearly from r_bottom (y1) to r_top (y2)."""
        rmax = max(r_bottom, r_top)
        span = max(y2 - y1, 1)

        def f(X, y, Z):
            r = r_bottom + (r_top - r_bottom) * (y - y1) / span
            d2 = (X - cx) ** 2 + (Z - cz) ** 2
            m = d2 <= r * r + r
            if hollow:
                m &= d2 > (r - thickness) ** 2 + (r - thickness)
            return m
        self.fill_where(cx - rmax, y1, cz - rmax, cx + rmax, y2, cz + rmax, f, block)

    def dome(self, cx, cy, cz, r, block, hollow=True, thickness=1):
        """Upper hemisphere centred on (cx, cy, cz)."""
        def f(X, y, Z):
            d2 = (X - cx) ** 2 + (y - cy) ** 2 + (Z - cz) ** 2
            m = d2 <= r * r + r * 0.5
            if hollow:
                m &= d2 > (r - thickness) ** 2
            return m
        self.fill_where(cx - r, cy, cz - r, cx + r, cy + r, cz + r, f, block)

    def heightfield(self, x1, z1, x2, z2, y_base, height_fn, block):
        """Fill columns from y_base up to height_fn(X, Z) (ints, array-valued)."""
        x1, x2 = sorted((x1, x2)); z1, z2 = sorted((z1, z2))
        X = np.arange(x1, x2 + 1)[:, None]
        Z = np.arange(z1, z2 + 1)[None, :]
        H = np.broadcast_to(np.floor(height_fn(X, Z)).astype(int), (x2 - x1 + 1, z2 - z1 + 1))
        top = int(H.max())
        if top < y_base:
            return
        bid = self.register(block)
        for y in range(y_base, top + 1):
            m = H >= y
            if m.any():
                self._write(x1, y, z1, x2, y, z2, bid, m[:, None, :])

    # ---------------------------------------------------------------- prefabs
    def stamp(self, src, x, y, z, rot=0, mirror=False, include_air=True):
        """Copy another BigBuild (a reusable module) into this one.

        src's local (0,0,0) lands at (x,y,z). rot = number of 90-degree clockwise turns
        (seen from above); mirror flips east<->west first. Directional block states are
        rotated too, so stairs, doors, logs and fences stay correct.
        include_air=False leaves existing blocks where the prefab has air."""
        lut = np.zeros(len(src.names), dtype=np.uint16)
        for i, n in enumerate(src.names):
            if i >= 1:
                lut[i] = AIR_ID if i == AIR_ID else self.register(transform_block(n, rot % 4, mirror))
        xs, ys, zs, vs = [], [], [], []
        for (tx, tz), a in src.tiles.items():
            idx = np.argwhere(a > (0 if include_air else 1))
            if len(idx):
                xs.append(idx[:, 0] + tx * T); ys.append(idx[:, 1] + src.y_min)
                zs.append(idx[:, 2] + tz * T); vs.append(a[idx[:, 0], idx[:, 1], idx[:, 2]])
        if not xs:
            return
        X = np.concatenate(xs); Y = np.concatenate(ys); Z = np.concatenate(zs)
        V = lut[np.concatenate(vs)]
        if mirror:
            X = -X
        for _ in range(rot % 4):
            X, Z = -Z, X
        X = X + x; Y = Y + y; Z = Z + z
        if Y.min() < self.y_min or Y.max() > self.y_max:
            raise ValueError(f"stamp spans y {Y.min()}..{Y.max()}, outside {self.y_min}..{self.y_max}")
        tx_, tz_ = X // T, Z // T
        keys = np.stack([tx_, tz_], axis=1)
        uniq, inv = np.unique(keys, axis=0, return_inverse=True)
        inv = inv.ravel()
        for g, (tx, tz) in enumerate(uniq):
            sel = inv == g
            tile = self._tile(int(tx), int(tz))
            tile[X[sel] - tx * T, Y[sel] - self.y_min, Z[sel] - tz * T] = V[sel]

    def stamp_many(self, src, placements, **kw):
        """placements: iterable of (x, y, z) or (x, y, z, rot) or (x, y, z, rot, mirror)."""
        for p in placements:
            self.stamp(src, *p, **kw)

    # ------------------------------------------------------------ inspection
    def bounds(self):
        lo = [10**9] * 3; hi = [-10**9] * 3
        for (tx, tz), a in self.tiles.items():
            occ = a > 0
            if not occ.any():
                continue
            xs = np.nonzero(occ.any(axis=(1, 2)))[0]
            ys = np.nonzero(occ.any(axis=(0, 2)))[0]
            zs = np.nonzero(occ.any(axis=(0, 1)))[0]
            lo = [min(lo[0], tx * T + xs[0]), min(lo[1], self.y_min + ys[0]), min(lo[2], tz * T + zs[0])]
            hi = [max(hi[0], tx * T + xs[-1]), max(hi[1], self.y_min + ys[-1]), max(hi[2], tz * T + zs[-1])]
        return tuple(lo), tuple(hi)

    def materials(self):
        counts = np.zeros(len(self.names), dtype=np.int64)
        for a in self.tiles.values():
            counts += np.bincount(a.ravel(), minlength=len(self.names))[:len(self.names)]
        rows = [(self.names[i], int(counts[i])) for i in range(2, len(self.names)) if counts[i]]
        return sorted(rows, key=lambda r: -r[1])

    def summary(self, top=15):
        lo, hi = self.bounds()
        size = tuple(h - l + 1 for l, h in zip(lo, hi))
        total = sum(n for _, n in self.materials())
        lines = [f"size (x,y,z): {size[0]} x {size[1]} x {size[2]}   solid blocks: {total:,}",
                 f"tiles: {len(self.tiles)}   distinct blocks: {len(self.names) - 2}"]
        lines += [f"{n:12,d}  {b}" for b, n in self.materials()[:top]]
        return "\n".join(lines)

    # --------------------------------------------------------------- render
    def _palette_lut(self):
        lut = np.zeros((len(self.names), 3), dtype=np.uint8)
        for i, n in enumerate(self.names):
            lut[i] = block_color(n) if i >= 2 else (0, 0, 0)
        return lut

    def render_top(self, path, px=2, sky=(18, 24, 40), max_side=640):
        """Top-down PNG: block colour shaded by height and slope."""
        _save_png(self._top_img(px, sky), path, max_side)
        return path

    def _top_img(self, px=2, sky=(18, 24, 40)):
        from PIL import Image
        lo, hi = self.bounds()
        w, d = hi[0] - lo[0] + 1, hi[2] - lo[2] + 1
        col = np.zeros((w, d, 3), dtype=np.float32); col[:] = sky
        H = np.full((w, d), np.nan, dtype=np.float32)
        lut = self._palette_lut()
        for (tx, tz), a in self.tiles.items():
            occ = a > 1
            has = occ.any(axis=1)
            top = self.ny - 1 - np.argmax(occ[:, ::-1, :], axis=1)
            ids = np.take_along_axis(a, top[:, None, :], axis=1)[:, 0, :]
            gx = tx * T - lo[0]; gz = tz * T - lo[2]
            xs0, zs0 = max(gx, 0), max(gz, 0)
            xs1, zs1 = min(gx + T, w), min(gz + T, d)
            if xs1 <= xs0 or zs1 <= zs0:
                continue
            sub = (slice(xs0 - gx, xs1 - gx), slice(zs0 - gz, zs1 - gz))
            hs = has[sub]
            cs = lut[ids[sub]].astype(np.float32)
            hh = (top[sub] + self.y_min).astype(np.float32)
            region = (slice(xs0, xs1), slice(zs0, zs1))
            col[region][hs] = cs[hs]
            Hr = H[region]; Hr[hs] = hh[hs]; H[region] = Hr
        valid = ~np.isnan(H)
        if valid.any():
            hmin, hmax = np.nanmin(H), np.nanmax(H)
            Hf = np.where(valid, H, hmin)
            gx_, gz_ = np.gradient(Hf)
            shade = 0.65 + 0.35 * (Hf - hmin) / max(hmax - hmin, 1) + 0.08 * (gx_ + gz_)
            col = np.where(valid[..., None], col * np.clip(shade, 0.3, 1.3)[..., None], col)
        img = np.clip(col, 0, 255).astype(np.uint8).transpose(1, 0, 2)  # rows = z
        img = np.repeat(np.repeat(img, px, axis=0), px, axis=1)
        return img

    def render_section(self, path, axis="z", index=0, px=3, sky=(18, 24, 40), max_side=640):
        """Vertical cross-section PNG through the plane axis=index (axis 'z' or 'x')."""
        from PIL import Image
        lo, hi = self.bounds()
        lut = self._palette_lut()
        if axis == "z":
            u0, u1 = lo[0], hi[0]
        else:
            u0, u1 = lo[2], hi[2]
        img = np.zeros((u1 - u0 + 1, self.ny, 3), dtype=np.uint8); img[:] = sky
        for (tx, tz), a in self.tiles.items():
            if axis == "z":
                if index // T != tz:
                    continue
                sl = a[:, :, index % T]; start = tx * T
            else:
                if index // T != tx:
                    continue
                sl = a[index % T, :, :].T; start = tz * T
            n = sl.shape[0]
            s0, s1 = max(start, u0), min(start + n, u1 + 1)
            if s1 <= s0:
                continue
            part = sl[s0 - start:s1 - start]
            colors = lut[part]
            mask = part > 1
            dst = img[s0 - u0:s1 - u0]
            dst[mask] = colors[mask]
        img = img[:, ::-1, :].transpose(1, 0, 2)  # rows = y (top = high)
        img = np.repeat(np.repeat(img, px, axis=0), px, axis=1)
        _save_png(img, path, max_side)
        return path

    # ------------------------------------------------------ all-angle views
    def elevation_maps(self):
        """Orthographic views from the four sides. Returns {dir: (ids, hit, depth)} where
        arrays are indexed [horizontal, vertical-from-bottom] as seen by a viewer standing
        outside that side (south view: east is right; north: flipped; east view: north is
        right; west view: south is right). depth = blocks from the nearest face."""
        lo, hi = self.bounds()
        reg = self.get_region(*lo, *hi)
        occ = reg > 1
        out = {}
        for name, axis, rev in [("south", 2, True), ("north", 2, False),
                                ("east", 0, True), ("west", 0, False)]:
            o = occ[:, :, ::-1] if (axis == 2 and rev) else occ[:, :, :]
            r = reg[:, :, ::-1] if (axis == 2 and rev) else reg[:, :, :]
            if axis == 0:
                o = np.swapaxes(occ, 0, 2); r = np.swapaxes(reg, 0, 2)
                if rev:
                    o = o[:, :, ::-1]; r = r[:, :, ::-1]
            hit = o.any(axis=2)
            idx = np.argmax(o, axis=2)
            ids = np.take_along_axis(r, idx[:, :, None], axis=2)[:, :, 0]
            if name in ("north",):
                hit, idx, ids = hit[::-1], idx[::-1], ids[::-1]
            if name == "east":
                hit, idx, ids = hit[::-1], idx[::-1], ids[::-1]
            out[name] = (ids, hit, idx)
        return out

    def render_elevations(self, path, max_side=900, px=2, sky=(18, 24, 40)):
        """One contact-sheet PNG: top view plus south, north, east, west elevations,
        shaded by depth. A cheap way to check the build from every side."""
        from PIL import Image, ImageDraw
        lut = self._palette_lut()
        panels = [("top", self._top_img(px, sky))]
        for name, (ids, hit, depth) in self.elevation_maps().items():
            dmax = max(int(depth[hit].max()), 1) if hit.any() else 1
            col = lut[ids].astype(np.float32) * (1.0 - 0.5 * depth[..., None] / dmax)
            col[~hit] = sky
            img = np.clip(col, 0, 255).astype(np.uint8)[:, ::-1, :].transpose(1, 0, 2)
            panels.append((name, np.repeat(np.repeat(img, px, axis=0), px, axis=1)))
        cell = max_side // 3
        sheet = Image.new("RGB", (cell * 3, cell * 2), sky)
        d = ImageDraw.Draw(sheet)
        for i, (name, arr) in enumerate(panels):
            im = Image.fromarray(arr)
            s = min((cell - 4) / im.width, (cell - 14) / im.height)
            im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.NEAREST)
            ox, oy = (i % 3) * cell + 2, (i // 3) * cell + 12
            sheet.paste(im, (ox, oy))
            d.text((ox, oy - 11), name, fill=(220, 220, 220))
        sheet.save(path)
        return path

    # ---------------------------------------------------------------- export
    @staticmethod
    def _greedy2d(m):
        """Greedy rectangles over a 2D bool array (mutated). Returns (x1,x2,z1,z2) list."""
        rects = []
        nz = m.shape[1]; nx = m.shape[0]
        while True:
            idx = int(m.argmax())
            x, z = divmod(idx, nz)
            if not m[x, z]:
                break
            row = m[x, z:]
            ln = len(row) if row.all() else int(np.argmin(row))
            z2 = z + ln - 1
            x2 = x
            while x2 + 1 < nx and m[x2 + 1, z:z2 + 1].all():
                x2 += 1
            m[x:x2 + 1, z:z2 + 1] = False
            rects.append((x, x2, z, z2))
        return rects

    def _compile_tile(self, arr, skip_air):
        """Return [(x1,y1,z1,x2,y2,z2,bid)] in tile-local coords (y is array index)."""
        out = []
        present = np.unique(arr)
        present = present[present > 0]
        if skip_air:
            present = present[present != AIR_ID]
        for bid in present:
            mask3 = arr == bid
            layer_any = mask3.any(axis=(0, 2))
            open_ = {}

            def emit(rect, ys, ye):
                x1, x2, z1, z2 = rect
                area = (x2 - x1 + 1) * (z2 - z1 + 1)
                step = max(FILL_LIMIT // area, 1)
                y = ys
                while y <= ye:
                    top = min(y + step - 1, ye)
                    out.append((x1, y, z1, x2, top, z2, int(bid)))
                    y = top + 1

            for yi in range(self.ny):
                rects = set(self._greedy2d(mask3[:, yi, :].copy())) if layer_any[yi] else set()
                for r in [r for r in open_ if r not in rects]:
                    emit(r, open_.pop(r), yi - 1)
                for r in rects:
                    if r not in open_:
                        open_[r] = yi
            for r, ys in open_.items():
                emit(r, ys, self.ny - 1)
        return out

    def commands(self, origin=(0, 0, 0), relative=True, clear_first=False):
        """All commands as a list. relative=True: '~' coordinates where build-local
        `origin` maps to the executing position. relative=False: world coords with
        `origin` = world position of local (0,0,0)."""
        ox, oy, oz = origin
        def c(x, y, z):
            if relative:
                f = lambda v, o: "~" if v == o else f"~{v - o}"
                return f"{f(x, ox)} {f(y, oy)} {f(z, oz)}"
            return f"{x + ox} {y + oy} {z + oz}"
        cmds = []
        if clear_first:
            lo, hi = self.bounds()
            step = 8
            for y in range(lo[1], hi[1] + 1, step):
                ye = min(y + step - 1, hi[1])
                # keep each fill under the volume cap by slicing along x
                w = max(FILL_LIMIT // ((ye - y + 1) * (hi[2] - lo[2] + 1)), 1)
                for x in range(lo[0], hi[0] + 1, w):
                    cmds.append(f"fill {c(x, y, lo[2])} {c(min(x + w - 1, hi[0]), ye, hi[2])} minecraft:air")
        for (tx, tz) in sorted(self.tiles):
            arr = self.tiles[(tx, tz)]
            for (x1, y1, z1, x2, y2, z2, bid) in self._compile_tile(arr, skip_air=clear_first):
                a = (tx * T + x1, y1 + self.y_min, tz * T + z1)
                e = (tx * T + x2, y2 + self.y_min, tz * T + z2)
                if a == e:
                    cmds.append(f"setblock {c(*a)} {self.names[bid]}")
                else:
                    cmds.append(f"fill {c(*a)} {c(*e)} {self.names[bid]}")
        return cmds

    def save_function(self, path, origin=(0, 0, 0), relative=True, clear_first=False):
        """Single .mcfunction file for SMALL/MEDIUM builds (a few thousand commands).
        Use save_sharded for anything bigger (65,536-command chain limit)."""
        cmds = self.commands(origin, relative, clear_first)
        if len(cmds) > 30000:
            raise ValueError(f"{len(cmds)} commands is too many for one function; use save_sharded")
        with open(path, "w") as f:
            f.write(f"# generated by mcbig, {len(cmds)} commands\n" + "\n".join(cmds) + "\n")
        return len(cmds)

    def save_sharded(self, out_dir, namespace="build", name="build", origin=(0, 0, 0),
                     max_commands=4000, load_delay=40, step_delay=2, clear_first=False,
                     function_dir="function", pack_format=48, pack_name=None,
                     world_y_min=-64, world_y_max=319, forceload=True):
        """Write a datapack that builds everything step by step.

        origin: world (x,y,z) of build-local (0,0,0).
        function_dir: 'function' for Minecraft 1.21+, 'functions' for 1.20.6 and earlier.
        pack_format: datapack format number for the target version (change if the game
                     reports the pack as incompatible).
        Run in game:  /datapack enable "file/<pack_name>"  then  /function <ns>:<name>/start
        """
        ox, oy, oz = origin
        lo, hi = self.bounds()
        if hi[1] + oy > world_y_max or lo[1] + oy < world_y_min:
            raise ValueError(f"build spans world y {lo[1] + oy}..{hi[1] + oy}, outside {world_y_min}..{world_y_max}")
        pack_name = pack_name or f"{namespace}_{name}"
        root = os.path.join(out_dir, pack_name)
        fdir = os.path.join(root, "data", namespace, function_dir, name)
        os.makedirs(fdir, exist_ok=True)
        with open(os.path.join(root, "pack.mcmeta"), "w") as f:
            json.dump({"pack": {"pack_format": pack_format,
                                "description": f"{name} generated by mcbig"}}, f, indent=2)

        steps = []   # each: dict(cmds=[...], kind=...)
        tile_keys = sorted(self.tiles)
        total_cmds = 0
        built_tiles = []
        for key in tile_keys:
            tx, tz = key
            arr = self.tiles[key]
            if not (arr > 0).any():
                continue
            boxes = self._compile_tile(arr, skip_air=clear_first)
            cmds = []
            bx0, bz0 = tx * T + ox, tz * T + oz
            if clear_first:
                occ_y = np.nonzero((arr > 0).any(axis=(0, 2)))[0]
                ya, yb = int(occ_y[0]), int(occ_y[-1])
                step = max(FILL_LIMIT // (T * T), 1)
                y = ya
                while y <= yb:
                    top = min(y + step - 1, yb)
                    cmds.append(f"fill {bx0} {y + self.y_min + oy} {bz0} {bx0 + T - 1} "
                                f"{top + self.y_min + oy} {bz0 + T - 1} minecraft:air")
                    y = top + 1
            for (x1, y1, z1, x2, y2, z2, bid) in boxes:
                b = self.names[bid]
                a = (bx0 + x1, y1 + self.y_min + oy, bz0 + z1)
                if (x1, y1, z1) == (x2, y2, z2):
                    cmds.append(f"setblock {a[0]} {a[1]} {a[2]} {b}")
                else:
                    cmds.append(f"fill {a[0]} {a[1]} {a[2]} {bx0 + x2} {y2 + self.y_min + oy} {bz0 + z2} {b}")
            total_cmds += len(cmds)
            built_tiles.append((key, cmds, (bx0, bz0, bx0 + T - 1, bz0 + T - 1)))

        n_tiles = len(built_tiles)
        for i, (key, cmds, (x1, z1, x2, z2)) in enumerate(built_tiles, 1):
            msg = f'tellraw @a {{"text":"[{name}] tile {i}/{n_tiles}","color":"aqua"}}'
            load_cmds = [msg]
            if forceload:
                load_cmds.insert(0, f"forceload add {x1} {z1} {x2} {z2}")
            steps.append({"cmds": load_cmds, "delay": load_delay if forceload else 1})
            parts = [cmds[j:j + max_commands] for j in range(0, len(cmds), max_commands)]
            for pi, part in enumerate(parts):
                part = list(part)
                if pi == len(parts) - 1 and forceload:
                    part.append(f"forceload remove {x1} {z1} {x2} {z2}")
                steps.append({"cmds": part, "delay": step_delay})
        steps.append({"cmds": [f'tellraw @a {{"text":"[{name}] finished","color":"green"}}'], "delay": 0})

        for k, s in enumerate(steps):
            lines = list(s["cmds"])
            if k + 1 < len(steps):
                lines.append(f"schedule function {namespace}:{name}/step_{k + 1:05d} {s['delay']}t")
            with open(os.path.join(fdir, f"step_{k:05d}.mcfunction"), "w") as f:
                f.write("\n".join(lines) + "\n")
        with open(os.path.join(fdir, "start.mcfunction"), "w") as f:
            f.write(f"function {namespace}:{name}/step_00000\n")

        ticks = sum(s["delay"] for s in steps)
        stats = {"pack": root, "steps": len(steps), "tiles": n_tiles, "commands": total_cmds,
                 "min_scheduled_seconds": round(ticks / 20, 1)}
        return stats
