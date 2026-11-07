package com.onepiecemod.world;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.levelgen.GenerationStep;
import net.minecraft.world.level.levelgen.placement.PlacedFeature;

import net.fabricmc.fabric.api.biome.v1.BiomeModifications;
import net.fabricmc.fabric.api.biome.v1.BiomeSelectors;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.character.CharacterEntity;

/**
 * World generation: ores, biomes, structures and the "Grand Line" world type.
 *
 * Almost all of it is data (JSON and .nbt files) in src/main/resources/data/onepiece/worldgen
 * and data/onepiece/structure. This class only does the few things data can't do on its own.
 * OnePieceMod calls initialize() once while the game loads.
 */
public class WorldFeature {
	/**
	 * Characters placed by a structure (a Marine Base, a Pirate Camp...) carry this tag.
	 * The first time one is loaded we give it full health, its name and its weapons.
	 */
	public static final String NEW_CHARACTER_TAG = "onepiece_new_character";

	// Biome tags in data/onepiece/tags/worldgen/biome. Edit those files to change where things grow.
	private static final TagKey<Biome> HAS_SEASTONE_ORE = TagKey.create(Registries.BIOME, OnePieceMod.id("has_seastone_ore"));
	private static final TagKey<Biome> HAS_ADAM_TREE = TagKey.create(Registries.BIOME, OnePieceMod.id("has_adam_tree"));

	public static void initialize() {
		WorldBlocks.initialize();
		SeastoneEffects.initialize();
		DimensionBiomes.initialize();
		// A custom tree shape for palm trees (data/onepiece/worldgen/feature/palm_tree.json uses it).
		Registry.register(BuiltInRegistries.FEATURE_TYPE, OnePieceMod.id("palm"), PalmTreeFeature.CODEC);
		// The Grand Line world's rings (easy islands near spawn, deadly ones far away) and the matching structure placement.
		Registry.register(BuiltInRegistries.BIOME_SOURCE, OnePieceMod.id("rings"), RingBiomeSource.CODEC);
		Registry.register(BuiltInRegistries.STRUCTURE_PLACEMENT, OnePieceMod.id("ring_spread"), RingSpreadPlacement.CODEC);

		// Put Seastone ore and Adam trees into normal Minecraft biomes too (oceans and jungles),
		// so you find them in any world, not only in the Grand Line world type.
		BiomeModifications.addFeature(BiomeSelectors.tag(HAS_SEASTONE_ORE),
				GenerationStep.Decoration.UNDERGROUND_ORES, placedFeature("ore_seastone"));
		BiomeModifications.addFeature(BiomeSelectors.tag(HAS_ADAM_TREE),
				GenerationStep.Decoration.VEGETAL_DECORATION, placedFeature("adam_tree_rare"));

		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity instanceof CharacterEntity character && character.entityTags().contains(NEW_CHARACTER_TAG)) {
				character.removeTag(NEW_CHARACTER_TAG);
				character.setCharacter(character.getCharacterId(), character.isBoss());
			} else if (entity instanceof Mob mob && mob.entityTags().contains(GuardKit.GUARD_TAG)) {
				// Pirates and Marines become the mod's own NPCs (com.onepiecemod.npc); everyone else gets vanilla gear.
				if (!com.onepiecemod.npc.NpcFeature.claimGuard(mob, level)) {
					GuardKit.applyFromTags(mob);
				}
			}
		});
	}

	private static ResourceKey<PlacedFeature> placedFeature(String name) {
		return ResourceKey.create(Registries.PLACED_FEATURE, OnePieceMod.id(name));
	}
}
