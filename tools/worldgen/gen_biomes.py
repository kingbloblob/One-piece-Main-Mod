"""Island biomes, their mobs, their ground blocks, and the Grand Line world type that places them."""
import json, os, re
V = '/tmp/claude-0/vanilla'
OUT = '/tmp/claude-0/sync/one-piece-mod/src/main/resources'
D = OUT + '/data/onepiece'

def w(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(obj, f, indent=2); f.write('\n')

# ------------------------------------------------------------------ mobs
# Each entry: (mob, weight, min group, max group). Passive mobs never attack, neutral ones fight back
# (wolves, polar bears, pandas, llamas, goats, dolphins), hostile ones attack on sight.
DANGER = {
    # how thin hostile spawns are (spawn_costs) and how many animals generate with the world
    "easy":   {"budget": 0.10, "animals": 0.12},
    "medium": {"budget": None, "animals": 0.08},
    "hard":   {"budget": None, "animals": 0.04},
    "deadly": {"budget": None, "animals": 0.01},
}
def entry(m, wgt, lo, hi):
    return {"type": f"minecraft:{m}", "count": lo if lo == hi else {"type": "minecraft:uniform", "min_inclusive": lo, "max_inclusive": hi}, "weight": wgt}
def mobs(danger, passive=(), neutral=(), hostile=(), water=(), ambient=(("bat", 10, 8, 8),), water_ambient=()):
    cats = {}
    if passive or neutral: cats["creature"] = [entry(*m) for m in list(passive) + list(neutral)]
    if hostile: cats["monster"] = [entry(*m) for m in hostile]
    if ambient: cats["ambient"] = [entry(*m) for m in ambient]
    if water: cats["water_creature"] = [entry(*m) for m in water]
    if water_ambient: cats["water_ambient"] = [entry(*m) for m in water_ambient]
    costs = {}
    if DANGER[danger]["budget"]:
        costs = {f"minecraft:{m[0]}": {"charge": 1.0, "energy_budget": DANGER[danger]["budget"]} for m in hostile}
    return {"argument": {"spawn_costs": costs, "spawns_by_category": cats}, "modifier": "overlay"}

STANDARD = (("zombie", 95, 4, 4), ("skeleton", 100, 4, 4), ("spider", 100, 4, 4), ("creeper", 100, 4, 4),
            ("enderman", 10, 1, 4), ("witch", 5, 1, 1), ("zombie_villager", 5, 1, 1), ("slime", 100, 4, 4))
GENTLE = (("zombie", 60, 1, 2), ("skeleton", 60, 1, 2), ("spider", 40, 1, 2), ("creeper", 30, 1, 1), ("enderman", 5, 1, 1))

# ------------------------------------------------------------------ biomes
def vb(name): return json.load(open(f'{V}/worldgen/biome/{name}.json'))
VEG = 9
def make(base, danger, spawns, sky=None, fog=None, water=None, grass=None, foliage=None, temp=None, downfall=None, precip=None,
         add=None, remove=(), particles=None, fog_distance=None):
    b = vb(base); a = b['attributes']
    a['minecraft:gameplay/natural_mob_spawns'] = spawns
    a['minecraft:gameplay/creature_world_gen_spawn_probability'] = DANGER[danger]["animals"]
    if sky: a['minecraft:visual/sky_color'] = sky
    if fog: a['minecraft:visual/fog_color'] = fog
    if fog_distance: a['minecraft:visual/fog_end_distance'] = {"argument": fog_distance, "modifier": "multiply"}
    if particles: a['minecraft:visual/ambient_particles'] = {"argument": [{"particle": {"type": particles[0]}, "probability": particles[1]}], "modifier": "append"}
    if water: b['effects']['water_color'] = water
    if grass: b['effects']['grass_color'] = grass
    if foliage: b['effects']['foliage_color'] = foliage
    if temp is not None: b['temperature'] = temp
    if downfall is not None: b['downfall'] = downfall
    if precip is not None: b['has_precipitation'] = precip
    for step, feats in (add or {}).items():
        b['features'][step] = b['features'][step] + [f for f in feats if f not in b['features'][step]]
    b['features'] = [[f for f in step if f not in remove] for step in b['features']]
    b['_danger'] = danger
    return b

BIOMES = {
    # ---- easy, peaceful islands
    "east_blue": make("plains", "easy", mobs("easy",
        passive=(("cow", 8, 2, 4), ("sheep", 12, 2, 4), ("pig", 10, 2, 4), ("chicken", 10, 2, 4), ("horse", 5, 2, 4)),
        neutral=(("wolf", 2, 2, 4),), hostile=GENTLE),
        sky="#79b6ff", add={VEG: ["minecraft:flower_plains", "minecraft:trees_plains"]}),
    "dressrosa": make("sunflower_plains", "easy", mobs("easy",
        passive=(("donkey", 4, 1, 2), ("horse", 4, 2, 4), ("sheep", 10, 2, 4), ("rabbit", 6, 2, 3), ("cow", 6, 2, 4)),
        neutral=(("llama", 4, 2, 4),), hostile=GENTLE),
        sky="#8ec9ff", grass="#9fd65a", temp=1.0),
    "zou": make("flower_forest", "easy", mobs("easy",
        passive=(("ocelot", 4, 1, 3), ("fox", 6, 2, 4), ("rabbit", 6, 2, 3), ("cat", 4, 1, 2), ("parrot", 6, 1, 2)),
        neutral=(("panda", 2, 1, 2), ("wolf", 3, 2, 4)), hostile=GENTLE),
        sky="#9ad0ff", grass="#6fc24a", foliage="#5fb03a"),
    "sabaody": make("mangrove_swamp", "easy", mobs("easy",
        passive=(("frog", 10, 2, 5), ("chicken", 6, 2, 4), ("parrot", 4, 1, 2)),
        neutral=(), hostile=GENTLE + (("slime", 20, 1, 2),), water=(("tropical_fish", 25, 8, 8),)),
        sky="#9fe0ff", fog="#d6f3ff", water="#4fc3d8"),
    # ---- medium
    "whole_cake": make("meadow", "medium", mobs("medium",
        passive=(("sheep", 10, 2, 4), ("pig", 10, 2, 4), ("chicken", 10, 2, 4), ("rabbit", 6, 2, 3)),
        neutral=(("goat", 3, 1, 2), ("llama", 3, 2, 3)),
        hostile=tuple(m for m in STANDARD if m[0] != "witch") + (("witch", 20, 1, 2),)),
        sky="#ffc4e6", fog="#ffe0f2", grass="#ff9fd0", foliage="#ff8fc8", water="#c87dff"),
    "wano": make("cherry_grove", "medium", mobs("medium",
        passive=(("rabbit", 6, 2, 3), ("pig", 6, 2, 4), ("horse", 4, 2, 4)),
        neutral=(("wolf", 4, 2, 4),), hostile=STANDARD),
        sky="#ffb7c5", fog="#ffd9e2", add={VEG: ["minecraft:bamboo_light"]}),
    "drum_island": make("snowy_taiga", "medium", mobs("medium",
        passive=(("rabbit", 6, 2, 3), ("fox", 6, 2, 4)),
        neutral=(("wolf", 6, 2, 4), ("polar_bear", 2, 1, 2), ("goat", 3, 1, 3)),
        hostile=STANDARD + (("stray", 60, 2, 4),)),
        sky="#c6d4ff", fog="#e6ecff", temp=-0.6),
    "elbaph": make("old_growth_spruce_taiga", "medium", mobs("medium",
        passive=(("sheep", 8, 2, 4), ("cow", 8, 2, 4), ("rabbit", 4, 2, 3)),
        neutral=(("wolf", 8, 2, 4), ("goat", 4, 1, 3), ("polar_bear", 1, 1, 2)), hostile=STANDARD),
        sky="#b9c9ff", temp=-0.3, add={VEG: ["onepiece:adam_tree_upper_yard"]}),
    "egghead": make("snowy_plains", "medium", mobs("medium",
        passive=(("rabbit", 8, 2, 3), ("fox", 4, 2, 3)),
        neutral=(("polar_bear", 3, 1, 2),),
        hostile=STANDARD + (("stray", 80, 2, 4),)),
        sky="#d2f0ff", fog="#f0fbff", particles=("minecraft:electric_spark", 0.002)),
    "alabasta": make("desert", "medium", mobs("medium",
        passive=(("camel", 4, 1, 2), ("rabbit", 8, 2, 3), ("armadillo", 4, 1, 2)),
        neutral=(("llama", 2, 2, 3),),
        hostile=(("husk", 80, 4, 4), ("parched", 50, 2, 4), ("spider", 80, 4, 4), ("creeper", 80, 4, 4), ("zombie", 20, 4, 4), ("enderman", 10, 1, 4))),
        sky="#f2d59b", fog="#f0dcb0", water="#3fb5c4", remove=["minecraft:desert_well"]),
    "jaya": make("jungle", "medium", mobs("medium",
        passive=(("parrot", 10, 1, 2), ("ocelot", 2, 1, 3), ("chicken", 10, 2, 4)),
        neutral=(("panda", 1, 1, 2),), hostile=STANDARD),
        sky="#8fc8ff", grass="#4fbf3f"),
    "skypiea": make("jungle", "medium", mobs("medium",
        passive=(("parrot", 12, 1, 2), ("chicken", 8, 2, 4), ("rabbit", 4, 2, 3)),
        neutral=(("llama", 2, 2, 3),), hostile=STANDARD),
        sky="#a8dcff", fog="#e8f6ff", water="#6ecbff", add={VEG: ["onepiece:adam_tree_upper_yard"]}, particles=("minecraft:white_ash", 0.004)),
    "fishman_reef": make("warm_ocean", "medium", mobs("medium",
        passive=(("turtle", 5, 2, 5),), neutral=(),
        hostile=(("drowned", 100, 1, 3), ("zombie", 20, 4, 4), ("skeleton", 20, 4, 4)),
        water=(("dolphin", 6, 1, 2), ("squid", 4, 1, 4)), water_ambient=(("tropical_fish", 25, 8, 8), ("pufferfish", 15, 1, 3))),
        sky="#7ec8ff", water="#2ad1d1"),
    # ---- hard
    "amazon_lily": make("bamboo_jungle", "hard", mobs("hard",
        passive=(("parrot", 10, 1, 2), ("ocelot", 4, 1, 3)),
        neutral=(("panda", 4, 1, 2),),
        hostile=(("spider", 140, 2, 4), ("witch", 30, 1, 2), ("creeper", 100, 4, 4), ("skeleton", 80, 4, 4), ("zombie", 60, 4, 4))),
        sky="#a6e0a0", grass="#3fa64a"),
    "punk_hazard_frozen": make("ice_spikes", "hard", mobs("hard",
        passive=(("rabbit", 3, 1, 2),),
        neutral=(("polar_bear", 6, 1, 2),),
        hostile=(("stray", 140, 2, 4), ("skeleton", 40, 4, 4), ("zombie", 60, 4, 4), ("creeper", 80, 4, 4), ("enderman", 10, 1, 4))),
        sky="#bfe6ff", fog="#dff2ff", water="#8fd3ff", temp=-0.7, particles=("minecraft:white_ash", 0.01)),
    "punk_hazard_burning": make("badlands", "hard", mobs("hard",
        passive=(("armadillo", 2, 1, 1),), neutral=(),
        hostile=(("magma_cube", 80, 1, 3), ("husk", 60, 2, 4), ("skeleton", 60, 2, 4), ("creeper", 60, 2, 4), ("blaze", 10, 1, 2))),
        sky="#ff7a4a", fog="#8a3b26", water="#c86b3a", grass="#6b4a2a", foliage="#6b4a2a",
        remove=["minecraft:patch_cactus_decorated", "minecraft:patch_sugar_cane_badlands", "minecraft:patch_pumpkin"],
        add={1: ["minecraft:lake_lava_surface"]}, particles=("minecraft:ash", 0.02)),
    "little_garden": make("jungle", "hard", mobs("hard",
        passive=(("sniffer", 4, 1, 2), ("parrot", 8, 1, 2), ("frog", 6, 2, 4)),
        neutral=(("panda", 2, 1, 2),),
        hostile=(("spider", 120, 2, 4), ("cave_spider", 40, 1, 3), ("zombie", 80, 4, 4), ("creeper", 100, 4, 4), ("witch", 15, 1, 1))),
        sky="#9fd18a", fog="#c8e8b4", grass="#2f9a2f", foliage="#2a8a2a", add={VEG: ["onepiece:adam_tree_upper_yard"]}),
    "thriller_bark": make("dark_forest", "hard", mobs("hard",
        passive=(), neutral=(),
        hostile=(("zombie", 160, 2, 5), ("zombie_villager", 40, 1, 2), ("skeleton", 80, 2, 4), ("bogged", 40, 1, 3), ("witch", 30, 1, 2), ("spider", 60, 2, 4)),
        ambient=(("bat", 30, 8, 8),)),
        sky="#5a5a6e", fog="#46465a", grass="#4b5a3a", foliage="#3e4a30", water="#3a3a55", fog_distance=0.3, particles=("minecraft:white_ash", 0.02)),
    # ---- deadly
    "onigashima": make("eroded_badlands", "deadly", mobs("deadly",
        passive=(), neutral=(),
        hostile=(("wither_skeleton", 60, 1, 3), ("blaze", 30, 1, 2), ("magma_cube", 60, 1, 3), ("husk", 60, 2, 4), ("creeper", 60, 2, 4))),
        sky="#3a2030", fog="#4a2028", water="#5a3040", grass="#3a2a20", foliage="#3a2a20",
        remove=["minecraft:patch_cactus_decorated", "minecraft:patch_sugar_cane_badlands", "minecraft:patch_pumpkin"],
        add={1: ["minecraft:lake_lava_surface"]}, particles=("minecraft:ash", 0.04)),
    "red_line": make("stony_peaks", "deadly", mobs("deadly",
        passive=(), neutral=(("goat", 6, 1, 3),),
        hostile=(("wither_skeleton", 40, 1, 2), ("stray", 60, 2, 4), ("enderman", 30, 1, 4), ("creeper", 80, 2, 4), ("skeleton", 80, 2, 4))),
        sky="#ffb08a", fog="#e0a080"),
}
NAMES = {f"biome.onepiece.{k}": v for k, v in {
    "east_blue": "East Blue Isle", "dressrosa": "Dressrosa Fields", "zou": "Zou Forest", "sabaody": "Sabaody Archipelago",
    "whole_cake": "Totto Land", "wano": "Wano Country", "drum_island": "Drum Island", "elbaph": "Elbaph", "egghead": "Egghead",
    "alabasta": "Alabasta", "jaya": "Jaya", "skypiea": "Skypiea Upper Yard", "fishman_reef": "Fish-Man Reef",
    "amazon_lily": "Amazon Lily", "punk_hazard_frozen": "Punk Hazard (Frozen Side)", "punk_hazard_burning": "Punk Hazard (Burning Side)",
    "little_garden": "Little Garden", "thriller_bark": "Thriller Bark Mist", "onigashima": "Onigashima Wastes", "red_line": "Red Line Cliffs"}.items()}
DANGER_OF = {k: b.pop('_danger') for k, b in BIOMES.items()}
for name, b in BIOMES.items():
    w(f'{D}/worldgen/biome/{name}.json', b)
for old in os.listdir(f'{D}/worldgen/biome'):
    if old[:-5] not in BIOMES: os.remove(f'{D}/worldgen/biome/{old}')

# ------------------------------------------------------------------ ground blocks (surface rules)
def biome_is(*n): return {"type": "minecraft:biome", "biome_is": [f"onepiece:{x}" for x in n]}
def block_state(s):
    # "minecraft:basalt[axis=y]" -> {"id": ..., "properties": {...}}; the [..] string form doesn't parse
    if "[" not in s: return s
    name, props = s[:-1].split("[", 1)
    return {"id": name, "properties": dict(p.split("=", 1) for p in props.split(","))}
def block(s): return {"type": "minecraft:block", "result_state": block_state(s)}
def cond(c, then): return {"type": "minecraft:condition", "if_true": c, "then_run": then}
def seq(*r): return {"type": "minecraft:sequence", "sequence": list(r)}
def patch(lo, hi, then): return cond({"type": "minecraft:noise_threshold", "noise": "minecraft:surface", "min_threshold": lo, "max_threshold": hi}, then)
FLOOR, UNDER, DEEP = "minecraft:on_floor", "minecraft:under_floor", "minecraft:deep_under_floor"
surface = seq(
    cond(biome_is("alabasta"), seq(cond(FLOOR, "minecraft:overworld/sand_or_sandstone_if_ceiling"), cond(UNDER, block("minecraft:sand")), cond(DEEP, block("minecraft:sandstone")))),
    cond(biome_is("fishman_reef"), seq(cond(FLOOR, block("minecraft:sand")), cond(UNDER, block("minecraft:sand")))),
    cond(biome_is("punk_hazard_burning"), seq(cond(FLOOR, seq(patch(-0.15, 0.15, block("minecraft:magma_block")), patch(0.5, 1.0, block("minecraft:basalt[axis=y]")), block("minecraft:blackstone"))), cond(UNDER, block("minecraft:blackstone")))),
    cond(biome_is("onigashima"), seq(cond(FLOOR, seq(patch(-0.1, 0.1, block("minecraft:magma_block")), patch(0.3, 1.0, block("minecraft:basalt[axis=y]")), patch(-1.0, -0.4, block("minecraft:tuff")), block("minecraft:blackstone"))), cond(UNDER, block("minecraft:basalt[axis=y]")))),
    cond(biome_is("red_line"), seq(cond(FLOOR, seq(patch(-0.2, 0.2, block("minecraft:orange_terracotta")), block("minecraft:red_terracotta"))), cond(UNDER, block("minecraft:red_sandstone")), cond(DEEP, block("minecraft:red_terracotta")))),
    cond(biome_is("punk_hazard_frozen"), seq(cond(FLOOR, seq(patch(-0.2, 0.2, block("minecraft:packed_ice")), block("minecraft:snow_block"))), cond(UNDER, block("minecraft:packed_ice")))),
    cond(biome_is("whole_cake"), cond(FLOOR, cond("minecraft:not_underwater", seq(patch(-0.12, 0.12, block("minecraft:pink_terracotta")), patch(0.6, 0.75, block("minecraft:white_terracotta")))))),
    cond(biome_is("thriller_bark"), cond(FLOOR, cond("minecraft:not_underwater", seq(patch(-0.3, 0.1, block("minecraft:podzol[snowy=false]")), patch(0.4, 1.0, block("minecraft:coarse_dirt")))))),
    cond(biome_is("little_garden", "elbaph"), cond(FLOOR, cond("minecraft:not_underwater", patch(-0.2, 0.0, block("minecraft:podzol[snowy=false]"))))),
    cond(biome_is("sabaody"), cond(FLOOR, cond("minecraft:not_underwater", "minecraft:overworld/biome_surface/mangrove_swamp"))),
    cond(biome_is("drum_island", "egghead"), cond(FLOOR, cond("minecraft:not_underwater", patch(-0.1, 0.1, block("minecraft:powder_snow"))))),
)
w(f'{D}/worldgen/material_rule/grand_line.json', seq(
    "minecraft:bedrock_floor", "minecraft:overworld/copper_ore_vein", "minecraft:overworld/iron_ore_vein",
    cond({"type": "minecraft:above_preliminary_surface"}, seq(surface, "minecraft:overworld/surface")),
    "minecraft:overworld/underground"))

# ------------------------------------------------------------------ terrain: a sea of islands
src = f'{V}/worldgen/density_function/overworld'
fnames = []
for root, _, files in os.walk(src):
    for fn in files: fnames.append(os.path.relpath(os.path.join(root, fn), src)[:-5])
def rewrite(text):
    return re.sub(r'"minecraft:overworld/([a-z0-9_/]+)"', lambda m: f'"onepiece:grand_line/{m.group(1)}"' if m.group(1) in fnames else m.group(0), text)
for n in fnames:
    w(f'{D}/worldgen/density_function/grand_line/{n}.json', json.loads(rewrite(open(f'{src}/{n}.json').read())))
ISLAND_SCALE = 0.55    # Minecraft uses 0.25. Higher = smaller, more frequent islands.
SEA_SHIFT = -0.30      # More negative = more sea.
CLIMATE_SCALE = 0.5    # Minecraft uses 0.25. Higher = neighbouring islands differ more.
cont = json.load(open(f'{src}/continents.json'))
cont['input']['xz_scale'] = ISLAND_SCALE
cont['input'] = {"type": "minecraft:add", "left": cont['input'], "right": SEA_SHIFT}
w(f'{D}/worldgen/density_function/grand_line/continents.json', cont)
for n in ('temperature', 'vegetation'):
    o = json.load(open(f'{src}/{n}.json'))
    (o['input'] if 'input' in o else o)['xz_scale'] = CLIMATE_SCALE
    w(f'{D}/worldgen/density_function/grand_line/{n}.json', o)
ns = json.loads(rewrite(open(f'{V}/worldgen/noise_settings/overworld.json').read()))
ns['material_rule'] = 'onepiece:grand_line'
w(f'{D}/worldgen/noise_settings/grand_line.json', ns)

# ------------------------------------------------------------------ which biome goes where
R = lambda a, b: [a, b]
entries = []
def add(biome, T, H, C, E=(-1.0, 1.0), W=(-1.0, 1.0), depth=None):
    for d in ([0.0, 0.0], [1.0, 1.0]) if depth is None else [depth]:
        entries.append({"biome": biome, "parameters": {"temperature": R(*T), "humidity": R(*H), "continentalness": R(*C),
                        "erosion": R(*E), "weirdness": R(*W), "depth": d, "offset": 0.0}})
TEMPS = [(-1.0, -0.45), (-0.45, -0.15), (-0.15, 0.2), (0.2, 0.55), (0.55, 1.0)]
HUMID = [(-1.0, -0.1), (-0.1, 0.3), (0.3, 1.0)]
WEIRD = [(-1.0, 0.0), (0.0, 1.0)]
DEEP_SEA = ["minecraft:deep_frozen_ocean", "minecraft:deep_cold_ocean", "minecraft:deep_ocean", "minecraft:deep_lukewarm_ocean", "minecraft:warm_ocean"]
SEA = [["minecraft:frozen_ocean"] * 2, ["minecraft:cold_ocean"] * 2, ["minecraft:ocean"] * 2, ["minecraft:lukewarm_ocean", "onepiece:fishman_reef"], ["minecraft:warm_ocean", "onepiece:fishman_reef"]]
SHORE = ["minecraft:snowy_beach", "minecraft:beach", "minecraft:beach", "minecraft:beach", "minecraft:beach"]
o = lambda n: f"onepiece:{n}"
ISLANDS = [  # [temperature][humidity] = (biome when weirdness < 0, biome when weirdness > 0)
    [(o("punk_hazard_frozen"), o("egghead")), (o("drum_island"), o("elbaph")), (o("drum_island"), o("elbaph"))],
    [(o("east_blue"), "minecraft:plains"), (o("wano"), o("zou")), (o("thriller_bark"), o("wano"))],
    [(o("east_blue"), o("dressrosa")), (o("whole_cake"), "minecraft:forest"), (o("sabaody"), o("amazon_lily"))],
    [("minecraft:savanna", o("dressrosa")), (o("skypiea"), o("jaya")), (o("amazon_lily"), o("little_garden"))],
    [(o("alabasta"), o("alabasta")), (o("punk_hazard_burning"), o("onigashima")), (o("little_garden"), o("skypiea"))],
]
for ti, T in enumerate(TEMPS):
    add(DEEP_SEA[ti], T, (-1, 1), (-1.2, -0.455))
    for wi, Wr in enumerate(WEIRD):
        add(SEA[ti][wi], T, (-1, 1), (-0.455, -0.19), W=Wr)
    add(SHORE[ti], T, (-1, 1), (-0.19, -0.11))
    for hi, H in enumerate(HUMID):
        for wi, Wr in enumerate(WEIRD):
            b = ISLANDS[ti][hi][wi]
            add(b, T, H, (-0.11, 0.3), W=Wr)
            add(b, T, H, (0.3, 1.0), E=(-0.6, 1.0), W=Wr)
# High, rugged inland ground becomes the Red Line cliffs.
add(o("red_line"), (-1, 1), (-1, 1), (0.3, 1.0), E=(-1.0, -0.6))
add("minecraft:lush_caves", (-1, 1), (0.7, 1.0), (-1.2, 1.0), depth=[0.2, 0.9])
add("minecraft:dripstone_caves", (-1, 1), (-1, 0.7), (0.8, 1.0), depth=[0.2, 0.9])
normal = json.load(open(f'{V}/worldgen/world_preset/normal.json'))
normal['dimensions']['minecraft:overworld'] = {"type": "minecraft:overworld", "generator": {"type": "minecraft:noise",
    "biome_source": {"type": "minecraft:multi_noise", "biomes": entries}, "settings": "onepiece:grand_line"}}
w(f'{D}/worldgen/world_preset/grand_line.json', normal)
w(f'{OUT}/data/minecraft/tags/worldgen/world_preset/normal.json', {"replace": False, "values": ["onepiece:grand_line"]})
used = {e['biome'] for e in entries}
missing = [k for k in BIOMES if o(k) not in used]
assert not missing, missing
print("biomes:", len(BIOMES), "map entries:", len(entries))

# Put the island look (fog, particles, island music) back on the biomes we just rewrote.
import subprocess as _sp, sys as _sys, os as _os
_sp.run([_sys.executable, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "islands", "island_look.py")])
