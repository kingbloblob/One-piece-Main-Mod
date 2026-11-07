package com.onepiecemod.questtree.client;

import org.lwjgl.sdl.SDLScancode;

import net.minecraft.client.KeyMapping;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.questtree.QuestTreeFeature;

/**
 * Client-only setup for the quest tree. Press J (change it in Options > Controls) or type /quests.
 * It also shows in a panel to the left of the inventory (QuestTreePanel).
 * The key only asks the server for your progress; the screen opens when the answer arrives.
 * OnePieceModClient calls initialize().
 */
public class QuestTreeClient {
	private static final KeyMapping.Category CATEGORY = KeyMapping.Category.register(OnePieceMod.id("quests"));

	private static final KeyMapping OPEN = KeyMappingHelper.registerKeyMapping(new KeyMapping(
			"key.onepiece.quest_tree",
			SDLScancode.SDL_SCANCODE_J, // J for "journal". R, Y, V, B, G, Z, L, U and K are already used.
			CATEGORY
	));

	public static void initialize() {
		// The answer fills the inventory panel if that's what asked, otherwise it opens the big screen.
		ClientPlayNetworking.registerGlobalReceiver(QuestTreeFeature.Open.TYPE, (payload, context) -> {
			if (QuestTreePanel.waiting) {
				QuestTreePanel.receive(payload);
			} else {
				context.client().gui.setScreen(new QuestTreeScreen(payload));
			}
		});
		QuestTreePanel.initialize();

		ClientTickEvents.END_CLIENT_TICK.register(client -> {
			while (OPEN.consumeClick()) {
				if (client.player != null && client.gui.screen() == null) {
					QuestTreePanel.waiting = false; // This answer should open the big screen.
					ClientPlayNetworking.send(QuestTreeFeature.Request.INSTANCE);
				}
			}
		});
	}
}
