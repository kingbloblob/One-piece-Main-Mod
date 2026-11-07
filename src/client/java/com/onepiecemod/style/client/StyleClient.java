package com.onepiecemod.style.client;

import com.mojang.blaze3d.platform.InputConstants;
import org.lwjgl.sdl.SDLScancode;

import net.minecraft.client.KeyMapping;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.resources.Identifier;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.style.StylePayload;

/**
 * Client-only setup for fighting styles. OnePieceModClient calls initialize().
 * Z uses your selected technique, Shift+Z picks the next one. You can change the key in
 * Options > Controls > Key Binds, under "One Piece: Fighting Styles".
 * Pressing jump in mid-air also tells the server, for Geppo and Sky Walk.
 */
public class StyleClient {
	private static final KeyMapping.Category CATEGORY = KeyMapping.Category.register(
			Identifier.fromNamespaceAndPath("onepiece_styles", "fighting_styles"));

	private static boolean jumpWasDown;
	/** Ticks the player has been off the ground. A normal jump leaves the ground this tick, so it isn't an air jump. */
	private static int ticksInAir;

	public static void initialize() {
		KeyMapping techniqueKey = KeyMappingHelper.registerKeyMapping(new KeyMapping(
				"key.onepiece_styles.technique", InputConstants.Type.KEYBOARD, SDLScancode.SDL_SCANCODE_Z, CATEGORY));

		ClientTickEvents.END_CLIENT_TICK.register(client -> {
			LocalPlayer player = client.player;
			if (player == null || !ClientPlayNetworking.canSend(StylePayload.TYPE)) {
				return;
			}

			while (techniqueKey.consumeClick()) {
				ClientPlayNetworking.send(new StylePayload(player.isShiftKeyDown() ? StylePayload.NEXT : StylePayload.USE));
			}

			// Only the moment jump is pressed counts, not holding it down.
			boolean jumpDown = client.options.keyJump.isDown();
			if (jumpDown && !jumpWasDown && ticksInAir > 0 && client.gui.screen() == null && !player.onGround() && !player.isInWater()
					&& !player.getAbilities().flying && !player.isPassenger()) {
				ClientPlayNetworking.send(new StylePayload(StylePayload.AIR_JUMP));
			}
			jumpWasDown = jumpDown;
			ticksInAir = player.onGround() ? 0 : ticksInAir + 1;
		});
	}
}
