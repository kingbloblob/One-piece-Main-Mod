package com.onepiecemod.empire;

import net.minecraft.ChatFormatting;

/**
 * The late-game titles, earned in this order. Each one gives more loot, more taxes and more kingdoms,
 * and makes the Navy hunt you much harder. See EmpireRanks for what it takes to earn each one.
 */
public enum Title {
	NONE("None", ChatFormatting.GRAY, 0, 0.0f, 1, 3, 4, 1.0f, 1.0f),
	EMPEROR("Emperor of the Sea", ChatFormatting.GOLD, 4, 0.25f, 3, 20, 6, 2.0f, 0.5f),
	PIRATE_KING("Pirate King", ChatFormatting.RED, 1, 0.5f, 5, 40, 8, 3.0f, 0.33f),
	KING_OF_THE_WORLD("King of the World", ChatFormatting.DARK_PURPLE, 1, 1.0f, 8, 75, 10, 4.0f, 0.25f);

	public final String displayName;
	public final ChatFormatting color;
	/** How many players can hold this title at once (the Four Emperors, one Pirate King...). 0 = no limit. */
	public final int maxHolders;
	/** Extra loot from mobs and chests: 0.25 = 25% more. */
	public final float lootBonus;
	/** How many Kingdom Flags you may have planted. */
	public final int maxKingdoms;
	/** Berries each kingdom pays per Minecraft day (plus 1 per guard). */
	public final int taxPerDay;
	/** Most pirate guards one kingdom can have. */
	public final int maxGuards;
	/** Navy hunts and raids roll this many times more often. */
	public final float navyChance;
	/** The break between Navy hunts and raids is multiplied by this. */
	public final float navyBreak;

	Title(String displayName, ChatFormatting color, int maxHolders, float lootBonus, int maxKingdoms, int taxPerDay,
			int maxGuards, float navyChance, float navyBreak) {
		this.displayName = displayName;
		this.color = color;
		this.maxHolders = maxHolders;
		this.lootBonus = lootBonus;
		this.maxKingdoms = maxKingdoms;
		this.taxPerDay = taxPerDay;
		this.maxGuards = maxGuards;
		this.navyChance = navyChance;
		this.navyBreak = navyBreak;
	}

	public static Title byLevel(int level) {
		Title[] all = values();
		return all[Math.max(0, Math.min(all.length - 1, level))];
	}

	public Title next() {
		return this == KING_OF_THE_WORLD ? null : values()[ordinal() + 1];
	}

	public boolean atLeast(Title other) {
		return ordinal() >= other.ordinal();
	}
}
