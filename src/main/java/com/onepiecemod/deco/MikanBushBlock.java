package com.onepiecemod.deco;

import net.minecraft.core.BlockPos;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.BlockTags;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.InsideBlockEffectApplier;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.SweetBerryBushBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.phys.BlockHitResult;

/**
 * Like a sweet berry bush, but it grows Mikans (Nami's tangerines from Cocoyasi Village) and has no thorns.
 * Right-click a ripe bush to pick them.
 */
public class MikanBushBlock extends SweetBerryBushBlock {
	public MikanBushBlock(Properties properties) {
		super(properties);
	}

	/** Also sits on leaves, so the Cocoyasi Village tangerine grove keeps its bushes. */
	@Override
	protected boolean mayPlaceOn(BlockState state, BlockGetter level, BlockPos pos) {
		return super.mayPlaceOn(state, level, pos) || state.is(BlockTags.LEAVES);
	}

	@Override
	protected ItemStack getCloneItemStack(LevelReader level, BlockPos pos, BlockState state, boolean includeData) {
		return new ItemStack(DecoItems.MIKAN);
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hitResult) {
		int age = state.getValue(AGE);
		if (age < 2) {
			return super.useWithoutItem(state, level, pos, player, hitResult);
		}
		int count = 1 + level.getRandom().nextInt(2) + (age == MAX_AGE ? 1 : 0);
		popResource(level, pos, new ItemStack(DecoItems.MIKAN, count));
		level.playSound(null, pos, SoundEvents.SWEET_BERRY_BUSH_PICK_BERRIES, SoundSource.BLOCKS, 1.0f, 0.8f + level.getRandom().nextFloat() * 0.4f);
		BlockState picked = state.setValue(AGE, 1);
		level.setBlock(pos, picked, 2);
		level.gameEvent(GameEvent.BLOCK_CHANGE, pos, GameEvent.Context.of(player, picked));
		return InteractionResult.SUCCESS;
	}

	@Override
	protected void entityInside(BlockState state, Level level, BlockPos pos, Entity entity, InsideBlockEffectApplier effectApplier, boolean isPrecise) {
		// No thorns: walking through a mikan bush doesn't hurt.
	}
}
