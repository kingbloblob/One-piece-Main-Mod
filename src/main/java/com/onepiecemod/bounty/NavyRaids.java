package com.onepiecemod.bounty;

import com.onepiecemod.sound.ModSounds;
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
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.character.CharacterData;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.ship.ShipEntity;

/**
 * Navy raids: the Marines attack the place where a wanted pirate is standing, in waves, like a village raid.
 *
 * Differences from a Marine hunt (MarineHunters): a raid stays at one spot, comes in several waves with a
 * raid bar, can bring a warship that fires cannonballs from the sea, and ends with a commander.
 * Beat every wave and your bounty jumps. Run more than 80 blocks away for 30 seconds and the raid ends.
 *
 * Every minute each wanted player (Overworld, survival or adventure, not Peaceful) rolls a chance.
 * After a raid there is a 10 minute break before the next one.
 */
public class NavyRaids {
	private static final int CHECK_EVERY_TICKS = 20 * 60;
	private static final int BREAK_TICKS = 20 * 60 * 10;
	private static final int WARNING_TICKS = 20 * 10;
	private static final int BETWEEN_WAVES_TICKS = 20 * 8;
	private static final double RAID_RADIUS = 64.0;
	private static final double ESCAPE_DISTANCE = 80.0;
	private static final int ESCAPE_TICKS = 20 * 30;
	/** A wave not beaten in this time pulls back, so one Marine stuck somewhere can't hold up the raid forever. */
	private static final int WAVE_TICKS = 20 * 180;

	// Everything below is by threat level 0..5 (see Bounty.threatLevel).
	/** Chance per minute that a raid starts. Level 1 is about once an hour, level 5 every few minutes. */
	private static final float[] CHANCE = {0f, 0.02f, 0.04f, 0.06f, 0.09f, 0.12f};
	private static final int[] WAVES = {0, 2, 3, 4, 5, 6};
	/** Ticks between warship cannon shots. 0 = no warship at that level. */
	private static final int[] CANNON_EVERY = {0, 0, 200, 140, 100, 60};
	/** Who leads the last wave (ids from characters.json). Empty = a Marine Captain leads it. */
	private static final String[][] COMMANDERS = {
			{}, {}, {},
			{"smoker"},
			{"lucci", "smoker"},
			{"kizaru", "akainu", "fujitora", "ryokugyu"}
	};
	/** Bounty for beating a whole raid, per wave. */
	private static final long BOUNTY_PER_WAVE = 1_000_000L; // Kept small so raids don't outrun the story's bounty curve.

	private static final Map<UUID, Raid> raids = new HashMap<>();
	private static final Map<UUID, Integer> nextRaidTick = new HashMap<>();

	public static boolean isRaiding(ServerPlayer player) {
		return raids.containsKey(player.getUUID());
	}

	/** What a raid looks like at this threat level, for /bounty. */
	public static String describe(int threat) {
		if (threat == 0) {
			return "No Navy raids.";
		}
		String text = "Navy raids: " + WAVES[threat] + " waves";
		if (CANNON_EVERY[threat] > 0) {
			text += ", a warship shelling you from the sea";
		}
		if (COMMANDERS[threat].length > 0) {
			text += ", led by " + String.join(" or ", commanderNames(threat));
		}
		return text + ".";
	}

	private static List<String> commanderNames(int threat) {
		List<String> names = new ArrayList<>();
		for (String id : COMMANDERS[threat]) {
			names.add(CharacterData.get(id).name);
		}
		return names;
	}

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			// Run every raid each tick.
			Iterator<Raid> it = raids.values().iterator();
			while (it.hasNext()) {
				Raid raid = it.next();
				if (!raid.tick(server)) {
					raid.cleanUp();
					ServerPlayer pirate = server.getPlayerList().getPlayer(raid.pirateId);
					// Emperors and up get shorter breaks between raids.
					nextRaidTick.put(raid.pirateId, server.getTickCount()
							+ (pirate != null ? com.onepiecemod.empire.EmpireRanks.navyBreak(pirate, BREAK_TICKS) : BREAK_TICKS));
					it.remove();
				}
			}

