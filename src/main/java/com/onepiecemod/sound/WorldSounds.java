package com.onepiecemod.sound;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;

import com.onepiecemod.ship.ShipEntity;

/**
 * Ship, sea and creature sounds. All made from scratch by tools/sounds (sfx_world.py).
 * Creatures pick a voice in creature/CreatureSpecies with voice("bear"), which uses
 * onepiece_sounds:creature.bear_ambient, _hurt and _death.
 */
public class WorldSounds {
	public static final SoundEvent SHIP_CREAK = ModSounds.register("ship.creak");
	public static final SoundEvent SHIP_SAIL = ModSounds.register("ship.sail");
	public static final SoundEvent SHIP_WAKE = ModSounds.register("ship.wake");
	public static final SoundEvent SHIP_LAUNCH = ModSounds.register("ship.launch");
	public static final SoundEvent SHIP_HULL_HIT = ModSounds.register("ship.hull_hit");
	public static final SoundEvent SHIP_REPAIR = ModSounds.register("ship.repair");
	public static final SoundEvent SHIP_SINK = ModSounds.register("ship.sink");
	public static final SoundEvent SHIP_BREAK = ModSounds.register("ship.break");
	public static final SoundEvent CANNONBALL_SPLASH = ModSounds.register("ship.cannonball_splash");
	public static final SoundEvent GRAPPLE = ModSounds.register("ship.grapple");
	public static final SoundEvent BOARDING = ModSounds.register("ship.boarding");
	public static final SoundEvent WHIRLPOOL = ModSounds.register("sea.whirlpool");
	public static final SoundEvent WAVE_CRASH = ModSounds.register("sea.wave_crash");

	/** Creature voices: each has _ambient, _hurt and _death sounds. */
	public static final String[] VOICES = {"snail", "deer", "giant", "bird", "bear", "horse", "seal", "bull", "cat", "wolf",
			"snake", "sea_monster", "monkey", "reptile", "dragon", "bug", "machine", "tree", "mole"};
	public static final SoundEvent SEA_KING_AMBIENT;
	public static final SoundEvent SEA_KING_HURT;
	public static final SoundEvent SEA_KING_DEATH;

	static {
		for (String voice : VOICES) {
			for (String kind : new String[] {"ambient", "hurt", "death"}) {
				ModSounds.register("creature." + voice + "_" + kind);
			}
		}
		SEA_KING_AMBIENT = voice("sea_monster", "ambient");
		SEA_KING_HURT = voice("sea_monster", "hurt");
		SEA_KING_DEATH = voice("sea_monster", "death");
	}

	private static SoundEvent voice(String voice, String kind) {
		return net.minecraft.core.registries.BuiltInRegistries.SOUND_EVENT.getValue(
				net.minecraft.resources.Identifier.fromNamespaceAndPath(ModSounds.NAMESPACE, "creature." + voice + "_" + kind));
	}

	/**
	 * Called every tick by each ship on the server: the hull creaks now and then, and while it sails the
	 * sails fill and water rushes past. Quiet, so a harbour full of ships doesn't get noisy.
	 */
	public static void tickShip(ShipEntity ship) {
		if (!(ship.level() instanceof ServerLevel level) || ship.isRemoved()) {
			return;
		}
		// Spread ships out so they don't all creak on the same tick.
		int tick = ship.tickCount + (ship.getId() * 37);
		double moved = ship.position().subtract(ship.xo, ship.yo, ship.zo).horizontalDistanceSqr();
		boolean sailing = moved > 0.0025; // faster than about 1 block a second
		if (tick % 120 == 0 && level.getRandom().nextFloat() < (sailing ? 0.9f : 0.4f)) {
			play(level, ship, SHIP_CREAK, sailing ? 0.8f : 0.5f);
		}
		if (sailing && tick % 50 == 0) {
			play(level, ship, SHIP_WAKE, 0.6f);
		}
		if (sailing && tick % 200 == 100) {
			play(level, ship, SHIP_SAIL, 0.6f);
		}
	}

	private static void play(ServerLevel level, ShipEntity ship, SoundEvent sound, float volume) {
		level.playSound(null, ship.getX(), ship.getY() + 1, ship.getZ(), sound, SoundSource.NEUTRAL, volume,
				0.9f + level.getRandom().nextFloat() * 0.2f);
	}

	/** Called once from SoundFeature so the class loads and every sound gets registered. */
	static void initialize() {
	}
}
