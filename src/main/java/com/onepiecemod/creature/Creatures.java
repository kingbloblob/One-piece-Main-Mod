package com.onepiecemod.creature;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.tags.FluidTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.SpawnPlacementTypes;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.levelgen.Heightmap;

import net.fabricmc.fabric.api.biome.v1.BiomeModifications;
import net.fabricmc.fabric.api.biome.v1.BiomeSelectors;
import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricEntityType;

import com.onepiecemod.OnePieceMod;

/**
 * Registers every One Piece creature, its spawn egg, and where it spawns in the world.
 * OnePieceMod calls initialize() once at startup.
 *
 * Spawning uses biome tags, so the creatures show up both in normal Minecraft worlds (deserts, jungles,
 * snowy plains, oceans...) and on the Grand Line islands. Each creature's list is in
 * data/onepiece/tags/worldgen/biome/spawns/<id>.json, so you can change where it lives without touching code.
 */
public final class Creatures {
	private static final Map<EntityType<?>, CreatureSpecies> SPECIES_BY_TYPE = new HashMap<>();
	public static final Map<String, EntityType<CreatureEntity>> TYPES = new LinkedHashMap<>();
	private static final List<Item> EGGS = new ArrayList<>();

	public static final ResourceKey<CreativeModeTab> TAB_KEY = ResourceKey.create(
			BuiltInRegistries.CREATIVE_MODE_TAB.key(), OnePieceMod.id("creatures"));

	private Creatures() {
	}

	public static CreatureSpecies speciesOf(EntityType<?> type) {
		return SPECIES_BY_TYPE.get(type);
	}

	public static void initialize() {
		for (CreatureSpecies species : CreatureSpecies.ALL) {
			EntityType<CreatureEntity> type = register(species);
			SPECIES_BY_TYPE.put(type, species);
			TYPES.put(species.id(), type);

			TagKey<Biome> biomes = TagKey.create(Registries.BIOME, OnePieceMod.id("spawns/" + species.id()));
			BiomeModifications.addSpawn(BiomeSelectors.tag(biomes), species.category(), type,
					species.spawnWeight(), species.minGroup(), species.maxGroup());

			EGGS.add(registerEgg(species, type));
		}
		com.onepiecemod.pet.Pets.initialize();

		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY, FabricCreativeModeTab.builder()
				.icon(() -> new ItemStack(EGGS.get(0)))
				.title(Component.literal("One Piece: Creatures"))
				.displayItems((params, output) -> {
					output.accept(com.onepiecemod.pet.Pets.PET_WHISTLE);
					output.accept(com.onepiecemod.pet.Pets.TOWING_HARNESS);
					EGGS.forEach(output::accept);
				})
				.build());
	}

	private static EntityType<CreatureEntity> register(CreatureSpecies species) {
		ResourceKey<EntityType<?>> key = ResourceKey.create(Registries.ENTITY_TYPE, OnePieceMod.id(species.id()));
		EntityType.Builder<CreatureEntity> builder = FabricEntityType.Builder.createMob(CreatureEntity::new, species.category(), mob -> mob
				.spawnPlacement(
						species.swims() ? SpawnPlacementTypes.IN_WATER : SpawnPlacementTypes.ON_GROUND,
						species.swims() ? Heightmap.Types.OCEAN_FLOOR : Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
						spawnRule(species))
				.defaultAttributes(() -> CreatureEntity.createAttributes(species)));
		builder.sized(species.width(), species.height()).clientTrackingRange(10);
		if (species.underground() && species.fireSeconds() > 0) {
			builder.fireImmune(); // lives next to magma and sulfur vents
		}
		return Registry.register(BuiltInRegistries.ENTITY_TYPE, key, builder.build(key));
	}

	/** Where a creature is allowed to appear when Minecraft tries to spawn it naturally. */
	private static net.minecraft.world.entity.SpawnPlacements.SpawnPredicate<CreatureEntity> spawnRule(CreatureSpecies species) {
		boolean hostile = species.behavior() == CreatureSpecies.Behavior.HOSTILE;
		if (species.underground()) {
			// Cave creatures: below the open sky only, between their heights; hunters also need darkness.
			return (type, level, reason, pos, random) ->
					pos.getY() >= species.caveMinY() && pos.getY() <= species.caveMaxY()
							&& !level.canSeeSky(pos)
							&& (!hostile || (level.getDifficulty() != Difficulty.PEACEFUL && Monster.isDarkEnoughToSpawn(level, pos, random)))
							&& Mob.checkMobSpawnRules(type, level, reason, pos, random);
		}
		if (species.swims()) {
			// In water, with water above too, so fish don't spawn in puddles.
			return (type, level, reason, pos, random) ->
					(!hostile || level.getDifficulty() != Difficulty.PEACEFUL)
							&& level.getFluidState(pos).is(FluidTags.WATER)
							&& level.getFluidState(pos.above()).is(FluidTags.WATER);
		}
		if (hostile) {
			// Night creatures need darkness, like zombies. Day creatures (desert and snow beasts) don't.
			return (type, level, reason, pos, random) ->
					level.getDifficulty() != Difficulty.PEACEFUL
							&& (species.dayActive() || Monster.isDarkEnoughToSpawn(level, pos, random))
							&& Mob.checkMobSpawnRules(type, level, reason, pos, random);
		}
		// Animals spawn on solid ground in daylight.
		return (type, level, reason, pos, random) ->
				level.getRawBrightness(pos, 0) > 8 && Mob.checkMobSpawnRules(type, level, reason, pos, random);
	}

	private static Item registerEgg(CreatureSpecies species, EntityType<CreatureEntity> type) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(species.id() + "_spawn_egg"));
		Item egg = new CreatureEggItem(type, new Item.Properties().setId(key));
		return Registry.register(BuiltInRegistries.ITEM, key, egg);
	}
}
