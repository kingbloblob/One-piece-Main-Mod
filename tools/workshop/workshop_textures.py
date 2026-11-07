"""Draws the 16x16 textures for the workshop feature (station upgrade trees, Dials, cooking tiers, rare drops).
Usage: python3 tools/workshop/workshop_textures.py <path to src/main/resources>"""
import math, random, sys, os
from PIL import Image

RES = sys.argv[1] if len(sys.argv) > 1 else 'src/main/resources'
ITEM = os.path.join(RES, 'assets/onepiece/textures/item')
BLOCK = os.path.join(RES, 'assets/onepiece/textures/block')
os.makedirs(ITEM, exist_ok=True); os.makedirs(BLOCK, exist_ok=True)

def img(): return Image.new('RGBA', (16, 16), (0, 0, 0, 0))
def shade(c, f): return tuple(max(0, min(255, int(v * f))) for v in c[:3]) + (255,)
def put(im, x, y, c):
    if 0 <= x < 16 and 0 <= y < 16: im.putpixel((x, y), c if len(c) == 4 else c + (255,))

def outline(im, colour=(40, 30, 25, 255)):
    src = im.copy()
    for y in range(16):
        for x in range(16):
            if src.getpixel((x, y))[3] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < 16 and 0 <= ny < 16 and src.getpixel((nx, ny))[3] > 0:
                        im.putpixel((x, y), colour); break
    return im

def dial(accent, mark):
    """A Skypiea dial shell (spiral cone, like the existing dials) with a coloured opening and a mark."""
    im = img()
    shell, dark = (232, 214, 178), (190, 160, 120)
    for y in range(3, 14):
        for x in range(2, 14):
            d = math.hypot(x - 7.5, (y - 8.5) * 1.15)
            if d < 5.6:
                ang = math.atan2(y - 8.5, x - 7.5)
                stripe = (int((d * 1.3 + ang * 1.6) * 1.0) % 3 == 0)
                put(im, x, y, dark if stripe else shell)
    # The open end of the shell, where the dial keeps its power.
    for y in range(6, 12):
        for x in range(9, 14):
            if math.hypot(x - 11, y - 9) < 2.6:
                put(im, x, y, shade(accent, 0.75 if (x + y) % 2 else 1.0))
    for (x, y) in mark:
        put(im, x, y, shade(accent, 1.25))
    put(im, 5, 6, (255, 250, 235)); put(im, 6, 5, (255, 250, 235))
    return outline(im)

def save(im, name, folder=ITEM): im.save(os.path.join(folder, name + '.png'))

save(dial((90, 200, 230), [(3, 3), (4, 2), (5, 3), (4, 4)]), 'tone_dial')            # note-blue
save(dial((235, 120, 40), [(2, 12), (3, 13), (1, 11)]), 'jet_dial')                   # orange flame
save(dial((50, 110, 220), [(3, 2), (3, 3), (2, 4), (3, 4), (4, 4)]), 'water_dial')    # water drop
save(dial((245, 245, 250), [(2, 3), (3, 3), (4, 3), (3, 2)]), 'milky_dial')           # cloud white
save(dial((140, 145, 160), [(2, 2), (3, 2), (2, 3), (3, 3)]), 'eisen_dial')           # iron grey
save(dial((120, 230, 160), [(2, 2), (3, 3), (4, 4), (5, 5)]), 'axe_dial')             # wind green
save(dial((150, 60, 200), [(2, 2), (4, 2), (3, 3), (2, 4), (4, 4)]), 'reject_dial')   # purple X

