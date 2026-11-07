package com.onepiecemod.career;

import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import com.onepiecemod.sound.ModSounds;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.Level;

import com.onepiecemod.bounty.NavyCalm;
import com.onepiecemod.npc.HumanNpc;

/**
 * The other side of the coin. Pirates don't hunt a Marine for a bounty, they hunt for revenge:
 * the higher a Marine's rank, the more often pirate crews ambush them, and the tougher the crews.
 * Revolutionaries are already hunted by the Navy through their bounty; from Officer up,
 * CP agents also come after them now and then.
 *
 * Same rules as Marine hunts: checks every 20 seconds, a break after each ambush, never at home
 * (near your bed), in a boss fight, a raid, or in Creative, Spectator or Peaceful. Uses the Marine hunt setting.
 */
final class CareerAmbush {
	static final String TAG = "onepiece_career_ambush";
	private static final int CHECK_EVERY_TICKS = 20 * 20;
	private static final int BREAK_TICKS = 20 * 150;

	/** Chance per check for a Marine, by rank (Seaman Recruit to Fleet Admiral). */
	private static final float[] MARINE_CHANCE = {0.06f, 0.07f, 0.08f, 0.10f, 0.11f, 0.13f, 0.15f, 0.17f, 0.19f, 0.22f, 0.25f};
	/** Chance per check of CP agents for a Revolutionary Officer or higher. */
	private static final float CP_CHANCE = 0.06f;

	private static final Map<UUID, Integer> nextTick = new HashMap<>();
	private static final Map<UUID, Set<UUID>> LIVE = new HashMap<>();

	private CareerAmbush() {
	}

	static void tick(MinecraftServer server) {
		int now = server.getTickCount();
		if (now % CHECK_EVERY_TICKS != 7) {
			return;
		}
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			cleanUp(player);
			CareerData data = Careers.get(player);
			float chance = switch (data.path()) {
				case MARINE -> MARINE_CHANCE[Math.min(data.rank(), MARINE_CHANCE.length - 1)];
				case REVOLUTIONARY -> data.rank() >= 3 ? CP_CHANCE : 0f;
				default -> 0f;
			};
			if (chance <= 0 || !canAmbush(player) || now < nextTick.getOrDefault(player.getUUID(), 0)) {
				continue;
			}
			if (player.getRandom().nextFloat() < chance * com.onepiecemod.config.ModConfig.marineHuntRate() && ambush(player)) {
				nextTick.put(player.getUUID(), now + BREAK_TICKS);
			}
		}
	}

	private static boolean canAmbush(ServerPlayer player) {
		ServerLevel level = (ServerLevel) player.level();
		return level.dimension() == Level.OVERWORLD && level.getDifficulty() != Difficulty.PEACEFUL
				&& !player.isCreative() && !player.isSpectator() && NavyCalm.canStart(player);
	}

	/** Sends a squad now. Also used by /career ambush. */
	static boolean ambush(ServerPlayer player) {
		CareerData data = Careers.get(player);
		Set<UUID> live = LIVE.computeIfAbsent(player.getUUID(), id -> new HashSet<>());
		if (!live.isEmpty() || data.path() == Career.PIRATE) {
			return false;
		}
		ServerLevel level = (ServerLevel) player.level();
		BlockPos spot = CareerSquads.spotNear(level, player.blockPosition(), 18, 30);
		if (spot == null) {
			return false;
		}
		boolean marine = data.path() == Career.MARINE;
		int rank = data.rank();
		List<String> kits = marine
				? CareerSquads.pirateCrew(rank, Math.min(6, 2 + rank / 2))
				: (rank >= 6 ? List.of("cp0_agent", "cp_agent", "cp_agent") : List.of("cp_agent", "cp_agent"));
		double toughness = 1.0 + 0.1 * rank;
		for (String kit : kits) {
			HumanNpc npc = CareerSquads.enemy(level, kit, toughness);
			if (npc == null) {
				continue;
			}
			BlockPos pos = CareerSquads.dryGround(level, spot.getX() + level.getRandom().nextInt(5) - 2, spot.getZ() + level.getRandom().nextInt(5) - 2);
			CareerSquads.place(level, npc, pos != null ? pos : spot, player, TAG);
			live.add(npc.getUUID());
		}
		if (live.isEmpty()) {
			return false;
		}
		ModSounds.play(player, marine ? ModSounds.CANNON : ModSounds.NAVY_BUGLE);
		player.sendSystemMessage(Component.literal(marine
				? "Pirates! A crew is out for revenge on the Marine " + data.currentRank().name() + "!"
				: "CP agents! The World Government has found the Revolutionary " + data.currentRank().name() + ".")
				.withStyle(ChatFormatting.RED));
		return true;
	}

	/** Ambushers who lost you (128 blocks) or died are forgotten, so the next ambush can come. */
	private static void cleanUp(ServerPlayer player) {
		Set<UUID> live = LIVE.get(player.getUUID());
		if (live == null || live.isEmpty()) {
			return;
		}
		ServerLevel level = (ServerLevel) player.level();
		live.removeIf(id -> {
			Entity entity = level.getEntity(id);
			if (entity == null || !entity.isAlive()) {
				return true;
			}
			if (entity.distanceToSqr(player) > 128.0 * 128.0) {
				entity.discard();
				return true;
			}
			return false;
		});
	}
}
