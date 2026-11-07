package com.onepiecemod.empire;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import com.mojang.serialization.Codec;

import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.player.Player;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;

/**
 * What the empire feature saves: each player's title and kingdoms, and who holds which title on the server.
 */
public class EmpireData {
	/** The player's title, as Title.ordinal(). Kept when you die. */
	public static final AttachmentType<Integer> TITLE = AttachmentRegistry.create(
			OnePieceMod.id("title"),
			builder -> builder.persistent(Codec.INT).copyOnDeath()
	);

	/** Where the player's Kingdom Flags stand (BlockPos.asLong), all in the Overworld. */
	public static final AttachmentType<List<Long>> KINGDOMS = AttachmentRegistry.create(
			OnePieceMod.id("kingdoms"),
			builder -> builder.persistent(Codec.LONG.listOf()).copyOnDeath()
	);

	/**
	 * Saved on the Overworld: player id -> title, for everyone holding a title (even when offline).
	 * This is how we know the Four Emperors seats are all taken.
	 */
	public static final AttachmentType<Map<String, Integer>> HOLDERS = AttachmentRegistry.create(
			OnePieceMod.id("title_holders"),
			builder -> builder.persistent(Codec.unboundedMap(Codec.STRING, Codec.INT))
	);

	public static Title title(Player player) {
		return Title.byLevel(player.getAttachedOrElse(TITLE, 0));
	}

	public static void setTitle(Player player, Title title) {
		player.setAttached(TITLE, title.ordinal());
		if (player.level().getServer() != null) {
			Map<String, Integer> holders = new HashMap<>(holders(player.level().getServer()));
			if (title == Title.NONE) {
				holders.remove(player.getUUID().toString());
			} else {
				holders.put(player.getUUID().toString(), title.ordinal());
			}
			player.level().getServer().overworld().setAttached(HOLDERS, holders);
		}
	}

	public static Map<String, Integer> holders(MinecraftServer server) {
		return server.overworld().getAttachedOrElse(HOLDERS, Map.of());
	}

	/** How many players other than this one hold exactly this title. */
	public static int otherHolders(MinecraftServer server, UUID self, Title title) {
		int count = 0;
		for (Map.Entry<String, Integer> entry : holders(server).entrySet()) {
			if (entry.getValue() == title.ordinal() && !entry.getKey().equals(self.toString())) {
				count++;
			}
		}
		return count;
	}

	public static List<BlockPos> kingdoms(Player player) {
		List<BlockPos> list = new ArrayList<>();
		for (long packed : player.getAttachedOrElse(KINGDOMS, List.of())) {
			list.add(BlockPos.of(packed));
		}
		return list;
	}

	public static void addKingdom(Player player, BlockPos pos) {
		List<Long> list = new ArrayList<>(player.getAttachedOrElse(KINGDOMS, List.of()));
		if (!list.contains(pos.asLong())) {
			list.add(pos.asLong());
			player.setAttached(KINGDOMS, list);
		}
	}

	public static void removeKingdom(Player player, BlockPos pos) {
		List<Long> list = new ArrayList<>(player.getAttachedOrElse(KINGDOMS, List.of()));
		if (list.remove(pos.asLong())) {
			player.setAttached(KINGDOMS, list);
		}
	}

	/** True if this spot is inside one of this player's kingdoms. */
	public static boolean inOwnKingdom(Player player, BlockPos pos) {
		if (!(player.level() instanceof ServerLevel level) || level != level.getServer().overworld()) {
			return false;
		}
		for (BlockPos flag : kingdoms(player)) {
			if (flag.closerThan(pos, KingdomFlagBlockEntity.RADIUS)) {
				return true;
			}
		}
		return false;
	}

	public static void initialize() {
		// Loading this class is enough to register the attachments.
	}
}
