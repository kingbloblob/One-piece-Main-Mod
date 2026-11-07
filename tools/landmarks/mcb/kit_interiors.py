"""Room kit for the newest Builder skill rules: furniture from shape blocks, rooms 20-35% furnished, lights on the
walls (about one per 10 floor cells), a clear path from every door.

    from mcb.kit_interiors import furnish_kit, coverage
    furnish_kit(bb, room, y, h, "mess", wood="spruce", seed=1, doors=[(x, z), ...])

room = (x1, z1, x2, z2) interior floor cells, y = first air layer, h = clear height (ceiling solid at y + h).
Pieces (usable on their own): chair, bench, stool, table_group, bar_counter, kitchen_line, bunk, bed_nook,
bookshelf_aisle, storage_wall, rug, wall_lights. Kinds: mess, dining, tavern, barracks, kitchen, office, armory,
infirmary, storeroom, library, bedroom, cell, radio, workshop, captain.
Stair `facing` = the side the tall back is on (the way it climbs)."""
import numpy as np

AIR = "minecraft:air"
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
DV = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}
CARPETS = ["red", "blue", "green", "brown", "gray", "cyan", "light_gray", "purple", "orange", "yellow", "white", "black"]


def _st(block, facing, half="bottom"):
    return f"{block}[facing={facing},half={half}]"


class Plan:
    """Occupancy of one room's floor: 0 free, 1 furniture, 2 kept clear (door approaches, aisles)."""

    def __init__(self, room, doors, wide=False):
        self.x1, self.z1, self.x2, self.z2 = room
        self.g = np.zeros((self.x2 - self.x1 + 1, self.z2 - self.z1 + 1), np.int8)
        for (dx, dz) in doors:
            # the door cell sits in the wall: keep the 3x2 patch inside the room in front of it clear
            for ox in range(-1, 2):
                for oz in range(-1, 2):
                    for k in (1, 2):
                        for (ax, az) in ((dx + ox, dz + oz * k), (dx + ox * k, dz + oz)):
                            self.keep(ax, az)

    def inside(self, x, z):
        return self.x1 <= x <= self.x2 and self.z1 <= z <= self.z2

    def keep(self, x, z):
        if self.inside(x, z) and self.g[x - self.x1, z - self.z1] == 0:
            self.g[x - self.x1, z - self.z1] = 2

    def free(self, cells):
        return all(self.inside(x, z) and self.g[x - self.x1, z - self.z1] == 0 for (x, z) in cells)

    def take(self, cells):
        for (x, z) in cells:
            self.g[x - self.x1, z - self.z1] = 1

    def cover(self):
        return float((self.g == 1).sum()) / self.g.size


# ------------------------------------------------------------------ pieces
def chair(bb, x, y, z, back, wood="spruce", arms=True):
    """A chair: a bottom stair with its back on side `back`, wall-sign armrests on both sides."""
    bb.set(x, y, z, _st(f"minecraft:{wood}_stairs", back))
    if arms:
        a, b = ("east", "west") if back in ("north", "south") else ("south", "north")
        for side in (a, b):
            ox, oz = DV[side]
            if bb.get_region(x + ox, y, z + oz, x + ox, y, z + oz)[0, 0, 0] in (0, 1):
                bb.set(x + ox, y, z + oz, f"minecraft:{wood}_wall_sign[facing={side}]")


def stool(bb, x, y, z, wood="spruce", cloth="red"):
    bb.set(x, y, z, f"minecraft:{wood}_fence")
    bb.set(x, y + 1, z, f"minecraft:{cloth}_carpet")


