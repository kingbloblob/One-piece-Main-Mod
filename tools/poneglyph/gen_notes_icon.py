"""Draws the Ohara Survey Notes item icon (a brown notebook with a blue Poneglyph square on it).
Run: python3 gen_notes_icon.py [source dir, default ../../source]
"""
import os
import sys

from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "..", "source")
OUT = os.path.join(SRC, "src", "main", "resources", "assets", "onepiece", "textures", "item", "ohara_survey_notes.png")
ART = [
    "................",
    "..oooooooooooo..",
    "..oBBBBBBBBBBPo.",
    "..oBBBBBBBBBBPo.",
    "..oBBkkkkkkBBPo.",
    "..oBBkccccckBPo.",
    "..oBBkcmcmckBPo.",
    "..oBBkccccckBPo.",
    "..oBBkcmmcckBPo.",
    "..oBBkccccckBPo.",
    "..oBBkkkkkkBBPo.",
    "..oBBBBBBBBBBPo.",
    "..oBBBBBBRBBBPo.",
    "..oBBBBBBRBBBPo.",
    "..ooooooooooooo.",
    "................",
]
PAL = {"o": (50, 30, 18, 255), "B": (122, 78, 44, 255), "P": (232, 222, 196, 255), "k": (20, 30, 60, 255),
       "c": (40, 70, 130, 255), "m": (120, 170, 230, 255), "R": (170, 40, 40, 255)}
img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
for y, row in enumerate(ART):
    for x, ch in enumerate(row):
        if ch != ".":
            img.putpixel((x, y), PAL[ch])
img.save(OUT)
