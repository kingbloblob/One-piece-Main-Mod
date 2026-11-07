package com.onepiecemod.sea;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/**
 * Sea King Bait: throw it over deep water and a Sea King rises for it about 12 blocks in front of you.
 * Handy for testing, or for hunting Sea Kings for their meat.
 */
public class SeaKingBaitItem extends Item {
	public SeaKingBaitItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (!(level instanceof ServerLevel serverLevel)) {
			return InteractionResult.SUCCESS;
		}
		// A beaten Sea King is right here: they meant to feed it (right-click the Sea King itself), not call another.
		if (!level.getEntitiesOfClass(SeaKingEntity.class, player.getBoundingBox().inflate(16.0),
				king -> !king.isTamed() && king.getHealth() <= king.getMaxHealth() * 0.25f).isEmpty()) {
			player.sendSystemMessage(Component.literal("Aim at the beaten Sea King and right-click it to feed it the bait.").withStyle(ChatFormatting.GRAY));
			return InteractionResult.FAIL;
		}
		player.getCooldowns().addCooldown(player.getItemInHand(hand), 40);
		// Straight ahead of the player, ignoring whether they look up or down.
		Vec3 ahead = Vec3.directionFromRotation(0.0f, player.getYRot()).scale(12.0);
		BlockPos spot = BlockPos.containing(player.getX() + ahead.x, level.getSeaLevel() - 5, player.getZ() + ahead.z);
		if (!SeaKingSpawner.isDeepWater(serverLevel, spot)) {
			player.sendSystemMessage(Component.literal("Throw the bait over deep water (at least 8 blocks deep).").withStyle(ChatFormatting.GRAY));
			return InteractionResult.FAIL;
		}

		SeaKingEntity seaKing = SeaEntities.SEA_KING.create(serverLevel, EntitySpawnReason.SPAWN_ITEM_USE);
		if (seaKing != null) {
			seaKing.setPos(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
			seaKing.setYRot(player.getYRot() + 180.0f); // Facing you. Good luck.
			serverLevel.addFreshEntity(seaKing);
			player.sendSystemMessage(Component.literal("The water churns... a Sea King took the bait!").withStyle(ChatFormatting.DARK_AQUA));
			if (!player.isCreative()) {
				player.getItemInHand(hand).shrink(1);
			}
		}
		return InteractionResult.SUCCESS;
	}
}
