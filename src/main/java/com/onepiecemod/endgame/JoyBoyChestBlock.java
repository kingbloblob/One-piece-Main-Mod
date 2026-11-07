package com.onepiecemod.endgame;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * Joy Boy's Treasure Chest, in two kinds:
 * - treasure=true (the default, placed by the Laugh Tale treasure room and the finale): the final treasure. Sealed until
 *   you finish the story, then each player can open it once per playthrough. Can't be broken.
 * - treasure=false (placed by a player, from the chests Imu and the Roger raid drop): a fancy storage chest with 27 slots
 *   that you can pick up again (its items fall out).
 */
public class JoyBoyChestBlock extends BaseEntityBlock {
	public static final EnumProperty<Direction> FACING = BlockStateProperties.HORIZONTAL_FACING;
	public static final BooleanProperty TREASURE = BooleanProperty.create("treasure");
	private static final VoxelShape SHAPE = Block.box(1, 0, 1, 15, 14, 15);

	public JoyBoyChestBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(TREASURE, true));
	}

	@Override
	public void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(FACING, TREASURE);
	}

	@Override
	public BlockState getStateForPlacement(BlockPlaceContext context) {
		return defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite()).setValue(TREASURE, false);
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
	public VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return SHAPE;
	}

	@Override
	protected float getDestroyProgress(BlockState state, Player player, BlockGetter level, BlockPos pos) {
		return state.getValue(TREASURE) ? 0.0f : super.getDestroyProgress(state, player, level, pos);
	}

	@Override
	public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new JoyBoyChestBlockEntity(pos, state);
	}

	@Override
	public InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (!(player instanceof ServerPlayer serverPlayer)) {
			return InteractionResult.SUCCESS;
		}
		if (state.getValue(TREASURE)) {
			Finale.openTreasure(serverPlayer, pos);
		} else if (level.getBlockEntity(pos) instanceof JoyBoyChestBlockEntity chest) {
			serverPlayer.openMenu(chest);
			level.playSound(null, pos, SoundEvents.CHEST_OPEN, SoundSource.BLOCKS, 0.6f, 0.8f);
		}
		return InteractionResult.SUCCESS;
	}
}
