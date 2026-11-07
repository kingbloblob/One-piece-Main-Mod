package com.onepiecemod.worldevent;

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
import net.minecraft.util.RandomSource;
import net.minecraft.world.BossEvent;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.bounty.MarineHunters;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.npc.HumanNpc;
import com.onepiecemod.npc.NpcFeature;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.shipcombat.SeaEncounters;
import com.onepiecemod.shipcombat.ShipBrain;
import com.onepiecemod.sound.ModSounds;

/**
 * A Buster Call on an ISLAND (like Ohara and Enies Lobby), for pirates who made too much trouble there.
 * (Emperors get a different Buster Call aimed at them wherever they are: empire.BusterCall.)
 *
 *  1. Warning (60 s): the call goes out by Den Den Mushi. Get off the island, or get ready.
 *  2. Bombardment (150 s): a fleet of battleships offshore shells the whole island. Shells blow real craters,
 *     but every block is written down and rebuilt 10 minutes after the Buster Call (see Ruins).
 *     40 seconds in, Vice Admirals and elite Marines land. Wanted at 1,000,000,000+? An Admiral comes too.
 *  3. Over: the island lies in ruins, and its Trouble meter is back to 0.
 *
 * Sink or capture every ship of the fleet before the shelling ends and you BREAK the Buster Call:
 * a huge bounty and a headline in every paper. If nobody stays within 200 blocks, the fleet leaves early.
 */
public class IslandBusterCall {
	public static final String TAG = "onepiece_island_buster_call";
	private static final int WARNING_TICKS = 20 * 60;
	private static final int SHELLING_TICKS = 20 * 150;
	private static final int LANDING_AT = 20 * 40;
	private static final double SHELL_RADIUS = 64;
	private static final double STAY_RANGE = 200;

	private static final Map<String, Call> CALLS = new HashMap<>();

	public static boolean isRunning(String islandKey) {
		return CALLS.containsKey(islandKey);
	}

	public static boolean anyRunning() {
		return !CALLS.isEmpty();
	}

