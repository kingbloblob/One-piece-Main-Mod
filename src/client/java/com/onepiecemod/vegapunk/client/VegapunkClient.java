package com.onepiecemod.vegapunk.client;

import com.mojang.blaze3d.platform.InputConstants;
import org.lwjgl.sdl.SDLScancode;

import net.minecraft.client.KeyMapping;
import net.minecraft.resources.Identifier;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.vegapunk.Cyborg;
import com.onepiecemod.vegapunk.CyborgData;
import com.onepiecemod.vegapunk.VegapunkPayloads;

/**
 * Client side of the cyborg upgrades. C fires the Radical Beam, Sneak + C the Coup de Vent.
 * The key can be changed in Options > Controls > Key Binds, under "One Piece: Cyborg".
 */
public class VegapunkClient {
	private static final KeyMapping.Category CATEGORY = KeyMapping.Category.register(
			Identifier.fromNamespaceAndPath("onepiece_cyborg", "cyborg"));

	public static void initialize() {
		KeyMapping fire = KeyMappingHelper.registerKeyMapping(new KeyMapping(
				"key.onepiece_cyborg.fire", InputConstants.Type.KEYBOARD, SDLScancode.SDL_SCANCODE_C, CATEGORY));

		ClientPlayNetworking.registerGlobalReceiver(VegapunkPayloads.Sync.TYPE,
				(payload, context) -> Cyborg.clientData = new CyborgData(java.util.Map.copyOf(payload.tiers()), payload.fuel()));
		ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> Cyborg.clientData = CyborgData.EMPTY);

		ClientTickEvents.END_CLIENT_TICK.register(client -> {
			while (fire.consumeClick()) {
				if (client.player != null && client.gui.screen() == null && Cyborg.clientData.any()) {
					ClientPlayNetworking.send(new VegapunkPayloads.Use(client.player.isShiftKeyDown()));
				}
			}
		});
	}
}
