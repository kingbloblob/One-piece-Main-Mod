"""mcbuild: design Minecraft builds with macros, export an efficient .mcfunction.

Usage (from a build script):
    import sys; sys.path.insert(0, "<skill>/scripts")
    from mcbuild import Build, Palette
    pal = Palette.load("palette.json")          # optional, validates modded IDs
    b = Build(palette=pal, seed=7)
    b.box(0, 0, 0, 12, 0, 8, "minecraft:stone_bricks")      # solid
    b.hollow_box(0, 1, 0, 12, 5, 8, "mymod:copper_bricks")  # walls+floor+ceiling
    b.save("house.mcfunction")
    print(b.summary()); print(b.layer(1))

Coordinates are integers (x east+, y up+, z south+). Everything is painted into a
voxel map first (later paint wins), then compiled into as few /fill commands as
possible at save time. Output uses ~ relative coordinates by default, so the
build appears relative to whoever runs the function.
"""
import difflib
import json
import math
import random
from collections import Counter

FILL_LIMIT = 32768  # vanilla /fill volume cap
AIR = "minecraft:air"


def _norm(block):
    """'stone' -> 'minecraft:stone'; keeps [state=...] suffix."""
    block = block.strip()
    base, sep, state = block.partition("[")
    if ":" not in base:
        base = "minecraft:" + base
    return base + (sep + state if sep else "")


def _id(block):
    return block.partition("[")[0]


class Palette:
    """Allowed modded blocks. Vanilla (minecraft:) IDs are not checked offline."""

    def __init__(self, data=None):
        self.data = data or {"blocks": {}}
        self.blocks = self.data.get("blocks", {})

    @classmethod
    def load(cls, path):
        with open(path) as f:
            return cls(json.load(f))

    def check(self, block):
        bid = _id(block)
        ns = bid.split(":")[0]
        if ns == "minecraft" or bid in self.blocks:
            return
        close = difflib.get_close_matches(bid, list(self.blocks), n=4)
        raise ValueError(
            f"Unknown modded block '{bid}'. Not in palette."
            + (f" Did you mean: {', '.join(close)}?" if close else "")
        )


