package com.onepiecemod.sea;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;

import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;

import com.onepiecemod.OnePieceMod;

/**
 * Registers the Sea King so Minecraft knows it exists.
 */
public class SeaEntities {
	public static final ResourceKey<EntityType<?>> SEA_KING_KEY = ResourceKey.create(Registries.ENTITY_TYPE, OnePieceMod.id("sea_king"));

	public static final EntityType<SeaKingEntity> SEA_KING = Registry.register(
			BuiltInRegistries.ENTITY_TYPE,
			SEA_KING_KEY,
			EntityType.Builder.of(SeaKingEntity::new, MobCategory.MONSTER)
					// Show-sized (2026-11-06): the head is about 9 blocks across and the whole body about 75 blocks long,
					// twice the Going Merry. The hitbox covers the head; the long body behind it is only for show
					// (a body-sized hitbox would make swimming and pathfinding far too slow).
					.sized(8.0f, 7.5f)
					.eyeHeight(5.0f)
					.clientTrackingRange(16) // Seen from far away, it's huge.
					.build(SEA_KING_KEY)
	);

	public static void initialize() {
		FabricDefaultAttributeRegistry.register(SEA_KING, SeaKingEntity.createAttributes());
	}
}
