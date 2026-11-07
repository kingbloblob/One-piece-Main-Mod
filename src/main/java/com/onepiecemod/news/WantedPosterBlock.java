package com.onepiecemod.news;

import java.util.Map;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.ScheduledTickAccess;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * A Wanted Poster pinned to a wall. It always shows a pirate's CURRENT bounty: the face, name,
 * bounty and race are drawn in front of it and update by themselves.
 *
 * Right-click: read the poster. Sneak + right-click: pin up a different pirate's poster instead.
 * Towns and Marine bases put these up on their own (see PosterPlacer).
 */
public class WantedPosterBlock extends BaseEntityBlock {
	public static final net.minecraft.world.level.block.state.properties.EnumProperty<Direction> FACING = HorizontalDirectionalBlock.FACING;

	private static final Map<Direction, VoxelShape> SHAPES = Map.of(
			Direction.NORTH, Block.box(0, 0, 15, 16, 16, 16),
			Direction.SOUTH, Block.box(0, 0, 0, 16, 16, 1),
			Direction.EAST, Block.box(0, 0, 0, 1, 16, 16),
			Direction.WEST, Block.box(15, 0, 0, 16, 16, 16));

	public WantedPosterBlock(Properties properties) {
		super(properties);
		registerDefaultState(this.stateDefinition.any().setValue(FACING, Direction.NORTH));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(FACING);
	}

	@Override
	public BlockState getStateForPlacement(BlockPlaceContext context) {
		Direction face = context.getClickedFace();
		if (face.getAxis().isVertical()) {
			// Clicked a floor or ceiling: stick it to a wall the player is facing instead.
			face = context.getHorizontalDirection().getOpposite();
		}
		BlockState state = defaultBlockState().setValue(FACING, face);
		return canSurvive(state, context.getLevel(), context.getClickedPos()) ? state : null;
	}

	/** A new poster next to others shows the next pirate on the list, so a notice board isn't all the same face. */
	@Override
	public void setPlacedBy(Level level, BlockPos pos, BlockState state, LivingEntity placer, ItemStack stack) {
		super.setPlacedBy(level, pos, state, placer, stack);
		if (level.isClientSide() || !(level.getBlockEntity(pos) instanceof WantedPosterBlockEntity poster)) {
			return;
		}
		int nearby = 0;
		for (BlockPos other : BlockPos.betweenClosed(pos.offset(-6, -3, -6), pos.offset(6, 3, 6))) {
			if (!other.equals(pos) && level.getBlockState(other).is(this)) {
				nearby++;
			}
		}
		poster.setSlot(nearby);
	}

	@Override
	protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
		Direction facing = state.getValue(FACING);
		BlockPos wall = pos.relative(facing.getOpposite());
		return level.getBlockState(wall).isFaceSturdy(level, wall, facing);
	}

	@Override
	protected BlockState updateShape(BlockState state, LevelReader level, ScheduledTickAccess ticks, BlockPos pos, Direction direction,
			BlockPos neighborPos, BlockState neighborState, RandomSource random) {
		if (direction == state.getValue(FACING).getOpposite() && !canSurvive(state, level, pos)) {
			return Blocks.AIR.defaultBlockState();
		}
		return super.updateShape(state, level, ticks, pos, direction, neighborPos, neighborState, random);
	}

	@Override
	protected BlockState rotate(BlockState state, Rotation rotation) {
		return state.setValue(FACING, rotation.rotate(state.getValue(FACING)));
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return SHAPES.get(state.getValue(FACING));
	}

	@Override
	protected VoxelShape getCollisionShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return net.minecraft.world.phys.shapes.Shapes.empty();
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (player instanceof ServerPlayer serverPlayer && level.getBlockEntity(pos) instanceof WantedPosterBlockEntity poster) {
			if (player.isShiftKeyDown()) {
				poster.nextPirate(serverPlayer);
			} else {
				poster.read(serverPlayer);
			}
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new WantedPosterBlockEntity(pos, state);
	}

	@Override
	public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
		if (level.isClientSide()) {
			return null;
		}
		return createTickerHelper(type, NewsFeature.WANTED_POSTER_ENTITY, WantedPosterBlockEntity::serverTick);
	}

	@Override
	protected RenderShape getRenderShape(BlockState state) {
		return RenderShape.MODEL;
	}
}
