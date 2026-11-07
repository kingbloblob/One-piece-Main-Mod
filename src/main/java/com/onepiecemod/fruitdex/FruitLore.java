package com.onepiecemod.fruitdex;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import com.onepiecemod.OnePieceMod;

/**
 * Extra encyclopedia text for each fruit: its English name, its famous user in the series,
 * and a line of lore. Read from src/main/resources/onepiece/fruitdex.json.
 */
public class FruitLore {
	public record Entry(String english, String user, String lore) {
	}

	private static final Entry UNKNOWN = new Entry("", "Unknown", "");
	private static Map<String, Entry> entries;

	/** The lore for a fruit id like "mera_mera_no_mi". Never null. */
	public static Entry get(String fruitId) {
		if (entries == null) {
			entries = load();
		}
		return entries.getOrDefault(fruitId, UNKNOWN);
	}

	private static Map<String, Entry> load() {
		Map<String, Entry> map = new HashMap<>();
		try (InputStream in = FruitLore.class.getResourceAsStream("/onepiece/fruitdex.json")) {
			JsonObject root = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
			for (Map.Entry<String, JsonElement> e : root.entrySet()) {
				JsonObject o = e.getValue().getAsJsonObject();
				map.put(e.getKey(), new Entry(o.get("english").getAsString(), o.get("user").getAsString(), o.get("lore").getAsString()));
			}
		} catch (Exception e) {
			OnePieceMod.LOGGER.error("Could not read onepiece/fruitdex.json", e);
		}
		return map;
	}
}
