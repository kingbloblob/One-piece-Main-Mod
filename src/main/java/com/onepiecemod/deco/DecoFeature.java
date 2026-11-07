package com.onepiecemod.deco;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.levelgen.GenerationStep;
import net.minecraft.world.level.levelgen.placement.PlacedFeature;

import net.fabricmc.fabric.api.biome.v1.BiomeModifications;
import net.fabricmc.fabric.api.biome.v1.BiomeSelectors;
import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;

import com.onepiecemod.OnePieceMod;

/**
 * Island building blocks, trees, flowers and snacks. OnePieceMod calls initialize() once.
 *
 * Trees and flowers are added to biomes by tag: data/onepiece/tags/worldgen/biome/has_deco_*.json
 * lists the biomes each one grows in, so you can change where things grow without touching code.
 * This file is made by tools/deco/gen_deco.py.
 */
public class DecoFeature {
	public static final ResourceKey<CreativeModeTab> TAB_KEY = ResourceKey.create(
			BuiltInRegistries.CREATIVE_MODE_TAB.key(), OnePieceMod.id("deco"));

	public static void initialize() {
		DecoBlocks.initialize();
		DecoItems.initialize();

		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY, FabricCreativeModeTab.builder()
				.icon(() -> new ItemStack(DecoBlocks.SAKURA_SAPLING))
				.title(Component.translatable("itemGroup.onepiece.deco"))
				.displayItems((params, output) -> {
					output.accept(DecoBlocks.SAKURA_LOG);
					output.accept(DecoBlocks.SAKURA_WOOD);
					output.accept(DecoBlocks.STRIPPED_SAKURA_LOG);
					output.accept(DecoBlocks.STRIPPED_SAKURA_WOOD);
					output.accept(DecoBlocks.SAKURA_PLANKS);
					output.accept(DecoBlocks.SAKURA_STAIRS);
					output.accept(DecoBlocks.SAKURA_SLAB);
					output.accept(DecoBlocks.SAKURA_FENCE);
					output.accept(DecoBlocks.SAKURA_FENCE_GATE);
					output.accept(DecoBlocks.SAKURA_DOOR);
					output.accept(DecoBlocks.SAKURA_TRAPDOOR);
					output.accept(DecoBlocks.SAKURA_BUTTON);
					output.accept(DecoBlocks.SAKURA_PRESSURE_PLATE);
					output.accept(DecoBlocks.SAKURA_LEAVES);
					output.accept(DecoBlocks.SAKURA_SAPLING);
					output.accept(DecoBlocks.YARUKIMAN_LOG);
					output.accept(DecoBlocks.YARUKIMAN_WOOD);
					output.accept(DecoBlocks.STRIPPED_YARUKIMAN_LOG);
					output.accept(DecoBlocks.STRIPPED_YARUKIMAN_WOOD);
					output.accept(DecoBlocks.YARUKIMAN_PLANKS);
					output.accept(DecoBlocks.YARUKIMAN_STAIRS);
					output.accept(DecoBlocks.YARUKIMAN_SLAB);
					output.accept(DecoBlocks.YARUKIMAN_FENCE);
					output.accept(DecoBlocks.YARUKIMAN_FENCE_GATE);
					output.accept(DecoBlocks.YARUKIMAN_DOOR);
					output.accept(DecoBlocks.YARUKIMAN_TRAPDOOR);
					output.accept(DecoBlocks.YARUKIMAN_BUTTON);
					output.accept(DecoBlocks.YARUKIMAN_PRESSURE_PLATE);
					output.accept(DecoBlocks.YARUKIMAN_LEAVES);
					output.accept(DecoBlocks.YARUKIMAN_SAPLING);
					output.accept(DecoBlocks.PALM_LOG);
					output.accept(DecoBlocks.PALM_WOOD);
					output.accept(DecoBlocks.STRIPPED_PALM_LOG);
					output.accept(DecoBlocks.STRIPPED_PALM_WOOD);
					output.accept(DecoBlocks.PALM_PLANKS);
					output.accept(DecoBlocks.PALM_STAIRS);
					output.accept(DecoBlocks.PALM_SLAB);
					output.accept(DecoBlocks.PALM_FENCE);
					output.accept(DecoBlocks.PALM_FENCE_GATE);
					output.accept(DecoBlocks.PALM_DOOR);
					output.accept(DecoBlocks.PALM_TRAPDOOR);
					output.accept(DecoBlocks.PALM_BUTTON);
					output.accept(DecoBlocks.PALM_PRESSURE_PLATE);
					output.accept(DecoBlocks.PALM_LEAVES);
					output.accept(DecoBlocks.PALM_SAPLING);
					output.accept(DecoBlocks.GLOOM_LOG);
					output.accept(DecoBlocks.GLOOM_WOOD);
					output.accept(DecoBlocks.STRIPPED_GLOOM_LOG);
					output.accept(DecoBlocks.STRIPPED_GLOOM_WOOD);
					output.accept(DecoBlocks.GLOOM_PLANKS);
					output.accept(DecoBlocks.GLOOM_STAIRS);
					output.accept(DecoBlocks.GLOOM_SLAB);
					output.accept(DecoBlocks.GLOOM_FENCE);
					output.accept(DecoBlocks.GLOOM_FENCE_GATE);
					output.accept(DecoBlocks.GLOOM_DOOR);
					output.accept(DecoBlocks.GLOOM_TRAPDOOR);
					output.accept(DecoBlocks.GLOOM_BUTTON);
					output.accept(DecoBlocks.GLOOM_PRESSURE_PLATE);
					output.accept(DecoBlocks.GLOOM_LEAVES);
					output.accept(DecoBlocks.GLOOM_SAPLING);
					output.accept(DecoBlocks.ADAM_STAIRS);
					output.accept(DecoBlocks.ADAM_SLAB);
					output.accept(DecoBlocks.ADAM_FENCE);
					output.accept(DecoBlocks.ADAM_FENCE_GATE);
					output.accept(DecoBlocks.ADAM_DOOR);
					output.accept(DecoBlocks.ADAM_TRAPDOOR);
					output.accept(DecoBlocks.ADAM_BUTTON);
					output.accept(DecoBlocks.ADAM_PRESSURE_PLATE);
					output.accept(DecoBlocks.ALABASTA_SANDSTONE_BRICKS);
					output.accept(DecoBlocks.ALABASTA_SANDSTONE_BRICK_STAIRS);
					output.accept(DecoBlocks.ALABASTA_SANDSTONE_BRICK_SLAB);
					output.accept(DecoBlocks.ALABASTA_SANDSTONE_BRICK_WALL);
					output.accept(DecoBlocks.ALABASTA_TILES);
					output.accept(DecoBlocks.ALABASTA_TILE_STAIRS);
					output.accept(DecoBlocks.ALABASTA_TILE_SLAB);
					output.accept(DecoBlocks.WANO_ROOF_TILES);
					output.accept(DecoBlocks.WANO_ROOF_TILE_STAIRS);
					output.accept(DecoBlocks.WANO_ROOF_TILE_SLAB);
					output.accept(DecoBlocks.WANO_LACQUER_PLANKS);
					output.accept(DecoBlocks.WANO_LACQUER_STAIRS);
					output.accept(DecoBlocks.WANO_LACQUER_SLAB);
					output.accept(DecoBlocks.MARINE_BRICKS);
					output.accept(DecoBlocks.MARINE_BRICK_STAIRS);
					output.accept(DecoBlocks.MARINE_BRICK_SLAB);
					output.accept(DecoBlocks.MARINE_BRICK_WALL);
					output.accept(DecoBlocks.MARINE_TILES);
					output.accept(DecoBlocks.MARINE_TILE_STAIRS);
					output.accept(DecoBlocks.MARINE_TILE_SLAB);
					output.accept(DecoBlocks.CANAL_BRICKS);
					output.accept(DecoBlocks.CANAL_BRICK_STAIRS);
					output.accept(DecoBlocks.CANAL_BRICK_SLAB);
					output.accept(DecoBlocks.CANAL_BRICK_WALL);
					output.accept(DecoBlocks.WATER7_COBBLES);
					output.accept(DecoBlocks.WATER7_COBBLE_STAIRS);
					output.accept(DecoBlocks.WATER7_COBBLE_SLAB);
					output.accept(DecoBlocks.WATER7_COBBLE_WALL);
					output.accept(DecoBlocks.DRESSROSA_MOSAIC);
					output.accept(DecoBlocks.DRESSROSA_MOSAIC_STAIRS);
					output.accept(DecoBlocks.DRESSROSA_MOSAIC_SLAB);
					output.accept(DecoBlocks.DRESSROSA_TILES);
					output.accept(DecoBlocks.DRESSROSA_TILE_STAIRS);
					output.accept(DecoBlocks.DRESSROSA_TILE_SLAB);
					output.accept(DecoBlocks.DRESSROSA_STUCCO);
					output.accept(DecoBlocks.DRESSROSA_STUCCO_STAIRS);
					output.accept(DecoBlocks.DRESSROSA_STUCCO_SLAB);
					output.accept(DecoBlocks.DRESSROSA_STUCCO_WALL);
					output.accept(DecoBlocks.CORAL_BRICKS);
					output.accept(DecoBlocks.CORAL_BRICK_STAIRS);
					output.accept(DecoBlocks.CORAL_BRICK_SLAB);
					output.accept(DecoBlocks.CORAL_BRICK_WALL);
					output.accept(DecoBlocks.PEARL_BLOCK);
					output.accept(DecoBlocks.PEARL_STAIRS);
					output.accept(DecoBlocks.PEARL_SLAB);
					output.accept(DecoBlocks.CLOUD_BRICKS);
					output.accept(DecoBlocks.CLOUD_BRICK_STAIRS);
					output.accept(DecoBlocks.CLOUD_BRICK_SLAB);
					output.accept(DecoBlocks.SHANDORA_GOLD_BRICKS);
					output.accept(DecoBlocks.SHANDORA_GOLD_BRICK_STAIRS);
					output.accept(DecoBlocks.SHANDORA_GOLD_BRICK_SLAB);
					output.accept(DecoBlocks.SHANDORA_GOLD_BRICK_WALL);
					output.accept(DecoBlocks.SHANDIAN_RUIN_STONE);
					output.accept(DecoBlocks.SHANDIAN_RUIN_STONE_STAIRS);
					output.accept(DecoBlocks.SHANDIAN_RUIN_STONE_SLAB);
					output.accept(DecoBlocks.SHANDIAN_RUIN_STONE_WALL);
					output.accept(DecoBlocks.SNOW_BRICKS);
					output.accept(DecoBlocks.SNOW_BRICK_STAIRS);
					output.accept(DecoBlocks.SNOW_BRICK_SLAB);
					output.accept(DecoBlocks.SNOW_BRICK_WALL);
					output.accept(DecoBlocks.FROZEN_STONE);
					output.accept(DecoBlocks.FROZEN_STONE_STAIRS);
					output.accept(DecoBlocks.FROZEN_STONE_SLAB);
					output.accept(DecoBlocks.FROZEN_STONE_WALL);
					output.accept(DecoBlocks.SCORCHED_STONE);
					output.accept(DecoBlocks.SCORCHED_STONE_STAIRS);
					output.accept(DecoBlocks.SCORCHED_STONE_SLAB);
					output.accept(DecoBlocks.SCORCHED_STONE_WALL);
					output.accept(DecoBlocks.SEASTONE_BRICKS);
					output.accept(DecoBlocks.SEASTONE_BRICK_STAIRS);
					output.accept(DecoBlocks.SEASTONE_BRICK_SLAB);
					output.accept(DecoBlocks.SEASTONE_BRICK_WALL);
					output.accept(DecoBlocks.LAB_PANEL);
					output.accept(DecoBlocks.LAB_PANEL_STAIRS);
					output.accept(DecoBlocks.LAB_PANEL_SLAB);
					output.accept(DecoBlocks.CHOCOLATE_BLOCK);
					output.accept(DecoBlocks.CHOCOLATE_STAIRS);
					output.accept(DecoBlocks.CHOCOLATE_SLAB);
					output.accept(DecoBlocks.COOKIE_BRICKS);
					output.accept(DecoBlocks.COOKIE_BRICK_STAIRS);
					output.accept(DecoBlocks.COOKIE_BRICK_SLAB);
					output.accept(DecoBlocks.COOKIE_BRICK_WALL);
					output.accept(DecoBlocks.FROSTING_BLOCK);
					output.accept(DecoBlocks.FROSTING_STAIRS);
					output.accept(DecoBlocks.FROSTING_SLAB);
					output.accept(DecoBlocks.LAB_LIGHT);
					output.accept(DecoBlocks.BERRY_BLOCK);
					output.accept(DecoBlocks.ALUBARNA_PILLAR);
					output.accept(DecoBlocks.MARINE_PILLAR);
					output.accept(DecoBlocks.CANDY_CANE_BLOCK);
					output.accept(DecoBlocks.TATAMI);
					output.accept(DecoBlocks.SAKE_BARREL);
					output.accept(DecoBlocks.COLA_CRATE);
					output.accept(DecoBlocks.MIKAN_CRATE);
					output.accept(DecoBlocks.BUBBLE_GLASS);
					output.accept(DecoBlocks.BUBBLE_GLASS_PANE);
					output.accept(DecoBlocks.SHOJI_SCREEN);
					output.accept(DecoBlocks.PRISON_BARS);
					output.accept(DecoBlocks.PAPER_LANTERN);
					output.accept(DecoBlocks.BUBBLE_LAMP);
					output.accept(DecoBlocks.CLOUD_PUFF);
					output.accept(DecoBlocks.SKY_LOTUS);
					output.accept(DecoBlocks.FIRE_LILY);
					output.accept(DecoBlocks.FROST_BLOOM);
					output.accept(DecoBlocks.SNOW_LILY);
					output.accept(DecoBlocks.GHOST_MUSHROOM);
					output.accept(DecoBlocks.DESERT_BLOOM);
					output.accept(DecoBlocks.CANDY_CANE_SPROUT);
					output.accept(DecoBlocks.LOLLIPOP_FLOWER);
					output.accept(DecoBlocks.AMAZON_FLOWER);
					output.accept(DecoBlocks.GIANT_FERN);
					output.accept(DecoBlocks.SAKURA_PETALS);
					output.accept(DecoItems.MIKAN);
					output.accept(DecoItems.COCONUT);
					output.accept(DecoItems.ONIGIRI);
					output.accept(DecoItems.DANGO);
					output.accept(DecoItems.SAKE);
					output.accept(DecoItems.COLA);
					output.accept(DecoItems.COTTON_CANDY);
					output.accept(DecoItems.BUBBLE_RESIN);
				})
				.build());

