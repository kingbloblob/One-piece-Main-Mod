"""Procedural 16x16 pixel art for farming and ranching (com.onepiecemod.farm). Every texture is drawn
here from scratch, seeded by its name so reruns give the same pictures. Used by gen_farm.py."""
import math
import random
from PIL import Image

T = (0, 0, 0, 0)


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def shade(c, f):
    c = rgb(c) if isinstance(c, str) else c
    return tuple(max(0, min(255, int(v * f))) for v in c[:3]) + (255,)


def new():
    return Image.new('RGBA', (16, 16), T)


def put(img, x, y, c):
    if 0 <= x < 16 and 0 <= y < 16:
        img.putpixel((x, y), rgb(c) if isinstance(c, str) else c)


def disc(img, cx, cy, r, c, r2=None, light=1.25, dark=0.75):
    """A shaded round blob (light top-left, dark bottom-right)."""
    r2 = r2 or r
    for y in range(16):
        for x in range(16):
            dx, dy = (x + 0.5 - cx) / r, (y + 0.5 - cy) / r2
            d = dx * dx + dy * dy
            if d <= 1.0:
                f = 1.0
                if dx + dy < -0.6:
                    f = light
                elif dx + dy > 0.7 or d > 0.8:
                    f = dark
                put(img, x, y, shade(c, f))


def outline(img, c=(40, 30, 20, 255)):
    """Dark outline around the opaque shape, like vanilla item icons."""
    src = img.copy()
    for y in range(16):
        for x in range(16):
            if src.getpixel((x, y))[3] == 0:
                for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + ox, y + oy
                    if 0 <= nx < 16 and 0 <= ny < 16 and src.getpixel((nx, ny))[3] > 0:
                        img.putpixel((x, y), c)
                        break
    return img


# ---------------------------------------------------------------- crop stages (age 0..3)

