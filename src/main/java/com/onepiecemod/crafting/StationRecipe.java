package com.onepiecemod.crafting;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.google.gson.Gson;

import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.character.CharacterAttachments;
import com.onepiecemod.character.CharacterData;
import com.onepiecemod.crew.Crew;
import com.onepiecemod.crew.CrewAttachments;
import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.haki.HakiAttachments;
import com.onepiecemod.sea.LogPoseTracker;

/**
 * One recipe made at a crafting station, read from src/main/resources/onepiece/station_recipes.json.
 * To add or change a station recipe, edit that JSON file, not this class.
 *
 * Station recipes don't use a 3x3 grid: you just need the ingredients somewhere in your inventory.
 */
public class StationRecipe {
	/** A short unique name, like "ships_wheel". */
	public String id;
	/** Which station makes it, like "shipwright_bench". */
	public String station;
	/** The item you get, like "onepiece:ships_wheel". */
	public String result;
	public int count = 1;
	public List<Ingredient> ingredients = List.of();
	/** What the player must have done first. Leave it out for "nothing". */
	public Requirements requires;

	/** Either an exact item ("item") or any item in a tag ("tag"), and how many. */
	public static class Ingredient {
		public String item;
		public String tag;
		/** For tags: the item to show in the station screen, like "minecraft:oak_planks". */
		public String icon;
		/** For tags: the name to show, like "Any Planks". */
		public String name;
		public int count = 1;

		public boolean matches(ItemStack stack) {
			if (stack.isEmpty()) {
				return false;
			}
			if (tag != null) {
				return stack.is(TagKey.create(Registries.ITEM, Identifier.parse(tag)));
			}
			return stack.is(CharacterData.item(item));
		}

		public ItemStack display() {
			return CharacterData.stack(tag != null ? icon : item, count);
		}

		public String displayName() {
			if (name != null) {
				return name;
			}
			return display().getHoverName().getString();
		}
	}

	/** Progress gates. Every one that is set must be met. */
	public static class Requirements {
		/** A boss the player must have beaten, like "smoker" (ids from characters.json). */
		public String boss;
		/** Minimum bounty in Berries. */
		public long bounty;
		/** Minimum number of islands recorded with a Log Pose. */
		public int islands;
		/** Minimum Armament Haki level (1-5). */
		public int armament;
		/** A role someone must fill in the player's crew, like "navigator" (ids from CrewRole). */
		public String crew;
		/** A station upgrade the player must have built, like "brick_oven" (ids from station_upgrades.json). */
		public String upgrade;
	}

	public Station stationType() {
		return Station.byId(station);
	}

	public ItemStack resultStack() {
		return CharacterData.stack(result, count);
	}

	// ---- Checks (server side) ----

	/** Returns null if the player may craft this, or a short reason why not, like "Beat Smoker".
	 * Several reasons are separated by "; ". */
	public String lockReason(ServerPlayer player) {
		if (requires == null) {
			return null;
		}
		List<String> missing = new ArrayList<>();
		if (requires.boss != null && !CharacterAttachments.has(player, CharacterAttachments.BOSSES_DEFEATED, requires.boss)) {
			CharacterData boss = CharacterData.get(requires.boss);
			missing.add("Beat " + (boss != null ? boss.name : requires.boss));
		}
		if (requires.bounty > 0 && Bounty.get(player) < requires.bounty) {
			missing.add("Bounty " + Bounty.format(requires.bounty));
		}
		if (requires.islands > 0 && LogPoseTracker.journey(player).visited().size() < requires.islands) {
			missing.add("Log Pose: " + requires.islands + " islands");
		}
		if (requires.armament > 0 && HakiAttachments.get(player).armamentLevel() < requires.armament) {
			missing.add("Armament Haki level " + requires.armament);
		}
		if (requires.crew != null) {
			CrewRole role = CrewRole.byId(requires.crew);
			Crew crew = player.getAttached(CrewAttachments.CREW);
			if (role != null && (crew == null || crew.member(role) == null)) {
				missing.add("A " + role.title() + " in your crew");
			}
		}
		if (requires.upgrade != null && !com.onepiecemod.workshop.StationUpgrades.has(player, requires.upgrade)) {
			com.onepiecemod.workshop.StationUpgrade upgrade = com.onepiecemod.workshop.StationUpgrade.get(requires.upgrade);
			missing.add("Station upgrade: " + (upgrade != null ? upgrade.name : requires.upgrade));
		}
		return missing.isEmpty() ? null : String.join("; ", missing);
	}

