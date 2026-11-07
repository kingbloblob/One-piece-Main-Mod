"""Draws the 16x16 item textures of Sanji's Galley dishes, from scratch.
Usage: python3 food_textures.py <source folder> [preview.png]"""
import os
import sys

from PIL import Image

from station_textures import Tex, shade

PLATE, PLATE_RIM = '#e8e6df', '#b8b4aa'


def plate(t, y0=9):
    for y in range(y0, y0 + 5):
        w = [5, 7, 7, 6, 4][y - y0]
        t.rect(8 - w, y, 7 + w, y, PLATE if y < y0 + 3 else PLATE_RIM, 0.02)


def bowl(t, colour, y0=7):
    for y in range(y0, y0 + 7):
        w = [6, 6, 6, 5, 5, 4, 3][y - y0]
        t.rect(8 - w, y, 7 + w, y, '#8a5a32' if y > y0 else colour, 0.05)
    t.rect(2, y0 - 1, 13, y0, colour, 0.1)


def bone_in_meat():
    t = Tex('bone_in_meat')
    for (x, y) in [(2, 12), (3, 13), (3, 11), (4, 12), (12, 3), (13, 2), (11, 2), (12, 1)]:
        t.px(x, y, '#f2ecd8', 0.03)
    for i in range(9):
        cx, cy = 4 + i, 11 - i
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if abs(dx) + abs(dy) <= 3 and 2 <= i <= 7:
                    t.px(cx + dx, cy + dy, '#8a3e22' if dx + dy < 1 else '#b45a2e', 0.1)
    t.px(7, 6, '#d88a54'); t.px(9, 5, '#d88a54')
    return t.img


def seafood_paella():
    t = Tex('seafood_paella')
    t.rect(1, 6, 14, 13, '#2a2a2a', 0.03)
    t.rect(2, 7, 13, 12, '#e0b030', 0.12)
    for (x, y) in [(4, 8), (9, 10), (11, 8)]:
        t.px(x, y, '#e05a3a'); t.px(x + 1, y, '#f07a5a')
    for (x, y) in [(6, 11), (7, 9), (3, 11)]:
        t.px(x, y, '#5a9a3a')
    t.rect(0, 8, 0, 9, '#2a2a2a'); t.rect(15, 8, 15, 9, '#2a2a2a')
    return t.img


def mikan_sorbet():
    t = Tex('mikan_sorbet')
    for y in range(9, 15):
        w = max(1, 5 - (y - 9))
        t.rect(8 - w, y, 7 + w, y, '#c9e4ea' if y < 11 else '#9ab8c0', 0.03)
    for (cy, r) in [(6, 4)]:
        for y in range(cy - r, cy + r):
            for x in range(8 - r, 8 + r):
                if (x - 7.5) ** 2 + (y - cy + 0.5) ** 2 <= r * r:
                    t.px(x, y, '#f39a2a', 0.1)
    t.px(6, 3, '#ffd08a'); t.px(9, 1, '#4a8a2a'); t.px(10, 1, '#4a8a2a')
    return t.img


def fire_curry():
    t = Tex('fire_curry'); plate(t)
    t.rect(3, 8, 7, 10, '#f4f0e4', 0.04)  # rice
    t.rect(8, 8, 12, 10, '#b8501a', 0.12)  # curry
    t.px(10, 9, '#e8d040'); t.px(9, 8, '#d02020')
    for (x, y) in [(9, 6), (10, 5), (11, 6), (10, 4), (12, 5)]:
        t.px(x, y, '#ff7a20', 0.1)
    return t.img


def herbal_tea():
    t = Tex('herbal_tea')
    t.rect(6, 2, 9, 3, '#8a6a3a', 0.03)
    t.rect(7, 4, 8, 5, '#c9e4ea', 0.02)
    for y in range(6, 15):
        w = 3 if y < 8 else 4
        t.rect(8 - w, y, 7 + w, y, '#c9e4ea' if y < 9 else '#7ab04a', 0.06)
    t.px(5, 11, '#d04040'); t.px(9, 12, '#d04040'); t.px(6, 13, '#a0d070')
    return t.img


def all_blue_feast():
    t = Tex('all_blue_feast'); plate(t, 10)
    t.rect(2, 6, 7, 10, '#a04a26', 0.1); t.px(1, 7, '#f2ecd8'); t.px(1, 6, '#f2ecd8')  # meat
    t.rect(8, 7, 13, 10, '#e88a6a', 0.1); t.rect(8, 8, 13, 8, '#f4c0a0', 0.04)  # salmon
    t.rect(6, 3, 9, 6, '#e8b040', 0.1)  # bread
    t.px(11, 5, '#f39a2a'); t.px(12, 5, '#f39a2a'); t.px(4, 4, '#5a9a3a')
    t.px(7, 11, '#3a7ad0'); t.px(8, 11, '#3a7ad0')  # a blue garnish: All Blue
    return t.img


DISHES = [bone_in_meat, seafood_paella, mikan_sorbet, fire_curry, herbal_tea, all_blue_feast]


def main():
    out = os.path.join(sys.argv[1], 'src/main/resources/assets/onepiece/textures/item')
    sheet = Image.new('RGBA', (len(DISHES) * 136 + 8, 144), (60, 60, 60, 255))
    for i, make in enumerate(DISHES):
        img = make()
        img.save(os.path.join(out, make.__name__ + '.png'))
        sheet.paste(img.resize((128, 128), Image.NEAREST), (8 + i * 136, 8), img.resize((128, 128), Image.NEAREST))
    if len(sys.argv) > 2:
        sheet.save(sys.argv[2])
    print('wrote', len(DISHES), 'dish textures')


if __name__ == '__main__':
    main()
