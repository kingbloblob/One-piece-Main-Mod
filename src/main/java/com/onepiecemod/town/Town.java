package com.onepiecemod.town;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.BedBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BedPart;
import net.minecraft.world.level.levelgen.structure.BoundingBox;

/**
 * One town in the world (one generated Foosha Village, one Water 7...), found from its structure.
 *
 * The first time a player comes near, the town looks over its own blocks a little each tick (a "scan") to learn
 * where the beds, workplaces, docks, bar and open plaza are. Townsfolk use those spots for their daily routine.
 * Nothing here is saved: it's rebuilt from the blocks whenever the world loads.
 */
public class Town {
	private static final int BLOCKS_PER_TICK = 24000;
	private static final int MAX_SPOTS = 96;

	public final String structureId;
	public final TownData.TownDef def;
	public final ServerLevel level;
	public final BoundingBox box;
	/** Unique per town, saved on its townsfolk: "foosha_village@12,-40". */
	public final String key;

	// What the scan found.
	public final List<BlockPos> beds = new ArrayList<>();
	public final List<BlockPos> indoor = new ArrayList<>();
	public final List<BlockPos> open = new ArrayList<>();
	public final List<BlockPos> water = new ArrayList<>();
	/** Dry ground right next to the water: piers, beaches and quays, where fishers and shipwrights work. */
	public final List<BlockPos> docks = new ArrayList<>();
	public final List<BlockPos> barMarkers = new ArrayList<>();
	public final Map<String, List<BlockPos>> workBlocks = new HashMap<>();
	public BlockPos plaza;
	public BlockPos bar;
	public final List<BlockPos> marketSpots = new ArrayList<>();
	public boolean scanned;
	private long scanStarted = -1;

	private final Deque<long[]> columns = new ArrayDeque<>();
	private final java.util.Set<String> wantedBlocks = new java.util.HashSet<>();

	// Live state.
	public long lastVisited;
	public String forcedFestival;
	public long forcedUntil;
	/** A victory banquet for this player name, until this game time. */
	public String banquetFor;
	public long banquetUntil;
	public long lastFestivalDay = -1;
	public String lastFestivalId;
	public final java.util.Set<java.util.UUID> giftsGiven = new java.util.HashSet<>();
	public final java.util.Set<java.util.UUID> announcedTo = new java.util.HashSet<>();
	/** Spots townsfolk couldn't find a way to (sealed rooms, roofs, behind walls), skipped until the given game time. */
	private final Map<BlockPos, Long> unreachable = new HashMap<>();

	public Town(String structureId, TownData.TownDef def, ServerLevel level, BoundingBox box, String key) {
		this.structureId = structureId;
		this.def = def;
		this.level = level;
		this.box = box;
		this.key = key;
		for (String job : def.jobs.keySet()) {
			wantedBlocks.addAll(TownData.job(job).workBlocks);
		}
		for (int x = box.minX(); x <= box.maxX(); x++) {
			for (int z = box.minZ(); z <= box.maxZ(); z++) {
				columns.add(new long[] {x, z});
			}
		}
		this.plaza = new BlockPos(box.getCenter().getX(), box.minY() + 1, box.getCenter().getZ());
		this.bar = plaza;
	}

	public String name() {
		return def.name.isEmpty() ? structureId : def.name;
	}

	public boolean contains(BlockPos pos, int margin) {
		return pos.getX() >= box.minX() - margin && pos.getX() <= box.maxX() + margin
				&& pos.getZ() >= box.minZ() - margin && pos.getZ() <= box.maxZ() + margin
				&& pos.getY() >= box.minY() - margin && pos.getY() <= box.maxY() + margin;
	}

	/** True when every corner of the town has its entities loaded, so counting townsfolk gives the real number. */
	public boolean entitiesLoaded() {
		int y = box.minY();
		return level.isPositionEntityTicking(new BlockPos(box.minX(), y, box.minZ()))
				&& level.isPositionEntityTicking(new BlockPos(box.maxX(), y, box.minZ()))
				&& level.isPositionEntityTicking(new BlockPos(box.minX(), y, box.maxZ()))
				&& level.isPositionEntityTicking(new BlockPos(box.maxX(), y, box.maxZ()))
				&& level.isPositionEntityTicking(box.getCenter());
	}

	public boolean isAngryAt(java.util.UUID player) {
		return TownGrudges.isAngry(this, player); // Saved with the world (see TownGrudges).
	}

	// ---------- Scanning ----------

