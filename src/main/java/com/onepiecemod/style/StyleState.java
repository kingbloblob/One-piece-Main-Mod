package com.onepiecemod.style;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;

/**
 * Short-lived combat state for each player: cooldowns, timed buffs and air jumps.
 * Buffs and air jumps only live in memory. Cooldowns are also saved on the player (StyleAttachments.COOLDOWNS),
 * so logging out and back in doesn't make every move ready again.
 * Times are in game ticks, from level.getGameTime().
 */
public class StyleState {
	private static final Map<UUID, StyleState> STATES = new HashMap<>();

	/** Game time when each technique can be used again. */
	public final Map<Technique, Long> readyAt = new EnumMap<>(Technique.class);
	/** Game time until which each timed buff (Diable Jambe, Tekkai, Asura...) lasts. */
	public final Map<Technique, Long> activeUntil = new EnumMap<>(Technique.class);
	/** Air jumps used since the player last stood on the ground. */
	public int airJumps;
	/** Game time when Concasse started, or 0 when the player isn't in the middle of one. */
	public long concasseStart;
	/** Yahazu Giri cuts that land a moment after you walk past. */
	public final List<DelayedCut> delayedCuts = new ArrayList<>();

	public record DelayedCut(LivingEntity target, long at, float damage) {
	}

	public static StyleState of(Player player) {
		return STATES.computeIfAbsent(player.getUUID(), id -> {
			StyleState state = new StyleState();
			// Pick up the cooldowns saved from last time.
			player.getAttachedOrElse(StyleAttachments.COOLDOWNS, Map.<String, Long>of()).forEach((name, at) -> {
				Technique technique = Technique.byName(name);
				if (technique != null) {
					state.readyAt.put(technique, at);
				}
			});
			return state;
		});
	}

	/** Starts a move's cooldown and saves it on the player. */
	public void startCooldown(Player player, Technique technique, long readyTime) {
		readyAt.put(technique, readyTime);
		long now = player.level().getGameTime();
		Map<String, Long> saved = new HashMap<>();
		readyAt.forEach((move, at) -> {
			if (at > now) {
				saved.put(move.name(), at);
			}
		});
		player.setAttached(StyleAttachments.COOLDOWNS, saved);
	}

	public static void forget(UUID playerId) {
		STATES.remove(playerId);
	}

	public boolean isActive(Technique technique, long now) {
		return activeUntil.getOrDefault(technique, 0L) > now;
	}

	/** Seconds left before the move is ready, or 0 if it's ready now. */
	public int secondsLeft(Technique technique, long now) {
		long ticks = readyAt.getOrDefault(technique, 0L) - now;
		return ticks <= 0 ? 0 : (int) Math.ceil(ticks / 20.0);
	}
}
