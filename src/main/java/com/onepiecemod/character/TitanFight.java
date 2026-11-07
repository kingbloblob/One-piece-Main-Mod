package com.onepiecemod.character;

import com.onepiecemod.util.Motion;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.function.Consumer;

import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.fx.MoveFx;
import com.onepiecemod.fx.MoveStyle;

/**
 * The extra layer on top of a normal boss fight for the Four Emperors and the Admirals ("titans").
 * Any boss with "mechanics" in boss_fights.json is a titan. Titans get:
 *
 * - Phase mechanics: every ~10 seconds from phase 2 on, a move you have to read and dodge
 *   (jump the waves, look away from Big Mom, get out of the magma, leave the closing forest...).
 *   mechanics[0] runs in phase 2, phase 3 alternates mechanics[1] and [0].
 * - Phase 4 at 12% health: the boss awakens, shouts its phase4 line and fires its ultimate
 *   (a mix of its mechanics, bigger), after a long warning. Mechanics come faster after that.
 *
 * Every hit is marked on the ground first (red circle, yellow just before it lands), like BossStrikes.
 * Only players, their crewmates and tamed pets get hurt. Nothing here places or breaks blocks.
 */
public class TitanFight {
	private static final int RED = 0xFFE02020;
	private static final int YELLOW = 0xFFFFE040;
	/** Ticks between mechanics in phase 2 and 3 (10 seconds). Legend rungs and phase 4 make it shorter. */
	private static final int INTERVAL = 200;

	/** A marked circle that does something when its fuse runs out. */
	private static final class Mark {
		final Vec3 at;
		final double radius;
		int fuse;
		final Consumer<Mark> land;

		Mark(Vec3 at, double radius, int fuse, Consumer<Mark> land) {
			this.at = at;
			this.radius = radius;
			this.fuse = fuse;
			this.land = land;
		}
	}

	/** A spot that keeps hurting (magma, ice, gravity, roots) for a while. */
	private static final class Pool {
		final Vec3 at;
		final double radius;
		final String kind;
		int life;

		Pool(Vec3 at, double radius, String kind, int life) {
			this.at = at;
			this.radius = radius;
			this.kind = kind;
			this.life = life;
		}
	}

	/** Something that happens a few ticks from now (follow-up strikes, Big Mom's question). */
	private record Later(int at, Runnable run) {}

	private final BossStrikes strikes;
	private final List<Mark> marks = new ArrayList<>();
	private final List<Pool> pools = new ArrayList<>();
	private final List<Later> later = new ArrayList<>();
	private int clock = 0;
	private int cooldown = 120;
	private int used = 0;
	private boolean ultimateDone = false;

	public TitanFight(BossStrikes strikes) {
		this.strikes = strikes;
	}

	public static boolean isTitan(String characterId) {
		return !BossFightData.get(characterId).mechanics.isEmpty();
	}

	/** Back to the start of the fight (calm reset). */
	public void clear() {
		marks.clear();
		pools.clear();
		later.clear();
		cooldown = 120;
		used = 0;
		ultimateDone = false;
	}

	/**
	 * Runs every boss tick. phase is 1-4, rung is the Legend Ladder rung (0 = not a ladder fight).
	 * From rung 3 on, mechanics already start in phase 1.
	 */
	public void tick(CharacterEntity boss, ServerLevel level, int phase, int rung) {
		clock++;
		tickMarks(level);
		tickPools(boss, level);
		// Pulled out first: a Later may line up more Laters while it runs.
		List<Later> due = new ArrayList<>();
		later.removeIf(next -> clock >= next.at() && due.add(next));
		for (Later next : due) {
			next.run().run();
		}

		LivingEntity target = boss.getTarget();
		if (target == null || !target.isAlive() || boss.distanceTo(target) > 32) {
			return;
		}
		if (phase < 2 && rung < 3) {
			return;
		}
		if (com.onepiecemod.power.SeaWeakness.drainsFruitUser(boss)) {
			return; // Sealed by Seastone or standing in the sea: no fruit tricks.
		}
		if (--cooldown > 0) {
			return;
		}
		int interval = Math.max(110, INTERVAL - rung * 18);
		cooldown = phase >= 4 ? interval * 3 / 4 : interval;
		List<String> mechanics = BossFightData.get(boss.getCharacterId()).mechanics;
		String mechanic = mechanics.get(0);
		if (phase >= 3 && mechanics.size() > 1 && used % 2 == 0) {
			mechanic = mechanics.get(1);
		}
		used++;
		run(mechanic, false, boss, target, level);
	}

