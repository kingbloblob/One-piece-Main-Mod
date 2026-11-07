package com.onepiecemod.advancement;

import java.util.Map;
import java.util.function.Predicate;

import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.PlayerAdvancements;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.OnePieceMod;

/**
 * Grand Line achievements: three advancement tabs (The Grand Line, Hidden Power, A Pirate's Life).
 * The advancements themselves are JSON files in data/onepiece/advancement. The ones that track mod progress
 * (story chapters, Haki, bounty, titles...) are awarded here, by checking every player every 2 seconds.
 * OnePieceMod calls initialize() once while the game loads.
 */
public final class AdvancementFeature {
	private static final int CHECK_EVERY_TICKS = 40;

	private AdvancementFeature() {
	}

	public static void initialize() {
		AdvancementChecks.CHECKS.size(); // Loads the checks now, which registers their saved player data.
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % CHECK_EVERY_TICKS != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				update(server, player);
			}
		});
		ServerLifecycleEvents.SERVER_STARTED.register(AdvancementFeature::warnAboutMissing);
	}

	/** Awards every advancement this player has newly earned. */
	public static void update(MinecraftServer server, ServerPlayer player) {
		PlayerAdvancements progress = player.getAdvancements();
		for (Map.Entry<String, Predicate<ServerPlayer>> entry : AdvancementChecks.CHECKS.entrySet()) {
			AdvancementHolder holder = server.getAdvancements().get(OnePieceMod.id(entry.getKey()));
			if (holder == null || progress.getOrStartProgress(holder).isDone()) {
				continue;
			}
			boolean earned;
			try {
				earned = entry.getValue().test(player);
			} catch (RuntimeException e) {
				// One broken check must never stop the others or crash the server.
				earned = false;
			}
			if (earned) {
				progress.award(holder, "done");
			}
		}
	}

	/** Awards an advancement that is earned by an event rather than a check, like sinking a ship. */
	public static void grant(ServerPlayer player, String id) {
		grant(player, id, "done");
	}

	/** Awards one criterion of an event advancement that has several, like one Seraphim of the four. */
	public static void grant(ServerPlayer player, String id, String criterion) {
		AdvancementHolder holder = player.level().getServer().getAdvancements().get(OnePieceMod.id(id));
		if (holder != null) {
			player.getAdvancements().award(holder, criterion);
		}
	}

	private static void warnAboutMissing(MinecraftServer server) {
		for (String id : AdvancementChecks.CHECKS.keySet()) {
			if (server.getAdvancements().get(OnePieceMod.id(id)) == null) {
				OnePieceMod.LOGGER.warn("Advancement onepiece:{} has a check but no JSON file", id);
			}
		}
	}
}
