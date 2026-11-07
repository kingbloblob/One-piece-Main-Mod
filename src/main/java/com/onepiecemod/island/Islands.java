package com.onepiecemod.island;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Map;

import com.google.gson.Gson;

/**
 * Every named island: its title, subtitle and climate, by biome id.
 * Read once from src/main/resources/onepiece/islands.json, so new islands only need a line there.
 */
public class Islands {
	public enum Climate { WINTER, SUMMER, MILD }

	/** One island, as written in islands.json. */
	public static class Island {
		public String name;
		public String subtitle;
		public String climate = "mild";
		/** True if the climate works indoors and underground too (Impel Down has no sky). */
		public boolean everywhere;

		public Climate climate() {
			return switch (climate) {
				case "winter" -> Climate.WINTER;
				case "summer" -> Climate.SUMMER;
				default -> Climate.MILD;
			};
		}
	}

	private static class File {
		Map<String, Island> islands = Map.of();
	}

	private static Map<String, Island> islands;

	/** The island for a biome id like "onepiece:drum_island", or null if it isn't a named island. */
	public static Island byBiome(String biomeId) {
		if (islands == null) {
			try (InputStream in = Islands.class.getResourceAsStream("/onepiece/islands.json")) {
				islands = new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), File.class).islands;
			} catch (Exception e) {
				throw new RuntimeException("Could not read onepiece/islands.json", e);
			}
		}
		return islands.get(biomeId);
	}
}
