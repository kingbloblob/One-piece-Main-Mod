"""Generates the One Piece deco blocks: Java registration, models, textures, loot, tags, recipes,
tree/flower worldgen and names. Owned by the "Building blocks and plants" thread.

Usage: python3 gen_deco.py <vanilla_dir> <out_dir>
  vanilla_dir: the 26.3 client.jar unzipped (needs assets/minecraft and data/minecraft), used only
               as JSON templates for block models/blockstates/loot (no vanilla art is copied).
  out_dir:     a scratch folder. Copy its src/ over the mod's src/ afterwards (see README in this folder).
"""
import json, os, re, sys
from collections import OrderedDict
import textures as tx

VAN = sys.argv[1]
OUT = sys.argv[2]
RES = os.path.join(OUT, 'src/main/resources')
JAVA = os.path.join(OUT, 'src/main/java/com/onepiecemod/deco')
A = os.path.join(RES, 'assets/onepiece')
D = os.path.join(RES, 'data/onepiece')

names = OrderedDict()          # id -> English name
java_blocks = []               # lines for DecoBlocks
tab_order = []                 # ids in creative tab order (blocks and items)
tags = {}                      # 'block:minecraft:logs' -> set(ids)
texture_jobs = {}              # 'block/foo' -> PIL image
strip_pairs = []               # (log, stripped)
flammable = []                 # (id, burn, spread)


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        if isinstance(data, str):
            f.write(data)
        else:
            json.dump(data, f, indent=2)
            f.write('\n')


def vread(rel):
    with open(os.path.join(VAN, rel)) as f:
        return f.read()


def tag(kind, name, *ids):
    tags.setdefault(f'{kind}:{name}', []).extend(i if ':' in i or i.startswith('#') else 'onepiece:' + i for i in ids)


def title(i):
    return ' '.join(w.capitalize() for w in i.split('_'))


def const(i):
    return i.upper()


def clone(files, subs, extra_rename=None):
    """Copies vanilla JSON templates, renaming them with regex substitutions."""
    for rel in files:
        text = vread(rel)
        for pat, rep in subs:
            text = re.sub(pat, rep, text)
        out = rel
        for pat, rep in (extra_rename or subs):
            out = re.sub(pat, rep, out)
        out = out.replace('assets/minecraft/', 'assets/onepiece/').replace('data/minecraft/', 'data/onepiece/')
        out = out.replace('onepiece:', '').replace('block/onepiece', 'block/')
        write(os.path.join(RES, out), text)


def simple_loot(i):
    write(f'{D}/loot_table/blocks/{i}.json', {
        "type": "minecraft:block",
        "pools": [{"rolls": 1, "bonus_rolls": 0, "entries": [{"type": "minecraft:item", "name": f"onepiece:{i}"}],
                   "condition": {"type": "minecraft:survives_explosion"}}],
        "random_sequence": f"onepiece:blocks/{i}"})


def item_model_block(i, model=None):
    write(f'{A}/items/{i}.json', {"model": {"type": "minecraft:model", "model": model or f"onepiece:block/{i}"}})


def item_model_flat(i, texture=None):
    write(f'{A}/models/item/{i}.json', {"parent": "minecraft:item/generated", "textures": {"layer0": texture or f"onepiece:item/{i}"}})
    write(f'{A}/items/{i}.json', {"model": {"type": "minecraft:model", "model": f"onepiece:item/{i}"}})


# =====================================================================================================
# Wood sets
# =====================================================================================================

WOODS = [
    dict(id='sakura', name='Sakura', bark='#4f3030', wood='#d79a8c', leaf='#f2a7c6', blossom='#fde0ec',
         set='CHERRY', type='CHERRY', particle='ParticleTypes.CHERRY_LEAVES', feature='cherry',
         sapling_recipe=['minecraft:oak_sapling', 'minecraft:pink_dye']),
    dict(id='yarukiman', name='Yarukiman Mangrove', bark='#8f8a76', wood='#d8cca6', leaf='#5f9c55', blossom='#a6d39a',
         set='MANGROVE', type='MANGROVE', particle='ColorParticleOption.create(ParticleTypes.TINTED_LEAVES, 0xFF5F9C55)',
         feature='tall_mangrove', extra_drop=('bubble_resin', 0.1),
         sapling_recipe=['minecraft:oak_sapling', 'minecraft:slime_ball']),
    dict(id='palm', name='Palm', bark='#8a6a3c', wood='#d9b97d', leaf='#4c9a3a', blossom='#6fbf4d',
         set='JUNGLE', type='JUNGLE', particle='ColorParticleOption.create(ParticleTypes.TINTED_LEAVES, 0xFF4C9A3A)',
         feature=None, extra_drop=('coconut', 0.08), sand=True,
         sapling_recipe=['minecraft:jungle_sapling', 'minecraft:sand']),
    dict(id='gloom', name='Gloom', bark='#3a3440', wood='#6c6077', leaf='#3d3047', blossom='#5c2f61',
         set='PALE_OAK', type='PALE_OAK', particle='ParticleTypes.PALE_OAK_LEAVES', feature='dark_oak',
         sapling_recipe=['minecraft:dark_oak_sapling', 'minecraft:black_dye']),
]
WOOD_PARTS = ['log', 'wood', 'stripped_log', 'stripped_wood', 'planks', 'stairs', 'slab', 'fence', 'fence_gate',
              'door', 'trapdoor', 'button', 'pressure_plate', 'leaves', 'sapling']
ADAM_PARTS = ['stairs', 'slab', 'fence', 'fence_gate', 'door', 'trapdoor', 'button', 'pressure_plate']


def part_id(w, p):
    return f'stripped_{w}_{p[9:]}' if p.startswith('stripped_') else f'{w}_{p}'


def wood_files(parts):
    files = []
    for p in parts:
        vid = part_id('cherry', p)
        files.append(f'assets/minecraft/blockstates/{vid}.json')
        files.append(f'assets/minecraft/items/{vid}.json')
        files.append(f'data/minecraft/loot_table/blocks/{vid}.json')
        for f in os.listdir(os.path.join(VAN, 'assets/minecraft/models/block')):
            stem = f[:-5]
            if stem == vid or (stem.startswith(vid + '_') and not any(
                    stem.startswith(part_id('cherry', q)) for q in WOOD_PARTS if len(part_id('cherry', q)) > len(vid))):
                files.append(f'assets/minecraft/models/block/{f}')
        if os.path.exists(os.path.join(VAN, f'assets/minecraft/models/item/{vid}.json')):
            files.append(f'assets/minecraft/models/item/{vid}.json')
        if p not in ('log', 'stripped_log', 'leaves', 'sapling') and os.path.exists(os.path.join(VAN, f'data/minecraft/recipe/{vid}.json')):
            files.append(f'data/minecraft/recipe/{vid}.json')
    return files


def wood_subs(w):
    return [(r'minecraft:(block/|item/|blocks/|recipe/)?(stripped_)?cherry_', rf'onepiece:\1\2{w}_'),
            (r'(stripped_)?cherry_', rf'\1{w}_')]


