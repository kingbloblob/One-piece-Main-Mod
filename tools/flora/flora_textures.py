"""Procedural 16x16 pixel art for the flora blocks (grass tufts, shrubs, ground cover, soils and a few flower shapes).
Reuses the deco helpers in tools/deco/textures.py; everything is drawn here, nothing is copied from vanilla.
Seeded by the texture name, so reruns give the same pictures."""
import os, sys

for _d in (os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'deco'), '/mnt/project-files/one-piece-mod/tools/deco'):
    if os.path.exists(os.path.join(_d, 'textures.py')):
        sys.path.insert(0, _d); break
import textures as tx  # noqa: E402

T = tx.T
rgb, shade, mix, new, rng = tx.rgb, tx.shade, tx.mix, tx.new, tx.rng


def _put(img, x, y, c):
    if 0 <= x < 16 and 0 <= y < 16:
        img.putpixel((x, y), c)


# ---------------------------------------------------------------- grass and tufts

def grass(name, base, tip, blades=6, height=11, dry=False):
    """A tuft of thin blades fanning out from the bottom middle; tips a lighter colour."""
    r = rng(name); img = new()
    for b in range(blades):
        x0 = 8 + r.randint(-3, 3)
        h = height - r.randint(0, 4)
        lean = r.uniform(-0.45, 0.45)
        for i in range(h):
            y = 15 - i
            x = int(round(x0 + lean * i))
            t = i / max(1, h - 1)
            c = mix(base, tip, t * t)
            _put(img, x, y, shade(c, r.uniform(0.9, 1.1)))
            if i < h // 3 and r.random() < 0.5:
                _put(img, x + (1 if lean > 0 else -1), y, shade(base, 0.85))
    if dry:  # a few bent seed heads
        for _ in range(3):
            x = r.randint(3, 12); y = r.randint(2, 6)
            _put(img, x, y, shade(tip, 1.1)); _put(img, x + 1, y, shade(tip, 0.95))
    return img


# ---------------------------------------------------------------- shrubs

def bush(name, leaf, berry=None, width=12, height=11, dark=None):
    """A round leafy shrub with a short stem; optional berries."""
    r = rng(name); img = new()
    dark = dark or shade(leaf, 0.7)
    for y in range(14, 16):
        _put(img, 8, y, shade('#5a4030', 1)); _put(img, 7, y, shade('#5a4030', 0.85))
    cx, cy = 7.5, 15 - height / 2 - 1
    for y in range(16):
        for x in range(16):
            d = ((x - cx) / (width / 2)) ** 2 + ((y - cy) / (height / 2)) ** 2
            if d < 1 and r.random() < 0.92:
                f = 1.15 - 0.4 * d + r.uniform(-0.1, 0.1)
                if y > cy + height / 4: f -= 0.15
                c = leaf if r.random() > 0.2 else dark
                _put(img, x, y, shade(c, f))
    if berry:
        for _ in range(6):
            x = r.randint(3, 12); y = r.randint(int(cy - height / 3), int(cy + height / 3))
            _put(img, x, y, shade(berry, 1.1)); _put(img, x + 1, y + 1, shade(berry, 0.8))
    return img


# ---------------------------------------------------------------- ground cover (flowerbed texture + stem texture)

def cover(name, color, leaf, density=10, glow=False):
    """Little leaves/petals scattered in each quarter (the flowerbed model shows one quarter per segment)."""
    r = rng(name); img = new()
    for qx in (0, 8):
        for qy in (0, 8):
            for _ in range(density):
                x = qx + r.randrange(1, 7); y = qy + r.randrange(1, 7)
                c = color if r.random() < 0.65 else leaf
                _put(img, x, y, shade(c, r.uniform(0.85, 1.2 if glow else 1.1)))
                if r.random() < 0.4:
                    _put(img, x + 1, y, shade(c, 0.9))
    return img


def moss(name, color, leaf):
    """Denser carpet: almost every pixel of each quarter is covered."""
    r = rng(name); img = new()
    for qx in (0, 8):
        for qy in (0, 8):
            for y in range(qy + 1, qy + 7):
                for x in range(qx + 1, qx + 7):
                    if r.random() < 0.88:
                        c = color if r.random() < 0.75 else leaf
                        _put(img, x, y, shade(c, r.uniform(0.85, 1.12)))
    return img


# ---------------------------------------------------------------- flower shapes (tx.flower is the round one)

def spike(name, petal, center, stem='#3f8a2e'):
    """A vertical spike of small blooms (lavender, thistle, iris)."""
    r = rng(name); img = new()
    for y in range(6, 16):
        _put(img, 8, y, shade(stem, 1 if y % 2 else 0.85))
    _put(img, 7, 13, shade(stem, 1.1)); _put(img, 6, 12, shade(stem, 1.1)); _put(img, 9, 12, shade(stem, 1.1))
    for y in range(1, 9):
        w = 1 if y in (1, 8) else 2
        for x in range(8 - w, 9 + w):
            if r.random() < 0.85:
                _put(img, x, y, shade(petal, r.uniform(0.85, 1.15)))
    for (x, y) in [(8, 3), (7, 5), (9, 6)]:
        _put(img, x, y, shade(center, 1))
    return img


def bell(name, petal, center, stem='#3f8a2e'):
    """Bell flowers hanging from a bent stem."""
    r = rng(name); img = new()
    for y in range(5, 16):
        _put(img, 8 if y > 8 else 7 + (y % 2), y, shade(stem, 1 if y % 2 else 0.85))
    for (bx, by) in [(5, 7), (10, 8), (7, 4)]:
        for y in range(by, by + 4):
            w = 1 if y == by else 2
            for x in range(bx - w, bx + w + 1):
                _put(img, x, y, shade(petal, r.uniform(0.85, 1.1) * (0.9 if y == by + 3 else 1)))
        _put(img, bx, by + 4, shade(center, 1))
    return img


def daisy(name, petal, center, stem='#3f8a2e'):
    """A ring of petals around a big centre."""
    r = rng(name); img = new()
    for y in range(9, 16):
        _put(img, 8, y, shade(stem, 1 if y % 2 else 0.85))
    _put(img, 9, 13, shade(stem, 1.1)); _put(img, 10, 12, shade(stem, 1.1))
    cx, cy = 8, 5
    for y in range(1, 10):
        for x in range(4, 13):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d < 4.3:
                if d < 1.6:
                    _put(img, x, y, shade(center, r.uniform(0.9, 1.1)))
                elif (abs(x - cx) < 1.5 or abs(y - cy) < 1.5 or abs(abs(x - cx) - abs(y - cy)) < 1.5):
                    _put(img, x, y, shade(petal, r.uniform(0.85, 1.15)))
    return img


# ---------------------------------------------------------------- soils

def soil(name, base, specks=None, amount=0.14):
    return tx.stone(name, base, amount, specks)


def sand(name, base, specks=None):
    r = rng(name); img = new(); tx.noise(img, r, base, 0.07)
    if specks:
        for _ in range(10):
            img.putpixel((r.randrange(16), r.randrange(16)), shade(specks, r.uniform(0.9, 1.1)))
    return img
