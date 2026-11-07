package com.onepiecemod.style;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import com.mojang.serialization.Codec;

import net.minecraft.world.entity.player.Player;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;

/**
 * Remembers which fighting styles each player knows and which one they're using.
 * Saved with the world and kept when they die.
 */
public class StyleAttachments {
	/** Every style the player has learned, like ["santoryu", "rokushiki"]. */
	public static final AttachmentType<List<String>> KNOWN_STYLES = AttachmentRegistry.create(
			OnePieceMod.id("known_styles"),
			builder -> builder
					.persistent(Codec.STRING.listOf())
					.copyOnDeath()
	);

	/** The style the player is fighting with right now. */
	public static final AttachmentType<String> ACTIVE_STYLE = AttachmentRegistry.create(
			OnePieceMod.id("active_style"),
			builder -> builder
					.persistent(Codec.STRING)
					.copyOnDeath()
	);

	/** Which of the active style's moves Z uses (0 = the first one). */
	public static final AttachmentType<Integer> SELECTED_TECHNIQUE = AttachmentRegistry.create(
			OnePieceMod.id("selected_technique"),
			builder -> builder
					.persistent(Codec.INT)
					.copyOnDeath()
	);

	/** When each move can be used again (move name -> game time in ticks). Saved so relogging doesn't skip cooldowns. */
	public static final AttachmentType<Map<String, Long>> COOLDOWNS = AttachmentRegistry.create(
			OnePieceMod.id("style_cooldowns"),
			builder -> builder
					.persistent(Codec.unboundedMap(Codec.STRING, Codec.LONG))
					.copyOnDeath()
	);

	/** Mastery points per style (style id -> points). See StyleMastery. */
	public static final AttachmentType<Map<String, Integer>> MASTERY = AttachmentRegistry.create(
			OnePieceMod.id("style_mastery"),
			builder -> builder
					.persistent(Codec.unboundedMap(Codec.STRING, Codec.INT))
					.copyOnDeath()
	);

	public static boolean knows(Player player, FightingStyle style) {
		return player.getAttachedOrElse(KNOWN_STYLES, List.<String>of()).contains(style.id());
	}

	/** Teaches the style and switches to it. */
	public static void learn(Player player, FightingStyle style) {
		List<String> known = new ArrayList<>(player.getAttachedOrElse(KNOWN_STYLES, List.<String>of()));
		if (!known.contains(style.id())) {
			known.add(style.id());
			player.setAttached(KNOWN_STYLES, known);
		}
		setActive(player, style);
	}

	public static void setActive(Player player, FightingStyle style) {
		player.setAttached(ACTIVE_STYLE, style.id());
		player.setAttached(SELECTED_TECHNIQUE, 0);
	}

	/** The style the player is using, or null if they haven't learned any. */
	public static FightingStyle active(Player player) {
		String id = player.getAttached(ACTIVE_STYLE);
		return id == null ? null : FightingStyle.byId(id);
	}

	public static boolean isUsing(Player player, FightingStyle style) {
		return active(player) == style;
	}

	public static void initialize() {
		// Loading this class is enough to register the attachments.
	}
}
