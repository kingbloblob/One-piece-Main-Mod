package com.onepiecemod.baseworks;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Predicate;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;

import com.onepiecemod.building.GhostPlan;
import com.onepiecemod.building.Parts;

/**
 * One page of a plan book: a small build drawn as letters, layer by layer, like a recipe for a room or a hut.
 *
 * Every letter is a "slot": what counts there (loose on purpose, so any planks or any fence will do) and which
 * block to draw as a see-through ghost while it's missing. A space or a dot means "anything, leave it as it is".
 *
 * Layers go from the bottom up. In each layer the TOP text row is the far side (straight ahead of you when you
 * click the ground) and the BOTTOM row is right in front of you. The plan turns to face the way you look.
 * Facing blocks (stairs, cannons, furniture, beds) are drawn as if you look north; they turn with the plan.
 */
public final class LayoutPlan {
	/** What a letter means. */
	public record Slot(String label, Predicate<BlockState> matches, String ghostId, Block fallback, Direction facing,
			Map<String, String> props) {
		BlockState ghost() {
			BlockState state = BuiltInRegistries.BLOCK.getOptional(Identifier.parse(ghostId)).orElse(fallback).defaultBlockState();
			if (facing != null) {
				if (state.hasProperty(BlockStateProperties.HORIZONTAL_FACING)) {
					state = state.setValue(BlockStateProperties.HORIZONTAL_FACING, facing);
				}
			}
			for (Map.Entry<String, String> entry : props.entrySet()) {
				state = withProperty(state, entry.getKey(), entry.getValue());
			}
			return state;
		}
	}

	public final String id;
	public final String title;
	/** What it's for, in one line ("A Galley: your cook works here..."). */
	public final String purpose;
	/** Extra tips shown on the page (what else helps). */
	public final List<String> tips = new ArrayList<>();
	/** Layer 0 sits this many blocks above the clicked block: 1 = on top of it (a room on a deck), 0 = level with it (a floor). */
	public int floorOffset = 1;
	private final List<String[]> layers = new ArrayList<>();
	private final Map<Character, Slot> legend = new HashMap<>();

	public LayoutPlan(String id, String title, String purpose) {
		this.id = id;
		this.title = title;
		this.purpose = purpose;
		Legend.common(legend);
	}

	// ---------- Building a plan ----------

	public LayoutPlan key(char letter, String label, Predicate<BlockState> matches, String ghostId) {
		legend.put(letter, new Slot(label, matches, ghostId, Blocks.OAK_PLANKS, null, Map.of()));
		return this;
	}

	public LayoutPlan key(char letter, String label, Predicate<BlockState> matches, String ghostId, Direction facing) {
		legend.put(letter, new Slot(label, matches, ghostId, Blocks.OAK_PLANKS, facing, Map.of()));
		return this;
	}

	public LayoutPlan key(char letter, String label, Predicate<BlockState> matches, String ghostId, Direction facing, Map<String, String> props) {
		legend.put(letter, new Slot(label, matches, ghostId, Blocks.OAK_PLANKS, facing, props));
		return this;
	}

	/** The exact block (by id) is needed here, and it's also the ghost. */
	public LayoutPlan exact(char letter, String label, String id, Direction facing) {
		return key(letter, label, ids(id), id, facing);
	}

	public LayoutPlan layer(String... rows) {
		layers.add(rows);
		return this;
	}

	public LayoutPlan floor(int offset) {
		this.floorOffset = offset;
		return this;
	}

	public LayoutPlan tip(String line) {
		tips.add(line);
		return this;
	}

	public int width() {
		int width = 0;
		for (String[] layer : layers) {
			for (String row : layer) {
				width = Math.max(width, row.length());
			}
		}
		return width;
	}

	public int depth() {
		int depth = 0;
		for (String[] layer : layers) {
			depth = Math.max(depth, layer.length);
		}
		return depth;
	}

	public int height() {
		return layers.size();
	}

