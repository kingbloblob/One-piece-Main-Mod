"""Small painter for 64x64 Minecraft skins (classic 4 px arms, as the zombie model uses).

The zombie model mirrors the right arm and right leg onto the left ones, so only those
are painted. Every part is painted as a "wrap": the four sides laid out left to right,
which matches the skin layout, so a stripe at row r goes all the way around the part.

Wrap columns:
  head  0-31  (right side 0-7, front 8-15, left 16-23, back 24-31), rows 0-7
  body  0-23  (right side 0-3, front 4-11, left 12-15, back 16-23), rows 0-11
  arm   0-15  (outer 0-3, front 4-7, inner 8-11, back 12-15), rows 0-11
  leg   0-15  (outer 0-3, front 4-7, inner 8-11, back 12-15), rows 0-11
"""
import random
from PIL import Image

PARTS = {
    # name: (wrap origin x, y, wrap width, height, top xy, bottom xy, top w, top h)
    'head': (0, 8, 32, 8, (8, 0), (16, 0), 8, 8),
    'hat': (32, 8, 32, 8, (40, 0), (48, 0), 8, 8),
    'body': (16, 20, 24, 12, (20, 16), (28, 16), 8, 4),
    'arm': (40, 20, 16, 12, (44, 16), (48, 16), 4, 4),
    'leg': (0, 20, 16, 12, (4, 16), (8, 16), 4, 4),
}
FRONT = {'head': range(8, 16), 'hat': range(8, 16), 'body': range(4, 12), 'arm': range(4, 8), 'leg': range(4, 8)}
BACK = {'head': range(24, 32), 'hat': range(24, 32), 'body': range(16, 24), 'arm': range(12, 16), 'leg': range(12, 16)}


def hexc(s):
    if s is None:
        return None
    if isinstance(s, tuple):
        return s if len(s) == 4 else s + (255,)
    s = s.lstrip('#')
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def shade(c, f):
    c = hexc(c)
    return tuple(max(0, min(255, int(v * f))) for v in c[:3]) + (c[3],)


def mix(a, b, t):
    a, b = hexc(a), hexc(b)
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,)


class Skin:
    def __init__(self, seed=1):
        self.img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        self.rnd = random.Random(seed)

    # --- raw access ---
    def px(self, x, y, c, noise=0.0):
        if c is None:
            self.img.putpixel((x, y), (0, 0, 0, 0))
            return
        c = hexc(c)
        if noise:
            c = shade(c, 1 + self.rnd.uniform(-noise, noise))
        self.img.putpixel((x, y), c)

    def get(self, x, y):
        return self.img.getpixel((x, y))

    # --- wraps ---
    def w(self, part, col, row, c, noise=0.04):
        ox, oy, ww, hh = PARTS[part][:4]
        if 0 <= col < ww and 0 <= row < hh:
            self.px(ox + col, oy + row, c, noise)

    def wget(self, part, col, row):
        ox, oy = PARTS[part][:2]
        return self.get(ox + col, oy + row)

    def band(self, part, r0, r1, c, cols=None, noise=0.04):
        """Fill rows r0..r1-1 all around (or only the given columns)."""
        ww = PARTS[part][2]
        for r in range(r0, r1):
            for col in (cols if cols is not None else range(ww)):
                self.w(part, col, r, c, noise)

    def cap(self, part, which, c, noise=0.04, fn=None):
        """Fill the top or bottom face. fn(x, y) -> colour or None to skip."""
        _, _, _, _, top, bot, tw, th = PARTS[part]
        x0, y0 = top if which == 'top' else bot
        for y in range(th):
            for x in range(tw):
                col = fn(x, y) if fn else c
                if col is not None:
                    self.px(x0 + x, y0 + y, col, noise)

    def fill(self, part, c, noise=0.04):
        self.band(part, 0, PARTS[part][3], c, noise=noise)
        self.cap(part, 'top', c, noise)
        self.cap(part, 'bottom', c, noise)

    def front(self, part, x, y, c, noise=0.0):
        """Pixel on the front face, x counted from the viewer's left."""
        self.w(part, FRONT[part][0] + x, y, c, noise)

    def back(self, part, x, y, c, noise=0.0):
        self.w(part, BACK[part][0] + x, y, c, noise)

    def side(self, part, which, x, y, c, noise=0.0):
        """which='r' = the model's right side (viewer's left when facing it)."""
        ww = PARTS[part][2]
        fw = len(FRONT[part])
        sw = (ww - 2 * fw) // 2
        start = 0 if which == 'r' else fw + sw
        self.w(part, start + x, y, c, noise)

    # --- finishing ---
    def finish(self, path):
        """Soft lighting: darker towards the bottom of each part and on the back."""
        out = self.img.copy()
        for part, (ox, oy, ww, hh, *_ ) in PARTS.items():
            for r in range(hh):
                for col in range(ww):
                    p = self.img.getpixel((ox + col, oy + r))
                    if p[3] == 0:
                        continue
                    f = 1.04 - 0.08 * r / max(1, hh - 1)
                    if col in BACK[part]:
                        f *= 0.93
                    elif col not in FRONT[part]:
                        f *= 0.97
                    out.putpixel((ox + col, oy + r), shade(p, f))
        out.save(path)
        return out


def preview(img, scale=4):
    """Front and back view side by side, for checking skins by eye."""
    v = Image.new('RGBA', (34, 34), (70, 70, 80, 255))

    def blit(sx, sy, w, h, dx, dy, flip=False):
        reg = img.crop((sx, sy, sx + w, sy + h))
        if flip:
            reg = reg.transpose(Image.FLIP_LEFT_RIGHT)
        v.alpha_composite(reg, (dx, dy))

    for off, fr in ((0, True), (17, False)):
        hx = 8 if fr else 24
        bx = 20 if fr else 32
        ax = 44 if fr else 52
        lx = 4 if fr else 12
        blit(hx, 8, 8, 8, off + 4, 1)
        blit(hx + 32, 8, 8, 8, off + 4, 1)
        blit(bx, 20, 8, 12, off + 4, 9)
        blit(ax, 20, 4, 12, off + 0, 9)
        blit(ax, 20, 4, 12, off + 12, 9, True)
        blit(lx, 20, 4, 12, off + 4, 21)
        blit(lx, 20, 4, 12, off + 8, 21, True)
    return v.resize((34 * scale, 34 * scale), Image.NEAREST)
