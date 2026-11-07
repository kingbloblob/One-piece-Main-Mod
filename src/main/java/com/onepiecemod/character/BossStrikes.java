package com.onepiecemod.character;

import com.onepiecemod.util.Motion;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.fx.MoveFx;
import com.onepiecemod.fx.MoveStyle;

/**
 * Boss signature moves (phase 3) that hit marked spots on the ground a moment later.
 * Every strike draws a red circle first, so a player who watches the ground can step out of the way.
 *
 * - rain_&lt;look&gt;: magma, lightning, ice... falls onto 5-8 spots around you.
 * - slash_line: a long flying slash along a line toward you (step sideways).
 * - black_hole: everyone is dragged toward the boss, then it bursts (run outward).
 * - ground_wave: a shockwave rolls along the ground (jump to dodge it).
 */
public class BossStrikes {
	/** Things the boss called (its crew) carry this tag, so strikes never hurt them. */
	public static final String MINION_TAG = "onepiece_boss_minion";

	private static final int RED = 0xFFE02020;
	private static final int YELLOW = 0xFFFFE040;

	private enum Kind { RAIN, SLASH, BLACK_HOLE, WAVE }

	private static final class Strike {
		final Kind kind;
		final Vec3 at;
		final double radius;
		final float damage;
		final String look;
		final Vec3 reach; // Slashes: how far and which way the blade flies.
		int fuse;

		Strike(Kind kind, Vec3 at, double radius, int fuse, float damage, String look, Vec3 reach) {
			this.kind = kind;
			this.at = at;
			this.radius = radius;
			this.fuse = fuse;
			this.damage = damage;
			this.look = look;
			this.reach = reach;
		}
	}

	/** How each kind of rain looks. Falling ones drop from the sky, the rest burst out where they land. */
	private record RainLook(MoveFx.Look look, boolean falls) {}

	private static final Map<String, RainLook> RAIN = Map.ofEntries(
			Map.entry("magma", new RainLook(MoveFx.MAGMA_BALL, true)),
			Map.entry("fire", new RainLook(new MoveFx.Look(MoveStyle.ORB, MoveFx.FIRE, MoveFx.FIRE_OUT, 1.8f, ParticleTypes.FLAME), true)),
			Map.entry("ice", new RainLook(MoveFx.ICE_SPEAR.sized(1.6f), true)),
			Map.entry("rock", new RainLook(new MoveFx.Look(MoveStyle.ORB, 0xFFB09070, 0xFF4A3A2A, 2.2f, ParticleTypes.CLOUD), true)),
			Map.entry("metal", new RainLook(new MoveFx.Look(MoveStyle.ORB, 0xFFD0D0D8, 0xFF505060, 1.8f, ParticleTypes.CRIT), true)),
			Map.entry("poison", new RainLook(new MoveFx.Look(MoveStyle.ORB, MoveFx.POISON, MoveFx.POISON_OUT, 1.6f, ParticleTypes.ITEM_SLIME), true)),
			Map.entry("curse", new RainLook(new MoveFx.Look(MoveStyle.ORB, MoveFx.DARK, MoveFx.DARK_OUT, 1.4f, ParticleTypes.WITCH), true)),
			Map.entry("lightning", new RainLook(null, false)),
			Map.entry("light", new RainLook(MoveFx.LASER, false)),
			Map.entry("string", new RainLook(MoveFx.STRING.sized(0.3f), false)),
			Map.entry("sand", new RainLook(new MoveFx.Look(MoveStyle.TORNADO, MoveFx.SAND, MoveFx.SAND_OUT, 1.2f, null), false)),
			Map.entry("smoke", new RainLook(new MoveFx.Look(MoveStyle.TORNADO, MoveFx.SMOKE, MoveFx.SMOKE_OUT, 1.2f, null), false)),
			Map.entry("plant", new RainLook(new MoveFx.Look(MoveStyle.SPIKES, MoveFx.PLANT, MoveFx.PLANT_OUT, 1.0f, null), false)));

