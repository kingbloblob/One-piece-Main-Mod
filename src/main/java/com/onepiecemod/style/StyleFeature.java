package com.onepiecemod.style;

import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

/**
 * Fighting styles: Santoryu, Black Leg, Fish-Man Karate, Rokushiki, Ryusoken, Oden Nitoryu,
 * Kitsunebi-ryu, Soul King Fencing, Fist of Love and Sogeking Sniping. Masters and prices are in FightingStyle.
 * OnePieceMod calls initialize() once while the game loads.
 * The keys (Z and Shift+Z) are set up in style/client/StyleClient.java.
 */
public class StyleFeature {
	public static void initialize() {
		StyleAttachments.initialize();
		StyleItems.initialize();
		StyleMasters.initialize();
		StylePassives.initialize();
		StyleCommands.initialize();

		// Listen for the key presses the player's game sends us.
		PayloadTypeRegistry.serverboundPlay().register(StylePayload.TYPE, StylePayload.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(StylePayload.TYPE,
				(payload, context) -> StyleMoves.handle(context.player(), payload.action()));

		// Cooldowns only matter while you're online.
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> StyleState.forget(handler.player.getUUID()));
	}
}