java_blocks.append('\t// ---- Wood sets: Sakura (Wano), Yarukiman Mangrove (Sabaody), Palm (beaches), Gloom (Thriller Bark) ----')
for W in WOODS:
    w = W['id']
    subs = wood_subs(w)
    clone(wood_files(WOOD_PARTS), subs[:1], subs[1:])
    planks = const(w + '_planks')
    java_blocks.append('')
    java_blocks.append(f'\tpublic static final Block {const(w)}_LOG = log("{w}_log", Blocks.CHERRY_LOG);')
    java_blocks.append(f'\tpublic static final Block {const(w)}_WOOD = log("{w}_wood", Blocks.CHERRY_WOOD);')
    java_blocks.append(f'\tpublic static final Block STRIPPED_{const(w)}_LOG = log("stripped_{w}_log", Blocks.STRIPPED_CHERRY_LOG);')
    java_blocks.append(f'\tpublic static final Block STRIPPED_{const(w)}_WOOD = log("stripped_{w}_wood", Blocks.STRIPPED_CHERRY_LOG);')
    java_blocks.append(f'\tpublic static final Block {planks} = cube("{w}_planks", Blocks.OAK_PLANKS);')
    java_blocks.append(f'\tpublic static final Block {const(w)}_STAIRS = stairs("{w}_stairs", {planks});')
    java_blocks.append(f'\tpublic static final Block {const(w)}_SLAB = slab("{w}_slab", {planks});')
    java_blocks.append(f'\tpublic static final Block {const(w)}_FENCE = fence("{w}_fence", {planks});')
    java_blocks.append(f'\tpublic static final Block {const(w)}_FENCE_GATE = fenceGate("{w}_fence_gate", {planks}, WoodType.{W["type"]});')
    java_blocks.append(f'\tpublic static final Block {const(w)}_DOOR = door("{w}_door", BlockSetType.{W["set"]});')
    java_blocks.append(f'\tpublic static final Block {const(w)}_TRAPDOOR = trapdoor("{w}_trapdoor", BlockSetType.{W["set"]});')
    java_blocks.append(f'\tpublic static final Block {const(w)}_BUTTON = button("{w}_button", BlockSetType.{W["set"]});')
    java_blocks.append(f'\tpublic static final Block {const(w)}_PRESSURE_PLATE = pressurePlate("{w}_pressure_plate", BlockSetType.{W["set"]});')
    java_blocks.append(f'\tpublic static final Block {const(w)}_LEAVES = leaves("{w}_leaves", {W["particle"]});')
    java_blocks.append(f'\tpublic static final Block {const(w)}_SAPLING = sapling("{w}_sapling", "{w}_tree"{", true" if W.get("sand") else ", false"});')
    ids = [part_id(w, p) for p in WOOD_PARTS]
    tab_order.extend(ids)
    nm = W['name']
    for p, i in zip(WOOD_PARTS, ids):
        names[i] = {'log': f'{nm} Log', 'wood': f'{nm} Wood', 'stripped_log': f'Stripped {nm} Log',
                    'stripped_wood': f'Stripped {nm} Wood'}.get(p, f'{nm} {title(p)}')
    strip_pairs.extend([(f'{w}_log', f'stripped_{w}_log'), (f'{w}_wood', f'stripped_{w}_wood')])
    logs = [f'{w}_log', f'{w}_wood', f'stripped_{w}_log', f'stripped_{w}_wood']
    for k in ('block', 'item'):
        tag(k, f'onepiece:{w}_logs', *logs)
        tag(k, 'minecraft:logs_that_burn', f'#onepiece:{w}_logs')
        tag(k, 'minecraft:planks', f'{w}_planks')
        tag(k, 'minecraft:wooden_stairs', f'{w}_stairs')
        tag(k, 'minecraft:wooden_slabs', f'{w}_slab')
        tag(k, 'minecraft:wooden_fences', f'{w}_fence')
        tag(k, 'minecraft:fence_gates', f'{w}_fence_gate')
        tag(k, 'minecraft:wooden_doors', f'{w}_door')
        tag(k, 'minecraft:wooden_trapdoors', f'{w}_trapdoor')
        tag(k, 'minecraft:wooden_buttons', f'{w}_button')
        tag(k, 'minecraft:wooden_pressure_plates', f'{w}_pressure_plate')
        tag(k, 'minecraft:leaves', f'{w}_leaves')
        tag(k, 'minecraft:saplings', f'{w}_sapling')
    tag('block', 'minecraft:overworld_natural_logs', f'{w}_log')
    tag('block', 'minecraft:mineable/axe', *[i for i in ids if not i.endswith(('leaves', 'sapling'))])
    tag('block', 'minecraft:mineable/hoe', f'{w}_leaves')
    for i in logs:
        flammable.append((i, 5, 5))
    for i in (f'{w}_planks', f'{w}_stairs', f'{w}_slab', f'{w}_fence', f'{w}_fence_gate'):
        flammable.append((i, 5, 20))
    flammable.append((f'{w}_leaves', 30, 60))

    # textures
    bark, wood = W['bark'], W['wood']
    texture_jobs[f'block/{w}_log'] = tx.log_side(w + 'log', bark)
    texture_jobs[f'block/{w}_log_top'] = tx.log_top(w + 'logtop', bark, wood)
    texture_jobs[f'block/stripped_{w}_log'] = tx.log_side(w + 'slog', tx.shade(wood, 0.92), tx.shade(wood, 0.8))
    texture_jobs[f'block/stripped_{w}_log_top'] = tx.log_top(w + 'slogtop', tx.shade(wood, 0.85), wood)
    texture_jobs[f'block/{w}_planks'] = tx.planks(w + 'planks', wood)
    texture_jobs[f'block/{w}_leaves'] = tx.leaves(w + 'leaves', W['leaf'], W['blossom'])
    texture_jobs[f'block/{w}_door_top'] = tx.door_half(w + 'doortop', wood, True)
    texture_jobs[f'block/{w}_door_bottom'] = tx.door_half(w + 'doorbottom', wood, False)
    texture_jobs[f'block/{w}_trapdoor'] = tx.trapdoor(w + 'trapdoor', wood)
    texture_jobs[f'item/{w}_door'] = tx.door_item(w + 'door', wood)
    texture_jobs[f'block/{w}_sapling'] = tx.palm_sapling(w) if w == 'palm' else tx.sapling(w + 'sapling', bark, W['leaf'], W['blossom'])

    # extra leaf drops (coconuts, bubble resin)
    if W.get('extra_drop'):
        item, chance = W['extra_drop']
        p = f'{D}/loot_table/blocks/{w}_leaves.json'
        loot = json.load(open(p))
        loot['pools'].append({"rolls": 1, "entries": [{"type": "minecraft:item", "name": f"onepiece:{item}"}],
                              "condition": {"type": "minecraft:all_of", "terms": [
                                  {"type": "minecraft:inverted", "term": {"type": "minecraft:any_of", "terms": ["minecraft:tool/can_shear", "minecraft:tool/can_silk_touch"]}},
                                  {"type": "minecraft:random_chance", "chance": chance}]}})
        write(p, loot)

    # sapling recipe (so you can start a grove without finding the island)
    write(f'{D}/recipe/{w}_sapling.json', {"type": "minecraft:crafting_shapeless", "category": "misc",
                                            "ingredients": W['sapling_recipe'], "result": {"id": f"onepiece:{w}_sapling"}})

# Adam extras (the planks belong to the worldgen thread's WorldBlocks)
java_blocks.append('')
java_blocks.append('\t// ---- Extra shapes for Adam wood (the log and planks are in world/WorldBlocks) ----')
subs = wood_subs('adam')
clone(wood_files(ADAM_PARTS), subs[:1], subs[1:])
java_blocks += [
    '\tpublic static final Block ADAM_STAIRS = stairs("adam_stairs", WorldBlocks.ADAM_PLANKS);',
    '\tpublic static final Block ADAM_SLAB = slab("adam_slab", WorldBlocks.ADAM_PLANKS);',
    '\tpublic static final Block ADAM_FENCE = fence("adam_fence", WorldBlocks.ADAM_PLANKS);',
    '\tpublic static final Block ADAM_FENCE_GATE = fenceGate("adam_fence_gate", WorldBlocks.ADAM_PLANKS, WoodType.OAK);',
    '\tpublic static final Block ADAM_DOOR = door("adam_door", BlockSetType.OAK);',
    '\tpublic static final Block ADAM_TRAPDOOR = trapdoor("adam_trapdoor", BlockSetType.OAK);',
    '\tpublic static final Block ADAM_BUTTON = button("adam_button", BlockSetType.OAK);',
    '\tpublic static final Block ADAM_PRESSURE_PLATE = pressurePlate("adam_pressure_plate", BlockSetType.OAK);',
]
adam_ids = [f'adam_{p}' for p in ADAM_PARTS]
tab_order.extend(adam_ids)
for p, i in zip(ADAM_PARTS, adam_ids):
    names[i] = f'Adam {title(p)}'
