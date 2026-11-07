package com.onepiecemod.ship;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.world.Clearable;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.phys.Vec3;

/**
 * Turns a block build into a sailing ship, and back again.
 *
 * Building: every block touching the Ship's Wheel, and every block touching those, and so on, becomes part of
 * the ship. Natural blocks (stone, dirt, sand...) never count, so your ship won't take the sea floor with it.
 * The list of ignored blocks is the tag data/onepiece/tags/block/not_ship.json, so you can change it.
 */
public class ShipAssembler {
	/** The biggest ship allowed, in blocks. Bigger ships take longer to send to players. (The Thousand Sunny is about 4,500.) */
	public static final int MAX_BLOCKS = 6000;

	// Set the blocks without breaking anything attached to them, and without dropping items.
	private static final int QUIET = Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE | Block.UPDATE_SUPPRESS_DROPS;

	/** Tries to turn the build around the wheel at helmPos into a ship. Returns a problem to show the player, or null if it worked. */
	public static String assemble(ServerLevel level, BlockPos helmPos, Player player) {
		// 1. Find every connected block.
		Set<BlockPos> found = new HashSet<>();
		ArrayDeque<BlockPos> toCheck = new ArrayDeque<>();
		found.add(helmPos);
		toCheck.add(helmPos);
		while (!toCheck.isEmpty()) {
			BlockPos pos = toCheck.poll();
			// Corner-to-corner counts as connected too: rigging, stays and sloping spars run diagonally, and a
			// face-only search left the Going Merry's shrouds floating at the dock when she set sail again.
			for (BlockPos next : BlockPos.betweenClosed(pos.offset(-1, -1, -1), pos.offset(1, 1, 1))) {
				if (!found.contains(next) && isShipBlock(level.getBlockState(next))) {
					next = next.immutable();
					if (found.size() >= MAX_BLOCKS) {
						return "This ship is over " + MAX_BLOCKS + " blocks. Is it touching land, or a pier?";
					}
					found.add(next);
					toCheck.add(next);
				}
			}
		}

		// 2. Find the sea around it (beside it, or underneath for a raft sitting on the water).
		double surface = Double.NEGATIVE_INFINITY;
		for (BlockPos pos : found) {
			for (Direction direction : Direction.values()) {
				BlockPos next = pos.relative(direction);
				FluidState fluid = level.getFluidState(next);
				if (!found.contains(next) && fluid.is(FluidTags.WATER) && !level.getFluidState(next.above()).is(FluidTags.WATER)) {
					surface = Math.max(surface, next.getY() + fluid.getHeight(level, next));
				}
			}
		}
		if (surface == Double.NEGATIVE_INFINITY) {
			return "A ship needs to be in the water. Build it so the bottom touches the sea.";
		}

		// 3. Work out the ship's centre. Positions are stored relative to it.
		int minX = Integer.MAX_VALUE, minY = Integer.MAX_VALUE, minZ = Integer.MAX_VALUE;
		int maxX = Integer.MIN_VALUE, maxZ = Integer.MIN_VALUE;
		for (BlockPos pos : found) {
			minX = Math.min(minX, pos.getX());
			minY = Math.min(minY, pos.getY());
			minZ = Math.min(minZ, pos.getZ());
			maxX = Math.max(maxX, pos.getX());
			maxZ = Math.max(maxZ, pos.getZ());
		}
		BlockPos anchor = new BlockPos(Math.floorDiv(minX + maxX, 2), minY, Math.floorDiv(minZ + maxZ, 2));

		// 4. Copy every block, including what's inside chests, and any painted flags.
		List<ShipLayout.ShipBlock> blocks = new ArrayList<>();
		List<ShipLayout.FlagEntry> flags = new ArrayList<>();
		for (BlockPos pos : found) {
			BlockState state = level.getBlockState(pos);
			BlockEntity blockEntity = level.getBlockEntity(pos);
			Optional<CompoundTag> nbt = Optional.empty();
			if (blockEntity != null) {
				nbt = Optional.of(blockEntity.saveWithFullMetadata(level.registryAccess()));
				if (blockEntity instanceof FlagBlockEntity flag) {
					flags.add(new ShipLayout.FlagEntry(pos.subtract(anchor), flag.getDesign()));
				}
			}
			blocks.add(new ShipLayout.ShipBlock(pos.subtract(anchor), state, nbt));
		}

		BlockState helmState = level.getBlockState(helmPos);
		Direction bow = helmState.getValue(HelmBlock.FACING);
		ShipLayout layout = new ShipLayout(blocks, flags, helmPos.subtract(anchor), bow, (float) (surface - anchor.getY()));

		// 5. Take the blocks out of the world. Anything below the waterline becomes sea again.
		for (BlockPos pos : found) {
			BlockEntity blockEntity = level.getBlockEntity(pos);
			if (blockEntity != null) {
				if (blockEntity instanceof Clearable clearable) clearable.clearContent(); // so chests don't spill their items
				level.removeBlockEntity(pos);
			}
		}
		for (BlockPos pos : found) {
			level.setBlock(pos, pos.getY() + 0.5 < surface ? Blocks.WATER.defaultBlockState() : Blocks.AIR.defaultBlockState(), QUIET);
		}
		floodHullInside(level, found, surface);

		// 6. Launch!
		ShipEntity ship = ShipFeature.SHIP.create(level, EntitySpawnReason.TRIGGERED);
		if (ship == null) {
			return "Something went wrong making the ship.";
		}
		ship.setLayout(layout);
		ship.snapTo(anchor.getX() + 0.5, anchor.getY(), anchor.getZ() + 0.5, bow.toYRot(), 0);
		level.addFreshEntity(ship);
		player.startRiding(ship);
		return null;
	}

