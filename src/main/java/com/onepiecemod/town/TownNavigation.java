package com.onepiecemod.town;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.navigation.GroundPathNavigation;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.FenceGateBlock;
import net.minecraft.world.level.block.LadderBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.pathfinder.Node;
import net.minecraft.world.level.pathfinder.PathFinder;
import net.minecraft.world.level.pathfinder.PathType;
import net.minecraft.world.level.pathfinder.PathfindingContext;
import net.minecraft.world.level.pathfinder.WalkNodeEvaluator;

/**
 * How townsfolk find their way. Like a villager's, but they also plan routes through wooden doors and fence gates
 * (every house in town has a front door and every garden a gate; {@link TownDoorGoal} opens and closes them), and up
 * and down ladders, which is how you get upstairs in most town houses (beds are usually up there).
 */
public class TownNavigation extends GroundPathNavigation {
	/** Rebuilt towns are big: plan routes up to this far (vanilla stops at the follow range, 48). */
	public static final float RANGE = 80f;

	public TownNavigation(Mob mob, Level level) {
		super(mob, level);
		this.setRequiredPathLength(RANGE);
	}

	@Override
	protected PathFinder createPathFinder(int maxVisitedNodes) {
		this.nodeEvaluator = new GateEvaluator();
		this.nodeEvaluator.setCanPassDoors(true);
		this.nodeEvaluator.setCanOpenDoors(true);
		this.nodeEvaluator.setCanFloat(true);
		return new PathFinder(this.nodeEvaluator, maxVisitedNodes);
	}

	/**
	 * Treats a closed fence gate like a closed wooden door: something you can open on the way through. Also lets a
	 * route step into a ladder from the side and climb it up or down (vanilla walkers never use ladders). Climbing
	 * itself is ordinary movement: walking into a ladder and jumping climbs it, and stepping off the top lets you down.
	 */
	private static class GateEvaluator extends WalkNodeEvaluator {
		@Override
		public int getNeighbors(Node[] neighbors, Node node) {
			int count = super.getNeighbors(neighbors, node);
			int x = node.x;
			int y = node.y;
			int z = node.z;
			if (ladder(x, y, z) && roomAt(x, y + 1, z) && leadsSomewhere(x, y, z)) {
				count = add(neighbors, count, x, y + 1, z); // Up the ladder (or off its top, onto the floor above).
			}
			if (ladder(x, y - 1, z)) {
				count = add(neighbors, count, x, y - 1, z); // Down through the hatch.
			}
			for (Direction direction : Direction.Plane.HORIZONTAL) {
				int nx = x + direction.getStepX();
				int nz = z + direction.getStepZ();
				if (ladder(nx, y, nz) && roomAt(nx, y + 1, nz) && leadsSomewhere(nx, y, nz)) {
					count = add(neighbors, count, nx, y, nz); // Onto the foot of a ladder.
				}
			}
			return count;
		}

		private int add(Node[] neighbors, int count, int x, int y, int z) {
			if (count >= neighbors.length) {
				return count;
			}
			Node next = this.getNode(x, y, z);
			if (next.closed) {
				return count;
			}
			for (int i = 0; i < count; i++) {
				if (neighbors[i] == next) {
					return count;
				}
			}
			next.type = PathType.WALKABLE;
			next.costMalus = Math.max(next.costMalus, 1.0f); // A little slower than stairs, so stairs win when there are both.
			neighbors[count] = next;
			return count + 1;
		}

		/** Only climb a ladder whose top lets you off (not one with a flower pot or a floor over the hatch). */
		private boolean leadsSomewhere(int x, int y, int z) {
			int top = y;
			while (top - y < 32 && ladder(x, top + 1, z)) {
				top++;
			}
			return roomAt(x, top + 1, z) && roomAt(x, top + 2, z);
		}

		private boolean ladder(int x, int y, int z) {
			return this.currentContext.getBlockState(new BlockPos(x, y, z)).getBlock() instanceof LadderBlock;
		}

		/** Space for a body: a ladder, or nothing in the way. */
		private boolean roomAt(int x, int y, int z) {
			BlockPos pos = new BlockPos(x, y, z);
			BlockState state = this.currentContext.getBlockState(pos);
			return state.getBlock() instanceof LadderBlock || state.getCollisionShape(this.currentContext.level(), pos).isEmpty();
		}

		@Override
		public PathType getPathType(PathfindingContext context, int x, int y, int z) {
			BlockState state = context.getBlockState(new BlockPos(x, y, z));
			if (state.getBlock() instanceof FenceGateBlock && !state.getValue(FenceGateBlock.OPEN)) {
				return PathType.DOOR_WOOD_CLOSED;
			}
			return super.getPathType(context, x, y, z);
		}
	}
}
