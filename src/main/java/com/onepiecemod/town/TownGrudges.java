package com.onepiecemod.town;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import com.mojang.serialization.Codec;

import net.minecraft.server.level.ServerLevel;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;

/**
 * What towns remember about players, saved with the world so a restart doesn't wipe it:
 * - grudges: who hurt someone here, and until when the town stays angry;
 * - kills today: how many townsfolk each player killed here today. Only the first few raise their bounty,
 *   because the town keeps bringing in new people and that would let you farm bounty forever.
 * Kept on the town's level, keyed by the town key ("foosha_village@12,-40").
 */
public class TownGrudges {
	/** Kills per town per day that still raise your bounty. */
	public static final int BOUNTY_KILLS_PER_DAY = 2;

	/** Town key -> player UUID -> game time the grudge ends. */
	public static final AttachmentType<Map<String, Map<String, Long>>> GRUDGES = AttachmentRegistry.create(
			OnePieceMod.id("town_grudges"),
			builder -> builder.persistent(Codec.unboundedMap(Codec.STRING, Codec.unboundedMap(Codec.STRING, Codec.LONG)))
	);

	/** "townKey|playerUUID" -> day * 1000 + kills that day. */
	public static final AttachmentType<Map<String, Long>> KILLS = AttachmentRegistry.create(
			OnePieceMod.id("town_kills"),
			builder -> builder.persistent(Codec.unboundedMap(Codec.STRING, Codec.LONG))
	);

	private TownGrudges() {
	}

	public static boolean isAngry(Town town, UUID player) {
		Map<String, Long> players = town.level.getAttachedOrElse(GRUDGES, Map.of()).get(town.key);
		Long until = players == null ? null : players.get(player.toString());
		return until != null && until > town.level.getGameTime();
	}

	/** The town stays angry with this player until the given game time (an older, longer grudge is kept). */
	public static void makeAngry(Town town, UUID player, long until) {
		ServerLevel level = town.level;
		long now = level.getGameTime();
		Map<String, Map<String, Long>> copy = new HashMap<>();
		for (Map.Entry<String, Map<String, Long>> e : level.getAttachedOrElse(GRUDGES, Map.<String, Map<String, Long>>of()).entrySet()) {
			Map<String, Long> players = new HashMap<>();
			e.getValue().forEach((id, end) -> {
				if (end > now) {
					players.put(id, end); // Forgiven grudges are dropped so the save stays small.
				}
			});
			if (!players.isEmpty()) {
				copy.put(e.getKey(), players);
			}
		}
		copy.computeIfAbsent(town.key, k -> new HashMap<>()).merge(player.toString(), until, Math::max);
		level.setAttached(GRUDGES, copy);
	}

	/** Counts a kill. True if it's still one of today's first few here, so it should raise the bounty. */
	public static boolean countKill(Town town, UUID player) {
		ServerLevel level = town.level;
		long day = level.getOverworldClockTime() / 24000L;
		String key = town.key + "|" + player;
		Map<String, Long> copy = new HashMap<>();
		level.getAttachedOrElse(KILLS, Map.<String, Long>of()).forEach((k, v) -> {
			if (v / 1000 == day) {
				copy.put(k, v); // Older days are forgotten.
			}
		});
		long kills = copy.containsKey(key) ? copy.get(key) % 1000 + 1 : 1;
		copy.put(key, day * 1000 + Math.min(kills, 999));
		level.setAttached(KILLS, copy);
		return kills <= BOUNTY_KILLS_PER_DAY;
	}
}
