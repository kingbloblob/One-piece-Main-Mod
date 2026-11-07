"""Generates the assets and data for the mineable/collectable resources (package com.onepiecemod.resource).

Run: python3 gen_resources.py <path to source/>
Writes textures, models, blockstates, equipment, names (assets/onepiece_resources/lang), block loot tables,
vanilla recipes, ore features and their biome tags, and appends to shared tag files and station_recipes.json.
"""
import json, os, random, sys
from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else '/mnt/project-files/one-piece-mod/source'
RES = os.path.join(SRC, 'src/main/resources')
A = os.path.join(RES, 'assets/onepiece')
D = os.path.join(RES, 'data/onepiece')


def wjson(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')


def append_tag(path, values):
    d = json.load(open(path)) if os.path.exists(path) else {"replace": False, "values": []}
    for v in values:
        if v not in d['values']:
            d['values'].append(v)
    wjson(path, d)


# ---------------- textures ----------------

def jit(c, r, a=12):
    return tuple(max(0, min(255, v + r.randint(-a, a))) for v in c[:3]) + (255,)


def base(color, seed, a=12):
    r = random.Random(seed)
    im = Image.new('RGBA', (16, 16))
    for x in range(16):
        for y in range(16):
            im.putpixel((x, y), jit(color, r, a))
    return im, r


def ore(name, stone, dark, light, seed, spots=((3, 3), (10, 2), (6, 8), (12, 10), (2, 12), (8, 13))):
    im, r = base(stone, seed)
    for sx, sy in spots:
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (-1, 0)):
            x, y = sx + dx, sy + dy
            if 0 <= x < 16 and 0 <= y < 16:
                im.putpixel((x, y), jit(dark if (dx + dy) % 2 else light, r, 8))
    save(im, 'block', name)


def save(im, kind, name):
    os.makedirs(os.path.join(A, 'textures', kind), exist_ok=True)
    im.save(os.path.join(A, 'textures', kind, name + '.png'))


def sprite(name, rows, colors, seed):
    r = random.Random(seed)
    im = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row[:16]):
            if ch != '.':
                im.putpixel((x, y), jit(colors[ch], r, 6))
    save(im, 'item', name)


def hexc(s):
    s = s.lstrip('#')
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def shades(c):
    c = hexc(c)
    return {'a': tuple(int(v * 0.5) for v in c), 'b': c, 'c': tuple(min(255, int(v * 1.35 + 30)) for v in c)}


RAW = ["................", "................", "................", ".....aaaa.......", "....abbbaa......", "...abbcbbba.....",
       "...abccbbbba....", "..abbbbbcbba....", "..abbcbbbbba....", "..aabbbbcba.....", "...aabbbbaa.....", "....aaaaaa......",
       "................", "................", "................", "................"]
INGOT = ["................", "................", "................", "................", "................", "......aaaaaa....",
         ".....abccccba...", "....abbbbbbba...", "...abbbbbbbba...", "...aaaaaaaaaa...", "................", "................",
         "................", "................", "................", "................"]
CRYSTAL = ["................", "................", ".......a........", "......aca.......", "......aca..a....", ".....abcba.aca...",
           ".....abcba.aba...", "..a..abbba.aba...", ".aca.abbba.aba...", ".abaaabbbaaaba...", ".abbbbbbbbbbba...", "..aaaaaaaaaaa....",
           "................", "................", "................", "................"]
SHELL = ["................", "................", "................", "......aaaa......", "....aabbbbaa....", "...abbccbbbba...",
         "..abcbaaabcbba..", "..abcabbbacbba..", "..abcabcbacbba..", "..abcbaabcbbba..", "...abccccbbba...", "....aabbbbaa....",
         "......aaaa......", "................", "................", "................"]
DIAL = ["................", "................", "......aaaa......", "....aabbbbaa....", "...abbccbbbba...", "..abcbaaabcbba..",
        "..abcadddacbba..", "..abcaddeacbba..", "..abcadddacbba..", "..abcbaaabcbba..", "...abbccccbba...", "....aabbbbaa....",
        "......aaaa......", "................", "................", "................"]
PEARL = ["................", "................", "................", "................", "......aaaa......", ".....abccba.....",
         "....abccbbba....", "....abcbbbba....", "....abbbbbba....", "....abbbbbba....", ".....abbbba.....", "......aaaa......",
         "................", "................", "................", "................"]
