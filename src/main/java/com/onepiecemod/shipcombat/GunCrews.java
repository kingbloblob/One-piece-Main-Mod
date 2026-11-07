package com.onepiecemod.shipcombat;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;

import org.jetbrains.annotations.Nullable;

import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.crew.CrewmateEntity;
import com.onepiecemod.ship.ShipDecks;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.ship.ShipUpgrades;

/**
 * Your crew mans the cannons. Every crewmate standing on your ship's deck (following you or told to wait there)
 * works one gun: every RELOAD ticks, when an enemy ship that is out to fight you is in range, they fire the cannons
 * on the side facing her, aimed by the crew, using cannonballs from the captain's inventory.
 * More crewmates aboard = more guns firing (up to MAX_GUNS). A Sniper among them aims tighter.
 * Your own broadside (the cannon key) still works on top of this.
 */
public class GunCrews {
	private static final int RELOAD = 20 * 6;
	private static final double RANGE = 56;
	private static final int MAX_GUNS = 4;
	/** The crew aims a little worse than the captain does with the cannon key. */
	private static final float CREW_DAMAGE = 0.8f;
	private static final int TALK_EVERY = 20 * 60;

	private static final Map<ShipEntity, Long> NEXT_VOLLEY = new WeakHashMap<>();
	private static final Map<ShipEntity, Long> NEXT_TALK = new WeakHashMap<>();

	/** Once a second (from ShipCombat). */
	static void tick(MinecraftServer server) {
		for (ShipEntity ship : ShipCombat.loadedShips()) {
			if (ship.isRemoved() || ship.sinking || ShipBrain.isAi(ship) || !(ship.level() instanceof ServerLevel level)) {
				continue;
			}
			long now = level.getGameTime();
			if (now < NEXT_VOLLEY.getOrDefault(ship, 0L)) {
				continue;
			}
			List<CrewmateEntity> gunners = gunners(ship);
			if (gunners.isEmpty()) {
				continue;
			}
			ServerPlayer captain = gunners.get(0).getCaptain();
			if (captain == null || ShipEntity.aboard(captain) != ship) {
				continue; // The ammo is in the captain's pockets.
			}
			ShipEntity enemy = nearestFoe(level, ship);
			if (enemy == null) {
				continue;
			}
			if (volley(level, ship, enemy, gunners, captain)) {
				NEXT_VOLLEY.put(ship, now + Math.round(RELOAD * ShipUpgrades.reloadTime(ShipUpgrades.guns(ship.getLayout()))));
				if (now >= NEXT_TALK.getOrDefault(ship, 0L)) {
					NEXT_TALK.put(ship, now + TALK_EVERY);
					gunners.get(0).tellCaptain("Gun crew firing on the " + enemy.getName().getString() + "!");
				}
			}
		}
	}

	/** Crewmates on this ship's deck who can work a gun. */
	private static List<CrewmateEntity> gunners(ShipEntity ship) {
		List<CrewmateEntity> gunners = new ArrayList<>();
		for (Entity entity : ShipDecks.onDeck(ship)) {
			if (entity instanceof CrewmateEntity mate && mate.isAlive() && !mate.isKnockedOut() && mate.getCaptainId() != null) {
				gunners.add(mate);
			}
		}
		return gunners;
	}

	/** The closest enemy ship within range that is hunting this ship or that this ship has fired on. */
	@Nullable
	private static ShipEntity nearestFoe(ServerLevel level, ShipEntity ship) {
		ShipEntity best = null;
		double bestDistance = RANGE * RANGE;
		for (ShipEntity other : ShipCombat.loadedShips()) {
			ShipBrain brain = ShipBrain.of(other);
			boolean rival = com.onepiecemod.multiplayer.SeaWars.isRivalShip(ship, other); // a player crew we're in a sea battle with
			if (other == ship || other.level() != level || other.sinking || other.isRemoved() || !(rival || brain != null && brain.isFoe(ship))) {
				continue;
			}
			double distance = other.distanceToSqr(ship);
			if (distance < bestDistance) {
				bestDistance = distance;
				best = other;
			}
		}
		return best;
	}

	private static boolean volley(ServerLevel level, ShipEntity ship, ShipEntity enemy, List<CrewmateEntity> gunners, ServerPlayer captain) {
		Vec3 toEnemy = enemy.position().subtract(ship.position());
		List<Cannons.Gun> guns = Cannons.gunsFacing(ship, toEnemy);
		if (guns.isEmpty()) {
			return false; // Nothing points her way yet: the helmsman has to bring the ship side-on.
		}
		int ammo = captain.isCreative() ? Integer.MAX_VALUE : Cannons.countAmmo(captain.getInventory(), ShipCombatFeature.CANNONBALL);
		int shots = Math.min(Math.min(guns.size(), gunners.size()), Math.min(MAX_GUNS, ammo));
		if (shots <= 0) {
			return false;
		}
		if (!captain.isCreative()) {
			takeCannonballs(captain, shots);
		}
		boolean sniper = gunners.stream().anyMatch(mate -> mate.getRole() == CrewRole.SNIPER);
		double wobble = sniper ? 0.4 : 1.0;
		float damage = ShipHull.CANNONBALL_DAMAGE * ShipUpgrades.gunDamage(ShipUpgrades.guns(ship.getLayout())) * CREW_DAMAGE;
		// Aim at her deck, a little ahead of where she's sailing.
		Vec3 aimAt = enemy.position().add(0, enemy.getLayout().waterline + 1, 0);
		for (int i = 0; i < shots; i++) {
			Cannons.Gun gun = guns.get(i);
			CannonAddons.Profile profile = gun.profile(level);
			double flightTicks = gun.muzzle().distanceTo(aimAt) / (Cannons.MUZZLE_SPEED * profile.speed());
			Vec3 target = aimAt.add(enemy.getDeltaMovement().multiply(flightTicks, 0, flightTicks));
			double spread = wobble * profile.spread();
			Vec3 velocity = Cannons.aim(gun.muzzle(), target).scale(profile.speed()).add(level.getRandom().nextGaussian() * 0.05 * spread,
					level.getRandom().nextGaussian() * 0.03 * spread, level.getRandom().nextGaussian() * 0.05 * spread);
			Cannons.fire(level, gun.muzzle(), velocity, captain, ship, damage * profile.damage());
		}
		return true;
	}

	private static void takeCannonballs(ServerPlayer captain, int amount) {
		var inventory = captain.getInventory();
		for (int slot = 0; slot < inventory.getContainerSize() && amount > 0; slot++) {
			var stack = inventory.getItem(slot);
			if (stack.is(ShipCombatFeature.CANNONBALL)) {
				int take = Math.min(amount, stack.getCount());
				stack.shrink(take);
				amount -= take;
			}
		}
	}
}
