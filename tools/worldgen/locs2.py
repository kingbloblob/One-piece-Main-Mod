"""Story locations (not tied to one boss)."""
from kit import *
from locs1 import L, ground, BEACH, PLAINS, OCEAN, DEEP
FOREST = ["#minecraft:is_forest", "onepiece:zou", "onepiece:east_blue"]
JUNGLE = ["#minecraft:is_jungle"]
SNOW = ["minecraft:snowy_plains", "minecraft:snowy_taiga", "onepiece:drum_island", "onepiece:egghead", "onepiece:elbaph"]
DESERT = ["minecraft:desert", "onepiece:alabasta"]
WANO = ["onepiece:wano", "minecraft:cherry_grove"]

# ============================================================ EAST BLUE
@L("foosha_village", "Foosha Village", "easy", PLAINS + ["minecraft:meadow"], "land", who="Luffy (quest giver)")
def _(b):
    ground(b, 0, 0, 24, 18)
    b.house(1, 1, 9, 7, 4, "minecraft:oak_planks", "minecraft:red_terracotta", corner=log("oak"))  # Partys Bar
    b.set(5, 1, 3, "minecraft:barrel[facing=up,open=false]"); b.set(3, 1, 3, FENCE.format("oak")); b.set(3, 2, 3, "minecraft:oak_pressure_plate[powered=false]")
    b.house(13, 1, 7, 6, 4, "minecraft:white_terracotta", "minecraft:brown_terracotta")
    b.cyl(19, 13, 2, 1, 9, "minecraft:stripped_oak_log[axis=y]")  # windmill
    for i in range(-4, 5): b.set(19 + i, 8, 11, "minecraft:white_wool"); b.set(19, 8 + i, 11, "minecraft:white_wool")
    b.fruit_tree(6, 1, 14, "minecraft:red_wool")
    b.chest(8, 1, 6, "easy", "west")
    b.npc(5, 1, 10, "luffy", False)

@L("dadan_hideout", "Dadan's Hideout (Mt. Colubo)", "easy", FOREST + ["minecraft:taiga", "minecraft:windswept_forest"], "land", who="Mountain Bandits")
def _(b):
    ground(b, 0, 0, 14, 14, "minecraft:coarse_dirt")
    b.house(2, 2, 9, 8, 3, "minecraft:spruce_planks", "minecraft:spruce_planks", floor="minecraft:dirt", corner=log("spruce"), gable=True)
    b.set(12, 1, 12, CAMPFIRE); b.set(6, 1, 4, BARREL); b.set(4, 1, 4, "minecraft:crafting_table")
    b.chest(9, 1, 4, "easy", "west")
    b.guards("bandit", ((12, 4), (2, 12), (7, 12)))

@L("shells_town", "Shells Town Marine Base", "easy", PLAINS + BEACH, "land", who="Koby (quest giver), Marine Recruits")
def _(b):
    ground(b, 0, 0, 18, 18, "minecraft:stone_bricks")
    b.walls(0, 1, 0, 18, 3, 18, "minecraft:stone_brick_wall[east=low,north=none,south=none,up=true,waterlogged=false,west=low]")
    b.door(8, 1, 18, h=2, w=3)
    b.house(5, 2, 9, 8, 6, "minecraft:white_concrete", "minecraft:light_blue_terracotta")
    for y in range(1, 7): b.set(9, y, 14, "minecraft:stone")  # Morgan's statue
    b.box(8, 5, 14, 10, 5, 14, "minecraft:stone"); b.set(10, 4, 14, "minecraft:iron_block")
    b.chest(6, 1, 3, "marine", "east")
    b.npc(9, 1, 7, "koby", False)
    b.guards("marine_recruit", ((3, 15), (15, 15), (15, 3)))

@L("syrup_village", "Syrup Village (Kaya's Mansion)", "easy", PLAINS + FOREST, "land", who="Usopp (trader)")
def _(b):
    ground(b, 0, 0, 22, 20)
    b.house(5, 2, 13, 9, 5, "minecraft:white_terracotta", "minecraft:red_nether_bricks", floor="minecraft:polished_andesite")
    b.walls(0, 1, 0, 22, 1, 20, FENCE.format("oak")); b.door(11, 1, 20, h=1, w=1)
    b.tree(2, 1, 17, 5); b.tree(20, 1, 17, 5)
    b.chest(15, 1, 5, "easy", "west")
    b.npc(11, 1, 15, "usopp", False)

@L("arlong_park", "Arlong Park", "medium", BEACH + ["minecraft:stony_shore", "onepiece:east_blue"], "land", who="Fish-Men")
def _(b):
    b.box(0, 0, 0, 26, 0, 26, "minecraft:prismarine_bricks")
    b.walls(0, 1, 0, 26, 8, 26, "minecraft:dark_prismarine"); b.door(12, 1, 26, h=4, w=3)
    b.box(6, 0, 6, 20, -3, 14, "minecraft:water[level=0]")  # pool
    b.box(5, -4, 5, 21, -4, 15, "minecraft:prismarine")
    b.house(6, 17, 15, 7, 6, "minecraft:prismarine_bricks", "minecraft:dark_prismarine")
    for x in (2, 24): b.flag(x, 9, 2, 6, ("minecraft:cyan_wool", "minecraft:black_wool"))
    b.chest(8, 1, 19, "pirate", "east")
    b.guards("fishman", ((10, 10), (16, 10), (13, 20), (4, 22)))

@L("cocoyasi_village", "Cocoyasi Village (Tangerine Grove)", "easy", PLAINS + BEACH + ["minecraft:savanna"], "land", who="Nami (trader)")
def _(b):
    ground(b, 0, 0, 20, 20)
    b.house(2, 2, 7, 6, 3, "minecraft:white_terracotta", "minecraft:orange_terracotta")
    for x in range(11, 20, 4):
        for z in range(3, 20, 4): b.fruit_tree(x, 1, z, "minecraft:orange_wool")
    b.chest(4, 1, 4, "easy", "south")
    b.npc(5, 1, 12, "nami", False)

@L("twin_capes_lighthouse", "Twin Capes Lighthouse (Reverse Mountain)", "easy", BEACH + ["minecraft:stony_shore"], "land", who="nobody (Laboon's scars on the wall)")
def _(b):
    ground(b, 0, 0, 14, 14, "minecraft:stone")
    b.tower(7, 7, 3, 18, "minecraft:white_concrete", None, ladder_side=True)
    b.box(6, 18, 6, 8, 20, 8, "minecraft:glass"); b.set(7, 19, 7, "minecraft:glowstone")
    b.box(7, 1, 10, 7, 2, 10, AIR)
    for i in range(10): b.set(0, 1 + i % 5, i + 2, "minecraft:cracked_stone_bricks")  # scarred wall
    b.chest(7, 1, 6, "easy", "south")

