package com.onepiecemod.weapon;

import com.onepiecemod.util.Motion;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.event.player.AttackEntityCallback;

import com.onepiecemod.haki.HakiPowers;
import com.onepiecemod.world.SeastoneEffects;

/**
 * The special effects of the melee weapons. They happen on fully charged hits only
 * (wait for the attack bar to fill), so spam-clicking doesn't trigger them.
 */
public class MeleeEffects {
	/** When each player last used a weapon's big effect, so shockwaves and lightning have a cooldown. */
	private static final Map<String, Long> LAST_USED = new HashMap<>();

	static void initialize() {
		AttackEntityCallback.EVENT.register((player, level, hand, target, hitResult) -> {
			if (player instanceof ServerPlayer attacker && level instanceof ServerLevel serverLevel
					&& target instanceof LivingEntity living && !player.isSpectator()
					&& player.getAttackStrengthScale(0.5f) >= 0.9f) {
				ItemStack weapon = player.getMainHandItem();
				onHit(attacker, serverLevel, living, weapon);
				float bonus = bonusDamage(attacker, serverLevel, living, weapon);
				if (bonus > 0) {
					extraHit(attacker, serverLevel, living, bonus);
				}
				afterHit(attacker, serverLevel, living, weapon);
				flyingSlash(attacker, serverLevel, living, weapon);
			}
			return InteractionResult.PASS; // PASS lets the normal hit happen too.
		});
	}

