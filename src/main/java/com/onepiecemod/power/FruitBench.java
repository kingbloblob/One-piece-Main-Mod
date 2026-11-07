package com.onepiecemod.power;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;

import com.mojang.authlib.GameProfile;

import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.entity.FakePlayer;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.OnePieceMod;

/**
 * A test bench for Devil Fruit balance. It only runs when the server is started with
 * -Donepiece.fruitbench=true, so players never see it.
 *
 * Every fruit fights training dummies in three 30 second tests, using its moves whenever they are ready:
 *   duel    - one tough dummy (marked as a boss) 3 blocks away; Strength from the fruit counts as
 *             extra damage on sword swings
 *   crowd   - six dummies around you
 *   survive - an enemy hits you for 3 hearts every second while you fight (counts health saved)
 * The results go to fruit-bench.csv in the server folder (damage per second, health saved per second,
 * and how much of the time the boss dummy was stunned). Other options:
 *   -Donepiece.fruitbench.exit=true            stop the server when done
 *   -Donepiece.fruitbench.only=id1,id2         only test these fruits
 *   -Donepiece.fruitbench.debug=true           log each test every 50 ticks
 */
public class FruitBench {
	/** Dummies with this tag count as bosses for FruitControl. */
	public static final String BOSS_TAG = "onepiece_bench_boss";

	private static final int TEST_TICKS = 600;
	private static final int SETUP_TICKS = 40;
	private static final int ARENAS_PER_BATCH = 24;
	private static final float DUMMY_HEALTH = 1000;
	private static final int SWING_TICKS = 13;   // An iron sword is ready again after about 13 ticks.
	private static final float INCOMING_HIT = 6;

	private enum Test { DUEL, CROWD, SURVIVE }

	/** A player that isn't really connected, so the bench can use moves as one. */
	private static class BenchPlayer extends FakePlayer {
		BenchPlayer(ServerLevel level, GameProfile profile) {
			super(level, profile);
		}

		// Fake players normally can't be hurt at all; the bench needs real hits for the survive test.
		@Override
		public boolean isInvulnerableTo(ServerLevel level, net.minecraft.world.damagesource.DamageSource source) {
			return isPermanentlyInvulnerable();
		}

		void tickBench() {
			tickEffects();
			if (getInvulnerableTime() > 0) {
				setInvulnerableTime(getInvulnerableTime() - 1);
			}
		}
	}

	private static class Arena {
		final DevilFruit fruit; // null = no fruit, the baseline
		final Test test;
		final Vec3 center;
		BenchPlayer caster;
		final List<LivingEntity> dummies = new ArrayList<>();
		final List<Vec3> dummySpots = new ArrayList<>();
		LivingEntity attacker;
		double damageDealt;
		double healthLost;
		int lockedTicks;
		int casts;
		float[] lastHealth;
		float lastCasterHealth;

		Arena(DevilFruit fruit, Test test, Vec3 center) {
			this.fruit = fruit;
			this.test = test;
			this.center = center;
		}
	}

	private static final List<Arena> QUEUE = new ArrayList<>();
	private static final List<Arena> DONE = new ArrayList<>();
	private static List<Arena> batch = new ArrayList<>();
	private static int tick;
	private static int waited;

	public static void initialize() {
		if (!Boolean.getBoolean("onepiece.fruitbench")) {
			return;
		}
		ServerLifecycleEvents.SERVER_STARTED.register(server -> {
			int index = 0;
			for (Test test : Test.values()) {
				if (test != Test.CROWD) {
					QUEUE.add(new Arena(null, test, spot(index++)));
				}
				for (DevilFruit fruit : DevilFruits.ALL) {
					String only = System.getProperty("onepiece.fruitbench.only");
					if (only != null && !java.util.Arrays.asList(only.split(",")).contains(fruit.id())) {
						continue;
					}
					QUEUE.add(new Arena(fruit, test, spot(index++)));
				}
			}
			OnePieceMod.LOGGER.info("[FruitBench] {} tests queued", QUEUE.size());
		});
		ServerTickEvents.END_SERVER_TICK.register(FruitBench::tick);
	}

