package com.onepiecemod.treasure;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/**
 * X marks the spot: a patch of freshly dug earth with a red X scratched into it. Treasure maps lead here, and the
 * chest is buried right under it. Drops nothing when dug up.
 */
public class DigSpotBlock extends Block {
	public DigSpotBlock(Properties properties) {
		super(properties);
	}

	@Override
	public BlockState playerWillDestroy(Level level, BlockPos pos, BlockState state, Player player) {
		if (!level.isClientSide()) {
			player.sendOverlayMessage(Component.literal("Your shovel scrapes on wood. Something is buried here!"));
			level.playSound(null, pos, SoundEvents.CHEST_LOCKED, SoundSource.BLOCKS, 0.8f, 0.7f);
		}
		return super.playerWillDestroy(level, pos, state, player);
	}
}
