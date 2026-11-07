package com.onepiecemod.empire;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.bounty.MarineHunters;
import com.onepiecemod.bounty.MarineWarship;
import com.onepiecemod.bounty.NavyRaids;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.ship.ShipEntity;

/**
 * A Buster Call: the World Government's answer to an Emperor. Only title holders get them.
 *
 * A fleet of warships (3 for an Emperor, 4 for the Pirate King, 5 for the King of the World)
 * shells the area for two minutes, and Admirals land to finish the job: one for an Emperor,
 * two for the Pirate King, and two plus Garp and Fleet Admiral Sengoku for the King of the World.
 * Beat every Admiral to win (and a huge bounty). Run 100 blocks away for 30 seconds to escape.
 *
 * Every minute a title holder rolls a chance (3% / 5% / 8%), with a 30 minute break after each one.
 */
public class BusterCall {
	private static final int CHECK_EVERY_TICKS = 20 * 60;
	private static final int BREAK_TICKS = 20 * 60 * 30;
	private static final int WARNING_TICKS = 20 * 15;
	private static final int SHELLING_TICKS = 20 * 120;
	private static final int ADMIRALS_LAND_TICKS = 20 * 20;
	private static final double ESCAPE_DISTANCE = 100.0;
	private static final int ESCAPE_TICKS = 20 * 30;
	public static final String TAG = "onepiece_buster_call";

	private static final Map<UUID, Call> calls = new HashMap<>();
	private static final Map<UUID, Integer> nextCallTick = new HashMap<>();

