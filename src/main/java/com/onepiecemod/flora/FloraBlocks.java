package com.onepiecemod.flora;

import java.util.function.Function;

import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.DoubleHighBlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockBehaviour;

import com.onepiecemod.OnePieceMod;

/**
 * Flowers, tall plants, grass, shrubs, ground cover and soils for every island of the Grand Line.
 *
 * This file is made by tools/flora/gen_flora.py (together with the models, textures, loot tables,
 * tags, recipes and the biome tags saying where each plant grows). To add a plant, add it to that
 * script's tables and run it again rather than editing here.
 */
public class FloraBlocks {
	// ---- Flowers (one block; also grow on sand, snow, rock and the island soils, see FloraPlants.SOIL) ----
	public static final Block DAWN_POPPY = flower("dawn_poppy", MobEffects.REGENERATION, 3, 0);
	public static final Block SEA_PINK = flower("sea_pink", MobEffects.WATER_BREATHING, 4, 0);
	public static final Block MARINE_ROSE = flower("marine_rose", MobEffects.RESISTANCE, 3, 0);
	public static final Block TOY_TULIP = flower("toy_tulip", MobEffects.JUMP_BOOST, 4, 0);
	public static final Block JAYA_HIBISCUS = flower("jaya_hibiscus", MobEffects.SATURATION, 1, 0);
	public static final Block WINTER_ROSE = flower("winter_rose", MobEffects.RESISTANCE, 4, 0);
	public static final Block WANO_IRIS = flower("wano_iris", MobEffects.NIGHT_VISION, 4, 0);
	public static final Block KIKU_CHRYSANTHEMUM = flower("kiku_chrysanthemum", MobEffects.REGENERATION, 3, 0);
	public static final Block JUSTICE_LILY = flower("justice_lily", MobEffects.RESISTANCE, 3, 0);
	public static final Block KUJA_ORCHID = flower("kuja_orchid", MobEffects.POISON, 6, 0);
	public static final Block CACAO_BLOSSOM = flower("cacao_blossom", MobEffects.SATURATION, 1, 0);
	public static final Block GRAVE_LILY = flower("grave_lily", MobEffects.WEAKNESS, 5, 0);
	public static final Block HOLO_FLOWER = flower("holo_flower", MobEffects.HASTE, 5, 8);
	public static final Block SKULL_LILY = flower("skull_lily", MobEffects.STRENGTH, 4, 0);
	public static final Block CINDER_POPPY = flower("cinder_poppy", MobEffects.FIRE_RESISTANCE, 4, 7);
	public static final Block VALLEY_BLOOM = flower("valley_bloom", MobEffects.LUCK, 5, 3);
	public static final Block TONTATTA_CLOVER = flower("tontatta_clover", MobEffects.LUCK, 5, 0);
	public static final Block SKY_BELL = flower("sky_bell", MobEffects.SLOW_FALLING, 5, 0);
	public static final Block GIANTS_CLOVER = flower("giants_clover", MobEffects.STRENGTH, 3, 0);
	public static final Block ZUNESHA_BLOSSOM = flower("zunesha_blossom", MobEffects.REGENERATION, 3, 0);
	public static final Block SAND_ROSE = flower("sand_rose", MobEffects.SATURATION, 1, 0);
	public static final Block CLIFF_EDELWEISS = flower("cliff_edelweiss", MobEffects.RESISTANCE, 4, 0);
	public static final Block SABAODY_BUBBLE_BLOOM = flower("sabaody_bubble_bloom", MobEffects.SLOW_FALLING, 4, 2);
	public static final Block FROST_THISTLE_BLOOM = flower("frost_thistle_bloom", MobEffects.SLOWNESS, 3, 3);

