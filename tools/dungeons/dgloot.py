"""Chest loot for the dungeons (26.3 format: "modifier" + "type", "condition").

Every dungeon has three kinds of chest:
  dungeon_common            barracks and side-vault supplies (shared by all dungeons)
  dungeon_vault_<sid>       the side vault behind the trap corridor: the dungeon's own treasure
  dungeon_sanctum_<sid>     the sanctum behind the boss's throne: the best loot and a map to the next dungeon
The legendary blades themselves never come from chests: the mini-boss drops them (onepiece/dungeon_bosses.json).
"""
import json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "underground"))
from loot import item, treasure_map, table, pool, ENCH  # noqa: E402

# the order a player is meant to find them in (Paradise first); each sanctum maps the next one
ORDER = ["sand_king_tomb", "ryuma_crypt", "kitetsu_forge", "oden_shrine", "roger_vault"]
MAP_NAMES = {"sand_king_tomb": "Map to the Sand King's Tomb", "ryuma_crypt": "Map to Ryuma's Crypt",
             "kitetsu_forge": "Map to the Cursed Forge", "oden_shrine": "Map to Oden's Hidden Shrine",
             "roger_vault": "Map to Roger's Hidden Vault"}

VAULT = {
    "sand_king_tomb": [item("onepiece:shandora_gold_ingot", 8, 1, 4), item("minecraft:gold_ingot", 10, 3, 8), item("minecraft:sand", 2, 4, 8),
                       item("minecraft:emerald", 6, 2, 5), item("onepiece:berry", 10, 20, 50), item("minecraft:golden_apple", 2),
                       item("onepiece:sea_pearl", 4, 1, 3), item("minecraft:diamond", 3, 1, 2)],
    "ryuma_crypt": [item("minecraft:bone", 8, 3, 8), item("minecraft:gold_ingot", 8, 2, 6), item("onepiece:berry", 10, 25, 60),
                    item("minecraft:diamond", 4, 1, 3), item("minecraft:echo_shard", 3, 1, 2), item("onepiece:dojo_scroll_santoryu", 2),
                    item("minecraft:iron_sword", 3, extra=ENCH), item("minecraft:experience_bottle", 4, 2, 5)],
    "kitetsu_forge": [item("onepiece:raw_kokuto", 8, 1, 3), item("onepiece:kokuto_ingot", 4, 1, 2), item("minecraft:iron_ingot", 10, 4, 10),
                      item("minecraft:netherite_scrap", 2), item("onepiece:berry", 10, 30, 70), item("minecraft:diamond", 4, 1, 3),
                      item("minecraft:diamond_sword", 2, extra=ENCH), item("minecraft:coal_block", 4, 1, 3)],
    "oden_shrine": [item("onepiece:golden_koi", 3), item("onepiece:berry", 10, 30, 80), item("minecraft:gold_ingot", 8, 3, 8),
                    item("minecraft:diamond", 5, 1, 3), item("onepiece:dojo_scroll_nitoryu", 2), item("onepiece:kokuto_ingot", 3, 1, 2),
                    item("minecraft:cherry_sapling", 3, 1, 3), item("minecraft:enchanted_golden_apple", 1)],
    "roger_vault": [item("onepiece:berry", 12, 50, 120), item("minecraft:gold_block", 6, 1, 3), item("minecraft:diamond", 6, 2, 4),
                    item("onepiece:shandora_gold_ingot", 6, 2, 5), item("minecraft:netherite_scrap", 3, 1, 2), item("onepiece:kokuto_ingot", 4, 1, 3),
                    item("minecraft:enchanted_golden_apple", 2), item("onepiece:grand_line_wall_map", 2)],
}


def tables():
    t = {"dungeon_common": table("dungeon_common",
        pool(4, 7, item("onepiece:berry", 12, 5, 20), item("minecraft:bread", 8, 2, 5), item("minecraft:cooked_beef", 6, 1, 4),
             item("minecraft:iron_ingot", 8, 2, 6), item("minecraft:gold_nugget", 8, 6, 18), item("minecraft:arrow", 6, 4, 12),
             item("minecraft:gunpowder", 5, 2, 6), item("minecraft:torch", 5, 4, 10), item("minecraft:string", 5, 2, 6), item("onepiece:sea_chart", 2), item("minecraft:shield", 2, extra=ENCH)),
        pool(1, 1, item("minecraft:enchanted_book", 1, extra=ENCH), chance=0.35))}
    for i, sid in enumerate(ORDER):
        t["dungeon_vault_" + sid] = table("dungeon_vault_" + sid, pool(4, 7, *VAULT[sid]),
                                          pool(1, 1, item("minecraft:enchanted_book", 1, extra=ENCH), chance=0.6))
        nxt = ORDER[(i + 1) % len(ORDER)]
        t["dungeon_sanctum_" + sid] = table("dungeon_sanctum_" + sid,
            pool(5, 8, *VAULT[sid], item("minecraft:diamond", 6, 2, 4), item("minecraft:experience_bottle", 6, 3, 8)),
            pool(1, 2, item("minecraft:enchanted_book", 3, extra=ENCH), item("minecraft:diamond_sword", 1, extra=ENCH),
                 item("minecraft:golden_apple", 3, 1, 2), item("minecraft:totem_of_undying", 1)),
            pool(1, 1, treasure_map("on_" + nxt + "_maps", MAP_NAMES[nxt])))
    return t


def write(res):
    for name, t in tables().items():
        p = os.path.join(res, "loot_table/chests", name + ".json")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            json.dump(t, f, indent=2)
            f.write("\n")
