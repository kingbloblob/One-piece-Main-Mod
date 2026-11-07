"""Gives each Grand Line island biome the plants, ground and colours of the island it is named after (2026-10-24,
ryan: "make the biomes more immersive").

- Vanilla trees, flowers, grass and oddities (fossils, boulders, ice, bamboo, poplars, fallen logs, giant mushrooms...)
  are added to or removed from each island biome's feature list. Vanilla placed features are used as they are; trees that
  vanilla only places from inside its "trees_*" selectors get a small placed feature of our own (onepiece:flavour_*).
  Every step's list is then re-sorted into vanilla's own feature order, because Minecraft refuses to start
  ("feature order cycle") when two biomes list the same features in different orders.
- Ground patches per island (Island Cloud on Skypiea, moss on Zou, Sugar Sand on Totto Land, Volcanic Ash on Punk Hazard,
  Grave Soil on Thriller Bark...) go into the Grand Line surface rules (worldgen/material_rule/grand_line.json) as one
  sequence at the front, so they are tried before the older per-biome rules and fall through to them where they don't match.
- Grass and leaf colours for islands that still had the vanilla ones.
- The mod's own flora plants (com.onepiecemod.flora) are NOT placed here: tools/flora/gen_flora.py writes the biome tags
  has_flora_*.json and Java adds them to the biomes at runtime, like the deco plants.

Safe to rerun. The worldgen generators (gen_biomes.py, gen_boss_islands.py) rewrite biome files, so they call this after
island_look.py to put the island flavour back. Needs vanilla 26.3 data for the feature order: pass it as the second argument
or in $VANILLA (a folder with data/minecraft/worldgen/biome/*.json); without it, the order from tools/islands/feature_order.json is used.

Usage: python3 island_flavour.py [source dir] [vanilla data dir]
"""
import json, os, sys
from collections import defaultdict
import heapq

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('ONEPIECE_SOURCE', '/mnt/project-files/one-piece-mod/source')
VANILLA = sys.argv[2] if len(sys.argv) > 2 else os.environ.get('VANILLA', '')
RES = f'{SRC}/src/main/resources'
BIOMES = f'{RES}/data/onepiece/worldgen/biome'
PLACED = f'{RES}/data/onepiece/worldgen/placed_feature'
MATERIAL_RULE = f'{RES}/data/onepiece/worldgen/material_rule/grand_line.json'
ORDER_FILE = f'{HERE}/feature_order.json'

M = 'minecraft:'
VEG = 9  # vegetal_decoration; vanilla features are put in the step vanilla uses them in (forest_rock 2, fossils 3...)


# ---------------------------------------------------------------- our own placed features for vanilla trees and piles
def tree(feature, chance=1, count=1, sapling='minecraft:oak_sapling'):
    """A vanilla tree (configured feature) placed like vanilla's trees_* do: on dry ground where a sapling would live."""
    placement = []
    if chance > 1: placement.append({"type": "minecraft:rarity_filter", "chance": chance})
    if count > 1: placement.append({"type": "minecraft:count", "count": count})
    placement += [{"type": "minecraft:in_square"}, {"type": "minecraft:surface_water_depth_filter", "max_water_depth": 0},
                  {"type": "minecraft:heightmap", "heightmap": "OCEAN_FLOOR"}, {"type": "minecraft:biome"},
                  {"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:would_survive", "state": sapling}}]
    return {"feature": feature, "placement": placement}


def pile(feature, chance=1, count=1):
    placement = []
    if chance > 1: placement.append({"type": "minecraft:rarity_filter", "chance": chance})
    if count > 1: placement.append({"type": "minecraft:count", "count": count})
    placement += [{"type": "minecraft:in_square"}, {"type": "minecraft:heightmap", "heightmap": "MOTION_BLOCKING_NO_LEAVES"}, {"type": "minecraft:biome"}]
    return {"feature": feature, "placement": placement}