BOTTLE = ["................", "................", "......dddd......", "......eeee......", ".......ee.......", ".......ee.......",
          "......ebbe......", ".....ebbbbe.....", "....ebccbbbe....", "....ebcbbbbe....", "....ebbbbbbe....", "....ebbbbbbe....",
          ".....ebbbbe.....", "......eeee......", "................", "................"]
SCALE = ["................", "................", "................", "......aaaa......", ".....abccba.....", "....abccbbba....",
         "....abcbbbba....", "...abcbbbbbba...", "...abbbbbbbba...", "...abbbbbbbba...", "....abbbbbba....", ".....abbbba.....",
         "......abba......", ".......aa.......", "................", "................"]
BUBBLE = ["................", "................", ".....aaaaaa.....", "....a......a....", "...a.cc.....a...", "..a.cc.......a..",
          "..a.c........a..", "..a..........a..", "..a..........a..", "..a.........ba..", "...a.......ba...", "....a....bba....",
          ".....aaaaaa.....", "................", "................", "................"]
SWORD = ["..............a.", ".............aba", "............abc.", "...........abc..", "..........abc...", ".........abc....",
         "........abc.....", "...e...abc......", "...ee.abc.......", "....eeac........", ".....edd........", "....dd.ee.......",
         "...dd...........", "..fd............", ".ff.............", "................"]
HELMET = ["................", "................", "................", "....aaaaaaaa....", "...abbbbbbbba...", "...abccccccba...",
          "...abc....cba...", "...abc....cba...", "...aba....aba...", "....a......a....", "................", "................",
          "................", "................", "................", "................"]
CHEST = ["................", "...aaa....aaa...", "..abba....abba..", "..abbbaaaabbba..", "..abcbbbbbbcba..", "..abcbbbbbbcba..",
         "...aabbbbbbaa...", "....abbccbba....", "....abbbbbba....", "....abbccbba....", "....abbbbbba....", "....abbbbbba....",
         "....aaaaaaaa....", "................", "................", "................"]
LEGS = ["................", "................", "....aaaaaaaa....", "....abbccbba....", "....abbbbbba....", "....abba.bba....",
        "....abba.bba....", "....abca.bca....", "....abca.bca....", "....abba.bba....", "....abba.bba....", "....aaaa.aaa....",
        "................", "................", "................", "................"]
BOOTS = ["................", "................", "................", "................", "................", "................",
         "....aaa..aaa....", "....aba..aba....", "....aca..aca....", "....aba..aba....", "...abba..abba...", "...aaaa..aaaa...",
         "................", "................", "................", "................"]


def armor_layers(name, color, seed):
    r = random.Random(seed)
    c = hexc(color)
    out = os.path.join(A, 'textures/entity/equipment')
    for layer, regions in (('humanoid', [(0, 0, 32, 16), (16, 16, 40, 32), (40, 16, 56, 32), (0, 16, 16, 32)]),
                           ('humanoid_leggings', [(16, 16, 40, 32), (0, 16, 16, 32)])):
        im = Image.new('RGBA', (64, 32), (0, 0, 0, 0))
        for x0, y0, x1, y1 in regions:
            for y in range(y0, y1):
                for x in range(x0, x1):
                    f = 1.0
                    if (x - x0) % 4 == 0 or (y - y0) % 4 == 0:
                        f = 0.82
                    if y == y0 or x == x0:
                        f = 1.25
                    im.putpixel((x, y), jit(tuple(min(255, int(v * f)) for v in c), r, 8))
        os.makedirs(os.path.join(out, layer), exist_ok=True)
        im.save(os.path.join(out, layer, name + '.png'))
    wjson(os.path.join(A, 'equipment', name + '.json'), {"layers": {
        "humanoid": [{"texture": "onepiece:" + name}], "humanoid_leggings": [{"texture": "onepiece:" + name}]}})


