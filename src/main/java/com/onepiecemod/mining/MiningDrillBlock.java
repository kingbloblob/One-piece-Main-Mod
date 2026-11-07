package com.onepiecemod.mining;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.phys.BlockHitResult;

/**
 * The Mining Drill (Franky would approve). Place it facing the rock you want to dig (it faces away from you, like a
 * piston, so look down to drill a shaft). Then:
 * - right-click with fuel (coal, charcoal, sulfur, blaze rods, coal blocks, electro crystals) to fill it up,
 * - right-click with a drill bit to fit it (Adam, Seastone or Sea Prism: better bits dig faster, further and harder rock),
 * - right-click with an empty hand to see how it is doing, sneak + right-click to switch it on or off.
 * It bores a 3x3 tunnel and drops what it digs into an Ore Cart, chest, barrel or chest minecart right next to it.
 */
public class MiningDrillBlock extends BaseEntityBlock {
	public static final EnumProperty<Direction> FACING = BlockStateProperties.FACING;
	public static final BooleanProperty LIT = BlockStateProperties.LIT;

	public MiningDrillBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(LIT, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(FACING, LIT);
	}

	@Override
	public BlockState getStateForPlacement(BlockPlaceContext context) {
		return defaultBlockState().setValue(FACING, context.getNearestLookingDirection());
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
	protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
			InteractionHand hand, BlockHitResult hit) {
		if (stack.isEmpty() || !(level.getBlockEntity(pos) instanceof MiningDrillBlockEntity drill)) {
			return InteractionResult.TRY_WITH_EMPTY_HAND;
		}
		boolean fuel = MiningDrillBlockEntity.fuelValue(stack) > 0;
		boolean bit = MiningFeature.bitTier(stack) > 0;
		if (!fuel && !bit) {
			return InteractionResult.TRY_WITH_EMPTY_HAND;
		}
		if (player instanceof ServerPlayer sp) {
			if (fuel) {
				drill.addFuel(stack, player.isShiftKeyDown() ? stack.getCount() : 1, player.isCreative());
			} else {
				drill.fitBit(stack, sp);
			}
			sp.sendOverlayMessage(drill.statusLine());
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (player instanceof ServerPlayer sp && level.getBlockEntity(pos) instanceof MiningDrillBlockEntity drill) {
			if (player.isShiftKeyDown()) {
				drill.toggle();
			}
			drill.report(sp);
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new MiningDrillBlockEntity(pos, state);
	}

	@Override
	public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
		return level.isClientSide() ? null : createTickerHelper(type, MiningFeature.DRILL_ENTITY, MiningDrillBlockEntity::serverTick);
	}

	@Override
	public RenderShape getRenderShape(BlockState state) {
		return RenderShape.MODEL;
	}
}
