package com.onepiecemod.career;

import java.util.List;

import net.minecraft.ChatFormatting;

/**
 * The three lives a player can lead: a pirate (everyone starts here), a Marine, or a Revolutionary.
 *
 * Marines earn Merit instead of a bounty: they hunt pirates, carry out orders and climb from Seaman Recruit
 * to Fleet Admiral. Revolutionaries keep their bounty, earn Liberation by fighting the Navy and the World
 * Government, and climb from Sympathizer to Dragon's Right Hand. Change the numbers in the rank lists below.
 */
public enum Career {
	PIRATE("pirate", "Pirate", ChatFormatting.GOLD, "", List.of()),
	MARINE("marine", "Marine", ChatFormatting.AQUA, "Merit", List.of(
			//       name               short       need   bosses to bring in (any of)                  how many  salary backup
			new Rank("Seaman Recruit", "Recruit", 0, List.of(), 0, 2, 1),
			new Rank("Petty Officer", "P. Officer", 60, List.of(), 0, 3, 2),
			new Rank("Ensign", "Ensign", 200, List.of(), 0, 4, 2),
			new Rank("Lieutenant", "Lt.", 500, List.of("buggy"), 1, 6, 3),
			new Rank("Commander", "Cmdr.", 1000, List.of(), 0, 8, 3),
			new Rank("Captain", "Capt.", 2000, List.of("crocodile", "enel"), 1, 12, 4),
			new Rank("Commodore", "Cdre.", 3500, List.of("moria", "hawkins", "killer"), 1, 16, 4),
			new Rank("Rear Admiral", "R. Adm.", 5500, List.of("doflamingo", "kid"), 1, 22, 5),
			new Rank("Vice Admiral", "V. Adm.", 8500, List.of("katakuri", "king"), 1, 30, 5),
			new Rank("Admiral", "Admiral", 13000, List.of("kaido", "big_mom", "whitebeard", "blackbeard"), 1, 45, 6),
			new Rank("Fleet Admiral", "F. Adm.", 20000, List.of("kaido", "big_mom", "whitebeard", "blackbeard"), 3, 70, 7))),
	REVOLUTIONARY("revolutionary", "Revolutionary", ChatFormatting.GREEN, "Liberation", List.of(
			new Rank("Sympathizer", "Sympathizer", 0, List.of(), 0, 1, 1),
			new Rank("Recruit", "Recruit", 60, List.of(), 0, 2, 2),
			new Rank("Soldier", "Soldier", 200, List.of(), 0, 3, 2),
			new Rank("Officer", "Officer", 500, List.of("smoker"), 1, 5, 3),
			new Rank("Commander", "Cmdr.", 1000, List.of(), 0, 7, 3),
			new Rank("Army Commander", "Army Cmdr.", 2500, List.of("lucci", "magellan"), 1, 12, 4),
			new Rank("Chief of Staff", "Chief of Staff", 6000, List.of("kizaru", "akainu", "fujitora", "ryokugyu", "aokiji"), 1, 22, 5),
			new Rank("Dragon's Right Hand", "Right Hand", 12000, List.of("kizaru", "akainu", "fujitora", "ryokugyu", "aokiji"), 3, 40, 6)));

	/**
	 * One rank on the ladder.
	 * @param need    Merit (or Liberation) needed
	 * @param trial   story bosses, by characters.json id; beating {@code trialCount} different ones is part of the promotion
	 * @param salary  Berries paid every in-game day
	 * @param backup  how many soldiers come when you call for backup
	 */
	public record Rank(String name, String shortName, int need, List<String> trial, int trialCount, int salary, int backup) {
	}

	/** Bosses on the Marine side. A Marine gets no Merit for beating them; a Revolutionary gets Liberation. */
	public static final List<String> NAVY_BOSSES = List.of("smoker", "lucci", "kizaru", "akainu", "fujitora", "ryokugyu",
			"aokiji", "magellan", "imu", "garp", "sengoku", "koby", "tashigi");

	/** Who you talk to in order to join: Marines at Shells Town, the Marine base, Loguetown and Marineford. */
	public static final List<String> MARINE_RECRUITERS = List.of("koby", "garp", "sengoku", "tashigi");
	/** Revolutionaries at Baltigo and Newkama Land (or use a Revolutionary Invitation). */
	public static final List<String> REVOLUTIONARY_RECRUITERS = List.of("dragon", "sabo", "ivankov");

	public final String id;
	public final String displayName;
	public final ChatFormatting color;
	/** What the points are called: "Merit" or "Liberation". */
	public final String points;
	public final List<Rank> ranks;

	Career(String id, String displayName, ChatFormatting color, String points, List<Rank> ranks) {
		this.id = id;
		this.displayName = displayName;
		this.color = color;
		this.points = points;
		this.ranks = ranks;
	}

	public Rank rank(int index) {
		return ranks.isEmpty() ? null : ranks.get(Math.max(0, Math.min(index, ranks.size() - 1)));
	}

	public static Career byId(String id) {
		for (Career career : values()) {
			if (career.id.equals(id)) {
				return career;
			}
		}
		return PIRATE;
	}
}
