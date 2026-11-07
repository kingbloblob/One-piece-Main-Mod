package com.onepiecemod.building;

import java.util.HashSet;
import java.util.Set;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.level.block.Blocks;

import com.onepiecemod.crew.Crew;
import com.onepiecemod.crew.CrewAttachments;
import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.crew.CrewmateEntity;

/**
 * Baratie Feast Table: a dining hall, like the floating restaurant where Sanji cooked.
 * Once a day, bring 8 pieces of food and throw a feast: everyone nearby (players and crewmates)
 * gets stronger and tougher for a while. Different kinds of food make a better feast,
 * and a Cook in your crew makes it last longer.
 */
public class FeastBuilding extends Multiblock {
	private static final int FOOD_NEEDED = 8;
	private static final int BASE_TICKS = 6000; // 5 minutes.
	private static final int COOK_TICKS = 9000; // 7.5 minutes with a Cook in the crew.
	private static final double RANGE = 16.0;

	public FeastBuilding() {
		super("feast_table", "Baratie Feast Table");
		fill("planks, wooden slabs or Tatami for the 5x5 dining room floor",
				state -> Parts.WOOD_DECK.test(state) || Parts.TATAMI.test(state),
				Parts.block("onepiece:palm_planks", Blocks.OAK_PLANKS), square(-1, 2));
		contains("wooden stairs as chairs around the table", Parts.CHAIR, new BlockPos(-2, 0, -2), new BlockPos(2, 1, 2), 4);
		contains("Campfire or Smoker (the kitchen stove)", Parts.COOKING_FIRE, new BlockPos(-2, 0, -2), new BlockPos(2, 2, 2), 1);
		contains("Cauldron (the soup pot)", Parts.CAULDRON, new BlockPos(-2, 0, -2), new BlockPos(2, 2, 2), 1);
		contains("Lantern or Paper Lantern", Parts.LANTERN, new BlockPos(-2, 0, -2), new BlockPos(2, 3, 2), 1);

		planLine("Floor: a 5x5 square of planks, wooden slabs or Tatami.");
		planLine("The Feast Table goes on the floor in the very middle.");
		planLine("Chairs: at least 4 wooden stairs on the floor around the table.");
		planLine("Kitchen: a Campfire or Smoker and a Cauldron on the floor.");
		planLine("Light: a Lantern or Paper Lantern. Walls and a roof are up to you.");
	}

	@Override
	public String purpose() {
		return "Right-click it with 8 pieces of food in your bag to throw a feast that powers up everyone nearby (once a day).";
	}

	@Override
	public void use(ServerPlayer player, BuildingRegistry.Entry entry) {
		ServerLevel level = (ServerLevel) player.level();
		long today = BuildingRegistry.day(level);
		if (entry.lastDay() == today) {
			player.sendSystemMessage(Component.literal("The kitchen is cleaning up after today's feast. Come back tomorrow!")
					.withStyle(ChatFormatting.GRAY));
			return;
		}
		int food = 0;
		for (ItemStack stack : player.getInventory().getNonEquipmentItems()) {
			if (stack.has(DataComponents.FOOD)) {
				food += stack.getCount();
			}
		}
		if (food < FOOD_NEEDED) {
			player.sendSystemMessage(Component.literal("A feast needs " + FOOD_NEEDED + " pieces of food in your bag. You have " + food + ".")
					.withStyle(ChatFormatting.RED));
			return;
		}

		// Take the food, one piece at a time from each stack in turn, so the feast uses lots of different dishes.
		Set<Item> kinds = new HashSet<>();
		int taken = 0;
		while (taken < FOOD_NEEDED) {
			for (ItemStack stack : player.getInventory().getNonEquipmentItems()) {
				if (taken < FOOD_NEEDED && stack.has(DataComponents.FOOD) && !stack.isEmpty()) {
					kinds.add(stack.getItem());
					stack.shrink(1);
					taken++;
				}
			}
		}
		BuildingRegistry.put(level, entry.withLastDay(today));

		Crew crew = player.getAttached(CrewAttachments.CREW);
		boolean cook = crew != null && crew.member(CrewRole.COOK) != null;
		boolean variety = kinds.size() >= 4;
		int ticks = cook ? COOK_TICKS : BASE_TICKS;

		BlockPos pos = entry.pos();
		AABB area = new AABB(pos).inflate(RANGE);
		int guests = 0;
		for (LivingEntity guest : level.getEntitiesOfClass(LivingEntity.class, area,
				entity -> entity.isAlive() && (entity instanceof ServerPlayer || entity instanceof CrewmateEntity))) {
			guest.addEffect(new MobEffectInstance(MobEffects.STRENGTH, ticks, 0));
			guest.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, ticks, 0));
			guest.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 600, 0));
			guest.addEffect(new MobEffectInstance(MobEffects.SATURATION, 10, 0));
			if (variety) {
				guest.addEffect(new MobEffectInstance(MobEffects.SPEED, ticks, 0));
				guest.addEffect(new MobEffectInstance(MobEffects.HASTE, ticks, 0));
			}
			level.sendParticles(ParticleTypes.HEART, guest.getX(), guest.getY() + 1.8, guest.getZ(), 3, 0.3, 0.2, 0.3, 0.0);
			if (guest instanceof ServerPlayer guestPlayer) {
				guestPlayer.sendSystemMessage(Component.literal("FEAST! " + player.getName().getString()
						+ " throws a feast. Eat up, you'll be stronger and tougher for " + ticks / 1200 + " minutes!").withStyle(ChatFormatting.GOLD));
			}
			guests++;
		}
		level.playSound(null, pos, SoundEvents.GENERIC_EAT.value(), SoundSource.PLAYERS, 1.0f, 1.0f);
		level.playSound(null, pos, SoundEvents.PLAYER_BURP, SoundSource.PLAYERS, 1.0f, 1.0f);
		player.sendSystemMessage(Component.literal(guests + (guests == 1 ? " guest" : " guests") + " fed with " + kinds.size()
				+ (kinds.size() == 1 ? " kind" : " kinds") + " of food.").withStyle(ChatFormatting.YELLOW));
		if (!variety) {
			player.sendSystemMessage(Component.literal("Tip: bring 4 or more different kinds of food for a bigger feast (speed and haste too).")
					.withStyle(ChatFormatting.GRAY));
		}
		if (!cook) {
			player.sendSystemMessage(Component.literal("Tip: with a Cook in your crew the feast lasts longer.").withStyle(ChatFormatting.GRAY));
		}
	}
}
