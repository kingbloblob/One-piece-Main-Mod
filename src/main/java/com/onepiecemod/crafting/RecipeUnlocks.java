package com.onepiecemod.crafting;

import java.util.ArrayList;
import java.util.List;

import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;

/**
 * Tells players when a locked station recipe opens up, like "New recipe at the Swordsmith's Forge: Shusui"
 * after beating the right boss. Checks every few seconds; the first check for a player only remembers
 * what is already open, so nobody gets a flood of pop-ups for old unlocks.
 */
public class RecipeUnlocks {
	/** Locked station recipes this player has already been told about (recipe ids). */
	public static final AttachmentType<List<String>> SEEN = AttachmentRegistry.create(
			OnePieceMod.id("station_unlocks_seen"),
			builder -> builder.persistent(Codec.STRING.listOf()).copyOnDeath()
	);

	private static final int CHECK_EVERY_TICKS = 100;

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % CHECK_EVERY_TICKS != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				check(player);
			}
		});
	}

	private static void check(ServerPlayer player) {
		List<String> seen = player.getAttached(SEEN);
		List<String> open = new ArrayList<>();
		for (StationRecipe recipe : StationRecipe.all().values()) {
			if (recipe.requires != null && recipe.lockReason(player) == null) {
				open.add(recipe.id);
			}
		}
		if (seen == null) {
			player.setAttached(SEEN, open);
			return;
		}
		List<String> fresh = new ArrayList<>();
		for (String id : open) {
			if (!seen.contains(id)) {
				fresh.add(id);
			}
		}
		if (fresh.isEmpty()) {
			return;
		}
		List<String> updated = new ArrayList<>(seen);
		updated.addAll(fresh);
		player.setAttached(SEEN, updated);

		for (String id : fresh) {
			StationRecipe recipe = StationRecipe.get(id);
			Station station = recipe.stationType();
			player.sendSystemMessage(Component.literal("New recipe unlocked at the " + (station != null ? station.title() : recipe.station)
					+ ": " + recipe.resultStack().getHoverName().getString()).withStyle(ChatFormatting.GOLD));
		}
		if (ServerPlayNetworking.canSend(player, StationPayloads.Unlocked.TYPE)) {
			ServerPlayNetworking.send(player, new StationPayloads.Unlocked(fresh));
		}
	}
}
