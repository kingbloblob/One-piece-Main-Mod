package com.onepiecemod.crew;

import net.minecraft.world.entity.LivingEntity;

/**
 * Crewmate levels, 1 to 10. Crewmates earn XP by defeating enemies (more for tougher ones)
 * and a little for every job they finish in Work mode.
 *
 * Each level above 1 gives +8% health, +6% strength and makes jobs 4% quicker,
 * so a level 10 crewmate has 72% more health, 54% more strength and works about a third faster.
 */
public class CrewLevels {
	public static final int MAX_LEVEL = 10;

	/** XP needed to go from this level to the next: 25, 100, 225 ... 2025. About 7,000 XP in total. */
	public static int xpToNext(int level) {
		return 25 * level * level;
	}

	/** XP for defeating an enemy: half its max health, between 2 and 200. Bosses give the most. */
	public static int xpForKill(LivingEntity victim) {
		return (int) Math.max(2, Math.min(200, Math.round(victim.getMaxHealth() / 2.0)));
	}

	public static double healthMultiplier(int level) {
		return 1.0 + 0.08 * (level - 1);
	}

	public static double damageMultiplier(int level) {
		return 1.0 + 0.06 * (level - 1);
	}

	public static double workTimeMultiplier(int level) {
		return 1.0 - 0.04 * (level - 1);
	}
}
