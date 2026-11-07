package com.onepiecemod.weather;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/**
 * How sea events push things around. This runs on the server AND on each player's game,
 * because the captain's own game is the one that moves a ship.
 */
public class SeaForces {
	// ---- Tune these to make events stronger or weaker ----
	/** How hard storm winds shove a ship sideways, in blocks per tick at full gust. */
	public static final double STORM_PUSH = 0.07;
	/** How hard a whirlpool drags a ship toward its middle, at the very middle. */
	public static final double WHIRLPOOL_PULL = 0.11;
	/** How fast a whirlpool spins a ship around, at the very middle. */
	public static final double WHIRLPOOL_SPIN = 0.16;
	/** How hard Aqua Laguna's wave throws a ship. */
	public static final double WAVE_PUSH = 0.4;
	/** How hard a waterspout drags a ship toward its funnel and spins it. */
	public static final double SPOUT_PULL = 0.08;
	public static final double SPOUT_SPIN = 0.18;

	/** The events this side of the game knows about. */
	public static List<SeaEvent> events(Level level) {
		return level.isClientSide() ? SeaEventSync.CLIENT_EVENTS : SeaEvents.ACTIVE;
	}

	/** Extra wind in a ship's sails here. The Calm Belt's "no wind" is applied on top of this by multiplying. */
	public static double windAt(Level level, BlockPos pos) {
		long time = level.getGameTime();
		double wind = 1.0;
		for (SeaEvent event : events(level)) {
			if (event.isActive(time) && event.isInside(pos.getX() + 0.5, pos.getZ() + 0.5)) {
				wind *= event.type.wind;
			}
		}
		return wind;
	}

	/** Extra movement for a ship (or anything floating) this tick, from every event it's in. */
	public static Vec3 push(Entity entity) {
		Level level = entity.level();
		long time = level.getGameTime();
		Vec3 total = Vec3.ZERO;
		for (SeaEvent event : events(level)) {
			if (event.isActive(time)) {
				total = total.add(push(event, entity.getX(), entity.getZ(), time));
			}
		}
		return total;
	}

	public static Vec3 push(SeaEvent event, double x, double z, long time) {
		switch (event.type) {
			case STORM -> {
				if (!event.isInside(x, z)) {
					return Vec3.ZERO;
				}
				return event.direction().scale(STORM_PUSH * event.gust(time));
			}
			case WHIRLPOOL -> {
				double distance = event.distance(x, z);
				if (distance > event.radius || distance < 0.01) {
					return Vec3.ZERO;
				}
				// Stronger the closer you get. The arrow inward plus an arrow around the circle makes a spiral.
				double strength = 1.0 - distance / event.radius;
				strength = strength * strength * 0.7 + strength * 0.3;
				Vec3 inward = new Vec3(event.x - x, 0, event.z - z).normalize();
				Vec3 around = new Vec3(-inward.z, 0, inward.x);
				return inward.scale(WHIRLPOOL_PULL * strength).add(around.scale(WHIRLPOOL_SPIN * strength));
			}
			case WATERSPOUT -> {
				Vec3 spout = event.spout(time);
				double dx = spout.x - x;
				double dz = spout.z - z;
				double distance = Math.sqrt(dx * dx + dz * dz);
				double reach = SeaEvent.SPOUT_RADIUS * 2.5;
				if (distance > reach || distance < 0.01) {
					return Vec3.ZERO;
				}
				double strength = 1.0 - distance / reach;
				Vec3 inward = new Vec3(dx / distance, 0, dz / distance);
				Vec3 around = new Vec3(-inward.z, 0, inward.x);
				return inward.scale(SPOUT_PULL * strength).add(around.scale(SPOUT_SPIN * strength * strength));
			}
			case AQUA_LAGUNA, ROGUE_WAVE -> {
				Vec3 dir = event.direction();
				double along = (x - event.x) * dir.x + (z - event.z) * dir.z;
				double side = Math.abs((x - event.x) * dir.z - (z - event.z) * dir.x);
				double front = event.waveFront(time);
				if (side < event.radius && along < front && along > front - 8) {
					return dir.scale(event.type == SeaEventType.ROGUE_WAVE ? WAVE_PUSH * 0.75 : WAVE_PUSH);
				}
				return Vec3.ZERO;
			}
			case CALM_BELT_AMBUSH -> {
				if (!event.isInside(x, z)) {
					return Vec3.ZERO;
				}
				// Sea Kings bumping the hull from below: the ship lurches this way and that.
				double t = (time + event.id * 13) / 9.0;
				return new Vec3(Math.sin(t) * 0.04, 0, Math.cos(t * 1.3) * 0.04);
			}
			default -> {
				return Vec3.ZERO;
			}
		}
	}
}
