package com.onepiecemod.world;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.WeakHashMap;
import java.util.concurrent.ConcurrentHashMap;
import com.onepiecemod.world.mixin.JigsawStructureAccessor;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.QuartPos;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.biome.BiomeSource;
import net.minecraft.world.level.chunk.ChunkGeneratorStructureState;
import net.minecraft.world.level.levelgen.LegacyRandomSource;
import net.minecraft.world.level.levelgen.WorldgenRandom;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.levelgen.WorldGenerationContext;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.pools.EmptyPoolElement;
import net.minecraft.world.level.levelgen.structure.pools.StructurePoolElement;
import net.minecraft.world.level.levelgen.structure.structures.JigsawStructure;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureSet;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePiecesBuilder;
import net.minecraft.world.level.levelgen.structure.placement.ConcentricRingsStructurePlacement;
import net.minecraft.world.level.levelgen.structure.placement.RandomSpreadStructurePlacement;
import net.minecraft.world.level.levelgen.structure.placement.StructurePlacement;

/**
 * Keeps our structures apart: no two of them closer than {@link #GAP} blocks, footprint to footprint,
 * so towns, lairs and landmarks never spawn inside each other (one build's cleared air or ground used to
 * cut into the other and leave floating windmill sails, roofs and chains behind).
 * Vanilla only spaces structures within one structure set. Here every candidate also looks at the
 * candidates of all our sets around it, and gives way when a more important one really generates too close.
 * Importance is the set's place in {@link #RANK}; inside one set a seeded hash of the chunk decides, so the
 * answer never depends on which chunk generates first. A neighbour only counts if it really generates: its own
 * biome, terrain and spacing checks all run (recursively, always towards more important candidates, and every
 * answer is cached). Runs inside Structure.findValidGenerationPoint (via StructureSiteRules), so /locate, Sea
 * Charts and world generation all agree.
 * -Donepiece.structureGap=0 turns it off.
 */
public final class StructureSpacing {
	private StructureSpacing() {}

	public static final int GAP = Integer.getInteger("onepiece.structureGap", 200);
	/** Places the story sends the player to (onepiece/story.json "place"): these win over all but the landmarks. */
	private static final Set<String> STORY = Set.of("arlong_park", "twin_capes_lighthouse", "yuba_oasis", "alubarna_palace",
			"shandora", "amazon_lily", "punk_hazard_lab", "rusukaina", "ryugu_palace", "laugh_tale", "sabaody_park",
			"shakky_bar", "cricket_house");
	/** Inside this distance from the world centre (the East Blue and a bit), easy builds outrank medium ones. */
	private static final int EAST_BLUE = 2000;
	/** How far a neighbour's footprint can reach from its start chunk: half the widest build plus the site slide. */
	private static final int NEIGHBOUR_REACH = 128 + 112;
	/** Our structure sets from least to most important. Sets not listed (underground caves) are not spaced. Of the
	 * boss and landmark sets, the ones nearer the start win: their rings are smaller, so they have fewer spots
	 * (Alubarna has only a handful in the whole of Paradise). */
	private static final List<String> RANK = List.of("deep_trench_locations", "dungeon_locations", "dungeon_wano_locations", "nether_locations", "end_locations", "easy_locations",
			"medium_locations", "hard_locations", "legendary_locations", "boss_deep_new_world_locations",
			"boss_new_world_locations", "boss_paradise_locations", "boss_east_blue_locations", "landmark_locations",
			"landmark_new_world_locations", "landmark_paradise_locations", "early_landmark_locations", "foosha_village");

	/** How many neighbour checks deep this thread is. Each step goes to a strictly more important candidate, and the
	 * random tie-break inside a set keeps those chains short; past MAX_DEPTH a neighbour is judged on terrain alone. */
	private static final ThreadLocal<int[]> DEPTH = ThreadLocal.withInitial(() -> new int[1]);
	private static final int MAX_DEPTH = 24;

	private static final boolean DEBUG = Boolean.getBoolean("onepiece.spacingDebug");
	private static final org.slf4j.Logger LOGGER = org.slf4j.LoggerFactory.getLogger("onepiece/spacing");

