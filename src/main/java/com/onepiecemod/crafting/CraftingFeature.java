package com.onepiecemod.crafting;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.component.Consumable;
import net.minecraft.world.item.component.Consumables;
import net.minecraft.world.item.consume_effects.ApplyStatusEffectsConsumeEffect;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;

import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;

import com.onepiecemod.OnePieceMod;

/**
 * Crafting stations: themed work blocks that make the mod's gear, unlocked step by step.
 *
 * The ladder:
 *  1. Shipwright's Bench and Ship's Galley (East Blue) - made at a normal crafting table.
 *  2. Navigator's Desk (Grand Line) - Log Pose, Eternal Pose, Den Den Mushi.
 *  3. Seastone Workbench - built from Seastone; makes Seastone gear.
 *  4. Swordsmith's Forge - forges famous swords once your bounty is high enough.
 *
 * The recipes themselves are in src/main/resources/onepiece/station_recipes.json.
 */
public class CraftingFeature {
	public static final Map<Station, Block> STATIONS = new EnumMap<>(Station.class);
	private static final List<Item> TAB_ITEMS = new ArrayList<>();

	// ---- New items made at the stations ----

	/** Sanji's packed lunch: a big, filling meal. */
	public static final Item PIRATE_BENTO = registerItem("pirate_bento", Item::new,
			new Item.Properties().stacksTo(16)
					.food(new FoodProperties.Builder().nutrition(14).saturationModifier(1.2f).build()));

	/** A hearty stew from the Ship's Galley. */
	public static final Item SEA_KING_STEW = registerItem("sea_king_stew", Item::new,
			new Item.Properties().stacksTo(16)
					.food(new FoodProperties.Builder().nutrition(10).saturationModifier(0.9f).alwaysEdible().build()));

	/** Chopper's invention. See RumbleBallItem. */
	public static final Item RUMBLE_BALL = registerItem("rumble_ball", RumbleBallItem::new,
			new Item.Properties().stacksTo(16).rarity(Rarity.UNCOMMON));

	// ---- Sanji's dishes from the Ship's Galley: each one gives a buff ----

	/** Luffy's favourite. Strength for a minute. */
	public static final Item BONE_IN_MEAT = registerItem("bone_in_meat", Item::new,
			new Item.Properties().stacksTo(16)
					.food(food(12, 1.0f), dish(new MobEffectInstance(MobEffects.STRENGTH, 1200))));

	/** Breathe underwater and swim fast for a while. */
	public static final Item SEAFOOD_PAELLA = registerItem("seafood_paella", Item::new,
			new Item.Properties().stacksTo(16)
					.food(food(10, 0.9f), dish(new MobEffectInstance(MobEffects.WATER_BREATHING, 3600),
							new MobEffectInstance(MobEffects.DOLPHINS_GRACE, 600))));

	/** Made from Nami's mikans. Run faster. */
	public static final Item MIKAN_SORBET = registerItem("mikan_sorbet", Item::new,
			new Item.Properties().stacksTo(16)
					.food(new FoodProperties.Builder().nutrition(5).saturationModifier(0.5f).alwaysEdible().build(),
							dish(new MobEffectInstance(MobEffects.SPEED, 2400))));

	/** So hot that fire stops hurting. */
	public static final Item FIRE_CURRY = registerItem("fire_curry", Item::new,
			new Item.Properties().stacksTo(16)
					.food(food(10, 0.8f), dish(new MobEffectInstance(MobEffects.FIRE_RESISTANCE, 3600))));

	/** Chopper's remedy: a drink that heals over time. */
	public static final Item HERBAL_TEA = registerItem("herbal_tea", Item::new,
			new Item.Properties().stacksTo(16).usingConvertsTo(Items.GLASS_BOTTLE)
					.food(new FoodProperties.Builder().nutrition(2).saturationModifier(0.3f).alwaysEdible().build(),
							Consumables.defaultDrink().onConsume(effects(new MobEffectInstance(MobEffects.REGENERATION, 400))).build()));

