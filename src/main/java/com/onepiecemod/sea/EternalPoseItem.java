package com.onepiecemod.sea;

import java.util.List;
import java.util.Optional;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.GlobalPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.ItemLore;
import net.minecraft.world.item.component.LodestoneTracker;
import net.minecraft.world.level.Level;

/**
 * The Eternal Pose remembers one island forever. A new one is blank: right-click it while standing
 * on an island to tie it to that island. After that it always points home, wherever you sail.
 * Craft one for each island you want to get back to.
 */
public class EternalPoseItem extends Item {
	public EternalPoseItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (!(level instanceof ServerLevel serverLevel)) {
			return InteractionResult.SUCCESS;
		}
		ItemStack stack = player.getItemInHand(hand);
		LodestoneTracker tracker = stack.get(DataComponents.LODESTONE_TRACKER);

		if (tracker != null && tracker.target().isPresent()) {
			// Already tied to an island: say how far it is.
			GlobalPos home = tracker.target().get();
			if (home.dimension() != level.dimension()) {
				player.sendSystemMessage(Component.literal("Its island is in another dimension.").withStyle(ChatFormatting.GRAY));
			} else {
				int distance = (int) IslandFinder.horizontalDistance(player.blockPosition(), home.pos());
				player.sendSystemMessage(Component.literal("The needle points to its island, " + distance + " blocks away.")
						.withStyle(ChatFormatting.AQUA));
			}
			return InteractionResult.SUCCESS;
		}

		BlockPos here = player.blockPosition();
		if (level.dimension() != Level.OVERWORLD || !player.onGround() || player.isInWater()
				|| !IslandFinder.isLand(level.getBiome(here))) {
			player.sendSystemMessage(Component.literal("Stand on an island to tie this Eternal Pose to it.").withStyle(ChatFormatting.GRAY));
			return InteractionResult.FAIL;
		}

		Component islandName = IslandFinder.islandName(serverLevel, here);
		stack.set(DataComponents.LODESTONE_TRACKER, new LodestoneTracker(Optional.of(GlobalPos.of(level.dimension(), here)), false));
		stack.set(DataComponents.ITEM_NAME, Component.literal("Eternal Pose: ").append(islandName));
		stack.set(DataComponents.LORE, new ItemLore(List.of(
				Component.literal("Always points to " + here.getX() + ", " + here.getZ()).withStyle(ChatFormatting.GRAY))));
		level.playSound(null, here, SoundEvents.LODESTONE_COMPASS_LOCK, SoundSource.PLAYERS, 1.0f, 1.0f);
		player.sendSystemMessage(Component.literal("This Eternal Pose will point to this island forever.").withStyle(ChatFormatting.GOLD));
		return InteractionResult.SUCCESS;
	}
}
