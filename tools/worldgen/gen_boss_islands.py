"""Boss islands and distance rings (2026-10-24, asked by ryan: "easy biomes closer to spawn and the hard ones far away",
"put bosses in the hard biomes, and a new biome for each boss just like in the show").

- 13 new island biomes, one per boss without a fitting island yet (copied from an existing biome for the look,
  and from another for how dangerous the mobs are).
- The Grand Line world preset uses onepiece:rings (com.onepiecemod.world.RingBiomeSource): 4 rings around spawn,
  East Blue -> Paradise -> New World edge -> deep New World, each with its own island biomes.
- Structure sets use onepiece:ring_spread (RingSpreadPlacement): boss lairs only in their ring, harder places only far out.
Safe to run again. Writes straight into source/.
"""
import copy, glob, json, os

# The rings (RingBiomeSource / RingSpreadPlacement in source/.../world) passed build + Grand Line tests 2026-10-24 05:29.
# RINGS_JAVA=0 writes plain vanilla multi_noise + random_spread instead (only if those classes ever have to come out).
RINGS_JAVA = os.environ.get('RINGS_JAVA', '1') == '1'

RES = os.environ.get('ONEPIECE_SOURCE', '/mnt/project-files/one-piece-mod/source') + '/src/main/resources'
D = RES + '/data/onepiece'
BIOMES = D + '/worldgen/biome'
TAGS = D + '/tags/worldgen/biome'