# ---------------- definitions ----------------
# (id, display name)
BLOCKS = [
    ('tamahagane_ore', 'Tamahagane Ore'), ('deepslate_tamahagane_ore', 'Deepslate Tamahagane Ore'),
    ('wapometal_ore', 'Wapometal Ore'), ('deepslate_wapometal_ore', 'Deepslate Wapometal Ore'),
    ('shandora_gold_ore', 'Shandora Gold Ore'), ('sulfur_ore', 'Sulfur Ore'), ('nether_sulfur_ore', 'Nether Sulfur Ore'),
    ('deepslate_kokuto_ore', 'Kokuto Ore'), ('shell_sand', 'Shell Sand'), ('oyster_gravel', 'Oyster Gravel'),
    ('poneglyph', 'Poneglyph'),
]
METALS = {  # raw, ingot colors
    'tamahagane': '#9aa4b0', 'wapometal': '#6f8a96', 'shandora_gold': '#f2c230', 'kokuto': '#2c2830',
}
ITEMS = [
    ('raw_tamahagane', 'Raw Tamahagane'), ('tamahagane_ingot', 'Tamahagane Ingot'),
    ('raw_wapometal', 'Raw Wapometal'), ('wapometal_ingot', 'Wapometal Ingot'),
    ('raw_shandora_gold', 'Raw Shandora Gold'), ('shandora_gold_ingot', 'Shandora Gold Ingot'),
    ('sulfur', 'Sulfur'), ('raw_kokuto', 'Raw Kokuto'), ('kokuto_ingot', 'Kokuto Black Steel'),
    ('dial_shell', 'Dial Shell'), ('sea_pearl', 'Sea Pearl'), ('yarukiman_resin', 'Yarukiman Resin'),
    ('sea_king_scale', 'Sea King Scale'), ('kraken_ink', 'Kraken Ink'), ('dragon_scale', 'Dragon Scale'),
    ('flash_dial', 'Flash Dial'), ('breath_dial', 'Breath Dial'), ('bubble_coating', 'Bubble Coating'),
    ('tamahagane_katana', 'Tamahagane Katana'), ('kokuto_blade', 'Kokuto Black Blade'),
    ('diving_helmet', 'Fishman Diving Helmet'),
]
ARMOR = {'wapometal': ('Wapometal', '#6f8a96'), 'sea_king_scale': ('Sea King Scale', '#2f8f9a'),
         'dragon_scale': ('Dragon Scale', '#8a2a2a')}
PIECES = [('helmet', 'Helmet', HELMET), ('chestplate', 'Chestplate', CHEST), ('leggings', 'Leggings', LEGS),
          ('boots', 'Boots', BOOTS)]


def textures():
    stone, deep, nether = (125, 125, 125), (72, 72, 78), (110, 52, 52)
    ore('tamahagane_ore', stone, (90, 100, 112), (200, 210, 222), 21)
    ore('deepslate_tamahagane_ore', deep, (90, 100, 112), (200, 210, 222), 22)
    ore('wapometal_ore', stone, (60, 80, 92), (130, 170, 185), 23)
    ore('deepslate_wapometal_ore', deep, (60, 80, 92), (130, 170, 185), 24)
    ore('shandora_gold_ore', (150, 140, 110), (200, 140, 20), (255, 220, 70), 25)
    ore('sulfur_ore', stone, (180, 160, 20), (240, 225, 60), 26)
    ore('nether_sulfur_ore', nether, (180, 160, 20), (240, 225, 60), 27)
    ore('deepslate_kokuto_ore', deep, (20, 18, 24), (90, 60, 110), 28, spots=((4, 4), (11, 7), (6, 12)))
    ore('shell_sand', (219, 207, 163), (200, 120, 140), (250, 230, 240), 29, spots=((3, 4), (11, 3), (7, 10), (13, 12)))
    ore('oyster_gravel', (130, 124, 122), (70, 70, 80), (235, 235, 245), 30, spots=((4, 5), (12, 9), (6, 13)))
    im, r = base((38, 38, 44), 31, 6)
    for y in range(2, 15, 3):
        for x in range(2, 14):
            if r.random() < 0.55:
                im.putpixel((x, y), jit((95, 110, 120), r, 6))
    for i in range(16):
        for p in ((i, 0), (0, i)):
            im.putpixel(p, jit((60, 60, 68), r, 4))
    save(im, 'block', 'poneglyph')

    for i, (m, c) in enumerate(METALS.items()):
        sprite('raw_' + m, RAW, shades(c), 40 + i)
        sprite(m + ('_ingot'), INGOT, shades(c), 50 + i)
    sprite('sulfur', CRYSTAL, shades('#e6d23a'), 60)
    sprite('dial_shell', SHELL, shades('#e8c0c8'), 61)
    sprite('sea_pearl', PEARL, shades('#e8eef6'), 62)
    sprite('yarukiman_resin', BOTTLE, dict(shades('#d89a30'), d=(120, 80, 40), e=(200, 220, 230)), 63)
    sprite('sea_king_scale', SCALE, shades('#2f8f9a'), 64)
    sprite('kraken_ink', BOTTLE, dict(shades('#3a1a40'), d=(120, 80, 40), e=(200, 220, 230)), 65)
    sprite('dragon_scale', SCALE, shades('#a02a2a'), 66)
    sprite('flash_dial', DIAL, dict(shades('#e8c0c8'), d=(255, 250, 180), e=(255, 255, 255)), 67)
    sprite('breath_dial', DIAL, dict(shades('#e8c0c8'), d=(180, 230, 240), e=(255, 255, 255)), 68)
    sprite('bubble_coating', BUBBLE, {'a': (150, 200, 230), 'b': (100, 160, 210), 'c': (240, 250, 255)}, 69)
    sprite('tamahagane_katana', SWORD, {'a': (90, 100, 112), 'b': (200, 210, 222), 'c': (150, 160, 172),
                                        'd': (40, 30, 60), 'e': (200, 170, 60), 'f': (20, 20, 30)}, 70)
    sprite('kokuto_blade', SWORD, {'a': (10, 8, 14), 'b': (70, 50, 90), 'c': (40, 30, 50),
                                   'd': (120, 20, 20), 'e': (200, 170, 60), 'f': (20, 20, 30)}, 71)
    sprite('diving_helmet', HELMET, dict(shades('#b87333')), 72)
    for i, (m, (_, c)) in enumerate(ARMOR.items()):
        for j, (piece, _, rows) in enumerate(PIECES):
            sprite('%s_%s' % (m, piece), rows, shades(c), 80 + i * 4 + j)
        armor_layers(m, c, 90 + i)
    armor_layers('diving', '#b87333', 95)


