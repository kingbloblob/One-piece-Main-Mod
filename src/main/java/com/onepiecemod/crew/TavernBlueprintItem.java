package com.onepiecemod.crew;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;

/**
 * The Tavern Blueprint. Use it in the air to read the building plan.
 * Use it on the ground to see the tavern's outline there: flames show every block that's
 * still missing, and green sparkles show where the Recruitment Board goes.
 */
public class TavernBlueprintItem extends Item {
	public TavernBlueprintItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (player instanceof ServerPlayer serverPlayer) {
			if (player.isShiftKeyDown()) {
				com.onepiecemod.building.BuildingOutlines.hide(serverPlayer); // Sneak + use in the air: hide the ghost blocks.
			} else {
				CrewTavern.printPlan(serverPlayer);
			}
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public InteractionResult useOn(UseOnContext context) {
		if (context.getPlayer() instanceof ServerPlayer player) {
			BlockPos clicked = context.getClickedPos();
			// Clicking the board itself checks that tavern; clicking the ground plans one on top of it.
			BlockPos boardPos = context.getLevel().getBlockState(clicked).is(CrewBlocks.RECRUITMENT_BOARD) ? clicked : clicked.above();
			CrewTavern.explain(player, boardPos);
		}
		return InteractionResult.SUCCESS;
	}
}
