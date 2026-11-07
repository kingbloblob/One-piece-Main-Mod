package com.onepiecemod.settlement;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BellBlock;

/**
 * The Town Planner: found your own town and mark out its plots.
 *
 *  - Use on a bell: found a town around it (or, if it's your town's bell, read the town report and collect rent).
 *  - Use in the air: pick the next kind of plot (House, Shop, Tavern...). Sneak: the town report.
 *  - Use on the ground twice: the two opposite corners of a new plot.
 *  - Sneak and use on the ground: remove the plot there (or forget the first corner).
 *  - While you hold it in your town, every plot is outlined in see-through glass, coloured by kind.
 */
public class TownPlannerItem extends Item {
	public TownPlannerItem(Properties properties) {
		super(properties);
	}

	static PlotKind kind(ItemStack stack) {
		CustomData data = stack.get(DataComponents.CUSTOM_DATA);
		int index = data == null ? 0 : data.copyTag().getIntOr("Kind", 0);
		PlotKind[] kinds = PlotKind.values();
		return kinds[Math.floorMod(index, kinds.length)];
	}

	static BlockPos corner(ItemStack stack) {
		CustomData data = stack.get(DataComponents.CUSTOM_DATA);
		if (data == null) {
			return null;
		}
		CompoundTag tag = data.copyTag();
		return tag.getBooleanOr("HasCorner", false) ? BlockPos.of(tag.getLongOr("Corner", 0L)) : null;
	}

	private static void edit(ItemStack stack, java.util.function.Consumer<CompoundTag> change) {
		CustomData data = stack.get(DataComponents.CUSTOM_DATA);
		CompoundTag tag = data == null ? new CompoundTag() : data.copyTag();
		change.accept(tag);
		stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
	}

	static void setCorner(ItemStack stack, BlockPos pos) {
		edit(stack, tag -> {
			tag.putBoolean("HasCorner", pos != null);
			tag.putLong("Corner", pos == null ? 0L : pos.asLong());
		});
	}

	@Override
	public Component getName(ItemStack stack) {
		return Component.literal("Town Planner (" + kind(stack).title + ")");
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (player instanceof ServerPlayer serverPlayer) {
			ItemStack stack = player.getItemInHand(hand);
			if (player.isShiftKeyDown()) {
				Settlements.report(serverPlayer);
			} else {
				edit(stack, tag -> tag.putInt("Kind", Math.floorMod(tag.getIntOr("Kind", 0) + 1, PlotKind.values().length)));
				PlotKind kind = kind(stack);
				serverPlayer.sendSystemMessage(Component.literal("Planning: " + kind.title).withStyle(ChatFormatting.GOLD)
						.append(Component.literal("  needs " + kind.needsText()
								+ (kind.job != null ? ". A " + kind.job + " moves in to work here." : kind == PlotKind.HOUSE ? ". 2 townsfolk move in." : ".")
								+ " Rent " + kind.rent + "/day.").withStyle(ChatFormatting.YELLOW)));
			}
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public InteractionResult useOn(UseOnContext context) {
		if (!(context.getPlayer() instanceof ServerPlayer player)) {
			return InteractionResult.SUCCESS;
		}
		BlockPos pos = context.getClickedPos();
		ItemStack stack = context.getItemInHand();
		if (context.getLevel().getBlockState(pos).getBlock() instanceof BellBlock) {
			Settlements.useOnBell(player, pos.immutable());
			return InteractionResult.SUCCESS;
		}
		if (player.isShiftKeyDown()) {
			if (corner(stack) != null) {
				setCorner(stack, null);
				player.sendSystemMessage(Component.literal("First corner forgotten.").withStyle(ChatFormatting.GRAY));
			} else {
				Settlements.removePlot(player, pos);
			}
			return InteractionResult.SUCCESS;
		}
		BlockPos first = corner(stack);
		if (first == null) {
			String problem = Settlements.canPlotAt(player, pos);
			if (problem != null) {
				player.sendSystemMessage(Component.literal(problem).withStyle(ChatFormatting.RED));
				return InteractionResult.SUCCESS;
			}
			setCorner(stack, pos.immutable());
			player.sendSystemMessage(Component.literal("First corner of the " + kind(stack).title
					+ " set. Now click the opposite corner.").withStyle(ChatFormatting.YELLOW));
			return InteractionResult.SUCCESS;
		}
		setCorner(stack, null);
		Settlements.addPlot(player, kind(stack), first, pos.immutable());
		return InteractionResult.SUCCESS;
	}
}
