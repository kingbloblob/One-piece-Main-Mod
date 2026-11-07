package com.onepiecemod.npc;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.google.gson.Gson;

import net.minecraft.util.RandomSource;

/**
 * One kind of pirate or Marine NPC: who they are (crew, ranks, name pattern), how they look (skin groups)
 * and how they fight (loadouts). Read from src/main/resources/onepiece/npc_kits.json.
 * Edit that file to change them; tools/npcs/gen_kits.py writes it.
 *
 * Every NPC that spawns rolls its own skin, crew, rank, name and loadout from its kit, so a squad never looks the same twice.
 */
public class NpcKit {
	public String id;
	public String faction;        // "marine" (entity onepiece:marine) or "pirate" (entity onepiece:sea_pirate)
	public List<String> crews;    // "*" = a random made-up pirate crew, "" = no crew
	public String name;           // pattern with {rank} {name} {surname} {epithet} {crew} {num}
	public List<String> ranks;    // later ranks are a bit tougher
	public List<String> skins;    // skin groups from NpcSkins
	public List<Loadout> loadouts;
	public float health;
	public float damage;
	public float armor;
	public float speed;           // 0 = normal (0.3)
	public float knockbackResistance;
	public float scale;           // 0 = normal size
	public int berries;           // Berries dropped when beaten
	public long bounty;           // bounty a pirate player earns for beating this Marine (Marines only)

	/** A combat style and the weapons that go with it ("" = bare fists). */
	public static class Loadout {
		public String style;
		public List<String> weapons;
		public String offhand;
		public int weight = 1;
	}

	/** A group of NPCs that walks around a biome together. */
	public static class Patrol {
		public List<String> kits;
		public String leader;
		public int weight = 1;
		public int min = 2;
		public int max = 4;
	}

	private static class FileData {
		List<NpcKit> kits;
		Map<String, List<Patrol>> patrols;
	}

	private static final Map<String, NpcKit> ALL = new LinkedHashMap<>();
	private static Map<String, List<Patrol>> patrols = Map.of();

	private static void load() {
		if (!ALL.isEmpty()) {
			return;
		}
		try (InputStream in = NpcKit.class.getResourceAsStream("/onepiece/npc_kits.json")) {
			FileData data = new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), FileData.class);
			for (NpcKit kit : data.kits) {
				ALL.put(kit.id, kit);
			}
			patrols = data.patrols;
		} catch (Exception e) {
			throw new RuntimeException("Could not read onepiece/npc_kits.json", e);
		}
	}

	public static NpcKit get(String id) {
		load();
		return id == null ? null : ALL.get(id);
	}

	public static Map<String, NpcKit> all() {
		load();
		return ALL;
	}

	/** The patrol groups for a biome id, or the "default" ones. An empty list means nobody patrols there. */
	public static List<Patrol> patrolsFor(String biomeId) {
		load();
		List<Patrol> list = patrols.get(biomeId);
		return list != null ? list : patrols.getOrDefault("default", List.of());
	}

	/** True if npc_kits.json names this biome in "patrols" (so it gets patrols even outside the Grand Line islands). */
	public static boolean listsBiome(String biomeId) {
		load();
		return patrols.containsKey(biomeId);
	}

	public boolean isMarine() {
		return "marine".equals(faction);
	}

	public Loadout pickLoadout(RandomSource random) {
		int total = 0;
		for (Loadout loadout : loadouts) {
			total += Math.max(1, loadout.weight);
		}
		int roll = random.nextInt(Math.max(1, total));
		for (Loadout loadout : loadouts) {
			roll -= Math.max(1, loadout.weight);
			if (roll < 0) {
				return loadout;
			}
		}
		return loadouts.get(0);
	}

	/** A random skin texture name, like "marine_grunt_7". */
	public String pickSkin(RandomSource random) {
		List<String> groups = new ArrayList<>();
		for (String group : skins) {
			if (NpcSkins.COUNT.containsKey(group)) {
				groups.add(group);
			}
		}
		if (groups.isEmpty()) {
			return isMarine() ? "marine_grunt_0" : "deckhand_0";
		}
		String group = groups.get(random.nextInt(groups.size()));
		return group + "_" + random.nextInt(NpcSkins.COUNT.get(group));
	}

	public static <T> T pick(List<T> list, RandomSource random) {
		return list.get(random.nextInt(list.size()));
	}
}
