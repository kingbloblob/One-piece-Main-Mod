package com.onepiecemod.farm;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/**
 * A wooden cabinet of seed drawers. Right-click with an island seed to bank that kind (it keeps one);
 * right-click with an empty hand to see your catalog and draw one free seed of each banked kind a day.
 * See SeedVault for the catalog and rewards.
 */
public class SeedVaultBlock extends Block {
	public SeedVaultBlock(Properties properties) {
		super(properties);
	}

	@Override
	protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
			InteractionHand hand, BlockHitResult hit) {
		IslandCrop crop = FarmItems.cropOfSeed(stack);
		if (crop == null) {
			return InteractionResult.TRY_WITH_EMPTY_HAND;
		}
		if (player instanceof ServerPlayer serverPlayer) {
			SeedVault.bank(serverPlayer, crop, stack);
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (player instanceof ServerPlayer serverPlayer) {
			SeedVault.showCatalog(serverPlayer);
		}
		return InteractionResult.SUCCESS;
	}
}
