package com.onepiecemod.crafting;


import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
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
 * A crafting station. Right-click it to see what it can make and what you still need.
 * Its front faces you when you place it, like a furnace.
 */
public class StationBlock extends HorizontalDirectionalBlock {
	private final Station station;

	public StationBlock(Station station, Properties properties) {
		super(properties);
		this.station = station;
		registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
	}

	public Station station() {
		return station;
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
			StationPayloads.open(serverPlayer, pos, station);
		}
		return InteractionResult.SUCCESS;
	}
}