for k in ('block', 'item'):
    tag(k, 'minecraft:wooden_stairs', 'adam_stairs'); tag(k, 'minecraft:wooden_slabs', 'adam_slab')
    tag(k, 'minecraft:wooden_fences', 'adam_fence'); tag(k, 'minecraft:fence_gates', 'adam_fence_gate')
    tag(k, 'minecraft:wooden_doors', 'adam_door'); tag(k, 'minecraft:wooden_trapdoors', 'adam_trapdoor')
    tag(k, 'minecraft:wooden_buttons', 'adam_button'); tag(k, 'minecraft:wooden_pressure_plates', 'adam_pressure_plate')
tag('block', 'minecraft:mineable/axe', *adam_ids)
texture_jobs['block/adam_door_top'] = tx.door_half('adamdoortop', '#9c6a3e', True)
texture_jobs['block/adam_door_bottom'] = tx.door_half('adamdoorbottom', '#9c6a3e', False)
texture_jobs['block/adam_trapdoor'] = tx.trapdoor('adamtrapdoor', '#9c6a3e')
texture_jobs['item/adam_door'] = tx.door_item('adamdoor', '#9c6a3e')

# =====================================================================================================
# Building blocks: (id, name, copy-from vanilla block, mining tool, shapes, texture, recipe)
#   shapes: S = stairs, s = slab, W = wall
# =====================================================================================================

def shaped(pattern, key, count):
    return {"type": "minecraft:crafting_shaped", "category": "building", "pattern": pattern, "key": key, "result": {"count": count}}


def ring(center, outer, count=8):
    """8 of `outer` around 1 `center` -> count (like stained glass)."""
    return shaped(["###", "#X#", "###"], {"#": outer, "X": center}, count)


def square(item, count=4):
    return shaped(["##", "##"], {"#": item}, count)


BUILD = [
    # Alabasta
    ('alabasta_sandstone_bricks', 'Alabasta Sandstone Bricks', 'SANDSTONE', 'pickaxe', 'SsW',
     lambda n: tx.bricks(n, '#e3c48a', '#b3925a'), square('minecraft:sandstone')),
    ('alabasta_tiles', 'Alabasta Tiles', 'SMOOTH_SANDSTONE', 'pickaxe', 'Ss',
     lambda n: tx.tiles(n, '#e8cf98', '#d98f4a', '#a8834f'), ring('minecraft:orange_dye', 'minecraft:smooth_sandstone')),
    # Wano
    ('wano_roof_tiles', 'Wano Roof Tiles', 'DEEPSLATE_TILES', 'pickaxe', 'Ss',
     lambda n: tx.roof_tiles(n, '#3c4a63'), ring('minecraft:blue_dye', 'minecraft:stone')),
    ('wano_lacquer_planks', 'Wano Lacquer Planks', 'OAK_PLANKS', 'axe', 'Ss',
     lambda n: tx.planks(n, '#a8322b'), ring('minecraft:red_dye', '#minecraft:planks')),
    # Marines
    ('marine_bricks', 'Marine Bricks', 'STONE_BRICKS', 'pickaxe', 'SsW',
     lambda n: tx.bricks(n, '#eef0f2', '#9aa3ad', amount=0.05), ring('minecraft:white_dye', 'minecraft:stone_bricks')),
    ('marine_tiles', 'Marine Tiles', 'STONE_BRICKS', 'pickaxe', 'Ss',
     lambda n: tx.tiles(n, '#2f5d9e', '#eef0f2', '#9aa3ad'), ring('minecraft:blue_dye', 'minecraft:stone_bricks')),
    # Water 7
    ('canal_bricks', 'Water 7 Canal Bricks', 'BRICKS', 'pickaxe', 'SsW',
     lambda n: tx.bricks(n, '#c9775a', '#e2d6c3', rows=4, length=6), square('minecraft:bricks')),
    ('water7_cobbles', 'Water 7 Cobbles', 'COBBLESTONE', 'pickaxe', 'SsW',
     lambda n: tx.tiles(n, '#a69a8a', '#8f8576', '#5f574e', size=4, checker=True), ring('minecraft:sand', 'minecraft:cobblestone')),
    # Dressrosa
    ('dressrosa_mosaic', 'Dressrosa Mosaic', 'TERRACOTTA', 'pickaxe', 'Ss',
     lambda n: tx.mosaic(n, ['#e86f2c', '#f2a93b', '#3fa0c9', '#f3e6c4'], '#f3e6c4'), ring('minecraft:yellow_dye', 'minecraft:terracotta')),
    ('dressrosa_tiles', 'Dressrosa Roof Tiles', 'TERRACOTTA', 'pickaxe', 'Ss',
     lambda n: tx.roof_tiles(n, '#c8552f'), ring('minecraft:red_dye', 'minecraft:terracotta')),
    ('dressrosa_stucco', 'Dressrosa Stucco', 'SMOOTH_SANDSTONE', 'pickaxe', 'SsW',
     lambda n: tx.stone(n, '#f1e7d2', 0.04), ring('minecraft:white_dye', 'minecraft:smooth_sandstone')),
    # Fish-Man Island
    ('coral_bricks', 'Coral Bricks', 'PRISMARINE_BRICKS', 'pickaxe', 'SsW',
     lambda n: tx.bricks(n, '#e5799b', '#8e3d59', rows=4, length=8, accent='#fbd3e3'), ring('minecraft:pink_dye', 'minecraft:stone_bricks')),
    ('pearl_block', 'Pearl Block', 'QUARTZ_BLOCK', 'pickaxe', 'Ss',
     lambda n: tx.stone(n, '#f4f1ee', 0.05, specks='#d8e8f4'), ring('minecraft:white_dye', 'minecraft:diorite')),
    # Skypiea
    ('cloud_bricks', 'Cloud Bricks', 'MOSS_BLOCK', 'hoe', 'Ss',
     lambda n: tx.bricks(n, '#fbfbff', '#d6dcef', rows=2, length=8, amount=0.02), square('onepiece:island_cloud')),
    ('shandora_gold_bricks', 'Shandora Gold Bricks', 'STONE_BRICKS', 'pickaxe', 'SsW',
     lambda n: tx.bricks(n, '#e2b23a', '#8a6417', accent='#fff1a8'), ring('minecraft:gold_ingot', 'minecraft:stone_bricks')),
    ('shandian_ruin_stone', 'Shandian Ruin Stone', 'MOSSY_STONE_BRICKS', 'pickaxe', 'SsW',
     lambda n: tx.bricks(n, '#a49c84', '#6b6553', rows=2, length=16, accent='#5d8a3a'), ring('minecraft:vine', 'minecraft:stone_bricks')),
    # Drum and Punk Hazard
    ('snow_bricks', 'Snow Bricks', 'STONE_BRICKS', 'pickaxe', 'SsW',
     lambda n: tx.bricks(n, '#f3f8fc', '#b9cfe0', amount=0.03), square('minecraft:snow_block')),
    ('frozen_stone', 'Frozen Stone', 'STONE', 'pickaxe', 'SsW',
     lambda n: tx.stone(n, '#9cc7e6', 0.1, specks='#e8f6ff'), ring('minecraft:ice', 'minecraft:stone')),
    ('scorched_stone', 'Scorched Stone', 'BLACKSTONE', 'pickaxe', 'SsW',
     lambda n: tx.stone(n, '#3a2a26', 0.15, specks='#e2581d'), ring('#minecraft:coals', 'minecraft:stone')),
    # Impel Down / Enies Lobby
    ('seastone_bricks', 'Seastone Bricks', 'DEEPSLATE_BRICKS', 'pickaxe', 'SsW',
     lambda n: tx.bricks(n, '#2f6f7a', '#163a40', accent='#79c7cf'), ring('onepiece:seastone_ingot', 'minecraft:stone_bricks')),
    # Egghead
    ('lab_panel', 'Egghead Lab Panel', 'SMOOTH_STONE', 'pickaxe', 'Ss',
     lambda n: tx.panel(n, '#e8edf2', '#7d8a99'), ring('minecraft:iron_ingot', 'minecraft:smooth_stone')),
    # Whole Cake
    ('chocolate_block', 'Chocolate Block', 'PACKED_MUD', 'pickaxe', 'Ss',
     lambda n: tx.tiles(n, '#5a3420', '#5a3420', '#3c2114', size=8, checker=False), square('minecraft:cocoa_beans', 2)),
    ('cookie_bricks', 'Cookie Bricks', 'MUD_BRICKS', 'pickaxe', 'SsW',
     lambda n: tx.cookie(n), square('minecraft:cookie', 2)),
    ('frosting_block', 'Frosting Block', 'MOSS_BLOCK', 'hoe', 'Ss',
     lambda n: tx.frosting(n), square('minecraft:sugar', 1)),
]

