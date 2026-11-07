package com.onepiecemod.lifeskill;

import java.util.HashMap;
import java.util.Map;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

/**
 * A player's life skill XP, saved on the player. Levels are worked out from the XP, so they never get out of step.
 *
 * @param xp total XP ever earned in each skill, by skill id (missing means 0)
 */
public record LifeSkillData(Map<String, Integer> xp) {
	public static final LifeSkillData EMPTY = new LifeSkillData(Map.of());

	public static final Codec<LifeSkillData> CODEC = RecordCodecBuilder.create(instance -> instance.group(
			Codec.unboundedMap(Codec.STRING, Codec.INT).optionalFieldOf("xp", Map.of()).forGetter(LifeSkillData::xp)
	).apply(instance, LifeSkillData::new));

	/**
	 * XP from this level to the next. Level 1 -> 2 takes 40 XP (a field of wheat),
	 * 49 -> 50 takes 520. Reaching 50 takes 13,720 XP: a long-term goal, a bit at a time.
	 */
	public static int xpForNextLevel(int level) {
		return 30 + 10 * level;
	}

	/** Total XP to reach this level. Everyone starts at level 1. */
	public static int totalXpForLevel(int level) {
		int total = 0;
		for (int l = 1; l < level; l++) {
			total += xpForNextLevel(l);
		}
		return total;
	}

	public int xp(LifeSkill skill) {
		return xp.getOrDefault(skill.id, 0);
	}

	public int level(LifeSkill skill) {
		int points = xp(skill);
		int level = 1;
		while (level < LifeSkill.MAX_LEVEL && points >= totalXpForLevel(level + 1)) {
			level++;
		}
		return level;
	}

	/** XP earned since the current level started. */
	public int xpIntoLevel(LifeSkill skill) {
		return xp(skill) - totalXpForLevel(level(skill));
	}

	public LifeSkillData withXp(LifeSkill skill, int amount) {
		Map<String, Integer> copy = new HashMap<>(xp);
		copy.put(skill.id, Math.max(0, amount));
		return new LifeSkillData(Map.copyOf(copy));
	}
}
