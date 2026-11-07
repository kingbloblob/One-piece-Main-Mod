package com.onepiecemod.building;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Predicate;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/**
 * A building the player puts together out of normal blocks, like the Pirate Tavern.
 *
 * Every building has one special "core" block (the Den Den Mushi Relay, the Training Post...).
 * All the other blocks are measured from the core. A building is a list of rules, for example
 * "a 5x5 floor of planks under the core" or "2 lanterns somewhere in the room".
 * Each rule that is about exact spots also names a block to suggest there: the blueprint
 * draws that block as a see-through ghost where it's missing.
 *
 * Each building in {@link Buildings} is a small subclass that says what its rules are
 * and what happens when you use the finished core.
 */
public abstract class Multiblock implements GhostPlan {
	private final String id;
	private final String name;
	private final List<Rule> rules = new ArrayList<>();
	private final List<String> plan = new ArrayList<>();
	private Block core;

	protected Multiblock(String id, String name) {
		this.id = id;
		this.name = name;
	}

	public String id() { return id; }
	@Override
	public String name() { return name; }
	public Block core() { return core; }
	public List<String> plan() { return plan; }

	void setCore(Block core) {
		this.core = core;
	}

	/** One step of the plan, shown when you read the blueprint. */
	protected void planLine(String line) {
		plan.add(line);
	}

	// ---------- Rules ----------

	/** One thing the building needs. It adds ghost blocks and chat lines for whatever is missing. */
	public interface Rule {
		void check(ServerLevel level, BlockPos core, Map<BlockPos, BlockState> ghosts, List<String> missingThings);
	}

	/** Every one of these spots must hold a matching block, like every block of a floor. */
	protected void fill(String what, Predicate<BlockState> matches, BlockState ghost, List<BlockPos> offsets) {
		rules.add((level, core, ghosts, missingThings) -> {
			int missing = 0;
			for (BlockPos offset : offsets) {
				BlockPos pos = core.offset(offset);
				if (!matches.test(level.getBlockState(pos))) {
					ghosts.put(pos, ghost);
					missing++;
				}
			}
			if (missing > 0) {
				missingThings.add(missing + " more " + what);
			}
		});
	}

	/** At least `needed` of these spots must hold a matching block (handy for water or railings). */
	protected void atLeastAt(String what, Predicate<BlockState> matches, BlockState ghost, List<BlockPos> offsets, int needed) {
		rules.add((level, core, ghosts, missingThings) -> {
			int found = 0;
			List<BlockPos> empty = new ArrayList<>();
			for (BlockPos offset : offsets) {
				BlockPos pos = core.offset(offset);
				if (matches.test(level.getBlockState(pos))) {
					found++;
				} else {
					empty.add(pos);
				}
			}
			if (found < needed) {
				for (BlockPos pos : empty) {
					ghosts.put(pos, ghost);
				}
				missingThings.add((needed - found) + " more " + what);
			}
		});
	}

	/**
	 * At least `needed` of these spots must match, but the ghost only shows one suggested place
	 * (like "a door goes here", instead of a door ghost on every wall block).
	 */
	protected void atLeastAt(String what, Predicate<BlockState> matches, List<BlockPos> offsets, int needed,
			Map<BlockPos, BlockState> suggestedGhosts) {
		rules.add((level, core, ghosts, missingThings) -> {
			int found = 0;
			for (BlockPos offset : offsets) {
				if (matches.test(level.getBlockState(core.offset(offset)))) {
					found++;
				}
			}
			if (found < needed) {
				suggestedGhosts.forEach((offset, state) -> ghosts.put(core.offset(offset), state));
				missingThings.add((needed - found) + " more " + what);
			}
		});
	}

	/** At least `needed` matching blocks anywhere inside a box (furniture in a room). Listed in chat only. */
	protected void contains(String what, Predicate<BlockState> matches, BlockPos from, BlockPos to, int needed) {
		rules.add((level, core, ghosts, missingThings) -> {
			int found = 0;
			for (BlockPos pos : BlockPos.betweenClosed(core.offset(from), core.offset(to))) {
				if (matches.test(level.getBlockState(pos))) {
					found++;
				}
			}
			if (found < needed) {
				missingThings.add((needed - found) + " more " + what);
			}
		});
	}

	// ---------- Shapes (lists of offsets from the core) ----------

	/** A full square layer, like a floor or a roof. half = 2 gives 5x5. */
	protected static List<BlockPos> square(int dy, int half) {
		List<BlockPos> list = new ArrayList<>();
		for (int dx = -half; dx <= half; dx++) {
			for (int dz = -half; dz <= half; dz++) {
				list.add(new BlockPos(dx, dy, dz));
			}
		}
		return list;
	}

	/** Only the outer edge of a square layer, like a wall or a railing. */
	protected static List<BlockPos> ring(int dy, int half) {
		List<BlockPos> list = new ArrayList<>();
		for (BlockPos pos : square(dy, half)) {
			if (Math.abs(pos.getX()) == half || Math.abs(pos.getZ()) == half) {
				list.add(pos);
			}
		}
		return list;
	}

	/** A post in each corner of a square, from dyFrom up to dyTo. */
	protected static List<BlockPos> corners(int dyFrom, int dyTo, int half) {
		List<BlockPos> list = new ArrayList<>();
		for (int dy = dyFrom; dy <= dyTo; dy++) {
			for (int sx : new int[] {-half, half}) {
				for (int sz : new int[] {-half, half}) {
					list.add(new BlockPos(sx, dy, sz));
				}
			}
		}
		return list;
	}

	/** A straight up-and-down column. */
	protected static List<BlockPos> column(int dx, int dz, int dyFrom, int dyTo) {
		List<BlockPos> list = new ArrayList<>();
		for (int dy = dyFrom; dy <= dyTo; dy++) {
			list.add(new BlockPos(dx, dy, dz));
		}
		return list;
	}

	/** Several shapes joined together. */
	@SafeVarargs
	protected static List<BlockPos> join(List<BlockPos>... parts) {
		List<BlockPos> list = new ArrayList<>();
		for (List<BlockPos> part : parts) {
			list.addAll(part);
		}
		return list;
	}

	// ---------- Checking ----------

	@Override
	public Check check(ServerLevel level, BlockPos corePos) {
		Map<BlockPos, BlockState> ghosts = new LinkedHashMap<>();
		List<String> missingThings = new ArrayList<>();
		if (!level.getBlockState(corePos).is(core)) {
			missingThings.add("the " + core.getName().getString() + " itself, in the middle");
			ghosts.put(corePos, core.defaultBlockState());
		}
		for (Rule rule : rules) {
			rule.check(level, corePos, ghosts, missingThings);
		}
		List<Ghost> list = new ArrayList<>();
		ghosts.forEach((pos, state) -> list.add(new Ghost(pos, state)));
		return new Check(list, missingThings);
	}

	// ---------- What the finished building does ----------

	/** The player right-clicked the core of a finished building. */
	public abstract void use(ServerPlayer player, BuildingRegistry.Entry building);

	/** Called about once a second for every finished building near a player. */
	public void tick(ServerLevel level, BuildingRegistry.Entry building) {
	}
}