# plain full blocks and pillars with no shapes
EXTRA_CUBES = [
    ('lab_light', 'Egghead Lab Light', 'SEA_LANTERN', None, lambda n: tx.panel(n, '#e8edf2', '#7d8a99', light='#bff4ff'),
     shaped([" # ", "#X#", " # "], {"#": "onepiece:lab_panel", "X": "minecraft:glowstone_dust"}, 4), 15),
    ('berry_block', 'Block of Berries', 'GOLD_BLOCK', 'pickaxe', lambda n: tx.coins(n),
     shaped(["###", "###", "###"], {"#": "onepiece:berry"}, 1), 0),
]
PILLARS = [
    # id, name, copy, tool, side tex, end tex, recipe
    ('alubarna_pillar', 'Alubarna Pillar', 'SANDSTONE', 'pickaxe',
     lambda n: tx.bricks(n, '#e3c48a', '#c9a76c', rows=1, length=16), lambda n: tx.stone(n, '#d8b77a', 0.05),
     shaped(["#", "#"], {"#": "onepiece:alabasta_sandstone_bricks"}, 2)),
    ('marine_pillar', 'Marine Pillar', 'QUARTZ_PILLAR', 'pickaxe',
     lambda n: tx.bricks(n, '#f2f4f6', '#3b6db3', rows=1, length=16), lambda n: tx.stone(n, '#e6e9ec', 0.03),
     shaped(["#", "#"], {"#": "onepiece:marine_bricks"}, 2)),
    ('candy_cane_block', 'Candy Cane Block', 'QUARTZ_PILLAR', 'pickaxe',
     lambda n: tx.candy_stripes(n), lambda n: tx.candy_stripes(n + 'e'),
     shaped(["RS", "SR"], {"R": "minecraft:red_dye", "S": "minecraft:sugar"}, 2)),
    ('tatami', 'Tatami Mat', 'HAY_BLOCK', 'hoe',
     lambda n: tx.tatami(n, '#b9b56a'), lambda n: tx.tatami(n + 'e', '#a9a55d'),
     square('minecraft:wheat', 2)),
    ('sake_barrel', 'Sake Barrel', 'BARREL', 'axe',
     lambda n: tx.barrel_side(n, '#b98c58', '#3a3a3a'), lambda n: tx.barrel_top(n, '#c99c66', '#e8e2d0'),
     shaped(["P", "S", "P"], {"P": "#minecraft:planks", "S": "onepiece:sake"}, 1)),
    ('cola_crate', 'Crate of Cola', 'OAK_PLANKS', 'axe',
     lambda n: tx.crate_side(n, '#8b6239', '#3a2216', '#6ab2d8'), lambda n: tx.barrel_top(n, '#8b6239'),
     shaped(["###", "###", "###"], {"#": "onepiece:cola"}, 1)),
    ('mikan_crate', 'Crate of Mikans', 'OAK_PLANKS', 'axe',
     lambda n: tx.crate_side(n, '#8b6239', '#f08a1c', '#3f8a2e'), lambda n: tx.barrel_top(n, '#8b6239'),
     shaped(["###", "###", "###"], {"#": "onepiece:mikan"}, 1)),
]


def shape_prefix(base):
    for suf, rep in (('_bricks', '_brick'), ('_tiles', '_tile'), ('_cobbles', '_cobble'), ('_planks', '')):
        if base.endswith(suf):
            return base[:-len(suf)] + rep
    if base.endswith('_block'):
        return base[:-6]
    return base


def shape_name(nm):
    words = [{'Bricks': 'Brick', 'Tiles': 'Tile', 'Cobbles': 'Cobble'}.get(x, x) for x in nm.split() if x not in ('Block', 'Planks')]
    return ' '.join(words)


def stone_family(base, prefix, shapes):
    subs = [(r'minecraft:(block/|blocks/)?stone_brick_', rf'onepiece:\1{prefix}_'),
            (r'minecraft:(block/|blocks/)?stone_bricks', rf'onepiece:\1{base}')]
    ren = [(r'stone_brick_', f'{prefix}_')]
    files = []
    for part, letter in (('stairs', 'S'), ('slab', 's'), ('wall', 'W')):
        if letter not in shapes:
            continue
        vid = f'stone_brick_{part}'
        files += [f'assets/minecraft/blockstates/{vid}.json', f'assets/minecraft/items/{vid}.json',
                  f'data/minecraft/loot_table/blocks/{vid}.json']
        files += [f'assets/minecraft/models/block/{f}' for f in os.listdir(os.path.join(VAN, 'assets/minecraft/models/block'))
                  if f.startswith(vid)]
    clone(files, subs, ren)


def cube_assets(i):
    write(f'{A}/blockstates/{i}.json', {"variants": {"": {"model": f"onepiece:block/{i}"}}})
    write(f'{A}/models/block/{i}.json', {"parent": "minecraft:block/cube_all", "textures": {"all": f"onepiece:block/{i}"}})
    item_model_block(i)
    simple_loot(i)


def pillar_assets(i):
    write(f'{A}/blockstates/{i}.json', {"variants": {
        "axis=x": {"model": f"onepiece:block/{i}_horizontal", "x": 90, "y": 90},
        "axis=y": {"model": f"onepiece:block/{i}"},
        "axis=z": {"model": f"onepiece:block/{i}_horizontal", "x": 90}}})
    t = {"end": f"onepiece:block/{i}_top", "side": f"onepiece:block/{i}"}
    write(f'{A}/models/block/{i}.json', {"parent": "minecraft:block/cube_column", "textures": t})
    write(f'{A}/models/block/{i}_horizontal.json', {"parent": "minecraft:block/cube_column_horizontal", "textures": t})
    item_model_block(i)
    simple_loot(i)


