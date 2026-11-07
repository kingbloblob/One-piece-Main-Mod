"""God Valley: the ruined holy island where the Rocks Pirates fought Roger and Garp 38 years ago.
Arena for the optional superboss Rocks D. Xebec (character "xebec"). Overworld, legendary tier, rare.
Writes the structure and its jigsaw files into source/ and appends it to the legendary structure set and
the one_piece_locations tag. Safe to run again. Afterwards rerun tools/worldgen/swap_blocks.py for deco blocks.
"""
import json, math, os, random, sys
sys.path.insert(0, '/mnt/project-files/one-piece-mod/tools/worldgen')
from kit import *

RES = '/mnt/project-files/one-piece-mod/source/src/main/resources'
D = RES + '/data/onepiece'
NAME = "god_valley"


def w(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f: json.dump(obj, f, indent=2); f.write('\n')


sys.exit("god_valley is now built life-size by tools/landmarks/god_valley.py; this old script would overwrite it.")
rnd = random.Random(38)  # fixed seed, so the ruin looks the same every run
b = B()
C, R = 24, 23  # centre and radius of the island floor

# ---- ground: grass meadow on the outside, white flagstones, then the scorched arena
for x in range(C - R, C + R + 1):
    for z in range(C - R, C + R + 1):
        d = math.hypot(x - C, z - C)
        if d > R + 0.3: continue
        b.set(x, -1, z, "minecraft:dirt"); b.set(x, -2, z, "minecraft:dirt")
        if d > 19:
            b.set(x, 0, z, "minecraft:grass_block[snowy=false]")
            if rnd.random() < 0.18: b.set(x, 1, z, rnd.choice(["minecraft:lily_of_the_valley", "minecraft:oxeye_daisy", "minecraft:white_tulip"]))
        elif d > 15:
            b.set(x, 0, z, rnd.choice(["minecraft:polished_diorite", "minecraft:calcite", "minecraft:cracked_stone_bricks"]))
        else:  # the arena: scorched, cracked, with craters
            b.set(x, 0, z, rnd.choice(["minecraft:blackstone", "minecraft:basalt[axis=y]", "minecraft:coarse_dirt", "minecraft:cracked_polished_blackstone_bricks", "minecraft:magma_block" if rnd.random() < 0.15 else "minecraft:blackstone"]))
        for y in range(1, 20):
            if d <= 19: b.set(x, y, z, AIR)  # keep the fighting space clear for a 1.8x boss

# craters from the battle
for cx, cz, r in ((16, 18, 2.5), (31, 28, 3), (22, 33, 2), (30, 15, 2)):
    b.cyl(cx, cz, r, 0, 0, "minecraft:soul_soil")
    b.set(cx, 0, cz, "minecraft:magma_block")

# ---- ring of broken white columns with gold trim around the arena
for i, a in enumerate(range(0, 360, 24)):
    x = round(C + 17 * math.cos(math.radians(a))); z = round(C + 17 * math.sin(math.radians(a)))
    if 75 < a < 105: continue  # the gap for the entrance, south
    h = rnd.choice((2, 3, 5, 7, 9, 10, 11))
    for y in range(1, h + 1): b.set(x, y, z, "minecraft:quartz_pillar[axis=y]")
    if h >= 9:
        b.set(x, h + 1, z, "minecraft:gold_block")
    else:  # fallen top lying next to it
        dx, dz = rnd.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
        for k in range(1, 4): b.set(x + dx * k, 1, z + dz * k, f"minecraft:quartz_pillar[axis={'x' if dx else 'z'}]")

# ---- the broken temple on the north side, where the Celestial Dragons watched the hunt
TX0, TX1, TZ0, TZ1 = 13, 35, 1, 9
b.box(TX0, 0, TZ0, TX1, 2, TZ1, "minecraft:smooth_quartz")  # raised platform
for s in range(3):  # steps down to the arena
    b.box(TX0 + 4, s, TZ1 + 3 - s, TX1 - 4, s, TZ1 + 3 - s, "minecraft:quartz_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
for x in range(TX0 + 1, TX1, 3):
    h = 12 if x < 25 else rnd.choice((4, 6, 8))  # the east half collapsed
    for y in range(3, 3 + h): b.set(x, y, TZ1 - 1, "minecraft:quartz_pillar[axis=y]"); b.set(x, y, TZ0 + 1, "minecraft:quartz_pillar[axis=y]")
for x in range(TX0, 25):  # roof survives only on the west half
    for z in range(TZ0, TZ1 + 1): b.set(x, 15, z, "minecraft:smooth_quartz_slab[type=bottom,waterlogged=false]")
    b.set(x, 15, TZ0, "minecraft:gold_block"); b.set(x, 15, TZ1, "minecraft:gold_block")
for x in range(25, TX1 + 1, 2):  # rubble of the fallen roof
    b.set(x, 3, rnd.randint(TZ0, TZ1), rnd.choice(["minecraft:smooth_quartz", "minecraft:chiseled_quartz_block", "minecraft:gold_block"]))
# the viewing thrones of the World Nobles
for x in (19, 22, 25, 28):
    b.set(x, 3, 4, "minecraft:quartz_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
    b.set(x, 3, 3, "minecraft:gold_block")
b.set(24, 3, 6, "minecraft:red_carpet"); b.set(23, 3, 6, "minecraft:red_carpet"); b.set(25, 3, 6, "minecraft:red_carpet")
b.chest(15, 3, 3, "legendary", "east"); b.chest(33, 3, 3, "treasure", "west")

# ---- scars of Roger, Garp and the Rocks Pirates: soul fire, a broken Marine anchor and a Rocks flag
for x, z in ((10, 24), (38, 24), (24, 38), (14, 32), (34, 32)): b.set(x, 1, z, SOUL_FIRE)
for y in range(1, 6): b.set(40, y, 18, "minecraft:iron_block")  # Garp's half-buried anchor
b.box(38, 1, 18, 42, 1, 18, "minecraft:iron_block")
b.flag(8, 1, 14, h=9, colors=("minecraft:black_wool", "minecraft:white_wool"))
b.bones(5, -1, 36, 9, "x", 5)

# ---- the superboss in the middle of the arena
assert "xebec" in {c['id'] for c in json.load(open(f'{RES}/onepiece/characters.json'))}
b.npc(C, 1, C + 2, "xebec", True)

# ---- save + jigsaw files
size, my = b.save(f'{D}/structure/{NAME}.nbt')
w(f'{D}/worldgen/structure/{NAME}.json', {"type": "minecraft:jigsaw", "biomes": f"#onepiece:has_structure/{NAME}", "step": "surface_structures",
    "spawn_overrides": {"monster": {"bounding_box": "piece", "spawns": []}, "ambient": {"bounding_box": "piece", "spawns": []}}, "terrain_adaptation": "beard_thin", "start_pool": f"onepiece:{NAME}", "size": 1, "max_distance_from_center": 80,
    "use_expansion_hack": False, "project_start_to_heightmap": "WORLD_SURFACE_WG", "start_height": {"absolute": -1 + my}})
w(f'{D}/worldgen/template_pool/{NAME}.json', {"fallback": "minecraft:empty", "elements": [{"weight": 1, "element": {
    "element_type": "minecraft:single_pool_element", "location": f"onepiece:{NAME}", "processors": {"processors": []}, "projection": "rigid"}}]})
w(f'{D}/tags/worldgen/biome/has_structure/{NAME}.json', {"replace": False, "values": [
    "minecraft:plains", "minecraft:meadow", "minecraft:sunflower_plains", "minecraft:savanna", "onepiece:east_blue", "onepiece:dressrosa"]})

def append(path, key, entry):
    d = json.load(open(path))
    if entry not in d[key]: d[key].append(entry)
    w(path, d)
append(f'{D}/worldgen/structure_set/legendary_locations.json', "structures", {"structure": f"onepiece:{NAME}", "weight": 1})
append(f'{D}/tags/worldgen/structure/one_piece_locations.json', "values", f"onepiece:{NAME}")
print(NAME, "size", size)