	/** Phase 4: the boss awakens and fires its ultimate, once per fight. */
	public void ultimate(CharacterEntity boss, ServerLevel level) {
		if (ultimateDone) {
			return;
		}
		ultimateDone = true;
		BossFightData fight = BossFightData.get(boss.getCharacterId());
		LivingEntity target = boss.getTarget();
		// Hard to stop while it gathers its power, and glowing so you know something big is coming.
		boss.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 60, 2));
		boss.addEffect(new MobEffectInstance(MobEffects.GLOWING, 100, 0));
		com.onepiecemod.anim.CombatAnims.play(boss, com.onepiecemod.anim.Anim.POWER_UP, 40);
		level.sendParticles(ParticleTypes.SONIC_BOOM, boss.getX(), boss.getY() + boss.getBbHeight() * 0.6, boss.getZ(), 1, 0, 0, 0, 0);
		level.playSound(null, boss.blockPosition(), com.onepiecemod.sound.ModSounds.CONQUEROR_AWAKEN, SoundSource.HOSTILE, 3.0f, 0.8f);
		tell(boss, level, Component.literal(boss.getData().name + " unleashes " + (fight.ultimateName.isEmpty() ? "everything" : fight.ultimateName) + "!")
				.withStyle(ChatFormatting.DARK_RED, ChatFormatting.BOLD), false);
		if (target == null) {
			return;
		}
		cooldown = 140; // Breathing room after the ultimate.
		String[] parts = fight.ultimate.isEmpty() ? fight.mechanics.toArray(new String[0]) : fight.ultimate.split("\\+");
		for (int i = 0; i < parts.length; i++) {
			String part = parts[i];
			after(20 + i * 30, () -> {
				if (boss.isAlive() && boss.getTarget() != null) {
					run(part, true, boss, boss.getTarget(), level);
				}
			});
		}
	}

	// ---- The mechanics ----

	private void run(String mechanic, boolean big, CharacterEntity boss, LivingEntity target, ServerLevel level) {
		float damage = (float) boss.getAttributeValue(net.minecraft.world.entity.ai.attributes.Attributes.ATTACK_DAMAGE);
		level.playSound(null, boss.blockPosition(), com.onepiecemod.sound.BossSounds.SIGNATURE, SoundSource.HOSTILE, 1.6f, 1.1f);
		switch (mechanic) {
			case "quake_split" -> quakeSplit(boss, target, level, damage, big ? 5 : 3, "quake");
			case "tsunami" -> tsunami(boss, level, damage, big ? 6 : 4);
			case "zeus_storm" -> zeusStorm(boss, target, level, damage, big ? 8 : 5);
			case "soul_pocus" -> gaze(boss, level, damage, true);
			case "spider_needles" -> strikes.signature("rain_poison", boss, target, level, damage, big ? 8 : 5);
			case "gorosei_glare" -> glare(boss, level, damage, big);
			case "bolo_breath" -> quakeSplit(boss, target, level, damage, big ? 5 : 3, "fire");
			case "drunk" -> drunk(boss, level, big);
			case "liberation" -> liberation(boss, level, damage, big);
			case "gura_yami" -> {
				strikes.signature("black_hole", boss, target, level, damage, 1);
				after(50, () -> tsunami(boss, level, damage, 3));
			}
			case "haoshoku_crash" -> haoshoku(boss, level, damage, big ? 18 : 12);
			case "divine_departure" -> divineDeparture(boss, target, level, damage, big);
			case "magma_pools" -> pools(boss, target, level, damage, big ? 7 : 4, "magma");
			case "meteor_volcano" -> {
				strikes.signature("rain_magma", boss, target, level, damage, big ? 8 : 3);
				after(40, () -> pools(boss, target, level, damage, 2, "magma"));
			}
			case "light_blink" -> lightBlink(boss, target, level, damage, big ? 5 : 3);
			case "yata_mirror" -> gaze(boss, level, damage, false);
			case "yasakani" -> strikes.signature("rain_light", boss, target, level, damage, big ? 8 : 4);
			case "ice_field" -> pools(boss, target, level, damage, big ? 7 : 4, "ice");
			case "ice_age" -> iceAge(boss, level, damage, big ? 20 : 14);
			case "gravity_well" -> pools(boss, target, level, damage, big ? 6 : 3, "gravity");
			case "meteor" -> {
				meteor(boss, target, level, damage);
				if (big) {
					after(25, () -> meteor(boss, boss.getTarget() != null ? boss.getTarget() : target, level, damage));
					after(50, () -> meteor(boss, boss.getTarget() != null ? boss.getTarget() : target, level, damage));
				}
			}
			case "root_field" -> pools(boss, target, level, damage, big ? 7 : 4, "roots");
			case "forest_prison" -> forestPrison(boss, target, level, damage, big ? 10 : 7);
			case "thunder_bagua" -> thunderBagua(boss, target, level, damage);
			default -> strikes.signature("ground_wave", boss, target, level, damage, 0);
		}
	}

	/** Whitebeard's cracks (or Kaido's Bolo Breath): lines of strikes fanning out toward you. Step between them. */
	private void quakeSplit(CharacterEntity boss, LivingEntity target, ServerLevel level, float damage, int lines, String look) {
		Vec3 flat = new Vec3(target.getX() - boss.getX(), 0, target.getZ() - boss.getZ());
		Vec3 dir = flat.lengthSqr() < 0.01 ? boss.getLookAngle().multiply(1, 0, 1).normalize() : flat.normalize();
		boolean fire = look.equals("fire");
		for (int l = 0; l < lines; l++) {
			double angle = Math.toRadians((l - (lines - 1) / 2.0) * 28);
			Vec3 lineDir = new Vec3(dir.x * Math.cos(angle) - dir.z * Math.sin(angle), 0, dir.x * Math.sin(angle) + dir.z * Math.cos(angle));
			if (fire) {
				MoveFx.spawn(level, MoveStyle.BEAM, boss.getEyePosition(), lineDir.scale(18), MoveFx.FIRE, MoveFx.FIRE_OUT, 2.0f, 30, boss, ParticleTypes.FLAME);
			}
			for (int i = 1; i <= 8; i++) {
				Vec3 spot = BossStrikes.ground(level, boss.position().add(lineDir.scale(i * 2.2)));
				boolean first = i == 1;
				mark(spot, 1.5, 26 + i * 2, m -> {
					if (first && !fire) {
						MoveFx.spawn(level, MoveStyle.CRACK, m.at.add(0, 0.2, 0), lineDir.scale(17), MoveFx.QUAKE, MoveFx.QUAKE_OUT, 1.8f, 20, null, null);
						level.playSound(null, m.at.x, m.at.y, m.at.z, com.onepiecemod.sound.ModSounds.MOVE_QUAKE, SoundSource.HOSTILE, 1.4f, 0.8f);
					}
					level.sendParticles(fire ? ParticleTypes.FLAME : ParticleTypes.CLOUD, m.at.x, m.at.y + 0.3, m.at.z, 6, 0.4, 0.2, 0.4, 0.02);
					for (LivingEntity victim : BossStrikes.victims(boss, level, m.at, m.radius)) {
						victim.hurtServer(level, boss.damageSources().mobAttack(boss), damage * 0.9f);
						if (fire) {
							victim.igniteForSeconds(5);
						} else {
							victim.setDeltaMovement(victim.getDeltaMovement().x, 0.9, victim.getDeltaMovement().z);
							Motion.sync(victim);
						}
					}
				});
			}
		}
	}

	/** Rings of shockwave rolling out from the boss one after another. Jump as each one reaches you. */
	private void tsunami(CharacterEntity boss, ServerLevel level, float damage, int rings) {
		Vec3 center = boss.position();
		tell(boss, level, Component.literal("Jump the waves!").withStyle(ChatFormatting.RED), true);
		for (int r = 0; r < rings; r++) {
			double radius = 4 + r * 3;
			mark(center, radius, 22 + r * 8, m -> {
				MoveFx.shockwave(level, m.at, m.radius, MoveFx.QUAKE, MoveFx.QUAKE_OUT);
				level.playSound(null, m.at.x, m.at.y, m.at.z, com.onepiecemod.sound.BossSounds.GROUND_WAVE, SoundSource.HOSTILE, 1.4f, 1.0f);
				for (LivingEntity victim : BossStrikes.victims(boss, level, m.at, m.radius + 1.5)) {
					double dist = Math.sqrt(horizontal(victim.position(), m.at));
					if (dist < m.radius - 1.5 || !victim.onGround()) {
						continue; // Inside the wave already, or jumped it.
					}
					victim.hurtServer(level, boss.damageSources().mobAttack(boss), damage * 0.9f);
					Vec3 away = victim.position().subtract(m.at).multiply(1, 0, 1).normalize().scale(1.3);
					victim.setDeltaMovement(away.x, 0.45, away.z);
					Motion.sync(victim);
				}
			});
		}
	}

	/** Big Mom's Zeus follows one player and strikes where they stood. Keep moving. */
	private void zeusStorm(CharacterEntity boss, LivingEntity target, ServerLevel level, float damage, int strikesLeft) {
		if (target instanceof ServerPlayer player) {
			player.sendSystemMessage(Component.literal("Zeus is following you! Keep moving!").withStyle(ChatFormatting.YELLOW), true);
		}
		for (int i = 0; i < strikesLeft; i++) {
			after(i * 14, () -> {
				if (!target.isAlive() || !boss.isAlive()) {
					return;
				}
				level.sendParticles(ParticleTypes.CLOUD, target.getX(), target.getY() + 6, target.getZ(), 15, 1.2, 0.3, 1.2, 0.0);
				mark(BossStrikes.ground(level, target.position()), 2.0, 16, m -> {
					MoveFx.bolt(level, m.at, 1.2f);
					level.playSound(null, m.at.x, m.at.y, m.at.z, com.onepiecemod.sound.ModSounds.MOVE_LIGHTNING, SoundSource.HOSTILE, 1.2f, 1.0f);
					for (LivingEntity victim : BossStrikes.victims(boss, level, m.at, m.radius)) {
						victim.hurtServer(level, boss.damageSources().mobAttack(boss), damage * 0.8f);
					}
				});
			});
		}
	}

	/**
	 * Big Mom's Soul Pocus ("Life or death?!") and Kizaru's Yata no Kagami flash:
	 * a warning, then everyone close by who is still facing the boss gets hit. Turn your back to dodge it.
	 */
	/** Saturn's glare: "Kneel." Anyone still facing him when it lands is pinned to the ground and loses some health; he heals a bit. */
	private void glare(CharacterEntity boss, ServerLevel level, float damage, boolean big) {
		tell(boss, level, Component.literal("\"Kneel.\" Don't meet the Gorosei's eyes!").withStyle(ChatFormatting.DARK_PURPLE), true);
		level.sendParticles(ParticleTypes.WITCH, boss.getX(), boss.getY() + boss.getBbHeight() * 0.7, boss.getZ(), 30, 0.8, 0.8, 0.8, 0.05);
		after(45, () -> {
			if (!boss.isAlive()) {
				return;
			}
			level.sendParticles(ParticleTypes.SQUID_INK, boss.getX(), boss.getY() + 1, boss.getZ(), 50, 3, 0.5, 3, 0.05);
			level.playSound(null, boss.blockPosition(), SoundEvents.WARDEN_SONIC_BOOM, SoundSource.HOSTILE, 1.5f, 0.6f);
			for (LivingEntity victim : BossStrikes.victims(boss, level, boss.position(), 20)) {
				Vec3 toBoss = boss.getEyePosition().subtract(victim.getEyePosition()).normalize();
				if (victim.getLookAngle().dot(toBoss) < 0.4) {
					continue; // Looked away in time.
				}
				victim.hurtServer(level, boss.damageSources().mobAttack(boss), damage * (big ? 0.9f : 0.7f));
				victim.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, big ? 80 : 50, 4));
				victim.addEffect(new MobEffectInstance(MobEffects.POISON, 100, 1));
				boss.heal(boss.getMaxHealth() * 0.02f); // The Gorosei barely feel their wounds.
			}
		});
	}

	private void gaze(CharacterEntity boss, ServerLevel level, float damage, boolean soul) {
		tell(boss, level, Component.literal(soul ? "\"Life... or death?!\" Look away from her!" : "A blinding light gathers! Look away!")
				.withStyle(soul ? ChatFormatting.LIGHT_PURPLE : ChatFormatting.YELLOW), true);
		level.sendParticles(soul ? ParticleTypes.SOUL : ParticleTypes.END_ROD, boss.getX(), boss.getY() + boss.getBbHeight() * 0.7, boss.getZ(), 30, 0.8, 0.8, 0.8, 0.05);
		after(45, () -> {
			if (!boss.isAlive()) {
				return;
			}
			if (soul) {
				level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, boss.getX(), boss.getY() + 1, boss.getZ(), 40, 2, 1, 2, 0.05);
			} else {
				MoveFx.shockwave(level, boss.position(), 6, MoveFx.LIGHT, MoveFx.LIGHT_OUT);
				level.playSound(null, boss.blockPosition(), com.onepiecemod.sound.ModSounds.MOVE_LIGHT, SoundSource.HOSTILE, 2.0f, 1.0f);
			}
			for (LivingEntity victim : BossStrikes.victims(boss, level, boss.position(), 20)) {
				Vec3 toBoss = boss.getEyePosition().subtract(victim.getEyePosition()).normalize();
				if (victim.getLookAngle().dot(toBoss) < 0.4) {
					continue; // Looked away in time.
				}
				victim.hurtServer(level, boss.damageSources().mobAttack(boss), damage * 0.8f);
				if (soul) {
					victim.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 200, 1));
					boss.heal(boss.getMaxHealth() * 0.03f); // She takes some of your lifespan.
				} else {
					victim.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 80, 0));
				}
			}
		});
	}

	/** Kaido's drunken moods: a random stance for 10 seconds (fast, tough, or hitting harder). */
	private void drunk(CharacterEntity boss, ServerLevel level, boolean big) {
		int mood = boss.getRandom().nextInt(3);
		int ticks = big ? 300 : 200;
		String text = switch (mood) {
			case 0 -> {
				boss.addEffect(new MobEffectInstance(MobEffects.SPEED, ticks, 2));
				yield "Laughing Drunk! Kaido gets fast!";
			}
			case 1 -> {
				boss.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, ticks, 1));
				boss.addEffect(new MobEffectInstance(MobEffects.REGENERATION, ticks, 1));
				yield "Crying Drunk! Kaido shrugs off your hits!";
			}
			default -> {
				boss.addEffect(new MobEffectInstance(MobEffects.STRENGTH, ticks, 1));
				yield "Angry Drunk! Kaido hits harder!";
			}
		};
		level.sendParticles(ParticleTypes.SPLASH, boss.getX(), boss.getY() + boss.getBbHeight(), boss.getZ(), 30, 0.8, 0.4, 0.8, 0.1);
		tell(boss, level, Component.literal(text).withStyle(ChatFormatting.GOLD), true);
	}

	/** Blackbeard drags everyone in. Get caught in the middle and your Devil Fruit stops working for a while. */
	private void liberation(CharacterEntity boss, ServerLevel level, float damage, boolean big) {
		MoveFx.blackHole(boss, level, 10);
		tell(boss, level, Component.literal("The darkness pulls you in! Don't get caught in the middle!").withStyle(ChatFormatting.DARK_PURPLE), true);
		Vec3 center = boss.position();
		for (int t = 0; t < 36; t += 2) {
			after(t, () -> {
				for (LivingEntity victim : BossStrikes.victims(boss, level, center, 11)) {
					Vec3 in = center.subtract(victim.position());
					if (in.lengthSqr() > 1.0) {
						Vec3 step = in.normalize().scale(0.1);
						victim.setDeltaMovement(victim.getDeltaMovement().add(step.x, 0, step.z));
						Motion.sync(victim);
					}
				}
			});
		}
		mark(center, 4.0, 40, m -> {
			MoveFx.shockwave(level, m.at, 5, MoveFx.DARK, MoveFx.DARK_OUT);
			level.playSound(null, m.at.x, m.at.y, m.at.z, com.onepiecemod.sound.BossSounds.BLACK_HOLE, SoundSource.HOSTILE, 1.6f, 0.9f);
			for (LivingEntity victim : BossStrikes.victims(boss, level, m.at, m.radius)) {
				victim.hurtServer(level, boss.damageSources().mobAttack(boss), damage * (big ? 1.4f : 1.0f));
				com.onepiecemod.power.SeaWeakness.seal(victim, big ? 200 : 120);
				victim.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 100, 0));
				if (victim instanceof ServerPlayer player) {
					player.sendSystemMessage(Component.literal("Your Devil Fruit is sealed!").withStyle(ChatFormatting.DARK_PURPLE), true);
				}
			}
		});
	}

	/** Shanks's Conqueror's Haki crashes down around him. Get out of range, or sneak to brace yourself. */
	private void haoshoku(CharacterEntity boss, ServerLevel level, float damage, double radius) {
		tell(boss, level, Component.literal("Conqueror's Haki! Get away, or sneak to brace!").withStyle(ChatFormatting.DARK_RED), true);
		mark(boss.position(), radius, 40, m -> {
			MoveFx.shockwave(level, boss.position(), m.radius, MoveFx.HAKI, 0xFFE03030);
			level.playSound(null, boss.blockPosition(), com.onepiecemod.sound.ModSounds.CONQUEROR_BURST, SoundSource.HOSTILE, 2.5f, 0.9f);
			for (LivingEntity victim : BossStrikes.victims(boss, level, boss.position(), m.radius)) {
				boolean braced = victim.isShiftKeyDown();
				victim.hurtServer(level, boss.damageSources().mobAttack(boss), damage * (braced ? 0.3f : 0.7f));
				if (!braced) {
					victim.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 100, 3));
					victim.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 100, 1));
					victim.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 100, 0));
				}
			}
		});
	}

	/** Shanks's Divine Departure: three long slash lines side by side. Step out sideways. */
	private void divineDeparture(CharacterEntity boss, LivingEntity target, ServerLevel level, float damage, boolean big) {
		Vec3 flat = new Vec3(target.getX() - boss.getX(), 0, target.getZ() - boss.getZ());
		Vec3 dir = flat.lengthSqr() < 0.01 ? boss.getLookAngle().multiply(1, 0, 1).normalize() : flat.normalize();
		Vec3 side = new Vec3(-dir.z, 0, dir.x);
		int lanes = big ? 5 : 3;
		for (int lane = 0; lane < lanes; lane++) {
			Vec3 offset = side.scale((lane - (lanes - 1) / 2.0) * 3.2);
			for (int i = 1; i <= 10; i++) {
				Vec3 spot = BossStrikes.ground(level, boss.position().add(offset).add(dir.scale(i * 2.0)));
				boolean blade = i == 1;
				mark(spot, 1.6, 34, m -> {
					if (blade) {
						MoveFx.spawn(level, MoveStyle.SLASH, m.at.add(0, 1, 0), dir.scale(20), 0xFFFFFFFF, 0xFFE03030, 2.4f, 12, boss, null);
						level.playSound(null, m.at.x, m.at.y, m.at.z, com.onepiecemod.sound.BossSounds.SLASH_LINE, SoundSource.HOSTILE, 1.6f, 0.9f);
					}
					for (LivingEntity victim : BossStrikes.victims(boss, level, m.at, m.radius)) {
						victim.hurtServer(level, boss.damageSources().mobAttack(boss), damage * 1.3f);
					}
				});
			}
		}
	}

	/** Akainu's magma, Aokiji's ice, Fujitora's gravity, Ryokugyu's roots: marked spots that stay dangerous. */
	private void pools(CharacterEntity boss, LivingEntity target, ServerLevel level, float damage, int count, String kind) {
		for (int i = 0; i < count; i++) {
			Vec3 spot = i == 0 ? target.position() : target.position().add(
					(boss.getRandom().nextDouble() - 0.5) * 14, 0, (boss.getRandom().nextDouble() - 0.5) * 14);
			spot = BossStrikes.ground(level, spot);
			mark(spot, 2.6, 24 + i * 3, m -> {
				poolBurst(level, m.at, kind);
				for (LivingEntity victim : BossStrikes.victims(boss, level, m.at, m.radius)) {
					victim.hurtServer(level, boss.damageSources().mobAttack(boss), damage * 0.7f);
				}
				pools.add(new Pool(m.at, m.radius, kind, 160));
			});
		}
	}

	private static void poolBurst(ServerLevel level, Vec3 at, String kind) {
		switch (kind) {
			case "magma" -> MoveFx.spawn(level, MoveStyle.PILLAR, at, new Vec3(0, 4, 0), MoveFx.MAGMA, MoveFx.MAGMA_OUT, 1.4f, 14, null, ParticleTypes.LAVA);
			case "ice" -> MoveFx.spawn(level, MoveStyle.SPIKES, at, new Vec3(0, 3, 0), MoveFx.ICE, MoveFx.ICE_OUT, 1.2f, 20, null, ParticleTypes.SNOWFLAKE);
			case "gravity" -> MoveFx.spawn(level, MoveStyle.RING, at.add(0, 0.1, 0), new Vec3(2.6, 0, 0), 0xFFD8B8FF, 0xFF4A2080, 1.0f, 20, null, null);
			default -> MoveFx.spawn(level, MoveStyle.SPIKES, at, new Vec3(0, 3, 0), MoveFx.PLANT, MoveFx.PLANT_OUT, 1.0f, 20, null, null);
		}
	}

	/** Aokiji's Ice Age: a huge circle freezes over. Get out of it, or be in the air when it lands. */
	private void iceAge(CharacterEntity boss, ServerLevel level, float damage, double radius) {
		tell(boss, level, Component.literal("The ground is freezing over! Get out or jump!").withStyle(ChatFormatting.AQUA), true);
		mark(boss.position(), radius, 50, m -> {
			MoveFx.shockwave(level, m.at, m.radius, MoveFx.ICE, MoveFx.ICE_OUT);
			level.sendParticles(ParticleTypes.SNOWFLAKE, m.at.x, m.at.y + 0.5, m.at.z, 120, m.radius * 0.6, 0.3, m.radius * 0.6, 0.02);
			level.playSound(null, m.at.x, m.at.y, m.at.z, com.onepiecemod.sound.ModSounds.MOVE_ICE, SoundSource.HOSTILE, 2.0f, 0.7f);
			for (LivingEntity victim : BossStrikes.victims(boss, level, m.at, m.radius)) {
				if (!victim.onGround()) {
					continue;
				}
				victim.hurtServer(level, boss.damageSources().mobAttack(boss), damage * 0.8f);
				victim.setTicksFrozen(victim.getTicksRequiredToFreeze() + 120);
				victim.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 5));
			}
		});
	}

	/** Kizaru blinks around you at the speed of light, firing a laser each time. */
	private void lightBlink(CharacterEntity boss, LivingEntity target, ServerLevel level, float damage, int blinks) {
		for (int i = 0; i < blinks; i++) {
			after(i * 16, () -> {
				if (!boss.isAlive() || !target.isAlive()) {
					return;
				}
				double angle = boss.getRandom().nextDouble() * Math.PI * 2;
				Vec3 spot = BossStrikes.ground(level, target.position().add(Math.cos(angle) * 7, 0, Math.sin(angle) * 7));
				if (level.noCollision(boss, boss.getBoundingBox().move(spot.subtract(boss.position())))) {
					level.sendParticles(ParticleTypes.END_ROD, boss.getX(), boss.getY() + 1, boss.getZ(), 15, 0.3, 0.6, 0.3, 0.05);
					boss.teleportTo(spot.x, spot.y, spot.z);
					level.playSound(null, boss.blockPosition(), com.onepiecemod.sound.ModSounds.MOVE_WARP, SoundSource.HOSTILE, 1.0f, 1.4f);
				}
				Vec3 aim = BossStrikes.ground(level, target.position());
				mark(aim, 1.8, 14, m -> {
					Vec3 from = boss.getEyePosition();
					MoveFx.spawn(level, MoveStyle.BEAM, from, m.at.add(0, 0.8, 0).subtract(from), 0xFFFFFFB0, 0xFFFFC000, 1.2f, 10, boss, null);
					level.playSound(null, m.at.x, m.at.y, m.at.z, com.onepiecemod.sound.ModSounds.MOVE_LIGHT, SoundSource.HOSTILE, 1.2f, 1.2f);
					for (LivingEntity victim : BossStrikes.victims(boss, level, m.at, m.radius)) {
						victim.hurtServer(level, boss.damageSources().mobAttack(boss), damage * 0.7f);
					}
				});
			});
		}
	}

	/** Fujitora pulls a meteor out of the sky onto you. A big circle and a long warning: run. */
	private void meteor(CharacterEntity boss, LivingEntity target, ServerLevel level, float damage) {
		tell(boss, level, Component.literal("A meteor is falling! Get out of the circle!").withStyle(ChatFormatting.LIGHT_PURPLE), true);
		Vec3 at = BossStrikes.ground(level, target.position());
		after(44, () -> MoveFx.meteor(level, at, new MoveFx.Look(MoveStyle.ORB, 0xFFB09070, 0xFF4A3A2A, 5.0f, ParticleTypes.LARGE_SMOKE)));
		mark(at, 5.0, 60, m -> {
			level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, m.at.x, m.at.y + 0.5, m.at.z, 1, 0, 0, 0, 0);
			MoveFx.shockwave(level, m.at, 6, 0xFFD8B8FF, 0xFF4A2080);
			level.playSound(null, m.at.x, m.at.y, m.at.z, com.onepiecemod.sound.ModSounds.MOVE_EXPLOSION, SoundSource.HOSTILE, 2.5f, 0.7f);
			for (LivingEntity victim : BossStrikes.victims(boss, level, m.at, m.radius)) {
				victim.hurtServer(level, boss.damageSources().mobAttack(boss), damage * 1.8f);
				Vec3 away = victim.position().subtract(m.at).multiply(1, 0, 1).normalize().scale(1.5);
				victim.setDeltaMovement(away.x, 0.6, away.z);
				Motion.sync(victim);
			}
		});
	}

	/** Ryokugyu's forest closes around you. Leave the circle before it does. */
	private void forestPrison(CharacterEntity boss, LivingEntity target, ServerLevel level, float damage, double radius) {
		Vec3 at = BossStrikes.ground(level, target.position());
		tell(boss, level, Component.literal("The forest is closing in! Get out of the circle!").withStyle(ChatFormatting.GREEN), true);
		mark(at, radius, 50, m -> {
			MoveFx.ring(level, m.at, m.radius, 10, MoveStyle.SPIKES, MoveFx.PLANT, MoveFx.PLANT_OUT, 1.4f, 3.5f, 30, null);
			level.playSound(null, m.at.x, m.at.y, m.at.z, com.onepiecemod.sound.ModSounds.MOVE_PLANT, SoundSource.HOSTILE, 2.0f, 0.8f);
			for (LivingEntity victim : BossStrikes.victims(boss, level, m.at, m.radius)) {
				victim.hurtServer(level, boss.damageSources().mobAttack(boss), damage * 1.1f);
				victim.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 5));
				boss.heal(damage * 0.5f);
			}
		});
	}

	/** Kaido's Thunder Bagua: he marks you, then crashes down on the mark with his club. */
	private void thunderBagua(CharacterEntity boss, LivingEntity target, ServerLevel level, float damage) {
		Vec3 at = BossStrikes.ground(level, target.position());
		tell(boss, level, Component.literal("Thunder Bagua! Get off the mark!").withStyle(ChatFormatting.YELLOW), true);
		mark(at, 3.5, 46, m -> {
			if (level.noCollision(boss, boss.getBoundingBox().move(m.at.subtract(boss.position())))) {
				boss.teleportTo(m.at.x, m.at.y, m.at.z);
			}
			com.onepiecemod.anim.CombatAnims.play(boss, com.onepiecemod.anim.Anim.GROUND_SLAM);
			MoveFx.bolt(level, m.at, 2.0f);
			MoveFx.shockwave(level, m.at, 5, MoveFx.SPARK, MoveFx.SPARK_OUT);
			level.playSound(null, m.at.x, m.at.y, m.at.z, com.onepiecemod.sound.ModSounds.MOVE_LIGHTNING, SoundSource.HOSTILE, 2.5f, 0.7f);
			for (LivingEntity victim : BossStrikes.victims(boss, level, m.at, m.radius)) {
				victim.hurtServer(level, boss.damageSources().mobAttack(boss), damage * 2.2f);
				Vec3 away = victim.position().subtract(m.at).multiply(1, 0, 1).normalize().scale(1.8);
				victim.setDeltaMovement(away.x, 0.7, away.z);
				Motion.sync(victim);
			}
		});
	}

	// ---- Plumbing ----

	private void mark(Vec3 at, double radius, int fuse, Consumer<Mark> land) {
		marks.add(new Mark(at, radius, fuse, land));
	}

	private void after(int ticks, Runnable run) {
		later.add(new Later(clock + ticks, run));
	}

	private void tickMarks(ServerLevel level) {
		List<Mark> landed = new ArrayList<>();
		for (Iterator<Mark> it = marks.iterator(); it.hasNext();) {
			Mark mark = it.next();
			mark.fuse--;
			if (mark.fuse % 4 == 0) {
				BossStrikes.ring(level, mark.at, mark.radius, mark.fuse <= 10 ? YELLOW : RED);
			}
			if (mark.fuse <= 0) {
				it.remove();
				landed.add(mark);
			}
		}
		for (Mark mark : landed) {
			mark.land.accept(mark);
		}
	}

	private void tickPools(CharacterEntity boss, ServerLevel level) {
		float damage = (float) boss.getAttributeValue(net.minecraft.world.entity.ai.attributes.Attributes.ATTACK_DAMAGE);
		for (Iterator<Pool> it = pools.iterator(); it.hasNext();) {
			Pool pool = it.next();
			pool.life--;
			if (pool.life <= 0) {
				it.remove();
				continue;
			}
			if (pool.life % 5 == 0) {
				ParticleOptions particle = switch (pool.kind) {
					case "magma" -> ParticleTypes.LAVA;
					case "ice" -> ParticleTypes.SNOWFLAKE;
					case "gravity" -> ParticleTypes.REVERSE_PORTAL;
					default -> ParticleTypes.COMPOSTER;
				};
				level.sendParticles(particle, pool.at.x, pool.at.y + 0.2, pool.at.z, 4, pool.radius * 0.5, 0.05, pool.radius * 0.5, 0.0);
			}
			if (pool.life % 20 == 0) {
				BossStrikes.ring(level, pool.at, pool.radius, 0xFFFF8020);
			}
			if (pool.life % 10 != 0) {
				continue;
			}
			for (LivingEntity victim : BossStrikes.victims(boss, level, pool.at, pool.radius)) {
				switch (pool.kind) {
					case "magma" -> {
						victim.igniteForSeconds(3);
						victim.hurtServer(level, boss.damageSources().mobAttack(boss), damage * 0.15f);
					}
					case "ice" -> {
						victim.setTicksFrozen(Math.min(victim.getTicksFrozen() + 40, victim.getTicksRequiredToFreeze() + 60));
						victim.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 3));
					}
					case "gravity" -> {
						victim.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 4));
						victim.setDeltaMovement(victim.getDeltaMovement().x * 0.3, -0.8, victim.getDeltaMovement().z * 0.3);
						Motion.sync(victim);
						victim.hurtServer(level, boss.damageSources().mobAttack(boss), damage * 0.1f);
					}
					default -> {
						victim.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 30, 4));
						victim.hurtServer(level, boss.damageSources().mobAttack(boss), damage * 0.1f);
						boss.heal(damage * 0.2f); // Ryokugyu drinks from his roots.
					}
				}
			}
		}
	}

	/** Tells everyone fighting this boss (within 40 blocks). overlay = above the hotbar instead of in chat. */
	private static void tell(CharacterEntity boss, ServerLevel level, Component text, boolean overlay) {
		for (Player player : level.getEntitiesOfClass(Player.class, boss.getBoundingBox().inflate(40), p -> !p.isSpectator())) {
			if (player instanceof ServerPlayer serverPlayer) {
				serverPlayer.sendSystemMessage(text, overlay);
			}
		}
	}

	private static double horizontal(Vec3 a, Vec3 b) {
		double dx = a.x - b.x;
		double dz = a.z - b.z;
		return dx * dx + dz * dz;
	}
}
