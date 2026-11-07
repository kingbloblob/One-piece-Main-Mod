package com.onepiecemod.anim;

/**
 * Every custom body animation a person-shaped mob (or player) can play: sword slashes, punches, kicks,
 * casting poses, ground slams... The server picks one when a move is used (see CombatAnims) and every
 * nearby player's game plays it on that entity's model (see anim/client/Poses).
 *
 * ticks is how long the animation lasts (20 ticks = 1 second).
 */
public enum Anim {
	/** A wide sword cut from right to left. */
	SLASH(10),
	/** An overhead chop straight down. */
	CHOP(11),
	/** A full spin with the swords held out (Tatsumaki, boss sword sweeps). */
	SPIN_SLASH(14),
	/** Both arms cross high, then cut down and outward (Nitoryu, Paradise Totsuka). */
	CROSS_SLASH(12),
	/** A straight stab forward (sword lunges, Shigan, Gavotte). */
	THRUST(8),
	/** A straight punch with the right fist. */
	PUNCH(8),
	/** A straight punch with the left fist. */
	PUNCH_LEFT(8),
	/** A rising punch from low down (haymakers). */
	UPPERCUT(10),
	/** Lots of fast punches with both fists (Gatling, Fist of Love). */
	BARRAGE(20),
	/** A high front kick with the right leg. */
	KICK(10),
	/** A spinning kick with the leg out wide (Party Table, Rankyaku). */
	SPIN_KICK(14),
	/** Leg raised high and dropped like an axe (Concasse). */
	HEEL_DROP(12),
	/** Both palms thrust forward to fire something (beams, breath, waves). */
	CAST(14),
	/** One arm points forward to fire something (lasers, orbs, curses). */
	POINT(12),
	/** Both arms raised to the sky, then brought down (lightning, meteors, strings). */
	SUMMON(16),
	/** Arms crossed, then flung out in a burst of power (power-ups, transformations, Armament). */
	POWER_UP(16),
	/** Chest out, arms spread, head back: Conqueror's Haki. */
	ROAR(20),
	/** Both fists raised overhead and smashed into the ground. */
	GROUND_SLAM(14),
	/** Crouch, then leap forward with claws out (Zoan users). */
	POUNCE(12),
	/** A diagonal claw swipe (Dragon Claw). */
	CLAW(8),
	/** Leaning forward with the arms back, moving too fast to see (Soru, teleports). */
	DASH(8),
	/** An overhand throw (bombs, cannonballs). */
	THROW(10),
	/** A quick backhand flick (Uchimizu, water shots). */
	FLICK(8),
	/** Draw back a slingshot or bow and let go. */
	SHOOT(12),
	/** Arms crossed in front, braced (Tekkai, Samehada). */
	GUARD(20);

	public final int ticks;

	Anim(int ticks) {
		this.ticks = ticks;
	}

	private static final Anim[] VALUES = values();

	public static Anim byId(int id) {
		return id >= 0 && id < VALUES.length ? VALUES[id] : null;
	}
}