CUSTOM = {  # "@name" in FLAVOUR -> data/onepiece/worldgen/placed_feature/flavour_<name>.json
    'fallen_oak':      tree('minecraft:fallen_oak_tree', chance=3),
    'fallen_jungle':   tree('minecraft:fallen_jungle_tree', chance=2, sapling='minecraft:jungle_sapling'),
    'fallen_spruce':   tree('minecraft:fallen_spruce_tree', chance=2, sapling='minecraft:spruce_sapling'),
    'fallen_birch':    tree('minecraft:fallen_birch_tree', chance=3, sapling='minecraft:birch_sapling'),
    'fallen_poplar':   tree('minecraft:fallen_poplar_tree', chance=2),
    'big_oaks':        tree('minecraft:fancy_oak', chance=2),
    'bee_oaks':        tree('minecraft:oak_bees_002', chance=3),
    'bee_big_oaks':    tree('minecraft:fancy_oak_bees_002', chance=2),
    'leafy_oaks':      tree('minecraft:oak_leaf_litter', chance=2),
    'mega_jungle':     tree('minecraft:mega_jungle_tree', chance=2, sapling='minecraft:jungle_sapling'),
    'mega_spruce':     tree('minecraft:mega_spruce', sapling='minecraft:spruce_sapling'),
    'pale_oaks':       tree('minecraft:pale_oak', chance=2, sapling='minecraft:pale_oak_sapling'),
    'orange_poplars':  tree('minecraft:orange_poplar_leaf_litter', count=2),
    'red_poplars':     tree('minecraft:red_poplar_leaf_litter', chance=2),
    'yellow_poplars':  tree('minecraft:yellow_poplar', chance=2),
    'giant_brown_mushrooms': pile('minecraft:huge_brown_mushroom', chance=4),
    'giant_red_mushrooms':   pile('minecraft:huge_red_mushroom', chance=6),
    'snow_piles':      pile('minecraft:pile_snow', chance=2, count=2),
    'ice_piles':       pile('minecraft:pile_ice', chance=3),
    'ice_patches':     pile('minecraft:ice_patch', chance=2, count=2),
}

