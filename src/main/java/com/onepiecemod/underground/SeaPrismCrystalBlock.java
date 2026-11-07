package com.onepiecemod.underground;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.AmethystClusterBlock;
import net.minecraft.world.level.block.state.BlockState;

/** A glowing Sea Prism crystal cluster. Grows on any side of a block like amethyst, and sheds a faint blue shimmer. */
public class SeaPrismCrystalBlock extends AmethystClusterBlock {
	private static final DustParticleOptions SHIMMER = new DustParticleOptions(0x7fe3ff, 0.6f);

	public SeaPrismCrystalBlock(float height, float aabbOffset, Properties properties) {
		super(height, aabbOffset, properties);
	}

	@Override
	public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
		if (random.nextInt(6) == 0) {
			level.addParticle(SHIMMER, pos.getX() + random.nextDouble(), pos.getY() + random.nextDouble(),
					pos.getZ() + random.nextDouble(), 0.0, 0.01, 0.0);
		}
	}
}
