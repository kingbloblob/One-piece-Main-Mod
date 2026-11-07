package com.onepiecemod.world;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.world.level.levelgen.structure.placement.RandomSpreadStructurePlacement;
import net.minecraft.world.level.levelgen.structure.placement.RandomSpreadType;

/**
 * Like vanilla "random_spread", but only between min_distance and max_distance blocks from spawn (0, 0).
 * Easy places and early bosses stay near spawn, hard and legendary ones only appear far out (works in every
 * world type, and /locate and Sea Charts respect it). Used by data/onepiece/worldgen/structure_set/*.json:
 * {"type": "onepiece:ring_spread", "spacing": 24, "separation": 8, "salt": 1, "min_distance": 0, "max_distance": 1500}
 */
public class RingSpreadPlacement extends RandomSpreadStructurePlacement {
	public static final MapCodec<RingSpreadPlacement> CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
			Codec.intRange(1, 4096).fieldOf("spacing").forGetter(RandomSpreadStructurePlacement::spacing),
			Codec.intRange(0, 4096).fieldOf("separation").forGetter(RandomSpreadStructurePlacement::separation),
			RandomSpreadType.CODEC.optionalFieldOf("spread_type", RandomSpreadType.LINEAR).forGetter(RandomSpreadStructurePlacement::spreadType),
			Codec.INT.fieldOf("salt").forGetter(placement -> placement.saltValue),
			Codec.INT.optionalFieldOf("min_distance", 0).forGetter(placement -> placement.minDistance),
			Codec.INT.optionalFieldOf("max_distance", Integer.MAX_VALUE).forGetter(placement -> placement.maxDistance)
	).apply(instance, RingSpreadPlacement::new));

	private final int saltValue;
	private final int minDistance;
	private final int maxDistance;

	public RingSpreadPlacement(int spacing, int separation, RandomSpreadType spreadType, int salt, int minDistance, int maxDistance) {
		super(spacing, separation, spreadType, salt);
		this.saltValue = salt;
		this.minDistance = minDistance;
		this.maxDistance = maxDistance;
	}

	/** Called both when the world generates and when /locate searches, so both skip chunks outside the ring. */
	@Override
	public boolean applyAdditionalChunkRestrictions(int chunkX, int chunkZ, long seed) {
		double x = chunkX * 16.0 + 8.0;
		double z = chunkZ * 16.0 + 8.0;
		double distance = Math.sqrt(x * x + z * z);
		return distance >= minDistance && distance < maxDistance && super.applyAdditionalChunkRestrictions(chunkX, chunkZ, seed);
	}

	// Vanilla's random_spread says its codec() is a MapCodec<RandomSpreadStructurePlacement>, so ours has to be
	// handed back as one. It is still our CODEC, which is what the structure placement registry looks up.
	@SuppressWarnings("unchecked")
	@Override
	public MapCodec<RandomSpreadStructurePlacement> codec() {
		return (MapCodec<RandomSpreadStructurePlacement>) (MapCodec<?>) CODEC;
	}
}
