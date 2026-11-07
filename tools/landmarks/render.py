"""Isometric preview renderer for structure canvases (dict of (x,y,z) -> block state string).

Colors come from the real block textures (vanilla client jar assets + the mod's assets), averaged per face.
Usage from python: render(blocks, "out.png", view="se"|"nw", cut=None, scale=6)
"""
import json, math, os
import numpy as np
from PIL import Image

VANILLA = os.environ.get("MC_ASSETS", "/root/mc/client/assets")
MOD = os.environ.get("MOD_ASSETS", "/mnt/project-files/one-piece-mod/source/src/main/resources/assets")
ROOTS = [MOD, VANILLA, "/root/opbuild/src/main/resources/assets"]

TINT = {"grass": (145, 189, 89), "foliage": (90, 160, 50), "water": (63, 118, 228), "spruce": (97, 153, 97), "birch": (128, 167, 85)}
SKIP = {"minecraft:air", "minecraft:cave_air", "minecraft:structure_void", "minecraft:jigsaw", "minecraft:barrier", "minecraft:light"}
THIN = ("fence", "wall", "pane", "bars", "chain", "torch", "lantern", "flower", "sapling", "rose", "tulip", "poppy", "dandelion", "orchid",
        "allium", "bluet", "daisy", "cornflower", "lily_of", "bush", "fern", "grass", "bamboo", "sugar_cane", "candle", "rod", "ladder",
        "sign", "banner", "button", "lever", "vine", "sprout", "bloom", "lily", "lotus", "mushroom", "petals", "head", "skull", "flower_pot",
        "anchor", "cannon", "lamp", "sconce", "chandelier", "candelabra", "flower_box", "kingdom_flag", "jolly_roger", "chest", "cake", "bell", "pot", "campfire", "rail", "door", "trapdoor", "gate")
FLAT = ("carpet", "pressure_plate", "petals", "snow[", "rail", "lily_pad", "trapdoor")
NOT_THIN = ("block", "_planks", "grass_block", "tall_grass_block", "bricks", "_wood", "mushroom_block", "_stairs", "_slab", "dried_kelp", "bamboo_block",
            "bamboo_planks", "bamboo_mosaic", "_log", "wallpaper", "sandstone")

_cache = {}


def _find(rel):
    for r in ROOTS:
        p = os.path.join(r, rel)
        if os.path.exists(p): return p
    return None


def _model(ref, depth=0):
    ns, path = (ref.split(":", 1) if ":" in ref else ("minecraft", ref))
    p = _find(f"{ns}/models/{path}.json")
    if not p or depth > 8: return {}
    m = json.load(open(p))
    tex = {}
    if "parent" in m and not m["parent"].endswith("builtin/generated"):
        tex.update(_model(m["parent"], depth + 1))
    tex.update(m.get("textures", {}))
    return tex


def _tex_color(ref):
    if ref in _cache: return _cache[ref]
    ns, path = (ref.split(":", 1) if ":" in ref else ("minecraft", ref))
    p = _find(f"{ns}/textures/{path}.png")
    col = None
    if p:
        im = np.asarray(Image.open(p).convert("RGBA")).astype(float)
        h = im.shape[1]
        im = im[:h]  # first frame of animated textures
        a = im[..., 3:4] / 255.0
        if a.sum() > 0:
            col = tuple((im[..., :3] * a).sum(axis=(0, 1)) / a.sum())
    _cache[ref] = col
    return col


def _resolve(tex, key, seen=0):
    v = tex.get(key)
    if isinstance(v, dict): v = v.get("sprite")
    while v and v.startswith("#") and seen < 10:
        v = tex.get(v[1:]); seen += 1
        if isinstance(v, dict): v = v.get("sprite")
    return v


def block_colors(state):
    """(top rgb, side rgb) for a block state string, or None to skip."""
    if state in _cache: return _cache[state]
    name = state.split("[")[0]
    ns, path = name.split(":")
    out = None
    bs = _find(f"{ns}/blockstates/{path}.json")
    model = None
    if bs:
        j = json.load(open(bs))
        if "variants" in j:
            v = list(j["variants"].values())[0]
            model = (v[0] if isinstance(v, list) else v)["model"]
        elif "multipart" in j:
            a = j["multipart"][0]["apply"]
            model = (a[0] if isinstance(a, list) else a)["model"]
    tex = _model(model) if model else {}
    def pick(keys):
        for k in keys:
            r = _resolve(tex, k)
            if r:
                c = _tex_color(r)
                if c: return c
        return None
    top = pick(["top", "end", "up", "all", "texture", "cross", "plant", "pane", "rail", "fan", "side", "particle", "lantern", "bars", "edge", "wool", "flowerbed"])
    side = pick(["side", "north", "front", "all", "texture", "cross", "plant", "pane", "edge", "bars", "particle", "lantern", "top", "end", "wool"])
    if name in ("minecraft:water", "minecraft:bubble_column"):
        top = side = (63, 118, 228)
    if name == "minecraft:lava": top = side = (220, 100, 20)
    if top is None and side is None:
        top = side = (200, 0, 200)
    top = top or side; side = side or top
    def tint(c, t): return tuple(c[i] * t[i] / 255.0 * 1.15 for i in range(3))
    if name in ("minecraft:grass_block",):
        top = tint(top, TINT["grass"]); side = _tex_color("minecraft:block/dirt") or side
    elif "leaves" in name and not any(k in name for k in ("cherry", "azalea", "sakura", "gloom", "palm", "yarukiman")) and ns == "minecraft":
        t = TINT["spruce"] if "spruce" in name else TINT["birch"] if "birch" in name else TINT["foliage"]
        top = tint(top, t); side = tint(side, t)
    elif any(k in name for k in ("short_grass", "tall_grass", "fern", "vine", "lily_pad", "sugar_cane")) and ns == "minecraft":
        top = tint(top, TINT["grass"]); side = tint(side, TINT["grass"])
    out = (np.array(top), np.array(side))
    _cache[state] = out
    return out


