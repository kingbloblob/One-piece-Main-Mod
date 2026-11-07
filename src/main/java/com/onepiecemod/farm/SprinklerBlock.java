package com.onepiecemod.farm;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * Irrigation. Every few seconds a sprinkler wets the farmland around it and gives the crops there a little
 * extra growth. The copper Sprinkler needs water touching it (a pond, a canal, a water block under it);
 * the Dial Sprinkler keeps its water in a dial shell and reaches further.
 */
public class SprinklerBlock extends BaseEntityBlock {
	private static final VoxelShape SHAPE = Block.box(5, 0, 5, 11, 10, 11);
	public final int radius;
	public final boolean needsWater;

	public SprinklerBlock(Properties properties, int radius, boolean needsWater) {
		super(properties);
		this.radius = radius;
		this.needsWater = needsWater;
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (!level.isClientSide()) {
			boolean wet = !needsWater || SprinklerBlockEntity.hasWater(level, pos);
			int size = radius * 2 + 1;
			player.sendOverlayMessage(Component.literal(wet
					? "Watering a " + size + "x" + size + " patch of farmland around it."
					: "Dry! Put water next to it or under it (a canal or a pond).")
					.withStyle(wet ? ChatFormatting.AQUA : ChatFormatting.RED));
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new SprinklerBlockEntity(pos, state);
	}

	@Override
	public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
		return level.isClientSide() ? null : createTickerHelper(type, FarmBlocks.SPRINKLER_ENTITY, SprinklerBlockEntity::serverTick);
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
