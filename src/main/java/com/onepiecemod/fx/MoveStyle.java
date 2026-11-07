package com.onepiecemod.fx;

/**
 * The shapes a Devil Fruit move can draw in the world. Each one is drawn by MoveRenderer on the client.
 *
 * "Length" means how far the shape reaches (for arms, fists, beams) or how wide it gets (for rings,
 * spheres, spikes). "Size" is how thick it is.
 */
public enum MoveStyle {
	/** A stretchy rubber arm that shoots out from the shoulder and snaps back (Gomu Gomu). */
	ARM,
	/** A huge fist made of an element that flies forward, with a trail behind it (Hiken, Dai Funka). */
	FIST,
	/** A straight glowing beam that thins out and fades (lasers, breath, strings). */
	BEAM,
	/** A pointed crystal that flies forward and shatters (ice spears, weapons). */
	SPEAR,
	/** A glowing ball that flies forward and bursts (fireballs, poison, generic blasts). */
	ORB,
	/** A jagged bolt of lightning that flickers. */
	BOLT,
	/** A bubble that grows and fades. With a negative size it shrinks instead (Black Hole). */
	SPHERE,
	/** A flat shockwave ring that spreads out along the ground. */
	RING,
	/** A crescent blade cut in front of you. */
	SLASH,
	/** Three claw marks (Zoan pounces). */
	CLAW,
	/** A column that bursts up out of the ground (volcanoes, fire pillars). */
	PILLAR,
	/** Crystals or roots that burst out of the ground in a circle (Ice Age, Mori Mori). */
	SPIKES,
	/** A spinning funnel (sandstorms, smoke). */
	TORNADO,
	/** Cracks in the air itself (Gura Gura). */
	CRACK,
	// Added in the 2026-11-03 polish pass. New shapes go at the end, so the ids of the old ones don't change.
	/** An explosion: a white-hot core, rays shooting out and a smoke ring (Bomu, Pamu, Shiro, Buki). */
	BURST,
	/** A glowing doorway or portal standing in the air, facing along its reach (Wapu, Doa, Mira, Toki). */
	GATE,
	/** Sound waves: rings that roll forward along the reach and grow as they go (Oto Oto). */
	WAVES,
	/** A glassy panel of hexagons facing along its reach (Bari Bari walls, diamond and stone skin). */
	SHIELD,
	/** Two ribbons of light spiraling up around you, following you (power-ups and healing). */
	HELIX,
	/** A spider web or net spreading out flat, facing along its reach (Kumo, Ori, Nui). */
	WEB;

	private static final MoveStyle[] VALUES = values();

	public static MoveStyle byId(int id) {
		return id >= 0 && id < VALUES.length ? VALUES[id] : ORB;
	}
}
