package com.onepiecemod.guide.client;

import net.minecraft.client.Minecraft;

import com.onepiecemod.guide.GuideFeature;

/**
 * Client-only setup for the Pirate's Handbook. OnePieceModClient calls initialize().
 */
public class GuideClient {
	public static void initialize() {
		// The handbook became the Crafter's Journal (journal/client): same item, bigger book.
		GuideFeature.openBook = hand -> Minecraft.getInstance().gui.setScreen(new com.onepiecemod.journal.client.JournalScreen());
	}
}
