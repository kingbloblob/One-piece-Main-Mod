package com.onepiecemod.tutorial.client;

import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.tutorial.TutorialSteps;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.screen.v1.ScreenEvents;

import com.onepiecemod.body.client.BodyEditorScreen;
import com.onepiecemod.hud.client.HudClient;
import com.onepiecemod.hud.client.KeysScreen;
import com.onepiecemod.journal.client.JournalScreen;
import com.onepiecemod.questtree.client.QuestTreeScreen;
import com.onepiecemod.race.client.RacePickerScreen;
import com.onepiecemod.tutorial.TutorialFeature;
import com.onepiecemod.tutorial.TutorialStep;

/**
 * Client side of the First Voyage guide: keeps what the server last sent, draws the panel in the
 * inventory screen (TutorialOverlay), and tells the server when the player opens the Crafter's Journal,
 * the quest tree or the One Piece Keys list, or changes the HUD size, since only the game itself can see those.
 * OnePieceModClient calls initialize().
 */
public class TutorialClient {
	/** The latest guide data, or null on servers without the mod. */
	private static TutorialFeature.Sync data;
	/** When the current step started showing (in client ticks), so its hint can fold away after a while. */
	private static long stepShownAt;
	private static long ticks;
	private static HudClient.Mode lastHudMode;

	public static TutorialFeature.Sync data() {
		return data;
	}

	/** Ticks since the current step appeared. */
	public static long ticksOnStep() {
		return ticks - stepShownAt;
	}

	public static void initialize() {
		ClientPlayNetworking.registerGlobalReceiver(TutorialFeature.Sync.TYPE, (payload, context) -> {
			if (data == null && payload.step() >= TutorialStep.COUNT) {
				stepShownAt = ticks - 1_000_000; // Finished long ago: don't cheer again on every login.
			} else if (data == null || data.step() != payload.step() || data.off() != payload.off()) {
				stepShownAt = ticks;
			}
			data = payload;
		});
		ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> data = null);
		// The mod has its own First Voyage guide, so the vanilla "use WASD / punch a tree" popups are switched off:
		// they sat right on top of the race picker and body editor buttons (playtest 2026-11-01).
		ClientPlayConnectionEvents.JOIN.register((handler, sender, client) -> {
			if (client.options.tutorialStep != TutorialSteps.NONE) {
				client.getTutorial().setStep(TutorialSteps.NONE);
			}
		});

		ScreenEvents.AFTER_INIT.register((client, screen, scaledWidth, scaledHeight) -> {
			if (screen instanceof RacePickerScreen || screen instanceof BodyEditorScreen) {
				client.gui.toastManager().clear(); // no popup over the Confirm / Done buttons
			} else if (screen instanceof JournalScreen) {
				seen("journal");
			} else if (screen instanceof QuestTreeScreen) {
				seen("quests");
			} else if (screen instanceof KeysScreen) {
				seen("keys");
			}
		});

		ClientTickEvents.END_CLIENT_TICK.register(client -> {
			ticks++;
			HudClient.Mode mode = HudClient.mode();
			if (lastHudMode != null && mode != lastHudMode) {
				seen("hud");
			}
			lastHudMode = mode;
		});

		// The panel is drawn in the inventory screen, not on the game screen (ryan asked 2026-10-29).
		TutorialOverlay.initialize();
	}

	private static void seen(String what) {
		if (data != null && ClientPlayNetworking.canSend(TutorialFeature.Seen.TYPE)) {
			ClientPlayNetworking.send(new TutorialFeature.Seen(what));
		}
	}

	/** The key currently bound to this key bind, like "J", or "-" if nothing is bound. */
	static String keyName(String name) {
		for (KeyMapping mapping : Minecraft.getInstance().options.keyMappings) {
			if (mapping.getName().equals(name)) {
				return mapping.isUnbound() ? "(unbound key)" : mapping.getTranslatedKeyMessage().getString();
			}
		}
		return "?";
	}
}
