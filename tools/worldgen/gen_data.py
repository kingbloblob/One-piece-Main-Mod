import json, os, copy, re, sys
sys.path.insert(0, '/tmp/claude-0/gen')
V = '/tmp/claude-0/vanilla'
OUT = '/tmp/claude-0/sync/one-piece-mod/src/main/resources'
D = OUT + '/data/onepiece'

def w(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(obj, f, indent=2)
        f.write('\n')

def vb(name):
    return json.load(open(f'{V}/worldgen/biome/{name}.json'))

# ------------------------------------------------------------------ features
ore_targets = lambda stone, deep: [
    {"state": stone, "target": {"predicate_type": "minecraft:tag_match", "tag": "minecraft:stone_ore_replaceables"}},
    {"state": deep, "target": {"predicate_type": "minecraft:tag_match", "tag": "minecraft:deepslate_ore_replaceables"}},
]
w(f'{D}/worldgen/feature/ore_seastone.json', {
    "type": "minecraft:ore", "discard_chance_on_air_exposure": 0.3, "size": 6,
    "targets": ore_targets("onepiece:seastone_ore", "onepiece:deepslate_seastone_ore")})
w(f'{D}/worldgen/placed_feature/ore_seastone.json', {
    "feature": "onepiece:ore_seastone",
    "placement": [
        {"type": "minecraft:count", "count": 6},
        {"type": "minecraft:in_square"},
        {"type": "minecraft:height_range", "height": {"type": "minecraft:uniform",
            "min_inclusive": {"absolute": -48}, "max_inclusive": {"absolute": 40}}},
        {"type": "minecraft:biome"}]})

adam = json.load(open(f'{V}/worldgen/feature/mega_jungle_tree.json'))
adam['trunk_provider'] = {"id": "onepiece:adam_log", "properties": {"axis": "y"}}
adam['trunk_placer'] = {"type": "minecraft:mega_jungle_trunk_placer", "base_height": 22, "height_rand_a": 6, "height_rand_b": 10}
adam['foliage_provider'] = {"id": "minecraft:oak_leaves", "properties": {"distance": "7", "persistent": "false", "waterlogged": "false"}}
adam['foliage_placer'] = {"type": "minecraft:jungle_foliage_placer", "height": 3, "offset": 0, "radius": 3}
adam['decorators'] = [{"type": "minecraft:leave_vine", "probability": 0.1}]
w(f'{D}/worldgen/feature/adam_tree.json', adam)

def tree_placement(feature, count_or_rarity):
    p = [count_or_rarity, {"type": "minecraft:in_square"},
         {"type": "minecraft:surface_water_depth_filter", "max_water_depth": 0},
         {"type": "minecraft:heightmap", "heightmap": "OCEAN_FLOOR"},
         {"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:would_survive", "state": "minecraft:oak_sapling"}},
         {"type": "minecraft:biome"}]
    return {"feature": feature, "placement": p}
# Rare in normal jungles (about 1 tree every 40 chunks), common in Skypiea's Upper Yard.
w(f'{D}/worldgen/placed_feature/adam_tree_rare.json', tree_placement("onepiece:adam_tree", {"type": "minecraft:rarity_filter", "chance": 40}))
w(f'{D}/worldgen/placed_feature/adam_tree_upper_yard.json', tree_placement("onepiece:adam_tree", {"type": "minecraft:rarity_filter", "chance": 3}))

import gen_biomes
BIOMES = gen_biomes.BIOMES

# ------------------------------------------------------------------ tags
def tag(path, values): w(path, {"replace": False, "values": values})
tag(f'{D}/tags/worldgen/biome/has_seastone_ore.json', ["#minecraft:is_ocean"])
tag(f'{D}/tags/worldgen/biome/has_adam_tree.json', ["#minecraft:is_jungle"])
tag(f'{D}/tags/worldgen/biome/one_piece_islands.json', [f"onepiece:{n}" for n in BIOMES])
MC = f'{OUT}/data/minecraft/tags'
tag(f'{MC}/block/mineable/pickaxe.json', ["onepiece:seastone_ore", "onepiece:deepslate_seastone_ore", "onepiece:seastone_block"])
tag(f'{MC}/block/needs_iron_tool.json', ["onepiece:seastone_ore", "onepiece:deepslate_seastone_ore", "onepiece:seastone_block"])
tag(f'{MC}/block/mineable/axe.json', ["onepiece:adam_log", "onepiece:adam_planks"])
tag(f'{MC}/block/logs.json', ["onepiece:adam_log"])
tag(f'{MC}/block/planks.json', ["onepiece:adam_planks"])
tag(f'{MC}/item/logs.json', ["onepiece:adam_log"])
tag(f'{MC}/item/planks.json', ["onepiece:adam_planks"])
# The overworld tags make vanilla things (like mob spawning rules) treat our biomes as normal land.
tag(f'{MC}/worldgen/biome/is_overworld.json', [f"onepiece:{n}" for n in BIOMES])
tag(f'{MC}/worldgen/biome/is_jungle.json', ["onepiece:skypiea", "onepiece:jaya", "onepiece:amazon_lily", "onepiece:little_garden"])
tag(f'{MC}/worldgen/biome/is_taiga.json', ["onepiece:drum_island", "onepiece:elbaph"])
tag(f'{MC}/worldgen/biome/is_ocean.json', ["onepiece:fishman_reef"])

