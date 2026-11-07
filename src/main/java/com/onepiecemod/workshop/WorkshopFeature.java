package com.onepiecemod.workshop;

import net.minecraft.world.item.Item;

import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.crafting.CraftingFeature;

/**
 * Station upgrade trees, the Skypiea Dials, the higher cooking tiers and rare station drops.
 *
 *  - Every station has an upgrade tree (onepiece/station_upgrades.json). Open a station and press "Upgrades".
 *    Upgrades unlock new recipes (the Galley's cooking tiers II and III, the Dials, the Fang Blade)
 *    and give perks: a chance of an extra result, or of keeping the ingredients.
 *  - The new recipes are in onepiece/station_recipes.json with "requires": {"upgrade": "..."}.
 *  - Rare drops (RareDrops) are only used at one station each.
 * Call initialize() after CraftingFeature.
 */
public class WorkshopFeature {
	public static void initialize() {
		WorkshopItems.initialize();
		StationUpgrades.initialize();
		DialTools.initialize();
		RareDrops.initialize();

		CreativeModeTabEvents.modifyOutputEvent(CraftingFeature.TAB_KEY).register(output -> {
			for (Item item : WorkshopItems.TAB_ITEMS) {
				output.accept(item);
			}
		});

		// Typos in station_upgrades.json would only show up as a missing upgrade, so list them in the log.
		ServerLifecycleEvents.SERVER_STARTED.register(server -> {
			for (String problem : StationUpgrade.problems()) {
				OnePieceMod.LOGGER.warn("Station upgrade problem: {}", problem);
			}
			OnePieceMod.LOGGER.info("Station upgrades: {}", StationUpgrade.all().size());
		});
	}
}
