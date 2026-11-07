package com.onepiecemod.dialogue.client;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.dialogue.DialogueFeature;

/**
 * Client-only setup for the talk screen. Each page the server sends either opens the screen
 * or, while you're already talking to that character, replaces what's on it.
 * OnePieceModClient calls initialize().
 */
public class DialogueClient {
	public static void initialize() {
		ClientPlayNetworking.registerGlobalReceiver(DialogueFeature.Page.TYPE, (payload, context) -> {
			if (context.client().gui.screen() instanceof DialogueScreen screen && screen.entityId() == payload.entityId()) {
				screen.show(payload);
			} else {
				context.client().gui.setScreen(new DialogueScreen(payload));
			}
		});
	}
}