	private static void onHit(ServerPlayer player, ServerLevel level, LivingEntity target, ItemStack weapon) {
		long now = level.getGameTime();

		if (weapon.is(WeaponItems.HASSAIKAI) && ready(player, "hassaikai", now, 60)) {
			// Raimei Hakke: the target flies, and the blast hits everyone close by.
			push(target, player, 2.2, 0.6);
			for (LivingEntity other : around(player, level, target, 3.0)) {
				extraHit(player, level, other, 6.0f);
				push(other, player, 1.0, 0.3);
			}
			level.sendParticles(ParticleTypes.EXPLOSION, target.getX(), target.getY() + 1, target.getZ(), 3, 0.5, 0.5, 0.5, 0.0);
			sound(level, player, SoundEvents.PLAYER_ATTACK_KNOCKBACK);
		} else if (weapon.is(WeaponItems.MURAKUMOGIRI) && ready(player, "murakumogiri", now, 80)) {
			// The air cracks like glass, and the quake throws everyone back.
			for (LivingEntity other : around(player, level, target, 5.0)) {
				extraHit(player, level, other, 5.0f);
				push(other, player, 1.6, 0.4);
			}
			push(target, player, 1.6, 0.4);
			level.sendParticles(ParticleTypes.SONIC_BOOM, target.getX(), target.getY() + 1, target.getZ(), 1, 0.0, 0.0, 0.0, 0.0);
			sound(level, player, SoundEvents.GENERIC_EXPLODE.value());
		} else if (weapon.is(WeaponItems.GOLDEN_HOOK)) {
			target.addEffect(new MobEffectInstance(MobEffects.POISON, 80, 1));
		} else if (weapon.is(WeaponItems.PUNISHER)) {
			for (LivingEntity other : around(player, level, target, 2.5)) {
				extraHit(player, level, other, 4.0f);
			}
			level.sendParticles(ParticleTypes.SWEEP_ATTACK, player.getX(), player.getY() + 1, player.getZ(), 4, 1.0, 0.2, 1.0, 0.0);
		} else if (weapon.is(WeaponItems.MOGURA)) {
			target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 2));
			push(target, player, -0.6, 0.1); // a negative push pulls them in
		} else if (weapon.is(WeaponItems.NONOSAMA_BO) && level.getRandom().nextFloat() < 0.25f && ready(player, "nonosama_bo", now, 60)) {
			Shot.lightning(player, level, target.position(), 5.0f);
		} else if (weapon.is(WeaponItems.KIRIBACHI)) {
			target.addEffect(new MobEffectInstance(MobEffects.WITHER, 60, 0));
		} else if (weapon.is(WeaponItems.NEKO_NO_TE)) {
			player.addEffect(new MobEffectInstance(MobEffects.SPEED, 60, 1));
		} else if (weapon.is(WeaponItems.SOUL_SOLID)) {
			target.setTicksFrozen(target.getTicksRequiredToFreeze() + 60);
			target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 0));
			level.sendParticles(ParticleTypes.SNOWFLAKE, target.getX(), target.getY() + 1, target.getZ(), 10, 0.3, 0.5, 0.3, 0.0);
		} else if (weapon.is(WeaponItems.GRYPHON) && HakiPowers.hasArmamentActive(player)) {
			extraHit(player, level, target, 4.0f);
			push(target, player, 1.2, 0.3);
			level.sendParticles(ParticleTypes.ELECTRIC_SPARK, target.getX(), target.getY() + 1, target.getZ(), 15, 0.4, 0.5, 0.4, 0.2);
		}
	}

	// ---- Enchantments and Dials (these work on any weapon that has them, guns included) ----

	/** Extra damage from Seastone Edge and Haki Coating. */
	static float bonusDamage(ServerPlayer player, ServerLevel level, LivingEntity target, ItemStack weapon) {
		float bonus = 0.0f;
		int seastone = WeaponEnchantments.level(level, weapon, WeaponEnchantments.SEASTONE_EDGE);
		if (seastone > 0 && SeastoneEffects.isFruitUser(target)) {
			bonus += 2.0f * seastone;
		}
		int haki = WeaponEnchantments.level(level, weapon, WeaponEnchantments.HAKI_COATING);
		if (haki > 0 && HakiPowers.hasArmamentActive(player)) {
			bonus += 1.5f * haki;
		}
		return bonus;
	}

	/** Seastone Edge's weakening, and the Flame and Impact Dials. */
	static void afterHit(ServerPlayer player, ServerLevel level, LivingEntity target, ItemStack weapon) {
		int seastone = WeaponEnchantments.level(level, weapon, WeaponEnchantments.SEASTONE_EDGE);
		if (seastone > 0 && SeastoneEffects.isFruitUser(target) && level.getRandom().nextFloat() < 0.1f * seastone) {
			SeastoneEffects.drain(target, 60);
		}
		int dial = WeaponUpgrades.dial(weapon);
		if (dial == WeaponUpgrades.FLAME_DIAL) {
			target.igniteForSeconds(4.0f);
		} else if (dial == WeaponUpgrades.IMPACT_DIAL) {
			push(target, player, 1.8, 0.5);
			level.sendParticles(ParticleTypes.EXPLOSION, target.getX(), target.getY() + 1, target.getZ(), 1, 0.0, 0.0, 0.0, 0.0);
		}
	}

	/** Flying Slash: a cutting wave flies ahead and hits everything in a line behind the target too. */
	private static void flyingSlash(ServerPlayer player, ServerLevel level, LivingEntity target, ItemStack weapon) {
		int slash = WeaponEnchantments.level(level, weapon, WeaponEnchantments.FLYING_SLASH);
		if (slash <= 0 || !ready(player, "flying_slash", level.getGameTime(), 30)) {
			return;
		}
		Vec3 start = player.getEyePosition();
		Vec3 direction = player.getLookAngle();
		double range = 4.0 + 3.0 * slash;
		List<LivingEntity> cut = new java.util.ArrayList<>();
		for (double distance = 1.0; distance <= range; distance += 0.5) {
			Vec3 point = start.add(direction.scale(distance));
			level.sendParticles(ParticleTypes.SWEEP_ATTACK, point.x, point.y, point.z, 1, 0.0, 0.0, 0.0, 0.0);
			for (LivingEntity entity : level.getEntitiesOfClass(LivingEntity.class, new net.minecraft.world.phys.AABB(point, point).inflate(0.8),
					entity -> entity != target && Shot.canHit(player, entity))) {
				if (!cut.contains(entity)) {
					cut.add(entity);
				}
			}
		}
		for (LivingEntity entity : cut) {
			extraHit(player, level, entity, 3.0f + 2.0f * slash);
		}
		sound(level, player, SoundEvents.PLAYER_ATTACK_SWEEP);
	}

	/** True (and starts the cooldown) if this player's effect is ready again. */
	private static boolean ready(ServerPlayer player, String effect, long now, int cooldownTicks) {
		String key = player.getUUID() + "/" + effect;
		Long last = LAST_USED.get(key);
		if (last != null && now - last < cooldownTicks) {
			return false;
		}
		LAST_USED.put(key, now);
		return true;
	}

	/** Creatures near the target that may be hit (not you, your pets or crewmates, nor the target itself). */
	private static List<LivingEntity> around(ServerPlayer player, ServerLevel level, LivingEntity target, double radius) {
		return level.getEntitiesOfClass(LivingEntity.class, target.getBoundingBox().inflate(radius),
				entity -> entity != target && Shot.canHit(player, entity));
	}

	/**
	 * Bonus damage on top of the normal hit. It uses "thrown" damage, not a melee hit, so it can't set off
	 * these effects again. Resetting the invulnerable time lets the normal hit still land in full.
	 */
	private static void extraHit(ServerPlayer player, ServerLevel level, LivingEntity target, float damage) {
		target.damageCooldownTime = 0;
		target.hurtServer(level, player.damageSources().thrown(player, player), damage);
		target.damageCooldownTime = 0; // 26.3's hit-safety timer (setInvulnerableTime no longer does this)
	}

	/** Shoves a creature away from the player (or toward them if strength is negative). */
	private static void push(LivingEntity target, ServerPlayer player, double strength, double up) {
		Vec3 away = target.position().subtract(player.position()).multiply(1, 0, 1).normalize().scale(strength);
		target.setDeltaMovement(away.x, up, away.z);
		Motion.sync(target);
	}

	private static void sound(ServerLevel level, ServerPlayer player, net.minecraft.sounds.SoundEvent event) {
		level.playSound(null, player.getX(), player.getY(), player.getZ(), event, SoundSource.PLAYERS, 1.0f, 0.8f);
	}
}
