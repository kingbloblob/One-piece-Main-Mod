"""Makes the two Egghead sea boss textures from the plain Sea King texture (sea_king_0.png):
  sea_king_7.png  Mecha-Shark (Vegapunk's robot shark): steel plates, rivets, red eyes. Shark parts (SeaKingModel style 6).
  sea_king_8.png  Sea Beast Weapon (Lilith's cyborg Sea King): dark living hide with steel fins, plates and a head cannon (style 7).
The area from y=96 down holds the extra parts; their boxes are listed in SHARK / CYBORG and must match SeaKingModel.
gen_sea_king_styles.py leaves these two files alone.
Run:  python3 -I gen_mecha_sea_kings.py [source dir, default ../..]
"""
import colorsys
import os
import random
import sys

from PIL import Image

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
DIR = os.path.join(ROOT, "src", "main", "resources", "assets", "onepiece", "textures", "entity", "sea_king")

# (u, v, w, h, d, colour key)
SHARK = [
    (0, 96, 11, 10, 12, "hull"),      # bulk on segment 0
    (46, 96, 10, 9, 12, "hull"),      # bulk on segment 1
    (90, 96, 1, 14, 10, "fin"),       # dorsal fin
    (112, 96, 1, 16, 6, "fin"),       # upper tail lobe
    (0, 118, 12, 1, 8, "fin"),        # pectoral fins
    (58, 117, 1, 7, 4, "fin"),        # lower tail lobe
    (68, 118, 10, 1, 1, "visor"),     # eye visor
]
CYBORG = [
    (0, 96, 6, 3, 10, "plate"),       # back plates
    (32, 96, 3, 3, 10, "barrel"),     # head cannon barrel
    (58, 96, 5, 3, 5, "plate"),       # cannon mount
    (78, 96, 10, 1, 1, "visor"),      # eye visor
    (0, 110, 2, 2, 6, "barrel"),      # side laser pods
]


def kind(rgb):
    r, g, b = (c / 255 for c in rgb)
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if s < 0.3 and v > 0.7:
        return "light"
    if 0.11 < h < 0.2 and s > 0.6 and v > 0.7:
        return "eye"
    if (h > 0.9 or h < 0.02) and s > 0.5:
        return "mouth"
    if 0.0 <= h < 0.11 and s > 0.5:
        return "fin"
    return "body"


def shade(c, f):
    return tuple(max(0, min(255, int(x * f))) for x in c)


def make(palette, parts, steel_body, seed):
    rnd = random.Random(seed)
    src = Image.open(os.path.join(DIR, "sea_king_0.png")).convert("RGBA")
    img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    sp, px = src.load(), img.load()
    for y in range(96):
        for x in range(128):
            r, g, b, a = sp[x, y]
            if not a:
                continue
            k = kind((r, g, b))
            lum = (0.3 * r + 0.59 * g + 0.11 * b) / 255
            if k == "eye":
                px[x, y] = palette["eye"] + (255,)
                continue
            if k == "mouth":
                px[x, y] = (r, g, b, a)
                continue
            base = palette["belly"] if k == "light" else palette["fin"] if k == "fin" else palette["body"]
            f = 0.75 + lum * 0.5 + rnd.random() * 0.06
            if steel_body or k == "fin":
                # Steel panels: a dark seam every 6 pixels, a rivet now and then.
                if x % 6 == 0 or y % 6 == 0:
                    f *= 0.7
                elif x % 6 == 3 and y % 6 == 3 and rnd.random() < 0.5:
                    f *= 1.3
            px[x, y] = shade(base, f) + (255,)
    for (u, v, w, h, d, key) in parts:
        base = palette[key]
        for y in range(v, v + h + d):
            for x in range(u, u + 2 * (w + d)):
                f = 0.9 + rnd.random() * 0.12
                if key in ("hull", "plate", "fin") and ((x - u) % 5 == 0 or (y - v) % 5 == 0):
                    f *= 0.72
                if key == "hull" and y >= v + d + h - 3:
                    px[x, y] = shade(palette["belly"], f) + (255,)
                    continue
                if key == "barrel" and (y - v) % 4 == 0:
                    f *= 0.6
                px[x, y] = shade(base, f) + (255,)
    return img


STEEL = {"body": (112, 128, 146), "belly": (196, 204, 212), "fin": (74, 84, 98), "hull": (112, 128, 146),
         "eye": (255, 40, 30), "visor": (255, 50, 40), "plate": (150, 160, 172), "barrel": (60, 64, 72)}
CYBORG_PAL = {"body": (92, 58, 104), "belly": (214, 196, 170), "fin": (120, 130, 142), "hull": (92, 58, 104),
              "eye": (255, 40, 30), "visor": (255, 50, 40), "plate": (150, 160, 172), "barrel": (60, 64, 72)}

make(STEEL, SHARK, True, 11).save(os.path.join(DIR, "sea_king_7.png"))
make(CYBORG_PAL, CYBORG, False, 12).save(os.path.join(DIR, "sea_king_8.png"))
print("wrote sea_king_7.png and sea_king_8.png")


def icons():
    """16x16 trophies: a steel shark fin with rivets, and a glowing red core in a steel case."""
    out = os.path.join(ROOT, "src", "main", "resources", "assets", "onepiece", "textures", "item")
    fin = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = fin.load()
    for y in range(2, 14):
        # A fin leaning back: its front edge slopes, the back edge curves in.
        left = 3 + (13 - y) // 3
        right = 4 + (y - 2)
        if y > 9:
            right = min(right, 13)
        for x in range(left, min(15, right)):
            c = (128, 142, 160) if x > left else (190, 200, 212)
            if (x + y) % 5 == 0:
                c = (88, 98, 112)
            p[x, y] = c + (255,)
    for x in range(2, 15):
        p[x, 14] = (60, 66, 76, 255)
    for (x, y) in ((6, 10), (9, 12), (11, 12), (7, 7)):
        p[x, y] = (230, 236, 244, 255)
    fin.save(os.path.join(out, "mecha_shark_fin.png"))

    core = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = core.load()
    for y in range(2, 14):
        for x in range(2, 14):
            dx, dy = x - 7.5, y - 7.5
            d = (dx * dx + dy * dy) ** 0.5
            if d < 3.0:
                p[x, y] = (255, 230 - int(d * 50), 200 - int(d * 60), 255)
            elif d < 4.2:
                p[x, y] = (230, 40, 30, 255)
            elif d < 6.2:
                p[x, y] = (150, 160, 172, 255) if (x + y) % 3 else (96, 104, 116, 255)
    for (x, y) in ((3, 3), (12, 3), (3, 12), (12, 12)):
        p[x, y] = (220, 226, 234, 255)
    core.save(os.path.join(out, "beast_weapon_core.png"))
    print("wrote item icons")


icons()
