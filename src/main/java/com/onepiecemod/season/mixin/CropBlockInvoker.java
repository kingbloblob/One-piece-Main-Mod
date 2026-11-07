package com.onepiecemod.season.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Invoker;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.state.BlockState;

/** Lets the season mixin give a crop a bonus growth tick in spring. */
@Mixin(CropBlock.class)
public interface CropBlockInvoker {
	@Invoker("randomTick")
	void onepiece$randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random);
}
