package com.onepiecemod.recipeview.client;

import java.io.Reader;
import java.net.URI;
import java.net.URL;
import java.nio.file.FileSystem;
import java.nio.file.FileSystemNotFoundException;
import java.nio.file.FileSystems;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Stream;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import net.fabricmc.loader.api.FabricLoader;
import net.fabricmc.loader.api.ModContainer;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.character.CharacterData;
import com.onepiecemod.crafting.Station;
import com.onepiecemod.crafting.StationRecipe;
import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.item.ModItems;
import com.onepiecemod.keepsake.Keepsakes;

/**
 * Everything the recipe viewer knows: which recipes make an item, and which use it.
 *
 * It reads the recipe files straight out of the game and mod jars (data/<mod>/recipe/*.json),
 * the station recipes (onepiece/station_recipes.json), trader deals and boss drops (onepiece/characters.json).
 * It is built the first time the viewer is opened in a world, and again after joining another world.
 */
public class RecipeIndex {
	private static RecipeIndex current;

	/** Every recipe, in the order they were found. */
	private final List<ViewRecipe> all = new ArrayList<>();
	/** Item -> recipes that make it. */
	private final Map<Item, List<ViewRecipe>> byResult = new HashMap<>();
	/** Item -> recipes that need it. */
	private final Map<Item, List<ViewRecipe>> byInput = new HashMap<>();
	/** Every item, One Piece items first, for the item list beside the inventory. */
	private final List<ItemStack> items = new ArrayList<>();
	private final Map<String, List<ItemStack>> tagCache = new HashMap<>();
	/** Where recipes come from: "entity:<id>" (mob drops), "char:<id>" (trades, boss drops, quest rewards), "chest:<id>". */
	private final Map<String, List<ViewRecipe>> bySource = new HashMap<>();

	public static RecipeIndex get() {
		if (current == null) {
			current = new RecipeIndex();
			current.build();
		}
		return current;
	}

	/** Forget everything (tags can differ between worlds and servers). */
	public static void reset() {
		current = null;
	}

	/** Every recipe the index knows (JEI reads these). */
	public List<ViewRecipe> all() {
		return all;
	}

	public List<ItemStack> items() {
		return items;
	}

	/** Recipes that make this item. */
	public List<ViewRecipe> recipesFor(ItemStack stack) {
		return byResult.getOrDefault(stack.getItem(), List.of());
	}

	/** Recipes that come from one source, like everything a creature drops ("entity:onepiece:sea_king"). */
	public List<ViewRecipe> fromSource(String source) {
		return bySource.getOrDefault(source, List.of());
	}

	private void addFrom(String source, ViewRecipe recipe) {
		if (source.startsWith("char:") || source.contains(":onepiece")) {
			recipe.jeiCategory = "source";
		}
		if (!recipe.result.isEmpty()) {
			bySource.computeIfAbsent(source, k -> new ArrayList<>()).add(recipe);
		}
		add(recipe);
	}

	/** Recipes that use this item as an ingredient. */
	public List<ViewRecipe> usesOf(ItemStack stack) {
		return byInput.getOrDefault(stack.getItem(), List.of());
	}

	// ---- Building ----

