package com.onepiecemod.ship;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.WeakHashMap;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.EmptyBlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

/**
 * Walking on deck while a ship sails.
 *
 * A sailing ship's blocks aren't real blocks, so two things make its deck feel solid:
 *  - Bumping: whenever anything moves (a player, a mob, a dropped item), it also bumps into the blocks of nearby ships.
 *    The ship is turned, so the move is turned into the ship's own square grid, checked against its blocks there,
 *    and turned back (see collide, called from mixin.EntityCollideMixin).
 *  - Carrying: every tick, whatever stands on a ship moves and turns with it. Each player's own game carries them
 *    (players' games decide where they are), the server carries everything else.
 *
 * Below the waterline the sea fills the hull while sailing, so lower cabins are flooded until you drop anchor.
 */
public final class ShipDecks {
	private ShipDecks() {
	}

	/** Ships in the world on each side (client and server keep their own copies of every entity). */
	private static final Set<ShipEntity> CLIENT_SHIPS = Collections.newSetFromMap(new WeakHashMap<>());
	private static final Set<ShipEntity> SERVER_SHIPS = Collections.newSetFromMap(new WeakHashMap<>());

	/** Where each ship was at the last carrying pass: x, y, z, yaw. */
	private static final Map<ShipEntity, double[]> CLIENT_LAST = new WeakHashMap<>();
	private static final Map<ShipEntity, double[]> SERVER_LAST = new WeakHashMap<>();

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(ShipDecks::carryOnServer);
	}

	static void track(ShipEntity ship) {
		ships(ship.level()).add(ship);
	}

	static void untrack(ShipEntity ship) {
		ships(ship.level()).remove(ship);
	}

	private static Set<ShipEntity> ships(Level level) {
		return level.isClientSide() ? CLIENT_SHIPS : SERVER_SHIPS;
	}

	/** Ships in this level whose box touches `box`. */
	public static List<ShipEntity> shipsTouching(Level level, AABB box) {
		Set<ShipEntity> all = ships(level);
		if (all.isEmpty()) {
			return List.of();
		}
		List<ShipEntity> result = new ArrayList<>(2);
		for (ShipEntity ship : all) {
			if (ship.level() == level && !ship.isRemoved() && ship.getLayout().size() > 0 && ship.getBoundingBox().inflate(1, 2, 1).intersects(box)) {
				result.add(ship);
			}
		}
		return result;
	}

	// ---- Turning between the world and a ship's own grid ----

	/** A world offset from the ship's position, turned into the ship's own (as-built) directions. */
	static Vec3 toShip(Vec3 world, float shipYaw, ShipLayout layout) {
		float radians = -(shipYaw - layout.bow.toYRot()) * Mth.DEG_TO_RAD;
		float cos = Mth.cos(radians), sin = Mth.sin(radians);
		return new Vec3(world.x * cos - world.z * sin, world.y, world.x * sin + world.z * cos);
	}

	/** The opposite of toShip. */
	static Vec3 toWorld(Vec3 local, float shipYaw, ShipLayout layout) {
		float radians = (shipYaw - layout.bow.toYRot()) * Mth.DEG_TO_RAD;
		float cos = Mth.cos(radians), sin = Mth.sin(radians);
		return new Vec3(local.x * cos - local.z * sin, local.y, local.x * sin + local.z * cos);
	}

	// ---- Bumping ----

	/** The entity's move after also bumping into the blocks of any ship it touches. `movement` already bumped into the world. */
	public static Vec3 collide(Entity entity, Vec3 movement) {
		if (entity instanceof ShipEntity || entity.isPassenger() || entity.noPhysics || movement.lengthSqr() == 0) {
			return movement;
		}
		AABB box = entity.getBoundingBox();
		List<ShipEntity> ships = shipsTouching(entity.level(), box.expandTowards(movement));
		for (ShipEntity ship : ships) {
			// Catch up with the ship first if it already moved this tick, so the entity bumps into the deck where it now is.
			if (entity.level().isClientSide()) {
				if (entity instanceof Player player && player.isLocalPlayer()) {
					carry(ship, CLIENT_LAST, other -> other == player);
				}
			} else if (!(entity instanceof Player)) {
				carry(ship, SERVER_LAST, other -> !(other instanceof Player));
			}
			movement = entity instanceof Player && !entity.level().isClientSide()
					? landOnShip(entity, ship, movement)
					: collideWithShip(entity, ship, movement);
		}
		return movement;
	}

	/**
	 * A player's move as the server checks it. Each player's own game walks them on deck (and carries them), against
	 * the ship where that game sees it, which is a little behind where the server has it. If the server bumped the
	 * move into its own copy of the ship it would get a different answer and pull the player back ("moved wrongly"),
	 * every few steps, until they fell off. So the server only lets the deck stop a fall: that keeps the player
	 * standing (not "flying") without ever turning a step aside. Small up/down differences the server ignores anyway.
	 */
	private static Vec3 landOnShip(Entity entity, ShipEntity ship, Vec3 movement) {
		if (movement.y >= 0) {
			return movement;
		}
		ShipLayout layout = ship.getLayout();
		Vec3 local = toShip(entity.position().subtract(ship.position()), ship.getYRot(), layout);
		double half = entity.getBbWidth() / 2;
		AABB box = new AABB(local.x - half, local.y, local.z - half, local.x + half, local.y + entity.getBbHeight(), local.z + half);
		List<VoxelShape> shapes = shapesNear(layout, box.expandTowards(0, movement.y, 0).inflate(0.5));
		if (shapes.isEmpty()) {
			return movement;
		}
		// Positions come rounded off the network, so feet can sit a hair inside the deck, and the game lets a box fall
		// through any shape it already overlaps: check from a little higher up.
		double above = 0.01;
		double fall = Shapes.collide(Direction.Axis.Y, box.move(0, above, 0), shapes, movement.y - above);
		if (fall == movement.y - above) {
			return movement; // Nothing underfoot.
		}
		// Turning only touches x and z, so up and down are the same in the ship's grid and in the world.
		return new Vec3(movement.x, fall + above, movement.z);
	}

	private static Vec3 collideWithShip(Entity entity, ShipEntity ship, Vec3 movement) {
		ShipLayout layout = ship.getLayout();
		float yaw = ship.getYRot();
		Vec3 local = toShip(entity.position().subtract(ship.position()), yaw, layout);
		Vec3 localMove = toShip(movement, yaw, layout);
		double half = entity.getBbWidth() / 2;
		// A turned entity box is near enough the same square in the ship's grid (entities are narrow and roughly round).
		AABB box = new AABB(local.x - half, local.y, local.z - half, local.x + half, local.y + entity.getBbHeight(), local.z + half);
		List<VoxelShape> shapes = shapesNear(layout, box.expandTowards(localMove).inflate(0.5, entity.maxUpStep() + 0.5, 0.5));
		if (shapes.isEmpty()) {
			return movement;
		}
		// A deck that rose into the entity's feet (the ship bobbed up) lifts it, instead of letting it drop through.
		double lift = 0;
		if (localMove.y <= 0) {
			AABB feet = box.deflate(1.0e-3, 0, 1.0e-3);
			for (VoxelShape shape : shapes) {
				double top = shape.max(Direction.Axis.Y);
				if (top > box.minY + 1.0e-7 && top - box.minY <= Math.max(0.6, entity.maxUpStep()) && shape.bounds().intersects(feet)
						&& shape.toAabbs().stream().anyMatch(part -> part.intersects(feet))) {
					lift = Math.max(lift, top - box.minY);
				}
			}
			if (lift > 0) {
				box = box.move(0, lift, 0);
				localMove = new Vec3(localMove.x, 0, localMove.z);
			}
		}
		Vec3 result = collideWithShapes(localMove, box, shapes);
		if (lift > 0) {
			result = result.add(0, lift, 0);
		}
		// Stairs and slabs: step up like on land, if moving sideways was blocked and the entity was standing.
		double step = entity.maxUpStep();
		boolean blockedSideways = result.x != localMove.x || result.z != localMove.z;
		boolean standing = entity.onGround() || (localMove.y < 0 && result.y != localMove.y);
		if (step > 0 && blockedSideways && standing) {
			Vec3 stepped = collideWithShapes(new Vec3(localMove.x, step, localMove.z), box, shapes);
			Vec3 down = collideWithShapes(new Vec3(0, -step + Math.min(0, localMove.y), 0), box.move(stepped), shapes);
			stepped = stepped.add(down);
			if (stepped.horizontalDistanceSqr() > result.horizontalDistanceSqr() + 1.0e-7) {
				result = stepped;
			}
		}
		return toWorld(result, yaw, layout);
	}

	/** Same as the game's own collideWithShapes: up/down first, then the bigger of the two sideways moves. */
	private static Vec3 collideWithShapes(Vec3 move, AABB box, List<VoxelShape> shapes) {
		double y = move.y == 0 ? 0 : Shapes.collide(Direction.Axis.Y, box, shapes, move.y);
		box = box.move(0, y, 0);
		double x = move.x;
		double z = move.z;
		boolean zFirst = Math.abs(x) < Math.abs(z);
		if (zFirst && z != 0) {
			z = Shapes.collide(Direction.Axis.Z, box, shapes, z);
			box = box.move(0, 0, z);
		}
		if (x != 0) {
			x = Shapes.collide(Direction.Axis.X, box, shapes, x);
			box = box.move(x, 0, 0);
		}
		if (!zFirst && z != 0) {
			z = Shapes.collide(Direction.Axis.Z, box, shapes, z);
		}
		return new Vec3(x, y, z);
	}

	/** Collision shapes of the ship blocks in a box of the ship's grid. A block at (x, y, z) spans x-0.5..x+0.5, y..y+1. */
	private static List<VoxelShape> shapesNear(ShipLayout layout, AABB box) {
		List<VoxelShape> shapes = new ArrayList<>();
		int x0 = Mth.floor(box.minX + 0.5), x1 = Mth.floor(box.maxX + 0.5);
		int y0 = Mth.floor(box.minY), y1 = Mth.floor(box.maxY);
		int z0 = Mth.floor(box.minZ + 0.5), z1 = Mth.floor(box.maxZ + 0.5);
		if ((long) (x1 - x0 + 1) * (y1 - y0 + 1) * (z1 - z0 + 1) > 4096) {
			return shapes; // Something moving absurdly fast: don't stall the game checking.
		}
		BlockPos.MutableBlockPos cell = new BlockPos.MutableBlockPos();
		for (int x = x0; x <= x1; x++) {
			for (int y = y0; y <= y1; y++) {
				for (int z = z0; z <= z1; z++) {
					int index = layout.indexAt(cell.set(x, y, z));
					if (index >= 0) {
						VoxelShape shape = layout.blocks.get(index).state().getCollisionShape(EmptyBlockGetter.INSTANCE, BlockPos.ZERO);
						if (!shape.isEmpty()) {
							shapes.add(shape.move(x - 0.5, y, z - 0.5));
						}
					}
				}
			}
		}
		return shapes;
	}

	// ---- Who is aboard ----

	/** True if the entity is standing on (or just above, or inside) this ship, not riding it. */
	public static boolean isOnDeck(ShipEntity ship, Entity entity) {
		return isOnDeck(ship, entity, ship.position(), ship.getYRot());
	}

	private static boolean isOnDeck(ShipEntity ship, Entity entity, Vec3 shipPos, float shipYaw) {
		ShipLayout layout = ship.getLayout();
		if (layout.size() == 0 || entity.getVehicle() != null) {
			return false;
		}
		Vec3 local = toShip(entity.position().subtract(shipPos), shipYaw, layout);
		if (local.y < layout.min.getY() - 0.5 || local.y > layout.max.getY() + 3) {
			return false;
		}
		// Some ship block must be under (or around) the entity's feet, in its column.
		double half = Math.min(0.45, entity.getBbWidth() / 2);
		BlockPos.MutableBlockPos cell = new BlockPos.MutableBlockPos();
		int top = Math.min(Mth.floor(local.y + 0.01), layout.max.getY());
		for (int corner = 0; corner < 5; corner++) {
			double cx = corner == 4 ? local.x : local.x + ((corner & 1) == 0 ? -half : half);
			double cz = corner == 4 ? local.z : local.z + ((corner & 2) == 0 ? -half : half);
			int x = Mth.floor(cx + 0.5);
			int z = Mth.floor(cz + 0.5);
			for (int y = top; y >= layout.min.getY(); y--) {
				if (layout.indexAt(cell.set(x, y, z)) >= 0) {
					return true;
				}
			}
		}
		return false;
	}

	/** The ship this entity is aboard: riding it (the captain at the wheel) or walking its deck. Null if none. */
	public static ShipEntity shipOf(Entity entity) {
		if (entity.getVehicle() instanceof ShipEntity ship) {
			return ship;
		}
		for (ShipEntity ship : shipsTouching(entity.level(), entity.getBoundingBox())) {
			if (isOnDeck(ship, entity)) {
				return ship;
			}
		}
		return null;
	}

	/** Everyone walking on this ship's deck (riders not included). */
	public static List<Entity> onDeck(ShipEntity ship) {
		List<Entity> result = new ArrayList<>();
		for (Entity entity : ship.level().getEntities(ship, ship.getBoundingBox().inflate(1, 3, 1),
				entity -> !(entity instanceof ShipEntity) && entity.getVehicle() == null && !entity.isSpectator())) {
			if (isOnDeck(ship, entity)) {
				result.add(entity);
			}
		}
		return result;
	}

	// ---- Carrying ----

	/** Server, end of every tick: move everything (but players) standing on each ship along with it. */
	private static void carryOnServer(MinecraftServer server) {
		for (ShipEntity ship : new ArrayList<>(SERVER_SHIPS)) {
			if (ship.isRemoved() || !(ship.level() instanceof ServerLevel)) {
				SERVER_LAST.remove(ship);
				continue;
			}
			carry(ship, SERVER_LAST, entity -> !(entity instanceof Player));
		}
	}

	/** Client, end of every tick: move the local player along with the ship they stand on. */
	public static void carryOnClient(Player localPlayer) {
		for (ShipEntity ship : new ArrayList<>(CLIENT_SHIPS)) {
			if (ship.isRemoved()) {
				CLIENT_LAST.remove(ship);
				continue;
			}
			carry(ship, CLIENT_LAST, entity -> entity == localPlayer);
		}
	}

	private static void carry(ShipEntity ship, Map<ShipEntity, double[]> last, java.util.function.Predicate<Entity> who) {
		double[] before = last.get(ship);
		double[] now = {ship.getX(), ship.getY(), ship.getZ(), ship.getYRot()};
		last.put(ship, now);
		if (before == null || ship.getLayout().size() == 0) {
			return;
		}
		double dx = now[0] - before[0], dy = now[1] - before[1], dz = now[2] - before[2];
		float turn = (float) Mth.wrapDegrees(now[3] - before[3]);
		if (dx * dx + dy * dy + dz * dz < 1.0e-10 && Math.abs(turn) < 1.0e-4) {
			return;
		}
		if (dx * dx + dz * dz > 16 * 16) {
			return; // The ship jumped (teleported): don't fling anyone across the sea.
		}
		Vec3 oldPos = new Vec3(before[0], before[1], before[2]);
		AABB search = ship.getBoundingBox().move(-dx, -dy, -dz).inflate(1, 3, 1);
		for (Entity entity : ship.level().getEntities(ship, search, entity -> !(entity instanceof ShipEntity) && entity.getVehicle() == null
				&& !entity.isSpectator() && who.test(entity))) {
			if (!isOnDeck(ship, entity, oldPos, (float) before[3])) {
				continue;
			}
			// Turn the entity's spot around the ship's old centre, then move it with the ship.
			Vec3 rel = entity.position().subtract(oldPos);
			float radians = turn * Mth.DEG_TO_RAD;
			float cos = Mth.cos(radians), sin = Mth.sin(radians);
			Vec3 turned = new Vec3(rel.x * cos - rel.z * sin, rel.y, rel.x * sin + rel.z * cos);
			entity.setPos(now[0] + turned.x, now[1] + turned.y, now[2] + turned.z);
			if (turn != 0) {
				entity.setYRot(entity.getYRot() + turn);
				entity.setYHeadRot(entity.getYHeadRot() + turn);
			}
		}
	}
}
