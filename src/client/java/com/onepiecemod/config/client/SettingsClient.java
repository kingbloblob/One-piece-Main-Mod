package com.onepiecemod.config.client;

import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.PauseScreen;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.network.chat.Component;

import net.fabricmc.fabric.api.client.screen.v1.ScreenEvents;
import net.fabricmc.fabric.api.client.screen.v1.Screens;

import com.onepiecemod.hud.client.KeysScreen;

/**
 * Puts "One Piece Keys" and "One Piece Settings" buttons in the bottom left corner of the pause menu,
 * and a "One Piece Settings" button in the top left corner of the title screen. On a server the
 * settings screen opens on its HUD tab, since the server's own settings count for the rest.
 */
public class SettingsClient {
	public static void initialize() {
		ScreenEvents.AFTER_INIT.register((client, screen, width, height) -> {
			if (screen instanceof PauseScreen pause && pause.showsPauseMenu()) {
				Screens.getWidgets(screen).add(Button.builder(Component.literal("One Piece Keys"),
						b -> client.gui.setScreen(new KeysScreen(screen))).pos(4, height - 48).size(110, 20).build());
				Screens.getWidgets(screen).add(Button.builder(Component.literal("One Piece Settings"),
						b -> client.gui.setScreen(new SettingsScreen(screen))).pos(4, height - 24).size(110, 20).build());
			} else if (screen instanceof TitleScreen) {
				Screens.getWidgets(screen).add(Button.builder(Component.literal("One Piece Settings"),
						b -> client.gui.setScreen(new SettingsScreen(screen))).pos(4, 4).size(110, 20).build());
			}
		});
	}
}