	private void build() {
		long start = System.currentTimeMillis();
		for (Item item : BuiltInRegistries.ITEM) {
			if (item != Items.AIR) {
				items.add(new ItemStack(item));
			}
		}
		// One Piece items first, then everything else in game order.
		items.sort(Comparator.comparingInt(stack -> BuiltInRegistries.ITEM.getKey(stack.getItem()).getNamespace().startsWith("onepiece") ? 0 : 1));

		for (StationRecipe recipe : StationRecipe.all().values()) {
			addStation(recipe);
		}
		for (Map.Entry<String, JsonObject> entry : readRecipeFiles().entrySet()) {
			try {
				addJson(entry.getValue());
			} catch (Exception e) {
				// An unusual recipe file: just leave it out of the viewer.
			}
		}
		for (CharacterData character : CharacterData.all().values()) {
			addCharacter(character);
		}
		for (Map.Entry<String, JsonObject> entry : readDataFiles("loot_table", "minecraft/loot_table/blocks/stone.json").entrySet()) {
			try {
				addLoot(entry.getKey(), entry.getValue());
			} catch (Exception e) {
				// Leave out loot tables we can't read.
			}
		}
		// Items handed out by code (boss sword drops, raid trophies, music discs...), listed in onepiece/item_sources.json.
		addItemSources();
		for (CharacterData character : CharacterData.all().values()) {
			addKeepsakes(character);
		}
		// Devil Fruits also fall from leaves (item/ModLootTables, done in code so not in a loot file).
		for (Item fruit : ModItems.DEVIL_FRUITS.values()) {
			ViewRecipe view = new ViewRecipe("Falls from leaves", stack(Items.OAK_LEAVES), 0, stack(fruit));
			view.notes.add("Very rare: about 1 in 2,000 leaves you break drops a random Devil Fruit.");
			view.jeiCategory = "source";
			add(view);
		}
		OnePieceMod.LOGGER.info("Recipe viewer: {} items have recipes ({} ms)", byResult.size(), System.currentTimeMillis() - start);
	}

	private void add(ViewRecipe recipe) {
		if (recipe.result.isEmpty()) {
			return;
		}
		all.add(recipe);
		byResult.computeIfAbsent(recipe.result.getItem(), k -> new ArrayList<>()).add(recipe);
		Set<Item> seen = new HashSet<>();
		for (ViewRecipe.Slot slot : recipe.inputs) {
			for (ItemStack option : slot.options) {
				if (seen.add(option.getItem())) {
					byInput.computeIfAbsent(option.getItem(), k -> new ArrayList<>()).add(recipe);
				}
			}
		}
	}

	// ---- Station recipes ----

	private void addStation(StationRecipe recipe) {
		Station station = recipe.stationType();
		if (station == null) {
			return;
		}
		ViewRecipe view = new ViewRecipe(station.title() + " (Tier " + station.tier() + ")",
				CharacterData.stack("onepiece:" + station.id(), 1), 0, recipe.resultStack());
		for (StationRecipe.Ingredient ingredient : recipe.ingredients) {
			List<ItemStack> options = ingredient.tag != null ? tag(ingredient.tag, ingredient.count) : single(ingredient.item, ingredient.count);
			if (options.isEmpty()) {
				options = single(ingredient.icon, ingredient.count);
			}
			view.inputs.add(new ViewRecipe.Slot(options, ingredient.name));
		}
		view.notes.add("Ingredients just need to be in your inventory.");
		view.jeiCategory = "station:" + station.id();
		StationRecipe.Requirements needs = recipe.requires;
		if (needs != null) {
			if (needs.boss != null) {
				CharacterData boss = CharacterData.get(needs.boss);
				gate(view, "Beat " + (boss != null ? boss.name : needs.boss));
			}
			if (needs.bounty > 0) {
				gate(view, "Bounty of " + Bounty.format(needs.bounty));
			}
			if (needs.islands > 0) {
				gate(view, "Log Pose: " + needs.islands + " islands");
			}
			if (needs.armament > 0) {
				gate(view, "Armament Haki level " + needs.armament);
			}
			if (needs.crew != null) {
				CrewRole role = CrewRole.byId(needs.crew);
				gate(view, "A " + (role != null ? role.title() : needs.crew) + " in your crew");
			}
		}
		add(view);
	}

	// ---- Character Wanted Posters and Vivre Cards (keepsake/Keepsakes) ----

