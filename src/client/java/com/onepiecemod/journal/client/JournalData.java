package com.onepiecemod.journal.client;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonParser;

import net.minecraft.client.resources.language.I18n;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.character.CharacterData;
import com.onepiecemod.character.Locations;
import com.onepiecemod.creature.CreatureSpecies;
import com.onepiecemod.guide.GuideData;
import com.onepiecemod.item.ModItems;
import com.onepiecemod.power.DevilFruit;
import com.onepiecemod.power.DevilFruits;
import com.onepiecemod.recipeview.client.ItemDescriptions;
import com.onepiecemod.recipeview.client.RecipeIndex;
import com.onepiecemod.recipeview.client.ViewRecipe;

/**
 * Everything in the Crafter's Journal: its tabs and the entries in each tab.
 *
 * The tab list and which items go where are in src/main/resources/onepiece/journal.json
 * (written by tools/journal/gen_journal.py). Each tab starts with chapters from the old handbook (onepiece/guide.json).
 * Devil Fruits, creatures, bosses, characters and structures are built here from their own data,
 * so new ones show up in the journal by themselves.
 */
public class JournalData {
	/** One page of the journal about one thing: an item, a creature, a boss, a place... */
	public static class Entry {
		public final String title;
		public final ItemStack icon;
		/** The item this entry is about, or EMPTY (creatures, places). Its recipes and uses are shown. */
		public final ItemStack item;
		/** Text for the left page. "# " = heading, "- " = bullet, "> " = tip, "" = space. */
		public final List<String> lines = new ArrayList<>();
		/** Cards shown before the item's own recipes, like a creature's drops or a trader's deals. */
		public final List<ViewRecipe> cards = new ArrayList<>();
		/** What the first card list is called, like "Drops" or "How to get". */
		public String cardsTitle = "How to get";
		final String search;

		Entry(String title, ItemStack icon, ItemStack item, String searchExtra) {
			this.title = title;
			this.icon = icon;
			this.item = item;
			this.search = (title + " " + searchExtra).toLowerCase(Locale.ROOT);
		}

		/** The cards for the first list: this entry's own cards, then the item's recipes. */
		public List<ViewRecipe> howToGet() {
			List<ViewRecipe> list = new ArrayList<>(cards);
			if (!item.isEmpty()) {
				for (ViewRecipe recipe : RecipeIndex.get().recipesFor(item)) {
					if (!list.contains(recipe)) {
						list.add(recipe);
					}
				}
			}
			return list;
		}

		public List<ViewRecipe> usedIn() {
			return item.isEmpty() ? List.of() : RecipeIndex.get().usesOf(item);
		}
	}

	public static class Tab {
		public String id;
		public String title;
		public String icon;
		public String color;
		public List<String> chapters = List.of();
		public List<String> intro = List.of();
		public String dynamic;
		public List<String> items = List.of();

		/** Built from chapters + intro. */
		public transient List<String> lines;
		public transient List<Entry> entries;
		public transient ItemStack iconStack;

		public int colorArgb() {
			try {
				return 0xFF000000 | Integer.parseInt(color, 16);
			} catch (RuntimeException e) {
				return 0xFFFFD75E;
			}
		}
	}

	private static class Structure {
		String id, name, tier, who, guards, where;
		boolean lair;
	}

	private static class File {
		List<Tab> tabs = new ArrayList<>();
		List<Structure> structures = new ArrayList<>();
	}

	private static JournalData current;

	public final List<Tab> tabs;
	private final List<Structure> structures;
	/** Item -> its entry, so clicking an item anywhere opens the right page. */
	private final Map<Item, Entry> byItem = new HashMap<>();

	public static JournalData get() {
		if (current == null) {
			current = new JournalData();
		}
		return current;
	}

	public static void reset() {
		current = null;
	}

