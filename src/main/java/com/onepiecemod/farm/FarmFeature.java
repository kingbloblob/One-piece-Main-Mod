package com.onepiecemod.farm;

/**
 * Farming and ranching across the Grand Line. OnePieceMod calls initialize() once at startup (after cuisine).
 *
 *  - Island crops (IslandCrop, IslandCropBlock): 14 crops from Wano rice to Thriller Bark's ghost pumpkins.
 *    Each grows at a normal pace on its home island and slowly anywhere else. Seeds: WildSeeds, harvests, the vault.
 *  - Seed Vault (SeedVaultBlock, SeedVault): bank one seed of each kind, draw a free one per day, earn rewards.
 *  - Irrigation (SprinklerBlock, WateringCanItem): wet farmland and extra growth. Ranch Manure: 5x5 growth.
 *  - Ranching (RanchTroughBlock, Ranching): fill a trough with fodder; animals around it make milk, eggs, wool,
 *    truffles and manure, and breed on their own.
 *  - Crew farm plots (ScarecrowBlock, FarmhandGoal): crewmates set to Work by a Straw Hat Scarecrow farm for you.
 *  - Farm dishes (FarmItems): 16 Ship's Galley meals with long buffs, using the island crops and ranch goods.
 *
 * Data (models, textures, loot, recipes, lang assets/onepiece_farm): tools/farm/gen_farm.py.
 */
public final class FarmFeature {
	private FarmFeature() {
	}

	public static void initialize() {
		FarmItems.initialize(); // Loading FarmItems loads FarmBlocks first (seeds need their crops).
		SeedVault.initialize();
		WildSeeds.initialize();
	}
}