	/** "12 Planks, 1 Smoker..." counted from the drawing, for the plan page. */
	public Map<String, Integer> materials() {
		Map<String, Integer> counts = new LinkedHashMap<>();
		for (String[] layer : layers) {
			for (String row : layer) {
				for (char c : row.toCharArray()) {
					Slot slot = legend.get(c);
					if (slot != null) {
						counts.merge(slot.label(), 1, Integer::sum);
					}
				}
			}
		}
		return counts;
	}

	// ---------- Placing and checking ----------

	/** This plan laid out at a spot, turned to face one way. */
	public Placed at(BlockPos clicked, Direction facing) {
		return new Placed(this, clicked.above(floorOffset).immutable(), facing.getAxis().isHorizontal() ? facing : Direction.NORTH);
	}

	/** A plan put down in the world: what the blueprint ghosts show and what "finished" means. */
	public record Placed(LayoutPlan plan, BlockPos origin, Direction facing) implements GhostPlan {
		@Override
		public String name() {
			return plan.title;
		}

		@Override
		public String purpose() {
			return plan.purpose;
		}

		/** Every lettered spot of the plan, in the world. */
		public Map<BlockPos, Slot> cells() {
			Map<BlockPos, Slot> cells = new LinkedHashMap<>();
			Direction right = facing.getClockWise();
			int width = plan.width();
			for (int y = 0; y < plan.layers.size(); y++) {
				String[] rows = plan.layers.get(y);
				for (int r = 0; r < rows.length; r++) {
					int forward = rows.length - 1 - r; // Bottom row = right in front of you.
					String row = rows[r];
					for (int c = 0; c < row.length(); c++) {
						Slot slot = plan.legend.get(row.charAt(c));
						if (slot == null) {
							continue;
						}
						int side = c - width / 2;
						BlockPos pos = origin.offset(facing.getStepX() * forward + right.getStepX() * side, y,
								facing.getStepZ() * forward + right.getStepZ() * side);
						cells.put(pos, slot);
					}
				}
			}
			return cells;
		}

		@Override
		public Check check(ServerLevel level, BlockPos ignored) {
			Rotation rotation = rotationFor(facing);
			List<Ghost> ghosts = new ArrayList<>();
			Map<String, Integer> missing = new LinkedHashMap<>();
			for (Map.Entry<BlockPos, Slot> cell : cells().entrySet()) {
				BlockState there = level.getBlockState(cell.getKey());
				if (!cell.getValue().matches().test(there)) {
					ghosts.add(new Ghost(cell.getKey(), cell.getValue().ghost().rotate(rotation)));
					missing.merge(cell.getValue().label(), 1, Integer::sum);
				}
			}
			List<String> lines = new ArrayList<>();
			missing.forEach((label, count) -> lines.add(count + " more " + label.replaceFirst("^(a|an) ", "")));
			return new Check(ghosts, lines);
		}

		/** The middle of the plan at floor level, for "is this inside my claim / on my ship" checks. */
		public BlockPos center() {
			int forward = plan.depth() / 2;
			return origin.offset(facing.getStepX() * forward, 0, facing.getStepZ() * forward);
		}
	}

	static Rotation rotationFor(Direction facing) {
		return switch (facing) {
			case EAST -> Rotation.CLOCKWISE_90;
			case SOUTH -> Rotation.CLOCKWISE_180;
			case WEST -> Rotation.COUNTERCLOCKWISE_90;
			default -> Rotation.NONE;
		};
	}

	// ---------- Matching helpers ----------

	static String idOf(BlockState state) {
		return BuiltInRegistries.BLOCK.getKey(state.getBlock()).toString();
	}

	/** Any of these block ids. */
	public static Predicate<BlockState> ids(String... names) {
		Set<String> set = Set.of(names);
		return state -> set.contains(idOf(state));
	}

	public static Predicate<BlockState> suffix(String... ends) {
		return state -> {
			String id = idOf(state);
			for (String end : ends) {
				if (id.endsWith(end)) {
					return true;
				}
			}
			return false;
		};
	}

	@SuppressWarnings({"unchecked", "rawtypes"})
	private static BlockState withProperty(BlockState state, String name, String value) {
		for (net.minecraft.world.level.block.state.properties.Property property : state.getProperties()) {
			if (property.getName().equals(name)) {
				java.util.Optional parsed = property.getValue(value);
				if (parsed.isPresent()) {
					return state.setValue(property, (Comparable) parsed.get());
				}
			}
		}
		return state;
	}