# ---- Rare drops ----
im = img()  # Sea King fang: a long curved tooth
for i in range(12):
    x = 4 + i * 0.6; y = 2 + i
    w = max(1, 3 - i // 4)
    for k in range(w):
        put(im, int(x + k), y, (245, 240, 225) if k < w - 1 else (205, 195, 175))
put(im, 4, 2, (160, 60, 60)); put(im, 5, 2, (160, 60, 60))
save(outline(im), 'sea_king_fang')

im = img()  # Ambergris: a waxy grey-gold lump
random.seed(3)
for y in range(16):
    for x in range(16):
        if math.hypot(x - 8, (y - 9) * 1.3) < 5.5 + random.random() * 0.8:
            put(im, x, y, random.choice([(196, 170, 112), (176, 152, 102), (214, 192, 138), (150, 134, 96)]))
save(outline(im), 'ambergris')

im = img()  # Dragon heartstone: a glowing red-orange gem
for y in range(16):
    for x in range(16):
        d = abs(x - 7.5) + abs(y - 8) * 0.8
        if d < 6:
            put(im, x, y, shade((255, 110, 30), 1.15 - d / 9) if (x + y) % 3 else shade((255, 200, 60), 1.0))
put(im, 6, 5, (255, 240, 200)); put(im, 7, 4, (255, 240, 200))
save(outline(im), 'dragon_heartstone')

im = img()  # Pacifista core: a steel sphere with a red lens
for y in range(16):
    for x in range(16):
        d = math.hypot(x - 7.5, y - 7.5)
        if d < 6:
            put(im, x, y, shade((150, 158, 170), 1.2 - d / 10))
for y in range(6, 10):
    for x in range(6, 10):
        if math.hypot(x - 7.5, y - 7.5) < 2.1:
            put(im, x, y, (230, 40, 40) if (x, y) != (7, 7) else (255, 180, 180))
save(outline(im), 'pacifista_core')

im = img()  # Sea King Fang Blade: a white fang-like blade on a dark hilt
for i in range(10):
    x, y = 4 + i, 11 - i
    put(im, x, y, (240, 236, 220)); put(im, x + 1, y, (210, 202, 186)); put(im, x, y - 1, (250, 248, 240))
for i in range(3):
    put(im, 2 + i, 13 - i, (70, 40, 30))
put(im, 3, 10, (60, 120, 140)); put(im, 4, 11, (60, 120, 140)); put(im, 5, 12, (60, 120, 140)); put(im, 2, 9, (60, 120, 140))
put(im, 1, 14, (180, 150, 60))
save(outline(im), 'sea_king_fang_blade')

# ---- Dishes ----
def plate(im):
    for x in range(2, 14):
        put(im, x, 13, (225, 225, 230)); put(im, x, 14, (185, 185, 195))

im = img(); plate(im)  # Takoyaki: three balls with sauce
for cx in (5, 8, 11):
    for y in range(9, 13):
        for x in range(cx - 2, cx + 2):
            if math.hypot(x - cx + 0.5, y - 10.5) < 2.0:
                put(im, x, y, (196, 132, 62) if y > 9 else (120, 60, 30))
    put(im, cx - 1, 9, (90, 160, 70))
save(outline(im), 'takoyaki')

im = img()  # Ramen bowl
for y in range(8, 14):
    for x in range(2, 14):
        if (x - 7.5) ** 2 / 36 + (y - 8) ** 2 / 30 < 1:
            put(im, x, y, (200, 60, 50) if y > 9 else (200, 60, 50))
for x in range(3, 13):
    put(im, x, 8, (240, 210, 130)); put(im, x, 7, (235, 200, 120) if x % 2 else (250, 225, 150))
put(im, 5, 6, (240, 160, 140)); put(im, 6, 6, (240, 160, 140)); put(im, 10, 6, (250, 250, 240)); put(im, 11, 6, (250, 220, 90))
for i in range(6):
    put(im, 11 + i // 2, 1 + i, (120, 80, 40))
save(outline(im), 'sea_king_ramen')

im = img()  # Kibi dango: three balls on a stick
for i in range(14):
    put(im, 2 + i // 1 if i < 13 else 14, 14 - i, (150, 110, 60)) if False else put(im, 1 + i, 14 - i, (160, 120, 70))
for (cx, cy, c) in ((5, 10, (250, 200, 210)), (8, 7, (250, 250, 240)), (11, 4, (170, 210, 120))):
    for y in range(cy - 2, cy + 2):
        for x in range(cx - 2, cx + 2):
            if math.hypot(x - cx + 0.5, y - cy + 0.5) < 2.0:
                put(im, x, y, c)
save(outline(im), 'kibi_dango')

im = img(); plate(im)  # Wedding cake slice: a pink and white wedge
for y in range(5, 13):
    for x in range(3, 3 + (y - 3) + 2):
        if x < 14:
            put(im, x, y, (250, 240, 235) if (y - 5) % 3 else (240, 140, 170))
for x in range(3, 6):
    put(im, x, 4, (240, 140, 170))
put(im, 4, 3, (220, 30, 50))
save(outline(im), 'wedding_cake_slice')

im = img(); plate(im)  # Ambergris roast: glazed meat on the bone
for y in range(6, 13):
    for x in range(3, 12):
        if math.hypot(x - 7, (y - 9.5) * 1.3) < 4.3:
            put(im, x, y, (150, 80, 40) if (x + y) % 3 else (205, 160, 70))
for i in range(3):
    put(im, 12 + i, 6 - i, (245, 240, 225))
put(im, 14, 3, (245, 240, 225)); put(im, 15, 4, (245, 240, 225))
save(outline(im), 'ambergris_roast')

im = img(); plate(im)  # Diable flambe: meat with flames on top
for y in range(9, 13):
    for x in range(3, 13):
        if math.hypot(x - 7.5, (y - 11) * 1.8) < 5:
            put(im, x, y, (140, 70, 35) if (x + y) % 2 else (170, 90, 45))
for (x, h) in ((5, 4), (7, 6), (9, 5), (11, 3)):
    for k in range(h):
        put(im, x, 8 - k, (255, 200, 60) if k < h - 2 else (255, 90, 30))
save(outline(im), 'diable_flambe')

# ---- Milky cloud block: puffy white with soft blue-grey hollows ----
random.seed(7)
im = Image.new('RGBA', (16, 16))
puffs = [(3, 4), (11, 3), (7, 9), (13, 12), (2, 13)]
for y in range(16):
    for x in range(16):
        d = min(math.hypot((x - px + 8) % 16 - 8, (y - py + 8) % 16 - 8) for px, py in puffs)
        v = 255 - int(max(0, d - 2.2) * 6) - random.randint(0, 4)
        im.putpixel((x, y), (v, v, min(255, v + 6), 255))
save(im, 'milky_cloud', BLOCK)
print('textures written')
