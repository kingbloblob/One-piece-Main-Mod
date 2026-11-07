package com.onepiecemod.world;

import com.mojang.datafixers.util.Either;
import com.onepiecemod.world.mixin.JigsawStructureAccessor;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;
import java.util.concurrent.ConcurrentHashMap;
import java.util.Optional;
import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.RandomState;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePiecesBuilder;
import net.minecraft.world.level.levelgen.structure.structures.JigsawStructure;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Terrain check for our structures, on top of the biome check vanilla does at the start point.
 * The biome alone let a sea-floor wreck land on a beach hill and the Baratie sit on an island
 * (ocean biomes reach onto the shore, and the Grand Line is an archipelago of small islands).
 * This samples the ground across the structure's real footprint and, if the spot doesn't suit
 * its kind, slides the whole build up to {@link #MAX_SHIFT} blocks to the nearest spot that does;
 * if none fits, the structure is skipped here.
 * SEAFLOOR builds need water under the whole footprint with the build's top under the surface,
 * OPEN_SEA builds need water under the whole footprint, COAST builds need land in the middle and
 * sea at an edge, LAND builds need a mostly dry, not too steep footprint (so beard_thin doesn't
 * raise big platforms out of the sea).
 * Hooked into Structure.findValidGenerationPoint, so /locate agrees with world generation.
 */
public final class StructureSiteRules {
	private StructureSiteRules() {}

	private static final Logger LOGGER = LoggerFactory.getLogger("onepiece-sites");
	private static final boolean DEBUG = Boolean.getBoolean("onepiece.siteDebug");
	/** -Donepiece.siteRules=false turns the check off (vanilla placement), for comparing worlds. */
	private static final boolean ENABLED = !"false".equals(System.getProperty("onepiece.siteRules"));

	enum Site { SEAFLOOR, OPEN_SEA, COAST, LAND, ANY }

	private static final Set<String> SEAFLOOR = Set.of("sunken_galleon", "sea_king_bones", "fishman_district", "ryugu_palace");
	private static final Set<String> OPEN_SEA = Set.of("baratie", "moby_dick", "marine_battleship", "thriller_bark",
			"tequila_wolf", "impel_down");
	private static final Set<String> COAST = Set.of("arlong_park", "twin_capes_lighthouse", "nanohana_port",
			"going_merry_farewell", "sea_train_station", "den_den_outpost", "marineford", "galley_la_dock",
			"victoria_punk", "navarone", "marine_base",
			// islands drawn with their own ring of sea at y 0 (tools/landmarks/audit/quality.py: water on the build's edge).
			// As LAND builds they landed on dry hills with that sea standing on the ground and pouring off its edges
			// (ryan 2026-11-01); as coast builds they sit at sea level where the real sea meets them
			"auction_house", "baltigo", "banaro_island", "buggy_big_top", "chocolate_town", "corrida_colosseum",
			"cricket_house", "dadan_hideout", "davy_back_stage", "drum_castle", "ebisu_town", "foosha_village",
			"franky_house", "g5_base", "god_valley", "gray_terminal", "hachinosu", "kamazo_hideout",
			"little_garden_camp", "loguetown", "mary_geoise", "mirror_hall", "mock_town", "mokomo_dukedom",
			"momoiro_island", "onigashima", "punk_hazard_lab", "shells_town", "tower_of_justice", "toy_house",
			"wano_house", "whisky_peak", "whole_cake_chateau",
			// Wano dungeons (tools/dungeons): Wano's steep little islands almost never pass the LAND check
			"kitetsu_forge", "oden_shrine");
	/** Fixed-height builds: sky islands, Nether and End. Their own y is the rule. */
	private static final Set<String> ANY = Set.of("angel_beach", "weatheria", "shandora",
			"blazing_hell_furnace", "freezing_hell_cells", "newkama_land", "eternal_hell_vault",
			"pangaea_castle", "celestial_mansion", "void_century_ruins");

	private static final int GRID = 5;
	/** Worst score a land or coast build still accepts: up to 8 of the 25 columns under water. */
	private static final int ACCEPTABLE = 36;
	private static final int SLOPE_RANGE = 16;
	private static final int STEP = 24;
	/**
	 * A chunk only looks 8 chunks around for structure starts, so a build may slide at most
	 * 128 blocks minus half its width (and a chunk of slack) from its start chunk.
	 */
	private static final int MAX_SHIFT = 128 - 16;
	/** Story-critical: always placed on the best spot found, never skipped. */
	private static final Set<String> ESSENTIAL = Set.of("foosha_village");

	/** One of our (onepiece:) structures, and the site rules are on. */
	public static boolean ours(Structure structure, Structure.GenerationContext ctx) {
		if (!ENABLED) return false;
		Identifier id = ctx.registryAccess().lookupOrThrow(Registries.STRUCTURE).getKey(structure);
		return id != null && id.getNamespace().equals("onepiece");
	}

	static Site siteOf(Identifier id) {
		if (id == null || !id.getNamespace().equals("onepiece")) return Site.ANY;
		String p = id.getPath();
		if (ANY.contains(p)) return Site.ANY;
		if (SEAFLOOR.contains(p)) return Site.SEAFLOOR;
		if (OPEN_SEA.contains(p)) return Site.OPEN_SEA;
		if (COAST.contains(p)) return Site.COAST;
		return Site.LAND;
	}

	public static Optional<Structure.GenerationStub> filter(Structure structure, Structure.GenerationContext ctx,
			Optional<Structure.GenerationStub> found) {
		if (!ENABLED || found.isEmpty() || !(structure instanceof JigsawStructure jigsaw)) return found;
		Identifier id = ctx.registryAccess().lookupOrThrow(Registries.STRUCTURE).getKey(structure);
		Site site = siteOf(id);
		if (site == Site.ANY) return spaced(structure, id, ctx, found);
		Optional<Heightmap.Types> heightmap = ((JigsawStructureAccessor) (Object) jigsaw).onepiece$projectStartToHeightmap();
		if (heightmap.isEmpty()) return spaced(structure, id, ctx, found);

		Structure.GenerationStub stub = found.get();
		// Lay the pieces out once to get the real footprint; the finished builder is handed on so
		// generate() doesn't lay them out a second time.
		StructurePiecesBuilder builder = stub.getPiecesBuilder();
		if (builder.isEmpty()) return found;
		BoundingBox box = builder.getBoundingBox();
		BlockPos start = stub.position();
		ChunkGenerator gen = ctx.chunkGenerator();
		int startGround = height(ctx, heightmap.get(), start.getX(), start.getZ());

		// Sea builds must find water or they are skipped; land and coast builds take the best spot
		// of up to 81 as long as it isn't mostly sea (a town on a hillside is fine, a town on a
		// sand platform raised out of the ocean is not).
		boolean strict = site == Site.SEAFLOOR || site == Site.OPEN_SEA;
		boolean essential = ESSENTIAL.contains(id.getPath());
		// A spot must score under this to matter: better than the best so far, and (unless essential) good enough to
		// be accepted at all. score() stops sampling a spot as soon as it can't get under it, which gives the same
		// answer as scoring every spot in full but skips most of the (slow) ground sampling over open sea.
		int acceptLimit = essential ? Integer.MAX_VALUE : ((strict ? 0 : ACCEPTABLE) + 1) * SLOPE_RANGE;
		int rings = Math.max(0, (MAX_SHIFT - Math.max(box.getXSpan(), box.getZSpan()) / 2) / STEP);
		int[][] spots = spiral(Math.min(rings, 4));
		// Most candidates sit on ground that suits no spot at all (a town in open sea). Find that out before asking
		// StructureSpacing about the neighbours, which lays out every more important build nearby and is far slower.
		// Skipping it then changes nothing: with no spot good enough the build is skipped whatever the neighbours are.
		if (!essential && !anySpotFits(id, site, box, start, startGround, heightmap.get(), ctx, spots, acceptLimit)) return Optional.empty();
		// our more important builds nearby: every spot tried must keep clear of them (StructureSpacing)
		List<BoundingBox> keepClear = StructureSpacing.blockers(structure, ctx, box, essential, MAX_SHIFT);
		if (keepClear == null) return Optional.empty();
		int bestScore = Integer.MAX_VALUE, bestDx = 0, bestDy = 0, bestDz = 0;
		for (int[] o : spots) {
			int dx = o[0], dz = o[1];
			if (!StructureSpacing.clear(box.moved(dx, 0, dz), keepClear)) continue;
			// the build follows the ground at its start point, like vanilla's heightmap projection
			int dy = dx == 0 && dz == 0 ? 0
					: height(ctx, heightmap.get(), start.getX() + dx, start.getZ() + dz) - startGround;
			int score = score(id, site, box.moved(dx, dy, dz), ctx, Math.min(bestScore, acceptLimit));
			if (score < bestScore) {
				bestScore = score;
				bestDx = dx;
				bestDy = dy;
				bestDz = dz;
			}
			if (score <= 4) break; // dry and fairly flat: good enough, stop looking
		}
		if (bestScore == Integer.MAX_VALUE || (bestScore / SLOPE_RANGE > (strict ? 0 : ACCEPTABLE) && !essential)) return Optional.empty();
		if (site == Site.COAST) bestDy += toSea(ctx, startGround + bestDy);
		else if (!strict) bestDy += settle(ctx, box.moved(bestDx, 0, bestDz), startGround + bestDy);
		if (bestDx != 0 || bestDy != 0 || bestDz != 0) {
			for (StructurePiece piece : builder.build().pieces()) piece.move(bestDx, bestDy, bestDz);
			start = start.offset(bestDx, bestDy, bestDz);
		}
		return Optional.of(new Structure.GenerationStub(start, Either.right(builder)));
	}

	/** True if at least one spot (ignoring the neighbours) scores under `limit`. */
	private static boolean anySpotFits(Identifier id, Site site, BoundingBox box, BlockPos start, int startGround, Heightmap.Types heightmap,
			Structure.GenerationContext ctx, int[][] spots, int limit) {
		for (int[] o : spots) {
			int dx = o[0], dz = o[1];
			int dy = dx == 0 && dz == 0 ? 0 : height(ctx, heightmap, start.getX() + dx, start.getZ() + dz) - startGround;
			if (score(id, site, box.moved(dx, dy, dz), ctx, limit) < limit) return true;
		}
		return false;
	}

	/** Keeps a build that needs no terrain check clear of our other builds too (StructureSpacing). */
	private static Optional<Structure.GenerationStub> spaced(Structure structure, Identifier id, Structure.GenerationContext ctx,
			Optional<Structure.GenerationStub> found) {
		if (id == null) return found;
		Structure.GenerationStub stub = found.get();
		StructurePiecesBuilder builder = stub.getPiecesBuilder();
		if (builder.isEmpty()) return found;
		List<BoundingBox> keepClear = StructureSpacing.blockers(structure, ctx, builder.getBoundingBox(), ESSENTIAL.contains(id.getPath()), 0);
		if (keepClear == null || !StructureSpacing.clear(builder.getBoundingBox(), keepClear)) return Optional.empty();
		return Optional.of(new Structure.GenerationStub(stub.position(), Either.right(builder)));
	}

	/** Ground heights already worked out, per world: sampling the noise is the slow part of both this check and
	 * StructureSpacing, and neighbouring candidates sample the same ground over and over. Points are snapped to a
	 * 4-block grid, which is far finer than the 5x5 grid laid over a build. */
	private static final Map<RandomState, ConcurrentHashMap<Long, Integer>> HEIGHTS = Collections.synchronizedMap(new WeakHashMap<>());

	static int height(Structure.GenerationContext ctx, Heightmap.Types type, int x, int z) {
		ConcurrentHashMap<Long, Integer> cache = HEIGHTS.computeIfAbsent(ctx.randomState(), r -> new ConcurrentHashMap<>());
		if (cache.size() > 400_000) cache.clear();
		int sx = (x & ~3) + 2, sz = (z & ~3) + 2;
		long key = ((long) sx << 36) ^ ((long) (sz & 0xFFFFFFFL) << 4) ^ type.ordinal();
		Integer h = cache.get(key);
		if (h == null) {
			h = ctx.chunkGenerator().getFirstFreeHeight(sx, sz, type, ctx.heightAccessor(), ctx.randomState());
			cache.put(key, h);
		}
		return h;
	}

	/** Exact ground heights (not snapped), for checks that must match vanilla's own reading to the block. */
	private static final Map<RandomState, ConcurrentHashMap<Long, Integer>> EXACT_HEIGHTS = Collections.synchronizedMap(new WeakHashMap<>());

	static int exactHeight(Structure.GenerationContext ctx, Heightmap.Types type, int x, int z) {
		ConcurrentHashMap<Long, Integer> cache = EXACT_HEIGHTS.computeIfAbsent(ctx.randomState(), r -> new ConcurrentHashMap<>());
		if (cache.size() > 200_000) cache.clear();
		long key = ((long) x << 36) ^ ((long) (z & 0xFFFFFFFL) << 4) ^ type.ordinal();
		Integer h = cache.get(key);
		if (h == null) {
			h = ctx.chunkGenerator().getFirstFreeHeight(x, z, type, ctx.heightAccessor(), ctx.randomState());
			cache.put(key, h);
		}
		return h;
	}

	/**
	 * How far to move a land or coast build up or down so it sits IN the ground rather than on top of it. Vanilla
	 * puts the build's ground level at the height under its start piece; on a slope, or with the start on a hilltop,
	 * the rest of the site then hangs in the air over a wall of dirt (ryan 2026-10-25: "spawn higher than it should").
	 * This uses the lower third of the dry ground under the footprint instead (never below the sea), so the build
	 * settles a little into the slope and the edge skirt meets the real ground. At most 8 blocks either way.
	 */
	private static int settle(Structure.GenerationContext ctx, BoundingBox box, int groundNow) {
		int sea = ctx.chunkGenerator().getSeaLevel();
		int x0 = box.minX() + 2, x1 = box.maxX() - 2, z0 = box.minZ() + 2, z1 = box.maxZ() - 2;
		List<Integer> dry = new ArrayList<>();
		for (int i = 0; i < GRID; i++) {
			for (int j = 0; j < GRID; j++) {
				int h = height(ctx, Heightmap.Types.OCEAN_FLOOR_WG, x0 + (x1 - x0) * i / (GRID - 1), z0 + (z1 - z0) * j / (GRID - 1));
				if (h >= sea) dry.add(h);
			}
		}
		if (dry.size() < 5) return 0;
		Collections.sort(dry);
		int target = Math.max(sea, dry.get(dry.size() * 3 / 10));
		return Math.max(-8, Math.min(8, target - groundNow));
	}

	/**
	 * Coast builds are drawn with their y 0 at the sea surface: quays, harbour basins and moored ships carry water at that
	 * level. On a high shore the old settle() kept them on the ground, so the harbour water stood on a hilltop and poured
	 * off its edge (ryan 2026-11-01: "some builds spawn weird"). They now always sit at sea level; score() prefers low
	 * shores, so the hill they cut into is small.
	 */
	private static int toSea(Structure.GenerationContext ctx, int groundNow) {
		return Math.max(-24, Math.min(8, ctx.chunkGenerator().getSeaLevel() - groundNow));
	}

	/** The 5x5 sample grid, middle first, then the rest of the inner 3x3, then the edge: what decides a spot early. */
	private static final int[][] SAMPLE_ORDER = sampleOrder();

	private static int[][] sampleOrder() {
		List<int[]> out = new ArrayList<>();
		out.add(new int[] {GRID / 2, GRID / 2});
		for (int pass = 0; pass < 2; pass++) {
			for (int i = 0; i < GRID; i++) {
				for (int j = 0; j < GRID; j++) {
					boolean inner = i >= 1 && i <= GRID - 2 && j >= 1 && j <= GRID - 2;
					if ((i == GRID / 2 && j == GRID / 2) || inner != (pass == 0)) continue;
					out.add(new int[] {i, j});
				}
			}
		}
		return out.toArray(new int[0][]);
	}

	/**
	 * 0 = the spot suits the build; higher is worse. Once the spot is sure to score `limit` or more, sampling stops
	 * and Integer.MAX_VALUE comes back (the caller ignores such spots, so the answer is the same as a full score).
	 */
	private static int score(Identifier id, Site site, BoundingBox box, Structure.GenerationContext ctx, int limit) {
		ChunkGenerator gen = ctx.chunkGenerator();
		int sea = gen.getSeaLevel();
		// a seafloor build that pokes out of the water is out whatever the ground does
		if (site == Site.SEAFLOOR && box.maxY() > sea - 2 && limit <= SLOPE_RANGE) return Integer.MAX_VALUE;
		int x0 = box.minX() + 2, x1 = box.maxX() - 2, z0 = box.minZ() + 2, z1 = box.maxZ() - 2;
		int wet = 0, dry = 0, dryMin = Integer.MAX_VALUE, dryMax = Integer.MIN_VALUE;
		int floorMin = Integer.MAX_VALUE, floorMax = Integer.MIN_VALUE, center = 0;
		boolean innerDry = true;
		for (int[] sample : SAMPLE_ORDER) {
			int i = sample[0], j = sample[1];
			int x = x0 + (x1 - x0) * i / (GRID - 1);
			int z = z0 + (z1 - z0) * j / (GRID - 1);
			// top of the solid ground (water doesn't count)
			int h = height(ctx, Heightmap.Types.OCEAN_FLOOR_WG, x, z);
			floorMin = Math.min(floorMin, h);
			floorMax = Math.max(floorMax, h);
			boolean inner = i >= 1 && i <= GRID - 2 && j >= 1 && j <= GRID - 2;
			if (i == GRID / 2 && j == GRID / 2) center = h;
			if (h >= sea) {
				dry++;
				dryMin = Math.min(dryMin, h);
				dryMax = Math.max(dryMax, h);
			} else {
				wet++;
				if (inner) innerDry = false;
			}
			// the least this spot can still score, whatever the samples not taken yet say
			int least = switch (site) {
				case SEAFLOOR -> floorMax <= sea - 4 && box.maxY() <= sea - 2 ? 0 : 1;
				case OPEN_SEA -> floorMax <= sea - 3 && center <= sea - 6 ? 0 : 1;
				// the middle is sampled first; past 6 wet columns more water only makes it worse
				case COAST -> (center < sea ? 40 : 0) + (wet > 6 ? wet - 6 : 0) + (wet > 10 ? (wet - 10) * 4 : 0);
				case LAND -> wet * 2 + (innerDry ? 0 : 20);
				case ANY -> 0;
			};
			if (least * SLOPE_RANGE >= limit) return Integer.MAX_VALUE;
		}
		int score = switch (site) {
			// water under everything, at least 4 deep, and the build's top stays under the surface
			case SEAFLOOR -> (floorMax <= sea - 4 && box.maxY() <= sea - 2) ? 0 : 1;
			// open water under the whole footprint, deeper in the middle
			case OPEN_SEA -> (floorMax <= sea - 3 && center <= sea - 6) ? 0 : 1;
			// dry middle, a few sea columns round the edge; 0 = ideal
			// (and a low shore: the build is set down to sea level, so every block of shore above it is dug away)
			case COAST -> (center < sea ? 40 : 0) + Math.abs(Math.max(wet, 3) - 6) + (wet > 10 ? (wet - 10) * 4 : 0)
					+ (dry > 0 ? Math.max(0, dryMax - sea - 6) / 2 : 0);
			// as dry as possible, nothing wet under the middle; 0 = ideal
			case LAND -> wet * 2 + (innerDry ? 0 : 20);
			case ANY -> 0;
		};
		// ...then, between two spots that are equally good, the flatter one: a build on a big slope floats on one side
		// or is buried on the other. Slope only breaks ties (score / SLOPE_RANGE is what must be ACCEPTABLE), so it
		// never rules a mountain island out.
		int slope = site == Site.LAND || site == Site.COAST ? Math.min(SLOPE_RANGE - 1, Math.max(0, dryMax - dryMin - 4)) : 0;
		score = score * SLOPE_RANGE + (dry > 0 ? slope : 0);
		if (DEBUG) LOGGER.info("site {} {} {} box {}x{}x{} wet {} dry {} innerDry {} dry {}..{} floor {}..{} center {} -> {}",
				id, site, box.getCenter(), box.getXSpan(), box.getYSpan(), box.getZSpan(), wet, dry, innerDry, dryMin, dryMax, floorMin, floorMax, center, score);
		return score;
	}

	private static int[][] spiral(int rings) {
		List<int[]> out = new ArrayList<>();
		out.add(new int[] {0, 0});
		for (int r = 1; r <= rings; r++) {
			for (int i = -r; i <= r; i++) {
				for (int j = -r; j <= r; j++) {
					if (Math.max(Math.abs(i), Math.abs(j)) == r) out.add(new int[] {i * STEP, j * STEP});
				}
			}
		}
		return out.toArray(new int[0][]);
	}
}
