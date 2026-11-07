package com.onepiecemod.weather;

import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;

/**
 * One event happening somewhere at sea: what it is, where its middle is, how big it is and when it starts and ends.
 * The server keeps the real list. Each player's game gets a copy (see SeaEventSync) so ships can feel the
 * wind and whirlpools smoothly, because the captain's own game moves the ship.
 *
 * Times are world game times in ticks (20 ticks = 1 second).
 */
public class SeaEvent {
	/** Aqua Laguna's wave starts this far out at sea and rolls this fast (blocks per tick). */
	public static final double WAVE_START = -60;
	public static final double WAVE_SPEED = 0.5;

	/** Waterspout: how close to the funnel you get caught, in blocks. */
	public static final double SPOUT_RADIUS = 7;

	/** Great Cyclone: how wide the tornado's funnel is where it touches the sea, in blocks. */
	public static final double FUNNEL_RADIUS = 9;

	public final int id;
	public final SeaEventType type;
	/** Where the event started. Most events stay there; a drifting one (the Great Cyclone) moves on from it. */
	public final double originX;
	public final double originZ;
	/** Where its middle is right now (see advance). */
	public double x;
	public double z;
	public final float radius;
	/** The warning lasts until this time, then the event really starts. */
	public final long startTime;
	public final long endTime;
	/** Storms: which way the wind blows. Aqua Laguna: which way the wave rolls. In radians. */
	public final float angle;

	// Server only: who was already warned or hit, so it only happens once each.
	final Set<UUID> told = new HashSet<>();
	final Set<UUID> toldStart = new HashSet<>();
	final Set<UUID> hitByWave = new HashSet<>();
	final Set<UUID> reachedFunnel = new HashSet<>();
	boolean started;

	public SeaEvent(int id, SeaEventType type, double x, double z, float radius, long startTime, long endTime, float angle) {
		this.id = id;
		this.type = type;
		this.originX = x;
		this.originZ = z;
		this.x = x;
		this.z = z;
		this.radius = radius;
		this.startTime = startTime;
		this.endTime = endTime;
		this.angle = angle;
	}

	/**
	 * Moves a drifting event's middle to where it is at this time. It sits still during the warning, then drifts along its
	 * angle. Same sums on the server and every player's game, so both agree where the storm is.
	 */
	public void advance(long time) {
		if (type.drift <= 0) {
			return;
		}
		double travelled = Math.max(0, time - startTime) * type.drift;
		Vec3 dir = direction();
		x = originX + dir.x * travelled;
		z = originZ + dir.z * travelled;
	}

	/** Great Cyclone: true inside the funnel itself. */
	public boolean inFunnel(double px, double pz) {
		return type == SeaEventType.CYCLONE && distance(px, pz) <= FUNNEL_RADIUS;
	}

	public boolean isActive(long time) {
		return time >= startTime && time < endTime;
	}

	public double distance(double px, double pz) {
		return Math.sqrt(Mth.square(px - x) + Mth.square(pz - z));
	}

	public boolean isInside(double px, double pz) {
		return distance(px, pz) <= radius;
	}

	/** Which way the wind or wave goes, as a flat arrow one block long. */
	public Vec3 direction() {
		return new Vec3(Math.cos(angle), 0, Math.sin(angle));
	}

	/** Aqua Laguna: how far past the middle (the beach) the wave's front is right now. */
	public double waveFront(long time) {
		return WAVE_START + (time - startTime) * WAVE_SPEED;
	}

	/**
	 * Waterspout: where the funnel touches the sea right now. It crosses the event's area along its angle, weaving
	 * from side to side, so you can see it coming and steer around it. Same on the server and every player's game.
	 */
	public Vec3 spout(long time) {
		double total = Math.max(1, endTime - startTime);
		double t = Mth.clamp((time - startTime) / total, 0, 1);
		double along = -radius * 0.7 + t * radius * 1.4;
		double weave = Math.sin((time + id * 31) / 45.0) * 12;
		Vec3 dir = direction();
		return new Vec3(x + dir.x * along - dir.z * weave, 0, z + dir.z * along + dir.x * weave);
	}

	/** How strong the storm's gusts are right now, from 0.3 to 1. Same on the server and every player's game. */
	public double gust(long time) {
		return 0.65 + 0.35 * Math.sin((time + id * 37) / 30.0);
	}

	// ---- Sending to players ----

	public void write(FriendlyByteBuf buf) {
		buf.writeVarInt(id);
		buf.writeVarInt(type.ordinal());
		buf.writeDouble(originX);
		buf.writeDouble(originZ);
		buf.writeFloat(radius);
		buf.writeLong(startTime);
		buf.writeLong(endTime);
		buf.writeFloat(angle);
	}

	public static SeaEvent read(FriendlyByteBuf buf) {
		int id = buf.readVarInt();
		SeaEventType type = SeaEventType.values()[buf.readVarInt()];
		return new SeaEvent(id, type, buf.readDouble(), buf.readDouble(), buf.readFloat(), buf.readLong(), buf.readLong(), buf.readFloat());
	}
}
