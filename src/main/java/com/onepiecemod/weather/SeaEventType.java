package com.onepiecemod.weather;

import net.minecraft.ChatFormatting;

/**
 * Every kind of sea and weather event. The numbers are easy to change:
 * radius is in blocks, durations are in seconds.
 *
 * wind is how much a ship's sails fill inside the event (1 = normal, 0 = none).
 */
public enum SeaEventType {
	STORM("storm", "Grand Line Storm", ChatFormatting.DARK_GRAY,
			"The sky is turning black... a storm is coming!",
			"A Grand Line storm hits! Lightning, wild winds and rough seas!",
			"The storm has passed.",
			110, 150, 1.4),
	WHIRLPOOL("whirlpool", "Whirlpool", ChatFormatting.DARK_AQUA,
			"The sea is starting to spin...",
			"A giant whirlpool opens up! Full sails to break free!",
			"The whirlpool calms down and spits out what it swallowed.",
			28, 100, 1.0),
	AQUA_LAGUNA("aqua_laguna", "Aqua Laguna", ChatFormatting.BLUE,
			"The tide is pulling far out... AQUA LAGUNA is coming! Get to high ground!",
			"AQUA LAGUNA! A giant wave is crashing over the island!",
			"The great wave has passed. The sea washed treasure ashore!",
			70, 45, 1.0),
	CALM_BELT_AMBUSH("calm_belt_ambush", "Sea King Ambush", ChatFormatting.DARK_RED,
			"The sea is dead calm. Too calm... something is under the ship.",
			"SEA KINGS! They're surfacing all around you!",
			"The Sea Kings sink back into the deep.",
			40, 60, 0.0),
	BLIZZARD("blizzard", "Sudden Blizzard", ChatFormatting.WHITE,
			"The air is getting icy cold. The Grand Line's seasons are changing!",
			"A blizzard! Stay near a fire or wear leather armor, or you'll freeze!",
			"The blizzard is over and the air warms up again.",
			100, 150, 0.7),
	HEAT_WAVE("heat_wave", "Scorching Heat Wave", ChatFormatting.GOLD,
			"The wind is dying and the sun is burning hotter...",
			"A heat wave! You'll get hungry fast out in the sun. Find shade or water!",
			"The heat breaks. A cool breeze is back.",
			110, 150, 0.4),
	FLORIAN_MIST("florian_mist", "Florian Triangle Mist", ChatFormatting.GRAY,
			"A cold white mist is rolling over the water...",
			"You sailed into the Florian Triangle's mist. Lost souls wander here...",
			"The mist lifts. Was it all a dream?",
			80, 120, 0.5),
	WATERSPOUT("waterspout", "Waterspout", ChatFormatting.DARK_AQUA,
			"A dark funnel is reaching down from the clouds toward the sea...",
			"A WATERSPOUT! Keep clear of the funnel or it'll tear at your hull and throw you overboard!",
			"The waterspout breaks apart into rain.",
			70, 90, 1.2),
	ROGUE_WAVE("rogue_wave", "Rogue Wave", ChatFormatting.BLUE,
			"The sea is drawing back... a huge wave is building out there!",
			"ROGUE WAVE! Turn your bow into it! A wave that hits you side-on can smash your hull!",
			"The rogue wave rolls on toward the horizon.",
			45, 0, 1.0),
	HAILSTORM("hailstorm", "Hailstorm", ChatFormatting.WHITE,
			"Black clouds are piling up and the air turns cold. That's hail weather!",
			"HAIL! Chunks of ice as big as cannonballs! Get under a roof or wear a helmet!",
			"The hail stops. The deck is covered in melting ice.",
			90, 100, 0.9),
	CYCLONE("cyclone", "Great Cyclone", ChatFormatting.DARK_PURPLE,
			"The horizon has gone black from end to end. A GREAT CYCLONE is crossing the sea toward you!",
			"The Great Cyclone hits! A tornado as tall as the sky, winds that spin ships around, lightning on every mast. Keep away from the funnel!",
			"The Great Cyclone rolls away over the horizon.",
			120, 300, 1.7, 0.05);

	public final String id;
	public final String title;
	public final ChatFormatting color;
	public final String warning;
	public final String startMessage;
	public final String endMessage;
	public final float radius;
	public final int seconds;
	public final double wind;
	/** How fast the whole event moves along its angle once it starts, in blocks per tick (0 = it stays put). */
	public final double drift;

	SeaEventType(String id, String title, ChatFormatting color, String warning, String startMessage, String endMessage,
			float radius, int seconds, double wind) {
		this(id, title, color, warning, startMessage, endMessage, radius, seconds, wind, 0);
	}

	SeaEventType(String id, String title, ChatFormatting color, String warning, String startMessage, String endMessage,
			float radius, int seconds, double wind, double drift) {
		this.id = id;
		this.title = title;
		this.color = color;
		this.warning = warning;
		this.startMessage = startMessage;
		this.endMessage = endMessage;
		this.radius = radius;
		this.seconds = seconds;
		this.wind = wind;
		this.drift = drift;
	}

	public static SeaEventType byId(String id) {
		for (SeaEventType type : values()) {
			if (type.id.equals(id)) {
				return type;
			}
		}
		return null;
	}
}
