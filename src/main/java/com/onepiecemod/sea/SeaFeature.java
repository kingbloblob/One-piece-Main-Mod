package com.onepiecemod.sea;

import com.onepiecemod.ship.ShipEntity;

/**
 * Sets up the dangers and tools of the sea: Sea Kings, the Calm Belt, Log Poses,
 * Eternal Poses and Den Den Mushi. OnePieceMod calls initialize() once while the game loads.
 */
public class SeaFeature {
	public static void initialize() {
		SeaItems.initialize();
		SeaEntities.initialize();
		SeaKingSpawner.initialize();
		SeaKingLoot.initialize();
		SeaBosses.initialize(); // The four named Sea King bosses, the Sea Lord Lure and /seaboss.
		CalmBelt.initialize();
		LogPoseTracker.initialize();
		StartingIsland.initialize();

		// Ships get no wind in their sails inside the Calm Belt. They can still crawl along slowly.
		ShipEntity.windAt = CalmBelt::windMultiplier;
	}
}
