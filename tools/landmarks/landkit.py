"""Terrain and planting kit (BUILDING_GUIDE sections 11 and 15): relief, terraces, foundations, rocks, branched trees,
palms, groves with understory, organic paths, lived-in clutter and lamp posts.

Every helper reads the local ground with ground_y() instead of assuming y 0, so it works on a relief, a terrace or a
hill. Nothing is left floating: props stand on ground or lean on a wall, lanterns stand on or hang from a block, and
lines run between two posts. Pass a random.Random (rnd) so builds stay deterministic."""
import math
from canvas import *  # noqa: F401,F403

# pipeline.GROUND plus the bare earth and rock that relief(), paths and banks put on the surface. Copied, not
# imported: pipeline loads the landmark modules (and finish), so landkit stays importable on its own.
GROUND = {"grass_block", "dirt", "podzol", "sand", "red_sand", "snow_block", "snow", "mycelium", "rooted_dirt", "moss_block",
          "mud", "sandstone", "red_sandstone", "terracotta", "clay", "packed_mud", "powder_snow",
          "coarse_dirt", "gravel", "dirt_path", "stone", "andesite", "tuff", "diorite", "granite", "calcite", "pale_moss_block",
          "muddy_mangrove_roots", "suspicious_gravel"}
PLANT = ("short_grass", "tall_grass", "fern", "large_fern", "dandelion", "poppy", "flower", "tulip", "orchid", "allium",
         "bluet", "daisy", "cornflower", "lily_of_the_valley", "bush", "dead_bush", "sweet_berry", "petals", "sapling",
         "mushroom", "leaf_litter", "wildflowers", "cactus", "sugar_cane", "seagrass", "snow[", "moss_carpet", "_dry_grass")
SOIL = {"grass_block", "dirt", "podzol", "coarse_dirt", "rooted_dirt", "moss_block", "mud", "packed_mud", "muddy_mangrove_roots"}
DIRS = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
TOP_Y = 60  # ground_y scans down from here
# what ground_y also stands things on: paving and retaining-wall tops (relief only lifts natural GROUND)
SURFACE = GROUND | {"stone_bricks", "mossy_stone_bricks", "cracked_stone_bricks", "cobblestone", "mossy_cobblestone", "polished_andesite",
                    "smooth_sandstone", "cut_sandstone", "farmland", "mud_bricks"}


def _sh(s):
    return s.split("[")[0].split(":")[-1] if s else ""


def _free(b, x, y, z):
    """Air, nothing, or a plant: a cell a prop or a leaf may take."""
    s = b.blocks.get((x, y, z))
    return s is None or s == AIR or _sh(s) in ("air", "cave_air") or any(k in s for k in PLANT)


def _put(b, x, y, z, s):
    if _free(b, x, y, z): b.set(x, y, z, s)


def ground_y(b, x, z, top=TOP_Y, low=-16):
    """Highest ground block in the column (grass, dirt, sand, bare rock, paving...), or 0 if the column has none."""
    for y in range(top, low - 1, -1):
        s = b.blocks.get((x, y, z))
        if s and _sh(s) in SURFACE: return y
    return 0


def noise2(x, z, seed, cell=11):
    """Smooth value noise in 0..1 (same hash as pipeline._noise, so soften_edges and relief agree in style)."""
    def h(i, j):
        n = (i * 73856093) ^ (j * 19349663) ^ (seed * 83492791)
        n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
        return (n & 0xFFFF) / 65535
    fx, fz = x / cell, z / cell
    i, j = math.floor(fx), math.floor(fz)
    tx, tz = fx - i, fz - j
    tx, tz = tx * tx * (3 - 2 * tx), tz * tz * (3 - 2 * tz)
    a = h(i, j) + (h(i + 1, j) - h(i, j)) * tx
    c = h(i, j + 1) + (h(i + 1, j + 1) - h(i, j + 1)) * tx
    return a + (c - a) * tz


def _smooth(t):
    t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)


def _rock(x, y, z, seed, moss=True):
    """Bare rock in patches (not salt and pepper): stone, andesite, tuff and moss, as real banks show it."""
    r = noise2(x * 1.7 + y * 3.1, z * 1.7 - y * 2.3, seed + 41, cell=3)
    if r < 0.30: return "minecraft:stone"
    if r < 0.50: return "minecraft:andesite"
    if r < 0.62: return "minecraft:tuff"
    if r < 0.72 and moss: return "minecraft:moss_block"
    if r < 0.84: return "minecraft:coarse_dirt"
    return "minecraft:stone"


def _variant(block, kind):
    """cobblestone -> cobblestone_stairs, stone_bricks -> stone_brick_stairs, ... (kind: stairs, slab, wall)."""
    n = block.split("[")[0]
    for pl, si in (("bricks", "brick"), ("tiles", "tile"), ("_planks", "")):
        if n.endswith(pl): n = n[: -len(pl)] + si; break
    if kind == "wall" and _sh(n) not in WALLS: n = "minecraft:cobblestone"
    return f"{n}_{kind}"


WALLS = {"cobblestone", "mossy_cobblestone", "stone_brick", "mossy_stone_brick", "sandstone", "red_sandstone", "brick", "mud_brick",
         "andesite", "granite", "diorite", "deepslate_brick", "cobbled_deepslate", "polished_deepslate", "deepslate_tile", "tuff",
         "tuff_brick", "polished_tuff", "blackstone", "polished_blackstone", "polished_blackstone_brick", "nether_brick",
         "red_nether_brick", "end_stone_brick", "prismarine", "resin_brick"}
MOSSY = {"minecraft:cobblestone": "minecraft:mossy_cobblestone", "minecraft:stone_bricks": "minecraft:mossy_stone_bricks"}


def _vine(toward):
    """A vine in a cell, stuck to the block on its `toward` side."""
    f = {k: "false" for k in DIRS}; f[toward] = "true"
    return f"minecraft:vine[east={f['east']},north={f['north']},south={f['south']},up=false,west={f['west']}]"


# ------------------------------------------------------------------ terrain
def relief(b, x0, z0, x1, z1, seed, amp=3, cell=18, keep_flat=None, edge=6, blend=4):
    """Raise the site's ground by up to `amp` with smooth noise, so it rolls instead of lying flat as a plate.
    Only bare columns move (top = ground block at y 0, nothing but plants above); keep_flat(x, z) cells (streets,
    plazas) and every built column stay at 0, and the ground eases back to 0 over `blend` blocks round them and over
    `edge` blocks at the rect border (so soften_edges' skirt starts at 0). Under the surface: dirt 3 deep, then
    stone; where a column stands 2 or more above a neighbour its face is bare rock. Returns {(x, z): height}."""
    cols = {}
    for (x, y, z), s in b.blocks.items():
        if x0 <= x <= x1 and z0 <= z <= z1 and -4 <= y <= TOP_Y: cols.setdefault((x, z), {})[y] = s
    def bare(c):
        ys = cols.get(c, {})
        if _sh(ys.get(0)) not in GROUND: return False
        return all(y < 1 or _sh(s) in ("air", "cave_air") or any(k in s for k in PLANT) for y, s in ys.items())
    fixed = [c for c in cols if not bare(c) or (keep_flat and keep_flat(*c))]
    # distance (chamfer, 8 ways) to the nearest fixed column, out to `blend`
    dist = {c: 0.0 for c in fixed}
    front = list(fixed)
    while front:
        nxt = []
        for (x, z) in front:
            d = dist[(x, z)]
            for dx, dz, k in ((1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.41), (1, -1, 1.41), (-1, 1, 1.41), (-1, -1, 1.41)):
                n = (x + dx, z + dz)
                if n in cols and d + k < dist.get(n, 1e9) and d + k <= blend + 1:
                    dist[n] = d + k; nxt.append(n)
        front = nxt
    H = {}
    for c in cols:
        if not bare(c) or (keep_flat and keep_flat(*c)): continue
        x, z = c
        n = 0.6 * noise2(x, z, seed, cell) + 0.28 * noise2(x, z, seed + 1, cell / 2.6) + 0.12 * noise2(x, z, seed + 2, cell / 6)
        n = min(1.0, max(0.0, (n - 0.32) / 0.5)) ** 1.15  # flat meadows between the rises, rounded tops
        w = _smooth(dist.get(c, 99) / blend) * _smooth(min(x - x0, x1 - x, z - z0, z1 - z) / max(1, edge))
        h = int(round(amp * n * w))
        if h > 0: H[c] = h
    for (x, z), h in H.items():
        ys = cols[(x, z)]
        top = ys[0]
        under = "minecraft:sandstone" if _sh(top) in ("sand", "red_sand") else "minecraft:dirt"
        if _sh(top) in ("dirt", "coarse_dirt", "rooted_dirt", "gravel"): under = top
        plants = {y: s for y, s in ys.items() if y >= 1 and any(k in s for k in PLANT)}
        for y in plants: b.blocks.pop((x, y, z), None)
        for y in range(-3, h): b.set(x, y, z, under if y >= h - 3 else "minecraft:stone")
        b.set(x, h, z, top)
        for y, s in plants.items(): b.set(x, y + h, z, s)
    # rock on the faces of steps of 2 or more
    for (x, z), h in H.items():
        low = min(H.get((x + dx, z + dz), 0) for dx, dz in DIRS.values())
        if h - low < 2: continue
        for y in range(low + 1, h): b.set(x, y, z, _rock(x, y, z, seed))
        if h - low >= 3 and noise2(x, z, seed + 5, 4) < 0.5:
            b.set(x, h, z, _rock(x, h, z, seed, moss=True))
            if (x, h + 1, z) in b.blocks and _free(b, x, h + 1, z): b.blocks.pop((x, h + 1, z))
            if "upper" in (b.get(x, h + 2, z) or ""): b.blocks.pop((x, h + 2, z))
    return H


