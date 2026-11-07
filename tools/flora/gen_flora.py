"""Generates the island flora of com.onepiecemod.flora: a plant or ground block for every Grand Line island biome
(2026-10-24, ryan: "add new blocks, plants and more for every biome so they look better").

What it makes, all from the tables below:
  - Java: FloraBlocks.java (block + item registration, creative tab "One Piece: Nature") and FloraFeature.java
    (adds each plant to its biomes at runtime by biome tag, like the deco plants). FloraPlants.java is hand-written.
  - Models, blockstates, item definitions and procedurally drawn textures (nothing copied from vanilla).
  - Loot tables (every block drops itself), recipes (every plant and soil is craftable, and flowers give dye).
  - Worldgen: a patch feature per plant and the biome tag has_flora_<id>.json saying where it grows.
  - Tags: small_flowers/flowers (bees like them), replaceable_by_trees, mineable/shovel, sand/dirt for the soils,
    and onepiece:flora_plant_soil (what the flora may stand on).

Usage: python3 gen_flora.py <out_dir> [--install <mod_source_dir>]
  Writes src/... under out_dir. With --install, copies it into the mod source: our own files are replaced,
  shared data/minecraft/tags files are union-merged (same rule as tools/deco/install.py).
"""
import json, os, shutil, sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flora_textures as ft  # noqa: E402
tx = ft.tx

OUT = sys.argv[1]
INSTALL = sys.argv[sys.argv.index('--install') + 1] if '--install' in sys.argv else None
RES = os.path.join(OUT, 'src/main/resources')
JAVA = os.path.join(OUT, 'src/main/java/com/onepiecemod/flora')
A = os.path.join(RES, 'assets/onepiece')
D = os.path.join(RES, 'data/onepiece')

# ==================================================================================================== the plants
# Biomes are our island biome names (onepiece:) or full vanilla ids.
EAST_BLUE = ['east_blue', 'orange_town', 'conomi_islands', 'loguetown', 'marineford']

