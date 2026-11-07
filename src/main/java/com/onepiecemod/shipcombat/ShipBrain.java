package com.onepiecemod.shipcombat;

import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.WeakHashMap;

import org.jetbrains.annotations.Nullable;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.bounty.MarineWarship;
import com.onepiecemod.ship.ShipEntity;

/**
 * The "captain" of a Marine or pirate ship. Each tick it picks a heading and fires the cannons.
 *  - Marines go after ships with a wanted pirate aboard (bounty above 0), pirate ships, and anyone who fires on them.
 *  - Pirates go after every player ship and every Marine ship.
 *  - Far away: sail closer. In cannon range: turn side-on and fire broadsides. Too close: open up some room.
 *  - Land ahead: turn away from it.
 * The ship's side is saved as an entity tag, so these ships keep fighting after a server restart.
 */
public class ShipBrain {
	public enum Faction { MARINE, PIRATE }

	public static final String TAG_MARINE = "onepiece_ai_marine";
	public static final String TAG_PIRATE = "onepiece_ai_pirate";
	private static final String TAG_TIER = "onepiece_ai_tier_";

	// ---- How they fight. Change these to make enemy ships easier or harder. ----
	private static final double SIGHT = 112;          // blocks: how far they spot enemies
	private static final double CANNON_RANGE = 56;    // blocks: furthest they shoot from
	private static final double BEST_RANGE = 30;      // blocks: they try to stay about this far
	private static final double TOO_CLOSE = 14;
	private static final double LEASH = 120;         // blocks: further than this from every player, head back toward one
	private static final int MARINE_RELOAD = 100;     // ticks between broadsides (5 seconds)
	private static final int PIRATE_RELOAD = 120;

	private static final Map<ShipEntity, ShipBrain> BRAINS = new WeakHashMap<>();

	private final ShipEntity ship;
	public final Faction faction;
	public final int tier;
	private final Set<UUID> grudges = new HashSet<>(); // Ships that fired on us.

	private UUID targetId;
	private Vec3 targetLastPos;
	private Vec3 targetVelocity = Vec3.ZERO;
	private int retarget;
	private int reload = 60;
	private int awayTicks;
	private float wanderYaw = Float.NaN;
	private int wanderTimer;
	private int avoidTicks;
	private float avoidYaw;

	private ShipBrain(ShipEntity ship, Faction faction, int tier) {
		this.ship = ship;
		this.faction = faction;
		this.tier = tier;
	}

	// ---- Who's who ----

	public static boolean isAi(ShipEntity ship) {
		return ship.entityTags().contains(TAG_MARINE) || ship.entityTags().contains(TAG_PIRATE);
	}

	/** MARINE or PIRATE for an enemy ship (raid warships count as Marines), null for a player's ship. */
	@Nullable
	public static Faction factionOf(ShipEntity ship) {
		Set<String> tags = ship.entityTags();
		if (tags.contains(TAG_MARINE) || tags.contains(MarineWarship.TAG)) {
			return Faction.MARINE;
		}
		return tags.contains(TAG_PIRATE) ? Faction.PIRATE : null;
	}

	public static int tierOf(ShipEntity ship) {
		for (String tag : ship.entityTags()) {
			if (tag.startsWith(TAG_TIER)) {
				try {
					return Integer.parseInt(tag.substring(TAG_TIER.length()));
				} catch (NumberFormatException ignored) {
					return 0;
				}
			}
		}
		return 0;
	}

	/** Marks a freshly made ship as a Marine or pirate ship. Call before adding it to the world. */
	public static void mark(ShipEntity ship, Faction faction, int tier) {
		ship.addTag(faction == Faction.MARINE ? TAG_MARINE : TAG_PIRATE);
		ship.addTag(TAG_TIER + tier);
	}

	/** True if both are enemy ships of the same side (so they don't shoot each other). */
	public static boolean sameSide(ShipEntity a, ShipEntity b) {
		Faction fa = isAi(a) ? factionOf(a) : null;
		Faction fb = isAi(b) ? factionOf(b) : null;
		return fa != null && fa == fb;
	}

	@Nullable
	public static ShipBrain of(ShipEntity ship) {
		if (!isAi(ship)) {
			return null;
		}
		return BRAINS.computeIfAbsent(ship, s -> new ShipBrain(s, factionOf(s), tierOf(s)));
	}

	/** True if this ship is hunting that one. */
	public boolean isTargeting(ShipEntity other) {
		return other.getUUID().equals(targetId);
	}

