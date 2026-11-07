package com.onepiecemod.stats.client;

import com.mojang.blaze3d.platform.InputConstants;
import org.lwjgl.sdl.SDLScancode;

import net.minecraft.client.KeyMapping;
import net.minecraft.resources.Identifier;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.stats.StatsData;
import com.onepiecemod.stats.StatsPayloads;

/**
 * Client-only setup for the stat tree. OnePieceModClient calls initialize().
 * K opens the stat tree. You can change the key in Options > Controls > Key Binds, under "One Piece: Stats".
 */
public class StatsClient {
	private static final KeyMapping.Category CATEGORY = KeyMapping.Category.register(
			Identifier.fromNamespaceAndPath("onepiece_stats", "stats"));

	/** The latest stats the server told us about. */
	private static StatsData data = StatsData.EMPTY;

	/** What the Reset button costs right now, in Berries (0 = free). */
	private static int respecCost = 0;

	public static StatsData data() {
		return data;
	}

	public static int respecCost() {
		return respecCost;
	}

	public static void initialize() {
		KeyMapping openKey = KeyMappingHelper.registerKeyMapping(new KeyMapping(
				"key.onepiece_stats.stat_tree", InputConstants.Type.KEYBOARD, SDLScancode.SDL_SCANCODE_K, CATEGORY));

		ClientPlayNetworking.registerGlobalReceiver(StatsPayloads.Sync.TYPE, (payload, context) -> {
			data = payload.toData();
			respecCost = payload.respecCost();
		});
		ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> data = StatsData.EMPTY);

		ClientTickEvents.END_CLIENT_TICK.register(client -> {
			while (openKey.consumeClick()) {
				if (client.player != null && client.gui.screen() == null) {
					client.gui.setScreen(new StatTreeScreen());
				}
			}
		});
	}
}