# id, name, shape (round/spike/bell/daisy), petal, centre, stew effect, seconds, light, dye, biomes
FLOWERS = [
    ('dawn_poppy',        'Dawn Poppy',               'round', '#e23a2e', '#f7e04a', 'REGENERATION', 3, 0,  'red',        EAST_BLUE + ['minecraft:plains']),
    ('sea_pink',          'Sea Pink',                 'daisy', '#f08ab0', '#f7e6a0', 'WATER_BREATHING', 4, 0, 'pink',     ['east_blue', 'conomi_islands', 'orange_town', 'minecraft:beach']),
    ('marine_rose',       'Marine Rose',              'round', '#f4f8ff', '#1f5fbf', 'RESISTANCE', 3, 0,    'white',      ['marineford', 'loguetown', 'enies_lobby']),
    ('toy_tulip',         'Dressrosa Toy Tulip',      'bell',  '#ff4040', '#ffe066', 'JUMP_BOOST', 4, 0,    'red',        ['dressrosa', 'enies_lobby']),
    ('jaya_hibiscus',     'Jaya Hibiscus',            'daisy', '#ff5a7a', '#ffd34d', 'SATURATION', 1, 0,    'pink',       ['jaya', 'conomi_islands', 'minecraft:jungle']),
    ('winter_rose',       'Drum Winter Rose',         'round', '#c81e3c', '#ffffff', 'RESISTANCE', 4, 0,    'red',        ['drum_island', 'elbaph', 'minecraft:snowy_taiga']),
    ('wano_iris',         'Wano Iris',                'spike', '#6a4fc8', '#f2d43c', 'NIGHT_VISION', 4, 0,  'purple',     ['wano', 'kuri', 'minecraft:cherry_grove']),
    ('kiku_chrysanthemum', 'Kiku Chrysanthemum',      'daisy', '#f4e9c8', '#f0b429', 'REGENERATION', 3, 0,  'yellow',     ['wano', 'onigashima']),
    ('justice_lily',      'Justice Lily',             'bell',  '#ffffff', '#5aa0ff', 'RESISTANCE', 3, 0,    'white',      ['enies_lobby', 'marineford']),
    ('kuja_orchid',       'Kuja Orchid',              'spike', '#d12ea0', '#ffd0f0', 'POISON', 6, 0,        'magenta',    ['amazon_lily', 'green_bit']),
    ('cacao_blossom',     'Cacao Blossom',            'round', '#f6e4c9', '#7a4a24', 'SATURATION', 1, 0,    'brown',      ['cacao_island', 'whole_cake']),
    ('grave_lily',        'Grave Lily',               'bell',  '#2a2430', '#d9d9e8', 'WEAKNESS', 5, 0,      'black',      ['thriller_bark', 'kuraigana', 'minecraft:dark_forest']),
    ('holo_flower',       'Egghead Holo Flower',      'daisy', '#3ef0ff', '#ffffff', 'HASTE', 5, 8,         'cyan',       ['egghead']),
    ('skull_lily',        'Skull Lily',               'bell',  '#8a1020', '#f0e8d0', 'STRENGTH', 4, 0,      'red',        ['onigashima', 'hachinosu']),
    ('cinder_poppy',      'Cinder Poppy',             'round', '#ff3b1f', '#ffd060', 'FIRE_RESISTANCE', 4, 7, 'orange',   ['kuri', 'hachinosu', 'punk_hazard_burning']),
    ('valley_bloom',      'God Valley Bloom',         'daisy', '#ffd94a', '#ffffff', 'LUCK', 5, 3,          'yellow',     ['god_valley']),
    ('tontatta_clover',   'Tontatta Clover',          'round', '#39c25a', '#ffffff', 'LUCK', 5, 0,          'lime',       ['green_bit', 'dressrosa']),
    ('sky_bell',          'Sky Bell',                 'bell',  '#c8e8ff', '#ffffff', 'SLOW_FALLING', 5, 0,  'light_blue', ['skypiea']),
    ('giants_clover',     "Giant's Clover",           'round', '#2f8a3a', '#f2e6a0', 'STRENGTH', 3, 0,      'green',      ['elbaph']),
    ('zunesha_blossom',   'Zunesha Blossom',          'daisy', '#ffb3d9', '#ffffff', 'REGENERATION', 3, 0,  'pink',       ['zou']),
    ('sand_rose',         'Alabasta Sand Rose',       'round', '#e8a060', '#f2d43c', 'SATURATION', 1, 0,    'orange',     ['alabasta', 'minecraft:desert']),
    ('cliff_edelweiss',   'Red Line Edelweiss',       'daisy', '#f7f7f7', '#e0b040', 'RESISTANCE', 4, 0,    'white',      ['red_line', 'minecraft:stony_peaks']),
    ('sabaody_bubble_bloom', 'Sabaody Bubble Bloom',  'round', '#bfe9ff', '#ffffff', 'SLOW_FALLING', 4, 2,  'light_blue', ['sabaody']),
    ('frost_thistle_bloom', 'Punk Hazard Frost Bloom', 'spike', '#9fd8ff', '#ffffff', 'SLOWNESS', 3, 3,     'light_blue', ['punk_hazard_frozen']),
]
# id, name, stem, leaf, bloom (None = leafy plant), light, dye, biomes
TALL = [
    ('sea_lavender',      'Conomi Sea Lavender',      '#4f7a3a', '#5f9a4a', '#9a7fd6', 0, 'purple', ['conomi_islands', 'east_blue', 'orange_town']),
    ('desert_thistle',    'Alabasta Desert Thistle',  '#8a7a4a', '#a09060', '#c860a0', 0, 'magenta', ['alabasta']),
    ('south_bird_fern',   'Jaya South Bird Fern',     '#2f6a2a', '#4e9a3a', None,      0, None,     ['jaya', 'little_garden']),
    ('primeval_blossom',  'Primeval Blossom',         '#3a5a2a', '#4a8a3a', '#e83a2a', 0, 'red',    ['little_garden']),
    ('withered_bramble',  'Withered Bramble',         '#4a3a2a', '#6a5a3a', None,      0, None,     ['thriller_bark', 'withered_forest', 'kuraigana']),
    ('kuri_pampas',       'Kuri Pampas Grass',        '#b8a060', '#d8c890', '#f0e8d0', 0, 'white',  ['kuri', 'alabasta']),
    ('ice_thistle',       'Ice Thistle',              '#8ac8e8', '#b8e0f8', '#ffffff', 0, 'white',  ['punk_hazard_frozen', 'drum_island']),
    ('cinder_shrub',      'Cinder Shrub',             '#3a2a28', '#5a3a30', '#ff6a20', 6, 'orange', ['punk_hazard_burning', 'hachinosu', 'onigashima']),
    ('giant_barley',      'Elbaph Giant Barley',      '#a08a40', '#d8c060', '#f0d870', 0, 'yellow', ['elbaph']),
    ('mink_fern',         'Zou Mink Fern',            '#2a7a3a', '#4fb84a', None,      0, None,     ['zou', 'green_bit']),
    ('passion_rose',      'Dressrosa Passion Rose',   '#3a6a2a', '#4f8a3a', '#e8203a', 0, 'red',    ['dressrosa']),
    ('candy_shrub',       'Totto Land Candy Shrub',   '#f0c0e0', '#f8d8f0', '#ff60a0', 0, 'pink',   ['whole_cake', 'cacao_island']),
    ('oni_thistle',       'Oni Thistle',              '#3a1a20', '#5a2a30', '#b01030', 0, 'red',    ['onigashima']),
    ('pirate_bramble',    'Hachinosu Pirate Bramble', '#3a3028', '#5a4a38', None,      0, None,     ['hachinosu']),
    ('kuraigana_thistle', 'Kuraigana Thistle',        '#4a4a50', '#6a6a70', '#8a6aa0', 0, 'purple', ['kuraigana']),
    ('celestial_lily',    'Celestial Lily',           '#6a8a3a', '#8aa84a', '#fff0b0', 2, 'yellow', ['god_valley', 'enies_lobby']),
    ('cliff_thistle',     'Red Line Cliff Thistle',   '#6a4a3a', '#8a6a4a', '#c04040', 0, 'red',    ['red_line']),
    ('upper_yard_reed',   'Upper Yard Reed',          '#9fc8a0', '#c8e8c8', '#ffffff', 0, 'white',  ['skypiea']),
    ('mangrove_reed',     'Sabaody Mangrove Reed',    '#5a8a4a', '#7aa860', None,      0, None,     ['sabaody']),
    ('neon_fern',         'Egghead Neon Fern',        '#20808a', '#40f0ff', None,      6, None,     ['egghead']),
]
# id, name, base colour, tip colour, dry seed heads, light, dye, biomes
GRASS = [
    ('frost_fern',        'Frost Fern',               '#a8d8f0', '#d8f0ff', False, 0, 'light_blue', ['drum_island', 'punk_hazard_frozen', 'elbaph']),
    ('sand_sage',         'Sand Sage',                '#b8a870', '#d0c090', True,  0, 'yellow',     ['alabasta', 'kuri']),
    ('heaven_grass',      'Heaven Grass',             '#d8e8ff', '#f0f6ff', False, 0, 'white',      ['skypiea']),
    ('dino_fern',         'Dino Fern',                '#2f7a2a', '#3f9a3a', False, 0, 'green',      ['little_garden', 'jaya']),
    ('ember_grass',       'Ember Grass',              '#c83a1a', '#ff7a30', True,  5, 'orange',     ['punk_hazard_burning', 'hachinosu', 'onigashima']),
    ('wafer_grass',       'Wafer Grass',              '#e8d0a0', '#f8e8c8', True,  0, 'white',      ['whole_cake', 'cacao_island']),
    ('ash_grass',         'Ash Grass',                '#6a6060', '#8a8080', True,  0, 'gray',       ['onigashima', 'hachinosu', 'kuraigana']),
    ('celestial_grass',   'Celestial Grass',          '#e8e0a0', '#fff8d0', False, 0, 'yellow',     ['god_valley', 'enies_lobby']),
    ('harbor_sedge',      'Harbor Sedge',             '#5a8a5a', '#7aa87a', False, 0, 'green',      ['loguetown', 'marineford', 'east_blue', 'conomi_islands']),
    ('sawgrass',          'Jungle Sawgrass',          '#3a9a3a', '#5ab84a', False, 0, 'lime',       ['amazon_lily', 'green_bit', 'zou']),
    ('gloom_grass',       'Gloom Grass',              '#3a4a3a', '#4a5a48', False, 0, 'gray',       ['thriller_bark', 'withered_forest']),
    ('cliff_tuft',        'Red Line Cliff Tuft',      '#8a7a60', '#a89a80', True,  0, 'brown',      ['red_line']),
    ('wano_rice_grass',   'Wano Rice Grass',          '#6aa84a', '#c8d890', True,  0, 'lime',       ['wano', 'kuri']),
    ('olive_grass',       'Dressrosa Olive Grass',    '#7a9a4a', '#a8b870', False, 0, 'green',      ['dressrosa', 'orange_town']),
    ('mangrove_sedge',    'Mangrove Sedge',           '#4a8a5a', '#6aa87a', False, 0, 'green',      ['sabaody']),
    ('lab_moss_tuft',     'Lab Moss Tuft',            '#5a9a90', '#a0f0e0', False, 0, 'cyan',       ['egghead']),
]
# id, name, leaf, berry, dye, biomes
BUSHES = [
    ('drum_holly',        'Drum Holly',               '#1f5a2a', '#e02020', 'red',    ['drum_island', 'elbaph']),
    ('date_shrub',        'Desert Date Shrub',        '#6a7a40', '#c88a30', 'brown',  ['alabasta', 'kuri']),
    ('jungle_shrub',      'Jungle Shrub',             '#2f7a2a', None,      'green',  ['jaya', 'little_garden', 'amazon_lily', 'green_bit', 'zou']),
    ('cloud_shrub',       'Cloud Shrub',              '#e8f0ff', None,      'white',  ['skypiea']),
    ('thorn_bramble',     'Thorn Bramble',            '#4a3a30', '#5a1020', 'black',  ['thriller_bark', 'kuraigana', 'withered_forest', 'hachinosu']),
    ('wano_azalea',       'Wano Azalea',              '#4a8a3a', '#f080b0', 'pink',   ['wano']),
    ('gumdrop_bush',      'Gumdrop Bush',             '#f0c0e8', '#ff4080', 'magenta', ['whole_cake', 'cacao_island']),
    ('olive_shrub',       'Dressrosa Olive Shrub',    '#6a8a4a', '#3a4a2a', 'green',  ['dressrosa', 'enies_lobby', 'god_valley']),
    ('sea_grape_shrub',   'Sea Grape Shrub',          '#4a8a4a', '#8a4aa0', 'purple', EAST_BLUE),
    ('cinder_bush',       'Cinder Bush',              '#3a3030', '#ff6020', 'orange', ['punk_hazard_burning', 'onigashima']),
    ('frostberry_bush',   'Frostberry Bush',          '#5a8aa0', '#a0e0ff', 'light_blue', ['punk_hazard_frozen', 'elbaph', 'drum_island']),
    ('resin_shrub',       'Yarukiman Resin Shrub',    '#5a9a5a', '#bfe9ff', 'light_blue', ['sabaody']),
    ('egghead_hedge',     'Egghead Hedge',            '#3a8a80', '#40f0ff', 'cyan',   ['egghead']),
    ('red_line_scrub',    'Red Line Scrub',           '#7a6a4a', None,      'brown',  ['red_line']),
]
# id, name, colour, leaf colour, kind (cover = scattered, moss = dense carpet), light, dye, biomes
COVERS = [
    ('orange_blossom_petals', 'Orange Blossom Petals', '#fff2e0', '#f08a1c', 'cover', 0, 'orange',    ['orange_town', 'conomi_islands']),
    ('harbor_moss',       'Harbor Moss',              '#5a7a4a', '#4a6a3a', 'moss',  0, 'green',      ['loguetown', 'marineford', 'east_blue']),
    ('frost_moss',        'Frost Moss',               '#cfe8f8', '#a8c8e0', 'moss',  0, 'light_blue', ['punk_hazard_frozen', 'drum_island', 'egghead']),
    ('fern_litter',       'Fern Litter',              '#4a7a2a', '#3a6a2a', 'cover', 0, 'green',      ['little_garden', 'jaya']),
    ('cobweb_moss',       'Cobweb Moss',              '#c8c8d0', '#8a8a98', 'cover', 0, 'light_gray', ['thriller_bark', 'kuraigana']),
    ('fallen_leaves',     'Fallen Leaves',            '#d8702a', '#8a4a20', 'cover', 0, 'orange',     ['withered_forest', 'kuri']),
    ('white_clover',      'White Clover',             '#ffffff', '#4a9a3a', 'cover', 0, 'white',      ['enies_lobby', 'marineford', 'dressrosa']),
    ('zunesha_moss',      'Zunesha Moss',             '#5ad04a', '#3a9a3a', 'moss',  0, 'lime',       ['zou', 'green_bit']),
    ('python_ivy',        'Python Ivy',               '#2a8a3a', '#1a6a2a', 'moss',  0, 'green',      ['amazon_lily']),
    ('chocolate_moss',    'Chocolate Moss',           '#6a3a1a', '#4a2a10', 'moss',  0, 'brown',      ['cacao_island']),
    ('sugar_frost',       'Sugar Frost',              '#fff0f8', '#f8c8e8', 'cover', 0, 'pink',       ['whole_cake']),
    ('lab_lichen',        'Lab Lichen',               '#40e8ff', '#208090', 'cover', 6, 'cyan',       ['egghead']),
    ('ruin_moss',         'Ruin Moss',                '#6a7a5a', '#4a5a40', 'moss',  0, 'green',      ['kuraigana', 'god_valley', 'red_line']),
    ('ember_ash',         'Ember Ash',                '#4a3a38', '#ff5a20', 'cover', 3, 'gray',       ['punk_hazard_burning', 'onigashima', 'hachinosu']),
    ('royal_ivy',         'Royal Ivy',                '#c8a840', '#6a8a3a', 'cover', 0, 'yellow',     ['god_valley']),
    ('cloud_moss',        'Cloud Moss',               '#f0f6ff', '#c8d8f0', 'moss',  0, 'white',      ['skypiea']),
    ('bubble_lichen',     'Sabaody Bubble Lichen',    '#bfe9ff', '#7aa860', 'cover', 2, 'light_blue', ['sabaody']),
    ('dune_scrub',        'Alabasta Dune Scrub',      '#c8b070', '#8a7a4a', 'cover', 0, 'yellow',     ['alabasta']),
    ('tatami_rush',       'Wano Tatami Rush',         '#a8b860', '#6a8a3a', 'cover', 0, 'lime',       ['wano']),
    ('giant_clover_patch', 'Elbaph Clover Patch',     '#3a8a3a', '#f2e6a0', 'moss',  0, 'green',      ['elbaph']),
]
# id, name, kind (sand/soil), colour, specks, vanilla block to copy, recipe ingredients (x2 output)
CUBES = [
    ('sugar_sand',   'Sugar Sand',   'sand', '#f8ecf0', '#f8c8e8', 'SAND',        ['minecraft:sand', 'minecraft:sugar']),
    ('black_sand',   'Black Sand',   'sand', '#2a2a30', '#4a4a50', 'SAND',        ['minecraft:sand', 'minecraft:black_dye']),
    ('volcanic_ash', 'Volcanic Ash', 'soil', '#4a4446', '#ff6a20', 'COARSE_DIRT', ['minecraft:gravel', 'minecraft:charcoal']),
    ('grave_soil',   'Grave Soil',   'soil', '#3a3230', '#8a8a80', 'COARSE_DIRT', ['minecraft:dirt', 'minecraft:bone_meal']),
    ('jungle_loam',  'Jungle Loam',  'soil', '#4a3a22', '#6a8a3a', 'DIRT',        ['minecraft:dirt', 'minecraft:vine']),
    ('permafrost',   'Permafrost',   'soil', '#8a9aa8', '#d8e8f0', 'COARSE_DIRT', ['minecraft:dirt', 'minecraft:snowball']),
]
# What our plants may stand on, besides what the deco plants accept (grass, dirt, sand, snow, stone, ash...).
EXTRA_SOIL = ['#onepiece:deco_plant_soil', 'minecraft:mud', 'minecraft:moss_block', 'minecraft:pale_moss_block',
              'minecraft:red_sand', 'minecraft:suspicious_sand', 'minecraft:clay'] + [f'onepiece:{c[0]}' for c in CUBES]

