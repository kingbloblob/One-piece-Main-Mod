package com.onepiecemod.sound.client;

import java.util.List;

import net.minecraft.client.Minecraft;
import net.minecraft.core.Holder;
import net.minecraft.sounds.Music;
import net.minecraft.sounds.SoundEvent;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;

import com.onepiecemod.bounty.MarineEntity;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.sea.SeaKingEntity;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.sound.BossMusic;
import com.onepiecemod.sound.ModSounds;

/**
 * Picks the mod's music, a bit like the vanilla music system:
 * - a boss is close by: battle music, looping. Admirals, Warlords, Emperors and the final enemies each have their
 *   own theme (see BossMusic); with several bosses around, the strongest one's theme plays;
 * - a big group of Marines is around (a Navy raid): march music, looping;
 * - a Sea King is close by: its own looming theme, looping;
 * - a boss you were fighting falls: a short victory fanfare;
 * - deep under the sea (swimming or in a submarine, 20+ blocks below sea level): a slow, dark theme, looping;
 * - you're sailing a ship in rain or a storm: the storm theme, looping;
 * - you're sailing a ship: a sea shanty, played once, then a few minutes of quiet (a gentle one at night).
 * While one of these plays, normal Minecraft music is paused. All of it follows the "Music" volume slider.
 * Island themes (music.island.*) come from the biomes. When you arrive on a new island and no music is playing,
 * its theme starts after a few seconds instead of waiting for the vanilla music timer.
 */
public class MusicDirector {
	private static final double BOSS_RANGE = 40;
	private static final double NAVY_RANGE = 40;
	private static final int NAVY_CROWD = 4;
	private static final double SEA_KING_RANGE = 56;
	private static final int DEEP_BELOW_SEA = 20;
	private static final int VICTORY_COOLDOWN_TICKS = 20 * 30;
	private static final int LINGER_TICKS = 120; // keep battle music 6 seconds after the fight is out of sight
	private static final int SAILING_REST_TICKS = 20 * 60 * 3;

	private static MusicTrack current;
	private static Holder<SoundEvent> currentSong;
	private static Holder<SoundEvent> wanted;
	private static int lingerTicks;
	private static int sailingRest;
	private static int sailingSongs;
	private static int trackAge;
	private static final int ISLAND_START_TICKS = 60; // 3 seconds on a new island before its theme starts
	private static Holder<SoundEvent> lastIsland;
	private static int islandWait;
	private static int victoryCooldown;

	public static void initialize() {
		ClientTickEvents.END_CLIENT_TICK.register(MusicDirector::tick);
	}

	private static void tick(Minecraft mc) {
		if (mc.player == null || mc.level == null) {
			stopNow(mc);
			return;
		}
		if (sailingRest > 0) {
			sailingRest--;
		}
		if (victoryCooldown > 0) {
			victoryCooldown--;
		}
		if (mc.level.getGameTime() % 10 == 0) {
			Holder<SoundEvent> battle = battleSong(mc);
			if (battle == null && isBattleSong(currentSong) && victoryCooldown == 0 && bossJustFell(mc)) {
				// The fight is won: cut the battle theme and play the fanfare.
				victoryCooldown = VICTORY_COOLDOWN_TICKS;
				lingerTicks = 0;
				wanted = ModSounds.MUSIC_VICTORY;
			} else if (wanted == ModSounds.MUSIC_VICTORY && battle == null) {
				// Let the fanfare finish.
			} else if (battle != null) {
				wanted = battle;
				lingerTicks = LINGER_TICKS;
			} else if (lingerTicks > 0) {
				lingerTicks -= 10;
			} else {
				wanted = null;
			}
		}

		trackAge++;
		boolean playing = current != null && mc.getSoundManager().isActive(current);
		if (current != null && trackAge > 40 && !playing && !current.isFadingOut() && !current.isLooping()) {
			if (currentSong == ModSounds.MUSIC_VICTORY) {
				wanted = null; // The fanfare is over.
			} else {
				// A sailing song finished on its own: rest for a while.
				sailingRest = SAILING_REST_TICKS;
			}
			current = null;
			currentSong = null;
		}

		Holder<SoundEvent> next = wanted;
		if (next == ModSounds.MUSIC_VICTORY && currentSong != ModSounds.MUSIC_VICTORY && current == null && trackAge > 40) {
			next = null; // Already played and finished.
			wanted = null;
		}
		boolean aboard = ShipEntity.aboard(mc.player) != null;
		if (next == null && deepUnderSea(mc, aboard)) {
			next = ModSounds.MUSIC_DEEP_SEA;
		}
		if (next == null && aboard && (mc.level.isRaining() || mc.level.isThundering())) {
			next = ModSounds.MUSIC_STORM;
		}
		if (next == null && aboard) {
			next = currentSong != null && isSailingSong(currentSong) ? currentSong : (sailingRest == 0 ? sailingSong(mc) : null);
		}

		if (next != currentSong) {
			if (current != null) {
				current.fadeOut();
			}
			current = null;
			currentSong = next;
			if (next != null) {
				current = new MusicTrack(next.value(), !isSailingSong(next) && next != ModSounds.MUSIC_VICTORY);
				trackAge = 0;
				mc.getSoundManager().play(current);
			}
		}
		if (current != null) {
			mc.getMusicManager().stopPlaying(); // our song replaces the normal background music
			islandWait = 0;
		} else {
			startIslandTheme(mc);
		}
	}

