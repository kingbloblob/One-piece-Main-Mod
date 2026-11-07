package com.onepiecemod.farm;

import java.util.function.Consumer;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;

/**
 * Right-click water to fill it, right-click a crop or farmland to water a 3x3 patch: the soil gets wet
 * and each crop has a good chance of growing a step. The durability bar is how much water is left.
 */
public class WateringCanItem extends Item {
	public static final int CAPACITY = 40;

	public WateringCanItem(Properties properties) {
		super(properties);
	}

	private static int water(ItemStack stack) {
		return CAPACITY - 1 - stack.getDamageValue();
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		ItemStack stack = player.getItemInHand(hand);
		BlockHitResult hit = getPlayerPOVHitResult(level, player, ClipContext.Fluid.SOURCE_ONLY);
		if (hit.getType() == HitResult.Type.BLOCK && level.getFluidState(hit.getBlockPos()).is(FluidTags.WATER)) {
			if (!level.isClientSide()) {
				stack.setDamageValue(0);
				level.playSound(null, player.blockPosition(), SoundEvents.BUCKET_FILL, SoundSource.PLAYERS, 1.0f, 1.2f);
				player.sendOverlayMessage(Component.literal("Watering Can filled.").withStyle(ChatFormatting.AQUA));
			}
			return InteractionResult.SUCCESS;
		}
		return InteractionResult.PASS;
	}

	@Override
	public InteractionResult useOn(UseOnContext context) {
		Level level = context.getLevel();
		BlockPos pos = context.getClickedPos();
		ItemStack stack = context.getItemInHand();
		if (level.getBlockState(pos).getBlock() instanceof CropBlock) {
			pos = pos.below();
		}
		if (!(level instanceof ServerLevel server)) {
			return InteractionResult.SUCCESS;
		}
		if (water(stack) <= 0) {
			if (context.getPlayer() != null) {
				context.getPlayer().sendOverlayMessage(Component.literal("Empty! Right-click water to fill it.").withStyle(ChatFormatting.RED));
			}
			return InteractionResult.FAIL;
		}
		boolean any = false;
		for (int dx = -1; dx <= 1; dx++) {
			for (int dz = -1; dz <= 1; dz++) {
				BlockPos soil = pos.offset(dx, 0, dz);
				if (FarmHelpers.water(server, soil)) {
					any = true;
					if (server.getRandom().nextInt(3) == 0) {
						FarmHelpers.boost(server, soil.above());
					}
					server.sendParticles(ParticleTypes.SPLASH, soil.getX() + 0.5, soil.getY() + 1.1, soil.getZ() + 0.5, 4, 0.3, 0.1, 0.3, 0.0);
				}
			}
		}
		if (!any) {
			return InteractionResult.PASS;
		}
		stack.setDamageValue(stack.getDamageValue() + 1);
		level.playSound(null, pos, SoundEvents.WEATHER_RAIN, SoundSource.BLOCKS, 0.6f, 1.6f);
		return InteractionResult.SUCCESS;
	}

	@Override
	public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> lines, TooltipFlag flag) {
		super.appendHoverText(stack, context, display, lines, flag);
		lines.accept(Component.literal("Water: " + Math.max(0, water(stack)) + " / " + (CAPACITY - 1)).withStyle(ChatFormatting.AQUA));
		lines.accept(Component.literal("Waters 3x3 farmland; crops may grow a step.").withStyle(ChatFormatting.GRAY));
	}
}
