package com.onepiecemod.recipeview.client;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;

import com.onepiecemod.journal.client.JournalData;

/**
 * Client setup for item descriptions and the recipe data the Crafter's Journal shows.
 * (The item list beside the inventory was removed: JEI does that job, and the journal covers the rest.)
 * OnePieceModClient calls initialize().
 */
public class RecipeViewClient {
	public static void initialize() {
		ItemDescriptions.initialize();
		// Tags can differ between worlds and servers, so rebuild the recipe data after joining.
		ClientPlayConnectionEvents.JOIN.register((handler, sender, client) -> {
			RecipeIndex.reset();
			JournalData.reset();
		});
	}
}
