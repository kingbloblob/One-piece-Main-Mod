package com.onepiecemod.haki.client;

import java.util.HashMap;
import java.util.Map;

import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.Entity;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.haki.HakiSensePayload;

/**
 * Remembers which creatures your Observation Haki is sensing right now, so only you see them glow.
 * The server sends the list twice a second while you sneak; each entry fades 15 ticks later.
 */
public class HakiSenseClient {
	private static final int GLOW_TICKS = 15;
	private static final Map<Integer, Long> GLOWING_UNTIL = new HashMap<>();

	public static void initialize() {
		ClientPlayNetworking.registerGlobalReceiver(HakiSensePayload.TYPE, (payload, context) -> {
			long until = gameTime() + GLOW_TICKS;
			for (int id : payload.entityIds()) {
				GLOWING_UNTIL.put(id, until);
			}
		});
	}

	/** Called by MinecraftGlowMixin for every entity drawn. */
	public static boolean isSensed(Entity entity) {
		if (GLOWING_UNTIL.isEmpty()) {
			return false;
		}
		long now = gameTime();
		GLOWING_UNTIL.values().removeIf(until -> until < now);
		return GLOWING_UNTIL.containsKey(entity.getId());
	}

	private static long gameTime() {
		Minecraft client = Minecraft.getInstance();
		return client.level == null ? 0 : client.level.getGameTime();
	}
}
