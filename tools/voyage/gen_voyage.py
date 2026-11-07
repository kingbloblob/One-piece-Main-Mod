"""Makes the data and assets for sea exploration (packages com.onepiecemod.voyage, plus the castaway cache in treasure).

Usage: python3 tools/voyage/gen_voyage.py <source root>
Writes: loot tables data/onepiece/loot_table/{treasure/castaway, voyage/*}.json, item defs, models and textures for the
Message in a Bottle and the Castaway's Chart, and their names in assets/onepiece/lang/en_us.json.
Achievements for these are in tools/advancements/gen_advancements.py.
"""
import json
import os
import sys

from PIL import Image

SRC = sys.argv[1]
RES = os.path.join(SRC, "src/main/resources")
ASSETS = os.path.join(RES, "assets/onepiece")
DATA = os.path.join(RES, "data/onepiece")


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


# ---------- Loot (26.3: "modifier"/"condition" with "type") ----------

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
DAMAGED = {"type": "minecraft:set_damage", "damage": {"type": "minecraft:uniform", "min": 0.2, "max": 0.7}}


def pool(rolls, entries, chance=None):
    p = {"rolls": rolls if isinstance(rolls, int) else {"type": "minecraft:uniform", "min": rolls[0], "max": rolls[1]},
         "entries": entries}
    if chance is not None:
        p["condition"] = {"type": "minecraft:random_chance", "chance": chance}
    return p


def table(*pools):
    return {"type": "minecraft:chest", "pools": list(pools)}


LOOT = {
    # A castaway's savings, buried under the sandbar's palm.
    "treasure/castaway": table(
        pool((4, 6), [
            item("onepiece:berry", 14, 15, 40),
            item("minecraft:gold_ingot", 10, 2, 6),
            item("minecraft:emerald", 7, 2, 5),
            item("onepiece:sea_pearl", 6, 1, 3),
            item("minecraft:cocoa_beans", 4, 2, 5),
            item("onepiece:sake", 4, 1, 2),
            item("minecraft:spyglass", 3),
            item("minecraft:compass", 3),
            item("minecraft:nautilus_shell", 3, 1, 2),
            item("minecraft:diamond", 2, 1, 2),
        ]),
        pool(1, [
            item("onepiece:message_in_a_bottle", 3),
            item("onepiece:treasure_map", 2),
            item("onepiece:wreck_chart", 2),
            item("minecraft:enchanted_book", 2, None, None, ENCHANT),
            item("minecraft:golden_apple", 2),
        ], chance=0.45),
    ),
    # What's left in a drifting supply boat.
    "voyage/flotsam": table(
        pool((3, 6), [
            item("minecraft:bread", 8, 1, 4),
            item("minecraft:cod", 6, 1, 3),
            item("minecraft:string", 6, 2, 6),
            item("minecraft:oak_planks", 7, 3, 9),
            item("minecraft:iron_nugget", 6, 3, 10),
            item("minecraft:gunpowder", 5, 1, 4),
            item("onepiece:cannonball", 4, 1, 4),
            item("onepiece:berry", 7, 5, 20),
            item("minecraft:paper", 4, 1, 4),
            item("minecraft:emerald", 2, 1, 2),
        ]),
        pool(1, [
            item("onepiece:message_in_a_bottle", 5),
            item("onepiece:sea_chart", 2),
            item("onepiece:castaway_chart", 2),
            item("minecraft:name_tag", 1),
        ], chance=0.5),
    ),
    # The merchant ship's hold (only spills if she's sunk, see WanderingShips).
    "voyage/merchant_hold": table(
        pool((4, 7), [
            item("onepiece:berry", 10, 20, 50),
            item("minecraft:sugar", 6, 4, 12),
            item("minecraft:cocoa_beans", 5, 3, 9),
            item("minecraft:emerald", 6, 2, 6),
            item("minecraft:white_wool", 5, 4, 12),
            item("minecraft:honey_bottle", 3, 1, 3),
            item("onepiece:sake", 4, 1, 3),
            item("minecraft:gold_ingot", 4, 1, 4),
            item("onepiece:sea_pearl", 2, 1, 2),
        ]),
    ),
    # A derelict's forgotten chest.
    "voyage/derelict": table(
        pool((4, 7), [
            item("onepiece:berry", 10, 10, 35),
            item("minecraft:iron_ingot", 8, 2, 6),
            item("minecraft:gold_nugget", 7, 4, 14),
            item("onepiece:cannonball", 6, 2, 6),
            item("minecraft:gunpowder", 5, 2, 5),
            item("minecraft:rotten_flesh", 4, 1, 4),
            item("minecraft:compass", 2),
            item("minecraft:iron_sword", 3, None, None, DAMAGED),
            item("minecraft:emerald", 3, 1, 3),
        ]),
        pool(1, [
            item("onepiece:treasure_map", 3),
            item("onepiece:wreck_chart", 2),
            item("onepiece:message_in_a_bottle", 3),
            item("onepiece:castaway_chart", 2),
        ], chance=0.5),
    ),
    # A ghost ship's chest: the dead keep their gold.
    "voyage/ghost_ship": table(
        pool((5, 8), [
            item("onepiece:berry", 12, 25, 60),
            item("minecraft:gold_ingot", 10, 3, 9),
            item("minecraft:emerald", 6, 3, 7),
            item("minecraft:diamond", 4, 1, 3),
            item("minecraft:bone", 6, 2, 6),
            item("minecraft:soul_lantern", 3, 1, 2),
            item("onepiece:sea_pearl", 4, 1, 3),
            item("minecraft:golden_apple", 2),
            item("minecraft:music_disc_13", 1),
        ]),
        pool(1, [
            item("onepiece:hoard_map", 2),
            item("minecraft:enchanted_book", 3, None, None, {"type": "minecraft:enchant_with_levels", "levels": 20}),
            item("minecraft:iron_sword", 2, None, None, ENCHANT),
            item("minecraft:heart_of_the_sea", 1),
        ], chance=0.6),
    ),
}

