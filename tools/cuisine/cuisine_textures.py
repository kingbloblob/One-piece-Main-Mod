"""Draws the 16x16 item textures for fishing and cooking (fish, Sanji's dishes, the All Blue compass)
and the 18x18 icons of the cooking effects, from scratch.
Usage: python3 cuisine_textures.py <source folder> [preview.png]"""
import math
import os
import random
import sys

from PIL import Image

T = (0, 0, 0, 0)


def rgb(c):
    c = c.lstrip('#')
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def shade(c, f):
    c = rgb(c) if isinstance(c, str) else c
    return tuple(max(0, min(255, int(v * f))) for v in c[:3]) + (255,)


class Tex:
    def __init__(self, name, size=16):
        self.r = random.Random(name)
        self.size = size
        self.img = Image.new('RGBA', (size, size), T)

    def px(self, x, y, c, jitter=0.0):
        if 0 <= x < self.size and 0 <= y < self.size:
            self.img.putpixel((x, y), shade(c, 1 + self.r.uniform(-jitter, jitter)))

    def rect(self, x0, y0, x1, y1, c, jitter=0.06):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.px(x, y, c, jitter)

    def outline(self, c='#1a1a22'):
        """A dark 1-pixel outline around everything drawn, like vanilla items."""
        src = self.img.copy()
        for y in range(self.size):
            for x in range(self.size):
                if src.getpixel((x, y))[3] == 0 and any(
                        0 <= x + dx < self.size and 0 <= y + dy < self.size and src.getpixel((x + dx, y + dy))[3]
                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    self.img.putpixel((x, y), shade(c, 1))


# ---- Fish ----
# A fish lies diagonally like vanilla cod: head top-right, tail bottom-left.
# shape: 'fish' (normal), 'long' (eel), 'round' (puffer/sunfish), 'sword', 'lobster', 'angler', 'koi', 'fry'

FISH = {
    # id: (shape, back colour, belly colour, fin colour, extra)
    'blue_sea_bream': ('fish', '#3a78c8', '#f0a8b8', '#2a5aa0', None),
    'striped_mackerel': ('fish', '#3a6a7a', '#d8e4e8', '#2a4a5a', 'stripes'),
    'east_blue_lobster': ('lobster', '#c83a2a', '#e86a4a', '#8a2418', None),
    'calm_belt_eel': ('long', '#4a5a3a', '#c8c088', '#2e3a24', None),
    'sea_king_fry': ('fry', '#7a3a9a', '#e8c8a8', '#4a2a6a', 'spots'),
    'elephant_honmaguro': ('fish', '#5a6a8a', '#c8ccd8', '#3a4460', 'trunk'),
    'grand_line_puffer': ('round', '#d8b030', '#f4e8b0', '#8a6a20', 'spikes'),
    'rainbow_snapper': ('fish', '#e84a4a', '#f4e070', '#4a9ae8', 'rainbow'),
    'new_world_swordfish': ('sword', '#2a3a6a', '#b8c4d8', '#1a2448', None),
    'abyss_angler': ('angler', '#3a2a3a', '#6a4a5a', '#241824', None),
    'glowfin': ('fish', '#2ac8c0', '#b8f8f0', '#f0f070', 'glow'),
    'sky_fish': ('fish', '#e8f0f8', '#ffffff', '#88b8e8', 'wings'),
    'golden_koi': ('koi', '#e8a020', '#f8e8c8', '#c84a20', 'spots'),
    'frostfin_cod': ('fish', '#8ab8d8', '#eef6fa', '#5a88b0', 'frost'),
    'sandora_catfish': ('fish', '#a88a5a', '#e8d8b0', '#6a5434', 'whiskers'),
    'ghost_fish': ('fish', '#b8c0d0', '#e8ecf4', '#8890a8', 'ghost'),
    'all_blue_kingfish': ('sword', '#2a8ae8', '#f4f8ff', '#f0c030', 'crown'),
    'rainbow_sunfish': ('round', '#e86a8a', '#f8f0a0', '#6ac8e8', 'rainbow'),
}


def fish_body(t, back, belly, fin, length=10, width=3, x0=3, y0=12):
    """Draws a diagonal fish body from tail (x0, y0) towards the head, returns the head point."""
    hx, hy = x0 + length, y0 - length
    for i in range(length + 1):
        cx, cy = x0 + i, y0 - i
        w = width if 2 <= i <= length - 2 else max(1, width - 1)
        if i == length:
            w = 1
        for d in range(-w, w + 1):
            # d < 0 is the back (top-left side), d > 0 the belly.
            x, y = cx + (d if d < 0 else 0), cy + (d if d > 0 else 0)
            c = back if d < 0 else belly if d > 0 else shade(back, 1.15)
            t.px(cx - (d if d < 0 else 0) * 0 + (d if d < 0 else 0), cy + (d if d > 0 else 0), c, 0.07)
            t.px(cx + (d if d > 0 else 0), cy + (d if d < 0 else 0), c, 0.07)
    # Tail fin.
    for (dx, dy) in [(-1, 0), (-2, 0), (0, 1), (0, 2), (-2, 1), (-1, 2), (-2, 2), (-3, 1), (-1, 3)]:
        t.px(x0 + dx, y0 + dy, fin, 0.05)
    # Back and belly fins.
    mx, my = x0 + length // 2, y0 - length // 2
    for (dx, dy) in [(-width - 1, -1), (-width - 1, 0), (-width, -width - 1)]:
        t.px(mx + dx, my + dy, fin, 0.05)
    t.px(mx + width + 1, my + 1, fin); t.px(mx + 1, my + width + 1, fin)
    # Eye.
    t.px(hx - 2, hy + 1, '#ffffff'); t.px(hx - 2, hy + 2, '#101010')
    return hx, hy


def draw_fish(name):
    shape, back, belly, fin, extra = FISH[name]
    t = Tex(name)
    if shape == 'fish' or shape == 'koi':
        hx, hy = fish_body(t, back, belly, fin)
    elif shape == 'long':
        for i in range(14):
            cx, cy = 1 + i, 14 - i + int(round(math.sin(i * 0.9) * 1.2))
            for d in (-1, 0, 1):
                t.px(cx, cy + d, back if d < 0 else belly if d > 0 else shade(back, 1.2), 0.06)
        t.px(13, 2, '#ffffff'); t.px(13, 3, '#101010')
        for i in range(2, 12, 2):
            t.px(1 + i, 14 - i - 2 + int(round(math.sin(i * 0.9) * 1.2)), fin)
    elif shape == 'round':
        for y in range(16):
            for x in range(16):
                d = (x - 7.5) ** 2 / 30 + (y - 7.5) ** 2 / 26
                if d <= 1:
                    t.px(x, y, back if y < 8 - (x - 8) * 0.2 else belly, 0.06)
        t.px(11, 5, '#ffffff'); t.px(11, 6, '#101010')
        for (x, y) in [(1, 7), (0, 6), (0, 8), (7, 1), (8, 0), (7, 14), (8, 15)]:
            t.px(x, y, fin)
        if extra == 'spikes':
            for (x, y) in [(3, 2), (12, 2), (2, 12), (13, 12), (14, 7), (5, 0), (10, 0), (5, 15), (10, 15)]:
                t.px(x, y, '#f4f0d0')
    elif shape == 'sword':
        hx, hy = fish_body(t, back, belly, fin, length=9, width=2, x0=2, y0=13)
        for i in range(1, 5):
            t.px(hx + i - 1, hy - i + 1 - 1, '#d8dce8')
    elif shape == 'angler':
        for y in range(4, 15):
            for x in range(2, 15):
                d = (x - 8.5) ** 2 / 36 + (y - 9.5) ** 2 / 22
                if d <= 1:
                    t.px(x, y, back if y < 10 else belly, 0.08)
        for x in range(9, 15):
            t.px(x, 11, '#f0f0e0' if x % 2 else '#2a1a2a')  # teeth
        t.px(12, 7, '#f8f8f8'); t.px(12, 8, '#101010')
        for (x, y) in [(10, 3), (11, 2), (12, 1), (13, 1)]:
            t.px(x, y, '#5a4a5a')
        t.px(14, 1, '#f8f080'); t.px(14, 2, '#d8d060'); t.px(15, 1, '#fffcc0')
        for (x, y) in [(1, 8), (0, 7), (0, 10), (1, 11)]:
            t.px(x, y, fin)
    elif shape == 'lobster':
        for i in range(10):
            cx, cy = 3 + i, 13 - i
            for d in (-1, 0, 1):
                t.px(cx + d, cy, back if (i % 2) else shade(back, 0.85), 0.05)
        for (x, y) in [(1, 14), (2, 15), (0, 13), (1, 15), (2, 14)]:
            t.px(x, y, fin)
        for (x, y) in [(10, 1), (11, 1), (11, 2), (9, 2), (14, 5), (14, 6), (13, 6), (13, 4)]:
            t.px(x, y, belly, 0.05)  # claws
        for (x, y) in [(12, 3), (12, 2), (13, 3)]:
            t.px(x, y, back)
        for i in range(4):
            t.px(13 + i // 2, 1 - i // 3, '#f0c0a0')
        t.px(11, 4, '#101010')
    elif shape == 'fry':
        # A baby Sea King: a curled serpent with a big head.
        for a in range(0, 300, 12):
            r = 5 - a / 120
            x = 8 + r * math.cos(math.radians(a))
            y = 9 + r * math.sin(math.radians(a))
            for d in (0, 1):
                t.px(int(x) + d, int(y), back if d == 0 else belly, 0.06)
        t.rect(9, 1, 13, 4, back, 0.05)
        t.rect(12, 3, 14, 4, belly, 0.05)
        t.px(11, 2, '#f0e040'); t.px(10, 0, fin); t.px(12, 0, fin)
    # Extras.
    if extra == 'stripes':
        for i in range(3, 10, 2):
            t.px(3 + i - 2, 12 - i - 1, '#1a2a30'); t.px(3 + i - 3, 12 - i - 2, '#1a2a30')
    elif extra == 'trunk':
        t.px(14, 1, back); t.px(15, 2, back); t.px(15, 3, shade(back, 0.8))
    elif extra == 'rainbow':
        cols = ['#e84a4a', '#f0a030', '#f0e050', '#5ac84a', '#4a9ae8', '#9a5ad8']
        for y in range(16):
            for x in range(16):
                p = t.img.getpixel((x, y))
                if p[3] and p[:3] != (255, 255, 255) and p[:3] != (16, 16, 16) and (x + y) % 3 == 0:
                    t.px(x, y, cols[(x - y + 32) // 2 % len(cols)], 0.04)
    elif extra == 'spots' and shape == 'koi':
        for (x, y) in [(6, 8), (7, 9), (9, 5), (10, 6), (5, 10)]:
            t.px(x, y, '#f8f4ec')
        for (x, y) in [(8, 7), (4, 9)]:
            t.px(x, y, '#c82a1a')
    elif extra == 'spots':
        for (x, y) in [(4, 12), (11, 8), (6, 4)]:
            t.px(x, y, '#e8c040')
    elif extra == 'glow':
        for (x, y) in [(5, 10), (7, 8), (9, 6), (11, 4)]:
            t.px(x, y, '#f8ff9a')
    elif extra == 'wings':
        for (x, y) in [(6, 4), (5, 3), (4, 2), (5, 2), (6, 3), (10, 11), (11, 12), (12, 12), (11, 11)]:
            t.px(x, y, '#ffffff', 0.03)
    elif extra == 'frost':
        for (x, y) in [(5, 9), (8, 6), (10, 5), (6, 11)]:
            t.px(x, y, '#ffffff')
    elif extra == 'whiskers':
        for (x, y) in [(14, 4), (15, 5), (12, 1), (12, 0)]:
            t.px(x, y, '#3a2a1a')
    elif extra == 'ghost':
        for y in range(16):
            for x in range(16):
                p = t.img.getpixel((x, y))
                if p[3]:
                    t.img.putpixel((x, y), p[:3] + (175,))
        t.px(11, 3, '#30d0a0')
    elif extra == 'crown':
        for (x, y) in [(9, 1), (10, 0), (11, 1), (12, 0), (13, 1), (10, 1), (11, 0), (12, 1)]:
            t.px(x, y, '#f8d040')
    t.outline()
    return t.img


# ---- Dishes ----

PLATE, RIM = '#e8e6df', '#b8b4aa'


def plate(t, y0=10):
    for y in range(y0, y0 + 4):
        w = [6, 7, 6, 4][y - y0]
        t.rect(8 - w, y, 7 + w, y, PLATE if y < y0 + 2 else RIM, 0.02)


def bowl(t, soup, y0=7, wood='#8a5a32'):
    t.rect(2, y0, 13, y0, soup, 0.1)
    for y in range(y0 + 1, y0 + 7):
        w = [6, 6, 5, 5, 4, 3][y - y0 - 1]
        t.rect(8 - w, y, 7 + w, y, wood, 0.05)
    t.rect(1, y0 - 1, 14, y0 - 1, shade(soup, 1.1), 0.1)


def pot(t, soup):
    t.rect(1, 6, 14, 6, '#4a4a50', 0.03)
    t.rect(2, 5, 13, 5, soup, 0.12)
    t.rect(2, 7, 13, 13, '#3a3a40', 0.05)
    t.rect(0, 7, 0, 8, '#4a4a50'); t.rect(15, 7, 15, 8, '#4a4a50')


def fish_on_plate(t, fish, cooked=None):
    plate(t)
    for i in range(9):
        for d in (-1, 0, 1):
            c = cooked or (fish if d < 0 else shade(fish, 1.3))
            t.px(3 + i, 9 - i // 3 + d + (1 if i > 6 else 0), c, 0.08)
    t.px(12, 7, '#ffffff')


def dish(name):
    t = Tex(name)
    if name == 'grilled_fish':
        fish_body(t, '#8a5228', '#d8a060', '#6a3a1a')
        for i in range(3, 10, 2):
            t.px(3 + i - 1, 12 - i - 1, '#3a1a0a'); t.px(3 + i, 12 - i + 1, '#3a1a0a')
    elif name == 'sea_bream_sashimi':
        plate(t)
        for k, x in enumerate((3, 6, 9)):
            t.rect(x, 7 - (k % 2), x + 2, 9 - (k % 2), '#f4a8b0', 0.06)
            t.px(x, 7 - (k % 2), '#ffffff')
        t.rect(11, 8, 12, 9, '#5aa83a'); t.px(13, 9, '#f0f0f0')
    elif name == 'lobster_bisque':
        bowl(t, '#e8783a')
        t.px(5, 5, '#c83a2a'); t.px(6, 4, '#c83a2a'); t.px(10, 5, '#f4e8d8')
    elif name == 'seafood_fried_rice':
        plate(t)
        for y in range(5, 10):
            w = [2, 4, 5, 6, 6][y - 5]
            t.rect(8 - w, y, 7 + w, y, '#f0d890', 0.12)
        for (x, y) in [(5, 7), (9, 6), (7, 8), (11, 8)]:
            t.px(x, y, '#e86a4a')
        for (x, y) in [(6, 6), (10, 8), (4, 8)]:
            t.px(x, y, '#5aa83a')
        t.px(8, 5, '#f8e040')
    elif name == 'eel_kabayaki':
        t.rect(1, 9, 14, 13, '#2a1a1a', 0.03)  # lacquer box
        t.rect(2, 9, 13, 9, '#f4f0e4', 0.04)
        t.rect(2, 7, 13, 8, '#8a4a1a', 0.12)
        for x in range(3, 13, 3):
            t.px(x, 7, '#5a2a0a')
    elif name == 'sea_king_barbecue':
        for i in range(12):
            t.px(2 + i, 13 - i, '#8a6a3a')  # skewer
        for (cx, cy) in [(5, 10), (8, 7), (11, 4)]:
            t.rect(cx - 2, cy - 1, cx + 1, cy + 2, '#9a3a2a', 0.12)
            t.px(cx - 1, cy, '#d86a3a'); t.px(cx, cy + 1, '#5a1a10')
    elif name == 'elephant_tuna_sushi':
        plate(t)
        for x in (3, 9):
            t.rect(x, 7, x + 4, 9, '#f4f0e4', 0.04)
            t.rect(x, 5, x + 4, 6, '#d84a5a', 0.08)
            t.px(x + 2, 6, '#f8a0a8')
    elif name == 'puffer_hot_pot':
        pot(t, '#e8d8a0')
        t.px(5, 4, '#d8b030'); t.px(6, 4, '#d8b030'); t.px(9, 4, '#f08a30'); t.px(11, 5, '#5aa83a')
        for (x, y) in [(5, 2), (8, 1), (11, 2)]:
            t.px(x, y, '#e8e8f0')
    elif name == 'rainbow_snapper_carpaccio':
        plate(t)
        cols = ['#e84a4a', '#f0a030', '#f0e050', '#5ac84a', '#4a9ae8']
        for k, c in enumerate(cols):
            t.rect(2 + k * 2 + (k > 2), 7 + (k % 2), 3 + k * 2 + (k > 2), 9, c, 0.05)
        t.px(12, 7, '#f39a2a'); t.px(13, 8, '#f39a2a')
    elif name == 'swordfish_steak':
        fish_on_plate(t, '#2a3a6a', '#8a4a2a')
        for i in range(0, 8, 3):
            t.px(4 + i, 9 - i // 3, '#3a1a0a')
        t.px(13, 5, '#d8dce8'); t.px(14, 4, '#d8dce8')
    elif name == 'angler_lantern_soup':
        bowl(t, '#3a6a7a')
        t.px(7, 5, '#f8f080'); t.px(8, 5, '#fffcc0'); t.px(7, 4, '#5a4a5a'); t.px(6, 3, '#5a4a5a')
    elif name == 'glowfin_stew':
        bowl(t, '#2ac8c0')
        for (x, y) in [(4, 6), (7, 5), (11, 6)]:
            t.px(x, y, '#f8ff9a')
        t.px(9, 6, '#2a8a3a')
    elif name == 'sky_fish_skewers':
        for i in range(14):
            t.px(1 + i, 14 - i, '#8a6a3a')
        for (cx, cy) in [(5, 10), (9, 6)]:
            t.rect(cx - 1, cy - 1, cx + 1, cy + 1, '#f0e8d8', 0.06)
            t.px(cx + 2, cy - 1, '#ffffff'); t.px(cx - 2, cy + 1, '#88b8e8')
    elif name == 'golden_koi_oden':
        pot(t, '#c8a05a')
        t.rect(4, 2, 5, 5, '#f4f0d0', 0.04)  # daikon
        t.rect(7, 3, 9, 5, '#e8a020', 0.06)  # koi cake
        t.px(11, 4, '#f8f8f0'); t.px(12, 4, '#f8e040')  # egg
        t.px(10, 1, '#8a6a3a'); t.px(9, 2, '#8a6a3a')
    elif name == 'frostfin_hot_pot':
        pot(t, '#e86a3a')
        for (x, y) in [(4, 4), (7, 4), (10, 4)]:
            t.px(x, y, '#eef6fa'); t.px(x + 1, y, '#8ab8d8')
        for (x, y) in [(5, 2), (8, 1), (11, 2), (6, 0)]:
            t.px(x, y, '#e0e0e8')
    elif name == 'sandora_catfish_kebab':
        for i in range(14):
            t.px(1 + i, 14 - i, '#8a6a3a')
        for k, (cx, cy) in enumerate([(4, 11), (7, 8), (10, 5)]):
            t.rect(cx - 1, cy - 1, cx + 1, cy + 1, '#c88a4a' if k != 1 else '#e8c040', 0.1)
        t.px(12, 2, '#5aa83a')
    elif name == 'ghost_fish_soup':
        bowl(t, '#c8d0e0')
        for (x, y) in [(6, 4), (7, 3), (8, 4), (7, 2)]:
            t.px(x, y, '#f4f8ff')
        t.px(7, 3, '#30d0a0')
    elif name == 'all_blue_full_course':
        plate(t, 11)
        t.rect(3, 8, 6, 10, '#f4a8b0', 0.05)  # sashimi
        t.rect(9, 7, 12, 10, '#9a3a2a', 0.1)  # sea king
        t.px(10, 7, '#d86a3a')
        t.rect(6, 5, 9, 7, '#2a8ae8', 0.05)  # kingfish
        t.px(8, 5, '#ffffff')
        for (x, y) in [(7, 3), (6, 2), (8, 2), (9, 3), (7, 2)]:
            t.px(x, y, '#f8d040')
    t.outline()
    return t.img


DISHES = ['grilled_fish', 'sea_bream_sashimi', 'lobster_bisque', 'seafood_fried_rice', 'eel_kabayaki',
          'sea_king_barbecue', 'elephant_tuna_sushi', 'puffer_hot_pot', 'rainbow_snapper_carpaccio',
          'swordfish_steak', 'angler_lantern_soup', 'glowfin_stew', 'sky_fish_skewers', 'golden_koi_oden',
          'frostfin_hot_pot', 'sandora_catfish_kebab', 'ghost_fish_soup', 'all_blue_full_course']


def compass():
    """The All Blue compass base frame: a seashell-blue case. The needle is drawn per frame."""
    frames = []
    for f in range(32):
        t = Tex('all_blue_compass')
        for y in range(16):
            for x in range(16):
                d = (x - 7.5) ** 2 + (y - 7.5) ** 2
                if d <= 49:
                    t.px(x, y, '#2a6aa8' if d > 30 else '#cfe8f4', 0.04)
        for (x, y) in [(7, 1), (8, 1), (1, 7), (14, 8)]:
            t.px(x, y, '#f0c030')
        a = math.radians(f * 360 / 32 - 90)
        for r in range(0, 5):
            t.px(int(round(7.5 + math.cos(a) * r)), int(round(7.5 + math.sin(a) * r)), '#e84a4a')
            t.px(int(round(7.5 - math.cos(a) * r * 0.6)), int(round(7.5 - math.sin(a) * r * 0.6)), '#3a3a4a')
        t.px(7, 7, '#f0c030')
        t.outline()
        frames.append(t.img)
    return frames


def effect_icon(name):
    t = Tex(name, 18)
    if name == 'well_fed':
        # A drumstick on a plate.
        for y in range(11, 16):
            w = [8, 8, 7, 5, 3][y - 11]
            t.rect(9 - w, y, 8 + w, y, '#e8e6df' if y < 14 else '#b8b4aa', 0.02)
        for i in range(8):
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    if abs(dx) + abs(dy) <= 3:
                        t.px(5 + i + dx, 10 - i + dy, '#8a3e22' if dx + dy < 1 else '#b45a2e', 0.08)
        for (x, y) in [(13, 2), (14, 1), (12, 1), (14, 3)]:
            t.px(x, y, '#f2ecd8')
    else:
        # warm_belly: a steaming bowl.
        for y in range(9, 16):
            w = [8, 8, 7, 6, 5, 4, 3][y - 9]
            t.rect(9 - w, y, 8 + w, y, '#e86a3a' if y == 9 else '#8a5a32', 0.05)
        for (x, y) in [(5, 6), (6, 5), (5, 4), (9, 6), (10, 5), (9, 4), (9, 3), (13, 6), (12, 5), (13, 4)]:
            t.px(x, y, '#f0f0f4', 0.03)
    t.outline()
    return t.img


def main():
    root = sys.argv[1]
    item = os.path.join(root, 'src/main/resources/assets/onepiece/textures/item')
    effect = os.path.join(root, 'src/main/resources/assets/onepiece/textures/mob_effect')
    os.makedirs(item, exist_ok=True)
    os.makedirs(effect, exist_ok=True)
    images = []
    for name in FISH:
        img = draw_fish(name)
        img.save(os.path.join(item, name + '.png'))
        images.append(img)
    for name in DISHES:
        img = dish(name)
        img.save(os.path.join(item, name + '.png'))
        images.append(img)
    for i, img in enumerate(compass()):
        img.save(os.path.join(item, 'all_blue_compass_%02d.png' % i))
        if i == 0:
            images.append(img)
    for name in ('well_fed', 'warm_belly'):
        effect_icon(name).save(os.path.join(effect, name + '.png'))
    if len(sys.argv) > 2:
        cols = 10
        rows = (len(images) + cols - 1) // cols
        sheet = Image.new('RGBA', (cols * 72 + 8, rows * 72 + 8), (70, 70, 76, 255))
        for i, img in enumerate(images):
            big = img.resize((64, 64), Image.NEAREST)
            sheet.paste(big, (8 + (i % cols) * 72, 8 + (i // cols) * 72), big)
        sheet.save(sys.argv[2])
    print('wrote', len(FISH), 'fish,', len(DISHES), 'dishes, compass and 2 effect icons')


if __name__ == '__main__':
    main()
