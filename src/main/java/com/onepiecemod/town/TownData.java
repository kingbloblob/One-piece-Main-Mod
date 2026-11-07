package com.onepiecemod.town;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.google.gson.Gson;
import com.google.gson.annotations.SerializedName;

import net.minecraft.util.RandomSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.trading.ItemCost;
import net.minecraft.world.item.trading.MerchantOffer;

import com.onepiecemod.character.CharacterData;

/**
 * Everything about towns that lives in src/main/resources/onepiece/towns.json:
 * which structures are towns, who lives there (jobs), how they dress (cultures), what they sell,
 * and the festivals each town holds. Edit the JSON to add a town or a festival, no code needed.
 */
public class TownData {
	public static class TownDef {
		public String name = "";
		public String culture = "east_blue";
		public int population = 8;
		public boolean bar;
		public boolean market;
		public String festival;
		/** How likely bar brawls are here (1 = normal, Mock Town = 3). */
		public float brawlChance = 1.0f;
		public Map<String, Integer> jobs = Map.of();
	}

	public static class Culture {
		@SerializedName("default")
		public String defaultSkin = "villager";
		/** Jobs that dress differently here, like Wano's dancers. */
		public Map<String, String> skins = Map.of();
		/** Local goods that this island's merchants sell (a few each day). */
		public List<Trade> goods = List.of();
	}

	public static class Job {
		public String title = "Townsperson";
		public String skin;
		/** Blocks this job works at (a farmer's composter, a cook's smoker). */
		public List<String> workBlocks = List.of();
		/** Or a kind of place: "water" (docks), "market" (the plaza stalls), "bar". */
		public String workAt;
		public String hold;
		public boolean brawler;
		public boolean nightOwl;
		public boolean marketer;
		public boolean child;
		public List<Trade> trades = List.of();
		public List<String> lines = List.of();
		/** What market sellers shout to passers-by. */
		public List<String> calls = List.of();
	}

	public static class Trade {
		public String buy;
		public int buyCount = 1;
		public String sell;
		public int sellCount = 1;
		public int maxUses = 12;
		public int xp = 2;

		/** The trade as a Minecraft offer, or null if one of its items doesn't exist. */
		public MerchantOffer toOffer() {
			ItemStack result = CharacterData.stack(sell, sellCount);
			if (result.isEmpty() || CharacterData.item(buy) == Items.AIR) {
				return null;
			}
			return new MerchantOffer(new ItemCost(CharacterData.item(buy), buyCount), result, maxUses, xp, 0.05f);
		}
	}

	public static class Festival {
		public String name = "Festival";
		/** Held every this many days (0 = only when something triggers it, like a victory banquet). */
		public int every;
		public int offset;
		/** Time of day it runs, in ticks (0 = 6 am, 6000 = noon, 13000 = dusk, 18000 = midnight). */
		public int start = 12000;
		public int end = 20000;
		/** Aqua Laguna: a danger, not a party. Townsfolk hide indoors. */
		public boolean hazard;
		public String announce = "%s is celebrating!";
		public List<String> particles = List.of();
		public List<Integer> fireworks = List.of();
		public String music = "";
		public List<Trade> goods = List.of();
		/** Given once per festival to each player who joins in, "item*count". */
		public List<String> gifts = List.of();
		public String effect = "";
	}

	private static class FileData {
		Map<String, TownDef> towns = new LinkedHashMap<>();
		Map<String, Culture> cultures = new LinkedHashMap<>();
		Map<String, Job> jobs = new LinkedHashMap<>();
		List<Trade> imports = new ArrayList<>();
		List<String> rumors = new ArrayList<>();
		Map<String, Festival> festivals = new LinkedHashMap<>();
	}

	private static FileData data;

	private static FileData data() {
		if (data == null) {
			try (InputStream in = TownData.class.getResourceAsStream("/onepiece/towns.json")) {
				data = new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), FileData.class);
			} catch (Exception e) {
				throw new RuntimeException("Could not read onepiece/towns.json", e);
			}
		}
		return data;
	}

	public static Map<String, TownDef> towns() {
		return data().towns;
	}

	public static TownDef town(String structureId) {
		return data().towns.get(structureId);
	}

	public static Job job(String id) {
		Job job = data().jobs.get(id);
		return job != null ? job : data().jobs.getOrDefault("elder", new Job());
	}

	public static Map<String, Job> jobs() {
		return data().jobs;
	}

	public static Culture culture(String id) {
		Culture culture = data().cultures.get(id);
		return culture != null ? culture : new Culture();
	}

	public static Festival festival(String id) {
		return id == null ? null : data().festivals.get(id);
	}

	public static Map<String, Festival> festivals() {
		return data().festivals;
	}

	public static List<Trade> imports() {
		return data().imports;
	}

	public static List<String> rumors() {
		return data().rumors;
	}

	/** The skin group a job wears in a culture: the culture's own look for that job, else the job's look, else the culture's. */
	public static String skinGroup(String cultureId, String jobId) {
		Culture culture = culture(cultureId);
		if (culture.skins != null && culture.skins.containsKey(jobId)) {
			return culture.skins.get(jobId);
		}
		if (!"east_blue".equals(cultureId)) {
			return culture.defaultSkin; // Islands with their own fashion dress everybody in it.
		}
		Job job = job(jobId);
		return job.skin != null ? job.skin : culture.defaultSkin;
	}

	/** Picks a job for a new townsperson, weighted by the town's jobs list. */
	public static String pickJob(TownDef town, Map<String, Integer> alreadyThere, RandomSource random) {
		// First fill every job up to its count, so a town always has its bartender and its cook.
		for (Map.Entry<String, Integer> entry : town.jobs.entrySet()) {
			if (alreadyThere.getOrDefault(entry.getKey(), 0) < entry.getValue()) {
				return entry.getKey();
			}
		}
		int total = 0;
		for (int weight : town.jobs.values()) {
			total += weight;
		}
		if (total <= 0) {
			return "elder";
		}
		int roll = random.nextInt(total);
		for (Map.Entry<String, Integer> entry : town.jobs.entrySet()) {
			roll -= entry.getValue();
			if (roll < 0) {
				return entry.getKey();
			}
		}
		return "elder";
	}

	/** "minecraft:cake*2" -> a stack of 2 cakes (empty if the item doesn't exist). */
	public static ItemStack gift(String spec) {
		int star = spec.indexOf('*');
		String id = star < 0 ? spec : spec.substring(0, star);
		int count = 1;
		if (star >= 0) {
			try {
				count = Integer.parseInt(spec.substring(star + 1));
			} catch (NumberFormatException ignored) {
			}
		}
		return CharacterData.stack(id, count);
	}
}