	/** Someone fired on this ship: it fights back. */
	void hitBy(@Nullable ShipEntity attackerShip, @Nullable Player attacker) {
		Entity vehicle = attacker != null ? attacker.getVehicle() : null;
		ShipEntity from = attackerShip != null ? attackerShip : vehicle instanceof ShipEntity s ? s : null;
		if (from != null && from != ship) {
			grudges.add(from.getUUID());
			if (targetId == null) {
				targetId = from.getUUID();
			}
		}
	}

	// ---- Every tick ----

	void tick(ServerLevel level) {
		if (ship.sinking) {
			return;
		}
		if (--retarget <= 0) {
			retarget = 20;
			pickTarget(level);
		}

		float yaw = ship.getYRot();
		float desired;
		ShipEntity target = currentTarget(level);
		if (target != null) {
			Vec3 now = target.position();
			if (targetLastPos != null) {
				targetVelocity = targetVelocity.scale(0.8).add(now.subtract(targetLastPos).scale(0.2));
			}
			targetLastPos = now;

			double dx = now.x - ship.getX();
			double dz = now.z - ship.getZ();
			double distance = Math.sqrt(dx * dx + dz * dz);
			float bearing = yawTowards(dx, dz);
			if (distance > BEST_RANGE + 8) {
				desired = bearing; // Close in.
			} else {
				// Circle the enemy side-on. Every enemy ship circles the same way round (clockwise seen from above),
				// so two of them orbit each other instead of sailing off over the horizon side by side.
				float angle = distance < TOO_CLOSE ? 125 : distance < BEST_RANGE - 6 ? 100 : 75;
				desired = bearing + angle;
			}
			fireIfReady(level, target, distance);
		} else {
			targetLastPos = null;
			targetVelocity = Vec3.ZERO;
			if (Float.isNaN(wanderYaw) || --wanderTimer <= 0) {
				wanderYaw = yaw + (level.getRandom().nextFloat() - 0.5f) * 80f;
				wanderTimer = 200 + level.getRandom().nextInt(200);
			}
			desired = wanderYaw;
			if (reload > 0) {
				reload--;
			}
		}

		// Stay where the players are: drift back toward the nearest one if the ship strays too far.
		Player nearest = nearestPlayer(level, Double.MAX_VALUE);
		if (nearest != null) {
			double px = nearest.getX() - ship.getX();
			double pz = nearest.getZ() - ship.getZ();
			double playerDistance = Math.sqrt(px * px + pz * pz);
			if (playerDistance > LEASH || target == null && playerDistance > 70) {
				desired = yawTowards(px, pz);
			}
		}

		// Never run aground: if land is ahead, keep turning until the way is clear.
		if (avoidTicks > 0) {
			avoidTicks--;
			desired = avoidYaw;
		} else if (!openWater(level, yaw, 12) || !openWater(level, yaw, 20)) {
			avoidTicks = 50;
			avoidYaw = openWater(level, yaw + 90, 16) ? yaw + 90 : yaw - 90;
			wanderYaw = avoidYaw;
			desired = avoidYaw;
		}

		float turnNeeded = Mth.wrapDegrees(desired - yaw);
		ship.aiTurn = Mth.clamp(-turnNeeded / 15f, -1f, 1f); // Negative turns right (ShipEntity subtracts turn from yaw).
		ship.aiForward = 1;
	}

	private void pickTarget(ServerLevel level) {
		ShipEntity current = currentTarget(level);
		ShipEntity best = null;
		double bestDistance = SIGHT * SIGHT;
		for (ShipEntity other : ShipCombat.loadedShips()) {
			if (other == ship || other.isRemoved() || other.sinking || other.level() != level) {
				continue;
			}
			double distance = other.distanceToSqr(ship);
			if (distance < bestDistance && isEnemy(other)) {
				bestDistance = distance;
				best = other;
			}
		}
		// Stick with the current target unless it's gone or something is much closer.
		if (current != null && (best == null || current.distanceToSqr(ship) < bestDistance * 2.0)) {
			return;
		}
		targetId = best == null ? null : best.getUUID();
		targetLastPos = null;
	}

	private boolean isEnemy(ShipEntity other) {
		if (grudges.contains(other.getUUID())) {
			return true;
		}
		if (isAi(other)) {
			return factionOf(other) != faction;
		}
		for (Player player : ShipEntity.playersAboard(other)) {
			if (!player.isCreative() && !player.isSpectator()) {
				// Pirates attack anyone. Marines only attack wanted pirates.
				if (faction == Faction.PIRATE || Bounty.get(player) > 0) {
					return true;
				}
			}
		}
		return false;
	}

	/** True if this ship is out to fight that one: hunting it, or holding a grudge because it fired on us. */
	public boolean isFoe(ShipEntity other) {
		return isTargeting(other) || grudges.contains(other.getUUID());
	}