def stalk(img, r, x, base, h, stem, lean=0):
    for i in range(h):
        put(img, x + (lean if i > h // 2 else 0), 15 - i, shade(stem, r.uniform(0.85, 1.1)))
    return x + (lean if h > 1 else 0), 16 - h


def crop_grain(name, age, stem, head, tall=False):
    r = random.Random(f"{name}{age}")
    img = new()
    heights = [3, 7, 11, 14 if not tall else 15][age]
    for x in (1, 4, 7, 10, 13):
        x += r.randint(0, 1)
        h = max(2, heights - r.randint(0, 2))
        tx, ty = stalk(img, r, x, 15, h, stem, r.choice((-1, 0, 1)))
        if age >= 2:
            col = head if age == 3 else shade(stem, 1.25)
            for i in range(3 if age == 3 else 2):
                put(img, tx, ty + i, shade(col, r.uniform(0.85, 1.15)))
                put(img, tx + (1 if i % 2 == 0 else -1), ty + i + 1, shade(col, r.uniform(0.8, 1.05)))
        # A leaf on each stalk.
        ly = 15 - h // 2
        put(img, x + 1, ly, shade(stem, 1.15))
        put(img, x - 1, ly + 2, shade(stem, 0.9))
    return img


def crop_root(name, age, stem, root, top=None):
    r = random.Random(f"{name}{age}")
    img = new()
    h = [2, 5, 8, 10][age]
    for x in (2, 6, 10, 13):
        x += r.randint(-1, 1)
        for i in range(h):
            put(img, x, 15 - i, shade(stem, r.uniform(0.85, 1.15)))
            if i > 1 and i % 2 == 0:
                put(img, x - 1, 15 - i, shade(stem, 1.2))
                put(img, x + 1, 14 - i, shade(stem, 0.85))
        if age == 3:
            for ox in (-1, 0, 1):
                put(img, x + ox, 15, shade(root, 0.9))
                put(img, x + ox, 14, shade(top or root, 1.1))
            put(img, x, 13, shade(top or root, 1.0))
    return img


def crop_fruit(name, age, stem, fruit, long=False):
    r = random.Random(f"{name}{age}")
    img = new()
    h = [3, 7, 11, 13][age]
    for x in (3, 8, 12):
        x += r.randint(-1, 0)
        for i in range(h):
            put(img, x, 15 - i, shade(stem, r.uniform(0.85, 1.1)))
        for i in range(2, h, 2):
            side = 1 if (i // 2) % 2 else -1
            put(img, x + side, 15 - i, shade(stem, 1.2))
            put(img, x + 2 * side, 15 - i, shade(stem, 1.0))
        if age >= 2:
            col = fruit if age == 3 else shade(stem, 1.35)
            for i in range(4, h, 3):
                side = -1 if (i // 3) % 2 else 1
                fx, fy = x + side * 2, 15 - i
                put(img, fx, fy, shade(col, 1.2))
                put(img, fx, fy + 1, shade(col, 0.9))
                if long:
                    put(img, fx, fy + 2, shade(col, 0.8))
                else:
                    put(img, fx + side, fy + 1, shade(col, 0.8))
    return img


def crop_bush(name, age, stem, pod):
    r = random.Random(f"{name}{age}")
    img = new()
    h = [3, 6, 9, 12][age]
    for y in range(16 - h, 16):
        w = max(1, int((y - (16 - h)) * 0.8) + 1)
        for x in range(8 - w, 8 + w):
            if r.random() < 0.8:
                put(img, x, y, shade(stem, r.uniform(0.75, 1.2)))
    if age >= 2:
        col = pod if age == 3 else shade(stem, 1.4)
        for _ in range(4 if age == 3 else 2):
            px, py = r.randint(4, 10), r.randint(16 - h + 2, 13)
            put(img, px, py, shade(col, 1.2))
            put(img, px + 1, py, shade(col, 1.0))
            put(img, px, py + 1, shade(col, 0.85))
            put(img, px + 1, py + 1, shade(col, 0.7))
    return img


def crop_leaf(name, age, stem, leaf):
    r = random.Random(f"{name}{age}")
    img = new()
    h = [2, 5, 8, 10][age]
    for x in (2, 7, 12):
        for i in range(h):
            put(img, x, 15 - i, shade(stem, 0.9))
        for i in range(1, h, 2):
            for side in (-1, 1):
                c = leaf if age >= 2 else stem
                put(img, x + side, 15 - i, shade(c, r.uniform(0.9, 1.2)))
                put(img, x + 2 * side, 14 - i, shade(c, r.uniform(0.8, 1.0)))
    return img


def crop_gourd(name, age, stem, gourd, stripes=None, face=False):
    r = random.Random(f"{name}{age}")
    img = new()
    # A low creeping vine with big leaves.
    for x in range(1, 15):
        y = 14 - (1 if math.sin(x * 0.9) > 0.5 else 0)
        put(img, x, y, shade(stem, r.uniform(0.85, 1.1)))
    for lx in (2, 6, 11):
        size = [1, 2, 2, 2][age]
        for dy in range(size + 1):
            for dx in range(-size, size + 1):
                put(img, lx + dx, 13 - dy - age, shade(stem, r.uniform(1.0, 1.25)))
    if age >= 2:
        rad = 2.2 if age == 2 else 3.6
        col = gourd if age == 3 else shade(stem, 1.4)
        disc(img, 8, 15 - rad, rad, col, rad * 0.85)
        if age == 3 and stripes:
            for x in range(5, 12, 2):
                for y in range(10, 15):
                    if img.getpixel((x, y))[3]:
                        put(img, x, y, shade(stripes, 1.0))
        if age == 3 and face:
            for x, y in ((6, 11), (10, 11), (7, 13), (8, 13), (9, 13)):
                put(img, x, y, (30, 30, 40, 255))
    return img


# ---------------------------------------------------------------- items

def seeds(name, c):
    r = random.Random(name)
    img = new()
    for sx, sy in ((5, 6), (9, 5), (7, 9), (11, 9), (4, 10), (8, 12), (10, 12)):
        sx += r.randint(-1, 1)
        sy += r.randint(-1, 1)
        put(img, sx, sy, shade(c, 1.2))
        put(img, sx + 1, sy, shade(c, 1.0))
        put(img, sx, sy + 1, shade(c, 0.8))
    return outline(img, shade(c, 0.4))


def grain_bundle(name, stem, head):
    r = random.Random(name)
    img = new()
    for i, x in enumerate((5, 7, 9, 11)):
        for y in range(6, 15):
            put(img, x - (y - 6) // 4 + 1 if i < 2 else x + (y - 6) // 4 - 1, y, shade(stem, r.uniform(0.85, 1.1)))
        for y in range(2, 7):
            put(img, x, y, shade(head, r.uniform(0.85, 1.2)))
            put(img, x + (1 if y % 2 else -1), y, shade(head, 0.8))
    for x in range(5, 12):
        put(img, x, 10, rgb('#a0703a'))
    return outline(img)


def round_fruit(name, c, leaf='#3f7f2a', r_=4.5, long=False):
    img = new()
    if long:
        for y in range(4, 14):
            w = 2 if y < 11 else 1
            for x in range(8 - w, 8 + w):
                put(img, x + (y - 4) // 4, y, shade(c, 1.2 if x < 8 else 0.85))
        for x, y in ((7, 3), (8, 2), (8, 3)):
            put(img, x, y, leaf)
    else:
        disc(img, 8, 9, r_, c)
        for x, y in ((7, 4), (8, 4), (9, 3), (6, 3)):
            put(img, x, y, leaf)
    return outline(img)


def root_veg(name, body, top, leaf):
    img = new()
    disc(img, 8, 10, 4.2, body, 3.8)
    for x in range(4, 13):
        for y in range(6, 9):
            if img.getpixel((x, y))[3]:
                put(img, x, y, shade(top, 1.0 if x > 6 else 1.2))
    put(img, 8, 15, shade(body, 0.7))
    for x, y in ((7, 1), (7, 2), (8, 3), (9, 1), (9, 2), (10, 0), (6, 0), (8, 4), (8, 5)):
        put(img, x, y, shade(leaf, 1.0 if y % 2 else 1.2))
    return outline(img)


def long_root(name, body, leaf):
    img = new()
    for i in range(10):
        x, y = 4 + i, 12 - i // 2 - (i % 2)
        for dy in range(-1, 2):
            put(img, x, y + dy, shade(body, 1.2 if dy < 0 else (0.75 if dy > 0 else 1.0)))
    for x, y in ((13, 4), (14, 3), (12, 3), (13, 2)):
        put(img, x, y, leaf)
    return outline(img)


def bead_cluster(name, c, stem):
    r = random.Random(name)
    img = new()
    for y in range(2, 14):
        put(img, 8, y, stem)
    for y in range(3, 14, 2):
        for side in (-1, 1):
            put(img, 8 + side, y, shade(c, 1.25))
            put(img, 8 + 2 * side, y + 1, shade(c, r.uniform(0.8, 1.0)))
    return outline(img)


def pod(name, c):
    img = new()
    disc(img, 8, 8.5, 3.6, c, 6.0)
    for y in range(4, 14, 3):
        for x in range(6, 11):
            if img.getpixel((x, y))[3]:
                put(img, x, y, shade(c, 0.7))
    put(img, 8, 1, '#4a6f2a')
    return outline(img)


def leaves(name, c):
    img = new()
    for (cx, cy, ang) in ((6, 9, -0.6), (10, 7, 0.5)):
        for t in range(-5, 6):
            for w in range(-2, 3):
                if abs(w) <= 2 - abs(t) // 3:
                    x = int(cx + t * math.sin(ang) + w * math.cos(ang))
                    y = int(cy - t * math.cos(ang) + w * math.sin(ang))
                    put(img, x, y, shade(c, 1.2 if w < 0 else 0.9))
        put(img, cx, cy, shade(c, 0.6))
    return outline(img)


def gourd(name, c, stripes=None, face=False):
    img = new()
    disc(img, 8, 9.5, 6, c, 5)
    if stripes:
        for x in (4, 7, 10, 12):
            for y in range(5, 15):
                if img.getpixel((x, y))[3]:
                    put(img, x, y, stripes)
    if face:
        for x, y in ((5, 8), (6, 8), (10, 8), (11, 8), (6, 11), (7, 12), (8, 11), (9, 12), (10, 11)):
            put(img, x, y, (30, 30, 50, 255))
    for x, y in ((8, 3), (8, 4), (9, 2)):
        put(img, x, y, '#4a5a3a')
    return outline(img)


def melon_slice(name, flesh, rind):
    img = new()
    for y in range(4, 14):
        for x in range(2, 14):
            # A wedge: rind along the bottom curve.
            if y >= 4 + abs(x - 8) * 0.8 * 0 and (x - 8) ** 2 / 36 + (y - 4) ** 2 / 100 <= 1 and y >= 4 + abs(x - 8) - 2:
                put(img, x, y, flesh)
    for x in range(2, 14):
        for y in range(15, 3, -1):
            if img.getpixel((x, y))[3]:
                put(img, x, y, rind)
                put(img, x, y - 1, shade(rind, 1.3))
                break
    for x, y in ((7, 8), (9, 9), (8, 11), (6, 10), (10, 7)):
        put(img, x, y, (40, 30, 30, 255))
    return outline(img)


def bottle(name, liquid, glass='#c8e0e8', mug=False):
    img = new()
    if mug:
        for y in range(4, 15):
            for x in range(4, 12):
                put(img, x, y, shade('#8a5a2a', 1.15 if x < 6 else (0.8 if x > 9 else 1.0)))
        for x in range(4, 12):
            put(img, x, 4, rgb('#f4f0e0'))
            put(img, x, 5, shade(liquid, 1.2))
        for y in range(7, 12):
            put(img, 12, y, '#6a4520')
            put(img, 13, y, '#6a4520')
        for x in range(4, 12, 3):
            for y in range(6, 15):
                put(img, x, y, '#5a3a18')
    else:
        for y in range(7, 15):
            for x in range(4, 12):
                put(img, x, y, shade(liquid, 1.2 if x < 6 else (0.85 if x > 9 else 1.0)))
        for y in range(3, 7):
            put(img, 7, y, glass)
            put(img, 8, y, glass)
        put(img, 7, 2, '#8a6a4a')
        put(img, 8, 2, '#8a6a4a')
    return outline(img)


def egg(name, c, spots=None, big=False):
    r = random.Random(name)
    img = new()
    disc(img, 8, 9, 5 if big else 4, c, 6.5 if big else 5.2)
    if spots:
        for _ in range(7):
            x, y = r.randint(5, 11), r.randint(5, 13)
            if img.getpixel((x, y))[3]:
                put(img, x, y, spots)
    return outline(img)


def lump(name, c, specks=None):
    r = random.Random(name)
    img = new()
    for cx, cy, rr in ((7, 10, 4), (10, 9, 3), (8, 7, 3)):
        disc(img, cx, cy, rr, c)
    if specks:
        for _ in range(8):
            x, y = r.randint(4, 12), r.randint(5, 13)
            if img.getpixel((x, y))[3]:
                put(img, x, y, specks)
    return outline(img)


def wedge(name, c, holes):
    img = new()
    for y in range(5, 14):
        for x in range(2, 15):
            if x <= 2 + (y - 5) * 1.5 + 2:
                put(img, x, y, shade(c, 1.2 if y < 7 else 1.0))
    for x, y in ((5, 10), (8, 12), (4, 12), (9, 9)):
        put(img, x, y, holes)
    return outline(img)


def watering_can():
    img = new()
    body = '#4f8f9a'
    for y in range(6, 14):
        for x in range(3, 11):
            put(img, x, y, shade(body, 1.2 if x < 5 else (0.8 if x > 8 else 1.0)))
    for x in range(4, 10):
        put(img, x, 5, shade(body, 0.7))
    for i in range(5):
        put(img, 11 + i // 2 + (1 if i == 4 else 0), 11 - i, shade(body, 0.9))
    put(img, 15, 6, '#9fd8e8')
    put(img, 14, 5, '#9fd8e8')
    for x in range(4, 10):
        put(img, x, 3, '#3a6a72')
    put(img, 3, 4, '#3a6a72')
    put(img, 10, 4, '#3a6a72')
    return outline(img)


def plate(name, food, accent=None, kind='plate'):
    r = random.Random(name)
    img = new()
    if kind == 'bowl':
        for y in range(9, 15):
            w = 7 - (y - 9) // 2
            for x in range(8 - w, 8 + w):
                put(img, x, y, shade('#8a5a3a', 1.1 if x < 6 else 0.9))
        for x in range(2, 14):
            put(img, x, 8, shade(food, 1.2))
            put(img, x, 9, shade(food, 1.0))
        for x in range(4, 12):
            put(img, x, 7, shade(food, r.uniform(1.0, 1.3)))
        if accent:
            for x, y in ((5, 7), (8, 8), (10, 7), (7, 6)):
                put(img, x, y, accent)
    elif kind == 'skewer':
        for i in range(14):
            put(img, 1 + i, 14 - i, '#c8a060')
        for cx, cy in ((5, 10), (8, 7), (11, 4)):
            disc(img, cx, cy, 2.2, food)
    elif kind == 'bar':
        for y in range(5, 12):
            for x in range(3, 13):
                put(img, x, y + (x - 3) // 4, shade(food, 1.2 if y < 6 else 1.0))
        for x in range(3, 13, 3):
            for y in range(5, 13):
                if img.getpixel((x, y))[3]:
                    put(img, x, y, shade(food, 0.7))
        if accent:
            for x in range(3, 13):
                put(img, x, 12 + (x - 3) // 4, accent)
    elif kind == 'loaf':
        disc(img, 8, 10, 6, food, 4)
        for x in (5, 8, 11):
            put(img, x, 8, shade(food, 0.75))
            put(img, x + 1, 9, shade(food, 0.75))
    else:  # plate
        for x in range(1, 15):
            put(img, x, 12, rgb('#e8e8f0'))
            put(img, x, 13, rgb('#b8b8c8'))
        disc(img, 8, 9, 5, food, 3)
        if accent:
            for x, y in ((6, 8), (9, 7), (10, 9), (7, 10)):
                put(img, x, y, accent)
    return outline(img)


# ---------------------------------------------------------------- blocks

def planks(name, c):
    r = random.Random(name)
    img = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            f = r.uniform(0.9, 1.08) * (0.75 if y % 4 == 3 else 1.0)
            img.putpixel((x, y), shade(c, f))
    return img


def seed_vault_side():
    img = planks('vault_side', '#8a6038')
    for row in range(3):
        for col in range(2):
            x0, y0 = 1 + col * 7, 1 + row * 5
            for y in range(y0, y0 + 4):
                for x in range(x0, x0 + 6):
                    img.putpixel((x, y), shade('#5a3a1e', 1.0 if y > y0 else 0.8))
            img.putpixel((x0 + 2, y0 + 2), rgb('#d8b040'))
            img.putpixel((x0 + 3, y0 + 2), rgb('#d8b040'))
            img.putpixel((x0 + 1, y0 + 1), rgb('#e8e0c0'))
    return img


def seed_vault_top():
    img = planks('vault_top', '#9a6e40')
    r = random.Random('jars')
    for cx, cy, c in ((4, 4, '#d8c070'), (11, 4, '#7ab840'), (4, 11, '#c84a3a'), (11, 11, '#9a6ad8')):
        for y in range(cy - 2, cy + 2):
            for x in range(cx - 2, cx + 2):
                img.putpixel((x, y), shade(c, r.uniform(0.8, 1.2)))
    return img


def copper(name, base='#c87a4a'):
    r = random.Random(name)
    img = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            img.putpixel((x, y), shade(base, r.uniform(0.85, 1.12)))
    for _ in range(10):
        img.putpixel((r.randrange(16), r.randrange(16)), rgb('#5aa890'))
    return img


def dial_shell(name):
    r = random.Random(name)
    img = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            ring = int(math.hypot(x - 7.5, y - 7.5)) % 3 == 0
            img.putpixel((x, y), shade('#e8d8b0' if not ring else '#c8a878', r.uniform(0.92, 1.06)))
    return img


def trough_side():
    img = planks('trough_side', '#7a5430')
    for y in range(16):
        img.putpixel((0, y), rgb('#4a3018'))
        img.putpixel((15, y), rgb('#4a3018'))
    return img


def hay_top(name):
    r = random.Random(name)
    img = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            img.putpixel((x, y), shade('#c8a840' if (x + y * 3) % 5 else '#a08028', r.uniform(0.85, 1.15)))
    return img


def straw(name):
    r = random.Random(name)
    img = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            img.putpixel((x, y), shade('#e0c060' if x % 3 else '#b89838', r.uniform(0.85, 1.1)))
    return img


def hat_band():
    img = straw('hat_band')
    for x in range(16):
        for y in range(6, 9):
            img.putpixel((x, y), rgb('#c02020'))
    return img


def burlap(name):
    r = random.Random(name)
    img = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            img.putpixel((x, y), shade('#c8a878', r.uniform(0.82, 1.1) * (0.9 if (x + y) % 2 else 1.0)))
    for x, y in ((4, 6), (5, 6), (10, 6), (11, 6), (5, 10), (6, 11), (7, 11), (8, 11), (9, 11), (10, 10)):
        img.putpixel((x, y), rgb('#3a2a1a'))
    return img


def plaid(name):
    img = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            c = '#3a5aa8' if (x // 4 + y // 4) % 2 else '#c84a3a'
            img.putpixel((x, y), shade(c, 0.8 if x % 4 == 0 or y % 4 == 0 else 1.0))
    return img
