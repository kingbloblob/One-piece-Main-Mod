package com.onepiecemod.furniture;

import java.util.List;
import java.util.Map;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.ScheduledTickAccess;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.SimpleWaterloggedBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.material.Fluids;
import net.minecraft.world.level.pathfinder.PathComputationType;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * One piece of furniture or a prop: a table, chair, shelf, sack, rug... It turns to face the player,
 * can sit in water, and its shape follows its model.
 *
 * The model is drawn facing north with its back to the south. Wall props (shelves, nets, life rings)
 * hang on the block behind them, ceiling props (ropes) hang from the block above and everything else
 * stands on the block below; each pops off when that block goes. Seats let you sit down with an empty-handed right click.
 */
public class FurnitureBlock extends HorizontalDirectionalBlock implements SimpleWaterloggedBlock {
	public static final BooleanProperty WATERLOGGED = BlockStateProperties.WATERLOGGED;

	public enum Mount { FLOOR, WALL, CEILING }

	private final Map<Direction, VoxelShape> shapes;
	private final Mount mount;
	private final double seatHeight;
	private final boolean solid;
	/** Floor props that reach the bottom of the block stand on something. Beams sit high up and may span gaps. */
	private final boolean needsFloor;

	/**
	 * @param shape      the outline, facing north
	 * @param seatHeight where you sit, in pixels from the bottom (0 = not a seat)
	 * @param solid      false for things you walk through (curtains, nets, rugs keep their thin shape)
	 */
	public FurnitureBlock(Properties properties, VoxelShape shape, Mount mount, double seatHeight, boolean solid) {
		super(properties);
		this.shapes = Shapes.rotateHorizontal(shape);
		this.mount = mount;
		this.seatHeight = seatHeight;
		this.solid = solid;
		this.needsFloor = mount == Mount.FLOOR && !shape.isEmpty() && shape.min(Direction.Axis.Y) <= 0;
		registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(WATERLOGGED, false));
	}

	public boolean isSeat() {
		return seatHeight > 0;
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(FACING, WATERLOGGED);
	}

	@Override
	public BlockState getStateForPlacement(BlockPlaceContext context) {
		boolean water = context.getLevel().getFluidState(context.getClickedPos()).getType() == Fluids.WATER;
		BlockState state = defaultBlockState().setValue(WATERLOGGED, water);
		if (mount == Mount.WALL) {
			// Hang on the wall that was clicked, or else on any wall next to the spot.
			Direction clicked = context.getClickedFace();
			if (clicked.getAxis().isHorizontal()) {
				BlockState onClicked = state.setValue(FACING, clicked);
				if (onClicked.canSurvive(context.getLevel(), context.getClickedPos())) {
					return onClicked;
				}
			}
			for (Direction direction : context.getNearestLookingDirections()) {
				if (direction.getAxis().isHorizontal()) {
					BlockState facing = state.setValue(FACING, direction.getOpposite());
					if (facing.canSurvive(context.getLevel(), context.getClickedPos())) {
						return facing;
					}
				}
			}
			return null;
		}
		BlockState facing = state.setValue(FACING, context.getHorizontalDirection().getOpposite());
		return facing.canSurvive(context.getLevel(), context.getClickedPos()) ? facing : null;
	}

	@Override
	protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
		switch (mount) {
			case WALL: {
				Direction back = state.getValue(FACING).getOpposite();
				BlockPos behind = pos.relative(back);
				return level.getBlockState(behind).isFaceSturdy(level, behind, back.getOpposite());
			}
			case CEILING: {
				BlockPos above = pos.above();
				BlockState up = level.getBlockState(above);
				return up.getBlock() == this || up.isFaceSturdy(level, above, Direction.DOWN)
						|| Block.canSupportCenter(level, above, Direction.DOWN);
			}
			default: {
				if (!needsFloor) {
					return true;
				}
				// Floor props need something under them: a solid top, or anything with a body (slabs, carpets,
				// fences, other furniture), but not air, water, grass or flowers.
				BlockPos below = pos.below();
				BlockState down = level.getBlockState(below);
				return down.getBlock() instanceof FurnitureBlock || down.isFaceSturdy(level, below, Direction.UP)
						|| !down.getCollisionShape(level, below).isEmpty();
			}
		}
	}

	@Override
	protected BlockState updateShape(BlockState state, LevelReader level, ScheduledTickAccess ticks, BlockPos pos, Direction direction,
			BlockPos neighborPos, BlockState neighborState, RandomSource random) {
		if (state.getValue(WATERLOGGED)) {
			ticks.scheduleTick(pos, Fluids.WATER, Fluids.WATER.getTickDelay(level));
		}
		if (!state.canSurvive(level, pos)) {
			return net.minecraft.world.level.block.Blocks.AIR.defaultBlockState();
		}
		return super.updateShape(state, level, ticks, pos, direction, neighborPos, neighborState, random);
	}

	@Override
	protected FluidState getFluidState(BlockState state) {
		return state.getValue(WATERLOGGED) ? Fluids.WATER.getSource(false) : super.getFluidState(state);
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return shapes.get(state.getValue(FACING));
	}

	@Override
	protected VoxelShape getCollisionShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return solid ? shapes.get(state.getValue(FACING)) : Shapes.empty();
	}

	@Override
	protected boolean propagatesSkylightDown(BlockState state) {
		return !state.getValue(WATERLOGGED);
	}

	@Override
	protected boolean isPathfindable(BlockState state, PathComputationType type) {
		return !solid || (type == PathComputationType.WATER && state.getValue(WATERLOGGED));
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (!isSeat() || player.isSecondaryUseActive() || player.isPassenger()) {
			return InteractionResult.PASS;
		}
		if (level.isClientSide()) {
			return InteractionResult.SUCCESS;
		}
		List<SeatEntity> taken = level.getEntitiesOfClass(SeatEntity.class, new AABB(pos));
		if (!taken.isEmpty()) {
			return InteractionResult.PASS;
		}
		SeatEntity seat = new SeatEntity(Furniture.SEAT, level);
		seat.setPos(pos.getX() + 0.5, pos.getY() + seatHeight / 16.0, pos.getZ() + 0.5);
		level.addFreshEntity(seat);
		player.startRiding(seat);
		return InteractionResult.SUCCESS;
	}
}
