"""Generates the assets and data for mining (package com.onepiecemod.mining).

Run: python3 -I gen_mining.py <path to source/>
Writes textures, models, blockstates, item defs, names (assets/onepiece_mining/lang), block loot tables, smelting,
ore features + biome tags, tool tier tags, advancements, item descriptions, and appends to the shared tag files,
station_recipes.json and guide.json (append-only: entries already there are kept as they are).
"""
import json, os, random, sys
from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else '/mnt/project-files/one-piece-mod/source'
RES = os.path.join(SRC, 'src/main/resources')
A = os.path.join(RES, 'assets/onepiece')
D = os.path.join(RES, 'data/onepiece')
op = lambda s: 'onepiece:' + s
mc = lambda s: 'minecraft:' + s


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


# ---------------- painting ----------------

def jit(c, r, a=10):
    return tuple(max(0, min(255, int(v) + r.randint(-a, a))) for v in c[:3]) + (255,)


def save(im, kind, name):
    os.makedirs(os.path.join(A, 'textures', kind), exist_ok=True)
    im.save(os.path.join(A, 'textures', kind, name + '.png'))


def stone_base(color, seed, a=12, cracks=None):
    r = random.Random(seed)
    im = Image.new('RGBA', (16, 16))
    for x in range(16):
        for y in range(16):
            im.putpixel((x, y), jit(color, r, a))
    if cracks:
        for _ in range(5):
            x, y = r.randrange(16), r.randrange(16)
            for _ in range(r.randint(2, 5)):
                im.putpixel((x % 16, y % 16), jit(cracks, r, 5))
                x += r.choice((-1, 0, 1)); y += r.choice((0, 1))
    return im, r


def gem_ore(name, stone, dark, mid, light, seed, crystal=False):
    """Stone with 4-5 clusters of the mineral; crystal=True draws little pointed shards instead of round lumps."""
    im, r = stone_base(stone, seed, cracks=tuple(int(v * 0.75) for v in stone))
    spots = [(3, 3), (11, 2), (6, 8), (12, 10), (3, 12), (9, 14)]
    r.shuffle(spots)
    for sx, sy in spots[:5]:
        if crystal:
            shape = [(0, 0), (0, -1), (0, -2), (1, 0), (1, -1), (-1, 0)]
        else:
            shape = [(0, 0), (1, 0), (0, 1), (1, 1), (-1, 0), (0, -1)]
        for i, (dx, dy) in enumerate(shape):
            x, y = sx + dx, sy + dy
            if 0 <= x < 16 and 0 <= y < 16:
                c = light if i == (2 if crystal else 0) else (mid if i % 2 else dark)
                im.putpixel((x, y), jit(c, r, 6))
    save(im, 'block', name)


def sprite(name, rows, colors, seed):
    r = random.Random(seed)
    im = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row[:16]):
            if ch != '.':
                im.putpixel((x, y), jit(colors[ch], r, 5))
    save(im, 'item', name)


def hexc(s):
    s = s.lstrip('#')
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def shades(c):
    c = hexc(c)
    return {'a': tuple(int(v * 0.45) for v in c), 'b': c, 'c': tuple(min(255, int(v * 1.3 + 40)) for v in c)}


GEM = ["................", "................", "................", "................", "......aaaa......", ".....abccba.....",
       "....abcccbba....", "...abccbbbbba...", "...abbbbbbbba...", "....abbbbbba....", ".....abbbba.....", "......abba......",
       ".......aa.......", "................", "................", "................"]
SHARD = ["................", "................", "..........a.....", ".........aca....", "........acba....", ".......acba.....",
         "......acba......", ".....abba.......", "....abba........", "....aba.........", "...aba..........", "...aa...........",
         "................", "................", "................", "................"]
CRYSTAL = ["................", "................", ".......a........", "......aca.......", "......aca..a....", ".....abcba.aca...",
           ".....abcba.aba...", "..a..abbba.aba...", ".aca.abbba.aba...", ".abaaabbbaaaba...", ".abbbbbbbbbbba...", "..aaaaaaaaaaa....",
           "................", "................", "................", "................"]
RAW = ["................", "................", "................", ".....aaaa.......", "....abbbaa......", "...abbcbbba.....",
       "...abccbbbba....", "..abbbbbcbba....", "..abbcbbbbba....", "..aabbbbcba.....", "...aabbbbaa.....", "....aaaaaa......",
       "................", "................", "................", "................"]
INGOT = ["................", "................", "................", "................", "................", "......aaaaaa....",
         ".....abccccba...", "....abbbbbbba...", "...abbbbbbbba...", "...aaaaaaaaaa...", "................", "................",
         "................", "................", "................", "................"]
CORAL = ["................", "................", "....a.....a.....", "...aca...aca....", "...aba...aba..a.", "....aba.aba..aca",
         ".a...abbba...aba", "aca...aba...aba.", ".aba..aba..aba..", "..abbbbbbbbba...", "....abbbbba.....", "......aba.......",
         "......aba.......", ".....abbba......", "................", "................"]
CANDY = ["................", "................", "........a.......", ".......aca......", "......acbca.....", ".....acbbbca....",
         "....acbbcbbca...", "....abbcbbbba...", ".....abbbbba....", "......abbba.....", ".......dd.......", ".......dd.......",
         ".......dd.......", ".......dd.......", "................", "................"]
