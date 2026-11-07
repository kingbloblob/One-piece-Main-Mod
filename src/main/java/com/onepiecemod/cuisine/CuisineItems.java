package com.onepiecemod.cuisine;

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
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.Consumables;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.item.consume_effects.ApplyStatusEffectsConsumeEffect;

import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;

import com.onepiecemod.OnePieceMod;

/** The fish, Sanji's dishes and the All Blue compass. Recipes are in onepiece/station_recipes.json (Ship's Galley). */
public class CuisineItems {
	private static final int MINUTE = 1200;
	private static final List<Item> TAB_ITEMS = new ArrayList<>();
	public static final Map<Fish, Item> FISH = new EnumMap<>(Fish.class);

	static {
		for (Fish fish : Fish.values()) {
			FISH.put(fish, register(fish.id, properties -> new FishItem(properties, fish), fishProperties(fish)));
		}
	}

	/** Any raw fish cooked over a fire, in a furnace or smoker. */
	public static final Item GRILLED_FISH = register("grilled_fish", Item::new,
			new Item.Properties().food(new FoodProperties.Builder().nutrition(6).saturationModifier(0.8f).build()));

	// ---- Sanji's dishes (Ship's Galley) ----

	public static final Item SEA_BREAM_SASHIMI = dish("sea_bream_sashimi", 6, 0.8f, false, 0,
			effect(MobEffects.LUCK, 10, 0));
	public static final Item LOBSTER_BISQUE = dish("lobster_bisque", 8, 0.9f, true, 0,
			effect(MobEffects.RESISTANCE, 8, 0));
	public static final Item SEAFOOD_FRIED_RICE = dish("seafood_fried_rice", 12, 1.0f, false, 0,
			effect(MobEffects.HEALTH_BOOST, 15, 0));
	public static final Item EEL_KABAYAKI = dish("eel_kabayaki", 8, 0.8f, false, 0,
			effect(MobEffects.SPEED, 10, 0));
	public static final Item SEA_KING_BARBECUE = dish("sea_king_barbecue", 14, 1.2f, false, 0,
			effect(MobEffects.STRENGTH, 15, 0), effect(MobEffects.HEALTH_BOOST, 15, 0));
	public static final Item ELEPHANT_TUNA_SUSHI = dish("elephant_tuna_sushi", 10, 1.0f, false, 0,
			effect(MobEffects.HASTE, 15, 0), effect(MobEffects.WATER_BREATHING, 15, 0));
	public static final Item PUFFER_HOT_POT = dish("puffer_hot_pot", 10, 1.0f, true, 0,
			effect(MobEffects.RESISTANCE, 12, 0), new MobEffectInstance(MobEffects.REGENERATION, MINUTE, 0));
	public static final Item RAINBOW_SNAPPER_CARPACCIO = dish("rainbow_snapper_carpaccio", 8, 0.8f, false, 0,
			effect(MobEffects.SPEED, 12, 0), effect(MobEffects.JUMP_BOOST, 12, 0));
	public static final Item SWORDFISH_STEAK = dish("swordfish_steak", 12, 1.0f, false, 0,
			effect(MobEffects.STRENGTH, 8, 1));
	public static final Item ANGLER_LANTERN_SOUP = dish("angler_lantern_soup", 8, 0.8f, true, 0,
			effect(MobEffects.NIGHT_VISION, 20, 0), effect(MobEffects.CONDUIT_POWER, 10, 0));
	public static final Item GLOWFIN_STEW = dish("glowfin_stew", 8, 0.8f, true, 0,
			effect(MobEffects.WATER_BREATHING, 20, 0), effect(MobEffects.DOLPHINS_GRACE, 10, 0), effect(MobEffects.NIGHT_VISION, 20, 0));
	public static final Item SKY_FISH_SKEWERS = dish("sky_fish_skewers", 8, 0.8f, false, 0,
			effect(MobEffects.SLOW_FALLING, 10, 0), effect(MobEffects.JUMP_BOOST, 10, 1));
	public static final Item GOLDEN_KOI_ODEN = dish("golden_koi_oden", 10, 1.0f, true, 0,
			effect(MobEffects.RESISTANCE, 15, 0), effect(MobEffects.FIRE_RESISTANCE, 15, 0));
	public static final Item FROSTFIN_HOT_POT = dish("frostfin_hot_pot", 10, 1.0f, true, 0,
			effect(CuisineEffects.WARM_BELLY, 20, 0), new MobEffectInstance(MobEffects.REGENERATION, 600, 0));
	public static final Item SANDORA_CATFISH_KEBAB = dish("sandora_catfish_kebab", 8, 0.8f, false, 0,
			effect(MobEffects.FIRE_RESISTANCE, 15, 0), effect(MobEffects.SPEED, 8, 0));
	public static final Item GHOST_FISH_SOUP = dish("ghost_fish_soup", 6, 0.6f, true, 0,
			effect(MobEffects.INVISIBILITY, 5, 0), effect(MobEffects.NIGHT_VISION, 15, 0));
	/** Sanji's dream meal, made from fish only the All Blue has. Needs a Cook in your crew. */
	public static final Item ALL_BLUE_FULL_COURSE = register("all_blue_full_course",
			properties -> new DishItem(properties, 1, List.of(effect(MobEffects.STRENGTH, 20, 0), effect(MobEffects.RESISTANCE, 20, 0),
					effect(MobEffects.SPEED, 20, 0), effect(MobEffects.HEALTH_BOOST, 20, 1), effect(MobEffects.LUCK, 20, 0),
					new MobEffectInstance(MobEffects.REGENERATION, MINUTE, 0))),
			new Item.Properties().stacksTo(8).rarity(Rarity.EPIC)
					.food(new FoodProperties.Builder().nutrition(20).saturationModifier(1.4f).alwaysEdible().build()));

