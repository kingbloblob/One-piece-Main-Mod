package com.onepiecemod.voyage;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.ChestBlock;
import net.minecraft.world.level.block.LanternBlock;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.level.storage.loot.parameters.LootContextParamSets;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.ship.HelmBlock;
import com.onepiecemod.ship.ShipFeature;
import com.onepiecemod.ship.ShipLayout;
import com.onepiecemod.shipcombat.ShipDesigns;

/**
 * The blocks of the wandering ships (see WanderingShips):
 * - a merchant cog with striped sails and a deck full of cargo,
 * - a derelict: a battered pirate sloop with torn sails, left to drift,
 * - a ghost ship: a pirate galleon with grey rags for sails, cobwebs and soul lanterns.
 * Their chests are packed when the ship appears (a ship's chest can't roll its loot table while sailing).
 */
final class WanderingDesigns {
	static final ResourceKey<LootTable> MERCHANT_LOOT = loot("voyage/merchant_hold");
	static final ResourceKey<LootTable> DERELICT_LOOT = loot("voyage/derelict");
	static final ResourceKey<LootTable> GHOST_LOOT = loot("voyage/ghost_ship");
	private static final float WATERLINE = 1.5f;

	private WanderingDesigns() {
	}

	private static ResourceKey<LootTable> loot(String path) {
		return ResourceKey.create(Registries.LOOT_TABLE, OnePieceMod.id(path));
	}

	/** A broad, slow cog: two masts with blue-and-white sails, barrels and crates on deck. */
	static ShipLayout merchant(ServerLevel level) {
		List<ShipLayout.ShipBlock> blocks = new ArrayList<>();
		BlockState keel = Blocks.OAK_PLANKS.defaultBlockState();
		BlockState hull = Blocks.STRIPPED_OAK_LOG.defaultBlockState();
		BlockState trim = Blocks.WOOL.blue().defaultBlockState();
		BlockState deck = Blocks.BIRCH_PLANKS.defaultBlockState();
		BlockState rail = Blocks.OAK_FENCE.defaultBlockState();
		BlockState mast = Blocks.OAK_LOG.defaultBlockState();
		BlockState white = Blocks.WOOL.white().defaultBlockState();
		BlockState blue = Blocks.WOOL.lightBlue().defaultBlockState();

		for (int z = -6; z <= 6; z++) {
			for (int x = -1; x <= 1; x++) {
				add(blocks, x, 0, z, keel);
			}
		}
		for (int z = -7; z <= 7; z++) {
			int half = Math.abs(z) >= 7 ? 1 : Math.abs(z) >= 5 ? 2 : 3;
			for (int x = -half; x <= half; x++) {
				boolean edge = Math.abs(x) == half || Math.abs(z) == 7;
				add(blocks, x, 1, z, edge ? hull : deck);
				if (edge) {
					add(blocks, x, 2, z, trim);
					add(blocks, x, 3, z, rail);
				}
			}
		}
		for (int y = 2; y <= 11; y++) {
			add(blocks, 0, y, -2, mast);
		}
		for (int y = 2; y <= 9; y++) {
			add(blocks, 0, y, 3, mast);
		}
		for (int x = -3; x <= 3; x++) {
			for (int y = 5; y <= 10; y++) {
				add(blocks, x, y, -1, (x + 3) % 2 == 0 ? white : blue);
			}
			if (Math.abs(x) <= 2) {
				for (int y = 5; y <= 8; y++) {
					add(blocks, x, y, 4, (x + 2) % 2 == 0 ? white : blue);
				}
			}
		}
		// Cargo: barrels and crates (the crates are just wood blocks), and the hold's chest.
		add(blocks, 2, 2, 1, Blocks.BARREL.defaultBlockState());
		add(blocks, -2, 2, 1, Blocks.BARREL.defaultBlockState());
		add(blocks, 2, 2, 2, Blocks.BARREL.defaultBlockState());
		add(blocks, -2, 2, 0, Blocks.SPRUCE_PLANKS.defaultBlockState());
		add(blocks, -2, 3, 0, Blocks.HAY_BLOCK.defaultBlockState());
		add(blocks, 1, 2, 5, Blocks.SPRUCE_PLANKS.defaultBlockState());
		add(blocks, 0, 2, 6, Blocks.LANTERN.defaultBlockState());
		BlockPos helm = new BlockPos(0, 2, -5);
		add(blocks, helm.getX(), helm.getY(), helm.getZ(), ShipFeature.HELM.defaultBlockState().setValue(HelmBlock.FACING, Direction.SOUTH));
		packedChest(blocks, level, -1, 2, 5, Direction.EAST, MERCHANT_LOOT);
		return new ShipLayout(blocks, List.of(), helm, Direction.SOUTH, WATERLINE);
	}

