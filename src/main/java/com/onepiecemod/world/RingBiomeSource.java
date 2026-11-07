package com.onepiecemod.world;

import java.util.List;
import java.util.stream.Stream;

import com.mojang.datafixers.util.Pair;
import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.util.Mth;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.biome.BiomeResolver;
import net.minecraft.world.level.biome.BiomeSource;
import net.minecraft.world.level.biome.Climate;
import net.minecraft.world.level.biome.MultiNoiseBiomeSource;

/**
 * The Grand Line world's biome map: rings around spawn, like sailing from the East Blue into the New World.
 * Each ring has its own list of biomes (picked by the normal climate noise, like vanilla's multi_noise), so the
 * easy islands are near spawn and the deadly ones far away. Ring edges wobble a little so they are not perfect circles.
 * Used by data/onepiece/worldgen/world_preset/grand_line.json ("type": "onepiece:rings").
 *
 * Soft edges (2026-10-24, ryan: "blend with other biomes so it's not so instant"):
 * - Between two biomes the climate is read a little to the side of where you stand. The offset is a slow wave plus a
 *   fine mottle, so the border wanders and the two biomes finger into each other over about "edge" blocks instead of
 *   changing on a straight line. Only temperature, humidity and weirdness are read off to the side; continentalness,
 *   erosion and depth stay exact, so beaches and seas still sit where the land really ends.
 * - Between two rings there is a band "blend" blocks wide where patches of the next ring's biomes appear more and more
 *   often, so the Paradise islands fade into the New World instead of switching at a line.
 */
public class RingBiomeSource extends BiomeSource {
	/** One ring: everything closer than maxDistance blocks (the last ring goes on forever). */
	public record Ring(int maxDistance, Climate.ParameterList<Holder<Biome>> biomes) {
		public static final Codec<Ring> CODEC = RecordCodecBuilder.create(instance -> instance.group(
				Codec.INT.fieldOf("max_distance").forGetter(Ring::maxDistance),
				MultiNoiseBiomeSource.DIRECT_CODEC.forGetter(Ring::biomes) // "biomes": the same list multi_noise uses
		).apply(instance, Ring::new));
	}