	/** Tries to put a ship's blocks back into the world where it is now. Returns a problem, or null if it worked. */
	public static String dock(ServerLevel level, ShipEntity ship) {
		ShipLayout layout = ship.getLayout();

		// Ships dock square to the world, so snap to the nearest quarter turn.
		int quarterTurns = Math.floorMod(Math.round(Mth.wrapDegrees(ship.rotationSinceBuilt(1.0f)) / 90f), 4);
		Rotation rotation = switch (quarterTurns) {
			case 1 -> Rotation.CLOCKWISE_90;
			case 2 -> Rotation.CLOCKWISE_180;
			case 3 -> Rotation.COUNTERCLOCKWISE_90;
			default -> Rotation.NONE;
		};
		BlockPos anchor = BlockPos.containing(ship.getX(), Math.round(ship.getY()), ship.getZ());

		// Check there is room first, so we never place half a ship.
		Map<BlockPos, ShipLayout.ShipBlock> placements = new HashMap<>();
		int blocked = 0;
		for (ShipLayout.ShipBlock block : layout.blocks) {
			BlockPos target = anchor.offset(block.pos().rotate(rotation));
			if (!level.getBlockState(target).canBeReplaced()) {
				blocked++;
			}
			placements.put(target, block);
		}
		if (blocked > 0) {
			return "Can't drop anchor here: " + blocked + " blocks are in the way. Sail into open water.";
		}

		// Close any chest screens first, so every item is saved into the ship before it becomes real chests.
		ShipInteractions.closeAll(ship, level);

		List<Vec3> seats = ship.seatPositions();
		List<Entity> crew = List.copyOf(ship.getPassengers());
		// People walking the deck: remember where they stand on the ship, to put them on the same spot once she's square.
		List<Entity> walkers = ShipDecks.onDeck(ship);
		List<Vec3> walkerSpots = new ArrayList<>();
		for (Entity walker : walkers) {
			walkerSpots.add(ShipDecks.toShip(walker.position().subtract(ship.position()), ship.getYRot(), layout));
		}
		ship.ejectPassengers();

		for (Map.Entry<BlockPos, ShipLayout.ShipBlock> entry : placements.entrySet()) {
			level.setBlock(entry.getKey(), entry.getValue().state().rotate(rotation), QUIET);
		}
		for (Map.Entry<BlockPos, ShipLayout.ShipBlock> entry : placements.entrySet()) {
			ShipLayout.ShipBlock block = entry.getValue();
			if (block.nbt().isPresent()) {
				BlockState placed = level.getBlockState(entry.getKey());
				BlockEntity restored = BlockEntity.loadStatic(entry.getKey(), placed, block.nbt().get(), level.registryAccess());
				if (restored != null) {
					level.setBlockEntity(restored);
				}
			}
		}
		drainHullInside(level, placements.keySet(), anchor.getY() + layout.waterline);

		// Put everyone back on deck where they were standing.
		for (int i = 0; i < crew.size() && i < seats.size(); i++) {
			Vec3 seat = seats.get(i);
			crew.get(i).teleportTo(seat.x, Math.round(seat.y) + 0.05, seat.z);
		}
		for (int i = 0; i < walkers.size(); i++) {
			Vec3 local = walkerSpots.get(i);
			Vec3 turned = switch (quarterTurns) {
				case 1 -> new Vec3(-local.z, local.y, local.x);
				case 2 -> new Vec3(-local.x, local.y, -local.z);
				case 3 -> new Vec3(local.z, local.y, -local.x);
				default -> local;
			};
			walkers.get(i).teleportTo(anchor.getX() + 0.5 + turned.x, anchor.getY() + turned.y + 0.05, anchor.getZ() + 0.5 + turned.z);
		}
		ship.discard();
		return null;
	}

