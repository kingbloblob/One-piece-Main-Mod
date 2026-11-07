package com.onepiecemod.character;

import java.util.ArrayList;
import java.util.List;

import com.mojang.serialization.Codec;

import net.minecraft.world.entity.player.Player;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;

/**
 * Remembers each player's story progress. Saved with the world and kept when they die.
 */
public class CharacterAttachments {
	/** Quest steps the player has been given, like "luffy:0" (Luffy's first step). */
	public static final AttachmentType<List<String>> QUESTS_STARTED = list("quests_started");
	/** Quest steps the player has finished, like "luffy:0". */
	public static final AttachmentType<List<String>> QUESTS_DONE = list("quests_done");
	/** Characters the player has talked to since a "talk" quest step asked them to. */
	public static final AttachmentType<List<String>> MET = list("characters_met");
	/** Bosses the player has beaten, like "buggy". */
	public static final AttachmentType<List<String>> BOSSES_DEFEATED = list("bosses_defeated");

	private static AttachmentType<List<String>> list(String name) {
		return AttachmentRegistry.create(
				OnePieceMod.id(name),
				builder -> builder
						.persistent(Codec.STRING.listOf())
						.copyOnDeath()
		);
	}

	public static boolean has(Player player, AttachmentType<List<String>> type, String id) {
		List<String> list = player.getAttached(type);
		return list != null && list.contains(id);
	}

	public static void add(Player player, AttachmentType<List<String>> type, String id) {
		List<String> list = new ArrayList<>(player.getAttachedOrElse(type, List.of()));
		if (!list.contains(id)) {
			list.add(id);
			player.setAttached(type, list);
		}
	}

	public static void remove(Player player, AttachmentType<List<String>> type, String id) {
		List<String> list = new ArrayList<>(player.getAttachedOrElse(type, List.of()));
		if (list.remove(id)) {
			player.setAttached(type, list);
		}
	}

	public static void initialize() {
		// Loading this class is enough to register the attachments.
	}
}
