package com.onepiecemod.sea;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/**
 * The Log Pose: a compass worn on the wrist. All the work happens in LogPoseTracker.
 * Right-click it to read where the needle points.
 */
public class LogPoseItem extends Item {
	public LogPoseItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (level instanceof ServerLevel serverLevel && player instanceof ServerPlayer serverPlayer) {
			// Holding right-click would repeat this every few ticks, so wait 3 seconds between readings.
			ItemStack stack = player.getItemInHand(hand);
			if (player.getCooldowns().isOnCooldown(stack)) {
				return InteractionResult.PASS;
			}
			player.getCooldowns().addCooldown(stack, 60);
			player.sendSystemMessage(status(serverLevel, serverPlayer));
		}
		return InteractionResult.SUCCESS;
	}

	private static Component status(ServerLevel level, ServerPlayer player) {
		if (level.dimension() != Level.OVERWORLD) {
			return Component.literal("The needle spins wildly. There are no islands in this dimension.").withStyle(ChatFormatting.GRAY);
		}
		int recording = LogPoseTracker.secondsRecorded(player);
		if (recording > 0) {
			return Component.literal("Recording this island: " + recording + "/" + LogPoseTracker.recordSeconds() + " seconds.")
					.withStyle(ChatFormatting.AQUA);
		}
		LogPoseTracker.Journey journey = LogPoseTracker.journey(player);
		if (journey.target().isEmpty()) {
			return Component.literal("The needle isn't set yet. Stay on an island for " + LogPoseTracker.recordSeconds()
					+ " seconds with the Log Pose in your inventory.").withStyle(ChatFormatting.GRAY);
		}
		int distance = (int) IslandFinder.horizontalDistance(player.blockPosition(), journey.target().get());
		return Component.literal("The needle points to ")
				.append(LogPoseTracker.targetName(level, journey.target().get()))
				.append(", " + distance + " blocks away. " + journey.visited().size() + " islands recorded so far.")
				.withStyle(ChatFormatting.AQUA);
	}
}
