package com.onepiecemod.stats;

import java.util.HashMap;
import java.util.Map;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

/**
 * A player's Pirate Level and stat tree, saved on the player.
 *
 * Only the total training XP and the ranks bought are saved. The level and the
 * free points are worked out from those, so they can never get out of step.
 *
 * @param xp    all training XP ever earned
 * @param ranks ranks bought in each stat, by stat id (missing means 0)
 */
public record StatsData(int xp, Map<String, Integer> ranks) {
	public static final StatsData EMPTY = new StatsData(0, Map.of());

	public static final Codec<StatsData> CODEC = RecordCodecBuilder.create(instance -> instance.group(
			Codec.INT.optionalFieldOf("xp", 0).forGetter(StatsData::xp),
			Codec.unboundedMap(Codec.STRING, Codec.INT).optionalFieldOf("ranks", Map.of()).forGetter(StatsData::ranks)
	).apply(instance, StatsData::new));

	/** The highest Pirate Level. 60 points can't fill all 100 ranks, so every player picks a build. */
	public static final int MAX_LEVEL = 60;

	/**
	 * XP needed to go from this level to the next. Level 1 takes 50 XP (a few zombies),
	 * level 59 takes over 1,500 (about an hour of adventuring). Reaching 60 takes 47,250 XP in total.
	 */
	public static int xpForNextLevel(int level) {
		return 50 + 25 * level;
	}

	/** Total XP needed to reach this level from zero. */
	public static int totalXpForLevel(int level) {
		return 50 * level + 25 * level * (level - 1) / 2;
	}

	public int level() {
		int level = 0;
		while (level < MAX_LEVEL && xp >= totalXpForLevel(level + 1)) {
			level++;
		}
		return level;
	}

	/** XP earned since the current level started. */
	public int xpIntoLevel() {
		return xp - totalXpForLevel(level());
	}

	public int rank(PlayerStat stat) {
		return ranks.getOrDefault(stat.id, 0);
	}

	public int spentPoints() {
		int spent = 0;
		for (PlayerStat stat : PlayerStat.values()) {
			spent += rank(stat);
		}
		return spent;
	}

	/** Stat points the player can still spend. */
	public int freePoints() {
		return Math.max(0, level() - spentPoints());
	}

	public boolean canRaise(PlayerStat stat) {
		return freePoints() > 0 && rank(stat) < PlayerStat.MAX_RANK;
	}

	public StatsData withXp(int newXp) {
		return new StatsData(Math.max(0, newXp), ranks);
	}

	public StatsData withRank(PlayerStat stat, int rank) {
		Map<String, Integer> copy = new HashMap<>(ranks);
		copy.put(stat.id, rank);
		return new StatsData(xp, Map.copyOf(copy));
	}

	/** Same XP, but every point handed back (a respec). */
	public StatsData withoutRanks() {
		return new StatsData(xp, Map.of());
	}
}
