package com.onepiecemod.resource;

import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;

/**
 * Sabaody's bubble coating, made from Yarukiman resin. Use it to wrap yourself in a bubble for 5 minutes:
 * you breathe and swim easily underwater, and can see in the dark depths. Good for the trip to Fishman Island.
 */
public class BubbleCoatingItem extends Item {
	private static final int DURATION = 20 * 60 * 5;

	public BubbleCoatingItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (!level.isClientSide()) {
			player.addEffect(new MobEffectInstance(MobEffects.WATER_BREATHING, DURATION, 0));
			player.addEffect(new MobEffectInstance(MobEffects.DOLPHINS_GRACE, DURATION, 0));
			player.addEffect(new MobEffectInstance(MobEffects.NIGHT_VISION, DURATION, 0));
			com.onepiecemod.deepsea.DeepPressure.coat(player, DURATION); // Keeps the deep sea's pressure off too.
			level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.BUBBLE_COLUMN_UPWARDS_AMBIENT, SoundSource.PLAYERS, 1.0f, 1.0f);
			if (!player.isCreative()) {
				player.getItemInHand(hand).shrink(1);
			}
		}
		return InteractionResult.SUCCESS;
	}
}
