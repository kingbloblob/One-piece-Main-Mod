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
	private static float cachedThunder;
	/** A tornado needs light behind it to be seen: under a Great Cyclone the sky only darkens this much. */
	private static final float CYCLONE_DARKNESS = 0.3f;

	private LocalStorm() {
	}

	/** 0 = no storm here, 1 = right inside one. */
	public static float strength() {
		Minecraft minecraft = Minecraft.getInstance();
		LocalPlayer player = minecraft.player;
		if (player == null || minecraft.level == null || SeaEventSync.CLIENT_EVENTS.isEmpty()) {
			cachedThunder = 0;
			return 0;
		}
		long time = minecraft.level.getGameTime();
		if (time == cachedTick) {
			return cached;
		}
		float best = 0;
		float thunder = 0;
		for (SeaEvent event : SeaEventSync.CLIENT_EVENTS) {
			boolean cyclone = event.type == SeaEventType.CYCLONE;
			if (event.type != SeaEventType.STORM && event.type != SeaEventType.HAILSTORM && !cyclone || !event.isActive(time)) {
				continue;
			}
			double inTime = Math.min(time - event.startTime, event.endTime - time) / FADE_TICKS;
			double distance = event.distance(player.getX(), player.getZ());
			double past = distance - event.radius;
			// A cyclone's black wall is seen from twice as far away.
			double inSpace = 1 - past / (cyclone ? EDGE * 2 : EDGE);
			float here = (float) Mth.clamp(Math.min(inTime, inSpace), 0, 1);
			best = Math.max(best, here);
			thunder = Math.max(thunder, cyclone ? here * CYCLONE_DARKNESS : here);
		}
		cachedTick = time;
		cached = best;
		cachedThunder = thunder;
		return best;
	}

	/** How dark and thundery the sky looks: like strength, but a Great Cyclone keeps the sky lighter so its funnel shows. */
	public static float thunder() {
		strength();
		return cachedThunder;
	}
}
