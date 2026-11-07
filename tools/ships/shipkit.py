"""Ship-building kit for the One Piece mod: life-size, show-accurate ships that sail as one entity.

Every ship is a block canvas (tools/landmarks/canvas.py, which wraps tools/worldgen/kit.py) with a few rules:
  * +x is the bow (front). z runs across the ship; CZ is the centre line.
  * The sea surface is y 0: a block at y 0 is just under water, y 1 is the first dry block. Keels go to negative y.
  * Build the ship in blocks, then `ship.save(res_dir)` writes
        data/onepiece/structure/ships/<id>.nbt      the blocks (one structure template)
        data/onepiece/ships/<id>.json               name, waterline, which way the bow points, hull size
    and `ship.preview(dir)` renders isometric pictures of it.
  * Put exactly one Ship's Wheel on deck (ship.helm(x, y, z)). It faces the bow; the captain stands behind it.
  * Keep ships under ~4,500 blocks (ShipAssembler.MAX_BLOCKS is 6,000, and every block is drawn every frame).

Java reads the .json + .nbt pair in com.onepiecemod.ship.ShipTemplates and turns it into a ShipLayout.

Materials are block state strings exactly as the game writes them ("minecraft:oak_planks", "minecraft:oak_stairs[facing=east,...]").
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(TOOLS, "landmarks"))
sys.path.insert(0, os.path.join(TOOLS, "worldgen"))
from canvas import *  # noqa: F401,F403  (B, AIR, FENCE, stairs, slab, fence, lantern, log, ...)
from canvas import B as _CanvasB
import interiors as I  # noqa: F401  (I.furnish for cabins)

RES_DEFAULT = "/mnt/project-files/one-piece-mod/source/src/main/resources"
PREVIEWS = "/mnt/project-files/one-piece-mod/previews/ships"

WOOL = {c: f"minecraft:{c}_wool" for c in ("white", "black", "red", "yellow", "orange", "blue", "light_blue", "green", "lime",
                                           "pink", "purple", "brown", "gray", "light_gray", "cyan", "magenta")}
CONCRETE = {c: f"minecraft:{c}_concrete" for c in WOOL}
TERRACOTTA = {c: f"minecraft:{c}_terracotta" for c in WOOL}
GLASS = {c: f"minecraft:{c}_stained_glass" for c in WOOL}


def pane(color=None):
    return pane_of(f"minecraft:{color}_stained_glass_pane") if color else PANE


def ropes(wood="dark_oak"):
    return fence(wood)


class Ship(_CanvasB):
    """A ship canvas. sid = file id (snake_case), name = what players see."""

    def __init__(self, sid, name, faction="pirate", tiers=(), crew=None, scale=1.0):
        super().__init__()
        self.sid = sid
        self.name = name
        self.faction = faction        # "player", "pirate" or "marine": who sails it when the game spawns it
        self.tiers = list(tiers)      # enemy tiers (0..5) this ship shows up at, for pirate/marine ships
        self.crew = crew              # the crew's name for the ship's name tag, e.g. "Buggy Pirates"
        self.scale = scale
        self.helm_pos = None
        self.notes = []

    # ---------------------------------------------------------------- hull
    def hull(self, x0, length, cz, beam, keel_y, deck_y, side, bottom=None, deck="minecraft:oak_planks", wale=None,
             bow_len=None, stern_len=None, bow="sharp", stern="transom", sheer_bow=2, sheer_stern=1,
             keel_rise_bow=None, keel_rise_stern=None, fullness=0.6, flat=0.45, bulwark=1, bulwark_mat=None,
             rail=None, paint=None, keep_inside=False, inner_decks=()):
        """Lofted hull pointing +x, from x0 to x0+length-1. Returns a dict x -> (half width at deck, deck y, bottom y).

        beam = full width amidships. keel_y = lowest block, deck_y = deck level amidships (sheer raises it toward the
        bow and stern by sheer_bow / sheer_stern blocks). bow = "sharp" (caravel/galleon) or "round" (fat ships like the
        Sunny); stern = "transom" (flat back) or "round". fullness: how boxy the sections are (0.4 = slack, 0.8 = barge).
        flat: fraction of the beam that is flat bottom. bulwark: rows of solid wall above the deck at the sides.
        paint(x, y, z, kind) -> block or None overrides materials; kind is "side", "bottom", "deck", "bulwark",
        "bow", "stern". Blocks under water (y < 1) use `bottom` when given. wale = block for a stripe at the deck
        edge one block below the deck (the thick plank band along the side). rail = block placed on top of the bulwark.
        inner_decks = [(y, material), ...] adds floors inside the hull at those heights (full width, with a hatch left
        to you). keep_inside=True leaves the inside filled instead of hollowing it (small boats)."""
        bow_len = bow_len if bow_len is not None else int(length * 0.3)
        stern_len = stern_len if stern_len is not None else int(length * 0.12)
        keel_rise_bow = keel_rise_bow if keel_rise_bow is not None else max(2, (deck_y - keel_y) // 2)
        keel_rise_stern = keel_rise_stern if keel_rise_stern is not None else max(1, (deck_y - keel_y) // 3)
        x1 = x0 + length - 1
        info = {}
        for x in range(x0, x1 + 1):
            f = x - x0
            k = 1.0
            dy = 0
            rise = 0.0
            if f >= length - bow_len:
                t = (f - (length - bow_len)) / max(1, bow_len - 1)
                t = min(1.0, t)
                if bow == "round":
                    k = math.sqrt(max(0.0, 1 - t ** 2.6)) * 0.98 + 0.02
                else:
                    k = math.sqrt(max(0.0, 1 - t ** 2.0)) * (1 - 0.1 * t)
                dy = int(round(sheer_bow * t ** 1.4))
                rise = keel_rise_bow * t ** 1.6
            if f < stern_len:
                t = (stern_len - f) / max(1, stern_len)
                if stern == "round":
                    k = min(k, math.sqrt(max(0.0, 1 - t ** 2.0)) * 0.97 + 0.03)
                else:
                    k = min(k, 1 - 0.28 * t)
                dy = max(dy, int(round(sheer_stern * t ** 1.4)))
                rise = max(rise, keel_rise_stern * t ** 1.5)
            hw = max(0.5, k * (beam - 1) / 2)
            info[x] = (hw, deck_y + dy, keel_y + rise)
        p = 1.0 - fullness  # section exponent

        def halfw(x, y):
            if x not in info:
                return -1
            hw, dy, by = info[x]
            if y > dy or y < by - 0.5:
                return -1
            t = (y - by) / max(0.5, (dy - by))
            t = max(0.0, min(1.0, t))
            w = hw * (flat + (1 - flat) * math.sin(t * math.pi / 2) ** p)
            return w

        def inside(x, y, z):
            w = halfw(x, y)
            return w >= 0 and abs(z - cz) <= w + 0.01

        bw = int(round(max(v[0] for v in info.values()))) + 2
        top = max(v[1] for v in info.values()) + bulwark + 1
        bot = int(math.floor(min(v[2] for v in info.values()))) - 1
        water = 1
        for x in range(x0, x1 + 1):
            for y in range(bot, top + 1):
                for z in range(cz - bw, cz + bw + 1):
                    if not inside(x, y, z):
                        continue
                    hw, dy, by = info[x]
                    surf = y == dy or not all(inside(x + d[0], y + d[1], z + d[2])
                                              for d in ((1, 0, 0), (-1, 0, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)))
                    if y == dy:
                        kind = "deck"
                        edge = not inside(x, y, z + 1) or not inside(x, y, z - 1) or not inside(x + 1, y, z) or not inside(x - 1, y, z)
                        mat = deck if not edge else side
                        if edge:
                            kind = "side"
                    elif not surf:
                        if keep_inside:
                            mat = side
                            kind = "inside"
                        else:
                            self.set(x, y, z, AIR)
                            continue
                    else:
                        kind = "side"
                        if y < water and bottom:
                            mat, kind = bottom, "bottom"
                        else:
                            mat = side
                        if x == x1 or (not inside(x + 1, y, z) and x > x0 + length - bow_len):
                            kind = "bow" if kind != "bottom" else kind
                        if x == x0:
                            kind = "stern" if kind != "bottom" else kind
                        if wale and y == dy - 1 and kind == "side":
                            mat = wale
                    if paint:
                        mat = paint(x, y, z, kind) or mat
                    self.set(x, y, z, mat)
            # bulwark: solid wall on the deck edge, with the rail on top
            hw, dy, by = info[x]
            for z in range(cz - bw, cz + bw + 1):
                if not inside(x, dy, z):
                    continue
                edge = not inside(x, dy, z + 1) or not inside(x, dy, z - 1) or not inside(x + 1, dy, z) or not inside(x - 1, dy, z)
                if not edge:
                    continue
                for h in range(1, bulwark + 1):
                    m = bulwark_mat or side
                    if paint:
                        m = paint(x, dy + h, z, "bulwark") or m
                    self.set(x, dy + h, z, m)
                if rail:
                    self.set(x, dy + bulwark + 1, z, rail)
        for (fy, fm) in inner_decks:
            for x in range(x0 + 1, x1):
                for z in range(cz - bw, cz + bw + 1):
                    if inside(x, fy, z) and inside(x, fy - 1, z) and self.get(x, fy, z) == AIR:
                        self.set(x, fy, z, fm)
        self._hull = info
        self._cz = cz
        self._inside = inside
        return info

    def halfwidth(self, x, y=None):
        """Half width of the hull at x (at the deck, or at height y)."""
        if y is None:
            return self._hull[x][0] if x in self._hull else 0
        for w in range(40, -1, -1):
            if self._inside(x, y, self._cz + w):
                return w
        return 0

    def deck_y(self, x):
        return self._hull[x][1] if x in self._hull else None

    def open_hatch(self, x, y, z, w=1, ladder_facing="west", down_to=None):
        """Cuts a hatch in a deck/floor and runs a ladder down to `down_to`."""
        self.box(x, y, z, x + w - 1, y, z + w - 1, AIR)
        if down_to is not None:
            for yy in range(down_to, y + 1):
                self.set(x, yy, z, ladder(ladder_facing))

    # ---------------------------------------------------------------- superstructure
    def cabin(self, x0, y0, z0, x1, y1, z1, wall, floor=None, roof=None, windows=None, every=2, window_y=None,
              window_sides=("north", "south", "east", "west"), door=None, post=None):
        """Hollow cabin with walls, floor and roof. windows = pane block put every `every` blocks at window_y
        (default 2 above the floor). door = (x, z, facing) on a wall: a 2-high opening with a door block.
        post = corner block (log) for framed walls."""
        self.box(x0, y0, z0, x1, y1, z1, wall)
        self.box(x0 + 1, y0 + 1, z0 + 1, x1 - 1, y1 - 1, z1 - 1, AIR)
        if floor:
            self.box(x0 + 1, y0, z0 + 1, x1 - 1, y0, z1 - 1, floor)
        if roof:
            self.box(x0, y1, z0, x1, y1, z1, roof)
        if post:
            for (x, z) in ((x0, z0), (x0, z1), (x1, z0), (x1, z1)):
                self.column(x, z, y0, y1, post)
        if windows:
            wy = window_y if window_y is not None else y0 + 2
            if "north" in window_sides:
                for x in range(x0 + 1, x1, every):
                    self.set(x, wy, z0, windows)
            if "south" in window_sides:
                for x in range(x0 + 1, x1, every):
                    self.set(x, wy, z1, windows)
            if "west" in window_sides:
                for z in range(z0 + 1, z1, every):
                    self.set(x0, wy, z, windows)
            if "east" in window_sides:
                for z in range(z0 + 1, z1, every):
                    self.set(x1, wy, z, windows)
        if door:
            dx, dz, facing = door
            self.set(dx, y0 + 1, dz, AIR)
            self.set(dx, y0 + 2, dz, AIR)

    def dome(self, cx, cy, cz, r, mat, ry=None, hollow=True):
        """Upper half of a sphere (a rounded roof)."""
        self.sphere(cx, cy, cz, r, mat, hollow=hollow, upper=True, ry=ry)

    def barrel_roof(self, x0, z0, x1, z1, y, mat, slab_mat=None, axis="x"):
        """Rounded roof along `axis`: full blocks on the ridge, slabs on the shoulders."""
        if axis == "x":
            n = z1 - z0
            for z in range(z0, z1 + 1):
                t = abs((z - z0) / max(1, n) * 2 - 1)  # 0 middle, 1 edge
                h = int(round((1 - t * t) * 2))
                for x in range(x0, x1 + 1):
                    self.set(x, y + h, z, mat)
                    if slab_mat and h < 2:
                        self.set(x, y + h + 1, z, slab_mat)
        else:
            n = x1 - x0
            for x in range(x0, x1 + 1):
                t = abs((x - x0) / max(1, n) * 2 - 1)
                h = int(round((1 - t * t) * 2))
                for z in range(z0, z1 + 1):
                    self.set(x, y + h, z, mat)
                    if slab_mat and h < 2:
                        self.set(x, y + h + 1, z, slab_mat)

    def porthole(self, x, y, z, facing, rim=None):
        """A round window: the mod's porthole block, or a pane with a rim block around it."""
        if rim:
            self.set(x, y, z, pane())
        else:
            self.set(x, y, z, f"onepiece:porthole[facing={facing}]")

    # ---------------------------------------------------------------- masts, sails, rigging
    def mast(self, x, cz, y0, h, wood="spruce", r=0, nest=None, nest_r=2, top_flag=None):
        """Mast from y0 up h blocks. r = 0 is one block thick, r = 1 a 3x3 round mast. nest = y of a crow's nest.
        Returns the top y."""
        if r <= 0:
            for y in range(y0, y0 + h):
                self.set(x, y, cz, log(wood))
        else:
            self.cyl(x, cz, r, y0, y0 + h - 1, log(wood))
        top = y0 + h - 1
        if nest is not None:
            self.crows_nest(x, nest, cz, nest_r, wood)
        if top_flag:
            self.flag(x, top + 1, cz, top_flag)
        return top

    def crows_nest(self, x, y, cz, r=2, wood="spruce"):
        self.disk(x, y, cz, r, f"minecraft:{wood}_planks")
        for a in range(0, 360, 20):
            t = math.radians(a)
            px, pz = round(x + r * math.cos(t)), round(cz + r * math.sin(t))
            self.set(px, y + 1, pz, f"minecraft:{wood}_planks")
            self.set(px, y + 2, pz, fence(wood))
        self.set(x, y, cz, log(wood))
        self.set(x, y + 1, cz, log(wood))

    def yard(self, x, y, cz, half, wood="spruce"):
        for z in range(cz - half - 1, cz + half + 2):
            self.set(x, y, z, log(wood, "z"))

    def square_sail(self, x, cz, y0, y1, half, s, belly=None, yard=None, axis="z", pattern=None, bitmap=None):
        """Square sail in the z-y plane at x, from y0 (foot) to y1 (head), spanning cz-half..cz+half, full of
        wind and bellied forward (+x): see canvas.B.square_sail (never flat, at least canvas.sail_belly deep).
        pattern(u, v) -> block or None paints an emblem (u across -1..1, v up -1..1).
        bitmap = (rows, palette) is an easier way to paint one: see bitmap_pattern()."""
        if bitmap:
            pattern = bitmap_pattern(*bitmap)
        _CanvasB.square_sail(self, x, cz, y0, y1, half, s, belly=belly, pattern=pattern)
        if yard:
            self.yard(x, y1 + 1, cz, half, yard)

    def tri_sail(self, z, p0, p1, p2, s, pattern=None, bitmap=None, belly=None, side=1):
        """Triangular sail (jib or lateen) in the x-y plane at z. p = (x, y) corners. Full of wind like the square
        sails: the middle bows out sideways (+z, or -z with side=-1) by `belly` (default from its size), the
        edges stay on the line between the corners."""
        if bitmap:
            pattern = bitmap_pattern(*bitmap)
        xs = [p[0] for p in (p0, p1, p2)]
        ys = [p[1] for p in (p0, p1, p2)]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        cells = {}

        def sign(a, b, c):
            return (a[0] - c[0]) * (b[1] - c[1]) - (b[0] - c[0]) * (a[1] - c[1])
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                pt = (x + 0.5, y + 0.5)
                d1, d2, d3 = sign(pt, p0, p1), sign(pt, p1, p2), sign(pt, p2, p0)
                neg = d1 < 0 or d2 < 0 or d3 < 0
                pos = d1 > 0 or d2 > 0 or d3 > 0
                if neg and pos:
                    # include the edge blocks the lines pass through
                    if not (abs(d1) < 0.6 * (x1 - x0 + y1 - y0) or abs(d2) < 0.6 * (x1 - x0 + y1 - y0) or abs(d3) < 0.6 * (x1 - x0 + y1 - y0)):
                        continue
                    if min(abs(d1), abs(d2), abs(d3)) > 0.55 * max(1, min(x1 - x0, y1 - y0)):
                        continue
                blk = s
                if pattern:
                    p = pattern((x - (x0 + x1) / 2) / max(1, (x1 - x0) / 2), (y - (y0 + y1) / 2) / max(1, (y1 - y0) / 2))
                    if p:
                        blk = p
                cells[(x, y)] = blk
        if belly is None:
            belly = max(1, int(round(0.15 * min(x1 - x0, y1 - y0))))
        area = sign(p0, p1, p2) or 1
        depth = {}
        for (x, y) in cells:
            pt = (x + 0.5, y + 0.5)
            bary = min(sign(pt, p1, p2) / area, sign(pt, p2, p0) / area, sign(pt, p0, p1) / area)
            depth[(x, y)] = int(round(belly * min(1.0, max(0.0, 3 * bary)) ** 0.8))
        for (x, y), blk in cells.items():
            dz = depth[(x, y)]
            lo = min([dz] + [depth[n] for n in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)) if n in depth])
            for k in range(max(0, lo), dz + 1):
                self.set(x, y, z + side * k, blk)

    def rope(self, p0, p1, s=None):
        """A line of fence (rigging) between two points."""
        self.line(p0, p1, s or ropes())

    def shrouds(self, mast_x, mast_y, cz, deck_y, half, wood="dark_oak", n=3, spread=2):
        """Ropes from a mast up at mast_y down to both deck edges."""
        for side in (-1, 1):
            for k in range(n):
                dx = (k - (n - 1) / 2) * spread
                self.line((mast_x, mast_y, cz), (round(mast_x + dx), deck_y + 1, cz + side * half), fence(wood))

    def flag(self, x, y, z, bitmap, w=None, h=None, axis="z"):
        """A flag flying from (x, y, z) toward +z (axis='z') or +x (axis='x'), painted from a bitmap (rows, palette).
        The pole block at (x, y, z) is a fence."""
        rows, palette = bitmap
        h = h or len(rows)
        w = w or len(rows[0])
        for j in range(h):
            for i in range(w):
                ch = rows[j][i] if j < len(rows) and i < len(rows[j]) else "."
                blk = palette.get(ch)
                if blk:
                    if axis == "z":
                        self.set(x, y + h - 1 - j, z + 1 + i, blk)
                    else:
                        self.set(x + 1 + i, y + h - 1 - j, z, blk)
        for yy in range(y, y + h):
            self.set(x, yy, z, fence("dark_oak"))

    def paint_wall(self, x, y, z, bitmap, axis="z", flip=False):
        """Paints a bitmap on a wall: axis='z' spreads the columns along +z at fixed x (seen from +x side);
        axis='x' along +x at fixed z. (x, y, z) = bottom-left. flip mirrors it."""
        rows, palette = bitmap
        h = len(rows)
        w = max(len(r) for r in rows)
        for j in range(h):
            for i in range(w):
                ch = rows[j][i] if i < len(rows[j]) else "."
                blk = palette.get(ch)
                if not blk:
                    continue
                ii = w - 1 - i if flip else i
                if axis == "z":
                    self.set(x, y + h - 1 - j, z + ii, blk)
                else:
                    self.set(x + ii, y + h - 1 - j, z, blk)

    # ---------------------------------------------------------------- deck gear
    def helm(self, x, y, z):
        """The Ship's Wheel. Faces the bow (+x); the captain stands at x-1."""
        self.set(x, y, z, "onepiece:ships_wheel[facing=east]")
        self.helm_pos = (x, y, z)

    def cannon(self, x, y, z, facing):
        """facing: south = fires toward +z, north = -z, east = toward the bow."""
        self.set(x, y, z, f"onepiece:cannon[facing={facing}]")

    def broadside(self, xs, y, cz, half_at, port=True, starboard=True, gunport=None, gunport_y=None):
        """Cannons along both sides at the given xs, standing on deck y at the edge. half_at(x) -> half width.
        gunport = block painted on the hull outside each cannon (e.g. black concrete) at gunport_y.
        A gunport at deck height becomes the cannon itself (onepiece:cannon[mounted=true]: dark port in the hull,
        barrel out over the sea, carriage on deck behind it); tools/shipcombat/mount_cannons.py does the same to
        finished .nbt files."""
        for x in xs:
            hw = int(round(half_at(x)))
            gy = gunport_y if gunport_y is not None else y
            mount = bool(gunport) and gy == y
            if starboard:
                if mount:
                    self.set(x, y, cz + hw, "onepiece:cannon[facing=south,mounted=true]")
                else:
                    self.cannon(x, y, cz + hw - 1, "south")
            if port:
                if mount:
                    self.set(x, y, cz - hw, "onepiece:cannon[facing=north,mounted=true]")
                else:
                    self.cannon(x, y, cz - hw + 1, "north")
            if gunport and not mount:
                self.set(x, gy, cz + hw, gunport)
                self.set(x, gy, cz - hw, gunport)

    def anchor(self, x, y, z, facing="east"):
        self.set(x, y, z, f"onepiece:anchor[facing={facing}]")

    def chest(self, x, y, z, loot, facing="south"):
        self.set(x, y, z, f"minecraft:chest[facing={facing},type=single,waterlogged=false]",
                 {"id": "minecraft:chest", "LootTable": f"onepiece:chests/{loot}"})

    def ladder_up(self, x, z, y0, y1, facing="west"):
        for y in range(y0, y1 + 1):
            self.set(x, y, z, ladder(facing))

    def stairs_run(self, x, y, z, n, st, facing, w=1, clear=3):
        self.stairs_up(x, y, z, n, st, facing, w=w, clear=clear)

    def railing(self, x0, x1, y, z, mat=None):
        for x in range(x0, x1 + 1):
            self.set(x, y, z, mat or fence("oak"))

    def lamp(self, x, y, z, hanging=False):
        self.set(x, y, z, lantern(hanging=hanging))

    def tree(self, x, y, z, h=5, kind="oak", r=2.0):
        super().tree(x, y, z, h=h, kind=kind, r=r)

    # ---------------------------------------------------------------- figureheads and blobs
    def blob(self, cx, cy, cz, rx, ry, rz, mat, power=2.0, hollow=False):
        """A rounded lump (superellipsoid). power 2 = egg, 3+ = boxy. mat may be a function (x, y, z) -> block."""
        m = mat if callable(mat) else (lambda x, y, z: mat)

        def ins(x, y, z):
            return (abs((x - cx) / rx) ** power + abs((y - cy) / ry) ** power + abs((z - cz) / rz) ** power) <= 1.0
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
                for z in range(int(cz - rz) - 1, int(cz + rz) + 2):
                    if not ins(x, y, z):
                        continue
                    if hollow and all(ins(x + d[0], y + d[1], z + d[2]) for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))):
                        continue
                    self.set(x, y, z, m(x, y, z))

    def ring(self, cx, cy, cz, r, mat, axis="x", thick=1.0):
        """A ring of blocks (a rim for a round hatch, a mane, a wheel) in the plane normal to `axis`."""
        for a in range(0, 360, 3):
            t = math.radians(a)
            for rr in (r, r - thick + 1) if thick > 1 else (r,):
                u, v = rr * math.cos(t), rr * math.sin(t)
                if axis == "x":
                    self.set(cx, round(cy + v), round(cz + u), mat)
                elif axis == "z":
                    self.set(round(cx + u), round(cy + v), cz, mat)
                else:
                    self.set(round(cx + u), cy, round(cz + v), mat)

    def disc(self, cx, cy, cz, r, mat, axis="x"):
        """Filled disc in the plane normal to `axis`."""
        for u in range(-int(r) - 1, int(r) + 2):
            for v in range(-int(r) - 1, int(r) + 2):
                if u * u + v * v <= r * r + 0.3:
                    if axis == "x":
                        self.set(cx, cy + v, cz + u, mat)
                    elif axis == "z":
                        self.set(cx + u, cy + v, cz, mat)
                    else:
                        self.set(cx + u, cy, cz + v, mat)

    # ---------------------------------------------------------------- output
    def count(self):
        return sum(1 for s in self.blocks.values() if s != AIR)

    def bounds(self):
        pts = [p for p, s in self.blocks.items() if s != AIR]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; zs = [p[2] for p in pts]
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))

    def check(self):
        """Prints problems: no wheel, too many blocks, floating bits. Returns a list of messages."""
        msgs = []
        if not self.helm_pos:
            msgs.append("NO SHIP'S WHEEL: call ship.helm(x, y, z) on the deck")
        n = self.count()
        if n > 4500:
            msgs.append(f"{n} blocks: over the 4,500 budget (ships over 6,000 can't be relaunched after docking)")
        (x0, y0, z0), (x1, y1, z1) = self.bounds()
        if y0 > 0:
            msgs.append("nothing under the water: the lowest block must be at y <= 0")
        if y0 < -12:
            msgs.append(f"keel at y {y0}: deeper than 12 blocks will hit the sea floor in shallow seas")
        return msgs

    def water_depth(self):
        (x0, y0, z0), (x1, y1, z1) = self.bounds()
        return round(0.9 - y0, 3)

    # Blocks the game treats as land, never as part of a ship (data/onepiece/tags/block/not_ship.json): a ship made of
    # them loses them the moment she docks and sets sail again. Use onepiece:deck_lawn / onepiece:deck_soil instead.
    NATURAL = ("minecraft:dirt", "minecraft:grass_block", "minecraft:podzol", "minecraft:coarse_dirt", "minecraft:mycelium",
               "minecraft:rooted_dirt", "minecraft:moss_block", "minecraft:pale_moss_block", "minecraft:mud", "minecraft:dirt_path",
               "minecraft:farmland", "minecraft:sand", "minecraft:red_sand", "minecraft:gravel", "minecraft:clay", "minecraft:stone",
               "minecraft:granite", "minecraft:diorite", "minecraft:andesite", "minecraft:tuff", "minecraft:deepslate",
               "minecraft:sandstone", "minecraft:red_sandstone", "minecraft:ice", "minecraft:packed_ice", "minecraft:blue_ice",
               "minecraft:snow", "minecraft:magma_block", "minecraft:obsidian", "minecraft:bedrock", "minecraft:short_grass",
               "minecraft:tall_grass", "minecraft:seagrass", "minecraft:kelp", "minecraft:lily_pad", "minecraft:sea_pickle")

    def natural_blocks(self):
        """Warnings for blocks the game never counts as part of a ship."""
        counts = {}
        for s in self.blocks.values():
            name = s.split("[")[0]
            if name in self.NATURAL or name.endswith("_coral_block") or name.endswith("_coral"):
                counts[name] = counts.get(name, 0) + 1
        return [f"{n} x{c}: natural blocks never sail (they'd drag the land along). Use onepiece:deck_lawn (grass) or "
                f"onepiece:deck_soil (dirt), or a built block." for n, c in sorted(counts.items())]

    def save(self, res=RES_DEFAULT):
        """Writes the structure template and the ship's json. Returns the json dict."""
        for m in self.check():
            print("  !!", m)
        for m in self.natural_blocks():
            print("  !!", m)
        solid = {p: s for p, s in self.blocks.items() if s != AIR}
        tmp = _CanvasB()
        tmp.blocks = solid
        tmp.nbt = {p: d for p, d in self.nbt.items() if p in solid}
        tmp.entities = []
        path = os.path.join(res, "data", "onepiece", "structure", "ships", f"{self.sid}.nbt")
        size, my = tmp.save(path)
        (x0, y0, z0), (x1, y1, z1) = self.bounds()
        meta = {
            "name": self.name,
            "template": f"onepiece:ships/{self.sid}",
            "bow": "east",
            "waterline": self.water_depth(),
            "faction": self.faction,
            "tiers": self.tiers,
            "crew": self.crew,
            "length": x1 - x0 + 1,
            "beam": z1 - z0 + 1,
            "height": y1 - y0 + 1,
            "blocks": len(solid),
        }
        jp = os.path.join(res, "data", "onepiece", "ships", f"{self.sid}.json")
        os.makedirs(os.path.dirname(jp), exist_ok=True)
        with open(jp, "w") as f:
            json.dump(meta, f, indent=2)
        print(f"{self.sid}: {len(solid)} blocks, {meta['length']}x{meta['height']}x{meta['beam']} (l x h x w), waterline {meta['waterline']}")
        return meta

    def preview(self, out_dir=PREVIEWS, views=("se", "nw"), cuts=(), title=None, scale=8, side=True):
        """Isometric pictures with the sea drawn around the hull, plus a flat side view (<id>_side.png) and a front
        view (<id>_front.png). Needs the landmarks renderer and vanilla textures."""
        import render
        os.makedirs(out_dir, exist_ok=True)
        blocks = dict(self.blocks)
        (x0, y0, z0), (x1, y1, z1) = self.bounds()
        for x in range(x0 - 4, x1 + 5):
            for z in range(z0 - 4, z1 + 5):
                if (x, 0, z) not in blocks or blocks[(x, 0, z)] == AIR:
                    blocks[(x, 0, z)] = "minecraft:water[level=0]"
        title = title or self.name
        outs = []
        for v in views:
            p = f"{out_dir}/{self.sid}_{v}.png"
            render.render(blocks, p, v, scale=scale, title=f"{title} (from the {'south-east' if v == 'se' else 'north-west' if v == 'nw' else v})")
            outs.append(p)
        for c in cuts:
            p = f"{out_dir}/{self.sid}_cut{c}.png"
            render.render(blocks, p, "se", cut=c, scale=scale, title=f"{title}: inside, cut at height {c}")
            outs.append(p)
        if side:
            p = f"{out_dir}/{self.sid}_side.png"
            self.elevation(p, axis="z", scale=scale, title=f"{title}: side view (bow to the right)")
            outs.append(p)
            p = f"{out_dir}/{self.sid}_front.png"
            self.elevation(p, axis="x", scale=scale, title=f"{title}: seen from the bow")
            outs.append(p)
        return outs

    def elevation(self, out, axis="z", scale=8, title=None):
        """Flat orthographic view: axis='z' looks along z (side view, +x to the right), axis='x' looks along -x
        (front view from the bow). Nearest block wins; its side colour is shaded by depth."""
        import render
        import numpy as np
        from PIL import Image, ImageDraw
        pts = {}
        for (x, y, z), s in self.blocks.items():
            if s == AIR or s.split("[")[0] in render.SKIP:
                continue
            if axis == "z":
                key, depth = (x, y), z
            else:
                key, depth = (-z, y), x  # viewer at the bow: the largest x is nearest
            if key not in pts or depth > pts[key][0]:
                pts[key] = (depth, s)
        if not pts:
            return
        us = [k[0] for k in pts]; vs = [k[1] for k in pts]
        u0, u1, v0, v1 = min(us), max(us), min(vs), max(vs)
        pad = 12
        W = (u1 - u0 + 1) * scale + 2 * pad
        H = (v1 - v0 + 1) * scale + 2 * pad + (30 if title else 0)
        img = Image.new("RGB", (W, H), (206, 224, 236))
        d = ImageDraw.Draw(img)
        # the sea
        sea_y = pad + (v1 - 0) * scale + (30 if title else 0)
        d.rectangle([0, sea_y + scale, W, H], fill=(96, 140, 210))
        depths = [p[0] for p in pts.values()]
        dmin, dmax = min(depths), max(depths)
        for (u, v), (depth, s) in pts.items():
            cols = render.block_colors(s)
            if cols is None:
                continue
            c = cols[1]
            t = 0.75 + 0.25 * ((depth - dmin) / max(1, dmax - dmin))
            c = tuple(int(min(255, cc * t)) for cc in c)
            px = pad + (u - u0) * scale
            py = pad + (v1 - v) * scale + (30 if title else 0)
            d.rectangle([px, py, px + scale - 1, py + scale - 1], fill=c)
        if title:
            d.text((pad, 8), title, fill=(30, 40, 60))
        img.save(out)
        return out


