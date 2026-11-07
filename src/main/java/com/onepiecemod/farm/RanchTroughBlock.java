package com.onepiecemod.farm;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * A feed trough for a ranch. Fill it with fodder (wheat, hay, carrots, island crops...). Grown animals
 * within 8 blocks eat from it: now and then each one leaves milk, eggs, wool, truffles or manure (into
 * a chest under or beside the trough if there is one), and well-fed farm animals breed on their own.
 */
public class RanchTroughBlock extends BaseEntityBlock {
	public static final BooleanProperty FULL = BooleanProperty.create("full");
	private static final VoxelShape SHAPE = Block.box(0, 0, 0, 16, 8, 16);

	public RanchTroughBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(FULL, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(FULL);
	}

	@Override
	protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
			InteractionHand hand, BlockHitResult hit) {
		if (!stack.is(Ranching.FODDER)) {
			return InteractionResult.TRY_WITH_EMPTY_HAND;
		}
		if (!level.isClientSide() && level.getBlockEntity(pos) instanceof RanchTroughBlockEntity trough) {
			int each = stack.is(Items.HAY_BLOCK) ? 9 : 1;
			int room = (RanchTroughBlockEntity.MAX_FODDER - trough.fodder()) / each;
			int used = Math.min(room, player.isShiftKeyDown() ? stack.getCount() : 1);
			if (used <= 0) {
				player.sendOverlayMessage(Component.literal("The trough is full.").withStyle(ChatFormatting.YELLOW));
				return InteractionResult.SUCCESS;
			}
			trough.addFodder(used * each);
			stack.consume(used, player);
			level.playSound(null, pos, SoundEvents.COMPOSTER_FILL, SoundSource.BLOCKS, 1.0f, 1.0f);
			player.sendOverlayMessage(Component.literal("Fodder: " + trough.fodder() + "/" + RanchTroughBlockEntity.MAX_FODDER)
					.withStyle(ChatFormatting.GREEN));
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (!level.isClientSide() && level.getBlockEntity(pos) instanceof RanchTroughBlockEntity trough) {
			int animals = trough.countAnimals();
			player.sendSystemMessage(Component.literal("Ranch Trough: " + trough.fodder() + "/" + RanchTroughBlockEntity.MAX_FODDER
					+ " fodder, " + animals + " animal" + (animals == 1 ? "" : "s") + " eating here.").withStyle(ChatFormatting.GOLD));
			player.sendSystemMessage(Component.literal("Use fodder on it (sneak to pour the whole stack). Put a chest under or beside it to collect.")
					.withStyle(ChatFormatting.GRAY));
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new RanchTroughBlockEntity(pos, state);
	}

	@Override
	public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
		return level.isClientSide() ? null : createTickerHelper(type, FarmBlocks.TROUGH_ENTITY, RanchTroughBlockEntity::serverTick);
	}

	@Override
	protected RenderShape getRenderShape(BlockState state) {
		return RenderShape.MODEL;
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return SHAPE;
	}
}
