package com.onepiecemod.workshop;

import java.util.List;

import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.storage.loot.LootPool;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.level.storage.loot.entries.LootItem;
import net.minecraft.world.level.storage.loot.predicates.LootItemKilledByPlayerCondition;
import net.minecraft.world.level.storage.loot.predicates.LootItemRandomChanceCondition;

import net.fabricmc.fabric.api.loot.v3.LootTableEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.resource.Resources;

/**
 * Rare drops that only one station can use. Added to the existing loot tables in code, so the
 * creature generators can keep rewriting their JSON files without losing these.
 *
 *  Sea King          -> Sea King Fang (12%)       Swordsmith's Forge: Tempering Anvil, Sea King Fang Blade
 *  Island Whale      -> Ambergris (20%)           Ship's Galley: Sanji's Kitchen, Ambergris Roast
 *  Punk Hazard Dragon-> Dragon Heartstone (8%)    Swordsmith's Forge: Dragon Hearth
 *  Pacifista         -> Pacifista Core (15%)      Shipwright's Bench: Franky's Workshop
 *  Sky Shark         -> Dial Shell (30%)          Navigator's Desk: the Dials
 * Creature drops need a player kill. Sky treasure chests can hold Dial Shells, lab chests a Pacifista Core.
 */
public class RareDrops {
	private record Drop(String table, Item item, float chance, boolean playerKill) {}

	public static void initialize() {
		List<Drop> drops = List.of(
				new Drop("entities/sea_king", WorkshopItems.SEA_KING_FANG, 0.12f, true),
				new Drop("entities/island_whale", WorkshopItems.AMBERGRIS, 0.20f, true),
				new Drop("entities/punk_hazard_dragon", WorkshopItems.DRAGON_HEARTSTONE, 0.08f, true),
				new Drop("entities/pacifista", WorkshopItems.PACIFISTA_CORE, 0.15f, true),
				new Drop("entities/sky_shark", Resources.DIAL_SHELL, 0.30f, true),
				new Drop("chests/sky_treasure", Resources.DIAL_SHELL, 0.50f, false),
				new Drop("chests/lab", WorkshopItems.PACIFISTA_CORE, 0.10f, false));

		LootTableEvents.MODIFY.register((key, tableBuilder, source, registries) -> {
			for (Drop drop : drops) {
				if (key.equals(ResourceKey.create(Registries.LOOT_TABLE, OnePieceMod.id(drop.table())))) {
					LootPool.Builder pool = LootPool.lootPool()
							.add(LootItem.lootTableItem(drop.item()))
							.when(LootItemRandomChanceCondition.randomChance(drop.chance()));
					if (drop.playerKill()) {
						pool.when(LootItemKilledByPlayerCondition.killedByPlayer());
					}
					tableBuilder.withPool(pool);
				}
			}
		});
	}
}