def foundation_cells(b, cells, y, block, depth=8):
    """Continue a base course down from y-1 under every cell until it meets solid ground (or y - depth), so no wall,
    post or floor hangs over lower ground. The world fills what is below y - depth; tiler culls what is buried."""
    for (x, z) in cells:
        for yy in range(y - 1, y - depth - 1, -1):
            if not _free(b, x, yy, z): break
            b.set(x, yy, z, block)


def foundation(b, x0, z0, x1, z1, y, block, depth=8):
    foundation_cells(b, [(x, z) for x in range(x0, x1 + 1) for z in range(z0, z1 + 1)], y, block, depth)


def terrace(b, x0, z0, x1, z1, y, wall_block, rnd, top=None, stair=True, kink=True):
    """A level pad at y for a house on a slope: fills lower ground with dirt, cuts higher ground away, and holds the
    drop with a retaining wall of wall_block that kinks in or out by 1 every 4-6 blocks (no straight 10-block edge),
    with a stair skirt at its foot, moss and vines on about 20 %, a wall rail where the drop is over 2, and a
    2-wide stair down the face (stair=True: the highest drop; or a side name such as "south"; False: none). Cut faces
    uphill are walled too. Returns (pad cells, (x, z) at the stair foot or None) so a path can start there."""
    pad = {(x, z) for x in range(x0, x1 + 1) for z in range(z0, z1 + 1)}
    if kink:
        for side in DIRS:
            run = list(range(x0 + 1, x1)) if side in ("north", "south") else list(range(z0 + 1, z1))
            i = 0
            while i < len(run):
                L = rnd.randint(4, 6); k = rnd.choice((-1, 0, 0, 1))
                for a in run[i:i + L]:
                    if side == "north": c, o = (a, z0), (a, z0 - 1)
                    elif side == "south": c, o = (a, z1), (a, z1 + 1)
                    elif side == "west": c, o = (x0, a), (x0 - 1, a)
                    else: c, o = (x1, a), (x1 + 1, a)
                    if k > 0: pad.add(o)
                    elif k < 0: pad.discard(c)
                i += L
    G = {c: ground_y(b, *c) for c in pad}
    for (x, z), g in G.items():
        surf = b.get(x, g, z)
        surf = top or (surf if _sh(surf) in ("grass_block", "sand", "podzol", "snow_block", "moss_block", "red_sand") else "minecraft:grass_block")
        under = "minecraft:sandstone" if "sand" in surf else "minecraft:dirt"
        for yy in range(y + 1, max(g, y) + 3):
            if (x, yy, z) in b.blocks and (_sh(b.blocks[(x, yy, z)]) in GROUND or _free(b, x, yy, z)): b.blocks[(x, yy, z)] = AIR
        for yy in range(min(g, y - 3), y):
            if yy > g - 1 or _free(b, x, yy, z): b.set(x, yy, z, under)
        b.set(x, y, z, surf)
    # retaining walls: pad cells next to lower outside ground (downhill) and outside cells higher than the pad (cuts)
    mossy = MOSSY.get(wall_block.split("[")[0], wall_block)
    st = _variant(wall_block, "stairs"); rail = wall(_variant(wall_block, "wall"))
    def wb(x, yy, z):
        return mossy if noise2(x * 2 + yy, z * 2 - yy, 77, 2.2) < 0.22 else wall_block
    down = []
    for (x, z) in pad:
        for f, (dx, dz) in DIRS.items():
            q = (x + dx, z + dz)
            if q in pad: continue
            gq = ground_y(b, *q)
            if gq < y:
                down.append(((x, z), q, f, y - gq))
                for yy in range(gq - 1, y): b.set(x, yy, z, wb(x, yy, z))
                # the top course: wall where the drop is tall, else the pad's grass grows to the edge
                if y - gq >= 3 or noise2(x, z, 91, 3) < 0.35: b.set(x, y, z, wb(x, y, z))
            elif gq > y + 1:  # uphill cut: wall the bank so the hill doesn't hang over the pad
                for yy in range(y + 1, gq + 1):
                    if _free(b, q[0], yy, q[1]) or _sh(b.blocks.get((q[0], yy, q[1]))) in GROUND: b.set(q[0], yy, q[1], wb(q[0], yy, q[1]))
                if gq - y > 3: _put(b, q[0], gq + 1, q[1], rail)
    cand = [t for t in down if stair is True or t[2] == stair]
    mid = ((x0 + x1) / 2, (z0 + z1) / 2)
    best = max(cand, key=lambda t: (min(t[3], 3), -abs(t[0][0] - mid[0]) - abs(t[0][1] - mid[1])), default=None) if stair else None
    for (p, q, f, drop) in down:
        if drop >= 2: _put(b, q[0], y - drop + 1, q[1], stairs(st, OPP[f]))
        if drop > 2: _put(b, p[0], y + 1, p[1], rail)
        if drop >= 2 and rnd.random() < 0.2:
            for k in range(rnd.randint(1, drop - 1)):
                _put(b, q[0], y - k, q[1], _vine(OPP[f]))
    foot = None
    if best:  # a 2-wide flight down the face, each step on a footing of the wall block
        (px, pz), _, f, drop = best
        dx, dz = DIRS[f]
        for w in (0, 1):
            sx, sz = px + dz * w, pz + dx * w
            if (sx, sz) not in pad: continue
            b.blocks.pop((sx, y + 1, sz), None)
            for i in range(1, drop + 2):
                cx, cz, cy = sx + dx * i, sz + dz * i, y - i + 1
                if cy <= ground_y(b, cx, cz):
                    foot = foot or (cx, cz); break
                b.set(cx, cy, cz, stairs(st, OPP[f]))
                for yy in range(cy + 1, cy + 4):
                    if (cx, yy, cz) in b.blocks and _free(b, cx, yy, cz): b.blocks.pop((cx, yy, cz))
                foundation_cells(b, [(cx, cz)], cy, wall_block, depth=6)
    return pad, foot


