package com.onepiecemod.workshop;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Solid cloud from a Milky Dial (a road) or an Eisen Dial (a wall). You can walk on it,
 * and it melts away on its own after half a minute, so it never litters the world.
 */
public class MilkyCloudBlock extends Block {
	/** How long a cloud lasts, in ticks (30 seconds). */
	public static final int LIFETIME = 600;

	public MilkyCloudBlock(Properties properties) {
		super(properties);
	}

	@Override
	protected void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState, boolean movedByPiston) {
		super.onPlace(state, level, pos, oldState, movedByPiston);
		if (!level.isClientSide()) {
			// A little spread so a long road melts bit by bit, not all at once.
			level.scheduleTick(pos, this, LIFETIME + level.getRandom().nextInt(60));
		}
	}

	@Override
	protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
		level.removeBlock(pos, false);
		level.sendParticles(ParticleTypes.CLOUD, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5, 3, 0.3, 0.3, 0.3, 0.01);
	}
}
