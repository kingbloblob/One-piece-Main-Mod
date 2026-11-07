"""Makes the Sea King boss textures and the item icons for the sea bosses.

Run:  python3 gen_sea_boss_art.py [source dir, default ../../source]
Writes textures/entity/sea_king/sea_king_3..6.png (recolors of sea_king_0.png: the body changes, the mouth and teeth stay)
and textures/item/{sea_lord_lure,coast_lord_fang,phantom_scale,behemoth_horn,ancient_sea_king_fang}.png.
"""
import colorsys
import os
import sys

from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "..", "source")
TEX = os.path.join(SRC, "src", "main", "resources", "assets", "onepiece", "textures")

# variant: (hue, saturation, brightness factor)
BOSSES = {
    3: (0.20, 0.55, 1.05),   # Lord of the Coast: olive green-brown
    4: (0.55, 0.10, 2.10),   # Florian Phantom: ghostly pale grey-blue
    5: (0.99, 0.65, 0.55),   # Calm Belt Behemoth: almost black, blood red
    6: (0.12, 0.75, 1.45),   # Ancient Sea King: old gold
}


def recolor():
    base = Image.open(os.path.join(TEX, "entity", "sea_king", "sea_king_0.png")).convert("RGBA")
    for variant, (hue, sat, bright) in BOSSES.items():
        img = base.copy()
        px = img.load()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = px[x, y]
                if a == 0:
                    continue
                h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
                if s < 0.15 or not (0.3 < h < 0.62):
                    continue  # mouth, teeth, eyes stay as they are
                nr, ng, nb = colorsys.hsv_to_rgb(hue, sat, min(1.0, v * bright))
                px[x, y] = (int(nr * 255), int(ng * 255), int(nb * 255), a)
        img.save(os.path.join(TEX, "entity", "sea_king", "sea_king_%d.png" % variant))


def icon(name, pixels, palette):
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y, row in enumerate(pixels):
        for x, ch in enumerate(row):
            if ch != ".":
                img.putpixel((x, y), palette[ch])
    img.save(os.path.join(TEX, "item", name + ".png"))


FANG = [
    "................",
    "...........oo...",
    "..........oWWo..",
    ".........oWWWo..",
    "........oWWWWo..",
    ".......oWWWWo...",
    "......oWWWWso...",
    ".....oWWWWso....",
    "....oWWWWso.....",
    "...oWWWWso......",
    "...oWWWso.......",
    "..oWWWso........",
    "..oWWso.........",
    "..oWso..........",
    "...oo...........",
    "................",
]
SCALE = [
    "................",
    "......oooo......",
    "....ooLLLLoo....",
    "...oLLLWWLLLo...",
    "..oLLLWWLLLLLo..",
    "..oLLWWLLLLLLo..",
    ".oLLLLLLLLLLLLo.",
    ".oLLLLLLLLLLsLo.",
    ".oLLLLLLLLLssLo.",
    "..oLLLLLLLssLo..",
    "..oLLLLLLsssLo..",
    "...oLLLLsssLo...",
    "....ooLsssoo....",
    "......oooo......",
    "................",
    "................",
]
HORN = [
    "................",
    "............oo..",
    "...........oHo..",
    "..........oHHo..",
    ".........oHHo...",
    "........oHHHo...",
    ".......oHHHo....",
    "......oHHHHo....",
    ".....oHHHHo.....",
    "....oHHHHHo.....",
    "...oHHsHHo......",
    "..oHHssHHo......",
    "..oHssssHo......",
    "..oooooooo......",
    "................",
    "................",
]
LURE = [
    "................",
    ".......oo.......",
    "......oSSo......",
    ".......oo.......",
    "......oRRo......",
    ".....oRRRRo.....",
    "....oRRGRRRo....",
    "....oRGGGRRo....",
    "....oRRGRRRo....",
    "....oRRRRRRo....",
    ".....oRRRRo.....",
    "......oRRo......",
    ".......oo.......",
    "................",
    "................",
    "................",
]


def icons():
    icon("coast_lord_fang", FANG, {"o": (60, 50, 35, 255), "W": (236, 228, 200, 255), "s": (180, 168, 130, 255)})
    icon("ancient_sea_king_fang", FANG, {"o": (90, 60, 10, 255), "W": (255, 214, 90, 255), "s": (196, 140, 40, 255)})
    icon("phantom_scale", SCALE, {"o": (90, 100, 120, 255), "L": (214, 224, 236, 255), "W": (255, 255, 255, 255), "s": (160, 176, 196, 255)})
    icon("behemoth_horn", HORN, {"o": (30, 10, 12, 255), "H": (110, 26, 30, 255), "s": (60, 16, 20, 255)})
    icon("sea_lord_lure", LURE, {"o": (40, 30, 30, 255), "S": (200, 200, 210, 255), "R": (150, 40, 50, 255), "G": (255, 210, 80, 255)})


if __name__ == "__main__":
    recolor()
    icons()