	/** The crew's big meal before a fight. Needs a Cook in your crew to make. */
	public static final Item ALL_BLUE_FEAST = registerItem("all_blue_feast", Item::new,
			new Item.Properties().stacksTo(8).rarity(Rarity.UNCOMMON)
					.food(food(20, 1.2f), dish(new MobEffectInstance(MobEffects.ABSORPTION, 2400, 1),
							new MobEffectInstance(MobEffects.STRENGTH, 2400), new MobEffectInstance(MobEffects.RESISTANCE, 2400))));

	public static final ResourceKey<CreativeModeTab> TAB_KEY = ResourceKey.create(
			BuiltInRegistries.CREATIVE_MODE_TAB.key(), OnePieceMod.id("crafting")
	);

	public static void initialize() {
		STATIONS.put(Station.SHIPWRIGHT_BENCH, registerStation(Station.SHIPWRIGHT_BENCH, wood()));
		STATIONS.put(Station.SHIPS_GALLEY, registerStation(Station.SHIPS_GALLEY, stone()));
		STATIONS.put(Station.NAVIGATORS_DESK, registerStation(Station.NAVIGATORS_DESK, wood()));
		STATIONS.put(Station.SEASTONE_WORKBENCH, registerStation(Station.SEASTONE_WORKBENCH,
				BlockBehaviour.Properties.of().mapColor(MapColor.WATER).strength(5.0f, 12.0f)
						.sound(SoundType.METAL).requiresCorrectToolForDrops()));
		STATIONS.put(Station.SWORDSMITH_FORGE, registerStation(Station.SWORDSMITH_FORGE,
				stone().lightLevel(state -> 9)));

		StationPayloads.initialize();
		RecipeUnlocks.initialize();
		com.onepiecemod.keepsake.Keepsakes.initialize(); // How survival players get character posters and Vivre Cards.

		// Typos in station_recipes.json would only show up as a missing recipe, so list them in the log.
		ServerLifecycleEvents.SERVER_STARTED.register(server -> {
			for (String problem : StationRecipe.problems()) {
				OnePieceMod.LOGGER.warn("Station recipe problem: {}", problem);
			}
		});

		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY, FabricCreativeModeTab.builder()
				.icon(() -> new ItemStack(STATIONS.get(Station.SWORDSMITH_FORGE)))
				.title(Component.literal("One Piece: Crafting"))
				.displayItems((params, output) -> {
					for (Item item : TAB_ITEMS) {
						output.accept(item);
					}
				})
				.build());
	}

	// ---- Helpers ----

	private static BlockBehaviour.Properties wood() {
		return BlockBehaviour.Properties.of().mapColor(MapColor.WOOD).strength(2.5f).sound(SoundType.WOOD).ignitedByLava();
	}

	private static BlockBehaviour.Properties stone() {
		return BlockBehaviour.Properties.of().mapColor(MapColor.STONE).strength(3.5f).sound(SoundType.STONE).requiresCorrectToolForDrops();
	}

	private static FoodProperties food(int nutrition, float saturation) {
		return new FoodProperties.Builder().nutrition(nutrition).saturationModifier(saturation).build();
	}

	/** A food that gives these effects when eaten. */
	private static Consumable dish(MobEffectInstance... effects) {
		return Consumables.defaultFood().onConsume(effects(effects)).build();
	}

	private static ApplyStatusEffectsConsumeEffect effects(MobEffectInstance... effects) {
		return new ApplyStatusEffectsConsumeEffect(List.of(effects));
	}

	/** Registers a station block and the item you hold to place it. */
	private static Block registerStation(Station station, BlockBehaviour.Properties properties) {
		ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, OnePieceMod.id(station.id()));
		Block block = Registry.register(BuiltInRegistries.BLOCK, key, new StationBlock(station, properties.setId(key)));
		registerItem(station.id(), itemProperties -> new BlockItem(block, itemProperties), new Item.Properties().useBlockDescriptionPrefix());
		return block;
	}

	private static Item registerItem(String name, Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = factory.apply(properties.setId(key));
		Registry.register(BuiltInRegistries.ITEM, key, item);
		TAB_ITEMS.add(item);
		return item;
	}
}
