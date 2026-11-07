package com.onepiecemod.questlog.client;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import net.fabricmc.loader.api.FabricLoader;

import com.onepiecemod.OnePieceMod;

/**
 * Settings that only change what you see, saved on this computer in config/onepiece-client.properties.
 * They work on any world or server. Modpack makers can ship this file to turn off panels that clash
 * with other mods (minimaps, quest mods, JEI and so on).
 *
 * Each setting is a choice of words; the first word is the default. Change them in game under
 * One Piece Settings > Screen, or edit the file.
 */
public final class ClientConfig {
	private static final Path FILE = FabricLoader.getInstance().getConfigDir().resolve("onepiece-client.properties");

	/** One setting: its key, label, help text and choices (the first one is the default). */
	public record Option(String key, String label, String help, List<String> choices) {
	}

	private static final Map<String, Option> OPTIONS = new LinkedHashMap<>();
	private static final Map<String, String> VALUES = new LinkedHashMap<>();

	public static final String NAV_BAR = option("navigation_bar", "Compass bar",
			"The compass at the top of the screen with your sea and Log Pose needle. always: always shown. "
					+ "log_pose: only while you carry a Log Pose. off: hidden.",
			"always", "log_pose", "off");
	public static final String NAV_POSITION = option("navigation_position", "Compass bar place",
			"Where the compass bar sits. top_center moves down under boss bars. Pick a corner if a minimap mod uses the top.",
			"top_center", "top_left", "top_right");
	public static final String NAV_SIZE = option("navigation_size", "Compass bar size",
			"How big the compass bar is. small is the default; large is the old, bigger bar.",
			"small", "tiny", "medium", "large");
	public static final String COORDINATES = option("show_coordinates", "Coordinates",
			"Show your X / Z under the compass.", "off", "on");
	public static final String QUEST_TRACKER = option("quest_tracker", "Tracked quest",
			"Show the quest you track in the journal (O key) under the compass.", "on", "off");
	public static final String INVENTORY_QUESTS = option("inventory_quest_panel", "Quest panel in inventory",
			"The quest tree panel left of the inventory. Turn it off if a quest or recipe mod uses that space.", "on", "off");
	public static final String QUEST_MARKERS = option("quest_markers", "Quest markers",
			"The ! and ? over characters who have a quest for you.", "on", "off");

	public static final String CUTSCENES = option("cutscenes", "Cutscenes",
			"Boss intros (the first time you meet a boss) and story flashbacks. Enter skips one. "
					+ "bosses_only / flashbacks_only keep just one kind.", "on", "bosses_only", "flashbacks_only", "off");
	public static final String CUTSCENE_CAMERA = option("cutscene_camera", "Cutscene camera",
			"During a boss intro, gently turn your view toward the boss.", "on", "off");

	private ClientConfig() {
	}

	private static String option(String key, String label, String help, String... choices) {
		OPTIONS.put(key, new Option(key, label, help, List.of(choices)));
		VALUES.put(key, choices[0]);
		return key;
	}

	public static Iterable<Option> options() {
		return OPTIONS.values();
	}

	public static String get(String key) {
		return VALUES.get(key);
	}

	public static boolean is(String key, String value) {
		return value.equals(VALUES.get(key));
	}

	/** Steps a setting to its next (or previous) choice and saves the file. */
	public static void cycle(String key, boolean back) {
		List<String> choices = OPTIONS.get(key).choices();
		int index = choices.indexOf(VALUES.get(key));
		index = Math.floorMod(index + (back ? -1 : 1), choices.size());
		VALUES.put(key, choices.get(index));
		save();
	}

	public static void reset() {
		for (Option option : OPTIONS.values()) {
			VALUES.put(option.key(), option.choices().get(0));
		}
		save();
	}

	// ---- Shortcuts the rest of the mod reads ----

	public static boolean inventoryQuestPanel() {
		return is(INVENTORY_QUESTS, "on");
	}

	/** How much to scale the compass bar by (on top of the automatic GUI-scale shrink). */
	public static float navigationScale() {
		return switch (get(NAV_SIZE)) {
			case "tiny" -> 0.5f;
			case "medium" -> 0.85f;
			case "large" -> 1f;
			default -> 0.7f;
		};
	}

	public static boolean questMarkers() {
		return is(QUEST_MARKERS, "on");
	}

	// ---- The file ----

	/** Reads the file, then writes it back so new settings show up. Unknown or broken lines are ignored. */
	public static void load() {
		if (Files.exists(FILE)) {
			try {
				for (String line : Files.readAllLines(FILE, StandardCharsets.UTF_8)) {
					line = line.strip();
					int equals = line.indexOf('=');
					if (line.isEmpty() || line.startsWith("#") || equals < 0) {
						continue;
					}
					String key = line.substring(0, equals).strip().toLowerCase(Locale.ROOT);
					String value = line.substring(equals + 1).strip().toLowerCase(Locale.ROOT);
					Option option = OPTIONS.get(key);
					if (option != null && option.choices().contains(value)) {
						VALUES.put(key, value);
					} else {
						OnePieceMod.LOGGER.warn("Ignoring '{}' in {}", line, FILE.getFileName());
					}
				}
			} catch (Exception e) {
				OnePieceMod.LOGGER.warn("Couldn't read {}, using the defaults", FILE, e);
			}
		}
		save();
	}

	private static void save() {
		StringBuilder out = new StringBuilder();
		out.append("# One Piece Mod screen settings (this computer only, works on any server).\n");
		out.append("# The first choice listed is the default. Also in game: One Piece Settings > Screen.\n");
		for (Option option : OPTIONS.values()) {
			out.append("\n# ").append(option.help()).append('\n');
			out.append("# Choices: ").append(String.join(", ", option.choices())).append('\n');
			out.append(option.key()).append('=').append(VALUES.get(option.key())).append('\n');
		}
		try {
			Files.createDirectories(FILE.getParent());
			Files.writeString(FILE, out.toString(), StandardCharsets.UTF_8);
		} catch (Exception e) {
			OnePieceMod.LOGGER.warn("Couldn't write {}", FILE, e);
		}
	}
}
