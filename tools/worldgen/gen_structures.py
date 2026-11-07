"""Builds every structure (.nbt), its jigsaw files, the structure sets by difficulty, the chest loot and the guard list."""
import json, os, sys, shutil
sys.path.insert(0, '/tmp/claude-0/gen')
import kits
from locs1 import LOCS
import locs2  # registers the story locations into LOCS

OUT = '/tmp/claude-0/sync/one-piece-mod/src/main/resources'
D = OUT + '/data/onepiece'
def w(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f: json.dump(obj, f, indent=2); f.write('\n')

# start fresh (all of these folders belong to the world generator)
for p in ('structure', 'worldgen/template_pool', 'worldgen/structure', 'worldgen/structure_set', 'tags/worldgen/biome/has_structure', 'loot_table/chests'):
    shutil.rmtree(f'{D}/{p}', ignore_errors=True)

chars = {c['id'] for c in json.load(open(f'{OUT}/onepiece/characters.json'))}
# How rare each difficulty is: one structure of that tier per spacing x spacing chunks (on average a bit more).
TIERS = {"easy": (20, 7, 1408172001), "medium": (28, 10, 1408172002), "hard": (40, 14, 1408172003), "legendary": (64, 24, 1408172004)}
by_tier = {t: [] for t in TIERS}
catalogue = []
for loc in LOCS:
    from kit import B
    b = B(); loc['build'](b)
    for (eid, *_r, data) in b.entities:
        if eid == "onepiece:character": assert data["Character"] in chars, (loc['name'], data["Character"])
    name = loc['name']
    size, my = b.save(f'{D}/structure/{name}.nbt')
    place = loc['place']
    st = {"type": "minecraft:jigsaw", "biomes": f"#onepiece:has_structure/{name}", "step": "surface_structures",
          "spawn_overrides": {"monster": {"bounding_box": "piece", "spawns": []}, "ambient": {"bounding_box": "piece", "spawns": []}}, "terrain_adaptation": "beard_thin", "start_pool": f"onepiece:{name}",
          "size": 1, "max_distance_from_center": 80, "use_expansion_hack": False}
    if place in ("land", "under"):
        st["project_start_to_heightmap"] = "WORLD_SURFACE_WG"; st["start_height"] = {"absolute": -1 + my}
        if place == "under": st["terrain_adaptation"] = "none"
    elif place == "sea":
        st["project_start_to_heightmap"] = "WORLD_SURFACE_WG"; st["start_height"] = {"absolute": -1 - b.waterline + my}; st["terrain_adaptation"] = "none"
    elif place == "seafloor":
        st["project_start_to_heightmap"] = "OCEAN_FLOOR_WG"; st["start_height"] = {"absolute": -1 + my}; st["terrain_adaptation"] = "none"
    elif place == "sky":
        st["start_height"] = {"absolute": 170 + my}; st["terrain_adaptation"] = "none"
    w(f'{D}/worldgen/structure/{name}.json', st)
    w(f'{D}/worldgen/template_pool/{name}.json', {"fallback": "minecraft:empty", "elements": [{"weight": 1, "element": {
        "element_type": "minecraft:single_pool_element", "location": f"onepiece:{name}", "processors": {"processors": []}, "projection": "rigid"}}]})
    w(f'{D}/tags/worldgen/biome/has_structure/{name}.json', {"replace": False, "values": loc['biomes']})
    by_tier[loc['tier']].append(name)
    catalogue.append(dict(name=name, title=loc['title'], tier=loc['tier'], boss=loc['boss'], who=loc['who'], place=place,
                          biomes=loc['biomes'], size=size, guards=sum(1 for e in b.entities if e[0] != "onepiece:character")))
for t, (spacing, sep, salt) in TIERS.items():
    w(f'{D}/worldgen/structure_set/{t}_locations.json', {
        "structures": [{"structure": f"onepiece:{n}", "weight": 1} for n in by_tier[t]],
        "placement": {"type": "minecraft:random_spread", "spacing": spacing, "separation": sep, "salt": salt}})

# ---------------------------------------------------------------- guards for GuardKit.java
out = []
for kid, kv in kits.KITS.items():
    o = {"id": kid}; o.update({k: v for k, v in kv.items() if v not in (None, 0)}); out.append(o)
w(f'{OUT}/onepiece/guards.json', out)

# ---------------------------------------------------------------- chest loot (26.3 format: "modifier" with "type")
def item(name, weight, lo=1, hi=1, extra=None):
    e = {"type": "minecraft:item", "name": name, "weight": weight}
    mods = []
    if hi > 1 or lo > 1: mods.append({"type": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": lo, "max": hi}})
    if extra: mods.append(extra)
    if mods: e["modifier"] = mods
    return e
def table(*pools):
    return {"type": "minecraft:chest", "pools": [{"rolls": {"type": "minecraft:uniform", "min": lo, "max": hi}, "entries": es} for lo, hi, es in pools]}
potion = lambda p: {"type": "minecraft:set_potion", "id": f"minecraft:{p}"}
enchant = {"type": "minecraft:enchant_randomly"}
B_ = "onepiece:berry"
L = f'{D}/loot_table/chests'
w(f'{L}/easy.json', table((3, 6, [item(B_, 10, 1, 6), item("minecraft:bread", 10, 1, 4), item("minecraft:apple", 8, 1, 3), item("minecraft:iron_nugget", 8, 2, 8),
    item("minecraft:gold_nugget", 6, 2, 8), item("minecraft:map", 2), item("minecraft:leather", 6, 1, 3), item("minecraft:stone_sword", 3)])))
w(f'{L}/medium.json', table((4, 7, [item(B_, 10, 4, 12), item("minecraft:iron_ingot", 10, 1, 5), item("minecraft:gold_ingot", 6, 1, 4), item("minecraft:cooked_beef", 8, 2, 5),
    item("minecraft:emerald", 4, 1, 3), item("minecraft:iron_sword", 3), item("onepiece:raw_seastone", 3, 1, 2), item("minecraft:golden_apple", 1)])))
w(f'{L}/hard.json', table((5, 8, [item(B_, 10, 10, 30), item("minecraft:diamond", 6, 1, 3), item("minecraft:gold_ingot", 8, 2, 6), item("minecraft:golden_apple", 4, 1, 2),
    item("onepiece:seastone_ingot", 4, 1, 3), item("minecraft:diamond_sword", 2, 1, 1, enchant), item("minecraft:experience_bottle", 6, 2, 8),
    item("minecraft:ender_pearl", 3, 1, 3)]), (1, 1, [item("minecraft:enchanted_book", 1, 1, 1, enchant)])))
w(f'{L}/legendary.json', table((6, 10, [item(B_, 10, 32, 64), item("minecraft:diamond", 8, 2, 6), item("minecraft:netherite_scrap", 4, 1, 2), item("minecraft:enchanted_golden_apple", 2),
    item("minecraft:golden_apple", 6, 2, 4), item("onepiece:seastone_jitte", 2), item("minecraft:netherite_ingot", 1), item("minecraft:totem_of_undying", 2),
    item("minecraft:diamond_chestplate", 2, 1, 1, enchant), item("onepiece:adam_log", 4, 4, 16)]), (2, 2, [item("minecraft:enchanted_book", 1, 1, 1, enchant)])))
w(f'{L}/laugh_tale.json', table((8, 12, [item(B_, 10, 64, 64), item("minecraft:gold_block", 8, 4, 12), item("minecraft:diamond_block", 4, 1, 3),
    item("minecraft:netherite_ingot", 3, 1, 2), item("minecraft:enchanted_golden_apple", 3, 1, 2), item("minecraft:totem_of_undying", 2)]),
    (1, 1, [item("onepiece:gomu_gomu_no_mi", 1)])))
w(f'{L}/treasure.json', table((4, 8, [item("minecraft:gold_ingot", 10, 2, 8), item("minecraft:gold_block", 3, 1, 2), item(B_, 8, 10, 30), item("minecraft:emerald", 6, 2, 6),
    item("minecraft:diamond", 3, 1, 3), item("minecraft:golden_apple", 2)])))
w(f'{L}/marine.json', table((3, 6, [item(B_, 10, 2, 8), item("minecraft:iron_ingot", 8, 1, 5), item("minecraft:bread", 8, 2, 5), item("minecraft:arrow", 5, 4, 12),
    item("onepiece:seastone_cuffs", 3, 1, 2), item("onepiece:raw_seastone", 3, 1, 3), item("minecraft:iron_sword", 2), item("minecraft:crossbow", 1)])))
w(f'{L}/pirate.json', table((3, 7, [item(B_, 10, 3, 12), item("minecraft:gold_ingot", 8, 1, 5), item("minecraft:gold_nugget", 8, 3, 12), item("minecraft:map", 3),
    item("minecraft:gunpowder", 6, 1, 4), item("minecraft:cooked_porkchop", 6, 1, 4), item("minecraft:emerald", 4, 1, 3), item("onepiece:adam_planks", 2, 2, 6)])))
w(f'{L}/galley.json', table((4, 8, [item("minecraft:cooked_cod", 10, 2, 6), item("minecraft:cooked_salmon", 10, 2, 6), item("minecraft:cooked_beef", 8, 1, 4),
    item("minecraft:bread", 8, 2, 6), item("minecraft:cake", 2), item("minecraft:pumpkin_pie", 4, 1, 3), item("minecraft:golden_carrot", 3, 1, 4), item(B_, 4, 2, 6)])))
w(f'{L}/sky_treasure.json', table((4, 8, [item("minecraft:gold_ingot", 10, 2, 8), item("minecraft:gold_block", 4, 1, 2), item(B_, 8, 10, 30), item("minecraft:golden_apple", 3),
    item("minecraft:diamond", 3, 1, 3), item("minecraft:feather", 6, 3, 10), item("minecraft:enchanted_golden_apple", 1)])))
w(f'{L}/wano.json', table((3, 6, [item("minecraft:iron_sword", 4), item("minecraft:diamond_sword", 1, 1, 1, enchant), item("minecraft:cherry_sapling", 6, 1, 3),
    item("minecraft:bamboo", 6, 4, 12), item("minecraft:bread", 6, 2, 5), item(B_, 8, 4, 12), item("minecraft:gold_ingot", 4, 1, 4)])))
w(f'{L}/lab.json', table((3, 7, [item("minecraft:glass_bottle", 8, 2, 6), item("minecraft:redstone", 8, 4, 12), item("minecraft:iron_ingot", 6, 2, 6),
    item("minecraft:ender_pearl", 2, 1, 2), item("onepiece:seastone_ingot", 3, 1, 3), item("minecraft:experience_bottle", 4, 2, 6),
    item("minecraft:potion", 4, 1, 2, potion("healing")), item(B_, 6, 4, 12)])))
w(f'{L}/medicine.json', table((3, 6, [item("minecraft:potion", 10, 1, 3, potion("healing")), item("minecraft:potion", 6, 1, 2, potion("regeneration")),
    item("minecraft:golden_apple", 3), item("minecraft:glistering_melon_slice", 5, 1, 3), item("minecraft:sweet_berries", 8, 3, 9), item(B_, 6, 3, 10)])))
w(f'{L}/candy.json', table((4, 8, [item("minecraft:cake", 4), item("minecraft:cookie", 10, 4, 16), item("minecraft:pumpkin_pie", 6, 1, 3), item("minecraft:sugar", 8, 4, 12),
    item("minecraft:honey_bottle", 6, 1, 3), item(B_, 6, 6, 20), item("minecraft:golden_apple", 1)])))
w(f'{L}/library.json', table((3, 6, [item("minecraft:book", 10, 2, 6), item("minecraft:enchanted_book", 3, 1, 1, enchant), item("minecraft:paper", 8, 4, 12),
    item("minecraft:writable_book", 3), item("minecraft:compass", 2), item(B_, 4, 2, 6)])))

w('/tmp/claude-0/gen/catalogue.json', catalogue)
print({t: len(v) for t, v in by_tier.items()}, "total", len(LOCS))
