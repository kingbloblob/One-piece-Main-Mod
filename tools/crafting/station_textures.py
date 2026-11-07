"""Draws the 16x16 textures of the 5 crafting stations (front, side, top, bottom each), from scratch.
Usage: python3 station_textures.py <source folder> [preview.png]
Writes src/main/resources/assets/onepiece/textures/block/station/<station>_<face>.png."""
import os
import random
import sys

from PIL import Image

T = (0, 0, 0, 0)


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def shade(c, f):
    c = rgb(c) if isinstance(c, str) else c
    return tuple(max(0, min(255, int(v * f))) for v in c[:3]) + (255,)


class Tex:
    def __init__(self, name):
        self.r = random.Random(name)
        self.img = Image.new('RGBA', (16, 16), T)

    def px(self, x, y, c, jitter=0.0):
        if 0 <= x < 16 and 0 <= y < 16:
            self.img.putpixel((x, y), shade(c, 1 + self.r.uniform(-jitter, jitter)))

    def rect(self, x0, y0, x1, y1, c, jitter=0.06):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.px(x, y, c, jitter)

    def frame(self, x0, y0, x1, y1, c):
        for x in range(x0, x1 + 1):
            self.px(x, y0, c, 0.04); self.px(x, y1, shade(c, 0.8), 0.04)
        for y in range(y0, y1 + 1):
            self.px(x0, y, c, 0.04); self.px(x1, y, shade(c, 0.8), 0.04)

    def planks(self, base, horizontal=True, size=4):
        for y in range(16):
            for x in range(16):
                a, b = (y, x) if horizontal else (x, y)
                row = a // size
                f = 1 + self.r.uniform(-0.05, 0.05) + (0.06 if row % 2 else -0.02)
                c = shade(base, f)
                if a % size == size - 1:
                    c = shade(base, 0.62)
                elif (b + row * 5) % 11 == 0 and a % size == 1:
                    c = shade(base, 0.75)  # a knot
                self.px(x, y, c)

    def bricks(self, base, mortar, h=4, length=8):
        for y in range(16):
            off = (length // 2) * ((y // h) % 2)
            for x in range(16):
                if y % h == h - 1 or (x + off) % length == length - 1:
                    self.px(x, y, mortar, 0.05)
                else:
                    self.px(x, y, shade(base, 1.08 if y % h == 0 else 1.0), 0.09)

    def stone(self, base, amount=0.1):
        for y in range(16):
            for x in range(16):
                self.px(x, y, base, amount)


# ---------------------------------------------------------------- Shipwright's Bench (wood, ship tools)
OAK, DARK, ROPE, IRON = '#a0763f', '#5e3f1e', '#c9a86a', '#9aa1a8'


def shipwright_top():
    t = Tex('sw_top'); t.planks(OAK)
    t.frame(0, 0, 15, 15, DARK)
    # Ship plan pinned to the bench: a little hull outline on paper.
    t.rect(2, 2, 9, 7, '#e8dcb5', 0.03)
    for x in range(3, 9):
        t.px(x, 5 + (1 if x in (3, 8) else 0), '#3a5a8a')
    t.px(5, 3, '#3a5a8a'); t.px(5, 4, '#3a5a8a'); t.px(6, 3, '#b03030')
    # Saw.
    for x in range(10, 15):
        t.px(x, 10, IRON); t.px(x, 11, shade(IRON, 0.8) if x % 2 else IRON)
    t.rect(8, 10, 9, 11, DARK, 0.02)
    # Rope coil.
    for (x, y) in [(3, 11), (4, 10), (5, 10), (6, 11), (6, 12), (5, 13), (4, 13), (3, 12), (4, 11), (5, 12)]:
        t.px(x, y, ROPE, 0.06)
    return t.img


def shipwright_side():
    t = Tex('sw_side'); t.planks(OAK, horizontal=False)
    t.rect(0, 0, 15, 1, DARK); t.rect(0, 14, 15, 15, DARK)
    # Hanging hammer and mallet on pegs.
    t.px(4, 3, DARK); t.rect(4, 4, 4, 10, '#7a5530', 0.03); t.rect(2, 4, 6, 5, IRON, 0.05)
    t.px(11, 3, DARK); t.rect(11, 4, 11, 10, '#7a5530', 0.03); t.rect(9, 9, 13, 11, '#8a6a3a', 0.05)
    return t.img


def shipwright_front():
    t = Tex('sw_front'); t.planks(OAK)
    t.rect(0, 0, 15, 1, DARK); t.rect(0, 14, 15, 15, DARK); t.rect(0, 0, 0, 15, DARK); t.rect(15, 0, 15, 15, DARK)
    # Drawer.
    t.frame(2, 9, 13, 12, DARK); t.rect(7, 10, 8, 11, '#d4af37', 0.02)
    # Ship's wheel emblem: a rim, a hub and spokes poking out past the rim.
    cx, cy = 8, 4
    for (dx, dy) in [(-1, -2), (0, -2), (1, -2), (-1, 2), (0, 2), (1, 2), (-2, -1), (-2, 0), (-2, 1), (2, -1), (2, 0), (2, 1)]:
        t.px(cx + dx, cy + dy, '#7a5530', 0.03)
    for (dx, dy) in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
        t.px(cx + dx, cy + dy, shade(OAK, 1.15))
    t.px(cx, cy, '#d4af37')
    for (dx, dy) in [(0, -3), (0, 3), (-3, 0), (3, 0), (-2, -2), (2, -2), (-2, 2), (2, 2)]:
        t.px(cx + dx, cy + dy, DARK)
    return t.img


# ---------------------------------------------------------------- Ship's Galley (brick stove)
BRICK, MORTAR, STEEL = '#9c4a35', '#b9ab96', '#4a4f55'


def galley_top():
    t = Tex('ga_top'); t.stone(STEEL, 0.06)
    t.frame(0, 0, 15, 15, '#2c3035')
    # Two burners with glowing rings and a pot on one.
    for (cx, cy) in [(4, 11), (11, 11)]:
        for (dx, dy) in [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, -1), (-1, 1), (1, 1)]:
            t.px(cx + dx, cy + dy, '#e0602a', 0.1)
        t.px(cx, cy, '#1d1f22')
    t.rect(2, 2, 9, 7, '#2b2b2b', 0.04); t.rect(3, 3, 8, 6, '#c9733a', 0.12)  # pot of stew
    t.px(4, 4, '#e8b060'); t.px(7, 5, '#7a9a3a')
    t.rect(11, 2, 13, 3, '#c8c8c8', 0.04); t.rect(12, 4, 12, 7, '#8a6a3a', 0.03)  # ladle
    return t.img


