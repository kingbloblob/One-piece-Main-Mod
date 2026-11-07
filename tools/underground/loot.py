"""Chest loot for the underground structures (26.3 format: "modifier" + "type", "condition")."""
import json, os


def item(name, weight, lo=1, hi=1, extra=None):
    e = {"type": "minecraft:item", "name": name, "weight": weight}
    mods = []
    if (lo, hi) != (1, 1): mods.append({"type": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": lo, "max": hi}})
    if extra: mods += extra
    if mods: e["modifier"] = mods
    return e


def treasure_map(dest, name):
    """A map that marks the nearest structure of tag `dest` with a red X (like vanilla buried treasure maps)."""
    return {"type": "minecraft:item", "name": "minecraft:map", "weight": 1, "modifier": [
        {"type": "minecraft:exploration_map", "decoration": "minecraft:red_x", "destination": f"#onepiece:{dest}",
         "skip_existing_chunks": False, "zoom": 1},
        {"type": "minecraft:set_name", "name": name, "target": "item_name"},
        {"type": "minecraft:filtered", "item_filter": {"predicates": {"minecraft:map_id": {}}}, "on_fail": {"type": "minecraft:discard"}}]}


def table(name, *pools):
    return {"type": "minecraft:chest", "pools": list(pools), "random_sequence": f"onepiece:chests/{name}"}


def pool(lo, hi, *entries, chance=None):
    p = {"rolls": {"type": "minecraft:uniform", "min": lo, "max": hi} if (lo, hi) != (1, 1) else 1, "entries": list(entries)}
    if chance: p["condition"] = {"type": "minecraft:random_chance", "chance": chance}
    return p


ENCH = [{"type": "minecraft:enchant_randomly"}]

TABLES = {
    # the pirate hoard: gold, coins, gems and the captain's prizes
    "underground_treasure": table("underground_treasure",
        pool(5, 9, item("minecraft:gold_ingot", 12, 3, 9), item("minecraft:gold_nugget", 10, 8, 24), item("onepiece:berry", 12, 10, 40),
             item("minecraft:emerald", 7, 2, 6), item("minecraft:diamond", 4, 1, 3), item("onepiece:sea_pearl", 5, 1, 3),
             item("minecraft:golden_apple", 3), item("onepiece:shandora_gold_ingot", 4, 1, 3), item("minecraft:gold_block", 2, 1, 2),
             item("minecraft:golden_sword", 2, extra=ENCH), item("minecraft:golden_helmet", 2, extra=ENCH), item("onepiece:sea_chart", 3)),
        pool(1, 1, item("minecraft:enchanted_book", 3, extra=ENCH), item("minecraft:enchanted_golden_apple", 1),
             item("minecraft:diamond_sword", 1, extra=ENCH), item("minecraft:heart_of_the_sea", 1), chance=0.45),
        pool(1, 1, treasure_map("on_marine_bunker_maps", "Stolen Marine Orders"), chance=0.3),
        pool(1, 1, treasure_map("dungeons", "Map to a Forgotten Dungeon"), chance=0.35)),
    # the Void Century ruins: relics, ancient gold and a map deeper in
    "underground_ruins": table("underground_ruins",
        pool(4, 7, item("onepiece:shandora_gold_ingot", 8, 1, 4), item("onepiece:raw_shandora_gold", 8, 2, 6), item("minecraft:paper", 6, 2, 6),
             item("onepiece:kraken_ink", 3), item("minecraft:echo_shard", 3, 1, 2), item("minecraft:amethyst_shard", 6, 2, 8),
             item("onepiece:ancient_glyph_stone", 5, 2, 6), item("minecraft:diamond", 3, 1, 2), item("onepiece:berry", 6, 8, 24),
             item("minecraft:book", 4, 1, 3)),
        pool(1, 1, treasure_map("on_treasure_grotto_maps", "Faded Pirate Map"), chance=0.35),
        pool(1, 1, item("minecraft:enchanted_book", 1, extra=ENCH), chance=0.5)),
    # the secret Marine bunker: weapons, rations, seastone and seized intelligence
    "marine_bunker": table("marine_bunker",
        pool(4, 7, item("onepiece:berry", 10, 5, 20), item("minecraft:iron_ingot", 8, 2, 6), item("minecraft:bread", 7, 2, 5),
             item("minecraft:cooked_beef", 5, 1, 4), item("minecraft:arrow", 5, 4, 12), item("onepiece:raw_seastone", 5, 1, 3),
             item("onepiece:seastone_ingot", 2), item("onepiece:seastone_cuffs", 2), item("minecraft:crossbow", 2, extra=ENCH),
             item("minecraft:iron_sword", 2, extra=ENCH), item("minecraft:gunpowder", 5, 2, 6), item("onepiece:sea_chart", 3),
             item("minecraft:paper", 5, 2, 8)),
        pool(1, 1, treasure_map("on_smile_factory_maps", "Seized Smuggling Chart"), chance=0.3),
        pool(1, 1, treasure_map("on_deep_mine_maps", "Impel Down Quarry Survey"), chance=0.3)),
    # the SMILE factory: Donquixote smuggling goods, sulfur and chemicals, and a fortune in Berries
    "smile_factory": table("smile_factory",
        pool(4, 8, item("onepiece:berry", 12, 15, 50), item("onepiece:sulfur", 8, 3, 10), item("minecraft:gunpowder", 7, 3, 8),
             item("minecraft:glass_bottle", 5, 2, 5), item("minecraft:redstone", 6, 4, 12), item("minecraft:iron_ingot", 6, 2, 6),
             item("minecraft:emerald", 5, 2, 5), item("minecraft:experience_bottle", 4, 1, 4), item("minecraft:glowstone_dust", 4, 2, 8),
             item("onepiece:kokuto_ingot", 1), item("minecraft:diamond", 2, 1, 2), item("minecraft:golden_carrot", 3, 2, 6)),
        pool(1, 1, treasure_map("on_ancient_ruins_maps", "Underground Trade Route"), chance=0.25)),
    # the Seastone Deep Mine's supply chests: fuel, picks, drill bits, raw seastone and the jailers' rations
    "deep_mine": table("deep_mine",
        pool(4, 7, item("minecraft:coal", 10, 4, 12), item("onepiece:sulfur", 7, 2, 8), item("onepiece:raw_seastone", 8, 1, 4),
             item("onepiece:seastone_ingot", 3, 1, 2), item("minecraft:iron_ingot", 6, 2, 5), item("minecraft:rail", 6, 4, 12),
             item("minecraft:torch", 6, 6, 16), item("minecraft:bread", 6, 2, 5), item("onepiece:rock_candy", 3, 1, 3),
             item("onepiece:gloom_crystal", 3, 1, 2), item("onepiece:adam_drill_bit", 2), item("onepiece:seastone_cuffs", 2),
             item("onepiece:sea_prism_shard", 2, 1, 2), item("minecraft:iron_pickaxe", 2, extra=ENCH)),
        pool(1, 1, treasure_map("on_deep_mine_maps", "Survey of the Lower Quarries"), chance=0.15)),
    # the sealed Abyss vault: what the World Government kept from the deepest seam
    "deep_mine_vault": table("deep_mine_vault",
        pool(4, 7, item("onepiece:sea_prism_shard", 10, 2, 5), item("onepiece:sea_prism_ingot", 3, 1, 2),
             item("onepiece:seastone_ingot", 6, 2, 5), item("onepiece:kokuto_ingot", 3, 1, 2), item("minecraft:diamond", 5, 1, 4),
             item("onepiece:egghead_alloy", 3, 1, 3), item("onepiece:electro_crystal", 4, 2, 5), item("onepiece:berry", 8, 20, 60),
             item("minecraft:enchanted_book", 3, extra=ENCH), item("onepiece:seastone_drill_bit", 2),
             item("minecraft:netherite_scrap", 1, 1, 2)),
        pool(1, 1, item("onepiece:sea_prism_drill_bit", 1), chance=0.1)),
}


def write(res):
    for name, t in TABLES.items():
        p = os.path.join(res, 'loot_table/chests', name + '.json')
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w') as f:
            json.dump(t, f, indent=2)
            f.write('\n')
