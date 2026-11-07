"""Shared pieces for the town rebuilds: furnished houses in several styles, the town well, market stalls, a pier,
windmill, lamp posts, gardens and trees. Every house gets real rooms (beds, kitchens, tables), so the townsfolk
system finds homes, work blocks and bars in them.

Houses are archkit houses (compound plans, varied roofs, add-ons; neighbours kept different), paths, trees, lamps,
wells and gardens use landkit (organic paths, branched trees with understory, ground_y everywhere), so a town is not
a grid of boxes on a plate. Site-level shaping needs to know where everything stands, so it is opt-in: plot()
(a house on a terrace) and landscape() (relief and rocks, called last). The old house is kept as legacy=True."""
import math, random
from canvas import *
import interiors as I
import archkit as A
import landkit as L

FH = 4  # storey height (3 rows of room + the beam / floor row), as archkit

STYLES = {
    # wall, frame/post, floor, roof stairs base, roof full, window, door wood
    "east_blue": ("minecraft:white_terracotta", "minecraft:stripped_spruce_log[axis=y]", "minecraft:spruce_planks", "minecraft:spruce", "minecraft:spruce_planks", "minecraft:glass_pane", "spruce"),
    "cottage":   ("minecraft:oak_planks", "minecraft:oak_log[axis=y]", "minecraft:oak_planks", "minecraft:dark_oak", "minecraft:dark_oak_planks", "minecraft:glass_pane", "oak"),
    "stone":     ("minecraft:stone_bricks", "minecraft:polished_andesite", "minecraft:spruce_planks", "minecraft:deepslate_tile", "minecraft:deepslate_tiles", "minecraft:glass_pane", "spruce"),
    "brick":     ("minecraft:bricks", "minecraft:stripped_dark_oak_log[axis=y]", "minecraft:spruce_planks", "minecraft:dark_oak", "minecraft:dark_oak_planks", "minecraft:glass_pane", "dark_oak"),
    "plaster":   ("minecraft:white_concrete", "minecraft:stripped_oak_log[axis=y]", "minecraft:birch_planks", "minecraft:red_nether_brick", "minecraft:red_nether_bricks", "minecraft:glass_pane", "birch"),
    "orange":    ("minecraft:orange_terracotta", "minecraft:stripped_spruce_log[axis=y]", "minecraft:spruce_planks", "minecraft:spruce", "minecraft:spruce_planks", "minecraft:glass_pane", "spruce"),
    "sand":      ("minecraft:smooth_sandstone", "minecraft:cut_sandstone", "minecraft:jungle_planks", None, "minecraft:smooth_sandstone", "minecraft:glass_pane", "jungle"),
    "snow":      ("minecraft:spruce_planks", "minecraft:stripped_spruce_log[axis=y]", "minecraft:spruce_planks", "minecraft:spruce", "minecraft:spruce_planks", "minecraft:glass_pane", "spruce"),
    "shack":     ("minecraft:spruce_planks", "minecraft:spruce_log[axis=y]", "minecraft:spruce_planks", "minecraft:spruce", "minecraft:spruce_planks", "minecraft:glass_pane", "spruce"),
    "marine":    ("minecraft:white_concrete", "minecraft:light_blue_concrete", "minecraft:birch_planks", "minecraft:prismarine_brick", "minecraft:prismarine_bricks", "minecraft:glass_pane", "birch"),
}
HOME_KINDS = ("bedroom", "kitchen", "dining", "study", "storage", "workshop", "library", "tavern")


# Wall palettes: the main block and a few close variants mixed in (a gentle gradient, darker and rougher near the ground).
VARIANTS = {
    "minecraft:white_terracotta": ("minecraft:calcite", "minecraft:white_terracotta", "minecraft:diorite"),
    "minecraft:oak_planks": ("minecraft:oak_planks", "minecraft:stripped_oak_wood[axis=y]", "minecraft:oak_planks"),
    "minecraft:stone_bricks": ("minecraft:cracked_stone_bricks", "minecraft:mossy_stone_bricks", "minecraft:stone_bricks"),
    "minecraft:bricks": ("minecraft:bricks", "minecraft:mud_bricks", "minecraft:bricks"),
    "minecraft:white_concrete": ("minecraft:white_concrete", "minecraft:calcite", "minecraft:white_concrete_powder"),
    "minecraft:orange_terracotta": ("minecraft:orange_terracotta", "minecraft:terracotta", "minecraft:orange_terracotta"),
    "minecraft:smooth_sandstone": ("minecraft:smooth_sandstone", "minecraft:sandstone", "minecraft:cut_sandstone"),
    "minecraft:spruce_planks": ("minecraft:spruce_planks", "minecraft:stripped_spruce_wood[axis=y]", "minecraft:spruce_planks"),
}
BASE = {"sand": ("minecraft:sandstone", "minecraft:sandstone_stairs"), "marine": ("minecraft:polished_andesite", "minecraft:polished_andesite_stairs"),
        "stone": ("minecraft:cobblestone", "minecraft:cobblestone_stairs"), "snow": ("minecraft:cobblestone", "minecraft:cobblestone_stairs"),
        "brick": ("minecraft:stone_bricks", "minecraft:stone_brick_stairs"), "plaster": ("minecraft:stone_bricks", "minecraft:stone_brick_stairs")}
JETTY = ("east_blue", "cottage", "brick", "plaster", "orange", "snow")
SIDES = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}


def _beam(post, axis):
    n = post.split("[")[0]
    return f"{n}[axis={axis}]" if ("log" in n or "wood" in n) else post


def _empty(b, x, y, z):
    s = b.get(x, y, z)
    return s in (None, AIR) or "short_grass" in s or s.endswith("snow[layers=1]")


def _side_cells(f, ax0, az0, ax1, az1):
    """Wall cells of one side (corners left out) as (x, z)."""
    if f == "north": return [(x, az0) for x in range(ax0 + 1, ax1)]
    if f == "south": return [(x, az1) for x in range(ax0 + 1, ax1)]
    if f == "west": return [(ax0, z) for z in range(az0 + 1, az1)]
    return [(ax1, z) for z in range(az0 + 1, az1)]


