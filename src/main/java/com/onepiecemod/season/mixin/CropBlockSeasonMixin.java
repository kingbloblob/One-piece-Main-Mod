package com.onepiecemod.season.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.state.BlockState;

import com.onepiecemod.farm.IslandCropBlock;
import com.onepiecemod.season.Seasons;

/**
 * Seasons for vanilla crops (wheat, carrots, potatoes, beetroot and any mod's CropBlock): winter skips most growth
 * ticks outdoors, spring gives some bonus ones. Island crops handle their own seasons in IslandCropBlock.
 */
@Mixin(CropBlock.class)
public abstract class CropBlockSeasonMixin {
	@Unique
	private static boolean onepiece$bonusTick;

	@Inject(method = "randomTick", at = @At("HEAD"), cancellable = true)
	private void onepiece$seasonSlow(BlockState state, ServerLevel level, BlockPos pos, RandomSource random, CallbackInfo ci) {
		if (onepiece$bonusTick || (Object) this instanceof IslandCropBlock) {
			return;
		}
		float factor = Seasons.growth(level, pos, null);
		if (factor < 1 && random.nextFloat() >= factor) {
			ci.cancel();
		}
	}

	@Inject(method = "randomTick", at = @At("TAIL"))
	private void onepiece$seasonBonus(BlockState state, ServerLevel level, BlockPos pos, RandomSource random, CallbackInfo ci) {
		if (onepiece$bonusTick || (Object) this instanceof IslandCropBlock) {
			return;
		}
		float factor = Seasons.growth(level, pos, null);
		if (factor > 1 && random.nextFloat() < factor - 1) {
			BlockState now = level.getBlockState(pos);
			if (now.getBlock() == (Object) this) {
				onepiece$bonusTick = true;
				try {
					((CropBlockInvoker) this).onepiece$randomTick(now, level, pos, random);
				} finally {
					onepiece$bonusTick = false;
				}
			}
		}
	}
}