def add_recipe(i, recipe):
    recipe = json.loads(json.dumps(recipe))
    recipe['result']['id'] = f'onepiece:{i}'
    write(f'{D}/recipe/{i}.json', recipe)


def stonecut(i, base, count=1):
    write(f'{D}/recipe/{i}_from_{base}_stonecutting.json',
          {"type": "minecraft:stonecutting", "ingredient": f"onepiece:{base}", "result": {"id": f"onepiece:{i}", "count": count}})


java_blocks.append('')
java_blocks.append('\t// ---- Island building blocks ----')
for (i, nm, copy, tool, shapes, tex, recipe) in BUILD:
    c = const(i)
    java_blocks.append(f'\tpublic static final Block {c} = cube("{i}", Blocks.{copy});')
    names[i] = nm
    tab_order.append(i)
    cube_assets(i)
    texture_jobs[f'block/{i}'] = tex(i)
    add_recipe(i, recipe)
    pre = shape_prefix(i)
    stone_family(i, pre, shapes)
    shaped_ids = [i]
    stoney = tool == 'pickaxe'
    pname = shape_name(nm)
    if 'S' in shapes:
        java_blocks.append(f'\tpublic static final Block {const(pre)}_STAIRS = stairs("{pre}_stairs", {c});')
        names[f'{pre}_stairs'] = f'{pname} Stairs'
        add_recipe(f'{pre}_stairs', shaped(["#  ", "## ", "###"], {"#": f"onepiece:{i}"}, 8))
        tag('block', 'minecraft:stairs', f'{pre}_stairs'); tag('item', 'minecraft:stairs', f'{pre}_stairs')
        shaped_ids.append(f'{pre}_stairs')
        if stoney:
            stonecut(f'{pre}_stairs', i)
    if 's' in shapes:
        java_blocks.append(f'\tpublic static final Block {const(pre)}_SLAB = slab("{pre}_slab", {c});')
        names[f'{pre}_slab'] = f'{pname} Slab'
        add_recipe(f'{pre}_slab', shaped(["###"], {"#": f"onepiece:{i}"}, 6))
        tag('block', 'minecraft:slabs', f'{pre}_slab'); tag('item', 'minecraft:slabs', f'{pre}_slab')
        shaped_ids.append(f'{pre}_slab')
        if stoney:
            stonecut(f'{pre}_slab', i, 2)
    if 'W' in shapes:
        java_blocks.append(f'\tpublic static final Block {const(pre)}_WALL = wall("{pre}_wall", {c});')
        names[f'{pre}_wall'] = f'{pname} Wall'
        add_recipe(f'{pre}_wall', shaped(["###", "###"], {"#": f"onepiece:{i}"}, 6))
        tag('block', 'minecraft:walls', f'{pre}_wall'); tag('item', 'minecraft:walls', f'{pre}_wall')
        shaped_ids.append(f'{pre}_wall')
        if stoney:
            stonecut(f'{pre}_wall', i)
    tab_order.extend(shaped_ids[1:])
    if tool:
        tag('block', f'minecraft:mineable/{tool}', *shaped_ids)
    if tool == 'axe':
        for s in shaped_ids:
            flammable.append((s, 5, 20))

for (i, nm, copy, tool, tex, recipe, light) in EXTRA_CUBES:
    java_blocks.append(f'\tpublic static final Block {const(i)} = cube("{i}", Blocks.{copy}{", " + str(light) if light else ""});')
    names[i] = nm; tab_order.append(i)
    cube_assets(i); texture_jobs[f'block/{i}'] = tex(i); add_recipe(i, recipe)
    if tool:
        tag('block', f'minecraft:mineable/{tool}', i)
# berries back out of the block
write(f'{D}/recipe/berry_from_berry_block.json', {"type": "minecraft:crafting_shapeless", "category": "misc",
                                                  "ingredients": ["onepiece:berry_block"], "result": {"id": "onepiece:berry", "count": 9}})

java_blocks.append('')
java_blocks.append('\t// ---- Pillars, barrels and crates (they turn like logs) ----')
for (i, nm, copy, tool, side, end, recipe) in PILLARS:
    java_blocks.append(f'\tpublic static final Block {const(i)} = pillar("{i}", Blocks.{copy});')
    names[i] = nm; tab_order.append(i)
    pillar_assets(i)
    texture_jobs[f'block/{i}'] = side(i); texture_jobs[f'block/{i}_top'] = end(i)
    add_recipe(i, recipe)
    tag('block', f'minecraft:mineable/{tool}', i)
write(f'{D}/recipe/sake_from_sake_barrel.json', {"type": "minecraft:crafting_shapeless", "category": "misc",
                                                 "ingredients": ["onepiece:sake_barrel"], "result": {"id": "onepiece:sake", "count": 1}})
for crate, item in (('cola_crate', 'cola'), ('mikan_crate', 'mikan')):
    write(f'{D}/recipe/{item}_from_{crate}.json', {"type": "minecraft:crafting_shapeless", "category": "misc",
                                                   "ingredients": [f"onepiece:{crate}"], "result": {"id": f"onepiece:{item}", "count": 9}})

# ---- glass, panes, bars, lanterns ----
java_blocks.append('')
java_blocks.append('\t// ---- Glass, screens, bars and lanterns ----')
java_blocks += [
    '\tpublic static final Block BUBBLE_GLASS = glass("bubble_glass");',
    '\tpublic static final Block BUBBLE_GLASS_PANE = pane("bubble_glass_pane", Blocks.GLASS_PANE);',
    '\tpublic static final Block SHOJI_SCREEN = pane("shoji_screen", Blocks.GLASS_PANE);',
    '\tpublic static final Block PRISON_BARS = pane("prison_bars", Blocks.IRON_BARS);',
    '\tpublic static final Block PAPER_LANTERN = lantern("paper_lantern");',
    '\tpublic static final Block BUBBLE_LAMP = lantern("bubble_lamp");',
]
for i, nm in (('bubble_glass', 'Bubble Glass'), ('bubble_glass_pane', 'Bubble Glass Pane'), ('shoji_screen', 'Shoji Screen'),
              ('prison_bars', 'Impel Down Prison Bars'), ('paper_lantern', 'Paper Lantern'), ('bubble_lamp', 'Sabaody Bubble Lamp')):
    names[i] = nm; tab_order.append(i)
cube_assets('bubble_glass')
texture_jobs['block/bubble_glass'] = tx.glass('bubble_glass', '#cfeeff', '#bfe8ff', 70)
add_recipe('bubble_glass', ring('onepiece:bubble_resin', 'minecraft:glass'))
write(f'{D}/recipe/bubble_glass_from_slime.json', dict(ring('minecraft:slime_ball', 'minecraft:glass'), result={"id": "onepiece:bubble_glass", "count": 8}))
for i, glass_tex, top in (('bubble_glass_pane', 'onepiece:block/bubble_glass', 'onepiece:block/bubble_glass_pane_top'),
                          ('shoji_screen', 'onepiece:block/shoji_screen', 'onepiece:block/shoji_screen_pane_top')):
    files = [f'assets/minecraft/blockstates/white_stained_glass_pane.json'] + \
            [f'assets/minecraft/models/block/{f}' for f in os.listdir(os.path.join(VAN, 'assets/minecraft/models/block'))
             if f.startswith('white_stained_glass_pane_')]
    subs = [(r'minecraft:block/white_stained_glass_pane_top', top),
            (r'minecraft:block/white_stained_glass_pane_', f'onepiece:block/{i}_'),
            (r'minecraft:block/white_stained_glass', glass_tex)]
    clone(files, subs, [(r'white_stained_glass_pane', i)])
    item_model_flat(i, glass_tex)
    simple_loot(i)
