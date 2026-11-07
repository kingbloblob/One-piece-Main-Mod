package com.onepiecemod.crafting;

import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.power.Awakening;
import com.onepiecemod.power.DevilFruit;
import com.onepiecemod.power.DevilFruitPowers;
import com.onepiecemod.race.Sulong;

/**
 * Chopper's Rumble Ball: right-click to swallow it. It works for 60 seconds, then your body needs
 * 10 minutes to recover. Swallowing another one before that is an overdose, like Chopper's
 * Monster Point at Enies Lobby: you lose control and are left weak afterwards.
 *
 * What it does depends on who takes it (and stacks if more than one fits):
 *  - Minks turn Sulong (no full moon needed), see Sulong.
 *  - Devil Fruit users with at least 250 mastery get a borrowed awakening: the awakened form starts
 *    right away, and the awakened bonuses last the whole minute. See Awakening.rumbleAwaken.
 *  - Chopper's own fruit (Hito Hito no Mi) also gets Monster Point strength and toughness.
 *  - Everyone gets Strength, Speed and Resistance.
 */
public class RumbleBallItem extends Item {
	private static final int SECONDS = 60;
	private static final int RECOVERY_SECONDS = 10 * 60;

	/** Game time when the body has recovered from the last Rumble Ball. Saved, so relogging doesn't skip it. */
	public static final AttachmentType<Long> READY_AT = AttachmentRegistry.create(OnePieceMod.id("rumble_ball_ready_at"),
			builder -> builder.persistent(Codec.LONG).copyOnDeath());

	public RumbleBallItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (player instanceof ServerPlayer serverPlayer) {
			ItemStack stack = player.getItemInHand(hand);
			long now = level.getGameTime();
			long readyAt = player.getAttachedOrElse(READY_AT, 0L);
			if (now < readyAt) {
				overdose(serverPlayer, (readyAt - now) / 20);
			} else {
				swallow(serverPlayer);
				player.setAttached(READY_AT, now + (SECONDS + RECOVERY_SECONDS) * 20L);
				player.getCooldowns().addCooldown(stack, (SECONDS + RECOVERY_SECONDS) * 20);
			}
			if (!player.isCreative()) {
				stack.shrink(1);
			}
			level.playSound(null, player.blockPosition(), SoundEvents.GENERIC_EAT.value(), SoundSource.PLAYERS, 1.0f, 1.2f);
		}
		return InteractionResult.SUCCESS;
	}

	private static void swallow(ServerPlayer player) {
		int ticks = SECONDS * 20;
		player.addEffect(new MobEffectInstance(MobEffects.STRENGTH, ticks, 1));
		player.addEffect(new MobEffectInstance(MobEffects.SPEED, ticks, 0));
		player.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, ticks, 0));

		StringBuilder what = new StringBuilder("Rumble! " + SECONDS + " seconds of monster strength");
		if (Sulong.force(player, SECONDS)) {
			what.append(", and Sulong");
		}
		DevilFruit fruit = DevilFruitPowers.getFruit(player);
		if (fruit != null) {
			if (fruit.id().equals("hito_hito_no_mi")) {
				player.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, ticks, 1));
				player.addEffect(new MobEffectInstance(MobEffects.HEALTH_BOOST, ticks, 2));
				what.append(", Monster Point");
			}
			if (Awakening.rumbleAwaken(player, fruit, SECONDS)) {
				what.append(", and an awakened fruit");
			}
		}
		player.sendOverlayMessage(Component.literal(what.append("!").toString()).withStyle(ChatFormatting.GOLD));
		player.sendSystemMessage(Component.literal("Your body needs " + RECOVERY_SECONDS / 60
				+ " minutes to recover after this one. Taking another sooner is an overdose.").withStyle(ChatFormatting.GRAY));
	}

	/** Too many Rumble Balls: the body goes out of control. */
	private static void overdose(ServerPlayer player, long secondsLeft) {
		player.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 200, 0));
		player.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 600, 1));
		player.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 300, 1));
		player.hurtServer(player.level(), player.damageSources().magic(), 4.0f);
		player.sendOverlayMessage(Component.literal("Overdose! Your body goes out of control... (recovered in "
				+ (secondsLeft + 59) / 60 + " min)").withStyle(ChatFormatting.RED));
	}
}
