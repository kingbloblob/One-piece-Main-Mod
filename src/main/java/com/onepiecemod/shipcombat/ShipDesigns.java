package com.onepiecemod.shipcombat;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.ChestBlock;
import net.minecraft.world.level.block.state.BlockState;

import com.onepiecemod.bounty.MarineWarship;
import com.onepiecemod.ship.DecorBlock;
import com.onepiecemod.ship.HelmBlock;
import com.onepiecemod.ship.ShipFeature;
import com.onepiecemod.ship.ShipLayout;
import com.onepiecemod.ship.ShipTemplates;

/**
 * The enemy ships, built from blocks in code (bow pointing south, +Z), like MarineWarship.
 * Each has Cannon blocks on both sides and a treasure chest in the hold that you keep if you capture the ship.
 */
public class ShipDesigns {
	private static final float WATERLINE = 1.5f;

	/** A ship picked for an encounter: its blocks and the name on its name tag. */
	public record Pick(ShipLayout layout, String name) {
	}

	/**
	 * A Marine ship as it looks in the show (templates marine_warship / marine_battleship from ShipTemplates).
	 * Falls back to the old block-code warship if the templates are missing.
	 */
	public static Pick marine(ServerLevel level, boolean battleship) {
		String id = battleship ? "marine_battleship" : "marine_warship";
		ShipLayout layout = ShipTemplates.layout(level, id);
		if (layout != null) {
			ShipTemplates.Spec spec = ShipTemplates.spec(level.getServer(), id);
			return new Pick(layout, spec == null ? (battleship ? "Marine Battleship" : "Marine Warship") : spec.displayName().getString());
		}
		return new Pick(marine(battleship), battleship ? "Marine Battleship" : "Marine Warship");
	}

	/**
	 * A famous pirate ship for this tier (Buggy's Big Top in the East Blue, Law's Polar Tang on the Grand Line, Shanks'
	 * Red Force in the New World...), or the plain sloop/galleon if no famous ship sails at this tier.
	 */
	public static Pick pirate(ServerLevel level, int tier, RandomSource random) {
		List<ShipTemplates.Spec> famous = ShipTemplates.forTier(level.getServer(), "pirate", tier);
		if (!famous.isEmpty()) {
			ShipTemplates.Spec spec = famous.get(random.nextInt(famous.size()));
			ShipLayout layout = ShipTemplates.layout(level, spec.id);
			if (layout != null) {
				return new Pick(layout, spec.displayName().getString());
			}
		}
		boolean galleon = tier >= 2;
		return new Pick(galleon ? pirateGalleon() : pirateSloop(), CREWS[random.nextInt(CREWS.length)] + (galleon ? " Galleon" : " Sloop"));
	}

	/** Made-up pirate crews for the plain ships' names. */
	private static final String[] CREWS = {
			"Bluejaw Pirates'", "Red Gull Pirates'", "Saltbones Pirates'", "Iron Hook Pirates'", "Crossbone Pirates'",
			"Black Tide Pirates'", "Rumble Barrel Pirates'", "Sea Wolf Pirates'", "Thunder Kraken Pirates'", "Golden Fang Pirates'"
	};

	/** The old block-code raid warship with a loot chest, and two extra cannons for the tougher Battleship. */
	public static ShipLayout marine(boolean battleship) {
		ShipLayout base = MarineWarship.layout();
		List<ShipLayout.ShipBlock> blocks = new ArrayList<>(base.blocks);
		if (battleship) {
			add(blocks, 2, 3, 4, cannon(Direction.EAST));
			add(blocks, -2, 3, 4, cannon(Direction.WEST));
		}
		addChest(blocks, 1, 2, 3, Direction.WEST, "onepiece:chests/marine");
		return new ShipLayout(blocks, base.flags, base.helm, base.bow, base.waterline);
	}

	/** A small, quick pirate ship: dark wood, one black sail with a white skull, two cannons a side. */
	public static ShipLayout pirateSloop() {
		List<ShipLayout.ShipBlock> blocks = new ArrayList<>();
		BlockState keel = Blocks.DARK_OAK_PLANKS.defaultBlockState();
		BlockState hull = Blocks.DARK_OAK_PLANKS.defaultBlockState();
		BlockState rail = Blocks.DARK_OAK_FENCE.defaultBlockState();
		BlockState deck = Blocks.SPRUCE_PLANKS.defaultBlockState();
		BlockState mast = Blocks.DARK_OAK_LOG.defaultBlockState();
		BlockState sail = Blocks.WOOL.black().defaultBlockState();
		BlockState skull = Blocks.WOOL.white().defaultBlockState();

		for (int z = -4; z <= 4; z++) {
			add(blocks, 0, 0, z, keel);
		}
		for (int z = -5; z <= 5; z++) {
			int halfWidth = Math.abs(z) >= 4 ? 1 : 2;
			for (int x = -halfWidth; x <= halfWidth; x++) {
				boolean edge = Math.abs(x) == halfWidth || Math.abs(z) == 5;
				add(blocks, x, 1, z, edge ? hull : deck);
				if (edge && Math.abs(z) != 2) {
					add(blocks, x, 2, z, rail);
				} else if (edge) {
					add(blocks, x, 2, z, hull);
				}
			}
		}
		for (int y = 2; y <= 9; y++) {
			add(blocks, 0, y, 0, mast);
		}
		for (int x = -2; x <= 2; x++) {
			for (int y = 4; y <= 8; y++) {
				add(blocks, x, y, 1, sail);
			}
		}
		// A little skull on the sail.
		for (int[] p : new int[][] {{-1, 7}, {0, 7}, {1, 7}, {-1, 6}, {1, 6}, {0, 5}}) {
			add(blocks, p[0], p[1], 1, skull);
		}
		for (int z : new int[] {-2, 2}) {
			add(blocks, 2, 3, z, cannon(Direction.EAST));
			add(blocks, -2, 3, z, cannon(Direction.WEST));
		}
		BlockPos helm = new BlockPos(0, 2, -3);
		add(blocks, helm.getX(), helm.getY(), helm.getZ(), ShipFeature.HELM.defaultBlockState().setValue(HelmBlock.FACING, Direction.SOUTH));
		addChest(blocks, 1, 2, 3, Direction.WEST, "onepiece:chests/pirate");
		return new ShipLayout(blocks, List.of(), helm, Direction.SOUTH, WATERLINE);
	}

