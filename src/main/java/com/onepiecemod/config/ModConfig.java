package com.onepiecemod.config;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import net.fabricmc.loader.api.FabricLoader;

import com.onepiecemod.OnePieceMod;

/**
 * The mod's settings file, config/onepiece.properties. Players and modpack makers can change difficulty,
 * Devil Fruit drop rates, boss strength and progression speed there, or in game from the pause menu
 * (or Mod Menu). The file is written with every setting and a comment explaining it, so it is easy to edit.
 *
 * Every setting is a number. A few are a choice of words (like difficulty), which are saved as the word.
 * Missing or broken lines fall back to the default, so an old file keeps working after an update.
 *
 * On a server, the server's file is the one that counts. In single player the game uses your own file.
 */
public final class ModConfig {
	private static final Path FILE = FabricLoader.getInstance().getConfigDir().resolve("onepiece.properties");

	/** One setting. choices is null for plain numbers, or the words for 0, 1, 2... for a choice. */
	public record Setting(String key, String category, String label, String comment, double defaultValue,
			double min, double max, double[] steps, List<String> choices, boolean needsRestart) {

		public boolean isChoice() {
			return choices != null;
		}

		public double clamp(double value) {
			if (Double.isNaN(value)) {
				return defaultValue;
			}
			return Math.max(min, Math.min(max, value));
		}

		/** How the value is shown on the settings screen and written to the file. */
		public String format(double value) {
			if (isChoice()) {
				return choices.get((int) Math.round(value));
			}
			if (value == Math.rint(value) && Math.abs(value) < 1e9) {
				return String.valueOf((long) value);
			}
			return String.format(Locale.ROOT, "%.4f", value).replaceAll("0+$", "");
		}
	}

	public static final String DIFFICULTY = "difficulty";

	public static final String SIMPLE_MODE = "simple_mode";
	public static final String LOCK_SETTINGS = "lock_settings";

	private static final List<String> DIFFICULTIES = List.of("story", "easy", "normal", "hard", "brutal");
	/** Enemy health and damage for story, easy, normal, hard, brutal. */
	private static final double[] DIFFICULTY_HEALTH = {0.5, 0.75, 1.0, 1.4, 2.0};
	private static final double[] DIFFICULTY_DAMAGE = {0.4, 0.6, 1.0, 1.4, 2.0};
	private static final List<String> OFF_ON = List.of("off", "on");

	private static final double[] MULTIPLIER_STEPS = {0.1, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 5.0, 10.0};
	private static final double[] SPAWN_STEPS = {0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0};

	private static final Map<String, Setting> SETTINGS = new LinkedHashMap<>();
	private static final Map<String, Double> VALUES = new ConcurrentHashMap<>(); // The settings screen and the server thread both use it.

