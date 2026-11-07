#!/usr/bin/env python3
"""Writes src/main/resources/onepiece/item_descriptions.json: the short grey line shown under
every One Piece item's name (recipe viewer thread). Edit the HAND dict or the templates, then rerun:
    python3 gen_descriptions.py /mnt/project-files/one-piece-mod/source
Devil Fruits (own tooltip), Wanted Posters and Vivre Cards (built from characters.json in code) are not listed here."""
import json, sys, os, glob, re

HAND = {
 # Ships and navigation
 "berry": "The currency of the seas. Earned from bosses, quests and bounties; spent at traders.",
 "sea_chart": "Right-click to chart the nearest unexplored island. Becomes a map marked with a red X.",
 "bounty_poster": "A blank Wanted Poster. Your own bounty shows up on it.",
 "recruitment_board": "Place it to hire crewmates who wander by.",
 "tavern_blueprint": "Shows how to build a Pirate Tavern, where crewmates gather.",
 "ships_wheel": "Build a ship around it, then right-click to set sail. The wheel faces the bow.",
 "jolly_roger": "Right-click to paint your own pirate flag. Place it on your ship.",
 "figurehead_merry": "The Going Merry's sheep head. Decoration for the bow of your ship.",
 "figurehead_sunny": "The Thousand Sunny's lion head. Decoration for the bow of your ship.",
 "figurehead_moby": "The Moby Dick's whale head. Decoration for the bow of your ship.",
 "cannon": "A ship's cannon. Decoration for your deck.",
 "anchor": "A heavy iron anchor. Decoration for your ship.",
 "porthole": "A round ship window.",
 "rope_coil": "A coil of rigging rope. Decoration for your deck.",
 "log_pose": "Records each island you stand on for 15 seconds and points to the next one.",
 "eternal_pose": "Always points to one island, no matter how far you sail.",
 "den_den_mushi": "A snail phone. Call your crew and give them orders from far away.",
 "sea_king_bait": "Throw it into the sea to lure out a Sea King. Be ready to fight.",
 "sea_king_meat": "Raw meat from a Sea King. Cook it for a feast.",
 "cooked_sea_king_meat": "Meat on the bone, Luffy's favourite. Very filling.",
 "pirate_bento": "A packed lunch cooked at the Ship's Galley. Restores lots of hunger.",
 "bone_in_meat": "Luffy's favourite, from the Ship's Galley. Gives Strength for a minute.",
 "seafood_paella": "From the Ship's Galley. Breathe underwater for 3 minutes and swim fast for a bit.",
 "mikan_sorbet": "Made with Nami's mikans at the Ship's Galley. Run faster for 2 minutes.",
 "fire_curry": "So spicy fire stops hurting: Fire Resistance for 3 minutes. Cooked at the Ship's Galley.",
 "herbal_tea": "Chopper's remedy from the Ship's Galley. Heals you slowly for 20 seconds.",
 "all_blue_feast": "The crew's big meal before a fight: extra hearts, Strength and Resistance for 2 minutes. Needs a Cook in your crew.",
 "sea_king_stew": "A rich stew cooked at the Ship's Galley.",
 "rumble_ball": "Chopper's invention. Gives a short burst of strength and speed.",
 # Stations
 "shipwright_bench": "Crafting station for ship parts. Ingredients only need to be in your inventory.",
 "ships_galley": "Crafting station for cooking pirate food.",
 "navigators_desk": "Crafting station for sea charts and poses (Tier 2).",
 "seastone_workbench": "Crafting station for seastone gear (Tier 3).",
 "swordsmith_forge": "Crafting station for famous blades and weapon upgrades (Tier 4).",
 # Swords and styles
 "wado_ichimonji": "Zoro's white-hilted katana. One of the 21 Great Grade swords.",
 "sandai_kitetsu": "A cursed Grade sword. Said to bring misfortune to its owner.",
 "shusui": "Ryuma's black blade. Dropped by Gecko Moria.",
 "enma": "Oden's sword that draws out the wielder's Haki. Dropped by Kaido.",
 "yoru": "Mihawk's black blade, the strongest of the Supreme Grade swords. Dropped by Mihawk.",
 "dojo_scroll_santoryu": "Right-click to learn Santoryu, Zoro's three sword style.",
 "dojo_scroll_black_leg": "Right-click to learn Black Leg Style, Sanji's kicks.",
 "dojo_scroll_fishman_karate": "Right-click to learn Fish-Man Karate, Jinbe's water-shaking fists.",
 "dojo_scroll_rokushiki": "Right-click to learn Rokushiki, the six powers of the Marines.",
 "dojo_scroll_ryusoken": "Right-click to learn Ryusoken, Sabo's crushing claw.",
 "dojo_scroll_nitoryu": "Right-click to learn Oden Nitoryu, the two sword style of Wano.",
 "dojo_scroll_kitsunebi": "Right-click to learn Kitsunebi-ryu, Kin'emon's fire-cutting style.",
 "dojo_scroll_soul_fencing": "Right-click to learn Soul King Fencing, Brook's icy blade.",
 "dojo_scroll_fist_of_love": "Right-click to learn Fist of Love, Garp's brawling.",
 "dojo_scroll_sogeking": "Right-click to learn Sogeking Sniping, Usopp's long shots.",
 # Seastone and island resources
 "seastone_ore": "Seastone ore. Seastone drains the power of Devil Fruit users.",
 "deepslate_seastone_ore": "Deep seastone ore. Seastone drains the power of Devil Fruit users.",
 "seastone_block": "A block of solid seastone.",
 "raw_seastone": "Smelt it into a seastone ingot.",
 "seastone_ingot": "Used at the Seastone Workbench to make gear that stops Devil Fruit users.",
 "seastone_jitte": "Smoker's seastone weapon. Hits weaken Devil Fruit users.",
 "seastone_cuffs": "Use on a Devil Fruit user to stop their powers.",
 "adam_log": "Wood from the Treasure Tree Adam, the strongest wood in the world.",
 "adam_planks": "Planks of Adam wood. Franky built the Thousand Sunny from it.",
 "island_cloud": "Solid sky island cloud you can stand on.",
 "sea_cloud": "Milky sea cloud from round the sky islands. Slow to wade through.",
 "tamahagane_ore": "Ore of Wano's jewel steel, used for katanas.",
 "deepslate_tamahagane_ore": "Deep ore of Wano's jewel steel, used for katanas.",
 "wapometal_ore": "Ore of Wapol's edible metal, used for armor.",
 "deepslate_wapometal_ore": "Deep ore of Wapol's edible metal, used for armor.",
 "shandora_gold_ore": "Gold from the lost city of Shandora.",
 "sulfur_ore": "Sulfur ore from volcanic islands.",
 "nether_sulfur_ore": "Sulfur ore from the burning depths.",
 "deepslate_kokuto_ore": "Ore of black steel, found very deep underground.",
 "shell_sand": "Sand full of sky island shells. Sift it for Dial Shells.",
 "oyster_gravel": "Gravel full of oysters. Sometimes hides a Sea Pearl.",
 "poneglyph": "An unbreakable stone carved with ancient text. Make rubbings with an archaeologist in your crew.",
 "raw_tamahagane": "Smelt it into a Tamahagane Ingot.",
 "tamahagane_ingot": "Wano's jewel steel. Used to forge katanas.",
 "raw_wapometal": "Smelt it into a Wapometal Ingot.",
 "wapometal_ingot": "Used to make Wapometal armor.",
 "raw_shandora_gold": "Smelt it into a Shandora Gold Ingot.",
 "shandora_gold_ingot": "Ancient gold from Shandora. Valuable and decorative.",
 "sulfur": "Used for gunpowder and explosive ammo.",
 "raw_kokuto": "Smelt it into Kokuto Black Steel.",
 "kokuto_ingot": "The black steel of the strongest blades.",
 "dial_shell": "A sky island shell. Crafted into Dials that store light, wind, fire or impact.",
 "sea_pearl": "A rare pearl from oyster gravel and Sea King treasure.",
 "yarukiman_resin": "Resin from Sabaody's mangroves. Used for bubble coating.",
 "sea_king_scale": "A tough scale from a Sea King. Used for armor.",
 "kraken_ink": "Ink from a Kraken. Needed to make Poneglyph rubbings.",
 "dragon_scale": "A scale from the Punk Hazard Dragon. Used for the best armor.",
 "flash_dial": "Right-click to release a blinding flash of stored light.",
 "breath_dial": "Right-click to release a gust of stored wind.",
 "bubble_coating": "Coats your ship in a bubble so it can dive under the sea.",
 "tamahagane_katana": "A katana forged from Wano's jewel steel.",
 "kokuto_blade": "A black steel blade, among the strongest swords there are.",
 "wapometal_helmet": "Armor made from Wapometal.", "wapometal_chestplate": "Armor made from Wapometal.",
 "wapometal_leggings": "Armor made from Wapometal.", "wapometal_boots": "Armor made from Wapometal.",
 "sea_king_scale_helmet": "Armor made from Sea King scales.", "sea_king_scale_chestplate": "Armor made from Sea King scales.",
 "sea_king_scale_leggings": "Armor made from Sea King scales.", "sea_king_scale_boots": "Armor made from Sea King scales.",
 "dragon_scale_helmet": "Armor made from dragon scales. The toughest armor of the seas.",
 "dragon_scale_chestplate": "Armor made from dragon scales. The toughest armor of the seas.",
 "dragon_scale_leggings": "Armor made from dragon scales. The toughest armor of the seas.",
 "dragon_scale_boots": "Armor made from dragon scales. The toughest armor of the seas.",
 "diving_helmet": "A Fishman diving helmet. Breathe underwater.",
 # Guns, ammo and weapons
 "flintlock_pistol": "A pirate's pistol. Ammo goes in your off hand or inventory.",
 "marine_rifle": "The standard Marine rifle. Longer range than a pistol.",
 "tommy_gun": "Capone Bege's machine gun. Fires quick bursts.",
 "hand_cannon": "A cannon you can carry. Slow, but hits hard.",
 "senriku": "Van Augur's sniper rifle. Hits targets very far away.",
 "kabuto": "Usopp's slingshot. Fires Pop Greens and star ammo.",
 "kuro_kabuto": "Usopp's upgraded black slingshot.",
 "bullet": "Ammo for guns.",
 "seastone_bullet": "Gun ammo that weakens Devil Fruit users.",
 "cannonball": "Ammo for the Hand Cannon.",
 "lead_star": "Slingshot ammo. A heavy lead ball.",
 "exploding_star": "Slingshot ammo that explodes on hit.",
 "tabasco_star": "Slingshot ammo that sets targets on fire.",
 "pop_green": "Slingshot ammo: a seed that bursts into a plant on hit.",
 "hassaikai": "Kaido's huge spiked club. Dropped by Kaido.",
 "murakumogiri": "Whitebeard's bisento. Dropped by Whitebeard.",
 "golden_hook": "Crocodile's golden hook. Dropped by Crocodile.",
 "punisher": "Killer's spinning blades. Dropped by Killer.",
 "mogura": "Katakuri's trident. Dropped by Katakuri.",
 "nonosama_bo": "Enel's golden staff. Dropped by Enel.",
 "kiribachi": "Arlong's saw-toothed sword.",
 "neko_no_te": "Kuro's cat-claw blades. Fast attacks.",
 "shigure": "Tashigi's katana.",
 "soul_solid": "Brook's cane sword, cold as the underworld.",
 "kikoku": "Law's long nodachi.",
 "gryphon": "Shanks' sabre.",
 "sorcery_clima_tact": "Nami's weather staff. Calls lightning and storms.",
 "buggy_knife": "Buggy's throwing knives. Dropped by Buggy.",
 "skillful_whetstone": "Upgrades a sword to Skillful Grade. Hold the sword in your off hand and right-click.",
 "great_whetstone": "Upgrades a sword to Great Grade. Hold the sword in your off hand and right-click.",
 "supreme_whetstone": "Upgrades a sword to Supreme Grade. Hold the sword in your off hand and right-click.",
 "scope": "Gun upgrade: better aim at range. Hold the gun in your off hand and right-click.",
 "long_barrel": "Gun upgrade: more range. Hold the gun in your off hand and right-click.",
 "hair_trigger": "Gun upgrade: faster shots. Hold the gun in your off hand and right-click.",
 "flame_dial": "Weapon upgrade: hits set targets on fire. Hold the weapon in your off hand and right-click.",
 "impact_dial": "Weapon upgrade: hits knock targets back hard. Hold the weapon in your off hand and right-click.",
 # Story, guides, empire
 "captains_log": "Your story journal. Right-click to see your current chapter and goals.",
 "road_poneglyph_zou": "A rubbing of the Road Poneglyph from Zou. One of four that lead to Laugh Tale.",
 "road_poneglyph_whole_cake": "A rubbing of the Road Poneglyph from Whole Cake Island. One of four that lead to Laugh Tale.",
 "road_poneglyph_wano": "A rubbing of the Road Poneglyph from Wano. One of four that lead to Laugh Tale.",
 "road_poneglyph_hachinosu": "A rubbing of the Road Poneglyph from Hachinosu. One of four that lead to Laugh Tale.",
 "the_one_piece": "The treasure left by Gol D. Roger at Laugh Tale. It's real!",
 "kingdom_flag": "Plant it to claim land as your pirate kingdom.",
 "hideout_flag": "Plant it on an island to claim a pirate hideout. Right-click for its level, crew and stash.",
 "pirates_handbook": "Right-click to read the guide to everything in the mod.",
 "sea_purge": "Removes your Devil Fruit power so you can eat another one.",
 "devil_fruit_encyclopedia": "Right-click to see every Devil Fruit you have found and eaten.",
 # Buildings
 "den_den_relay": "Core of a Den Den Mushi Relay. Build it as the blueprint shows to call across the sea.",
 "den_den_relay_blueprint": "Shows how to build a Den Den Mushi Relay around its core.",
 "shipyard_crane": "Core of a Galley-La Shipyard. Build it as the blueprint shows.",
 "shipyard_crane_blueprint": "Shows how to build a Galley-La Shipyard around its crane.",
 "training_post": "Core of a Haki Dojo. Train here to grow your Haki.",
 "training_post_blueprint": "Shows how to build a Haki Dojo around its training post.",
 "alarm_bell": "Core of a Marine Watchtower. Rings when Marines come near.",
 "alarm_bell_blueprint": "Shows how to build a Marine Watchtower around its bell.",
 "feast_table": "Core of a Baratie Feast Table. Your cook makes meals for the crew here.",
 "feast_table_blueprint": "Shows how to build a Baratie Feast Table.",
 "treasure_vault": "Core of a Treasure Vault. Keeps your Berries safe, even when you die.",
 "treasure_vault_blueprint": "Shows how to build a Treasure Vault around its core.",
 # Deco snacks and specials
 "mikan": "A tangerine from Nami's grove. A sweet snack.",
 "mikan_bush": "Plant it to grow mikan tangerines.",
 "mikan_crate": "A crate of mikan tangerines.",
 "coconut": "A coconut from a palm tree. A small snack.",
 "onigiri": "A rice ball. A simple snack from Wano.",
 "dango": "Sweet dumplings on a stick, loved in Wano.",
 "sake": "Rice wine. Zoro's favourite drink.",
 "sake_barrel": "A barrel of sake.",
 "cola": "Franky's fuel. A fizzy drink.",
 "cola_crate": "A crate of cola bottles.",
 "cotton_candy": "Cotton candy from Whole Cake Island.",
 "bubble_resin": "Resin that blows Sabaody bubbles.",
 "berry_block": "A big stack of Berries. Show off your wealth.",
 "bubble_glass": "Glass that looks like a Sabaody bubble.",
 "bubble_glass_pane": "Thin pane of bubble glass.",
 "bubble_lamp": "A glowing bubble light from Sabaody.",
 "paper_lantern": "A Wano paper lantern. Gives off light.",
 "lab_light": "A bright Punk Hazard lab light.",
 "prison_bars": "Impel Down cell bars.",
 "shoji_screen": "A sliding paper screen from Wano.",
 "tatami": "A Wano straw floor mat.",
 "cloud_puff": "A soft puff of sky island cloud.",
 "candy_cane_block": "A block of candy cane from Whole Cake Island.",
 "candy_cane_sprout": "A small candy cane plant.",
 "chocolate_block": "Solid chocolate from Cacao Island.",
 "alubarna_pillar": "A pillar from Alabasta's royal palace.",
 "marine_pillar": "A pillar from a Marine base.",
 "pearl_block": "A block of shining pearl.",
 "sakura_petals": "Fallen sakura petals to scatter on the ground.",
}

