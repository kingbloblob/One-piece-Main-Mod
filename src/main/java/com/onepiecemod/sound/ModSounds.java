package com.onepiecemod.sound;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;

/**
 * Every sound and song the mod adds. The audio files live in assets/onepiece_sounds/sounds/ and were
 * all generated from scratch by tools/sounds (no samples or copied music, so they're safe to publish).
 *
 * To use one from server code: ModSounds.play(player, ModSounds.CANNON);
 */
public class ModSounds {
	public static final String NAMESPACE = "onepiece_sounds";

	// Haki
	public static final SoundEvent CONQUEROR_BURST = register("haki.conqueror_burst");
	public static final SoundEvent CONQUEROR_AWAKEN = register("haki.conqueror_awaken");
	public static final SoundEvent ARMAMENT_ON = register("haki.armament_on");
	public static final SoundEvent ARMAMENT_HIT = register("haki.armament_hit");
	public static final SoundEvent OBSERVATION_ON = register("haki.observation_on");
	// Den Den Mushi: "Puru puru puru... gacha!"
	public static final SoundEvent DEN_DEN_MUSHI_CALL = register("den_den_mushi.call");
	// Devil Fruits
	public static final SoundEvent FRUIT_EAT = register("devil_fruit.eat");
	public static final SoundEvent FRUIT_AWAKEN = register("devil_fruit.awaken");
	public static final SoundEvent AWAKEN_LOGIA = register("devil_fruit.awaken_logia");
	public static final SoundEvent AWAKEN_ZOAN = register("devil_fruit.awaken_zoan");
	public static final SoundEvent AWAKEN_PARAMECIA = register("devil_fruit.awaken_paramecia");
	// Bounties and the Navy
	public static final SoundEvent BOUNTY_RAISE = register("bounty.raise");
	public static final SoundEvent NEWS_COO = register("bounty.news_coo");
	public static final SoundEvent NAVY_BUGLE = register("navy.bugle");
	public static final SoundEvent CANNON = register("navy.cannon");
	// Bosses, story and quests
	public static final SoundEvent BOSS_DEFEATED = register("boss.defeated");
	public static final SoundEvent STORY_GOAL = register("story.goal");
	public static final SoundEvent STORY_CHAPTER = register("story.chapter");
	public static final SoundEvent QUEST_COMPLETE = register("story.quest_complete");
	// Devil Fruit moves, one per element or kind of power. FruitSounds picks which fruit uses which.
	public static final SoundEvent MOVE_FIRE = register("fruit_move.fire");
	public static final SoundEvent MOVE_MAGMA = register("fruit_move.magma");
	public static final SoundEvent MOVE_ICE = register("fruit_move.ice");
	public static final SoundEvent MOVE_LIGHTNING = register("fruit_move.lightning");
	public static final SoundEvent MOVE_LIGHT = register("fruit_move.light");
	public static final SoundEvent MOVE_DARKNESS = register("fruit_move.darkness");
	public static final SoundEvent MOVE_SMOKE = register("fruit_move.smoke");
	public static final SoundEvent MOVE_SAND = register("fruit_move.sand");
	public static final SoundEvent MOVE_QUAKE = register("fruit_move.quake");
	public static final SoundEvent MOVE_RUBBER = register("fruit_move.rubber");
	public static final SoundEvent MOVE_BLADE = register("fruit_move.blade");
	public static final SoundEvent MOVE_GRAVITY = register("fruit_move.gravity");
	public static final SoundEvent MOVE_PLANT = register("fruit_move.plant");
	public static final SoundEvent MOVE_POISON = register("fruit_move.poison");
	public static final SoundEvent MOVE_EXPLOSION = register("fruit_move.explosion");
	public static final SoundEvent MOVE_BUBBLE = register("fruit_move.bubble");
	public static final SoundEvent MOVE_WARP = register("fruit_move.warp");
	public static final SoundEvent MOVE_STRING = register("fruit_move.string");
	public static final SoundEvent MOVE_CURSE = register("fruit_move.curse");
	public static final SoundEvent MOVE_IMPACT = register("fruit_move.impact");
	public static final SoundEvent MOVE_BEAST_ROAR = register("fruit_move.beast_roar");
	public static final SoundEvent MOVE_DRAGON_ROAR = register("fruit_move.dragon_roar");
	public static final SoundEvent MOVE_BIRD_CRY = register("fruit_move.bird_cry");
	// Each kind of Zoan animal has its own cry.
	public static final SoundEvent MOVE_HOWL = register("fruit_move.howl");
	public static final SoundEvent MOVE_SNARL = register("fruit_move.snarl");
	public static final SoundEvent MOVE_SNAKE = register("fruit_move.snake");
	public static final SoundEvent MOVE_NEIGH = register("fruit_move.neigh");
	public static final SoundEvent MOVE_BELLOW = register("fruit_move.bellow");
	public static final SoundEvent MOVE_TRUMPET = register("fruit_move.trumpet");
	public static final SoundEvent MOVE_SPIDER = register("fruit_move.spider");
	public static final SoundEvent MOVE_STOMP = register("fruit_move.stomp");
	public static final SoundEvent MOVE_DIG = register("fruit_move.dig");
	public static final SoundEvent MOVE_BARRIER = register("fruit_move.barrier");
	public static final SoundEvent MOVE_HUSH = register("fruit_move.hush");
	// Polish pass: fruits that used to borrow another fruit's sound.
	public static final SoundEvent MOVE_SOUND_WAVE = register("fruit_move.sound_wave");
	public static final SoundEvent MOVE_CLOCK = register("fruit_move.clock");
	public static final SoundEvent MOVE_MIRROR = register("fruit_move.mirror");
	public static final SoundEvent MOVE_DOOR = register("fruit_move.door");
	public static final SoundEvent MOVE_HARDEN = register("fruit_move.harden");
	public static final SoundEvent MOVE_SLIP = register("fruit_move.slip");
	public static final SoundEvent MOVE_HEAVY_BLOW = register("fruit_move.heavy_blow");
	public static final SoundEvent MOVE_PHOTON = register("fruit_move.photon");
	// 2026-11-05: fruits that used to share a sound with others got their own (tools/sounds/sfx_unique.py).
	public static final SoundEvent MOVE_WASH = register("fruit_move.wash");
	public static final SoundEvent MOVE_FLOAT = register("fruit_move.float");
	public static final SoundEvent MOVE_HORMONE = register("fruit_move.hormone");
	public static final SoundEvent MOVE_SWIM = register("fruit_move.swim");
	public static final SoundEvent MOVE_SPIN = register("fruit_move.spin");
	public static final SoundEvent MOVE_CRUNCH = register("fruit_move.crunch");
	public static final SoundEvent MOVE_COPY = register("fruit_move.copy");
	public static final SoundEvent MOVE_MEMORY = register("fruit_move.memory");
	public static final SoundEvent MOVE_TOY = register("fruit_move.toy");
	public static final SoundEvent MOVE_LOVE = register("fruit_move.love");
	public static final SoundEvent MOVE_GHOST = register("fruit_move.ghost");
	public static final SoundEvent MOVE_STRAW = register("fruit_move.straw");
	public static final SoundEvent MOVE_ROOM = register("fruit_move.room");
	public static final SoundEvent MOVE_STICKY = register("fruit_move.sticky");
	public static final SoundEvent MOVE_SOUL = register("fruit_move.soul");
	public static final SoundEvent MOVE_GAS = register("fruit_move.gas");
	public static final SoundEvent MOVE_BLOOM = register("fruit_move.bloom");
	public static final SoundEvent MOVE_MAGNET = register("fruit_move.magnet");