# ---------------------------------------------------------------- emblems
def bitmap_pattern(rows, palette):
    """Turns ASCII art (list of equal-length strings, top row first) + {char: block} into a pattern(u, v) function
    for sails. '.' or any char not in the palette = leave the sail colour."""
    h = len(rows)
    w = max(len(r) for r in rows)

    def pattern(u, v):
        i = int((u + 1) / 2 * w)
        j = int((1 - v) / 2 * h)
        i = min(w - 1, max(0, i))
        j = min(h - 1, max(0, j))
        ch = rows[j][i] if i < len(rows[j]) else "."
        return palette.get(ch)
    return pattern


def fit_bitmap(rows, palette, margin=0.15):
    """Like bitmap_pattern but leaves a margin of plain sail around the picture."""
    inner = bitmap_pattern(rows, palette)
    s = 1 - margin

    def pattern(u, v):
        if abs(u) > s or abs(v) > s:
            return None
        return inner(u / s, v / s)
    return pattern


# The Straw Hat Pirates' Jolly Roger: skull in a straw hat (yellow, red band), crossbones behind.
STRAW_HAT_ROWS = [
    ".......YYYYYY.......",
    "......YYYYYYYY......",
    "......YRRRRRRY......",
    "..YYYYYYRRRRYYYYYY..",
    "..YYYYYYYYYYYYYYYY..",
    "W......WWWWWW......W",
    ".W....WWWWWWWW....W.",
    "..W...WKKWWKKW...W..",
    "...W..WKKWWKKW..W...",
    "....W.WWWWWWWW.W....",
    ".....WWWWKKWWWW.....",
    "......WWWWWWWW......",
    "......WKWKWKWK......",
    ".....W.WWWWWW.W.....",
    "....W..........W....",
    "...W............W...",
    "..W..............W..",
]
STRAW_HAT = (STRAW_HAT_ROWS, {"Y": WOOL["yellow"], "R": WOOL["red"], "W": WOOL["white"], "K": WOOL["black"]})
STRAW_HAT_ON_BLACK = (STRAW_HAT_ROWS, {"Y": WOOL["yellow"], "R": WOOL["red"], "W": WOOL["white"], "K": WOOL["black"]})

