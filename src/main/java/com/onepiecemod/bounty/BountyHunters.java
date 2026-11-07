package com.onepiecemod.bounty;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.level.levelgen.Heightmap;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

/**
 * Sends Devil Fruit bounty hunters after pirates with a bounty of 100,000,000 or more (threat level 3+).
 * They aren't Marines: they come alone or in small groups, each with a random Devil Fruit.
 * Higher bounties bring more of them, tougher ones, and stronger fruits.
 *
 * Every 30 seconds each wanted player (Overworld, survival or adventure, not Peaceful, not in a Navy raid)
 * rolls a chance. After hunters arrive there is a 5 minute break.
 */
public class BountyHunters {
	private static final int CHECK_EVERY_TICKS = 20 * 30;
	private static final int BREAK_TICKS = 20 * 60 * 5;

	/** Chance per check at threat level 0..5. Level 3 is about once every 12 minutes, level 5 every 5. */
	private static final float[] CHANCE = {0f, 0f, 0f, 0.04f, 0.06f, 0.10f};
	/** How many hunters come together at threat level 0..5 (smallest, largest). */
	private static final int[][] GROUP = {{0, 0}, {0, 0}, {0, 0}, {1, 1}, {1, 2}, {2, 3}};
	public static final int FIRST_LEVEL = 3;

	private static final Map<UUID, Integer> nextTick = new HashMap<>();

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % CHECK_EVERY_TICKS != 0) {
				return;
			}
			int now = server.getTickCount();
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				int threat = Bounty.threatLevel(player);
				if (threat < FIRST_LEVEL || !MarineHunters.canBeHunted(player) || !NavyCalm.canStart(player)
						|| now < nextTick.getOrDefault(player.getUUID(), 0)) {
					continue;
				}
				if (player.getRandom().nextFloat() < CHANCE[threat] * com.onepiecemod.config.ModConfig.bountyHunterRate() && send(player) > 0) {
					nextTick.put(player.getUUID(), now + BREAK_TICKS);
				}
			}
		});
	}

	/** What comes at this threat level, for /bounty. */
	public static String describe(int threat) {
		if (threat < FIRST_LEVEL) {
			return "Bounty hunters with Devil Fruits come after you from " + Bounty.format(100_000_000L) + ".";
		}
		int[] group = GROUP[threat];
		String size = group[0] == group[1] ? String.valueOf(group[0]) : group[0] + " to " + group[1];
		return "Bounty hunters: " + size + " at a time, each with a Devil Fruit.";
	}

	/** Sends hunters at the player. Returns how many came (0 if there was nowhere to stand). */
	public static int send(ServerPlayer player) {
		ServerLevel level = (ServerLevel) player.level();
		int threat = Math.max(FIRST_LEVEL, Math.min(5, Bounty.threatLevel(player)));

		// Don't pile them up: wait until the last ones are gone.
		List<BountyHunterEntity> alreadyHere = level.getEntitiesOfClass(BountyHunterEntity.class,
				player.getBoundingBox().inflate(96.0), hunter -> hunter.isAlive());
		if (!alreadyHere.isEmpty()) {
			return 0;
		}

		int[] group = GROUP[threat];
		int count = group[0] + player.getRandom().nextInt(group[1] - group[0] + 1);
		StringBuilder names = new StringBuilder();
		int sent = 0;
		for (int i = 0; i < count; i++) {
			BlockPos spot = findSpot(level, player);
			BountyHunterEntity hunter = spot == null ? null : BountyFeature.BOUNTY_HUNTER.create(level, EntitySpawnReason.EVENT);
			if (hunter == null) {
				continue;
			}
			hunter.setPos(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
			hunter.setup(HunterFruit.random(player.getRandom(), threat), threat);
			hunter.setHunted(player);
			level.addFreshEntity(hunter);
			if (sent > 0) {
				names.append(", ");
			}
			names.append(hunter.getCustomName().getString());
			sent++;
		}
		if (sent > 0) {
			player.sendSystemMessage(Component.literal((sent == 1 ? "A bounty hunter is" : sent + " bounty hunters are")
					+ " after your " + Bounty.format(Bounty.get(player)) + ": " + names + "!").withStyle(ChatFormatting.DARK_PURPLE));
			level.playSound(null, player.blockPosition(), SoundEvents.ILLUSIONER_PREPARE_MIRROR, SoundSource.HOSTILE, 1.5f, 0.8f);
		}
		return sent;
	}

	/** Dry ground 16 to 28 blocks from the player. */
	private static BlockPos findSpot(ServerLevel level, ServerPlayer player) {
		for (int attempt = 0; attempt < 12; attempt++) {
			double angle = player.getRandom().nextDouble() * Math.PI * 2;
			int distance = 16 + player.getRandom().nextInt(13);
			int x = Mth.floor(player.getX() + Math.cos(angle) * distance);
			int z = Mth.floor(player.getZ() + Math.sin(angle) * distance);
			if (!level.hasChunkAt(new BlockPos(x, 0, z))) {
				continue;
			}
			BlockPos pos = new BlockPos(x, level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z), z);
			if (level.getFluidState(pos.below()).isEmpty() && level.getBlockState(pos.below()).isSolid()
					&& Math.abs(pos.getY() - player.getY()) < 16) {
				return pos;
			}
		}
		return null;
	}
}
