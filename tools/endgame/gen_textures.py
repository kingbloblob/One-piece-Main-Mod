# Makes the endgame item textures (16x16 pixel art) and their item model files.
import json, os, sys
from PIL import Image
OUT = sys.argv[1]
def draw(name, rows, pal):
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in pal:
                img.putpixel((x, y), pal[ch])
    img.save(os.path.join(OUT, "textures/item", name + ".png"))
    json.dump({"model": {"type": "minecraft:model", "model": "onepiece:item/" + name}},
              open(os.path.join(OUT, "items", name + ".json"), "w"), indent=2)
    json.dump({"parent": "minecraft:item/generated", "textures": {"layer0": "onepiece:item/" + name}},
              open(os.path.join(OUT, "models/item", name + ".json"), "w"), indent=2)
def c(h, a=255): return ((h >> 16) & 255, (h >> 8) & 255, h & 255, a)
K = c(0x1a1a1a); W = c(0xf4f4f4); G = c(0xd4a017); g = c(0x8a6508); R = c(0xc8262b); r = c(0x7a1214)

draw("raid_den_den_mushi", [
"................",
"......kk........",
".....kRRk.......",
"....kRrrRk......",
"...kRrRRrRk.....",
"...kRrRrRrk.....",
"...kRrRRrRk..kk.",
"....kRrrRk..kYYk",
"..kkkkRRkkkkYYk.",
".kYYYYYYYYYYYk..",
"kYyYYYYYYYYYk...",
"kYYYYYYYYYYk....",
".kkkkkkkkkk.....",
"..kSk...........",
"..kSSk..........",
"...kk..........."], {"k": K, "R": R, "r": r, "Y": c(0xe8c070), "y": c(0x3a2a10), "S": c(0x555555)})

def tint(base, dark): return {"k": K, "B": c(base), "b": c(dark), "W": W, "G": G, "g": g}
SHAPES = {
 "medal": [
"................",
"....bBb..bBb....",
".....bBbbBb.....",
"......bBBb......",
".......bb.......",
"......kGGk......",
".....kGggGk.....",
"....kGgGGgGk....",
"....kGGWWGGk....",
"....kGgWWgGk....",
"....kGGggGGk....",
".....kGGGGk.....",
"......kkkk......",
"................",
"................",
"................"],
 "horn": [
"................",
"............kk..",
"...........kWk..",
"..........kWWk..",
".........kWWBk..",
"........kWWBk...",
".......kWWBbk...",
"......kWWBbk....",
".....kWWBbk.....",
"....kWWBbk......",
"...kBBBbk.......",
"..kbbbbk........",
"..kbbbk.........",
"...kkk..........",
"................",
"................"],
 "hat": [
"................",
"......kkkk......",
".....kBBBBk.....",
"....kBBBBBBk....",
"....kBWWWWBk....",
"...kBBBBBBBBk...",
"...kGGGGGGGGk...",
".kkBBBBBBBBBBkk.",
"kbBBBBBBBBBBBBbk",
".kbbbbbbbbbbbbk.",
"..kkkkkkkkkkkk..",
"................",
"................",
"................",
"................",
"................"],
 "flag": [
"k...............",
"kkkkkkkkkkkkkk..",
"kBBBBBBBBBBBBBk.",
"kBBBBWWWWBBBBBk.",
"kBBBWWWWWWBBBBk.",
"kBBBWbWWbWBBBBk.",
"kBBBWWWWWWBBBBk.",
"kBBBBWWWWBBBBBk.",
"kBBWBBWWBBWBBBk.",
"kBBBWBBBBWBBBBk.",
"kBBWBBBBBBWBBBk.",
"kkkkkkkkkkkkkk..",
"k...............",
"k...............",
"k...............",
"k..............."],
 "tassel": [
"................",
"......kkkk......",
".....kGGGGk.....",
".....kGggGk.....",
"......kGGk......",
"......kBBk......",
".....kBBBBk.....",
".....kBbBBk.....",
"....kBBbBBBk....",
"....kBbBbBBk....",
"....kBBbBbBk....",
"...kBbBBbBBBk...",
"...kBBbBBbBBk...",
"...kbkbkbkbkk...",
"................",
"................"],
 "hilt": [
"................",
"..............k.",
".............kWk",
"............kWk.",
"...........kWk..",
"..........kWk...",
".........kWk....",
"....kk..kWk.....",
"....kGkkWk......",
".....kGGk.......",
"......kGGk......",
".....kBkkGk.....",
"....kBk..kk.....",
"...kBk..........",
"..kBk...........",
"..kk............"],
 "coat": [
"................",
"....kkk..kkk....",
"...kBBBkkBBBk...",
"..kBBBWkkWBBBk..",
"..kBBBWWWWBBBk..",
".kBBBkBWWBkBBBk.",
".kBBkkBGGBkkBBk.",
".kBk.kBBBBk.kBk.",
".kGk.kBGGBk.kGk.",
"..k..kBBBBk..k..",
".....kBBBBk.....",
".....kBbbBk.....",
"....kBBkkBBk....",
"....kBk..kBk....",
"....kkk..kkk....",
"................"],
}
TROPHIES = {
 "final_war": ("medal", 0x3fa7d6, 0x1d5f80),
 "beasts": ("horn", 0x9b5fc0, 0x5a2d77),
 "big_mom": ("hat", 0xe36fae, 0x8f3a69),
 "blackbeard": ("flag", 0x2b2b2b, 0x111111),
 "whitebeard": ("tassel", 0xe8e8ff, 0x9a9ab8),
 "red_hair": ("hilt", 0xc8262b, 0x7a1214),
 "rocks": ("flag", 0x7a1010, 0x3a0505),
 "roger": ("coat", 0xc81e1e, 0x7a1010),
}
for raid, (shape, base, dark) in TROPHIES.items():
    pal = tint(base, dark)
    if raid == "blackbeard": pal["b"] = c(0x1a1a1a)
    draw("trophy_" + raid, SHAPES[shape], pal)
print("ok")