class Build:
    def __init__(self, palette=None, seed=0):
        self.vox = {}  # (x,y,z) -> block string
        self.palette = palette
        self.rng = random.Random(seed)

    # ---------- primitives ----------
    def set(self, x, y, z, block):
        block = _norm(block)
        if self.palette:
            self.palette.check(block)
        self.vox[(x, y, z)] = block

    def fill(self, x1, y1, z1, x2, y2, z2, block):
        block = _norm(block)
        if self.palette:
            self.palette.check(block)
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                for z in range(min(z1, z2), max(z1, z2) + 1):
                    self.vox[(x, y, z)] = block

    def clear(self, x1, y1, z1, x2, y2, z2):
        """Carve air (doors, windows, interiors)."""
        self.fill(x1, y1, z1, x2, y2, z2, AIR)

    def mix(self, x1, y1, z1, x2, y2, z2, blocks, weights=None):
        """Fill a region with randomly mixed blocks (breaks up flat texture)."""
        blocks = [_norm(b) for b in blocks]
        if self.palette:
            for b in blocks:
                self.palette.check(b)
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                for z in range(min(z1, z2), max(z1, z2) + 1):
                    self.vox[(x, y, z)] = self.rng.choices(blocks, weights)[0]

    # ---------- macros ----------
    def box(self, x1, y1, z1, x2, y2, z2, block):
        self.fill(x1, y1, z1, x2, y2, z2, block)

    def hollow_box(self, x1, y1, z1, x2, y2, z2, block):
        """Shell with 1-thick walls, floor and ceiling; interior is air."""
        self.fill(x1, y1, z1, x2, y2, z2, block)
        if x2 - x1 >= 2 and y2 - y1 >= 2 and z2 - z1 >= 2:
            lo = (min(x1, x2) + 1, min(y1, y2) + 1, min(z1, z2) + 1)
            hi = (max(x1, x2) - 1, max(y1, y2) - 1, max(z1, z2) - 1)
            self.clear(*lo, *hi)

    def walls(self, x1, y1, z1, x2, y2, z2, block):
        """Four walls only (no floor/ceiling), interior untouched."""
        x1, x2 = sorted((x1, x2)); z1, z2 = sorted((z1, z2))
        self.fill(x1, y1, z1, x2, y2, z1, block)
        self.fill(x1, y1, z2, x2, y2, z2, block)
        self.fill(x1, y1, z1, x1, y2, z2, block)
        self.fill(x2, y1, z1, x2, y2, z2, block)

    def pillar(self, x, y1, z, y2, block):
        self.fill(x, y1, z, x, y2, z, block)

    def _disc_rows(self, r, hollow):
        """Yield (dz, [(dx1,dx2),...]) spans for a circle of radius r."""
        lim = r * r + r
        inner = (r - 1) * (r - 1) + (r - 1)
        for dz in range(-r, r + 1):
            xs = [dx for dx in range(-r, r + 1) if dx * dx + dz * dz <= lim]
            if not xs:
                continue
            if not hollow or r < 2:
                yield dz, [(xs[0], xs[-1])]
            else:
                ring = [dx for dx in xs if dx * dx + dz * dz > inner]
                spans, start, prev = [], None, None
                for dx in ring:
                    if start is None:
                        start = prev = dx
                    elif dx == prev + 1:
                        prev = dx
                    else:
                        spans.append((start, prev)); start = prev = dx
                if start is not None:
                    spans.append((start, prev))
                yield dz, spans

    def cylinder(self, cx, y1, cz, r, y2, block, hollow=False):
        for dz, spans in self._disc_rows(r, hollow):
            for a, b in spans:
                self.fill(cx + a, y1, cz + dz, cx + b, y2, cz + dz, block)

    def dome(self, cx, cy, cz, r, block, hollow=True):
        """Upper hemisphere centred at (cx,cy,cz)."""
        for dy in range(0, r + 1):
            ro = math.sqrt(max(r * r - dy * dy, 0))
            ri = math.sqrt(max((r - 1) ** 2 - dy * dy, 0)) if hollow else -1.0
            for dz in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    d = math.sqrt(dx * dx + dz * dz)
                    if d <= ro + 0.3 and (not hollow or d > ri + 0.3):
                        self.set(cx + dx, cy + dy, cz + dz, block)

    def gable_roof(self, x1, z1, x2, z2, y, stairs, ridge=None, ridge_axis="x",
                   gable_fill=None, overhang=0):
        """Stair roof starting at height y (first layer sits ON y).

        ridge_axis 'x': ridge runs along x, slopes fall toward north/south.
        ridge_axis 'z': ridge runs along z, slopes fall toward west/east.
        stairs: stair block id (no state). ridge: block for the ridge line if the
        span is odd (defaults to the stairs' matching slab guess: use a full block).
        gable_fill: block to close the triangular end walls.
        overhang: extend the eaves by N blocks on the sloping sides.
        """
        x1, x2 = sorted((x1, x2)); z1, z2 = sorted((z1, z2))
        sid = _id(_norm(stairs))
        if ridge_axis == "x":
            lo, hi = z1 - overhang, z2 + overhang
        else:
            lo, hi = x1 - overhang, x2 + overhang
        i = 0
        while lo + i <= hi - i:
            a, b, yy = lo + i, hi - i, y + i
            if ridge_axis == "x":
                if a == b:
                    self.fill(x1, yy, a, x2, yy, a, ridge or sid.replace("_stairs", ""))
                else:
                    self.fill(x1, yy, a, x2, yy, a, f"{sid}[facing=south,half=bottom]")
                    self.fill(x1, yy, b, x2, yy, b, f"{sid}[facing=north,half=bottom]")
                if gable_fill and a < b:
                    for gx in (x1, x2):
                        if a + 1 <= b - 1:
                            self.fill(gx, yy, a + 1, gx, yy, b - 1, gable_fill)
            else:
                if a == b:
                    self.fill(a, yy, z1, a, yy, z2, ridge or sid.replace("_stairs", ""))
                else:
                    self.fill(a, yy, z1, a, yy, z2, f"{sid}[facing=east,half=bottom]")
                    self.fill(b, yy, z1, b, yy, z2, f"{sid}[facing=west,half=bottom]")
                if gable_fill and a < b:
                    for gz in (z1, z2):
                        if a + 1 <= b - 1:
                            self.fill(a + 1, yy, gz, b - 1, yy, gz, gable_fill)
            i += 1

    def mirror_x(self, about_x):
        """Mirror everything painted so far across x = about_x (symmetry).
        Fixes stair/facing east<->west."""
        add = {}
        for (x, y, z), b in self.vox.items():
            nx = 2 * about_x - x
            if nx != x:
                add[(nx, y, z)] = (b.replace("facing=east", "facing=@@")
                                    .replace("facing=west", "facing=east")
                                    .replace("facing=@@", "facing=west"))
        for k, v in add.items():
            self.vox.setdefault(k, v)

    # ---------- inspection ----------
    def bounds(self):
        xs, ys, zs = zip(*self.vox)
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))

    def materials(self):
        c = Counter(_id(b) for b in self.vox.values() if _id(b) != AIR)
        return c.most_common()

    def summary(self):
        lo, hi = self.bounds()
        size = tuple(h - l + 1 for l, h in zip(lo, hi))
        lines = [f"size (x,y,z): {size[0]} x {size[1]} x {size[2]}"]
        lines += [f"{n:6d}  {b}" for b, n in self.materials()]
        return "\n".join(lines)

    def layer(self, y):
        """ASCII top-down view of one horizontal layer (north is up)."""
        lo, hi = self.bounds()
        ids = [b for b, _ in self.materials()]
        sym = {b: "#@%&*+=-:~^ovwxyz0123456789"[i % 27] for i, b in enumerate(ids)}
        rows = []
        for z in range(lo[2], hi[2] + 1):
            row = ""
            for x in range(lo[0], hi[0] + 1):
                b = self.vox.get((x, y, z))
                row += "." if b is None or _id(b) == AIR else sym[_id(b)]
            rows.append(row)
        legend = "  ".join(f"{s}={b}" for b, s in sym.items())
        return f"layer y={y}\n" + "\n".join(rows) + "\n" + legend

    def side(self, axis="z"):
        """ASCII side view (front elevation) projected along an axis, y up."""
        lo, hi = self.bounds()
        ids = [b for b, _ in self.materials()]
        sym = {b: "#@%&*+=-:~^ovwxyz0123456789"[i % 27] for i, b in enumerate(ids)}
        rows = []
        for y in range(hi[1], lo[1] - 1, -1):
            row = ""
            rng = range(lo[0], hi[0] + 1) if axis == "z" else range(lo[2], hi[2] + 1)
            for u in rng:
                cell = "."
                depth = range(lo[2], hi[2] + 1) if axis == "z" else range(lo[0], hi[0] + 1)
                for d in depth:
                    key = (u, y, d) if axis == "z" else (d, y, u)
                    b = self.vox.get(key)
                    if b and _id(b) != AIR:
                        cell = sym[_id(b)]
                        break
                row += cell
            rows.append(row)
        return "\n".join(rows)

    # ---------- export ----------
    def _compile(self, skip_air):
        remaining = {}
        for k, b in self.vox.items():
            if skip_air and _id(b) == AIR:
                continue
            remaining.setdefault(b, set()).add(k)
        boxes = []
        for block, pts in remaining.items():
            todo = set(pts)
            for (x, y, z) in sorted(pts, key=lambda p: (p[1], p[2], p[0])):
                if (x, y, z) not in todo:
                    continue
                x2 = x
                while (x2 + 1, y, z) in todo and (x2 + 1 - x + 1) <= FILL_LIMIT:
                    x2 += 1
                z2 = z
                while all((xx, y, z2 + 1) in todo for xx in range(x, x2 + 1)) \
                        and (x2 - x + 1) * (z2 + 1 - z + 1) <= FILL_LIMIT:
                    z2 += 1
                y2 = y
                while all((xx, y2 + 1, zz) in todo
                          for xx in range(x, x2 + 1) for zz in range(z, z2 + 1)) \
                        and (x2 - x + 1) * (z2 - z + 1) * (y2 + 1 - y + 1) <= FILL_LIMIT:
                    y2 += 1
                for xx in range(x, x2 + 1):
                    for yy in range(y, y2 + 1):
                        for zz in range(z, z2 + 1):
                            todo.discard((xx, yy, zz))
                boxes.append((x, y, z, x2, y2, z2, block))
        return boxes

    def commands(self, relative=True, origin=(0, 0, 0), clear_bbox=False):
        ox, oy, oz = origin

        def c(x, y, z):
            if relative:
                f = lambda v, o: "~" if v - o == 0 else f"~{v - o}"
                return f"{f(x, ox)} {f(y, oy)} {f(z, oz)}"
            return f"{x} {y} {z}"

        cmds = []
        if clear_bbox:
            lo, hi = self.bounds()
            # split clear region to respect the fill limit
            cmds += self._clear_cmds(lo, hi, c)
        for (x, y, z, x2, y2, z2, b) in self._compile(skip_air=clear_bbox):
            if (x, y, z) == (x2, y2, z2):
                cmds.append(f"setblock {c(x, y, z)} {b}")
            else:
                cmds.append(f"fill {c(x, y, z)} {c(x2, y2, z2)} {b}")
        return cmds

    def _clear_cmds(self, lo, hi, c):
        out = []
        for y in range(lo[1], hi[1] + 1):
            # one layer at a time keeps volume under the cap for builds up to ~180x180
            out.append(f"fill {c(lo[0], y, lo[2])} {c(hi[0], y, hi[2])} minecraft:air")
        return out

    def save(self, path, relative=True, origin=(0, 0, 0), clear_bbox=False, header=None):
        cmds = self.commands(relative, origin, clear_bbox)
        with open(path, "w") as f:
            f.write(f"# {header or 'Generated by mcbuild'}\n")
            f.write(f"# {len(cmds)} commands. Run with: /function <namespace>:<name>\n")
            f.write("\n".join(cmds) + "\n")
        return len(cmds)