# biome: add = features to add (vanilla placed feature name, or @name from CUSTOM), remove = ones to take out, colours
FLAVOUR = {
    # ---- East Blue: green, gentle, farmland and orchards
    'east_blue':       dict(add=['patch_tall_grass', 'wildflowers_birch_forest', '@fallen_oak', '@bee_oaks']),
    'orange_town':     dict(add=['@bee_big_oaks', 'flower_flower_forest', 'patch_tall_grass', 'patch_bush']),
    'conomi_islands':  dict(add=['patch_tall_grass', '@fallen_oak', 'flower_warm', 'patch_bush', 'patch_melon_sparse']),
    'loguetown':       dict(add=['forest_rock', 'patch_grass_forest', 'trees_birch_and_oak_leaf_litter', '@leafy_oaks'],
                            remove=['trees_plains'], grass='#7fae58', foliage='#6c9e4a'),
    'marineford':      dict(add=['trees_birch', 'patch_grass_meadow', 'flower_meadow'], remove=['trees_plains', 'patch_pumpkin']),
    # ---- Paradise
    'drum_island':     dict(add=['@snow_piles', '@ice_patches', 'trees_grove']),
    'alabasta':        dict(add=['patch_cactus_decorated', 'patch_dry_grass_badlands', 'patch_dead_bush', 'fossil_upper'],
                            remove=['brown_mushroom_normal', 'red_mushroom_normal', 'patch_pumpkin']),
    'jaya':            dict(add=['@fallen_jungle', 'patch_bush', 'patch_large_fern', 'trees_sparse_jungle']),
    'skypiea':         dict(add=['flower_meadow', 'wildflowers_meadow', 'patch_tall_grass', 'patch_grass_meadow'],
                            remove=['patch_melon', 'vines', 'patch_sugar_cane', 'patch_pumpkin'], grass='#b7e3a4', foliage='#9fd68e'),
    'sabaody':         dict(add=['patch_bush', 'patch_tall_grass_2', 'patch_waterlily'], grass='#6fb86a'),
    'little_garden':   dict(add=['patch_large_fern', '@fallen_jungle', 'patch_tall_grass', 'fossil_upper', 'fossil_lower', 'patch_bush', '@mega_jungle']),
    'thriller_bark':   dict(add=['@pale_oaks', 'pale_moss_patch', 'pale_garden_flowers', 'patch_dead_bush', '@fallen_oak', '@giant_brown_mushrooms', '@giant_red_mushrooms'],
                            remove=['flower_default', 'forest_flowers', 'patch_pumpkin', 'patch_sugar_cane']),
    'kuri':            dict(add=['bamboo_light', 'trees_badlands', 'patch_grass_badlands', 'patch_dry_grass_badlands', 'patch_dead_bush_badlands', '@fallen_oak'],
                            remove=['lake_lava_surface'], grass='#b09a58', foliage='#978444'),
    'enies_lobby':     dict(add=['trees_birch', 'patch_grass_meadow', 'flower_default', 'wildflowers_meadow'], remove=['patch_sunflower']),
    'green_bit':       dict(add=['patch_large_fern', 'flower_forest_flowers', 'patch_bush', '@fallen_jungle', 'trees_sparse_jungle']),
    'cacao_island':    dict(add=['patch_berry_common', 'patch_bush', 'trees_birch', 'flower_flower_forest']),
    'withered_forest': dict(add=['@orange_poplars', '@red_poplars', '@yellow_poplars', '@fallen_poplar', 'patch_dead_bush_2', 'patch_leaf_litter', 'patch_dry_grass_badlands'],
                            remove=['dark_forest_vegetation', 'forest_flowers', 'flower_default', 'patch_pumpkin', 'patch_sugar_cane'],
                            grass='#9a8a4a', foliage='#b8742a'),
    'kuraigana':       dict(add=['@pale_oaks', 'pale_moss_patch', 'forest_rock', 'patch_dead_bush', '@fallen_oak'],
                            remove=['flower_default', 'forest_flowers', 'patch_pumpkin', 'patch_sugar_cane']),
    # ---- New World
    'punk_hazard_frozen':  dict(add=['@ice_piles', '@ice_patches', '@snow_piles'], remove=['patch_grass_badlands', 'patch_sugar_cane', 'patch_pumpkin', 'brown_mushroom_normal', 'red_mushroom_normal']),
    'punk_hazard_burning': dict(add=['patch_dead_bush_badlands', 'fossil_upper'], remove=['brown_mushroom_normal', 'red_mushroom_normal', 'patch_pumpkin']),
    'elbaph':          dict(add=['forest_rock', '@fallen_spruce', '@mega_spruce', 'patch_tall_grass'], grass='#6c9d4c', foliage='#5d8c40'),
    'wano':            dict(add=['flower_meadow', 'patch_bush', '@fallen_birch', 'patch_tall_grass']),
    'zou':             dict(add=['@mega_jungle', 'patch_large_fern', 'vines', '@fallen_jungle']),
    'dressrosa':       dict(add=['@big_oaks', 'flower_meadow', 'patch_bush', 'wildflowers_meadow', 'trees_savanna']),
    'amazon_lily':     dict(add=['@mega_jungle', 'patch_large_fern', '@fallen_jungle', 'vines']),
    'egghead':         dict(add=['patch_grass_plain'], remove=['patch_pumpkin', 'patch_sugar_cane', 'trees_snowy'], grass='#a9c9c2', foliage='#8fb8b0'),
    'whole_cake':      dict(add=['patch_berry_common', 'flower_flower_forest', 'patch_bush']),
    'onigashima':      dict(add=['fossil_upper', 'patch_dry_grass_badlands', 'patch_dead_bush_badlands'], remove=['brown_mushroom_normal', 'red_mushroom_normal']),
    'hachinosu':       dict(add=['fossil_upper', 'patch_dead_bush_badlands', 'trees_badlands', 'patch_dry_grass_badlands'], remove=['lake_lava_surface']),
    'god_valley':      dict(add=['@big_oaks', 'forest_rock', 'wildflowers_meadow', 'flower_meadow', 'patch_tall_grass']),
    'red_line':        dict(add=['patch_grass_badlands', 'patch_dry_grass_badlands'], grass='#8c7c5c', foliage='#7a6a4a'),
    'fishman_reef':    dict(add=['kelp_warm', 'sea_pickle']),
    'new_world_sea':   dict(add=['kelp_cold', 'seagrass_deep']),
}


# Ground patches per island: (biomes, [(noise min, noise max, block state)]); only on the floor, above water.
# Blocks named onepiece:* come from com.onepiecemod.flora (tools/flora/gen_flora.py) and com.onepiecemod.world (island_cloud).
def st(s):
    if '[' not in s: return s
    name, props = s[:-1].split('[', 1)
    return {"id": name, "properties": dict(p.split('=', 1) for p in props.split(','))}