	/** The ship this one is hunting right now, or null. */
	@Nullable
	ShipEntity target(ServerLevel level) {
		return currentTarget(level);
	}

	@Nullable
	private ShipEntity currentTarget(ServerLevel level) {
		if (targetId == null) {
			return null;
		}
		if (level.getEntity(targetId) instanceof ShipEntity target && !target.isRemoved() && !target.sinking
				&& target.distanceToSqr(ship) < SIGHT * SIGHT * 1.5) {
			return target;
		}
		targetId = null;
		return null;
	}

	// ---- Cannons ----

	private void fireIfReady(ServerLevel level, ShipEntity target, double distance) {
		if (reload > 0) {
			reload--;
			return;
		}
		if (distance > CANNON_RANGE) {
			return;
		}
		Vec3 toTarget = target.position().subtract(ship.position());
		List<Cannons.Gun> guns = Cannons.gunsFacing(ship, toTarget);
		if (guns.isEmpty()) {
			reload = 10; // Not side-on yet. Check again soon.
			return;
		}

		// Aim at the deck, a little ahead of where the target is going. Better crews (higher tier) aim better.
		double spread = Math.max(0.6, 2.6 - tier * 0.35);
		double flightTicks = distance / (Cannons.MUZZLE_SPEED * 0.85);
		Vec3 deck = target.position().add(0, target.getLayout().waterline + 1.0, 0).add(targetVelocity.scale(flightTicks));
		// Seasoned crews mix in special shot: Marines tangle your rigging with chain shot, pirates set you ablaze.
		ShipAmmo ammo = tier >= 2 && level.getRandom().nextFloat() < 0.25f
				? (faction == Faction.MARINE ? ShipAmmo.CHAIN_SHOT : ShipAmmo.FIRE_SHOT) : ShipAmmo.CANNONBALL;
		for (Cannons.Gun gun : guns) {
			Vec3 aimPoint = deck.add(level.getRandom().nextGaussian() * spread, level.getRandom().nextGaussian() * 0.5,
					level.getRandom().nextGaussian() * spread);
			Cannons.fire(level, gun.muzzle(), Cannons.aim(gun.muzzle(), aimPoint), ship, ship,
					ShipHull.CANNONBALL_DAMAGE * (1 + tier * 0.1f) * gun.profile(level).damage(), ammo);
		}
		int base = faction == Faction.MARINE ? MARINE_RELOAD : PIRATE_RELOAD;
		reload = Math.max(50, base - tier * 8) + level.getRandom().nextInt(30);
	}

	/**
	 * Called every 5 seconds. True once no player has been within `range` blocks for 30 seconds in a row
	 * (and somebody is online: an empty server keeps its ships).
	 */
	boolean awayFromPlayers(ServerLevel level, double range) {
		Player nearest = nearestPlayer(level, range);
		if (nearest != null || level.players().isEmpty()) {
			awayTicks = 0;
			return false;
		}
		awayTicks += 100;
		return awayTicks >= 600;
	}

	/**
	 * The closest player within range, creative players included (vanilla's getNearestPlayer skips them,
	 * which made ships vanish next to a creative-mode player). Spectators don't count.
	 */
	@Nullable
	private Player nearestPlayer(ServerLevel level, double range) {
		Player best = null;
		double bestDistance = range == Double.MAX_VALUE ? Double.MAX_VALUE : range * range;
		for (Player player : level.players()) {
			double distance = player.distanceToSqr(ship);
			if (!player.isSpectator() && player.isAlive() && distance < bestDistance) {
				bestDistance = distance;
				best = player;
			}
		}
		return best;
	}

	// ---- Steering helpers ----

	/** The heading (yaw) that points along dx, dz. Ships move along (-sin yaw, cos yaw). */
	static float yawTowards(double dx, double dz) {
		return (float) Math.toDegrees(Math.atan2(-dx, dz));
	}

	/** True if there is open sea a certain distance ahead along a heading. */
	private boolean openWater(ServerLevel level, float yaw, double ahead) {
		float radians = yaw * Mth.DEG_TO_RAD;
		double x = ship.getX() - Mth.sin(radians) * ahead;
		double z = ship.getZ() + Mth.cos(radians) * ahead;
		BlockPos surface = BlockPos.containing(x, ship.getY() + ship.getLayout().waterline - 0.5, z);
		if (!level.hasChunkAt(surface)) {
			return false;
		}
		return level.getFluidState(surface).is(FluidTags.WATER) && level.getFluidState(surface.below()).is(FluidTags.WATER)
				&& level.getBlockState(surface.above()).canBeReplaced();
	}
}
