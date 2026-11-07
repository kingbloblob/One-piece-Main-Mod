package com.onepiecemod.crewship;

import java.util.ArrayList;
import java.util.List;

/**
 * The five steps from a little sloop to a Dream Ship like the Thousand Sunny. Each step needs everything of the
 * steps before it. "Stationed" = crewmates set to Work while standing aboard (they live on the ship).
 *
 *  1 Pirate Sloop         2 bunks, 1 job room
 *  2 Crew Ship            4 bunks, 3 job rooms with a Galley, 4 chests/barrels, 2 crewmates stationed
 *  3 Pirate Brig          6 bunks, 5 job rooms with an Infirmary, a Captain's Cabin, 2 cannons, 4 stationed
 *  4 Grand Line Galleon   8 bunks, 7 job rooms, a Garden or a Bath, 4 cannons, Hull II + Sails II, 6 stationed
 *  5 Dream Ship           10 bunks, all 9 job rooms, a Garden and a Bath, 6 cannons, a Cola Engine,
 *                         Hull III + Sails III + Guns III, 9 stationed
 */
public final class CrewShipLevels {
	public static final String[] NAMES = {"Unfinished Ship", "Pirate Sloop", "Crew Ship", "Pirate Brig", "Grand Line Galleon", "Dream Ship"};
	public static final int MAX = 5;

	private static final int[] BUNKS = {0, 2, 4, 6, 8, 10};
	private static final int[] JOB_ROOMS = {0, 1, 3, 5, 7, 9};
	private static final int[] STATIONED = {0, 0, 2, 4, 6, 9};
	private static final int[] CANNONS = {0, 0, 0, 2, 4, 6};

	/** One thing a level needs. */
	public record Need(String text, int have, int need) {
		public boolean done() {
			return have >= need;
		}
	}

	private CrewShipLevels() {
	}

	/** Everything the given level asks for (whole totals, not just what's new at that level). */
	public static List<Need> needs(int level, CrewShipSurvey survey, int stationed) {
		List<Need> needs = new ArrayList<>();
		if (level < 1 || level > MAX) {
			return needs;
		}
		needs.add(new Need("Bunks (beds or hammocks)", survey.bunks.size(), BUNKS[level]));
		needs.add(new Need("Crew job rooms", survey.jobRooms(), JOB_ROOMS[level]));
		if (level >= 2) {
			needs.add(new Need("Galley", flag(survey.has(ShipRoom.GALLEY)), 1));
			needs.add(new Need("Chests or barrels", survey.storage, 4));
			needs.add(new Need("Crewmates stationed aboard", stationed, STATIONED[level]));
		}
		if (level >= 3) {
			needs.add(new Need("Infirmary", flag(survey.has(ShipRoom.INFIRMARY)), 1));
			needs.add(new Need("Captain's Cabin", flag(survey.has(ShipRoom.CABIN)), 1));
			needs.add(new Need("Cannons", survey.cannons, CANNONS[level]));
		}
		if (level == 4) {
			needs.add(new Need("Garden or Bath", flag(survey.has(ShipRoom.GARDEN) || survey.has(ShipRoom.BATH)), 1));
		}
		if (level >= 4) {
			int fitted = level >= 5 ? 3 : 2;
			needs.add(new Need("Hull upgrade (Shipyard)", survey.hull, fitted));
			needs.add(new Need("Sails upgrade (Shipyard)", survey.sails, fitted));
		}
		if (level >= 5) {
			needs.add(new Need("Garden", flag(survey.has(ShipRoom.GARDEN)), 1));
			needs.add(new Need("Bath", flag(survey.has(ShipRoom.BATH)), 1));
			needs.add(new Need("Cola Engine", flag(survey.colaEngine), 1));
			needs.add(new Need("Guns upgrade (Shipyard)", survey.guns, 3));
		}
		return needs;
	}

	/** The highest level whose needs are all met. */
	public static int levelFor(CrewShipSurvey survey, int stationed) {
		int level = 0;
		for (int next = 1; next <= MAX; next++) {
			for (Need need : needs(next, survey, stationed)) {
				if (!need.done()) {
					return level;
				}
			}
			level = next;
		}
		return level;
	}

	/** What the level does for the crew, for the report. */
	public static String perk(int level) {
		return switch (level) {
			case 0 -> "Nothing yet. Add 2 bunks and a room for one crew job.";
			case 1 -> "Stationed crewmates live aboard, sleep in the bunks and bring a daily haul to the Ship's Log.";
			case 2 -> "Hauls x1.25. Crew resting aboard heal between fights.";
			case 3 -> "Hauls x1.5. Sails 5% faster.";
			case 4 -> "Hauls x1.75. Sails 10% faster and turns 10% faster.";
			default -> "Hauls x2. Sails 15% faster, turns 15% faster, and the crew trains aboard.";
		};
	}

	public static double haulBoost(int level) {
		return 1.0 + 0.25 * Math.max(0, level - 1);
	}

	public static float speedBonus(int level) {
		return level >= 5 ? 1.15f : level == 4 ? 1.10f : level == 3 ? 1.05f : 1f;
	}

	public static float turnBonus(int level) {
		return level >= 5 ? 1.15f : level == 4 ? 1.10f : 1f;
	}

	private static int flag(boolean value) {
		return value ? 1 : 0;
	}
}
