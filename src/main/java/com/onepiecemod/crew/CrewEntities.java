package com.onepiecemod.crew;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;

import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;

import com.onepiecemod.OnePieceMod;

/**
 * Registers the crewmate mob so Minecraft knows it exists.
 */
public class CrewEntities {
	public static final ResourceKey<EntityType<?>> CREWMATE_KEY = ResourceKey.create(Registries.ENTITY_TYPE, OnePieceMod.id("crewmate"));

	public static final EntityType<CrewmateEntity> CREWMATE = Registry.register(
			BuiltInRegistries.ENTITY_TYPE,
			CREWMATE_KEY,
			EntityType.Builder.of(CrewmateEntity::new, MobCategory.CREATURE)
					.sized(0.6f, 1.8f) // Same size as a player.
					.eyeHeight(1.62f)
					.clientTrackingRange(10)
					.build(CREWMATE_KEY)
	);

	public static void initialize() {
		// Health, speed and damage. Each role changes some of these when hired.
		FabricDefaultAttributeRegistry.register(CREWMATE, CrewmateEntity.createAttributes());
	}
}
