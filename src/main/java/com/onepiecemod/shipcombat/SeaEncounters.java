package com.onepiecemod.shipcombat;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import org.jetbrains.annotations.Nullable;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.ship.ShipFeature;
import com.onepiecemod.ship.ShipLayout;
import com.onepiecemod.sound.ModSounds;

/**
 * Enemy ships at sea. Every 20 seconds, each player out sailing has a small chance to meet one:
 *  - A Marine warship if they are wanted (bounty above 0). Bigger bounties bring Battleships.
 *  - A Marine patrol otherwise. Patrols leave you alone but attack pirate ships.
 *  - Pirate ships, which attack everyone. Galleons sail the Grand Line.
 *  - Sometimes a Marine and a pirate ship already in a fight.
 * Ships appear 80 to 110 blocks away on open sea and leave when nobody is within 200 blocks.
 */
public class SeaEncounters {
	// ---- How often. Change these to meet more or fewer ships. ----
	private static final int CHECK_EVERY = 20 * 20;            // ticks between rolls (20 seconds)
	private static final float CHANCE = 0.12f;                  // chance per roll
	private static final int COOLDOWN = 20 * 60 * 3;            // after a meeting, 3 minutes of calm for that player
	private static final double NEARBY = 200;                    // at most MAX_NEARBY enemy ships this close to a player
	private static final int MAX_NEARBY = 2;
	/** The Grand Line is the sea within this many blocks of z = 0 (same rule as sea.CalmBelt). */
	private static final int GRAND_LINE = 1000;

	private static final Map<UUID, Long> NEXT_MEETING = new HashMap<>();

