package com.onepiecemod.ship.client;

import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.projectile.ProjectileUtil;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.ship.ShipEntity;

/**
 * Finds what the crosshair is really on near ships, where the game's own pick gets it wrong.
 *
 * The game looks for entities near the player's position, by the entity's own position. A ship's position is its
 * centre at the keel, so from the deck of a tall ship (or from a rowboat next to a long ship's bow) the game never
 * even considers the ship, and right-clicking to drop anchor, open a chest or climb aboard does nothing. The old
 * sloop was small enough to get away with it; the Going Merry and the Thousand Sunny are not.
 *
 * The other way round, a ship's box is a big square over the whole ship. Walking on her deck your eyes are inside it,
 * and the game then picks the ship whatever you look at: you couldn't hit a Marine on deck or click the sea.
 * So for people walking a deck, the ship only counts where you look at one of her real blocks.
 */
public final class ShipPick {
	/** How far from the player's line of sight to look for ships (by their centre). Ships are up to ~60 blocks long. */
	private static final double SEARCH = 48;

	private ShipPick() {
	}

	/** What the crosshair is really on this frame, or null to keep what the game found. */
	public static HitResult pick(Entity camera, LocalPlayer player, float partialTick, HitResult current) {
		Vec3 eye = camera.getEyePosition(partialTick);

		// At the wheel: anywhere you look, the deck under you is the ship. This is also what the game would do for a
		// small ship: a ray that starts inside an entity's box hits it at distance 0.
		if (camera.getVehicle() instanceof ShipEntity ship && !ship.isRemoved() && ship.getBoundingBox().contains(eye)) {
			if (current instanceof EntityHitResult entityHit && entityHit.getEntity() == ship) {
				return null;
			}
			return new EntityHitResult(ship, eye);
		}

		double reach = player.entityInteractionRange();
		Vec3 look = camera.getViewVector(partialTick);
		Vec3 end = eye.add(look.scale(reach));

		// The game picked a ship just because our eyes are inside its big box: start again, without ships' boxes.
		boolean redo = current instanceof EntityHitResult entityHit && entityHit.getEntity() instanceof ShipEntity;
		if (redo) {
			current = camera.pick(Math.max(reach, player.blockInteractionRange()), partialTick, false);
			double limit = current.getType() == HitResult.Type.MISS ? reach : Math.min(reach, Math.sqrt(current.getLocation().distanceToSqr(eye)));
			EntityHitResult other = ProjectileUtil.getEntityHitResult(camera, eye, eye.add(look.scale(limit)),
					camera.getBoundingBox().expandTowards(look.scale(limit)).inflate(1),
					entity -> !(entity instanceof ShipEntity) && !entity.isSpectator() && entity.isPickable(), limit * limit);
			if (other != null) {
				current = other;
			}
		}

		// Near (or on) a ship: follow the line of sight through the ship's real blocks (its box is a big square that also
		// covers open water beside the hull, so the box alone would steal clicks meant for the dock or the sea).
		double best = current == null || current.getType() == HitResult.Type.MISS ? reach : Math.sqrt(current.getLocation().distanceToSqr(eye));
		HitResult found = redo ? current : null;
		AABB search = new AABB(eye, end).inflate(SEARCH, 16, SEARCH);
		for (ShipEntity ship : camera.level().getEntitiesOfClass(ShipEntity.class, search, s -> s.isPickable() && s != camera.getVehicle())) {
			double distance = ship.blockHitDistance(eye, look, Math.min(best, reach), partialTick);
			if (distance >= 0 && distance < best) {
				best = distance;
				found = new EntityHitResult(ship, eye.add(look.scale(distance)));
			}
		}
		return found;
	}
}
