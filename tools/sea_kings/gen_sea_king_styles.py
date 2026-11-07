"""Paints the extra body-style parts (horns, whiskers, frills, toad eyes, armour...) onto every Sea King texture.

Run:  python3 -I gen_sea_king_styles.py [source dir, default ../..]
Edits textures/entity/sea_king/sea_king_0..6.png (7 and 8 are made by gen_mecha_sea_kings.py) in place: only the area from y=96 down, which the base
serpent model doesn't use. Colours come from each texture's own body and fin colours, so every colour
variant (and boss recolour) gets matching parts. The UV spots must match SeaKingModel.createBodyLayer(int).
"""
import os
import random
import sys

from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "..")
DIR = os.path.join(SRC, "src", "main", "resources", "assets", "onepiece", "textures", "entity", "sea_king")

# (u, v, w, h, d, kind): one box's UV area is 2*(w+d) wide and h+d tall.
PARTS = [
    (0, 96, 3, 3, 10, "horn"),
    (26, 96, 2, 2, 5, "horn_tip"),
    (40, 96, 1, 1, 16, "whisker"),
    (74, 96, 1, 12, 10, "frill"),
    (96, 96, 1, 6, 6, "spike"),
    (110, 96, 4, 4, 4, "eye"),
    (0, 113, 4, 5, 6, "body"),
    (20, 113, 6, 3, 10, "plate"),
    (52, 113, 3, 8, 3, "body"),
]


def average(img, box):
    px = img.load()
    total, n = [0, 0, 0], 0
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            r, g, b, a = px[x, y]
            if a:
                total[0] += r; total[1] += g; total[2] += b; n += 1
    return tuple(c // max(n, 1) for c in total)


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def paint(img):
    rnd = random.Random(7)
    body = average(img, (2, 33, 38, 37))    # first body segment, side
    fin = average(img, (36, 62, 44, 70))    # tail fin
    belly = average(img, (20, 4, 30, 10))   # pale underside of the skull
    colours = {
        "horn": (232, 222, 196), "horn_tip": (70, 60, 50), "whisker": shade(body, 0.7), "frill": fin,
        "spike": shade(fin, 0.85), "body": body, "plate": tuple((a + b) // 2 for a, b in zip(fin, (225, 215, 185))), "eye": (240, 200, 40),
    }
    px = img.load()
    for x in range(128):
        for y in range(96, 128):
            px[x, y] = (0, 0, 0, 0)
    px_fang = None
    for (u, v, w, h, d, kind) in PARTS:
        base = colours[kind]
        for y in range(v, v + h + d):
            for x in range(u, u + 2 * (w + d)):
                f = 0.88 + rnd.random() * 0.2
                if kind == "frill" and (x - u) % 3 == 0:
                    f *= 0.75  # ribs in the fan
                if kind == "plate" and (x - u) % 4 == 0:
                    f *= 0.8
                if kind == "body" and y >= v + d + h - 1:
                    px[x, y] = belly + (255,)
                    continue
                px[x, y] = shade(base, f) + (255,)
        if kind == "eye":
            # Front face of the eye box: u+d .. u+d+w, rows v+d .. v+d+h. Black slit pupil in the middle.
            for y in range(v + d, v + d + h):
                px[u + d + w // 2 - 1, y] = (20, 20, 20, 255)
                px[u + d + w // 2, y] = (20, 20, 20, 255)


for name in sorted(os.listdir(DIR)):
    if name.startswith("sea_king_") and name.endswith(".png") and name not in ("sea_king_7.png", "sea_king_8.png"):
        path = os.path.join(DIR, name)
        img = Image.open(path).convert("RGBA")
        paint(img)
        img.save(path)
        print("painted", name)