GROUND = [
    (['skypiea'],                                 [(-0.25, 0.05, 'onepiece:island_cloud'), (0.55, 0.7, 'onepiece:island_cloud')]),
    (['zou'],                                     [(-0.15, 0.1, 'minecraft:moss_block'), (0.5, 0.62, 'minecraft:rooted_dirt')]),
    (['jaya', 'little_garden', 'amazon_lily', 'green_bit'], [(0.4, 0.55, 'onepiece:jungle_loam'), (-0.5, -0.4, 'minecraft:mud')]),
    (['kuraigana'],                               [(-0.3, -0.1, 'minecraft:gravel'), (0.45, 0.6, 'minecraft:mossy_cobblestone'), (0.15, 0.3, 'onepiece:grave_soil')]),
    (['thriller_bark', 'withered_forest'],        [(0.15, 0.3, 'onepiece:grave_soil')]),
    (['wano'],                                    [(0.55, 0.68, 'minecraft:moss_block'), (-0.2, -0.1, 'minecraft:podzol[snowy=false]')]),
    (['whole_cake', 'cacao_island'],              [(-0.55, -0.3, 'onepiece:sugar_sand')]),
    (['hachinosu'],                               [(-0.6, -0.3, 'onepiece:black_sand'), (0.6, 1.0, 'onepiece:volcanic_ash')]),
    (['onigashima'],                              [(-0.45, -0.25, 'onepiece:volcanic_ash'), (0.7, 1.0, 'onepiece:black_sand')]),
    (['punk_hazard_burning'],                     [(0.3, 0.5, 'onepiece:volcanic_ash')]),
    (['drum_island', 'punk_hazard_frozen', 'elbaph'], [(0.5, 0.62, 'onepiece:permafrost')]),
    (['egghead'],                                 [(-0.2, -0.05, 'onepiece:permafrost'), (0.6, 0.7, 'minecraft:gravel')]),
    (['god_valley', 'enies_lobby'],               [(0.6, 0.7, 'minecraft:mossy_cobblestone')]),
    (['loguetown', 'marineford'],                 [(0.62, 0.72, 'minecraft:cobblestone')]),
    (['alabasta'],                                [(0.65, 0.75, 'minecraft:red_sand')]),
    (['red_line'],                                [(0.45, 0.6, 'minecraft:red_sand'), (-0.3, -0.2, 'minecraft:gravel')]),
    (['kuri'],                                    [(-0.3, -0.15, 'minecraft:coarse_dirt'), (0.5, 0.6, 'minecraft:red_sand')]),
    (['east_blue', 'orange_town', 'conomi_islands'], [(0.66, 0.72, 'minecraft:coarse_dirt')]),
]


def load(p):
    return json.load(open(p))


def save(p, o):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w') as f:
        json.dump(o, f, indent=2); f.write('\n')


# ---------------------------------------------------------------- vanilla feature order and steps
def vanilla_order():
    """{step: ordered list of features} from the vanilla biomes (a topological sort of every biome's list)."""
    if VANILLA and os.path.isdir(f'{VANILLA}/data/minecraft/worldgen/biome'):
        steps = defaultdict(list)
        for f in sorted(os.listdir(f'{VANILLA}/data/minecraft/worldgen/biome')):
            for i, lst in enumerate(load(f'{VANILLA}/data/minecraft/worldgen/biome/{f}')['features']):
                steps[i].append(lst)
        order = {}
        for i, lists in steps.items():
            edges = defaultdict(set); nodes = set()
            for lst in lists:
                for k, x in enumerate(lst):
                    nodes.add(x)
                    if k: edges[lst[k - 1]].add(x)
            indeg = {n: 0 for n in nodes}
            for a, bs in edges.items():
                for b in bs: indeg[b] += 1
            heap = [n for n in nodes if indeg[n] == 0]; heapq.heapify(heap); out = []
            while heap:
                n = heapq.heappop(heap); out.append(n)
                for m in sorted(edges[n]):
                    indeg[m] -= 1
                    if indeg[m] == 0: heapq.heappush(heap, m)
            assert len(out) == len(nodes), f'feature order cycle in vanilla step {i}'
            order[str(i)] = out
        save(ORDER_FILE, order)
        return {int(k): v for k, v in order.items()}
    if os.path.exists(ORDER_FILE):
        return {int(k): v for k, v in load(ORDER_FILE).items()}
    sys.exit('island_flavour.py: need vanilla data (argument 2 or $VANILLA) or tools/islands/feature_order.json')


