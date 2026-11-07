package com.onepiecemod.sea;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetActionBarTextPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BiomeTags;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.EntitySpawnReason;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

/**
 * Every 10 seconds, each player out at sea has a chance to attract a Sea King.
 * The Calm Belt is full of them. The Grand Line has a few, and the Blue seas almost none.
 */
public class SeaKingSpawner {
	private static final int CHECK_EVERY_TICKS = 200;

	// Chance per check, and how many Sea Kings may already be nearby.
	private static final float CALM_BELT_CHANCE = 0.35f;
	private static final int CALM_BELT_MAX_NEARBY = 3;
	private static final float GRAND_LINE_CHANCE = 0.04f;
	private static final float BLUE_SEA_CHANCE = 0.01f;
	private static final int OPEN_SEA_MAX_NEARBY = 1;
	/** Chance that a Sea King that would appear is the sea's boss instead (SeaBosses). */
	private static final float BOSS_CHANCE = 0.04f;
	private static final float BOSS_CHANCE_CALM_BELT = 0.01f;

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % CHECK_EVERY_TICKS != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				if (!player.isSpectator()) {
					trySpawnNear(player);
				}
			}
		});
	}

	private static void trySpawnNear(ServerPlayer player) {
		ServerLevel level = (ServerLevel) player.level();
		if (level.getDifficulty() == Difficulty.PEACEFUL) {
			return;
		}
		CalmBelt.Sea sea = CalmBelt.seaAt(level, player.blockPosition());
		if (sea == null) {
			return; // Not at sea.
		}

		float chance;
		int maxNearby;
		switch (sea) {
			case CALM_BELT -> {
				chance = CALM_BELT_CHANCE;
				maxNearby = CALM_BELT_MAX_NEARBY;
			}
			case GRAND_LINE -> {
				chance = GRAND_LINE_CHANCE;
				maxNearby = OPEN_SEA_MAX_NEARBY;
			}
			default -> {
				chance = BLUE_SEA_CHANCE;
				maxNearby = OPEN_SEA_MAX_NEARBY;
			}
		}
		chance *= com.onepiecemod.config.ModConfig.seaKingRate(); // Settings file: sea_king_rate (0 = no Sea Kings).
		if (chance <= 0) {
			return;
		}
		// Outside the Calm Belt they only live in deep ocean.
		if (sea != CalmBelt.Sea.CALM_BELT && !level.getBiome(player.blockPosition()).is(BiomeTags.IS_DEEP_OCEAN)) {
			return;
		}

		RandomSource random = level.getRandom();
		if (random.nextFloat() >= chance) {
			return;
		}
		int nearby = level.getEntitiesOfClass(SeaKingEntity.class, player.getBoundingBox().inflate(96.0)).size();
		if (nearby >= maxNearby) {
			return;
		}

		BlockPos spot = findDeepWater(level, player, random);
		if (spot == null) {
			return;
		}
		SeaKingEntity seaKing = SeaEntities.SEA_KING.create(level, EntitySpawnReason.NATURAL);
		if (seaKing != null) {
			seaKing.setPos(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
			seaKing.setYRot(random.nextFloat() * 360.0f);
			// Now and then it's the boss of this sea itself (SeaBosses), if no boss is around already.
			SeaBosses.Boss boss = SeaBosses.forSea(sea);
			if (boss != null && random.nextFloat() < (sea == CalmBelt.Sea.CALM_BELT ? BOSS_CHANCE_CALM_BELT : BOSS_CHANCE)
					&& level.getEntitiesOfClass(SeaKingEntity.class, player.getBoundingBox().inflate(160), SeaKingEntity::isSeaBoss).isEmpty()) {
				SeaBosses.spawn(level, boss, seaKing.position(), player);
				return;
			}
			level.addFreshEntity(seaKing);
			player.connection.send(new ClientboundSetActionBarTextPacket(
					Component.literal("Something huge is moving beneath the waves...").withStyle(ChatFormatting.DARK_AQUA, ChatFormatting.ITALIC)));
		}
	}

	/** A random spot 32 to 52 blocks from the player with at least 8 blocks of water, or null. */
	public static BlockPos findDeepWater(ServerLevel level, ServerPlayer player, RandomSource random) {
		int seaLevel = level.getSeaLevel();
		for (int attempt = 0; attempt < 8; attempt++) {
			double angle = random.nextDouble() * Math.PI * 2.0;
			double distance = 32.0 + random.nextDouble() * 20.0; // they're huge now: surface a fair way off
			int x = (int) Math.floor(player.getX() + Math.cos(angle) * distance);
			int z = (int) Math.floor(player.getZ() + Math.sin(angle) * distance);
			BlockPos spot = new BlockPos(x, seaLevel - 5, z);
			if (isDeepWater(level, spot)) {
				return spot;
			}
		}
		return null;
	}

	/** True if there's water from 1 block below the surface down to 8 blocks below it. */
	public static boolean isDeepWater(ServerLevel level, BlockPos spot) {
		int seaLevel = level.getSeaLevel();
		for (int y : new int[] {seaLevel - 2, seaLevel - 5, seaLevel - 8}) {
			BlockPos check = new BlockPos(spot.getX(), y, spot.getZ());
			if (!level.isLoaded(check) || !level.getFluidState(check).is(FluidTags.WATER)) {
				return false;
			}
		}
		return true;
	}
}