	public static boolean isActive(ServerPlayer player) {
		return calls.containsKey(player.getUUID());
	}

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			Iterator<Call> it = calls.values().iterator();
			while (it.hasNext()) {
				Call call = it.next();
				if (!call.tick(server)) {
					call.cleanUp();
					nextCallTick.put(call.pirateId, server.getTickCount() + BREAK_TICKS);
					it.remove();
				}
			}
			if (server.getTickCount() % CHECK_EVERY_TICKS != 0) {
				return;
			}
			int now = server.getTickCount();
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				Title title = EmpireData.title(player);
				if (title == Title.NONE || isActive(player) || NavyRaids.isRaiding(player) || !canBeCalled(player)
						|| now < nextCallTick.getOrDefault(player.getUUID(), BREAK_TICKS)) {
					continue;
				}
				if (player.getRandom().nextFloat() < chance(title)) {
					start(player);
				}
			}
		});

		// Ships from a Buster Call that is no longer running (for example after a restart) are gone.
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity.entityTags().contains(TAG) && !isActiveMember(entity.getUUID())
					&& (!(entity instanceof ShipEntity ship) || ship.getPassengers().isEmpty())) {
				entity.discard();
			}
		});
	}

	private static float chance(Title title) {
		return switch (title) {
			case EMPEROR -> 0.03f;
			case PIRATE_KING -> 0.05f;
			case KING_OF_THE_WORLD -> 0.08f;
			default -> 0f;
		};
	}

	private static boolean canBeCalled(ServerPlayer player) {
		ServerLevel level = (ServerLevel) player.level();
		return level.dimension() == Level.OVERWORLD && level.getDifficulty() != Difficulty.PEACEFUL
				&& !player.isCreative() && !player.isSpectator();
	}

	private static boolean isActiveMember(UUID id) {
		for (Call call : calls.values()) {
			if (call.ships.contains(id) || call.admirals.contains(id)) {
				return true;
			}
		}
		return false;
	}

	/** Starts a Buster Call on the player. Returns an error message, or null if it started. */
	public static String start(ServerPlayer player) {
		if (isActive(player)) {
			return "A Buster Call is already on its way.";
		}
		Title title = EmpireData.title(player);
		Call call = new Call(player, title == Title.NONE ? Title.EMPEROR : title);
		calls.put(player.getUUID(), call);
		call.announce(player);
		return null;
	}

	public static boolean stop(ServerPlayer player) {
		Call call = calls.remove(player.getUUID());
		if (call == null) {
			return false;
		}
		call.cleanUp();
		return true;
	}

	// ------------------------------------------------------------------------------------------

	private static class Call {
		final UUID pirateId;
		final ServerLevel level;
		final BlockPos center;
		final Title title;
		final ServerBossEvent bar;
		final List<UUID> ships = new ArrayList<>();
		final List<UUID> admirals = new ArrayList<>();
		final List<Shell> shells = new ArrayList<>();
		int age = 0;
		int awayTicks = 0;
		float admiralHealth = 1;

		Call(ServerPlayer pirate, Title title) {
			this.pirateId = pirate.getUUID();
			this.level = (ServerLevel) pirate.level();
			this.center = pirate.blockPosition();
			this.title = title;
			this.bar = new ServerBossEvent(UUID.randomUUID(), Component.literal("BUSTER CALL"), BossEvent.BossBarColor.RED,
					BossEvent.BossBarOverlay.PROGRESS);
		}

		void announce(ServerPlayer pirate) {
			EmpireRanks.broadcast(level.getServer(), Component.literal("The World Government has issued a BUSTER CALL on "
					+ title.displayName + " " + pirate.getName().getString() + "!").withStyle(ChatFormatting.DARK_RED, ChatFormatting.BOLD));
			pirate.sendSystemMessage(Component.literal("The fleet arrives in 15 seconds. Survive the shelling and beat the Admirals, or run!")
					.withStyle(ChatFormatting.RED));
			level.playSound(null, center, SoundEvents.RAID_HORN.value(), SoundSource.HOSTILE, 6.0f, 0.6f);
			int fleet = 2 + title.ordinal();
			for (int i = 0; i < fleet; i++) {
				ShipEntity ship = MarineWarship.spawn(level, center, pirate.getRandom());
				if (ship == null) {
					break; // No sea nearby: the shells come from ships beyond the horizon instead.
				}
				ship.removeTag(MarineWarship.TAG); // Ours, not a raid's: keep NavyRaids from removing it.
				ship.addTag(TAG);
				ships.add(ship.getUUID());
			}
		}

		/** Returns false when the Buster Call is over. */
		boolean tick(MinecraftServer server) {
			ServerPlayer pirate = server.getPlayerList().getPlayer(pirateId);
			if (pirate == null || pirate.level() != level) {
				return false;
			}
			age++;
			updateBar();

			if (pirate.distanceToSqr(Vec3.atCenterOf(center)) > ESCAPE_DISTANCE * ESCAPE_DISTANCE) {
				if (++awayTicks >= ESCAPE_TICKS) {
					pirate.sendSystemMessage(Component.literal("You escaped the Buster Call. The island is in ruins, but you live.")
							.withStyle(ChatFormatting.GRAY));
					return false;
				}
			} else {
				awayTicks = 0;
			}

			tickShells();
			if (age < WARNING_TICKS) {
				bar.setName(Component.literal("BUSTER CALL: the fleet is coming"));
				bar.setProgress(age / (float) WARNING_TICKS);
				return true;
			}
			if (age < WARNING_TICKS + SHELLING_TICKS && pirate.isAlive() && age % shellEvery() == 0) {
				fire(pirate);
			}
			if (age == WARNING_TICKS + ADMIRALS_LAND_TICKS) {
				landAdmirals(pirate);
			}
			if (age <= WARNING_TICKS + ADMIRALS_LAND_TICKS) {
				bar.setName(Component.literal("BUSTER CALL: bombardment"));
				bar.setProgress(1);
				return true;
			}

			float health = 0;
			for (UUID id : admirals) {
				Entity entity = level.getEntity(id);
				if (entity instanceof LivingEntity living && living.isAlive()) {
					health += living.getHealth();
				}
			}
			bar.setName(Component.literal("BUSTER CALL: defeat the Admirals"));
			bar.setProgress(Mth.clamp(health / admiralHealth, 0, 1));
			if (health <= 0) {
				win(pirate);
				return false;
			}
			return true;
		}

		int shellEvery() {
			return Math.max(8, 30 - 6 * title.ordinal());
		}

		void updateBar() {
			for (ServerPlayer player : List.copyOf(bar.getPlayers())) {
				if (player.level() != level || player.distanceToSqr(Vec3.atCenterOf(center)) > ESCAPE_DISTANCE * ESCAPE_DISTANCE) {
					bar.removePlayer(player);
				}
			}
			for (ServerPlayer player : level.players()) {
				if (player.distanceToSqr(Vec3.atCenterOf(center)) < ESCAPE_DISTANCE * ESCAPE_DISTANCE) {
					bar.addPlayer(player);
				}
			}
		}

		/** One cannonball from a random ship (or from beyond the horizon) at the pirate, with spread. */
		void fire(ServerPlayer pirate) {
			Vec3 from = null;
			if (!ships.isEmpty()) {
				Entity ship = level.getEntity(ships.get(pirate.getRandom().nextInt(ships.size())));
				if (ship != null && ship.isAlive() && ship.getPassengers().isEmpty()) {
					from = ship.position().add(0, 3.5, 0);
				}
			}
			if (from == null) {
				double angle = pirate.getRandom().nextDouble() * Math.PI * 2;
				from = Vec3.atCenterOf(center).add(Math.cos(angle) * 60, 25, Math.sin(angle) * 60);
			}
			Vec3 to = pirate.position().add(pirate.getRandom().nextGaussian() * 5, 0, pirate.getRandom().nextGaussian() * 5);
			level.sendParticles(ParticleTypes.EXPLOSION, from.x, from.y, from.z, 1, 0, 0, 0, 0);
			level.playSound(null, BlockPos.containing(from), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 6.0f, 0.5f);
			shells.add(new Shell(from, to, Math.max(20, (int) (from.distanceTo(to) * 0.8))));
		}

		/** Shells fly in an arc and explode where they land. Like raids, they don't break blocks. */
		void tickShells() {
			Iterator<Shell> it = shells.iterator();
			while (it.hasNext()) {
				Shell shell = it.next();
				shell.age++;
				Vec3 pos = shell.positionAt(shell.age);
				level.sendParticles(ParticleTypes.LARGE_SMOKE, pos.x, pos.y, pos.z, 2, 0.05, 0.05, 0.05, 0);
				if (shell.age >= shell.flightTicks) {
					level.explode(null, shell.to.x, shell.to.y, shell.to.z, 3.0f, Level.ExplosionInteraction.NONE);
					it.remove();
				}
			}
		}

		void landAdmirals(ServerPlayer pirate) {
			List<String> ids = new ArrayList<>(List.of("akainu", "kizaru", "fujitora", "ryokugyu"));
			java.util.Collections.shuffle(ids, new java.util.Random(pirate.getRandom().nextLong()));
			List<String> landing = new ArrayList<>(ids.subList(0, title == Title.EMPEROR ? 1 : 2));
			if (title == Title.KING_OF_THE_WORLD) {
				landing.add("garp");
				landing.add("sengoku");
			}
			admiralHealth = 0;
			List<String> names = new ArrayList<>();
			for (String id : landing) {
				BlockPos spot = landingSpot(pirate);
				CharacterEntity boss = spot == null ? null : CharacterFeature.CHARACTER.create(level, EntitySpawnReason.EVENT);
				if (boss == null) {
					continue;
				}
				boss.setPos(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
				boss.setCharacter(id, true);
				boss.addTag(MarineHunters.HUNTER_TAG);
				boss.addTag(TAG);
				boss.setTarget(pirate);
				level.addFreshEntity(boss);
				admirals.add(boss.getUUID());
				admiralHealth += boss.getMaxHealth();
				names.add(boss.getData().name);
			}
			if (admirals.isEmpty()) {
				admiralHealth = 1;
				return;
			}
			pirate.sendSystemMessage(Component.literal(String.join(", ", names) + " landed!").withStyle(ChatFormatting.RED));
		}

		BlockPos landingSpot(ServerPlayer pirate) {
			for (int attempt = 0; attempt < 16; attempt++) {
				double angle = pirate.getRandom().nextDouble() * Math.PI * 2;
				int distance = 10 + pirate.getRandom().nextInt(15);
				int x = Mth.floor(pirate.getX() + Math.cos(angle) * distance);
				int z = Mth.floor(pirate.getZ() + Math.sin(angle) * distance);
				if (!level.hasChunkAt(new BlockPos(x, 0, z))) {
					continue;
				}
				BlockPos pos = new BlockPos(x, level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z), z);
				if (level.getBlockState(pos.below()).isSolid() && Math.abs(pos.getY() - pirate.getBlockY()) < 20) {
					return pos;
				}
			}
			return null;
		}

		void win(ServerPlayer pirate) {
			EmpireRanks.broadcast(level.getServer(), Component.literal(pirate.getName().getString()
					+ " survived a Buster Call and defeated the Admirals!").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
			Bounty.raise(pirate, 250_000_000L * title.ordinal(), "The world is shaken.", true);
			level.playSound(null, pirate.blockPosition(), SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.PLAYERS, 1.0f, 1.0f);
		}

		void cleanUp() {
			bar.removeAllPlayers();
			for (UUID id : admirals) {
				Entity entity = level.getEntity(id);
				if (entity != null && entity.isAlive()) {
					entity.discard();
				}
			}
			for (UUID id : ships) {
				Entity ship = level.getEntity(id);
				if (ship != null && ship.getPassengers().isEmpty()) {
					ship.discard(); // The fleet sails away, unless a pirate stole a ship.
				}
			}
		}
	}

	private static class Shell {
		final Vec3 from;
		final Vec3 to;
		final int flightTicks;
		int age = 0;

		Shell(Vec3 from, Vec3 to, int flightTicks) {
			this.from = from;
			this.to = to;
			this.flightTicks = flightTicks;
		}

		Vec3 positionAt(int tick) {
			double t = Math.min(1.0, tick / (double) flightTicks);
			double arc = from.distanceTo(to) * 0.25 * 4 * t * (1 - t);
			return from.lerp(to, t).add(0, arc, 0);
		}
	}
}
