package com.onepiecemod.weapon;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.SweetBerryBushBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import java.util.List;

import com.onepiecemod.multiplayer.PlayerCrews;
import com.onepiecemod.world.SeastoneEffects;

/**
 * One shot from a gun, slingshot or thrown knife.
 * It travels in a straight line from the shooter's eyes and stops at the first creature or solid block.
 */
public class Shot {
	/** What a shot hit: the creature (or null) and the point where it stopped. */
	public record Hit(LivingEntity target, Vec3 point) {}

	/** Fires a gun shot with this ammo and applies its damage and special effect. */
	public static void fire(ServerPlayer shooter, ServerLevel level, GunItem.Stats stats, Ammo ammo, ItemStack gun) {
		fire(shooter, level, stats, ammo, gun, ItemStack.EMPTY);
	}

	/**
	 * Fires a gun shot. round is the one round fired: for an add-on round (see GunAddons) its Round adds to
	 * what ammo (its base) does. Empty, or the main mod's own ammo, fires exactly like ammo.
	 */
	public static void fire(ServerPlayer shooter, ServerLevel level, GunItem.Stats stats, Ammo ammo, ItemStack gun, ItemStack round) {
		GunAddons.Round addon = GunAddons.round(round);
		gunSound(shooter, level, ammo);
		ParticleOptions trail = addon == null ? null : addon.trail(round);
		Hit hit = trace(shooter, level, stats.range(), stats.spread(), trail != null ? trail : trail(ammo));
		float damage = stats.damage();

		if (hit.target() != null) {
			LivingEntity target = hit.target();
			if (ammo == Ammo.SEASTONE_BULLET && SeastoneEffects.isFruitUser(target)) {
				damage += 4.0f;
				SeastoneEffects.drain(target, 100);
			}
			damage += MeleeEffects.bonusDamage(shooter, level, target, gun);
			if (addon != null) {
				damage += addon.bonusDamage(shooter, level, target, round);
			}
			boolean headshot = isHeadshot(target, hit.point());
			if (headshot) {
				damage *= HEADSHOT;
			}
			hurt(shooter, level, target, damage);
			hitMarker(shooter, headshot);
			MeleeEffects.afterHit(shooter, level, target, gun);
			if (addon != null) {
				addon.onHit(shooter, level, target, round, gun);
			}
			level.sendParticles(ParticleTypes.CRIT, target.getX(), target.getY() + target.getBbHeight() / 2, target.getZ(), 8, 0.2, 0.2, 0.2, 0.1);
			switch (ammo) {
				case TABASCO_STAR -> {
					target.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 100, 0));
					target.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 160, 0));
				}
				case POP_GREEN -> {
					target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 4));
					target.addEffect(new MobEffectInstance(MobEffects.POISON, 60, 0));
					sprout(level, target.blockPosition());
				}
				default -> { }
			}
		} else if (ammo == Ammo.POP_GREEN) {
			sprout(level, BlockPos.containing(hit.point()).above());
		}

		if (addon != null) {
			addon.onLand(shooter, level, hit.point(), hit.target(), round);
		}

		// Explosions never break blocks: a stray shot shouldn't wreck your ship.
		if (ammo == Ammo.CANNONBALL) {
			level.explode(shooter, hit.point().x, hit.point().y, hit.point().z, 2.0f, Level.ExplosionInteraction.NONE);
		} else if (ammo == Ammo.EXPLODING_STAR) {
			level.explode(shooter, hit.point().x, hit.point().y, hit.point().z, 1.2f, Level.ExplosionInteraction.NONE);
		}
	}

	/** Headshots do this much more damage. */
	public static final float HEADSHOT = 1.5f;

	/**
	 * Damage from a shot or a thrown knife. Each shot is its own hit: Minecraft normally ignores
	 * hits that land within half a second of the last one, which made the Tommy Gun's 2nd and 3rd
	 * rounds (and fast slingshots) do nothing.
	 */
	public static void hurt(ServerPlayer shooter, ServerLevel level, LivingEntity target, float damage) {
		// In 26.3 the half-second of hit safety is damageCooldownTime (setInvulnerableTime is something else now).
		target.damageCooldownTime = 0;
		target.hurtServer(level, shooter.damageSources().thrown(shooter, shooter), damage);
		target.damageCooldownTime = 0;
	}

	/** True if the shot stopped up by the target's eyes (the top quarter of a person-sized body). */
	public static boolean isHeadshot(LivingEntity target, Vec3 point) {
		return target.getBbHeight() >= 1.0f && point.y >= target.getEyeY() - 0.3;
	}

	/** A small "tick" only the shooter hears, so you know you hit (louder and higher for headshots). */
	public static void hitMarker(ServerPlayer shooter, boolean headshot) {
		shooter.connection.send(new ClientboundSoundPacket(BuiltInRegistries.SOUND_EVENT.wrapAsHolder(SoundEvents.ARROW_HIT_PLAYER),
				SoundSource.PLAYERS, shooter.getX(), shooter.getY(), shooter.getZ(), headshot ? 0.6f : 0.35f, headshot ? 1.6f : 1.2f,
				shooter.getRandom().nextLong()));
	}

	/**
	 * A lightning strike that hurts what's around it but never you, your crew or your pets,
	 * and never sets blocks on fire (so it can't burn down your ship).
	 */
	public static void lightning(ServerPlayer caster, ServerLevel level, Vec3 at, float damage) {
		LightningBolt bolt = new LightningBolt(EntityTypes.LIGHTNING_BOLT, level);
		bolt.setPos(at);
		bolt.setVisualOnly(true);
		level.addFreshEntity(bolt);
		level.playSound(null, at.x, at.y, at.z, SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.WEATHER, 2.0f, 1.2f);
		for (LivingEntity entity : level.getEntitiesOfClass(LivingEntity.class, new AABB(at, at).inflate(2.5, 3.0, 2.5),
				entity -> canHit(caster, entity))) {
			entity.hurtServer(level, caster.damageSources().source(DamageTypes.LIGHTNING_BOLT, caster), damage);
			entity.igniteForSeconds(3.0f);
		}
	}

	/**
	 * Draws a line of particles from the shooter's eyes and returns what it hit.
	 * spread tilts the line by a small random amount.
	 */
	public static Hit trace(ServerPlayer shooter, ServerLevel level, double range, float spread, ParticleOptions particle) {
		RandomSource random = level.getRandom();
		Vec3 start = shooter.getEyePosition();
		Vec3 direction = shooter.getLookAngle().add(
				(random.nextFloat() - 0.5) * spread, (random.nextFloat() - 0.5) * spread, (random.nextFloat() - 0.5) * spread).normalize();
		Vec3 last = start;

		for (double distance = 0.5; distance <= range; distance += 0.5) {
			Vec3 point = start.add(direction.scale(distance));
			if (distance > 3.0 && ((int) (distance * 2)) % 3 == 0) { // not right in front of your own eyes
				level.sendParticles(particle, point.x, point.y, point.z, 1, 0.0, 0.0, 0.0, 0.0);
			}
			BlockPos pos = BlockPos.containing(point);
			if (!level.getBlockState(pos).getCollisionShape(level, pos).isEmpty()) {
				return new Hit(null, last);
			}
			List<LivingEntity> hits = level.getEntitiesOfClass(LivingEntity.class, new AABB(point, point).inflate(0.35),
					entity -> canHit(shooter, entity));
			if (!hits.isEmpty()) {
				return new Hit(hits.get(0), point);
			}
			last = point;
		}
		return new Hit(null, last);
	}

	/** Never yourself, creative players, your own pets, or your crew and allied crews (shots pass them by). */
	public static boolean canHit(ServerPlayer shooter, LivingEntity entity) {
		if (entity == shooter || !entity.isAlive()) {
			return false;
		}
		if (entity instanceof Player other && (other.isCreative() || other.isSpectator())) {
			return false;
		}
		if (entity instanceof TamableAnimal pet && pet.isOwnedBy(shooter)) {
			return false;
		}
		return !PlayerCrews.friendly(shooter.level().getServer(), shooter, entity);
	}

	/** Pop Green: a ripe, thorny berry bush springs up (only where one can grow). */
	private static void sprout(ServerLevel level, BlockPos pos) {
		BlockState bush = Blocks.SWEET_BERRY_BUSH.defaultBlockState().setValue(SweetBerryBushBlock.AGE, 3);
		if (level.getBlockState(pos).isAir() && bush.canSurvive(level, pos)) {
			level.setBlockAndUpdate(pos, bush);
		}
		level.sendParticles(ParticleTypes.HAPPY_VILLAGER, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5, 12, 0.5, 0.5, 0.5, 0.0);
	}

	private static ParticleOptions trail(Ammo ammo) {
		return switch (ammo) {
			case CANNONBALL -> ParticleTypes.LARGE_SMOKE;
			case SEASTONE_BULLET -> ParticleTypes.BUBBLE_POP;
			case EXPLODING_STAR -> ParticleTypes.FLAME;
			case TABASCO_STAR -> ParticleTypes.SMALL_FLAME;
			case POP_GREEN -> ParticleTypes.COMPOSTER;
			case LEAD_STAR -> ParticleTypes.CRIT;
			default -> ParticleTypes.SMOKE;
		};
	}

	/** A gunshot is a sharp crack plus a deeper boom; a slingshot is a twang. */
	private static void gunSound(ServerPlayer shooter, ServerLevel level, Ammo ammo) {
		float wobble = level.getRandom().nextFloat() * 0.1f;
		double x = shooter.getX(), y = shooter.getY(), z = shooter.getZ();
		switch (ammo.kind()) {
			case BULLET -> {
				level.playSound(null, x, y, z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 0.35f, 1.85f + wobble);
				level.playSound(null, x, y, z, SoundEvents.FIREWORK_ROCKET_BLAST, SoundSource.PLAYERS, 1.0f, 0.65f + wobble);
			}
			case CANNONBALL -> {
				level.playSound(null, x, y, z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 1.0f, 0.9f + wobble);
				level.playSound(null, x, y, z, SoundEvents.FIREWORK_ROCKET_LARGE_BLAST, SoundSource.PLAYERS, 1.0f, 0.5f + wobble);
			}
			case STAR -> level.playSound(null, x, y, z, SoundEvents.CROSSBOW_SHOOT, SoundSource.PLAYERS, 1.0f, 1.2f + wobble);
		}
	}
}
