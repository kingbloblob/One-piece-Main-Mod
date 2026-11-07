package com.onepiecemod.item;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.function.Function;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.component.Consumables;

import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.power.DevilFruit;
import com.onepiecemod.power.DevilFruits;

/**
 * Every item the mod adds is created and registered here.
 */
public class ModItems {
	// Devil Fruits never fill you up, but you can always eat them.
	private static final FoodProperties DEVIL_FRUIT_FOOD = new FoodProperties.Builder()
			.alwaysEdible()
			.build();

	// One item for every fruit in DevilFruits.ALL, looked up by id ("mera_mera_no_mi").
	public static final Map<String, Item> DEVIL_FRUITS = new LinkedHashMap<>();

	static {
		for (DevilFruit fruit : DevilFruits.ALL) {
			DEVIL_FRUITS.put(fruit.id(), register(
					fruit.id(),
					properties -> new DevilFruitItem(fruit, properties),
					new Item.Properties()
							.food(DEVIL_FRUIT_FOOD, Consumables.defaultFood().build())
							.stacksTo(1)
							.rarity(Rarity.EPIC)
			));
		}
	}

	public static final Item GOMU_GOMU_NO_MI = DEVIL_FRUITS.get("gomu_gomu_no_mi");

	// Our own tab in the creative inventory.
	public static final ResourceKey<CreativeModeTab> ONE_PIECE_TAB_KEY = ResourceKey.create(
			BuiltInRegistries.CREATIVE_MODE_TAB.key(), OnePieceMod.id("one_piece")
	);
	public static final CreativeModeTab ONE_PIECE_TAB = FabricCreativeModeTab.builder()
			.icon(() -> new ItemStack(GOMU_GOMU_NO_MI))
			.title(Component.translatable("creativeTab.onepiece"))
			.displayItems((params, output) -> {
				for (Item fruit : DEVIL_FRUITS.values()) {
					output.accept(fruit);
				}
			})
			.build();

	private static Item register(String name, Function<Item.Properties, Item> itemFactory, Item.Properties properties) {
		ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = itemFactory.apply(properties.setId(itemKey));
		Registry.register(BuiltInRegistries.ITEM, itemKey, item);
		return item;
	}

	public static void initialize() {
		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, ONE_PIECE_TAB_KEY, ONE_PIECE_TAB);
	}
}