# ==================================================================================================== helpers
names = OrderedDict()
java_blocks = []
tab_order = []
tags = {}
textures = {}
placed = []  # (id, state to place, survive state, rarity, count, spread)


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        if isinstance(data, str):
            f.write(data)
        else:
            json.dump(data, f, indent=2); f.write('\n')


def tag(kind, name, *ids):
    tags.setdefault(f'{kind}:{name}', []).extend(i if ':' in i or i.startswith('#') else 'onepiece:' + i for i in ids)


def const(i):
    return i.upper()


def biome_id(b):
    return b if ':' in b else 'onepiece:' + b


def cross_model(i, texture=None):
    write(f'{A}/blockstates/{i}.json', {"variants": {"": {"model": f"onepiece:block/{i}"}}})
    write(f'{A}/models/block/{i}.json', {"parent": "minecraft:block/cross", "textures": {"cross": f"onepiece:block/{texture or i}"}})


def flat_item(i, texture):
    write(f'{A}/models/item/{i}.json', {"parent": "minecraft:item/generated", "textures": {"layer0": texture}})
    write(f'{A}/items/{i}.json', {"model": {"type": "minecraft:model", "model": f"onepiece:item/{i}"}})


def self_loot(i):
    write(f'{D}/loot_table/blocks/{i}.json', {
        "type": "minecraft:block",
        "pools": [{"rolls": 1, "bonus_rolls": 0, "entries": [{"type": "minecraft:item", "name": f"onepiece:{i}"}],
                   "condition": {"type": "minecraft:survives_explosion"}}],
        "random_sequence": f"onepiece:blocks/{i}"})


