package com.onepiecemod.farm;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;
import java.util.function.Function;

import net.minecraft.ChatFormatting;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.block.Block;

import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.cuisine.CuisineEffects;
import com.onepiecemod.cuisine.DishItem;

/**
 * Seeds and crops, ranch goods, farm tools and the farm dishes.
 * Dish recipes are at the Ship's Galley (onepiece/station_recipes.json, written by tools/farm/gen_farm.py).
 */
public final class FarmItems {
	private static final int MINUTE = 1200;
	private static final List<Item> TAB_ITEMS = new ArrayList<>();
	public static final Map<IslandCrop, Item> SEEDS = new EnumMap<>(IslandCrop.class);
	public static final Map<IslandCrop, Item> PRODUCE = new EnumMap<>(IslandCrop.class);

	static {
		for (IslandCrop crop : IslandCrop.values()) {
			SEEDS.put(crop, register(crop.id + "_seeds", p -> new SeedItem(FarmBlocks.crop(crop), p, crop),
					new Item.Properties().useItemDescriptionPrefix()));
		}
		for (IslandCrop crop : IslandCrop.values()) {
			Item.Properties properties = new Item.Properties();
			if (crop.nutrition > 0) {
				properties.food(new FoodProperties.Builder().nutrition(crop.nutrition).saturationModifier(crop.saturation).build());
			}
			PRODUCE.put(crop, register(crop.id, p -> new ProduceItem(p, crop), properties));
		}
	}

	// ---- Blocks ----
	public static final Item SEED_VAULT = block(FarmBlocks.SEED_VAULT);
	public static final Item SPRINKLER = block(FarmBlocks.SPRINKLER);
	public static final Item DIAL_SPRINKLER = block(FarmBlocks.DIAL_SPRINKLER);
	public static final Item RANCH_TROUGH = block(FarmBlocks.RANCH_TROUGH);
	public static final Item SCARECROW = block(FarmBlocks.SCARECROW);

	// ---- Tools ----
	public static final Item WATERING_CAN = register("watering_can", WateringCanItem::new,
			new Item.Properties().stacksTo(1).durability(WateringCanItem.CAPACITY));
	public static final Item RANCH_MANURE = register("ranch_manure", ManureItem::new, new Item.Properties());

	// ---- Ranch goods ----
	public static final Item FRESH_MILK = register("fresh_milk", Item::new, new Item.Properties().stacksTo(16)
			.usingConvertsTo(Items.GLASS_BOTTLE)
			.food(new FoodProperties.Builder().nutrition(3).saturationModifier(0.4f).alwaysEdible().build()));
	public static final Item CHEESE = register("cheese", Item::new, new Item.Properties()
			.food(new FoodProperties.Builder().nutrition(5).saturationModifier(0.7f).build()));
	public static final Item TRUFFLE = register("truffle", Item::new, new Item.Properties().rarity(Rarity.UNCOMMON)
			.food(new FoodProperties.Builder().nutrition(2).saturationModifier(0.3f).build()));
	public static final Item SOUTH_BIRD_EGG = register("south_bird_egg", Item::new, new Item.Properties().stacksTo(16));
	public static final Item DUCK_EGG = register("duck_egg", Item::new, new Item.Properties().stacksTo(16));

	// ---- Dishes (Ship's Galley) ----
	public static final Item OMURICE = dish("omurice", 10, 0.9f, null, effect(MobEffects.HASTE, 12, 0));
	public static final Item CLOUD_BREAD = dish("cloud_bread", 7, 0.7f, null, effect(MobEffects.SLOW_FALLING, 10, 0),
			effect(MobEffects.JUMP_BOOST, 10, 0));
	public static final Item SAND_MELON_SORBET = dish("sand_melon_sorbet", 5, 0.5f, Items.BOWL,
			effect(MobEffects.FIRE_RESISTANCE, 15, 0), effect(MobEffects.SPEED, 6, 0));
	public static final Item FROST_TURNIP_STEW = dish("frost_turnip_stew", 9, 0.9f, Items.BOWL,
			effect(CuisineEffects.WARM_BELLY, 20, 0), effect(MobEffects.RESISTANCE, 8, 0));
	public static final Item TOTLAND_CHOCOLATE = dish("totland_chocolate", 6, 0.6f, null, effect(MobEffects.SPEED, 12, 0),
			effect(MobEffects.HEALTH_BOOST, 12, 0));
	public static final Item GHOST_PUMPKIN_PIE = dish("ghost_pumpkin_pie", 8, 0.7f, null, effect(MobEffects.NIGHT_VISION, 15, 0),
			effect(MobEffects.RESISTANCE, 10, 0));
	public static final Item DRESSROSA_PAELLA = dish("dressrosa_paella", 12, 1.0f, null, effect(MobEffects.STRENGTH, 12, 0));
	public static final Item GIANTS_ALE = dish("giants_ale", 4, 0.4f, Items.GLASS_BOTTLE, effect(MobEffects.STRENGTH, 8, 1),
			effect(MobEffects.HEALTH_BOOST, 15, 1));
	public static final Item MINK_TEA_CUP = dish("mink_tea_cup", 3, 0.3f, Items.GLASS_BOTTLE, effect(MobEffects.SPEED, 15, 0),
			effect(MobEffects.NIGHT_VISION, 15, 0));
	public static final Item SEA_GRAPE_SALAD = dish("sea_grape_salad", 6, 0.6f, Items.BOWL,
			effect(MobEffects.WATER_BREATHING, 15, 0), effect(MobEffects.DOLPHINS_GRACE, 8, 0));
	public static final Item KUJA_CURRY = dish("kuja_curry", 12, 1.0f, Items.BOWL, effect(MobEffects.FIRE_RESISTANCE, 15, 0),
			effect(MobEffects.STRENGTH, 10, 0));
	public static final Item JUNGLE_YAM_STEW = dish("jungle_yam_stew", 10, 0.9f, Items.BOWL,
			effect(MobEffects.HEALTH_BOOST, 15, 0), new MobEffectInstance(MobEffects.REGENERATION, MINUTE, 0));
	public static final Item BARATIE_CABBAGE_ROLLS = dish("baratie_cabbage_rolls", 9, 0.8f, null,
			effect(MobEffects.RESISTANCE, 10, 0), effect(MobEffects.ABSORPTION, 10, 0));
	public static final Item TRUFFLE_RISOTTO = dish("truffle_risotto", 12, 1.0f, Items.BOWL, effect(MobEffects.LUCK, 15, 1));
	public static final Item RANCH_BREAKFAST = dish("ranch_breakfast", 16, 1.2f, null, effect(MobEffects.RESISTANCE, 15, 0),
			effect(MobEffects.HEALTH_BOOST, 15, 0), effect(MobEffects.HASTE, 15, 0));

