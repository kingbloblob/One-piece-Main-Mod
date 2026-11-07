"""Draws the few furniture textures vanilla has no match for (rope net, sack canvas, sea chart, notice
posters, piano keys, gold coins, meat on the bone). 16x16, procedural, safe to publish."""
import random
from PIL import Image


def _img():
    return Image.new("RGBA", (16, 16), (0, 0, 0, 0))


def net():
    im, px = _img(), None
    px = im.load()
    for y in range(16):
        for x in range(16):
            if (x + y) % 5 == 0 or (x - y) % 5 == 0:
                shade = 150 + ((x * 7 + y * 3) % 3) * 12
                px[x, y] = (shade, int(shade * 0.82), int(shade * 0.55), 255)
    return im


def canvas():
    r = random.Random(3)
    im = _img(); px = im.load()
    for y in range(16):
        for x in range(16):
            v = 182 + r.randint(-10, 10) - (8 if (x + y * 2) % 4 == 0 else 0)
            px[x, y] = (v, int(v * 0.9), int(v * 0.7), 255)
    for x in range(16):  # tie band
        px[x, 3] = (120, 95, 60, 255)
    return im


def chart():
    r = random.Random(5)
    im = _img(); px = im.load()
    for y in range(16):
        for x in range(16):
            v = 222 + r.randint(-8, 6)
            px[x, y] = (v, int(v * 0.93), int(v * 0.74), 255)
    land = [(3, 4), (4, 4), (4, 5), (5, 5), (10, 9), (11, 9), (11, 10), (12, 10), (10, 10), (6, 12), (7, 12)]
    for x, y in land:
        px[x, y] = (120, 150, 80, 255)
    for i in range(2, 14):  # the Grand Line: a red route across the map
        px[i, 8 - (i % 3 == 0)] = (180, 40, 30, 255)
    for i in range(16):
        px[i, 0] = px[i, 15] = px[0, i] = px[15, i] = (150, 110, 70, 255)
    return im


def posters():
    im = _img(); px = im.load()
    for y in range(16):
        for x in range(16):
            px[x, y] = (150, 105, 65, 255)  # cork
    for (x0, y0, w, h, c) in ((1, 1, 6, 7, (225, 210, 170)), (8, 2, 6, 6, (235, 225, 200)), (2, 9, 5, 5, (225, 210, 170)), (9, 9, 5, 6, (240, 235, 220))):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                px[x, y] = c + (255,)
        for x in range(x0 + 1, x0 + w - 1):
            px[x, y0 + 1] = (60, 40, 30, 255)
        px[x0 + w // 2, y0 + h // 2] = (60, 40, 30, 255)
        px[x0 + w // 2 - 1, y0 + h // 2] = (60, 40, 30, 255)
        px[x0 + w // 2, y0] = (200, 40, 40, 255)  # pin
    return im


def keys():
    im = _img(); px = im.load()
    for y in range(16):
        for x in range(16):
            px[x, y] = (240, 238, 228, 255) if x % 2 == 0 or y > 9 else (230, 228, 218, 255)
            if x % 2 == 1 and x % 7 != 6 and y < 9:
                px[x, y] = (25, 25, 28, 255)
            if x % 2 == 1 and y >= 9 and False:
                pass
    for y in range(16):
        px[0, y] = (90, 90, 90, 255)
    return im


def coins():
    r = random.Random(9)
    im = _img(); px = im.load()
    for y in range(16):
        for x in range(16):
            v = r.randint(0, 4)
            px[x, y] = [(250, 210, 70), (230, 180, 40), (200, 145, 30), (255, 235, 130), (215, 160, 35)][v] + (255,)
    for _ in range(10):
        x, y = r.randint(1, 14), r.randint(1, 14)
        px[x, y] = (255, 250, 200, 255)
    return im


def meat():
    r = random.Random(11)
    im = _img(); px = im.load()
    for y in range(16):
        for x in range(16):
            v = r.randint(-12, 12)
            px[x, y] = (150 + v, 70 + v // 2, 40 + v // 3, 255)
            if (x * 3 + y) % 9 == 0:
                px[x, y] = (110, 50, 30, 255)
    return im


def jolly_roger():
    """The Straw Hat Pirates' flag: a skull in a straw hat over crossed bones, on black."""
    im = _img(); px = im.load()
    for y in range(16):
        for x in range(16):
            px[x, y] = (20, 20, 22, 255)
    bone = (235, 232, 220, 255)
    for i in range(3, 14):  # crossed bones behind the skull
        px[i, i] = px[i, 16 - i] = bone
    for (x, y) in ((2, 2), (3, 2), (2, 3), (13, 2), (14, 2), (14, 3), (2, 13), (2, 14), (3, 14), (14, 13), (13, 14), (14, 14)):
        px[x, y] = bone
    for y in range(6, 12):  # skull
        for x in range(5, 11):
            px[x, y] = bone
    for x in range(6, 10):
        px[x, 12] = bone
    for (x, y) in ((6, 8), (7, 8), (9, 8), (8, 8)):
        px[x, y] = (20, 20, 22, 255) if x in (6, 9) else bone
    px[6, 8] = px[9, 8] = px[6, 9] = px[9, 9] = (20, 20, 22, 255)  # eyes
    px[7, 11] = px[8, 11] = (20, 20, 22, 255)  # teeth gap
    hat = (228, 196, 92, 255)
    for x in range(3, 13):  # brim
        px[x, 5] = hat
    for y in range(2, 5):  # crown
        for x in range(5, 11):
            px[x, y] = hat
    for x in range(5, 11):  # red band
        px[x, 4] = (190, 35, 35, 255)
    return im


ALL = {"net": net, "canvas": canvas, "chart": chart, "posters": posters, "keys": keys, "coins": coins, "meat": meat, "jolly_roger": jolly_roger}