	static {
		add(new Setting(DIFFICULTY, "Difficulty", "Difficulty",
				"How tough enemies are: story, easy, normal, hard or brutal. Changes the health and damage of bosses,\n"
						+ "creatures, pirates and Marines, on top of the multipliers below.\n"
						+ "story = half health, 40% damage (for just enjoying the adventure). easy = 75% health, 60% damage.",
				2, 0, 4, new double[] {0, 1, 2, 3, 4}, DIFFICULTIES, false));

		multiplier("boss_health", "Difficulty", "Boss health", "Health of story bosses. 2 = twice as much.");
		multiplier("boss_damage", "Difficulty", "Boss damage", "Damage story bosses deal.");
		multiplier("creature_health", "Difficulty", "Creature health", "Health of sea kings and other creatures. Needs a restart.", true);
		multiplier("creature_damage", "Difficulty", "Creature damage", "Damage creatures deal. Needs a restart.", true);
		multiplier("npc_health", "Difficulty", "Pirate/Marine health", "Health of pirate and Marine NPCs, applied when they spawn.");
		multiplier("npc_damage", "Difficulty", "Pirate/Marine damage", "Damage pirate and Marine NPCs deal, applied when they spawn.");
		add(new Setting("new_world_strength", "Difficulty", "New World enemies",
				"How much tougher enemies get past the New World line (3500 blocks from spawn), in the deep New World (6000+)\n"
						+ "and in the End. 1 = normal (+50% health in the New World, +100% in the deep New World), 0 = off.",
				1, 0, 3, SPAWN_STEPS, null, false));

		add(new Setting(SIMPLE_MODE, "Easy Play", "Simple mode",
				"For players new to the mod. on: the Navy, bounty hunters and Marine hunts leave you alone until you beat\n"
						+ "your first story boss and then come half as often, dying never costs Devil Fruit mastery,\n"
						+ "move cooldowns are 25% shorter, and Haki and Pirate Level XP come 25% faster.",
				0, 0, 1, new double[] {0, 1}, OFF_ON, false));
		add(new Setting("power_cooldowns", "Easy Play", "Move cooldowns",
				"How long Devil Fruit moves and fighting style techniques take to recharge. 0.5 = half as long. 1 = normal.",
				1, 0.1, 5, new double[] {0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0}, null, false));
		add(new Setting("death_mastery_loss", "Easy Play", "Mastery lost on death",
				"Share of your Devil Fruit mastery you lose when you die (before you awaken). 0.1 = 10%. 0 = none.",
				0.1, 0, 1, new double[] {0, 0.05, 0.1, 0.2, 0.25, 0.5}, null, false));
		add(new Setting("safe_until_bosses", "Easy Play", "Navy waits for",
				"The Navy, bounty hunters and Marine hunts leave you alone until you've beaten this many story bosses.\n"
						+ "0 = they can come as soon as you have a bounty. Simple mode makes this at least 1.",
				0, 0, 20, new double[] {0, 1, 2, 3, 5, 8}, null, false));

		add(new Setting("fruit_leaf_drop_chance", "Devil Fruits", "Fruit from leaves",
				"Chance that a broken leaves block drops a random Devil Fruit. 0.0005 = 1 in 2,000. 0 = never.\n"
						+ "Takes effect when a world loads (or after /reload).",
				0.0005, 0, 1, new double[] {0, 0.0001, 0.00025, 0.0005, 0.001, 0.0025, 0.005, 0.01, 0.05}, null, false));
		add(new Setting("awakening_mastery", "Devil Fruits", "Mastery to awaken",
				"Fruit mastery needed before you can awaken your Devil Fruit.",
				1000, 1, 100000, new double[] {100, 250, 500, 750, 1000, 1500, 2000, 3000, 5000}, null, false));

		multiplier("boss_berries", "Rewards", "Boss Berries", "Berries dropped by bosses.");
		add(new Setting("rematch_berry_share", "Rewards", "Rematch Berries",
				"Share of the Berries you get for beating a boss again at a difficulty you already won. 0.15 = 15%.",
				0.15, 0, 1, new double[] {0, 0.05, 0.1, 0.15, 0.25, 0.5, 0.75, 1.0}, null, false));
		multiplier("bounty_gain", "Rewards", "Bounty gain", "How fast your bounty rises.");
		multiplier("haki_xp", "Rewards", "Haki XP", "How fast Observation, Armament and Conqueror's Haki level up.");
		multiplier("pirate_xp", "Rewards", "Pirate Level XP", "How fast your Pirate Level (stat tree, K key) rises.");

		add(new Setting("bounty_hunter_rate", "Raids", "Bounty hunters",
				"How often bounty hunters come after wanted pirates. 0 = never.",
				1, 0, 10, SPAWN_STEPS, null, false));
		add(new Setting("navy_raid_rate", "Raids", "Navy raids",
				"How often the Navy raids wanted pirates. 0 = never.",
				1, 0, 10, SPAWN_STEPS, null, false));
		add(new Setting("marine_hunt_rate", "Raids", "Marine hunts",
				"How often Marine squads hunt wanted pirates. 0 = never.",
				1, 0, 10, SPAWN_STEPS, null, false));

		add(new Setting("sea_king_rate", "World", "Sea Kings",
				"How often Sea Kings come up around ships at sea. 0 = never (handy with other sea monster mods).",
				1, 0, 10, SPAWN_STEPS, null, false));
		add(new Setting("log_pose_record_seconds", "World", "Log Pose record time",
				"Seconds you must stay on an island before your Log Pose records it and points to the next one.",
				45, 5, 600, new double[] {5, 10, 15, 30, 45, 60, 90, 120, 180}, null, false));

		add(new Setting("crew_fame_share", "Multiplayer", "Crew fame share",
				"When a player's bounty rises, every crewmate (player) within 64 blocks gets this share of it too:\n"
						+ "the Marines blame the whole crew. 0.15 = 15%. 0 = off.",
				0.15, 0, 1, new double[] {0, 0.05, 0.1, 0.15, 0.25, 0.5}, null, false));
		add(new Setting("player_kill_bounty", "Multiplayer", "Defeat a player",
				"Share of a rival player's bounty added to yours when you defeat them (once per rival every 30 minutes).\n"
						+ "Doubled during a crew sea battle. 0.1 = 10%. 0 = off.",
				0.1, 0, 1, new double[] {0, 0.05, 0.1, 0.2, 0.3, 0.5}, null, false));
		add(new Setting("open_sea_pvp", "Multiplayer", "Open-sea ship PvP",
				"off: players can only cannon another crew's ship during a sea battle they both agreed to (/crew challenge).\n"
						+ "on: any crew's ship can be attacked any time (allied and own-crew ships are always safe).",
				0, 0, 1, new double[] {0, 1}, OFF_ON, false));
		add(new Setting(LOCK_SETTINGS, "Multiplayer", "Lock settings",
				"For modpacks and servers. on: the in-game One Piece Settings screen shows these settings but can't change them,\n"
						+ "so players keep the pack's balance. Change them here in the file (or with /onepiece_config) instead.",
				0, 0, 1, new double[] {0, 1}, OFF_ON, false));

		for (Setting setting : SETTINGS.values()) {
			VALUES.put(setting.key(), setting.defaultValue());
		}
	}