	// Each arena in a batch gets its own spot far from spawn, 64 blocks apart so moves can't reach the next one.
	private static Vec3 spot(int index) {
		return new Vec3(20000 + (index % ARENAS_PER_BATCH) * 64 + 0.5, 230, 20000.5);
	}

	private static void tick(MinecraftServer server) {
		if (QUEUE.isEmpty() && batch.isEmpty()) {
			return;
		}
		ServerLevel level = server.overworld();

		if (batch.isEmpty()) {
			while (!QUEUE.isEmpty() && batch.size() < ARENAS_PER_BATCH) {
				batch.add(QUEUE.remove(0));
			}
			for (Arena arena : batch) {
				int cx = (int) Math.floor(arena.center.x) >> 4;
				int cz = (int) Math.floor(arena.center.z) >> 4;
				for (int dx = -1; dx <= 1; dx++) {
					for (int dz = -1; dz <= 1; dz++) {
						level.setChunkForced(cx + dx, cz + dz, true);
					}
				}
			}
			tick = 0;
			waited = 0;
			return;
		}

		// Wait until the arenas' chunks are generated and ticking, or dummies there can't be found by moves.
		if (tick == 0 && waited < 2400 && !batch.stream().allMatch(arena -> level.isPositionEntityTicking(BlockPos.containing(arena.center)))) {
			waited++;
			return;
		}
		tick++;
		if (tick == SETUP_TICKS) {
			for (Arena arena : batch) {
				setUp(level, arena);
			}
		} else if (tick > SETUP_TICKS && tick <= SETUP_TICKS + TEST_TICKS) {
			for (Arena arena : batch) {
				run(level, arena, tick - SETUP_TICKS);
			}
		} else if (tick > SETUP_TICKS + TEST_TICKS) {
			for (Arena arena : batch) {
				cleanUp(level, arena);
			}
			DONE.addAll(batch);
			OnePieceMod.LOGGER.info("[FruitBench] {} of {} tests done", DONE.size(), DONE.size() + QUEUE.size());
			batch = new ArrayList<>();
			if (QUEUE.isEmpty()) {
				finish(server);
			}
		}
	}

	private static void setUp(ServerLevel level, Arena arena) {
		String name = "bench" + Math.abs(arena.center.hashCode() % 100000) + arena.test.ordinal();
		arena.caster = new BenchPlayer(level, new GameProfile(UUID.randomUUID(), name.substring(0, Math.min(16, name.length()))));
		arena.caster.setPos(arena.center);
		if (arena.fruit != null) {
			arena.caster.setAttached(ModAttachments.DEVIL_FRUIT, arena.fruit.id());
		}
		arena.caster.setPermanentlyInvulnerable(arena.test != Test.SURVIVE);

		if (arena.test == Test.CROWD) {
			arena.dummySpots.add(arena.center.add(3, 0, 0));
			arena.dummySpots.add(arena.center.add(3, 0, 1.5));
			arena.dummySpots.add(arena.center.add(-4, 0, 3));
			arena.dummySpots.add(arena.center.add(-4, 0, -3));
			arena.dummySpots.add(arena.center.add(0, 0, 5));
			arena.dummySpots.add(arena.center.add(0, 0, -5));
		} else {
			arena.dummySpots.add(arena.center.add(3, 0, 0));
		}
		for (Vec3 at : arena.dummySpots) {
			LivingEntity dummy = dummy(level, at);
			if (arena.test == Test.DUEL) {
				dummy.addTag(BOSS_TAG);
			}
			arena.dummies.add(dummy);
		}
		arena.lastHealth = new float[arena.dummies.size()];
		for (int i = 0; i < arena.dummies.size(); i++) {
			arena.lastHealth[i] = arena.dummies.get(i).getHealth();
		}
		if (arena.test == Test.SURVIVE) {
			arena.attacker = dummy(level, arena.center.add(0, 0, -2));
		}
		arena.lastCasterHealth = arena.caster.getHealth() + arena.caster.getAbsorptionAmount();
	}

