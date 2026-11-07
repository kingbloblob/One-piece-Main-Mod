package com.onepiecemod.weapon;

import java.util.function.Consumer;

import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.Level;

/**
 * Buggy's Knives: right-click to throw one. It lands where it hit, so you can pick it up again
 * (about 1 in 4 breaks). They stack, so carry a handful.
 */
public class ThrowingKnifeItem extends Item {
	private static final float DAMAGE = 6.0f;
	private static final double RANGE = 20.0;
	private static final float BREAK_CHANCE = 0.25f;

	public ThrowingKnifeItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		ItemStack stack = player.getItemInHand(hand);
		if (level instanceof ServerLevel serverLevel && player instanceof ServerPlayer thrower) {
			level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.ARROW_SHOOT, SoundSource.PLAYERS, 0.8f, 1.6f);
			Shot.Hit hit = Shot.trace(thrower, serverLevel, RANGE, 0.03f, ParticleTypes.CRIT);
			if (hit.target() != null) {
				boolean headshot = Shot.isHeadshot(hit.target(), hit.point());
				Shot.hurt(thrower, serverLevel, hit.target(), headshot ? DAMAGE * Shot.HEADSHOT : DAMAGE);
				Shot.hitMarker(thrower, headshot);
			}
			boolean breaks = serverLevel.getRandom().nextFloat() < BREAK_CHANCE;
			if (!thrower.getAbilities().instabuild) {
				ItemStack thrown = stack.split(1);
				if (!breaks) {
					serverLevel.addFreshEntity(new ItemEntity(serverLevel, hit.point().x, hit.point().y, hit.point().z, thrown));
				}
			}
			player.getCooldowns().addCooldown(stack, 8);
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay displayComponent, Consumer<Component> textConsumer, TooltipFlag type) {
		textConsumer.accept(Component.literal("Right-click to throw. Pick it back up where it lands.").withStyle(ChatFormatting.GRAY));
	}
}