	private ModConfig() {
	}

	private static void multiplier(String key, String category, String label, String comment) {
		multiplier(key, category, label, comment, false);
	}

	private static void multiplier(String key, String category, String label, String comment, boolean restart) {
		add(new Setting(key, category, label, comment + " 1 = normal.", 1, 0.01, 100, MULTIPLIER_STEPS, null, restart));
	}

	private static void add(Setting setting) {
		SETTINGS.put(setting.key(), setting);
	}

	// ---- Values the rest of the mod reads ----

	public static double get(String key) {
		Double value = VALUES.get(key);
		return value != null ? value : SETTINGS.get(key).defaultValue();
	}

	private static int difficultyIndex() {
		return (int) Math.round(get(DIFFICULTY));
	}

	public static double bossHealth() {
		return get("boss_health") * DIFFICULTY_HEALTH[difficultyIndex()];
	}

	public static double bossDamage() {
		return get("boss_damage") * DIFFICULTY_DAMAGE[difficultyIndex()];
	}

	public static double creatureHealth() {
		return get("creature_health") * DIFFICULTY_HEALTH[difficultyIndex()];
	}

	public static double creatureDamage() {
		return get("creature_damage") * DIFFICULTY_DAMAGE[difficultyIndex()];
	}

	public static double npcHealth() {
		return get("npc_health") * DIFFICULTY_HEALTH[difficultyIndex()];
	}

	public static double npcDamage() {
		return get("npc_damage") * DIFFICULTY_DAMAGE[difficultyIndex()];
	}

	public static boolean simpleMode() {
		return get(SIMPLE_MODE) >= 0.5;
	}

	public static boolean locked() {
		return get(LOCK_SETTINGS) >= 0.5;
	}

	/** Multiplier for Devil Fruit and fighting style cooldowns. */
	public static double powerCooldowns() {
		return get("power_cooldowns") * (simpleMode() ? 0.75 : 1.0);
	}

	/** Share of fruit mastery lost on death. */
	public static double deathMasteryLoss() {
		return simpleMode() ? 0 : get("death_mastery_loss");
	}

	/** Story bosses a player must beat before the Navy, bounty hunters and Marine hunts come for them. */
	public static int safeUntilBosses() {
		return Math.max((int) Math.round(get("safe_until_bosses")), simpleMode() ? 1 : 0);
	}

	/** Simple mode halves how often the Navy and hunters come. */
	private static float raidScale() {
		return simpleMode() ? 0.5f : 1.0f;
	}

	public static double newWorldStrength() {
		return get("new_world_strength");
	}

	public static float fruitLeafChance() {
		return (float) get("fruit_leaf_drop_chance");
	}

	public static int awakeningMastery() {
		return (int) Math.round(get("awakening_mastery"));
	}

	public static double bossBerries() {
		return get("boss_berries");
	}

	public static float rematchBerryShare() {
		return (float) get("rematch_berry_share");
	}