	// ---- Two-block plants ----
	public static final Block SEA_LAVENDER = tall("sea_lavender", 0);
	public static final Block DESERT_THISTLE = tall("desert_thistle", 0);
	public static final Block SOUTH_BIRD_FERN = tall("south_bird_fern", 0);
	public static final Block PRIMEVAL_BLOSSOM = tall("primeval_blossom", 0);
	public static final Block WITHERED_BRAMBLE = tall("withered_bramble", 0);
	public static final Block KURI_PAMPAS = tall("kuri_pampas", 0);
	public static final Block ICE_THISTLE = tall("ice_thistle", 0);
	public static final Block CINDER_SHRUB = tall("cinder_shrub", 6);
	public static final Block GIANT_BARLEY = tall("giant_barley", 0);
	public static final Block MINK_FERN = tall("mink_fern", 0);
	public static final Block PASSION_ROSE = tall("passion_rose", 0);
	public static final Block CANDY_SHRUB = tall("candy_shrub", 0);
	public static final Block ONI_THISTLE = tall("oni_thistle", 0);
	public static final Block PIRATE_BRAMBLE = tall("pirate_bramble", 0);
	public static final Block KURAIGANA_THISTLE = tall("kuraigana_thistle", 0);
	public static final Block CELESTIAL_LILY = tall("celestial_lily", 2);
	public static final Block CLIFF_THISTLE = tall("cliff_thistle", 0);
	public static final Block UPPER_YARD_REED = tall("upper_yard_reed", 0);
	public static final Block MANGROVE_REED = tall("mangrove_reed", 0);
	public static final Block NEON_FERN = tall("neon_fern", 6);

	// ---- Grass tufts with their own colours ----
	public static final Block FROST_FERN = grass("frost_fern", 0);
	public static final Block SAND_SAGE = grass("sand_sage", 0);
	public static final Block HEAVEN_GRASS = grass("heaven_grass", 0);
	public static final Block DINO_FERN = grass("dino_fern", 0);
	public static final Block EMBER_GRASS = grass("ember_grass", 5);
	public static final Block WAFER_GRASS = grass("wafer_grass", 0);
	public static final Block ASH_GRASS = grass("ash_grass", 0);
	public static final Block CELESTIAL_GRASS = grass("celestial_grass", 0);
	public static final Block HARBOR_SEDGE = grass("harbor_sedge", 0);
	public static final Block SAWGRASS = grass("sawgrass", 0);
	public static final Block GLOOM_GRASS = grass("gloom_grass", 0);
	public static final Block CLIFF_TUFT = grass("cliff_tuft", 0);
	public static final Block WANO_RICE_GRASS = grass("wano_rice_grass", 0);
	public static final Block OLIVE_GRASS = grass("olive_grass", 0);
	public static final Block MANGROVE_SEDGE = grass("mangrove_sedge", 0);
	public static final Block LAB_MOSS_TUFT = grass("lab_moss_tuft", 0);

	// ---- Shrubs ----
	public static final Block DRUM_HOLLY = shrub("drum_holly");
	public static final Block DATE_SHRUB = shrub("date_shrub");
	public static final Block JUNGLE_SHRUB = shrub("jungle_shrub");
	public static final Block CLOUD_SHRUB = shrub("cloud_shrub");
	public static final Block THORN_BRAMBLE = shrub("thorn_bramble");
	public static final Block WANO_AZALEA = shrub("wano_azalea");
	public static final Block GUMDROP_BUSH = shrub("gumdrop_bush");
	public static final Block OLIVE_SHRUB = shrub("olive_shrub");
	public static final Block SEA_GRAPE_SHRUB = shrub("sea_grape_shrub");
	public static final Block CINDER_BUSH = shrub("cinder_bush");
	public static final Block FROSTBERRY_BUSH = shrub("frostberry_bush");
	public static final Block RESIN_SHRUB = shrub("resin_shrub");
	public static final Block EGGHEAD_HEDGE = shrub("egghead_hedge");
	public static final Block RED_LINE_SCRUB = shrub("red_line_scrub");

