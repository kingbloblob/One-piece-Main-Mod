package com.onepiecemod.sea;

import java.util.List;
import java.util.Optional;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.QuartPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BiomeTags;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.biome.BiomeSource;
import net.minecraft.world.level.levelgen.Heightmap;

/**
 * Finds islands for the Log Pose. It asks the world generator which biome will be at sea level,
 * the same way /locate biome does, so it works on land that hasn't been generated yet
 * and it doesn't slow the game down by loading chunks.
 */
public class IslandFinder {
	/** Islands closer together than this count as the same island. */
	public static final int ISLAND_SPACING = 256;
	/** How far the Log Pose can sense the next island. */
	private static final int SEARCH_RADIUS = 2048;
	private static final int STEP = 32;
	/** The search looks for the nearest island in each of this many directions. */
	private static final int SECTORS = 16;
	/** How strongly the route prefers islands further out: 0.5 means each block outward counts as half a block less sailing. */
	private static final double OUTWARD_PULL = 0.5;

	/**
	 * The next island on the route from {@code from}, skipping islands in {@code visited}. Empty if there's only sea in range.
	 *
	 * Like the real Log Pose, the route runs onward: it looks at the nearest island in each direction and
	 * prefers ones further from the world's center, so following the needle leads from the East Blue out
	 * through Paradise into the New World. A much closer island the other way can still win.
	 */
	public static Optional<BlockPos> findNext(ServerLevel level, BlockPos from, List<BlockPos> visited) {
		int seaLevel = level.getSeaLevel();
		BlockPos[] nearestPerSector = new BlockPos[SECTORS];
		BlockPos best = null;
		double bestScore = Double.MAX_VALUE;
		for (int radius = STEP; radius <= SEARCH_RADIUS; radius += STEP) {
			// Nothing further out can beat what we have: even straight outward it would score at least radius * (1 - OUTWARD_PULL).
			if (best != null && radius * (1.0 - OUTWARD_PULL) > bestScore) {
				break;
			}
			int points = Math.max(8, (int) (2 * Math.PI * radius / STEP));
			for (int i = 0; i < points; i++) {
				double angle = 2 * Math.PI * i / points;
				int sector = (int) (i * (long) SECTORS / points);
				if (nearestPerSector[sector] != null) {
					continue;
				}
				int x = from.getX() + (int) Math.round(Math.cos(angle) * radius);
				int z = from.getZ() + (int) Math.round(Math.sin(angle) * radius);
				BlockPos spot = new BlockPos(x, seaLevel, z);
				if (farFromAll(spot, visited) && isLand(biomeAt(level, spot)) && aboveWater(level, spot)) {
					nearestPerSector[sector] = spot;
					double score = radius - OUTWARD_PULL * (distanceFromCenter(spot) - distanceFromCenter(from));
					if (score < bestScore) {
						bestScore = score;
						best = spot;
					}
				}
			}
		}
		return Optional.ofNullable(best);
	}

	/** Real dry land there, not just a beach biome over shallow water. */
	private static boolean aboveWater(ServerLevel level, BlockPos spot) {
		return level.getChunkSource().getGenerator().getBaseHeight(spot.getX(), spot.getZ(), Heightmap.Types.OCEAN_FLOOR_WG,
				level, level.getChunkSource().randomState()) > level.getSeaLevel() + 1;
	}

	private static double distanceFromCenter(BlockPos pos) {
		return Math.sqrt((double) pos.getX() * pos.getX() + (double) pos.getZ() * pos.getZ());
	}

	/** The name of the biome there, like "Alabasta" or "Jungle", to tell the player where they're headed. */
	public static Component islandName(ServerLevel level, BlockPos pos) {
		String id = biomeAt(level, pos).getRegisteredName(); // e.g. "onepiece:alabasta"
		return Component.translatable("biome." + id.replace(':', '.'));
	}

	public static boolean isLand(Holder<Biome> biome) {
		return !CalmBelt.isOcean(biome) && !biome.is(BiomeTags.IS_RIVER);
	}

	public static double horizontalDistance(BlockPos a, BlockPos b) {
		double dx = a.getX() - b.getX();
		double dz = a.getZ() - b.getZ();
		return Math.sqrt(dx * dx + dz * dz);
	}

	private static boolean farFromAll(BlockPos spot, List<BlockPos> visited) {
		for (BlockPos island : visited) {
			if (horizontalDistance(spot, island) < ISLAND_SPACING) {
				return false;
			}
		}
		return true;
	}

	/** Which biome the world generator will put here, without loading the chunk. */
	private static Holder<Biome> biomeAt(ServerLevel level, BlockPos pos) {
		BiomeSource source = level.getChunkSource().getGenerator().getBiomeSource();
		return source.createUncachedResolver(level.getChunkSource().randomState())
				.getNoiseBiome(QuartPos.fromBlock(pos.getX()), QuartPos.fromBlock(pos.getY()), QuartPos.fromBlock(pos.getZ()));
	}
}