	/** Falling looks start this many ticks before they land. */
	private static final int FALL_TICKS = 16;

	private final List<Strike> strikes = new ArrayList<>();

	public boolean isEmpty() {
		return strikes.isEmpty();
	}

	public void clear() {
		strikes.clear();
	}

	/** Starts a signature move. extra (0-3) adds more rain spots on harder fights. */
	public void signature(String signature, Mob boss, LivingEntity target, ServerLevel level, float damage, int extra) {
		com.onepiecemod.anim.CombatAnims.play(boss, com.onepiecemod.anim.Anim.SUMMON, 30);
		level.playSound(null, boss.blockPosition(), com.onepiecemod.sound.BossSounds.SIGNATURE, SoundSource.HOSTILE, 2.0f, 1.0f);
		if (signature.startsWith("rain_")) {
			String look = signature.substring(5);
			int count = 5 + extra;
			for (int i = 0; i < count; i++) {
				Vec3 spot = i == 0 ? target.position() : target.position().add(
						(boss.getRandom().nextDouble() - 0.5) * 12, 0, (boss.getRandom().nextDouble() - 0.5) * 12);
				spot = ground(level, spot);
				strikes.add(new Strike(Kind.RAIN, spot, 2.2, 30 + i * 4, damage * 0.9f, look, null));
			}
		} else if (signature.equals("slash_line")) {
			Vec3 flat = new Vec3(target.getX() - boss.getX(), 0, target.getZ() - boss.getZ());
			Vec3 dir = flat.lengthSqr() < 0.01 ? boss.getLookAngle().multiply(1, 0, 1).normalize() : flat.normalize();
			for (int i = 1; i <= 9; i++) {
				Vec3 spot = ground(level, boss.position().add(dir.scale(i * 2.0)));
				// The first point carries the blade that flies the whole length.
				strikes.add(new Strike(Kind.SLASH, spot, 1.7, 26, damage * 1.3f, i == 1 ? "blade" : "", dir.scale(18)));
			}
		} else if (signature.equals("black_hole")) {
			MoveFx.blackHole(boss, level, 10);
			strikes.add(new Strike(Kind.BLACK_HOLE, boss.position(), 10, 40, damage * 1.5f, "", null));
		} else {
			strikes.add(new Strike(Kind.WAVE, boss.position(), 12, 26, damage * 1.2f, "", null));
		}
	}

	public void tick(Mob boss, ServerLevel level) {
		Iterator<Strike> it = strikes.iterator();
		while (it.hasNext()) {
			Strike strike = it.next();
			strike.fuse--;
			if (strike.fuse % 4 == 0) {
				drawMarker(level, strike);
			}
			switch (strike.kind) {
				case RAIN -> {
					RainLook look = RAIN.getOrDefault(strike.look, RAIN.get("rock"));
					if (look.falls() && strike.fuse == FALL_TICKS) {
						MoveFx.Look l = look.look();
						Vec3 top = strike.at.add(level.getRandom().nextDouble() * 4 - 2, 14, level.getRandom().nextDouble() * 4 - 2);
						MoveFx.spawn(level, l.style(), top, strike.at.subtract(top), l.color(), l.color2(), l.size(), FALL_TICKS, null, l.trail());
					}
				}
				case BLACK_HOLE -> pull(boss, level, strike);
				case WAVE -> {
					if (strike.fuse == 10) {
						for (Player player : players(level, strike.at, strike.radius)) {
							if (player instanceof ServerPlayer serverPlayer) {
								serverPlayer.sendSystemMessage(Component.literal("Jump!").withStyle(net.minecraft.ChatFormatting.RED), true);
							}
						}
					}
				}
				default -> { }
			}
			if (strike.fuse <= 0) {
				land(boss, level, strike);
				it.remove();
			}
		}
	}