def shapeless(name, ingredients, result, count):
    write(f'{D}/recipe/{name}.json', {"type": "minecraft:crafting_shapeless", "category": "misc",
                                      "ingredients": ingredients, "result": {"id": result, "count": count}})


def dye_recipes(i, dye, dye_count, grow_from):
    """Flower -> dye, and 'grow' recipe: a vanilla plant + the dye -> 2 of ours (so everything can be made at home)."""
    if dye:
        shapeless(f'{dye}_dye_from_{i}', [f'onepiece:{i}'], f'minecraft:{dye}_dye', dye_count)
        shapeless(i, [grow_from, f'minecraft:{dye}_dye'], f'onepiece:{i}', 2)
    else:
        shapeless(i, [grow_from, 'minecraft:bone_meal'], f'onepiece:{i}', 2)


def grows_in(i, biomes):
    write(f'{D}/tags/worldgen/biome/has_flora_{i}.json', {"replace": False, "values": [biome_id(b) for b in biomes]})


# ==================================================================================================== flowers
java_blocks.append('\t// ---- Flowers (one block; also grow on sand, snow, rock and the island soils, see FloraPlants.SOIL) ----')
for (i, nm, shape, petal, center, effect, secs, light, dye, biomes) in FLOWERS:
    java_blocks.append(f'\tpublic static final Block {const(i)} = flower("{i}", MobEffects.{effect}, {secs}, {light});')
    names[i] = nm; tab_order.append(i)
    cross_model(i); flat_item(i, f'onepiece:block/{i}'); self_loot(i)
    draw = {'round': lambda: tx.flower(i, petal, center, glow=light > 0), 'spike': lambda: ft.spike(i, petal, center),
            'bell': lambda: ft.bell(i, petal, center), 'daisy': lambda: ft.daisy(i, petal, center)}[shape]
    textures[f'block/{i}'] = draw()
    dye_recipes(i, dye, 1, 'minecraft:dandelion')
    for k in ('block', 'item'):
        tag(k, 'minecraft:small_flowers', i); tag(k, 'minecraft:flowers', i)
    placed.append((i, {"id": f"onepiece:{i}"}, f"onepiece:{i}", 3, 32, 6))
    grows_in(i, biomes)

