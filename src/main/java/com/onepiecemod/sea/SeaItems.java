package com.onepiecemod.sea;

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

import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;

import com.onepiecemod.OnePieceMod;

/**
 * The sea items: navigation tools, the snail phone, Sea King Meat, and bait to call a Sea King.
 */
public class SeaItems {
	/** Points to the next island after it records the island you're standing on. */
	public static final Item LOG_POSE = register("log_pose", LogPoseItem::new,
			new Item.Properties().stacksTo(1));

	/** Remembers one island forever and always points back to it. */
	public static final Item ETERNAL_POSE = register("eternal_pose", EternalPoseItem::new,
			new Item.Properties().stacksTo(1).rarity(Rarity.UNCOMMON));

	/** A snail phone. Call your crew to your side, or tell them to wait. */
	public static final Item DEN_DEN_MUSHI = register("den_den_mushi", DenDenMushiItem::new,
			new Item.Properties().stacksTo(1));

	/** Use it over deep water and a Sea King comes for it. */
	public static final Item SEA_KING_BAIT = register("sea_king_bait", SeaKingBaitItem::new,
			new Item.Properties().stacksTo(16).rarity(Rarity.UNCOMMON));

	public static final Item SEA_KING_MEAT = register("sea_king_meat", Item::new,
			new Item.Properties().food(new FoodProperties.Builder().nutrition(4).saturationModifier(0.3f).build()));

	/** Luffy's favorite: a huge chunk of meat on the bone. */
	public static final Item COOKED_SEA_KING_MEAT = register("cooked_sea_king_meat", Item::new,
			new Item.Properties().food(new FoodProperties.Builder().nutrition(12).saturationModifier(1.0f).build()));

	public static final ResourceKey<CreativeModeTab> TAB_KEY = ResourceKey.create(
			BuiltInRegistries.CREATIVE_MODE_TAB.key(), OnePieceMod.id("seas")
	);

	private static Item register(String name, Function<Item.Properties, Item> itemFactory, Item.Properties properties) {
		ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = itemFactory.apply(properties.setId(itemKey));
		Registry.register(BuiltInRegistries.ITEM, itemKey, item);
		return item;
	}

	public static void initialize() {
		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY, FabricCreativeModeTab.builder()
				.icon(() -> new ItemStack(LOG_POSE))
				.title(Component.literal("One Piece: Seas"))
				.displayItems((params, output) -> {
					output.accept(LOG_POSE);
					output.accept(ETERNAL_POSE);
					output.accept(DEN_DEN_MUSHI);
					output.accept(SEA_KING_BAIT);
					output.accept(SEA_KING_MEAT);
					output.accept(COOKED_SEA_KING_MEAT);
				})
				.build());
	}
}