	public static final ResourceKey<CreativeModeTab> TAB_KEY = ResourceKey.create(
			BuiltInRegistries.CREATIVE_MODE_TAB.key(), OnePieceMod.id("farming"));

	private FarmItems() {
	}

	public static void initialize() {
		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY, FabricCreativeModeTab.builder()
				.icon(() -> new ItemStack(PRODUCE.get(IslandCrop.WANO_RICE)))
				.title(Component.literal("One Piece: Farming & Ranching"))
				.displayItems((params, output) -> TAB_ITEMS.forEach(output::accept))
				.build());
	}

	public static Item seeds(IslandCrop crop) {
		return SEEDS.get(crop);
	}

	public static Item produce(IslandCrop crop) {
		return PRODUCE.get(crop);
	}

	/** The island crop this seed plants, or null. */
	public static IslandCrop cropOfSeed(ItemStack stack) {
		return stack.getItem() instanceof SeedItem seed ? seed.crop : null;
	}

	// ---- Helpers ----

	private static MobEffectInstance effect(Holder<MobEffect> effect, int minutes, int amplifier) {
		return new MobEffectInstance(effect, minutes * MINUTE, amplifier);
	}

	private static Item dish(String name, int nutrition, float saturation, Item container, MobEffectInstance... effects) {
		Item.Properties properties = new Item.Properties().stacksTo(16)
				.food(new FoodProperties.Builder().nutrition(nutrition).saturationModifier(saturation).alwaysEdible().build());
		if (container != null) {
			properties.usingConvertsTo(container);
		}
		return register(name, p -> new DishItem(p, 0, List.of(effects)), properties);
	}

	private static Item block(Block block) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, BuiltInRegistries.BLOCK.getKey(block));
		Item item = new BlockItem(block, new Item.Properties().useBlockDescriptionPrefix().setId(key));
		Registry.register(BuiltInRegistries.ITEM, key, item);
		TAB_ITEMS.add(item);
		return item;
	}

	private static Item register(String name, Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = factory.apply(properties.setId(key));
		Registry.register(BuiltInRegistries.ITEM, key, item);
		TAB_ITEMS.add(item);
		return item;
	}

	/** Plants an island crop. The tooltip says where it grows best. */
	public static class SeedItem extends BlockItem {
		public final IslandCrop crop;

		public SeedItem(Block block, Properties properties, IslandCrop crop) {
			super(block, properties);
			this.crop = crop;
		}

		@Override
		public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> lines, TooltipFlag flag) {
			super.appendHoverText(stack, context, display, lines, flag);
			lines.accept(Component.literal("Grows best on " + crop.homeName).withStyle(ChatFormatting.GREEN));
			com.onepiecemod.season.Season loves = com.onepiecemod.season.Seasons.favourite(crop.id);
			if (loves != null) {
				lines.accept(Component.literal("Loves " + loves.title.toLowerCase() + ": grows 50% faster then").withStyle(loves.color));
			}
			lines.accept(Component.literal("Slow anywhere else. Bank it in a Seed Vault.").withStyle(ChatFormatting.DARK_GRAY));
		}
	}

	/** A harvested island crop. */
	public static class ProduceItem extends Item {
		public final IslandCrop crop;

		public ProduceItem(Properties properties, IslandCrop crop) {
			super(properties);
			this.crop = crop;
		}

		@Override
		public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> lines, TooltipFlag flag) {
			super.appendHoverText(stack, context, display, lines, flag);
			lines.accept(Component.literal("Grown on " + crop.homeName + ". Cook it at the Ship's Galley.").withStyle(ChatFormatting.GRAY));
		}
	}
}
