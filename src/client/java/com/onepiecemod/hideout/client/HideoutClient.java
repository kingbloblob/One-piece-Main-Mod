package com.onepiecemod.hideout.client;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.hideout.HideoutPayloads;

/**
 * Client-only setup for hideouts. OnePieceModClient calls initialize().
 * Opens (or refreshes) the hideout screen when the server sends the flag's data.
 */
public final class HideoutClient {
	private HideoutClient() {
	}

	public static void initialize() {
		ClientPlayNetworking.registerGlobalReceiver(HideoutPayloads.Sync.TYPE, (payload, context) -> {
			if (payload.open()) {
				context.client().gui.setScreen(new HideoutScreen(payload));
			} else if (context.client().gui.screen() instanceof HideoutScreen screen) {
				screen.refresh(payload);
			}
		});
	}
}
