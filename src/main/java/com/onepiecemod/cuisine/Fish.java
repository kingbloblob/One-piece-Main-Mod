package com.onepiecemod.cuisine;

import java.util.List;

import com.onepiecemod.sea.CalmBelt;

/**
 * Every fish you can catch, and where it bites.
 *
 * A fish lives either in one of the seas (by distance from spawn, see sea/CalmBelt), around certain islands
 * (by the biome under the bobber), or only in the All Blue. Weight decides how often it bites compared with
 * the other fish of the same place: common 10, uncommon 5, rare 2.
 */
public enum Fish {
	// The East Blue
	BLUE_SEA_BREAM("blue_sea_bream", "Blue Sea Bream", Where.SEA, CalmBelt.Sea.BLUE, List.of(), 10, 3, 0.4f),
	STRIPED_MACKEREL("striped_mackerel", "Striped Mackerel", Where.SEA, CalmBelt.Sea.BLUE, List.of(), 10, 3, 0.4f),
	EAST_BLUE_LOBSTER("east_blue_lobster", "East Blue Lobster", Where.SEA, CalmBelt.Sea.BLUE, List.of(), 4, 4, 0.5f),
	// The Calm Belt
	CALM_BELT_EEL("calm_belt_eel", "Calm Belt Eel", Where.SEA, CalmBelt.Sea.CALM_BELT, List.of(), 10, 3, 0.5f),
	SEA_KING_FRY("sea_king_fry", "Sea King Fry", Where.SEA, CalmBelt.Sea.CALM_BELT, List.of(), 2, 5, 0.6f),
	// The Grand Line (Paradise)
	ELEPHANT_HONMAGURO("elephant_honmaguro", "Elephant Honmaguro", Where.SEA, CalmBelt.Sea.GRAND_LINE, List.of(), 6, 5, 0.6f),
	GRAND_LINE_PUFFER("grand_line_puffer", "Grand Line Puffer", Where.SEA, CalmBelt.Sea.GRAND_LINE, List.of(), 8, 1, 0.1f),
	RAINBOW_SNAPPER("rainbow_snapper", "Rainbow Snapper", Where.SEA, CalmBelt.Sea.GRAND_LINE, List.of(), 6, 3, 0.4f),
	// The New World
	NEW_WORLD_SWORDFISH("new_world_swordfish", "New World Swordfish", Where.SEA, CalmBelt.Sea.NEW_WORLD, List.of(), 8, 4, 0.5f),
	ABYSS_ANGLER("abyss_angler", "Abyss Anglerfish", Where.SEA, CalmBelt.Sea.NEW_WORLD, List.of(), 5, 3, 0.4f),
	// Island waters (fish anywhere in or next to these islands, rivers and ponds count too)
	GLOWFIN("glowfin", "Glowfin", Where.ISLAND, null, List.of("onepiece:fishman_reef", "onepiece:sabaody"), 10, 3, 0.4f),
	SKY_FISH("sky_fish", "Sky Fish", Where.ISLAND, null, List.of("onepiece:skypiea"), 10, 3, 0.4f),
	GOLDEN_KOI("golden_koi", "Golden Koi", Where.ISLAND, null, List.of("onepiece:wano", "onepiece:onigashima"), 10, 3, 0.4f),
	FROSTFIN_COD("frostfin_cod", "Frostfin Cod", Where.ISLAND, null,
			List.of("onepiece:drum_island", "onepiece:punk_hazard_frozen"), 10, 3, 0.4f),
	SANDORA_CATFISH("sandora_catfish", "Sandora Catfish", Where.ISLAND, null, List.of("onepiece:alabasta"), 10, 3, 0.4f),
	GHOST_FISH("ghost_fish", "Ghost Fish", Where.ISLAND, null, List.of("onepiece:thriller_bark"), 10, 2, 0.2f),
	// Only in the All Blue
	ALL_BLUE_KINGFISH("all_blue_kingfish", "All Blue Kingfish", Where.ALL_BLUE, null, List.of(), 3, 6, 0.8f),
	RAINBOW_SUNFISH("rainbow_sunfish", "Rainbow Sunfish", Where.ALL_BLUE, null, List.of(), 4, 5, 0.7f);

	public enum Where { SEA, ISLAND, ALL_BLUE }

	public final String id;
	public final String title;
	public final Where where;
	/** For SEA fish: which sea. */
	public final CalmBelt.Sea sea;
	/** For ISLAND fish: the biome ids it lives in. */
	public final List<String> biomes;
	public final int weight;
	public final int nutrition;
	public final float saturation;

	Fish(String id, String title, Where where, CalmBelt.Sea sea, List<String> biomes, int weight, int nutrition, float saturation) {
		this.id = id;
		this.title = title;
		this.where = where;
		this.sea = sea;
		this.biomes = biomes;
		this.weight = weight;
		this.nutrition = nutrition;
		this.saturation = saturation;
	}

	/** Where to find it, for tooltips and the fish log. */
	public String habitat() {
		return switch (where) {
			case SEA -> switch (sea) {
				case BLUE -> "the East Blue";
				case CALM_BELT -> "the Calm Belt";
				case GRAND_LINE -> "the Grand Line";
				case NEW_WORLD -> "the New World";
			};
			case ISLAND -> switch (this) {
				case GLOWFIN -> "Fishman Island and Sabaody waters";
				case SKY_FISH -> "the White Sea of Skypiea";
				case GOLDEN_KOI -> "the rivers of Wano";
				case FROSTFIN_COD -> "the icy waters of Drum and Punk Hazard";
				case SANDORA_CATFISH -> "the Sandora River in Alabasta";
				default -> "Thriller Bark's foggy sea";
			};
			case ALL_BLUE -> "the All Blue, and nowhere else";
		};
	}

	public static Fish byId(String id) {
		for (Fish fish : values()) {
			if (fish.id.equals(id)) {
				return fish;
			}
		}
		return null;
	}
}
