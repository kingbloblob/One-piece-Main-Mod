package com.onepiecemod.building;

import java.util.function.Predicate;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Prediction;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

/**
 * The kinds of blocks buildings are made of. Most are loose on purpose, so the mod's own
 * building blocks (Marine Bricks, Tatami, Wano Roof Tiles, Paper Lanterns...) count too.
 * Plus two little inventory helpers for paying and getting paid.
 */
public class Parts {
	/** The block's name without the "minecraft:" or "onepiece:" part, like "marine_bricks". */
	public static String name(BlockState state) {
		return BuiltInRegistries.BLOCK.getKey(state.getBlock()).getPath();
	}

	private static boolean nameHas(BlockState state, String... parts) {
		String name = name(state);
		for (String part : parts) {
			if (name.contains(part)) {
				return true;
			}
		}
		return false;
	}

	private static boolean isShaped(BlockState state) {
		return nameHas(state, "slab", "stairs", "wall", "button", "pressure_plate", "fence");
	}

	public static final Predicate<BlockState> PLANKS = state -> state.is(BlockTags.PLANKS);

	/** Planks, wooden slabs or wooden stairs. */
	public static final Predicate<BlockState> WOOD_DECK = state ->
			state.is(BlockTags.PLANKS) || state.is(BlockTags.WOODEN_SLABS) || state.is(BlockTags.WOODEN_STAIRS);

	/** A roof: any wood, or roof tiles (like the Wano Roof Tiles). */
	public static final Predicate<BlockState> ROOF = state -> WOOD_DECK.test(state) || nameHas(state, "roof_tile");

	/** Logs, wood and pillars (like the Marine Pillar). */
	public static final Predicate<BlockState> POST = state -> state.is(BlockTags.LOGS) || name(state).endsWith("pillar");

	/** Any full stone or brick block: stone bricks, Marine Bricks, Seastone Bricks, deepslate... */
	public static final Predicate<BlockState> STONE = state -> !isShaped(state)
			&& (nameHas(state, "stone", "brick", "cobble", "deepslate", "tiles", "andesite", "diorite", "granite",
					"prismarine", "quartz", "concrete", "pillar", "mosaic", "stucco")
					|| isTreasure(state));

	/** Strong walls for the vault: stone, or iron blocks. */
	public static final Predicate<BlockState> STRONG = state -> STONE.test(state) || state.is(Blocks.IRON_BLOCK)
			|| state.is(Blocks.OBSIDIAN) || state.is(Blocks.CRYING_OBSIDIAN);

	/** Fences, walls, iron bars and Prison Bars: anything that works as a railing or a mast. */
	public static final Predicate<BlockState> RAIL = state -> state.is(BlockTags.FENCES) || state.is(BlockTags.WALLS)
			|| nameHas(state, "bars", "chain");

	public static final Predicate<BlockState> LANTERN = state -> nameHas(state, "lantern", "lamp");

	public static final Predicate<BlockState> WATER = state -> state.getFluidState().is(FluidTags.WATER);

	public static final Predicate<BlockState> DOOR = state -> state.is(BlockTags.DOORS);

	public static final Predicate<BlockState> CHEST = state -> state.is(Blocks.CHEST) || state.is(Blocks.TRAPPED_CHEST)
			|| state.is(Blocks.BARREL);

	public static final Predicate<BlockState> TATAMI = state -> nameHas(state, "tatami");

	public static final Predicate<BlockState> SHOJI = state -> nameHas(state, "shoji");

	public static final Predicate<BlockState> CHAIR = state -> state.is(BlockTags.WOODEN_STAIRS);

	public static final Predicate<BlockState> COOKING_FIRE = state -> state.is(BlockTags.CAMPFIRES) || state.is(Blocks.SMOKER);

	public static final Predicate<BlockState> CAULDRON = state -> nameHas(state, "cauldron");

	public static final Predicate<BlockState> LIGHTNING_ROD = state -> name(state).endsWith("lightning_rod");

	public static final Predicate<BlockState> ANCHOR = state -> name(state).equals("anchor");

	public static final Predicate<BlockState> ROPE_COIL = state -> name(state).equals("rope_coil");

	public static final Predicate<BlockState> TREASURE = Parts::isTreasure;

	/** Gold blocks, raw gold blocks, Berry Blocks and Shandora Gold Bricks. */
	private static boolean isTreasure(BlockState state) {
		String name = name(state);
		return name.equals("gold_block") || name.equals("raw_gold_block") || name.equals("berry_block")
				|| name.equals("shandora_gold_bricks");
	}

	/**
	 * A block to suggest as a ghost, looked up by its id (like "onepiece:marine_bricks"),
	 * with a vanilla block to use instead if that one doesn't exist.
	 */
	public static BlockState block(String id, Block fallback) {
		return BuiltInRegistries.BLOCK.getOptional(Identifier.parse(id)).orElse(fallback).defaultBlockState();
	}

	// ---------- Paying and getting paid ----------

	/** How many of this item the player carries. */
	public static int count(ServerPlayer player, Item item) {
		int total = 0;
		for (ItemStack stack : player.getInventory().getNonEquipmentItems()) {
			if (stack.is(item)) {
				total += stack.getCount();
			}
		}
		return total;
	}

	/** Takes this many of the item from the player. Check count() first. */
	public static void take(ServerPlayer player, Item item, int amount) {
		for (ItemStack stack : player.getInventory().getNonEquipmentItems()) {
			if (amount <= 0) {
				return;
			}
			if (stack.is(item)) {
				int taken = Math.min(amount, stack.getCount());
				stack.shrink(taken);
				amount -= taken;
			}
		}
	}

	/** Gives the player an item, dropping it at their feet if the bag is full. */
	public static void give(ServerPlayer player, ItemStack stack) {
		if (!player.getInventory().add(stack) && !stack.isEmpty()) {
			player.drop(stack, false, Prediction.SERVER_ONLY);
		}
	}
}
