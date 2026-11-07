package com.onepiecemod.voyage;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import org.jetbrains.annotations.Nullable;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.vehicle.boat.ChestBoat;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.ship.ShipEntity;

/**
 * Drifting supply boats: now and then an abandoned rowboat with a chest of salvage bobs into view ahead of your ship.
 * Sail up, hop over and open the chest (they're plain vanilla chest boats, so you can keep the boat too).
 * Boats nobody bothered with are cleared away once every player has sailed far off.
 */
public final class Flotsam {
	public static final String TAG = "onepiece_flotsam";
	public static final ResourceKey<LootTable> LOOT = ResourceKey.create(Registries.LOOT_TABLE, OnePieceMod.id("voyage/flotsam"));

	// ---- Tune these ----
	private static final int CHECK_EVERY = 20 * 45;
	private static final float CHANCE = 0.10f;
	private static final int COOLDOWN = 20 * 60 * 4;
	/** Untouched drifting boats this far from every player are removed. */
	private static final double FORGET_RANGE = 180;

	private static final Map<UUID, Long> NEXT = new HashMap<>();

	private Flotsam() {
	}

	static void clear() {
		NEXT.clear();
	}

	static void tick(MinecraftServer server) {
		ServerLevel level = server.overworld();
		if (server.getTickCount() % 600 == 41) {
			cleanUp(level);
		}
		if (server.getTickCount() % CHECK_EVERY != 13) {
			return;
		}
		long now = level.getGameTime();
		for (ServerPlayer player : level.players()) {
			ShipEntity ship = SeaSpots.sailing(player);
			if (ship == null || now < NEXT.getOrDefault(player.getUUID(), 0L) || SeaSpots.sea(level, ship.blockPosition()) == null
					|| player.getRandom().nextFloat() >= CHANCE) {
				continue;
			}
			if (spawnAhead(level, ship) != null) {
				NEXT.put(player.getUUID(), now + COOLDOWN);
				player.sendSystemMessage(Component.literal("Something is bobbing on the waves ahead... an abandoned supply boat!")
						.withStyle(ChatFormatting.YELLOW));
			}
		}
	}

	/** Puts a drifting supply boat 40 to 70 blocks ahead of the ship. Null if there's no open water there. */
	@Nullable
	public static ChestBoat spawnAhead(ServerLevel level, ShipEntity ship) {
		BlockPos spot = SeaSpots.openWaterNear(level, ship, 40, 30, 60, 3, 3);
		return spot == null ? null : spawnAt(level, new Vec3(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5), level.getRandom().nextFloat() * 360);
	}

	/** A drifting supply boat on the sea's surface here. */
	@Nullable
	public static ChestBoat spawnAt(ServerLevel level, Vec3 at, float yaw) {
		ChestBoat boat = EntityTypes.OAK_CHEST_BOAT.create(level, EntitySpawnReason.EVENT);
		if (boat == null) {
			return null;
		}
		boat.snapTo(at.x, at.y, at.z, yaw, 0);
		boat.setContainerLootTable(LOOT);
		boat.setContainerLootTableSeed(level.getRandom().nextLong());
		boat.setCustomName(Component.literal("Drifting Supply Boat"));
		boat.addTag(TAG);
		level.addFreshEntity(boat);
		return boat;
	}

	/** Removes drifting boats that no player is anywhere near (and nobody is sitting in). */
	private static void cleanUp(ServerLevel level) {
		for (ChestBoat boat : level.getEntities(EntityTypes.OAK_CHEST_BOAT, boat -> boat.entityTags().contains(TAG))) {
			if (boat.getPassengers().isEmpty() && !SeaSpots.anyPlayerNear(level, boat.position(), FORGET_RANGE)) {
				boat.discard();
			}
		}
	}

	/** Every drifting boat near a spot (for /voyage list). */
	static int countNear(ServerLevel level, Vec3 at, double within) {
		return level.getEntitiesOfClass(ChestBoat.class, new AABB(at, at).inflate(within), boat -> boat.entityTags().contains(TAG)).size();
	}
}
