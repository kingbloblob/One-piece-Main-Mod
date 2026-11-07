package com.onepiecemod.weather.client;

import java.util.HashMap;
import java.util.Map;

import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.Particle;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ParticleStatus;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;

import com.onepiecemod.weather.SeaEvent;
import com.onepiecemod.weather.SeaEventSync;
import com.onepiecemod.weather.SeaEventType;

/**
 * Draws whirlpools and Aqua Laguna's wave on this player's own game, from the copy of the events the server sends.
 * Doing it here means lots of particles with no lag, visible from far away, sitting right on the water.
 */
public class WeatherVisuals {
	/** How far away you can see these, in blocks. */
	private static final double VIEW_DISTANCE = 160;

	private static final ParticleOptions FOAM = new DustParticleOptions(0xF4FAFF, 2.5f);
	private static final ParticleOptions LIGHT_WATER = new DustParticleOptions(0x5FA8E0, 3.0f);
	private static final ParticleOptions DEEP_WATER = new DustParticleOptions(0x1C4F86, 3.5f);
	private static final ParticleOptions EYE = new DustParticleOptions(0x06182C, 4.0f);
	private static final ParticleOptions WAVE_BODY = new DustParticleOptions(0x2E78C8, 4.0f);
	private static final ParticleOptions WAVE_DARK = new DustParticleOptions(0x1A5596, 4.0f);

	/** Where the water's surface is under each whirlpool, so the swirl sits on the water and not in the air. */
	private static final Map<Integer, Double> SURFACE = new HashMap<>();
	/** Longest a whirlpool or wave particle lives, in ticks. New ones appear every tick, so the shape stays full. */
	private static final int MAX_LIFE = 20;

	public static void initialize() {
		ClientTickEvents.END_CLIENT_TICK.register(client -> {
			ClientLevel level = client.level;
			if (level == null || client.player == null || client.isPaused()) {
				return;
			}
			long time = level.getGameTime();
			Vec3 eye = client.player.position();
			for (SeaEvent event : SeaEventSync.CLIENT_EVENTS) {
				if (event.distance(eye.x, eye.z) > VIEW_DISTANCE + event.radius) {
					continue;
				}
				if (event.type == SeaEventType.WHIRLPOOL) {
					whirlpool(level, event, time);
				} else if (event.type == SeaEventType.AQUA_LAGUNA && event.isActive(time)) {
					wave(level, event, time, 10);
				} else if (event.type == SeaEventType.ROGUE_WAVE && event.isActive(time)) {
					wave(level, event, time, 7);
				} else if (event.type == SeaEventType.WATERSPOUT) {
					waterspout(level, event, time);
				}
			}
			if (SeaEventSync.CLIENT_EVENTS.isEmpty()) {
				SURFACE.clear();
			}
		});
	}

	// ---- Whirlpool: spiral arms of foam turning around a dark eye ----

	private static void whirlpool(ClientLevel level, SeaEvent event, long time) {
		RandomSource random = level.getRandom();
		double y = SURFACE.computeIfAbsent(event.id, id -> waterSurface(level, event.x, event.z)) + 0.15;
		boolean active = event.isActive(time);
		// While it's still a warning, it's just a slow ring that's starting to turn.
		float size = active ? event.radius : 7;
		int arms = active ? 5 : 3;
		int perArm = active ? 14 : 4;
		double spin = time * (active ? 0.09 : 0.03);

		for (int arm = 0; arm < arms; arm++) {
			for (int i = 0; i < perArm; i++) {
				double r = 1.5 + random.nextDouble() * (size - 1.5);
				// Inner parts turn faster, so the arms curl into a spiral.
				double angle = spin * (1 + 2.5 * (size - r) / size) + arm * Mth.TWO_PI / arms + r * 0.35;
				double x = event.x + Math.cos(angle) * r;
				double z = event.z + Math.sin(angle) * r;
				double edge = r / size;
				ParticleOptions look = edge < 0.25 ? DEEP_WATER : random.nextFloat() < 0.65f ? FOAM : LIGHT_WATER;
				spawn(level, look, x, y - (1 - edge) * 1.2, z, 0, 0, 0);
			}
		}
		if (!active) {
			return;
		}

		// The dark eye in the middle, sinking down.
		for (int i = 0; i < 18; i++) {
			double r = random.nextDouble() * 3.5;
			double angle = random.nextDouble() * Mth.TWO_PI;
			spawn(level, EYE, event.x + Math.cos(angle) * r, y - 1.4 - random.nextDouble(), event.z + Math.sin(angle) * r, 0, 0, 0);
		}
		// Spray thrown around the circle, moving with the spin.
		for (int i = 0; i < 8; i++) {
			double r = 3 + random.nextDouble() * (size - 3);
			double angle = random.nextDouble() * Mth.TWO_PI;
			double speed = 0.35 * (1 - r / size) + 0.08;
			spawn(level, ParticleTypes.CLOUD, event.x + Math.cos(angle) * r, y + 0.2, event.z + Math.sin(angle) * r,
					-Math.sin(angle) * speed, 0.02, Math.cos(angle) * speed);
		}
		for (int i = 0; i < 4; i++) {
			spawn(level, ParticleTypes.SQUID_INK, event.x + (random.nextDouble() - 0.5) * 3, y - 0.5, event.z + (random.nextDouble() - 0.5) * 3,
					0, -0.15, 0);
		}
	}

	// ---- Aqua Laguna: a moving wall of blue water with white foam on top ----

