package com.onepiecemod.deco;

import java.util.function.Function;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.Consumable;
import net.minecraft.world.item.component.Consumables;
import net.minecraft.world.item.consume_effects.ApplyStatusEffectsConsumeEffect;

import com.onepiecemod.OnePieceMod;

/**
 * Snacks and drinks from around the Grand Line, plus Bubble Resin from Yarukiman trees.
 * Recipes are in data/onepiece/recipe (made by tools/deco/gen_deco.py).
 */
public class DecoItems {
	/** Nami's favourite fruit from Cocoyasi Village. Plant it to grow a Mikan Bush. */
	public static final Item MIKAN = register("mikan", properties -> new BlockItem(DecoBlocks.MIKAN_BUSH, properties),
			new Item.Properties().useItemDescriptionPrefix()
					.food(new FoodProperties.Builder().nutrition(3).saturationModifier(0.4f).build()));

	/** Falls from Palm leaves. */
	public static final Item COCONUT = register("coconut", Item::new,
			new Item.Properties().food(new FoodProperties.Builder().nutrition(4).saturationModifier(0.5f).build()));

	public static final Item ONIGIRI = register("onigiri", Item::new,
			new Item.Properties().food(new FoodProperties.Builder().nutrition(6).saturationModifier(0.7f).build()));

	/** Wano sweets. A little healing. */
	public static final Item DANGO = register("dango", Item::new,
			new Item.Properties().food(new FoodProperties.Builder().nutrition(5).saturationModifier(0.6f).build(),
					Consumables.defaultFood().onConsume(effect(new MobEffectInstance(MobEffects.REGENERATION, 100))).build()));

	/** Zoro's drink: stronger for a while, but the world spins a little. */
	public static final Item SAKE = register("sake", Item::new,
			new Item.Properties().stacksTo(16).usingConvertsTo(Items.GLASS_BOTTLE)
					.food(new FoodProperties.Builder().nutrition(2).saturationModifier(0.2f).alwaysEdible().build(),
							drink(new MobEffectInstance(MobEffects.STRENGTH, 400), new MobEffectInstance(MobEffects.NAUSEA, 100))));

	/** Franky's fuel. Makes you fast. */
	public static final Item COLA = register("cola", Item::new,
			new Item.Properties().stacksTo(16).usingConvertsTo(Items.GLASS_BOTTLE)
					.food(new FoodProperties.Builder().nutrition(2).saturationModifier(0.2f).alwaysEdible().build(),
							drink(new MobEffectInstance(MobEffects.SPEED, 600))));

	/** Chopper's favourite. */
	public static final Item COTTON_CANDY = register("cotton_candy", Item::new,
			new Item.Properties().food(new FoodProperties.Builder().nutrition(2).saturationModifier(0.1f).alwaysEdible().build(),
					Consumables.defaultFood().onConsume(effect(new MobEffectInstance(MobEffects.SPEED, 200))).build()));

	/** The sticky sap of Sabaody's Yarukiman trees that blows bubbles. Crafts Bubble Glass and lamps. */
	public static final Item BUBBLE_RESIN = register("bubble_resin", Item::new, new Item.Properties());

	public static void initialize() {
		// Loading this class registers the items above.
	}

	private static ApplyStatusEffectsConsumeEffect effect(MobEffectInstance... effects) {
		return new ApplyStatusEffectsConsumeEffect(java.util.List.of(effects));
	}

	private static Consumable drink(MobEffectInstance... effects) {
		return Consumables.defaultDrink().onConsume(effect(effects)).build();
	}

	private static Item register(String name, Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		return Registry.register(BuiltInRegistries.ITEM, key, factory.apply(properties.setId(key)));
	}
}