def galley_side():
    t = Tex('ga_side'); t.bricks(BRICK, MORTAR)
    t.rect(0, 0, 15, 1, STEEL, 0.04)
    # A fish hung up to dry.
    t.px(8, 2, '#3a3a3a')
    for y, w in [(3, 1), (4, 2), (5, 3), (6, 3), (7, 2), (8, 1)]:
        t.rect(8 - w // 2, y, 8 + (w - 1) // 2 + 1, y, '#7f9fb4', 0.06)
    t.rect(7, 9, 9, 9, '#5f7f94', 0.04)
    return t.img


def galley_front():
    t = Tex('ga_front'); t.bricks(BRICK, MORTAR)
    t.rect(0, 0, 15, 1, STEEL, 0.04)
    # Iron oven door with a fire inside.
    t.rect(2, 5, 13, 14, '#2a2d31', 0.04); t.frame(2, 5, 13, 14, '#5a6068')
    for y in range(8, 14):
        for x in range(4, 12):
            hot = (y - 8) / 6
            t.px(x, y, '#ffcf4a' if hot > 0.7 else '#f08a24' if hot > 0.35 else '#a03a18', 0.12)
    t.rect(4, 7, 11, 7, '#5a6068', 0.02)  # grate
    t.rect(6, 3, 9, 3, '#d4af37', 0.02)  # handle
    return t.img


# ---------------------------------------------------------------- Navigator's Desk (charts, compass)
MAHOG, PAPER, INK, GOLD = '#6b3a22', '#e8dcb5', '#2a3f66', '#d4af37'


def navigator_top():
    t = Tex('nv_top'); t.planks(MAHOG)
    # A sea chart with islands, a red route and a compass rose.
    t.rect(1, 1, 14, 14, PAPER, 0.04)
    t.rect(2, 2, 13, 13, '#c8dce0', 0.05)  # sea
    for (x, y) in [(3, 4), (4, 4), (4, 3), (10, 10), (11, 10), (11, 11), (9, 4), (10, 4)]:
        t.px(x, y, '#8aa45a', 0.05)
    for (x, y) in [(4, 5), (5, 6), (6, 7), (7, 7), (8, 6), (9, 5), (9, 7), (10, 8), (10, 9)]:
        t.px(x, y, '#b03030')
    for (dx, dy) in [(0, -2), (0, -1), (0, 1), (0, 2), (-2, 0), (-1, 0), (1, 0), (2, 0)]:
        t.px(4 + dx, 11 + dy, INK)
    t.px(4, 9, '#b03030')
    t.frame(1, 1, 14, 14, '#a8946a')
    return t.img


def navigator_side():
    t = Tex('nv_side'); t.planks(MAHOG, horizontal=False)
    t.rect(0, 0, 15, 1, shade(MAHOG, 0.6)); t.rect(0, 14, 15, 15, shade(MAHOG, 0.6))
    # Rolled charts in a rack.
    for x0 in (2, 6, 10):
        t.rect(x0, 4, x0 + 2, 11, PAPER, 0.05)
        t.rect(x0, 6, x0 + 2, 6, '#b03030', 0.02)
        t.rect(x0 + 1, 4, x0 + 1, 11, shade(PAPER, 0.85), 0.02)
    return t.img


def navigator_front():
    t = Tex('nv_front'); t.planks(MAHOG)
    t.rect(0, 0, 15, 1, shade(MAHOG, 0.6)); t.rect(0, 14, 15, 15, shade(MAHOG, 0.6))
    # Two drawers with gold handles and a brass compass inlay.
    t.frame(1, 8, 7, 12, shade(MAHOG, 0.55)); t.px(4, 10, GOLD)
    t.frame(8, 8, 14, 12, shade(MAHOG, 0.55)); t.px(11, 10, GOLD)
    for (dx, dy) in [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, -1), (-1, 1), (1, 1)]:
        t.px(8 + dx, 4 + dy, GOLD, 0.05)
    t.px(8, 3, '#b03030'); t.px(8, 4, PAPER)
    return t.img


