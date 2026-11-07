package com.onepiecemod.ship;

import java.util.function.Consumer;

import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;

/**
 * The Jolly Roger item.
 * - Right-click the air: opens the paint screen.
 * - Right-click a block: hangs it up as a flag, sail or plaque (whatever you chose in the paint screen).
 */
public class JollyRogerItem extends BlockItem {
	/**
	 * Opens the paint screen. The real screen only exists on the client, so the client part of the mod
	 * fills this in when the game starts. On a dedicated server it stays empty and does nothing.
	 */
	public static Consumer<InteractionHand> openDesigner = hand -> {};

	public JollyRogerItem(Block block, Properties properties) {
		super(block, properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (level.isClientSide()) {
			openDesigner.accept(hand);
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public Component getName(ItemStack stack) {
		FlagDesign design = stack.get(ShipFeature.FLAG_DESIGN);
		if (design == null) {
			return Component.literal("Jolly Roger");
		}
		String style = switch (design.style()) {
			case FlagDesign.STYLE_SAIL -> "Sail";
			case FlagDesign.STYLE_PLAQUE -> "Plaque";
			default -> "Flag";
		};
		return Component.literal("Jolly Roger (" + style + ", " + design.size() + "x" + design.size() + ")");
	}
}
