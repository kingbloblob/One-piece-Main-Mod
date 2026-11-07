package com.onepiecemod.crafting;

import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;

/**
 * The five crafting stations, from the first one you can build to the last.
 * Each station only knows its own recipes (see onepiece/station_recipes.json).
 */
public enum Station {
	SHIPWRIGHT_BENCH("shipwright_bench", "Shipwright's Bench", 1, SoundEvents.VILLAGER_WORK_FLETCHER),
	SHIPS_GALLEY("ships_galley", "Ship's Galley", 1, SoundEvents.VILLAGER_WORK_BUTCHER),
	NAVIGATORS_DESK("navigators_desk", "Navigator's Desk", 2, SoundEvents.VILLAGER_WORK_CARTOGRAPHER),
	SEASTONE_WORKBENCH("seastone_workbench", "Seastone Workbench", 3, SoundEvents.SMITHING_TABLE_USE),
	SWORDSMITH_FORGE("swordsmith_forge", "Swordsmith's Forge", 4, SoundEvents.ANVIL_USE);

	private final String id;
	private final String title;
	private final int tier;
	private final SoundEvent sound;

	Station(String id, String title, int tier, SoundEvent sound) {
		this.id = id;
		this.title = title;
		this.tier = tier;
		this.sound = sound;
	}

	/** The block id, like "shipwright_bench". Also used in the recipe file. */
	public String id() {
		return id;
	}

	public String title() {
		return title;
	}

	/** 1 = East Blue, 2 = Grand Line, 3 = Seastone, 4 = Meito. Only shown to players. */
	public int tier() {
		return tier;
	}

	/** Played when something is crafted here. */
	public SoundEvent sound() {
		return sound;
	}

	public static Station byId(String id) {
		for (Station station : values()) {
			if (station.id.equals(id)) {
				return station;
			}
		}
		return null;
	}
}
