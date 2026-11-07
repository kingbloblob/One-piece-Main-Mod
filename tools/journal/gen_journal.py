#!/usr/bin/env python3
"""Writes src/main/resources/onepiece/journal.json: the tabs of the Crafter's Journal and which items
go in each tab, plus the structure list (read from /mnt/project-files/one-piece-mod/structures.md).
Fruits, creatures, bosses and characters are filled in by the game itself from their own data.
Run after adding items or structures:
    python3 gen_journal.py /mnt/project-files/one-piece-mod/source"""
import json, sys, os, glob, re

ROOT = "/mnt/project-files/one-piece-mod"

# id, title, icon, colour, guide.json chapters shown as the tab's intro, dynamic entries, extra intro lines
TABS = [
 ("start", "Getting Started", "onepiece:pirates_handbook", "FFD75E", ["welcome", "keys", "recipes"], None, []),
 ("crafting", "Crafting & Cooking", "onepiece:shipwright_bench", "C8A26B", ["stations"], "stations", []),
 ("fishing", "Fishing & Cooking", "onepiece:all_blue_kingfish", "4FB8E8", [], None,
  ["# Fishing & Cooking", "Every sea has its own fish. Cast a normal fishing rod and see what bites.", "",
   "- East Blue, Calm Belt, Grand Line and New World each have their own fish. Islands like Wano, Skypiea and Alabasta have more.",
   "- In the Calm Belt you can hook Sea King Fry and slabs of Sea King meat.",
   "- Sanji's dishes are made at the Ship's Galley. Their buffs last 8 to 20 minutes, and half as long again with a Cook in your crew.",
   "- Far out in the New World lies the All Blue, where the fish of every sea meet. The All Blue Compass points the way.",
   "> Type /fishlog to see which fish you have caught."]),
 ("fruits", "Devil Fruits", "onepiece:gomu_gomu_no_mi", "C060FF", ["fruits"], "fruits",
  ["> The Devil Fruit Encyclopedia keeps track of which fruits you have found and eaten."]),
 ("weapons", "Weapons", "onepiece:flintlock_pistol", "E05050", ["weapons"], None, []),
 ("creatures", "Creatures", "minecraft:turtle_egg", "60C060", ["creatures"], "creatures", []),
 ("bosses", "Bosses", "onepiece:wanted_poster_kaido", "FF5555", [], "bosses",
  ["# Bosses", "Bosses guard the strongest treasures of the seas. Each one lives in a lair you can find with a Sea Chart.",
   "", "- Beat a boss and their Wanted Poster lets you fight them again on Hard, then Expert.",
   "- Sengoku sells the posters of the bosses you can rematch.", "- Hard and Expert bosses drop better rewards.",
   "> Each entry lists the boss's attacks, health and drops."]),
 ("characters", "Characters & Traders", "onepiece:berry", "FFAA00", ["characters"], "characters", []),
 ("structures", "Structures", "minecraft:filled_map", "5FA8FF", ["world"], "structures", []),
 ("ships", "Ships & the Sea", "onepiece:ships_wheel", "3FA0D0", ["ships", "seas"], None, []),
 ("haki", "Haki, Styles & Races", "onepiece:wado_ichimonji", "B0B0FF", ["haki", "styles", "races"], None, []),
 ("crew", "Crew & Buildings", "onepiece:recruitment_board", "D09060", ["crew"], None,
  ["# Buildings", "Some blocks are the core of a bigger building. Hold its blueprint to see where every block goes; when the building is complete, the core comes alive."]),
 ("story", "Story, Bounty & Empire", "onepiece:captains_log", "FFC23C", ["story", "bounty", "empire"], None, []),
 ("resources", "Ores & Resources", "onepiece:seastone_ingot", "80D0D0", ["resources"], None, []),
 ("blocks", "Blocks & Plants", "onepiece:sakura_planks", "FF9FCF", [], None,
  ["# Blocks & Plants", "Building blocks from every island of the Grand Line: Wano roofs, Water 7 cobbles, Whole Cake cookies and more.",
   "", "- Four new woods: sakura, yarukiman, palm and gloom.", "- Flowers and plants grow on the islands they come from.",
   "> Building blocks are cheap: most take only stone, sand or wood plus a dye."]),
 ("furniture", "Furniture & Props", "onepiece:oak_chair", "B07A4A", [], None,
  ["# Furniture & Props", "Tables, chairs, shelves, rugs, curtains, crates and props for taverns, kitchens, ships, libraries and palaces.",
   "", "- Chairs, stools, benches, armchairs and cushions: right-click with an empty hand to sit down.",
   "- Shelves, nets, life rings, tool and weapon racks hang on a wall. Ropes hang from a ceiling.",
   "- Rope ladders and hanging ropes can be climbed.", "> Every piece is made at a crafting table. Wood pieces come in oak, spruce, birch, dark oak, sakura and palm."]),
 ("all", "All Items", "minecraft:chest", "E0E0E0", [], "all",
  ["# All Items", "Every item in the mod, A to Z. Use the search box to find one fast."]),
]

