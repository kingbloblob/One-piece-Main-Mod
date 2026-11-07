"""Bridge between the Minecraft Builder skill (mcbig.BigBuild + mcparts) and the landmark pipeline (canvas.B).

New designs are drawn with the skill's BigBuild (numpy voxels, vectorised shapes, roofs, arches, interiors with
PropTracker/audit_props), then to_canvas() copies them into a canvas.B so the unchanged pipeline (finish pass,
soft edges, tiler, jigsaw tiles, NPC/loot markers) writes the mod's structure files. Carved air stays air."""
import os, sys
import numpy as np

SKILL = os.environ.get("MCB_SKILL") or next(
    (os.path.join(r, d, "minecraft-builder", "scripts") for r in ("/root/.claude/skills/synced",)
     if os.path.isdir(r) for d in sorted(os.listdir(r))
     if os.path.isdir(os.path.join(r, d, "minecraft-builder", "scripts"))), None)
HERE = os.path.dirname(os.path.abspath(__file__))
# a vendored copy of the skill scripts keeps the build reproducible on machines without the skill installed
for p in (os.path.join(HERE, "skill"), SKILL):
    if p and os.path.isdir(p) and p not in sys.path: sys.path.insert(0, p)

from mcbig import BigBuild, T  # noqa: E402,F401
import mcparts as P  # noqa: E402,F401

# 26.3 renamed / dropped ids the skill still emits
RENAME = {"minecraft:chain": "minecraft:iron_chain", "minecraft:grass": "minecraft:short_grass"}


def _fix(s):
    base, sep, st = s.partition("[")
    base = RENAME.get(base, base)
    if base.endswith("_leaves") and "persistent=" not in st:     # bare leaves decay and drop saplings when the build generates
        st = (st[:-1] + ",persistent=true]") if st else "persistent=true]"
        sep = "["
    return base + sep + st


def to_canvas(bb, b=None, dx=0, dy=0, dz=0):
    """Copy every painted voxel of BigBuild `bb` into canvas B `b` (made if None), shifted by (dx, dy, dz)."""
    if b is None:
        from canvas import B
        b = B()
    names = [_fix(n) if n else n for n in bb.names]
    for (tx, tz), a in bb.tiles.items():
        xs, ys, zs = np.nonzero(a)
        for x, y, z in zip(xs.tolist(), ys.tolist(), zs.tolist()):
            b.blocks[(tx * T + x + dx, bb.y_min + y + dy, tz * T + z + dz)] = names[a[x, y, z]]
    return b


_KNOWN = None


def known_blocks():
    """Every block id the game knows: vanilla blockstates from the client jar assets + the mod's blockstates."""
    global _KNOWN
    if _KNOWN is None:
        _KNOWN = set()
        roots = [(os.environ.get("MC_ASSETS", "/root/mc/client/assets"), "minecraft"),
                 (os.environ.get("MOD_ASSETS", "/mnt/project-files/one-piece-mod/source/src/main/resources/assets"), None)]
        for root, only in roots:
            if not os.path.isdir(root):
                continue
            for ns in os.listdir(root):
                if only and ns != only:
                    continue
                d = os.path.join(root, ns, "blockstates")
                if os.path.isdir(d):
                    _KNOWN |= {f"{ns}:{f[:-5]}" for f in os.listdir(d) if f.endswith(".json")}
        _KNOWN |= {"minecraft:air", "minecraft:cave_air", "minecraft:void_air", "minecraft:water", "minecraft:lava"}
    return _KNOWN


def check_ids(b):
    """Block ids in a canvas that the game doesn't have (they'd turn into air or purple in game)."""
    kn = known_blocks()
    if len(kn) < 500:
        return []
    bad = sorted({s.split("[")[0] for s in b.blocks.values()} - kn)
    return bad
