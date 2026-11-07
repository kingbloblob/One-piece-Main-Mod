package com.onepiecemod.character;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

import com.google.gson.Gson;

import com.onepiecemod.OnePieceMod;

/**
 * How each boss fight plays out, read from onepiece/boss_fights.json:
 * which NPC kit the boss calls as its crew, its phase 3 signature move, what it shouts at 66% and 33% health,
 * and the monster form it turns into at phase 2. Titans also have phase mechanics, a phase 4 line and an ultimate.
 */
public class BossFightData {
	public String crew = "";
	public String signature = "ground_wave";
	public String phase2 = "";
	public String phase3 = "";
	/** The monster form the boss turns into at phase 2 (drawn by character.client.BossForms), or "" for none. */
	public String form = "";
	/** A second monster form the boss turns into at phase 3 (Imu's beast form), or "" to stay in the first. */
	public String form3 = "";
	/** Titans only (Emperors and Admirals, see TitanFight): the phase 2 and phase 3 mechanics. Empty = a normal 3-phase boss. */
	public java.util.List<String> mechanics = java.util.List.of();
	/** Titans: what the boss shouts at 12% health (phase 4), and its ultimate: mechanics joined by "+", fired big. */
	public String phase4 = "";
	public String ultimate = "";
	public String ultimateName = "";
	/**
	 * A beast the boss unleashes at phase 2, fighting beside it (a creature id from creature/CreatureSpecies, like
	 * "cerberus" for Shamrock's sword). companionName names it, companionHealth/companionDamage/companionScale make it
	 * boss-sized. It leaves with the crew when the fight ends.
	 */
	public String companion = "";
	public String companionName = "";
	public String companionLine = "";
	public double companionHealth = 200;
	public double companionDamage = 12;
	public double companionScale = 2.0;

	private static final BossFightData DEFAULT = new BossFightData();
	private static Map<String, BossFightData> bosses;

	private static class FileData {
		Map<String, BossFightData> bosses = new HashMap<>();
	}

	public static BossFightData get(String characterId) {
		if (bosses == null) {
			load();
		}
		return bosses.getOrDefault(characterId, DEFAULT);
	}

	private static void load() {
		bosses = new HashMap<>();
		try (InputStream in = BossFightData.class.getResourceAsStream("/onepiece/boss_fights.json")) {
			if (in == null) {
				return;
			}
			FileData data = new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), FileData.class);
			if (data != null && data.bosses != null) {
				bosses.putAll(data.bosses);
			}
		} catch (Exception e) {
			OnePieceMod.LOGGER.error("Could not read onepiece/boss_fights.json", e);
		}
	}
}