def boulder(b, x, z, r, rnd):
    """A half-sunk rock cluster on the ground: one lumpy body of radius r plus 1-2 small stones beside it, mixed
    stone/andesite/cobble with moss on top, a button or wall bit for irregularity. Columns that would overhang lower
    ground are filled down, so no rock floats on a slope."""
    mats = ("minecraft:stone",) * 4 + ("minecraft:andesite",) * 3 + ("minecraft:cobblestone", "minecraft:tuff", "minecraft:mossy_cobblestone")
    parts = [(x, z, r)]
    for _ in range(rnd.randint(1, 2)):
        a = rnd.random() * math.tau; d = r + rnd.uniform(0.6, 1.6)
        parts.append((x + round(math.cos(a) * d), z + round(math.sin(a) * d), max(0.8, r * rnd.uniform(0.35, 0.6))))
    seed = rnd.randint(0, 99999)
    for (cx, cz, rr) in parts:
        g = ground_y(b, cx, cz)
        cy = g - rr * 0.35
        tops = {}
        for dx in range(-int(rr) - 1, int(rr) + 2):
            for dz in range(-int(rr) - 1, int(rr) + 2):
                for dy in range(-int(rr) - 1, int(rr) + 2):
                    j = 0.75 + 0.5 * noise2(cx + dx, (cz + dz) * 1.3 + dy * 2.1, seed, 2.0)
                    if (dx / rr) ** 2 + (dy / (rr * 0.8)) ** 2 + (dz / rr) ** 2 > j: continue
                    yy = round(cy + dy)
                    if yy <= ground_y(b, cx + dx, cz + dz) - 1: continue
                    m = rnd.choice(mats)
                    b.set(cx + dx, yy, cz + dz, m)
                    tops[(cx + dx, cz + dz)] = max(tops.get((cx + dx, cz + dz), -99), yy)
        for (px, pz), ty in tops.items():
            for k in (1, 2):  # a plant that stood on the old ground would now stand on rock
                q = b.blocks.get((px, ty + k, pz))
                if q and any(t in q for t in PLANT): b.blocks.pop((px, ty + k, pz))
            gb = ground_y(b, px, pz, top=ty - 1)
            for yy in range(gb + 1, ty): _put(b, px, yy, pz, "minecraft:stone")
            if rnd.random() < 0.3 and ty >= g + 1:
                b.set(px, ty, pz, "minecraft:mossy_cobblestone" if rnd.random() < 0.5 else "minecraft:moss_block")
                if rnd.random() < 0.4: _put(b, px, ty + 1, pz, "minecraft:moss_carpet")
        if rr >= 1.5 and tops and rnd.random() < 0.5:
            (px, pz), ty = max(tops.items(), key=lambda t: t[1])
            _put(b, px, ty + 1, pz, "minecraft:stone_button[face=floor,facing=north,powered=false]" if rnd.random() < 0.5
                 else wall("minecraft:cobblestone_wall"))


# ------------------------------------------------------------------ trees
TREE = {  # wood, leaves, default height range
    "oak": ("oak", "oak", (5, 9)), "birch": ("birch", "birch", (7, 10)), "spruce": ("spruce", "spruce", (8, 13)),
    "dark_oak": ("dark_oak", "dark_oak", (5, 8)), "cherry": ("cherry", "cherry", (6, 8)), "jungle": ("jungle", "jungle", (9, 14)),
    "acacia": ("acacia", "acacia", (5, 7)), "mangrove": ("mangrove", "mangrove", (6, 9)), "pale_oak": ("pale_oak", "pale_oak", (6, 9)),
    "azalea": ("oak", "azalea", (4, 5)),
}
DIAG = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def _logs(b, pts, wood):
    """Lay logs along a face-connected chain of points, each log turned along the axis it was reached by."""
    prev = None
    for p in pts:
        ax = "y"
        if prev:
            d = (p[0] - prev[0], p[1] - prev[1], p[2] - prev[2])
            ax = "x" if d[0] else "z" if d[2] else "y"
        s = b.blocks.get(p)
        if s is None or _free(b, *p) or "leaves" in s: b.set(*p, log(wood, ax))
        prev = p


def _walk(p0, p1):
    """Face-connected 3D line from p0 to p1 (each step moves along one axis), so branches have no diagonal gaps."""
    pts = [p0]; x, y, z = p0
    while (x, y, z) != tuple(p1):
        rem = [p1[0] - x, p1[1] - y, p1[2] - z]
        i = max(range(3), key=lambda k: abs(rem[k]) + (0.1 if k == 1 else 0))
        if i == 0: x += 1 if rem[0] > 0 else -1
        elif i == 1: y += 1 if rem[1] > 0 else -1
        else: z += 1 if rem[2] > 0 else -1
        pts.append((x, y, z))
    return pts


def _blob(b, cx, cy, cz, rx, ry, rnd, leaf, rz=None, holes=0.15, down=None, droop=0.0):
    """A leaf cluster: an ellipsoid with a lumpy edge, flatter underneath (down = lower radius), with `holes` of
    the outer shell left out so the crown is not a smooth ball. droop > 0 hangs single leaves under the rim."""
    rz = rz or rx; down = down or ry * 0.7
    seed = rnd.randint(0, 99999)
    cells = []
    for dx in range(-int(rx) - 1, int(rx) + 2):
        for dz in range(-int(rz) - 1, int(rz) + 2):
            for dy in range(-int(down) - 1, int(ry) + 2):
                v = ry if dy >= 0 else down
                d = (dx / rx) ** 2 + (dy / v) ** 2 + (dz / rz) ** 2
                j = 0.82 + 0.36 * noise2(cx + dx + dy * 3.3, cz + dz - dy * 2.7, seed, 1.7)
                if d > j: continue
                if d > 0.6 * j and rnd.random() < holes: continue
                cells.append((cx + dx, cy + dy, cz + dz))
    for p in cells: _put(b, *p, leaf)
    if droop:
        for (x, y, z) in cells:
            if (x, y - 1, z) not in cells and math.hypot(x - cx, z - cz) > rx * 0.65 and rnd.random() < droop:
                for k in range(1, rnd.randint(1, 2) + 1): _put(b, x, y - k, z, leaf)
    return cells


def _roots(b, x, g, z, wood, rnd, size=1, soil=True):
    """Root flares: 1-3 sideways logs at the trunk foot (on and in the ground) and rooted dirt round it."""
    for (dx, dz) in rnd.sample(list(DIRS.values()), rnd.randint(1, 3)):
        ax = "x" if dx else "z"
        # the cell just outside the trunk (size 2 = a 2x2 trunk at x..x+1, z..z+1) on that side
        rx = x + (size if dx > 0 else -1) if dx else x + rnd.randint(0, size - 1)
        rz = z + (size if dz > 0 else -1) if dz else z + rnd.randint(0, size - 1)
        gl = ground_y(b, rx, rz)
        if gl == g and _free(b, rx, g + 1, rz) and rnd.random() < 0.6: b.set(rx, g + 1, rz, log(wood, ax))  # a flare
        elif gl <= g and _sh(b.get(rx, gl, rz)) in SOIL: b.set(rx, gl, rz, log(wood, ax))  # a root in the ground
        fx, fz = rx + dx, rz + dz
        gl2 = ground_y(b, fx, fz)
        if rnd.random() < 0.5 and _sh(b.get(fx, gl2, fz)) in SOIL: b.set(fx, gl2, fz, log(wood, ax))
    if soil:
        for dx in range(-2, 2 + size):
            for dz in range(-2, 2 + size):
                if rnd.random() < 0.45:
                    gl = ground_y(b, x + dx, z + dz)
                    if _sh(b.get(x + dx, gl, z + dz)) in ("grass_block", "dirt"):
                        b.set(x + dx, gl, z + dz, rnd.choice(("minecraft:rooted_dirt", "minecraft:rooted_dirt", "minecraft:coarse_dirt")))


def _prune(b, x, z, y0, y1, R=7):
    """Drop leaves that touch nothing by a face (lone corner leaves read as floating bits)."""
    for px in range(x - R, x + R + 1):
        for pz in range(z - R, z + R + 1):
            for py in range(y0, y1 + 1):
                s = b.blocks.get((px, py, pz))
                if s and "leaves" in s and not any(not _free(b, px + dx, py + dy, pz + dz) for dx, dy, dz in
                                                     ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))):
                    b.blocks.pop((px, py, pz))


def tree2(b, x, z, kind="oak", h=None, rnd=None):
    """A tree that is not a lollipop: a leaning or forked trunk, 1-2 side branches from about 60 % up, 2-4
    overlapping leaf clusters of different sizes on the branch ends with 15 % of the outer leaves left out, and root
    flares in rooted dirt. Kinds: oak, birch, spruce, dark_oak, cherry, jungle, acacia, mangrove, pale_oak, azalea.
    Stands on ground_y(x, z). Returns the top y."""
    import random as _r
    rnd = rnd or _r.Random(x * 7919 + z * 104729)
    wood, lv, (h0, h1) = TREE[kind]
    h = h or rnd.randint(h0, h1)
    g = ground_y(b, x, z)
    f = {"spruce": _spruce, "dark_oak": _dark_oak, "acacia": _acacia}.get(kind, _broadleaf)
    top = crown_guard(b, lambda: f(b, x, g, z, h, rnd, kind) if f is _broadleaf else f(b, x, g, z, h, rnd))
    if top is None: return None
    _prune(b, x, z, g, top + 2)
    return top


