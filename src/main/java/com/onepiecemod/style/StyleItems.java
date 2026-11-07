package com.onepiecemod.style;

import java.util.EnumMap;
import java.util.Map;
import java.util.function.Function;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.ToolMaterial;

import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;

import com.onepiecemod.OnePieceMod;

/**
 * The named swords (meito) and the Dojo Scrolls, plus their creative tab.
 *
 * Sword damage = 1 (your fist) + the material's bonus (diamond 3, netherite 4) + the number below.
 * So Wado Ichimonji does 7, the same as a diamond sword, and Yoru does 13.
 * Their special effects (Kitetsu's curse, Enma's hunger...) are in StylePassives.java.
 */
public class StyleItems {
	/** Kuina's sword, which Zoro holds in his mouth. Zoro gives it to you when he teaches you Santoryu. */
	public static final Item WADO_ICHIMONJI = sword("wado_ichimonji", "Wado Ichimonji", ToolMaterial.DIAMOND, 3.0f, -2.2f, Rarity.RARE);
	/** A cursed blade: hits harder, but sometimes cuts its owner. Crafted. */
	public static final Item SANDAI_KITETSU = sword("sandai_kitetsu", "Sandai Kitetsu", ToolMaterial.DIAMOND, 5.0f, -2.4f, Rarity.RARE);
	/** Ryuma's black blade. Dropped by Gecko Moria, who kept Ryuma as a zombie. */
	public static final Item SHUSUI = sword("shusui", "Shusui", ToolMaterial.NETHERITE, 4.0f, -2.4f, Rarity.EPIC);
	/** Oden's sword, the one that scarred Kaido. Dropped by Kaido. Strong, but it drains your stamina. */
	public static final Item ENMA = sword("enma", "Enma", ToolMaterial.NETHERITE, 6.0f, -2.4f, Rarity.EPIC);
	/** Mihawk's black blade, the strongest sword in the world. Dropped by Mihawk. */
	public static final Item YORU = sword("yoru", "Yoru", ToolMaterial.NETHERITE, 8.0f, -2.6f, Rarity.EPIC);

	/** The first Kitetsu, a Supreme Grade blade from Wano. Even more cursed than the third. Forged from Sandai Kitetsu. */
	public static final Item SHODAI_KITETSU = sword("shodai_kitetsu", "Shodai Kitetsu", ToolMaterial.NETHERITE, 7.0f, -2.4f, Rarity.EPIC);
	/** Kozuki Oden's second sword, Enma's partner. From the Beasts Pirates raid. */
	public static final Item AME_NO_HABAKIRI = sword("ame_no_habakiri", "Ame no Habakiri", ToolMaterial.NETHERITE, 6.0f, -2.3f, Rarity.EPIC);
	/** Gol D. Roger's sword, Ace. From the Roger Pirates raid: the last sword in the game. */
	public static final Item ACE = sword("ace", "Ace", ToolMaterial.NETHERITE, 9.0f, -2.4f, Rarity.EPIC);

	/** One Dojo Scroll per style. Reading it teaches the style instantly (no master needed). */
	public static final Map<FightingStyle, Item> SCROLLS = new EnumMap<>(FightingStyle.class);

	public static final ResourceKey<CreativeModeTab> TAB_KEY = ResourceKey.create(
			BuiltInRegistries.CREATIVE_MODE_TAB.key(), OnePieceMod.id("fighting_styles")
	);

	private static Item sword(String name, String displayName, ToolMaterial material, float damage, float speed, Rarity rarity) {
		return register(name,
				properties -> new Item(properties) {
					@Override
					public Component getName(ItemStack stack) {
						return Component.literal(displayName);
					}
				},
				new Item.Properties().sword(material, damage, speed).rarity(rarity).fireResistant());
	}

	private static Item register(String name, Function<Item.Properties, Item> itemFactory, Item.Properties properties) {
		ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = itemFactory.apply(properties.setId(itemKey));
		Registry.register(BuiltInRegistries.ITEM, itemKey, item);
		return item;
	}

	public static boolean isNamedSword(ItemStack stack) {
		return stack.is(WADO_ICHIMONJI) || stack.is(SANDAI_KITETSU) || stack.is(SHUSUI) || stack.is(ENMA) || stack.is(YORU)
				|| stack.is(SHODAI_KITETSU) || stack.is(AME_NO_HABAKIRI) || stack.is(ACE);
	}

	public static void initialize() {
		for (FightingStyle style : FightingStyle.values()) {
			SCROLLS.put(style, register("dojo_scroll_" + style.id(),
					properties -> new DojoScrollItem(style, properties),
					new Item.Properties().stacksTo(1).rarity(Rarity.UNCOMMON)));
		}

		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY, FabricCreativeModeTab.builder()
				.icon(() -> new ItemStack(WADO_ICHIMONJI))
				.title(Component.literal("One Piece: Fighting Styles"))
				.displayItems((params, output) -> {
					for (Item scroll : SCROLLS.values()) {
						output.accept(scroll);
					}
					output.accept(WADO_ICHIMONJI);
					output.accept(SANDAI_KITETSU);
					output.accept(SHUSUI);
					output.accept(ENMA);
					output.accept(YORU);
					output.accept(SHODAI_KITETSU);
					output.accept(AME_NO_HABAKIRI);
					output.accept(ACE);
				})
				.build());
	}
}
