package com.onepiecemod.npc;

import net.minecraft.util.RandomSource;

/**
 * Made-up names for pirates and Marines, so every NPC has their own.
 * None of these are story characters, so nobody mistakes a deckhand for someone famous.
 */
public final class NpcNames {
	private static final String[] FIRST = {
			"Bolo", "Jiro", "Kenta", "Rocco", "Tobe", "Gaspar", "Mako", "Duval", "Hector", "Iwao", "Benny", "Okra", "Pepe", "Sato",
			"Marlo", "Gonzo", "Bart", "Kiku", "Rina", "Saya", "Tula", "Nico", "Vargas", "Higo", "Orin", "Pike", "Dobbs", "Toma",
			"Ruben", "Shin", "Yusuf", "Lars", "Fenn", "Ozzie", "Kobo", "Mira", "Wade", "Ines", "Taro", "Bram", "Cosmo", "Dario",
			"Elio", "Fumi", "Grete", "Hamid", "Ivo", "Jojo", "Kai", "Luca", "Momo", "Nils", "Otto", "Pia", "Quill", "Rafa",
			"Suki", "Tiko", "Ugo", "Vito", "Wim", "Yori", "Zed", "Abe", "Bea", "Cato", "Dex", "Esme", "Flint", "Gil", "Hana",
			"Ike", "Juno", "Kip", "Lulu", "Moe", "Nash", "Odo", "Poppy", "Rex", "Sid", "Tess", "Umi", "Vic", "Wren"
	};
	private static final String[] SURNAME = {
			"Kato", "Garcia", "Moreau", "Tanaka", "Okafor", "Silva", "Brandt", "Novak", "Ricci", "Haddad", "Yamada", "Lund",
			"Pereira", "Ito", "Kowal", "Mendes", "Sato", "Fischer", "Abara", "Costa", "Hayashi", "Duarte", "Weller", "Rossi",
			"Nakamura", "Bianchi", "Ogawa", "Ferreira", "Strand", "Mori", "Vidal", "Kane", "Ando", "Rhee", "Bauer", "Leclerc",
			"Ota", "Barros", "Quinn", "Sorensen", "Uchida", "Valdez", "Wolfe", "Yoshida", "Zamora", "Ibarra", "Holm", "Jansen"
	};
	private static final String[] EPITHET = {
			"\"Iron-Jaw\"", "\"Red Gull\"", "\"Saltbeard\"", "\"the Hook\"", "\"Two-Blade\"", "\"Cannon-Arm\"", "\"Sea Dog\"",
			"\"Gunpowder\"", "\"the Shark\"", "\"Stormcaller\"", "\"Bone-Breaker\"", "\"Barnacle\"", "\"Black Wind\"",
			"\"Golden Tooth\"", "\"the Eel\"", "\"Thunder Fist\"", "\"Rusty\"", "\"One-Eye\"", "\"Smiling\"", "\"Mad Dog\"",
			"\"Silver Fang\"", "\"the Crab\"", "\"Tidebreaker\"", "\"Scarlet\"", "\"Cutlass\"", "\"Wildfire\"", "\"the Viper\"",
			"\"Gale\"", "\"Anchor\"", "\"Copper Lung\""
	};
	private static final String[] CREW_A = {
			"Red", "Black", "Iron", "Golden", "Storm", "Sea", "Skull", "Silver", "Crimson", "Thunder", "Rusty", "Salt", "Shark",
			"Grinning", "Broken", "Wild", "Midnight", "Coral", "Burning", "Howling", "Lucky", "Rotten", "Jade", "Sunken"
	};
	private static final String[] CREW_B = {
			"Gull", "Fang", "Anchor", "Crab", "Eel", "Wolf", "Kraken", "Cutlass", "Lantern", "Moon", "Barrel", "Tide", "Hook",
			"Serpent", "Parrot", "Bones", "Compass", "Cannon", "Squid", "Marlin", "Ghost", "Rose", "Monkey", "Boar"
	};

	private NpcNames() {
	}

	public static String first(RandomSource random) {
		return FIRST[random.nextInt(FIRST.length)];
	}

	public static String surname(RandomSource random) {
		return SURNAME[random.nextInt(SURNAME.length)];
	}

	public static String epithet(RandomSource random) {
		return EPITHET[random.nextInt(EPITHET.length)];
	}

	/** A made-up pirate crew, like "Red Gull Pirates". */
	public static String crew(RandomSource random) {
		return CREW_A[random.nextInt(CREW_A.length)] + " " + CREW_B[random.nextInt(CREW_B.length)] + " Pirates";
	}

	/** Fills in a kit's name pattern. Extra spaces from empty parts are tidied away. */
	public static String fill(String pattern, String rank, String crew, RandomSource random) {
		String name = pattern
				.replace("{rank}", rank)
				.replace("{crew}", crew)
				.replace("{name}", first(random))
				.replace("{surname}", surname(random))
				.replace("{epithet}", epithet(random))
				.replace("{num}", String.valueOf(1 + random.nextInt(999)));
		return name.trim().replaceAll(" +", " ");
	}
}
