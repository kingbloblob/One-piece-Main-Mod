package com.onepiecemod.stats;

/**
 * The five branches of the stat tree. Each one has 20 ranks, and every rank costs 1 stat point.
 * Ranks 10 and 20 also unlock a bonus perk (a "milestone").
 *
 * The text here is what the stat tree screen and /stats show, so keep it in step with StatBonuses.
 */
public enum PlayerStat {
	STRENGTH("strength", "Strength", 0xE74C3C,
			"Hit harder with everything: fists, swords and guns alike.",
			"+0.25 attack damage per rank",
			"Heavy Blows: your hits knock enemies further",
			"Herculean: break blocks 25% faster"),

	TOUGHNESS("toughness", "Toughness", 0xB0793B,
			"Take a beating and keep standing, like Luffy after Enies Lobby.",
			"+1/4 heart and +0.1 armor per rank",
			"Rooted: 25% harder to knock back",
			"Iron Body: +3 armor toughness"),

	SPEED("speed", "Speed", 0x4FC3F7,
			"Run and swim faster, the first step towards Soru.",
			"+0.75% run speed and faster swimming per rank",
			"Light Feet: step up full blocks",
			"Soru Step: jump higher and fall 3 blocks further safely"),

	STAMINA("stamina", "Stamina", 0x7BC67E,
			"Keep fighting for longer: heal over time and hold your breath.",
			"Slowly heal when fed, and hold your breath longer, per rank",
			"Iron Stomach: get hungry 25% slower",
			"Second Wind: when nearly dead, heal up (once every 5 minutes)"),

	SWORDSMANSHIP("swordsmanship", "Swordsmanship", 0xC0C8D8,
			"The way of the sword. Only works while you hold a sword.",
			"+0.3 sword damage and +1.5% swing speed per rank",
			"Wide Cuts: sweeping attacks hit 30% harder",
			"Long Reach: +1 block sword reach");

	/** Highest rank of every branch. */
	public static final int MAX_RANK = 20;
	/** Ranks where a milestone perk unlocks. */
	public static final int FIRST_MILESTONE = 10;
	public static final int SECOND_MILESTONE = 20;

	public final String id;
	public final String displayName;
	public final int color;
	public final String description;
	public final String perRank;
	public final String firstMilestone;
	public final String secondMilestone;

	PlayerStat(String id, String displayName, int color, String description, String perRank,
			String firstMilestone, String secondMilestone) {
		this.id = id;
		this.displayName = displayName;
		this.color = color;
		this.description = description;
		this.perRank = perRank;
		this.firstMilestone = firstMilestone;
		this.secondMilestone = secondMilestone;
	}

	/** Finds a stat by its id, like "strength". Returns null if there is none. */
	public static PlayerStat byId(String id) {
		for (PlayerStat stat : values()) {
			if (stat.id.equals(id)) {
				return stat;
			}
		}
		return null;
	}
}