def models():
    for b, _ in BLOCKS:
        wjson(os.path.join(A, 'blockstates', b + '.json'), {"variants": {"": {"model": "onepiece:block/" + b}}})
        wjson(os.path.join(A, 'models/block', b + '.json'), {"parent": "minecraft:block/cube_all", "textures": {"all": "onepiece:block/" + b}})
        wjson(os.path.join(A, 'items', b + '.json'), {"model": {"type": "minecraft:model", "model": "onepiece:block/" + b}})
    names = [i for i, _ in ITEMS] + ['%s_%s' % (m, p) for m in ARMOR for p, _, _ in PIECES]
    for i in names:
        parent = 'minecraft:item/handheld' if i in ('tamahagane_katana', 'kokuto_blade') else 'minecraft:item/generated'
        wjson(os.path.join(A, 'models/item', i + '.json'), {"parent": parent, "textures": {"layer0": "onepiece:item/" + i}})
        wjson(os.path.join(A, 'items', i + '.json'), {"model": {"type": "minecraft:model", "model": "onepiece:item/" + i}})
    lang = {'block.onepiece.' + b: n for b, n in BLOCKS}
    lang.update({'item.onepiece.' + i: n for i, n in ITEMS})
    for m, (n, _) in ARMOR.items():
        for p, pn, _ in PIECES:
            lang['item.onepiece.%s_%s' % (m, p)] = '%s %s' % (n, pn)
    wjson(os.path.join(RES, 'assets/onepiece_resources/lang/en_us.json'), lang)