ORDER = vanilla_order()
STEP_OF = {f: step for step, lst in ORDER.items() for f in lst}


def sort_step(step, lst):
    """Vanilla features in vanilla order, then the mod's own features (onepiece:*) in a fixed order after them."""
    rank = {f: i for i, f in enumerate(ORDER.get(step, []))}
    van = sorted((f for f in lst if f in rank), key=rank.get)
    mod = sorted(set(f for f in lst if f not in rank))
    return list(dict.fromkeys(van + mod))


# ---------------------------------------------------------------- our placed features
for name, placed in CUSTOM.items():
    save(f'{PLACED}/flavour_{name}.json', placed)

# ---------------------------------------------------------------- biomes
changed = 0
for name, fl in FLAVOUR.items():
    path = f'{BIOMES}/{name}.json'
    if not os.path.exists(path):
        print('missing biome', name); continue
    b = load(path)
    before = json.dumps(b, sort_keys=True)
    feats = b['features']
    while len(feats) < 11: feats.append([])
    remove = {M + x for x in fl.get('remove', [])}
    for x in fl.get('add', []):
        if x.startswith('@'):
            if x[1:] not in CUSTOM: sys.exit(f'{name}: unknown custom feature {x}')
            f, step = f'onepiece:flavour_{x[1:]}', VEG
        else:
            f, step = M + x, STEP_OF.get(M + x)
            if step is None: sys.exit(f'{name}: {f} is not placed by any vanilla biome; wrap it in CUSTOM instead')
        if f not in feats[step]: feats[step].append(f)
    for i in range(len(feats)):
        feats[i] = sort_step(i, [f for f in feats[i] if f not in remove])
    eff = b.setdefault('effects', {})
    for k in ('grass', 'foliage', 'water'):
        if k in fl: eff[f'{k}_color'] = fl[k]
    if json.dumps(b, sort_keys=True) != before:
        save(path, b); changed += 1

# every onepiece biome (also the ones without flavour) gets the vanilla feature order, so no two lists disagree
for f in sorted(os.listdir(BIOMES)):
    path = f'{BIOMES}/{f}'
    b = load(path)
    feats = b['features']
    fixed = [sort_step(i, lst) for i, lst in enumerate(feats)]
    if fixed != feats:
        b['features'] = fixed; save(path, b); changed += 1
print('island flavour: changed', changed, 'biome files;', len(CUSTOM), 'flavour_* placed features')


# ---------------------------------------------------------------- ground patches (surface rules)
def cond(c, then): return {"type": "minecraft:condition", "if_true": c, "then_run": then}
def seq(*r): return {"type": "minecraft:sequence", "sequence": list(r)}
def biome_is(*n): return {"type": "minecraft:biome", "biome_is": [f"onepiece:{x}" for x in n]}
def block(s): return {"type": "minecraft:block", "result_state": st(s)}
def patch(lo, hi, then): return cond({"type": "minecraft:noise_threshold", "noise": "minecraft:surface", "min_threshold": lo, "max_threshold": hi}, then)


rules = []
for biomes, patches in GROUND:
    rules.append(cond(biome_is(*biomes), cond("minecraft:on_floor", cond("minecraft:not_underwater",
                 seq(*[patch(lo, hi, block(s)) for lo, hi, s in patches])))))
flavour_rules = seq(*rules)

mr = load(MATERIAL_RULE)
# find the per-biome surface sequence: top sequence -> condition(above_preliminary_surface) -> sequence -> [0] = biome rules
top = mr['sequence']
aps = next(r for r in top if isinstance(r, dict) and r.get('type') == 'minecraft:condition' and r['if_true'].get('type') == 'minecraft:above_preliminary_surface')
surface = aps['then_run']['sequence'][0]['sequence']
if surface and surface[0].get('type') == 'minecraft:sequence':
    surface[0] = flavour_rules  # ours from an earlier run: replace
else:
    surface.insert(0, flavour_rules)
save(MATERIAL_RULE, mr)
print('island flavour: ground patches for', sum(len(b) for b, _ in GROUND), 'biomes written to', os.path.relpath(MATERIAL_RULE, SRC))