	public static double bountyGain() {
		return get("bounty_gain");
	}

	public static double hakiXp() {
		return get("haki_xp") * (simpleMode() ? 1.25 : 1.0);
	}

	public static double pirateXp() {
		return get("pirate_xp") * (simpleMode() ? 1.25 : 1.0);
	}

	public static float bountyHunterRate() {
		return (float) get("bounty_hunter_rate") * raidScale();
	}

	public static float navyRaidRate() {
		return (float) get("navy_raid_rate") * raidScale();
	}

	public static float marineHuntRate() {
		return (float) get("marine_hunt_rate") * raidScale();
	}

	public static float seaKingRate() {
		return (float) get("sea_king_rate");
	}

	public static double crewFameShare() {
		return get("crew_fame_share");
	}

	public static double playerKillBounty() {
		return get("player_kill_bounty");
	}

	public static boolean openSeaPvp() {
		return get("open_sea_pvp") >= 0.5;
	}

	public static int logPoseRecordSeconds() {
		return (int) Math.round(get("log_pose_record_seconds"));
	}

	/** Scales a whole-number reward, keeping at least 1 when the original was positive. */
	public static int scale(int amount, double multiplier) {
		if (amount <= 0 || multiplier == 1.0) {
			return amount;
		}
		return (int) Math.max(1, Math.min(Integer.MAX_VALUE, Math.round(amount * multiplier)));
	}

	public static long scale(long amount, double multiplier) {
		if (amount <= 0 || multiplier == 1.0) {
			return amount;
		}
		return Math.max(1, Math.round(amount * multiplier));
	}

	// ---- Presets: one click sets the "how easy is it" settings together ----

	/** A named bundle of settings. Only the keys listed change; everything else is kept. */
	public record Preset(String id, String label, String help, Map<String, String> values) {}

	private static final List<Preset> PRESETS = List.of(
			new Preset("story", "Story", "The easiest way to play: story difficulty and Simple mode, half-length cooldowns, and the Navy waits until you've beaten 2 bosses.",
					presetValues("story", "on", "0.5", "0", "2")),
			new Preset("simple", "Simple", "For players new to the mod: easy difficulty and Simple mode.",
					presetValues("easy", "on", "1", "0", "1")),
			new Preset("standard", "Standard", "The mod as designed: normal difficulty, Simple mode off.",
					presetValues("normal", "off", "1", "0.1", "0")),
			new Preset("challenge", "Challenge", "For veterans: hard difficulty, longer cooldowns, and dying costs a fifth of your mastery.",
					presetValues("hard", "off", "1.25", "0.2", "0")));

	private static Map<String, String> presetValues(String difficulty, String simple, String cooldowns, String deathLoss, String safeBosses) {
		Map<String, String> values = new LinkedHashMap<>();
		values.put(DIFFICULTY, difficulty);
		values.put(SIMPLE_MODE, simple);
		values.put("power_cooldowns", cooldowns);
		values.put("death_mastery_loss", deathLoss);
		values.put("safe_until_bosses", safeBosses);
		return values;
	}

	public static List<Preset> presets() {
		return PRESETS;
	}

	public static Preset preset(String id) {
		for (Preset preset : PRESETS) {
			if (preset.id().equalsIgnoreCase(id)) {
				return preset;
			}
		}
		return null;
	}

	public static void apply(Preset preset) {
		preset.values().forEach(ModConfig::setFromText);
	}

	/** The preset whose values all match the current settings, or null. */
	public static Preset currentPreset() {
		for (Preset preset : PRESETS) {
			boolean all = true;
			for (Map.Entry<String, String> entry : preset.values().entrySet()) {
				Setting setting = SETTINGS.get(entry.getKey());
				if (!setting.format(get(setting.key())).equals(setting.format(parse(setting, entry.getValue())))) {
					all = false;
					break;
				}
			}
			if (all) {
				return preset;
			}
		}
		return null;
	}

	private static double parse(Setting setting, String text) {
		return setting.isChoice() ? setting.choices().indexOf(text) : Double.parseDouble(text);
	}

	// ---- For the settings screen ----

	public static Iterable<Setting> settings() {
		return SETTINGS.values();
	}

	/** The setting with this key, or null. */
	public static Setting setting(String key) {
		return SETTINGS.get(key.toLowerCase(Locale.ROOT));
	}

