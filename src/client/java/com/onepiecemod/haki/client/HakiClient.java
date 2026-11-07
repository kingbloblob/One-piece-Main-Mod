package com.onepiecemod.haki.client;

import org.lwjgl.sdl.SDLScancode;

import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;

import com.onepiecemod.OnePieceMod;

/**
 * The Haki keys. Each one just types the matching /haki command for you, so all the real work
 * happens on the server in HakiPowers. You can change the keys in Options > Controls > Key Binds > Haki.
 */
public class HakiClient {
	private static final KeyMapping.Category CATEGORY = KeyMapping.Category.register(OnePieceMod.id("haki"));

	private static KeyMapping observation;
	private static KeyMapping armament;
	private static KeyMapping conqueror;

	public static void initialize() {
		HakiSenseClient.initialize();
		observation = register("key.onepiece.observation_haki", SDLScancode.SDL_SCANCODE_V);
		armament = register("key.onepiece.armament_haki", SDLScancode.SDL_SCANCODE_B);
		conqueror = register("key.onepiece.conquerors_haki", SDLScancode.SDL_SCANCODE_G);

		ClientTickEvents.END_CLIENT_TICK.register(client -> {
			while (observation.consumeClick()) {
				send(client, "haki observation");
			}
			while (armament.consumeClick()) {
				send(client, "haki armament");
			}
			while (conqueror.consumeClick()) {
				send(client, "haki conqueror");
			}
		});
	}

	private static KeyMapping register(String name, int key) {
		return KeyMappingHelper.registerKeyMapping(new KeyMapping(name, key, CATEGORY));
	}

	private static void send(Minecraft client, String command) {
		if (client.player != null) {
			client.player.connection.sendCommand(command);
		}
	}
}
