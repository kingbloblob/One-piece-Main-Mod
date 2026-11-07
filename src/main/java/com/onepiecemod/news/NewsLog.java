package com.onepiecemod.news;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.ChatFormatting;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.race.Race;
import com.onepiecemod.race.RaceAttachments;
import com.onepiecemod.worldevent.WorldNews;

/**
 * What the world is talking about, for the paper and the wall posters:
 *  - headlines: kept by worldevent/WorldNews (world events and players' deeds in one list).
 *  - most wanted: every player who ever had a bounty, saved on the Overworld (works when they're offline too).
 */
public class NewsLog {
	/** One headline as the paper prints it. day = the game day the worldevent list stamped on it. */
	public record Headline(long day, String headline, String story) {
	}

	/** A pirate on the wall posters. */
	public record Wanted(String name, long bounty, String race) {
		public static final Codec<Wanted> CODEC = RecordCodecBuilder.create(instance -> instance.group(
				Codec.STRING.fieldOf("name").forGetter(Wanted::name),
				Codec.LONG.fieldOf("bounty").forGetter(Wanted::bounty),
				Codec.STRING.fieldOf("race").forGetter(Wanted::race)
		).apply(instance, Wanted::new));
	}

	/** Player UUID (as text) to their poster. */
	public static final AttachmentType<Map<String, Wanted>> MOST_WANTED = AttachmentRegistry.create(
			OnePieceMod.id("most_wanted"),
			builder -> builder.persistent(Codec.unboundedMap(Codec.STRING, Wanted.CODEC))
	);

	/** The world day (by the day/night clock), counting from 0. */
	public static long day(MinecraftServer server) {
		return server.overworld().getDefaultClockTime() / 24000L;
	}

	/**
	 * Prints a headline in tomorrow's paper. All news goes into the one list the worldevent package keeps
	 * (worldevent/WorldNews), so world events and players' deeds share a paper. Stored as "HEADLINE: story".
	 * announce = also tell everyone right now in chat (with the News Coo sound).
	 */
	public static void report(MinecraftServer server, String headline, String story, boolean announce) {
		String line = headline + (headline.endsWith("!") ? " " : ": ") + story;
		if (announce) {
			WorldNews.report(server, line, ChatFormatting.GOLD);
		} else {
			WorldNews.remember(server, line);
		}
	}

	/** Headlines from the last daysBack days (0 = today only), newest first. */
	public static List<Headline> recent(MinecraftServer server, long daysBack) {
		List<Headline> out = new ArrayList<>();
		long today = server.overworld().getGameTime() / 24000L + 1; // How worldevent/WorldNews counts days.
		for (String entry : server.overworld().getAttachedOrElse(WorldNews.HEADLINES, List.<String>of())) {
			int bar = entry.indexOf('|');
			long day;
			try {
				day = bar > 0 ? Long.parseLong(entry.substring(0, bar)) : today;
			} catch (NumberFormatException e) {
				day = today;
			}
			if (day >= today - daysBack) {
				String[] split = split(bar >= 0 ? entry.substring(bar + 1) : entry);
				out.add(0, new Headline(day, split[0], split[1]));
			}
		}
		return out;
	}

	/** "HEADLINE: story" or "BUSTER CALL! The World..." becomes {headline, story}. Short ones are all headline. */
	public static String[] split(String text) {
		int colon = text.indexOf(": ");
		int bang = text.indexOf("! ");
		int cut = colon >= 0 && colon < 60 ? colon : (bang >= 0 && bang < 40 ? bang + 1 : -1);
		if (cut < 0) {
			return new String[] {"BREAKING NEWS", text};
		}
		String story = text.substring(cut + (text.charAt(cut) == ':' ? 2 : 1)).trim();
		return new String[] {text.substring(0, cut).toUpperCase(), story};
	}

	/** Keeps this player's poster up to date. */
	public static void updateWanted(ServerPlayer player) {
		long bounty = Bounty.get(player);
		Map<String, Wanted> map = player.level().getServer().overworld().getAttachedOrElse(MOST_WANTED, Map.of());
		String key = player.getUUID().toString();
		Race race = RaceAttachments.get(player);
		Wanted now = new Wanted(player.getName().getString(), bounty, race != null ? race.displayName : "Human");
		if (now.equals(map.get(key)) || (bounty <= 0 && !map.containsKey(key))) {
			return;
		}
		Map<String, Wanted> copy = new HashMap<>(map);
		copy.put(key, now);
		player.level().getServer().overworld().setAttached(MOST_WANTED, copy);
	}

	/** Every player with a bounty, highest first. */
	public static List<Map.Entry<String, Wanted>> mostWanted(MinecraftServer server) {
		List<Map.Entry<String, Wanted>> list = new ArrayList<>();
		for (Map.Entry<String, Wanted> e : server.overworld().getAttachedOrElse(MOST_WANTED, Map.<String, Wanted>of()).entrySet()) {
			if (e.getValue().bounty() > 0) {
				list.add(e);
			}
		}
		list.sort(Comparator.comparingLong((Map.Entry<String, Wanted> e) -> e.getValue().bounty()).reversed());
		return list;
	}
}
