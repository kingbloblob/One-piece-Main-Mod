package com.onepiecemod.ship;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * The Cannon: a full-size ship cannon on a wheeled carriage, about 2-3 blocks long.
 *  - Placed by a player (mounted=false): the block is the carriage and the barrel reaches a block out in front.
 *  - In a gunport (mounted=true, used by the ship templates): the block sits in the hull wall as a dark gunport,
 *    the barrel sticks out over the sea and the carriage stands on the deck behind it. The block is then a full
 *    block, so the hull stays watertight (ShipHold).
 * Models: models/block/cannon.json and cannon_mounted.json (tools/shipcombat/gen_cannon_model.py).
 */
public class CannonBlock extends DecorBlock {
	public static final BooleanProperty MOUNTED = BooleanProperty.create("mounted");
	private static final VoxelShape FREE = Block.box(1, 0, 1, 15, 14, 15);

	public CannonBlock(Properties properties) {
		super(properties, FREE);
		registerDefaultState(defaultBlockState().setValue(MOUNTED, false));
	}

	@Override
	public void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		super.createBlockStateDefinition(builder);
		builder.add(MOUNTED);
	}

	@Override
	public VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return state.getValue(MOUNTED) ? Shapes.block() : FREE;
	}
}
