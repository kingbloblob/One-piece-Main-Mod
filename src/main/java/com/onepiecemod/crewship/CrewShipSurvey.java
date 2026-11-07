package com.onepiecemod.crewship;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.EmptyBlockGetter;
import net.minecraft.world.phys.shapes.VoxelShape;
import net.minecraft.world.level.block.BarrelBlock;
import net.minecraft.world.level.block.BedBlock;
import net.minecraft.world.level.block.ChestBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BedPart;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.ship.HelmBlock;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.ship.ShipFeature;

/**
 * A look over a crew ship's blocks: which rooms she has, her bunks, cannons and storage, and where
 * each crewmate stands to work. Works the same on a docked ship (world positions) and a sailing one
 * (positions in the ship's own grid), see {@link Frame}.
 */
public final class CrewShipSurvey {
	/** One room: its main block, and the spot next to it where its crewmate works. */
	public record Room(ShipRoom type, BlockPos core, BlockPos post) {}

	/** One place to sleep: the bed head or hammock, and how high its top is. */
	public record Bunk(BlockPos pos, double top) {}

	/**
	 * Turns survey positions into the world. Docked: they already are world positions. Sailing: they are
	 * in the ship's grid and move with her (a block at x, y, z is centred on x, z sideways).
	 */
	public record Frame(ShipEntity ship) {
		public static final Frame DOCKED = new Frame(null);

		public boolean sailing() {
			return ship != null;
		}

		/** Where an entity's feet go to stand in this cell (raised by `lift`). */
		public Vec3 feet(BlockPos cell, double lift) {
			if (ship == null) {
				return new Vec3(cell.getX() + 0.5, cell.getY() + lift, cell.getZ() + 0.5);
			}
			return ship.rotate(new Vec3(cell.getX(), cell.getY() + lift, cell.getZ()), 1.0f).add(ship.position());
		}

		/** The middle of a block, to look at. */
		public Vec3 center(BlockPos cell) {
			return feet(cell, 0.5);
		}
	}

	public final Map<ShipRoom, Room> rooms = new EnumMap<>(ShipRoom.class);
	public final List<Bunk> bunks = new ArrayList<>();
	/** Free deck spots near the wheel, for crewmates whose room isn't built yet. */
	public final List<BlockPos> deckSpots = new ArrayList<>();
	public int cannons;
	public int storage;
	public boolean colaEngine;
	public int hull;
	public int sails;
	public int guns;
	public int blocks;

	private final Map<BlockPos, BlockState> shipBlocks;

	private CrewShipSurvey(Map<BlockPos, BlockState> shipBlocks) {
		this.shipBlocks = shipBlocks;
	}

	/** Looks over the ship. `helm` is where the Ship's Wheel is (or null). */
	public static CrewShipSurvey of(Map<BlockPos, BlockState> shipBlocks, BlockPos helm) {
		CrewShipSurvey survey = new CrewShipSurvey(shipBlocks);
		survey.scan(helm);
		return survey;
	}

	public int jobRooms() {
		int count = 0;
		for (ShipRoom room : rooms.keySet()) {
			if (room.role != null) {
				count++;
			}
		}
		return count;
	}

	public boolean has(ShipRoom room) {
		return rooms.containsKey(room);
	}

