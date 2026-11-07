package com.onepiecemod.haki;

import com.mojang.serialization.Codec;

import net.minecraft.world.entity.player.Player;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;

/**
 * Saves each player's Haki training on the player, so it survives restarts and deaths.
 */
public class HakiAttachments {
	public static final AttachmentType<HakiData> HAKI = AttachmentRegistry.create(
			OnePieceMod.id("haki"),
			builder -> builder
					.persistent(HakiData.CODEC) // Save it to disk.
					.copyOnDeath() // Training isn't lost when you die.
	);

	/** Game time (in ticks) when this player may release Conqueror's Haki again. Saved, so logging out doesn't reset it. */
	public static final AttachmentType<Long> CONQUEROR_READY_AT = AttachmentRegistry.create(
			OnePieceMod.id("conqueror_ready_at"),
			builder -> builder
					.persistent(Codec.LONG)
					.copyOnDeath()
	);

	/** Game time when Future Sight (Observation level 5) can save this player from a hit again. */
	public static final AttachmentType<Long> FUTURE_SIGHT_READY_AT = AttachmentRegistry.create(
			OnePieceMod.id("future_sight_ready_at"),
			builder -> builder
					.persistent(Codec.LONG)
					.copyOnDeath()
	);

	/** A player's Haki. Players who never trained get HakiData.EMPTY. */
	public static HakiData get(Player player) {
		HakiData data = player.getAttached(HAKI);
		return data != null ? data : HakiData.EMPTY;
	}

	public static void set(Player player, HakiData data) {
		player.setAttached(HAKI, data);
	}

	public static void initialize() {
		// Loading this class is enough to register the attachment.
	}
}