	private static final Map<BiomeSource, Sets> WORLDS = Collections.synchronizedMap(new WeakHashMap<>());

	/** Called when a dimension's structure state is made (StructureStateMixin). */
	public static void register(ChunkGeneratorStructureState state, BiomeSource biomeSource) {
		WORLDS.put(biomeSource, new Sets(state));
	}

	private record SetInfo(Holder<StructureSet> set, String name, int rank) {}

	/** One dimension's spaced sets, which set each structure belongs to, and what each candidate generated. */
	private static final class Sets {
		final ChunkGeneratorStructureState state;
		private volatile List<SetInfo> sets;
		private volatile Map<Structure, SetInfo> bySet;
		final ConcurrentHashMap<String, Optional<BoundingBox>> generated = new ConcurrentHashMap<>();
		final ConcurrentHashMap<String, String> firstPicks = new ConcurrentHashMap<>();

		Sets(ChunkGeneratorStructureState state) {
			this.state = state;
		}

		synchronized void load() {
			if (sets != null) return;
			List<SetInfo> list = new ArrayList<>();
			Map<Structure, SetInfo> map = new HashMap<>();
			for (Holder<StructureSet> holder : state.possibleStructureSets()) {
				Optional<ResourceKey<StructureSet>> key = holder.unwrapKey();
				if (key.isEmpty() || !key.get().identifier().getNamespace().equals("onepiece")) continue;
				int rank = RANK.indexOf(key.get().identifier().getPath());
				if (rank < 0) continue;
				SetInfo info = new SetInfo(holder, key.get().identifier().getPath(), rank);
				list.add(info);
				for (StructureSet.StructureSelectionEntry e : holder.value().structures()) map.put(e.structure().value(), info);
			}
			bySet = map;
			sets = list;
		}
	}

	/** False when a more important structure of ours generates within GAP blocks of this footprint. */
	/**
	 * The footprints of more important structures of ours that really generate near this candidate; the build must
	 * stay GAP blocks clear of all of them ({@link #clear}). StructureSiteRules slides the build to such a spot when it
	 * can, so a build moves aside instead of vanishing. `slack` is how far it may slide. Returns null when the build
	 * must not generate at all: for a set placed on rings (Foosha Village) an earlier ring spot already holds one, so
	 * there is only ever one. `essential` builds keep clear of nothing but still stay unique.
	 */
	public static List<BoundingBox> blockers(Structure structure, Structure.GenerationContext ctx, BoundingBox box, boolean essential, int slack) {
		if (GAP <= 0 || DEPTH.get()[0] > MAX_DEPTH) return List.of();
		long t0 = DEBUG ? System.nanoTime() : 0;
		List<BoundingBox> out = find(structure, ctx, box, essential, slack);
		if (DEBUG) LOGGER.info("spacing {} -> {} in {} ms ({} cached)", ctx.chunkPos(), out == null ? "unique taken" : out.size() + " to keep clear of",
				(System.nanoTime() - t0) / 1_000_000, WORLDS.get(ctx.biomeSource()) == null ? 0 : WORLDS.get(ctx.biomeSource()).generated.size());
		return out;
	}

	/** True when the footprint keeps GAP blocks from every one of the blockers. */
	public static boolean clear(BoundingBox box, List<BoundingBox> blockers) {
		for (BoundingBox b : blockers) if (gap(box, b) < GAP) return false;
		return true;
	}

