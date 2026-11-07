package com.onepiecemod.farm;

import java.util.function.Consumer;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.CropBlock;

/** From well-fed ranch animals. Spread it on a crop: every crop in a 5x5 patch grows a step. */
public class ManureItem extends Item {
	public ManureItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult useOn(UseOnContext context) {
		Level level = context.getLevel();
		BlockPos pos = context.getClickedPos();
		if (!(level.getBlockState(pos).getBlock() instanceof CropBlock)) {
			pos = pos.above();
		}
		if (!(level.getBlockState(pos).getBlock() instanceof CropBlock)) {
			return InteractionResult.PASS;
		}
		if (level instanceof ServerLevel server) {
			int grown = 0;
			for (int dx = -2; dx <= 2; dx++) {
				for (int dz = -2; dz <= 2; dz++) {
					for (int dy = -1; dy <= 1; dy++) {
						BlockPos crop = pos.offset(dx, dy, dz);
						if (FarmHelpers.boost(server, crop)) {
							grown++;
							server.sendParticles(ParticleTypes.HAPPY_VILLAGER, crop.getX() + 0.5, crop.getY() + 0.5, crop.getZ() + 0.5,
									3, 0.3, 0.3, 0.3, 0.0);
						}
					}
				}
			}
			if (grown > 0) {
				context.getItemInHand().consume(1, context.getPlayer());
			}
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> lines, TooltipFlag flag) {
		super.appendHoverText(stack, context, display, lines, flag);
		lines.accept(Component.literal("Use on a crop: every crop in a 5x5 patch grows a step.").withStyle(ChatFormatting.GRAY));
	}
}
