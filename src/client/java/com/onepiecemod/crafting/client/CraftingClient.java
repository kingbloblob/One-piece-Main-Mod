package com.onepiecemod.crafting.client;

import net.minecraft.client.gui.components.toasts.SystemToast;
import net.minecraft.network.chat.Component;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.crafting.Station;
import com.onepiecemod.crafting.StationPayloads;
import com.onepiecemod.crafting.StationRecipe;

/**
 * Client-only setup for crafting stations. OnePieceModClient calls initialize().
 */
public class CraftingClient {
	/** One pop-up slot for unlocks, so several at once update it instead of stacking up. */
	private static final SystemToast.SystemToastId UNLOCK_TOAST = new SystemToast.SystemToastId();

	public static void initialize() {
		// Sent just before "open this station": that station's upgrade tree for this player.
		ClientPlayNetworking.registerGlobalReceiver(StationPayloads.UpgradeState.TYPE, (payload, context) -> StationScreen.upgradeState = payload);

		// The server says "open this station": show its screen.
		ClientPlayNetworking.registerGlobalReceiver(StationPayloads.OpenStation.TYPE, (payload, context) -> {
			Station station = Station.byId(payload.station());
			if (station != null) {
				context.client().gui.setScreen(new StationScreen(payload.pos(), station, payload.lockReasons()));
			}
		});

		// The server says "these station recipes just unlocked": show a pop-up in the corner.
		ClientPlayNetworking.registerGlobalReceiver(StationPayloads.Unlocked.TYPE, (payload, context) -> {
			if (payload.recipes().isEmpty()) {
				return;
			}
			Component body;
			StationRecipe first = StationRecipe.get(payload.recipes().get(0));
			if (payload.recipes().size() == 1 && first != null && first.stationType() != null) {
				body = Component.literal(first.resultStack().getHoverName().getString() + " at the " + first.stationType().title());
			} else {
				body = Component.literal(payload.recipes().size() + " new station recipes. See chat.");
			}
			SystemToast.addOrUpdate(context.client().gui.toastManager(), UNLOCK_TOAST, Component.literal("New recipe unlocked!"), body);
		});
	}
}