def crown_guard(b, grow, share=0.33):
    """Run grow() (a tree writing into b) and take back every cell it put where a tree may not go: within 1 of a house
    box townkit registered (leaves in a wall or a bedroom), or under something already built above it (a room, an
    eave, a porch roof). When that is more than `share` of the tree, none of it is planted (a crown cut in half reads
    worse than no tree). Returns grow()'s result, or None when the tree was taken out."""
    log, _set = {}, b.set
    def rec(x, y, z, s, data=None):
        k = (int(x), int(y), int(z))
        if k not in log: log[k] = b.blocks.get(k)
        _set(x, y, z, s, data)
    b.set = rec
    try: top = grow()
    finally: del b.set
    if not log: return top
    boxes = [h["box"] for h in getattr(b, "_tk_houses", ())]
    lo = min(q[1] for q in log)
    def before(q): return log[q] if q in log else b.blocks.get(q)
    cover = {}
    def roofed(q):
        c = (q[0], q[2])
        if c not in cover:  # lowest block built over this column before the tree (not another tree's crown)
            cover[c] = next((yy for yy in range(lo, lo + 40) if before((q[0], yy, q[2])) and before((q[0], yy, q[2])) != AIR
                             and not _free(b, q[0], yy, q[2]) and "leaves" not in before((q[0], yy, q[2])) and "_log" not in before((q[0], yy, q[2]))
                             and _sh(before((q[0], yy, q[2]))) not in GROUND), None)
        return cover[c] is not None and cover[c] > q[1]
    bad = [q for q in log if any(bx[0] - 1 <= q[0] <= bx[2] + 1 and bx[1] - 1 <= q[2] <= bx[3] + 1 for bx in boxes) or roofed(q)]
    for q in (log if len(bad) > share * len(log) else bad):
        if log[q] is None: b.blocks.pop(q, None)
        else: b.blocks[q] = log[q]
    return None if len(bad) > share * len(log) else top


def _broadleaf(b, x, g, z, h, rnd, kind):
    """Oak, birch, cherry, jungle, mangrove, pale oak, azalea: trunk (leaning, forked, on prop roots), branches, crowns."""
    wood, lv, _ = TREE[kind]
    leaf = leaves(lv); y0 = g + 1
    lean = rnd.choice(list(DIRS.values()))
    big = kind == "jungle" and h >= 11
    # trunk
    trunk = []; cx, cz = x, z
    shifts = {"oak": 2, "birch": 1, "cherry": 1, "jungle": 1, "mangrove": 1, "pale_oak": 1, "azalea": 1}[kind] if rnd.random() < 0.65 else 0
    base = y0
    if kind == "mangrove":  # the trunk stands on arching prop roots
        base = y0 + 2
        for (dx, dz) in rnd.sample(DIAG, rnd.randint(3, 5)):
            d = 2
            ex, ez = x + dx * d, z + dz * d
            ge = ground_y(b, ex, ez)
            pts = _walk((x + dx, base, z + dz), (ex, base - 1, ez)) + _walk((ex, base - 1, ez), (ex, ge + 1, ez))[1:]
            for p in pts: _put(b, *p, "minecraft:mangrove_roots")
            if _sh(b.get(ex, ge, ez)) in SOIL: b.set(ex, ge, ez, "minecraft:muddy_mangrove_roots")
        for yy in range(y0, base): _put(b, x, yy, z, "minecraft:mangrove_roots")
    fork = kind == "cherry" or kind in ("oak", "pale_oak") and rnd.random() < 0.4
    trunk_h = int(h * (0.55 if fork else 1.0)) if kind != "cherry" else h - 3
    at = sorted(rnd.sample(range(max(2, int(trunk_h * 0.4)), max(3, trunk_h)), min(shifts, max(0, trunk_h - 3)))) if shifts else []
    for i in range(trunk_h):
        yy = base + i
        if i in at:
            trunk.append((cx, yy, cz)); cx, cz = cx + lean[0], cz + lean[1]
        trunk.append((cx, yy, cz))
    _logs(b, trunk, wood)
    if big:
        for (dx, dz) in ((1, 0), (0, 1), (1, 1)):
            _logs(b, [(p[0] + dx, p[1], p[2] + dz) for p in trunk], wood)
    top = trunk[-1]
    ends = []  # (point, radius): one leaf cluster per branch end
    side = [d for d in DIAG if d != (-lean[0], -lean[1])]
    if fork:  # the trunk splits at about 55 % into 2 (cherry 2-3) limbs going up and out
        for d in rnd.sample(side, 2) if kind != "cherry" else rnd.sample(DIAG, rnd.randint(2, 3)):
            L, up = (rnd.randint(2, 3), rnd.randint(2, 3)) if kind != "cherry" else (rnd.randint(3, 4), rnd.randint(1, 2))
            e = (top[0] + d[0] * L, top[1] + up, top[2] + d[1] * L)
            _logs(b, _walk(top, e), wood); ends.append((e, rnd.uniform(2.2, 3.0) if kind != "cherry" else rnd.uniform(2.4, 2.9)))
        if kind != "cherry" and rnd.random() < 0.7: ends.append(((top[0], top[1] + 3, top[2]), rnd.uniform(1.6, 2.2)))
    else:
        r_main = {"birch": rnd.uniform(2.0, 2.4), "jungle": rnd.uniform(3.4, 4.0), "mangrove": rnd.uniform(3.0, 3.4), "azalea": 2.0}.get(kind, rnd.uniform(2.5, 3.1))
        ends.append(((top[0], top[1] + (1 if kind != "birch" else 0), top[2]), r_main))
        if kind in ("oak", "pale_oak", "birch", "mangrove"):  # a second, smaller cluster beside the top: a lopsided crown
            d = rnd.choice(side); ends.append(((top[0] + d[0] * 2, top[1] - 1, top[2] + d[1] * 2), r_main * 0.7))
        nb = {"birch": rnd.randint(0, 1), "jungle": rnd.randint(3, 4), "azalea": 0, "mangrove": 2}.get(kind, rnd.randint(1, 2))
        lo, hi = (0.45, 0.85) if kind == "jungle" else (0.5, 0.7)
        for d in rnd.sample(side, nb):
            p = trunk[max(1, int(len(trunk) * rnd.uniform(lo, hi)))]
            L = rnd.randint(2, 3) if kind != "birch" else 1
            e = (p[0] + d[0] * L, p[1] + rnd.randint(1, 2), p[2] + d[1] * L)
            _logs(b, _walk(p, e), wood); ends.append((e, rnd.uniform(1.5, 2.2) if kind != "jungle" else rnd.uniform(1.6, 2.3)))
    crown = []
    for (e, r) in ends:
        if kind == "birch": crown += _blob(b, e[0], e[1], e[2], r * 0.85, r * 1.35, rnd, leaf, down=r * 1.1)
        elif kind == "cherry": crown += _blob(b, e[0], e[1] + 1, e[2], r, r * 0.6, rnd, leaf, down=r * 0.4, droop=0.5, holes=0.22)
        elif kind == "jungle": crown += _blob(b, e[0], e[1], e[2], r, r * 0.6, rnd, leaf, down=r * 0.45, droop=0.15)
        elif kind == "mangrove": crown += _blob(b, e[0], e[1], e[2], r, r * 0.75, rnd, leaf, down=r * 0.55, droop=0.15)
        else: crown += _blob(b, e[0], e[1], e[2], r, r * 0.7, rnd, leaf, down=r * 0.6)
    crown = [p for p in crown if b.blocks.get(p) == leaf]
    if kind == "azalea":  # flowering patches through the crown
        for p in crown:
            if rnd.random() < 0.3: b.blocks[p] = leaves("flowering_azalea")
    if kind in ("jungle", "mangrove"): _hang_vines(b, crown, rnd, 0.1 if kind == "jungle" else 0.03)
    if kind == "jungle":  # cocoa pods on the trunk
        for p in rnd.sample(trunk[1:-2], min(2, max(0, len(trunk) - 3))):
            for f, (dx, dz) in rnd.sample(list(DIRS.items()), 4):
                q = (p[0] + dx, p[1], p[2] + dz)
                if _free(b, *q) and q not in b.blocks:
                    b.set(*q, f"minecraft:cocoa[age=2,facing={OPP[f]}]"); break
    if kind == "mangrove":
        for (px, py, pz) in crown:
            if (px, py - 1, pz) not in b.blocks and rnd.random() < 0.06:
                b.set(px, py - 1, pz, "minecraft:mangrove_propagule[age=4,hanging=true,stage=0,waterlogged=false]")
    else:
        _roots(b, x, g, z, wood, rnd, size=2 if big else 1)
    return top[1] + 3


