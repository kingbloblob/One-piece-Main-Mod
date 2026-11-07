package com.onepiecemod.story;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.world.entity.player.Player;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;

/**
 * How far a player is in the main story. Saved on the player and kept when they die.
 *
 * @param chapter  the chapter they are on, counting from 0. Equal to the number of chapters once the story is done.
 * @param goals    goals already done in the current chapter, by their position ("0", "2"...).
 *                 A goal stays done even if, say, you later drop the item it asked for.
 * @param counters running totals, like blocks sailed ("sail") or mobs beaten at a place ("kills:arlong_park").
 * @param flags    one-time things: finished story events, Conqueror's rolls already used, and so on.
 * @param at       the id of the chapter they are on ("end" once every chapter is done). Chapters can be added
 *                 in the middle of the story (Wano and Egghead were, in November 2026), so a save also remembers
 *                 the chapter by name, and {@link #of} moves it to that chapter's new position.
 */
public record StoryProgress(int chapter, List<String> goals, Map<String, Integer> counters, List<String> flags, String at) {
	/** The last chapter of the main story. */
	public static final String LAUGH_TALE = "laugh_tale";
	public static final StoryProgress START = new StoryProgress(0, List.of(), Map.of(), List.of(), "");
	/** What "at" says once every chapter is done. */
	private static final String END = "end";
	/**
	 * The chapter order before "at" was saved (up to November 2026). Saves without "at" are read with this list.
	 * Never change it.
	 */
	private static final List<String> FIRST_ORDER = List.of("dream", "koby", "set_sail", "orange_town", "syrup_village",
			"baratie", "arlong_park", "loguetown", "reverse_mountain", "drum_island", "alabasta", "sky_island",
			"enies_lobby", "thriller_bark", "sabaody", "amazon_lily", "impel_down", "marineford", "training",
			"fishman_island", "punk_hazard", "dressrosa", "zou", "whole_cake", "wano", "hachinosu", "laugh_tale",
			"red_line", "void_century", "empty_throne", "dawn");

	public static final Codec<StoryProgress> CODEC = RecordCodecBuilder.create(instance -> instance.group(
			Codec.INT.optionalFieldOf("chapter", 0).forGetter(StoryProgress::chapter),
			Codec.STRING.listOf().optionalFieldOf("goals", List.of()).forGetter(StoryProgress::goals),
			Codec.unboundedMap(Codec.STRING, Codec.INT).optionalFieldOf("counters", Map.of()).forGetter(StoryProgress::counters),
			Codec.STRING.listOf().optionalFieldOf("flags", List.of()).forGetter(StoryProgress::flags),
			Codec.STRING.optionalFieldOf("at", "").forGetter(StoryProgress::at)
	).apply(instance, StoryProgress::new));

	public static final AttachmentType<StoryProgress> PROGRESS = AttachmentRegistry.create(
			OnePieceMod.id("story"),
			builder -> builder
					.persistent(CODEC) // Save it to disk.
					.copyOnDeath() // Dying doesn't send you back to Foosha Village.
	);

	/** A player's progress, or null if they have never had a Captain's Log. */
	public static StoryProgress of(Player player) {
		StoryProgress progress = player.getAttached(PROGRESS);
		if (progress == null || player.level().isClientSide()) {
			return progress;
		}
		StoryProgress fixed = progress.placed();
		if (fixed != progress) {
			player.setAttached(PROGRESS, fixed);
		}
		return fixed;
	}

	/** The id of the chapter at a position, or "end". */
	private static String idAt(int index) {
		StoryData.Chapter chapter = StoryData.chapter(index);
		return chapter != null ? chapter.id : END;
	}