def shape_of(state):
    name = state.split("[")[0]
    if name in ("minecraft:water", "minecraft:bubble_column"): return "water"
    if "_slab" in name and "type=double" not in state: return "slab_top" if "type=top" in state else "slab"
    if any(k in name for k in FLAT) and not any(k in name for k in NOT_THIN) or ("snow" in name and "layers" in state): return "flat"
    if any(k in name for k in THIN) and not any(k in name for k in NOT_THIN): return "thin"
    return "full"


def _masks(a):
    """Face masks for an iso cube with edge a: canvas (2a+1) x (2a+1+?)."""
    W = 2 * a; H = 2 * a
    yy, xx = np.mgrid[0:H, 0:W]
    # top face: diamond in rows 0..a
    cx = W / 2 - 0.5
    top = (np.abs(xx - cx) / a + np.abs(yy - (a / 2 - 0.5)) / (a / 2)) <= 1.0
    # left face (south, +z): parallelogram under the left half
    left = (xx < W / 2) & (yy >= (a / 2) + xx / 2 - 0.5 + 0) & (yy < (a / 2) + xx / 2 + a)
    left &= ~top
    right = (xx >= W / 2) & (yy >= (a / 2) + (W - 1 - xx) / 2 - 0.5) & (yy < (a / 2) + (W - 1 - xx) / 2 + a)
    right &= ~top
    return top, left, right


def render(blocks, out, view="se", cut=None, scale=6, water_y=None, title=None, bg=(206, 224, 236)):
    a = scale
    pts = {}
    for (x, y, z), s in blocks.items():
        if s.split("[")[0] in SKIP: continue
        if cut is not None and y > cut: continue
        if view == "nw": x, z = -x, -z
        elif view == "ne": x, z = -z, x
        elif view == "sw": x, z = z, -x
        pts[(x, y, z)] = s
    if not pts: return
    shapes = {p: shape_of(s) for p, s in pts.items()}
    def opaque(p): return shapes.get(p) == "full"
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; zs = [p[2] for p in pts]
    minx, maxx, miny, maxy, minz, maxz = min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)
    # screen coords: sx = (x - z) * a, sy = (x + z) * a/2 - y * a
    sxs = [(x - z) * a for x, y, z in pts]; sys_ = [(x + z) * a / 2 - y * a for x, y, z in pts]
    ox = -min(sxs) + 20; oy = -min(sys_) + 20 + (40 if title else 0)
    Wd = int(max(sxs) + ox + 2 * a + 20); Ht = int(max(sys_) + oy + 2 * a + 20)
    img = np.zeros((Ht, Wd, 3), dtype=float); img[:] = bg
    top, left, right = _masks(a)
    order = sorted(pts, key=lambda p: (p[0] + p[2], p[1], p[0]))
    # optional sea surface drawn first under everything above it: we draw water cells as translucent later
    for p in order:
        x, y, z = p
        sh = shapes[p]
        if sh == "full" and opaque((x + 1, y, z)) and opaque((x, y, z + 1)) and opaque((x, y + 1, z)):
            continue
        cols = block_colors(pts[p])
        if cols is None: continue
        tc, sc = cols
        sx = int((x - z) * a + ox); sy = int((x + z) * a / 2 - y * a + oy)
        reg = img[sy:sy + 2 * a, sx:sx + 2 * a]
        if reg.shape[:2] != top.shape: continue
        if sh == "water":
            if shapes.get((x, y + 1, z)) == "water": continue
            m = top
            reg[m] = reg[m] * 0.45 + tc * 0.55
            continue
        if sh == "flat":
            off = a  # drop the top face to the bottom of the cell
            r2 = img[sy + off:sy + off + 2 * a, sx:sx + 2 * a]
            if r2.shape[:2] == top.shape: r2[top] = tc
            continue
        if sh == "thin":
            # a narrow column in the middle of the cell
            m = np.zeros_like(top); w = max(1, a // 3)
            m[a // 4:2 * a - a // 4, a - w:a + w] = True
            reg[m & (np.arange(2 * a)[None, :] < a)] = sc * 0.85
            reg[m & (np.arange(2 * a)[None, :] >= a)] = sc * 0.7
            reg[a // 4:a // 4 + 1, a - w:a + w] = tc
            continue
        dy = 0
        if sh == "slab": dy = a // 2
        if sh == "slab_top": dy = 0
        r = img[sy + dy:sy + dy + 2 * a, sx:sx + 2 * a]
        if r.shape[:2] != top.shape: continue
        hcut = a // 2 if sh in ("slab", "slab_top") else a
        lm = left.copy(); rm = right.copy()
        if hcut < a:
            rows = np.arange(2 * a)[:, None]
            lim = (a / 2) + np.arange(2 * a)[None, :] / 2 + hcut
            lim2 = (a / 2) + (2 * a - 1 - np.arange(2 * a))[None, :] / 2 + hcut
            lm &= rows < lim; rm &= rows < lim2
        if not opaque((x, y, z + 1)): r[lm] = sc * 0.80
        if not opaque((x + 1, y, z)): r[rm] = sc * 0.62
        if not opaque((x, y + 1, z)) or sh != "full": r[top] = tc
    if water_y is not None:
        pass
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    if title:
        from PIL import ImageDraw, ImageFont
        d = ImageDraw.Draw(im)
        try: f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        except Exception: f = None
        d.text((20, 12), title, fill=(30, 40, 60), font=f)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    im.save(out)
    return out