	// Music. The client picks battle, raid and sailing music (see sound/client/MusicDirector);
	// each song also has a music disc (see MusicDiscs).
	public static final List<Holder<SoundEvent>> SONGS = new ArrayList<>();
	public static final Holder<SoundEvent> MUSIC_BOSS = song("boss_battle");
	public static final Holder<SoundEvent> MUSIC_EMPEROR = song("emperor_battle");
	public static final Holder<SoundEvent> MUSIC_NAVY = song("justice_marches");
	public static final Holder<SoundEvent> MUSIC_SAILING = song("fair_winds");
	public static final Holder<SoundEvent> MUSIC_ADVENTURE = song("toward_the_grand_line");
	public static final Holder<SoundEvent> MUSIC_JIG = song("drink_to_the_horizon");
	public static final Holder<SoundEvent> MUSIC_ANCHOR = song("haul_the_anchor");
	public static final Holder<SoundEvent> MUSIC_NIGHT_SAILING = song("lantern_on_the_waves");
	public static final Holder<SoundEvent> MUSIC_ADMIRAL = song("admiral_battle");
	public static final Holder<SoundEvent> MUSIC_WARLORD = song("warlord_battle");
	public static final Holder<SoundEvent> MUSIC_FINAL = song("final_battle");
	// 2026-11-05: personal battle themes (see BossMusic).
	public static final Holder<SoundEvent> MUSIC_WHITEBEARD = song("whitebeard_battle");
	public static final Holder<SoundEvent> MUSIC_BIG_MOM = song("big_mom_battle");
	public static final Holder<SoundEvent> MUSIC_KAIDO = song("kaido_battle");
	public static final Holder<SoundEvent> MUSIC_BLACKBEARD = song("blackbeard_battle");
	public static final Holder<SoundEvent> MUSIC_ELDER_STAR = song("elder_star_battle");
	public static final Holder<SoundEvent> MUSIC_SUPERNOVA = song("supernova_battle");
	/** Sailing through rain or a thunderstorm. */
	public static final Holder<SoundEvent> MUSIC_STORM = song("storm_at_sea");
	/** Deep under the sea, swimming or in a submarine. */
	public static final Holder<SoundEvent> MUSIC_DEEP_SEA = song("deep_sea");
	/** A Sea King is close by. */
	public static final Holder<SoundEvent> MUSIC_SEA_KING = song("sea_king");
	/** A short fanfare when a boss falls. Not a song (no disc), but it plays on the Music slider like one. */
	public static final Holder<SoundEvent> MUSIC_VICTORY = Registry.registerForHolder(BuiltInRegistries.SOUND_EVENT,
			Identifier.fromNamespaceAndPath(NAMESPACE, "music_stinger.victory"),
			SoundEvent.createVariableRangeEvent(Identifier.fromNamespaceAndPath(NAMESPACE, "music_stinger.victory")));
	/** Played on long voyages, in turn. The night song replaces them after dark. */
	public static final List<Holder<SoundEvent>> SAILING_SONGS = List.of(MUSIC_SAILING, MUSIC_JIG, MUSIC_ADVENTURE, MUSIC_ANCHOR);