# Where each building block family comes from, for "<Family> building block."
FAMILY = {
 "alabasta_sandstone_brick": "Alabasta sandstone bricks", "alabasta_tile": "Alabasta tiles", "canal_brick": "Water 7 canal bricks",
 "chocolate": "chocolate from Whole Cake Island", "cloud_brick": "sky island cloud bricks", "cookie_brick": "Whole Cake Island cookie bricks",
 "coral_brick": "Fishman Island coral bricks", "dressrosa_mosaic": "Dressrosa mosaic", "dressrosa_stucco": "Dressrosa stucco",
 "dressrosa_tile": "Dressrosa tiles", "frosting": "Whole Cake Island frosting", "frozen_stone": "Punk Hazard frozen stone",
 "lab_panel": "Punk Hazard lab panels", "marine_brick": "Marine base bricks", "marine_tile": "Marine base tiles", "pearl": "pearl",
 "scorched_stone": "Punk Hazard scorched stone", "seastone_brick": "seastone bricks", "shandian_ruin_stone": "Shandora ruin stone",
 "shandora_gold_brick": "Shandora gold bricks", "snow_brick": "Drum Island snow bricks", "wano_lacquer": "Wano lacquered wood",
 "wano_roof_tile": "Wano roof tiles", "wano_lacquer_plank": "Wano lacquered wood", "water7_cobble": "Water 7 cobblestone", "dressrosa_mosaic_": "Dressrosa mosaic",
}
WOOD = {"sakura": "Wano sakura", "yarukiman": "Sabaody yarukiman mangrove", "palm": "island palm", "gloom": "Thriller Bark gloom", "adam": "Adam"}
SHAPES = {"_slab": "Slab of", "_stairs": "Stairs of", "_wall": "Wall of", "s": "Building block:", "": "Building block:"}
WOOD_PARTS = {"log": "Log", "wood": "Bark block", "planks": "Planks", "stairs": "Stairs", "slab": "Slab", "fence": "Fence",
              "fence_gate": "Fence gate", "door": "Door", "trapdoor": "Trapdoor", "button": "Button", "pressure_plate": "Pressure plate",
              "leaves": "Leaves", "sapling": "Sapling. Plant it to grow a tree"}
