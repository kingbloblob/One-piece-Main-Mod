"""Regional furniture sets (added 2026-11-05, thread "Expand building and base tools"): five pieces each for
Wano, Alabasta, Skypiea, Fishman Island, the Marines, Whole Cake Island and Water 7, so a room can look like
it belongs to one island. Same format as props.py (boxes in pixels, drawn facing north, front at z=0)."""

def T(n): return "minecraft:block/" + n
def O(n): return "onepiece:block/" + n
def F(n): return "onepiece:block/furniture/" + n


def wano():
    lac, dark, gold = O("wano_lacquer_planks"), T("dark_oak_planks"), T("gold_block")
    return [
        dict(id="wano_tansu", name="Wano Tansu Chest", mat="wood", cat="top", storage=27,
             tex={"l": lac, "d": dark, "i": T("iron_block")},
             boxes=[(0, 0, 1, 16, 14, 16, "l"), (0, 14, 0.5, 16, 16, 16, "d"),
                    (1, 1, 0.5, 15, 4.5, 1, "d"), (1, 5.5, 0.5, 15, 9, 1, "d"), (1, 10, 0.5, 7.5, 13, 1, "d"), (8.5, 10, 0.5, 15, 13, 1, "d"),
                    (7, 2.5, 0, 9, 3.25, 0.5, "i"), (7, 7, 0, 9, 7.75, 0.5, "i"), (3.5, 11.25, 0, 5, 12, 0.5, "i"), (11, 11.25, 0, 12.5, 12, 0.5, "i")],
             recipe=(["SSS", "PCP"], {"S": "onepiece:wano_lacquer_slab", "P": "onepiece:wano_lacquer_planks", "C": "minecraft:chest"}, 1),
             desc="A lacquered Wano chest of drawers with iron pulls. It holds as much as a chest. Right-click to open it."),
        dict(id="engawa_bench", name="Engawa Bench", mat="wood", cat="other", seat=8, tex={"l": lac, "d": dark},
             boxes=[(0, 6, 2, 16, 8, 14, "l"), (1, 0, 3, 3, 6, 13, "d"), (13, 0, 3, 15, 6, 13, "d"), (3, 2, 7, 13, 3, 9, "d")],
             recipe=(["SSS", "D D"], {"S": "onepiece:wano_lacquer_slab", "D": "minecraft:dark_oak_fence"}, 2),
             desc="A low veranda bench from Wano, for watching the cherry blossoms fall. Right-click with an empty hand to sit down."),
        dict(id="golden_byobu", name="Golden Byobu Screen", mat="wood", cat="other",
             tex={"g": gold, "k": T("black_concrete"), "w": O("sakura_petals")},
             boxes=[(0, 0, 12, 6, 16, 13, {"north": "g", "south": "g", "*": "k"}), (5, 0, 13, 11, 16, 14, {"north": "g", "south": "g", "*": "k"}),
                    (10, 0, 12, 16, 16, 13, {"north": "g", "south": "g", "*": "k"}),
                    (0, 15, 11.9, 6, 16, 13.1, "k"), (5, 15, 12.9, 11, 16, 14.1, "k"), (10, 15, 11.9, 16, 16, 13.1, "k")],
             shapeless=(["onepiece:folding_screen", "minecraft:gold_ingot"], 1),
             desc="A gold-leaf folding screen fit for the Shogun's castle. Puts any Wano room in its best light."),
        dict(id="hibachi_brazier", name="Hibachi Brazier", mat="metal", cat="other", light=13,
             tex={"k": T("black_concrete"), "c": T("magma"), "t": T("terracotta")},
             boxes=[(3, 0, 3, 13, 1, 13, "k"), (3.5, 1, 3.5, 12.5, 6, 12.5, "t"), (3, 6, 3, 13, 7, 13, "k"), (4.5, 6, 4.5, 11.5, 6.75, 11.5, "c")],
             shapeless=(["minecraft:clay_ball", "minecraft:iron_ingot", "minecraft:charcoal"], 1),
             desc="A clay charcoal brazier from Wano. Warms the hands on cold nights and gives a soft glow."),
        dict(id="kakejiku_scroll", name="Kakejiku Scroll", mat="wool", cat="other", mount="WALL", solid=False,
             tex={"d": dark, "p": T("white_terracotta"), "i": T("black_concrete"), "r": T("red_terracotta")},
             boxes=[(2, 14, 15, 14, 15, 16, "d"), (2, 1, 15, 14, 2, 16, "d"), (3, 2, 15.5, 13, 14, 16, "p"),
                    (7, 5, 15.4, 9, 12, 15.5, "i"), (9.5, 3, 15.4, 11, 4.5, 15.5, "r")],
             shapeless=(["minecraft:paper", "minecraft:stick", "minecraft:ink_sac", "minecraft:paper"], 1),
             desc="A hanging scroll with brushed ink and a red seal, for the alcove of a Wano room."),
    ]