def w(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f: json.dump(obj, f, indent=2); f.write('\n')


def append(path, values):
    d = json.load(open(path)) if os.path.exists(path) else {"replace": False, "values": []}
    for v in values:
        if v not in d["values"]: d["values"].append(v)
    w(path, d)


# ================================================================ 1. the new biomes
# name: (title, looks like, mobs as dangerous as, colours {sky, fog, water, grass, foliage}, extra deco tags)
NEW = {
    "orange_town":     ("Orange Town", "east_blue", "east_blue", dict(sky="#8fc6ff", water="#3f8fe4", grass="#8fd45a", foliage="#7cc24a"), ["has_deco_mikan_bush"]),
    "loguetown":       ("Loguetown", "east_blue", "east_blue", dict(sky="#9fb8d8", fog="#c8d4e0", grass="#86b95a", foliage="#72a84a"), []),
    "conomi_islands":  ("Conomi Islands", "east_blue", "east_blue", dict(sky="#7ed0ff", water="#2fc4d8", grass="#79d04f", foliage="#5fc23a"), ["has_deco_mikan_bush", "has_deco_palm_trees"]),
    "kuri":            ("Kuri (Wano)", "punk_hazard_burning", "wano", dict(sky="#d9a77a", fog="#b48a66", water="#5a8ab4", grass="#a8945a", foliage="#8f7d44"), []),
    "enies_lobby":     ("Enies Lobby", "dressrosa", "amazon_lily", dict(sky="#a9d6ff", water="#3a7fd4", grass="#8cc46a", foliage="#78b05a"), []),
    "green_bit":       ("Green Bit", "amazon_lily", "amazon_lily", dict(sky="#9fd8b0", water="#3a9a8a", grass="#4fb83a", foliage="#3aa22a"), ["has_deco_giant_fern"]),
    "cacao_island":    ("Cacao Island", "whole_cake", "amazon_lily", dict(sky="#e8c4a0", fog="#d8b08a", water="#6b3a1f", grass="#8a5a3a", foliage="#7a4a2a"), []),
    "withered_forest": ("Withered Forest", "thriller_bark", "amazon_lily", dict(sky="#c8b48a", fog="#a8946a", water="#6a6a4a", grass="#8a7a4a", foliage="#7a6a3a"), []),
    "kuraigana":       ("Kuraigana Island", "thriller_bark", "onigashima", dict(sky="#4a4a5a", fog="#3a3a48", water="#2a2a3a", grass="#3e4a30", foliage="#34402a"), ["has_deco_gloom_trees"]),
    "hachinosu":       ("Hachinosu (Pirate Island)", "punk_hazard_burning", "onigashima", dict(sky="#5a4a4a", fog="#4a3a3a", water="#2a3a4a", grass="#5a5040", foliage="#4a4030"), []),
    "marineford":      ("Marineford", "east_blue", "red_line", dict(sky="#a8d8ff", water="#3f76e4", grass="#7cbd5a", foliage="#6aa84a"), []),
    "new_world_sea":   ("New World Sea", "fishman_reef", "fishman_reef", dict(sky="#5a7a9a", water="#1f3a6b"), []),
    "god_valley":      ("God Valley", "zou", "onigashima", dict(sky="#ffe9b0", water="#4a9ae4", grass="#9bd46a", foliage="#88c25a"), []),
}
SPAWN_KEYS = ("minecraft:gameplay/natural_mob_spawns", "minecraft:gameplay/creature_world_gen_spawn_probability")
for name, (title, look, danger, col, deco) in NEW.items():
    b = copy.deepcopy(json.load(open(f'{BIOMES}/{look}.json')))
    dangerous = json.load(open(f'{BIOMES}/{danger}.json'))['attributes']
    for k in SPAWN_KEYS:
        b['attributes'].pop(k, None)
        if k in dangerous: b['attributes'][k] = copy.deepcopy(dangerous[k])
    b['attributes']['minecraft:visual/sky_color'] = col['sky']
    if 'fog' in col: b['attributes']['minecraft:visual/fog_color'] = col['fog']
    if 'water' in col: b['effects']['water_color'] = col['water']
    if 'grass' in col: b['effects']['grass_color'] = col['grass']
    if 'foliage' in col: b['effects']['foliage_color'] = col['foliage']
    if name == "new_world_sea": b['attributes']['minecraft:visual/water_fog_color'] = "#06121f"
    w(f'{BIOMES}/{name}.json', b)

    me = f'onepiece:{name}'
    # Every biome tag the look-alike biome is in (mod tags, creature spawns, ores, deco, minecraft:is_*), except structures.
    for f in glob.glob(f'{TAGS}/**/*.json', recursive=True) + glob.glob(f'{RES}/data/minecraft/tags/worldgen/biome/*.json'):
        if '/has_structure/' in f: continue
        if f'onepiece:{look}' in json.load(open(f))['values']: append(f, [me])
    for t in deco: append(f'{TAGS}/{t}.json', [me])

# surface rules: a new biome gets the same ground as the biome it looks like
MR = D + '/worldgen/material_rule/grand_line.json'
mr = json.load(open(MR))
def walk(o):
    if isinstance(o, dict):
        if o.get('type') == 'minecraft:biome':
            for name, (_t, look, *_r) in NEW.items():
                if f'onepiece:{look}' in o['biome_is'] and f'onepiece:{name}' not in o['biome_is']:
                    o['biome_is'].append(f'onepiece:{name}')
        for v in o.values(): walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
walk(mr)
w(MR, mr)

# names
lang = f'{RES}/assets/onepiece_world/lang/en_us.json'
names = json.load(open(lang))
names.update({f'biome.onepiece.{n}': v[0] for n, v in NEW.items()})
w(lang, names)

# ================================================================ 2. the Grand Line rings
RINGS = [1500, 3500, 6000]  # blocks from spawn where East Blue, Paradise and the New World edge end
T = [[-1.0, -0.45], [-0.45, -0.15], [-0.15, 0.2], [0.2, 0.55], [0.55, 1.0]]  # cold .. hot
H = [[-1.0, -0.1], [-0.1, 0.3], [0.3, 1.0]]                                 # dry .. wet
W = [[-1.0, 0.0], [0.0, 1.0]]                                               # two variants per spot
# Land biomes per ring: GRID[ring][temperature] = [(dry a, dry b), (mid a, mid b), (wet a, wet b)]
v = lambda n: n if ':' in n else 'onepiece:' + n
GRID = [
    [  # 1. East Blue: Buggy, Smoker, Arlong
        [("minecraft:snowy_plains", "minecraft:snowy_plains"), ("minecraft:snowy_taiga", "minecraft:taiga"), ("minecraft:taiga", "minecraft:snowy_taiga")],
        [("east_blue", "minecraft:plains"), ("loguetown", "minecraft:forest"), ("minecraft:birch_forest", "east_blue")],
        [("east_blue", "orange_town"), ("conomi_islands", "minecraft:forest"), ("orange_town", "minecraft:flower_forest")],
        [("minecraft:savanna", "conomi_islands"), ("loguetown", "minecraft:plains"), ("minecraft:jungle", "east_blue")],
        [("minecraft:desert", "minecraft:savanna"), ("conomi_islands", "minecraft:savanna"), ("orange_town", "minecraft:jungle")],
    ],
    [  # 2. Paradise: Crocodile, Enel, Hawkins, Moria, Killer
        [("drum_island", "drum_island"), ("drum_island", "minecraft:snowy_taiga"), ("minecraft:snowy_taiga", "drum_island")],
        [("thriller_bark", "kuri"), ("sabaody", "thriller_bark"), ("kuri", "sabaody")],
        [("sabaody", "jaya"), ("kuri", "little_garden"), ("thriller_bark", "jaya")],
        [("alabasta", "jaya"), ("skypiea", "little_garden"), ("little_garden", "skypiea")],
        [("alabasta", "alabasta"), ("skypiea", "alabasta"), ("jaya", "skypiea")],
    ],
    [  # 3. New World edge: Lucci, Aokiji, Doflamingo, Fujitora, Katakuri, Kid, Ryokugyu, King
        [("punk_hazard_frozen", "elbaph"), ("elbaph", "punk_hazard_frozen"), ("punk_hazard_frozen", "elbaph")],
        [("wano", "withered_forest"), ("zou", "wano"), ("withered_forest", "enies_lobby")],
        [("dressrosa", "green_bit"), ("enies_lobby", "cacao_island"), ("green_bit", "dressrosa")],
        [("cacao_island", "amazon_lily"), ("dressrosa", "enies_lobby"), ("amazon_lily", "cacao_island")],
        [("punk_hazard_burning", "punk_hazard_burning"), ("amazon_lily", "punk_hazard_burning"), ("green_bit", "amazon_lily")],
    ],
    [  # 4. Deep New World: Kaido, Big Mom, Kizaru, Mihawk, Blackbeard, Akainu, Whitebeard, Xebec
        [("egghead", "egghead"), ("kuraigana", "egghead"), ("egghead", "kuraigana")],
        [("kuraigana", "marineford"), ("onigashima", "kuraigana"), ("marineford", "onigashima")],
        [("whole_cake", "god_valley"), ("marineford", "whole_cake"), ("god_valley", "hachinosu")],
        [("hachinosu", "whole_cake"), ("god_valley", "marineford"), ("whole_cake", "hachinosu")],
        [("onigashima", "hachinosu"), ("onigashima", "god_valley"), ("hachinosu", "onigashima")],
    ],
]
# Sea, beaches, caves and the Red Line mountains come from the old preset, changed per ring.
SEA_SWAP = [
    {"onepiece:red_line": "minecraft:stony_peaks", "onepiece:fishman_reef": "minecraft:lukewarm_ocean"},
    {"onepiece:red_line": "minecraft:stony_peaks"},
    {},
    {"onepiece:fishman_reef": "onepiece:new_world_sea", "minecraft:ocean": "onepiece:new_world_sea",
     "minecraft:lukewarm_ocean": "onepiece:new_world_sea", "minecraft:cold_ocean": "onepiece:new_world_sea"},
]
PRESET = D + '/worldgen/world_preset/grand_line.json'
preset = json.load(open(PRESET))
gen = preset['dimensions']['minecraft:overworld']['generator']
src = gen['biome_source']
if src['type'] == 'minecraft:multi_noise':  # first run: keep the old list as the template for sea and caves
    w(os.path.dirname(os.path.abspath(__file__)) + '/grand_line_multi_noise_backup.json', src)
    old = src['biomes']
else:
    old = json.load(open(os.path.dirname(os.path.abspath(__file__)) + '/grand_line_multi_noise_backup.json'))['biomes']
sea = [e for e in old if e['parameters']['continentalness'][1] <= -0.11 or e['biome'] in ('minecraft:lush_caves', 'minecraft:dripstone_caves', 'onepiece:red_line')]
rings = []
for r, grid in enumerate(GRID):
    entries = []
    for e in sea:
        e2 = copy.deepcopy(e); e2['biome'] = SEA_SWAP[r].get(e['biome'], e['biome']); entries.append(e2)
    for ti, row in enumerate(grid):
        for hi, pair in enumerate(row):
            for wi, name in enumerate(pair):
                for cont, ero in (([-0.11, 0.3], [-1.0, 1.0]), ([0.3, 1.0], [-0.6, 1.0])):
                    for depth in ([0.0, 0.0], [1.0, 1.0]):
                        entries.append({"biome": v(name), "parameters": {"temperature": T[ti], "humidity": H[hi], "continentalness": cont,
                                        "erosion": ero, "weirdness": W[wi], "depth": depth, "offset": 0.0}})
    rings.append({"max_distance": RINGS[r] if r < len(RINGS) else 1000000000, "biomes": entries})
# blend = how many blocks wide the mixed band between two rings is; edge = how far neighbouring biomes finger into each
# other (RingBiomeSource, biome-blending thread 2026-10-24). 0 and 0 give the old hard edges.
gen['biome_source'] = {"type": "onepiece:rings", "wobble": 250, "blend": 400, "edge": 32, "rings": rings} if RINGS_JAVA else {"type": "minecraft:multi_noise", "biomes": old}
w(PRESET, preset)
used = {e['biome'] for ring in rings for e in ring['biomes']}
missing = [b for b in used if b.startswith('onepiece:') and not os.path.exists(f"{BIOMES}/{b.split(':')[1]}.json")]
assert not missing, missing
append(f'{TAGS}/one_piece_islands.json', [f'onepiece:{n}' for n in NEW])

# ================================================================ 3. structures by distance
LAIR_BIOMES = {  # boss lair -> its island (old biomes stay, so lairs still appear in normal worlds)
    "buggy_big_top": ["orange_town"], "loguetown": ["loguetown"], "arlong_park": ["conomi_islands"], "cocoyasi_village": ["conomi_islands"],
    "kamazo_hideout": ["kuri"], "tower_of_justice": ["enies_lobby"], "corrida_colosseum": ["green_bit"], "mirror_hall": ["cacao_island"],
    "chocolate_town": ["cacao_island"], "victoria_punk": ["elbaph"], "withered_forest": ["withered_forest"], "hachinosu": ["hachinosu"],
    "kuraigana_castle": ["kuraigana"], "marineford": ["marineford"], "moby_dick": ["new_world_sea"], "god_valley": ["god_valley"],
    "flame_fortress": ["wano"], "ice_fortress": ["punk_hazard_frozen"], "foosha_village": ["orange_town"], "shells_town": ["loguetown"],
}
for s, bs in LAIR_BIOMES.items():
    append(f'{TAGS}/has_structure/{s}.json', [v(b) for b in bs])

E, P, N = RINGS
SETS = {  # file: (structures or None to keep, spacing, separation, salt, min distance, max distance)
    # 2026-10-25: spacings widened when StructureSpacing.java started keeping all our builds 200+ blocks apart
    # (it ranks the sets and the story places; see RANK and STORY there).
    # Lairs rebuilt life-size are up to ~125 blocks across, so separation (chunks) * 16 stays above that.
    "boss_east_blue_locations":   (["buggy_big_top", "loguetown"], 22, 10, 1408172031, 0, E),
    "boss_paradise_locations":    (["rain_dinners", "shandora", "straw_shrine", "kamazo_hideout"], 24, 11, 1408172032, E, P),
    "boss_new_world_locations":   (["ice_fortress", "corrida_colosseum", "mirror_hall", "victoria_punk", "flame_fortress", "withered_forest", "dressrosa_palace"], 28, 12, 1408172033, P, N),
    "boss_deep_new_world_locations": (["egghead_lab", "hachinosu", "kuraigana_castle", "god_valley"], 32, 12, 1408172034, N, None),
    "early_landmark_locations":   (["baratie", "arlong_park"], 32, 12, 1408172022, 0, E + 300),
    "landmark_paradise_locations": (["alubarna_palace", "galley_la_dock", "thriller_bark"], 40, 16, 1408172023, E, P),
    "landmark_new_world_locations": (["tower_of_justice", "ryugu_palace"], 44, 18, 1408172024, P, N),
    "landmark_locations":         (["marineford", "onigashima", "whole_cake_chateau", "moby_dick"], 56, 24, 1408172021, N, None),
    "easy_locations":             (None, 24, 12, 1408172001, 0, None),  # towns rebuilt up to ~115 blocks across
    "medium_locations":           (None, 30, 13, 1408172002, 1000, None),
    "hard_locations":             (None, 40, 14, 1408172003, 3000, None),
    "legendary_locations":        (None, 64, 24, 1408172004, 5500, None),
}
SS = D + '/worldgen/structure_set'
moved = {s for v_ in SETS.values() if v_[0] for s in v_[0]}
for fname, (structs, spacing, sep, salt, lo, hi) in SETS.items():
    path = f'{SS}/{fname}.json'
    if structs is None:
        structs = [x['structure'].split(':')[1] for x in json.load(open(path))['structures'] if x['structure'].split(':')[1] not in moved]
    placement = {"type": "onepiece:ring_spread", "spacing": spacing, "separation": sep, "salt": salt, "min_distance": lo}
    if hi: placement["max_distance"] = hi
    if not RINGS_JAVA: placement = {"type": "minecraft:random_spread", "spacing": spacing, "separation": sep, "salt": salt}
    w(path, {"structures": [{"structure": f"onepiece:{x}", "weight": 1} for x in structs], "placement": placement})
# every overworld structure must be in exactly one set
seen = {}
for f in glob.glob(f'{SS}/*.json'):
    for x in json.load(open(f))['structures']:
        seen.setdefault(x['structure'], []).append(os.path.basename(f))
dups = {k: v_ for k, v_ in seen.items() if len(v_) > 1}
assert not dups, dups
print("new biomes:", len(NEW), "rings:", [len(r['biomes']) for r in rings], "sets:", {k: len(json.load(open(f'{SS}/{k}.json'))['structures']) for k in SETS})

# Put the island look (fog, particles, island music) back on the biomes we just rewrote.
import subprocess as _sp, sys as _sys, os as _os
_sp.run([_sys.executable, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "islands", "island_look.py")])
# ...and the island flavour (per-island vanilla plants, ground patches, colours, feature order; needs $VANILLA or the saved order).
_sp.run([_sys.executable, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "islands", "island_flavour.py"), RES.rsplit('/src/main/resources', 1)[0]])