def _house_legacy(b, x0, z0, w, d, floors=1, style="east_blue", rnd=None, kinds=None, theme="pirate", y=0, door="south", flat_roof=False,
                  chimney=None, flowers=True, sign=None):
    """A furnished house built with depth: a stone base course with a stair skirt, a timber frame (corner and
    middle posts, a beam at every floor), a jettied upper floor on stair brackets, framed windows with sills,
    shutters and flower boxes, a wall lamp and an awning at the door, deep eaves under the roof. Floors are linked
    by a ladder. Returns the roof top y. kinds: room kind per floor (defaults: ground = kitchen/dining/tavern,
    upper = bedroom)."""
    rnd = rnd or random.Random(x0 * 31 + z0)
    wall, post, floor, rst, rfull, win, dw = STYLES[style]
    fh = 4
    top = y + floors * fh
    var = VARIANTS.get(wall, (wall,))
    base, base_st = BASE.get(style, ("minecraft:cobblestone", "minecraft:cobblestone_stairs"))
    jetty = style in JETTY and floors > 1 and w >= 7 and d >= 7
    trap = f"minecraft:{dw}_trapdoor"
    out = SIDES[door]
    rects = []
    for f in range(floors):
        j = 1 if (jetty and f >= 1) else 0
        rects.append((x0 - j, z0 - j, x0 + w - 1 + j, z0 + d - 1 + j))
    # ground floor and stone base course
    b.box(x0, y, z0, x0 + w - 1, y, z0 + d - 1, floor)
    for f, (ax0, az0, ax1, az1) in enumerate(rects):
        fy = y + 1 + f * fh
        for xx in range(ax0, ax1 + 1):
            for zz in range(az0, az1 + 1):
                edge = xx in (ax0, ax1) or zz in (az0, az1)
                for yy in range(fy, fy + fh - 1):
                    if not edge: b.set(xx, yy, zz, AIR); continue
                    if f == 0 and yy == fy: b.set(xx, yy, zz, base); continue
                    h = (yy - y) / max(1, floors * fh)
                    b.set(xx, yy, zz, var[0] if h > 0.6 and len(var) > 1 and rnd.random() < 0.5 else rnd.choice(var))
                # the beam on top of every floor: a ring of sideways logs, the floor above inside it
                yb = fy + fh - 1
                if edge: b.set(xx, yb, zz, _beam(post, "x" if zz in (az0, az1) and xx not in (ax0, ax1) else "z"))
                elif f < floors - 1: b.set(xx, yb, zz, floor)
                else: b.set(xx, yb, zz, AIR)
        # posts: corners and every 3-4 blocks
        for (px, pz) in ((ax0, az0), (ax1, az0), (ax0, az1), (ax1, az1)):
            b.column(px, pz, fy, fy + fh - 2, post)
        for fside in SIDES:
            cells = _side_cells(fside, ax0, az0, ax1, az1)
            n = len(cells)
            if n >= 7:
                for k in range(3, n - 2, 4):
                    px, pz = cells[k]
                    b.column(px, pz, fy + (1 if f == 0 else 0), fy + fh - 2, post)
        # jetty: a moulding of upside-down stairs carries the overhanging floor, with brackets below at the posts
        if jetty and f >= 1:
            st_ = f"{rst}_stairs" if rst else "minecraft:spruce_stairs"
            for fside, (ox, oz) in SIDES.items():
                for k, (px, pz) in enumerate(_side_cells(fside, ax0, az0, ax1, az1)):
                    b.set(px, fy - 1, pz, stairs(st_, OPP[fside], "top"))
                    if k % 3 == 1 and _empty(b, px, fy - 2, pz): b.set(px, fy - 2, pz, stairs(st_, OPP[fside], "top"))
            for (px, pz) in ((ax0, az0), (ax1, az0), (ax0, az1), (ax1, az1)): b.set(px, fy - 1, pz, post)
    # windows: two tall panes, sill below, shutters each side, a head above; flower boxes upstairs
    for f, (ax0, az0, ax1, az1) in enumerate(rects):
        fy = y + 1 + f * fh
        for fside, (ox, oz) in SIDES.items():
            cells = _side_cells(fside, ax0, az0, ax1, az1)
            posts = {cells[k] for k in range(3, len(cells) - 2, 4)} if len(cells) >= 7 else set()
            dx = x0 + w // 2 if fside in ("north", "south") else None
            dzc = z0 + d // 2 if fside in ("east", "west") else None
            for k, (wx, wz) in enumerate(cells):
                if (wx, wz) in posts or k in (0, len(cells) - 1): continue
                along = wx if fside in ("north", "south") else wz
                if (k - 1) % 4 != 1: continue
                if f == 0 and fside == door and abs(along - (dx if dx is not None else dzc)) <= 1: continue
                for yy in (fy + 1, fy + 2) if fh >= 4 else (fy + 1,):
                    b.set(wx, yy, wz, win)
                sx, sz = wx + ox, wz + oz
                if f == 0 or not flowers:
                    if _empty(b, sx, fy, sz): b.set(sx, fy, sz, stairs(f"{rst}_stairs" if rst else "minecraft:smooth_sandstone_stairs", OPP[fside], "top"))
                elif _empty(b, sx, fy, sz):
                    b.set(sx, fy, sz, f"onepiece:flower_box[facing={fside}]")
                ax, az = (1, 0) if fside in ("north", "south") else (0, 1)
                for s in (-1, 1):
                    tx, tz = sx + ax * s, sz + az * s
                    for yy in (fy + 1, fy + 2):
                        if _empty(b, tx, yy, tz): b.set(tx, yy, tz, trapdoor(trap, fside, "bottom", "true"))
    # stair skirt along the base, outside, where the ground is free
    ax0, az0, ax1, az1 = rects[0]
    for fside, (ox, oz) in SIDES.items():
        for (wx, wz) in _side_cells(fside, ax0, az0, ax1, az1):
            sx, sz = wx + ox, wz + oz
            if _empty(b, sx, y + 1, sz) and not _empty(b, sx, y, sz) and not (fside == door and abs((wx if fside in ("north", "south") else wz) - (x0 + w // 2 if fside in ("north", "south") else z0 + d // 2)) <= 1):
                b.set(sx, y + 1, sz, slab(base_st.replace("_stairs", "_slab").replace("smooth_sandstone_slab", "smooth_sandstone_slab"), "bottom"))
    # ladder between floors in a back corner (inside the ground-floor walls, so every floor reaches it)
    lf = "south" if door == "south" else "north" if door == "north" else "east" if door == "east" else "west"
    if floors > 1:
        if door in ("south", "north"):
            lx, lz = x0 + 1, (z0 + 1 if door == "south" else z0 + d - 2)
            lad = f"minecraft:ladder[facing={'south' if door == 'south' else 'north'},waterlogged=false]"
        else:
            lx, lz = (x0 + 1 if door == "east" else x0 + w - 2), z0 + 1
            lad = f"minecraft:ladder[facing={'east' if door == 'east' else 'west'},waterlogged=false]"
        for k in range(1, (floors - 1) * fh + 1): b.set(lx, y + k, lz, lad)
    # door with a frame, an awning and a wall lamp
    if door in ("south", "north"):
        mx = x0 + w // 2; dz = z0 + d - 1 if door == "south" else z0
        dpos = [(mx, dz)]; step = (mx, dz + out[1]); lamp = (mx + 1, dz); awn = [(mx + k, dz + out[1]) for k in (-1, 0, 1)]
    else:
        mz = z0 + d // 2; dx_ = x0 + w - 1 if door == "east" else x0
        dpos = [(dx_, mz)]; step = (dx_ + out[0], mz); lamp = (dx_, mz + 1); awn = [(dx_ + out[0], mz + k) for k in (-1, 0, 1)]
    for (px, pz) in dpos:
        b.set(px, y + 1, pz, f"minecraft:{dw}_door[facing={door},half=lower,hinge=left,open=false,powered=false]")
        b.set(px, y + 2, pz, f"minecraft:{dw}_door[facing={door},half=upper,hinge=left,open=false,powered=false]")
        b.set(px, y + 3, pz, _beam(post, "x" if door in ("south", "north") else "z"))
    if b.get(step[0], y, step[1]) in (None, AIR): b.set(step[0], y, step[1], f"minecraft:{dw}_slab[type=top,waterlogged=false]" if y > 0 else floor)
    b.set(step[0], y + 1, step[1], AIR) if (b.get(step[0], y + 1, step[1]) or "").endswith("_slab[type=bottom,waterlogged=false]") else None
    for (ax, az) in awn:
        if _empty(b, ax, y + 4, az): b.set(ax, y + 4, az, slab(f"{rst}_slab" if rst else "minecraft:smooth_sandstone_slab", "top") if rst != "minecraft:deepslate_tile" else slab("minecraft:deepslate_tile_slab", "top"))
    lx_, lz_ = lamp
    b.set(lx_ + out[0], y + 3, lz_ + out[1], f"onepiece:wall_lamp[facing={door}]")
    kinds = kinds or ([rnd.choice(("kitchen", "dining", "tavern", "workshop"))] + ["bedroom"] * (floors - 1) if floors > 1 else [rnd.choice(("bedroom", "kitchen"))])
    for f in range(floors):
        fy = y + 1 + f * fh
        I.furnish(b, x0 + 1, fy, z0 + 1, x0 + w - 2, z0 + d - 2, fh - 1, kinds[f % len(kinds)], theme, seed=rnd.randint(0, 99999))
    if floors > 1:  # keep the ladder clear of furniture
        for k in range(1, (floors - 1) * fh + 1): b.set(lx, y + k, lz, lad)
        for k in range(1, 3): b.set(lx, y + (floors - 1) * fh + k, lz, AIR)
    # roof over the top floor, with eave brackets under the overhang
    rx0, rz0, rx1, rz1 = rects[-1]
    if flat_roof or rst is None:
        b.box(rx0, top, rz0, rx1, top, rz1, rfull)
        for xx in range(rx0, rx1 + 1):
            for zz in (rz0, rz1): b.set(xx, top + 1, zz, f"{wall.split('[')[0]}" if style != "sand" else "minecraft:smooth_sandstone_slab[type=bottom,waterlogged=false]")
        for zz in range(rz0, rz1 + 1):
            for xx in (rx0, rx1): b.set(xx, top + 1, zz, f"{wall.split('[')[0]}" if style != "sand" else "minecraft:smooth_sandstone_slab[type=bottom,waterlogged=false]")
        if style == "sand":  # a cornice of stairs under the parapet
            for fside, (ox, oz) in SIDES.items():
                for (wx, wz) in _side_cells(fside, rx0, rz0, rx1, rz1):
                    if _empty(b, wx + ox, top, wz + oz): b.set(wx + ox, top, wz + oz, stairs("minecraft:smooth_sandstone_stairs", OPP[fside], "top"))
        rtop = top + 1
    elif (rx1 - rx0) >= (rz1 - rz0):
        b.gable_roof(rx0, rz0, rx1, rz1, top, f"{rst}_stairs", rfull, gable_wall=wall)
        for xx in range(rx0 - 1, rx1 + 2, 2):  # brackets under the eaves
            for zz, f in ((rz0 - 1, "south"), (rz1 + 1, "north")):
                if _empty(b, xx, top - 1, zz): b.set(xx, top - 1, zz, stairs(f"{rst}_stairs", f, "top"))
        for zz in range(rz0, rz1 + 1):  # a trim beam across the gable ends
            for xx in (rx0, rx1): b.set(xx, top, zz, _beam(post, "z"))
        rtop = top + (rz1 - rz0 + 3) // 2
    else:
        b.hip_roof(rx0, rz0, rx1, rz1, top, f"{rst}_stairs", rfull)
        for zz in range(rz0 - 1, rz1 + 2, 2):
            for xx, f in ((rx0 - 1, "east"), (rx1 + 1, "west")):
                if _empty(b, xx, top - 1, zz): b.set(xx, top - 1, zz, stairs(f"{rst}_stairs", f, "top"))
        rtop = top + (min(rx1 - rx0, rz1 - rz0) + 3) // 2
    if chimney or (chimney is None and rnd.random() < 0.5):  # a chimney up the back wall, capped with a smoking campfire
        back = OPP[door]; bo = SIDES[back]
        if back in ("north", "south"):
            cx, cz = x0 + 1, (rects[-1][1] if back == "north" else rects[-1][3]) + bo[1]
        else:
            cx, cz = (rects[-1][0] if back == "west" else rects[-1][2]) + bo[0], z0 + 1
        for yy in range(y + 1, rtop + 2): b.set(cx, yy, cz, "minecraft:bricks" if yy > y + 1 else base)
        b.set(cx, rtop + 2, cz, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    if sign:  # a shop sign on a bracket by the door
        if door in ("south", "north"):
            sx, sz = x0 + w // 2 - 2, (z0 + d - 1 if door == "south" else z0) + out[1]
        else:
            sx, sz = (x0 + w - 1 if door == "east" else x0) + out[0], z0 + d // 2 - 2
        b.set(sx, y + 3, sz, fence(dw)); b.set(sx, y + 2, sz, sign)
    return rtop


# ------------------------------------------------------------------ houses (guide 10, 12, 13)
# styles archkit has no palette for: the plank shack and the white-and-blue Marine house
A.PAL.setdefault("shack", dict(rec="timber", frame="minecraft:spruce_log", infill=("minecraft:spruce_planks", "minecraft:stripped_spruce_wood[axis=y]",
                 "minecraft:spruce_planks", "minecraft:oak_planks"), st="minecraft:spruce_stairs", full="minecraft:spruce_planks",
                 ridge="minecraft:dark_oak_slab", alt="minecraft:oak_stairs", floor="minecraft:spruce_planks", wood="spruce",
                 base="minecraft:cobblestone", roofs=("saltbox", "gable", "half_hip")))
A.PAL.setdefault("marine", dict(rec="stone", frame="minecraft:polished_andesite", infill=("minecraft:white_terracotta", "minecraft:calcite",
                 "minecraft:white_concrete", "minecraft:white_terracotta"), st="minecraft:prismarine_brick_stairs", full="minecraft:prismarine_bricks",
                 ridge="minecraft:dark_prismarine_slab", alt="minecraft:dark_prismarine_stairs", floor="minecraft:birch_planks", wood="birch",
                 base="minecraft:polished_andesite", roofs=("hip", "half_hip", "hip_low")))
# a second roof kind per style, so a street of one style still mixes roofs
EXTRA_ROOFS = {"east_blue": ("hip",), "cottage": ("gambrel",), "brick": ("hip",), "plaster": ("gable",), "orange": ("half_hip",),
               "snow": ("half_hip",), "stone": ("gable",), "shack": (), "marine": ("gable",)}
# roof materials (stairs, full block, ridge, a second stairs mixed in low down). The mix-in sits close in value to the
# main block (guide 3: a gradient, not patches; a dark stair in a red roof reads as burn marks)
ROOF_MATS = {
    "spruce": ("minecraft:spruce_stairs", "minecraft:spruce_planks", "minecraft:dark_oak_slab", "minecraft:dark_oak_stairs"),
    "dark_oak": ("minecraft:dark_oak_stairs", "minecraft:dark_oak_planks", "minecraft:spruce_slab", "minecraft:dark_oak_stairs"),
    "oak": ("minecraft:oak_stairs", "minecraft:oak_planks", "minecraft:spruce_slab", "minecraft:oak_stairs"),
    "red": ("minecraft:brick_stairs", "minecraft:bricks", "minecraft:red_nether_brick_slab", "minecraft:granite_stairs"),
    "maroon": ("minecraft:red_nether_brick_stairs", "minecraft:red_nether_bricks", "minecraft:nether_brick_slab", "minecraft:red_nether_brick_stairs"),
    "orange": ("minecraft:acacia_stairs", "minecraft:acacia_planks", "minecraft:dark_oak_slab", "minecraft:waxed_cut_copper_stairs"),
    "slate": ("minecraft:deepslate_tile_stairs", "minecraft:deepslate_tiles", "minecraft:polished_blackstone_slab", "minecraft:cobbled_deepslate_stairs"),
    "blue": ("minecraft:prismarine_brick_stairs", "minecraft:prismarine_bricks", "minecraft:dark_prismarine_slab", "minecraft:prismarine_brick_stairs"),
}
# per style: the old house's roof first (each island keeps its look), then the accents a town may mix in
STYLE_ROOFS = {"east_blue": ("spruce", "dark_oak", "red"), "cottage": ("dark_oak", "spruce"), "orange": ("spruce", "dark_oak"),
               "plaster": ("maroon", "red"), "brick": ("dark_oak", "spruce", "slate"), "stone": ("slate", "dark_oak"),
               "snow": ("spruce", "dark_oak"), "shack": ("spruce", "oak", "dark_oak"), "marine": ("blue",)}
ACCENT = 0.3  # share of a town's houses (per style) roofed in its one accent material
PLANS = (("L", 4), ("T", 3), ("offset", 3), ("plain", 1))
YARD = {"timber": ("woodpile", "crates", "bench", "pots", "crates"), "stone": ("crates", "bench", "pots"), "sand": ("pots", "crates", "pots"),
        "snow": ("woodpile", "crates", "woodpile"), "shack": ("crates", "woodpile", "crates", "trough")}


def _open(b, cells, y0, y1):
    """True when nothing is built in these columns between y0 and y1 (air, plants and snow layers only)."""
    return all(L._free(b, x, yy, z) for (x, z) in cells for yy in range(y0, y1 + 1))


def _strip(x0, z0, x1, z1, side, depth, lo=0):
    """Cells of a strip `depth` deep outside one side of a box (starting `lo` + 1 out)."""
    if side == "south": return [(x, z) for x in range(x0, x1 + 1) for z in range(z1 + 1 + lo, z1 + 1 + depth)]
    if side == "north": return [(x, z) for x in range(x0, x1 + 1) for z in range(z0 - depth, z0 - lo)]
    if side == "east": return [(x, z) for x in range(x1 + 1 + lo, x1 + 1 + depth) for z in range(z0, z1 + 1)]
    return [(x, z) for x in range(x0 - depth, x0 - lo) for z in range(z0, z1 + 1)]


def _overlap(a, c):
    return a[0] <= c[2] and a[2] >= c[0] and a[1] <= c[3] and a[3] >= c[1]


def _grow(cells):
    """Bounding box of a list of cells."""
    xs = [c[0] for c in cells]; zs = [c[1] for c in cells]
    return (min(xs), min(zs), max(xs), max(zs))


def _rise(kind, span):
    """Rough roof height over the eaves for a roof kind and span (to keep neighbouring ridges apart)."""
    n = (span + 1) // 2
    return {"gambrel": n + round(n * 0.45), "mansard": (n + 3 * round(n * 0.5) + 1) // 2, "hip_low": n // 2 + 1}.get(kind, n)


def _neighbours(b, cx, cz, r=14):
    return [h for h in getattr(b, "_tk_houses", ()) if abs(h["c"][0] - cx) + abs(h["c"][1] - cz) <= r]


def _roof_style(b, r, style, mat=None):
    """The style with a roof material: one main (the old look) and one accent per town and style, the accent on about
    3 houses in 10 (guide 3: one palette per build, not a colour per house). Registered in archkit.PAL as "style/mat"
    so house2 builds roof, dormers, bays and jetty brackets from it."""
    mats = STYLE_ROOFS.get(style, ())
    if not mats: return style, None
    if mat is None:
        if not hasattr(b, "_tk_mats"): b._tk_mats = {}
        if style not in b._tk_mats:  # seeded from the first house of the style: the same town always gets the same pair
            b._tk_mats[style] = (mats[0], random.Random(r.randint(0, 1 << 30)).choice(mats[1:]) if len(mats) > 1 else mats[0])
        main, acc = b._tk_mats[style]
        mat = acc if r.random() < ACCENT else main
    key = f"{style}/{mat}"
    if key not in A.PAL:
        st, full, ridge, alt = ROOF_MATS[mat]
        # snow: a full-block ridge (a snow layer can lie on it; snow blocks there read as a white stripe)
        A.PAL[key] = dict(A.PAL[style], st=st, full=full, alt=alt, ridge=full if style == "snow" else ridge)
    return key, mat


def _plans_ok(W, D):
    """The plan kinds a plot of W (along the front) x D allows (see _town_rects)."""
    return [k for k, wt in PLANS if k == "plain" or (W >= 7 and D >= 7 and (k != "T" or W >= 9) and (k != "offset" or W >= 9 and D >= 8))]


def _town_rects(kind, x0, z0, w, d, door, floors, r):
    """Compound plans for town plots (guide 10), main block first. archkit.plan_rects gives the main block 60 % of
    the depth, which on 7-10 deep town plots leaves 3-wide rooms with no space for beds; here the main block keeps the
    plot's width and all but k = 2-3 rows of its depth, and a gabled wing (deeper than wide, so its ridge runs to the
    street: a cross gable) or a second offset block steps forward into those rows. Upper wings sit a floor lower on 7
    in 10 houses. Returns [(x0, z0, x1, z1, floors_delta), ...] in world coordinates."""
    W, D = (d, w) if door in ("east", "west") else (w, d)
    k = 2 if D <= 9 else 3
    low = -1 if floors >= 2 and r.random() < 0.7 else 0
    ww = 5 if W < 12 else 7
    if kind == "L":
        wx = 0 if r.random() < 0.5 else W - ww
        rs = [(0, 0, W - 1, D - 1 - k, 0), (wx, max(1, min(D - k - 2, D - ww - 1)), wx + ww - 1, D - 1, low)]
    elif kind == "T":
        wx = (W - ww) // 2
        rs = [(0, 0, W - 1, D - 1 - k, 0), (wx, max(1, min(D - k - 2, D - ww - 1)), wx + ww - 1, D - 1, low)]
    elif kind == "offset":
        s_ = 2 if W < 12 else 3; w2 = max(5, min(W - 2, W // 2 + 1 + (W // 2) % 2))
        main = (0, 0, W - 1 - s_, D - 1 - k, 0); sec = (W - w2, k, W - 1, D - 1, low)
        if r.random() < 0.5: main, sec = (s_, 0, W - 1, D - 1 - k, 0), (0, k, w2 - 1, D - 1, low)
        rs = [main, sec]
    else:
        rs = [(0, 0, W - 1, D - 1, 0)]
    out = []
    for (a, c, e, g, dl) in rs:
        if door == "south": q = (x0 + a, z0 + c, x0 + e, z0 + g)
        elif door == "north": q = (x0 + a, z0 + D - 1 - g, x0 + e, z0 + D - 1 - c)
        elif door == "east": q = (x0 + c, z0 + a, x0 + g, z0 + e)
        else: q = (x0 + D - 1 - g, z0 + a, x0 + D - 1 - c, z0 + e)
        out.append(q + (dl,))
    return out


def _pick_plan(r, W, D, near):
    """L / T / offset / plain (guide 10 weights) as the plot allows, not the same as the nearest neighbour's."""
    ok = [(k, wt) for k, wt in PLANS if k in _plans_ok(W, D)]
    last = near[-1]["plan"] if near else None
    if len(ok) > 1 and last: ok = [(k, wt) for k, wt in ok if k != last] or ok
    return A._wpick(r, ok)


def _pick_roof(r, style, y, floors, w, d, near, dormer=False):
    """A roof kind for the style whose ridge differs from the neighbours' by 2 or more where it can (guide 10).
    dormer=True: only kinds that take dormers, when the walls can't have a bay or balcony (2 add-ons still)."""
    kinds = list(A.PAL[style]["roofs"]) + list(EXTRA_ROOFS.get(style, ()))
    if dormer and min(w, d) >= 7: kinds = [k for k in kinds if k in ("gable", "half_hip", "hip")] or kinds
    if min(w, d) < 9: kinds = [k for k in kinds if k not in ("gambrel", "mansard")] or ["gable"]  # a barn roof on a cottage dwarfs the street
    r.shuffle(kinds)
    span = min(w, d) + 2
    tops = [h["top"] for h in near]
    def score(k):
        t = y + floors * FH + _rise(k, span)
        gap = min((abs(t - u) for u in tops), default=9)
        same = sum(1 for h in near[-2:] if h["roof"] == k)
        return (min(gap, 3) - 2 * same, r.random())
    return max(kinds, key=score)


def _rects_of(cells, least=4):
    """Cover a set of floor cells with rooms: the largest rectangle first, then the largest in what is left."""
    cells, out = set(cells), []
    while cells:
        xs = sorted({c[0] for c in cells}); zs = sorted({c[1] for c in cells})
        best, ba = None, 0
        for xa in xs:
            for za in zs:
                if (xa, za) not in cells: continue
                zmax = None
                for xb in range(xa, xs[-1] + 1):
                    if (xb, za) not in cells: break
                    zb = za
                    while (xb, zb + 1) in cells and (zmax is None or zb + 1 <= zmax): zb += 1
                    zmax = zb if zmax is None else min(zmax, zb)
                    a = (xb - xa + 1) * (zmax - za + 1)
                    if a > ba: best, ba = (xa, za, xb, zmax), a
        if not best or ba < least: break
        out.append(best)
        cells -= {(x, z) for x in range(best[0], best[2] + 1) for z in range(best[1], best[3] + 1)}
    return out


def _air_rooms(b, info):
    """The real rooms of every storey: the open floor reached from inside (flood fill over air 2 high within the
    footprint, 1 wider upstairs for jetties; walls and doors stop it): (rectangles cut from it, the cell sets). A recessed wall or an L wing no longer shrinks a room to a cupboard, which
    archkit's inset rects did on small plots (no space left for beds)."""
    lad = {(l[0], l[1]) for l in info["ladder"]}
    F = {(x, z) for r_ in info["rects"] for x in range(r_[0], r_[2] + 1) for z in range(r_[1], r_[3] + 1)}
    F1 = F | {(x + dx, z + dz) for (x, z) in F for dx in (-1, 0, 1) for dz in (-1, 0, 1)}  # upper storeys may be jettied
    def air(x, y, z): return (x, z) in lad or b.get(x, y, z) in (None, AIR)
    out = []
    for f, fy in enumerate(info["floors"]):
        inside = F if f == 0 else F1
        seeds = [((r_[0] + r_[2]) // 2, (r_[1] + r_[3]) // 2) for r_ in info["rooms"][f]] if f < len(info["rooms"]) else []
        seen, todo = set(), [c for c in seeds if air(c[0], fy, c[1]) and air(c[0], fy + 1, c[1])]
        while todo:
            c = todo.pop()
            if c in seen: continue
            seen.add(c)
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (c[0] + dx, c[1] + dz)
                if n in inside and n not in seen and air(n[0], fy, n[1]) and air(n[0], fy + 1, n[1]) \
                        and A._solid(b.get(n[0], fy - 1, n[1])): todo.append(n)
        if not seen:  # nothing reached (a seed under furniture): fall back on archkit's rooms
            seen = {(x, z) for r_ in (info["rooms"][f] if f < len(info["rooms"]) else []) for x in range(r_[0], r_[2] + 1) for z in range(r_[1], r_[3] + 1)}
        out.append(seen)
    return [_rects_of(m) for m in out], out


_Room = I.Room


class _Plan(_Room):
    """A Room over a storey's whole open floor, however shaped: cells outside it count as wall, and its edge is every
    floor cell beside a wall, so an L or T storey is furnished as one room against its real walls (rectangles cut
    from it leave furniture standing in the middle of the floor, and no room at all for beds)."""
    mask = frozenset()

    def free(self, x, y, z):
        return (x, z) in self.mask and _Room.free(self, x, y, z)

    def edge(self):
        out = []
        for (x, z) in sorted(self.mask):
            for f, (dx, dz) in (("south", (0, -1)), ("north", (0, 1)), ("east", (-1, 0)), ("west", (1, 0))):
                if (x + dx, z + dz) not in self.mask: out.append((x, z, f))
        return out


def _plan_room(mask):
    return type("_P", (_Plan,), {"mask": frozenset(mask)})


def _room(b, mask, fy, theme, r):
    xs = [c[0] for c in mask]; zs = [c[1] for c in mask]
    return _plan_room(mask)(b, min(xs), fy, min(zs), max(xs), max(zs), FH - 1, theme, r)


def _heads(b, mask, fy):
    return [(x, z) for (x, z) in mask if "_bed[" in (b.get(x, fy, z) or "") and "part=head" in b.get(x, fy, z)]


def _cap(kind, mask):
    """Beds a sleeping storey should hold: a double in a bedroom, about one bunk per 10 m2 in barracks."""
    return max(2, (len(mask) + 5) // 10) if kind == "barracks" else 2


def _beds(b, mask, fy, kind, theme, r, want=None):
    """Top a sleeping storey up to its beds (the townsfolk count on them), head to a real wall where the furnishing
    left room: never more than _cap, so a bedroom is not three beds in a row."""
    if kind not in ("barracks", "bedroom") or not mask: return
    want = min(want or _cap(kind, mask), _cap(kind, mask))
    have = len(_heads(b, mask, fy))
    R = _room(b, mask, fy, theme, r)
    for (x, z, f) in R.edge():
        if have >= want: return
        if R.wall_is_solid(x, z, f) and R.bed(x, z, f): have += 1


def _trim_beds(b, mask, fy, kind, keep):
    """Take out the beds the furnishing added past the cap (the latest first; `keep` are the bunks placed before it)."""
    extra = [c for c in _heads(b, mask, fy) if c not in keep]
    n = len(keep) + len(extra) - _cap(kind, mask)
    for (x, z) in sorted(extra, reverse=True)[:max(0, n)]:
        f = b.get(x, fy, z).split("facing=")[1].split(",")[0]
        dx, dz = A.DIRV[f]
        b.blocks[(x, fy, z)] = AIR
        if "_bed[" in (b.get(x - dx, fy, z - dz) or ""): b.blocks[(x - dx, fy, z - dz)] = AIR


JOBS = {"kitchen": ("smoker[facing={f},lit=true]", "furnace[facing={f},lit=true]", "crafting_table"),
        "workshop": ("crafting_table", "smithing_table"), "study": ("lectern[facing={f},has_book=false,powered=false]",),
        "bedroom": ("lectern[facing={f},has_book=false,powered=false]",)}


def _jobs(b, mask, fy, kind, theme, r):
    """The work blocks a storey's kind stands for (villagers take their trade from them): any the furnishing could not
    fit go on the first free wall cell."""
    if not mask: return
    have = {(b.get(x, fy, z) or "").split("[")[0] for (x, z) in mask}
    R = _room(b, mask, fy, theme, r)
    for j in JOBS.get(kind, ()):
        if "minecraft:" + j.split("[")[0] in have: continue
        spot = next(((x, z, f) for (x, z, f) in R.edge() if R.wall_is_solid(x, z, f) and R.ok(x, fy, z)), None)
        if spot: b.set(spot[0], fy, spot[1], "minecraft:" + j.format(f=spot[2]))


DRESS = ("minecraft:barrel[facing=up,open=false]", "onepiece:mikan_crate[axis=y]", "minecraft:decorated_pot", "minecraft:potted_fern",
         "onepiece:sake_barrel[axis=y]", "minecraft:potted_azalea_bush")


def _dress(b, mask, fy, kind, theme, r):
    """A day room the furnishing left bare (an 8x4 dining room with one table) gets things along its walls up to about
    1 cell in 5 taken: barrels, crates, pots and plants (guide 7), never in a doorway (Room keeps those clear)."""
    if kind in ("bedroom", "barracks", "storage", "treasure") or len(mask) < 12: return
    have = sum(1 for (x, z) in mask if b.get(x, fy, z) not in (None, AIR) and "carpet" not in b.get(x, fy, z))
    n = len(mask) // 5 - have
    if n > 0: _room(b, mask, fy, theme, r).scatter(DRESS, n, wall=True)


def _furnish(b, info, kinds, theme, r, defaulted):
    """Furnish every storey as one room of its kind over its real open floor (interiors.furnish on a _Plan room), with
    beds placed first on sleeping storeys and the kind's work blocks topped up after."""
    info["rooms"], masks = _air_rooms(b, info)
    if defaulted and not set(kinds) & {"bedroom", "barracks"} and masks and masks[-1]:  # a defaulted kitchen cottage still sleeps someone
        _beds(b, masks[-1], info["floors"][len(masks) - 1], "bedroom", theme, r)
    for f, mask in enumerate(masks):
        k, fy = kinds[f % len(kinds)], info["floors"][f]
        if len(mask) < 4: continue
        if k == "barracks": _beds(b, mask, fy, k, theme, r)  # bunks first along the walls, the rest round them
        keep = set(_heads(b, mask, fy))
        xs = [c[0] for c in mask]; zs = [c[1] for c in mask]
        I.Room = _plan_room(mask)  # interiors.furnish builds its Room by this name
        try: I.furnish(b, min(xs), fy, min(zs), max(xs), max(zs), FH - 1, k, theme, seed=r.randint(0, 99999))
        finally: I.Room = _Room
        if k in ("barracks", "bedroom"): _trim_beds(b, mask, fy, k, keep)
        _beds(b, mask, fy, k, theme, r)
        _jobs(b, mask, fy, k, theme, r)
        _dress(b, mask, fy, k, theme, r)
    for (lx, lz, ya, yb, lad) in info["ladder"]:  # keep the ladder and the hatch above it clear of furniture
        for yy in range(ya, yb + 1): b.set(lx, yy, lz, lad)
        for k in (1, 2): b.set(lx, yb + k, lz, AIR)
        fl = b.get(lx, ya - 1, lz)
        A.back_ladder(b, (lx, lz, ya, yb, lad), fl if A._solid(fl) and "slab" not in fl and "stairs" not in fl else "minecraft:spruce_planks")


def _desert_ladder(b, info, door):
    """desert_house links its storeys only by the outside stair: add a ladder in the back corner that every storey
    keeps (the top storey steps back from the front and the CW side, never from the back or CCW side)."""
    x0, z0, x1, z1 = info["rects"][0][:4]
    n = len(info["floors"])
    if n < 2: return
    back, side = OPP[door], A.CCW[door]
    lx = {"west": x0 + 1, "east": x1 - 1}.get(side, {"west": x0 + 1, "east": x1 - 1}.get(back))
    lz = {"north": z0 + 1, "south": z1 - 1}.get(back, {"north": z0 + 1, "south": z1 - 1}.get(side))
    lad = f"minecraft:ladder[facing={door},waterlogged=false]"
    y = info["y"]
    info["ladder"] = [(lx, lz, y + 1, y + (n - 1) * FH, lad)]


def _sign(b, info, sign, wood):
    """A shop sign hung from a fence bracket on the wall beside the door (the first wall cell with room in front)."""
    dx, dy, dz, side = info["door"]
    P = A._loc(dx, dz, side)
    for u in (-2, 2, -3, 3, -1, 1):
        wx, wz = P(u, 0); sx, sz = P(u, 1)
        if A._solid(b.get(wx, dy + 2, wz)) and A._soft(b.get(sx, dy + 2, sz)) and A._soft(b.get(sx, dy + 1, sz)):
            b.set(sx, dy + 2, sz, fence(wood)); b.set(sx, dy + 1, sz, sign); return


def _walk(b, info, rnd, reach):
    """A step and a 3x3 apron at the door, then a short walk out to the plot edge (guide 11c), on open ground only."""
    ox_, oy, oz_ = info["outside"]
    side = info["door"][3]; ox, oz = A.DIRV[side]; ax, az = (1, 0) if side in ("north", "south") else (0, 1)
    y = info["y"]
    top = b.get(ox_, y, oz_) or ""
    if "sand" in top: mid, edge = ("minecraft:smooth_sandstone", "minecraft:sandstone"), ("minecraft:sandstone", "minecraft:sand")
    elif "snow" in top: mid, edge = ("minecraft:cobblestone", "minecraft:stone_bricks"), ("minecraft:gravel", "minecraft:snow_block")
    elif "grass" in top or "dirt" in top or "podzol" in top: mid, edge = ("minecraft:dirt_path",), L.EDGE
    else: return
    for k in range(0, max(2, reach) + 1):
        for u in ((-1, 0, 1) if k < 2 else (0,) if rnd.random() < 0.6 else (0, rnd.choice((-1, 1)))):
            x, z = ox_ + ox * k + ax * u, oz_ + oz * k + az * u
            if L.ground_y(b, x, z) != y or L._sh(b.get(x, y, z)) not in ("grass_block", "dirt", "podzol", "sand", "red_sand", "snow_block", "coarse_dirt"): continue
            if not L._free(b, x, y + 1, z): continue
            b.set(x, y, z, rnd.choice(mid) if u == 0 or rnd.random() < 0.5 else rnd.choice(edge))
            q = b.get(x, y + 1, z)
            if q and q != AIR: b.blocks.pop((x, y + 1, z), None)


def yard(b, info, rnd, n=None, kinds=("crates", "woodpile", "bench", "pots")):
    """The lived-in layer round a house (guide 11e): n props (2-3) against the side and back walls, never on the
    door side (streets and paths come in there), each on open ground with a free row in front of it; a bush or a
    one-colour flower clump at two corners. info is the dict house() returns with info=True."""
    F = set()
    for r_ in info["rects"]: F.update((x, z) for x in range(r_[0], r_[2] + 1) for z in range(r_[1], r_[3] + 1))
    door = info["door"][3]; y = info["y"]
    n = rnd.randint(2, 3) if n is None else n
    spots = []
    for (x, z) in F:
        for s, (dx, dz) in A.DIRV.items():
            if s == door or (x + dx, z + dz) in F: continue
            c1, c2 = (x + dx, z + dz), (x + 2 * dx, z + 2 * dz)
            if all(L.ground_y(b, *c) == y and L._free(b, c[0], y + 1, c[1]) and L._free(b, c[0], y + 2, c[1]) for c in (c1, c2)):
                spots.append((c1, s))
    rnd.shuffle(spots)
    used, placed = set(), 0
    for (c, s) in spots:
        if placed >= n: break
        if any(abs(c[0] - u[0]) + abs(c[1] - u[1]) < 5 for u in used): continue
        win = [(x, yy, z) for x in range(c[0] - 7, c[0] + 8) for z in range(c[1] - 7, c[1] + 8) for yy in range(y - 2, y + 6)]
        was = {q: b.blocks.get(q) for q in win}
        if L.clutter(b, c[0], c[1], s, rnd.choice(kinds), rnd) is not False:
            used.add(c); placed += 1
            cells = {q: (was[q], b.blocks.get(q)) for q in win if b.blocks.get(q) != was[q]}  # what the prop changed, so a path can lift it
            if not hasattr(b, "_tk_props"): b._tk_props = []
            b._tk_props.append(cells)
    xs = [c[0] for c in F]; zs = [c[1] for c in F]
    for (cx, cz) in rnd.sample([(min(xs) - 1, min(zs) - 1), (max(xs) + 1, min(zs) - 1), (min(xs) - 1, max(zs) + 1), (max(xs) + 1, max(zs) + 1)], 2):
        if L.ground_y(b, cx, cz) != y: continue
        if rnd.random() < 0.5: L.bush(b, cx, cz, rnd)
        else: L.flower_clump(b, cx, cz, rnd.choice(L.FLOWERS), rnd, n=rnd.randint(3, 4), r=1)
    return placed


def house(b, x0, z0, w, d, floors=1, style="east_blue", rnd=None, kinds=None, theme="pirate", y=0, door="south", flat_roof=False,
          chimney=None, flowers=True, sign=None, plan=None, roof_kind=None, roof_mat=None, addons=None, curve=None, props=True, walk=True,
          info=False, legacy=False):
    """A furnished house in the w x d plot, built with archkit so a street is not a row of boxes: a compound plan
    (L / T / offset / plain, picked so it differs from the nearest neighbour's), a roof kind per style chosen so the
    ridge stands 2+ blocks off the neighbours' (cross gables, hips, gambrels, saltboxes, mansards, a bell or flared
    curve now and then), two or more add-ons (porch, bay, dormers, balcony; a porch or bay only where the ground in
    front of that wall is open, so neighbours are never built into), a chimney, a step and apron at the door with a
    short walk out, and a few props and bushes round the back. Every room is furnished (interiors.furnish: beds,
    kitchens, work blocks), storeys are linked by a ladder, and the door stays where the old house had it (mid `door`
    side, or the panel next to it), so streets laid to it still arrive. "sand" builds an
    Alabasta house (archkit.desert_house). y is the floor level as before (the base goes down to the ground below).
    Returns the roof top y (info=True: archkit's dict). New keywords: plan, roof_kind, addons, curve (archkit),
    roof_mat (a ROOF_MATS key; default: one of the style's STYLE_ROOFS, not the nearest neighbour's),
    props / walk (the yard and the door walk), legacy=True for the old box house (also used for flat_roof on
    styles other than sand)."""
    if legacy or (flat_roof and style != "sand") or (style != "sand" and style not in A.PAL):
        return _house_legacy(b, x0, z0, w, d, floors, style, rnd, kinds, theme, y, door, flat_roof, chimney, flowers, sign)
    # the caller's rnd must come out of here exactly as the old house left it (callers draw the next plot's size and
    # place from it, and buildings must not move): seed our own stream from a copy, then replay the old house on a
    # scratch canvas to advance theirs
    if rnd:
        cp = random.Random(); cp.setstate(rnd.getstate()); r = random.Random(cp.randint(0, 1 << 30))
        _house_legacy(B(), x0, z0, w, d, floors, style, rnd, kinds, theme, y, door, flat_roof, chimney, flowers, sign)
    else: r = random.Random(x0 * 7919 + z0 * 104729)
    defaulted = kinds is None
    kinds = kinds or ([r.choice(("kitchen", "dining", "tavern", "workshop"))] + ["bedroom"] * (floors - 1) if floors > 1 else [r.choice(("bedroom", "kitchen"))])
    x1, z1 = x0 + w - 1, z0 + d - 1
    _clear_props(b, None, 0, {(x, z) for x in range(x0 - 3, x1 + 4) for z in range(z0 - 3, z1 + 4)})  # a neighbour's yard props
    near = _neighbours(b, x0 + w // 2, z0 + d // 2)
    guard = _guard(b, x0, z0, x1, z1, y)
    W, D = (d, w) if door in ("east", "west") else (w, d)
    mid = x0 + w // 2 if door in ("north", "south") else z0 + d // 2  # the old door: callers run their streets to it
    bunk = "barracks" in kinds and min(w, d) < 10  # a small bunkhouse keeps one open room so the bunks fit
    if bunk and not plan: plan = "plain"
    if style == "sand":
        pl = plan or _pick_plan(r, W, D, near)
        res = A.desert_house(b, x0, z0, w, d, floors, rnd=r, y=y, door=door, door_at=mid,
                             plan=_town_rects(pl, x0, z0, w, d, door, floors, r) if pl in dict(PLANS) else pl,
                             outside_stair=_open(b, [c for s in A.DIRV if s != door for c in _strip(x0, z0, x1, z1, s, 1)], y + 1, y + 4),
                             arcade_=False if not _open(b, [c for s in A.DIRV if s != door for c in _strip(x0, z0, x1, z1, s, 3)], y + 1, y + 5) else None)
        _desert_ladder(b, res, door)
        pal = None; wood = "jungle"; yk = YARD["sand"]; mat = None
    else:
        pal = A.PAL[style]; wood = pal["wood"]
        pl = plan or _pick_plan(r, W, D, near)
        pstyle, mat = _roof_style(b, r, style, roof_mat)
        # add-ons stick out only where the ground is open: the porch on the door side, a bay or balcony on the back
        # (the plot's ends usually face the next house in the row, which may not be built yet)
        back = OPP[door]
        houses = getattr(b, "_tk_houses", ())
        front_ok = _open(b, _strip(x0, z0, x1, z1, door, 3), y + 1, y + 5)
        behind = [h for h in houses if _overlap(h["box"], _grow(_strip(x0, z0, x1, z1, back, 4)))]
        back_ok = _open(b, _strip(x0, z0, x1, z1, back, 3), y + 1, y + FH + 3) and not behind
        xsides = [back] if back_ok else []
        if any(_overlap(h["box"], _grow(_strip(x0, z0, x1, z1, back, 2))) for h in behind):
            # a row running through the door axis: the next house will stand as close in front, but the ends are free
            front_ok = False
            xsides = [s_ for s_ in (A.CW[door], A.CCW[door]) if _open(b, _strip(x0, z0, x1, z1, s_, 3), y + 1, y + FH + 3) and
                      not any(_overlap(h["box"], _grow(_strip(x0, z0, x1, z1, s_, 4))) for h in houses)]
        # a neighbour within 2: no jetty and no add-on toward it (a terrace row: the walls stand on the plot lines)
        close = [s_ for s_ in A.DIRV if any(_overlap(h["box"], _grow(_strip(x0, z0, x1, z1, s_, 2))) for h in houses)]
        xsides = [s_ for s_ in xsides if s_ not in close]
        rk = roof_kind or _pick_roof(r, style, y, floors, w, d, near, dormer=not back_ok)
        seed = r.randint(0, 1 << 30)
        shaped = isinstance(pl, str) and pl in dict(PLANS)
        def dormers(p_):  # dormers only on 2+ storeys under a main roof 9+ long and 6+ deep (on less they bury the walls)
            m = _town_rects(p_, x0, z0, w, d, door, floors, random.Random(seed))[0] if isinstance(p_, str) and p_ in dict(PLANS) else pl[0]
            jet = pal["rec"] == "timber" and floors > 1
            return floors >= 2 and rk in ("gable", "half_hip", "hip") and min(m[2] - m[0], m[3] - m[1]) + (1 if jet else 0) >= 6 \
                and max(m[2] - m[0], m[3] - m[1]) + 1 >= 9
        if plan is None and addons is None and front_ok + bool(xsides) + dormers(pl) < 2:
            pl = next((p_ for p_ in _plans_ok(W, D) if p_ not in (pl, "plain") and dormers(p_)), pl)  # a shaped plan with 2 add-ons
        if addons is None:
            walls = (["bay", "balcony"] if floors >= 2 else ["bay"]) if len(xsides) >= 2 else \
                    [r.choice(("bay", "balcony")) if floors >= 2 else "bay"] if xsides else []
            want = walls + (["dormer"] if dormers(pl) else [])
            r.shuffle(want)
            # a porch only on a plain front (a wing already steps forward on the door side) deep enough to give it 2 rows
            if front_ok and pl == "plain" and D >= 9 and (len(want) < 2 or r.random() < 0.5): want.insert(r.randint(0, len(want)), "porch")
            # small plots: the wing plus one add-on (more and the walls vanish under roofs, guide 10)
            want = want[:1 if w * d < 100 and pl != "plain" else 2 if w * d < 170 else 3]
        else: want = list(addons)
        rects = _town_rects(pl, x0, z0, w, d, door, floors, random.Random(seed)) if shaped else pl
        if shaped:  # porches, bays and balconies stay inside the plot (a neighbour built later may stand right beside it)
            outs = ([(door, 2, "porch")] if "porch" in want else []) + [(s_, 1, a_) for s_, a_ in zip(xsides, [a_ for a_ in want if a_ in ("bay", "balcony")])]
            for (s_, k, a_) in outs:
                shr = _inset(rects, (x0, z0, x1, z1), s_, k)
                if shr: rects = shr
                else: want.remove(a_)
            xsides = [s_ for (s_, k, a_) in outs if a_ in want and a_ != "porch"]
        cv = curve if curve is not None else (r.choice(("bell", "flare")) if min(w, d) >= 9 and r.random() < 0.3 else None)
        res = A.house2(b, x0, z0, w, d, floors, pstyle, rnd=random.Random(seed), y=y, door=door, roof_kind=rk, plan=rects, addons=want, curve=cv,
                       chimney_=chimney if chimney is not None else r.random() < 0.65, min_d=7, addon_sides=xsides,
                       dormer_min=6, recess=False if min(w, d) < 11 else None, door_at=mid,
                       jetty_sides=[s_ for s_ in A.DIRV if s_ not in close and s_ not in xsides])
        if not flowers:
            for q in [q for q, v in b.blocks.items() if "flower_box" in v and x0 - 2 <= q[0] <= x1 + 2 and z0 - 2 <= q[2] <= z1 + 2]: b.blocks[q] = AIR
        yk = YARD["snow" if style == "snow" else "shack" if style == "shack" else pal["rec"]]
    ox_, oy_, oz_ = res["outside"]; sd = res["door"][3]
    apron = {(ox_ + A.DIRV[sd][0] * k + (u if sd in ("north", "south") else 0), oz_ + A.DIRV[sd][1] * k + (u if sd in ("east", "west") else 0))
             for k in (0, 1) for u in (-1, 0, 1)}
    for q, v in guard.items():  # an eave or gable pushed into an older neighbour's roof or wall: the neighbour stays
        if b.blocks.get(q) != v and not ((q[0], q[2]) in apron and q[1] <= y + 3): b.blocks[q] = v
    if isinstance(pl, str): res["plan"] = pl
    _tidy(b, x0 - 3, z0 - 3, x1 + 3, z1 + 3, y + 3, res["top"] + 3)
    _furnish(b, res, kinds, theme, r, defaulted)
    if style == "snow": snow_roofs(b, res)
    if sign: _sign(b, res, sign, wood)
    if walk:
        dx, dy, dz, side = res["door"]
        reach = {"south": z1 - dz, "north": dz - z0, "east": x1 - dx, "west": dx - x0}[side]
        _walk(b, res, r, reach + 1)
    if props: yard(b, res, r, kinds=yk)
    if not hasattr(b, "_tk_houses"): b._tk_houses = []
    b._tk_houses.append({"c": (x0 + w // 2, z0 + d // 2), "box": (x0, z0, x1, z1), "top": res["top"], "plan": pl if isinstance(pl, str) else "custom", "roof": res.get("roof"),
                         "addons": res.get("addons"), "style": style, "floors": floors, "mat": mat})
    return res if info else res["top"]


def _inset(rects, plot, side, k):
    """Pull the rects lying on one edge of the plot in by k (room for an add-on inside the plot), or None when a block
    would get too small (a main block under 7 or a wing under 5 across)."""
    x0, z0, x1, z1 = plot
    out = []
    for i, r_ in enumerate(rects):
        q = list(r_)
        if side == "south" and q[3] == z1: q[3] -= k
        elif side == "north" and q[1] == z0: q[1] += k
        elif side == "east" and q[2] == x1: q[2] -= k
        elif side == "west" and q[0] == x0: q[0] += k
        if min(q[2] - q[0], q[3] - q[1]) + 1 < (7 if i == 0 else 5): return None
        out.append(tuple(q))
    return out


def _guard(b, x0, z0, x1, z1, y):
    """What the older neighbours have built outside this plot within reach of its eaves (their box + 2), above the
    ground: house() puts it back after building, so a later house never cuts into an older one's roof."""
    out = {}
    for h in getattr(b, "_tk_houses", ()):
        hx0, hz0, hx1, hz1 = h["box"]
        if hx0 - 3 > x1 + 3 or hx1 + 3 < x0 - 3 or hz0 - 3 > z1 + 3 or hz1 + 3 < z0 - 3: continue
        for x in range(max(hx0 - 2, x0 - 3), min(hx1 + 2, x1 + 3) + 1):
            for z in range(max(hz0 - 2, z0 - 3), min(hz1 + 2, z1 + 3) + 1):
                if x0 <= x <= x1 and z0 <= z <= z1: continue
                for yy in range(y + 1, h["top"] + 4):
                    v = b.blocks.get((x, yy, z))
                    if v and v != AIR and not L._free(b, x, yy, z): out[(x, yy, z)] = v
    return out


def snow_roofs(b, info, margin=3, layers=2):
    """Snow on every roof surface of a house (main block, wings, porch, bay, dormers), from house(info=True): the top
    stair, slab or plank of each column within the house's rects plus `margin` gets a snow layer."""
    xs = [c for r_ in info["rects"] for c in (r_[0], r_[2])]; zs = [c for r_ in info["rects"] for c in (r_[1], r_[3])]
    for x in range(min(xs) - margin, max(xs) + margin + 1):
        for z in range(min(zs) - margin, max(zs) + margin + 1):
            for yy in range(info["top"] + 3, info["y"], -1):
                v = b.blocks.get((x, yy, z))
                if not v or v == AIR: continue
                if ("stairs" in v or "planks" in v or "slab" in v or "tiles" in v) and (x, yy + 1, z) not in b.blocks: b.set(x, yy + 1, z, f"minecraft:snow[layers={layers}]")
                break


def _tidy(b, x0, z0, x1, z1, y0, y1):
    """Drop roof stairs and slabs that touch nothing face-on (a dormer eave past a lower wing roof): they hang in the
    air on their own, which reads as a floating bit (guide 13)."""
    air = lambda q: b.blocks.get(q, AIR) == AIR
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            for yy in range(y0, y1 + 1):
                v = b.blocks.get((x, yy, z), AIR)
                if ("_stairs" in v or "_slab" in v) and all(air(q) for q in ((x + 1, yy, z), (x - 1, yy, z), (x, yy, z + 1), (x, yy, z - 1), (x, yy + 1, z), (x, yy - 1, z))):
                    b.blocks[(x, yy, z)] = AIR


def plot(b, x0, z0, w, d, rnd, y=None, wall_block="minecraft:cobblestone", margin=2, **kw):
    """Opt-in for sloped sites (guide 11b): level a terrace a `margin` wider than the plot at y (default: the 30th
    percentile of the ground under it), with a kinked retaining wall and a stair down on the door side, then build
    house() on it. Takes house()'s keywords; returns what house() returns."""
    cells = [(x, z) for x in range(x0 - margin, x0 + w + margin) for z in range(z0 - margin, z0 + d + margin)]
    if y is None:
        hs = sorted(L.ground_y(b, x, z) for (x, z) in cells); y = hs[int(len(hs) * 0.3)]
    L.terrace(b, x0 - margin, z0 - margin, x0 + w - 1 + margin, z0 + d - 1 + margin, y, wall_block, rnd, stair=kw.get("door", "south"))
    return house(b, x0, z0, w, d, rnd=rnd, y=y, **kw)


def _gy(b, x, z, y):
    """The y to build on: the caller's y when given (not 0), else the ground there when it is above 0 (a relief, a
    terrace, a hill), else 0 as before."""
    if y: return y
    g = L.ground_y(b, x, z)
    return g if g > 0 and L._sh(b.get(x, g, z)) in L.SURFACE else 0


def well(b, x, z, y=0):
    """The town well (guide 11e): a round stone-brick shaft with a mossy foot and a slab rim, water inside, two log
    posts carrying a beam with a little gable roof, a bucket rope (chain) and lantern hung from the beam, and a broken
    ring of paving round it. Stands on the ground at (x, z) unless y is given."""
    y = _gy(b, x, z, y)
    rr = random.Random(x * 3301 + z * 7)
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            d = math.hypot(dx, dz)
            if d > 2.3: continue
            inner = d < 1.2
            for yy in range(y - 4, y + 2):
                if inner: b.set(x + dx, yy, z + dz, WATER if yy >= y - 3 else "minecraft:stone")
                else: b.set(x + dx, yy, z + dz, "minecraft:mossy_stone_bricks" if yy <= y and rr.random() < 0.5 else
                            rr.choice(("minecraft:stone_bricks", "minecraft:stone_bricks", "minecraft:cracked_stone_bricks", "minecraft:mossy_stone_bricks")))
            if not inner: b.set(x + dx, y + 2, z + dz, slab("minecraft:stone_brick_slab"))
    for dx in (-2, 2):  # posts on the rim, a beam across, a small gable roof over it
        for yy in range(y + 2, y + 5): b.set(x + dx, yy, z, "minecraft:spruce_log[axis=y]")
    for dx in range(-2, 3):
        b.set(x + dx, y + 5, z, "minecraft:stripped_spruce_log[axis=x]")
        b.set(x + dx, y + 5, z - 1, stairs("minecraft:spruce_stairs", "south")); b.set(x + dx, y + 5, z + 1, stairs("minecraft:spruce_stairs", "north"))
        b.set(x + dx, y + 6, z, slab("minecraft:dark_oak_slab"))
    for dx in (-3, 3): b.set(x + dx, y + 5, z, stairs("minecraft:spruce_stairs", "east" if dx < 0 else "west", "top"))
    b.set(x, y + 4, z, "minecraft:iron_chain[axis=y,waterlogged=false]"); b.set(x, y + 3, z, lantern(True))
    ring = [(x + dx, z + dz) for dx in range(-4, 5) for dz in range(-4, 5) if 2.3 < math.hypot(dx, dz) <= 3.3 + rr.random() * 0.8]
    L.pave(b, ring, rr, street=True, grass=0.3)


def stall(b, x, z, color, goods, y=0, facing="south"):
    """A market stall (same footprint as before: posts at x..x+3, z..z+2, the roof from x-1..x+4, z-1..z+3): fence
    posts, a striped awning (one colour and white, by column) that slopes down to the front with a fringe, a counter of
    top slabs with a trapdoor apron and the goods on it, a barrel and crates behind. On the ground unless y is given."""
    y = _gy(b, x, z, y)
    rr = random.Random(x * 811 + z * 13)
    for (dx, dz) in ((0, 0), (3, 0), (0, 2), (3, 2)):
        b.column(x + dx, z + dz, y + 1, y + (4 if dz == 0 else 3), fence("spruce"))
        L.foundation_cells(b, [(x + dx, z + dz)], y + 1, "minecraft:spruce_planks", depth=3)
    for dx in range(-1, 5):
        cl = f"minecraft:{color}_wool" if dx % 2 == 0 else "minecraft:white_wool"
        for dz in range(-1, 4):
            b.set(x + dx, y + (5 if dz <= 0 else 4), z + dz, cl)
        if dx % 2 == 0: b.set(x + dx, y + 3, z + 3, cl)  # the fringe, hung from the front edge
    goods = [g for g in (goods or ()) if g]
    for dx in (1, 2):  # the counter between the front posts, goods on it
        b.set(x + dx, y + 1, z + 2, slab("minecraft:spruce_slab", "top"))
        if L._free(b, x + dx, y + 1, z + 3): b.set(x + dx, y + 1, z + 3, trapdoor("minecraft:spruce_trapdoor", "south", "bottom", "true"))
        if goods: b.set(x + dx, y + 2, z + 2, goods[(dx - 1) % len(goods)])
    for dx in (1, 2):  # stock at the back: barrels, the rest of the goods on top (plants need soil, so not those)
        b.set(x + dx, y + 1, z, "minecraft:barrel[facing=up,open=false]" if dx == 1 or rr.random() < 0.5 else "minecraft:hay_block[axis=y]")
        g = goods[(dx + 1) % len(goods)] if len(goods) > 2 else None
        if g and not any(k in g for k in L.PLANT): b.set(x + dx, y + 2, z, g)
    for (cx, cz) in ((x - 1, z + 1), (x + 4, z + 1)):  # a crate or pot beside the stall, under the awning
        if L._free(b, cx, y + 1, cz) and L.ground_y(b, cx, cz) == y and rr.random() < 0.6:
            b.set(cx, y + 1, cz, rr.choice(("minecraft:barrel[facing=up,open=false]", "minecraft:decorated_pot[cracked=false,facing=south,waterlogged=false]")))


def pier(b, x0, z0, length, axis="z", y=1, w=3, posts=4, boat=True):
    for i in range(length):
        for k in range(w):
            x, z = (x0 + k, z0 + i) if axis == "z" else (x0 + i, z0 + k)
            b.set(x, y, z, "minecraft:spruce_planks")
        if i % posts == 0:
            for k in (-1, w):
                x, z = (x0 + k, z0 + i) if axis == "z" else (x0 + i, z0 + k)
                b.column(x, z, y - 5, y + 1, "minecraft:spruce_log[axis=y]")
                b.set(x, y + 2, z, lantern()) if i % (posts * 2) == 0 else None
    if boat:
        bx, bz = (x0 + w + 1, z0 + length - 6) if axis == "z" else (x0 + length - 6, z0 + w + 1)
        for i in range(5):
            for k in (0, 1):
                x, z = (bx + k, bz + i) if axis == "z" else (bx + i, bz + k)
                b.set(x, y - 1, z, "minecraft:oak_planks" if 0 < i < 4 else "minecraft:oak_slab[type=top,waterlogged=false]")


def windmill(b, x, z, y=0, h=12):
    b.cyl(x, z, 3, y, y + h, "minecraft:white_concrete", hollow=True)
    for yy in range(y + 3, y + h, 4): b.set(x + 3, yy, z, "minecraft:glass_pane"); b.set(x - 3, yy, z, "minecraft:glass_pane")
    b.cyl(x, z, 2.2, y, y, "minecraft:spruce_planks")
    for k in range(4): b.cyl(x, z, 3.5 - k * 0.9, y + h + 1 + k, y + h + 1 + k, "minecraft:spruce_planks")
    b.set(x, y + 1, z + 3, AIR); b.set(x, y + 2, z + 3, AIR)
    hy = y + h - 1
    for a in (0, 90, 180, 270):  # sails on the south face
        t = math.radians(a + 20)
        for r in range(1, 9):
            px, py = round(x + r * math.cos(t)), round(hy + r * math.sin(t))
            b.set(px, py, z + 4, "minecraft:stripped_oak_log[axis=z]" if r < 2 else "minecraft:white_wool" if r > 3 else fence("oak"))
    b.set(x, hy, z + 4, "minecraft:oak_log[axis=z]")
    I.furnish(b, x - 1, y + 1, z - 1, x + 1, z + 1, 3, "storage", "pirate", seed=x + z)


def lamp_post(b, x, z, y=0, style=None):
    """A street lamp on the ground at (x, z) (landkit styles: wood, hanging arm, stone foot, street column on stone
    paving), picked per spot so a street mixes them; where the ground can't be read (a deck, water) it is the old
    fence post with a lantern at y + 1."""
    g = L.ground_y(b, x, z)
    top = L._sh(b.get(x, g, z))
    if y or g < 0 or top not in L.SURFACE or not L._free(b, x, g + 1, z):
        b.column(x, z, y + 1, y + 3, fence("dark_oak")); b.set(x, y + 4, z, lantern()); return
    rr = random.Random(x * 92821 + z * 68917)
    paved = top in ("stone_bricks", "cobblestone", "mossy_stone_bricks", "cracked_stone_bricks", "polished_andesite", "andesite", "mossy_cobblestone")
    L.lamp_post(b, x, z, rr, style or ("street" if paved and rr.random() < 0.7 else rr.choice(("wood", "hanging", "hanging", "stone"))))


def tree(b, x, z, y=0, kind="oak", h=5, r=2.6, legacy=False, under=True):
    """A tree on the ground at (x, z): landkit.tree2 (leaning or forked trunk, branches, clustered crowns, roots in
    rooted dirt) with a little understory (moss or leaf litter, grass, ferns, now and then a bush or flowers).
    h is the trunk height as before (the crown sits on top). legacy=True, a kind tree2 doesn't know, or a y that is
    not the ground there: the old trunk and ellipsoid."""
    g = L.ground_y(b, x, z)
    if legacy or kind not in L.TREE or (y and y != g) or L._sh(b.get(x, g, z)) not in L.SURFACE or not L._free(b, x, g + 1, z):
        def old():  # the old trunk and ellipsoid, its leaves only in free cells (it used to write over walls)
            for yy in range(y + 1, y + h + 1): b.set(x, yy, z, f"minecraft:{kind}_log[axis=y]")
            ri, ry = int(r) + 1, r * 0.8
            for dx in range(-ri, ri + 1):
                for dy in range(-ri, ri + 1):
                    for dz in range(-ri, ri + 1):
                        if (dx / r) ** 2 + (dy / ry) ** 2 + (dz / r) ** 2 <= 1: L._put(b, x + dx, y + h + 1 + dy, z + dz, f"minecraft:{kind}_leaves[distance=7,persistent=true,waterlogged=false]")
        L.crown_guard(b, old)
        return
    rr = random.Random(x * 7349 + z * 1931 + h * 17)
    lo, hi = L.TREE[kind][2]
    if L.tree2(b, x, z, kind, h=max(lo, min(hi + 1, h + 2 + rr.randint(-1, 1))), rnd=rr) is None:  # no room for a crown here
        L.bush(b, x, z, rr); return
    if not under: return
    litter = "minecraft:pink_petals" if kind == "cherry" else "minecraft:leaf_litter" if kind in ("oak", "birch", "dark_oak", "pale_oak") else None
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            d = math.hypot(dx, dz)
            if d > 3.2 or (dx == dz == 0): continue
            q = rr.random()
            if q < 0.12 and litter and d < 2.5: L._plant(b, x + dx, z + dz, litter, rr)
            elif q < 0.20 and d < 2.2: L._plant(b, x + dx, z + dz, "minecraft:moss_carpet")
            elif q < 0.30: L._plant(b, x + dx, z + dz, "minecraft:short_grass")
            elif q < 0.34: L._plant(b, x + dx, z + dz, "minecraft:fern")
    if rr.random() < 0.5:
        a = rr.random() * math.tau; L.bush(b, x + round(math.cos(a) * 3), z + round(math.sin(a) * 3), rr)
    elif rr.random() < 0.6:
        a = rr.random() * math.tau
        L.flower_clump(b, x + round(math.cos(a) * 3), z + round(math.sin(a) * 3), rr.choice(L.FLOWERS), rr, n=rr.randint(3, 5), r=1)


def orchard_tree(b, x, z, y=0, fruit="onepiece:mikan_bush"):
    for yy in range(y + 1, y + 4): b.set(x, yy, z, "minecraft:jungle_log[axis=y]")
    b.sphere(x, y + 5, z, 2.2, "minecraft:jungle_leaves[distance=7,persistent=true,waterlogged=false]", ry=1.6)
    for (dx, dz) in ((2, 0), (-2, 0), (0, 2), (0, -2)): b.set(x + dx, y + 4, z + dz, "minecraft:orange_concrete")


def _field(b, x0, z0, x1, z1, y, crop, cold, rr, gate=True):
    """One fenced bed of crops at level y: water channels every 4, a bank of coarse dirt under the edge, log posts at
    the corners (one with a lantern), a scarecrow in the middle row, a gate on the south side."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            edge = x in (x0, x1) or z in (z0, z1)
            for yy in range(y + 1, y + 8):  # plants, and on a slope the higher ground, off the bed
                s = b.blocks.get((x, yy, z))
                if s and (L._free(b, x, yy, z) or L._sh(s) in L.GROUND): b.blocks.pop((x, yy, z))
            L.foundation_cells(b, [(x, z)], y, "minecraft:dirt" if not edge else "minecraft:coarse_dirt", depth=6)
            if edge:
                if L._free(b, x, y, z) or L._sh(b.get(x, y, z)) in L.GROUND: b.set(x, y, z, "minecraft:coarse_dirt")
                corner = x in (x0, x1) and z in (z0, z1)
                b.set(x, y + 1, z, "minecraft:stripped_spruce_log[axis=y]" if corner else fence("oak"))
            elif (x - x0) % 4 == 2:
                b.set(x, y, z, WATER)
                b.set(x, y + 1, z, "minecraft:spruce_slab[type=bottom,waterlogged=false]" if cold else AIR)
            else: b.set(x, y, z, "minecraft:farmland[moisture=7]"); b.set(x, y + 1, z, crop)
    b.set(x0, y + 2, z0, lantern()) if rr.random() < 0.7 else None
    if gate: b.set((x0 + x1) // 2, y + 1, z1, "minecraft:oak_fence_gate[facing=south,in_wall=false,open=false,powered=false]")
    if x1 - x0 >= 6 and z1 - z0 >= 4:  # a scarecrow on a crop row
        sx, sz = x0 + 3, (z0 + z1) // 2
        b.set(sx, y + 1, sz, fence("oak")); b.set(sx, y + 2, sz, "minecraft:hay_block[axis=y]")
        b.set(sx, y + 3, sz, "minecraft:carved_pumpkin[facing=south]")
        for ax in (-1, 1):
            if b.get(sx + ax, y + 2, sz) in (None, AIR): b.set(sx + ax, y + 2, sz, fence("oak"))


def garden(b, x0, z0, x1, z1, y=0, crop="minecraft:wheat[age=7]", rnd=None, cold=None):
    """A fenced crop field with water channels. In snow (cold) the channels get a slab lid, so they don't freeze over.
    On a slope (y not given and the ground under it differs) it is built as 2 or 3 terraced beds across the slope,
    each level with its own fence on a coarse-dirt bank (guide 9b.4). Log corner posts, a lantern, a scarecrow, a
    composter by the gate."""
    if cold is None:
        near = [b.get(x, y, z) or "" for x in (x0 - 1, x1 + 1) for z in (z0 - 1, z1 + 1)] + [b.get(x, y + 1, z) or "" for x in (x0 - 1, x1 + 1) for z in (z0 - 1, z1 + 1)]
        cold = any("snow" in s or "ice" in s for s in near)
    rr = random.Random(x0 * 31 + z0 * 17 + x1)
    hs = {(x, z): L.ground_y(b, x, z) for x in range(x0, x1 + 1) for z in range(z0, z1 + 1)} if not y else {}
    if not y and hs and max(hs.values()) - min(hs.values()) >= 1 and z1 - z0 >= 6:
        n = 2 if z1 - z0 < 12 else 3
        cuts = [z0 + round(i * (z1 - z0 + 1) / n) for i in range(n + 1)]
        for a, c in zip(cuts, cuts[1:]):
            ys = sorted(h for (x, z), h in hs.items() if a <= z < c)
            _field(b, x0, a, x1, c - 1, ys[len(ys) // 2], crop, cold, rr)
    else:
        if not y and hs: y = sorted(hs.values())[len(hs) // 2]
        _field(b, x0, z0, x1, z1, y, crop, cold, rr)
    gx, gy = (x0 + x1) // 2 + 2, L.ground_y(b, (x0 + x1) // 2 + 2, z1 + 1)
    if L._free(b, gx, gy + 1, z1 + 1) and L._sh(b.get(gx, gy, z1 + 1)) in ("grass_block", "dirt", "podzol", "snow_block", "sand"):
        b.set(gx, gy + 1, z1 + 1, "minecraft:composter[level=3]")


NATURAL = {"dirt_path": None, "coarse_dirt": None, "gravel": None, "dirt": None, "rooted_dirt": None, "podzol": None,
           "mud": ("minecraft:packed_mud", "minecraft:coarse_dirt", "minecraft:mud", "minecraft:rooted_dirt"),
           "packed_mud": ("minecraft:mud", "minecraft:coarse_dirt", "minecraft:packed_mud", "minecraft:rooted_dirt"),
           "snow_block": ("minecraft:snow_block", "minecraft:snow_block", "minecraft:gravel", "minecraft:coarse_dirt")}
STONE_PATHS = {"stone_bricks", "cobblestone", "mossy_cobblestone", "andesite", "mossy_stone_bricks", "cracked_stone_bricks", "stone"}


def _path_legacy(b, pts, w=1, y=0, s="minecraft:dirt_path", alt=None, only=None):
    for (a, c) in zip(pts, pts[1:]):
        n = int(max(abs(c[0] - a[0]), abs(c[1] - a[1]))) + 1
        for i in range(n):
            t = i / max(1, n - 1)
            x, z = round(a[0] + (c[0] - a[0]) * t), round(a[1] + (c[1] - a[1]) * t)
            for dx in range(-w, w + 1):
                for dz in range(-w, w + 1):
                    if only and not only(x + dx, z + dz): continue
                    if b.get(x + dx, y + 1, z + dz) in (None, AIR) or "grass" in (b.get(x + dx, y + 1, z + dz) or ""):
                        b.set(x + dx, y, z + dz, alt if alt and (x + dx + z + dz) % 3 == 0 else s)
                        if (b.get(x + dx, y + 1, z + dz) or "").startswith("minecraft:short_grass"): b.set(x + dx, y + 1, z + dz, AIR)


def _clear_props(b, pts, w, near=None):
    """A path (or a house) laid after the houses lifts any yard prop (whole, never half a cart) standing within w of
    its line (or on the `near` cells)."""
    props = getattr(b, "_tk_props", None)
    if not props: return
    if near is None:
        near = set()
        for (a, c) in zip(pts, pts[1:]):
            n = int(max(abs(c[0] - a[0]), abs(c[1] - a[1]))) + 1
            for i in range(n):
                t = i / max(1, n - 1)
                x, z = round(a[0] + (c[0] - a[0]) * t), round(a[1] + (c[1] - a[1]) * t)
                near.update((x + dx, z + dz) for dx in range(-w, w + 1) for dz in range(-w, w + 1))
    keep = []
    for cells in props:
        if any((q[0], q[2]) in near for q in cells):
            for q, (old, new) in cells.items():
                if b.blocks.get(q) != new: continue  # built over since: leave it
                if old is None: b.blocks.pop(q, None)
                else: b.blocks[q] = old
        else: keep.append(cells)
    b._tk_props = keep


def path(b, pts, w=1, y=0, s="minecraft:dirt_path", alt=None, organic=None, rnd=None):
    """A path through the points, w blocks either side of the line. Earth, gravel, mud, snow and stone streets are
    laid as landkit.organic_path (guide 11c): a smooth curve with a sideways wobble, width +-1, a broken edge mix
    with some grass left, following the ground with a stair at every 1-block climb, never paved over built cells.
    `alt` is mixed into the middle. Other materials (planks, concrete, quartz, terracotta, custom cobbles) are
    designed surfaces and keep the old straight raster, as does organic=False; where the old raster crossed water
    at y it still lays the causeway it always did."""
    _clear_props(b, pts, w + 2)
    sh = L._sh(s)
    org = organic if organic is not None else (sh in NATURAL or sh in STONE_PATHS) and not y
    if not org: return _path_legacy(b, pts, w, y, s, alt)
    rr = rnd or random.Random(sum(int(p[0]) * 31 + int(p[1]) * 17 for p in pts) + len(pts))
    if sh in STONE_PATHS:
        mid = [(s, 8)] + ([(alt, 4)] if alt else []) + [(m, wt // 8) for m, wt in L.STREET if m not in (s, alt) and wt >= 8]
        done = L.organic_path(b, pts, 2 * w + 1, rr, mid=mid, street=True, wobble=0.5, grass=0.15)
    else:
        mid = [(s, 7)] + ([(alt, 3)] if alt else [])
        edge = NATURAL[sh] or L.EDGE
        done = L.organic_path(b, pts, 2 * w + 1, rr, mid=mid, edge=edge, grass=0.4 if sh == "snow_block" else 0.25, wobble=0.9)
    _path_legacy(b, pts, w, y, s, alt, only=lambda x, z: (b.get(x, y, z) or "").startswith("minecraft:water"))
    return done


def ground(b, nx, nz, rnd, top="minecraft:grass_block", deco=0.06, decos=("minecraft:short_grass", "minecraft:dandelion", "minecraft:poppy", "minecraft:short_grass"),
           legacy=False):
    """The site's ground: dirt to y -3 and `top` at y 0 (flat, so streets and buildings placed later sit right). The
    plants are no longer an even speckle: they grow in drifts (smooth noise, denser in some patches, bare in others)
    and every flower in `decos` comes in one-colour clumps, so a meadow reads as planted by nature (guide 11d).
    Relief is landscape(), called once the town stands (it needs to know where the buildings are)."""
    if legacy:
        for x in range(nx):
            for z in range(nz):
                for y in (-3, -2, -1): b.set(x, y, z, "minecraft:dirt")
                b.set(x, 0, z, top)
                if deco and rnd.random() < deco: b.set(x, 1, z, rnd.choice(decos))
        return
    seed = nx * 131 + nz * 71 + len(decos)  # never a draw: the caller's rnd advances exactly as the old speckle did
    grassy = [d for d in decos if any(k in d for k in ("grass", "fern", "snow[", "moss", "dead_bush", "leaf", "petals"))] or list(decos)
    flowers = [d for d in decos if d not in grassy]
    for x in range(nx):
        for z in range(nz):
            for y in (-3, -2, -1): b.set(x, y, z, "minecraft:dirt")
            b.set(x, 0, z, top)
            if not deco: continue
            if rnd.random() < deco: rnd.choice(decos)
            m = L.noise2(x, z, seed, 7) * 0.7 + L.noise2(x, z, seed + 1, 3) * 0.3
            if L.noise2(x * 5 + 3, z * 5 + 1, seed + 5, 1) < deco * max(0.0, 2.8 * m - 0.5):
                fm = L.noise2(x, z, seed + 2, 4)
                if flowers and fm > 0.7: b.set(x, 1, z, flowers[int(L.noise2(x, z, seed + 3, 9) * len(flowers) * 0.999)])
                else: b.set(x, 1, z, grassy[int(L.noise2(x * 3, z * 3, seed + 4, 2) * len(grassy) * 0.999)])


NATURAL_TOPS = ("grass_block", "sand", "red_sand", "snow_block", "podzol", "moss_block")


def landscape(b, x0, z0, x1, z1, rnd, amp=3, cell=18, keep=None, rocks=True, meadow=False, top=None, edge=10, unpave=None):
    """Opt-in, call it LAST, once everything in the town stands (guide 9b.1, 11a): raise the bare open ground into
    gentle rises of up to `amp` (landkit.relief: built columns, streets, paths and plazas stay at their level with a
    4-block blend round them; keep(x, z) -> True protects more), then scatter half-sunk boulders on the open ground
    (1 per ~200 m2) and, with meadow=True, grass drifts and flower clumps. top: the site's own ground block when it is
    not grass, sand or snow (coarse dirt); edge: rises stay this far in from the rect border (pipeline.soften_edges
    keeps ground near anything raised, so a rise close to the border would square the outline off again). unpave: the
    paving block a stone site was laid in (Loguetown): open paving 4+ from anything built turns to grass first, with a
    broken edge of gravel and coarse dirt, so the empty corners are not a stone plate. Returns the height map."""
    tops = NATURAL_TOPS + ((L._sh(top),) if top else ())
    if unpave: _unpave(b, x0, z0, x1, z1, unpave, rnd, keep)
    paved = lambda x, z: L._sh(b.get(x, 0, z)) not in tops
    folk = {(int(e[1]) + dx, int(e[3]) + dz) for e in getattr(b, "entities", ()) for dx in (-1, 0, 1) for dz in (-1, 0, 1)}  # people stand where they were put
    flat = lambda x, z: paved(x, z) or (x, z) in folk or (keep and keep(x, z))
    H = L.relief(b, x0, z0, x1, z1, rnd.randint(0, 9999), amp=amp, cell=cell, keep_flat=flat, edge=edge)
    if rocks:
        opens = [c for c in H if H[c] >= 1] or []
        for _ in range(len(opens) // 200):
            x, z = rnd.choice(opens)
            if all(L._free(b, x + dx, L.ground_y(b, x + dx, z + dz) + 1, z + dz) for dx in (-2, 0, 2) for dz in (-2, 0, 2)):
                L.boulder(b, x, z, rnd.uniform(1.2, 2.2), rnd)
    if meadow: L.meadow(b, x0, z0, x1, z1, rnd, density=0.06, avoid=flat)
    return H


def _unpave(b, x0, z0, x1, z1, block, rnd, keep=None, dist=4):
    """Open paving of `block` (only plants or nothing above it) more than `dist` from anything built becomes grass,
    the cells 1 short of that a mix of gravel and coarse dirt, so a paved site frays into ground instead of ending in
    a stone plate."""
    sh = L._sh(block)
    cols = {}
    for (x, y, z), v in b.blocks.items():
        if x0 <= x <= x1 and z0 <= z <= z1 and 1 <= y <= 40 and v != AIR and not L._free(b, x, y, z): cols[(x, z)] = True
    open_ = {(x, z) for x in range(x0, x1 + 1) for z in range(z0, z1 + 1) if L._sh(b.get(x, 0, z)) == sh and (x, z) not in cols
             and not (keep and keep(x, z))}
    fixed = [(x, z) for x in range(x0, x1 + 1) for z in range(z0, z1 + 1) if (x, z) not in open_]
    d = {c: 0 for c in fixed}; front = list(fixed)
    for k in range(1, dist + 2):
        nxt = []
        for (x, z) in front:
            for n in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)):
                if n in open_ and n not in d: d[n] = k; nxt.append(n)
        front = nxt
    for (x, z) in open_:
        k = d.get((x, z), 99) + L.noise2(x, z, 913, 3) * 2 - 1
        if k > dist: b.set(x, 0, z, "minecraft:grass_block")
        elif k > dist - 1.5: b.set(x, 0, z, rnd.choice(("minecraft:gravel", "minecraft:coarse_dirt", "minecraft:grass_block", "minecraft:cobblestone")))


def sea(b, nx, nz, inside, depth=5, floor="minecraft:sand"):
    """Cut sea water into the build where inside(x, z) is True (y 0 down to -depth)."""
    for x in range(nx):
        for z in range(nz):
            if inside(x, z):
                for y in range(-depth, 1): b.set(x, y, z, WATER)
                b.set(x, -depth - 1, z, floor if floor != "minecraft:sand" else "minecraft:sandstone")
                if b.get(x, 1, z) is not None: b.set(x, 1, z, AIR)