# ---------------------------------------------------------------- Seastone Workbench (blue-grey sea prism stone)
SEA, SEA_DARK, SEA_GLOW = '#6f8f9a', '#3f5a66', '#9fe3f0'


def seastone_top():
    t = Tex('ss_top'); t.stone(SEA, 0.07)
    t.frame(0, 0, 15, 15, SEA_DARK)
    # Two Seastone ingots and a hammer on the slab.
    for y0 in (3, 7):
        t.rect(2, y0, 7, y0 + 2, '#a9c4cc', 0.05); t.rect(2, y0, 7, y0, '#cfe4ea', 0.03)
    t.rect(10, 3, 10, 12, '#7a5530', 0.03); t.rect(9, 3, 12, 5, '#4d5358', 0.04)
    for (x, y) in [(3, 12), (4, 13), (6, 12), (13, 13)]:
        t.px(x, y, SEA_GLOW, 0.05)
    return t.img


def seastone_side():
    t = Tex('ss_side'); t.stone(SEA, 0.08)
    t.rect(0, 0, 15, 2, SEA_DARK, 0.04); t.rect(0, 13, 15, 15, SEA_DARK, 0.04)
    # Glowing veins in the stone.
    for (x, y) in [(2, 5), (3, 6), (4, 6), (5, 7), (9, 4), (10, 5), (10, 6), (11, 7), (12, 8), (6, 10), (7, 11)]:
        t.px(x, y, SEA_GLOW, 0.06)
    return t.img


def seastone_front():
    t = Tex('ss_front'); t.stone(SEA, 0.08)
    t.rect(0, 0, 15, 2, SEA_DARK, 0.04); t.rect(0, 13, 15, 15, SEA_DARK, 0.04)
    # A chained pair of Seastone cuffs hanging on the front.
    for cx in (5, 10):
        for (dx, dy) in [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]:
            t.px(cx + dx, 8 + dy, '#cfe4ea', 0.04)
    for x in range(6, 10):
        t.px(x, 5 + (x % 2), '#4d5358')
    t.px(5, 6, '#4d5358'); t.px(10, 6, '#4d5358')
    for (x, y) in [(2, 11), (3, 11), (12, 4), (13, 4)]:
        t.px(x, y, SEA_GLOW)
    return t.img