# Plain skull and crossbones (white on whatever the sail/flag is).
SKULL_ROWS = [
    "W....WWWWWW....W",
    ".W..WWWWWWWW..W.",
    "..W.WWKKWWKKW.W.",
    "...WWWKKWWKKWW..",
    "....WWWWWWWWW...",
    "....WWWWKKWWW...",
    "...W.WWWWWWW.W..",
    "..W..WKWKWKW..W.",
    ".W....WWWWW....W",
    "W...............",
]
SKULL = (SKULL_ROWS, {"W": WOOL["white"], "K": WOOL["black"]})

# The Marine seagull (blue) with MARINE under it is drawn with text(); this is the gull alone.
GULL_ROWS = [
    "......BB....BB......",
    "....BBBBB..BBBBB....",
    "..BBBBBBBBBBBBBBBB..",
    "BBBBBBBBBBBBBBBBBBBB",
    "......BBBBBBBB......",
    "........BBBB........",
    ".........BB.........",
]
GULL = (GULL_ROWS, {"B": WOOL["blue"]})

# Buggy's mark: skull with a big red clown nose and crossbones, striped hat.
BUGGY_ROWS = [
    "....RWRWRWRW....",
    "...WWWWWWWWWW...",
    "W..WWWWWWWWWW..W",
    ".W.WWKKWWWWKKW.W",
    "..WWWKKWWWWKKWW.",
    "...WWWWRRRRWWW..",
    "...WWWWRRRRWWW..",
    "..W.WWWWWWWW.W..",
    ".W..WKWKWKWK..W.",
    "W....WWWWWW....W",
]
BUGGY = (BUGGY_ROWS, {"W": WOOL["white"], "K": WOOL["black"], "R": WOOL["red"]})

