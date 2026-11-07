package com.onepiecemod.voyage;

import org.jetbrains.annotations.Nullable;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Difficulty;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.sea.CalmBelt;
import com.onepiecemod.ship.ShipEntity;

/** Small helpers shared by the sea encounters: who is out sailing, and where there is open sea to put something. */
final class SeaSpots {
	private SeaSpots() {
	}

	/** The ship this player is sailing on the surface of an Overworld sea, or null (on land, diving, creative...). */
	@Nullable
	static ShipEntity sailing(ServerPlayer player) {
		if (player.isSpectator() || player.isCreative() || player.level().dimension() != Level.OVERWORLD) {
			return null;
		}
		if (!(ShipEntity.aboard(player) instanceof ShipEntity ship) || ship.sinking || com.onepiecemod.deepsea.ShipDive.isDown(ship)
				|| com.onepiecemod.shipcombat.ShipBrain.isAi(ship)) {
			return null;
		}
		return ship;
	}

	static boolean peaceful(ServerLevel level) {
		return level.getDifficulty() == Difficulty.PEACEFUL;
	}

	/** Which sea a spot is in, or null if it's not open sea. */
	@Nullable
	static CalmBelt.Sea sea(ServerLevel level, BlockPos pos) {
		return CalmBelt.seaAt(level, pos);
	}

	/** The y of the first air block above the sea here if it is open water at least `depth` deep, otherwise null. */
	@Nullable
	static Integer waterSurface(ServerLevel level, int x, int z, int depth) {
		if (!level.hasChunkAt(new BlockPos(x, 0, z))) {
			return null;
		}
		int top = level.getHeight(Heightmap.Types.WORLD_SURFACE, x, z);
		int floor = level.getHeight(Heightmap.Types.OCEAN_FLOOR, x, z);
		if (!level.getFluidState(new BlockPos(x, top - 1, z)).is(FluidTags.WATER) || top - floor < depth) {
			return null;
		}
		return top;
	}

	/** True if a square `reach` blocks out from the middle (and the middle) is all open water `depth` deep. */
	static boolean open(ServerLevel level, int x, int z, int reach, int depth) {
		return waterSurface(level, x, z, depth) != null && waterSurface(level, x + reach, z, depth) != null
				&& waterSurface(level, x - reach, z, depth) != null && waterSurface(level, x, z + reach, depth) != null
				&& waterSurface(level, x, z - reach, depth) != null;
	}

	/**
	 * Open water `distance` to `distance + spread` blocks from the ship, within `cone` degrees of where it's heading
	 * (360 = anywhere). Null if none of the tries found any.
	 */
	@Nullable
	static BlockPos openWaterNear(ServerLevel level, ShipEntity ship, double distance, double spread, float cone, int reach, int depth) {
		RandomSource random = level.getRandom();
		for (int attempt = 0; attempt < 24; attempt++) {
			float yaw = ship.getYRot() + (random.nextFloat() - 0.5f) * cone;
			double far = distance + random.nextDouble() * spread;
			int x = Mth.floor(ship.getX() - Mth.sin(yaw * Mth.DEG_TO_RAD) * far);
			int z = Mth.floor(ship.getZ() + Mth.cos(yaw * Mth.DEG_TO_RAD) * far);
			if (open(level, x, z, reach, depth)) {
				Integer surface = waterSurface(level, x, z, depth);
				return new BlockPos(x, surface, z);
			}
		}
		return null;
	}

	/** True if any player at all (spectators too) is within this many blocks, flat distance. */
	static boolean anyPlayerNear(ServerLevel level, Vec3 at, double within) {
		for (net.minecraft.server.level.ServerPlayer player : level.players()) {
			double dx = player.getX() - at.x;
			double dz = player.getZ() - at.z;
			if (dx * dx + dz * dz < within * within) {
				return true;
			}
		}
		return false;
	}

	/** A point beside the ship, `out` blocks off to one side (left or right at random), at sea level minus `under`. */
	static Vec3 beside(ServerLevel level, ShipEntity ship, double out, double under) {
		float yaw = (ship.getYRot() + (level.getRandom().nextBoolean() ? 90 : -90)) * Mth.DEG_TO_RAD;
		return new Vec3(ship.getX() - Mth.sin(yaw) * out, level.getSeaLevel() - under, ship.getZ() + Mth.cos(yaw) * out);
	}
}
