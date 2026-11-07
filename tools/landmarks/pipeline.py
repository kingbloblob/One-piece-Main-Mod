"""prepare(sid): build one landmark and run the finishing pass, exactly as make.py writes it (tests use this too)."""
import importlib
import finish
from canvas import AIR, WATER

MODS = {"baratie": "baratie", "arlong_park": "arlong_park", "moby_dick": "moby_dick", "alubarna_palace": "alubarna",
        "galley_la_dock": "water7", "tower_of_justice": "enies_lobby", "thriller_bark": "thriller_bark", "marineford": "marineford",
        "ryugu_palace": "ryugu", "onigashima": "onigashima", "whole_cake_chateau": "whole_cake"}
CLEAR = 24  # land builds: air this high over the whole site, so hills and overhangs never cover a town


def mode_of(m):
    opts = getattr(m, "TILER", {})
    return getattr(m, "FINISH_MODE", None) or (
        "seafloor" if opts.get("heightmap") == "OCEAN_FLOOR_WG" else "cave" if opts.get("sky_y", 999) < 100 else
        "sky" if "sky_y" in opts else "sea" if getattr(m, "WATER_Y", None) is not None else "land")


def clear_above(b, h=CLEAR):
    cols = {}
    for (x, y, z) in b.blocks:
        if y == 0: cols[(x, z)] = True
    n = 0
    for (x, z) in cols:
        for y in range(1, h + 1):
            if (x, y, z) not in b.blocks: b.blocks[(x, y, z)] = AIR; n += 1
    return n


GROUND = {"grass_block", "dirt", "podzol", "sand", "red_sand", "snow_block", "snow", "mycelium", "rooted_dirt", "moss_block",
          "mud", "sandstone", "red_sandstone", "terracotta", "clay", "packed_mud", "powder_snow"}
PLANT = ("short_grass", "tall_grass", "fern", "large_fern", "dandelion", "poppy", "flower", "tulip", "orchid", "allium",
         "bluet", "daisy", "cornflower", "lily_of_the_valley", "bush", "dead_bush", "sweet_berry", "petals", "sapling",
         "mushroom", "leaf_litter", "wildflowers", "cactus", "sugar_cane", "seagrass", "snow[")


def _short(s):
    return s.split("[")[0].split(":")[-1]


def _noise(x, z, seed, cell=11):
    """Smooth value noise in 0..1."""
    import math
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


