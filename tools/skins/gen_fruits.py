"""Paints the 16x16 Devil Fruit item icons: a shaded fruit covered in swirls, with a curly stem.

Run:  python3 gen_fruits.py [path to source/] [--preview out.png]
Reads the fruit list (id, type, two colours) from power/DevilFruits.java and writes
assets/onepiece/textures/item/<id>.png. Each fruit gets a shape (round, pear, heart, grape
cluster, melon, peach, tall, spiky) picked from SHAPES below or from its id.
"""
import math
import os
import re
import sys
import zlib

from PIL import Image

SRC = next((a for a in sys.argv[1:] if not a.startswith('--') and not a.endswith('.png')),
           '/mnt/project-files/one-piece-mod/source')
JAVA = os.path.join(SRC, 'src/main/java/com/onepiecemod/power/DevilFruits.java')
OUT = os.path.join(SRC, 'src/main/resources/assets/onepiece/textures/item')

# Fruits that should look like they do in the story.
SHAPES = {
    'gomu_gomu_no_mi': 'grapes', 'hito_hito_no_mi_nika': 'grapes', 'ope_ope_no_mi': 'heart',
    'mera_mera_no_mi': 'round', 'hito_hito_no_mi': 'pear', 'gura_gura_no_mi': 'round',
    'yami_yami_no_mi': 'tall', 'tori_tori_no_mi_phoenix': 'pear', 'mero_mero_no_mi': 'heart',
    'hana_hana_no_mi': 'peach', 'bara_bara_no_mi': 'melon', 'goro_goro_no_mi': 'spiky',
    'pika_pika_no_mi': 'spiky', 'magu_magu_no_mi': 'round', 'hie_hie_no_mi': 'tall',
    'uo_uo_no_mi_seiryu': 'tall', 'ito_ito_no_mi': 'grapes', 'suna_suna_no_mi': 'melon',
}
BY_TYPE = {
    'PARAMECIA': ['round', 'peach', 'heart', 'grapes', 'melon', 'pear', 'round', 'peach'],
    'LOGIA': ['tall', 'spiky', 'round', 'tall'],
    'ZOAN': ['pear', 'melon', 'peach', 'tall', 'pear'],
}


def rgb(v):
    return ((v >> 16) & 255, (v >> 8) & 255, v & 255)


def sh(c, f):
    return tuple(max(0, min(255, int(x * f))) for x in c)


def lum(c):
    return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]


def inside(shape, x, y):
    px, py = x + 0.5, y + 0.5
    if shape == 'round':
        return ((px - 8) / 6.3) ** 2 + ((py - 9.6) / 5.9) ** 2 <= 1
    if shape == 'peach':
        return ((px - 8) / 6.4) ** 2 + ((py - 9.8) / 5.7) ** 2 <= 1 and not (py < 5.2 and abs(px - 8) < 1)
    if shape == 'melon':
        return ((px - 8) / 7.0) ** 2 + ((py - 10.2) / 5.0) ** 2 <= 1
    if shape == 'tall':
        return ((px - 8) / 4.9) ** 2 + ((py - 9.4) / 6.4) ** 2 <= 1
    if shape == 'pear':
        t = (py - 3.4) / 12.0
        rx = 2.4 + 4.0 * math.sin(min(1.0, max(0.0, t * 1.5)) * math.pi / 2)
        return 3.4 <= py <= 15.4 and abs(px - 8) <= rx * (1 - max(0, (py - 13.2) / 2.4) ** 2) ** 0.5
    if shape == 'heart':
        a = ((px - 5.4) / 3.4) ** 2 + ((py - 7.4) / 3.2) ** 2 <= 1
        b = ((px - 10.6) / 3.4) ** 2 + ((py - 7.4) / 3.2) ** 2 <= 1
        c = 7 <= py <= 15.2 and abs(px - 8) <= (15.6 - py) * 0.78
        return a or b or c
    if shape == 'grapes':
        balls = [(5.0, 6.2), (11.0, 6.2), (8.0, 5.0), (3.8, 9.8), (8.0, 9.4), (12.2, 9.8), (5.8, 13.0), (10.2, 13.0)]
        return any((px - bx) ** 2 + (py - by) ** 2 <= 2.9 ** 2 for bx, by in balls)
    if shape == 'spiky':
        ang = math.atan2(py - 9.5, px - 8)
        r = 5.6 + 0.9 * math.cos(ang * 7)
        return math.hypot((px - 8) / 0.9, py - 9.5) <= r
    raise ValueError(shape)