	/** Arriving on an island: play its theme soon, unless it is already playing. */
	private static void startIslandTheme(Minecraft mc) {
		Music music = mc.getSituationalMusic();
		Holder<SoundEvent> song = music != null ? music.sound() : null;
		if (song == null || !song.value().location().getPath().startsWith("music.island.")) {
			lastIsland = null;
			islandWait = 0;
			return;
		}
		if (song != lastIsland) {
			lastIsland = song;
			islandWait = ISLAND_START_TICKS;
		}
		if (islandWait > 0 && --islandWait == 0 && !mc.getMusicManager().isPlayingMusic(music)) {
			mc.getMusicManager().stopPlaying();
			mc.getMusicManager().startPlaying(music);
		}
	}

	private static Holder<SoundEvent> battleSong(Minecraft mc) {
		if (mc.player.isSpectator()) {
			return null;
		}
		List<CharacterEntity> bosses = mc.level.getEntitiesOfClass(CharacterEntity.class,
				mc.player.getBoundingBox().inflate(BOSS_RANGE), e -> e.isBoss() && e.isAlive());
		if (!bosses.isEmpty()) {
			BossMusic theme = BossMusic.BOSS;
			for (CharacterEntity boss : bosses) {
				BossMusic own = BossMusic.of(boss);
				if (own.ordinal() > theme.ordinal()) {
					theme = own;
				}
			}
			return theme.song;
		}
		int marines = mc.level.getEntitiesOfClass(MarineEntity.class, mc.player.getBoundingBox().inflate(NAVY_RANGE),
				MarineEntity::isAlive).size();
		if (marines >= NAVY_CROWD) {
			return ModSounds.MUSIC_NAVY;
		}
		boolean seaKing = !mc.level.getEntitiesOfClass(SeaKingEntity.class, mc.player.getBoundingBox().inflate(SEA_KING_RANGE),
				SeaKingEntity::isAlive).isEmpty();
		return seaKing ? ModSounds.MUSIC_SEA_KING : null;
	}

	/** Boss and Sea King themes: the ones a victory fanfare can follow. */
	private static boolean isBattleSong(Holder<SoundEvent> song) {
		if (song == null) {
			return false;
		}
		if (song == ModSounds.MUSIC_SEA_KING) {
			return true;
		}
		for (BossMusic theme : BossMusic.values()) {
			if (theme.song == song) {
				return true;
			}
		}
		return false;
	}

	/** A boss (or a Sea King) nearby is in its death fall right now. */
	private static boolean bossJustFell(Minecraft mc) {
		return !mc.level.getEntitiesOfClass(CharacterEntity.class, mc.player.getBoundingBox().inflate(BOSS_RANGE),
				e -> e.isBoss() && e.isDeadOrDying()).isEmpty()
				|| !mc.level.getEntitiesOfClass(SeaKingEntity.class, mc.player.getBoundingBox().inflate(SEA_KING_RANGE),
						SeaKingEntity::isDeadOrDying).isEmpty();
	}

	/** 20+ blocks under the sea, swimming or in a diving ship. */
	private static boolean deepUnderSea(Minecraft mc, boolean aboard) {
		if (mc.player.isSpectator() || mc.player.getEyeY() > mc.level.getSeaLevel() - DEEP_BELOW_SEA) {
			return false;
		}
		return mc.player.isUnderWater() || (aboard && mc.player.isInWater());
	}

	private static boolean isSailingSong(Holder<SoundEvent> song) {
		return song == ModSounds.MUSIC_NIGHT_SAILING || ModSounds.SAILING_SONGS.contains(song);
	}

	private static Holder<SoundEvent> sailingSong(Minecraft mc) {
		if (mc.level.isDarkOutside()) {
			return ModSounds.MUSIC_NIGHT_SAILING;
		}
		return ModSounds.SAILING_SONGS.get(sailingSongs++ % ModSounds.SAILING_SONGS.size());
	}

	private static void stopNow(Minecraft mc) {
		if (current != null) {
			mc.getSoundManager().stop(current);
		}
		current = null;
		currentSong = null;
		wanted = null;
		lingerTicks = 0;
		lastIsland = null;
		islandWait = 0;
		victoryCooldown = 0;
	}
}
