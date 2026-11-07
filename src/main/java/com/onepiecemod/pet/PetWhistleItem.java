package com.onepiecemod.pet;

import java.util.List;
import java.util.function.Consumer;

import net.minecraft.ChatFormatting;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.Level;

/**
 * The Pet Whistle. Blow it and every pet you have within 128 blocks comes running (or swimming) to you,
 * and you get a list of them with their health. Sneak while blowing it and they all wait where they are.
 */
public class PetWhistleItem extends Item {
	private static final double RANGE = 128.0;

	public PetWhistleItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		ItemStack stack = player.getItemInHand(hand);
		if (!(level instanceof ServerLevel serverLevel)) {
			return InteractionResult.SUCCESS;
		}
		player.getCooldowns().addCooldown(stack, 20);
		SoundEvent sound = BuiltInRegistries.SOUND_EVENT.getValue(Identifier.parse("block.note_block.flute"));
		if (sound != null) {
			serverLevel.playSound(null, player.getX(), player.getY(), player.getZ(), sound, SoundSource.PLAYERS, 1.5f,
					player.isShiftKeyDown() ? 0.7f : 1.6f);
		}

		List<Mob> pets = Pets.petsOf(player, RANGE);
		pets.removeIf(pet -> pet == player.getVehicle());
		if (pets.isEmpty()) {
			Pets.tell(player, Component.literal("No pets heard you. Tame a creature first, or get within 128 blocks of yours."),
					ChatFormatting.GRAY);
			return InteractionResult.SUCCESS;
		}

		boolean stay = player.isShiftKeyDown();
		MutableComponent list = Component.empty();
		int unreachable = 0;
		for (Mob mob : pets) {
			Pet pet = (Pet) mob;
			pet.setStaying(stay);
			mob.getNavigation().stop();
			if (!stay && mob.distanceToSqr(player) > 144.0 && !Pets.bringTo(mob, player)) {
				unreachable++; // a swimmer and no water nearby: it swims as close as it can
			}
			if (!list.getSiblings().isEmpty()) {
				list.append(", ");
			}
			list.append(mob.getName()).append(" " + Math.round(mob.getHealth()) + "/" + Math.round(mob.getMaxHealth()) + " HP, bond "
					+ PetBond.level(pet));
		}

		String head = stay ? pets.size() + (pets.size() == 1 ? " pet waits" : " pets wait") + " here: "
				: pets.size() + (pets.size() == 1 ? " pet is" : " pets are") + " coming: ";
		Pets.tell(player, Component.literal(head).append(list), ChatFormatting.GREEN);
		if (unreachable > 0) {
			Pets.tell(player, Component.literal(unreachable + " of them only swim. Stand by the sea so they can reach you."),
					ChatFormatting.GRAY);
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public void appendHoverText(ItemStack stack, Item.TooltipContext context, TooltipDisplay display,
			Consumer<Component> tooltip, TooltipFlag flag) {
		tooltip.accept(Component.literal("Use: call all your pets within 128 blocks").withStyle(ChatFormatting.GRAY));
		tooltip.accept(Component.literal("Sneak + use: tell them all to wait").withStyle(ChatFormatting.GRAY));
		tooltip.accept(Component.literal("Type /pets to see their bond and abilities").withStyle(ChatFormatting.GRAY));
	}
}
