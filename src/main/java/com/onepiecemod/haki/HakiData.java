package com.onepiecemod.haki;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

/**
 * A player's Haki, saved on the player.
 *
 * @param observationXp training points for Observation Haki (sensing and dodging)
 * @param armamentXp    training points for Armament Haki (hardening)
 * @param conquerorXp   training points for Conqueror's Haki, only grows once awakened
 * @param conqueror     true if this player has the rare Conqueror's Haki
 * @param observationOn whether Observation Haki is switched on
 * @param armamentOn    whether Armament Haki is switched on
 * @param bornRolled    true once we rolled the "born with Conqueror's Haki" chance for this player
 */
public record HakiData(int observationXp, int armamentXp, int conquerorXp, boolean conqueror,
		boolean observationOn, boolean armamentOn, boolean bornRolled) {
	public static final HakiData EMPTY = new HakiData(0, 0, 0, false, true, false, false);

	public static final Codec<HakiData> CODEC = RecordCodecBuilder.create(instance -> instance.group(
			Codec.INT.optionalFieldOf("observation_xp", 0).forGetter(HakiData::observationXp),
			Codec.INT.optionalFieldOf("armament_xp", 0).forGetter(HakiData::armamentXp),
			Codec.INT.optionalFieldOf("conqueror_xp", 0).forGetter(HakiData::conquerorXp),
			Codec.BOOL.optionalFieldOf("conqueror", false).forGetter(HakiData::conqueror),
			Codec.BOOL.optionalFieldOf("observation_on", true).forGetter(HakiData::observationOn),
			Codec.BOOL.optionalFieldOf("armament_on", false).forGetter(HakiData::armamentOn),
			Codec.BOOL.optionalFieldOf("born_rolled", false).forGetter(HakiData::bornRolled)
	).apply(instance, HakiData::new));

	/** Training points needed for levels 1 to 5. Level 0 means "not awakened yet". */
	private static final int[] LEVEL_XP = {100, 400, 1000, 2500, 6000}; // Balance pass 2026-10-24: was 50/200/500/1200/3000.
	public static final int MAX_LEVEL = LEVEL_XP.length;

	/** Turns training points into a level from 0 (locked) to 5 (master). */
	public static int level(int xp) {
		int level = 0;
		while (level < LEVEL_XP.length && xp >= LEVEL_XP[level]) {
			level++;
		}
		return level;
	}

	/** Training points still needed for the next level, or 0 at max level. */
	public static int xpToNext(int xp) {
		int level = level(xp);
		return level >= MAX_LEVEL ? 0 : LEVEL_XP[level] - xp;
	}

	public int observationLevel() {
		return level(observationXp);
	}

	public int armamentLevel() {
		return level(armamentXp);
	}

	/** Conqueror's Haki starts at level 1 the moment it awakens. */
	public int conquerorLevel() {
		return conqueror ? Math.max(1, level(conquerorXp)) : 0;
	}

	public HakiData withObservationXp(int xp) {
		return new HakiData(xp, armamentXp, conquerorXp, conqueror, observationOn, armamentOn, bornRolled);
	}

	public HakiData withArmamentXp(int xp) {
		return new HakiData(observationXp, xp, conquerorXp, conqueror, observationOn, armamentOn, bornRolled);
	}

	public HakiData withConquerorXp(int xp) {
		return new HakiData(observationXp, armamentXp, xp, conqueror, observationOn, armamentOn, bornRolled);
	}

	public HakiData withConqueror(boolean value) {
		return new HakiData(observationXp, armamentXp, conquerorXp, value, observationOn, armamentOn, true);
	}

	public HakiData withObservationOn(boolean value) {
		return new HakiData(observationXp, armamentXp, conquerorXp, conqueror, value, armamentOn, bornRolled);
	}

	public HakiData withArmamentOn(boolean value) {
		return new HakiData(observationXp, armamentXp, conquerorXp, conqueror, observationOn, value, bornRolled);
	}

	public HakiData withBornRolled() {
		return new HakiData(observationXp, armamentXp, conquerorXp, conqueror, observationOn, armamentOn, true);
	}
}
