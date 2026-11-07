package com.onepiecemod.sea;

import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.storage.loot.LootPool;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.level.storage.loot.entries.LootItem;
import net.minecraft.world.level.storage.loot.predicates.LootItemRandomChanceCondition;

import net.fabricmc.fabric.api.loot.v3.LootTableEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.item.ModItems;

/**
 * Sometimes a Sea King has swallowed a Devil Fruit. This adds a very small chance of one random fruit
 * to its drops. The rest of its loot (meat, scales, Berries, books and treasure) is in
 * data/onepiece/loot_table/entities/sea_king.json.
 */
public class SeaKingLoot {
	/** 1.5% per Sea King: about 1 in 67. */
	public static final float DEVIL_FRUIT_CHANCE = 0.015f;

	private static final ResourceKey<LootTable> SEA_KING_LOOT = ResourceKey.create(Registries.LOOT_TABLE, OnePieceMod.id("entities/sea_king"));

	public static void initialize() {
		LootTableEvents.MODIFY.register((key, tableBuilder, source, registries) -> {
			if (key.equals(SEA_KING_LOOT)) {
				LootPool.Builder pool = LootPool.lootPool()
						.when(LootItemRandomChanceCondition.randomChance(DEVIL_FRUIT_CHANCE));
				for (Item fruit : ModItems.DEVIL_FRUITS.values()) {
					pool.add(LootItem.lootTableItem(fruit));
				}
				tableBuilder.withPool(pool);
			}
		});
	}
}