			if (server.getTickCount() % CHECK_EVERY_TICKS != 0) {
				return;
			}
			int now = server.getTickCount();
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				int threat = Bounty.threatLevel(player);
				if (threat == 0 || !NavyCalm.canStart(player) || !MarineHunters.canBeHunted(player)
						|| now < nextRaidTick.getOrDefault(player.getUUID(), 0) || insideRaid(player)) {
					continue;
				}
				if (player.getRandom().nextFloat() < CHANCE[threat] * com.onepiecemod.empire.EmpireRanks.navyChance(player) * com.onepiecemod.config.ModConfig.navyRaidRate()) {
					start(player);
				}
			}
		});

		// A warship left over from a raid that is no longer running (for example after a restart) sails away.
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity instanceof ShipEntity ship && ship.entityTags().contains(MarineWarship.TAG)
					&& ship.getPassengers().isEmpty() && !isActiveWarship(ship.getUUID())) {
				ship.discard();
			}
		});
	}

	/** True if the player is already in the middle of someone's raid (say a crewmate's): one fleet at a time. */
	private static boolean insideRaid(ServerPlayer player) {
		for (Raid raid : raids.values()) {
			if (raid.level == player.level() && player.distanceToSqr(Vec3.atCenterOf(raid.center)) < RAID_RADIUS * RAID_RADIUS) {
				return true;
			}
		}
		return false;
	}

	private static boolean isActiveWarship(UUID id) {
		for (Raid raid : raids.values()) {
			if (id.equals(raid.shipId)) {
				return true;
			}
		}
		return false;
	}

	/** Starts a raid on the player's position. Returns an error message, or null if it started. */
	public static String start(ServerPlayer player) {
		if (isRaiding(player)) {
			return "A raid is already coming for you.";
		}
		int threat = Bounty.threatLevel(player);
		if (threat == 0) {
			return "You need a bounty first.";
		}
		Raid raid = new Raid(player, threat);
		raids.put(player.getUUID(), raid);
		raid.announce(player);
		return null;
	}

	/** Ends the player's raid right away (for /bounty raid stop). */
	public static boolean stop(ServerPlayer player) {
		Raid raid = raids.remove(player.getUUID());
		if (raid == null) {
			return false;
		}
		raid.cleanUp();
		return true;
	}

	// ------------------------------------------------------------------------------------------

	/** One running raid. Lives only in memory: if the server stops, the raid is simply over. */
	private static class Raid {
		final UUID pirateId;
		final ServerLevel level;
		final BlockPos center;
		final int threat;
		final int totalWaves;
		final ServerBossEvent bar;

		int wave = 0; // 0 while the fleet is still coming.
		int countdown = WARNING_TICKS;
		int awayTicks = 0;
		int waveTicks = 0;
		int cannonTimer;
		float waveHealth = 1;
		final List<UUID> members = new ArrayList<>();
		UUID shipId;
		boolean noLanding = false;
		final List<Shell> shells = new ArrayList<>();

		Raid(ServerPlayer pirate, int threat) {
			this.pirateId = pirate.getUUID();
			this.level = (ServerLevel) pirate.level();
			this.center = pirate.blockPosition();
			this.threat = threat;
			this.totalWaves = WAVES[threat];
			this.cannonTimer = CANNON_EVERY[threat];
			this.bar = new ServerBossEvent(UUID.randomUUID(), Component.literal("Navy Raid"), BossEvent.BossBarColor.BLUE, BossEvent.BossBarOverlay.NOTCHED_10);
			this.bar.setProgress(0);
		}

		void announce(ServerPlayer pirate) {
			Component warning = Component.literal("The Navy has found " + pirate.getName().getString() + " (bounty "
					+ Bounty.format(Bounty.get(pirate)) + ")! A raid of " + totalWaves + " waves lands in 10 seconds!")
					.withStyle(ChatFormatting.DARK_AQUA);
			for (ServerPlayer player : level.players()) {
				if (player.distanceToSqr(Vec3.atCenterOf(center)) < RAID_RADIUS * RAID_RADIUS) {
					player.sendSystemMessage(warning);
				}
			}
			level.playSound(null, center, ModSounds.NAVY_BUGLE, SoundSource.HOSTILE, 4.0f, 1.0f);
			bar.setName(Component.literal("Navy Raid: the fleet is coming"));

			if (CANNON_EVERY[threat] > 0) {
				ShipEntity ship = MarineWarship.spawn(level, center, pirate.getRandom());
				if (ship != null) {
					shipId = ship.getUUID();
					pirate.sendSystemMessage(Component.literal("A Marine warship is anchored offshore. Watch out for cannonballs!")
							.withStyle(ChatFormatting.RED));
				}
			}
		}

		/** Returns false when the raid is over. */
		boolean tick(MinecraftServer server) {
			ServerPlayer pirate = server.getPlayerList().getPlayer(pirateId);
			if (pirate == null || pirate.level() != level) {
				return false; // Logged out or left the Overworld: the Navy goes home.
			}
			updateBarPlayers();

			// Running away ends the raid, but you get nothing for it.
			if (pirate.distanceToSqr(Vec3.atCenterOf(center)) > ESCAPE_DISTANCE * ESCAPE_DISTANCE) {
				awayTicks++;
				if (awayTicks >= ESCAPE_TICKS) {
					pirate.sendSystemMessage(Component.literal("You escaped the Navy raid. They'll be back.").withStyle(ChatFormatting.GRAY));
					return false;
				}
			} else {
				awayTicks = 0;
			}
			if (!pirate.isAlive()) {
				return true; // Wait for them to respawn; the raid carries on.
			}

			tickShells();
			tickCannon(pirate);

			if (countdown > 0) {
				countdown--;
				if (countdown == 0) {
					wave++;
					spawnWave(pirate);
					if (noLanding) {
						pirate.sendSystemMessage(Component.literal("The Marines couldn't find dry ground to land on. The raid is off, for now.")
								.withStyle(ChatFormatting.GRAY));
						return false;
					}
				}
				return true;
			}

			// A wave is running: the bar shows how much of the wave is left.
			float health = 0;
			for (UUID id : members) {
				Entity entity = level.getEntity(id);
				if (entity instanceof LivingEntity living && living.isAlive()) {
					health += living.getHealth();
				}
			}
			bar.setProgress(Mth.clamp(health / waveHealth, 0, 1));

			if (health > 0 && ++waveTicks >= WAVE_TICKS) {
				// Out of time: whoever is left of this wave goes back to the ships.
				retreatWave();
				if (wave >= totalWaves) {
					pirate.sendSystemMessage(Component.literal("The last Marines fall back to their ships. The raid is over, but they got away.")
							.withStyle(ChatFormatting.GOLD));
					win(pirate, false);
					return false;
				}
				pirate.sendSystemMessage(Component.literal("The rest of this wave falls back to regroup.").withStyle(ChatFormatting.GRAY));
				health = 0;
			}

			if (health <= 0) {
				if (wave >= totalWaves) {
					win(pirate, true);
					return false;
				}
				bar.setName(Component.literal("Navy Raid: wave " + (wave + 1) + " of " + totalWaves + " is coming"));
				bar.setProgress(0);
				countdown = BETWEEN_WAVES_TICKS;
			}
			return true;
		}

		void updateBarPlayers() {
			for (ServerPlayer player : List.copyOf(bar.getPlayers())) {
				if (player.level() != level || player.distanceToSqr(Vec3.atCenterOf(center)) > RAID_RADIUS * RAID_RADIUS) {
					bar.removePlayer(player);
				}
			}
			for (ServerPlayer player : level.players()) {
				if (player.distanceToSqr(Vec3.atCenterOf(center)) < RAID_RADIUS * RAID_RADIUS) {
					bar.addPlayer(player);
				}
			}
		}

		/** Which Marines come in a wave. Bigger and tougher with higher bounty and later waves. */
		List<MarineRank> squad(ServerPlayer pirate) {
			List<MarineRank> squad = new ArrayList<>();
			int size = Math.min(10, 2 + threat + wave);
			boolean lastWave = wave == totalWaves;
			// The leader.
			if (threat >= 4 || (lastWave && threat >= 2)) {
				squad.add(MarineRank.CAPTAIN);
			} else if (threat >= 3 || wave >= 2) {
				squad.add(MarineRank.LIEUTENANT);
			}
			while (squad.size() < size) {
				float roll = pirate.getRandom().nextFloat();
				if (threat >= 4 && roll < 0.15f) {
					squad.add(MarineRank.LIEUTENANT);
				} else if (threat >= 2 && roll < 0.45f) {
					squad.add(MarineRank.RIFLEMAN);
				} else {
					squad.add(MarineRank.RECRUIT);
				}
			}
			return squad;
		}

		void spawnWave(ServerPlayer pirate) {
			members.clear();
			waveHealth = 0;
			waveTicks = 0;
			for (MarineRank rank : squad(pirate)) {
				MarineEntity marine = BountyFeature.MARINE.create(level, EntitySpawnReason.EVENT);
				BlockPos spot = landingSpot(pirate);
				if (marine == null || spot == null) {
					continue;
				}
				marine.setPos(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
				marine.setRank(rank);
				marine.setHunted(pirate);
				level.addFreshEntity(marine);
				members.add(marine.getUUID());
				waveHealth += marine.getMaxHealth();
			}

			// The last wave is led by a famous Marine at high bounties.
			String commander = null;
			String[] choices = COMMANDERS[threat];
			if (wave == totalWaves && choices.length > 0) {
				BlockPos spot = landingSpot(pirate);
				CharacterEntity boss = spot == null ? null : CharacterFeature.CHARACTER.create(level, EntitySpawnReason.EVENT);
				if (boss != null) {
					String id = choices[pirate.getRandom().nextInt(choices.length)];
					boss.setPos(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
					boss.setCharacter(id, true);
					boss.addTag(MarineHunters.HUNTER_TAG);
					EventBosses.mark(boss);
					boss.setTarget(pirate);
					level.addFreshEntity(boss);
					members.add(boss.getUUID());
					waveHealth += boss.getMaxHealth();
					commander = boss.getData().name;
				}
			}

			if (members.isEmpty()) {
				waveHealth = 1;
				noLanding = true; // Nowhere to land (at sea, or no dry ground nearby).
				return;
			}
			String name = wave == totalWaves ? "Navy Raid: final wave" : "Navy Raid: wave " + wave + " of " + totalWaves;
			bar.setName(Component.literal(commander != null ? name + " (" + commander + ")" : name));
			bar.setProgress(1);
			level.playSound(null, center, SoundEvents.RAID_HORN.value(), SoundSource.HOSTILE, 4.0f, 1.1f);
			if (commander != null) {
				pirate.sendSystemMessage(Component.literal(commander + " is leading the final wave!").withStyle(ChatFormatting.RED));
			}
		}

		/** Dry ground 12 to 28 blocks from the raid's centre. */
		BlockPos landingSpot(ServerPlayer pirate) {
			for (int attempt = 0; attempt < 12; attempt++) {
				double angle = pirate.getRandom().nextDouble() * Math.PI * 2;
				int distance = 12 + pirate.getRandom().nextInt(17);
				int x = Mth.floor(center.getX() + Math.cos(angle) * distance);
				int z = Mth.floor(center.getZ() + Math.sin(angle) * distance);
				if (!level.hasChunkAt(new BlockPos(x, 0, z))) {
					continue;
				}
				BlockPos pos = new BlockPos(x, level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z), z);
				if (level.getFluidState(pos.below()).isEmpty() && level.getBlockState(pos.below()).isSolid()
						&& Math.abs(pos.getY() - center.getY()) < 20) {
					return pos;
				}
			}
			return null;
		}

		// ---- The warship's cannons ----

		void tickCannon(ServerPlayer pirate) {
			if (shipId == null || wave == 0) {
				return;
			}
			Entity ship = level.getEntity(shipId);
			if (ship == null || !ship.isAlive() || !ship.getPassengers().isEmpty()) {
				return; // Sunk, gone, or a pirate has taken the helm.
			}
			if (--cannonTimer > 0) {
				return;
			}
			cannonTimer = CANNON_EVERY[threat];

			// Aim at a random pirate near the raid, with a few blocks of spread.
			List<ServerPlayer> targets = new ArrayList<>();
			for (ServerPlayer player : level.players()) {
				if (Bounty.get(player) > 0 && !player.isCreative() && !player.isSpectator() && player.isAlive()
						&& player.distanceToSqr(Vec3.atCenterOf(center)) < RAID_RADIUS * RAID_RADIUS) {
					targets.add(player);
				}
			}
			if (targets.isEmpty()) {
				return;
			}
			ServerPlayer target = targets.get(pirate.getRandom().nextInt(targets.size()));
			Vec3 from = ship.position().add(0, 3.5, 0);
			Vec3 to = target.position().add(pirate.getRandom().nextGaussian() * 3, 0, pirate.getRandom().nextGaussian() * 3);

			level.sendParticles(ParticleTypes.EXPLOSION, from.x, from.y, from.z, 1, 0, 0, 0, 0);
			level.sendParticles(ParticleTypes.LARGE_SMOKE, from.x, from.y, from.z, 12, 0.5, 0.5, 0.5, 0.05);
			level.playSound(null, BlockPos.containing(from), ModSounds.CANNON, SoundSource.HOSTILE, 6.0f, 1.0f);
			shells.add(new Shell(from, to, Math.max(20, (int) (from.distanceTo(to) * 0.8))));
		}

		/** Cannonballs fly in an arc (drawn with smoke) and explode where they land. They don't break blocks. */
		void tickShells() {
			Iterator<Shell> it = shells.iterator();
			while (it.hasNext()) {
				Shell shell = it.next();
				shell.age++;
				Vec3 pos = shell.positionAt(shell.age);
				level.sendParticles(ParticleTypes.LARGE_SMOKE, pos.x, pos.y, pos.z, 2, 0.05, 0.05, 0.05, 0);
				if (shell.age >= shell.flightTicks) {
					level.explode(null, shell.to.x, shell.to.y, shell.to.z, 2.5f, Level.ExplosionInteraction.NONE);
					it.remove();
				}
			}
		}

		// ---- The end ----

		/** Every wave beaten (full reward), or the last one ran out of time and pulled back (half). */
		void win(ServerPlayer pirate, boolean full) {
			long reward = BOUNTY_PER_WAVE * totalWaves * threat / (full ? 1 : 2);
			if (full) {
				pirate.sendSystemMessage(Component.literal("You fought off the Navy raid!").withStyle(ChatFormatting.GOLD));
			}
			int berryCount = Math.max(1, 2 * totalWaves * threat / (full ? 1 : 2));
			ItemStack berries = new ItemStack(CharacterFeature.BERRY, berryCount);
			if (!pirate.getInventory().add(berries)) {
				pirate.spawnAtLocation(level, berries);
			}
			Bounty.raise(pirate, reward, "The whole Navy is talking about it.", true);
			level.playSound(null, center, SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.PLAYERS, 1.0f, 1.0f);

			// Crewmates and allies who stood and fought get their share: the Berries, and half the bounty.
			for (ServerPlayer friend : level.players()) {
				if (friend == pirate || !friend.isAlive() || friend.isSpectator()
						|| friend.distanceToSqr(Vec3.atCenterOf(center)) > RAID_RADIUS * RAID_RADIUS
						|| !com.onepiecemod.multiplayer.PlayerCrews.friendly(level.getServer(), pirate, friend)) {
					continue;
				}
				ItemStack share = new ItemStack(CharacterFeature.BERRY, berryCount);
				if (!friend.getInventory().add(share)) {
					friend.spawnAtLocation(level, share);
				}
				Bounty.raise(friend, reward / 2, "You helped " + pirate.getName().getString() + " fight off the Navy.", false);
			}
		}

		/** The Marines (and commander) still alive in this wave leave in a puff of smoke. */
		void retreatWave() {
			for (UUID id : members) {
				Entity entity = level.getEntity(id);
				if (entity != null && entity.isAlive()) {
					level.sendParticles(ParticleTypes.CLOUD, entity.getX(), entity.getY() + 1, entity.getZ(), 15, 0.4, 0.6, 0.4, 0.02);
					entity.discard();
				}
			}
			members.clear();
		}

		/** Removes the bar, any Marines still around, and the warship (unless a pirate has stolen it). */
		void cleanUp() {
			bar.removeAllPlayers();
			for (UUID id : members) {
				Entity entity = level.getEntity(id);
				if (entity != null && entity.isAlive()) {
					entity.discard();
				}
			}
			if (shipId != null) {
				Entity ship = level.getEntity(shipId);
				if (ship instanceof ShipEntity warship && ShipEntity.playersAboard(warship).isEmpty()) {
					ship.discard(); // The warship sails away (unless pirates are aboard: then it's theirs now).
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
