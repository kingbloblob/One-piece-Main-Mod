package com.onepiecemod.resource;

import com.onepiecemod.util.Motion;
import net.minecraft.core.particles.ColorParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/**
 * Skypiea Dials you hold and use (the Flame and Impact Dials are weapon upgrades from the weapons feature).
 * - Flash Dial: a blinding flash. Mobs around you are blinded and glow so you can see them.
 * - Breath Dial: a blast of wind that launches you forward and up, and saves you from fall damage.
 * Each use wears the Dial down a little, and it needs a few seconds to recharge.
 */
public class DialItem extends Item {
	public enum Kind { FLASH, BREATH }

	private final Kind kind;

	public DialItem(Kind kind, Properties properties) {
		super(properties);
		this.kind = kind;
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		ItemStack stack = player.getItemInHand(hand);
		if (level instanceof ServerLevel serverLevel) {
			if (kind == Kind.FLASH) {
				for (Mob mob : level.getEntitiesOfClass(Mob.class, player.getBoundingBox().inflate(8.0))) {
					mob.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 100, 0), player);
					mob.addEffect(new MobEffectInstance(MobEffects.GLOWING, 200, 0), player);
					mob.setTarget(null);
				}
				serverLevel.sendParticles(ColorParticleOption.create(ParticleTypes.FLASH, 0xFFFFFFFF), player.getX(), player.getEyeY(), player.getZ(), 1, 0, 0, 0, 0);
				level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.FIREWORK_ROCKET_BLAST, SoundSource.PLAYERS, 1.0f, 1.5f);
			} else {
				Vec3 look = player.getLookAngle();
				player.setDeltaMovement(look.x * 1.4, Math.max(0.6, look.y * 1.4 + 0.4), look.z * 1.4);
				Motion.sync(player);
				player.resetFallDistance();
				serverLevel.sendParticles(ParticleTypes.GUST, player.getX(), player.getY(), player.getZ(), 3, 0.3, 0.1, 0.3, 0);
				level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.WIND_CHARGE_BURST, SoundSource.PLAYERS, 1.0f, 1.0f);
			}
			stack.hurtAndBreak(1, player, hand);
			player.getCooldowns().addCooldown(stack, kind == Kind.FLASH ? 200 : 60);
		}
		return InteractionResult.SUCCESS;
	}
}