def alabasta():
    sand, tile = O("alabasta_sandstone_bricks"), O("alabasta_tiles")
    return [
        dict(id="alabasta_divan", name="Alabasta Divan", mat="wool", cat="other", seat=7,
             tex={"s": sand, "o": T("orange_wool"), "r": T("red_wool"), "g": T("gold_block")},
             boxes=[(0, 0, 2, 16, 5, 15, "s"), (0.5, 5, 2.5, 15.5, 7, 13, "o"), (0, 5, 13, 16, 12, 15.5, "r"),
                    (0, 5, 2, 2, 9, 13, "s"), (14, 5, 2, 16, 9, 13, "s"), (0, 11.5, 13, 16, 12.5, 15.5, "g")],
             recipe=(["OOO", "SSS"], {"O": "minecraft:orange_wool", "S": "minecraft:sandstone_slab"}, 1),
             desc="A low sandstone couch piled with cushions, like the ones in Alubarna Palace. Right-click with an empty hand to sit down."),
        dict(id="brass_oil_lamp", name="Brass Oil Lamp", mat="metal", cat="other", light=14,
             tex={"g": T("gold_block"), "f": T("glowstone")},
             boxes=[(6, 0, 6, 10, 1, 10, "g"), (5, 1, 5, 11, 4, 11, "g"), (10, 3, 7.5, 13, 4, 8.5, "g"),
                    (3.5, 2, 7.5, 5, 5, 8.5, "g"), (7, 4, 7, 9, 5, 9, "g"), (12, 4, 7.5, 13, 6, 8.5, "f")],
             shapeless=(["minecraft:gold_ingot", "minecraft:torch", "minecraft:gold_nugget"], 1),
             desc="A desert oil lamp of polished brass. Rub it all you like: no genie, just light."),
        dict(id="clay_water_jar", name="Clay Water Jar", mat="stone", cat="other",
             tex={"t": T("terracotta"), "b": T("blue_terracotta"), "w": T("light_blue_concrete")},
             boxes=[(4, 0, 4, 12, 10, 12, "t"), (5.5, 10, 5.5, 10.5, 13, 10.5, "t"), (5, 13, 5, 11, 14, 11, "t"),
                    (3.9, 4, 3.9, 12.1, 5, 12.1, "b"), (6, 13.5, 6, 10, 13.75, 10, "w")],
             recipe=(["T T", "TWT"], {"T": "minecraft:terracotta", "W": "minecraft:water_bucket"}, 2),
             desc="A tall clay jar of cool water, the most precious thing in a drought-stricken land."),
        dict(id="alabasta_rug", name="Alabasta Rug", mat="wool", cat="other",
             tex={"c": tile, "b": T("red_wool"), "y": T("yellow_wool")},
             boxes=[(1, 0, 1, 15, 1, 15, "c"), (0, 0, 0, 16, 1, 1, "b"), (0, 0, 15, 16, 1, 16, "b"), (0, 0, 1, 1, 1, 15, "b"),
                    (15, 0, 1, 16, 1, 15, "b"), (7, 0.05, 7, 9, 1.05, 9, "y")],
             recipe=(["RTR"], {"R": "minecraft:red_carpet", "T": "onepiece:alabasta_tiles"}, 3),
             desc="A desert rug woven in the pattern of Alabasta's palace floors. Flat on the floor like a carpet."),
        dict(id="sand_floor_pillow", name="Sand Floor Pillow", mat="wool", cat="other", seat=4,
             tex={"y": T("yellow_wool"), "o": T("orange_wool"), "g": T("gold_block")},
             boxes=[(1, 0, 1, 15, 3, 15, "y"), (2, 3, 2, 14, 4, 14, "o"), (0.5, 0, 0.5, 1.5, 2, 1.5, "g"),
                    (14.5, 0, 0.5, 15.5, 2, 1.5, "g"), (0.5, 0, 14.5, 1.5, 2, 15.5, "g"), (14.5, 0, 14.5, 15.5, 2, 15.5, "g")],
             shapeless=(["minecraft:yellow_wool", "minecraft:orange_wool", "minecraft:gold_nugget"], 2),
             desc="A big tasselled floor pillow from Alabasta. Right-click with an empty hand to sit down."),
    ]