	private static List<BoundingBox> find(Structure structure, Structure.GenerationContext ctx, BoundingBox box, boolean essential, int slack) {
		Sets w = WORLDS.get(ctx.biomeSource());
		if (w == null) return List.of();
		w.load();
		SetInfo me = w.bySet.get(structure);
		if (me == null) return List.of();
		ChunkPos here = ctx.chunkPos();
		if (me.set.value().placement() instanceof ConcentricRingsStructurePlacement rings) {
			for (ChunkPos p : w.state.getRingPositionsFor(rings)) {
				if (p.equals(here)) break;
				if (generated(w, me, p, ctx).isPresent()) {
					if (DEBUG) LOGGER.info("spacing: {} at {} gives way to the one at {}", me.name, here, p);
					return null;
				}
			}
		}
		if (essential) return List.of();
		long[] mine = priority(w, me, here, ctx);
		int cx = (box.minX() + box.maxX()) / 2, cz = (box.minZ() + box.maxZ()) / 2;
		int reach = Math.max(box.getXSpan(), box.getZSpan()) / 2 + slack + GAP + NEIGHBOUR_REACH;
		List<BoundingBox> out = new ArrayList<>();
		for (SetInfo other : w.sets) {
			for (ChunkPos n : candidates(w, other, cx, cz, reach)) {
				if (other == me && n.equals(here)) continue;
				if (compare(priority(w, other, n, ctx), mine) <= 0) continue;
				Optional<BoundingBox> nb = generated(w, other, n, ctx);
				if (nb.isPresent() && gap(box, nb.get()) < GAP + slack * 1.5) {
					if (DEBUG) LOGGER.info("spacing: {} at {} keeps clear of {} at {} ({} blocks apart)", me.name, here, other.name, n, (int) gap(box, nb.get()));
					out.add(nb.get());
				}
			}
		}
		return out;
	}

	/**
	 * Who wins when two candidates are too close: first the set's rank (doubled, so a candidate can be lifted between
	 * two ranks), then a seeded hash of the chunk, then the chunk itself. Two lifts: inside the East Blue the easy builds
	 * (the first towns of the story) win over the medium ones, so they stay near the start, and a chunk whose first
	 * pick is a story place ({@link #STORY}) wins over everything but the landmarks and Foosha. Any fixed answer per
	 * chunk keeps the result the same whichever chunk generates first; it doesn't have to be the build that ends up there.
	 */
	private static long[] priority(Sets w, SetInfo info, ChunkPos p, Structure.GenerationContext ctx) {
		long rank = info.rank * 2L;
		if (info.name.equals("easy_locations")) {
			double bx = p.x() * 16 + 8, bz = p.z() * 16 + 8;
			if (bx * bx + bz * bz < (double) EAST_BLUE * EAST_BLUE) rank = RANK.indexOf("medium_locations") * 2L + 1;
		}
		long story = RANK.indexOf("landmark_locations") * 2L - 1;
		if (rank < story && STORY.contains(firstPick(w, info, p, ctx))) rank = story;
		long h = w.state.getLevelSeed() ^ (p.x() * 0x9E3779B97F4A7C15L) ^ (p.z() * 0xC2B2AE3D27D4EB4FL) ^ (rank << 40);
		h ^= h >>> 33;
		h *= 0xFF51AFD7ED558CCDL;
		h ^= h >>> 33;
		h *= 0xC4CEB9FE1A85EC53L;
		h ^= h >>> 33;
		return new long[] {rank, h, -p.x(), -p.z()};
	}

	/** The id of the first structure in the chunk's weighted draw (vanilla's order) whose biome fits, or "". */
	private static String firstPick(Sets w, SetInfo info, ChunkPos n, Structure.GenerationContext ctx) {
		String key = info.name + "@" + n.x() + "," + n.z();
		String done = w.firstPicks.get(key);
		if (done != null) return done;
		String result = "";
		for (StructureSet.StructureSelectionEntry e : drawOrder(w, info, n)) {
			if (startBiomeFits(e.structure().value(), n, ctx)) {
				result = e.structure().unwrapKey().map(k -> k.identifier().getPath()).orElse("");
				break;
			}
		}
		w.firstPicks.put(key, result);
		return result;
	}

