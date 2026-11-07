package com.onepiecemod.world;

import java.util.ArrayDeque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.feature.Feature;

import com.onepiecemod.deco.DecoBlocks;

/**
 * A real palm tree: a thin trunk that leans and curves to one side, topped by eight long fronds
 * that reach out and droop at the tips. Used by the configured feature onepiece:palm_tree
 * ({"type": "onepiece:palm"}), so it grows on beaches and from Palm Saplings.
 */
public record PalmTreeFeature() implements Feature {
	public static final PalmTreeFeature INSTANCE = new PalmTreeFeature();
	public static final MapCodec<PalmTreeFeature> CODEC = MapCodec.unit(INSTANCE);

	private static final Direction[] SIDES = {Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST};

	@Override
	public MapCodec<PalmTreeFeature> codec() {
		return CODEC;
	}

	@Override
	public boolean place(WorldGenLevel level, ChunkGenerator chunkGenerator, RandomSource random, BlockPos origin) {
		// Standing in tall grass or snow? Start the trunk at the ground under it (the trunk replaces the plant).
		for (int i = 0; i < 2; i++) {
			BlockState below = level.getBlockState(origin.below());
			if (below.isAir() || !below.canBeReplaced() || !below.getFluidState().isEmpty()) {
				break;
			}
			origin = origin.below();
		}
		// Needs a real block to stand on. Where palms may grow is decided elsewhere: in the world by the placed
		// feature (only where a Palm Sapling could survive) and for saplings by the sapling itself.
		BlockState ground = level.getBlockState(origin.below());
		if (ground.isAir() || ground.canBeReplaced() || ground.is(BlockTags.LEAVES)) {
			return false;
		}

		// The trunk: 6 to 9 tall, leaning 1 to 3 blocks, more at the top than at the bottom (a curve).
		int height = 6 + random.nextInt(4);
		int lean = 1 + random.nextInt(3);
		Direction leanTo = SIDES[random.nextInt(4)];
		Set<BlockPos> trunk = new HashSet<>();
		BlockPos top = origin;
		int shifted = 0;
		for (int i = 0; i < height; i++) {
			double t = (double) i / (height - 1);
			int want = (int) Math.round(lean * t * t);
			BlockPos pos = origin.above(i).relative(leanTo, want);
			if (want > shifted && i > 0) {
				trunk.add(pos.below()); // a step sideways, so the trunk stays joined
				shifted = want;
			}
			trunk.add(pos);
			top = pos;
		}
		for (BlockPos pos : trunk) {
			if (!canReplace(level, pos)) {
				return false;
			}
		}

		// The crown: four straight fronds and four diagonal ones, flat at first and drooping at the end.
		Set<BlockPos> leaves = new HashSet<>();
		leaves.add(top.above());
		for (Direction side : SIDES) {
			leaves.add(top.relative(side));
			frond(leaves, top, side.getStepX(), side.getStepZ(), 3 + random.nextInt(2));
			Direction next = side.getClockWise();
			frond(leaves, top, side.getStepX() + next.getStepX(), side.getStepZ() + next.getStepZ(), 2 + random.nextInt(2));
		}
		leaves.removeAll(trunk);

		BlockState log = DecoBlocks.PALM_LOG.defaultBlockState();
		if (log.hasProperty(BlockStateProperties.AXIS)) {
			log = log.setValue(BlockStateProperties.AXIS, Direction.Axis.Y);
		}
		for (BlockPos pos : trunk) {
			level.setBlock(pos, log, 3);
		}

		// Leaves need their distance to the nearest log, or they would fall apart (decay) in a few minutes.
		Map<BlockPos, Integer> distance = new HashMap<>();
		ArrayDeque<BlockPos> queue = new ArrayDeque<>();
		for (BlockPos pos : trunk) {
			distance.put(pos, 0);
			queue.add(pos);
		}
		while (!queue.isEmpty()) {
			BlockPos pos = queue.poll();
			for (Direction direction : Direction.values()) {
				BlockPos next = pos.relative(direction);
				if (leaves.contains(next) && !distance.containsKey(next)) {
					distance.put(next, distance.get(pos) + 1);
					queue.add(next);
				}
			}
		}
		BlockState leaf = DecoBlocks.PALM_LEAVES.defaultBlockState();
		for (BlockPos pos : leaves) {
			int d = Math.min(7, distance.getOrDefault(pos, 7));
			if (d < 7 && level.getBlockState(pos).isAir()) {
				level.setBlock(pos, leaf.hasProperty(BlockStateProperties.DISTANCE) ? leaf.setValue(BlockStateProperties.DISTANCE, d) : leaf, 3);
			}
		}
		return true;
	}

	/** One frond going out from the top of the trunk in steps of (dx, dz). The last two steps droop down. */
	private static void frond(Set<BlockPos> leaves, BlockPos top, int dx, int dz, int length) {
		BlockPos previous = top;
		int y = 0;
		for (int k = 1; k <= length; k++) {
			int drop = k > length - 2 ? (k - (length - 2)) : 0;
			BlockPos pos = top.offset(dx * k, -drop, dz * k);
			if (dx != 0 && dz != 0) {
				leaves.add(previous.offset(dx, 0, 0)); // diagonal steps need a joining leaf
			}
			if (-drop < y) {
				leaves.add(pos.above()); // a drooping tip hangs from the leaf above it
			}
			leaves.add(pos);
			previous = pos;
			y = -drop;
		}
	}

	private static boolean canReplace(WorldGenLevel level, BlockPos pos) {
		BlockState state = level.getBlockState(pos);
		return state.isAir() || state.is(BlockTags.LEAVES) || state.canBeReplaced();
	}
}
