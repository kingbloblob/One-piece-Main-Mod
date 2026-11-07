"""Nether and End content: the Impel Down biomes and levels in the Nether, the Holy Land (Red Line heights) and
Void Century ruins in the End. Writes biomes, terrain blob features, structures (.nbt plus jigsaw files),
structure sets, chest loot, tags and names straight into source/. Safe to run again: it only touches its own files
(and re-appends its ids to the shared tag and location lists).

Usage: python3 gen_dimensions.py
"""
import json, math, os, sys
sys.path.insert(0, '/mnt/project-files/one-piece-mod/tools/worldgen')
from kit import *

RES = '/mnt/project-files/one-piece-mod/source/src/main/resources'
D = RES + '/data/onepiece'


def w(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f: json.dump(obj, f, indent=2); f.write('\n')


def append_tag(path, values):
    d = json.load(open(path)) if os.path.exists(path) else {"replace": False, "values": []}
    for v in values:
        if v not in d["values"]: d["values"].append(v)
    w(path, d)


CHARS = {c['id'] for c in json.load(open(f'{RES}/onepiece/characters.json'))}

# ================================================================ terrain blobs
# "netherrack_replace_blobs" swaps one block for another in round clumps, which re-colours the ground of a biome.
def blob(name, target, state, rmin, rmax, count):
    w(f'{D}/worldgen/feature/{name}.json', {"type": "minecraft:netherrack_replace_blobs",
        "radius": {"type": "minecraft:uniform", "min_inclusive": rmin, "max_inclusive": rmax}, "state": state, "target": target})
    w(f'{D}/worldgen/placed_feature/{name}.json', {"feature": f"onepiece:{name}", "placement": [
        {"type": "minecraft:count", "count": count}, {"type": "minecraft:in_square"},
        {"type": "minecraft:height_range", "height": {"type": "minecraft:uniform", "min_inclusive": {"above_bottom": 0}, "max_inclusive": {"below_top": 0}}},
        {"type": "minecraft:biome"}]})
    return f"onepiece:{name}"

NR, ES = "minecraft:netherrack", "minecraft:end_stone"
BLAZING = [blob("blazing_hell_magma", NR, "minecraft:magma_block", 2, 4, 30), blob("blazing_hell_blackstone", NR, "minecraft:blackstone", 3, 6, 45),
           blob("blazing_hell_basalt", NR, "minecraft:basalt", 2, 4, 15)]
FREEZING = [blob("freezing_hell_packed_ice", NR, "minecraft:packed_ice", 3, 7, 60), blob("freezing_hell_snow", NR, "minecraft:snow_block", 2, 5, 45),
            blob("freezing_hell_blue_ice", NR, "minecraft:blue_ice", 1, 3, 12)]
NEWKAMA = [blob("newkama_pink", NR, "minecraft:pink_terracotta", 3, 7, 60), blob("newkama_magenta", NR, "minecraft:magenta_terracotta", 2, 4, 25),
           blob("newkama_shroomlight", NR, "minecraft:shroomlight", 1, 2, 10)]
RED_LINE = [blob("red_line_rock", ES, "minecraft:red_terracotta", 3, 7, 45), blob("red_line_sandstone", ES, "minecraft:smooth_red_sandstone", 2, 5, 25),
            blob("holy_land_calcite", ES, "minecraft:calcite", 2, 4, 12)]
VOID = [blob("void_century_tuff", ES, "minecraft:tuff", 3, 6, 35), blob("void_century_blackstone", ES, "minecraft:polished_blackstone", 2, 4, 15),
        blob("void_century_crying_obsidian", ES, "minecraft:crying_obsidian", 1, 2, 6)]

# ================================================================ biomes
def spawn(t, weight, lo, hi):
    return {"type": t, "count": lo if lo == hi else {"type": "minecraft:uniform", "min_inclusive": lo, "max_inclusive": hi}, "weight": weight}

# Every vanilla Nether feature of the underground_decoration step, in the order vanilla biomes use them.
NETHER_ORDER = ["minecraft:spring_open", "minecraft:spring_delta", "minecraft:patch_fire", "minecraft:patch_soul_fire",
                "minecraft:glowstone_extra", "minecraft:glowstone", "minecraft:brown_mushroom_nether", "minecraft:red_mushroom_nether",
                "minecraft:patch_crimson_roots", "minecraft:ore_magma", "minecraft:spring_closed", "minecraft:spring_closed_double",
                "minecraft:ore_soul_sand", "minecraft:ore_gravel_nether", "minecraft:ore_blackstone", "minecraft:ore_gold_nether",
                "minecraft:ore_gold_deltas", "minecraft:ore_quartz_nether", "minecraft:ore_quartz_deltas",
                "minecraft:ore_ancient_debris_large", "minecraft:ore_debris_small"]

def nether_biome(name, fog, music, ambient, particle, monsters, creatures, blobs, extra):
    attrs = {
        "minecraft:audio/ambient_sounds": {"additions": {"sound": f"minecraft:ambient.{ambient}.additions", "tick_chance": 0.0111},
                                           "loop": f"minecraft:ambient.{ambient}.loop",
                                           "mood": {"block_search_extent": 8, "offset": 2.0, "sound": f"minecraft:ambient.{ambient}.mood", "tick_delay": 6000}},
        "minecraft:audio/background_music": {"default": {"max_delay": 24000, "min_delay": 12000, "sound": f"minecraft:music.nether.{music}"}},
        "minecraft:gameplay/natural_mob_spawns": {"argument": {"spawn_costs": {}, "spawns_by_category": {"creature": creatures, "monster": monsters}}, "modifier": "overlay"},
        "minecraft:visual/fog_color": fog}
    if particle:
        attrs["minecraft:visual/ambient_particles"] = {"argument": [{"particle": {"type": particle[0]}, "probability": particle[1]}], "modifier": "append"}
    features = [[] for _ in range(10)]
    # Vanilla features must keep the same order as in the vanilla Nether biomes, or the game refuses to load
    # the world ("Feature order cycle found"). Our own features go first, then the vanilla ones in NETHER_ORDER.
    vanilla = set(extra) | {"minecraft:ore_gravel_nether", "minecraft:ore_gold_nether", "minecraft:ore_quartz_nether",
                            "minecraft:ore_ancient_debris_large", "minecraft:ore_debris_small"}
    features[7] = blobs + [f for f in NETHER_ORDER if f in vanilla]
    assert vanilla <= set(NETHER_ORDER), vanilla - set(NETHER_ORDER)
    w(f'{D}/worldgen/biome/{name}.json', {"attributes": attrs, "carvers": "minecraft:nether_cave", "downfall": 0.0,
        "effects": {"water_color": "#3f76e4"}, "features": features, "has_precipitation": False, "temperature": 2.0})

STRIDER = [spawn("minecraft:strider", 60, 1, 2)]
nether_biome("impel_down_blazing_hell", "#5a1206", "basalt_deltas", "basalt_deltas", ("minecraft:white_ash", 0.05),
             [spawn("minecraft:magma_cube", 100, 2, 4), spawn("minecraft:blaze", 30, 1, 2), spawn("minecraft:ghast", 20, 1, 1), spawn("minecraft:wither_skeleton", 15, 1, 3)],
             STRIDER, BLAZING, ["minecraft:patch_fire", "minecraft:spring_open", "minecraft:spring_closed", "minecraft:ore_magma", "minecraft:glowstone"])
nether_biome("impel_down_freezing_hell", "#7fa4c4", "soul_sand_valley", "soul_sand_valley", ("minecraft:white_ash", 0.12),
             [spawn("minecraft:stray", 80, 2, 4), spawn("minecraft:skeleton", 30, 2, 3), spawn("minecraft:ghast", 10, 1, 1)],
             STRIDER, FREEZING, ["minecraft:glowstone_extra", "minecraft:glowstone"])
nether_biome("newkama_land", "#b0367f", "crimson_forest", "crimson_forest", ("minecraft:crimson_spore", 0.025),
             [spawn("minecraft:piglin", 40, 2, 4), spawn("minecraft:zombified_piglin", 30, 2, 4), spawn("minecraft:magma_cube", 5, 1, 2)],
             STRIDER, NEWKAMA, ["minecraft:glowstone_extra", "minecraft:glowstone", "minecraft:patch_crimson_roots", "minecraft:spring_open"])

def end_biome(name, fog, sky, blobs, extra, monsters):
    features = [[] for _ in range(10)]
    features[4] = ["minecraft:end_gateway_return"]
    features[7] = blobs
    features[9] = extra
    w(f'{D}/worldgen/biome/{name}.json', {"attributes": {
        "minecraft:gameplay/natural_mob_spawns": {"argument": {"spawn_costs": {}, "spawns_by_category": {"monster": monsters}}, "modifier": "overlay"},
        "minecraft:visual/fog_color": fog, "minecraft:visual/sky_color": sky},
        "carvers": [], "downfall": 0.5, "effects": {"water_color": "#3f76e4"}, "features": features, "has_precipitation": False, "temperature": 0.5})

end_biome("red_line_heights", "#3a1414", "#000000", RED_LINE, [], [spawn("minecraft:enderman", 10, 2, 4)])
end_biome("void_century_ruins", "#14102a", "#000000", VOID, ["minecraft:chorus_plant"], [spawn("minecraft:enderman", 10, 2, 4), spawn("minecraft:endermite", 2, 1, 2)])

NETHER_BIOMES = ["onepiece:impel_down_blazing_hell", "onepiece:impel_down_freezing_hell", "onepiece:newkama_land"]
END_BIOMES = ["onepiece:red_line_heights", "onepiece:void_century_ruins"]
T = RES + '/data/minecraft/tags/worldgen/biome'
append_tag(f'{T}/is_nether.json', NETHER_BIOMES)
append_tag(f'{T}/is_end.json', END_BIOMES)
# wild creatures that also live down here
SP = f'{D}/tags/worldgen/biome/spawns'
append_tag(f'{SP}/basilisk.json', ["onepiece:impel_down_blazing_hell"])
append_tag(f'{SP}/manticore.json', ["onepiece:impel_down_freezing_hell", "onepiece:impel_down_blazing_hell"])
append_tag(f'{SP}/cerberus.json', ["onepiece:impel_down_freezing_hell"])
append_tag(f'{SP}/pacifista.json', ["onepiece:red_line_heights"])

# ================================================================ structures
LOCS = []
def S(name, title, tier, dim, biomes, boss=None, who=""):
    def deco(fn):
        LOCS.append(dict(name=name, title=title, tier=tier, dim=dim, biomes=biomes, build=fn, boss=boss, who=who)); return fn
    return deco

def npc(b, x, y, z, cid, boss=False):
    """Only places characters the mod has; the Story thread adds new ones, then this script is run again."""
    if cid in CHARS: b.npc(x, y, z, cid, boss)
    else: print('  (no character yet, left out:', cid + ')')

def cell(b, x0, z0, wall, door_side="south", w=4, d=4, h=4):
    b.room(x0, 0, z0, x0 + w, h, z0 + d, wall, floor=wall)
    z = z0 + d if door_side == "south" else z0
    for x in range(x0 + 1, x0 + w):
        for y in range(1, h): b.set(x, y, z, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]")
    b.set(x0 + 1, h - 1, z0 + (d // 2), CHAIN)

def foundation(b, x0, z0, x1, z1, s, depth=8):
    """Pillars that hold a platform up over the lava sea."""
    for x, z in ((x0, z0), (x1, z0), (x0, z1), (x1, z1), ((x0 + x1) // 2, z0), ((x0 + x1) // 2, z1)):
        for y in range(-depth, 0): b.set(x, y, z, s)

def island(b, cx, cz, r, top="minecraft:end_stone", depth=14):
    """A floating End island under a building: wide at the top, narrowing to a point."""
    for d in range(depth):
        rr = r * (1 - (d / depth) ** 0.7)
        if rr < 0.6: break
        b.cyl(cx, cz, rr, -d, -d, top if d == 0 else "minecraft:end_stone")

# ---------------------------------------------------------------- Nether: Impel Down's deep levels
@S("blazing_hell_furnace", "Impel Down Level 4: Blazing Hell", "hard", "nether", ["onepiece:impel_down_blazing_hell", "minecraft:basalt_deltas"],
   "magellan", "Magellan (boss, once added), Jailers, Flame Guards")
def _(b):
    N = 30
    foundation(b, 0, 0, N, N, "minecraft:polished_blackstone_bricks")
    b.room(0, 0, 0, N, 12, N, "minecraft:polished_blackstone_bricks", floor="minecraft:blackstone", ceiling="minecraft:basalt[axis=y]")
    # the great boiling cauldron in the middle, with a walkway of bars across
    b.cyl(15, 15, 6, 0, 2, "minecraft:nether_bricks")
    b.cyl(15, 15, 5, 0, 2, "minecraft:lava[level=0]")
    b.cyl(15, 15, 5, -1, -1, "minecraft:nether_bricks")
    for x in range(9, 22): b.set(x, 3, 15, "minecraft:iron_bars[east=true,north=false,south=false,west=true,waterlogged=false]")
    for x in range(9, 22): b.set(x, 2, 15, "minecraft:polished_blackstone_slab[type=top,waterlogged=false]")
    for y in range(4, 12): b.set(15, y, 15, CHAIN)
    # magma floor and fire
    for x, z in ((4, 6), (25, 8), (6, 24), (24, 25), (12, 4), (19, 26)):
        b.box(x - 1, 0, z - 1, x + 1, 0, z + 1, "minecraft:magma_block")
    for x, z in ((3, 15), (27, 15), (15, 3), (15, 27)): b.set(x, 1, z, SOUL_FIRE)
    # prisoner cells on the north wall
    for i in range(4): cell(b, 2 + i * 7, 1, "minecraft:nether_bricks", w=5, d=4)
    b.door(14, 1, N, h=3, w=3)  # gate
    for x, z in ((5, 12), (25, 12), (10, 24), (20, 24)): b.set(x, 11, z, HANG.replace("lantern", "soul_lantern"))
    b.chest(27, 1, 27, "impel_down", "west"); b.chest(3, 1, 27, "impel_down", "east")
    npc(b, 15, 1, 22, "magellan", True)
    b.guards("jailer", ((6, 12), (24, 12), (15, 24)))
    b.guards("flame_guard", ((8, 20), (22, 20)))
    b.guard(15, 1, 8, "warden_jailer")

@S("freezing_hell_cells", "Impel Down Level 5: Freezing Hell", "hard", "nether", ["onepiece:impel_down_freezing_hell"],
   None, "Frozen prisoners, Jailers, Frost Soldiers")
def _(b):
    N = 28
    foundation(b, 0, 0, N, N, "minecraft:packed_ice")
    b.room(0, 0, 0, N, 10, N, "minecraft:packed_ice", floor="minecraft:snow_block", ceiling="minecraft:blue_ice")
    for i in range(4):  # two rows of icy cells
        cell(b, 1 + i * 7, 1, "minecraft:blue_ice", "south", w=5, d=5)
        cell(b, 1 + i * 7, N - 6, "minecraft:blue_ice", "north", w=5, d=5)
    for x in range(5, N, 5): b.set(x, 0, 14, "minecraft:powder_snow")  # hidden snow traps
    for x, z in ((6, 14), (14, 14), (22, 14)):  # icicle pillars
        for y in range(1, 10): b.set(x, y, z, "minecraft:packed_ice")
    for x, z in ((3, 3), (10, 3), (17, 3), (24, 3)):
        b.set(x + 1, 1, z + 1, "minecraft:skeleton_skull[powered=false,rotation=0]")
    for x, z in ((4, 14), (24, 14)): b.set(x, 9, z, HANG)
    b.door(0, 1, 13, h=3, w=3, axis="z"); b.door(N, 1, 13, h=3, w=3, axis="z")
    b.chest(14, 1, 9, "impel_down", "south"); b.chest(14, 1, 19, "impel_down", "north")
    b.guards("frost_soldier", ((10, 12), (18, 16), (4, 17)))
    b.guards("jailer", ((20, 11), (8, 17)))

@S("newkama_land", "Newkama Land (Impel Down Level 5.5)", "medium", "nether", ["onepiece:newkama_land", "minecraft:crimson_forest"],
   None, "Emporio Ivankov (once added) and the Newkama")
def _(b):
    N = 26
    foundation(b, 0, 0, N, N, "minecraft:pink_terracotta")
    b.room(0, 0, 0, N, 9, N, "minecraft:pink_terracotta", floor="minecraft:polished_blackstone", ceiling="minecraft:magenta_terracotta")
    cols = ["minecraft:pink_concrete", "minecraft:magenta_concrete", "minecraft:purple_concrete", "minecraft:light_blue_concrete"]
    for x in range(7, 20):  # disco dance floor
        for z in range(7, 20): b.set(x, 0, z, cols[(x + z) % 4] if (x // 2 + z // 2) % 2 else "minecraft:shroomlight")
    b.box(9, 1, 2, 17, 1, 3, "minecraft:polished_blackstone_bricks")  # stage
    b.box(9, 2, 2, 17, 2, 2, "minecraft:pink_stained_glass")
    for x in (9, 17):
        for y in range(1, 8): b.set(x, y, 2, "minecraft:crimson_stem[axis=y]")
    b.box(2, 1, 21, 9, 1, 22, "minecraft:dark_oak_planks")  # bar
    for x in range(2, 10, 2): b.set(x, 2, 21, "minecraft:brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
    for x in range(3, 10, 3): b.set(x, 1, 24, BARREL)
    b.set(22, 1, 22, "minecraft:cake[bites=0]"); b.box(21, 0, 21, 23, 0, 23, "minecraft:pink_wool")
    for x, z in ((4, 4), (22, 4), (4, 17), (22, 17)): b.set(x, 1, z, "minecraft:jukebox[has_record=false]")
    for x, z in ((6, 6), (20, 6), (6, 20), (20, 20), (13, 13)): b.set(x, 8, z, "minecraft:pearlescent_froglight[axis=y]")
    b.room(19, 0, 1, 25, 5, 6, "minecraft:magenta_terracotta", floor="minecraft:pink_wool")
    bed("pink", 21, 1, 2, b, "south"); bed("magenta", 23, 1, 2, b, "south")
    b.door(20, 1, 6, h=2)
    b.door(12, 1, N, h=3, w=3)
    b.chest(2, 1, 24, "newkama", "east")
    npc(b, 13, 2, 3, "ivankov", False)

@S("eternal_hell_vault", "Impel Down Level 6: Eternal Hell", "legendary", "nether", NETHER_BIOMES + ["minecraft:soul_sand_valley"],
   None, "Jailer Beasts and the most dangerous prisoners")
def _(b):
    N = 32
    foundation(b, 0, 0, N, N, "minecraft:obsidian", depth=10)
    b.room(0, 0, 0, N, 14, N, "minecraft:deepslate_tiles", floor="minecraft:polished_deepslate", ceiling="minecraft:obsidian")
    b.walls(0, 13, 0, N, 13, N, "minecraft:crying_obsidian")
    for i in range(4):  # the deepest cells, sealed with seastone bars and obsidian
        for side in (1, N - 6):
            cell(b, 1 + i * 8, side, "minecraft:obsidian", "south" if side == 1 else "north", w=6, d=5, h=5)
            b.set(4 + i * 8, 1, side + 2, "minecraft:soul_lantern[hanging=false,waterlogged=false]")
    for x in range(3, N - 2, 4):  # corridor of soul fire
        b.set(x, 0, 16, "minecraft:soul_sand"); b.set(x, 1, 16, "minecraft:soul_fire")
    for x, z in ((8, 16), (24, 16)):
        for y in range(1, 14): b.set(x, y, z - 3, "minecraft:polished_blackstone_bricks"); b.set(x, y, z + 3, "minecraft:polished_blackstone_bricks")
    b.box(14, 1, 14, 18, 1, 18, "minecraft:obsidian")  # sealed vault in the middle
    b.chest(16, 2, 16, "eternal_hell", "south")
    b.door(15, 1, 0, h=3, w=3)
    b.guards("warden_jailer", ((6, 12), (26, 20)))
    b.guards("jailer", ((12, 10), (20, 22), (26, 10)))

# ---------------------------------------------------------------- End: the Holy Land and the Void Century
@S("pangaea_castle", "Pangaea Castle (Holy Land Mary Geoise)", "legendary", "end", ["onepiece:red_line_heights"],
   "imu", "Imu (post-game boss, once added), CP0 and Seraphim")
def _(b):
    C = 20
    island(b, C, C, 22, top="minecraft:grass_block[snowy=false]")
    b.cyl(C, C, 19, 1, 1, AIR)
    for a in range(0, 360, 9):  # flower field around the castle
        r = 15 + (a % 3)
        b.set(round(C + r * math.cos(math.radians(a))), 1, round(C + r * math.sin(math.radians(a))),
              "minecraft:lily_of_the_valley" if a % 2 else "minecraft:white_tulip")
    b.room(8, 1, 8, 32, 14, 32, "minecraft:quartz_bricks", floor="minecraft:polished_diorite", ceiling="minecraft:smooth_quartz")
    for x in range(8, 33, 4):
        for z in (8, 32): b.set(x, 15, z, "minecraft:gold_block")
    for z in range(8, 33, 4):
        for x in (8, 32): b.set(x, 15, z, "minecraft:gold_block")
    for cx, cz in ((8, 8), (32, 8), (8, 32), (32, 32)):
        b.tower(cx, cz, 3, 20, "minecraft:quartz_bricks", roof="minecraft:gold_block", y=1, ladder_side=False)
    # the great hall: a red carpet to the Empty Throne
    for z in range(10, 31): b.set(19, 1, z, "minecraft:red_carpet"); b.set(20, 1, z, "minecraft:red_carpet"); b.set(21, 1, z, "minecraft:red_carpet")
    b.box(17, 1, 10, 23, 2, 12, "minecraft:smooth_quartz")
    b.box(19, 3, 10, 21, 3, 10, "minecraft:gold_block"); b.box(19, 4, 10, 21, 8, 10, "minecraft:gold_block")
    b.set(20, 3, 11, "minecraft:quartz_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
    for y in range(4, 13): b.set(20, y, 9, "minecraft:gold_block")
    b.sphere(20, 13, 9, 2, "minecraft:gold_block", hollow=True)
    for x in (12, 28):  # flower wall of straw hats (the room of hats)
        for z in range(14, 30, 3): b.set(x, 3, z, "minecraft:hay_block[axis=y]")
    for x, z in ((12, 14), (28, 14), (12, 26), (28, 26)):
        for y in range(1, 14): b.set(x, y, z, "minecraft:quartz_pillar[axis=y]")
    for x, z in ((15, 18), (25, 18), (15, 26), (25, 26)): b.set(x, 13, z, "minecraft:end_rod[facing=down]")
    b.door(19, 2, 32, h=4, w=3)
    b.chest(10, 2, 10, "celestial", "south"); b.chest(30, 2, 10, "celestial", "south")
    npc(b, 20, 3, 13, "imu", True)
    b.guards("cp0_agent", ((14, 20), (26, 20), (20, 28)), y=2)
    b.guards("seraphim", ((16, 14), (24, 14)), y=2)

@S("celestial_mansion", "Celestial Dragon Mansion (Mary Geoise)", "hard", "end", ["onepiece:red_line_heights"],
   None, "World Nobles' guards: CP agents and a Pacifista")
def _(b):
    island(b, 13, 12, 16, top="minecraft:grass_block[snowy=false]")
    b.house(2, 2, 22, 16, 6, "minecraft:white_concrete", "minecraft:gold_block", floor="minecraft:polished_diorite", y=1,
            corner="minecraft:quartz_pillar[axis=y]")
    b.box(2, 7, 2, 24, 7, 18, "minecraft:smooth_quartz")
    b.house(6, 5, 14, 10, 5, "minecraft:white_concrete", "minecraft:gold_block", floor="minecraft:polished_diorite", y=7)
    for x in range(4, 23, 3): b.set(x, 2, 20, "minecraft:rose_bush[half=lower]"); b.set(x, 3, 20, "minecraft:rose_bush[half=upper]")
    b.box(9, 1, 21, 17, 1, 23, "minecraft:water[level=0]")
    b.cyl(13, 22, 1, 1, 3, "minecraft:quartz_pillar[axis=y]")
    for x in range(4, 10): b.set(x, 2, 4, "minecraft:red_carpet")
    b.set(16, 2, 5, "minecraft:bell[attachment=floor,facing=north,powered=false]")
    bed("red", 18, 2, 4, b, "south")
    b.chest(20, 2, 5, "celestial", "west"); b.chest(10, 8, 7, "celestial", "south")
    b.guards("cp_agent", ((5, 10), (20, 12), (12, 20)), y=2)
    b.guard(13, 2, 14, "pacifista")

@S("void_century_ruins", "Ruins of the Ancient Kingdom (Void Century)", "hard", "end", ["onepiece:void_century_ruins", "minecraft:end_highlands"],
   None, "Ancient Guardians")
def _(b):
    C = 16
    island(b, C, C, 17, top="minecraft:tuff")
    b.cyl(C, C, 14, 1, 1, AIR)
    b.cyl(C, C, 12, 0, 0, "minecraft:polished_tuff")
    b.cyl(C, C, 6, 0, 0, "minecraft:chiseled_tuff_bricks")
    # a ring of broken columns, each a different height
    for i, a in enumerate(range(0, 360, 30)):
        x = round(C + 11 * math.cos(math.radians(a))); z = round(C + 11 * math.sin(math.radians(a)))
        h = (3, 9, 5, 2, 7, 10, 4, 1, 8, 6, 3, 9)[i]
        for y in range(1, h + 1): b.set(x, y, z, "minecraft:tuff_bricks" if y % 3 else "minecraft:chiseled_tuff")
        if h > 6: b.set(x, h + 1, z, "minecraft:tuff_brick_slab[type=bottom,waterlogged=false]")
    # the fallen gate of the Great Kingdom
    for x in (11, 21):
        for y in range(1, 11): b.set(x, y, 4, "minecraft:polished_blackstone_bricks")
    b.box(11, 11, 4, 17, 11, 4, "minecraft:chiseled_polished_blackstone")
    for x in range(18, 24): b.set(x, 1, 2 + (x - 18) // 3, "minecraft:cracked_polished_blackstone_bricks")
    for x, z in ((6, 20), (8, 23), (24, 22), (22, 26)):  # rubble
        b.set(x, 1, z, "minecraft:cobbled_deepslate"); b.set(x + 1, 1, z, "minecraft:mossy_cobblestone")
    b.set(C, 1, C, "minecraft:crying_obsidian")
    for dx, dz in ((3, 0), (-3, 0), (0, 3), (0, -3)): b.set(C + dx, 1, C + dz, "minecraft:soul_lantern[hanging=false,waterlogged=false]")
    # a poneglyph telling what was erased (onepiece:poneglyph, two blocks tall)
    b.set(C, 1, C + 4, "onepiece:poneglyph"); b.set(C, 2, C + 4, "onepiece:poneglyph")
    b.chest(C + 2, 1, C - 5, "void_century", "north")
    b.guards("ancient_guardian", ((C - 6, C), (C + 6, C + 2)))

# ---------------------------------------------------------------- write everything
SETS = {"nether": ("nether_locations", 24, 8, 1408172011), "end": ("end_locations", 22, 9, 1408172012)}
by_set = {k: [] for k in SETS}
# These seven are now built life-size by tools/landmarks (one module each); never overwrite their files here.
LANDMARK_OWNED = {"blazing_hell_furnace", "freezing_hell_cells", "newkama_land", "eternal_hell_vault", "pangaea_castle", "celestial_mansion", "void_century_ruins"}
for loc in LOCS:
    name = loc['name']
    if name in LANDMARK_OWNED:
        by_set[loc['dim']].append(name)
        continue
    b = B(); loc['build'](b)
    size, my = b.save(f'{D}/structure/{name}.nbt')
    st = {"type": "minecraft:jigsaw", "biomes": f"#onepiece:has_structure/{name}", "step": "surface_structures",
          "spawn_overrides": {"monster": {"bounding_box": "piece", "spawns": []}, "ambient": {"bounding_box": "piece", "spawns": []}}, "start_pool": f"onepiece:{name}", "size": 1, "max_distance_from_center": 80, "use_expansion_hack": False}
    if loc['dim'] == "nether":
        # Floor just above the lava sea (y 32); beard_box clears the netherrack around the building.
        st["start_height"] = {"absolute": 33 + my}; st["terrain_adaptation"] = "beard_box"
    else:
        # Each End building sits on its own floating island at a fixed height, so it never lands in the void.
        st["start_height"] = {"absolute": 62 + my}; st["terrain_adaptation"] = "beard_thin"
    w(f'{D}/worldgen/structure/{name}.json', st)
    w(f'{D}/worldgen/template_pool/{name}.json', {"fallback": "minecraft:empty", "elements": [{"weight": 1, "element": {
        "element_type": "minecraft:single_pool_element", "location": f"onepiece:{name}", "processors": {"processors": []}, "projection": "rigid"}}]})
    w(f'{D}/tags/worldgen/biome/has_structure/{name}.json', {"replace": False, "values": loc['biomes']})
    by_set[loc['dim']].append(name)
    print(f"{name}: size {size}, {sum(1 for e in b.entities if e[0] != 'onepiece:character')} guards")
for dim, (sname, spacing, sep, salt) in SETS.items():
    w(f'{D}/worldgen/structure_set/{sname}.json', {
        "structures": [{"structure": f"onepiece:{n}", "weight": 1} for n in by_set[dim]],
        "placement": {"type": "minecraft:random_spread", "spacing": spacing, "separation": sep, "salt": salt}})

# shared location lists (Sea Charts, Vivre Cards, the story)
append_tag(f'{D}/tags/worldgen/structure/one_piece_locations.json', [f"onepiece:{l['name']}" for l in LOCS])
lp = f'{RES}/onepiece/locations.json'
locs = json.load(open(lp))
for l in LOCS: locs["locations"][l['name']] = l['title']
w(lp, locs)

# ---------------------------------------------------------------- chest loot (26.3 format)
def item(name, weight, lo=1, hi=1, extra=None):
    e = {"type": "minecraft:item", "name": name, "weight": weight}
    mods = []
    if hi > 1 or lo > 1: mods.append({"type": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": lo, "max": hi}})
    if extra: mods.append(extra)
    if mods: e["modifier"] = mods
    return e
def table(*pools):
    return {"type": "minecraft:chest", "pools": [{"rolls": {"type": "minecraft:uniform", "min": lo, "max": hi}, "entries": es} for lo, hi, es in pools]}
enchant = {"type": "minecraft:enchant_randomly"}
BERRY = "onepiece:berry"
L = f'{D}/loot_table/chests'
w(f'{L}/impel_down.json', table((4, 7, [item(BERRY, 10, 6, 20), item("onepiece:seastone_cuffs", 4, 1, 2), item("onepiece:raw_seastone", 6, 1, 4),
    item("onepiece:sulfur", 8, 2, 6), item("minecraft:magma_cream", 6, 1, 4), item("minecraft:blaze_rod", 5, 1, 3),
    item("minecraft:iron_ingot", 8, 2, 6), item("minecraft:golden_apple", 2), item("minecraft:netherite_scrap", 1)])))
w(f'{L}/newkama.json', table((4, 8, [item("minecraft:cake", 4), item("minecraft:cookie", 8, 4, 12), item("minecraft:potion", 6, 1, 2, {"type": "minecraft:set_potion", "id": "minecraft:healing"}),
    item("minecraft:potion", 4, 1, 1, {"type": "minecraft:set_potion", "id": "minecraft:strength"}), item("minecraft:glistering_melon_slice", 5, 1, 3),
    item("minecraft:pink_dye", 6, 2, 6), item(BERRY, 8, 6, 18), item("minecraft:golden_apple", 2), item("minecraft:music_disc_pigstep", 1)])))
w(f'{L}/eternal_hell.json', table((6, 9, [item(BERRY, 10, 30, 64), item("minecraft:netherite_scrap", 5, 1, 3), item("minecraft:diamond", 6, 2, 5),
    item("onepiece:seastone_ingot", 5, 2, 4), item("onepiece:seastone_jitte", 2), item("minecraft:enchanted_golden_apple", 2),
    item("minecraft:totem_of_undying", 2), item("onepiece:kokuto_blade", 1)]), (2, 2, [item("minecraft:enchanted_book", 1, 1, 1, enchant)])))
w(f'{L}/celestial.json', table((5, 9, [item(BERRY, 10, 40, 64), item("minecraft:gold_block", 8, 2, 6), item("minecraft:diamond", 6, 2, 6),
    item("onepiece:sea_pearl", 6, 2, 6), item("minecraft:enchanted_golden_apple", 2), item("minecraft:netherite_ingot", 2),
    item("minecraft:elytra", 1), item("onepiece:shandora_gold_ingot", 6, 2, 6)]), (1, 2, [item("minecraft:enchanted_book", 1, 1, 1, enchant)])))
w(f'{L}/void_century.json', table((4, 8, [item("onepiece:kraken_ink", 6, 1, 3), item("minecraft:paper", 8, 4, 12), item("onepiece:shandora_gold_ingot", 6, 2, 5),
    item("minecraft:ancient_debris", 3, 1, 2), item("minecraft:echo_shard", 4, 1, 3), item("minecraft:diamond", 5, 1, 4),
    item("minecraft:enchanted_golden_apple", 1), item(BERRY, 8, 20, 50)]), (1, 1, [item("minecraft:enchanted_book", 1, 1, 1, enchant)])))

# ---------------------------------------------------------------- names
lang = f'{RES}/assets/onepiece_world/lang/en_us.json'
names = json.load(open(lang))
names.update({
    "biome.onepiece.impel_down_blazing_hell": "Impel Down: Blazing Hell",
    "biome.onepiece.impel_down_freezing_hell": "Impel Down: Freezing Hell",
    "biome.onepiece.newkama_land": "Newkama Land",
    "biome.onepiece.red_line_heights": "Red Line Heights (Holy Land)",
    "biome.onepiece.void_century_ruins": "Void Century Ruins"})
w(lang, names)
print("structures:", {k: len(v) for k, v in by_set.items()})

# Put the island look (fog, particles, island music) back on the biomes we just rewrote.
import subprocess as _sp, sys as _sys, os as _os
_sp.run([_sys.executable, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "islands", "island_look.py")])