	/** A pirate sloop nobody has sailed for months: holes in the deck, torn sails, the cannons gone. */
	static ShipLayout derelict(ServerLevel level) {
		RandomSource random = level.getRandom();
		ShipLayout base = ShipDesigns.pirateSloop();
		List<ShipLayout.ShipBlock> blocks = new ArrayList<>();
		for (ShipLayout.ShipBlock block : base.blocks) {
			BlockState state = block.state();
			if (state.is(ShipFeature.CANNON) || state.is(Blocks.CHEST)) {
				continue;
			}
			if (state.is(net.minecraft.tags.BlockTags.WOOL) && random.nextFloat() < 0.35f) {
				continue; // Torn sails.
			}
			if (block.pos().getY() == 2 && state.is(Blocks.DARK_OAK_FENCE) && random.nextFloat() < 0.4f) {
				continue; // Broken rails.
			}
			if (state.is(Blocks.DARK_OAK_PLANKS) && block.pos().getY() == 1 && random.nextFloat() < 0.25f) {
				state = Blocks.MOSSY_COBBLESTONE.defaultBlockState(); // Barnacles and weed on the hull.
			}
			blocks.add(new ShipLayout.ShipBlock(block.pos(), state, block.nbt()));
		}
		add(blocks, -1, 2, 2, Blocks.COBWEB.defaultBlockState());
		add(blocks, 1, 2, -1, Blocks.BARREL.defaultBlockState());
		packedChest(blocks, level, 1, 2, 3, Direction.WEST, DERELICT_LOOT);
		return new ShipLayout(blocks, List.of(), base.helm, base.bow, base.waterline);
	}

	/** A galleon crewed by the dead: grey rags for sails, cobwebs in the rigging, soul lanterns on the rails. */
	static ShipLayout ghost(ServerLevel level) {
		RandomSource random = level.getRandom();
		ShipLayout base = ShipDesigns.pirateGalleon();
		List<ShipLayout.ShipBlock> blocks = new ArrayList<>();
		for (ShipLayout.ShipBlock block : base.blocks) {
			BlockState state = block.state();
			if (state.is(Blocks.CHEST)) {
				continue;
			}
			if (state.is(net.minecraft.tags.BlockTags.WOOL)) {
				if (block.pos().getY() >= 5 && random.nextFloat() < 0.3f) {
					continue; // Holes in the sails.
				}
				state = block.pos().getY() <= 3 ? Blocks.WOOL.black().defaultBlockState()
						: random.nextFloat() < 0.6f ? Blocks.WOOL.lightGray().defaultBlockState() : Blocks.WOOL.gray().defaultBlockState();
			} else if (state.is(Blocks.SPRUCE_PLANKS)) {
				state = random.nextFloat() < 0.2f ? Blocks.DARK_OAK_PLANKS.defaultBlockState() : Blocks.PALE_OAK_PLANKS.defaultBlockState();
			} else if (state.is(Blocks.SPRUCE_LOG)) {
				state = Blocks.PALE_OAK_LOG.defaultBlockState();
			}
			blocks.add(new ShipLayout.ShipBlock(block.pos(), state, block.nbt()));
		}
		for (int[] p : new int[][] {{0, 12, -2}, {1, 7, 4}, {-2, 10, -2}, {2, 2, -3}, {-2, 2, 3}}) {
			add(blocks, p[0], p[1], p[2], Blocks.COBWEB.defaultBlockState());
		}
		for (int[] p : new int[][] {{3, 4, -6}, {-3, 4, 2}, {2, 4, 7}, {-2, 4, -7}}) {
			add(blocks, p[0], p[1], p[2], Blocks.SOUL_LANTERN.defaultBlockState().setValue(LanternBlock.HANGING, false));
		}
		packedChest(blocks, level, 1, 2, 6, Direction.WEST, GHOST_LOOT);
		packedChest(blocks, level, -1, 2, 6, Direction.EAST, GHOST_LOOT);
		return new ShipLayout(blocks, List.of(), base.helm, base.bow, base.waterline);
	}

	// ---- Helpers ----

	private static void add(List<ShipLayout.ShipBlock> blocks, int x, int y, int z, BlockState state) {
		BlockPos pos = new BlockPos(x, y, z);
		blocks.removeIf(block -> block.pos().equals(pos));
		blocks.add(new ShipLayout.ShipBlock(pos, state, Optional.empty()));
	}

	/** A chest already full of loot, saved the way a ship keeps its chests. */
	private static void packedChest(List<ShipLayout.ShipBlock> blocks, ServerLevel level, int x, int y, int z, Direction facing,
			ResourceKey<LootTable> table) {
		BlockState state = Blocks.CHEST.defaultBlockState().setValue(ChestBlock.FACING, facing);
		ChestBlockEntity chest = new ChestBlockEntity(BlockPos.ZERO, state);
		LootTable loot = level.getServer().reloadableRegistries().getLootTable(table);
		LootParams params = new LootParams.Builder(level).withParameter(LootContextParams.ORIGIN, Vec3.ZERO).create(LootContextParamSets.CHEST);
		RandomSource random = level.getRandom();
		List<ItemStack> items = loot.getRandomItems(params);
		for (ItemStack stack : items) {
			// Scatter the loot around the chest like a real loot chest.
			for (int tries = 0; tries < 8; tries++) {
				int slot = random.nextInt(chest.getContainerSize());
				if (chest.getItem(slot).isEmpty()) {
					chest.setItem(slot, stack);
					break;
				}
			}
		}
		CompoundTag nbt = chest.saveWithFullMetadata(level.registryAccess());
		BlockPos pos = new BlockPos(x, y, z);
		blocks.removeIf(block -> block.pos().equals(pos));
		blocks.add(new ShipLayout.ShipBlock(pos, state, Optional.of(nbt)));
	}
}
