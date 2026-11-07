package com.onepiecemod.creature;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.context.UseOnContext;

/**
 * A spawn egg for a One Piece creature. Right-click a block to place the creature there.
 */
public class CreatureEggItem extends Item {
	private final EntityType<CreatureEntity> type;

	public CreatureEggItem(EntityType<CreatureEntity> type, Properties properties) {
		super(properties);
		this.type = type;
	}

	@Override
	public InteractionResult useOn(UseOnContext context) {
		if (context.getLevel() instanceof ServerLevel level) {
			CreatureEntity creature = type.create(level, EntitySpawnReason.SPAWN_ITEM_USE);
			if (creature != null) {
				BlockPos pos = context.getClickedPos().relative(context.getClickedFace());
				float yaw = context.getPlayer() != null ? context.getPlayer().getYRot() + 180 : 0;
				creature.setPos(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5);
				creature.setYRot(yaw);
				creature.setYHeadRot(yaw);
				creature.setPersistenceRequired(); // Creatures you place yourself never wander off and vanish.
				level.addFreshEntity(creature);
				if (context.getPlayer() == null || !context.getPlayer().isCreative()) {
					context.getItemInHand().shrink(1);
				}
			}
		}
		return InteractionResult.SUCCESS;
	}
}
