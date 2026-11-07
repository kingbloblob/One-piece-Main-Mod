package com.onepiecemod.bounty;

import com.onepiecemod.sound.ModSounds;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import com.google.gson.Gson;
import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.character.CharacterData;

/**
 * Each player's bounty, in Berries. It is saved with the world and kept when you die.
 * How much a boss is worth is in src/main/resources/onepiece/bounties.json.
 */
public class Bounty {
	/** The player's bounty, like 30000000 for 30 million Berries. */
	public static final AttachmentType<Long> BOUNTY = AttachmentRegistry.create(
			OnePieceMod.id("bounty"),
			builder -> builder.persistent(Codec.LONG).copyOnDeath()
	);

	/** Bosses that already raised this player's bounty. Beating them again only adds a little. */
	public static final AttachmentType<List<String>> BOSSES_COUNTED = AttachmentRegistry.create(
			OnePieceMod.id("bounty_bosses"),
			builder -> builder.persistent(Codec.STRING.listOf()).copyOnDeath()
	);

	public static long get(Player player) {
		return player.getAttachedOrElse(BOUNTY, 0L);
	}

	public static void set(Player player, long amount) {
		player.setAttached(BOUNTY, Math.max(0L, amount));
	}

	/** Raises the bounty and returns the new total. */
	public static long add(Player player, long amount) {
		long total = get(player) + amount;
		set(player, total);
		return total;
	}

	/** Returns true the first time this boss raises this player's bounty. */
	public static boolean countBoss(Player player, String characterId) {
		List<String> list = new ArrayList<>(player.getAttachedOrElse(BOSSES_COUNTED, List.of()));
		if (list.contains(characterId)) {
			return false;
		}
		list.add(characterId);
		player.setAttached(BOSSES_COUNTED, list);
		return true;
	}

	/** 30000000 becomes "30,000,000 Berries". */
	public static String format(long amount) {
		return String.format("%,d Berries", amount);
	}

	// ---- How much bosses and Marines are worth ----

	/** The shape of bounties.json. */
	private static class Table {
		Map<String, Long> bosses = Map.of();
		Map<String, Long> tiers = Map.of();
		double repeatShare = 0.1;
	}

	private static Table table;

	private static Table table() {
		if (table == null) {
			try (InputStream in = Bounty.class.getResourceAsStream("/onepiece/bounties.json")) {
				table = new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), Table.class);
			} catch (Exception e) {
				throw new RuntimeException("Could not read onepiece/bounties.json", e);
			}
		}
		return table;
	}

	/** How much beating this boss raises your bounty the first time. */
	public static long bossReward(String characterId) {
		Long reward = table().bosses.get(characterId);
		if (reward != null) {
			return reward;
		}
		CharacterData data = CharacterData.get(characterId);
		int tier = data != null ? data.tier : 1;
		return table().tiers.getOrDefault(String.valueOf(tier), 30_000_000L);
	}

	/** Beating the same boss again only adds this share (10%) of the first reward. */
	public static long repeatReward(String characterId) {
		return (long) (bossReward(characterId) * table().repeatShare);
	}

	// ---- Threat levels: how hard the Marines hunt you ----

	/** Bounty needed for each threat level. Level 0 means the Marines don't care about you. */
	private static final long[] LEVEL_START = {0, 1, 50_000_000L, 100_000_000L, 500_000_000L, 1_000_000_000L};
	private static final String[] LEVEL_NAME = {
			"Nobody", "Rookie Pirate", "Known Pirate", "Supernova", "Worst Generation", "Emperor Class"
	};

	public static int threatLevel(long bounty) {
		int level = 0;
		for (int i = 0; i < LEVEL_START.length; i++) {
			if (bounty >= LEVEL_START[i]) {
				level = i;
			}
		}
		return level;
	}

	public static int threatLevel(Player player) {
		return threatLevel(get(player));
	}

	public static String levelName(int level) {
		return LEVEL_NAME[level];
	}

	/** What the Marines send at each level, shown in /bounty. */
	public static String levelDescription(int level) {
		return switch (level) {
			case 0 -> "The Marines aren't looking for you.";
			case 1 -> "Small Marine patrols (2 recruits) now and then.";
			case 2 -> "Patrols of 3 with riflemen, more often.";
			case 3 -> "Squads of 4 led by a Lieutenant. Smoker may come for you.";
			case 4 -> "Squads of 5 led by a Captain. CP0's Rob Lucci may come for you.";
			default -> "Squads of 6, very often. An Admiral may come for you.";
		};
	}

	/**
	 * Raises the bounty (with a sound, no chat line). If the threat level went up, everyone hears about it.
	 * With newPoster (or on a level up) the player also gets a fresh Wanted Poster of themselves.
	 */
	public static void raise(ServerPlayer player, long amount, String reason, boolean newPoster) {
		if (com.onepiecemod.career.Careers.interceptBounty(player, amount, reason)) {
			return; // Marines never get a bounty (career package).
		}
		amount = com.onepiecemod.config.ModConfig.scale(amount, com.onepiecemod.config.ModConfig.bountyGain());
		if (amount <= 0) {
			return;
		}
		int oldLevel = threatLevel(player);
		long total = add(player, amount);
		int newLevel = threatLevel(total);
		ModSounds.play(player, newLevel > oldLevel ? ModSounds.NEWS_COO : ModSounds.BOUNTY_RAISE);

		// No chat line for every raise (ryan asked): the bounty shows on the poster in the inventory,
		// and the sound plays. Only a new threat level still makes the News.

		if (newLevel > oldLevel) {
			// A News Coo spreads the word, just like in the anime.
			String rank = levelName(newLevel);
			String article = "AEIOU".indexOf(Character.toUpperCase(rank.charAt(0))) >= 0 ? "an " : "a ";
			Component news = Component.literal("[News Coo] " + player.getName().getString() + " is now " + article
					+ rank + " with a bounty of " + format(total) + "!").withStyle(ChatFormatting.GOLD);
			player.level().getServer().getPlayerList().broadcastSystemMessage(news, false);
			player.sendSystemMessage(Component.literal(levelDescription(newLevel)).withStyle(ChatFormatting.YELLOW));
			newPoster = true;
		}
		if (newPoster) {
			BountyPosterItem.give(player);
		}
	}

	public static void initialize() {
		// Loading this class registers the attachments. Read the table now so a typo shows up at startup.
		table();
	}
}
