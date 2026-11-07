package com.onepiecemod.furnish;

import java.util.EnumMap;
import java.util.Map;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.ScheduledTickAccess;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * A small fixture that must hang on something: a wall lamp or flower box on a wall, a chandelier under a ceiling,
 * a candelabra on a table or floor. It pops off when what holds it is broken, so builds never show floating lights.
 * All of them face a horizontal direction (for wall fixtures: away from the wall).
 */
public class FixtureBlock extends Block {
	public static final EnumProperty<Direction> FACING = HorizontalDirectionalBlock.FACING;

	public enum Mount { WALL, CEILING, FLOOR }

	private final Mount mount;
	private final Map<Direction, VoxelShape> shapes = new EnumMap<>(Direction.class);

	/** box = the shape for a fixture facing north (a wall fixture's wall is then to the south, z = 16). */
	public FixtureBlock(Properties properties, Mount mount, double x0, double y0, double z0, double x1, double y1, double z1) {
		super(properties);
		this.mount = mount;
		shapes.put(Direction.NORTH, Block.box(x0, y0, z0, x1, y1, z1));
		shapes.put(Direction.SOUTH, Block.box(16 - x1, y0, 16 - z1, 16 - x0, y1, 16 - z0));
		shapes.put(Direction.EAST, Block.box(16 - z1, y0, x0, 16 - z0, y1, x1));
		shapes.put(Direction.WEST, Block.box(z0, y0, 16 - x1, z1, y1, 16 - x0));
		registerDefaultState(this.stateDefinition.any().setValue(FACING, Direction.NORTH));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(FACING);
	}

	@Override
	public BlockState getStateForPlacement(BlockPlaceContext context) {
		Direction face = context.getClickedFace();
		Direction facing = mount == Mount.WALL && face.getAxis().isHorizontal() ? face : context.getHorizontalDirection().getOpposite();
		BlockState state = defaultBlockState().setValue(FACING, facing);
		if (mount == Mount.WALL && !canSurvive(state, context.getLevel(), context.getClickedPos())) {
			// Clicked a floor: try the wall the player is looking at.
			state = state.setValue(FACING, context.getHorizontalDirection().getOpposite());
		}
		return canSurvive(state, context.getLevel(), context.getClickedPos()) ? state : null;
	}

	@Override
	protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
		return switch (mount) {
			case WALL -> {
				Direction facing = state.getValue(FACING);
				BlockPos wall = pos.relative(facing.getOpposite());
				yield level.getBlockState(wall).isFaceSturdy(level, wall, facing);
			}
			case CEILING -> Block.canSupportCenter(level, pos.above(), Direction.DOWN) || level.getBlockState(pos.above()).is(Blocks.IRON_CHAIN);
			case FLOOR -> Block.canSupportCenter(level, pos.below(), Direction.UP);
		};
	}

	private Direction supportSide(BlockState state) {
		return switch (mount) {
			case WALL -> state.getValue(FACING).getOpposite();
			case CEILING -> Direction.UP;
			case FLOOR -> Direction.DOWN;
		};
	}

	@Override
	protected BlockState updateShape(BlockState state, LevelReader level, ScheduledTickAccess ticks, BlockPos pos, Direction direction,
			BlockPos neighborPos, BlockState neighborState, RandomSource random) {
		if (direction == supportSide(state) && !canSurvive(state, level, pos)) {
			return Blocks.AIR.defaultBlockState();
		}
		return super.updateShape(state, level, ticks, pos, direction, neighborPos, neighborState, random);
	}

	@Override
	protected BlockState rotate(BlockState state, Rotation rotation) {
		return state.setValue(FACING, rotation.rotate(state.getValue(FACING)));
	}

	@Override
	protected BlockState mirror(BlockState state, Mirror mirror) {
		return state.rotate(mirror.getRotation(state.getValue(FACING)));
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return shapes.get(state.getValue(FACING));
	}

	@Override
	protected VoxelShape getCollisionShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return mount == Mount.FLOOR ? shapes.get(state.getValue(FACING)) : Shapes.empty();
	}
}
