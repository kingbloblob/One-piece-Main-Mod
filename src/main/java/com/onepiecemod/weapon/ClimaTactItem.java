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
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/**
 * Nami's Sorcery Clima-Tact, built by Usopp.
 * Right-click: Thunderbolt Tempo, a lightning bolt where you look (up to 24 blocks).
 * Sneak + right-click: Mirage Tempo, you turn invisible for 10 seconds.
 */
public class ClimaTactItem extends Item {
	public ClimaTactItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		ItemStack stack = player.getItemInHand(hand);
		if (!(level instanceof ServerLevel serverLevel) || !(player instanceof ServerPlayer nami)) {
			return InteractionResult.SUCCESS;
		}
		if (player.isShiftKeyDown()) {
			player.addEffect(new MobEffectInstance(MobEffects.INVISIBILITY, 200, 0));
			serverLevel.sendParticles(ParticleTypes.CLOUD, player.getX(), player.getY() + 1, player.getZ(), 20, 0.5, 0.8, 0.5, 0.02);
			nami.sendOverlayMessage(Component.literal("Mirage Tempo!").withStyle(ChatFormatting.AQUA));
			player.getCooldowns().addCooldown(stack, 600);
		} else {
			Shot.Hit hit = Shot.trace(nami, serverLevel, 24.0, 0.0f, ParticleTypes.ELECTRIC_SPARK);
			Vec3 at = hit.target() != null ? hit.target().position() : hit.point();
			Shot.lightning(nami, serverLevel, at, 6.0f);
			level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.LIGHTNING_BOLT_IMPACT, SoundSource.PLAYERS, 0.6f, 1.5f);
			nami.sendOverlayMessage(Component.literal("Thunderbolt Tempo!").withStyle(ChatFormatting.YELLOW));
			player.getCooldowns().addCooldown(stack, 160);
		}
		stack.hurtAndBreak(1, player, hand.asEquipmentSlot());
		return InteractionResult.SUCCESS;
	}

	@Override
	public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay displayComponent, Consumer<Component> textConsumer, TooltipFlag type) {
		textConsumer.accept(Component.literal("Right-click: Thunderbolt Tempo").withStyle(ChatFormatting.GRAY));
		textConsumer.accept(Component.literal("Sneak + right-click: Mirage Tempo").withStyle(ChatFormatting.GRAY));
	}
}
