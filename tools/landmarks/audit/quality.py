"""Build-quality audit (ryan's 2026-11-01 in-game review): counts, per landmark, the problems he saw.

    python3 audit/quality.py [sid ...] [--json=out.json] [--samples=3] [--raw]

--raw audits the build before the finishing pass (to see what the generators make on their own).
Checks:
  eave_gap      an open slot in a wall right under the roof (air with wall on both sides, roof above, wall below)
  trap_stool    a closed top-half trapdoor over an empty cell that stands on a floor (reads as a floating stool)
  chest_table   a chest used as a table or nightstand (candle / pot / lantern on it, or right beside a bed's pillow)
  bed_back      a bed whose pillow end is open while the foot end is against a wall
  bed_hole      a bed half with nothing solid under it
  pane_loose    a glass pane / bars with a solid neighbour it is not joined to, or joined to nothing at all
  helm_side     a ship's wheel that faces across the hull instead of along it
  door_blocked  a door with no standing room on one side (solid in the way, or a drop of 2+ with no step)
"""
import os, sys, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import pipeline, finish
from finish import nm, short, props, kind, top_sturdy, is_pane, is_wall, is_fence, AIRS

H4 = ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north"))
DV = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
TOPPERS = ("candle", "flower_pot", "potted_", "lantern", "skull", "head", "book_stack", "fruit_bowl", "bread_basket", "sake_set",
           "beer_mugs", "tea_set", "meat_platter", "candelabra", "decorated_pot")


def air(s):
    return s is None or nm(s) in AIRS


def solid(s):
    return s is not None and kind(s) in ("full", "glass")


def sturdy_side(s, toward):
    """Would a pane next to s (on side `toward` of s) join it in game? Full blocks, panes, walls, stairs backs."""
    if s is None or air(s): return False
    sh = short(s)
    if "leaves" in sh: return False  # the game never joins panes or bars to leaves
    if kind(s) in ("full", "glass") or is_pane(sh) or is_wall(sh): return True
    p = props(s)
    if sh.endswith("_stairs"): return p.get("facing") == toward  # the tall back of a stair faces `facing`
    if sh.endswith("_slab"): return p.get("type") == "double"
    return False


def roofish(s):
    if s is None or air(s): return False
    sh = short(s)
    return sh.endswith("_stairs") or sh.endswith("_slab") or kind(s) == "full"


def check(B):
    out = collections.defaultdict(list)
    G = B.get
    for p, s in B.items():
        if s is None: continue
        x, y, z = p
        sh = short(s) if ":" in s else s
        pr = props(s)
        if nm(s) in AIRS: continue
        if sh.endswith("trapdoor"):
            floor_round = sum(1 for dx, dz, _ in H4 if air(G((x + dx, y, z + dz))) and top_sturdy(G((x + dx, y - 1, z + dz))))
            if pr.get("half") == "top" and pr.get("open") == "false" and not air(G((x, y - 1, z))) and \
                    top_sturdy(G((x, y - 1, z))) and air(G((x, y + 1, z))) and floor_round >= 2:
                out["trap_stool"].append(p)
            elif pr.get("half") == "top" and pr.get("open") == "false" and air(G((x, y - 1, z))) and top_sturdy(G((x, y - 2, z))) \
                    and air(G((x, y + 1, z))):
                out["trap_stool_high"].append(p)
            continue
        if sh in ("chest", "trapped_chest"):
            above = G((x, y + 1, z))
            bedside = any("_bed[" in (G((x + dx, y, z + dz)) or "") and props(G((x + dx, y, z + dz))).get("part") == "head"
                          for dx, dz, _ in H4)
            if above and any(t in short(above) for t in TOPPERS) or bedside:
                out["chest_table"].append(p)
            continue
        if sh.endswith("_bed"):
            f = pr.get("facing", "north"); part = pr.get("part", "foot")
            if not top_sturdy(G((x, y - 1, z))) or kind(G((x, y - 1, z))) == "glass": out["bed_hole"].append(p)
            if part == "head":
                dx, dz = DV[f]
                foot = (x - dx, y, z - dz)
                beyond_head = G((x + dx, y, z + dz)); beyond_foot = G((foot[0] - dx, y, foot[2] - dz))
                if not solid(beyond_head) and solid(beyond_foot): out["bed_back"].append(p)
            continue
        if is_pane(sh):
            n_con = sum(1 for dx, dz, f in H4 if pr.get(f) == "true")
            loose = n_con == 0 and "glass" in sh
            for dx, dz, f in H4:
                if pr.get(f) != "true" and sturdy_side(G((x + dx, y, z + dz)), OPP[f]): loose = True
            if loose: out["pane_loose"].append(p)
            continue
        if sh == "ships_wheel":
            if "facing" not in pr: out["helm_side"].append(p)  # no facing = north whatever the ship's heading
            continue
        if sh.endswith("_door") and "trap" not in sh and pr.get("half") == "lower":
            for dx, dz, _ in H4:
                if pr.get("facing") not in (_, OPP[_]): continue
                c0, c1, c_1, c_2 = G((x + dx, y, z + dz)), G((x + dx, y + 1, z + dz)), G((x + dx, y - 1, z + dz)), G((x + dx, y - 2, z + dz))
                blocked = solid(c0) or solid(c1)
                drop = air(c_1) and air(c_2) and (x + dx, y - 1, z + dz) in B
                if blocked or drop:
                    out["door_blocked"].append(p); break
    # sea water laid at ground level (a harbour basin): such a build must sit at sea level, not on a hill
    w0 = [q for q, v in B.items() if q[1] == 0 and v and short(v) == "water"]
    if len(w0) > 40: out["harbour_water"] = w0[:3] + [None] * (len(w0) - 3)
    # eave holes: what finish.eaves() would still close
    f = finish.Finisher(type("V", (), {"blocks": dict(B)})(), "land", "", finish.STYLE_DEFAULT)
    f.eaves()
    if f.rep.get("eave gaps closed"):
        out["eave_hole"] = [q for q in f.B if f.B[q] != B.get(q)]
    return out


def sids():
    d = os.path.join(os.path.dirname(HERE), "..", "..", "src", "main", "resources", "data", "onepiece", "worldgen", "structure")
    return sorted(f[:-5] for f in os.listdir(d) if f.endswith(".json") and f[:-5] not in ("deep_trench",))


def run(sid, raw=False):
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        m, b, ground, mode, rep = pipeline.prepare(sid, not raw)
    return mode, check(b.blocks)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")] or sids()
    raw = "--raw" in sys.argv
    ns = int(next((a[10:] for a in sys.argv if a.startswith("--samples=")), 2))
    js = next((a[7:] for a in sys.argv if a.startswith("--json=")), None)
    allr, tot = {}, collections.Counter()
    for sid in args:
        try:
            mode, r = run(sid, raw)
        except Exception as e:
            print(sid, "ERROR", type(e).__name__, str(e)[:120], flush=True); continue
        allr[sid] = {k: v for k, v in r.items()}
        for k, v in r.items(): tot[k] += len(v)
        print(sid, mode, " ".join(f"{k}={len(v)}{v[:ns]}" for k, v in sorted(r.items())), flush=True)
    print("TOTAL", dict(tot))
    if js: json.dump(allr, open(js, "w"))
