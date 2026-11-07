package com.onepiecemod.bounty;

import java.util.List;

import net.minecraft.util.Prediction;
import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.ItemLore;
import net.minecraft.world.level.Level;

/**
 * A Wanted Poster of a player. It remembers whose face is on it and the bounty when it was printed.
 * Right-click it to read it. You get a new one when your bounty goes up a lot, or with /bounty poster.
 *
 * (The character posters that summon bosses are a different item, in the character package.)
 */
public class BountyPosterItem extends Item {
	public BountyPosterItem(Properties properties) {
		super(properties);
	}

	/** Prints a poster with the player's current bounty. */
	public static ItemStack create(Player pirate) {
		ItemStack poster = new ItemStack(BountyFeature.BOUNTY_POSTER);
		String name = pirate.getName().getString();
		long bounty = Bounty.get(pirate);
		poster.set(DataComponents.ITEM_NAME, Component.literal("Wanted: " + name));
		poster.set(DataComponents.LORE, new ItemLore(List.of(
				Component.literal("DEAD OR ALIVE").withStyle(ChatFormatting.DARK_RED),
				Component.literal(name).withStyle(ChatFormatting.GOLD),
				Component.literal(Bounty.format(bounty)).withStyle(ChatFormatting.YELLOW),
				Component.literal(Bounty.levelName(Bounty.threatLevel(bounty))).withStyle(ChatFormatting.GRAY),
				Component.literal("MARINE").withStyle(ChatFormatting.BLUE))));
		return poster;
	}

	/** Gives the player a fresh poster, or drops it at their feet if their bag is full. */
	public static void give(ServerPlayer pirate) {
		ItemStack poster = create(pirate);
		if (!pirate.getInventory().add(poster)) {
			pirate.drop(poster, false, Prediction.SERVER_ONLY);
		}
		pirate.sendSystemMessage(Component.literal("The Marines printed a new Wanted Poster of you!").withStyle(ChatFormatting.GOLD));
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (!level.isClientSide()) {
			ItemStack poster = player.getItemInHand(hand);
			ItemLore lore = poster.get(DataComponents.LORE);
			player.sendSystemMessage(Component.literal("+--------- WANTED ---------+").withStyle(ChatFormatting.GOLD));
			if (lore == null || lore.lines().isEmpty()) {
				player.sendSystemMessage(Component.literal("  This poster is blank. Use /bounty poster for yours."));
			} else {
				for (Component line : lore.lines()) {
					player.sendSystemMessage(Component.literal("  ").append(line));
				}
			}
			player.sendSystemMessage(Component.literal("+--------------------------+").withStyle(ChatFormatting.GOLD));
		}
		return InteractionResult.SUCCESS;
	}
}
