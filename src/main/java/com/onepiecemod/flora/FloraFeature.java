package com.onepiecemod.flora;

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
 * Island flora: flowers, tall plants, grass, shrubs, ground cover and soils for every Grand Line island.
 * OnePieceMod calls initialize() once.
 *
 * Each plant is added to its biomes by tag: data/onepiece/tags/worldgen/biome/has_flora_<plant>.json lists the
 * biomes it grows in, so where things grow can change without touching code. The soils are placed by the Grand Line
 * surface rules instead (tools/islands/island_flavour.py). This file is made by tools/flora/gen_flora.py.
 */
public class FloraFeature {
	public static final ResourceKey<CreativeModeTab> TAB_KEY = ResourceKey.create(
			BuiltInRegistries.CREATIVE_MODE_TAB.key(), OnePieceMod.id("flora"));

	public static void initialize() {
		FloraBlocks.initialize();

		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY, FabricCreativeModeTab.builder()
				.icon(() -> new ItemStack(FloraBlocks.DAWN_POPPY))
				.title(Component.translatable("itemGroup.onepiece.flora"))
				.displayItems((params, output) -> {
					output.accept(FloraBlocks.DAWN_POPPY);
					output.accept(FloraBlocks.SEA_PINK);
					output.accept(FloraBlocks.MARINE_ROSE);
					output.accept(FloraBlocks.TOY_TULIP);
					output.accept(FloraBlocks.JAYA_HIBISCUS);
					output.accept(FloraBlocks.WINTER_ROSE);
					output.accept(FloraBlocks.WANO_IRIS);
					output.accept(FloraBlocks.KIKU_CHRYSANTHEMUM);
					output.accept(FloraBlocks.JUSTICE_LILY);
					output.accept(FloraBlocks.KUJA_ORCHID);
					output.accept(FloraBlocks.CACAO_BLOSSOM);
					output.accept(FloraBlocks.GRAVE_LILY);
					output.accept(FloraBlocks.HOLO_FLOWER);
					output.accept(FloraBlocks.SKULL_LILY);
					output.accept(FloraBlocks.CINDER_POPPY);
					output.accept(FloraBlocks.VALLEY_BLOOM);
					output.accept(FloraBlocks.TONTATTA_CLOVER);
					output.accept(FloraBlocks.SKY_BELL);
					output.accept(FloraBlocks.GIANTS_CLOVER);
					output.accept(FloraBlocks.ZUNESHA_BLOSSOM);
					output.accept(FloraBlocks.SAND_ROSE);
					output.accept(FloraBlocks.CLIFF_EDELWEISS);
					output.accept(FloraBlocks.SABAODY_BUBBLE_BLOOM);
					output.accept(FloraBlocks.FROST_THISTLE_BLOOM);
					output.accept(FloraBlocks.SEA_LAVENDER);
					output.accept(FloraBlocks.DESERT_THISTLE);
					output.accept(FloraBlocks.SOUTH_BIRD_FERN);
					output.accept(FloraBlocks.PRIMEVAL_BLOSSOM);
					output.accept(FloraBlocks.WITHERED_BRAMBLE);
					output.accept(FloraBlocks.KURI_PAMPAS);
					output.accept(FloraBlocks.ICE_THISTLE);
					output.accept(FloraBlocks.CINDER_SHRUB);
					output.accept(FloraBlocks.GIANT_BARLEY);
					output.accept(FloraBlocks.MINK_FERN);
					output.accept(FloraBlocks.PASSION_ROSE);
					output.accept(FloraBlocks.CANDY_SHRUB);
					output.accept(FloraBlocks.ONI_THISTLE);
					output.accept(FloraBlocks.PIRATE_BRAMBLE);
					output.accept(FloraBlocks.KURAIGANA_THISTLE);
					output.accept(FloraBlocks.CELESTIAL_LILY);
					output.accept(FloraBlocks.CLIFF_THISTLE);
					output.accept(FloraBlocks.UPPER_YARD_REED);
					output.accept(FloraBlocks.MANGROVE_REED);
					output.accept(FloraBlocks.NEON_FERN);
					output.accept(FloraBlocks.FROST_FERN);
					output.accept(FloraBlocks.SAND_SAGE);
					output.accept(FloraBlocks.HEAVEN_GRASS);
					output.accept(FloraBlocks.DINO_FERN);
					output.accept(FloraBlocks.EMBER_GRASS);
					output.accept(FloraBlocks.WAFER_GRASS);
					output.accept(FloraBlocks.ASH_GRASS);
					output.accept(FloraBlocks.CELESTIAL_GRASS);
					output.accept(FloraBlocks.HARBOR_SEDGE);
					output.accept(FloraBlocks.SAWGRASS);
					output.accept(FloraBlocks.GLOOM_GRASS);
					output.accept(FloraBlocks.CLIFF_TUFT);
					output.accept(FloraBlocks.WANO_RICE_GRASS);
					output.accept(FloraBlocks.OLIVE_GRASS);
					output.accept(FloraBlocks.MANGROVE_SEDGE);
					output.accept(FloraBlocks.LAB_MOSS_TUFT);
					output.accept(FloraBlocks.DRUM_HOLLY);
					output.accept(FloraBlocks.DATE_SHRUB);
					output.accept(FloraBlocks.JUNGLE_SHRUB);
					output.accept(FloraBlocks.CLOUD_SHRUB);
					output.accept(FloraBlocks.THORN_BRAMBLE);
					output.accept(FloraBlocks.WANO_AZALEA);
					output.accept(FloraBlocks.GUMDROP_BUSH);
					output.accept(FloraBlocks.OLIVE_SHRUB);
					output.accept(FloraBlocks.SEA_GRAPE_SHRUB);
					output.accept(FloraBlocks.CINDER_BUSH);
					output.accept(FloraBlocks.FROSTBERRY_BUSH);
					output.accept(FloraBlocks.RESIN_SHRUB);
					output.accept(FloraBlocks.EGGHEAD_HEDGE);
					output.accept(FloraBlocks.RED_LINE_SCRUB);
					output.accept(FloraBlocks.ORANGE_BLOSSOM_PETALS);
					output.accept(FloraBlocks.HARBOR_MOSS);
					output.accept(FloraBlocks.FROST_MOSS);
					output.accept(FloraBlocks.FERN_LITTER);
					output.accept(FloraBlocks.COBWEB_MOSS);
					output.accept(FloraBlocks.FALLEN_LEAVES);
					output.accept(FloraBlocks.WHITE_CLOVER);
					output.accept(FloraBlocks.ZUNESHA_MOSS);
					output.accept(FloraBlocks.PYTHON_IVY);
					output.accept(FloraBlocks.CHOCOLATE_MOSS);
					output.accept(FloraBlocks.SUGAR_FROST);
					output.accept(FloraBlocks.LAB_LICHEN);
					output.accept(FloraBlocks.RUIN_MOSS);
					output.accept(FloraBlocks.EMBER_ASH);
					output.accept(FloraBlocks.ROYAL_IVY);
					output.accept(FloraBlocks.CLOUD_MOSS);
					output.accept(FloraBlocks.BUBBLE_LICHEN);
					output.accept(FloraBlocks.DUNE_SCRUB);
					output.accept(FloraBlocks.TATAMI_RUSH);
					output.accept(FloraBlocks.GIANT_CLOVER_PATCH);
					output.accept(FloraBlocks.SUGAR_SAND);
					output.accept(FloraBlocks.BLACK_SAND);
					output.accept(FloraBlocks.VOLCANIC_ASH);
					output.accept(FloraBlocks.GRAVE_SOIL);
					output.accept(FloraBlocks.JUNGLE_LOAM);
					output.accept(FloraBlocks.PERMAFROST);
				})
				.build());