	private void addKeepsakes(CharacterData character) {
		if (Keepsakes.hasPoster(character)) {
			ViewRecipe view = new ViewRecipe("Buy at a wall Wanted Poster", CharacterData.stack("onepiece:wall_wanted_poster", 1), 0,
					CharacterData.stack("onepiece:wanted_poster_" + character.id, 1));
			view.inputs.add(new ViewRecipe.Slot(single("onepiece:berry", Keepsakes.posterPrice(character)), null));
			view.notes.add("Hold Berries and right-click a wall Wanted Poster in a town.");
			view.notes.add(character.isBossRole() ? "For sale once you've beaten " + character.name + "."
					: "For sale from the " + Keepsakes.SAGA_NAMES[Keepsakes.posterSaga(character)] + " part of the story.");
			if (!character.isBossRole()) {
				view.notes.add("Sometimes it falls out of the morning newspaper.");
			}
			addFrom("char:" + character.id, view);
		}
		if (Keepsakes.hasCard(character)) {
			ViewRecipe view = new ViewRecipe("Gift from " + character.name, CharacterData.stack("minecraft:paper", 1), 0,
					CharacterData.stack("onepiece:vivre_card_" + character.id, 1));
			view.notes.add(character.quests.isEmpty() ? "Trade with " + character.name + " at Master level."
					: "Finish " + character.name + "'s quests, or trade with them at Master level.");
			addFrom("char:" + character.id, view);
		}
	}

	// ---- Items given out by code ----

	/** Reads onepiece/item_sources.json: one "how to get it" card per item that no recipe or loot table makes. */
	private void addItemSources() {
		try (var in = RecipeIndex.class.getResourceAsStream("/onepiece/item_sources.json")) {
			if (in == null) {
				return;
			}
			JsonArray list = JsonParser.parseReader(new java.io.InputStreamReader(in, java.nio.charset.StandardCharsets.UTF_8)).getAsJsonArray();
			for (JsonElement element : list) {
				JsonObject source = element.getAsJsonObject();
				ViewRecipe view = new ViewRecipe(source.get("title").getAsString(),
						CharacterData.stack(source.get("icon").getAsString(), 1), 0, CharacterData.stack(source.get("item").getAsString(), 1));
				for (JsonElement note : source.getAsJsonArray("notes")) {
					view.notes.add(note.getAsString());
				}
				view.jeiCategory = "source";
				if (source.has("boss")) {
					addFrom("char:" + source.get("boss").getAsString(), view);
				} else {
					add(view);
				}
			}
		} catch (Exception e) {
			OnePieceMod.LOGGER.warn("Could not read onepiece/item_sources.json", e);
		}
	}

	private static void gate(ViewRecipe view, String line) {
		view.notes.add("Requires: " + line);
		view.locked = true;
	}

	// ---- Traders and bosses ----

	private void addCharacter(CharacterData character) {
		for (int level = 0; level < character.levels.size(); level++) {
			for (CharacterData.Trade trade : character.levels.get(level)) {
				if (trade.chart != null || trade.sell == null) {
					continue;
				}
				ViewRecipe view = new ViewRecipe("Trade with " + character.name, CharacterData.stack("minecraft:emerald", 1), 0,
						CharacterData.stack(trade.sell, trade.sellCount));
				view.inputs.add(new ViewRecipe.Slot(single(trade.buy, trade.buyCount), null));
				view.notes.add("Trader level " + (level + 1) + " (" + LEVEL_NAMES[Math.min(level, 4)] + ")");
				addFrom("char:" + character.id, view);
			}
		}
		if (character.isBossRole()) {
			drop(character, character.fruitItem, "Beat " + character.name + " as a boss");
			drop(character, character.bonusDrop, "Beat " + character.name + " as a boss");
			for (String reward : character.hardRewards) {
				drop(character, reward, "Beat " + character.name + " on Hard");
			}
			for (String reward : character.expertRewards) {
				drop(character, reward, "Beat " + character.name + " on Expert");
			}
		}
		for (CharacterData.Quest quest : character.quests) {
			// Starting a "defeat" step hands you the boss's Wanted Poster; a "talk" step hands you a Vivre Card.
			if (quest.target != null && ("defeat".equals(quest.type) || "talk".equals(quest.type))) {
				boolean defeat = "defeat".equals(quest.type);
				CharacterData target = CharacterData.get(quest.target);
				String targetName = target != null ? target.name : quest.target;
				ViewRecipe view = new ViewRecipe("Quest for " + character.name, CharacterData.stack("minecraft:writable_book", 1), 0,
						CharacterData.stack("onepiece:" + (defeat ? "wanted_poster_" : "vivre_card_") + quest.target, 1));
				view.notes.add(character.name + " gives it to you when the quest asks you to "
						+ (defeat ? "defeat " : "find ") + targetName + ".");
				addFrom("char:" + character.id, view);
			}
			if (quest.rewardItem != null) {
				ViewRecipe view = new ViewRecipe("Quest for " + character.name, CharacterData.stack("minecraft:writable_book", 1), 0,
						CharacterData.stack(quest.rewardItem, quest.rewardCount));
				if ("fetch".equals(quest.type) && quest.item != null) {
					view.inputs.add(new ViewRecipe.Slot(single(quest.item, quest.count), null));
					view.notes.add("Bring the items to " + character.name + ".");
				} else if ("defeat".equals(quest.type) && quest.target != null) {
					CharacterData target = CharacterData.get(quest.target);
					view.notes.add("Defeat " + (target != null ? target.name : quest.target) + ".");
				} else {
					view.notes.add("Finish this step of " + character.name + "'s quest.");
				}
				addFrom("char:" + character.id, view);
			}
		}
	}

