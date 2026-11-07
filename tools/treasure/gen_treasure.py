"""Makes the data and assets for treasure maps and buried loot (package com.onepiecemod.treasure).

Usage: python3 tools/treasure/gen_treasure.py <source root> [vanilla client jar]
Writes: loot tables data/onepiece/loot_table/treasure/*.json, the dig_spot blockstate + models, item defs and
models for the three maps, and the textures (drawn here; dig_spot's top is painted onto vanilla coarse dirt
when the jar is given, else the old texture is kept).
"""
import io
import json
import os
import random
import sys
import zipfile

from PIL import Image

SRC = sys.argv[1]
JAR = sys.argv[2] if len(sys.argv) > 2 else None
RES = os.path.join(SRC, "src/main/resources")
ASSETS = os.path.join(RES, "assets/onepiece")


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


# ---------- Loot ----------

def item(name, weight, lo=None, hi=None, *extra):
    e = {"type": "minecraft:item", "name": name, "weight": weight}
    mods = []
    if lo is not None:
        mods.append({"type": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": lo, "max": hi}})
    mods.extend(extra)
    if mods:
        e["modifier"] = mods
    return e


ENCHANT = {"type": "minecraft:enchant_randomly"}


def pool(rolls, entries, chance=None):
    p = {"rolls": rolls if isinstance(rolls, int) else {"type": "minecraft:uniform", "min": rolls[0], "max": rolls[1]},
         "entries": entries}
    if chance is not None:
        p["condition"] = {"type": "minecraft:random_chance", "chance": chance}
    return p


def table(*pools):
    return {"type": "minecraft:chest", "pools": list(pools)}


LOOT = {
    # A small pirate stash: Berries and gold, sometimes gems.
    "buried": table(
        pool((4, 7), [
            item("onepiece:berry", 14, 15, 45),
            item("minecraft:gold_ingot", 12, 2, 7),
            item("minecraft:gold_nugget", 8, 6, 20),
            item("minecraft:emerald", 7, 2, 5),
            item("onepiece:sea_pearl", 5, 1, 2),
            item("minecraft:diamond", 3, 1, 2),
            item("minecraft:golden_apple", 3),
            item("onepiece:sake", 4, 1, 2),
            item("minecraft:iron_ingot", 6, 2, 6),
            item("onepiece:sea_chart", 2),
        ]),
        pool(1, [
            item("onepiece:berry_block", 2),
            item("minecraft:enchanted_book", 3, None, None, ENCHANT),
            item("minecraft:golden_sword", 2, None, None, ENCHANT),
            item("onepiece:treasure_map", 2),
            item("onepiece:wreck_chart", 1),
        ], chance=0.35),
    ),
    # A captain's hoard: a lot more of everything, and (added in code) a 10% Devil Fruit.
    "hoard": table(
        pool((7, 11), [
            item("onepiece:berry", 12, 32, 64),
            item("onepiece:berry_block", 6, 1, 3),
            item("minecraft:gold_ingot", 10, 6, 16),
            item("minecraft:gold_block", 4, 1, 3),
            item("minecraft:emerald", 7, 4, 10),
            item("minecraft:diamond", 6, 2, 5),
            item("onepiece:sea_pearl", 5, 2, 4),
            item("onepiece:shandora_gold_ingot", 4, 1, 4),
            item("minecraft:golden_apple", 4, 1, 2),
            item("minecraft:diamond_sword", 2, None, None, ENCHANT),
            item("minecraft:diamond_chestplate", 2, None, None, ENCHANT),
        ]),
        pool(1, [
            item("minecraft:enchanted_golden_apple", 2),
            item("minecraft:heart_of_the_sea", 2),
            item("minecraft:enchanted_book", 3, None, None, {"type": "minecraft:enchant_with_levels", "levels": 30}),
            item("onepiece:hoard_map", 1),
        ], chance=0.6),
    ),
    # A sunken ship's strongbox.
    "wreck": table(
        pool((5, 8), [
            item("onepiece:berry", 12, 20, 50),
            item("minecraft:gold_ingot", 12, 3, 9),
            item("minecraft:emerald", 8, 2, 6),
            item("minecraft:diamond", 4, 1, 3),
            item("onepiece:sea_pearl", 8, 1, 4),
            item("minecraft:prismarine_crystals", 5, 2, 6),
            item("minecraft:nautilus_shell", 4, 1, 2),
            item("onepiece:cannonball", 5, 2, 6),
            item("minecraft:golden_apple", 3),
        ]),
        pool(1, [
            item("minecraft:heart_of_the_sea", 2),
            item("minecraft:trident", 1),
            item("minecraft:enchanted_book", 3, None, None, ENCHANT),
            item("onepiece:berry_block", 2),
        ], chance=0.4),
    ),
    # The navigator's chest: charts to the next treasure.
    "wreck_map": table(
        pool(1, [
            item("onepiece:treasure_map", 3),
            item("onepiece:wreck_chart", 2),
        ]),
        pool((2, 4), [
            item("minecraft:paper", 6, 2, 6),
            item("minecraft:compass", 3),
            item("onepiece:sea_chart", 2),
            item("minecraft:feather", 4, 1, 3),
            item("minecraft:ink_sac", 4, 1, 3),
            item("onepiece:berry", 5, 5, 15),
        ]),
    ),
}

for name, data in LOOT.items():
    write(os.path.join(RES, "data/onepiece/loot_table/treasure", name + ".json"), data)

# ---------- Models ----------

for name in ("treasure_map", "wreck_chart", "hoard_map"):
    write(os.path.join(ASSETS, "items", name + ".json"), {"model": {"type": "minecraft:model", "model": "onepiece:item/" + name}})
    write(os.path.join(ASSETS, "models/item", name + ".json"),
          {"parent": "minecraft:item/generated", "textures": {"layer0": "onepiece:item/" + name}})

write(os.path.join(ASSETS, "blockstates/dig_spot.json"), {"variants": {"": {"model": "onepiece:block/dig_spot"}}})
write(os.path.join(ASSETS, "models/block/dig_spot.json"), {
    "parent": "minecraft:block/cube_bottom_top",
    "textures": {"top": "onepiece:block/dig_spot_top", "side": "minecraft:block/coarse_dirt",
                 "bottom": "minecraft:block/dirt"}})
write(os.path.join(ASSETS, "items/dig_spot.json"), {"model": {"type": "minecraft:model", "model": "onepiece:block/dig_spot"}})

# ---------- Textures ----------

T = (0, 0, 0, 0)


def hexc(h, a=255):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def from_rows(rows, palette):
    img = Image.new("RGBA", (16, 16), T)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                img.putpixel((x, y), palette[ch])
    return img


# A torn, rolled parchment with a red X and a dotted trail.
MAP_ROWS = [
    "................",
    "..bbbbbbbbbbbb..",
    ".bppppppppppppb.",
    ".bpqpppppppqppb.",
    ".bppppdpppppppb.",
    ".bpppdpdppprpr..",
    "..bppppppdpprpb.",
    ".bpppppppppdrprb",
    ".bpppqppppppppb.",
    ".bpppppdpppppqb.",
    "..bpppdpdpppppb.",
    ".bppppppppqpppb.",
    ".bppqpppppppppb.",
    ".bppppppppppppb.",
    "..bbbbbbbbbbbb..",
    "................",
]
PARCH = {"b": hexc("8a6236"), "p": hexc("e8d3a0"), "q": hexc("d6bc82"), "d": hexc("8f7b5a"), "r": hexc("c0281e")}
SOGGY = {"b": hexc("4b5f62"), "p": hexc("b9c6b4"), "q": hexc("9fb2a6"), "d": hexc("4f6d7a"), "r": hexc("2f5fa8")}
HOARD = {"b": hexc("3a2514"), "p": hexc("c9a867"), "q": hexc("b08e4c"), "d": hexc("5b4426"), "r": hexc("e0b020")}

tex = os.path.join(ASSETS, "textures/item")
os.makedirs(tex, exist_ok=True)
from_rows(MAP_ROWS, PARCH).save(os.path.join(tex, "treasure_map.png"))

# The wreck chart: soggy blue-green paper with a little sunken ship instead of the trail.
WRECK_ROWS = [
    "................",
    "..bbbbbbbbbbbb..",
    ".bppppppppppppb.",
    ".bpqppppdpppqpb.",
    ".bppppppdpppppb.",
    ".bpppppddrpppp..",
    "..bppppppdppppb.",
    ".bpppdddddddppb.",
    ".bppppdddddpppb.",
    ".bqqqqqqqqqqqqb.",
    "..bqpqqqpqqqpqb.",
    ".bqqqqqqqqqqqqb.",
    ".bppqppppppqppb.",
    ".bppppppppppppb.",
    "..bbbbbbbbbbbb..",
    "................",
]
from_rows(WRECK_ROWS, SOGGY).save(os.path.join(tex, "wreck_chart.png"))

# The hoard map: old dark-edged gold leaf with a skull and a gold X.
HOARD_ROWS = [
    "................",
    "..bbbbbbbbbbbb..",
    ".bppppppppppppb.",
    ".bppqpppppppqpb.",
    ".bpppddddpppppb.",
    ".bppddddddpppp..",
    "..bpdpddpdpprpb.",
    ".bppddddddprprb.",
    ".bpppdpdpppprpb.",
    ".bpppppppppprprb",
    "..bpqppppppppppb",
    ".bpppppdpdppqpb.",
    ".bppppppdpppppb.",
    ".bppqpppdpdpppb.",
    "..bbbbbbbbbbbb..",
    "................",
]
from_rows(HOARD_ROWS, HOARD).save(os.path.join(tex, "hoard_map.png"))

# Dig spot top: vanilla coarse dirt, darker loose soil in a patch, and a red X scratched into it.
block_tex = os.path.join(ASSETS, "textures/block")
os.makedirs(block_tex, exist_ok=True)
base = None
if JAR:
    with zipfile.ZipFile(JAR) as z:
        base = Image.open(io.BytesIO(z.read("assets/minecraft/textures/block/coarse_dirt.png"))).convert("RGBA")
if base is not None:
    img = base.copy()
    rnd = random.Random(7)
    for y in range(16):
        for x in range(16):
            dx, dy = x - 7.5, y - 7.5
            if dx * dx + dy * dy < 44 + rnd.randint(-6, 6):
                r, g, b, a = img.getpixel((x, y))
                img.putpixel((x, y), (int(r * 0.72), int(g * 0.68), int(b * 0.62), 255))
    red, dark = (178, 34, 26, 255), (120, 20, 16, 255)
    for i in range(3, 13):
        for (x, y) in ((i, i), (i, 15 - i)):
            img.putpixel((x, y), red)
            if x + 1 < 16:
                img.putpixel((x + 1, y), dark if i % 3 == 0 else red)
    img.save(os.path.join(block_tex, "dig_spot_top.png"))
print("treasure data written to", SRC)