	/**
	 * This progress with "chapter" pointing at the chapter "at" names (or, for an old save, the chapter that
	 * position had in {@link #FIRST_ORDER}). Returns this same object when nothing moved.
	 * A chapter that moved starts its goals fresh: they are checked again a second later anyway. So does a chapter
	 * whose goal list was changed ({@link StoryData.Chapter#goalsChanged}), once.
	 */
	StoryProgress placed() {
		String id = at;
		if (id.isEmpty()) {
			id = chapter >= 0 && chapter < FIRST_ORDER.size() ? FIRST_ORDER.get(chapter) : END;
		}
		int index = END.equals(id) ? StoryData.chapters().size() : StoryData.indexOf(id);
		if (index < 0) {
			index = chapter; // A chapter that was taken out: stay at the same position.
			id = idAt(index);
		}
		StoryData.Chapter current = StoryData.chapter(index);
		String changed = current == null || current.goalsChanged.isEmpty() ? null : "goals:" + current.id + ":" + current.goalsChanged;
		boolean stale = changed != null && !flags.contains(changed);
		if (index == chapter && id.equals(at) && !stale) {
			return this;
		}
		List<String> newFlags = flags;
		if (stale) {
			newFlags = new ArrayList<>(flags);
			newFlags.add(changed);
		}
		return new StoryProgress(index, index == chapter && !stale ? goals : List.of(), counters, newFlags, id);
	}

	/** A player's progress, or the very start if they have none yet. */
	public static StoryProgress orStart(Player player) {
		StoryProgress progress = of(player);
		return progress != null ? progress : START;
	}

	public static void set(Player player, StoryProgress progress) {
		player.setAttached(PROGRESS, progress);
	}

	/** True once the main story is done (Laugh Tale). The post-game chapters come after it. */
	public boolean finished() {
		return completed(LAUGH_TALE);
	}

	/** True once every chapter is done, post-game included. */
	public boolean allDone() {
		return chapter >= StoryData.chapters().size();
	}

	public boolean goalDone(int goal) {
		return goals.contains(Integer.toString(goal));
	}

	public StoryProgress withGoal(int goal) {
		List<String> list = new ArrayList<>(goals);
		list.add(Integer.toString(goal));
		return new StoryProgress(chapter, list, counters, flags, at);
	}

	/**
	 * Moves on to another chapter. Goals start fresh; counters and flags are kept.
	 * Blocks sailed so far are noted, so a chapter's sailing goal only counts sailing done during that chapter.
	 */
	public StoryProgress atChapter(int index) {
		Map<String, Integer> map = new HashMap<>(counters);
		for (String key : List.of("sail", "sail_ship")) {
			map.put(key + "@start", counter(key));
		}
		return new StoryProgress(index, List.of(), map, flags, idAt(index));
	}

	/** How much a counter grew since this chapter started (the whole count for saves from before chapters noted it). */
	public int counterThisChapter(String key) {
		return counter(key) - counter(key + "@start");
	}

	public int counter(String key) {
		return counters.getOrDefault(key, 0);
	}

	public StoryProgress addCounter(String key, int amount) {
		Map<String, Integer> map = new HashMap<>(counters);
		map.merge(key, amount, Integer::sum);
		return new StoryProgress(chapter, goals, map, flags, at);
	}

	public boolean hasFlag(String flag) {
		return flags.contains(flag);
	}

	public StoryProgress withFlag(String flag) {
		if (flags.contains(flag)) {
			return this;
		}
		List<String> list = new ArrayList<>(flags);
		list.add(flag);
		return new StoryProgress(chapter, goals, counters, list, at);
	}

	/** True once the player has reached (started) the chapter with this id. Unknown ids count as reached. */
	public boolean reached(String chapterId) {
		int index = StoryData.indexOf(chapterId);
		return index < 0 || chapter >= index;
	}

	/** True once the player has finished the chapter with this id. */
	public boolean completed(String chapterId) {
		int index = StoryData.indexOf(chapterId);
		return index < 0 || chapter > index;
	}

	public static void initialize() {
		// Loading this class is enough to register the attachment.
	}
}
