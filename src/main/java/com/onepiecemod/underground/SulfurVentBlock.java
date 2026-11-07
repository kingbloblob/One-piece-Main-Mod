package com.onepiecemod.underground;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.MagmaBlock;
import net.minecraft.world.level.block.state.BlockState;

/** A smoking sulfur vent deep underground. Hot like magma (MagmaBlock burns walkers who don't sneak). */
public class SulfurVentBlock extends MagmaBlock {
	private static final DustParticleOptions SULFUR = new DustParticleOptions(0xe8d23a, 1.2f);

	public SulfurVentBlock(Properties properties) {
		super(properties);
	}

	@Override
	public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
		if (!level.getBlockState(pos.above()).isAir()) {
			return;
		}
		double x = pos.getX() + 0.3 + random.nextDouble() * 0.4;
		double z = pos.getZ() + 0.3 + random.nextDouble() * 0.4;
		if (random.nextInt(3) == 0) {
			level.addParticle(ParticleTypes.LARGE_SMOKE, x, pos.getY() + 1.05, z, 0.0, 0.04, 0.0);
		}
		if (random.nextInt(2) == 0) {
			level.addParticle(SULFUR, x, pos.getY() + 1.1 + random.nextDouble() * 0.6, z, 0.0, 0.03, 0.0);
		}
	}
}
