package com.onepiecemod.baseworks;

import java.util.List;
import java.util.Map;

import net.minecraft.ChatFormatting;
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

/**
 * A plan book: Deck Plans (rooms for your crew ship) or Island Base Plans (pieces of your hideout).
 *
 *  - Use in the air: turn to the next page (sneak: the page before) and read it.
 *  - Use on a block: see that page as see-through ghost blocks there, facing the way you look.
 *  - Sneak and use on a block: put the ghosts away.
 */
public class PlanBookItem extends Item {
	public enum Book {
		DECK("Deck Plans", "deck"),
		BASE("Island Base Plans", "base");

		final String title;
		final String word;

		Book(String title, String word) {
			this.title = title;
			this.word = word;
		}
	}

	private final Book book;

	public PlanBookItem(Book book, Properties properties) {
		super(properties);
		this.book = book;
	}

	public static int page(ItemStack stack, int pages) {
		CustomData data = stack.get(DataComponents.CUSTOM_DATA);
		int page = data == null ? 0 : data.copyTag().getIntOr("Page", 0);
		return Math.floorMod(page, Math.max(1, pages));
	}

	private static void setPage(ItemStack stack, int page) {
		CustomData data = stack.get(DataComponents.CUSTOM_DATA);
		CompoundTag tag = data == null ? new CompoundTag() : data.copyTag();
		tag.putInt("Page", page);
		stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
	}

	private LayoutPlan current(ItemStack stack) {
		List<LayoutPlan> pages = PlanBooks.book(book);
		return pages.get(page(stack, pages.size()));
	}

	@Override
	public Component getName(ItemStack stack) {
		List<LayoutPlan> pages = PlanBooks.book(book);
		int page = page(stack, pages.size());
		return Component.literal(book.title + ": " + pages.get(page).title + " (" + (page + 1) + "/" + pages.size() + ")");
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (player instanceof ServerPlayer serverPlayer) {
			ItemStack stack = player.getItemInHand(hand);
			List<LayoutPlan> pages = PlanBooks.book(book);
			int page = page(stack, pages.size()) + (player.isShiftKeyDown() ? -1 : 1);
			setPage(stack, Math.floorMod(page, pages.size()));
			printPage(serverPlayer, current(stack), Math.floorMod(page, pages.size()) + 1, pages.size());
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public InteractionResult useOn(UseOnContext context) {
		if (context.getPlayer() instanceof ServerPlayer player) {
			if (player.isShiftKeyDown()) {
				PlanOutlines.hide(player, true);
				return InteractionResult.SUCCESS;
			}
			LayoutPlan plan = current(context.getItemInHand());
			LayoutPlan.Placed placed = plan.at(context.getClickedPos(), player.getDirection());
			PlanOutlines.show(player, placed);
		}
		return InteractionResult.SUCCESS;
	}

	void printPage(ServerPlayer player, LayoutPlan plan, int page, int pages) {
		player.sendSystemMessage(Component.literal("=== " + book.title + " " + page + "/" + pages + ": " + plan.title + " ===")
				.withStyle(ChatFormatting.GOLD));
		player.sendSystemMessage(Component.literal(plan.purpose).withStyle(ChatFormatting.AQUA));
		StringBuilder needs = new StringBuilder();
		for (Map.Entry<String, Integer> entry : plan.materials().entrySet()) {
			if (needs.length() > 0) {
				needs.append(", ");
			}
			needs.append(entry.getValue()).append(" x ").append(entry.getKey());
		}
		player.sendSystemMessage(Component.literal("Size " + plan.width() + " wide, " + plan.depth() + " deep, " + plan.height()
				+ " tall. Needs: " + needs).withStyle(ChatFormatting.YELLOW));
		for (String tip : plan.tips) {
			player.sendSystemMessage(Component.literal("Tip: " + tip).withStyle(ChatFormatting.GRAY));
		}
		player.sendSystemMessage(Component.literal("Click the " + (book == Book.DECK ? "deck" : "ground")
				+ " to see it as ghost blocks, facing the way you look. Use in the air for the next page (sneak: back).")
				.withStyle(ChatFormatting.GRAY));
	}
}