# ==================================================================================================== tall plants
java_blocks.append('')
java_blocks.append('\t// ---- Two-block plants ----')
for (i, nm, stem, leaf, bloom, light, dye, biomes) in TALL:
    java_blocks.append(f'\tpublic static final Block {const(i)} = tall("{i}", {light});')
    names[i] = nm; tab_order.append(i)
    write(f'{A}/blockstates/{i}.json', {"variants": {"half=lower": {"model": f"onepiece:block/{i}_bottom"}, "half=upper": {"model": f"onepiece:block/{i}_top"}}})
    for half in ('bottom', 'top'):
        write(f'{A}/models/block/{i}_{half}.json', {"parent": "minecraft:block/cross", "textures": {"cross": f"onepiece:block/{i}_{half}"}})
    flat_item(i, f'onepiece:block/{i}_top')
    write(f'{D}/loot_table/blocks/{i}.json', {
        "type": "minecraft:block",
        "pools": [{"rolls": 1, "condition": {"type": "minecraft:survives_explosion"},
                   "entries": [{"type": "minecraft:item", "name": f"onepiece:{i}",
                                "condition": {"type": "minecraft:match_block", "blocks": f"onepiece:{i}", "state": {"half": "lower"}}}]}],
        "random_sequence": f"onepiece:blocks/{i}"})
    textures[f'block/{i}_bottom'] = tx.tall_bottom(i + 'b', stem, leaf)
    textures[f'block/{i}_top'] = tx.tall_top(i + 't', stem, leaf, bloom)
    dye_recipes(i, dye, 2, 'minecraft:tall_grass')
    tag('block', 'minecraft:flowers' if bloom else 'minecraft:replaceable_by_trees', i)
    if bloom: tag('item', 'minecraft:flowers', i)
    placed.append((i, {"id": f"onepiece:{i}", "properties": {"half": "lower"}}, f"onepiece:{i}", 3, 20, 6))
    grows_in(i, biomes)

