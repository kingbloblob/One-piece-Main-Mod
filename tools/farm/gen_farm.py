#!/usr/bin/env python3
"""Writes every data and asset file for farming and ranching (Java: com.onepiecemod.farm) and merges its
entries into the shared files. Safe to run again: own files are rewritten, shared entries replaced by id.

    python3 -I gen_farm.py <source folder>

Own files: textures, models, blockstates, item definitions, loot tables, crafting recipes (data/onepiece/recipe/farm_*),
lang assets/onepiece_farm/lang/en_us.json, item tags onepiece:ranch_fodder / onepiece:island_seeds / onepiece:island_crops.
Union-merges (shared): minecraft block tags crops, bee_growables, maintains_farmland, mineable/axe, mineable/pickaxe;
minecraft item tag villager_plantable_seeds. Merges by id: onepiece/station_recipes.json (Ship's Galley dishes),
onepiece/item_descriptions.json, onepiece/item_sources.json.
Keep the CROPS table in step with IslandCrop.java (same ids, names, homes)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import farm_textures as tx  # noqa: E402

# id, crop name, produce name, home (for text), stage style + colours, produce icon
CROPS = [
    ("east_blue_cabbage", "East Blue Cabbage", "East Blue Cabbage", "East Blue (Conomi, Orange Town, Loguetown)",
     ("gourd", "#4f8f3a", "#9fd86a", "#6fb048", False), ("gourd", "#9fd86a", "#6fb048", False), "#c8d870"),
    ("wano_rice", "Wano Rice", "Wano Rice", "Wano, Kuri and Onigashima",
     ("grain", "#6a9a3a", "#f0e8c0"), ("grain", "#7a9a4a", "#f4eed0"), "#e8dfb0"),
    ("kibi_millet", "Kibi Millet", "Kibi Millet", "Wano and Kuri",
     ("grain", "#7a9a3a", "#e0b040"), ("grain", "#8a9a3a", "#e8b848"), "#d9a441"),
    ("cloud_wheat", "Cloud Wheat", "Cloud Wheat", "Skypiea",
     ("grain", "#8fb86a", "#ffffff"), ("grain", "#a0c070", "#ffffff"), "#e8f0ff"),
    ("elbaph_barley", "Elbaph Barley", "Elbaph Barley", "Elbaph, the land of giants",
     ("grain_tall", "#6f8f3a", "#c9a25a"), ("grain", "#7f8f3a", "#d0aa60"), "#b89048"),
    ("frost_turnip", "Frost Turnip", "Frost Turnip", "Drum Island and frozen Punk Hazard",
     ("root", "#5f8f8a", "#e8e6f0", "#8a5aa8"), ("rootveg", "#eceaf4", "#8a5aa8", "#5f8f8a"), "#b8a0d0"),
    ("jungle_yam", "Jungle Yam", "Jungle Yam", "Jaya and Little Garden",
     ("root", "#4f7f2a", "#8a5a3a"), ("longroot", "#9a6a42", "#4f7f2a"), "#8a6a3a"),
    ("dressrosa_tomato", "Dressrosa Tomato", "Dressrosa Tomato", "Dressrosa and Green Bit",
     ("fruit", "#3f7f2a", "#d8322a"), ("round", "#d8322a"), "#e8d070"),
    ("snake_pepper", "Snake Pepper", "Snake Pepper", "Amazon Lily",
     ("fruit_long", "#3f6f2a", "#b81f4f"), ("long", "#c8203a"), "#e8c050"),
    ("sea_grape", "Sea Grapes", "Sea Grapes", "Fishman Island and Sabaody",
     ("fruit", "#3a8a5a", "#4fd8a8"), ("beads", "#4fd8a8", "#2a6a4a"), "#3a8a6a"),
    ("totland_cacao", "Totland Cacao", "Totland Cacao Pod", "Whole Cake Island and Cacao Island",
     ("bush", "#4a6f2a", "#a8622a"), ("pod", "#b0682a"), "#6a3a20"),
    ("mink_tea", "Mink Tea", "Mink Tea Leaves", "Zou, on the elephant's back",
     ("leaf", "#3f7a3a", "#6fb84a"), ("leaves", "#5fa83a"), "#5a7a3a"),
    ("ghost_pumpkin", "Ghost Pumpkin", "Ghost Pumpkin", "Thriller Bark, Kuraigana and the Withered Forest",
     ("gourd", "#5a6a4a", "#b8c8d8", None, True), ("gourd", "#c0d0e0", None, True), "#e0e8f0"),
    ("sand_melon", "Sand Melon", "Sand Melon Slice", "Alabasta",
     ("gourd", "#7a8a3a", "#d8c06a", "#8a9a3a", False), ("slice", "#e8584a", "#6a8a3a"), "#2a2020"),
]

RANCH = {
    "fresh_milk": ("Fresh Milk", "Creamy milk from a ranch cow, goat or Drum reindeer. Cooks into cheese and sweets.",
                   lambda: tx.bottle("fresh_milk", "#f4f4ec")),
    "cheese": ("Cheese", "Made from Fresh Milk at the Ship's Galley.", lambda: tx.wedge("cheese", "#f0c848", "#c89a28")),
    "truffle": ("Truffle", "Pigs fed at a Ranch Trough root these up. A rare treat for risotto.",
                lambda: tx.lump("truffle", "#4a3426", "#8a6a50")),
    "south_bird_egg": ("South Bird Egg", "From a well-fed South Bird. The yolk always points south.",
                       lambda: tx.egg("south_bird_egg", "#e8e0c8", "#8a6a3a")),
    "duck_egg": ("Giant Duck Egg", "From a Spot-billed Duck like Carue. Big enough for a whole breakfast.",
                 lambda: tx.egg("duck_egg", "#d8ecf0", None, True)),
    "ranch_manure": ("Ranch Manure", "Left by ranch animals. Use it on a crop: every crop in a 5x5 patch grows a step.",
                     lambda: tx.lump("ranch_manure", "#6a4a28", "#4a3018")),
    "watering_can": ("Watering Can", "Right-click water to fill. Waters a 3x3 patch of farmland and helps the crops grow.",
                     tx.watering_can),
}

# Kibi Dango belongs to the workshop feature (tools/workshop); kibi millet makes plain dango here.
# id, name, description, galley ingredients [(item or #tag, count)], count made, needs a Cook, icon (kind, food, accent)
DISHES = [
    ("omurice", "Omurice", "Fried Wano rice wrapped in an omelette with tomato sauce. Haste for 12 minutes.",
     [("onepiece:wano_rice", 2), ("minecraft:egg", 1), ("onepiece:dressrosa_tomato", 1)], 1, False, ("plate", "#f0d040", "#d8322a")),
    ("cloud_bread", "Cloud Bread", "Light as a Skypiea cloud. Slow Falling and Jump Boost for 10 minutes.",
     [("onepiece:cloud_wheat", 3)], 2, False, ("loaf", "#f8f4e8", None)),
    ("sand_melon_sorbet", "Sand Melon Sorbet", "An icy Alabasta treat. Fire Resistance for 15 minutes, Speed for 6.",
     [("onepiece:sand_melon", 2), ("minecraft:snowball", 1), ("minecraft:sugar", 1), ("minecraft:bowl", 1)], 1, False,
     ("bowl", "#f08878", "#ffffff")),
    ("frost_turnip_stew", "Frost Turnip Stew", "A Drum Island stew. Winter Islands can't freeze you for 20 minutes, plus Resistance.",
     [("onepiece:frost_turnip", 2), ("minecraft:potato", 1), ("minecraft:bowl", 1)], 1, False, ("bowl", "#c8b8d8", "#8a5aa8")),
    ("totland_chocolate", "Totland Chocolate", "Big Mom would want this. Speed and extra hearts for 12 minutes.",
     [("onepiece:totland_cacao", 3), ("minecraft:sugar", 1), ("onepiece:fresh_milk", 1)], 2, False, ("bar", "#6a3a20", "#c8a070")),
    ("ghost_pumpkin_pie", "Ghost Pumpkin Pie", "Spooky and sweet. Night Vision for 15 minutes and Resistance for 10.",
     [("onepiece:ghost_pumpkin", 1), ("minecraft:sugar", 1), ("minecraft:egg", 1)], 1, False, ("plate", "#c8d8e8", "#8a7aa8")),
    ("dressrosa_paella", "Dressrosa Paella", "Rice, tomato and fish, the way the Corrida fighters like it. Strength for 12 minutes.",
     [("onepiece:wano_rice", 1), ("onepiece:dressrosa_tomato", 2), ("#onepiece:raw_fish", 1)], 1, False,
     ("plate", "#e8b830", "#d8322a")),
    ("giants_ale", "Giant's Ale", "Brewed in Elbaph. Strength II for 8 minutes and lots of extra hearts for 15.",
     [("onepiece:elbaph_barley", 3), ("minecraft:glass_bottle", 1)], 1, False, ("mug", "#d8a030", None)),
    ("mink_tea_cup", "Mink Tea", "Zou's leaf tea. Speed and Night Vision for 15 minutes.",
     [("onepiece:mink_tea", 2), ("minecraft:glass_bottle", 1)], 1, False, ("bottle", "#8ab840", None)),
    ("sea_grape_salad", "Sea Grape Salad", "A Fishman Island salad. Water Breathing for 15 minutes and Dolphin's Grace for 8.",
     [("onepiece:sea_grape", 2), ("minecraft:kelp", 1), ("minecraft:bowl", 1)], 1, False, ("bowl", "#4fd8a8", "#2a8a5a")),
    ("kuja_curry", "Kuja Curry", "Hot enough for the Amazon Lily warriors. Fire Resistance for 15 minutes and Strength for 10.",
     [("onepiece:snake_pepper", 2), ("onepiece:wano_rice", 1), ("minecraft:beef", 1), ("minecraft:bowl", 1)], 1, False,
     ("bowl", "#c8782a", "#c8203a")),
    ("jungle_yam_stew", "Jungle Yam Stew", "A filling Jaya stew. Extra hearts for 15 minutes and a minute of Regeneration.",
     [("onepiece:jungle_yam", 2), ("minecraft:carrot", 1), ("minecraft:bowl", 1)], 1, False, ("bowl", "#b8885a", "#e8902a")),
    ("baratie_cabbage_rolls", "Baratie Cabbage Rolls", "Zeff's recipe. Resistance and Absorption for 10 minutes.",
     [("onepiece:east_blue_cabbage", 2), ("minecraft:porkchop", 1)], 2, False, ("plate", "#a8d870", "#c8783a")),
    ("truffle_risotto", "Truffle Risotto", "Only a Cook gets it right. Luck II for 15 minutes: much better loot and fishing.",
     [("onepiece:wano_rice", 1), ("onepiece:truffle", 1), ("onepiece:fresh_milk", 1), ("minecraft:bowl", 1)], 1, True,
     ("bowl", "#f0e8d0", "#4a3426")),
    ("ranch_breakfast", "Sanji's Ranch Breakfast", "Everything the ranch makes on one plate. Resistance, extra hearts and Haste for 15 minutes.",
     [("onepiece:south_bird_egg", 1), ("onepiece:duck_egg", 1), ("onepiece:cheese", 1), ("onepiece:truffle", 1),
      ("minecraft:bread", 1)], 1, True, ("plate", "#f0d040", "#c87a3a")),
]

EXTRA_GALLEY = [
    {"id": "cheese", "station": "ships_galley", "result": "onepiece:cheese", "count": 1,
     "ingredients": [{"item": "onepiece:fresh_milk", "count": 2}]},
]

BLOCKS = {
    "seed_vault": ("Seed Vault", "Bank one seed of each island crop, then draw a free seed of every banked kind each day. Rewards at 3, 6, 9 and all 14."),
    "sprinkler": ("Sprinkler", "Waters farmland 3 blocks around it and makes crops grow faster. Needs water touching it."),
    "dial_sprinkler": ("Dial Sprinkler", "A Skypiea sprinkler: the dial shell holds its own water. Reaches 5 blocks, no water needed."),
    "ranch_trough": ("Ranch Trough", "Fill with fodder. Animals within 8 blocks give milk, eggs, wool, truffles and manure, and breed on their own. Put a chest under or beside it."),
    "straw_hat_scarecrow": ("Straw Hat Scarecrow", "Marks a crew farm plot. A crewmate set to Work within 6 blocks of it farms, sows, feeds troughs and stores the harvest."),
}

FODDER = ["minecraft:wheat", "minecraft:hay_block", "minecraft:carrot", "minecraft:potato", "minecraft:beetroot",
          "minecraft:apple", "minecraft:melon_slice", "minecraft:sugar_cane", "minecraft:kelp", "minecraft:sweet_berries",
          "minecraft:short_grass", "minecraft:fern"]


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def merge_list(path, entries, key):
    data = json.load(open(path))
    ids = {e[key] for e in entries}
    data = [e for e in data if e.get(key) not in ids] + entries
    write(path, data)


def union_tag(path, values):
    data = json.load(open(path)) if os.path.exists(path) else {"values": []}
    for v in values:
        if v not in data["values"]:
            data["values"].append(v)
    write(path, data)


def save(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def stage_image(cid, age, style):
    kind = style[0]
    if kind == "grain":
        return tx.crop_grain(cid, age, style[1], style[2])
    if kind == "grain_tall":
        return tx.crop_grain(cid, age, style[1], style[2], tall=True)
    if kind == "root":
        return tx.crop_root(cid, age, style[1], style[2], style[3] if len(style) > 3 else None)
    if kind == "fruit":
        return tx.crop_fruit(cid, age, style[1], style[2])
    if kind == "fruit_long":
        return tx.crop_fruit(cid, age, style[1], style[2], long=True)
    if kind == "bush":
        return tx.crop_bush(cid, age, style[1], style[2])
    if kind == "leaf":
        return tx.crop_leaf(cid, age, style[1], style[2])
    if kind == "gourd":
        return tx.crop_gourd(cid, age, style[1], style[2], style[3], style[4])
    raise ValueError(kind)


def produce_image(cid, icon):
    kind = icon[0]
    if kind == "grain":
        return tx.grain_bundle(cid, icon[1], icon[2])
    if kind == "root":
        return tx.root_veg(cid, icon[1], icon[2], icon[3])
    if kind == "rootveg":
        return tx.root_veg(cid, icon[1], icon[2], icon[3])
    if kind == "longroot":
        return tx.long_root(cid, icon[1], icon[2])
    if kind == "round":
        return tx.round_fruit(cid, icon[1])
    if kind == "long":
        return tx.round_fruit(cid, icon[1], long=True)
    if kind == "beads":
        return tx.bead_cluster(cid, icon[1], icon[2])
    if kind == "pod":
        return tx.pod(cid, icon[1])
    if kind == "leaves":
        return tx.leaves(cid, icon[1])
    if kind == "gourd":
        return tx.gourd(cid, icon[1], icon[2], icon[3])
    if kind == "slice":
        return tx.melon_slice(cid, icon[1], icon[2])
    raise ValueError(kind)


def dish_image(did, icon):
    kind, food, accent = icon
    if kind in ("plate", "bowl", "skewer", "bar", "loaf"):
        return tx.plate(did, food, accent, kind)
    if kind == "mug":
        return tx.bottle(did, food, mug=True)
    return tx.bottle(did, food)


def item_def(assets, name, model=None):
    write(f"{assets}/items/{name}.json", {"model": {"type": "minecraft:model", "model": model or f"onepiece:item/{name}"}})


def flat_item(assets, name):
    item_def(assets, name)
    write(f"{assets}/models/item/{name}.json", {"parent": "minecraft:item/generated", "textures": {"layer0": f"onepiece:item/{name}"}})


def self_drop(name):
    return {"type": "minecraft:block", "pools": [{"condition": {"type": "minecraft:survives_explosion"},
            "entries": [{"type": "minecraft:item", "name": f"onepiece:{name}"}], "rolls": 1}],
            "random_sequence": f"onepiece:blocks/{name}"}


def crop_loot(cid):
    block = f"onepiece:{cid}_crop"
    grown = {"type": "minecraft:match_block", "blocks": block, "state": {"age": "3"}}
    return {
        "type": "minecraft:block",
        "modifier": {"type": "minecraft:explosion_decay"},
        "pools": [
            {"entries": [{"type": "minecraft:alternatives", "children": [
                {"type": "minecraft:item", "condition": grown, "name": f"onepiece:{cid}",
                 "modifier": {"type": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": 1, "max": 3}}},
                {"type": "minecraft:item", "name": f"onepiece:{cid}_seeds"}]}], "rolls": 1},
            {"condition": grown, "entries": [{"type": "minecraft:item", "name": f"onepiece:{cid}_seeds",
                "modifier": {"type": "minecraft:apply_bonus", "enchantment": "minecraft:fortune",
                             "formula": "minecraft:binomial_with_bonus_count", "parameters": {"extra": 2, "probability": 0.5}}}],
             "rolls": 1},
        ],
        "random_sequence": f"onepiece:blocks/{cid}_crop",
    }


def model_sprinkler(texture):
    t = "#metal"
    faces = lambda: {d: {"texture": t} for d in ("north", "south", "east", "west", "up", "down")}
    return {"parent": "minecraft:block/block", "textures": {"metal": texture, "particle": texture}, "elements": [
        {"from": [5, 0, 5], "to": [11, 2, 11], "faces": faces()},
        {"from": [7, 2, 7], "to": [9, 8, 9], "faces": faces()},
        {"from": [5, 8, 5], "to": [11, 10, 11], "faces": faces()},
        {"from": [2, 8.5, 7.5], "to": [14, 9.5, 8.5], "faces": faces()},
        {"from": [7.5, 8.5, 2], "to": [8.5, 9.5, 14], "faces": faces()},
    ]}


def model_trough(full):
    side = "#side"
    f = lambda: {d: {"texture": side} for d in ("north", "south", "east", "west", "up", "down")}
    elements = [
        {"from": [0, 0, 0], "to": [16, 2, 16], "faces": f()},
        {"from": [0, 2, 0], "to": [16, 8, 2], "faces": f()},
        {"from": [0, 2, 14], "to": [16, 8, 16], "faces": f()},
        {"from": [0, 2, 2], "to": [2, 8, 14], "faces": f()},
        {"from": [14, 2, 2], "to": [16, 8, 14], "faces": f()},
    ]
    textures = {"side": "onepiece:block/ranch_trough_side", "particle": "onepiece:block/ranch_trough_side"}
    if full:
        textures["hay"] = "onepiece:block/ranch_trough_hay"
        elements.append({"from": [2, 2, 2], "to": [14, 6, 14], "faces": {"up": {"texture": "#hay"},
                         "north": {"texture": "#hay"}, "south": {"texture": "#hay"}, "east": {"texture": "#hay"},
                         "west": {"texture": "#hay"}}})
    return {"parent": "minecraft:block/block", "textures": textures, "elements": elements}


def model_scarecrow():
    def box(fr, to, tex, front=None):
        faces = {d: {"texture": tex} for d in ("north", "south", "east", "west", "up", "down")}
        if front:
            faces["north"] = {"texture": front}
        return {"from": fr, "to": to, "faces": faces}
    return {"parent": "minecraft:block/block", "textures": {
        "post": "minecraft:block/stripped_oak_log", "shirt": "onepiece:block/scarecrow_shirt",
        "straw": "onepiece:block/scarecrow_straw", "face": "onepiece:block/scarecrow_face",
        "sack": "onepiece:block/scarecrow_sack", "band": "onepiece:block/scarecrow_hat",
        "particle": "onepiece:block/scarecrow_straw"}, "elements": [
        box([7, 0, 7], [9, 6, 9], "#post"),
        box([5, 5, 6], [11, 11, 10], "#shirt"),
        box([0, 9, 7], [16, 11, 9], "#shirt"),
        box([0, 7, 7.5], [2, 9, 8.5], "#straw"),
        box([14, 7, 7.5], [16, 9, 8.5], "#straw"),
        box([5, 11, 5], [11, 16, 11], "#sack", "#face"),
        box([2, 15, 2], [14, 16, 14], "#straw"),
        box([5, 16, 5], [11, 19, 11], "#band"),
    ]}


def main(source):
    res = os.path.join(source, "src/main/resources")
    assets = os.path.join(res, "assets/onepiece")
    data = os.path.join(res, "data")
    lang = {}
    descriptions = {}
    sources = []

    # ---- Crops, seeds and produce ----
    for cid, crop_name, produce_name, home, style, icon, seed_colour in CROPS:
        variants = {}
        for age in range(4):
            stage = f"{cid}_stage{age}"
            save(stage_image(cid, age, style), f"{assets}/textures/block/{stage}.png")
            write(f"{assets}/models/block/{stage}.json", {"parent": "minecraft:block/crop", "textures": {"crop": f"onepiece:block/{stage}"}})
            variants[f"age={age}"] = {"model": f"onepiece:block/{stage}"}
        write(f"{assets}/blockstates/{cid}_crop.json", {"variants": variants})
        write(f"{data}/onepiece/loot_table/blocks/{cid}_crop.json", crop_loot(cid))

        save(produce_image(cid, icon), f"{assets}/textures/item/{cid}.png")
        save(tx.seeds(f"{cid}_seeds", seed_colour), f"{assets}/textures/item/{cid}_seeds.png")
        flat_item(assets, cid)
        flat_item(assets, f"{cid}_seeds")

        seed_name = (crop_name[:-1] if crop_name.endswith("s") else crop_name) + " Seeds"
        lang[f"block.onepiece.{cid}_crop"] = crop_name
        lang[f"item.onepiece.{cid}"] = produce_name
        lang[f"item.onepiece.{cid}_seeds"] = seed_name
        descriptions[f"onepiece:{cid}_seeds"] = f"Plant on farmland. Grows best on {home}; slowly anywhere else."
        descriptions[f"onepiece:{cid}"] = f"An island crop from {home}. Cook it at the Ship's Galley or feed it to a Ranch Trough."
        sources.append({"item": f"onepiece:{cid}_seeds", "title": "Wild seeds: " + home, "icon": "minecraft:short_grass",
                        "notes": [f"Break grass, ferns and wild plants on {home}: now and then a seed drops.",
                                  "A grown crop drops more seeds. Bank one in a Seed Vault to draw a free seed every day."]})
        sources.append({"item": f"onepiece:{cid}", "title": "Farming", "icon": f"onepiece:{cid}_seeds",
                        "notes": [f"Grow {crop_name} on farmland. Fastest on {home}.",
                                  "Sprinklers, the Watering Can and Ranch Manure speed it up."]})
        write(f"{data}/onepiece/recipe/farm_{cid}_seeds.json", {
            "type": "minecraft:crafting_shapeless", "category": "misc",
            "ingredients": [f"onepiece:{cid}"], "result": {"count": 2, "id": f"onepiece:{cid}_seeds"}})

    # ---- Ranch goods and tools ----
    for rid, (name, text, draw) in RANCH.items():
        save(draw(), f"{assets}/textures/item/{rid}.png")
        flat_item(assets, rid)
        lang[f"item.onepiece.{rid}"] = name
        descriptions[f"onepiece:{rid}"] = text
    for rid, animal in (("fresh_milk", "a cow, goat or Drum Reindeer"), ("truffle", "a pig"),
                        ("south_bird_egg", "a South Bird"), ("duck_egg", "a Spot-billed Duck"),
                        ("ranch_manure", "any ranch animal")):
        sources.append({"item": f"onepiece:{rid}", "title": "Ranching", "icon": "onepiece:ranch_trough",
                        "notes": [f"Keep {animal} near a Ranch Trough filled with fodder.",
                                  "Now and then it leaves this in a chest beside the trough."]})

    # ---- Dishes ----
    recipes = []
    for did, name, text, ingredients, count, cook, icon in DISHES:
        save(dish_image(did, icon), f"{assets}/textures/item/{did}.png")
        flat_item(assets, did)
        lang[f"item.onepiece.{did}"] = name
        descriptions[f"onepiece:{did}"] = text
        ing = []
        for item, n in ingredients:
            if item.startswith("#"):
                ing.append({"tag": item[1:], "icon": "onepiece:striped_mackerel", "name": "Any One Piece Fish", "count": n})
            else:
                ing.append({"item": item, "count": n})
        r = {"id": did, "station": "ships_galley", "result": f"onepiece:{did}", "count": count, "ingredients": ing}
        if cook:
            r["requires"] = {"crew": "cook"}
        recipes.append(r)
    merge_list(f"{res}/onepiece/station_recipes.json", recipes + EXTRA_GALLEY, "id")

    # ---- Blocks ----
    T = "onepiece:block/"
    save(tx.seed_vault_side(), f"{assets}/textures/block/seed_vault_side.png")
    save(tx.seed_vault_top(), f"{assets}/textures/block/seed_vault_top.png")
    save(tx.planks("vault_bottom", "#7a5430"), f"{assets}/textures/block/seed_vault_bottom.png")
    write(f"{assets}/models/block/seed_vault.json", {"parent": "minecraft:block/cube_bottom_top", "textures": {
        "top": T + "seed_vault_top", "bottom": T + "seed_vault_bottom", "side": T + "seed_vault_side"}})
    write(f"{assets}/blockstates/seed_vault.json", {"variants": {"": {"model": T + "seed_vault"}}})

    save(tx.copper("sprinkler"), f"{assets}/textures/block/sprinkler.png")
    save(tx.dial_shell("dial_sprinkler"), f"{assets}/textures/block/dial_sprinkler.png")
    for sid in ("sprinkler", "dial_sprinkler"):
        write(f"{assets}/models/block/{sid}.json", model_sprinkler(T + sid))
        write(f"{assets}/blockstates/{sid}.json", {"variants": {"": {"model": T + sid}}})

    save(tx.trough_side(), f"{assets}/textures/block/ranch_trough_side.png")
    save(tx.hay_top("trough_hay"), f"{assets}/textures/block/ranch_trough_hay.png")
    write(f"{assets}/models/block/ranch_trough.json", model_trough(False))
    write(f"{assets}/models/block/ranch_trough_full.json", model_trough(True))
    write(f"{assets}/blockstates/ranch_trough.json", {"variants": {
        "full=false": {"model": T + "ranch_trough"}, "full=true": {"model": T + "ranch_trough_full"}}})

    save(tx.plaid("scarecrow_shirt"), f"{assets}/textures/block/scarecrow_shirt.png")
    save(tx.straw("scarecrow_straw"), f"{assets}/textures/block/scarecrow_straw.png")
    save(tx.burlap("scarecrow_face"), f"{assets}/textures/block/scarecrow_face.png")
    plain = tx.burlap("scarecrow_sack")
    for x, y in ((4, 6), (5, 6), (10, 6), (11, 6), (5, 10), (6, 11), (7, 11), (8, 11), (9, 11), (10, 10)):
        plain.putpixel((x, y), plain.getpixel((x + 1 if x < 15 else x - 1, y - 1)))
    save(plain, f"{assets}/textures/block/scarecrow_sack.png")
    save(tx.hat_band(), f"{assets}/textures/block/scarecrow_hat.png")
    write(f"{assets}/models/block/straw_hat_scarecrow.json", model_scarecrow())
    write(f"{assets}/blockstates/straw_hat_scarecrow.json", {"variants": {
        "facing=north": {"model": T + "straw_hat_scarecrow"},
        "facing=east": {"model": T + "straw_hat_scarecrow", "y": 90},
        "facing=south": {"model": T + "straw_hat_scarecrow", "y": 180},
        "facing=west": {"model": T + "straw_hat_scarecrow", "y": 270}}})

    for bid, (name, text) in BLOCKS.items():
        item_def(assets, bid, model=T + bid)
        lang[f"block.onepiece.{bid}"] = name
        descriptions[f"onepiece:{bid}"] = text
        write(f"{data}/onepiece/loot_table/blocks/{bid}.json", self_drop(bid))

    # ---- Crafting recipes ----
    def shaped(name, pattern, key, result, count=1):
        write(f"{data}/onepiece/recipe/farm_{name}.json", {"type": "minecraft:crafting_shaped", "category": "misc",
              "key": key, "pattern": pattern, "result": {"count": count, "id": result}})

    def shapeless(name, ingredients, result, count=1):
        write(f"{data}/onepiece/recipe/farm_{name}.json", {"type": "minecraft:crafting_shapeless", "category": "misc",
              "ingredients": ingredients, "result": {"count": count, "id": result}})

    shaped("seed_vault", ["PSP", "SCS", "PSP"], {"P": "#minecraft:planks", "S": "minecraft:wheat_seeds", "C": "minecraft:chest"},
           "onepiece:seed_vault")
    shaped("sprinkler", [" C ", "CBC", " C "], {"C": "minecraft:copper_ingot", "B": "minecraft:bucket"}, "onepiece:sprinkler")
    shaped("dial_sprinkler", [" D ", "DSD", " D "], {"D": "onepiece:dial_shell", "S": "onepiece:sprinkler"}, "onepiece:dial_sprinkler")
    shaped("ranch_trough", ["P P", "LLL"], {"P": "#minecraft:planks", "L": "#minecraft:logs"}, "onepiece:ranch_trough")
    shaped("straw_hat_scarecrow", [" H ", "SWS", " S "], {"H": "minecraft:hay_block", "W": "#minecraft:wool", "S": "minecraft:stick"},
           "onepiece:straw_hat_scarecrow")
    shaped("watering_can", ["C  ", "CBC", " CC"], {"C": "minecraft:copper_ingot", "B": "minecraft:bowl"}, "onepiece:watering_can")
    shapeless("fresh_milk", ["minecraft:milk_bucket", "minecraft:glass_bottle", "minecraft:glass_bottle", "minecraft:glass_bottle"],
              "onepiece:fresh_milk", 3)
    shapeless("onigiri_from_wano_rice", ["onepiece:wano_rice", "onepiece:wano_rice", "minecraft:dried_kelp"], "onepiece:onigiri", 3)
    shapeless("sake_from_wano_rice", ["minecraft:glass_bottle", "onepiece:wano_rice", "onepiece:wano_rice", "minecraft:sugar"],
              "onepiece:sake", 2)
    shapeless("dango_from_kibi_millet", ["onepiece:kibi_millet", "onepiece:kibi_millet", "minecraft:sugar"], "onepiece:dango", 2)
    shapeless("bread_from_elbaph_barley", ["onepiece:elbaph_barley", "onepiece:elbaph_barley", "onepiece:elbaph_barley"],
              "minecraft:bread", 1)

    # ---- Tags ----
    crops = [f"onepiece:{c[0]}_crop" for c in CROPS]
    seeds = [f"onepiece:{c[0]}_seeds" for c in CROPS]
    produce = [f"onepiece:{c[0]}" for c in CROPS]
    write(f"{data}/onepiece/tags/item/island_seeds.json", {"values": seeds})
    write(f"{data}/onepiece/tags/item/island_crops.json", {"values": produce})
    write(f"{data}/onepiece/tags/item/ranch_fodder.json", {"values": FODDER + ["#onepiece:island_crops"]})
    for tag in ("crops", "bee_growables", "maintains_farmland"):
        union_tag(f"{data}/minecraft/tags/block/{tag}.json", crops)
    union_tag(f"{data}/minecraft/tags/block/mineable/axe.json", ["onepiece:seed_vault", "onepiece:ranch_trough", "onepiece:straw_hat_scarecrow"])
    union_tag(f"{data}/minecraft/tags/block/mineable/pickaxe.json", ["onepiece:sprinkler", "onepiece:dial_sprinkler"])
    union_tag(f"{data}/minecraft/tags/item/villager_plantable_seeds.json", seeds)

    # ---- Lang and the shared text files ----
    lang["tag.item.onepiece.ranch_fodder"] = "Ranch Fodder"
    lang["tag.item.onepiece.island_seeds"] = "Island Seeds"
    lang["tag.item.onepiece.island_crops"] = "Island Crops"
    write(f"{res}/assets/onepiece_farm/lang/en_us.json", lang)

    desc_path = f"{res}/onepiece/item_descriptions.json"
    desc = json.load(open(desc_path))
    desc.update(descriptions)
    write(desc_path, desc)
    merge_list(f"{res}/onepiece/item_sources.json", sources, "item")
    print(len(CROPS), "crops,", len(DISHES), "dishes,", len(recipes) + len(EXTRA_GALLEY), "galley recipes,", len(lang), "lang keys")


if __name__ == "__main__":
    main(sys.argv[1])