def _hang_vines(b, cells, rnd, p):
    """Vines on the outside faces of a crown, hanging 1-4 down (each stuck to a leaf or the vine above it)."""
    for (lx, ly, lz) in cells:
        for f, (dx, dz) in DIRS.items():
            q = (lx + dx, ly, lz + dz)
            if q not in b.blocks and rnd.random() < p:
                for k in range(rnd.randint(1, 4)):
                    if (q[0], q[1] - k, q[2]) in b.blocks: break
                    b.set(q[0], q[1] - k, q[2], _vine(OPP[f]))


def _spruce(b, x, g, z, h, rnd):
    """A spruce with uneven tiers: rings that widen and narrow down the trunk, each side a little different."""
    leaf = leaves("spruce"); y0 = g + 1
    _logs(b, [(x, y0 + i, z) for i in range(h)], "spruce")
    R = rnd.uniform(2.6, 3.4) * h / 11
    first = rnd.randint(2, 3)
    seed = rnd.randint(0, 9999)
    for i in range(first, h + 1):
        t = (i - first) / max(1, h - first)
        r = R * (1 - t) ** 0.9 + 0.6
        if (h - i) % 2 == 1: r *= 0.62  # the tier steps: wide, narrow, wide
        for dx in range(-4, 5):
            for dz in range(-4, 5):
                jit = 0.75 + 0.5 * noise2(dx + i * 1.7, dz - i * 2.3, seed, 1.5)
                if math.hypot(dx, dz) <= r * jit and not (dx == dz == 0):
                    if rnd.random() < 0.08 and math.hypot(dx, dz) > r * 0.6: continue
                    _put(b, x + dx, y0 + i, z + dz, leaf)
    _put(b, x, y0 + h, z, leaf); _put(b, x, y0 + h + 1, z, leaf)
    _roots(b, x, g, z, "spruce", rnd)
    for dx in range(-2, 3):  # podzol under it
        for dz in range(-2, 3):
            gl = ground_y(b, x + dx, z + dz)
            if _sh(b.get(x + dx, gl, z + dz)) == "grass_block" and rnd.random() < 0.5: b.set(x + dx, gl, z + dz, "minecraft:podzol[snowy=false]")
    return y0 + h + 1


def _dark_oak(b, x, g, z, h, rnd):
    """A 2x2 dark oak: thick trunk with corner roots, branches spreading near the top, a wide flat crown."""
    leaf = leaves("dark_oak"); y0 = g + 1
    for dx, dz in ((0, 0), (1, 0), (0, 1), (1, 1)):
        gl = ground_y(b, x + dx, z + dz)
        _logs(b, [(x + dx, yy, z + dz) for yy in range(gl + 1, y0 + h)], "dark_oak")
    top = y0 + h - 1
    ends = [((x, top + 1, z), rnd.uniform(3.6, 4.4))]
    for (dx, dz) in rnd.sample(DIAG, rnd.randint(2, 4)):
        L = rnd.randint(2, 3)
        sx, sz = x + (1 if dx > 0 else 0), z + (1 if dz > 0 else 0)
        sy = top - rnd.randint(1, 2)
        e = (sx + dx * L, sy + rnd.randint(1, 2), sz + dz * L)
        _logs(b, _walk((sx, sy, sz), e), "dark_oak"); ends.append((e, rnd.uniform(2.2, 2.8)))
    for (e, r) in ends: _blob(b, e[0], e[1], e[2], r, r * 0.45, rnd, leaf, down=r * 0.35)
    _roots(b, x, g, z, "dark_oak", rnd, size=2)
    return top + 3


def _acacia(b, x, g, z, h, rnd):
    """An acacia: a short trunk that bends off sideways in one or two arms, each ending in a flat two-layer crown."""
    leaf = leaves("acacia"); y0 = g + 1
    bend = rnd.randint(2, 3)
    stem = [(x, y0 + i, z) for i in range(bend)]
    _logs(b, stem, "acacia")
    arms = rnd.sample(DIAG, 2 if rnd.random() < 0.6 else 1)
    tops = []
    for k, (dx, dz) in enumerate(arms):
        L = h - bend - (1 if k else 0)
        p = stem[-1]; pts = []
        for i in range(1, L + 1):
            q = (p[0] + (dx if i <= 3 else 0), p[1] + 1, p[2] + (dz if i <= 3 else 0))
            pts += _walk(p, q)[1:]; p = q
        _logs(b, pts, "acacia"); tops.append(p)
    for i, (tx, ty, tz) in enumerate(tops):
        r = rnd.uniform(2.6, 3.3) if i == 0 else rnd.uniform(2.0, 2.5)
        seed = rnd.randint(0, 9999)
        for dx in range(-4, 5):
            for dz in range(-4, 5):
                d = math.hypot(dx, dz) * (0.85 + 0.3 * noise2(dx, dz, seed, 1.6))
                if d <= r and rnd.random() > 0.1: _put(b, tx + dx, ty + 1, tz + dz, leaf)
                if d <= r - 1.3: _put(b, tx + dx, ty + 2, tz + dz, leaf)
    _roots(b, x, g, z, "acacia", rnd, soil=False)
    return max(t[1] for t in tops) + 2


def palm(b, x, z, h=None, lean=None, rnd=None):
    """A palm with a curved trunk (1 block over every 2-3 up, all one way, bending more near the top) and drooping
    fronds of jungle leaves, with cocoa pods under the crown for coconuts. lean: north/south/east/west or None."""
    import random as _r
    rnd = rnd or _r.Random(x * 31 + z * 17)
    h = h or rnd.randint(7, 11)
    lean = lean or rnd.choice(list(DIRS))
    dx, dz = DIRS[lean]
    g = ground_y(b, x, z)
    cx, cz, pts = x, z, []
    nxt = rnd.randint(2, 3)
    for i in range(h):
        yy = g + 1 + i
        if i == nxt:
            pts.append((cx, yy, cz)); cx, cz = cx + dx, cz + dz
            nxt = i + (3 if i < h * 0.45 else 2)
        pts.append((cx, yy, cz))
    _logs(b, pts, "jungle")
    tx, ty, tz = pts[-1]
    leaf = leaves("jungle")
    _put(b, tx, ty + 1, tz, leaf)
    for (fx, fz) in DIAG:  # fronds: out level for 1-2, then droop ever faster, the tip hanging down
        prof = (1, 0, -1, -2, -3)[: rnd.randint(3, 4)] if fx and fz else (1, 1, 0, -1, -2, -3)[: rnd.randint(4, 6)]
        px, py, pz = tx, ty + 1, tz
        for i, dy in enumerate(prof, 1):
            nx, nz, ny = tx + fx * i, tz + fz * i, ty + dy
            # out first, then down: every leaf touches the one before by a face, so the frond is one piece
            if fx and fz: _put(b, px + fx, py, pz, leaf)
            for yy in range(py, ny, -1): _put(b, nx, yy, nz, leaf)
            _put(b, nx, ny, nz, leaf); px, py, pz = nx, ny, nz
        if rnd.random() < 0.6: _put(b, px, py - 1, pz, leaf)  # the tip hangs
    cy = ty - 1 if _sh(b.get(tx, ty - 1, tz)) == "jungle_log" else ty
    for f, (ox, oz) in rnd.sample(list(DIRS.items()), rnd.randint(2, 3)):
        q = (tx + ox, cy, tz + oz)
        if q not in b.blocks: b.set(*q, f"minecraft:cocoa[age=2,facing={OPP[f]}]")
    _prune(b, tx, tz, ty - 6, ty + 2)
    return ty + 1


# ------------------------------------------------------------------ planting
FLOWERS = ("poppy", "dandelion", "cornflower", "oxeye_daisy", "azure_bluet", "allium", "red_tulip", "orange_tulip", "white_tulip",
           "pink_tulip", "lily_of_the_valley", "blue_orchid")


def _soil_top(b, x, z):
    """(y, block) of the ground if it is soil with room above, else None."""
    g = ground_y(b, x, z)
    s = b.get(x, g, z)
    if _sh(s) not in SOIL or not _free(b, x, g + 1, z) or (x, g + 1, z) in b.blocks and b.blocks[(x, g + 1, z)] != AIR \
            and not _sh(b.blocks[(x, g + 1, z)]) in ("short_grass",): return None
    return g