	/** Points the way to the All Blue. Made at the Navigator's Desk from one fish of every sea. */
	public static final Item ALL_BLUE_COMPASS = register("all_blue_compass", AllBlueCompassItem::new,
			new Item.Properties().stacksTo(1).rarity(Rarity.RARE));

	public static final ResourceKey<CreativeModeTab> TAB_KEY = ResourceKey.create(
			BuiltInRegistries.CREATIVE_MODE_TAB.key(), OnePieceMod.id("cuisine"));

	public static void initialize() {
		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY, FabricCreativeModeTab.builder()
				.icon(() -> new ItemStack(FISH.get(Fish.ALL_BLUE_KINGFISH)))
				.title(Component.literal("One Piece: Fishing & Cooking"))
				.displayItems((params, output) -> TAB_ITEMS.forEach(output::accept))
				.build());
	}

	public static Item fish(Fish fish) {
		return FISH.get(fish);
	}

	// ---- Helpers ----

	private static Item.Properties fishProperties(Fish fish) {
		Item.Properties properties = new Item.Properties();
		FoodProperties food = new FoodProperties.Builder().nutrition(fish.nutrition).saturationModifier(fish.saturation).build();
		if (fish == Fish.GRAND_LINE_PUFFER) {
			// Raw puffer is poisonous, like the vanilla pufferfish. Cook it into a hot pot instead.
			return properties.food(food, Consumables.defaultFood().onConsume(new ApplyStatusEffectsConsumeEffect(List.of(
					new MobEffectInstance(MobEffects.POISON, 600, 1), new MobEffectInstance(MobEffects.NAUSEA, 300, 0)))).build());
		}
		if (fish.where == Fish.Where.ALL_BLUE) {
			properties.rarity(Rarity.RARE);
		}
		return properties.food(food);
	}

	private static MobEffectInstance effect(Holder<MobEffect> effect, int minutes, int amplifier) {
		return new MobEffectInstance(effect, minutes * MINUTE, amplifier);
	}

	private static Item dish(String name, int nutrition, float saturation, boolean bowl, int wellFed, MobEffectInstance... effects) {
		Item.Properties properties = new Item.Properties().stacksTo(16)
				.food(new FoodProperties.Builder().nutrition(nutrition).saturationModifier(saturation).alwaysEdible().build());
		if (bowl) {
			properties.usingConvertsTo(Items.BOWL);
		}
		return register(name, p -> new DishItem(p, wellFed, List.of(effects)), properties);
	}

	private static Item register(String name, Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = factory.apply(properties.setId(key));
		Registry.register(BuiltInRegistries.ITEM, key, item);
		TAB_ITEMS.add(item);
		return item;
	}

	/** A raw fish. Its tooltip says where it bites. */
	public static class FishItem extends Item {
		private final Fish fish;

		public FishItem(Properties properties, Fish fish) {
			super(properties);
			this.fish = fish;
		}

		public Fish fish() {
			return fish;
		}

		@Override
		public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> lines, TooltipFlag flag) {
			super.appendHoverText(stack, context, display, lines, flag);
			lines.accept(Component.literal("Bites in " + fish.habitat()).withStyle(ChatFormatting.GRAY));
		}
	}
}