	private static boolean isShipBlock(BlockState state) {
		// Air and loose water don't count. Waterlogged blocks (like a wet fence) do.
		return !state.isAir() && !state.liquid() && !state.is(ShipFeature.NOT_SHIP);
	}

	/**
	 * Cabins below the waterline are air while the ship is built. When the ship sails away,
	 * fill those spaces with sea so it doesn't leave an air bubble behind.
	 */
	private static void floodHullInside(ServerLevel level, Set<BlockPos> shipBlocks, double surface) {
		for (BlockPos pos : hullInside(shipBlocks, surface)) {
			if (level.getBlockState(pos).isAir()) {
				level.setBlock(pos, Blocks.WATER.defaultBlockState(), QUIET);
			}
		}
	}

	/** The opposite of floodHullInside: pump the sea out of a docked ship's cabins. */
	private static void drainHullInside(ServerLevel level, Set<BlockPos> shipBlocks, double surface) {
		for (BlockPos pos : hullInside(shipBlocks, surface)) {
			if (level.getBlockState(pos).is(Blocks.WATER)) {
				level.setBlock(pos, Blocks.AIR.defaultBlockState(), QUIET);
			}
		}
	}

	/** Spaces below the waterline that have part of the ship underneath them: the inside of the hull. */
	private static List<BlockPos> hullInside(Set<BlockPos> shipBlocks, double surface) {
		Map<Long, Integer> lowestInColumn = new HashMap<>();
		for (BlockPos pos : shipBlocks) {
			long column = BlockPos.asLong(pos.getX(), 0, pos.getZ());
			lowestInColumn.merge(column, pos.getY(), Math::min);
		}
		List<BlockPos> inside = new ArrayList<>();
		for (Map.Entry<Long, Integer> column : lowestInColumn.entrySet()) {
			BlockPos base = BlockPos.of(column.getKey());
			for (int y = column.getValue() + 1; y + 0.5 < surface; y++) {
				BlockPos pos = new BlockPos(base.getX(), y, base.getZ());
				if (!shipBlocks.contains(pos)) {
					inside.add(pos);
				}
			}
		}
		return inside;
	}
}