texture_jobs['block/bubble_glass_pane_top'] = tx.pane_top('#cfeeff')
texture_jobs['block/shoji_screen'] = tx.shoji('shoji')
texture_jobs['block/shoji_screen_pane_top'] = tx.pane_top('#7b5532')
add_recipe('bubble_glass_pane', shaped(["###", "###"], {"#": "onepiece:bubble_glass"}, 16))
add_recipe('shoji_screen', shaped(["SPS", "SPS"], {"S": "minecraft:stick", "P": "minecraft:paper"}, 8))
# prison bars from the vanilla iron bars templates
files = ['assets/minecraft/blockstates/iron_bars.json', 'assets/minecraft/items/iron_bars.json'] + \
        [f'assets/minecraft/models/block/{f}' for f in os.listdir(os.path.join(VAN, 'assets/minecraft/models/block')) if f.startswith('iron_bars')]
if os.path.exists(os.path.join(VAN, 'assets/minecraft/models/item/iron_bars.json')):
    files.append('assets/minecraft/models/item/iron_bars.json')
clone(files, [(r'minecraft:(block/|item/)?iron_bars', r'onepiece:\1prison_bars')], [(r'iron_bars', 'prison_bars')])
simple_loot('prison_bars')
texture_jobs['block/prison_bars'] = tx.bars('prison_bars', '#3f4a52')
add_recipe('prison_bars', ring('minecraft:black_dye', 'minecraft:iron_bars'))
tag('block', 'minecraft:mineable/pickaxe', 'prison_bars', 'paper_lantern', 'bubble_lamp')
tag('block', 'minecraft:mineable/axe', 'shoji_screen')
# lanterns from the vanilla lantern model (texture drawn to fit its layout)
for i, body, frame, glow, recipe in (
        ('paper_lantern', '#c23b2b', '#2b2b2b', '#f6d48a', shaped(["S", "P", "T"], {"S": "minecraft:string", "P": "minecraft:paper", "T": "minecraft:torch"}, 1)),
        ('bubble_lamp', '#d9f2ff', '#8a6a3c', '#e9fbff', shaped(["S", "B", "T"], {"S": "minecraft:string", "B": "onepiece:bubble_glass", "T": "minecraft:torch"}, 2))):
    files = ['assets/minecraft/blockstates/lantern.json', 'assets/minecraft/models/block/lantern.json',
             'assets/minecraft/models/block/lantern_hanging.json', 'data/minecraft/loot_table/blocks/lantern.json']
    clone(files, [(r'minecraft:(block/|item/|blocks/)?lantern', rf'onepiece:\1{i}')], [(r'lantern', i)])
    item_model_flat(i)
    texture_jobs[f'block/{i}'] = tx.lantern(i, body, frame, glow)
    texture_jobs[f'item/{i}'] = tx.lantern_item(texture_jobs[f'block/{i}'])
    add_recipe(i, recipe)

# =====================================================================================================
# Plants
# =====================================================================================================

FLOWERS = [
    # id, name, petal, center, effect, seconds, light, recipe dye output
    ('cloud_puff', 'Cloud Puff', '#ffffff', '#dfe7f7', 'SLOW_FALLING', 7, 0, 'minecraft:white_dye'),
    ('sky_lotus', 'Sky Lotus', '#f6a8cf', '#f2d43c', 'JUMP_BOOST', 7, 0, 'minecraft:pink_dye'),
    ('fire_lily', 'Fire Lily', '#ff6a1f', '#ffd23f', 'FIRE_RESISTANCE', 5, 10, 'minecraft:orange_dye'),
    ('frost_bloom', 'Frost Bloom', '#9fdcff', '#ffffff', 'SLOWNESS', 5, 4, 'minecraft:light_blue_dye'),
    ('snow_lily', 'Drum Snow Lily', '#f4f8ff', '#ffcf3f', 'REGENERATION', 4, 0, 'minecraft:white_dye'),
    ('ghost_mushroom', 'Ghost Mushroom', '#7d5aa6', '#c9f2ff', 'NIGHT_VISION', 5, 7, 'minecraft:purple_dye'),
    ('desert_bloom', 'Desert Bloom', '#e8465a', '#f2c522', 'SATURATION', 1, 0, 'minecraft:red_dye'),
    ('candy_cane_sprout', 'Candy Cane Sprout', None, None, 'SPEED', 5, 0, 'minecraft:red_dye'),
    ('lollipop_flower', 'Lollipop Flower', None, None, 'SPEED', 5, 0, 'minecraft:magenta_dye'),
]
TALL = [
    ('amazon_flower', 'Amazon Jungle Flower', '#2f7d32', '#3f9a3a', '#e8467c', 'minecraft:pink_dye'),
    ('giant_fern', 'Little Garden Giant Fern', '#2f6a2a', '#4e9a3a', None, None),
]

java_blocks.append('')
java_blocks.append('\t// ---- Flowers and plants. Flowers grow on grass, sand, snow, stone and Island Cloud (tag onepiece:deco_plant_soil). ----')
for (i, nm, petal, center, effect, secs, light, dye) in FLOWERS:
    java_blocks.append(f'\tpublic static final Block {const(i)} = flower("{i}", MobEffects.{effect}, {secs}, {light});')
    names[i] = nm; tab_order.append(i)
    clone(['assets/minecraft/blockstates/poppy.json', 'assets/minecraft/models/block/poppy.json', 'data/minecraft/loot_table/blocks/poppy.json'],
          [(r'minecraft:(block/|item/|blocks/)?poppy', rf'onepiece:\1{i}')], [(r'poppy', i)])
    item_model_flat(i, f'onepiece:block/{i}')
    if i == 'sky_lotus':
        img = tx.lotus(i, petal, '#5aa04a')
    elif i == 'cloud_puff':
        img = tx.puff(i, petal)
    elif i == 'ghost_mushroom':
        img = tx.mushroom(i, petal, center)
    elif i == 'candy_cane_sprout':
        img = tx.candy_sprout(i)
    elif i == 'lollipop_flower':
        img = tx.lollipop(i)
    else:
        img = tx.flower(i, petal, center, glow=light > 0)
    texture_jobs[f'block/{i}'] = img
    write(f'{D}/recipe/{dye.split(":")[1]}_from_{i}.json', {"type": "minecraft:crafting_shapeless", "category": "misc",
                                                            "ingredients": [f"onepiece:{i}"], "result": {"id": dye, "count": 1}})
    for k in ('block', 'item'):
        tag(k, 'minecraft:small_flowers', i)
for (i, nm, stem, leaf, bloom, dye) in TALL:
    java_blocks.append(f'\tpublic static final Block {const(i)} = tallPlant("{i}");')
    names[i] = nm; tab_order.append(i)
    clone(['assets/minecraft/blockstates/rose_bush.json', 'assets/minecraft/models/block/rose_bush_bottom.json',
           'assets/minecraft/models/block/rose_bush_top.json', 'data/minecraft/loot_table/blocks/rose_bush.json'],
          [(r'minecraft:(block/|item/|blocks/)?rose_bush', rf'onepiece:\1{i}')], [(r'rose_bush', i)])
    item_model_flat(i, f'onepiece:block/{i}_top')
    texture_jobs[f'block/{i}_bottom'] = tx.tall_bottom(i + 'b', stem, leaf)
    texture_jobs[f'block/{i}_top'] = tx.tall_top(i + 't', stem, leaf, bloom)
    if dye:
        write(f'{D}/recipe/{dye.split(":")[1]}_from_{i}.json', {"type": "minecraft:crafting_shapeless", "category": "misc",
                                                                "ingredients": [f"onepiece:{i}"], "result": {"id": dye, "count": 2}})
    tag('block', 'minecraft:flowers' if bloom else 'minecraft:replaceable_by_trees', i)
    if bloom:
        tag('item', 'minecraft:flowers', i)