SCRAP = ["................", "................", "................", "....aaaaa.......", "...abbbbba......", "...abccdba..aa..",
         "...abcbdbba.aba.", "....abbbbbbbbba.", ".....aabccbbba..", "......abbbdbba..", ".....abbbbbba...", ".....aaaaaaa....",
         "................", "................", "................", "................"]
# Tools: 'h' head (a/b/c shades), 'w' wood handle (d dark, e light)
PICK = ["................", "...aaaaaaa......", "..abbbbbbbba....", ".abcccccccbba...", ".aba....dde.aa..", ".aa....dde..ba..",
        ".......dde...a..", "......dde.......", ".....dde........", "....dde.........", "...dde..........", "..dde...........",
        ".dde............", ".dd.............", "................", "................"]
AXE = ["................", "......aaa.......", ".....abbba......", "....abccbbda....", "....abcbbdea....", "....abbbdeaa....",
       ".....aadea......", "......dde.......", ".....dde........", "....dde.........", "...dde..........", "..dde...........",
       ".dde............", ".dd.............", "................", "................"]
SHOVEL = ["................", "..........aaa...", ".........abcba..", "........abcbba..", "........abbbba..", ".........abba...",
          "........dea.....", ".......dde.......", "......dde.......", ".....dde........", "....dde.........", "...dde..........",
          "..dde...........", "..dd............", "................", "................"]
BIT = ["................", "................", ".......aa.......", "......abba......", "......abca......", ".....abccba.....",
       ".....abcbba.....", "....abccbbba....", "....abcbbbba....", "...abccbbbbba...", "...ddddddddddd..", "...deeeeeeeeed..",
       "...ddddddddddd..", "......dddd......", "................", "................"]

ADAM_WOOD = {'d': (92, 60, 34), 'e': (160, 112, 64)}

# (block id, name, stone rgb, dark, mid, light, crystal?)
ISLAND_ORES = [
    ('desert_amber_ore', 'Desert Amber Ore', (196, 172, 120), (150, 80, 10), (214, 130, 30), (255, 200, 90), False),
    ('sun_coral_ore', 'Sun Coral Ore', (118, 124, 128), (190, 70, 30), (245, 130, 40), (255, 220, 120), True),
    ('rock_candy_ore', 'Rock Candy Ore', (140, 128, 136), (200, 80, 140), (240, 140, 200), (255, 220, 240), True),
    ('giant_iron_ore', 'Giant Iron Ore', (120, 120, 120), (90, 60, 50), (150, 110, 90), (210, 180, 160), False),
    ('egghead_alloy_ore', 'Egghead Alloy Ore', (128, 128, 132), (70, 90, 120), (140, 190, 230), (230, 250, 255), False),
    ('gloom_crystal_ore', 'Gloom Crystal Ore', (88, 84, 96), (60, 30, 90), (130, 70, 180), (210, 170, 255), True),
    ('electro_crystal_ore', 'Electro Crystal Ore', (122, 122, 118), (160, 130, 10), (240, 210, 40), (255, 255, 200), True),
    ('snake_jade_ore', 'Snake Jade Ore', (120, 126, 120), (20, 90, 50), (40, 170, 90), (170, 240, 190), False),
]
BLOCK_NAMES = {b: n for b, n, *_ in ISLAND_ORES}
BLOCK_NAMES.update({'sea_prism_vein': 'Sea Prism Vein', 'abyss_stone': 'Abyss Stone', 'abyss_stone_bricks': 'Abyss Stone Bricks',
                    'mining_drill': 'Mining Drill', 'ore_cart': 'Ore Cart'})
# item id -> (name, sprite, color)
MATERIALS = {
    'sea_prism_shard': ('Sea Prism Shard', SHARD, '#7fd8e8'), 'sea_prism_ingot': ('Sea Prism Ingot', INGOT, '#5fc6dc'),
    'desert_amber': ('Desert Amber', GEM, '#e09a2a'), 'sun_coral': ('Sun Coral', CORAL, '#f58a30'),
    'rock_candy': ('Rock Candy', CANDY, '#f08cc8'), 'raw_giant_iron': ('Raw Giant Iron', RAW, '#9a6c58'),
    'giant_iron_ingot': ('Giant Iron Ingot', INGOT, '#a08070'), 'egghead_alloy': ('Egghead Alloy', SCRAP, '#8cbee6'),
    'gloom_crystal': ('Gloom Crystal', CRYSTAL, '#8a50c0'), 'electro_crystal': ('Electro Crystal', CRYSTAL, '#f0d22a'),
    'snake_jade': ('Snake Jade', GEM, '#2aa860'),
}
TIERS = {'adam': ('Adam Wood', '#b07840'), 'seastone': ('Seastone', '#4a8fb0'), 'sea_prism': ('Sea Prism', '#6fd8ec')}
TOOLS = [('pickaxe', 'Pickaxe', PICK), ('axe', 'Axe', AXE), ('shovel', 'Shovel', SHOVEL)]


