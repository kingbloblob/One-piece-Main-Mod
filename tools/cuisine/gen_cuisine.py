#!/usr/bin/env python3
"""Writes the data and asset files for fishing, cooking and the All Blue (Java: com.onepiecemod.cuisine)
and merges its entries into the shared data files. Safe to run again: entries are replaced by id.

    python3 -I gen_cuisine.py <source folder>

Writes (own files): item model definitions + models, lang assets/onepiece_cuisine/lang/en_us.json,
grilling recipes data/onepiece/recipe/grilled_fish_from_*.json, item tag data/onepiece/tags/item/raw_fish.json.
Merges (shared files): onepiece/station_recipes.json, onepiece/item_descriptions.json, onepiece/item_sources.json.
Textures come from cuisine_textures.py (run it first)."""
import json
import os
import sys

# id, name, description (tooltip), where (for "how to get it" cards)
FISH = [
    ("blue_sea_bream", "Blue Sea Bream", "A pretty pink and blue fish. Sanji's sashimi starts here.", "East Blue"),
    ("striped_mackerel", "Striped Mackerel", "A common catch. Good in fried rice.", "East Blue"),
    ("east_blue_lobster", "East Blue Lobster", "The Baratie's favourite. Makes a fine bisque.", "East Blue"),
    ("calm_belt_eel", "Calm Belt Eel", "A slippery eel that never needed any wind.", "Calm Belt"),
    ("sea_king_fry", "Sea King Fry", "A baby Sea King! Clean it at the Ship's Galley for Sea King meat.", "Calm Belt"),
    ("elephant_honmaguro", "Elephant Honmaguro", "A slab of the giant Elephant Tuna. The best sushi there is.", "Grand Line"),
    ("grand_line_puffer", "Grand Line Puffer", "Poisonous raw! A Cook knows how to make it safe.", "Grand Line"),
    ("rainbow_snapper", "Rainbow Snapper", "Shines in seven colours.", "Grand Line"),
    ("new_world_swordfish", "New World Swordfish", "A fierce fish with a blade for a nose. Makes a strong steak.", "New World"),
    ("abyss_angler", "Abyss Anglerfish", "Comes up from the deep sea, lantern and all.", "New World"),
    ("glowfin", "Glowfin", "Glows in dark water. Fishmen love it in a stew.", "Fishman Island or Sabaody"),
    ("sky_fish", "Sky Fish", "A fish that swims through clouds.", "Skypiea"),
    ("golden_koi", "Golden Koi", "A lucky golden koi. Makes a fine oden.", "Wano or Onigashima"),
    ("frostfin_cod", "Frostfin Cod", "Lives in icy water. Makes a hot pot that keeps the cold out.", "Drum Island or frozen Punk Hazard"),
    ("sandora_catfish", "Sandora Catfish", "A big whiskered river catfish.", "Alabasta"),
    ("ghost_fish", "Ghost Fish", "See-through and spooky. Yohohoho!", "Thriller Bark"),
    ("all_blue_kingfish", "All Blue Kingfish", "The king of all fish.", "the All Blue"),
    ("rainbow_sunfish", "Rainbow Sunfish", "A round, glittering fish.", "the All Blue"),
]