# plant recipes, so players can grow them anywhere
PLANT_RECIPES = {
    'cloud_puff': ['minecraft:oxeye_daisy', 'onepiece:island_cloud'],
    'sky_lotus': ['minecraft:lily_pad', 'minecraft:pink_dye'],
    'fire_lily': ['minecraft:orange_tulip', 'minecraft:blaze_powder'],
    'frost_bloom': ['minecraft:blue_orchid', 'minecraft:snowball'],
    'snow_lily': ['minecraft:lily_of_the_valley', 'minecraft:snowball'],
    'ghost_mushroom': ['minecraft:brown_mushroom', 'minecraft:glow_berries'],
    'desert_bloom': ['minecraft:cactus', 'minecraft:red_dye'],
    'candy_cane_sprout': ['minecraft:sugar_cane', 'minecraft:red_dye'],
    'lollipop_flower': ['minecraft:allium', 'minecraft:sugar'],
    'amazon_flower': ['minecraft:peony', 'minecraft:vine'],
    'giant_fern': ['minecraft:large_fern', 'minecraft:bone_meal'],
    'sakura_petals': ['minecraft:pink_petals', 'minecraft:white_dye'],
}
for i, ing in PLANT_RECIPES.items():
    write(f'{D}/recipe/{i}.json', {"type": "minecraft:crafting_shapeless", "category": "misc", "ingredients": ing,
                                   "result": {"id": f"onepiece:{i}", "count": 2}})

# sakura petals (ground cover like pink petals)
java_blocks.append('\tpublic static final Block SAKURA_PETALS = petals("sakura_petals");')
names['sakura_petals'] = 'Sakura Petals'; tab_order.append('sakura_petals')
files = ['assets/minecraft/blockstates/pink_petals.json', 'data/minecraft/loot_table/blocks/pink_petals.json'] + \
        [f'assets/minecraft/models/block/{f}' for f in os.listdir(os.path.join(VAN, 'assets/minecraft/models/block')) if f.startswith('pink_petals')]
clone(files, [(r'minecraft:(block/|item/|blocks/)?pink_petals', rf'onepiece:\1sakura_petals')], [(r'pink_petals', 'sakura_petals')])
item_model_flat('sakura_petals')
texture_jobs['block/sakura_petals'] = tx.petals('sakura_petals', '#f6b3cf')
texture_jobs['block/sakura_petals_stem'] = tx.stem('sakura_petals_stem', '#5f8a3a')
texture_jobs['item/sakura_petals'] = tx.flower('sakura_petals_item', '#f6b3cf', '#fde0ec')
for k in ('block', 'item'):
    tag(k, 'minecraft:flowers', 'sakura_petals')

# mikan bush (pick mikans like sweet berries)
java_blocks.append('\tpublic static final Block MIKAN_BUSH = registerBlockOnly("mikan_bush", MikanBushBlock::new, BlockBehaviour.Properties.ofFullCopy(Blocks.SWEET_BERRY_BUSH));')
names['mikan_bush'] = 'Mikan Bush'
clone(['assets/minecraft/blockstates/sweet_berry_bush.json'] +
      [f'assets/minecraft/models/block/sweet_berry_bush_stage{n}.json' for n in range(4)] +
      ['data/minecraft/loot_table/blocks/sweet_berry_bush.json'],
      [(r'minecraft:sweet_berries', 'onepiece:mikan'), (r'minecraft:(block/|blocks/)?sweet_berry_bush', r'onepiece:\1mikan_bush')],
      [(r'sweet_berry_bush', 'mikan_bush')])
for n in range(4):
    texture_jobs[f'block/mikan_bush_stage{n}'] = tx.bush(f'mikan{n}', n, '#3f7a2e', '#f08a1c')
tag('block', 'minecraft:replaceable_by_trees', 'mikan_bush')

# =====================================================================================================
# Food and items
# =====================================================================================================
ITEMS = [
    # id, name, texture, recipe
    ('mikan', 'Mikan', tx.blob_item('mikan', '#f2901d', '#a85a0c', leaf='#3f8a2e'), None),
    ('coconut', 'Coconut', tx.blob_item('coconut', '#7a5530', '#4a3018', shine=False), None),
    ('onigiri', 'Onigiri', tx.onigiri(), {"type": "minecraft:crafting_shapeless", "category": "misc",
                                          "ingredients": ["minecraft:wheat", "minecraft:wheat", "minecraft:dried_kelp"], "result": {"count": 2}}),
    ('dango', 'Dango', tx.dango(), {"type": "minecraft:crafting_shapeless", "category": "misc",
                                    "ingredients": ["minecraft:wheat", "minecraft:sugar", "minecraft:stick", "minecraft:pink_dye"], "result": {"count": 2}}),
    ('sake', 'Sake', tx.bottle('sake', '#d8e8e0', '#f4f1e8', '#c23b2b'), {"type": "minecraft:crafting_shapeless", "category": "misc",
                                                                          "ingredients": ["minecraft:glass_bottle", "minecraft:wheat", "minecraft:wheat", "minecraft:sugar"], "result": {"count": 1}}),
    ('cola', 'Cola', tx.bottle('cola', '#a8d8e8', '#4a1f12', '#d42a2a'), {"type": "minecraft:crafting_shapeless", "category": "misc",
                                                                          "ingredients": ["minecraft:glass_bottle", "minecraft:sugar", "minecraft:cocoa_beans"], "result": {"count": 1}}),
    ('cotton_candy', 'Cotton Candy', tx.cotton_candy(), {"type": "minecraft:crafting_shapeless", "category": "misc",
                                                         "ingredients": ["minecraft:sugar", "minecraft:sugar", "minecraft:stick"], "result": {"count": 2}}),
    ('bubble_resin', 'Bubble Resin', tx.resin(), {"type": "minecraft:crafting_shapeless", "category": "misc",
                                                  "ingredients": ["minecraft:slime_ball", "minecraft:sugar"], "result": {"count": 4}}),
]
for (i, nm, img, recipe) in ITEMS:
    names[i] = nm
    tab_order.append(i)
    item_model_flat(i)
    texture_jobs[f'item/{i}'] = img
    if recipe:
        add_recipe(i, recipe)
# =====================================================================================================
# Worldgen: trees and flower patches (added to biomes from Java via biome tags has_deco_*)
# =====================================================================================================
WG = f'{D}/worldgen'


def tree_feature(w, template):
    if template is None:  # palm: drawn by Java (com.onepiecemod.world.PalmTreeFeature): curved trunk, 8 drooping fronds
        feat = {"type": "onepiece:palm"}
        write(f'{WG}/feature/{w}_tree.json', feat)
        return
    text = vread(f'data/minecraft/worldgen/feature/{template}.json')
    van = {'cherry': 'cherry', 'tall_mangrove': 'mangrove', 'dark_oak': 'dark_oak'}[template]
    text = text.replace(f'"minecraft:{van}_log"', f'"onepiece:{w}_log"').replace(f'"minecraft:{van}_leaves"', f'"onepiece:{w}_leaves"')
    feat = json.loads(text)
    # hanging mangrove propagules only stay on vanilla mangrove leaves, so leave them out
    feat['decorators'] = [d for d in feat.get('decorators', []) if d.get('type') != 'minecraft:attached_to_leaves']
    write(f'{WG}/feature/{w}_tree.json', feat)


