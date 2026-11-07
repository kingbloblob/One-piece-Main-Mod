package com.onepiecemod.building;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;

/**
 * A building blueprint, the same idea as the Tavern Blueprint.
 * Use it in the air to read the building plan (sneak to hide the ghost blocks again).
 * Use it on the ground to see the building there as see-through ghost blocks: every block
 * that's still missing, including the core block in the middle.
 */
public class BlueprintItem extends Item {
	private final String buildingId;

	public BlueprintItem(String buildingId, Properties properties) {
		super(properties);
		this.buildingId = buildingId;
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (player instanceof ServerPlayer serverPlayer) {
			if (player.isShiftKeyDown()) {
				BuildingOutlines.hide(serverPlayer); // Sneak + use in the air: hide the ghost blocks.
			} else {
				BuildingOutlines.printPlan(serverPlayer, Buildings.get(buildingId));
			}
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public InteractionResult useOn(UseOnContext context) {
		if (context.getPlayer() instanceof ServerPlayer player) {
			Multiblock building = Buildings.get(buildingId);
			BlockPos clicked = context.getClickedPos();
			// Clicking the core itself checks that building; clicking the ground plans one on top of it.
			BlockPos corePos = context.getLevel().getBlockState(clicked).is(building.core()) ? clicked : clicked.above();
			BuildingOutlines.explain(player, building, corePos);
		}
		return InteractionResult.SUCCESS;
	}
}