	/** The order ChunkGenerator.createStructures tries a set's structures in at chunk n (weighted draw without putting back). */
	private static List<StructureSet.StructureSelectionEntry> drawOrder(Sets w, SetInfo info, ChunkPos n) {
		List<StructureSet.StructureSelectionEntry> list = new ArrayList<>(info.set.value().structures());
		if (list.size() == 1) return list;
		List<StructureSet.StructureSelectionEntry> out = new ArrayList<>();
		WorldgenRandom random = new WorldgenRandom(new LegacyRandomSource(0L));
		random.setLargeFeatureSeed(w.state.getLevelSeed(), n.x(), n.z());
		int total = 0;
		for (StructureSet.StructureSelectionEntry e : list) total += e.weight();
		while (!list.isEmpty()) {
			int pick = random.nextInt(total), k = 0;
			for (StructureSet.StructureSelectionEntry e : list) {
				pick -= e.weight();
				if (pick < 0) break;
				k++;
			}
			StructureSet.StructureSelectionEntry e = list.remove(k);
			total -= e.weight();
			out.add(e);
		}
		return out;
	}

	private static int compare(long[] a, long[] b) {
		for (int i = 0; i < a.length; i++) if (a[i] != b[i]) return Long.compare(a[i], b[i]);
		return 0;
	}

	private static double gap(BoundingBox a, BoundingBox b) {
		int dx = Math.max(0, Math.max(a.minX() - b.maxX(), b.minX() - a.maxX()));
		int dz = Math.max(0, Math.max(a.minZ() - b.maxZ(), b.minZ() - a.maxZ()));
		return Math.sqrt((double) dx * dx + (double) dz * dz);
	}

	/** The set's start chunks whose centre lies within `reach` blocks (square) of cx, cz. */
	private static List<ChunkPos> candidates(Sets w, SetInfo info, int cx, int cz, int reach) {
		List<ChunkPos> out = new ArrayList<>();
		StructurePlacement placement = info.set.value().placement();
		if (placement instanceof RandomSpreadStructurePlacement spread) {
			int spacing = spread.spacing();
			int c0x = Math.floorDiv(cx - reach, 16), c1x = Math.floorDiv(cx + reach, 16);
			int c0z = Math.floorDiv(cz - reach, 16), c1z = Math.floorDiv(cz + reach, 16);
			for (int gx = Math.floorDiv(c0x, spacing); gx <= Math.floorDiv(c1x, spacing); gx++) {
				for (int gz = Math.floorDiv(c0z, spacing); gz <= Math.floorDiv(c1z, spacing); gz++) {
					ChunkPos p = spread.getPotentialStructureChunk(w.state.getLevelSeed(), gx * spacing, gz * spacing);
					if (p.x() < c0x || p.x() > c1x || p.z() < c0z || p.z() > c1z) continue;
					if (spread.isStructureChunk(w.state, p.x(), p.z())) out.add(p);
				}
			}
		} else if (placement instanceof ConcentricRingsStructurePlacement rings) {
			for (ChunkPos p : w.state.getRingPositionsFor(rings)) {
				if (Math.abs(p.x() * 16 + 8 - cx) <= reach && Math.abs(p.z() * 16 + 8 - cz) <= reach) out.add(p);
			}
		}
		return out;
	}

	/** The footprint the set really generates at chunk n (picked the way ChunkGenerator.createStructures does), if any. */
	private static Optional<BoundingBox> generated(Sets w, SetInfo info, ChunkPos n, Structure.GenerationContext ctx) {
		String key = info.name + "@" + n.x() + "," + n.z();
		Optional<BoundingBox> done = w.generated.get(key);
		if (done != null) return done;
		Optional<BoundingBox> result = Optional.empty();
		for (StructureSet.StructureSelectionEntry e : drawOrder(w, info, n)) {
			result = tryOne(e, n, ctx);
			if (result.isPresent()) break;
		}
		if (DEBUG) LOGGER.info("spacing: {} -> {}", key, result.map(BoundingBox::toString).orElse("nothing"));
		w.generated.put(key, result);
		return result;
	}

