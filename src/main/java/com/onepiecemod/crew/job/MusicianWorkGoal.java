package com.onepiecemod.crew.job;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;

import com.onepiecemod.anim.Anim;
import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.crew.CrewmateEntity;

/**
 * The musician's job (like Brook). The musician plays songs at their post:
 * 1. Every 3 seconds they play a few notes (you can hear them and see music notes).
 * 2. The music helps nearby crops grow: each song, each growing crop has a 1 in 4 chance to grow a stage.
 * 3. Young animals nearby grow up faster too.
 */
public class MusicianWorkGoal extends WorkGoal {
	// A short tune, as note block pitches (1.0 is the middle note). Played one note per song, in a loop.
	private static final float[] SONG = {1.0f, 1.19f, 1.33f, 1.5f, 1.33f, 1.19f, 1.0f, 0.89f};

	private int seconds;
	private int note;

	public MusicianWorkGoal(CrewmateEntity musician) {
		super(musician, CrewRole.MUSICIAN);
	}

	@Override
	protected void workTick(ServerLevel level, BlockPos post) {
		seconds++;
		if (seconds % 3 != 0) {
			return;
		}

		// Play the next notes of the tune.
		for (int i = 0; i < 2; i++) {
			float pitch = SONG[note];
			note = (note + 1) % SONG.length;
			level.playSound(null, worker.blockPosition(), SoundEvents.NOTE_BLOCK_HARP.value(), SoundSource.RECORDS, 1.0f, pitch);
		}
		level.sendParticles(ParticleTypes.NOTE, worker.getX(), worker.getY() + 2.2, worker.getZ(), 3, 0.5, 0.3, 0.5, 1.0);

		// Crops love music.
		List<BlockPos> crops = new ArrayList<>();
		for (BlockPos pos : BlockPos.betweenClosed(post.offset(-RANGE, -3, -RANGE), post.offset(RANGE, 3, RANGE))) {
			BlockState state = level.getBlockState(pos);
			if (state.getBlock() instanceof CropBlock crop && !crop.isMaxAge(state)) {
				crops.add(pos.immutable());
			}
		}
		for (BlockPos pos : crops) {
			if (level.getRandom().nextInt(4) == 0) {
				BlockState state = level.getBlockState(pos);
				if (state.getBlock() instanceof CropBlock crop) {
					level.setBlock(pos, crop.getStateForAge(Math.min(crop.getMaxAge(), currentAge(crop, state) + 1)), 2);
				}
			}
		}

		// So do baby animals.
		for (Animal animal : level.getEntitiesOfClass(Animal.class, new AABB(post).inflate(RANGE), Animal::isBaby)) {
			animal.ageUp(10); // 10 seconds closer to growing up.
		}
	}

	// Works out a crop's age by checking which stage matches its current look.
	private static int currentAge(CropBlock crop, BlockState state) {
		for (int age = 0; age <= crop.getMaxAge(); age++) {
			if (crop.getStateForAge(age).equals(state)) {
				return age;
			}
		}
		return crop.getMaxAge();
	}

	// Stay at the post so the music reaches the farm.
	@Override
	protected BlockPos findTarget(ServerLevel level, BlockPos post) {
		return awayFromPost(post) ? post : null;
	}

	// Conducting the tune.
	@Override
	protected Anim workAnim() {
		return Anim.POINT;
	}

	@Override
	protected void act(ServerLevel level, BlockPos pos) {
		// Back at the post.
	}
}
