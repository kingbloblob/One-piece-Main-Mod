package com.onepiecemod.vegapunk;

import java.util.HashMap;
import java.util.Map;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

/**
 * A player's cyborg body: the tier (0-3) of each upgrade, and how much Cola fuel is in the tank (100 = one Cola).
 */
public record CyborgData(Map<String, Integer> tiers, int fuel) {
	public static final CyborgData EMPTY = new CyborgData(Map.of(), 0);

	public static final Codec<CyborgData> CODEC = RecordCodecBuilder.create(instance -> instance.group(
			Codec.unboundedMap(Codec.STRING, Codec.INT).optionalFieldOf("tiers", Map.of()).forGetter(CyborgData::tiers),
			Codec.INT.optionalFieldOf("fuel", 0).forGetter(CyborgData::fuel)
	).apply(instance, CyborgData::new));

	public int tier(CyborgUpgrade upgrade) {
		return tiers.getOrDefault(upgrade.id, 0);
	}

	public boolean any() {
		return tiers.values().stream().anyMatch(t -> t > 0);
	}

	public CyborgData withTier(CyborgUpgrade upgrade, int tier) {
		Map<String, Integer> copy = new HashMap<>(tiers);
		if (tier <= 0) {
			copy.remove(upgrade.id);
		} else {
			copy.put(upgrade.id, Math.min(CyborgUpgrade.MAX_TIER, tier));
		}
		return new CyborgData(Map.copyOf(copy), Math.min(fuel, tankFor(copy)));
	}

	public CyborgData withFuel(int amount) {
		return new CyborgData(tiers, Math.max(0, Math.min(amount, tank())));
	}

	/** Fuel the tank holds: 3 Colas per Cola Engine tier, nothing without an engine. */
	public int tank() {
		return tankFor(tiers);
	}

	private static int tankFor(Map<String, Integer> tiers) {
		return tiers.getOrDefault(CyborgUpgrade.COLA_ENGINE.id, 0) * Cyborg.COLA * 3;
	}
}