	public static final MapCodec<RingBiomeSource> CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
			Ring.CODEC.listOf().fieldOf("rings").forGetter(source -> source.rings),
			Codec.INT.optionalFieldOf("wobble", 250).forGetter(source -> source.wobble),
			Codec.INT.optionalFieldOf("blend", 400).forGetter(source -> source.blend),
			Codec.INT.optionalFieldOf("edge", 32).forGetter(source -> source.edge)
	).apply(instance, RingBiomeSource::new));

	private final List<Ring> rings;
	private final int wobble;
	/** How many blocks wide the mixed band between two rings is (0 = hard ring edges, like before). */
	private final int blend;
	/** About how many blocks two neighbouring biomes finger into each other (0 = hard biome edges). */
	private final int edge;
	/** A vanilla multi_noise source per ring, only used for the F3 debug lines. */
	private final List<MultiNoiseBiomeSource> sources;

	public RingBiomeSource(List<Ring> rings, int wobble) {
		this(rings, wobble, 400, 32);
	}

	public RingBiomeSource(List<Ring> rings, int wobble, int blend, int edge) {
		this.rings = rings;
		this.wobble = wobble;
		this.blend = blend;
		this.edge = edge;
		this.sources = rings.stream().map(ring -> MultiNoiseBiomeSource.createFromList(ring.biomes())).toList();
	}

	@Override
	protected MapCodec<? extends BiomeSource> codec() {
		return CODEC;
	}

	@Override
	protected Stream<Holder<Biome>> collectPossibleBiomes() {
		return rings.stream().flatMap(ring -> ring.biomes().values().stream().map(Pair::getSecond));
	}

	// x, y and z are in quarter-chunk steps (4 blocks), like everywhere biomes are looked up.
	@Override
	public BiomeResolver createResolver(Climate.Sampler sampler) {
		return (x, y, z) -> biomeAt(sampler, x, y, z, null);
	}

	/**
	 * For a whole chunk. The climate read off to the side is the same for every y of a column (temperature, humidity
	 * and weirdness are flat noises), so it is remembered per column while the chunk is filled.
	 */
	@Override
	public BiomeResolver createResolverForChunk(Climate.Sampler sampler, int a, int b, int c, int d, int e, int f) {
		ColumnCache cache = new ColumnCache();
		return (x, y, z) -> biomeAt(sampler, x, y, z, cache);
	}

	/** Remembers the sideways climate of the last few columns (a chunk is 4 x 4 columns of quarter-chunk cells). */
	private static final class ColumnCache {
		private final long[] keys = new long[16];
		private final long[] temperature = new long[16];
		private final long[] humidity = new long[16];
		private final long[] weirdness = new long[16];
		private final boolean[] filled = new boolean[16];
	}

	private Holder<Biome> biomeAt(Climate.Sampler sampler, int x, int y, int z, ColumnCache cache) {
		Climate.TargetPoint here = sampler.sample(x, y, z);
		if (edge <= 0) {
			return rings.get(ringIndex(x * 4, z * 4, true)).biomes().findValue(here);
		}
		double blockX = x * 4 + 2;
		double blockZ = z * 4 + 2;
		double offsetX = sideways(blockX, blockZ, 11);
		double offsetZ = sideways(blockX, blockZ, 29);
		long temperature;
		long humidity;
		long weirdness;
		int slot = (x & 3) | ((z & 3) << 2);
		long key = ((long) x << 32) ^ (z & 0xffffffffL);
		if (cache != null && cache.filled[slot] && cache.keys[slot] == key) {
			temperature = cache.temperature[slot];
			humidity = cache.humidity[slot];
			weirdness = cache.weirdness[slot];
		} else {
			// The climate a few blocks to the side; y does not matter for these three.
			Climate.TargetPoint there = sampler.sample(x + (int) Math.round(offsetX / 4), y, z + (int) Math.round(offsetZ / 4));
			temperature = there.temperature();
			humidity = there.humidity();
			weirdness = there.weirdness();
			if (cache != null) {
				cache.filled[slot] = true;
				cache.keys[slot] = key;
				cache.temperature[slot] = temperature;
				cache.humidity[slot] = humidity;
				cache.weirdness[slot] = weirdness;
			}
		}
		Climate.TargetPoint mixed = new Climate.TargetPoint(temperature, humidity, here.continentalness(), here.erosion(), here.depth(), weirdness);
		int ring = ringIndex(blockX + offsetX, blockZ + offsetZ, true);
		return rings.get(ring).biomes().findValue(mixed);
	}

	/**
	 * How far (in blocks, plus or minus) the climate is read off to the side at this spot: a slow wave about 180 blocks
	 * long that bends the border, plus a fine mottle about 20 blocks across that makes the two sides finger into each
	 * other. "salt" makes the x and z offsets different patterns.
	 */
	private double sideways(double blockX, double blockZ, int salt) {
		double wave = valueNoise(blockX / 180.0, blockZ / 180.0, salt);
		double mottle = valueNoise(blockX / 20.0, blockZ / 20.0, salt + 101);
		return edge * (1.2 * wave + 0.7 * mottle);
	}

	@Override
	public void addDebugInfo(List<String> lines, BlockPos pos, Climate.Sampler sampler) {
		int ring = ringIndex(pos.getX(), pos.getZ(), false);
		lines.add("Grand Line ring: " + (ring + 1) + " of " + rings.size() + " (edge blend " + blend + ", biome edge " + edge + ")");
		sources.get(ring).addDebugInfo(lines, pos, sampler);
	}

	/** Which ring (0 = nearest spawn) a block position is in, with hard edges (for the debug screen and other mods). */
	public int ringIndex(double blockX, double blockZ) {
		return ringIndex(blockX, blockZ, false);
	}

	/**
	 * Which ring a block position is in. With soft edges, inside the "blend" band around a ring's edge the answer
	 * is the next ring in patches that get bigger and more common the further out you are.
	 */
	private int ringIndex(double blockX, double blockZ, boolean soft) {
		double distance = Math.sqrt(blockX * blockX + blockZ * blockZ) + wobble(blockX, blockZ);
		for (int i = 0; i < rings.size() - 1; i++) {
			double limit = rings.get(i).maxDistance();
			if (!soft || blend <= 0) {
				if (distance < limit) {
					return i;
				}
				continue;
			}
			if (distance < limit - blend / 2.0) {
				return i;
			}
			if (distance < limit + blend / 2.0) {
				// 0 at the inner side of the band, 1 at the outer side; patches of the next ring where the noise is below it
				double t = Mth.clamp((distance - (limit - blend / 2.0)) / blend, 0.0, 1.0);
				double patches = 0.5 + 0.5 * valueNoise(blockX / 90.0, blockZ / 90.0, 7 + i);
				if (patches >= t * t * (3 - 2 * t)) {
					return i;
				}
			}
		}
		return rings.size() - 1;
	}

	/** A slow, bumpy offset (plus or minus wobble blocks) so ring edges look like coastlines, not circles. */
	private double wobble(double x, double z) {
		double angle = Math.atan2(z, x);
		return wobble * (0.5 * Math.sin(angle * 5.0 + x / 900.0) + 0.3 * Math.sin(x / 377.0) * Math.cos(z / 433.0) + 0.2 * Math.sin(angle * 11.0));
	}

	/** Smooth random bumps between -1 and 1, about one bump per unit of x and z. The same for every world. */
	private static double valueNoise(double x, double z, int salt) {
		int x0 = Mth.floor(x);
		int z0 = Mth.floor(z);
		double fx = x - x0;
		double fz = z - z0;
		fx = fx * fx * (3 - 2 * fx);
		fz = fz * fz * (3 - 2 * fz);
		double a = Mth.lerp(fx, hash(x0, z0, salt), hash(x0 + 1, z0, salt));
		double b = Mth.lerp(fx, hash(x0, z0 + 1, salt), hash(x0 + 1, z0 + 1, salt));
		return Mth.lerp(fz, a, b) * 2.0 - 1.0;
	}

	private static double hash(int x, int z, int salt) {
		long h = x * 0x9E3779B97F4A7C15L ^ (z + 0x632BE59BD9B4E019L) * 0xC2B2AE3D27D4EB4FL ^ salt * 0x165667B19E3779F9L;
		h ^= h >>> 29;
		h *= 0xBF58476D1CE4E5B9L;
		h ^= h >>> 32;
		return (h & 0xFFFFFF) / (double) 0x1000000;
	}
}