	/** Looks at a slice of the town's blocks. Returns true once everything has been seen. */
	public boolean scanSome() {
		if (scanned) {
			return true;
		}
		int budget = BLOCKS_PER_TICK;
		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
		int height = box.maxY() - box.minY() + 1;
		if (scanStarted < 0) {
			scanStarted = level.getGameTime();
		}
		boolean givingUp = level.getGameTime() - scanStarted > 20 * 60;
		int unloadedInARow = 0;
		while (budget > 0 && !columns.isEmpty() && unloadedInARow < columns.size()) {
			long[] column = columns.poll();
			int x = (int) column[0];
			int z = (int) column[1];
			if (!level.hasChunkAt(pos.set(x, box.minY(), z))) {
				// Not loaded yet (the player just arrived): try again later. After a minute, do without it.
				if (!givingUp) {
					columns.add(column);
					unloadedInARow++;
				}
				budget -= 16;
				continue;
			}
			unloadedInARow = 0;
			scanColumn(x, z, pos);
			budget -= height;
		}
		if (columns.isEmpty()) {
			finishScan();
			scanned = true;
		}
		return scanned;
	}

	private void scanColumn(int x, int z, BlockPos.MutableBlockPos pos) {
		boolean sample = Math.floorMod(x, 3) == 0 && Math.floorMod(z, 3) == 0;
		BlockState above2 = null;
		BlockState above1 = null;
		for (int y = box.maxY(); y >= box.minY(); y--) {
			BlockState state = level.getBlockState(pos.set(x, y, z));
			if (state.getBlock() instanceof BedBlock && state.getValue(BedBlock.PART) == BedPart.HEAD) {
				beds.add(pos.immutable());
			}
			if (!state.isAir()) {
				String id = BuiltInRegistries.BLOCK.getKey(state.getBlock()).toString();
				if (wantedBlocks.contains(id)) {
					List<BlockPos> list = workBlocks.computeIfAbsent(id, k -> new ArrayList<>());
					if (list.size() < MAX_SPOTS) {
						list.add(pos.immutable());
					}
				}
				if (id.equals("minecraft:brewing_stand") || id.equals("minecraft:barrel") || id.equals("onepiece:sake_barrel")) {
					if (barMarkers.size() < MAX_SPOTS) {
						barMarkers.add(pos.immutable());
					}
				}
			}
			// A spot to stand: something solid underfoot, two free blocks above.
			if (above1 != null && above2 != null && isFree(above1) && isFree(above2)) {
				if (state.getFluidState().is(FluidTags.WATER)) {
					if (sample && water.size() < MAX_SPOTS) {
						water.add(pos.immutable().above());
					}
				} else if (state.isSolid() && docks.size() < MAX_SPOTS && Math.floorMod(x + z, 2) == 0 && nextToWater(x, y, z)) {
					docks.add(new BlockPos(x, y + 1, z));
				}
				if (state.isSolid() && sample && state.getFluidState().isEmpty()) {
					BlockPos feet = pos.immutable().above();
					if (level.canSeeSky(feet)) {
						if (open.size() < MAX_SPOTS * 3) {
							open.add(feet);
						}
					} else if (indoor.size() < MAX_SPOTS) {
						indoor.add(feet);
					}
				}
			}
			above2 = above1;
			above1 = state;
		}
	}

	/** Ground at the water's edge: water beside it at the same height, and dry beside where you'd stand (so not a hole below the sea). */
	private boolean nextToWater(int x, int y, int z) {
		boolean water = false;
		for (net.minecraft.core.Direction side : net.minecraft.core.Direction.Plane.HORIZONTAL) {
			BlockPos beside = new BlockPos(x + side.getStepX(), y, z + side.getStepZ());
			if (level.getFluidState(beside.above()).is(FluidTags.WATER)) {
				return false;
			}
			water |= level.getFluidState(beside).is(FluidTags.WATER) && level.getBlockState(beside.above()).isAir(); // The surface, not a hole under it.
		}
		return water;
	}

	private static boolean isFree(BlockState state) {
		return !state.isSolid() && state.getFluidState().isEmpty();
	}

	/** Roofs and walls look like open ground from above: there's a room (two free blocks) just under them. */
	private boolean onARoof(BlockPos feet) {
		for (int down = 2; down <= 6; down++) {
			BlockPos pos = feet.below(down);
			if (isFree(level.getBlockState(pos)) && isFree(level.getBlockState(pos.below()))) {
				return true;
			}
		}
		return false;
	}

