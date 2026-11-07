package com.onepiecemod.collection;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.google.gson.Gson;

import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.cuisine.CuisineItems;
import com.onepiecemod.cuisine.Fish;
import com.onepiecemod.item.DevilFruitItem;

/**
 * What the Collector's Log can hold: read from src/main/resources/onepiece/collections.json
 * (made by tools/collections/gen_collections.py), plus the fish and food lists, which come from the game itself.
 * Used by both the server (progress, rewards) and the player's game (the book screen).
 */
public final class CollectionData {
	public static final String FISH = "fish", FOOD = "food", SHIPS = "ships", SWORDS = "swords", ISLANDS = "islands";
	public static final List<String> TABS = List.of(FISH, FOOD, SHIPS, SWORDS, ISLANDS);

	public static class Reward {
		public int berries;
		public int xp;
		public List<String> items = List.of();
	}

	public static class Tab {
		/** "6" -> 150 berries when 6 entries are collected. Keys "half" and "all" scale with the tab's size. */
		public Map<String, Integer> milestones = Map.of();
		/** Extra things for collecting every entry. */
		public List<String> items = List.of();
		public int xp;
	}

	public static class Ship {
		public String id;
		public String name;
		public String crew = "";
		public String faction = "pirate";
		public int length;
		public String icon;
		public String hint = "";
	}

	public static class Sword {
		public String item;
		public String hint = "";
	}

	public static class Region {
		public String id;
		public String title;
		public Reward reward = new Reward();
	}

	public static class Goal {
		/** visit, explore, boss, quest, meet */
		public String type;
		public String text;
		public String character;
		public int seconds;
	}

	public static class Island {
		public String id;
		public String name;
		public String region;
		public List<Goal> goals = List.of();
		public Reward reward = new Reward();
	}

	private static class File {
		Map<String, Tab> tabs = Map.of();
		List<Ship> ships = List.of();
		List<Sword> swords = List.of();
		List<Region> regions = List.of();
		List<Island> islands = List.of();
	}

	private static File file;
	private static Map<String, Island> islandsById;
	private static List<Item> foods;

	private CollectionData() {
	}

	private static File file() {
		if (file == null) {
			try (InputStream in = CollectionData.class.getResourceAsStream("/onepiece/collections.json")) {
				file = new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), File.class);
			} catch (Exception e) {
				OnePieceMod.LOGGER.error("Could not read onepiece/collections.json", e);
				file = new File();
			}
			islandsById = new LinkedHashMap<>();
			for (Island island : file.islands) {
				islandsById.put(island.id, island);
			}
		}
		return file;
	}

	public static Tab tab(String tab) {
		return file().tabs.getOrDefault(tab, new Tab());
	}

	public static List<Ship> ships() {
		return file().ships;
	}

	public static List<Sword> swords() {
		return file().swords;
	}

	public static List<Region> regions() {
		return file().regions;
	}

	public static List<Island> islands() {
		return file().islands;
	}

	public static Island island(String id) {
		file();
		return islandsById.get(id);
	}

	/** Every One Piece food you can eat, except Devil Fruits (they have their own encyclopedia) and raw fish (the fish tab). */
	public static synchronized List<Item> foods() {
		if (foods == null) {
			List<Item> list = new ArrayList<>();
			for (Item item : BuiltInRegistries.ITEM) {
				Identifier id = BuiltInRegistries.ITEM.getKey(item);
				if (!id.getNamespace().equals(OnePieceMod.MOD_ID) || item instanceof DevilFruitItem || item instanceof CuisineItems.FishItem) {
					continue;
				}
				if (item.components().has(DataComponents.FOOD)) {
					list.add(item);
				}
			}
			foods = List.copyOf(list);
		}
		return foods;
	}

	public static List<Item> fishItems() {
		List<Item> list = new ArrayList<>();
		for (Fish fish : Fish.values()) {
			list.add(CuisineItems.fish(fish));
		}
		return list;
	}

	/** How many entries a tab has. */
	public static int size(String tab) {
		return switch (tab) {
			case FISH -> Fish.values().length;
			case FOOD -> foods().size();
			case SHIPS -> ships().size();
			case SWORDS -> swords().size();
			case ISLANDS -> islands().size();
			default -> 0;
		};
	}

	/** The milestone key as a count: "12" -> 12, "half" -> half the tab, "all" -> the whole tab. */
	public static int threshold(String tab, String key) {
		int size = size(tab);
		return switch (key) {
			case "all" -> size;
			case "half" -> (size + 1) / 2;
			default -> {
				try {
					yield Math.min(size, Integer.parseInt(key));
				} catch (NumberFormatException e) {
					yield Integer.MAX_VALUE;
				}
			}
		};
	}

	/** "onepiece:supreme_whetstone*3" -> 3 Supreme Whetstones. Unknown ids give an empty stack. */
	public static ItemStack stack(String spec) {
		int count = 1;
		int star = spec.indexOf('*');
		if (star >= 0) {
			count = Integer.parseInt(spec.substring(star + 1));
			spec = spec.substring(0, star);
		}
		Identifier id = Identifier.tryParse(spec);
		if (id == null) {
			return ItemStack.EMPTY;
		}
		Item item = BuiltInRegistries.ITEM.getValue(id);
		return item == Items.AIR ? ItemStack.EMPTY : new ItemStack(item, count);
	}

	public static Item item(String id) {
		Identifier key = Identifier.tryParse(id);
		return key == null ? Items.AIR : BuiltInRegistries.ITEM.getValue(key);
	}
}
