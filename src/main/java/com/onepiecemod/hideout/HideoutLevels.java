package com.onepiecemod.hideout;

import java.util.ArrayList;
import java.util.List;

/**
 * The five steps from a beach camp to a pirate fortress. Each needs everything of the steps before it.
 *
 *  1 Pirate Camp      1 bed, a campfire
 *  2 Hideout          3 beds, 2 chests or barrels, a crafting table, a furnace or smoker, 3 crewmates living here
 *  3 Pirate Fort      5 beds, 2 cannons, a finished Marine Watchtower, 5 crewmates
 *  4 Stronghold       7 beds, 4 cannons, 2 more finished buildings (Dojo, Shipyard, Feast Table, Vault, Relay), 7 crewmates
 *  5 Pirate Fortress  9 beds, 8 cannons, 4 more buildings with a Treasure Vault among them, all 9 crewmates
 *
 * Crewmates "live here" when they're set to Work somewhere inside the claim.
 */
public final class HideoutLevels {
	public static final String[] NAMES = {"Claimed Land", "Pirate Camp", "Hideout", "Pirate Fort", "Stronghold", "Pirate Fortress"};
	public static final int MAX = 5;

	private static final int[] BEDS = {0, 1, 3, 5, 7, 9};
	private static final int[] CANNONS = {0, 0, 0, 2, 4, 8};
	private static final int[] RESIDENTS = {0, 0, 3, 5, 7, 9};
	private static final int[] BUILDINGS = {0, 0, 0, 0, 2, 4};

	/** One thing a level needs. */
	public record Need(String text, int have, int need) {
		public boolean done() {
			return have >= need;
		}
	}

	private HideoutLevels() {
	}

	/** Everything the given level asks for (cumulative numbers, not just what's new at that level). */
	public static List<Need> needs(int level, HideoutSurvey survey, int residents) {
		List<Need> needs = new ArrayList<>();
		if (level < 1 || level > MAX) {
			return needs;
		}
		needs.add(new Need("Beds", survey.beds.size(), BEDS[level]));
		if (level >= 1) {
			needs.add(new Need("Campfire", survey.campfires.size(), 1));
		}
		if (level >= 2) {
			needs.add(new Need("Chests or barrels", survey.storage, 2));
			needs.add(new Need("Crafting table", survey.craftingTable ? 1 : 0, 1));
			needs.add(new Need("Furnace, smoker or stove", survey.kitchen ? 1 : 0, 1));
			needs.add(new Need("Crewmates living here", residents, RESIDENTS[level]));
		}
		if (level >= 3) {
			needs.add(new Need("Cannons", survey.cannons.size(), CANNONS[level]));
			needs.add(new Need("Marine Watchtower (finished)", survey.buildings.contains("alarm_bell") ? 1 : 0, 1));
		}
		if (level >= 4) {
			needs.add(new Need("Other finished buildings", survey.otherBuildings(), BUILDINGS[level]));
		}
		if (level >= 5) {
			needs.add(new Need("Treasure Vault (finished)", survey.buildings.contains("treasure_vault") ? 1 : 0, 1));
		}
		return needs;
	}

	/** The highest level whose needs are all met. */
	public static int levelFor(HideoutSurvey survey, int residents) {
		int level = 0;
		for (int next = 1; next <= MAX; next++) {
			boolean ok = true;
			for (Need need : needs(next, survey, residents)) {
				ok &= need.done();
			}
			if (!ok) {
				break;
			}
			level = next;
		}
		return level;
	}

	/** What the level does for you, for the screen and chat. */
	public static String perk(int level) {
		return switch (level) {
			case 0 -> "Nothing yet. Put down a bed and a campfire to make camp.";
			case 1 -> "Your crew can sleep here and brings in a small daily haul.";
			case 2 -> "Bigger hauls. Resting here heals you between fights.";
			case 3 -> "Cannons fire at Navy attackers. The Watchtower spots them early.";
			case 4 -> "Hauls x1.75. Crewmates heal faster here.";
			default -> "Hauls x2. The Navy needs its best to break you.";
		};
	}

	/** Daily haul multiplier. */
	public static double haulBoost(int level) {
		return 1.0 + 0.25 * Math.max(0, level - 1);
	}
}
