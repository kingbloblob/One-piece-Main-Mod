package com.onepiecemod.farm;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/** The sprinkler's timer. See SprinklerBlock. */
public class SprinklerBlockEntity extends BlockEntity {
	/** How often it sprays, in ticks. */
	public static final int INTERVAL = 100;
	/** Chance per spray that each growing crop gets one extra growth step (about 2x faster farming overall). */
	public static final int BOOST_ONE_IN = 48;

	public SprinklerBlockEntity(BlockPos pos, BlockState state) {
		super(FarmBlocks.SPRINKLER_ENTITY, pos, state);
	}

	public static boolean hasWater(Level level, BlockPos pos) {
		for (Direction direction : Direction.values()) {
			if (direction != Direction.UP && level.getFluidState(pos.relative(direction)).is(FluidTags.WATER)) {
				return true;
			}
		}
		return level.getFluidState(pos.below(2)).is(FluidTags.WATER);
	}

	public static void serverTick(Level level, BlockPos pos, BlockState state, SprinklerBlockEntity sprinkler) {
		if (!(level instanceof ServerLevel server) || !(state.getBlock() instanceof SprinklerBlock block)) {
			return;
		}
		// Spread the sprinklers out so a big farm doesn't do them all on the same tick.
		if ((level.getGameTime() + pos.asLong()) % INTERVAL != 0) {
			return;
		}
		if (block.needsWater && !hasWater(level, pos)) {
			return;
		}
		spray(server, pos, block.radius);
	}

	static void spray(ServerLevel level, BlockPos center, int radius) {
		BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
		for (int dx = -radius; dx <= radius; dx++) {
			for (int dz = -radius; dz <= radius; dz++) {
				for (int dy = -2; dy <= 1; dy++) {
					p.set(center.getX() + dx, center.getY() + dy, center.getZ() + dz);
					if (FarmHelpers.water(level, p)) {
						BlockPos crop = p.above();
						if (level.getRandom().nextInt(BOOST_ONE_IN) == 0) {
							FarmHelpers.boost(level, crop);
						}
						if (level.getRandom().nextInt(6) == 0) {
							level.sendParticles(ParticleTypes.SPLASH, crop.getX() + 0.5, crop.getY() + 0.3, crop.getZ() + 0.5,
									3, 0.3, 0.1, 0.3, 0.0);
						}
					}
				}
			}
		}
		level.sendParticles(ParticleTypes.FALLING_WATER, center.getX() + 0.5, center.getY() + 0.9, center.getZ() + 0.5,
				8, 0.6, 0.1, 0.6, 0.0);
	}
}
