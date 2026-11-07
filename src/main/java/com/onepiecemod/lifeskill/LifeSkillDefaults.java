package com.onepiecemod.lifeskill;

import net.minecraft.world.level.block.Blocks;

/**
 * Starting XP values for vanilla blocks that aren't found by the general rules in LifeSkillHooks
 * (crops with an age, ores ending in "_ore"). Other features add their own with LifeSkills.registerBlock/registerCraft.
 */
final class LifeSkillDefaults {
	private LifeSkillDefaults() {
	}

	static void register() {
		LifeSkills.registerBlock(Blocks.ANCIENT_DEBRIS, LifeSkill.MINING, 20);
		LifeSkills.registerBlock(Blocks.AMETHYST_CLUSTER, LifeSkill.MINING, 3);
		LifeSkills.registerBlock(Blocks.MELON, LifeSkill.FARMING, 2);
		// Pumpkins and sugar cane are left out on purpose: you could place them and break them again forever.
	}

	/**
	 * XP for an ore, from its id. Works for ores other features add later, as long as the id says what it is.
	 * Order matters: "nether_gold" is checked before "gold", "deepslate_x" just contains "x".
	 */
	static int oreXp(String path) {
		if (path.contains("emerald") || path.contains("kokuto")) return 15;
		if (path.contains("diamond")) return 12;
		if (path.contains("seastone")) return 10;
		if (path.contains("shandora_gold")) return 8;
		if (path.contains("nether_gold")) return 3;
		if (path.contains("gold") || path.contains("tamahagane") || path.contains("wapometal")) return 6;
		if (path.contains("lapis")) return 5;
		if (path.contains("redstone") || path.contains("iron")) return 4;
		if (path.contains("copper") || path.contains("quartz") || path.contains("sulfur")) return 3;
		if (path.contains("coal")) return 2;
		return LifeSkills.DEFAULT_ORE_XP;
	}
}