	static void tick(MinecraftServer server) {
		if (server.getTickCount() % CHECK_EVERY != 0) {
			return;
		}
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			if (!(ShipEntity.aboard(player) instanceof ShipEntity ship) || ShipBrain.isAi(ship) || ship.sinking
					|| com.onepiecemod.deepsea.ShipDive.isDown(ship) // Ships on the surface can't find you under the sea.
					|| player.isCreative() || player.isSpectator() || player.level().dimension() != Level.OVERWORLD) {
				continue;
			}
			ServerLevel level = (ServerLevel) player.level();
			if (level.getDifficulty() == Difficulty.PEACEFUL) {
				continue;
			}
			long now = level.getGameTime();
			if (now < NEXT_MEETING.getOrDefault(player.getUUID(), 0L) || enemiesNear(level, player) >= MAX_NEARBY) {
				continue;
			}
			if (player.getRandom().nextFloat() >= CHANCE) {
				continue;
			}
			if (meet(level, player, ship)) {
				NEXT_MEETING.put(player.getUUID(), now + COOLDOWN);
			}
		}
	}

	private static int enemiesNear(ServerLevel level, ServerPlayer player) {
		int count = 0;
		for (ShipEntity other : ShipCombat.loadedShips()) {
			if (other.level() == level && ShipBrain.isAi(other) && other.distanceToSqr(player) < NEARBY * NEARBY) {
				count++;
			}
		}
		return count;
	}

	/** Picks what kind of ship turns up and sends it in. Returns false if there was no open sea for it. */
	public static boolean meet(ServerLevel level, ServerPlayer player, ShipEntity playerShip) {
		RandomSource random = level.getRandom();
		boolean grandLine = Math.abs(player.getZ()) <= GRAND_LINE;
		int threat = Bounty.threatLevel(player);
		boolean wanted = Bounty.get(player) > 0;

		// Now and then it's a whole fleet (see NavalBattles).
		if (NavalBattles.maybeMeet(level, player, playerShip, grandLine)) {
			return true;
		}

		if (random.nextFloat() < 0.15f) {
			// A sea battle already under way: a Marine ship and a pirate ship, 30 blocks apart.
			int tier = grandLine ? 1 + random.nextInt(2) : random.nextInt(2);
			ShipEntity marine = spawn(level, player, playerShip, ShipBrain.Faction.MARINE, tier, null);
			if (marine == null) {
				return false;
			}
			spawn(level, player, playerShip, ShipBrain.Faction.PIRATE, tier, marine.position());
			tell(player, "Cannon fire on the horizon! Marines and pirates are fighting out there.", ChatFormatting.GOLD);
			return true;
		}

		boolean marines = wanted ? random.nextFloat() < 0.55f : random.nextFloat() < 0.25f;
		if (marines) {
			int tier = Math.max(threat, grandLine ? 1 : 0);
			if (spawn(level, player, playerShip, ShipBrain.Faction.MARINE, tier, null) == null) {
				return false;
			}
			if (wanted) {
				ModSounds.play(player, ModSounds.NAVY_BUGLE);
				tell(player, "A Marine warship has spotted you! Man the cannons!", ChatFormatting.RED);
			} else {
				tell(player, "A Marine patrol ship is on the horizon. They're hunting pirates, not you... for now.", ChatFormatting.AQUA);
			}
		} else {
			int tier = Mth.clamp((grandLine ? 2 : 0) + random.nextInt(2) + threat / 2, 0, 5);
			ShipEntity pirates = spawn(level, player, playerShip, ShipBrain.Faction.PIRATE, tier, null);
			if (pirates == null) {
				return false;
			}
			tell(player, "Pirates! The " + pirates.getName().getString() + " is coming about to attack!", ChatFormatting.RED);
		}
		return true;
	}

	/** Puts an enemy ship on open sea 80-110 blocks from the player, mostly ahead of their ship, heading their way. */
	@Nullable
	public static ShipEntity spawn(ServerLevel level, ServerPlayer player, ShipEntity playerShip, ShipBrain.Faction faction, int tier, @Nullable Vec3 near) {
		return spawnAt(level, player.position(), playerShip.getYRot(), 80, faction, tier, near);
	}

	/**
	 * Puts an enemy ship on open sea about `distance` blocks from a spot (within 80 degrees of `heading`),
	 * or about 30 blocks from `near` if given. The ship turns toward the spot. Null if there's no open sea.
	 */
	@Nullable
	public static ShipEntity spawnAt(ServerLevel level, Vec3 center, float heading, double distance, ShipBrain.Faction faction, int tier, @Nullable Vec3 near) {
		RandomSource random = level.getRandom();
		float hullBonus = 1 + tier * 0.25f;
		// The ships look like the show's: Marine warships with the gull on the bow, Buggy's Big Top, the Red Force...
		ShipDesigns.Pick pick = faction == ShipBrain.Faction.MARINE ? ShipDesigns.marine(level, tier >= 3) : ShipDesigns.pirate(level, tier, random);
		ShipLayout layout = pick.layout();
		String name = pick.name();
		int reach = Math.max(9, Math.max(layout.max.getX() - layout.min.getX(), layout.max.getZ() - layout.min.getZ()) / 2 + 1);

		for (int attempt = 0; attempt < 32; attempt++) {
			double x;
			double z;
			if (near != null) {
				double angle = random.nextDouble() * Math.PI * 2;
				x = near.x + Math.cos(angle) * 30;
				z = near.z + Math.sin(angle) * 30;
			} else {
				float yaw = heading + (random.nextFloat() - 0.5f) * 160f;
				double far = distance + random.nextInt(31);
				x = center.x - Mth.sin(yaw * Mth.DEG_TO_RAD) * far;
				z = center.z + Mth.cos(yaw * Mth.DEG_TO_RAD) * far;
			}
			int bx = Mth.floor(x);
			int bz = Mth.floor(z);
			Integer surface = deepWaterSurface(level, bx, bz);
			if (surface == null || deepWaterSurface(level, bx + reach, bz) == null || deepWaterSurface(level, bx - reach, bz) == null
					|| deepWaterSurface(level, bx, bz + reach) == null || deepWaterSurface(level, bx, bz - reach) == null) {
				continue;
			}

			ShipEntity ship = ShipFeature.SHIP.create(level, EntitySpawnReason.EVENT);
			if (ship == null) {
				return null;
			}
			ship.setLayout(layout);
			float toward = ShipBrain.yawTowards(center.x - x, center.z - z);
			ship.snapTo(bx + 0.5, surface - layout.waterline, bz + 0.5, toward, 0);
			ship.setCustomName(Component.literal(name));
			ShipBrain.mark(ship, faction, tier);
			ShipHull.setMax(ship, ShipHull.sizeToHull(layout.size()) * hullBonus);
			level.addFreshEntity(ship);
			return ship;
		}
		return null;
	}

	private static void tell(ServerPlayer player, String text, ChatFormatting color) {
		player.sendSystemMessage(Component.literal(text).withStyle(color));
	}

	/** The Y just above the sea's surface if this column is open sea at least 5 blocks deep, otherwise null. */
	@Nullable
	private static Integer deepWaterSurface(ServerLevel level, int x, int z) {
		if (!level.hasChunkAt(new BlockPos(x, 0, z))) {
			return null;
		}
		int top = level.getHeight(Heightmap.Types.WORLD_SURFACE, x, z);
		int floor = level.getHeight(Heightmap.Types.OCEAN_FLOOR, x, z);
		BlockPos water = new BlockPos(x, top - 1, z);
		if (!level.getFluidState(water).is(FluidTags.WATER) || top - floor < 5) {
			return null;
		}
		return top;
	}
}