@L("pirate_camp", "Pirate Camp", "easy", BEACH + PLAINS + JUNGLE + ["minecraft:savanna"], "land", who="Rookie Pirates")
def _(b):
    ground(b, 0, 0, 14, 14, "minecraft:coarse_dirt")
    for x0, wool in ((1, "minecraft:red_wool"), (9, "minecraft:black_wool")):
        for i, h in enumerate((1, 2, 3, 2, 1)):
            for z in range(1, 6):
                b.set(x0 + i, h, z, wool)
                for y in range(1, h): b.set(x0 + i, y, z, AIR if 0 < i < 4 else wool)
    b.set(7, 1, 8, CAMPFIRE); b.set(11, 1, 12, BARREL); b.set(12, 1, 12, "minecraft:tnt[unstable=false]")
    b.flag(13, 1, 7, 10)
    b.chest(3, 1, 3, "pirate", "south")
    b.guards("rookie_pirate", ((7, 11), (4, 9), (10, 7)))

@L("marine_base", "Marine Outpost", "medium", BEACH + PLAINS + ["minecraft:savanna", "onepiece:sabaody", "onepiece:drum_island"], "land", who="Garp (quest giver), Marines")
def _(b):
    b.box(0, 0, 0, 16, 0, 16, "minecraft:stone_bricks")
    b.room(0, 0, 0, 16, 6, 16, "minecraft:white_concrete", floor="minecraft:smooth_stone")
    b.walls(0, 4, 0, 16, 4, 16, "minecraft:light_blue_concrete"); b.door(7, 1, 16, h=3, w=3)
    b.tower(13, 13, 2, 12, "minecraft:white_concrete")
    for x in (2, 4, 6): bed("white", x, 1, 2, b)
    b.chest(2, 1, 14, "marine", "east")
    b.npc(8, 1, 9, "garp", False)
    b.guards("marine", ((5, 11), (11, 5)))
    b.guards("marine_rifle", ((13, 13),), y=13)

@L("baratie", "Baratie (sea restaurant)", "easy", OCEAN, "sea", who="Sanji (trader)")
def _(b):
    dy = b.ship(0, 0, 0, 28, 13, hull="minecraft:spruce_planks", deck="minecraft:oak_planks", masts=((22, 12),), sail="minecraft:white_wool", flag=None, depth=3)
    b.sphere(28, dy + 1, 6, 3.5, "minecraft:orange_terracotta"); b.set(31, dy + 2, 4, "minecraft:black_concrete"); b.set(31, dy + 2, 8, "minecraft:black_concrete")
    b.room(5, dy, 3, 19, dy + 5, 9, "minecraft:white_terracotta", floor="minecraft:oak_planks")
    b.roof(4, 2, 20, 10, dy + 6, "minecraft:red_terracotta", top="minecraft:red_terracotta")
    b.door(19, dy + 1, 6, axis="z")
    for x in (8, 12): b.set(x, dy + 1, 5, FENCE.format("oak")); b.set(x, dy + 2, 5, "minecraft:oak_pressure_plate[powered=false]")
    for x in (16, 17): b.set(x, dy + 1, 4, "minecraft:smoker[facing=south,lit=false]")
    b.chest(18, dy + 1, 8, "galley", "north")
    b.npc(14, dy + 1, 6, "sanji", False)

