package com.onepiecemod.power;

import java.util.List;

import com.mojang.serialization.Codec;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;

/**
 * Extra data we store on players. Minecraft saves it with the world, so powers survive a restart.
 */
public class ModAttachments {
	/** Which Devil Fruit a player has eaten, such as "gomu_gomu_no_mi". Empty when they have none. */
	public static final AttachmentType<String> DEVIL_FRUIT = AttachmentRegistry.create(
			OnePieceMod.id("devil_fruit"),
			builder -> builder
					.persistent(Codec.STRING) // Save it to disk.
					.copyOnDeath() // Keep the power when the player respawns.
	);

	/** Devil Fruit mastery: goes up by 1 each time one of your moves hits an enemy. */
	public static final AttachmentType<Integer> FRUIT_MASTERY = AttachmentRegistry.create(
			OnePieceMod.id("fruit_mastery"),
			builder -> builder
					.persistent(Codec.INT)
					.copyOnDeath()
	);

	/** True once the player has awakened their Devil Fruit. */
	public static final AttachmentType<Boolean> AWAKENED = AttachmentRegistry.create(
			OnePieceMod.id("fruit_awakened"),
			builder -> builder
					.persistent(Codec.BOOL)
					.copyOnDeath()
	);

	/**
	 * When the R and Sneak + R moves are ready again, in game ticks. Saved on the player, so leaving and
	 * rejoining doesn't skip a cooldown.
	 */
	public static final AttachmentType<List<Long>> FRUIT_COOLDOWNS = AttachmentRegistry.create(
			OnePieceMod.id("fruit_cooldowns"),
			builder -> builder
					.persistent(Codec.LONG.listOf())
					.copyOnDeath()
	);

	/** When Yomi Yomi (or Orochi's eight heads) can bring this player back to life again, in game ticks. */
	public static final AttachmentType<Long> REVIVE_READY = AttachmentRegistry.create(
			OnePieceMod.id("fruit_revive_ready"),
			builder -> builder
					.persistent(Codec.LONG)
					.copyOnDeath()
	);

	/**
	 * Until when (game ticks) Seastone seals this fruit user's powers: cuffs, a Seastone Jitte hit, a Seastone bullet.
	 * Saved, so logging out doesn't break the cuffs. Works on players and on fruit-user characters. See SeaWeakness.
	 */
	public static final AttachmentType<Long> SEASTONE_SEALED = AttachmentRegistry.create(
			OnePieceMod.id("seastone_sealed"),
			builder -> builder.persistent(Codec.LONG)
	);

	public static void initialize() {
		// Loading this class is enough to register the attachment.
	}
}
