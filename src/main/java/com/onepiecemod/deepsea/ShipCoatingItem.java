package com.onepiecemod.deepsea;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;

/** Ship Coating: barrels of Yarukiman resin. Used on a ship, not in the air (see DeepSeaFeature and ShipCoating). */
public class ShipCoatingItem extends Item {
	public ShipCoatingItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (!level.isClientSide()) {
			player.sendOverlayMessage(Component.literal("Board your ship near Sabaody and right-click her with this to coat her for the deep sea.")
					.withStyle(ChatFormatting.AQUA));
		}
		return InteractionResult.PASS;
	}
}