	/** The letters every plan knows. Plans can add more or change these. */
	static final class Legend {
		private Legend() {
		}

		static void common(Map<Character, Slot> legend) {
			put(legend, 'P', "planks", Parts.WOOD_DECK, "minecraft:spruce_planks", null);
			put(legend, 'S', "wooden slabs", state -> state.is(BlockTags.WOODEN_SLABS) || state.is(BlockTags.PLANKS),
					"minecraft:spruce_slab", null);
			put(legend, 'L', "logs or posts", Parts.POST.or(state -> state.is(BlockTags.PLANKS)), "minecraft:spruce_log", null);
			put(legend, 'F', "fences or railings", Parts.RAIL, "minecraft:spruce_fence", null);
			put(legend, '#', "stone or bricks", Parts.STONE, "minecraft:stone_bricks", null);
			put(legend, 'W', "a crafting table", ids("minecraft:crafting_table", "minecraft:crafter"), "minecraft:crafting_table", null);
			put(legend, 'X', "chests or barrels", Parts.CHEST.or(suffix("_crate", "crate_stack", "pirate_chest", "_cupboard")),
					"minecraft:barrel", null);
			put(legend, 'T', "lights (lantern, lamp, torch)",
					state -> state.getLightEmission() >= 10 || state.is(BlockTags.CANDLES) || Parts.LANTERN.test(state),
					"minecraft:lantern", null);
			put(legend, 'O', "a campfire", state -> state.is(BlockTags.CAMPFIRES), "minecraft:campfire", null);
			put(legend, 'K', "a smoker, furnace or stove",
					ids("minecraft:smoker", "minecraft:furnace", "minecraft:blast_furnace", "onepiece:iron_stove", "onepiece:hearth",
							"onepiece:ships_galley"), "minecraft:smoker", Direction.SOUTH);
			put(legend, 'D', "a door", Parts.DOOR, "minecraft:spruce_door", Direction.SOUTH);
			put(legend, 'G', "a fence gate", state -> state.is(BlockTags.FENCE_GATES), "minecraft:spruce_fence_gate", Direction.SOUTH);
			put(legend, 'C', "cannons", ids("onepiece:cannon"), "onepiece:cannon", Direction.NORTH);
			put(legend, 'H', "hammocks or beds", state -> state.getBlock() instanceof net.minecraft.world.level.block.BedBlock
					|| idOf(state).equals("onepiece:hammock"), "onepiece:hammock", Direction.NORTH);
			put(legend, 'R', "roof (slabs, planks or roof tiles)", Parts.ROOF.or(Parts.STONE), "minecraft:spruce_slab", null);
			put(legend, 'w', "glass or windows", state -> Parts.name(state).contains("glass") || Parts.name(state).contains("pane")
					|| Parts.name(state).contains("shoji") || Parts.RAIL.test(state), "minecraft:glass_pane", null);
			put(legend, '~', "water", Parts.WATER, "minecraft:water", null);
			put(legend, 's', "stools or chairs", state -> state.is(BlockTags.WOODEN_STAIRS)
					|| suffix("_stool", "_chair", "_bench", "cushion", "bar_stool", "captains_chair", "armchair").test(state),
					"onepiece:spruce_stool", Direction.SOUTH);
			put(legend, 't', "tables", suffix("_table", "low_table", "kotatsu", "barrel_table"), "onepiece:spruce_table", null);
			put(legend, 'g', "grass, dirt or sand", state -> state.is(BlockTags.DIRT) || state.is(BlockTags.SAND)
					|| idOf(state).equals("onepiece:deck_lawn") || idOf(state).equals("onepiece:deck_soil"), "minecraft:grass_block", null);
		}

		private static void put(Map<Character, Slot> legend, char letter, String label, Predicate<BlockState> matches, String ghost, Direction facing) {
			legend.put(letter, new Slot(label, matches, ghost, Blocks.OAK_PLANKS, facing, Map.of()));
		}
	}
}
