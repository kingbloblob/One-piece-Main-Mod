package com.onepiecemod.sound;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.item.Item;

import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;

import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.item.ModItems;

/**
 * Sounds and music. Registers every sound, the music discs, and plays a victory fanfare when a boss falls.
 * Other features play these sounds with one line each, e.g. ModSounds.play(player, ModSounds.CANNON).
 * Battle, raid and sailing music are picked on the client (sound/client/MusicDirector).
 */
public class SoundFeature {
	/** Chance that a beaten boss drops a music disc. */
	private static final float DISC_CHANCE = 0.12f;

	public static void initialize() {
		ModSounds.initialize();
		BossSounds.initialize();
		StyleSounds.initialize();
		FruitSounds.initialize();
		WorldSounds.initialize();
		MusicDiscs.initialize();

		CreativeModeTabEvents.modifyOutputEvent(ModItems.ONE_PIECE_TAB_KEY).register(output -> {
			for (Item disc : MusicDiscs.ALL) {
				output.accept(disc);
			}
		});

		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (entity.level() instanceof ServerLevel level && entity instanceof com.onepiecemod.sea.SeaKingEntity
					&& level.getRandom().nextFloat() < DISC_CHANCE) {
				entity.spawnAtLocation(level, MusicDiscs.SOMETHING_BENEATH_THE_WAVES);
				return;
			}
			if (!(entity.level() instanceof ServerLevel level) || !(entity instanceof CharacterEntity boss) || !boss.isBoss()) {
				return;
			}
			level.playSound(null, entity.getX(), entity.getY(), entity.getZ(), ModSounds.BOSS_DEFEATED, SoundSource.PLAYERS, 3.0f, 1.0f);
			if (level.getRandom().nextFloat() < DISC_CHANCE) {
				// Admirals, Warlords, Emperors and the final enemies drop their own battle theme; everyone else a random song.
				BossMusic theme = BossMusic.of(boss);
				Item disc = theme != BossMusic.BOSS ? theme.disc
						: MusicDiscs.ALL.get(level.getRandom().nextInt(MusicDiscs.ALL.size()));
				boss.spawnAtLocation(level, disc);
			}
		});
	}
}