def skypiea():
    cloud, gold = O("island_cloud"), O("shandora_gold_bricks")
    return [
        dict(id="cloud_sofa", name="Cloud Sofa", mat="wool", cat="other", seat=7, tex={"c": cloud},
             boxes=[(0, 0, 2, 16, 6, 14, "c"), (0, 6, 11, 16, 13, 15, "c"), (0, 6, 2, 3, 10, 11, "c"), (13, 6, 2, 16, 10, 11, "c")],
             recipe=(["C  ", "CCC"], {"C": "onepiece:island_cloud"}, 1),
             desc="A sofa of sea cloud from Skypiea, soft as it looks. Right-click with an empty hand to sit down."),
        dict(id="cloud_table", name="Cloud Table", mat="wool", cat="top", tex={"c": cloud},
             boxes=[(0, 12, 0, 16, 16, 16, "c"), (5, 0, 5, 11, 12, 11, "c"), (3, 0, 3, 13, 3, 13, "c")],
             recipe=(["CCC", " C ", " C "], {"C": "onepiece:island_cloud"}, 1),
             desc="A puffy table of island cloud. Things you set on it don't sink in. Much."),
        dict(id="cloud_stool", name="Cloud Stool", mat="wool", cat="other", seat=8, tex={"c": cloud},
             boxes=[(3, 0, 3, 13, 8, 13, "c"), (2, 5, 2, 14, 8, 14, "c")],
             recipe=([" C ", "C C"], {"C": "onepiece:island_cloud"}, 2),
             desc="A little stool of island cloud. Right-click with an empty hand to sit down."),
        dict(id="shandian_drum", name="Shandian War Drum", mat="wood", cat="top",
             tex={"w": T("stripped_jungle_log"), "h": T("white_wool"), "g": gold, "r": T("red_wool")},
             boxes=[(2, 0, 2, 14, 11, 14, "w"), (2.5, 11, 2.5, 13.5, 11.5, 13.5, "h"), (1.9, 2, 1.9, 14.1, 3, 14.1, "g"),
                    (1.9, 8, 1.9, 14.1, 9, 14.1, "g"), (1.8, 4, 7.5, 2, 7, 8.5, "r"), (14, 4, 7.5, 14.2, 7, 8.5, "r")],
             shapeless=(["minecraft:jungle_log", "minecraft:leather", "minecraft:gold_nugget"], 1),
             desc="A great drum of the Shandia, beaten before battle and at the Bell of Shandora's festival."),
        dict(id="sky_shell_lamp", name="Sky Shell Lamp", mat="metal", cat="other", light=14,
             tex={"s": T("white_terracotta"), "p": O("pearl_block"), "g": gold},
             boxes=[(3, 0, 3, 13, 1, 13, "g"), (4, 1, 4, 12, 3, 12, "s"), (5, 3, 5, 11, 9, 11, "p"), (6, 9, 6, 10, 10, 10, "s")],
             shapeless=(["minecraft:nautilus_shell", "minecraft:glowstone_dust", "minecraft:gold_nugget"], 1),
             desc="A Lamp Dial set in a seashell, the way they light homes on Angel Island."),
    ]


