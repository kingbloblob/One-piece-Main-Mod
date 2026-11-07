package com.onepiecemod.furniture;

import net.minecraft.core.BlockPos;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * Furniture you can put things in: cupboards, counters, nightstands, the filing cabinet and the pirate chest.
 * Right-click opens it like a chest. Breaking it drops what is inside (vanilla does that for every
 * block entity that is a Container). Structures that place one get an empty one.
 */
public class StorageFurnitureBlock extends FurnitureBlock implements EntityBlock {
	private final int slots;

	/** @param slots 9 (one row, like a drawer) or 27 (three rows, like a chest) */
	public StorageFurnitureBlock(Properties properties, VoxelShape shape, Mount mount, double seatHeight, boolean solid, int slots) {
		super(properties, shape, mount, seatHeight, solid);
		this.slots = slots;
	}

	public int slots() {
		return slots;
	}

	@Override
	public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new FurnitureStorageBlockEntity(pos, state);
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (level.isClientSide()) {
			return InteractionResult.SUCCESS;
		}
		if (level.getBlockEntity(pos) instanceof FurnitureStorageBlockEntity storage) {
			player.openMenu(storage);
			level.playSound(null, pos, slots > 9 ? SoundEvents.BARREL_OPEN : SoundEvents.CHISELED_BOOKSHELF_PICKUP,
					SoundSource.BLOCKS, 0.5f, level.getRandom().nextFloat() * 0.1f + 0.9f);
		}
		return InteractionResult.SUCCESS;
	}
}