# id, name, description, galley ingredients [(item, count)], count made, needs a Cook
DISHES = [
    ("sea_bream_sashimi", "Sea Bream Sashimi", "Thin slices of sea bream. Luck for 10 minutes: better fishing and loot.",
     [("onepiece:blue_sea_bream", 2)], 1, False),
    ("lobster_bisque", "Baratie Lobster Bisque", "The Baratie's famous soup. Resistance for 8 minutes.",
     [("onepiece:east_blue_lobster", 1), ("minecraft:brown_mushroom", 1), ("minecraft:bowl", 1)], 1, False),
    ("seafood_fried_rice", "Seafood Fried Rice", "What Sanji cooked for a starving Gin. Extra hearts for 15 minutes.",
     [("onepiece:striped_mackerel", 1), ("onepiece:blue_sea_bream", 1), ("minecraft:egg", 1), ("minecraft:wheat", 2)], 1, False),
    ("eel_kabayaki", "Eel Kabayaki", "Grilled glazed eel. Speed for 10 minutes.",
     [("onepiece:calm_belt_eel", 1), ("minecraft:sugar", 1), ("minecraft:wheat", 1)], 1, False),
    ("sea_king_barbecue", "Sea King Barbecue", "Luffy's dream skewer. Strength and extra hearts for 15 minutes.",
     [("onepiece:cooked_sea_king_meat", 2), ("minecraft:carrot", 1), ("minecraft:stick", 1)], 1, False),
    ("elephant_tuna_sushi", "Elephant Tuna Sushi", "Sushi from the Elephant Honmaguro. Haste and Water Breathing for 15 minutes.",
     [("onepiece:elephant_honmaguro", 1), ("minecraft:dried_kelp", 2), ("minecraft:wheat", 1)], 2, False),
    ("puffer_hot_pot", "Puffer Hot Pot", "Only a Cook can make the puffer safe. Resistance for 12 minutes and a minute of Regeneration.",
     [("onepiece:grand_line_puffer", 1), ("minecraft:carrot", 1), ("minecraft:potato", 1), ("minecraft:bowl", 1)], 1, True),
    ("rainbow_snapper_carpaccio", "Rainbow Snapper Carpaccio", "With Nami's mikans. Speed and Jump Boost for 12 minutes.",
     [("onepiece:rainbow_snapper", 1), ("onepiece:mikan", 1)], 1, False),
    ("swordfish_steak", "Swordfish Steak", "A thick New World steak. Strength II for 8 minutes.",
     [("onepiece:new_world_swordfish", 1), ("minecraft:baked_potato", 1)], 1, False),
    ("angler_lantern_soup", "Angler Lantern Soup", "Glows from inside. Night Vision for 20 minutes and Conduit Power for 10.",
     [("onepiece:abyss_angler", 1), ("minecraft:glow_berries", 1), ("minecraft:bowl", 1)], 1, False),
    ("glowfin_stew", "Glowfin Stew", "A Fishman Island recipe. Breathe, swim fast and see underwater for a long dive.",
     [("onepiece:glowfin", 1), ("minecraft:kelp", 1), ("minecraft:bowl", 1)], 1, False),
    ("sky_fish_skewers", "Sky Fish Skewers", "Light as a cloud. Slow Falling and Jump Boost II for 10 minutes.",
     [("onepiece:sky_fish", 2), ("minecraft:stick", 1)], 1, False),
    ("golden_koi_oden", "Golden Koi Oden", "Wano's oden, boiled like Oden himself. Resistance and Fire Resistance for 15 minutes.",
     [("onepiece:golden_koi", 1), ("minecraft:egg", 1), ("minecraft:dried_kelp", 1), ("minecraft:bowl", 1)], 1, False),
    ("frostfin_hot_pot", "Frostfin Hot Pot", "Warms you to the bones: Winter Islands can't freeze you for 20 minutes.",
     [("onepiece:frostfin_cod", 1), ("minecraft:potato", 1), ("minecraft:bowl", 1)], 1, False),
    ("sandora_catfish_kebab", "Sandora Catfish Kebab", "Alabasta street food. Fire Resistance for 15 minutes, Speed for 8.",
     [("onepiece:sandora_catfish", 1), ("minecraft:beetroot", 1), ("minecraft:stick", 1)], 1, False),
    ("ghost_fish_soup", "Ghost Fish Soup", "Yohohoho! Invisibility for 5 minutes and Night Vision for 15.",
     [("onepiece:ghost_fish", 1), ("minecraft:bone", 1), ("minecraft:bowl", 1)], 1, False),
    ("all_blue_full_course", "All Blue Full Course", "Sanji's dream meal. Strength, Resistance, Speed, Luck and lots of extra hearts for 20 minutes.",
     [("onepiece:all_blue_kingfish", 1), ("onepiece:rainbow_sunfish", 1), ("onepiece:cooked_sea_king_meat", 1),
      ("minecraft:golden_carrot", 1), ("minecraft:bread", 1)], 1, True),
]

EXTRA_RECIPES = [
    {"id": "sea_king_meat_from_fry", "station": "ships_galley", "result": "onepiece:sea_king_meat", "count": 2,
     "ingredients": [{"item": "onepiece:sea_king_fry", "count": 1}]},
    {"id": "all_blue_compass", "station": "navigators_desk", "result": "onepiece:all_blue_compass", "count": 1,
     "ingredients": [{"item": "minecraft:compass", "count": 1}, {"item": "onepiece:blue_sea_bream", "count": 1},
                     {"item": "onepiece:calm_belt_eel", "count": 1}, {"item": "onepiece:elephant_honmaguro", "count": 1},
                     {"item": "onepiece:new_world_swordfish", "count": 1}],
     "requires": {"crew": "cook"}},
]

OTHER = {
    "grilled_fish": ("Grilled Fish", "Any One Piece fish grilled over a fire, in a furnace or a smoker."),
    "all_blue_compass": ("All Blue Compass", "Points to the All Blue, the sea where the fish of every sea meet. Right-click for the distance."),
}

BOWL = {"lobster_bisque", "puffer_hot_pot", "angler_lantern_soup", "glowfin_stew", "golden_koi_oden", "frostfin_hot_pot", "ghost_fish_soup"}


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def merge_list(path, entries, key):
    """Replaces entries with the same key in a shared JSON list, adds the rest at the end. Keeps the file's other entries."""
    data = json.load(open(path))
    ids = {e[key] for e in entries}
    data = [e for e in data if e.get(key) not in ids] + entries
    write(path, data)


