package com.onepiecemod.season;

import net.minecraft.ChatFormatting;

/**
 * The four seasons. The world turns through them every few in-game days (see Seasons), but in the Grand Line each
 * island keeps its own: Drum is always in winter, Alabasta always in summer, and the rest are each at their own
 * point of the year, so sailing to the next island can take you from autumn straight into spring.
 */
public enum Season {
	SPRING("spring", "Spring", ChatFormatting.GREEN,
			"Spring has come. Crops grow faster and the seas are calmer."),
	SUMMER("summer", "Summer", ChatFormatting.GOLD,
			"Summer is here. Sunny crops thrive, and heat waves and waterspouts come more often."),
	AUTUMN("autumn", "Autumn", ChatFormatting.RED,
			"Autumn has come. Harvests are bigger, but it's storm season: Great Cyclones roam the sea."),
	WINTER("winter", "Winter", ChatFormatting.AQUA,
			"Winter has set in. Crops outdoors grow slowly unless they're in a lit greenhouse. Watch out for blizzards.");

	public final String id;
	public final String title;
	public final ChatFormatting color;
	public final String blurb;

	Season(String id, String title, ChatFormatting color, String blurb) {
		this.id = id;
		this.title = title;
		this.color = color;
		this.blurb = blurb;
	}

	public Season next() {
		return values()[(ordinal() + 1) % 4];
	}

	public static Season byId(String id) {
		for (Season season : values()) {
			if (season.id.equals(id)) {
				return season;
			}
		}
		return null;
	}
}