	private void land(Mob boss, ServerLevel level, Strike strike) {
		switch (strike.kind) {
			case RAIN -> {
				RainLook look = RAIN.getOrDefault(strike.look, RAIN.get("rock"));
				if (!look.falls()) {
					if (look.look() == null) {
						MoveFx.bolt(level, strike.at, 1.2f);
					} else {
						MoveFx.Look l = look.look();
						Vec3 start = l.style() == MoveStyle.BEAM ? strike.at.add(0, 20, 0) : strike.at;
						Vec3 reach = l.style() == MoveStyle.BEAM ? new Vec3(0, -20, 0) : new Vec3(0, 5, 0);
						MoveFx.spawn(level, l.style(), start, reach, l.color(), l.color2(), l.size(), 14, null, l.trail());
					}
				}
				level.sendParticles(ParticleTypes.EXPLOSION, strike.at.x, strike.at.y + 0.3, strike.at.z, 1, 0, 0, 0, 0);
				level.playSound(null, strike.at.x, strike.at.y, strike.at.z, strike.look.equals("lightning")
						? com.onepiecemod.sound.ModSounds.MOVE_LIGHTNING : com.onepiecemod.sound.BossSounds.STRIKE_LAND, SoundSource.HOSTILE, 1.0f, 0.9f + level.getRandom().nextFloat() * 0.2f);
				for (LivingEntity victim : victims(boss, level, strike.at, strike.radius)) {
					victim.hurtServer(level, boss.damageSources().mobAttack(boss), strike.damage);
					rainEffect(strike.look, victim);
				}
				if (strike.look.equals("plant")) {
					boss.heal(strike.damage * 0.5f); // Ryokugyu's roots feed him.
				}
			}
			case SLASH -> {
				if (strike.look.equals("blade")) {
					MoveFx.spawn(level, MoveStyle.SLASH, boss.getEyePosition().add(0, -0.4, 0), strike.reach,
							0xFFFFFFFF, 0xFF30C050, 2.2f, 12, boss, null);
					level.playSound(null, boss.blockPosition(), com.onepiecemod.sound.BossSounds.SLASH_LINE, SoundSource.HOSTILE, 1.6f, 1.0f);
				}
				for (LivingEntity victim : victims(boss, level, strike.at, strike.radius)) {
					victim.hurtServer(level, boss.damageSources().mobAttack(boss), strike.damage);
				}
			}
			case BLACK_HOLE -> {
				MoveFx.shockwave(level, strike.at, 5, MoveFx.DARK, MoveFx.DARK_OUT);
				level.playSound(null, strike.at.x, strike.at.y, strike.at.z, com.onepiecemod.sound.BossSounds.BLACK_HOLE, SoundSource.HOSTILE, 1.6f, 1.0f);
				for (LivingEntity victim : victims(boss, level, strike.at, 4.5)) {
					victim.hurtServer(level, boss.damageSources().mobAttack(boss), strike.damage);
					victim.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 80, 0));
				}
			}
			case WAVE -> {
				MoveFx.shockwave(level, strike.at, strike.radius, MoveFx.QUAKE, MoveFx.QUAKE_OUT);
				level.playSound(null, strike.at.x, strike.at.y, strike.at.z, com.onepiecemod.sound.BossSounds.GROUND_WAVE, SoundSource.HOSTILE, 1.6f, 1.0f);
				for (LivingEntity victim : victims(boss, level, strike.at, strike.radius)) {
					if (!victim.onGround()) {
						continue; // Jumped over it.
					}
					victim.hurtServer(level, boss.damageSources().mobAttack(boss), strike.damage);
					Vec3 away = victim.position().subtract(strike.at).normalize().scale(1.4);
					victim.setDeltaMovement(away.x, 0.5, away.z);
					Motion.sync(victim);
				}
			}
		}
	}

	/** The black hole drags everyone close by toward its middle until it bursts. */
	private void pull(Mob boss, ServerLevel level, Strike strike) {
		for (LivingEntity victim : victims(boss, level, strike.at, strike.radius)) {
			Vec3 in = strike.at.subtract(victim.position());
			if (in.lengthSqr() > 1.0) {
				Vec3 step = in.normalize().scale(0.09);
				victim.setDeltaMovement(victim.getDeltaMovement().add(step.x, 0, step.z));
				Motion.sync(victim);
			}
		}
	}

	private static void rainEffect(String look, LivingEntity victim) {
		switch (look) {
			case "magma", "fire" -> victim.igniteForSeconds(5);
			case "ice" -> victim.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 3));
			case "poison" -> victim.addEffect(new MobEffectInstance(MobEffects.POISON, 100, 1));
			case "curse" -> victim.addEffect(new MobEffectInstance(MobEffects.WITHER, 60, 1));
			case "string", "plant" -> victim.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 2));
			case "sand" -> victim.addEffect(new MobEffectInstance(MobEffects.HUNGER, 120, 2));
			case "smoke" -> victim.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 40, 0));
			default -> { }
		}
	}

	/** The warning circle: red while there's time, yellow just before it lands. */
	private static void drawMarker(ServerLevel level, Strike strike) {
		double radius = strike.radius;
		if (strike.kind == Kind.BLACK_HOLE) {
			radius = 4.5; // The burst zone; the pull reaches further.
		}
		int color = strike.fuse <= 10 ? YELLOW : RED;
		ring(level, strike.at, radius, color);
		if (strike.kind == Kind.WAVE) {
			ring(level, strike.at, radius * 0.5, color);
		}
	}

	/** A circle of dust on the ground. Shared with the boss's normal wind-up warnings. */
	public static void ring(ServerLevel level, Vec3 center, double radius, int color) {
		DustParticleOptions dust = new DustParticleOptions(color, 1.6f);
		int points = (int) Math.max(10, radius * 7);
		for (int i = 0; i < points; i++) {
			double angle = i * Math.PI * 2 / points;
			level.sendParticles(dust, center.x + Math.cos(angle) * radius, center.y + 0.15, center.z + Math.sin(angle) * radius, 1, 0, 0, 0, 0);
		}
	}

	/** Moves a spot down (or up a little) onto the ground, so markers aren't drawn in the air. */
	static Vec3 ground(ServerLevel level, Vec3 spot) {
		net.minecraft.core.BlockPos pos = net.minecraft.core.BlockPos.containing(spot);
		for (int dy = 2; dy >= -6; dy--) {
			net.minecraft.core.BlockPos below = pos.offset(0, dy - 1, 0);
			if (!level.getBlockState(below).getCollisionShape(level, below).isEmpty()
					&& level.getBlockState(pos.offset(0, dy, 0)).getCollisionShape(level, pos.offset(0, dy, 0)).isEmpty()) {
				return new Vec3(spot.x, pos.getY() + dy, spot.z);
			}
		}
		return spot;
	}

	private static List<Player> players(ServerLevel level, Vec3 at, double radius) {
		return level.getEntitiesOfClass(Player.class, new AABB(at, at).inflate(radius, 3, radius),
				p -> p.isAlive() && !p.isCreative() && !p.isSpectator() && p.position().distanceToSqr(at) <= radius * radius);
	}

	/** Everyone a strike hits: players and their crew, never the boss or the crew it called. */
	static List<LivingEntity> victims(Mob boss, ServerLevel level, Vec3 at, double radius) {
		return level.getEntitiesOfClass(LivingEntity.class, new AABB(at, at).inflate(radius, 3, radius), e -> e != boss && e.isAlive()
				&& !e.entityTags().contains(MINION_TAG)
				&& !(e instanceof Player p && (p.isCreative() || p.isSpectator()))
				&& (e instanceof Player || e instanceof com.onepiecemod.crew.CrewmateEntity
						|| (e instanceof com.onepiecemod.creature.CreatureEntity pet && pet.isTamed()))
				&& horizontal(e.position(), at) <= radius * radius);
	}

	private static double horizontal(Vec3 a, Vec3 b) {
		double dx = a.x - b.x;
		double dz = a.z - b.z;
		return dx * dx + dz * dz;
	}
}
