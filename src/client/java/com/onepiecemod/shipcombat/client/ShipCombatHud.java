package com.onepiecemod.shipcombat.client;

import java.util.Locale;

import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;

import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElement;

import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.shipcombat.Cannons;

/**
 * One line under the crosshair while you're aboard a ship with cannons: how many guns face where you look,
 * which ammo they'll load and how much you have, and whether they're ready or still reloading.
 */
public class ShipCombatHud implements HudElement {
	private static final int READY = 0xFF7CFC6A;
	private static final int WAIT = 0xFFB0B0B0;
	private static final int NONE = 0xFFFFC857;

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, DeltaTracker deltaTracker) {
		Minecraft client = Minecraft.getInstance();
		if (client.player == null || client.gui.screen() != null) {
			return;
		}
		ShipEntity ship = ShipEntity.aboard(client.player);
		if (ship == null || Cannons.guns(ship).isEmpty()) {
			return;
		}
		int facing = Cannons.gunsFacing(ship, client.player.getViewVector(1.0f)).size();
		Cannons.Loaded ammo = Cannons.loaded(client.player);
		int count = ammo.count();
		long left = ShipCombatClient.reloadLeft(client, ship);

		String text;
		int color;
		if (facing == 0) {
			text = "No cannons face this way";
			color = WAIT;
		} else if (left > 0) {
			text = String.format(Locale.ROOT, "Reloading %.1fs", left / 20.0);
			color = WAIT;
		} else {
			text = facing + (facing == 1 ? " cannon" : " cannons") + " ready: " + ammo.title() + " x" + (client.player.isCreative() ? "∞" : count) + "  [" + ShipCombatClient.FIRE_CANNONS.getTranslatedKeyMessage().getString() + "]";
			color = count > 0 || client.player.isCreative() ? READY : NONE;
		}
		int width = client.font.width(text);
		graphics.text(client.font, text, (graphics.guiWidth() - width) / 2, graphics.guiHeight() / 2 + 14, color, true);
	}
}