	private void scan(BlockPos helm) {
		blocks = shipBlocks.size();
		List<BlockPos> cores = new ArrayList<>();
		for (Map.Entry<BlockPos, BlockState> entry : shipBlocks.entrySet()) {
			BlockState state = entry.getValue();
			BlockPos pos = entry.getKey();
			if (state.getBlock() instanceof BedBlock) {
				if (state.getValue(BedBlock.PART) == BedPart.HEAD) {
					bunks.add(new Bunk(pos, 0.5625));
				}
			} else if (ShipRoom.isBunk(state)) {
				bunks.add(new Bunk(pos, 0.25));
			} else if (state.is(ShipFeature.CANNON)) {
				cannons++;
			} else if (state.is(ShipFeature.COLA_ENGINE)) {
				colaEngine = true;
			} else if (state.getBlock() instanceof ChestBlock || state.getBlock() instanceof BarrelBlock) {
				storage++;
			} else {
				String id = ShipRoom.id(state);
				if (id.endsWith("_cupboard") || id.equals("onepiece:pirate_chest") || id.equals(CrewShipFeature.SHIP_LOG_ID)) {
					storage++;
				}
			}
			if (state.is(ShipFeature.HELM) && state.hasProperty(HelmBlock.HULL)) {
				hull = state.getValue(HelmBlock.HULL);
				sails = state.getValue(HelmBlock.SAILS);
				guns = state.getValue(HelmBlock.GUNS);
			}
		}
		// Rooms: the first core block of each kind with enough partners around it.
		for (ShipRoom room : ShipRoom.values()) {
			for (Map.Entry<BlockPos, BlockState> entry : shipBlocks.entrySet()) {
				if (!room.isCore(entry.getValue())) {
					continue;
				}
				if (partners(room, entry.getKey()) >= room.partnersNeeded) {
					BlockPos post = standingSpotNear(entry.getKey(), 2);
					rooms.put(room, new Room(room, entry.getKey(), post != null ? post : entry.getKey().above()));
					break;
				}
			}
		}
		// Deck spots for crewmates without a room: the open deck nearest the wheel.
		if (helm != null) {
			for (BlockPos pos : BlockPos.betweenClosed(helm.offset(-6, -2, -6), helm.offset(6, 2, 6))) {
				if (standable(pos)) {
					cores.add(pos.immutable());
				}
			}
			cores.sort(Comparator.comparingDouble(p -> p.distSqr(helm)));
			for (int i = 1; i < cores.size() && deckSpots.size() < 12; i += 2) {
				deckSpots.add(cores.get(i));
			}
		}
		bunks.sort(Comparator.comparingLong(bunk -> bunk.pos().asLong()));
	}

	/** How many partner blocks (not counting the core itself) are within RADIUS of the core. */
	private int partners(ShipRoom room, BlockPos core) {
		if (room.partnersNeeded == 0) {
			return 0;
		}
		int count = 0;
		int r = ShipRoom.RADIUS;
		for (BlockPos pos : BlockPos.betweenClosed(core.offset(-r, -r, -r), core.offset(r, r, r))) {
			if (pos.equals(core)) {
				continue;
			}
			BlockState state = shipBlocks.get(pos);
			if (state != null && room.isPartner(state)) {
				count++;
				if (count >= room.partnersNeeded) {
					return count;
				}
			}
		}
		return count;
	}

	/** An open cell (floor below, room for a body) beside `pos`, closest first. */
	private BlockPos standingSpotNear(BlockPos pos, int reach) {
		BlockPos best = null;
		double bestDistance = Double.MAX_VALUE;
		for (BlockPos cell : BlockPos.betweenClosed(pos.offset(-reach, -1, -reach), pos.offset(reach, 1, reach))) {
			if (cell.equals(pos) || !standable(cell)) {
				continue;
			}
			double distance = cell.distSqr(pos) + (cell.getY() != pos.getY() ? 0.5 : 0);
			if (distance < bestDistance) {
				bestDistance = distance;
				best = cell.immutable();
			}
		}
		return best;
	}

	/** True if someone can stand in this cell: a solid ship block under it and two open cells. */
	private boolean standable(BlockPos cell) {
		BlockState below = shipBlocks.get(cell.below());
		return below != null && !shape(below).isEmpty() && open(cell) && open(cell.above());
	}

	private boolean open(BlockPos cell) {
		BlockState state = shipBlocks.get(cell);
		if (state == null) {
			return true;
		}
		VoxelShape shape = shape(state);
		return shape.isEmpty() || shape.max(Direction.Axis.Y) <= 0.2; // Rugs and carpets are fine to stand on.
	}

	private static VoxelShape shape(BlockState state) {
		return state.getCollisionShape(EmptyBlockGetter.INSTANCE, BlockPos.ZERO);
	}
}
