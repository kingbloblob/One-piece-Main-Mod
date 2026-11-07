package com.onepiecemod.collection;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

/**
 * One player's Collector's Log, saved on the player (kept after death).
 *
 * lists:    "ships" ships spotted, "sailed" ships sailed aboard, "swords" swords held,
 *           "visited" places set foot on, "islands" places finished, "claimed" rewards already paid
 *           (like "fish:6" or "region:east_blue").
 * counters: "explore:<place>" seconds spent there, "food" dishes tasted the last time we looked.
 */
public record CollectionProgress(Map<String, List<String>> lists, Map<String, Integer> counters) {
	public static final CollectionProgress EMPTY = new CollectionProgress(Map.of(), Map.of());

	public static final Codec<CollectionProgress> CODEC = RecordCodecBuilder.create(instance -> instance.group(
			Codec.unboundedMap(Codec.STRING, Codec.STRING.listOf()).optionalFieldOf("lists", Map.of()).forGetter(CollectionProgress::lists),
			Codec.unboundedMap(Codec.STRING, Codec.INT).optionalFieldOf("counters", Map.of()).forGetter(CollectionProgress::counters)
	).apply(instance, CollectionProgress::new));

	public List<String> list(String key) {
		return lists.getOrDefault(key, List.of());
	}

	public boolean has(String key, String value) {
		return list(key).contains(value);
	}

	public int counter(String key) {
		return counters.getOrDefault(key, 0);
	}

	public CollectionProgress with(String key, String value) {
		if (has(key, value)) {
			return this;
		}
		Map<String, List<String>> newLists = new HashMap<>(lists);
		List<String> values = new ArrayList<>(list(key));
		values.add(value);
		newLists.put(key, values);
		return new CollectionProgress(newLists, counters);
	}

	public CollectionProgress withCounter(String key, int value) {
		Map<String, Integer> newCounters = new HashMap<>(counters);
		newCounters.put(key, value);
		return new CollectionProgress(lists, newCounters);
	}
}
