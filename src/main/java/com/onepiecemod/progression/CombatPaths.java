package com.onepiecemod.progression;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import com.mojang.serialization.Codec;

import net.minecraft.world.entity.player.Player;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.character.CharacterAttachments;
import com.onepiecemod.haki.HakiAttachments;
import com.onepiecemod.haki.HakiData;
import com.onepiecemod.style.FightingStyle;
import com.onepiecemod.style.StyleMastery;
import com.onepiecemod.style.Technique;

/**
 * Branching upgrades ("paths") for Haki and the fighting styles.
 *
 * Every Haki and every fighting style has tiers. At each tier you pick ONE of two upgrades (A or B) from a trainer,
 * so two players with the same Haki level can fight very differently. You can switch a tier later by paying again.
 *
 * - Observation and Armament: 3 tiers, open at Haki level 2, 4 and 5. Tier 3 also needs a boss (Katakuri / Kaido).
 * - Conqueror's: 2 tiers, open at Conqueror's level 2 and 4.
 * - Each fighting style: 3 tiers, open at style mastery 3, 6 and 9. Tier 3 also needs the style's final-move boss.
 *
 * Trainers: Rayleigh (all Haki), Boa Hancock (Observation and Armament), Shanks (Conqueror's and every tier 3).
 * A style's paths are taught by that style's master.
 *
 * The effects themselves live where the power already works: HakiPowers, StyleMoves and StyleMastery ask has().
 */
public final class CombatPaths {
	private CombatPaths() {
	}

	/** Chosen paths: "haki.observation.1" -> "a", "style.santoryu.3" -> "b". Saved, kept on death. */
	public static final AttachmentType<Map<String, String>> PATHS = AttachmentRegistry.create(
			OnePieceMod.id("combat_paths"),
			builder -> builder
					.persistent(Codec.unboundedMap(Codec.STRING, Codec.STRING))
					.copyOnDeath()
	);

	/** One upgrade you can pick. */
	public record Choice(String name, String effect) {
	}

	/** One tier: what opens it, what it costs, and the two upgrades to pick between. */
	public record Tier(int number, int levelNeeded, int berries, String bossNeeded, Choice a, Choice b) {
		public Choice choice(String letter) {
			return "a".equals(letter) ? a : b;
		}
	}

	// ---- Haki ----

	public enum Haki {
		OBSERVATION("observation", "Observation Haki", List.of(
				new Tier(1, 2, 40, null,
						new Choice("Wide Sense", "Sense creatures 50% farther away."),
						new Choice("Battle Instinct", "+6% chance to dodge attacks.")),
				new Tier(2, 4, 120, null,
						new Choice("Counter", "After a dodge you get Strength II for 3 seconds: hit back hard."),
						new Choice("Swift Reflexes", "After a dodge you get Speed II for 3 seconds and heal a little.")),
				new Tier(3, 5, 300, "katakuri",
						new Choice("Clear Future", "Future Sight recharges every 5 seconds instead of 8."),
						new Choice("Foresight Strike", "When Future Sight dodges a hit, you strike the attacker back (8 damage).")))),
		ARMAMENT("armament", "Armament Haki", List.of(
				new Tier(1, 2, 40, null,
						new Choice("Iron Body", "+3 armor while Armament is on."),
						new Choice("Hardened Fists", "+2 punch damage while Armament is on and your main hand is free.")),
				new Tier(2, 4, 120, null,
						new Choice("Blade Coating", "+2 sword damage while Armament is on."),
						new Choice("Efficient Will", "Armament costs half the hunger and holds until you're starving.")),
				new Tier(3, 5, 300, "kaido",
						new Choice("Ryou Burst", "Advanced Armament's inner blow hits for 40% instead of 25%."),
						new Choice("Emission", "Advanced Armament's blow bursts out and hits up to 2 enemies behind your target.")))),
		CONQUEROR("conqueror", "Conqueror's Haki", List.of(
				new Tier(1, 2, 80, null,
						new Choice("Overwhelming Will", "Wider wave (+4 blocks) and tougher mobs faint."),
						new Choice("Kingly Presence", "Conqueror's recharges 25% faster.")),
				new Tier(2, 4, 250, null,
						new Choice("Crown of Will", "Even bosses buckle: Slowness IV and Weakness II for 4 seconds."),
						new Choice("Rally the Crew", "Your crew, allies and pets nearby get Strength and Resistance for 10 seconds."))));

		private final String id;
		private final String title;
		private final List<Tier> tiers;

		Haki(String id, String title, List<Tier> tiers) {
			this.id = id;
			this.title = title;
			this.tiers = tiers;
		}

		public String id() {
			return id;
		}

		public String title() {
			return title;
		}

		public List<Tier> tiers() {
			return tiers;
		}

		public String key(int tier) {
			return "haki." + id + "." + tier;
		}

		/** The player's current level in this Haki. */
		public int level(Player player) {
			HakiData haki = HakiAttachments.get(player);
			return switch (this) {
				case OBSERVATION -> haki.observationLevel();
				case ARMAMENT -> haki.armamentLevel();
				case CONQUEROR -> haki.conquerorLevel();
			};
		}

