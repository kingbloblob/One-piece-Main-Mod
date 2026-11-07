package com.onepiecemod.news;

import java.util.ArrayList;
import java.util.List;

import com.mojang.serialization.Codec;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.Registries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.TagKey;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.StructureStart;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.OnePieceMod;

/**
 * The Marines put up Wanted Posters in towns and Marine bases. The first time a player walks into one
 * (any structure in the tag onepiece:has_wanted_posters, plus vanilla villages), a few posters get pinned
 * to its walls at eye height. The first one shows the most wanted pirate in the world, the next the
 * second most wanted, and so on.
 */
public class PosterPlacer {
	public static final TagKey<Structure> TOWNS = TagKey.create(Registries.STRUCTURE, OnePieceMod.id("has_wanted_posters"));

	/** Structures that already got their posters (start chunk, as a long). Saved per dimension. */
	public static final AttachmentType<List<Long>> DONE = AttachmentRegistry.create(
			OnePieceMod.id("poster_towns"),
			builder -> builder.persistent(Codec.LONG.listOf())
	);

	private static final int TRIES = 400;

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 100 != 50) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				if (player.level() instanceof ServerLevel level && !player.isSpectator()) {
					check(level, player.blockPosition());
				}
			}
		});
	}

	/** Pins posters in the town at this spot if it doesn't have them yet. Returns how many went up (-1 = not a town). */
	public static int check(ServerLevel level, BlockPos at) {
		StructureStart start = townAt(level, at);
		if (start == null) {
			return -1;
		}
		long key = start.getChunkPos().pack();
		List<Long> done = level.getAttachedOrElse(DONE, List.of());
		if (done.contains(key)) {
			return 0;
		}
		BoundingBox box = start.getBoundingBox();
		int wanted = Math.max(2, Math.min(6, box.getXSpan() * box.getZSpan() / 500));
		int placed = place(level, start, wanted, level.getRandom());
		List<Long> copy = new ArrayList<>(done);
		copy.add(key);
		level.setAttached(DONE, copy);
		return placed;
	}

	/** The town at this spot: standing in one of its buildings, or anywhere inside its outline. */
	public static StructureStart townAt(ServerLevel level, BlockPos at) {
		for (BlockPos pos : new BlockPos[] {at, at.below(4)}) {
			StructureStart start = level.structureManager().getStructureWithPieceAt(pos, TOWNS);
			if (start != null && start.isValid()) {
				return start;
			}
		}
		var towns = level.registryAccess().lookupOrThrow(Registries.STRUCTURE).get(TOWNS);
		if (towns.isPresent()) {
			StructureStart start = level.structureManager().getStructureAt(at, towns.get());
			if (start != null && start.isValid()) {
				return start;
			}
		}
		return null;
	}

	private static int place(ServerLevel level, StructureStart start, int wanted, RandomSource random) {
		List<StructurePiece> pieces = start.getPieces();
		List<BlockPos> placed = new ArrayList<>();
		for (int tries = 0; tries < TRIES && placed.size() < wanted && !pieces.isEmpty(); tries++) {
			BoundingBox box = pieces.get(random.nextInt(pieces.size())).getBoundingBox();
			int x = box.minX() + random.nextInt(box.getXSpan());
			int z = box.minZ() + random.nextInt(box.getZSpan());
			Direction wallSide = Direction.Plane.HORIZONTAL.getRandomDirection(random);
			BlockPos spot = findSpot(level, x, z, box.minY(), box.maxY(), wallSide);
			if (spot == null || tooClose(spot, placed)) {
				continue;
			}
			BlockState state = NewsFeature.WANTED_POSTER.defaultBlockState().setValue(WantedPosterBlock.FACING, wallSide.getOpposite());
			if (!level.setBlock(spot, state, Block.UPDATE_ALL)) {
				continue;
			}
			if (level.getBlockEntity(spot) instanceof WantedPosterBlockEntity poster) {
				poster.setSlot(placed.size());
			}
			placed.add(spot);
		}
		if (!placed.isEmpty()) {
			OnePieceMod.LOGGER.info("Pinned Wanted Posters at {}", placed);
		}
		return placed.size();
	}

	/** An air block at eye height (floor below), with a solid wall on wallSide. */
	private static BlockPos findSpot(ServerLevel level, int x, int z, int minY, int maxY, Direction wallSide) {
		for (int y = maxY; y > minY; y--) {
			BlockPos pos = new BlockPos(x, y, z);
			if (!level.isLoaded(pos) || !level.isLoaded(pos.relative(wallSide))) {
				return null;
			}
			if (!level.getBlockState(pos).isAir()) {
				continue;
			}
			BlockPos floor = pos.below();
			BlockState floorState = level.getBlockState(floor);
			if (!floorState.isFaceSturdy(level, floor, Direction.UP)) {
				continue;
			}
			BlockPos wall = pos.relative(wallSide);
			BlockState wallState = level.getBlockState(wall);
			if (wallState.is(BlockTags.LEAVES) || !wallState.isFaceSturdy(level, wall, wallSide.getOpposite())
					|| !level.getBlockState(wall.above()).isFaceSturdy(level, wall.above(), wallSide.getOpposite())) {
				continue; // A real wall: at least two blocks tall.
			}
			if (!level.getBlockState(pos.above()).isAir()) {
				continue;
			}
			return pos;
		}
		return null;
	}

	private static boolean tooClose(BlockPos spot, List<BlockPos> placed) {
		for (BlockPos other : placed) {
			if (other.distManhattan(spot) < 6) {
				return true;
			}
		}
		return false;
	}
}