# Red Hair Pirates: skull with three scars over the left eye, crossed sabres behind.
RED_HAIR_ROWS = [
    "G....WWWWWW....G",
    ".G..WWWWWWWW..G.",
    "..G.WRKKWWKKW.G.",
    "...GWRKKWWKKWG..",
    "....WRWWWWWWW...",
    "....WWWWKKWWW...",
    "...G.WWWWWWW.G..",
    "..G..WKWKWKW..G.",
    ".G....WWWWW....G",
    "G...............",
]
RED_HAIR = (RED_HAIR_ROWS, {"W": WOOL["white"], "K": WOOL["black"], "R": WOOL["red"], "G": WOOL["light_gray"]})

# Heart Pirates: the smiling face with six spikes, in black (on the yellow submarine) or white (on a flag).
HEART_ROWS = [
    ".......KK.......",
    "..KK...KK...KK..",
    "...KKKKKKKKKK...",
    "....KK....KK....",
    "...KK..KK..KK...",
    "...KK......KK...",
    "...KK.K..K.KK...",
    "....KK....KK....",
    "...KKKKKKKKKK...",
    "..KK...KK...KK..",
    ".......KK.......",
]
HEART_BLACK = (HEART_ROWS, {"K": WOOL["black"]})
HEART_WHITE = (HEART_ROWS, {"K": WOOL["white"]})

