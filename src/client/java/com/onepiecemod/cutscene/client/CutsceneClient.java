package com.onepiecemod.cutscene.client;

import java.util.ArrayDeque;
import java.util.Deque;

import com.mojang.blaze3d.platform.InputConstants;
import org.lwjgl.sdl.SDLScancode;

import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.hud.VanillaHudElements;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.cutscene.CutsceneFeature;
import com.onepiecemod.questlog.client.ClientConfig;

/**
 * Client side of boss intros and flashbacks: keeps the cutscene that is playing (and any waiting behind it),
 * the "Skip cutscene" key (Enter), and the gentle camera turn toward a boss.
 * The drawing is in CutsceneOverlay. OnePieceModClient calls initialize().
 */
public final class CutsceneClient {
	private static final KeyMapping.Category CATEGORY = KeyMapping.Category.register(OnePieceMod.id("cutscenes"));

	/** A cutscene on screen: the packet plus how far into it we are (ticks; negative while its delay runs). */
	static final class Playing {
		final CutsceneFeature.Play play;
		int age;
		boolean ending;
		int endAge;

		Playing(CutsceneFeature.Play play) {
			this.play = play;
			this.age = -play.delay();
		}

		/** 0..1 for the cinema bars sliding in and out. */
		float bars(float partial) {
			float t = age + partial;
			float in = Math.min(1f, Math.max(0f, t / 10f));
			if (ending) {
				return Math.min(in, Math.max(0f, 1f - (t - endAge) / 8f));
			}
			return in;
		}

		boolean done() {
			return ending && age - endAge > 8;
		}
	}

	private static Playing current;
	private static final Deque<CutsceneFeature.Play> QUEUE = new ArrayDeque<>();
	private static KeyMapping skip;

	static Playing current() {
		return current;
	}

	static KeyMapping skipKey() {
		return skip;
	}

	public static void initialize() {
		skip = KeyMappingHelper.registerKeyMapping(new KeyMapping(
				"key.onepiece.skip_cutscene", InputConstants.Type.KEYBOARD, SDLScancode.SDL_SCANCODE_RETURN, CATEGORY));

		ClientPlayNetworking.registerGlobalReceiver(CutsceneFeature.Play.TYPE, (payload, context) -> receive(payload));
		ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> {
			current = null;
			QUEUE.clear();
		});

		ClientTickEvents.END_CLIENT_TICK.register(CutsceneClient::tick);
		HudElementRegistry.attachElementAfter(VanillaHudElements.CHAT, OnePieceMod.id("cutscene"), new CutsceneOverlay());
	}

	private static void receive(CutsceneFeature.Play play) {
		if (!wanted(play.kind())) {
			// Turned off: tell the server straight away, so a boss doesn't stand around waiting for us.
			if (play.kind() == CutsceneFeature.BOSS_INTRO) {
				ClientPlayNetworking.send(CutsceneFeature.Skip.INSTANCE);
			}
			return;
		}
		if (play.kind() == CutsceneFeature.BOSS_INTRO) {
			// A fight is starting: it goes first, and anything quieter waits.
			if (current != null && current.play.kind() != CutsceneFeature.BOSS_INTRO) {
				QUEUE.addFirst(current.play);
			}
			current = new Playing(play);
		} else if (current == null) {
			current = new Playing(play);
		} else if (QUEUE.size() < 8) {
			QUEUE.addLast(play);
		}
	}

	private static boolean wanted(int kind) {
		String setting = ClientConfig.get(ClientConfig.CUTSCENES);
		return switch (setting) {
			case "off" -> false;
			case "bosses_only" -> kind == CutsceneFeature.BOSS_INTRO;
			case "flashbacks_only" -> kind == CutsceneFeature.FLASHBACK;
			default -> true;
		};
	}

	private static void tick(Minecraft client) {
		boolean pressed = false;
		while (skip.consumeClick()) {
			pressed = true;
		}
		if (current == null) {
			return;
		}
		if (client.player == null) {
			current = null;
			QUEUE.clear();
			return;
		}
		if (client.isPaused() || current.play.kind() == CutsceneFeature.FLASHBACK && client.gui.screen() != null) {
			return; // A flashback waits while a screen is open (race picker, death screen, inventory), so you never miss it.
		}
		current.age++;
		if (!current.ending && current.age >= 0 && (current.age >= current.play.ticks()
				|| pressed && client.gui.screen() == null)) {
			end();
		}
		if (current.done()) {
			current = QUEUE.isEmpty() ? null : new Playing(QUEUE.pollFirst());
		}
	}

	/** Starts the bars sliding out. For a boss intro, tells the server we're done watching. */
	private static void end() {
		current.ending = true;
		current.endAge = current.age;
		if (current.play.kind() == CutsceneFeature.BOSS_INTRO) {
			ClientPlayNetworking.send(CutsceneFeature.Skip.INSTANCE);
		}
	}

	/** Last frame's time, for frame-rate independent camera turning. */
	private static long lastFrame;

	/**
	 * Turns the view a little toward the boss each frame during the first part of its intro.
	 * The player can still look around with the mouse; this only nudges.
	 */
	static void turnCamera(Minecraft client, Playing playing) {
		long now = System.nanoTime();
		float seconds = lastFrame == 0 ? 0f : Math.min(0.1f, (now - lastFrame) / 1.0e9f);
		lastFrame = now;
		if (playing.play.kind() != CutsceneFeature.BOSS_INTRO || playing.ending || playing.age > playing.play.ticks() * 0.6f
				|| playing.play.entity() < 0 || client.level == null || client.player == null
				|| !ClientConfig.is(ClientConfig.CUTSCENE_CAMERA, "on") || client.gui.screen() != null) {
			return;
		}
		Entity boss = client.level.getEntity(playing.play.entity());
		if (boss == null) {
			return;
		}
		Vec3 eye = client.player.getEyePosition();
		Vec3 look = boss.position().add(0, boss.getBbHeight() * 0.8, 0).subtract(eye);
		double flat = Math.sqrt(look.x * look.x + look.z * look.z);
		if (flat < 0.5) {
			return;
		}
		float wantYaw = (float) (Math.toDegrees(Math.atan2(look.z, look.x)) - 90.0);
		float wantPitch = (float) -Math.toDegrees(Math.atan2(look.y, flat));
		wantPitch = Math.max(-40f, Math.min(40f, wantPitch));
		float dYaw = wrap(wantYaw - client.player.getYRot());
		float dPitch = wantPitch - client.player.getXRot();
		float k = Math.min(1f, seconds * 4f);
		// Entity.turn multiplies by 0.15 (it's made for mouse input), so divide that back out.
		client.player.turn(dYaw * k / 0.15, dPitch * k / 0.15);
	}

	static void resetFrameClock() {
		lastFrame = 0;
	}

	private static float wrap(float degrees) {
		degrees %= 360f;
		if (degrees >= 180f) {
			degrees -= 360f;
		}
		if (degrees < -180f) {
			degrees += 360f;
		}
		return degrees;
	}

	private CutsceneClient() {
	}
}
