package com.onepiecemod.race;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.attribute.EnvironmentAttributes;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.MoonPhase;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.entity.event.v1.ServerPlayerEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.OnePieceMod;

/**
 * Sulong: a Mink's moon form. Their fur turns white and long, their eyes go red, and they get
 * far stronger and faster. In the story it happens when a Mink looks at the full moon, and only
 * a few trained Minks (like Carrot after Whole Cake Island) can call it up at will.
 *
 * In the mod:
 *  - Under a full moon, at night, in the open sky of the Overworld, every Mink turns Sulong.
 *    It lasts while they can see the moon.
 *  - An untrained Sulong is wild: strong and fast, but it burns through food and leaves you
 *    exhausted when the moon goes down.
 *  - Every second spent in Sulong trains it. After 10 minutes in total (about two full-moon nights)
 *    it is mastered: a stronger, calm Sulong, and you can call it up any time for 45 seconds
 *    with the Awaken key (Y). Minks who also ate a Devil Fruit sneak + Y. 5 minute cooldown.
 *  - A Rumble Ball forces a 60 second Sulong on any Mink, mastered or not (see RumbleBallItem).
 *
 * While Sulong, Electro is much stronger: most punches shock, and the shock hits harder (RacePerks).
 */
public class Sulong {
	/** Seconds needed in Sulong before it is mastered. */
	public static final int MASTERY_SECONDS = 600;
	private static final int AT_WILL_SECONDS = 45;
	private static final int AT_WILL_COOLDOWN_SECONDS = 300;

	/** Total seconds this player has spent in Sulong. Saved, and kept after death. */
	public static final AttachmentType<Integer> TRAINING = AttachmentRegistry.create(OnePieceMod.id("sulong_training"),
			builder -> builder.persistent(Codec.INT).copyOnDeath());
	/** Game time when the at-will Sulong can be used again. Saved so relogging doesn't skip the wait. */
	public static final AttachmentType<Long> READY_AT = AttachmentRegistry.create(OnePieceMod.id("sulong_ready_at"),
			builder -> builder.persistent(Codec.LONG).copyOnDeath());

