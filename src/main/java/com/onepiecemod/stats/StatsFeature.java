package com.onepiecemod.stats;

/**
 * Pirate Level and the stat tree: grow stronger by fighting and training, then spend
 * stat points on Strength, Toughness, Speed, Stamina and Swordsmanship (K key or /stats).
 *
 * This is separate from Haki and Devil Fruit mastery, which keep their own training.
 * OnePieceMod calls initialize() once while the game loads.
 */
public class StatsFeature {
	public static void initialize() {
		StatsAttachments.initialize();
		StatsPayloads.initialize();
		StatTraining.initialize();
		StatBonuses.initialize();
		StatsCommands.initialize();
	}
}