	// ---- Ground cover (1 to 4 segments per block, like pink petals) ----
	public static final Block ORANGE_BLOSSOM_PETALS = cover("orange_blossom_petals", 0);
	public static final Block HARBOR_MOSS = cover("harbor_moss", 0);
	public static final Block FROST_MOSS = cover("frost_moss", 0);
	public static final Block FERN_LITTER = cover("fern_litter", 0);
	public static final Block COBWEB_MOSS = cover("cobweb_moss", 0);
	public static final Block FALLEN_LEAVES = cover("fallen_leaves", 0);
	public static final Block WHITE_CLOVER = cover("white_clover", 0);
	public static final Block ZUNESHA_MOSS = cover("zunesha_moss", 0);
	public static final Block PYTHON_IVY = cover("python_ivy", 0);
	public static final Block CHOCOLATE_MOSS = cover("chocolate_moss", 0);
	public static final Block SUGAR_FROST = cover("sugar_frost", 0);
	public static final Block LAB_LICHEN = cover("lab_lichen", 6);
	public static final Block RUIN_MOSS = cover("ruin_moss", 0);
	public static final Block EMBER_ASH = cover("ember_ash", 3);
	public static final Block ROYAL_IVY = cover("royal_ivy", 0);
	public static final Block CLOUD_MOSS = cover("cloud_moss", 0);
	public static final Block BUBBLE_LICHEN = cover("bubble_lichen", 2);
	public static final Block DUNE_SCRUB = cover("dune_scrub", 0);
	public static final Block TATAMI_RUSH = cover("tatami_rush", 0);
	public static final Block GIANT_CLOVER_PATCH = cover("giant_clover_patch", 0);

	// ---- Island grounds (placed by the Grand Line surface rules, tools/islands/island_flavour.py) ----
	public static final Block SUGAR_SAND = cube("sugar_sand", Blocks.SAND);
	public static final Block BLACK_SAND = cube("black_sand", Blocks.SAND);
	public static final Block VOLCANIC_ASH = cube("volcanic_ash", Blocks.COARSE_DIRT);
	public static final Block GRAVE_SOIL = cube("grave_soil", Blocks.COARSE_DIRT);
	public static final Block JUNGLE_LOAM = cube("jungle_loam", Blocks.DIRT);
	public static final Block PERMAFROST = cube("permafrost", Blocks.COARSE_DIRT);

	public static void initialize() {
		// Blocks register when this class loads.
	}

	// ---------------------------------------------------------------- helpers

	private static Block flower(String name, Holder<MobEffect> stewEffect, float seconds, int light) {
		return register(name, properties -> new FloraPlants.Flower(stewEffect, seconds, properties),
				BlockBehaviour.Properties.ofFullCopy(Blocks.POPPY).lightLevel(state -> light));
	}

	private static Block tall(String name, int light) {
		return registerTall(name, FloraPlants.Tall::new, BlockBehaviour.Properties.ofFullCopy(Blocks.ROSE_BUSH).lightLevel(state -> light));
	}

	private static Block grass(String name, int light) {
		return register(name, FloraPlants.Grass::new, BlockBehaviour.Properties.ofFullCopy(Blocks.SHORT_GRASS).lightLevel(state -> light));
	}

	private static Block shrub(String name) {
		return register(name, FloraPlants.Shrub::new, BlockBehaviour.Properties.ofFullCopy(Blocks.BUSH));
	}

	private static Block cover(String name, int light) {
		return register(name, FloraPlants.Cover::new, BlockBehaviour.Properties.ofFullCopy(Blocks.PINK_PETALS).lightLevel(state -> light));
	}

	private static Block cube(String name, Block copy) {
		return register(name, Block::new, BlockBehaviour.Properties.ofFullCopy(copy));
	}

	/** Registers a block and the item you hold to place it. */
	private static Block register(String name, Function<BlockBehaviour.Properties, Block> factory, BlockBehaviour.Properties properties) {
		Block block = registerBlockOnly(name, factory, properties);
		registerItem(name, itemProperties -> new BlockItem(block, itemProperties));
		return block;
	}

	/** Two-block plants use an item that places both halves. */
	private static Block registerTall(String name, Function<BlockBehaviour.Properties, Block> factory, BlockBehaviour.Properties properties) {
		Block block = registerBlockOnly(name, factory, properties);
		registerItem(name, itemProperties -> new DoubleHighBlockItem(block, itemProperties));
		return block;
	}

	private static Block registerBlockOnly(String name, Function<BlockBehaviour.Properties, Block> factory, BlockBehaviour.Properties properties) {
		ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, OnePieceMod.id(name));
		return Registry.register(BuiltInRegistries.BLOCK, key, factory.apply(properties.setId(key)));
	}

	private static void registerItem(String name, Function<Item.Properties, Item> factory) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Registry.register(BuiltInRegistries.ITEM, key, factory.apply(new Item.Properties().useBlockDescriptionPrefix().setId(key)));
	}
}