	/**
	 * True if a station may use this stack up. Enchanted, renamed or upgraded items (anything changed
	 * beyond wear, repair cost and a Log Pose's needle) are kept safe, so crafting Kitetsu never eats your best diamond sword.
	 */
	public static boolean isPlain(ItemStack stack) {
		return stack.getComponentsPatch()
				.forget(type -> type == DataComponents.DAMAGE || type == DataComponents.REPAIR_COST
						// A Log Pose's needle direction: the journey itself is saved on the player.
						|| type == DataComponents.LODESTONE_TRACKER)
				.isEmpty();
	}

	/** How many plain items matching this ingredient the player is carrying. Armor and the offhand don't count.
	 * Works on both sides. */
	public static int countIn(Inventory inventory, Ingredient ingredient) {
		int total = 0;
		for (ItemStack stack : inventory.getNonEquipmentItems()) {
			if (ingredient.matches(stack) && isPlain(stack)) {
				total += stack.getCount();
			}
		}
		return total;
	}

	/** True if the player carries a matching item that is kept safe (enchanted, renamed or upgraded). */
	public static boolean hasKeptSafe(Inventory inventory, Ingredient ingredient) {
		for (ItemStack stack : inventory.getNonEquipmentItems()) {
			if (ingredient.matches(stack) && !isPlain(stack)) {
				return true;
			}
		}
		return false;
	}

	public boolean hasIngredients(Player player) {
		for (Ingredient ingredient : ingredients) {
			if (countIn(player.getInventory(), ingredient) < ingredient.count) {
				return false;
			}
		}
		return true;
	}

	/** How many times in a row the player could craft this with what they carry. */
	public int timesCraftable(Player player) {
		int times = Integer.MAX_VALUE;
		for (Ingredient ingredient : ingredients) {
			times = Math.min(times, countIn(player.getInventory(), ingredient) / Math.max(1, ingredient.count));
		}
		return ingredients.isEmpty() ? 0 : times;
	}

	/** Takes the ingredients out of the player's inventory. Check hasIngredients first. */
	public void takeIngredients(Player player) {
		Inventory inventory = player.getInventory();
		for (Ingredient ingredient : ingredients) {
			int left = ingredient.count;
			for (ItemStack stack : inventory.getNonEquipmentItems()) {
				if (left <= 0) {
					break;
				}
				if (ingredient.matches(stack) && isPlain(stack)) {
					int take = Math.min(left, stack.getCount());
					stack.shrink(take);
					left -= take;
				}
			}
		}
		inventory.setChanged();
	}

	// ---- Loading ----

	private static final Map<String, StationRecipe> ALL = new LinkedHashMap<>();

	public static Map<String, StationRecipe> all() {
		if (ALL.isEmpty()) {
			try (InputStream in = StationRecipe.class.getResourceAsStream("/onepiece/station_recipes.json")) {
				StationRecipe[] list = new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), StationRecipe[].class);
				for (StationRecipe recipe : list) {
					ALL.put(recipe.id, recipe);
				}
			} catch (Exception e) {
				throw new RuntimeException("Could not read onepiece/station_recipes.json", e);
			}
		}
		return ALL;
	}

	public static StationRecipe get(String id) {
		return all().get(id);
	}

	/** The recipes of one station, in the order they appear in the file. */
	public static List<StationRecipe> forStation(Station station) {
		List<StationRecipe> list = new ArrayList<>();
		for (StationRecipe recipe : all().values()) {
			if (recipe.stationType() == station) {
				list.add(recipe);
			}
		}
		return list;
	}

	/** Lists recipe ingredients or results that don't exist, so typos show up in the log at startup. */
	public static List<String> problems() {
		List<String> problems = new ArrayList<>();
		for (StationRecipe recipe : all().values()) {
			if (recipe.stationType() == null) {
				problems.add(recipe.id + ": unknown station " + recipe.station);
			}
			if (CharacterData.item(recipe.result) == Items.AIR) {
				problems.add(recipe.id + ": unknown result " + recipe.result);
			}
			for (Ingredient ingredient : recipe.ingredients) {
				String id = ingredient.tag != null ? ingredient.icon : ingredient.item;
				Item item = CharacterData.item(id);
				if (item == Items.AIR) {
					problems.add(recipe.id + ": unknown ingredient " + id);
				}
			}
			if (recipe.requires != null && recipe.requires.boss != null && CharacterData.get(recipe.requires.boss) == null) {
				problems.add(recipe.id + ": unknown boss " + recipe.requires.boss);
			}
		}
		return problems;
	}
}