# ==================================================================================================== grass
java_blocks.append('')
java_blocks.append('\t// ---- Grass tufts with their own colours ----')
for (i, nm, base, tip, dry, light, dye, biomes) in GRASS:
    java_blocks.append(f'\tpublic static final Block {const(i)} = grass("{i}", {light});')
    names[i] = nm; tab_order.append(i)
    cross_model(i); flat_item(i, f'onepiece:block/{i}'); self_loot(i)
    textures[f'block/{i}'] = ft.grass(i, base, tip, dry=dry)
    dye_recipes(i, dye, 1, 'minecraft:short_grass')
    tag('block', 'minecraft:replaceable_by_trees', i); tag('block', 'minecraft:sword_efficient', i)
    placed.append((i, {"id": f"onepiece:{i}"}, f"onepiece:{i}", 1, 40, 7))
    grows_in(i, biomes)

# ==================================================================================================== shrubs
java_blocks.append('')
java_blocks.append('\t// ---- Shrubs ----')
for (i, nm, leaf, berry, dye, biomes) in BUSHES:
    java_blocks.append(f'\tpublic static final Block {const(i)} = shrub("{i}");')
    names[i] = nm; tab_order.append(i)
    cross_model(i); flat_item(i, f'onepiece:block/{i}'); self_loot(i)
    textures[f'block/{i}'] = ft.bush(i, leaf, berry)
    dye_recipes(i, dye, 1, 'minecraft:bush')
    tag('block', 'minecraft:replaceable_by_trees', i); tag('block', 'minecraft:sword_efficient', i)
    placed.append((i, {"id": f"onepiece:{i}"}, f"onepiece:{i}", 2, 12, 6))
    grows_in(i, biomes)

