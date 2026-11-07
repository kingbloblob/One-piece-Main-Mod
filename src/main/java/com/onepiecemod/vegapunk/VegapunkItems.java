package com.onepiecemod.vegapunk;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;
import java.util.function.Function;

import net.minecraft.ChatFormatting;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;

import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;

import com.onepiecemod.OnePieceMod;

/**
 * Parts that Pacifista and Seraphim drop, and the cyborg modules built from them at the Shipwright's Bench.
 * Recipes: onepiece/station_recipes.json (station shipwright_bench, ids starting with "cyborg_").
 */
public class VegapunkItems {
	private static final List<Item> TAB_ITEMS = new ArrayList<>();

	/** Common: every Pacifista and Seraphim may drop some. */
	public static final Item PACIFISTA_SCRAP = part("pacifista_scrap", Rarity.COMMON,
			"Armour plate torn off a Pacifista.", "Dropped by Pacifista and Seraphim.");
	/** One per Pacifista hunt (two from a Mark III). */
	public static final Item LASER_CORE = part("laser_core", Rarity.UNCOMMON,
			"The heart of a Pacifista's beam, still warm.", "Dropped by hunting Pacifista.");
	/** Sometimes from Pacifista hunts, always from Seraphim. Needed for tier II and III upgrades. */
	public static final Item VEGAPUNK_CHIP = part("vegapunk_chip", Rarity.RARE,
			"Dr. Vegapunk's control chip. Genius-grade circuitry.", "Dropped by hunting Pacifista (sometimes) and Seraphim.");
	/** Only from Seraphim. Lunarian Plating and every tier III upgrade need it. */
	public static final Item SERAPHIM_FEATHER = part("seraphim_feather", Rarity.EPIC,
			"A black Lunarian feather that never stops smouldering.", "Dropped by Seraphim.");

	public static final Map<CyborgUpgrade, Item> MODULES = new EnumMap<>(CyborgUpgrade.class);

	static {
		for (CyborgUpgrade upgrade : CyborgUpgrade.values()) {
			MODULES.put(upgrade, register(upgrade.itemId, properties -> new CyborgModuleItem(properties, upgrade),
					new Item.Properties().stacksTo(16).rarity(upgrade.needsFeather ? Rarity.EPIC : Rarity.RARE)));
		}
	}

	public static final ResourceKey<CreativeModeTab> TAB_KEY = ResourceKey.create(
			BuiltInRegistries.CREATIVE_MODE_TAB.key(), OnePieceMod.id("cyborg"));

	public static void initialize() {
		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY, FabricCreativeModeTab.builder()
				.icon(() -> new ItemStack(LASER_CORE))
				.title(Component.literal("One Piece: Cyborg Parts"))
				.displayItems((params, output) -> TAB_ITEMS.forEach(output::accept))
				.build());
	}

	public static Item module(CyborgUpgrade upgrade) {
		return MODULES.get(upgrade);
	}

	private static Item part(String name, Rarity rarity, String flavour, String where) {
		return register(name, properties -> new PartItem(properties, flavour, where), new Item.Properties().rarity(rarity));
	}

	private static Item register(String name, Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = factory.apply(properties.setId(key));
		Registry.register(BuiltInRegistries.ITEM, key, item);
		TAB_ITEMS.add(item);
		return item;
	}

	/** A part: a line of flavour and where it comes from. */
	public static class PartItem extends Item {
		private final String flavour;
		private final String where;

		public PartItem(Properties properties, String flavour, String where) {
			super(properties);
			this.flavour = flavour;
			this.where = where;
		}

		@Override
		public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> lines, TooltipFlag flag) {
			super.appendHoverText(stack, context, display, lines, flag);
			lines.accept(Component.literal(flavour).withStyle(ChatFormatting.GRAY, ChatFormatting.ITALIC));
			lines.accept(Component.literal(where).withStyle(ChatFormatting.DARK_AQUA));
			lines.accept(Component.literal("Builds cyborg modules at the Shipwright's Bench.").withStyle(ChatFormatting.DARK_GRAY));
		}
	}
}
