package com.onepiecemod.cuisine;

import java.util.Optional;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.GlobalPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.LodestoneTracker;
import net.minecraft.world.level.Level;

/**
 * Sanji's compass to the All Blue. In the Overworld its needle points at the All Blue; elsewhere it spins.
 * Right-click for a rough distance.
 */
public class AllBlueCompassItem extends Item {
	public AllBlueCompassItem(Properties properties) {
		super(properties);
	}

	@Override
	public void inventoryTick(ItemStack stack, ServerLevel level, Entity entity, EquipmentSlot slot) {
		if (level.getGameTime() % 20 != 0) {
			return;
		}
		LodestoneTracker current = stack.get(DataComponents.LODESTONE_TRACKER);
		if (level.dimension() != Level.OVERWORLD) {
			if (current != null) {
				stack.remove(DataComponents.LODESTONE_TRACKER);
			}
			return;
		}
		GlobalPos target = GlobalPos.of(Level.OVERWORLD, AllBlue.center(level.getServer()));
		if (current == null || !current.target().equals(Optional.of(target))) {
			stack.set(DataComponents.LODESTONE_TRACKER, new LodestoneTracker(Optional.of(target), false));
		}
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (level instanceof ServerLevel server && player instanceof ServerPlayer serverPlayer) {
			if (level.dimension() != Level.OVERWORLD) {
				serverPlayer.sendOverlayMessage(Component.literal("The needle just spins. The All Blue is in the Overworld's seas.")
						.withStyle(ChatFormatting.GRAY));
			} else if (AllBlue.contains(server, player.getX(), player.getZ())) {
				serverPlayer.sendOverlayMessage(Component.literal("You're in the All Blue! Cast a line.").withStyle(ChatFormatting.AQUA));
			} else {
				BlockPos center = AllBlue.center(server.getServer());
				double distance = Math.sqrt(player.distanceToSqr(center.getX(), player.getY(), center.getZ()));
				long rounded = Math.max(100, Math.round(distance / 100.0) * 100);
				serverPlayer.sendOverlayMessage(Component.literal("The All Blue is about " + rounded + " blocks that way.")
						.withStyle(ChatFormatting.AQUA));
			}
		}
		return InteractionResult.SUCCESS;
	}
}