# ---------------------------------------------------------------- Swordsmith's Forge (dark bricks, fire, katana)
FORGE, FORGE_MORTAR, BLADE = '#3c3a40', '#24232a', '#d8dde2'


def forge_top():
    t = Tex('fo_top'); t.bricks(FORGE, FORGE_MORTAR)
    # A bed of hot coals with a blade being heated.
    t.rect(2, 2, 13, 8, '#2a1a14', 0.05)
    for y in range(3, 8):
        for x in range(3, 13):
            if t.r.random() < 0.55:
                t.px(x, y, '#f08a24' if t.r.random() < 0.6 else '#ffcf4a', 0.1)
    for x in range(3, 13):
        t.px(x, 11, BLADE, 0.03)
    t.px(13, 11, '#c03030'); t.rect(13, 10, 13, 12, '#d4af37', 0.02); t.rect(14, 11, 15, 11, '#2a2a2a', 0.02)
    t.px(12, 11, '#ff9a40')  # the hot tip end
    return t.img


def forge_side():
    t = Tex('fo_side'); t.bricks(FORGE, FORGE_MORTAR)
    # Two crossed katana.
    for i in range(10):
        t.px(3 + i, 3 + i, BLADE, 0.03)
        t.px(12 - i, 3 + i, BLADE, 0.03)
    for (x, y) in [(2, 2), (13, 2)]:
        t.px(x, y, '#2a2a2a'); t.px(x + (1 if x < 8 else -1), y + 1, '#d4af37')
    return t.img


def forge_front():
    t = Tex('fo_front'); t.bricks(FORGE, FORGE_MORTAR)
    # A stone-framed furnace mouth: dark inside, fire and coals at the bottom.
    t.rect(3, 5, 12, 14, '#6a6670', 0.05)
    t.rect(4, 6, 11, 14, '#1a1418', 0.05)
    for x in range(4, 12):
        top = 10 + int(t.r.uniform(0, 2.5))
        for y in range(top, 15):
            t.px(x, y, '#ffe07a' if y >= 13 else '#ff9a30' if y >= 12 else '#c0441a', 0.12)
    t.rect(4, 14, 11, 14, '#3a2a20', 0.08)
    t.rect(2, 4, 13, 4, '#7c7882', 0.04)
    return t.img


def bottom(name, base, kind):
    t = Tex(name + '_bottom')
    if kind == 'planks':
        t.planks(base)
    else:
        t.stone(base, 0.08)
    return t.img


TEXTURES = {
    'shipwright_bench': (shipwright_front, shipwright_side, shipwright_top, lambda: bottom('sw', DARK, 'planks')),
    'ships_galley': (galley_front, galley_side, galley_top, lambda: bottom('ga', '#5b5550', 'stone')),
    'navigators_desk': (navigator_front, navigator_side, navigator_top, lambda: bottom('nv', shade(MAHOG, 0.7), 'planks')),
    'seastone_workbench': (seastone_front, seastone_side, seastone_top, lambda: bottom('ss', SEA_DARK, 'stone')),
    'swordsmith_forge': (forge_front, forge_side, forge_top, lambda: bottom('fo', FORGE_MORTAR, 'stone')),
}
FACES = ('front', 'side', 'top', 'bottom')


def main():
    source = sys.argv[1]
    out = os.path.join(source, 'src/main/resources/assets/onepiece/textures/block/station')
    os.makedirs(out, exist_ok=True)
    sheet = Image.new('RGBA', (len(FACES) * 16 * 8 + 40, len(TEXTURES) * 16 * 8 + 48), (40, 40, 40, 255))
    for row, (station, makers) in enumerate(TEXTURES.items()):
        for col, (face, make) in enumerate(zip(FACES, makers)):
            img = make()
            img.save(os.path.join(out, f'{station}_{face}.png'))
            sheet.paste(img.resize((128, 128), Image.NEAREST), (8 + col * 136, 8 + row * 136))
    if len(sys.argv) > 2:
        sheet.save(sys.argv[2])
    print('wrote', len(TEXTURES) * len(FACES), 'textures to', out)


if __name__ == '__main__':
    main()
