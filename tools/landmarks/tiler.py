"""Splits one big canvas into a grid of jigsaw tiles and writes everything the game needs:

  data/onepiece/structure/<id>/t_<i>_<j>.nbt         one template per tile (full height of the build)
  data/onepiece/worldgen/template_pool/<id>.json      start pool -> the middle tile
  data/onepiece/worldgen/template_pool/<id>/t_<i>_<j>.json   one pool per other tile
  data/onepiece/worldgen/structure/<id>.json          jigsaw size and max distance updated (other fields kept)

Neighbouring tiles are linked by pairs of jigsaw blocks on their shared face (a spanning tree grown from the
middle tile), so the game rebuilds the exact picture. Each jigsaw is replaced by the block that belongs there.
"""
import json, os, shutil
from collections import deque
import canvas as C

RES = "/mnt/project-files/one-piece-mod/source/src/main/resources/data/onepiece"
DIRS = {(1, 0): ("east", "west"), (-1, 0): ("west", "east"), (0, 1): ("south", "north"), (0, -1): ("north", "south")}


ASSETS = os.path.join(os.path.dirname(RES.rstrip("/")), "..", "assets", "onepiece")
FULL_PARENTS = ("block/cube_all", "block/cube", "block/cube_column", "block/cube_column_horizontal", "block/cube_bottom_top",
                "block/cube_top", "block/cube_mirrored_all", "block/cube_mirrored", "block/orientable", "block/orientable_vertical",
                "block/orientable_with_bottom", "block/cube_directional", "block/cube_north_west_mirrored_all", "block/leaves",
                "block/cube_column_uv_locked_x", "block/cube_column_uv_locked_y", "block/cube_column_uv_locked_z",
                "block/cube_column_mirrored", "block/cube_bottom_top_inner_faces")
_OP_FULL = {}


def _model_full(model, depth=0):
    """True if a block model (onepiece: or minecraft:) is a plain full cube: its parent chain ends in a cube model."""
    if depth > 8 or not model: return False
    ns, _, path = model.partition(":") if ":" in model else ("minecraft", "", model)
    if ns == "minecraft": return path in FULL_PARENTS
    f = os.path.join(ASSETS, "models", path + ".json")
    try: m = json.load(open(f))
    except (OSError, ValueError): return False
    if "elements" in m: return False
    return _model_full(m.get("parent"), depth + 1)


def op_full(name):
    """onepiece: blocks are full cubes only when their model really is one. render.shape_of() calls any block it
    doesn't know "full", so cloud moss, cloud puffs and shrubs counted as solid and the island cloud under them was
    culled: in the sky that left hollow islands with see-through holes under the moss (ryan 2026-11-02)."""
    if name not in _OP_FULL:
        full = False
        try:
            bs = json.load(open(os.path.join(ASSETS, "blockstates", name.split(":")[1] + ".json")))
            if "variants" in bs:
                vs = [v if isinstance(v, dict) else v[0] for v in bs["variants"].values()]
                full = bool(vs) and all(_model_full(v.get("model")) for v in vs)
        except (OSError, ValueError, IndexError):
            full = False
        _OP_FULL[name] = full
    return _OP_FULL[name]


def cull_hidden(b):
    """Drop solid blocks buried on all six sides by other solid blocks: nobody can see them, and the world's own
    ground fills those spots anyway. Saves a lot of memory and file size on cliffs and foundations."""
    import render
    from finish import FURN
    # furniture is never a full cube: a floor block under a counter or table must stay, or at sea the world's water
    # takes its place and the furniture pops off as an item when the structure generates (Foosha's bar counters)
    full = {p for p, s in b.blocks.items() if render.shape_of(s) == "full" and s.split("[")[0] not in render.SKIP
            and not any(k in s for k in ("glass", "leaves", "ice", "slime", "honey", "spawner", "chest", "barrel", "lantern", "jigsaw"))
            and s.split("[")[0].split(":")[-1] not in FURN
            and (not s.startswith("onepiece:") or op_full(s.split("[")[0]))}
    out = {}
    for p, s in b.blocks.items():
        if p in full and p not in b.nbt:
            x, y, z = p
            above = b.blocks.get((x, y + 1, z), "")
            falls = any(k in above for k in ("sand", "gravel", "concrete_powder")) and "sandstone" not in above
            if not falls and all(n in full for n in ((x + 1, y, z), (x - 1, y, z), (x, y + 1, z), (x, y - 1, z), (x, y, z + 1), (x, y, z - 1))):
                continue  # (a block holding up sand or gravel is kept, or the sand would fall where the world has water or caves)
        out[p] = s
    return out


