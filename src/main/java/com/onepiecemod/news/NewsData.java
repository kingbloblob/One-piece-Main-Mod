package com.onepiecemod.news;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;

import com.google.gson.Gson;

import net.minecraft.util.RandomSource;

import com.onepiecemod.OnePieceMod;

/**
 * The text in src/main/resources/onepiece/news.json: world stories for the paper, canon pirates
 * for the wall posters, and what bosses say over the Den Den Mushi.
 */
public class NewsData {
	public Map<String, List<String>> world = Map.of();
	public List<String> anytime = List.of();
	public List<String> islands = List.of("Dawn Island");
	public List<String> pirates = List.of("Krieg");
	public List<String> marines = List.of("Garp");
	public List<String> seas = List.of("Grand Line");
	public List<Canon> canon = List.of();
	public Map<String, List<String>> taunts = Map.of();

	/** A famous pirate who can appear on a wall poster. */
	public static class Canon {
		public String name;
		public long bounty;
		/** The first saga (0 = Romance Dawn ... 5 = Final Saga) this poster shows up in. */
		public int saga;
	}

	private static NewsData data;

	public static NewsData get() {
		if (data == null) {
			try (InputStream in = NewsData.class.getResourceAsStream("/onepiece/news.json")) {
				data = new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), NewsData.class);
			} catch (Exception e) {
				OnePieceMod.LOGGER.error("News problem: could not read onepiece/news.json", e);
				data = new NewsData();
			}
		}
		return data;
	}

	/** An "anytime" story with the {island}, {pirate}, {marine} and {sea} blanks filled in. */
	public String randomAnytime(RandomSource random) {
		if (anytime.isEmpty()) {
			return "CALM SEAS: Nothing much happened today. The News Coo took the morning off.";
		}
		return anytime.get(random.nextInt(anytime.size()))
				.replace("{island}", pick(islands, random))
				.replace("{pirate}", pick(pirates, random))
				.replace("{marine}", pick(marines, random))
				.replace("{sea}", pick(seas, random).toUpperCase());
	}

	/** What this boss says over the snail phone. Bosses without their own lines use their tier's. */
	public String taunt(String bossId, int tier, RandomSource random) {
		List<String> lines = taunts.get(bossId);
		if (lines == null || lines.isEmpty()) {
			lines = taunts.getOrDefault("tier" + Math.max(1, Math.min(5, tier)), List.of("..."));
		}
		return pick(lines, random);
	}

	private static String pick(List<String> list, RandomSource random) {
		return list.get(random.nextInt(list.size()));
	}
}
