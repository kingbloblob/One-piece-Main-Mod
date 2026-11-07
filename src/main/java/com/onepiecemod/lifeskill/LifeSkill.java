package com.onepiecemod.lifeskill;

import java.util.List;

/**
 * The four life skills. Each levels 1 to 50 on its own by doing the job, with perks along the way.
 *
 * Every skill has a small bonus that grows with each level, plus three milestone perks.
 * The milestone levels are the same for every skill (10, 25 and 50), so they're easy to remember.
 */
public enum LifeSkill {
	FARMING("farming", "Farming", 0x7BC24F,
			"Bountiful Harvest: +0.5% chance per level to harvest twice",
			List.of(
					new Milestone(10, "Green Thumb", "Harvested crops replant themselves if you carry the seed."),
					new Milestone(25, "Fertile Touch", "Harvesting can make nearby crops grow a stage."),
					new Milestone(50, "Bumper Crop", "Bountiful Harvest rolls twice.")
			)),
	MINING("mining", "Mining", 0x9AA7B8,
			"Lucky Strike: +0.4% chance per level to get an ore's drops twice",
			List.of(
					new Milestone(10, "Steady Pick", "Mining an ore gives Haste I for 10 seconds."),
					new Milestone(25, "Hard Hat", "Steady Pick becomes Haste II."),
					new Milestone(50, "Prospector", "Ores drop twice as much experience.")
			)),
	COOKING("cooking", "Cooking", 0xF29B4B,
			"Extra Portion: +0.5% chance per level to cook one extra food",
			List.of(
					new Milestone(10, "Hearty Eater", "Every meal fills 1 more hunger."),
					new Milestone(25, "Warm Meal", "Eating gives Regeneration I for 5 seconds."),
					new Milestone(50, "Master Chef", "Extra Portion gives 2, and Hearty Eater fills 2.")
			)),
	SMITHING("smithing", "Smithing", 0xD9A441,
			"Sturdy Make: gear you craft has +1% durability per level",
			List.of(
					new Milestone(10, "Field Repair", "The tool in your hand mends 1 durability every 30 seconds."),
					new Milestone(25, "Smith's Mark", "Gear you craft has a 15% chance to be Fine (Unbreaking I)."),
					new Milestone(50, "Master Smith", "Sturdy Make doubles, and Fine gear gets Unbreaking II.")
			));

	public static final int MAX_LEVEL = 50;

	public final String id;
	public final String displayName;
	public final int color;
	/** The small bonus that grows every level. */
	public final String levelBonus;
	public final List<Milestone> milestones;

	LifeSkill(String id, String displayName, int color, String levelBonus, List<Milestone> milestones) {
		this.id = id;
		this.displayName = displayName;
		this.color = color;
		this.levelBonus = levelBonus;
		this.milestones = milestones;
	}

	public static LifeSkill byId(String id) {
		for (LifeSkill skill : values()) {
			if (skill.id.equalsIgnoreCase(id)) {
				return skill;
			}
		}
		return null;
	}

	/** The milestone unlocked exactly at this level, or null. */
	public Milestone milestoneAt(int level) {
		for (Milestone milestone : milestones) {
			if (milestone.level() == level) {
				return milestone;
			}
		}
		return null;
	}

	public record Milestone(int level, String name, String description) {
	}
}