def _plant(b, x, z, s, rnd=None):
    """Put one plant (or a 2-high tall plant, given by its id without half) on soil at the column's ground."""
    g = _soil_top(b, x, z)
    if g is None: return False
    sh = _sh(s)
    if sh in ("tall_grass", "large_fern", "rose_bush", "lilac", "peony", "sunflower"):
        if (x, g + 2, z) in b.blocks and b.blocks[(x, g + 2, z)] != AIR: return False
        b.set(x, g + 1, z, f"minecraft:{sh}[half=lower]"); b.set(x, g + 2, z, f"minecraft:{sh}[half=upper]")
    elif sh in ("pink_petals", "wildflowers"):
        b.set(x, g + 1, z, f"minecraft:{sh}[facing={rnd.choice(FACING)},flower_amount={rnd.randint(1, 4)}]")
    elif sh == "leaf_litter":
        b.set(x, g + 1, z, f"minecraft:leaf_litter[facing={rnd.choice(FACING)},segment_amount={rnd.randint(1, 4)}]")
    else: b.set(x, g + 1, z, s)
    return True


def flower_clump(b, x, z, flower, rnd, n=None, r=2):
    """3-7 of one flower round (x, z): one colour per clump reads as planted, one of each reads as noise. Never on a
    door's apron (flowers there get trampled, and block the way in pictures)."""
    for _ in range(n or rnd.randint(3, 7)):
        px, pz = x + rnd.randint(-r, r), z + rnd.randint(-r, r)
        if not near_door(b, px, ground_y(b, px, pz) + 1, pz): _plant(b, px, pz, "minecraft:" + flower, rnd)


def bush(b, x, z, rnd, leaf=None):
    """A leafy bush 1-2 high on the ground (persistent leaves), sometimes two cells wide."""
    leaf = leaf or leaves(rnd.choice(("oak", "oak", "azalea", "dark_oak")))
    g = _soil_top(b, x, z)
    if g is None or near_door(b, x, g + 1, z): return
    b.set(x, g + 1, z, leaf)
    if rnd.random() < 0.5: _put(b, x, g + 2, z, leaf)
    d = rnd.choice(list(DIRS.values()))
    if rnd.random() < 0.6 and _soil_top(b, x + d[0], z + d[1]) == g: b.set(x + d[0], g + 1, z + d[1], leaf)


