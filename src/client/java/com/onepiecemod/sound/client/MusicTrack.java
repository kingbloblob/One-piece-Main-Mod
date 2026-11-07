package com.onepiecemod.sound.client;

import net.minecraft.client.resources.sounds.AbstractTickableSoundInstance;
import net.minecraft.client.resources.sounds.SoundInstance;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;

/** One song playing "in your head" (not from a spot in the world). It fades in, and fades out when asked. */
public class MusicTrack extends AbstractTickableSoundInstance {
	private static final float FADE_PER_TICK = 0.04f; // about 1.25 seconds

	private boolean fadingOut;

	public MusicTrack(SoundEvent song, boolean loop) {
		super(song, SoundSource.MUSIC, RandomSource.create());
		this.looping = loop;
		this.relative = true;
		this.attenuation = SoundInstance.Attenuation.NONE;
		this.volume = 0.01f;
	}

	public void fadeOut() {
		fadingOut = true;
	}

	public boolean isFadingOut() {
		return fadingOut;
	}

	@Override
	public void tick() {
		if (fadingOut) {
			volume -= FADE_PER_TICK;
			if (volume <= 0) {
				volume = 0;
				stop();
			}
		} else if (volume < 1) {
			volume = Math.min(1, volume + FADE_PER_TICK);
		}
	}
}