def textures():
    for b, _, stone, dark, mid, light, crystal in ISLAND_ORES:
        gem_ore(b, stone, dark, mid, light, sum(map(ord, b)))
    gem_ore('sea_prism_vein', (70, 72, 80), (40, 120, 150), (90, 200, 225), (210, 250, 255), 301, crystal=True)
    im, r = stone_base((34, 32, 40), 302, 6, cracks=(20, 18, 26))
    for _ in range(6):
        im.putpixel((r.randrange(16), r.randrange(16)), jit((40, 90, 110), r, 6))  # faint sea-prism glints
    save(im, 'block', 'abyss_stone')
    im, r = stone_base((38, 36, 44), 303, 5)
    for y in range(16):
        for x in range(16):
            if y % 4 == 3 or (x + (4 if (y // 4) % 2 else 0)) % 8 == 7:
                im.putpixel((x, y), jit((18, 16, 22), r, 3))
    save(im, 'block', 'abyss_stone_bricks')
    # Mining Drill: riveted iron casing, a drill bit on the front, a furnace glow when running.
    for name, lit in (('mining_drill_front', False), ('mining_drill_front_on', True)):
        im, r = stone_base((110, 110, 116), 310, 6)
        for i in range(16):
            for p in ((i, 0), (i, 15), (0, i), (15, i)):
                im.putpixel(p, jit((70, 70, 76), r, 4))
        for y in range(3, 13):
            for x in range(3, 13):
                d = abs(x - 7.5) + abs(y - 7.5)
                if d < 5.5:
                    c = (180, 120, 60) if lit and (x + y) % 3 == 0 else ((150, 150, 160) if (x * 3 + y) % 4 else (90, 90, 100))
                    im.putpixel((x, y), jit(c, r, 6))
        im.putpixel((7, 7), (40, 40, 44, 255)); im.putpixel((8, 8), (40, 40, 44, 255))
        save(im, 'block', name)
    im, r = stone_base((110, 110, 116), 311, 6)
    for i in range(16):
        for p in ((i, 0), (i, 15), (0, i), (15, i)):
            im.putpixel(p, jit((70, 70, 76), r, 4))
    for p in ((2, 2), (13, 2), (2, 13), (13, 13)):
        im.putpixel(p, (200, 200, 205, 255))
    for x in range(3, 13):
        im.putpixel((x, 7), jit((200, 150, 40), r, 6))  # Franky-style yellow stripe
        im.putpixel((x, 8), jit((40, 40, 44), r, 4))
    save(im, 'block', 'mining_drill_side')
    im, r = stone_base((96, 96, 102), 312, 6)
    for y in range(4, 12, 3):
        for x in range(4, 12):
            im.putpixel((x, y), jit((40, 40, 44), r, 4))  # vent
    save(im, 'block', 'mining_drill_top')
    # Ore Cart: wooden planks with iron bands, ore lumps on top, wheels.
    im, r = stone_base((120, 84, 50), 320, 8)
    for y in range(16):
        for x in range(16):
            if y % 5 == 4:
                im.putpixel((x, y), jit((80, 56, 34), r, 4))
            if x in (0, 15) or x in (5, 10) and y % 5 != 4:
                im.putpixel((x, y), jit((80, 80, 86), r, 4))
    save(im, 'block', 'ore_cart_side')
    im, r = stone_base((60, 58, 62), 321, 8)
    for _ in range(26):
        c = r.choice([(130, 130, 130), (220, 200, 90), (90, 200, 225), (200, 120, 60), (160, 160, 170)])
        x, y = r.randrange(1, 15), r.randrange(1, 15)
        im.putpixel((x, y), jit(c, r, 8)); im.putpixel((x + 1, y), jit(c, r, 8))
    save(im, 'block', 'ore_cart_top')
    im, r = stone_base((44, 44, 48), 322, 4)
    save(im, 'block', 'ore_cart_wheel')

    for i, (it, (_, rows, color)) in enumerate(MATERIALS.items()):
        sprite(it, rows, dict(shades(color), d=(230, 230, 230), e=(200, 200, 200)), 400 + i)
    for i, (t, (_, color)) in enumerate(TIERS.items()):
        for j, (tool, _, rows) in enumerate(TOOLS):
            sprite('%s_%s' % (t, tool), rows, dict(shades(color), **ADAM_WOOD), 500 + i * 5 + j)
        sprite('%s_drill_bit' % t, BIT, dict(shades(color), d=(70, 70, 76), e=(150, 150, 158)), 520 + i)


def models():
    simple = [b for b, *_ in ISLAND_ORES] + ['sea_prism_vein', 'abyss_stone', 'abyss_stone_bricks']
    for b in simple:
        wjson(os.path.join(A, 'blockstates', b + '.json'), {"variants": {"": {"model": "onepiece:block/" + b}}})
        wjson(os.path.join(A, 'models/block', b + '.json'), {"parent": "minecraft:block/cube_all", "textures": {"all": "onepiece:block/" + b}})
        wjson(os.path.join(A, 'items', b + '.json'), {"model": {"type": "minecraft:model", "model": "onepiece:block/" + b}})
    # Mining Drill: like a dispenser (orientable sideways, orientable_vertical up/down), front lights up when running.
    for lit in ('', '_on'):
        wjson(os.path.join(A, 'models/block/mining_drill%s.json' % lit), {"parent": "minecraft:block/orientable", "textures": {
            "front": "onepiece:block/mining_drill_front" + lit, "side": "onepiece:block/mining_drill_side",
            "top": "onepiece:block/mining_drill_top"}})
        wjson(os.path.join(A, 'models/block/mining_drill_vertical%s.json' % lit), {"parent": "minecraft:block/orientable_vertical",
              "textures": {"front": "onepiece:block/mining_drill_front" + lit, "side": "onepiece:block/mining_drill_side"}})
    rot = {'north': {}, 'east': {"y": 90}, 'south': {"y": 180}, 'west': {"y": 270}}
    variants = {}
    for lit in ('false', 'true'):
        sfx = '_on' if lit == 'true' else ''
        for f, extra in rot.items():
            variants['facing=%s,lit=%s' % (f, lit)] = dict({"model": "onepiece:block/mining_drill" + sfx}, **extra)
        variants['facing=up,lit=%s' % lit] = {"model": "onepiece:block/mining_drill_vertical" + sfx}
        variants['facing=down,lit=%s' % lit] = {"model": "onepiece:block/mining_drill_vertical" + sfx, "x": 180}
    wjson(os.path.join(A, 'blockstates/mining_drill.json'), {"variants": variants})
    wjson(os.path.join(A, 'items/mining_drill.json'), {"model": {"type": "minecraft:model", "model": "onepiece:block/mining_drill"}})
    # Ore Cart: a wagon body heaped with ore, on four wheels.
    def box(f, t, tex_side, tex_top):
        faces = {d: {"texture": "#" + (tex_top if d in ('up', 'down') else tex_side)} for d in ('north', 'south', 'east', 'west', 'up', 'down')}
        return {"from": f, "to": t, "faces": faces}
    elements = [box([1, 3, 2], [15, 12, 14], 'side', 'top')]
    for x in (2, 11):
        for z in (2, 11):
            elements.append(box([x, 0, z], [x + 3, 3, z + 3], 'wheel', 'wheel'))
    wjson(os.path.join(A, 'models/block/ore_cart.json'), {"parent": "minecraft:block/block", "textures": {
        "particle": "onepiece:block/ore_cart_side", "side": "onepiece:block/ore_cart_side", "top": "onepiece:block/ore_cart_top",
        "wheel": "onepiece:block/ore_cart_wheel"}, "elements": elements})
    wjson(os.path.join(A, 'blockstates/ore_cart.json'), {"variants": {'facing=' + f: dict({"model": "onepiece:block/ore_cart"}, **e)
                                                                      for f, e in rot.items()}})
    wjson(os.path.join(A, 'items/ore_cart.json'), {"model": {"type": "minecraft:model", "model": "onepiece:block/ore_cart"}})

    items = list(MATERIALS) + ['%s_%s' % (t, tool) for t in TIERS for tool, _, _ in TOOLS] + ['%s_drill_bit' % t for t in TIERS]
    for i in items:
        parent = 'minecraft:item/handheld' if any(i.endswith(t) for t in ('_pickaxe', '_axe', '_shovel')) else 'minecraft:item/generated'
        wjson(os.path.join(A, 'models/item', i + '.json'), {"parent": parent, "textures": {"layer0": "onepiece:item/" + i}})
        wjson(os.path.join(A, 'items', i + '.json'), {"model": {"type": "minecraft:model", "model": "onepiece:item/" + i}})
    lang = {'block.onepiece.' + b: n for b, n in BLOCK_NAMES.items()}
    lang.update({'item.onepiece.' + i: n for i, (n, _, _) in MATERIALS.items()})
    for t, (tn, _) in TIERS.items():
        for tool, toolname, _ in TOOLS:
            lang['item.onepiece.%s_%s' % (t, tool)] = '%s %s' % (tn, toolname)
        lang['item.onepiece.%s_drill_bit' % t] = '%s Drill Bit' % tn.replace(' Wood', '')
    lang['itemGroup.onepiece.mining'] = 'One Piece: Mining'
    for aid, (title, desc) in ADVANCEMENTS_TEXT.items():
        lang['advancements.onepiece.wonders.%s.title' % aid] = title
        lang['advancements.onepiece.wonders.%s.description' % aid] = desc
    wjson(os.path.join(RES, 'assets/onepiece_mining/lang/en_us.json'), lang)


DROPS = {  # block -> (item, min, max)
    'desert_amber_ore': ('desert_amber', 1, 2), 'sun_coral_ore': ('sun_coral', 1, 3), 'rock_candy_ore': ('rock_candy', 2, 4),
    'giant_iron_ore': ('raw_giant_iron', 1, 1), 'egghead_alloy_ore': ('egghead_alloy', 1, 2), 'gloom_crystal_ore': ('gloom_crystal', 1, 2),
    'electro_crystal_ore': ('electro_crystal', 1, 3), 'snake_jade_ore': ('snake_jade', 1, 1), 'sea_prism_vein': ('sea_prism_shard', 1, 2),
}


def loot():
    def ore_loot(b, drop, lo, hi):
        mods = []
        if (lo, hi) != (1, 1):
            mods.append({"type": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": lo, "max": hi}})
        mods += [{"type": "minecraft:apply_bonus", "enchantment": "minecraft:fortune", "formula": "minecraft:ore_drops"},
                 {"type": "minecraft:explosion_decay"}]
        return {"type": "minecraft:block", "pools": [{"rolls": 1, "entries": [{"type": "minecraft:alternatives", "children": [
            {"type": "minecraft:item", "condition": "minecraft:tool/can_silk_touch", "name": op(b)},
            {"type": "minecraft:item", "name": op(drop), "modifier": mods}]}]}], "random_sequence": "onepiece:blocks/" + b}

    def self_loot(b):
        return {"type": "minecraft:block", "pools": [{"rolls": 1, "entries": [{"type": "minecraft:item", "name": op(b)}],
                "condition": {"type": "minecraft:survives_explosion"}}], "random_sequence": "onepiece:blocks/" + b}
    for b, (drop, lo, hi) in DROPS.items():
        wjson(os.path.join(D, 'loot_table/blocks', b + '.json'), ore_loot(b, drop, lo, hi))
    for b in ('abyss_stone', 'abyss_stone_bricks', 'mining_drill', 'ore_cart'):
        wjson(os.path.join(D, 'loot_table/blocks', b + '.json'), self_loot(b))


def recipes():
    R = os.path.join(D, 'recipe')
    for kind, t in (('smelting', 200), ('blasting', 100)):
        wjson(os.path.join(R, 'giant_iron_ingot_from_%s.json' % kind), {"type": "minecraft:" + kind, "cookingtime": t,
              "experience": 0.8, "group": "giant_iron_ingot", "ingredient": op('raw_giant_iron'), "result": {"id": op('giant_iron_ingot')}})
    for gem, n in (('desert_amber', 6), ('snake_jade', 8)):
        wjson(os.path.join(R, 'berry_from_%s.json' % gem), {"type": "minecraft:crafting_shapeless", "category": "misc",
              "ingredients": [op(gem)], "result": {"count": n, "id": op('berry')}})
    wjson(os.path.join(R, 'abyss_stone_bricks.json'), {"type": "minecraft:crafting_shaped", "category": "building",
          "pattern": ["##", "##"], "key": {"#": op('abyss_stone')}, "result": {"count": 4, "id": op('abyss_stone_bricks')}})


STONE = {"predicate_type": "minecraft:tag_match", "tag": "minecraft:stone_ore_replaceables"}
DEEP = {"predicate_type": "minecraft:tag_match", "tag": "minecraft:deepslate_ore_replaceables"}


def match(block):
    return {"predicate_type": "minecraft:block_match", "block": block}


def ore_feature(name, targets, size, count, lo, hi, biomes, discard=0.0):
    wjson(os.path.join(D, 'worldgen/feature/ore_%s.json' % name), {"type": "minecraft:ore",
          "discard_chance_on_air_exposure": discard, "size": size,
          "targets": [{"state": s, "target": t} for s, t in targets]})
    wjson(os.path.join(D, 'worldgen/placed_feature/ore_%s.json' % name), {"feature": "onepiece:ore_" + name, "placement": [
        {"type": "minecraft:count", "count": count}, {"type": "minecraft:in_square"},
        {"type": "minecraft:height_range", "height": {"type": "minecraft:uniform", "min_inclusive": {"absolute": lo},
                                                       "max_inclusive": {"absolute": hi}}},
        {"type": "minecraft:biome"}]})
    wjson(os.path.join(D, 'tags/worldgen/biome/has_ore_%s.json' % name), {"replace": False, "values": biomes})


def worldgen():
    ore_feature('sea_prism_vein', [(op('sea_prism_vein'), DEEP)], 4, 3, -64, -32, ['#minecraft:is_overworld'], 0.3)
    ore_feature('desert_amber', [(op('desert_amber_ore'), STONE), (op('desert_amber_ore'), match('minecraft:sandstone'))],
                7, 10, 0, 110, ['onepiece:alabasta'])
    ore_feature('sun_coral', [(op('sun_coral_ore'), STONE), (op('sun_coral_ore'), DEEP)], 6, 10, -24, 70, ['onepiece:fishman_reef'])
    ore_feature('rock_candy', [(op('rock_candy_ore'), STONE)], 8, 12, 0, 120, ['onepiece:whole_cake', 'onepiece:cacao_island'])
    ore_feature('giant_iron', [(op('giant_iron_ore'), STONE), (op('giant_iron_ore'), DEEP)], 9, 10, -24, 130,
                ['onepiece:elbaph', 'onepiece:little_garden'])
    ore_feature('egghead_alloy', [(op('egghead_alloy_ore'), STONE), (op('egghead_alloy_ore'), DEEP)], 5, 8, -24, 100, ['onepiece:egghead'])
    ore_feature('gloom_crystal', [(op('gloom_crystal_ore'), STONE), (op('gloom_crystal_ore'), DEEP)], 6, 10, -24, 100,
                ['onepiece:thriller_bark', 'onepiece:kuraigana'])
    ore_feature('electro_crystal', [(op('electro_crystal_ore'), STONE)], 6, 10, 0, 150, ['onepiece:zou'])
    ore_feature('snake_jade', [(op('snake_jade_ore'), STONE)], 6, 8, 0, 110, ['onepiece:amazon_lily'])
    # Wano exports seastone, and Impel Down is built of it: much richer seastone veins there.
    ore_feature('rich_seastone', [(op('seastone_ore'), STONE), (op('deepslate_seastone_ore'), DEEP)], 8, 8, -48, 72,
                ['onepiece:wano', 'onepiece:kuri', 'onepiece:onigashima', 'onepiece:impel_down_blazing_hell',
                 'onepiece:impel_down_freezing_hell'])


def tags():
    T = os.path.join(RES, 'data/minecraft/tags/block')
    ores = [op(b) for b, *_ in ISLAND_ORES] + [op('sea_prism_vein')]
    append_tag(os.path.join(T, 'mineable/pickaxe.json'), ores + [op('abyss_stone'), op('abyss_stone_bricks'), op('mining_drill')])
    append_tag(os.path.join(T, 'mineable/axe.json'), [op('ore_cart')])
    append_tag(os.path.join(T, 'needs_iron_tool.json'), [op(b) for b, *_ in ISLAND_ORES] + [op('mining_drill')])
    wjson(os.path.join(D, 'tags/block/needs_seastone_tool.json'), {"replace": False, "values": [op('sea_prism_vein')]})
    wjson(os.path.join(D, 'tags/block/needs_sea_prism_tool.json'), {"replace": False, "values": [op('abyss_stone'), op('abyss_stone_bricks')]})
    wjson(os.path.join(D, 'tags/block/incorrect_for_adam_tool.json'), {"replace": False, "values": [
        "#minecraft:needs_diamond_tool", "#onepiece:needs_seastone_tool", "#onepiece:needs_sea_prism_tool"]})
    wjson(os.path.join(D, 'tags/block/incorrect_for_seastone_tool.json'), {"replace": False, "values": ["#onepiece:needs_sea_prism_tool"]})
    wjson(os.path.join(D, 'tags/block/incorrect_for_sea_prism_tool.json'), {"replace": False, "values": []})
    # Vanilla tools: diamond can't cut sea prism veins, nothing but Sea Prism cuts Abyss Stone.
    for t in ('wooden', 'stone', 'copper', 'gold', 'iron', 'diamond'):
        append_tag(os.path.join(T, 'incorrect_for_%s_tool.json' % t), ["#onepiece:needs_seastone_tool", "#onepiece:needs_sea_prism_tool"])
    append_tag(os.path.join(T, 'incorrect_for_netherite_tool.json'), ["#onepiece:needs_sea_prism_tool"])
    I = os.path.join(RES, 'data/minecraft/tags/item')
    for tool in ('pickaxe', 'axe', 'shovel'):
        append_tag(os.path.join(I, tool + 's.json'), [op('%s_%s' % (t, tool)) for t in TIERS])
    wjson(os.path.join(D, 'tags/item/repairs_adam_tool.json'), {"values": [op('adam_planks')]})
    wjson(os.path.join(D, 'tags/item/repairs_seastone_tool.json'), {"values": [op('seastone_ingot')]})
    wjson(os.path.join(D, 'tags/item/repairs_sea_prism_tool.json'), {"values": [op('sea_prism_ingot')]})
    wjson(os.path.join(D, 'tags/item/mined_materials.json'), {"replace": False, "values": [op(i) for i in MATERIALS]
          + [op('raw_seastone'), op('sulfur'), op('raw_tamahagane'), op('raw_wapometal'), op('raw_shandora_gold'), op('raw_kokuto'),
             mc('flint'), mc('coal'), mc('diamond'), mc('emerald'), mc('redstone'), mc('lapis_lazuli'), mc('raw_iron'),
             mc('raw_gold'), mc('raw_copper'), mc('amethyst_shard'), mc('quartz'), mc('bone')]})
    # Common tags, so other mods (and the Gloom Crystal) know these are ores.
    append_tag(os.path.join(RES, 'data/c/tags/block/ores.json'), ores + [op('seastone_ore'), op('deepslate_seastone_ore'),
               op('tamahagane_ore'), op('deepslate_tamahagane_ore'), op('wapometal_ore'), op('deepslate_wapometal_ore'),
               op('shandora_gold_ore'), op('sulfur_ore'), op('nether_sulfur_ore'), op('deepslate_kokuto_ore')])
    append_tag(os.path.join(RES, 'data/c/tags/item/ores.json'), ores)


def station_recipes():
    path = os.path.join(RES, 'onepiece/station_recipes.json')
    recipes = json.load(open(path))
    ids = {r['id'] for r in recipes}
    planks = {"tag": "minecraft:planks", "icon": "minecraft:oak_planks", "name": "Any Planks", "count": 2}

    def add(rid, station, result, count, ingredients, requires=None):
        r = {"id": rid, "station": station, "result": result, "count": count,
             "ingredients": [i if isinstance(i, dict) else {"item": i[0], "count": i[1]} for i in ingredients]}
        if requires:
            r["requires"] = requires
        if rid not in ids:
            recipes.append(r)
            ids.add(rid)
    add('mining_drill', 'shipwright_bench', op('mining_drill'), 1,
        [(mc('iron_ingot'), 8), (mc('piston'), 1), (mc('furnace'), 1), (mc('redstone'), 4)])
    add('ore_cart', 'shipwright_bench', op('ore_cart'), 1, [(mc('iron_ingot'), 3), (mc('chest'), 1), planks])
    add('adam_drill_bit', 'shipwright_bench', op('adam_drill_bit'), 1, [(op('adam_planks'), 2), (mc('iron_ingot'), 3), (mc('flint'), 2)])
    add('adam_pickaxe', 'shipwright_bench', op('adam_pickaxe'), 1, [(op('adam_planks'), 3), (mc('stick'), 2), (mc('iron_nugget'), 3)])
    add('adam_axe', 'shipwright_bench', op('adam_axe'), 1, [(op('adam_planks'), 3), (mc('stick'), 2), (mc('iron_nugget'), 3)])
    add('adam_shovel', 'shipwright_bench', op('adam_shovel'), 1, [(op('adam_planks'), 1), (mc('stick'), 2), (mc('iron_nugget'), 1)])
    for tool, n in (('pickaxe', 3), ('axe', 3), ('shovel', 1)):
        add('seastone_' + tool, 'seastone_workbench', op('seastone_' + tool), 1, [(op('seastone_ingot'), n), (op('adam_log'), 1)])
    add('seastone_drill_bit', 'seastone_workbench', op('seastone_drill_bit'), 1, [(op('seastone_ingot'), 4), (op('adam_drill_bit'), 1)])
    add('sea_prism_ingot', 'seastone_workbench', op('sea_prism_ingot'), 1,
        [(op('sea_prism_shard'), 4), (op('seastone_ingot'), 2), (op('giant_iron_ingot'), 1)], {"boss": "magellan"})
    add('sea_prism_pickaxe', 'seastone_workbench', op('sea_prism_pickaxe'), 1,
        [(op('sea_prism_ingot'), 3), (op('adam_log'), 1), (op('electro_crystal'), 4)], {"boss": "magellan"})
    add('sea_prism_axe', 'seastone_workbench', op('sea_prism_axe'), 1,
        [(op('sea_prism_ingot'), 3), (op('adam_log'), 1), (op('snake_jade'), 4)], {"boss": "magellan"})
    add('sea_prism_shovel', 'seastone_workbench', op('sea_prism_shovel'), 1,
        [(op('sea_prism_ingot'), 1), (op('adam_log'), 1), (op('sun_coral'), 4)], {"boss": "magellan"})
    add('sea_prism_drill_bit', 'seastone_workbench', op('sea_prism_drill_bit'), 1,
        [(op('sea_prism_ingot'), 4), (op('seastone_drill_bit'), 1), (op('egghead_alloy'), 4)], {"boss": "magellan"})
    with open(path, 'w') as f:
        json.dump(recipes, f, indent=2)
        f.write('\n')


DESCRIPTIONS = {
    'sea_prism_vein': 'Pure sea prism deep under the islands (below y -32). Needs a Seastone pickaxe or better.',
    'abyss_stone': 'The black rock at the bottom of the deep mines. Only a Sea Prism pickaxe can cut it.',
    'abyss_stone_bricks': 'Carved Abyss Stone. Only a Sea Prism pickaxe can cut it.',
    'desert_amber_ore': 'Only found under Alabasta.', 'sun_coral_ore': 'Only found under Fishman Island. Glows.',
    'rock_candy_ore': 'Only found under Whole Cake and Cacao Island.', 'giant_iron_ore': 'Only found under Elbaph and Little Garden.',
    'egghead_alloy_ore': 'Only found under Egghead.', 'gloom_crystal_ore': 'Only found under Thriller Bark and Kuraigana.',
    'electro_crystal_ore': 'Only found under Zou.', 'snake_jade_ore': 'Only found under Amazon Lily.',
    'mining_drill': 'Fuel it, fit a bit, and it digs a 3x3 tunnel into an Ore Cart beside it. A crewmate set to Work next to it runs it.',
    'ore_cart': 'Put it beside a Mining Drill: everything the drill digs lands in here.',
    'sea_prism_shard': 'Four of these, two Seastone ingots and a Giant Iron ingot make a Sea Prism ingot (beat Magellan first).',
    'sea_prism_ingot': 'The best tool metal in the world. Makes Sea Prism tools and drill bits.',
    'desert_amber': 'Alabasta amber. Trade it for Berries, or keep it.', 'sun_coral': 'Glowing coral from Fishman Island. Goes into the Sea Prism shovel.',
    'rock_candy': 'Eat it for two minutes of Haste II.', 'raw_giant_iron': 'Smelt it into Giant Iron.',
    'giant_iron_ingot': 'The giants of Elbaph forge their weapons from it. Needed for Sea Prism.',
    'egghead_alloy': "Vegapunk's future metal. Goes into the Sea Prism drill bit.",
    'gloom_crystal': 'Use it to see which ores hide in the rock within 12 blocks, and where.',
    'electro_crystal': 'Charged like a Mink. Great drill fuel (160 blocks), and part of the Sea Prism pickaxe.',
    'snake_jade': 'Green jade of the Kuja. Trade it for Berries, or use it in the Sea Prism axe.',
    'adam_drill_bit': 'Drill bit: 32 block tunnels, 600 blocks, iron-level rock.',
    'seastone_drill_bit': 'Drill bit: 64 block tunnels, 2400 blocks, cuts Sea Prism Veins.',
    'sea_prism_drill_bit': 'Drill bit: 128 block tunnels, 9000 blocks, cuts anything (even Abyss Stone).',
}
for t, tn in (('adam', 'Adam Wood: tough as the Thousand Sunny. Iron-level mining, lasts a long time.'),
              ('seastone', 'Seastone: diamond-level, cuts Sea Prism Veins. Hits drain Devil Fruit users.'),
              ('sea_prism', 'Sea Prism: the best there is, cuts Abyss Stone. Hits drain Devil Fruit users.')):
    for tool in ('pickaxe', 'axe', 'shovel'):
        DESCRIPTIONS['%s_%s' % (t, tool)] = tn


def descriptions():
    path = os.path.join(RES, 'onepiece/item_descriptions.json')
    d = json.load(open(path))
    for k, v in DESCRIPTIONS.items():
        d.setdefault(op(k), v)
    wjson(path, d)


ADVANCEMENTS_TEXT = {
    'island_ore': ('Island Treasure', 'Mine a material found under only one island'),
    'geologist': ('Grand Line Geologist', 'Collect all eight island materials'),
    'mining_drill': ('SUPER Drill!', 'Build a Mining Drill'),
    'sea_prism_vein': ('Solid Sea', 'Mine a Sea Prism Vein deep underground'),
    'sea_prism_tools': ('Sea Prism Smith', 'Make a Sea Prism pickaxe'),
    'deep_mine': ('Level Six', 'Go down into a Seastone Deep Mine'),
}
ISLAND_ITEMS = ['desert_amber', 'sun_coral', 'rock_candy', 'raw_giant_iron', 'egghead_alloy', 'gloom_crystal', 'electro_crystal', 'snake_jade']


def advancements():
    def adv(aid, icon, criteria, parent, frame='task', xp=None, requirements=None):
        d = {"display": {"icon": {"id": icon}, "title": {"translate": "advancements.onepiece.wonders.%s.title" % aid},
                         "description": {"translate": "advancements.onepiece.wonders.%s.description" % aid},
                         "frame": frame, "show_toast": True, "announce_to_chat": True, "hidden": False},
             "criteria": criteria, "requirements": requirements or [list(criteria)], "parent": parent}
        if xp:
            d["rewards"] = {"experience": xp}
        wjson(os.path.join(D, 'advancement/wonders', aid + '.json'), d)

    def has(*items):
        return {"trigger": "minecraft:inventory_changed", "conditions": {"items": [{"items": list(items) if len(items) > 1 else items[0]}]}}
    adv('island_ore', op('snake_jade'), {"done": has(*[op(i) for i in ISLAND_ITEMS])}, 'onepiece:wonders/root')
    adv('geologist', op('electro_crystal'), {i: has(op(i)) for i in ISLAND_ITEMS}, 'onepiece:wonders/island_ore', 'challenge', 500)
    adv('mining_drill', op('mining_drill'), {"done": has(op('mining_drill'))}, 'onepiece:wonders/root', 'goal')
    adv('sea_prism_vein', op('sea_prism_shard'), {"done": has(op('sea_prism_shard'))}, 'onepiece:wonders/mining_drill')
    adv('sea_prism_tools', op('sea_prism_pickaxe'), {"done": has(op('sea_prism_pickaxe'))}, 'onepiece:wonders/sea_prism_vein', 'challenge', 300)
    adv('deep_mine', op('abyss_stone_bricks'), {"done": {"trigger": "minecraft:location", "conditions": {"player": {
        "type": "minecraft:entity_properties", "entity": "this",
        "predicate": {"minecraft:location": {"structures": "onepiece:seastone_deep_mine"}}}}}}, 'onepiece:wonders/root', 'goal')


GUIDE = {"id": "mining", "title": "Mining & Drills", "icon": "onepiece:sea_prism_pickaxe", "color": "6FD8EC", "text": [
    "# Tool tiers",
    "- Adam Wood (Shipwright's Bench): iron-level, but lasts much longer. Needs Adam planks from the rare Treasure Tree Adam.",
    "- Seastone (Seastone Workbench): diamond-level, and the only tier below Sea Prism that cuts Sea Prism Veins. Hits drain Devil Fruit users.",
    "- Sea Prism (Seastone Workbench, after you beat Magellan): the best there is. Only Sea Prism cuts Abyss Stone.",
    "> The Adam wood grips keep a Devil Fruit user safe while holding them.",
    "",
    "# Island ores",
    "Every big island hides a material found nowhere else:",
    "- Alabasta: Desert Amber. Fishman Island: Sun Coral. Whole Cake and Cacao: Rock Candy (eat it for Haste).",
    "- Elbaph and Little Garden: Giant Iron. Egghead: Egghead Alloy. Thriller Bark and Kuraigana: Gloom Crystal.",
    "- Zou: Electro Crystal (great drill fuel). Amazon Lily: Snake Jade.",
    "- Wano, Kuri and Impel Down: much richer seastone veins.",
    "- Everywhere, below y -32: Sea Prism Veins (Seastone pickaxe or better).",
    "> Crush a Gloom Crystal to see which ores hide in the rock around you.",
    "",
    "# The Mining Drill",
    "Build it at the Shipwright's Bench. Place it facing the rock (it points away from you, so look down for a shaft).",
    "- Right-click with coal, charcoal, sulfur, blaze rods, coal blocks or electro crystals to fuel it (sneak for the whole stack).",
    "- Right-click with a drill bit to fit it. Adam bits dig 32 blocks, Seastone 64, Sea Prism 128.",
    "- Put an Ore Cart (or a chest, barrel or chest minecart) right next to it: that's where everything it digs goes.",
    "- Empty hand: see how it's doing. Sneak + empty hand: switch it on or off.",
    "",
    "# Crew miners",
    "Set any crewmate to Work within 6 blocks of a drill and they become its miner: they keep it fuelled from the chests nearby, fit new bits, and haul half-full carts into the chests. While they stand by, the drill digs 40% faster.",
    "",
    "# Seastone Deep Mines",
    "Old Impel Down quarries lie deep under the Grand Line: shafts, cell blocks and ore galleries going down level by level, with jailers still on guard. The richest Sea Prism and the Abyss Stone vault are at the bottom.",
]}


def guide():
    path = os.path.join(RES, 'onepiece/guide.json')
    g = json.load(open(path))
    if not any(c['id'] == 'mining' for c in g['chapters']):
        g['chapters'].append(GUIDE)
        with open(path, 'w') as f:  # this file is tab-indented
            json.dump(g, f, indent='\t', ensure_ascii=False)
            f.write('\n')


if __name__ == '__main__':
    textures()
    models()
    loot()
    recipes()
    worldgen()
    tags()
    station_recipes()
    descriptions()
    advancements()
    guide()
    print('mining generated')
