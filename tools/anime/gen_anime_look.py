"""Anime look for vanilla Minecraft: regrades the game's own textures so they sit next to the mod's art.
Brighter, more saturated and slightly warmer colours, flatter cel-style shading, and a dark ink edge on items.
Nothing is redrawn; each texture keeps its size and shape, and its .png.mcmeta (animation, blur) is copied next to it,
because the game only reads the .mcmeta from the same pack as the PNG.

Usage: gen_anime_look.py <vanilla textures> <pack assets/minecraft/textures folder>
  <vanilla textures> is the Minecraft client jar (e.g. .minecraft/versions/26.3/26.3.jar) or a folder laid out
  like its assets/minecraft/textures. Run it again after a Minecraft update so new textures get the look too.
"""
import sys, os, io, zipfile, shutil
import numpy as np
from PIL import Image

SRC, OUT = sys.argv[1], sys.argv[2]

# Folders we leave alone: menus belong to the pirate_menus pack, the rest are masks, palettes or data, not art.
SKIP = ("gui/", "font/", "misc/", "map/", "effect/", "trims/", "colormap/", "environment/end_sky", "block/destroy_stage")

def sources():
    """Yields (path under textures/, bytes) for every .png and .png.mcmeta."""
    if zipfile.is_zipfile(SRC):
        z = zipfile.ZipFile(SRC)
        for n in z.namelist():
            if n.startswith("assets/minecraft/textures/") and n.endswith((".png", ".png.mcmeta")):
                yield n[len("assets/minecraft/textures/"):], z.read(n)
    else:
        for dp, _, fs in os.walk(SRC):
            for f in fs:
                if f.endswith((".png", ".png.mcmeta")):
                    p = os.path.relpath(os.path.join(dp, f), SRC).replace(os.sep, "/")
                    yield p, open(os.path.join(dp, f), "rb").read()

def rgb_to_hsv(c):
    mx, mn = c.max(-1), c.min(-1)
    d = mx - mn
    s = np.where(mx > 0, d / np.maximum(mx, 1e-6), 0)
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    dd = np.maximum(d, 1e-6)
    h = np.where(mx == r, ((g - b) / dd) % 6, np.where(mx == g, (b - r) / dd + 2, (r - g) / dd + 4)) / 6
    return np.where(d > 0, h, 0), s, mx

def hsv_to_rgb(h, s, v):
    i = np.floor(h * 6).astype(int) % 6
    f = h * 6 - np.floor(h * 6)
    p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
    out = np.choose(i[..., None].repeat(3, -1), [np.stack(x, -1) for x in
          ((v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q))])
    return out

def grade(c, sat=1.2, bands=5, flat=0.45):
    """c: float RGB 0..1. Boosts saturation, lifts mids, warms a touch, and pulls brightness toward a few flat bands."""
    h, s, v = rgb_to_hsv(c)
    s = np.clip(s * sat + 0.02 * (s > 0.08), 0, 1)
    v = np.clip(v ** 0.92 * 1.02, 0, 1)
    q = (np.round(v * (bands - 1)) / (bands - 1))
    v = v * (1 - flat) + q * flat
    out = hsv_to_rgb(h, s, v)
    out[..., 0] *= 1.025
    out[..., 2] *= 0.975
    return np.clip(out, 0, 1)

def ink(a, rgb):
    """Darkens opaque pixels that touch transparency, like the outlines on the mod's own items."""
    solid = a > 127
    pad = np.pad(solid, 1, constant_values=False)
    edge = solid & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    rgb[edge] *= 0.45
    return rgb

def kind(p):
    if p.startswith("item/") or p.startswith("particle/") or p.startswith("mob_effect/"):
        return "item"
    if p.startswith("entity/") or p.startswith("painting/"):
        return "entity"
    if p.startswith("environment/celestial/sun"):
        return "sun"
    return "block"

def restyle(p, data):
    im = Image.open(io.BytesIO(data)).convert("RGBA")
    a = np.asarray(im, float) / 255
    rgb, alpha = a[..., :3], a[..., 3]
    vis = alpha > 0.5
    k = kind(p)
    # Grey textures are tinted by the biome (grass, leaves, water): only flatten them, the colormaps add the colour.
    grey = vis.any() and rgb_to_hsv(rgb[vis])[1].mean() < 0.06
    if k == "sun":
        rgb = grade(rgb, sat=1.4, bands=4, flat=0.6)
    elif k == "item":
        rgb = ink(alpha * 255, grade(rgb, sat=1.22, bands=5, flat=0.5))
    elif k == "entity":
        rgb = grade(rgb, sat=1.15, bands=6, flat=0.35)
    else:
        rgb = grade(rgb, sat=1.0 if grey else 1.18, bands=6 if grey else 5, flat=0.4)
    a[..., :3] = rgb
    return Image.fromarray(np.round(a * 255).astype(np.uint8), "RGBA")

def colormap(p, data):
    """Lusher, brighter grass and leaves, the way anime islands look."""
    im = Image.open(io.BytesIO(data)).convert("RGBA")
    a = np.asarray(im, float) / 255
    h, s, v = rgb_to_hsv(a[..., :3])
    h = h - 0.012 * (h > 0.15) * (h < 0.45)           # nudge greens toward yellow-green
    a[..., :3] = hsv_to_rgb(h % 1, np.clip(s * 1.3, 0, 1), np.clip(v * 1.1, 0, 1))
    return Image.fromarray(np.round(np.clip(a, 0, 1) * 255).astype(np.uint8), "RGBA")

if os.path.isdir(OUT):
    shutil.rmtree(OUT)
files = dict(sources())
n = 0
for p, data in files.items():
    if not p.endswith(".png"):
        continue
    if p.startswith("colormap/"):
        img = colormap(p, data)
    elif p.startswith(SKIP):
        continue
    else:
        img = restyle(p, data)
    dst = os.path.join(OUT, p)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    img.save(dst, optimize=True)
    meta = files.get(p + ".mcmeta")
    if meta is not None:
        open(dst + ".mcmeta", "wb").write(meta)
    n += 1
print(f"{n} textures written to {OUT}")
