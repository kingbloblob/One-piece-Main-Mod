"""Original title logo: gold 3D lettering with a dark outline, plus an 'edition' ribbon.
Usage: logo.py <pack textures/gui/title folder>"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
FONT = "/usr/share/fonts/truetype/crosextra/Caladea-Bold.ttf"

def lettering(text, w, h, size, depth, outline, fill_top, fill_bot, ext_col, out_col, tracking=0):
    S = 2  # supersample
    W, H = w * S, h * S
    font = ImageFont.truetype(FONT, size * S)
    # text mask, centred
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    widths = [d.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * S * (len(text) - 1)
    bbox = d.textbbox((0, 0), text, font=font)
    x = (W - total) / 2
    y = (H - depth * S - (bbox[3] - bbox[1])) / 2 - bbox[1] - outline * S * 0.3
    for ch, cw in zip(text, widths):
        d.text((x, y), ch, font=font, fill=255)
        x += cw + tracking * S
    m = np.asarray(mask, float) / 255

    def shift(a, dx, dy):
        out = np.zeros_like(a)
        out[max(dy, 0):H + min(dy, 0), max(dx, 0):W + min(dx, 0)] = a[max(-dy, 0):H - max(dy, 0), max(-dx, 0):W - max(dx, 0)]
        return out

    # extrusion: stack the mask down-right
    ext = np.zeros_like(m)
    for k in range(1, depth * S + 1):
        ext = np.maximum(ext, shift(m, k // 3, k))
    body = np.maximum(m, ext)
    outl = np.asarray(Image.fromarray((body * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(outline * S * 2 + 1)), float) / 255

    img = np.zeros((H, W, 4))
    img[..., :3] = out_col; img[..., 3] = outl * 255
    ys = np.arange(H)[:, None, None] / H
    ext_rgb = np.asarray(ext_col, float) * (1.0 - ys * 0.35)
    img[..., :3] = np.where(ext[..., None] > 0.5, ext_rgb, img[..., :3])
    # face: vertical gold gradient with a shine band and fine wood-like streaks
    rows = np.where(m.sum(1) > 0)[0]
    top, bot = rows.min(), rows.max()
    t = np.clip((np.arange(H) - top) / max(bot - top, 1), 0, 1)[:, None, None]
    face = np.asarray(fill_top, float) * (1 - t) + np.asarray(fill_bot, float) * t
    face = face + (np.abs(t - 0.38) < 0.05) * 40
    streak = np.random.default_rng(3).normal(0, 1, (1, W)).repeat(H, 0)[..., None]
    streak = np.asarray(Image.fromarray(((streak[..., 0] + 4) * 30).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), float)[..., None] / 30 - 4
    face = face + streak * 6
    # thin inner highlight on the top-left edges of the face
    inner = m - shift(m, 2 * S, 2 * S).clip(0, 1)
    face = np.where((inner > 0.5)[..., None], face + 55, face)
    a = m[..., None]
    img[..., :3] = img[..., :3] * (1 - a) + face * a
    img[..., 3] = np.maximum(img[..., 3], m * 255)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGBA")
    return im.resize((w, h), Image.LANCZOS)

# main logo: drawn at 256x44 GUI units from the top 176 px of a 1024x256 texture
logo = Image.new("RGBA", (1024, 256), (0, 0, 0, 0))
main = lettering("ONE PIECE", 1024, 176, 150, 16, 7, (255, 232, 120), (226, 128, 28), (120, 54, 20), (34, 16, 8), tracking=4)
logo.alpha_composite(main, (0, 0))
logo.save(os.path.join(OUT, "minecraft.png"))
logo.save(os.path.join(OUT, "minceraft.png"))

# edition ribbon: drawn at 128x14 from the top 56 px of a 512x64 texture
ed = Image.new("RGBA", (512, 64), (0, 0, 0, 0))
rib = Image.new("RGBA", (512, 56), (0, 0, 0, 0))
d = ImageDraw.Draw(rib)
d.polygon([(28, 6), (484, 6), (500, 28), (484, 50), (28, 50), (12, 28)], fill=(36, 18, 10, 255))
d.polygon([(34, 10), (478, 10), (492, 28), (478, 46), (34, 46), (20, 28)], fill=(176, 36, 30, 255))
d.line([(40, 15), (472, 15)], fill=(214, 82, 64, 255), width=2)
ed.alpha_composite(rib, (0, 0))
txt = lettering("PIRATE  EDITION", 512, 56, 30, 3, 3, (255, 244, 210), (240, 200, 120), (90, 40, 20), (36, 18, 10), tracking=3)
ed.alpha_composite(txt, (0, -1))
ed.save(os.path.join(OUT, "edition.png"))
print("logo done")