	private static final String[] LEVEL_NAMES = {"Novice", "Apprentice", "Journeyman", "Expert", "Master"};

	private void drop(CharacterData boss, String itemId, String how) {
		ItemStack stack = itemId == null ? ItemStack.EMPTY : CharacterData.stack(itemId, 1);
		if (stack.isEmpty()) {
			return;
		}
		ViewRecipe view = new ViewRecipe("Boss drop: " + boss.name, CharacterData.stack("minecraft:iron_sword", 1), 0, stack);
		view.notes.add(how + ".");
		addFrom("char:" + boss.id, view);
	}

	// ---- Loot tables (mob drops, block drops, chest loot, fishing...) ----

	private void addLoot(String id, JsonObject json) {
		Identifier tableId = Identifier.parse(id);
		String path = tableId.getPath();
		String kind = path.contains("/") ? path.substring(0, path.indexOf('/')) : "";
		String name = path.substring(path.lastIndexOf('/') + 1);
		Identifier thing = Identifier.fromNamespaceAndPath(tableId.getNamespace(), name);

		String title;
		ItemStack icon;
		switch (kind) {
			case "blocks" -> {
				Item blockItem = BuiltInRegistries.ITEM.getValue(thing);
				title = "Break " + (blockItem != Items.AIR ? new ItemStack(blockItem).getHoverName().getString() : pretty(name));
				icon = blockItem != Items.AIR ? new ItemStack(blockItem) : stack(Items.IRON_PICKAXE);
			}
			case "entities" -> {
				var type = BuiltInRegistries.ENTITY_TYPE.getOptional(thing);
				title = "Dropped by " + (type.isPresent() ? type.get().getDescription().getString() : pretty(name));
				Item egg = BuiltInRegistries.ITEM.getValue(Identifier.fromNamespaceAndPath(tableId.getNamespace(), name + "_spawn_egg"));
				icon = egg != Items.AIR ? new ItemStack(egg) : stack(Items.IRON_SWORD);
			}
			case "chests" -> {
				title = "Chest loot: " + pretty(path.substring(path.indexOf('/') + 1).replace('/', ' '));
				icon = stack(Items.CHEST);
			}
			case "gameplay" -> {
				title = pretty(path.substring(path.indexOf('/') + 1).replace('/', ' '));
				icon = path.contains("fishing") ? stack(Items.FISHING_ROD) : stack(Items.EMERALD);
			}
			case "archaeology" -> {
				title = "Brushing: " + pretty(name);
				icon = stack(Items.BRUSH);
			}
			default -> {
				return;
			}
		}
		if (!json.has("pools")) {
			return;
		}
		Map<Item, Float> chances = new LinkedHashMap<>();
		for (JsonElement poolElement : json.getAsJsonArray("pools")) {
			JsonObject pool = poolElement.getAsJsonObject();
			if (!pool.has("entries")) {
				continue;
			}
			float poolChance = chanceOf(pool);
			int totalWeight = 0;
			for (JsonElement entry : pool.getAsJsonArray("entries")) {
				totalWeight += weightOf(entry.getAsJsonObject());
			}
			for (JsonElement entry : pool.getAsJsonArray("entries")) {
				JsonObject object = entry.getAsJsonObject();
				float chance = poolChance * chanceOf(object) * weightOf(object) / Math.max(1, totalWeight);
				collectItems(object, chance, chances);
			}
		}
		for (Map.Entry<Item, Float> drop : chances.entrySet()) {
			// Skip "this block drops itself": every block does that, so it would just be noise.
			if (kind.equals("blocks") && BuiltInRegistries.ITEM.getKey(drop.getKey()).equals(thing)) {
				continue;
			}
			ViewRecipe view = new ViewRecipe(title, icon, 0, new ItemStack(drop.getKey()));
			String source = kind.equals("entities") ? "entity:" + thing : kind.equals("chests") ? "chest:" + id : null;
			float percent = Math.min(1f, drop.getValue()) * 100f;
			if (percent < 99.5f) {
				view.notes.add("Chance: " + (percent >= 10 ? Math.round(percent) : Math.round(percent * 10) / 10.0f) + "%"
						+ (kind.equals("chests") ? " per roll" : ""));
			}
			if (kind.equals("chests")) {
				view.notes.add("Found in chests in the world.");
			}
			if (source != null) {
				addFrom(source, view);
			} else {
				add(view);
			}
		}
	}

