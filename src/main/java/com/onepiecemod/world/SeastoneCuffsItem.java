package com.onepiecemod.world;

import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

/**
 * Seastone handcuffs. Right-click a Devil Fruit user (a player or a character like Crocodile)
 * to cuff them: their Devil Fruit power is sealed and they are slow and weak for 30 seconds (15 for a boss).
 * Each pair of cuffs works once.
 */
public class SeastoneCuffsItem extends Item {
	public SeastoneCuffsItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult interactLivingEntity(ItemStack stack, Player player, LivingEntity target, InteractionHand hand) {
		if (!SeastoneEffects.isFruitUser(target)) {
			if (!player.level().isClientSide()) {
				player.sendOverlayMessage(Component.literal("Seastone only works on Devil Fruit users."));
			}
			return InteractionResult.PASS;
		}
		if (!player.level().isClientSide()) {
			boolean boss = target instanceof com.onepiecemod.character.CharacterEntity character && character.isBoss();
			int seconds = boss ? 15 : 30;
			SeastoneEffects.drain(target, seconds * 20);
			player.sendOverlayMessage(Component.literal("Cuffed! Their power is sealed for " + seconds + " seconds."));
			if (target instanceof Player cuffed) {
				cuffed.sendOverlayMessage(Component.literal("Seastone Cuffs! Your Devil Fruit power is sealed for " + seconds + " seconds."));
			}
			if (!player.isCreative()) {
				stack.shrink(1);
			}
		}
		return InteractionResult.SUCCESS;
	}
}
