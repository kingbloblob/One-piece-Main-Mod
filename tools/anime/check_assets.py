"""Catches purple/invisible blocks and items and broken animations before launching the game.
Checks the mod's assets (blockstate -> model -> parent -> texture, item definitions) and the built-in packs
(pack.mcmeta format, animated textures that lost their .png.mcmeta).
Usage: check_assets.py <mod resources folder>   e.g. check_assets.py src/main/resources
Exits with 1 and lists every problem if it finds any.
"""
import sys, os, re, json
from PIL import Image

RES = sys.argv[1]
ASSETS = os.path.join(RES, "assets")
problems = []

def split(ref):
    return ref.split(":", 1) if ":" in ref else ("minecraft", ref)

def model_file(ref):
    ns, p = split(ref)
    return ns, os.path.join(ASSETS, ns, "models", p + ".json")

def check_model(ref, src, seen=()):
    ns, path = model_file(ref)
    if ns == "minecraft" or ref in seen:
        return
    if not os.path.exists(path):
        problems.append(f"{src}: model {ref} is missing")
        return
    d = json.load(open(path))
    if "loader" in d:
        problems.append(f"{path}: has a Forge 'loader' field")
    parent = d.get("parent", "")
    if parent.startswith("builtin/"):
        problems.append(f"{path}: parent {parent} no longer exists")
    elif parent:
        check_model(parent, path, seen + (ref,))
    for t in (d.get("textures") or {}).values():
        if isinstance(t, str) and not t.startswith("#"):
            tns, tp = split(t)
            if tns != "minecraft" and not os.path.exists(os.path.join(ASSETS, tns, "textures", tp + ".png")):
                problems.append(f"{path}: texture {t} is missing")

for ns in sorted(os.listdir(ASSETS)):
    for kind in ("blockstates", "items"):
        folder = os.path.join(ASSETS, ns, kind)
        if not os.path.isdir(folder):
            continue
        for f in sorted(os.listdir(folder)):
            src = os.path.join(folder, f)
            for m in set(re.findall(r'"model"\s*:\s*"([^"]+)"', open(src).read())):
                check_model(m, src)
    # an item model nothing points at usually means a missing items/ definition (purple icon)
    models = os.path.join(ASSETS, ns, "models", "item")
    if os.path.isdir(models):
        used = set()
        for kind in ("items", "models"):
            for dp, _, fs in os.walk(os.path.join(ASSETS, ns, kind)):
                for f in fs:
                    used.update(re.findall(r'"([a-z0-9_.-]+:item/[a-z0-9_/.-]+)"', open(os.path.join(dp, f)).read()))
        for f in sorted(os.listdir(models)):
            n = f[:-5]
            if not os.path.exists(os.path.join(ASSETS, ns, "items", f)) and f"{ns}:item/{n}" not in used:
                problems.append(f"{ns}:item/{n}: no items/{f} definition points at it")

packs = os.path.join(RES, "resourcepacks")
for pack in sorted(os.listdir(packs)) if os.path.isdir(packs) else []:
    meta = os.path.join(packs, pack, "pack.mcmeta")
    p = json.load(open(meta))["pack"]
    if "min_format" not in p or "max_format" not in p:
        problems.append(f"{meta}: needs min_format and max_format")
    elif (p["min_format"][0] if isinstance(p["min_format"], list) else p["min_format"]) < 97:
        problems.append(f"{meta}: min_format is older than 26.3 (97)")
    for dp, _, fs in os.walk(os.path.join(packs, pack, "assets")):
        for f in fs:
            path = os.path.join(dp, f)
            if f.endswith(".png.mcmeta"):
                frames = json.load(open(path)).get("animation", {}).get("frames")
                if frames == []:
                    problems.append(f"{path}: empty frames list blacks out the atlas")
            elif f.endswith(".png") and "/textures/block/" in path.replace(os.sep, "/"):
                w, h = Image.open(path).size
                if h > w and h % w == 0 and not os.path.exists(path + ".mcmeta"):
                    problems.append(f"{path}: looks like an animation strip but has no .png.mcmeta")

for p in problems:
    print(p)
print(f"{len(problems)} problem(s)")
sys.exit(1 if problems else 0)
