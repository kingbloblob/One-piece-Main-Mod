package com.onepiecemod.power;

import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;

/**
 * Wild Nika: Luffy's feral, ape-like form from chapter 1198 (from leaks; the official chapter comes out
 * 8 Nov 2026). In the mod it is a second stage of Gear 5: while Gear 5 is running, press Y again.
 *
 * You turn into a hunched, long-armed, tailed rubber beast (the "nika_wild" Zoan model) for 20 seconds:
 * very fast and springy, every enemy close by gets bitten and bounced each second, and each bite heals you.
 * Sneak + R is Wild Bite (see ZoanForms). It replaces the rest of Gear 5, so it's a burst, not a free extension:
 * the awakening cooldown starts from when Gear 5 started.
 */
public final class WildNika {
	public static final String NAME = "Gear 5: Wild Nika";
	public static final int SECONDS = 20;

	private WildNika() {
	}

	/** Gomu users in Gear 5 (not already wild). */
	static boolean canShift(ServerPlayer player, DevilFruit fruit, String activeFormName) {
		return fruit.id().equals("gomu_gomu_no_mi") && activeFormName.startsWith("Gear 5: Sun God");
	}

	static void start(ServerPlayer player, ServerLevel level) {
		int ticks = SECONDS * 20;
		player.addEffect(new MobEffectInstance(MobEffects.SPEED, ticks, 2));
		player.addEffect(new MobEffectInstance(MobEffects.JUMP_BOOST, ticks, 3));
		player.addEffect(new MobEffectInstance(MobEffects.STRENGTH, ticks, 2));
		player.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, ticks, 1));
		ZoanForms.startForm(player, "nika_wild", ticks);
		level.sendParticles(ParticleTypes.CLOUD, player.getX(), player.getY() + 1, player.getZ(), 80, 1.2, 1.2, 1.2, 0.1);
		level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, player.getX(), player.getY() + 1, player.getZ(), 1, 0, 0, 0, 0);
		level.playSound(null, player.blockPosition(), SoundEvents.RAVAGER_ROAR, SoundSource.PLAYERS, 2.0f, 1.3f);
		player.sendOverlayMessage(Component.literal(NAME + "!").withStyle(ChatFormatting.WHITE, ChatFormatting.BOLD));
		com.onepiecemod.advancement.AdvancementFeature.grant(player, "powers/wild_nika");
	}

	/** Bouncing drum-beat clouds around you while the form lasts. */
	static void everySecond(ServerPlayer player) {
		ServerLevel level = (ServerLevel) player.level();
		level.sendParticles(ParticleTypes.CLOUD, player.getX(), player.getY() + 0.2, player.getZ(), 12, 0.8, 0.1, 0.8, 0.05);
	}
}