	private static void wave(ClientLevel level, SeaEvent event, long time, double height) {
		RandomSource random = level.getRandom();
		Vec3 dir = event.direction();
		Vec3 side = new Vec3(-dir.z, 0, dir.x);
		double front = event.waveFront(time);
		double sea = level.getSeaLevel();

		for (double s = -event.radius; s <= event.radius; s += 2.5) {
			double bx = event.x + dir.x * front + side.x * s;
			double bz = event.z + dir.z * front + side.z * s;
			// The face of the wave, curling forward at the top.
			for (int i = 0; i < 4; i++) {
				double h = random.nextDouble() * height;
				double lean = (h / height) * (h / height) * 2.5;
				spawn(level, random.nextBoolean() ? WAVE_BODY : WAVE_DARK,
						bx + dir.x * lean - dir.x * random.nextDouble() * 3, sea + h, bz + dir.z * lean - dir.z * random.nextDouble() * 3,
						0, 0, 0);
			}
			// White foam crest.
			spawn(level, FOAM, bx + dir.x * 2.5, sea + height + random.nextDouble(), bz + dir.z * 2.5, 0, 0, 0);
			if (random.nextFloat() < 0.4f) {
				spawn(level, ParticleTypes.CLOUD, bx + dir.x * 3, sea + height, bz + dir.z * 3, dir.x * 0.3, 0.05, dir.z * 0.3);
			}
			if (random.nextFloat() < 0.5f) {
				spawn(level, ParticleTypes.FALLING_WATER, bx + dir.x * 3, sea + height - 0.5, bz + dir.z * 3, 0, 0, 0);
			}
		}
	}

	// ---- Waterspout: a twisting funnel of grey water from the sea up into the clouds ----

	private static final ParticleOptions SPOUT_GREY = new DustParticleOptions(0x7D8C99, 3.5f);
	private static final ParticleOptions SPOUT_DARK = new DustParticleOptions(0x46535E, 4.0f);

	private static void waterspout(ClientLevel level, SeaEvent event, long time) {
		RandomSource random = level.getRandom();
		Vec3 base = event.spout(Math.max(time, event.startTime));
		double sea = level.getSeaLevel();
		boolean active = event.isActive(time);
		// During the warning only the top of the funnel shows, reaching down out of the clouds.
		double top = sea + 40;
		double bottom = active ? sea : sea + 22;
		double spin = time * 0.35;
		int count = active ? 130 : 30;
		for (int i = 0; i < count; i++) {
			double h = bottom + random.nextDouble() * (top - bottom);
			double up = (h - sea) / (top - sea);
			// Thin at the sea, wide at the clouds, and leaning a little with the wind.
			double r = 1.5 + up * up * 8;
			double angle = spin + random.nextDouble() * Mth.TWO_PI;
			double lean = Math.sin((time + event.id * 31) / 45.0) * up * 3;
			double x = base.x + Math.cos(angle) * r + event.direction().z * lean;
			double z = base.z + Math.sin(angle) * r - event.direction().x * lean;
			spawn(level, random.nextFloat() < 0.6f ? SPOUT_GREY : SPOUT_DARK, x, h, z, -Math.sin(angle) * 0.25, 0.05, Math.cos(angle) * 0.25);
		}
		if (!active) {
			return;
		}
		// The skirt of spray where it sucks up the sea.
		for (int i = 0; i < 16; i++) {
			double angle = random.nextDouble() * Mth.TWO_PI;
			double r = 2 + random.nextDouble() * 4;
			spawn(level, random.nextBoolean() ? FOAM : ParticleTypes.CLOUD, base.x + Math.cos(angle) * r, sea + 0.3 + random.nextDouble(),
					base.z + Math.sin(angle) * r, -Math.sin(angle) * 0.3, 0.15, Math.cos(angle) * 0.3);
		}
		for (int i = 0; i < 4; i++) {
			spawn(level, ParticleTypes.FALLING_WATER, base.x + (random.nextDouble() - 0.5) * 16, sea + 20 + random.nextDouble() * 8,
					base.z + (random.nextDouble() - 0.5) * 16, 0, 0, 0);
		}
	}

	private static void spawn(ClientLevel level, ParticleOptions particle, double x, double y, double z, double vx, double vy, double vz) {
		// These skip the particle distance limit so you can see them from your ship. They still follow the Particles
		// setting (Decreased = half, Minimal = a quarter), and live at most MAX_LIFE ticks: big dust otherwise hangs
		// around for up to 8 seconds, and thousands of them made the game stutter on weaker PCs.
		Minecraft client = Minecraft.getInstance();
		ParticleStatus setting = client.options.particles().get();
		if (setting == ParticleStatus.MINIMAL ? level.getRandom().nextInt(4) != 0
				: setting == ParticleStatus.DECREASED && level.getRandom().nextBoolean()) {
			return;
		}
		Particle made = client.particleEngine.createParticle(particle, x, y, z, vx, vy, vz);
		if (made != null && made.getLifetime() > MAX_LIFE) {
			made.setLifetime(MAX_LIFE);
		}
	}

	/** The top of the water at this spot, or sea level if there's no water. */
	private static double waterSurface(ClientLevel level, double x, double z) {
		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
		for (int y = level.getSeaLevel() + 8; y > level.getSeaLevel() - 16; y--) {
			pos.set(x, y, z);
			if (level.getFluidState(pos).is(FluidTags.WATER)) {
				return y + level.getFluidState(pos).getHeight(level, pos);
			}
		}
		return level.getSeaLevel();
	}
}