	/**
	 * Sets a setting from text the way the file is read (a number, or a word for choices).
	 * Returns null when it worked, or what's wrong.
	 */
	public static String setFromText(String key, String text) {
		Setting setting = setting(key);
		if (setting == null) {
			return "There's no setting called '" + key + "'.";
		}
		text = text.strip().toLowerCase(Locale.ROOT);
		if (setting.isChoice()) {
			int index = setting.choices().indexOf(text);
			if (index < 0) {
				return "'" + setting.key() + "' should be one of " + String.join(", ", setting.choices()) + ".";
			}
			VALUES.put(setting.key(), (double) index);
			return null;
		}
		try {
			VALUES.put(setting.key(), setting.clamp(Double.parseDouble(text)));
			return null;
		} catch (NumberFormatException e) {
			return "'" + setting.key() + "' should be a number.";
		}
	}

	public static void set(String key, double value) {
		Setting setting = SETTINGS.get(key);
		if (setting != null) {
			VALUES.put(key, setting.clamp(value));
		}
	}

	public static void resetAll() {
		for (Setting setting : SETTINGS.values()) {
			VALUES.put(setting.key(), setting.defaultValue());
		}
	}

	// ---- The file ----

	/** Reads the file, then writes it back so new settings and comments show up. Called first thing at startup. */
	public static void load() {
		resetAll();
		if (Files.exists(FILE)) {
			try {
				for (String line : Files.readAllLines(FILE, StandardCharsets.UTF_8)) {
					readLine(line);
				}
			} catch (IOException e) {
				OnePieceMod.LOGGER.warn("Couldn't read {}, using default settings", FILE, e);
			}
		}
		save();
	}

	private static void readLine(String line) {
		line = line.strip();
		int equals = line.indexOf('=');
		if (line.isEmpty() || line.startsWith("#") || equals < 0) {
			return;
		}
		String key = line.substring(0, equals).strip().toLowerCase(Locale.ROOT);
		String text = line.substring(equals + 1).strip().toLowerCase(Locale.ROOT);
		Setting setting = SETTINGS.get(key);
		if (setting == null) {
			OnePieceMod.LOGGER.warn("Unknown setting '{}' in {}", key, FILE.getFileName());
			return;
		}
		if (setting.isChoice()) {
			int index = setting.choices().indexOf(text);
			if (index >= 0) {
				VALUES.put(key, (double) index);
			} else {
				OnePieceMod.LOGGER.warn("Setting '{}' should be one of {}, not '{}'", key, setting.choices(), text);
			}
			return;
		}
		try {
			VALUES.put(key, setting.clamp(Double.parseDouble(text)));
		} catch (NumberFormatException e) {
			OnePieceMod.LOGGER.warn("Setting '{}' should be a number, not '{}'", key, text);
		}
	}

	public static void save() {
		StringBuilder out = new StringBuilder();
		out.append("# One Piece Mod settings.\n");
		out.append("# Change a value after the = sign and restart the game (or open the world again).\n");
		out.append("# You can also change these in game: pause menu > One Piece Settings, or with Mod Menu.\n");
		out.append("# On a server, the server's copy of this file is the one that counts.\n");
		out.append("# Delete a line (or the whole file) to get the default back.\n");
		out.append("# Presets (story, simple, standard, challenge) set the Easy Play settings together: /onepiece_config preset <name>.\n");
		out.append("# Modpack makers: ship this file in your pack's config folder, and set lock_settings=on to stop players changing it.\n");
		String category = "";
		for (Setting setting : SETTINGS.values()) {
			if (!setting.category().equals(category)) {
				category = setting.category();
				out.append("\n# ===== ").append(category).append(" =====\n");
			}
			out.append('\n');
			for (String comment : setting.comment().split("\n")) {
				out.append("# ").append(comment).append('\n');
			}
			out.append("# Default: ").append(setting.format(setting.defaultValue())).append('\n');
			out.append(setting.key()).append('=').append(setting.format(get(setting.key()))).append('\n');
		}
		try {
			Files.createDirectories(FILE.getParent());
			Files.writeString(FILE, out.toString(), StandardCharsets.UTF_8);
		} catch (IOException e) {
			OnePieceMod.LOGGER.warn("Couldn't write {}", FILE, e);
		}
	}
}