# ============================================================ PARADISE (first half of the Grand Line)
@L("whisky_peak", "Whisky Peak", "medium", DESERT + ["minecraft:badlands", "minecraft:savanna"], "land", who="Bounty Hunters")
def _(b):
    ground(b, 0, 0, 24, 24, "minecraft:sand")
    for (x, z, h) in ((4, 4, 16), (20, 6, 20), (6, 20, 14), (19, 19, 18)):  # cactus-shaped mountains
        b.cyl(x, z, 2, 1, h, "minecraft:green_terracotta")
        b.cyl(x + 3, z, 1, h // 2, h // 2 + 5, "minecraft:green_terracotta"); b.box(x + 1, h // 2, z, x + 3, h // 2, z, "minecraft:green_terracotta")
    b.house(9, 8, 7, 8, 4, "minecraft:spruce_planks", "minecraft:spruce_planks", corner=log("spruce"))
    for x in (10, 13): b.set(x, 1, 11, FENCE.format("spruce")); b.set(x, 2, 11, "minecraft:oak_pressure_plate[powered=false]")
    b.chest(14, 1, 9, "medium", "west")
    b.guards("bounty_hunter", ((12, 4), (12, 20), (2, 12), (22, 12)))

@L("little_garden_camp", "Little Garden Giants' Camp", "medium", ["onepiece:little_garden"] + JUNGLE, "land", who="nobody (giant bones and duel ground)")
def _(b):
    ground(b, 0, 0, 34, 34, "minecraft:podzol[snowy=false]")
    b.bones(2, 0, 4, 28)
    for (cx, cz) in ((8, 26), (26, 26)):  # giant huts
        b.cyl(cx, cz, 5, 1, 8, "minecraft:mud_bricks", hollow=True)
        for i in range(6): b.cyl(cx, cz, 5 - i, 9 + i, 9 + i, "minecraft:hay_block[axis=y]", hollow=False)
        b.box(cx, 1, cz - 5, cx + 1, 4, cz - 5, AIR)
    b.box(15, 0, 22, 19, 0, 30, "minecraft:dirt_path")
    b.chest(8, 1, 26, "medium", "north"); b.chest(26, 1, 26, "medium", "north")
    b.guards("bounty_hunter", ((17, 18), (12, 14)))

@L("drum_castle", "Drum Castle", "easy", SNOW, "land", who="Chopper (trader)")
def _(b):
    b.box(0, 0, 0, 14, 0, 14, "minecraft:stone_bricks")
    b.room(2, 0, 2, 12, 9, 12, "minecraft:stone_bricks", floor="minecraft:stone_bricks")
    b.tower(7, 7, 2, 10, "minecraft:stone_bricks", "minecraft:blue_terracotta", y=9, ladder_side=False)
    b.door(7, 1, 12, h=3, w=1)
    for x in (4, 9): bed("red", x, 1, 4, b)
    b.set(4, 1, 10, "minecraft:brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
    b.chest(10, 1, 10, "medicine", "west")
    b.npc(7, 1, 8, "chopper", False)

@L("alubarna_palace", "Alubarna Palace", "medium", DESERT, "land", who="Baroque Works agents")
def _(b):
    b.box(0, 0, 0, 30, 0, 30, "minecraft:smooth_sandstone")
    b.room(5, 0, 5, 25, 10, 25, "minecraft:cut_sandstone", floor="minecraft:smooth_sandstone")
    for cx, cz in ((5, 5), (25, 5), (5, 25), (25, 25)): b.tower(cx, cz, 2, 16, "minecraft:sandstone", "minecraft:gold_block")
    b.sphere(15, 10, 15, 7, "minecraft:smooth_sandstone", hollow=True, upper=True)
    b.door(14, 1, 25, h=4, w=3)
    b.box(8, 1, 8, 22, 1, 8, "minecraft:blue_carpet")
    b.chest(15, 1, 7, "treasure", "south")
    b.guards("baroque_agent", ((10, 18), (20, 18), (15, 28), (2, 15), (28, 15)))

@L("nanohana_port", "Nanohana Market", "easy", DESERT + BEACH, "land", who="nobody (market town)")
def _(b):
    ground(b, 0, 0, 22, 16, "minecraft:sandstone")
    for i, c in enumerate(("red", "yellow", "blue", "orange", "purple")): b.stall(1 + i * 4, 0, 2, c)
    b.house(2, 8, 7, 7, 4, "minecraft:smooth_sandstone", "minecraft:cut_sandstone")
    b.house(12, 8, 8, 7, 4, "minecraft:smooth_sandstone", "minecraft:cut_sandstone")
    b.chest(4, 1, 10, "easy", "south")

@L("yuba_oasis", "Yuba Oasis", "easy", DESERT, "land", who="nobody (half-buried town)")
def _(b):
    ground(b, 0, 0, 20, 20, "minecraft:sand")
    b.box(8, -2, 8, 12, 0, 12, "minecraft:water[level=0]"); b.walls(7, -2, 7, 13, 1, 13, "minecraft:sandstone")
    for x, z in ((3, 3), (17, 4), (4, 17)): b.palm(x, 1, z)
    for x, z in ((2, 10), (15, 15)):
        b.box(x, 1, z, x + 3, 2, z + 3, "minecraft:sandstone"); b.box(x + 1, 1, z + 1, x + 2, 2, z + 2, AIR)
    b.chest(16, 1, 16, "easy", "north")

@L("mock_town", "Mock Town (Jaya)", "medium", ["onepiece:jaya", "minecraft:savanna", "minecraft:plains"] + BEACH, "land", who="Pirates and Pirate Gunners")
def _(b):
    ground(b, 0, 0, 26, 22, "minecraft:dirt_path")
    b.house(1, 1, 8, 7, 4, "minecraft:spruce_planks", "minecraft:dark_oak_planks", corner=log("spruce"))  # tavern
    b.house(11, 1, 6, 6, 5, "minecraft:mossy_cobblestone", "minecraft:spruce_planks")
    b.house(19, 1, 7, 8, 4, "minecraft:spruce_planks", "minecraft:dark_oak_planks")
    b.house(4, 12, 9, 8, 4, "minecraft:cracked_stone_bricks", "minecraft:spruce_planks")
    for x in range(2, 9, 2): b.set(x, 1, 4, BARREL)
    b.flag(22, 1, 14, 9)
    b.chest(6, 1, 15, "pirate", "east")
    b.guards("pirate", ((10, 10), (16, 14), (22, 10)))
    b.guards("pirate_gunner", ((14, 19),))

@L("cricket_house", "Montblanc Cricket's House", "easy", ["onepiece:jaya"] + BEACH + JUNGLE, "land", who="nobody (just a castle facade)")
def _(b):
    ground(b, 0, 0, 14, 14, "minecraft:sand")
    b.box(0, 1, 6, 14, 12, 6, "minecraft:white_terracotta")  # the famous fake castle front
    for x in (0, 14): b.box(x, 13, 6, x, 15, 6, "minecraft:white_terracotta")
    for x in range(1, 14, 4): b.set(x, 8, 6, PANE)
    b.house(3, 7, 9, 6, 3, "minecraft:spruce_planks", "minecraft:spruce_planks")
    b.set(10, 1, 3, "minecraft:dark_oak_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]")
    b.chest(5, 1, 9, "treasure", "east")

@L("angel_beach", "Angel Beach (Skypiea)", "easy", ["onepiece:skypiea"] + JUNGLE + OCEAN, "sky", who="nobody (cloud cottages)")
def _(b):
    for x in range(-14, 15):
        for z in range(-10, 11):
            if (x / 14) ** 2 + (z / 10) ** 2 <= 1:
                b.set(x, 0, z, "onepiece:island_cloud"); b.set(x, -1, z, "onepiece:island_cloud")
                if (x / 14) ** 2 + (z / 10) ** 2 <= 0.5: b.set(x, -2, z, "onepiece:island_cloud")
    for cx in (-8, 0, 8):
        b.sphere(cx, 1, 2, 2.5, "minecraft:white_concrete", hollow=True, upper=True); b.set(cx, 1, -1, AIR); b.set(cx, 2, -1, AIR)
    for x, z in ((-11, -5), (11, -4)): b.palm(x, 1, z, 5)
    b.chest(0, 1, 3, "sky_treasure", "north")

@L("giant_jack", "Giant Jack (the giant beanstalk)", "medium", ["onepiece:skypiea"] + JUNGLE, "land", who="Sky Priests at the top")
def _(b):
    ground(b, 0, 0, 12, 12)
    for y in range(1, 100):  # twisting stalk
        a = y / 8.0; cx, cz = 6 + 2 * math.cos(a), 6 + 2 * math.sin(a)
        b.cyl(cx, cz, 2, y, y, "minecraft:moss_block")
        if y % 6 == 0:
            b.box(round(cx) - 2, y, round(cz) - 2, round(cx) + 2, y, round(cz) + 2, leaves("jungle"))
    b.disk(6, 100, 6, 6, "onepiece:island_cloud")
    b.chest(6, 101, 6, "sky_treasure", "south")
    b.guards("sky_priest", ((3, 3),), y=101)

@L("weatheria", "Weatheria (weather science island)", "easy", OCEAN + ["onepiece:skypiea"], "sky", who="nobody (weather balls and a lab)")
def _(b):
    b.disk(0, 0, 0, 12, "onepiece:island_cloud"); b.disk(0, -1, 0, 10, "onepiece:island_cloud"); b.disk(0, -2, 0, 6, "onepiece:island_cloud")
    b.house(-4, -4, 9, 8, 4, "minecraft:white_terracotta", "minecraft:light_blue_terracotta", y=0)
    for (x, z) in ((-9, 0), (9, 2), (0, 9)): b.sphere(x, 3, z, 1.5, "minecraft:light_blue_stained_glass"); b.set(x, 1, z, FENCE.format("birch")); b.set(x, 2, z, FENCE.format("birch"))
    b.chest(2, 1, -2, "lab", "west")

@L("davy_back_stage", "Davy Back Fight Arena (Long Ring Long Land)", "easy", PLAINS + ["minecraft:savanna"], "land", who="Pirates (friendly duel crowd)")
def _(b):
    ground(b, 0, 0, 40, 10)
    b.walls(0, 1, 0, 40, 1, 10, FENCE.format("acacia")); b.door(20, 1, 10, h=1, w=1)
    for x in range(4, 38, 8): b.box(x, 1, 2, x, 3, 2, "minecraft:hay_block[axis=y]")
    b.box(18, 1, 4, 22, 3, 6, "minecraft:acacia_planks"); b.box(18, 4, 4, 22, 4, 6, "minecraft:red_wool")
    b.chest(20, 1, 8, "easy", "north")
    b.guards("rookie_pirate", ((10, 5), (30, 5)))

@L("galley_la_dock", "Galley-La Shipyard (Water 7)", "easy", BEACH + ["minecraft:stony_shore"], "land", who="Franky (trader)")
def _(b):
    b.box(0, 0, 0, 34, 0, 16, "minecraft:stone_bricks")
    for x in range(2, 33, 2): b.box(x, 1, 2, x, 7 - abs(x - 17) // 4, 2, "minecraft:stripped_spruce_log[axis=y]")  # ship ribs under construction
    b.box(2, 1, 1, 32, 1, 3, "minecraft:spruce_planks")
    for x in (4, 30):  # cranes
        b.box(x, 1, 8, x, 14, 8, "minecraft:iron_block"); b.box(x, 14, 2, x, 14, 8, "minecraft:iron_block"); b.box(x, 8, 2, x, 13, 2, CHAIN)
    b.house(10, 9, 14, 7, 4, "minecraft:bricks", "minecraft:blue_terracotta")
    b.chest(12, 1, 11, "easy", "east")
    b.npc(17, 1, 12, "franky", False)

@L("franky_house", "Franky House", "medium", BEACH, "land", who="Franky Family (pirates)")
def _(b):
    ground(b, 0, 0, 20, 16, "minecraft:gravel")
    b.house(2, 2, 14, 11, 5, "minecraft:iron_block", "minecraft:blue_concrete", floor="minecraft:spruce_planks")
    for x in range(3, 16, 3): b.set(x, 6, 2, "minecraft:redstone_lamp[lit=true]")
    b.set(8, 1, 6, "minecraft:anvil[facing=north]"); b.set(10, 1, 6, "minecraft:blast_furnace[facing=south,lit=false]")
    b.chest(4, 1, 4, "medium", "east")
    b.guards("pirate", ((6, 9), (12, 9), (17, 14)))

@L("sea_train_station", "Puffing Tom Station", "easy", BEACH + ["minecraft:stony_shore"], "land", who="nobody (sea train platform)")
def _(b):
    ground(b, 0, 0, 30, 8, "minecraft:stone_bricks")
    b.box(0, 1, 2, 30, 1, 2, "minecraft:rail[shape=east_west,waterlogged=false]")
    b.house(10, 4, 10, 5, 4, "minecraft:bricks", "minecraft:red_terracotta")
    b.box(2, 1, 3, 6, 3, 5, "minecraft:black_concrete"); b.box(2, 4, 4, 2, 6, 4, "minecraft:black_concrete")  # locomotive
    b.chest(12, 1, 6, "easy", "east")

# ============================================================ SABAODY, AMAZON LILY, IMPEL DOWN, FISH-MAN ISLAND
@L("shakky_bar", "Shakky's Rip-off Bar (Sabaody)", "easy", ["onepiece:sabaody", "minecraft:mangrove_swamp", "minecraft:swamp"], "land", who="Rayleigh (quest giver)")
def _(b):
    ground(b, 0, 0, 14, 14, "minecraft:mud")
    b.house(2, 2, 10, 9, 4, "minecraft:mangrove_planks", "minecraft:dark_oak_planks", floor="minecraft:mangrove_planks", corner=log("mangrove"))
    for x in range(4, 10, 2): b.set(x, 1, 4, FENCE.format("mangrove")); b.set(x, 2, 4, "minecraft:mangrove_pressure_plate[powered=false]")
    b.chest(10, 1, 4, "easy", "west")
    b.npc(6, 1, 8, "rayleigh", False)
    for x, z in ((1, 1), (13, 13)): b.sphere(x, 7, z, 1.5, "minecraft:light_blue_stained_glass")  # bubbles

@L("sabaody_park", "Sabaody Park", "easy", ["onepiece:sabaody", "minecraft:mangrove_swamp"], "land", who="nobody (amusement park)")
def _(b):
    ground(b, 0, 0, 26, 26, "minecraft:mangrove_planks")
    for a in range(0, 360, 6):  # ferris wheel
        t = math.radians(a); b.set(13, round(13 + 10 * math.sin(t)), round(13 + 10 * math.cos(t)), "minecraft:white_concrete")
    for a in range(0, 360, 45):
        t = math.radians(a)
        for r in range(1, 10): b.set(13, round(13 + r * math.sin(t)), round(13 + r * math.cos(t)), "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]")
        b.set(13, round(13 + 10 * math.sin(t)), round(13 + 10 * math.cos(t)), "minecraft:pink_wool")
    for x, z in ((4, 4), (22, 22), (4, 22)): b.sphere(x, 6, z, 2, "minecraft:light_blue_stained_glass")
    b.chest(2, 1, 13, "easy", "east")

@L("auction_house", "Human Auction House", "medium", ["onepiece:sabaody", "minecraft:mangrove_swamp"] + PLAINS, "land", who="Marines guarding the auction")
def _(b):
    ground(b, 0, 0, 22, 22, "minecraft:mangrove_planks")
    b.room(1, 0, 1, 21, 10, 21, "minecraft:red_nether_bricks", floor="minecraft:red_carpet")
    b.box(5, 1, 4, 17, 2, 6, "minecraft:dark_oak_planks"); b.box(9, 3, 5, 13, 5, 5, BARS)  # stage with a cage
    for z in range(10, 20, 2):
        for x in range(4, 19, 2): b.set(x, 1, z, "minecraft:red_carpet")
    b.door(10, 1, 21, h=3, w=3)
    b.chest(11, 3, 4, "treasure", "south")
    b.guards("marine", ((4, 16), (18, 16), (11, 19)))
    b.guards("cp_agent", ((11, 8),))

@L("amazon_lily", "Amazon Lily Kuja Palace", "medium", ["onepiece:amazon_lily"] + JUNGLE, "land", who="Boa Hancock (quest giver), Kuja Warriors")
def _(b):
    ground(b, 0, 0, 28, 28, "minecraft:mossy_stone_bricks")
    b.room(6, 0, 6, 22, 12, 22, "minecraft:purple_terracotta", floor="minecraft:polished_deepslate")
    b.sphere(14, 12, 14, 6, "minecraft:gold_block", hollow=True, upper=True)
    for i in range(0, 28, 1):  # snake statues coiling around the gate
        b.set(3 + (i % 2), 1 + i // 3, 12 + (i % 4), "minecraft:green_terracotta"); b.set(24 - (i % 2), 1 + i // 3, 12 + (i % 4), "minecraft:green_terracotta")
    b.door(13, 1, 22, h=4, w=3)
    b.box(10, 1, 9, 18, 1, 9, "minecraft:purple_carpet")
    b.chest(20, 1, 9, "treasure", "west")
    b.npc(14, 1, 12, "hancock", False)
    b.guards("kuja_warrior", ((9, 18), (19, 18), (2, 2), (26, 26)))

@L("impel_down", "Impel Down", "legendary", OCEAN + BEACH + ["minecraft:stony_shore"], "under", who="Jailers and Jailer Beasts on 5 floors underground")
def _(b):
    # Above ground: the gate tower. Below: five prison levels going down, each meaner than the last.
    b.box(0, 0, 0, 24, 0, 24, "minecraft:polished_deepslate")
    b.room(6, 0, 6, 18, 14, 18, "minecraft:deepslate_tiles"); b.door(12, 1, 18, h=4, w=1)
    levels = [("minecraft:red_nether_bricks", "minecraft:lava[level=0]"), ("minecraft:mud_bricks", "minecraft:magma_block"),
              ("minecraft:blue_ice", "minecraft:powder_snow"), ("minecraft:blackstone", "minecraft:fire[age=0,east=false,north=false,south=false,up=false,west=false]"),
              ("minecraft:obsidian", "minecraft:soul_fire")]
    for i, (wall, hazard) in enumerate(levels):
        y0 = -8 * (i + 1)
        b.room(0, y0, 0, 24, y0 + 8, 24, wall, floor=wall)
        for x in range(2, 23, 5):  # cells
            b.box(x, y0 + 1, 2, x + 3, y0 + 4, 2, BARS); b.box(x, y0 + 1, 22, x + 3, y0 + 4, 22, BARS)
        if i in (0, 1, 2): b.box(15, y0, 6, 21, y0, 18, hazard)  # Crimson Hell, Starvation Hell, Freezing Hell...
        if i == 4: b.box(15, y0 + 1, 9, 21, y0 + 1, 9, "minecraft:soul_sand")
    for y in range(-39, 14): b.set(12, y, 12, ladder("north")); b.set(12, y, 13, "minecraft:deepslate_tiles")
    for i in range(5): b.set(12, -8 * (i + 1) + 8, 12, ladder("north"))
    for i in range(5):
        y0 = -8 * (i + 1) + 1
        kit = ("jailer", "jailer", "warden_jailer", "warden_jailer", "warden_jailer")[i]
        b.guards(kit, ((5, 8), (8, 18), (5, 16), (8, 6))[:2 + i // 2], y=y0)
    b.chest(20, -39, 20, "legendary", "west"); b.chest(4, -23, 20, "hard", "east")
    b.guards("pacifista", ((6, 12),), y=-39)

@L("ryugu_palace", "Ryugu Palace (Fish-Man Island)", "medium", ["onepiece:fishman_reef", "minecraft:warm_ocean", "minecraft:lukewarm_ocean", "minecraft:deep_lukewarm_ocean"], "seafloor", who="Jinbe (quest giver), Fish-Men")
def _(b):
    b.disk(14, 0, 14, 14, "minecraft:sand")
    b.sphere(14, 0, 14, 13, "minecraft:glass", hollow=True, upper=True)  # the bubble
    b.room(7, 0, 7, 21, 9, 21, "minecraft:prismarine_bricks", floor="minecraft:prismarine")
    b.roof(6, 6, 22, 22, 10, "minecraft:pink_terracotta", top="minecraft:pink_terracotta")
    b.door(14, 1, 21, h=3, w=1)
    for x, z in ((3, 14), (25, 14), (14, 3)): b.box(x, 1, z, x, 3, z, "minecraft:tube_coral_block")
    b.set(14, 1, 9, "minecraft:conduit[waterlogged=false]")
    b.chest(10, 1, 10, "treasure", "east")
    b.npc(14, 1, 14, "jinbe", False)
    b.guards("fishman", ((5, 18), (23, 18)))

@L("fishman_district", "Fish-Man District", "medium", ["onepiece:fishman_reef", "minecraft:warm_ocean", "minecraft:ocean"], "seafloor", who="Fish-Men (lots)")
def _(b):
    b.disk(12, 0, 12, 12, "minecraft:sand")
    for (x, z) in ((4, 4), (16, 3), (4, 16), (17, 16)):
        b.house(x, z, 5, 5, 3, "minecraft:dark_prismarine", "minecraft:prismarine", floor="minecraft:sand")
    b.box(10, 1, 10, 13, 6, 13, "minecraft:mossy_cobblestone"); b.box(11, 7, 11, 12, 9, 12, "minecraft:mossy_cobblestone")
    b.chest(6, 1, 6, "pirate", "east")
    b.guards("fishman", ((12, 2), (2, 12), (22, 12), (12, 22), (8, 8)))

@L("punk_hazard_lab", "Punk Hazard Laboratory", "medium", ["onepiece:punk_hazard_burning", "onepiece:punk_hazard_frozen", "minecraft:ice_spikes", "minecraft:badlands"], "land", who="Vegapunk (trader), Law (quest giver), Frost Soldiers")
def _(b):
    b.box(0, 0, 0, 16, 0, 14, "minecraft:polished_andesite")
    b.room(0, 0, 0, 16, 6, 14, "minecraft:white_concrete")
    b.walls(0, 3, 0, 16, 3, 14, "minecraft:cyan_concrete")
    b.door(7, 1, 14, h=3, w=3)
    b.box(5, 7, 4, 11, 9, 10, "minecraft:glass"); b.box(6, 7, 5, 10, 8, 9, AIR)
    for x in (2, 4): b.set(x, 1, 2, "minecraft:brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
    b.chest(14, 1, 12, "lab", "west")
    b.npc(8, 1, 4, "vegapunk", False); b.npc(10, 1, 9, "law", False)
    b.guards("frost_soldier", ((3, 18), (13, 18)))

@L("g5_base", "G-5 Marine Base", "hard", ["onepiece:punk_hazard_frozen"] + SNOW, "land", who="Marine Captains and Riflemen")
def _(b):
    b.box(0, 0, 0, 26, 0, 26, "minecraft:polished_andesite")
    b.walls(0, 1, 0, 26, 7, 26, "minecraft:gray_concrete"); b.walls(0, 6, 0, 26, 6, 26, "minecraft:black_concrete")
    b.door(12, 1, 26, h=4, w=3)
    b.house(5, 4, 16, 10, 5, "minecraft:light_gray_concrete", "minecraft:gray_concrete")
    for cx, cz in ((3, 3), (23, 3), (3, 23), (23, 23)): b.tower(cx, cz, 2, 12, "minecraft:gray_concrete")
    b.chest(7, 1, 6, "marine", "east"); b.chest(19, 1, 6, "hard", "west")
    b.guards("elite_marine", ((13, 18), (8, 20), (18, 20)))
    b.guards("marine_rifle", ((3, 3), (23, 3), (3, 23), (23, 23)), y=13)
    b.guards("marine", ((10, 9), (16, 9)))

@L("toy_house", "Dressrosa Toy House", "easy", ["onepiece:dressrosa", "minecraft:sunflower_plains"] + PLAINS, "land", who="nobody (a cheerful toy factory)")
def _(b):
    ground(b, 0, 0, 18, 18)
    cols = ["red", "yellow", "lime", "light_blue", "pink", "orange"]
    for i in range(6):
        b.box(3 + i * 2, 1, 3, 4 + i * 2, 3 + i, 4, f"minecraft:{cols[i]}_concrete")
    b.house(3, 7, 12, 9, 5, "minecraft:yellow_terracotta", "minecraft:red_terracotta")
    b.chest(5, 1, 9, "easy", "east")

@L("mokomo_dukedom", "Mokomo Dukedom (Zou)", "easy", ["onepiece:zou"] + FOREST + JUNGLE, "land", who="nobody (Mink tree houses)")
def _(b):
    ground(b, 0, 0, 26, 26)
    for (x, z) in ((6, 6), (20, 8), (10, 20)):
        b.cyl(x, z, 2, 1, 14, log("jungle"))
        b.sphere(x, 16, z, 5, leaves("jungle"), ry=3)
        b.disk(x, 9, z, 4, "minecraft:jungle_planks"); b.cyl(x, z, 2, 9, 9, log("jungle"))
        b.room(x - 2, 10, z + 2, x + 2, 13, z + 5, "minecraft:jungle_planks")
        for y in range(1, 10): b.set(x, y, z - 3, ladder("north"))
    b.chest(6, 10, 8, "easy", "north")

@L("chocolate_town", "Cacao Island Chocolate Town", "easy", ["onepiece:whole_cake", "minecraft:meadow"] + PLAINS, "land", who="Homies (just a few)")
def _(b):
    ground(b, 0, 0, 22, 22, "minecraft:brown_terracotta")
    for (x, z) in ((1, 1), (12, 1), (1, 12), (12, 12)):
        b.house(x, z, 8, 7, 3, "minecraft:brown_terracotta", "minecraft:pink_concrete", floor="minecraft:white_terracotta")
    for x, z in ((10, 10), (11, 11)): b.box(x, 1, z, x, 4, z, "minecraft:red_concrete")
    b.chest(3, 1, 3, "candy", "south")
    b.guards("homie", ((10, 20),))

@L("flower_capital", "Flower Capital (Wano)", "medium", WANO, "land", who="Samurai, Kin'emon (quest giver)")
def _(b):
    b.box(0, 0, 0, 30, 0, 30, "minecraft:gravel")
    b.walls(0, 1, 0, 30, 4, 30, "minecraft:white_terracotta"); b.walls(0, 5, 0, 30, 5, 30, "minecraft:deepslate_tiles"); b.door(14, 1, 30, h=3, w=3)
    for i, w_ in enumerate((14, 11, 8, 5)):  # pagoda castle
        y = i * 5; o = (14 - w_) // 2 + 8
        b.room(o, y, o, o + w_, y + 4, o + w_, "minecraft:white_terracotta", floor="minecraft:dark_oak_planks")
        b.box(o - 1, y + 5, o - 1, o + w_ + 1, y + 5, o + w_ + 1, "minecraft:deepslate_tiles")
    for y in range(1, 20): b.set(9, y, 9, ladder("south"))
    for y in (5, 10, 15): b.set(9, y, 9, ladder("south"))
    for (x, z) in ((3, 3), (25, 3), (3, 25), (25, 25)): b.tree(x, 1, z, 5, "cherry", 2.5)
    b.door(15, 1, 22, h=3, w=1)
    b.chest(12, 1, 12, "wano", "south")
    b.npc(15, 1, 26, "kinemon", False)
    b.guards("samurai", ((5, 15), (25, 15), (15, 5)))

@L("ebisu_town", "Ebisu Town (Wano)", "easy", WANO, "land", who="nobody (poor but always smiling)")
def _(b):
    ground(b, 0, 0, 20, 20, "minecraft:coarse_dirt")
    for (x, z) in ((1, 1), (11, 1), (1, 11), (11, 11)):
        b.house(x, z, 7, 6, 3, "minecraft:stripped_spruce_log[axis=y]", "minecraft:spruce_slab[type=bottom,waterlogged=false]", floor="minecraft:dirt")
    b.chest(3, 1, 3, "easy", "south")

@L("wano_house", "Wano Samurai House", "easy", WANO, "land", who="Oden or Yamato (quest giver)")
def _(b):
    ground(b, 0, 0, 12, 14, "minecraft:gravel")
    b.house(1, 1, 11, 9, 4, "minecraft:cherry_planks", "minecraft:deepslate_tiles", floor="minecraft:dark_oak_planks", corner=log("dark_oak"))
    for x in (3, 9):
        for y in range(1, 6): b.set(x, y, 13, "minecraft:red_concrete")
    b.box(2, 6, 13, 10, 6, 13, "minecraft:black_concrete"); b.box(3, 4, 13, 9, 4, 13, "minecraft:red_concrete")
    b.chest(9, 1, 3, "wano", "west")
    b.npc(6, 1, 5, "oden", False); b.npc(6, 1, 11, "yamato", False)

@L("udon_prison", "Udon Prisoner Mine", "hard", WANO + ["minecraft:windswept_hills", "minecraft:stony_shore", "onepiece:onigashima"], "under", who="Gifters, Headliner, War Beast")
def _(b):
    b.box(0, 0, 0, 20, 0, 20, "minecraft:cobbled_deepslate")
    b.room(6, 0, 6, 14, 8, 14, "minecraft:deepslate_bricks"); b.door(10, 1, 14, h=3, w=1)
    for lvl in (1, 2):
        y0 = -9 * lvl
        b.room(0, y0, 0, 20, y0 + 9, 20, "minecraft:cobbled_deepslate", floor="minecraft:gravel")
        for x in range(2, 19, 4): b.box(x, y0 + 1, 2, x + 2, y0 + 4, 2, BARS)
        for x in range(3, 18, 5): b.set(x, y0 + 1, 18, "minecraft:deepslate_coal_ore"); b.set(x + 1, y0 + 1, 18, "minecraft:deepslate_gold_ore")
        b.box(4, y0 + 1, 10, 16, y0 + 1, 10, "minecraft:rail[shape=east_west,waterlogged=false]")
    for y in range(-17, 8): b.set(10, y, 9, ladder("north")); b.set(10, y, 10, "minecraft:deepslate_bricks")
    b.chest(17, -17, 16, "hard", "west")
    b.guards("gifter", ((5, 6), (15, 6)), y=-8)
    b.guards("headliner", ((10, 15),), y=-17)
    b.guards("war_beast", ((5, 12),), y=-17)

@L("elbaph_tree", "Elbaph Great Tree", "medium", ["onepiece:elbaph"] + SNOW + ["minecraft:old_growth_spruce_taiga"], "land", who="nobody (giants' longhouse; wild wolves nearby)")
def _(b):
    ground(b, 0, 0, 30, 30, "minecraft:podzol[snowy=false]")
    b.cyl(15, 15, 5, 1, 45, "onepiece:adam_log")
    for y in (30, 38, 46): b.sphere(15, y, 15, 12 - (y - 30) // 4, leaves("spruce"), ry=4)
    b.room(2, 0, 20, 14, 9, 28, "minecraft:spruce_planks", floor="minecraft:spruce_planks")  # giant longhouse
    b.gable(1, 19, 15, 29, 9, "minecraft:dark_oak_planks")
    b.door(8, 1, 20, h=5, w=3)
    b.set(8, 1, 25, CAMPFIRE)
    b.chest(4, 1, 26, "medium", "east")
    b.guards("bounty_hunter", ((20, 6), (24, 24)))

@L("mary_geoise", "Mary Geoise (the Holy Land on the Red Line)", "legendary", ["onepiece:red_line", "minecraft:badlands", "minecraft:wooded_badlands", "minecraft:windswept_hills"], "land", who="CP0 agents, Vice Admirals, Pacifistas")
def _(b):
    b.box(0, 0, 0, 40, 22, 40, "minecraft:red_terracotta")  # chunk of the Red Line
    for y in range(0, 23, 4): b.walls(0, y, 0, 40, y, 40, "minecraft:orange_terracotta")
    for y in range(1, 24): b.set(20, y, 41, ladder("south"))  # long climb up the cliff
    b.box(0, 23, 0, 40, 23, 40, "minecraft:quartz_block")
    b.room(10, 23, 8, 30, 38, 28, "minecraft:quartz_bricks", floor="minecraft:smooth_quartz")
    b.roof(9, 7, 31, 29, 39, "minecraft:gold_block", top="minecraft:gold_block")
    for cx, cz in ((10, 8), (30, 8), (10, 28), (30, 28)): b.tower(cx, cz, 3, 22, "minecraft:quartz_bricks", "minecraft:gold_block", y=23)
    b.door(20, 24, 28, h=5, w=3)
    b.chest(14, 24, 12, "legendary", "east"); b.chest(26, 24, 12, "treasure", "west")
    b.guards("cp0_agent", ((15, 18), (25, 18), (20, 12)), y=24)
    b.guards("vice_admiral", ((20, 32),), y=24)
    b.guards("pacifista", ((5, 34), (35, 34)), y=24)

@L("laugh_tale", "Laugh Tale (the final island)", "legendary", BEACH + ["onepiece:red_line", "minecraft:stony_shore"], "land", who="Roger (quest giver) waits past the Ancient Guardians")
def _(b):
    b.box(0, 0, 0, 36, 0, 36, "minecraft:mossy_stone_bricks")
    b.room(4, 0, 4, 32, 7, 32, "minecraft:chiseled_stone_bricks", floor="minecraft:mossy_stone_bricks")
    for i in range(6, 31, 4):  # the maze
        gap = 6 + (i * 7) % 22
        b.box(i, 1, 5, i, 6, 31, "minecraft:stone_bricks"); b.box(i, 1, gap, i, 3, gap + 1, AIR)
    b.box(17, 0, 17, 19, 0, 19, "minecraft:gold_block")
    b.door(17, 1, 32, h=3, w=3)
    b.box(30, 1, 16, 30, 4, 20, "minecraft:obsidian")  # the final Poneglyph
    b.set(30, 2, 18, "minecraft:crying_obsidian")
    b.chest(29, 1, 17, "laugh_tale", "west"); b.chest(29, 1, 19, "legendary", "west")
    b.npc(27, 1, 18, "roger", False)
    b.guards("ancient_guardian", ((8, 10), (16, 26), (24, 10), (28, 28), (12, 18)))
    b.guards("warden_jailer", ((20, 18), (26, 8)))

# ============================================================ SEA, MISC
@L("marine_battleship", "Marine Battleship", "hard", OCEAN + DEEP, "sea", who="Marine Captain, Marines, Riflemen")
def _(b):
    dy = b.ship(0, 0, 0, 40, 15, hull="minecraft:white_concrete", deck="minecraft:spruce_planks", masts=((12, 18), (26, 20)),
                sail="minecraft:white_wool", flag=("minecraft:blue_wool", "minecraft:white_wool"), cabin=(8, 5, "minecraft:light_blue_concrete"))
    for x in range(10, 36, 5):
        for z in (2, 12): b.set(x, dy, z, "minecraft:dispenser[facing=up,triggered=false]")
    b.chest(3, dy + 1, 7, "marine", "east")
    b.guards("elite_marine", ((20, 7),), y=dy + 1)
    b.guards("marine", ((14, 5), (14, 9), (30, 5), (30, 9)), y=dy + 1)
    b.guards("marine_rifle", ((36, 7), (24, 7)), y=dy + 1)

@L("sunken_galleon", "Sunken Treasure Galleon", "easy", OCEAN + DEEP, "seafloor", who="a few Fish-Men")
def _(b):
    dy = b.ship(0, 0, 0, 26, 9, hull="minecraft:stripped_dark_oak_wood[axis=y]", deck="minecraft:dark_oak_planks", masts=((12, 8),),
                sail="minecraft:gray_wool", flag=None, depth=3)
    for x, z in ((6, 4), (18, 5)): b.box(x, dy, z, x + 1, dy, z, AIR)  # holes
    b.chest(8, dy - 1, 4, "treasure", "east"); b.chest(16, 1, 4, "easy", "east")
    b.guards("fishman", ((20, 4),), y=dy + 1)

@L("sea_king_bones", "Sea King Skeleton", "easy", BEACH + OCEAN, "seafloor", who="nobody")
def _(b):
    b.bones(0, 0, 3, 34, height=8)
    b.chest(16, 1, 3, "easy", "south")

@L("going_merry_farewell", "Going Merry's Farewell", "easy", BEACH, "land", who="nobody (a quiet farewell)")
def _(b):
    ground(b, 0, 0, 22, 12, "minecraft:sand")
    dy = b.ship(1, 0, 1, 18, 9, hull="minecraft:oak_planks", deck="minecraft:oak_planks", masts=((9, 9),), sail="minecraft:white_wool",
                flag=("minecraft:black_wool", "minecraft:white_wool"), depth=2)
    b.box(19, dy, 4, 20, dy + 2, 6, "minecraft:white_wool"); b.set(21, dy + 1, 5, "minecraft:white_wool")  # the sheep head
    b.chest(5, dy + 1, 5, "easy", "east")

@L("baltigo", "Baltigo (Revolutionary Army HQ)", "easy", ["minecraft:snowy_plains", "minecraft:desert", "minecraft:badlands", "onepiece:egghead"], "land", who="Dragon and Sabo (quest givers)")
def _(b):
    b.box(0, 0, 0, 24, 0, 24, "minecraft:smooth_stone")
    b.room(3, 0, 3, 21, 12, 21, "minecraft:white_concrete", floor="minecraft:light_gray_concrete")
    for f in (6,): b.box(4, f, 4, 20, f, 20, "minecraft:white_concrete"); b.box(5, f, 5, 6, f, 6, AIR)
    for y in range(1, 7): b.set(5, y, 4, ladder("south"))
    b.door(12, 1, 21, h=3, w=1)
    b.flag(1, 1, 1, 14, ("minecraft:red_wool", "minecraft:black_wool"), skull=False)
    b.chest(18, 1, 6, "medium", "west")
    b.npc(10, 1, 12, "dragon", False); b.npc(14, 7, 12, "sabo", False)

@L("navarone", "Navarone (G-8) Fortress", "medium", ["minecraft:stony_shore", "minecraft:windswept_hills", "minecraft:stony_peaks"] + BEACH, "land", who="Marines and Riflemen")
def _(b):
    b.box(0, 0, 0, 22, 14, 22, "minecraft:stone")
    b.room(4, 0, 4, 18, 8, 18, "minecraft:stone_bricks", floor="minecraft:smooth_stone")
    b.box(10, 1, 18, 12, 4, 22, AIR)
    for y in range(9, 15): b.set(11, y, 11, ladder("south")); b.set(11, y, 10, "minecraft:stone")
    b.box(11, 9, 11, 11, 14, 11, AIR)
    for y in range(9, 15): b.set(11, y, 11, ladder("north")); b.set(11, y, 12, "minecraft:stone")
    b.box(0, 15, 0, 22, 15, 22, "minecraft:stone_brick_slab[type=bottom,waterlogged=false]")
    b.chest(6, 1, 6, "marine", "east")
    b.guards("marine", ((8, 12), (14, 12), (11, 8)))
    b.guards("marine_rifle", ((3, 3), (19, 19)), y=16)

@L("ohara_library", "Ohara's Tree of Knowledge", "easy", FOREST + PLAINS, "land", who="Robin (quest giver)")
def _(b):
    ground(b, 0, 0, 24, 24)
    b.cyl(12, 12, 7, 1, 16, "minecraft:oak_wood[axis=y]", hollow=True)
    b.sphere(12, 22, 12, 11, leaves("oak"), ry=6)
    b.box(12, 1, 5, 12, 3, 5, AIR)
    for y in range(1, 15):
        for a in range(0, 360, 20):
            if y % 4:
                t = math.radians(a); b.set(round(12 + 5.6 * math.cos(t)), y, round(12 + 5.6 * math.sin(t)), "minecraft:bookshelf")
    b.set(12, 1, 12, "minecraft:lectern[facing=south,has_book=false,powered=false]")
    b.chest(14, 1, 12, "library", "west")
    b.npc(10, 1, 12, "robin", False)

@L("gray_terminal", "Gray Terminal (Goa's junk heap)", "easy", PLAINS + ["minecraft:savanna", "minecraft:badlands"], "land", who="Bandits")
def _(b):
    ground(b, 0, 0, 22, 22, "minecraft:coarse_dirt")
    import random; r = random.Random(7)
    for _i in range(70):
        x, z = r.randint(0, 22), r.randint(0, 22); h = r.randint(1, 4)
        b.box(x, 1, z, x, h, z, r.choice(["minecraft:cobblestone", "minecraft:gravel", "minecraft:oak_planks", "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]", "minecraft:composter[level=0]"]))
    b.house(8, 8, 6, 6, 3, "minecraft:oak_planks", "minecraft:cobblestone")
    b.chest(10, 1, 10, "easy", "south")
    b.guards("bandit", ((3, 19), (19, 3)))

@L("momoiro_island", "Momoiro Island (Kamabakka Kingdom)", "easy", ["onepiece:amazon_lily", "minecraft:flower_forest", "onepiece:zou"] + JUNGLE, "land", who="nobody (very pink)")
def _(b):
    ground(b, 0, 0, 20, 20, "minecraft:pink_concrete")
    b.house(4, 4, 12, 10, 5, "minecraft:pink_terracotta", "minecraft:magenta_terracotta", floor="minecraft:pink_wool")
    for x, z in ((1, 1), (18, 18), (1, 18), (18, 1)): b.sphere(x, 3, z, 1.8, "minecraft:pink_wool")
    b.chest(6, 1, 6, "easy", "east")

@L("rusukaina", "Rusukaina Training Grounds", "hard", ["onepiece:little_garden", "onepiece:amazon_lily"] + JUNGLE, "land", who="War Beasts (the island's wild giants)")
def _(b):
    ground(b, 0, 0, 26, 26, "minecraft:podzol[snowy=false]")
    for (x, z) in ((4, 4), (22, 5), (5, 21), (21, 21)): b.tree(x, 1, z, 9, "jungle", 3.5)
    b.cyl(13, 13, 5, 1, 1, "minecraft:coarse_dirt")
    for (x, z) in ((10, 10), (16, 16), (16, 10)): b.box(x, 1, z, x, 2, z, "minecraft:mossy_cobblestone")
    b.set(13, 1, 13, CAMPFIRE)
    b.chest(13, 1, 16, "hard", "north")
    b.guards("war_beast", ((6, 13), (20, 13)))

@L("banaro_island", "Banaro Island (burnt town)", "medium", PLAINS + DESERT + ["minecraft:savanna"], "land", who="Blackbeard Pirates (stragglers)")
def _(b):
    ground(b, 0, 0, 24, 24, "minecraft:coarse_dirt")
    for (x, z) in ((2, 2), (14, 2), (2, 14)):
        b.house(x, z, 8, 7, 3, "minecraft:blackstone", "minecraft:basalt[axis=y]", floor="minecraft:blackstone")
        b.box(x + 3, 4, z + 2, x + 5, 6, z + 4, AIR)
    b.sphere(17, 0, 17, 5, AIR); b.sphere(17, -1, 17, 5, "minecraft:magma_block", hollow=True)
    b.chest(4, 1, 4, "medium", "south")
    b.guards("pirate", ((12, 12), (6, 20)))
    b.guards("blackbeard_pirate", ((20, 8),))

@L("tequila_wolf", "Tequila Wolf (the endless bridge)", "medium", OCEAN + BEACH, "sea", who="Marine overseers")
def _(b):
    b.box(0, 0, 0, 44, 5, 8, "minecraft:stone_bricks"); b.waterline = -1
    for x in range(0, 45, 8): b.box(x, -12, 2, x + 2, -1, 6, "minecraft:stone_bricks")  # pillars into the sea
    b.box(0, 6, 0, 44, 6, 0, "minecraft:stone_brick_wall[east=low,north=none,south=none,up=true,waterlogged=false,west=low]")
    b.box(0, 6, 8, 44, 6, 8, "minecraft:stone_brick_wall[east=low,north=none,south=none,up=true,waterlogged=false,west=low]")
    b.box(40, 6, 2, 44, 6, 6, "minecraft:cobblestone")
    b.chest(4, 6, 4, "medium", "east")
    b.guards("marine", ((12, 4), (28, 4)), y=6)
    b.guards("marine_rifle", ((20, 4),), y=6)

@L("boin_archipelago", "Boin Archipelago", "easy", JUNGLE + ["onepiece:little_garden"], "land", who="nobody (giant plants)")
def _(b):
    ground(b, 0, 0, 22, 22, "minecraft:moss_block")
    for (x, z) in ((5, 5), (16, 6), (8, 16)):
        b.cyl(x, z, 1, 1, 10, "minecraft:mushroom_stem[down=true,east=true,north=true,south=true,up=true,west=true]")
        b.disk(x, 11, z, 4, "minecraft:red_mushroom_block[down=true,east=true,north=true,south=true,up=true,west=true]")
    for (x, z) in ((18, 18), (3, 19)):
        b.box(x, 1, z, x, 6, z, "minecraft:green_terracotta"); b.sphere(x, 7, z, 2, "minecraft:yellow_wool")
    b.chest(11, 1, 11, "easy", "south")

@L("den_den_outpost", "Den Den Mushi Relay Outpost", "easy", PLAINS + BEACH + ["minecraft:savanna"], "land", who="a Marine Recruit")
def _(b):
    ground(b, 0, 0, 10, 10)
    b.sphere(5, 1, 5, 4, "minecraft:brown_terracotta", hollow=True, upper=True)  # the snail shell
    b.sphere(5, 1, 5, 2.5, "minecraft:pink_terracotta", upper=True)
    b.box(5, 1, 1, 5, 2, 1, AIR)
    b.box(9, 1, 5, 9, 4, 5, "minecraft:lime_terracotta")
    b.chest(3, 1, 5, "easy", "east")
    b.guards("marine_recruit", ((5, 8),))
