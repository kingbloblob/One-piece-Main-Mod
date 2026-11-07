package com.onepiecemod.weather.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.Mth;

import com.onepiecemod.weather.SeaEvent;
import com.onepiecemod.weather.SeaEventSync;
import com.onepiecemod.weather.SeaEventType;

/**
 * How stormy the sky looks to this player: rain and thunder only near a sea storm, not across the whole world.
 * The server never touches the world's weather for a storm, so friends on land far away keep their sunshine.
 * LevelWeatherMixin mixes this into the client's rain and thunder levels.
 */
public class LocalStorm {
	/** Rain fades in over this many blocks past the storm's edge. */
	private static final double EDGE = 40;
	/** Ticks the storm takes to roll in and to clear. */
	private static final double FADE_TICKS = 100;

	private static long cachedTick = Long.MIN_VALUE;
	private static float cached;

	private LocalStorm() {
	}

	/** 0 = no storm here, 1 = right inside one. */
	public static float strength() {
		Minecraft minecraft = Minecraft.getInstance();
		LocalPlayer player = minecraft.player;
		if (player == null || minecraft.level == null || SeaEventSync.CLIENT_EVENTS.isEmpty()) {
			return 0;
		}
		long time = minecraft.level.getGameTime();
		if (time == cachedTick) {
			return cached;
		}
		float best = 0;
		for (SeaEvent event : SeaEventSync.CLIENT_EVENTS) {
			if (event.type != SeaEventType.STORM && event.type != SeaEventType.HAILSTORM || !event.isActive(time)) {
				continue;
			}
			double inTime = Math.min(time - event.startTime, event.endTime - time) / FADE_TICKS;
			double past = event.distance(player.getX(), player.getZ()) - event.radius;
			double inSpace = 1 - past / EDGE;
			best = Math.max(best, (float) Mth.clamp(Math.min(inTime, inSpace), 0, 1));
		}
		cachedTick = time;
		cached = best;
		return best;
	}
}
