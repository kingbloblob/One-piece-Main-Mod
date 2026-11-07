package com.onepiecemod.fruitdex.client;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.fruitdex.FruitdexPayloads;

/**
 * Opens the encyclopedia and plays the first-bite cutscene when the server asks for them.
 */
public class FruitdexClient {
	public static void initialize() {
		ClientPlayNetworking.registerGlobalReceiver(FruitdexPayloads.Open.TYPE, (payload, context) ->
				context.client().gui.setScreen(new FruitdexScreen(payload)));
		ClientPlayNetworking.registerGlobalReceiver(FruitdexPayloads.FirstBite.TYPE, (payload, context) ->
				context.client().gui.setScreen(new FirstBiteScreen(payload.fruitId())));
	}
}
