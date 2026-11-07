"""Guards that structures spawn. Written to src/main/resources/onepiece/guards.json for GuardKit.java."""
def k(entity, name, main=None, head=None, chest=None, legs=None, feet=None, health=0, damage=0, off=None):
    return {"entity": f"minecraft:{entity}", "name": name, "mainhand": main and f"minecraft:{main}", "offhand": off and f"minecraft:{off}",
            "head": head and f"minecraft:{head}", "chest": chest and f"minecraft:{chest}", "legs": legs and f"minecraft:{legs}",
            "feet": feet and f"minecraft:{feet}", "health": health, "damage": damage}
KITS = {
    # ---- easy (zombies and skeletons wear helmets so they don't burn in the sun)
    "bandit":         k("zombie", "Mountain Bandit", "wooden_axe", "leather_helmet"),
    "rookie_pirate":  k("zombie", "Rookie Pirate", "wooden_sword", "leather_helmet"),
    "marine_recruit": k("skeleton", "Marine Recruit", "bow", "leather_helmet"),
    "buggy_pirate":   k("zombie", "Buggy Pirate", "stone_sword", "leather_helmet"),
    "kuja_warrior":   k("skeleton", "Kuja Warrior", "bow", "golden_helmet"),
    # ---- medium
    "marine":         k("vindicator", "Marine Soldier", "iron_sword", "chainmail_helmet"),
    "marine_rifle":   k("pillager", "Marine Rifleman", "crossbow", "chainmail_helmet"),
    "pirate":         k("vindicator", "Pirate", "iron_axe"),
    "pirate_gunner":  k("pillager", "Pirate Gunner", "crossbow"),
    "fishman":        k("drowned", "Fish-Man", "trident", health=30),
    "zombie_soldier": k("zombie", "Zombie Soldier", "iron_sword", "iron_helmet", health=30),
    "baroque_agent":  k("husk", "Baroque Works Agent", "iron_sword", "golden_helmet"),
    "bounty_hunter":  k("vindicator", "Bounty Hunter", "iron_sword"),
    "homie":          k("zombie", "Homie", "stone_sword", "carved_pumpkin", health=26),
    "samurai":        k("vindicator", "Samurai", "iron_sword", "iron_helmet"),
    "frost_soldier":  k("stray", "Frost Soldier", "bow", "iron_helmet"),
    # ---- hard
    "elite_marine":   k("vindicator", "Marine Captain", "diamond_sword", "iron_helmet", "iron_chestplate", health=40),
    "cp_agent":       k("vindicator", "CP Agent", "iron_sword", "leather_helmet", health=36, damage=8),
    "gifter":         k("vindicator", "Gifter", "diamond_axe", "iron_helmet", "chainmail_chestplate", health=40),
    "headliner":      k("vindicator", "Headliner", "netherite_axe", "diamond_helmet", "diamond_chestplate", health=60),
    "jailer":         k("wither_skeleton", "Impel Down Jailer", "stone_sword", health=40),
    "humandrill":     k("vindicator", "Humandrill", "iron_sword", health=40),
    "gladiator":      k("vindicator", "Gladiator", "iron_sword", "golden_helmet", "golden_chestplate", health=40, off="shield"),
    "donquixote":     k("pillager", "Donquixote Pirate", "crossbow", "iron_helmet", health=30),
    "whitebeard_pirate": k("vindicator", "Whitebeard Pirate", "diamond_sword", "iron_helmet", "iron_chestplate", health=50),
    "blackbeard_pirate": k("vindicator", "Blackbeard Pirate", "netherite_sword", "iron_helmet", "diamond_chestplate", health=50),
    "flame_guard":    k("blaze", "Flame Guard", health=40),
    "sky_priest":     k("blaze", "Sky Priest", health=30),
    "war_beast":      k("ravager", "War Beast", health=120),
    # ---- legendary
    "vice_admiral":   k("vindicator", "Vice Admiral", "netherite_sword", "diamond_helmet", "diamond_chestplate", "diamond_leggings", "diamond_boots", health=80, damage=12),
    "pacifista":      k("vindicator", "Pacifista", "netherite_axe", "netherite_helmet", "netherite_chestplate", health=120, damage=14),
    "seraphim":       k("blaze", "Seraphim", health=100),
    "cp0_agent":      k("vindicator", "CP0 Agent", "netherite_sword", "iron_helmet", "netherite_chestplate", health=70, damage=12),
    "warden_jailer":  k("wither_skeleton", "Jailer Beast", "netherite_sword", "netherite_helmet", health=90),
    "ancient_guardian": k("wither_skeleton", "Ancient Guardian", "netherite_sword", "netherite_helmet", "netherite_chestplate", health=120),
}

# Pirates and Marines are the mod's own NPCs (com.onepiecemod.npc), never vanilla mobs. Their looks, crews, ranks
# and weapons come from src/main/resources/onepiece/npc_kits.json (same ids); the gear above is only a fallback.
NPC_MARINES = ["marine_recruit", "marine", "marine_rifle", "elite_marine", "vice_admiral", "cp_agent", "cp0_agent",
               "pacifista", "seraphim", "jailer"]
NPC_PIRATES = ["bandit", "rookie_pirate", "buggy_pirate", "pirate", "pirate_gunner", "fishman", "baroque_agent",
               "bounty_hunter", "gifter", "headliner", "donquixote", "whitebeard_pirate", "blackbeard_pirate"]
for _id in NPC_MARINES:
    KITS[_id]["entity"] = "onepiece:marine"
for _id in NPC_PIRATES:
    KITS[_id]["entity"] = "onepiece:sea_pirate"
