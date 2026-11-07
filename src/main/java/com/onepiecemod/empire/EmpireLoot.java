package com.onepiecemod.empire;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.resources.ResourceKey;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;

import net.fabricmc.fabric.api.loot.v3.LootTableEvents;

/**
 * Title holders get more loot from mobs they kill and chests they open:
 * Emperor +25%, Pirate King +50%, King of the World +100% (every stack doubled).
 */
public class EmpireLoot {
	public static void initialize() {
		LootTableEvents.MODIFY_DROPS.register((table, context, drops) -> {
			String path = table.unwrapKey().map(ResourceKey::identifier).map(Object::toString).orElse("");
			Player player = null;
			if (path.contains(":entities/")) {
				player = context.getOptional(LootContextParams.LAST_DAMAGE_PLAYER);
			} else if (path.contains(":chests/")) {
				Entity opener = context.getOptional(LootContextParams.THIS_ENTITY);
				player = opener instanceof Player p ? p : null;
			}
			if (player == null) {
				return;
			}
			float bonus = EmpireData.title(player).lootBonus;
			if (bonus <= 0) {
				return;
			}
			RandomSource random = context.getRandom();
			List<ItemStack> extra = new ArrayList<>();
			for (ItemStack stack : drops) {
				// For example 25% of a stack of 4 is 1 more item; 25% of 1 item is a 1-in-4 chance of one more.
				float wanted = stack.getCount() * bonus;
				int count = (int) wanted + (random.nextFloat() < wanted - (int) wanted ? 1 : 0);
				if (count > 0 && !stack.isEmpty()) {
					extra.add(stack.copyWithCount(count));
				}
			}
			drops.addAll(extra);
		});
	}
}