	// Island themes: island biomes use these as their background music (set in each biome's JSON).
	public static final Holder<SoundEvent> ISLAND_WINTER = islandTheme("winter");
	public static final Holder<SoundEvent> ISLAND_DESERT = islandTheme("desert");
	public static final Holder<SoundEvent> ISLAND_WANO = islandTheme("wano");
	public static final Holder<SoundEvent> ISLAND_SKY = islandTheme("sky");
	public static final Holder<SoundEvent> ISLAND_SPOOKY = islandTheme("spooky");
	public static final Holder<SoundEvent> ISLAND_MARINE = islandTheme("marine");
	public static final Holder<SoundEvent> ISLAND_TROPICAL = islandTheme("tropical");
	public static final Holder<SoundEvent> ISLAND_EAST_BLUE = islandTheme("east_blue");
	public static final Holder<SoundEvent> ISLAND_FISHMAN = islandTheme("fishman");
	public static final Holder<SoundEvent> ISLAND_SABAODY = islandTheme("sabaody");
	public static final Holder<SoundEvent> ISLAND_DRESSROSA = islandTheme("dressrosa");
	public static final Holder<SoundEvent> ISLAND_WHOLE_CAKE = islandTheme("whole_cake");
	public static final Holder<SoundEvent> ISLAND_EGGHEAD = islandTheme("egghead");
	public static final Holder<SoundEvent> ISLAND_GIANTS = islandTheme("giants");
	public static final Holder<SoundEvent> ISLAND_JUNGLE = islandTheme("jungle");
	public static final Holder<SoundEvent> ISLAND_PRISON = islandTheme("prison");
	public static final Holder<SoundEvent> ISLAND_HOLY = islandTheme("holy");
	public static final Holder<SoundEvent> ISLAND_ANCIENT = islandTheme("ancient");
	public static final Holder<SoundEvent> ISLAND_NEWKAMA = islandTheme("newkama");
	public static final Holder<SoundEvent> ISLAND_PUNK_HAZARD = islandTheme("punk_hazard");
	public static final Holder<SoundEvent> ISLAND_LOGUETOWN = islandTheme("loguetown");
	public static final Holder<SoundEvent> ISLAND_ENIES_LOBBY = islandTheme("enies_lobby");
	public static final Holder<SoundEvent> ISLAND_ONIGASHIMA = islandTheme("onigashima");
	public static final Holder<SoundEvent> ISLAND_ZOU = islandTheme("zou");
	public static final Holder<SoundEvent> ISLAND_AMAZON_LILY = islandTheme("amazon_lily");
	public static final Holder<SoundEvent> ISLAND_JAYA = islandTheme("jaya");
	public static final Holder<SoundEvent> ISLAND_LITTLE_GARDEN = islandTheme("little_garden");
	public static final Holder<SoundEvent> ISLAND_KURAIGANA = islandTheme("kuraigana");
	public static final Holder<SoundEvent> ISLAND_HACHINOSU = islandTheme("hachinosu");

	static SoundEvent register(String name) {
		Identifier id = Identifier.fromNamespaceAndPath(NAMESPACE, name);
		return Registry.register(BuiltInRegistries.SOUND_EVENT, id, SoundEvent.createVariableRangeEvent(id));
	}

	private static Holder<SoundEvent> song(String name) {
		Identifier id = Identifier.fromNamespaceAndPath(NAMESPACE, "music." + name);
		Holder<SoundEvent> holder = Registry.registerForHolder(BuiltInRegistries.SOUND_EVENT, id, SoundEvent.createVariableRangeEvent(id));
		SONGS.add(holder);
		return holder;
	}

	private static Holder<SoundEvent> islandTheme(String name) {
		Identifier id = Identifier.fromNamespaceAndPath(NAMESPACE, "music.island." + name);
		return Registry.registerForHolder(BuiltInRegistries.SOUND_EVENT, id, SoundEvent.createVariableRangeEvent(id));
	}

	/** Plays a sound at an entity so everyone nearby hears it. Server side only. */
	public static void play(Entity at, SoundEvent sound) {
		play(at, sound, 1.0f);
	}

	public static void play(Entity at, SoundEvent sound, float volume) {
		if (!at.level().isClientSide()) {
			at.level().playSound(null, at.getX(), at.getY(), at.getZ(), sound, SoundSource.PLAYERS, volume, 1.0f);
		}
	}

	/** Called once from SoundFeature so the class loads and every sound gets registered. */
	static void initialize() {
	}
}