def fishman():
    coral, pearl = O("coral_bricks"), O("pearl_block")
    return [
        dict(id="coral_throne_chair", name="Coral Chair", mat="stone", cat="other", seat=9,
             tex={"c": coral, "p": T("prismarine"), "k": T("brain_coral_block")},
             boxes=[(2, 0, 2, 14, 7, 14, "c"), (2, 7, 2, 14, 9, 14, "k"), (2, 9, 12, 14, 16, 14, "c"),
                    (3, 16, 12.5, 5, 18, 13.5, "k"), (7, 16, 12.5, 9, 19, 13.5, "k"), (11, 16, 12.5, 13, 18, 13.5, "k")],
             recipe=(["B  ", "BBB", "B B"], {"B": "onepiece:coral_bricks"}, 1),
             desc="A chair grown from coral, like those in Ryugu Palace. Right-click with an empty hand to sit down."),
        dict(id="coral_table", name="Coral Table", mat="stone", cat="top",
             tex={"c": coral, "p": T("prismarine")},
             boxes=[(0, 13, 0, 16, 16, 16, "p"), (5, 0, 5, 11, 13, 11, "c"), (3, 0, 3, 13, 2, 13, "c")],
             recipe=(["SSS", " B ", " B "], {"S": "minecraft:prismarine_slab", "B": "onepiece:coral_bricks"}, 1),
             desc="A prismarine table on a coral stem, from Fishman Island."),
        dict(id="pearl_lamp", name="Pearl Lamp", mat="stone", cat="other", light=15,
             tex={"c": coral, "p": pearl},
             boxes=[(5, 0, 5, 11, 3, 11, "c"), (4, 3, 4, 12, 11, 12, "p")],
             shapeless=(["onepiece:pearl_block", "minecraft:glowstone_dust", "onepiece:coral_bricks"], 1),
             desc="A glowing pearl as big as your head, set on coral. The mermaids of Fishman Island light their cafes with them."),
        dict(id="giant_clam_basin", name="Giant Clam Basin", mat="stone", cat="other",
             tex={"s": T("white_terracotta"), "w": T("light_blue_concrete"), "p": pearl},
             boxes=[(1, 0, 1, 15, 4, 15, "s"), (2, 3.5, 2, 14, 4.05, 14, "w"), (7, 4, 7, 9, 6, 9, "p"), (1, 4, 13, 15, 8, 15, "s")],
             shapeless=(["minecraft:white_terracotta", "minecraft:water_bucket", "onepiece:pearl_block"], 1),
             desc="A giant clam shell full of water with a pearl inside. A fountain, a bath or a bird bath."),
        dict(id="bubble_dome_lamp", name="Bubble Dome Lamp", mat="stone", cat="other", light=15,
             tex={"c": coral, "b": O("bubble_glass"), "g": T("glowstone")},
             boxes=[(3, 0, 3, 13, 2, 13, "c"), (6, 2, 6, 10, 6, 10, "g"), (3.5, 2, 3.5, 12.5, 11, 12.5, "b")],
             shapeless=(["onepiece:bubble_glass", "minecraft:glowstone_dust", "onepiece:coral_bricks"], 1),
             desc="A glow inside a bubble dome, like the lights of the Fishman District."),
    ]


