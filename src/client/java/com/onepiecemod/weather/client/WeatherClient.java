package com.onepiecemod.weather.client;

import java.util.List;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.weather.SeaEventSync;

/** Keeps this game's copy of the sea events up to date, so a ship you steer feels storms and whirlpools. */
public class WeatherClient {
	public static void initialize() {
		ClientPlayNetworking.registerGlobalReceiver(SeaEventSync.SeaEventsPayload.TYPE,
				(payload, context) -> SeaEventSync.CLIENT_EVENTS = payload.events());
		WeatherVisuals.initialize();
		CycloneRenderer.initialize();
		ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> SeaEventSync.CLIENT_EVENTS = List.of());
	}
}
