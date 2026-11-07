package com.onepiecemod.deepsea;

import java.util.Map;
import java.util.WeakHashMap;
import java.util.function.ToIntFunction;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.ship.ShipLayout;
import com.onepiecemod.ship.ShipUpgrades;

/**
 * Diving: submarines (any ship with a Ballast Tank and a sealed hull, like the Polar Tang) and ships wrapped in
 * Sabaody's bubble coating can leave the surface and sail under the sea.
 *
 * The captain holds Jump to rise and Sprint to dive. Let go and she holds her depth, even with nobody at the wheel.
 * A submarine can only go as deep as its hull is rated for (more tanks and Hull upgrades go deeper); a coated ship
 * goes all the way to the sea floor, but its coating wears thin the longer it stays down (see ShipCoating).
 *
 * The sea "surface" for diving is the world's sea level, so depth means blocks under the open sea.
 * ShipEntity calls verticalSpeed each tick on whichever game steers the ship, and tick on both sides.
 */
public final class ShipDive {
	private ShipDive() {
	}

	/** How fast a ship sinks or rises when the captain asks, in blocks per tick. */
	public static final double DIVE_SPEED = 0.07;
	public static final double RISE_SPEED = 0.09;
	/** Deeper than this (blocks under the surface) the ship counts as down: no anchoring, the coating wears. */
	public static final double DOWN = 1.5;

	/** A submarine with one tank and no Hull upgrade can reach this depth. */
	private static final int BASE_DEPTH = 40;
	private static final int PER_EXTRA_TANK = 15;
	private static final int MAX_TANKS = 4;
	private static final int PER_HULL_LEVEL = 10;
	/** A coated ship can go as deep as the sea goes. */
	private static final int COATED_DEPTH = 400;

	/**
	 * The captain's dive input on the game that steers the ship: +1 rise, -1 dive, 0 hold. Set by the client
	 * (DeepSeaClient: Jump and Sprint while at the wheel); the server never steers a captained ship.
	 */
	public static ToIntFunction<Player> diveInput = player -> 0;

	private static final Map<ShipLayout, Integer> TANKS = new WeakHashMap<>();

	/** How many Ballast Tanks this ship carries. */
	public static int tanks(ShipLayout layout) {
		synchronized (TANKS) {
			return TANKS.computeIfAbsent(layout, l -> {
				int n = 0;
				for (ShipLayout.ShipBlock block : l.blocks) {
					if (block.state().is(DeepSeaFeature.BALLAST_TANK)) {
						n++;
					}
				}
				return n;
			});
		}
	}

	public static boolean isSubmarine(ShipEntity ship) {
		return tanks(ship.getLayout()) > 0;
	}

	public static boolean isCoated(ShipEntity ship) {
		return ship.coating() > 0;
	}

	/** True if this ship can leave the surface at all. */
	public static boolean canDive(ShipEntity ship) {
		return !ship.sinking && (isSubmarine(ship) || isCoated(ship));
	}

	/** How deep (blocks under the surface) this ship may go. */
	public static int maxDepth(ShipEntity ship) {
		int depth = 0;
		int tanks = tanks(ship.getLayout());
		if (tanks > 0) {
			depth = BASE_DEPTH + PER_EXTRA_TANK * (Math.min(tanks, MAX_TANKS) - 1) + PER_HULL_LEVEL * ShipUpgrades.hull(ship.getLayout());
		}
		if (isCoated(ship)) {
			depth = Math.max(depth, COATED_DEPTH);
		}
		return depth;
	}

	/** The sea's surface height, for diving. */
	public static double surface(ShipEntity ship) {
		return ship.level().getSeaLevel() - 0.11;
	}

	/** How many blocks under her floating height the ship is now (0 or less = afloat). */
	public static double depth(ShipEntity ship) {
		return surface(ship) - ship.getLayout().waterline - ship.getY();
	}

	/** True while the ship is down under the sea, not just bobbing. */
	public static boolean isDown(ShipEntity ship) {
		return depth(ship) > DOWN;
	}

	/** True when even the top of the ship is under the sea's surface. Then only a sealed hull stays dry. */
	public static boolean fullySubmerged(ShipEntity ship) {
		return ship.getY() + ship.getLayout().max.getY() + 1 < surface(ship);
	}