	private JournalData() {
		File file;
		try (InputStream in = JournalData.class.getResourceAsStream("/onepiece/journal.json")) {
			file = new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), File.class);
		} catch (Exception e) {
			OnePieceMod.LOGGER.error("Could not read onepiece/journal.json", e);
			file = new File();
		}
		tabs = file.tabs;
		structures = file.structures;

		Map<String, GuideData.Chapter> chapters = new HashMap<>();
		for (GuideData.Chapter chapter : GuideData.chapters()) {
			chapters.put(chapter.id, chapter);
		}
		// Dynamic tabs first, so their entries (fruits...) win over plain item entries.
		for (Tab tab : tabs) {
			tab.iconStack = stack(tab.icon);
			tab.lines = new ArrayList<>();
			for (String id : tab.chapters) {
				GuideData.Chapter chapter = chapters.get(id);
				if (chapter != null) {
					if (!tab.lines.isEmpty()) {
						tab.lines.add("");
					}
					tab.lines.add("# " + chapter.title);
					tab.lines.addAll(chapter.text);
				}
			}
			if (!tab.intro.isEmpty() && !tab.lines.isEmpty()) {
				tab.lines.add("");
			}
			tab.lines.addAll(tab.intro);
			tab.entries = new ArrayList<>();
			if (tab.dynamic != null && !tab.dynamic.equals("all") && !tab.dynamic.equals("stations")) {
				switch (tab.dynamic) {
					case "fruits" -> fruits(tab.entries);
					case "creatures" -> creatures(tab.entries);
					case "bosses" -> characters(tab.entries, true);
					case "characters" -> characters(tab.entries, false);
					case "structures" -> structures(tab.entries);
					default -> { }
				}
			}
		}
		for (Tab tab : tabs) {
			for (String id : tab.items) {
				Entry entry = entryFor(stack(id));
				if (entry != null && !tab.entries.contains(entry)) {
					tab.entries.add(entry);
				}
			}
			if ("stations".equals(tab.dynamic)) {
				// Everything a crafting station makes.
				for (var recipe : com.onepiecemod.crafting.StationRecipe.all().values()) {
					Entry entry = entryFor(recipe.resultStack());
					if (entry != null && !tab.entries.contains(entry)) {
						tab.entries.add(entry);
					}
				}
			}
			if ("all".equals(tab.dynamic)) {
				List<Entry> all = new ArrayList<>();
				for (Item item : BuiltInRegistries.ITEM) {
					if (BuiltInRegistries.ITEM.getKey(item).getNamespace().startsWith(OnePieceMod.MOD_ID)) {
						Entry entry = entryFor(new ItemStack(item));
						if (entry != null && !all.contains(entry)) {
							all.add(entry);
						}
					}
				}
				all.sort(Comparator.comparing(entry -> entry.title.toLowerCase(Locale.ROOT)));
				tab.entries.addAll(all);
			}
		}
	}

	/** Every entry whose name (or item id) contains the text, from every tab. */
	public List<Entry> search(String text) {
		String query = text.trim().toLowerCase(Locale.ROOT);
		List<Entry> found = new ArrayList<>();
		for (Tab tab : tabs) {
			for (Entry entry : tab.entries) {
				if (entry.search.contains(query) && !found.contains(entry)) {
					found.add(entry);
				}
			}
		}
		return found;
	}

	/** The tab an entry belongs to (the first one that lists it). */
	public Tab tabOf(Entry entry) {
		for (Tab tab : tabs) {
			if (tab.entries.contains(entry) && !"all".equals(tab.dynamic)) {
				return tab;
			}
		}
		return tabs.isEmpty() ? null : tabs.get(tabs.size() - 1);
	}

	/** The entry about an item: a fruit page, a page made from its description, or a plain one for vanilla items. */
	public Entry entryFor(ItemStack stack) {
		if (stack.isEmpty()) {
			return null;
		}
		Entry entry = byItem.get(stack.getItem());
		if (entry == null) {
			ItemStack one = stack.copyWithCount(1);
			Identifier id = BuiltInRegistries.ITEM.getKey(stack.getItem());
			entry = new Entry(one.getHoverName().getString(), one, one, id.toString());
			String description = ItemDescriptions.describe(id);
			if (description != null) {
				entry.lines.add(description);
			}
			byItem.put(stack.getItem(), entry);
		}
		return entry;
	}

	// ---- Devil Fruits ----

	private void fruits(List<Entry> into) {
		List<DevilFruit> sorted = new ArrayList<>(DevilFruits.ALL);
		sorted.sort(Comparator.comparing(DevilFruit::name));
		for (DevilFruit fruit : sorted) {
			Item item = ModItems.DEVIL_FRUITS.get(fruit.id());
			if (item == null) {
				continue;
			}
			ItemStack stack = new ItemStack(item);
			Entry entry = new Entry(fruit.name(), stack, stack, fruit.id() + " " + fruit.type().name());
			String type = fruit.type().name().charAt(0) + fruit.type().name().substring(1).toLowerCase(Locale.ROOT);
			entry.lines.add("# " + type + " fruit");
			entry.lines.add(switch (fruit.type()) {
				case LOGIA -> "Turns your body into an element. Most attacks pass right through you, unless the attacker uses Haki.";
				case ZOAN -> "Lets you turn into an animal, or a half-animal, for great strength and speed.";
				case PARAMECIA -> "Gives your body a special power, from rubber skin to strings to bubbles.";
			});
			entry.lines.add("");
			entry.lines.add("- Power key (R): " + fruit.primary());
			entry.lines.add("- Sneak + R: " + fruit.secondary());
			entry.lines.add("");
			entry.lines.add("> Eat it to gain its power. You can only hold one power at a time, and you can no longer swim.");
			byItem.put(item, entry);
			into.add(entry);
		}
	}

	// ---- Creatures ----

	private void creatures(List<Entry> into) {
		for (CreatureSpecies species : CreatureSpecies.ALL) {
			Identifier id = OnePieceMod.id(species.id());
			var type = BuiltInRegistries.ENTITY_TYPE.getOptional(id);
			String name = type.isPresent() ? type.get().getDescription().getString() : pretty(species.id());
			ItemStack egg = stack("onepiece:" + species.id() + "_spawn_egg");
			Entry entry = new Entry(name, egg.isEmpty() ? new ItemStack(Items.EGG) : egg, ItemStack.EMPTY, species.id());
			entry.lines.add("# " + switch (species.behavior()) {
				case PASSIVE -> "Harmless";
				case NEUTRAL -> "Neutral: fights back";
				case HOSTILE -> "Hostile: attacks on sight";
			});
			entry.lines.add("- Health: " + hearts(species.health()));
			if (species.fights()) {
				entry.lines.add("- Attack: " + hearts(species.damage()));
			}
			if (species.poisonSeconds() > 0) {
				entry.lines.add("- Its bite poisons you.");
			}
			if (species.fireSeconds() > 0) {
				entry.lines.add("- Its attacks set you on fire.");
			}
			if (species.swims()) {
				entry.lines.add("- Lives in the water.");
			}
			String biomes = spawnBiomes(species.id());
			if (!biomes.isEmpty()) {
				entry.lines.add("- Found in: " + biomes);
			}
			if (!species.food().isEmpty()) {
				String food = stack(species.food()).getHoverName().getString();
				entry.lines.add(species.tameable() ? "- Tame it by feeding it " + food + "." : "- Loves " + food + ".");
			}
			if (species.rideable()) {
				entry.lines.add("- Once tamed, right-click it with an empty hand to ride it.");
			}
			if (!species.harvestTool().isEmpty() && !species.harvestDrop().isEmpty()) {
				entry.lines.add("- Use " + stack(species.harvestTool()).getHoverName().getString() + " on it to get "
						+ stack(species.harvestDrop()).getHoverName().getString() + ".");
			}
			if (species.sleepsAtNight()) {
				entry.lines.add("> It sleeps at night.");
			}
			entry.cardsTitle = "Drops";
			entry.cards.addAll(RecipeIndex.get().fromSource("entity:" + id));
			if (!egg.isEmpty()) {
				byItem.put(egg.getItem(), entry);
			}
			into.add(entry);
		}
		into.sort(Comparator.comparing(entry -> entry.title));
	}

	private static String hearts(double points) {
		double hearts = points / 2.0;
		return (hearts == Math.floor(hearts) ? String.valueOf((int) hearts) : String.valueOf(hearts)) + " hearts";
	}

	/** Biome names from data/onepiece/tags/worldgen/biome/spawns/<id>.json. */
	private static String spawnBiomes(String id) {
		try (InputStream in = JournalData.class.getResourceAsStream("/data/onepiece/tags/worldgen/biome/spawns/" + id + ".json")) {
			if (in == null) {
				return "";
			}
			JsonArray values = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject().getAsJsonArray("values");
			List<String> names = new ArrayList<>();
			for (JsonElement value : values) {
				String biome = value.isJsonObject() ? value.getAsJsonObject().get("id").getAsString() : value.getAsString();
				String name = biomeName(biome);
				if (!names.contains(name)) {
					names.add(name);
				}
			}
			return String.join(", ", names);
		} catch (Exception e) {
			return "";
		}
	}

	private static String biomeName(String biome) {
		boolean tag = biome.startsWith("#");
		Identifier id = Identifier.tryParse(tag ? biome.substring(1) : biome);
		if (id == null) {
			return biome;
		}
		String key = "biome." + id.getNamespace() + "." + id.getPath();
		if (!tag) {
			String translated = I18n.get(key);
			if (!translated.equals(key)) {
				return translated;
			}
		}
		String path = id.getPath();
		path = path.substring(path.lastIndexOf('/') + 1).replace("is_", "");
		return pretty(path) + (tag ? " biomes" : "");
	}

	// ---- Bosses, quest givers and traders ----

	private static final String[] TIERS = {"East Blue", "Paradise", "Grand Line", "New World", "Emperors and Admirals"};

	private void characters(List<Entry> into, boolean bosses) {
		for (CharacterData character : CharacterData.all().values()) {
			if (character.isBossRole() != bosses) {
				continue;
			}
			ItemStack poster = stack("onepiece:wanted_poster_" + character.id);
			ItemStack card = stack("onepiece:vivre_card_" + character.id);
			ItemStack icon = bosses || card.isEmpty() ? poster : card;
			Entry entry = new Entry(character.name, icon.isEmpty() ? new ItemStack(Items.PLAYER_HEAD) : icon,
					bosses ? poster : ItemStack.EMPTY, character.id);
			String tier = TIERS[Math.max(0, Math.min(TIERS.length - 1, character.tier - 1))];
			if (bosses) {
				entry.lines.add("# Boss, tier " + character.tier + " (" + tier + ")");
				entry.lines.add("- Health: " + hearts(character.health) + "   Attack: " + hearts(character.damage));
				entry.lines.add("- Special attack: " + power(character.power));
				if (!character.hardPower.equals(character.power)) {
					entry.lines.add("- On Hard and Expert also: " + power(character.hardPower));
				}
				if (character.bounty > 0) {
					entry.lines.add("- Reward: " + Bounty.format(character.bounty) + " Berries");
				}
			} else {
				entry.lines.add("# " + (CharacterData.TRADER.equals(character.role) ? "Trader" : "Quest giver") + " (" + tier + ")");
			}
			String home = Locations.home(character.id);
			if (home != null) {
				entry.lines.add("- " + (Locations.onlyLastSeen(character.id) ? "Last seen at: " : "Lives at: ") + Locations.name(home));
			}
			if (!character.greeting.isEmpty()) {
				entry.lines.add("");
				entry.lines.add("\"" + character.greeting + "\"");
			}
			if (!character.quests.isEmpty()) {
				entry.lines.add("");
				entry.lines.add("# Quest line");
				int step = 1;
				for (CharacterData.Quest quest : character.quests) {
					entry.lines.add("- " + step++ + ". " + questText(quest));
				}
			}
			if (!character.levels.isEmpty()) {
				entry.lines.add("");
				entry.lines.add("> Trade with them to raise their level and unlock better deals, like a villager.");
			}
			if (bosses) {
				entry.lines.add("");
				entry.lines.add("> Use their Wanted Poster on a block to fight them. Win, and the poster brings them back on Hard, then Expert.");
			}
			entry.cardsTitle = bosses ? "Drops & rewards" : "Trades & rewards";
			entry.cards.addAll(RecipeIndex.get().fromSource("char:" + character.id));
			if (bosses && !poster.isEmpty()) {
				byItem.put(poster.getItem(), entry);
			} else if (!bosses && !card.isEmpty()) {
				byItem.put(card.getItem(), entry);
			}
			into.add(entry);
		}
		into.sort(Comparator.comparing(entry -> entry.title));
	}

	private static String questText(CharacterData.Quest quest) {
		CharacterData target = quest.target != null ? CharacterData.get(quest.target) : null;
		String name = target != null ? target.name : quest.target;
		return switch (quest.type == null ? "" : quest.type) {
			case "defeat" -> "Defeat " + name;
			case "talk" -> "Talk to " + name;
			case "fetch" -> "Bring " + quest.count + " " + stack(quest.item).getHoverName().getString();
			default -> "Finish the task";
		};
	}

	private static String power(String id) {
		return switch (id == null ? "" : id) {
			case "punch" -> "heavy punches";
			case "sword" -> "sword slashes";
			case "fire" -> "fire attacks";
			case "ice" -> "freezing ice";
			case "lightning" -> "lightning strikes";
			case "magma" -> "burning magma";
			case "sand" -> "drying sand";
			case "smoke" -> "smoke that pins you down";
			case "string" -> "cutting strings";
			case "darkness" -> "darkness that pulls you in";
			case "quake" -> "earthquake shockwaves";
			case "gravity" -> "crushing gravity";
			case "haki" -> "Haki blasts";
			case "poison" -> "poison";
			case "shadow" -> "shadow stealing";
			case "soul" -> "soul stealing";
			case "beast" -> "beast form";
			case "dragon" -> "dragon breath";
			case "forest" -> "grabbing roots";
			case "heal" -> "healing itself";
			case "paw" -> "paw shockwaves";
			case "petrify" -> "turning you to stone";
			case "pull" -> "pulling you close";
			case "teleport" -> "teleporting";
			case "curse" -> "curses";
			case "rocks" -> "a bit of everything";
			default -> pretty(id);
		};
	}

	// ---- Structures ----

	private void structures(List<Entry> into) {
		List<Structure> sorted = new ArrayList<>(structures);
		sorted.sort(Comparator.comparing(structure -> structure.name));
		for (Structure structure : sorted) {
			Entry entry = new Entry(structure.name, new ItemStack(structure.lair ? Items.WITHER_SKELETON_SKULL : Items.FILLED_MAP),
					ItemStack.EMPTY, structure.id + " " + structure.who);
			entry.lines.add("# " + structure.tier + (structure.lair ? " boss lair" : " location"));
			entry.lines.add("- Where: " + structure.where);
			entry.lines.add("- Who you meet: " + structure.who);
			if (!"0".equals(structure.guards)) {
				entry.lines.add("- Guards: " + structure.guards);
			}
			entry.lines.add("- Has a loot chest.");
			entry.lines.add("");
			entry.lines.add("> Find it with a Sea Chart, or a character's Vivre Card if they live there. In Creative: /locate structure onepiece:" + structure.id);
			entry.cardsTitle = "Loot";
			into.add(entry);
		}
	}

	// ---- Helpers ----

	static ItemStack stack(String id) {
		if (id == null) {
			return ItemStack.EMPTY;
		}
		return CharacterData.stack(id, 1);
	}

	private static String pretty(String name) {
		StringBuilder out = new StringBuilder();
		for (String word : name.split("[_ ]")) {
			if (!word.isEmpty()) {
				out.append(out.isEmpty() ? "" : " ").append(Character.toUpperCase(word.charAt(0))).append(word.substring(1));
			}
		}
		return out.toString();
	}
}