		addVegetation("has_deco_sakura_trees", "deco_sakura_trees");
		addVegetation("has_deco_yarukiman_trees", "deco_yarukiman_trees");
		addVegetation("has_deco_palm_trees", "deco_palm_trees");
		addVegetation("has_deco_gloom_trees", "deco_gloom_trees");
		addVegetation("has_deco_sakura_petals", "deco_sakura_petals");
		addVegetation("has_deco_mikan_bush", "deco_mikan_bush");
		addVegetation("has_deco_cloud_puff", "deco_cloud_puff");
		addVegetation("has_deco_sky_lotus", "deco_sky_lotus");
		addVegetation("has_deco_fire_lily", "deco_fire_lily");
		addVegetation("has_deco_frost_bloom", "deco_frost_bloom");
		addVegetation("has_deco_snow_lily", "deco_snow_lily");
		addVegetation("has_deco_ghost_mushroom", "deco_ghost_mushroom");
		addVegetation("has_deco_desert_bloom", "deco_desert_bloom");
		addVegetation("has_deco_candy_cane_sprout", "deco_candy_cane_sprout");
		addVegetation("has_deco_lollipop_flower", "deco_lollipop_flower");
		addVegetation("has_deco_amazon_flower", "deco_amazon_flower");
		addVegetation("has_deco_giant_fern", "deco_giant_fern");
	}

	private static void addVegetation(String biomeTag, String placedFeature) {
		TagKey<Biome> tag = TagKey.create(Registries.BIOME, OnePieceMod.id(biomeTag));
		ResourceKey<PlacedFeature> feature = ResourceKey.create(Registries.PLACED_FEATURE, OnePieceMod.id(placedFeature));
		BiomeModifications.addFeature(BiomeSelectors.tag(tag), GenerationStep.Decoration.VEGETAL_DECORATION, feature);
	}
}