	private static LivingEntity dummy(ServerLevel level, Vec3 at) {
		Mob dummy = EntityTypes.VINDICATOR.create(level, EntitySpawnReason.COMMAND);
		dummy.setNoAi(true);
		dummy.setPersistenceRequired();
		dummy.getAttribute(Attributes.MAX_HEALTH).setBaseValue(DUMMY_HEALTH);
		dummy.setHealth(DUMMY_HEALTH);
		dummy.setPos(at);
		level.addFreshEntity(dummy);
		return dummy;
	}

	private static void run(ServerLevel level, Arena arena, int t) {
		BenchPlayer caster = arena.caster;
		caster.tickBench();
		if (Boolean.getBoolean("onepiece.fruitbench.debug") && t % 50 == 0) {
			LivingEntity d = arena.dummies.get(0);
			OnePieceMod.LOGGER.info("[FruitBench] {} {} t={} dummy alive={} removed={} pos={} hp={} caster hp={} dealt={} lost={} casts={}",
					arena.fruit == null ? "none" : arena.fruit.id(), arena.test, t, d.isAlive(), d.isRemoved(), d.position(), d.getHealth(),
					caster.getHealth(), arena.damageDealt, arena.healthLost, arena.casts);
		}

		// Count what happened since last tick, then put everyone back on their spot.
		for (int i = 0; i < arena.dummies.size(); i++) {
			LivingEntity dummy = arena.dummies.get(i);
			if (!dummy.isAlive()) {
				LivingEntity fresh = dummy(level, arena.dummySpots.get(i));
				dummy.entityTags().forEach(fresh::addTag);
				arena.dummies.set(i, fresh);
				arena.damageDealt += arena.lastHealth[i];
				arena.lastHealth[i] = fresh.getHealth();
				continue;
			}
			arena.damageDealt += Math.max(0, arena.lastHealth[i] - dummy.getHealth());
			if (dummy.getHealth() < DUMMY_HEALTH * 0.3f) {
				dummy.setHealth(DUMMY_HEALTH);
			}
			arena.lastHealth[i] = dummy.getHealth();
			if (i == 0 && isLocked(dummy)) {
				arena.lockedTicks++;
			}
			Vec3 at = arena.dummySpots.get(i);
			dummy.teleportTo(at.x, at.y, at.z);
			dummy.setDeltaMovement(Vec3.ZERO);
			dummy.setInvulnerableTime(0);
			dummy.damageCooldownTime = 0;
		}
		caster.setPos(arena.center);
		caster.setDeltaMovement(Vec3.ZERO);
		caster.fallDistance = 0;
		aim(caster, arena.dummies.get(0));

		if (arena.test == Test.SURVIVE) {
			float now = caster.getHealth() + caster.getAbsorptionAmount();
			arena.healthLost += arena.lastCasterHealth - now; // Healing since last tick counts against it.
			if (caster.getHealth() < 8 || !caster.isAlive()) {
				caster.setHealth(caster.getMaxHealth());
			}
			if (t % 20 == 0) {
				float before = caster.getHealth() + caster.getAbsorptionAmount();
				caster.damageCooldownTime = 0;
				caster.setInvulnerableTime(0);
				caster.hurtServer(level, level.damageSources().mobAttack((LivingEntity) arena.attacker), INCOMING_HIT);
				arena.healthLost += before - (caster.getHealth() + caster.getAbsorptionAmount());
			}
			arena.lastCasterHealth = caster.getHealth() + caster.getAbsorptionAmount();
		}

		if (arena.fruit != null && !caster.isInWater()) {
			// Use whichever move is ready, the stronger-feeling Sneak move first.
			if (t % 2 == 0) {
				if (FruitAbilities.secondsLeft(caster, true) == 0) {
					FruitAbilities.use(caster, arena.fruit, true);
					arena.casts++;
				} else if (FruitAbilities.secondsLeft(caster, false) == 0) {
					FruitAbilities.use(caster, arena.fruit, false);
					arena.casts++;
				}
			}
		}

		// The sword: instead of really swinging (hits close together cancel each other out), count what
		// Strength from the fruit adds to each swing.
		if (arena.test == Test.DUEL && t % SWING_TICKS == 1) {
			arena.damageDealt += Math.max(0, caster.getAttributeValue(Attributes.ATTACK_DAMAGE) - 1);
		}
	}