def loot():
    def ore_loot(b, drop, lo=1, hi=1):
        mods = []
        if (lo, hi) != (1, 1):
            mods.append({"type": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": lo, "max": hi}})
        mods += [{"type": "minecraft:apply_bonus", "enchantment": "minecraft:fortune", "formula": "minecraft:ore_drops"},
                 {"type": "minecraft:explosion_decay"}]
        return {"type": "minecraft:block", "pools": [{"rolls": 1, "entries": [{"type": "minecraft:alternatives", "children": [
            {"type": "minecraft:item", "condition": "minecraft:tool/can_silk_touch", "name": "onepiece:" + b},
            {"type": "minecraft:item", "name": drop, "modifier": mods}]}]}], "random_sequence": "onepiece:blocks/" + b}
    for m in ('tamahagane', 'wapometal'):
        for b in (m + '_ore', 'deepslate_' + m + '_ore'):
            wjson(os.path.join(D, 'loot_table/blocks', b + '.json'), ore_loot(b, 'onepiece:raw_' + m))
    wjson(os.path.join(D, 'loot_table/blocks/shandora_gold_ore.json'), ore_loot('shandora_gold_ore', 'onepiece:raw_shandora_gold'))
    wjson(os.path.join(D, 'loot_table/blocks/deepslate_kokuto_ore.json'), ore_loot('deepslate_kokuto_ore', 'onepiece:raw_kokuto'))
    for b in ('sulfur_ore', 'nether_sulfur_ore'):
        wjson(os.path.join(D, 'loot_table/blocks', b + '.json'), ore_loot(b, 'onepiece:sulfur', 1, 3))
    wjson(os.path.join(D, 'loot_table/blocks/shell_sand.json'), ore_loot('shell_sand', 'onepiece:dial_shell'))
    # Oyster gravel: gravel back, plus a 1 in 5 chance of a pearl (better with Fortune).
    wjson(os.path.join(D, 'loot_table/blocks/oyster_gravel.json'), {"type": "minecraft:block", "pools": [
        {"rolls": 1, "entries": [{"type": "minecraft:alternatives", "children": [
            {"type": "minecraft:item", "condition": "minecraft:tool/can_silk_touch", "name": "onepiece:oyster_gravel"},
            {"type": "minecraft:item", "name": "minecraft:gravel"}]}]},
        {"rolls": 1, "condition": {"type": "minecraft:all_of", "terms": [
            {"type": "minecraft:inverted", "term": "minecraft:tool/can_silk_touch"},
            {"type": "minecraft:table_bonus", "enchantment": "minecraft:fortune", "chances": [0.2, 0.3, 0.4, 0.6]}]},
         "entries": [{"type": "minecraft:item", "name": "onepiece:sea_pearl"}]}],
        "random_sequence": "onepiece:blocks/oyster_gravel"})


def recipes():
    R = os.path.join(D, 'recipe')
    for m in METALS:
        for kind, t in (('smelting', 200), ('blasting', 100)):
            wjson(os.path.join(R, '%s_ingot_from_%s.json' % (m, kind) if m != 'kokuto' else 'kokuto_ingot_from_%s.json' % kind),
                  {"type": "minecraft:" + kind, "cookingtime": t * (2 if m == 'kokuto' else 1), "experience": 1.0,
                   "group": m + "_ingot", "ingredient": "onepiece:raw_" + m, "result": {"id": "onepiece:%s_ingot" % m}})

    def shapeless(name, ingredients, result, count):
        wjson(os.path.join(R, name + '.json'), {"type": "minecraft:crafting_shapeless", "category": "misc",
                                                "ingredients": ingredients, "result": {"count": count, "id": result}})
    shapeless('gunpowder_from_sulfur', ["onepiece:sulfur", "onepiece:sulfur", "minecraft:charcoal"], "minecraft:gunpowder", 3)
    shapeless('berry_from_shandora_gold', ["onepiece:shandora_gold_ingot"], "onepiece:berry", 10)
    shapeless('black_dye_from_kraken_ink', ["onepiece:kraken_ink"], "minecraft:black_dye", 2)
    shapeless('bubble_resin_from_yarukiman_resin', ["onepiece:yarukiman_resin"], "onepiece:bubble_resin", 4)
    wjson(os.path.join(R, 'pearl_block_from_sea_pearl.json'), {"type": "minecraft:crafting_shaped", "category": "building",
          "pattern": ["##", "##"], "key": {"#": "onepiece:sea_pearl"}, "result": {"count": 4, "id": "onepiece:pearl_block"}})
    wjson(os.path.join(R, 'shandora_gold_bricks_from_shandora_gold.json'), {"type": "minecraft:crafting_shaped",
          "category": "building", "pattern": ["###", "#X#", "###"],
          "key": {"#": "minecraft:stone_bricks", "X": "onepiece:shandora_gold_ingot"},
          "result": {"count": 8, "id": "onepiece:shandora_gold_bricks"}})


def ore_feature(name, targets, size, count, lo, hi, biomes, discard=0.0):
    wjson(os.path.join(D, 'worldgen/feature/ore_%s.json' % name), {"type": "minecraft:ore",
          "discard_chance_on_air_exposure": discard, "size": size,
          "targets": [{"state": state, "target": t} for state, t in targets]})
    wjson(os.path.join(D, 'worldgen/placed_feature/ore_%s.json' % name), {"feature": "onepiece:ore_" + name, "placement": [
        {"type": "minecraft:count", "count": count}, {"type": "minecraft:in_square"},
        {"type": "minecraft:height_range", "height": {"type": "minecraft:uniform", "min_inclusive": {"absolute": lo},
                                                       "max_inclusive": {"absolute": hi}}},
        {"type": "minecraft:biome"}]})
    wjson(os.path.join(D, 'tags/worldgen/biome/has_ore_%s.json' % name),
          {"replace": False, "values": [b if (':' in b or b.startswith('#')) else 'minecraft:' + b for b in biomes]})


STONE = {"predicate_type": "minecraft:tag_match", "tag": "minecraft:stone_ore_replaceables"}
DEEP = {"predicate_type": "minecraft:tag_match", "tag": "minecraft:deepslate_ore_replaceables"}


def match(block):
    return {"predicate_type": "minecraft:block_match", "block": block}


def worldgen():
    ore_feature('tamahagane', [('onepiece:tamahagane_ore', STONE), ('onepiece:deepslate_tamahagane_ore', DEEP)], 8, 10, -16, 160,
                ['jagged_peaks', 'stony_peaks', 'frozen_peaks', 'snowy_slopes', 'grove', 'meadow', 'windswept_hills',
                 'windswept_gravelly_hills', 'windswept_forest', 'cherry_grove', 'onepiece:wano', 'onepiece:onigashima'])
    ore_feature('wapometal', [('onepiece:wapometal_ore', STONE), ('onepiece:deepslate_wapometal_ore', DEEP)], 7, 8, -16, 128,
                ['snowy_slopes', 'frozen_peaks', 'jagged_peaks', 'ice_spikes', 'snowy_plains', 'snowy_taiga', 'grove',
                 'onepiece:drum_island', 'onepiece:punk_hazard_frozen'])
    ore_feature('shandora_gold', [('onepiece:shandora_gold_ore', STONE)], 8, 6, 0, 120,
                ['badlands', 'eroded_badlands', 'wooded_badlands', 'jungle', 'bamboo_jungle', 'sparse_jungle',
                 'onepiece:skypiea', 'onepiece:jaya'])
    ore_feature('sulfur', [('onepiece:sulfur_ore', STONE)], 12, 12, 0, 96,
                ['badlands', 'eroded_badlands', 'desert', 'onepiece:punk_hazard_burning', 'onepiece:punk_hazard_frozen',
                 'onepiece:alabasta'])
    ore_feature('nether_sulfur', [('onepiece:nether_sulfur_ore', match('minecraft:netherrack'))], 10, 14, 10, 118,
                ['#minecraft:is_nether'])
    ore_feature('kokuto', [('onepiece:deepslate_kokuto_ore', DEEP)], 4, 2, -64, -24, ['#minecraft:is_overworld'], 0.5)
    ore_feature('shell_sand', [('onepiece:shell_sand', match('minecraft:sand')), ('onepiece:shell_sand', match('onepiece:island_cloud'))],
                10, 6, 50, 140, ['beach', 'onepiece:skypiea', 'onepiece:jaya', 'onepiece:east_blue', 'onepiece:alabasta'])
    ore_feature('oyster_gravel', [('onepiece:oyster_gravel', match('minecraft:gravel')), ('onepiece:oyster_gravel', match('minecraft:sand'))],
                10, 10, 20, 62, ['#minecraft:is_ocean', 'onepiece:fishman_reef'])


def tags():
    T = os.path.join(RES, 'data/minecraft/tags/block')
    ores = ['onepiece:' + b for b, _ in BLOCKS if b.endswith('_ore')]
    append_tag(os.path.join(T, 'mineable/pickaxe.json'), ores)
    append_tag(os.path.join(T, 'mineable/shovel.json'), ['onepiece:shell_sand', 'onepiece:oyster_gravel'])
    append_tag(os.path.join(T, 'needs_iron_tool.json'), ['onepiece:tamahagane_ore', 'onepiece:deepslate_tamahagane_ore',
                                                         'onepiece:wapometal_ore', 'onepiece:deepslate_wapometal_ore',
                                                         'onepiece:shandora_gold_ore'])
    append_tag(os.path.join(T, 'needs_diamond_tool.json'), ['onepiece:deepslate_kokuto_ore'])
    append_tag(os.path.join(RES, 'data/minecraft/tags/item/swords.json'), ['onepiece:tamahagane_katana', 'onepiece:kokuto_blade'])
    for m, item in (('wapometal', 'wapometal_ingot'), ('sea_king_scale', 'sea_king_scale'),
                    ('dragon_scale', 'dragon_scale'), ('diving', 'sea_pearl')):
        wjson(os.path.join(D, 'tags/item/repairs_%s_armor.json' % m), {"values": ["onepiece:" + item]})


def station_recipes():
    path = os.path.join(RES, 'onepiece/station_recipes.json')
    recipes = json.load(open(path))
    ids = {r['id'] for r in recipes}

    def add(rid, station, result, count, ingredients, boss=None):
        r = {"id": rid, "station": station, "result": result, "count": count,
             "ingredients": [{"item": i, "count": c} for i, c in ingredients]}
        if boss:
            r["requires"] = {"boss": boss}
        if rid not in ids:
            recipes.append(r)
            ids.add(rid)
    op = lambda s: 'onepiece:' + s
    mc = lambda s: 'minecraft:' + s
    add('tamahagane_katana', 'swordsmith_forge', op('tamahagane_katana'), 1,
        [(op('tamahagane_ingot'), 3), (mc('stick'), 1), (mc('leather'), 1)])
    add('kokuto_blade', 'swordsmith_forge', op('kokuto_blade'), 1,
        [(op('tamahagane_katana'), 1), (op('kokuto_ingot'), 3), (mc('blaze_powder'), 2)], 'mihawk')
    for m, ing, station, boss in (('wapometal', op('wapometal_ingot'), 'shipwright_bench', None),
                                  ('sea_king_scale', op('sea_king_scale'), 'seastone_workbench', None),
                                  ('dragon_scale', op('dragon_scale'), 'swordsmith_forge', 'kaido')):
        extra = [] if m == 'wapometal' else [(op('seastone_ingot') if m == 'sea_king_scale' else op('kokuto_ingot'), 1)]
        for piece, n in (('helmet', 5), ('chestplate', 8), ('leggings', 7), ('boots', 4)):
            add('%s_%s' % (m, piece), station, op('%s_%s' % (m, piece)), 1, [(ing, n)] + extra, boss)
    add('diving_helmet', 'shipwright_bench', op('diving_helmet'), 1,
        [(op('sea_pearl'), 3), (mc('copper_ingot'), 5), (mc('glass'), 1)])
    add('flash_dial', 'navigators_desk', op('flash_dial'), 1, [(op('dial_shell'), 1), (mc('glowstone_dust'), 4)])
    add('breath_dial', 'navigators_desk', op('breath_dial'), 1, [(op('dial_shell'), 1), (mc('feather'), 4), (mc('phantom_membrane'), 1)])
    add('bubble_coating', 'navigators_desk', op('bubble_coating'), 2, [(op('yarukiman_resin'), 1), (mc('slime_ball'), 1)])
    add('bullet_from_sulfur', 'shipwright_bench', op('bullet'), 12, [(mc('iron_ingot'), 1), (op('sulfur'), 1)])
    add('cannonball_from_sulfur', 'shipwright_bench', op('cannonball'), 4, [(mc('iron_ingot'), 2), (op('sulfur'), 2)])
    # The weapon Dials are carved from real Dial shells now, instead of nautilus shells.
    for r in recipes:
        if r['id'] in ('flame_dial', 'impact_dial'):
            for ing in r['ingredients']:
                if ing.get('item') == 'minecraft:nautilus_shell':
                    ing['item'] = 'onepiece:dial_shell'
    with open(path, 'w') as f:
        json.dump(recipes, f, indent=2)
        f.write('\n')


def creature_drops():
    # Sea King scale on the Sea King (sea feature's loot table): add one pool if missing.
    p = os.path.join(D, 'loot_table/entities/sea_king.json')
    d = json.load(open(p))
    if 'onepiece:sea_king_scale' not in json.dumps(d):
        d['pools'].append({"rolls": 1, "entries": [{"type": "minecraft:item", "name": "onepiece:sea_king_scale", "modifier": [
            {"type": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": 2, "max": 5}},
            {"type": "minecraft:enchanted_count_increase", "count": {"type": "minecraft:uniform", "min": 0.0, "max": 1.0},
             "enchantment": "minecraft:looting"}]}]})
        wjson(p, d)


if __name__ == '__main__':
    textures()
    models()
    loot()
    recipes()
    worldgen()
    tags()
    station_recipes()
    creature_drops()
    print('resources generated')
