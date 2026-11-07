package com.onepiecemod.power;

import java.util.function.Consumer;

import net.minecraft.ChatFormatting;
import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
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
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.Level;

import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.crafting.CraftingFeature;

/**
 * Sea Purge: a Seastone draught that washes a Devil Fruit out of your body, so you can eat a new one.
 * Made at the Seastone Workbench (see station_recipes.json). Drinking it costs 30 XP levels,
 * wipes your fruit, mastery and awakening, and leaves you sick for a few minutes.
 * Sneak + right-click to drink, so nobody throws their fruit away by accident.
 */
public class SeaPurgeItem extends Item {
	/** XP levels it takes to drink. */
	public static final int LEVEL_COST = 30;
	private static final int SICK_TIME = 5 * 60 * 20;

	public static final Item SEA_PURGE = register();

	public SeaPurgeItem(Properties properties) {
		super(properties);
	}

	public static void initialize() {
		CreativeModeTabEvents.modifyOutputEvent(CraftingFeature.TAB_KEY).register(output -> output.accept(SEA_PURGE));
	}

	private static Item register() {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id("sea_purge"));
		Item item = new SeaPurgeItem(new Item.Properties().setId(key).stacksTo(1).rarity(Rarity.EPIC)
				.component(DataComponents.ITEM_NAME, Component.literal("Sea Purge")));
		return Registry.register(BuiltInRegistries.ITEM, key, item);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (!(player instanceof ServerPlayer)) {
			return InteractionResult.SUCCESS;
		}
		if (!DevilFruitPowers.hasAnyFruit(player)) {
			player.sendOverlayMessage(Component.literal("You have no Devil Fruit to purge.").withStyle(ChatFormatting.GRAY));
			return InteractionResult.FAIL;
		}
		if (!player.isShiftKeyDown()) {
			player.sendOverlayMessage(Component.literal("Sneak + right-click to drink. Your fruit, mastery and awakening will be gone.").withStyle(ChatFormatting.YELLOW));
			return InteractionResult.FAIL;
		}
		if (!player.isCreative() && player.experienceLevel < LEVEL_COST) {
			player.sendOverlayMessage(Component.literal("You need " + LEVEL_COST + " XP levels to survive the purge.").withStyle(ChatFormatting.RED));
			return InteractionResult.FAIL;
		}

		DevilFruit old = DevilFruitPowers.getFruit(player);
		player.removeAttached(ModAttachments.DEVIL_FRUIT);
		player.removeAttached(ModAttachments.FRUIT_MASTERY);
		player.removeAttached(ModAttachments.AWAKENED);

		// The sea takes its price: weak, slow and dizzy for a while.
		player.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, SICK_TIME, 1));
		player.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, SICK_TIME, 0));
		player.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 200, 0));
		level.playSound(null, player.blockPosition(), SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.PLAYERS, 0.8f, 1.0f);

		if (!player.isCreative()) {
			player.giveExperienceLevels(-LEVEL_COST);
			player.getItemInHand(hand).shrink(1);
		}
		String name = old != null ? old.name() : "Devil Fruit";
		player.sendSystemMessage(Component.literal("The sea washes the " + name + " out of your body. You can eat a new fruit now.").withStyle(ChatFormatting.AQUA));
		return InteractionResult.SUCCESS;
	}

	@Override
	public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> text, TooltipFlag flag) {
		text.accept(Component.literal("Removes your Devil Fruit so you can eat another.").withStyle(ChatFormatting.GRAY));
		text.accept(Component.literal("Costs " + LEVEL_COST + " XP levels. Mastery and awakening are lost.").withStyle(ChatFormatting.DARK_RED));
		text.accept(Component.literal("Sneak + right-click to drink.").withStyle(ChatFormatting.DARK_GRAY));
	}
}
