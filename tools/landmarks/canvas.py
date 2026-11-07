"""Canvas for the landmark rebuilds: kit.B (tools/worldgen) plus helpers for detailed, life-size builds.

1 block = 1 meter. +x is the "front" of a ship (bow). y=0 is the ground / sea level of the build unless noted.
"""
import math, sys
sys.path.insert(0, "/mnt/project-files/one-piece-mod/tools/worldgen")
from kit import *  # noqa: F401,F403  (B, AIR, FENCE, LANTERN, HANG, log, leaves, bed, ...)
from kit import B as _KitB

WATER = "minecraft:water[level=0]"
FACING = ("north", "south", "east", "west")
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


def stairs(block, facing, half="bottom", shape="straight"):
    return f"{block}[facing={facing},half={half},shape={shape},waterlogged=false]"


def slab(block, kind="bottom"):
    return f"{block}[type={kind},waterlogged=false]"


def wall(block):
    return f"{block}[east=none,north=none,south=none,up=true,waterlogged=false,west=none]"


def fence(wood):
    return FENCE.format(wood)


def pane_of(block):
    return f"{block}[east=false,north=false,south=false,west=false,waterlogged=false]"


def trapdoor(block, facing="north", half="top", open_="false"):
    return f"{block}[facing={facing},half={half},open={open_},powered=false,waterlogged=false]"


def lantern(hanging=False, soul=False):
    return f"minecraft:{'soul_' if soul else ''}lantern[hanging={'true' if hanging else 'false'},waterlogged=false]"


def door(block, facing, half, hinge="left"):
    return f"{block}[facing={facing},half={half},hinge={hinge},open=false,powered=false]"


def candle(color=None, n=1):
    c = f"{color}_candle" if color else "candle"
    return f"minecraft:{c}[candles={n},lit=true,waterlogged=false]"


# a 3x5 font for big block lettering on signs
FONT = {
    "A": ["010", "101", "111", "101", "101"], "B": ["110", "101", "110", "101", "110"], "C": ["011", "100", "100", "100", "011"],
    "D": ["110", "101", "101", "101", "110"], "E": ["111", "100", "110", "100", "111"], "F": ["111", "100", "110", "100", "100"],
    "G": ["011", "100", "101", "101", "011"], "H": ["101", "101", "111", "101", "101"], "I": ["111", "010", "010", "010", "111"],
    "J": ["001", "001", "001", "101", "010"], "K": ["101", "101", "110", "101", "101"], "L": ["100", "100", "100", "100", "111"],
    "M": ["101", "111", "111", "101", "101"], "N": ["110", "101", "101", "101", "101"], "O": ["010", "101", "101", "101", "010"],
    "P": ["110", "101", "110", "100", "100"], "Q": ["010", "101", "101", "110", "011"], "R": ["110", "101", "110", "101", "101"],
    "S": ["011", "100", "010", "001", "110"], "T": ["111", "010", "010", "010", "010"], "U": ["101", "101", "101", "101", "111"],
    "V": ["101", "101", "101", "101", "010"], "W": ["101", "101", "111", "111", "101"], "X": ["101", "101", "010", "101", "101"],
    "Y": ["101", "101", "010", "010", "010"], "Z": ["111", "001", "010", "100", "111"], " ": ["0", "0", "0", "0", "0"],
    "-": ["000", "000", "111", "000", "000"], "7": ["111", "001", "010", "010", "010"],
    "0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"], "2": ["110", "001", "010", "100", "111"],
    "3": ["110", "001", "010", "001", "110"], "4": ["101", "101", "111", "001", "001"], "5": ["111", "100", "110", "001", "110"],
    "6": ["011", "100", "110", "101", "010"], "8": ["010", "101", "010", "101", "010"], "9": ["010", "101", "011", "001", "110"],
    "'": ["1", "1", "0", "0", "0"],
}