		public static Haki byId(String id) {
			for (Haki haki : values()) {
				if (haki.id.equals(id)) {
					return haki;
				}
			}
			return null;
		}
	}

	// ---- Fighting styles ----

	/** Style tiers open at these mastery levels and cost these Berries. */
	public static final int[] STYLE_MASTERY = {3, 6, 9};
	public static final int[] STYLE_BERRIES = {30, 100, 250};

	/** What each style tier's A and B do (the same for every style, the names change per style). */
	public static final String[][] STYLE_EFFECTS = {
			{"Techniques deal 15% more damage.", "Techniques recharge 15% faster."},
			{"Techniques deal 35% more damage to enemies below 40% health.", "Landing a technique cuts its cooldown by a third."},
			{"Using a technique gives you Resistance I for 4 seconds.", "Technique hits heal you for 15% of the damage dealt."},
	};

	/** Each style's names for its six upgrades: tier 1 A, tier 1 B, tier 2 A, tier 2 B, tier 3 A, tier 3 B. */
	private static String[] styleNames(FightingStyle style) {
		return switch (style) {
			case SANTORYU -> new String[] {"Demon's Weight", "Swift Blades", "Lion's Finish", "Endless Slashes", "Asura's Resolve", "Hungry Steel"};
			case BLACK_LEG -> new String[] {"Mutton Shot Power", "Quick Feet", "Final Course", "Tempo Kicks", "Iron Chef", "Chef's Appetite"};
			case FISHMAN_KARATE -> new String[] {"Deep Sea Force", "Flowing Water", "Ocean Current Crush", "Rising Tide", "Shark Skin", "Healing Tide"};
			case ROKUSHIKI -> new String[] {"Shigan Mastery", "Soru Speed", "Killing Strike", "Six Powers Flow", "Tekkai Body", "Life Return"};
			case RYUSOKEN -> new String[] {"Dragon's Grip", "Talon Rush", "Breaking Point", "Claw Chain", "Dragon Scales", "Dragon's Breath"};
			case NITORYU -> new String[] {"Oden's Strength", "Twin Rhythm", "Toh Toh Finish", "Wild Momentum", "Boiling Will", "Kozuki Spirit"};
			case KITSUNEBI -> new String[] {"Blazing Edge", "Fox's Step", "Fire Cutter", "Spreading Flame", "Flame Armor", "Ember Heart"};
			case SOUL_FENCING -> new String[] {"Frozen Blade", "Light Feet", "Requiem", "Song of the Dead", "Bone Body", "Soul Feast"};
			case FIST_OF_LOVE -> new String[] {"Hero's Fist", "Fast Knuckles", "Galaxy Impact", "Brawl Rhythm", "Grit Your Teeth", "Old Man's Stamina"};
			case SOGEKING -> new String[] {"Heavy Rounds", "Quick Draw", "Sniper's Mark", "Reload Trick", "Brave Warrior", "Island of Courage"};
		};
	}

	public static String styleKey(FightingStyle style, int tier) {
		return "style." + style.id() + "." + tier;
	}

	public static List<Tier> styleTiers(FightingStyle style) {
		String[] names = styleNames(style);
		Technique last = null;
		for (Technique technique : style.techniques()) {
			if (technique.unlockBoss() != null) {
				last = technique;
			}
		}
		String finalBoss = last == null ? null : last.unlockBoss();
		return List.of(
				styleTier(1, names, null),
				styleTier(2, names, null),
				styleTier(3, names, finalBoss));
	}

	private static Tier styleTier(int number, String[] names, String boss) {
		int i = number - 1;
		return new Tier(number, STYLE_MASTERY[i], STYLE_BERRIES[i], boss,
				new Choice(names[i * 2], STYLE_EFFECTS[i][0]),
				new Choice(names[i * 2 + 1], STYLE_EFFECTS[i][1]));
	}

	// ---- Reading and writing the choices ----

	/** "a", "b" or null if nothing picked for this key. */
	public static String chosen(Player player, String key) {
		Map<String, String> all = player.getAttached(PATHS);
		return all == null ? null : all.get(key);
	}

	public static boolean has(Player player, Haki haki, int tier, String letter) {
		return letter.equals(chosen(player, haki.key(tier)));
	}

	public static boolean has(Player player, FightingStyle style, int tier, String letter) {
		return style != null && letter.equals(chosen(player, styleKey(style, tier)));
	}

	public static void set(Player player, String key, String letter) {
		Map<String, String> all = new HashMap<>(player.getAttachedOrElse(PATHS, Map.<String, String>of()));
		all.put(key, letter);
		player.setAttached(PATHS, all);
	}

	/** How many upgrades this player has picked in total (for advancements and the stats line). */
	public static int count(Player player) {
		return player.getAttachedOrElse(PATHS, Map.<String, String>of()).size();
	}

	static boolean bossBeaten(Player player, String bossId) {
		return bossId == null || CharacterAttachments.has(player, CharacterAttachments.BOSSES_DEFEATED, bossId);
	}

	static int styleLevel(Player player, FightingStyle style) {
		return StyleMastery.level(player, style);
	}

	public static void initialize() {
		// Loading this class registers the attachment.
	}
}
