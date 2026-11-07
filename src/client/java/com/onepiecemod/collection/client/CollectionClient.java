package com.onepiecemod.collection.client;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.collection.CollectionPayloads;

/** Opens the Collector's Log when the server sends the player's collection. */
public class CollectionClient {
	public static void initialize() {
		ClientPlayNetworking.registerGlobalReceiver(CollectionPayloads.Open.TYPE, (payload, context) ->
				context.client().gui.setScreen(new CollectionScreen(payload)));
	}
}
