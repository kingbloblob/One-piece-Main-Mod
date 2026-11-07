package com.onepiecemod.farm;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.FarmlandBlock;
import net.minecraft.world.level.block.state.BlockState;

/** Small shared bits: watering farmland and giving a crop an extra bit of growth. */
final class FarmHelpers {
	private FarmHelpers() {
	}

	/** Makes farmland fully wet. Returns true if it was farmland. */
	static boolean water(ServerLevel level, BlockPos pos) {
		BlockState state = level.getBlockState(pos);
		if (state.getBlock() instanceof FarmlandBlock && state.hasProperty(FarmlandBlock.MOISTURE)) {
			if (state.getValue(FarmlandBlock.MOISTURE) < FarmlandBlock.MAX_MOISTURE) {
				level.setBlock(pos, state.setValue(FarmlandBlock.MOISTURE, FarmlandBlock.MAX_MOISTURE), Block.UPDATE_CLIENTS);
			}
			return true;
		}
		return false;
	}

	/** One extra growth step for a crop that isn't grown yet (island crops: one stage; others: a random tick). */
	static boolean boost(ServerLevel level, BlockPos pos) {
		BlockState state = level.getBlockState(pos);
		if (state.getBlock() instanceof CropBlock crop && !crop.isMaxAge(state)) {
			if (crop instanceof IslandCropBlock) {
				crop.growCrops(level, pos, state);
			} else {
				state.randomTick(level, pos, level.getRandom());
			}
			return true;
		}
		return false;
	}
}
