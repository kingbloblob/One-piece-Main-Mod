"""Procedural 16x16 pixel art for the deco blocks. Every texture is drawn here from scratch
(no vanilla art is copied), seeded by the texture name so reruns give the same pictures."""
import random
from PIL import Image

T = (0, 0, 0, 0)


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def shade(c, f):
    c = rgb(c) if isinstance(c, str) else c
    return tuple(max(0, min(255, int(v * f))) for v in c[:3]) + (255,)


def mix(a, b, t):
    a = rgb(a) if isinstance(a, str) else a
    b = rgb(b) if isinstance(b, str) else b
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,)


def new(fill=T):
    return Image.new('RGBA', (16, 16), fill)


def rng(name):
    return random.Random(name)


def noise(img, r, base, amount=0.12):
    for y in range(16):
        for x in range(16):
            img.putpixel((x, y), shade(base, 1 + r.uniform(-amount, amount)))


# ---------------------------------------------------------------- building blocks

def stone(name, base, amount=0.12, specks=None):
    r = rng(name); img = new(); noise(img, r, base, amount)
    if specks:
        for _ in range(14):
            img.putpixel((r.randrange(16), r.randrange(16)), shade(specks, r.uniform(0.9, 1.1)))
    return img


def bricks(name, base, mortar, rows=4, length=8, amount=0.1, accent=None):
    """Running-bond bricks. rows=4 -> 4px tall bricks."""
    r = rng(name); img = new(); h = 16 // rows
    for y in range(16):
        row = y // h
        off = (length // 2) * (row % 2)
        for x in range(16):
            if y % h == h - 1 or (x + off) % length == length - 1:
                img.putpixel((x, y), shade(mortar, r.uniform(0.95, 1.05)))
            else:
                f = 1 + r.uniform(-amount, amount)
                if y % h == 0:
                    f += 0.08
                img.putpixel((x, y), shade(base, f))
    if accent:
        for _ in range(5):
            img.putpixel((r.randrange(16), r.randrange(16)), shade(accent, 1))
    return img


def tiles(name, a, b, grout, size=4, checker=True):
    r = rng(name); img = new()
    for y in range(16):
        for x in range(16):
            if x % size == size - 1 or y % size == size - 1:
                img.putpixel((x, y), shade(grout, r.uniform(0.95, 1.05)))
            else:
                c = a if (not checker or ((x // size + y // size) % 2 == 0)) else b
                f = 1.08 if (x % size == 0 or y % size == 0) else r.uniform(0.94, 1.04)
                img.putpixel((x, y), shade(c, f))
    return img


def mosaic(name, colors, grout):
    r = rng(name); img = new()
    for by in range(0, 16, 2):
        for bx in range(0, 16, 2):
            c = r.choice(colors)
            for y in range(by, by + 2):
                for x in range(bx, bx + 2):
                    img.putpixel((x, y), shade(c, r.uniform(0.92, 1.06)) if (x + y) % 3 else shade(grout, 1))
    # a sunflower in the middle (Dressrosa)
    for (x, y) in [(7, 5), (8, 5), (6, 6), (9, 6), (6, 7), (9, 7), (7, 8), (8, 8), (5, 6), (10, 7), (7, 4), (8, 9)]:
        img.putpixel((x, y), shade('#f2c522', 1.05))
    for (x, y) in [(7, 6), (8, 6), (7, 7), (8, 7)]:
        img.putpixel((x, y), shade('#7a4a1c', 1))
    return img


def roof_tiles(name, base):
    """Japanese kawara roof: rounded rows of tiles."""
    r = rng(name); img = new()
    for y in range(16):
        for x in range(16):
            col = x % 4
            row = y % 4
            f = [0.85, 1.12, 1.05, 0.9][col] * (0.75 if row == 3 else 1.0)
            img.putpixel((x, y), shade(base, f * r.uniform(0.96, 1.04)))
    return img


def planks(name, base, grain=None):
    r = rng(name); img = new(); grain = grain or shade(base, 0.8)
    for y in range(16):
        board = y // 4
        for x in range(16):
            f = r.uniform(0.94, 1.04) - 0.04 * (board % 2)
            img.putpixel((x, y), shade(base, f))
        if y % 4 == 3:
            for x in range(16):
                img.putpixel((x, y), shade(base, 0.7))
    for board in range(4):
        x = (board * 7 + 3) % 16
        img.putpixel((x, board * 4 + 1), shade(base, 0.72))
        for _ in range(3):
            img.putpixel((r.randrange(16), board * 4 + r.randrange(3)), shade(grain, r.uniform(0.95, 1.05)))
    return img


def log_side(name, bark, dark=None):
    r = rng(name); img = new(); dark = dark or shade(bark, 0.7)
    stripes = [r.uniform(0.85, 1.12) for _ in range(16)]
    for y in range(16):
        for x in range(16):
            f = stripes[x] * r.uniform(0.95, 1.05)
            img.putpixel((x, y), shade(bark, f))
    for _ in range(10):
        x = r.randrange(16); y = r.randrange(15)
        img.putpixel((x, y), shade(dark, 1)); img.putpixel((x, y + 1), shade(dark, 1.05))
    return img


def log_top(name, bark, wood):
    r = rng(name); img = new()
    for y in range(16):
        for x in range(16):
            d = max(abs(x - 7.5), abs(y - 7.5))
            if d > 6.5:
                img.putpixel((x, y), shade(bark, r.uniform(0.9, 1.05)))
            else:
                ring = int(d) % 2
                img.putpixel((x, y), shade(wood, (0.88 if ring else 1.02) * r.uniform(0.97, 1.03)))
    return img


def leaves(name, base, blossom=None, density=0.78):
    r = rng(name); img = new()
    for y in range(16):
        for x in range(16):
            if r.random() < density:
                c = blossom if (blossom and r.random() < 0.35) else base
                img.putpixel((x, y), shade(c, r.uniform(0.75, 1.15)))
    return img


def glass(name, frame, tint, alpha=90):
    r = rng(name); img = new()
    t = rgb(tint)
    for y in range(16):
        for x in range(16):
            if x in (0, 15) or y in (0, 15):
                img.putpixel((x, y), shade(frame, r.uniform(0.95, 1.05)))
            else:
                img.putpixel((x, y), t + (alpha,))
    # shine streaks
    for i in range(4):
        img.putpixel((3 + i, 6 - i), (255, 255, 255, 170))
        img.putpixel((9 + i, 12 - i), (255, 255, 255, 150))
    # bubbles
    for (cx, cy) in [(11, 4), (5, 11)]:
        for (dx, dy) in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            img.putpixel((cx + dx, cy + dy), (255, 255, 255, 200))
    return img


def pane_top(frame):
    img = new()
    for y in range(16):
        for x in (7, 8):
            img.putpixel((x, y), shade(frame, 1))
    return img


def bars(name, color):
    r = rng(name); img = new()
    for y in range(16):
        for x in (1, 2, 6, 7, 11, 12):
            img.putpixel((x, y), shade(color, 1.1 if x % 5 in (1, 6) else 0.8))
        if y in (1, 14):
            for x in range(16):
                img.putpixel((x, y), shade(color, 0.9))
    return img


def panel(name, base, line, light=None):
    r = rng(name); img = new(); noise(img, r, base, 0.03)
    for i in range(16):
        img.putpixel((i, 0), shade(line, 1)); img.putpixel((i, 15), shade(line, 0.8))
        img.putpixel((0, i), shade(line, 1)); img.putpixel((15, i), shade(line, 0.8))
    for i in range(3, 13):
        img.putpixel((i, 8), shade(line, 1.1))
    if light:
        for y in range(4, 12):
            for x in range(4, 12):
                img.putpixel((x, y), shade(light, 1.15 - 0.03 * abs(x - 7.5)))
    for (x, y) in [(2, 2), (13, 2), (2, 13), (13, 13)]:
        img.putpixel((x, y), shade(line, 0.6))
    return img


def tatami(name, top):
    r = rng(name); img = new()
    for y in range(16):
        for x in range(16):
            img.putpixel((x, y), shade(top, (1.05 if y % 2 else 0.95) * r.uniform(0.97, 1.03)))
    for y in range(16):
        img.putpixel((0, y), shade('#2b3d2a', 1)); img.putpixel((15, y), shade('#2b3d2a', 1))
    return img


def shoji(name):
    img = new((245, 240, 222, 255))
    for i in range(16):
        for k in (0, 5, 10, 15):
            img.putpixel((k, i), shade('#7b5532', 1)); img.putpixel((i, k), shade('#7b5532', 1))
    return img


def barrel_side(name, wood, band):
    img = planks(name, wood).transpose(Image.Transpose.ROTATE_90)
    for x in range(16):
        for y in (2, 3, 12, 13):
            img.putpixel((x, y), shade(band, 1.0 if y in (2, 12) else 0.8))
    return img


def barrel_top(name, wood, label=None):
    r = rng(name); img = new()
    for y in range(16):
        for x in range(16):
            img.putpixel((x, y), shade(wood, r.uniform(0.9, 1.05) * (0.75 if x in (0, 15) or y in (0, 15) else 1)))
    if label:
        for y in range(5, 11):
            for x in range(5, 11):
                img.putpixel((x, y), shade(label, 1))
    return img


def crate_side(name, wood, fill, fill2=None):
    r = rng(name); img = new()
    for y in range(16):
        for x in range(16):
            edge = x in (0, 15) or y in (0, 15) or x == y or x == 15 - y
            if edge:
                img.putpixel((x, y), shade(wood, r.uniform(0.8, 0.95)))
            else:
                c = fill2 if (fill2 and r.random() < 0.3) else fill
                img.putpixel((x, y), shade(c, r.uniform(0.85, 1.1)))
    return img


def coins(name):
    r = rng(name); img = new()
    noise(img, r, '#b98a1c', 0.1)
    for _ in range(18):
        cx, cy = r.randrange(1, 15), r.randrange(1, 15)
        for (dx, dy) in [(0, 0), (1, 0), (0, 1), (1, 1)]:
            if 0 <= cx + dx < 16 and 0 <= cy + dy < 16:
                img.putpixel((cx + dx, cy + dy), shade('#f5cf45', 1.1 if dx == dy == 0 else 0.95))
    return img


def candy_stripes(name, a='#f4f0ec', b='#d42a2a'):
    img = new()
    for y in range(16):
        for x in range(16):
            img.putpixel((x, y), shade(b if ((x + y) // 3) % 2 else a, 1))
    return img


def frosting(name):
    r = rng(name); img = new(); noise(img, r, '#fbe3ef', 0.04)
    for _ in range(12):
        img.putpixel((r.randrange(16), r.randrange(16)), shade(r.choice(['#e8467c', '#4fb6e8', '#f2d43c', '#6ad35b']), 1))
    return img


def cookie(name):
    img = bricks(name, '#c58a46', '#7b4a1e', rows=2, length=8, amount=0.06)
    r = rng(name + 'chips')
    for _ in range(10):
        img.putpixel((r.randrange(16), r.randrange(16)), shade('#3d2414', 1))
    return img


# ---------------------------------------------------------------- doors and wood bits

def door_half(name, wood, top):
    r = rng(name); img = new()
    for y in range(16):
        for x in range(16):
            img.putpixel((x, y), shade(wood, r.uniform(0.92, 1.05) * (0.8 if x in (0, 15) or y in (0, 15) else 1)))
    if top:
        for y in range(3, 10):
            for x in range(3, 13):
                if x in (7, 8) or y == 6:
                    continue
                img.putpixel((x, y), T)
    else:
        img.putpixel((12, 6), shade('#d8c27a', 1)); img.putpixel((12, 7), shade('#a08a4a', 1))
        for x in range(3, 13):
            img.putpixel((x, 10), shade(wood, 0.75))
    return img


def trapdoor(name, wood):
    r = rng(name); img = new()
    for y in range(16):
        for x in range(16):
            if x in (0, 1, 14, 15) or y in (0, 1, 14, 15) or x in (7, 8) or y in (7, 8):
                img.putpixel((x, y), shade(wood, r.uniform(0.85, 1.0)))
            elif (x + y) % 5 == 0:
                img.putpixel((x, y), T)
            else:
                img.putpixel((x, y), shade(wood, r.uniform(0.95, 1.08)))
    return img


def door_item(name, wood):
    img = new()
    full = Image.new('RGBA', (16, 32))
    full.paste(door_half(name + 't', wood, True), (0, 0)); full.paste(door_half(name + 'b', wood, False), (0, 16))
    small = full.resize((8, 16), Image.Resampling.NEAREST)
    img.paste(small, (4, 0))
    return img


# ---------------------------------------------------------------- plants

def sapling(name, trunk, leaf, blossom=None):
    r = rng(name); img = new()
    for y in range(9, 16):
        img.putpixel((7, y), shade(trunk, 1)); img.putpixel((8, y), shade(trunk, 0.8))
    for y in range(1, 11):
        for x in range(2, 14):
            if (x - 7.5) ** 2 / 30 + (y - 5.5) ** 2 / 20 < 1 and r.random() < 0.85:
                c = blossom if (blossom and r.random() < 0.4) else leaf
                img.putpixel((x, y), shade(c, r.uniform(0.8, 1.15)))
    return img


def palm_sapling(name):
    img = new()
    for y in range(6, 16):
        img.putpixel((8 - (y < 10), y), shade('#8a6a3c', 1))
    for i in range(6):
        for (x, y) in [(7 - i, 5 + i // 2), (8 + i, 5 + i // 2), (7 - i // 2, 5 - i // 2), (8 + i // 2, 5 - i // 2)]:
            if 0 <= x < 16 and 0 <= y < 16:
                img.putpixel((x, y), shade('#4c9a3a', 1 - 0.04 * i))
    return img


def flower(name, petal, center, stem='#3f8a2e', size=2, glow=False):
    r = rng(name); img = new()
    for y in range(8, 16):
        img.putpixel((8, y), shade(stem, 1 if y % 2 else 0.85))
    img.putpixel((9, 12), shade(stem, 1.1)); img.putpixel((10, 11), shade(stem, 1.1))
    img.putpixel((7, 13), shade(stem, 1.1)); img.putpixel((6, 12), shade(stem, 1.1))
    cx, cy = 8, 5
    for y in range(cy - size - 1, cy + size + 2):
        for x in range(cx - size - 1, cx + size + 2):
            d = abs(x - cx) + abs(y - cy)
            if d <= size + 1 and (x, y) != (cx, cy):
                img.putpixel((x, y), shade(petal, r.uniform(0.85, 1.15) * (1.15 if glow else 1)))
    img.putpixel((cx, cy), shade(center, 1))
    return img


def lotus(name, petal, pad):
    img = new()
    for y in range(12, 15):
        for x in range(2, 14):
            if (x - 7.5) ** 2 / 36 + (y - 13) ** 2 / 2.5 < 1:
                img.putpixel((x, y), shade(pad, 1 - 0.05 * (y - 12)))
    for (x, y) in [(5, 10), (6, 9), (6, 10), (7, 8), (8, 8), (7, 9), (8, 9), (9, 9), (9, 10), (10, 10), (7, 10), (8, 10), (7, 7), (8, 7)]:
        img.putpixel((x, y), shade(petal, 1.05 if y < 9 else 0.95))
    img.putpixel((7, 11), shade('#f2d43c', 1)); img.putpixel((8, 11), shade('#f2d43c', 1))
    return img


def puff(name, color):
    r = rng(name); img = new()
    for y in range(9, 16):
        img.putpixel((8, y), shade('#9fb7a0', 1))
    for y in range(1, 10):
        for x in range(3, 13):
            if (x - 7.5) ** 2 + (y - 5) ** 2 < 18 and r.random() < 0.9:
                img.putpixel((x, y), shade(color, r.uniform(0.9, 1.05)))
    return img


def mushroom(name, cap, glow):
    r = rng(name); img = new()
    for y in range(9, 16):
        img.putpixel((7, y), shade('#d9d4c2', 1)); img.putpixel((8, y), shade('#bcb6a2', 1))
    for y in range(4, 10):
        for x in range(2, 14):
            if (x - 7.5) ** 2 / 30 + (y - 9) ** 2 / 25 < 1 and y < 10:
                img.putpixel((x, y), shade(cap, r.uniform(0.85, 1.1)))
    for (x, y) in [(5, 6), (9, 5), (11, 8), (4, 8)]:
        img.putpixel((x, y), shade(glow, 1.2))
    return img


def candy_sprout(name):
    img = new()
    for y in range(4, 16):
        img.putpixel((8, y), shade('#f4f0ec' if (y // 2) % 2 else '#d42a2a', 1))
    for (x, y) in [(7, 3), (6, 3), (5, 4), (5, 5), (6, 3)]:
        img.putpixel((x, y), shade('#d42a2a', 1))
    img.putpixel((7, 2), shade('#f4f0ec', 1))
    return img


def lollipop(name):
    img = new()
    for y in range(9, 16):
        img.putpixel((8, y), shade('#f4f0ec', 1))
    cols = ['#e8467c', '#f2d43c', '#4fb6e8', '#6ad35b']
    for y in range(1, 10):
        for x in range(3, 13):
            d = ((x - 7.5) ** 2 + (y - 5) ** 2) ** 0.5
            if d < 4.6:
                img.putpixel((x, y), shade(cols[int(d * 1.3) % 4], 1))
    return img


def tall_bottom(name, stem, leaf):
    r = rng(name); img = new()
    for y in range(16):
        img.putpixel((8, y), shade(stem, 1)); img.putpixel((7, y), shade(stem, 0.85))
    for _ in range(40):
        x, y = r.randrange(2, 14), r.randrange(4, 16)
        if abs(x - 7.5) < (16 - y) * 0.6 + 2:
            img.putpixel((x, y), shade(leaf, r.uniform(0.8, 1.1)))
    return img


def tall_top(name, stem, leaf, bloom=None):
    r = rng(name); img = new()
    for y in range(6, 16):
        img.putpixel((8, y), shade(stem, 1)); img.putpixel((7, y), shade(stem, 0.85))
    for _ in range(45):
        x, y = r.randrange(1, 15), r.randrange(2, 16)
        img.putpixel((x, y), shade(leaf, r.uniform(0.8, 1.1)))
    if bloom:
        for y in range(1, 8):
            for x in range(3, 13):
                if (x - 7.5) ** 2 + (y - 4) ** 2 < 11:
                    img.putpixel((x, y), shade(bloom, r.uniform(0.85, 1.15)))
        img.putpixel((7, 4), shade('#f2d43c', 1)); img.putpixel((8, 4), shade('#f2d43c', 1))
    return img


def bush(name, stage, leaf, fruit):
    r = rng(name); img = new()
    h = [5, 9, 12, 13][stage]
    for _ in range(30 + stage * 25):
        x = r.randrange(2, 14); y = r.randrange(16 - h, 16)
        img.putpixel((x, y), shade(leaf, r.uniform(0.75, 1.1)))
    if stage >= 2:
        for _ in range(3 if stage == 2 else 7):
            x = r.randrange(3, 12); y = r.randrange(16 - h + 1, 14)
            c = '#9cbf3a' if stage == 2 else fruit
            img.putpixel((x, y), shade(c, 1.05)); img.putpixel((x + 1, y), shade(c, 0.95))
            img.putpixel((x, y + 1), shade(c, 0.9)); img.putpixel((x + 1, y + 1), shade(c, 0.8))
    return img


def petals(name, color):
    r = rng(name); img = new()
    for qx in (0, 8):
        for qy in (0, 8):
            for _ in range(10):
                x = qx + r.randrange(1, 7); y = qy + r.randrange(1, 7)
                img.putpixel((x, y), shade(color, r.uniform(0.85, 1.15)))
    return img


def stem(name, color):
    img = new()
    for y in range(16):
        img.putpixel((0, y), shade(color, 1))
    return img


# ---------------------------------------------------------------- lantern (fits the vanilla lantern model layout)

def lantern(name, body, frame, glow):
    img = new()
    for y in range(2, 9):            # body sides
        for x in range(0, 6):
            edge = x in (0, 5) or y in (2, 8)
            img.putpixel((x, y), shade(frame if edge else glow, 1 if edge else 1.0 + 0.04 * (3 - abs(x - 2.5))))
    for y in range(9, 15):           # top / bottom
        for x in range(0, 6):
            img.putpixel((x, y), shade(body, 0.9 if x in (0, 5) or y in (9, 14) else 1.05))
    for y in range(0, 2):            # cap sides
        for x in range(1, 5):
            img.putpixel((x, y), shade(frame, 0.9))
    for y in range(10, 14):          # cap top
        for x in range(1, 5):
            img.putpixel((x, y), shade(frame, 1))
    for y in range(1, 12):           # handle
        for x in range(11, 14):
            if y in (1, 2, 4, 6, 7, 11) or x in (11, 13):
                img.putpixel((x, y), shade(frame, 0.8))
    return img


def lantern_item(body_img):
    img = new()
    side = body_img.crop((0, 2, 6, 9)).resize((8, 10), Image.Resampling.NEAREST)
    img.paste(side, (4, 5))
    cap = body_img.crop((1, 0, 5, 2)).resize((6, 2), Image.Resampling.NEAREST)
    img.paste(cap, (5, 3))
    for y in range(0, 3):
        img.putpixel((7, y), body_img.getpixel((11, 1))); img.putpixel((8, y), body_img.getpixel((11, 1)))
    return img


# ---------------------------------------------------------------- items

def blob_item(name, color, outline, leaf=None, shine=True, rx=5, ry=5, cy=9):
    img = new()
    for y in range(16):
        for x in range(16):
            v = (x - 7.5) ** 2 / rx ** 2 + (y - cy) ** 2 / ry ** 2
            if v < 1:
                img.putpixel((x, y), shade(color, 1.1 - 0.25 * v))
            elif v < 1.35:
                img.putpixel((x, y), shade(outline, 1))
    if shine:
        img.putpixel((5, cy - 2), (255, 255, 255, 255)); img.putpixel((6, cy - 3), (255, 255, 255, 220))
    if leaf:
        for (x, y) in [(8, cy - ry - 1), (9, cy - ry - 2), (10, cy - ry - 2), (11, cy - ry - 3)]:
            if y >= 0:
                img.putpixel((x, y), shade(leaf, 1))
    return img


def onigiri():
    img = new()
    for y in range(2, 15):
        half = (y - 2) * 0.55 + 0.5
        for x in range(16):
            if abs(x - 7.5) <= half:
                img.putpixel((x, y), shade('#f6f3ea', 1 - 0.01 * y))
    for y in range(10, 15):
        for x in range(5, 11):
            img.putpixel((x, y), shade('#1f2a1d', 1))
    return img


def dango():
    img = new()
    for i in range(16):
        if 2 <= i <= 15:
            img.putpixel((i, 17 - i if 17 - i < 16 else 15), shade('#c79b5a', 1))
    for (cx, cy, c) in [(5, 10, '#f3a6c1'), (8, 7, '#f6f3ea'), (11, 4, '#9cc96b')]:
        for y in range(cy - 2, cy + 3):
            for x in range(cx - 2, cx + 3):
                if (x - cx) ** 2 + (y - cy) ** 2 <= 5:
                    img.putpixel((x, y), shade(c, 1.05 if x < cx else 0.92))
    return img


def bottle(name, glass_col, liquid, label=None):
    img = new()
    for y in range(1, 5):
        img.putpixel((7, y), shade(glass_col, 1)); img.putpixel((8, y), shade(glass_col, 0.85))
    img.putpixel((7, 0), shade('#7b5532', 1)); img.putpixel((8, 0), shade('#7b5532', 1))
    for y in range(5, 15):
        for x in range(4, 12):
            edge = x in (4, 11) or y == 14
            img.putpixel((x, y), shade(glass_col if edge else liquid, 0.9 if edge else 1.0 + 0.05 * (x < 7)))
    if label:
        for y in range(8, 12):
            for x in range(5, 11):
                img.putpixel((x, y), shade(label, 1))
    return img


def cotton_candy():
    r = rng('cotton'); img = new()
    for i in range(9, 16):
        img.putpixel((8, i), shade('#f4f0ec', 1))
    for y in range(0, 11):
        for x in range(2, 14):
            if (x - 7.5) ** 2 + (y - 5) ** 2 < 26 and r.random() < 0.92:
                img.putpixel((x, y), shade(r.choice(['#f6a8cf', '#f9c4de', '#a8d8f6']), r.uniform(0.95, 1.05)))
    return img


def resin():
    img = blob_item('resin', '#e8f6ff', '#7fb6d6', rx=4, ry=4, cy=9)
    for (x, y) in [(4, 3), (11, 4), (12, 12)]:
        img.putpixel((x, y), (200, 235, 255, 200))
    return img