	private static boolean isLocked(LivingEntity dummy) {
		var speed = dummy.getAttribute(Attributes.MOVEMENT_SPEED);
		return speed != null && speed.getValue() < speed.getBaseValue() * 0.45;
	}

	private static void aim(Player player, Entity target) {
		Vec3 from = player.getEyePosition();
		Vec3 to = target.getBoundingBox().getCenter();
		double dx = to.x - from.x;
		double dy = to.y - from.y;
		double dz = to.z - from.z;
		double flat = Math.sqrt(dx * dx + dz * dz);
		player.setYRot((float) Math.toDegrees(Math.atan2(-dx, dz)));
		player.setXRot((float) -Math.toDegrees(Math.atan2(dy, flat)));
		player.setYHeadRot(player.getYRot());
	}

	private static void cleanUp(ServerLevel level, Arena arena) {
		for (LivingEntity dummy : arena.dummies) {
			dummy.discard();
		}
		if (arena.attacker != null) {
			arena.attacker.discard();
		}
		// Anything a move made (golems, effects) goes too.
		for (Entity entity : level.getEntities((Entity) null, new net.minecraft.world.phys.AABB(arena.center, arena.center).inflate(40),
				entity -> !(entity instanceof Player))) {
			entity.discard();
		}
		FruitAbilities.resetCooldowns(arena.caster);
	}

	private static void finish(MinecraftServer server) {
		Map<String, double[]> rows = new LinkedHashMap<>();
		double[] baseline = new double[3];
		for (Arena arena : DONE) {
			double value = switch (arena.test) {
				case DUEL, CROWD -> arena.damageDealt;
				case SURVIVE -> arena.healthLost;
			};
			if (arena.fruit == null) {
				baseline[arena.test.ordinal()] = value;
				continue;
			}
			double[] row = rows.computeIfAbsent(arena.fruit.id(), id -> new double[5]);
			row[arena.test.ordinal()] = value;
			if (arena.test == Test.DUEL) {
				row[3] = arena.lockedTicks * 100.0 / TEST_TICKS;
				row[4] = arena.casts;
			}
		}

		StringBuilder csv = new StringBuilder("fruit,type,duel_extra_dps,crowd_dps,survive_hp_saved_per_s,lock_percent,casts\n");
		for (DevilFruit fruit : DevilFruits.ALL) {
			double[] row = rows.get(fruit.id());
			if (row == null) {
				continue;
			}
			double seconds = TEST_TICKS / 20.0;
			csv.append(String.format(Locale.ROOT, "%s,%s,%.2f,%.2f,%.2f,%.0f,%.0f%n", fruit.id(), fruit.type(),
					(row[0] - baseline[0]) / seconds, row[1] / seconds, (baseline[2] - row[2]) / seconds, row[3], row[4]));
		}
		csv.append(String.format(Locale.ROOT, "# baseline: sword dps %.2f, hp lost per s %.2f%n",
				baseline[0] / (TEST_TICKS / 20.0), baseline[2] / (TEST_TICKS / 20.0)));
		try {
			Path out = server.getServerDirectory().resolve("fruit-bench.csv");
			Files.writeString(out, csv.toString());
			OnePieceMod.LOGGER.info("[FruitBench] wrote {}", out.toAbsolutePath());
		} catch (IOException e) {
			OnePieceMod.LOGGER.error("[FruitBench] could not write results", e);
		}
		if (Boolean.getBoolean("onepiece.fruitbench.exit")) {
			server.halt(false);
		}
	}
}