FLOWERS = {"amazon_flower": "Amazon Lily", "desert_bloom": "Alabasta's deserts", "fire_lily": "volcanic islands", "frost_bloom": "frozen islands",
           "ghost_mushroom": "Thriller Bark", "giant_fern": "Little Garden", "lollipop_flower": "Whole Cake Island", "sky_lotus": "the sky islands",
           "snow_lily": "Drum Island"}

def deco(name):
    if name in HAND:
        return HAND[name]
    if name in FLOWERS:
        return f"A plant found on {FLOWERS[name]}. Decoration."
    stripped = name.startswith("stripped_")
    base = name[9:] if stripped else name
    for wood, label in WOOD.items():
        if base.startswith(wood + "_"):
            part = base[len(wood) + 1:]
            if part in WOOD_PARTS:
                return f"{WOOD_PARTS[part]} of {label} wood." if not stripped else f"Stripped {label} wood."
    for suffix in ("_slab", "_stairs", "_wall"):
        if name.endswith(suffix):
            fam = name[:-len(suffix)]
            label = FAMILY.get(fam) or FAMILY.get(fam.rstrip("s")) or fam.replace("_", " ")
            return f"{SHAPES[suffix]} {label}."
    fam = name[:-1] if name.endswith("s") else name
    fam = fam.removesuffix("_block")
    label = FAMILY.get(fam) or FAMILY.get(name) or name.replace("_", " ")
    return f"Building block: {label}."

