package com.onepiecemod.fx;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentSyncPredicate;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.haki.HakiPowers;

/**
 * Registers the move effect entity, and tells every player's game whose arms are coated in
 * Armament Haki so they can be drawn black. OnePieceMod calls initialize().
 */
public class FxFeature {
	public static final ResourceKey<EntityType<?>> MOVE_EFFECT_KEY = ResourceKey.create(Registries.ENTITY_TYPE, OnePieceMod.id("move_effect"));

	public static final EntityType<MoveEffectEntity> MOVE_EFFECT = Registry.register(
			BuiltInRegistries.ENTITY_TYPE,
			MOVE_EFFECT_KEY,
			EntityType.Builder.<MoveEffectEntity>of(MoveEffectEntity::new, MobCategory.MISC)
					.sized(0.25f, 0.25f)
					.noSave()
					.noSummon()
					.fireImmune()
					.clientTrackingRange(6)
					.updateInterval(20) // It never moves, so it hardly needs updates.
					.build(MOVE_EFFECT_KEY)
	);

	/**
	 * True while a player has Armament Haki switched on. Only for drawing: the real Haki data lives in
	 * HakiAttachments and stays on the server. Not saved, it is worked out again every second.
	 */
	public static final AttachmentType<Boolean> ARMAMENT_VISIBLE = AttachmentRegistry.create(
			OnePieceMod.id("armament_visible"),
			builder -> builder.syncWith(ByteBufCodecs.BOOL, AttachmentSyncPredicate.all())
	);

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 10 != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				boolean on = HakiPowers.hasArmamentActive(player);
				if (on != armamentVisible(player)) {
					if (on) {
						player.setAttached(ARMAMENT_VISIBLE, true);
					} else {
						player.removeAttached(ARMAMENT_VISIBLE);
					}
				}
			}
		});
	}

	public static boolean armamentVisible(Entity entity) {
		return Boolean.TRUE.equals(entity.getAttached(ARMAMENT_VISIBLE));
	}
}
