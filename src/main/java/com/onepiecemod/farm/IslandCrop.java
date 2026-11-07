package com.onepiecemod.farm;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.biome.Biome;

import com.onepiecemod.OnePieceMod;

/**
 * The island crops of the Grand Line. Each one comes from one or two islands (its home biomes):
 * it grows at a normal pace there and only slowly anywhere else, so a farmer who wants every crop
 * has to sail and bring seeds home, or set up a farm on each island.
 *
 * Seeds: break grass, ferns and wild plants on the home island (WildSeeds), harvest a grown crop,
 * or draw a free seed a day from a Seed Vault once you have banked that kind (SeedVault).
 * Tools/farm/gen_farm.py draws the textures and writes the models, loot and recipes from the same table.
 */
public enum IslandCrop {
	EAST_BLUE_CABBAGE("east_blue_cabbage", "East Blue Cabbage", 3, 0.4f, "East Blue", "east_blue", "conomi_islands", "orange_town", "loguetown"),
	WANO_RICE("wano_rice", "Wano Rice", 1, 0.3f, "Wano", "wano", "kuri", "onigashima"),
	KIBI_MILLET("kibi_millet", "Kibi Millet", 1, 0.3f, "Wano", "wano", "kuri"),
	CLOUD_WHEAT("cloud_wheat", "Cloud Wheat", 1, 0.2f, "Skypiea", "skypiea"),
	ELBAPH_BARLEY("elbaph_barley", "Elbaph Barley", 1, 0.3f, "Elbaph", "elbaph"),
	FROST_TURNIP("frost_turnip", "Frost Turnip", 3, 0.5f, "Drum Island", "drum_island", "punk_hazard_frozen"),
	JUNGLE_YAM("jungle_yam", "Jungle Yam", 4, 0.5f, "Jaya and Little Garden", "jaya", "little_garden"),
	DRESSROSA_TOMATO("dressrosa_tomato", "Dressrosa Tomato", 3, 0.4f, "Dressrosa", "dressrosa", "green_bit"),
	SNAKE_PEPPER("snake_pepper", "Snake Pepper", 1, 0.2f, "Amazon Lily", "amazon_lily"),
	SEA_GRAPE("sea_grape", "Sea Grapes", 2, 0.3f, "Fishman Island and Sabaody", "fishman_reef", "sabaody"),
	TOTLAND_CACAO("totland_cacao", "Totland Cacao Pod", 2, 0.3f, "Whole Cake and Cacao Island", "whole_cake", "cacao_island"),
	MINK_TEA("mink_tea", "Mink Tea Leaves", 0, 0f, "Zou", "zou"),
	GHOST_PUMPKIN("ghost_pumpkin", "Ghost Pumpkin", 3, 0.4f, "Thriller Bark", "thriller_bark", "kuraigana", "withered_forest"),
	SAND_MELON("sand_melon", "Sand Melon Slice", 2, 0.3f, "Alabasta", "alabasta");

	public final String id;
	public final String title;
	/** Food value of the raw crop (0 = not edible, like tea leaves). */
	public final int nutrition;
	public final float saturation;
	/** Where it grows best, for tooltips. */
	public final String homeName;
	private final List<ResourceKey<Biome>> homes;

	IslandCrop(String id, String title, int nutrition, float saturation, String homeName, String... biomes) {
		this.id = id;
		this.title = title;
		this.nutrition = nutrition;
		this.saturation = saturation;
		this.homeName = homeName;
		this.homes = java.util.Arrays.stream(biomes).map(b -> ResourceKey.create(Registries.BIOME, OnePieceMod.id(b))).toList();
	}

	/** True when this spot is on one of the crop's home islands. */
	public boolean isHome(Level level, BlockPos pos) {
		var biome = level.getBiome(pos);
		for (ResourceKey<Biome> home : homes) {
			if (biome.is(home)) {
				return true;
			}
		}
		return false;
	}

	public static IslandCrop byId(String id) {
		for (IslandCrop crop : values()) {
			if (crop.id.equals(id)) {
				return crop;
			}
		}
		return null;
	}

	/** The crop whose home this spot is, or null (the first match if two share an island). */
	public static List<IslandCrop> homeCrops(Level level, BlockPos pos) {
		return java.util.Arrays.stream(values()).filter(c -> c.isHome(level, pos)).toList();
	}
}