def table_group(pl, bb, x, z, y, length, axis="x", wood="spruce", cloth=None, chairs=True, arms=False):
    """A 2-deep table of upside-down stairs facing each other (solid tops, carpet placemats) with chairs along both
    long sides, backs away from the table. (x, z) = first cell; runs `length` along axis. Returns True if placed."""
    if axis == "x":
        top = [(x + i, z + j) for i in range(length) for j in (0, 1)]
        seats = [(x + i, z - 1, "north") for i in range(length)] + [(x + i, z + 2, "south") for i in range(length)]
        ring = [(x - 1, z), (x - 1, z + 1), (x + length, z), (x + length, z + 1)]
    else:
        top = [(x + j, z + i) for i in range(length) for j in (0, 1)]
        seats = [(x - 1, z + i, "west") for i in range(length)] + [(x + 2, z + i, "east") for i in range(length)]
        ring = [(x, z - 1), (x + 1, z - 1), (x, z + length), (x + 1, z + length)]
    if not pl.free(top + [(a, b) for a, b, _ in seats]):
        return False
    for (a, b) in top:
        if axis == "x":
            face = "south" if b == z else "north"
        else:
            face = "east" if a == x else "west"
        bb.set(a, y, b, _st(f"minecraft:{wood}_stairs", face, "top"))
    for k, (a, b) in enumerate(top):
        if cloth and k % 2 == 0:
            bb.set(a, y + 1, b, f"minecraft:{cloth}_carpet")
    if length >= 3:
        mid = top[len(top) // 2]
        bb.set(mid[0], y + 1, mid[1], "minecraft:candle[candles=3,lit=true]")
    pl.take(top)
    if chairs:
        for (a, b, back) in seats:
            chair(bb, a, y, b, back, wood, arms=False)
        pl.take([(a, b) for a, b, _ in seats])
    for c in ring:
        pl.keep(*c)
    return True


def bench(bb, x, y, z, length, back, wood="spruce", axis="x"):
    """A bench of stairs with sign ends."""
    for i in range(length):
        a, b = (x + i, z) if axis == "x" else (x, z + i)
        bb.set(a, y, b, _st(f"minecraft:{wood}_stairs", back))
    e1, e2 = ((x - 1, z), (x + length, z)) if axis == "x" else ((x, z - 1), (x, z + length))
    f1, f2 = ("west", "east") if axis == "x" else ("north", "south")
    bb.set(e1[0], y, e1[1], f"minecraft:{wood}_wall_sign[facing={f1}]")
    bb.set(e2[0], y, e2[1], f"minecraft:{wood}_wall_sign[facing={f2}]")


def bar_counter(pl, bb, x, z, y, length, staff, wood="spruce", axis="x", stools=True):
    """A bar: upside-down stairs with the solid half toward the staff side, barrels + shelves behind, stools in
    front. `staff` = side (north/south/east/west) the barman stands on."""
    cells = [(x + i, z) if axis == "x" else (x, z + i) for i in range(length)]
    sx, sz = DV[staff]
    if not pl.free(cells):
        return False
    for (a, b) in cells:
        bb.set(a, y, b, _st(f"minecraft:{wood}_stairs", staff, "top"))
    for k, (a, b) in enumerate(cells):
        if k % 3 == 1:
            bb.set(a, y + 1, b, "minecraft:candle[candles=2,lit=true]" if k % 2 else "minecraft:brown_candle[candles=1,lit=true]")
    pl.take(cells)
    behind = [(a + 2 * sx, b + 2 * sz) for (a, b) in cells]
    for k, (a, b) in enumerate(behind):
        if pl.inside(a, b):
            bb.set(a, y, b, "minecraft:barrel[facing=up,open=false]" if k % 3 else "minecraft:smoker[facing=" + OPP[staff] + ",lit=false]")
            bb.set(a, y + 1, b, _st(f"minecraft:{wood}_stairs", staff, "top") if k % 2 else f"minecraft:{wood}_slab[type=bottom]")
            pl.take([(a, b)])
    for (a, b) in cells:
        pl.keep(a + sx, b + sz)
    if stools:
        for k, (a, b) in enumerate(cells):
            if k % 2 == 0 and pl.free([(a - sx, b - sz)]):
                stool(bb, a - sx, y, b - sz, wood, "red")
                pl.take([(a - sx, b - sz)])
    return True


def wall_run(pl, bb, y, h, side, items, start=0, step=1):
    """Put `items` (a list of block states or None) along the wall on `side`, from offset `start`."""
    x1, z1, x2, z2 = pl.x1, pl.z1, pl.x2, pl.z2
    if side in ("north", "south"):
        z = z1 if side == "north" else z2
        cells = [(x, z) for x in range(x1, x2 + 1)]
    else:
        x = x1 if side == "west" else x2
        cells = [(x, z) for z in range(z1, z2 + 1)]
    placed = 0
    for k, c in enumerate(cells[start::step]):
        it = items[k % len(items)]
        if it is None or not pl.free([c]):
            continue
        if isinstance(it, tuple):
            for dy, s in enumerate(it):
                if s:
                    bb.set(c[0], y + dy, c[1], s)
        else:
            bb.set(c[0], y, c[1], it)
        pl.take([c])
        placed += 1
    return placed


def bunk(pl, bb, x, z, y, head, wood="spruce", color="light_blue"):
    """A bunk bed: two beds, the top one on an upside-down slab frame, fence posts at the foot. head = side the
    pillow is on. (x, z) = head cell."""
    fx, fz = x - DV[head][0], z - DV[head][1]
    if not pl.free([(x, z), (fx, fz)]):
        return False
    for yy in (y, y + 2):
        bb.set(x, yy, z, f"minecraft:{color}_bed[facing={head},part=head]")
        bb.set(fx, yy, fz, f"minecraft:{color}_bed[facing={head},part=foot]")
    bb.set(x, y + 1, z, f"minecraft:{wood}_slab[type=top]")
    bb.set(fx, y + 1, fz, f"minecraft:{wood}_slab[type=top]")
    pl.take([(x, z), (fx, fz)])
    return True


def wall_lights(pl, bb, y, h, every=10, doors=(), light="minecraft:lantern[hanging=true]", panel="minecraft:sea_lantern"):
    """About one light per `every` floor cells: lanterns hung under the ceiling along the walls (one every ~4 wall
    cells), the rest as flush light panels set into the ceiling of big rooms (hidden light, no lantern forest)."""
    x1, z1, x2, z2 = pl.x1, pl.z1, pl.x2, pl.z2
    area = (x2 - x1 + 1) * (z2 - z1 + 1)
    want = max(2, area // every)
    ring = [(x, z1) for x in range(x1, x2 + 1)] + [(x2, z) for z in range(z1 + 1, z2 + 1)] + \
           [(x, z2) for x in range(x2 - 1, x1 - 1, -1)] + [(x1, z) for z in range(z2 - 1, z1, -1)]
    on_wall = min(want, max(2, len(ring) // 4))
    step = max(1, len(ring) / float(on_wall))
    ly = y + h - 1
    n = 0
    for k in range(on_wall):
        a, b = ring[int(k * step + step / 2) % len(ring)]
        if bb.get_region(a, ly, b, a, ly, b)[0, 0, 0] in (0, 1):
            bb.set(a, ly, b, light); n += 1
    rest = want - n
    if rest > 0 and x2 - x1 >= 6 and z2 - z1 >= 6 and panel:
        rest = max(1, rest // 3)              # a panel lights a 7x7 patch, so a third of the lanterns' count is plenty
        cols = max(1, int(round((rest * (x2 - x1) / max(1, z2 - z1)) ** 0.5)))
        rows = max(1, (rest + cols - 1) // cols)
        for i in range(cols):
            for j in range(rows):
                a = x1 + 2 + int((x2 - x1 - 4) * (i + 0.5) / cols)
                b = z1 + 2 + int((z2 - z1 - 4) * (j + 0.5) / rows)
                if bb.get_region(a, y + h, b, a, y + h, b)[0, 0, 0] > 1:
                    bb.set(a, y + h, b, panel)


def rug(pl, bb, y, x1, z1, x2, z2, color, border=None):
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if pl.inside(x, z) and pl.g[x - pl.x1, z - pl.z1] != 1 and bb.get_region(x, y, z, x, y, z)[0, 0, 0] in (0, 1):
                edge = border and (x in (x1, x2) or z in (z1, z2))
                bb.set(x, y, z, f"minecraft:{border if edge else color}_carpet")


# ------------------------------------------------------------------ rooms
def _long(pl):
    return "x" if pl.x2 - pl.x1 >= pl.z2 - pl.z1 else "z"


def _tables(pl, bb, y, wood, cloth, length=4, gap=2):
    """Rows of table groups through the middle: chairs, 2-deep table, chairs, then a 1-wide aisle; groups along
    the row are split by `gap` free cells."""
    ax = _long(pl)
    n = 0
    a1, a2, b1, b2 = (pl.x1, pl.x2, pl.z1, pl.z2) if ax == "x" else (pl.z1, pl.z2, pl.x1, pl.x2)
    rows = max(1, (b2 - b1 + 1 - 1) // 5)
    off = b1 + 1 + ((b2 - b1 + 1 - 1) - rows * 5 + 1) // 2
    for r in range(rows):
        b = off + r * 5 + 1
        if b + 2 > b2:
            break
        a = a1 + 1
        while a + length - 1 <= a2 - 1:
            if ax == "x":
                ok = table_group(pl, bb, a, b, y, length, "x", wood, cloth)
            else:
                ok = table_group(pl, bb, b, a, y, length, "z", wood, cloth)
            n += ok
            a += length + gap if ok else 1
    return n


def _shelf(wood):
    return (f"minecraft:barrel[facing=up,open=false]", f"minecraft:{wood}_slab[type=bottom]")


def furnish_kit(bb, room, y, h, kind, wood="spruce", seed=0, doors=(), accent="red"):
    """Furnish one room by kind with the shape-block kit. Returns the floor coverage (0..1)."""
    rng = np.random.default_rng(seed)
    x1, z1, x2, z2 = room
    if x2 - x1 < 2 or z2 - z1 < 2:
        return 0.0
    pl = Plan(room, [d for d in doors if x1 - 1 <= d[0] <= x2 + 1 and z1 - 1 <= d[1] <= z2 + 1])
    W, D = x2 - x1 + 1, z2 - z1 + 1
    sides = ["north", "south", "west", "east"]
    long_sides = ["north", "south"] if W >= D else ["west", "east"]
    short_sides = [s for s in sides if s not in long_sides]
    k = kind
    if k in ("mess", "dining"):
        _tables(pl, bb, y, wood, accent if k == "dining" else None, length=4 if max(W, D) > 9 else 3)
        wall_run(pl, bb, y, h, short_sides[0], [_shelf(wood), "minecraft:barrel[facing=up,open=false]", None])
    elif k == "tavern":
        if long_sides[0] in ("north", "south"):
            bar_counter(pl, bb, x1 + 1, z1 + 2, y, max(3, W - 4), "north", wood, "x")
        else:
            bar_counter(pl, bb, x1 + 2, z1 + 1, y, max(3, D - 4), "west", wood, "z")
        _tables(pl, bb, y, wood, accent, length=2, gap=1)
    elif k == "barracks":
        for s in long_sides:
            if s in ("north", "south"):
                z = z1 if s == "north" else z2
                for x in range(x1, x2 + 1, 3):
                    bunk(pl, bb, x, z, y, s, wood, "light_blue" if accent == "red" else accent)
                    if pl.free([(x + 1, z)]) and x + 1 <= x2:
                        bb.set(x + 1, y, z, "minecraft:chest[facing=" + OPP[s] + ",type=single]")
                        bb.set(x + 1, y + 1, z, f"minecraft:{wood}_trapdoor[facing={OPP[s]},half=bottom,open=false]")
                        pl.take([(x + 1, z)])
            else:
                x = x1 if s == "west" else x2
                for z in range(z1, z2 + 1, 3):
                    bunk(pl, bb, x, z, y, s, wood, "light_blue" if accent == "red" else accent)
                    if pl.free([(x, z + 1)]) and z + 1 <= z2:
                        bb.set(x, y, z + 1, "minecraft:chest[facing=" + OPP[s] + ",type=single]")
                        bb.set(x, y + 1, z + 1, f"minecraft:{wood}_trapdoor[facing={OPP[s]},half=bottom,open=false]")
                        pl.take([(x, z + 1)])
        if min(W, D) >= 8:
            cx, cz = (x1 + x2) // 2 - 1, (z1 + z2) // 2
            table_group(pl, bb, cx, cz, y, 3, "x", wood, None)
    elif k == "kitchen":
        line = [("minecraft:smoker[facing=%s,lit=true]",), ("minecraft:furnace[facing=%s,lit=false]",), ("minecraft:water_cauldron[level=3]",),
                (_st(f"minecraft:{wood}_stairs", "%s", "top"), "minecraft:bamboo_block[axis=y]"), ("minecraft:barrel[facing=up,open=false]", "minecraft:flower_pot"),
                (_st(f"minecraft:{wood}_stairs", "%s", "top"),)]
        for i, s in enumerate(long_sides):
            face = OPP[s]
            wall_run(pl, bb, y, h, s, [tuple(p.replace("%s", face) for p in t) for t in line[i::1]] if i == 0 else
                     [(_st(f"minecraft:{wood}_stairs", face, "top"), "minecraft:barrel[facing=up,open=false]" if j % 3 == 0 else None) for j in range(3)])
        cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
        isl = [(cx - 1, cz), (cx, cz), (cx + 1, cz)]
        if pl.free(isl):
            for (a, b) in isl:
                bb.set(a, y, b, f"minecraft:{wood}_planks"); bb.set(a, y + 1, b, "minecraft:stone_pressure_plate" if a == cx else AIR)
            bb.set(cx - 1, y + 1, cz, "minecraft:melon")
            pl.take(isl)
        for a in range(x1 + 1, x2, 3):
            if h >= 4:
                bb.set(a, y + h - 1, cz, "minecraft:iron_chain[axis=y]")
    elif k in ("office", "captain"):
        s = long_sides[0]
        wall_run(pl, bb, y, h, s, [("minecraft:bookshelf", "minecraft:bookshelf"), ("minecraft:bookshelf", "minecraft:bookshelf"), ("minecraft:chiseled_bookshelf[facing=%s]" % OPP[s], "minecraft:flower_pot")])
        cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
        if s in ("north", "south"):
            dz = z1 + 2 if s == "north" else z2 - 2
            desk = [(cx - 1, dz), (cx, dz), (cx + 1, dz)]
            if pl.free(desk):
                for (a, b) in desk:
                    bb.set(a, y, b, _st(f"minecraft:{'dark_oak' if k == 'captain' else wood}_stairs", OPP[s], "top"))
                bb.set(cx - 1, y + 1, dz, "minecraft:lantern[hanging=false]"); bb.set(cx + 1, y + 1, dz, "minecraft:flower_pot")
                pl.take(desk)
                chair(bb, cx, y, dz - 1 if s == "north" else dz + 1, s, wood)
                pl.take([(cx, dz - 1 if s == "north" else dz + 1)])
        else:
            dx = x1 + 2 if s == "west" else x2 - 2
            desk = [(dx, cz - 1), (dx, cz), (dx, cz + 1)]
            if pl.free(desk):
                for (a, b) in desk:
                    bb.set(a, y, b, _st(f"minecraft:{wood}_stairs", OPP[s], "top"))
                bb.set(dx, y + 1, cz - 1, "minecraft:lantern[hanging=false]")
                pl.take(desk)
                chair(bb, dx - 1 if s == "west" else dx + 1, y, cz, s, wood)
                pl.take([(dx - 1 if s == "west" else dx + 1, cz)])
        o = long_sides[1]
        wall_run(pl, bb, y, h, o, [None, _st(f"minecraft:{wood}_stairs", s), _st(f"minecraft:{wood}_stairs", s), None], start=1)
        wall_run(pl, bb, y, h, short_sides[0], [("minecraft:barrel[facing=up,open=false]", "minecraft:lantern[hanging=false]"), "minecraft:lectern[facing=%s]" % OPP[short_sides[0]]], start=1, step=3)
        rug(pl, bb, y, cx - 2, cz - 1, cx + 2, cz + 2, accent, "white")
    elif k == "armory":
        rack = [("minecraft:smithing_table",), ("minecraft:barrel[facing=up,open=false]", "minecraft:iron_bars"),
                ("minecraft:grindstone[face=floor,facing=north]",), ("minecraft:chest[facing=%s,type=single]",),
                ("minecraft:anvil[facing=north]",), ("minecraft:barrel[facing=up,open=false]", f"minecraft:{wood}_slab[type=bottom]")]
        for s in sides[:3]:
            wall_run(pl, bb, y, h, s, [tuple(p.replace("%s", OPP[s]) for p in t) for t in rack[sides.index(s):] + rack], start=1)
        cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
        if pl.free([(cx, cz), (cx + 1, cz)]):
            bb.set(cx, y, cz, "minecraft:target"); bb.set(cx + 1, y, cz, "minecraft:hay_block[axis=y]"); pl.take([(cx, cz), (cx + 1, cz)])
    elif k == "infirmary":
        s = long_sides[0]
        if s in ("north", "south"):
            for x in range(x1 + 1, x2, 3):
                if pl.free([(x, z1), (x, z1 + 1)]):
                    bb.set(x, y, z1, "minecraft:white_bed[facing=north,part=head]"); bb.set(x, y, z1 + 1, "minecraft:white_bed[facing=north,part=foot]")
                    pl.take([(x, z1), (x, z1 + 1)])
                    if x + 1 <= x2 and pl.free([(x + 1, z1)]):
                        bb.set(x + 1, y, z1, "minecraft:white_stained_glass_pane"); bb.set(x + 1, y + 1, z1, "minecraft:white_stained_glass_pane"); pl.take([(x + 1, z1)])
        else:
            for z in range(z1 + 1, z2, 3):
                if pl.free([(x1, z), (x1 + 1, z)]):
                    bb.set(x1, y, z, "minecraft:white_bed[facing=west,part=head]"); bb.set(x1 + 1, y, z, "minecraft:white_bed[facing=west,part=foot]")
                    pl.take([(x1, z), (x1 + 1, z)])
        wall_run(pl, bb, y, h, long_sides[1], [("minecraft:water_cauldron[level=3]",), ("minecraft:brewing_stand",), None,
                                              ("minecraft:barrel[facing=up,open=false]", "minecraft:white_candle[candles=2,lit=true]"),
                                              (_st(f"minecraft:{wood}_stairs", long_sides[0]),)], start=1)
    elif k == "storeroom":
        for s in sides:
            wall_run(pl, bb, y, h, s, [("minecraft:barrel[facing=up,open=false]", "minecraft:barrel[facing=up,open=false]"),
                                       (f"minecraft:{wood}_planks", f"minecraft:{wood}_trapdoor[facing=north,half=bottom,open=false]"),
                                       ("minecraft:chest[facing=%s,type=single]" % OPP[s],), ("minecraft:hay_block[axis=y]",)])
        cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
        if pl.free([(cx, cz), (cx + 1, cz), (cx, cz + 1)]):
            bb.set(cx, y, cz, "minecraft:barrel[facing=up,open=false]"); bb.set(cx, y + 1, cz, "minecraft:barrel[facing=up,open=false]")
            bb.set(cx + 1, y, cz, f"minecraft:{wood}_planks"); bb.set(cx, y, cz + 1, "minecraft:composter[level=0]")
            pl.take([(cx, cz), (cx + 1, cz), (cx, cz + 1)])
    elif k == "library":
        ax = _long(pl)
        if ax == "x":
            for z in range(z1 + 1, z2 - 1, 3):
                cells = [(x, z) for x in range(x1 + 1, x2 - 3)]
                if pl.free(cells):
                    for (a, b) in cells:
                        bb.set(a, y, b, "minecraft:bookshelf"); bb.set(a, y + 1, b, "minecraft:bookshelf")
                    pl.take(cells)
        else:
            for x in range(x1 + 1, x2 - 1, 3):
                cells = [(x, z) for z in range(z1 + 1, z2 - 3)]
                if pl.free(cells):
                    for (a, b) in cells:
                        bb.set(a, y, b, "minecraft:bookshelf"); bb.set(a, y + 1, b, "minecraft:bookshelf")
                    pl.take(cells)
        rx, rz = (x2 - 2, (z1 + z2) // 2) if ax == "x" else ((x1 + x2) // 2, z2 - 2)
        if pl.free([(rx, rz)]):
            bb.set(rx, y, rz, "minecraft:lectern[facing=west]"); pl.take([(rx, rz)])
    elif k == "bedroom":
        s = short_sides[0]
        hx, hz = ((x1 + x2) // 2, z1) if s == "north" else ((x1 + x2) // 2, z2) if s == "south" else (x1, (z1 + z2) // 2) if s == "west" else (x2, (z1 + z2) // 2)
        fx, fz = hx - DV[s][0], hz - DV[s][1]
        if pl.free([(hx, hz), (fx, fz)]):
            bb.set(hx, y, hz, f"minecraft:{accent}_bed[facing={s},part=head]"); bb.set(fx, y, fz, f"minecraft:{accent}_bed[facing={s},part=foot]")
            pl.take([(hx, hz), (fx, fz)])
            for o in (-1, 1):
                nx, nz = (hx + o, hz) if s in ("north", "south") else (hx, hz + o)
                if pl.free([(nx, nz)]):
                    bb.set(nx, y, nz, "minecraft:barrel[facing=up,open=false]"); bb.set(nx, y + 1, nz, "minecraft:lantern[hanging=false]" if o < 0 else "minecraft:flower_pot")
                    pl.take([(nx, nz)])
            rug(pl, bb, y, min(hx, fx) - 1 - (s in ("west", "east")) * 2, min(hz, fz) - 1 - (s in ("north", "south")) * 2,
                max(hx, fx) + 1 + (s in ("west", "east")) * 2, max(hz, fz) + 1 + (s in ("north", "south")) * 2, accent)
        o = long_sides[0]
        wall_run(pl, bb, y, h, o, [None, (f"minecraft:{wood}_planks", f"minecraft:{wood}_planks"), ("minecraft:chest[facing=%s,type=single]" % OPP[o],), None,
                                   (_st(f"minecraft:{wood}_stairs", OPP[o], "top"), "minecraft:flower_pot")])
    elif k == "cell":
        wall_run(pl, bb, y, h, long_sides[0], [("minecraft:hay_block[axis=y]",), None, ("minecraft:cauldron",), None])
        wall_run(pl, bb, y, h, short_sides[0], [None, ("minecraft:iron_chain[axis=y]",)])
    elif k == "radio":
        s = long_sides[0]
        wall_run(pl, bb, y, h, s, [(_st(f"minecraft:{wood}_stairs", OPP[s], "top"), "minecraft:daylight_detector[inverted=false,power=0]"),
                                   (_st(f"minecraft:{wood}_stairs", OPP[s], "top"), "minecraft:turtle_egg[eggs=1,hatch=0]"),
                                   (_st(f"minecraft:{wood}_stairs", OPP[s], "top"), "minecraft:observer[facing=%s,powered=false]" % s)])
        cx, cz = (x1 + x2) // 2 - 1, (z1 + z2) // 2
        table_group(pl, bb, cx, cz, y, 3, "x", wood, "blue")
        wall_run(pl, bb, y, h, long_sides[1], [("minecraft:cartography_table",), None, ("minecraft:lectern[facing=%s]" % s,), None], start=1)
    elif k == "workshop":
        wall_run(pl, bb, y, h, long_sides[0], [("minecraft:crafting_table",), ("minecraft:stonecutter[facing=north]",), (_st(f"minecraft:{wood}_stairs", OPP[long_sides[0]], "top"), "minecraft:lantern[hanging=false]"),
                                               ("minecraft:fletching_table",), ("minecraft:barrel[facing=up,open=false]",), ("minecraft:loom[facing=north]",)])
        wall_run(pl, bb, y, h, long_sides[1], [(f"minecraft:{wood}_planks", "minecraft:barrel[facing=up,open=false]"), None, ("minecraft:anvil[facing=north]",), None])
    else:
        _tables(pl, bb, y, wood, accent, length=2, gap=2)
    if pl.cover() < 0.18 and k not in ("cell", "library") and W >= 7 and D >= 7:
        # sparse room: a small table group in the free middle (skill rule: 20-35% of floor cells furnished)
        cx, cz = (x1 + x2) // 2 - 1, (z1 + z2) // 2
        table_group(pl, bb, cx, cz, y, 2, "x", wood, accent)
    wall_lights(pl, bb, y, h, 10)
    return pl.cover()


def coverage(bb, room, y):
    """Share of floor cells with something standing on them (for checking the 20-35% rule)."""
    x1, z1, x2, z2 = room
    reg = bb.get_region(x1, y, z1, x2, y, z2)
    return float((reg > 1).sum()) / reg.size
