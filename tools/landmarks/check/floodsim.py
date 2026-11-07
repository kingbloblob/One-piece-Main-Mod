"""floodsim.py sid...: like floodcheck.py but spreads water the way Minecraft does (sources and waterlogged blocks spread
7 blocks, falling water spreads again where it lands, flow heads for the nearest drop within 4 blocks, two sources make a
third). Prints flooded template-air cells per source kind and the entry cells (flooded cells right next to a source)."""
import sys, os, collections
LM = os.environ.get("LM_DIR", "/mnt/project-files/one-piece-mod/tools/landmarks")
sys.path.insert(0, LM)
os.chdir(LM)
import pipeline, tiler, finish

PASS_NAMES = ("torch", "flower", "short_grass", "tall_grass", "fern", "sapling", "rail", "button", "lever", "redstone_wire",
              "tripwire", "dead_bush", "vine", "snow[", "moss_carpet")
H = ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1))


def sim(pts, culled, S, apply_, bbox):
    x0, x1, z0, z1, y0, y1 = bbox

    def inside(p): return x0 <= p[0] <= x1 and z0 <= p[2] <= z1 and y0 <= p[1] <= y1

    def passable(p):
        s = pts.get(p)
        if s is None: return p not in culled
        if finish.kind(s) == "air": return True
        return any(k in s for k in PASS_NAMES)

    src = {}
    for p, s in pts.items():
        if finish.kind(s) == "water" and "cauldron" not in s: src[p] = "template water"
        elif "waterlogged=true" in s: src[p] = "waterlogged in template"
        elif apply_ and "waterlogged=false" in s and p[1] <= S: src[p] = "soaked up sea: " + s.split("[")[0]
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            for y in range(y0, S + 1):
                p = (x, y, z)
                if p not in pts and p not in culled: src.setdefault(p, "sea")
    amt = {p: 8 for p in src}; why = dict(src); source = set(src)
    q = collections.deque(src)

    def hole_dist(p, first):
        # distance (<=4) to a cell water can fall from, walking through passable cells, starting with step `first`
        seen = {p}; fr = [(first, 1)]
        while fr:
            c, d = fr.pop(0)
            if c in seen or not inside(c) or not passable(c) and c not in amt: continue
            seen.add(c)
            b = (c[0], c[1] - 1, c[2])
            if inside(b) and passable(b) and b not in source: return d
            if d < 4:
                for h in H: fr.append(((c[0] + h[0], c[1], c[2] + h[2]), d + 1))
        return 99

    def give(n, a, w):
        if n in source: return
        if amt.get(n, 0) >= a: return
        amt[n] = a; why[n] = w; q.append(n)

    while q:
        p = q.popleft(); a = amt[p]; w = why[p]
        below = (p[0], p[1] - 1, p[2])
        can_fall = inside(below) and passable(below) and below not in source
        if can_fall: give(below, 8, w)
        # Minecraft: flowing water only spreads sideways if it is a source or has no "water hole" under it, and water
        # already under it counts as one (a waterfall landing in a pool does not spill over the rim)
        if p not in source and (can_fall or below in amt): continue
        na = (7 if a >= 8 else a - 1) if p not in source else 7
        if na <= 0: continue
        opts = [(p[0] + h[0], p[1], p[2] + h[2]) for h in H]
        opts = [n for n in opts if inside(n) and passable(n)]
        if not opts: continue
        ds = {n: hole_dist(p, n) for n in opts}
        m = min(ds.values())
        for n in opts:
            if m == 99 or ds[n] == m: give(n, na, w)
    # two sources side by side over a solid block make a new source (only matters in corners and channels)
    flooded = collections.Counter(); ex = collections.defaultdict(list)
    for p, a in amt.items():
        if p in source or p not in pts: continue
        below = (p[0], p[1] - 1, p[2])
        if below in amt or below in source or (inside(below) and passable(below)): continue  # falling into a pool: a waterfall, fine
        flooded[why[p]] += 1  # water lying on a floor where the build wants air
        if any((p[0] + h[0], p[1], p[2] + h[2]) in source for h in H) or (p[0], p[1] + 1, p[2]) in source:
            if len(ex[why[p]]) < 8: ex[why[p]].append(p)
    return flooded, ex


def check(sid):
    m, b, ground, mode, rep = pipeline.prepare(sid)
    pts = tiler.cull_hidden(b)
    culled = set(b.blocks) - set(pts)
    if mode in ("sky", "cave"): return sid, mode, None
    ys = [p[1] for p in pts]; xs = [p[0] for p in pts]; zs = [p[2] for p in pts]
    S = ground if mode == "sea" else (max(ys) + 1 if mode == "seafloor" else 0)
    S += int(os.environ.get("FLOOD_S_OFFSET", "0"))
    apply_ = os.environ.get("FLOOD_APPLY") == "1"
    fl, ex = sim(pts, culled, S, apply_, (min(xs) - 1, max(xs) + 1, min(zs) - 1, max(zs) + 1, min(ys) - 1, max(ys) + 1))
    return sid, mode, S, sum(fl.values()), dict(fl), dict(ex)


if __name__ == "__main__":
    for sid in sys.argv[1:]:
        try: r = check(sid)
        except Exception as e:
            import traceback; traceback.print_exc(); r = (sid, "error", repr(e))
        print(r, flush=True)
