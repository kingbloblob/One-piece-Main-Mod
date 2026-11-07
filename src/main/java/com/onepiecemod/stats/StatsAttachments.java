package com.onepiecemod.stats;

import com.mojang.serialization.Codec;

import net.minecraft.world.entity.player.Player;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;

/**
 * Saves each player's Pirate Level and stat tree on the player, so it survives restarts and deaths.
 */
public class StatsAttachments {
	public static final AttachmentType<StatsData> STATS = AttachmentRegistry.create(
			OnePieceMod.id("player_stats"),
			builder -> builder
					.persistent(StatsData.CODEC) // Save it to disk.
					.copyOnDeath() // Training isn't lost when you die.
	);

	/** Game time (ticks) when Second Wind can save this player again. Saved, so relogging doesn't reset it. */
	public static final AttachmentType<Long> SECOND_WIND_READY_AT = AttachmentRegistry.create(
			OnePieceMod.id("second_wind_ready_at"),
			builder -> builder
					.persistent(Codec.LONG)
					.copyOnDeath()
	);

	/** How many times this player has reset their stat points (the first reset is free). */
	public static final AttachmentType<Integer> RESPECS = AttachmentRegistry.create(
			OnePieceMod.id("stat_respecs"),
			builder -> builder
					.persistent(Codec.INT)
					.copyOnDeath()
	);

	/** A player's stats. Players who never trained get StatsData.EMPTY. */
	public static StatsData get(Player player) {
		StatsData data = player.getAttached(STATS);
		return data != null ? data : StatsData.EMPTY;
	}

	public static void set(Player player, StatsData data) {
		player.setAttached(STATS, data);
	}

	/** The rank a player has in one stat. Handy for other features, e.g. StatsAttachments.rank(player, PlayerStat.SPEED). */
	public static int rank(Player player, PlayerStat stat) {
		return get(player).rank(stat);
	}

	public static void initialize() {
		// Loading this class is enough to register the attachment.
	}
}