# Kid Pirates: skull with Kid's spiky hair and goggles.
KID_ROWS = [
    ".R.R.RRRRRR.R.R.",
    "..RRRRRRRRRRRR..",
    "...RRRRRRRRRR...",
    "W..KKKKKKKKKK..W",
    ".W.KWWKKKKWWK.W.",
    "..WWWKKWWKKWWW..",
    "...WWWWWWWWWW...",
    "...WWWWKKWWWW...",
    "..W.WWWWWWWW.W..",
    ".W..WKWKWKWK..W.",
    "W....WWWWWW....W",
]
KID = (KID_ROWS, {"W": WOOL["white"], "K": WOOL["black"], "R": WOOL["red"]})

# Whitebeard: skull with the big crescent moustache and crossbones.
WHITEBEARD_ROWS = [
    "W....WWWWWW....W",
    ".W..WWWWWWWW..W.",
    "..W.WWKKWWKKW.W.",
    "...WWWKKWWKKWW..",
    "....WWWWWWWWW...",
    "..WWWWWWKKWWWWW.",
    ".WWW.WWWWWWW.WWW",
    "..W..WKWKWKW..W.",
    ".W....WWWWW....W",
    "W...............",
]
WHITEBEARD = (WHITEBEARD_ROWS, {"W": WOOL["white"], "K": WOOL["black"]})