def write(sid, b, ground_y, tile=48, res=RES, heightmap=None, terrain=None, biomes=None, sky_y=None, liquid=None):
    """sky_y: build floats at a fixed world height (canvas ground_y lands on world y sky_y), no heightmap."""
    """ground_y = canvas y that should sit on the world surface block (land: top grass block; sea: top water block)."""
    # sky builds float over open air: a culled block there leaves a hollow the player can dig or look into, not the
    # world's ground, so they keep every block (solid cloud islands)
    pts = cull_hidden(b) if sky_y is None or sky_y < 100 else dict(b.blocks)
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; zs = [p[2] for p in pts]
    minx, maxx, miny, maxy, minz, maxz = min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)
    # grid centred on the middle of the build, so the start tile sits in the middle and holds real content
    ccx = (minx + maxx) // 2; ccz = (minz + maxz) // 2
    gx = ccx - tile // 2; gz = ccz - tile // 2
    gx -= -(-(gx - minx) // tile) * tile; gz -= -(-(gz - minz) // tile) * tile
    nx = (maxx - gx) // tile + 1; nz = (maxz - gz) // tile + 1
    def tid(x, z): return ((x - gx) // tile, (z - gz) // tile)
    tiles = {}
    for p, s in pts.items(): tiles.setdefault(tid(p[0], p[2]), {})[p] = s
    # bridge holes so the grid is connected: include every cell in the bounding grid
    cells = {(i, j) for i in range(nx) for j in range(nz)}
    for c in cells: tiles.setdefault(c, {})
    start = tid(ccx, ccz)
    parent = {start: None}; depth = {start: 0}; q = deque([start]); order = []
    while q:
        c = q.popleft(); order.append(c)
        for d in DIRS:
            n = (c[0] + d[0], c[1] + d[1])
            if n in cells and n not in parent:
                parent[n] = (c, d); depth[n] = depth[c] + 1; q.append(n)
    # drop empty leaf cells that nothing hangs from (keeps piece count low)
    used = {c for c in cells if tiles[c]}
    keep = set()
    for c in used:
        while c is not None and c not in keep:
            keep.add(c); c = parent[c][0] if parent[c] else None
    out_dir = os.path.join(res, "structure", sid)
    pool_dir = os.path.join(res, "worldgen", "template_pool", sid)
    for d in (out_dir, pool_dir):
        if os.path.isdir(d): shutil.rmtree(d)
        os.makedirs(d)
    jig = {c: [] for c in keep}  # (pos, facing, name, target, pool, final)
    jused = set()  # one jigsaw per block: two links must never share a corner block
    for c in keep:
        if parent[c] is None: continue
        pc, d = parent[c]
        face_p, face_c = DIRS[d]
        # parent's edge column and child's first column
        if d[0]:
            ex = gx + (pc[0] + (1 if d[0] > 0 else 0)) * tile - (1 if d[0] > 0 else 0)
            cx = ex + d[0]
            span = [(y, z) for y in range(miny, maxy + 1) for z in range(gz + c[1] * tile, gz + c[1] * tile + tile)]
            P = lambda y, z: (ex, y, z); Q = lambda y, z: (cx, y, z)
        else:
            ez = gz + (pc[1] + (1 if d[1] > 0 else 0)) * tile - (1 if d[1] > 0 else 0)
            cz = ez + d[1]
            span = [(y, x) for y in range(miny, maxy + 1) for x in range(gx + c[0] * tile, gx + c[0] * tile + tile)]
            P = lambda y, x: (x, y, ez); Q = lambda y, x: (x, y, cz)
        best = None
        for (u, v) in span:
            a, bb = pts.get(P(u, v)), pts.get(Q(u, v))
            if (v - (gz if d[0] else gx)) % tile in (0, tile - 1) or P(u, v) in jused or Q(u, v) in jused: continue
            if a is not None and bb is not None and (P(u, v) not in b.nbt) and (Q(u, v) not in b.nbt):
                score = (a == C.AIR) + (bb == C.AIR)  # prefer air/air, then anything
                if best is None or score > best[0]: best = (score, u, v)
                if score == 2: break
        if best is None:
            lo, hi = (minz, maxz) if d[0] else (minx, maxx)  # keep the link inside the build's footprint
            u, v = maxy + 1, min(max(span[len(span) // 2][1], lo + 1), hi - 1)
            while P(u, v) in jused or Q(u, v) in jused: v += 1
        else:
            u, v = best[1], best[2]
        pp, qp = P(u, v), Q(u, v)
        jused.update((pp, qp))
        pool = f"onepiece:{sid}/t_{c[0]}_{c[1]}"
        link = f"onepiece:{sid}_{c[0]}_{c[1]}"  # unique per child, so only its own incoming jigsaw can match
        jig[pc].append((pp, face_p, "onepiece:out", link, pool, pts.get(pp, C.AIR)))
        jig[c].append((qp, face_c, link, "minecraft:empty", "minecraft:empty", pts.get(qp, C.AIR)))
    max_depth = 0; total = 0
    ent_by_tile = {}
    for e in b.entities:
        ent_by_tile.setdefault(tid(e[1], e[3]), []).append(e)
    starts = {}
    for c in keep:
        t = C.B()
        for p, s in tiles[c].items():
            t.set(*p, s, b.nbt.get(p))
        for (p, face, name, target, pool, final) in jig[c]:
            t.set(*p, f"minecraft:jigsaw[orientation={face}_up]",
                  {"id": "minecraft:jigsaw", "name": name, "target": target, "pool": pool, "final_state": final, "joint": "rollable"})
        t.entities = ent_by_tile.get(c, [])
        if not t.blocks: t.set(gx + c[0] * tile, maxy + 1, gz + c[1] * tile, C.AIR)
        t.save(os.path.join(out_dir, f"t_{c[0]}_{c[1]}.nbt"))
        tys = [p[1] for p in t.blocks]; starts[c] = min(tys)
        total += 1; max_depth = max(max_depth, depth[c])
        if c != start:
            json.dump({"fallback": "minecraft:empty", "elements": [{"weight": 1, "element": {
                "element_type": "minecraft:single_pool_element", "location": f"onepiece:{sid}/t_{c[0]}_{c[1]}",
                "processors": {"processors": []}, "projection": "rigid"}}]},
                open(os.path.join(pool_dir, f"t_{c[0]}_{c[1]}.json"), "w"), indent=2)
    json.dump({"fallback": "minecraft:empty", "elements": [{"weight": 1, "element": {
        "element_type": "minecraft:single_pool_element", "location": f"onepiece:{sid}/t_{start[0]}_{start[1]}",
        "processors": {"processors": []}, "projection": "rigid"}}]},
        open(os.path.join(res, "worldgen", "template_pool", f"{sid}.json"), "w"), indent=2)  # noqa
    old = os.path.join(res, "structure", f"{sid}.nbt")
    if os.path.exists(old): os.remove(old)
    # structure json
    sp = os.path.join(res, "worldgen", "structure", f"{sid}.json")
    sj = json.load(open(sp if os.path.exists(sp) else os.path.join(RES, "worldgen", "structure", f"{sid}.json")))
    os.makedirs(os.path.dirname(sp), exist_ok=True)
    sx0 = gx + start[0] * tile; sz0 = gz + start[1] * tile
    scx = sx0 + tile // 2; scz = sz0 + tile // 2
    reach = max(maxx - scx, scx - minx, maxz - scz, scz - minz) + 2
    sj["size"] = max(1, max_depth)
    # horizontal limit is 128, minus 12 when the terrain is adapted; vertical reach counts from the start piece bottom
    hlim = 128 if (terrain or sj.get("terrain_adaptation", "none")) == "none" else 116
    sj["max_distance_from_center"] = {"horizontal": min(hlim, reach), "vertical": maxy - miny + 8}
    if reach > hlim: print(f"WARNING {sid}: reach {reach} > {hlim}, outer tiles may be cut")
    # world y of the start template's lowest block: heightmap gives the first free block above the surface. The game
    # then sets the piece one lower than that (StructurePoolElement.getGroundLevelDelta() == 1), so add the 1 back:
    # without it every build sat a block too deep and a harbour at sea level had the sea one block above its quay.
    if sky_y is not None:
        sj["start_height"] = {"absolute": sky_y + (starts[start] - ground_y) + 1}
        sj.pop("project_start_to_heightmap", None)
    else:
        sj["start_height"] = {"absolute": -(ground_y - starts[start])}
    if heightmap: sj["project_start_to_heightmap"] = heightmap
    if terrain: sj["terrain_adaptation"] = terrain
    if biomes: sj["biomes"] = biomes
    # land builds keep their own block states: with the default (apply_waterlogging) every fence, slab, wall or lamp that
    # lands where the world had sea water turns into a water source and floods the plaza around it
    if liquid: sj["liquid_settings"] = liquid
    json.dump(sj, open(sp, "w"), indent=2)
    return dict(tiles=total, depth=max_depth, size=(maxx - minx + 1, maxy - miny + 1, maxz - minz + 1), reach=reach)
