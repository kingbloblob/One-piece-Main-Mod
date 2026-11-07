package com.onepiecemod.power;

import java.util.Map;
import java.util.UUID;

import net.minecraft.core.Holder;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;

import com.onepiecemod.character.CharacterEntity;

/**
 * Keeps Devil Fruit stuns fair against bosses and other players.
 *
 * Ordinary mobs get the full effect. Bosses and players ("tough" targets) instead get:
 * - stuns (heavy Slowness, Levitation) of at most 3 seconds,
 * - then 4 seconds where new stuns only slow them a little, so they can't be stun-locked forever,
 * - Weakness of at most level I, so a boss still hits hard,
 * - other slowing and weakening effects for half as long.
 * Damage over time (poison, wither, fire) and blinding are not changed.
 */
public final class FruitControl {
	private static final int MAX_STUN_TICKS = 60;
	private static final int IMMUNE_TICKS = 80;

	// When each tough target can be stunned again, in game ticks.
	private static final Map<UUID, Long> STUN_READY = new java.util.HashMap<>();

	private FruitControl() {
	}

	/** Bosses and players resist stuns. */
	public static boolean isTough(LivingEntity target) {
		return target instanceof Player
				|| target instanceof CharacterEntity character && character.isBoss()
				|| target.entityTags().contains(FruitBench.BOSS_TAG);
	}

	/** Gives the target an effect from a Devil Fruit move, made fair for bosses and players. */
	public static void apply(LivingEntity target, MobEffectInstance effect) {
		if (!isTough(target)) {
			target.addEffect(effect);
			return;
		}
		Holder<MobEffect> type = effect.getEffect();
		int ticks = effect.getDuration();
		int level = effect.getAmplifier();
		boolean stun = type.equals(MobEffects.LEVITATION) || type.equals(MobEffects.SLOWNESS) && level >= 3;

		if (stun) {
			long now = target.level().getGameTime();
			if (now < STUN_READY.getOrDefault(target.getUUID(), 0L)) {
				// Still shaking off the last stun: only a light slow gets through.
				if (type.equals(MobEffects.SLOWNESS)) {
					target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, Math.min(ticks, 40), 0));
				}
				return;
			}
			ticks = Math.min(ticks, MAX_STUN_TICKS);
			level = type.equals(MobEffects.SLOWNESS) ? Math.min(level, 3) : level;
			STUN_READY.put(target.getUUID(), now + ticks + IMMUNE_TICKS);
			if (STUN_READY.size() > 512) {
				STUN_READY.entrySet().removeIf(entry -> entry.getValue() < now);
			}
		} else if (type.equals(MobEffects.WEAKNESS)) {
			ticks /= 2;
			level = 0;
		} else if (type.equals(MobEffects.SLOWNESS) || type.equals(MobEffects.MINING_FATIGUE) || type.equals(MobEffects.NAUSEA)) {
			ticks /= 2;
		}
		target.addEffect(new MobEffectInstance(type, Math.max(ticks, 20), level));
	}
}
