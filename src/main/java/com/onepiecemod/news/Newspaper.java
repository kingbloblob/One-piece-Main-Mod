package com.onepiecemod.news;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.Filterable;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.WrittenBookContent;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.empire.EmpireData;
import com.onepiecemod.empire.Title;
import com.onepiecemod.story.StoryData;
import com.onepiecemod.story.StoryProgress;

/**
 * The World Economy News Paper that the News Coo brings every morning.
 * It's a normal written book (so the vanilla book screen reads it) that looks like a newspaper.
 *
 * Pages: front page, pirate news (what players did since the last paper), world news
 * (canon events that fit the reader's place in the story), the Most Wanted list, and the reader's own bounty.
 */
public class Newspaper {
	/** How many player headlines fit in one paper. */
	private static final int MAX_PIRATE_NEWS = 8;

	/** Prints today's paper for this reader. sinceDay = the first day whose news they haven't read yet. */
	public static ItemStack print(ServerPlayer reader, long sinceDay) {
		MinecraftServer server = reader.level().getServer();
		long day = NewsLog.day(server);
		RandomSource random = RandomSource.create(day * 31L + reader.getUUID().getLeastSignificantBits());
		NewsData data = NewsData.get();

		List<NewsLog.Headline> pirateNews = NewsLog.recent(server, day - Math.max(0, sinceDay));
		List<String> worldNews = worldStories(reader, day, random, data);

		List<Component> pages = new ArrayList<>();

		// Front page: the biggest pirate story if there is one, otherwise world news.
		MutableComponent front = Component.empty()
				.append(Component.literal("WORLD ECONOMY\nNEWS PAPER\n").withStyle(ChatFormatting.BOLD))
				.append(Component.literal("Day " + (day + 1) + "  -  100 Berries\n").withStyle(ChatFormatting.DARK_GRAY))
				.append(Component.literal("-------------------\n").withStyle(ChatFormatting.GRAY));
		if (!pirateNews.isEmpty()) {
			NewsLog.Headline top = pirateNews.get(0);
			front.append(story(top.headline(), top.story()));
		} else {
			String[] split = splitStory(worldNews.get(0));
			front.append(story(split[0], split[1]));
		}
		pages.add(front);

		// Pirate news.
		int shown = 0;
		for (int i = pirateNews.isEmpty() ? 0 : 1; i < pirateNews.size() && shown < MAX_PIRATE_NEWS; i++, shown++) {
			NewsLog.Headline h = pirateNews.get(i);
			pages.add(section("PIRATE NEWS").append(story(h.headline(), h.story())));
		}

		// World news.
		for (int i = pirateNews.isEmpty() ? 1 : 0; i < worldNews.size(); i++) {
			String[] split = splitStory(worldNews.get(i));
			pages.add(section("WORLD NEWS").append(story(split[0], split[1])));
		}

		pages.add(mostWanted(server, reader));
		pages.add(yourBounty(reader));

		List<Filterable<Component>> filtered = new ArrayList<>();
		for (Component page : pages) {
			filtered.add(Filterable.passThrough(page));
		}
		ItemStack paper = new ItemStack(Items.WRITTEN_BOOK);
		paper.set(DataComponents.WRITTEN_BOOK_CONTENT, new WrittenBookContent(
				Filterable.passThrough("News Coo Paper, Day " + (day + 1)), "Morgans", 0, filtered, true));
		paper.set(DataComponents.ITEM_MODEL, OnePieceMod.id("newspaper"));
		return paper;
	}

	/** Two stories for the reader's saga, plus one from anywhere in the seas. */
	private static List<String> worldStories(ServerPlayer reader, long day, RandomSource random, NewsData data) {
		List<String> out = new ArrayList<>();
		List<String> pool = new ArrayList<>(data.world.getOrDefault(sagaOf(reader), List.of()));
		for (int i = 0; i < 2 && !pool.isEmpty(); i++) {
			out.add(pool.remove(random.nextInt(pool.size())));
		}
		out.add(data.randomAnytime(random));
		return out;
	}