	/**
	 * How fast the ship moves up or down this tick, or null to float on the surface as usual.
	 * Called by ShipEntity.tick on the game that steers the ship.
	 */
	public static Double verticalSpeed(ShipEntity ship) {
		if (!canDive(ship)) {
			return null;
		}
		double depth = depth(ship);
		int input = ship.getControllingPassenger() instanceof Player captain ? diveInput.applyAsInt(captain) : 0;
		if (depth < 0.3 && input >= 0) {
			return null; // On the surface: float.
		}
		if (input < 0) {
			return depth >= maxDepth(ship) ? 0.0 : -DIVE_SPEED;
		}
		if (input > 0) {
			return depth < 0.6 ? null : RISE_SPEED;
		}
		return 0.0; // Hold this depth.
	}

	/** Under the sea, sails catch no wind: a submarine runs on its engine, a coated ship on the deep currents. */
	public static double speedFactor(ShipEntity ship, double sailSpeed, double baseSpeed) {
		if (isSubmarine(ship)) {
			// A submarine's engine: steady speed with or without sails, and no wind needed (subs cross the Calm Belt).
			return Math.max(sailSpeed, baseSpeed * 2.2);
		}
		if (isDown(ship)) {
			return Math.max(baseSpeed, sailSpeed * 0.6);
		}
		return sailSpeed;
	}

	/** Why the captain can't drop anchor here, or null. Anchoring turns the ship back into blocks, which would flood. */
	public static String dockBlockedReason(ShipEntity ship) {
		if (isDown(ship)) {
			return "You can't drop anchor under the sea. Surface first (hold Jump).";
		}
		return null;
	}

	/**
	 * Is this point (in the ship's own grid, see ShipHold) inside the ship's bubble? A coated ship carries a big air
	 * bubble around her whole hull, decks and rigging, like the Thousand Sunny on the way to Fish-Man Island.
	 */
	public static boolean inBubble(ShipEntity ship, Vec3 local) {
		if (!isCoated(ship)) {
			return false;
		}
		ShipLayout layout = ship.getLayout();
		double cx = (layout.min.getX() + layout.max.getX()) / 2.0;
		double cy = (layout.min.getY() + layout.max.getY() + 1) / 2.0;
		double cz = (layout.min.getZ() + layout.max.getZ()) / 2.0;
		double rx = bubbleRadius(layout.max.getX() - layout.min.getX());
		double ry = bubbleRadius(layout.max.getY() - layout.min.getY());
		double rz = bubbleRadius(layout.max.getZ() - layout.min.getZ());
		double dx = (local.x - cx) / rx, dy = (local.y - cy) / ry, dz = (local.z - cz) / rz;
		return dx * dx + dy * dy + dz * dz <= 1.0;
	}

	/** Half the ship's length along one axis, plus room to stand at the rail. */
	public static double bubbleRadius(int extent) {
		return (extent + 1) / 2.0 + 2.5;
	}

	// ---- Every tick, both sides ----

	/** Server: the coating wears while down, depth warnings, and the bubble bursting. Called from ShipEntity.tick. */
	public static void tick(ShipEntity ship) {
		if (!(ship.level() instanceof ServerLevel level)) {
			return;
		}
		boolean down = isDown(ship);
		int coating = ship.coating();
		if (coating > 0 && down) {
			ship.setCoating(coating - 1);
			if (coating - 1 == ShipCoating.WARN_TICKS) {
				tell(ship, Component.literal("The bubble coating is wearing thin! About a minute of air left. Surface soon.").withStyle(ChatFormatting.GOLD));
			}
			if (coating - 1 == 0) {
				level.playSound(null, ship.getX(), ship.getY() + ship.getLayout().waterline, ship.getZ(),
						SoundEvents.BUBBLE_POP, SoundSource.NEUTRAL, 3.0f, 0.6f);
				tell(ship, Component.literal("The coating bursts! The sea rushes in and the ship rises.").withStyle(ChatFormatting.RED));
			}
		}
		if (down && ship.tickCount % 40 == 0 && isSubmarine(ship) && !isCoated(ship)) {
			int max = maxDepth(ship);
			if (depth(ship) >= max - 0.5) {
				// The hull groans at its rated depth.
				level.playSound(null, ship.getX(), ship.getY(), ship.getZ(), SoundEvents.WOOD_BREAK, SoundSource.NEUTRAL, 1.5f, 0.5f);
				if (ship.tickCount % 1200 == 0) {
					tell(ship, Component.literal("The hull creaks: she's rated to " + max + " blocks deep. More Ballast Tanks or Hull upgrades go deeper.")
							.withStyle(ChatFormatting.YELLOW));
				}
			}
		}
	}

	private static void tell(ShipEntity ship, Component text) {
		for (ServerPlayer player : ShipEntity.playersAboard(ship)) {
			player.sendSystemMessage(text);
		}
	}
}