# Alvida: skull with a heart on the forehead, pink.
ALVIDA_ROWS = [
    "W....WWWWWW....W",
    ".W..WWPWWPWW..W.",
    "..W.WWPPPPWW.W..",
    "...WWWKKWKKWW...",
    "....WWWWWWWWW...",
    "....WWWWKKWWW...",
    "...W.WWWWWWW.W..",
    "..W..WKWKWKW..W.",
    ".W....WWWWW....W",
    "W...............",
]
ALVIDA = (ALVIDA_ROWS, {"W": WOOL["white"], "K": WOOL["black"], "P": WOOL["pink"]})

# Black Cat Pirates (Kuro): a cat skull with ears and whiskers.
BLACK_CAT_ROWS = [
    "W.WW......WW...W",
    ".WWWW....WWWW.W.",
    "..WWWWWWWWWWW...",
    "...WWKKWWKKWW...",
    "...WWKKWWKKWW...",
    "..WWWWWWWWWWWW..",
    "..W.WWWWKKWW.W..",
    ".W..WKWKWKWK..W.",
    "W....WWWWWW....W",
]
BLACK_CAT = (BLACK_CAT_ROWS, {"W": WOOL["white"], "K": WOOL["black"]})


def stripes(color_a, color_b, width=2, axis="u"):
    """Vertical (axis='u') or horizontal stripes for a sail or tent."""
    def pattern(u, v):
        t = u if axis == "u" else v
        k = int((t + 1) * 7 / width)
        return color_a if k % 2 == 0 else color_b
    return pattern


def text_rows(msg):
    """ASCII rows for big 3x5 letters, usable as a bitmap with palette {'#': block}."""
    rows = ["" for _ in range(5)]
    for ch in msg.upper():
        g = FONT.get(ch, FONT[" "])
        for r in range(5):
            rows[r] += "".join("#" if c == "1" else "." for c in g[r]) + "."
    return rows


def write_all(ships, res=RES_DEFAULT, previews=PREVIEWS, cuts=()):
    """Builds every ship module given (list of module names), saves templates + json + previews."""
    import importlib
    sys.path.insert(0, HERE)
    out = {}
    for name in ships:
        m = importlib.import_module(name)
        ship = m.build()
        out[name] = ship.save(res)
        ship.preview(previews, cuts=getattr(m, "CUTS", cuts))
    return out