	/** The id of the saga the reader is in, like "east_blue". */
	public static String sagaOf(ServerPlayer reader) {
		StoryProgress progress = StoryProgress.orStart(reader);
		List<StoryData.Chapter> chapters = StoryData.chapters();
		if (chapters.isEmpty()) {
			return "romance_dawn";
		}
		int index = Math.max(0, Math.min(progress.chapter(), chapters.size() - 1));
		StoryData.Chapter chapter = chapters.get(index);
		return chapter.saga != null ? chapter.saga.id : "romance_dawn";
	}

	/** 0 = Romance Dawn ... 5 = Final Saga (the post-game counts as 5 too). */
	public static int sagaNumber(ServerPlayer reader) {
		return switch (sagaOf(reader)) {
			case "romance_dawn" -> 0;
			case "east_blue" -> 1;
			case "paradise" -> 2;
			case "summit_war" -> 3;
			case "new_world" -> 4;
			default -> 5;
		};
	}

	private static MutableComponent mostWanted(MinecraftServer server, ServerPlayer reader) {
		MutableComponent page = section("MOST WANTED");
		List<Map.Entry<String, NewsLog.Wanted>> list = NewsLog.mostWanted(server);
		int rank = 1;
		for (Map.Entry<String, NewsLog.Wanted> e : list) {
			if (rank > 5) {
				break;
			}
			page.append(Component.literal(rank + ". " + e.getValue().name() + "\n").withStyle(ChatFormatting.DARK_RED))
					.append(Component.literal("   " + Bounty.format(e.getValue().bounty()) + "\n").withStyle(ChatFormatting.BLACK));
			rank++;
		}
		if (list.isEmpty()) {
			page.append(Component.literal("No pirate in these waters has a bounty yet. The Marines are watching, though.\n")
					.withStyle(ChatFormatting.DARK_GRAY));
		}
		page.append(Component.literal("\nNew posters go up in every town and Marine base.").withStyle(ChatFormatting.DARK_GRAY));
		return page;
	}

	private static MutableComponent yourBounty(ServerPlayer reader) {
		long bounty = Bounty.get(reader);
		MutableComponent page = section("YOUR BOUNTY");
		page.append(Component.literal(reader.getName().getString() + "\n").withStyle(ChatFormatting.DARK_RED, ChatFormatting.BOLD));
		page.append(Component.literal(Bounty.format(bounty) + "\n").withStyle(ChatFormatting.BLACK));
		page.append(Component.literal(Bounty.levelName(Bounty.threatLevel(bounty)) + "\n").withStyle(ChatFormatting.DARK_GRAY));
		Title title = EmpireData.title(reader);
		if (title != Title.NONE) {
			page.append(Component.literal(title.displayName + "\n").withStyle(ChatFormatting.GOLD));
		}
		page.append(Component.literal("\nThe News Coo comes every morning. Don't want the paper? /news off").withStyle(ChatFormatting.DARK_GRAY));
		return page;
	}

	private static MutableComponent section(String name) {
		// Children of an empty component don't inherit each other's style, so the bold stays on the title.
		return Component.empty()
				.append(Component.literal(name + "\n").withStyle(ChatFormatting.BOLD, ChatFormatting.DARK_BLUE))
				.append(Component.literal("-------------------\n").withStyle(ChatFormatting.GRAY));
	}

	private static MutableComponent story(String headline, String body) {
		return Component.empty()
				.append(Component.literal(headline + "\n").withStyle(ChatFormatting.BOLD, ChatFormatting.BLACK))
				.append(Component.literal(body).withStyle(ChatFormatting.BLACK));
	}

	/** "HEADLINE: the story" becomes {"HEADLINE", "the story"}. */
	private static String[] splitStory(String text) {
		int colon = text.indexOf(": ");
		if (colon < 0) {
			return new String[] {"NEWS", text};
		}
		return new String[] {text.substring(0, colon).toUpperCase(), text.substring(colon + 2)};
	}
}
