package com.onepiecemod.style;

import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/**
 * A Dojo Scroll: right-click to read it and learn its fighting style on the spot.
 * The scroll is used up (except in Creative). Rob Lucci's boss drops the Rokushiki one.
 */
public class DojoScrollItem extends Item {
	private final FightingStyle style;

	public DojoScrollItem(FightingStyle style, Properties properties) {
		super(properties);
		this.style = style;
	}

	@Override
	public Component getName(ItemStack stack) {
		return Component.literal("Dojo Scroll: " + style.title());
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (player instanceof ServerPlayer serverPlayer) {
			if (StyleAttachments.knows(player, style)) {
				StyleMasters.tell(serverPlayer, "You already know " + style.title() + ". Use /style use " + style.id() + " to switch to it.");
				return InteractionResult.FAIL;
			}
			StyleMasters.teach(serverPlayer, style);
			if (!player.isCreative()) {
				player.getItemInHand(hand).shrink(1);
			}
		}
		return InteractionResult.SUCCESS;
	}
}