for name, data in LOOT.items():
    write(os.path.join(DATA, "loot_table", name + ".json"), data)

# ---------- Items: textures, models, item defs, names ----------

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


# A green glass bottle lying on its side, a cork in its neck and a rolled note inside.
BOTTLE = [
    "................",
    "................",
    "...........cc...",
    "..........cCcc..",
    ".........gwcc...",
    "........gwgg....",
    ".......gwhpg....",
    "......ghppPg....",
    ".....gwpppg.....",
    "....gwPpphg.....",
    "...gwhpPpg......",
    "...ggppphg......",
    "...gGgpgg.......",
    "....gGGg........",
    "................",
    "................",
]
BOTTLE_COLORS = {"g": hexc("2f7a4a"), "G": hexc("1f5634"), "w": hexc("9fe0b0"), "h": hexc("5cae78"),
                 "p": hexc("efe2bc"), "P": hexc("c9b483"), "c": hexc("a6743f"), "C": hexc("7a5228")}

# A parchment chart: blue sea, a little yellow sandbar with a palm, and the red X.
CHART = [
    "................",
    "..bbbbbbbbbbbb..",
    ".bssssssssssssb.",
    ".bswssssssswssb.",
    ".bssssslllssssb.",
    ".bsssslllllsss..",
    "..bssssLlgssssb.",
    ".bsssssLgggsssb.",
    ".bsswsyyLyysssb.",
    ".bssyyyyyrryssb.",
    "..bssyyyyyrsssb.",
    ".bsssssssssswsb.",
    ".bswsssssssssb..",
    ".bssssssssssssb.",
    "..bbbbbbbbbbbb..",
    "................",
]
CHART_COLORS = {"b": hexc("8a6236"), "s": hexc("6fa6c9"), "w": hexc("d8eef7"), "y": hexc("e9d48c"),
                "l": hexc("3f8f3a"), "g": hexc("2d6b2a"), "L": hexc("6b4a2a"), "r": hexc("c0281e")}

tex = os.path.join(ASSETS, "textures/item")
os.makedirs(tex, exist_ok=True)
from_rows(BOTTLE, BOTTLE_COLORS).save(os.path.join(tex, "message_in_a_bottle.png"))
from_rows(CHART, CHART_COLORS).save(os.path.join(tex, "castaway_chart.png"))

NAMES = {"message_in_a_bottle": "Message in a Bottle", "castaway_chart": "Castaway's Chart"}
for name in NAMES:
    write(os.path.join(ASSETS, "items", name + ".json"), {"model": {"type": "minecraft:model", "model": "onepiece:item/" + name}})
    write(os.path.join(ASSETS, "models/item", name + ".json"),
          {"parent": "minecraft:item/generated", "textures": {"layer0": "onepiece:item/" + name}})

lang_path = os.path.join(ASSETS, "lang/en_us.json")
with open(lang_path) as f:
    lang = json.load(f)
for name, title in NAMES.items():
    lang["item.onepiece." + name] = title
with open(lang_path, "w") as f:
    json.dump(lang, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("voyage assets written:", len(LOOT), "loot tables,", len(NAMES), "items")