SHIPS = ["ships_wheel", "jolly_roger", "figurehead_merry", "figurehead_sunny", "figurehead_moby", "cannon", "cannonball", "anchor",
         "porthole", "rope_coil", "bubble_coating", "log_pose", "eternal_pose", "sea_chart", "den_den_mushi", "sea_king_bait",
         "sea_king_meat", "cooked_sea_king_meat", "sea_king_scale"]
HAKI = ["training_post", "training_post_blueprint"] + ["dojo_scroll_" + s for s in ("santoryu", "black_leg", "fishman_karate", "rokushiki", "ryusoken", "nitoryu", "kitsunebi", "soul_fencing", "fist_of_love", "sogeking")] + [ "wado_ichimonji", "sandai_kitetsu", "shusui", "enma", "yoru"]
CREW = ["recruitment_board", "tavern_blueprint", "den_den_mushi", "den_den_relay", "den_den_relay_blueprint", "shipyard_crane",
        "shipyard_crane_blueprint", "training_post", "training_post_blueprint", "alarm_bell", "alarm_bell_blueprint", "feast_table",
        "feast_table_blueprint", "treasure_vault", "treasure_vault_blueprint"]
STORY = ["captains_log", "pirates_handbook", "devil_fruit_encyclopedia", "bounty_poster", "berry", "poneglyph", "kraken_ink",
         "road_poneglyph_zou", "road_poneglyph_whole_cake", "road_poneglyph_wano", "road_poneglyph_hachinosu", "the_one_piece",
         "kingdom_flag", "seastone_cuffs", "sea_purge"]
START = ["pirates_handbook", "captains_log", "berry", "log_pose", "sea_chart", "shipwright_bench", "ships_wheel"]
CRAFT = ["shipwright_bench", "ships_galley", "navigators_desk", "seastone_workbench", "swordsmith_forge", "pirate_bento",
         "sea_king_stew", "rumble_ball", "mikan", "coconut", "onigiri", "dango", "sake", "cola", "cotton_candy", "cooked_sea_king_meat"]
RES_EXTRA = ["seastone_ore", "deepslate_seastone_ore", "raw_seastone", "seastone_ingot", "seastone_block", "adam_log", "adam_planks",
             "island_cloud", "sea_king_scale", "sea_pearl"]
WEAPON_EXTRA = ["wado_ichimonji", "sandai_kitetsu", "shusui", "enma", "yoru", "seastone_jitte", "seastone_cuffs"]


def lang_items(source):
    items = {}
    for f in glob.glob(source + "/src/main/resources/assets/*/lang/en_us.json"):
        ns = f.split("/")[-3]
        for k, v in json.load(open(f)).items():
            m = re.match(r"(item|block)\.onepiece\.([a-z0-9_]+)$", k)
            if m:
                items.setdefault(m.group(2), (v, ns))
    return items


def structures():
    out, tier = [], ""
    for line in open(ROOT + "/structures.md"):
        m = re.match(r"## (\w+)", line)
        if m:
            tier = m.group(1)
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 5 and cells[1].startswith("`"):
            name = re.sub(r"\*\*\(([^)]*)\)\*\*", "", cells[0]).strip()
            out.append({"id": cells[1].strip("`"), "name": name, "tier": tier, "lair": "boss lair" in cells[0],
                        "who": cells[2], "guards": cells[3], "where": cells[4]})
    return out


def main(source):
    items = lang_items(source)
    by_ns = lambda ns: sorted(k for k, (v, n) in items.items() if n == ns)
    lists = {
        "start": START, "crafting": CRAFT, "fishing": by_ns("onepiece_cuisine") + ["sea_king_meat", "cooked_sea_king_meat"], "weapons": by_ns("onepiece_weapons") + WEAPON_EXTRA, "ships": SHIPS, "haki": HAKI,
        "crew": CREW, "story": STORY, "resources": RES_EXTRA + by_ns("onepiece_resources") + by_ns("onepiece_world"),
        "blocks": by_ns("onepiece_deco") + by_ns("onepiece_building") + by_ns("onepiece_baseworks"),
        "furniture": by_ns("onepiece_furniture"),
    }
    tabs = []
    for tid, title, icon, color, chapters, dynamic, intro in TABS:
        seen, ids = set(), []
        for name in lists.get(tid, []):
            if name not in seen:
                seen.add(name)
                ids.append("onepiece:" + name)
        tabs.append({"id": tid, "title": title, "icon": icon, "color": color, "chapters": chapters, "intro": intro,
                     "dynamic": dynamic, "items": ids})
    data = {"_help": "Generated by tools/journal/gen_journal.py. Edit that script, not this file.",
            "tabs": tabs, "structures": structures()}
    path = source + "/src/main/resources/onepiece/journal.json"
    with open(path, "w") as f:
        json.dump(data, f, indent="\t", ensure_ascii=False)
        f.write("\n")
    print(len(tabs), "tabs,", len(data["structures"]), "structures ->", path)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ROOT + "/source")