def grove(b, pts_or_area, kind, rnd, n=None, avoid=None, under=True):
    """A stand of 3-5 trees with one dominant (tallest, first kind if kind is a tuple), the others smaller and
    leaning out round it, not in a line; then the understory: bushes, ferns, short and tall grass, a one-colour
    flower clump, moss carpet, and leaf litter or pink petals under the crowns. pts_or_area: [(x, z), ...] or
    (x0, z0, x1, z1). kind may be "palm". avoid(x, z) -> True keeps cells (paths, plazas) clear. Returns the
    tree positions."""
    kinds = (kind,) if isinstance(kind, str) else tuple(kind)
    avoid = avoid or (lambda x, z: False)
    if len(pts_or_area) == 4 and all(isinstance(v, int) for v in pts_or_area):
        x0, z0, x1, z1 = pts_or_area
        n = n or rnd.randint(3, 5)
        gap = 6.5 if set(kinds) & {"acacia", "dark_oak", "cherry", "palm", "jungle"} else 5.0 if "spruce" in kinds else 4.2  # wide crowns need room
        pts = [(rnd.randint(x0 + (x1 - x0) // 4, x1 - (x1 - x0) // 4), rnd.randint(z0 + (z1 - z0) // 4, z1 - (z1 - z0) // 4))]
        tries = 0
        while len(pts) < n and tries < 200:
            tries += 1
            a = rnd.random() * math.tau; d = rnd.uniform(gap, gap + 3.5)
            p = (round(pts[0][0] + math.cos(a) * d), round(pts[0][1] + math.sin(a) * d))
            if not (x0 <= p[0] <= x1 and z0 <= p[1] <= z1) or avoid(*p): continue
            if all(math.hypot(p[0] - q[0], p[1] - q[1]) >= gap for q in pts): pts.append(p)
    else:
        pts = list(pts_or_area)
    placed = []
    for i, (x, z) in enumerate(pts):
        k = kinds[0] if i == 0 else rnd.choice(kinds)
        if _soil_top(b, x, z) is None and _sh(b.get(x, ground_y(b, x, z), z)) not in ("sand", "red_sand"): continue
        if k == "palm":
            palm(b, x, z, rnd.randint(10, 12) if i == 0 else rnd.randint(7, 9), None, rnd)
        else:
            h0, h1 = TREE[k][2]
            tree2(b, x, z, k, h1 + rnd.randint(0, 1) if i == 0 else rnd.randint(h0, max(h0, h1 - 2)), rnd)
        placed.append((x, z, k))
    if not under or not placed: return placed
    cx = sum(p[0] for p in placed) / len(placed); cz = sum(p[1] for p in placed) / len(placed)
    R = 4 + max(math.hypot(p[0] - cx, p[1] - cz) for p in placed)
    seed = rnd.randint(0, 9999)
    ks = {p[2] for p in placed}
    litter = "pink_petals" if "cherry" in ks else "leaf_litter" if ks & {"oak", "birch", "dark_oak", "pale_oak"} else None
    dry = ks & {"acacia", "palm"}
    for dx in range(-int(R), int(R) + 1):
        for dz in range(-int(R), int(R) + 1):
            x, z = round(cx + dx), round(cz + dz)
            d = math.hypot(dx, dz) / R
            if d > 1 or avoid(x, z): continue
            r = rnd.random(); m = noise2(x, z, seed, 3.5)
            if m < 0.28 and not dry and d < 0.8:
                g = _soil_top(b, x, z)
                if g is not None and rnd.random() < 0.6: _plant(b, x, z, "minecraft:moss_carpet")
                continue
            if litter and m > 0.62 and d < 0.75 and r < 0.55: _plant(b, x, z, "minecraft:" + litter, rnd); continue
            if r < 0.10: _plant(b, x, z, "minecraft:short_dry_grass" if dry else "minecraft:short_grass")
            elif r < 0.15: _plant(b, x, z, "minecraft:tall_grass" if not dry else "minecraft:tall_dry_grass")
            elif r < 0.20 and not dry: _plant(b, x, z, "minecraft:fern")
            elif r < 0.215 and not dry: _plant(b, x, z, "minecraft:large_fern")
    for _ in range(rnd.randint(2, 3) if not dry else 1):  # bushes at the edge of the crowns
        a = rnd.random() * math.tau
        bush(b, round(cx + math.cos(a) * R * 0.7), round(cz + math.sin(a) * R * 0.7), rnd,
             leaves("acacia") if dry else None)
    if not dry:
        a = rnd.random() * math.tau
        fx, fz = round(cx + math.cos(a) * R * 0.8), round(cz + math.sin(a) * R * 0.8)
        if not avoid(fx, fz): flower_clump(b, fx, fz, rnd.choice(("lily_of_the_valley", "allium", "cornflower", "oxeye_daisy") if "cherry" not in ks else ("pink_tulip", "allium", "white_tulip")), rnd)
    return placed


def meadow(b, x0, z0, x1, z1, rnd, density=0.10, clumps=None, avoid=None, flowers=FLOWERS):
    """Open grass: short and tall grass in drifts (noise, not even speckle) and a few one-colour flower clumps."""
    avoid = avoid or (lambda x, z: False)
    seed = rnd.randint(0, 9999)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if avoid(x, z): continue
            m = noise2(x, z, seed, 5)
            if rnd.random() < density * (0.3 + 1.6 * m):
                _plant(b, x, z, "minecraft:tall_grass" if m > 0.65 and rnd.random() < 0.3 else "minecraft:short_grass")
    for _ in range(clumps if clumps is not None else max(1, (x1 - x0) * (z1 - z0) // 160)):
        x, z = rnd.randint(x0, x1), rnd.randint(z0, z1)
        if not avoid(x, z): flower_clump(b, x, z, rnd.choice(flowers), rnd)


# ------------------------------------------------------------------ paths
EDGE = ("minecraft:coarse_dirt", "minecraft:coarse_dirt", "minecraft:gravel", "minecraft:rooted_dirt", "minecraft:packed_mud")
STREET = (("minecraft:stone_bricks", 32), ("minecraft:cobblestone", 20), ("minecraft:andesite", 18), ("minecraft:polished_andesite", 12),
          ("minecraft:mossy_stone_bricks", 7), ("minecraft:cracked_stone_bricks", 6), ("minecraft:gravel", 3), ("minecraft:mossy_cobblestone", 2))
STREET_EDGE = ("minecraft:cobblestone", "minecraft:cobblestone", "minecraft:gravel", "minecraft:andesite", "minecraft:coarse_dirt")
PAVABLE = {"grass_block", "dirt", "coarse_dirt", "podzol", "rooted_dirt", "moss_block", "sand", "red_sand", "gravel", "mud", "packed_mud",
           "dirt_path", "stone", "andesite", "tuff", "snow_block", "mycelium"}


def _catmull(pts, step=0.35):
    """Points along a Catmull-Rom curve through the control points (a path that bends, not a polyline)."""
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        n = max(1, int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / step))
        for k in range(n):
            t = k / n; t2 = t * t; t3 = t2 * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(tuple(pts[-1]))
    return out


def organic_path(b, pts, w, rnd, mid="minecraft:dirt_path", edge=EDGE, street=False, step=None, grass=0.25, wobble=None):
    """A path through control points that bends smoothly, wobbles sideways by about a block every 4-6, varies in
    width by +-1 and follows the ground (ground_y per cell). The middle is `mid` (or the STREET stone mix when
    street=True), the edges a broken mix of `edge` with `grass` of them left as grass; where it climbs 1 block a
    stair of `step` (spruce log steps on trails, stone brick on streets) makes the step. wobble: sideways swing in
    blocks (default 1.2, streets 0.6). Built cells are never paved over.
    Returns {(x, z): y} of the paved cells."""
    seed = rnd.randint(0, 9999)
    curve = _catmull(pts)
    best = {}  # cell -> (d / half width, along)
    s_along = 0.0
    for i, (px, pz) in enumerate(curve):
        if i: s_along += math.hypot(px - curve[i - 1][0], pz - curve[i - 1][1])
        a = curve[min(i + 1, len(curve) - 1)]; c = curve[max(i - 1, 0)]
        tx, tz = a[0] - c[0], a[1] - c[1]; L = math.hypot(tx, tz) or 1
        nx, nz = -tz / L, tx / L
        off = (noise2(s_along, 0, seed, 5) - 0.5) * 2 * (wobble if wobble is not None else 0.6 if street else 1.2)
        hw = max(0.7, w / 2 + (noise2(s_along, 3, seed + 1, 7) - 0.5) * 2.2)
        cx, cz = px + nx * off, pz + nz * off
        for dx in range(-int(hw) - 2, int(hw) + 3):
            for dz in range(-int(hw) - 2, int(hw) + 3):
                X, Z = round(cx) + dx, round(cz) + dz
                d = math.hypot(X - cx, Z - cz) / hw
                if d <= 1.0 and d < best.get((X, Z), (9,))[0]: best[(X, Z)] = (d, s_along)
    # mid: one block, or [(block, weight), ...] mixed by weight (street=True with a plain mid uses the STREET mix)
    mids = list(STREET) if street and isinstance(mid, str) else [(mid, 1)] if isinstance(mid, str) else list(mid)
    edge = STREET_EDGE if street and edge is EDGE else edge
    step = step or ("minecraft:stone_brick" if street else "minecraft:spruce")
    tot = sum(wt for _, wt in mids)
    def pick_mid():
        r = rnd.random() * tot
        for s, wt in mids:
            r -= wt
            if r <= 0: return s
        return mids[0][0]
    done = {}
    for (x, z), (d, _) in best.items():
        g = ground_y(b, x, z)
        if _sh(b.get(x, g, z)) not in PAVABLE: continue
        above = b.blocks.get((x, g + 1, z))
        if above and not _free(b, x, g + 1, z): continue
        is_edge = d > 0.62 and w >= 2 or d > 0.9
        if is_edge:
            if rnd.random() < grass: done[(x, z)] = g; continue
            s = rnd.choice(edge)
        else:
            s = pick_mid() if street or len(mids) > 1 else (mids[0][0] if rnd.random() > 0.1 else rnd.choice(edge))
        b.set(x, g, z, s)
        for k in (1, 2):
            q = b.blocks.get((x, g + k, z))
            if q and any(t in q for t in PLANT): b.blocks.pop((x, g + k, z))
        done[(x, z)] = g
    # a stair where the path climbs one block, facing the higher cell (mossy now and then on dirt paths)
    for (x, z), g in list(done.items()):
        for f, (dx, dz) in DIRS.items():
            if done.get((x + dx, z + dz)) == g + 1 and _free(b, x, g + 1, z) and (x, g + 1, z) not in b.blocks:
                st = step if street or rnd.random() > 0.2 else "minecraft:mossy_cobblestone"
                b.set(x, g + 1, z, stairs(st + "_stairs", f))
                break
    return done


def pave(b, cells, rnd, street=True, mid="minecraft:dirt_path", edge=None, grass=0.2):
    """Pave a plaza or yard of any shape (a set of (x, z)) at each cell's ground: the stone mix (or `mid`) inside,
    a broken edge of cobble and gravel with some grass left on the outline. Returns {(x, z): y}."""
    cells = set(cells)
    edge = edge or (STREET_EDGE if street else EDGE)
    tot = sum(w for _, w in STREET)
    done = {}
    for (x, z) in cells:
        g = ground_y(b, x, z)
        if _sh(b.get(x, g, z)) not in PAVABLE or not _free(b, x, g + 1, z): continue
        rim = any((x + dx, z + dz) not in cells for dx, dz in DIRS.values())
        if rim and rnd.random() < grass: continue
        if rim: s = rnd.choice(edge)
        elif street:
            r = rnd.random() * tot
            for s, w in STREET:
                r -= w
                if r <= 0: break
        else: s = mid
        b.set(x, g, z, s)
        for k in (1, 2):
            q = b.blocks.get((x, g + k, z))
            if q and any(t in q for t in PLANT): b.blocks.pop((x, g + k, z))
        done[(x, z)] = g
    return done


# ------------------------------------------------------------------ the lived-in layer
def near_door(b, x, y, z, r=2):
    """True when a door (not a trapdoor) stands within r of (x, z) at about height y: its apron stays clear."""
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            for yy in (y - 1, y, y + 1):
                s = b.blocks.get((x + dx, yy, z + dz))
                if s and "_door[" in s and "half=lower" in s: return True
    return False


def _at(b, x, z):
    """y to stand a prop on at (x, z): one above the ground, or None if the cell is taken or in front of a door."""
    g = ground_y(b, x, z)
    return g + 1 if _free(b, x, g + 1, z) and not near_door(b, x, g + 1, z) else None


def _stand(b, x, z, s):
    y = _at(b, x, z)
    if y is not None: b.set(x, y, z, s)
    return y


def clutter(b, x, z, facing, kind, rnd):
    """One lived-in prop at (x, z), its front toward `facing` (its back to a house wall if there is one). Kinds:
    crates (barrels, a chest under a trapdoor, hay, stacked 1-3), woodpile, cart, washing_line, bench, trough, pots,
    fishing, camp. Every block stands on the ground (ground_y per cell) or on another block of the prop.
    Returns False when the spot has no room for it (a washing line or bench is never built by halves)."""
    dx, dz = DIRS[facing]; sx, sz = (1, 0) if dz else (0, 1)
    opp = OPP
    along = "x" if sx else "z"
    if kind == "crates":
        for i in range(rnd.randint(2, 3)):
            px, pz = x + sx * i, z + sz * i
            s = rnd.choice(("minecraft:barrel[facing=up,open=false]", "minecraft:barrel[facing=up,open=false]", "chest",
                            "minecraft:hay_block[axis=y]", "minecraft:barrel[facing=" + facing + ",open=false]"))
            if s == "chest":
                y = _stand(b, px, pz, f"minecraft:chest[facing={facing},type=single,waterlogged=false]")
                if y: _put(b, px, y + 1, pz, trapdoor("minecraft:spruce_trapdoor", facing, "bottom"))
                continue
            y = _stand(b, px, pz, s)
            if y and rnd.random() < 0.5: _put(b, px, y + 1, pz, rnd.choice(("minecraft:barrel[facing=up,open=false]", s)))
            if y and rnd.random() < 0.25 and _free(b, px, y + 2, pz) and _sh(b.get(px, y + 1, pz)) == "barrel":
                b.set(px, y + 2, pz, lantern())
    elif kind == "woodpile":  # logs on their side, a long row with a shorter row on top and a slab lid
        wood = rnd.choice(("spruce", "oak", "birch"))
        n = rnd.randint(3, 4)
        for i in range(n):
            y = _stand(b, x + sx * i, z + sz * i, log(wood, "x" if dz else "z") if rnd.random() < 0.8 else log("stripped_" + wood, "x" if dz else "z"))
            if y and 0 < i < n - 1 + (rnd.random() < 0.5): _put(b, x + sx * i, y + 1, z + sz * i, log(wood, "x" if dz else "z"))
        _stand(b, x + sx * n, z + sz * n, "minecraft:" + ("oak" if wood != "spruce" else "spruce") + "_slab[type=bottom,waterlogged=false]") if rnd.random() < 0.5 else None
    elif kind == "cart":  # a bed of top slabs on two trapdoor wheels, a shaft at the front, a load on the back
        wood = "spruce"
        bed = [(x, z), (x - dx, z - dz)]
        ys = [_at(b, *c) for c in bed]
        if None in ys: return False
        y = max(ys)
        for (cx, cz) in bed:
            b.set(cx, y, cz, slab(f"minecraft:{wood}_slab", "top"))
            foundation_cells(b, [(cx, cz)], y, "minecraft:dirt", depth=2)
        for sgn in (1, -1):
            wx, wz = bed[1][0] + sx * sgn, bed[1][1] + sz * sgn
            f = [k for k, v in DIRS.items() if v == (sx * sgn, sz * sgn)][0]
            _put(b, wx, y, wz, trapdoor("minecraft:oak_trapdoor", f, "bottom", "true"))
        _put(b, x + dx, y, z + dz, fence(wood))
        _put(b, bed[1][0], y + 1, bed[1][1], rnd.choice(("minecraft:hay_block[axis=y]", "minecraft:barrel[facing=up,open=false]", "minecraft:pumpkin")))
        if rnd.random() < 0.5: _put(b, x, y + 1, z, "minecraft:barrel[facing=up,open=false]")
    elif kind == "washing_line":  # two posts, a fence line on top, sheets hung from the line (each touches it)
        L = rnd.randint(4, 6)
        a, c = (x, z), (x + sx * L, z + sz * L)
        ga, gc = ground_y(b, *a), ground_y(b, *c)
        ytop = max(ga, gc) + 3
        if any(not _free(b, x + sx * i, yy, z + sz * i) for i in range(L + 1) for yy in range(ground_y(b, x + sx * i, z + sz * i) + 1, ytop + 1)) \
                or any(near_door(b, x + sx * i, ga + 1, z + sz * i) for i in (0, L)):
            return False  # never half a line: both posts and the whole run must have room
        for (px, pz), g in ((a, ga), (c, gc)):
            for yy in range(g + 1, ytop + 1): _put(b, px, yy, pz, fence("spruce"))
        cloth = ("white_wool", "white_wool", "light_blue_wool", "light_gray_wool", "yellow_wool", "pink_wool", "red_wool")
        for i in range(1, L):
            px, pz = x + sx * i, z + sz * i
            _put(b, px, ytop, pz, fence("spruce"))
            if rnd.random() < 0.75:
                c2 = "minecraft:" + rnd.choice(cloth)
                _put(b, px, ytop - 1, pz, c2)
                if rnd.random() < 0.3 and ground_y(b, px, pz) < ytop - 3: _put(b, px, ytop - 2, pz, c2)
        _stand(b, x + dx, z + dz, "minecraft:barrel[facing=up,open=false]") if rnd.random() < 0.5 else None
    elif kind == "bench":  # stairs as the seat (back to the wall), trapdoor arms
        n = rnd.randint(2, 3)
        ys = [_at(b, x + sx * i, z + sz * i) for i in range(n)]
        if None in ys: return False
        y = min(ys)
        for i in range(n): b.set(x + sx * i, y, z + sz * i, stairs("minecraft:spruce_stairs", opp[facing]))
        for (ex, ez, f) in ((x - sx, z - sz, [k for k, v in DIRS.items() if v == (-sx, -sz)][0]),
                            (x + sx * n, z + sz * n, [k for k, v in DIRS.items() if v == (sx, sz)][0])):
            if _at(b, ex, ez) == y: b.set(ex, y, ez, trapdoor("minecraft:spruce_trapdoor", f, "bottom", "true"))
    elif kind == "trough":  # water cauldrons in a row with hay beside, a post with a lantern
        for i in range(2):
            _stand(b, x + sx * i, z + sz * i, "minecraft:water_cauldron[level=3]")
        _stand(b, x + sx * 2, z + sz * 2, "minecraft:hay_block[axis=y]")
        y = _stand(b, x - sx, z - sz, fence("oak"))
        if y: _put(b, x - sx, y + 1, z - sz, lantern())
    elif kind == "pots":
        for i in range(rnd.randint(2, 3)):
            px, pz = x + sx * i, z + sz * i + (dz if i == 1 else 0) * 0
            s = rnd.choice((f"minecraft:decorated_pot[cracked=false,facing={facing},waterlogged=false]",
                            "minecraft:potted_" + rnd.choice(("red_tulip", "fern", "azalea_bush", "cornflower", "dandelion")),
                            f"minecraft:decorated_pot[cracked={rnd.choice(('true', 'false'))},facing={facing},waterlogged=false]"))
            if s.startswith("minecraft:potted_"):
                y = _stand(b, px, pz, "minecraft:barrel[facing=up,open=false]")
                if y: _put(b, px, y + 1, pz, s)
            else: _stand(b, px, pz, s)
    elif kind == "fishing":  # barrels and kelp, a net rack (open trapdoor hung on the post), a lantern on the post
        _stand(b, x, z, "minecraft:barrel[facing=up,open=false]")
        y = _stand(b, x + sx, z + sz, "minecraft:dried_kelp_block")
        if y and rnd.random() < 0.5: _put(b, x + sx, y + 1, z + sz, "minecraft:barrel[facing=up,open=false]")
        y = _stand(b, x + sx * 2, z + sz * 2, fence("spruce"))
        if y:
            _put(b, x + sx * 2, y + 1, z + sz * 2, fence("spruce")); _put(b, x + sx * 2, y + 2, z + sz * 2, lantern())
            _put(b, x + sx * 2 + dx, y + 1, z + sz * 2 + dz, trapdoor("minecraft:spruce_trapdoor", facing, "top", "true"))
    elif kind == "camp":  # a campfire ringed with log seats
        y = _stand(b, x, z, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
        if not y: return False
        for (ox, oz) in rnd.sample(list(DIRS.values()), 3):
            _stand(b, x + ox * 2, z + oz * 2, log("spruce", "x" if oz else "z"))
    return True


def lamp_post(b, x, z, rnd, style="wood"):
    """A lamp on a post standing on the ground. styles: wood (fence post, lantern on top), hanging (taller post with
    an arm and a lantern hanging under it), stone (cobble wall foot, fence, lantern), street (stone brick wall
    column on a polished andesite plinth)."""
    g = ground_y(b, x, z); y = g + 1
    if not _free(b, x, y, z): return
    if style == "hanging":
        h = rnd.randint(4, 5)
        for yy in range(y, y + h): b.set(x, yy, z, fence("dark_oak"))
        ax, az = rnd.choice(list(DIRS.values()))
        _put(b, x + ax, y + h - 1, z + az, fence("dark_oak"))
        _put(b, x + ax, y + h - 2, z + az, lantern(True))
        _put(b, x, y + h, z, slab("minecraft:dark_oak_slab", "bottom"))
    elif style == "stone":
        b.set(x, y, z, wall("minecraft:cobblestone_wall"))
        for yy in (y + 1, y + 2): b.set(x, yy, z, fence("spruce"))
        _put(b, x, y + 3, z, lantern())
    elif style == "street":
        b.set(x, y, z, "minecraft:polished_andesite")
        for yy in (y + 1, y + 2): b.set(x, yy, z, wall("minecraft:stone_brick_wall"))
        _put(b, x, y + 3, z, lantern())
    else:
        for yy in range(y, y + 3): b.set(x, yy, z, fence(rnd.choice(("spruce", "dark_oak"))))
        _put(b, x, y + 3, z, lantern())
