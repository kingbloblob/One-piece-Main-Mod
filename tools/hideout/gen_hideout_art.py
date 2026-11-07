"""Paints the Hideout Flag textures: the cloth (block) and the inventory icon. Run: python3 gen_hideout_art.py <resources dir>"""
import sys
from PIL import Image

out = sys.argv[1]
K, D, W, G, R = (18, 16, 20, 255), (40, 36, 44, 255), (236, 232, 220, 255), (120, 116, 112, 255), (150, 30, 30, 255)

def cloth():
    img = Image.new("RGBA", (16, 16), K)
    px = img.load()
    # Weathered cloth: a few lighter threads and a frayed fly edge.
    for x in range(16):
        for y in range(16):
            if (x * 7 + y * 3) % 11 == 0:
                px[x, y] = D
    for y in (1, 4, 8, 10):
        px[15, y] = D
        px[14, y + 1 if y < 15 else y] = D
    # Crossbones (an X under the skull).
    for i in range(9):
        for (x, y) in ((3 + i, 3 + i), (11 - i, 3 + i)):
            if 0 <= x < 16 and 0 <= y < 16:
                px[x, y] = W
    for (x, y) in ((2, 2), (3, 2), (2, 3), (12, 2), (11, 2), (12, 3), (2, 12), (2, 11), (3, 12), (12, 12), (12, 11), (11, 12)):
        px[x, y] = W
    # Skull.
    for x in range(5, 11):
        for y in range(2, 8):
            if not ((x in (5, 10)) and y in (2, 7)):
                px[x, y] = W
    for (x, y) in ((6, 4), (6, 5), (9, 4), (9, 5)):
        px[x, y] = K
    px[7, 6] = G
    px[8, 6] = G
    for x in (6, 8):
        px[x, 7] = K
    # A red headband, like a crew's own mark.
    for x in range(5, 11):
        px[x, 3] = R
    return img

def icon(c):
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    pole, pole_dark, gold = (122, 88, 52, 255), (86, 60, 34, 255), (230, 190, 60, 255)
    for y in range(1, 16):
        px[3, y] = pole
        px[4, y] = pole_dark
    px[3, 0] = gold
    px[4, 0] = gold
    small = c.resize((10, 8), Image.NEAREST)
    for x in range(10):
        for y in range(8):
            wave = 1 if x in (3, 4, 5) else 0
            if 2 + y + wave < 16:
                px[5 + x, 2 + y + wave] = small.getpixel((x, y))
    return img

c = cloth()
c.save(out + "/assets/onepiece/textures/block/hideout_flag_cloth.png")
icon(c).save(out + "/assets/onepiece/textures/item/hideout_flag.png")
print("ok")
