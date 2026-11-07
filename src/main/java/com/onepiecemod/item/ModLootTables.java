package com.onepiecemod.item;

import java.util.Optional;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.LeavesBlock;
import net.minecraft.world.level.storage.loot.LootPool;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.level.storage.loot.entries.LootItem;
import net.minecraft.world.level.storage.loot.predicates.LootItemRandomChanceCondition;

import net.fabricmc.fabric.api.loot.v3.LootTableEvents;

/**
 * Adds Devil Fruits to the drops of other blocks. A leaves block drops one random fruit.
 */
public class ModLootTables {
	/** 0.05% chance, written as a fraction: 0.05 / 100 = 0.0005 (about 1 in 2,000 leaves). The settings file can change it. */
	public static final float DEVIL_FRUIT_LEAF_CHANCE = 0.0005f;

	public static void initialize() {
		// Runs once for every loot table while the world is loading.
		LootTableEvents.MODIFY.register((key, tableBuilder, source, registries) -> {
			if (isLeavesLootTable(key)) {
				// A separate pool, so the leaves still drop their normal saplings and sticks.
				// Every fruit has the same chance to be the one that drops.
				LootPool.Builder pool = LootPool.lootPool()
						.when(LootItemRandomChanceCondition.randomChance(com.onepiecemod.config.ModConfig.fruitLeafChance()));
				for (Item fruit : ModItems.DEVIL_FRUITS.values()) {
					pool.add(LootItem.lootTableItem(fruit));
				}

				tableBuilder.withPool(pool);
			}
		});
	}

	// True for the loot table of any leaves block, including leaves added by other mods.
	private static boolean isLeavesLootTable(ResourceKey<LootTable> key) {
		for (Block block : BuiltInRegistries.BLOCK) {
			if (block instanceof LeavesBlock) {
				Optional<ResourceKey<LootTable>> lootTable = block.getLootTable();
				if (lootTable.isPresent() && lootTable.get().equals(key)) {
					return true;
				}
			}
		}
		return false;
	}
}