	/** Items in a loot entry, including entries inside "alternatives", "group" and "sequence". */
	private static void collectItems(JsonObject entry, float chance, Map<Item, Float> into) {
		String type = entry.has("type") ? entry.get("type").getAsString() : "";
		if (type.equals("minecraft:item") && entry.has("name")) {
			Item item = CharacterData.item(entry.get("name").getAsString());
			if (item != Items.AIR) {
				into.merge(item, chance, Math::max);
			}
		} else if (entry.has("children")) {
			for (JsonElement child : entry.getAsJsonArray("children")) {
				collectItems(child.getAsJsonObject(), chance * chanceOf(child.getAsJsonObject()), into);
			}
		}
	}

	private static int weightOf(JsonObject entry) {
		return entry.has("weight") ? entry.get("weight").getAsInt() : 1;
	}

	/** A "random_chance" condition, if any (1 = always). */
	private static float chanceOf(JsonObject object) {
		float chance = 1f;
		for (String key : new String[] {"conditions", "condition"}) {
			if (object.has(key)) {
				JsonElement value = object.get(key);
				JsonArray list = value.isJsonArray() ? value.getAsJsonArray() : new JsonArray();
				if (value.isJsonObject()) {
					list.add(value);
				}
				for (JsonElement condition : list) {
					JsonObject c = condition.getAsJsonObject();
					String type = c.has("condition") ? c.get("condition").getAsString() : c.has("type") ? c.get("type").getAsString() : "";
					if (type.endsWith("random_chance") && c.has("chance") && c.get("chance").isJsonPrimitive()) {
						chance *= c.get("chance").getAsFloat();
					}
				}
			}
		}
		return chance;
	}

	/** "sea_king" -> "Sea King". */
	private static String pretty(String name) {
		StringBuilder out = new StringBuilder();
		for (String word : name.split("[_ ]")) {
			if (!word.isEmpty()) {
				out.append(out.isEmpty() ? "" : " ").append(Character.toUpperCase(word.charAt(0))).append(word.substring(1));
			}
		}
		return out.toString();
	}

	// ---- Recipe files (crafting table, furnaces, stonecutter, smithing) ----