def soften_edges(b, sid, keep=2, wobble=7, skirt=12, cut=8, reach=14):
    """Land builds used to sit on a square plate of ground with straight dirt walls, and to cut a square of air
    into any hill around them. This makes the edge look like ground, not a slab:
      1. bare ground (grass, dirt, sand... with only plants on it) further than keep + wobble*noise blocks from
         anything built is left out, so the outline is uneven and the world's own terrain shows there;
      2. round the new outline a skirt of ground steps down outwards (to y -skirt, steeper or gentler with the noise,
         up to `reach` blocks out), so where the world is lower the build sits on a rolling mound instead of a 4-high
         dirt wall;
      3. above the skirt, air from about y k+1 up (k = blocks out from the edge, up to `cut`), so where the world is
         higher a hill slopes down to the build instead of standing as a sheer wall.
    Returns the number of columns left out."""
    import collections
    seed = sum(map(ord, sid))
    cols = collections.defaultdict(dict)
    for (x, y, z), st in b.blocks.items():
        if -6 <= y <= 30: cols[(x, z)][y] = st
    def bare(c):
        ys = cols[c]
        top = ys.get(0)
        if top is None or _short(top) not in GROUND: return False
        for y, st in ys.items():
            sh = _short(st)
            if y < 0 and sh not in GROUND and sh not in ("stone", "gravel", "coarse_dirt"): return False
            if y >= 1 and sh not in ("air", "cave_air") and not any(k in st for k in PLANT): return False
        return True
    ground_cols = [c for c, ys in cols.items() if any(y <= 0 for y in ys)]
    built = [c for c in ground_cols if not bare(c)]
    if not built: return 0
    dist = {c: 0 for c in built}
    q = collections.deque(built)
    gset = set(ground_cols)
    while q:
        c = q.popleft()
        d = dist[c]
        if d > keep + wobble + 2: continue
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            n = (c[0] + dx, c[1] + dz)
            if n in gset and n not in dist:
                dist[n] = d + 1; q.append(n)
    dropped = 0
    for c in ground_cols:
        if c in dist and dist[c] <= keep + wobble * _noise(c[0], c[1], seed): continue
        if c not in dist or bare(c):
            for y in list(cols[c]):
                if y <= 1 or any(k in cols[c][y] for k in PLANT):
                    b.blocks.pop((c[0], y, c[1]), None)
            dropped += 1
    # the new outline: kept ground columns next to a column with no ground
    kept = {(x, z) for (x, y, z) in b.blocks if y == 0}
    def top_of(c):
        st = b.blocks.get((c[0], 0, c[1]), "minecraft:grass_block")
        sh = _short(st)
        if sh == "water": return WATER          # a bay or cove reaching the edge carries on as water, not a dam
        return st if sh in ("grass_block", "sand", "red_sand", "snow_block", "podzol", "mycelium", "moss_block") else "minecraft:grass_block"
    def under_of(top):
        return {"sand": "minecraft:sandstone", "red_sand": "minecraft:red_sandstone"}.get(_short(top), "minecraft:dirt")
    ring = {}
    frontier = {c: top_of(c) for c in kept if any((c[0] + dx, c[1] + dz) not in kept for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    seen = set(kept)
    for k in range(1, max(reach, cut) + 1):
        nxt = {}
        for c, top in frontier.items():
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (c[0] + dx, c[1] + dz)
                if n in seen: continue
                seen.add(n); nxt[n] = top; ring[n] = (k, top)
        frontier = nxt
    for (x, z), (k, top) in ring.items():
        if top == WATER:
            if k <= reach:
                d = min(skirt, 3 + k // 2)
                for y in range(-d, 1):
                    if (x, y, z) not in b.blocks: b.blocks[(x, y, z)] = WATER
                if (x, -d - 1, z) not in b.blocks: b.blocks[(x, -d - 1, z)] = "minecraft:sand"
                for y in range(1, CLEAR + 1):
                    if (x, y, z) not in b.blocks: b.blocks[(x, y, z)] = AIR
            continue
        slope = 0.45 + 1.1 * _noise(x, z, seed + 7, cell=7)  # blocks down per block out
        d = int(k * slope + 0.5)
        if 0 < d <= skirt and k <= reach:
            t = top if _noise(x, z, seed + 3, cell=3) > 0.18 else "minecraft:coarse_dirt"
            if (x, -d, z) not in b.blocks: b.blocks[(x, -d, z)] = t
            for y in range(-skirt - 1, -d):
                if (x, y, z) not in b.blocks: b.blocks[(x, y, z)] = under_of(top)
        h = int(k * (0.6 + 0.9 * _noise(x, z, seed + 11, cell=7)) + 0.5)
        if k <= cut:
            for y in range(max(1, h + 1), CLEAR + 1):
                if (x, y, z) not in b.blocks: b.blocks[(x, y, z)] = AIR
    return dropped


def load(sid):
    """The Minecraft Builder redesign in mcb/<id>.py wins over the older module, so a landmark switches over by
    adding its file there (delete it to go back)."""
    import os
    name = MODS.get(sid, sid)
    if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcb", sid + ".py")):
        return importlib.import_module("mcb." + sid)
    return importlib.import_module(name)


def prepare(sid, do_finish=True):
    m = load(sid)
    b, ground = m.build()
    mode = mode_of(m)
    rep = {}
    if do_finish:
        rep = finish.finish(b, mode, getattr(m, "SID", sid))
        # sites already at the jigsaw size cap set EDGE_REACH low so the ground skirt doesn't push them past it
        er = getattr(m, "EDGE_REACH", 14)
        if mode == "land" and getattr(m, "SOFT_EDGES", True):
            rep["edge columns left out"] = soften_edges(b, getattr(m, "SID", sid), skirt=min(12, er), cut=min(8, er), reach=er)
        if mode == "land" and getattr(m, "CLEAR_ABOVE", True): rep["air above"] = clear_above(b)
    return m, b, ground, mode, rep