def marines():
    dark, iron = T("dark_oak_planks"), T("iron_block")
    return [
        dict(id="marine_desk", name="Marine Officer's Desk", mat="wood", cat="top", storage=9,
             tex={"t": dark, "s": T("stripped_dark_oak_log"), "b": T("blue_concrete"), "w": T("white_concrete"), "i": iron},
             boxes=[(0, 14, 0, 16, 16, 16, "t"), (0, 0, 1, 4, 14, 15, "s"), (12, 0, 1, 16, 14, 15, "s"), (4, 9, 14, 12, 14, 15, "s"),
                    (0.5, 9, 0.5, 3.5, 13, 1, "t"), (12.5, 9, 0.5, 15.5, 13, 1, "t"), (4, 11.5, 0.9, 12, 14, 1.4, "b"),
                    (7, 12, 0.7, 9, 13.5, 0.9, "w"), (1.5, 10.75, 0.25, 2.5, 11.25, 0.5, "i")],
             recipe=(["SSS", "PBP"], {"S": "minecraft:dark_oak_slab", "P": "minecraft:dark_oak_planks", "B": "minecraft:blue_dye"}, 1),
             desc="A Navy officer's desk with drawers that hold 9 stacks. Right-click to open it. Justice never sleeps (but its paperwork does)."),
        dict(id="marine_locker", name="Marine Locker", mat="metal", cat="top", storage=27,
             tex={"g": T("light_gray_concrete"), "k": T("black_concrete"), "b": T("blue_concrete")},
             boxes=[(1, 0, 2, 15, 16, 15, "g"), (1.5, 1, 1.5, 7.75, 15, 2, "g"), (8.25, 1, 1.5, 14.5, 15, 2, "g"),
                    (2.5, 12, 1.25, 6.5, 12.5, 1.5, "k"), (2.5, 13, 1.25, 6.5, 13.5, 1.5, "k"), (9.5, 12, 1.25, 13.5, 12.5, 1.5, "k"),
                    (9.5, 13, 1.25, 13.5, 13.5, 1.5, "k"), (1, 7, 1.4, 15, 8, 1.6, "b")],
             recipe=(["IBI", "ICI", "III"], {"I": "minecraft:iron_nugget", "B": "minecraft:blue_dye", "C": "minecraft:chest"}, 1),
             desc="A grey steel locker from a Marine base, with a blue Navy stripe. It holds as much as a chest. Right-click to open it."),
        dict(id="marine_flag_stand", name="Marine Flag Stand", mat="metal", cat="other",
             tex={"i": iron, "w": T("white_wool"), "b": T("blue_wool")},
             boxes=[(5, 0, 5, 11, 1, 11, "i"), (7.5, 1, 7.5, 8.5, 16, 8.5, "i"),
                    (8.5, 8, 7.75, 16, 15.5, 8.25, "w"), (8.5, 11, 7.7, 16, 12.5, 8.3, "b")],
             shapeless=(["minecraft:white_banner", "minecraft:blue_dye", "minecraft:iron_ingot"], 1),
             desc="The Navy's flag on a steel pole. Every Marine office has one."),
        dict(id="marine_office_chair", name="Marine Office Chair", mat="metal", cat="other", seat=9,
             tex={"n": T("blue_wool"), "i": iron, "k": T("black_concrete")},
             boxes=[(3, 7, 3, 13, 9, 13, "n"), (3, 9, 12, 13, 16, 13.5, "n"), (7, 1, 7, 9, 7, 9, "k"),
                    (2, 0, 7.5, 14, 1, 8.5, "i"), (7.5, 0, 2, 8.5, 1, 14, "i")],
             recipe=(["W  ", "WWW", " I "], {"W": "minecraft:blue_wool", "I": "minecraft:iron_ingot"}, 1),
             desc="A padded swivel chair for a Marine office. Right-click with an empty hand to sit down."),
        dict(id="marine_supply_crate", name="Marine Supply Crate", mat="wood", cat="top",
             tex={"c": T("spruce_planks"), "b": T("blue_concrete"), "w": T("white_concrete")},
             boxes=[(0, 0, 0, 16, 16, 16, "c"), (-0.05, 6, -0.05, 16.05, 10, 16.05, {"up": "c", "down": "c", "*": "b"}),
                    (6.5, 6.5, -0.1, 9.5, 9.5, 0, "w")],
             shapeless=(["onepiece:small_crate", "minecraft:blue_dye"], 1),
             desc="A crate stamped with the Navy's mark. Marine bases and battleships are stacked with them."),
    ]


