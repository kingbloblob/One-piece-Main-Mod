package com.onepiecemod.farm;

import java.util.List;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;

import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;

/** Breaking grass, ferns and wild plants on an island sometimes turns up that island's crop seeds. */
final class WildSeeds {
	/** 1 in this many plants broken on a crop's home island drops a seed. */
	private static final int ONE_IN = 12;

	private WildSeeds() {
	}

	static void initialize() {
		PlayerBlockBreakEvents.AFTER.register((level, player, pos, state, blockEntity) -> {
			if (!(level instanceof ServerLevel server) || player.isCreative() || !state.is(BlockTags.REPLACEABLE_BY_TREES)
					|| server.getRandom().nextInt(ONE_IN) != 0) {
				return;
			}
			List<IslandCrop> crops = IslandCrop.homeCrops(server, pos);
			if (!crops.isEmpty()) {
				IslandCrop crop = crops.get(server.getRandom().nextInt(crops.size()));
				Block.popResource(server, pos, new ItemStack(FarmItems.seeds(crop)));
			}
		});
	}
}