def sail_belly(half, height):
    """How deep (in blocks) a square sail of this size bellies out in a good wind."""
    return max(2, int(round(0.28 * half + 0.12 * height)))


def sail_depth(u, s, belly):
    """Belly of a wind-filled square sail at u (-1..1 across) and s (0 at the yard, 1 at the foot): zero along the
    head and at the yard arms, deepest a little below the middle, and the foot still bowed out by about half."""
    across = max(0.0, 1 - u * u) ** 0.75
    down = math.sin(math.pi * 0.8 * s) / math.sin(math.pi * 0.4) if s < 0.625 else 1 - 0.42 * ((s - 0.625) / 0.375) ** 1.4
    return int(round(belly * across * min(1.0, down)))


class B(_KitB):
    def fill_if(self, x, y, z, s, only_empty=True):
        if not only_empty or (x, y, z) not in self.blocks or self.blocks[(x, y, z)] == AIR:
            self.set(x, y, z, s)

    def line(self, p0, p1, s):
        (x0, y0, z0), (x1, y1, z1) = p0, p1
        n = int(max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))) + 1
        for i in range(n + 1):
            t = i / max(1, n)
            self.set(round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), round(z0 + (z1 - z0) * t), s)

    def ellipse(self, cx, cz, rx, rz, y0, y1, s, hollow=False, thick=1.0):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            for z in range(int(cz - rz) - 1, int(cz + rz) + 2):
                d = math.hypot((x - cx) / max(rx, .01), (z - cz) / max(rz, .01))
                if d <= 1.0:
                    inner = math.hypot((x - cx) / max(rx - thick, .01), (z - cz) / max(rz - thick, .01)) <= 1.0
                    for y in range(y0, y1 + 1):
                        self.set(x, y, z, AIR if (hollow and inner) else s)

    def text(self, x, y, z, msg, s, axis="x", step=1, scale=1):
        """Big 3x5 letters. axis='x': letters run along +x on the plane z and read the right way round from the +z (south)
        side when step=1; for a face seen from -z start at the right (high x) end with step=-1. axis='z': step=1 reads
        from the -x (west) side. (Checked in the real client, 2026-10-25.)"""
        cur = 0
        for ch in msg.upper():
            g = FONT.get(ch, FONT[" "])
            for row, bits in enumerate(g):
                for col, bit in enumerate(bits):
                    if bit != "1":
                        continue
                    for a in range(scale):          # scale: each font pixel becomes a scale x scale square
                        for c in range(scale):
                            yy = y + (4 - row) * scale + c
                            if axis == "x": self.set(x + ((cur + col) * scale + a) * step, yy, z, s)
                            else: self.set(x, yy, z + ((cur + col) * scale + a) * step, s)
            cur += len(g[0]) + 1
        return cur * scale

    def hip_roof(self, x0, z0, x1, z1, y, st, full, top=None, overhang=1, trim=None):
        """Sloped roof made of stairs on all four sides, rising to a ridge. st = stairs block id, full = full block."""
        x0 -= overhang; z0 -= overhang; x1 += overhang; z1 += overhang
        i = 0
        while x0 + i <= x1 - i and z0 + i <= z1 - i:
            yy = y + i
            ax0, ax1, az0, az1 = x0 + i, x1 - i, z0 + i, z1 - i
            if ax0 == ax1 or az0 == az1:
                self.box(ax0, yy, az0, ax1, yy, az1, top or full)
                break
            for x in range(ax0 + 1, ax1):
                self.set(x, yy, az0, stairs(st, "south")); self.set(x, yy, az1, stairs(st, "north"))
            for z in range(az0 + 1, az1):
                self.set(ax0, yy, z, stairs(st, "east")); self.set(ax1, yy, z, stairs(st, "west"))
            self.set(ax0, yy, az0, stairs(st, "east", shape="outer_right")); self.set(ax1, yy, az0, stairs(st, "south", shape="outer_right"))
            self.set(ax0, yy, az1, stairs(st, "north", shape="outer_right")); self.set(ax1, yy, az1, stairs(st, "west", shape="outer_right"))
            if i > 0:  # fill under the slope
                self.box(ax0 + 1, yy - 1, az0 + 1, ax1 - 1, yy - 1, az1 - 1, full) if ax1 - ax0 > 1 and az1 - az0 > 1 else None
            i += 1
        if trim:
            for x in range(x0, x1 + 1):
                self.set(x, y - 1, z0, trim); self.set(x, y - 1, z1, trim)
            for z in range(z0, z1 + 1):
                self.set(x0, y - 1, z, trim); self.set(x1, y - 1, z, trim)

    def gable_roof(self, x0, z0, x1, z1, y, st, full, gable_wall=None, overhang=1, ridge=None):
        """Roof sloping toward +z and -z, ridge along x. Gable ends filled with gable_wall."""
        z0 -= overhang; z1 += overhang
        i = 0
        while z0 + i < z1 - i:
            for x in range(x0 - overhang, x1 + overhang + 1):
                self.set(x, y + i, z0 + i, stairs(st, "south")); self.set(x, y + i, z1 - i, stairs(st, "north"))
            if gable_wall:
                for z in range(z0 + i + 1, z1 - i):
                    self.set(x0, y + i, z, gable_wall); self.set(x1, y + i, z, gable_wall)
            i += 1
        if z0 + i == z1 - i:
            for x in range(x0 - overhang, x1 + overhang + 1):
                self.set(x, y + i, z0 + i, ridge or slab(full.replace("_planks", "_slab").replace("bricks", "brick_slab"), "bottom") if ridge else full)
        return y + i

    def pagoda_roof(self, cx, cz, hw, hd, y, st, full, layers=3, flare=True, slab_block=None):
        """Asian style roof with up-turned corners. hw/hd = half width/depth of the eave. Returns top y."""
        for i in range(layers):
            w, d = hw - i, hd - i
            if w < 1 or d < 1: break
            yy = y + i
            for x in range(cx - w, cx + w + 1):
                self.set(x, yy, cz - d, stairs(st, "south")); self.set(x, yy, cz + d, stairs(st, "north"))
            for z in range(cz - d, cz + d + 1):
                self.set(cx - w, yy, z, stairs(st, "east")); self.set(cx + w, yy, z, stairs(st, "west"))
            self.box(cx - w + 1, yy, cz - d + 1, cx + w - 1, yy, cz + d - 1, full)
            if flare and i == 0:
                for sx in (-1, 1):
                    for sz in (-1, 1):
                        self.set(cx + sx * w, yy + 1, cz + sz * d, stairs(st, "east" if sx < 0 else "west", "top"))
                        self.set(cx + sx * (w + 1), yy + 1, cz + sz * (d + 1), slab(slab_block or (full.replace("tiles", "tile_slab") if "tiles" in full else "minecraft:dark_oak_slab"), "bottom"))
        return y + layers

    def arch_x(self, x0, x1, z, y, h, s, thick=1):
        """Semicircular arch spanning x0..x1 in the plane z (opening below)."""
        r = (x1 - x0) / 2; cx = (x0 + x1) / 2
        for x in range(x0, x1 + 1):
            yy = y + h + int(round(math.sqrt(max(0, r * r - (x - cx) ** 2)) * 0.6))
            for t in range(thick):
                self.set(x, yy, z + t, s)

    def column(self, x, z, y0, y1, s, cap=None, base=None):
        for y in range(y0, y1 + 1): self.set(x, y, z, s)
        if cap: self.set(x, y1 + 1, z, cap)
        if base: self.set(x, y0 - 1, z, base)

    def round_column(self, cx, cz, r, y0, y1, s, cap=None):
        self.cyl(cx, cz, r, y0, y1, s)
        if cap: self.cyl(cx, cz, r + 1, y1 + 1, y1 + 1, cap)

    def windows_band(self, x0, x1, z, y, s, every=2, h=2):
        for x in range(x0, x1 + 1, every):
            for yy in range(y, y + h): self.set(x, yy, z, s)

    def table_set(self, x, y, z, wood="spruce", cloth=None):
        self.set(x, y, z, fence(wood)); self.set(x, y + 1, z, f"minecraft:{cloth}_carpet" if cloth else f"minecraft:{wood}_pressure_plate[powered=false]")
        for dx, dz, f in ((1, 0, "west"), (-1, 0, "east"), (0, 1, "north"), (0, -1, "south")):
            if (x + dx, y, z + dz) not in self.blocks or self.blocks[(x + dx, y, z + dz)] == AIR:
                self.set(x + dx, y, z + dz, stairs(f"minecraft:{wood}_stairs", f))

    def hull(self, x0, length, cz, beam, keel_y, deck_y, plank, bottom=None, rail=None, bow_len=None, stern_len=None, stern_round=False,
             rail_h=1, fill_deck=None, flare=0.0, waterline=None, paint=None):
        """Lofted ship hull pointing +x. Smooth curved sides with stairs/slabs-free plank shell.
        beam = full width at deck. Returns a dict with per-x half widths at deck."""
        bow_len = bow_len or length * 0.32; stern_len = stern_len or length * 0.12
        halfw = {}
        for x in range(x0, x0 + length):
            f = x - x0
            if f > length - bow_len:
                t = (f - (length - bow_len)) / bow_len
                k = math.sqrt(max(0.0, 1 - t ** 2.2))
            elif f < stern_len:
                t = (stern_len - f) / stern_len
                k = math.sqrt(max(0.0, 1 - t ** 2)) if stern_round else 1 - 0.25 * t
            else:
                k = 1.0
            halfw[x] = k * beam / 2
        H = deck_y - keel_y

        def slice_at(x, y):
            """(half width in blocks, keel rise) of the hull at x, y, or None where the hull doesn't reach."""
            if x not in halfw: return None
            t = (y - keel_y) / max(1, H)  # 0 at keel, 1 at deck
            prof = math.sin(t * math.pi / 2) ** 0.7 * (1 + flare * t)
            f = x - x0
            rise = 0  # keel rises toward bow and stern
            if f > length - bow_len * 0.6: rise = (f - (length - bow_len * 0.6)) / (bow_len * 0.6) * H * 0.55
            if f < stern_len * 0.5: rise = max(rise, (stern_len * 0.5 - f) / (stern_len * 0.5) * H * 0.35)
            if y < keel_y + rise: return None
            w = halfw[x] * prof
            if w < 0.4 and y < deck_y: return None
            return int(round(w)), rise

        for x, hw in halfw.items():
            for y in range(keel_y, deck_y + 1):
                sl = slice_at(x, y)
                if sl is None: continue
                zr, rise = sl
                prev, nxt = slice_at(x - 1, y), slice_at(x + 1, y)
                for z in range(cz - zr, cz + zr + 1):
                    # a plank wherever the next slice fore or aft doesn't cover this cell: that closes the stern and
                    # the bow tip and the steps where the sides narrow fast, so the hold stays dry below the waterline
                    edge = abs(z - cz) >= zr - 0 or y <= keel_y + rise + 0.5 or any(o is None or abs(z - cz) > o[0] for o in (prev, nxt))
                    mat = plank
                    if paint: mat = paint(x, y, z, zr) or plank
                    if bottom and waterline is not None and y < waterline: mat = bottom
                    if y == deck_y:
                        self.set(x, y, z, fill_deck if (fill_deck and abs(z - cz) < zr) else mat)
                    elif edge:
                        self.set(x, y, z, mat)
                    else:
                        self.set(x, y, z, AIR)
            if rail:
                zr = int(round(hw))
                for h in range(1, rail_h + 1):
                    self.set(x, deck_y + h, cz - zr, rail); self.set(x, deck_y + h, cz + zr, rail)
        if rail:  # close the rail at the stern and bow tips
            xs = sorted(halfw)
            for x in (xs[0],):
                zr = int(round(halfw[x]))
                for z in range(cz - zr, cz + zr + 1):
                    for h in range(1, rail_h + 1): self.set(x, deck_y + h, z, rail)
        return halfw

    def square_sail(self, x, cz, y0, y1, half, s, belly=None, yard=None, axis="z", pattern=None, dir=1):
        """Square sail hanging from a yard at y1 (foot at y0), spanning cz-half..cz+half, full of wind: it bellies
        forward (+x, or -x with dir=-1) like a real sail with the wind behind it, deepest a little below the middle,
        the head lashed straight along the yard, the leeches (sides) curving back to the yard arms and the foot
        still bowed out. No sail is ever flat: belly is at least sail_belly(half, height), so callers that pass
        belly=1 get a proper curve too. The skin is filled between neighbouring cells so no light shows through.
        pattern(u, v) -> block or None, with u in -1..1 across and v in -1..1 bottom to top, paints an emblem
        (painted by position on the sail, so it still reads from the front)."""
        belly = max(belly or 0, sail_belly(half, y1 - y0 + 1))
        d = {}
        for y in range(y0, y1 + 1):
            for z in range(cz - half, cz + half + 1):
                d[(y, z)] = sail_depth((z - cz) / (half + 0.5), (y1 - y) / max(1, y1 - y0), belly)
        for (y, z), bx in d.items():
            blk = s
            if pattern:
                p = pattern((z - cz) / max(1, half), (y - (y0 + y1) / 2) / max(1, (y1 - y0) / 2))
                if p: blk = p
            # fill back towards the shallowest neighbour so the curved skin has no gaps
            lo = min([bx] + [d[n] for n in ((y - 1, z), (y + 1, z), (y, z - 1), (y, z + 1)) if n in d])
            for k in range(max(0, lo), bx + 1):
                self.set(x + dir * k, y, z, blk)
        if yard:
            for z in range(cz - half - 1, cz + half + 2): self.set(x, y1 + 1, z, yard)

    def mast(self, x, cz, y0, h, wood="spruce", rope=True, nest_y=None):
        for y in range(y0, y0 + h): self.set(x, y, cz, log(wood))
        if nest_y:
            self.disk(x, nest_y, cz, 2, f"minecraft:{wood}_planks")
            for i in range(0, 360, 45):
                a = math.radians(i); self.set(round(x + 2 * math.cos(a)), nest_y + 1, round(cz + 2 * math.sin(a)), fence(wood))
            self.set(x, nest_y, cz, log(wood))

    def jolly_roger(self, x, y, z, w, h, axis="z", bg="minecraft:black_wool", fg="minecraft:white_wool", style="skull"):
        """Flag in the plane x (spanning +z) with a skull and crossbones. (x,y,z) = top-left corner, hanging down."""
        for i in range(w):
            for j in range(h):
                self.set(x, y - j, z + i, bg)
        cz = z + w // 2; cy = y - h // 2
        r = max(1, min(w, h) // 5)
        # crossbones
        for k in range(-2 * r, 2 * r + 1):
            self.set(x, cy - r + k // 2 + 0, cz + k, fg); self.set(x, cy - r - k // 2, cz + k, fg)
        # skull
        for dz in range(-r - 1, r + 2):
            for dy in range(-r, r + 2):
                if (dz / (r + 1.2)) ** 2 + (dy / (r + 1.4)) ** 2 <= 1: self.set(x, cy + dy, cz + dz, fg)
        self.set(x, cy + 1, cz - 1, bg); self.set(x, cy + 1, cz + 1, bg)
        if style == "whitebeard":  # crescent moustache under the nose
            for dz in range(-r - 3, r + 4):
                dy = int(round(abs(dz) * 0.5)) - 1
                if abs(dz) > 1: self.set(x, cy + dy - 1, cz + dz, fg)
            self.set(x, cy - 1, cz, bg)

    def stairs_up(self, x, y, z, n, st, facing, w=1, clear=3):
        """Straight staircase: n steps starting at (x,y,z), climbing toward `facing`; clears headroom above."""
        dx, dz = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}[facing]
        px, pz = (1, 0) if dz != 0 else (0, 1)
        for i in range(n):
            for k in range(w):
                bx, bz = x + dx * i + px * k, z + dz * i + pz * k
                self.set(bx, y + i, bz, stairs(st, facing))
                for yy in range(y + i + 1, y + i + 1 + clear): self.set(bx, yy, bz, AIR)

    def shape(self, inside, x0, y0, z0, x1, y1, z1, mat, interior=AIR, open_top=None):
        """Voxelise a shape. inside(x,y,z) -> bool. mat(x,y,z) -> block (or a block string).
        Surface blocks get mat, inner blocks get `interior` (None = leave as is). open_top: y above which the
        shape is cut open (no lid)."""
        m = mat if callable(mat) else (lambda x, y, z: mat)
        ins = {}
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    if inside(x, y, z): ins[(x, y, z)] = True
        for (x, y, z) in ins:
            surf = False
            for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                n = (x + d[0], y + d[1], z + d[2])
                if n not in ins and not (open_top is not None and d[1] == 1 and y >= open_top):
                    surf = True; break
            if surf: self.set(x, y, z, m(x, y, z))
            elif interior is not None: self.set(x, y, z, interior)
        return ins


    def dome(self, cx, cz, y, r, h=None, s="minecraft:smooth_quartz", onion=False, tip="minecraft:gold_block", hollow=True):
        """Dome (or onion dome) sitting on y. r = radius, h = height."""
        h = h or (int(r * 2.1) if onion else r)
        for yy in range(0, h + 1):
            t = yy / h
            if onion:
                if t < 0.45: rr = r * (0.85 + 0.25 * math.sin(t / 0.45 * math.pi / 2))
                else: rr = r * 1.1 * math.cos((t - 0.45) / 0.55 * math.pi / 2) ** 1.3
            else:
                rr = r * math.sqrt(max(0.0, 1 - t * t))
            if rr < 0.5:
                self.set(cx, y + yy, cz, s); continue
            self.cyl(cx, cz, rr, y + yy, y + yy, s, hollow=hollow and yy < h - 1)
        if tip:
            self.set(cx, y + h + 1, cz, tip); self.set(cx, y + h + 2, cz, "minecraft:lightning_rod[facing=up,powered=false,waterlogged=false]")
        return y + h


def whitebeard_mark(fg="minecraft:black_wool"):
    """Pattern for a sail: Whitebeard's skull with the crescent moustache over crossed bones (u right, v up)."""
    def p(u, v):
        u2, v2 = u * 1.25, v * 1.15
        skull = (u2 / 0.42) ** 2 + ((v2 - 0.2) / 0.5) ** 2 <= 1
        jaw = abs(u2) <= 0.25 and -0.45 <= v2 <= -0.15
        eye = ((abs(u2) - 0.17) / 0.11) ** 2 + ((v2 - 0.25) / 0.13) ** 2 <= 1
        nose = abs(u2) <= 0.05 and 0.0 <= v2 <= 0.08
        must = abs(u2) <= 0.85 and abs(v2 - (-0.12 + 0.55 * u2 * u2)) <= 0.09 and abs(u2) >= 0.08
        bone = (abs(v2 - (-0.1) - u2 * 0.75) <= 0.07 or abs(v2 - (-0.1) + u2 * 0.75) <= 0.07) and abs(u2) <= 0.95
        if (skull or jaw) and not eye and not nose: return fg
        if must: return fg
        if bone and not (skull or jaw): return fg
        return None
    return p

