"""Draws the wall Wanted Poster and the newspaper textures (package com.onepiecemod.news).
Usage: python3 gen_news_textures.py <path to src/main/resources>"""
import random
import sys
from PIL import Image

RES = sys.argv[1] if len(sys.argv) > 1 else "src/main/resources"
TEX = RES + "/assets/onepiece/textures/"

BIG = {  # 5x7
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
}
SMALL = {  # 3x5
    "D": ["110", "101", "101", "101", "110"], "E": ["111", "100", "110", "100", "111"],
    "A": ["010", "101", "111", "101", "101"], "O": ["010", "101", "101", "101", "010"],
    "R": ["110", "101", "110", "101", "101"], "L": ["100", "100", "100", "100", "111"],
    "I": ["111", "010", "010", "010", "111"], "V": ["101", "101", "101", "101", "010"],
    "M": ["101", "111", "111", "101", "101"], "N": ["101", "111", "111", "111", "101"],
    " ": ["000"] * 5,
}


def text(img, s, x, y, font, color, bold=False):
    for ch in s:
        g = font[ch]
        for gy, row in enumerate(g):
            for gx, bit in enumerate(row):
                if bit == "1":
                    px = x + gx
                    img.putpixel((px, y + gy), color)
                    if bold:
                        img.putpixel((px + 1, y + gy), color)
        x += len(g[0]) + (2 if bold else 1)
    return x


def width(s, font, bold=False):
    return sum(len(font[c][0]) + (2 if bold else 1) for c in s) - 1


def poster():
    rnd = random.Random(7)
    w = h = 64
    img = Image.new("RGBA", (w, h))
    for y in range(h):
        for x in range(w):
            n = rnd.randint(-10, 10)
            edge = min(x, y, w - 1 - x, h - 1 - y)
            age = 18 if edge < 2 else (8 if edge < 4 else 0)
            img.putpixel((x, y), (232 + n - age, 211 + n - age, 160 + n - age, 255))
    ink = (58, 34, 18, 255)
    for x in range(3, 61):  # thin frame lines
        img.putpixel((x, 2), ink)
        img.putpixel((x, 61), ink)
    for y in range(2, 62):
        img.putpixel((2, y), ink)
        img.putpixel((61, y), ink)
    text(img, "WANTED", (w - width("WANTED", BIG, True)) // 2, 5, BIG, ink, True)
    # Photo frame with a shadowy silhouette (players' faces are drawn over it).
    fx0, fy0, fx1, fy1 = 19, 14, 44, 34
    for y in range(fy0, fy1 + 1):
        for x in range(fx0, fx1 + 1):
            border = x in (fx0, fx1) or y in (fy0, fy1)
            n = rnd.randint(-6, 6)
            img.putpixel((x, y), ink if border else (196 + n, 170 + n, 120 + n, 255))
    cx = (fx0 + fx1) / 2
    for y in range(fy0 + 1, fy1):
        for x in range(fx0 + 1, fx1):
            head = ((x - cx) / 5.5) ** 2 + ((y - 21) / 6.0) ** 2 <= 1
            body = y >= 28 and abs(x - cx) <= 3 + (y - 28) * 1.6
            if head or body:
                img.putpixel((x, y), (92, 64, 40, 255))
    text(img, "DEAD OR ALIVE", (w - width("DEAD OR ALIVE", SMALL)) // 2, 37, SMALL, ink)
    # Rows 44-60 stay empty: the name, bounty and race are drawn there in the game.
    return img


def newspaper():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    paper, shade, ink, line = (236, 232, 218, 255), (200, 196, 182, 255), (40, 40, 48, 255), (120, 120, 128, 255)
    for y in range(2, 14):
        for x in range(2, 14):
            img.putpixel((x, y), paper if x < 12 else shade)
    for x in range(2, 14):
        img.putpixel((x, 1), shade)
        img.putpixel((x, 14), (150, 146, 134, 255))
    for x in range(3, 11):  # masthead
        img.putpixel((x, 3), ink)
        img.putpixel((x, 4), ink)
    for y in (6, 8, 10, 12):
        for x in range(3, 7):
            img.putpixel((x, y), line)
    for y in range(6, 11):  # photo
        for x in range(8, 11):
            img.putpixel((x, y), (110, 100, 90, 255))
    img.putpixel((9, 7), (230, 200, 160, 255))
    for y in (12,):
        for x in range(8, 11):
            img.putpixel((x, y), line)
    return img


p = poster()
p.save(TEX + "block/wall_wanted_poster.png")
p.resize((16, 16), Image.LANCZOS).save(TEX + "item/wall_wanted_poster.png")
newspaper().save(TEX + "item/newspaper.png")
print("news textures written")
