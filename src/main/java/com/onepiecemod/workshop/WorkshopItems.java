package com.onepiecemod.workshop;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;

import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.ToolMaterial;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.cuisine.DishItem;

/**
 * Items from the station upgrade trees: rare creature drops, the Skypiea Dials, the higher cooking tiers
 * and the Sea King Fang Blade. They go in the "One Piece: Crafting" tab (see WorkshopFeature).
 */
public class WorkshopItems {
	public static final List<Item> TAB_ITEMS = new ArrayList<>();
	private static final int MINUTE = 1200;

	// ---- Rare drops: each one is only useful at one station ----

	/** Sea King drop. The Swordsmith's Forge (Tempering Anvil) makes it into a blade. */
	public static final Item SEA_KING_FANG = item("sea_king_fang", Rarity.UNCOMMON);
	/** Island Whale drop. Sanji's Kitchen at the Ship's Galley cooks with it. */
	public static final Item AMBERGRIS = item("ambergris", Rarity.RARE);
	/** Punk Hazard Dragon drop. Lights the Dragon Hearth at the Swordsmith's Forge. */
	public static final Item DRAGON_HEARTSTONE = item("dragon_heartstone", Rarity.EPIC);
	/** Pacifista drop. Franky's Workshop at the Shipwright's Bench runs on them. */
	public static final Item PACIFISTA_CORE = item("pacifista_core", Rarity.RARE);

	// ---- Skypiea Dials (made at the Navigator's Desk after building the Dial Bench) ----

	public static final Item TONE_DIAL = dial("tone_dial", DialTools.Kind.TONE, 64, Rarity.UNCOMMON);
	public static final Item JET_DIAL = dial("jet_dial", DialTools.Kind.JET, 48, Rarity.RARE);
	public static final Item WATER_DIAL = dial("water_dial", DialTools.Kind.WATER, 48, Rarity.UNCOMMON);
	public static final Item MILKY_DIAL = dial("milky_dial", DialTools.Kind.MILKY, 48, Rarity.UNCOMMON);
	public static final Item REJECT_DIAL = dial("reject_dial", DialTools.Kind.REJECT, 24, Rarity.EPIC);
	public static final Item AXE_DIAL = dial("axe_dial", DialTools.Kind.AXE, 48, Rarity.RARE);
	public static final Item EISEN_DIAL = dial("eisen_dial", DialTools.Kind.EISEN, 48, Rarity.RARE);

	/** The cloud a Milky or Eisen Dial puts out. It melts away after a while and drops nothing. */
	public static final Block MILKY_CLOUD = registerBlock("milky_cloud", MilkyCloudBlock::new,
			BlockBehaviour.Properties.of().mapColor(MapColor.SNOW).strength(0.2f).sound(SoundType.WOOL)
					.noLootTable().pushReaction(PushReaction.POPPED));

	// ---- Forge ----

	/** Forged from Sea King fangs at a Swordsmith's Forge with the Tempering Anvil. */
	public static final Item SEA_KING_FANG_BLADE = register("sea_king_fang_blade", Item::new,
			new Item.Properties().sword(ToolMaterial.DIAMOND, 4.0f, -2.3f).rarity(Rarity.RARE));

	// ---- Cooking tier II (Brick Oven) ----

	/** Hatchan's octopus balls. Dig faster and breathe underwater. */
	public static final Item TAKOYAKI = dish("takoyaki", 8, 0.8f, false, 1,
			effect(MobEffects.HASTE, 4, 0), effect(MobEffects.WATER_BREATHING, 4, 0));
	/** A big bowl of noodles with Sea King broth. */
	public static final Item SEA_KING_RAMEN = dish("sea_king_ramen", 12, 1.0f, true, 1,
			effect(MobEffects.STRENGTH, 3, 1), effect(MobEffects.REGENERATION, 0.5f, 0));
	/** Wano millet dumplings. Lucky and light on your feet. */
	public static final Item KIBI_DANGO = dish("kibi_dango", 6, 0.6f, false, 1,
			effect(MobEffects.LUCK, 6, 0), effect(MobEffects.SPEED, 4, 0));

	// ---- Cooking tier III (Sanji's Kitchen) ----

	/** A slice of Big Mom's wedding cake. */
	public static final Item WEDDING_CAKE_SLICE = dish("wedding_cake_slice", 10, 1.2f, false, 2,
			effect(MobEffects.ABSORPTION, 4, 2), effect(MobEffects.REGENERATION, 0.75f, 1), effect(MobEffects.STRENGTH, 4, 0));
	/** Sea King roast glazed with Island Whale ambergris. */
	public static final Item AMBERGRIS_ROAST = dish("ambergris_roast", 20, 1.4f, false, 2,
			effect(MobEffects.STRENGTH, 6, 1), effect(MobEffects.RESISTANCE, 6, 1), effect(MobEffects.FIRE_RESISTANCE, 6, 0));
	/** Set alight with a Diable Jambe kick. */
	public static final Item DIABLE_FLAMBE = dish("diable_flambe", 14, 1.2f, false, 2,
			effect(MobEffects.FIRE_RESISTANCE, 8, 0), effect(MobEffects.SPEED, 4, 1), effect(MobEffects.STRENGTH, 4, 1));

	public static void initialize() {
		// Calling this loads the class, which registers everything above.
	}

	// ---- Helpers ----

	private static MobEffectInstance effect(Holder<MobEffect> effect, float minutes, int amplifier) {
		return new MobEffectInstance(effect, Math.round(minutes * MINUTE), amplifier);
	}

	private static Item dish(String name, int nutrition, float saturation, boolean bowl, int wellFed, MobEffectInstance... effects) {
		Item.Properties properties = new Item.Properties().stacksTo(16).rarity(wellFed >= 2 ? Rarity.RARE : Rarity.UNCOMMON)
				.food(new FoodProperties.Builder().nutrition(nutrition).saturationModifier(saturation).alwaysEdible().build());
		if (bowl) {
			properties.usingConvertsTo(Items.BOWL);
		}
		return register(name, p -> new DishItem(p, wellFed, List.of(effects)), properties);
	}

	private static Item dial(String name, DialTools.Kind kind, int uses, Rarity rarity) {
		return register(name, p -> new DialTools.DialToolItem(kind, p), new Item.Properties().durability(uses).rarity(rarity));
	}

	private static Item item(String name, Rarity rarity) {
		return register(name, Item::new, new Item.Properties().rarity(rarity));
	}

	private static Item register(String name, Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = factory.apply(properties.setId(key));
		Registry.register(BuiltInRegistries.ITEM, key, item);
		TAB_ITEMS.add(item);
		return item;
	}

	private static Block registerBlock(String name, Function<BlockBehaviour.Properties, Block> factory, BlockBehaviour.Properties properties) {
		ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, OnePieceMod.id(name));
		return Registry.register(BuiltInRegistries.BLOCK, key, factory.apply(properties.setId(key)));
	}
}