	/** Sulongs started by hand or by a Rumble Ball: player -> game time it ends. */
	private static final Map<UUID, Long> FORCED = new HashMap<>();
	/** Players who were Sulong last second, so we can tell when it starts and ends. */
	private static final Map<UUID, Boolean> WAS = new HashMap<>();

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 20 != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				everySecond(player);
			}
		});
		ServerPlayerEvents.AFTER_RESPAWN.register((oldPlayer, newPlayer, alive) -> {
			FORCED.remove(oldPlayer.getUUID());
			WAS.remove(oldPlayer.getUUID());
		});
	}

	public static int training(ServerPlayer player) {
		return player.getAttachedOrElse(TRAINING, 0);
	}

	public static boolean mastered(ServerPlayer player) {
		return training(player) >= MASTERY_SECONDS;
	}

	/** True while this Mink is in Sulong form (any kind). */
	public static boolean isActive(ServerPlayer player) {
		return Boolean.TRUE.equals(WAS.get(player.getUUID()));
	}

	/** Whether this Mink is standing under the full moon right now. */
	public static boolean underFullMoon(ServerPlayer player) {
		Level level = player.level();
		if (level.dimension() != Level.OVERWORLD || !level.isDarkOutside() || !level.canSeeSky(player.blockPosition().above())) {
			return false;
		}
		return level.environmentAttributes().getValue(EnvironmentAttributes.MOON_PHASE, player.blockPosition()) == MoonPhase.FULL_MOON;
	}

	/** Forces Sulong for this many seconds (Rumble Ball). Returns false if the player is not a Mink. */
	public static boolean force(ServerPlayer player, int seconds) {
		if (!RaceAttachments.is(player, Race.MINK)) {
			return false;
		}
		long end = player.level().getGameTime() + seconds * 20L;
		FORCED.merge(player.getUUID(), end, Math::max);
		everySecond(player);
		return true;
	}

	/** The Awaken key for Minks: calls Sulong up at will, once mastered. */
	public static void useAtWill(ServerPlayer player) {
		if (!RaceAttachments.is(player, Race.MINK)) {
			return;
		}
		if (!mastered(player)) {
			player.sendOverlayMessage(Component.literal("You can't call Sulong up yet. Train it under the full moon: "
					+ training(player) / 60 + "/" + MASTERY_SECONDS / 60 + " min").withStyle(ChatFormatting.GRAY));
			return;
		}
		if (isActive(player)) {
			player.sendOverlayMessage(Component.literal("You are already Sulong.").withStyle(ChatFormatting.GRAY));
			return;
		}
		long now = player.level().getGameTime();
		long readyAt = player.getAttachedOrElse(READY_AT, 0L);
		if (now < readyAt) {
			player.sendOverlayMessage(Component.literal("Sulong is ready again in " + (readyAt - now + 19) / 20 + " s").withStyle(ChatFormatting.GRAY));
			return;
		}
		player.setAttached(READY_AT, now + (AT_WILL_SECONDS + AT_WILL_COOLDOWN_SECONDS) * 20L);
		force(player, AT_WILL_SECONDS);
	}

	/** One line for /race: how far the Sulong training has come. */
	public static Component describe(ServerPlayer player) {
		if (mastered(player)) {
			return Component.literal("Sulong: mastered. Awaken key (Y, or sneak + Y with a Devil Fruit) calls it up for "
					+ AT_WILL_SECONDS + " s.").withStyle(ChatFormatting.WHITE);
		}
		return Component.literal("Sulong: " + training(player) / 60 + "/" + MASTERY_SECONDS / 60
				+ " min trained. Stand under the full moon at night to turn Sulong.").withStyle(ChatFormatting.GRAY);
	}

	private static void everySecond(ServerPlayer player) {
		UUID id = player.getUUID();
		boolean mink = RaceAttachments.is(player, Race.MINK) && player.isAlive() && !player.isSpectator();
		long now = player.level().getGameTime();
		Long forcedEnd = FORCED.get(id);
		boolean forced = forcedEnd != null && now < forcedEnd;
		if (forcedEnd != null && !forced) {
			FORCED.remove(id);
		}
		boolean moon = mink && underFullMoon(player);
		boolean active = mink && (forced || moon);
		boolean was = Boolean.TRUE.equals(WAS.get(id));

		if (active && !was) {
			start(player, moon && !forced);
		} else if (!active && was) {
			end(player);
		}
		WAS.put(id, active);
		if (!active) {
			if (!mink) {
				WAS.remove(id);
			}
			return;
		}

		boolean strong = mastered(player) || forced;
		// Strength II and Speed II either way; a mastered (or Rumble Ball) Sulong is also tough and calm.
		effect(player, MobEffects.STRENGTH, 1);
		effect(player, MobEffects.SPEED, 1);
		effect(player, MobEffects.JUMP_BOOST, 1);
		if (strong) {
			effect(player, MobEffects.RESISTANCE, 0);
		} else {
			player.causeFoodExhaustion(0.6f); // A wild Sulong eats you alive.
		}
		if (player.getAttachedOrElse(TRAINING, 0) < MASTERY_SECONDS) {
			int trained = player.getAttachedOrElse(TRAINING, 0) + 1;
			player.setAttached(TRAINING, trained);
			if (trained == MASTERY_SECONDS) {
				com.onepiecemod.advancement.AdvancementFeature.grant(player, "powers/sulong_master");
				player.sendSystemMessage(Component.literal("You have mastered Sulong! Press the Awaken key (Y, or sneak + Y if you ate a Devil Fruit) to call it up at will.")
						.withStyle(ChatFormatting.WHITE, ChatFormatting.BOLD));
			}
		}
		ServerLevel level = (ServerLevel) player.level();
		level.sendParticles(ParticleTypes.END_ROD, player.getX(), player.getY() + 1.2, player.getZ(), 4, 0.35, 0.6, 0.35, 0.01);
		level.sendParticles(ParticleTypes.ELECTRIC_SPARK, player.getX(), player.getY() + 1.0, player.getZ(), 6, 0.4, 0.6, 0.4, 0.05);
	}

	private static void start(ServerPlayer player, boolean fromMoon) {
		ServerLevel level = (ServerLevel) player.level();
		level.playSound(null, player.blockPosition(), SoundEvents.LIGHTNING_BOLT_IMPACT, SoundSource.PLAYERS, 1.0f, 0.6f);
		level.sendParticles(ParticleTypes.EXPLOSION, player.getX(), player.getY() + 1, player.getZ(), 1, 0, 0, 0, 0);
		String text = fromMoon && !mastered(player)
				? "The full moon! Your fur turns white... SULONG! (It's wild: you will be worn out when it ends.)"
				: "SULONG!";
		player.sendOverlayMessage(Component.literal(text).withStyle(ChatFormatting.WHITE, ChatFormatting.BOLD));
		com.onepiecemod.advancement.AdvancementFeature.grant(player, "powers/sulong");
	}

	private static void end(ServerPlayer player) {
		for (Holder<MobEffect> effect : java.util.List.of(MobEffects.STRENGTH, MobEffects.SPEED, MobEffects.JUMP_BOOST, MobEffects.RESISTANCE)) {
			MobEffectInstance current = player.getEffect(effect);
			if (current != null && current.isAmbient() && current.getDuration() <= 60) {
				player.removeEffect(effect); // Only ours: short, quiet top-ups. Potions and fruit forms stay.
			}
		}
		if (!mastered(player)) {
			// Sulong burns a lot of life: untrained Minks collapse afterwards.
			player.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 30 * 20, 0));
			player.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 15 * 20, 0));
			player.sendOverlayMessage(Component.literal("Sulong fades... you are exhausted.").withStyle(ChatFormatting.GRAY));
		} else {
			player.sendOverlayMessage(Component.literal("Sulong fades.").withStyle(ChatFormatting.GRAY));
		}
	}

	private static void effect(ServerPlayer player, Holder<MobEffect> effect, int amplifier) {
		MobEffectInstance current = player.getEffect(effect);
		if (current == null || current.getAmplifier() < amplifier || (current.getAmplifier() == amplifier && current.getDuration() < 50)) {
			player.addEffect(new MobEffectInstance(effect, 60, amplifier, true, false, true));
		}
	}
}
