"""Paints the 16x16 item icons for the ship items (going_merry.png, thousand_sunny.png).

Run: python3 gen_icons.py [path to source/]   (default: the shared source)
Writes assets/onepiece/textures/item/<ship>.png: a little side view of the ship on the sea, bow to the right.
"""
import os
import sys

from PIL import Image

SRC = next((a for a in sys.argv[1:] if not a.startswith('--')), '/mnt/project-files/one-piece-mod/source')
OUT = os.path.join(SRC, 'src/main/resources/assets/onepiece/textures/item')

SEA = (52, 110, 200, 255)
SEA_DARK = (36, 80, 160, 255)
OUTLINE = (40, 28, 16, 255)


def paint(name, hull, hull_dark, trim, sail, emblem, head, head2, mane=None):
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    px = img.load()
    # sea
    for x in range(16):
        px[x, 14] = SEA
        px[x, 15] = SEA_DARK if x % 3 else SEA
    # hull: a banana shape from x=2 to x=13, deck at y=10, bottom at y=13
    for x in range(2, 14):
        px[x, 10] = trim
        for y in range(11, 14):
            if y == 13 and (x < 4 or x > 11):
                continue
            px[x, y] = hull_dark if y == 12 else hull
    px[1, 9] = trim; px[1, 10] = hull; px[1, 11] = hull   # stern
    px[14, 9] = hull; px[14, 10] = hull                   # bow
    # figurehead
    px[14, 8] = head; px[15, 8] = head; px[15, 9] = head2; px[14, 7] = head2
    if mane:
        for (x, y) in ((13, 7), (14, 6), (15, 7), (13, 8), (15, 10)):
            px[x, y] = mane
    # mast + sail
    for y in range(2, 10):
        px[8, y] = OUTLINE
    for x in range(5, 12):
        for y in range(3, 9):
            px[x, y] = sail
    px[8, 5] = emblem; px[7, 5] = emblem; px[9, 5] = emblem; px[8, 6] = emblem; px[8, 4] = emblem
    px[8, 1] = (20, 20, 20, 255); px[9, 1] = (20, 20, 20, 255); px[9, 2] = (20, 20, 20, 255)  # flag
    # stern cabin
    px[2, 9] = trim; px[3, 9] = trim; px[4, 9] = trim; px[3, 8] = trim
    os.makedirs(OUT, exist_ok=True)
    img.save(os.path.join(OUT, f'{name}.png'))


paint('going_merry', hull=(196, 150, 92, 255), hull_dark=(120, 82, 46, 255), trim=(240, 236, 226, 255),
      sail=(245, 245, 240, 255), emblem=(30, 30, 30, 255), head=(250, 250, 250, 255), head2=(236, 180, 60, 255))
paint('thousand_sunny', hull=(214, 176, 112, 255), hull_dark=(96, 60, 36, 255), trim=(120, 82, 46, 255),
      sail=(245, 245, 240, 255), emblem=(30, 30, 30, 255), head=(250, 220, 60, 255), head2=(240, 120, 40, 255), mane=(240, 130, 30, 255))
print('icons written to', OUT)
