package com.onepiecemod.arena;

import java.util.function.Consumer;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;

/** The two arena items: the Colosseum Ticket and the Davy Back Flag. */
public class ArenaItem {
	/** Use it inside the Corrida Colosseum to pick a cup; anywhere else it says where the Colosseum is. */
	public static class Ticket extends Item {
		public Ticket(Properties properties) {
			super(properties);
		}

		@Override
		public InteractionResult use(Level level, Player player, InteractionHand hand) {
			if (player instanceof ServerPlayer serverPlayer) {
				ArenaFeature.useTicket(serverPlayer);
			}
			return InteractionResult.SUCCESS;
		}

		@Override
		public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> tooltip, TooltipFlag flag) {
			tooltip.accept(Component.literal("Use inside the Corrida Colosseum to enter a cup.").withStyle(ChatFormatting.GRAY));
			tooltip.accept(Component.literal("Rookie 1 ticket, Veteran 2, Champion 3.").withStyle(ChatFormatting.DARK_GRAY));
		}
	}

	/** Plant it on dry ground to challenge a rival crew to a Davy Back Fight. Used up when they accept. */
	public static class Flag extends Item {
		public Flag(Properties properties) {
			super(properties);
		}

		@Override
		public InteractionResult useOn(UseOnContext context) {
			if (context.getPlayer() instanceof ServerPlayer player) {
				if (ArenaFeature.plantFlag(player, context.getClickedPos().above()) && !player.getAbilities().instabuild) {
					context.getItemInHand().shrink(1);
				}
			}
			return InteractionResult.SUCCESS;
		}

		@Override
		public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> tooltip, TooltipFlag flag) {
			tooltip.accept(Component.literal("Plant it on dry ground to challenge a rival crew.").withStyle(ChatFormatting.GRAY));
			tooltip.accept(Component.literal("Each game won takes one of their crew; each game lost costs you one.").withStyle(ChatFormatting.DARK_GRAY));
		}
	}
}
