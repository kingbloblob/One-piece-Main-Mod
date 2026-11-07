package com.onepiecemod.crew;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;

/**
 * Saves each captain's crew on the player, so it survives restarts and deaths.
 */
public class CrewAttachments {
	public static final AttachmentType<Crew> CREW = AttachmentRegistry.create(
			OnePieceMod.id("crew"),
			builder -> builder
					.persistent(Crew.CODEC) // Save it to disk.
					.copyOnDeath() // A captain who dies keeps their crew.
	);

	public static void initialize() {
		// Loading this class is enough to register the attachment.
	}
}
