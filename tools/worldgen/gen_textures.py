import random, os
from PIL import Image
T = '/tmp/claude-0/sync/one-piece-mod/src/main/resources/assets/onepiece/textures'
os.makedirs(f'{T}/block', exist_ok=True); os.makedirs(f'{T}/item', exist_ok=True)
def jit(c, r, a=12):
    return tuple(max(0, min(255, v + r.randint(-a, a))) for v in c) + (255,)
def base(color, seed, a=12):
    r = random.Random(seed); im = Image.new('RGBA', (16, 16))
    for x in range(16):
        for y in range(16): im.putpixel((x, y), jit(color, r, a))
    return im, r
def ore(stone, seed, name):
    im, r = base(stone, seed)
    spots = [(3, 3), (10, 2), (6, 8), (12, 10), (2, 12), (8, 13)]
    for sx, sy in spots:
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (-1, 0)):
            x, y = sx + dx, sy + dy
            if 0 <= x < 16 and 0 <= y < 16:
                im.putpixel((x, y), jit((40, 120, 140) if (dx + dy) % 2 else (70, 170, 185), r, 8))
    im.save(f'{T}/block/{name}.png')
ore((125, 125, 125), 1, 'seastone_ore')
ore((72, 72, 78), 2, 'deepslate_seastone_ore')
im, r = base((58, 120, 132), 3, 8)
for i in range(16): im.putpixel((i, 0), (90, 160, 170, 255)); im.putpixel((0, i), (90, 160, 170, 255)); im.putpixel((i, 15), (35, 80, 90, 255)); im.putpixel((15, i), (35, 80, 90, 255))
im.save(f'{T}/block/seastone_block.png')
im, r = base((92, 58, 34), 4, 10)
for x in (2, 6, 11, 14):
    for y in range(16): im.putpixel((x, y), jit((62, 38, 22), r, 6))
im.save(f'{T}/block/adam_log.png')
im, r = base((178, 128, 78), 5, 8)
for y in range(16):
    for x in range(16):
        d = max(abs(x - 7.5), abs(y - 7.5))
        if int(d) % 3 == 0: im.putpixel((x, y), jit((140, 96, 56), r, 6))
        if d > 6.6: im.putpixel((x, y), jit((92, 58, 34), r, 6))
im.save(f'{T}/block/adam_log_top.png')
im, r = base((168, 116, 70), 6, 8)
for y in (3, 7, 11, 15):
    for x in range(16): im.putpixel((x, y), jit((120, 80, 46), r, 4))
for (x, y) in ((5, 0), (12, 4), (3, 8), (9, 12)):
    for yy in range(y, y + 3): im.putpixel((x, yy), jit((120, 80, 46), r, 4))
im.save(f'{T}/block/adam_planks.png')
# Island Cloud: fluffy puffs, shaded pale blue-grey underneath (the old flat white with ring outlines looked odd).
# Sea Cloud: the milky White-White Sea, soft white with faint sky-blue ripples (it used to be white stained glass).
import math
def clamp(v): return max(0, min(255, int(round(v))))
def island_cloud(seed=7):
    """Fluffy cumulus: soft round puffs, bright tops, pale blue-grey shade underneath each puff. Tiles."""
    r = random.Random(seed)
    puffs = [(2, 3, 4.2), (9, 2, 4.6), (14, 7, 4.0), (5, 9, 4.4), (11, 12, 4.3), (1, 14, 3.8), (8, 7, 3.6)]
    im = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            best = None
            for (cx, cy, rad) in puffs:
                for ox in (-16, 0, 16):
                    for oy in (-16, 0, 16):
                        dx, dy = x - (cx + ox), y - (cy + oy)
                        d = math.hypot(dx, dy) / rad
                        if d < 1 and (best is None or cy + oy > best[1]):   # lower puffs sit in front
                            best = (d, cy + oy, dy / rad)
            if best is None:
                v = 0.55
            else:
                d, _, ny = best
                v = 1.0 - 0.45 * max(0.0, ny) * d - 0.25 * d ** 3        # shaded underneath and at the rim
            v += r.uniform(-0.02, 0.02)
            base = (236 + 18 * v, 240 + 14 * v, 248 + 7 * v)
            shade = (1 - v)
            c = (base[0] - 70 * shade, base[1] - 58 * shade, base[2] - 34 * shade)
            im.putpixel((x, y), tuple(clamp(t) for t in c) + (255,))
    return im
def sea_cloud(seed=11):
    """Milky sea cloud: soft white with slow, faint sky-blue ripples. Tiles."""
    r = random.Random(seed)
    im = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            w = math.sin(2 * math.pi * (y / 8 + 0.18 * math.sin(2 * math.pi * x / 16) + 0.06 * math.sin(2 * math.pi * 2 * x / 16 + 1)))
            w2 = math.sin(2 * math.pi * (x / 16 + y / 16) * 2)
            v = 0.5 + 0.35 * w + 0.15 * w2 + r.uniform(-0.05, 0.05)
            c = (238 - 22 * v, 243 - 16 * v, 250 - 6 * v)
            if w > 0.8: c = tuple(t + (255 - t) * (w - 0.8) * 4 for t in c)
            im.putpixel((x, y), tuple(clamp(t) for t in c) + (255,))
    return im
island_cloud().save(f'{T}/block/island_cloud.png')
sea_cloud().save(f'{T}/block/sea_cloud.png')
def sprite(name, pixels, colors, seed):
    r = random.Random(seed); im = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for y, row in enumerate(pixels):
        for x, ch in enumerate(row):
            if ch != '.': im.putpixel((x, y), jit(colors[ch], r, 8))
    im.save(f'{T}/item/{name}.png')
sprite('raw_seastone', [
    "................", "................", "................", ".....aaaa.......", "....abbbaa......", "...abbcbbba.....",
    "...abccbbbba....", "..abbbbbcbba....", "..abbcbbbbba....", "..aabbbbcba.....", "...aabbbbaa.....", "....aaaaaa......",
    "................", "................", "................", "................"],
    {'a': (35, 80, 90), 'b': (60, 135, 145), 'c': (110, 190, 200)}, 8)
sprite('seastone_ingot', [
    "................", "................", "................", "................", "................", "......aaaaaa....",
    ".....abccccba...", "....abbbbbbba....", "...abbbbbbbba....", "...aaaaaaaaaa...", "................", "................",
    "................", "................", "................", "................"],
    {'a': (35, 80, 90), 'b': (70, 150, 160), 'c': (140, 210, 215)}, 9)
sprite('seastone_jitte', [
    "..............a.", ".............aba", "............aba.", "...........aba..", "..........aba...", ".........aba....",
    "....c...aba.....", "....cc.aba......", ".....caba.......", "......ad........", ".....dad........", "....dd..........",
    "...dd...........", "..ed............", ".ee.............", "................"],
    {'a': (35, 80, 90), 'b': (90, 170, 180), 'c': (60, 135, 145), 'd': (90, 60, 40), 'e': (60, 40, 25)}, 10)
sprite('seastone_cuffs', [
    "................", "................", "..aaaa....aaaa..", ".ab..ba..ab..ba.", ".a....a..a....a.", ".a....acca....a.",
    ".a....a..a....a.", ".ab..ba..ab..ba.", "..aaaa....aaaa..", "................", "................", "................",
    "................", "................", "................", "................"],
    {'a': (60, 135, 145), 'b': (35, 80, 90), 'c': (150, 150, 150)}, 11)
print('textures done')
