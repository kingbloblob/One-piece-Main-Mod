package com.onepiecemod.sound;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.LivingEntity;

import com.onepiecemod.style.Technique;

/**
 * Fighting style sounds: one per kind of technique (a flying slash, Soru, Tekkai, a burning leg...).
 * All made from scratch by tools/sounds (sfx_combat.py). StyleMoves plays them when a technique is used.
 */
public class StyleSounds {
	public static final SoundEvent DASH_SLASH = ModSounds.register("style.dash_slash");
	public static final SoundEvent TORNADO = ModSounds.register("style.tornado");
	public static final SoundEvent BIG_SLASH = ModSounds.register("style.big_slash");
	public static final SoundEvent POWER_UP = ModSounds.register("style.power_up");
	public static final SoundEvent KICK = ModSounds.register("style.kick");
	public static final SoundEvent FIRE_KICK = ModSounds.register("style.fire_kick");
	public static final SoundEvent FIRE_SLASH = ModSounds.register("style.fire_slash");
	public static final SoundEvent SHOCK_PUNCH = ModSounds.register("style.shock_punch");
	public static final SoundEvent GROUND_CRUSH = ModSounds.register("style.ground_crush");
	public static final SoundEvent WATER_SHOT = ModSounds.register("style.water_shot");
	public static final SoundEvent WATER_WAVE = ModSounds.register("style.water_wave");
	public static final SoundEvent HARD_SKIN = ModSounds.register("style.hard_skin");
	public static final SoundEvent SORU = ModSounds.register("style.soru");
	public static final SoundEvent SHIGAN = ModSounds.register("style.shigan");
	public static final SoundEvent TEKKAI = ModSounds.register("style.tekkai");
	public static final SoundEvent GEPPO = ModSounds.register("style.geppo");
	public static final SoundEvent CLAW = ModSounds.register("style.claw");
	public static final SoundEvent CUT_FLAMES = ModSounds.register("style.cut_flames");
	public static final SoundEvent SHEATHE = ModSounds.register("style.sheathe");
	public static final SoundEvent LUNGE = ModSounds.register("style.lunge");
	public static final SoundEvent CHILL_BLADE = ModSounds.register("style.chill_blade");
	public static final SoundEvent LULLABY = ModSounds.register("style.lullaby");
	public static final SoundEvent PUNCH = ModSounds.register("style.punch");
	public static final SoundEvent THROW = ModSounds.register("style.throw");
	public static final SoundEvent SLINGSHOT = ModSounds.register("style.slingshot");

	/** The sound a technique makes when it's used. */
	public static SoundEvent of(Technique technique) {
		return switch (technique) {
			case ONI_GIRI -> DASH_SLASH;
			case TATSUMAKI -> TORNADO;
			case POUND_HO, RANKYAKU, PARADISE_TOTSUKA, TOGEN_TOTSUKA, ODENS_SCAR -> BIG_SLASH;
			case ASURA, BOILING_WILL -> POWER_UP;
			case CONCASSE, PARTY_TABLE -> KICK;
			case DIABLE_JAMBE, IFRIT_JAMBE -> FIRE_KICK;
			case HOMURA_GIRI, KITSUNEBI_BLADE -> FIRE_SLASH;
			case HIKEN -> ModSounds.MOVE_FIRE;
			case THOUSAND_BRICK, ROKUOGAN, GALAXY_IMPACT -> SHOCK_PUNCH;
			case RYU_NO_IBUKI -> GROUND_CRUSH;
			case UCHIMIZU -> WATER_SHOT;
			case BURAIKAN -> WATER_WAVE;
			case SAMEHADA -> HARD_SKIN;
			case SORU -> SORU;
			case SHIGAN -> SHIGAN;
			case TEKKAI -> TEKKAI;
			case RYU_NO_KAGIZUME -> CLAW;
			case CUT_THE_FLAMES -> CUT_FLAMES;
			case YAHAZU_GIRI -> SHEATHE;
			case GAVOTTE -> LUNGE;
			case SOUL_SOLID -> CHILL_BLADE;
			case LULLABY -> LULLABY;
			case FIST_OF_LOVE_PUNCH -> PUNCH;
			case CANNONBALL -> THROW;
			case LEAD_STAR, KAEN_BOSHI, POP_GREEN, FIREBIRD_STAR -> SLINGSHOT;
		};
	}

	/** Plays a technique's sound at the fighter, for everyone nearby. */
	public static void play(Technique technique, LivingEntity at, ServerLevel level) {
		play(of(technique), at, level, 1.0f);
	}

	public static void play(SoundEvent sound, LivingEntity at, ServerLevel level, float volume) {
		level.playSound(null, at.getX(), at.getY(), at.getZ(), sound, SoundSource.PLAYERS, volume, 0.95f + level.getRandom().nextFloat() * 0.1f);
	}

	/** Called once from SoundFeature so the class loads and every sound gets registered. */
	static void initialize() {
	}
}