# ==================================================================================================== ground cover
java_blocks.append('')
java_blocks.append('\t// ---- Ground cover (1 to 4 segments per block, like pink petals) ----')
FACING = [('north', 0), ('east', 90), ('south', 180), ('west', 270)]
for (i, nm, color, leaf, kind, light, dye, biomes) in COVERS:
    java_blocks.append(f'\tpublic static final Block {const(i)} = cover("{i}", {light});')
    names[i] = nm; tab_order.append(i)
    parts = []
    for amount in range(1, 5):
        write(f'{A}/models/block/{i}_{amount}.json', {"parent": f"minecraft:block/flowerbed_{amount}",
              "textures": {"flowerbed": f"onepiece:block/{i}", "stem": f"onepiece:block/{i}_stem"}})
        for facing, rot in FACING:
            apply = {"model": f"onepiece:block/{i}_{amount}"}
            if rot: apply["y"] = rot
            parts.append({"apply": apply, "when": {"facing": facing, "flower_amount": str(amount)}})
    write(f'{A}/blockstates/{i}.json', {"multipart": parts})
    flat_item(i, f'onepiece:block/{i}')
    write(f'{D}/loot_table/blocks/{i}.json', {
        "type": "minecraft:block",
        "pools": [{"rolls": 1, "entries": [{"type": "minecraft:item", "name": f"onepiece:{i}", "modifier": [
            {"type": "minecraft:set_count", "count": n, "condition": {"type": "minecraft:match_block", "blocks": f"onepiece:{i}", "state": {"flower_amount": str(n)}}}
            for n in range(1, 5)] + [{"type": "minecraft:explosion_decay"}]}]}],
        "random_sequence": f"onepiece:blocks/{i}"})
    textures[f'block/{i}'] = ft.moss(i, color, leaf) if kind == 'moss' else ft.cover(i, color, leaf, glow=light > 0)
    textures[f'block/{i}_stem'] = tx.stem(i + '_stem', leaf)
    dye_recipes(i, dye, 1, 'minecraft:moss_carpet')
    tag('block', 'minecraft:replaceable_by_trees', i); tag('block', 'minecraft:sword_efficient', i)
    placed.append((i, {"id": f"onepiece:{i}", "properties": {"facing": "north", "flower_amount": "3"}}, f"onepiece:{i}", 2, 36, 5))
    grows_in(i, biomes)

# ==================================================================================================== soils
java_blocks.append('')
java_blocks.append('\t// ---- Island grounds (placed by the Grand Line surface rules, tools/islands/island_flavour.py) ----')
for (i, nm, kind, color, specks, like, recipe) in CUBES:
    java_blocks.append(f'\tpublic static final Block {const(i)} = cube("{i}", Blocks.{like});')
    names[i] = nm; tab_order.append(i)
    write(f'{A}/blockstates/{i}.json', {"variants": {"": {"model": f"onepiece:block/{i}"}}})
    write(f'{A}/models/block/{i}.json', {"parent": "minecraft:block/cube_all", "textures": {"all": f"onepiece:block/{i}"}})
    write(f'{A}/models/item/{i}.json', {"parent": f"onepiece:block/{i}"})
    write(f'{A}/items/{i}.json', {"model": {"type": "minecraft:model", "model": f"onepiece:item/{i}"}})
    self_loot(i)
    textures[f'block/{i}'] = ft.sand(i, color, specks) if kind == 'sand' else ft.soil(i, color, specks)
    shapeless(i, recipe, f'onepiece:{i}', 2)
    tag('block', 'minecraft:mineable/shovel', i)
    tag('block', 'minecraft:sand' if kind == 'sand' else 'minecraft:dirt', i)
    tag('item', 'minecraft:sand' if kind == 'sand' else 'minecraft:dirt', i)
    if kind == 'sand': tag('block', 'minecraft:smelts_to_glass', i)

