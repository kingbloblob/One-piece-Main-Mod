package com.onepiecemod.ship;

import java.util.ArrayDeque;
import java.util.BitSet;
import java.util.Map;
import java.util.WeakHashMap;

import net.minecraft.core.BlockPos;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * Keeps the inside of a ship's hull dry. A ship is one entity floating in the real sea, so without this the sea
 * is "inside" every cabin below the waterline: people swim, drown and see underwater fog in the hold.
 *
 * The inside of the hull is worked out once per ship layout, one layer at a time: flood in from the edges of the
 * ship's box over empty cells; any empty cell the flood can't reach is walled in by the hull, so it's dry. Any ship
 * block counts as a wall (doors, panes and fences too). A layer with a hole in its walls lets the sea in, like a
 * real hull would.
 *
 * A ship that dives (deepsea.ShipDive) is stricter once she's all the way under: then the sea comes in from above too,
 * so only cells sealed on every side stay dry (a submarine's hull with its hatch shut). A coated ship's bubble keeps
 * everything inside it dry, on deck and in the rigging too.
 *
 * Used by EntityFluidMixin (no swimming or drowning in the hold), CameraFluidMixin (no underwater fog) and
 * ShipRenderer (hides the sea's surface inside the hull, like a boat does).
 */
public final class ShipHold {
	private static final Map<ShipLayout, Interior> INTERIORS = new WeakHashMap<>();
	/** How far past a ship's box her bubble can reach (deepsea.ShipDive.bubbleRadius adds 2.5 to each side). */
	private static final double BUBBLE_REACH = 4;

	private ShipHold() {
	}

	/** The walled-in empty cells of a layout, as a bit grid over the layout's box. */
	public static final class Interior {
		final BlockPos min;
		final int sizeX, sizeY, sizeZ;
		final BitSet dry;
		/** Cells the sea can't reach from any side, above and below included. */
		final BitSet sealed;

		Interior(BlockPos min, int sizeX, int sizeY, int sizeZ, BitSet dry, BitSet sealed) {
			this.min = min;
			this.sizeX = sizeX;
			this.sizeY = sizeY;
			this.sizeZ = sizeZ;
			this.dry = dry;
			this.sealed = sealed;
		}

		/** True if the cell at this ship-grid position is closed in on all six sides (see ShipHold). */
		public boolean isSealed(int x, int y, int z) {
			int ix = x - min.getX(), iy = y - min.getY(), iz = z - min.getZ();
			if (ix < 0 || iy < 0 || iz < 0 || ix >= sizeX || iy >= sizeY || iz >= sizeZ) {
				return false;
			}
			return sealed.get((iy * sizeZ + iz) * sizeX + ix);
		}

		/** How many empty cells are sealed in. A submarine needs some, or there's nowhere dry to stand. */
		public int sealedCount() {
			return sealed.cardinality();
		}

		/** True if the cell at this ship-grid position is walled in. */
		public boolean isDry(int x, int y, int z) {
			int ix = x - min.getX(), iy = y - min.getY(), iz = z - min.getZ();
			if (ix < 0 || iy < 0 || iz < 0 || ix >= sizeX || iy >= sizeY || iz >= sizeZ) {
				return false;
			}
			return dry.get((iy * sizeZ + iz) * sizeX + ix);
		}

		public BlockPos min() {
			return min;
		}

		public int sizeX() {
			return sizeX;
		}

		public int sizeZ() {
			return sizeZ;
		}
	}

	public static Interior interior(ShipLayout layout) {
		synchronized (INTERIORS) {
			return INTERIORS.computeIfAbsent(layout, ShipHold::compute);
		}
	}

	private static Interior compute(ShipLayout layout) {
		BlockPos min = layout.min, max = layout.max;
		int sizeX = max.getX() - min.getX() + 1, sizeY = max.getY() - min.getY() + 1, sizeZ = max.getZ() - min.getZ() + 1;
		BitSet dry = new BitSet(sizeX * sizeY * sizeZ);
		if (layout.size() == 0) {
			return new Interior(min, 0, 0, 0, dry, new BitSet());
		}
		BlockPos.MutableBlockPos cell = new BlockPos.MutableBlockPos();
		boolean[] wall = new boolean[sizeX * sizeZ];
		boolean[] outside = new boolean[sizeX * sizeZ];
		ArrayDeque<Integer> queue = new ArrayDeque<>();
		for (int iy = 0; iy < sizeY; iy++) {
			for (int iz = 0; iz < sizeZ; iz++) {
				for (int ix = 0; ix < sizeX; ix++) {
					wall[iz * sizeX + ix] = layout.indexAt(cell.set(min.getX() + ix, min.getY() + iy, min.getZ() + iz)) >= 0;
				}
			}
			java.util.Arrays.fill(outside, false);
			// The sea comes in from every open cell on the edge of the box.
			for (int iz = 0; iz < sizeZ; iz++) {
				for (int ix = 0; ix < sizeX; ix++) {
					if ((ix == 0 || iz == 0 || ix == sizeX - 1 || iz == sizeZ - 1) && !wall[iz * sizeX + ix]) {
						outside[iz * sizeX + ix] = true;
						queue.add(iz * sizeX + ix);
					}
				}
			}
			while (!queue.isEmpty()) {
				int at = queue.poll();
				int ix = at % sizeX, iz = at / sizeX;
				flow(ix + 1, iz, sizeX, sizeZ, wall, outside, queue);
				flow(ix - 1, iz, sizeX, sizeZ, wall, outside, queue);
				flow(ix, iz + 1, sizeX, sizeZ, wall, outside, queue);
				flow(ix, iz - 1, sizeX, sizeZ, wall, outside, queue);
			}
			for (int i = 0; i < wall.length; i++) {
				if (!wall[i] && !outside[i]) {
					dry.set(iy * sizeZ * sizeX + i);
				}
			}
		}
		return new Interior(min, sizeX, sizeY, sizeZ, dry, sealed(layout, min, sizeX, sizeY, sizeZ));
	}

	/** The empty cells a flood from every face of the box can't reach, going up and down too. */
	private static BitSet sealed(ShipLayout layout, BlockPos min, int sizeX, int sizeY, int sizeZ) {
		int total = sizeX * sizeY * sizeZ;
		BitSet wall = new BitSet(total);
		BitSet outside = new BitSet(total);
		BlockPos.MutableBlockPos cell = new BlockPos.MutableBlockPos();
		for (int iy = 0; iy < sizeY; iy++) {
			for (int iz = 0; iz < sizeZ; iz++) {
				for (int ix = 0; ix < sizeX; ix++) {
					if (layout.indexAt(cell.set(min.getX() + ix, min.getY() + iy, min.getZ() + iz)) >= 0) {
						wall.set((iy * sizeZ + iz) * sizeX + ix);
					}
				}
			}
		}
		ArrayDeque<Integer> queue = new ArrayDeque<>();
		for (int iy = 0; iy < sizeY; iy++) {
			for (int iz = 0; iz < sizeZ; iz++) {
				for (int ix = 0; ix < sizeX; ix++) {
					boolean edge = ix == 0 || iy == 0 || iz == 0 || ix == sizeX - 1 || iy == sizeY - 1 || iz == sizeZ - 1;
					int i = (iy * sizeZ + iz) * sizeX + ix;
					if (edge && !wall.get(i)) {
						outside.set(i);
						queue.add(i);
					}
				}
			}
		}
		int layer = sizeX * sizeZ;
		while (!queue.isEmpty()) {
			int at = queue.poll();
			int ix = at % sizeX, iz = (at / sizeX) % sizeZ, iy = at / layer;
			if (ix > 0) flow3(at - 1, wall, outside, queue);
			if (ix < sizeX - 1) flow3(at + 1, wall, outside, queue);
			if (iz > 0) flow3(at - sizeX, wall, outside, queue);
			if (iz < sizeZ - 1) flow3(at + sizeX, wall, outside, queue);
			if (iy > 0) flow3(at - layer, wall, outside, queue);
			if (iy < sizeY - 1) flow3(at + layer, wall, outside, queue);
		}
		BitSet sealed = new BitSet(total);
		for (int i = 0; i < total; i++) {
			if (!wall.get(i) && !outside.get(i)) {
				sealed.set(i);
			}
		}
		return sealed;
	}

	private static void flow3(int i, BitSet wall, BitSet outside, ArrayDeque<Integer> queue) {
		if (!wall.get(i) && !outside.get(i)) {
			outside.set(i);
			queue.add(i);
		}
	}

	private static void flow(int ix, int iz, int sizeX, int sizeZ, boolean[] wall, boolean[] outside, ArrayDeque<Integer> queue) {
		if (ix < 0 || iz < 0 || ix >= sizeX || iz >= sizeZ) {
			return;
		}
		int i = iz * sizeX + ix;
		if (!wall[i] && !outside[i]) {
			outside[i] = true;
			queue.add(i);
		}
	}

	/** True if this world point is inside the walled-in part of a ship's hull. */
	public static boolean isDry(Level level, Vec3 point) {
		// Reach a bit past the ships' boxes: a coated ship's bubble sticks out round her hull.
		for (ShipEntity ship : ShipDecks.shipsTouching(level, new AABB(point, point).inflate(BUBBLE_REACH))) {
			ShipLayout layout = ship.getLayout();
			Vec3 local = ShipDecks.toShip(point.subtract(ship.position()), ship.getYRot(), layout);
			if (com.onepiecemod.deepsea.ShipDive.inBubble(ship, local)) {
				return true;
			}
			int x = Mth.floor(local.x + 0.5), y = Mth.floor(local.y), z = Mth.floor(local.z + 0.5);
			Interior hold = interior(layout);
			if (com.onepiecemod.deepsea.ShipDive.fullySubmerged(ship) ? hold.isSealed(x, y, z) : hold.isDry(x, y, z)) {
				return true;
			}
		}
		return false;
	}

	/** True if the entity stands in a ship's dry hold, so the sea around the ship shouldn't reach it. */
	public static boolean isDry(Entity entity) {
		if (entity instanceof ShipEntity) {
			return false;
		}
		// The captain of a submarine or a coated ship steers from inside (the Polar Tang's wheel is up on the tower).
		if (entity.getVehicle() instanceof ShipEntity ship && com.onepiecemod.deepsea.ShipDive.canDive(ship)) {
			return true;
		}
		return isDry(entity.level(), entity.position().add(0, 0.1, 0));
	}
}