	private void addJson(JsonObject json) {
		String type = json.has("type") ? json.get("type").getAsString() : "";
		switch (type) {
			case "minecraft:crafting_shaped" -> {
				ViewRecipe view = new ViewRecipe("Crafting Table", stack(Items.CRAFTING_TABLE), 3, result(json.get("result")));
				JsonObject key = json.getAsJsonObject("key");
				JsonArray pattern = json.getAsJsonArray("pattern");
				for (int row = 0; row < 3; row++) {
					String line = row < pattern.size() ? pattern.get(row).getAsString() : "";
					for (int col = 0; col < 3; col++) {
						char c = col < line.length() ? line.charAt(col) : ' ';
						view.inputs.add(c == ' ' || !key.has(String.valueOf(c)) ? ViewRecipe.Slot.EMPTY : slot(key.get(String.valueOf(c))));
					}
				}
				add(view);
			}
			case "minecraft:crafting_shapeless" -> {
				ViewRecipe view = new ViewRecipe("Crafting Table (any shape)", stack(Items.CRAFTING_TABLE), 3, result(json.get("result")));
				for (JsonElement ingredient : json.getAsJsonArray("ingredients")) {
					view.inputs.add(slot(ingredient));
				}
				add(view);
			}
			case "minecraft:crafting_transmute" -> {
				ViewRecipe view = new ViewRecipe("Crafting Table (any shape)", stack(Items.CRAFTING_TABLE), 3, result(json.get("result")));
				view.inputs.add(slot(json.get("input")));
				view.inputs.add(slot(json.get("material")));
				add(view);
			}
			case "minecraft:smelting" -> cooking(json, "Furnace", Items.FURNACE);
			case "minecraft:blasting" -> cooking(json, "Blast Furnace", Items.BLAST_FURNACE);
			case "minecraft:smoking" -> cooking(json, "Smoker", Items.SMOKER);
			case "minecraft:campfire_cooking" -> cooking(json, "Campfire", Items.CAMPFIRE);
			case "minecraft:stonecutting" -> {
				ViewRecipe view = new ViewRecipe("Stonecutter", stack(Items.STONECUTTER), 0, result(json.get("result")));
				view.inputs.add(slot(json.get("ingredient")));
				add(view);
			}
			case "minecraft:smithing_transform" -> {
				ViewRecipe view = new ViewRecipe("Smithing Table", stack(Items.SMITHING_TABLE), 0, result(json.get("result")));
				view.inputs.add(slot(json.get("template")));
				view.inputs.add(slot(json.get("base")));
				view.inputs.add(slot(json.get("addition")));
				add(view);
			}
			default -> {
				// Special recipes (map cloning, fireworks...) have no fixed ingredients: skip them.
			}
		}
	}

	private void cooking(JsonObject json, String title, Item block) {
		ViewRecipe view = new ViewRecipe(title, stack(block), 0, result(json.get("result")));
		view.inputs.add(slot(json.get("ingredient")));
		if (json.has("cookingtime")) {
			view.notes.add("Takes " + (json.get("cookingtime").getAsInt() / 20.0f) + " seconds");
		}
		add(view);
	}

	/** "minecraft:stick", "#minecraft:planks", {"item": ...}, {"tag": ...} or a list of those. */
	private ViewRecipe.Slot slot(JsonElement json) {
		if (json == null || json.isJsonNull()) {
			return ViewRecipe.Slot.EMPTY;
		}
		List<ItemStack> options = new ArrayList<>();
		if (json.isJsonArray()) {
			for (JsonElement element : json.getAsJsonArray()) {
				options.addAll(slot(element).options);
			}
			return new ViewRecipe.Slot(options, null);
		}
		String id;
		if (json.isJsonObject()) {
			JsonObject object = json.getAsJsonObject();
			id = object.has("tag") ? "#" + object.get("tag").getAsString() : object.has("item") ? object.get("item").getAsString() : null;
		} else {
			id = json.getAsString();
		}
		if (id == null) {
			return ViewRecipe.Slot.EMPTY;
		}
		return id.startsWith("#") ? new ViewRecipe.Slot(tag(id.substring(1), 1), null) : new ViewRecipe.Slot(single(id, 1), null);
	}

	/** {"id": "minecraft:stick", "count": 4} or just "minecraft:stick". */
	private static ItemStack result(JsonElement json) {
		if (json == null) {
			return ItemStack.EMPTY;
		}
		if (json.isJsonPrimitive()) {
			return CharacterData.stack(json.getAsString(), 1);
		}
		JsonObject object = json.getAsJsonObject();
		String id = object.has("id") ? object.get("id").getAsString() : object.has("item") ? object.get("item").getAsString() : null;
		int count = object.has("count") ? object.get("count").getAsInt() : 1;
		return id == null ? ItemStack.EMPTY : CharacterData.stack(id, count);
	}

