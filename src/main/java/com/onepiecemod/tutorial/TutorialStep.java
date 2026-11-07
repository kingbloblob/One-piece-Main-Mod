package com.onepiecemod.tutorial;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;

/**
 * The steps of "First Voyage", the new player guide, in the order they are done.
 * The server checks them (TutorialFeature) and the player's game shows them (tutorial/client/TutorialOverlay).
 * Steps come in parts (Castaway, Set Sail, ...) so the guide reads like a short voyage.
 *
 * Text can name a key bind like {key.onepiece.quest_tree}: it shows the key the player really uses,
 * so it stays right when they rebind it in Options > Controls.
 */
public enum TutorialStep {
	// Part 1: on the starting island.
	RACE(Part.CASTAWAY, "Choose your race",
			"Pick one on the screen that opens when you first join. Every race has a perk and a drawback. Type /race to see yours."),
	JOURNAL(Part.CASTAWAY, "Open your Crafter's Journal",
			"Right-click the book you were given. Each tab explains one part of the mod and lists its items. Lost it? Type /guide."),
	KEYS(Part.CASTAWAY, "Learn your pirate keys",
			"Press Esc and click One Piece Keys in the bottom-left corner. It lists every key this mod adds: Devil Fruit, Haki, fighting styles, ships. You can change them there too."),
	HUD(Part.CASTAWAY, "Look at your HUD",
			"The bar beside your hotbar shows your bounty, Pirate Level, story goal and cooldowns. Press {key.onepiece.toggle_hud} to make it smaller or hide it."),
	QUESTS(Part.CASTAWAY, "Open your quest tree",
			"Press {key.onepiece.quest_tree} to see the whole story and every character's quest line. Locked parts show ???."),

	// Part 2: the first trip across the sea, to Foosha Village.
	BOAT(Part.SET_SAIL, "Get in your boat",
			"You washed up with a boat. Place it on the water and right-click it to climb in. W sails, A and D turn, Sneak gets out."),
	LOG_POSE(Part.SET_SAIL, "Read your Log Pose",
			"Hold the Log Pose and right-click. Its needle points to the next island, and on your starting island it points to Foosha Village."),
	FOOSHA(Part.SET_SAIL, "Find Foosha Village",
			"Sail where the Log Pose points (or right-click your Sea Chart). Foosha is a few hundred blocks away. /story lists the story goals."),
	LUFFY(Part.SET_SAIL, "Help Luffy",
			"Talk to the boy in the straw hat and bring him what he asks for. That finishes Chapter 1 and pays your first Berries."),

	// Part 3: getting stronger and finding company.
	LEVEL(Part.PIRATE, "Train to Pirate Level 1",
			"Beating hostile mobs and pirates earns Pirate XP. Once you level up, press {key.onepiece_stats.stat_tree} and spend your stat point."),
	CREW(Part.PIRATE, "Start your crew",
			"Type /crew create <name>. You are the captain now. Koby at Shells Town is waiting for you too."),
	CREWMATE(Part.PIRATE, "Recruit your first crewmate",
			"Type /crew blueprint for the Pirate Tavern plan and build it. Then use /crew hire <role> to meet 3 candidates."),

	// Part 4: a real ship.
	SHIP(Part.CAPTAIN, "Take the helm of your own ship",
			"Craft a Shipwright's Bench, make a Ship's Wheel there, and put it on any build floating in the sea, facing the front. Right-click the wheel to set sail."),

	// Part 5: the first Devil Fruit, which takes the longest.
	FRUIT(Part.DEVIL_FRUIT, "Find a Devil Fruit",
			"Fruits are rare: about 1 leaf in 2,000 drops one, Sea Kings sometimes carry one, and bosses drop theirs when beaten (Buggy the Clown is the weakest)."),
	EAT(Part.DEVIL_FRUIT, "Eat your Devil Fruit",
			"Right-click to eat it. Its power is yours forever, but you can never swim again, and a second fruit kills you. Rather sell it? /tutorial skip."),
	POWER(Part.DEVIL_FRUIT, "Use your power",
			"Press {key.onepiece.use_fruit_power} for your fruit's main move and Sneak + {key.onepiece.use_fruit_power} for the second. Each use trains your mastery.");

	/** The chapters of the guide. */
	public enum Part {
		CASTAWAY("Castaway"),
		SET_SAIL("Set Sail"),
		PIRATE("Pirate Life"),
		CAPTAIN("Captain"),
		DEVIL_FRUIT("Devil Fruit");

		public final String title;

		Part(String title) {
			this.title = title;
		}
	}

	public final Part part;
	public final String title;
	public final String hint;

	TutorialStep(Part part, String title, String hint) {
		this.part = part;
		this.title = title;
		this.hint = hint;
	}

	public static final int COUNT = values().length;

	private static final Pattern KEY = Pattern.compile("\\{(key\\.[a-z0-9_.]+)\\}");

	/** The step at this position, or null once the guide is done. */
	public static TutorialStep at(int index) {
		return index >= 0 && index < COUNT ? values()[index] : null;
	}

	/** The hint for chat: key binds become keybind text, which the player's game fills in. */
	public Component hintComponent() {
		return withKeys(hint);
	}

	/** Any text with {key.x} parts, for chat: key binds become keybind text, which the player's game fills in. */
	public static MutableComponent withKeys(String text) {
		MutableComponent out = Component.empty();
		for (Object part : split(text)) {
			out.append(part instanceof KeyName key ? Component.keybind(key.name()) : Component.literal((String) part));
		}
		return out;
	}

	/** The hint as plain text, with each key bind turned into a key name by keyName (for the on-screen panel). */
	public String hintText(Function<String, String> keyName) {
		return keysText(hint, keyName);
	}

	/** Any text with {key.x} parts as plain text, with each key bind turned into a key name by keyName. */
	public static String keysText(String text, Function<String, String> keyName) {
		StringBuilder out = new StringBuilder();
		for (Object part : split(text)) {
			out.append(part instanceof KeyName key ? keyName.apply(key.name()) : (String) part);
		}
		return out.toString();
	}

	private record KeyName(String name) {}

	private static List<Object> split(String text) {
		List<Object> parts = new ArrayList<>();
		Matcher matcher = KEY.matcher(text);
		int at = 0;
		while (matcher.find()) {
			parts.add(text.substring(at, matcher.start()));
			parts.add(new KeyName(matcher.group(1)));
			at = matcher.end();
		}
		parts.add(text.substring(at));
		return parts;
	}
}
