package com.onepiecemod.race;

import com.mojang.serialization.Codec;

import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.world.entity.player.Player;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentSyncPredicate;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;

/**
 * Saves each player's race on the player, so it survives restarts and deaths.
 * Players who have not picked yet have nothing saved.
 */
public class RaceAttachments {
	public static final AttachmentType<String> RACE = AttachmentRegistry.create(
			OnePieceMod.id("race"),
			builder -> builder
					.persistent(Codec.STRING) // Save it to disk.
					.copyOnDeath() // You are still a Fish-Man after you respawn.
					.syncWith(ByteBufCodecs.STRING_UTF8, AttachmentSyncPredicate.all()) // Everyone's game draws your ears, horns or wings.
	);

	/** The player's race, or null if they have not picked one yet. */
	public static Race get(Player player) {
		String id = player.getAttached(RACE);
		return id != null ? Race.byId(id) : null;
	}

	/** True if this player is the given race. Handy for other features, e.g. RaceAttachments.is(player, Race.FISHMAN). */
	public static boolean is(Player player, Race race) {
		return get(player) == race;
	}

	/** Sets the race, or forgets it when race is null (the picker will show again). */
	public static void set(Player player, Race race) {
		if (race == null) {
			player.removeAttached(RACE);
		} else {
			player.setAttached(RACE, race.id);
		}
	}

	public static void initialize() {
		// Loading this class is enough to register the attachment.
	}
}