	private static ItemStack stack(Item item) {
		return new ItemStack(item);
	}

	private static List<ItemStack> single(String id, int count) {
		ItemStack stack = id == null ? ItemStack.EMPTY : CharacterData.stack(id, count);
		return stack.isEmpty() ? List.of() : List.of(stack);
	}

	/** Every item in a tag, like all planks for "minecraft:planks". */
	private List<ItemStack> tag(String id, int count) {
		List<ItemStack> list = tagCache.computeIfAbsent(id, key -> {
			TagKey<Item> tag = TagKey.create(Registries.ITEM, Identifier.parse(key));
			List<ItemStack> found = new ArrayList<>();
			for (ItemStack stack : items) {
				if (stack.is(tag)) {
					found.add(stack);
				}
			}
			return found;
		});
		if (count == 1) {
			return list;
		}
		List<ItemStack> counted = new ArrayList<>();
		for (ItemStack stack : list) {
			counted.add(stack.copyWithCount(count));
		}
		return counted;
	}

	// ---- Finding the recipe files inside the jars ----

	/** Recipe id -> JSON, from every mod (Minecraft itself counts as a mod here). */
	private static Map<String, JsonObject> readRecipeFiles() {
		return readDataFiles("recipe", "minecraft/recipe/stick.json");
	}

	/** File id -> JSON for every data/<namespace>/<folder>/**.json in the game and mod jars. */
	private static Map<String, JsonObject> readDataFiles(String folder, String vanillaExample) {
		Map<String, JsonObject> found = new LinkedHashMap<>();
		for (ModContainer mod : FabricLoader.getInstance().getAllMods()) {
			for (Path root : mod.getRootPaths()) {
				readDataFolder(root.resolve("data"), folder, found);
			}
		}
		// Backup in case the game jar isn't listed as a mod root: find it through a vanilla recipe file.
		boolean hasVanilla = found.keySet().stream().anyMatch(id -> id.startsWith("minecraft:"));
		if (!hasVanilla) {
			try {
				URL url = Items.class.getClassLoader().getResource("data/" + vanillaExample);
				if (url != null && "jar".equals(url.getProtocol())) {
					URI uri = url.toURI();
					FileSystem fs;
					try {
						fs = FileSystems.getFileSystem(uri);
					} catch (FileSystemNotFoundException e) {
						fs = FileSystems.newFileSystem(uri, Map.of());
					}
					readDataFolder(fs.getPath("/data"), folder, found);
				} else if (url != null) {
					Path data = Path.of(url.toURI());
					for (int i = 0; i < vanillaExample.split("/").length; i++) {
						data = data.getParent();
					}
					readDataFolder(data, folder, found);
				}
			} catch (Exception e) {
				OnePieceMod.LOGGER.warn("Recipe viewer: could not find the vanilla {} files", folder, e);
			}
		}
		return found;
	}

	private static void readDataFolder(Path data, String folder, Map<String, JsonObject> found) {
		if (!Files.isDirectory(data)) {
			return;
		}
		try (Stream<Path> namespaces = Files.list(data)) {
			for (Path namespace : namespaces.toList()) {
				Path recipes = namespace.resolve(folder);
				if (!Files.isDirectory(recipes)) {
					continue;
				}
				String ns = namespace.getFileName().toString().replace("/", "");
				try (Stream<Path> files = Files.walk(recipes)) {
					for (Path file : files.filter(p -> p.toString().endsWith(".json")).toList()) {
						String name = recipes.relativize(file).toString().replace('\\', '/');
						String id = ns + ":" + name.substring(0, name.length() - 5);
						if (found.containsKey(id)) {
							continue;
						}
						try (Reader reader = Files.newBufferedReader(file)) {
							JsonElement json = JsonParser.parseReader(reader);
							if (json.isJsonObject()) {
								found.put(id, json.getAsJsonObject());
							}
						} catch (Exception e) {
							// Skip files that aren't valid JSON.
						}
					}
				}
			}
		} catch (Exception e) {
			OnePieceMod.LOGGER.warn("Recipe viewer: could not read {} files in {}", folder, data, e);
		}
	}
}