		addVegetation("dawn_poppy");
		addVegetation("sea_pink");
		addVegetation("marine_rose");
		addVegetation("toy_tulip");
		addVegetation("jaya_hibiscus");
		addVegetation("winter_rose");
		addVegetation("wano_iris");
		addVegetation("kiku_chrysanthemum");
		addVegetation("justice_lily");
		addVegetation("kuja_orchid");
		addVegetation("cacao_blossom");
		addVegetation("grave_lily");
		addVegetation("holo_flower");
		addVegetation("skull_lily");
		addVegetation("cinder_poppy");
		addVegetation("valley_bloom");
		addVegetation("tontatta_clover");
		addVegetation("sky_bell");
		addVegetation("giants_clover");
		addVegetation("zunesha_blossom");
		addVegetation("sand_rose");
		addVegetation("cliff_edelweiss");
		addVegetation("sabaody_bubble_bloom");
		addVegetation("frost_thistle_bloom");
		addVegetation("sea_lavender");
		addVegetation("desert_thistle");
		addVegetation("south_bird_fern");
		addVegetation("primeval_blossom");
		addVegetation("withered_bramble");
		addVegetation("kuri_pampas");
		addVegetation("ice_thistle");
		addVegetation("cinder_shrub");
		addVegetation("giant_barley");
		addVegetation("mink_fern");
		addVegetation("passion_rose");
		addVegetation("candy_shrub");
		addVegetation("oni_thistle");
		addVegetation("pirate_bramble");
		addVegetation("kuraigana_thistle");
		addVegetation("celestial_lily");
		addVegetation("cliff_thistle");
		addVegetation("upper_yard_reed");
		addVegetation("mangrove_reed");
		addVegetation("neon_fern");
		addVegetation("frost_fern");
		addVegetation("sand_sage");
		addVegetation("heaven_grass");
		addVegetation("dino_fern");
		addVegetation("ember_grass");
		addVegetation("wafer_grass");
		addVegetation("ash_grass");
		addVegetation("celestial_grass");
		addVegetation("harbor_sedge");
		addVegetation("sawgrass");
		addVegetation("gloom_grass");
		addVegetation("cliff_tuft");
		addVegetation("wano_rice_grass");
		addVegetation("olive_grass");
		addVegetation("mangrove_sedge");
		addVegetation("lab_moss_tuft");
		addVegetation("drum_holly");
		addVegetation("date_shrub");
		addVegetation("jungle_shrub");
		addVegetation("cloud_shrub");
		addVegetation("thorn_bramble");
		addVegetation("wano_azalea");
		addVegetation("gumdrop_bush");
		addVegetation("olive_shrub");
		addVegetation("sea_grape_shrub");
		addVegetation("cinder_bush");
		addVegetation("frostberry_bush");
		addVegetation("resin_shrub");
		addVegetation("egghead_hedge");
		addVegetation("red_line_scrub");
		addVegetation("orange_blossom_petals");
		addVegetation("harbor_moss");
		addVegetation("frost_moss");
		addVegetation("fern_litter");
		addVegetation("cobweb_moss");
		addVegetation("fallen_leaves");
		addVegetation("white_clover");
		addVegetation("zunesha_moss");
		addVegetation("python_ivy");
		addVegetation("chocolate_moss");
		addVegetation("sugar_frost");
		addVegetation("lab_lichen");
		addVegetation("ruin_moss");
		addVegetation("ember_ash");
		addVegetation("royal_ivy");
		addVegetation("cloud_moss");
		addVegetation("bubble_lichen");
		addVegetation("dune_scrub");
		addVegetation("tatami_rush");
		addVegetation("giant_clover_patch");
	}

	private static void addVegetation(String plant) {
		TagKey<Biome> tag = TagKey.create(Registries.BIOME, OnePieceMod.id("has_flora_" + plant));
		ResourceKey<PlacedFeature> feature = ResourceKey.create(Registries.PLACED_FEATURE, OnePieceMod.id("flora_" + plant));
		BiomeModifications.addFeature(BiomeSelectors.tag(tag), GenerationStep.Decoration.VEGETAL_DECORATION, feature);
	}
}
