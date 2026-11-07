package com.onepiecemod.questlog.client;

import com.mojang.blaze3d.platform.InputConstants;
import org.lwjgl.sdl.SDLScancode;

import net.minecraft.client.KeyMapping;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.hud.VanillaHudElements;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.questlog.QuestLogFeature;

/**
 * Client-only setup for the quest journal (O key, or /questlog) and the compass bar at the top of the screen.
 * The key asks the server for your quests; the journal opens when the answer arrives.
 * OnePieceModClient calls initialize().
 */
public class QuestLogClient {
	private static final KeyMapping.Category CATEGORY = KeyMapping.Category.register(OnePieceMod.id("quest_journal"));

	/** The latest compass bar data from the server, or null on servers without the mod. */
	private static QuestLogFeature.Nav nav;

	public static QuestLogFeature.Nav nav() {
		return nav;
	}

	public static void initialize() {
		ClientConfig.load();

		KeyMapping open = KeyMappingHelper.registerKeyMapping(new KeyMapping(
				"key.onepiece.quest_journal", InputConstants.Type.KEYBOARD, SDLScancode.SDL_SCANCODE_O, CATEGORY));

		ClientPlayNetworking.registerGlobalReceiver(QuestLogFeature.Open.TYPE,
				(payload, context) -> context.client().gui.setScreen(new QuestJournalScreen(payload)));
		ClientPlayNetworking.registerGlobalReceiver(QuestLogFeature.Nav.TYPE, (payload, context) -> nav = payload);
		ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> nav = null);

		ClientTickEvents.END_CLIENT_TICK.register(client -> {
			freeTheOKey(client, open);
			while (open.consumeClick()) {
				if (client.player != null && client.gui.screen() == null) {
					ClientPlayNetworking.send(QuestLogFeature.Request.INSTANCE);
				}
			}
		});

		HudElementRegistry.attachElementBefore(VanillaHudElements.CHAT, OnePieceMod.id("navigation"), new NavigationOverlay());
	}

	/**
	 * Minecraft 26.3 opens its own Friends List with O, which swallowed the journal key (the Friends List screen
	 * opened first, so the journal never did). Once per computer, if both are still on the same key, the Friends
	 * List is unbound (it can be bound again under Options > Controls). A marker file keeps it from happening twice,
	 * so a player who puts the Friends List back on O keeps it there.
	 */
	private static void freeTheOKey(net.minecraft.client.Minecraft client, KeyMapping journal) {
		if (keyChecked || client.options == null) {
			return;
		}
		keyChecked = true;
		java.nio.file.Path marker = net.fabricmc.loader.api.FabricLoader.getInstance().getConfigDir().resolve("onepiece-journal-key.done");
		if (java.nio.file.Files.exists(marker)) {
			return;
		}
		KeyMapping friends = client.options.keyFriends;
		if (!journal.isUnbound() && journal.same(friends)) {
			friends.setKey(InputConstants.UNKNOWN);
			KeyMapping.resetMapping();
			client.options.save();
			OnePieceMod.LOGGER.info("Unbound the Friends List key so {} opens the quest journal", journal.getTranslatedKeyMessage().getString());
		}
		try {
			java.nio.file.Files.createDirectories(marker.getParent());
			java.nio.file.Files.writeString(marker, "The Friends List key was moved off the quest journal key once. Delete this file to check again.\n");
		} catch (java.io.IOException e) {
			OnePieceMod.LOGGER.warn("Couldn't write {}", marker, e);
		}
	}

	private static boolean keyChecked = false;

	/** Tells the server which quest to show under the compass, and updates the bar straight away. */
	static void track(String key) {
		ClientPlayNetworking.send(new QuestLogFeature.Track(key));
		if (nav != null) {
			nav = new QuestLogFeature.Nav(nav.sea(), nav.logPose(), nav.hasTarget(), nav.targetX(), nav.targetZ(),
					nav.targetBiome(), nav.recording(), nav.recordNeeded(), nav.islands(), key, false);
		}
	}
}
