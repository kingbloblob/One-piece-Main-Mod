"""Checks shared with tools/underground/make_structures.py (that script runs on import, so the pieces live here)."""
import json, os

AIR = "minecraft:air"
_props = {}


def check_states(b, sid, assets):
    """Every onepiece: block must use property names its blockstate file knows (else the game drops the state)."""
    bad = set()
    for s in set(b.blocks.values()):
        if not s.startswith("onepiece:"):
            continue
        name = s.split("[")[0].split(":")[1]
        if name not in _props:
            p = os.path.join(assets, "blockstates", name + ".json")
            if not os.path.exists(p):
                _props[name] = None
            else:
                d = json.load(open(p)); keys = set()
                for v in (d.get("variants") or {}):
                    keys |= {kv.split("=")[0] for kv in v.split(",") if "=" in kv}
                for part in d.get("multipart", []):
                    w = part.get("when", {})
                    for c in (w.get("OR") or [w]):
                        keys |= set(c.keys())
                _props[name] = keys
        if _props[name] is None:
            bad.add(f"{s} (no such block)"); continue
        if "[" in s:
            for kv in s.split("[")[1].rstrip("]").split(","):
                if kv.split("=")[0] not in _props[name] and not kv.startswith("waterlogged"):
                    bad.add(f"{s} (unknown property {kv})")
    if bad:
        raise SystemExit(f"{sid}: bad block states:\n  " + "\n  ".join(sorted(bad)))


def cull_deep_factory(cull_hidden, keep=4):
    """Keep all rock within `keep` blocks of the build's air, drop only buried blocks further in."""
    def cull(b):
        hidden = cull_hidden(b)
        air = [p for p, v in b.blocks.items() if v in (AIR, "minecraft:cave_air") and p[1] < 0]
        near = set()
        for (x, y, z) in air:
            for dx in range(-keep, keep + 1):
                for dy in range(-keep, keep + 1):
                    for dz in range(-keep, keep + 1):
                        near.add((x + dx, y + dy, z + dz))
        return {p: s for p, s in b.blocks.items() if p in hidden or (p in near and p[1] < 0)}
    return cull


def steady(b):
    """Sand, gravel and concrete powder with nothing solid under them would fall when the chunk generates."""
    import render
    for (x, y, z), s in list(b.blocks.items()):
        n = s.split("[")[0]
        if n.endswith(("gravel", "sand", "concrete_powder")) and "sandstone" not in n:
            below = b.blocks.get((x, y - 1, z))
            if below is None or render.shape_of(below) != "full":
                b.blocks[(x, y, z)] = "minecraft:coarse_dirt" if "gravel" in n else "minecraft:smooth_sandstone" if "sand" in n else \
                    n.replace("concrete_powder", "concrete")
