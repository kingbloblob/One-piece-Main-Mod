package com.onepiecemod.world;

import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.biome.Biomes;
import net.minecraft.world.level.biome.Climate;

import net.fabricmc.fabric.api.biome.v1.NetherBiomes;
import net.fabricmc.fabric.api.biome.v1.TheEndBiomes;

import com.onepiecemod.OnePieceMod;

/**
 * Adds the mod's Nether and End biomes to normal worlds (their JSON is in data/onepiece/worldgen/biome,
 * made by tools/dimensions/gen_dimensions.py).
 * - Nether: the deep levels of Impel Down (Blazing Hell, Freezing Hell) and the hidden Newkama Land.
 * - End: the Red Line heights with the Holy Land Mary Geoise, and the ruins of the Void Century.
 */
public class DimensionBiomes {
	public static final ResourceKey<Biome> BLAZING_HELL = key("impel_down_blazing_hell");
	public static final ResourceKey<Biome> FREEZING_HELL = key("impel_down_freezing_hell");
	public static final ResourceKey<Biome> NEWKAMA_LAND = key("newkama_land");
	public static final ResourceKey<Biome> RED_LINE_HEIGHTS = key("red_line_heights");
	public static final ResourceKey<Biome> VOID_CENTURY_RUINS = key("void_century_ruins");

	public static void initialize() {
		// Each Nether biome sits at its own spot on the Nether's climate map (temperature, humidity and an offset
		// that makes it rarer). Vanilla uses: wastes 0/0, soul sand -0.5 humidity, crimson 0.4 temp,
		// warped 0.5 humidity, basalt deltas -0.5 temp.
		NetherBiomes.addNetherBiome(BLAZING_HELL, Climate.parameters(0.8f, -0.3f, 0.0f, 0.0f, 0.0f, 0.0f, 0.2f));
		NetherBiomes.addNetherBiome(FREEZING_HELL, Climate.parameters(-0.8f, 0.3f, 0.0f, 0.0f, 0.0f, 0.0f, 0.2f));
		NetherBiomes.addNetherBiome(NEWKAMA_LAND, Climate.parameters(0.3f, 0.8f, 0.0f, 0.0f, 0.0f, 0.0f, 0.3f));

		// End: weights are compared with the vanilla End Highlands (1.0). The edges of these islands stay vanilla.
		TheEndBiomes.addHighlandsBiome(RED_LINE_HEIGHTS, 0.5);
		TheEndBiomes.addMidlandsBiome(RED_LINE_HEIGHTS, Biomes.END_MIDLANDS, 1.0);
		TheEndBiomes.addBarrensBiome(RED_LINE_HEIGHTS, Biomes.END_BARRENS, 1.0);
		TheEndBiomes.addHighlandsBiome(VOID_CENTURY_RUINS, 0.4);
		TheEndBiomes.addMidlandsBiome(VOID_CENTURY_RUINS, Biomes.END_MIDLANDS, 1.0);
		TheEndBiomes.addBarrensBiome(VOID_CENTURY_RUINS, Biomes.END_BARRENS, 1.0);
	}

	private static ResourceKey<Biome> key(String name) {
		return ResourceKey.create(Registries.BIOME, OnePieceMod.id(name));
	}
}
