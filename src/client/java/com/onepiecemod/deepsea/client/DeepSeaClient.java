package com.onepiecemod.deepsea.client;

import java.util.Locale;

import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.player.LocalPlayer;

import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElement;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.hud.VanillaHudElements;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.deepsea.DeepPressure;
import com.onepiecemod.deepsea.ShipCoating;
import com.onepiecemod.deepsea.ShipDive;
import com.onepiecemod.ship.ShipEntity;

/**
 * Client side of the deep sea: Jump and Sprint dive and surface while you're at the wheel of a submarine or a coated
 * ship, and a depth gauge line above the hotbar while you're aboard one. OnePieceModClient calls initialize().
 * The coated ship's bubble is drawn by ship.client.ShipRenderer.
 */
public final class DeepSeaClient {
	private DeepSeaClient() {
	}

	private static final int GAUGE = 0xFF7FD8FF;
	private static final int WARN = 0xFFFFB347;

	public static void initialize() {
		// The captain's own game steers the ship, so it reads the captain's keys right here.
		ShipDive.diveInput = player -> {
			if (!(player instanceof LocalPlayer local) || Minecraft.getInstance().gui.screen() != null) {
				return 0;
			}
			if (local.input.keyPresses.jump()) {
				return 1;
			}
			return local.input.keyPresses.sprint() || Minecraft.getInstance().options.keySprint.isDown() ? -1 : 0;
		};
		HudElementRegistry.attachElementAfter(VanillaHudElements.CROSSHAIR, OnePieceMod.id("depth_gauge"), new Gauge());
	}

	/** "Depth 34 of 85 · Coating 12:30 · [Space] rise [Ctrl] dive", above the hotbar. */
	private static final class Gauge implements HudElement {
		@Override
		public void extractRenderState(GuiGraphicsExtractor graphics, DeltaTracker deltaTracker) {
			Minecraft client = Minecraft.getInstance();
			if (client.player == null || client.gui.screen() != null) {
				return;
			}
			ShipEntity ship = ShipEntity.aboard(client.player);
			if (ship == null || !ShipDive.canDive(ship)) {
				return;
			}
			int depth = (int) Math.max(0, Math.round(ShipDive.depth(ship)));
			int max = ShipDive.maxDepth(ship);
			StringBuilder text = new StringBuilder();
			text.append(ShipDive.isSubmarine(ship) ? "Submarine" : "Coated ship");
			text.append(String.format(Locale.ROOT, "  Depth %d", depth));
			if (!ShipDive.isCoated(ship)) {
				text.append(" of ").append(max);
			}
			String coating = ShipCoating.describe(ship.coating());
			if (coating != null) {
				text.append("  ").append(coating);
			}
			if (client.player.getVehicle() == ship) {
				text.append("  [").append(client.options.keyJump.getTranslatedKeyMessage().getString()).append("] rise  [")
						.append(client.options.keySprint.getTranslatedKeyMessage().getString()).append("] dive");
			}
			boolean warn = ShipDive.isCoated(ship) ? ship.coating() <= ShipCoating.WARN_TICKS
					: depth >= max - 1;
			if (depth >= DeepPressure.SAFE_DEPTH) {
				text.append("  The deep: don't leave the ship!");
			}
			int width = client.font.width(text.toString());
			graphics.text(client.font, text.toString(), (graphics.guiWidth() - width) / 2, graphics.guiHeight() - 72,
					warn ? WARN : GAUGE, true);
		}
	}
}
