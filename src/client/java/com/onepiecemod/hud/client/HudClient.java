package com.onepiecemod.hud.client;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;

import com.mojang.blaze3d.platform.InputConstants;
import org.lwjgl.sdl.SDLScancode;

import net.minecraft.ChatFormatting;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.Component;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.hud.VanillaHudElements;
import net.fabricmc.loader.api.FabricLoader;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.hud.HudPayload;

/**
 * Client-only setup for the HUD in the bottom-right corner. OnePieceModClient calls initialize().
 * H switches it between Full (with key reminders), Small and Off. You can change the key in
 * Options > Controls > Key Binds, under "HUD". The choice is saved in config/onepiece-hud.txt.
 */
public class HudClient {
	public enum Mode { FULL, SMALL, OFF }

	/** Which corner the HUD sits in. Bottom right (beside the hotbar) is the default. */
	public enum Position { BOTTOM_RIGHT, BOTTOM_LEFT, TOP_LEFT }

	/** How big the HUD is drawn, on top of the automatic size for your GUI scale. */
	public enum Size {
		SMALL(0.75f), NORMAL(1f), LARGE(1.25f);

		public final float factor;

		Size(float factor) {
			this.factor = factor;
		}
	}

	private static final KeyMapping.Category CATEGORY = KeyMapping.Category.register(OnePieceMod.id("hud"));
	private static final Path CONFIG = FabricLoader.getInstance().getConfigDir().resolve("onepiece-hud.txt");

	/** The latest HUD data the server sent, or null on servers without the mod. */
	private static HudPayload data;
	/** The game time when that data arrived, so cooldowns can count down smoothly between updates. */
	private static long receivedAt;
	private static Mode mode = Mode.FULL;
	private static Position position = Position.BOTTOM_RIGHT;
	private static Size size = Size.NORMAL;

	public static HudPayload data() {
		return data;
	}

	/** Ticks since the last HUD data arrived (fractional, for smooth countdowns). */
	public static float ticksSinceData(float partialTick) {
		Minecraft client = Minecraft.getInstance();
		return client.level == null ? 0 : Math.max(0, client.level.getGameTime() - receivedAt + partialTick);
	}

	public static Mode mode() {
		return mode;
	}

	public static Position position() {
		return position;
	}

	public static Size size() {
		return size;
	}

	/** For the One Piece Settings screen: step to the next choice and save it. */
	public static void cycleMode() {
		mode = Mode.values()[(mode.ordinal() + 1) % Mode.values().length];
		save();
	}

	/** Back to the full HUD in the bottom-right corner at normal size. */
	public static void reset() {
		mode = Mode.FULL;
		position = Position.BOTTOM_RIGHT;
		size = Size.NORMAL;
		save();
	}

	public static void cyclePosition() {
		position = Position.values()[(position.ordinal() + 1) % Position.values().length];
		save();
	}

	public static void cycleSize() {
		size = Size.values()[(size.ordinal() + 1) % Size.values().length];
		save();
	}

	public static void initialize() {
		load();

		KeyMapping toggleKey = KeyMappingHelper.registerKeyMapping(new KeyMapping(
				"key.onepiece.toggle_hud", InputConstants.Type.KEYBOARD, SDLScancode.SDL_SCANCODE_H, CATEGORY));

		ClientPlayNetworking.registerGlobalReceiver(HudPayload.TYPE, (payload, context) -> {
			data = payload;
			receivedAt = context.client().level != null ? context.client().level.getGameTime() : 0;
		});
		ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> data = null);

		ClientTickEvents.END_CLIENT_TICK.register(client -> {
			while (toggleKey.consumeClick()) {
				cycleMode();
				if (client.player != null) {
					String name = switch (mode) {
						case FULL -> "Full";
						case SMALL -> "Small";
						case OFF -> "Off";
					};
					client.player.sendOverlayMessage(Component.literal("HUD: " + name).withStyle(ChatFormatting.GOLD));
				}
			}
		});

		// Drawn just before chat, so chat stays on top of it.
		HudElementRegistry.attachElementBefore(VanillaHudElements.CHAT, OnePieceMod.id("hud"), new HudOverlay());

		// While the HUD is showing, lift the chat so it sits above the HUD instead of on top of it.
		// When you open chat to type, the HUD hides and the chat goes back to its normal place.
		HudElementRegistry.replaceElement(VanillaHudElements.CHAT, chat -> (graphics, deltaTracker) -> {
			int lift = HudOverlay.chatLift();
			if (lift <= 0) {
				chat.extractRenderState(graphics, deltaTracker);
				return;
			}
			graphics.pose().pushMatrix();
			graphics.pose().translate(0, -lift);
			chat.extractRenderState(graphics, deltaTracker);
			graphics.pose().popMatrix();
		});
	}

	/**
	 * Reads config/onepiece-hud.txt: lines like "mode=full", "position=top_left", "size=large".
	 * Older versions saved only the mode as one word, which still works.
	 */
	private static void load() {
		try {
			if (!Files.exists(CONFIG)) {
				return;
			}
			for (String line : Files.readAllLines(CONFIG)) {
				line = line.trim().toUpperCase(Locale.ROOT);
				if (line.isEmpty() || line.startsWith("#")) {
					continue;
				}
				int eq = line.indexOf('=');
				String key = eq < 0 ? "MODE" : line.substring(0, eq).trim();
				String value = eq < 0 ? line : line.substring(eq + 1).trim();
				try {
					switch (key) {
						case "MODE" -> mode = Mode.valueOf(value);
						case "POSITION" -> position = Position.valueOf(value);
						case "SIZE" -> size = Size.valueOf(value);
						default -> { }
					}
				} catch (IllegalArgumentException e) {
					OnePieceMod.LOGGER.warn("Ignoring unknown HUD setting '{}' in {}", line, CONFIG);
				}
			}
		} catch (Exception e) {
			OnePieceMod.LOGGER.warn("Could not read {}, using the default HUD", CONFIG);
		}
	}

	private static void save() {
		try {
			Files.writeString(CONFIG, "# One Piece HUD. mode: full / small / off, position: bottom_right / bottom_left / top_left, size: small / normal / large\n"
					+ "mode=" + mode.name().toLowerCase(Locale.ROOT) + "\n"
					+ "position=" + position.name().toLowerCase(Locale.ROOT) + "\n"
					+ "size=" + size.name().toLowerCase(Locale.ROOT) + "\n");
		} catch (Exception e) {
			OnePieceMod.LOGGER.warn("Could not save {}", CONFIG);
		}
	}
}