	static void initialize() {
		// Ships and Marines from a Buster Call that's no longer running (for example after a restart) have gone home.
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity.entityTags().contains(TAG) && !isMember(entity.getUUID())
					&& (!(entity instanceof ShipEntity ship) || ship.getPassengers().isEmpty())) {
				entity.discard();
			}
		});
	}

	private static boolean isMember(UUID id) {
		for (Call call : CALLS.values()) {
			if (call.members.contains(id)) {
				return true;
			}
		}
		return false;
	}

	static void start(ServerLevel level, IslandTrouble.Spot spot, ServerPlayer culprit) {
		if (CALLS.containsKey(spot.key) || spot.center == null) {
			return;
		}
		Call call = new Call(level, spot, culprit);
		CALLS.put(spot.key, call);
		call.announce();
	}

	/** Starts a Buster Call on the island where the player stands (for /worldevent bustercall). */
	static String startHere(ServerPlayer player) {
		ServerLevel level = (ServerLevel) player.level();
		IslandTrouble.Spot spot = IslandTrouble.islandAt(level, player.blockPosition(), true);
		if (spot == null) {
			return "Stand on an island in the Overworld first.";
		}
		if (CALLS.containsKey(spot.key)) {
			return "A Buster Call is already under way here.";
		}
		start(level, spot, player);
		return null;
	}

	static int stopAll() {
		int count = CALLS.size();
		for (Call call : CALLS.values()) {
			call.end(false);
		}
		CALLS.clear();
		return count;
	}

	static void tick(MinecraftServer server) {
		Iterator<Call> it = CALLS.values().iterator();
		while (it.hasNext()) {
			Call call = it.next();
			if (!call.tick()) {
				it.remove();
			}
		}
	}

	// ------------------------------------------------------------------------------------------

	private static class Call {
		final ServerLevel level;
		final IslandTrouble.Spot spot;
		final BlockPos center;
		final Component name;
		final UUID culpritId;
		final String culpritName;
		final int threat;
		final ServerBossEvent bar;
		final Ruins.Live ruins;
		final List<UUID> fleet = new ArrayList<>();
		final List<UUID> members = new ArrayList<>();
		final List<Shell> shells = new ArrayList<>();
		int age = 0;
		int lonelyTicks = 0;
		boolean fired = false;

		Call(ServerLevel level, IslandTrouble.Spot spot, ServerPlayer culprit) {
			this.level = level;
			this.spot = spot;
			this.center = spot.center;
			this.name = IslandTrouble.islandName(spot.key);
			this.culpritId = culprit.getUUID();
			this.culpritName = culprit.getName().getString();
			this.threat = Bounty.threatLevel(culprit);
			this.bar = new ServerBossEvent(UUID.randomUUID(), Component.literal("BUSTER CALL"), BossEvent.BossBarColor.RED,
					BossEvent.BossBarOverlay.NOTCHED_10);
			this.ruins = Ruins.open(spot.key);
		}

		void announce() {
			WorldNews.report(level.getServer(), "BUSTER CALL! The World Government has ordered the destruction of "
					+ name.getString() + " to stop the pirate " + culpritName + "!", ChatFormatting.DARK_RED);
			for (ServerPlayer player : IslandTrouble.playersOn(level, spot)) {
				WorldNews.call(player, "Marine HQ", "Buster Call authorised. Ten battleships and five Vice Admirals... "
						+ "Everyone on " + name.getString() + " has 60 seconds.", ChatFormatting.RED);
				ModSounds.play(player, ModSounds.NAVY_BUGLE);
			}
			level.playSound(null, center, SoundEvents.RAID_HORN.value(), SoundSource.HOSTILE, 8.0f, 0.5f);

			// The fleet takes up position offshore, all round the island.
			int ships = 4 + (threat >= 4 ? 1 : 0);
			int tier = Math.min(5, 3 + threat / 3);
			RandomSource random = level.getRandom();
			Vec3 middle = Vec3.atCenterOf(center);
			for (int i = 0; i < ships; i++) {
				float heading = i * 360f / ships + random.nextFloat() * 40f;
				ShipEntity ship = SeaEncounters.spawnAt(level, middle, heading, 70, ShipBrain.Faction.MARINE, tier, null);
				if (ship == null) {
					continue; // No open sea that way: the shells come from beyond the horizon.
				}
				ship.setCustomName(Component.literal("Buster Call Battleship"));
				ship.addTag(TAG);
				fleet.add(ship.getUUID());
				members.add(ship.getUUID());
			}
		}

		/** False when it's over. */
		boolean tick() {
			age++;
			updateBar();
			tickShells();

			if (nearbyPlayers().isEmpty()) {
				if ((lonelyTicks += 1) > 20 * 30) {
					end(false);
					return false;
				}
			} else {
				lonelyTicks = 0;
			}

			if (age < WARNING_TICKS) {
				bar.setName(Component.literal("BUSTER CALL on ").append(name).append(Component.literal(": evacuate!")));
				bar.setProgress(1 - age / (float) WARNING_TICKS);
				return true;
			}
			int shelling = age - WARNING_TICKS;
			if (shelling == 0) {
				for (ServerPlayer player : nearbyPlayers()) {
					player.sendSystemMessage(Component.literal("The bombardment begins!").withStyle(ChatFormatting.DARK_RED, ChatFormatting.BOLD));
				}
			}
			if (shelling == LANDING_AT) {
				landTroops();
			}
			if (shelling < SHELLING_TICKS) {
				int every = Math.max(4, 12 - threat);
				if (shelling % every == 0) {
					fire();
					if (threat >= 3 && level.getRandom().nextBoolean()) {
						fire();
					}
				}
				bar.setName(Component.literal("BUSTER CALL on ").append(name).append(Component.literal(": " + fleetLeft() + " ships")));
				bar.setProgress(1 - shelling / (float) SHELLING_TICKS);
				if (!fleet.isEmpty() && fleetLeft() == 0) {
					broken();
					end(true);
					return false;
				}
				return true;
			}
			if (!shells.isEmpty()) {
				return true; // Let the last shells land.
			}
			end(false);
			return false;
		}

		int fleetLeft() {
			int count = 0;
			for (UUID id : fleet) {
				if (level.getEntity(id) instanceof ShipEntity ship && ship.isAlive() && !ship.sinking && ship.getPassengers().isEmpty()) {
					count++; // A ship with a player aboard has been captured.
				}
			}
			return count;
		}

		List<ServerPlayer> nearbyPlayers() {
			List<ServerPlayer> list = new ArrayList<>();
			for (ServerPlayer player : level.players()) {
				if (!player.isSpectator() && horizontalDistanceSqr(player) < STAY_RANGE * STAY_RANGE) {
					list.add(player);
				}
			}
			return list;
		}

		double horizontalDistanceSqr(Entity entity) {
			double dx = entity.getX() - center.getX();
			double dz = entity.getZ() - center.getZ();
			return dx * dx + dz * dz;
		}

		void updateBar() {
			for (ServerPlayer player : List.copyOf(bar.getPlayers())) {
				if (player.level() != level || horizontalDistanceSqr(player) > STAY_RANGE * STAY_RANGE) {
					bar.removePlayer(player);
				}
			}
			for (ServerPlayer player : nearbyPlayers()) {
				bar.addPlayer(player);
			}
		}

		/** One shell from a ship of the fleet (or from beyond the horizon) at a spot on the island. */
		void fire() {
			RandomSource random = level.getRandom();
			Vec3 from = null;
			if (!fleet.isEmpty()) {
				Entity ship = level.getEntity(fleet.get(random.nextInt(fleet.size())));
				if (ship instanceof ShipEntity s && s.isAlive() && !s.sinking && s.getPassengers().isEmpty()) {
					from = s.position().add(0, 4, 0);
				}
			}
			if (from == null) {
				double angle = random.nextDouble() * Math.PI * 2;
				from = Vec3.atCenterOf(center).add(Math.cos(angle) * 90, 30, Math.sin(angle) * 90);
				from = new Vec3(from.x, Math.max(from.y, level.getSeaLevel() + 30), from.z);
			}
			// A third of the shells go for a player on the island, the rest anywhere on it.
			double tx;
			double tz;
			List<ServerPlayer> players = nearbyPlayers();
			if (!players.isEmpty() && random.nextInt(3) == 0) {
				Player target = players.get(random.nextInt(players.size()));
				tx = target.getX() + random.nextGaussian() * 6;
				tz = target.getZ() + random.nextGaussian() * 6;
			} else {
				double angle = random.nextDouble() * Math.PI * 2;
				double distance = Math.sqrt(random.nextDouble()) * SHELL_RADIUS;
				tx = center.getX() + Math.cos(angle) * distance;
				tz = center.getZ() + Math.sin(angle) * distance;
			}
			BlockPos column = BlockPos.containing(tx, 0, tz);
			if (!level.hasChunkAt(column)) {
				return;
			}
			int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, column.getX(), column.getZ());
			Vec3 to = new Vec3(tx, y, tz);
			level.sendParticles(ParticleTypes.EXPLOSION, from.x, from.y, from.z, 1, 0, 0, 0, 0);
			level.playSound(null, BlockPos.containing(from), ModSounds.CANNON, SoundSource.HOSTILE, 5.0f, 0.7f + random.nextFloat() * 0.2f);
			shells.add(new Shell(from, to, Mth.clamp((int) (from.distanceTo(to) * 0.7), 20, 80)));
			fired = true;
		}

		void tickShells() {
			Iterator<Shell> it = shells.iterator();
			while (it.hasNext()) {
				Shell shell = it.next();
				shell.age++;
				Vec3 pos = shell.positionAt(shell.age);
				level.sendParticles(ParticleTypes.LARGE_SMOKE, pos.x, pos.y, pos.z, 2, 0.05, 0.05, 0.05, 0);
				if (shell.age >= shell.flightTicks) {
					BlockPos hit = BlockPos.containing(shell.to);
					int radius = 2 + level.getRandom().nextInt(2) + (threat >= 4 ? 1 : 0);
					Ruins.crater(level, ruins, hit, radius, level.getRandom());
					level.explode(null, shell.to.x, shell.to.y + 0.5, shell.to.z, 3.0f, Level.ExplosionInteraction.NONE);
					level.sendParticles(ParticleTypes.FLAME, shell.to.x, shell.to.y + 1, shell.to.z, 20, radius * 0.6, 0.6, radius * 0.6, 0.02);
					it.remove();
				}
			}
		}

		/** Vice Admirals and elite Marines come ashore near the players. A wanted Emperor-class pirate gets an Admiral too. */
		void landTroops() {
			List<ServerPlayer> players = nearbyPlayers();
			if (players.isEmpty()) {
				return;
			}
			RandomSource random = level.getRandom();
			ServerPlayer target = players.get(random.nextInt(players.size()));
			BlockPos spot = WorldEvents.landingSpot(level, target.blockPosition(), 12, 24, random);
			if (spot == null) {
				return;
			}
			int viceAdmirals = Math.min(3, 1 + threat / 2);
			for (int i = 0; i < viceAdmirals + 3; i++) {
				String kit = i < viceAdmirals ? "vice_admiral" : "elite_marine";
				HumanNpc npc = NpcFeature.spawn(level, kit, spot.offset(random.nextInt(7) - 3, 0, random.nextInt(7) - 3), 0);
				if (npc != null) {
					npc.addTag(TAG);
					npc.setPersistenceRequired();
					npc.setTarget(target);
					members.add(npc.getUUID());
				}
			}
			String admiral = null;
			if (threat >= 5) {
				String[] admirals = {"akainu", "kizaru", "fujitora", "ryokugyu"};
				admiral = admirals[random.nextInt(admirals.length)];
				CharacterEntity boss = CharacterFeature.CHARACTER.create(level, EntitySpawnReason.EVENT);
				if (boss != null) {
					boss.setPos(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
					boss.setCharacter(admiral, true);
					boss.addTag(MarineHunters.HUNTER_TAG);
					boss.addTag(TAG);
					boss.setTarget(target);
					level.addFreshEntity(boss);
					members.add(boss.getUUID());
					admiral = boss.getData().name;
				}
			}
			for (ServerPlayer player : players) {
				player.sendSystemMessage(Component.literal(viceAdmirals + (viceAdmirals == 1 ? " Vice Admiral has" : " Vice Admirals have")
						+ " landed" + (admiral != null ? ", with Admiral " + admiral : "") + "!").withStyle(ChatFormatting.RED));
			}
		}

		void broken() {
			WorldNews.report(level.getServer(), "The Buster Call on " + name.getString() + " has FAILED! The pirates sank the whole fleet!",
					ChatFormatting.GOLD);
			long reward = 30_000_000L * (threat + 1);
			for (ServerPlayer player : nearbyPlayers()) {
				if (Bounty.get(player) > 0 || player.getUUID().equals(culpritId)) {
					Bounty.raise(player, reward, "You broke a Buster Call!", true);
				}
				level.playSound(null, player.blockPosition(), SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.PLAYERS, 1.0f, 1.0f);
			}
		}

		void end(boolean broken) {
			bar.removeAllPlayers();
			if (!broken && fired) {
				for (ServerPlayer player : nearbyPlayers()) {
					player.sendSystemMessage(Component.literal("The Buster Call is over. ").withStyle(ChatFormatting.GRAY)
							.append(name.copy().withStyle(ChatFormatting.GRAY))
							.append(Component.literal(" lies in ruins... but its people will rebuild.").withStyle(ChatFormatting.GRAY)));
				}
				WorldNews.remember(level.getServer(), "Buster Call reduces " + name.getString() + " to rubble while hunting " + culpritName + ".");
			}
			Ruins.close(ruins, level.getGameTime());
			IslandTrouble.clearTrouble(spot);
			for (UUID id : members) {
				Entity entity = level.getEntity(id);
				if (entity == null || !entity.isAlive()) {
					continue;
				}
				if (entity instanceof ShipEntity ship) {
					if (ship.getPassengers().isEmpty() && !ship.sinking) {
						ship.discard(); // The fleet sails home, unless a pirate stole a ship.
					}
				} else {
					entity.discard(); // The landing party goes back aboard.
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
