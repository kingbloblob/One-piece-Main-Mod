package com.onepiecemod.vegapunk;

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
import net.minecraft.world.level.Level;

/** A cyborg module. Right-click to install it into your body (one tier per module). */
public class CyborgModuleItem extends Item {
	private final CyborgUpgrade upgrade;

	public CyborgModuleItem(Properties properties, CyborgUpgrade upgrade) {
		super(properties);
		this.upgrade = upgrade;
	}

	public CyborgUpgrade upgrade() {
		return upgrade;
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (player instanceof ServerPlayer serverPlayer) {
			return Cyborg.install(serverPlayer, upgrade, player.getItemInHand(hand)) ? InteractionResult.SUCCESS_SERVER : InteractionResult.FAIL;
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> lines, TooltipFlag flag) {
		super.appendHoverText(stack, context, display, lines, flag);
		int installed = Cyborg.clientData.tier(upgrade);
		for (int tier = 1; tier <= CyborgUpgrade.MAX_TIER; tier++) {
			ChatFormatting colour = tier <= installed ? ChatFormatting.GREEN : tier == installed + 1 ? ChatFormatting.WHITE : ChatFormatting.DARK_GRAY;
			lines.accept(Component.literal((tier <= installed ? "✔ " : "  ") + "Tier " + Cyborg.roman(tier) + ": " + upgrade.tiers.get(tier - 1))
					.withStyle(colour));
		}
		if (installed < CyborgUpgrade.MAX_TIER) {
			lines.accept(Component.literal("Right-click to install tier " + Cyborg.roman(installed + 1)
					+ " (uses " + Cyborg.installCost(installed + 1).text() + ")").withStyle(ChatFormatting.AQUA));
		} else {
			lines.accept(Component.literal("Fully installed!").withStyle(ChatFormatting.GOLD));
		}
		if (upgrade == CyborgUpgrade.RADICAL_BEAM || upgrade == CyborgUpgrade.COUP_DE_VENT) {
			lines.accept(Component.literal("Runs on Cola: needs a Cola Engine.").withStyle(ChatFormatting.GRAY));
		}
	}
}
