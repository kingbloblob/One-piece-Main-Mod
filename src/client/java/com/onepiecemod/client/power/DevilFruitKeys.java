package com.onepiecemod.client.power;

import org.lwjgl.sdl.SDLScancode;

import net.minecraft.client.KeyMapping;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.power.UseFruitPowerPayload;

/**
 * The Devil Fruit power key. Press R to use your fruit's first move,
 * or sneak (Shift) and press R for the second move. Y uses your awakened form (or shows your progress
 * toward awakening). You can change the keys in Options > Controls.
 */
public class DevilFruitKeys {
	private static final KeyMapping.Category CATEGORY = KeyMapping.Category.register(OnePieceMod.id("devil_fruit"));

	private static final KeyMapping USE_POWER = KeyMappingHelper.registerKeyMapping(new KeyMapping(
			"key.onepiece.use_fruit_power",
			SDLScancode.SDL_SCANCODE_R, // Minecraft 26 reads keys through SDL, so keys are named SDL_SCANCODE_...
			CATEGORY
	));

	private static final KeyMapping AWAKEN = KeyMappingHelper.registerKeyMapping(new KeyMapping(
			"key.onepiece.awaken_fruit",
			SDLScancode.SDL_SCANCODE_Y,
			CATEGORY
	));

	public static void initialize() {
		ClientTickEvents.END_CLIENT_TICK.register(client -> {
			while (USE_POWER.consumeClick()) {
				if (client.player != null) {
					// Tell the server; it decides what actually happens.
					int move = client.player.isShiftKeyDown() ? UseFruitPowerPayload.SECONDARY : UseFruitPowerPayload.PRIMARY;
					ClientPlayNetworking.send(new UseFruitPowerPayload(move));
				}
			}
			while (AWAKEN.consumeClick()) {
				if (client.player != null) {
					ClientPlayNetworking.send(new UseFruitPowerPayload(UseFruitPowerPayload.AWAKENED));
				}
			}
		});
	}
}
