package com.onepiecemod.seatrain;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.Entity;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.OnePieceMod;

/**
 * The Sea Train: ride the Puffing Tom between Water 7, Enies Lobby and the Sea Train Stations,
 * and build Sea Train Stations of your own for fast travel between stops you've visited.
 * The building itself (Ticket Booth + blueprint) is registered with the other buildings in building/Buildings.
 */
public class SeaTrainFeature {
	public static final ResourceKey<EntityType<?>> SEA_TRAIN_KEY = ResourceKey.create(Registries.ENTITY_TYPE, OnePieceMod.id("sea_train"));

	public static final EntityType<SeaTrainEntity> SEA_TRAIN = Registry.register(BuiltInRegistries.ENTITY_TYPE, SEA_TRAIN_KEY,
			EntityType.Builder.<SeaTrainEntity>of(SeaTrainEntity::new, MobCategory.MISC)
					.sized(1.0f, 1.0f)
					.clientTrackingRange(10)
					.updateInterval(1) // Sent every tick, so the ride is smooth.
					.noSummon()
					.build(SEA_TRAIN_KEY));

	/** Train parts that just loaded; any that aren't riding a train by the end of the tick are strays. */
	private static final List<Entity> NEW_PARTS = new ArrayList<>();

	public static void initialize() {
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity instanceof Display && entity.entityTags().contains(PuffingTom.PART_TAG)) {
				NEW_PARTS.add(entity);
			}
		});
		Stations.initialize();
		SeaTrainCommands.register();
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			Trips.tick(server);
			for (Entity part : NEW_PARTS) {
				if (!part.isPassenger()) {
					part.discard(); // Left behind when the server stopped mid-trip.
				}
			}
			NEW_PARTS.clear();
			if (server.getTickCount() % 40 == 0) {
				for (ServerPlayer player : server.getPlayerList().getPlayers()) {
					Stations.notice(player);
				}
			}
		});
	}
}