TREE_COUNTS = {'sakura': 3, 'yarukiman': 2, 'palm': 1, 'gloom': 3}
for W in WOODS:
    w = W['id']
    tree_feature(w, W['feature'])
    write(f'{WG}/placed_feature/deco_{w}_trees.json', {
        "feature": f"onepiece:{w}_tree",
        "placement": [
            {"type": "minecraft:count", "count": TREE_COUNTS[w]},
            {"type": "minecraft:in_square"},
            {"type": "minecraft:surface_water_depth_filter", "max_water_depth": 0},
            {"type": "minecraft:heightmap", "heightmap": "OCEAN_FLOOR"},
            {"type": "minecraft:biome"},
            {"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:would_survive", "state": f"onepiece:{w}_sapling"}}]})


def patch(name, to_place, survive_state, rarity, count=32, spread=6):
    write(f'{WG}/feature/deco_{name}.json', {"type": "minecraft:simple_block", "to_place": to_place})
    write(f'{WG}/placed_feature/deco_{name}.json', {
        "feature": f"onepiece:deco_{name}",
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
                {"type": "minecraft:would_survive", "state": survive_state}]}}]})


PATCHES = [
    # placed feature name, block, rarity
    ('sakura_petals', {"id": "onepiece:sakura_petals", "properties": {"facing": "north", "flower_amount": "4"}}, 'onepiece:sakura_petals', 1),
    ('mikan_bush', {"id": "onepiece:mikan_bush", "properties": {"age": "3"}}, 'onepiece:mikan_bush', 6),
] + [(i, {"id": f"onepiece:{i}"}, f'onepiece:{i}', 3) for (i, *_rest) in FLOWERS] + \
    [(i, {"id": f"onepiece:{i}", "properties": {"half": "lower"}}, f'onepiece:{i}', 3) for (i, *_rest) in TALL]
for (name, place, survive, rarity) in PATCHES:
    patch(name, place, survive, rarity)

# where everything grows: biome tag -> biomes (Grand Line islands plus a few normal Minecraft biomes)
BIOMES = {
    'sakura_trees': ['onepiece:wano', 'onepiece:onigashima', 'minecraft:cherry_grove'],
    'yarukiman_trees': ['onepiece:sabaody', 'minecraft:mangrove_swamp'],
    'palm_trees': ['onepiece:east_blue', 'onepiece:alabasta', 'onepiece:amazon_lily', 'onepiece:jaya', 'minecraft:beach'],
    'gloom_trees': ['onepiece:thriller_bark'],
    'sakura_petals': ['onepiece:wano', 'onepiece:onigashima'],
    'mikan_bush': ['onepiece:east_blue', 'minecraft:flower_forest'],
    'cloud_puff': ['onepiece:skypiea'],
    'sky_lotus': ['onepiece:skypiea'],
    'fire_lily': ['onepiece:punk_hazard_burning'],
    'frost_bloom': ['onepiece:punk_hazard_frozen', 'minecraft:ice_spikes'],
    'snow_lily': ['onepiece:drum_island', 'minecraft:snowy_plains'],
    'ghost_mushroom': ['onepiece:thriller_bark', 'minecraft:dark_forest'],
    'desert_bloom': ['onepiece:alabasta', 'minecraft:desert'],
    'candy_cane_sprout': ['onepiece:whole_cake'],
    'lollipop_flower': ['onepiece:whole_cake'],
    'amazon_flower': ['onepiece:amazon_lily', 'minecraft:jungle'],
    'giant_fern': ['onepiece:little_garden'],
}
for key, biomes in BIOMES.items():
    write(f'{D}/tags/worldgen/biome/has_deco_{key}.json', {"replace": False, "values": biomes})

# ground the deco flowers may grow on
write(f'{D}/tags/block/deco_plant_soil.json', {"replace": False, "values": [
    "#minecraft:dirt", "#minecraft:sand", "#minecraft:terracotta", "#minecraft:base_stone_overworld",
    "minecraft:snow_block", "minecraft:packed_ice", "minecraft:blue_ice", "minecraft:gravel",
    "minecraft:blackstone", "minecraft:basalt", "minecraft:magma_block", "onepiece:island_cloud"]})

# =====================================================================================================
# Axe stripping (26.3 keeps it as data in minecraft:block_transformer/axe; we add our logs in front)
# =====================================================================================================
axe = json.loads(vread('data/minecraft/block_transformer/axe.json'))
rules = axe[0]['block_state_provider']['rules']
mine = [{"if_true": {"type": "minecraft:matching_blocks", "blocks": f"onepiece:{a}"},
         "then": {"type": "minecraft:copy_properties", "source": {"id": f"onepiece:{b}", "properties": {"axis": "y"}}}}
        for a, b in strip_pairs]
axe[0]['block_state_provider']['rules'] = mine + rules
write(os.path.join(RES, 'data/minecraft/block_transformer/axe.json'), axe)

# =====================================================================================================
# Textures, tags, names, Java
# =====================================================================================================
for rel, img in texture_jobs.items():
    p = f'{A}/textures/{rel}.png'
    os.makedirs(os.path.dirname(p), exist_ok=True)
    img.save(p)

# every texture a model points at must exist
missing = set()
for root, _, fs in os.walk(f'{A}/models'):
    for f in fs:
        for ref in re.findall(r'"onepiece:((?:block|item)/[a-z0-9_/]+)"', open(os.path.join(root, f)).read()):
            if not os.path.exists(f'{A}/textures/{ref}.png') and not os.path.exists(f'{A}/models/{ref}.json') \
                    and ref != 'block/adam_planks':
                missing.add(ref)
if missing:
    print('MISSING TEXTURES:', sorted(missing))

for key, vals in tags.items():
    kind, full = key.split(':', 1)
    ns, path = full.split(':')
    folder = 'block' if kind == 'block' else 'item'
    write(os.path.join(RES, f'data/{ns}/tags/{folder}/{path}.json'),
          {"replace": False, "values": list(OrderedDict.fromkeys(vals))})

lang = OrderedDict()
for i, nm in names.items():
    is_item = i in [x[0] for x in ITEMS]
    lang[f'{"item" if is_item else "block"}.onepiece.{i}'] = nm
lang['itemGroup.onepiece.deco'] = 'One Piece: Building'
write(os.path.join(RES, 'assets/onepiece_deco/lang/en_us.json'), lang)

with open(os.path.join(os.path.dirname(__file__), 'DecoBlocks.java.in')) as f:
    tmpl = f.read()
tab_lines = '\n'.join(f'\t\t\t\t\toutput.accept({"DecoItems." if i in [x[0] for x in ITEMS] else "DecoBlocks."}{const(i)});' for i in tab_order)
flam = '\n'.join(f'\t\tflammable.add({const(i)}, {b}, {s});' for i, b, s in flammable)
java = tmpl.replace('%%BLOCKS%%', '\n'.join(java_blocks)).replace('%%FLAMMABLE%%', flam)
write(os.path.join(JAVA, 'DecoBlocks.java'), java)
with open(os.path.join(os.path.dirname(__file__), 'DecoFeature.java.in')) as f:
    write(os.path.join(JAVA, 'DecoFeature.java'), f.read().replace('%%TAB%%', tab_lines).replace(
        '%%BIOMES%%', '\n'.join(f'\t\taddVegetation("has_deco_{k}", "deco_{k}");' for k in BIOMES)))

# record what we own, for the README and structure swaps
write(os.path.join(OUT, 'deco-ids.json'), {"blocks": [i for i in names if i not in [x[0] for x in ITEMS]],
                                           "items": [x[0] for x in ITEMS]})
print(f'{len(names)} names, {len(texture_jobs)} textures, {len(java_blocks)} java lines')
