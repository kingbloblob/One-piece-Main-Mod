package com.onepiecemod.sea;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetActionBarTextPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BiomeTags;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.biome.Biome;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;

/**
 * Splits the Overworld's oceans into the seas of One Piece, in rings around spawn (matching the Grand Line
 * world's biome rings, see world/RingBiomeSource):
 *
 * <pre>
 *   0 ... 1400 blocks from spawn      the East Blue (calm, where every pirate starts)
 *   1400 ... 1650                     the Calm Belt (no wind, Sea King nests)
 *   1650 ... 3500                     the Grand Line (Paradise, the first half)
 *   further out                       the New World
 * </pre>
 *
 * Only ocean biomes count. Land is just land. Change the numbers below to move the belts.
 */
public class CalmBelt {
	/** How far the East Blue reaches from spawn, in blocks. */
	public static final int EAST_BLUE_RADIUS = 1400;
	/** How wide the Calm Belt ring is, in blocks. */
	public static final int CALM_BELT_WIDTH = 250;
	/** Where the New World starts, in blocks from spawn. */
	public static final int NEW_WORLD_RADIUS = 3500;

	public enum Sea {
		BLUE("the East Blue", "Calm waters. Not many Sea Kings out here.", ChatFormatting.AQUA),
		CALM_BELT("the Calm Belt", "There is no wind here, so sails are useless... and this is where Sea Kings nest!", ChatFormatting.DARK_RED),
		GRAND_LINE("the Grand Line", "Compasses go crazy here. Sail by Log Pose!", ChatFormatting.GOLD),
		NEW_WORLD("the New World", "The second half of the Grand Line. The weather here is even wilder, and so are the pirates.", ChatFormatting.RED);

		private final String title;
		private final String warning;
		private final ChatFormatting color;

		Sea(String title, String warning, ChatFormatting color) {
			this.title = title;
			this.warning = warning;
			this.color = color;
		}

		/** Like "the East Blue". */
		public String title() {
			return title;
		}

		/** The Grand Line, either half. */
		public boolean grandLine() {
			return this == GRAND_LINE || this == NEW_WORLD;
		}
	}

	/** Which sea a spot is in, or null if it isn't open ocean in the Overworld. */
	public static Sea seaAt(Level level, BlockPos pos) {
		if (level.dimension() != Level.OVERWORLD || !isOcean(level.getBiome(pos))) {
			return null;
		}
		return seaByDistance(pos);
	}

	/** Which sea a spot would be by its distance from spawn alone, land or not. */
	public static Sea seaByDistance(BlockPos pos) {
		double distance = Math.sqrt((double) pos.getX() * pos.getX() + (double) pos.getZ() * pos.getZ());
		if (distance < EAST_BLUE_RADIUS) {
			return Sea.BLUE;
		}
		if (distance < EAST_BLUE_RADIUS + CALM_BELT_WIDTH) {
			return Sea.CALM_BELT;
		}
		return distance < NEW_WORLD_RADIUS ? Sea.GRAND_LINE : Sea.NEW_WORLD;
	}

	public static boolean isCalmBelt(Level level, BlockPos pos) {
		return seaAt(level, pos) == Sea.CALM_BELT;
	}

	/** How much wind fills a ship's sails here: 0 in the Calm Belt, full wind everywhere else. Ships use this. */
	public static Double windMultiplier(Level level, BlockPos pos) {
		return isCalmBelt(level, pos) ? 0.0 : 1.0;
	}

	public static boolean isOcean(Holder<Biome> biome) {
		return biome.is(BiomeTags.IS_OCEAN) || biome.is(BiomeTags.IS_DEEP_OCEAN);
	}

	// ---------- Tell players when they sail into a new sea ----------

	private static final Map<UUID, Sea> LAST_SEA = new HashMap<>();

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 20 != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				Sea sea = seaAt(player.level(), player.blockPosition());
				// On land we stay quiet, and we remember the last sea so walking across an island doesn't repeat it.
				if (sea != null && sea != LAST_SEA.get(player.getUUID())) {
					boolean firstCheck = !LAST_SEA.containsKey(player.getUUID());
					LAST_SEA.put(player.getUUID(), sea);
					if (!firstCheck) {
						announce(player, sea);
					}
				}
			}
		});
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> LAST_SEA.remove(handler.getPlayer().getUUID()));
	}

	private static void announce(ServerPlayer player, Sea sea) {
		player.connection.send(new ClientboundSetActionBarTextPacket(
				Component.literal("You sailed into " + sea.title + "!").withStyle(sea.color, ChatFormatting.BOLD)));
		player.sendSystemMessage(Component.literal("You sailed into " + sea.title + ". " + sea.warning).withStyle(sea.color));
	}
}
