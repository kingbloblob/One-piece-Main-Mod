package com.onepiecemod.crew.client;

import com.mojang.blaze3d.platform.InputConstants;
import org.lwjgl.sdl.SDLScancode;

import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.entity.EntityRenderers;
import net.minecraft.resources.Identifier;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.crew.CrewEntities;
import com.onepiecemod.crew.CrewPayloads;

/**
 * Client-only setup for crewmates. OnePieceModClient calls initialize().
 * U opens the crew window. You can change the key in Options > Controls > Key Binds, under "One Piece: Crew".
 */
public class CrewClient {
	private static final KeyMapping.Category CATEGORY = KeyMapping.Category.register(
			Identifier.fromNamespaceAndPath("onepiece_crew", "crew"));

	public static void initialize() {
		EntityRenderers.register(CrewEntities.CREWMATE, CrewmateRenderer::new);

		KeyMapping openKey = KeyMappingHelper.registerKeyMapping(new KeyMapping(
				"key.onepiece_crew.open", InputConstants.Type.KEYBOARD, SDLScancode.SDL_SCANCODE_U, CATEGORY));
		ClientTickEvents.END_CLIENT_TICK.register(client -> {
			while (openKey.consumeClick()) {
				if (client.player != null && client.gui.screen() == null) {
					ClientPlayNetworking.send(new CrewPayloads.Action("open", "", 0, 0, ""));
				}
			}
		});

		ClientPlayNetworking.registerGlobalReceiver(CrewPayloads.View.TYPE, (payload, context) -> {
			Minecraft client = context.client();
			if (client.gui.screen() instanceof CrewScreen screen) {
				screen.update(payload);
			} else if (payload.open() && client.gui.screen() == null) {
				client.gui.setScreen(new CrewScreen(payload));
			}
		});
		ClientPlayNetworking.registerGlobalReceiver(CrewPayloads.Recruits.TYPE, (payload, context) -> {
			if (context.client().gui.screen() instanceof CrewScreen screen) {
				screen.showRecruits(payload);
			}
		});
	}
}