# ==================================================================================================== worldgen patches
for (i, state, survive, rarity, count, spread) in placed:
    write(f'{D}/worldgen/feature/flora_{i}.json', {"type": "minecraft:simple_block", "to_place": state})
    write(f'{D}/worldgen/placed_feature/flora_{i}.json', {
        "feature": f"onepiece:flora_{i}",
        "placement": [
            {"type": "minecraft:rarity_filter", "chance": rarity},
            {"type": "minecraft:in_square"},
            {"type": "minecraft:heightmap", "heightmap": "MOTION_BLOCKING"},
            {"type": "minecraft:biome"},
            {"type": "minecraft:count", "count": count},
            {"type": "minecraft:offset",
             "x": {"type": "minecraft:trapezoid", "max": spread, "min": -spread, "plateau": 0},
             "y": {"type": "minecraft:trapezoid", "max": 2, "min": -2, "plateau": 0},
             "z": {"type": "minecraft:trapezoid", "max": spread, "min": -spread, "plateau": 0}},
            {"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:all_of", "predicates": [
                {"type": "minecraft:matching_block_tag", "tag": "minecraft:air"},
                {"type": "minecraft:would_survive", "state": survive}]}}]})

write(f'{D}/tags/block/flora_plant_soil.json', {"replace": False, "values": EXTRA_SOIL})

# ==================================================================================================== textures, tags, names
for rel, img in textures.items():
    p = f'{A}/textures/{rel}.png'
    os.makedirs(os.path.dirname(p), exist_ok=True)
    img.save(p)
for key, vals in tags.items():
    kind, full = key.split(':', 1)
    ns, path = full.split(':')
    write(os.path.join(RES, f'data/{ns}/tags/{kind}/{path}.json'), {"replace": False, "values": list(OrderedDict.fromkeys(vals))})
lang = OrderedDict((f'block.onepiece.{i}', nm) for i, nm in names.items())
lang['itemGroup.onepiece.flora'] = 'One Piece: Nature'
write(os.path.join(RES, 'assets/onepiece_flora/lang/en_us.json'), lang)

# ==================================================================================================== Java
HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, 'FloraBlocks.java.in')) as f:
    write(os.path.join(JAVA, 'FloraBlocks.java'), f.read().replace('%%BLOCKS%%', '\n'.join(java_blocks)))
with open(os.path.join(HERE, 'FloraFeature.java.in')) as f:
    tab = '\n'.join(f'\t\t\t\t\toutput.accept(FloraBlocks.{const(i)});' for i in tab_order)
    veg = '\n'.join(f'\t\taddVegetation("{i}");' for (i, *_rest) in placed)
    write(os.path.join(JAVA, 'FloraFeature.java'), f.read().replace('%%TAB%%', tab).replace('%%BIOMES%%', veg))
shutil.copyfile(os.path.join(HERE, 'FloraPlants.java'), os.path.join(JAVA, 'FloraPlants.java'))

# a guide for the project folder: what grows where
guide = ['# Island flora', '', 'Made by tools/flora/gen_flora.py. Every plant is craftable (a vanilla plant + the matching dye, or bone meal) and flowers give dye.', '']
for title, rows, bi in (('Flowers', FLOWERS, -1), ('Two-block plants', TALL, -1), ('Grass', GRASS, -1), ('Shrubs', BUSHES, -1), ('Ground cover', COVERS, -1)):
    guide.append(f'## {title}')
    for row in rows:
        guide.append(f'- **{row[1]}** (`{row[0]}`): ' + ', '.join(b.replace("minecraft:", "vanilla ") for b in row[bi]))
    guide.append('')
guide.append('## Island grounds (surface patches)')
for (i, nm, *_r) in CUBES:
    guide.append(f'- **{nm}** (`{i}`)')
write(os.path.join(OUT, 'flora-guide.md'), '\n'.join(guide) + '\n')
print(f'{len(names)} blocks, {len(textures)} textures, {len(placed)} patch features')

# ==================================================================================================== install
if INSTALL:
    copied = merged = 0
    for root, _, files in os.walk(os.path.join(OUT, 'src')):
        for f in files:
            a = os.path.join(root, f)
            rel = os.path.relpath(a, OUT)
            b = os.path.join(INSTALL, rel)
            os.makedirs(os.path.dirname(b), exist_ok=True)
            if '/data/minecraft/tags/' in rel and os.path.exists(b):
                old = json.load(open(b)); new = json.load(open(a))
                old['values'] = list(OrderedDict.fromkeys(old.get('values', []) + new['values']))
                write(b, old); merged += 1
            else:
                shutil.copyfile(a, b); copied += 1
    print(f'installed into {INSTALL}: copied {copied}, merged {merged} shared tag files')
