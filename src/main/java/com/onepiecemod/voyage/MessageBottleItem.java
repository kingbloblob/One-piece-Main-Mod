package com.onepiecemod.voyage;

import java.util.List;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemUtils;
import net.minecraft.world.level.Level;

import com.onepiecemod.treasure.TreasureFeature;

/**
 * A Message in a Bottle. Fished up at sea, found in drifting supply boats, left behind by Island Whales.
 * Right-click to pull out the note: a few lines from someone lost at sea, and folded inside it a chart, usually
 * to the castaway's own cache on a little sandbar island (TreasureKind.CASTAWAY).
 */
public class MessageBottleItem extends Item {
	/** What the notes say. Some are castaways, some are pirates, a few are odder than that. */
	private static final List<String> NOTES = List.of(
			"\"Day 41 on this sandbar. Ate the last coconut. If you find this, my savings are buried under the palm. Spend them well.\"",
			"\"To whoever finds this: I hid the crew's share before the Marines caught us. The chart is true. Don't tell the captain.\"",
			"\"A Sea King ate our ship. I swam to a sandbar no bigger than a dinner table. Please send meat.\"",
			"\"I was the ship's cook. We ran aground and everyone left without me. My recipe box is buried with the rest. Yohoho... no wait, that's someone else's line.\"",
			"\"The Log Pose spun and spun and then we hit a whirlpool. I'm the only one who made it. The chart marks where I wait.\"",
			"\"Note to self: never bet your ship in a Davy Back Fight. Treasure's under the X. Signed, a very sorry captain.\"",
			"\"If you are reading this, I am probably still here. Bring a shovel. And maybe a boat.\"",
			"\"They said the Grand Line was dangerous. They didn't say it would rain fish. I've had enough fish.\"",
			"\"I've marked my stash. I'm off to find the One Piece on a raft made of barrels. Wish me luck!\"",
			"\"Whoever finds this bottle: the giant whale with the island on its back saved my life. Be kind to it.\"");

	public MessageBottleItem(Properties properties) {
		super(properties);
	}

	@Override
	public Component getName(ItemStack stack) {
		return Component.literal("Message in a Bottle");
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (!(player instanceof ServerPlayer serverPlayer)) {
			return InteractionResult.SUCCESS;
		}
		RandomSource random = level.getRandom();
		serverPlayer.sendSystemMessage(Component.literal("You pull the cork and unroll a damp note...").withStyle(ChatFormatting.GRAY));
		serverPlayer.sendSystemMessage(Component.literal(NOTES.get(random.nextInt(NOTES.size()))).withStyle(ChatFormatting.ITALIC, ChatFormatting.AQUA));

		int roll = random.nextInt(100);
		Item chart = roll < 60 ? TreasureFeature.CASTAWAY_CHART : roll < 82 ? TreasureFeature.TREASURE_MAP
				: roll < 96 ? TreasureFeature.WRECK_CHART : TreasureFeature.HOARD_MAP;
		ItemStack found = new ItemStack(chart);
		serverPlayer.sendSystemMessage(Component.literal("Something else was rolled up inside: a " + found.getHoverName().getString() + "!")
				.withStyle(ChatFormatting.GOLD));
		level.playSound(null, player.blockPosition(), SoundEvents.BOTTLE_EMPTY, SoundSource.PLAYERS, 1.0f, 1.0f);
		com.onepiecemod.advancement.AdvancementFeature.grant(serverPlayer, "journey/message_bottle");

		// The bottle turns into the chart, like filling a bucket.
		ItemStack result = ItemUtils.createFilledResult(player.getItemInHand(hand), player, found);
		return InteractionResult.SUCCESS.heldItemTransformedTo(result);
	}
}