def whole_cake():
    cookie, frost, choc, cane = O("cookie_bricks"), O("frosting_block"), O("chocolate_block"), O("candy_cane_block")
    return [
        dict(id="candy_chair", name="Candy Chair", mat="wood", cat="other", seat=9,
             tex={"c": cane, "f": frost, "k": choc},
             boxes=[(2, 7, 2, 14, 9, 14, "f"), (2, 0, 2, 4, 7, 4, "c"), (12, 0, 2, 14, 7, 4, "c"), (2, 0, 12, 4, 7, 14, "c"),
                    (12, 0, 12, 14, 7, 14, "c"), (2, 9, 12, 14, 16, 14, "k")],
             recipe=(["C  ", "CCC", "I I"], {"C": "onepiece:chocolate_block", "I": "onepiece:candy_cane_block"}, 1),
             desc="A chair you could eat: chocolate back, frosting seat, candy-cane legs. From Whole Cake Island. Right-click with an empty hand to sit down."),
        dict(id="cake_table", name="Cake Table", mat="wood", cat="top",
             tex={"k": cookie, "f": frost, "r": T("red_concrete")},
             boxes=[(1, 0, 1, 15, 12, 15, "k"), (0, 12, 0, 16, 16, 16, "f"), (7, 16, 7, 9, 17.5, 9, "r")],
             recipe=(["FFF", "KKK"], {"F": "onepiece:frosting_block", "K": "onepiece:cookie_bricks"}, 1),
             desc="A table that is also a cake. Big Mom would never let it last the night."),
        dict(id="lollipop_lamp", name="Lollipop Lamp", mat="wood", cat="other", light=14,
             tex={"w": T("white_concrete"), "p": T("pink_concrete"), "g": T("glowstone")},
             boxes=[(7.5, 0, 7.5, 8.5, 9, 8.5, "w"), (4, 9, 7, 12, 16, 9, "p"), (5, 10, 6.9, 11, 15, 9.1, "g"), (6, 0, 6, 10, 1, 10, "w")],
             shapeless=(["minecraft:sugar", "minecraft:pink_dye", "minecraft:glowstone_dust", "minecraft:stick"], 1),
             desc="A giant glowing lollipop on a stick, the street lamps of Sweet City."),
        dict(id="cookie_cabinet", name="Cookie Cabinet", mat="wood", cat="top", storage=27,
             tex={"k": cookie, "c": choc, "f": frost},
             boxes=[(0, 0, 1, 16, 15, 16, "k"), (0, 15, 0.5, 16, 16, 16, "f"), (1, 1, 0.5, 7.75, 14, 1, "c"), (8.25, 1, 0.5, 15, 14, 1, "c"),
                    (6.5, 7, 0, 7.25, 9, 0.5, "f"), (8.75, 7, 0, 9.5, 9, 0.5, "f")],
             recipe=(["FFF", "KCK", "KKK"], {"F": "onepiece:frosting_block", "K": "onepiece:cookie_bricks", "C": "minecraft:chest"}, 1),
             desc="A cupboard of cookie with chocolate doors and frosting trim. It holds as much as a chest. Right-click to open it."),
        dict(id="cupcake_stool", name="Cupcake Stool", mat="wool", cat="other", seat=8,
             tex={"p": T("pink_concrete"), "f": frost, "r": T("red_concrete")},
             boxes=[(3, 0, 3, 13, 5, 13, "p"), (2.5, 5, 2.5, 13.5, 8, 13.5, "f"), (7, 8, 7, 9, 9.5, 9, "r")],
             shapeless=(["onepiece:frosting_block", "minecraft:pink_dye", "minecraft:paper"], 2),
             desc="A stool shaped like a cupcake, cherry on top. Right-click with an empty hand to sit down."),
    ]