# ------------------------------------------------------------------ loot, recipes
def ore_loot(name, raw):
    return {"type": "minecraft:block", "pools": [{"rolls": 1, "entries": [{"type": "minecraft:alternatives", "children": [
        {"type": "minecraft:item", "condition": "minecraft:tool/can_silk_touch", "name": f"onepiece:{name}"},
        {"type": "minecraft:item", "name": raw, "modifier": [
            {"type": "minecraft:apply_bonus", "enchantment": "minecraft:fortune", "formula": "minecraft:ore_drops"},
            {"type": "minecraft:explosion_decay"}]}]}]}],
        "random_sequence": f"onepiece:blocks/{name}"}
def self_loot(name):
    return {"type": "minecraft:block", "pools": [{"rolls": 1,
        "condition": {"type": "minecraft:survives_explosion"},
        "entries": [{"type": "minecraft:item", "name": f"onepiece:{name}"}]}],
        "random_sequence": f"onepiece:blocks/{name}"}
w(f'{D}/loot_table/blocks/seastone_ore.json', ore_loot("seastone_ore", "onepiece:raw_seastone"))
w(f'{D}/loot_table/blocks/deepslate_seastone_ore.json', ore_loot("deepslate_seastone_ore", "onepiece:raw_seastone"))
for n in ("seastone_block", "adam_log", "adam_planks", "island_cloud", "sea_cloud"):
    w(f'{D}/loot_table/blocks/{n}.json', self_loot(n))

r = f'{D}/recipe'
for kind, time in (("smelting", 200), ("blasting", 100)):
    w(f'{r}/seastone_ingot_from_{kind}.json', {"type": f"minecraft:{kind}", "cookingtime": time, "experience": 1.0,
        "group": "seastone_ingot", "ingredient": "onepiece:raw_seastone", "result": {"id": "onepiece:seastone_ingot"}})
w(f'{r}/seastone_block.json', {"type": "minecraft:crafting_shaped", "category": "building", "key": {"#": "onepiece:seastone_ingot"},
    "pattern": ["###", "###", "###"], "result": {"id": "onepiece:seastone_block"}})
w(f'{r}/seastone_ingot_from_block.json', {"type": "minecraft:crafting_shapeless", "group": "seastone_ingot",
    "ingredients": ["onepiece:seastone_block"], "result": {"count": 9, "id": "onepiece:seastone_ingot"}})
w(f'{r}/adam_planks.json', {"type": "minecraft:crafting_shapeless", "category": "building", "group": "planks",
    "ingredients": ["onepiece:adam_log"], "result": {"count": 4, "id": "onepiece:adam_planks"}})
# Seastone Jitte and Cuffs are made at the Seastone Workbench (see onepiece/station_recipes.json),
# so there is no crafting-table recipe for them here.


# ------------------------------------------------------------------ assets: models, item definitions, names
A = OUT + '/assets/onepiece'
def item_def(n, model): w(f'{A}/items/{n}.json', {"model": {"type": "minecraft:model", "model": model}})
for n in ("seastone_ore", "deepslate_seastone_ore", "seastone_block", "adam_planks", "island_cloud", "sea_cloud"):
    w(f'{A}/blockstates/{n}.json', {"variants": {"": {"model": f"onepiece:block/{n}"}}})
    w(f'{A}/models/block/{n}.json', {"parent": "minecraft:block/cube_all", "textures": {"all": f"onepiece:block/{n}"}})
    item_def(n, f"onepiece:block/{n}")
w(f'{A}/blockstates/adam_log.json', {"variants": {
    "axis=x": {"model": "onepiece:block/adam_log_horizontal", "x": 90, "y": 90},
    "axis=y": {"model": "onepiece:block/adam_log"},
    "axis=z": {"model": "onepiece:block/adam_log_horizontal", "x": 90}}})
for suffix, parent in (("", "cube_column"), ("_horizontal", "cube_column_horizontal")):
    w(f'{A}/models/block/adam_log{suffix}.json', {"parent": f"minecraft:block/{parent}",
        "textures": {"end": "onepiece:block/adam_log_top", "side": "onepiece:block/adam_log"}})
item_def("adam_log", "onepiece:block/adam_log")
for n, parent in (("raw_seastone", "generated"), ("seastone_ingot", "generated"), ("seastone_jitte", "handheld"), ("seastone_cuffs", "generated")):
    w(f'{A}/models/item/{n}.json', {"parent": f"minecraft:item/{parent}", "textures": {"layer0": f"onepiece:item/{n}"}})
    item_def(n, f"onepiece:item/{n}")

# Names live in their own language file (assets/onepiece_world) so they never clash with
# assets/onepiece/lang/en_us.json, which other parts of the mod edit. Minecraft reads both.
names = {
    "block.onepiece.seastone_ore": "Seastone Ore",
    "block.onepiece.deepslate_seastone_ore": "Deepslate Seastone Ore",
    "block.onepiece.seastone_block": "Block of Seastone",
    "block.onepiece.adam_log": "Adam Log",
    "block.onepiece.adam_planks": "Adam Planks",
    "block.onepiece.island_cloud": "Island Cloud",
    "block.onepiece.sea_cloud": "Sea Cloud",
    "item.onepiece.raw_seastone": "Raw Seastone",
    "item.onepiece.seastone_ingot": "Seastone Ingot",
    "item.onepiece.seastone_jitte": "Seastone Jitte",
    "item.onepiece.seastone_cuffs": "Seastone Cuffs",
    "generator.onepiece.grand_line": "Grand Line",
}
names.update(gen_biomes.NAMES)
w(f'{OUT}/assets/onepiece_world/lang/en_us.json', names)