# Furniture descriptions are written by tools/furniture/gen_furniture.py.
_FURN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "furniture", "descriptions.json")
FURNITURE = json.load(open(_FURN)) if os.path.exists(_FURN) else {}

def main(source):
    assets = os.path.join(source, "src/main/resources/assets")
    names = {}
    for f in glob.glob(assets + "/*/lang/en_us.json"):
        ns = f.split("/")[-3]
        for k, v in json.load(open(f)).items():
            m = re.match(r"(item|block)\.onepiece\.([a-z0-9_]+)$", k)
            if m:
                names[m.group(2)] = (v, ns)
    out = {}
    for name, (label, ns) in sorted(names.items()):
        if name.endswith("_no_mi") or "_no_mi_" in name:
            continue  # Devil Fruits have their own tooltip
        if name.endswith("_spawn_egg"):
            out["onepiece:" + name] = "Creative only. Spawns a " + label.removesuffix(" Spawn Egg") + "."
        elif ns == "onepiece_furniture" and ("onepiece:" + name) in FURNITURE:
            out["onepiece:" + name] = FURNITURE["onepiece:" + name]
        elif ns == "onepiece_deco":
            out["onepiece:" + name] = deco(name)
        elif name in HAND:
            out["onepiece:" + name] = HAND[name]
    for name, text in HAND.items():
        out.setdefault("onepiece:" + name, text)
    for disc in ("toward_the_grand_line", "fair_winds", "boss_battle", "emperor_battle", "justice_marches"):
        out["onepiece_sounds:music_disc_" + disc] = "A record of One Piece music. Play it in a jukebox."
    path = os.path.join(source, "src/main/resources/onepiece/item_descriptions.json")
    with open(path, "w") as f:
        json.dump(dict(sorted(out.items())), f, indent="\t", ensure_ascii=False)
        f.write("\n")
    print(len(out), "descriptions written to", path)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/mnt/project-files/one-piece-mod/source")
