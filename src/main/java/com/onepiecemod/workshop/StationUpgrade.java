package com.onepiecemod.workshop;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.google.gson.Gson;

import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;

import com.onepiecemod.character.CharacterData;
import com.onepiecemod.crafting.Station;
import com.onepiecemod.crafting.StationRecipe;

/**
 * One upgrade in a station's upgrade tree, read from src/main/resources/onepiece/station_upgrades.json.
 * To add or change an upgrade, edit that JSON file, not this class.
 *
 * You build an upgrade once at its station (the cost is taken from your inventory, like a station recipe).
 * It stays yours for good, even on another copy of that station. An upgrade can:
 *  - unlock station recipes (a recipe with "requires": {"upgrade": "<id>"}), like the higher cooking tiers;
 *  - give perks: a chance of one extra result ("bonus") or a chance to keep the ingredients ("save").
 */
public class StationUpgrade {
	/** A short unique name, like "stoked_bellows". */
	public String id;
	/** Which station it belongs to, like "swordsmith_forge". */
	public String station;
	public String name;
	public String description;
	/** The item shown next to it in the tree. */
	public String icon;
	/** Upgrades you must own first (the branches of the tree). */
	public List<String> parents = List.of();
	public List<StationRecipe.Ingredient> cost = List.of();
	/** Progress gates, the same as for station recipes. */
	public StationRecipe.Requirements requires;
	public List<Perk> perks = List.of();

	/**
	 * "bonus": chance of one extra result each time you craft.
	 * "save": chance that crafting doesn't use up the ingredients.
	 * recipes: which station recipes it works on (leave it out for every recipe at this station).
	 */
	public static class Perk {
		public String type;
		public float chance;
		public List<String> recipes;
		/** A short label for the screen, like "Ammo". Leave it out for "everything here". */
		public String label;

		public boolean appliesTo(String recipe) {
			return recipes == null || recipes.isEmpty() || recipes.contains(recipe);
		}

		public String describe() {
			int percent = Math.round(chance * 100);
			String text = percent + ("save".equals(type) ? "% keep ingredients" : "% extra result");
			return label != null ? text + " (" + label + ")" : text;
		}
	}

	public Station stationType() {
		return Station.byId(station);
	}

	/** Depth in the tree: 0 for a root, 1 for its children and so on. Used to indent the list. */
	public int depth() {
		int deepest = -1;
		for (String parent : parents) {
			StationUpgrade up = get(parent);
			if (up != null && up != this) {
				deepest = Math.max(deepest, up.depth());
			}
		}
		return deepest + 1;
	}

	// ---- Loading ----

	private static final Map<String, StationUpgrade> ALL = new LinkedHashMap<>();

	public static Map<String, StationUpgrade> all() {
		if (ALL.isEmpty()) {
			try (InputStream in = StationUpgrade.class.getResourceAsStream("/onepiece/station_upgrades.json")) {
				StationUpgrade[] list = new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), StationUpgrade[].class);
				for (StationUpgrade upgrade : list) {
					ALL.put(upgrade.id, upgrade);
				}
			} catch (Exception e) {
				throw new RuntimeException("Could not read onepiece/station_upgrades.json", e);
			}
		}
		return ALL;
	}

	public static StationUpgrade get(String id) {
		return all().get(id);
	}

	/** The upgrades of one station, in the order they appear in the file. */
	public static List<StationUpgrade> forStation(Station station) {
		List<StationUpgrade> list = new ArrayList<>();
		for (StationUpgrade upgrade : all().values()) {
			if (upgrade.stationType() == station) {
				list.add(upgrade);
			}
		}
		return list;
	}

	/** Lists typos (unknown stations, items, parents) so they show up in the log at startup. */
	public static List<String> problems() {
		List<String> problems = new ArrayList<>();
		for (StationUpgrade upgrade : all().values()) {
			if (upgrade.stationType() == null) {
				problems.add(upgrade.id + ": unknown station " + upgrade.station);
			}
			for (String parent : upgrade.parents) {
				if (get(parent) == null) {
					problems.add(upgrade.id + ": unknown parent " + parent);
				}
			}
			for (StationRecipe.Ingredient ingredient : upgrade.cost) {
				String id = ingredient.tag != null ? ingredient.icon : ingredient.item;
				Item item = CharacterData.item(id);
				if (item == Items.AIR) {
					problems.add(upgrade.id + ": unknown cost item " + id);
				}
			}
			for (Perk perk : upgrade.perks) {
				if (perk.recipes != null) {
					for (String recipe : perk.recipes) {
						if (StationRecipe.get(recipe) == null) {
							problems.add(upgrade.id + ": perk names unknown recipe " + recipe);
						}
					}
				}
			}
		}
		for (StationRecipe recipe : StationRecipe.all().values()) {
			if (recipe.requires != null && recipe.requires.upgrade != null && get(recipe.requires.upgrade) == null) {
				problems.add("recipe " + recipe.id + ": unknown upgrade " + recipe.requires.upgrade);
			}
		}
		return problems;
	}
}
