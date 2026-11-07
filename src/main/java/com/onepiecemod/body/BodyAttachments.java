package com.onepiecemod.body;

import net.minecraft.world.entity.Entity;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentSyncPredicate;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;

/**
 * Saves each player's body shape on the player.
 * It is also sent to every player who can see them, so everyone's game draws them the same way.
 */
public class BodyAttachments {
	public static final AttachmentType<Body> BODY = AttachmentRegistry.create(
			OnePieceMod.id("body"),
			builder -> builder
					.persistent(Body.CODEC) // Save it to disk.
					.copyOnDeath() // Keep your body after you respawn.
					.syncWith(Body.STREAM_CODEC, AttachmentSyncPredicate.all()) // Everyone nearby gets it.
	);

	/** Hair, scar and outfit from the body screen. Also sent to everyone nearby. */
	public static final AttachmentType<Look> LOOK = AttachmentRegistry.create(
			OnePieceMod.id("look"),
			builder -> builder
					.persistent(Look.CODEC)
					.copyOnDeath()
					.syncWith(Look.STREAM_CODEC, AttachmentSyncPredicate.all())
	);

	/** The player's looks, or Look.DEFAULT if they never picked any. */
	public static Look look(Entity entity) {
		Look look = entity.getAttached(LOOK);
		return look != null ? look : Look.DEFAULT;
	}

	/** The body shape, or null if they have not used the body screen yet. */
	public static Body get(Entity entity) {
		return entity.getAttached(BODY);
	}

	public static void set(Entity entity, Body body) {
		entity.setAttached(BODY, body);
	}

	public static void initialize() {
		// Loading this class is enough to register the attachment.
	}
}