def main(source):
    res = os.path.join(source, "src/main/resources")
    assets = os.path.join(res, "assets/onepiece")
    names = [f[0] for f in FISH] + [d[0] for d in DISHES] + ["grilled_fish"]
    for name in names:
        write(f"{assets}/items/{name}.json", {"model": {"type": "minecraft:model", "model": f"onepiece:item/{name}"}})
        write(f"{assets}/models/item/{name}.json", {"parent": "minecraft:item/generated", "textures": {"layer0": f"onepiece:item/{name}"}})

    # The compass: 32 needle frames, like the vanilla compass. Spins when it has no target.
    entries = []
    for i in range(32):
        frame = f"all_blue_compass_{i:02d}"
        write(f"{assets}/models/item/{frame}.json", {"parent": "minecraft:item/generated", "textures": {"layer0": f"onepiece:item/{frame}"}})
        entries.append({"threshold": 0.0 if i == 0 else i - 0.5, "model": {"type": "minecraft:model", "model": f"onepiece:item/{frame}"}})
    entries.append({"threshold": 31.5, "model": {"type": "minecraft:model", "model": "onepiece:item/all_blue_compass_00"}})
    dispatch = lambda target: {"type": "minecraft:range_dispatch", "property": "minecraft:compass", "target": target, "scale": 32.0,
                               "entries": entries}
    write(f"{assets}/items/all_blue_compass.json", {"model": {
        "type": "minecraft:condition", "property": "minecraft:has_component", "component": "minecraft:lodestone_tracker",
        "on_true": dispatch("lodestone"), "on_false": dispatch("none")}})

    lang = {"effect.onepiece.well_fed": "Well Fed", "effect.onepiece.warm_belly": "Warm Belly", "tag.item.onepiece.raw_fish": "Raw Fish"}
    for fid, name, _, _ in FISH:
        lang[f"item.onepiece.{fid}"] = name
    for did, name, *_ in DISHES:
        lang[f"item.onepiece.{did}"] = name
    for oid, (name, _) in OTHER.items():
        lang[f"item.onepiece.{oid}"] = name
    write(f"{res}/assets/onepiece_cuisine/lang/en_us.json", lang)

    # Grilling: any raw fish (tag) in a furnace, smoker or over a campfire.
    write(f"{res}/data/onepiece/tags/item/raw_fish.json", {"values": [f"onepiece:{f[0]}" for f in FISH]})
    for kind, time in (("smelting", 200), ("smoking", 100), ("campfire_cooking", 600)):
        write(f"{res}/data/onepiece/recipe/grilled_fish_from_{kind}.json", {
            "type": f"minecraft:{kind}", "category": "food", "cookingtime": time, "experience": 0.35,
            "ingredient": "#onepiece:raw_fish", "result": {"id": "onepiece:grilled_fish"}})

    recipes = []
    for did, name, _, ingredients, count, cook in DISHES:
        r = {"id": did, "station": "ships_galley", "result": f"onepiece:{did}", "count": count,
             "ingredients": [{"item": i, "count": c} for i, c in ingredients]}
        if cook:
            r["requires"] = {"crew": "cook"}
        recipes.append(r)
    merge_list(f"{res}/onepiece/station_recipes.json", recipes + EXTRA_RECIPES, "id")

    desc_path = f"{res}/onepiece/item_descriptions.json"
    desc = json.load(open(desc_path))
    for fid, _, text, _ in FISH:
        desc[f"onepiece:{fid}"] = text
    for did, _, text, *_ in DISHES:
        desc[f"onepiece:{did}"] = text
    for oid, (_, text) in OTHER.items():
        desc[f"onepiece:{oid}"] = text
    write(desc_path, desc)

    sources = []
    for fid, name, _, where in FISH:
        notes = [f"Fish with a normal fishing rod in {where}.", "Grill it, or cook it at the Ship's Galley."]
        if where == "the All Blue":
            notes = ["Fish in the All Blue, far out in the New World.", "The All Blue Compass points the way."]
        sources.append({"item": f"onepiece:{fid}", "title": "Fishing: " + where, "icon": "minecraft:fishing_rod", "notes": notes})
    sources.append({"item": "onepiece:sea_king_meat", "title": "Fishing: Calm Belt", "icon": "minecraft:fishing_rod",
                    "notes": ["Now and then a Calm Belt catch is a slab of Sea King meat.", "Sea Kings drop it too."]})
    merge_list(f"{res}/onepiece/item_sources.json", sources, "item")
    print(len(FISH), "fish,", len(DISHES), "dishes,", len(recipes) + len(EXTRA_RECIPES), "station recipes")


if __name__ == "__main__":
    main(sys.argv[1])
