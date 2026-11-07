package com.onepiecemod.sound;

import net.minecraft.sounds.SoundEvent;

/**
 * Boss fight sounds: the fight starting, phase roars, wind-ups, signature moves and each boss power.
 * All made from scratch by tools/sounds (sfx_combat.py). Played from character/CharacterEntity,
 * BossAbility and BossStrikes.
 */
public class BossSounds {
	public static final SoundEvent INTRO = ModSounds.register("boss.intro");
	public static final SoundEvent PHASE = ModSounds.register("boss.phase");
	public static final SoundEvent WINDUP = ModSounds.register("boss.windup");
	public static final SoundEvent SIGNATURE = ModSounds.register("boss.signature");
	public static final SoundEvent STRIKE_LAND = ModSounds.register("boss.strike_land");
	public static final SoundEvent SLASH_LINE = ModSounds.register("boss.slash_line");
	public static final SoundEvent BLACK_HOLE = ModSounds.register("boss.black_hole");
	public static final SoundEvent GROUND_WAVE = ModSounds.register("boss.ground_wave");
	public static final SoundEvent ENRAGE = ModSounds.register("boss.enrage");
	public static final SoundEvent LEAP = ModSounds.register("boss.leap");
	public static final SoundEvent PETRIFY = ModSounds.register("boss.petrify");
	public static final SoundEvent PAW = ModSounds.register("boss.paw");
	public static final SoundEvent HEAL = ModSounds.register("boss.heal");

	/** Called once from SoundFeature so the class loads and every sound gets registered. */
	static void initialize() {
	}
}
