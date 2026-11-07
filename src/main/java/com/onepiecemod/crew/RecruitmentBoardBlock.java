package com.onepiecemod.crew;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.phys.BlockHitResult;

/**
 * The heart of the Pirate Tavern. Right-click it: if the tavern isn't finished it shows what's
 * missing, otherwise it lists the recruits waiting for each job.
 */
public class RecruitmentBoardBlock extends HorizontalDirectionalBlock {
	public RecruitmentBoardBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
	}

	@Override
	public void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(FACING);
	}

	@Override
	public BlockState getStateForPlacement(BlockPlaceContext context) {
		return defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
	}

	@Override
	public InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (player instanceof ServerPlayer serverPlayer) {
			if (CrewTavern.check((ServerLevel) level, pos).complete()) {
				if (CrewPayloads.hasWindow(serverPlayer)) {
					CrewPayloads.open(serverPlayer);
				} else {
					CrewCommands.showRecruitBoard(serverPlayer);
				}
			} else {
				CrewTavern.explain(serverPlayer, pos);
			}
		}
		return InteractionResult.SUCCESS;
	}
}
