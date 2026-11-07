package com.onepiecemod.dungeon;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.google.gson.Gson;

import com.onepiecemod.OnePieceMod;

/**
 * One dungeon mini-boss, read from src/main/resources/onepiece/dungeon_bosses.json. The id is the dungeon's
 * structure id (tools/dungeons/<id>.py); the structure places the boss with the tag onepiece_miniboss_<id>.
 */
public class DungeonBossDef {
	public String id;
	public String kit;
	public String name;
	public String title;
	public String color = "red";
	public float health;
	public float damage;
	public float armor;
	public float scale;
	public long bounty;
	public List<String> moves = List.of("slam");
	public Minions minions;
	public Legendary legendary;
	public List<Drop> drops = List.of();
	public List<String> lines = List.of();

	public static class Minions {
		public String kit;
		public int count;
	}

	public static class Legendary {
		public String item;
		public float chance;
		public int pity;
	}

	public static class Drop {
		public String item;
		public int min = 1;
		public int max = 1;
		public float chance = 1.0f;
	}

	private static class FileData {
		List<DungeonBossDef> bosses;
	}

	private static final Map<String, DungeonBossDef> ALL = new LinkedHashMap<>();

	public static Map<String, DungeonBossDef> all() {
		if (ALL.isEmpty()) {
			try (InputStream in = DungeonBossDef.class.getResourceAsStream("/onepiece/dungeon_bosses.json")) {
				FileData data = new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), FileData.class);
				for (DungeonBossDef def : data.bosses) {
					ALL.put(def.id, def);
				}
			} catch (Exception e) {
				OnePieceMod.LOGGER.error("Could not read onepiece/dungeon_bosses.json", e);
			}
		}
		return ALL;
	}

	public static DungeonBossDef get(String id) {
		return id == null ? null : all().get(id);
	}

	/** A line the boss shouts: 0 = when the fight starts, 1 = calling minions, 2 = enraged. */
	public String line(int i) {
		return i < lines.size() ? lines.get(i) : "";
	}
}