	/** A big pirate galleon: tall red sails on two masts and three cannons a side. Found in rougher seas. */
	public static ShipLayout pirateGalleon() {
		List<ShipLayout.ShipBlock> blocks = new ArrayList<>();
		BlockState keel = Blocks.DARK_OAK_PLANKS.defaultBlockState();
		BlockState hull = Blocks.STRIPPED_DARK_OAK_LOG.defaultBlockState();
		BlockState stripe = Blocks.WOOL.red().defaultBlockState();
		BlockState deck = Blocks.SPRUCE_PLANKS.defaultBlockState();
		BlockState mast = Blocks.SPRUCE_LOG.defaultBlockState();
		BlockState sail = Blocks.WOOL.red().defaultBlockState();
		BlockState flag = Blocks.WOOL.black().defaultBlockState();

		for (int z = -7; z <= 7; z++) {
			for (int x = -1; x <= 1; x++) {
				add(blocks, x, 0, z, keel);
			}
		}
		for (int z = -8; z <= 8; z++) {
			int halfWidth = Math.abs(z) >= 8 ? 1 : Math.abs(z) >= 6 ? 2 : 3;
			for (int x = -halfWidth; x <= halfWidth; x++) {
				boolean edge = Math.abs(x) == halfWidth || Math.abs(z) == 8;
				add(blocks, x, 1, z, edge ? hull : deck);
				if (edge) {
					add(blocks, x, 2, z, stripe);
					add(blocks, x, 3, z, hull);
				}
			}
		}
		for (int y = 2; y <= 13; y++) {
			add(blocks, 0, y, -3, mast);
		}
		for (int y = 2; y <= 11; y++) {
			add(blocks, 0, y, 3, mast);
		}
		for (int x = -3; x <= 3; x++) {
			for (int y = 6; y <= 11; y++) {
				add(blocks, x, y, -2, sail);
			}
			for (int y = 5; y <= 9; y++) {
				if (Math.abs(x) <= 2) {
					add(blocks, x, y, 4, sail);
				}
			}
		}
		add(blocks, 0, 14, -3, flag);
		add(blocks, 0, 13, -4, flag);
		for (int z : new int[] {-4, 0, 4}) {
			add(blocks, 3, 4, z, cannon(Direction.EAST));
			add(blocks, -3, 4, z, cannon(Direction.WEST));
		}
		BlockPos helm = new BlockPos(0, 2, -6);
		add(blocks, helm.getX(), helm.getY(), helm.getZ(), ShipFeature.HELM.defaultBlockState().setValue(HelmBlock.FACING, Direction.SOUTH));
		addChest(blocks, 1, 2, 6, Direction.WEST, "onepiece:chests/pirate");
		addChest(blocks, -1, 2, 6, Direction.EAST, "onepiece:chests/treasure");
		return new ShipLayout(blocks, List.of(), helm, Direction.SOUTH, WATERLINE);
	}

	// ---- Helpers ----

	private static BlockState cannon(Direction facing) {
		return ShipFeature.CANNON.defaultBlockState().setValue(DecorBlock.FACING, facing);
	}

	/** A chest block that fills itself from a loot table the first time someone opens it (after the ship has docked). */
	private static void addChest(List<ShipLayout.ShipBlock> blocks, int x, int y, int z, Direction facing, String lootTable) {
		CompoundTag nbt = new CompoundTag();
		nbt.putString("id", "minecraft:chest");
		nbt.putString("LootTable", lootTable);
		BlockPos pos = new BlockPos(x, y, z);
		blocks.removeIf(block -> block.pos().equals(pos));
		blocks.add(new ShipLayout.ShipBlock(pos, Blocks.CHEST.defaultBlockState().setValue(ChestBlock.FACING, facing), Optional.of(nbt)));
	}

	private static void add(List<ShipLayout.ShipBlock> blocks, int x, int y, int z, BlockState state) {
		BlockPos pos = new BlockPos(x, y, z);
		blocks.removeIf(block -> block.pos().equals(pos)); // Later blocks replace earlier ones.
		blocks.add(new ShipLayout.ShipBlock(pos, state, Optional.empty()));
	}
}
