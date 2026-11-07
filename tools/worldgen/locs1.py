"""Boss lairs (one per boss character)."""
from kit import *
LOCS = []
def L(name, title, tier, biomes, place, boss=None, who=""):
    def deco(fn):
        LOCS.append(dict(name=name, title=title, tier=tier, biomes=biomes, place=place, build=fn, boss=boss, who=who)); return fn
    return deco
BEACH = ["#minecraft:is_beach"]
PLAINS = ["minecraft:plains", "minecraft:sunflower_plains", "onepiece:east_blue"]
OCEAN = ["minecraft:ocean", "minecraft:lukewarm_ocean", "minecraft:warm_ocean", "minecraft:cold_ocean", "onepiece:fishman_reef"]
DEEP = ["minecraft:deep_ocean", "minecraft:deep_lukewarm_ocean", "minecraft:deep_cold_ocean"]

def ground(b, x0, z0, x1, z1, s="minecraft:grass_block[snowy=false]", y=0):
    b.box(x0, y, z0, x1, y, z1, s)

# ============================================================ EASY lairs
@L("buggy_big_top", "Buggy's Big Top (Orange Town)", "easy", BEACH + PLAINS + ["onepiece:sabaody"], "land", "buggy", "Buggy (boss) and Buggy Pirates")
def _(b):
    ground(b, 0, 0, 20, 20, "minecraft:coarse_dirt")
    for y in range(1, 9):  # striped circus tent
        r = 9 - max(0, y - 4) * 1.6
        for i in range(0, 360, 6):
            a = math.radians(i); x = round(10 + r * math.cos(a)); z = round(10 + r * math.sin(a))
            b.set(x, y, z, "minecraft:red_wool" if (i // 30) % 2 else "minecraft:white_wool")
    b.cyl(10, 10, 8.2, 1, 3, AIR); b.disk(10, 9, 10, 2, "minecraft:red_wool")
    for y in range(9, 13): b.set(10, y, 10, FENCE.format("oak"))
    b.box(10, 11, 11, 10, 12, 13, "minecraft:blue_wool")
    b.box(10, 1, 1, 11, 3, 2, AIR)
    b.cyl(10, 10, 3, 1, 1, "minecraft:yellow_concrete")  # ring
    for x, z in ((4, 4), (16, 16)): b.set(x, 1, z, "minecraft:dispenser[facing=up,triggered=false]")
    b.chest(15, 1, 6, "easy", "west")
    b.npc(10, 2, 10, "buggy", True)
    b.guards("buggy_pirate", ((6, 8), (14, 12), (8, 14)))

@L("loguetown", "Loguetown Execution Square", "medium", PLAINS + BEACH, "land", "smoker", "Smoker (boss), Marines")
def _(b):
    ground(b, 0, 0, 24, 24, "minecraft:stone_bricks")
    b.box(9, 1, 9, 15, 4, 15, "minecraft:dark_oak_planks"); b.box(10, 1, 10, 14, 4, 14, AIR)  # scaffold
    b.box(9, 5, 9, 15, 5, 15, "minecraft:dark_oak_planks")
    for x in (10, 14):
        for y in range(6, 11): b.set(x, y, 12, log("dark_oak"))
    b.box(10, 11, 12, 14, 11, 12, log("dark_oak", "x"))
    for i in range(5): b.set(12, 1 + i, 16 + i if i < 4 else 20, "minecraft:dark_oak_planks")
    for i in range(1, 5): b.set(12, i, 15 + i, "minecraft:dark_oak_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
    b.house(1, 1, 7, 6, 4, "minecraft:white_terracotta", "minecraft:blue_terracotta")
    b.house(17, 1, 7, 6, 4, "minecraft:white_terracotta", "minecraft:blue_terracotta")
    b.house(1, 17, 7, 7, 4, "minecraft:bricks", "minecraft:dark_oak_planks")
    b.chest(3, 1, 3, "marine")
    b.npc(12, 6, 13, "smoker", True)
    b.guards("marine", ((5, 12), (19, 12), (12, 22)))
    b.guards("marine_rifle", ((20, 20), (4, 22)))

@L("rain_dinners", "Rain Dinners (Alabasta)", "medium", ["onepiece:alabasta", "minecraft:desert"], "land", "crocodile", "Crocodile (boss), Baroque Works agents")
def _(b):
    N = 16
    b.box(0, 0, 0, N, 0, N, "minecraft:smooth_sandstone")
    b.walls(1, 1, 1, N - 1, 7, N - 1, "minecraft:cut_sandstone"); b.walls(1, 4, 1, N - 1, 4, N - 1, "minecraft:chiseled_sandstone")
    b.box(2, 1, 2, N - 2, 7, N - 2, AIR); b.box(1, 8, 1, N - 1, 8, N - 1, "minecraft:smooth_sandstone")
    b.sphere(8, 9, 8, 6, "minecraft:sandstone", hollow=True, upper=True); b.set(8, 15, 8, "minecraft:gold_block")
    for x in range(4, 13): b.set(x, 9, 1, "minecraft:gold_block")
    b.box(7, 1, 1, 9, 3, 1, AIR)
    for x, z in ((4, 5), (12, 5), (4, 11)): b.set(x, 0, z, "minecraft:emerald_block"); b.set(x, 1, z, "minecraft:green_carpet")
    b.box(9, 0, 9, 13, 0, 13, "minecraft:water[level=0]")
    b.chest(13, 1, 3, "treasure", "west")
    b.npc(8, 1, 7, "crocodile", True)
    b.guards("baroque_agent", ((4, 8), (12, 8), (8, 12)))

@L("kamazo_hideout", "Killer's Hideout (Wano)", "medium", ["onepiece:wano", "minecraft:cherry_grove"], "land", "killer", "Killer (boss), Gifters")
def _(b):
    ground(b, 0, 0, 14, 14, "minecraft:gravel")
    b.house(2, 2, 11, 9, 4, "minecraft:dark_oak_planks", "minecraft:deepslate_tiles", corner=log("dark_oak"))
    for x in range(2, 13, 2): b.set(x, 1, 13, "minecraft:bamboo_block[axis=y]"); b.set(x, 2, 13, "minecraft:bamboo_block[axis=y]")
    b.set(4, 1, 4, "minecraft:grindstone[face=floor,facing=north]")
    b.chest(11, 1, 4, "wano", "west")
    b.npc(7, 1, 6, "killer", True)
    b.guards("gifter", ((5, 12), (9, 12)))

@L("straw_shrine", "Hawkins' Straw Shrine", "medium", ["minecraft:swamp", "minecraft:dark_forest", "onepiece:sabaody", "onepiece:thriller_bark"], "land", "hawkins", "Basil Hawkins (boss), Pirates")
def _(b):
    ground(b, 0, 0, 16, 16, "minecraft:podzol[snowy=false]")
    b.cyl(8, 8, 5, 1, 5, "minecraft:hay_block[axis=y]", hollow=True); b.disk(8, 6, 8, 5, "minecraft:hay_block[axis=y]")
    for i in range(4): b.disk(8, 7 + i, 8, 4 - i, "minecraft:hay_block[axis=y]")
    b.box(8, 1, 3, 8, 2, 3, AIR)
    for x, z in ((2, 2), (14, 2), (2, 14), (14, 14)):  # straw dolls
        b.box(x, 1, z, x, 2, z, "minecraft:hay_block[axis=y]"); b.set(x, 3, z, "minecraft:carved_pumpkin[facing=south]")
    b.set(8, 1, 8, "minecraft:enchanting_table"); b.set(6, 1, 8, "minecraft:candle[candles=3,lit=true,waterlogged=false]")
    b.chest(10, 1, 9, "medium", "west")
    b.npc(8, 1, 10, "hawkins", True)
    b.guards("pirate", ((3, 8), (13, 8)))

@L("victoria_punk", "Victoria Punk (Kid's scrap ship)", "hard", BEACH + ["minecraft:stony_shore"], "land", "kid", "Eustass Kid (boss), Kid Pirates")
def _(b):
    dy = b.ship(0, 0, 0, 30, 11, hull="minecraft:iron_block", deck="minecraft:cut_copper", masts=((14, 14),), sail="minecraft:red_wool",
                flag=("minecraft:red_wool", "minecraft:black_wool"), cabin=(8, 4, "minecraft:exposed_copper"))
    for x in range(2, 28, 4): b.set(x, dy + 1, 5, CHAIN); b.set(x, dy + 2, 5, "minecraft:anvil[facing=north]")
    b.box(24, dy + 1, 4, 26, dy + 3, 6, "minecraft:weathered_cut_copper")
    b.chest(3, dy + 1, 5, "hard", "east")
    b.npc(18, dy + 1, 5, "kid", True)
    b.guards("pirate", ((10, 4), (12, 6), (20, 4), (22, 6)), y=dy + 1)
    b.guards("pirate_gunner", ((26, 5),), y=dy + 4)

@L("shandora", "Shandora Sky Ruins", "hard", ["onepiece:skypiea", "#minecraft:is_jungle", "minecraft:ocean", "minecraft:warm_ocean"], "sky", "enel", "Enel (boss), Sky Priests")
def _(b):
    R = 15
    for x in range(-R, R + 1):
        for z in range(-R, R + 1):
            d = math.hypot(x, z)
            if d > R: continue
            for y in range(-int((1 - d / R) * 7) - 1, 1): b.set(x, y, z, "onepiece:island_cloud")
            if d < R - 3 and (x * 7 + z * 13) % 11 == 0: b.set(x, 1, z, "minecraft:short_grass")
    for (x, z, h) in ((-9, -3, 5), (-9, 3, 3), (-4, -9, 4), (4, -9, 2), (9, 3, 5), (9, -3, 4), (-6, 8, 3)):
        for y in range(1, h + 1): b.set(x, y, z, "minecraft:cut_sandstone")
        b.set(x, h + 1, z, "minecraft:gold_block")
    b.box(-2, 1, -2, 2, 1, 2, "minecraft:gold_block")
    for x, z in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
        for y in range(2, 10): b.set(x, y, z, "minecraft:cut_sandstone")
    b.box(-2, 10, -2, 2, 10, 2, "minecraft:gold_block"); b.box(-1, 11, -1, 1, 11, 1, "minecraft:gold_block")
    b.set(0, 9, 0, "minecraft:bell[attachment=ceiling,facing=north,powered=false]")
    b.chest(0, 2, 2, "sky_treasure", "south")
    b.npc(0, 1, 7, "enel", True)
    b.guards("sky_priest", ((-7, 0), (7, 0), (0, -7)))

@L("thriller_bark", "Thriller Bark", "hard", OCEAN + DEEP, "sea", "moria", "Gecko Moria (boss), Zombie Soldiers")
def _(b):
    dy = b.ship(0, 0, 0, 44, 25, hull="minecraft:blackstone", deck="minecraft:podzol[snowy=false]", masts=((38, 18),),
                sail="minecraft:gray_wool", flag=("minecraft:black_wool", "minecraft:purple_wool"), depth=5)
    b.room(10, dy, 6, 30, dy + 9, 18, "minecraft:deepslate_bricks", floor="minecraft:dark_oak_planks")  # mansion
    b.roof(9, 5, 31, 19, dy + 10, "minecraft:deepslate_tiles", top="minecraft:deepslate_tiles")
    b.tower(12, 12, 3, 16, "minecraft:deepslate_bricks", "minecraft:purple_terracotta", y=dy)
    b.door(30, dy + 1, 12, h=3, w=2, axis="z")
    for x in range(12, 30, 4): b.set(x, dy + 5, 6, pane("purple")); b.set(x, dy + 5, 18, pane("purple"))
    for x, z in ((4, 12), (6, 8), (6, 16), (34, 8), (34, 16)): b.tree(x, dy + 1, z, 4, "dark_oak", 1.8)
    for x, z in ((16, 10), (24, 14)): b.set(x, dy + 1, z, SOUL_LANTERN)
    b.chest(27, dy + 1, 15, "hard", "west")
    b.npc(20, dy + 1, 12, "moria", True)
    b.guards("zombie_soldier", ((15, 9), (15, 15), (25, 9), (25, 15), (36, 12), (8, 12)), y=dy + 1)

@L("tower_of_justice", "Enies Lobby: Tower of Justice", "hard", BEACH + PLAINS + ["minecraft:savanna", "onepiece:jaya"], "land", "lucci", "Rob Lucci (boss), CP9 agents")
def _(b):
    ground(b, 0, 0, 26, 26, "minecraft:stone_bricks")
    b.box(0, 1, 0, 26, 2, 0, "minecraft:stone_brick_wall[east=low,north=none,south=none,up=true,waterlogged=false,west=low]")
    b.room(6, 0, 6, 20, 14, 20, "minecraft:polished_andesite", floor="minecraft:polished_diorite")
    for f in (5, 10): b.box(7, f, 7, 19, f, 19, "minecraft:polished_andesite"); b.box(8, f, 8, 9, f, 9, AIR)
    for y in range(1, 14): b.set(8, y, 7, ladder("south"))
    b.room(9, 14, 9, 17, 22, 17, "minecraft:polished_andesite")
    b.roof(8, 8, 18, 18, 23, "minecraft:dark_prismarine", top="minecraft:gold_block")
    b.door(13, 1, 20, h=3, w=1)
    for y in (3, 8, 12, 18):
        for i in (9, 13, 17): b.set(i, y, 6, PANE); b.set(i, y, 20, PANE)
    b.flag(2, 1, 2, h=12, colors=("minecraft:white_wool", "minecraft:blue_wool"), skull=False)
    b.chest(16, 15, 15, "hard", "west")
    b.npc(13, 15, 13, "lucci", True)
    b.guards("cp_agent", ((10, 10), (16, 16), (13, 3), (4, 13)), y=1)
    b.guards("marine_rifle", ((12, 11), (14, 11)), y=11)

@L("dressrosa_palace", "Dressrosa Royal Palace (the Birdcage)", "legendary", ["onepiece:dressrosa", "minecraft:sunflower_plains", "minecraft:savanna"], "land", "doflamingo", "Doflamingo (boss), Donquixote Pirates, Gladiators")
def _(b):
    b.box(0, 0, 0, 40, 6, 40, "minecraft:stone_bricks")  # plateau
    b.room(8, 6, 8, 32, 18, 32, "minecraft:pink_terracotta", floor="minecraft:polished_diorite")
    b.box(9, 12, 9, 31, 12, 31, "minecraft:pink_terracotta"); b.box(10, 12, 10, 11, 12, 11, AIR)
    for y in range(7, 13): b.set(10, y, 9, ladder("south"))
    for cx, cz in ((8, 8), (32, 8), (8, 32), (32, 32)):
        b.tower(cx, cz, 3, 22, "minecraft:white_terracotta", "minecraft:pink_concrete", y=6)
    b.door(20, 7, 32, h=4, w=3)
    for i in range(0, 41, 5):  # the Birdcage: strings from the sky
        for y in range(7, 40, 2):
            for (x, z) in ((i, 0), (i, 40), (0, i), (40, i)):
                b.set(x, y, z, "minecraft:white_stained_glass_pane[east=false,north=false,south=false,west=false,waterlogged=false]")
    b.box(16, 13, 16, 24, 13, 24, "minecraft:pink_carpet")
    b.set(20, 13, 26, "minecraft:gold_block"); b.set(20, 14, 26, "minecraft:pink_wool")  # throne
    b.chest(12, 13, 28, "legendary", "east"); b.chest(28, 7, 12, "treasure", "west")
    b.npc(20, 13, 22, "doflamingo", True)
    b.guards("donquixote", ((14, 10), (26, 10), (14, 30), (26, 30)), y=7)
    b.guards("gladiator", ((20, 16), (12, 20), (28, 20)), y=7)
    b.guards("cp_agent", ((16, 14), (24, 14)), y=13)

@L("corrida_colosseum", "Corrida Colosseum", "hard", ["onepiece:dressrosa", "minecraft:savanna", "minecraft:plains", "onepiece:alabasta"], "land", "fujitora", "Fujitora (boss), Gladiators")
def _(b):
    b.cyl(17, 17, 17, 0, 0, "minecraft:sandstone")
    for t in range(6): b.cyl(17, 17, 17 - t, 1 + t, 1 + t, "minecraft:smooth_sandstone", hollow=True)
    b.cyl(17, 17, 17, 1, 9, "minecraft:cut_sandstone", hollow=True)
    b.cyl(17, 17, 10, 1, 1, "minecraft:sand")
    for a in range(0, 360, 45):
        r = math.radians(a); b.set(round(17 + 16 * math.cos(r)), 10, round(17 + 16 * math.sin(r)), "minecraft:red_banner[rotation=0]")
    b.box(16, 1, 0, 18, 4, 1, AIR)
    b.chest(17, 1, 31, "hard", "north")
    b.npc(17, 1, 17, "fujitora", True)
    b.guards("gladiator", ((12, 14), (22, 14), (12, 20), (22, 20)))

@L("mirror_hall", "Katakuri's Mirror Hall (Totto Land)", "hard", ["onepiece:whole_cake", "minecraft:meadow", "minecraft:flower_forest"], "land", "katakuri", "Charlotte Katakuri (boss), Homies")
def _(b):
    ground(b, 0, 0, 22, 22, "minecraft:white_terracotta")
    b.room(1, 0, 1, 21, 9, 21, "minecraft:brown_terracotta", floor="minecraft:white_concrete")
    for x in range(3, 20, 4):
        for z in range(3, 20, 4):
            b.box(x, 1, z, x, 6, z, "minecraft:glass")  # mirrors
    for i in range(3):  # mochi blobs
        b.sphere(5 + i * 6, 1, 17 - i * 5, 1.8, "minecraft:white_concrete_powder", upper=True)
    b.door(11, 1, 21, h=3, w=1)
    b.roof(0, 0, 22, 22, 10, "minecraft:pink_terracotta", top="minecraft:pink_terracotta")
    b.chest(3, 1, 3, "candy", "south")
    b.npc(11, 1, 9, "katakuri", True)
    b.guards("homie", ((6, 14), (16, 14), (11, 18)))

@L("flame_fortress", "King's Flame Fortress", "hard", ["onepiece:onigashima", "onepiece:punk_hazard_burning", "minecraft:badlands", "onepiece:wano"], "land", "king", "King (boss), Gifters, Flame Guards")
def _(b):
    ground(b, 0, 0, 20, 20, "minecraft:blackstone")
    b.room(3, 0, 3, 17, 10, 17, "minecraft:polished_blackstone_bricks", floor="minecraft:blackstone")
    b.tower(10, 10, 3, 20, "minecraft:polished_blackstone_bricks", "minecraft:red_nether_bricks", y=10, ladder_side=False)
    for x, z in ((5, 5), (15, 5), (5, 15), (15, 15)): b.set(x, 0, z, "minecraft:magma_block"); b.set(x, 1, z, CAMPFIRE)
    b.box(8, 0, 8, 12, 0, 12, "minecraft:lava[level=0]")
    b.box(9, 1, 3, 11, 3, 3, AIR)
    b.chest(15, 1, 10, "hard", "west")
    b.npc(10, 1, 14, "king", True)
    b.guards("gifter", ((6, 10), (14, 6)))
    b.guards("flame_guard", ((6, 14), (14, 14)))

@L("onigashima", "Onigashima Skull Dome", "legendary", ["onepiece:onigashima", "onepiece:wano", "minecraft:stony_shore", "minecraft:eroded_badlands"], "land", "kaido", "Kaido (boss), Headliners, Gifters, War Beasts")
def _(b):
    b.box(0, 0, 0, 44, 0, 44, "minecraft:blackstone")
    b.sphere(22, 4, 22, 18, "minecraft:bone_block[axis=y]", hollow=True, upper=True, ry=20)  # the skull
    b.cyl(22, 22, 18, 1, 4, "minecraft:bone_block[axis=y]", hollow=True)
    b.box(4, 0, 4, 40, 0, 40, "minecraft:polished_blackstone")
    for ex in (14, 30):  # eye sockets
        b.sphere(ex, 14, 4, 4, AIR); b.sphere(ex, 14, 5, 3, "minecraft:black_concrete", hollow=True)
    b.box(18, 1, 2, 26, 8, 6, AIR)  # mouth gate
    for x in range(18, 27, 2): b.set(x, 8, 4, "minecraft:white_concrete"); b.set(x, 7, 4, "minecraft:white_concrete")
    for hx in (8, 36):  # horns
        for i in range(10): b.sphere(hx + (i // 3) * (1 if hx > 22 else -1), 22 + i, 18, 2.5 - i * 0.2, "minecraft:quartz_block")
    b.box(10, 12, 10, 34, 12, 34, "minecraft:dark_oak_planks"); b.box(12, 12, 12, 14, 12, 14, AIR)  # live floor
    for y in range(1, 12): b.set(13, y, 11, ladder("south"))
    for x, z in ((12, 24), (32, 24), (22, 36)): b.set(x, 1, z, CAMPFIRE)
    b.chest(22, 13, 32, "legendary", "north"); b.chest(10, 1, 30, "hard", "east")
    b.npc(22, 13, 24, "kaido", True)
    b.guards("headliner", ((16, 18), (28, 18), (22, 30)))
    b.guards("gifter", ((12, 10), (32, 10), (12, 34), (32, 34), (22, 12)))
    b.guards("gifter", ((16, 28), (28, 28)), y=13)
    b.guards("war_beast", ((22, 18),))

@L("whole_cake_chateau", "Whole Cake Chateau", "legendary", ["onepiece:whole_cake", "minecraft:meadow", "minecraft:flower_forest"], "land", "big_mom", "Big Mom (boss), Homies, Chess Soldiers")
def _(b):
    layers = [(20, "minecraft:brown_terracotta", 6), (16, "minecraft:pink_terracotta", 6), (12, "minecraft:white_terracotta", 6), (8, "minecraft:pink_concrete", 5)]
    y = 0
    for r, mat, h in layers:
        b.cyl(22, 22, r, y, y + h - 1, mat, hollow=True)
        b.disk(22, y, 22, r, mat)
        for a in range(0, 360, 20):  # frosting drips and candles
            t = math.radians(a); b.set(round(22 + r * math.cos(t)), y + h - 2, round(22 + r * math.sin(t)), "minecraft:white_concrete")
        y += h
    b.disk(22, y, 22, 8, "minecraft:pink_concrete")
    for a in range(0, 360, 45):
        t = math.radians(a); x, z = round(22 + 6 * math.cos(t)), round(22 + 6 * math.sin(t))
        b.box(x, y + 1, z, x, y + 3, z, "minecraft:red_concrete"); b.set(x, y + 4, z, "minecraft:candle[candles=1,lit=true,waterlogged=false]")
    b.box(21, 1, 1, 23, 4, 2, AIR)
    for (fy, r) in ((6, 15), (12, 11), (18, 7)): b.disk(22, fy, 22, r, "minecraft:white_terracotta")
    for yy in range(1, 20): b.set(22, yy, 21, ladder("north"))  # ladder up through every floor
    b.box(22, 1, 22, 22, 19, 22, "minecraft:white_terracotta")  # center pillar holds the ladder
    b.chest(16, 19, 22, "legendary", "east"); b.chest(30, 1, 22, "candy", "west")
    b.npc(22, 19, 26, "big_mom", True)
    b.guards("homie", ((12, 12), (32, 12), (12, 32), (32, 32), (22, 8)))
    b.guards("homie", ((16, 16), (28, 28)), y=7)
    b.guards("donquixote", ((18, 18), (26, 26)), y=13)

@L("moby_dick", "Moby Dick (Whitebeard's flagship)", "legendary", OCEAN + DEEP, "sea", "whitebeard", "Whitebeard (boss), Whitebeard Pirates, Marco")
def _(b):
    dy = b.ship(0, 0, 0, 52, 21, hull="minecraft:white_concrete", deck="minecraft:spruce_planks", masts=((14, 22), (28, 26), (40, 20)),
                sail="minecraft:white_wool", flag=("minecraft:black_wool", "minecraft:white_wool"), cabin=(10, 6, "minecraft:white_terracotta"), depth=6)
    b.sphere(52, dy - 2, 10, 6, "minecraft:white_concrete", ry=5)  # whale head
    b.set(56, dy, 7, "minecraft:black_concrete"); b.set(56, dy, 13, "minecraft:black_concrete")
    b.box(57, dy - 3, 9, 57, dy - 3, 11, "minecraft:red_concrete")
    b.chest(4, dy + 1, 10, "legendary", "east"); b.chest(4, dy + 1, 12, "treasure", "east")
    b.set(30, dy + 1, 10, "minecraft:gold_block")
    b.npc(30, dy + 2, 10, "whitebeard", True)
    b.npc(20, dy + 1, 8, "marco", False)
    b.guards("whitebeard_pirate", ((16, 7), (16, 13), (24, 7), (24, 13), (36, 8), (36, 12), (44, 10)), y=dy + 1)

@L("hachinosu", "Hachinosu, Pirate Island", "legendary", BEACH + ["minecraft:stony_shore", "onepiece:onigashima", "onepiece:red_line"], "land", "blackbeard", "Blackbeard (boss), Blackbeard Pirates")
def _(b):
    b.sphere(20, 0, 20, 20, "minecraft:blackstone", upper=True, ry=26)  # the skull rock
    b.sphere(20, 0, 20, 17, AIR, upper=True, ry=22)
    b.box(2, 0, 2, 38, 0, 38, "minecraft:honeycomb_block")  # "beehive" floor
    for ex in (13, 27): b.sphere(ex, 16, 3, 3.5, AIR)
    b.box(16, 1, 0, 24, 9, 4, AIR)
    for (x, z) in ((8, 10), (32, 10), (8, 30), (32, 30)):  # beehive huts
        b.sphere(x, 1, z, 3, "minecraft:honeycomb_block", hollow=True, upper=True); b.set(x, 1, z - 3, AIR); b.set(x, 2, z - 3, AIR)
    b.box(17, 1, 22, 23, 4, 26, "minecraft:obsidian"); b.box(18, 2, 23, 22, 4, 25, AIR)
    b.set(20, 5, 24, "minecraft:crying_obsidian")
    b.chest(20, 2, 25, "legendary", "north"); b.chest(8, 1, 30, "treasure", "north")
    b.npc(20, 1, 18, "blackbeard", True)
    b.guards("blackbeard_pirate", ((12, 14), (28, 14), (12, 26), (28, 26), (20, 8)))
    b.guards("pirate_gunner", ((6, 20), (34, 20)))
    b.guards("war_beast", ((20, 30),))

@L("kuraigana_castle", "Kuraigana Castle (Mihawk)", "legendary", ["minecraft:dark_forest", "onepiece:thriller_bark", "minecraft:swamp", "minecraft:pale_garden"], "land", "mihawk", "Dracule Mihawk (boss), Humandrills")
def _(b):
    ground(b, 0, 0, 30, 30, "minecraft:coarse_dirt")
    b.room(5, 0, 5, 25, 12, 25, "minecraft:cobbled_deepslate", floor="minecraft:deepslate_tiles")
    for x in range(5, 26, 3):  # ruined top
        b.set(x, 13, 5, "minecraft:cobbled_deepslate"); b.set(x, 13, 25, "minecraft:cobbled_deepslate")
    for x, z in ((9, 12), (16, 20), (20, 8)): b.box(x, 12, z, x + 2, 12, z + 2, AIR)
    for cx, cz in ((5, 5), (25, 5), (5, 25), (25, 25)): b.tower(cx, cz, 3, 18, "minecraft:cobbled_deepslate", "minecraft:deepslate_tiles")
    b.door(15, 1, 25, h=4, w=2)
    for x, z in ((10, 10), (20, 20), (10, 20)): b.set(x, 1, z, SOUL_LANTERN)
    b.box(13, 1, 8, 17, 1, 8, "minecraft:red_carpet"); b.set(15, 1, 7, "minecraft:dark_oak_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
    for x, z in ((2, 14), (28, 16), (14, 2)): b.tree(x, 1, z, 6, "pale_oak", 2)
    b.chest(22, 1, 8, "legendary", "west")
    b.npc(15, 1, 12, "mihawk", True)
    b.guards("humandrill", ((9, 16), (21, 16), (15, 22), (2, 2), (28, 28), (28, 2)))

@L("marineford", "Marineford Headquarters", "legendary", BEACH + ["minecraft:plains", "onepiece:east_blue", "minecraft:savanna"], "land", "akainu", "Akainu (boss), Vice Admirals, Pacifistas, Marines")
def _(b):
    b.box(0, 0, 0, 46, 0, 46, "minecraft:smooth_stone")
    b.walls(0, 1, 0, 46, 6, 46, "minecraft:white_concrete"); b.walls(0, 5, 0, 46, 5, 46, "minecraft:light_blue_concrete")
    b.door(21, 1, 46, h=5, w=5)
    b.room(13, 0, 6, 33, 22, 22, "minecraft:white_concrete", floor="minecraft:polished_diorite")  # HQ
    for f in (8, 15): b.box(14, f, 7, 32, f, 21, "minecraft:white_concrete"); b.box(15, f, 8, 16, f, 9, AIR)
    for y in range(1, 22): b.set(15, y, 7, ladder("south"))
    b.roof(12, 5, 34, 23, 23, "minecraft:blue_terracotta", top="minecraft:gold_block")
    for x in range(15, 32, 3):
        for y in (3, 10, 17): b.set(x, y, 22, pane("light_blue"))
    b.box(20, 12, 22, 26, 13, 22, "minecraft:white_wool")  # MARINE banner area
    b.box(20, 1, 22, 24, 4, 22, AIR)
    b.box(19, 1, 30, 27, 5, 34, "minecraft:dark_oak_planks"); b.box(20, 1, 31, 26, 4, 33, AIR)  # execution platform
    for x in (20, 26):
        for y in range(6, 10): b.set(x, y, 32, log("dark_oak"))
    for cx, cz in ((4, 4), (42, 4), (4, 42), (42, 42)): b.tower(cx, cz, 3, 14, "minecraft:white_concrete", "minecraft:light_blue_concrete")
    b.chest(30, 16, 18, "legendary", "west"); b.chest(16, 1, 18, "marine", "east"); b.chest(30, 1, 10, "marine", "west")
    b.npc(23, 16, 14, "akainu", True)
    b.guards("vice_admiral", ((18, 12), (28, 12)), y=16)
    b.guards("pacifista", ((10, 28), (36, 28)))
    b.guards("elite_marine", ((18, 26), (28, 26), (23, 38)))
    b.guards("marine", ((8, 12), (38, 12), (8, 36), (38, 36), (23, 42)))
    b.guards("marine_rifle", ((4, 4), (42, 4), (4, 42), (42, 42)), y=15)

@L("ice_fortress", "Aokiji's Ice Fortress", "hard", ["onepiece:punk_hazard_frozen", "minecraft:ice_spikes", "minecraft:snowy_plains", "onepiece:egghead"], "land", "aokiji", "Aokiji (boss), Frost Soldiers")
def _(b):
    ground(b, 0, 0, 24, 24, "minecraft:packed_ice")
    b.room(4, 0, 4, 20, 9, 20, "minecraft:packed_ice", floor="minecraft:blue_ice")
    for cx, cz in ((4, 4), (20, 4), (4, 20), (20, 20)): b.tower(cx, cz, 2, 14, "minecraft:blue_ice", "minecraft:packed_ice", windows=False)
    for x, z, h in ((1, 12, 10), (23, 8, 8), (12, 23, 12), (12, 1, 7)):
        for y in range(1, h): b.set(x, y, z, "minecraft:ice")
    b.door(12, 1, 20, h=3, w=1)
    b.chest(17, 1, 7, "hard", "west")
    b.npc(12, 1, 12, "aokiji", True)
    b.guards("frost_soldier", ((7, 7), (17, 17), (7, 17), (12, 22)))

@L("egghead_lab", "Egghead Labophase", "legendary", ["onepiece:egghead", "minecraft:snowy_plains", "minecraft:plains", "#minecraft:is_beach"], "land", "kizaru", "Kizaru (boss), Seraphim, Pacifistas")
def _(b):
    b.box(0, 0, 0, 34, 0, 34, "minecraft:smooth_quartz")
    b.sphere(17, 0, 17, 14, "minecraft:white_concrete", hollow=True, upper=True, ry=20)  # the egg
    b.box(3, 0, 3, 31, 0, 31, "minecraft:smooth_quartz")
    for yy in (8, 14): b.disk(17, yy, 17, 12, "minecraft:white_concrete"); b.disk(17, yy, 17, 2, AIR)
    for yy in range(1, 15): b.set(17, yy, 15, ladder("south"))
    for a in range(0, 360, 30):
        t = math.radians(a)
        for yy in (5, 11, 17): b.set(round(17 + 13.6 * math.cos(t)), yy, round(17 + 13.6 * math.sin(t)), "minecraft:sea_lantern")
    b.box(15, 1, 31, 19, 4, 33, AIR)
    for x, z in ((10, 10), (24, 10), (10, 24), (24, 24)): b.set(x, 1, z, "minecraft:lodestone")
    b.chest(17, 15, 20, "legendary", "north"); b.chest(22, 1, 17, "lab", "west")
    b.npc(17, 15, 17, "kizaru", True)
    b.guards("seraphim", ((12, 12), (22, 22)), y=9)
    b.guards("pacifista", ((8, 17), (26, 17), (17, 26)))

@L("withered_forest", "Ryokugyu's Withered Forest", "hard", ["onepiece:wano", "#minecraft:is_forest", "#minecraft:is_jungle", "onepiece:elbaph"], "land", "ryokugyu", "Ryokugyu (boss), War Beast")
def _(b):
    ground(b, 0, 0, 30, 30, "minecraft:rooted_dirt")
    for (x, z, h) in ((6, 6, 22), (24, 8, 18), (8, 24, 20), (22, 22, 24), (15, 4, 14), (4, 15, 16)):
        b.cyl(x, z, 1.5, 1, h, log("dark_oak"))
        b.sphere(x, h, z, 4.5, leaves("dark_oak"), ry=3)
        for dx, dz in ((3, 0), (-3, 0), (0, 3), (0, -3)): b.set(x + dx, 1, z + dz, "minecraft:mangrove_roots[waterlogged=false]")
    for x in range(2, 29, 3):
        for z in range(2, 29, 4): b.set(x, 1, z, "minecraft:dead_bush")
    b.chest(15, 1, 16, "hard", "south")
    b.npc(15, 1, 14, "ryokugyu", True)
    b.guards("war_beast", ((15, 24),))
    b.guards("marine", ((10, 14), (20, 14)))
