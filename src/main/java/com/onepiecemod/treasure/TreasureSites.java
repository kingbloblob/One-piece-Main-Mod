package com.onepiecemod.treasure;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.QuartPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BiomeTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.levelgen.Heightmap;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.sea.CalmBelt;

/**
 * Every treasure that a map points to, kept on the Overworld.
 * A site starts as WAITING (only a spot on a map). When a player comes within BUILD_RANGE and the chunks are
 * loaded, TreasureBuilder digs in the chest (or sinks the wreck) and the site becomes BUILT, remembering where
 * the treasure chest is. Once that chest has been opened the site is found and forgotten.
 */
public final class TreasureSites {
	public static final int WAITING = 0;
	public static final int BUILT = 1;
	/** At most this many treasures per world; the oldest is dropped first. */
	private static final int MAX_SITES = 96;

	/** kind = TreasureKind id. x, y, z = the X on the map while waiting, the treasure chest once built. */
	public record Site(String kind, int x, int y, int z, int state, String owner) {
		public static final Codec<Site> CODEC = RecordCodecBuilder.create(i -> i.group(
				Codec.STRING.fieldOf("kind").forGetter(Site::kind),
				Codec.INT.fieldOf("x").forGetter(Site::x),
				Codec.INT.fieldOf("y").forGetter(Site::y),
				Codec.INT.fieldOf("z").forGetter(Site::z),
				Codec.INT.fieldOf("state").forGetter(Site::state),
				Codec.STRING.optionalFieldOf("owner", "").forGetter(Site::owner)
		).apply(i, Site::new));

		public BlockPos pos() {
			return new BlockPos(x, y, z);
		}

		public Site built(BlockPos chest) {
			return new Site(kind, chest.getX(), chest.getY(), chest.getZ(), BUILT, owner);
		}
	}

	public static final AttachmentType<List<Site>> SITES = AttachmentRegistry.create(
			OnePieceMod.id("treasure_sites"),
			builder -> builder.persistent(Site.CODEC.listOf())
	);

	private TreasureSites() {
	}

	public static List<Site> all(ServerLevel level) {
		return level.getAttachedOrElse(SITES, List.of());
	}

	public static void add(ServerLevel level, Site site) {
		List<Site> sites = new ArrayList<>(all(level));
		sites.add(site);
		while (sites.size() > MAX_SITES) {
			sites.remove(0);
		}
		level.setAttached(SITES, sites);
	}

	public static void replace(ServerLevel level, Site old, Site now) {
		List<Site> sites = new ArrayList<>(all(level));
		int i = sites.indexOf(old);
		if (i < 0) {
			return;
		}
		if (now == null) {
			sites.remove(i);
		} else {
			sites.set(i, now);
		}
		level.setAttached(SITES, sites);
	}

	// ---------- Picking a spot for a new map ----------

	/**
	 * A random spot for this kind of treasure, using only the world generator's terrain shape (cheap: no chunks are
	 * made and no structures are searched). Land kinds want dry ground on an island, wrecks want sea 10+ blocks deep.
	 */
	public static Optional<BlockPos> pickSpot(ServerLevel level, BlockPos from, TreasureKind kind) {
		RandomSource random = level.getRandom();
		int sea = level.getSeaLevel();
		for (int attempt = 0; attempt < 40; attempt++) {
			double angle = random.nextDouble() * Math.PI * 2;
			int distance = kind.minDistance + random.nextInt(kind.maxDistance - kind.minDistance + 1);
			int x = from.getX() + (int) Math.round(Math.cos(angle) * distance);
			int z = from.getZ() + (int) Math.round(Math.sin(angle) * distance);
			int floor = floorHeight(level, x, z);
			if (kind == TreasureKind.CASTAWAY) {
				// Shallow open sea, where a sandbar can break the surface.
				if (floor <= sea - 3 && floor >= sea - 16 && CalmBelt.isOcean(biomeAt(level, x, floor, z))) {
					return Optional.of(new BlockPos(x, floor, z));
				}
			} else if (kind.land) {
				// Dry island ground, not a mountain top, not a beach biome over shallow water.
				if (floor > sea + 1 && floor < sea + 45 && isLand(biomeAt(level, x, floor, z))) {
					return Optional.of(new BlockPos(x, floor, z));
				}
			} else if (floor < sea - 10 && floor > sea - 45 && CalmBelt.isOcean(biomeAt(level, x, floor, z))) {
				return Optional.of(new BlockPos(x, floor, z));
			}
		}
		return Optional.empty();
	}

	private static int floorHeight(ServerLevel level, int x, int z) {
		return level.getChunkSource().getGenerator().getBaseHeight(x, z, Heightmap.Types.OCEAN_FLOOR_WG, level,
				level.getChunkSource().randomState());
	}

	private static Holder<Biome> biomeAt(ServerLevel level, int x, int y, int z) {
		return level.getChunkSource().getGenerator().getBiomeSource()
				.createUncachedResolver(level.getChunkSource().randomState())
				.getNoiseBiome(QuartPos.fromBlock(x), QuartPos.fromBlock(y), QuartPos.fromBlock(z));
	}

	private static boolean isLand(Holder<Biome> biome) {
		return !CalmBelt.isOcean(biome) && !biome.is(BiomeTags.IS_RIVER) && !biome.is(BiomeTags.IS_BEACH);
	}

	// ---------- Building and finding (called a few times a second) ----------

	/** How close a player must be before the treasure is put into the world, in blocks. */
	private static final int BUILD_RANGE = 72;
	/** How close a player must be to get the "found it" message. */
	private static final int FOUND_RANGE = 12;

	public static void tick(ServerLevel level) {
		List<Site> sites = all(level);
		if (sites.isEmpty() || level.players().isEmpty()) {
			return;
		}
		for (Site site : List.copyOf(sites)) {
			ServerPlayer near = nearestPlayer(level, site, site.state() == WAITING ? BUILD_RANGE : FOUND_RANGE);
			if (near == null) {
				continue;
			}
			if (site.state() == WAITING) {
				BlockPos chest = TreasureBuilder.build(level, site, near);
				if (chest != null) {
					replace(level, site, site.built(chest));
				}
			} else if (TreasureBuilder.isLooted(level, site.pos())) {
				replace(level, site, null);
				TreasureFeature.found(level, near, TreasureKind.byId(site.kind()), site.pos());
			}
		}
	}

	private static ServerPlayer nearestPlayer(ServerLevel level, Site site, int range) {
		ServerPlayer best = null;
		double bestDistance = (double) range * range;
		for (ServerPlayer player : level.players()) {
			if (player.isSpectator()) {
				continue;
			}
			double dx = player.getX() - (site.x() + 0.5);
			double dz = player.getZ() - (site.z() + 0.5);
			double d = dx * dx + dz * dz;
			if (d < bestDistance) {
				bestDistance = d;
				best = player;
			}
		}
		return best;
	}
}