	/**
	 * Vanilla's biome check for a jigsaw structure, done without the layout: JigsawStructure.findGenerationPoint and
	 * JigsawPlacement.addPieces draw the start height, the rotation and the start template from the chunk's random in
	 * this order, and the biome is read at the middle of that start piece, on the ground if projected. Anything this
	 * can't follow (a start jigsaw name, pool aliases, other structure types) counts as fitting, so the full check runs.
	 */
	public static boolean startBiomeFits(Structure structure, ChunkPos n, Structure.GenerationContext ctx) {
		if (!(structure instanceof JigsawStructure jigsaw) || !jigsaw.getPoolAliases().isEmpty()) return true;
		JigsawStructureAccessor acc = (JigsawStructureAccessor) (Object) jigsaw;
		if (acc.onepiece$startJigsawName().isPresent()) return true;
		try {
			Structure.GenerationContext c = new Structure.GenerationContext(ctx.registryAccess(), ctx.chunkGenerator(), ctx.biomeSource(),
					ctx.climateSampler(), ctx.randomState(), ctx.structureTemplateManager(), ctx.seed(), n, ctx.heightAccessor(), structure.biomes()::contains);
			WorldgenRandom random = c.random();
			int y = acc.onepiece$startHeight().sample(random, new WorldGenerationContext(ctx.chunkGenerator(), ctx.heightAccessor()));
			Rotation rotation = Rotation.getRandom(random);
			StructurePoolElement element = jigsaw.getStartPool().value().getRandomTemplate(random);
			if (element == EmptyPoolElement.INSTANCE) return false;
			BlockPos start = new BlockPos(n.getMinBlockX(), y, n.getMinBlockZ());
			BoundingBox box = element.getBoundingBox(ctx.structureTemplateManager(), start, rotation);
			int x = (box.maxX() + box.minX()) / 2, z = (box.maxZ() + box.minZ()) / 2;
			int by = acc.onepiece$projectStartToHeightmap().isPresent()
					? y + StructureSiteRules.exactHeight(ctx, acc.onepiece$projectStartToHeightmap().get(), x, z) : y;
			Holder<Biome> biome = ctx.biomeSource().createResolver(ctx.climateSampler()).getNoiseBiome(QuartPos.fromBlock(x),
					QuartPos.fromBlock(by), QuartPos.fromBlock(z));
			return structure.biomes().contains(biome);
		} catch (RuntimeException e) {
			return true;
		}
	}

	private static Optional<BoundingBox> tryOne(StructureSet.StructureSelectionEntry entry, ChunkPos n, Structure.GenerationContext ctx) {
		Structure structure = entry.structure().value();
		// Cheap first: vanilla checks the biome only after laying all the pieces out, at the middle of the start
		// piece. That spot can be worked out from the start piece alone, which costs almost nothing, and most picks
		// fail here.
		if (!startBiomeFits(structure, n, ctx)) {
			if (DEBUG) LOGGER.info("spacing: try {} at {}: wrong biome", entry.structure().unwrapKey().map(k -> k.identifier().getPath()).orElse("?"), n);
			return Optional.empty();
		}
		Structure.GenerationContext there = new Structure.GenerationContext(ctx.registryAccess(), ctx.chunkGenerator(),
				ctx.biomeSource(), ctx.climateSampler(), ctx.randomState(), ctx.structureTemplateManager(), ctx.seed(), n,
				ctx.heightAccessor(), structure.biomes()::contains);
		int[] depth = DEPTH.get();
		depth[0]++;
		try {
			Optional<Structure.GenerationStub> stub = structure.findValidGenerationPoint(there);
			if (DEBUG) LOGGER.info("spacing: try {} at {}: {}", entry.structure().unwrapKey().map(k -> k.identifier().getPath()).orElse("?"), n, stub.isPresent() ? "fits" : "no");
			if (stub.isEmpty()) return Optional.empty();
			StructurePiecesBuilder builder = stub.get().getPiecesBuilder();
			if (DEBUG && !builder.isEmpty()) LOGGER.info("spacing: picked {} at {}", entry.structure().unwrapKey().map(k -> k.identifier().getPath()).orElse("?"), n);
			return builder.isEmpty() ? Optional.empty() : Optional.of(builder.getBoundingBox());
		} finally {
			depth[0]--;
		}
	}
}
