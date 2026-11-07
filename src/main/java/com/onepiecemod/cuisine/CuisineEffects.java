package com.onepiecemod.cuisine;

import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;

import com.onepiecemod.OnePieceMod;

/**
 * The two buffs only cooking gives.
 *
 *  - Well Fed: every dish of Sanji's gives it. Now and then it tops your hunger back up, so a good meal
 *    lasts a whole voyage. Level II (the All Blue Full Course) tops up twice as often.
 *  - Warm Belly: hot pots. It melts frost off you, so Winter Islands (Drum, Punk Hazard) don't freeze you.
 */
public class CuisineEffects {
	/** Ticks between hunger top-ups for Well Fed I (half that for level II). */
	private static final int TOP_UP_TICKS = 300;

	public static final Holder<MobEffect> WELL_FED = register("well_fed", new WellFed());
	public static final Holder<MobEffect> WARM_BELLY = register("warm_belly", new WarmBelly());

	public static void initialize() {
		// Loading the class registers the effects.
	}

	private static Holder<MobEffect> register(String name, MobEffect effect) {
		return Registry.registerForHolder(BuiltInRegistries.MOB_EFFECT, OnePieceMod.id(name), effect);
	}

	private static class WellFed extends MobEffect {
		WellFed() {
			super(MobEffectCategory.BENEFICIAL, 0xE8A040);
		}

		@Override
		public boolean shouldApplyEffectTickThisTick(int duration, int amplifier) {
			return duration % (TOP_UP_TICKS >> Math.min(amplifier, 2)) == 0;
		}

		@Override
		public boolean applyEffectTick(ServerLevel level, LivingEntity entity, int amplifier) {
			if (entity instanceof Player player && player.getFoodData().getFoodLevel() < 20) {
				player.getFoodData().eat(1, 0.3f);
			}
			return true;
		}
	}

	private static class WarmBelly extends MobEffect {
		WarmBelly() {
			super(MobEffectCategory.BENEFICIAL, 0xE8603A);
		}

		@Override
		public boolean shouldApplyEffectTickThisTick(int duration, int amplifier) {
			return true;
		}

		@Override
		public boolean applyEffectTick(ServerLevel level, LivingEntity entity, int amplifier) {
			// Winter Islands add about 2.3 frost a tick; this melts 6.
			if (entity.getTicksFrozen() > 0) {
				entity.setTicksFrozen(Math.max(0, entity.getTicksFrozen() - 6));
			}
			return true;
		}
	}
}
