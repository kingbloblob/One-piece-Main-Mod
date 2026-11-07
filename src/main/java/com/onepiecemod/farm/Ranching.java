package com.onepiecemod.farm;

import java.util.Map;
import java.util.function.Function;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.animal.sheep.Sheep;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.creature.CreatureEntity;
import com.onepiecemod.deco.DecoItems;

/**
 * What each ranch animal gives when it eats well at a Ranch Trough. Vanilla farm animals and the
 * gentle One Piece creatures (South Birds, Spot-billed Ducks, Cotton Candy Lambs, Drum reindeer...)
 * all count. Any other grown farm animal still leaves Ranch Manure for the fields.
 */
public final class Ranching {
	/** Items a trough takes as fodder. Hay bales count as 9. */
	public static final TagKey<Item> FODDER = TagKey.create(Registries.ITEM, OnePieceMod.id("ranch_fodder"));

	private static final Map<String, Function<LivingEntity, ItemStack>> PRODUCTS = Map.ofEntries(
			Map.entry("minecraft:cow", e -> new ItemStack(FarmItems.FRESH_MILK)),
			Map.entry("minecraft:mooshroom", e -> new ItemStack(FarmItems.FRESH_MILK)),
			Map.entry("minecraft:goat", e -> new ItemStack(FarmItems.FRESH_MILK)),
			Map.entry("minecraft:chicken", e -> new ItemStack(Items.EGG)),
			Map.entry("minecraft:sheep", Ranching::wool),
			Map.entry("minecraft:pig", e -> new ItemStack(FarmItems.TRUFFLE)),
			Map.entry("minecraft:rabbit", e -> new ItemStack(Items.RABBIT_HIDE)),
			Map.entry("minecraft:turtle", e -> new ItemStack(Items.SEAGRASS, 2)),
			Map.entry("onepiece:south_bird", e -> new ItemStack(FarmItems.SOUTH_BIRD_EGG)),
			Map.entry("onepiece:spot_billed_duck", e -> new ItemStack(FarmItems.DUCK_EGG)),
			Map.entry("onepiece:cotton_candy_lamb", e -> new ItemStack(DecoItems.COTTON_CANDY)),
			Map.entry("onepiece:drum_reindeer", e -> new ItemStack(FarmItems.FRESH_MILK)),
			Map.entry("onepiece:fuzza", e -> new ItemStack(Items.FEATHER, 2)),
			Map.entry("onepiece:hiking_bear", e -> new ItemStack(Items.HONEYCOMB)),
			Map.entry("onepiece:sauropod", e -> new ItemStack(FarmItems.RANCH_MANURE, 3)),
			Map.entry("onepiece:long_horse", e -> new ItemStack(FarmItems.RANCH_MANURE)));

	private Ranching() {
	}

	/** True for an animal a trough looks after: a grown vanilla farm animal or a gentle One Piece creature. */
	public static boolean isRanchAnimal(LivingEntity entity) {
		if (!entity.isAlive()) {
			return false;
		}
		if (entity instanceof Animal animal) {
			return !animal.isBaby();
		}
		return entity instanceof CreatureEntity && PRODUCTS.containsKey(typeId(entity));
	}

	/** What this animal gives today (manure if it has nothing of its own). */
	public static ItemStack product(LivingEntity entity) {
		Function<LivingEntity, ItemStack> product = PRODUCTS.get(typeId(entity));
		return product != null ? product.apply(entity) : new ItemStack(FarmItems.RANCH_MANURE);
	}

	static String typeId(LivingEntity entity) {
		return BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType()).toString();
	}

	private static ItemStack wool(LivingEntity entity) {
		if (entity instanceof Sheep sheep) {
			return new ItemStack(Items.WOOL.pick(sheep.getColor()));
		}
		return new ItemStack(Items.WOOL.white());
	}
}
