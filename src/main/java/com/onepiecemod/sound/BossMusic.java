package com.onepiecemod.sound;

import java.util.Set;

import net.minecraft.core.Holder;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.item.Item;

import com.onepiecemod.character.CharacterEntity;

/**
 * Which battle theme a boss fights to, and which music disc it can drop.
 * Admirals, Warlords and the final enemies each get their own theme. Whitebeard, Big Mom, Kaido and Blackbeard
 * (with their top officers), the Five Elders and the Worst Generation rookies have personal themes too.
 * Other top-tier bosses get the Emperor theme and everyone else the normal boss theme.
 */
public enum BossMusic {
	// Listed weakest first: when several bosses are close, the strongest theme wins.
	BOSS(ModSounds.MUSIC_BOSS, MusicDiscs.CLASH_ON_THE_GRAND_LINE),
	SUPERNOVA(ModSounds.MUSIC_SUPERNOVA, MusicDiscs.WORST_GENERATION),
	WARLORD(ModSounds.MUSIC_WARLORD, MusicDiscs.WARLORD_OF_THE_SEA),
	ADMIRAL(ModSounds.MUSIC_ADMIRAL, MusicDiscs.ABSOLUTE_JUSTICE),
	EMPEROR(ModSounds.MUSIC_EMPEROR, MusicDiscs.CLASH_OF_EMPERORS),
	BIG_MOM(ModSounds.MUSIC_BIG_MOM, MusicDiscs.SWEET_TYRANT),
	KAIDO(ModSounds.MUSIC_KAIDO, MusicDiscs.THE_STRONGEST_CREATURE),
	BLACKBEARD(ModSounds.MUSIC_BLACKBEARD, MusicDiscs.DARKNESS_RISING),
	WHITEBEARD(ModSounds.MUSIC_WHITEBEARD, MusicDiscs.FATHER_OF_THE_SEAS),
	ELDER_STAR(ModSounds.MUSIC_ELDER_STAR, MusicDiscs.FIVE_ELDERS),
	FINAL(ModSounds.MUSIC_FINAL, MusicDiscs.DAWN_OF_THE_VOID_CENTURY);

	private static final Set<String> FINAL_BOSSES = Set.of("imu", "xebec");
	/** The Five Elders. */
	private static final Set<String> ELDER_STARS = Set.of("saturn", "mars", "warcury", "nusjuro", "ju_peter");
	/** Emperors with their own theme; their crews' top officers fight to it too. */
	private static final Set<String> WHITEBEARD_CREW = Set.of("whitebeard");
	private static final Set<String> BLACKBEARD_CREW = Set.of("blackbeard");
	private static final Set<String> KAIDO_CREW = Set.of("kaido", "king", "queen");
	private static final Set<String> BIG_MOM_CREW = Set.of("big_mom", "katakuri");
	private static final Set<String> ADMIRALS = Set.of("akainu", "kizaru", "fujitora", "ryokugyu", "aokiji", "garp",
			"sengoku", "kong");
	/** Warlords, and the World Government's strongest agents and jailers. */
	private static final Set<String> WARLORDS = Set.of("mihawk", "crocodile", "doflamingo", "moria", "hancock", "kuma",
			"jinbe", "law", "weevil", "lucci", "magellan", "kaku", "jabra", "spandam");
	/** Rival rookies of the Worst Generation. */
	private static final Set<String> SUPERNOVAS = Set.of("kid", "killer", "hawkins", "drake", "bonney", "apoo",
			"urouge", "bege");

	public final Holder<SoundEvent> song;
	public final Item disc;

	BossMusic(Holder<SoundEvent> song, Item disc) {
		this.song = song;
		this.disc = disc;
	}

	public static BossMusic of(CharacterEntity boss) {
		if (boss.getData() == null) {
			return BOSS;
		}
		return of(boss.getData().id, boss.getData().tier);
	}

	/** The theme for a boss by its character id and tier (5 = Emperor level). */
	public static BossMusic of(String id, int tier) {
		if (FINAL_BOSSES.contains(id)) {
			return FINAL;
		}
		if (ELDER_STARS.contains(id)) {
			return ELDER_STAR;
		}
		if (WHITEBEARD_CREW.contains(id)) {
			return WHITEBEARD;
		}
		if (BLACKBEARD_CREW.contains(id)) {
			return BLACKBEARD;
		}
		if (KAIDO_CREW.contains(id)) {
			return KAIDO;
		}
		if (BIG_MOM_CREW.contains(id)) {
			return BIG_MOM;
		}
		if (ADMIRALS.contains(id)) {
			return ADMIRAL;
		}
		if (WARLORDS.contains(id)) {
			return WARLORD;
		}
		if (SUPERNOVAS.contains(id)) {
			return SUPERNOVA;
		}
		return tier >= 5 ? EMPEROR : BOSS;
	}
}