def water7():
    canal, cob, iron = O("canal_bricks"), O("water7_cobbles"), T("iron_block")
    return [
        dict(id="water7_street_lamp", name="Water 7 Street Lamp", mat="metal", cat="other", light=15,
             tex={"s": canal, "k": T("black_concrete"), "g": T("glowstone")},
             boxes=[(5, 0, 5, 11, 2, 11, "s"), (7, 2, 7, 9, 12, 9, "k"), (5, 12, 5, 11, 13, 11, "k"), (5.5, 13, 5.5, 10.5, 16, 10.5, "g"),
                    (5, 15.5, 5, 11, 16.5, 11, "k")],
             recipe=(["G", "I", "B"], {"G": "minecraft:glowstone", "I": "minecraft:iron_bars", "B": "onepiece:canal_bricks"}, 2),
             desc="A black iron lamp from the canal streets of Water 7."),
        dict(id="canal_bench", name="Canal Bench", mat="stone", cat="other", seat=8,
             tex={"s": canal, "w": T("spruce_planks")},
             boxes=[(0, 6, 2, 16, 8, 12, "w"), (1, 0, 3, 4, 6, 11, "s"), (12, 0, 3, 15, 6, 11, "s"), (0, 10, 11, 16, 14, 12.5, "w"),
                    (1, 8, 11, 3, 10, 12, "s"), (13, 8, 11, 15, 10, 12, "s")],
             recipe=(["S  ", "SSS", "B B"], {"S": "minecraft:spruce_slab", "B": "onepiece:canal_bricks"}, 2),
             desc="A bench on stone feet by the water, where Water 7 waits for the Yagara Bulls. Right-click with an empty hand to sit down."),
        dict(id="blueprint_board", name="Shipwright's Blueprint Board", mat="wood", cat="other", mount="WALL", solid=False,
             tex={"p": T("spruce_planks"), "b": T("blue_terracotta"), "w": T("white_concrete")},
             boxes=[(0, 1, 15, 16, 15, 16, "p"), (1, 2, 14.5, 15, 14, 15, "b"),
                    (3, 6, 14.4, 13, 6.5, 14.5, "w"), (4, 6.5, 14.4, 12, 7, 14.5, "w"), (7.75, 7, 14.4, 8.25, 12, 14.5, "w"),
                    (8.25, 8, 14.4, 11, 11, 14.5, "w")],
             shapeless=(["minecraft:paper", "minecraft:blue_dye", "minecraft:spruce_slab"], 1),
             desc="A ship's blueprint pinned to a board, from the Galley-La docks. (Rumor says the Pluton plans looked a lot like it.)"),
        dict(id="shipwright_tool_chest", name="Shipwright's Tool Chest", mat="metal", cat="top", storage=27,
             tex={"r": T("red_concrete"), "i": iron, "k": T("black_concrete")},
             boxes=[(1, 0, 2, 15, 13, 15, "r"), (1.5, 1, 1.5, 14.5, 4, 2, "r"), (1.5, 5, 1.5, 14.5, 8, 2, "r"), (1.5, 9, 1.5, 14.5, 12, 2, "r"),
                    (6, 2.25, 1.25, 10, 2.75, 1.5, "i"), (6, 6.25, 1.25, 10, 6.75, 1.5, "i"), (6, 10.25, 1.25, 10, 10.75, 1.5, "i"),
                    (1, 13, 2, 15, 14, 15, "k")],
             recipe=(["IRI", "ICI"], {"I": "minecraft:iron_ingot", "R": "minecraft:red_dye", "C": "minecraft:chest"}, 1),
             desc="A red steel tool chest on a Galley-La slipway. It holds as much as a chest. Right-click to open it."),
        dict(id="mooring_bollard", name="Mooring Bollard", mat="stone", cat="top",
             tex={"i": T("polished_blackstone"), "r": O("rope")},
             boxes=[(4, 0, 4, 12, 10, 12, "i"), (3, 10, 3, 13, 12, 13, "i"), (3.9, 5, 3.9, 12.1, 7, 12.1, "r")],
             recipe=(["B", "B", "R"], {"B": "minecraft:polished_blackstone", "R": "onepiece:rope_coil"}, 1),
             desc="An iron bollard to tie a ship to, with a rope round it. Line them along a quay."),
    ]


def regional_sets():
    return wano() + alabasta() + skypiea() + fishman() + marines() + whole_cake() + water7()
