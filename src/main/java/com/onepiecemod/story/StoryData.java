package com.onepiecemod.story;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

import com.google.gson.Gson;

import com.onepiecemod.character.CharacterData;
import com.onepiecemod.character.Locations;

/**
 * The main story, read from src/main/resources/onepiece/story.json.
 * To change a chapter (its text, goals or rewards), edit that JSON file, not this class.
 *
 * The story is a list of sagas, and each saga is a list of chapters. You play the chapters one after another.
 */
public class StoryData {
	public List<Saga> sagas = List.of();

	public static class Saga {
		public String id;
		public String title;
		/** Highest boss tier whose Devil Fruit can drop from leaves during this saga (story gates). */
		public int fruitTier = 5;
		public List<Chapter> chapters = List.of();
	}

	public static class Chapter {
		/** A short unique name, like "orange_town". Other code uses these (see StoryGates). */
		public String id;
		public String title;
		/** Shown when the chapter starts. */
		public String intro = "";
		/** Shown when the chapter is done. */
		public String outro = "";
		/** Structure ids. You get a Sea Chart to each one when the chapter starts. */
		public List<String> charts = List.of();
		public List<Goal> goals = List.of();
		public Reward reward = new Reward();
		/**
		 * Set (to a date, like "2026-11-06") when this chapter's goal list was changed after players may already have
		 * been on it. Goals are saved by position, so a save that is on this chapter starts its goals fresh, once.
		 */
		public String goalsChanged = "";

		/** Filled in after loading. */
		public transient Saga saga;
		public transient int index;
	}

	/**
	 * One thing to do. Which fields matter depends on the type:
	 *   race                          pick a race
	 *   reach      place              stand inside a structure, like "foosha_village"
	 *   talk       character          talk to a friendly character, like "koby"
	 *   quest      character, step    finish step N (counting from 1) of a character's quest line
	 *   boss       boss               beat a boss, like "buggy"
	 *   crew                          start a crew with /crew create
	 *   crew       role               have that role in your crew, like "navigator"
	 *   item       item, count        carry an item, like "onepiece:log_pose"
	 *   sail       count, ship        sail this many blocks in a boat (or a ship, if ship is true)
	 *   bounty     amount             have at least this bounty
	 *   islands    count              record this many islands with a Log Pose
	 *   sea        sea                sail into a sea: "calm_belt", "grand_line" or "blue"
	 *   haki       kind, level        reach a Haki level: "observation" or "armament"
	 *   styles     count              know this many fighting styles
	 *   mastery    amount             Devil Fruit mastery
	 *   kills      place, count       beat this many hostile mobs inside a structure
	 *   event      event              finish a story event (see StoryEvents)
	 *   any        of                 any one of the goals listed in "of"
	 *   treasure   count              dig up this many buried treasures or hoards (treasure maps)
	 *   fish       count              catch this many kinds of fish (/fishlog)
	 *   colosseum  level              win this Corrida Colosseum cup: 0 Rookie, 1 Veteran, 2 Champion
	 *   davyback   count              play this many Davy Back Fights, won or lost
	 *   history    count              read this many pages of the true history from Poneglyphs (endgame/VoidCentury)
	 *   page       page               have read this one page of the true history, like "elbaph"
	 *
	 * Two extras for "boss" and "talk" goals:
	 *   difficulty   1 = the boss must be beaten on Hard, 2 = Expert (a rematch that's part of the story)
	 *   summon       true = the story brings this character to "place" (or their home) once every earlier goal
	 *                of the chapter is done, for characters no structure has (Queen, Saturn) or who moved (Vegapunk)
	 */
	public static class Goal {
		public String type;
		/** What the Captain's Log shows, like "Beat Buggy at his Big Top". */
		public String text;
		public String place;
		public String character;
		public int step;
		public String boss;
		public String role;
		public String item;
		public int count = 1;
		public boolean ship;
		public long amount;
		public String sea;
		public String kind;
		public int level;
		public String event;
		public int difficulty;
		public boolean summon;
		/** A page id of endgame/VoidCentury, for "page" goals. */
		public String page;
		public List<Goal> of = List.of();
	}

	public static class Reward {
		public int berries;
		/** Pirate XP (stats/StatTraining) for finishing the chapter. */
		public int xp;
		public List<ItemReward> items = List.of();
	}

	public static class ItemReward {
		public String item;
		public int count = 1;
	}

	// ---- Loading ----

	private static StoryData data;
	private static final List<Chapter> CHAPTERS = new ArrayList<>();

	public static StoryData get() {
		if (data == null) {
			try (InputStream in = StoryData.class.getResourceAsStream("/onepiece/story.json")) {
				data = new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), StoryData.class);
			} catch (Exception e) {
				throw new RuntimeException("Could not read onepiece/story.json", e);
			}
			for (Saga saga : data.sagas) {
				for (Chapter chapter : saga.chapters) {
					chapter.saga = saga;
					chapter.index = CHAPTERS.size();
					CHAPTERS.add(chapter);
				}
			}
		}
		return data;
	}

	/** Every chapter in order. */
	public static List<Chapter> chapters() {
		get();
		return CHAPTERS;
	}

	/** The chapter at this position, or null once the story is finished. */
	public static Chapter chapter(int index) {
		List<Chapter> all = chapters();
		return index >= 0 && index < all.size() ? all.get(index) : null;
	}

	/** The position of a chapter by its id, or -1. */
	public static int indexOf(String chapterId) {
		for (Chapter chapter : chapters()) {
			if (chapter.id.equals(chapterId)) {
				return chapter.index;
			}
		}
		return -1;
	}

	/** Lists typos (unknown bosses, characters and places), so they show up in the log at startup. */
	public static List<String> problems() {
		List<String> problems = new ArrayList<>();
		for (Chapter chapter : chapters()) {
			for (String place : chapter.charts) {
				if (Locations.name(place).equals(place)) {
					problems.add(chapter.id + ": unknown place " + place);
				}
			}
			for (Goal goal : chapter.goals) {
				check(chapter, goal, problems);
				for (Goal option : goal.of) {
					check(chapter, option, problems);
				}
			}
		}
		return problems;
	}

	private static void check(Chapter chapter, Goal goal, List<String> problems) {
		if (goal.boss != null && CharacterData.get(goal.boss) == null) {
			problems.add(chapter.id + ": unknown boss " + goal.boss);
		}
		if (goal.character != null && CharacterData.get(goal.character) == null) {
			problems.add(chapter.id + ": unknown character " + goal.character);
		}
		if (goal.place != null && Locations.name(goal.place).equals(goal.place)) {
			problems.add(chapter.id + ": unknown place " + goal.place);
		}
		if ("page".equals(goal.type) && com.onepiecemod.endgame.VoidCentury.page(goal.page) == null) {
			problems.add(chapter.id + ": unknown history page " + goal.page);
		}
		if (goal.text == null) {
			problems.add(chapter.id + ": a " + goal.type + " goal has no text");
		}
	}
}
