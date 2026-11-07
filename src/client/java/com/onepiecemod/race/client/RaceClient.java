package com.onepiecemod.race.client;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.race.RacePayloads;

/**
 * Opens the race picker when the server asks for it.
 */
public class RaceClient {
	/** True when the server asked us to show the picker, but the world is still loading. */
	private static boolean pickerWanted = false;

	public static void initialize() {
		ClientPlayNetworking.registerGlobalReceiver(RacePayloads.OpenPicker.TYPE, (payload, context) -> pickerWanted = true);

		// Wait until the loading screen is gone (and no other screen is open), then show the picker.
		ClientTickEvents.END_CLIENT_TICK.register(client -> {
			if (pickerWanted && client.player != null && client.gui.screen() == null) {
				pickerWanted = false;
				client.gui.setScreen(new RacePickerScreen());
			}
		});
	}
}
