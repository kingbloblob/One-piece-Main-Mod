package com.onepiecemod.ship;


import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * A decoration for your ship: figureheads, cannons, anchors and so on. They don't do anything,
 * they just look good. The look of each one is in assets/onepiece/models/block/<name>.json.
 *
 * Each one faces the way you look when you place it, so stand on deck facing the sea to put a figurehead on the bow.
 */
public class DecorBlock extends HorizontalDirectionalBlock {
	private final VoxelShape shape;

	public DecorBlock(Properties properties) {
		this(properties, Block.box(0, 0, 0, 16, 16, 16));
	}

	public DecorBlock(Properties properties, VoxelShape shape) {
		super(properties);
		this.shape = shape;
		registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
	}

	@Override
	public void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(FACING);
	}

	@Override
	public BlockState getStateForPlacement(BlockPlaceContext context) {
		return defaultBlockState().setValue(FACING, context.getHorizontalDirection());
	}

	@Override
	public VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return shape;
	}
}
