package com.onepiecemod.stats;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.ItemStack;

import com.onepiecemod.character.CharacterFeature;

/**
 * Lets players take back all their stat points and spend them again (the Reset button on the K screen,
 * or /stats respec). The first reset is free; after that it costs Berries for every point you had spent.
 */
public class StatRespec {
	public static final int BERRIES_PER_POINT = 5;

	/** What a reset costs this player right now, in Berries. */
	public static int cost(int respecsSoFar, StatsData data) {
		return respecsSoFar == 0 ? 0 : BERRIES_PER_POINT * data.spentPoints();
	}

	public static int respecs(ServerPlayer player) {
		return player.getAttachedOrElse(StatsAttachments.RESPECS, 0);
	}

	public static void respec(ServerPlayer player) {
		StatsData data = StatsAttachments.get(player);
		if (data.spentPoints() == 0) {
			player.sendSystemMessage(Component.literal("You haven't spent any points yet.").withStyle(ChatFormatting.GRAY));
			return;
		}
		int price = cost(respecs(player), data);
		boolean free = player.getAbilities().instabuild;
		if (!free && price > 0) {
			if (count(player.getInventory()) < price) {
				player.sendSystemMessage(Component.literal("Resetting your stats costs " + price + " Berries.").withStyle(ChatFormatting.RED));
				return;
			}
			take(player.getInventory(), price);
		}
		StatsAttachments.set(player, data.withoutRanks());
		player.setAttached(StatsAttachments.RESPECS, respecs(player) + 1);
		StatBonuses.apply(player);
		StatsPayloads.sync(player);
		player.level().playSound(null, player.blockPosition(), SoundEvents.ENCHANTMENT_TABLE_USE, SoundSource.PLAYERS, 0.8f, 1.0f);
		player.sendSystemMessage(Component.literal("Your stat points are back" + (price > 0 && !free ? " (paid " + price + " Berries)" : "")
				+ ". Press K to spend them again.").withStyle(ChatFormatting.YELLOW));
	}

	private static int count(Inventory inventory) {
		int total = 0;
		for (int i = 0; i < inventory.getContainerSize(); i++) {
			ItemStack stack = inventory.getItem(i);
			if (stack.is(CharacterFeature.BERRY)) {
				total += stack.getCount();
			}
		}
		return total;
	}

	private static void take(Inventory inventory, int amount) {
		for (int i = 0; i < inventory.getContainerSize() && amount > 0; i++) {
			ItemStack stack = inventory.getItem(i);
			if (stack.is(CharacterFeature.BERRY)) {
				int used = Math.min(amount, stack.getCount());
				stack.shrink(used);
				amount -= used;
			}
		}
	}
}
