package com.onepiecemod.character;

import com.onepiecemod.util.Motion;
import java.util.List;

import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

/**
 * Boss special attacks. Each character's "power" in characters.json picks one of these.
 * Any mob can use them (Devil Fruit bounty hunters do too), not only story characters.
 * A boss uses its attack every 5 seconds (every 3 seconds once it's below half health).
 */
public class BossAbility {
	public static void use(String power, Mob boss, LivingEntity target, ServerLevel level) {
		float damage = (float) boss.getAttributeValue(Attributes.ATTACK_DAMAGE);
		com.onepiecemod.anim.CombatAnims.bossPower(boss, power); // The boss's body acts out the attack.
		BossVisuals.show(power, boss, target, level); // And the attack itself is drawn like a Devil Fruit move.

		switch (power) {
			case "punch" -> { // Gomu Gomu no Pistol and friends: a punch that sends you flying.
				hit(boss, target, level, damage);
				push(target, boss, 2.5, 0.5);
				effect(level, target, ParticleTypes.EXPLOSION, 1, com.onepiecemod.sound.ModSounds.MOVE_IMPACT);
			}
			case "sword" -> { // A wide slash that hits everyone close by.
				for (Player player : playersNear(boss, level, 4.0)) {
					hit(boss, player, level, damage * 1.2f);
				}
				effect(level, boss, ParticleTypes.SWEEP_ATTACK, 8, com.onepiecemod.sound.ModSounds.MOVE_BLADE);
			}
			case "fire", "dragon" -> { // Flames (Ace, Sanji, King). Kaido's dragon breath is the same but stronger.
				float multiplier = power.equals("dragon") ? 1.5f : 1.0f;
				for (Player player : playersNear(boss, level, power.equals("dragon") ? 8.0 : 5.0)) {
					player.igniteForSeconds(5 * multiplier);
					hit(boss, player, level, damage * 0.5f * multiplier);
				}
				effect(level, boss, ParticleTypes.FLAME, 40, power.equals("dragon") ? com.onepiecemod.sound.ModSounds.MOVE_DRAGON_ROAR : com.onepiecemod.sound.ModSounds.MOVE_FIRE);
			}
			case "magma" -> { // Akainu: magma burns longer and hurts more.
				target.igniteForSeconds(10);
				hit(boss, target, level, damage * 1.5f);
				effect(level, target, ParticleTypes.LAVA, 20, com.onepiecemod.sound.ModSounds.MOVE_MAGMA);
			}
			case "ice" -> { // Aokiji, Yamato, Brook: freeze in place.
				target.setTicksFrozen(target.getTicksRequiredToFreeze() + 100);
				target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 3));
				hit(boss, target, level, damage * 0.5f);
				effect(level, target, ParticleTypes.SNOWFLAKE, 30, com.onepiecemod.sound.ModSounds.MOVE_ICE);
			}
			case "lightning" -> { // Enel, Nami, Vegapunk: a bolt from the sky.
				lightning(level, target);
			}
			case "soul" -> { // Big Mom: steals your lifespan, and Zeus strikes.
				target.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 100, 1));
				target.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 100, 0));
				lightning(level, target);
			}
			case "teleport" -> { // Kizaru's light speed, Law's Shambles: suddenly right next to you.
				Vec3 behind = target.position().subtract(target.getLookAngle().scale(1.5));
				effect(level, boss, ParticleTypes.END_ROD, 20, com.onepiecemod.sound.ModSounds.MOVE_WARP);
				boss.teleportTo(behind.x, target.getY(), behind.z);
				hit(boss, target, level, damage);
			}
			case "quake" -> { // Whitebeard, Sengoku, Franky: shockwave that throws everyone back.
				for (Player player : playersNear(boss, level, 8.0)) {
					hit(boss, player, level, damage * 0.8f);
					push(player, boss, 3.0, 0.8);
				}
				effect(level, boss, ParticleTypes.EXPLOSION_EMITTER, 1, com.onepiecemod.sound.ModSounds.MOVE_QUAKE);
			}
			case "pull", "darkness" -> { // Kid's magnetism, Blackbeard's black hole: pulls you in.
				push(target, boss, -2.0, 0.3);
				if (power.equals("darkness")) {
					target.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 100, 0));
					target.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 100, 1));
				}
				effect(level, target, ParticleTypes.SQUID_INK, 30, power.equals("darkness") ? com.onepiecemod.sound.ModSounds.MOVE_DARKNESS : com.onepiecemod.sound.ModSounds.MOVE_GRAVITY);
			}
			case "sand" -> { // Crocodile: dries you out.
				target.addEffect(new MobEffectInstance(MobEffects.HUNGER, 200, 2));
				target.addEffect(new MobEffectInstance(MobEffects.WITHER, 80, 1));
				effect(level, target, ParticleTypes.WHITE_ASH, 40, com.onepiecemod.sound.ModSounds.MOVE_SAND);
			}
			case "string" -> { // Doflamingo, Robin: strings / arms hold you up in the air.
				target.addEffect(new MobEffectInstance(MobEffects.LEVITATION, 30, 1));
				target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 2));
				effect(level, target, ParticleTypes.CRIT, 20, com.onepiecemod.sound.ModSounds.MOVE_STRING);
			}
			case "petrify" -> { // Hancock's love beam, Katakuri's mochi: you can't move.
				target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 9));
				target.addEffect(new MobEffectInstance(MobEffects.MINING_FATIGUE, 60, 2));
				effect(level, target, ParticleTypes.HEART, 10, com.onepiecemod.sound.BossSounds.PETRIFY);
			}
			case "shadow", "smoke" -> { // Moria steals your shadow, Smoker blinds you.
				target.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 80, 0));
				target.addEffect(new MobEffectInstance(power.equals("smoke") ? MobEffects.SLOWNESS : MobEffects.WEAKNESS, 80, 1));
				effect(level, target, ParticleTypes.LARGE_SMOKE, 40, power.equals("smoke") ? com.onepiecemod.sound.ModSounds.MOVE_SMOKE : com.onepiecemod.sound.ModSounds.MOVE_DARKNESS);
			}
			case "gravity" -> { // Fujitora slams you into the ground.
				target.setDeltaMovement(target.getDeltaMovement().x, -2.0, target.getDeltaMovement().z);
				Motion.sync(target);
				target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 4));
				hit(boss, target, level, damage);
				effect(level, target, ParticleTypes.CLOUD, 30, com.onepiecemod.sound.ModSounds.MOVE_GRAVITY);
			}
			case "beast" -> { // Zoan users (Lucci, Drake, Chopper): pounce.
				Vec3 leap = target.position().subtract(boss.position()).normalize().scale(1.2);
				boss.setDeltaMovement(leap.x, 0.5, leap.z);
				Motion.sync(boss);
				hit(boss, target, level, damage * 1.2f);
				effect(level, boss, ParticleTypes.CRIT, 15, com.onepiecemod.sound.ModSounds.MOVE_BEAST_ROAR);
			}
			case "paw" -> { // Kuma and Dragon: blasts you high into the sky.
				target.setDeltaMovement(target.getDeltaMovement().x, 2.5, target.getDeltaMovement().z);
				Motion.sync(target);
				effect(level, target, ParticleTypes.CLOUD, 30, com.onepiecemod.sound.BossSounds.PAW);
			}
			case "haki" -> { // Conqueror's Haki: everyone nearby feels it.
				for (Player player : playersNear(boss, level, 10.0)) {
					player.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 100, 0));
					player.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 2));
					hit(boss, player, level, damage * 0.5f);
				}
				effect(level, boss, ParticleTypes.ELECTRIC_SPARK, 60, com.onepiecemod.sound.ModSounds.CONQUEROR_BURST);
			}
			case "heal" -> { // Marco's phoenix flames heal him.
				boss.heal(boss.getMaxHealth() * 0.15f);
				effect(level, boss, ParticleTypes.SOUL_FIRE_FLAME, 40, com.onepiecemod.sound.BossSounds.HEAL);
			}
			case "rocks" -> { // Rocks D. Xebec: the strongest pirate of his era. Each time, one of his attacks at random.
				use(resolve(power, boss.getRandom()), boss, target, level);
			}
			case "poison" -> { // Magellan's Hydra: a cloud of poison hits everyone close by.
				for (Player player : playersNear(boss, level, 5.0)) {
					player.addEffect(new MobEffectInstance(MobEffects.POISON, 120, 1));
					hit(boss, player, level, damage * 0.5f);
				}
				effect(level, boss, ParticleTypes.ITEM_SLIME, 40, com.onepiecemod.sound.ModSounds.MOVE_POISON);
			}
			case "curse" -> { // Hawkins' straw dolls, Bonney's age powers.
				target.addEffect(new MobEffectInstance(MobEffects.WITHER, 100, 1));
				target.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 100, 1));
				effect(level, target, ParticleTypes.WITCH, 30, com.onepiecemod.sound.ModSounds.MOVE_CURSE);
			}
			case "forest" -> { // Ryokugyu's roots drain you and heal him.
				hit(boss, target, level, damage * 0.8f);
				boss.heal(damage);
				target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 2));
				effect(level, target, ParticleTypes.HAPPY_VILLAGER, 30, com.onepiecemod.sound.ModSounds.MOVE_PLANT);
			}
			default -> hit(boss, target, level, damage);
		}
	}

	private static final String[] ROCKS_MOVES = {"darkness", "quake", "haki", "punch", "sword"};

	/** "rocks" is a random one of Xebec's attacks. Picking it early lets the warning circle match the attack. */
	public static String resolve(String power, net.minecraft.util.RandomSource random) {
		return power.equals("rocks") ? ROCKS_MOVES[random.nextInt(ROCKS_MOVES.length)] : power;
	}

	/**
	 * How far around the boss an area power reaches, or 0 for powers aimed at one target.
	 * Used for the warning circle before the attack.
	 */
	public static double areaRadius(String power) {
		return switch (power) {
			case "sword" -> 4.0;
			case "fire", "poison" -> 5.0;
			case "dragon", "quake" -> 8.0;
			case "haki" -> 10.0;
			default -> 0.0;
		};
	}

	/** Powers that close the gap (or heal) happen wherever the target is; they can't be dodged by stepping aside. */
	public static boolean alwaysHits(String power) {
		return power.equals("teleport") || power.equals("beast") || power.equals("heal");
	}

	private static void hit(Mob boss, LivingEntity target, ServerLevel level, float damage) {
		target.hurtServer(level, boss.damageSources().mobAttack(boss), damage);
	}

	/** Pushes the target away from the boss (a negative strength pulls it closer). */
	private static void push(LivingEntity target, Mob boss, double strength, double up) {
		Vec3 away = target.position().subtract(boss.position()).normalize().scale(strength);
		target.setDeltaMovement(away.x, up, away.z);
		Motion.sync(target);
	}

	private static List<Player> playersNear(Mob boss, ServerLevel level, double radius) {
		return level.getEntitiesOfClass(Player.class, boss.getBoundingBox().inflate(radius),
				player -> player.isAlive() && !player.isCreative() && !player.isSpectator());
	}

	private static void lightning(ServerLevel level, LivingEntity target) {
		LightningBolt bolt = new LightningBolt(EntityTypes.LIGHTNING_BOLT, level);
		bolt.setPos(target.getX(), target.getY(), target.getZ());
		level.addFreshEntity(bolt);
		level.playSound(null, target.getX(), target.getY(), target.getZ(), com.onepiecemod.sound.ModSounds.MOVE_LIGHTNING, target.getSoundSource(), 1.0f, 1.0f);
	}

	private static void effect(ServerLevel level, LivingEntity at, ParticleOptions particle, int count, SoundEvent sound) {
		level.sendParticles(particle, at.getX(), at.getY() + at.getBbHeight() / 2, at.getZ(), count, 0.6, 0.6, 0.6, 0.05);
		level.playSound(null, at.getX(), at.getY(), at.getZ(), sound, at.getSoundSource(), 1.0f, 1.0f);
	}
}
