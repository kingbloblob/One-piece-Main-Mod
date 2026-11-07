package com.onepiecemod.crew;

/**
 * The three kinds of recruit for each role. Each kind has its own outfit and stats:
 *   0 - the all-rounder (normal stats, the original outfit),
 *   1 - quick and hard-hitting, but less health,
 *   2 - a tough veteran: lots of health, a bit slower, costs more.
 *
 * Outfits: assets/onepiece/textures/entity/crewmate/<role>.png for kind 0,
 * and <role>_1.png / <role>_2.png for the others (painted by tools/skins/gen_crew_variants.py).
 */
public record CrewVariant(String title, double healthMultiplier, double damageMultiplier, double speedMultiplier,
		double costMultiplier) {
	public static final int COUNT = 3;

	public static CrewVariant of(CrewRole role, int index) {
		String[] titles = switch (role) {
			case SWORDSMAN -> new String[]{"Ronin", "Fencer", "Brute"};
			case NAVIGATOR -> new String[]{"Cartographer", "Sky Reader", "Old Sea Dog"};
			case SNIPER -> new String[]{"Sharpshooter", "Trickster", "Hunter"};
			case COOK -> new String[]{"Line Cook", "Kick Chef", "Galley Boss"};
			case DOCTOR -> new String[]{"Ship's Medic", "Field Surgeon", "Old Healer"};
			case SHIPWRIGHT -> new String[]{"Carpenter", "Tinkerer", "Iron Builder"};
			case ARCHAEOLOGIST -> new String[]{"Scholar", "Treasure Hunter", "Professor"};
			case MUSICIAN -> new String[]{"Fiddler", "Drummer", "Soul Singer"};
			case HELMSMAN -> new String[]{"Steersman", "Fish-man Swimmer", "Old Captain"};
		};
		return switch (Math.floorMod(index, COUNT)) {
			case 1 -> new CrewVariant(titles[1], 0.85, 1.15, 1.15, 1.15);
			case 2 -> new CrewVariant(titles[2], 1.3, 1.1, 0.9, 1.35);
			default -> new CrewVariant(titles[0], 1.0, 1.0, 1.0, 1.0);
		};
	}

	/** A short word for the speed, shown in the candidate list. */
	public String speedWord() {
		return speedMultiplier > 1.0 ? "fast" : speedMultiplier < 1.0 ? "slow" : "normal speed";
	}
}