	private void finishScan() {
		open.removeIf(this::onARoof);
		docks.removeIf(this::onARoof);
		BlockPos center = box.getCenter();
		// The plaza: the open spot nearest the middle of town, a little above the lowest ground.
		BlockPos best = null;
		double bestScore = Double.MAX_VALUE;
		for (BlockPos spot : open) {
			double score = horizontal(spot, center) + Math.max(0, spot.getY() - center.getY()) * 0.5;
			if (score < bestScore) {
				bestScore = score;
				best = spot;
			}
		}
		if (best != null) {
			plaza = best;
		}
		// The bar: the busiest corner of barrels and brewing stands (indoors if possible), else near the plaza.
		BlockPos barSpot = null;
		int most = 0;
		for (BlockPos marker : barMarkers) {
			int count = 0;
			for (BlockPos other : barMarkers) {
				if (other.distSqr(marker) < 49) {
					count++;
				}
			}
			if (count > most) {
				most = count;
				barSpot = marker;
			}
		}
		bar = barSpot != null ? nearest(indoor.isEmpty() ? open : indoor, barSpot, plaza)
				: nearest(indoor, plaza, plaza);
		// Market stalls: open spots around the plaza, a few blocks apart.
		for (BlockPos spot : open) {
			double distance = Math.sqrt(horizontal(spot, plaza));
			if (distance >= 3 && distance <= 12 && Math.abs(spot.getY() - plaza.getY()) <= 2) {
				boolean crowded = false;
				for (BlockPos other : marketSpots) {
					if (other.distSqr(spot) < 9) {
						crowded = true;
						break;
					}
				}
				if (!crowded && marketSpots.size() < 10) {
					marketSpots.add(spot);
				}
			}
		}
		if (marketSpots.isEmpty()) {
			marketSpots.add(plaza);
		}
	}

	private static double horizontal(BlockPos a, BlockPos b) {
		double dx = a.getX() - b.getX();
		double dz = a.getZ() - b.getZ();
		return dx * dx + dz * dz;
	}

	private static BlockPos nearest(List<BlockPos> spots, BlockPos to, BlockPos fallback) {
		BlockPos best = fallback;
		double bestDistance = Double.MAX_VALUE;
		for (BlockPos spot : spots) {
			double distance = spot.distSqr(to);
			if (distance < bestDistance) {
				bestDistance = distance;
				best = spot;
			}
		}
		return best;
	}

	// ---------- Spots for townsfolk ----------

	/** Nobody could get to this spot: leave it out for a day (it's tried again after that, in case it was a crowd). */
	public void markUnreachable(BlockPos pos) {
		if (unreachable.size() > 512) {
			unreachable.values().removeIf(until -> until < level.getGameTime());
		}
		unreachable.put(pos.immutable(), level.getGameTime() + 24000L);
	}

	public boolean reachable(BlockPos pos) {
		Long until = unreachable.get(pos);
		return until == null || until < level.getGameTime();
	}

	/** A random spot from the list that nobody has found unreachable (any spot if they all are). */
	private BlockPos pick(List<BlockPos> spots, RandomSource random) {
		for (int i = 0; i < 8; i++) {
			BlockPos spot = spots.get(random.nextInt(spots.size()));
			if (reachable(spot)) {
				return spot;
			}
		}
		return spots.get(random.nextInt(spots.size()));
	}

	/** Where a new townsperson lives: a bed nobody has claimed yet, else somewhere under a roof. */
	public BlockPos pickHome(java.util.Set<BlockPos> claimed, RandomSource random) {
		for (BlockPos bed : beds) {
			if (!claimed.contains(bed) && reachable(bed)) {
				return bed;
			}
		}
		if (!indoor.isEmpty()) {
			return pick(indoor, random);
		}
		return open.isEmpty() ? plaza : pick(open, random);
	}

	/** Where a job works during the day. */
	public BlockPos pickWork(TownData.Job job, int index, RandomSource random) {
		if ("water".equals(job.workAt) && !docks.isEmpty()) {
			return pick(docks, random);
		}
		if ("market".equals(job.workAt)) {
			return marketSpots.get(Math.floorMod(index, marketSpots.size()));
		}
		if ("bar".equals(job.workAt)) {
			return bar;
		}
		List<BlockPos> options = new ArrayList<>();
		for (String block : job.workBlocks) {
			options.addAll(workBlocks.getOrDefault(block, List.of()));
		}
		if (!options.isEmpty()) {
			return pick(options, random);
		}
		return open.isEmpty() ? plaza : pick(open, random);
	}

	/** Somewhere to spawn a new townsperson: preferably indoors, out of sight. */
	public BlockPos pickSpawn(RandomSource random) {
		if (!indoor.isEmpty()) {
			return pick(indoor, random);
		}
		if (!open.isEmpty()) {
			return pick(open, random);
		}
		return null;
	}

	public BlockPos randomOpenNear(BlockPos center, int radius, RandomSource random) {
		List<BlockPos> near = new ArrayList<>();
		for (BlockPos spot : open) {
			if (spot.closerThan(center, radius) && reachable(spot)) {
				near.add(spot);
			}
		}
		return near.isEmpty() ? center : near.get(random.nextInt(near.size()));
	}
}