CURL = [".###.",
        "#...#",
        "#.#.#",
        "#..#.",
        ".#..."]


def swirl(x, y, seed):
    """True where a swirl line is: little curls on a staggered grid (6 wide, 6 tall)."""
    row = (y + seed % 4) // 6
    lx = (x + (row % 2) * 3 + seed % 5) % 6
    ly = (y + seed % 4) % 6
    return lx < 5 and ly < 5 and CURL[ly][lx] == '#'


def paint(fid, ftype, c1, c2, idx):
    shape = SHAPES.get(fid) or BY_TYPE[ftype][zlib.crc32(fid.encode()) % len(BY_TYPE[ftype])]
    base, acc = rgb(c1), rgb(c2)
    # make sure the swirls show up against the skin of the fruit
    if abs(lum(base) - lum(acc)) < 45:
        acc = sh(acc, 0.6) if lum(base) > 110 else sh(acc, 1.6)
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    m = [[inside(shape, x, y) for x in range(16)] for y in range(16)]
    top = min(y for y in range(16) for x in range(16) if m[y][x])
    seed = zlib.crc32(fid.encode()) & 255
    for y in range(16):
        for x in range(16):
            if not m[y][x]:
                continue
            edge = any(not (0 <= x + dx < 16 and 0 <= y + dy < 16 and m[y + dy][x + dx])
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            # light from the top left
            d = math.hypot(x - 5, y - (top + 3)) / 11
            f = 1.18 - 0.5 * d
            col = acc if swirl(x, y, seed) else base
            if edge:
                col = sh(base, 0.42 if lum(base) > 60 else 1.6)
                f = 1
            img.putpixel((x, y), sh(col, f) + (255,))
    # shine
    for (x, y) in ((5, top + 2), (4, top + 3)):
        if m[y][x]:
            img.putpixel((x, y), sh((255, 255, 255), 0.96) + (255,))
    # curly stem and a leaf
    stem, leaf = (92, 62, 32), (78, 156, 58)
    sx = 8
    sy = min(y for y in range(16) if m[y][sx])
    for (x, y, c) in ((sx, sy - 1, stem), (sx - 1, sy - 2, stem), (sx, sy - 3, stem), (sx + 1, sy - 3, stem),
                      (sx + 1, sy - 2, leaf), (sx + 2, sy - 2, leaf), (sx + 2, sy - 1, sh(leaf, 0.75)),
                      (sx + 3, sy - 2, sh(leaf, 0.75))):
        if 0 <= y < 16 and 0 <= x < 16 and not m[y][x]:
            img.putpixel((x, y), c + (255,))
    return img


def main():
    src = open(JAVA).read()
    fruits = re.findall(r'new DevilFruit\("([a-z_]+)",\s*"[^"]*",\s*Type\.([A-Z]+),\s*0x([0-9A-Fa-f]{6}),\s*0x([0-9A-Fa-f]{6})', src)
    icons = []
    for i, (fid, ftype, a, b) in enumerate(fruits):
        img = paint(fid, ftype, int(a, 16), int(b, 16), i)
        img.save(os.path.join(OUT, fid + '.png'))
        icons.append(img)
    if '--preview' in sys.argv:
        out = sys.argv[sys.argv.index('--preview') + 1]
        cols = 12
        sheet = Image.new('RGBA', (cols * 70, ((len(icons) + cols - 1) // cols) * 70), (139, 139, 139, 255))
        for k, im in enumerate(icons):
            sheet.alpha_composite(im.resize((64, 64), Image.NEAREST), ((k % cols) * 70 + 3, (k // cols) * 70 + 3))
        sheet.save(out)
    print('painted %d fruits' % len(icons))


if __name__ == '__main__':
    main()
