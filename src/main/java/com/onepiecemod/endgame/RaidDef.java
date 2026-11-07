package com.onepiecemod.endgame;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Predicate;

import net.minecraft.ChatFormatting;
import net.minecraft.server.level.ServerPlayer;

import com.onepiecemod.character.CharacterAttachments;
import com.onepiecemod.story.StoryProgress;

/**
 * The endgame raids. Each raid is a few waves; a wave is some pirate or Marine NPCs (kits from npc_kits.json)
 * and maybe a boss or two from characters.json. The last wave's boss is the raid's big name.
 *
 * Wave spawns are written as short strings:
 *   "gifter*8"            8 NPCs with the gifter kit (more with more players)
 *   "boss:king@expert"    King as a boss, on Expert (also "@hard" or "@normal")
 */
public record RaidDef(String id, String name, String crew, ChatFormatting color, String unlockText,
		Predicate<ServerPlayer> unlocked, List<Wave> waves, int berries, int statXp, List<String> loot,
		String trophyName, int trophyColor, int resistance) {

	/** One wave: a title for the boss bar and what spawns. */
	public record Wave(String title, List<String> spawns) {
	}

	/** Health (counting the part past the 1024 cap) and attack damage a character has as a raid boss. */
	public record BossStats(float health, double damage) {
	}

	/**
	 * Raid stats for characters who are friendly quest givers in characters.json (400 health), so they fight like legends.
	 * For scale, on Expert: Kaido has 5250 health and 40 damage, Whitebeard 5950 and 44, Xebec 10500 and 56.
	 * Balance pass 2026-11-01: Rayleigh 7000 -> 5000 and Roger 12000 -> 8000, because the Roger raid took about 35 minutes
	 * solo even for a maxed player (over the time limit). Now about 16 minutes. Model: tools/balance/endgame_model.py.
	 */
	private static final Map<String, BossStats> BOSS_STATS = Map.of(
			"garp", new BossStats(3500, 40),
			"marco", new BossStats(3500, 36),
			"shanks", new BossStats(6500, 50),
			"rayleigh", new BossStats(5000, 48),
			"roger", new BossStats(8000, 58));

	/** Raid stats for this character, or null to use characters.json. */
	public static BossStats bossStats(String id) {
		return BOSS_STATS.get(id);
	}

	/** Full loot from the same raid at most once every 7 Minecraft days. */
	public static final long FULL_LOOT_EVERY = 24000L * 7;

	private static final Map<String, RaidDef> RAIDS = new LinkedHashMap<>();

	public static Map<String, RaidDef> all() {
		return RAIDS;
	}

	public static RaidDef get(String id) {
		return RAIDS.get(id);
	}

	/** The five crews whose raids count toward the Rocks and Roger raids. */
	private static final List<String> EMPEROR_RAIDS = List.of("beasts", "big_mom", "blackbeard", "whitebeard", "red_hair");

	static {
		add(new RaidDef("final_war", "The Final War", "World Government", ChatFormatting.AQUA,
				"Finish the story at Laugh Tale",
				player -> StoryProgress.orStart(player).finished() || EndgameData.of(player).cycle() > 0,
				List.of(
						new Wave("Marine landing party", List.of("marine*6", "marine_rifle*4", "marine_officer*2")),
						new Wave("Pacifista squad", List.of("elite_marine*5", "pacifista*3", "vice_admiral*1")),
						new Wave("Vice Admiral Garp", List.of("boss:garp@expert", "seraphim*2", "elite_marine*3")),
						new Wave("Admirals Kizaru and Akainu", List.of("boss:kizaru@hard", "boss:akainu@expert"))),
				1500, 1500, List.of("onepiece:berry_block*24", "minecraft:enchanted_golden_apple*2", "minecraft:netherite_ingot*2",
						"minecraft:totem_of_undying*1"),
				"Final War Medal", 0x3fa7d6, 0));

		add(new RaidDef("beasts", "Beasts Pirates", "Onigashima", ChatFormatting.DARK_PURPLE,
				"Beat Kaido on Hard",
				player -> beaten(player, "kaido:hard"),
				List.of(
						new Wave("Gifters", List.of("gifter*8", "pirate_gunner*3")),
						new Wave("Headliners and King the Wildfire", List.of("headliner*5", "boss:king@expert")),
						new Wave("Kaido of the Beasts", List.of("boss:kaido@expert", "headliner*2"))),
				1200, 1200, List.of("onepiece:berry_block*16", "minecraft:enchanted_golden_apple*2", "minecraft:netherite_ingot*2",
						"minecraft:nether_star*1", "onepiece:ame_no_habakiri*1"),
				"Kaido's Horn", 0x7b3fa0, 1));

		add(new RaidDef("big_mom", "Big Mom Pirates", "Totto Land", ChatFormatting.LIGHT_PURPLE,
				"Beat Big Mom on Hard",
				player -> beaten(player, "big_mom:hard"),
				List.of(
						new Wave("Chess soldiers", List.of("pirate*10", "pirate_gunner*3")),
						new Wave("Sweet Commander Katakuri", List.of("boss:katakuri@expert", "pirate_captain*3")),
						new Wave("Charlotte Linlin", List.of("boss:big_mom@expert", "pirate_captain*2"))),
				1200, 1200, List.of("onepiece:berry_block*16", "minecraft:enchanted_golden_apple*2", "minecraft:netherite_ingot*2",
						"minecraft:cake*4", "minecraft:nether_star*1"),
				"Napoleon's Hat", 0xe36fae, 1));

		add(new RaidDef("blackbeard", "Blackbeard Pirates", "Hachinosu", ChatFormatting.DARK_GRAY,
				"Beat Blackbeard on Hard",
				player -> beaten(player, "blackbeard:hard"),
				List.of(
						new Wave("Hachinosu thugs", List.of("blackbeard_pirate*8", "pirate_gunner*4")),
						new Wave("The Titanic Captains", List.of("blackbeard_pirate*4", "pirate_captain*4", "boss:magellan@expert")),
						new Wave("Marshall D. Teach", List.of("boss:blackbeard@expert", "blackbeard_pirate*3"))),
				1300, 1300, List.of("onepiece:berry_block*18", "minecraft:enchanted_golden_apple*2", "minecraft:netherite_ingot*3",
						"minecraft:nether_star*1"),
				"Blackbeard's Jolly Roger", 0x2b2b2b, 1));

		add(new RaidDef("whitebeard", "Whitebeard's Legacy", "Moby Dick", ChatFormatting.WHITE,
				"Beat Whitebeard on Hard",
				player -> beaten(player, "whitebeard:hard"),
				List.of(
						new Wave("The Whitebeard divisions", List.of("whitebeard_pirate*10")),
						new Wave("First Division Commander Marco", List.of("boss:marco@expert", "whitebeard_pirate*4")),
						new Wave("Edward Newgate", List.of("boss:whitebeard@expert"))),
				1400, 1400, List.of("onepiece:berry_block*20", "minecraft:enchanted_golden_apple*3", "minecraft:netherite_ingot*3",
						"minecraft:nether_star*1"),
				"Whitebeard's Bisento Tassel", 0xf2f2f2, 1));

		add(new RaidDef("red_hair", "Red Hair Pirates", "Elbaph", ChatFormatting.RED,
				"Win two other Emperor raids",
				player -> clearedCount(player, EMPEROR_RAIDS) >= 2,
				List.of(
						new Wave("The Red Force crew", List.of("pirate*8", "pirate_gunner*4", "pirate_captain*2")),
						new Wave("Benn Beckman's sharpshooters", List.of("pirate_gunner*6", "pirate_captain*4")),
						new Wave("Red-Haired Shanks", List.of("boss:shanks@expert"))),
				1500, 1500, List.of("onepiece:berry_block*20", "minecraft:enchanted_golden_apple*3", "minecraft:netherite_ingot*3",
						"minecraft:nether_star*2"),
				"Shanks's Gryphon Hilt", 0xc8262b, 2));

		add(new RaidDef("rocks", "Rocks Pirates", "God Valley", ChatFormatting.DARK_RED,
				"Beat Rocks D. Xebec, or win four Emperor raids",
				player -> beaten(player, "xebec") || clearedCount(player, EMPEROR_RAIDS) >= 4,
				List.of(
						new Wave("God Valley's warriors", List.of("pirate_captain*6", "headliner*4", "blackbeard_pirate*3")),
						new Wave("Young Newgate and Linlin", List.of("boss:whitebeard@hard", "boss:big_mom@hard")),
						new Wave("Rocks D. Xebec", List.of("boss:xebec@expert"))),
				2000, 2000, List.of("onepiece:berry_block*28", "minecraft:enchanted_golden_apple*4", "minecraft:netherite_ingot*4",
						"minecraft:nether_star*2", "minecraft:totem_of_undying*1"),
				"Rocks's Jolly Roger", 0x7a1010, 1));

		add(new RaidDef("roger", "Roger Pirates", "Laugh Tale", ChatFormatting.GOLD,
				"Win all the other raids and beat Imu",
				player -> clearedCount(player, List.of("final_war", "beasts", "big_mom", "blackbeard", "whitebeard", "red_hair", "rocks")) >= 7
						&& beaten(player, "imu"),
				List.of(
						new Wave("The Oro Jackson's crew", List.of("pirate_captain*8", "whitebeard_pirate*4")),
						new Wave("Dark King Silvers Rayleigh", List.of("boss:rayleigh@expert")),
						new Wave("Gol D. Roger, King of the Pirates", List.of("boss:roger@expert"))),
				3000, 3000, List.of("onepiece:berry_block*40", "minecraft:enchanted_golden_apple*6", "minecraft:netherite_ingot*6",
						"minecraft:nether_star*3", "minecraft:totem_of_undying*2", "onepiece:joy_boy_chest*1", "onepiece:ace*1"),
				"Roger's Captain Coat", 0xd4a017, 2));
	}

	private static void add(RaidDef raid) {
		RAIDS.put(raid.id, raid);
	}

	/** Beaten in any cycle. */
	static boolean beaten(ServerPlayer player, String key) {
		return CharacterAttachments.has(player, CharacterAttachments.BOSSES_DEFEATED, key);
	}

	private static int clearedCount(ServerPlayer player, List<String> raids) {
		List<String> cleared = EndgameData.of(player).cleared();
		return (int) raids.stream().filter(cleared::contains).count();
	}
}
