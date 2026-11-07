package com.onepiecemod.character;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.fx.MoveFx;
import com.onepiecemod.fx.MoveStyle;

/**
 * Makes boss powers look like the Devil Fruit moves players use: flying fists, beams, slashes,
 * shockwaves and so on, drawn with the same shapes (com.onepiecemod.fx). Visual only, no damage.
 */
public class BossVisuals {
	/**
	 * Draws a boss power going from the boss to a spot (usually the target).
	 * BossAbility calls this for every power it uses; a missed attack aims at the warning circle instead.
	 */
	public static void show(String power, Mob boss, Vec3 at, ServerLevel level) {
		Vec3 hand = MoveFx.hand(boss);
		Vec3 chest = at.add(0, 1.0, 0);
		switch (power) {
			case "punch" -> look(level, MoveFx.FLYING_FIST.sized(1.4f), hand, chest, 8, boss);
			case "sword" -> MoveFx.ring(level, boss.position().add(0, 1, 0), 2.5, 6, MoveStyle.SLASH,
					0xFFFFFFFF, 0xFF8CC8FF, 1.3f, 0.1f, 8, null);
			case "fire" -> look(level, MoveFx.FIRE_FIST, hand, chest, 10, boss);
			case "dragon" -> look(level, MoveFx.DRAGON_BREATH, boss.getEyePosition(), chest, 14, boss);
			case "magma" -> look(level, MoveFx.MAGMA_FIST, hand, chest, 10, boss);
			case "ice" -> look(level, MoveFx.ICE_SPEAR, hand, chest, 10, boss);
			case "lightning", "soul" -> MoveFx.bolt(level, at, power.equals("soul") ? 1.4f : 1.0f);
			case "teleport" -> look(level, MoveFx.LASER, boss.position().add(0, 1, 0), chest, 6, boss);
			case "quake" -> MoveFx.quake(boss, level, 8);
			case "pull", "darkness" -> look(level, MoveFx.DARK_PULL, hand, chest, 12, boss);
			case "sand" -> MoveFx.spawn(level, MoveStyle.TORNADO, at, new Vec3(0, 4, 0), MoveFx.SAND, MoveFx.SAND_OUT, 1.0f, 20, boss, null);
			case "string" -> look(level, MoveFx.STRING, hand, chest, 12, boss);
			case "petrify" -> look(level, MoveFx.HEART_ORB, hand, chest, 12, boss);
			case "shadow" -> look(level, new MoveFx.Look(MoveStyle.BEAM, MoveFx.DARK, MoveFx.DARK_OUT, 0.6f, ParticleTypes.SQUID_INK), hand, chest, 12, boss);
			case "smoke" -> look(level, MoveFx.SMOKE_FIST, hand, chest, 10, boss);
			case "gravity" -> {
				look(level, MoveFx.GRAVITY_BLADE, hand, chest, 10, boss);
				MoveFx.spawn(level, MoveStyle.RING, at.add(0, 0.1, 0), new Vec3(3, 0, 0), 0xFFD8B8FF, 0xFF4A2080, 0.8f, 12, null, null);
			}
			case "beast" -> MoveFx.spawn(level, MoveStyle.CLAW, chest, at.subtract(boss.position()).normalize(),
					0xFFFFFFFF, 0xFFE03030, 1.3f, 10, boss, null);
			case "paw" -> look(level, MoveFx.PAW_ORB, hand, chest, 10, boss);
			case "haki" -> MoveFx.shockwave(level, boss.position(), 10, MoveFx.HAKI, MoveFx.HAKI_OUT);
			case "heal" -> MoveFx.spawn(level, MoveStyle.SPHERE, boss.position().add(0, 1, 0), Vec3.ZERO,
					MoveFx.BLUE_FIRE, MoveFx.BLUE_FIRE_OUT, 1.6f, 16, boss, null);
			case "poison" -> MoveFx.shockwave(level, boss.position(), 5, MoveFx.POISON, MoveFx.POISON_OUT);
			case "curse" -> look(level, new MoveFx.Look(MoveStyle.ORB, MoveFx.DARK, MoveFx.DARK_OUT, 1.0f, ParticleTypes.WITCH), hand, chest, 12, boss);
			case "forest" -> MoveFx.spawn(level, MoveStyle.SPIKES, at, new Vec3(2.5, 0, 0), MoveFx.PLANT, MoveFx.PLANT_OUT, 1.0f, 16, boss, null);
			default -> { }
		}
	}

	public static void show(String power, Mob boss, LivingEntity target, ServerLevel level) {
		show(power, boss, target.position(), level);
	}

	private static void look(ServerLevel level, MoveFx.Look look, Vec3 from, Vec3 to, int life, Mob owner) {
		MoveFx.spawn(level, look.style(), from, to.subtract(from), look.color(), look.color2(), look.size(), life, owner, look.trail());
	}
}
